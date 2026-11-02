from __future__ import annotations

import json
from pathlib import Path

import h5py
import numpy as np
import pytest
import yaml

from diffusion_support_reconstruction import REQUIRED_PRODUCER_FILES, _load_producer, _sha256, run


def _synthetic_h5(path: Path, producer_root: Path, *, corrupt: bool = False) -> None:
    diffusion, _validity = _load_producer(producer_root)
    rng = np.random.default_rng(7)
    x = np.cumsum(rng.normal(size=(36, 3)).astype(np.float32), axis=0)
    time = np.arange(36, dtype=np.float64) * 30.0
    segments = np.zeros(36, dtype=np.int32)
    result = diffusion.estimate_local_diffusion_geometry(
        x, time, segment_id=segments, coordinate_layer="coords_3d_subject_anchored",
        coordinate_names=["m", "d", "e"], neighborhood_k=20, min_samples=30,
        min_neighborhood_samples=10, max_gap_sec=None,
        max_dt_relative_deviation=0.05, psd_floor=1e-8,
    )
    tensor = np.asarray(result["series"]["diffusion_tensor"])
    if corrupt:
        tensor = tensor.copy()
        tensor[0, 0, 0] += np.float32(1.0)
    with h5py.File(path, "w") as handle:
        handle.create_dataset("coords_3d_subject_anchored/values", data=x)
        handle.create_dataset("time", data=time)
        handle.create_dataset("epoch_id", data=np.arange(36, dtype=np.int64))
        handle.create_dataset("window_start", data=time)
        handle.create_dataset("window_end", data=time + 30.0)
        handle.create_dataset("labels/stage", data=np.zeros(36, dtype=np.int8))
        raw = np.asarray(["synthetic.edf"] * 36, dtype=object)
        handle.create_dataset("row_source/raw_file", data=raw, dtype=h5py.string_dtype())
        handle.create_dataset("dynamical_families/diffusion/v1/series/diffusion_tensor", data=tensor)
        handle.create_dataset("dynamical_families/diffusion/v1/series/support_count", data=result["series"]["support_count"])
        handle.create_dataset("dynamical_families/diffusion/v1/series/valid", data=result["series"]["valid"])
        for key, value in result["provenance"]["settings"].items():
            if value is not None:
                handle.create_dataset(f"dynamical_families/diffusion/v1/provenance/settings/{key}", data=value)


@pytest.mark.skipif(not Path("H:/SourceRepo2/NeuralManifoldDynamics/mndm/src").exists(), reason="producer checkout unavailable")
def test_candidate_export_requires_exact_reproduction_gate(tmp_path: Path) -> None:
    producer_root = Path("H:/SourceRepo2/NeuralManifoldDynamics")
    h5_path = tmp_path / "input.h5"
    _synthetic_h5(h5_path, producer_root)
    config = {
        "input_h5": str(h5_path), "producer_root": str(producer_root),
        "output": str(tmp_path / "out"), "producer_git_revision_recorded": "synthetic",
        "input_h5_sha256": _sha256(h5_path),
        "analysis_code": str(Path(__file__).parents[1] / "src" / "diffusion_support_reconstruction.py"),
        "analysis_code_sha256": _sha256(Path(__file__).parents[1] / "src" / "diffusion_support_reconstruction.py"),
        "producer_files": sorted(REQUIRED_PRODUCER_FILES),
        "producer_file_sha256": {relative: _sha256(producer_root / relative) for relative in REQUIRED_PRODUCER_FILES},
        "settings": {"neighborhood_k": 20, "min_samples": 30, "min_neighborhood_samples": 10,
                     "max_gap_sec": None, "max_dt_relative_deviation": 0.05, "min_valid_fraction": 0.1, "psd_floor": 1e-8},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    manifest = run(config_path)
    assert manifest["status"] == "candidate_only_membership_exported"
    assert manifest["gate"]["tensor_exact_after_stored_dtype_cast"] is True
    assert manifest["gate"]["selected_covariance_algebra_exact"] is True
    assert (tmp_path / "out" / "candidate_neighbors.csv").exists()
    assert (tmp_path / "out" / "candidate_query_stage_support.csv").exists()


@pytest.mark.skipif(not Path("H:/SourceRepo2/NeuralManifoldDynamics/mndm/src").exists(), reason="producer checkout unavailable")
def test_gate_failure_writes_no_candidate_membership(tmp_path: Path) -> None:
    producer_root = Path("H:/SourceRepo2/NeuralManifoldDynamics")
    h5_path = tmp_path / "input.h5"
    _synthetic_h5(h5_path, producer_root, corrupt=True)
    config = {
        "input_h5": str(h5_path), "producer_root": str(producer_root),
        "output": str(tmp_path / "out"), "producer_git_revision_recorded": "synthetic",
        "input_h5_sha256": _sha256(h5_path),
        "analysis_code": str(Path(__file__).parents[1] / "src" / "diffusion_support_reconstruction.py"),
        "analysis_code_sha256": _sha256(Path(__file__).parents[1] / "src" / "diffusion_support_reconstruction.py"),
        "producer_files": sorted(REQUIRED_PRODUCER_FILES),
        "producer_file_sha256": {relative: _sha256(producer_root / relative) for relative in REQUIRED_PRODUCER_FILES},
        "settings": {"neighborhood_k": 20, "min_samples": 30, "min_neighborhood_samples": 10,
                     "max_gap_sec": None, "max_dt_relative_deviation": 0.05, "min_valid_fraction": 0.1, "psd_floor": 1e-8},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    manifest = run(config_path)
    assert manifest["status"] == "candidate_only_gate_failed"
    assert not (tmp_path / "out" / "candidate_neighbors.csv").exists()
    assert json.loads((tmp_path / "out" / "gate_report.json").read_text())["gate"]["tensor_exact_after_stored_dtype_cast"] is False
