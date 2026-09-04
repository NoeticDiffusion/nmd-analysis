"""Audit ds004587 export coverage and available physiology/QC surfaces.

Usage: python articles/illusionGame_EAP/src/00_sanity_check.py
"""
from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ds004587_support import (ANCHOR_COLUMNS, QC_COLUMNS, classify_condition,
    load_analysis_table, make_results_subdir, write_metadata)


def main() -> None:
    frame, source = load_analysis_table(("subject_id", "condition"))
    out = make_results_subdir("00_sanity_check")
    frame["analysis_condition"] = frame["condition"].map(classify_condition)
    coverage = (frame.groupby(["subject_id", "condition"]).size()
                .rename("n_rows").reset_index())
    coverage["analysis_condition"] = coverage["condition"].map(classify_condition)
    coverage.to_csv(out / "session_coverage.csv", index=False)
    availability = pd.DataFrame({
        "column": [*ANCHOR_COLUMNS, *QC_COLUMNS],
        "present": [column in frame.columns for column in [*ANCHOR_COLUMNS, *QC_COLUMNS]],
        "nonmissing_fraction": [frame[column].notna().mean() if column in frame else None
                                for column in [*ANCHOR_COLUMNS, *QC_COLUMNS]],
    })
    availability.to_csv(out / "physiology_qc_availability.csv", index=False)
    inclusion = (coverage.assign(has_rest=lambda x: x.analysis_condition.eq("rest"),
                                 has_illusion=lambda x: x.analysis_condition.eq("illusion"))
                 .groupby("subject_id")[["has_rest", "has_illusion"]].any().reset_index())
    inclusion["eligible_rest_vs_illusion"] = inclusion.has_rest & inclusion.has_illusion
    inclusion.to_csv(out / "inclusion_matrix.csv", index=False)
    write_metadata(out, script=Path(__file__).name, source=source,
                   extra={"n_rows": len(frame), "n_subjects": int(frame.subject_id.nunique())})
    print(f"Wrote sanity-check outputs to {out}")


if __name__ == "__main__":
    main()
