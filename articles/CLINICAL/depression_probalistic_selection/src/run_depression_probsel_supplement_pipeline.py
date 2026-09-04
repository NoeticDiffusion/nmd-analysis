from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent
ARTICLE_DIR = SRC_DIR.parents[0]
RESULTS_ROOT = ARTICLE_DIR / "results"
FIGURES_DIR = ARTICLE_DIR / "figures"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run supplementary QC/robustness and violin-plot support for depression_probsel."
    )
    parser.add_argument("--results-root", type=Path, default=RESULTS_ROOT)
    parser.add_argument("--figures-dir", type=Path, default=FIGURES_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    subprocess.run(
        [
            sys.executable,
            str(SRC_DIR / "run_depression_probsel_additional_qc.py"),
            "--results-root",
            str(args.results_root),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(SRC_DIR / "build_depression_probsel_violin_plots.py"),
            "--results-root",
            str(args.results_root),
            "--figures-dir",
            str(args.figures_dir),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
