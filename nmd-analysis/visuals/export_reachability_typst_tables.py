from __future__ import annotations

import argparse
from pathlib import Path
import sys

THIS_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = THIS_DIR.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from nmd_analysis.analysis_config import load_analysis_config
from nmd_analysis.reachability_typst import (
    build_contrast_displays,
    build_reachability_typst_sections,
    load_latest_contrast_results,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ANALYSIS_DIR = REPO_ROOT / "data" / "analysis"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export reachability Typst table rows from nmd-analysis Parquet outputs.")
    parser.add_argument("--config", required=True, help="Path to analysis YAML for the dataset.")
    parser.add_argument("--analysis-dir", default=str(DEFAULT_ANALYSIS_DIR), help="Directory containing analysis parquet outputs.")
    parser.add_argument("--out", required=True, help="Output Typst rows file.")
    parser.add_argument("--horizon", type=int, default=4, help="Max horizon H to export.")
    parser.add_argument("--p-threshold", type=float, default=None, help="Optional raw-p display threshold.")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    dataset = load_analysis_config(config_path).dataset
    analysis_dir = Path(args.analysis_dir).resolve()
    output_path = Path(args.out).resolve()

    displays = build_contrast_displays(config_path)
    frame = load_latest_contrast_results(analysis_dir, dataset)
    lines = build_reachability_typst_sections(
        frame,
        displays,
        horizon=int(args.horizon),
        p_threshold=args.p_threshold,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
