"""Validate observed ECG/PPG/respiration anchor fields before EAP inference."""
from __future__ import annotations

from pathlib import Path
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ds004587_support import (ANCHOR_COLUMNS, QC_COLUMNS, apply_documented_physio_exclusions,
    load_analysis_table, make_results_subdir, valid_anchor_columns, write_metadata)


def main() -> None:
    frame, source = load_analysis_table(("subject_id", "condition"))
    frame = apply_documented_physio_exclusions(frame, context="02_anchor_validation")
    available = [column for column in ANCHOR_COLUMNS if column in frame]
    if not available:
        raise ValueError("Anchor validation cannot proceed: no expected ECG/PPG/respiration anchor columns exist.")
    out = make_results_subdir("02_anchor_validation")
    rows = []
    for column in available:
        values = pd.to_numeric(frame[column], errors="coerce")
        rows.append({"feature": column, "n_finite": int(values.notna().sum()),
                     "median": values.median(), "iqr": values.quantile(.75) - values.quantile(.25),
                     "min": values.min(), "max": values.max(),
                     "constant": bool(values.nunique(dropna=True) <= 1)})
    pd.DataFrame(rows).to_csv(out / "anchor_feature_plausibility.csv", index=False)
    qc = [column for column in QC_COLUMNS if column in frame]
    if qc:
        frame.groupby("condition")[qc].mean(numeric_only=True).reset_index().to_csv(
            out / "anchor_qc_by_condition.csv", index=False)
    gate = pd.DataFrame(rows)
    gate["passes_minimum_coverage"] = gate.n_finite >= 5
    gate["passes_nonconstant"] = ~gate.constant
    gate["max_abs_over_iqr"] = gate["max"].abs() / gate["iqr"].replace(0, np.nan)
    gate["passes_scale_sanity"] = gate.max_abs_over_iqr <= 1000
    gate["anchor_inference_permitted"] = gate.feature.isin(valid_anchor_columns(frame))
    gate.to_csv(out / "anchor_inference_gate.csv", index=False)
    write_metadata(out, script=Path(__file__).name, source=source,
                   extra={"validated_features": available, "qc_columns": qc})
    print(f"Wrote anchor-validation outputs to {out}")


if __name__ == "__main__":
    main()
