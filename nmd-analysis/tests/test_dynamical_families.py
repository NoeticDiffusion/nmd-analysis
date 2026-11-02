from pathlib import Path
import h5py
import numpy as np
import pandas as pd
import pytest

from nmd_analysis.dynamical_families import read_family, read_identity
from nmd_analysis.dynamical_families.adapters import (
    collectors,
    diffusion_window_rows,
    family_recording_rows,
    one_step_recording_rows,
)
from nmd_analysis.dynamical_families.schemas import FAMILY_H5_NAME

def _family(
    path: Path,
    root: str = "dynamical_families",
    *,
    series=True,
    status="computed",
    source_idx=None,
    nested_increment=False,
):
    with h5py.File(path, "w") as h:
        h.create_dataset("time", data=np.arange(3, dtype=float))
        h.create_dataset("window_start", data=np.arange(3, dtype=float))
        h.create_dataset("window_end", data=np.arange(3, dtype=float) + 1)
        family_name = "diffusion_geometry" if root == "orthogonal_dynamics" else "diffusion"
        g = h.create_group(f"{root}/{family_name}/v1")
        g.create_dataset("schema_version", data="mndm.diffusion_geometry.v1")
        g.create_dataset("computation_status", data=status)
        g.create_dataset("measurement_validity", data="not_assessed")
        g.create_dataset("provenance/coordinate_layer", data="coords_3d_subject_anchored")
        g.create_dataset("grain/native", data="window")
        if series:
            g.create_dataset("series/a_hat", data=np.tile(np.eye(2), (3, 1, 1)))
            g.create_dataset("series/valid", data=np.ones(3, dtype=np.int8))
            if source_idx is not None:
                g.create_dataset("series/source_idx", data=np.asarray(source_idx, dtype=np.int32))
        if nested_increment:
            nested = g.create_group("increment_covariance_level0")
            nested.create_dataset("schema_version", data="mndm.diffusion_geometry.v1")
            nested.create_dataset("computation_status", data="computed")
            nested.create_dataset("measurement_id", data="increment_covariance_level0")
            nested.create_dataset("qualification_status", data="unconditional_increment_covariance_not_a_hat")
            nested.create_dataset("series/increment_covariance", data=np.tile(np.eye(2), (3, 1, 1)))
            nested.create_dataset("summary/n_timepoints", data=3)

def test_canonical_and_window_rows_are_parquet_safe(tmp_path):
    path = tmp_path / "canonical.h5"
    _family(path)
    payload = read_family(path, "diffusion")
    assert payload["namespace_origin"] == "canonical"
    rows = diffusion_window_rows(path)
    assert len(rows) == 3 and rows[0]["table_grain"] == "window"
    assert rows[0]["coordinate_layer"] if "coordinate_layer" in rows[0] else True
    pd.DataFrame(rows).to_parquet(tmp_path / "rows.parquet")

def test_legacy_and_missing_are_explicit(tmp_path):
    legacy = tmp_path / "legacy.h5"
    _family(legacy, "orthogonal_dynamics")
    assert read_family(legacy, "diffusion")["namespace_origin"] == "legacy_orthogonal_dynamics"
    missing = tmp_path / "missing.h5"
    with h5py.File(missing, "w") as h: h.attrs["dataset_id"] = "x"
    row = family_recording_rows(missing, "destination")[0]
    assert row["computation_status"] == "not_recorded"
    assert row["measurement_validity"] == "not_recorded"

def test_unknown_schema_and_alignment_fail_closed(tmp_path):
    bad = tmp_path / "bad.h5"
    _family(bad)
    with h5py.File(bad, "a") as h: h["dynamical_families/diffusion/v1/schema_version"][...] = "unknown.v9"
    with pytest.raises(ValueError): read_family(bad, "diffusion")
    mis = tmp_path / "mis.h5"
    _family(mis)
    with h5py.File(mis, "a") as h: del h["time"]; h.create_dataset("time", data=np.arange(2))
    with pytest.raises(ValueError): diffusion_window_rows(mis)

def test_nan_a_hat_is_not_zero(tmp_path):
    path = tmp_path / "nan.h5"
    _family(path)
    with h5py.File(path, "a") as h: h["dynamical_families/diffusion/v1/series/a_hat"][0, 0, 0] = np.nan
    row = diffusion_window_rows(path)[0]
    assert row["finite_ok"] is False and np.isnan(row["a_hat"][0])


def test_sibling_certificate_and_source_grain_survive(tmp_path):
    path = tmp_path / "certificate.h5"
    _family(path)
    with h5py.File(path, "a") as h:
        h.attrs["primary_coordinate_contract"] = "subject_anchored"
        g = h["dynamical_families/diffusion/v1"]
        g.create_dataset("claim_status", data="no_biological_claim")
        g.create_dataset("provenance/claim_status", data="different_legacy_token")
        g.create_dataset("grain/biological_unit", data="subject")
    row = family_recording_rows(path, "diffusion")[0]
    assert row["claim_status"] == "no_biological_claim"
    assert row["grain_native"] == "window"
    assert row["grain_biological_unit"] == "subject"
    assert row["grain_parent"] == "not_recorded"
    assert row["table_grain"] == "recording"
    assert row["coordinate_contract"] == "subject_anchored"


def test_valid_mask_and_series_alignment_are_not_guessed(tmp_path):
    path = tmp_path / "mask.h5"
    _family(path)
    with h5py.File(path, "a") as h:
        h["dynamical_families/diffusion/v1/series/valid"][:] = 0
    assert family_recording_rows(path, "diffusion")[0]["not_testable"] is True
    assert all(row["not_testable"] for row in diffusion_window_rows(path))
    with h5py.File(path, "a") as h:
        h.create_dataset("dynamical_families/diffusion/v1/series/A_bD", data=np.ones(2))
    with pytest.raises(ValueError, match="alignment"):
        diffusion_window_rows(path)


def test_source_idx_need_not_match_time_length(tmp_path):
    path = tmp_path / "source_idx.h5"
    _family(path, source_idx=[0, 1])
    rows = diffusion_window_rows(path)
    assert len(rows) == 3
    assert "source_idx" not in rows[0]
    recording = family_recording_rows(path, "diffusion")[0]
    assert recording["source_idx_n"] == 2
    assert recording["source_idx"] == [0, 1]
    pd.DataFrame(rows).to_parquet(tmp_path / "windows.parquet")
    pd.DataFrame([recording]).to_parquet(tmp_path / "recording.parquet")


def test_nested_increment_covariance_is_not_flattened(tmp_path):
    path = tmp_path / "nested.h5"
    _family(path, nested_increment=True)
    payload = read_family(path, "diffusion")
    assert "increment_covariance_level0" not in payload
    recording = family_recording_rows(path, "diffusion")[0]
    assert "increment_covariance_level0" not in recording
    identity = read_identity(path, "diffusion", "increment_covariance_level0")
    assert identity["computation_status"] == "computed"
    assert identity["qualification_status"] == "unconditional_increment_covariance_not_a_hat"
    nested_row = collectors()["diffusion_increment_covariance_recording"](path)[0]
    assert nested_row["identity_id"] == "increment_covariance_level0"
    pd.DataFrame([recording, nested_row]).to_parquet(tmp_path / "nested.parquet")


def test_chart_drift_uses_h5_path_drift_not_chart_drift(tmp_path):
    path = tmp_path / "drift.h5"
    with h5py.File(path, "w") as h:
        h.create_dataset("time", data=np.arange(3, dtype=float))
        g = h.create_group("dynamical_families/drift/v1")
        g.create_dataset("schema_version", data="mndm.chart_drift.v1")
        g.create_dataset("computation_status", data="computed")
        g.create_dataset("qualification_status", data="not_assessed")
        g.create_dataset("measurement_validity", data="not_assessed")
        g.create_dataset("claim_status", data="no_biological_claim")
        pooled = g.create_group("conditional_mean_rate_level1/pooled")
        pooled.create_dataset("schema_version", data="mndm.chart_drift.v1")
        pooled.create_dataset("computation_status", data="computed")
        pooled.create_dataset("qualification_status", data="ito_not_qualified")
        pooled.create_dataset("series/b_hat", data=np.ones((3, 3), dtype=float))
        pooled.create_dataset("series/valid", data=np.ones(3, dtype=np.int8))
        pooled.create_dataset("series/source_idx", data=np.array([0, 1], dtype=np.int32))
        pooled.create_dataset("grain/native", data="window")
        pooled.create_dataset("grain/repeated_measure", data="true")
    assert FAMILY_H5_NAME["chart_drift"] == "drift"
    payload = read_family(path, "chart_drift")
    assert payload["namespace_origin"] == "canonical"
    assert payload["source_dataset_path"] == "/dynamical_families/drift/v1"
    assert "conditional_mean_rate_level1" not in payload
    identity = read_identity(path, "chart_drift", "conditional_mean_rate_level1/pooled")
    assert identity["qualification_status"] == "ito_not_qualified"
    rows = collectors()["chart_drift_conditional_mean_window"](path)
    assert len(rows) == 3
    assert rows[0]["variant_id"] == "pooled"
    assert rows[0]["qualification_status"] == "ito_not_qualified"
    assert "source_idx" not in rows[0]
    pd.DataFrame(rows).to_parquet(tmp_path / "chart_drift.parquet")


def test_one_step_rows_are_recording_grain_not_window_replicates(tmp_path):
    path = tmp_path / "one_step.h5"
    with h5py.File(path, "w") as h:
        h.create_dataset("time", data=np.arange(3, dtype=float))
        g = h.create_group("dynamical_families/one_step/v1")
        g.create_dataset("schema_version", data="mndm.affine_one_step.v1")
        g.create_dataset("computation_status", data="computed")
        g.create_dataset("qualification_status", data="one_step_identified")
        g.create_dataset("measurement_validity", data="not_assessed")
        g.create_dataset("claim_status", data="no_biological_claim")
        leaf = g.create_group("spectral_abscissa_level3")
        leaf.create_dataset("schema_version", data="mndm.affine_one_step.v1")
        leaf.create_dataset("computation_status", data="computed")
        leaf.create_dataset("qualification_status", data="generator_proxy_from_qualified_one_step_not_ito")
        leaf.create_dataset("series/spectral_abscissa", data=np.full(3, -0.2))
        leaf.create_dataset("grain/native", data="recording")
        leaf.create_dataset("grain/repeated_measure", data="false")
        leaf.create_dataset("grain/biological_unit", data="subject")
        leaf.create_dataset("grain/parent", data="recording")
        leaf.create_dataset("grain/direct_between_subject_inference", data="forbidden")
    rows = one_step_recording_rows(path)
    assert "one_step_window" not in collectors()
    abscissa = [row for row in rows if row["identity_id"] == "spectral_abscissa_level3"]
    assert abscissa and all(row["table_grain"] == "recording" for row in abscissa)
    assert abscissa[0]["grain_repeated_measure"] == "false"
    assert abscissa[0]["declared_lag"] == 1
    assert abscissa[0]["qualification_status"] == "generator_proxy_from_qualified_one_step_not_ito"
    pd.DataFrame(rows).to_parquet(tmp_path / "one_step.parquet")


def test_nan_abd_is_not_rewritten_to_zero(tmp_path):
    path = tmp_path / "abd.h5"
    _family(path)
    with h5py.File(path, "a") as h:
        h.create_dataset("dynamical_families/diffusion/v1/series/A_bD", data=np.array([np.nan, np.nan, np.nan]))
    row = diffusion_window_rows(path)[0]
    assert np.isnan(row["A_bD"])
    recording = family_recording_rows(path, "diffusion")[0]
    assert recording["A_bD_finite_fraction"] == 0.0
