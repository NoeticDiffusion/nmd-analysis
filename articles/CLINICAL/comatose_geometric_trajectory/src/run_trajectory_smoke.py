from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from trajectory_support import SMOKE_DIR, ensure_dir


ARTICLE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ARTICLE_DIR / "src"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a small smoke test for coma trajectory metrics.")
    parser.add_argument("--part", choices=("part1", "part2"), default="part1")
    parser.add_argument("--limit-h5", type=int, default=80)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dir(SMOKE_DIR)
    timeline_dir = SMOKE_DIR / f"timeline_{args.part}_limit{args.limit_h5}"
    metric_dir = SMOKE_DIR / f"metrics_{args.part}_limit{args.limit_h5}"
    contrast_dir = SMOKE_DIR / f"contrasts_{args.part}_limit{args.limit_h5}"

    subprocess.run(
        [
            sys.executable,
            str(SRC_DIR / "compute_trajectory_metrics.py"),
            "--part",
            args.part,
            "--limit-h5",
            str(args.limit_h5),
            "--timeline-dir",
            str(timeline_dir),
            "--output-dir",
            str(metric_dir),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(SRC_DIR / "export_trajectory_contrasts.py"),
            "--input-dir",
            str(metric_dir),
            "--contrast-dir",
            str(contrast_dir),
            "--ledger-dir",
            str(contrast_dir),
            "--cohort-tag",
            f"{args.part}_smoke_limit{args.limit_h5}",
        ],
        check=True,
    )

    payload = {
        "part": args.part,
        "limit_h5": int(args.limit_h5),
        "timeline_dir": str(timeline_dir),
        "metric_dir": str(metric_dir),
        "contrast_dir": str(contrast_dir),
    }
    (contrast_dir / "smoke_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
