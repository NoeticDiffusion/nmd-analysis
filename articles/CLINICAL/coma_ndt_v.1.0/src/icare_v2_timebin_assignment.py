"""Assign primary 0-12h and hourly bins from EEG-anchor run midpoints."""
from __future__ import annotations

import argparse

import pandas as pd

from icare_v2_common import (
    add_common_args,
    assign_time_bin,
    resolve_pipeline_config,
    write_csv,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    in_dir = args.input_dir or cfg.output_dir
    out_dir = cfg.output_dir
    runs = pd.read_csv(in_dir / "run_inventory.csv")
    hours = pd.to_numeric(runs.get("run_midpoint_from_anchor_hours"), errors="coerce")
    runs["time_bin_primary"] = [assign_time_bin(value, cfg.primary_scheme) for value in hours]
    runs["time_bin_hourly"] = [assign_time_bin(value, cfg.hourly_scheme) for value in hours]
    runs["in_primary_window"] = runs["time_bin_primary"].eq(cfg.primary_window)
    patient = (
        runs.groupby(["subject_id", "time_bin_primary"], as_index=False)
        .agg(
            cpc=("cpc", "first"),
            outcome=("outcome", "first"),
            age=("age", "first"),
            sex=("sex", "first"),
            hospital=("hospital", "first"),
            ttm=("ttm", "first"),
            shockable_rhythm=("shockable_rhythm", "first"),
            ohca=("ohca", "first"),
            n_runs=("source_h5", "nunique"),
            n_windows=("n_windows", "sum"),
            run_midpoint_from_anchor_hours_median=("run_midpoint_from_anchor_hours", "median"),
        )
        if not runs.empty
        else pd.DataFrame()
    )
    write_csv(out_dir / "run_inventory_timebinned.csv", runs)
    write_csv(out_dir / "patient_timebin_index.csv", patient)
    write_json(
        out_dir / "timebin_assignment_manifest.json",
        {
            "primary_scheme": cfg.primary_scheme,
            "hourly_scheme": cfg.hourly_scheme,
            "primary_window": cfg.primary_window,
            "n_runs": int(len(runs)),
            "n_primary_window_runs": int(runs["in_primary_window"].sum()) if not runs.empty else 0,
            "n_unassigned": int((runs["time_bin_primary"] == "unassigned").sum()) if not runs.empty else 0,
            "primary_bin_counts": runs["time_bin_primary"].value_counts(dropna=False).to_dict() if not runs.empty else {},
        },
    )
    print(
        f"Timebins: {len(runs)} runs, "
        f"{int(runs['in_primary_window'].sum()) if not runs.empty else 0} in {cfg.primary_window}",
        flush=True,
    )


if __name__ == "__main__":
    main()
