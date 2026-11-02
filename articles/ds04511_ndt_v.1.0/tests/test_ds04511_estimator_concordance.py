"""Synthetic checks for common-support estimator concordance."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ds04511_estimator_concordance import concordance_table, sign_agreement


def test_sign_agreement_excludes_zero_directions():
    agreeing, denominator, proportion = sign_agreement([1.0, -1.0, 0.0], [2.0, -3.0, 4.0])
    assert (agreeing, denominator) == (2, 2)
    assert proportion == 1.0


def test_concordance_uses_only_complete_common_pairs():
    frame = pd.DataFrame(
        [
            {"contrast_id": "gambling_minus_rest", "chart_task_difference": 1.0, "l3_task_difference": 2.0, "common_complete": True},
            {"contrast_id": "gambling_minus_rest", "chart_task_difference": -1.0, "l3_task_difference": -2.0, "common_complete": True},
            {"contrast_id": "gambling_minus_rest", "chart_task_difference": 4.0, "l3_task_difference": np.nan, "common_complete": False},
        ]
    )
    table = concordance_table(frame)
    row = table[table["contrast_id"] == "gambling_minus_rest"].iloc[0]
    assert row["n_subject_pairs"] == 2
    assert row["sign_agree_n"] == 2
    assert row["sign_nonzero_n"] == 2
    assert np.isclose(row["spearman_rho"], 1.0)
