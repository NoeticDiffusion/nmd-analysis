"""Synthetic checks for the duration/support sensitivity helpers."""
from __future__ import annotations

import h5py
import numpy as np

from ds04511_duration_robustness import fixed_prefix_median


def test_fixed_prefix_preserves_missingness_and_support(tmp_path):
    path = tmp_path / "sample.h5"
    with h5py.File(path, "w") as handle:
        handle.create_dataset(
            "jacobian/derived_metrics/v1/series/spectral_abscissa",
            data=np.array([1.0, 2.0, np.nan, 4.0, 5.0, 6.0]),
        )
    included = fixed_prefix_median(path, n_windows=6, min_valid_n=3, min_valid_fraction=0.5)
    assert included["included"] is True
    assert included["n_valid"] == 5
    assert np.isclose(included["jacobian_alpha_fixed_median"], 4.0)

    too_short = fixed_prefix_median(path, n_windows=7, min_valid_n=3, min_valid_fraction=0.5)
    assert too_short["included"] is False
    assert too_short["reason"] == "shorter_than_fixed_prefix"


def test_fixed_prefix_does_not_fill_nan(tmp_path):
    path = tmp_path / "all_missing.h5"
    with h5py.File(path, "w") as handle:
        handle.create_dataset(
            "jacobian/derived_metrics/v1/series/spectral_abscissa",
            data=np.array([np.nan, np.nan, np.nan, np.nan]),
        )
    result = fixed_prefix_median(path, n_windows=4, min_valid_n=1, min_valid_fraction=0.5)
    assert result["included"] is False
    assert result["n_valid"] == 0
    assert not np.isfinite(result["jacobian_alpha_fixed_median"])
