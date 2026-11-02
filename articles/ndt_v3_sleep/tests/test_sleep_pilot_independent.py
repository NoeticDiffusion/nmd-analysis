"""Independent adversarial checks for the article-local sleep pilot."""

from pathlib import Path
import hashlib

import h5py
import numpy as np
import pytest
import yaml

from sleep_pilot import _read_stage_audit, run_pilot


def _fixture(path: Path, *, gap: bool = False, status: str = "computed") -> None:
    n = 4
    time = np.arange(n, dtype=float) * 30.0 + 15.0
    bounds_start = np.arange(n, dtype=float) * 30.0
    bounds_end = np.arange(1, n + 1, dtype=float) * 30.0
    if gap:
        time[2:] += 90.0
        bounds_start[2:] += 90.0
        bounds_end[2:] += 90.0
    with h5py.File(path, "w") as handle:
        handle.create_dataset("time", data=time)
        handle.create_dataset("epoch_id", data=np.arange(n, dtype=np.int32))
        handle.create_dataset("window_start", data=bounds_start)
        handle.create_dataset("window_end", data=bounds_end)
        handle.create_dataset("labels/stage", data=np.array([0, 1, 99, 2], dtype=np.int8))
        handle.create_dataset("codebooks/stage/codes", data=np.array([0, 1, 2], dtype=np.int32))
        handle.create_dataset("codebooks/stage/labels", data=np.array([b"W", b"N1", b"N2"]))
        group = handle.create_group("dynamical_families/diffusion/v1")
        for key, value in {
            "schema_version": "mndm.diffusion_geometry.v1",
            "computation_status": status,
            "measurement_validity": "not_assessed",
            "claim_status": "no_biological_claim",
        }.items():
            group.create_dataset(key, data=np.bytes_(value))
        group.create_dataset("grain/native", data=np.bytes_("window"))
        group.create_dataset("grain/parent", data=np.bytes_("recording"))
        group.create_dataset("series/a_hat", data=np.repeat(np.eye(2)[None], n, axis=0))
        group.create_dataset("series/valid", data=np.ones(n, dtype=np.int8))
        group.create_dataset("summary/n_valid", data=n)


def _diffusion_rows(*, gap: bool = False) -> list[dict[str, object]]:
    time = np.arange(4, dtype=float) * 30.0 + 15.0
    if gap:
        time[2:] += 90.0
    return [{"window_id": i, "timestamp": float(value), "finite_ok": True} for i, value in enumerate(time)]


def test_explicit_source_leaf_gate_rejects_wrong_name(tmp_path: Path) -> None:
    source = tmp_path / "other.h5"
    _fixture(source)

    with pytest.raises(ValueError, match="explicit verified leaf H5"):
        run_pilot(source, tmp_path / "out")


def test_nonempty_output_gate_is_checked_before_reuse(tmp_path: Path) -> None:
    source = tmp_path / "sub-99_Sleep_acq-psg.h5"
    _fixture(source)
    output = tmp_path / "out"
    output.mkdir()
    (output / "sentinel").write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError, match="fresh and empty"):
        run_pilot(source, output)


def test_unknown_stage_code_is_retained_as_unknown_status(tmp_path: Path) -> None:
    source = tmp_path / "sub-99_Sleep_acq-psg.h5"
    _fixture(source)
    rows = _read_stage_audit(source, _diffusion_rows())

    assert rows[2]["stage_code"] == 99
    assert rows[2]["stage_label"] is None
    assert rows[2]["stage_label_status"] == "missing_or_unknown"
    assert rows[2]["recording_wq_used_as_stage"] is False


def test_temporal_gap_is_flagged_without_claiming_stage_purity(tmp_path: Path) -> None:
    source = tmp_path / "sub-99_Sleep_acq-psg.h5"
    _fixture(source, gap=True)

    rows = _read_stage_audit(source, _diffusion_rows(gap=True))

    assert rows[2]["time_gap_before"] is True
    assert rows[2]["stage_purity_status"] == "not_assessed"
    assert rows[2]["recording_wq_used_as_stage"] is False


def test_unknown_family_status_is_preserved_in_manifest(tmp_path: Path) -> None:
    source = tmp_path / "sub-99_Sleep_acq-psg.h5"
    _fixture(source, status="unknown")

    manifest = run_pilot(source, tmp_path / "out")

    assert manifest["families"]["diffusion"]["computation_status"] == "unknown"
    assert manifest["qualification_status"] == "not_assessed"
    assert manifest["claim_status"] == "no_biological_claim"


def test_config_gate_checks_real_leaf_path_and_hash(tmp_path: Path) -> None:
    source = tmp_path / "sub-99_Sleep_acq-psg.h5"
    _fixture(source)
    config = tmp_path / "pilot.yaml"
    config.write_text(yaml.safe_dump({
        "expected_source": {
            "leaf_path": str(source),
            "expected_h5_count": 1,
            "sha256": "0" * 64,
        },
    }), encoding="utf-8")

    with pytest.raises(ValueError, match="SHA-256"):
        run_pilot(source, tmp_path / "out", config)

    assert hashlib.sha256(source.read_bytes()).hexdigest() != "0" * 64
