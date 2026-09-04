from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ARTICLE_DIR = Path(__file__).resolve().parents[1]
COMA_DIR = ARTICLE_DIR.parent / "comatose_ndt"
DEFAULT_PROCESSED_ROOT = Path(
    "E:/Science_Datasets/physionet/processed/physionet_icare_2_1/"
    "neuralmanifolddynamics_physionet_icare_2_1_20260525_141608"
)
DEFAULT_PRIMARY_SUMMARY_DIR = ARTICLE_DIR / "results" / "mnps_summary_20260526_regional_primary12h"
DEFAULT_HOURLY_SUMMARY_DIR = ARTICLE_DIR / "results" / "mnps_summary_20260526_regional_hourly12h"
DEFAULT_EXPORT_DIR = ARTICLE_DIR / "results" / "article_exports_20260526_regional_cpc15"
DEFAULT_FIGURE_DIR = ARTICLE_DIR / "figures" / "20260526_regional_cpc15"
DEFAULT_PRIMARY_TIMELINE_INPUT_DIR = COMA_DIR / "results" / "timeline_analysis_20260525_part1_primary12h"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the regional I-CARE article pipeline end to end.")
    parser.add_argument("--processed-root", type=Path, default=DEFAULT_PROCESSED_ROOT)
    parser.add_argument("--primary-summary-dir", type=Path, default=DEFAULT_PRIMARY_SUMMARY_DIR)
    parser.add_argument("--hourly-summary-dir", type=Path, default=DEFAULT_HOURLY_SUMMARY_DIR)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    parser.add_argument("--primary-timeline-input-dir", type=Path, default=DEFAULT_PRIMARY_TIMELINE_INPUT_DIR)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--skip-primary-summary", action="store_true")
    parser.add_argument("--skip-hourly-summary", action="store_true")
    parser.add_argument("--skip-exports", action="store_true")
    return parser.parse_args()


def run_command(command: list[str]) -> None:
    print("Running:", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def main() -> None:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    summary_script = script_dir / "icare_regional_mnps_summary_analysis.py"
    export_script = script_dir / "build_regional_article_exports.py"
    rebin_script = COMA_DIR / "src" / "icare_rebin_mnps_summary.py"

    if not args.skip_primary_summary:
        run_command(
            [
                sys.executable,
                str(summary_script),
                "--processed-root",
                str(args.processed_root),
                "--output-dir",
                str(args.primary_summary_dir),
                "--timeline-input-dir",
                str(args.primary_timeline_input_dir),
                "--time-bin-scheme",
                "primary_12h",
                "--analysis",
                "regional_mnps_jacobian_3d",
                "--analysis",
                "regional_reachability_cones_3d",
                "--prefilter-good-cpc",
                "1",
                "--prefilter-poor-cpc",
                "5",
                "--prefilter-time-bin",
                "0_12h",
                "--workers",
                str(args.workers),
            ]
        )
    if not args.skip_hourly_summary:
        run_command(
            [
                sys.executable,
                str(rebin_script),
                "--input-dir",
                str(args.primary_summary_dir),
                "--output-dir",
                str(args.hourly_summary_dir),
                "--time-bin-scheme",
                "hourly_12h",
            ]
        )
    if not args.skip_exports:
        run_command(
            [
                sys.executable,
                str(export_script),
                "--primary-summary-dir",
                str(args.primary_summary_dir),
                "--hourly-summary-dir",
                str(args.hourly_summary_dir),
                "--output-dir",
                str(args.export_dir),
                "--figure-dir",
                str(args.figure_dir),
            ]
        )


if __name__ == "__main__":
    main()
