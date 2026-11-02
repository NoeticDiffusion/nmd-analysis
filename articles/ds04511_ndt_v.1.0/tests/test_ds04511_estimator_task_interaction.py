"""Synthetic checks for estimator-by-task interaction semantics."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ds04511_estimator_task_interaction import (
    _sign_flip_p,
    interaction_pairs,
    interaction_results,
    robust_location_scale,
)


def test_robust_calibration_is_outcome_blind_and_deterministic():
    calibration = robust_location_scale([1.0, 2.0, 3.0, 100.0])
    assert calibration["method"] == "median_1.4826_mad"
    assert calibration["center"] == 2.5
    assert calibration["scale"] > 0


def test_sign_flip_is_reproducible_and_detects_consistent_interaction():
    values = np.full(12, 1.0)
    assert _sign_flip_p(values, n_permutations=2000, seed=17) <= 0.01
    assert _sign_flip_p(values, n_permutations=2000, seed=17) == _sign_flip_p(
        values, n_permutations=2000, seed=17
    )


def test_interaction_uses_only_common_subject_task_support():
    subjects = pd.DataFrame(
        [
            {"subject_id": "s1", "task_label": "rest", "jacobian_alpha_z": 0.0, "one_step_spectral_abscissa_z": 0.0},
            {"subject_id": "s1", "task_label": "gambling", "jacobian_alpha_z": 1.0, "one_step_spectral_abscissa_z": 0.5},
            {"subject_id": "s2", "task_label": "rest", "jacobian_alpha_z": 0.0, "one_step_spectral_abscissa_z": 0.0},
            {"subject_id": "s2", "task_label": "gambling", "jacobian_alpha_z": 1.0, "one_step_spectral_abscissa_z": np.nan},
        ]
    )
    pairs = interaction_pairs(subjects)
    gg_rest = pairs[pairs["contrast_id"] == "gambling_minus_rest"]
    assert len(gg_rest) == 2
    assert int(gg_rest["common_complete"].sum()) == 1
    result = interaction_results(pairs)
    row = result[result["contrast_id"] == "gambling_minus_rest"].iloc[0]
    assert row["n_subject_pairs"] == 1
