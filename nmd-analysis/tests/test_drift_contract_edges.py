import numpy as np
import pytest

from nmd_analysis.dynamical_families.drift import DriftContractError, crossfit_local_chart_b


def _trajectory(n=80, dimension=3):
    time = np.arange(n, dtype=float) * 0.2
    index = np.arange(n, dtype=float)
    if dimension == 3:
        trajectory = np.column_stack(
            (
                np.sin(0.23 * index) + 0.01 * index,
                np.cos(0.17 * index) + 0.02 * np.sin(0.07 * index),
                0.35 * np.sin(0.11 * index + 0.4) + 0.015 * index,
            )
        )
    else:
        trajectory = np.column_stack((index, 2.0 * index))
    return trajectory, time


def _call(x, t, train, evaluation, **kwargs):
    return crossfit_local_chart_b(
        x,
        t,
        np.asarray(train, dtype=np.int64),
        np.asarray(evaluation, dtype=np.int64),
        **kwargs,
    )


@pytest.mark.parametrize("estimator", ["local_mean", "local_linear"])
def test_evaluation_target_isolation(estimator):
    x, t = _trajectory()
    train = np.arange(0, 32)
    # Separated targets keep each perturbed x[i+1] out of the next
    # evaluation current-state set.
    evaluation = np.arange(60, 68, 2)
    first = _call(x, t, train, evaluation, estimator=estimator, n_neighbors=8, min_train_support=4)
    changed = x.copy()
    changed[evaluation + 1] += np.array([100.0, -75.0, 50.0])
    second = _call(changed, t, train, evaluation, estimator=estimator, n_neighbors=8, min_train_support=4)
    np.testing.assert_array_equal(first.b_hat, second.b_hat)


def test_rank_deficient_linear_fit_refuses_explicitly():
    x, t = _trajectory(dimension=2)
    with pytest.raises(DriftContractError, match="insufficient local rank"):
        _call(x, t, np.arange(0, 32), np.arange(60, 64), estimator="local_linear", n_neighbors=8, min_train_support=4)


def test_nonfinite_input_and_irregular_dt_refuse():
    x, t = _trajectory()
    x[4, 1] = np.nan
    with pytest.raises(DriftContractError, match="finite array"):
        _call(x, t, np.arange(0, 32), np.arange(60, 64))
    x, t = _trajectory()
    t[12] += 0.01
    with pytest.raises(DriftContractError, match="irregular dt"):
        _call(x, t, np.arange(0, 32), np.arange(60, 64))


def test_insufficient_support_and_increment_overlap_refuse():
    x, t = _trajectory()
    with pytest.raises(DriftContractError, match="insufficient training support"):
        _call(x, t, [0, 1], [60], min_train_support=3)
    with pytest.raises(DriftContractError, match="overlap"):
        _call(x, t, [0, 1, 2], [2, 3], min_train_support=1)


def test_shared_endpoint_raw_support_and_embargo_refuse():
    x, t = _trajectory()
    with pytest.raises(DriftContractError, match="embargo"):
        _call(x, t, [0], [1], n_neighbors=1, min_train_support=1, embargo=0.0)
    with pytest.raises(DriftContractError, match="embargo"):
        _call(
            x,
            t,
            [5],
            [10],
            n_neighbors=1,
            min_train_support=1,
            train_window_support=np.asarray([[0.8, 1.4]]),
            evaluation_window_support=np.asarray([[1.4, 2.4]]),
        )
    with pytest.raises(DriftContractError, match="embargo"):
        _call(x, t, [0], [4], n_neighbors=1, min_train_support=1, embargo=0.7)


def test_noncontiguous_increment_gap_is_explicit_and_not_bridged():
    x, t = _trajectory()
    result = _call(
        x,
        t,
        [0, 2, 4, 6],
        [60],
        n_neighbors=4,
        min_train_support=3,
        embargo=0.0,
    )
    assert np.isfinite(result.b_hat).all()
    assert result.provenance["train_increment_indices"] == [0, 2, 4, 6]


def test_finite_huge_values_must_fail_closed_before_nonfinite_b_hat():
    x, t = _trajectory()
    huge = np.full_like(x, 1.0e308)
    huge[1::2] = -1.0e308
    with pytest.raises(DriftContractError, match="overflow|finite"):
        _call(huge, t, np.arange(0, 32), np.arange(60, 64), n_neighbors=8, min_train_support=4)
