"""Independent checks for the full-night descriptive wrapper.

These tests exercise the wrapper through the reviewed epoch exporter and stage
dependency audit.  They do not reproduce the coordinate summary algorithm;
they check source identity, temporal geometry, unknown-code handling, and
fail-closed input/configuration behavior.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

import h5py
import numpy as np
import pandas as pd
import pytest

from src.fullnight_stage_description import run_fullnight_description


HERE = Path(__file__).resolve()
STAGING = HERE.parents[1]
CONFIG = STAGING / "config" / "epoch_sub99_fullnight_support_20260910.yaml"
POLICY = Path(r"J:/repos/nmd-analysis/articles/ndt_v3_sleep/stage_dependency_policy_20260910.json")
EPOCH_SUPPORT = Path(r"J:/repos/nmd-analysis/articles/ndt_v3_sleep/src/epoch_support.py")
DESCRIPTIVE = Path(r"J:/repos/nmd-analysis/articles/ndt_v3_sleep/src/descriptive_epoch_analysis.py")


def _source_from_config() -> Path:
    # Avoid a second YAML dependency in the independent test; the pinned
    # source line is deliberately read from the reviewed config.
    for line in CONFIG.read_text(encoding="utf-8").splitlines():
        if line.startswith("  h5:"):
            return Path(line.split(":", 1)[1].strip()).resolve()
    raise AssertionError("pinned H5 path is missing")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _config_for(source: Path, destination: Path, tmp_path: Path) -> Path:
    config = tmp_path / "epoch.yaml"
    config.write_text(
        "source:\n"
        f"  h5: {str(source).replace(chr(92), '/')}\n"
        f"  sha256: {_sha(source)}\n"
        "  expected_h5_count: 1\n"
        "coordinate_contract: subject_anchored\n"
        f"output_root: {str(destination).replace(chr(92), '/')}\n",
        encoding="utf-8",
    )
    return config


def _run(source: Path, destination: Path, tmp_path: Path):
    config = _config_for(source, destination, tmp_path)
    return run_fullnight_description(
        source,
        destination,
        config,
        POLICY,
        epoch_support_path=EPOCH_SUPPORT,
        descriptive_path=DESCRIPTIVE,
    )


def test_real_fullnight_wrapper_preserves_geometry_labels_and_unknown_support(tmp_path):
    source = _source_from_config()
    before = _sha(source)
    result = _run(source, tmp_path / "description", tmp_path)

    assert result["status"] == "descriptive_development_pilot"
    assert result["claim_status"] == "no_biological_claim"
    assert result["n_rows"] == 1068
    assert result["stage_purity_status"] == "not_assessed"
    assert result["scientific_qualification"] == "not_assessed"
    assert result["normalization"] == {
        "scope": "recording_parent_global", "fit_performed": False, "per_stage_fit": False
    }
    counts = {row["stage_code"]: row["n_rows"] for row in result["stage_counts"]}
    assert counts == {0: 275, 1: 20, 2: 642, 3: 15, 4: 107, 8: 9, None: 0}
    assert result["mask_state_counts"]["coverage_ok"] == {
        "true": 1068, "false": 0, "unknown": 0, "invalid": 0
    }
    assert result["stage_dependency_audit"]["result"]["status"] == "audited"
    assert result["stage_dependency_audit"]["result"]["sources"][0]["full_support_status"] == "unknown"
    assert result["stage_dependency_audit"]["result"]["sources"][0]["qualified_increment_count"] is None
    assert result["source"]["sha256_before"] == before == result["source"]["sha256_after"]

    table = pd.read_parquet(tmp_path / "description" / "epoch_coordinates.parquet")
    np.testing.assert_array_equal(table["epoch_id"].to_numpy(), np.arange(1068))
    np.testing.assert_allclose(table["timestamp"].to_numpy(), 15.0 + 30.0 * np.arange(1068))
    np.testing.assert_allclose(table["window_start"].to_numpy(), 30.0 * np.arange(1068))
    np.testing.assert_allclose(table["window_end"].to_numpy(), 30.0 * np.arange(1, 1069))
    assert int((table["stage_code"] == 8).sum()) == 9
    assert (tmp_path / "description" / "fullnight_stage_summary.json").is_file()


def test_wrapper_rejects_tampered_source_pin_before_export(tmp_path):
    source = _source_from_config()
    config = _config_for(source, tmp_path / "bad", tmp_path)
    config.write_text(config.read_text(encoding="utf-8").replace(_sha(source), "0" * 64), encoding="utf-8")
    with pytest.raises(ValueError, match="source SHA mismatch"):
        run_fullnight_description(
            source, tmp_path / "bad", config, POLICY,
            epoch_support_path=EPOCH_SUPPORT, descriptive_path=DESCRIPTIVE,
        )


def test_wrapper_preserves_missing_mask_as_unknown_on_actual_h5(tmp_path):
    source = _source_from_config()
    copied = tmp_path / "sub-99_Sleep_acq-psg.h5"
    shutil.copy2(source, copied)
    with h5py.File(copied, "r+") as handle:
        del handle["qc/windows/coverage_ok"]
    result = _run(copied, tmp_path / "missing_mask", tmp_path)
    assert result["mask_state_counts"]["coverage_ok"] == {
        "true": 0, "false": 0, "unknown": 1068, "invalid": 0
    }
    assert result["mask_state_counts"]["retained_after_qc"]["true"] == 1068
    exported = json.loads((tmp_path / "missing_mask" / "epoch_manifest.json").read_text(encoding="utf-8"))
    coverage = next(item for item in exported["producer_masks"]["datasets"] if item["path"].endswith("coverage_ok"))
    assert coverage["status"] == "not_recorded"
    assert coverage["unknown_count"] == 1068


def test_wrapper_rejects_nonfinite_geometry_via_stage_audit(tmp_path):
    source = _source_from_config()
    copied = tmp_path / "sub-99_Sleep_acq-psg.h5"
    shutil.copy2(source, copied)
    with h5py.File(copied, "r+") as handle:
        handle["time"][10] = np.nan
    with pytest.raises(RuntimeError, match="nonfinite|nonmonotonic"):
        _run(copied, tmp_path / "bad_geometry", tmp_path)
