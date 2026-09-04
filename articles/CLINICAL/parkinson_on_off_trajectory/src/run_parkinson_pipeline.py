from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from parkinson_trajectory_support import (
    ANALYZE_CONFIG_PATH,
    COHORT_COORDINATE_CONTRACT,
    DATASET_ROOT,
    ESB_CONTRASTS_CSV,
    EVENT_CONTRASTS_CSV,
    MANIFEST_JSON,
    NDT_ANALYSIS_ROOT,
    RESULTS_DIR,
    RUN_CONFIG_PATH,
    SUBJECT_COORDINATE_CONTRACT,
    ensure_dir,
)

if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.analysis_pipeline import run_cleaned_analysis_pipeline  # noqa: E402
from ndt_analysis.pipeline import run_dataset_pipeline  # noqa: E402


SRC_DIR = Path(__file__).resolve().parent
COHORT_RUN_CONFIG_PATH = NDT_ANALYSIS_ROOT / "config" / "ndt-analysis-ds003490-cohort.yaml"
COHORT_ANALYZE_CONFIG_PATH = NDT_ANALYSIS_ROOT / "config" / "analysis-ds003490-cohort.yaml"
CONTRAST_PRIORITY = {
    "Parkinson_OFF_vs_ON": SUBJECT_COORDINATE_CONTRACT,
    "Control_vs_Parkinson_OFF": COHORT_COORDINATE_CONTRACT,
    "Control_vs_Parkinson_ON": COHORT_COORDINATE_CONTRACT,
}
PRIMARY_STANDARD_CONTRASTS_CSV = "primary_standard_contrasts.csv"
PRIMARY_EVENT_CONTRASTS_CSV = "primary_event_contrasts.csv"
PRIMARY_ESB_CONTRASTS_CSV = "primary_trajectory_esb_contrasts.csv"
SUMMARY_FILENAME = "exploratory_summary.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the dual-contract Parkinson ds003490 pipeline.")
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--limit-h5", type=int, default=None)
    return parser.parse_args()


def latest_parquet(root: Path, analysis_type: str) -> Path | None:
    matches = sorted(root.glob(f"ds003490_{analysis_type}_*.parquet"), key=lambda path: path.stat().st_mtime_ns)
    return matches[-1] if matches else None


def fmt(value: object) -> str:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return "nan"
    if not pd.notna(parsed):
        return "nan"
    return f"{parsed:.4g}"


def top_rows(frame: pd.DataFrame, contrast_name: str, limit: int = 6) -> pd.DataFrame:
    block = frame[frame["contrast_name"] == contrast_name].copy()
    if block.empty:
        return block
    effect_col = "effect_size" if "effect_size" in block.columns else "effect_estimate"
    block["abs_effect_proxy"] = pd.to_numeric(block[effect_col], errors="coerce").abs()
    sort_cols = [column for column in ["q_value", "p_value", "abs_effect_proxy"] if column in block.columns]
    if sort_cols:
        ascending_map = {"q_value": True, "p_value": True, "abs_effect_proxy": False}
        block = block.sort_values(sort_cols, ascending=[ascending_map[column] for column in sort_cols], na_position="last")
    return block.head(limit)


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
        if frame.empty:
            continue
        block = frame[frame["contrast_name"] == contrast_name].copy()
        if block.empty:
            continue
        block["primary_contract"] = contract
        selected.append(block)
    if not selected:
        return pd.DataFrame()
    out = pd.concat(selected, ignore_index=True)
    sort_cols = [
        column
        for column in ["contrast_name", "q_value", "p_value", "analysis_type", "segment_label", "network", "metric"]
        if column in out.columns
    ]
    return out.sort_values(sort_cols, na_position="last").reset_index(drop=True) if sort_cols else out.reset_index(drop=True)


def run_wrapper_pass(dataset_root: Path, event_metric_dir: Path, wrapper_dir: Path, contract: str, limit_h5: int | None) -> None:
    ensure_dir(event_metric_dir)
    ensure_dir(wrapper_dir)
    compute_cmd = [
        sys.executable,
        str(SRC_DIR / "compute_parkinson_event_metrics.py"),
        "--dataset-root",
        str(dataset_root),
        "--output-dir",
        str(event_metric_dir),
        "--coordinate-contract",
        contract,
    ]
    if limit_h5 is not None:
        compute_cmd.extend(["--limit-h5", str(limit_h5)])
    subprocess.run(compute_cmd, check=True)
    subprocess.run(
        [
            sys.executable,
            str(SRC_DIR / "export_parkinson_contrasts.py"),
            "--input-dir",
            str(event_metric_dir),
            "--output-dir",
            str(wrapper_dir),
        ],
        check=True,
    )


def run_standard_pass(
    dataset_root: Path,
    cleaned_dir: Path,
    analysis_dir: Path,
    *,
    run_config_path: Path,
    analyze_config_path: Path,
) -> tuple[dict[str, object], dict[str, object], Path | None]:
    ensure_dir(cleaned_dir)
    ensure_dir(analysis_dir)
    run_result = run_dataset_pipeline(
        config_path=run_config_path,
        input_root=dataset_root,
        output_root=cleaned_dir,
        workers=4,
    )
    analyze_result = run_cleaned_analysis_pipeline(
        config_path=analyze_config_path,
        cleaned_root=cleaned_dir,
        output_root=analysis_dir,
    )
    contrast_path = latest_parquet(analysis_dir, "contrast_results")
    return run_result, analyze_result, contrast_path


def load_csv_if_exists(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False) if path.exists() else pd.DataFrame()


def build_summary(
    standard_results: pd.DataFrame,
    wrapper_contrasts: pd.DataFrame,
    esb_contrasts: pd.DataFrame,
) -> str:
    lines = [
        "# Exploratory Parkinson ON/OFF summary",
        "",
        "This rerun splits inference by coordinate contract: `cohort_anchored` is primary for disease-state contrasts (`Control vs Parkinson OFF`, plus disease-facing `Control vs Parkinson ON` context), while `subject_anchored` remains primary for the paired pharmacology contrast (`Parkinson OFF vs ON`).",
        "",
        "Oddball segmentation now prefers H5 `event_windows/*` start/stop indices when present, with guarded fallback to the older nearest-time mapping.",
        "",
        "## Standard ndt-analysis layer",
        "",
    ]
    if standard_results.empty:
        lines.extend(["No merged standard contrast rows were produced.", ""])
    else:
        for contrast_name, contract in CONTRAST_PRIORITY.items():
            lines.append(f"### {contrast_name} ({contract})")
            lines.append("")
            rows = top_rows(standard_results, contrast_name)
            if rows.empty:
                lines.extend(["No rows were retained for this contrast.", ""])
                continue
            for _, row in rows.iterrows():
                context = [str(row.get("analysis_type"))]
                if pd.notna(row.get("network")):
                    context.append(str(row.get("network")))
                if pd.notna(row.get("metric")):
                    context.append(str(row.get("metric")))
                lines.append(
                    f"- `{' / '.join(context)}`: d={fmt(row.get('effect_size'))}, p={fmt(row.get('p_value'))}, q={fmt(row.get('q_value'))}"
                )
            lines.append("")

    lines.extend(["## Event-locked trajectory layer", ""])
    if wrapper_contrasts.empty:
        lines.extend(["No merged wrapper event contrasts were produced.", ""])
    else:
        for contrast_name, contract in CONTRAST_PRIORITY.items():
            rows = top_rows(wrapper_contrasts, contrast_name, limit=6)
            if rows.empty:
                continue
            lines.append(f"### {contrast_name} ({contract})")
            lines.append("")
            for _, row in rows.iterrows():
                lines.append(
                    f"- `{row['analysis_type']}` / `{row['segment_label']}` / `{row['network']}` / `{row['metric']}`: "
                    f"d={fmt(row.get('effect_size'))}, p={fmt(row.get('p_value'))}, q={fmt(row.get('q_value'))}"
                )
            lines.append("")

    lines.extend(["## Trajectory ESB", ""])
    if esb_contrasts.empty:
        lines.extend(["No merged ESB-style rows were produced.", ""])
    else:
        for contrast_name, contract in CONTRAST_PRIORITY.items():
            rows = top_rows(esb_contrasts, contrast_name, limit=4)
            if rows.empty:
                continue
            lines.append(f"### {contrast_name} ({contract})")
            lines.append("")
            for _, row in rows.iterrows():
                lines.append(
                    f"- `{row['segment_label']}` / `{row['network']}` / `{row['metric']}`: "
                    f"d={fmt(row.get('effect_size'))}, p={fmt(row.get('p_value'))}, q={fmt(row.get('q_value'))}"
                )
            lines.append("")

    lines.extend(
        [
            "## Caveats",
            "",
            "- Oddball structure is still event-driven inside a run indexed as `task=rest`, so event-locking remains a processed-window approximation rather than raw-trial EEG reconstruction.",
            "- Standard/MNJ/reachability outputs come from the repository `ndt-analysis` pipeline; trajectory hysteresis and ESB-style scores remain article-local exploratory layers.",
            "- Control subjects have no medication pairing, so disease-state and pharmacology questions are intentionally answered with different optimal coordinate contracts.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ensure_dir(args.results_dir)

    standard_subject_cleaned_dir = args.results_dir / "standard_cleaned_subject"
    standard_subject_analysis_dir = args.results_dir / "standard_analysis_subject"
    standard_cohort_cleaned_dir = args.results_dir / "standard_cleaned_cohort"
    standard_cohort_analysis_dir = args.results_dir / "standard_analysis_cohort"
    event_metric_subject_dir = args.results_dir / "event_metrics_subject"
    event_metric_cohort_dir = args.results_dir / "event_metrics_cohort"
    wrapper_subject_dir = args.results_dir / "wrapper_subject"
    wrapper_cohort_dir = args.results_dir / "wrapper_cohort"
    summary_path = args.results_dir / SUMMARY_FILENAME

    subject_run_result, subject_analyze_result, subject_standard_contrast_path = run_standard_pass(
        args.dataset_root,
        standard_subject_cleaned_dir,
        standard_subject_analysis_dir,
        run_config_path=RUN_CONFIG_PATH,
        analyze_config_path=ANALYZE_CONFIG_PATH,
    )
    cohort_run_result, cohort_analyze_result, cohort_standard_contrast_path = run_standard_pass(
        args.dataset_root,
        standard_cohort_cleaned_dir,
        standard_cohort_analysis_dir,
        run_config_path=COHORT_RUN_CONFIG_PATH,
        analyze_config_path=COHORT_ANALYZE_CONFIG_PATH,
    )

    run_wrapper_pass(
        args.dataset_root,
        event_metric_subject_dir,
        wrapper_subject_dir,
        SUBJECT_COORDINATE_CONTRACT,
        args.limit_h5,
    )
    run_wrapper_pass(
        args.dataset_root,
        event_metric_cohort_dir,
        wrapper_cohort_dir,
        COHORT_COORDINATE_CONTRACT,
        args.limit_h5,
    )

    standard_by_contract = {
        SUBJECT_COORDINATE_CONTRACT: (
            pd.read_parquet(subject_standard_contrast_path) if subject_standard_contrast_path is not None else pd.DataFrame()
        ),
        COHORT_COORDINATE_CONTRACT: (
            pd.read_parquet(cohort_standard_contrast_path) if cohort_standard_contrast_path is not None else pd.DataFrame()
        ),
    }
    wrapper_by_contract = {
        SUBJECT_COORDINATE_CONTRACT: load_csv_if_exists(wrapper_subject_dir / EVENT_CONTRASTS_CSV),
        COHORT_COORDINATE_CONTRACT: load_csv_if_exists(wrapper_cohort_dir / EVENT_CONTRASTS_CSV),
    }
    esb_by_contract = {
        SUBJECT_COORDINATE_CONTRACT: load_csv_if_exists(wrapper_subject_dir / ESB_CONTRASTS_CSV),
        COHORT_COORDINATE_CONTRACT: load_csv_if_exists(wrapper_cohort_dir / ESB_CONTRASTS_CSV),
    }

    primary_standard = select_primary_rows(standard_by_contract)
    primary_wrapper = select_primary_rows(wrapper_by_contract)
    primary_esb = select_primary_rows(esb_by_contract)

    primary_standard.to_csv(args.results_dir / PRIMARY_STANDARD_CONTRASTS_CSV, index=False)
    primary_wrapper.to_csv(args.results_dir / PRIMARY_EVENT_CONTRASTS_CSV, index=False)
    primary_esb.to_csv(args.results_dir / PRIMARY_ESB_CONTRASTS_CSV, index=False)
    summary_path.write_text(build_summary(primary_standard, primary_wrapper, primary_esb), encoding="utf-8")

    manifest = {
        "dataset_root": str(args.dataset_root),
        "results_dir": str(args.results_dir),
        "contrast_priority": CONTRAST_PRIORITY,
        "standard_subject": {
            "coordinate_contract": SUBJECT_COORDINATE_CONTRACT,
            "config_path": str(RUN_CONFIG_PATH),
            "analysis_config_path": str(ANALYZE_CONFIG_PATH),
            "cleaned_dir": str(standard_subject_cleaned_dir),
            "analysis_dir": str(standard_subject_analysis_dir),
            "contrast_path": str(subject_standard_contrast_path) if subject_standard_contrast_path is not None else None,
            "run_result": subject_run_result,
            "analyze_result": subject_analyze_result,
        },
        "standard_cohort": {
            "coordinate_contract": COHORT_COORDINATE_CONTRACT,
            "config_path": str(COHORT_RUN_CONFIG_PATH),
            "analysis_config_path": str(COHORT_ANALYZE_CONFIG_PATH),
            "cleaned_dir": str(standard_cohort_cleaned_dir),
            "analysis_dir": str(standard_cohort_analysis_dir),
            "contrast_path": str(cohort_standard_contrast_path) if cohort_standard_contrast_path is not None else None,
            "run_result": cohort_run_result,
            "analyze_result": cohort_analyze_result,
        },
        "wrapper_subject": {
            "coordinate_contract": SUBJECT_COORDINATE_CONTRACT,
            "event_metric_dir": str(event_metric_subject_dir),
            "wrapper_dir": str(wrapper_subject_dir),
            "event_contrasts": str(wrapper_subject_dir / EVENT_CONTRASTS_CSV),
            "esb_contrasts": str(wrapper_subject_dir / ESB_CONTRASTS_CSV),
        },
        "wrapper_cohort": {
            "coordinate_contract": COHORT_COORDINATE_CONTRACT,
            "event_metric_dir": str(event_metric_cohort_dir),
            "wrapper_dir": str(wrapper_cohort_dir),
            "event_contrasts": str(wrapper_cohort_dir / EVENT_CONTRASTS_CSV),
            "esb_contrasts": str(wrapper_cohort_dir / ESB_CONTRASTS_CSV),
        },
        "primary_standard_contrasts": str(args.results_dir / PRIMARY_STANDARD_CONTRASTS_CSV),
        "primary_event_contrasts": str(args.results_dir / PRIMARY_EVENT_CONTRASTS_CSV),
        "primary_esb_contrasts": str(args.results_dir / PRIMARY_ESB_CONTRASTS_CSV),
        "summary_path": str(summary_path),
    }
    (args.results_dir / MANIFEST_JSON).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
