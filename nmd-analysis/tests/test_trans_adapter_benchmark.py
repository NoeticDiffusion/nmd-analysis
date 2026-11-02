"""Independent TRANS adapter contract tests; no primary streams or full runs."""
from __future__ import annotations

import copy
import os
from pathlib import Path
import sys

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.stats import binom

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nmd_analysis.dynamical_families import trans_adapter_benchmark as bench


@pytest.fixture
def ingest_root():
    value = os.environ.get("NMD_INGEST_ROOT")
    if not value:
        pytest.skip("Set NMD_INGEST_ROOT for unchanged-ingest adapter integration tests")
    return Path(value)


def packet(paths, labels, *, dt=bench.DT):
    lengths = [len(p) for p in paths]
    return {"reaction": np.concatenate(paths).astype(float),
            "offsets": np.r_[0, np.cumsum(lengths)].astype(np.int64),
            "terminal_labels": np.asarray(labels, dtype=np.int64),
            "path_starts": np.asarray([p[0] for p in paths]),
            "dt": dt, "horizon": (max(lengths)-1)*dt,
            "n_steps": max(lengths)-1, "n_paths": len(paths), "D": .2}


def analytic_q(xs):
    weight = lambda y: np.exp((y**4/4-y*y/2)/.2)
    denominator = quad(weight, -1, 1, epsabs=1e-12)[0]
    return np.asarray([quad(weight, -1, x, epsabs=1e-12)[0]/denominator for x in xs])


def test_real_overshoots_and_replay_are_retained():
    starts = np.resize([-.999, .999], 32)
    first = bench.simulate_paths(starts, seed=991, horizon=8*bench.DT)
    second = bench.simulate_paths(starts, seed=991, horizon=8*bench.DT)
    for key in ("reaction", "offsets", "terminal_labels"):
        np.testing.assert_array_equal(first[key], second[key])
    ends = first["reaction"][first["offsets"][1:]-1]
    resolved = first["terminal_labels"] >= 0
    assert resolved.any() and np.all(np.abs(ends[resolved]) > 1)
    for lo, hi, label in zip(first["offsets"][:-1], first["offsets"][1:], first["terminal_labels"]):
        values = first["reaction"][lo:hi]
        assert np.all(np.abs(values[:-1]) < 1)
        assert int(label) == (0 if values[-1] <= -1 else 1 if values[-1] >= 1 else -1)


def test_packing_resets_time_and_never_joins_paths():
    p = packet([[-.9, -1.03], [.9, 1.04], [0., .1, .2]], [0, 1, -1])
    packed = bench.pack_training(p)
    same = np.diff(packed["segment_id"]) == 0
    np.testing.assert_allclose(np.diff(packed["time"])[same], bench.DT, rtol=0, atol=1e-14)
    assert same.sum() == 4
    np.testing.assert_array_equal(packed["regime_labels"], [-1, 0, -1, 1, -1, -1, -1])
    np.testing.assert_array_equal(packed["time"][p["offsets"][:-1]], 0)
    np.testing.assert_array_equal(packed["reaction_coordinate"], p["reaction"])


@pytest.mark.parametrize("paths,labels", [
    ([[.9, 1.02, -1.02]], [0]),
    ([[-.9, -1.02, -1.04]], [0]),
    ([[0., 1.02]], [-1]),
    ([[0., .2]], [1]),
    ([[0., np.nan]], [-1]),
    ([[-.9, -1.02]], [256]),
    ([[0., .2]], [255]),
])
def test_invalid_terminal_and_nonfinite_packets_are_rejected(paths, labels):
    with pytest.raises(ValueError):
        bench.pack_training(packet(paths, labels))


def test_timestamp_gap_is_not_silently_reconstructed_away(ingest_root):
    packed = bench.pack_training(packet([[0., .1, .2]], [-1]))
    packed["time"][1] += bench.DT/2
    with pytest.raises(ValueError):
        bench.fit_adapter(packed, ingest_root=ingest_root)


def test_nondefault_dt_is_never_relabeled_as_primary(ingest_root):
    p = packet([[0., .1, .2]], [-1], dt=.01)
    try:
        packed = bench.pack_training(p)
    except ValueError:
        return  # Refusal at either boundary is acceptable; silent relabeling is not.
    same = np.diff(packed["segment_id"]) == 0
    np.testing.assert_allclose(np.diff(packed["time"])[same], .01, rtol=0, atol=1e-14)
    with pytest.raises(ValueError):
        bench.fit_adapter(p, ingest_root=ingest_root)


def deterministic_probe_fixture():
    """Unit-only antithetic increments with exact drift mean, never primary data."""
    xs = np.repeat(np.clip(np.linspace(-1, 1, 65), -.999999, .999999), 32)
    noise = np.tile([-1., 1.], xs.size//2)*np.sqrt(.4*bench.DT)
    ys = xs+(xs-xs**3)*bench.DT+noise
    labels = np.where(ys <= -1, 0, np.where(ys >= 1, 1, -1))
    return packet([[x, y] for x, y in zip(xs, ys)], labels)


def test_unchanged_adapter_factor_two_convention_and_segment_order(ingest_root):
    p = deterministic_probe_fixture()
    correct = bench.fit_adapter(p, ingest_root=ingest_root, diffusion_coefficient=.4)
    wrong = bench.fit_adapter(p, ingest_root=ingest_root, diffusion_coefficient=.2)
    assert correct["computation_status"] == wrong["computation_status"] == "computed"
    assert correct["certificate"]["measurement_validity"] == "not_assessed"
    assert correct["certificate"]["claim_status"] == "no_biological_claim"
    truth = analytic_q(bench.STARTS)
    assert np.max(np.abs(bench.predict_grid(correct["q_grid"], bench.STARTS)-truth)) < .001
    assert np.max(np.abs(bench.predict_grid(wrong["q_grid"], bench.STARTS)-truth)) > .025
    pairs = p["reaction"].reshape(-1, 2)[::-1]
    reversed_packet = packet(pairs, p["terminal_labels"][::-1])
    reordered = bench.fit_adapter(reversed_packet, ingest_root=ingest_root)
    np.testing.assert_allclose(reordered["q_grid"], correct["q_grid"], atol=2e-7, rtol=0)
    np.testing.assert_array_equal(reordered["grid_support_count"], correct["grid_support_count"])


def test_missing_grid_support_stays_unavailable(ingest_root):
    p = deterministic_probe_fixture()
    pairs = p["reaction"].reshape(-1, 2)
    keep = np.abs(pairs[:, 0]) > .01  # Delete all source observations in the central bin.
    result = bench.fit_adapter(packet(pairs[keep], p["terminal_labels"][keep]), ingest_root=ingest_root)
    assert result["computation_status"] == "insufficient_support"
    assert result["failure_reason"] == "dense_query_grid_has_under_supported_points"
    assert result["q_grid"] is None


def test_predictions_use_only_the_fitted_grid_and_refuse_extrapolation():
    fitted = analytic_q(np.linspace(-1, 1, 65))
    np.testing.assert_allclose(bench.predict_grid(fitted, bench.STARTS), analytic_q(bench.STARTS))
    with pytest.raises(ValueError):
        bench.predict_grid(fitted, [1.1])
    with pytest.raises(ValueError):
        bench.predict_grid(fitted, [np.nan])


def test_brier_censoring_envelope_matches_all_possible_unresolved_labels():
    p = .2
    counts = {"n_A": 3, "n_B": 2, "n_unresolved": 4, "n_total": 9}
    result = bench.score_counts(p, counts)
    possible = [(3*p*p+2*(1-p)**2+k*p*p+(4-k)*(1-p)**2)/9 for k in range(5)]
    assert result["brier_lower"] == pytest.approx(min(possible))
    assert result["brier_upper"] == pytest.approx(max(possible))
    assert result["p_B_plugin"] == 2/9  # Not 2/5 resolved-only.
    assert bench.score_counts(.5, counts)["brier_lower"] == .25
    assert bench.score_counts(.5, counts)["brier_upper"] == .25
    with pytest.raises(ValueError):
        bench.score_counts(p, {**counts, "n_total": 10})


@pytest.mark.parametrize("a,b,u", [(9, 0, 1), (0, 10, 0), (3, 4, 3)])
def test_heldout_bounds_match_independent_binomial_inversion(a, b, u):
    n, alpha = a+b+u, .05/15
    result = bench.score_counts(.3, {"n_A": a, "n_B": b, "n_unresolved": u, "n_total": n})
    lower = 0 if b == 0 else brentq(lambda p: binom.sf(b-1, n, p)-alpha, 0, 1)
    def upper(k):
        return 1 if k == n else brentq(lambda p: binom.cdf(k, n, p)-alpha, 0, 1)
    assert result["lower_p_B"] == pytest.approx(lower, abs=1e-10)
    assert result["upper_p_not_A"] == pytest.approx(upper(b+u), abs=1e-10)
    assert result["upper_p_unresolved"] == pytest.approx(upper(u), abs=1e-10)


def summary_fixture():
    grid = analytic_q(np.linspace(-1, 1, 65))
    fits = [{"fit_index": i, "convention": c, "computation_status": "computed",
             "diffusion_coefficient": .4 if c == "correct" else .2,
             "q_grid": grid.copy(), "grid_support_count": np.full(65, 32)}
            for i in range(8) for c in ("correct", "wrong_convention")]
    counts = [{"n_A": 6, "n_B": 4, "n_unresolved": 0, "n_total": 10} for _ in range(5)]
    return fits, counts


@pytest.mark.parametrize("seed", [992, 993, 994])
def test_count_only_simulation_preserves_raw_path_rng_sequence(seed):
    starts = np.resize(np.array([-1., -.999, -.25, 0, .25, .999, 1.]), 70)
    raw = bench.simulate_paths(starts, seed=seed, horizon=200*bench.DT)
    counts = bench.simulate_counts(starts, seed=seed, horizon=200*bench.DT)
    assert counts['n_A'] == np.sum(raw['terminal_labels'] == 0)
    assert counts['n_B'] == np.sum(raw['terminal_labels'] == 1)
    assert counts['n_unresolved'] == np.sum(raw['terminal_labels'] == -1)
    assert counts['seed'] == raw['seed']


def test_recovery_verdict_precedence_and_no_missing_value_imputation():
    fits, counts = summary_fixture()
    assert bench.summarize(fits, counts)["recovery_decision"] == "PASS"
    fits[0].update(computation_status="insufficient_support", q_grid=None, failure_reason="test_missing")
    assert bench.summarize(fits, counts)["recovery_decision"] == "INCONCLUSIVE"
    fits[2]["q_grid"] = np.linspace(0, 1, 65)
    assert bench.summarize(fits, counts)["recovery_decision"] == "FAIL"


def test_duplicate_fit_ids_cannot_masquerade_as_eight_independent_fits():
    fits, counts = summary_fixture()
    fits[2]["fit_index"] = 0
    with pytest.raises(ValueError):
        bench.summarize(fits, counts)


@pytest.mark.parametrize("kind", ["nonfinite", "range", "nonmonotone"])
def test_invalid_fitted_curve_cannot_pass(kind):
    fits, counts = summary_fixture()
    if kind == "nonfinite":
        fits[0]["q_grid"][17] = np.nan
    elif kind == "range":
        fits[0]["q_grid"][1] = -.01
    else:
        fits[0]["q_grid"][17] = fits[0]["q_grid"][19]
    try:
        result = bench.summarize(fits, counts)
    except ValueError:
        return
    assert result["recovery_decision"] != "PASS"
