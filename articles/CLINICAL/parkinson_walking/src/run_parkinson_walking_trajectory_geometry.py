from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import MiniBatchKMeans

from parkinson_walking_support import (
    DATASET_ROOT,
    GROUP_ORDER,
    PARTICIPANTS_PATH,
    PD_CLINICAL_COLUMNS,
    RESULTS_DIR,
    TASK_ORDER,
    TRAJECTORY_ALL_METRICS,
    bh_fdr,
    cohens_d,
    curvature_series,
    ensure_dir,
    fmt,
    list_h5_paths,
    load_participants,
    noetic_action_metrics,
    participant_lookup,
    parse_run_slug,
    read_json_dict,
    decode_scalar,
    repertoire_metrics,
    robust_median,
    sample_evenly,
    stable_variance_metric,
    tortuosity,
    path_length,
    write_json,
    _array_paths_for_anchor,
    _first_existing_array,
    _normalize_anchor,
)


TRAJECTORY_DIR = RESULTS_DIR / "trajectory_geometry"
REPERTOIRE_STATES_BY_DIM = {3: 12, 9: 24}
MAX_POINTS_PER_RUN_FOR_FIT = {3: 256, 9: 256}
MAX_CODEBOOK_POINTS_BY_DIM = {3: 40000, 9: 60000}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run exploratory trajectory-geometry metrics for the Parkinson walking dataset."
    )
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--participants-tsv", type=Path, default=PARTICIPANTS_PATH)
    parser.add_argument("--output-dir", type=Path, default=TRAJECTORY_DIR)
    parser.add_argument("--anchor", choices=("auto", "cohort", "subject"), default="auto")
    return parser.parse_args()


def compact_summary_mapping() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"compact_summary_symbol": "H_rate", "implemented_metric": "entropy_rate", "status": "implemented"},
            {"compact_summary_symbol": "I", "implemented_metric": "irreversibility", "status": "implemented"},
            {"compact_summary_symbol": "A_MNPS", "implemented_metric": "noetic_action", "status": "implemented"},
            {"compact_summary_symbol": "kappa_median", "implemented_metric": "curvature_median", "status": "implemented"},
            {"compact_summary_symbol": "T_path", "implemented_metric": "tortuosity", "status": "implemented"},
            {"compact_summary_symbol": "entropy_production", "implemented_metric": "entropy_production", "status": "implemented_supportive"},
            {"compact_summary_symbol": "self_loop_rate", "implemented_metric": "self_loop_rate", "status": "implemented_supportive"},
            {"compact_summary_symbol": "transition_sparsity", "implemented_metric": "transition_sparsity", "status": "implemented_supportive"},
            {"compact_summary_symbol": "return_probability", "implemented_metric": "", "status": "not_implemented_in_this_pass"},
            {"compact_summary_symbol": "torsion", "implemented_metric": "", "status": "not_implemented_in_this_pass"},
            {"compact_summary_symbol": "H_path", "implemented_metric": "", "status": "not_implemented_in_this_pass"},
            {"compact_summary_symbol": "C_ab_tau / A_ab", "implemented_metric": "", "status": "not_implemented_in_this_pass"},
        ]
    )


def collect_run_payloads(dataset_root: Path, participants_tsv: Path, *, anchor: str) -> list[dict[str, Any]]:
    participants = load_participants(participants_tsv)
    participants_by_id = participant_lookup(participants)
    payloads: list[dict[str, Any]] = []
    for h5_path in list_h5_paths(dataset_root):
        parsed = parse_run_slug(h5_path)
        participant_id = parsed["participant_id"]
        participant_row = participants_by_id.get(participant_id, {})
        with h5py.File(h5_path, "r") as handle:
            attrs = {key: decode_scalar(value) for key, value in handle.attrs.items()}
            mapped_json = read_json_dict(handle, "participant/mapped_json")
            row_json = read_json_dict(handle, "participant/row_json")
            task = str(attrs.get("task") or mapped_json.get("task") or parsed["task"])
            group = str(
                participant_row.get("group")
                or attrs.get("meta_group")
                or mapped_json.get("group")
                or row_json.get("group")
                or attrs.get("group")
                or ""
            ).strip() or "unknown"
            coords_3d, coords_3d_path = _first_existing_array(handle, _array_paths_for_anchor("coords3", anchor))
            coords_9d, coords_9d_path = _first_existing_array(handle, _array_paths_for_anchor("coords9", anchor))
            time = np.asarray(handle["time"], dtype=float) if "time" in handle else np.full((0,), np.nan)
        payloads.append(
            {
                "participant_id": participant_id,
                "source_subject_code": participant_row.get("source_subject_code") or attrs.get("meta_subject_id"),
                "group": group,
                "task": task,
                "sex": participant_row.get("sex") or attrs.get("meta_sex"),
                "dataset_id": attrs.get("dataset_id"),
                "h5_path": str(h5_path),
                "anchor_mode_requested": anchor,
                "primary_coordinate_contract": attrs.get("primary_coordinate_contract"),
                "primary_coordinate_layer": attrs.get("primary_coordinate_layer"),
                "coords_3d_path": coords_3d_path,
                "coords_9d_path": coords_9d_path,
                "coords_3d": coords_3d,
                "coords_9d": coords_9d,
                "time": time,
                **{column: participant_row.get(column, float("nan")) for column in PD_CLINICAL_COLUMNS},
                "age": participant_row.get("age", float("nan")),
            }
        )
    return payloads


def fit_codebook(payloads: list[dict[str, Any]], *, dim: int) -> tuple[MiniBatchKMeans, np.ndarray]:
    key = "coords_3d" if dim == 3 else "coords_9d"
    blocks: list[np.ndarray] = []
    for payload in payloads:
        coords = payload.get(key)
        if not isinstance(coords, np.ndarray) or coords.ndim != 2 or len(coords) < 16:
            continue
        blocks.append(sample_evenly(coords, MAX_POINTS_PER_RUN_FOR_FIT[dim]))
    if not blocks:
        raise RuntimeError(f"No usable {dim}D coordinates found for trajectory fitting.")
    sampled = np.concatenate(blocks, axis=0)
    sampled = sample_evenly(sampled, MAX_CODEBOOK_POINTS_BY_DIM[dim])
    model = MiniBatchKMeans(
        n_clusters=REPERTOIRE_STATES_BY_DIM[dim],
        random_state=20260610 + dim,
        n_init=10,
        batch_size=min(4096, max(512, len(sampled))),
        reassignment_ratio=0.01,
    )
    model.fit(sampled)
    return model, stable_variance_metric(sampled)


def trajectory_rows(payloads: list[dict[str, Any]]) -> pd.DataFrame:
    fit_lookup = {dim: fit_codebook(payloads, dim=dim) for dim in (3, 9)}
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        time = np.asarray(payload["time"], dtype=float)
        for dim in (3, 9):
            key = "coords_3d" if dim == 3 else "coords_9d"
            coords = payload.get(key)
            if not isinstance(coords, np.ndarray) or coords.ndim != 2 or len(coords) < 16:
                continue
            model, metric_diag = fit_lookup[dim]
            states = model.predict(coords)
            rep = repertoire_metrics(states, n_states=REPERTOIRE_STATES_BY_DIM[dim])
            action = noetic_action_metrics(coords, time, metric_diag=metric_diag)
            rows.append(
                {
                    "participant_id": payload["participant_id"],
                    "source_subject_code": payload["source_subject_code"],
                    "group": payload["group"],
                    "task": payload["task"],
                    "sex": payload["sex"],
                    "dataset_id": payload["dataset_id"],
                    "h5_path": payload["h5_path"],
                    "anchor_mode_requested": payload["anchor_mode_requested"],
                    "primary_coordinate_contract": payload["primary_coordinate_contract"],
                    "primary_coordinate_layer": payload["primary_coordinate_layer"],
                    "dimension": dim,
                    "analysis_type": f"trajectory_geometry_{payload['anchor_mode_requested']}_{dim}d",
                    "n_windows": int(coords.shape[0]),
                    "coords_path": payload["coords_3d_path"] if dim == 3 else payload["coords_9d_path"],
                    "curvature_median": robust_median(curvature_series(coords, time)),
                    "tortuosity": tortuosity(coords),
                    "path_length": path_length(coords),
                    **rep,
                    **action,
                    **{column: payload.get(column, float("nan")) for column in PD_CLINICAL_COLUMNS},
                }
            )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["group"] = pd.Categorical(frame["group"], categories=GROUP_ORDER, ordered=True)
    frame["task"] = pd.Categorical(frame["task"], categories=TASK_ORDER, ordered=True)
    return frame.sort_values(["dimension", "group", "participant_id", "task"], na_position="last").reset_index(drop=True)


def group_contrasts(trajectory_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for task in TASK_ORDER:
        task_frame = trajectory_metrics[trajectory_metrics["task"] == task].copy()
        for dim in (3, 9):
            dim_frame = task_frame[task_frame["dimension"] == dim].copy()
            left_frame = dim_frame[dim_frame["group"] == "HC"].copy()
            right_frame = dim_frame[dim_frame["group"] == "PD"].copy()
            for metric in TRAJECTORY_ALL_METRICS:
                left = pd.to_numeric(left_frame[metric], errors="coerce").dropna().to_numpy(dtype=float)
                right = pd.to_numeric(right_frame[metric], errors="coerce").dropna().to_numpy(dtype=float)
                if left.size < 3 or right.size < 3:
                    continue
                stat, p_value = stats.mannwhitneyu(left, right, alternative="two-sided")
                rows.append(
                    {
                        "contrast_name": f"HC_vs_PD_{task}_trajectory_{dim}d",
                        "task": task,
                        "dimension": dim,
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
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["q_value"] = frame.groupby("contrast_name", dropna=False)["p_value"].transform(bh_fdr)
    frame["abs_effect_size"] = pd.to_numeric(frame["effect_size"], errors="coerce").abs()
    return frame.sort_values(["contrast_name", "q_value", "p_value", "abs_effect_size"], ascending=[True, True, True, False]).reset_index(drop=True)


def clinical_associations(trajectory_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    pd_runs = trajectory_metrics[trajectory_metrics["group"] == "PD"].copy()
    for task in TASK_ORDER:
        task_frame = pd_runs[pd_runs["task"] == task].copy()
        for dim in (3, 9):
            dim_frame = task_frame[task_frame["dimension"] == dim].copy()
            for variable in PD_CLINICAL_COLUMNS:
                x = pd.to_numeric(dim_frame[variable], errors="coerce")
                if x.notna().sum() < 8 or x.nunique(dropna=True) < 3:
                    continue
                for metric in TRAJECTORY_ALL_METRICS:
                    y = pd.to_numeric(dim_frame[metric], errors="coerce")
                    valid = x.notna() & y.notna()
                    if valid.sum() < 8:
                        continue
                    if x[valid].nunique(dropna=True) < 3 or y[valid].nunique(dropna=True) < 3:
                        continue
                    rho, p_value = stats.spearmanr(x[valid], y[valid])
                    rows.append(
                        {
                            "task": task,
                            "group": "PD",
                            "dimension": dim,
                            "clinical_variable": variable,
                            "metric": metric,
                            "n_subjects": int(valid.sum()),
                            "rho": float(rho) if np.isfinite(rho) else np.nan,
                            "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
                        }
                    )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["q_value"] = frame.groupby(["task", "dimension", "clinical_variable"], dropna=False)["p_value"].transform(bh_fdr)
    frame["abs_rho"] = pd.to_numeric(frame["rho"], errors="coerce").abs()
    return frame.sort_values(["task", "dimension", "clinical_variable", "q_value", "p_value", "abs_rho"], ascending=[True, True, True, True, True, False]).reset_index(drop=True)


def build_markdown(group_rows: pd.DataFrame, clinical_rows: pd.DataFrame, *, anchor: str) -> str:
    lines = [
        "# Parkinson walking trajectory geometry",
        "",
        "This pass is explicitly exploratory and follows the compact-summary trajectory layer rather than the standard NMD contract.",
        "",
        f"- Anchor mode: `{anchor}`",
        "- Implemented compact-summary endpoints: `H_rate`, `I`, `A_MNPS`, `kappa_median`, `T_path`",
        "- Here these map to `entropy_rate`, `irreversibility`, `noetic_action`, `curvature_median`, and `tortuosity`",
        "",
        "## Top HC vs PD trajectory rows",
        "",
    ]
    if group_rows.empty:
        lines.extend(["No trajectory group contrasts were estimable.", ""])
    else:
        for _, row in group_rows.head(12).iterrows():
            lines.append(
                f"- `{row['task']}` / `{int(row['dimension'])}D` / `{row['metric']}`: "
                f"HC median={fmt(row['left_median'])}, PD median={fmt(row['right_median'])}, "
                f"d={fmt(row['effect_size'])}, p={fmt(row['p_value'])}, q={fmt(row['q_value'])}"
            )
        lines.append("")
    lines.extend(["## Top rho rows", ""])
    if clinical_rows.empty:
        lines.extend(["No trajectory clinical rho rows were estimable.", ""])
    else:
        hits = clinical_rows[clinical_rows["q_value"] < 0.1].copy()
        source = hits if not hits.empty else clinical_rows.head(12)
        for _, row in source.head(12).iterrows():
            lines.append(
                f"- `{row['task']}` / `{int(row['dimension'])}D` / `{row['clinical_variable']}` / `{row['metric']}`: "
                f"rho={fmt(row['rho'])}, p={fmt(row['p_value'])}, q={fmt(row['q_value'])}, n={int(row['n_subjects'])}"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    anchor = _normalize_anchor(args.anchor)
    payloads = collect_run_payloads(args.dataset_root, args.participants_tsv, anchor=anchor)
    trajectory_metrics = trajectory_rows(payloads)
    group_rows = group_contrasts(trajectory_metrics)
    clinical_rows = clinical_associations(trajectory_metrics)
    mapping = compact_summary_mapping()
    if not trajectory_metrics.empty:
        trajectory_metrics.to_csv(args.output_dir / "trajectory_run_metrics.csv", index=False)
    if not group_rows.empty:
        group_rows.to_csv(args.output_dir / "trajectory_group_contrasts.csv", index=False)
    if not clinical_rows.empty:
        clinical_rows.to_csv(args.output_dir / "trajectory_pd_clinical_associations.csv", index=False)
    mapping.to_csv(args.output_dir / "compact_summary_metric_mapping.csv", index=False)
    (args.output_dir / "trajectory_summary.md").write_text(build_markdown(group_rows, clinical_rows, anchor=anchor), encoding="utf-8")
    manifest = {
        "dataset_root": str(args.dataset_root),
        "participants_tsv": str(args.participants_tsv),
        "output_dir": str(args.output_dir),
        "anchor": anchor,
        "n_payloads": int(len(payloads)),
        "n_trajectory_rows": int(len(trajectory_metrics)),
        "n_group_rows": int(len(group_rows)),
        "n_clinical_rows": int(len(clinical_rows)),
        "implemented_compact_summary_metrics": compact_summary_mapping().to_dict(orient="records"),
    }
    write_json(args.output_dir / "trajectory_manifest.json", manifest)
    print(f"Wrote trajectory geometry outputs to {args.output_dir}")
    print(f"Trajectory rows: {len(trajectory_metrics)} | group rows: {len(group_rows)} | rho rows: {len(clinical_rows)}")


if __name__ == "__main__":
    main()
