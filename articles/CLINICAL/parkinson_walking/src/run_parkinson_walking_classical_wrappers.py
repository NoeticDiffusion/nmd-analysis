from __future__ import annotations

import argparse
from pathlib import Path
import sys

import h5py
import numpy as np
import pandas as pd
from scipy import stats

from parkinson_walking_support import (
    DATASET_ROOT,
    GROUP_ORDER,
    NDT_ANALYSIS_ROOT,
    PARTICIPANTS_PATH,
    PD_CLINICAL_COLUMNS,
    RESULTS_DIR,
    TASK_ORDER,
    base_h5_metadata_from_handle,
    bh_fdr,
    cohens_d,
    ensure_dir,
    fmt,
    list_h5_paths,
    load_participants,
    parse_run_slug,
    write_json,
)

if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.eeg_classical_comparators import build_eeg_classical_comparators_frame  # noqa: E402


CLASSICAL_DIR = RESULTS_DIR / "classical_wrappers"
CLASSICAL_RUN_CSV = "classical_run_metrics.csv"
CLASSICAL_EXTENSION_PATH = "extensions/conventional_eeg/families"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run article-local classical EEG comparator wrappers for the Parkinson walking dataset."
    )
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--participants-tsv", type=Path, default=PARTICIPANTS_PATH)
    parser.add_argument("--output-dir", type=Path, default=CLASSICAL_DIR)
    parser.add_argument("--anchor", choices=("auto", "cohort", "subject"), default="cohort")
    return parser.parse_args()


def anchor_to_contract(anchor: str) -> str:
    if anchor == "subject":
        return "subject_anchored"
    return "cohort_anchored"


def detect_extension_counts(h5_paths: list[Path]) -> dict[str, int]:
    present = 0
    for h5_path in h5_paths:
        with h5py.File(h5_path, "r") as handle:
            if CLASSICAL_EXTENSION_PATH in handle:
                present += 1
    return {"n_h5_total": len(h5_paths), "n_h5_with_classical_extension": present}


def attach_participant_metadata(frame: pd.DataFrame, participants_tsv: Path) -> pd.DataFrame:
    if frame.empty:
        return frame
    participants = load_participants(participants_tsv)
    keep = ["participant_id", "group", "sex", *PD_CLINICAL_COLUMNS]
    meta = participants[keep].copy()
    out = frame.copy()
    out = out.merge(meta, on="participant_id", how="left", suffixes=("", "_participants"))
    if "group_participants" in out.columns:
        out["group"] = out["group"].fillna(out["group_participants"])
        out = out.drop(columns=["group_participants"])
    if "sex_participants" in out.columns:
        out["sex"] = out["sex"].fillna(out["sex_participants"])
        out = out.drop(columns=["sex_participants"])
    return out


def classical_metric_columns(frame: pd.DataFrame) -> list[str]:
    return sorted([column for column in frame.columns if column.startswith("eeg_classical_")])


def build_classical_frame(dataset_root: Path, participants_tsv: Path, *, anchor: str) -> tuple[pd.DataFrame, dict[str, int]]:
    h5_paths = list_h5_paths(dataset_root)
    counts = detect_extension_counts(h5_paths)
    frame = build_eeg_classical_comparators_frame(
        h5_paths,
        coordinate_contract=anchor_to_contract(anchor),
        base_metadata_builder=base_h5_metadata_from_handle,
    )
    if frame.empty:
        return frame, counts
    frame = frame.copy()
    frame["participant_id"] = [
        str(subject_id) if pd.notna(subject_id) and str(subject_id).strip() else parse_run_slug(Path(path)).get("participant_id")
        for subject_id, path in zip(frame.get("subject_id", pd.Series(dtype=object)), frame["source_h5_path"], strict=False)
    ]
    frame["task"] = frame["task"].fillna(
        [parse_run_slug(Path(path)).get("task") for path in frame["source_h5_path"]]
    )
    frame["anchor_mode_requested"] = anchor
    frame = attach_participant_metadata(frame, participants_tsv)
    for column in classical_metric_columns(frame) + list(PD_CLINICAL_COLUMNS):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["group"] = pd.Categorical(frame["group"], categories=GROUP_ORDER, ordered=True)
    frame["task"] = pd.Categorical(frame["task"], categories=TASK_ORDER, ordered=True)
    return frame.sort_values(["group", "participant_id", "task"], na_position="last").reset_index(drop=True), counts


def group_contrast_rows(frame: pd.DataFrame) -> pd.DataFrame:
    metric_columns = classical_metric_columns(frame)
    rows: list[dict[str, object]] = []
    for task in TASK_ORDER:
        task_frame = frame[frame["task"] == task].copy()
        left_frame = task_frame[task_frame["group"] == "HC"].copy()
        right_frame = task_frame[task_frame["group"] == "PD"].copy()
        for metric in metric_columns:
            left = pd.to_numeric(left_frame[metric], errors="coerce").dropna().to_numpy(dtype=float)
            right = pd.to_numeric(right_frame[metric], errors="coerce").dropna().to_numpy(dtype=float)
            if left.size < 3 or right.size < 3:
                continue
            stat, p_value = stats.mannwhitneyu(left, right, alternative="two-sided")
            rows.append(
                {
                    "contrast_name": f"HC_vs_PD_{task}_classical",
                    "task": task,
                    "metric": metric,
                    "left_label": "HC",
                    "right_label": "PD",
                    "left_n": int(left.size),
                    "right_n": int(right.size),
                    "left_median": float(np.median(left)),
                    "right_median": float(np.median(right)),
                    "effect_estimate": float(np.median(right) - np.median(left)),
                    "effect_size": float(cohens_d(left, right)),
                    "test_stat": float(stat),
                    "p_value": float(p_value),
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["q_value"] = out.groupby("contrast_name", dropna=False)["p_value"].transform(bh_fdr)
    out["abs_effect_size"] = pd.to_numeric(out["effect_size"], errors="coerce").abs()
    return out.sort_values(["contrast_name", "q_value", "p_value", "abs_effect_size"], ascending=[True, True, True, False]).reset_index(drop=True)


def clinical_rho_rows(frame: pd.DataFrame) -> pd.DataFrame:
    metric_columns = classical_metric_columns(frame)
    rows: list[dict[str, object]] = []
    pd_runs = frame[frame["group"] == "PD"].copy()
    for task in TASK_ORDER:
        task_frame = pd_runs[pd_runs["task"] == task].copy()
        for variable in PD_CLINICAL_COLUMNS:
            x = pd.to_numeric(task_frame[variable], errors="coerce")
            if x.notna().sum() < 8 or x.nunique(dropna=True) < 3:
                continue
            for metric in metric_columns:
                y = pd.to_numeric(task_frame[metric], errors="coerce")
                valid = x.notna() & y.notna()
                if valid.sum() < 8:
                    continue
                if x[valid].nunique(dropna=True) < 3 or y[valid].nunique(dropna=True) < 3:
                    continue
                rho, p_value = stats.spearmanr(x[valid], y[valid])
                rows.append(
                    {
                        "task": task,
                        "clinical_variable": variable,
                        "metric": metric,
                        "n_subjects": int(valid.sum()),
                        "rho": float(rho) if np.isfinite(rho) else np.nan,
                        "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
                    }
                )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["q_value"] = out.groupby(["task", "clinical_variable"], dropna=False)["p_value"].transform(bh_fdr)
    out["abs_rho"] = pd.to_numeric(out["rho"], errors="coerce").abs()
    return out.sort_values(["task", "clinical_variable", "q_value", "p_value", "abs_rho"], ascending=[True, True, True, True, False]).reset_index(drop=True)


def build_markdown(frame: pd.DataFrame, group_rows: pd.DataFrame, rho_rows: pd.DataFrame, *, anchor: str, counts: dict[str, int]) -> str:
    lines = [
        "# Parkinson walking classical EEG wrappers",
        "",
        "This article-local wrapper calls `ndt_analysis.eeg_classical_comparators.build_eeg_classical_comparators_frame(...)` directly.",
        "",
        f"- Anchor mode: `{anchor}`",
        f"- Coordinate contract passed to wrapper: `{anchor_to_contract(anchor)}`",
        f"- H5 files scanned: `{counts['n_h5_total']}`",
        f"- H5 files with `conventional_eeg` extension: `{counts['n_h5_with_classical_extension']}`",
        "",
    ]
    if frame.empty:
        lines.extend(
            [
                "## Availability",
                "",
                "No classical comparator rows were produced. For this bundle the `extensions/conventional_eeg/families` H5 extension is absent, so there is currently no article-local classical EEG comparator surface to compare against.",
                "",
            ]
        )
        return "\n".join(lines) + "\n"
    lines.extend(["## Top HC vs PD classical rows", ""])
    if group_rows.empty:
        lines.extend(["No classical group contrasts were estimable.", ""])
    else:
        for _, row in group_rows.head(12).iterrows():
            lines.append(
                f"- `{row['task']}` / `{row['metric']}`: HC median={fmt(row['left_median'])}, "
                f"PD median={fmt(row['right_median'])}, d={fmt(row['effect_size'])}, p={fmt(row['p_value'])}, q={fmt(row['q_value'])}"
            )
        lines.append("")
    lines.extend(["## Top PD rho rows", ""])
    if rho_rows.empty:
        lines.extend(["No classical clinical rho rows were estimable.", ""])
    else:
        hits = rho_rows[rho_rows["q_value"] < 0.1].copy()
        source = hits if not hits.empty else rho_rows.head(12)
        for _, row in source.head(12).iterrows():
            lines.append(
                f"- `{row['task']}` / `{row['clinical_variable']}` / `{row['metric']}`: "
                f"rho={fmt(row['rho'])}, p={fmt(row['p_value'])}, q={fmt(row['q_value'])}, n={int(row['n_subjects'])}"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    frame, counts = build_classical_frame(args.dataset_root, args.participants_tsv, anchor=args.anchor)
    group_rows = group_contrast_rows(frame) if not frame.empty else pd.DataFrame()
    rho_rows = clinical_rho_rows(frame) if not frame.empty else pd.DataFrame()
    if not frame.empty:
        frame.to_csv(args.output_dir / CLASSICAL_RUN_CSV, index=False)
    if not group_rows.empty:
        group_rows.to_csv(args.output_dir / "classical_group_contrasts.csv", index=False)
    if not rho_rows.empty:
        rho_rows.to_csv(args.output_dir / "classical_pd_clinical_associations.csv", index=False)
    (args.output_dir / "classical_summary.md").write_text(
        build_markdown(frame, group_rows, rho_rows, anchor=args.anchor, counts=counts),
        encoding="utf-8",
    )
    manifest = {
        "dataset_root": str(args.dataset_root),
        "participants_tsv": str(args.participants_tsv),
        "output_dir": str(args.output_dir),
        "anchor": args.anchor,
        "coordinate_contract": anchor_to_contract(args.anchor),
        **counts,
        "classical_extension_path": CLASSICAL_EXTENSION_PATH,
        "n_run_rows": int(len(frame)),
        "n_group_rows": int(len(group_rows)),
        "n_rho_rows": int(len(rho_rows)),
    }
    write_json(args.output_dir / "classical_manifest.json", manifest)
    print(f"Wrote classical wrapper outputs to {args.output_dir}")
    print(
        f"H5 with extension: {counts['n_h5_with_classical_extension']}/{counts['n_h5_total']} | "
        f"run rows: {len(frame)} | group rows: {len(group_rows)} | rho rows: {len(rho_rows)}"
    )


if __name__ == "__main__":
    main()
