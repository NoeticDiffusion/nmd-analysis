"""
run_sbeg_detector.py — Spontaneous Burst-Evoked Geometry (SBEG) analysis.

Implements the minimal first specification from ideas.md (section 10):

  Detector:
    A_k = 0.5 * rank_z(log broadband power)
        + 0.25 * rank_z(Hjorth mobility)
        + 0.25 * rank_z(Hjorth complexity / entropy)
    Suppression = A_k <= q25(A)    [bottom 25th percentile]
    Active      = A_k >= q60(A)    [top 40th percentile]

  Burst-onset events:
    mean(S_{k-L_s : k-1}) >= p_s   (L_s = 5 windows, ~20 s)
    mean(U_{k : k+L_a})   >= p_a   (L_a = 3 windows, ~12 s)
    refractory period T_ref = 60 s

  Peri-event zones (relative to burst-onset):
    pre  = [-60 s,    0)
    peak = [  0 s,  +30 s]
    rec  = [+30 s, +120 s]

  Geometry metrics:
    lambda_k  = spectral_radius(J_k)         3D Jacobian
    F_k       = ||J_k||_F                    Frobenius norm
    z_k       = MNPS 3D coords

  Per-event evoked measures:
    E_lambda = (lambda_peak - lambda_pre)  / (MAD_run(lambda) + eps)
    E_F      = (F_peak      - F_pre)       / (MAD_run(F)      + eps)
    R_lambda = |lambda_rec  - lambda_pre|  / (MAD_run(lambda) + eps)
    R_F      = |F_rec       - F_pre|       / (MAD_run(F)      + eps)
    SBEG_recovery = E_lambda + E_F + R_lambda + R_F
    H_CD = shoelace hysteresis area in (-F, lambda) plane
    R_CD = ||median(p_rec) - median(p_pre)||_2

  Patient-level:
    SBEG_i        = median over events
    EventRate_i   = N_events / duration_min
    NoBurst_i     = 1 if no events detected

  Nulls:
    circular-shift null: shift event times, recompute per-run, compare

Usage
-----
  python run_sbeg_detector.py \\
      --processed-root J:/repos/.../neuralmanifolddynamics_physionet_icare_2_1_20260605_202236 \\
      --processed-root J:/repos/.../neuralmanifolddynamics_physionet_icare_2_1_20260605_210700 \\
      --output-dir     J:/repos/.../comatose_event_sliced/results/sbeg_20260607_fullcohort
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
REPO_ROOT = ARTICLE_DIR.parents[2]

DEFAULT_PROCESSED_ROOTS = (
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260605_202236",
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260605_210700",
)
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "sbeg_20260607_fullcohort"

GOOD_CPC = 1
POOR_CPC = 5
WINDOW_SEC_FALLBACK = 4.0

# Detector parameters (from ideas.md section 10)
DEFAULT_Q_SUPPRESS = 0.25    # bottom quartile = suppression
DEFAULT_Q_ACTIVE   = 0.60    # top 40% = active
DEFAULT_L_SUP_WIN  = 5       # min suppression windows before onset
DEFAULT_L_ACT_WIN  = 3       # min active windows after onset
DEFAULT_P_SUP      = 0.80    # fraction of L_s windows in suppression
DEFAULT_P_ACT      = 0.67    # fraction of L_a windows in active
DEFAULT_T_REF_SEC  = 60.0    # refractory period (seconds)

# Peri-event zones (seconds, relative to burst-onset)
PRE_START_SEC  = -60.0
PRE_END_SEC    = 0.0
PEAK_START_SEC = 0.0
PEAK_END_SEC   = 30.0
REC_START_SEC  = 30.0
REC_END_SEC    = 120.0

# Activity score weights
W_POWER  = 0.50
W_MOBILE = 0.25
W_ENTROPY= 0.25

EPS = 1e-9
NULL_SHIFTS = 500   # circular-shift null iterations


@dataclass(frozen=True)
class Config:
    processed_roots: tuple[Path, ...]
    output_dir: Path
    good_cpc: int
    poor_cpc: int
    q_suppress: float
    q_active: float
    l_sup_win: int
    l_act_win: int
    p_sup: float
    p_act: float
    t_ref_sec: float
    min_events_for_sbeg: int
    max_subjects_per_class: int | None
    run_null: bool


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def infer_source_cohort(root: Path) -> str:
    name = root.name.lower()
    if "part1" in name or "202236" in name:
        return "part1"
    if "part2" in name or "210700" in name:
        return "part2"
    return root.name


def window_duration(time_arr: np.ndarray) -> float:
    arr = np.asarray(time_arr, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size < 2:
        return WINDOW_SEC_FALLBACK
    diffs = np.diff(arr)
    diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
    return float(np.median(diffs)) if diffs.size else WINDOW_SEC_FALLBACK


def rank_z(values: np.ndarray) -> np.ndarray:
    """Rank-based normal scores (probit transform of rank / n)."""
    arr = np.asarray(values, dtype=float)
    n = arr.size
    ranks = np.argsort(np.argsort(arr)) + 1  # 1-based ranks
    # Phi^{-1}((rank - 0.5) / n)
    from scipy.special import ndtri
    return ndtri((ranks - 0.5) / n)


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    g = good[np.isfinite(good)]
    p = poor[np.isfinite(poor)]
    if g.size < 2 or p.size < 2:
        return float("nan")
    pooled = ((g.size - 1) * np.var(g, ddof=1) + (p.size - 1) * np.var(p, ddof=1)) / (g.size + p.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(g) - np.mean(p)) / np.sqrt(pooled))


def safe_nanmedian(arr: np.ndarray | list) -> float:
    a = np.asarray(arr, dtype=float)
    a = a[np.isfinite(a)]
    return float(np.median(a)) if a.size else float("nan")


def safe_nanmad(arr: np.ndarray | list) -> float:
    a = np.asarray(arr, dtype=float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return float("nan")
    return float(np.median(np.abs(a - np.median(a))))


# ---------------------------------------------------------------------------
# Feature identification helpers
# ---------------------------------------------------------------------------
def find_feature_indices(names: list[str]) -> tuple[list[int], list[int], list[int]]:
    """
    Return (power_idxs, mobility_idxs, entropy_idxs) from feature name list.
    Fallback: if no mobility/entropy found, returns empty lists.
    """
    power_kw = ("delta", "theta", "alpha", "beta", "gamma", "highfreq",
                 "power", "bandpower", "relative", "broadband")
    mobile_kw = ("hjorth_mobility", "mobility")
    entropy_kw = ("permutation_entropy", "sample_entropy", "entropy",
                   "hjorth_complexity", "complexity")

    power_idxs = [i for i, n in enumerate(names) if any(k in n.lower() for k in power_kw)]
    mobile_idxs = [i for i, n in enumerate(names) if any(k in n.lower() for k in mobile_kw)]
    entropy_idxs = [i for i, n in enumerate(names) if any(k in n.lower() for k in entropy_kw)]

    # Avoid counting mobility/entropy features as power features
    mobile_entropy_set = set(mobile_idxs + entropy_idxs)
    power_idxs = [i for i in power_idxs if i not in mobile_entropy_set]

    # Fallback: use all features if nothing specific found
    if not power_idxs:
        power_idxs = list(range(len(names)))

    return power_idxs, mobile_idxs, entropy_idxs


# ---------------------------------------------------------------------------
# Activity score computation
# ---------------------------------------------------------------------------
def compute_activity_score(
    raw_features: np.ndarray,
    feature_names: list[str],
) -> np.ndarray:
    """
    A_k = 0.5 * rank_z(mean_j log(1 + |u_{k,j}|) for j in power)
        + 0.25 * rank_z(Hjorth_mobility_k)
        + 0.25 * rank_z(entropy_k)
    """
    T = raw_features.shape[0]
    power_idxs, mobile_idxs, entropy_idxs = find_feature_indices(feature_names)

    # Power component: mean over log-transformed power features
    power_mat = np.log1p(np.abs(raw_features[:, power_idxs]))
    power_score = np.nanmean(power_mat, axis=1)
    power_score[~np.isfinite(power_score)] = np.nanmedian(power_score[np.isfinite(power_score)]) if np.isfinite(power_score).any() else 0.0
    activity = W_POWER * rank_z(power_score)

    if mobile_idxs:
        mob = np.nanmedian(raw_features[:, mobile_idxs], axis=1)
        mob[~np.isfinite(mob)] = np.nanmedian(mob[np.isfinite(mob)]) if np.isfinite(mob).any() else 0.0
        activity += W_MOBILE * rank_z(mob)
    else:
        # redistribute weight to power
        activity += W_MOBILE * rank_z(power_score)

    if entropy_idxs:
        ent = np.nanmedian(raw_features[:, entropy_idxs], axis=1)
        ent[~np.isfinite(ent)] = np.nanmedian(ent[np.isfinite(ent)]) if np.isfinite(ent).any() else 0.0
        activity += W_ENTROPY * rank_z(ent)
    else:
        activity += W_ENTROPY * rank_z(power_score)

    return activity


# ---------------------------------------------------------------------------
# Burst-onset detection
# ---------------------------------------------------------------------------
def detect_burst_onsets(
    activity: np.ndarray,
    window_sec: float,
    *,
    q_suppress: float,
    q_active: float,
    l_sup_win: int,
    l_act_win: int,
    p_sup: float,
    p_act: float,
    t_ref_sec: float,
) -> list[int]:
    """
    Returns list of window indices where burst onset (suppression→active) detected.
    """
    T = len(activity)
    q_s = float(np.quantile(activity, q_suppress))
    q_u = float(np.quantile(activity, q_active))

    suppress_mask = activity <= q_s   # S_k
    active_mask   = activity >= q_u   # U_k

    t_ref_wins = max(1, int(np.ceil(t_ref_sec / window_sec)))
    onsets: list[int] = []
    last_onset = -t_ref_wins - 1

    for k in range(l_sup_win, T - l_act_win):
        if k - last_onset < t_ref_wins:
            continue
        pre_sup_frac = float(np.mean(suppress_mask[k - l_sup_win : k]))
        post_act_frac = float(np.mean(active_mask[k : k + l_act_win]))
        if pre_sup_frac >= p_sup and post_act_frac >= p_act:
            onsets.append(k)
            last_onset = k

    return onsets


# ---------------------------------------------------------------------------
# Jacobian geometry
# ---------------------------------------------------------------------------
def spectral_radius_seq(jacobian: np.ndarray) -> np.ndarray:
    out = np.full(len(jacobian), np.nan)
    for i, J in enumerate(jacobian):
        if not np.isfinite(J).all():
            continue
        try:
            out[i] = float(np.max(np.abs(np.linalg.eigvals(J))))
        except np.linalg.LinAlgError:
            pass
    return out


def frobenius_seq(jacobian: np.ndarray) -> np.ndarray:
    out = np.full(len(jacobian), np.nan)
    for i, J in enumerate(jacobian):
        if not np.isfinite(J).all():
            continue
        out[i] = float(np.linalg.norm(J, "fro"))
    return out


# ---------------------------------------------------------------------------
# Peri-event feature extraction
# ---------------------------------------------------------------------------
def peri_event_features(
    onset_idx: int,
    lambda_seq: np.ndarray,
    frob_seq: np.ndarray,
    window_sec: float,
) -> dict[str, float] | None:
    T = len(lambda_seq)

    # Window index ranges for each zone
    pre_start  = max(0, onset_idx + int(np.floor(PRE_START_SEC  / window_sec)))
    pre_end    = onset_idx + int(np.floor(PRE_END_SEC    / window_sec))
    peak_start = onset_idx + int(np.floor(PEAK_START_SEC / window_sec))
    peak_end   = min(T, onset_idx + int(np.ceil(PEAK_END_SEC  / window_sec)) + 1)
    rec_start  = onset_idx + int(np.floor(REC_START_SEC  / window_sec))
    rec_end    = min(T, onset_idx + int(np.ceil(REC_END_SEC   / window_sec)) + 1)

    # Clamp indices
    pre_end = min(pre_end, T)
    peak_end = min(peak_end, T)
    rec_end = min(rec_end, T)

    # Need at least 1 window in each zone
    if pre_end <= pre_start or peak_end <= peak_start or rec_end <= rec_start:
        return None

    lam_pre  = safe_nanmedian(lambda_seq[pre_start : pre_end])
    lam_peak = safe_nanmedian(lambda_seq[peak_start : peak_end])
    lam_rec  = safe_nanmedian(lambda_seq[rec_start  : rec_end])

    frob_pre  = safe_nanmedian(frob_seq[pre_start : pre_end])
    frob_peak = safe_nanmedian(frob_seq[peak_start : peak_end])
    frob_rec  = safe_nanmedian(frob_seq[rec_start  : rec_end])

    if any(not np.isfinite(v) for v in [lam_pre, lam_peak, lam_rec, frob_pre, frob_peak, frob_rec]):
        return None

    # Run-level MAD for normalisation (using the available sequence)
    lam_mad  = safe_nanmad(lambda_seq)
    frob_mad = safe_nanmad(frob_seq)

    E_lam  = (lam_peak  - lam_pre)  / (lam_mad  + EPS)
    E_frob = (frob_peak - frob_pre) / (frob_mad + EPS)
    R_lam  = abs(lam_rec  - lam_pre)  / (lam_mad  + EPS)
    R_frob = abs(frob_rec - frob_pre) / (frob_mad + EPS)

    sbeg_recovery = E_lam + E_frob + R_lam + R_frob

    # Hysteresis area in (C, D) plane: C = -frobenius, D = spectral_radius
    all_start = pre_start
    all_end   = rec_end
    C_path = -frob_seq[all_start : all_end]
    D_path = lambda_seq[all_start : all_end]
    valid  = np.isfinite(C_path) & np.isfinite(D_path)
    C_v, D_v = C_path[valid], D_path[valid]
    if len(C_v) >= 3:
        # Shoelace formula
        H_CD = 0.5 * abs(float(np.sum(C_v[:-1] * D_v[1:] - C_v[1:] * D_v[:-1])))
    else:
        H_CD = float("nan")

    # Recovery residual in plane
    p_pre_C  = safe_nanmedian(C_path[:max(1, pre_end - pre_start)])
    p_pre_D  = safe_nanmedian(D_path[:max(1, pre_end - pre_start)])
    rec_off  = rec_start - all_start
    p_rec_C  = safe_nanmedian(C_path[rec_off:])
    p_rec_D  = safe_nanmedian(D_path[rec_off:])
    if all(np.isfinite(v) for v in [p_pre_C, p_pre_D, p_rec_C, p_rec_D]):
        R_CD = float(np.sqrt((p_rec_C - p_pre_C) ** 2 + (p_rec_D - p_pre_D) ** 2))
    else:
        R_CD = float("nan")

    return {
        "E_lambda": E_lam,
        "E_frobenius": E_frob,
        "R_lambda": R_lam,
        "R_frobenius": R_frob,
        "sbeg_recovery": sbeg_recovery,
        "H_CD": H_CD,
        "R_CD": R_CD,
        "lambda_pre": lam_pre,
        "lambda_peak": lam_peak,
        "lambda_rec": lam_rec,
        "frob_pre": frob_pre,
        "frob_peak": frob_peak,
        "frob_rec": frob_rec,
    }


# ---------------------------------------------------------------------------
# Per-run processing
# ---------------------------------------------------------------------------
def process_run(
    h5_path: Path,
    config: Config,
) -> dict[str, Any] | None:
    try:
        with h5py.File(h5_path, "r") as f:
            subject  = str(f.attrs.get("subject_id", "")).strip()
            cpc      = int(f.attrs.get("meta_cpc", -1))
            mnps     = np.asarray(f["/mnps_3d"][:], dtype=float)
            raw_feat = np.asarray(f["/features_raw/values"][:], dtype=float)
            jacobian = np.asarray(f["/jacobian/J_hat"][:], dtype=float)
            time_arr = np.asarray(f["/time"][:], dtype=float) if "/time" in f else np.array([])
            # feature names
            if "/features_raw/names" in f:
                feat_names = [n.decode() if isinstance(n, bytes) else str(n)
                              for n in f["/features_raw/names"][:]]
            else:
                feat_names = [f"feat_{i}" for i in range(raw_feat.shape[1])]
    except Exception:
        return None

    if cpc not in (config.good_cpc, config.poor_cpc) or not subject:
        return None

    T = mnps.shape[0]
    if T < 20:
        return None

    ws = window_duration(time_arr)
    duration_min = T * ws / 60.0

    # Align jacobian to mnps length
    J = jacobian[: min(len(jacobian), T)]
    lambda_seq = spectral_radius_seq(J)
    frob_seq   = frobenius_seq(J)

    # Activity score
    activity = compute_activity_score(raw_feat, feat_names)

    # Burst onsets
    onsets = detect_burst_onsets(
        activity, ws,
        q_suppress=config.q_suppress,
        q_active=config.q_active,
        l_sup_win=config.l_sup_win,
        l_act_win=config.l_act_win,
        p_sup=config.p_sup,
        p_act=config.p_act,
        t_ref_sec=config.t_ref_sec,
    )

    event_rows: list[dict[str, Any]] = []
    for onset_idx in onsets:
        ev = peri_event_features(onset_idx, lambda_seq, frob_seq, ws)
        if ev is not None:
            ev["onset_window"] = onset_idx
            ev["onset_sec"]    = float(onset_idx * ws)
            event_rows.append(ev)

    n_events = len(event_rows)
    no_burst = int(n_events == 0)

    # Aggregate event-level to run-level
    sbeg_recovery = safe_nanmedian([r["sbeg_recovery"] for r in event_rows])
    sbeg_p95 = float(np.nanpercentile([r["sbeg_recovery"] for r in event_rows], 95)) if event_rows else float("nan")
    H_CD_med  = safe_nanmedian([r["H_CD"] for r in event_rows])
    R_CD_med  = safe_nanmedian([r["R_CD"] for r in event_rows])
    E_lam_med = safe_nanmedian([r["E_lambda"] for r in event_rows])
    E_frob_med= safe_nanmedian([r["E_frobenius"] for r in event_rows])
    R_lam_med = safe_nanmedian([r["R_lambda"] for r in event_rows])
    R_frob_med= safe_nanmedian([r["R_frobenius"] for r in event_rows])
    event_rate = float(n_events / duration_min) if duration_min > 0 else float("nan")

    # Circular-shift null (run-level: shift onsets by half-duration)
    null_sbeg: float = float("nan")
    if config.run_null and n_events >= 2:
        shift_wins = int(T / 2)
        shifted_onsets = [(o + shift_wins) % T for o in onsets]
        null_evs = []
        for oi in shifted_onsets:
            ev = peri_event_features(oi, lambda_seq, frob_seq, ws)
            if ev is not None:
                null_evs.append(ev["sbeg_recovery"])
        null_sbeg = safe_nanmedian(null_evs)

    return {
        "subject": subject,
        "cpc": cpc,
        "label": int(cpc == config.poor_cpc),
        "h5_path": str(h5_path),
        "n_windows": T,
        "window_sec": ws,
        "duration_min": duration_min,
        "n_events": n_events,
        "no_burst": no_burst,
        "event_rate_per_min": event_rate,
        "sbeg_recovery": sbeg_recovery,
        "sbeg_p95": sbeg_p95,
        "H_CD": H_CD_med,
        "R_CD": R_CD_med,
        "E_lambda": E_lam_med,
        "E_frobenius": E_frob_med,
        "R_lambda": R_lam_med,
        "R_frobenius": R_frob_med,
        "run_median_lambda": safe_nanmedian(lambda_seq),
        "run_median_frob": safe_nanmedian(frob_seq),
        "null_sbeg": null_sbeg,
    }


# ---------------------------------------------------------------------------
# Cohort collection and subject aggregation
# ---------------------------------------------------------------------------
def collect_and_process(config: Config) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    subject_counts: dict[int, int] = {config.good_cpc: 0, config.poor_cpc: 0}
    selected_subjects: set[str] = set()

    for root in config.processed_roots:
        cohort = infer_source_cohort(root)
        if not root.exists():
            print(f"  WARNING: root not found: {root}")
            continue
        h5_files = sorted(root.rglob("*.h5"))
        print(f"  {cohort}: {len(h5_files)} H5 files")
        for h5 in h5_files:
            try:
                with h5py.File(h5, "r") as f:
                    cpc = int(f.attrs.get("meta_cpc", -1))
                    subj = str(f.attrs.get("subject_id", "")).strip()
            except Exception:
                continue
            if cpc not in (config.good_cpc, config.poor_cpc) or not subj:
                continue
            pooled_subj = f"{cohort}::{subj}"
            if pooled_subj not in selected_subjects:
                if (config.max_subjects_per_class is not None
                        and subject_counts[cpc] >= config.max_subjects_per_class):
                    continue
                selected_subjects.add(pooled_subj)
                subject_counts[cpc] += 1
            result = process_run(h5, config)
            if result is not None:
                result["source_cohort"] = cohort
                result["pooled_subject"] = pooled_subj
                rows.append(result)

    return pd.DataFrame(rows)


def aggregate_to_subjects(run_df: pd.DataFrame) -> pd.DataFrame:
    if run_df.empty:
        return pd.DataFrame()
    numeric_cols = [c for c in run_df.columns
                    if c not in {"source_cohort", "pooled_subject", "subject",
                                 "h5_path", "label"}
                    and run_df[c].dtype.kind in "if"]
    agg = {c: "median" for c in numeric_cols}
    agg.update({"source_cohort": "first", "subject": "first", "h5_path": "first"})
    subj = run_df.groupby(["pooled_subject", "cpc", "label"], as_index=False).agg(agg)
    subj["n_runs"] = run_df.groupby("pooled_subject")["h5_path"].count().reindex(subj["pooled_subject"]).values
    return subj.sort_values("pooled_subject").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Contrast table
# ---------------------------------------------------------------------------
SBEG_METRICS = [
    "sbeg_recovery", "sbeg_p95", "H_CD", "R_CD",
    "E_lambda", "E_frobenius", "R_lambda", "R_frobenius",
    "event_rate_per_min", "no_burst",
    "run_median_lambda", "run_median_frob",
]


def build_contrast(subj_df: pd.DataFrame, *, good_cpc: int, poor_cpc: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for metric in SBEG_METRICS:
        if metric not in subj_df.columns:
            continue
        good = subj_df.loc[subj_df["cpc"] == good_cpc, metric].dropna().to_numpy(dtype=float)
        poor = subj_df.loc[subj_df["cpc"] == poor_cpc, metric].dropna().to_numpy(dtype=float)
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
        rows.append({
            "metric": metric,
            f"cpc{good_cpc}_median": float(np.nanmedian(good)),
            f"cpc{poor_cpc}_median": float(np.nanmedian(poor)),
            "cohens_d": d,
            "abs_d": abs(d) if np.isfinite(d) else float("nan"),
            "mw_p": float(mw.pvalue),
            "auroc": auroc,
            f"n_cpc{good_cpc}": int(good.size),
            f"n_cpc{poor_cpc}": int(poor.size),
        })
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("abs_d", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Null analysis (population-level circular shift)
# ---------------------------------------------------------------------------
def null_contrast(
    subj_df: pd.DataFrame,
    *,
    good_cpc: int,
    poor_cpc: int,
    metric: str = "sbeg_recovery",
    n_shifts: int = NULL_SHIFTS,
    rng_seed: int = 42,
) -> dict[str, float]:
    """
    Assess whether observed sbeg_recovery CPC difference exceeds circular-shift null.
    Null: within each run, shift event times by random fraction before aggregating.
    Here we approximate by permuting run-level null_sbeg values.
    """
    if metric not in subj_df.columns or "null_sbeg" not in subj_df.columns:
        return {"observed_d": float("nan"), "null_mean_d": float("nan"), "null_p95_d": float("nan"), "empirical_p": float("nan")}

    good = subj_df.loc[subj_df["cpc"] == good_cpc, metric].dropna().to_numpy(dtype=float)
    poor = subj_df.loc[subj_df["cpc"] == poor_cpc, metric].dropna().to_numpy(dtype=float)
    observed_d = cohens_d(good, poor)

    # Use subject-level null_sbeg; filter to rows that have valid values in both columns
    rng = np.random.default_rng(rng_seed)
    null_ds: list[float] = []
    valid_mask = subj_df["null_sbeg"].notna()
    valid_subj = subj_df[valid_mask]
    all_vals   = valid_subj["null_sbeg"].to_numpy(dtype=float)
    # Match labels to valid_subj rows: 1 if good_cpc, 0 if poor_cpc
    raw_labels = (valid_subj["cpc"] == good_cpc).astype(int).to_numpy()
    if all_vals.size < 4:
        return {"observed_d": observed_d, "null_mean_d": float("nan"), "null_p95_d": float("nan"), "empirical_p": float("nan")}
    for _ in range(n_shifts):
        shuffled_labels = rng.permutation(raw_labels)
        ng  = all_vals[shuffled_labels == 1]
        np_ = all_vals[shuffled_labels == 0]
        if ng.size >= 2 and np_.size >= 2:
            null_ds.append(abs(cohens_d(ng, np_)))
    null_arr = np.array(null_ds, dtype=float)
    null_arr = null_arr[np.isfinite(null_arr)]
    if null_arr.size == 0:
        return {"observed_d": observed_d, "null_mean_d": float("nan"), "null_p95_d": float("nan"), "empirical_p": float("nan")}
    empirical_p = float(np.mean(null_arr >= abs(observed_d)))
    return {
        "observed_d": observed_d,
        "null_mean_d": float(np.mean(null_arr)),
        "null_p95_d": float(np.percentile(null_arr, 95)),
        "empirical_p": empirical_p,
    }


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------
def build_markdown(
    contrast: pd.DataFrame,
    null_result: dict[str, float],
    *,
    n_runs: int,
    n_subj: int,
    n_good: int,
    n_poor: int,
    good_cpc: int,
    poor_cpc: int,
    config: Config,
) -> str:
    lines = [
        "# SBEG — Spontaneous Burst-Evoked Geometry",
        "",
        "## Cohort",
        "",
        f"- processed roots: `{len(config.processed_roots)}`",
        f"- runs analyzed: `{n_runs}`",
        f"- subjects analyzed: `{n_subj}`",
        "",
        f"| label | n |",
        f"|---|---:|",
        f"| CPC{good_cpc} | {n_good} |",
        f"| CPC{poor_cpc} | {n_poor} |",
        "",
        "## Detector",
        "",
        "```text",
        f"Activity score:",
        f"  A_k = {W_POWER} * rank_z(log broadband power)",
        f"      + {W_MOBILE} * rank_z(Hjorth mobility)",
        f"      + {W_ENTROPY} * rank_z(entropy / complexity)",
        f"Suppression: A_k <= q{int(config.q_suppress*100)}(A)",
        f"Active:      A_k >= q{int(config.q_active*100)}(A)",
        f"Burst onset: >= {config.l_sup_win} suppression windows before, >= {config.l_act_win} active windows after",
        f"Refractory period: {config.t_ref_sec} s",
        "```",
        "",
        "## Contrast — sorted by |Cohen's d|",
        "",
    ]
    if contrast.empty:
        lines.append("No contrast rows available.")
    else:
        lines.append(f"| Metric | CPC{good_cpc} med | CPC{poor_cpc} med | d | MW p | AUROC | n ({good_cpc}/{poor_cpc}) |")
        lines.append("|---|---|---|---|---|---|---|")
        for _, r in contrast.iterrows():
            lines.append(
                f"| `{r['metric']}` "
                f"| {r[f'cpc{good_cpc}_median']:.4g} "
                f"| {r[f'cpc{poor_cpc}_median']:.4g} "
                f"| {r['cohens_d']:+.3f} "
                f"| {r['mw_p']:.3g} "
                f"| {r['auroc']:.3f} "
                f"| {r[f'n_cpc{good_cpc}']}/{r[f'n_cpc{poor_cpc}']} |"
            )

    lines += ["", "## Circular-shift null (sbeg_recovery)", ""]
    nr = null_result
    lines.append(f"- observed |d| = `{abs(nr.get('observed_d', float('nan'))):.3f}`")
    lines.append(f"- null mean |d| = `{nr.get('null_mean_d', float('nan')):.3f}`")
    lines.append(f"- null p95  |d| = `{nr.get('null_p95_d', float('nan')):.3f}`")
    lines.append(f"- empirical p   = `{nr.get('empirical_p', float('nan')):.4f}`")

    lines += [
        "",
        "## Notes",
        "",
        "- SBEG measures the *shape* of peri-burst geometry: pre → peak → recovery.",
        "- `sbeg_recovery` = E_lambda + E_F + R_lambda + R_F (higher = more evoked deformation / worse recovery).",
        "- `no_burst` = fraction of runs with zero detected burst-onsets.",
        "- `run_median_lambda` = spectral radius median across full run (baseline comparator).",
        "- Per the ideas.md spec, the key hypothesis is that CPC5 shows either absent burst response",
        "  or higher baseline deformation with poor recovery form, not just elevated amplitude.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI and main
# ---------------------------------------------------------------------------
def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="SBEG burst-evoked geometry analysis.")
    parser.add_argument("--processed-root", dest="processed_roots", action="append", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--good-cpc", type=int, default=GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=POOR_CPC)
    parser.add_argument("--q-suppress", type=float, default=DEFAULT_Q_SUPPRESS)
    parser.add_argument("--q-active",   type=float, default=DEFAULT_Q_ACTIVE)
    parser.add_argument("--l-sup-win",  type=int,   default=DEFAULT_L_SUP_WIN)
    parser.add_argument("--l-act-win",  type=int,   default=DEFAULT_L_ACT_WIN)
    parser.add_argument("--p-sup",      type=float, default=DEFAULT_P_SUP)
    parser.add_argument("--p-act",      type=float, default=DEFAULT_P_ACT)
    parser.add_argument("--t-ref-sec",  type=float, default=DEFAULT_T_REF_SEC)
    parser.add_argument("--min-events-for-sbeg", type=int, default=1)
    parser.add_argument("--max-subjects-per-class", type=int, default=None)
    parser.add_argument("--no-null", action="store_true", help="Skip circular-shift null.")
    args = parser.parse_args()
    return Config(
        processed_roots=tuple(args.processed_roots) if args.processed_roots else DEFAULT_PROCESSED_ROOTS,
        output_dir=args.output_dir,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        q_suppress=args.q_suppress,
        q_active=args.q_active,
        l_sup_win=args.l_sup_win,
        l_act_win=args.l_act_win,
        p_sup=args.p_sup,
        p_act=args.p_act,
        t_ref_sec=args.t_ref_sec,
        min_events_for_sbeg=args.min_events_for_sbeg,
        max_subjects_per_class=args.max_subjects_per_class,
        run_null=not args.no_null,
    )


def main() -> None:
    config = parse_args()
    ensure_dir(config.output_dir)

    print(f"Collecting and processing H5 runs...")
    run_df = collect_and_process(config)
    if run_df.empty:
        raise RuntimeError("No runs processed. Check --processed-root paths.")

    n_runs = len(run_df)
    print(f"  {n_runs} runs processed")
    run_df.to_csv(config.output_dir / "sbeg_run_features.csv", index=False)

    print("Aggregating to subject level...")
    subj_df = aggregate_to_subjects(run_df)
    n_subj  = len(subj_df)
    n_good  = int((subj_df["cpc"] == config.good_cpc).sum())
    n_poor  = int((subj_df["cpc"] == config.poor_cpc).sum())
    print(f"  {n_subj} subjects ({n_good} CPC{config.good_cpc}, {n_poor} CPC{config.poor_cpc})")
    subj_df.to_csv(config.output_dir / "sbeg_subject_features.csv", index=False)

    print("Building contrast table...")
    contrast = build_contrast(subj_df, good_cpc=config.good_cpc, poor_cpc=config.poor_cpc)
    contrast.to_csv(config.output_dir / "sbeg_contrast.csv", index=False)

    print("Running circular-shift null...")
    null_result = null_contrast(subj_df, good_cpc=config.good_cpc, poor_cpc=config.poor_cpc)

    summary_md = build_markdown(
        contrast, null_result,
        n_runs=n_runs, n_subj=n_subj, n_good=n_good, n_poor=n_poor,
        good_cpc=config.good_cpc, poor_cpc=config.poor_cpc,
        config=config,
    )
    (config.output_dir / "sbeg_summary.md").write_text(summary_md, encoding="utf-8")

    manifest = {
        "processed_roots": [str(r) for r in config.processed_roots],
        "output_dir": str(config.output_dir),
        "good_cpc": config.good_cpc,
        "poor_cpc": config.poor_cpc,
        "q_suppress": config.q_suppress,
        "q_active": config.q_active,
        "l_sup_win": config.l_sup_win,
        "l_act_win": config.l_act_win,
        "p_sup": config.p_sup,
        "p_act": config.p_act,
        "t_ref_sec": config.t_ref_sec,
        "n_runs": n_runs,
        "n_subjects": n_subj,
        "n_good": n_good,
        "n_poor": n_poor,
    }
    (config.output_dir / "sbeg_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\nWrote results to {config.output_dir}")
    if not contrast.empty:
        print("\nTop contrasts:")
        for _, r in contrast.head(8).iterrows():
            print(
                f"  {r['metric']:<30} d={r['cohens_d']:+.3f}  "
                f"p={r['mw_p']:.3g}  AUROC={r['auroc']:.3f}  "
                f"n={r[f'n_cpc{config.good_cpc}']}/{r[f'n_cpc{config.poor_cpc}']}"
            )
    print(f"\nNull: observed |d|={abs(null_result.get('observed_d', float('nan'))):.3f}, "
          f"null p95={null_result.get('null_p95_d', float('nan')):.3f}, "
          f"empirical p={null_result.get('empirical_p', float('nan')):.4f}")


if __name__ == "__main__":
    main()
