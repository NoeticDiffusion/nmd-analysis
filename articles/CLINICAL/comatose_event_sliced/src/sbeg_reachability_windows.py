"""
sbeg_reachability_windows.py — classical reachability proxies in peri-event windows.

Uses kNN neighbourhood (nn/indices) to compute per-window local covariance metrics:
  local_log_det   = log(det(Sigma_knn))   ~ reachability volume
  local_min_eig   = min eigenvalue(Sigma) ~ tube_d_eff proxy
  local_log_eig_var = var(log eigenvalues) ~ anisotropy / log_eig_var

Also reads:
  condition_number  = jacobian/diagnostics/condition_number_windows  (already per window)
  mnps_dot_speed    = ||mnps_3d_dot||_2   (direct velocity, not finite-difference)

All evaluated in pre/peak/recovery zones around burst-onsets,
and also as run-level medians (for comparison).
"""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from scipy.special import ndtri
from sklearn.metrics import roc_auc_score

ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT   = ARTICLE_DIR.parents[2]

DEFAULT_PROCESSED_ROOTS = (
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260605_202236",
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260605_210700",
)
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "sbeg_reachability_20260607_smoke"

GOOD_CPC = 1
POOR_CPC = 5
EPS = 1e-9
WINDOW_SEC_FALLBACK = 4.0
K_NEIGHBORS = 10   # subset of 20 stored neighbours to use for local covariance

# Detector params (same as SBEG)
Q_SUPPRESS = 0.25; Q_ACTIVE = 0.60; L_SUP_WIN = 5; L_ACT_WIN = 3
P_SUP = 0.80; P_ACT = 0.67; T_REF_SEC = 60.0

PRE_START_SEC = -60.0; PEAK_END_SEC = 30.0; REC_END_SEC = 120.0


def window_duration(t: np.ndarray) -> float:
    t = t[np.isfinite(t)]
    if t.size < 2: return WINDOW_SEC_FALLBACK
    d = np.diff(t); d = d[(d > 0) & np.isfinite(d)]
    return float(np.median(d)) if d.size else WINDOW_SEC_FALLBACK

def rank_z(v: np.ndarray) -> np.ndarray:
    n = v.size; r = np.argsort(np.argsort(v)) + 1
    return ndtri((r - 0.5) / n)

def safe_med(a) -> float:
    v = np.asarray(a, dtype=float); v = v[np.isfinite(v)]
    return float(np.median(v)) if v.size else float("nan")

def infer_cohort(root: Path) -> str:
    n = root.name.lower()
    if "part1" in n or "202236" in n: return "part1"
    if "part2" in n or "210700" in n: return "part2"
    return root.name

# ── activity score & burst detection ────────────────────────────────────────
def activity_score(raw: np.ndarray, names: list[str]) -> np.ndarray:
    pw = ("delta","theta","alpha","beta","gamma","highfreq","power","bandpower","relative","broadband")
    mw = ("hjorth_mobility","mobility")
    ew = ("permutation_entropy","sample_entropy","entropy","hjorth_complexity","complexity")
    pi = [i for i,n in enumerate(names) if any(k in n.lower() for k in pw)]
    mi = [i for i,n in enumerate(names) if any(k in n.lower() for k in mw)]
    ei = [i for i,n in enumerate(names) if any(k in n.lower() for k in ew)]
    me = set(mi+ei); pi = [i for i in pi if i not in me]
    if not pi: pi = list(range(len(names)))
    ps = np.nanmean(np.log1p(np.abs(raw[:,pi])), axis=1)
    ps[~np.isfinite(ps)] = 0.0
    act = 0.50 * rank_z(ps)
    act += 0.25 * rank_z(np.nanmedian(raw[:,mi], axis=1) if mi else ps)
    act += 0.25 * rank_z(np.nanmedian(raw[:,ei], axis=1) if ei else ps)
    return act

def detect_onsets(act: np.ndarray, ws: float) -> list[int]:
    T = len(act); q_s = float(np.quantile(act, Q_SUPPRESS)); q_u = float(np.quantile(act, Q_ACTIVE))
    S = act <= q_s; U = act >= q_u
    ref = max(1, int(np.ceil(T_REF_SEC/ws))); onsets=[]; last=-ref-1
    for k in range(L_SUP_WIN, T-L_ACT_WIN):
        if k-last < ref: continue
        if np.mean(S[k-L_SUP_WIN:k]) >= P_SUP and np.mean(U[k:k+L_ACT_WIN]) >= P_ACT:
            onsets.append(k); last=k
    return onsets

# ── per-window reachability proxies ─────────────────────────────────────────
def local_cov_metrics(coords: np.ndarray, nn_idx: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Vectorised per-window local covariance from k nearest neighbours.
    Returns: log_det, min_eig, log_eig_var  (each shape T)
    """
    T, D = coords.shape
    k = min(k, nn_idx.shape[1])

    # Guard: replace non-finite coords with NaN
    coords_f = coords.copy()
    coords_f[~np.isfinite(coords_f)] = np.nan

    # Gather neighbour coords: (T, k, D)
    nbr_pts  = coords_f[nn_idx[:T, :k]]          # may contain nan
    self_pts = coords_f[:, np.newaxis, :]         # (T, 1, D)
    all_pts  = np.concatenate([self_pts, nbr_pts], axis=1)  # (T, k+1, D)

    # Per-window mean (nanmean over k+1 neighbours)
    mu       = np.nanmean(all_pts, axis=1, keepdims=True)    # (T, 1, D)
    centered = all_pts - mu                                   # (T, k+1, D)
    # Replace remaining NaN with 0 so they don't contribute
    centered = np.where(np.isfinite(centered), centered, 0.0)

    # Sigma = (1/k) * centeredᵀ @ centered  →  (T, D, D)
    Sigma = np.einsum("tnd,tne->tde", centered, centered) / max(1, k)

    # Batch eigendecomposition
    try:
        eigvals = np.linalg.eigvalsh(Sigma)   # (T, D) — sorted ascending
    except np.linalg.LinAlgError:
        return np.full(T, np.nan), np.full(T, np.nan), np.full(T, np.nan)

    # Clamp tiny negatives from numerical noise
    eigvals = np.clip(eigvals, 1e-12, None)

    log_det = np.sum(np.log(eigvals), axis=1)           # (T,)
    min_eig  = eigvals[:, 0]                             # smallest (T,)
    with np.errstate(invalid="ignore"):
        lev_var  = np.var(np.log(eigvals), axis=1)       # (T,)

    # Mark windows where coords were fully NaN as NaN
    all_nan_mask = ~np.isfinite(coords_f).any(axis=1)
    log_det[all_nan_mask] = np.nan
    min_eig[all_nan_mask] = np.nan
    lev_var[all_nan_mask] = np.nan

    return log_det, min_eig, lev_var

# ── peri-event zone median ───────────────────────────────────────────────────
def zone_med(seq, onset, start_s, end_s, ws, T) -> float:
    s = max(0, onset + int(np.floor(start_s/ws)))
    e = min(T, onset + int(np.ceil(end_s/ws)) + 1)
    return safe_med(seq[s:e]) if e > s else float("nan")

ZONES = [
    ("pre",   PRE_START_SEC, 0.0),
    ("peak",  0.0,           PEAK_END_SEC),
    ("rec",   PEAK_END_SEC,  REC_END_SEC),
]

# ── main run processing ──────────────────────────────────────────────────────
def process_run(h5_path: Path) -> dict[str, Any] | None:
    try:
        with h5py.File(h5_path, "r") as f:
            subject  = str(f.attrs.get("subject_id","")).strip()
            cpc      = int(f.attrs.get("meta_cpc",-1))
            mnps     = np.asarray(f["/mnps_3d"][:], dtype=float)
            raw_feat = np.asarray(f["/features_raw/values"][:], dtype=float)
            nn_idx   = np.asarray(f["/nn/indices"][:], dtype=int)
            time_arr = np.asarray(f["/time"][:], dtype=float) if "/time" in f else np.array([])
            feat_names = ([n.decode() if isinstance(n,bytes) else str(n)
                           for n in f["/features_raw/names"][:]]
                          if "/features_raw/names" in f
                          else [f"feat_{i}" for i in range(raw_feat.shape[1])])
            # Optional datasets
            cond_num = (np.asarray(f["/jacobian/diagnostics/condition_number_windows"][:], dtype=float)
                        if "/jacobian/diagnostics/condition_number_windows" in f else None)
            mnps_dot = (np.asarray(f["/mnps_3d_dot"][:], dtype=float)
                        if "/mnps_3d_dot" in f else None)
    except Exception:
        return None

    if cpc not in (GOOD_CPC, POOR_CPC) or not subject:
        return None
    T = mnps.shape[0]
    if T < 20:
        return None
    ws = window_duration(time_arr)

    # Activity score + onsets
    act = activity_score(raw_feat, feat_names)
    onsets = detect_onsets(act, ws)
    if not onsets:
        return None

    # Compute per-window sequences
    log_det, min_eig, lev_var = local_cov_metrics(mnps, nn_idx[:T], K_NEIGHBORS)

    # MNPS dot speed
    if mnps_dot is not None:
        dot_speed = np.sqrt(np.sum(mnps_dot[:T]**2, axis=1))
    else:
        dot_speed = np.full(T, np.nan)

    # Condition number (align to T; jacobian has T-2 centers)
    if cond_num is not None:
        cn_full = np.full(T, np.nan)
        cn_full[:min(len(cond_num), T)] = cond_num[:T]
        cond_seq = np.log1p(cn_full)  # log-condition for stability
    else:
        cond_seq = np.full(T, np.nan)

    seqs = {
        "local_log_det": log_det,
        "local_min_eig": min_eig,
        "local_lev_var": lev_var,
        "dot_speed": dot_speed,
        "log_cond": cond_seq,
    }

    # Aggregate per event
    event_rows: list[dict[str, float]] = []
    for onset in onsets:
        row: dict[str, float] = {}
        for sname, seq in seqs.items():
            mad = safe_med(np.abs(seq[np.isfinite(seq)] - np.nanmedian(seq[np.isfinite(seq)])))
            for zname, zs, ze in ZONES:
                v = zone_med(seq, onset, zs, ze, ws, T)
                row[f"{zname}_{sname}"] = v
            pre  = row[f"pre_{sname}"]
            peak = row[f"peak_{sname}"]
            rec  = row[f"rec_{sname}"]
            if all(np.isfinite([pre, peak, rec])):
                row[f"E_{sname}"] = (peak - pre) / (mad + EPS)
                row[f"R_{sname}"] = abs(rec - pre) / (mad + EPS)
            else:
                row[f"E_{sname}"] = float("nan")
                row[f"R_{sname}"] = float("nan")
        event_rows.append(row)

    # Subject-level aggregation from events
    agg: dict[str, Any] = {"subject": subject, "cpc": cpc,
                            "cohort": infer_cohort(h5_path.parent),
                            "n_events": float(len(event_rows))}
    for key in event_rows[0]:
        agg[key] = safe_med([r[key] for r in event_rows])

    # Run-level medians (baseline)
    for sname, seq in seqs.items():
        agg[f"run_med_{sname}"] = safe_med(seq)

    return agg


def cohens_d(a, b) -> float:
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if a.size < 2 or b.size < 2: return float("nan")
    pool = ((a.size-1)*np.var(a,ddof=1) + (b.size-1)*np.var(b,ddof=1)) / (a.size+b.size-2)
    if not np.isfinite(pool) or pool <= 0: return float("nan")
    return float((np.mean(a)-np.mean(b)) / np.sqrt(pool))

def build_contrast(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    num = [c for c in df.columns if c not in {"subject","cpc","cohort"}
           and df[c].dtype.kind in "if"]
    for col in num:
        g = df.loc[df.cpc==GOOD_CPC, col].dropna().to_numpy(float)
        p = df.loc[df.cpc==POOR_CPC, col].dropna().to_numpy(float)
        if g.size < 4 or p.size < 4: continue
        mw = mannwhitneyu(g, p, alternative="two-sided")
        d  = cohens_d(g, p)
        try:
            au = float(roc_auc_score(np.concatenate([np.ones(g.size),np.zeros(p.size)]),
                                     np.concatenate([g, p])))
        except: au = float("nan")
        rows.append({"metric":col, "d":d, "abs_d":abs(d) if np.isfinite(d) else float("nan"),
                     "p":float(mw.pvalue), "auroc":au, "n1":int(g.size), "n5":int(p.size),
                     "cpc1_med":safe_med(g), "cpc5_med":safe_med(p)})
    if not rows: return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("abs_d", ascending=False).reset_index(drop=True)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--processed-root", dest="roots", action="append", type=Path)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--max-subjects-per-class", type=int, default=None)
    return p.parse_args()


def main():
    args = parse_args()
    roots = tuple(args.roots) if args.roots else DEFAULT_PROCESSED_ROOTS
    out   = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    counts = {GOOD_CPC: 0, POOR_CPC: 0}
    seen: set[str] = set()

    for root in roots:
        cohort = infer_cohort(root)
        if not root.exists():
            print(f"  WARNING: {root} not found"); continue
        h5s = sorted(root.rglob("*.h5"))
        print(f"  {cohort}: {len(h5s)} H5 files")
        for h5 in h5s:
            try:
                with h5py.File(h5,"r") as f:
                    cpc = int(f.attrs.get("meta_cpc",-1))
                    subj = str(f.attrs.get("subject_id","")).strip()
            except: continue
            if cpc not in (GOOD_CPC, POOR_CPC) or not subj: continue
            key = f"{cohort}::{subj}"
            if key not in seen:
                if args.max_subjects_per_class and counts[cpc] >= args.max_subjects_per_class:
                    continue
                seen.add(key); counts[cpc] += 1
            r = process_run(h5)
            if r is not None:
                r["pooled_subject"] = key; rows.append(r)

    if not rows: raise RuntimeError("No runs processed.")

    run_df = pd.DataFrame(rows)
    print(f"  {len(run_df)} valid runs (with burst events)")

    num = [c for c in run_df.columns if c not in {"subject","cpc","cohort","pooled_subject"}
           and run_df[c].dtype.kind in "if"]
    agg = {c:"median" for c in num}
    agg.update({"subject":"first","cpc":"first","cohort":"first"})
    subj_df = run_df.groupby("pooled_subject", as_index=False).agg(agg)
    n1 = int((subj_df.cpc==GOOD_CPC).sum()); n5 = int((subj_df.cpc==POOR_CPC).sum())
    print(f"  {len(subj_df)} subjects  ({n1} CPC1, {n5} CPC5)")

    subj_df.to_csv(out/"reachability_subjects.csv", index=False)
    contrast = build_contrast(subj_df)
    contrast.to_csv(out/"reachability_contrast.csv", index=False)

    print(f"\nTop contrasts:")
    print(f"  {'Metric':<35} {'d':>7}  {'p':>9}  {'eff.AUROC':>9}")
    for _, r in contrast.head(20).iterrows():
        eff = r["auroc"] if r["auroc"]>=0.5 else 1-r["auroc"]
        sig = " *" if r["p"] < 0.05 else ("†" if r["p"] < 0.10 else "")
        print(f"  {r['metric']:<35} {r['d']:>+7.3f}  {r['p']:>9.3g}  {eff:>9.3f}{sig}")

    # Grouped summaries
    for prefix, label in [("run_med","Run-level baselines"),
                           ("E_","Evoked (peak-pre)"),
                           ("R_","Recovery residuals"),
                           ("pre_","Pre-zone snapshots"),
                           ("peak_","Peak-zone snapshots")]:
        sub = contrast[contrast.metric.str.startswith(prefix)]
        if sub.empty: continue
        print(f"\n-- {label} --")
        for _, r in sub.iterrows():
            eff = r["auroc"] if r["auroc"]>=0.5 else 1-r["auroc"]
            sig = " *" if r["p"] < 0.05 else ("†" if r["p"] < 0.10 else "")
            print(f"  {r['metric']:<35} d={r['d']:+.3f}  p={r['p']:.3g}  AUROC={eff:.3f}{sig}")

    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
