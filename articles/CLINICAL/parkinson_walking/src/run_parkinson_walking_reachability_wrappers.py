from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
import sys

import h5py
import numpy as np
import pandas as pd
from scipy import stats

from parkinson_walking_support import (
    DATASET_ROOT,
    GROUP_ORDER,
    NETWORK_ORDER,
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

from ndt_analysis.reachability_cones import ReachabilityConfig, summarize_reachability_h5  # noqa: E402


REACHABILITY_DIR = RESULTS_DIR / "reachability_wrappers"
REACHABILITY_RUN_CSV = "reachability_run_metrics.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run article-local reachability wrappers for the Parkinson walking dataset."
    )
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--participants-tsv", type=Path, default=PARTICIPANTS_PATH)
    parser.add_argument("--output-dir", type=Path, default=REACHABILITY_DIR)
    parser.add_argument("--anchor", choices=("auto", "cohort", "subject"), default="cohort")
    parser.add_argument("--rebuild-run-metrics", action="store_true")
    return parser.parse_args()


def anchor_to_contract(anchor: str) -> str:
    if anchor == "subject":
        return "subject_anchored"
    return "cohort_anchored"


def resolve_regional_dataset_path(handle: h5py.File, network: str, anchor: str) -> str | None:
    candidates: list[str]
    if anchor == "subject":
        candidates = [
            f"/regional_mnps/{network}/subject_anchored/mnps",
            f"/regional_mnps/{network}/mnps",
        ]
    elif anchor == "cohort":
        candidates = [
            f"/regional_mnps/{network}/cohort_anchored/mnps",
            f"/regional_mnps/{network}/mnps",
        ]
    else:
        candidates = [
            f"/regional_mnps/{network}/cohort_anchored/mnps",
            f"/regional_mnps/{network}/subject_anchored/mnps",
            f"/regional_mnps/{network}/mnps",
        ]
    for candidate in candidates:
        if candidate in handle:
            return candidate
    return None


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


def reachability_metric_columns(frame: pd.DataFrame) -> list[str]:
    prefixes = ("tube_", "cone_", "q_ratio_", "persistence_", "pred_err_")
    extras = {"near_singular_rate", "median_cond", "median_min_eig_over_median_eig"}
    cols = [column for column in frame.columns if column.startswith(prefixes) or column in extras]
    return sorted(cols)


def build_reachability_frame(dataset_root: Path, participants_tsv: Path, *, anchor: str) -> pd.DataFrame:
    contract = anchor_to_contract(anchor)
    cfg = ReachabilityConfig()
    rows: list[dict[str, object]] = []
    for h5_path in list_h5_paths(dataset_root):
        parsed = parse_run_slug(h5_path)
        global_summary = summarize_reachability_h5(
            h5_path,
            config=cfg,
            coordinate_contract=contract,
        )
        global_row = dict(global_summary["flat"])
        global_row["participant_id"] = parsed["participant_id"]
        global_row["task"] = global_row.get("task") or parsed["task"]
        global_row["network"] = "global"
        global_row["block_scope"] = "global"
        global_row["analysis_type"] = "reachability_global_3d"
        global_row["anchor_mode_requested"] = anchor
        rows.append(global_row)

        with h5py.File(h5_path, "r") as handle:
            _ = base_h5_metadata_from_handle(handle, h5_path)
            for network in NETWORK_ORDER:
                dataset_path = resolve_regional_dataset_path(handle, network, anchor)
                if dataset_path is None:
                    continue
                regional_summary = summarize_reachability_h5(
                    h5_path,
                    config=cfg,
                    coordinate_contract=contract,
                    dataset_path=dataset_path,
                    used_space_override="regional_mnps_3d",
                    flat_overrides={
                        "network": network,
                        "source_dataset_path": dataset_path,
                    },
                )
                regional_row = dict(regional_summary["flat"])
                regional_row["participant_id"] = parsed["participant_id"]
                regional_row["task"] = regional_row.get("task") or parsed["task"]
                regional_row["network"] = network
                regional_row["block_scope"] = "regional"
                regional_row["analysis_type"] = "reachability_regional_3d"
                regional_row["anchor_mode_requested"] = anchor
                rows.append(regional_row)
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame = attach_participant_metadata(frame, participants_tsv)
    for column in reachability_metric_columns(frame) + list(PD_CLINICAL_COLUMNS):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["group"] = pd.Categorical(frame["group"], categories=GROUP_ORDER, ordered=True)
    frame["task"] = pd.Categorical(frame["task"], categories=TASK_ORDER, ordered=True)
    return frame.sort_values(["block_scope", "network", "group", "participant_id", "task"], na_position="last").reset_index(drop=True)


def load_or_build_reachability_frame(
    csv_path: Path,
    *,
    dataset_root: Path,
    participants_tsv: Path,
    anchor: str,
    rebuild: bool,
) -> pd.DataFrame:
    if csv_path.exists() and not rebuild:
        frame = pd.read_csv(csv_path, low_memory=False)
        frame = attach_participant_metadata(frame, participants_tsv)
        for column in reachability_metric_columns(frame) + list(PD_CLINICAL_COLUMNS):
            if column in frame.columns:
                frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if "group" in frame.columns:
            frame["group"] = pd.Categorical(frame["group"], categories=GROUP_ORDER, ordered=True)
        if "task" in frame.columns:
            frame["task"] = pd.Categorical(frame["task"], categories=TASK_ORDER, ordered=True)
        return frame
    frame = build_reachability_frame(dataset_root, participants_tsv, anchor=anchor)
    ensure_dir(csv_path.parent)
    frame.to_csv(csv_path, index=False)
    return frame


def group_contrast_rows(frame: pd.DataFrame) -> pd.DataFrame:
    metric_columns = reachability_metric_columns(frame)
    rows: list[dict[str, object]] = []
    for task in TASK_ORDER:
        task_frame = frame[frame["task"] == task].copy()
        for scope in ("global", "regional"):
            scope_frame = task_frame[task_frame["block_scope"] == scope].copy()
            if scope_frame.empty:
                continue
            networks = ["global"] if scope == "global" else list(NETWORK_ORDER)
            for network in networks:
                network_frame = scope_frame[scope_frame["network"] == network].copy()
                left_frame = network_frame[network_frame["group"] == "HC"].copy()
                right_frame = network_frame[network_frame["group"] == "PD"].copy()
                for metric in metric_columns:
                    left = pd.to_numeric(left_frame[metric], errors="coerce").dropna().to_numpy(dtype=float)
                    right = pd.to_numeric(right_frame[metric], errors="coerce").dropna().to_numpy(dtype=float)
                    if left.size < 3 or right.size < 3:
                        continue
                    stat, p_value = stats.mannwhitneyu(left, right, alternative="two-sided")
                    rows.append(
                        {
                            "contrast_name": f"HC_vs_PD_{task}_{scope}_reachability",
                            "task": task,
                            "block_scope": scope,
                            "network": network,
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
    metric_columns = reachability_metric_columns(frame)
    rows: list[dict[str, object]] = []
    pd_runs = frame[frame["group"] == "PD"].copy()
    for task in TASK_ORDER:
        task_frame = pd_runs[pd_runs["task"] == task].copy()
        for scope in ("global", "regional"):
            scope_frame = task_frame[task_frame["block_scope"] == scope].copy()
            if scope_frame.empty:
                continue
            networks = ["global"] if scope == "global" else list(NETWORK_ORDER)
            for variable in PD_CLINICAL_COLUMNS:
                for network in networks:
                    network_frame = scope_frame[scope_frame["network"] == network].copy()
                    x = pd.to_numeric(network_frame[variable], errors="coerce")
                    if x.notna().sum() < 8 or x.nunique(dropna=True) < 3:
                        continue
                    for metric in metric_columns:
                        y = pd.to_numeric(network_frame[metric], errors="coerce")
                        valid = x.notna() & y.notna()
                        if valid.sum() < 8:
                            continue
                        if x[valid].nunique(dropna=True) < 3 or y[valid].nunique(dropna=True) < 3:
                            continue
                        rho, p_value = stats.spearmanr(x[valid], y[valid])
                        rows.append(
                            {
                                "task": task,
                                "block_scope": scope,
                                "network": network,
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
    out["q_value"] = out.groupby(["task", "block_scope", "clinical_variable"], dropna=False)["p_value"].transform(bh_fdr)
    out["abs_rho"] = pd.to_numeric(out["rho"], errors="coerce").abs()
    return out.sort_values(["task", "block_scope", "clinical_variable", "q_value", "p_value", "abs_rho"], ascending=[True, True, True, True, True, False]).reset_index(drop=True)


def build_markdown(run_metrics: pd.DataFrame, group_rows: pd.DataFrame, rho_rows: pd.DataFrame, *, anchor: str, config: ReachabilityConfig) -> str:
    lines = [
        "# Parkinson walking reachability wrappers",
        "",
        "This article-local wrapper calls `ndt_analysis.reachability_cones.summarize_reachability_h5(...)` directly.",
        "",
        f"- Anchor mode: `{anchor}`",
        f"- Coordinate contract: `{anchor_to_contract(anchor)}`",
        f"- Reachability config: `k={config.k}`, `horizon={config.horizon}`, `super_window_size={config.super_window_size}`, `persistence_mode={config.persistence_mode}`",
        f"- Run rows written: `{len(run_metrics)}`",
        "",
        "## Top HC vs PD reachability rows",
        "",
    ]
    if group_rows.empty:
        lines.extend(["No reachability group contrasts were estimable.", ""])
    else:
        for _, row in group_rows.head(12).iterrows():
            lines.append(
                f"- `{row['task']}` / `{row['block_scope']}` / `{row['network']}` / `{row['metric']}`: "
                f"HC median={fmt(row['left_median'])}, PD median={fmt(row['right_median'])}, "
                f"d={fmt(row['effect_size'])}, p={fmt(row['p_value'])}, q={fmt(row['q_value'])}"
            )
        lines.append("")
    lines.extend(["## Top PD rho rows", ""])
    if rho_rows.empty:
        lines.extend(["No reachability clinical rho rows were estimable.", ""])
    else:
        hits = rho_rows[rho_rows["q_value"] < 0.1].copy()
        source = hits if not hits.empty else rho_rows.head(12)
        for _, row in source.head(12).iterrows():
            lines.append(
                f"- `{row['task']}` / `{row['block_scope']}` / `{row['network']}` / `{row['clinical_variable']}` / `{row['metric']}`: "
                f"rho={fmt(row['rho'])}, p={fmt(row['p_value'])}, q={fmt(row['q_value'])}, n={int(row['n_subjects'])}"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    cfg = ReachabilityConfig()
    run_metrics_path = args.output_dir / REACHABILITY_RUN_CSV
    run_metrics = load_or_build_reachability_frame(
        run_metrics_path,
        dataset_root=args.dataset_root,
        participants_tsv=args.participants_tsv,
        anchor=args.anchor,
        rebuild=args.rebuild_run_metrics,
    )
    group_rows = group_contrast_rows(run_metrics)
    rho_rows = clinical_rho_rows(run_metrics)
    if not run_metrics.empty:
        run_metrics.to_csv(run_metrics_path, index=False)
    if not group_rows.empty:
        group_rows.to_csv(args.output_dir / "reachability_group_contrasts.csv", index=False)
    if not rho_rows.empty:
        rho_rows.to_csv(args.output_dir / "reachability_pd_clinical_associations.csv", index=False)
    (args.output_dir / "reachability_summary.md").write_text(
        build_markdown(run_metrics, group_rows, rho_rows, anchor=args.anchor, config=cfg),
        encoding="utf-8",
    )
    manifest = {
        "dataset_root": str(args.dataset_root),
        "participants_tsv": str(args.participants_tsv),
        "output_dir": str(args.output_dir),
        "anchor": args.anchor,
        "coordinate_contract": anchor_to_contract(args.anchor),
        "reachability_config": asdict(cfg),
        "reachability_run_metrics_csv": str(run_metrics_path),
        "n_run_rows": int(len(run_metrics)),
        "n_group_rows": int(len(group_rows)),
        "n_rho_rows": int(len(rho_rows)),
        "networks": ["global", *NETWORK_ORDER],
    }
    write_json(args.output_dir / "reachability_manifest.json", manifest)
    print(f"Wrote reachability wrapper outputs to {args.output_dir}")
    print(f"Run rows: {len(run_metrics)} | group rows: {len(group_rows)} | rho rows: {len(rho_rows)}")


if __name__ == "__main__":
    main()
