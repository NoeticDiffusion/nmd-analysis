from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = Path(__file__).resolve().parent

DEFAULT_PROCESSED_ROOT = (
    REPO_ROOT
    / "data"
    / "raw"
    / "neuralmanifolddynamics_physionet_icare_2_1_20260605_060324_12_24h_part1"
)
DEFAULT_RAW_ROOT = Path("E:/Science_Datasets/physionet/received/i-care_2_1_random100_longitudinal/training")
DEFAULT_RESULTS_ROOT = ARTICLE_DIR / "results"
DEFAULT_FIGURES_ROOT = ARTICLE_DIR / "figures"
DEFAULT_CONFIG_PATH = ARTICLE_DIR / "config" / "icare_ndt_analysis.yaml"
DEFAULT_STAMP = "20260605_part1_partial"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the 12-24 h coma pilot on the currently available iCARE H5 export."
    )
    parser.add_argument("--processed-root", type=Path, default=DEFAULT_PROCESSED_ROOT)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--figures-root", type=Path, default=DEFAULT_FIGURES_ROOT)
    parser.add_argument("--config-path", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--stamp", type=str, default=DEFAULT_STAMP)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--limit-h5", type=int, default=None)
    parser.add_argument("--skip-reviewer-checks", action="store_true")
    parser.add_argument("--skip-figures", action="store_true")
    return parser.parse_args()


def _run(command: list[str]) -> None:
    printable = " ".join(shlex.quote(part) for part in command)
    print(f"$ {printable}")
    subprocess.run(command, cwd=SRC_DIR, check=True)


def _append_optional_int(command: list[str], flag: str, value: int | None) -> list[str]:
    if value is not None:
        command.extend([flag, str(value)])
    return command


def build_paths(args: argparse.Namespace) -> dict[str, Path]:
    results_root = args.results_root
    figures_root = args.figures_root / f"{args.stamp}_true1224"
    return {
        "timeline_dir": results_root / f"timeline_analysis_{args.stamp}_primary12h_allavailable",
        "mnps_true1224_dir": results_root / f"mnps_summary_{args.stamp}_primary12h_true1224",
        "contrast_true1224_dir": results_root / f"outcome_contrasts_{args.stamp}_primary12h_true1224_cpc15",
        "reviewer_dir": results_root / f"reviewer_checks_{args.stamp}_true1224",
        "figures_dir": figures_root,
        "manifest_path": results_root / f"pilot_manifest_{args.stamp}.json",
    }


def main() -> None:
    args = parse_args()
    paths = build_paths(args)
    python = str(Path(sys.executable))

    timeline_cmd = [
        python,
        str(SRC_DIR / "icare_patient_timeline_analysis.py"),
        "--processed-root",
        str(args.processed_root),
        "--raw-root",
        str(args.raw_root),
        "--output-dir",
        str(paths["timeline_dir"]),
        "--coordinate-contract",
        "subject_anchored",
        "--time-bin-scheme",
        "primary_12h",
    ]
    _append_optional_int(timeline_cmd, "--limit-h5", args.limit_h5)
    _run(timeline_cmd)

    mnps_true1224_cmd = [
        python,
        str(SRC_DIR / "icare_mnps_summary_analysis.py"),
        "--processed-root",
        str(args.processed_root),
        "--raw-root",
        str(args.raw_root),
        "--output-dir",
        str(paths["mnps_true1224_dir"]),
        "--adapter-config-path",
        str(args.config_path),
        "--timeline-input-dir",
        str(paths["timeline_dir"]),
        "--time-bin-scheme",
        "primary_12h",
        "--prefilter-time-bin",
        "12_24h",
        "--workers",
        str(args.workers),
    ]
    _append_optional_int(mnps_true1224_cmd, "--limit-h5", args.limit_h5)
    _run(mnps_true1224_cmd)

    _run(
        [
            python,
            str(SRC_DIR / "icare_outcome_contrast_analysis.py"),
            "--input-dir",
            str(paths["mnps_true1224_dir"]),
            "--output-dir",
            str(paths["contrast_true1224_dir"]),
            "--good-label",
            "CPC1",
            "--poor-label",
            "CPC5",
            "--good-cpc",
            "1",
            "--poor-cpc",
            "5",
        ]
    )

    if not args.skip_reviewer_checks:
        _run(
            [
                python,
                str(SRC_DIR / "reviewer_response_checks.py"),
                "--timeline-dir",
                str(paths["timeline_dir"]),
                "--contrast-dir",
                str(paths["contrast_true1224_dir"]),
                "--mnps-dir",
                str(paths["mnps_true1224_dir"]),
                "--output-dir",
                str(paths["reviewer_dir"]),
                "--primary-time-bin",
                "12_24h",
                "--good-cpc",
                "1",
                "--poor-cpc",
                "5",
            ]
        )

    if not args.skip_figures:
        figure_cmd = [
            python,
            str(SRC_DIR / "make_coma_figures.py"),
            "--timeline-dir",
            str(paths["timeline_dir"]),
            "--primary-contrast-dir",
            str(paths["contrast_true1224_dir"]),
            "--reviewer-checks-dir",
            str(paths["reviewer_dir"]),
            "--figure-dir",
            str(paths["figures_dir"]),
            "--primary-time-bin",
            "12_24h",
            "--skip-hourly",
        ]
        _run(figure_cmd)

    manifest = {
        "processed_root": str(args.processed_root),
        "raw_root": str(args.raw_root),
        "config_path": str(args.config_path),
        "stamp": args.stamp,
        "workers": args.workers,
        "limit_h5": args.limit_h5,
        "timeline_dir": str(paths["timeline_dir"]),
        "mnps_true1224_dir": str(paths["mnps_true1224_dir"]),
        "contrast_true1224_dir": str(paths["contrast_true1224_dir"]),
        "reviewer_dir": str(paths["reviewer_dir"]),
        "figures_dir": str(paths["figures_dir"]),
    }
    paths["manifest_path"].write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Pilot manifest written to {paths['manifest_path']}")


if __name__ == "__main__":
    main()
