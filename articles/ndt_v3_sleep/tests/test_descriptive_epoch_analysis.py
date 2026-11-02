from pathlib import Path

import numpy as np
import pandas as pd

from descriptive_epoch_analysis import eligibility, run


def _frame():
    rows = []
    for i in range(5):
        row = {"window_id": i, "epoch_id": i + 10, "timestamp": 15 + i * 30,
               "window_start": i * 30.0, "window_end": i * 30.0 + 30.0,
               "stage_code": [0, 0, 1, 99, 1][i], "stage_label": ["Wake", "Wake", "N1", None, "N1"][i],
               "stage_label_status": ["recorded", "recorded", "recorded", "missing_or_unknown", "recorded"][i],
               "time_gap_before": False, "window_overlap_before": False}
        row.update({"producer_mask_coverage_ok": [1, 1, 1, np.nan, 1][i],
                    "producer_mask_retained_after_qc": 1,
                    "producer_mask_geometry_valid": 1,
                    "producer_mask_coords_9d_valid": 1})
        for j, c in enumerate(["m", "d", "e"]): row[f"mnps_3d_{c}"] = float(i + j)
        for j, c in enumerate(["m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"]): row[f"mnps_9d_{c}"] = float(i + j)
        rows.append(row)
    return pd.DataFrame(rows)


def test_unknown_stage_and_nan_mask_are_excluded_but_visible():
    frame = _frame()
    eligible, reasons = eligibility(frame, "3d")
    assert eligible.tolist() == [True, True, True, False, True]
    assert bool(reasons.loc[3, "coverage_ok"]) is False
    assert frame.loc[3, "stage_label_status"] == "missing_or_unknown"


def test_run_reports_fixed_boundary_diagnostic_without_stage_purity_claim(tmp_path):
    table = tmp_path / "epoch.parquet"
    _frame().to_parquet(table, index=False)
    manifest = run(table, tmp_path / "out")
    assert manifest["stage_purity_status"] == "not_assessed"
    trajectory = pd.read_csv(tmp_path / "out" / "epoch_trajectory.csv")
    assert trajectory["eligible_3d"].sum() == 4
    boundary = pd.read_csv(tmp_path / "out" / "boundary_diagnostic_3d.csv")
    assert set(boundary["diagnostic_status"]) == {"not_assessed"}
    assert (tmp_path / "out" / "coordinate_summary_3d.csv").is_file()
