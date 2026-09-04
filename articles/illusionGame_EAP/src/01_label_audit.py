"""Audit ds004587 condition/trial labels without inferring absent provenance."""
from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ds004587_support import classify_condition, load_analysis_table, make_results_subdir, write_metadata

LABEL_COLUMNS = ("condition", "trial_id", "illusion_family", "illusion_strength",
                 "block", "run", "onset", "duration", "rt", "correct")


def main() -> None:
    frame, source = load_analysis_table(("subject_id", "condition"))
    out = make_results_subdir("01_label_audit")
    frame["analysis_condition"] = frame.condition.map(classify_condition)
    frame.groupby(["subject_id", "condition", "analysis_condition"], dropna=False).size().rename(
        "n_rows").reset_index().to_csv(out / "label_counts_by_subject.csv", index=False)
    pd.DataFrame({
        "label_column": LABEL_COLUMNS,
        "present": [column in frame.columns for column in LABEL_COLUMNS],
        "nonmissing_fraction": [frame[column].notna().mean() if column in frame else None
                                for column in LABEL_COLUMNS],
    }).to_csv(out / "label_provenance_availability.csv", index=False)
    unknown = frame.loc[frame.analysis_condition.isna(), ["subject_id", "condition"]].drop_duplicates()
    unknown.to_csv(out / "unclassified_conditions.csv", index=False)
    write_metadata(out, script=Path(__file__).name, source=source,
                   extra={"trial_analysis_gate": bool({"trial_id", "illusion_strength"} <= set(frame.columns))})
    print(f"Wrote label-audit outputs to {out}")


if __name__ == "__main__":
    main()
