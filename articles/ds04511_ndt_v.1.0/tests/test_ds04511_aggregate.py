"""G2 inclusion and synthetic aggregation. No real task contrasts."""
from __future__ import annotations

import numpy as np

from ds04511_aggregate import (
    inferential_units,
    paired_subject_difference,
    recording_median,
    sign_test_denominator,
)
from ds04511_g2_support import _h1h2_inclusion


def test_nan_and_gaps_are_not_filled_with_zero():
    values = np.array([1.0, np.nan, 3.0, 5.0])
    valid = np.array([1, 1, 0, 1])
    result = recording_median(values, valid, min_n=2, min_frac=0.4)
    assert result["n_valid"] == 2
    assert result["median"] == 3.0
    assert result["missing_filled_with_zero"] is False


def test_insufficient_support_keeps_median_undefined():
    values = np.ones(10)
    valid = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    result = recording_median(values, valid, min_n=30, min_frac=0.5)
    assert result["included"] is False
    assert not np.isfinite(result["median"])


def test_psd_floor_exclusion_is_a_sensitivity_mask_not_zero_imputation():
    values = np.arange(40, dtype=float)
    valid = np.ones(40)
    floor = np.zeros(40)
    floor[:20] = 1
    full = recording_median(values, valid, min_n=30, min_frac=0.5)
    excluded = recording_median(values, valid, min_n=30, min_frac=0.5, extra_exclude=floor)
    assert full["included"] is True
    assert excluded["included"] is False
    assert not np.isfinite(excluded["median"])


def test_zero_differences_leave_the_table_but_not_the_sign_denominator():
    zero = paired_subject_difference(2.0, 2.0)
    pos = paired_subject_difference(1.0, 2.0)
    missing = paired_subject_difference(float("nan"), 1.0)
    assert zero["difference"] == 0.0
    assert zero["testable"] is False
    assert pos["sign"] == -1
    assert missing["testable"] is False
    counts = sign_test_denominator([0.0, -1.0, 2.0, np.nan])
    assert counts["n_zero"] == 1
    assert counts["n_nonzero"] == 2
    assert counts["n_positive"] == 1
    assert counts["n_negative"] == 1


def test_broadcast_one_step_operator_is_one_observation():
    assert inferential_units(grain="recording", n_rows=96, broadcast_recording_operator=False) == 1
    assert inferential_units(grain="window", n_rows=96, broadcast_recording_operator=True) == 1
    assert inferential_units(grain="window", n_rows=96, broadcast_recording_operator=False) == 96


def test_h1h2_inclusion_requires_computed_and_support_counts():
    ok = _h1h2_inclusion(
        computation_status="computed",
        support_status="sufficient",
        n_exported=96,
        n_valid=80,
        n_valid_no_psd_floor=80,
    )
    assert ok["h1_h2_support_included"] is True
    blocked = _h1h2_inclusion(
        computation_status="computed",
        support_status="insufficient",
        n_exported=96,
        n_valid=80,
        n_valid_no_psd_floor=80,
    )
    assert blocked["h1_h2_support_included"] is False
