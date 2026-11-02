"""Contracts for the PR-01 geometric dissection branch."""
import numpy as np

from apollo_pr01_geometric import _phase_summary, _spearman_bootstrap, _whitener


def test_whitener_is_symmetric_and_finite_for_collinear_baseline():
    points = np.column_stack([np.arange(8.0), np.arange(8.0), np.ones(8)])
    whitener = _whitener(points)
    assert whitener.shape == (3, 3)
    assert np.isfinite(whitener).all()
    assert np.allclose(whitener, whitener.T)


def test_phase_summary_separates_centre_and_dispersion():
    points = np.array([[2.0, 0.0], [4.0, 0.0], [6.0, 0.0]])
    summary = _phase_summary(points, np.eye(2))
    assert summary["n_eligible"] == 3
    assert summary["centre_displacement"] == 4.0
    assert summary["within_phase_dispersion"] == 2.0
    assert summary["radial_displacement"] == 4.0


def test_spearman_bootstrap_is_paired_and_deterministic():
    one = _spearman_bootstrap(np.arange(6.0), np.arange(6.0))
    two = _spearman_bootstrap(np.arange(6.0), np.arange(6.0))
    assert one == two
    assert one["n"] == 6
    assert one["rho"] == 1.0
