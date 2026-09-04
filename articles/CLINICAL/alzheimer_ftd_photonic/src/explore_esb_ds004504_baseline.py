from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from build_photonic_paper_exports import (
    DEFAULT_SELECTION_MODE,
    DEFAULT_RAW_ROOT as DEFAULT_PHOTIC_RAW_ROOT,
    DEFAULT_RESULTS_ROOT,
    MIN_JACOBIAN_WINDOWS,
    MIN_REACHABILITY_POINTS,
    ReachabilityConfig,
    _base_h5_metadata_from_handle,
    _bh_fdr,
    _cohens_d,
    load_stage_window_selection,
    resolve_jacobian_3d,
    resolve_jacobian_9d,
)
from explore_esb_proxy import (
    EYE_STAGE_CODES,
    PHOTIC_STAGE_CODES,
    SPECS,
    STAGE_ORDER,
    _compute_metric_for_indices,
    _safe_scale,
    _stage_rank,
    build_stage_response,
    build_window_inventory,
    load_metric_frame,
)

DEFAULT_REST_RAW_ROOT = Path("J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_ds004504_20260528_114734")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exploratory ESB run using ds004504 as resting-state baseline.")
    parser.add_argument("--photic-raw-root", type=Path, default=DEFAULT_PHOTIC_RAW_ROOT)
    parser.add_argument("--rest-raw-root", type=Path, default=DEFAULT_REST_RAW_ROOT)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--selection-mode", default=DEFAULT_SELECTION_MODE)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_RESULTS_ROOT / "esb_exploration_ds004504_baseline_20260529",
    )
    return parser.parse_args()


def _spec_metric_row(spec_name: str, metric_map: dict[str, float]) -> tuple[float, float]:
    if spec_name == "global_capacity_global_guidance":
        return metric_map["global_capacity"], metric_map["global_guidance"]
    if spec_name == "posterior_capacity_global_guidance":
        return metric_map["posterior_capacity"], metric_map["global_guidance"]
    if spec_name == "posterior_capacity_frontal_guidance":
        return metric_map["posterior_capacity"], metric_map["frontal_guidance"]
    raise KeyError(spec_name)


def _compute_required_metric_map(
    handle: h5py.File,
    h5_path: Path,
    sample_idx: np.ndarray,
    *,
    reach_cfg: ReachabilityConfig,
    base_row: dict[str, object],
    resolved_j3,
    resolved_j9,
) -> dict[str, float]:
    return {
        "global_capacity": _compute_metric_for_indices(
            handle,
            h5_path,
            sample_idx,
            analysis_type="global_reachability_3d",
            network="global",
            metric="tube_d_eff_median",
            reach_cfg=reach_cfg,
            resolved_j3=resolved_j3,
            resolved_j9=resolved_j9,
            base_row=base_row,
        ),
        "posterior_capacity": _compute_metric_for_indices(
            handle,
            h5_path,
            sample_idx,
            analysis_type="regional_reachability_3d",
            network="parietal_occipital",
            metric="tube_d_eff_median",
            reach_cfg=reach_cfg,
            resolved_j3=resolved_j3,
            resolved_j9=resolved_j9,
            base_row=base_row,
        ),
        "global_guidance": _compute_metric_for_indices(
            handle,
            h5_path,
            sample_idx,
            analysis_type="global_mnj_9d",
            network="global",
            metric="rotational_power_median",
            reach_cfg=reach_cfg,
            resolved_j3=resolved_j3,
            resolved_j9=resolved_j9,
            base_row=base_row,
        ),
        "frontal_guidance": _compute_metric_for_indices(
            handle,
            h5_path,
            sample_idx,
            analysis_type="regional_mnj_3d",
            network="frontal",
            metric="rotational_power_median",
            reach_cfg=reach_cfg,
            resolved_j3=resolved_j3,
            resolved_j9=resolved_j9,
            base_row=base_row,
        ),
    }


def build_rest_baseline_metrics(rest_raw_root: Path) -> pd.DataFrame:
    reach_cfg = ReachabilityConfig(persistence_mode="stability")
    rows: list[dict[str, object]] = []
    for h5_path in sorted(rest_raw_root.glob("sub-*/sub-*.h5")):
        subject_id = h5_path.stem.split("_")[0]
        with h5py.File(h5_path, "r") as handle:
            if "time" in handle:
                n_windows = int(np.asarray(handle["time"][:]).reshape(-1).size)
            elif "mnps_3d" in handle:
                n_windows = int(np.asarray(handle["mnps_3d"][:]).shape[0])
            else:
                n_windows = 0
            sample_idx = np.arange(n_windows, dtype=int)
            base_row = _base_h5_metadata_from_handle(handle, h5_path)
            resolved_j3 = resolve_jacobian_3d(handle, "cohort_anchored")
            resolved_j9 = resolve_jacobian_9d(handle, "cohort_anchored")
            metric_map = _compute_required_metric_map(
                handle,
                h5_path,
                sample_idx,
                reach_cfg=reach_cfg,
                base_row=base_row,
                resolved_j3=resolved_j3,
                resolved_j9=resolved_j9,
            )
            for spec in SPECS:
                rest_capacity, rest_guidance = _spec_metric_row(spec.name, metric_map)
                rows.append(
                    {
                        "subject_id": subject_id,
                        "spec_name": spec.name,
                        "spec_label": spec.label,
                        "rest_capacity": rest_capacity,
                        "rest_guidance": rest_guidance,
                        "rest_window_n": int(sample_idx.size),
                        "rest_source_h5_path": str(h5_path),
                    }
                )
    return pd.DataFrame(rows)


def build_photic_recovery_metrics(
    photic_raw_root: Path,
    *,
    selection_mode: str = DEFAULT_SELECTION_MODE,
) -> pd.DataFrame:
    reach_cfg = ReachabilityConfig(persistence_mode="stability")
    selection, _, _ = load_stage_window_selection(photic_raw_root, selection_mode=selection_mode)
    rows: list[dict[str, object]] = []
    for h5_path in sorted(photic_raw_root.glob("sub-*/sub-*.h5")):
        subject_id = h5_path.stem.split("_")[0]
        subject_selection = selection.get(subject_id, {})
        photic_idx = sorted({idx for values in subject_selection.values() for idx in values})
        with h5py.File(h5_path, "r") as handle:
            stage = np.asarray(handle["labels/stage"][:], dtype=int).reshape(-1)
            if not photic_idx:
                for spec in SPECS:
                    rows.append(
                        {
                            "subject_id": subject_id,
                            "spec_name": spec.name,
                            "spec_label": spec.label,
                            "recovery_capacity": float("nan"),
                            "recovery_guidance": float("nan"),
                            "recovery_window_n": 0,
                            "recovery_eye_window_n": 0,
                        }
                    )
                continue
            post_all_idx = np.arange(int(max(photic_idx)) + 1, stage.size, dtype=int)
            post_eye_idx = post_all_idx[np.isin(stage[post_all_idx], list(EYE_STAGE_CODES))]
            recovery_idx = post_eye_idx if post_eye_idx.size >= 2 else post_all_idx
            base_row = _base_h5_metadata_from_handle(handle, h5_path)
            resolved_j3 = resolve_jacobian_3d(handle, "cohort_anchored")
            resolved_j9 = resolve_jacobian_9d(handle, "cohort_anchored")
            metric_map = _compute_required_metric_map(
                handle,
                h5_path,
                recovery_idx,
                reach_cfg=reach_cfg,
                base_row=base_row,
                resolved_j3=resolved_j3,
                resolved_j9=resolved_j9,
            )
            for spec in SPECS:
                recovery_capacity, recovery_guidance = _spec_metric_row(spec.name, metric_map)
                rows.append(
                    {
                        "subject_id": subject_id,
                        "spec_name": spec.name,
                        "spec_label": spec.label,
                        "recovery_capacity": recovery_capacity,
                        "recovery_guidance": recovery_guidance,
                        "recovery_window_n": int(recovery_idx.size),
                        "recovery_eye_window_n": int(post_eye_idx.size),
                    }
                )
    return pd.DataFrame(rows)


def add_ds004504_scores(stage_response: pd.DataFrame, rest_baseline: pd.DataFrame, recovery: pd.DataFrame) -> pd.DataFrame:
    merged = stage_response.merge(
        rest_baseline[["subject_id", "spec_name", "rest_capacity", "rest_guidance", "rest_window_n"]],
        on=["subject_id", "spec_name"],
        how="left",
    ).merge(
        recovery[["subject_id", "spec_name", "recovery_capacity", "recovery_guidance", "recovery_window_n", "recovery_eye_window_n"]],
        on=["subject_id", "spec_name"],
        how="left",
    )
    merged["delta_capacity_rest"] = merged["capacity"] - merged["rest_capacity"]
    merged["delta_guidance_rest"] = merged["guidance"] - merged["rest_guidance"]
    merged["z_capacity_rest"] = np.nan
    merged["z_guidance_rest"] = np.nan
    merged["esb2_ds004504"] = np.nan

    for stage_label, idx in merged.groupby("stage_label", dropna=False).groups.items():
        healthy = merged.loc[idx][
            (merged.loc[idx, "group_label"] == "Healthy")
            & np.isfinite(merged.loc[idx, "delta_capacity_rest"])
            & np.isfinite(merged.loc[idx, "delta_guidance_rest"])
        ].copy()
        if len(healthy) < 3:
            continue
        cap_med = float(np.nanmedian(healthy["delta_capacity_rest"]))
        gui_med = float(np.nanmedian(healthy["delta_guidance_rest"]))
        cap_scale = _safe_scale(healthy["delta_capacity_rest"])
        gui_scale = _safe_scale(healthy["delta_guidance_rest"])
        merged.loc[idx, "z_capacity_rest"] = (merged.loc[idx, "delta_capacity_rest"] - cap_med) / cap_scale
        merged.loc[idx, "z_guidance_rest"] = (merged.loc[idx, "delta_guidance_rest"] - gui_med) / gui_scale
        merged.loc[idx, "esb2_ds004504"] = np.sqrt(
            merged.loc[idx, "z_capacity_rest"] ** 2 + merged.loc[idx, "z_guidance_rest"] ** 2
        ) / np.sqrt(2.0)

    merged["h_rest_raw"] = np.sqrt(
        (merged["recovery_capacity"] - merged["rest_capacity"]) ** 2
        + (merged["recovery_guidance"] - merged["rest_guidance"]) ** 2
    )
    merged["z_h_rest"] = np.nan
    merged["esb3_ds004504"] = np.nan
    healthy_h = merged[
        (merged["group_label"] == "Healthy")
        & np.isfinite(merged["h_rest_raw"])
    ].drop_duplicates(subset=["subject_id", "spec_name"])
    if len(healthy_h) >= 3:
        h_med = float(np.nanmedian(healthy_h["h_rest_raw"]))
        h_scale = _safe_scale(healthy_h["h_rest_raw"])
        merged["z_h_rest"] = (merged["h_rest_raw"] - h_med) / h_scale
        merged["esb3_ds004504"] = np.sqrt(
            merged["z_capacity_rest"] ** 2 + merged["z_guidance_rest"] ** 2 + merged["z_h_rest"] ** 2
        ) / np.sqrt(3.0)
    return merged


def build_group_summary(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    value_cols = ["esb2_ds004504", "esb3_ds004504", "h_rest_raw"]
    group_cols = ["spec_name", "spec_label", "stage_label", "stage_rank", "group_label"]
    for keys, group in scored.groupby(group_cols, dropna=False):
        row = dict(zip(group_cols, keys))
        row["n_subjects"] = int(group["subject_id"].nunique())
        for value_col in value_cols:
            values = pd.to_numeric(group[value_col], errors="coerce").dropna()
            row[f"{value_col}_median"] = float(values.median()) if not values.empty else float("nan")
            row[f"{value_col}_mean"] = float(values.mean()) if not values.empty else float("nan")
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["spec_name", "stage_rank", "group_label"]).reset_index(drop=True)


def build_contrasts(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    score_cols = ["esb2_ds004504", "esb3_ds004504", "h_rest_raw"]
    contrasts = [("AD_vs_Healthy", "AD", "Healthy"), ("FTD_vs_Healthy", "FTD", "Healthy"), ("AD_vs_FTD", "AD", "FTD")]
    group_cols = ["spec_name", "spec_label", "stage_label", "stage_rank"]
    for keys, group in scored.groupby(group_cols, dropna=False):
        base = dict(zip(group_cols, keys))
        for score_col in score_cols:
            for contrast_name, left_group, right_group in contrasts:
                left = pd.to_numeric(group.loc[group["group_label"] == left_group, score_col], errors="coerce").dropna().to_numpy(dtype=float)
                right = pd.to_numeric(group.loc[group["group_label"] == right_group, score_col], errors="coerce").dropna().to_numpy(dtype=float)
                row = dict(base)
                row.update(
                    {
                        "score_name": score_col,
                        "contrast_name": contrast_name,
                        "left_group": left_group,
                        "right_group": right_group,
                        "left_n": int(left.size),
                        "right_n": int(right.size),
                        "left_mean": float(np.mean(left)) if left.size else float("nan"),
                        "right_mean": float(np.mean(right)) if right.size else float("nan"),
                        "effect_size": _cohens_d(left, right),
                        "p_value": float("nan"),
                    }
                )
                if left.size and right.size:
                    from scipy import stats

                    row["p_value"] = float(stats.mannwhitneyu(left, right, alternative="two-sided").pvalue)
                rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["q_value"] = np.nan
    for _, group in out.groupby(["score_name", "contrast_name", "stage_label"], dropna=False):
        out.loc[group.index, "q_value"] = _bh_fdr(group["p_value"]).to_numpy(dtype=float)
    out["abs_effect"] = pd.to_numeric(out["effect_size"], errors="coerce").abs()
    return out.sort_values(["score_name", "contrast_name", "stage_rank", "q_value", "abs_effect"], na_position="last").reset_index(drop=True)


def build_summary_markdown(scored: pd.DataFrame, contrasts: pd.DataFrame, inventory: pd.DataFrame) -> str:
    lines = [
        "# Exploratory ESB summary with ds004504 baseline",
        "",
        "This pass treats `ds004504` resting-state recordings as the subject-level baseline for the same participants found in the photic cohort.",
        "",
        "Definitions used here:",
        "",
        "1. `ESB-2 ds004504`: healthy-template deviation of `[photic - rest]` in capacity-guidance space.",
        "2. `h_rest_raw`: post-photic residual distance from the same subject's ds004504 resting baseline.",
        "3. `ESB-3 ds004504`: `ESB-2 ds004504` plus the normalized residual recovery term.",
        "",
        "## Coverage",
        "",
        f"- Resting-state baseline coverage: `{int(scored[['subject_id','spec_name','rest_capacity','rest_guidance']].drop_duplicates()['subject_id'].nunique())}` subjects.",
        f"- Subjects with at least 4 post-photic windows: `{int((inventory['post_windows_n'] >= 4).sum())}` / `{int(len(inventory))}`.",
        f"- Subjects with at least 2 eye-labeled post-photic windows: `{int((inventory['post_eye_windows_n'] >= 2).sum())}` / `{int(len(inventory))}`.",
        "",
        "## AD vs Healthy highlights",
        "",
    ]
    ad = contrasts[contrasts["contrast_name"] == "AD_vs_Healthy"].copy()
    if ad.empty:
        lines.append("- No contrasts were computed.")
        return "\n".join(lines)
    for score_name in ("esb2_ds004504", "esb3_ds004504", "h_rest_raw"):
        sub = ad[ad["score_name"] == score_name].copy()
        if sub.empty:
            continue
        top = sub.sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]
        lines.append(
            f"- Strongest `{score_name}` row: `{top['spec_name']}` / `{top['stage_label']}` with "
            f"`d = {float(top['effect_size']):.3f}`, `p = {float(top['p_value']):.4g}`, `q = {float(top['q_value']):.4g}`."
        )
    lines.extend(["", "## Frequency pattern check", ""])
    for score_name in ("esb2_ds004504", "esb3_ds004504"):
        sub = ad[ad["score_name"] == score_name].copy()
        if sub.empty:
            continue
        best_spec = sub.sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]["spec_name"]
        pieces = []
        for row in sub[sub["spec_name"] == best_spec].sort_values("stage_rank").itertuples():
            if pd.isna(row.effect_size):
                continue
            pieces.append(f"`{row.stage_label}` d={float(row.effect_size):.3f}")
        if pieces:
            lines.append(f"- `{score_name}` best spec `{best_spec}` across frequencies: " + ", ".join(pieces) + ".")
    lines.extend(
        [
            "",
            "## Readout",
            "",
            "- If ds004504 solves the baseline problem, `ESB-2 ds004504` should become finite for the full cohort and give a cleaner stage-resolved abnormal-response signal than the pre-photic proxy version.",
            "- If the main lift still comes from `h_rest_raw`, the collapse story remains more recovery-led than evoked-deviation-led even under a real external baseline.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    metric_frame = load_metric_frame(args.results_root)
    inventory = build_window_inventory(args.photic_raw_root, selection_mode=args.selection_mode)
    rest_baseline = build_rest_baseline_metrics(args.rest_raw_root)
    recovery = build_photic_recovery_metrics(args.photic_raw_root, selection_mode=args.selection_mode)

    all_scored: list[pd.DataFrame] = []
    for spec in SPECS:
        stage_response = build_stage_response(metric_frame, spec)
        sub_rest = rest_baseline[rest_baseline["spec_name"] == spec.name].copy()
        sub_recovery = recovery[recovery["spec_name"] == spec.name].copy()
        scored = add_ds004504_scores(stage_response, sub_rest, sub_recovery)
        all_scored.append(scored)

    scored_all = pd.concat(all_scored, ignore_index=True)
    scored_all["stage_rank"] = scored_all["stage_label"].map(_stage_rank)
    group_summary = build_group_summary(scored_all)
    contrasts = build_contrasts(scored_all)
    summary_md = build_summary_markdown(scored_all, contrasts, inventory)

    scored_path = args.output_dir / "esb_subject_scores.csv"
    group_path = args.output_dir / "esb_group_summary.csv"
    contrast_path = args.output_dir / "esb_contrasts.csv"
    inventory_path = args.output_dir / "esb_window_inventory.csv"
    rest_path = args.output_dir / "ds004504_rest_baseline_metrics.csv"
    recovery_path = args.output_dir / "photic_recovery_metrics.csv"
    summary_path = args.output_dir / "esb_exploration_summary.md"
    manifest_path = args.output_dir / "esb_exploration_manifest.json"

    scored_all.to_csv(scored_path, index=False)
    group_summary.to_csv(group_path, index=False)
    contrasts.to_csv(contrast_path, index=False)
    inventory.to_csv(inventory_path, index=False)
    rest_baseline.to_csv(rest_path, index=False)
    recovery.to_csv(recovery_path, index=False)
    summary_path.write_text(summary_md, encoding="utf-8")

    manifest = {
        "photic_raw_root": str(args.photic_raw_root),
        "rest_raw_root": str(args.rest_raw_root),
        "results_root": str(args.results_root),
        "output_dir": str(args.output_dir),
        "specs": [spec.__dict__ for spec in SPECS],
        "output_files": {
            "subject_scores": str(scored_path),
            "group_summary": str(group_path),
            "contrasts": str(contrast_path),
            "window_inventory": str(inventory_path),
            "rest_baseline_metrics": str(rest_path),
            "recovery_metrics": str(recovery_path),
            "summary_markdown": str(summary_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote ds004504-baselined ESB exploration outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
