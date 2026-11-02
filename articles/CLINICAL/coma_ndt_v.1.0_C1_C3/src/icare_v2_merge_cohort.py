"""Join inventory, diffusion, MNJ-v3, and reachability into one analysis table."""
from __future__ import annotations

import argparse

import pandas as pd

from icare_v2_common import (
    add_common_args,
    outcome_label,
    resolve_pipeline_config,
    write_csv,
    write_json,
)


def _load(path, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return pd.DataFrame()
    return pd.read_csv(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    in_dir = args.input_dir or cfg.output_dir
    out_dir = cfg.output_dir
    index = _load(in_dir / "patient_timebin_index.csv")
    diffusion = _load(in_dir / "diffusion_geometry_patient_timebin.csv")
    mnj = _load(in_dir / "mnj_v3_patient_timebin.csv")
    reach = _load(in_dir / "reachability_horizon_patient_timebin.csv", required=False)

    keys = ["subject_id", "time_bin_primary"]
    table = index.copy()
    rename_map = {
        "diffusion": {"n_valid_windows": "n_valid_windows_diffusion", "n_runs": "n_runs_diffusion"},
        "mnj": {"n_valid_windows": "n_valid_windows_mnj", "n_runs": "n_runs_mnj"},
        "reach": {"n_valid_windows": "n_valid_windows_reach", "n_runs": "n_runs_reach", "n_ok_runs": "n_ok_reach_runs"},
    }
    drop = {"cpc", "outcome", "hospital", "ttm"}
    for frame, name in ((diffusion, "diffusion"), (mnj, "mnj"), (reach, "reach")):
        if frame.empty:
            continue
        work = frame.rename(columns=rename_map[name])
        extra = [column for column in work.columns if column not in drop or column in keys]
        table = table.merge(work[extra], on=keys, how="left")
    table["bundle_id"] = cfg.bundle_id
    table["confirmatory_status"] = cfg.confirmatory_status
    table["smoke"] = cfg.smoke
    table["contrast_group"] = [outcome_label(value, cfg) for value in table.get("cpc", [])]
    table["in_primary_window"] = table["time_bin_primary"].astype(str).eq(cfg.primary_window)
    primary = table[table["in_primary_window"] & table["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    write_csv(out_dir / "icare_v2_patient_timebin_analysis_table.csv", table)
    write_csv(out_dir / "icare_v2_primary_cpc15_table.csv", primary)
    write_json(
        out_dir / "merge_manifest.json",
        {
            "n_patient_timebins": int(len(table)),
            "n_primary_cpc15": int(len(primary)),
            "cpc_primary_counts": primary["cpc"].value_counts(dropna=False).to_dict() if not primary.empty else {},
            "bundle_id": cfg.bundle_id,
            "confirmatory_status": cfg.confirmatory_status,
            "smoke": cfg.smoke,
        },
    )
    print(f"Merged {len(table)} patient-timebins; primary CPC1/5 n={len(primary)}", flush=True)


if __name__ == "__main__":
    main()
