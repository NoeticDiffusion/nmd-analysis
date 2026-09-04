"""Primary paired rest-versus-illusion MNPS/MNJ analysis for ds004587."""
from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ds004587_support import (MNJ_COLUMNS, MNPS_COLUMNS, bh_fdr, classify_condition,
    load_analysis_table, make_results_subdir, paired_wilcoxon, subject_condition_medians, write_metadata)


def main() -> None:
    frame, source = load_analysis_table(("subject_id", "condition"))
    frame["condition"] = frame.condition.map(classify_condition)
    frame = frame[frame.condition.isin(("rest", "illusion"))].copy()
    metrics = [column for column in [*MNPS_COLUMNS, *MNJ_COLUMNS] if column in frame]
    if not metrics:
        raise ValueError("Primary geometry analysis requires MNPS or MNJ metric columns; none were found.")
    medians = subject_condition_medians(frame, metrics)
    medians.to_csv((out := make_results_subdir("03_rest_vs_ig_geometry")) / "subject_condition_medians.csv", index=False)
    rows = []
    for metric in metrics:
        wide = medians.pivot(index="subject_id", columns="condition", values=metric)
        if {"rest", "illusion"} <= set(wide):
            row = paired_wilcoxon(wide["illusion"], wide["rest"])
            row.update(metric=metric, contrast="illusion_minus_rest",
                       family="MNPS" if metric in MNPS_COLUMNS else "MNJ")
            rows.append(row)
    results = pd.DataFrame(rows)
    if results.empty:
        raise ValueError("No subject had paired rest and illusion observations for any geometry metric.")
    results["p_bh_family"] = results.groupby("family")["p"].transform(bh_fdr)
    results["significant_bh_05"] = results.p_bh_family < .05
    results.to_csv(out / "rest_vs_illusion_paired_tests.csv", index=False)
    write_metadata(out, script=Path(__file__).name, source=source,
                   extra={"conditions_retained": ["rest", "illusion"], "metrics": metrics})
    print(f"Wrote primary geometry outputs to {out}")


if __name__ == "__main__":
    main()
