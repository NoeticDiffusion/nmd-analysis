from __future__ import annotations

import h5py
import numpy as np
import pytest

from nmd_analysis.continuous_c3_match_support import _read_current_chart_h5


def _chart_h5(path, *, epochs=(0, 1), anchor_hash="anchor-sha"):
    with h5py.File(path, "w") as h5:
        h5.attrs["meta_participant_id"] = "sub-100"
        h5.attrs["meta_pid"] = 67
        h5.create_dataset("epoch_id", data=np.asarray(epochs, dtype=np.int64))
        h5.create_dataset("window_start", data=np.asarray([30.0 * value for value in epochs], dtype=np.float32))
        h5.create_dataset("window_end", data=np.asarray([30.0 * (value + 1) for value in epochs], dtype=np.float32))
        chart = h5.create_group("coords_3d_cohort_anchored")
        chart.create_dataset("names", data=np.asarray([b"m", b"d", b"e"]))
        chart.create_dataset("values", data=np.ones((len(epochs), 3), dtype=np.float32))
        chart.attrs["anchor_id"] = "fold0-label-free-v2"
        chart.attrs["anchor_hash"] = anchor_hash
        chart.attrs["anchor_source"] = "mndm.fold_split.training_ranges_only"
        chart.attrs["coordinate_contract"] = "cohort_anchored"
        qc = h5.create_group("qc/windows")
        for name in ("geometry_valid", "mnps_3d_valid", "retained_after_qc"):
            qc.create_dataset(name, data=np.ones(len(epochs), dtype=np.int8))
    return path


def test_current_chart_reader_loads_only_qualified_origin_fields(tmp_path):
    path = _chart_h5(tmp_path / "chart.h5")
    frame, evidence = _read_current_chart_h5(
        path,
        expected_bids_subject="sub-100",
        expected_pid="67",
        expected_anchor_id="fold0-label-free-v2",
        expected_anchor_hash="anchor-sha",
    )
    assert list(frame.columns) == [
        "epoch_id", "h5_window_start", "h5_window_end", "m", "d", "e",
        "chart3d_all_finite", "h5_geometry_valid", "h5_mnps_3d_valid",
        "h5_retained_after_qc", "coordinate_qc_valid",
    ]
    assert frame.coordinate_qc_valid.all()
    assert evidence["row_count"] == 2
    assert evidence["selected_chart_payload_sha256"]
    assert evidence["container_sha256"] is None
    with pytest.raises(ValueError, match="file hash differs from frozen support map"):
        _read_current_chart_h5(
            path,
            expected_bids_subject="sub-100",
            expected_pid="67",
            expected_anchor_id="fold0-label-free-v2",
            expected_anchor_hash="anchor-sha",
            expected_file_sha256="wrong-hash",
        )


@pytest.mark.parametrize(
    ("kwargs", "epochs", "message"),
    [
        ({"expected_pid": "68"}, (0, 1), "biological PID mismatch"),
        ({"expected_anchor_hash": "changed"}, (0, 1), "fold anchor"),
        ({}, (0, 0), "duplicate epoch IDs"),
    ],
)
def test_current_chart_reader_fails_closed_on_identity_or_anchor_changes(tmp_path, kwargs, epochs, message):
    path = _chart_h5(tmp_path / "chart.h5", epochs=epochs)
    expected = {
        "expected_bids_subject": "sub-100",
        "expected_pid": "67",
        "expected_anchor_id": "fold0-label-free-v2",
        "expected_anchor_hash": "anchor-sha",
    }
    expected.update(kwargs)
    with pytest.raises(ValueError, match=message):
        _read_current_chart_h5(path, **expected)
