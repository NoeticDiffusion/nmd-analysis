from __future__ import annotations

import json

import h5py
import numpy as np
import pandas as pd
import pytest
import yaml
from typer.testing import CliRunner

from nmd_analysis.cli import app
from nmd_analysis.pipeline import run_dataset_pipeline


def _pilot(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    with h5py.File(source / "demo.h5", "w") as h5:
        h5.attrs.update(subject_id="s1", dataset="demo", modality="eeg",
                        primary_coordinate_contract="subject_anchored",
                        primary_coordinate_layer="coords_3d_subject_anchored")
        h5.create_dataset("time", data=np.arange(4.0))
        h5.create_dataset("epoch_id", data=np.arange(4))
        h5.create_dataset("labels/stage", data=np.array([2, 2, 4, 4]))
        g = h5.create_group("dynamical_families/diffusion/v1")
        for name, value in {
            "schema_version": "mndm.diffusion_geometry.v1",
            "computation_status": "computed", "measurement_validity": "not_assessed",
            "claim_status": "no_biological_claim", "grain/native": "window",
            "grain/parent": "recording", "grain/biological_unit": "subject",
            "grain/repeated_measure": "true", "grain/direct_between_subject_inference": "forbidden",
            "provenance/coordinate_layer": "coords_3d_subject_anchored",
        }.items():
            g.create_dataset(name, data=value)
        g.create_dataset("series/a_hat", data=np.tile(np.eye(3), (4, 1, 1)))
        g.create_dataset("series/diffusion_tensor", data=np.tile(np.eye(3), (4, 1, 1)))
        g.create_dataset("series/valid", data=np.ones(4, dtype=bool))
        g.create_dataset("series/A_bD", data=np.full(4, np.nan))
        g.create_dataset("series/d_diff", data=np.full(4, 3.0))
        g.create_dataset("summary/n_timepoints", data=4)
        g.create_dataset("summary/A_bD_computation_status", data="not_testable")
    config = tmp_path / "pilot.yaml"
    config.write_text(yaml.safe_dump({
        "dataset": "demo", "coordinate_contract": "subject_anchored",
        "runtime": {"workers": 1},
        "analyses": {name: True for name in (
            "dynamical_families_availability", "diffusion_geometry_recording",
            "diffusion_geometry_window", "destination_recording", "resilience_recording")},
    }), encoding="utf-8")
    return source, config


def test_v3_cli_extraction_and_audit_roundtrip(tmp_path):
    source, config = _pilot(tmp_path)
    output = tmp_path / "out"
    result = CliRunner().invoke(app, ["v3-audit", "--config", str(config),
                                    "--input-root", str(source), "--output-root", str(output)])
    assert result.exit_code == 0, result.output + repr(result.exception)
    manifest = json.loads((output / "v3_extraction_manifest.json").read_text())
    windows = pd.read_parquet(manifest["written_files"]["diffusion_geometry_window"])
    assert len(windows) == 4
    assert set(windows["table_grain"]) == {"window"}
    assert windows["A_bD"].isna().all()
    assert len(windows.iloc[0]["a_hat"]) == 9
    audit = json.loads((output / "v3_support_audit.json").read_text())
    assert audit["extraction_complete"] is True
    assert audit["tables"]["diffusion_geometry_window"]["n_subjects_identified"] == 1
    missing = pd.read_parquet(manifest["written_files"]["destination_recording"])
    assert missing["not_testable"].all()


def test_missing_input_never_defaults_to_working_directory(tmp_path):
    _, config = _pilot(tmp_path)
    with pytest.raises(ValueError, match="No input root"):
        run_dataset_pipeline(config)
