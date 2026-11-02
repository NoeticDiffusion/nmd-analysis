"""Independent regression tests for the frozen descriptive stage policy."""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from descriptive_epoch_analysis import COORDS, MASKS, boundary_diagnostic, coordinate_summary, eligibility, run, stage_counts


def _frame(n: int = 7) -> pd.DataFrame:
    rows = []
    for i in range(n):
        row = {"window_id": i, "epoch_id": i + 100, "timestamp": 15.0 + i * 30.0,
               "window_start": i * 30.0, "window_end": i * 30.0 + 30.0,
               "stage_code": 0, "stage_label": "Wake", "stage_label_status": "recorded",
               "time_gap_before": False, "window_overlap_before": False}
        row.update({name: 1 for name in MASKS.values()})
        row.update({column: float(i + j) for j, column in enumerate(COORDS["3d"])})
        row.update({column: float(i + j) for j, column in enumerate(COORDS["9d"])})
        rows.append(row)
    return pd.DataFrame(rows)


def test_seven_contiguous_known_rows_have_five_two_sided_boundary_neighbors(tmp_path: Path):
    frame = _frame()
    eligible, _ = eligibility(frame, "3d")
    boundary = boundary_diagnostic(frame, "3d", eligible)
    assert int((boundary.left_supported & boundary.right_supported).sum()) == 5
    assert int(boundary.left_supported.sum()) == 6
    assert int(boundary.right_supported.sum()) == 6
    table = tmp_path / "boundary_epoch.parquet"
    frame.to_parquet(table, index=False)
    output = tmp_path / "boundary_review_output"
    manifest = run(table, output)
    summary = pd.read_csv(output / "coordinate_summary_boundary_3d.csv")
    assert manifest["stage_purity_status"] == "not_assessed"
    assert len(summary) == 15
    assert set(summary.loc[summary.stage_code == 0, "n"]) == {5}
    assert set(summary.loc[summary.stage_code.isin([1, 2, 3, 4]), "n"]) == {0}


@pytest.mark.parametrize("break_kind", ["unknown", "gap", "id_jump"])
def test_unknown_gap_or_id_jump_breaks_adjacent_boundary_support(break_kind: str):
    frame = _frame()
    if break_kind == "unknown":
        frame.loc[3, "stage_label_status"] = "missing_or_unknown"
        frame.loc[3, "stage_label"] = np.nan
    elif break_kind == "gap":
        frame.loc[3, "time_gap_before"] = True
        frame.loc[3:, ["window_start", "window_end", "timestamp"]] += 15.0
    else:
        frame.loc[3, "window_id"] = 30
    eligible, _ = eligibility(frame, "3d")
    boundary = boundary_diagnostic(frame, "3d", eligible)
    expected = {"unknown": 2, "gap": 3, "id_jump": 2}[break_kind]
    assert int((boundary.left_supported & boundary.right_supported).sum()) == expected


def test_primary_coordinate_summary_matches_hand_quantiles():
    frame = _frame()
    eligible, _ = eligibility(frame, "3d")
    summary = coordinate_summary(frame, "3d", eligible)
    m = summary.loc[(summary.coordinate == "mnps_3d_m") & (summary.stage_code == 0)].iloc[0]
    assert int(m["n"]) == 7
    assert float(m["median"]) == 3.0
    assert float(m["q1"]) == 1.5
    assert float(m["q3"]) == 4.5
    assert float(m["iqr"]) == 3.0
    assert len(summary) == 15
    assert set(summary["stage_code"]) == {0, 1, 2, 3, 4}


def test_fixed_stage_catalog_keeps_absent_stage_as_zero_nan_summary():
    frame = _frame()
    counts = stage_counts(frame)
    absent = counts.loc[counts.stage_code == 3].iloc[0]
    assert int(absent["n_rows"]) == 0
    eligible, _ = eligibility(frame, "3d")
    summary = coordinate_summary(frame, "3d", eligible)
    absent_summary = summary.loc[summary.stage_code == 3]
    assert len(absent_summary) == 3
    assert (absent_summary["n"] == 0).all()
    assert absent_summary[["median", "q1", "q3", "iqr"]].isna().all().all()


def test_single_coordinate_nan_rejects_only_that_representation_full_vector():
    frame = _frame()
    frame.loc[2, COORDS["3d"][1]] = np.nan
    good3, reasons3 = eligibility(frame, "3d")
    good9, reasons9 = eligibility(frame, "9d")
    assert not bool(good3.iloc[2])
    assert not bool(reasons3.iloc[2].finite_coordinates)
    assert bool(good9.iloc[2])
    assert bool(reasons9.iloc[2].finite_coordinates)


def test_nan_mask_is_unknown_false_for_eligibility_and_visible_in_state():
    frame = _frame()
    frame.loc[2, "producer_mask_coverage_ok"] = np.nan
    good, reasons = eligibility(frame, "3d")
    assert not bool(good.iloc[2])
    assert not bool(reasons.iloc[2].coverage_ok)
    from descriptive_epoch_analysis import _mask_state
    assert _mask_state(frame["producer_mask_coverage_ok"]).iloc[2] == "unknown"


def test_input_config_hash_drift_fails_before_output(tmp_path: Path):
    table = tmp_path / "epoch.parquet"
    _frame().to_parquet(table, index=False)
    config = tmp_path / "config.yaml"
    config.write_text(yaml.safe_dump({"source_table": str(table), "source_table_sha256": "0" * 64,
                                      "analysis_code": "descriptive_epoch_analysis.py",
                                      "analysis_code_sha256": "0" * 64}), encoding="utf-8")
    output = tmp_path / "out"
    with pytest.raises(ValueError, match="(hash|source|config)"):
        run(table, output, config)
    assert not output.exists()




