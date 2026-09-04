"""Shared support for the Stratified Family Temporal Coupling (SFTC) test run.

SFTC asks whether one MNPS 9D family (m, d, or e) systematically leads
changes in another family, using time-lagged cross-correlation on the same
APPLESEED cohort-anchored trajectories already used by the parent
`APPLESEED_infants` article. This module intentionally reuses that article's
H5 discovery, identity parsing, and low-level statistics helpers instead of
duplicating them, so that subject/session identity and the paired-contrast
machinery stay identical to the parent article.

Definition (matches `project/features/trajectory_geometry/trajectory_geometry.md`):

    bar_a_t  = mean of family a's three 9D axes at epoch t
    delta_a_t = bar_a_{t+1} - bar_a_t
    C_ab(tau) = corr(delta_a_t, bar_b_{t-tau})   # does b's earlier level predict a's next change?
    A_ab(tau) = C_ab(tau) - C_ba(tau)            # positive => b leads a more than a leads b

Correlations are Spearman (robust to the heavy-tailed, non-Gaussian marginal
shapes already documented for these coordinates elsewhere in this repo), and
are pooled within-subject across all valid lagged pairs from all contiguous
epoch segments in one session (never crossing a QC/time gap).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import h5py
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

SRC_DIR = Path(__file__).resolve().parent
ARTICLE_DIR = SRC_DIR.parent
REPO_ROOT = ARTICLE_DIR.parents[1]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
APPLESEED_SRC = REPO_ROOT / "articles" / "APPLESEED_infants" / "src"
for path in (NDT_ANALYSIS_ROOT, APPLESEED_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ndt_analysis.h5_contract import resolve_coords_9d  # noqa: E402
from appleseed_support import (  # noqa: E402
    DEFAULT_DATA_ROOT,
    COORDINATE_CONTRACT,
    bh_fdr,
    bootstrap_icc,
    finite_median,
    h5_paths,
    icc_a1,
    paired_summary,
    participant_metadata,
    session_identity,
)

NAMES_9D: Tuple[str, ...] = ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m")
FAMILIES: Dict[str, Tuple[str, ...]] = {
    "m": ("m_a", "m_e", "m_o"),
    "d": ("d_n", "d_l", "d_s"),
    "e": ("e_e", "e_s", "e_m"),
}
FAMILY_NAMES: Tuple[str, ...] = tuple(FAMILIES.keys())
ORDERED_PAIRS: Tuple[Tuple[str, str], ...] = tuple(
    (a, b) for a in FAMILY_NAMES for b in FAMILY_NAMES if a != b
)
UNORDERED_PAIRS: Tuple[Tuple[str, str], ...] = (("d", "e"), ("m", "d"), ("m", "e"))
LAGS: Tuple[int, ...] = (1, 2, 4)
MIN_VALID_PAIRS = 20
TIME_GAP_FACTOR = 1.5
EPS = 1e-12


def read_time(handle: h5py.File, length: int) -> np.ndarray:
    if "time" in handle:
        values = np.asarray(handle["time"], dtype=float)
    elif "window_start" in handle and "window_end" in handle:
        values = 0.5 * (np.asarray(handle["window_start"], dtype=float) + np.asarray(handle["window_end"], dtype=float))
    elif "window_start" in handle:
        values = np.asarray(handle["window_start"], dtype=float)
    else:
        values = np.arange(length, dtype=float)
    return values[:length]


def contiguous_segments(time: np.ndarray) -> List[np.ndarray]:
    """Row-index segments, breaking at non-positive, non-finite, or large time gaps."""
    time = np.asarray(time, dtype=float)
    if time.size == 0:
        return []
    finite = np.isfinite(time)
    diffs = np.diff(time)
    positive = diffs[np.isfinite(diffs) & (diffs > 0)]
    baseline = float(np.median(positive)) if positive.size else 1.0
    gap = max(baseline * TIME_GAP_FACTOR, baseline + EPS)
    breaks = np.r_[True, ~finite[1:] | ~finite[:-1] | (diffs <= 0) | (diffs > gap)]
    valid_indices = np.flatnonzero(finite)
    if valid_indices.size == 0:
        return []
    segments: List[np.ndarray] = []
    start = 0
    for index in range(1, valid_indices.size):
        if valid_indices[index] != valid_indices[index - 1] + 1 or breaks[valid_indices[index]]:
            segments.append(valid_indices[start:index])
            start = index
    segments.append(valid_indices[start:])
    return [segment for segment in segments if segment.size]


def family_series(coords9: np.ndarray, names9: Iterable[str]) -> Dict[str, np.ndarray]:
    """Unweighted per-epoch mean of each family's three 9D axes."""
    names = list(names9)
    index = {name: i for i, name in enumerate(names)}
    if not all(name in index for name in NAMES_9D):
        return {}
    return {
        family: np.mean(np.column_stack([coords9[:, index[name]] for name in axes]), axis=1)
        for family, axes in FAMILIES.items()
    }


def read_subject_h5(path: Path) -> Dict[str, Any] | None:
    with h5py.File(path, "r") as handle:
        resolved = resolve_coords_9d(handle, COORDINATE_CONTRACT)
        if resolved is None:
            return None
        coords9 = np.asarray(resolved.values, dtype=float)
        names9 = tuple(resolved.names)
        time = read_time(handle, coords9.shape[0])
        n_rows = min(coords9.shape[0], time.size)
        if n_rows == 0:
            return None
        participant = participant_metadata(handle)
    families = family_series(coords9[:n_rows], names9)
    if not families:
        return None
    identity = session_identity(path)
    return {
        **identity,
        "sex": participant.get("sex"),
        "source_group": participant.get("group"),
        "families": families,
        "time": np.asarray(time[:n_rows], dtype=float),
        "n_timepoints": int(n_rows),
    }


def _pooled_lag_pairs(
    families: Dict[str, np.ndarray], segments: Iterable[np.ndarray], receiver: str, driver: str, lag: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Pool (delta_receiver_t, driver_{t-lag}) pairs across contiguous segments."""
    delta_chunks: List[np.ndarray] = []
    driver_chunks: List[np.ndarray] = []
    for segment in segments:
        if segment.size <= lag + 1:
            continue
        receiver_values = families[receiver][segment]
        driver_values = families[driver][segment]
        delta = receiver_values[1:] - receiver_values[:-1]  # delta_t indexed by t = 0..n-2
        # delta_t (change starting at t) pairs with driver level at (t - lag); need t - lag >= 0
        if delta.shape[0] <= lag:
            continue
        delta_lagged = delta[lag:]
        driver_lagged = driver_values[: delta.shape[0] - lag]
        finite = np.isfinite(delta_lagged) & np.isfinite(driver_lagged)
        if finite.any():
            delta_chunks.append(delta_lagged[finite])
            driver_chunks.append(driver_lagged[finite])
    if not delta_chunks:
        return np.empty(0), np.empty(0)
    return np.concatenate(delta_chunks), np.concatenate(driver_chunks)


def compute_family_coupling(families: Dict[str, np.ndarray], segments: List[np.ndarray]) -> List[Dict[str, Any]]:
    """Return one row per (receiver, driver, lag) with Spearman C_ab(tau)."""
    rows: List[Dict[str, Any]] = []
    for receiver, driver in ORDERED_PAIRS:
        for lag in LAGS:
            delta, driver_lag = _pooled_lag_pairs(families, segments, receiver, driver, lag)
            n_pairs = int(delta.size)
            if n_pairs >= MIN_VALID_PAIRS and np.std(delta) > EPS and np.std(driver_lag) > EPS:
                rho, p_value = spearmanr(delta, driver_lag)
            else:
                rho, p_value = float("nan"), float("nan")
            rows.append(
                {
                    "receiver_family": receiver,
                    "driver_family": driver,
                    "lag_epochs": lag,
                    "n_pairs": n_pairs,
                    "spearman_r": float(rho) if np.isfinite(rho) else float("nan"),
                    "spearman_p": float(p_value) if np.isfinite(p_value) else float("nan"),
                }
            )
    return rows


def wide_columns() -> List[str]:
    columns = [f"fc_r_{receiver}_recv_{driver}_drive_lag{lag}" for receiver, driver in ORDERED_PAIRS for lag in LAGS]
    columns += [f"fc_asym_{b}_minus_{a}_lag{lag}" for a, b in UNORDERED_PAIRS for lag in LAGS]
    return columns


def rows_to_wide(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    """Fold long-format coupling rows for one session into the fixed wide-column layout."""
    lookup = {(row["receiver_family"], row["driver_family"], row["lag_epochs"]): row["spearman_r"] for row in rows}
    wide: Dict[str, float] = {}
    for receiver, driver in ORDERED_PAIRS:
        for lag in LAGS:
            wide[f"fc_r_{receiver}_recv_{driver}_drive_lag{lag}"] = lookup.get((receiver, driver, lag), float("nan"))
    for a, b in UNORDERED_PAIRS:
        for lag in LAGS:
            r_b_drives_a = lookup.get((a, b, lag), float("nan"))  # C_ab: b's earlier level predicts a's change
            r_a_drives_b = lookup.get((b, a, lag), float("nan"))  # C_ba: a's earlier level predicts b's change
            wide[f"fc_asym_{b}_minus_{a}_lag{lag}"] = (
                r_a_drives_b - r_b_drives_a if np.isfinite(r_a_drives_b) and np.isfinite(r_b_drives_a) else float("nan")
            )
    return wide


def cohort_age_contrast(metrics: pd.DataFrame, endpoints: Tuple[str, ...], label: str, target_session: int) -> pd.DataFrame:
    """Balanced paired age contrast: mean(session 1, 2) at 4m versus a follow-up session.

    Identical statistical design to `APPLESEED_infants/src/02_reliability_longitudinal.py`
    (`cohort_age_contrast`), reimplemented here against the same low-level
    `paired_summary`/`bh_fdr` helpers so the two articles stay comparable.
    """
    target_label = {3: "8m", 4: "12m"}[target_session]
    eligible = metrics.groupby("subject_id")["session"].agg(set)
    eligible = eligible[eligible.apply(lambda visits: {1, 2, target_session}.issubset(visits))].index
    panel = metrics[metrics["subject_id"].isin(eligible)].pivot(index="subject_id", columns="session", values=list(endpoints))
    if panel.empty or not {1, 2, target_session}.issubset(set(panel.columns.get_level_values(1))):
        return pd.DataFrame(
            {
                "analysis_layer": [label] * len(endpoints),
                "endpoint": endpoints,
                "contrast": [f"age_{target_label}_minus_age_4m_mean"] * len(endpoints),
            }
        )
    rows = []
    for endpoint in endpoints:
        baseline = 0.5 * (panel[(endpoint, 1)] + panel[(endpoint, 2)])
        follow_up = panel[(endpoint, target_session)]
        rows.append(
            {
                "analysis_layer": label,
                "endpoint": endpoint,
                "contrast": f"age_{target_label}_minus_age_4m_mean",
                "n_eligible_subjects": len(panel),
                **paired_summary(baseline, follow_up),
            }
        )
    output = pd.DataFrame(rows)
    output["p_fdr"] = bh_fdr(output["p_raw"]) if "p_raw" in output else np.nan
    return output


def reliability_table(metrics: pd.DataFrame, endpoints: Tuple[str, ...], n_bootstrap: int, seed: int) -> pd.DataFrame:
    """4m-test vs 4m-retest ICC(A,1), same design as the parent article's reliability_table."""
    paired = metrics.pivot(index="subject_id", columns="session", values=list(endpoints))
    rows = []
    for endpoint in endpoints:
        a = paired[(endpoint, 1)].to_numpy() if (endpoint, 1) in paired else np.full(len(paired), np.nan)
        b = paired[(endpoint, 2)].to_numpy() if (endpoint, 2) in paired else np.full(len(paired), np.nan)
        row = {"endpoint": endpoint, **icc_a1(a, b), **paired_summary(a, b)}
        row["icc_ci95_low"], row["icc_ci95_high"] = bootstrap_icc(a, b, n_bootstrap, seed)
        rows.append(row)
    output = pd.DataFrame(rows)
    output["p_fdr"] = bh_fdr(output["p_raw"])
    return output


__all__ = [
    "DEFAULT_DATA_ROOT",
    "COORDINATE_CONTRACT",
    "FAMILIES",
    "FAMILY_NAMES",
    "ORDERED_PAIRS",
    "UNORDERED_PAIRS",
    "LAGS",
    "MIN_VALID_PAIRS",
    "h5_paths",
    "read_subject_h5",
    "contiguous_segments",
    "compute_family_coupling",
    "wide_columns",
    "rows_to_wide",
    "cohort_age_contrast",
    "reliability_table",
    "finite_median",
]
