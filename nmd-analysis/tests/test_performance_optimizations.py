from __future__ import annotations

from unittest.mock import patch

import h5py
import numpy as np
import pytest
import yaml
from scipy.spatial.distance import cdist
from sklearn.linear_model import Ridge as ReferenceRidge

import nmd_analysis.pipeline as pipeline
import nmd_analysis.reachability_core as reachability_core
import nmd_analysis.local_dynamics.adapters as local_adapters
from nmd_analysis.local_dynamics.adapters import transition_rows
from nmd_analysis.regional_stratified_mnps import compute_windowed_features


def _write_transition_fixture(path) -> None:
    with h5py.File(path, "w") as h5:
        h5.attrs.update(dataset_id="demo", subject_id="sub-01", modality="eeg")
        group = h5.create_group("/transition_residuals/v1/primary")
        group.create_dataset("schema_version", data=np.bytes_("mndm.transition_residuals.v1"))
        group.create_dataset("computation_status", data=np.bytes_("computed"))
        series = group.create_group("series")
        series.create_dataset("source_window_id", data=np.array([2, 3, 4], dtype=np.int32))
        series.create_dataset("target_window_id", data=np.array([3, 4, 5], dtype=np.int32))
        series.create_dataset("source_center", data=np.array([10, 20, 30], dtype=np.int32))
        series.create_dataset("target_center", data=np.array([20, 30, 40], dtype=np.int32))
        series.create_dataset("dt_sec", data=np.array([1.0, 1.0, 1.0]))
        series.create_dataset("transition_residual", data=np.eye(3))
        series.create_dataset("x_pred_next", data=np.ones((3, 3)))


def test_transition_rows_bulk_loads_indexed_series_and_preserves_values(tmp_path):
    path = tmp_path / "transition.h5"
    _write_transition_fixture(path)

    with patch.object(local_adapters, "scalar", wraps=local_adapters.scalar) as scalar_mock:
        rows = transition_rows(path, dimension=3)

    assert [row["source_window_id"] for row in rows] == [2, 3, 4]
    assert [row["target_center"] for row in rows] == [20, 30, 40]
    assert all(row["computation_status"] == "computed" for row in rows)
    assert all(row["source_h5_path"] == str(path) for row in rows)
    assert rows[0] is not rows[1]
    rows[0]["source_h5"] = "mutated"
    assert rows[1]["source_h5"] == str(path)
    indexed_names = {"source_window_id", "target_window_id", "source_center", "target_center", "dt_sec"}
    scalar_paths = {call.args[1] for call in scalar_mock.call_args_list}
    assert not indexed_names & scalar_paths
    assert sum(call.args[1] == "schema_version" for call in scalar_mock.call_args_list) == 1


def test_transition_rows_keep_missing_optional_index_fields_as_fallbacks(tmp_path):
    path = tmp_path / "transition_missing_optional.h5"
    _write_transition_fixture(path)
    with h5py.File(path, "a") as h5:
        series = h5["/transition_residuals/v1/primary/series"]
        del series["source_window_id"]
        del series["source_center"]

    rows = transition_rows(path, dimension=3)
    assert [row["source_window_id"] for row in rows] == [0, 1, 2]
    assert [row["source_center"] for row in rows] == [None, None, None]
    assert [row["target_window_id"] for row in rows] == [3, 4, 5]


def _write_jacobian_fixture(path) -> None:
    with h5py.File(path, "w") as h5:
        h5.attrs.update(dataset_id="demo", subject_id="sub-01", modality="eeg")
        h5.create_dataset("/jacobian/centers", data=np.array([10, 20], dtype=np.int32))
        group = h5.create_group("/jacobian/derived_metrics/v1")
        group.create_dataset("schema_version", data=np.bytes_("mndm.jacobian_metrics.v1"))
        group.create_dataset("computation_status", data=np.bytes_("computed"))
        series = group.create_group("series")
        series.create_dataset("spectral_abscissa", data=np.array([-1.0, -2.0]))


def test_jacobian_window_rows_cache_static_context_per_file(tmp_path):
    path = tmp_path / "jacobian.h5"
    _write_jacobian_fixture(path)

    with patch.object(local_adapters, "_base", wraps=local_adapters._base) as base_mock:
        rows = local_adapters.jacobian_metrics_window_rows(path, dimension=3)

    assert len(rows) == 2
    assert base_mock.call_count == 1
    assert [row["center"] for row in rows] == [10, 20]
    assert all(row["finite_ok"] for row in rows)


def test_singleton_alpha_uses_ridge_fast_path():
    rng = np.random.default_rng(20260907)
    x = rng.normal(size=(12, 3))
    nn_indices = np.tile(np.arange(6, dtype=np.int32), (12, 1))

    with patch.object(reachability_core, "RidgeCV", side_effect=AssertionError("singleton alpha must not use CV")):
        A_hat, b_hat, Q_hat, meta = reachability_core.estimate_local_linear_model(
            x,
            nn_indices=nn_indices,
            super_window_indices=[[0]],
            alpha_grid=[0.1],
            cv_folds=3,
        )

    candidate_indices = np.arange(6)
    reference = ReferenceRidge(alpha=0.1, fit_intercept=True).fit(
        x[candidate_indices], x[candidate_indices + 1]
    )
    assert np.isfinite(A_hat).all()
    assert np.isfinite(b_hat).all()
    assert np.isfinite(Q_hat).all()
    np.testing.assert_allclose(A_hat[0], reference.coef_)
    np.testing.assert_allclose(b_hat[0], reference.intercept_)
    assert meta["alpha_used"][0] == pytest.approx(0.1)


def test_knn_inverse_positions_preserve_nan_and_tie_behavior():
    x = np.array([[0.0, 0.0], [1.0, 0.0], [np.nan, np.nan], [2.0, 0.0], [3.0, 0.0]])
    k = 2
    expected = np.zeros((len(x), k), dtype=np.int32)
    valid_mask = ~np.isnan(x).any(axis=1)
    valid_indices = np.where(valid_mask)[0]
    distances = cdist(x[valid_mask], x[valid_mask], metric="euclidean")
    for i in range(len(x)):
        if valid_mask[i]:
            position = np.where(valid_indices == i)[0][0]
            expected[i] = valid_indices[np.argsort(distances[position])[:k]]
        else:
            expected[i] = valid_indices[:k]

    actual = reachability_core.build_knn_neighborhoods(x, k=k)
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(actual[1], expected[1])


def test_stratified_window_mask_reuse_preserves_modularity_values():
    rng = np.random.default_rng(20260907)
    bold = rng.normal(size=(3, 20))
    _, _, _, modularity = compute_windowed_features(
        bold, sfreq=2.0, window_sec=4.0, step_sec=2.0
    )

    expected = []
    mask = ~np.eye(3, dtype=bool)
    for start in range(0, 13, 4):
        segment = bold[:, start : start + 8]
        segment_z = segment - segment.mean(axis=1, keepdims=True)
        std = segment.std(axis=1, keepdims=True)
        std[std < 1e-12] = 1e-12
        corr = (segment_z / std) @ (segment_z / std).T / 8
        expected.append(np.mean(corr[mask]))

    np.testing.assert_allclose(modularity, np.asarray(expected))


def test_q_ratio_empty_horizon_keeps_empty_result_without_validating_a():
    result = reachability_core.compute_q_ratio_series(np.empty((1, 2, 2)), None)
    assert result.shape == (0,)


class _FakeAdapter:
    def collect_rows(self, path):
        return [{"source_h5_path": str(path), "finite_ok": True}]


def _write_pipeline_config(path, modality_rules=None) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "dataset": "demo",
                "input": {"h5_root": None},
                "runtime": {"workers": 1},
                "analyses": {"dummy": True},
                "modality_rules": modality_rules or {},
            }
        ),
        encoding="utf-8",
    )


def test_pipeline_skips_modality_io_when_no_rules(tmp_path):
    input_root = tmp_path / "input"
    input_root.mkdir()
    (input_root / "demo.h5").write_bytes(b"not-read-by-fake-adapter")
    config = tmp_path / "config.yaml"
    _write_pipeline_config(config)

    with (
        patch.object(pipeline, "build_adapters", return_value={"dummy": _FakeAdapter()}),
        patch.object(pipeline, "_read_modality", side_effect=AssertionError("modality scan was unnecessary")),
        patch.object(pipeline, "write_parquet_table"),
    ):
        result = pipeline.run_dataset_pipeline(config, input_root=input_root, output_root=tmp_path / "out", workers=1)

    assert result["written_files"]["dummy"]


def test_pipeline_keeps_modality_filtering_when_rules_are_present(tmp_path):
    input_root = tmp_path / "input"
    input_root.mkdir()
    (input_root / "demo.h5").write_bytes(b"not-read-by-fake-adapter")
    config = tmp_path / "config.yaml"
    _write_pipeline_config(config, {"eeg": {"force_disable": ["dummy"]}})

    with (
        patch.object(pipeline, "build_adapters", return_value={"dummy": _FakeAdapter()}),
        patch.object(pipeline, "_read_modality", return_value="eeg") as read_modality,
        patch.object(pipeline, "write_parquet_table"),
    ):
        result = pipeline.run_dataset_pipeline(config, input_root=input_root, output_root=tmp_path / "out", workers=1)

    read_modality.assert_called_once()
    assert "dummy:no_candidate_files" in result["skipped"]
