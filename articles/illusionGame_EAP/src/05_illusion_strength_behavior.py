"""Conditional trial-level illusion-strength/behavior analysis.

This script deliberately refuses to run unless trial identity, strength, and
behavioral timing fields coexist in the same discovered artifact.
"""
from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ds004587_support import (MNJ_COLUMNS, MNPS_COLUMNS, bh_fdr, load_analysis_table,
    make_results_subdir, spearman, write_metadata)

REQUIRED = ("subject_id", "condition", "trial_id", "illusion_strength")
BEHAVIOR = ("rt", "reaction_time", "correct", "accuracy")

def main() -> None:
    frame, source = load_analysis_table(REQUIRED)
    behavior = next((column for column in BEHAVIOR if column in frame), None)
    if behavior is None:
        raise ValueError("Trial-level analysis is gated: no RT/correctness/accuracy field accompanies trial labels.")
    geometry = [column for column in [*MNPS_COLUMNS, *MNJ_COLUMNS] if column in frame]
    if not geometry:
        raise ValueError("Trial-level analysis is gated: source has no MNPS/MNJ geometry columns.")
    out = make_results_subdir("05_illusion_strength_behavior")
    rows = []
    for subject_id, group in frame.groupby("subject_id"):
        for metric in geometry:
            strength = spearman(group.illusion_strength, group[metric])
            strength.update(subject_id=subject_id, association="strength_x_geometry", geometry=metric)
            behavior_result = spearman(group[behavior], group[metric])
            behavior_result.update(subject_id=subject_id, association=f"{behavior}_x_geometry", geometry=metric)
            rows.extend((strength, behavior_result))
    result = pd.DataFrame(rows)
    result["p_bh_association"] = result.groupby("association")["p"].transform(bh_fdr)
    result.to_csv(out / "subject_trial_associations.csv", index=False)
    frame.groupby(["subject_id", "condition"]).agg(n_trials=("trial_id", "nunique"),
        strength_nonmissing=("illusion_strength", lambda x: x.notna().sum()),
        behavior_nonmissing=(behavior, lambda x: x.notna().sum())).reset_index().to_csv(
            out / "trial_alignment_coverage.csv", index=False)
    write_metadata(out, script=Path(__file__).name, source=source,
                   extra={"behavior_field": behavior, "geometry_columns": geometry})
    print(f"Wrote conditional trial-level outputs to {out}")

if __name__ == "__main__":
    main()
