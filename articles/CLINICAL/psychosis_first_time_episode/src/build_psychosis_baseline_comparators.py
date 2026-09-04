from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any, Dict, Iterable, List

import h5py
import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "psychosis_cohort_anchor_20260520"
RAW_ROOT = REPO_ROOT / "data" / "raw"
RESULTS_ROOT = ARTICLE_DIR / "results"
FIGURES_ROOT = ARTICLE_DIR / "figures"

DATASETS = ("ds003944", "ds003947")
CONTRASTS = {
    "FEP_unmedicated_vs_Healthy": ("Healthy", "FEP unmedicated"),
    "FEP_medicated_vs_Healthy": ("Healthy", "FEP medicated"),
    "FEP_medicated_vs_FEP_unmedicated": ("FEP unmedicated", "FEP medicated"),
}

FEATURE_FAMILIES: Dict[str, tuple[str, ...]] = {
    "spectral": (
        "eeg_delta",
        "eeg_theta",
        "eeg_alpha",
        "eeg_beta",
        "eeg_alpha_theta",
        "eeg_beta_alpha",
    ),
    "complexity": (
        "eeg_hjorth_mobility",
        "eeg_hjorth_complexity",
        "eeg_permutation_entropy",
        "eeg_sample_entropy",
    ),
}
TRAJECTORY_BASELINES: tuple[str, ...] = (
    "speed_mean",
    "speed_median",
    "curvature_median",
    "path_length",
    "endpoint_dist",
    "traj_efficiency",
    "corner_entropy",
    "corner_transition_entropy",
)
FAMILY_LABELS = {
    "spectral": "Spectral EEG",
    "complexity": "Complexity",
    "simple_dynamics": "Simple dynamics",
}
METRIC_LABELS = {
    "eeg_delta_median": "delta power",
    "eeg_theta_median": "theta power",
    "eeg_alpha_median": "alpha power",
    "eeg_beta_median": "beta power",
    "eeg_alpha_theta_median": "alpha/theta",
    "eeg_beta_alpha_median": "beta/alpha",
    "eeg_hjorth_mobility_median": "Hjorth mobility",
    "eeg_hjorth_complexity_median": "Hjorth complexity",
    "eeg_permutation_entropy_median": "permutation entropy",
    "eeg_sample_entropy_median": "sample entropy",
    "speed_mean": "speed mean",
    "speed_median": "speed median",
    "curvature_median": "curvature median",
    "path_length": "path length",
    "endpoint_dist": "endpoint distance",
    "traj_efficiency": "trajectory efficiency",
    "corner_entropy": "corner entropy",
    "corner_transition_entropy": "corner transition entropy",
}


def _latest_parquet(dataset: str, stem: str) -> Path:
    matches = sorted(ANALYSIS_ROOT.glob(f"{dataset}_{stem}_*.parquet"))
    if not matches:
        raise FileNotFoundError(f"No {stem} parquet found for {dataset} under {ANALYSIS_ROOT}")
    return matches[-1]


def _resolve_local_h5_path(raw_path: Path) -> Path:
    if raw_path.exists():
        return raw_path
    parts = list(raw_path.parts)
    for idx, part in enumerate(parts):
        if str(part).startswith("neuralmanifolddynamics_"):
            candidate = RAW_ROOT.joinpath(*parts[idx:])
            if candidate.exists():
                return candidate
    matches = list(RAW_ROOT.glob(f"**/{raw_path.name}"))
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError(f"Could not resolve local H5 path for {raw_path}")


def _contiguous_segments(idx: np.ndarray) -> List[np.ndarray]:
    if idx.size == 0:
        return []
    values = np.unique(np.asarray(idx, dtype=int))
    breaks = np.where(np.diff(values) != 1)[0]
    starts = np.r_[0, breaks + 1]
    ends = np.r_[breaks + 1, values.size]
    return [values[start:end] for start, end in zip(starts, ends)]


def _segmentwise_speed(coords: np.ndarray, segments: List[np.ndarray]) -> np.ndarray:
    chunks: List[np.ndarray] = []
    for seg in segments:
        if seg.size < 2:
            continue
        diff = np.diff(coords[seg], axis=0)
        chunks.append(np.linalg.norm(diff, axis=1))
    return np.concatenate(chunks) if chunks else np.zeros((0,), dtype=float)


def _segmentwise_curvature(coords: np.ndarray, segments: List[np.ndarray]) -> np.ndarray:
    chunks: List[np.ndarray] = []
    for seg in segments:
        if seg.size < 3:
            continue
        window = coords[seg]
        v1 = np.diff(window, axis=0)[:-1]
        v2 = np.diff(window, axis=0)[1:]
        denom = np.linalg.norm(v1, axis=1) * np.linalg.norm(v2, axis=1) + 1e-12
        cosang = np.clip(np.sum(v1 * v2, axis=1) / denom, -1.0, 1.0)
        chunks.append(np.arccos(cosang))
    return np.concatenate(chunks) if chunks else np.zeros((0,), dtype=float)


def _segmentwise_path_length(coords: np.ndarray, segments: List[np.ndarray]) -> float:
    total = 0.0
    for seg in segments:
        if seg.size < 2:
            continue
        diff = np.diff(coords[seg], axis=0)
        total += float(np.nansum(np.linalg.norm(diff, axis=1)))
    return total


def _segmentwise_endpoint_dist(coords: np.ndarray, segments: List[np.ndarray]) -> float:
    total = 0.0
    for seg in segments:
        if seg.size < 2:
            continue
        endpoints = np.asarray(coords[seg[[0, -1]]], dtype=float)
        if endpoints.shape != (2, coords.shape[1]) or not np.isfinite(endpoints).all():
            continue
        total += float(np.linalg.norm(endpoints[1] - endpoints[0]))
    return total


def _trajectory_efficiency(endpoint_dist: float, path_length: float) -> float:
    if not np.isfinite(endpoint_dist) or not np.isfinite(path_length) or path_length <= 0:
        return float("nan")
    return float(np.clip(endpoint_dist / path_length, 0.0, 1.0))


def _corner_codes(coords: np.ndarray, thr_high: np.ndarray) -> np.ndarray:
    high = np.asarray(coords, dtype=float) >= np.asarray(thr_high, dtype=float)
    return (high[:, 0].astype(int) << 2) | (high[:, 1].astype(int) << 1) | high[:, 2].astype(int)


def _occupancy_entropy(codes: np.ndarray) -> float:
    counts = np.bincount(np.asarray(codes, dtype=int), minlength=8).astype(float)
    total = float(np.sum(counts))
    if total <= 0:
        return float("nan")
    probs = np.clip(counts / total, 1e-12, 1.0)
    probs = probs / probs.sum()
    return float(-np.sum(probs * np.log(probs)))


def _transition_entropy(codes: np.ndarray) -> float:
    if codes.size < 2:
        return float("nan")
    left = codes[:-1]
    right = codes[1:]
    valid = (left >= 0) & (left < 8) & (right >= 0) & (right < 8)
    if not np.any(valid):
        return float("nan")
    counts = np.zeros((8, 8), dtype=float)
    for src, dst in zip(left[valid].tolist(), right[valid].tolist()):
        counts[int(src), int(dst)] += 1.0
    total = float(np.sum(counts))
    if total <= 0:
        return float("nan")
    probs = np.clip(counts.reshape(-1) / total, 1e-12, 1.0)
    probs = probs / probs.sum()
    return float(-np.sum(probs * np.log(probs)))


def _resolve_coords_3d(handle: h5py.File) -> np.ndarray:
    for path in ("/coords_3d_cohort_anchored/values", "/coords_3d_subject_anchored/values", "/mnps_3d"):
        if path in handle:
            return np.asarray(handle[path][()], dtype=float)
    raise KeyError("No 3D coordinate dataset found in H5.")


def _trajectory_baselines_from_h5(h5_path: Path) -> Dict[str, float]:
    with h5py.File(h5_path, "r") as handle:
        coords = _resolve_coords_3d(handle)
    if coords.ndim != 2 or coords.shape[1] < 3:
        return {metric: float("nan") for metric in TRAJECTORY_BASELINES}
    coords = np.asarray(coords[:, :3], dtype=float)
    finite_mask = np.isfinite(coords).all(axis=1)
    finite_coords = coords[finite_mask]
    if finite_coords.shape[0] < 3:
        return {metric: float("nan") for metric in TRAJECTORY_BASELINES}
    sample_idx = np.flatnonzero(finite_mask)
    segments = _contiguous_segments(sample_idx)
    speed_values = _segmentwise_speed(coords, segments)
    curvature_values = _segmentwise_curvature(coords, segments)
    path_length = _segmentwise_path_length(coords, segments)
    endpoint_dist = _segmentwise_endpoint_dist(coords, segments)
    thr_high = np.nanpercentile(finite_coords, 60, axis=0).astype(float)
    corner_codes = _corner_codes(finite_coords, thr_high=thr_high)
    return {
        "speed_mean": float(np.mean(speed_values)) if speed_values.size else float("nan"),
        "speed_median": float(np.median(speed_values)) if speed_values.size else float("nan"),
        "curvature_median": float(np.median(curvature_values)) if curvature_values.size else float("nan"),
        "path_length": path_length,
        "endpoint_dist": endpoint_dist,
        "traj_efficiency": _trajectory_efficiency(endpoint_dist, path_length),
        "corner_entropy": _occupancy_entropy(corner_codes),
        "corner_transition_entropy": _transition_entropy(corner_codes),
    }


def _cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 2 or right.size < 2:
        return float("nan")
    left_var = left.var(ddof=1)
    right_var = right.var(ddof=1)
    pooled_var = ((left.size - 1) * left_var + (right.size - 1) * right_var) / (left.size + right.size - 2)
    if not np.isfinite(pooled_var) or pooled_var <= 0:
        return float("nan")
    return float((right.mean() - left.mean()) / np.sqrt(pooled_var))


def _bh_fdr(values: pd.Series) -> pd.Series:
    arr = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    valid = np.isfinite(arr)
    if not valid.any():
        return pd.Series(out, index=values.index)
    p = arr[valid]
    order = np.argsort(p)
    ranked = p[order]
    n = ranked.size
    adjusted = ranked * n / np.arange(1, n + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    restored = np.empty_like(adjusted)
    restored[order] = adjusted
    out[valid] = restored
    return pd.Series(out, index=values.index)


def _sig_tier(p_value: float | None, q_value: float | None) -> str:
    if q_value is not None and np.isfinite(q_value) and q_value <= 0.05:
        return "q<=0.05"
    if p_value is not None and np.isfinite(p_value) and p_value < 0.05:
        return "p<0.05"
    if p_value is not None and np.isfinite(p_value) and p_value < 0.1:
        return "p<0.1"
    return "ns"


def _sig_star(p_value: float | None, q_value: float | None) -> str:
    return {"q<=0.05": "q", "p<0.05": "*", "p<0.1": "~"}.get(_sig_tier(p_value, q_value), "")


def _sorted_results(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["abs_effect"] = out["effect_size"].abs()
    out["sig_rank"] = out.apply(
        lambda row: {"q<=0.05": 0, "p<0.05": 1, "p<0.1": 2, "ns": 3}[
            _sig_tier(
                float(row["p_value"]) if pd.notna(row["p_value"]) else None,
                float(row["q_value"]) if pd.notna(row["q_value"]) else None,
            )
        ],
        axis=1,
    )
    return out.sort_values(
        by=["sig_rank", "q_value", "p_value", "abs_effect", "metric"],
        ascending=[True, True, True, False, True],
        na_position="last",
    ).reset_index(drop=True)


def _median_feature_summary(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return float("nan")
    return float(np.median(finite))


def _subject_feature_frame(dataset: str, subject_metrics: pd.DataFrame) -> pd.DataFrame:
    subject_rows = (
        subject_metrics[
            ["subject_id", "group", "medication_group", "cpz_at_scan", "source_h5_path"]
        ]
        .dropna(subset=["subject_id", "source_h5_path"])
        .drop_duplicates(subset=["subject_id"])
        .copy()
    )
    rows: List[Dict[str, Any]] = []
    for row in subject_rows.itertuples(index=False):
        h5_path = _resolve_local_h5_path(Path(str(row.source_h5_path)))
        with h5py.File(h5_path, "r") as handle:
            names = [
                item.decode("utf-8") if isinstance(item, bytes) else str(item)
                for item in handle["features_raw"]["names"][()]
            ]
            values = np.asarray(handle["features_raw"]["values"][()], dtype=float)
        name_to_idx = {name: idx for idx, name in enumerate(names)}
        out: Dict[str, Any] = {
            "dataset": dataset,
            "subject_id": str(row.subject_id),
            "group": row.group,
            "medication_group": row.medication_group,
            "cpz_at_scan": row.cpz_at_scan,
        }
        for family_name, features in FEATURE_FAMILIES.items():
            for feature_name in features:
                if feature_name not in name_to_idx:
                    continue
                out[f"{feature_name}_median"] = _median_feature_summary(values[:, name_to_idx[feature_name]])
        rows.append(out)
    return pd.DataFrame(rows)


def _trajectory_frame(dataset: str, subject_metrics: pd.DataFrame) -> pd.DataFrame:
    subject_rows = (
        subject_metrics[["subject_id", "source_h5_path"]]
        .dropna(subset=["subject_id", "source_h5_path"])
        .drop_duplicates(subset=["subject_id"])
        .copy()
    )
    rows: List[Dict[str, Any]] = []
    for row in subject_rows.itertuples(index=False):
        metrics = _trajectory_baselines_from_h5(_resolve_local_h5_path(Path(str(row.source_h5_path))))
        metrics["dataset"] = dataset
        metrics["subject_id"] = str(row.subject_id)
        rows.append(metrics)
    return pd.DataFrame(rows)


def _combined_subject_baselines(dataset: str) -> pd.DataFrame:
    subject_metrics = pd.read_parquet(_latest_parquet(dataset, "subject_metrics"))
    feature_frame = _subject_feature_frame(dataset, subject_metrics)
    trajectory_frame = _trajectory_frame(dataset, subject_metrics)
    merged = feature_frame.merge(trajectory_frame, on=["dataset", "subject_id"], how="left")
    return merged


def _family_for_metric(metric: str) -> str:
    if metric in TRAJECTORY_BASELINES:
        return "simple_dynamics"
    if metric.startswith("eeg_") and ("entropy" in metric or "hjorth" in metric):
        return "complexity"
    return "spectral"


def _contrast_results(dataset: str, frame: pd.DataFrame) -> pd.DataFrame:
    metric_columns = [
        column
        for column in frame.columns
        if column.startswith("eeg_") and column.endswith("_median")
    ] + [metric for metric in TRAJECTORY_BASELINES if metric in frame.columns]
    rows: List[Dict[str, Any]] = []
    for contrast_name, (left_label, right_label) in CONTRASTS.items():
        sub = frame[frame["medication_group"].isin([left_label, right_label])].copy()
        for metric in metric_columns:
            left = pd.to_numeric(
                sub.loc[sub["medication_group"] == left_label, metric],
                errors="coerce",
            ).dropna()
            right = pd.to_numeric(
                sub.loc[sub["medication_group"] == right_label, metric],
                errors="coerce",
            ).dropna()
            if len(left) < 3 or len(right) < 3:
                continue
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                _, p_value = stats.ttest_ind(
                    left.to_numpy(),
                    right.to_numpy(),
                    equal_var=False,
                    nan_policy="omit",
                )
            rows.append(
                {
                    "dataset": dataset,
                    "contrast_name": contrast_name,
                    "family": _family_for_metric(metric),
                    "metric": metric,
                    "metric_label": METRIC_LABELS.get(metric, metric),
                    "left_group": left_label,
                    "right_group": right_label,
                    "left_n": int(len(left)),
                    "right_n": int(len(right)),
                    "left_mean": float(left.mean()),
                    "right_mean": float(right.mean()),
                    "effect_estimate": float(right.mean() - left.mean()),
                    "effect_size": _cohens_d(left.to_numpy(), right.to_numpy()),
                    "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
                }
            )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["q_value"] = result.groupby(["dataset", "contrast_name", "family"], dropna=False)["p_value"].transform(_bh_fdr)
    result["sig_tier"] = result.apply(
        lambda row: _sig_tier(
            float(row["p_value"]) if pd.notna(row["p_value"]) else None,
            float(row["q_value"]) if pd.notna(row["q_value"]) else None,
        ),
        axis=1,
    )
    return result


def _summary_rows(detail: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for (dataset, contrast_name, family), sub in detail.groupby(["dataset", "contrast_name", "family"], dropna=False):
        selected = _sorted_results(sub).iloc[0]
        rows.append(
            {
                "dataset": dataset,
                "contrast_name": contrast_name,
                "family": family,
                "family_label": FAMILY_LABELS.get(str(family), str(family)),
                "metric": selected["metric"],
                "metric_label": selected["metric_label"],
                "effect_size": selected["effect_size"],
                "effect_estimate": selected["effect_estimate"],
                "p_value": selected["p_value"],
                "q_value": selected["q_value"],
                "left_group": selected["left_group"],
                "right_group": selected["right_group"],
                "left_n": selected["left_n"],
                "right_n": selected["right_n"],
                "sig_tier": selected["sig_tier"],
            }
        )
    return pd.DataFrame(rows)


def _cpz_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for dataset, sub in frame.groupby("dataset", dropna=False):
        fep = sub[sub["medication_group"].isin(["FEP unmedicated", "FEP medicated"])].copy()
        for group_label, group_frame in fep.groupby("medication_group", dropna=False):
            cpz = pd.to_numeric(group_frame["cpz_at_scan"], errors="coerce").dropna()
            rows.append(
                {
                    "dataset": dataset,
                    "medication_group": group_label,
                    "n_subjects": int(group_frame["subject_id"].nunique()),
                    "cpz_nonmissing_n": int(cpz.size),
                    "cpz_mean": float(cpz.mean()) if cpz.size else np.nan,
                    "cpz_median": float(cpz.median()) if cpz.size else np.nan,
                }
            )
    return pd.DataFrame(rows)


def _draw_comparator_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    families = ["spectral", "complexity", "simple_dynamics"]
    row_labels: List[str] = []
    values: List[List[float]] = []
    annotations: List[List[str]] = []
    for dataset in DATASETS:
        dataset_frame = summary[summary["dataset"] == dataset].copy()
        for contrast_name in CONTRASTS:
            row_labels.append(f"{dataset}\n{contrast_name.replace('_', ' ')}")
            row_values: List[float] = []
            row_annotations: List[str] = []
            for family in families:
                match = dataset_frame[
                    (dataset_frame["contrast_name"] == contrast_name) & (dataset_frame["family"] == family)
                ]
                if match.empty:
                    row_values.append(np.nan)
                    row_annotations.append("")
                    continue
                row = match.iloc[0]
                p_value = float(row["p_value"]) if pd.notna(row["p_value"]) else None
                q_value = float(row["q_value"]) if pd.notna(row["q_value"]) else None
                row_values.append(float(row["effect_size"]))
                row_annotations.append(f"{row['metric_label']}\n{_sig_star(p_value, q_value)}")
            values.append(row_values)
            annotations.append(row_annotations)

    matrix = np.asarray(values, dtype=float)
    vmax = np.nanmax(np.abs(matrix)) if np.isfinite(matrix).any() else 1.0
    fig, ax = plt.subplots(figsize=(10.5, 7.5))
    im = ax.imshow(matrix, cmap="coolwarm", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(families)))
    ax.set_xticklabels([FAMILY_LABELS[family] for family in families], rotation=20, ha="right")
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    ax.set_title("Best simple baseline signals by family")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if np.isfinite(matrix[i, j]):
                ax.text(j, i, annotations[i][j], ha="center", va="center", fontsize=8)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Effect size (Cohen's d)")
    fig.tight_layout()
    fig.savefig(output_path, format="svg")
    plt.close(fig)


def main() -> None:
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    FIGURES_ROOT.mkdir(parents=True, exist_ok=True)

    subject_frames: List[pd.DataFrame] = []
    detail_frames: List[pd.DataFrame] = []
    for dataset in DATASETS:
        combined = _combined_subject_baselines(dataset)
        subject_frames.append(combined)
        detail = _contrast_results(dataset, combined)
        detail_frames.append(detail)

    subject_frame = pd.concat(subject_frames, ignore_index=True)
    detail_frame = pd.concat(detail_frames, ignore_index=True)
    summary_frame = _summary_rows(detail_frame)
    cpz_frame = _cpz_summary(subject_frame)

    detail_csv = RESULTS_ROOT / "psychosis_baseline_comparator_detail.csv"
    summary_csv = RESULTS_ROOT / "psychosis_baseline_comparator_summary.csv"
    cpz_csv = RESULTS_ROOT / "psychosis_baseline_cpz_summary.csv"
    detail_frame.to_csv(detail_csv, index=False)
    summary_frame.to_csv(summary_csv, index=False)
    cpz_frame.to_csv(cpz_csv, index=False)

    figure_path = FIGURES_ROOT / "psychosis_baseline_comparators.svg"
    _draw_comparator_heatmap(summary_frame, figure_path)

    manifest = {
        "source_subject_metrics": {
            dataset: str(_latest_parquet(dataset, "subject_metrics")) for dataset in DATASETS
        },
        "detail_csv": str(detail_csv),
        "summary_csv": str(summary_csv),
        "cpz_summary_csv": str(cpz_csv),
        "figure_svg": str(figure_path),
        "feature_families": {key: list(value) for key, value in FEATURE_FAMILIES.items()},
        "trajectory_baselines": list(TRAJECTORY_BASELINES),
    }
    (RESULTS_ROOT / "baseline_comparator_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
