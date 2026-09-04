"""
rvc_sleep_support.py — Shared constants, loaders, and statistics for the
Rhythmic Variance Control (RVC) sleep-spindle analysis.

Datasets:  ANPHY   — 27 subjects, HD-EEG sleep (Biosemi, 93 channels)
           BOAS / ds005555 — 128 subjects, PSG sleep (OpenNeuro)
           RichSleep — 24 subjects, full PSG (verification-only, see below)

Design:    Dual dataset (ANPHY, BOAS) x dual surface (primary EEG-only,
           anchor-augmented sensitivity). The primary surface is used for
           the main scientific claim (Pass A, Pass C); the anchor-augmented
           surface is sensitivity-only (Pass B). See:
           articles/RVC_SLEEP_peak_analysis/handover/handover_From_nmd.md
           (inherited from articles/RVC_SLEEP/ - see that article for the
           original three-dataset ANPHY/BOAS replication; this folder is a
           RichSleep-only follow-up, see diary 241/242/243)

Pipeline runs (frozen, Gate #2 QC passed; Pass A/B/C complete per
sciencelead/004.md — DATASETS below stays exactly [ANPHY, BOAS] and must
NOT be edited to include RichSleep):
    ANPHY primary      neuralmanifolddynamics_ANPHY_20260709_100213
    ANPHY anchor-aug   neuralmanifolddynamics_ANPHY_20260709_102151
    BOAS primary       neuralmanifolddynamics_ds005555_20260709_100213
    BOAS anchor-aug    neuralmanifolddynamics_ds005555_20260709_100219

    REPLACED 2026-07-09: corrected resp_anchor_index sign bug (diary 184);
    previous runs 20260702_082429 / 20260702_084940 / 20260702_080821 /
    20260702_084946 had resp_slowing_index double-negated.

RichSleep (added 2026-07-04, verification dataset only — see
09_richsleep_verification.py and diary 231):
    RichSleep primary  neuralmanifolddynamics_RichSleep_20260709_100219
                        (primary_eeg_only surface; no anchor-augmented
                        counterpart was ingested for this dataset)
                        REPLACED 2026-07-09: corrected resp_anchor_index sign
                        bug (diary 184); previous run 20260708_135627 had
                        resp_slowing_index double-negated.

RichSleep is a THIRD, independent dataset used only to (a) replicate the
frozen A1r/A2r spindle-timing effect out-of-sample, and (b) run a "proper"
EAP moderation test: unlike ANPHY (cardiac-only anchor) and BOAS (resp-only
anchor, ~66/128 subjects missing), RichSleep has simultaneous, ~100%-covered
ECG + respiratory + EOG + chin-EMG channels, so its `anchor_state` group
carries a genuine dual-arm cardiorespiratory composite
(`cardioresp_anchor_index`) with none of the single-channel missingness that
limited Pass C on ANPHY/BOAS. It is deliberately kept OUT of the frozen
`DATASETS` list / Pass A-C scripts so it cannot silently change the already
-frozen ANPHY/BOAS results; it gets its own script and its own results
subfolder instead.
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
ARTICLE_DIR = REPO_ROOT / "articles" / "RVC_SLEEP_peak_analysis"
RESULTS_DIR = ARTICLE_DIR / "results"
FIGURES_DIR = ARTICLE_DIR / "figures"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

DATA_RAW = REPO_ROOT / "data" / "raw"

# Dataset identifiers as they appear in the event-locked parquet `dataset_id` column
DATASET_ANPHY = "ANPHY"
DATASET_BOAS = "ds005555"
DATASETS = [DATASET_ANPHY, DATASET_BOAS]  # FROZEN — do not add RichSleep here

# Verification-only third dataset (see module docstring). Kept separate from
# DATASETS so Pass A-C scripts and their frozen results are untouched.
DATASET_RICHSLEEP = "RichSleep"

SURFACE_PRIMARY = "primary"
SURFACE_ANCHOR_AUG = "anchor_aug"
SURFACES = [SURFACE_PRIMARY, SURFACE_ANCHOR_AUG]

# Run-root registry: (dataset, surface) -> run directory under data/raw/
RUN_ROOTS: Dict[Tuple[str, str], Path] = {
    # 2026-07-09: NMD delivered 20260709 re-summarize runs for all 3 datasets
    # (diary 184/238 — resp_anchor_index sign fix). REVERTED ANPHY/BOAS back to
    # the frozen 20260702 runs (diary 239): the new ANPHY primary run has 2
    # corrupted event-locked parquets (sub-EPCTL13, sub-EPCTL16 - unreadable by
    # pyarrow), and the new BOAS runs (both surfaces) are missing
    # `resp_regular_index`/`resp_depth_index`/`resp_rate_bpm` columns that BOAS's
    # primary Pass C anchor test requires. Geometry (m/d/e) confirmed
    # bit-identical between old and new BOAS runs where comparable, so this is a
    # delivery/export regression, not a scientific change - flagged back to NMD
    # (handover_To_nmd_resp_anchor_index_followup.md §7), re-verify once fixed.
    (DATASET_ANPHY, SURFACE_PRIMARY): DATA_RAW / "neuralmanifolddynamics_ANPHY_20260702_082429",
    (DATASET_ANPHY, SURFACE_ANCHOR_AUG): DATA_RAW / "neuralmanifolddynamics_ANPHY_20260702_084940",
    (DATASET_BOAS, SURFACE_PRIMARY): DATA_RAW / "neuralmanifolddynamics_ds005555_20260702_080821",
    (DATASET_BOAS, SURFACE_ANCHOR_AUG): DATA_RAW / "neuralmanifolddynamics_ds005555_20260702_084946",
    # RichSleep: primary_eeg_only surface only, no anchor-augmented run exists.
    # 2026-07-09: replaced 20260708_135627 with 20260709_100219 (diary 184 fix —
    # corrected resp_anchor_index sign bug; resp_slowing_index was double-negated).
    # Independently verified clean (24/24 subjects, no corrupted files, all
    # expected columns present) - kept on the new run.
    (DATASET_RICHSLEEP, SURFACE_PRIMARY): DATA_RAW / "neuralmanifolddynamics_RichSleep_20260709_100219",
}

# First 16 chars of run_manifest.json -> config.digest_sha256, used to assert
# the correct run is loaded (see handover_From_nmd.md §1)
CONFIG_HASH: Dict[Tuple[str, str], str] = {
    # 2026-07-09 (diary 239): ANPHY/BOAS reverted to original frozen digests
    # alongside the RUN_ROOTS revert above.
    (DATASET_ANPHY, SURFACE_PRIMARY): "b6d72c504414c540",
    (DATASET_ANPHY, SURFACE_ANCHOR_AUG): "e52ce463339d642b",
    (DATASET_BOAS, SURFACE_PRIMARY): "19e24fb3acea8f8e",
    (DATASET_BOAS, SURFACE_ANCHOR_AUG): "1374fa95bc12d6d1",
    # RichSleep config YAML unchanged — digest unchanged from 20260708_135627 run.
    (DATASET_RICHSLEEP, SURFACE_PRIMARY): "0c8d751c52029306",
}

# Expected subject counts (handover_From_nmd.md §1), used as a sanity-check target
EXPECTED_N_SUBJECTS: Dict[str, int] = {
    DATASET_ANPHY: 27,
    DATASET_BOAS: 128,
    DATASET_RICHSLEEP: 24,
}

# ──────────────────────────────────────────────────────────────────────────────
# Geometry / bin / anchor column groups
# ──────────────────────────────────────────────────────────────────────────────

# Primary endpoint family, frozen per plan2.md "Primary endpoint set"
GEOMETRY_COLS: List[str] = ["m", "d", "e", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"]

# Secondary layers, added only if available/stable
REACH_COLS: List[str] = ["tube_d_eff", "tube_log_det", "tube_kappa", "tube_rotation", "tube_dir_entropy"]
MNJ_COLS: List[str] = ["frobenius_norm", "rotation_norm", "spectral_radius", "rotational_power", "trace"]

BIN_LABEL_ORDER: List[str] = ["pre_far", "pre_near", "event", "post_near", "post_far"]
CONTROL_BIN_LABEL = "control"

CONDITION_EVENT = "spindle_event"
CONDITION_CONTROL = "matched_control"

# Per-dataset anchor (EAP) column groups — used only against the primary
# EEG-only surface (Pass C) or the anchor-augmented surface (Pass B)
ANCHOR_COLS_BY_DATASET: Dict[str, List[str]] = {
    DATASET_ANPHY: ["ecg_hrv_rmssd_ms", "ecg_hrv_sdnn_ms", "ecg_hrv_pnn50"],
    DATASET_BOAS: ["resp_regular_index", "resp_depth_index", "resp_rate_bpm", "anchor_index_v02"],
    # RichSleep event-locked rows carry the composite anchor_state columns
    # (not the raw features_raw columns — those stay inside the per-subject
    # H5 only). cardioresp_anchor_index is the dual-arm cardiorespiratory
    # composite named in the run's anchor_contract
    # ("rvc_v1_anchor_v02_dual_arm_cardioresp") and has ~0% NaN across all 24
    # subjects (see 00_sanity_check-equivalent numbers in diary 231) — this is
    # the "proper EAP" anchor the ANPHY/BOAS single-channel anchors could not
    # be, because RichSleep has simultaneous, near-complete ECG+resp+EOG+EMG
    # coverage rather than one channel with heavy missingness.
    DATASET_RICHSLEEP: [
        "cardioresp_anchor_index", "anchor_index", "anchor_index_v02",
        "sympathetic_index", "vagal_index", "resp_anchor_index", "ocular_stability_index",
    ],
}

# Primary Pass C anchor per dataset (see handover_From_nmd.md §5, Pass C)
PRIMARY_ANCHOR_COL: Dict[str, str] = {
    DATASET_ANPHY: "ecg_hrv_rmssd_ms",
    DATASET_BOAS: "resp_regular_index",
    DATASET_RICHSLEEP: "cardioresp_anchor_index",
}

# ──────────────────────────────────────────────────────────────────────────────
# Data loaders
# ──────────────────────────────────────────────────────────────────────────────

def run_root(dataset: str, surface: str = SURFACE_PRIMARY) -> Path:
    """Return the run root directory for (dataset, surface)."""
    key = (dataset, surface)
    if key not in RUN_ROOTS:
        raise KeyError(f"Unknown (dataset, surface) combination: {key}")
    return RUN_ROOTS[key]


def load_event_locked(dataset: str, surface: str = SURFACE_PRIMARY) -> pd.DataFrame:
    """Load and concatenate all event-locked parquets for one (dataset, surface)."""
    root = run_root(dataset, surface)
    pqs = sorted(root.rglob("*event_locked*.parquet"))
    if not pqs:
        raise FileNotFoundError(f"No event-locked parquet files found under {root}")
    df = pd.concat([pd.read_parquet(p) for p in pqs], ignore_index=True)
    df["dataset_id"] = dataset
    df["surface"] = surface
    return df


def load_all_primary() -> pd.DataFrame:
    """Load and concatenate primary (EEG-only) event-locked rows for both datasets."""
    return pd.concat(
        [load_event_locked(ds, SURFACE_PRIMARY) for ds in DATASETS],
        ignore_index=True,
    )


def load_all_anchor_aug() -> pd.DataFrame:
    """Load and concatenate anchor-augmented event-locked rows for both datasets."""
    return pd.concat(
        [load_event_locked(ds, SURFACE_ANCHOR_AUG) for ds in DATASETS],
        ignore_index=True,
    )


def pass_a_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Recommended base filter for Pass A (handover_From_nmd.md §7).

    NOTE: silently does NOT filter by sleep stage if neither `n2` nor `stage`
    is present. RichSleep's event-locked schema has no `n2`/`n3`/`rem`/`wake`
    indicator columns (unlike ANPHY/BOAS) — call `ensure_n2_column()` first
    for RichSleep so this filter behaves the same way as it does for the two
    frozen datasets.
    """
    mask = pd.Series(True, index=df.index)
    if "coords_9d_finite" in df.columns:
        mask &= df["coords_9d_finite"] == 1
    if "n2" in df.columns:
        mask &= df["n2"] == 1
    elif "stage" in df.columns:
        mask &= df["stage"] == RICHSLEEP_STAGE_N2
    return df[mask]


# RichSleep numeric stage codebook (config_ingest_richsleep_rvc_trv.yaml
# `sleep_annotations.stage_map`): Wake=0, N1=1, N2=2, N3=3, REM=4; -1 = unscored.
RICHSLEEP_STAGE_N2 = 2


def ensure_n2_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add an `n2` 0/1 column derived from `stage` if `n2` is not already
    present (RichSleep has `stage` but no `n2`/`n3`/`rem`/`wake` columns).
    No-op (returns df unchanged) if `n2` already exists or `stage` is absent.
    """
    if "n2" not in df.columns and "stage" in df.columns:
        df = df.copy()
        df["n2"] = (df["stage"] == RICHSLEEP_STAGE_N2).astype(int)
    return df


def load_regional_mnps(dataset: str, surface: str = SURFACE_PRIMARY) -> pd.DataFrame:
    """Load the cohort-level regional MNPS CSV for one (dataset, surface).

    Only available for ANPHY runs at present (see data/raw/<run>/regional_mnps_subjects_*.csv).
    """
    root = run_root(dataset, surface)
    matches = sorted(root.glob("regional_mnps_subjects_*.csv"))
    if not matches:
        raise FileNotFoundError(f"No regional_mnps_subjects_*.csv found under {root}")
    return pd.read_csv(matches[0])


def available_covariates(
    df: pd.DataFrame, candidates: List[str], *, min_coverage: float = 0.5
) -> List[str]:
    """Filter candidate covariate columns to those present AND with at least
    `min_coverage` non-NaN fraction (default 50%).

    Column *presence* alone is not sufficient: several NMD-exported columns
    (e.g. `match_distance` in some runs) exist but are entirely or mostly
    NaN, which silently drops all rows once patsy applies its default NA
    handling to a mixedlm formula, producing a cryptic
    "zero-size array to reduction operation maximum" failure deep inside
    statsmodels rather than a clear "no data" message.
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
    """Create and return a dated results subdirectory: results/rvc_sleep_<YYYYMMDD>/<phase>/."""
    today = datetime.now().strftime("%Y%m%d")
    d = RESULTS_DIR / f"rvc_sleep_{today}" / phase
    d.mkdir(parents=True, exist_ok=True)
    return d


def iter_run_manifests() -> List[Tuple[str, str, Path]]:
    """Yield (dataset, surface, run_manifest_path) for all four frozen runs."""
    out = []
    for (dataset, surface), root in RUN_ROOTS.items():
        manifest = root / "run_manifest.json"
        out.append((dataset, surface, manifest))
    return out


# ──────────────────────────────────────────────────────────────────────────────
# Statistics helpers
# ──────────────────────────────────────────────────────────────────────────────

def wilcoxon_paired(
    a: np.ndarray, b: np.ndarray
) -> Tuple[float, float, int, float]:
    """Wilcoxon signed-rank test on paired (a, b), returning (stat, p, n, cohend)."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    a, b = a[mask], b[mask]
    n = len(a)
    if n < 5:
        return np.nan, np.nan, n, np.nan
    diff = a - b
    try:
        stat, p = stats.wilcoxon(diff, zero_method="wilcox")
    except ValueError:
        return np.nan, np.nan, n, np.nan
    d = float(np.mean(diff) / (np.std(diff) + 1e-12))
    return float(stat), float(p), n, d


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


def spearman_r(x, y) -> Tuple[float, float]:
    """Spearman r between two Series/arrays, dropping NaN pairs."""
    df = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(df) < 5:
        return np.nan, np.nan
    r, p = stats.spearmanr(df["x"], df["y"])
    return float(r), float(p)


def fit_mixedlm(
    formula: str,
    data: pd.DataFrame,
    groups_col: str = "subject_id",
) -> Optional["object"]:
    """Fit `geometry ~ ... + (1|subject_id)`-style models via statsmodels MixedLM.

    `formula` should be the fixed-effects part only (statsmodels formula syntax,
    e.g. "m ~ C(condition) * C(bin_label) + event_duration_sec"); the random
    intercept on `groups_col` is added via the `groups=` argument, matching the
    convention used in articles/embodied_anchoring/src/run_lme_traj_vagal.py.

    Returns the fitted results object, or None if fitting fails (e.g. singular
    random-effects covariance, insufficient data).
    """
    import warnings

    try:
        import statsmodels.formula.api as smf
    except ImportError:
        warnings.warn(
            "statsmodels is not installed; fit_mixedlm() is returning None. "
            "pip install statsmodels to enable mixed-effects model fitting."
        )
        return None

    try:
        model = smf.mixedlm(formula, data=data, groups=data[groups_col])
        return model.fit(reml=True, method="lbfgs")
    except Exception as exc:  # noqa: BLE001 — deliberately broad; caller decides how to handle
        warnings.warn(f"fit_mixedlm failed for formula '{formula}': {exc}")
        return None


def random_effects_meta(
    effects: np.ndarray, variances: np.ndarray
) -> Dict[str, float]:
    """DerSimonian-Laird random-effects meta-analysis over per-dataset effect sizes.

    Used by 06_meta_analysis_boas_anphy.py to combine ANPHY + BOAS per-endpoint
    effect sizes from Pass A1/A2. With only two datasets this is a coarse
    summary (tau^2 estimated from k=2 studies), not a substitute for a
    proper multi-study meta-analysis — treat as descriptive pooling.
    """
    effects = np.asarray(effects, dtype=float)
    variances = np.asarray(variances, dtype=float)
    mask = np.isfinite(effects) & np.isfinite(variances) & (variances > 0)
    effects, variances = effects[mask], variances[mask]
    k = len(effects)
    if k == 0:
        return {"pooled_effect": np.nan, "se": np.nan, "z": np.nan, "p": np.nan, "tau2": np.nan, "k": 0}

    w_fixed = 1.0 / variances
    fixed_effect = np.sum(w_fixed * effects) / np.sum(w_fixed)
    q = np.sum(w_fixed * (effects - fixed_effect) ** 2)
    df = k - 1
    c = np.sum(w_fixed) - np.sum(w_fixed ** 2) / np.sum(w_fixed) if k > 1 else 1.0
    tau2 = max(0.0, (q - df) / c) if k > 1 and c > 0 else 0.0

    w_random = 1.0 / (variances + tau2)
    pooled = np.sum(w_random * effects) / np.sum(w_random)
    se = np.sqrt(1.0 / np.sum(w_random))
    z = pooled / se if se > 0 else np.nan
    p = float(2 * (1 - stats.norm.cdf(abs(z)))) if np.isfinite(z) else np.nan
    return {"pooled_effect": float(pooled), "se": float(se), "z": float(z), "p": p, "tau2": float(tau2), "k": k}


def fit_ols_cluster(
    formula: str,
    data: pd.DataFrame,
    groups_col: str = "subject_id",
) -> Optional["object"]:
    """Fit an OLS model with cluster-robust standard errors by `groups_col`.

    This is the A1-primary fallback (plan1.md / sciencelead correction,
    2026-07-02): the one-row-per-event delta table is often too sparse per
    subject for a random-intercept MixedLM to identify (singular random
    effects covariance, degenerate p=1.0 fits). An OLS intercept model with
    cluster-robust SEs respects the same subject-clustering structure without
    requiring a variance component to be estimated, and does not degenerate
    the same way.
    """
    import warnings

    try:
        import statsmodels.formula.api as smf
    except ImportError:
        warnings.warn(
            "statsmodels is not installed; fit_ols_cluster() is returning None. "
            "pip install statsmodels to enable cluster-robust OLS fitting."
        )
        return None

    try:
        model = smf.ols(formula, data=data)
        return model.fit(cov_type="cluster", cov_kwds={"groups": data[groups_col]})
    except Exception as exc:  # noqa: BLE001
        warnings.warn(f"fit_ols_cluster failed for formula '{formula}': {exc}")
        return None


def fit_wls_cluster(
    formula: str,
    data: pd.DataFrame,
    weights_col: str,
    groups_col: str = "subject_id",
) -> Optional["object"]:
    """Fit a WLS model (weights = `weights_col`, typically `1 / n_events_subject`
    to approximate equal-subject weighting in a pooled event-level regression)
    with cluster-robust SE by `groups_col`.

    Used by Pass C (sciencelead/001.md protocol amendment, 2026-07-03): the
    same event-count imbalance that motivated the A1r subject-weighted primary
    also risks letting high-event-count subjects dominate the pooled EAP
    moderation slope. Weighting each event by 1/n_events_subject makes every
    subject contribute the same total weight regardless of event count.
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


def subject_level_slopes(
    x: np.ndarray, y: np.ndarray, groups: np.ndarray, *, min_events: int = 3
) -> pd.Series:
    """Per-subject OLS slope of y on x (simple bivariate regression, no
    covariates — within-subject N is usually too small for more). Subjects
    with fewer than `min_events` events are skipped. Returns a Series indexed
    by subject with one slope per subject, for use with
    subject_level_sensitivity()/sign_flip_permutation_test() to test whether
    the moderation slope differs from 0 across subjects, independent of how
    many events any single subject contributed.
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
    """A1-sensitivity-1: aggregate to one row per subject (mean delta), then
    one-sample t-test and Wilcoxon signed-rank against 0.

    Avoids pseudo-replication from subjects contributing very different
    numbers of events, and gives an easily interpretable subject-level effect.
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
    """A1-sensitivity-2: within-subject sign-flip permutation test.

    Under H0 (no true event-vs-matched-control geometry difference), each
    event's sign is exchangeable, since which side of the pair is "event" vs
    "control" carries no information. For each of `n_perm` permutations,
    every event-level delta has its sign flipped independently at random;
    the test statistic is the grand mean of per-subject mean deltas (matching
    subject_level_sensitivity's aggregation, so it respects clustering).

    Returns (observed_statistic, two_sided_permutation_p).
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


def one_sample_ci(values: np.ndarray, confidence: float = 0.95) -> Tuple[float, float, float]:
    """Mean and analytic t-based (1-confidence) CI for a 1-D sample (e.g. subject
    means for the A1r/A2r subject-weighted primary estimand). Returns
    (mean, ci_lo, ci_hi); (nan, nan, nan) if fewer than 2 finite values.
    """
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    n = len(v)
    if n < 2:
        return np.nan, np.nan, np.nan
    mean = float(v.mean())
    se = float(v.std(ddof=1) / np.sqrt(n))
    t_crit = float(stats.t.ppf(1 - (1 - confidence) / 2, df=n - 1))
    return mean, mean - t_crit * se, mean + t_crit * se


def circular_mean_resultant(phases: np.ndarray) -> Tuple[float, float, int]:
    """Circular mean angle and mean resultant length R in [0, 1] for a set of
    angles (radians, any range - only the unit-circle position matters).
    Returns (mean_angle, R, n).
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
    """Rayleigh test for non-uniformity of a circular distribution.

    Zar (1999) large-sample approximation for the Rayleigh test p-value
    (valid for n gtrsim 10; used descriptively here, not as an
    asymptotically-exact test for very small n). Returns (R, p, n).

    H0: phases are uniformly distributed on the circle (no preferred phase).
    A significant result indicates concentration around a single mean
    direction, NOT which direction - report the mean angle from
    circular_mean_resultant() alongside this.
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
    """(R1, R2, T2) for a pooled set of phases (radians).

    R1 = |mean(exp(i*phase))|   (Rayleigh resultant length, first harmonic)
    R2 = |mean(exp(2i*phase))|  (second harmonic; axial/bimodal-sensitive)
    T2 = R1**2 + R2**2          (simple omnibus statistic)

    T2 is an honestly-labelled analogue of Hermans-Rasson's robustness-to-
    multimodality motivation, NOT a re-implementation of that literature
    statistic itself (added 2026-07-10, diary 241, to avoid risking a subtly
    wrong formula). Used with Monte Carlo permutation p-values throughout
    (see subject_rotation_permutation_test), so no asymptotic-formula
    dependence is introduced by using a non-standard statistic.
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
    """Pseudo-replication-safe permutation test for population-level
    circular non-uniformity (diary 241; 02_response.md S7, option 3).

    Corrects a real flaw identified in an earlier proposed null (shuffling
    *subject labels* on a fixed pooled angle set does not change the pooled
    statistic at all, since that statistic is a function of the angle
    multiset only). Null here: for each permutation, draw one iid
    Uniform(0, 2*pi) rotation per subject and add it to *all* of that
    subject's phases. This destroys any common population-level preferred
    phase / axial alignment while exactly preserving each subject's event
    count, within-subject clustering, and the observed unequal per-subject
    sampling -- giving a Monte Carlo p-value with no asymptotic-formula
    dependence.
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


def subject_cluster_bootstrap_ci(
    phases: np.ndarray, subjects: np.ndarray, *, n_boot: int = 2000, seed: int = 43,
) -> Dict[str, float]:
    """Resample subjects with replacement, keeping each selected subject's
    full event set (diary 241; 02_response.md S7, option 2). Describes
    estimation stability (a CI on R1), not a hypothesis-test p-value.
    """
    phases = np.asarray(phases, dtype=float)
    subjects = np.asarray(subjects)
    mask = np.isfinite(phases)
    phases, subjects = phases[mask], subjects[mask]
    unique_subj = np.unique(subjects)
    n_subj = len(unique_subj)
    by_subject = {s: phases[subjects == s] for s in unique_subj}
    rng = np.random.default_rng(seed)

    boot_r1 = np.empty(n_boot)
    for k in range(n_boot):
        chosen = rng.choice(unique_subj, size=n_subj, replace=True)
        pooled = np.concatenate([by_subject[s] for s in chosen])
        r1, _, _ = harmonic_stats(pooled)
        boot_r1[k] = r1

    return {
        "boot_R1_mean": float(np.nanmean(boot_r1)),
        "boot_R1_ci_lo": float(np.nanpercentile(boot_r1, 2.5)),
        "boot_R1_ci_hi": float(np.nanpercentile(boot_r1, 97.5)),
    }


def binary_subject_level_test(flag: np.ndarray, subjects: np.ndarray) -> Dict[str, float]:
    """Subject-level proportion of a binary flag (e.g. inhale_at_onset) vs.
    the 0.5 null: aggregate to one proportion per subject first (avoids
    pseudo-replication by construction), then one-sample t-test + Wilcoxon
    across subjects.
    """
    df = pd.DataFrame({"flag": flag, "subject": subjects}).dropna()
    subj_props = df.groupby("subject")["flag"].mean()
    n_subj = len(subj_props)
    t_stat, t_p = stats.ttest_1samp(subj_props.values, 0.5)
    try:
        _, w_p = stats.wilcoxon(subj_props.values - 0.5)
    except ValueError:
        w_p = np.nan
    return {
        "n_subjects": n_subj, "mean_subject_proportion_inhale": float(subj_props.mean()),
        "ttest_stat": float(t_stat), "ttest_p": float(t_p), "wilcoxon_p": float(w_p),
    }


def aggregate_controls_per_event(
    df: pd.DataFrame,
    value_cols: List[str],
    *,
    match_col: str = "matched_event_id",
    extra_group_cols: Optional[List[str]] = ("dataset_id",),
) -> pd.DataFrame:
    """Aggregate matched_control rows to one row per (dataset, matched_event_id) (median).

    `matched_event_id` on control rows links back to the source spindle's
    `event_id` (handover_From_nmd.md §2). `extra_group_cols` defaults to
    `dataset_id` so that event ids are not accidentally collapsed across the
    two datasets. Avoids row-level pseudo-replication from the very large
    control pools (plan2.md "Avoid row-level pseudo-replication": ANPHY
    controls ~34k rows, BOAS controls ~192k rows, vs. far fewer spindle-event
    rows).
    """
    controls = df[df["condition"] == CONDITION_CONTROL].copy()
    avail = [c for c in value_cols if c in controls.columns]
    group_cols = [*(extra_group_cols or []), match_col]
    agg = controls.groupby(group_cols)[avail].median().reset_index()
    agg = agg.rename(columns={c: f"{c}_control_median" for c in avail})
    return agg
