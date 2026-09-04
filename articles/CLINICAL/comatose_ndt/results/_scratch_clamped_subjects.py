"""Identify subjects with persistence metric values outside physical bounds."""
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent

MNPS_DIR = BASE / "mnps_summary_20260602_combined_combat_corrected_primary12h_cpc15"
OUT_DIR  = BASE / "outcome_contrasts_20260605_clamp_primary12h_cpc15"

# Bounds (must match icare_outcome_contrast_analysis.py)
BOUNDS = {
    "persistence_d_eff":       3.0,
    "persistence_log_det":     50.0,
    "persistence_log_eig_var": 50.0,
    "persistence_kappa":       1.0e6,
}


def metric_bound(metric: str) -> float | None:
    for key, bound in BOUNDS.items():
        if key in metric:
            return bound
    return None


def load_and_flag(csv_path: Path, level: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, low_memory=False)
    # Keep only long-format metric rows (metric + value columns expected)
    # The file is wide-format adapter summaries; melt persistence columns
    persistence_cols = [c for c in df.columns if any(k in c for k in BOUNDS)]
    if not persistence_cols:
        print(f"  No persistence columns found in {csv_path.name}")
        return pd.DataFrame()

    id_cols = [c for c in ["subject", "analysis_type", "time_bin", "outcome", "cpc",
                            "block_scope", "block_space"] if c in df.columns]
    rows = []
    for col in persistence_cols:
        bound = metric_bound(col)
        if bound is None:
            continue
        sub = df[id_cols + [col]].copy()
        sub = sub.rename(columns={col: "value"})
        sub["metric"] = col
        sub["bound"] = bound
        sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
        mask = sub["value"].notna() & (sub["value"] > bound)
        if mask.any():
            sub = sub[mask].copy()
            sub["level"] = level
            rows.append(sub)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


print("Loading patient_timebin and run_level adapter summaries…")
patient_df = load_and_flag(MNPS_DIR / "patient_timebin_adapter_summaries.csv", "patient_timebin")
run_df     = load_and_flag(MNPS_DIR / "run_level_adapter_summaries.csv", "run_level")

combined = pd.concat([patient_df, run_df], ignore_index=True)

if combined.empty:
    print("No out-of-bounds values found.")
else:
    combined = combined.sort_values(["metric", "value"], ascending=[True, False])
    combined.to_csv(OUT_DIR / "clamped_subjects.csv", index=False)

    print(f"\n{'='*70}")
    print(f"SUBJECTS WITH PERSISTENCE VALUES EXCEEDING PHYSICAL BOUNDS")
    print(f"{'='*70}")

    for metric_name, grp in combined.groupby("metric"):
        bound = grp["bound"].iloc[0]
        print(f"\n  {metric_name}  (bound = {bound:.4g})")
        for _, row in grp.sort_values("value", ascending=False).iterrows():
            cpc_str = f"CPC {int(row['cpc'])}" if "cpc" in row and pd.notna(row.get("cpc")) else ""
            outcome_str = str(row.get("outcome", ""))
            tb = str(row.get("time_bin", ""))
            print(f"    sub={row['subject']:12s}  value={row['value']:>12.3g}  {cpc_str:6s}  {outcome_str:6s}  {tb}")

    print(f"\n{'='*70}")
    print(f"Total clamped rows: {len(combined)}")
    print(f"Unique subjects affected: {combined['subject'].nunique()}")
    print(f"Breakdown by metric:")
    summary = combined.groupby("metric").agg(
        n_rows=("value", "count"),
        n_subjects=("subject", "nunique"),
        value_min=("value", "min"),
        value_max=("value", "max"),
        value_median=("value", "median"),
    ).reset_index()
    print(summary.to_string(index=False))
    print(f"\nSaved: {OUT_DIR / 'clamped_subjects.csv'}")
