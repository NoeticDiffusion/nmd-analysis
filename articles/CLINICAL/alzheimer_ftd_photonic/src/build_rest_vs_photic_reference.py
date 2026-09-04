from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]

DEFAULT_REST_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "alzheimer_ftd_photonic_ds004504_20260528"
FALLBACK_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis"
DEFAULT_PHOTIC_RESULTS_ROOT = ARTICLE_DIR / "results"
DEFAULT_REFERENCE_ROOT = ARTICLE_DIR / "results" / "rest_vs_photic_reference"

GROUP_LABELS = {
    "A": "AD",
    "C": "Healthy",
    "F": "FTD",
}

REST_STAGE_CODE = 0
REST_STAGE_LABEL = "rest_baseline"
REST_STAGE_DISPLAY_LABEL = "Resting baseline"

ANALYSIS_SPECS = (
    {
        "analysis_key": "global_mnj_3d",
        "rest_analysis_type": "global_mnps_jacobian_3d",
        "photic_analysis_type": "global_mnj_3d",
        "analysis_label": "Global 3D MNJ",
        "metric": "mdr_median",
    },
    {
        "analysis_key": "global_mnj_9d",
        "rest_analysis_type": "global_mnps_jacobian_9d",
        "photic_analysis_type": "global_mnj_9d",
        "analysis_label": "Global 9D MNJ",
        "metric": "mdr_median",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an article-local resting-state vs photic reference bundle.")
    parser.add_argument("--rest-analysis-root", type=Path, default=None)
    parser.add_argument("--photic-results-root", type=Path, default=DEFAULT_PHOTIC_RESULTS_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_REFERENCE_ROOT)
    return parser.parse_args()


def _analysis_roots(preferred: Path | None) -> list[Path]:
    ordered: list[Path] = []
    for root in (preferred, DEFAULT_REST_ANALYSIS_ROOT, FALLBACK_ANALYSIS_ROOT):
        if root is None:
            continue
        if root not in ordered:
            ordered.append(root)
    return ordered


def _latest_parquet(roots: Iterable[Path], stem: str) -> Path:
    for root in roots:
        matches = sorted(root.glob(f"ds004504_{stem}_*.parquet"))
        if matches:
            return matches[-1]
    searched = ", ".join(str(root) for root in roots)
    raise FileNotFoundError(f"No {stem} parquet found for ds004504 under: {searched}")


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        if np.isfinite(value):
            return float(value)
        return None
    if pd.isna(value):
        return None
    return value


def _load_rest_subject_metrics(analysis_roots: list[Path]) -> pd.DataFrame:
    subject_metrics_path = _latest_parquet(analysis_roots, "subject_metrics")
    frame = pd.read_parquet(subject_metrics_path)
    rows: list[pd.DataFrame] = []
    for spec in ANALYSIS_SPECS:
        sub = frame[
            (frame["analysis_type"].astype(str) == spec["rest_analysis_type"])
            & (frame["metric"].astype(str) == spec["metric"])
        ].copy()
        if sub.empty:
            continue
        keep = sub[["subject_id", "group", "value"]].copy()
        keep["dataset"] = "ds004504"
        keep["analysis_key"] = spec["analysis_key"]
        keep["analysis_label"] = spec["analysis_label"]
        keep["metric"] = spec["metric"]
        keep["stage_code"] = REST_STAGE_CODE
        keep["stage_label"] = REST_STAGE_LABEL
        keep["stage_display_label"] = REST_STAGE_DISPLAY_LABEL
        keep["network"] = "global"
        rows.append(keep)
    if not rows:
        raise RuntimeError("No resting-state mdr_median rows were found in the ds004504 subject metrics.")
    return pd.concat(rows, ignore_index=True), subject_metrics_path


def _load_rest_effects(analysis_roots: list[Path]) -> tuple[pd.DataFrame, Path]:
    contrast_results_path = _latest_parquet(analysis_roots, "contrast_results")
    frame = pd.read_parquet(contrast_results_path)
    rows: list[pd.DataFrame] = []
    for spec in ANALYSIS_SPECS:
        sub = frame[
            (frame["contrast_name"].astype(str) == "AD_vs_Healthy")
            & (frame["analysis_type"].astype(str) == spec["rest_analysis_type"])
            & (frame["metric"].astype(str) == spec["metric"])
        ].copy()
        if sub.empty:
            continue
        keep = sub[
            [
                "contrast_name",
                "left_n",
                "right_n",
                "left_mean",
                "right_mean",
                "effect_size",
                "effect_estimate",
                "p_value",
                "q_value",
            ]
        ].copy()
        keep["dataset"] = "ds004504"
        keep["analysis_key"] = spec["analysis_key"]
        keep["analysis_label"] = spec["analysis_label"]
        keep["metric"] = spec["metric"]
        keep["stage_code"] = REST_STAGE_CODE
        keep["stage_label"] = REST_STAGE_LABEL
        keep["stage_display_label"] = REST_STAGE_DISPLAY_LABEL
        keep["network"] = "global"
        rows.append(keep)
    if not rows:
        raise RuntimeError("No resting-state AD_vs_Healthy mdr_median rows were found in the ds004504 contrasts.")
    return pd.concat(rows, ignore_index=True), contrast_results_path


def _load_photic_subject_metrics(photic_results_root: Path) -> pd.DataFrame:
    metric_path = photic_results_root / "subject_stage_region_metrics.csv"
    frame = pd.read_csv(metric_path)
    rows: list[pd.DataFrame] = []
    for spec in ANALYSIS_SPECS:
        sub = frame[
            (frame["analysis_type"].astype(str) == spec["photic_analysis_type"])
            & (frame["metric"].astype(str) == spec["metric"])
            & (frame["network"].astype(str) == "global")
        ].copy()
        if sub.empty:
            continue
        keep = sub[
            [
                "dataset",
                "subject_id",
                "group",
                "value",
                "stage_code",
                "stage_label",
                "stage_display_label",
                "network",
            ]
        ].copy()
        keep["analysis_key"] = spec["analysis_key"]
        keep["analysis_label"] = spec["analysis_label"]
        keep["metric"] = spec["metric"]
        rows.append(keep)
    if not rows:
        raise RuntimeError("No photic global mdr_median rows were found in the photic subject metrics.")
    return pd.concat(rows, ignore_index=True), metric_path


def _load_photic_effects(photic_results_root: Path) -> tuple[pd.DataFrame, Path]:
    contrast_path = photic_results_root / "group_frequency_contrasts.csv"
    frame = pd.read_csv(contrast_path)
    rows: list[pd.DataFrame] = []
    for spec in ANALYSIS_SPECS:
        sub = frame[
            (frame["contrast_name"].astype(str) == "AD_vs_Healthy")
            & (frame["analysis_type"].astype(str) == spec["photic_analysis_type"])
            & (frame["metric"].astype(str) == spec["metric"])
            & (frame["network"].astype(str) == "global")
        ].copy()
        if sub.empty:
            continue
        keep = sub[
            [
                "dataset",
                "contrast_name",
                "left_n",
                "right_n",
                "left_mean",
                "right_mean",
                "effect_size",
                "effect_estimate",
                "p_value",
                "q_value",
                "stage_code",
                "stage_label",
                "stage_display_label",
                "network",
            ]
        ].copy()
        keep["analysis_key"] = spec["analysis_key"]
        keep["analysis_label"] = spec["analysis_label"]
        keep["metric"] = spec["metric"]
        rows.append(keep)
    if not rows:
        raise RuntimeError("No photic AD_vs_Healthy global mdr_median rows were found in the contrast summary.")
    return pd.concat(rows, ignore_index=True), contrast_path


def _build_group_summary(subject_values: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "analysis_key",
        "analysis_label",
        "metric",
        "group",
        "stage_code",
        "stage_label",
        "stage_display_label",
    ]
    out = (
        subject_values.groupby(group_cols, dropna=False, as_index=False)
        .agg(
            n=("value", "size"),
            mean_value=("value", "mean"),
            median_value=("value", "median"),
            sd_value=("value", "std"),
        )
        .reset_index(drop=True)
    )
    out["sem_value"] = out["sd_value"] / np.sqrt(out["n"].clip(lower=1))
    out["group_label"] = out["group"].astype(str).map(GROUP_LABELS).fillna(out["group"].astype(str))
    return out.sort_values(["analysis_key", "group_label", "stage_code"]).reset_index(drop=True)


def _build_effect_summary(rest_effects: pd.DataFrame, photic_effects: pd.DataFrame) -> pd.DataFrame:
    merged = pd.concat([rest_effects, photic_effects], ignore_index=True)
    merged["abs_effect_size"] = pd.to_numeric(merged["effect_size"], errors="coerce").abs()
    return merged.sort_values(["analysis_key", "stage_code"]).reset_index(drop=True)


def _build_summary_markdown(group_summary: pd.DataFrame, effect_summary: pd.DataFrame) -> str:
    selection_note = "The photic stages come from the current canonical ds006036 article export."
    manifest_path = DEFAULT_PHOTIC_RESULTS_ROOT / "paper_exports_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            selection_summary = manifest.get("selection_summary") or {}
            if selection_summary.get("selection_mode") == "blocks::center_within_exact_block_interval":
                selection_note = (
                    "The photic stages come from the exact block-native ds006036 export, "
                    "using original windows whose centers fall inside inferred photic blocks."
                )
        except Exception:
            selection_note = "The photic stages come from the current canonical ds006036 article export."
    lines = [
        "# Resting-state vs photic reference",
        "",
        "- Resting-state baseline comes from `ds004504` with the same diagnostic contrasts (`AD`, `FTD`, `Healthy`).",
        f"- {selection_note}",
        "",
    ]
    for analysis_key in ("global_mnj_9d", "global_mnj_3d"):
        block = effect_summary[effect_summary["analysis_key"] == analysis_key].copy()
        if block.empty:
            continue
        lines.extend([f"## {analysis_key}", ""])
        baseline = block[block["stage_label"] == REST_STAGE_LABEL]
        if not baseline.empty:
            row = baseline.iloc[0]
            lines.append(
                f"- Resting baseline `AD vs Healthy` `{row['metric']}`: "
                f"d={float(row['effect_size']):.3f}, p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}."
            )
        photic = block[block["stage_label"] != REST_STAGE_LABEL].copy()
        if not photic.empty:
            top = photic.sort_values("abs_effect_size", ascending=False).iloc[0]
            lines.append(
                f"- Strongest photic stage: `{top['stage_display_label']}` with "
                f"d={float(top['effect_size']):.3f}, p={float(top['p_value']):.4g}, q={float(top['q_value']):.4g}."
            )
        lines.append("")

    means = group_summary[group_summary["analysis_key"] == "global_mnj_9d"].copy()
    if not means.empty:
        ad = means[means["group_label"] == "AD"].sort_values("stage_code")
        healthy = means[means["group_label"] == "Healthy"].sort_values("stage_code")
        if not ad.empty and not healthy.empty:
            lines.extend(
                [
                    "## Figure-2 note",
                    "",
                    "- The frequency-stress figure uses subject-level `global_mnj_9d` `mdr_median` means with `AD` and `Healthy` traced from resting baseline through `PHOTO 5/10/15/20 Hz`.",
                    "",
                ]
            )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    analysis_roots = _analysis_roots(args.rest_analysis_root)
    args.output_root.mkdir(parents=True, exist_ok=True)

    rest_subject_values, rest_subject_metrics_path = _load_rest_subject_metrics(analysis_roots)
    rest_effects, rest_contrast_results_path = _load_rest_effects(analysis_roots)
    photic_subject_values, photic_metric_path = _load_photic_subject_metrics(args.photic_results_root)
    photic_effects, photic_contrast_path = _load_photic_effects(args.photic_results_root)

    subject_values = pd.concat([rest_subject_values, photic_subject_values], ignore_index=True)
    subject_values["group_label"] = subject_values["group"].astype(str).map(GROUP_LABELS).fillna(subject_values["group"].astype(str))
    group_summary = _build_group_summary(subject_values)
    effect_summary = _build_effect_summary(rest_effects, photic_effects)

    subject_path = args.output_root / "rest_vs_photic_mdr_subject_values.csv"
    group_path = args.output_root / "rest_vs_photic_mdr_group_summary.csv"
    effect_path = args.output_root / "rest_vs_photic_mdr_ad_vs_healthy_effects.csv"
    summary_path = args.output_root / "rest_vs_photic_reference.md"
    manifest_path = args.output_root / "rest_vs_photic_reference_manifest.json"

    subject_values.to_csv(subject_path, index=False)
    group_summary.to_csv(group_path, index=False)
    effect_summary.to_csv(effect_path, index=False)
    summary_path.write_text(_build_summary_markdown(group_summary, effect_summary), encoding="utf-8")

    manifest = {
        "analysis_specs": list(ANALYSIS_SPECS),
        "rest_analysis_roots_considered": [str(root) for root in analysis_roots],
        "rest_subject_metrics_path": str(rest_subject_metrics_path),
        "rest_contrast_results_path": str(rest_contrast_results_path),
        "photic_subject_metrics_path": str(photic_metric_path),
        "photic_contrast_results_path": str(photic_contrast_path),
        "output_files": {
            "subject_values": str(subject_path),
            "group_summary": str(group_path),
            "effect_summary": str(effect_path),
            "summary_md": str(summary_path),
        },
        "stage_order": [
            _json_ready(stage)
            for stage in group_summary[["stage_code", "stage_label", "stage_display_label"]]
            .drop_duplicates()
            .sort_values("stage_code")
            .to_dict("records")
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote subject reference rows to {subject_path}")
    print(f"Wrote group summary to {group_path}")
    print(f"Wrote effect summary to {effect_path}")


if __name__ == "__main__":
    main()
