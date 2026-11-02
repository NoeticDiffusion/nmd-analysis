import hashlib
from pathlib import Path

import h5py
import pytest
import yaml

from src import epoch_support


def _config(path: Path, *, leaf_name: str | None = None) -> Path:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    source = {"h5": str(path), "sha256": digest, "expected_h5_count": 1}
    if leaf_name is not None:
        source["leaf_name"] = leaf_name
    config = path.parent / "config.yaml"
    config.write_text(yaml.safe_dump({"source": source}), encoding="utf-8")
    return config


def test_configured_non99_leaf_passes_leaf_gate_before_schema_validation(tmp_path):
    source = tmp_path / "sub-42_Sleep_acq-psg.h5"
    with h5py.File(source, "w"):
        pass
    config = _config(source, leaf_name=source.name)
    with pytest.raises(ValueError, match="missing or nonnumeric /time"):
        epoch_support.run_epoch_export(source, tmp_path / "out", config)


def test_default_sub99_leaf_remains_backward_compatible(tmp_path):
    source = tmp_path / epoch_support.SOURCE_LEAF
    with h5py.File(source, "w"):
        pass
    config = _config(source)
    with pytest.raises(ValueError, match="missing or nonnumeric /time"):
        epoch_support.run_epoch_export(source, tmp_path / "out", config)
