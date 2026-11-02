"""Synthetic-only regression tests for the preregistered continuous C1/C3 estimators."""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from nmd_analysis.continuous_c123_estimators import (
    C3Caliper,
    _participant_balanced_c1_reduction,
    _grouped_pid_manifest_payload,
    build_c1_examples,
    build_grouped_pid_manifest,
    circular_shift_stage_labels,
    c3_overlap_gate,
    combine_c3_out_of_fold,
    combine_c3_matched_origins_out_of_fold,
    evaluate_c1_fold,
    fit_c3_caliper,
    fit_c3_distance_transform,
    fit_participant_balanced_iqr,
    grouped_pid_splits,
    match_c3_origins,
    participant_cluster_bootstrap_interval,
    score_c3_matched_displacements,
    summarize_c1_out_of_fold,
    summarize_c3_effect,
)


def _chart_row(
    pid: str,
    recording: str,
    segment: str,
    epoch: int,
    x: float,
    y: float,
    *,
    stage: str = "N2",
    relative_time: float | None = None,
    end_time: float | None = None,
    valid: bool = True,
    supported: bool = True,
    pure: bool = True,
    conflict: bool = False,
) -> dict[str, object]:
    return {
        "pid": pid,
        "recording_id": recording,
        "segment_id": segment,
        "epoch_id": epoch,
        "t_end": float(end_time if end_time is not None else 30 * (epoch + 1)),
        "recording_relative_seconds": float(relative_time if relative_time is not None else 30 * epoch),
        "coordinate_qc_valid": valid,
        "source_support_eligible": supported,
        "stage": stage,
        "stage_window_pure": pure,
        "stage_conflict": conflict,
        "x": float(x),
        "y": float(y),
    }


def _c1_series(pid: str, pid_index: int, *, recording: str, n: int = 32) -> list[dict[str, object]]:
    rows = []
    for epoch in range(n):
        phase = epoch / 5.0
        rows.append(_chart_row(
            pid, recording, "seg-0", epoch,
            x=pid_index * 2.0 + epoch * 0.13,
            y=pid_index * 0.7 + np.sin(phase) + epoch * epoch * 0.002,
            end_time=30.0 * (epoch + 1),
        ))
    return rows


def test_participant_balanced_iqr_uses_pid_recording_medians_and_support():
    rows = pd.DataFrame([
        _chart_row("p1", "a", "s", 0, 0, 0),
        _chart_row("p1", "a", "s", 1, 2, 2),
        _chart_row("p1", "b", "s", 0, 4, 4),
        _chart_row("p1", "b", "s", 1, 6, 6),
        _chart_row("p2", "c", "s", 0, 10, 10),
        _chart_row("p2", "c", "s", 1, 12, 12),
        _chart_row("p3", "d", "s", 0, 20, 20),
        _chart_row("p3", "d", "s", 1, 22, 22),
        _chart_row("p1", "a", "s", 2, 999, 999, supported=False),
    ])
    fitted = fit_participant_balanced_iqr(rows, ["x", "y"])
    assert fitted.training_pids == ("p1", "p2", "p3")
    assert fitted.center == pytest.approx([11.0, 11.0])
    assert fitted.scale == pytest.approx([9.0, 9.0])
    assert fitted.finite_pid_counts == (3, 3)


def test_grouped_splits_never_separate_repeated_recordings_for_a_pid():
    rows = pd.DataFrame([
        {"pid": pid, "recording_id": recording, "value": 1.0}
        for pid in range(12)
        for recording in ("night-1", "night-2")
    ])
    for train, test in grouped_pid_splits(rows):
        assert set(train.pid).isdisjoint(set(test.pid))
        assert train.groupby("pid").recording_id.nunique().max() == 2
        assert test.groupby("pid").recording_id.nunique().max() == 2


def test_c1_examples_respect_gap_segment_qc_and_raw_support():
    rows = []
    for epoch in [0, 1, 2, 3, 6, 7, 8, 9]:
        rows.append(_chart_row("p", "r", "same-segment", epoch, epoch, epoch * 2))
    # Distinct contiguous segments cannot supply each other's histories.
    for epoch in range(4):
        rows.append(_chart_row("p", "r2", "first", epoch, epoch, epoch * 2))
    for epoch in range(4):
        rows.append(_chart_row("p", "r2", "second", epoch + 10, epoch, epoch * 2))
    rows[9]["coordinate_qc_valid"] = False
    rows[13]["source_support_eligible"] = False
    frame = pd.DataFrame(rows)
    frame.index = pd.Index([f"row-{i}" for i in range(len(frame))], name="nonstandard-index")
    examples = build_c1_examples(frame, ["x", "y"], horizon_lag=1)
    origins = set(zip(examples.metadata.recording_id, examples.metadata.origin_epoch_id))
    assert origins == {("r", 2), ("r", 8)}


def test_c1_shifted_history_is_past_only_and_requires_at_least_five_rows():
    frame = pd.DataFrame(_c1_series("p", 1, recording="r", n=24))
    with pytest.raises(ValueError):
        build_c1_examples(frame, ["x", "y"], horizon_lag=1, history_shift_rows=4)
    shifted = build_c1_examples(frame, ["x", "y"], horizon_lag=1, history_shift_rows=5)
    first = shifted.metadata.iloc[0]
    origin = int(first.origin_epoch_id)
    original = frame.set_index("epoch_id")
    assert shifted.history[0, :2] == pytest.approx(original.loc[origin, ["x", "y"]].to_numpy(dtype=float))
    assert shifted.history[0, 2:4] == pytest.approx(original.loc[origin - 6, ["x", "y"]].to_numpy(dtype=float))
    assert shifted.history[0, 4:6] == pytest.approx(original.loc[origin - 7, ["x", "y"]].to_numpy(dtype=float))
    with pytest.raises(ValueError):
        build_c1_examples(frame, ["x", "y"], horizon_lag=1.0)


def test_c1_participant_reduction_weights_recordings_then_pids_equally():
    rows = pd.DataFrame([
        {"pid": "p1", "recording_id": "a", "mse_m0": 2.0, "mse_m1": 0.0},
        {"pid": "p1", "recording_id": "a", "mse_m0": 4.0, "mse_m1": 0.0},
        {"pid": "p1", "recording_id": "b", "mse_m0": 4.0, "mse_m1": 0.0},
        {"pid": "p2", "recording_id": "c", "mse_m0": 9.0, "mse_m1": 0.0},
    ])
    reduced = _participant_balanced_c1_reduction(rows)
    assert reduced.to_dict() == pytest.approx({"p1": 3.5, "p2": 9.0})
    assert reduced.mean() == pytest.approx(6.25)


def test_c1_fold_is_synthetic_and_small_evaluation_support_is_inconclusive():
    train = pd.DataFrame([
        row for index in range(24)
        for row in _c1_series(f"train-{index:02d}", index, recording="r", n=28)
    ])
    evaluation = pd.DataFrame([
        row for index in range(20)
        for row in _c1_series(f"test-{index:02d}", index + 40, recording="r", n=28)
    ])
    result = evaluate_c1_fold(train, evaluation, ["x", "y"], horizon_lag=1, fold_id=0)
    assert result.evaluation_pid_count == 20
    assert result.scored_participant_count == 20
    assert result.training_pids == tuple(f"train-{index:02d}" for index in range(24))
    assert len(result.participant_reductions) == 20
    shifted_diagnostic = evaluate_c1_fold(
        train, evaluation, ["x", "y"], horizon_lag=1, fold_id=0, history_shift_rows=5
    )
    assert shifted_diagnostic.history_shift_rows == 5

    small = evaluation.loc[evaluation.pid.isin([f"test-{index:02d}" for index in range(10)])]
    small_result = evaluate_c1_fold(train, small, ["x", "y"], horizon_lag=1, fold_id=0)
    assert small_result.scored_participant_count == 10
    with pytest.raises(ValueError, match="all 5 expected folds"):
        summarize_c1_out_of_fold(
            [small_result], split_manifest=build_grouped_pid_manifest(small)
        )


def test_c1_out_of_fold_summary_combines_small_folds_and_rejects_repeated_pids():
    all_rows = pd.DataFrame([
        row for index in range(50)
        for row in _c1_series(f"pid-{index:02d}", index, recording="r", n=24)
    ])
    fold_results = [
        evaluate_c1_fold(train, test, ["x", "y"], horizon_lag=1, fold_id=fold_id)
        for fold_id, (train, test) in enumerate(grouped_pid_splits(all_rows))
    ]
    assert [fold.evaluation_pid_count for fold in fold_results] == [10] * 5
    expected = tuple(sorted(all_rows.pid.unique()))
    manifest = build_grouped_pid_manifest(all_rows)
    pooled = summarize_c1_out_of_fold(fold_results, split_manifest=manifest)
    assert pooled.gate_status == "DESCRIPTIVE_SCORE_AVAILABLE"
    assert pooled.participant_count == 50
    assert pooled.expected_pid_count == 50
    assert pooled.pids_without_scores == ()
    assert len(pooled.participant_reductions) == 50
    unregistered_horizon = [replace(fold, horizon_lag=3) for fold in fold_results]
    with pytest.raises(ValueError, match="preregistered integer row lags"):
        summarize_c1_out_of_fold(unregistered_horizon, split_manifest=manifest)
    with pytest.raises(ValueError, match="digest does not match"):
        summarize_c1_out_of_fold(
            fold_results, split_manifest=replace(manifest, sha256="0" * 64)
        )
    rotated_folds = tuple(
        replace(
            fold,
            training_pids=tuple(sorted(set(manifest.expected_pids) - set(
                manifest.folds[(fold.fold_id + 1) % 5].evaluation_pids
            ))),
            evaluation_pids=manifest.folds[(fold.fold_id + 1) % 5].evaluation_pids,
        )
        for fold in manifest.folds
    )
    rehashed_payload = _grouped_pid_manifest_payload(
        manifest.pid_column,
        manifest.row_count,
        manifest.participant_row_counts,
        manifest.expected_pids,
        rotated_folds,
    )
    rehashed_alternate_manifest = replace(
        manifest,
        folds=rotated_folds,
        sha256=hashlib.sha256(
            json.dumps(rehashed_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    )
    with pytest.raises(ValueError, match="differs from deterministic GroupKFold assignment"):
        summarize_c1_out_of_fold(fold_results, split_manifest=rehashed_alternate_manifest)
    with pytest.raises(ValueError, match="all 5 expected folds"):
        summarize_c1_out_of_fold(fold_results[:4], split_manifest=manifest)
    with pytest.raises(ValueError, match="mixed horizon"):
        summarize_c1_out_of_fold(
            [fold_results[0], replace(fold_results[1], horizon_lag=2), *fold_results[2:]],
            split_manifest=manifest,
        )
    incomplete_training_roster = replace(
        fold_results[1], training_pids=fold_results[1].training_pids[:-1]
    )
    with pytest.raises(ValueError, match="training PID roster differs"):
        summarize_c1_out_of_fold(
            [fold_results[0], incomplete_training_roster, *fold_results[2:]],
            split_manifest=manifest,
        )
    duplicate_fold = replace(
        fold_results[1],
        evaluation_pids=fold_results[0].evaluation_pids,
        evaluation_pid_count=fold_results[0].evaluation_pid_count,
        training_pids=fold_results[1].training_pids,
        participant_reductions=fold_results[0].participant_reductions,
        scored_participant_count=fold_results[0].scored_participant_count,
    )
    with pytest.raises(ValueError, match="evaluation PID roster differs"):
        summarize_c1_out_of_fold(
            [fold_results[0], duplicate_fold, *fold_results[2:]], split_manifest=manifest
        )

    small_rows = pd.DataFrame([
        row for index in range(15)
        for row in _c1_series(f"small-{index:02d}", index, recording="r", n=24)
    ])
    small_folds = [
        evaluate_c1_fold(train, test, ["x", "y"], horizon_lag=1, fold_id=fold_id)
        for fold_id, (train, test) in enumerate(grouped_pid_splits(small_rows))
    ]
    small_summary = summarize_c1_out_of_fold(
        small_folds, split_manifest=build_grouped_pid_manifest(small_rows)
    )
    assert small_summary.gate_status == "INCONCLUSIVE"
    assert small_summary.participant_count == 15


def test_participant_cluster_bootstrap_is_fixed_seed_and_10k_draws():
    values = np.linspace(-1.0, 1.0, 25)
    assert participant_cluster_bootstrap_interval(values) == participant_cluster_bootstrap_interval(values)
    with pytest.raises(ValueError):
        participant_cluster_bootstrap_interval(values, draws=100)


def _c3_training_rows() -> pd.DataFrame:
    rows = []
    for pid_index in range(6):
        pid = f"train-{pid_index:02d}"
        for epoch, stage, offset in [
            (0, "N2", 0.00), (1, "Wake", 0.12),
            (2, "N2", 0.45), (3, "Wake", 0.58),
        ]:
            rows.append(_chart_row(
                pid, "r", "seg", epoch,
                x=pid_index * 2.0 + offset,
                y=pid_index * 1.3 + offset * 1.8,
                stage=stage,
                relative_time=pid_index * 50.0 + epoch * 30.0,
                end_time=(epoch + 1) * 30.0,
            ))
    return pd.DataFrame(rows)


def _c3_evaluation_rows(pid: str = "heldout") -> pd.DataFrame:
    return pd.DataFrame([
        _chart_row(pid, "night", "seg", 0, 1.0, 2.0, stage="N2", relative_time=100, end_time=30),
        _chart_row(pid, "night", "seg", 1, 1.01, 2.01, stage="Wake", relative_time=101, end_time=60),
        _chart_row(pid, "night", "seg", 2, 4.0, 5.0, stage="N2", relative_time=200, end_time=90),
        _chart_row(pid, "night", "seg", 3, 4.01, 5.01, stage="Wake", relative_time=201, end_time=120),
    ])


def test_c3_caliper_is_training_only_and_cell_weighted_by_pid():
    training = _c3_training_rows()
    unsupported_pid_rows = pd.DataFrame([
        _chart_row(
            "train-unavailable", "r", "seg", epoch,
            x=100.0 + epoch, y=200.0 + epoch,
            stage=stage,
            relative_time=1000.0 + epoch * 30,
            supported=False,
        )
        for epoch, stage in [(0, "N2"), (1, "Wake"), (2, "N2"), (3, "Wake")]
    ])
    training = pd.concat([training, unsupported_pid_rows], ignore_index=True)
    transform = fit_c3_distance_transform(training, ["x", "y"])
    caliper = fit_c3_caliper(training, transform)
    modified_apply = _c3_evaluation_rows()
    modified_apply["x"] = 1e9
    # Neither fitting nor calibrating accepts apply data.
    refit = fit_c3_distance_transform(training, ["x", "y"])
    recaliper = fit_c3_caliper(training, refit)
    assert transform.chart.center == pytest.approx(refit.chart.center)
    assert caliper.threshold == pytest.approx(recaliper.threshold)
    assert "train-unavailable" in transform.training_pids
    assert caliper.training_pid_count == 6
    assert caliper.training_context_cell_count == 12
    with pytest.raises(ValueError, match="outside the fitted outer-training transform"):
        fit_c3_caliper(_c3_evaluation_rows(), transform)
    fully_withheld_overlap = _c3_evaluation_rows("train-unavailable")
    fully_withheld_overlap["source_support_eligible"] = False
    fully_withheld_overlap["coordinate_qc_valid"] = False
    with pytest.raises(ValueError, match="overlap outer-training PIDs"):
        match_c3_origins(fully_withheld_overlap, transform, caliper)


def test_c3_matching_is_deterministic_one_to_one_and_ignores_future_columns():
    training = _c3_training_rows()
    transform = fit_c3_distance_transform(training, ["x", "y"])
    caliper = fit_c3_caliper(training, transform)
    evaluation = _c3_evaluation_rows()
    evaluation["future_chart"] = [100.0, -100.0, 1000.0, -1000.0]
    evaluation["future_stage"] = ["Wake", "N2", "Wake", "N2"]
    pairs = match_c3_origins(evaluation, transform, caliper)
    repeated = match_c3_origins(evaluation.sample(frac=1, random_state=7), transform, caliper)
    columns = ["pid", "recording_id", "n2_epoch_id", "wake_epoch_id", "distance"]
    assert pairs[columns].sort_values("n2_epoch_id").reset_index(drop=True).equals(
        repeated[columns].sort_values("n2_epoch_id").reset_index(drop=True)
    )
    assert len(pairs) == 2
    assert pairs.n2_epoch_id.nunique() == len(pairs)
    assert pairs.wake_epoch_id.nunique() == len(pairs)
    assert np.all(pairs.distance <= caliper.threshold)

    conflicted = evaluation.copy()
    conflicted.loc[conflicted.epoch_id == 0, "stage_conflict"] = True
    filtered_pairs = match_c3_origins(conflicted, transform, caliper)
    assert 0 not in set(filtered_pairs.n2_epoch_id)


def test_c3_score_is_after_matching_and_requires_contiguous_supported_future_rows():
    training = _c3_training_rows()
    transform = fit_c3_distance_transform(training, ["x", "y"])
    evaluation = pd.DataFrame([
        _chart_row("heldout", "night", "seg", 0, 0, 0, stage="N2"),
        _chart_row("heldout", "night", "seg", 1, 2, 1, stage="Wake"),
        _chart_row("heldout", "night", "seg", 2, 5, 3, stage="Wake"),
        _chart_row("heldout", "night", "seg", 3, 6, 6, stage="N2"),
    ])
    pair = pd.DataFrame([{
        "pid": "heldout", "recording_id": "night",
        "n2_segment_id": "seg", "wake_segment_id": "seg",
        "n2_epoch_id": 0, "wake_epoch_id": 2,
    }])
    scored = score_c3_matched_displacements(pair, evaluation, transform, horizon_lag=1)
    assert scored.loc[0, "outcome_status"] == "AVAILABLE"
    assert scored.loc[0, "displacement_difference__x"] == pytest.approx(1.0 / transform.chart.scale[0])
    assert scored.loc[0, "displacement_difference__y"] == pytest.approx(-2.0 / transform.chart.scale[1])

    evaluation.loc[evaluation.epoch_id == 1, "source_support_eligible"] = False
    failed = score_c3_matched_displacements(pair, evaluation, transform, horizon_lag=1)
    assert failed.loc[0, "outcome_status"] == "NO_VALID_CONTIGUOUS_TARGET"
    assert np.isnan(failed.loc[0, "displacement_difference__x"])
    gapped_evaluation = evaluation.loc[evaluation.epoch_id != 1].copy()
    gapped = score_c3_matched_displacements(pair, gapped_evaluation, transform, horizon_lag=1)
    assert gapped.loc[0, "outcome_status"] == "NO_VALID_CONTIGUOUS_TARGET"


def _annotate_c3_fold_tables(
    matched: pd.DataFrame,
    scored: pd.DataFrame,
    manifest,
    chart_columns: tuple[str, ...] = ("x", "y"),
):
    matched_folds = []
    scored_folds = []
    for fold in manifest.folds:
        fold_matched = matched.loc[matched.pid.astype(str).isin(fold.evaluation_pids)].copy()
        fold_scored = scored.loc[scored.pid.astype(str).isin(fold.evaluation_pids)].copy()
        for frame in (fold_matched, fold_scored):
            frame["outer_fold_id"] = fold.fold_id
            frame["outer_training_pids"] = pd.Series(
                [fold.training_pids] * len(frame), index=frame.index, dtype=object
            )
            frame["chart_columns"] = pd.Series(
                [chart_columns] * len(frame), index=frame.index, dtype=object
            )
        matched_folds.append(fold_matched)
        scored_folds.append(fold_scored)
    return matched_folds, scored_folds


def test_c3_pre_outcome_overlap_gate_needs_no_scored_or_future_table():
    roster = pd.DataFrame({"pid": [f"p{index:02d}" for index in range(21)]})
    manifest = build_grouped_pid_manifest(roster)
    matched_by_fold = []
    for fold in manifest.folds:
        rows = []
        for pid_index in range(20):
            pid = f"p{pid_index:02d}"
            if pid not in fold.evaluation_pids:
                continue
            for pair_index in range(10):
                row = {
                    "pid": pid,
                    "recording_id": "recording-a",
                    "n2_segment_id": "segment-a",
                    "wake_segment_id": "segment-a",
                    "n2_epoch_id": pair_index * 2,
                    "wake_epoch_id": pair_index * 2 + 1,
                    "n2_t_end": float(pair_index * 60),
                    "wake_t_end": float(pair_index * 60 + 30),
                    "n2_stage": "N2",
                    "wake_stage": "Wake",
                    "distance": 0.0,
                    "outer_fold_id": fold.fold_id,
                    "outer_training_pids": fold.training_pids,
                    "chart_columns": ("m", "d", "e"),
                }
                for column in ("m", "d", "e", "recording_relative_seconds"):
                    row[f"n2_scaled__{column}"] = 0.0
                    row[f"wake_scaled__{column}"] = 0.0
                rows.append(row)
        matched_by_fold.append(pd.DataFrame(rows))

    result = combine_c3_matched_origins_out_of_fold(
        matched_by_fold,
        fold_ids=tuple(range(5)),
        split_manifest=manifest,
        chart_columns=("m", "d", "e"),
    )
    assert not hasattr(result, "scored_pairs")
    assert not any(column.startswith(("displacement", "outcome", "future")) for column in result.matched_pairs)
    gate = c3_overlap_gate(result)
    assert gate.gate_status == "OVERLAP_GATE_PASS"
    assert gate.expected_pid_count == 21
    assert gate.qualifying_pid_count == 20
    assert gate.pair_count == 200
    assert dict(gate.smd_iqr) == pytest.approx({
        "m": 0.0, "d": 0.0, "e": 0.0, "recording_relative_seconds": 0.0,
    })

    changed = result.matched_pairs.copy()
    changed.loc[changed.index[0], "n2_scaled__m"] = 0.25
    with pytest.raises(ValueError, match="matched table content changed"):
        c3_overlap_gate(replace(result, matched_pairs=changed))
    with pytest.raises(ValueError, match="all 5 expected folds"):
        combine_c3_matched_origins_out_of_fold(
            matched_by_fold[:4],
            fold_ids=tuple(range(4)),
            split_manifest=manifest,
            chart_columns=("m", "d", "e"),
        )


def test_c3_overlap_gate_and_effect_summary_use_pid_then_recording_weights():
    rows = []
    for pid_index in range(20):
        pid = f"p{pid_index:02d}"
        recordings = ["r1", "r2"] if pid_index == 0 else ["r1"]
        for recording in recordings:
            pair_count = 10
            x_difference = 0.0 if pid_index == 0 and recording == "r1" else (
                100.0 if pid_index == 0 else float(pid_index)
            )
            for pair_index in range(pair_count):
                rows.append({
                    "pid": pid,
                    "recording_id": recording,
                        "n2_segment_id": "seg",
                        "wake_segment_id": "seg",
                        "n2_epoch_id": pair_index * 2,
                        "wake_epoch_id": pair_index * 2 + 1,
                        "n2_t_end": float(pair_index * 60),
                        "wake_t_end": float(pair_index * 60 + 30),
                        "n2_stage": "N2",
                        "wake_stage": "Wake",
                        "distance": 0.05,
                        "horizon_lag": 1,
                    "outcome_status": "AVAILABLE",
                    "n2_scaled__x": 0.0,
                    "wake_scaled__x": 0.0,
                    "n2_scaled__y": 0.0,
                    "wake_scaled__y": 0.0,
                    "n2_scaled__recording_relative_seconds": 0.0,
                    "wake_scaled__recording_relative_seconds": 0.0,
                    "displacement_difference__x": x_difference,
                    "displacement_difference__y": -float(pid_index),
                })
    scored = pd.DataFrame(rows)
    matched = scored.drop(columns=[
        "outcome_status", "horizon_lag",
        "displacement_difference__x", "displacement_difference__y",
    ])
    expected_pids = tuple(f"p{index:02d}" for index in range(20))
    complete_roster = pd.DataFrame({"pid": [*expected_pids, "p20"]})
    manifest = build_grouped_pid_manifest(complete_roster)
    matched_folds, scored_folds = _annotate_c3_fold_tables(matched, scored, manifest)
    out_of_fold = combine_c3_out_of_fold(
        matched_folds,
        scored_folds,
        horizon_lag=1,
        fold_ids=tuple(range(5)),
        split_manifest=manifest,
        chart_columns=("x", "y"),
    )
    with pytest.raises(ValueError, match="does not match requested h2"):
        combine_c3_out_of_fold(
            matched_folds,
            scored_folds,
            horizon_lag=2,
            fold_ids=tuple(range(5)),
            split_manifest=manifest,
            chart_columns=("x", "y"),
        )
    mutated_pairs = out_of_fold.matched_pairs.copy()
    mutated_pairs.loc[mutated_pairs.index[0], "outer_fold_id"] = 99
    with pytest.raises(ValueError, match="unknown GroupKFold fold"):
        c3_overlap_gate(replace(out_of_fold, matched_pairs=mutated_pairs))
    with pytest.raises(ValueError, match="completion of all five"):
        c3_overlap_gate(replace(out_of_fold, assembled_fold_ids=(0, 1, 2, 3)))
    gate = c3_overlap_gate(out_of_fold)
    assert gate.gate_status == "OVERLAP_GATE_PASS"
    assert gate.expected_pid_count == 21
    assert gate.pids_without_matches == ("p20",)
    assert gate.qualifying_pid_count == 20
    assert gate.pair_count == 210
    assert dict(gate.smd_iqr) == pytest.approx({
        "x": 0.0, "y": 0.0, "recording_relative_seconds": 0.0,
    })
    summary = summarize_c3_effect(out_of_fold, overlap_gate=gate)
    assert summary.gate_status == "DESCRIPTIVE_SCORE_AVAILABLE"
    assert summary.participant_count == 20
    assert summary.mean_difference_iqr[0][1] == pytest.approx(12.0)
    assert summary.ci95 is not None
    assert summary.matched_pair_count == 210
    assert summary.outcome_eligible_pair_count == 210

    changed_origins = out_of_fold.matched_pairs.copy()
    changed_origins.loc[changed_origins.index[0], "n2_scaled__x"] += 0.5
    with pytest.raises(ValueError, match="matched table content changed"):
        summarize_c3_effect(replace(out_of_fold, matched_pairs=changed_origins), overlap_gate=gate)

    unavailable = scored.copy()
    unavailable.loc[unavailable.pid == "p00", "outcome_status"] = "NO_VALID_CONTIGUOUS_TARGET"
    _, unavailable_folds = _annotate_c3_fold_tables(matched, unavailable, manifest)
    unavailable_oof = combine_c3_out_of_fold(
        matched_folds, unavailable_folds, horizon_lag=1, fold_ids=tuple(range(5)),
        split_manifest=manifest, chart_columns=("x", "y"),
    )
    # Matched-origin gate is pre-outcome and does not shrink when future support fails.
    assert c3_overlap_gate(unavailable_oof).pair_count == gate.pair_count
    assert summarize_c3_effect(unavailable_oof, overlap_gate=gate).gate_status == "INCONCLUSIVE"

    changed_outcomes = out_of_fold.scored_pairs.copy()
    changed_outcomes.loc[changed_outcomes.index[0], "displacement_difference__x"] += 0.5
    changed_outcome_result = replace(out_of_fold, scored_pairs=changed_outcomes)
    # The pre-outcome gate depends only on matched origins, but the effect step
    # rejects outcome-table mutation relative to the assembled replay snapshot.
    assert c3_overlap_gate(changed_outcome_result).pair_count == gate.pair_count
    with pytest.raises(ValueError, match="scored table content changed"):
        summarize_c3_effect(changed_outcome_result, overlap_gate=gate)

    too_few = matched.loc[matched.pid.isin([f"p{index:02d}" for index in range(19)])]
    too_few_scored = scored.loc[scored.pid.isin([f"p{index:02d}" for index in range(19)])]
    too_few_matched_folds, too_few_scored_folds = _annotate_c3_fold_tables(
        too_few, too_few_scored, manifest
    )
    too_few_oof = combine_c3_out_of_fold(
        too_few_matched_folds, too_few_scored_folds, horizon_lag=1,
        fold_ids=tuple(range(5)), split_manifest=manifest, chart_columns=("x", "y"),
    )
    too_few_gate = c3_overlap_gate(too_few_oof)
    assert too_few_gate.gate_status == "INCONCLUSIVE"
    assert summarize_c3_effect(too_few_oof, overlap_gate=too_few_gate).mean_difference_iqr is None
    imbalanced = matched.copy()
    imbalanced["n2_scaled__x"] = 0.2
    imbalanced_folds, imbalanced_scored_folds = _annotate_c3_fold_tables(
        imbalanced, scored, manifest
    )
    imbalanced_oof = combine_c3_out_of_fold(
        imbalanced_folds, imbalanced_scored_folds, horizon_lag=1,
        fold_ids=tuple(range(5)), split_manifest=manifest, chart_columns=("x", "y"),
    )
    failed_balance = c3_overlap_gate(imbalanced_oof)
    assert failed_balance.gate_status == "INCONCLUSIVE"
    assert summarize_c3_effect(imbalanced_oof, overlap_gate=failed_balance).mean_difference_iqr is None
    forged_pass = replace(failed_balance, gate_status="OVERLAP_GATE_PASS")
    with pytest.raises(ValueError, match="status/diagnostics do not match"):
        summarize_c3_effect(imbalanced_oof, overlap_gate=forged_pass)
    with pytest.raises(ValueError, match="representation differs"):
        summarize_c3_effect(replace(out_of_fold, chart_columns=("x",)), overlap_gate=gate)

    combined_summary = summarize_c3_effect(out_of_fold, overlap_gate=gate)
    assert combined_summary.participant_count == 20
    assert gate.expected_pid_count == 21
    assert gate.pids_without_matches == ("p20",)
    with pytest.raises(ValueError, match="all 5 expected folds"):
        combine_c3_out_of_fold(
            matched_folds[:4],
            scored_folds[:4],
            horizon_lag=1,
            fold_ids=tuple(range(4)),
            split_manifest=manifest,
            chart_columns=("x", "y"),
        )
    wrong_binding = [frame.copy() for frame in matched_folds]
    wrong_binding[0].loc[wrong_binding[0].index[0], "outer_fold_id"] = 99
    with pytest.raises(ValueError, match="do not bind to GroupKFold fold"):
        combine_c3_out_of_fold(
            wrong_binding,
            scored_folds,
            horizon_lag=1,
            fold_ids=tuple(range(5)),
            split_manifest=manifest,
            chart_columns=("x", "y"),
        )
    wrong_training_roster = [frame.copy() for frame in matched_folds]
    row_index = wrong_training_roster[0].index[0]
    wrong_training_roster[0].at[row_index, "outer_training_pids"] = manifest.folds[0].training_pids[:-1]
    with pytest.raises(ValueError, match="full training PID roster"):
        combine_c3_out_of_fold(
            wrong_training_roster,
            scored_folds,
            horizon_lag=1,
            fold_ids=tuple(range(5)),
            split_manifest=manifest,
            chart_columns=("x", "y"),
        )


def test_c3_zero_match_rows_keep_schema_and_reach_an_inconclusive_gate():
    training = _c3_training_rows()
    transform = fit_c3_distance_transform(training, ["x", "y"])
    zero_caliper = C3Caliper(
        threshold=0.0,
        training_pid_count=6,
        training_context_cell_count=12,
        participant_cell_means=(),
    )
    evaluation = _c3_evaluation_rows()
    no_pairs = match_c3_origins(evaluation, transform, zero_caliper, fold_id=0)
    assert no_pairs.empty
    assert {"pid", "recording_id", "n2_epoch_id", "wake_epoch_id"}.issubset(no_pairs.columns)
    no_scores = score_c3_matched_displacements(no_pairs, evaluation, transform, horizon_lag=1)
    assert no_scores.empty
    assert "horizon_lag" in no_scores.columns

    roster = pd.DataFrame({"pid": [f"p{index:02d}" for index in range(20)]})
    manifest = build_grouped_pid_manifest(roster)
    matched_folds = []
    scored_folds = []
    for fold in manifest.folds:
        matched_fold = no_pairs.copy()
        scored_fold = no_scores.copy()
        for frame in (matched_fold, scored_fold):
            frame["outer_fold_id"] = pd.Series(dtype="int64")
            frame["outer_fold_id"] = frame["outer_fold_id"].astype("int64")
            frame["outer_training_pids"] = pd.Series(dtype="object")
            frame["chart_columns"] = pd.Series(dtype="object")
        matched_folds.append(matched_fold)
        scored_folds.append(scored_fold)
    no_match_oof = combine_c3_out_of_fold(
        matched_folds,
        scored_folds,
        horizon_lag=1,
        fold_ids=tuple(range(5)),
        split_manifest=manifest,
        chart_columns=("x", "y"),
    )
    assert no_match_oof.fold_match_counts == (0, 0, 0, 0, 0)
    no_match_gate = c3_overlap_gate(no_match_oof)
    assert no_match_gate.gate_status == "INCONCLUSIVE"
    assert "no_matched_origins" in no_match_gate.reasons
    assert summarize_c3_effect(no_match_oof, overlap_gate=no_match_gate).gate_status == "INCONCLUSIVE"


def test_c3_stage_label_shift_never_crosses_segment_and_reports_short_segments():
    rows = []
    for epoch in range(10):
        rows.append(_chart_row("p", "r", "long", epoch, epoch, epoch, stage=f"stage-{epoch}"))
    for epoch in range(7):
        rows.append(_chart_row("p", "r", "short", epoch, epoch, epoch, stage=f"short-{epoch}"))
    frame = pd.DataFrame(rows)
    shifted, audit = circular_shift_stage_labels(frame)
    long_labels = shifted.loc[shifted.segment_id == "long"].sort_values("epoch_id").stage.tolist()
    short_labels = shifted.loc[shifted.segment_id == "short"].sort_values("epoch_id").stage.tolist()
    expected_long = np.roll(frame.loc[frame.segment_id == "long"].sort_values("epoch_id").stage.to_numpy(), 8).tolist()
    assert long_labels == expected_long
    assert short_labels == [f"short-{epoch}" for epoch in range(7)]
    assert dict(zip(audit.segment_id, audit.feasible)) == {"long": True, "short": False}
    gapped = frame.loc[~((frame.segment_id == "long") & (frame.epoch_id == 5))].copy()
    with pytest.raises(ValueError, match="contains an epoch gap"):
        circular_shift_stage_labels(gapped)
