from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

from run_wave1_geometry_pilots import (
    COORDS_9D_PATHS,
    JACOBIAN_9D_CENTERS_PATH,
    JACOBIAN_9D_PATH,
    build_h5_lookup,
    ensure_dir,
    path_tail_key,
)


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
COMA_DIR = ARTICLE_DIR.parent / "comatose_ndt"

GOOD_CPC = 1
POOR_CPC = 5
PRIMARY_TIME_BIN = "0_12h"

DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "wave1_9d_export_audit_20260527_local_roots"


@dataclass(frozen=True)
class AuditTarget:
    tag: str
    timeline_dir: Path
    processed_root: Path


@dataclass(frozen=True)
class Config:
    output_dir: Path
    good_cpc: int
    poor_cpc: int
    primary_time_bin: str
    audit_targets: tuple[AuditTarget, ...]


DEFAULT_TARGETS: tuple[AuditTarget, ...] = (
    AuditTarget(
        tag="part1",
        timeline_dir=COMA_DIR / "results" / "timeline_analysis_20260525_part1_primary12h",
        processed_root=REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260523_173059_part1_141sub",
    ),
    AuditTarget(
        tag="part2",
        timeline_dir=COMA_DIR / "results" / "timeline_analysis_20260525_part2_primary12h",
        processed_root=REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260522_095945_part2_140sub",
    ),
)


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Audit whether the local raw I-CARE roots actually expose 9D coordinate and 9D Jacobian exports "
            "needed by the wave1 geometry pilots."
        )
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--good-cpc", type=int, default=GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=POOR_CPC)
    parser.add_argument("--primary-time-bin", type=str, default=PRIMARY_TIME_BIN)
    args = parser.parse_args()
    return Config(
        output_dir=args.output_dir,
        good_cpc=int(args.good_cpc),
        poor_cpc=int(args.poor_cpc),
        primary_time_bin=str(args.primary_time_bin),
        audit_targets=DEFAULT_TARGETS,
    )


def _shape_string(value: Any) -> str:
    if value is None:
        return ""
    arr = tuple(int(dim) for dim in value)
    return "x".join(str(dim) for dim in arr)


def load_timeline_runs(target: AuditTarget, config: Config) -> pd.DataFrame:
    frame = pd.read_csv(target.timeline_dir / "run_timing_metadata.csv", low_memory=False)
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[
        (frame["time_bin"] == config.primary_time_bin)
        & (frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)]))
    ].copy()
    frame["label"] = np.where(frame["cpc_numeric"] == float(config.good_cpc), 1, 0)
    frame["label_name"] = np.where(frame["label"] == 1, f"CPC{config.good_cpc}", f"CPC{config.poor_cpc}")
    frame["audit_tag"] = target.tag

    lookup = build_h5_lookup((target.processed_root,))
    frame["processed_h5_path_original"] = frame["processed_h5_path"].astype(str)
    frame["processed_h5_path_resolved"] = frame["processed_h5_path"].map(
        lambda value: str(lookup.get(path_tail_key(value), Path(str(value))))
    )
    frame["resolved_h5_exists"] = frame["processed_h5_path_resolved"].map(lambda value: Path(str(value)).exists())
    frame["run_key"] = (
        frame["subject"].astype(str)
        + "_run-"
        + frame["run"].astype(str).str.zfill(3)
        + "_acq-"
        + frame["acq"].astype(str)
    )
    return frame.reset_index(drop=True)


def inspect_h5(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "has_coords_9d": False,
        "coords_9d_path": "",
        "coords_9d_shape": "",
        "has_jacobian_9d": False,
        "jacobian_9d_shape": "",
        "has_jacobian_9d_centers": False,
        "jacobian_9d_centers_shape": "",
        "has_coords_3d": False,
        "coords_3d_shape": "",
        "has_jacobian_3d": False,
        "jacobian_3d_shape": "",
        "h5_error": "",
    }
    try:
        with h5py.File(path, "r") as h5:
            coords_9d_path = next((candidate for candidate in COORDS_9D_PATHS if candidate in h5), None)
            if coords_9d_path is not None:
                out["has_coords_9d"] = True
                out["coords_9d_path"] = coords_9d_path
                out["coords_9d_shape"] = _shape_string(h5[coords_9d_path].shape)
            if JACOBIAN_9D_PATH in h5:
                out["has_jacobian_9d"] = True
                out["jacobian_9d_shape"] = _shape_string(h5[JACOBIAN_9D_PATH].shape)
            if JACOBIAN_9D_CENTERS_PATH in h5:
                out["has_jacobian_9d_centers"] = True
                out["jacobian_9d_centers_shape"] = _shape_string(h5[JACOBIAN_9D_CENTERS_PATH].shape)
            if "/coords_3d/values" in h5:
                out["has_coords_3d"] = True
                out["coords_3d_shape"] = _shape_string(h5["/coords_3d/values"].shape)
            if "/jacobian/J_hat" in h5:
                out["has_jacobian_3d"] = True
                out["jacobian_3d_shape"] = _shape_string(h5["/jacobian/J_hat"].shape)
    except OSError as exc:
        out["h5_error"] = str(exc)
    out["has_full_9d_export"] = bool(
        out["has_coords_9d"] and out["has_jacobian_9d"] and out["has_jacobian_9d_centers"]
    )
    out["has_full_3d_export"] = bool(out["has_coords_3d"] and out["has_jacobian_3d"])
    return out


def build_run_audit_frame(target: AuditTarget, config: Config) -> pd.DataFrame:
    frame = load_timeline_runs(target, config)
    cache: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        resolved_path = Path(str(row["processed_h5_path_resolved"]))
        cache_key = str(resolved_path)
        inspection = cache.setdefault(cache_key, inspect_h5(resolved_path) if resolved_path.exists() else inspect_h5(resolved_path))
        rows.append(
            {
                "audit_tag": target.tag,
                "subject": str(row["subject"]),
                "run_key": str(row["run_key"]),
                "label": int(row["label"]),
                "label_name": str(row["label_name"]),
                "cpc": int(row["cpc_numeric"]),
                "hospital": str(row["hospital"]),
                "resolved_h5_exists": bool(row["resolved_h5_exists"]),
                "processed_h5_path_original": str(row["processed_h5_path_original"]),
                "processed_h5_path_resolved": str(resolved_path),
                **inspection,
            }
        )
    return pd.DataFrame(rows)


def build_subject_audit_frame(run_frame: pd.DataFrame) -> pd.DataFrame:
    grouped = run_frame.groupby(["audit_tag", "subject", "label", "label_name", "cpc"], dropna=False)
    subject_frame = grouped.agg(
        n_runs=("run_key", "count"),
        n_runs_existing=("resolved_h5_exists", "sum"),
        n_runs_full_9d=("has_full_9d_export", "sum"),
        n_runs_coords_9d=("has_coords_9d", "sum"),
        n_runs_jacobian_9d=("has_jacobian_9d", "sum"),
        n_runs_full_3d=("has_full_3d_export", "sum"),
    ).reset_index()
    subject_frame["has_any_full_9d"] = subject_frame["n_runs_full_9d"] > 0
    subject_frame["has_complete_full_9d"] = subject_frame["n_runs_full_9d"] == subject_frame["n_runs"]
    return subject_frame


def build_target_summary(subject_frame: pd.DataFrame, run_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for tag, tag_runs in run_frame.groupby("audit_tag", dropna=False):
        tag_subjects = subject_frame[subject_frame["audit_tag"] == tag].copy()
        rows.append(
            {
                "audit_tag": tag,
                "n_subjects": int(tag_subjects["subject"].nunique()),
                "n_subjects_any_full_9d": int(tag_subjects["has_any_full_9d"].sum()),
                "n_subjects_complete_full_9d": int(tag_subjects["has_complete_full_9d"].sum()),
                "n_runs": int(len(tag_runs)),
                "n_runs_existing": int(tag_runs["resolved_h5_exists"].sum()),
                "n_runs_full_9d": int(tag_runs["has_full_9d_export"].sum()),
                "n_runs_coords_9d": int(tag_runs["has_coords_9d"].sum()),
                "n_runs_jacobian_9d": int(tag_runs["has_jacobian_9d"].sum()),
                "n_runs_full_3d": int(tag_runs["has_full_3d_export"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values("audit_tag").reset_index(drop=True)


def build_summary_markdown(summary: pd.DataFrame, run_frame: pd.DataFrame, config: Config) -> str:
    lines = [
        "# Wave1 9D Export Audit",
        "",
        f"- primary time bin: `{config.primary_time_bin}`",
        f"- CPC contrast: `CPC{config.good_cpc}` vs `CPC{config.poor_cpc}`",
        "",
        "## Target Summary",
        "",
        "| Target | Subjects | Any full 9D | Complete full 9D | Runs | Full 9D runs | Full 3D runs |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary.iterrows():
        lines.append(
            "| {tag} | {subjects} | {any9d} | {complete9d} | {runs} | {full9d} | {full3d} |".format(
                tag=row["audit_tag"],
                subjects=int(row["n_subjects"]),
                any9d=int(row["n_subjects_any_full_9d"]),
                complete9d=int(row["n_subjects_complete_full_9d"]),
                runs=int(row["n_runs"]),
                full9d=int(row["n_runs_full_9d"]),
                full3d=int(row["n_runs_full_3d"]),
            )
        )

    lines.extend(["", "## Notes", ""])
    for tag, tag_runs in run_frame.groupby("audit_tag", dropna=False):
        missing_9d = tag_runs.loc[~tag_runs["has_full_9d_export"], "processed_h5_path_resolved"].drop_duplicates().tolist()[:3]
        if missing_9d:
            lines.append(f"- `{tag}` missing full 9D examples:")
            for path in missing_9d:
                lines.append(f"  - `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    config = parse_args()
    ensure_dir(config.output_dir)

    run_frames = [build_run_audit_frame(target, config) for target in config.audit_targets]
    run_frame = pd.concat(run_frames, ignore_index=True)
    subject_frame = build_subject_audit_frame(run_frame)
    summary = build_target_summary(subject_frame, run_frame)

    run_frame.to_csv(config.output_dir / "wave1_9d_export_audit_runs.csv", index=False)
    subject_frame.to_csv(config.output_dir / "wave1_9d_export_audit_subjects.csv", index=False)
    summary.to_csv(config.output_dir / "wave1_9d_export_audit_summary.csv", index=False)
    (config.output_dir / "wave1_9d_export_audit_summary.md").write_text(
        build_summary_markdown(summary, run_frame, config),
        encoding="utf-8",
    )

    manifest = {
        "output_dir": str(config.output_dir),
        "good_cpc": int(config.good_cpc),
        "poor_cpc": int(config.poor_cpc),
        "primary_time_bin": config.primary_time_bin,
        "audit_targets": [asdict(target) | {"timeline_dir": str(target.timeline_dir), "processed_root": str(target.processed_root)} for target in config.audit_targets],
        "n_rows_run_audit": int(len(run_frame)),
        "n_rows_subject_audit": int(len(subject_frame)),
    }
    (config.output_dir / "wave1_9d_export_audit_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote outputs to {config.output_dir}", flush=True)


if __name__ == "__main__":
    main()
