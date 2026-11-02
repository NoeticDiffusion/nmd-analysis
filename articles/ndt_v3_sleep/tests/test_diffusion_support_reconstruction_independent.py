"""Independent contract checks for candidate diffusion-support reconstruction."""

from __future__ import annotations

import json
from pathlib import Path

import h5py
import numpy as np
import pytest
import yaml

import diffusion_support_reconstruction as reconstruction
from diffusion_support_reconstruction import _candidate_rows, _load_producer, _settings, _sha256, run


PRODUCER_ROOT = Path("H:/SourceRepo2/NeuralManifoldDynamics")


def _synthetic_input(path: Path, *, corrupt_tensor: bool = False) -> None:
    diffusion, _validity = _load_producer(PRODUCER_ROOT)
    rng = np.random.default_rng(41)
    state = np.cumsum(rng.normal(size=(36, 3)).astype(np.float32), axis=0)
    time = np.arange(36, dtype=np.float64) * 30.0
    segments = np.zeros(36, dtype=np.int32)
    result = diffusion.estimate_local_diffusion_geometry(
        state,
        time,
        segment_id=segments,
        coordinate_layer="coords_3d_subject_anchored",
        coordinate_names=["m", "d", "e"],
        neighborhood_k=20,
        min_samples=30,
        min_neighborhood_samples=10,
        max_gap_sec=None,
        max_dt_relative_deviation=0.05,
        psd_floor=1e-8,
    )
    tensor = np.asarray(result["series"]["diffusion_tensor"])
    if corrupt_tensor:
        tensor = tensor.copy()
        tensor[0, 0, 0] += np.float32(1.0)
    settings = result["provenance"]["settings"]
    with h5py.File(path, "w") as handle:
        handle.create_dataset("coords_3d_subject_anchored/values", data=state)
        handle.create_dataset("time", data=time)
        handle.create_dataset("epoch_id", data=np.arange(36, dtype=np.int64))
        handle.create_dataset("window_start", data=time)
        handle.create_dataset("window_end", data=time + 30.0)
        handle.create_dataset("labels/stage", data=np.zeros(36, dtype=np.int8))
        handle.create_dataset(
            "row_source/raw_file",
            data=np.asarray(["synthetic.edf"] * 36, dtype=object),
            dtype=h5py.string_dtype(),
        )
        handle.create_dataset(
            "dynamical_families/diffusion/v1/series/diffusion_tensor", data=tensor
        )
        handle.create_dataset(
            "dynamical_families/diffusion/v1/series/support_count",
            data=result["series"]["support_count"],
        )
        handle.create_dataset(
            "dynamical_families/diffusion/v1/series/valid",
            data=result["series"]["valid"],
        )
        for key in (
            "neighborhood_k",
            "min_samples",
            "min_neighborhood_samples",
            "max_dt_relative_deviation",
            "min_valid_fraction",
            "psd_floor",
        ):
            handle.create_dataset(
                f"dynamical_families/diffusion/v1/provenance/settings/{key}",
                data=settings[key],
            )


def _config(tmp_path: Path, h5_path: Path, *, output_name: str = "out") -> Path:
    producer_files = sorted(reconstruction.REQUIRED_PRODUCER_FILES)
    config = {
        "input_h5": str(h5_path),
        "producer_root": str(PRODUCER_ROOT),
        "output": str(tmp_path / output_name),
        "producer_git_revision_recorded": "synthetic-independent",
        "input_h5_sha256": _sha256(h5_path),
        "analysis_code": str(Path(__file__).parents[1] / "src" / "diffusion_support_reconstruction.py"),
        "analysis_code_sha256": _sha256(Path(__file__).parents[1] / "src" / "diffusion_support_reconstruction.py"),
        "producer_files": producer_files,
        "producer_file_sha256": {
            relative: _sha256(PRODUCER_ROOT / relative) for relative in producer_files
        },
        "settings": {
            "neighborhood_k": 20,
            "min_samples": 30,
            "min_neighborhood_samples": 10,
            "max_gap_sec": None,
            "max_dt_relative_deviation": 0.05,
            "min_valid_fraction": 0.1,
            "psd_floor": 1e-8,
        },
    }
    config_path = tmp_path / f"{output_name}.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path


@pytest.mark.skipif(not (PRODUCER_ROOT / "mndm/src").exists(), reason="producer checkout unavailable")
def test_empty_or_partial_producer_pin_is_refused(tmp_path: Path):
    h5_path = tmp_path / "input.h5"
    _synthetic_input(h5_path)
    config_path = _config(tmp_path, h5_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["producer_files"] = []
    config["producer_file_sha256"] = {}
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValueError, match="exact required|producer_files"):
        run(config_path)


@pytest.mark.skipif(not (PRODUCER_ROOT / "mndm/src").exists(), reason="producer checkout unavailable")
def test_analysis_code_pin_must_name_this_runner(tmp_path: Path):
    h5_path = tmp_path / "input.h5"
    _synthetic_input(h5_path)
    config_path = _config(tmp_path, h5_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    copied_code = tmp_path / "copied_runner.py"
    runner = Path(__file__).parents[1] / "src" / "diffusion_support_reconstruction.py"
    copied_code.write_bytes(runner.read_bytes())
    config["analysis_code"] = str(copied_code)
    config["analysis_code_sha256"] = _sha256(copied_code)
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValueError, match="analysis_code"):
        run(config_path)


@pytest.mark.skipif(not (PRODUCER_ROOT / "mndm/src").exists(), reason="producer checkout unavailable")
def test_stored_settings_mismatch_refuses_candidate_export(tmp_path: Path):
    h5_path = tmp_path / "input.h5"
    _synthetic_input(h5_path)
    config_path = _config(tmp_path, h5_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["settings"]["psd_floor"] = 2e-8
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    manifest = run(config_path)
    assert manifest["status"] == "candidate_only_gate_failed"
    assert manifest["gate"]["settings_match_stored_provenance"] is False
    assert not (tmp_path / "out" / "candidate_neighbors.csv").exists()


def test_candidate_rows_flag_unknown_queries_and_endpoint_labels():
    data = {
        "stage": np.array([8, 8, 0], dtype=np.int8),
        "epoch_id": np.array([10, 11, 12], dtype=np.int64),
        "time": np.array([0.0, 30.0, 60.0]),
        "window_start": np.array([0.0, 30.0, 60.0]),
        "window_end": np.array([30.0, 60.0, 90.0]),
        "reference_count": 2,
    }
    rows, summaries = _candidate_rows(
        data,
        np.array([0, 1], dtype=np.int32),
        np.array([[0, 1]], dtype=np.int32),
        np.array([[0.0, 1.0]], dtype=float),
        np.array([0], dtype=np.int32),
    )
    assert summaries == [{
        "query_epoch_id": 10,
        "query_stage_code": 8,
        "query_stage_known": False,
        "same_known_stage_source_target_count": None,
        "same_known_stage_source_target_fraction": None,
        "kth_distance_tie_ambiguous": False,
    }]
    assert all(row["query_stage_unknown"] for row in rows)
    assert all(row["source_stage_unknown"] for row in rows)
    assert [row["target_stage_unknown"] for row in rows] == [True, False]


def test_candidate_rows_flags_equal_distance_cutoff_tie():
    data = {
        "stage": np.array([0, 0, 0, 0], dtype=np.int8),
        "epoch_id": np.arange(4, dtype=np.int64),
        "time": np.arange(4, dtype=float) * 30.0,
        "window_start": np.arange(4, dtype=float) * 30.0,
        "window_end": np.arange(4, dtype=float) * 30.0 + 30.0,
        "reference_count": 3,
        "state_for_estimator": np.array([[0.0], [1.0], [1.0]]),
    }
    _rows, summaries = _candidate_rows(
        data,
        np.array([0, 1, 2], dtype=np.int32),
        np.array([[0, 1]], dtype=np.int32),
        np.array([[0.0, 1.0]], dtype=float),
        np.array([0], dtype=np.int32),
    )
    assert summaries[0]["kth_distance_tie_ambiguous"] is True


def test_settings_reject_fractional_integer_and_missing_required_values():
    base = {
        "neighborhood_k": 20,
        "min_samples": 30,
        "min_neighborhood_samples": 10,
        "max_gap_sec": None,
        "max_dt_relative_deviation": 0.05,
        "min_valid_fraction": 0.1,
        "psd_floor": 1e-8,
    }
    fractional = dict(base, neighborhood_k=20.9)
    with pytest.raises(ValueError, match="neighborhood_k"):
        _settings({"settings": fractional})
    missing = dict(base)
    del missing["min_valid_fraction"]
    with pytest.raises(ValueError, match="seven"):
        _settings({"settings": missing})
