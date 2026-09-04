"""
04_pass_b_surface_sensitivity.py — Pass B: surface sensitivity.

Scope, per sciencelead/003.md (2026-07-03): Pass B answers ONLY

    Does putting anchor variables into the coordinate surface change the
    spindle-geometry results?

It does NOT answer "does EAP moderation exist?" — that is Pass C, and Pass C
is accepted as a null result (sciencelead/002.md, 003.md). If the
anchor-augmented surface shows a stronger effect than primary, the correct
reading is:

    Anchor-augmented coordinates are sensitive to body-derived signals when
    those signals are injected into the geometry. This does NOT imply that
    pre-event anchor state moderates EEG-only spindle geometry.

Pass B is sensitivity-only; the primary scientific claim always stays on the
EEG-only surface (handover_From_nmd.md §3).

Method: recompute the corrected subject-weighted A1r/A2r estimand
(subject_mean_delta ~ 1, subject-level sign-flip permutation, same as
02c/03b) on BOTH the primary and anchor-augmented surfaces, for both delta
definitions:

    A1r-style: event - matched_control_median
    A2r-style: event - mean(pre_far bins, same event)

then compare, per dataset x delta_mode x endpoint:
    primary_delta       (primary-surface subject mean delta + own FDR status)
    anchor_aug_delta     (anchor-aug-surface subject mean delta + own FDR status)
    surface_delta        = paired per-subject (anchor_aug - primary), averaged
                            over subjects present on both surfaces
    correlation           Pearson r between primary and anchor_aug subject
                           means (paired, subjects present on both surfaces)
    sign_agreement        whether primary and anchor_aug point the same way
    fdr_status_change     whether q<0.05 status differs between surfaces

Reporting focus (sciencelead/003.md): `e`, `e_m`, `d_n`, `e_s`, `d_s` — `e_m`
is the coordinate directly changed by anchor augmentation, `e` may inherit
that change through recomposition. All 9 frozen endpoints are computed for
completeness.

Run: python src/04_pass_b_surface_sensitivity.py
Requires: 01_build_event_level_tables.py to have been run first.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from rvc_sleep_support import (
    DATASETS,
    GEOMETRY_COLS,
    RESULTS_DIR,
    bh_fdr,
    make_results_subdir,
    sign_flip_permutation_test,
)

OUT = make_results_subdir("04_pass_b_surface_sensitivity")
DELTA_MODES = ["event_control", "event_prefar"]
FOCUS_ENDPOINTS = ["e", "e_m", "d_n", "e_s", "d_s"]


def find_latest(pattern: str) -> Path:
    candidates = sorted(RESULTS_DIR.glob(f"rvc_sleep_*/01_build_event_level_tables/{pattern}"))
    if not candidates:
        raise FileNotFoundError(f"No {pattern} found. Run 01_build_event_level_tables.py first.")
    return candidates[-1]


def event_level_deltas(event_level_df: pd.DataFrame, dataset: str, endpoint: str, delta_mode: str) -> pd.DataFrame | None:
    """One row per (subject_id, event_id) with a `delta` column, for the
    requested delta_mode, on whichever surface `event_level_df` is."""
    sub_ds = event_level_df[event_level_df["dataset_id"] == dataset]
    if endpoint not in sub_ds.columns:
        return None
    if delta_mode == "event_control":
        ctrl_col = f"{endpoint}_control_median"
        if ctrl_col not in sub_ds.columns:
            return None
        ev = sub_ds[sub_ds["bin_label"] == "event"][["subject_id", "event_id", endpoint, ctrl_col]].dropna()
        ev = ev.rename(columns={endpoint: "event_val"})
        ev["delta"] = ev["event_val"] - ev[ctrl_col]
        ev = ev[["subject_id", "event_id", "delta"]]
    else:  # event_prefar
        ev_vals = sub_ds[sub_ds["bin_label"] == "event"].groupby(["subject_id", "event_id"])[endpoint].mean().rename("event_val")
        far_vals = sub_ds[sub_ds["bin_label"] == "pre_far"].groupby(["subject_id", "event_id"])[endpoint].mean().rename("far_val")
        paired = pd.concat([ev_vals, far_vals], axis=1).dropna()
        paired["delta"] = paired["event_val"] - paired["far_val"]
        ev = paired.reset_index()[["subject_id", "event_id", "delta"]]
    if len(ev) < 10 or ev["subject_id"].nunique() < 5:
        return None
    return ev


print(f"Loading {find_latest('event_level_primary.parquet')} ...")
primary = pd.read_parquet(find_latest("event_level_primary.parquet"))
print(f"Loading {find_latest('event_level_anchor_aug.parquet')} ...")
anchor_aug = pd.read_parquet(find_latest("event_level_anchor_aug.parquet"))

results_rows = []
for delta_mode in DELTA_MODES:
    for dataset in DATASETS:
        for endpoint in GEOMETRY_COLS:
            ev_primary = event_level_deltas(primary, dataset, endpoint, delta_mode)
            ev_aug = event_level_deltas(anchor_aug, dataset, endpoint, delta_mode)
            if ev_primary is None or ev_aug is None:
                results_rows.append({
                    "delta_mode": delta_mode, "dataset": dataset, "endpoint": endpoint,
                    "note": "insufficient N on one or both surfaces",
                })
                continue

            subj_primary = ev_primary.groupby("subject_id")["delta"].mean()
            subj_aug = ev_aug.groupby("subject_id")["delta"].mean()
            paired = pd.concat([subj_primary.rename("primary"), subj_aug.rename("aug")], axis=1).dropna()

            _, perm_p_primary = sign_flip_permutation_test(ev_primary["delta"].values, ev_primary["subject_id"].values, n_perm=2000)
            _, perm_p_aug = sign_flip_permutation_test(ev_aug["delta"].values, ev_aug["subject_id"].values, n_perm=2000)

            row = {
                "delta_mode": delta_mode, "dataset": dataset, "endpoint": endpoint,
                "n_subjects_primary": subj_primary.shape[0], "n_subjects_aug": subj_aug.shape[0],
                "n_subjects_paired": len(paired),
                "primary_delta": float(subj_primary.mean()), "primary_perm_p": perm_p_primary,
                "anchor_aug_delta": float(subj_aug.mean()), "aug_perm_p": perm_p_aug,
            }

            if len(paired) >= 5:
                row["surface_delta"] = float((paired["aug"] - paired["primary"]).mean())
                if paired["primary"].nunique() > 1 and paired["aug"].nunique() > 1:
                    r, r_p = scipy_stats.pearsonr(paired["primary"], paired["aug"])
                    row["correlation"] = float(r)
                    row["correlation_p"] = float(r_p)
                else:
                    row["correlation"] = row["correlation_p"] = np.nan
                row["sign_agreement_frac"] = float((np.sign(paired["primary"]) == np.sign(paired["aug"])).mean())
                _, surface_delta_perm_p = sign_flip_permutation_test(
                    (paired["aug"] - paired["primary"]).values, paired.index.to_numpy(), n_perm=2000
                )
                row["surface_delta_perm_p"] = surface_delta_perm_p
            else:
                row["surface_delta"] = row["correlation"] = row["correlation_p"] = np.nan
                row["sign_agreement_frac"] = row["surface_delta_perm_p"] = np.nan

            results_rows.append(row)

results_df = pd.DataFrame(results_rows)

# FDR per surface, fresh, across the frozen 18-test family, computed
# separately for each delta_mode.
for surface_col, p_col in [("primary_perm_p", "primary_perm_p_fdr"), ("aug_perm_p", "aug_perm_p_fdr")]:
    if surface_col in results_df.columns:
        results_df[p_col] = np.nan
        for delta_mode in DELTA_MODES:
            mask = results_df["delta_mode"] == delta_mode
            if mask.any():
                results_df.loc[mask, p_col] = bh_fdr(results_df.loc[mask, surface_col].values)

results_df["primary_significant"] = results_df.get("primary_perm_p_fdr", np.nan) < 0.05
results_df["aug_significant"] = results_df.get("aug_perm_p_fdr", np.nan) < 0.05
results_df["fdr_status_change"] = results_df["primary_significant"] != results_df["aug_significant"]

print(results_df.to_string(index=False))
results_df.to_csv(OUT / "pass_b_surface_sensitivity.csv", index=False)

print(f"\n--- Focused report: {FOCUS_ENDPOINTS} ---")
focus = results_df[results_df["endpoint"].isin(FOCUS_ENDPOINTS)].sort_values(["delta_mode", "endpoint", "dataset"])
print(focus[["delta_mode", "dataset", "endpoint", "primary_delta", "primary_significant",
             "anchor_aug_delta", "aug_significant", "surface_delta", "correlation",
             "sign_agreement_frac", "fdr_status_change"]].to_string(index=False))
focus.to_csv(OUT / "focus_report.csv", index=False)

n_status_changes = int(results_df["fdr_status_change"].fillna(False).sum())
print(f"\n--- FDR status changed between surfaces in {n_status_changes}/{len(results_df.dropna(subset=['primary_significant','aug_significant']))} testable rows ---")

print("\n=== Pass B complete (sensitivity-only; does not test EAP moderation) ===")
print(f"All outputs in: {OUT}")
