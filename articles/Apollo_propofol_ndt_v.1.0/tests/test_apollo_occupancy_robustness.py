"""Synthetic contract tests for the isolated Apollo occupancy robustness branch."""
from __future__ import annotations

import numpy as np
import pandas as pd

from apollo_c3_match import baseline_center_scale
from apollo_occupancy_robustness import (
    IQR_NORMAL_CONSISTENCY,
    SCALE_VARIANTS,
    VARIANT_REFERENCE,
    _contrast_rows,
    _phase_row,
    _scale_alternative,
    reference_reproduction,
)
from apollo_c3_panel import SPECTRAL_FEATURES


def test_alternative_scales_are_baseline_only_and_finite():
    baseline = np.arange(32.0).reshape(4, 8)
    for variant in SCALE_VARIANTS:
        scale = _scale_alternative(baseline, variant)
        assert scale.shape == (8,)
        assert np.isfinite(scale).all()
        assert np.all(scale > 0)
    assert IQR_NORMAL_CONSISTENCY > 1.0


def test_phase_variants_reuse_reference_eligibility_and_decompose_radius():
    baseline = np.array(
        [[1, 2, 3, 4, 5, 6, 7, 8], [2, 3, 4, 5, 6, 7, 8, 9], [3, 2, 5, 4, 7, 6, 9, 8], [2, 1, 4, 3, 6, 5, 8, 7]],
        dtype=float,
    )
    later = baseline + 2.0
    centre, mad_scale = baseline_center_scale(baseline)
    scales = {variant: _scale_alternative(baseline, variant) for variant in SCALE_VARIANTS}
    variants, contributions, audit = _phase_row(
        subject_id="sub-test",
        phase="first_protocol_sedation",
        source_h5="synthetic.h5",
        raw=later,
        time=np.array([0.0, 4.0, 8.0, 12.0]),
        centre=centre,
        reference_scale=mad_scale,
        alternative_scales=scales,
    )
    assert audit["reference_status"] == "ok"
    assert audit["n_reference_eligible"] == 3
    by_variant = {row["variant"]: row for row in variants}
    assert by_variant[VARIANT_REFERENCE]["status"] == "ok"
    assert by_variant[VARIANT_REFERENCE]["n_variant_finite"] == audit["n_reference_eligible"]
    for feature in SPECTRAL_FEATURES:
        assert by_variant[f"loo_{feature}"]["status"] == "ok"
    shares = pd.DataFrame(contributions).groupby("feature")["mean_squared_share"].mean()
    assert np.isclose(float(shares.sum()), 1.0)


def test_missing_reference_rows_are_not_rescued():
    baseline = np.arange(48.0).reshape(6, 8)
    centre, mad_scale = baseline_center_scale(baseline[np.isfinite(baseline).all(axis=1)])
    scales = {variant: _scale_alternative(baseline[np.isfinite(baseline).all(axis=1)], variant) for variant in SCALE_VARIANTS}
    later = baseline + 2.0
    later[2, 3] = np.nan
    variants, _, audit = _phase_row(
        subject_id="sub-test",
        phase="first_protocol_sedation",
        source_h5="synthetic.h5",
        raw=later,
        time=np.arange(6.0) * 4.0,
        centre=centre,
        reference_scale=mad_scale,
        alternative_scales=scales,
    )
    assert audit["n_reference_eligible"] == 3
    assert all(row["n_reference_eligible"] == 3 for row in variants)
    assert all(row["n_variant_finite"] == 3 for row in variants)


def test_time_gap_is_excluded_by_reference_mask_for_all_variants():
    baseline = np.arange(48.0).reshape(6, 8)
    centre, mad_scale = baseline_center_scale(baseline)
    scales = {variant: _scale_alternative(baseline, variant) for variant in SCALE_VARIANTS}
    later = baseline + 2.0
    variants, _, audit = _phase_row(
        subject_id="sub-test",
        phase="first_protocol_sedation",
        source_h5="synthetic.h5",
        raw=later,
        time=np.array([0.0, 4.0, 8.0, 12.5, 16.5, 20.5]),
        centre=centre,
        reference_scale=mad_scale,
        alternative_scales=scales,
    )
    assert audit["n_reference_eligible"] == 4
    assert all(row["n_reference_eligible"] == 4 for row in variants)
    assert all(row["n_variant_finite"] == 4 for row in variants)


def test_contrast_summary_is_participant_level():
    rows = []
    for subject, baseline, later in (("s1", 1.0, 3.0), ("s2", 2.0, 1.0)):
        for phase, value in (("pre_drug_baseline", baseline), ("first_protocol_sedation", later), ("later_protocol_sedation", later), ("recovery", baseline)):
            rows.append({"variant": "full_mad", "subject_id": subject, "phase": phase, "occupancy": value})
    contrasts = _contrast_rows(pd.DataFrame(rows))
    first = contrasts[contrasts["phase"] == "first_protocol_sedation"].iloc[0]
    assert first["n_pairs"] == 2
    assert first["n_positive"] == 1
    assert first["n_negative"] == 1
    assert bool(first["participant_unit"])


def test_reference_reproduction_reports_exact_match(tmp_path):
    frozen = pd.DataFrame(
        [
            {
                "subject_id": "s1",
                "occupancy_pre_drug_baseline": 1.0,
                "occupancy_first_protocol_sedation": 2.0,
                "occupancy_later_protocol_sedation": np.nan,
                "occupancy_recovery": 1.5,
            }
        ]
    )
    frozen_path = tmp_path / "occupancy_subject.csv"
    frozen.to_csv(frozen_path, index=False)
    current = pd.DataFrame(
        [
            {"subject_id": "s1", "phase": "pre_drug_baseline", "variant": "full_mad", "occupancy": 1.0, "status": "ok"},
            {"subject_id": "s1", "phase": "first_protocol_sedation", "variant": "full_mad", "occupancy": 2.0, "status": "ok"},
            {"subject_id": "s1", "phase": "recovery", "variant": "full_mad", "occupancy": 1.5, "status": "ok"},
        ]
    )
    table, summary = reference_reproduction(current, frozen_path)
    assert len(table) == 3
    assert summary["n_expected_cells"] == 3
    assert summary["n_compared_cells"] == 3
    assert summary["max_abs_diff"] == 0.0
    assert summary["pass"] is True
