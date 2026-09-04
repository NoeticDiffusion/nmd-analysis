"""
sbeg_mnps_extended.py — extend SBEG with peri-event MNPS / MNJ metrics.

Additional per-window metrics (computed from /mnps_3d and /jacobian/J_hat):
  v_k       = MNPS speed: ||z_k - z_{k-1}||_2
  disp_k    = MNPS displacement from run centroid: ||z_k - median_z||_2
  rho_k     = Jacobian rotation fraction: ||Omega||_F / (||J||_F + eps)
  trace_k   = tr(J_k)   (divergence / contraction)

Evoked peri-event deltas (peak - pre, normalised by run MAD):
  E_v, R_v, E_disp, R_disp, E_rho, R_rho, E_trace, R_trace

Usage (smoke test ~25 per class):
  python sbeg_mnps_extended.py --max-subjects-per-class 25
"""
from __future__ import annotations
import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.metrics import roc_auc_score

ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT   = ARTICLE_DIR.parents[2]

DEFAULT_PROCESSED_ROOTS = (
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260605_202236",
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260605_210700",
)
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "sbeg_mnps_20260607_smoke"

GOOD_CPC = 1
POOR_CPC = 5
EPS = 1e-9
WINDOW_SEC_FALLBACK = 4.0

# Detector params (same as run_sbeg_detector)
Q_SUPPRESS = 0.25
Q_ACTIVE   = 0.60
L_SUP_WIN  = 5
L_ACT_WIN  = 3
P_SUP      = 0.80
P_ACT      = 0.67
T_REF_SEC  = 60.0

PRE_START_SEC  = -60.0
PEAK_END_SEC   =  30.0
REC_END_SEC    = 120.0


def window_duration(time_arr: np.ndarray) -> float:
    arr = np.asarray(time_arr, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size < 2:
        return WINDOW_SEC_FALLBACK
    diffs = np.diff(arr)
    diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
    return float(np.median(diffs)) if diffs.size else WINDOW_SEC_FALLBACK


def rank_z(values: np.ndarray) -> np.ndarray:
    from scipy.special import ndtri
    arr = np.asarray(values, dtype=float)
    n = arr.size
    ranks = np.argsort(np.argsort(arr)) + 1
    return ndtri((ranks - 0.5) / n)


def safe_nanmedian(a) -> float:
    v = np.asarray(a, dtype=float)
    v = v[np.isfinite(v)]
    return float(np.median(v)) if v.size else float("nan")


def safe_nanmad(a) -> float:
    v = np.asarray(a, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return float("nan")
    return float(np.median(np.abs(v - np.median(v))))


def infer_source_cohort(root: Path) -> str:
    name = root.name.lower()
    if "part1" in name or "202236" in name:
        return "part1"
    if "part2" in name or "210700" in name:
        return "part2"
    return root.name


# ── activity score ──────────────────────────────────────────────────────────
def find_feature_indices(names):
    power_kw   = ("delta","theta","alpha","beta","gamma","highfreq","power","bandpower","relative","broadband")
    mobile_kw  = ("hjorth_mobility","mobility")
    entropy_kw = ("permutation_entropy","sample_entropy","entropy","hjorth_complexity","complexity")
    power_i  = [i for i,n in enumerate(names) if any(k in n.lower() for k in power_kw)]
    mobile_i = [i for i,n in enumerate(names) if any(k in n.lower() for k in mobile_kw)]
    entrop_i = [i for i,n in enumerate(names) if any(k in n.lower() for k in entropy_kw)]
    me_set   = set(mobile_i + entrop_i)
    power_i  = [i for i in power_i if i not in me_set]
    if not power_i:
        power_i = list(range(len(names)))
    return power_i, mobile_i, entrop_i


def compute_activity_score(raw_features: np.ndarray, names: list[str]) -> np.ndarray:
    pi, mi, ei = find_feature_indices(names)
    power_score = np.nanmean(np.log1p(np.abs(raw_features[:, pi])), axis=1)
    power_score[~np.isfinite(power_score)] = 0.0
    act = 0.50 * rank_z(power_score)
    if mi:
        mob = np.nanmedian(raw_features[:, mi], axis=1)
        mob[~np.isfinite(mob)] = 0.0
        act += 0.25 * rank_z(mob)
    else:
        act += 0.25 * rank_z(power_score)
    if ei:
        ent = np.nanmedian(raw_features[:, ei], axis=1)
        ent[~np.isfinite(ent)] = 0.0
        act += 0.25 * rank_z(ent)
    else:
        act += 0.25 * rank_z(power_score)
    return act


def detect_burst_onsets(activity, ws) -> list[int]:
    T = len(activity)
    q_s = float(np.quantile(activity, Q_SUPPRESS))
    q_u = float(np.quantile(activity, Q_ACTIVE))
    supp = activity <= q_s
    actv = activity >= q_u
    t_ref_wins = max(1, int(np.ceil(T_REF_SEC / ws)))
    onsets: list[int] = []
    last = -t_ref_wins - 1
    for k in range(L_SUP_WIN, T - L_ACT_WIN):
        if k - last < t_ref_wins:
            continue
        if np.mean(supp[k - L_SUP_WIN : k]) >= P_SUP and np.mean(actv[k : k + L_ACT_WIN]) >= P_ACT:
            onsets.append(k)
            last = k
    return onsets


# ── per-window geometry sequences ───────────────────────────────────────────
def spectral_radius_seq(J: np.ndarray) -> np.ndarray:
    out = np.full(len(J), np.nan)
    for i, Jk in enumerate(J):
        if np.isfinite(Jk).all():
            try:
                out[i] = float(np.max(np.abs(np.linalg.eigvals(Jk))))
            except np.linalg.LinAlgError:
                pass
    return out


def rotation_fraction_seq(J: np.ndarray) -> np.ndarray:
    """||Omega||_F / (||J||_F + eps), Omega = antisymmetric part."""
    out = np.full(len(J), np.nan)
    for i, Jk in enumerate(J):
        if np.isfinite(Jk).all():
            Omega = (Jk - Jk.T) / 2
            out[i] = float(np.linalg.norm(Omega, "fro") / (np.linalg.norm(Jk, "fro") + EPS))
    return out


def trace_seq(J: np.ndarray) -> np.ndarray:
    out = np.full(len(J), np.nan)
    for i, Jk in enumerate(J):
        if np.isfinite(Jk).all():
            out[i] = float(np.trace(Jk))
    return out


def mnps_speed_seq(mnps: np.ndarray) -> np.ndarray:
    """||z_k - z_{k-1}||_2  (length T, index 0 is NaN)."""
    out = np.full(mnps.shape[0], np.nan)
    diff = mnps[1:] - mnps[:-1]
    out[1:] = np.sqrt(np.sum(diff ** 2, axis=1))
    return out


def mnps_displacement_seq(mnps: np.ndarray) -> np.ndarray:
    """||z_k - centroid||_2"""
    centroid = np.nanmedian(mnps, axis=0)
    return np.sqrt(np.sum((mnps - centroid) ** 2, axis=1))


# ── peri-event extraction ────────────────────────────────────────────────────
def zone_slice(onset_idx: int, start_sec: float, end_sec: float, ws: float, T: int):
    s = max(0, onset_idx + int(np.floor(start_sec / ws)))
    e = min(T, onset_idx + int(np.ceil(end_sec / ws)) + 1)
    return s, e


def evoked_triplet(seq, onset, ws, T):
    """Returns (pre_med, peak_med, rec_med) or (nan,nan,nan)."""
    ps, pe = zone_slice(onset, PRE_START_SEC, 0.0, ws, T)
    ks, ke = zone_slice(onset, 0.0, PEAK_END_SEC, ws, T)
    rs, re = zone_slice(onset, PEAK_END_SEC, REC_END_SEC, ws, T)
    if pe <= ps or ke <= ks or re <= rs:
        return float("nan"), float("nan"), float("nan")
    return (safe_nanmedian(seq[ps:pe]),
            safe_nanmedian(seq[ks:ke]),
            safe_nanmedian(seq[rs:re]))


METRICS = [
    ("lambda",  spectral_radius_seq,  "jacobian"),
    ("rho",     rotation_fraction_seq,"jacobian"),
    ("trace",   trace_seq,            "jacobian"),
    ("speed",   mnps_speed_seq,       "mnps"),
    ("disp",    mnps_displacement_seq,"mnps"),
]


def process_run(h5_path: Path, max_subjects=None) -> dict[str, Any] | None:
    try:
        with h5py.File(h5_path, "r") as f:
            subject  = str(f.attrs.get("subject_id", "")).strip()
            cpc      = int(f.attrs.get("meta_cpc", -1))
            mnps3d   = np.asarray(f["/mnps_3d"][:], dtype=float)
            raw_feat = np.asarray(f["/features_raw/values"][:], dtype=float)
            jacobian = np.asarray(f["/jacobian/J_hat"][:], dtype=float)
            time_arr = np.asarray(f["/time"][:], dtype=float) if "/time" in f else np.array([])
            if "/features_raw/names" in f:
                feat_names = [n.decode() if isinstance(n, bytes) else str(n)
                              for n in f["/features_raw/names"][:]]
            else:
                feat_names = [f"feat_{i}" for i in range(raw_feat.shape[1])]
    except Exception:
        return None

    if cpc not in (GOOD_CPC, POOR_CPC) or not subject:
        return None

    T  = mnps3d.shape[0]
    ws = window_duration(time_arr)
    if T < 20:
        return None

    J = jacobian[:T]
    activity = compute_activity_score(raw_feat, feat_names)
    onsets   = detect_burst_onsets(activity, ws)
    if not onsets:
        return None

    # Build per-window sequences
    seqs: dict[str, np.ndarray] = {}
    seqs["jacobian"] = J
    seqs["mnps"]     = mnps3d

    computed: dict[str, np.ndarray] = {}
    for name, fn, src in METRICS:
        computed[name] = fn(seqs[src])

    # Per-event triplets
    event_rows: list[dict[str, float]] = []
    for onset in onsets:
        row: dict[str, float] = {}
        valid = True
        for name, _, _ in METRICS:
            seq = computed[name]
            mad = safe_nanmad(seq)
            pre, peak, rec = evoked_triplet(seq, onset, ws, T)
            if not all(np.isfinite([pre, peak, rec])):
                valid = False
                break
            row[f"E_{name}"] = (peak - pre) / (mad + EPS)
            row[f"R_{name}"] = abs(rec - pre) / (mad + EPS)
            row[f"pre_{name}"]  = pre
            row[f"peak_{name}"] = peak
            row[f"rec_{name}"]  = rec
        if valid:
            event_rows.append(row)

    if not event_rows:
        return None

    agg: dict[str, float] = {}
    for key in event_rows[0]:
        agg[key] = safe_nanmedian([r[key] for r in event_rows])

    agg["n_events"]      = float(len(event_rows))
    agg["event_rate"]    = float(len(event_rows) / (T * ws / 60.0))
    agg["subject"]       = subject   # type: ignore[assignment]
    agg["cpc"]           = cpc       # type: ignore[assignment]
    agg["source"]        = infer_source_cohort(h5_path.parent)  # type: ignore[assignment]

    # Run-level medians (baseline comparators)
    for name, _, _ in METRICS:
        agg[f"run_med_{name}"] = safe_nanmedian(computed[name])

    return agg  # type: ignore[return-value]


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if a.size < 2 or b.size < 2:
        return float("nan")
    pool = ((a.size-1)*np.var(a,ddof=1) + (b.size-1)*np.var(b,ddof=1)) / (a.size+b.size-2)
    if not np.isfinite(pool) or pool <= 0:
        return float("nan")
    return float((np.mean(a) - np.mean(b)) / np.sqrt(pool))


def build_contrast(subj_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    num_cols = [c for c in subj_df.columns
                if c not in {"subject","cpc","source","h5_path"}
                and subj_df[c].dtype.kind in "if"]
    for col in num_cols:
        good = subj_df.loc[subj_df.cpc == GOOD_CPC, col].dropna().to_numpy(dtype=float)
        poor = subj_df.loc[subj_df.cpc == POOR_CPC, col].dropna().to_numpy(dtype=float)
        if good.size < 4 or poor.size < 4:
            continue
        mw = mannwhitneyu(good, poor, alternative="two-sided")
        d  = cohens_d(good, poor)
        try:
            auroc = float(roc_auc_score(
                np.concatenate([np.ones(good.size), np.zeros(poor.size)]),
                np.concatenate([good, poor])
            ))
        except Exception:
            auroc = float("nan")
        rows.append({"metric": col, "cpc1_med": safe_nanmedian(good),
                     "cpc5_med": safe_nanmedian(poor),
                     "d": d, "abs_d": abs(d) if np.isfinite(d) else float("nan"),
                     "p": float(mw.pvalue), "auroc": auroc,
                     "n1": int(good.size), "n5": int(poor.size)})
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("abs_d", ascending=False).reset_index(drop=True)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--processed-root", dest="roots", action="append", type=Path)
    p.add_argument("--output-dir",  type=Path, default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--max-subjects-per-class", type=int, default=None)
    return p.parse_args()


def main():
    args = parse_args()
    roots = tuple(args.roots) if args.roots else DEFAULT_PROCESSED_ROOTS
    out   = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    max_s = args.max_subjects_per_class

    rows: list[dict] = []
    counts = {GOOD_CPC: 0, POOR_CPC: 0}
    seen:   set[str] = set()

    for root in roots:
        cohort = infer_source_cohort(root)
        if not root.exists():
            print(f"  WARNING root not found: {root}")
            continue
        h5_files = sorted(root.rglob("*.h5"))
        print(f"  {cohort}: {len(h5_files)} H5 files")
        for h5 in h5_files:
            try:
                with h5py.File(h5, "r") as f:
                    cpc  = int(f.attrs.get("meta_cpc", -1))
                    subj = str(f.attrs.get("subject_id","")).strip()
            except Exception:
                continue
            if cpc not in (GOOD_CPC, POOR_CPC) or not subj:
                continue
            key = f"{cohort}::{subj}"
            if key not in seen:
                if max_s is not None and counts[cpc] >= max_s:
                    continue
                seen.add(key)
                counts[cpc] += 1
            r = process_run(h5, max_s)
            if r is not None:
                r["pooled_subject"] = key
                rows.append(r)

    if not rows:
        raise RuntimeError("No valid runs found.")

    run_df = pd.DataFrame(rows)
    print(f"  {len(run_df)} runs with burst events")

    # aggregate to subject
    num_cols = [c for c in run_df.columns
                if c not in {"subject","cpc","source","pooled_subject"}
                and run_df[c].dtype.kind in "if"]
    agg = {c: "median" for c in num_cols}
    agg.update({"subject":"first","cpc":"first","source":"first"})
    subj_df = run_df.groupby("pooled_subject", as_index=False).agg(agg)
    n1 = int((subj_df.cpc == GOOD_CPC).sum())
    n5 = int((subj_df.cpc == POOR_CPC).sum())
    print(f"  {len(subj_df)} subjects ({n1} CPC1, {n5} CPC5)")

    subj_df.to_csv(out / "sbeg_mnps_subjects.csv", index=False)
    contrast = build_contrast(subj_df)
    contrast.to_csv(out / "sbeg_mnps_contrast.csv", index=False)

    print(f"\nTop contrasts (sorted by |d|):")
    print(f"  {'Metric':<35} {'d':>7}  {'p':>9}  {'AUROC':>6}  n(1/5)")
    for _, r in contrast.head(20).iterrows():
        eff_auroc = r['auroc'] if r['auroc'] >= 0.5 else 1 - r['auroc']
        flag = " *" if r["p"] < 0.05 else ""
        print(f"  {r['metric']:<35} {r['d']:>+7.3f}  {r['p']:>9.3g}  {eff_auroc:>6.3f}{flag}  {r['n1']}/{r['n5']}")

    # Separate SBEG-evoked vs run-level vs pre-zone
    print(f"\n-- Evoked (E_*) metrics only --")
    evoked = contrast[contrast.metric.str.startswith("E_")]
    for _, r in evoked.iterrows():
        eff = r["auroc"] if r["auroc"] >= 0.5 else 1-r["auroc"]
        print(f"  {r['metric']:<35} d={r['d']:+.3f}  p={r['p']:.3g}  eff_AUROC={eff:.3f}")

    print(f"\n-- Recovery (R_*) metrics only --")
    recovery = contrast[contrast.metric.str.startswith("R_")]
    for _, r in recovery.iterrows():
        eff = r["auroc"] if r["auroc"] >= 0.5 else 1-r["auroc"]
        print(f"  {r['metric']:<35} d={r['d']:+.3f}  p={r['p']:.3g}  eff_AUROC={eff:.3f}")

    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
