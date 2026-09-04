from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ARTICLE_DIR = Path(__file__).resolve().parents[1]
COMA_DIR = ARTICLE_DIR.parent / "comatose_ndt"
DEFAULT_PROCESSED_ROOT = Path(
    "J:/repos/NoeticDiffusion/data/raw/"
    "neuralmanifolddynamics_physionet_icare_2_1_20260527_151403"
)
DEFAULT_SUMMARY_DIR = ARTICLE_DIR / "results" / "mnps_summary_20260528_part1_block_jacobian_cpc15_primary12h"
DEFAULT_EXPORT_DIR = ARTICLE_DIR / "results" / "block_pilot_20260528_part1_cpc15_primary12h"
DEFAULT_TIMELINE_INPUT_DIR = COMA_DIR / "results" / "timeline_analysis_20260524_part1_primary12h_9d"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the coma block-Jacobian pilot pipeline end to end.")
    parser.add_argument("--processed-root", type=Path, default=DEFAULT_PROCESSED_ROOT)
    parser.add_argument("--summary-dir", type=Path, default=DEFAULT_SUMMARY_DIR)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--timeline-input-dir", type=Path, default=DEFAULT_TIMELINE_INPUT_DIR)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit-h5", type=int, default=None)
    parser.add_argument("--skip-summary", action="store_true")
    parser.add_argument("--skip-export", action="store_true")
    return parser.parse_args()


def run_command(command: list[str]) -> None:
    print("Running:", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def main() -> None:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    summary_script = script_dir / "icare_block_jacobian_summary_analysis.py"
    export_script = script_dir / "export_block_jacobian_pilot.py"

    if not args.skip_summary:
        command = [
            sys.executable,
            str(summary_script),
            "--processed-root",
            str(args.processed_root),
            "--output-dir",
            str(args.summary_dir),
            "--timeline-input-dir",
            str(args.timeline_input_dir),
            "--analysis",
            "global_mnps_jacobian_9d_block_jacobian",
            "--prefilter-good-cpc",
            "1",
            "--prefilter-poor-cpc",
            "5",
            "--prefilter-time-bin",
            "0_12h",
            "--workers",
            str(args.workers),
        ]
        if args.limit_h5 is not None and args.limit_h5 > 0:
            command.extend(["--limit-h5", str(args.limit_h5)])
        run_command(command)

    if not args.skip_export:
        run_command(
            [
                sys.executable,
                str(export_script),
                "--summary-dir",
                str(args.summary_dir),
                "--output-dir",
                str(args.export_dir),
            ]
        )


if __name__ == "__main__":
    main()
