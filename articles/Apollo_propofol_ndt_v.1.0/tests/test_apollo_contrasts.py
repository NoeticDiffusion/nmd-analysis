"""Paired Cohen dz, BH, and within-subject aggregation. No real H5 outcomes."""
from __future__ import annotations

import numpy as np
import pandas as pd

from apollo_panel import CONTRASTS
from apollo_stage_part1 import contrast_row, paired_differences, subject_phase_table
from apollo_stats import bh_fdr, cohens_dz, exact_sign_test_p, holm


def test_cohens_dz_is_mean_over_sd_of_paired_differences():
    constant = np.array([2.0, 2.0, 2.0, 2.0])
    assert not np.isfinite(cohens_dz(constant))
    varied = np.array([-1.0, 0.0, 1.0, 2.0])
    assert np.isclose(cohens_dz(varied), np.mean(varied) / np.std(varied, ddof=1))


def test_bh_fdr_is_monotone_and_clips():
    q = bh_fdr([0.001, 0.01, 0.04, 0.20])
    assert np.all(np.diff(q) >= -1e-15)
    assert q[-1] <= 1.0
    assert q[0] <= q[1]


def test_holm_of_two_primary_pvalues():
    adjusted = holm([0.01, 0.04])
    assert adjusted[0] == 0.02
    assert adjusted[1] == 0.04


def test_sign_test_rejects_all_negative_differences():
    p = exact_sign_test_p([-1.0] * 12)
    assert p < 0.001


def test_subject_phase_takes_median_of_repeated_recordings():
    recordings = pd.DataFrame(
        [
            {
                "subject_id": "sub-002",
                "protocol_phase_label": "pre_drug_baseline",
                "h1_h2_support_included": True,
                "diffusion_total_included": True,
                "diffusion_total_median": 2.0,
                "diffusion_effective_dimension_included": True,
                "diffusion_effective_dimension_median": 1.0,
            },
            {
                "subject_id": "sub-002",
                "protocol_phase_label": "pre_drug_baseline",
                "h1_h2_support_included": True,
                "diffusion_total_included": True,
                "diffusion_total_median": 4.0,
                "diffusion_effective_dimension_included": True,
                "diffusion_effective_dimension_median": 3.0,
            },
        ]
    )
    for spec_id in (
        "R_b_over_a",
        "A_bD",
        "diffusion_concentration",
        "neighbor_gain_q90",
        "operator_max_gain_rate",
        "history_predictive_gain",
        "jacobian_spectral_abscissa",
        "jacobian_trace",
        "jacobian_rotation_norm",
        "jacobian_reactivity_gap",
        "turning_rate",
        "ftr_g_max_h1",
        "ftr_g_max_h2",
    ):
        recordings[f"{spec_id}_included"] = False
        recordings[f"{spec_id}_median"] = np.nan
    table = subject_phase_table(recordings)
    assert np.isclose(table.loc[0, "diffusion_total"], 3.0)


def test_paired_difference_is_later_minus_earlier_not_run_order():
    subjects = pd.DataFrame(
        [
            {"subject_id": "sub-002", "protocol_phase_label": "pre_drug_baseline", "diffusion_total": 10.0},
            {"subject_id": "sub-002", "protocol_phase_label": "first_protocol_sedation", "diffusion_total": 7.0},
        ]
    )
    contrast = CONTRASTS[0]
    paired = paired_differences(subjects, contrast, "diffusion_total")
    assert paired.loc[0, "difference"] == -3.0
    from apollo_panel import METRIC_BY_ID

    row = contrast_row(paired, METRIC_BY_ID["diffusion_total"], contrast)
    assert row["median_paired_difference"] == -3.0
    assert row["n_negative"] == 1


def test_reduce_series_tensor_norms():
    from apollo_stage_part1 import reduce_series

    identities = np.stack([np.eye(3), 2.0 * np.eye(3)])
    frob = reduce_series(identities, "frobenius")
    assert frob.shape == (2,)
    assert np.allclose(frob, [np.sqrt(3.0), 2.0 * np.sqrt(3.0)])
    vecs = np.array([[3.0, 4.0], [0.0, 1.0]])
    assert np.allclose(reduce_series(vecs, "l2"), [5.0, 1.0])
    cov = np.stack([2.0 * np.eye(3)])
    assert np.allclose(reduce_series(cov, "trace"), [6.0])
    scalars = np.array([1.0, 2.0])
    assert np.allclose(reduce_series(scalars, "frobenius"), [1.0, 2.0])


def test_level_panel_omits_empty_identities():
    from apollo_level_panel import LEVEL_METRICS

    ids = [spec.metric_id for spec in LEVEL_METRICS]
    assert len(ids) == len(set(ids))
    assert "jacobian_alpha" in ids
    assert {spec.level for spec in LEVEL_METRICS} == {"jacobian_alpha", "L1", "L2", "L3"}
    for omitted in ("A_bD", "R_b_over_a", "destination", "resilience"):
        assert omitted not in ids


def test_c3_greedy_match_respects_caliper_and_one_to_one():
    from apollo_c3_match import greedy_match, median_loo_nn, speed_scalar, spread_scalar

    later = np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]])
    earlier = np.array([[0.1, 0.0, 0.0], [0.2, 0.0, 0.0], [10.1, 0.0, 0.0]])
    i, j, d = greedy_match(later, earlier, caliper=0.5)
    pairs = set(zip(i.tolist(), j.tolist()))
    assert pairs == {(0, 0), (1, 2)} or pairs == {(0, 1), (1, 2)}
    assert np.all(d <= 0.5)
    none_i, none_j, none_d = greedy_match(later, earlier, caliper=0.01)
    assert none_i.size == 0 and none_j.size == 0 and none_d.size == 0
    points = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
    assert np.isclose(median_loo_nn(points), 1.0)
    dx = np.array([[3.0, 4.0, 0.0], [0.0, 0.0, 0.0]])
    assert np.isclose(speed_scalar(dx), 2.5)
    spread = spread_scalar(np.array([[1.0, 0.0], [-1.0, 0.0], [1.0, 0.0], [-1.0, 0.0]]))
    assert spread > 0.0


def test_baseline_feature_increments_and_anchor():
    from apollo_c3_match import baseline_center_scale, feature_increments, occupancy_scalar, robust_z

    time = np.array([0.0, 4.0, 8.0, 12.0])
    baseline = np.array([[9.0, 1.0], [10.0, 2.0], [11.0, 1.0], [10.0, 0.0]])
    later = np.array([[20.0, 8.0], [22.0, 9.0], [24.0, 10.0], [26.0, 11.0]])
    center, scale = baseline_center_scale(baseline)
    z_base = robust_z(baseline, center, scale)
    z_later = robust_z(later, center, scale)
    assert np.isfinite(z_base).all()
    assert occupancy_scalar(z_later) > occupancy_scalar(z_base)
    dxdt, valid, dt = feature_increments(z_later, time)
    assert np.all(valid[:3] == 1.0)
    assert valid[3] == 0.0
    assert np.allclose(dt[:3], 4.0)
    assert np.all(dxdt[:3, 0] > 0.0)


def test_occupancy_primary_uses_frozen_anchor_features():
    from apollo_c3_panel import SPECTRAL_FEATURES
    from apollo_occupancy_panel import OCCUPANCY_FEATURES, ORDERED_LATERS, PRIMARY_LATER_PHASE

    assert OCCUPANCY_FEATURES == SPECTRAL_FEATURES
    assert PRIMARY_LATER_PHASE == "first_protocol_sedation"
    assert ORDERED_LATERS == (
        "first_protocol_sedation",
        "later_protocol_sedation",
        "recovery",
    )


def test_chennu_binomial_lor_is_ci_nonoverlap_not_protocol_phase():
    from apollo_lor import lor_status, ror_status

    assert lor_status(40, 39) == "responsive"
    assert lor_status(40, 3) == "lor_impaired"
    assert lor_status(float("nan"), 3) == "missing"
    assert ror_status(40, 39, "lor_impaired") == "returned"
    assert ror_status(40, 3, "lor_impaired") == "not_returned"
    assert ror_status(40, 3, "responsive") == "not_applicable"


def test_independent_cohen_d_and_mannwhitney_sign():
    from apollo_stats import cohens_d, mannwhitney_p

    high = np.array([10.0, 11.0, 12.0, 13.0])
    low = np.array([1.0, 2.0, 3.0, 4.0])
    assert cohens_d(high, low) > 0
    assert mannwhitney_p(high, low) < 0.05
