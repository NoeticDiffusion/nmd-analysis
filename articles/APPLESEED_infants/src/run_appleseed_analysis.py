"""Run the APPLESEED reliability and longitudinal analysis reproducibly."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from appleseed_support import DEFAULT_DATA_ROOT, DEFAULT_RESULTS_ROOT

SRC_DIR = Path(__file__).parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--limit-sessions", type=int, default=None)
    parser.add_argument("--skip-events", action="store_true")
    parser.add_argument("--skip-figures", action="store_true")
    return parser.parse_args()


def run(command: list[str]) -> None:
    print("$", " ".join(command))
    subprocess.run(command, check=True, cwd=SRC_DIR)


def main() -> None:
    args = parse_args()
    args.data_root = args.data_root.resolve()
    args.output_dir = args.output_dir.resolve()
    python = str(Path(sys.executable))
    export = [
        python, str(SRC_DIR / "01_export_session_metrics.py"),
        "--data-root", str(args.data_root),
        "--output-dir", str(args.output_dir / "01_session_metrics"),
    ]
    if args.limit_sessions is not None:
        export.extend(["--limit-sessions", str(args.limit_sessions)])
    run(export)
    run([
        python, str(SRC_DIR / "02_reliability_longitudinal.py"),
        "--session-metrics", str(args.output_dir / "01_session_metrics" / "session_metrics.csv"),
        "--output-dir", str(args.output_dir / "02_reliability_longitudinal"),
    ])
    if not args.skip_events:
        run([
            python, str(SRC_DIR / "03_event_locked_exploratory.py"),
            "--data-root", str(args.data_root),
            "--output-dir", str(args.output_dir / "03_event_locked_exploratory"),
        ])
    if not args.skip_figures:
        run([
            python, str(SRC_DIR / "04_make_figures.py"),
            "--metrics", str(args.output_dir / "01_session_metrics" / "session_metrics.csv"),
            "--reliability", str(args.output_dir / "02_reliability_longitudinal" / "reliability_metrics.csv"),
            "--cohort-age", str(args.output_dir / "02_reliability_longitudinal" / "cohort_4m_to_8m.csv"),
            "--longitudinal", str(args.output_dir / "02_reliability_longitudinal" / "longitudinal_contrasts.csv"),
            "--output-dir", str(args.output_dir / "04_figures"),
        ])


if __name__ == "__main__":
    main()
