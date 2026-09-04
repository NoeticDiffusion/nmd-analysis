from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np
import pandas as pd

from icare_mnps_summary_analysis import aggregate_patient_bins, build_handoff_manifest, build_metric_long_table
from icare_patient_timeline_analysis import build_patient_bin_summary, build_subject_outcome_index


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_DIR = ARTICLE_DIR / "results"
DEFAULT_DEDUP_POLICY = "prefer_part2"
RUN_KEY_COLUMNS = ("subject", "run", "acq")
MNPS_ROW_KEY_COLUMNS = (
    "analysis_type",
    "subject",
    "run",
    "acq",
    "dataset_id",
    "subject_id",
    "group",
    "condition",
    "task",
    "session",
    "space",
    "source_dataset_path",
    "time_bin",
    "network",
    "block_scope",
    "block_space",
    "source_group",
    "target_group",
)


@dataclass(frozen=True)
class Config:
    part1_timeline_dir: Path
    part1_mnps_dir: Path
    part2_timeline_dir: Path
    part2_mnps_dir: Path
    timeline_output_dir: Path
    mnps_output_dir: Path
    manifest_output_path: Path
    summary_output_path: Path
    dedup_policy: str


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Merge locked part1 and verification part2 coma bundles into a provenance-preserving combined bundle."
    )
    parser.add_argument("--part1-timeline-dir", type=Path, required=True)
    parser.add_argument("--part1-mnps-dir", type=Path, required=True)
    parser.add_argument("--part2-timeline-dir", type=Path, required=True)
    parser.add_argument("--part2-mnps-dir", type=Path, required=True)
    parser.add_argument("--timeline-output-dir", type=Path, required=True)
    parser.add_argument("--mnps-output-dir", type=Path, required=True)
    parser.add_argument("--manifest-output-path", type=Path, required=True)
    parser.add_argument("--summary-output-path", type=Path, required=True)
    parser.add_argument(
        "--dedup-policy",
        type=str,
        choices=["prefer_part2", "prefer_part1", "error_on_overlap"],
        default=DEFAULT_DEDUP_POLICY,
    )
    args = parser.parse_args()
    return Config(
        part1_timeline_dir=args.part1_timeline_dir,
        part1_mnps_dir=args.part1_mnps_dir,
        part2_timeline_dir=args.part2_timeline_dir,
        part2_mnps_dir=args.part2_mnps_dir,
        timeline_output_dir=args.timeline_output_dir,
        mnps_output_dir=args.mnps_output_dir,
        manifest_output_path=args.manifest_output_path,
        summary_output_path=args.summary_output_path,
        dedup_policy=args.dedup_policy,
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _series_to_text(series: pd.Series) -> str:
    values = sorted({str(value) for value in series.dropna() if str(value).strip()})
    return ",".join(values)


def build_run_key(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["subject"].astype(str)
        + "|"
        + pd.to_numeric(frame["run"], errors="coerce").fillna(-1).astype(int).astype(str).str.zfill(3)
        + "|"
        + pd.to_numeric(frame["acq"], errors="coerce").fillna(-1).astype(int).astype(str).str.zfill(3)
    )


def build_mnps_row_key(frame: pd.DataFrame) -> pd.Series:
    parts: List[pd.Series] = []
    for column in MNPS_ROW_KEY_COLUMNS:
        if column in frame.columns:
            parts.append(frame[column].fillna("").astype(str))
        else:
            parts.append(pd.Series([""] * len(frame), index=frame.index, dtype=str))
    out = parts[0]
    for series in parts[1:]:
        out = out + "|" + series
    return out


def with_provenance(frame: pd.DataFrame, *, cohort_tag: str, source_dir: Path) -> pd.DataFrame:
    out = frame.copy()
    out["cohort_tag"] = cohort_tag
    out["bundle_tag"] = source_dir.name
    out["source_dir"] = str(source_dir)
    return out


def deduplicate_by_key(frame: pd.DataFrame, *, key_column: str, dedup_policy: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    working = frame.copy()
    if dedup_policy == "prefer_part2":
        priority_map = {"part2": 0, "part1": 1}
    else:
        priority_map = {"part1": 0, "part2": 1}
    working["__priority__"] = working["cohort_tag"].map(priority_map).fillna(99).astype(int)
    duplicates = working[working.duplicated(key_column, keep=False)].copy()
    if dedup_policy == "error_on_overlap" and not duplicates.empty:
        sample = duplicates[[key_column, "cohort_tag", "bundle_tag"]].head(10).to_dict(orient="records")
        raise ValueError(f"Found overlapping keys under error_on_overlap policy: {sample}")
    deduped = (
        working.sort_values(["__priority__", "bundle_tag", key_column], kind="stable")
        .drop_duplicates(subset=[key_column], keep="first")
        .drop(columns="__priority__")
        .reset_index(drop=True)
    )
    return deduped, duplicates.reset_index(drop=True)


def attach_timeline_group_provenance(patient_rows: pd.DataFrame, run_rows: pd.DataFrame) -> pd.DataFrame:
    if patient_rows.empty or run_rows.empty or "cohort_tag" not in run_rows.columns:
        return patient_rows
    provenance = (
        run_rows.groupby(["subject", "time_bin"], dropna=False, as_index=False)
        .agg(
            cohort_tag=("cohort_tag", _series_to_text),
            bundle_tag=("bundle_tag", _series_to_text),
            source_dir=("source_dir", _series_to_text),
        )
    )
    return patient_rows.merge(provenance, on=["subject", "time_bin"], how="left")


def attach_mnps_group_provenance(patient_rows: pd.DataFrame, run_rows: pd.DataFrame) -> pd.DataFrame:
    if patient_rows.empty or run_rows.empty or "cohort_tag" not in run_rows.columns:
        return patient_rows
    group_columns = [
        column
        for column in ("analysis_type", "subject", "time_bin", "network", "block_scope", "block_space", "source_group", "target_group", "source_dataset_path")
        if column in patient_rows.columns and column in run_rows.columns
    ]
    provenance = (
        run_rows.groupby(group_columns, dropna=False, as_index=False)
        .agg(
            cohort_tag=("cohort_tag", _series_to_text),
            bundle_tag=("bundle_tag", _series_to_text),
            source_dir=("source_dir", _series_to_text),
        )
    )
    return patient_rows.merge(provenance, on=group_columns, how="left")


def build_subject_metadata(run_rows: pd.DataFrame) -> pd.DataFrame:
    if run_rows.empty:
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    for subject, group in run_rows.groupby("subject", dropna=False):
        rows.append(
            {
                "subject": subject,
                "cohort_tag": _series_to_text(group["cohort_tag"]) if "cohort_tag" in group.columns else "",
                "bundle_tag": _series_to_text(group["bundle_tag"]) if "bundle_tag" in group.columns else "",
                "hospital": group["hospital"].dropna().iloc[0] if group["hospital"].notna().any() else None,
                "age": float(pd.to_numeric(group["age"], errors="coerce").median())
                if np.isfinite(pd.to_numeric(group["age"], errors="coerce")).any()
                else np.nan,
                "sex": group["sex"].dropna().iloc[0] if group["sex"].notna().any() else None,
                "rosc_minutes": float(pd.to_numeric(group["rosc_minutes"], errors="coerce").median())
                if np.isfinite(pd.to_numeric(group["rosc_minutes"], errors="coerce")).any()
                else np.nan,
                "ohca": group["ohca"].dropna().iloc[0] if group["ohca"].notna().any() else None,
                "shockable_rhythm": group["shockable_rhythm"].dropna().iloc[0] if group["shockable_rhythm"].notna().any() else None,
                "ttm_celsius": float(pd.to_numeric(group["ttm_celsius"], errors="coerce").median())
                if np.isfinite(pd.to_numeric(group["ttm_celsius"], errors="coerce")).any()
                else np.nan,
                "outcome": group["outcome"].dropna().iloc[0] if group["outcome"].notna().any() else None,
                "cpc": group["cpc"].dropna().iloc[0] if group["cpc"].notna().any() else np.nan,
                "n_runs_total": int(len(group)),
                "time_bins_present": _series_to_text(group["time_bin"]) if "time_bin" in group.columns else "",
                "recording_start_after_anchor_hours": float(pd.to_numeric(group["run_start_from_anchor_hours"], errors="coerce").min()),
                "recording_end_after_anchor_hours": float(pd.to_numeric(group["run_end_from_anchor_hours"], errors="coerce").max()),
            }
        )
    return pd.DataFrame(rows).sort_values("subject").reset_index(drop=True)


def summarize_subject_metadata(frame: pd.DataFrame, cohort_label: str) -> Dict[str, Any]:
    if frame.empty:
        return {"cohort": cohort_label, "n_subjects": 0}
    cpc_counts = pd.to_numeric(frame["cpc"], errors="coerce").value_counts(dropna=False).sort_index().to_dict()
    hospital_counts = frame["hospital"].fillna("missing").value_counts(dropna=False).to_dict()
    sex_counts = frame["sex"].fillna("missing").value_counts(dropna=False).to_dict()
    return {
        "cohort": cohort_label,
        "n_subjects": int(frame["subject"].nunique()),
        "cpc_counts": {str(key): int(value) for key, value in cpc_counts.items()},
        "hospital_counts": {str(key): int(value) for key, value in hospital_counts.items()},
        "sex_counts": {str(key): int(value) for key, value in sex_counts.items()},
        "age_median": float(pd.to_numeric(frame["age"], errors="coerce").median()),
        "rosc_median_minutes": float(pd.to_numeric(frame["rosc_minutes"], errors="coerce").median()),
    }


def write_subject_metadata_variants(manifest_output_path: Path, variants: Dict[str, pd.DataFrame]) -> Dict[str, str]:
    written: Dict[str, str] = {}
    base_dir = manifest_output_path.parent
    stem = manifest_output_path.stem
    for label, frame in variants.items():
        path = base_dir / f"{stem}_{label}_subject_metadata.csv"
        frame.to_csv(path, index=False)
        written[label] = str(path)
    return written


def build_summary_markdown(manifest: Dict[str, Any]) -> str:
    lines = [
        "# Combined coma cohort summary",
        "",
        f"- dedup policy: `{manifest['dedup_policy']}`",
        f"- subject overlap count: `{manifest['subject_overlap_count']}`",
        f"- run overlap count: `{manifest['timeline_overlap']['run_key_overlap_count']}`",
        "",
        "## Cohorts",
        "",
    ]
    for summary in manifest["cohort_metadata_summary"]:
        lines.append(
            f"- `{summary['cohort']}`: n_subjects={summary['n_subjects']}, "
            f"cpc_counts={summary.get('cpc_counts', {})}, hospital_counts={summary.get('hospital_counts', {})}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    ensure_dir(config.timeline_output_dir)
    ensure_dir(config.mnps_output_dir)
    ensure_dir(config.manifest_output_path.parent)

    part1_timeline = with_provenance(pd.read_csv(config.part1_timeline_dir / "run_timing_metadata.csv"), cohort_tag="part1", source_dir=config.part1_timeline_dir)
    part2_timeline = with_provenance(pd.read_csv(config.part2_timeline_dir / "run_timing_metadata.csv"), cohort_tag="part2", source_dir=config.part2_timeline_dir)
    part1_timeline["run_key"] = build_run_key(part1_timeline)
    part2_timeline["run_key"] = build_run_key(part2_timeline)
    timeline_union = pd.concat([part1_timeline, part2_timeline], ignore_index=True)
    combined_timeline, timeline_duplicates = deduplicate_by_key(
        timeline_union,
        key_column="run_key",
        dedup_policy=config.dedup_policy,
    )

    combined_subject_index = build_subject_outcome_index(combined_timeline)
    combined_subject_metadata = build_subject_metadata(combined_timeline)
    combined_patient_bins = attach_timeline_group_provenance(build_patient_bin_summary(combined_timeline), combined_timeline)

    combined_timeline.to_csv(config.timeline_output_dir / "run_timing_metadata.csv", index=False)
    combined_subject_index.to_csv(config.timeline_output_dir / "subject_outcome_index.csv", index=False)
    combined_patient_bins.to_csv(config.timeline_output_dir / "patient_timebin_summaries.csv", index=False)

    part1_mnps = with_provenance(
        pd.read_csv(config.part1_mnps_dir / "run_level_adapter_summaries.csv"),
        cohort_tag="part1",
        source_dir=config.part1_mnps_dir,
    )
    part2_mnps = with_provenance(
        pd.read_csv(config.part2_mnps_dir / "run_level_adapter_summaries.csv"),
        cohort_tag="part2",
        source_dir=config.part2_mnps_dir,
    )
    part1_mnps["row_key"] = build_mnps_row_key(part1_mnps)
    part2_mnps["row_key"] = build_mnps_row_key(part2_mnps)
    mnps_union = pd.concat([part1_mnps, part2_mnps], ignore_index=True)
    combined_mnps_runs, mnps_duplicates = deduplicate_by_key(
        mnps_union,
        key_column="row_key",
        dedup_policy=config.dedup_policy,
    )

    combined_mnps_patient = attach_mnps_group_provenance(aggregate_patient_bins(combined_mnps_runs), combined_mnps_runs)
    combined_run_metrics = build_metric_long_table(combined_mnps_runs, level="run")
    combined_patient_metrics = build_metric_long_table(combined_mnps_patient, level="patient_timebin")
    combined_handoff_manifest = build_handoff_manifest(combined_run_metrics, combined_patient_metrics)
    combined_handoff_manifest.update(
        {
            "source_mnps_dirs": [str(config.part1_mnps_dir), str(config.part2_mnps_dir)],
            "source_timeline_dirs": [str(config.part1_timeline_dir), str(config.part2_timeline_dir)],
            "dedup_policy": config.dedup_policy,
            "mnps_row_overlap_count": int(mnps_duplicates["row_key"].nunique()) if not mnps_duplicates.empty else 0,
        }
    )

    mnps_qc_rows = pd.concat(
        [
            with_provenance(pd.read_csv(config.part1_mnps_dir / "adapter_qc.csv"), cohort_tag="part1", source_dir=config.part1_mnps_dir),
            with_provenance(pd.read_csv(config.part2_mnps_dir / "adapter_qc.csv"), cohort_tag="part2", source_dir=config.part2_mnps_dir),
        ],
        ignore_index=True,
    )
    mnps_qc_summary = {
        "source_mnps_dirs": [str(config.part1_mnps_dir), str(config.part2_mnps_dir)],
        "dedup_policy": config.dedup_policy,
        "n_run_rows": int(len(combined_mnps_runs)),
        "n_patient_rows": int(len(combined_mnps_patient)),
        "mnps_row_overlap_count": int(mnps_duplicates["row_key"].nunique()) if not mnps_duplicates.empty else 0,
        "cohort_run_counts": combined_mnps_runs["cohort_tag"].value_counts(dropna=False).to_dict(),
    }

    combined_mnps_runs.to_csv(config.mnps_output_dir / "run_level_adapter_summaries.csv", index=False)
    combined_mnps_patient.to_csv(config.mnps_output_dir / "patient_timebin_adapter_summaries.csv", index=False)
    combined_run_metrics.to_csv(config.mnps_output_dir / "run_level_signal_metrics.csv", index=False)
    combined_patient_metrics.to_csv(config.mnps_output_dir / "patient_timebin_signal_metrics.csv", index=False)
    mnps_qc_rows.to_csv(config.mnps_output_dir / "adapter_qc.csv", index=False)
    combined_subject_index.to_csv(config.mnps_output_dir / "subject_outcome_index.csv", index=False)
    (config.mnps_output_dir / "metric_handoff_manifest.json").write_text(
        json.dumps(combined_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    (config.mnps_output_dir / "qc_summary.json").write_text(
        json.dumps(mnps_qc_summary, indent=2),
        encoding="utf-8",
    )

    timeline_summary = {
        "source_timeline_dirs": [str(config.part1_timeline_dir), str(config.part2_timeline_dir)],
        "dedup_policy": config.dedup_policy,
        "n_h5_runs": int(len(combined_timeline)),
        "n_subjects": int(combined_timeline["subject"].nunique()),
        "time_bin_scheme": load_json(config.part1_timeline_dir / "timeline_summary.json").get("time_bin_scheme"),
        "time_status_counts": combined_timeline["time_reference_status"].fillna("missing").value_counts(dropna=False).to_dict(),
        "time_anchor_sources": combined_timeline["run_anchor_source"].fillna("missing").value_counts(dropna=False).to_dict(),
        "subjects": combined_subject_index.to_dict(orient="records"),
        "subject_overlap_count": int(
            len(set(part1_timeline["subject"].astype(str)).intersection(set(part2_timeline["subject"].astype(str))))
        ),
        "run_overlap_count": int(timeline_duplicates["run_key"].nunique()) if not timeline_duplicates.empty else 0,
    }
    (config.timeline_output_dir / "timeline_summary.json").write_text(
        json.dumps(timeline_summary, indent=2),
        encoding="utf-8",
    )

    part1_subject_metadata = build_subject_metadata(part1_timeline)
    part2_subject_metadata = build_subject_metadata(part2_timeline)
    written_metadata = write_subject_metadata_variants(
        config.manifest_output_path,
        {
            "part1": part1_subject_metadata,
            "part2": part2_subject_metadata,
            "combined": combined_subject_metadata,
        },
    )

    manifest = {
        "dedup_policy": config.dedup_policy,
        "part1_timeline_dir": str(config.part1_timeline_dir),
        "part1_mnps_dir": str(config.part1_mnps_dir),
        "part2_timeline_dir": str(config.part2_timeline_dir),
        "part2_mnps_dir": str(config.part2_mnps_dir),
        "timeline_output_dir": str(config.timeline_output_dir),
        "mnps_output_dir": str(config.mnps_output_dir),
        "subject_overlap_count": int(
            len(set(part1_timeline["subject"].astype(str)).intersection(set(part2_timeline["subject"].astype(str))))
        ),
        "timeline_overlap": {
            "run_key_overlap_count": int(timeline_duplicates["run_key"].nunique()) if not timeline_duplicates.empty else 0,
            "run_key_overlap_examples": sorted(timeline_duplicates["run_key"].astype(str).unique().tolist())[:20]
            if not timeline_duplicates.empty
            else [],
        },
        "mnps_overlap": {
            "row_key_overlap_count": int(mnps_duplicates["row_key"].nunique()) if not mnps_duplicates.empty else 0,
        },
        "cohort_metadata_summary": [
            summarize_subject_metadata(part1_subject_metadata, "part1"),
            summarize_subject_metadata(part2_subject_metadata, "part2"),
            summarize_subject_metadata(combined_subject_metadata, "combined"),
        ],
        "metadata_exports": written_metadata,
    }
    config.manifest_output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    config.summary_output_path.write_text(build_summary_markdown(manifest), encoding="utf-8")

    print(f"Wrote combined timeline bundle to {config.timeline_output_dir}")
    print(f"Wrote combined mnps bundle to {config.mnps_output_dir}")
    print(f"Wrote cohort manifest to {config.manifest_output_path}")


if __name__ == "__main__":
    main()
