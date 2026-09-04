"""Shared paths, H5 readers, statistics, and provenance for APPLESEED."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

DEFAULT_DATA_ROOT = (
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003710_20260804_153346"
)
DEFAULT_RESULTS_ROOT = ARTICLE_DIR / "results" / "appleseed_cohort_20260805"
COORDINATE_CONTRACT = "cohort_anchored"
EVENT_COORDINATE_CONTRACT = "subject_anchored"
PRIMARY_ENDPOINTS = (
    "frobenius_norm_median",
    "rotation_norm_median",
    "trace_median",
    "spectral_radius_median",
    "tube_log_det_median",
    "tube_d_eff_median",
    "tube_kappa_median",
    "tube_dir_entropy_median",
    "tube_rotation_median",
)
CONVENTIONAL_ENDPOINTS = (
    "eeg_conventional_ratio_alpha_theta",
    "eeg_conventional_ratio_beta_alpha",
    "eeg_conventional_relative_delta",
    "eeg_conventional_complexity_permutation_entropy",
)
SESSION_RE = re.compile(r"^(sub-\d+)_(?:ses-(\d+)|age_(4m_test|4m_retest|8m|12m))_appleseedexample\.h5$")
SESSION_AGE_DAYS = {1: 125.0, 2: 133.0, 3: 242.0, 4: 355.0}
AGE_TOKEN_TO_SESSION = {"4m_test": 1, "4m_retest": 2, "8m": 3, "12m": 4}


def decode(value: Any) -> str:
    """Decode scalar H5 text values without assuming an H5 string dtype."""
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        return bytes(value).decode("utf-8")
    return str(value)


def h5_paths(data_root: Path) -> list[Path]:
    """Return the deterministic APPLESEED H5 file order."""
    paths = sorted(data_root.rglob("*.h5"))
    if not paths:
        raise FileNotFoundError(f"No APPLESEED H5 files found under {data_root}")
    return paths


def session_identity(h5_path: Path) -> dict[str, Any]:
    """Parse subject/session identity from the export filename."""
    match = SESSION_RE.match(h5_path.name)
    if not match:
        raise ValueError(f"Unexpected APPLESEED H5 filename: {h5_path.name}")
    session = int(match.group(2)) if match.group(2) else AGE_TOKEN_TO_SESSION[match.group(3)]
    return {
        "subject_id": match.group(1),
        "session": session,
        "age_stratum": ("age_" + match.group(3)) if match.group(3) else {
            1: "age_4m_test", 2: "age_4m_retest", 3: "age_8m", 4: "age_12m"
        }[session],
        "age_days_nominal": SESSION_AGE_DAYS[session],
        "source_h5_path": str(h5_path),
    }


def participant_metadata(handle: h5py.File) -> dict[str, Any]:
    """Read the source participant row exported with each H5."""
    raw = handle["participant/row_json"][()] if "participant/row_json" in handle else b"{}"
    try:
        return json.loads(decode(raw))
    except json.JSONDecodeError:
        return {}


def finite_median(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    return float(np.median(values)) if values.size else float("nan")


def bh_fdr(p_values: Iterable[float]) -> np.ndarray:
    """Benjamini-Hochberg adjusted p values, retaining NaN positions."""
    p = np.asarray(list(p_values), dtype=float)
    out = np.full(p.shape, np.nan)
    valid = np.isfinite(p)
    if not valid.any():
        return out
    values = p[valid]
    order = np.argsort(values)
    ranked = values[order] * len(values) / np.arange(1, len(values) + 1)
    adjusted = np.minimum.accumulate(ranked[::-1])[::-1]
    restored = np.empty_like(values)
    restored[order] = np.minimum(adjusted, 1.0)
    out[valid] = restored
    return out


def paired_summary(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    """Paired descriptive and Wilcoxon statistics for finite observations."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    valid = np.isfinite(a) & np.isfinite(b)
    a, b = a[valid], b[valid]
    difference = b - a
    result: dict[str, float] = {
        "n": int(len(difference)),
        "a_median": finite_median(a),
        "b_median": finite_median(b),
        "mean_difference_b_minus_a": float(np.mean(difference)) if len(difference) else np.nan,
        "median_difference_b_minus_a": finite_median(difference),
        "cohen_dz": float(np.mean(difference) / np.std(difference, ddof=1))
        if len(difference) > 1 and np.std(difference, ddof=1) > 0
        else np.nan,
    }
    if len(difference) >= 5 and not np.allclose(difference, 0):
        statistic, p_value = stats.wilcoxon(difference, zero_method="wilcox")
        result["wilcoxon_stat"] = float(statistic)
        result["p_raw"] = float(p_value)
    else:
        result["wilcoxon_stat"] = np.nan
        result["p_raw"] = np.nan
    return result


def icc_a1(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    """Two-way absolute-agreement, single-measure ICC(A,1)."""
    values = np.column_stack([a, b]).astype(float)
    values = values[np.isfinite(values).all(axis=1)]
    n, k = values.shape if values.ndim == 2 else (0, 0)
    if n < 3:
        return {"icc_a1": np.nan, "sem": np.nan, "mdc95": np.nan, "pearson_r": np.nan, "n": n}
    grand_mean = values.mean()
    ms_rows = k * np.sum((values.mean(axis=1) - grand_mean) ** 2) / (n - 1)
    ms_cols = n * np.sum((values.mean(axis=0) - grand_mean) ** 2) / (k - 1)
    residual = values - values.mean(axis=1, keepdims=True) - values.mean(axis=0) + grand_mean
    ms_error = np.sum(residual**2) / ((n - 1) * (k - 1))
    denominator = ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n
    icc = (ms_rows - ms_error) / denominator if denominator else np.nan
    pooled_sd = float(values.std(ddof=1))
    sem = pooled_sd * np.sqrt(max(0.0, 1.0 - icc)) if np.isfinite(icc) else np.nan
    pearson_r, pearson_p = stats.pearsonr(values[:, 0], values[:, 1])
    return {
        "icc_a1": float(icc),
        "sem": float(sem),
        "mdc95": float(1.96 * np.sqrt(2.0) * sem) if np.isfinite(sem) else np.nan,
        "pearson_r": float(pearson_r),
        "pearson_p": float(pearson_p),
        "n": int(n),
    }


def bootstrap_icc(a: np.ndarray, b: np.ndarray, n_boot: int = 2000, seed: int = 42) -> tuple[float, float]:
    """Subject-cluster bootstrap confidence interval for ICC(A,1)."""
    values = np.column_stack([a, b]).astype(float)
    values = values[np.isfinite(values).all(axis=1)]
    if len(values) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n_boot):
        sample = values[rng.integers(0, len(values), len(values))]
        value = icc_a1(sample[:, 0], sample[:, 1])["icc_a1"]
        if np.isfinite(value):
            draws.append(value)
    return (float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))) if draws else (np.nan, np.nan)
