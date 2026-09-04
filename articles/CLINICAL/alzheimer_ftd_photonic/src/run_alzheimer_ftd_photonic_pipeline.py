from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

from build_photonic_paper_exports import DEFAULT_SELECTION_MODE, write_photonic_exports


REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = Path(__file__).resolve().parent
DEFAULT_RAW_ROOT = REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds006036_20260604_132747"
DEFAULT_RESULTS_ROOT = ARTICLE_DIR / "results"
DEFAULT_REST_RAW_ROOT = REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds004504_20260528_114734"
DEFAULT_REST_CLEANED_ROOT = REPO_ROOT / "data" / "cleaned" / "alzheimer_ftd_photonic_ds004504_20260528"
DEFAULT_REST_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "alzheimer_ftd_photonic_ds004504_20260528"
DEFAULT_REST_RESULTS_ROOT = ARTICLE_DIR / "results" / "ds004504_reference"
DEFAULT_REFERENCE_ROOT = ARTICLE_DIR / "results" / "rest_vs_photic_reference"
DEFAULT_FIGURES_ROOT = ARTICLE_DIR / "figures"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the standalone ds006036 photic export pipeline with optional resting-reference and figures."
    )
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--selection-mode", default=DEFAULT_SELECTION_MODE)
    parser.add_argument("--block-length-windows", type=int, default=5)
    parser.add_argument("--duplicate-gap-windows", type=int, default=1)
    parser.add_argument("--build-rest-reference", action="store_true")
    parser.add_argument("--build-figures", action="store_true")
    parser.add_argument("--rest-raw-root", type=Path, default=DEFAULT_REST_RAW_ROOT)
    parser.add_argument("--rest-cleaned-root", type=Path, default=DEFAULT_REST_CLEANED_ROOT)
    parser.add_argument("--rest-analysis-root", type=Path, default=DEFAULT_REST_ANALYSIS_ROOT)
    parser.add_argument("--rest-results-root", type=Path, default=DEFAULT_REST_RESULTS_ROOT)
    parser.add_argument("--reference-root", type=Path, default=DEFAULT_REFERENCE_ROOT)
    parser.add_argument("--figures-root", type=Path, default=DEFAULT_FIGURES_ROOT)
    parser.add_argument(
        "--skip-rest-run",
        action="store_true",
        help="Use existing cleaned ds004504 outputs and run only the analysis/export/reference layers.",
    )
    return parser.parse_args()


def _run_command(command: list[str]) -> None:
    printable = " ".join(shlex.quote(part) for part in command)
    print(f"$ {printable}")
    subprocess.run(command, cwd=SRC_DIR, check=True)


def main() -> None:
    args = parse_args()
    outputs = write_photonic_exports(
        args.raw_root,
        args.results_root,
        selection_mode=args.selection_mode,
        block_length_windows=args.block_length_windows,
        duplicate_gap_windows=args.duplicate_gap_windows,
    )

    if args.build_rest_reference:
        rest_pipeline_cmd = [
            str(Path(sys.executable)),
            str(SRC_DIR / "run_alzheimer_ds004504_reference_pipeline.py"),
            "--raw-root",
            str(args.rest_raw_root),
            "--cleaned-root",
            str(args.rest_cleaned_root),
            "--analysis-root",
            str(args.rest_analysis_root),
        ]
        if args.skip_rest_run:
            rest_pipeline_cmd.append("--skip-run")
        _run_command(rest_pipeline_cmd)

        _run_command(
            [
                str(Path(sys.executable)),
                str(SRC_DIR / "build_ds004504_reference_exports.py"),
                "--analysis-root",
                str(args.rest_analysis_root),
                "--results-root",
                str(args.rest_results_root),
            ]
        )
        _run_command(
            [
                str(Path(sys.executable)),
                str(SRC_DIR / "build_rest_vs_photic_reference.py"),
                "--rest-analysis-root",
                str(args.rest_analysis_root),
                "--photic-results-root",
                str(args.results_root),
                "--output-root",
                str(args.reference_root),
            ]
        )

    if args.build_figures:
        _run_command(
            [
                str(Path(sys.executable)),
                str(SRC_DIR / "build_photonic_figures.py"),
                "--results-root",
                str(args.results_root),
                "--reference-root",
                str(args.reference_root),
                "--figures-root",
                str(args.figures_root),
            ]
        )

    print("Photonic Alzheimer pipeline completed successfully.")
    print(f"results_root={args.results_root}")
    print(f"manifest={outputs['manifest_path']}")


if __name__ == "__main__":
    main()
