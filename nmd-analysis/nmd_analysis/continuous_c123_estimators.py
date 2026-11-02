"""Protocol-bound, fold-local C1/C3 estimators for continuous BOAS charts.

This module consumes already-qualified, fold-safe chart surfaces. It does not
load data, create MNPS coordinates, qualify source support, or authorize a
cohort analysis. Callers must pass the outer-training partition separately
from each apply partition; all transforms below are fit on training PIDs only.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import pairwise_distances
from sklearn.model_selection import GroupKFold


C1_RIDGE_ALPHA = 1.0
MIN_REPORTING_PIDS = 20
OUTER_FOLDS = 5
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20260929
C3_MIN_PAIRS_PER_PID_H1 = 10
C3_MAX_ABS_SMD_IQR = 0.10
C3_STAGE_SHIFT_ROWS = 8


class EstimatorUnavailableError(ValueError):
    """Raised when a required fold-local estimator contract is unavailable."""


@dataclass(frozen=True)
class RobustCoordinateTransform:
    """One participant-balanced median/IQR transform for chart coordinates."""

    columns: tuple[str, ...]
    center: np.ndarray
    scale: np.ndarray
    training_pids: tuple[str, ...]
    finite_pid_counts: tuple[int, ...]

    def apply(self, values: Any) -> np.ndarray:
        array = np.asarray(values, dtype=float)
        if array.ndim != 2 or array.shape[1] != len(self.columns):
            raise ValueError("coordinate matrix does not match the fitted transform")
        if not np.isfinite(array).all():
            raise EstimatorUnavailableError("cannot transform non-finite chart coordinates")
        return (array - self.center[None, :]) / self.scale[None, :]


@dataclass(frozen=True)
class C1Examples:
    """Common M0/M1 origin-target rows for one fixed row-lag horizon."""

    current: np.ndarray
    history: np.ndarray
    target: np.ndarray
    metadata: pd.DataFrame


def _require_columns(frame: pd.DataFrame, columns: Iterable[str], name: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def _validity_mask(values: pd.Series, *, column: str) -> np.ndarray:
    """Parse a QC mask conservatively; unknown tokens are an error, not truthy."""
    parsed: list[bool] = []
    for value in values.tolist():
        if isinstance(value, (bool, np.bool_)):
            parsed.append(bool(value))
        elif value is None or value is pd.NA or (
            pd.api.types.is_scalar(value) and bool(pd.isna(value))
        ):
            parsed.append(False)
        elif isinstance(value, (int, np.integer, float, np.floating)) and value in (0, 1):
            parsed.append(bool(value))
        elif isinstance(value, str) and value.strip().casefold() in {"true", "false", "1", "0"}:
            parsed.append(value.strip().casefold() in {"true", "1"})
        else:
            raise ValueError(f"{column} must contain only boolean/0/1 values or missingness")
    return np.asarray(parsed, dtype=bool)


def _exact_epoch_ids(values: pd.Series, *, column: str) -> np.ndarray:
    numeric = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    rounded = np.rint(numeric)
    if (
        not np.isfinite(numeric).all()
        or np.any(numeric < 0)
        or np.any(numeric > 2**53)
        or np.any(numeric != rounded)
    ):
        raise EstimatorUnavailableError(f"{column} must contain exact, nonnegative integer identities")
    return rounded.astype(np.int64)


def _registered_lag(value: int, *, name: str = "horizon_lag") -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or int(value) not in {1, 2, 4}:
        raise ValueError(f"{name} must be one of the preregistered integer row lags 1, 2 or 4")
    return int(value)


def fit_participant_balanced_iqr(
    training_rows: pd.DataFrame,
    chart_columns: Sequence[str],
    *,
    pid_col: str = "pid",
    recording_col: str = "recording_id",
    valid_col: str = "coordinate_qc_valid",
    support_col: str = "source_support_eligible",
    min_training_pids: int = 1,
) -> RobustCoordinateTransform:
    """Fit the protocol's recording-median then PID-median chart IQR transform.

    For each training PID, the summary is the coordinate-wise median across
    that PID's recording-level coordinate medians. Apply rows and all target
    coordinates must use this same returned transform; no apply row is read.
    """
    columns = tuple(str(column) for column in chart_columns)
    if not columns or len(set(columns)) != len(columns):
        raise ValueError("chart_columns must be nonempty and unique")
    if min_training_pids < 1:
        raise ValueError("min_training_pids must be positive")
    _require_columns(training_rows, [pid_col, recording_col, valid_col, support_col, *columns], "training chart rows")
    if training_rows[[pid_col, recording_col]].isna().any().any():
        raise EstimatorUnavailableError("training chart rows have missing PID or recording identity")

    numeric = training_rows.loc[:, columns].apply(pd.to_numeric, errors="coerce")
    valid = _validity_mask(training_rows[valid_col], column=valid_col)
    supported = _validity_mask(training_rows[support_col], column=support_col)
    eligible = valid & supported
    numeric = numeric.loc[eligible].copy()
    identity = training_rows.loc[eligible, [pid_col, recording_col]].copy()
    if numeric.empty:
        raise EstimatorUnavailableError("no QC-valid training chart rows")
    combined = pd.concat([identity.reset_index(drop=True), numeric.reset_index(drop=True)], axis=1)
    recording_medians = combined.groupby([pid_col, recording_col], sort=True, dropna=False)[list(columns)].median()
    pid_summaries = recording_medians.groupby(level=0, sort=True).median()
    finite_counts = pid_summaries.notna().sum(axis=0).to_numpy(dtype=int)
    if np.any(finite_counts < min_training_pids):
        raise EstimatorUnavailableError("too few finite training-PID summaries for at least one chart coordinate")
    center = pid_summaries.median(axis=0).to_numpy(dtype=float)
    scale = (pid_summaries.quantile(0.75) - pid_summaries.quantile(0.25)).to_numpy(dtype=float)
    if not np.isfinite(center).all() or not np.isfinite(scale).all() or np.any(scale <= 0):
        raise EstimatorUnavailableError("a chart coordinate has a zero or non-finite training-PID IQR")
    # Retain the complete assigned training roster, including PIDs whose rows
    # are all unsupported/QC-invalid. This roster is also needed for leakage
    # checks; coordinate summaries/counts remain based only on eligible rows.
    training_pids = tuple(sorted(str(pid) for pid in training_rows[pid_col].unique()))
    return RobustCoordinateTransform(
        columns=columns,
        center=center,
        scale=scale,
        training_pids=training_pids,
        finite_pid_counts=tuple(int(value) for value in finite_counts),
    )


def grouped_pid_splits(
    rows: pd.DataFrame,
    *,
    pid_col: str = "pid",
    n_splits: int = 5,
) -> Iterable[tuple[pd.DataFrame, pd.DataFrame]]:
    """Yield deterministic GroupKFold partitions with all recordings per PID together."""
    _require_columns(rows, [pid_col], "chart rows")
    if rows[pid_col].isna().any():
        raise ValueError("GroupKFold requires a nonmissing PID for every row")
    groups = rows[pid_col].astype(str).to_numpy()
    if n_splits != OUTER_FOLDS:
        raise ValueError(f"the frozen C1/C3 outer split is exactly GroupKFold({OUTER_FOLDS})")
    if len(set(groups)) < OUTER_FOLDS:
        raise ValueError(f"GroupKFold({OUTER_FOLDS}) requires at least {OUTER_FOLDS} independent PIDs")
    splitter = GroupKFold(n_splits=n_splits)
    for train_index, test_index in splitter.split(np.zeros(len(rows)), groups=groups):
        train = rows.iloc[train_index].copy()
        test = rows.iloc[test_index].copy()
        if set(train[pid_col].astype(str)) & set(test[pid_col].astype(str)):
            raise RuntimeError("PID leakage across grouped outer folds")
        yield train, test


@dataclass(frozen=True)
class GroupedPIDFold:
    fold_id: int
    training_pids: tuple[str, ...]
    evaluation_pids: tuple[str, ...]


@dataclass(frozen=True)
class GroupedPIDSplitManifest:
    """Deterministic five-fold GroupKFold roster, bound to row/group counts."""

    pid_column: str
    expected_pids: tuple[str, ...]
    participant_row_counts: tuple[tuple[str, int], ...]
    folds: tuple[GroupedPIDFold, ...]
    row_count: int
    sha256: str


def _grouped_pid_manifest_payload(
    pid_column: str,
    row_count: int,
    participant_row_counts: tuple[tuple[str, int], ...],
    expected_pids: tuple[str, ...],
    folds: tuple[GroupedPIDFold, ...],
) -> dict[str, Any]:
    return {
        "pid_column": pid_column,
        "row_count": int(row_count),
        "participant_row_counts": participant_row_counts,
        "expected_pids": expected_pids,
        "folds": [
            {
                "fold_id": fold.fold_id,
                "training_pids": fold.training_pids,
                "evaluation_pids": fold.evaluation_pids,
            }
            for fold in folds
        ],
    }


def _validate_grouped_pid_manifest(manifest: GroupedPIDSplitManifest) -> None:
    if not isinstance(manifest, GroupedPIDSplitManifest):
        raise TypeError("C1/C3 assembly requires a GroupedPIDSplitManifest")
    if not manifest.pid_column or manifest.row_count < 0:
        raise ValueError("split manifest PID column and row count must be valid")
    counts = manifest.participant_row_counts
    count_pids = tuple(pid for pid, _ in counts)
    if (
        not count_pids
        or count_pids != tuple(sorted(set(count_pids)))
        or any(not isinstance(count, int) or isinstance(count, bool) or count <= 0 for _, count in counts)
        or sum(count for _, count in counts) != manifest.row_count
        or manifest.expected_pids != count_pids
        or len(count_pids) < OUTER_FOLDS
    ):
        raise ValueError("split manifest PID roster or participant row counts are invalid")
    if len(manifest.folds) != OUTER_FOLDS or tuple(fold.fold_id for fold in manifest.folds) != tuple(range(OUTER_FOLDS)):
        raise ValueError("split manifest fold IDs must be exactly 0..4 in GroupKFold order")
    expected = set(manifest.expected_pids)
    seen_evaluation: set[str] = set()
    for fold in manifest.folds:
        training = tuple(fold.training_pids)
        evaluation = tuple(fold.evaluation_pids)
        if (
            training != tuple(sorted(set(training)))
            or evaluation != tuple(sorted(set(evaluation)))
            or set(training) & set(evaluation)
            or set(training) | set(evaluation) != expected
            or seen_evaluation & set(evaluation)
        ):
            raise ValueError(f"split manifest fold {fold.fold_id} has invalid or overlapping PID rosters")
        seen_evaluation.update(evaluation)
    if seen_evaluation != expected:
        raise ValueError("split manifest evaluation rosters do not cover the expected PID roster exactly")
    reconstructed_groups = np.concatenate([
        np.repeat(pid, count) for pid, count in counts
    ])
    splitter = GroupKFold(n_splits=OUTER_FOLDS)
    for fold_id, (train_index, eval_index) in enumerate(
        splitter.split(np.zeros(len(reconstructed_groups)), groups=reconstructed_groups)
    ):
        actual_training = tuple(sorted(set(reconstructed_groups[train_index])))
        actual_evaluation = tuple(sorted(set(reconstructed_groups[eval_index])))
        manifest_fold = manifest.folds[fold_id]
        if actual_training != manifest_fold.training_pids or actual_evaluation != manifest_fold.evaluation_pids:
            raise ValueError(
                f"split manifest fold {fold_id} differs from deterministic GroupKFold assignment"
            )
    payload = _grouped_pid_manifest_payload(
        manifest.pid_column,
        manifest.row_count,
        manifest.participant_row_counts,
        manifest.expected_pids,
        manifest.folds,
    )
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if manifest.sha256 != digest:
        raise ValueError("split manifest digest does not match its row roster and fold assignments")


def build_grouped_pid_manifest(
    rows: pd.DataFrame,
    *,
    pid_col: str = "pid",
) -> GroupedPIDSplitManifest:
    """Freeze the exact deterministic GroupKFold assignment for the supplied rows."""
    _require_columns(rows, [pid_col], "chart rows")
    if rows[pid_col].isna().any():
        raise ValueError("GroupKFold requires a nonmissing PID for every row")
    groups = rows[pid_col].astype(str).to_numpy()
    if len(set(groups)) < OUTER_FOLDS:
        raise ValueError(f"GroupKFold({OUTER_FOLDS}) requires at least {OUTER_FOLDS} independent PIDs")
    participant_row_counts = tuple(
        (str(pid), int(count))
        for pid, count in rows.assign(__pid_normalized=groups).groupby("__pid_normalized", sort=True).size().items()
    )
    expected_pids = tuple(pid for pid, _ in participant_row_counts)
    fold_rosters: list[GroupedPIDFold] = []
    splitter = GroupKFold(n_splits=OUTER_FOLDS)
    for fold_id, (train_index, eval_index) in enumerate(splitter.split(np.zeros(len(rows)), groups=groups)):
        training_pids = tuple(sorted(set(groups[train_index])))
        evaluation_pids = tuple(sorted(set(groups[eval_index])))
        if set(training_pids) & set(evaluation_pids):
            raise RuntimeError("PID leakage while creating the deterministic split manifest")
        fold_rosters.append(GroupedPIDFold(fold_id, training_pids, evaluation_pids))
    payload = _grouped_pid_manifest_payload(
        pid_col,
        int(len(rows)),
        participant_row_counts,
        expected_pids,
        tuple(fold_rosters),
    )
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return GroupedPIDSplitManifest(
        pid_column=pid_col,
        expected_pids=expected_pids,
        participant_row_counts=participant_row_counts,
        folds=tuple(fold_rosters),
        row_count=int(len(rows)),
        sha256=digest,
    )


def _check_disjoint_pids(training: pd.DataFrame, apply: pd.DataFrame, pid_col: str) -> None:
    _require_columns(training, [pid_col], "training partition")
    _require_columns(apply, [pid_col], "apply partition")
    if training[pid_col].isna().any() or apply[pid_col].isna().any():
        raise ValueError("training/apply PID identity must be complete")
    overlap = set(training[pid_col].astype(str)) & set(apply[pid_col].astype(str))
    if overlap:
        raise ValueError(f"training and apply partitions share PIDs: {sorted(overlap)}")


def build_c1_examples(
    rows: pd.DataFrame,
    chart_columns: Sequence[str],
    *,
    horizon_lag: int,
    pid_col: str = "pid",
    recording_col: str = "recording_id",
    segment_col: str = "segment_id",
    epoch_col: str = "epoch_id",
    time_col: str = "t_end",
    valid_col: str = "coordinate_qc_valid",
    support_col: str = "source_support_eligible",
    history_shift_rows: int = 0,
) -> C1Examples:
    """Construct common M0/M1 rows without bridging gaps or segment boundaries.

    `history_shift_rows=0` is the primary two-row history. A value >=5 is the
    preregistered within-segment shifted-history diagnostic; it never changes
    the primary predictor or its evaluation-row intersection.
    """
    columns = tuple(str(column) for column in chart_columns)
    horizon_lag = _registered_lag(horizon_lag)
    if (
        isinstance(history_shift_rows, (bool, np.bool_))
        or not isinstance(history_shift_rows, (int, np.integer))
        or history_shift_rows < 0
        or (history_shift_rows not in {0} and history_shift_rows < 5)
    ):
        raise ValueError("history_shift_rows must be 0 or at least 5")
    history_shift_rows = int(history_shift_rows)
    _require_columns(
        rows,
        [pid_col, recording_col, segment_col, epoch_col, time_col, valid_col, support_col, *columns],
        "C1 chart rows",
    )
    if rows[[pid_col, recording_col, segment_col]].isna().any().any():
        raise EstimatorUnavailableError("C1 rows have missing PID, recording or contiguous-segment identity")
    # Use positional row identities internally. reset_index(drop=True) is safe
    # for named/non-integer caller indices and avoids overwriting an `index`
    # column supplied by the chart table.
    work = rows.copy().reset_index(drop=True)
    work["__epoch"] = _exact_epoch_ids(work[epoch_col], column=epoch_col)
    work["__time"] = pd.to_numeric(work[time_col], errors="coerce")
    work["__valid"] = _validity_mask(work[valid_col], column=valid_col)
    work["__support"] = _validity_mask(work[support_col], column=support_col)
    values = work.loc[:, columns].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    current_rows: list[np.ndarray] = []
    history_rows: list[np.ndarray] = []
    target_rows: list[np.ndarray] = []
    metadata: list[dict[str, Any]] = []

    groups = work.groupby([pid_col, recording_col, segment_col], sort=False, dropna=False)
    for (pid, recording, segment), group in groups:
        group = group.sort_values("__epoch", kind="stable")
        epoch_ids = group["__epoch"].to_numpy(dtype=np.int64)
        if len(np.unique(epoch_ids)) != len(epoch_ids):
            raise EstimatorUnavailableError("duplicate epoch identity within a C1 recording segment")
        positions = group.index.to_numpy(dtype=int)
        for origin_local in range(len(group)):
            target_local = origin_local + horizon_lag
            history1_local = origin_local - 1 - history_shift_rows
            history2_local = origin_local - 2 - history_shift_rows
            if min(history1_local, history2_local) < 0 or target_local >= len(group):
                continue
            start_local = history2_local
            interval_ids = epoch_ids[start_local:target_local + 1]
            if len(interval_ids) != target_local - start_local + 1 or np.any(np.diff(interval_ids) != 1):
                continue
            interval_positions = positions[start_local:target_local + 1]
            if not work.loc[interval_positions, "__valid"].all() or not work.loc[interval_positions, "__support"].all():
                continue
            interval_values = values[interval_positions]
            if not np.isfinite(interval_values).all():
                continue
            interval_times = pd.to_numeric(work.loc[interval_positions, "__time"], errors="coerce").to_numpy(dtype=float)
            if not np.isfinite(interval_times).all() or np.any(np.diff(interval_times) <= 0):
                continue
            origin_pos = int(positions[origin_local])
            target_pos = int(positions[target_local])
            current_rows.append(values[origin_pos])
            history_rows.append(np.concatenate([
                values[origin_pos],
                values[int(positions[history1_local])],
                values[int(positions[history2_local])],
            ]))
            target_rows.append(values[target_pos])
            metadata.append({
                "pid": pid,
                "recording_id": recording,
                "segment_id": segment,
                "origin_epoch_id": int(epoch_ids[origin_local]),
                "target_epoch_id": int(epoch_ids[target_local]),
                "origin_row_position": origin_pos,
                "target_row_position": target_pos,
                "origin_t_end": float(work.loc[origin_pos, "__time"]),
                "target_t_end": float(work.loc[target_pos, "__time"]),
                "actual_horizon_seconds": float(work.loc[target_pos, "__time"] - work.loc[origin_pos, "__time"]),
                "history_shift_rows": int(history_shift_rows),
            })

    d = len(columns)
    return C1Examples(
        current=np.vstack(current_rows) if current_rows else np.empty((0, d), dtype=float),
        history=np.vstack(history_rows) if history_rows else np.empty((0, 3 * d), dtype=float),
        target=np.vstack(target_rows) if target_rows else np.empty((0, d), dtype=float),
        metadata=pd.DataFrame(metadata),
    )


def _participant_balanced_c1_reduction(metrics: pd.DataFrame) -> pd.Series:
    """Reduce row MSEs: rows within recording, recordings within PID, PIDs equally."""
    _require_columns(metrics, ["pid", "recording_id", "mse_m0", "mse_m1"], "C1 row losses")
    recording = metrics.groupby(["pid", "recording_id"], sort=True)[["mse_m0", "mse_m1"]].mean()
    participant = recording.groupby(level=0, sort=True).mean()
    return participant["mse_m0"] - participant["mse_m1"]


def participant_cluster_bootstrap_interval(
    participant_values: Sequence[float],
    *,
    seed: int = BOOTSTRAP_SEED,
    draws: int = BOOTSTRAP_DRAWS,
) -> tuple[float, float]:
    """Percentile CI from participant-cluster bootstrap means (protocol default 10k)."""
    values = np.asarray(participant_values, dtype=float)
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise EstimatorUnavailableError("bootstrap requires a nonempty finite participant-level vector")
    if draws != BOOTSTRAP_DRAWS or seed != BOOTSTRAP_SEED:
        raise ValueError("bootstrap draws and seed are frozen at 10,000 and 20260929")
    rng = np.random.default_rng(seed)
    sampled = rng.integers(0, values.size, size=(draws, values.size))
    means = values[sampled].mean(axis=1)
    lower, upper = np.quantile(means, [0.025, 0.975])
    return float(lower), float(upper)


def _scale_history_blocks(history: np.ndarray, transform: RobustCoordinateTransform) -> np.ndarray:
    d = len(transform.columns)
    if history.shape[1] != 3 * d:
        raise ValueError("C1 history matrix must contain current plus exactly two chart rows")
    return np.concatenate(
        [transform.apply(history[:, i * d:(i + 1) * d]) for i in range(3)],
        axis=1,
    )


@dataclass(frozen=True)
class C1FoldResult:
    fold_id: int
    horizon_lag: int
    chart_columns: tuple[str, ...]
    history_shift_rows: int
    training_pids: tuple[str, ...]
    evaluation_pid_count: int
    scored_participant_count: int
    evaluation_pids: tuple[str, ...]
    training_example_count: int
    evaluation_example_count: int
    median_actual_horizon_seconds: float | None
    participant_reductions: tuple[tuple[str, float], ...]
    transform: RobustCoordinateTransform


@dataclass(frozen=True)
class C1OutOfFoldSummary:
    gate_status: str
    split_manifest_sha256: str
    participant_count: int
    expected_pid_count: int
    pids_without_scores: tuple[str, ...]
    mean_mse_reduction: float | None
    ci95: tuple[float, float] | None
    participant_reductions: tuple[tuple[str, float], ...]


def evaluate_c1_fold(
    training_rows: pd.DataFrame,
    evaluation_rows: pd.DataFrame,
    chart_columns: Sequence[str],
    *,
    horizon_lag: int,
    fold_id: int,
    pid_col: str = "pid",
    recording_col: str = "recording_id",
    segment_col: str = "segment_id",
    epoch_col: str = "epoch_id",
    time_col: str = "t_end",
    valid_col: str = "coordinate_qc_valid",
    support_col: str = "source_support_eligible",
    history_shift_rows: int = 0,
) -> C1FoldResult:
    """Fit fixed M0/M1 Ridge models in one explicitly numbered outer fold.

    This returns fold-local per-PID reductions and the complete assigned
    evaluation roster. The single cohort estimate/interval is produced only
    after all five fixed folds are assembled by ``summarize_c1_out_of_fold``.
    """
    horizon_lag = _registered_lag(horizon_lag)
    if isinstance(fold_id, (bool, np.bool_)) or not isinstance(fold_id, (int, np.integer)) or int(fold_id) not in range(OUTER_FOLDS):
        raise ValueError(f"fold_id must be an integer in 0..{OUTER_FOLDS - 1}")
    fold_id = int(fold_id)
    chart_columns = tuple(str(column) for column in chart_columns)
    _check_disjoint_pids(training_rows, evaluation_rows, pid_col)
    evaluation_pids = tuple(sorted(str(pid) for pid in evaluation_rows[pid_col].unique()))
    transform = fit_participant_balanced_iqr(
        training_rows, chart_columns, pid_col=pid_col,
        recording_col=recording_col, valid_col=valid_col, support_col=support_col,
    )
    train = build_c1_examples(
        training_rows, chart_columns, horizon_lag=horizon_lag,
        pid_col=pid_col, recording_col=recording_col, segment_col=segment_col,
        epoch_col=epoch_col, time_col=time_col, valid_col=valid_col, support_col=support_col,
        history_shift_rows=history_shift_rows,
    )
    apply = build_c1_examples(
        evaluation_rows, chart_columns, horizon_lag=horizon_lag,
        pid_col=pid_col, recording_col=recording_col, segment_col=segment_col,
        epoch_col=epoch_col, time_col=time_col, valid_col=valid_col, support_col=support_col,
        history_shift_rows=history_shift_rows,
    )
    if not train.metadata.shape[0]:
        raise EstimatorUnavailableError("C1 fold has no valid common M0/M1 training rows")
    if not apply.metadata.shape[0]:
        return C1FoldResult(
            fold_id=fold_id,
            horizon_lag=horizon_lag,
            chart_columns=chart_columns,
            history_shift_rows=int(history_shift_rows),
            training_pids=transform.training_pids,
            evaluation_pid_count=len(evaluation_pids),
            scored_participant_count=0,
            evaluation_pids=evaluation_pids,
            training_example_count=len(train.metadata),
            evaluation_example_count=0,
            median_actual_horizon_seconds=None,
            participant_reductions=(),
            transform=transform,
        )

    x0_train = transform.apply(train.current)
    x1_train = _scale_history_blocks(train.history, transform)
    y_train = transform.apply(train.target)
    x0_apply = transform.apply(apply.current)
    x1_apply = _scale_history_blocks(apply.history, transform)
    y_apply = transform.apply(apply.target)
    m0 = Ridge(alpha=C1_RIDGE_ALPHA, fit_intercept=True).fit(x0_train, y_train)
    m1 = Ridge(alpha=C1_RIDGE_ALPHA, fit_intercept=True).fit(x1_train, y_train)
    pred0, pred1 = m0.predict(x0_apply), m1.predict(x1_apply)
    losses = apply.metadata[["pid", "recording_id"]].copy()
    losses["mse_m0"] = np.mean((y_apply - pred0) ** 2, axis=1)
    losses["mse_m1"] = np.mean((y_apply - pred1) ** 2, axis=1)
    participant_reductions = _participant_balanced_c1_reduction(losses)
    participant_values = tuple(
        (str(pid), float(value)) for pid, value in participant_reductions.items()
    )
    n_pids = int(len(participant_values))
    actual_horizon = apply.metadata["actual_horizon_seconds"].to_numpy(dtype=float)
    return C1FoldResult(
        fold_id=fold_id,
        horizon_lag=horizon_lag,
        chart_columns=chart_columns,
        history_shift_rows=int(history_shift_rows),
        training_pids=transform.training_pids,
        evaluation_pid_count=len(evaluation_pids),
        scored_participant_count=n_pids,
        evaluation_pids=evaluation_pids,
        training_example_count=len(train.metadata),
        evaluation_example_count=len(apply.metadata),
        median_actual_horizon_seconds=float(np.median(actual_horizon)),
        participant_reductions=participant_values,
        transform=transform,
    )


def summarize_c1_out_of_fold(
    fold_results: Sequence[C1FoldResult],
    *,
    split_manifest: GroupedPIDSplitManifest,
) -> C1OutOfFoldSummary:
    """Pool fold-held-out participant reductions once, then bootstrap PIDs once.

    Grouped splits must ensure every biological PID is held out exactly once.
    Reject duplicate PIDs rather than silently averaging a leakage/assembly bug.
    """
    _validate_grouped_pid_manifest(split_manifest)
    if len(fold_results) != OUTER_FOLDS or len(split_manifest.folds) != OUTER_FOLDS:
        raise ValueError(f"C1 out-of-fold summary requires all {OUTER_FOLDS} expected folds")
    expected = split_manifest.expected_pids
    if not expected or len(set(expected)) != len(expected):
        raise ValueError("split manifest must contain a nonempty unique biological PID roster")
    if tuple(fold.fold_id for fold in split_manifest.folds) != tuple(range(OUTER_FOLDS)):
        raise ValueError("split manifest fold IDs must be exactly 0..4 in GroupKFold order")
    fold_ids = [result.fold_id for result in fold_results]
    if sorted(fold_ids) != list(range(OUTER_FOLDS)):
        raise ValueError(f"C1 out-of-fold summary requires each fold id 0..{OUTER_FOLDS - 1} exactly once")
    for result in fold_results:
        _registered_lag(result.horizon_lag)
    signatures = {
        (result.horizon_lag, result.chart_columns, result.history_shift_rows)
        for result in fold_results
    }
    if len(signatures) != 1:
        raise ValueError("C1 folds have mixed horizon, chart representation or history-shift settings")
    evaluation_roster: set[str] = set()
    reductions: list[tuple[str, float]] = []
    for result in fold_results:
        manifest_fold = split_manifest.folds[result.fold_id]
        fold_evaluation_pids = set(result.evaluation_pids)
        if len(fold_evaluation_pids) != result.evaluation_pid_count:
            raise ValueError(f"C1 fold {result.fold_id} has duplicate/mismatched evaluation PID roster")
        if tuple(sorted(result.training_pids)) != manifest_fold.training_pids:
            raise ValueError(f"C1 fold {result.fold_id} training PID roster differs from the GroupKFold manifest")
        if tuple(sorted(fold_evaluation_pids)) != manifest_fold.evaluation_pids:
            raise ValueError(f"C1 fold {result.fold_id} evaluation PID roster differs from the GroupKFold manifest")
        if set(result.training_pids) != set(expected) - fold_evaluation_pids:
            raise ValueError(f"C1 fold {result.fold_id} training roster is not the expected cohort complement")
        overlap = evaluation_roster & fold_evaluation_pids
        if overlap:
            raise ValueError(f"C1 evaluation PIDs occur in multiple outer folds: {sorted(overlap)}")
        evaluation_roster.update(fold_evaluation_pids)
        fold_score_pids = {str(pid) for pid, _ in result.participant_reductions}
        if not fold_score_pids.issubset(fold_evaluation_pids):
            raise ValueError(f"C1 fold {result.fold_id} contains scores for PIDs outside its evaluation roster")
        if len(fold_score_pids) != result.scored_participant_count:
            raise ValueError(f"C1 fold {result.fold_id} has duplicate/mismatched scored PID identities")
        for pid, value in result.participant_reductions:
            normalized_pid = str(pid)
            if not np.isfinite(value):
                raise EstimatorUnavailableError("out-of-fold participant reduction must be finite")
            reductions.append((normalized_pid, float(value)))
    if evaluation_roster != set(expected):
        raise ValueError(
            "C1 outer folds do not cover the expected PID roster exactly; "
            f"missing={sorted(set(expected) - evaluation_roster)}, extra={sorted(evaluation_roster - set(expected))}"
        )
    reductions.sort(key=lambda item: item[0])
    n_pids = len(reductions)
    scored_pids = {pid for pid, _ in reductions}
    pids_without_scores = tuple(sorted(set(expected) - scored_pids))
    if n_pids < MIN_REPORTING_PIDS:
        return C1OutOfFoldSummary(
            "INCONCLUSIVE", split_manifest.sha256, n_pids, len(expected),
            pids_without_scores, None, None, tuple(reductions)
        )
    values = np.asarray([value for _, value in reductions], dtype=float)
    return C1OutOfFoldSummary(
        "DESCRIPTIVE_SCORE_AVAILABLE",
        split_manifest.sha256,
        n_pids,
        len(expected),
        pids_without_scores,
        float(values.mean()),
        participant_cluster_bootstrap_interval(values),
        tuple(reductions),
    )


@dataclass(frozen=True)
class C3DistanceTransform:
    """Outer-training-only scaling for C3 chart coordinates and recording time."""

    chart: RobustCoordinateTransform
    time_column: str
    time_center: float
    time_scale: float

    @property
    def training_pids(self) -> tuple[str, ...]:
        return self.chart.training_pids

    def apply(self, chart_values: Any, relative_time: Any) -> np.ndarray:
        chart_scaled = self.chart.apply(chart_values)
        time = np.asarray(relative_time, dtype=float).reshape(-1)
        if time.size != chart_scaled.shape[0] or not np.isfinite(time).all():
            raise EstimatorUnavailableError("C3 distance transform needs one finite time per chart row")
        time_scaled = (time - self.time_center) / self.time_scale
        return np.column_stack([chart_scaled, time_scaled])


@dataclass(frozen=True)
class C3Caliper:
    """Frozen training-partition 95th-percentile nearest-origin distance."""

    threshold: float
    training_pid_count: int
    training_context_cell_count: int
    participant_cell_means: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class C3BalanceGate:
    gate_status: str
    chart_columns: tuple[str, ...]
    split_manifest_sha256: str
    expected_pid_count: int
    pids_without_matches: tuple[str, ...]
    eligible_pid_count: int
    qualifying_pid_count: int
    pair_count: int
    matched_pid_count: int
    matched_pair_count: int
    smd_iqr: tuple[tuple[str, float], ...]
    reasons: tuple[str, ...]
    matched_pair_digest: str
    matched_content_sha256: str


@dataclass(frozen=True)
class C3EffectSummary:
    gate_status: str
    participant_count: int
    outcome_eligible_pair_count: int
    matched_pair_count: int
    mean_difference_iqr: tuple[tuple[str, float], ...] | None
    ci95: tuple[tuple[str, tuple[float, float]], ...] | None


@dataclass(frozen=True)
class C3OutOfFoldResult:
    """Validated five-fold C3 matches and outcomes bound to one split/representation."""

    matched_pairs: pd.DataFrame
    scored_pairs: pd.DataFrame
    split_manifest: GroupedPIDSplitManifest
    horizon_lag: int
    chart_columns: tuple[str, ...]
    assembled_fold_ids: tuple[int, ...]
    fold_match_counts: tuple[int, ...]
    fold_scored_counts: tuple[int, ...]
    matched_content_sha256: str
    scored_content_sha256: str


@dataclass(frozen=True)
class C3MatchedOriginOutOfFold:
    """Validated five-fold C3 origin matches with no outcome table attached."""

    matched_pairs: pd.DataFrame
    split_manifest: GroupedPIDSplitManifest
    horizon_lag: int
    chart_columns: tuple[str, ...]
    assembled_fold_ids: tuple[int, ...]
    fold_match_counts: tuple[int, ...]
    matched_content_sha256: str


def fit_c3_distance_transform(
    training_rows: pd.DataFrame,
    chart_columns: Sequence[str],
    *,
    time_col: str = "recording_relative_seconds",
    pid_col: str = "pid",
    recording_col: str = "recording_id",
    valid_col: str = "coordinate_qc_valid",
    support_col: str = "source_support_eligible",
) -> C3DistanceTransform:
    """Fit chart/time centers and IQRs from participant-balanced training summaries.

    Each variable gets a recording median per PID and a median across that
    PID's recordings; the final center/IQR gives each training PID one vote.
    No apply/evaluation values are accepted by this function.
    """
    columns = tuple(str(column) for column in chart_columns)
    if not columns or time_col in columns:
        raise ValueError("C3 requires chart columns and a distinct recording-relative time column")
    combined = fit_participant_balanced_iqr(
        training_rows,
        [*columns, time_col],
        pid_col=pid_col,
        recording_col=recording_col,
        valid_col=valid_col,
        support_col=support_col,
    )
    chart = RobustCoordinateTransform(
        columns=columns,
        center=combined.center[:len(columns)].copy(),
        scale=combined.scale[:len(columns)].copy(),
        training_pids=combined.training_pids,
        finite_pid_counts=combined.finite_pid_counts[:len(columns)],
    )
    time_center = float(combined.center[-1])
    time_scale = float(combined.scale[-1])
    if not np.isfinite(time_center) or not np.isfinite(time_scale) or time_scale <= 0:
        raise EstimatorUnavailableError("recording-relative time has zero or non-finite training-PID IQR")
    return C3DistanceTransform(
        chart=chart,
        time_column=time_col,
        time_center=time_center,
        time_scale=time_scale,
    )


def _prepare_c3_current_rows(
    rows: pd.DataFrame,
    transform: C3DistanceTransform,
    *,
    pid_col: str,
    recording_col: str,
    segment_col: str,
    stage_col: str,
    epoch_col: str,
    time_col: str,
    stage_pure_col: str,
    stage_conflict_col: str | None,
    valid_col: str,
    support_col: str,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Validate and scale only current-origin fields used by C3 matching."""
    required = [
        pid_col, recording_col, segment_col, stage_col, epoch_col, "t_end", time_col,
        stage_pure_col, valid_col, support_col, *transform.chart.columns,
    ]
    if stage_conflict_col is not None:
        required.append(stage_conflict_col)
    _require_columns(rows, required, "C3 origin rows")
    identity = [pid_col, recording_col, segment_col]
    if rows[identity].isna().any().any():
        raise EstimatorUnavailableError("C3 rows have missing PID, recording or segment identity")

    work = rows.copy().reset_index(drop=True)
    work["__epoch"] = _exact_epoch_ids(work[epoch_col], column=epoch_col)
    work["__t_end"] = pd.to_numeric(work["t_end"], errors="coerce")
    work["__time_relative"] = pd.to_numeric(work[time_col], errors="coerce")
    work["__stage"] = work[stage_col].astype("string").str.strip().str.casefold().map(
        {"n2": "N2", "wake": "Wake"}
    )
    work["__valid"] = _validity_mask(work[valid_col], column=valid_col)
    work["__support"] = _validity_mask(work[support_col], column=support_col)
    work["__stage_pure"] = _validity_mask(work[stage_pure_col], column=stage_pure_col)
    if stage_conflict_col is not None:
        conflict = _validity_mask(work[stage_conflict_col], column=stage_conflict_col)
    else:
        conflict = np.zeros(len(work), dtype=bool)

    if work.duplicated([pid_col, recording_col, "__epoch"]).any():
        raise EstimatorUnavailableError("C3 origin epoch identities must be unique within each PID-recording")
    chart_values = work.loc[:, transform.chart.columns].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    time_values = work["__time_relative"].to_numpy(dtype=float)
    t_end = work["__t_end"].to_numpy(dtype=float)
    eligible = (
        work["__valid"].to_numpy(dtype=bool)
        & work["__support"].to_numpy(dtype=bool)
        & work["__stage_pure"].to_numpy(dtype=bool)
        & ~conflict
        & work["__stage"].notna().to_numpy(dtype=bool)
        & np.isfinite(chart_values).all(axis=1)
        & np.isfinite(time_values)
        & np.isfinite(t_end)
    )
    work = work.loc[eligible].copy().reset_index(drop=True)
    chart_values = chart_values[eligible]
    time_values = time_values[eligible]
    work["__stage"] = work["__stage"].astype(str)
    if work.empty:
        return work, np.empty((0, len(transform.chart.columns) + 1), dtype=float)
    return work, transform.apply(chart_values, time_values)


def fit_c3_caliper(
    training_rows: pd.DataFrame,
    transform: C3DistanceTransform,
    *,
    pid_col: str = "pid",
    recording_col: str = "recording_id",
    segment_col: str = "segment_id",
    stage_col: str = "stage",
    epoch_col: str = "epoch_id",
    time_col: str | None = None,
    stage_pure_col: str = "stage_window_pure",
    stage_conflict_col: str | None = "stage_conflict",
    valid_col: str = "coordinate_qc_valid",
    support_col: str = "source_support_eligible",
) -> C3Caliper:
    """Derive C3's distance threshold from nearest distinct training origins only."""
    effective_time_col = time_col or transform.time_column
    candidates, scaled = _prepare_c3_current_rows(
        training_rows, transform,
        pid_col=pid_col, recording_col=recording_col, segment_col=segment_col,
        stage_col=stage_col, epoch_col=epoch_col, time_col=effective_time_col,
        stage_pure_col=stage_pure_col, stage_conflict_col=stage_conflict_col,
        valid_col=valid_col, support_col=support_col,
    )
    unexpected_pids = set(candidates[pid_col].astype(str)) - set(transform.training_pids)
    if unexpected_pids:
        raise ValueError(f"caliper rows include PIDs outside the fitted outer-training transform: {sorted(unexpected_pids)}")
    cell_records: list[tuple[str, str, str, float]] = []
    for (pid, recording, stage), index in candidates.groupby(
        [pid_col, recording_col, "__stage"], sort=True
    ).groups.items():
        positions = np.asarray(list(index), dtype=int)
        if positions.size < 2:
            continue
        distances = pairwise_distances(scaled[positions], metric="euclidean")
        np.fill_diagonal(distances, np.inf)
        nearest = distances.min(axis=1)
        finite = nearest[np.isfinite(nearest)]
        if finite.size:
            cell_records.append((str(pid), str(recording), str(stage), float(np.median(finite))))
    if not cell_records:
        raise EstimatorUnavailableError("no training PID-recording-stage cell has distinct eligible origins")
    cells = pd.DataFrame(cell_records, columns=["pid", "recording_id", "stage", "median_nearest"])
    participant_means = cells.groupby("pid", sort=True)["median_nearest"].mean()
    threshold = float(participant_means.quantile(0.95, interpolation="linear"))
    if not np.isfinite(threshold) or threshold < 0:
        raise EstimatorUnavailableError("training-derived C3 caliper is non-finite")
    return C3Caliper(
        threshold=threshold,
        training_pid_count=int(participant_means.size),
        training_context_cell_count=int(len(cells)),
        participant_cell_means=tuple((str(pid), float(value)) for pid, value in participant_means.items()),
    )


def _empty_c3_match_table(
    transform: C3DistanceTransform,
    *,
    time_column: str,
) -> pd.DataFrame:
    columns = [
        "pid", "recording_id", "n2_segment_id", "wake_segment_id",
        "n2_epoch_id", "wake_epoch_id", "n2_t_end", "wake_t_end",
        "n2_stage", "wake_stage", "distance", "outer_fold_id",
        "outer_training_pids", "chart_columns",
    ]
    for column in (*transform.chart.columns, time_column):
        columns.extend((f"n2_scaled__{column}", f"wake_scaled__{column}"))
    return pd.DataFrame({column: pd.Series(dtype="object") for column in columns})


def match_c3_origins(
    evaluation_rows: pd.DataFrame,
    transform: C3DistanceTransform,
    caliper: C3Caliper,
    *,
    pid_col: str = "pid",
    recording_col: str = "recording_id",
    segment_col: str = "segment_id",
    stage_col: str = "stage",
    epoch_col: str = "epoch_id",
    time_col: str | None = None,
    stage_pure_col: str = "stage_window_pure",
    stage_conflict_col: str | None = "stage_conflict",
    valid_col: str = "coordinate_qc_valid",
    support_col: str = "source_support_eligible",
    fold_id: int | None = None,
) -> pd.DataFrame:
    """Greedy one-to-one N2/Wake matching on current chart and recording time.

    Future chart columns, future labels and outcomes are neither required nor
    accessed. Matching is confined to a single apply PID and recording.
    """
    if not np.isfinite(caliper.threshold) or caliper.threshold < 0:
        raise ValueError("C3 caliper threshold must be finite and nonnegative")
    if fold_id is not None and (
        isinstance(fold_id, (bool, np.bool_))
        or not isinstance(fold_id, (int, np.integer))
        or int(fold_id) not in range(OUTER_FOLDS)
    ):
        raise ValueError(f"fold_id must be None or an integer in 0..{OUTER_FOLDS - 1}")
    fold_id = int(fold_id) if fold_id is not None else None
    effective_time_col = time_col or transform.time_column
    _require_columns(evaluation_rows, [pid_col], "C3 evaluation PID roster")
    if evaluation_rows[pid_col].isna().any():
        raise ValueError("C3 evaluation PID roster must be complete")
    overlap = set(evaluation_rows[pid_col].astype(str)) & set(transform.training_pids)
    if overlap:
        raise ValueError(f"C3 evaluation PIDs overlap outer-training PIDs: {sorted(overlap)}")
    candidates, scaled = _prepare_c3_current_rows(
        evaluation_rows, transform,
        pid_col=pid_col, recording_col=recording_col, segment_col=segment_col,
        stage_col=stage_col, epoch_col=epoch_col, time_col=effective_time_col,
        stage_pure_col=stage_pure_col, stage_conflict_col=stage_conflict_col,
        valid_col=valid_col, support_col=support_col,
    )
    if candidates.empty:
        return _empty_c3_match_table(transform, time_column=effective_time_col)
    candidates = candidates.copy()
    candidates["__candidate_pos"] = np.arange(len(candidates), dtype=int)
    candidates["__scaled"] = list(scaled)
    output: list[dict[str, Any]] = []
    for (pid, recording), group in candidates.groupby([pid_col, recording_col], sort=True):
        n2 = group.loc[group["__stage"] == "N2"]
        wake = group.loc[group["__stage"] == "Wake"]
        if n2.empty or wake.empty:
            continue
        edges: list[tuple[tuple[Any, ...], int, int, float]] = []
        for n2_index, n2_row in n2.iterrows():
            n2_scaled = scaled[int(n2_row["__candidate_pos"])]
            wake_scaled = np.vstack([
                scaled[int(row["__candidate_pos"])] for _, row in wake.iterrows()
            ])
            distances = np.linalg.norm(wake_scaled - n2_scaled[None, :], axis=1)
            for (wake_index, wake_row), distance in zip(wake.iterrows(), distances):
                value = float(distance)
                if value <= caliper.threshold:
                    key = (
                        value,
                        float(n2_row["__t_end"]),
                        float(wake_row["__t_end"]),
                        int(n2_row["__epoch"]),
                        int(wake_row["__epoch"]),
                    )
                    edges.append((key, int(n2_index), int(wake_index), value))
        edges.sort(key=lambda edge: edge[0])
        used_n2: set[int] = set()
        used_wake: set[int] = set()
        for _, n2_index, wake_index, distance in edges:
            if n2_index in used_n2 or wake_index in used_wake:
                continue
            n2_row = candidates.loc[n2_index]
            wake_row = candidates.loc[wake_index]
            item: dict[str, Any] = {
                "pid": pid,
                "recording_id": recording,
                "n2_segment_id": n2_row[segment_col],
                "wake_segment_id": wake_row[segment_col],
                "n2_epoch_id": int(n2_row["__epoch"]),
                "wake_epoch_id": int(wake_row["__epoch"]),
                "n2_t_end": float(n2_row["__t_end"]),
                "wake_t_end": float(wake_row["__t_end"]),
                "n2_stage": "N2",
                "wake_stage": "Wake",
                "distance": distance,
                "outer_fold_id": fold_id,
                "outer_training_pids": transform.training_pids,
                "chart_columns": transform.chart.columns,
            }
            n2_scaled = scaled[int(n2_row["__candidate_pos"])]
            wake_scaled = scaled[int(wake_row["__candidate_pos"])]
            for column, n2_value, wake_value in zip(
                [*transform.chart.columns, effective_time_col], n2_scaled, wake_scaled
            ):
                item[f"n2_scaled__{column}"] = float(n2_value)
                item[f"wake_scaled__{column}"] = float(wake_value)
            output.append(item)
            used_n2.add(n2_index)
            used_wake.add(wake_index)
    if not output:
        return _empty_c3_match_table(transform, time_column=effective_time_col)
    return pd.DataFrame(output)


def score_c3_matched_displacements(
    matched_pairs: pd.DataFrame,
    evaluation_rows: pd.DataFrame,
    transform: C3DistanceTransform,
    *,
    horizon_lag: int,
    pid_col: str = "pid",
    recording_col: str = "recording_id",
    segment_col: str = "segment_id",
    epoch_col: str = "epoch_id",
    time_col: str = "t_end",
    valid_col: str = "coordinate_qc_valid",
    support_col: str = "source_support_eligible",
) -> pd.DataFrame:
    """Attach future displacements after matching, with gap-safe row-lag checks.

    This function never rematches or changes the pair assignment. It requires
    the origin, every intervening row and target to have finite, QC-valid,
    source-supported coordinates in one verified contiguous segment.
    """
    horizon_lag = _registered_lag(horizon_lag)
    pair_columns = [
        "pid", "recording_id", "n2_segment_id", "wake_segment_id",
        "n2_epoch_id", "wake_epoch_id",
    ]
    _require_columns(matched_pairs, pair_columns, "C3 matched origins")
    if matched_pairs.empty:
        result = matched_pairs.copy()
        result["outcome_status"] = pd.Series(dtype="object")
        result["horizon_lag"] = pd.Series(dtype="int64")
        result["n2_actual_horizon_seconds"] = pd.Series(dtype="float64")
        result["wake_actual_horizon_seconds"] = pd.Series(dtype="float64")
        for column in transform.chart.columns:
            result[f"displacement_difference__{column}"] = pd.Series(dtype="float64")
        return result
    _require_columns(
        evaluation_rows,
        [pid_col, recording_col, segment_col, epoch_col, time_col, valid_col, support_col, *transform.chart.columns],
        "C3 outcome chart rows",
    )
    if evaluation_rows[[pid_col, recording_col, segment_col]].isna().any().any():
        raise EstimatorUnavailableError("C3 outcome rows have missing PID, recording or segment identity")
    overlap = set(evaluation_rows[pid_col].astype(str)) & set(transform.training_pids)
    if overlap:
        raise ValueError(f"C3 outcome PIDs overlap outer-training PIDs: {sorted(overlap)}")

    work = evaluation_rows.copy().reset_index(drop=True)
    work["__epoch"] = _exact_epoch_ids(work[epoch_col], column=epoch_col)
    work["__time"] = pd.to_numeric(work[time_col], errors="coerce")
    work["__valid"] = _validity_mask(work[valid_col], column=valid_col)
    work["__support"] = _validity_mask(work[support_col], column=support_col)
    chart_values = work.loc[:, transform.chart.columns].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if work.duplicated([pid_col, recording_col, segment_col, "__epoch"]).any():
        raise EstimatorUnavailableError("C3 outcome epoch identities must be unique within each segment")

    # Keyed only by present/past origin identity. Stage labels are deliberately
    # not read here; the stage contrast was fixed by matching at forecast origin.
    displacement_lookup: dict[tuple[str, str, str, int], tuple[np.ndarray, float]] = {}
    for (pid, recording, segment), group in work.groupby(
        [pid_col, recording_col, segment_col], sort=False, dropna=False
    ):
        group = group.sort_values("__epoch", kind="stable")
        positions = group.index.to_numpy(dtype=int)
        epochs = group["__epoch"].to_numpy(dtype=np.int64)
        for origin_local in range(len(group)):
            target_local = origin_local + horizon_lag
            if target_local >= len(group):
                continue
            interval_positions = positions[origin_local:target_local + 1]
            interval_epochs = epochs[origin_local:target_local + 1]
            if (
                np.any(np.diff(interval_epochs) != 1)
                or not work.loc[interval_positions, "__valid"].all()
                or not work.loc[interval_positions, "__support"].all()
            ):
                continue
            interval_values = chart_values[interval_positions]
            interval_times = work.loc[interval_positions, "__time"].to_numpy(dtype=float)
            if (
                not np.isfinite(interval_values).all()
                or not np.isfinite(interval_times).all()
                or np.any(np.diff(interval_times) <= 0)
            ):
                continue
            origin = transform.chart.apply(interval_values[[0]])[0]
            target = transform.chart.apply(interval_values[-1:])[0]
            key = (str(pid), str(recording), str(segment), int(epochs[origin_local]))
            displacement_lookup[key] = (target - origin, float(interval_times[-1] - interval_times[0]))

    result = matched_pairs.copy().reset_index(drop=True)
    statuses: list[str] = []
    n2_horizons: list[float] = []
    wake_horizons: list[float] = []
    coordinate_differences: dict[str, list[float]] = {
        column: [] for column in transform.chart.columns
    }
    for _, pair in result.iterrows():
        pid = str(pair["pid"])
        recording = str(pair["recording_id"])
        n2_key = (pid, recording, str(pair["n2_segment_id"]), int(pair["n2_epoch_id"]))
        wake_key = (pid, recording, str(pair["wake_segment_id"]), int(pair["wake_epoch_id"]))
        if n2_key not in displacement_lookup or wake_key not in displacement_lookup:
            statuses.append("NO_VALID_CONTIGUOUS_TARGET")
            n2_horizons.append(float("nan"))
            wake_horizons.append(float("nan"))
            for column in transform.chart.columns:
                coordinate_differences[column].append(float("nan"))
            continue
        n2_displacement, n2_horizon = displacement_lookup[n2_key]
        wake_displacement, wake_horizon = displacement_lookup[wake_key]
        statuses.append("AVAILABLE")
        n2_horizons.append(n2_horizon)
        wake_horizons.append(wake_horizon)
        for index, column in enumerate(transform.chart.columns):
            coordinate_differences[column].append(float(n2_displacement[index] - wake_displacement[index]))

    result["outcome_status"] = statuses
    result["horizon_lag"] = int(horizon_lag)
    result["n2_actual_horizon_seconds"] = n2_horizons
    result["wake_actual_horizon_seconds"] = wake_horizons
    for column, values in coordinate_differences.items():
        result[f"displacement_difference__{column}"] = values
    return result


def _c3_pair_identity_digest(pairs: pd.DataFrame) -> str:
    identity_columns = [
        "pid", "recording_id", "n2_segment_id", "wake_segment_id",
        "n2_epoch_id", "wake_epoch_id",
    ]
    _require_columns(pairs, identity_columns, "C3 matched pair identities")
    if pairs[identity_columns].isna().any().any():
        raise EstimatorUnavailableError("C3 matched pair identities must be complete")
    n2_epochs = _exact_epoch_ids(pairs["n2_epoch_id"], column="n2_epoch_id")
    wake_epochs = _exact_epoch_ids(pairs["wake_epoch_id"], column="wake_epoch_id")
    identities = []
    for row, n2_epoch, wake_epoch in zip(
        pairs[identity_columns].itertuples(index=False, name="PairIdentity"), n2_epochs, wake_epochs
    ):
        identities.append((
            str(row.pid), str(row.recording_id), str(row.n2_segment_id),
            str(row.wake_segment_id), int(n2_epoch), int(wake_epoch),
        ))
    if len(set(identities)) != len(identities):
        raise EstimatorUnavailableError("duplicate C3 matched pair identity")
    identities.sort()
    canonical = json.dumps(identities, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _c3_frame_content_digest(frame: pd.DataFrame) -> str:
    """Hash ordered table schema and values to detect post-assembly mutation."""
    header = {
        "columns": [str(column) for column in frame.columns],
        "dtypes": [str(dtype) for dtype in frame.dtypes],
        "row_count": int(len(frame)),
    }
    content = pd.util.hash_pandas_object(frame, index=False, categorize=True).to_numpy(dtype=np.uint64)
    digest = hashlib.sha256(
        json.dumps(header, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    digest.update(content.tobytes())
    return digest.hexdigest()


def _c3_matched_origin_digest(frame: pd.DataFrame) -> str:
    """Bind only forecast-origin match data; exclude every post-origin outcome."""
    fixed_columns = [
        "pid", "recording_id", "n2_segment_id", "wake_segment_id",
        "n2_epoch_id", "wake_epoch_id", "n2_t_end", "wake_t_end",
        "n2_stage", "wake_stage", "distance", "outer_fold_id",
        "outer_training_pids", "chart_columns",
    ]
    scaled_columns = [
        column for column in frame.columns
        if str(column).startswith(("n2_scaled__", "wake_scaled__"))
    ]
    selected = [column for column in frame.columns if column in fixed_columns or column in scaled_columns]
    _require_columns(frame, fixed_columns, "C3 matched-origin content")
    if not scaled_columns:
        raise ValueError("C3 matched-origin content omits the origin chart/time coordinates")
    return _c3_frame_content_digest(frame.loc[:, selected])


def _validate_c3_oof_result(
    out_of_fold: C3OutOfFoldResult,
    *,
    verify_scored_content: bool = True,
) -> None:
    """Recheck public/mutable OOF containers before any C3 gate or summary."""
    if not isinstance(out_of_fold, C3OutOfFoldResult):
        raise TypeError("C3 processing requires a validated five-fold C3OutOfFoldResult")
    _validate_grouped_pid_manifest(out_of_fold.split_manifest)
    horizon_lag = _registered_lag(out_of_fold.horizon_lag)
    columns = tuple(str(column) for column in out_of_fold.chart_columns)
    if not columns or len(set(columns)) != len(columns) or columns != out_of_fold.chart_columns:
        raise ValueError("C3 out-of-fold result must retain one exact nonempty chart representation")
    if out_of_fold.assembled_fold_ids != tuple(range(OUTER_FOLDS)):
        raise ValueError("C3 result does not record completion of all five expected folds")
    if (
        len(out_of_fold.fold_match_counts) != OUTER_FOLDS
        or len(out_of_fold.fold_scored_counts) != OUTER_FOLDS
        or any(not isinstance(count, int) or isinstance(count, bool) or count < 0
               for count in (*out_of_fold.fold_match_counts, *out_of_fold.fold_scored_counts))
    ):
        raise ValueError("C3 result fold completion counts are invalid")
    matched_pairs = out_of_fold.matched_pairs
    scored_pairs = out_of_fold.scored_pairs
    expected_by_fold = {
        fold.fold_id: set(fold.evaluation_pids) for fold in out_of_fold.split_manifest.folds
    }
    for frame, name in ((matched_pairs, "matched"), (scored_pairs, "scored")):
        _require_columns(
            frame,
            ["pid", "outer_fold_id", "outer_training_pids", "chart_columns"],
            f"C3 {name} out-of-fold table",
        )
        if frame["pid"].isna().any():
            raise ValueError(f"C3 {name} out-of-fold PID identities cannot be missing")
        if frame.empty:
            continue
        fold_values = pd.to_numeric(frame["outer_fold_id"], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(fold_values).all() or np.any(fold_values != np.floor(fold_values)):
            raise ValueError(f"C3 {name} out-of-fold rows have invalid fold IDs")
        for row_position, (_, row) in enumerate(frame.iterrows()):
            fold_id = int(fold_values[row_position])
            if fold_id not in expected_by_fold:
                raise ValueError(f"C3 {name} out-of-fold row names an unknown GroupKFold fold")
            manifest_fold = out_of_fold.split_manifest.folds[fold_id]
            if str(row["pid"]) not in expected_by_fold[fold_id]:
                raise ValueError(f"C3 {name} out-of-fold PID is outside its manifest evaluation roster")
            try:
                training_pids = tuple(str(pid) for pid in row["outer_training_pids"])
                row_columns = tuple(str(column) for column in row["chart_columns"])
            except TypeError as exc:
                raise ValueError(f"C3 {name} out-of-fold provenance metadata is malformed") from exc
            if training_pids != manifest_fold.training_pids:
                raise ValueError(f"C3 {name} out-of-fold training roster differs from its manifest")
            if row_columns != columns:
                raise ValueError(f"C3 {name} out-of-fold representation differs from its manifest binding")
    for frame, name, counts in (
        (matched_pairs, "matched", out_of_fold.fold_match_counts),
        (scored_pairs, "scored", out_of_fold.fold_scored_counts),
    ):
        if "outer_fold_id" not in frame:
            raise ValueError(f"C3 {name} out-of-fold table omits fold-completion metadata")
        fold_values = pd.to_numeric(frame["outer_fold_id"], errors="coerce").to_numpy(dtype=float)
        observed_counts = tuple(int(np.count_nonzero(fold_values == fold_id)) for fold_id in range(OUTER_FOLDS))
        if observed_counts != counts:
            raise ValueError(f"C3 {name} rows do not match the recorded five-fold completion counts")
    if _c3_matched_origin_digest(matched_pairs) != out_of_fold.matched_content_sha256:
        raise ValueError("C3 matched table content changed after validated assembly")
    if verify_scored_content and _c3_frame_content_digest(scored_pairs) != out_of_fold.scored_content_sha256:
        raise ValueError("C3 scored table content changed after validated assembly")
    if set(matched_pairs["pid"].astype(str)) != set(scored_pairs["pid"].astype(str)):
        raise ValueError("C3 out-of-fold matched/scored PID rosters differ")
    if _c3_pair_identity_digest(matched_pairs) != _c3_pair_identity_digest(scored_pairs):
        raise ValueError("C3 out-of-fold scored rows changed the matched-origin identity set")
    _require_columns(scored_pairs, ["horizon_lag"], "C3 scored out-of-fold rows")
    if not scored_pairs.empty:
        lags = pd.to_numeric(scored_pairs["horizon_lag"], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(lags).all() or not np.all(lags == horizon_lag):
            raise ValueError("C3 scored out-of-fold horizon differs from its declared horizon")


def _validate_c3_matched_oof_result(
    out_of_fold: C3MatchedOriginOutOfFold | C3OutOfFoldResult,
) -> None:
    """Validate the pre-outcome five-fold match object used by the overlap gate."""
    if isinstance(out_of_fold, C3OutOfFoldResult):
        _validate_c3_oof_result(out_of_fold, verify_scored_content=False)
        return
    if not isinstance(out_of_fold, C3MatchedOriginOutOfFold):
        raise TypeError("C3 overlap gate requires a validated five-fold matched-origin result")
    _validate_grouped_pid_manifest(out_of_fold.split_manifest)
    horizon_lag = _registered_lag(out_of_fold.horizon_lag)
    columns = tuple(str(column) for column in out_of_fold.chart_columns)
    if not columns or len(set(columns)) != len(columns) or columns != out_of_fold.chart_columns:
        raise ValueError("C3 matched-origin result must retain one exact nonempty chart representation")
    if out_of_fold.assembled_fold_ids != tuple(range(OUTER_FOLDS)):
        raise ValueError("C3 result does not record completion of all five expected folds")
    if (
        len(out_of_fold.fold_match_counts) != OUTER_FOLDS
        or any(not isinstance(count, int) or isinstance(count, bool) or count < 0
               for count in out_of_fold.fold_match_counts)
    ):
        raise ValueError("C3 matched-origin fold completion counts are invalid")
    if tuple(fold.fold_id for fold in out_of_fold.split_manifest.folds) != tuple(range(OUTER_FOLDS)):
        raise ValueError("C3 split manifest fold IDs must be exactly 0..4 in GroupKFold order")

    matched = out_of_fold.matched_pairs
    expected_by_fold = {
        fold.fold_id: set(fold.evaluation_pids) for fold in out_of_fold.split_manifest.folds
    }
    _require_columns(
        matched,
        ["pid", "outer_fold_id", "outer_training_pids", "chart_columns"],
        "C3 matched-origin out-of-fold table",
    )
    if matched["pid"].isna().any():
        raise ValueError("C3 matched-origin out-of-fold PID identities cannot be missing")
    seen_pid_folds: dict[str, int] = {}
    fold_values = pd.to_numeric(matched["outer_fold_id"], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(fold_values).all() or np.any(fold_values != np.floor(fold_values)):
        raise ValueError("C3 matched-origin out-of-fold rows have invalid fold IDs")
    for row_position, (_, row) in enumerate(matched.iterrows()):
        fold_id = int(fold_values[row_position])
        if fold_id not in expected_by_fold:
            raise ValueError("C3 matched-origin out-of-fold row names an unknown GroupKFold fold")
        manifest_fold = out_of_fold.split_manifest.folds[fold_id]
        pid = str(row["pid"])
        if pid not in expected_by_fold[fold_id]:
            raise ValueError("C3 matched-origin PID is outside its manifest evaluation roster")
        if pid in seen_pid_folds and seen_pid_folds[pid] != fold_id:
            raise ValueError("C3 evaluation PIDs occur in multiple outer folds")
        seen_pid_folds[pid] = fold_id
        try:
            training_pids = tuple(str(value) for value in row["outer_training_pids"])
            row_columns = tuple(str(value) for value in row["chart_columns"])
        except TypeError as exc:
            raise ValueError("C3 matched-origin fold provenance metadata is malformed") from exc
        if training_pids != manifest_fold.training_pids:
            raise ValueError("C3 matched-origin training roster differs from its manifest")
        if row_columns != columns:
            raise ValueError("C3 matched-origin representation differs from its manifest binding")

    observed_counts = tuple(
        int(np.count_nonzero(fold_values == fold_id)) for fold_id in range(OUTER_FOLDS)
    )
    if observed_counts != out_of_fold.fold_match_counts:
        raise ValueError("C3 matched-origin rows do not match the recorded five-fold completion counts")
    if _c3_matched_origin_digest(matched) != out_of_fold.matched_content_sha256:
        raise ValueError("C3 matched table content changed after validated assembly")
    _c3_pair_identity_digest(matched)


def combine_c3_matched_origins_out_of_fold(
    matched_by_fold: Sequence[pd.DataFrame],
    *,
    fold_ids: Sequence[int],
    split_manifest: GroupedPIDSplitManifest,
    chart_columns: Sequence[str],
) -> C3MatchedOriginOutOfFold:
    """Assemble only pre-outcome C3 matches across the frozen five PID folds."""
    _validate_grouped_pid_manifest(split_manifest)
    columns = tuple(str(column) for column in chart_columns)
    if not columns or len(set(columns)) != len(columns):
        raise ValueError("C3 chart_columns must be nonempty and unique")
    if (
        len(matched_by_fold) != OUTER_FOLDS
        or len(fold_ids) != OUTER_FOLDS
        or len(split_manifest.folds) != OUTER_FOLDS
    ):
        raise ValueError(f"C3 out-of-fold assembly requires all {OUTER_FOLDS} expected folds")
    if tuple(int(fold_id) for fold_id in fold_ids) != tuple(range(OUTER_FOLDS)):
        raise ValueError("C3 fold IDs must be supplied in deterministic GroupKFold order 0..4")
    if tuple(fold.fold_id for fold in split_manifest.folds) != tuple(range(OUTER_FOLDS)):
        raise ValueError("C3 split manifest fold IDs must be exactly 0..4 in GroupKFold order")

    seen_pids: set[str] = set()
    for fold_id, matched in zip(fold_ids, matched_by_fold):
        _require_columns(
            matched,
            ["pid", "outer_fold_id", "outer_training_pids", "chart_columns"],
            f"C3 matched fold {fold_id}",
        )
        pids = set(matched["pid"].astype(str))
        if not pids.issubset(set(split_manifest.folds[fold_id].evaluation_pids)):
            raise ValueError(f"C3 fold {fold_id} contains a matched PID outside its evaluation roster")
        if seen_pids & pids:
            raise ValueError("C3 evaluation PIDs occur in multiple outer folds")
        seen_pids.update(pids)

    result = C3MatchedOriginOutOfFold(
        matched_pairs=pd.concat(matched_by_fold, ignore_index=True, sort=False),
        split_manifest=split_manifest,
        horizon_lag=1,
        chart_columns=columns,
        assembled_fold_ids=tuple(int(fold_id) for fold_id in fold_ids),
        fold_match_counts=tuple(int(len(frame)) for frame in matched_by_fold),
        matched_content_sha256="",
    )
    result = replace(
        result,
        matched_content_sha256=_c3_matched_origin_digest(result.matched_pairs),
    )
    _validate_c3_matched_oof_result(result)
    return result


def combine_c3_out_of_fold(
    matched_by_fold: Sequence[pd.DataFrame],
    scored_by_fold: Sequence[pd.DataFrame],
    *,
    horizon_lag: int,
    fold_ids: Sequence[int],
    split_manifest: GroupedPIDSplitManifest,
    chart_columns: Sequence[str],
) -> C3OutOfFoldResult:
    """Validate and concatenate fold-local C3 matches and post-match outcomes.

    Exactly five fold tables are required and must bind to the deterministic
    GroupKFold manifest through fold ID, full training PID roster, and chart
    representation metadata. Participants without matches remain represented
    by the split manifest and are reported by the overlap gate.
    """
    _validate_grouped_pid_manifest(split_manifest)
    horizon_lag = _registered_lag(horizon_lag)
    columns = tuple(str(column) for column in chart_columns)
    if not columns or len(set(columns)) != len(columns):
        raise ValueError("C3 chart_columns must be nonempty and unique")
    if (
        len(matched_by_fold) != OUTER_FOLDS
        or len(scored_by_fold) != OUTER_FOLDS
        or len(fold_ids) != OUTER_FOLDS
        or len(split_manifest.folds) != OUTER_FOLDS
    ):
        raise ValueError(f"C3 out-of-fold assembly requires all {OUTER_FOLDS} expected folds")
    if tuple(int(fold_id) for fold_id in fold_ids) != tuple(range(OUTER_FOLDS)):
        raise ValueError("C3 fold IDs must be supplied in deterministic GroupKFold order 0..4")
    if tuple(fold.fold_id for fold in split_manifest.folds) != tuple(range(OUTER_FOLDS)):
        raise ValueError("C3 split manifest fold IDs must be exactly 0..4 in GroupKFold order")
    if not split_manifest.expected_pids or len(set(split_manifest.expected_pids)) != len(split_manifest.expected_pids):
        raise ValueError("C3 split manifest must contain a complete unique PID roster")
    seen_pids: set[str] = set()
    for fold_number, (matched, scored, fold_id) in enumerate(
        zip(matched_by_fold, scored_by_fold, fold_ids)
    ):
        manifest_fold = split_manifest.folds[fold_id]
        matched_pids = set(matched["pid"].astype(str)) if "pid" in matched else set()
        scored_pids = set(scored["pid"].astype(str)) if "pid" in scored else set()
        if matched_pids != scored_pids:
            raise ValueError(f"C3 fold {fold_number} match/outcome PID sets differ")
        if not matched_pids.issubset(set(manifest_fold.evaluation_pids)):
            raise ValueError(f"C3 fold {fold_number} contains a matched PID outside its manifest evaluation roster")
        overlap = seen_pids & matched_pids
        if overlap:
            raise ValueError(f"C3 evaluation PIDs occur in multiple outer folds: {sorted(overlap)}")
        seen_pids.update(matched_pids)
        metadata_columns = ["outer_fold_id", "outer_training_pids", "chart_columns"]
        _require_columns(matched, metadata_columns, f"C3 matched fold {fold_id}")
        _require_columns(scored, metadata_columns, f"C3 scored fold {fold_id}")
        for frame, name in ((matched, "matched"), (scored, "scored")):
            if frame.empty:
                continue
            row_fold_ids = pd.to_numeric(frame["outer_fold_id"], errors="coerce").to_numpy(dtype=float)
            if not np.isfinite(row_fold_ids).all() or not np.all(row_fold_ids == fold_id):
                raise ValueError(f"C3 {name} rows do not bind to GroupKFold fold {fold_id}")
            row_training_rosters = {
                tuple(str(pid) for pid in roster)
                for roster in frame["outer_training_pids"].tolist()
            }
            if row_training_rosters != {manifest_fold.training_pids}:
                raise ValueError(f"C3 {name} rows do not bind to the fold's full training PID roster")
            row_chart_columns = {
                tuple(str(column) for column in cols)
                for cols in frame["chart_columns"].tolist()
            }
            if row_chart_columns != {columns}:
                raise ValueError(f"C3 {name} rows mix chart representations within fold {fold_id}")
        if _c3_pair_identity_digest(matched) != _c3_pair_identity_digest(scored):
            raise ValueError(f"C3 fold {fold_number} scored outcomes changed the matched-origin identity set")
        if "horizon_lag" not in scored:
            raise ValueError(f"C3 fold {fold_number} scored outcomes omit the horizon identity")
        if not scored.empty:
            lags = pd.to_numeric(scored["horizon_lag"], errors="coerce").to_numpy(dtype=float)
            if not np.isfinite(lags).all() or not np.all(lags == horizon_lag):
                raise ValueError(f"C3 fold {fold_number} does not match requested h{horizon_lag}")
    result = C3OutOfFoldResult(
        matched_pairs=pd.concat(matched_by_fold, ignore_index=True, sort=False),
        scored_pairs=pd.concat(scored_by_fold, ignore_index=True, sort=False),
        split_manifest=split_manifest,
        horizon_lag=horizon_lag,
        chart_columns=columns,
        assembled_fold_ids=tuple(int(fold_id) for fold_id in fold_ids),
        fold_match_counts=tuple(int(len(frame)) for frame in matched_by_fold),
        fold_scored_counts=tuple(int(len(frame)) for frame in scored_by_fold),
        matched_content_sha256="",
        scored_content_sha256="",
    )
    result = replace(
        result,
        matched_content_sha256=_c3_matched_origin_digest(result.matched_pairs),
        scored_content_sha256=_c3_frame_content_digest(result.scored_pairs),
    )
    _validate_c3_oof_result(result)
    return result


def c3_overlap_gate(
    out_of_fold: C3MatchedOriginOutOfFold | C3OutOfFoldResult,
    *,
    time_col: str = "recording_relative_seconds",
    pid_col: str = "pid",
    recording_col: str = "recording_id",
    min_pids: int = MIN_REPORTING_PIDS,
    min_pairs_per_pid: int = C3_MIN_PAIRS_PER_PID_H1,
    max_abs_smd_iqr: float = C3_MAX_ABS_SMD_IQR,
) -> C3BalanceGate:
    """Apply C3's pre-outcome origin-overlap and current-state balance gate.

    This consumes matches only: no target coordinates, future stage, outcome,
    or future-support availability is used. Pair-count and SMD_IQR diagnostics
    therefore describe the matched origin set before future-support attrition.
    The validated five-fold split manifest supplies the full expected roster.
    """
    _validate_c3_matched_oof_result(out_of_fold)
    if out_of_fold.horizon_lag != 1:
        raise ValueError("the C3 overlap gate is fixed to the primary h1 matched-origin set")
    matched_pairs = out_of_fold.matched_pairs
    columns = out_of_fold.chart_columns
    expected = out_of_fold.split_manifest.expected_pids
    if min_pids != MIN_REPORTING_PIDS:
        raise ValueError("the C3 reporting floor is fixed at exactly 20 independent PIDs")
    if min_pairs_per_pid != C3_MIN_PAIRS_PER_PID_H1 or max_abs_smd_iqr != C3_MAX_ABS_SMD_IQR:
        raise ValueError("C3 support/balance thresholds are frozen at 10 pairs and |SMD_IQR| <= 0.10")
    if not expected or len(set(expected)) != len(expected):
        raise ValueError("C3 split manifest must contain a nonempty unique biological PID roster")
    identity_digest = _c3_pair_identity_digest(matched_pairs)
    if matched_pairs.empty:
        return C3BalanceGate(
            gate_status="INCONCLUSIVE",
            chart_columns=columns,
            split_manifest_sha256=out_of_fold.split_manifest.sha256,
            expected_pid_count=len(expected),
            pids_without_matches=expected,
            eligible_pid_count=0,
            qualifying_pid_count=0,
            pair_count=0,
            matched_pid_count=0,
            matched_pair_count=0,
            smd_iqr=(),
            reasons=("no_matched_origins",),
            matched_pair_digest=identity_digest,
            matched_content_sha256=out_of_fold.matched_content_sha256,
        )
    required = [pid_col, recording_col]
    required += [f"n2_scaled__{column}" for column in (*columns, time_col)]
    required += [f"wake_scaled__{column}" for column in (*columns, time_col)]
    _require_columns(matched_pairs, required, "C3 matched origins")
    counts = matched_pairs.groupby(pid_col, sort=True).size()
    matched_pids = set(counts.index.astype(str))
    unexpected_pids = matched_pids - set(expected)
    if unexpected_pids:
        raise ValueError(f"C3 matched PIDs are outside the expected cohort roster: {sorted(unexpected_pids)}")
    pids_without_matches = tuple(sorted(set(expected) - matched_pids))
    for stage in ("n2", "wake"):
        origin_identity = [pid_col, recording_col, f"{stage}_segment_id", f"{stage}_epoch_id"]
        if matched_pairs.duplicated(origin_identity).any():
            raise EstimatorUnavailableError(f"C3 {stage.upper()} forecast origins are not one-to-one within recording")
    qualifying = counts[counts >= min_pairs_per_pid]
    smd: dict[str, float] = {}
    for column in (*columns, time_col):
        difference = (
            pd.to_numeric(matched_pairs[f"n2_scaled__{column}"], errors="coerce")
            - pd.to_numeric(matched_pairs[f"wake_scaled__{column}"], errors="coerce")
        )
        if not np.isfinite(difference.to_numpy(dtype=float)).all():
            smd[column] = float("nan")
            continue
        rows = matched_pairs[[pid_col, recording_col]].copy()
        rows["difference"] = difference.to_numpy(dtype=float)
        recording_means = rows.groupby([pid_col, recording_col], sort=True)["difference"].mean()
        participant_means = recording_means.groupby(level=0, sort=True).mean()
        smd[column] = float(participant_means.mean())
    reasons: list[str] = []
    if len(qualifying) < min_pids:
        reasons.append("fewer_than_20_pids_with_at_least_10_h1_matched_pairs")
    if any(not np.isfinite(value) or abs(value) > max_abs_smd_iqr for value in smd.values()):
        reasons.append("one_or_more_current_state_or_time_balance_values_exceed_0.10_iqr")
    return C3BalanceGate(
        gate_status="OVERLAP_GATE_PASS" if not reasons else "INCONCLUSIVE",
        chart_columns=columns,
        split_manifest_sha256=out_of_fold.split_manifest.sha256,
        expected_pid_count=len(expected),
        pids_without_matches=pids_without_matches,
        eligible_pid_count=int(counts.size),
        qualifying_pid_count=int(qualifying.size),
        pair_count=int(len(matched_pairs)),
        matched_pid_count=int(counts.size),
        matched_pair_count=int(len(matched_pairs)),
        smd_iqr=tuple(smd.items()),
        reasons=tuple(reasons),
        matched_pair_digest=identity_digest,
        matched_content_sha256=out_of_fold.matched_content_sha256,
    )


def _c3_balance_gates_equivalent(left: C3BalanceGate, right: C3BalanceGate) -> bool:
    """Exact diagnostic comparison with NaN-aware equality for failed gates."""
    scalar_fields = (
        "gate_status", "chart_columns", "split_manifest_sha256", "expected_pid_count",
        "pids_without_matches", "eligible_pid_count", "qualifying_pid_count",
        "pair_count", "matched_pid_count", "matched_pair_count", "reasons",
        "matched_pair_digest", "matched_content_sha256",
    )
    if any(getattr(left, field) != getattr(right, field) for field in scalar_fields):
        return False
    if len(left.smd_iqr) != len(right.smd_iqr):
        return False
    for (left_name, left_value), (right_name, right_value) in zip(left.smd_iqr, right.smd_iqr):
        if left_name != right_name:
            return False
        if left_value == right_value:
            continue
        if not (np.isnan(left_value) and np.isnan(right_value)):
            return False
    return True


def summarize_c3_effect(
    out_of_fold: C3OutOfFoldResult,
    *,
    overlap_gate: C3BalanceGate,
    pid_col: str = "pid",
    recording_col: str = "recording_id",
) -> C3EffectSummary:
    """Summarize C3 only after a passing pre-outcome overlap/balance gate."""
    _validate_c3_oof_result(out_of_fold)
    scored_pairs = out_of_fold.scored_pairs
    columns = out_of_fold.chart_columns
    diff_columns = [f"displacement_difference__{column}" for column in columns]
    if not isinstance(overlap_gate, C3BalanceGate):
        raise TypeError("C3 effect summarization requires a validated C3BalanceGate")
    recomputed_gate = c3_overlap_gate(out_of_fold)
    if not _c3_balance_gates_equivalent(overlap_gate, recomputed_gate):
        raise ValueError("C3 overlap gate status/diagnostics do not match the assembled matched origins")
    if overlap_gate.chart_columns != columns:
        raise ValueError("C3 overlap gate representation differs from the requested effect representation")
    if overlap_gate.split_manifest_sha256 != out_of_fold.split_manifest.sha256:
        raise ValueError("C3 overlap gate and effect rows have different GroupKFold split manifests")
    if overlap_gate.matched_content_sha256 != out_of_fold.matched_content_sha256:
        raise ValueError("C3 overlap gate and matched-origin content differ")
    if out_of_fold.horizon_lag not in {1, 2, 4}:
        raise ValueError("C3 effect summary has an unregistered forecast horizon")
    if scored_pairs.empty:
        if overlap_gate.matched_pair_digest != _c3_pair_identity_digest(scored_pairs):
            raise ValueError("C3 effect table does not correspond to the gated matched origins")
        return C3EffectSummary("INCONCLUSIVE", 0, 0, overlap_gate.pair_count, None, None)
    _require_columns(
        scored_pairs,
        [pid_col, recording_col, "outcome_status", "horizon_lag", *diff_columns],
        "C3 scored pairs",
    )
    if _c3_pair_identity_digest(scored_pairs) != overlap_gate.matched_pair_digest:
        raise ValueError("C3 effect table does not correspond to the gated matched origins")
    lags = pd.to_numeric(scored_pairs["horizon_lag"], errors="coerce").to_numpy(dtype=float)
    if (
        not np.isfinite(lags).all()
        or len(np.unique(lags)) != 1
        or float(lags[0]) not in {1.0, 2.0, 4.0}
    ):
        raise ValueError("C3 effect summarization requires exactly one registered horizon per call")
    if scored_pairs["outcome_status"].isna().any():
        raise EstimatorUnavailableError("C3 outcome availability status cannot be missing")
    allowed_status = {"AVAILABLE", "NO_VALID_CONTIGUOUS_TARGET"}
    unexpected_status = set(scored_pairs["outcome_status"].dropna().astype(str)) - allowed_status
    if unexpected_status:
        raise ValueError(f"unknown C3 outcome availability statuses: {sorted(unexpected_status)}")
    eligible = scored_pairs.loc[scored_pairs["outcome_status"] == "AVAILABLE"].copy()
    values = eligible[diff_columns].apply(pd.to_numeric, errors="coerce") if not eligible.empty else pd.DataFrame(columns=diff_columns)
    finite = np.isfinite(values.to_numpy(dtype=float)).all(axis=1) if not eligible.empty else np.zeros(0, dtype=bool)
    eligible = eligible.loc[finite].copy()
    values = values.loc[finite].copy()
    n_pids = int(eligible[pid_col].nunique()) if not eligible.empty else 0
    if overlap_gate.gate_status != "OVERLAP_GATE_PASS" or n_pids < MIN_REPORTING_PIDS:
        return C3EffectSummary(
            "INCONCLUSIVE", n_pids, int(len(eligible)), overlap_gate.pair_count, None, None
        )
    for column, diff_column in zip(columns, diff_columns):
        eligible[diff_column] = values[diff_column].to_numpy(dtype=float)
    recording_means = eligible.groupby([pid_col, recording_col], sort=True)[diff_columns].mean()
    participant_means = recording_means.groupby(level=0, sort=True).mean()
    means = tuple(
        (column, float(participant_means[f"displacement_difference__{column}"].mean()))
        for column in columns
    )
    intervals = tuple(
        (
            column,
            participant_cluster_bootstrap_interval(
                participant_means[f"displacement_difference__{column}"].to_numpy(dtype=float)
            ),
        )
        for column in columns
    )
    return C3EffectSummary(
        "DESCRIPTIVE_SCORE_AVAILABLE",
        int(len(participant_means)),
        int(len(eligible)),
        overlap_gate.pair_count,
        means,
        intervals,
    )


def circular_shift_stage_labels(
    rows: pd.DataFrame,
    *,
    stage_col: str = "stage",
    pid_col: str = "pid",
    recording_col: str = "recording_id",
    segment_col: str = "segment_id",
    epoch_col: str = "epoch_id",
    shift_rows: int = C3_STAGE_SHIFT_ROWS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Circularly shift labels inside segments only; short segments stay unchanged.

    A segment is feasible only when the fixed shift is at least eight rows and
    is not a multiple of its length (which would be the identity operation).
    No shift crosses a recording or verified contiguous-segment boundary.
    """
    if isinstance(shift_rows, (bool, np.bool_)) or not isinstance(shift_rows, (int, np.integer)) or shift_rows < C3_STAGE_SHIFT_ROWS:
        raise ValueError("the C3 stage-label diagnostic shift is fixed at >=8 rows")
    shift_rows = int(shift_rows)
    _require_columns(rows, [stage_col, pid_col, recording_col, segment_col, epoch_col], "stage-shift rows")
    if rows[[pid_col, recording_col, segment_col]].isna().any().any():
        raise EstimatorUnavailableError("stage shift requires complete PID/recording/segment identities")
    work = rows.copy().reset_index(drop=True)
    work["__epoch"] = _exact_epoch_ids(work[epoch_col], column=epoch_col)
    work["__stage_shifted"] = work[stage_col].copy()
    audit: list[dict[str, Any]] = []
    for (pid, recording, segment), group in work.groupby(
        [pid_col, recording_col, segment_col], sort=True, dropna=False
    ):
        group = group.sort_values("__epoch", kind="stable")
        epochs = group["__epoch"].to_numpy(dtype=np.int64)
        if len(np.unique(epochs)) != len(epochs):
            raise EstimatorUnavailableError("duplicate epoch identity in a stage-shift segment")
        if len(epochs) > 1 and np.any(np.diff(epochs) != 1):
            raise EstimatorUnavailableError(
                "stage-shift input segment contains an epoch gap; split/verify contiguous segments first"
            )
        feasible = len(group) > shift_rows and shift_rows % len(group) != 0
        if feasible:
            positions = group.index.to_numpy(dtype=int)
            labels = group[stage_col].to_numpy(copy=True)
            work.loc[positions, "__stage_shifted"] = np.roll(labels, shift_rows)
        audit.append({
            "pid": pid,
            "recording_id": recording,
            "segment_id": segment,
            "row_count": int(len(group)),
            "shift_rows": int(shift_rows),
            "feasible": bool(feasible),
        })
    work[stage_col] = work["__stage_shifted"]
    work = work.drop(columns=["__epoch", "__stage_shifted"])
    return work, pd.DataFrame(audit)
