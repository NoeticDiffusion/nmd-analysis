from pathlib import Path

import h5py
import numpy as np
import pytest

from sleep_pilot import _read_stage_audit, run_pilot


VERIFIED_SOURCE = Path(
    r"H:\SourceRepo2\NeuralManifoldDynamics\project\v3\ds005555_float64_verified_20260906\ds005555\neuralmanifolddynamics_ds005555_20260906_064207\sub-99_Sleep_acq-psg\sub-99_Sleep_acq-psg.h5"
)


def _write_fixture(path: Path, *, mismatch: bool = False, unknown_stage: bool = True) -> None:
    n = 4
    with h5py.File(path, "w") as h:
        h.attrs["dataset_id"] = "ds005555"
        h.attrs["subject_id"] = "sub-99"
        h.create_dataset("time", data=np.arange(n, dtype=float) * 30.0 + 15.0)
        h.create_dataset("epoch_id", data=np.arange(n, dtype=np.int32))
        h.create_dataset("window_start", data=np.arange(n, dtype=float) * 30.0)
        h.create_dataset("window_end", data=np.arange(1, n + 1, dtype=float) * 30.0)
        stage = np.asarray([0, 1, 8 if unknown_stage else 2, 2], dtype=np.int8)
        h.create_dataset("labels/stage", data=stage)
        h.create_dataset("codebooks/stage/codes", data=np.asarray([-1, 0, 1, 2], dtype=np.int32))
        h.create_dataset("codebooks/stage/labels", data=np.asarray([b"L", b"W", b"N1", b"N2"]))
        group = h.create_group("dynamical_families/diffusion/v1")
        for key, value in {
            "schema_version": "mndm.diffusion_geometry.v1",
            "computation_status": "computed",
            "measurement_validity": "not_assessed",
            "claim_status": "no_biological_claim",
        }.items():
            group.create_dataset(key, data=np.bytes_(value))
        group.create_dataset("grain/native", data=np.bytes_("window"))
        group.create_dataset("grain/parent", data=np.bytes_("recording"))
        group.create_dataset("provenance/coordinate_layer", data=np.bytes_("coords_3d_subject_anchored"))
        group.create_dataset("series/a_hat", data=np.repeat(np.eye(2)[None], n, axis=0))
        group.create_dataset("series/valid", data=np.ones(n, dtype=np.int8))
        group.create_dataset("summary/n_valid", data=n)
        rows = [{"finite_ok": True} for _ in range(n if not mismatch else n - 1)]
    return rows


def test_unknown_stage_is_retained_and_not_zero(tmp_path):
    path = tmp_path / "sub-99_Sleep_acq-psg.h5"
    _write_fixture(path)
    diffusion_rows = [
        {"window_id": index, "timestamp": index * 30.0 + 15.0, "finite_ok": True}
        for index in range(4)
    ]
    rows = _read_stage_audit(path, diffusion_rows)
    assert rows[2]["stage_label"] is None
    assert rows[2]["stage_label_status"] == "missing_or_unknown"
    assert rows[2]["recording_wq_used_as_stage"] is False


def test_mismatched_family_rows_fail_closed(tmp_path):
    path = tmp_path / "sub-99_Sleep_acq-psg.h5"
    _write_fixture(path)
    with pytest.raises(ValueError, match="alignment mismatch"):
        _read_stage_audit(path, [{"finite_ok": True}] * 3)


def test_pilot_fresh_output_and_missing_families_are_explicit(tmp_path):
    path = tmp_path / "sub-99_Sleep_acq-psg.h5"
    _write_fixture(path)
    output = tmp_path / "pilot"
    manifest = run_pilot(path, output)
    assert manifest["n_windows"] == 4
    assert manifest["family_availability"][1]["available"] is False
    assert manifest["stage_contract"]["recording_wq_used_as_stage"] is False
    with pytest.raises(FileExistsError):
        run_pilot(path, output)


@pytest.mark.skipif(not VERIFIED_SOURCE.is_file(), reason="verified reference H5 unavailable")
def test_verified_source_has_exact_stage_time_and_diffusion_support():
    with h5py.File(VERIFIED_SOURCE, "r") as handle:
        n = len(handle["/time"])
        assert n == len(handle["/labels/stage"]) == len(handle["/epoch_id"])
        assert n == len(handle["/window_start"]) == len(handle["/window_end"])
        assert handle["/dynamical_families/diffusion/v1/series/a_hat"].shape[0] == n
