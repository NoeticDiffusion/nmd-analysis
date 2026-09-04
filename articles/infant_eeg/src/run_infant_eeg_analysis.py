"""Run the full Figshare infant EEG developmental analysis pipeline."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from figshare_infant_support import DEFAULT_DATA_ROOT, DEFAULT_RESULTS_ROOT

CONVENTIONAL_DATA_ROOT_NAME = "neuralmanifolddynamics_figshare_infant_eeg_20260806_122539"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--n-permutation", type=int, default=5000)
    parser.add_argument(
        "--with-conventional-eeg",
        action="store_true",
        help="Also run 06_conventional_eeg_age.py (requires a re-export with conventional_eeg.enabled=true).",
    )
    args = parser.parse_args()
    if args.with_conventional_eeg:
        if args.data_root.name != CONVENTIONAL_DATA_ROOT_NAME:
            parser.error(
                "--with-conventional-eeg requires the coverage-fixed "
                f"data export named {CONVENTIONAL_DATA_ROOT_NAME!r}; "
                "the default artifact-masked export has no testable connectivity columns."
            )
        if args.output_root.resolve() == DEFAULT_RESULTS_ROOT.resolve():
            parser.error(
                "--with-conventional-eeg must use a separate --output-root; "
                "it must not overwrite the canonical primary result tree."
            )
    return args


def run(script: str, *arguments: str) -> None:
    subprocess.run([sys.executable, str(Path(__file__).with_name(script)), *arguments], check=True)


def main() -> None:
    args = parse_args()
    export_dir = args.output_root / "01_session_metrics"
    analysis_dir = args.output_root / "02_developmental_analysis"
    cohort_dir = args.output_root / "03_cohort_coordinate_age"
    pooled_reachability_dir = args.output_root / "05_cohort_pooled_reachability"
    figure_dir = args.output_root / "04_figures"
    run("01_export_session_metrics.py", "--data-root", str(args.data_root), "--output-dir", str(export_dir))
    run("02_developmental_analysis.py", "--session-metrics", str(export_dir / "session_metrics.csv"), "--output-dir", str(analysis_dir), "--n-bootstrap", str(args.n_bootstrap), "--n-permutation", str(args.n_permutation))
    run("03_cohort_coordinate_age.py", "--session-metrics", str(export_dir / "session_metrics.csv"), "--output-dir", str(cohort_dir))
    run("05_cohort_pooled_reachability.py", "--data-root", str(args.data_root), "--session-metrics", str(export_dir / "session_metrics.csv"), "--output-dir", str(pooled_reachability_dir), "--n-bootstrap", str(args.n_bootstrap), "--n-permutation", str(args.n_permutation))
    run(
        "04_make_figures.py",
        "--metrics", str(export_dir / "session_metrics.csv"),
        "--primary", str(analysis_dir / "within_child_age_associations.csv"),
        "--nine-d", str(analysis_dir / "within_child_age_associations_9d.csv"),
        "--cohort-age", str(cohort_dir / "cohort_coordinate_gee_results.csv"),
        "--cohort-predictions", str(cohort_dir / "cohort_coordinate_gee_predictions.csv"),
        "--pooled-reachability", str(pooled_reachability_dir / "cohort_pooled_reachability_age_associations.csv"),
        "--pooled-reachability-per-visit", str(pooled_reachability_dir / "cohort_pooled_reachability_per_visit.csv"),
        "--output-dir", str(figure_dir),
    )
    if args.with_conventional_eeg:
        conventional_dir = args.output_root / "06_conventional_eeg_age"
        run(
            "06_conventional_eeg_age.py",
            "--data-root", str(args.data_root),
            "--session-metrics", str(export_dir / "session_metrics.csv"),
            "--output-dir", str(conventional_dir),
            "--n-bootstrap", str(args.n_bootstrap),
            "--n-permutation", str(args.n_permutation),
        )


if __name__ == "__main__":
    main()
