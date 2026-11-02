"""Synthetic contract checks for the frozen BENCH-001 H1 analysis."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_h1 as bench


def _text_dataset(group, name, value):
    group.create_dataset(name, data=value, dtype=h5py.string_dtype("utf-8"))


def _synthetic_recording(path: Path) -> None:
    legacy_count = 16
    legacy_intervals = [(float(i * 4), float(i * 4 + 8)) for i in range(legacy_count)]
    v3_intervals = [(float(i * 20), float(i * 20 + 20)) for i in range(4)]
    with h5py.File(path, "w") as h5:
        rows = h5.require_group("row_source")
        _text_dataset(rows, "raw_file", np.asarray([
            "sub-001_ses-1_task-EyesClosed_acq-pre_eeg.edf"
        ] * legacy_count, dtype=object))
        h5.create_dataset("window_start", data=[x[0] for x in legacy_intervals])
        h5.create_dataset("window_end", data=[x[1] for x in legacy_intervals])

        coords = h5.require_group("coords_9d")
        _text_dataset(coords, "names", np.asarray(bench.LEGACY_FEATURES, dtype=object))
        coords.create_dataset(
            "values",
            data=np.arange(legacy_count, dtype=float)[:, None] + np.arange(9, dtype=float)[None, :],
        )
        qc = h5.require_group("qc/windows")
        qc.create_dataset("coords_9d_valid", data=np.ones(legacy_count, dtype=bool))

        raw = h5.require_group("features_raw")
        raw_names = (
            "eeg_delta", "eeg_theta", "eeg_alpha", "eeg_beta", "eeg_gamma",
            "eeg_highfreq_power_30_45", "eeg_alpha_theta", "eeg_beta_alpha",
            "eeg_hjorth_mobility", "eeg_hjorth_complexity", "eeg_permutation_entropy",
            "eeg_sample_entropy", "embodied_arousal_proxy",
        )
        _text_dataset(raw, "names", np.asarray(raw_names, dtype=object))
        raw.create_dataset("values", data=np.ones((legacy_count, len(raw_names)), dtype=float))

        rel = h5.require_group("extensions/conventional_eeg/families/relative")
        for name in bench.CONVENTIONAL_FEATURES:
            band = rel.require_group(name)
            _text_dataset(band, "column", f"eeg_conventional_relative_{name}")
            band.create_dataset("n", data=legacy_count)
            band.create_dataset("median", data=0.2)
            band.create_dataset("mean", data=0.21)

        measurements = []
        by_feature = {
            "PCV": "M1", "TP": "M2", "AR": "M3", "NIE": "D1", "RD": "D3",
            "OI": "E1", "SC": "E2", "ED": "E3",
        }
        for i, (start, end) in enumerate(v3_intervals):
            rows_for_window = []
            for feature, candidate in by_feature.items():
                value = np.arange(9, dtype=float) + i if feature == "AR" else float(i + 1)
                rows_for_window.append({
                    "candidate_id": candidate,
                    "computed": True,
                    "valid": True,
                    "value": value.tolist() if feature == "AR" else value,
                })
            measurements.append({
                "window_start_sec": start,
                "window_end_sec": end,
                "measurements": rows_for_window,
            })
        v3 = h5.require_group("measurements/v3_1")
        payload = [{"measurement_payload": {"windows": measurements}}]
        _text_dataset(v3, "recordings_json", json.dumps(payload))


def test_loader_uses_the_independent_v3_grid_and_preserves_ar_components(tmp_path):
    path = tmp_path / "sub-001_ses-1_task-EyesClosed_acq-pre.h5"
    _synthetic_recording(path)
    recording = bench.load_h1_recording(path)

    assert recording.subject == "sub-001"
    assert recording.state == "EyesClosed"
    assert len(recording.features["v3_full"]) == 16
    assert recording.features["v3_full"]["PCV"] == 2.5
    assert recording.features["v3_full"]["AR_pair_01"] == 1.5
    assert recording.features["v3_full"]["AR_pair_09"] == 9.5
    assert recording.qc["v3_window_count"] == 4
    assert recording.qc["legacy_window_count"] == 16
    ar_support = next(row for row in recording.coverage if row["feature"] == "AR_vector")
    assert ar_support["finite_window_count"] == 4
    assert ar_support["supported_seconds"] == 80.0
    assert recording.features["legacy_v2"]["m_a"] == 7.5
    assert recording.features["conventional_relative_power"]["alpha"] == 0.2
    alpha_support = next(
        row for row in recording.coverage
        if row["arm"] == "conventional_relative_power" and row["feature"] == "alpha"
    )
    assert alpha_support["finite_window_count"] == 16
    assert alpha_support["supported_seconds"] == 68.0


def test_conventional_support_is_a_conservative_union_bound_from_count_only():
    intervals = [(float(i * 4), float(i * 4 + 8)) for i in range(16)]
    assert bench.minimum_union_duration_for_count(intervals, 16) == 68.0
    assert bench.minimum_union_duration_for_count(intervals, 14) == 60.0
    assert bench.minimum_union_duration_for_count(intervals, 13) == 56.0
    assert bench.minimum_union_duration_for_count(intervals, 0) == 0.0


def test_grouped_nested_cv_schedule_keeps_each_participant_together():
    subjects = [f"sub-{index:03d}" for index in range(1, 21)]
    schedule = bench.make_split_schedule(subjects, n_repeats=2, n_outer=4, n_inner=3)
    groups = np.repeat(np.asarray(subjects), 2)
    for repeat in schedule:
        for fold in repeat:
            assert not set(groups[fold.train]) & set(groups[fold.test])
            for inner in fold.inner:
                inner_train = groups[fold.train][inner.train_local]
                inner_valid = groups[fold.train][inner.valid_local]
                assert not set(inner_train) & set(inner_valid)


def test_paired_auc_ties_and_holm_adjustment():
    scores = bench.paired_auc_by_subject(
        [0, 1, 0, 1], ["sub-1", "sub-1", "sub-2", "sub-2"], [0.4, 0.4, 0.8, 0.2],
    )
    assert scores == {"sub-1": 0.5, "sub-2": 0.0}
    np.testing.assert_allclose(bench.holm_adjust([0.01, 0.02, 0.9]), [0.03, 0.04, 0.9])


def test_unsupported_measurement_remains_missing_below_support_floor():
    value, support = bench._supported_aggregate(
        "PCV", [0.8, 0.9], [(0.0, 20.0), (20.0, 40.0)],
        subject="sub-001", state="EyesClosed", arm="v3_full",
    )
    assert np.isnan(value[0])
    assert support["support_pass"] is False
    assert support["supported_seconds"] == 40.0


def test_nested_cv_emits_one_oof_probability_per_row_and_repeat():
    subjects = [f"sub-{index:03d}" for index in range(1, 21)]
    labels = np.tile(np.asarray([0, 1], dtype=np.int8), len(subjects))
    groups = np.repeat(np.asarray(subjects), 2)
    rng = np.random.default_rng(44)
    matrix = rng.normal(size=(len(labels), 4))
    matrix[labels == 1, 0] += 0.5
    schedule = bench.make_split_schedule(subjects, n_repeats=2, n_outer=4, n_inner=3)
    result = bench.nested_grouped_cv(matrix, labels, groups, schedule)

    assert result["predictions_by_repeat"].shape == (2, len(labels))
    assert np.isfinite(result["mean_probability"]).all()
    assert len(result["c_choices"]) == 8
    assert 0.0 <= result["paired_auc"] <= 1.0
