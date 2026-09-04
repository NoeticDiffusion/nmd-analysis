from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"

DEFAULT_RAW_ROOT = REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds004504_20260521_082947"
DEFAULT_CLEANED_ROOT = REPO_ROOT / "data" / "cleaned" / "alzheimer_ds004504_20260521"
DEFAULT_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "alzheimer_ds004504_20260521"

DEFAULT_RUN_CONFIG = NDT_ANALYSIS_ROOT / "config" / "ndt-analysis-ds004504.yaml"
DEFAULT_ANALYZE_CONFIG = NDT_ANALYSIS_ROOT / "config" / "analysis-ds004504.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the ds004504 Alzheimer/FTD ndt-analysis pipeline with article-local defaults."
    )
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--cleaned-root", type=Path, default=DEFAULT_CLEANED_ROOT)
    parser.add_argument("--analysis-root", type=Path, default=DEFAULT_ANALYSIS_ROOT)
    parser.add_argument("--run-config", type=Path, default=DEFAULT_RUN_CONFIG)
    parser.add_argument("--analyze-config", type=Path, default=DEFAULT_ANALYZE_CONFIG)
    parser.add_argument(
        "--run-analyses",
        type=str,
        default=None,
        help="Optional comma-separated subset for `ndt_analysis run --analyses`.",
    )
    parser.add_argument(
        "--analysis-blocks",
        type=str,
        default=None,
        help="Optional comma-separated subset for `ndt_analysis analyze --analyses`.",
    )
    parser.add_argument(
        "--contrasts",
        type=str,
        default=None,
        help="Optional comma-separated subset for `ndt_analysis analyze --contrasts`.",
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Skip the raw->cleaned stage and run only cleaned->analysis.",
    )
    parser.add_argument(
        "--skip-analyze",
        action="store_true",
        help="Skip the cleaned->analysis stage and run only raw->cleaned.",
    )
    return parser.parse_args()


def _run_command(command: list[str]) -> None:
    printable = " ".join(shlex.quote(part) for part in command)
    print(f"$ {printable}")
    subprocess.run(command, cwd=NDT_ANALYSIS_ROOT, check=True)


def main() -> None:
    args = parse_args()

    if args.skip_run and args.skip_analyze:
        raise ValueError("At least one pipeline stage must remain enabled.")

    args.cleaned_root.mkdir(parents=True, exist_ok=True)
    args.analysis_root.mkdir(parents=True, exist_ok=True)

    if not args.skip_run:
        run_command = [
            str(args.python),
            "-m",
            "ndt_analysis.cli",
            "run",
            "--config",
            str(args.run_config),
            "--input-root",
            str(args.raw_root),
            "--output-root",
            str(args.cleaned_root),
        ]
        if args.run_analyses:
            run_command.extend(["--analyses", args.run_analyses])
        _run_command(run_command)

    if not args.skip_analyze:
        analyze_command = [
            str(args.python),
            "-m",
            "ndt_analysis.cli",
            "analyze",
            "--config",
            str(args.analyze_config),
            "--cleaned-root",
            str(args.cleaned_root),
            "--output-root",
            str(args.analysis_root),
        ]
        if args.analysis_blocks:
            analyze_command.extend(["--analyses", args.analysis_blocks])
        if args.contrasts:
            analyze_command.extend(["--contrasts", args.contrasts])
        _run_command(analyze_command)

    print("Pipeline wrapper completed successfully.")
    print(f"cleaned_root={args.cleaned_root}")
    print(f"analysis_root={args.analysis_root}")


if __name__ == "__main__":
    main()
