"""
06_meta_analysis_boas_anphy.py — Random-effects meta-analysis combining
per-dataset Pass A1 effect sizes across ANPHY and BOAS.

With only k=2 studies this is a coarse descriptive pooling (see
rvc_sleep_support.random_effects_meta docstring), not a substitute for a
proper multi-cohort meta-analysis. It answers: "pooling across both sleep
cohorts, is the spindle-vs-control geometry delta directionally and
statistically consistent?"

Input: pass_a1_rvc_specificity.csv (script 02), which reports
mean/median y_event_control per dataset x endpoint. This script additionally
needs a per-dataset variance estimate for each endpoint; since script 02's
mixed-model fit object is not persisted, this script recomputes
SE(mean_y_event_control) = std / sqrt(n_events) as an approximation. Replace
with the mixed-model standard error once script 02's model objects are
exported, for a more principled pooled estimate.

Run: python src/06_meta_analysis_boas_anphy.py
Requires: 01_build_event_level_tables.py and 02_pass_a1_rvc_specificity.py
          to have been run first.
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
    make_results_subdir,
    random_effects_meta,
)

OUT = make_results_subdir("06_meta_analysis_boas_anphy")


def find_latest(pattern: str) -> Path:
    candidates = sorted(RESULTS_DIR.glob(f"rvc_sleep_*/01_build_event_level_tables/{pattern}"))
    if not candidates:
        raise FileNotFoundError(f"No {pattern} found. Run 01_build_event_level_tables.py first.")
    return candidates[-1]


def find_latest_pass_a1() -> Path:
    candidates = sorted(RESULTS_DIR.glob("rvc_sleep_*/02_pass_a1_rvc_specificity/pass_a1_rvc_specificity.csv"))
    if not candidates:
        raise FileNotFoundError("No pass_a1_rvc_specificity.csv found. Run 02_pass_a1_rvc_specificity.py first.")
    return candidates[-1]


print(f"Loading {find_latest('event_level_primary.parquet')} ...")
event_level = pd.read_parquet(find_latest("event_level_primary.parquet"))
event_bins = event_level[event_level["bin_label"] == "event"].copy()

print(f"Loading {find_latest_pass_a1()} ...")
pass_a1 = pd.read_csv(find_latest_pass_a1())

results_rows = []
for endpoint in GEOMETRY_COLS:
    ctrl_col = f"{endpoint}_control_median"
    if endpoint not in event_bins.columns or ctrl_col not in event_bins.columns:
        continue

    effects, variances, per_dataset = [], [], []
    for dataset in DATASETS:
        sub = event_bins[
            (event_bins["dataset_id"] == dataset) & event_bins[endpoint].notna() & event_bins[ctrl_col].notna()
        ]
        if len(sub) < 10:
            continue
        y = (sub[endpoint] - sub[ctrl_col]).values
        mean_y = float(np.mean(y))
        se_y = float(np.std(y, ddof=1) / np.sqrt(len(y)))
        effects.append(mean_y)
        variances.append(se_y ** 2)
        per_dataset.append({"dataset": dataset, "endpoint": endpoint, "mean_y": mean_y, "se_y": se_y, "n": len(y)})

    if len(effects) < 2:
        continue

    meta = random_effects_meta(np.array(effects), np.array(variances))
    row = {"endpoint": endpoint, **meta}
    for pd_row in per_dataset:
        row[f"{pd_row['dataset']}_mean_y"] = pd_row["mean_y"]
        row[f"{pd_row['dataset']}_se_y"] = pd_row["se_y"]
        row[f"{pd_row['dataset']}_n"] = pd_row["n"]
    results_rows.append(row)

results_df = pd.DataFrame(results_rows)
print(results_df.to_string(index=False))
results_df.to_csv(OUT / "meta_analysis_boas_anphy.csv", index=False)

print("\n=== Meta-analysis complete ===")
print(f"All outputs in: {OUT}")

# TODO: replace the per-dataset mean/SE approximation with the mixed-model
# intercept coefficient and its standard error once 02_pass_a1_rvc_specificity.py
# persists fit objects (or their SEs) directly, rather than recomputing a
# naive per-event SE here.
