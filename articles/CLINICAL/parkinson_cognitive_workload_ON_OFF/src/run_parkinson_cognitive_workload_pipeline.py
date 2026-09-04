from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from parkinson_cognitive_workload_support import (
    COHORT_COORDINATE_CONTRACT,
    EVENT_CONTRASTS_CSV,
    MANIFEST_JSON,
    NDT_ANALYSIS_ROOT,
    PRIMARY_EVENT_CONTRASTS_CSV,
    PRIMARY_STANDARD_CONTRASTS_CSV,
    SUBJECT_COORDINATE_CONTRACT,
    SUMMARY_FILENAME,
    DatasetSpec,
    ensure_dir,
    infer_dataset_spec,
    results_dir_for_spec,
)

if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.analysis_pipeline import run_cleaned_analysis_pipeline  # noqa: E402
from ndt_analysis.pipeline import run_dataset_pipeline  # noqa: E402


SRC_DIR = Path(__file__).resolve().parent
CONTRAST_PRIORITY = {
    "Parkinson_OFF_vs_ON": SUBJECT_COORDINATE_CONTRACT,
    "Control_vs_Parkinson_OFF": COHORT_COORDINATE_CONTRACT,
    "Control_vs_Parkinson_ON": COHORT_COORDINATE_CONTRACT,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a dual-contract Parkinson cognitive workload pipeline.")
    parser.add_argument("--dataset-id", type=str, default=None)
    parser.add_argument("--dataset-root", type=Path, default=None)
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--limit-h5", type=int, default=None)
    return parser.parse_args()


def latest_parquet(root: Path, dataset_id: str, analysis_type: str) -> Path | None:
    matches = sorted(root.glob(f"{dataset_id}_{analysis_type}_*.parquet"), key=lambda path: path.stat().st_mtime_ns)
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
    block["abs_effect_proxy"] = pd.to_numeric(block["effect_size"], errors="coerce").abs()
    return block.sort_values(["q_value", "p_value", "abs_effect_proxy"], ascending=[True, True, False], na_position="last").head(limit)


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
    sort_cols = [column for column in ["contrast_name", "q_value", "p_value", "analysis_type", "segment_family", "segment_label", "network", "metric"] if column in out.columns]
    return out.sort_values(sort_cols, na_position="last").reset_index(drop=True)


def run_wrapper_pass(spec: DatasetSpec, dataset_root: Path, event_metric_dir: Path, wrapper_dir: Path, contract: str, limit_h5: int | None) -> None:
    ensure_dir(event_metric_dir)
    ensure_dir(wrapper_dir)
    compute_cmd = [
        sys.executable,
        str(SRC_DIR / "compute_parkinson_cognitive_workload_metrics.py"),
        "--dataset-id",
        spec.dataset_id,
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
            str(SRC_DIR / "export_parkinson_cognitive_workload_contrasts.py"),
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
    dataset_id: str,
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
    contrast_path = latest_parquet(analysis_dir, dataset_id, "contrast_results")
    return run_result, analyze_result, contrast_path


def load_csv_if_exists(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False) if path.exists() else pd.DataFrame()


def build_summary(spec: DatasetSpec, standard_results: pd.DataFrame, wrapper_contrasts: pd.DataFrame) -> str:
    lines = [
        f"# {spec.task_label} Parkinson cognitive workload summary",
        "",
        f"This run analyzes `{spec.dataset_id}` with a mixed-contract policy: `{COHORT_COORDINATE_CONTRACT}` is primary for disease-state contrasts against controls, while `{SUBJECT_COORDINATE_CONTRACT}` remains primary for the paired medication contrast.",
        "",
        "## Standard ndt-analysis layer",
        "",
    ]
    if standard_results.empty:
        lines.extend(["No merged standard contrast rows were produced.", ""])
    else:
        for contrast_name, contract in CONTRAST_PRIORITY.items():
            rows = top_rows(standard_results, contrast_name)
            if rows.empty:
                continue
            lines.append(f"### {contrast_name} ({contract})")
            lines.append("")
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

    lines.extend(
        [
            "## Caveats",
            "",
            "- Wrapper metrics use task-specific `event_windows/*` segmentation and remain article-local summaries on top of the repository standard exports.",
            "- Control subjects do not have medication pairing, so disease-state and pharmacology questions are answered with different optimal coordinate contracts.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    spec = infer_dataset_spec(dataset_root=args.dataset_root, dataset_id=args.dataset_id)
    dataset_root = args.dataset_root or spec.dataset_root
    results_dir = args.results_dir or results_dir_for_spec(spec)
    ensure_dir(results_dir)

    standard_subject_cleaned_dir = results_dir / "standard_cleaned_subject"
    standard_subject_analysis_dir = results_dir / "standard_analysis_subject"
    standard_cohort_cleaned_dir = results_dir / "standard_cleaned_cohort"
    standard_cohort_analysis_dir = results_dir / "standard_analysis_cohort"
    event_metric_subject_dir = results_dir / "event_metrics_subject"
    event_metric_cohort_dir = results_dir / "event_metrics_cohort"
    wrapper_subject_dir = results_dir / "wrapper_subject"
    wrapper_cohort_dir = results_dir / "wrapper_cohort"

    subject_run_result, subject_analyze_result, subject_standard_contrast_path = run_standard_pass(
        dataset_root,
        standard_subject_cleaned_dir,
        standard_subject_analysis_dir,
        run_config_path=spec.run_config_path,
        analyze_config_path=spec.analyze_config_path,
        dataset_id=spec.dataset_id,
    )
    cohort_run_result, cohort_analyze_result, cohort_standard_contrast_path = run_standard_pass(
        dataset_root,
        standard_cohort_cleaned_dir,
        standard_cohort_analysis_dir,
        run_config_path=spec.cohort_run_config_path,
        analyze_config_path=spec.cohort_analyze_config_path,
        dataset_id=spec.dataset_id,
    )

    run_wrapper_pass(
        spec,
        dataset_root,
        event_metric_subject_dir,
        wrapper_subject_dir,
        SUBJECT_COORDINATE_CONTRACT,
        args.limit_h5,
    )
    run_wrapper_pass(
        spec,
        dataset_root,
        event_metric_cohort_dir,
        wrapper_cohort_dir,
        COHORT_COORDINATE_CONTRACT,
        args.limit_h5,
    )

    standard_by_contract = {
        SUBJECT_COORDINATE_CONTRACT: pd.read_parquet(subject_standard_contrast_path) if subject_standard_contrast_path is not None else pd.DataFrame(),
        COHORT_COORDINATE_CONTRACT: pd.read_parquet(cohort_standard_contrast_path) if cohort_standard_contrast_path is not None else pd.DataFrame(),
    }
    wrapper_by_contract = {
        SUBJECT_COORDINATE_CONTRACT: load_csv_if_exists(wrapper_subject_dir / EVENT_CONTRASTS_CSV),
        COHORT_COORDINATE_CONTRACT: load_csv_if_exists(wrapper_cohort_dir / EVENT_CONTRASTS_CSV),
    }

    primary_standard = select_primary_rows(standard_by_contract)
    primary_wrapper = select_primary_rows(wrapper_by_contract)
    primary_standard.to_csv(results_dir / PRIMARY_STANDARD_CONTRASTS_CSV, index=False)
    primary_wrapper.to_csv(results_dir / PRIMARY_EVENT_CONTRASTS_CSV, index=False)
    (results_dir / SUMMARY_FILENAME).write_text(build_summary(spec, primary_standard, primary_wrapper), encoding="utf-8")

    manifest = {
        "dataset_id": spec.dataset_id,
        "task": spec.task,
        "dataset_root": str(dataset_root),
        "results_dir": str(results_dir),
        "contrast_priority": CONTRAST_PRIORITY,
        "standard_subject": {
            "coordinate_contract": SUBJECT_COORDINATE_CONTRACT,
            "config_path": str(spec.run_config_path),
            "analysis_config_path": str(spec.analyze_config_path),
            "cleaned_dir": str(standard_subject_cleaned_dir),
            "analysis_dir": str(standard_subject_analysis_dir),
            "contrast_path": str(subject_standard_contrast_path) if subject_standard_contrast_path is not None else None,
            "run_result": subject_run_result,
            "analyze_result": subject_analyze_result,
        },
        "standard_cohort": {
            "coordinate_contract": COHORT_COORDINATE_CONTRACT,
            "config_path": str(spec.cohort_run_config_path),
            "analysis_config_path": str(spec.cohort_analyze_config_path),
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
        },
        "wrapper_cohort": {
            "coordinate_contract": COHORT_COORDINATE_CONTRACT,
            "event_metric_dir": str(event_metric_cohort_dir),
            "wrapper_dir": str(wrapper_cohort_dir),
            "event_contrasts": str(wrapper_cohort_dir / EVENT_CONTRASTS_CSV),
        },
        "primary_standard_contrasts": str(results_dir / PRIMARY_STANDARD_CONTRASTS_CSV),
        "primary_event_contrasts": str(results_dir / PRIMARY_EVENT_CONTRASTS_CSV),
        "summary_path": str(results_dir / SUMMARY_FILENAME),
    }
    (results_dir / MANIFEST_JSON).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
