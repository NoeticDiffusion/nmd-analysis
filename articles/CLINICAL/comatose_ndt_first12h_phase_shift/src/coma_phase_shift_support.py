"""Shared helpers for the coma "d_n phase-shift" pipeline.

CRITICAL NAMING CAVEAT (read before using any coordinate named ``d_n``)
------------------------------------------------------------------------
The label ``d_n`` means two different things in this repository, and this
pipeline does **not** try to reconcile them:

* In ``articles/RVC_SLEEP`` (sleep spindles), ``d_n`` is a heat-kernel
  network-diffusivity term computed from a per-window graph Laplacian:
  ``d_n = 1 - norm(avg_W(Tr(e^{-t_h L(w)}) / |V|))`` (see
  ``articles/RVC_SLEEP/S1_Supplementary_methods.typ``).
* In ``articles/CLINICAL/comatose_ndt`` (I-CARE cardiac-arrest coma), under
  the current EEG feature contract ``d_n`` is an operational alias for
  ``eeg_gamma`` (log gamma-band power) - no graph or Laplacian is built for
  I-CARE at all (see ``articles/CLINICAL/comatose_ndt/S1_Supplementary_methods.typ``,
  the ``d`` / ``d_n`` / ``eeg_gamma`` row).

Because of this, this pipeline treats ``d_n`` as *one coordinate among many*
in the frozen 9D chart, rather than assuming it carries any particular
biophysical meaning inherited from the sleep article. Shift detection runs
on all nine chart coordinates plus the composite ``m``, ``d``, ``e`` axes,
and the CPC1-vs-CPC5 contrast (see ``04_cpc_contrast.py``) is what decides
which coordinate(s) - possibly ``d_n``, possibly not - carry a discriminative
shift signal.

Reuse policy
------------
This module intentionally reuses, rather than re-derives, the I-CARE H5
loading and cohort conventions already used and validated by the published
``comatose_ndt`` article (H5 discovery, run identity parsing, anchor-relative
timing, CPC labels, part1/part2 dedup, and outcome-contrast statistics). See
the imports below.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np

SRC_DIR = Path(__file__).resolve().parent
ARTICLE_DIR = SRC_DIR.parent
CLINICAL_DIR = ARTICLE_DIR.parent
REPO_ROOT = CLINICAL_DIR.parents[1]

COMATOSE_NDT_SRC = CLINICAL_DIR / "comatose_ndt" / "src"
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"

for _path in (COMATOSE_NDT_SRC, NDT_ANALYSIS_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


# The frozen 9D stratified chart, in the fixed release order used across
# every NDT article (S1_Supplementary_methods.typ, eq:core9d).
NAMES_9D: tuple[str, ...] = ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m")

# Fixed release composite-recomposition weights (identical formula quoted in
# both RVC_SLEEP and comatose_ndt S1 methods: m/d/e from the 9D chart).
COMPOSITE_WEIGHTS: dict[str, dict[str, float]] = {
    "m": {"m_a": 0.62, "m_e": 0.55, "m_o": 0.45},
    "d": {"d_n": 0.50, "d_l": 0.82, "d_s": 0.28},
    "e": {"e_e": 0.85, "e_s": 0.62, "e_m": 0.03},
}

# All coordinates the shift-detector runs on: the 9D chart plus the three
# fixed-weight composites. d_n is not privileged among these.
ALL_COORDINATES: tuple[str, ...] = (*NAMES_9D, "m", "d", "e")

# NDT MNPS window contract: 8s window, 50% overlap -> 4s step between epochs.
EPOCH_STEP_SEC: float = 4.0

# PELT / shift-detection defaults (documented here so they are one place to
# tune as a robustness check; see plan's "open implementation details").
PELT_MODEL: str = "rbf"
PELT_PENALTY_SCALE: float = 3.0
MIN_EPOCHS_FOR_PELT: int = 60  # ~4 minutes of data at 4s/epoch


def compute_composites(values_9d: np.ndarray, names: list[str]) -> dict[str, np.ndarray]:
    """Compute the fixed-weight m/d/e composites from a [T, 9] coordinate array.

    Returns an empty dict for any composite whose required 9D columns are
    missing from ``names`` (rather than raising), so callers can degrade
    gracefully on partial/legacy exports.
    """
    name_index = {name: idx for idx, name in enumerate(names)}
    out: dict[str, np.ndarray] = {}
    for composite_name, weights in COMPOSITE_WEIGHTS.items():
        if not all(component in name_index for component in weights):
            continue
        acc = np.zeros(values_9d.shape[0], dtype=float)
        for component, weight in weights.items():
            acc = acc + weight * values_9d[:, name_index[component]]
        out[composite_name] = acc
    return out


def robust_zscore(series: np.ndarray) -> np.ndarray:
    """Median/MAD standardization so PELT penalties are comparable across runs.

    Falls back to a tiny floor on scale so constant/near-constant segments
    (common near recording start/end or under heavy artifact rejection) do
    not blow up to +-inf.
    """
    values = np.asarray(series, dtype=float)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return values
    median = float(np.median(finite))
    mad = float(np.median(np.abs(finite - median)))
    scale = mad * 1.4826 if mad > 1e-9 else float(np.std(finite))
    if not np.isfinite(scale) or scale < 1e-9:
        scale = 1.0
    return (values - median) / scale


def welch_like_quality(before: np.ndarray, after: np.ndarray, magnitude: float) -> float:
    """A t-statistic-like "shift quality" score.

    This is *not* PELT's internal cost reduction (ruptures does not expose
    that per-breakpoint in a stable public API); it is our own explicit
    definition: the level-jump magnitude scaled by the harmonic mean of the
    two segment sizes, i.e. a Welch-style measure of how well-supported a
    given jump is by the surrounding data. Larger values indicate a jump
    that is both big and backed by enough samples on each side to be taken
    seriously; small segments produce a heavily discounted score even for a
    large raw magnitude. Documented explicitly so this is never confused
    with a p-value or a native ruptures cost value.
    """
    n_before, n_after = before.size, after.size
    if n_before == 0 or n_after == 0 or not np.isfinite(magnitude):
        return float("nan")
    harmonic_n = 2.0 * n_before * n_after / (n_before + n_after)
    return float(magnitude * np.sqrt(harmonic_n))


def detect_shifts_pelt(
    series: np.ndarray,
    *,
    model: str = PELT_MODEL,
    penalty_scale: float = PELT_PENALTY_SCALE,
) -> Optional[dict]:
    """Run PELT changepoint detection on one (already robust-z-scored) series.

    Returns ``None`` if the series is too short or degenerate. Otherwise
    returns a dict with per-breakpoint magnitude/quality plus run-level
    summary fields, ready to be flattened into a result row.
    """
    import ruptures as rpt

    values = np.asarray(series, dtype=float)
    finite_mask = np.isfinite(values)
    n_finite = int(finite_mask.sum())
    if n_finite < MIN_EPOCHS_FOR_PELT:
        return None

    # PELT requires a contiguous array; NaNs (artifact-rejected epochs) are
    # dropped rather than interpolated, so segment boundaries stay honest
    # about which epochs actually informed a detected shift.
    clean = values[finite_mask]
    penalty = penalty_scale * np.log(max(clean.size, 2))
    algo = rpt.Pelt(model=model, min_size=max(5, MIN_EPOCHS_FOR_PELT // 6)).fit(clean.reshape(-1, 1))
    breakpoints = algo.predict(pen=penalty)  # includes n_finite as the final "breakpoint"

    boundaries = [0, *breakpoints]
    segments = [clean[boundaries[i] : boundaries[i + 1]] for i in range(len(boundaries) - 1)]
    internal_breakpoints = breakpoints[:-1]

    magnitudes: list[float] = []
    qualities: list[float] = []
    for seg_idx in range(len(segments) - 1):
        before, after = segments[seg_idx], segments[seg_idx + 1]
        pooled_var = (
            (before.size - 1) * np.var(before, ddof=1) + (after.size - 1) * np.var(after, ddof=1)
        ) / max(before.size + after.size - 2, 1)
        pooled_sd = float(np.sqrt(pooled_var)) if pooled_var > 0 else float("nan")
        magnitude = float(abs(np.mean(after) - np.mean(before)) / pooled_sd) if np.isfinite(pooled_sd) and pooled_sd > 0 else float("nan")
        magnitudes.append(magnitude)
        qualities.append(welch_like_quality(before, after, magnitude))

    segment_lengths = np.diff(boundaries)
    return {
        "n_epochs_analyzed": n_finite,
        "n_shifts": int(len(internal_breakpoints)),
        "shift_epoch_indices": [int(bp) for bp in internal_breakpoints],
        "shift_magnitudes": magnitudes,
        "shift_qualities": qualities,
        "median_segment_length_epochs": float(np.median(segment_lengths)) if segment_lengths.size else float("nan"),
        "pelt_model": model,
        "pelt_penalty": float(penalty),
    }
