from __future__ import annotations

import importlib.util
from pathlib import Path

import h5py
import numpy as np
import pytest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "articles"
    / "BOAS_sleep_dataset_ndt._v.1.0"
    / "src"
    / "build_all_fold_apply_support_map.py"
)
SPEC = importlib.util.spec_from_file_location("boas_all_fold_support_map", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


def test_apply_ranges_cover_each_complete_window_once() -> None:
    ranges = [
        {"start_sec": 0.0, "end_sec": 60.0},
        {"start_sec": 90.0, "end_sec": 150.0},
    ]
    membership, counts = BUILDER.apply_range_memberships(
        np.array([0.0, 30.0, 90.0, 120.0]),
        np.array([30.0, 60.0, 120.0, 150.0]),
        ranges,
    )
    assert membership.tolist() == [1, 1, 1, 1]
    assert counts == [2, 2]


def test_gap_or_overlapping_manifest_ranges_are_detectable() -> None:
    gap_membership, _ = BUILDER.apply_range_memberships(
        np.array([0.0, 60.0]), np.array([30.0, 90.0]),
        [{"start_sec": 0.0, "end_sec": 30.0}],
    )
    overlap_membership, _ = BUILDER.apply_range_memberships(
        np.array([30.0]), np.array([60.0]),
        [{"start_sec": 0.0, "end_sec": 60.0}, {"start_sec": 30.0, "end_sec": 90.0}],
    )
    assert gap_membership.tolist() == [1, 0]
    assert overlap_membership.tolist() == [2]


def test_copied_yaml_must_be_byte_identical(tmp_path: Path) -> None:
    provided = tmp_path / "provided.yaml"
    copied = tmp_path / "copied.yaml"
    provided.write_text("fold: 2\n", encoding="utf-8")
    copied.write_text("fold: 2\n", encoding="utf-8")
    assert BUILDER.validate_copied_yaml(provided, copied) == BUILDER.sha256_file(provided)
    copied.write_text("fold: 3\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Copied YAML differs"):
        BUILDER.validate_copied_yaml(provided, copied)


def _empty_h5(path: Path) -> h5py.File:
    h5 = h5py.File(path, "w")
    h5.require_group("provenance/event_stage_mapping")
    h5.attrs["stage_codebook"] = "{}"
    return h5


def test_empty_generic_group_label_is_allowed(tmp_path: Path) -> None:
    path = tmp_path / "empty-label.h5"
    with _empty_h5(path) as h5:
        metadata = h5.require_group("features_raw/metadata")
        metadata.create_dataset("group_label", data=np.array(["", ""], dtype=object), dtype=h5py.string_dtype("utf-8"))
        assert BUILDER.validate_label_free_h5(h5, path) == 1


def test_nonblank_group_label_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "nonblank-label.h5"
    with _empty_h5(path) as h5:
        metadata = h5.require_group("features_raw/metadata")
        metadata.create_dataset("group_label", data=np.array(["N2"], dtype=object), dtype=h5py.string_dtype("utf-8"))
        with pytest.raises(RuntimeError, match="Non-empty group-label payload"):
            BUILDER.validate_label_free_h5(h5, path)


def test_unexpected_stage_dataset_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "stage-payload.h5"
    with _empty_h5(path) as h5:
        h5.create_dataset("labels/stage", data=np.array([2], dtype=np.int8))
        with pytest.raises(RuntimeError, match="Unexpected stage/label/event H5 object"):
            BUILDER.validate_label_free_h5(h5, path)


def test_nested_stage_attribute_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "nested-stage-attribute.h5"
    with _empty_h5(path) as h5:
        h5.require_group("features_raw/metadata").attrs["stage_label"] = "N2"
        with pytest.raises(RuntimeError, match="Unexpected stage/label/event H5 object attribute"):
            BUILDER.validate_label_free_h5(h5, path)
