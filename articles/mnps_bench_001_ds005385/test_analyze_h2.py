from __future__ import annotations

import math

import numpy as np
import pytest

import analyze_h2 as h2


@pytest.mark.parametrize("starts", [
    [0.0, 4.5, 9.0], [0.0, 3.5, 7.0], [0.0, 0.0], [4.0, 0.0],
    [0.0, float("nan")], [0.0, float("inf")],
])
def test_h2_rejects_invalid_cadence_before_derivatives(starts):
    starts = np.asarray(starts)
    with pytest.raises(ValueError, match="H2"):
        h2.compute_mnj_series(np.ones((len(starts), 4)), starts, starts + h2.WINDOW_SEC,
                              projection=None, jacobian_module=None)


def test_h2_accepts_regular_segments_with_gap_and_roundoff():
    h2._validate_h2_time_grid(np.asarray([0.0, 4.0 + 1e-8, 12.0, 16.0]))
    with pytest.raises(ValueError, match="window grid"):
        h2._validate_h2_time_grid(np.asarray([0.0, 4.0]), np.asarray([4.0, 8.5]))
    with pytest.raises(ValueError, match="intervals"):
        h2._validate_h2_time_grid(np.asarray([0.0, 4.0]), np.asarray([4.0, np.nan]))


def test_matrix_mnj_metrics_match_known_matrix() -> None:
    matrix = np.diag([4.0, 2.0, 1.0, 0.5])
    result = h2.matrix_mnj_metrics(matrix)

    assert math.isclose(result["mnj_frobenius_norm"], math.sqrt(21.25))
    assert result["mnj_antisymmetric_frobenius_norm"] == 0.0
    assert math.isclose(result["mnj_symmetric_frobenius_norm"], math.sqrt(21.25))
    assert result["mnj_singular_value_anisotropy"] == 8.0


def test_candidate_value_requires_one_finite_computed_valid_scalar() -> None:
    valid = [{"candidate_id": "M1", "computed": True, "valid": True, "value": [2.5]}]
    assert h2._candidate_value(valid, "M1") == 2.5
    assert h2._candidate_value([{**valid[0], "computed": False}], "M1") is None
    assert h2._candidate_value([{**valid[0], "value": [1.0, 2.0]}], "M1") is None
    assert h2._candidate_value([{**valid[0], "value": [float("nan")]}], "M1") is None


def test_trajectory_splits_at_missing_windows_and_large_jumps() -> None:
    class Projection:
        ROBUST_MAD_TO_SIGMA = 1.4826

    values = np.column_stack([np.arange(40.0)] * 4)
    values[24:] += 1000.0
    starts = np.arange(40.0) * h2.STEP_SEC
    starts[4:] += h2.STEP_SEC  # a missing interval forces a hard segment boundary
    segments = h2._trajectory_segments(
        values,
        starts,
        projection=Projection,
    )
    assert [segment.tolist() for segment in segments] == [
        list(range(4)), list(range(4, 24)), list(range(24, 40)),
    ]


def test_mnj_synthetic_series_emits_supported_metrics_and_keeps_short_series_missing() -> None:
    projection, jacobian = h2.load_nmd_kernels()
    t = np.arange(96, dtype=np.float64) * h2.STEP_SEC
    phase = t / 31.0
    values = np.column_stack(
        [
            np.sin(phase),
            np.cos(t / 37.0),
            np.sin(t / 23.0 + np.sin(t / 101.0)),
            np.cos(t / 19.0 + 0.2 * np.sin(t / 83.0)),
        ]
    )
    starts = t
    ends = starts + h2.WINDOW_SEC
    features, support = h2.compute_mnj_series(
        values,
        starts,
        ends,
        projection=projection,
        jacobian_module=jacobian,
    )

    assert len(support) == len(h2.MNJ_FEATURES)
    assert all(row["attempted_center_count"] > 30 for row in support)
    assert all(row["finite_jacobian_center_count"] > 30 for row in support)
    assert all(row["support_pass"] for row in support)
    assert all(np.isfinite(features[name]) for name in h2.MNJ_FEATURES)

    short_features, short_support = h2.compute_mnj_series(
        values[:24],
        starts[:24],
        ends[:24],
        projection=projection,
        jacobian_module=jacobian,
    )
    assert all(math.isnan(short_features[name]) for name in h2.MNJ_FEATURES)
    assert all(not row["support_pass"] for row in short_support)
