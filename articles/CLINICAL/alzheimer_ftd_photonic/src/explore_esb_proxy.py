from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy import stats

from build_photonic_paper_exports import (
    DEFAULT_SELECTION_MODE,
    DEFAULT_RAW_ROOT,
    DEFAULT_RESULTS_ROOT,
    MIN_JACOBIAN_WINDOWS,
    MIN_REACHABILITY_POINTS,
    ReachabilityConfig,
    _base_h5_metadata_from_handle,
    _bh_fdr,
    _cohens_d,
    _estimate_temporal_jacobian_delta,
    _regional_jacobian_row,
    _summarize_global_mnps_jacobian_row,
    load_stage_window_selection,
    resolve_jacobian_3d,
    resolve_jacobian_9d,
    summarize_reachability_h5,
)

STAGE_ORDER = ["photo_5hz", "photo_10hz", "photo_15hz", "photo_20hz"]
PHOTIC_STAGE_CODES = {50, 51, 52, 53}
EYE_STAGE_CODES = {60, 61, 62}
EPS = 1e-9


@dataclass(frozen=True)
class ResponseSpec:
    name: str
    capacity_analysis_type: str
    capacity_network: str
    capacity_metric: str
    guidance_analysis_type: str
    guidance_network: str
    guidance_metric: str
    label: str


SPECS: tuple[ResponseSpec, ...] = (
    ResponseSpec(
        name="global_capacity_global_guidance",
        capacity_analysis_type="global_reachability_3d",
        capacity_network="global",
        capacity_metric="tube_d_eff_median",
        guidance_analysis_type="global_mnj_9d",
        guidance_network="global",
        guidance_metric="rotational_power_median",
        label="Global 3D d_eff + Global 9D rotational power",
    ),
    ResponseSpec(
        name="posterior_capacity_global_guidance",
        capacity_analysis_type="regional_reachability_3d",
        capacity_network="parietal_occipital",
        capacity_metric="tube_d_eff_median",
        guidance_analysis_type="global_mnj_9d",
        guidance_network="global",
        guidance_metric="rotational_power_median",
        label="Parietal-occipital 3D d_eff + Global 9D rotational power",
    ),
    ResponseSpec(
        name="posterior_capacity_frontal_guidance",
        capacity_analysis_type="regional_reachability_3d",
        capacity_network="parietal_occipital",
        capacity_metric="tube_d_eff_median",
        guidance_analysis_type="regional_mnj_3d",
        guidance_network="frontal",
        guidance_metric="rotational_power_median",
        label="Parietal-occipital 3D d_eff + Frontal 3D rotational power",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exploratory ESB-2 / ESB-3 proxy runner for the photic dementia article.")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--selection-mode", default=DEFAULT_SELECTION_MODE)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_RESULTS_ROOT / "esb_exploration_proxy_20260529",
    )
    return parser.parse_args()


def _robust_mad(values: pd.Series) -> float:
    arr = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if arr.size == 0:
        return float("nan")
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    return mad


def _safe_scale(values: pd.Series) -> float:
    mad = _robust_mad(values)
    if np.isfinite(mad) and mad > EPS:
        return float(mad)
    arr = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if arr.size >= 2:
        alt = float(np.std(arr, ddof=1))
        if np.isfinite(alt) and alt > EPS:
            return alt
    return 1.0


def _stage_rank(stage_label: str) -> int:
    try:
        return STAGE_ORDER.index(stage_label)
    except ValueError:
        return 999


def _sample_mask_from_indices(centers: np.ndarray | None, sample_indices: np.ndarray, n_windows: int) -> np.ndarray:
    sample_indices = np.asarray(sample_indices, dtype=int).reshape(-1)
    if centers is None:
        centers_arr = np.arange(n_windows, dtype=int)
    else:
        centers_arr = np.asarray(centers[:n_windows], dtype=int).reshape(-1)
    lookup = np.zeros((max(int(centers_arr.max()) + 1 if centers_arr.size else 0, int(sample_indices.max()) + 1 if sample_indices.size else 0, 1),), dtype=bool)
    valid_samples = sample_indices[(sample_indices >= 0) & (sample_indices < lookup.size)]
    lookup[valid_samples] = True
    mask = np.zeros((n_windows,), dtype=bool)
    valid_centers = (centers_arr >= 0) & (centers_arr < lookup.size)
    mask[: centers_arr.shape[0]] = valid_centers & lookup[centers_arr]
    return mask


def _compute_metric_for_indices(
    handle: h5py.File,
    h5_path: Path,
    sample_indices: np.ndarray,
    *,
    analysis_type: str,
    network: str,
    metric: str,
    reach_cfg: ReachabilityConfig,
    resolved_j3,
    resolved_j9,
    base_row: dict[str, object],
) -> float:
    sample_indices = np.asarray(sample_indices, dtype=int).reshape(-1)
    sample_indices = sample_indices[sample_indices >= 0]
    if analysis_type == "global_reachability_3d":
        if sample_indices.size < MIN_REACHABILITY_POINTS:
            return float("nan")
        flat = summarize_reachability_h5(
            h5_path,
            config=reach_cfg,
            coordinate_contract="cohort_anchored",
            sample_indices=sample_indices,
        )["flat"]
        return float(flat.get(metric, np.nan))
    if analysis_type == "regional_reachability_3d":
        net_grp = handle["regional_mnps"][network]
        if "mnps" not in net_grp:
            return float("nan")
        region_idx = sample_indices[sample_indices < int(net_grp["mnps"].shape[0])]
        if region_idx.size < MIN_REACHABILITY_POINTS:
            return float("nan")
        flat = summarize_reachability_h5(
            h5_path,
            config=reach_cfg,
            sample_indices=region_idx,
            dataset_path=f"/regional_mnps/{network}/mnps",
            used_space_override="regional_mnps_3d",
            flat_overrides={
                "network": network,
                "source_dataset_path": f"/regional_mnps/{network}/mnps",
            },
        )["flat"]
        return float(flat.get(metric, np.nan))
    if analysis_type == "global_mnj_9d":
        if resolved_j9 is None:
            return float("nan")
        mask = _sample_mask_from_indices(resolved_j9.centers, sample_indices, int(resolved_j9.j_hat.shape[0]))
        if int(mask.sum()) < MIN_JACOBIAN_WINDOWS:
            return float("nan")
        row = _summarize_global_mnps_jacobian_row(
            dict(base_row),
            resolved_j9.j_hat[mask],
            resolved_j9.j_dot[mask] if resolved_j9.j_dot is not None else None,
            source_dataset_path=resolved_j9.dataset_path,
            dims=9,
        )
        return float(row.get(metric, np.nan)) if row is not None else float("nan")
    if analysis_type == "regional_mnj_3d":
        net_grp = handle["regional_mnps"][network]
        if "jacobian" not in net_grp:
            return float("nan")
        regional_j = np.asarray(net_grp["jacobian"][:], dtype=float)
        if regional_j.ndim != 3 or regional_j.shape[1:] != (3, 3):
            return float("nan")
        centers3 = resolved_j3.centers if resolved_j3 is not None else None
        mask = _sample_mask_from_indices(centers3, sample_indices, int(regional_j.shape[0]))
        if int(mask.sum()) < MIN_JACOBIAN_WINDOWS:
            return float("nan")
        regional_j_dot = None
        if "jacobian_dot" in net_grp:
            candidate = np.asarray(net_grp["jacobian_dot"][:], dtype=float)
            if candidate.shape == regional_j.shape:
                regional_j_dot = candidate[mask]
        if regional_j_dot is None:
            delta = _estimate_temporal_jacobian_delta(regional_j)
            regional_j_dot = delta[mask] if delta is not None else None
        row = _regional_jacobian_row(
            dict(base_row),
            j_hat=regional_j[mask],
            j_dot=regional_j_dot,
            network=network,
        )
        return float(row.get(metric, np.nan)) if row is not None else float("nan")
    raise ValueError(f"Unsupported analysis_type: {analysis_type}")


def load_metric_frame(results_root: Path) -> pd.DataFrame:
    path = results_root / "subject_stage_region_metrics.csv"
    frame = pd.read_csv(path)
    frame = frame[frame["stage_label"].isin(STAGE_ORDER)].copy()
    return frame


def build_stage_response(metric_frame: pd.DataFrame, spec: ResponseSpec) -> pd.DataFrame:
    need = [
        (spec.capacity_analysis_type, spec.capacity_network, spec.capacity_metric, "capacity"),
        (spec.guidance_analysis_type, spec.guidance_network, spec.guidance_metric, "guidance"),
    ]
    rows: list[pd.DataFrame] = []
    for analysis_type, network, metric, component in need:
        sub = metric_frame[
            (metric_frame["analysis_type"] == analysis_type)
            & (metric_frame["network"] == network)
            & (metric_frame["metric"] == metric)
        ][["subject_id", "group", "group_label", "mmse", "stage_label", "stage_display_label", "value"]].copy()
        sub = sub.rename(columns={"value": component})
        rows.append(sub)
    merged = rows[0].merge(
        rows[1][["subject_id", "stage_label", "guidance"]],
        on=["subject_id", "stage_label"],
        how="inner",
    )
    merged["spec_name"] = spec.name
    merged["spec_label"] = spec.label
    merged["stage_rank"] = merged["stage_label"].map(_stage_rank)
    return merged


def score_proxy_esb(stage_response: pd.DataFrame) -> pd.DataFrame:
    out = stage_response.copy()
    out["hc_capacity_median"] = np.nan
    out["hc_guidance_median"] = np.nan
    out["hc_capacity_scale"] = np.nan
    out["hc_guidance_scale"] = np.nan
    out["z_capacity"] = np.nan
    out["z_guidance"] = np.nan
    out["esb2_proxy"] = np.nan
    for stage_label, idx in out.groupby("stage_label", dropna=False).groups.items():
        healthy = out.loc[idx][out.loc[idx, "group_label"] == "Healthy"].copy()
        if healthy.empty:
            continue
        cap_med = float(np.median(healthy["capacity"]))
        gui_med = float(np.median(healthy["guidance"]))
        cap_scale = _safe_scale(healthy["capacity"])
        gui_scale = _safe_scale(healthy["guidance"])
        out.loc[idx, "hc_capacity_median"] = cap_med
        out.loc[idx, "hc_guidance_median"] = gui_med
        out.loc[idx, "hc_capacity_scale"] = cap_scale
        out.loc[idx, "hc_guidance_scale"] = gui_scale
        out.loc[idx, "z_capacity"] = (out.loc[idx, "capacity"] - cap_med) / cap_scale
        out.loc[idx, "z_guidance"] = (out.loc[idx, "guidance"] - gui_med) / gui_scale
        out.loc[idx, "esb2_proxy"] = np.sqrt(out.loc[idx, "z_capacity"] ** 2 + out.loc[idx, "z_guidance"] ** 2) / np.sqrt(2.0)
    return out


def build_window_inventory(raw_root: Path, *, selection_mode: str = DEFAULT_SELECTION_MODE) -> pd.DataFrame:
    selection, _, _ = load_stage_window_selection(raw_root, selection_mode=selection_mode)
    rows: list[dict[str, object]] = []
    for h5_path in sorted(raw_root.glob("sub-*/sub-*.h5")):
        subject_id = h5_path.stem.split("_")[0]
        subject_selection = selection.get(subject_id, {})
        with h5py.File(h5_path, "r") as handle:
            stage = np.asarray(handle["labels/stage"][:], dtype=int).reshape(-1)
        photic_idx = sorted({idx for values in subject_selection.values() for idx in values})
        if not photic_idx:
            continue
        first_photic = int(min(photic_idx))
        last_photic = int(max(photic_idx))
        pre_idx = np.arange(first_photic, dtype=int)
        post_idx = np.arange(last_photic + 1, stage.size, dtype=int)
        post_eye_idx = post_idx[np.isin(stage[post_idx], list(EYE_STAGE_CODES))]
        rows.append(
            {
                "subject_id": subject_id,
                "source_h5_path": str(h5_path),
                "n_windows": int(stage.size),
                "first_photic_idx": first_photic,
                "last_photic_idx": last_photic,
                "pre_windows_n": int(pre_idx.size),
                "post_windows_n": int(post_idx.size),
                "post_eye_windows_n": int(post_eye_idx.size),
            }
        )
    return pd.DataFrame(rows)

def build_anchor_metrics(
    raw_root: Path,
    spec: ResponseSpec,
    *,
    selection_mode: str = DEFAULT_SELECTION_MODE,
) -> pd.DataFrame:
    reach_cfg = ReachabilityConfig(persistence_mode="stability")
    selection, _, _ = load_stage_window_selection(raw_root, selection_mode=selection_mode)
    rows: list[dict[str, object]] = []
    for h5_path in sorted(raw_root.glob("sub-*/sub-*.h5")):
        subject_id = h5_path.stem.split("_")[0]
        subject_selection = selection.get(subject_id, {})
        photic_idx = sorted({idx for values in subject_selection.values() for idx in values})
        if not photic_idx:
            continue
        with h5py.File(h5_path, "r") as handle:
            stage = np.asarray(handle["labels/stage"][:], dtype=int).reshape(-1)
            first_photic = int(min(photic_idx))
            last_photic = int(max(photic_idx))
            pre_idx = np.arange(first_photic, dtype=int)
            post_all_idx = np.arange(last_photic + 1, stage.size, dtype=int)
            post_eye_idx = post_all_idx[np.isin(stage[post_all_idx], list(EYE_STAGE_CODES))]
            recovery_idx = post_eye_idx if post_eye_idx.size >= 2 else post_all_idx
            base_row = _base_h5_metadata_from_handle(handle, h5_path)
            resolved_j3 = resolve_jacobian_3d(handle, "cohort_anchored")
            resolved_j9 = resolve_jacobian_9d(handle, "cohort_anchored")

            baseline_capacity = _compute_metric_for_indices(
                handle,
                h5_path,
                pre_idx,
                analysis_type=spec.capacity_analysis_type,
                network=spec.capacity_network,
                metric=spec.capacity_metric,
                reach_cfg=reach_cfg,
                resolved_j3=resolved_j3,
                resolved_j9=resolved_j9,
                base_row=base_row,
            )
            baseline_guidance = _compute_metric_for_indices(
                handle,
                h5_path,
                pre_idx,
                analysis_type=spec.guidance_analysis_type,
                network=spec.guidance_network,
                metric=spec.guidance_metric,
                reach_cfg=reach_cfg,
                resolved_j3=resolved_j3,
                resolved_j9=resolved_j9,
                base_row=base_row,
            )
            recovery_capacity = _compute_metric_for_indices(
                handle,
                h5_path,
                recovery_idx,
                analysis_type=spec.capacity_analysis_type,
                network=spec.capacity_network,
                metric=spec.capacity_metric,
                reach_cfg=reach_cfg,
                resolved_j3=resolved_j3,
                resolved_j9=resolved_j9,
                base_row=base_row,
            )
            recovery_guidance = _compute_metric_for_indices(
                handle,
                h5_path,
                recovery_idx,
                analysis_type=spec.guidance_analysis_type,
                network=spec.guidance_network,
                metric=spec.guidance_metric,
                reach_cfg=reach_cfg,
                resolved_j3=resolved_j3,
                resolved_j9=resolved_j9,
                base_row=base_row,
            )
            rows.append(
                {
                    "subject_id": subject_id,
                    "spec_name": spec.name,
                    "baseline_capacity": baseline_capacity,
                    "baseline_guidance": baseline_guidance,
                    "recovery_capacity": recovery_capacity,
                    "recovery_guidance": recovery_guidance,
                    "baseline_window_n": int(pre_idx.size),
                    "recovery_window_n": int(recovery_idx.size),
                    "recovery_eye_window_n": int(post_eye_idx.size),
                }
            )
    return pd.DataFrame(rows)


def add_proxy_hysteresis(scored: pd.DataFrame, anchors: pd.DataFrame) -> pd.DataFrame:
    merged = scored.merge(anchors, on=["subject_id", "spec_name"], how="left")
    if "spec_label_x" in merged.columns:
        merged["spec_label"] = merged["spec_label_x"]
        merged = merged.drop(columns=["spec_label_x"], errors="ignore")
    if "spec_label_y" in merged.columns:
        merged = merged.drop(columns=["spec_label_y"], errors="ignore")
    merged["z_recovery_capacity"] = np.nan
    merged["z_recovery_guidance"] = np.nan
    merged["h_proxy"] = np.nan
    merged["esb3_proxy"] = np.nan
    healthy = merged[merged["group_label"] == "Healthy"].copy().drop_duplicates(subset=["subject_id"])
    if healthy.empty:
        return merged
    cap_med = float(np.nanmedian(healthy["recovery_capacity"]))
    gui_med = float(np.nanmedian(healthy["recovery_guidance"]))
    cap_scale = _safe_scale(healthy["recovery_capacity"])
    gui_scale = _safe_scale(healthy["recovery_guidance"])
    merged["z_recovery_capacity"] = (merged["recovery_capacity"] - cap_med) / cap_scale
    merged["z_recovery_guidance"] = (merged["recovery_guidance"] - gui_med) / gui_scale
    merged["h_proxy"] = np.sqrt(merged["z_recovery_capacity"] ** 2 + merged["z_recovery_guidance"] ** 2) / np.sqrt(2.0)
    merged["esb3_proxy"] = np.sqrt(
        merged["z_capacity"] ** 2 + merged["z_guidance"] ** 2 + merged["h_proxy"] ** 2
    ) / np.sqrt(3.0)
    return merged


def add_strict_scores(scored_with_proxy: pd.DataFrame) -> pd.DataFrame:
    out = scored_with_proxy.copy()
    out["delta_capacity"] = out["capacity"] - out["baseline_capacity"]
    out["delta_guidance"] = out["guidance"] - out["baseline_guidance"]
    out["h_strict_raw"] = np.sqrt(
        (out["recovery_capacity"] - out["baseline_capacity"]) ** 2
        + (out["recovery_guidance"] - out["baseline_guidance"]) ** 2
    )
    out["z_capacity_strict"] = np.nan
    out["z_guidance_strict"] = np.nan
    out["esb2_strict"] = np.nan
    for stage_label, idx in out.groupby("stage_label", dropna=False).groups.items():
        healthy = out.loc[idx][
            (out.loc[idx, "group_label"] == "Healthy")
            & np.isfinite(out.loc[idx, "delta_capacity"])
            & np.isfinite(out.loc[idx, "delta_guidance"])
        ].copy()
        if len(healthy) < 3:
            continue
        cap_med = float(np.nanmedian(healthy["delta_capacity"]))
        gui_med = float(np.nanmedian(healthy["delta_guidance"]))
        cap_scale = _safe_scale(healthy["delta_capacity"])
        gui_scale = _safe_scale(healthy["delta_guidance"])
        out.loc[idx, "z_capacity_strict"] = (out.loc[idx, "delta_capacity"] - cap_med) / cap_scale
        out.loc[idx, "z_guidance_strict"] = (out.loc[idx, "delta_guidance"] - gui_med) / gui_scale
        out.loc[idx, "esb2_strict"] = np.sqrt(
            out.loc[idx, "z_capacity_strict"] ** 2 + out.loc[idx, "z_guidance_strict"] ** 2
        ) / np.sqrt(2.0)

    out["z_h_strict"] = np.nan
    out["esb3_strict"] = np.nan
    healthy_h = out[(out["group_label"] == "Healthy") & np.isfinite(out["h_strict_raw"])].drop_duplicates(subset=["subject_id"])
    if len(healthy_h) >= 3:
        h_med = float(np.nanmedian(healthy_h["h_strict_raw"]))
        h_scale = _safe_scale(healthy_h["h_strict_raw"])
        out["z_h_strict"] = (out["h_strict_raw"] - h_med) / h_scale
        out["esb3_strict"] = np.sqrt(
            out["z_capacity_strict"] ** 2 + out["z_guidance_strict"] ** 2 + out["z_h_strict"] ** 2
        ) / np.sqrt(3.0)
    return out


def build_group_summary(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    value_cols = ["esb2_proxy", "esb3_proxy", "esb2_strict", "esb3_strict", "h_proxy", "h_strict_raw"]
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
    score_cols = ["esb2_proxy", "esb3_proxy", "esb2_strict", "esb3_strict", "h_proxy", "h_strict_raw"]
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
                        "p_value": float(stats.mannwhitneyu(left, right, alternative="two-sided").pvalue)
                        if left.size and right.size
                        else float("nan"),
                    }
                )
                rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["q_value"] = np.nan
    for _, group in out.groupby(["score_name", "contrast_name", "stage_label"], dropna=False):
        out.loc[group.index, "q_value"] = _bh_fdr(group["p_value"]).to_numpy(dtype=float)
    out["abs_effect"] = pd.to_numeric(out["effect_size"], errors="coerce").abs()
    return out.sort_values(["score_name", "contrast_name", "stage_rank", "q_value", "abs_effect"], na_position="last").reset_index(drop=True)


def build_summary_markdown(
    scored: pd.DataFrame,
    contrasts: pd.DataFrame,
    inventory: pd.DataFrame,
) -> str:
    lines = [
        "# Exploratory ESB proxy summary",
        "",
        "This pass uses the current manuscript-facing photic export surface and tests two exploratory constructions:",
        "",
        "1. `ESB-2 proxy`: healthy-template deviation in capacity-guidance space on the observed photic stage.",
        "2. `ESB-3 proxy`: `ESB-2 proxy` plus a session-level recovery abnormality term derived from post-photic windows.",
        "",
        "A stricter within-subject baseline/recovery variant is also attempted where pre-photic coverage is sufficient.",
        "",
        "## Coverage",
        "",
    ]
    if not inventory.empty:
        lines.extend(
            [
                f"- Subjects with any pre-photic windows: `{int((inventory['pre_windows_n'] > 0).sum())}` / `{int(len(inventory))}`.",
                f"- Subjects with at least 4 pre-photic windows: `{int((inventory['pre_windows_n'] >= 4).sum())}` / `{int(len(inventory))}`.",
                f"- Subjects with at least 4 post-photic windows: `{int((inventory['post_windows_n'] >= 4).sum())}` / `{int(len(inventory))}`.",
                f"- Subjects with at least 2 eye-labeled post-photic windows: `{int((inventory['post_eye_windows_n'] >= 2).sum())}` / `{int(len(inventory))}`.",
                "",
            ]
        )
    strict_nonnull = scored.dropna(subset=["esb2_strict"]).copy()
    lines.append(f"- Strict within-subject `ESB-2` coverage: `{int(strict_nonnull['subject_id'].nunique())}` subjects contribute at least one finite score.")
    lines.append("")

    lines.append("## AD vs Healthy highlights")
    lines.append("")
    ad = contrasts[contrasts["contrast_name"] == "AD_vs_Healthy"].copy()
    if ad.empty:
        lines.append("- No contrasts were computed.")
        return "\n".join(lines)

    for score_name in ("esb2_proxy", "esb3_proxy", "esb2_strict", "esb3_strict"):
        sub = ad[ad["score_name"] == score_name].copy()
        if sub.empty:
            continue
        top = sub.sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]
        lines.append(
            f"- Strongest `{score_name}` row: `{top['spec_name']}` / `{top['stage_label']}` with "
            f"`d = {float(top['effect_size']):.3f}`, `p = {float(top['p_value']):.4g}`, `q = {float(top['q_value']):.4g}`."
        )
    lines.append("")

    lines.append("## Frequency pattern check")
    lines.append("")
    for score_name in ("esb2_proxy", "esb3_proxy"):
        sub = ad[ad["score_name"] == score_name].copy()
        if sub.empty:
            continue
        best_spec = (
            sub.sort_values(["q_value", "p_value", "abs_effect"], na_position="last")
            .iloc[0]["spec_name"]
        )
        spec_rows = sub[sub["spec_name"] == best_spec].sort_values("stage_rank")
        pieces = []
        for row in spec_rows.itertuples():
            if pd.isna(row.effect_size):
                continue
            pieces.append(f"`{row.stage_label}` d={float(row.effect_size):.3f}")
        if pieces:
            lines.append(f"- `{score_name}` best spec `{best_spec}` across frequencies: " + ", ".join(pieces) + ".")
    lines.append("")

    lines.append("## Readout")
    lines.append("")
    lines.append(
        "- Clear capture would look like AD-vs-Healthy separation growing toward higher photic frequencies and remaining at least directionally coherent after adding the recovery term."
    )
    lines.append(
        "- If the strict within-subject version is sparse but the proxy version is coherent, that suggests the concept may be real while the current ds006036 baseline labeling is too thin for a clean article-grade ESB-3."
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    metric_frame = load_metric_frame(args.results_root)
    inventory = build_window_inventory(args.raw_root, selection_mode=args.selection_mode)
    all_scored: list[pd.DataFrame] = []
    anchor_frames: list[pd.DataFrame] = []

    for spec in SPECS:
        stage_response = build_stage_response(metric_frame, spec)
        scored = score_proxy_esb(stage_response)
        anchors = build_anchor_metrics(args.raw_root, spec, selection_mode=args.selection_mode)
        anchors["spec_label"] = spec.label
        scored = add_proxy_hysteresis(scored, anchors)
        scored = add_strict_scores(scored)
        all_scored.append(scored)
        anchor_frames.append(anchors)

    scored_all = pd.concat(all_scored, ignore_index=True)
    anchors_all = pd.concat(anchor_frames, ignore_index=True)
    group_summary = build_group_summary(scored_all)
    contrasts = build_contrasts(scored_all)
    summary_md = build_summary_markdown(scored_all, contrasts, inventory)

    scored_path = args.output_dir / "esb_subject_scores.csv"
    group_path = args.output_dir / "esb_group_summary.csv"
    contrast_path = args.output_dir / "esb_contrasts.csv"
    inventory_path = args.output_dir / "esb_window_inventory.csv"
    anchor_path = args.output_dir / "esb_anchor_metrics.csv"
    summary_path = args.output_dir / "esb_exploration_summary.md"
    manifest_path = args.output_dir / "esb_exploration_manifest.json"

    scored_all.to_csv(scored_path, index=False)
    group_summary.to_csv(group_path, index=False)
    contrasts.to_csv(contrast_path, index=False)
    inventory.to_csv(inventory_path, index=False)
    anchors_all.to_csv(anchor_path, index=False)
    summary_path.write_text(summary_md, encoding="utf-8")

    manifest = {
        "raw_root": str(args.raw_root),
        "results_root": str(args.results_root),
        "output_dir": str(args.output_dir),
        "specs": [spec.__dict__ for spec in SPECS],
        "output_files": {
            "subject_scores": str(scored_path),
            "group_summary": str(group_path),
            "contrasts": str(contrast_path),
            "window_inventory": str(inventory_path),
            "anchor_metrics": str(anchor_path),
            "summary_markdown": str(summary_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote ESB exploration outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
