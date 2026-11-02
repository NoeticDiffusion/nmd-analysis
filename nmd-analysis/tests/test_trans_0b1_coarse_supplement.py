"""Nonprimary tests for the corrected TRANS-0B1 coarse replay."""

from __future__ import annotations

import numpy as np

from nmd_analysis.dynamical_families import trans_0b1 as base
from nmd_analysis.dynamical_families import trans_0b1_coarse_supplement as supplement


def test_fine_replay_matches_frozen_simulator_exactly() -> None:
    seed = np.random.SeedSequence([base.ROOT_ENTROPY, 0, 0, 0])
    pair = supplement.simulate_owned_coarse_pair(
        base.STARTS[0], n_paths=64, seed=seed, horizon=16 * base.FINE_DT
    )
    reference = base.simulate_terminal_events(
        base.STARTS[0], n_paths=64,
        seed=np.random.SeedSequence([base.ROOT_ENTROPY, 0, 0, 0]),
        dt=base.FINE_DT, horizon=16 * base.FINE_DT,
    )
    assert supplement.compare_fine_to_primary(pair, reference)["matches"]


def test_coarse_owns_drift_step_and_aggregated_noise() -> None:
    seed = np.random.SeedSequence([base.ROOT_ENTROPY, 0, 0, 1])
    pair = supplement.simulate_owned_coarse_pair(
        base.STARTS[1], n_paths=256, seed=seed, horizon=16 * base.FINE_DT
    )
    assert pair["coarse"]["dt"] == base.COARSE_DT
    assert pair["coarse_from_fine_stride"] == 4
    assert pair["coarse_update"].startswith("own Euler drift")
    assert pair["fine"]["terminal_state_checksum"] != pair["coarse"]["terminal_state_checksum"]


def test_zero_noise_uses_distinct_fine_and_coarse_euler_matrices(monkeypatch) -> None:
    monkeypatch.setattr(supplement.np.linalg, "cholesky", lambda _: np.zeros((2, 2)))
    pair = supplement.simulate_owned_coarse_pair(
        base.STARTS[0], n_paths=1, seed=0
    )
    identity = np.eye(2)
    fine_matrix = np.linalg.matrix_power(identity + base.J * base.FINE_DT, 512)
    coarse_matrix = np.linalg.matrix_power(identity + base.J * base.COARSE_DT, 128)
    fine_expected = base.STARTS[0] @ fine_matrix.T
    coarse_expected = base.STARTS[0] @ coarse_matrix.T
    assert np.allclose(pair["fine"]["terminal_mean"], fine_expected)
    assert np.allclose(pair["coarse"]["terminal_mean"], coarse_expected)
    assert not np.allclose(fine_expected, coarse_expected)


def test_rejects_nonintegral_coarse_ratio() -> None:
    try:
        supplement.simulate_owned_coarse_pair(
            base.STARTS[0], n_paths=4, seed=0, fine_dt=1 / 256,
            coarse_dt=1 / 192, horizon=1,
        )
    except ValueError as error:
        assert "integer multiple" in str(error)
    else:
        raise AssertionError("non-integral coarse ratio was accepted")
