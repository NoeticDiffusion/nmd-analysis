"""Run ds003645 exports through ndt-analysis without duplicating core logic."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

from eeg_meg_support import ARTICLE_DIR, DATASET_ROOT, NDT_ANALYSIS_ROOT, REPO_ROOT


DEFAULT_CLEANED_ROOT = REPO_ROOT / "data" / "cleaned" / "eeg_meg_ds003645_20260723"
DEFAULT_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "eeg_meg_ds003645_20260723"
RUN_CONFIG = ARTICLE_DIR / "src" / "ndt-analysis-ds003645.yaml"
ANALYZE_CONFIG = ARTICLE_DIR / "src" / "analysis-ds003645.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--raw-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--cleaned-root", type=Path, default=DEFAULT_CLEANED_ROOT)
    parser.add_argument("--analysis-root", type=Path, default=DEFAULT_ANALYSIS_ROOT)
    parser.add_argument("--run-config", type=Path, default=RUN_CONFIG)
    parser.add_argument("--analyze-config", type=Path, default=ANALYZE_CONFIG)
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--skip-analyze", action="store_true")
    parser.add_argument("--workers", type=int, default=None)
    return parser.parse_args()


def run(command: list[str]) -> None:
    print("$", " ".join(shlex.quote(part) for part in command))
    subprocess.run(command, cwd=NDT_ANALYSIS_ROOT, check=True)


def main() -> None:
    args = parse_args()
    if args.skip_run and args.skip_analyze:
        raise ValueError("At least one stage must be enabled.")
    args.cleaned_root.mkdir(parents=True, exist_ok=True)
    args.analysis_root.mkdir(parents=True, exist_ok=True)

    if not args.skip_run:
        command = [
            str(args.python), "-m", "ndt_analysis.cli", "run",
            "--config", str(args.run_config),
            "--input-root", str(args.raw_root),
            "--output-root", str(args.cleaned_root),
        ]
        if args.workers is not None:
            command.extend(["--workers", str(args.workers)])
        run(command)
    if not args.skip_analyze:
        run([
            str(args.python), "-m", "ndt_analysis.cli", "analyze",
            "--config", str(args.analyze_config),
            "--cleaned-root", str(args.cleaned_root),
            "--output-root", str(args.analysis_root),
        ])


if __name__ == "__main__":
    main()
