"""
03_pass_a2_peri_spindle_profile.py — Pass A2: peri-spindle temporal profile.

Uses only spindle_event rows (all 5 peri-event bins). This is the "stronger
RVC timing claim" (plan2.md), distinct from and complementary to the Pass A1
matched-control specificity test in 02_pass_a1_rvc_specificity.py.

Model (per dataset, per endpoint), pre_far as reference level:
    geometry ~ C(bin_label, reference="pre_far") + <available covariates>
             + (1 | subject_id)

Key question: does geometry step up/down at the spindle event relative to
the pre-spindle baseline?

Run: python src/03_pass_a2_peri_spindle_profile.py
Requires: 01_build_event_level_tables.py to have been run first.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from rvc_sleep_support import (
    BIN_LABEL_ORDER,
    DATASETS,
    GEOMETRY_COLS,
    RESULTS_DIR,
    available_covariates,
    bh_fdr,
    fit_mixedlm,
    make_results_subdir,
)

OUT = make_results_subdir("03_pass_a2_peri_spindle_profile")

CANDIDATE_COVARIATES = ["event_duration_sec", "frequency_hz", "window_center_sec", "anchor_quality"]


def find_latest_event_level_primary() -> Path:
    candidates = sorted(RESULTS_DIR.glob("rvc_sleep_*/01_build_event_level_tables/event_level_primary.parquet"))
    if not candidates:
        raise FileNotFoundError(
            "No event_level_primary.parquet found. Run 01_build_event_level_tables.py first."
        )
    return candidates[-1]


print(f"Loading {find_latest_event_level_primary()} ...")
event_level = pd.read_parquet(find_latest_event_level_primary())
print(f"  {len(event_level)} spindle_event rows across {event_level['dataset_id'].nunique()} dataset(s)")

results_rows = []
for dataset in DATASETS:
    sub_ds = event_level[event_level["dataset_id"] == dataset].copy()
    sub_ds["bin_label"] = pd.Categorical(sub_ds["bin_label"], categories=BIN_LABEL_ORDER, ordered=True)
    covariates = available_covariates(sub_ds, CANDIDATE_COVARIATES)
    print(f"  [{dataset}] available covariates: {covariates}")

    for endpoint in GEOMETRY_COLS:
        if endpoint not in sub_ds.columns:
            continue
        sub = sub_ds.dropna(subset=[endpoint, "bin_label", "subject_id", *covariates]).copy()
        if sub["bin_label"].nunique() < 2 or len(sub) < 10:
            results_rows.append({
                "dataset": dataset, "endpoint": endpoint, "n_rows": len(sub),
                "note": "insufficient bin coverage or N",
            })
            continue

        formula = (
            f'{endpoint} ~ C(bin_label, Treatment(reference="pre_far"))'
            + "".join(f" + {c}" for c in covariates)
        )
        fit = fit_mixedlm(formula, sub, groups_col="subject_id")
        if fit is None:
            results_rows.append({"dataset": dataset, "endpoint": endpoint, "n_rows": len(sub), "note": "fit failed"})
            continue

        for bin_label in BIN_LABEL_ORDER:
            if bin_label == "pre_far":
                continue
            param_candidates = [p for p in fit.params.index if bin_label in p]
            if not param_candidates:
                continue
            pname = param_candidates[0]
            results_rows.append({
                "dataset": dataset,
                "endpoint": endpoint,
                "contrast": f"{bin_label}_vs_pre_far",
                "n_rows": len(sub),
                "n_subjects": sub["subject_id"].nunique(),
                "coef": float(fit.params.get(pname, np.nan)),
                "p": float(fit.pvalues.get(pname, np.nan)),
            })

results_df = pd.DataFrame(results_rows)

# Frozen FDR family: within each dataset, across the endpoint x contrast
# family (<=9 endpoints x 4 contrasts = 36 tests per dataset), per plan2.md.
if "p" in results_df.columns:
    results_df["p_fdr"] = np.nan
    for dataset in DATASETS:
        mask = results_df["dataset"] == dataset
        if mask.any():
            results_df.loc[mask, "p_fdr"] = bh_fdr(results_df.loc[mask, "p"].values)

print(results_df.to_string(index=False))
results_df.to_csv(OUT / "pass_a2_peri_spindle_profile.csv", index=False)

print("\n=== Pass A2 complete ===")
print(f"All outputs in: {OUT}")
