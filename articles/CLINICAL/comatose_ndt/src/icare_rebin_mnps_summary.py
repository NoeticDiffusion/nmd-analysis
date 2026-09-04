from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from icare_mnps_summary_analysis import (
    aggregate_patient_bins,
    build_handoff_manifest,
    build_metric_long_table,
    ensure_output_dir,
)
from icare_patient_timeline_analysis import DEFAULT_TIME_BIN_SCHEME, TIME_BIN_SCHEMES


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ARTICLE_DIR / "results" / "mnps_summary"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "mnps_summary_rebinned"


@dataclass(frozen=True)
class Config:
    input_dir: Path
    output_dir: Path
    time_bin_scheme: str


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Re-bin existing coma MNPS run-level summaries into an alternate anchor-relative time scheme."
    )
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--time-bin-scheme",
        type=str,
        choices=sorted(TIME_BIN_SCHEMES),
        default=DEFAULT_TIME_BIN_SCHEME,
    )
    args = parser.parse_args()
    return Config(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        time_bin_scheme=args.time_bin_scheme,
    )


def assign_time_bins(frame: pd.DataFrame, time_bins_hours: tuple[tuple[float, float, str], ...]) -> pd.DataFrame:
    out = frame.copy()
    labels: List[Optional[str]] = []
    midpoints = pd.to_numeric(out["run_midpoint_from_anchor_hours"], errors="coerce")
    for midpoint in midpoints:
        label: Optional[str] = None
        if np.isfinite(midpoint):
            for lower, upper, name in time_bins_hours:
                if lower <= float(midpoint) < upper:
                    label = name
                    break
        labels.append(label)
    out["time_bin"] = labels
    return out


def build_qc_summary(config: Config, run_rows: pd.DataFrame, patient_rows: pd.DataFrame) -> Dict[str, Any]:
    return {
        "source_input_dir": str(config.input_dir),
        "time_bin_scheme": config.time_bin_scheme,
        "time_bins_hours": [
            {"label": label, "start_h": lower, "end_h": upper if np.isfinite(upper) else None}
            for lower, upper, label in TIME_BIN_SCHEMES[config.time_bin_scheme]
        ],
        "n_run_rows": int(len(run_rows)),
        "n_patient_rows": int(len(patient_rows)),
        "time_bin_counts_run_level": run_rows["time_bin"].fillna("unassigned").value_counts(dropna=False).to_dict()
        if not run_rows.empty
        else {},
        "time_bin_counts_patient_level": patient_rows["time_bin"].fillna("unassigned").value_counts(dropna=False).to_dict()
        if not patient_rows.empty
        else {},
    }


def main() -> None:
    config = parse_args()
    ensure_output_dir(config.output_dir)

    input_manifest_path = config.input_dir / "metric_handoff_manifest.json"
    input_manifest: Dict[str, Any] = {}
    if input_manifest_path.exists():
        input_manifest = json.loads(input_manifest_path.read_text(encoding="utf-8"))

    run_rows = pd.read_csv(config.input_dir / "run_level_adapter_summaries.csv")
    run_rows = assign_time_bins(run_rows, TIME_BIN_SCHEMES[config.time_bin_scheme])
    patient_rows = aggregate_patient_bins(run_rows)
    run_metrics = build_metric_long_table(run_rows, level="run")
    patient_metrics = build_metric_long_table(patient_rows, level="patient_timebin")
    handoff_manifest = build_handoff_manifest(run_metrics, patient_metrics)
    for key in (
        "processed_root",
        "raw_root",
        "adapter_config_path",
        "analyses",
        "cohort_tag",
        "bundle_tag",
    ):
        if key in input_manifest:
            handoff_manifest[key] = input_manifest[key]
    handoff_manifest["time_bin_scheme"] = config.time_bin_scheme
    handoff_manifest["source_input_dir"] = str(config.input_dir)
    qc_summary = build_qc_summary(config, run_rows, patient_rows)

    run_rows.to_csv(config.output_dir / "run_level_adapter_summaries.csv", index=False)
    patient_rows.to_csv(config.output_dir / "patient_timebin_adapter_summaries.csv", index=False)
    run_metrics.to_csv(config.output_dir / "run_level_signal_metrics.csv", index=False)
    patient_metrics.to_csv(config.output_dir / "patient_timebin_signal_metrics.csv", index=False)
    (config.output_dir / "metric_handoff_manifest.json").write_text(
        json.dumps(handoff_manifest, indent=2),
        encoding="utf-8",
    )
    (config.output_dir / "qc_summary.json").write_text(
        json.dumps(qc_summary, indent=2),
        encoding="utf-8",
    )

    for passthrough_name in ("adapter_qc.csv", "subject_outcome_index.csv"):
        source_path = config.input_dir / passthrough_name
        if source_path.exists():
            target_path = config.output_dir / passthrough_name
            target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"Wrote rebinned MNPS summary to {config.output_dir}")


if __name__ == "__main__":
    main()
