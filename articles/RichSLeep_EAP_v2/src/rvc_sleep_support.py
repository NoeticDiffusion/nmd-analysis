"""
rvc_sleep_support.py -- Shared constants, loaders, and statistics for the
RichSleep EAP v2 article ("State Determines Carrier" + N2 efficacy;
.cursor/plans/richsleep_eap_v2_article_aa3119f9.plan.md).

RichSleep-only (24 subjects, full PSG). This module is a trimmed, adapted
copy of articles/RVC_SLEEP_peak_analysis/src/rvc_sleep_support.py: the
ANPHY/BOAS-specific dataset/surface machinery is dropped (irrelevant here -
this article never touches those two datasets), and path constants for the
five new NMD data products (see
handover/handover_From_nmd_richsleep_eap_v2_delivery_received.md) plus a
generic phase-locking test helper and an H5-hypnogram exposure helper are
added.

Data lineage:
  - Geometry (coords_9d and its deltas) comes from the *same* RichSleep NMD
    run used by RVC_SLEEP_peak_analysis (neuralmanifolddynamics_RichSleep_
    20260709_100219) -- unchanged by the new delivery. RUN_ROOT/CONFIG_HASH
    below are carried over unmodified from that article.
  - The six new phase/coupling/continuous/risk-set data products live under
    this article's own data/ folder (see PHASE_V3_DIR etc. below), not under
    data/raw/ -- they are article-scoped deliveries, not NMD run exports.
    `non_event_risk_v1` was found on K:/ExternalReceivedDatasets/RichSleep/
    (present alongside the other five, but not copied into data/ by the
    initial "ny leverans" message) and copied in during Phase 1 -- see
    handover/handover_From_nmd_richsleep_eap_v2_delivery_received.md.

Note on the per-subject geometry H5's `labels/stage` array (data/raw/..._
RichSleep_20260709_100219/sub-xnNNN_sleep_sleep/sub-xnNNN_sleep_sleep.h5):
this is NOT a continuous full-night hypnogram -- it is only populated at the
177 "jacobian_9d_centers" windows (a sparse local-dynamics-fit subset), with
all other windows defaulted to -1. An earlier version of this module used it
to build a continuous N2 time-at-risk mask for the spindle-onset hazard
model; that approach undercounted N2 exposure by roughly two orders of
magnitude (~0.3 h instead of a plausible ~1-2 h/subject) and has been
dropped in favor of the properly-constructed `non_event_risk_v1` risk-set
sample (`load_non_event_risk()` below), which NMD delivered specifically
for this purpose and does not depend on this H5 array at all.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTICLE_DIR = REPO_ROOT / "articles" / "RichSLeep_EAP_v2"
RESULTS_DIR = ARTICLE_DIR / "results"
FIGURES_DIR = ARTICLE_DIR / "figures"
DATA_DIR = ARTICLE_DIR / "data"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

DATA_RAW = REPO_ROOT / "data" / "raw"

# New NMD delivery, 2026-07-12/13 (see handover/handover_From_nmd_richsleep_eap_v2_delivery_received.md)
PHASE_V3_DIR = DATA_DIR / "phase_resolved_v3"
SO_V1_DIR = DATA_DIR / "slow_oscillation_v1"
PHASE_CONTINUOUS_DIR = DATA_DIR / "phase_continuous_v1"
N3_SO_DIR = DATA_DIR / "event_phase_n3_so_v1"
REM_THETA_DIR = DATA_DIR / "event_phase_rem_theta_v1"
NON_EVENT_RISK_DIR = DATA_DIR / "non_event_risk_v1"

# Companion article whose already-verified geometry table (09_richsleep_
# verification.py output) this article reuses rather than recomputing -- see
# 02_build_merged_table.py.
PEAK_ANALYSIS_DIR = REPO_ROOT / "articles" / "RVC_SLEEP_peak_analysis"

DATASET_RICHSLEEP = "RichSleep"
SURFACE_PRIMARY = "primary"

# RichSleep event-locked geometry run (unchanged from RVC_SLEEP_peak_analysis;
# see that article's rvc_sleep_support.py for the ANPHY/BOAS frozen runs this
# was originally registered alongside).
RUN_ROOT_RICHSLEEP = DATA_RAW / "neuralmanifolddynamics_RichSleep_20260709_100219"
CONFIG_HASH_RICHSLEEP = "0c8d751c52029306"
EXPECTED_N_SUBJECTS_RICHSLEEP = 24

# ──────────────────────────────────────────────────────────────────────────────
# Geometry / bin column groups
# ──────────────────────────────────────────────────────────────────────────────

GEOMETRY_COLS: List[str] = ["m", "d", "e", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"]

BIN_LABEL_ORDER: List[str] = ["pre_far", "pre_near", "event", "post_near", "post_far"]
CONTROL_BIN_LABEL = "control"

CONDITION_EVENT = "spindle_event"
CONDITION_CONTROL = "matched_control"

ANCHOR_COLS_RICHSLEEP: List[str] = [
    "cardioresp_anchor_index", "anchor_index", "anchor_index_v02",
    "sympathetic_index", "vagal_index", "resp_anchor_index", "ocular_stability_index",
]
PRIMARY_ANCHOR_COL_RICHSLEEP = "cardioresp_anchor_index"

# RichSleep numeric stage codebook (config_ingest_richsleep_rvc_trv.yaml
# `sleep_annotations.stage_map`): Wake=0, N1=1, N2=2, N3=3, REM=4; -1 = unscored.
RICHSLEEP_STAGE_WAKE = 0
RICHSLEEP_STAGE_N1 = 1
RICHSLEEP_STAGE_N2 = 2
RICHSLEEP_STAGE_N3 = 3
RICHSLEEP_STAGE_REM = 4

# ──────────────────────────────────────────────────────────────────────────────
# Data loaders
# ──────────────────────────────────────────────────────────────────────────────

def load_event_locked_richsleep() -> pd.DataFrame:
    """Load and concatenate all RichSleep event-locked parquets."""
    pqs = sorted(RUN_ROOT_RICHSLEEP.rglob("*event_locked*.parquet"))
    if not pqs:
        raise FileNotFoundError(f"No event-locked parquet files found under {RUN_ROOT_RICHSLEEP}")
    df = pd.concat([pd.read_parquet(p) for p in pqs], ignore_index=True)
    df["dataset_id"] = DATASET_RICHSLEEP
    df["surface"] = SURFACE_PRIMARY
    return df


def ensure_n2_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add an `n2` 0/1 column derived from `stage` if `n2` is not already
    present (RichSleep has `stage` but no `n2`/`n3`/`rem`/`wake` columns).
    No-op (returns df unchanged) if `n2` already exists or `stage` is absent.
    """
    if "n2" not in df.columns and "stage" in df.columns:
        df = df.copy()
        df["n2"] = (df["stage"] == RICHSLEEP_STAGE_N2).astype(int)
    return df


def pass_a_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Recommended base filter (coords_9d finite + N2 stage), matching the
    convention used throughout RVC_SLEEP/RVC_SLEEP_peak_analysis. Call
    `ensure_n2_column()` first if `n2` is not already present.
    """
    mask = pd.Series(True, index=df.index)
    if "coords_9d_finite" in df.columns:
        mask &= df["coords_9d_finite"] == 1
    if "n2" in df.columns:
        mask &= df["n2"] == 1
    elif "stage" in df.columns:
        mask &= df["stage"] == RICHSLEEP_STAGE_N2
    return df[mask]


def load_phase_v3() -> pd.DataFrame:
    """Load and concatenate all 24 subjects' phase_resolved_v3 parquets,
    adding a `subject_id` column (`sub-xnNNN`) matching the geometry table's
    convention.
    """
    files = sorted(PHASE_V3_DIR.glob("*_event_phase_v3.parquet"))
    if len(files) != EXPECTED_N_SUBJECTS_RICHSLEEP:
        raise RuntimeError(f"Expected {EXPECTED_N_SUBJECTS_RICHSLEEP} event_phase_v3 files, found {len(files)}")
    frames = []
    for p in files:
        d = pd.read_parquet(p)
        d["subject_id"] = f"sub-{p.stem.replace('_event_phase_v3', '')}"
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def load_n3_so() -> pd.DataFrame:
    """Load and concatenate all 24 subjects' event_phase_n3_so_v1 parquets."""
    files = sorted(N3_SO_DIR.glob("*_event_phase_n3_so_v1.parquet"))
    if len(files) != EXPECTED_N_SUBJECTS_RICHSLEEP:
        raise RuntimeError(f"Expected {EXPECTED_N_SUBJECTS_RICHSLEEP} event_phase_n3_so_v1 files, found {len(files)}")
    frames = [pd.read_parquet(p) for p in files]
    df = pd.concat(frames, ignore_index=True)
    df["subject_id"] = "sub-" + df["subject"].astype(str)
    return df


def load_rem_theta() -> pd.DataFrame:
    """Load and concatenate all 24 subjects' event_phase_rem_theta_v1 parquets."""
    files = sorted(REM_THETA_DIR.glob("*_event_phase_rem_theta_v1.parquet"))
    if len(files) != EXPECTED_N_SUBJECTS_RICHSLEEP:
        raise RuntimeError(f"Expected {EXPECTED_N_SUBJECTS_RICHSLEEP} event_phase_rem_theta_v1 files, found {len(files)}")
    frames = [pd.read_parquet(p) for p in files]
    df = pd.concat(frames, ignore_index=True)
    df["subject_id"] = "sub-" + df["subject"].astype(str)
    return df


def load_phase_continuous(subject_id: str) -> pd.DataFrame:
    """Load the continuous 10 Hz phase stream for one subject
    (`subject_id` like `sub-xn001` or bare `xn001`).
    """
    short = subject_id.replace("sub-", "")
    path = PHASE_CONTINUOUS_DIR / f"{short}_phase_continuous_v1.parquet"
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_parquet(path)


def load_non_event_risk() -> pd.DataFrame:
    """Load and concatenate all 24 subjects' non_event_risk_v1 parquets --
    NMD's purpose-built non-event risk-set sample: N2-stage timepoints drawn
    at random per subject (stratified by time-of-night quartile, excluding a
    30 s margin around every real spindle event -- `exclusion_margin_sec`),
    each carrying its own `phi_cardiac`/`phi_resp` phase. This is the genuine
    "risk set" used by 04_spindle_onset_hazard_model.py's case-control test:
    real spindle onsets are the cases, these rows are the (subject-matched,
    N2-restricted) controls, so comparing their phase distributions tests
    onset-phase-locking against the correct exposure-weighted null instead
    of an unweighted uniform-circular assumption.
    """
    files = sorted(NON_EVENT_RISK_DIR.glob("*_non_event_risk_v1.parquet"))
    if len(files) != EXPECTED_N_SUBJECTS_RICHSLEEP:
        raise RuntimeError(f"Expected {EXPECTED_N_SUBJECTS_RICHSLEEP} non_event_risk_v1 files, found {len(files)}")
    frames = [pd.read_parquet(p) for p in files]
    df = pd.concat(frames, ignore_index=True)
    df["subject_id"] = "sub-" + df["subject"].astype(str)
    return df


def available_covariates(
    df: pd.DataFrame, candidates: List[str], *, min_coverage: float = 0.5
) -> List[str]:
    """Filter candidate covariate columns to those present AND with at least
    `min_coverage` non-NaN fraction (default 50%). See RVC_SLEEP_peak_analysis's
    rvc_sleep_support.py for the original rationale (silent all-NaN columns
    otherwise crash patsy/statsmodels with a cryptic error).
    """
    out = []
    for c in candidates:
        if c not in df.columns:
            continue
        coverage = df[c].notna().mean()
        if coverage >= min_coverage:
            out.append(c)
    return out


def make_results_subdir(phase: str) -> Path:
    """Create and return a dated results subdirectory:
    results/rvc_sleep_v2_<YYYYMMDD>/<phase>/.
    """
    today = datetime.now().strftime("%Y%m%d")
    d = RESULTS_DIR / f"rvc_sleep_v2_{today}" / phase
    d.mkdir(parents=True, exist_ok=True)
    return d


# ──────────────────────────────────────────────────────────────────────────────
# Statistics helpers (circular stats, WLS-cluster regression, permutation
# tests -- carried over verbatim from RVC_SLEEP_peak_analysis's
# rvc_sleep_support.py, since none of this logic is dataset/article-specific)
# ──────────────────────────────────────────────────────────────────────────────

def bh_fdr(pvals: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg FDR correction."""
    pvals = np.asarray(pvals, dtype=float)
    n = len(pvals)
    if n == 0:
        return pvals
    rank = np.argsort(pvals).argsort() + 1
    adjusted = np.minimum(1.0, pvals * n / rank)
    sorted_idx = np.argsort(pvals)[::-1]
    min_so_far = 1.0
    result = adjusted.copy()
    for i in sorted_idx:
        min_so_far = min(min_so_far, adjusted[i])
        result[i] = min_so_far
    return result


def fit_wls_cluster(
    formula: str,
    data: pd.DataFrame,
    weights_col: str,
    groups_col: str = "subject_id",
) -> Optional["object"]:
    """Fit a WLS model (weights = `weights_col`, typically `1 / n_events_subject`)
    with cluster-robust SE by `groups_col`. See RVC_SLEEP_peak_analysis's
    rvc_sleep_support.py for the full rationale.
    """
    import warnings

    try:
        import statsmodels.formula.api as smf
    except ImportError:
        warnings.warn(
            "statsmodels is not installed; fit_wls_cluster() is returning None. "
            "pip install statsmodels to enable cluster-robust WLS fitting."
        )
        return None

    try:
        model = smf.wls(formula, data=data, weights=data[weights_col])
        return model.fit(cov_type="cluster", cov_kwds={"groups": data[groups_col]})
    except Exception as exc:  # noqa: BLE001
        warnings.warn(f"fit_wls_cluster failed for formula '{formula}': {exc}")
        return None


def fit_logit_cluster(
    formula: str,
    data: pd.DataFrame,
    groups_col: str = "subject_id",
) -> Optional["object"]:
    """Fit a logistic regression with cluster-robust SE by `groups_col`.

    Used by 04_spindle_onset_hazard_model.py's case-control test: `formula`'s
    LHS should be a 0/1 "is this row a real event (case) rather than a
    non_event_risk_v1 control" indicator, and the RHS a circular-phase basis
    (e.g. `is_case ~ cos_phase + sin_phase`). A significant cos/sin pair means
    the phase distribution of real onsets differs from the risk-set's
    (N2-restricted, subject-matched) phase distribution -- a genuine hazard-
    style test, not merely a uniform-circular-null Rayleigh test.
    """
    import warnings

    try:
        import statsmodels.formula.api as smf
    except ImportError:
        warnings.warn(
            "statsmodels is not installed; fit_logit_cluster() is returning None. "
            "pip install statsmodels to enable cluster-robust logit fitting."
        )
        return None

    try:
        model = smf.logit(formula, data=data)
        return model.fit(cov_type="cluster", cov_kwds={"groups": data[groups_col]}, disp=False)
    except Exception as exc:  # noqa: BLE001
        warnings.warn(f"fit_logit_cluster failed for formula '{formula}': {exc}")
        return None


def subject_level_slopes(
    x: np.ndarray, y: np.ndarray, groups: np.ndarray, *, min_events: int = 3
) -> pd.Series:
    """Per-subject OLS slope of y on x. Subjects with fewer than `min_events`
    events, or with a constant x, are skipped.
    """
    df = pd.DataFrame({"x": x, "y": y, "group": groups}).dropna()
    slopes = {}
    for g, sub in df.groupby("group"):
        if len(sub) < min_events or sub["x"].nunique() < 2:
            continue
        b, _ = np.polyfit(sub["x"].to_numpy(), sub["y"].to_numpy(), 1)
        slopes[g] = b
    return pd.Series(slopes, name="slope")


def subject_level_sensitivity(
    values: np.ndarray, groups: np.ndarray
) -> Dict[str, float]:
    """Aggregate to one row per subject (mean), then one-sample t-test and
    Wilcoxon signed-rank against 0. Avoids pseudo-replication.
    """
    df = pd.DataFrame({"value": values, "group": groups}).dropna()
    subj_means = df.groupby("group")["value"].mean()
    n_subjects = len(subj_means)
    out = {
        "n_subjects": n_subjects,
        "subject_mean_delta": float(subj_means.mean()) if n_subjects else np.nan,
        "ttest_stat": np.nan, "ttest_p": np.nan,
        "wilcoxon_stat": np.nan, "wilcoxon_p": np.nan,
    }
    if n_subjects < 5:
        return out
    t_stat, t_p = stats.ttest_1samp(subj_means.values, 0.0)
    out["ttest_stat"], out["ttest_p"] = float(t_stat), float(t_p)
    try:
        w_stat, w_p = stats.wilcoxon(subj_means.values, zero_method="wilcox")
        out["wilcoxon_stat"], out["wilcoxon_p"] = float(w_stat), float(w_p)
    except ValueError:
        pass
    return out


def sign_flip_permutation_test(
    values: np.ndarray,
    groups: np.ndarray,
    *,
    n_perm: int = 2000,
    seed: int = 42,
) -> Tuple[float, float]:
    """Within-subject sign-flip permutation test (H0: no true event-vs-
    baseline difference, so each event's sign is exchangeable). Returns
    (observed_statistic, two_sided_permutation_p).
    """
    df = pd.DataFrame({"value": values, "group": groups}).dropna()
    if len(df) < 5 or df["group"].nunique() < 5:
        return np.nan, np.nan

    values_arr = df["value"].to_numpy()
    group_codes, group_uniques = pd.factorize(df["group"])
    n_groups = len(group_uniques)
    group_counts = np.bincount(group_codes, minlength=n_groups).astype(float)

    indicator = np.zeros((len(values_arr), n_groups), dtype=np.float32)
    indicator[np.arange(len(values_arr)), group_codes] = 1.0

    subj_means = (values_arr @ indicator) / group_counts
    observed = float(subj_means.mean())

    rng = np.random.default_rng(seed)
    signs = rng.choice(np.array([-1.0, 1.0], dtype=np.float32), size=(n_perm, len(values_arr)))
    flipped = signs * values_arr.astype(np.float32)
    group_sums = flipped @ indicator
    group_means = group_sums / group_counts
    perm_stats = group_means.mean(axis=1)

    p = float((np.sum(np.abs(perm_stats) >= abs(observed)) + 1) / (n_perm + 1))
    return observed, p


def circular_mean_resultant(phases: np.ndarray) -> Tuple[float, float, int]:
    """Circular mean angle and mean resultant length R in [0, 1]. Returns
    (mean_angle, R, n).
    """
    phases = np.asarray(phases, dtype=float)
    phases = phases[np.isfinite(phases)]
    n = len(phases)
    if n == 0:
        return np.nan, np.nan, 0
    c = np.mean(np.cos(phases))
    s = np.mean(np.sin(phases))
    r = float(np.hypot(c, s))
    angle = float(np.arctan2(s, c))
    return angle, r, n


def rayleigh_test(phases: np.ndarray) -> Tuple[float, float, int]:
    """Rayleigh test for non-uniformity of a circular distribution (Zar 1999
    large-sample approximation, valid for n gtrsim 10). Returns (R, p, n).
    """
    _, r, n = circular_mean_resultant(phases)
    if n < 5:
        return r, np.nan, n
    z = n * r ** 2
    p = float(
        np.exp(-z)
        * (1 + (2 * z - z ** 2) / (4 * n)
           - (24 * z - 132 * z ** 2 + 76 * z ** 3 - 9 * z ** 4) / (288 * n ** 2))
    )
    p = float(np.clip(p, 0.0, 1.0))
    return r, p, n


def harmonic_stats(phases: np.ndarray) -> Tuple[float, float, float]:
    """(R1, R2, T2) for a pooled set of phases (radians). T2 = R1**2 + R2**2,
    an honestly-labelled omnibus statistic (not a literature Hermans-Rasson
    re-implementation) -- see RVC_SLEEP_peak_analysis's rvc_sleep_support.py.
    """
    phases = np.asarray(phases, dtype=float)
    phases = phases[np.isfinite(phases)]
    n = len(phases)
    if n == 0:
        return np.nan, np.nan, np.nan
    r1 = float(np.hypot(np.mean(np.cos(phases)), np.mean(np.sin(phases))))
    r2 = float(np.hypot(np.mean(np.cos(2 * phases)), np.mean(np.sin(2 * phases))))
    return r1, r2, r1 ** 2 + r2 ** 2


def subject_rotation_permutation_test(
    phases: np.ndarray, subjects: np.ndarray, *, n_perm: int = 2000, seed: int = 42,
) -> Dict[str, float]:
    """Pseudo-replication-safe permutation test for population-level circular
    non-uniformity (diary 241; 02_response.md S7, option 3). Null: for each
    permutation, draw one iid Uniform(0, 2*pi) rotation per subject and add
    it to *all* of that subject's phases, preserving per-subject event
    counts and within-subject clustering.
    """
    phases = np.asarray(phases, dtype=float)
    subjects = np.asarray(subjects)
    mask = np.isfinite(phases)
    phases, subjects = phases[mask], subjects[mask]
    obs_r1, obs_r2, obs_t2 = harmonic_stats(phases)

    unique_subj, subj_idx = np.unique(subjects, return_inverse=True)
    n_subj = len(unique_subj)
    rng = np.random.default_rng(seed)

    null_r1 = np.empty(n_perm)
    null_t2 = np.empty(n_perm)
    for k in range(n_perm):
        rotations = rng.uniform(0, 2 * np.pi, size=n_subj)
        rotated = phases + rotations[subj_idx]
        r1, _, t2 = harmonic_stats(rotated)
        null_r1[k] = r1
        null_t2[k] = t2

    p_r1 = (1 + np.sum(null_r1 >= obs_r1)) / (1 + n_perm)
    p_t2 = (1 + np.sum(null_t2 >= obs_t2)) / (1 + n_perm)
    return {
        "n_events": len(phases), "n_subjects": n_subj,
        "obs_R1": obs_r1, "obs_R2": obs_r2, "obs_T2": obs_t2,
        "null_R1_mean": float(np.mean(null_r1)), "null_R1_95pct": float(np.quantile(null_r1, 0.95)),
        "null_T2_mean": float(np.mean(null_t2)), "null_T2_95pct": float(np.quantile(null_t2, 0.95)),
        "perm_p_R1": float(p_r1), "perm_p_T2": float(p_t2),
    }


def circular_time_shift_surrogate_test(
    event_times: np.ndarray,
    subjects: np.ndarray,
    continuous_loader,
    channel: str = "phi_resp",
    *,
    n_perm: int = 500,
    seed: int = 44,
    min_shift_sec: float = 60.0,
) -> Dict[str, float]:
    """Circular time-shift surrogate null (02_response.md S7, option 4):
    for each permutation, shift each subject's *continuous* phase stream by
    an independent random lag (circularly, wrapping at that subject's
    recording duration) and re-read the phase value at each of that
    subject's real event times under the shifted stream. This preserves the
    exact (non-sinusoidal, quasi-periodic) waveform shape and autocorrelation
    structure of the physiological signal itself, unlike
    `subject_rotation_permutation_test`'s parametric uniform-rotation null on
    the discrete event-phase values -- a genuinely different, complementary
    null for the same onset-phase-locking question (used by
    04_spindle_onset_hazard_model.py as a cross-check).

    `continuous_loader(subject_id)` must return a DataFrame with
    `timestamp_sec` and `channel` columns (see `load_phase_continuous`).
    `event_times`/`subjects` are 1:1 arrays of (onset_sec, subject_id) for
    the real events under test.
    """
    df = pd.DataFrame({"t": event_times, "subject": subjects}).dropna()
    obs_phases = []
    for subj, sub in df.groupby("subject"):
        cont = continuous_loader(subj)
        idx = np.searchsorted(cont["timestamp_sec"].to_numpy(), sub["t"].to_numpy())
        idx = np.clip(idx, 0, len(cont) - 1)
        obs_phases.append(cont[channel].to_numpy()[idx])
    obs_phases = np.concatenate(obs_phases) if obs_phases else np.array([])
    obs_r1, obs_r2, obs_t2 = harmonic_stats(obs_phases)

    rng = np.random.default_rng(seed)
    null_r1 = np.empty(n_perm)
    null_t2 = np.empty(n_perm)
    subj_conts = {subj: continuous_loader(subj) for subj in df["subject"].unique()}
    for k in range(n_perm):
        shifted_phases = []
        for subj, sub in df.groupby("subject"):
            cont = subj_conts[subj]
            duration = cont["timestamp_sec"].max()
            lag = rng.uniform(min_shift_sec, duration - min_shift_sec)
            shifted_t = (sub["t"].to_numpy() + lag) % duration
            idx = np.searchsorted(cont["timestamp_sec"].to_numpy(), shifted_t)
            idx = np.clip(idx, 0, len(cont) - 1)
            shifted_phases.append(cont[channel].to_numpy()[idx])
        shifted_phases = np.concatenate(shifted_phases)
        r1, _, t2 = harmonic_stats(shifted_phases)
        null_r1[k] = r1
        null_t2[k] = t2

    p_r1 = (1 + np.sum(null_r1 >= obs_r1)) / (1 + n_perm)
    p_t2 = (1 + np.sum(null_t2 >= obs_t2)) / (1 + n_perm)
    return {
        "n_events": len(obs_phases), "n_subjects": df["subject"].nunique(),
        "obs_R1": obs_r1, "obs_R2": obs_r2, "obs_T2": obs_t2,
        "null_R1_mean": float(np.mean(null_r1)), "null_R1_95pct": float(np.quantile(null_r1, 0.95)),
        "null_T2_mean": float(np.mean(null_t2)), "null_T2_95pct": float(np.quantile(null_t2, 0.95)),
        "perm_p_R1": float(p_r1), "perm_p_T2": float(p_t2),
    }


def run_phase_locking_family(
    phases: np.ndarray,
    subjects: np.ndarray,
    *,
    label: str,
    n_perm: int = 2000,
    min_events_per_subject: int = 5,
) -> Dict[str, object]:
    """Generic phase-locking test for one channel/carrier: per-subject
    Rayleigh test, second-order (population-of-subject-means) Rayleigh test,
    and the pseudo-replication-safe `subject_rotation_permutation_test` on
    the pooled events. Used by 03_multistage_phase_locking.py for all four
    carriers (N2-onset, N2-peak, N3-SO trough/upstate, REM-theta) so the
    method is implemented once rather than four times.

    Returns a dict with `label`, per-subject DataFrame, second-order-mean
    summary dict, and the pooled subject-rotation permutation-test dict.
    """
    phases = np.asarray(phases, dtype=float)
    subjects = np.asarray(subjects)
    mask = np.isfinite(phases)
    phases, subjects = phases[mask], subjects[mask]

    per_subject_rows = []
    subject_mean_angles = {}
    for subj in pd.unique(subjects):
        sub_phases = phases[subjects == subj]
        r, p, n = rayleigh_test(sub_phases)
        angle, _, _ = circular_mean_resultant(sub_phases)
        per_subject_rows.append({"label": label, "subject_id": subj, "n_events": n,
                                   "mean_angle_rad": angle, "R": r, "rayleigh_p": p})
        if np.isfinite(angle) and n >= min_events_per_subject:
            subject_mean_angles[subj] = angle
    per_subject_df = pd.DataFrame(per_subject_rows)
    if len(per_subject_df) and per_subject_df["rayleigh_p"].notna().any():
        per_subject_df["rayleigh_p_fdr"] = bh_fdr(per_subject_df["rayleigh_p"].fillna(1.0).to_numpy())

    angles = np.array(list(subject_mean_angles.values()))
    r2, p2, n2 = rayleigh_test(angles)
    mean_angle2, _, _ = circular_mean_resultant(angles)
    second_order = {"label": label, "n_subjects": n2, "mean_of_subject_means_rad": mean_angle2,
                     "R_second_order": r2, "rayleigh_p_second_order": p2}

    pooled = subject_rotation_permutation_test(phases, subjects, n_perm=n_perm)
    pooled["label"] = label

    return {"label": label, "per_subject": per_subject_df, "second_order": second_order, "pooled": pooled}
