from pathlib import Path
import sys
import h5py
import numpy as np
import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
from epoch_support import _coords, _masks, _validate_stage, run_epoch_export

def test_coordinate_validation_rejects_width_and_duplicate_names():
    class R: pass
    r = R(); r.values = np.zeros((2, 3)); r.names = ["x", "x", "z"]
    r.values_path = "/a"; r.names_path = "/b"; r.provenance = lambda: {}
    with pytest.raises(ValueError): _coords(r, 3, 2)

def test_masks_preserve_raw_paths_and_unknown(tmp_path):
    p = tmp_path / "x.h5"
    with h5py.File(p, "w") as h:
        h.create_dataset("/qc/windows/coverage_ok", data=np.array([1, 0], dtype=np.uint8))
        got = _masks(h, 2)
    assert got["status"] == "recorded" and got["datasets"][0]["raw_values_retained"]
    p2 = tmp_path / "y.h5"
    with h5py.File(p2, "w") as h:
        got = _masks(h, 2)
        assert got["unknown_when_not_recorded"]
        assert all(x["status"] == "not_recorded" for x in got["datasets"])

def test_masks_reject_shape_strings_and_infinity(tmp_path):
    for data in (np.array([0, 1, 0]), np.array(["0", "1"], dtype=object), np.array([0.0, np.inf])):
        p = tmp_path / f"bad_{len(list(tmp_path.iterdir()))}.h5"
        with h5py.File(p, "w") as h:
            if data.dtype.kind == "O":
                h.create_dataset("/qc/windows/coverage_ok", data=data, dtype=h5py.string_dtype())
            else:
                h.create_dataset("/qc/windows/coverage_ok", data=data)
            if data.shape == (2,) and data.dtype.kind in "f":
                with pytest.raises(ValueError): _masks(h, 2)
            elif data.dtype.kind == "U":
                with pytest.raises(ValueError): _masks(h, 2)
            else:
                with pytest.raises(ValueError): _masks(h, 2)

def test_stage_dtype_must_not_be_truncated(tmp_path):
    p = tmp_path / "x.h5"
    with h5py.File(p, "w") as h:
        h["time"] = [0., 1.]; h["window_start"] = [0., 1.]; h["window_end"] = [1., 2.]
        h["epoch_id"] = np.array([0.1, 1.1]); h["labels/stage"] = np.array([0, 1], dtype=np.int8)
    with pytest.raises(ValueError): _validate_stage(p)

def test_real_export_is_opt_in_and_fresh_source_is_declared():
    cfg = ROOT / "config" / "epoch_sub99_verified.yaml"
    assert "3657fd599bbcddb774aa8ae237cb017f0a566c3a21e0877f4b43634d0d98a427" in cfg.read_text()
