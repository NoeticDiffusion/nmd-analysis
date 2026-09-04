from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"

DEFAULT_CLEANED_ROOT = REPO_ROOT / "data" / "cleaned" / "psychosis_cohort_anchor_20260520"
DEFAULT_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "psychosis_cohort_anchor_20260520"


@dataclass(frozen=True)
class DatasetSpec:
    dataset: str
    raw_root: Path
    run_config: Path
    analyze_config: Path


DATASET_SPECS = {
    "ds003944": DatasetSpec(
        dataset="ds003944",
        raw_root=REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003944_20260520_121126",
        run_config=ARTICLE_DIR / "src" / "ndt-analysis-ds003944-reachability.yaml",
        analyze_config=ARTICLE_DIR / "src" / "analysis-ds003944-reachability.yaml",
    ),
    "ds003947": DatasetSpec(
        dataset="ds003947",
        raw_root=REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds003947_20260520_114135",
        run_config=ARTICLE_DIR / "src" / "ndt-analysis-ds003947-reachability.yaml",
        analyze_config=ARTICLE_DIR / "src" / "analysis-ds003947-reachability.yaml",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresh psychosis cohort-anchor reachability outputs for ds003944 and ds003947."
    )
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--cleaned-root", type=Path, default=DEFAULT_CLEANED_ROOT)
    parser.add_argument("--analysis-root", type=Path, default=DEFAULT_ANALYSIS_ROOT)
    parser.add_argument(
        "--datasets",
        type=str,
        default="ds003944,ds003947",
        help="Comma-separated dataset list. Default: ds003944,ds003947",
    )
    parser.add_argument("--skip-run", action="store_true", help="Skip the raw->cleaned stage.")
    parser.add_argument("--skip-analyze", action="store_true", help="Skip the cleaned->analysis stage.")
    return parser.parse_args()


def _run_command(command: list[str]) -> None:
    printable = " ".join(shlex.quote(part) for part in command)
    print(f"$ {printable}")
    subprocess.run(command, cwd=NDT_ANALYSIS_ROOT, check=True)


def main() -> None:
    args = parse_args()
    if args.skip_run and args.skip_analyze:
        raise ValueError("At least one pipeline stage must remain enabled.")

    datasets = [item.strip() for item in args.datasets.split(",") if item.strip()]
    unknown = [dataset for dataset in datasets if dataset not in DATASET_SPECS]
    if unknown:
        raise ValueError(f"Unknown datasets: {', '.join(sorted(unknown))}")

    args.cleaned_root.mkdir(parents=True, exist_ok=True)
    args.analysis_root.mkdir(parents=True, exist_ok=True)

    for dataset in datasets:
        spec = DATASET_SPECS[dataset]
        print(f"=== {dataset} ===")

        if not args.skip_run:
            run_command = [
                str(args.python),
                "-m",
                "ndt_analysis.cli",
                "run",
                "--config",
                str(spec.run_config),
                "--input-root",
                str(spec.raw_root),
                "--output-root",
                str(args.cleaned_root),
                "--analyses",
                "reachability_cones",
            ]
            _run_command(run_command)

        if not args.skip_analyze:
            analyze_command = [
                str(args.python),
                "-m",
                "ndt_analysis.cli",
                "analyze",
                "--config",
                str(spec.analyze_config),
                "--cleaned-root",
                str(args.cleaned_root),
                "--output-root",
                str(args.analysis_root),
            ]
            _run_command(analyze_command)

    print("Psychosis reachability pipeline completed successfully.")
    print(f"cleaned_root={args.cleaned_root}")
    print(f"analysis_root={args.analysis_root}")


if __name__ == "__main__":
    main()
