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
        description="Run supplementary export/QC/violin support for the resting-state depression article."
    )
    parser.add_argument("--results-root", type=Path, default=RESULTS_ROOT)
    parser.add_argument("--figures-dir", type=Path, default=FIGURES_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    commands = [
        [sys.executable, str(SRC_DIR / "build_depression_paper_exports.py"), "--results-root", str(args.results_root)],
        [sys.executable, str(SRC_DIR / "run_depression_bdi_bins.py"), "--results-root", str(args.results_root)],
        [sys.executable, str(SRC_DIR / "run_depression_centroid_adjusted_analysis.py"), "--results-root", str(args.results_root)],
        [sys.executable, str(SRC_DIR / "build_depression_svg_and_qc.py"), "--results-root", str(args.results_root), "--figures-root", str(args.figures_dir)],
        [sys.executable, str(SRC_DIR / "run_depression_additional_qc.py"), "--results-root", str(args.results_root)],
        [sys.executable, str(SRC_DIR / "build_depression_violin_plots.py"), "--results-root", str(args.results_root), "--figures-dir", str(args.figures_dir)],
    ]

    for command in commands:
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
