"""Dementia resting/photic follow-up analyses.

The module deliberately uses the frozen local-dynamics H5 contract.  It
provides a diagnosis/MMSE eligibility audit and a subject-respecting
diagnosis-by-frequency interaction model for the photic export.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import pandas as pd
from scipy import stats


GROUP_LABELS = {"A": "AD", "C": "Healthy", "F": "FTD"}
PHOTIC_FREQUENCIES = (5, 10, 15, 20)
PRIMARY_PHOTIC_METRICS = ("mean_log_g_max", "mean_d_resp", "mean_c_1")
SECONDARY_PHOTIC_METRICS = (
    "mean_spectral_abscissa",
    "mean_numerical_abscissa",
    "mean_reactivity_gap",
    "stable_reactive_fraction",
)


def _decode(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, np.generic):
        return value.item()
    return value


def _scalar(group: h5py.Group, name: str, default: Any = np.nan) -> Any:
    if name not in group:
        return default
    value = group[name][()]
    return _decode(value)


def _finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def _participant_attrs(handle: h5py.File) -> dict[str, Any]:
    participant = handle.get("/participant")
    if not isinstance(participant, h5py.Group):
        return {}
    return {str(key): _decode(value) for key, value in participant.attrs.items()}


def load_dementia_metadata(raw_root: str | Path) -> pd.DataFrame:
    """Read diagnosis, MMSE, and photic frequency metadata from H5 attrs."""

    rows: list[dict[str, Any]] = []
    for path in sorted(Path(raw_root).rglob("*.h5")):
        with h5py.File(path, "r") as handle:
            attrs = _participant_attrs(handle)
            mmse = next(
                (
                    value
                    for key, value in attrs.items()
                    if "mmse" in key.lower()
                ),
                np.nan,
            )
            frequencies = (
                np.asarray(handle["/blocks/frequency_hz"][:], dtype=float)
                if "/blocks/frequency_hz" in handle
                else np.asarray([], dtype=float)
            )
            rows.append(
                {
                    "subject_id": str(_decode(handle.attrs.get("subject_id"))),
                    "group_code": str(_decode(handle.attrs.get("group"))),
                    "group": GROUP_LABELS.get(
                        str(_decode(handle.attrs.get("group"))),
                        str(_decode(handle.attrs.get("group"))),
                    ),
                    "MMSE": float(mmse) if _finite(mmse) else np.nan,
                    "n_block_frequencies": int(np.unique(frequencies).size),
                    "block_frequencies": ",".join(
                        str(int(value)) for value in sorted(set(frequencies.tolist()))
                    ),
                    "source_h5": str(path),
                }
            )
    return pd.DataFrame(rows).sort_values("subject_id").reset_index(drop=True)


def _availability_row(handle: h5py.File, *, dimension: int) -> dict[str, Any]:
    suffix = "" if dimension == 3 else "_9D"
    jacobian_path = f"/jacobian{suffix}/derived_metrics/v1"
    ftr_path = f"/finite_time_response/v1/{'primary' if dimension == 3 else 'stratified_9d'}"
    residual_path = f"/transition_residuals/v1/{'primary' if dimension == 3 else 'stratified_9d'}"
    q_path = f"/transition_residual_covariance_proxy/v1/{'primary' if dimension == 3 else 'stratified_9d'}"
    ftr_horizon = f"{ftr_path}/horizons/h4"

    jacobian_summary = f"{jacobian_path}/summary"
    jacobian_valid = (
        jacobian_path in handle
        and jacobian_summary in handle
        and _finite(_scalar(handle[jacobian_summary], "n_windows_metrics_valid"))
        and float(_scalar(handle[jacobian_summary], "n_windows_metrics_valid")) > 0
    )
    ftr_valid = (
        ftr_horizon in handle
        and _finite(_scalar(handle[ftr_horizon], "n_sequences_valid"))
        and float(_scalar(handle[ftr_horizon], "n_sequences_valid")) > 0
    )
    residual_status = _decode(_scalar(handle[residual_path], "computation_status", "")) if residual_path in handle else ""
    q_status = _decode(_scalar(handle[q_path], "computation_status", "")) if q_path in handle else ""
    return {
        "dimension": dimension,
        "jacobian_capability": jacobian_path in handle,
        "jacobian_valid": bool(jacobian_valid),
        "jacobian_n_windows_valid": _scalar(
            handle[jacobian_summary], "n_windows_metrics_valid"
        )
        if jacobian_summary in handle
        else np.nan,
        "ftr_capability": ftr_path in handle,
        "ftr_valid": bool(ftr_valid),
        "ftr_n_sequences_valid": _scalar(handle[ftr_horizon], "n_sequences_valid")
        if ftr_horizon in handle
        else np.nan,
        "residual_capability": residual_path in handle,
        "residual_computed": str(residual_status) == "computed",
        "q_proxy_capability": q_path in handle,
        "q_proxy_computed": str(q_status) == "computed",
    }


def _summarize_d0_audit(audit: pd.DataFrame) -> pd.DataFrame:
    summary_rows: list[dict[str, Any]] = []
    for (dataset, dimension, group), frame in audit.groupby(
        ["dataset", "dimension", "group"], dropna=False
    ):
        row: dict[str, Any] = {
            "dataset": dataset,
            "dimension": int(dimension),
            "group": group,
            "n_subjects": int(frame["subject_id"].nunique()),
            "mmse_n": int(frame["MMSE"].notna().sum()),
            "mmse_mean": float(frame["MMSE"].mean()),
            "block_frequency_mean": float(frame["n_block_frequencies"].mean()),
        }
        for field in (
            "jacobian_capability",
            "jacobian_valid",
            "ftr_capability",
            "ftr_valid",
            "residual_computed",
            "q_proxy_computed",
        ):
            row[f"{field}_rate"] = float(frame[field].mean())
        for field in ("jacobian_n_windows_valid", "ftr_n_sequences_valid"):
            values = pd.to_numeric(frame[field], errors="coerce").dropna()
            row[f"{field}_median"] = float(values.median()) if not values.empty else np.nan
        summary_rows.append(row)

    for eligibility in ("jacobian_valid", "ftr_valid"):
        frame = audit[audit["dimension"] == 9].copy()
        frame = frame[np.isfinite(pd.to_numeric(frame["MMSE"], errors="coerce"))]
        if frame.empty:
            continue
        eligible = frame[eligibility].astype(float)
        if eligible.nunique() > 1:
            rho, rho_p = stats.spearmanr(frame["MMSE"], eligible)
        else:
            rho, rho_p = np.nan, np.nan
        summary_rows.append(
            {
                "dataset": frame["dataset"].iloc[0],
                "dimension": 9,
                "group": "__MMSE_selection__",
                "eligibility": eligibility,
                "n_subjects": int(len(frame)),
                "eligible_n": int(eligible.sum()),
                "eligible_mmse_mean": float(frame.loc[eligible.astype(bool), "MMSE"].mean()),
                "excluded_mmse_mean": float(frame.loc[~eligible.astype(bool), "MMSE"].mean()),
                "spearman_rho": float(rho),
                "spearman_p": float(rho_p),
            }
        )
    return pd.DataFrame(summary_rows)


def build_d0_audit(raw_root: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Audit diagnosis/MMSE/frequency-dependent eligibility before contrasts."""

    metadata = load_dementia_metadata(raw_root)
    rows: list[dict[str, Any]] = []
    for source in metadata["source_h5"]:
        with h5py.File(source, "r") as handle:
            base = metadata.loc[metadata["source_h5"] == source].iloc[0].to_dict()
            for dimension in (3, 9):
                row = dict(base)
                row.update(_availability_row(handle, dimension=dimension))
                row["dataset"] = Path(raw_root).name
                rows.append(row)
    audit = pd.DataFrame(rows)

    return audit, _summarize_d0_audit(audit)


def _frequency_from_labels(handle: h5py.File, indices: np.ndarray) -> np.ndarray:
    labels = {}
    for frequency in PHOTIC_FREQUENCIES:
        path = f"/labels/photo_{frequency}hz"
        if path in handle:
            labels[frequency] = np.asarray(handle[path][:], dtype=int)
    result = np.full(indices.shape, np.nan, dtype=float)
    for frequency, values in labels.items():
        valid = (indices >= 0) & (indices < values.size) & (values[indices] > 0)
        result[valid] = float(frequency)
    return result


def _metric_rows_for_h5(
    handle: h5py.File,
    *,
    dimension: int,
    metric_names: Iterable[str],
    horizon_steps: int = 4,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    suffix = "" if dimension == 3 else "_9D"
    jacobian_base = f"/jacobian{suffix}/derived_metrics/v1"
    jacobian_series = f"{jacobian_base}/series"
    if jacobian_series in handle and f"/jacobian{suffix}/centers" in handle:
        centers = np.asarray(handle[f"/jacobian{suffix}/centers"][:], dtype=int)
        frequencies = _frequency_from_labels(handle, centers)
        for metric_name in metric_names:
            source_name = metric_name.removeprefix("mean_")
            if source_name == "stable_reactive_fraction":
                source_name = "stable_reactive_flag"
            if source_name not in handle[jacobian_series]:
                continue
            values = np.asarray(handle[f"{jacobian_series}/{source_name}"][:], dtype=float)
            for index, value in enumerate(values):
                frequency = frequencies[index] if index < frequencies.size else np.nan
                if not np.isfinite(value) or not np.isfinite(frequency):
                    continue
                rows.append(
                    {
                        "dimension": dimension,
                        "family": "jacobian",
                        "metric": metric_name,
                        "frequency_hz": int(frequency),
                        "value": float(value),
                        "support_unit": "window",
                    }
                )

    ftr_base = f"/finite_time_response/v1/{'primary' if dimension == 3 else 'stratified_9d'}"
    horizon = f"{ftr_base}/horizons/h{horizon_steps}"
    series = f"{horizon}/series"
    if series in handle and f"{horizon}/start_windows" in handle:
        starts = np.asarray(handle[f"{horizon}/start_windows"][:], dtype=int)
        frequencies = _frequency_from_labels(handle, starts)
        for metric_name in metric_names:
            source_name = metric_name.removeprefix("mean_")
            if source_name not in handle[series]:
                continue
            values = np.asarray(handle[f"{series}/{source_name}"][:], dtype=float)
            for index, value in enumerate(values):
                frequency = frequencies[index] if index < frequencies.size else np.nan
                if not np.isfinite(value) or not np.isfinite(frequency):
                    continue
                rows.append(
                    {
                        "dimension": dimension,
                        "family": "ftr",
                        "metric": metric_name,
                        "frequency_hz": int(frequency),
                        "value": float(value),
                        "support_unit": "sequence",
                    }
                )
    residual_base = (
        f"/transition_residuals/v1/"
        f"{'primary' if dimension == 3 else 'stratified_9d'}"
    )
    residual_series = f"{residual_base}/series"
    if residual_series in handle and f"{residual_series}/source_window_id" in handle:
        source_windows = np.asarray(
            handle[f"{residual_series}/source_window_id"][:], dtype=int
        )
        residuals = np.asarray(
            handle[f"{residual_series}/transition_residual"][:], dtype=float
        )
        frequencies = _frequency_from_labels(handle, source_windows)
        for index, residual in enumerate(residuals):
            frequency = frequencies[index] if index < frequencies.size else np.nan
            value = float(np.linalg.norm(residual))
            if not np.isfinite(value) or not np.isfinite(frequency):
                continue
            rows.append(
                {
                    "dimension": dimension,
                    "family": "transition_qc",
                    "metric": "transition_residual_mean_norm",
                    "frequency_hz": int(frequency),
                    "value": value,
                    "support_unit": "transition",
                }
            )
    return rows


def _aggregate_subject_frequency(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return raw
    return (
        raw.groupby(
            [
                "subject_id",
                "group",
                "group_code",
                "MMSE",
                "dimension",
                "family",
                "metric",
                "frequency_hz",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(value=("value", "mean"), n_support=("value", "size"))
    )


def _collect_photic_followup_frames(
    raw_root: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read each photic H5 once for metadata, D0, and subject×frequency rows."""

    metadata_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    dataset = Path(raw_root).name
    for path in sorted(Path(raw_root).rglob("*.h5")):
        with h5py.File(path, "r") as handle:
            attrs = _participant_attrs(handle)
            group_code = str(_decode(handle.attrs.get("group")))
            mmse = next(
                (value for key, value in attrs.items() if "mmse" in key.lower()),
                np.nan,
            )
            frequencies = (
                np.asarray(handle["/blocks/frequency_hz"][:], dtype=float)
                if "/blocks/frequency_hz" in handle
                else np.asarray([], dtype=float)
            )
            base = {
                "subject_id": str(_decode(handle.attrs.get("subject_id"))),
                "group_code": group_code,
                "group": GROUP_LABELS.get(group_code, group_code),
                "MMSE": float(mmse) if _finite(mmse) else np.nan,
                "n_block_frequencies": int(np.unique(frequencies).size),
                "block_frequencies": ",".join(
                    str(int(value)) for value in sorted(set(frequencies.tolist()))
                ),
                "source_h5": str(path),
            }
            metadata_rows.append(base)
            for dimension in (3, 9):
                availability = _availability_row(handle, dimension=dimension)
                audit_row = dict(base)
                audit_row.update(availability)
                audit_row["dataset"] = dataset
                audit_rows.append(audit_row)
                for metric_row in _metric_rows_for_h5(
                    handle,
                    dimension=dimension,
                    metric_names=PRIMARY_PHOTIC_METRICS + SECONDARY_PHOTIC_METRICS,
                ):
                    metric_row.update(
                        {
                            "subject_id": base["subject_id"],
                            "group": base["group"],
                            "group_code": group_code,
                            "MMSE": base["MMSE"],
                            "source_h5": str(path),
                        }
                    )
                    metric_rows.append(metric_row)
    return (
        pd.DataFrame(metadata_rows).sort_values("subject_id").reset_index(drop=True),
        pd.DataFrame(audit_rows),
        _aggregate_subject_frequency(pd.DataFrame(metric_rows)),
    )


def build_photic_subject_frequency_table(
    raw_root: str | Path,
    *,
    horizon_steps: int = 4,
) -> pd.DataFrame:
    """Extract finite local-dynamics metrics at subject × photic frequency."""

    rows: list[dict[str, Any]] = []
    for path in sorted(Path(raw_root).rglob("*.h5")):
        with h5py.File(path, "r") as handle:
            subject_id = str(_decode(handle.attrs.get("subject_id")))
            group_code = str(_decode(handle.attrs.get("group")))
            group = GROUP_LABELS.get(group_code, group_code)
            metadata = _participant_attrs(handle)
            mmse = next(
                (value for key, value in metadata.items() if "mmse" in key.lower()),
                np.nan,
            )
            metric_rows: list[dict[str, Any]] = []
            for dimension in (3, 9):
                metric_rows.extend(
                    _metric_rows_for_h5(
                        handle,
                        dimension=dimension,
                        metric_names=(
                            PRIMARY_PHOTIC_METRICS
                            if dimension in (3, 9)
                            else ()
                        )
                        + (
                            SECONDARY_PHOTIC_METRICS
                            if dimension in (3, 9)
                            else ()
                        ),
                        horizon_steps=horizon_steps,
                    )
                )
            for metric_row in metric_rows:
                metric_row.update(
                    {
                        "subject_id": subject_id,
                        "group": group,
                        "group_code": group_code,
                        "MMSE": float(mmse) if _finite(mmse) else np.nan,
                        "source_h5": str(path),
                    }
                )
                rows.append(metric_row)

    return _aggregate_subject_frequency(pd.DataFrame(rows))


def _interaction_f_statistic(frame: pd.DataFrame) -> float:
    subjects = sorted(frame["subject_id"].unique())
    frequencies = sorted(frame["frequency_hz"].unique())
    if len(subjects) < 3 or len(frequencies) < 2:
        return np.nan
    subject_index = {subject: index for index, subject in enumerate(subjects)}
    frequency_index = {frequency: index for index, frequency in enumerate(frequencies)}
    group_values = frame.drop_duplicates("subject_id").set_index("subject_id")["group"]
    groups = sorted(group_values.unique())
    reference_group = "Healthy" if "Healthy" in groups else groups[0]
    nonreference_groups = [group for group in groups if group != reference_group]
    frequency_reference = frequencies[0]
    nonreference_frequencies = frequencies[1:]

    rows: list[list[float]] = []
    y: list[float] = []
    for item in frame.itertuples(index=False):
        subject_dummy = [
            1.0 if subject_index[item.subject_id] == index else 0.0
            for index in range(1, len(subjects))
        ]
        frequency_dummy = [
            1.0 if item.frequency_hz == frequency else 0.0
            for frequency in nonreference_frequencies
        ]
        interaction = [
            float(item.group == group and item.frequency_hz == frequency)
            for group in nonreference_groups
            for frequency in nonreference_frequencies
        ]
        rows.append(subject_dummy + frequency_dummy + interaction)
        y.append(float(item.value))
    design = np.asarray(rows, dtype=float)
    outcome = np.asarray(y, dtype=float)
    reduced = design[:, : (len(subjects) - 1 + len(nonreference_frequencies))]
    full_rank = np.linalg.matrix_rank(design)
    reduced_rank = np.linalg.matrix_rank(reduced)
    if full_rank >= len(outcome) or full_rank <= reduced_rank:
        return np.nan
    rss_reduced = float(np.sum((outcome - reduced @ np.linalg.lstsq(reduced, outcome, rcond=None)[0]) ** 2))
    rss_full = float(np.sum((outcome - design @ np.linalg.lstsq(design, outcome, rcond=None)[0]) ** 2))
    numerator_df = full_rank - reduced_rank
    denominator_df = len(outcome) - full_rank
    if rss_full <= 0 or denominator_df <= 0:
        return np.nan
    return ((rss_reduced - rss_full) / numerator_df) / (rss_full / denominator_df)


def _fast_interaction_test(
    frame: pd.DataFrame,
    *,
    n_permutations: int,
    rng: np.random.Generator,
) -> tuple[float, np.ndarray, int, int]:
    """Evaluate the repeated-measures interaction with cached fixed effects."""

    work = frame.sort_values(["subject_id", "frequency_hz"]).reset_index(drop=True)
    subjects = sorted(work["subject_id"].unique())
    frequencies = sorted(work["frequency_hz"].unique())
    subject_index = {subject: index for index, subject in enumerate(subjects)}
    subject_rows = work["subject_id"].map(subject_index).to_numpy(dtype=int)
    frequency_rows = work["frequency_hz"].map(
        {frequency: index for index, frequency in enumerate(frequencies)}
    ).to_numpy(dtype=int)
    groups_by_subject = (
        work.drop_duplicates("subject_id")
        .set_index("subject_id")
        .loc[subjects, "group"]
        .to_numpy()
    )
    group_levels = sorted(set(groups_by_subject.tolist()))
    reference_group = "Healthy" if "Healthy" in group_levels else group_levels[0]
    nonreference_groups = [group for group in group_levels if group != reference_group]
    nonreference_frequencies = frequencies[1:]

    base_columns = []
    for subject in range(1, len(subjects)):
        base_columns.append((subject_rows == subject).astype(float))
    for frequency in range(1, len(frequencies)):
        base_columns.append((frequency_rows == frequency).astype(float))
    base = np.column_stack(base_columns)
    base_rank = int(np.linalg.matrix_rank(base))
    base_pinv = np.linalg.pinv(base)
    outcome = work["value"].to_numpy(dtype=float)
    outcome_residual = outcome - base @ (base_pinv @ outcome)
    rss_reduced = float(np.dot(outcome_residual, outcome_residual))

    def statistic(subject_groups: np.ndarray) -> float:
        row_groups = subject_groups[subject_rows]
        interaction_columns = [
            (
                (row_groups == group)
                & (frequency_rows == frequency_index)
            ).astype(float)
            for group in nonreference_groups
            for frequency_index in range(1, len(frequencies))
        ]
        interaction = np.column_stack(interaction_columns)
        interaction_residual = interaction - base @ (base_pinv @ interaction)
        interaction_rank = int(np.linalg.matrix_rank(interaction_residual))
        residual_df = len(outcome) - base_rank - interaction_rank
        if interaction_rank <= 0 or residual_df <= 0:
            return np.nan
        coefficients = np.linalg.lstsq(
            interaction_residual,
            outcome_residual,
            rcond=None,
        )[0]
        residual = outcome_residual - interaction_residual @ coefficients
        rss_full = float(np.dot(residual, residual))
        if rss_full <= 0:
            return np.nan
        return ((rss_reduced - rss_full) / interaction_rank) / (
            rss_full / residual_df
        )

    observed = statistic(groups_by_subject)
    permutation_values = np.asarray(
        [
            statistic(rng.permutation(groups_by_subject))
            for _ in range(n_permutations)
        ],
        dtype=float,
    )
    interaction_rank = max(1, len(nonreference_groups) * (len(frequencies) - 1))
    residual_df = len(outcome) - base_rank - interaction_rank
    return observed, permutation_values, interaction_rank, residual_df


def run_photic_interactions(
    subject_frequency: pd.DataFrame,
    *,
    n_permutations: int = 1000,
    seed: int = 6036,
    min_support: int = 3,
) -> pd.DataFrame:
    """Run subject-respecting diagnosis × frequency interaction tests."""

    if subject_frequency.empty:
        return pd.DataFrame()
    rng = np.random.default_rng(seed)
    results: list[dict[str, Any]] = []
    inferential = subject_frequency[subject_frequency["family"].isin(["ftr", "jacobian"])]
    for (dimension, family, metric), raw in inferential.groupby(
        ["dimension", "family", "metric"], dropna=False
    ):
        work = raw[
            raw["frequency_hz"].isin(PHOTIC_FREQUENCIES)
            & (pd.to_numeric(raw["n_support"], errors="coerce") >= min_support)
        ].copy()
        coverage = work.groupby("subject_id")["frequency_hz"].nunique()
        complete_subjects = coverage[coverage == len(PHOTIC_FREQUENCIES)].index
        work = work[work["subject_id"].isin(complete_subjects)].copy()
        if work.empty:
            continue
        observed, permuted_array, numerator_df, denominator_df = _fast_interaction_test(
            work,
            n_permutations=n_permutations,
            rng=rng,
        )
        permutation_p = (
            float((1 + np.sum(permuted_array >= observed)) / (1 + len(permuted_array)))
            if np.isfinite(observed) and len(permuted_array)
            else np.nan
        )
        group_counts = work.drop_duplicates("subject_id")["group"].value_counts().to_dict()
        results.append(
            {
                "dimension": int(dimension),
                "family": family,
                "metric": metric,
                "n_subjects": int(work["subject_id"].nunique()),
                "group_counts": json.dumps({str(key): int(value) for key, value in group_counts.items()}, sort_keys=True),
                "n_subject_frequency_rows": int(len(work)),
                "observed_f": observed,
                "permutation_p": permutation_p,
                "parametric_p": float(stats.f.sf(observed, numerator_df, denominator_df))
                if np.isfinite(observed)
                else np.nan,
                "min_support": min_support,
                "frequency_levels": ",".join(str(value) for value in PHOTIC_FREQUENCIES),
                "inference_status": (
                    "primary_9d_ftr"
                    if int(dimension) == 9 and family == "ftr" and metric in PRIMARY_PHOTIC_METRICS
                    else "secondary_or_reference"
                ),
            }
        )
    output = pd.DataFrame(results)
    if output.empty:
        return output
    for status in ["primary_9d_ftr", "secondary_or_reference"]:
        mask = output["inference_status"] == status
        output.loc[mask, "q_value"] = output.loc[mask, "permutation_p"].rank(method="min")
        p_values = output.loc[mask, "permutation_p"]
        valid = np.isfinite(p_values)
        if valid.any():
            ranked = p_values[valid].sort_values()
            adjusted = (ranked * valid.sum() / np.arange(1, valid.sum() + 1)).cummin()
            output.loc[adjusted.index, "q_value"] = adjusted.clip(upper=1.0)
    return output


def run_dementia_photic_followup(
    *,
    raw_root: str | Path,
    output_root: str | Path,
    n_permutations: int = 1000,
    min_support: int = 2,
) -> dict[str, str]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    metadata, audit, subject_frequency = _collect_photic_followup_frames(raw_root)
    audit_summary = _summarize_d0_audit(audit)
    interactions = run_photic_interactions(
        subject_frequency,
        n_permutations=n_permutations,
        min_support=min_support,
    )
    fidelity = subject_frequency[
        subject_frequency["family"] == "transition_qc"
    ].copy()
    paths = {
        "metadata": output / "ds006036_d0_metadata.csv",
        "audit": output / "ds006036_d0_audit.csv",
        "audit_summary": output / "ds006036_d0_audit_summary.csv",
        "subject_frequency": output / "ds006036_subject_frequency_local_dynamics.csv",
        "fidelity": output / "ds006036_photic_fidelity_by_frequency.csv",
        "interactions": output / "ds006036_photic_interactions.csv",
    }
    metadata.to_csv(paths["metadata"], index=False)
    audit.to_csv(paths["audit"], index=False)
    audit_summary.to_csv(paths["audit_summary"], index=False)
    subject_frequency.to_csv(paths["subject_frequency"], index=False)
    fidelity.to_csv(paths["fidelity"], index=False)
    interactions.to_csv(paths["interactions"], index=False)
    return {key: str(value) for key, value in paths.items()}
