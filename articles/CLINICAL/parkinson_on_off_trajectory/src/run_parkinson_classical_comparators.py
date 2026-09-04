from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from parkinson_trajectory_support import (
    ANALYZE_CONFIG_PATH,
    COHORT_COORDINATE_CONTRACT,
    NDT_ANALYSIS_ROOT,
    RESULTS_DIR,
    SUBJECT_COORDINATE_CONTRACT,
    ensure_dir,
)

if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.analysis_pipeline import run_cleaned_analysis_pipeline  # noqa: E402


COHORT_ANALYZE_CONFIG_PATH = NDT_ANALYSIS_ROOT / "config" / "analysis-ds003490-cohort.yaml"
CLASSICAL_ANALYSIS_TYPE = "eeg_classical_comparators"
CLASSICAL_SUBJECT_ANALYSIS_DIRNAME = "classical_analysis_subject"
CLASSICAL_COHORT_ANALYSIS_DIRNAME = "classical_analysis_cohort"
CLASSICAL_PRIMARY_CONTRASTS_CSV = "eeg_classical_primary_contrasts.csv"
CLASSICAL_SUBJECT_METRICS_SUBJECT_CSV = "eeg_classical_subject_metrics_subject_anchor.csv"
CLASSICAL_SUBJECT_METRICS_COHORT_CSV = "eeg_classical_subject_metrics_cohort_anchor.csv"
CLASSICAL_CONTRASTS_SUBJECT_CSV = "eeg_classical_contrasts_subject_anchor.csv"
CLASSICAL_CONTRASTS_COHORT_CSV = "eeg_classical_contrasts_cohort_anchor.csv"
CLASSICAL_SUMMARY_MD = "eeg_classical_summary.md"
CLASSICAL_MANIFEST_JSON = "eeg_classical_manifest.json"
CONTRAST_PRIORITY = {
    "Parkinson_OFF_vs_ON": SUBJECT_COORDINATE_CONTRACT,
    "Control_vs_Parkinson_OFF": COHORT_COORDINATE_CONTRACT,
    "Control_vs_Parkinson_ON": COHORT_COORDINATE_CONTRACT,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run article-facing classical EEG comparator exports for Parkinson ds003490.")
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    return parser.parse_args()


def latest_parquet(root: Path, analysis_type: str) -> Path | None:
    matches = sorted(root.glob(f"ds003490_{analysis_type}_*.parquet"), key=lambda path: path.stat().st_mtime_ns)
    return matches[-1] if matches else None


def load_filtered_parquet(path: Path | None, *, analysis_type: str) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame()
    frame = pd.read_parquet(path)
    if "analysis_type" in frame.columns:
        frame = frame[frame["analysis_type"] == analysis_type].copy()
    return frame.reset_index(drop=True)


def with_contract_columns(frame: pd.DataFrame, contract: str) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    out = frame.copy()
    if "requested_coordinate_contract" not in out.columns:
        out["requested_coordinate_contract"] = contract
    if "resolved_coordinate_contract" not in out.columns:
        out["resolved_coordinate_contract"] = contract
    return out


def select_primary_rows(frames_by_contract: dict[str, pd.DataFrame]) -> pd.DataFrame:
    selected: list[pd.DataFrame] = []
    for contrast_name, contract in CONTRAST_PRIORITY.items():
        frame = with_contract_columns(frames_by_contract.get(contract, pd.DataFrame()), contract)
        if frame.empty or "contrast_name" not in frame.columns:
            continue
        block = frame[frame["contrast_name"] == contrast_name].copy()
        if block.empty:
            continue
        block["primary_contract"] = contract
        selected.append(block)
    if not selected:
        return pd.DataFrame()
    out = pd.concat(selected, ignore_index=True)
    sort_cols = [column for column in ["contrast_name", "q_value", "p_value", "metric"] if column in out.columns]
    return out.sort_values(sort_cols, na_position="last").reset_index(drop=True) if sort_cols else out.reset_index(drop=True)


def article_metric_subset(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "metric" not in frame.columns:
        return frame.copy()
    mask = frame["metric"].astype(str).str.endswith("_median")
    return frame[mask].copy().reset_index(drop=True)


def fmt(value: object) -> str:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return "nan"
    if not pd.notna(parsed):
        return "nan"
    return f"{parsed:.4g}"


def top_rows(frame: pd.DataFrame, contrast_name: str, limit: int = 8) -> pd.DataFrame:
    if frame.empty or "contrast_name" not in frame.columns:
        return pd.DataFrame()
    block = frame[frame["contrast_name"] == contrast_name].copy()
    if block.empty:
        return block
    block["abs_effect_size"] = pd.to_numeric(block.get("effect_size"), errors="coerce").abs()
    sort_cols = [column for column in ["q_value", "p_value", "abs_effect_size"] if column in block.columns]
    ascending_map = {"q_value": True, "p_value": True, "abs_effect_size": False}
    if sort_cols:
        block = block.sort_values(sort_cols, ascending=[ascending_map[column] for column in sort_cols], na_position="last")
    return block.head(limit)


def build_summary(primary_contrasts: pd.DataFrame, subject_frames: dict[str, pd.DataFrame]) -> str:
    lines = [
        "# Classical EEG comparator summary",
        "",
        "This article-facing wrapper re-runs only the `eeg_classical_comparators` block and then applies the same mixed-contract selection rule as the main manuscript.",
        "For clinical readability, the article-facing `primary` table is restricted to median-valued comparator summaries, while the full contract-specific exports retain the wider metric inventory.",
        "",
        "- `cohort_anchored` remains primary for `Control vs Parkinson OFF` and `Control vs Parkinson ON`.",
        "- `subject_anchored` remains primary for `Parkinson OFF vs ON`.",
        "- These rows are intended as clinically familiar comparator surfaces rather than replacement endpoints for the NDT/NMD layers.",
        "",
    ]
    for contrast_name, contract in CONTRAST_PRIORITY.items():
        lines.append(f"## {contrast_name} ({contract})")
        lines.append("")
        rows = top_rows(primary_contrasts, contrast_name)
        if rows.empty:
            lines.extend(["No classical comparator row was retained for this contrast.", ""])
            continue
        for _, row in rows.iterrows():
            lines.append(
                f"- `{row.get('metric')}`: d={fmt(row.get('effect_size'))}, p={fmt(row.get('p_value'))}, q={fmt(row.get('q_value'))}"
            )
        lines.append("")

    for contract, frame in subject_frames.items():
        if frame.empty:
            continue
        lines.append(f"## Exported subject metrics ({contract})")
        lines.append("")
        lines.append(
            f"- rows: `{len(frame)}`; metrics: `{frame['metric'].nunique() if 'metric' in frame.columns else 0}`; "
            f"subjects: `{frame['subject_id'].nunique() if 'subject_id' in frame.columns else 0}`"
        )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ensure_dir(args.results_dir)

    subject_cleaned_dir = args.results_dir / "standard_cleaned_subject"
    cohort_cleaned_dir = args.results_dir / "standard_cleaned_cohort"
    subject_analysis_dir = args.results_dir / CLASSICAL_SUBJECT_ANALYSIS_DIRNAME
    cohort_analysis_dir = args.results_dir / CLASSICAL_COHORT_ANALYSIS_DIRNAME

    ensure_dir(subject_analysis_dir)
    ensure_dir(cohort_analysis_dir)

    subject_result = run_cleaned_analysis_pipeline(
        config_path=ANALYZE_CONFIG_PATH,
        cleaned_root=subject_cleaned_dir,
        output_root=subject_analysis_dir,
        blocks_filter=[CLASSICAL_ANALYSIS_TYPE],
    )
    cohort_result = run_cleaned_analysis_pipeline(
        config_path=COHORT_ANALYZE_CONFIG_PATH,
        cleaned_root=cohort_cleaned_dir,
        output_root=cohort_analysis_dir,
        blocks_filter=[CLASSICAL_ANALYSIS_TYPE],
    )

    subject_metrics_path = latest_parquet(subject_analysis_dir, "subject_metrics")
    subject_contrasts_path = latest_parquet(subject_analysis_dir, "contrast_results")
    cohort_metrics_path = latest_parquet(cohort_analysis_dir, "subject_metrics")
    cohort_contrasts_path = latest_parquet(cohort_analysis_dir, "contrast_results")

    subject_metrics = with_contract_columns(
        load_filtered_parquet(subject_metrics_path, analysis_type=CLASSICAL_ANALYSIS_TYPE),
        SUBJECT_COORDINATE_CONTRACT,
    )
    subject_contrasts = with_contract_columns(
        load_filtered_parquet(subject_contrasts_path, analysis_type=CLASSICAL_ANALYSIS_TYPE),
        SUBJECT_COORDINATE_CONTRACT,
    )
    cohort_metrics = with_contract_columns(
        load_filtered_parquet(cohort_metrics_path, analysis_type=CLASSICAL_ANALYSIS_TYPE),
        COHORT_COORDINATE_CONTRACT,
    )
    cohort_contrasts = with_contract_columns(
        load_filtered_parquet(cohort_contrasts_path, analysis_type=CLASSICAL_ANALYSIS_TYPE),
        COHORT_COORDINATE_CONTRACT,
    )

    primary_contrasts = select_primary_rows(
        {
            SUBJECT_COORDINATE_CONTRACT: article_metric_subset(subject_contrasts),
            COHORT_COORDINATE_CONTRACT: article_metric_subset(cohort_contrasts),
        }
    )

    subject_metrics.to_csv(args.results_dir / CLASSICAL_SUBJECT_METRICS_SUBJECT_CSV, index=False)
    cohort_metrics.to_csv(args.results_dir / CLASSICAL_SUBJECT_METRICS_COHORT_CSV, index=False)
    subject_contrasts.to_csv(args.results_dir / CLASSICAL_CONTRASTS_SUBJECT_CSV, index=False)
    cohort_contrasts.to_csv(args.results_dir / CLASSICAL_CONTRASTS_COHORT_CSV, index=False)
    primary_contrasts.to_csv(args.results_dir / CLASSICAL_PRIMARY_CONTRASTS_CSV, index=False)

    summary_text = build_summary(
        primary_contrasts,
        {
            SUBJECT_COORDINATE_CONTRACT: subject_metrics,
            COHORT_COORDINATE_CONTRACT: cohort_metrics,
        },
    )
    (args.results_dir / CLASSICAL_SUMMARY_MD).write_text(summary_text, encoding="utf-8")

    manifest = {
        "results_dir": str(args.results_dir),
        "analysis_type": CLASSICAL_ANALYSIS_TYPE,
        "contrast_priority": CONTRAST_PRIORITY,
        "subject_pass": {
            "cleaned_dir": str(subject_cleaned_dir),
            "analysis_dir": str(subject_analysis_dir),
            "subject_metrics_path": str(subject_metrics_path) if subject_metrics_path is not None else None,
            "contrast_results_path": str(subject_contrasts_path) if subject_contrasts_path is not None else None,
            "run_result": subject_result,
        },
        "cohort_pass": {
            "cleaned_dir": str(cohort_cleaned_dir),
            "analysis_dir": str(cohort_analysis_dir),
            "subject_metrics_path": str(cohort_metrics_path) if cohort_metrics_path is not None else None,
            "contrast_results_path": str(cohort_contrasts_path) if cohort_contrasts_path is not None else None,
            "run_result": cohort_result,
        },
        "written_files": {
            "subject_metrics_subject": str(args.results_dir / CLASSICAL_SUBJECT_METRICS_SUBJECT_CSV),
            "subject_metrics_cohort": str(args.results_dir / CLASSICAL_SUBJECT_METRICS_COHORT_CSV),
            "contrasts_subject": str(args.results_dir / CLASSICAL_CONTRASTS_SUBJECT_CSV),
            "contrasts_cohort": str(args.results_dir / CLASSICAL_CONTRASTS_COHORT_CSV),
            "primary_contrasts": str(args.results_dir / CLASSICAL_PRIMARY_CONTRASTS_CSV),
            "summary": str(args.results_dir / CLASSICAL_SUMMARY_MD),
        },
        "article_metric_filter": "metric.endswith('_median')",
    }
    (args.results_dir / CLASSICAL_MANIFEST_JSON).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
