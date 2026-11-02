"""Paired Cohen dz, BH, and within-subject aggregation. No real H5 outcomes."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ds04511_panel import (
    CONTRAST_BY_ID,
    CONTRASTS,
    METRIC_BY_ID,
    METRICS,
    QC_ONLY_METRIC_IDS,
    SUBSTANTIVE_METRIC_IDS,
    metric_test_scope,
)
from ds04511_stats import bh_fdr, cohens_dz, exact_sign_test_p, friedman_p
from ds04511_task_part1 import (
    contrast_row,
    friedman_rows,
    paired_differences,
    reduce_series,
    subject_task_table,
)


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


def test_sign_test_rejects_all_negative_differences():
    p = exact_sign_test_p([-1.0] * 12)
    assert p < 0.001


def test_friedman_detects_consistent_task_order():
    rest = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    cc = np.array([2.0, 2.0, 2.0, 2.0, 2.0, 2.0])
    gg = np.array([3.0, 3.0, 3.0, 3.0, 3.0, 3.0])
    chi2, p_value, n = friedman_p(rest, cc, gg)
    assert n == 6
    assert chi2 > 0
    assert p_value < 0.05


def test_subject_task_takes_median_of_repeated_recordings():
    recordings = pd.DataFrame(
        [
            {
                "subject_id": "sub-S200116",
                "task_label": "rest",
                "h1_h2_support_included": True,
                "occupancy_m_included": True,
                "occupancy_m_median": 2.0,
            },
            {
                "subject_id": "sub-S200116",
                "task_label": "rest",
                "h1_h2_support_included": True,
                "occupancy_m_included": True,
                "occupancy_m_median": 4.0,
            },
        ]
    )
    for spec in METRICS:
        if spec.metric_id == "occupancy_m":
            continue
        recordings[f"{spec.metric_id}_included"] = False
        recordings[f"{spec.metric_id}_median"] = np.nan
    table = subject_task_table(recordings)
    assert np.isclose(table.loc[0, "occupancy_m"], 3.0)


def test_paired_difference_is_gg_minus_rest_not_run_order():
    subjects = pd.DataFrame(
        [
            {"subject_id": "sub-S200116", "task_label": "rest", "occupancy_m": 10.0},
            {"subject_id": "sub-S200116", "task_label": "gambling", "occupancy_m": 7.0},
        ]
    )
    contrast = CONTRAST_BY_ID["gambling_minus_rest"]
    paired = paired_differences(subjects, contrast, "occupancy_m")
    assert paired.loc[0, "difference"] == -3.0
    row = contrast_row(paired, METRIC_BY_ID["occupancy_m"], contrast)
    assert row["median_paired_difference"] == -3.0
    assert row["n_negative"] == 1


def test_reduce_series_tensor_norms_and_occupancy_column():
    identities = np.stack([np.eye(3), 2.0 * np.eye(3)])
    frob = reduce_series(identities, "frobenius")
    assert frob.shape == (2,)
    assert np.allclose(frob, [np.sqrt(3.0), 2.0 * np.sqrt(3.0)])
    vecs = np.array([[3.0, 4.0], [0.0, 1.0]])
    assert np.allclose(reduce_series(vecs, "l2"), [5.0, 1.0])
    coords = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    assert np.allclose(reduce_series(coords, None, column=0), [1.0, 4.0])
    assert np.allclose(reduce_series(coords, None, column=2), [3.0, 6.0])


def test_panel_keeps_occupancy_mnj_l1_reach_and_omits_gated_layers():
    ids = [spec.metric_id for spec in METRICS]
    assert len(ids) == len(set(ids))
    assert "occupancy_m" in ids
    assert "jacobian_spectral_abscissa" in ids
    assert "diffusion_total" in ids
    assert "reach_d_eff" in ids
    assert {spec.level for spec in METRICS} == {"occupancy", "mnj", "L1", "L4"}
    for omitted in ("destination", "resilience", "committor"):
        assert omitted not in ids
    assert [c.contrast_id for c in CONTRASTS] == [
        "gambling_minus_rest",
        "cognitive_control_minus_rest",
        "gambling_minus_cognitive_control",
    ]


def test_level_panel_keeps_lag1_and_omits_empty_identities():
    from ds04511_level_panel import LEVEL_METRICS

    ids = [spec.metric_id for spec in LEVEL_METRICS]
    assert len(ids) == len(set(ids))
    assert "jacobian_alpha" in ids
    assert "one_step_phi_frob" in ids
    assert "one_step_spectral_abscissa" in ids
    assert {spec.level for spec in LEVEL_METRICS} == {"jacobian_alpha", "L2", "L3"}
    for omitted in ("lag2", "destination", "resilience", "occupancy_m", "reach_a_q"):
        assert omitted not in ids


def test_d_eff_near_one_is_flagged_as_degenerate():
    from ds04511_l4_qc import d_eff_report

    values = pd.Series([1.0, 1.0 + 1e-12, 1.0 - 1e-10, np.nan])
    report = d_eff_report(values)
    assert report["n_finite"] == 3
    assert report["n_near_one"] == 3
    assert report["near_one_fraction"] == 1.0


def test_reachability_d_eff_is_retained_but_qc_only():
    assert metric_test_scope("reach_d_eff") == "qc_only_degenerate"
    assert QC_ONLY_METRIC_IDS == {"reach_d_eff"}
    assert "reach_d_eff" not in SUBSTANTIVE_METRIC_IDS

    subjects = []
    for index in range(6):
        row = {"subject_id": f"sub-{index:03d}", "task_label": "rest"}
        for spec in METRICS:
            row[spec.metric_id] = float(index)
        subjects.append(row)
        for task, offset in (("cognitive_control", 1.0), ("gambling", 2.0)):
            row = {"subject_id": f"sub-{index:03d}", "task_label": task}
            for spec in METRICS:
                row[spec.metric_id] = float(index) + offset
            subjects.append(row)
    table = friedman_rows(pd.DataFrame(subjects), METRICS)
    qc = table.loc[table["metric"] == "reach_d_eff"].iloc[0]
    substantive = table.loc[table["metric"] == "occupancy_m"].iloc[0]
    assert qc["test_scope"] == "qc_only_degenerate"
    assert np.isfinite(qc["friedman_p"])
    assert pd.isna(qc["bh_q"])
    assert substantive["test_scope"] == "substantive"
    assert np.isfinite(substantive["bh_q"])


def test_contrast_row_retains_raw_d_eff_test_with_qc_scope():
    subjects = pd.DataFrame(
        [
            {"subject_id": "sub-1", "task_label": "rest", "reach_d_eff": 1.0},
            {"subject_id": "sub-1", "task_label": "gambling", "reach_d_eff": 1.1},
        ]
    )
    contrast = CONTRAST_BY_ID["gambling_minus_rest"]
    paired = paired_differences(subjects, contrast, "reach_d_eff")
    row = contrast_row(paired, METRIC_BY_ID["reach_d_eff"], contrast)
    assert row["test_scope"] == "qc_only_degenerate"
    assert np.isfinite(row["wilcoxon_p"])
