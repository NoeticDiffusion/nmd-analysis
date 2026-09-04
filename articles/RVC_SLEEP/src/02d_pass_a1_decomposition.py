"""
02d_pass_a1_decomposition.py — A1 decomposition diagnostic.

Requested by the science lead (sciencelead/002.md, 2026-07-03) to interpret
the A1r `d_n` cross-dataset sign conflict found after the subject-weighted
protocol amendment: ANPHY's `event - matched_control` delta is negative while
BOAS's is positive (both FDR-significant), even though `event - pre_far`
(A2r) is positive in BOTH datasets. This script decomposes the A1
event-control delta into its two additive pieces, per event, per subject:

    A = event - pre_far              (the A2r within-spindle timing piece)
    B = pre_far - matched_control    (how the event's own peri-spindle
                                       baseline compares to matched N2 controls)
    C = event - matched_control      (A1's original/A1r specificity delta)
    C ≈ A + B   (exact identity at the per-event level, up to rows dropped by
                 missing-data differences between A's and B's requirements)

If, e.g., ANPHY has A>0 (event above its own pre_far baseline, matching A2r)
but C<0 (event below matched control), then necessarily B<<0 — ANPHY's
matched non-spindle N2 controls sit at a HIGHER `d_n` baseline than the
event's own pre-spindle neighborhood. That would mean the A1 conflict is a
baseline/control-context difference, not a contradiction of the A2 timing
result.

Diagnostic only — does not touch A1-original, A1r, A2-original, or A2r
tables. Runs all 9 frozen endpoints; reporting focuses on d_n, e_s, d_s, m
per the science lead's request.

Estimator (per dataset, per endpoint, per event, paired via
(subject_id, event_id) as in 03b_pass_a2r_subject_balanced_profile.py):
    event_val      = value at the event's "event" bin
    far_val        = mean of the event's "pre_far" bin(s)
    control_median = event's matched-control median (`{endpoint}_control_median`,
                      built in 01_build_event_level_tables.py)
    A = event_val - far_val
    B = far_val - control_median
    C = event_val - control_median

Each component is aggregated to one row per subject (mean), then tested via
subject-level sign-flip permutation (primary) + t-test/Wilcoxon (sensitivity),
same convention as A1r/A2r. BH-FDR computed fresh per component across the
18-test family (9 endpoints x 2 datasets), though this script is a diagnostic
rather than a new hypothesis-testing layer.

Run: python src/02d_pass_a1_decomposition.py
Requires: 01_build_event_level_tables.py to have been run first.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from rvc_sleep_support import (
    DATASETS,
    GEOMETRY_COLS,
    RESULTS_DIR,
    bh_fdr,
    make_results_subdir,
    one_sample_ci,
    sign_flip_permutation_test,
    subject_level_sensitivity,
)

OUT = make_results_subdir("02d_pass_a1_decomposition")
FOCUS_ENDPOINTS = ["d_n", "e_s", "d_s", "m"]


def find_latest_event_level_primary() -> Path:
    candidates = sorted(RESULTS_DIR.glob("rvc_sleep_*/01_build_event_level_tables/event_level_primary.parquet"))
    if not candidates:
        raise FileNotFoundError("No event_level_primary.parquet found. Run 01_build_event_level_tables.py first.")
    return candidates[-1]


print(f"Loading {find_latest_event_level_primary()} ...")
event_level = pd.read_parquet(find_latest_event_level_primary())

results_rows = []
sanity_rows = []
for dataset in DATASETS:
    sub_ds = event_level[event_level["dataset_id"] == dataset]

    for endpoint in GEOMETRY_COLS:
        ctrl_col = f"{endpoint}_control_median"
        if endpoint not in sub_ds.columns or ctrl_col not in sub_ds.columns:
            continue

        event_vals = (
            sub_ds[sub_ds["bin_label"] == "event"]
            .set_index(["subject_id", "event_id"])[[endpoint, ctrl_col]]
            .rename(columns={endpoint: "event_val", ctrl_col: "control_median"})
        )
        far_vals = (
            sub_ds[sub_ds["bin_label"] == "pre_far"]
            .groupby(["subject_id", "event_id"])[endpoint].mean()
            .rename("far_val")
        )
        triplet = event_vals.join(far_vals, how="inner").dropna()
        if len(triplet) < 10 or triplet.index.get_level_values("subject_id").nunique() < 5:
            continue

        triplet["A_event_minus_prefar"] = triplet["event_val"] - triplet["far_val"]
        triplet["B_prefar_minus_control"] = triplet["far_val"] - triplet["control_median"]
        triplet["C_event_minus_control"] = triplet["event_val"] - triplet["control_median"]

        # Sanity check: C should equal A + B exactly (same rows, arithmetic identity).
        max_abs_residual = float((triplet["C_event_minus_control"]
                                   - (triplet["A_event_minus_prefar"] + triplet["B_prefar_minus_control"])).abs().max())
        sanity_rows.append({"dataset": dataset, "endpoint": endpoint,
                             "n_events": len(triplet), "max_abs_identity_residual": max_abs_residual})

        subject_ids = triplet.index.get_level_values("subject_id").to_numpy()
        for component_name, component_col in [
            ("A_event_minus_prefar", "A_event_minus_prefar"),
            ("B_prefar_minus_control", "B_prefar_minus_control"),
            ("C_event_minus_control", "C_event_minus_control"),
        ]:
            values = triplet[component_col].to_numpy()
            subj_means = pd.Series(values, index=subject_ids).groupby(level=0).mean()
            mean_delta, ci_lo, ci_hi = one_sample_ci(subj_means.values)
            perm_obs, perm_p = sign_flip_permutation_test(values, subject_ids, n_perm=2000)
            sens = subject_level_sensitivity(values, subject_ids)
            results_rows.append({
                "dataset": dataset, "endpoint": endpoint, "component": component_name,
                "n_events": len(triplet), "n_subjects": len(subj_means),
                "subject_mean_delta": mean_delta, "ci95_lo": ci_lo, "ci95_hi": ci_hi,
                "perm_p": perm_p, "ttest_p": sens["ttest_p"], "wilcoxon_p": sens["wilcoxon_p"],
            })

results_df = pd.DataFrame(results_rows)
for component in results_df["component"].unique():
    mask = results_df["component"] == component
    results_df.loc[mask, "perm_p_fdr"] = bh_fdr(results_df.loc[mask, "perm_p"].values)

sanity_df = pd.DataFrame(sanity_rows)
print("\n--- Identity sanity check: C == A + B (max abs residual per endpoint) ---")
print(sanity_df.to_string(index=False))
sanity_df.to_csv(OUT / "identity_sanity_check.csv", index=False)

results_df.to_csv(OUT / "pass_a1_decomposition.csv", index=False)

print("\n--- Focused report: d_n / e_s / d_s / m ---")
focus = results_df[results_df["endpoint"].isin(FOCUS_ENDPOINTS)].sort_values(["endpoint", "dataset", "component"])
print(focus[["dataset", "endpoint", "component", "n_events", "n_subjects",
             "subject_mean_delta", "ci95_lo", "ci95_hi", "perm_p_fdr"]].to_string(index=False))

print("\n--- Pivoted view: A / B / C side by side per dataset x endpoint (focus set) ---")
pivot = focus.pivot_table(index=["dataset", "endpoint"], columns="component",
                           values="subject_mean_delta").reset_index()
pivot["A_plus_B"] = pivot.get("A_event_minus_prefar", np.nan) + pivot.get("B_prefar_minus_control", np.nan)
print(pivot.to_string(index=False))
pivot.to_csv(OUT / "focus_pivot_A_B_C.csv", index=False)

print("\n=== Pass A1 decomposition complete (diagnostic only; no frozen tables modified) ===")
print(f"All outputs in: {OUT}")
