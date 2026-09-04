"""Shared contract, metadata, and statistics for the Figshare infant EEG study."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import pandas as pd
import statsmodels.api as sm
from patsy import dmatrix
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.genmod.families import Gaussian

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

DEFAULT_DATA_ROOT = REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_figshare_infant_eeg_20260805_132612"
DEFAULT_RESULTS_ROOT = ARTICLE_DIR / "results" / "figshare_infant_cohort_20260805_132612"
COORDINATE_CONTRACT = "cohort_anchored"
SUBJECT_COORDINATE_CONTRACT = "subject_anchored"
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
SESSION_RE = re.compile(r"^(sub-\d+)_visit_(\d+)_mixed_rest_reaching\.h5$")


def decode(value: Any) -> str:
    return bytes(value).decode("utf-8") if isinstance(value, (bytes, bytearray, np.bytes_)) else str(value)


def h5_paths(data_root: Path) -> list[Path]:
    paths = sorted(data_root.rglob("*.h5"))
    if not paths:
        raise FileNotFoundError(f"No Figshare infant H5 files found under {data_root}")
    return paths


def participant_metadata(handle: h5py.File) -> dict[str, Any]:
    raw = handle["participant/row_json"][()] if "participant/row_json" in handle else b"{}"
    try:
        return json.loads(decode(raw))
    except json.JSONDecodeError:
        return {}


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def session_identity(h5_path: Path, participant: dict[str, Any]) -> dict[str, Any]:
    match = SESSION_RE.match(h5_path.name)
    if not match:
        raise ValueError(f"Unexpected Figshare infant H5 filename: {h5_path.name}")
    visit = int(match.group(2))
    age_days = _as_float(participant.get("age_days", participant.get("age_at_recording_days")))
    return {
        "subject_id": match.group(1),
        "visit": visit,
        "age_days": age_days,
        "days_from_first_session": _as_float(participant.get("days_from_first_session")),
        "age_source": participant.get("age_source", "unknown"),
        "session_id": participant.get("session_id", f"ses-{visit:02d}"),
        "original_bdf_id": participant.get("original_bdf_id"),
        "source_h5_path": str(h5_path),
    }


def finite_median(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    return float(np.median(values)) if values.size else np.nan


def bh_fdr(p_values: Iterable[float]) -> np.ndarray:
    p = np.asarray(list(p_values), dtype=float)
    adjusted = np.full(p.shape, np.nan)
    valid = np.isfinite(p)
    if not valid.any():
        return adjusted
    values = p[valid]
    order = np.argsort(values)
    ranked = values[order] * len(values) / np.arange(1, len(values) + 1)
    restored = np.empty_like(values)
    restored[order] = np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted[valid] = np.minimum(restored, 1.0)
    return adjusted


def fit_within_between(frame: pd.DataFrame, endpoint: str) -> dict:
    """Exploratory within/between-child age decomposition (peer_review/pr_01.md M3).

    Shared by the primary cohort-coordinate family (`03_cohort_coordinate_age.py`) and
    the conventional-EEG comparator family (`06_conventional_eeg_age.py`, peer_review/
    pr_02.md), since a cohort-level omnibus effect can in principle be driven entirely
    by between-child differences rather than a true within-child trajectory, for either
    family. Adds a linear between-child term (each child's own mean age) alongside a
    cubic spline of the centered (within-child) age, and tests each component
    separately. Reported as an exploratory robustness diagnostic, not a second
    FDR-corrected confirmatory family.

    Returns a `not_testable_reason` (both Wald statistics/p-values NaN) if there are
    too few sessions/children with within-child age variation to identify the
    within-child spline term, rather than letting the GEE fit raise.
    """
    data = frame[["subject_id", "age_days", endpoint]].dropna().rename(columns={endpoint: "outcome"})
    n_children_with_variation = int((data.groupby("subject_id").age_days.nunique() > 1).sum()) if len(data) else 0
    if len(data) < MIN_SESSIONS_FOR_SPLINE_GEE or n_children_with_variation < 3:
        return {
            "endpoint": endpoint,
            "n_sessions": len(data),
            "n_children": int(data.subject_id.nunique()) if len(data) else 0,
            "n_children_with_within_child_age_variation": n_children_with_variation,
            "between_child_coef": np.nan,
            "between_wald_chi2": np.nan,
            "between_wald_df": 1,
            "between_p_raw": np.nan,
            "within_wald_chi2": np.nan,
            "within_wald_df": 3,
            "within_p_raw": np.nan,
            "not_testable_reason": f"too_few_sessions_or_within_child_variation_n_children_varying={n_children_with_variation}",
        }
    data["age_between"] = data.groupby("subject_id").age_days.transform("mean")
    data["age_within"] = data.age_days - data.age_between
    try:
        spline = dmatrix("0 + bs(age_within, df=3, degree=3, include_intercept=False)", data, return_type="dataframe")
        design = pd.concat(
            [
                pd.Series(1.0, index=data.index, name="intercept"),
                data[["age_between"]].reset_index(drop=True).set_axis(data.index),
                spline.set_axis(["within_spline_1", "within_spline_2", "within_spline_3"], axis=1),
            ],
            axis=1,
        )
        model = sm.GEE(data.outcome, design, groups=data.subject_id, family=Gaussian(), cov_struct=Exchangeable())
        result = model.fit()
        within_restriction = np.zeros((3, 5))
        within_restriction[0, 2] = within_restriction[1, 3] = within_restriction[2, 4] = 1.0
        within_test = result.wald_test(within_restriction, scalar=True)
        between_restriction = np.zeros((1, 5))
        between_restriction[0, 1] = 1.0
        between_test = result.wald_test(between_restriction, scalar=True)
    except Exception as error:  # noqa: BLE001 - reported as not-testable, not a crashed pipeline
        return {
            "endpoint": endpoint,
            "n_sessions": len(data),
            "n_children": int(data.subject_id.nunique()),
            "n_children_with_within_child_age_variation": n_children_with_variation,
            "between_child_coef": np.nan,
            "between_wald_chi2": np.nan,
            "between_wald_df": 1,
            "between_p_raw": np.nan,
            "within_wald_chi2": np.nan,
            "within_wald_df": 3,
            "within_p_raw": np.nan,
            "not_testable_reason": f"gee_fit_failed:{type(error).__name__}:{error}",
        }
    return {
        "endpoint": endpoint,
        "n_sessions": len(data),
        "n_children": data.subject_id.nunique(),
        "n_children_with_within_child_age_variation": n_children_with_variation,
        "between_child_coef": float(result.params["age_between"]),
        "between_wald_chi2": float(between_test.statistic),
        "between_wald_df": 1,
        "between_p_raw": float(between_test.pvalue),
        "within_wald_chi2": float(within_test.statistic),
        "within_wald_df": 3,
        "within_p_raw": float(within_test.pvalue),
        "not_testable_reason": None,
    }


def fit_within_between_family(metrics: pd.DataFrame, endpoints: Iterable[str]) -> pd.DataFrame:
    return pd.DataFrame([fit_within_between(metrics, endpoint) for endpoint in endpoints])


def cluster_permutation_p(frame: pd.DataFrame, endpoint: str, observed_chi2: float, n_permutation: int, rng: np.random.Generator) -> float:
    """Cluster-permutation robustness check on the GEE omnibus Wald statistic (peer_review/pr_01.md M4).

    Shared by the primary cohort-coordinate family and the conventional-EEG comparator
    family. See `fit_within_between` for why this and the within/between decomposition
    matter for any new cohort-level GEE family, not only the original 12-endpoint one.
    """
    if not np.isfinite(observed_chi2):
        return np.nan
    data = frame[["subject_id", "age_days", endpoint]].dropna().rename(columns={endpoint: "outcome"}).reset_index(drop=True)
    age_values = data.age_days.to_numpy()
    hits = 0
    valid_draws = 0
    for _ in range(n_permutation):
        permuted = data.copy()
        permuted["age_days"] = rng.permutation(age_values)
        try:
            spline = dmatrix("0 + bs(age_days, df=3, degree=3, include_intercept=False)", permuted, return_type="dataframe")
            design = pd.concat([pd.Series(1.0, index=permuted.index, name="intercept"), spline.set_axis(["spline_1", "spline_2", "spline_3"], axis=1)], axis=1)
            model = sm.GEE(permuted.outcome, design, groups=permuted.subject_id, family=Gaussian(), cov_struct=Exchangeable())
            result = model.fit()
            restriction = np.column_stack([np.zeros(3), np.eye(3)])
            test = result.wald_test(restriction, scalar=True)
            statistic = float(test.statistic)
        except Exception:
            continue
        if not np.isfinite(statistic):
            continue
        valid_draws += 1
        if statistic >= observed_chi2:
            hits += 1
    return float((hits + 1) / (valid_draws + 1)) if valid_draws else np.nan


def within_child_frame(metrics: pd.DataFrame, endpoint: str, direct_age_only: bool = False) -> pd.DataFrame:
    """Child-demeaned age/endpoint frame used by every within-child age-association test.

    Shared by the subject-level within-child MNJ/reachability analysis and the
    cohort-pooled reachability analysis so both use an identical estimator.
    """
    columns = ["subject_id", "age_days", endpoint] + (["age_source"] if "age_source" in metrics else [])
    frame = metrics[columns].copy()
    if direct_age_only and "age_source" in frame:
        frame = frame[frame.age_source.astype(str).str.lower().str.contains("direct", na=False)]
    frame = frame.dropna(subset=["subject_id", "age_days", endpoint])
    frame = frame.groupby("subject_id").filter(lambda group: len(group) >= 2 and group.age_days.nunique() >= 2)
    if frame.empty:
        return frame
    frame["age_centered"] = frame.age_days - frame.groupby("subject_id").age_days.transform("mean")
    frame["value_centered"] = frame[endpoint] - frame.groupby("subject_id")[endpoint].transform("mean")
    return frame


def within_child_slope(frame: pd.DataFrame) -> float:
    denominator = float(np.sum(frame.age_centered.to_numpy() ** 2))
    return float(np.sum(frame.age_centered.to_numpy() * frame.value_centered.to_numpy()) / denominator) if denominator else np.nan


def within_child_bootstrap_ci(frame: pd.DataFrame, n_bootstrap: int, rng: np.random.Generator) -> tuple[float, float]:
    children = frame.subject_id.unique()
    if len(children) < 3:
        return np.nan, np.nan
    numerator = frame.assign(product=frame.age_centered * frame.value_centered).groupby("subject_id").product.sum().reindex(children).to_numpy()
    denominator = frame.assign(square=frame.age_centered**2).groupby("subject_id").square.sum().reindex(children).to_numpy()
    draws_index = rng.integers(0, len(children), size=(n_bootstrap, len(children)))
    draws = numerator[draws_index].sum(axis=1) / denominator[draws_index].sum(axis=1)
    return tuple(np.percentile(draws[np.isfinite(draws)], [2.5, 97.5])) if np.isfinite(draws).any() else (np.nan, np.nan)


def within_child_sign_permutation_p(frame: pd.DataFrame, observed: float, n_permutation: int, rng: np.random.Generator) -> float:
    children = frame.subject_id.unique()
    if not len(children) or not np.isfinite(observed):
        return np.nan
    numerator = frame.assign(product=frame.age_centered * frame.value_centered).groupby("subject_id").product.sum().reindex(children).to_numpy()
    denominator = float(np.sum(frame.age_centered.to_numpy() ** 2))
    draws = (rng.choice((-1.0, 1.0), size=(n_permutation, len(children))) * numerator).sum(axis=1) / denominator
    return float((np.sum(np.abs(draws) >= abs(observed)) + 1) / (len(draws) + 1))


def conventional_eeg_medians(handle: h5py.File) -> dict[str, float]:
    """Per-session median of every `eeg_conventional_*` comparator column, if present.

    Tries the per-epoch raw feature-table layout first (`features_raw/names` +
    `features_raw/values`, the layout already used by the sibling APPLESEED_infants
    article's `appleseed_support.py`); this lets every present `eeg_conventional_*`
    column be discovered generically rather than hardcoding a fixed endpoint list,
    since the exact set of enabled comparator packs (tier1/complexity/connectivity)
    is a config-level, not code-level, choice (agent/CONFIG_GUIDE_20260701.md).

    Falls back to the pre-aggregated H5-extension layout
    (`extensions/conventional_eeg/families/<family>/<comparator>/median`, the
    MNDM 2.3 `conventional_eeg` extension schema documented in
    agent/Output_variables_guide.md) if the raw per-epoch layout is absent, in
    which case only the median statistic already computed upstream is used
    (no per-epoch data is available to re-derive it from in that layout).
    """
    output: dict[str, float] = {}
    if "features_raw/names" in handle and "features_raw/values" in handle:
        names = [decode(item) for item in handle["features_raw/names"][:]]
        values = np.asarray(handle["features_raw/values"][:], dtype=float)
        for index, name in enumerate(names):
            if name.startswith("eeg_conventional_"):
                output[name] = finite_median(values[:, index])
        return output
    families_group = handle.get("extensions/conventional_eeg/families")
    if families_group is not None:
        for family_name, family_group in families_group.items():
            if not isinstance(family_group, h5py.Group):
                continue
            for comparator_name, comparator_group in family_group.items():
                if not isinstance(comparator_group, h5py.Group) or "median" not in comparator_group:
                    continue
                name = f"eeg_conventional_{decode(family_name)}_{decode(comparator_name)}"
                value = np.asarray(comparator_group["median"][()]).reshape(-1)
                output[name] = float(value[0]) if value.size else np.nan
    return output


MIN_SESSIONS_FOR_SPLINE_GEE = 10
MIN_DISTINCT_AGES_FOR_SPLINE_GEE = 4  # cubic B-spline, df=3, needs at least df+1 distinct knot-eligible ages
_EMPTY_PREDICTION_COLUMNS = ("endpoint", "age_days", "predicted_mean", "ci95_low", "ci95_high")


def _not_testable_row(endpoint: str, data: pd.DataFrame, reason: str) -> tuple[dict, pd.DataFrame]:
    row = {
        "endpoint": endpoint,
        "n_sessions": int(len(data)),
        "n_children": int(data.subject_id.nunique()) if len(data) else 0,
        "wald_chi2": np.nan,
        "wald_df": 3,
        "p_raw": np.nan,
        "intercept": np.nan,
        "spline_1": np.nan,
        "spline_2": np.nan,
        "spline_3": np.nan,
        "not_testable_reason": reason,
    }
    return row, pd.DataFrame(columns=_EMPTY_PREDICTION_COLUMNS)


def fit_spline_gee(frame: pd.DataFrame, endpoint: str) -> tuple[dict, pd.DataFrame]:
    """Child-clustered Gaussian GEE with a 3-df cubic age spline for one endpoint.

    Shared by the primary cohort-coordinate family (`03_cohort_coordinate_age.py`)
    and the conventional-EEG comparator family (`06_conventional_eeg_age.py`) so
    both use an identical cohort-level age model.

    Guards against endpoints that are entirely or near-entirely missing/constant
    (e.g. a connectivity comparator for a channel pair absent in this montage) by
    returning a "not testable" row instead of letting patsy/statsmodels raise on
    an empty or degenerate design matrix. This matters specifically for
    `conventional_eeg` comparator families (06), where per-endpoint coverage is
    not guaranteed the way it is for the pipeline-internal MNPS/MNJ endpoints.
    """
    data = frame[["subject_id", "age_days", endpoint]].dropna().rename(columns={endpoint: "outcome"})
    if len(data) < MIN_SESSIONS_FOR_SPLINE_GEE:
        return _not_testable_row(endpoint, data, f"too_few_sessions_after_dropna_n={len(data)}")
    if data.age_days.nunique() < MIN_DISTINCT_AGES_FOR_SPLINE_GEE:
        return _not_testable_row(endpoint, data, f"too_few_distinct_ages_n={data.age_days.nunique()}")
    outcome_std = float(data.outcome.std(ddof=0))
    if not np.isfinite(outcome_std) or outcome_std == 0.0:
        return _not_testable_row(endpoint, data, "zero_or_non_finite_outcome_variance")
    try:
        spline = dmatrix("0 + bs(age_days, df=3, degree=3, include_intercept=False)", data, return_type="dataframe")
        design = pd.concat([pd.Series(1.0, index=data.index, name="intercept"), spline.set_axis(["spline_1", "spline_2", "spline_3"], axis=1)], axis=1)
        model = sm.GEE(data.outcome, design, groups=data.subject_id, family=Gaussian(), cov_struct=Exchangeable())
        result = model.fit()
        restriction = np.column_stack([np.zeros(3), np.eye(3)])
        test = result.wald_test(restriction, scalar=True)
        grid = pd.DataFrame({"age_days": np.linspace(data.age_days.min(), data.age_days.max(), 100)})
        grid_spline = dmatrix("0 + bs(age_days, df=3, degree=3, include_intercept=False)", grid, return_type="dataframe")
        grid_design = pd.concat([pd.Series(1.0, index=grid.index, name="intercept"), grid_spline.set_axis(["spline_1", "spline_2", "spline_3"], axis=1)], axis=1)
        prediction = result.get_prediction(grid_design).summary_frame()
    except Exception as error:  # noqa: BLE001 - deliberately broad: any fit/design failure becomes a reported "not testable" endpoint, not a crashed pipeline
        return _not_testable_row(endpoint, data, f"gee_fit_failed:{type(error).__name__}:{error}")
    predictions = pd.DataFrame({"endpoint": endpoint, "age_days": grid.age_days, "predicted_mean": prediction["mean"], "ci95_low": prediction["mean_ci_lower"], "ci95_high": prediction["mean_ci_upper"]})
    row = {
        "endpoint": endpoint,
        "n_sessions": len(data),
        "n_children": data.subject_id.nunique(),
        "wald_chi2": float(test.statistic),
        "wald_df": 3,
        "p_raw": float(test.pvalue),
        "intercept": float(result.params["intercept"]),
        "spline_1": float(result.params["spline_1"]),
        "spline_2": float(result.params["spline_2"]),
        "spline_3": float(result.params["spline_3"]),
        "not_testable_reason": None,
    }
    return row, predictions


def fit_spline_gee_family(metrics: pd.DataFrame, endpoints: Iterable[str], label: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, predictions = [], []
    for endpoint in endpoints:
        row, prediction = fit_spline_gee(metrics, endpoint)
        row["analysis_layer"] = label
        rows.append(row)
        predictions.append(prediction.assign(analysis_layer=label))
    results = pd.DataFrame(rows)
    results["p_fdr"] = bh_fdr(results.p_raw)
    return results, pd.concat(predictions, ignore_index=True)


def within_child_age_associations(
    metrics: pd.DataFrame,
    endpoints: tuple[str, ...],
    label: str,
    n_bootstrap: int,
    n_permutation: int,
    seed: int,
    direct_age_only: bool = False,
) -> pd.DataFrame:
    """Child-clustered within-unit age-association test (demeaned slope, cluster bootstrap CI, sign-permutation p, BH-FDR sensitivity).

    This is the single shared estimator used by both the subject/visit-level within-child
    MNJ/reachability family and the cohort-pooled reachability family, so the two are
    directly comparable.
    """
    rows = []
    for number, endpoint in enumerate(endpoints):
        frame = within_child_frame(metrics, endpoint, direct_age_only)
        slope = within_child_slope(frame) if not frame.empty else np.nan
        ci_low, ci_high = within_child_bootstrap_ci(frame, n_bootstrap, np.random.default_rng(seed + number)) if not frame.empty else (np.nan, np.nan)
        p_value = within_child_sign_permutation_p(frame, slope, n_permutation, np.random.default_rng(seed + 10_000 + number)) if not frame.empty else np.nan
        scale = float(frame.value_centered.std(ddof=1) / frame.age_centered.std(ddof=1)) if len(frame) > 2 and frame.age_centered.std(ddof=1) else np.nan
        rows.append({
            "analysis_layer": label,
            "endpoint": endpoint,
            "n_sessions": int(len(frame)),
            "n_children": int(frame.subject_id.nunique()) if not frame.empty else 0,
            "age_days_min": float(frame.age_days.min()) if not frame.empty else np.nan,
            "age_days_max": float(frame.age_days.max()) if not frame.empty else np.nan,
            "within_child_slope_per_day": slope,
            "within_child_slope_per_30_days": slope * 30 if np.isfinite(slope) else np.nan,
            "standardized_within_slope": slope / scale if np.isfinite(slope) and np.isfinite(scale) and scale else np.nan,
            "bootstrap_ci95_low": ci_low,
            "bootstrap_ci95_high": ci_high,
            "sign_permutation_p_raw": p_value,
        })
    output = pd.DataFrame(rows)
    output["p_fdr_sensitivity"] = bh_fdr(output.sign_permutation_p_raw)
    return output
