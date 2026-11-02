from __future__ import annotations

import json

import pandas as pd

from nmd_analysis.v3_audit import audit_tables, write_audit


def test_support_counts_preserve_unknown_and_subject_grain(tmp_path):
    table = tmp_path / "windows.parquet"
    pd.DataFrame({
        "subject_id": ["s1", "s1", "s1", "s2"],
        "source_h5": ["a.h5", "a.h5", "b.h5", "c.h5"],
        "table_grain": ["window"] * 4,
        "stage": ["n2", "n2", "rem", "n2"],
        "coordinate_contract": ["subject_anchored"] * 4,
        "finite_ok": [True, False, None, True],
        "not_testable": [False, True, None, False],
        "measurement_validity": ["not_assessed"] * 4,
    }).to_parquet(table)
    audit = audit_tables({"diffusion_geometry_window": table})
    counts = audit["tables"]["diffusion_geometry_window"]
    assert counts["n_rows"] == 4
    assert counts["n_subjects_identified"] == 2
    assert counts["n_recordings_identified"] == 3
    assert counts["finite_ok"] == {"true": 2, "false": 1, "unknown": 1}
    assert {row["stage"] for row in counts["strata"]} == {"n2", "rem"}
    assert audit["scientific_qualification"] == "not_assessed"
    assert audit["claim_status"] == "no_biological_claim"


def test_audit_preserves_extraction_failures(tmp_path):
    paths = write_audit({"dataset": "demo", "written_files": {},
                         "errors": ["invalid_schema"], "skipped": ["no_rows"]}, tmp_path)
    report = json.loads((tmp_path / "v3_support_audit.json").read_text())
    assert report["extraction_complete"] is False
    assert report["extraction_errors"] == ["invalid_schema"]
    assert report["extraction_skipped"] == ["no_rows"]
    assert "manifest" in paths


def test_audit_does_not_merge_coordinate_contracts(tmp_path):
    table = tmp_path / "recordings.parquet"
    pd.DataFrame({"subject_id": ["s1", "s2"], "table_grain": ["recording"] * 2,
                  "coordinate_contract": ["subject_anchored", "cohort_anchored"]}).to_parquet(table)
    strata = audit_tables({"recordings": table})["tables"]["recordings"]["strata"]
    assert len(strata) == 2
