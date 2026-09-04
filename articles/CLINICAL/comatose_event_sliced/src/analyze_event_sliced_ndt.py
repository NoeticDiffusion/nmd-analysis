from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
RESULT_STAMP = "20260607"
WINDOW_SEC_FALLBACK = 4.0
DEFAULT_RANDOM_STATE = 20260604
DEFAULT_N_SPLITS = 5
DEFAULT_N_REPEATS = 20
DEFAULT_GOOD_CPC = 1
DEFAULT_POOR_CPC = 5
DEFAULT_EVENT_THRESHOLD = 3.0
DEFAULT_ETA = 0.5
DEFAULT_SUPPORT_Z = 1.5
DEFAULT_MIN_REGIONAL_SUPPORT = 2
DEFAULT_MERGE_GAP = 1
DEFAULT_PRE_WINDOWS = 4
DEFAULT_POST_WINDOWS = 6
DEFAULT_MIN_EPISODE_WINDOWS = 1
DEFAULT_MIN_ALIGNED_WINDOWS = 80
SUPPORT_REGIONS = ("frontal", "central", "parietal_occipital", "temporal")
DEFAULT_PROCESSED_ROOTS = (
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260605_202236",
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260605_210700",
)
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / f"event_sliced_ndt_lpr_{RESULT_STAMP}_cpc15"
PROFILE_COLUMNS = (
    "episode_rate_per_min",
    "median_amp",
    "median_recovery_half_time_min",
    "median_peak_spec",
    "frac_recovered",
)
SINGLE_FEATURE_COLUMNS = (
    "run_median_spec",
    "run_median_spec_9d",
    *PROFILE_COLUMNS,
    "median_residual",
)


@dataclass(frozen=True)
class Config:
    processed_roots: tuple[Path, ...]
    output_dir: Path
    good_cpc: int
    poor_cpc: int
    event_threshold: float
    eta: float
    regional_support_z: float
    min_regional_support: int
    merge_gap: int
    pre_windows: int
    post_windows: int
    min_episode_windows: int
    min_aligned_windows: int
    max_subjects_per_class: int | None
    max_runs_per_subject: int | None
    n_splits: int
    n_repeats: int
    random_state: int


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Run event-sliced latent perturbation reactivity analysis for coma NDT exports."
    )
    parser.add_argument(
        "--processed-root",
        dest="processed_roots",
        action="append",
        type=Path,
        help="Processed H5 root. Pass multiple times to combine cohorts.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--good-cpc", type=int, default=DEFAULT_GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=DEFAULT_POOR_CPC)
    parser.add_argument("--event-threshold", type=float, default=DEFAULT_EVENT_THRESHOLD)
    parser.add_argument("--eta", type=float, default=DEFAULT_ETA)
    parser.add_argument("--regional-support-z", type=float, default=DEFAULT_SUPPORT_Z)
    parser.add_argument("--min-regional-support", type=int, default=DEFAULT_MIN_REGIONAL_SUPPORT)
    parser.add_argument("--merge-gap", type=int, default=DEFAULT_MERGE_GAP)
    parser.add_argument("--pre-windows", type=int, default=DEFAULT_PRE_WINDOWS)
    parser.add_argument("--post-windows", type=int, default=DEFAULT_POST_WINDOWS)
    parser.add_argument("--min-episode-windows", type=int, default=DEFAULT_MIN_EPISODE_WINDOWS)
    parser.add_argument("--min-aligned-windows", type=int, default=DEFAULT_MIN_ALIGNED_WINDOWS)
    parser.add_argument("--max-subjects-per-class", type=int, default=None)
    parser.add_argument("--max-runs-per-subject", type=int, default=None)
    parser.add_argument("--n-splits", type=int, default=DEFAULT_N_SPLITS)
    parser.add_argument("--n-repeats", type=int, default=DEFAULT_N_REPEATS)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    args = parser.parse_args()
    processed_roots = tuple(args.processed_roots) if args.processed_roots else DEFAULT_PROCESSED_ROOTS
    return Config(
        processed_roots=processed_roots,
        output_dir=args.output_dir,
        good_cpc=args.good_cpc,
        poor_cpc=args.poor_cpc,
        event_threshold=args.event_threshold,
        eta=args.eta,
        regional_support_z=args.regional_support_z,
        min_regional_support=args.min_regional_support,
        merge_gap=args.merge_gap,
        pre_windows=args.pre_windows,
        post_windows=args.post_windows,
        min_episode_windows=args.min_episode_windows,
        min_aligned_windows=args.min_aligned_windows,
        max_subjects_per_class=args.max_subjects_per_class,
        max_runs_per_subject=args.max_runs_per_subject,
        n_splits=args.n_splits,
        n_repeats=args.n_repeats,
        random_state=args.random_state,
    )


def infer_source_cohort(root: Path) -> str:
    name = root.name.lower()
    if "part1" in name or "202236" in name:
        return "part1"
    if "part2" in name or "210700" in name:
        return "part2"
    return root.name


def robust_scale_params(values: np.ndarray | pd.Series) -> tuple[float, float]:
    arr = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(dtype=float)
    if arr.size == 0:
        return 0.0, 1.0
    center = float(np.median(arr))
    mad = float(np.median(np.abs(arr - center)))
    scale = 1.4826 * mad
    if not np.isfinite(scale) or scale <= 1e-12:
        q75, q25 = np.quantile(arr, [0.75, 0.25])
        scale = float((q75 - q25) / 1.349)
    if not np.isfinite(scale) or scale <= 1e-12:
        scale = float(np.std(arr, ddof=1)) if arr.size > 1 else 1.0
    if not np.isfinite(scale) or scale <= 1e-12:
        scale = 1.0
    return center, scale


def robust_z(values: np.ndarray | pd.Series) -> np.ndarray:
    arr = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy(dtype=float)
    center, scale = robust_scale_params(arr)
    out = (arr - center) / scale
    out[~np.isfinite(arr)] = np.nan
    return out


def compute_window_sec(time_values: np.ndarray) -> float:
    arr = np.asarray(time_values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size < 2:
        return WINDOW_SEC_FALLBACK
    diffs = np.diff(arr)
    diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
    if diffs.size == 0:
        return WINDOW_SEC_FALLBACK
    return float(np.median(diffs))


def spectral_radius_sequence(jacobian: np.ndarray) -> np.ndarray:
    jacobian = np.asarray(jacobian, dtype=float)
    out = np.full(jacobian.shape[0], np.nan, dtype=float)
    for idx, matrix in enumerate(jacobian):
        if not np.isfinite(matrix).all():
            continue
        try:
            out[idx] = float(np.max(np.abs(np.linalg.eigvals(matrix))))
        except np.linalg.LinAlgError:
            continue
    return out


def safe_nanmedian(values: list[float] | np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan")
    return float(np.median(arr))


def safe_nanmax(values: list[float] | np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan")
    return float(np.max(arr))


def safe_nanpercentile(values: list[float] | np.ndarray, q: float) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan")
    return float(np.percentile(arr, q))


def cluster_boolean_events(mask: np.ndarray, merge_gap: int, min_episode_windows: int) -> list[tuple[int, int]]:
    event_idx = np.flatnonzero(mask)
    if event_idx.size == 0:
        return []
    episodes: list[tuple[int, int]] = []
    start = int(event_idx[0])
    prev = int(event_idx[0])
    for idx in event_idx[1:]:
        idx = int(idx)
        if idx - prev <= merge_gap + 1:
            prev = idx
            continue
        if prev - start + 1 >= min_episode_windows:
            episodes.append((start, prev))
        start = idx
        prev = idx
    if prev - start + 1 >= min_episode_windows:
        episodes.append((start, prev))
    return episodes


def make_classifier(random_state: int) -> Pipeline:
    return Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "logreg",
                LogisticRegression(
                    solver="liblinear",
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=random_state,
                ),
            ),
        ]
    )


def calibration_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    if len(np.unique(y_true)) < 2:
        return {"calibration_slope": float("nan"), "calibration_intercept": float("nan")}
    clipped = np.clip(y_prob, 1e-6, 1.0 - 1e-6)
    x = np.log(clipped / (1.0 - clipped)).reshape(-1, 1)
    model = LogisticRegression(solver="lbfgs", C=1e6, max_iter=2000)
    model.fit(x, y_true)
    return {
        "calibration_slope": float(model.coef_[0][0]),
        "calibration_intercept": float(model.intercept_[0]),
    }


def threshold_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=int)
    y_hat = (np.asarray(y_prob, dtype=float) >= threshold).astype(int)
    tp = int(np.sum((y_true == 1) & (y_hat == 1)))
    tn = int(np.sum((y_true == 0) & (y_hat == 0)))
    fp = int(np.sum((y_true == 0) & (y_hat == 1)))
    fn = int(np.sum((y_true == 1) & (y_hat == 0)))
    sensitivity = tp / (tp + fn) if (tp + fn) else float("nan")
    specificity = tn / (tn + fp) if (tn + fp) else float("nan")
    return {
        "prob_threshold": float(threshold),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
    }


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    out = {
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "average_precision": float(average_precision_score(y_true, y_prob)),
        "brier_score": float(brier_score_loss(y_true, y_prob)),
    }
    out.update(calibration_metrics(y_true, y_prob))
    out.update(threshold_metrics(y_true, y_prob))
    return out


def resolve_split_count(y: np.ndarray, requested_splits: int) -> int:
    class_counts = pd.Series(y).value_counts().to_dict()
    if len(class_counts) < 2:
        raise ValueError("Event-sliced analysis requires both CPC groups in the filtered cohort.")
    max_splits = int(min(class_counts.values()))
    if max_splits < 2:
        raise ValueError("Event-sliced analysis needs at least two subjects in each outcome group.")
    return min(requested_splits, max_splits)


def collect_run_index(config: Config) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    subject_counts: dict[int, int] = {config.good_cpc: 0, config.poor_cpc: 0}
    selected_subjects: set[str] = set()
    runs_per_subject: dict[str, int] = {}
    for root in config.processed_roots:
        cohort = infer_source_cohort(root)
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.h5")):
            try:
                with h5py.File(path, "r") as handle:
                    subject = str(handle.attrs.get("subject_id", "")).strip()
                    cpc = int(handle.attrs.get("meta_cpc", -1))
            except Exception:
                continue
            if cpc not in (config.good_cpc, config.poor_cpc) or not subject:
                continue
            pooled_subject = f"{cohort}::{subject}"
            if pooled_subject not in selected_subjects:
                max_subjects = config.max_subjects_per_class
                if max_subjects is not None and subject_counts[cpc] >= max_subjects:
                    continue
                selected_subjects.add(pooled_subject)
                subject_counts[cpc] += 1
                runs_per_subject[pooled_subject] = 0
            max_runs = config.max_runs_per_subject
            if max_runs is not None and runs_per_subject[pooled_subject] >= max_runs:
                continue
            runs_per_subject[pooled_subject] += 1
            rows.append(
                {
                    "source_cohort": cohort,
                    "processed_root": str(root),
                    "pooled_subject": pooled_subject,
                    "subject": subject,
                    "cpc": cpc,
                    "h5_path": str(path),
                }
            )
    return pd.DataFrame(rows)


def extract_run_features(row: pd.Series, config: Config) -> dict[str, Any] | None:
    path = Path(str(row["h5_path"]))
    try:
        with h5py.File(path, "r") as handle:
            mnps = handle["/mnps_3d"][:]
            raw_features = handle["/features_raw/values"][:]
            jacobian = handle["/jacobian/J_hat"][:]
            time_values = handle["/time"][:] if "/time" in handle else np.array([], dtype=float)
            # 9D Jacobian (optional — absent in ~34% of subjects)
            jacobian_9d: np.ndarray | None = None
            for jac9_path in ("/jacobian_9D_subject_anchored/J_hat", "/jacobian_9D/J_hat"):
                if jac9_path in handle:
                    arr = np.asarray(handle[jac9_path][:], dtype=float)
                    if arr.ndim == 3 and arr.shape[1] == 9:
                        jacobian_9d = arr
                    break
            regional_speeds: dict[str, np.ndarray] = {}
            if "regional_mnps" in handle:
                for region in SUPPORT_REGIONS:
                    region_group = handle["regional_mnps"].get(region)
                    if region_group is not None and "mnps_dot" in region_group:
                        regional_speeds[region] = np.linalg.norm(region_group["mnps_dot"][:], axis=1)
    except (KeyError, OSError, ValueError):
        return None

    mnps = np.asarray(mnps, dtype=float)
    raw_features = np.asarray(raw_features, dtype=float)
    d_mnps = np.linalg.norm(np.diff(mnps, axis=0), axis=1)
    log_raw_delta = np.linalg.norm(np.diff(np.log(np.abs(raw_features) + 1e-6), axis=0), axis=1)
    spec_radius = spectral_radius_sequence(jacobian)
    spec_aligned = spec_radius[: min(len(spec_radius), len(mnps))]
    spec_delta = np.abs(np.diff(spec_aligned))
    aligned_lengths = [len(d_mnps), len(log_raw_delta), len(spec_delta)]
    n_aligned = int(min(aligned_lengths)) if aligned_lengths else 0
    if n_aligned < config.min_aligned_windows:
        return None

    aligned_state = mnps
    aligned_speed = d_mnps[:n_aligned]
    aligned_raw_delta = log_raw_delta[:n_aligned]
    aligned_spec_radius = spec_aligned[: min(len(spec_aligned), len(aligned_state))]
    aligned_spec_delta = spec_delta[:n_aligned]
    window_sec = compute_window_sec(time_values)
    duration_min = (len(aligned_state) * window_sec) / 60.0

    event_score = robust_z(aligned_speed) + robust_z(aligned_raw_delta) + config.eta * robust_z(aligned_spec_delta)
    support_counts = np.full(n_aligned, int(config.min_regional_support), dtype=int)
    if regional_speeds:
        regional_columns = []
        for region in SUPPORT_REGIONS:
            region_speed = regional_speeds.get(region)
            if region_speed is None or len(region_speed) <= n_aligned:
                continue
            regional_columns.append(robust_z(np.diff(region_speed))[:n_aligned])
        if regional_columns:
            regional_matrix = np.column_stack(regional_columns)
            support_counts = np.sum(
                np.isfinite(regional_matrix) & (regional_matrix > config.regional_support_z),
                axis=1,
                dtype=int,
            )
    support_mask = support_counts >= int(config.min_regional_support)

    event_mask = np.isfinite(event_score) & (event_score > config.event_threshold) & support_mask
    episodes = cluster_boolean_events(event_mask, config.merge_gap, config.min_episode_windows)

    amplitudes: list[float] = []
    recoveries_min: list[float] = []
    residuals: list[float] = []
    fractions_recovered: list[float] = []
    peak_specs: list[float] = []
    peak_scores: list[float] = []

    for start, end in episodes:
        pre_start = max(0, start - config.pre_windows)
        baseline_slice = aligned_state[pre_start:start]
        post_slice = aligned_state[end + 1 : min(len(aligned_state), end + 1 + config.post_windows)]
        if baseline_slice.size == 0 or post_slice.size == 0:
            continue
        baseline = np.nanmedian(baseline_slice, axis=0)
        post = np.nanmedian(post_slice, axis=0)
        episode_states = aligned_state[start : end + 1]
        deviations = np.linalg.norm(episode_states - baseline, axis=1)
        if deviations.size == 0 or not np.isfinite(deviations).any():
            continue
        peak_amp = float(np.nanmax(deviations))
        if not np.isfinite(peak_amp):
            continue
        peak_scores.append(float(np.nanmax(event_score[start : end + 1])))
        peak_specs.append(float(np.nanmax(aligned_spec_radius[start : end + 1])))
        amplitudes.append(peak_amp)
        residual = float(np.linalg.norm(post - baseline))
        residuals.append(residual)
        if peak_amp > 1e-12 and np.isfinite(residual):
            fractions_recovered.append(float(np.clip(1.0 - residual / peak_amp, 0.0, 1.0)))
        else:
            fractions_recovered.append(float("nan"))
        post_dev = np.linalg.norm(aligned_state[end + 1 :] - baseline, axis=1)
        if peak_amp <= 1e-12 or post_dev.size == 0:
            recoveries_min.append(float("nan"))
        else:
            threshold = 0.5 * peak_amp
            recovered = np.flatnonzero(post_dev <= threshold)
            if recovered.size == 0:
                recoveries_min.append(float("nan"))
            else:
                recovery_windows = int(recovered[0]) + 1
                recoveries_min.append(float(recovery_windows * window_sec / 60.0))

    return {
        "source_cohort": row["source_cohort"],
        "processed_root": row["processed_root"],
        "pooled_subject": row["pooled_subject"],
        "subject": row["subject"],
        "cpc": int(row["cpc"]),
        "label": int(int(row["cpc"]) == config.poor_cpc),
        "label_name": f"CPC{int(row['cpc'])}",
        "h5_path": str(path),
        "n_aligned_windows": n_aligned,
        "window_sec": window_sec,
        "duration_min": duration_min,
        "n_episodes": int(len(amplitudes)),
        "event_window_fraction": float(np.mean(event_mask)) if event_mask.size else float("nan"),
        "event_score_p95": safe_nanpercentile(event_score, 95),
        "event_score_peak": safe_nanmax(event_score),
        "run_median_spec": safe_nanmedian(aligned_spec_radius),
        "run_median_spec_9d": safe_nanmedian(spectral_radius_sequence(jacobian_9d)) if jacobian_9d is not None else float("nan"),
        "episode_rate_per_min": float(len(amplitudes) / duration_min) if duration_min > 0 else float("nan"),
        "median_amp": safe_nanmedian(amplitudes),
        "median_recovery_half_time_min": safe_nanmedian(recoveries_min),
        "median_residual": safe_nanmedian(residuals),
        "frac_recovered": safe_nanmedian(fractions_recovered),
        "median_peak_spec": safe_nanmedian(peak_specs),
        "median_peak_score": safe_nanmedian(peak_scores),
    }


def build_run_feature_matrix(config: Config) -> pd.DataFrame:
    run_index = collect_run_index(config)
    rows: list[dict[str, Any]] = []
    for _, row in run_index.iterrows():
        features = extract_run_features(row, config)
        if features is not None:
            rows.append(features)
    return pd.DataFrame(rows)


def build_subject_feature_matrix(run_features: pd.DataFrame) -> pd.DataFrame:
    if run_features.empty:
        return pd.DataFrame()
    numeric_columns = [
        column
        for column in run_features.columns
        if column
        not in {
            "source_cohort",
            "processed_root",
            "pooled_subject",
            "subject",
            "label_name",
            "h5_path",
        }
    ]
    aggregation = {column: "median" for column in numeric_columns}
    aggregation.update(
        {
            "source_cohort": "first",
            "processed_root": "first",
            "subject": "first",
            "label_name": "first",
            "h5_path": "first",
        }
    )
    subject_features = run_features.groupby("pooled_subject", as_index=False).agg(aggregation)
    subject_features["n_runs"] = run_features.groupby("pooled_subject")["h5_path"].count().reindex(
        subject_features["pooled_subject"]
    ).to_numpy(dtype=int)
    subject_features["n_episodes_total"] = run_features.groupby("pooled_subject")["n_episodes"].sum().reindex(
        subject_features["pooled_subject"]
    ).to_numpy(dtype=float)
    return subject_features


def cohens_d(group_a: np.ndarray, group_b: np.ndarray) -> float:
    a = np.asarray(group_a, dtype=float)
    b = np.asarray(group_b, dtype=float)
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if a.size < 2 or b.size < 2:
        return float("nan")
    pooled = ((a.size - 1) * np.var(a, ddof=1) + (b.size - 1) * np.var(b, ddof=1)) / (a.size + b.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(a) - np.mean(b)) / np.sqrt(pooled))


def summarize_single_features(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if frame.empty:
        return pd.DataFrame()
    y = frame["label"].astype(int).to_numpy()
    for column in SINGLE_FEATURE_COLUMNS:
        if column not in frame.columns:
            continue
        values = pd.to_numeric(frame[column], errors="coerce")
        mask = np.isfinite(values.to_numpy(dtype=float))
        if int(mask.sum()) < 4 or len(np.unique(y[mask])) < 2:
            continue
        raw_auc = float(roc_auc_score(y[mask], values.to_numpy(dtype=float)[mask]))
        oriented_auc = float(max(raw_auc, 1.0 - raw_auc))
        direction = "higher_in_CPC5" if raw_auc >= 0.5 else "higher_in_CPC1"
        poor = values[frame["label"] == 1].dropna().to_numpy(dtype=float)
        good = values[frame["label"] == 0].dropna().to_numpy(dtype=float)
        rho = stats.spearmanr(frame["run_median_spec"], values, nan_policy="omit")
        rows.append(
            {
                "metric": column,
                "n_subjects": int(mask.sum()),
                "auc_oriented": oriented_auc,
                "auc_raw_cpc5_high": raw_auc,
                "direction": direction,
                "cpc1_median": float(np.nanmedian(good)) if good.size else float("nan"),
                "cpc5_median": float(np.nanmedian(poor)) if poor.size else float("nan"),
                "cohens_d_cpc5_minus_cpc1": cohens_d(poor, good),
                "spearman_rho_vs_run_median_spec": float(rho.statistic) if hasattr(rho, "statistic") else float(rho[0]),
                "spearman_p_vs_run_median_spec": float(rho.pvalue) if hasattr(rho, "pvalue") else float(rho[1]),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("auc_oriented", ascending=False).reset_index(drop=True)


def active_feature_sets(frame: pd.DataFrame) -> dict[str, list[str]]:
    feature_sets = {
        "run_median_spec_only": ["run_median_spec"],
        "lpr_profile_only": list(PROFILE_COLUMNS),
        "run_median_spec_plus_lpr_profile": ["run_median_spec", *PROFILE_COLUMNS],
    }
    active: dict[str, list[str]] = {}
    for name, columns in feature_sets.items():
        used = [
            column
            for column in columns
            if column in frame.columns and pd.to_numeric(frame[column], errors="coerce").notna().sum() > 0
        ]
        if used:
            active[name] = used
    return active


def evaluate_repeated_cv(frame: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    if frame.empty:
        return pd.DataFrame(), pd.DataFrame()
    y = frame["label"].astype(int).to_numpy()
    n_splits = resolve_split_count(y, config.n_splits)
    folds = RepeatedStratifiedKFold(
        n_splits=n_splits,
        n_repeats=config.n_repeats,
        random_state=config.random_state,
    )
    feature_sets = active_feature_sets(frame)
    fold_rows: list[dict[str, Any]] = []
    coef_rows: list[dict[str, Any]] = []
    for fold_idx, (train_idx, test_idx) in enumerate(folds.split(frame, y)):
        for model_name, columns in feature_sets.items():
            model = make_classifier(config.random_state)
            x_train = frame.iloc[train_idx][columns]
            x_test = frame.iloc[test_idx][columns]
            model.fit(x_train, y[train_idx])
            y_prob = model.predict_proba(x_test)[:, 1]
            fold_rows.append(
                {
                    "evaluation": "repeated_stratified_cv",
                    "fold": int(fold_idx),
                    "model": model_name,
                    "n_train": int(len(train_idx)),
                    "n_test": int(len(test_idx)),
                    "n_features": int(len(columns)),
                    **compute_metrics(y[test_idx], y_prob),
                }
            )
            coefficients = model.named_steps["logreg"].coef_[0]
            for feature_name, coef in zip(columns, coefficients):
                coef_rows.append(
                    {
                        "evaluation": "repeated_stratified_cv",
                        "fold": int(fold_idx),
                        "model": model_name,
                        "feature": feature_name,
                        "coef": float(coef),
                        "abs_coef": float(abs(coef)),
                    }
                )
    return pd.DataFrame(fold_rows), pd.DataFrame(coef_rows)


def summarize_scores(scores: pd.DataFrame) -> pd.DataFrame:
    if scores.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for (evaluation, model_name), group in scores.groupby(["evaluation", "model"], sort=False):
        row: dict[str, Any] = {
            "evaluation": evaluation,
            "model": model_name,
            "n_folds": int(len(group)),
            "n_features_median": int(group["n_features"].median()),
        }
        for metric in ("roc_auc", "average_precision", "brier_score", "calibration_slope", "sensitivity", "specificity"):
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values)) if values.size else float("nan")
            row[f"{metric}_sd"] = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_coefficients(coefficients: pd.DataFrame) -> pd.DataFrame:
    if coefficients.empty:
        return pd.DataFrame()
    return (
        coefficients.groupby(["evaluation", "model", "feature"], as_index=False)
        .agg(mean_abs_coef=("abs_coef", "mean"), mean_coef=("coef", "mean"), sd_coef=("coef", "std"))
        .sort_values(["evaluation", "model", "mean_abs_coef"], ascending=[True, True, False])
    )


def count_table(frame: pd.DataFrame) -> str:
    counts = frame.groupby("label_name")["pooled_subject"].nunique().to_dict()
    columns = sorted(counts)
    header = "| label | n_subjects |"
    sep = "|---|---:|"
    rows = [header, sep]
    for column in columns:
        rows.append(f"| {column} | {int(counts[column])} |")
    return "\n".join(rows)


def format_feature_row(row: pd.Series) -> str:
    return (
        f"- `{row['metric']}`: AUC `{row['auc_oriented']:.3f}` ({row['direction']}), "
        f"CPC1 median `{row['cpc1_median']:.3g}`, CPC5 median `{row['cpc5_median']:.3g}`, "
        f"Spearman rho vs `run_median_spec` `{row['spearman_rho_vs_run_median_spec']:+.3f}`"
    )


def format_cv_row(row: pd.Series) -> str:
    return (
        f"- `{row['model']}`: AUROC `{row['roc_auc_mean']:.3f} +/- {row['roc_auc_sd']:.3f}`, "
        f"AUPRC `{row['average_precision_mean']:.3f} +/- {row['average_precision_sd']:.3f}`, "
        f"Brier `{row['brier_score_mean']:.3f} +/- {row['brier_score_sd']:.3f}`"
    )


def write_summary(
    run_features: pd.DataFrame,
    subject_features: pd.DataFrame,
    single_feature_summary: pd.DataFrame,
    cv_summary: pd.DataFrame,
    config: Config,
) -> str:
    lines = [
        "# Event-Sliced NDT / Latent Perturbation Reactivity",
        "",
        "## Cohort",
        "",
        f"- processed roots: `{len(config.processed_roots)}`",
        f"- runs analyzed: `{len(run_features)}`",
        f"- subjects analyzed: `{subject_features['pooled_subject'].nunique() if not subject_features.empty else 0}`",
        f"- detector threshold: `E_t > {config.event_threshold:g}`",
        f"- Jacobian weight eta: `{config.eta:g}`",
        f"- regional support: `>= {config.min_regional_support}` of `{', '.join(SUPPORT_REGIONS)}` above robust-z `{config.regional_support_z:g}`",
        f"- episode merge gap: `<= {config.merge_gap}` window(s)",
        f"- minimum aligned windows per run: `{config.min_aligned_windows}`",
        "",
        count_table(subject_features) if not subject_features.empty else "_No subject features were generated._",
        "",
        "## Detector",
        "",
        "```text",
        "E_t = robz(||d mnps_3d||) + robz(||d log(abs(features_raw) + eps)||)",
        f"    + {config.eta:g} * robz(|d spectral_radius(J)|)",
        "episodes = supra-threshold windows clustered with short-gap merging",
        "run features = rate/min, median amplitude, recovery half-time, residual,",
        "               fraction recovered, and peak Jacobian spectral radius",
        "subject features = median over runs",
        "```",
        "",
        "## Single Features",
        "",
    ]
    if single_feature_summary.empty:
        lines.append("_No single-feature summary available._")
    else:
        for _, row in single_feature_summary.head(8).iterrows():
            lines.append(format_feature_row(row))
    lines.extend(["", "## Repeated CV", ""])
    if cv_summary.empty:
        lines.append("_No repeated-CV summary available._")
    else:
        for _, row in cv_summary.iterrows():
            lines.append(format_cv_row(row))
    lines.extend(
        [
            "",
            "## Interpretation Guardrail",
            "",
            "This output is exploratory and implementation-facing. It tests whether event-sliced latent perturbation reactivity carries outcome signal beyond a run-level median Jacobian metric, but it is not yet a frozen confirmatory specification.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)

    run_features = build_run_feature_matrix(config)
    subject_features = build_subject_feature_matrix(run_features)
    single_feature_summary = summarize_single_features(subject_features)
    cv_scores, coefficients = evaluate_repeated_cv(subject_features, config)
    cv_summary = summarize_scores(cv_scores)
    coefficient_summary = summarize_coefficients(coefficients)

    if not run_features.empty:
        run_features.to_csv(config.output_dir / "event_sliced_run_features.csv", index=False)
    if not subject_features.empty:
        subject_features.to_csv(config.output_dir / "event_sliced_subject_features.csv", index=False)
    if not single_feature_summary.empty:
        single_feature_summary.to_csv(config.output_dir / "event_sliced_single_feature_summary.csv", index=False)
    if not cv_scores.empty:
        cv_scores.to_csv(config.output_dir / "event_sliced_repeated_cv_fold_scores.csv", index=False)
    if not cv_summary.empty:
        cv_summary.to_csv(config.output_dir / "event_sliced_repeated_cv_summary.csv", index=False)
    if not coefficients.empty:
        coefficients.to_csv(config.output_dir / "event_sliced_model_coefficients.csv", index=False)
    if not coefficient_summary.empty:
        coefficient_summary.to_csv(config.output_dir / "event_sliced_model_coefficient_summary.csv", index=False)

    summary_text = write_summary(run_features, subject_features, single_feature_summary, cv_summary, config)
    (config.output_dir / "event_sliced_summary.md").write_text(summary_text, encoding="utf-8")
    (config.output_dir / "event_sliced_manifest.json").write_text(
        json.dumps(
            {
                "processed_roots": [str(path) for path in config.processed_roots],
                "output_dir": str(config.output_dir),
                "good_cpc": config.good_cpc,
                "poor_cpc": config.poor_cpc,
                "event_threshold": config.event_threshold,
                "eta": config.eta,
                "regional_support_z": config.regional_support_z,
                "min_regional_support": config.min_regional_support,
                "merge_gap": config.merge_gap,
                "pre_windows": config.pre_windows,
                "post_windows": config.post_windows,
                "min_episode_windows": config.min_episode_windows,
                "min_aligned_windows": config.min_aligned_windows,
                "max_subjects_per_class": config.max_subjects_per_class,
                "max_runs_per_subject": config.max_runs_per_subject,
                "n_splits": config.n_splits,
                "n_repeats": config.n_repeats,
                "random_state": config.random_state,
                "support_regions": list(SUPPORT_REGIONS),
                "profile_columns": list(PROFILE_COLUMNS),
                "n_runs_analyzed": int(len(run_features)),
                "n_subjects_analyzed": int(subject_features["pooled_subject"].nunique()) if not subject_features.empty else 0,
            },
            indent=2,
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    print(f"Wrote event-sliced summary to {config.output_dir / 'event_sliced_summary.md'}")
    print(f"Wrote subject features to {config.output_dir / 'event_sliced_subject_features.csv'}")


if __name__ == "__main__":
    main()
