"""Fold-local, training-only C2 accessibility candidate.

This module deliberately has no HDF5 reader and no outcome-scoring code. It
accepts only a validated outer-training transition table and current-state
queries. The proposed scalar is a local, training-estimated future-state
covariance log-determinant; it is a candidate feature, not a qualified C2
measurement.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd


FEATURE_NAME = "c2_local_future_cov_logdet_h1_3d_v2"
CHART_COLUMNS = ("m", "d", "e")
ORIGIN_COLUMNS = tuple(f"origin_{name}" for name in CHART_COLUMNS)
TARGET_COLUMNS = tuple(f"target_{name}" for name in CHART_COLUMNS)
QUERY_COLUMNS = ("m", "d", "e")
NEIGHBORS = 32
HORIZON_LAG = 1
WINDOW_SECONDS = 30.0
TIME_TOLERANCE_SECONDS = 0.01
RADIUS_QUANTILE = 0.95

TRANSITION_COLUMNS = {
    "pid", "recording_id", "segment_id", "target_segment_id", "epoch_id", "target_epoch_id",
    "origin_time_seconds", "target_time_seconds", "source_support_ok",
    "origin_coordinate_qc_ok", "target_coordinate_qc_ok",
    *ORIGIN_COLUMNS, *TARGET_COLUMNS,
}
QUERY_METADATA_COLUMNS = {
    "pid", "recording_id", "segment_id", "epoch_id", "time_seconds",
    "source_support_ok", "coordinate_qc_ok", *QUERY_COLUMNS,
}


class C2UnavailableError(ValueError):
    """Raised when the candidate estimator cannot meet its frozen contract."""


def _pid_set(values: Iterable[Any], *, name: str) -> frozenset[str]:
    result = frozenset(str(value) for value in values)
    if not result or any(not value or value.casefold() == "nan" for value in result):
        raise C2UnavailableError(f"{name} must contain nonempty participant IDs")
    return result


def _check_exact_columns(frame: pd.DataFrame, expected: set[str], *, name: str) -> None:
    actual = set(frame.columns)
    missing, extra = sorted(expected - actual), sorted(actual - expected)
    if missing or extra:
        raise C2UnavailableError(
            f"{name} schema mismatch; missing={missing}, extra={extra}; "
            "stage/outcome/future-apply fields are not accepted"
        )


def _bool_values(values: pd.Series, *, name: str) -> np.ndarray:
    parsed: list[bool] = []
    for value in values.tolist():
        if isinstance(value, (bool, np.bool_)):
            parsed.append(bool(value))
        elif isinstance(value, (int, np.integer, float, np.floating)) and value in (0, 1):
            parsed.append(bool(value))
        elif isinstance(value, str) and value.strip().casefold() in {"true", "false", "1", "0"}:
            parsed.append(value.strip().casefold() in {"true", "1"})
        else:
            raise C2UnavailableError(f"{name} must contain only explicit boolean/0/1 values")
    return np.asarray(parsed, dtype=bool)


def _positive_scale(scale: Sequence[float]) -> np.ndarray:
    values = np.asarray(scale, dtype=float)
    if values.shape != (3,) or not np.isfinite(values).all() or np.any(values <= 0):
        raise C2UnavailableError("the shared outer-training 3D chart IQR must be finite and positive")
    return values


@dataclass(frozen=True)
class C2TrainingAtlas:
    """Training-only local transition library in common outer-fold units."""

    training_pids: frozenset[str]
    scale_training_pids: frozenset[str]
    coordinate_scale: np.ndarray
    origin_states_scaled: np.ndarray
    future_states_scaled: np.ndarray
    transition_pids: np.ndarray
    transition_tie_keys: tuple[tuple[str, str, int], ...]
    participant_centers_scaled: dict[str, np.ndarray]
    pair_exclusion_counts: dict[str, int]
    radius_95: float
    n_neighbors: int = NEIGHBORS
    horizon_lag: int = HORIZON_LAG
    feature_name: str = FEATURE_NAME


def fit_c2_training_atlas(
    transitions: pd.DataFrame,
    *,
    training_pids: Sequence[str],
    scale_training_pids: Sequence[str],
    outer_training_iqr: Sequence[float],
    n_neighbors: int = NEIGHBORS,
) -> C2TrainingAtlas:
    """Fit the candidate atlas using outer-training transitions only.

    ``transitions`` contains current/target chart coordinates only for the
    explicitly listed library PIDs. Its support flags must already be bound to
    the outcome-blind source-support ledger. Invalid pairs are excluded; no
    interpolation or imputation is performed. ``outer_training_iqr`` must be
    the participant-balanced IQR transform fitted on exactly
    ``scale_training_pids``. Apply atlases use the complete outer-training
    roster. A training-OOF atlas must omit the queried PID from both its
    transition library and scale-training roster. The output log-determinant
    is converted back to native chart-coordinate units so leave-one-PID-out
    scales do not change its volume units.
    """
    if not isinstance(transitions, pd.DataFrame) or transitions.empty:
        raise C2UnavailableError("training transition table is empty or malformed")
    _check_exact_columns(transitions, TRANSITION_COLUMNS, name="training transition table")
    train_ids = _pid_set(training_pids, name="training_pids")
    scale_ids = _pid_set(scale_training_pids, name="scale_training_pids")
    if not train_ids.issubset(scale_ids):
        raise C2UnavailableError("transition-library PIDs must be included in the scale-training roster")
    if isinstance(n_neighbors, bool) or int(n_neighbors) != n_neighbors or n_neighbors < 2:
        raise C2UnavailableError("n_neighbors must be an integer of at least two")
    k = int(n_neighbors)
    if len(train_ids) < k + 1:
        raise C2UnavailableError(f"at least {k + 1} distinct training PIDs are required")
    scale = _positive_scale(outer_training_iqr)

    rows = transitions.copy()
    rows["pid"] = rows["pid"].astype(str)
    observed_ids = set(rows["pid"])
    if not observed_ids.issubset(train_ids):
        raise C2UnavailableError("transition table contains a PID outside the declared training roster")
    if observed_ids != set(train_ids):
        raise C2UnavailableError("every declared library PID must have transition rows")
    if rows[["pid", "recording_id", "segment_id", "target_segment_id", "epoch_id", "target_epoch_id"]].isna().any().any():
        raise C2UnavailableError("training transition identities must be complete")
    if rows["recording_id"].astype(str).str.strip().eq("").any():
        raise C2UnavailableError("training transition recording IDs must be nonempty")
    for column in ("epoch_id", "target_epoch_id"):
        numeric = pd.to_numeric(rows[column], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(numeric).all() or np.any(numeric != np.rint(numeric)):
            raise C2UnavailableError(f"{column} must contain exact integer row identities")
        rows[column] = np.rint(numeric).astype(np.int64)
    if rows.duplicated(["pid", "recording_id", "segment_id", "epoch_id"]).any():
        raise C2UnavailableError("duplicate training origin identity")
    for column in ("recording_id", "segment_id", "target_segment_id"):
        rows[column] = rows[column].astype(str)
    # Deterministic order is the tie-break for equal-distance transitions.
    rows = rows.sort_values(
        ["pid", "recording_id", "segment_id", "epoch_id"], kind="stable"
    ).reset_index(drop=True)

    origin_time = pd.to_numeric(rows["origin_time_seconds"], errors="coerce").to_numpy(dtype=float)
    target_time = pd.to_numeric(rows["target_time_seconds"], errors="coerce").to_numpy(dtype=float)
    dt = target_time - origin_time
    exact_lag = rows["target_epoch_id"].to_numpy() - rows["epoch_id"].to_numpy() == HORIZON_LAG
    valid_time = np.isfinite(dt) & (np.abs(dt - WINDOW_SECONDS) <= TIME_TOLERANCE_SECONDS)
    support = _bool_values(rows["source_support_ok"], name="source_support_ok")
    origin_qc = _bool_values(rows["origin_coordinate_qc_ok"], name="origin_coordinate_qc_ok")
    target_qc = _bool_values(rows["target_coordinate_qc_ok"], name="target_coordinate_qc_ok")
    origin_segment = rows["segment_id"].astype(str)
    target_segment = rows["target_segment_id"].astype(str)
    same_segment = (
        rows["segment_id"].notna().to_numpy()
        & rows["target_segment_id"].notna().to_numpy()
        & origin_segment.str.strip().ne("").to_numpy()
        & target_segment.str.strip().ne("").to_numpy()
        & (origin_segment.to_numpy() == target_segment.to_numpy())
    )
    origin = rows.loc[:, list(ORIGIN_COLUMNS)].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    future = rows.loc[:, list(TARGET_COLUMNS)].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    reasons = np.full(len(rows), "eligible", dtype=object)

    def mark_excluded(mask: np.ndarray, reason: str) -> None:
        select = (reasons == "eligible") & mask
        reasons[select] = reason

    mark_excluded(~exact_lag, "wrong_h1_row_lag")
    mark_excluded(~valid_time, "noncontiguous_or_wrong_h1_time")
    mark_excluded(~same_segment, "segment_mismatch_or_missing")
    mark_excluded(~support, "source_support_ineligible")
    mark_excluded(~origin_qc, "origin_coordinate_qc_invalid")
    mark_excluded(~target_qc, "target_coordinate_qc_invalid")
    mark_excluded(~np.isfinite(origin).all(axis=1) | ~np.isfinite(future).all(axis=1), "nonfinite_training_chart")
    eligible = reasons == "eligible"
    reason_values, reason_counts = np.unique(reasons, return_counts=True)
    exclusion_counts = {str(reason): int(count) for reason, count in zip(reason_values, reason_counts)}
    rows, origin, future = rows.loc[eligible].reset_index(drop=True), origin[eligible], future[eligible]
    if rows.empty:
        raise C2UnavailableError("no supported contiguous h1 training transitions")
    eligible_pids = set(rows["pid"])
    if len(eligible_pids) < k + 1:
        raise C2UnavailableError("too few distinct supported training PIDs for local covariance")

    origin_scaled = origin / scale[None, :]
    future_scaled = future / scale[None, :]
    pids = rows["pid"].to_numpy(dtype=str)
    tie_keys = tuple(
        (str(recording_id), str(segment_id), int(epoch_id))
        for recording_id, segment_id, epoch_id in rows[
            ["recording_id", "segment_id", "epoch_id"]
        ].itertuples(index=False, name=None)
    )
    centers: dict[str, np.ndarray] = {}
    # Participant-balanced calibration points: median within recording, then
    # median across recordings for each PID.
    state_table = pd.DataFrame(origin_scaled, columns=CHART_COLUMNS)
    state_table["pid"] = pids
    state_table["recording_id"] = rows["recording_id"].astype(str).to_numpy()
    rec = state_table.groupby(["pid", "recording_id"], sort=True, dropna=False)[list(CHART_COLUMNS)].median()
    pid_centers = rec.groupby(level=0, sort=True).median()
    for pid, values in pid_centers.iterrows():
        point = values.to_numpy(dtype=float)
        if np.isfinite(point).all():
            centers[str(pid)] = point
    if len(centers) < k + 1:
        raise C2UnavailableError("too few finite participant centers to calibrate local support")

    # The radius gate is estimated without any held-out PID. Use the same
    # nearest-transition-per-PID rule as apply queries, queried at one
    # participant-balanced median state per library PID.
    loo_radii: list[float] = []
    for pid, point in centers.items():
        best_by_other_pid: dict[str, float] = {}
        for state, transition_pid in zip(origin_scaled, pids):
            other_pid = str(transition_pid)
            if other_pid == pid:
                continue
            distance = float(np.linalg.norm(point - state))
            previous = best_by_other_pid.get(other_pid)
            if previous is None or distance < previous:
                best_by_other_pid[other_pid] = distance
        distances = list(best_by_other_pid.values())
        if len(distances) < k:
            raise C2UnavailableError("leave-one-PID-out support calibration lacks k distinct neighbors")
        loo_radii.append(float(np.partition(np.asarray(distances), k - 1)[k - 1]))
    radius = float(np.quantile(np.asarray(loo_radii), RADIUS_QUANTILE, method="linear"))
    if not np.isfinite(radius) or radius <= 0:
        raise C2UnavailableError("training-only local-support radius is zero or non-finite")

    return C2TrainingAtlas(
        training_pids=frozenset(eligible_pids),
        scale_training_pids=scale_ids,
        coordinate_scale=scale.copy(),
        origin_states_scaled=origin_scaled,
        future_states_scaled=future_scaled,
        transition_pids=pids,
        transition_tie_keys=tie_keys,
        participant_centers_scaled=centers,
        pair_exclusion_counts=exclusion_counts,
        radius_95=radius,
        n_neighbors=k,
    )


def estimate_c2_origin_feature(
    atlas: C2TrainingAtlas,
    origins: pd.DataFrame,
    *,
    partition: str,
) -> pd.DataFrame:
    """Return outcome-blind C2 candidate features for current-state queries.

    The query schema contains no target or stage fields. Apply PIDs must be
    disjoint from the training atlas; training features require a separately
    cross-fitted atlas that excludes the queried PID. Unsupported origins are
    retained with NaN feature and an explicit reason.
    """
    if not isinstance(origins, pd.DataFrame):
        raise C2UnavailableError("origins must be a pandas DataFrame")
    _check_exact_columns(origins, QUERY_METADATA_COLUMNS, name="origin query table")
    if partition not in {"apply", "training_oof"}:
        raise C2UnavailableError("partition must be 'apply' or 'training_oof'")
    query = origins.copy().reset_index(drop=True)
    query["pid"] = query["pid"].astype(str)
    if query[["pid", "recording_id", "segment_id", "epoch_id", "time_seconds"]].isna().any().any():
        raise C2UnavailableError("origin query identities and time must be present")
    query_time = pd.to_numeric(query["time_seconds"], errors="coerce").to_numpy(dtype=float)
    query_epoch = pd.to_numeric(query["epoch_id"], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(query_time).all() or not np.isfinite(query_epoch).all() or np.any(query_epoch != np.rint(query_epoch)):
        raise C2UnavailableError("origin query time and epoch identity must be finite and exact")
    if query.duplicated(["pid", "recording_id", "segment_id", "epoch_id"]).any():
        raise C2UnavailableError("duplicate origin query identity")
    query_pids = set(query["pid"])
    if partition == "apply" and query_pids.intersection(atlas.scale_training_pids):
        raise C2UnavailableError("apply PID overlaps the outer-training scale roster")
    if partition == "training_oof":
        if query_pids.intersection(atlas.training_pids):
            raise C2UnavailableError("training OOF query PID must be excluded from its transition atlas")
        if query_pids.intersection(atlas.scale_training_pids):
            raise C2UnavailableError("training OOF query PID must be excluded from its coordinate-scale roster")

    support = _bool_values(query["source_support_ok"], name="source_support_ok")
    qc = _bool_values(query["coordinate_qc_ok"], name="coordinate_qc_ok")
    values = query.loc[:, list(QUERY_COLUMNS)].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    result = query[["pid", "recording_id", "segment_id", "epoch_id", "time_seconds"]].copy()
    result[FEATURE_NAME] = np.nan
    result["c2_feature_status"] = "unavailable"
    result["c2_feature_reason"] = ""
    result["c2_neighbor_pid_count"] = 0
    result["c2_neighbor_radius_scaled"] = np.nan
    result["c2_training_radius95_scaled"] = atlas.radius_95
    result["c2_atlas_training_pid_count"] = len(atlas.training_pids)
    result["c2_atlas_training_pid_roster_sha256"] = hashlib.sha256(
        "\n".join(sorted(atlas.training_pids)).encode("utf-8")
    ).hexdigest()
    result["c2_scale_training_pid_count"] = len(atlas.scale_training_pids)
    result["c2_scale_training_pid_roster_sha256"] = hashlib.sha256(
        "\n".join(sorted(atlas.scale_training_pids)).encode("utf-8")
    ).hexdigest()
    result["c2_coordinate_scale_sha256"] = hashlib.sha256(
        np.asarray(atlas.coordinate_scale, dtype="<f8").tobytes()
    ).hexdigest()
    points = atlas.origin_states_scaled
    future = atlas.future_states_scaled
    train_pids = atlas.transition_pids

    for i in range(len(query)):
        if not support[i]:
            reason = "source_support_ineligible"
        elif not qc[i]:
            reason = "origin_coordinate_qc_invalid"
        elif not np.isfinite(values[i]).all():
            reason = "origin_chart_nonfinite"
        else:
            query_scaled = values[i] / atlas.coordinate_scale
            # One nearest origin/transition per training PID prevents dense or
            # long recordings from contributing multiple votes.
            best: dict[str, tuple[float, tuple[str, str, int], int]] = {}
            distances = np.linalg.norm(points - query_scaled[None, :], axis=1)
            for row_index, (pid, distance) in enumerate(zip(train_pids, distances)):
                candidate = (
                    float(distance), atlas.transition_tie_keys[row_index], row_index
                )
                prior = best.get(str(pid))
                if prior is None or candidate[:2] < prior[:2]:
                    best[str(pid)] = candidate
            nearest = sorted(best.items(), key=lambda item: (item[1][0], item[0]))[: atlas.n_neighbors]
            radius = nearest[-1][1][0] if len(nearest) == atlas.n_neighbors else np.inf
            result.at[i, "c2_neighbor_pid_count"] = len(nearest)
            result.at[i, "c2_neighbor_radius_scaled"] = radius
            if len(nearest) < atlas.n_neighbors:
                reason = "insufficient_distinct_training_pids"
            elif radius > atlas.radius_95:
                reason = "origin_outside_training_local_support"
            else:
                neighbor_rows = np.asarray([item[1][2] for item in nearest], dtype=int)
                covariance = np.cov(future[neighbor_rows], rowvar=False, ddof=1)
                sign, logdet = np.linalg.slogdet(covariance)
                if not np.isfinite(covariance).all() or sign <= 0 or not np.isfinite(logdet):
                    reason = "local_future_covariance_not_positive_definite"
                else:
                    # Undo the diagonal scale transform so every output uses
                    # the fixed native chart-coordinate volume units.
                    logdet_native_chart = float(logdet + 2.0 * np.log(atlas.coordinate_scale).sum())
                    if not np.isfinite(logdet_native_chart):
                        reason = "local_future_covariance_logdet_nonfinite"
                        result.at[i, "c2_feature_reason"] = reason
                        continue
                    result.at[i, FEATURE_NAME] = logdet_native_chart
                    result.at[i, "c2_feature_status"] = "candidate_computed"
                    result.at[i, "c2_feature_reason"] = ""
                    continue
        result.at[i, "c2_feature_reason"] = reason
    return result
