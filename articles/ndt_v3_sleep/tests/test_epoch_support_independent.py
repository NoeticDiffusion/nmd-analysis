"""Independent synthetic checks for the epoch support audit contract."""

from pathlib import Path
import hashlib
import json

import h5py
import numpy as np
import pytest

from sleep_pilot import _read_stage_audit
from epoch_support import run_epoch_export


def _source(tmp_path: Path, *, gap: bool = False, unknown: bool = False, nonfinite: bool = False) -> Path:
    path = tmp_path / "synthetic.h5"
    time = np.array([15.0, 45.0, 75.0, 105.0])
    start = np.array([0.0, 30.0, 60.0, 90.0])
    end = start + 30.0
    if gap:
        # Shift both timestamp and bounds: this is a real interval gap, not a
        # malformed timestamp-only fixture.
        time[2:] += 15.0
        start[2:] += 15.0
        end[2:] += 15.0
    if nonfinite:
        time[1] = np.nan
    stages = np.array([0, 1, 2, 99 if unknown else 3], dtype=np.int64)
    with h5py.File(path, "w") as handle:
        handle["time"] = time
        handle["labels/stage"] = stages
        handle["epoch_id"] = np.arange(4, dtype=np.int64) + 100
        handle["window_start"] = start
        handle["window_end"] = end
        handle["codebooks/stage/codes"] = np.array([0, 1, 2, 3], dtype=np.int64)
        handle["codebooks/stage/labels"] = np.array([b"Wake", b"N1", b"N2", b"N3"])
    return path


def _rows(n: int = 4, *, finite: bool = True, gap: bool = False):
    timestamps = np.array([15.0 + 30.0 * i for i in range(n)])
    if gap:
        timestamps[2:] += 15.0
    return [
        {"window_id": i, "timestamp": float(timestamps[i]), "finite_ok": finite}
        for i in range(n)
    ]


def test_exact_alignment_keeps_stage_purity_unassessed_and_preserves_family_status(tmp_path):
    rows = _read_stage_audit(_source(tmp_path), _rows())
    assert [row["window_id"] for row in rows] == list(range(4))
    assert [row["epoch_id"] for row in rows] == [100, 101, 102, 103]
    assert all(row["stage_purity_status"] == "not_assessed" for row in rows)
    assert all(row["recording_wq_used_as_stage"] is False for row in rows)
    assert all(row["diffusion_finite_ok"] is True for row in rows)


def test_missing_family_identifiers_fail_closed(tmp_path):
    bad = _rows()
    del bad[2]["window_id"]
    with pytest.raises(ValueError, match="identifiers"):
        _read_stage_audit(_source(tmp_path), bad)


def test_nonfinite_time_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="finite"):
        _read_stage_audit(_source(tmp_path, nonfinite=True), _rows())


def test_unknown_stage_code_is_retained_without_purity_upgrade(tmp_path):
    rows = _read_stage_audit(_source(tmp_path, unknown=True), _rows())
    assert rows[-1]["stage_code"] == 99
    assert rows[-1]["stage_label_status"] == "missing_or_unknown"
    assert rows[-1]["stage_label"] is None
    assert rows[-1]["stage_purity_status"] == "not_assessed"


def test_real_gap_is_flagged_and_does_not_bridge_support(tmp_path):
    rows = _read_stage_audit(_source(tmp_path, gap=True), _rows(gap=True))
    assert rows[2]["time_gap_before"] is True
    assert rows[2]["window_overlap_before"] is False
    assert all(row["stage_purity_status"] == "not_assessed" for row in rows)


def _export_fixture(tmp_path: Path, *, nonfinite_coordinate: bool = False,
                    missing_mask: str | None = None, invalid_mask: str | None = None) -> tuple[Path, Path]:
    source = tmp_path / "sub-99_Sleep_acq-psg.h5"
    n = 4
    with h5py.File(source, "w") as handle:
        handle["time"] = np.array([15.0, 45.0, 75.0, 105.0])
        handle["labels/stage"] = np.array([0, 1, 99, 3], dtype=np.int64)
        handle["epoch_id"] = np.arange(n, dtype=np.int64) + 100
        handle["window_start"] = np.arange(n, dtype=float) * 30.0
        handle["window_end"] = np.arange(n, dtype=float) * 30.0 + 30.0
        handle["codebooks/stage/codes"] = np.array([0, 1, 3], dtype=np.int64)
        handle["codebooks/stage/labels"] = np.array([b"Wake", b"N1", b"N3"])
        for dims in (3, 9):
            group = handle.create_group(f"coords_{dims}d_subject_anchored")
            values = np.arange(n * dims, dtype=float).reshape(n, dims)
            if nonfinite_coordinate:
                values[2, 1] = np.nan
            group["values"] = values
            group["names"] = np.asarray(
                ([b"m", b"d", b"e"] if dims == 3 else [f"f{i}".encode() for i in range(dims)])
            )
        for name in ("coverage_ok", "retained_after_qc", "geometry_valid", "coords_9d_valid"):
            if name == missing_mask:
                continue
            if name == invalid_mask:
                handle[f"qc/windows/{name}"] = np.array([0.0, 1.0, 2.0, 1.0])
            elif name == "coverage_ok":
                handle[f"qc/windows/{name}"] = np.array([0.0, 1.0, np.nan, 1.0])
            else:
                handle[f"qc/windows/{name}"] = np.ones(n, dtype=bool)
    config = tmp_path / "config.yaml"
    config.write_text(
        "source:\n"
        f"  h5: {str(source).replace(chr(92), '/')}\n"
        f"  sha256: {hashlib.sha256(source.read_bytes()).hexdigest()}\n"
        "  expected_h5_count: 1\n",
        encoding="utf-8",
    )
    return source, config


def test_actual_exporter_preserves_masks_provenance_unknown_stage_and_nonfinite_values(tmp_path):
    source, config = _export_fixture(tmp_path, nonfinite_coordinate=True)
    manifest = run_epoch_export(source, tmp_path / "out", config)
    assert manifest["status"] == "descriptive_epoch_export"
    assert manifest["source_h5"] == str(source.resolve())
    assert manifest["epoch_alignment"] == "exact_equal_length_and_window_index"
    assert manifest["stage_purity_status"] == "not_assessed"
    assert manifest["feature_filter_full_support"] == "not_assessed"
    assert manifest["diffusion_neighbor_stage_purity"] == "not_assessed"
    assert manifest["checks"]["nonfinite_values_preserved"] is True
    assert manifest["producer_masks"]["status"] == "recorded"
    assert all(item["aligned_first_dimension"] for item in manifest["producer_masks"]["datasets"])
    assert manifest["coordinates"]["3d"]["nonfinite_count"] == 1
    assert manifest["coordinates"]["9d"]["nonfinite_count"] == 1
    exported = json.loads((tmp_path / "out" / "epoch_manifest.json").read_text(encoding="utf-8"))
    assert exported["checks"]["unknown_stage_codes_retained"] is True
    assert exported["recording_wq_exported"] is False
    table = __import__("pandas").read_parquet(tmp_path / "out" / "epoch_coordinates.parquet")
    values = table["producer_mask_coverage_ok"].to_numpy()
    assert values[0] == 0.0 and values[1] == 1.0 and np.isnan(values[2]) and values[3] == 1.0
    assert bool(table.loc[2, "coordinate_finite_3d"]) is False
    assert bool(table.loc[2, "coordinate_finite_9d"]) is False


def test_actual_exporter_rejects_coordinate_name_alignment_error(tmp_path):
    source, config = _export_fixture(tmp_path)
    with h5py.File(source, "r+") as handle:
        del handle["coords_3d_subject_anchored/names"]
        handle["coords_3d_subject_anchored/names"] = np.asarray([b"m", b"d"])
    config_text = config.read_text(encoding="utf-8")
    config.write_text(
        config_text.replace(
            config_text.split("sha256: ", 1)[1].splitlines()[0],
            hashlib.sha256(source.read_bytes()).hexdigest(),
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="coordinate names"):
        run_epoch_export(source, tmp_path / "out", config)


def test_actual_exporter_missing_mask_is_all_null_and_marked_not_recorded(tmp_path):
    source, config = _export_fixture(tmp_path, missing_mask="geometry_valid")
    manifest = run_epoch_export(source, tmp_path / "out", config)
    record = next(item for item in manifest["producer_masks"]["datasets"] if item["path"].endswith("geometry_valid"))
    assert record["status"] == "not_recorded"
    table = __import__("pandas").read_parquet(tmp_path / "out" / "epoch_coordinates.parquet")
    assert table["producer_mask_geometry_valid"].isna().all()


def test_actual_exporter_rejects_bad_mask_values(tmp_path):
    source, config = _export_fixture(tmp_path, invalid_mask="geometry_valid")
    with pytest.raises(ValueError, match="other than 0, 1, or NaN"):
        run_epoch_export(source, tmp_path / "out", config)
