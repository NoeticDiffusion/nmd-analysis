"""Shared helpers for the coma "turning-angle geometry" pipeline.

Background
----------
``plan.md`` (this article's plan file, not edited by this module) was
originally written for the first-episode-psychosis resting-state cohorts
(ds003944/ds003947), proposing that three-point turning angles along the MNPS
trajectory - computed in 3D, 9D, and per-family 3D subspaces - might separate
groups by directional persistence vs. abrupt redirection. This module adapts
that same geometry to the I-CARE cardiac-arrest coma cohort, contrasting CPC1
(good outcome) vs. CPC5 (poor outcome) instead of psychosis medication groups.

Reuse policy
------------
This pipeline does **not** re-extract H5 data. It reuses the per-epoch 9D +
composite chart series already extracted (first 12h post-arrest, subject-
anchored contract) by the sibling ``comatose_ndt_first12h_phase_shift``
pipeline's ``01_extract_epoch_series.py``. Those parquet files already carry
one row per (subject, run, acq, epoch_idx) with all nine 9D-chart axes plus
the ``m``, ``d``, ``e`` composites.

Native-3D equivalence
----------------------
The ``m``, ``d``, ``e`` composite columns in that upstream parquet are
computed with the exact fixed weights documented as the *native* ``mnps_3d``
recomposition in ``articles/CLINICAL/comatose_ndt/S1_Supplementary_methods.typ``::

    m_t = 0.62 m_a + 0.55 m_e + 0.45 m_o
    d_t = 0.50 d_n + 0.82 d_l + 0.28 d_s
    e_t = 0.85 e_e + 0.62 e_s + 0.03 e_m

So treating those three columns as the "native 3D chart" for the primary
turning-angle analysis is not an approximation particular to this pipeline;
it is the same chart already used elsewhere in the ``comatose_ndt`` family of
articles.

Scope of this implementation pass
----------------------------------
Per plan.md's "recommended analysis hierarchy", this pipeline implements:

1. Native 3D turning (``m``, ``d``, ``e``) - primary.
2. Native 9D turning (all nine chart axes) - secondary.
3. Family-specific 3D turning: ``m_*=[m_a,m_e,m_o]``, ``d_*=[d_n,d_l,d_s]``,
   ``e_*=[e_e,e_s,e_m]``.
4. Lag sensitivity, ell in {1, 2, 4} epochs (~4s, ~8s, ~16s at the fixed
   4s MNPS step).
5. Step-length filtering (exclude turning triples whose adjacent step is
   below the pooled 10th percentile for that chart+lag).
6. Within-run displacement-permutation null -> per-run Z-score.
7. CPC1-vs-CPC5 contrast (replacing plan.md's medication-stratified
   contrast, since coma has no medication axis) - see ``03_cpc_contrast.py``.

**Not** implemented in this pass: the metric-adjusted (shrinkage-covariance)
9D angle. plan.md itself labels that layer "robustness only"; it is left as
a documented follow-up (see this article's README.md).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
ARTICLE_DIR = SRC_DIR.parent
CLINICAL_DIR = ARTICLE_DIR.parent
REPO_ROOT = CLINICAL_DIR.parents[1]

COMATOSE_NDT_SRC = CLINICAL_DIR / "comatose_ndt" / "src"
PHASE_SHIFT_SRC = CLINICAL_DIR / "comatose_ndt_first12h_phase_shift" / "src"
PHASE_SHIFT_RESULTS = CLINICAL_DIR / "comatose_ndt_first12h_phase_shift" / "results" / "epoch_series"

for _path in (COMATOSE_NDT_SRC, PHASE_SHIFT_SRC):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


# ---------------------------------------------------------------------------
# Chart / lag definitions
# ---------------------------------------------------------------------------

NAMES_9D: Tuple[str, ...] = ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m")

# chart_name -> ordered list of coordinate columns forming that chart.
CHARTS: Dict[str, Tuple[str, ...]] = {
    "3d": ("m", "d", "e"),
    "9d": NAMES_9D,
    "m3": ("m_a", "m_e", "m_o"),
    "d3": ("d_n", "d_l", "d_s"),
    "e3": ("e_e", "e_s", "e_m"),
}

# Lags in units of epochs (fixed 4s MNPS step -> 4s/8s/16s).
LAGS: Tuple[int, ...] = (1, 2, 4)

# Minimum number of valid (post-filtering) turning triples required to report
# summary statistics for a (run, chart, lag) cell, analogous in spirit to
# MIN_EPOCHS_FOR_PELT in the sibling phase-shift pipeline, but angles need
# less data since there is no changepoint model to fit.
MIN_VALID_ANGLES: int = 30

# Pooled step-length filter: triples where either adjacent step is below this
# percentile (computed per chart+lag, pooled across the whole deduped cohort)
# are excluded, per plan.md section 5 ("essential protection against false
# effects").
STEP_LENGTH_FILTER_PERCENTILE: float = 10.0

# Within-run displacement-permutation null (plan.md section 7).
N_PERMUTATIONS: int = 200
PERMUTATION_SEED_BASE: int = 20260718

# Fixed-width bins (degrees) used for the turn_entropy diversity metric.
ENTROPY_N_BINS: int = 12

EPS = 1e-12


# Columns actually needed downstream (age/sex/timing_source are dropped to
# reduce peak memory - this pipeline runs under real memory pressure from
# unrelated concurrent jobs on this machine).
EPOCH_SERIES_COLUMNS: Tuple[str, ...] = (
    "subject",
    "run",
    "acq",
    "cohort_tag",
    "cpc",
    "hospital",
    "epoch_idx",
    "t_hours_from_anchor",
    "m_a",
    "m_e",
    "m_o",
    "d_n",
    "d_l",
    "d_s",
    "e_e",
    "e_s",
    "e_m",
    "m",
    "d",
    "e",
)


def load_epoch_series(paths: Tuple[Path, ...]) -> pd.DataFrame:
    """Load and concatenate one or more epoch-series parquet files.

    Only reads ``EPOCH_SERIES_COLUMNS`` (not the full schema) to reduce peak
    memory. Does not deduplicate; callers should follow with a
    ``build_run_key``/``deduplicate_by_key`` pass (see
    ``merge_coma_cohort_results.py``) before computing turning angles, since
    the same run may be present in both a part1 and a part2 export.
    """
    frames = []
    for path in paths:
        frame = pd.read_parquet(path)
        columns = [c for c in EPOCH_SERIES_COLUMNS if c in frame.columns]
        frames.append(frame[columns])
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def available_charts(columns: pd.Index) -> Dict[str, Tuple[str, ...]]:
    """Restrict CHARTS to those whose columns are all present (graceful degradation)."""
    return {name: cols for name, cols in CHARTS.items() if all(col in columns for col in cols)}


def unit_vectors(vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (unit_vectors, norms); zero/degenerate rows get a NaN unit row."""
    norms = np.linalg.norm(vectors, axis=1)
    safe = np.where(norms > EPS, norms, np.nan)
    units = vectors / safe[:, None]
    return units, norms


def compute_lag_displacements(coords: np.ndarray, lag: int) -> tuple[np.ndarray, np.ndarray]:
    """Elementary lag-``lag`` displacement vectors ``x[t+lag]-x[t]`` and their norms.

    These are the building blocks both for pooling step-length statistics
    (across the whole cohort) and for constructing turning triples: for a
    turning angle at position t, ``u_t`` is the displacement ending at t and
    ``v_t`` is the displacement starting at t, i.e. both are drawn from this
    same elementary-displacement population, just offset by one lag.
    """
    n = coords.shape[0]
    if n <= lag:
        return np.empty((0, coords.shape[1])), np.empty(0)
    disp = coords[lag:] - coords[:-lag]
    _, norms = unit_vectors(disp)
    return disp, norms


def compute_turning_triples(
    coords: np.ndarray, lag: int, *, step_length_threshold: float
) -> Optional[dict]:
    """Compute filtered turning-angle triples for one (run, chart, lag) series.

    Returns None if fewer than ``MIN_VALID_ANGLES`` triples survive both the
    finiteness and step-length filters. Otherwise returns a dict with the
    filtered ``cos_theta``, ``theta_deg`` (arccos, degrees), mean step length
    per triple, and the *unfiltered* elementary displacement unit vectors
    (needed by the permutation null, which intentionally does not apply the
    step-length filter - see plan.md section 7: the null preserves "all
    displacement vectors and their lengths").
    """
    n = coords.shape[0]
    if n <= 2 * lag:
        return None

    finite_mask_rows = np.isfinite(coords).all(axis=1)
    disp, disp_norms = compute_lag_displacements(coords, lag)
    disp_finite = np.isfinite(disp_norms)

    # Triples indexed by center position t in [lag, n-lag).
    t_idx = np.arange(lag, n - lag)
    u = coords[t_idx] - coords[t_idx - lag]
    v = coords[t_idx + lag] - coords[t_idx]
    u_units, u_norms = unit_vectors(u)
    v_units, v_norms = unit_vectors(v)

    valid = (
        finite_mask_rows[t_idx - lag]
        & finite_mask_rows[t_idx]
        & finite_mask_rows[t_idx + lag]
        & np.isfinite(u_norms)
        & np.isfinite(v_norms)
    )
    step_ok = valid & (u_norms >= step_length_threshold) & (v_norms >= step_length_threshold)

    if int(step_ok.sum()) < MIN_VALID_ANGLES:
        return None

    cos_theta = np.sum(u_units[step_ok] * v_units[step_ok], axis=1)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    theta_deg = np.degrees(np.arccos(cos_theta))
    mean_step = 0.5 * (u_norms[step_ok] + v_norms[step_ok])

    return {
        "cos_theta": cos_theta,
        "theta_deg": theta_deg,
        "mean_step_length": mean_step,
        "n_valid": int(step_ok.sum()),
        "n_excluded_short_step": int(valid.sum() - step_ok.sum()),
        "n_total_triples": int(valid.size),
        "disp_units": disp[disp_finite],  # for the permutation null, unfiltered
        "disp_norms": disp_norms[disp_finite],
    }


def angle_entropy(theta_deg: np.ndarray, n_bins: int = ENTROPY_N_BINS) -> float:
    """Shannon entropy (nats) of the angle histogram over [0, 180] degrees.

    Not normalized by log(n_bins): larger values indicate a more diverse mix
    of turning regimes (straight-continuation, orthogonal, reversal) rather
    than a single dominant regime. Bounded above by log(n_bins).
    """
    theta_deg = theta_deg[np.isfinite(theta_deg)]
    if theta_deg.size == 0:
        return float("nan")
    counts, _ = np.histogram(theta_deg, bins=n_bins, range=(0.0, 180.0))
    total = counts.sum()
    if total <= 0:
        return float("nan")
    p = counts / total
    p_nonzero = p[p > 0]
    return float(-np.sum(p_nonzero * np.log(p_nonzero)))


def turn_length_coupling(theta_deg: np.ndarray, mean_step_length: np.ndarray) -> float:
    """Spearman correlation between turning angle and local step length.

    Answers plan.md's "whether large turns occur during large or tiny steps".
    NaN if either series is (near-)constant or too short for a stable
    correlation.
    """
    from scipy.stats import spearmanr

    if theta_deg.size < 5:
        return float("nan")
    if np.nanstd(theta_deg) < EPS or np.nanstd(mean_step_length) < EPS:
        return float("nan")
    rho, _ = spearmanr(theta_deg, mean_step_length)
    return float(rho) if np.isfinite(rho) else float("nan")


def permutation_null_z(
    disp_units: np.ndarray, observed_median_theta_deg: float, *, seed: int, n_perms: int = N_PERMUTATIONS
) -> tuple[float, float, float]:
    """Within-run displacement-permutation null (plan.md section 7).

    Randomly permutes the temporal order of the (unfiltered) unit
    displacement vectors ``n_perms`` times, and for each permutation
    recomputes the median turning angle between *consecutive* shuffled
    vectors (this is exactly the lag-1-in-permutation-order pairing implied
    by "preserve all displacement vectors ... but randomly permute their
    temporal order"). Returns (z_score, null_mean, null_sd) for the observed
    vs. null median-angle distribution.

    A positive Z means the run's *observed* trajectory is *more* organized
    (turns less, on average) than its own displacement repertoire would
    produce under random re-ordering; equivalently, per plan.md, the
    strong-form hypothesis compares Z_theta across outcome groups, not the
    raw angle.
    """
    n = disp_units.shape[0]
    if n < MIN_VALID_ANGLES + 1 or not np.isfinite(observed_median_theta_deg):
        return float("nan"), float("nan"), float("nan")

    rng = np.random.default_rng(seed)
    perm_indices = np.argsort(rng.random((n_perms, n)), axis=1)
    shuffled = disp_units[perm_indices]  # [n_perms, n, d]
    cos_pairs = np.sum(shuffled[:, :-1, :] * shuffled[:, 1:, :], axis=2)
    cos_pairs = np.clip(cos_pairs, -1.0, 1.0)
    theta_pairs_deg = np.degrees(np.arccos(cos_pairs))
    null_medians = np.nanmedian(theta_pairs_deg, axis=1)  # [n_perms]
    null_medians = null_medians[np.isfinite(null_medians)]
    if null_medians.size < 2:
        return float("nan"), float("nan"), float("nan")

    null_mean = float(np.mean(null_medians))
    null_sd = float(np.std(null_medians, ddof=1))
    if null_sd < EPS:
        return float("nan"), null_mean, null_sd
    z = float((observed_median_theta_deg - null_mean) / null_sd)
    return z, null_mean, null_sd


def stable_seed(*parts: object) -> int:
    """Deterministic per-(run, chart, lag) permutation seed, offset from a fixed base.

    Uses ``hashlib`` rather than the builtin ``hash()``, which is randomized
    per-process (``PYTHONHASHSEED``) for strings and would make permutation
    results non-reproducible across runs/workers.
    """
    import hashlib

    text = "|".join(str(p) for p in parts)
    digest = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
    return (PERMUTATION_SEED_BASE + digest) % (2**32 - 1)
