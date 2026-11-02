"""QC summaries for inventory and merged analysis tables."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from icare_v2_common import add_common_args, resolve_pipeline_config, write_json


STATUS_COLUMNS = [
    "geometry_contract_status",
    "diffusion_computation_status",
    "jacobian_metrics_3d_status",
    "jacobian_metrics_9d_status",
    "ftr_3d_status",
    "stochastic_reachability_3d_status",
    "destination_computation_status",
    "resilience_computation_status",
]


def _value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if column not in frame.columns or frame.empty:
        return {}
    return {str(k): int(v) for k, v in frame[column].value_counts(dropna=False).items()}


def inventory_qc(in_dir: Path) -> dict:
    runs = pd.read_csv(in_dir / "run_inventory.csv")
    subjects = pd.read_csv(in_dir / "subject_index.csv") if (in_dir / "subject_index.csv").exists() else pd.DataFrame()
    timebinned = (
        pd.read_csv(in_dir / "run_inventory_timebinned.csv")
        if (in_dir / "run_inventory_timebinned.csv").exists()
        else pd.DataFrame()
    )
    payload = {
        "mode": "inventory",
        "n_runs": int(len(runs)),
        "n_subjects": int(len(subjects)),
        "n_read_ok": int(runs["read_ok"].sum()) if "read_ok" in runs.columns else 0,
        "cpc_subject_counts": _value_counts(subjects, "cpc"),
        "hospital_subject_counts": _value_counts(subjects, "hospital"),
        "ttm_subject_counts": _value_counts(subjects, "ttm"),
        "status_counts": {column: _value_counts(runs, column) for column in STATUS_COLUMNS},
        "primary_window_runs": int(timebinned["in_primary_window"].sum()) if not timebinned.empty else None,
        "primary_bin_counts": _value_counts(timebinned, "time_bin_primary"),
        "sedation_note": "Sedation/medication/WLST are not present in this export and are not imputed.",
    }
    return payload


def merged_qc(in_dir: Path, primary_window: str) -> dict:
    table = pd.read_csv(in_dir / "icare_v2_patient_timebin_analysis_table.csv")
    primary = table[table["time_bin_primary"].astype(str) == primary_window].copy() if "time_bin_primary" in table.columns else table
    metric_cols = [
        column
        for column in table.columns
        if column.endswith("_median")
        or column.startswith("f_")
        or column in {"d_eff_a_median", "h_tilde_a_median", "e_perp_median", "d_total_median"}
    ]
    missing = {
        column: {
            "n_missing": int(pd.to_numeric(primary[column], errors="coerce").isna().sum()),
            "n_finite": int(pd.to_numeric(primary[column], errors="coerce").notna().sum()),
        }
        for column in metric_cols
        if column in primary.columns
    }
    return {
        "mode": "merged",
        "n_patient_timebins": int(len(table)),
        "n_primary_window_rows": int(len(primary)),
        "cpc_primary_counts": _value_counts(primary, "cpc"),
        "ttm_by_cpc": (
            primary.groupby(["cpc", "ttm"]).size().reset_index(name="n").to_dict(orient="records")
            if not primary.empty
            else []
        ),
        "missingness_primary_window": missing,
        "sedation_note": "Sedation/medication/WLST are not present in this export and are not imputed.",
    }


def render_markdown(payload: dict) -> str:
    lines = ["# I-CARE v2 QC summary", "", f"Mode: `{payload.get('mode')}`", ""]
    for key, value in payload.items():
        if key == "mode":
            continue
        lines.append(f"- **{key}**: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--mode", choices=["inventory", "merged"], default="inventory")
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    in_dir = args.input_dir or cfg.output_dir
    out_dir = cfg.output_dir
    payload = inventory_qc(in_dir) if args.mode == "inventory" else merged_qc(in_dir, cfg.primary_window)
    payload["bundle_id"] = cfg.bundle_id
    payload["confirmatory_status"] = cfg.confirmatory_status
    payload["smoke"] = cfg.smoke
    stem = "qc_summary" if args.mode == "inventory" else "qc_summary_merged"
    write_json(out_dir / f"{stem}.json", payload)
    (out_dir / f"{stem}.md").write_text(render_markdown(payload), encoding="utf-8")
    print(f"Wrote {out_dir / f'{stem}.md'}", flush=True)


if __name__ == "__main__":
    main()
