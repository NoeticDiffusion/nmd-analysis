from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from parkinson_auditory_support import (
    ANALYZE_CONFIG_PATH,
    ARTICLE_METRIC_RANKING_CSV,
    ARTICLE_METRIC_SUMMARY_MD,
    DATASET_ID,
    DATASET_ROOT,
    EVENT_CONTRASTS_CSV,
    EVENT_METRIC_DIR,
    MANIFEST_JSON,
    NDT_ANALYSIS_ROOT,
    RESULTS_DIR,
    RUN_CONFIG_PATH,
    STANDARD_ANALYSIS_DIR,
    STANDARD_CLEANED_DIR,
    SUMMARY_PATH,
    WRAPPER_SUMMARY_MD,
    ensure_dir,
)

if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.analysis_pipeline import run_cleaned_analysis_pipeline  # noqa: E402
from ndt_analysis.pipeline import run_dataset_pipeline  # noqa: E402


SRC_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full ds004574 Parkinson auditory recall pipeline.")
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--limit-h5", type=int, default=None)
    return parser.parse_args()


def latest_parquet(root: Path, analysis_type: str) -> Path | None:
    matches = sorted(root.glob(f"{DATASET_ID}_{analysis_type}_*.parquet"), key=lambda path: path.stat().st_mtime_ns)
    return matches[-1] if matches else None


def fmt(value: object) -> str:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return "nan"
    if not pd.notna(parsed):
        return "nan"
    return f"{parsed:.4g}"


def build_article_metric_ranking(standard_results: pd.DataFrame, wrapper_contrasts: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    if not standard_results.empty:
        keep_cols = [column for column in ["contrast_name", "analysis_type", "metric", "network", "effect_size", "p_value", "q_value"] if column in standard_results.columns]
        standard = standard_results[keep_cols].copy()
        standard["source_layer"] = "standard"
        standard["comparison_scope"] = standard.get("contrast_name", "standard")
        standard["segment_label"] = standard.get("network", "global")
        standard["dims"] = standard.get("dims")
        frames.append(standard)
    if not wrapper_contrasts.empty:
        keep_cols = [
            column
            for column in [
                "contrast_name",
                "comparison_scope",
                "analysis_type",
                "segment_label",
                "metric",
                "network",
                "dims",
                "effect_size",
                "p_value",
                "q_value",
            ]
            if column in wrapper_contrasts.columns
        ]
        wrapper = wrapper_contrasts[keep_cols].copy()
        wrapper["source_layer"] = "wrapper"
        frames.append(wrapper)
    if not frames:
        return pd.DataFrame()
    ranking = pd.concat(frames, ignore_index=True)
    ranking["abs_effect_size"] = pd.to_numeric(ranking["effect_size"], errors="coerce").abs()
    ranking["q_bucket"] = pd.to_numeric(ranking["q_value"], errors="coerce").fillna(1.0) <= 0.1
    ranking = ranking.sort_values(
        ["q_bucket", "q_value", "abs_effect_size", "p_value"],
        ascending=[False, True, False, True],
        na_position="last",
    ).reset_index(drop=True)
    ranking["selection_rank"] = range(1, len(ranking) + 1)
    return ranking


def build_metric_summary(ranking: pd.DataFrame) -> str:
    lines = ["# Parkinson auditory recall metric ranking", ""]
    if ranking.empty:
        lines.extend(["No candidate rows were produced.", ""])
        return "\n".join(lines)
    lines.extend(["## Top q <= 0.1 candidates", ""])
    top_q = ranking[pd.to_numeric(ranking["q_value"], errors="coerce") <= 0.1].head(15)
    if top_q.empty:
        lines.extend(["No rows reached q <= 0.1.", ""])
    else:
        for _, row in top_q.iterrows():
            lines.append(
                f"- `{row['source_layer']}` / `{row['contrast_name']}` / `{row['analysis_type']}` / "
                f"`{row.get('segment_label', 'global')}` / `{row['metric']}`: "
                f"d={fmt(row.get('effect_size'))}, p={fmt(row.get('p_value'))}, q={fmt(row.get('q_value'))}"
            )
        lines.append("")
    lines.extend(["## Largest effects overall", ""])
    for _, row in ranking.head(15).iterrows():
        lines.append(
            f"- `{row['source_layer']}` / `{row['contrast_name']}` / `{row['analysis_type']}` / "
            f"`{row.get('segment_label', 'global')}` / `{row['metric']}`: "
            f"|d|={fmt(row.get('abs_effect_size'))}, q={fmt(row.get('q_value'))}"
        )
    lines.append("")
    return "\n".join(lines)


def build_summary(standard_results: pd.DataFrame, wrapper_contrasts: pd.DataFrame, ranking: pd.DataFrame) -> str:
    lines = [
        "# Parkinson auditory recall summary",
        "",
        "This run uses the fixed `ds004574` subject-anchored bundle and treats `raw_*` labels as the event surface while leaving `labels/stage` out of the inferential story.",
        "",
        "## Standard ndt-analysis layer",
        "",
    ]
    if standard_results.empty:
        lines.extend(["No standard contrast results were produced.", ""])
    else:
        top_standard = standard_results.sort_values(
            ["q_value", "p_value", "effect_size"],
            ascending=[True, True, False],
            na_position="last",
        ).head(10)
        for _, row in top_standard.iterrows():
            lines.append(
                f"- `{row['analysis_type']}` / `{row['metric']}`: d={fmt(row.get('effect_size'))}, "
                f"p={fmt(row.get('p_value'))}, q={fmt(row.get('q_value'))}"
            )
        lines.append("")

    lines.extend(["## Event-locked wrapper layer", ""])
    if wrapper_contrasts.empty:
        lines.extend(["No wrapper contrasts were produced.", ""])
    else:
        for contrast_name in ["All_Auditory_vs_OtherMean", "All_Auditory_vs_Standard", "Control_vs_Parkinson"]:
            block = wrapper_contrasts[wrapper_contrasts["contrast_name"] == contrast_name].copy()
            if block.empty:
                continue
            lines.append(f"### {contrast_name}")
            lines.append("")
            block = block.sort_values(["q_value", "p_value", "abs_effect_size"], ascending=[True, True, False], na_position="last")
            for _, row in block.head(8).iterrows():
                lines.append(
                    f"- `{row['analysis_type']}` / `{row['segment_label']}` / `{row['metric']}`: "
                    f"d={fmt(row.get('effect_size'))}, p={fmt(row.get('p_value'))}, q={fmt(row.get('q_value'))}"
                )
            lines.append("")

    lines.extend(["## Candidate article metrics", ""])
    if ranking.empty:
        lines.extend(["No combined ranking rows were produced.", ""])
    else:
        for _, row in ranking.head(12).iterrows():
            lines.append(
                f"- `{row['source_layer']}` / `{row['contrast_name']}` / `{row['analysis_type']}` / "
                f"`{row.get('segment_label', 'global')}` / `{row['metric']}`: "
                f"|d|={fmt(row.get('abs_effect_size'))}, q={fmt(row.get('q_value'))}"
            )
        lines.append("")

    lines.extend(
        [
            "## Caveats",
            "",
            "- Event subtype labels come from behavior-enriched `raw_*` provenance rather than a stage-coded trial map.",
            "- `raw_nan_onset_sec` is excluded from the article-local wrapper by construction and is not treated as a meaningful event.",
            "- The bundle exposes no regional outputs, no cohort-anchor layer, and no ComBat normalization.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ensure_dir(args.results_dir)
    ensure_dir(STANDARD_CLEANED_DIR)
    ensure_dir(STANDARD_ANALYSIS_DIR)
    ensure_dir(EVENT_METRIC_DIR)

    run_result = run_dataset_pipeline(
        config_path=RUN_CONFIG_PATH,
        input_root=args.dataset_root,
        output_root=STANDARD_CLEANED_DIR,
        workers=4,
    )
    analyze_result = run_cleaned_analysis_pipeline(
        config_path=ANALYZE_CONFIG_PATH,
        cleaned_root=STANDARD_CLEANED_DIR,
        output_root=STANDARD_ANALYSIS_DIR,
    )

    compute_cmd = [
        sys.executable,
        str(SRC_DIR / "compute_parkinson_auditory_event_metrics.py"),
        "--dataset-root",
        str(args.dataset_root),
        "--output-dir",
        str(EVENT_METRIC_DIR),
    ]
    if args.limit_h5 is not None:
        compute_cmd.extend(["--limit-h5", str(args.limit_h5)])
    subprocess.run(compute_cmd, check=True)
    subprocess.run(
        [
            sys.executable,
            str(SRC_DIR / "export_parkinson_auditory_contrasts.py"),
            "--input-dir",
            str(EVENT_METRIC_DIR),
            "--output-dir",
            str(args.results_dir),
        ],
        check=True,
    )

    contrast_path = latest_parquet(STANDARD_ANALYSIS_DIR, "contrast_results")
    standard_results = pd.read_parquet(contrast_path) if contrast_path is not None else pd.DataFrame()
    wrapper_contrasts = (
        pd.read_csv(args.results_dir / EVENT_CONTRASTS_CSV, low_memory=False)
        if (args.results_dir / EVENT_CONTRASTS_CSV).exists()
        else pd.DataFrame()
    )
    ranking = build_article_metric_ranking(standard_results, wrapper_contrasts)
    ranking.to_csv(args.results_dir / ARTICLE_METRIC_RANKING_CSV, index=False)
    (args.results_dir / ARTICLE_METRIC_SUMMARY_MD).write_text(build_metric_summary(ranking), encoding="utf-8")
    SUMMARY_PATH.write_text(build_summary(standard_results, wrapper_contrasts, ranking), encoding="utf-8")

    manifest = {
        "dataset_root": str(args.dataset_root),
        "results_dir": str(args.results_dir),
        "run_result": run_result,
        "analyze_result": analyze_result,
        "standard_contrast_path": str(contrast_path) if contrast_path is not None else None,
        "wrapper_event_contrasts": str(args.results_dir / EVENT_CONTRASTS_CSV),
        "wrapper_summary_path": str(args.results_dir / WRAPPER_SUMMARY_MD),
        "article_metric_ranking": str(args.results_dir / ARTICLE_METRIC_RANKING_CSV),
        "article_metric_summary": str(args.results_dir / ARTICLE_METRIC_SUMMARY_MD),
        "summary_path": str(SUMMARY_PATH),
    }
    (args.results_dir / MANIFEST_JSON).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
