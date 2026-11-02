"""Synthetic support/missingness checks for the fixed-prefix L1 pilot."""
from __future__ import annotations

import h5py
import numpy as np

from ds04511_l1_duration_robustness import fixed_prefix_metric
from ds04511_panel import METRIC_BY_ID


def _write_l1_h5(path, values, valid=None, *, metric="diffusion_total"):
    spec = METRIC_BY_ID[metric]
    with h5py.File(path, "w") as handle:
        handle.create_dataset(spec.value_path, data=np.asarray(values))
        if valid is not None:
            handle.create_dataset(spec.valid_path, data=np.asarray(valid))


def test_fixed_prefix_uses_exported_validity_and_keeps_missing_values(tmp_path):
    path = tmp_path / "valid.h5"
    _write_l1_h5(path, [1.0, 2.0, np.nan, 4.0, 5.0, 6.0], [1, 1, 0, 1, 1, 1])
    result = fixed_prefix_metric(path, METRIC_BY_ID["diffusion_total"], n_windows=6, min_valid_n=3)
    assert result["fixed_diffusion_total_included"] is True
    assert result["fixed_diffusion_total_n_valid"] == 5
    assert np.isclose(result["fixed_diffusion_total_median"], 4.0)


def test_fixed_prefix_rejects_missing_or_mismatched_validity(tmp_path):
    missing = tmp_path / "missing_valid.h5"
    _write_l1_h5(missing, [1.0] * 6, valid=None)
    result = fixed_prefix_metric(missing, METRIC_BY_ID["diffusion_total"], n_windows=6, min_valid_n=3)
    assert result["fixed_diffusion_total_included"] is False
    assert result["fixed_diffusion_total_reason"] == "missing_validity_series"

    mismatch = tmp_path / "mismatch_valid.h5"
    _write_l1_h5(mismatch, [1.0] * 6, valid=[1, 1, 1])
    result = fixed_prefix_metric(mismatch, METRIC_BY_ID["diffusion_total"], n_windows=6, min_valid_n=3)
    assert result["fixed_diffusion_total_included"] is False
    assert result["fixed_diffusion_total_reason"] == "validity_length_mismatch"


def test_fixed_prefix_rejects_short_and_zero_support_prefix(tmp_path):
    short = tmp_path / "short.h5"
    _write_l1_h5(short, [1.0] * 5, valid=[1] * 5)
    result = fixed_prefix_metric(short, METRIC_BY_ID["diffusion_total"], n_windows=6, min_valid_n=3)
    assert result["fixed_diffusion_total_included"] is False
    assert result["fixed_diffusion_total_reason"] == "shorter_than_fixed_prefix"

    invalid = tmp_path / "invalid.h5"
    _write_l1_h5(invalid, [1.0] * 6, valid=[0] * 6)
    result = fixed_prefix_metric(invalid, METRIC_BY_ID["diffusion_total"], n_windows=6, min_valid_n=3)
    assert result["fixed_diffusion_total_included"] is False
    assert result["fixed_diffusion_total_reason"] == "insufficient_fixed_prefix_support"
