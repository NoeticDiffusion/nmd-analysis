from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from depression_probsel_event_support import (
    ARTICLE_DIR,
    BDI_CORRELATIONS_CSV,
    BDI_GROUP_CONTRASTS_CSV,
    DATASET_ROOT,
    EVENT_METRIC_DIR,
    EVENT_SUMMARY_MD,
    RESULTS_DIR,
    SUMMARY_PATH,
    WITHIN_SUBJECT_CONTRASTS_CSV,
    ensure_dir,
)


SRC_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ds003474 depression PST event-first wrapper pipeline.")
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--event-metric-dir", type=Path, default=EVENT_METRIC_DIR)
    parser.add_argument("--limit-h5", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dir(args.results_dir)
    ensure_dir(args.event_metric_dir)

    compute_cmd = [
        sys.executable,
        str(SRC_DIR / "compute_depression_probsel_event_metrics.py"),
        "--dataset-root",
        str(args.dataset_root),
        "--output-dir",
        str(args.event_metric_dir),
    ]
    if args.limit_h5 is not None:
        compute_cmd.extend(["--limit-h5", str(args.limit_h5)])
    subprocess.run(compute_cmd, check=True)

    subprocess.run(
        [
            sys.executable,
            str(SRC_DIR / "export_depression_probsel_event_contrasts.py"),
            "--input-dir",
            str(args.event_metric_dir),
            "--output-dir",
            str(args.results_dir),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(SRC_DIR / "build_depression_probsel_event_first_figures.py"),
            "--results-dir",
            str(args.results_dir),
        ],
        check=True,
    )

    manifest = {
        "dataset_root": str(args.dataset_root),
        "results_dir": str(args.results_dir),
        "event_metric_dir": str(args.event_metric_dir),
        "within_subject_contrasts": str(args.results_dir / WITHIN_SUBJECT_CONTRASTS_CSV),
        "bdi_group_contrasts": str(args.results_dir / BDI_GROUP_CONTRASTS_CSV),
        "bdi_correlations": str(args.results_dir / BDI_CORRELATIONS_CSV),
        "event_summary": str(args.results_dir / EVENT_SUMMARY_MD),
        "within_subject_figure": str(ARTICLE_DIR / "figures" / "draft2_within_subject_contrasts.png"),
        "bdi_group_figure": str(ARTICLE_DIR / "figures" / "draft2_bdi_group_modulation.png"),
        "bdi_correlation_figure": str(ARTICLE_DIR / "figures" / "draft2_bdi_correlation_modulation.png"),
    }
    (args.results_dir / "event_first_pipeline_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Depression event-first pipeline",
                "",
                f"- Event metric directory: `{args.event_metric_dir}`",
                f"- Within-subject contrasts: `{args.results_dir / WITHIN_SUBJECT_CONTRASTS_CSV}`",
                f"- BDI group contrasts: `{args.results_dir / BDI_GROUP_CONTRASTS_CSV}`",
                f"- BDI correlations: `{args.results_dir / BDI_CORRELATIONS_CSV}`",
                f"- Wrapper summary: `{args.results_dir / EVENT_SUMMARY_MD}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
