"""Run paired euglycemia-hypoglycemia H5 exports through ndt-analysis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
ARTICLE_SRC = Path(__file__).resolve().parent
DEFAULT_RAW_ROOT = (
    REPO_ROOT
    / "data"
    / "raw"
    / "neuralmanifolddynamics_hypoglycemia_t1d_20260723_180515"
)
DEFAULT_CLEANED_ROOT = REPO_ROOT / "data" / "cleaned" / "hypoglycemia_t1d_20260723"
DEFAULT_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "hypoglycemia_t1d_20260723"
DEFAULT_RUN_CONFIG = ARTICLE_SRC / "ndt-analysis-hypoglycemia-t1d.yaml"
DEFAULT_ANALYZE_CONFIG = ARTICLE_SRC / "analysis-hypoglycemia-t1d.yaml"
sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.analysis_pipeline import run_cleaned_analysis_pipeline
from ndt_analysis.pipeline import run_dataset_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--cleaned-root", type=Path, default=DEFAULT_CLEANED_ROOT)
    parser.add_argument("--analysis-root", type=Path, default=DEFAULT_ANALYSIS_ROOT)
    parser.add_argument("--run-config", type=Path, default=DEFAULT_RUN_CONFIG)
    parser.add_argument("--analyze-config", type=Path, default=DEFAULT_ANALYZE_CONFIG)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--run-analyses", help="Comma-separated run blocks.")
    parser.add_argument("--analysis-blocks", help="Comma-separated analysis blocks.")
    parser.add_argument("--contrasts", help="Comma-separated contrast names.")
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--skip-analyze", action="store_true")
    return parser.parse_args()


def materialize_condition_from_task(cleaned_root: Path) -> None:
    """Map H5 task metadata to the condition column expected by contrasts."""
    expected = {"euglycemia", "hypoglycemia"}
    files = sorted(cleaned_root.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No cleaned parquet files found in {cleaned_root}.")
    for path in files:
        frame = pd.read_parquet(path)
        if "task" not in frame:
            raise ValueError(f"{path.name} lacks task metadata required for condition mapping.")
        task = frame["task"].astype("string").str.strip().str.lower()
        invalid = task.notna() & ~task.isin(expected)
        if invalid.any():
            values = sorted(task[invalid].dropna().unique().tolist())
            raise ValueError(f"{path.name} has unexpected task labels: {values}")
        frame["condition"] = task
        frame.to_parquet(path, index=False)
    print(f"Mapped task -> condition in {len(files)} cleaned parquet files.")


def main() -> None:
    args = parse_args()
    if args.skip_run and args.skip_analyze:
        raise ValueError("At least one pipeline stage must remain enabled.")

    args.cleaned_root.mkdir(parents=True, exist_ok=True)
    args.analysis_root.mkdir(parents=True, exist_ok=True)

    if not args.skip_run:
        selected = (
            [item.strip() for item in args.run_analyses.split(",") if item.strip()]
            if args.run_analyses
            else None
        )
        result = run_dataset_pipeline(
            config_path=args.run_config,
            input_root=args.raw_root,
            output_root=args.cleaned_root,
            analyses_filter=selected,
            workers=args.workers,
        )
        print(f"run_result={result}")

    if not args.skip_analyze:
        materialize_condition_from_task(args.cleaned_root)
        selected_blocks = (
            [item.strip() for item in args.analysis_blocks.split(",") if item.strip()]
            if args.analysis_blocks
            else None
        )
        selected_contrasts = (
            [item.strip() for item in args.contrasts.split(",") if item.strip()]
            if args.contrasts
            else None
        )
        result = run_cleaned_analysis_pipeline(
            config_path=args.analyze_config,
            cleaned_root=args.cleaned_root,
            output_root=args.analysis_root,
            blocks_filter=selected_blocks,
            contrasts_filter=selected_contrasts,
        )
        print(f"analyze_result={result}")

    print(f"cleaned_root={args.cleaned_root}")
    print(f"analysis_root={args.analysis_root}")


if __name__ == "__main__":
    main()
