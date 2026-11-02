import numpy as np
import pytest

from nmd_analysis.dynamical_families.drift import DriftContractError, crossfit_local_chart_b


def _trajectory(n=40):
    t = np.arange(n, dtype=float) * 0.1
    x = np.zeros((n, 2), dtype=float)
    for i in range(n - 1):
        x[i + 1] = x[i] + 0.1 * np.array([1.0 + 0.2 * x[i, 0], -0.5])
    return x, t


def test_crossfit_provenance_and_disjoint_indices():
    x, t = _trajectory()
    result = crossfit_local_chart_b(x, t, np.arange(0, 10), np.arange(20, 30), n_neighbors=5)
    assert result.b_hat.shape == (10, 2)
    assert result.provenance["candidate_status"] == "candidate_not_qualified"
    assert result.provenance["claim_status"] == "no_biological_claim"
    assert result.provenance["train_evaluation_overlap"] == []
    assert len(result.provenance["b_hat_hash"]) == 64
    assert result.provenance["evaluation_increment_indices"] == list(range(20, 30))


def test_embargo_and_irregular_dt_fail_closed():
    x, t = _trajectory()
    with pytest.raises(DriftContractError, match="embargo"):
        crossfit_local_chart_b(x, t, [0, 1, 2], [3], embargo=0.2)
    t[10] += 0.01
    with pytest.raises(DriftContractError, match="irregular dt"):
        crossfit_local_chart_b(x, t, np.arange(0, 10), np.arange(20, 25))


def test_evaluation_increment_perturbation_does_not_change_fitted_b():
    x, t = _trajectory()
    train = np.arange(0, 10)
    evaluation = np.array([20])
    first = crossfit_local_chart_b(x, t, train, evaluation, n_neighbors=5)
    changed = x.copy()
    changed[evaluation + 1] += 100.0
    second = crossfit_local_chart_b(changed, t, train, evaluation, n_neighbors=5)
    np.testing.assert_allclose(first.b_hat, second.b_hat)


def test_known_constant_drift_sanity():
    t = np.arange(30, dtype=float) * 0.2
    x = np.cumsum(np.tile([0.2, -0.1], (30, 1)), axis=0)
    result = crossfit_local_chart_b(x, t, np.arange(0, 10), np.arange(20, 25), n_neighbors=4)
    np.testing.assert_allclose(result.b_hat, np.tile([1.0, -0.5], (5, 1)))


def test_overlap_and_insufficient_support_refuse():
    x, t = _trajectory()
    with pytest.raises(DriftContractError, match="overlap"):
        crossfit_local_chart_b(x, t, [0, 1, 2], [2, 3])
    with pytest.raises(DriftContractError, match="insufficient"):
        crossfit_local_chart_b(x, t, [0, 1], [10], min_train_support=3)
