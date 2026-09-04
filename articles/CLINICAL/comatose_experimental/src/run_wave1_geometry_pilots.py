from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.metrics import roc_auc_score


ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
COMA_DIR = ARTICLE_DIR.parent / "comatose_ndt"

DEFAULT_PROCESSED_ROOT = (
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260523_173059_part1_141sub"
)
DEFAULT_TIMELINE_DIR = COMA_DIR / "results" / "timeline_analysis_20260525_part1_primary12h"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "wave1_geometry_pilots_20260526_part1_cpc15"

GOOD_CPC = 1
POOR_CPC = 5
PRIMARY_TIME_BIN = "0_12h"
COORDS_9D_PATHS = ("/coords_9d_subject_anchored/values", "/coords_9d/values")
JACOBIAN_9D_PATH = "/jacobian_9D/J_hat"
JACOBIAN_9D_CENTERS_PATH = "/jacobian_9D/centers"
MIN_CHAOS_POINTS = 128
MIN_JACOBIAN_WINDOWS = 64
EPS = 1e-12
RNG_SEED = 20260526

OUTPUT_METRICS: tuple[str, ...] = (
    "largest_lyapunov_per_hour",
    "lyapunov_positive_sum_per_hour",
    "kaplan_yorke_dimension",
    "mnps_chaos_index_median",
    "mnps_chaos_index_iqr",
    "mnj_rho_burstiness",
    "mnj_rotational_burstiness",
    "mnj_non_normality_median",
    "mnj_henrici_departure_median",
    "mnj_reactivity_median",
    "mnj_reactivity_gap_median",
)


@dataclass(frozen=True)
class Config:
    processed_roots: tuple[Path, ...]
    timeline_dir: Path
    output_dir: Path
    good_cpc: int
    poor_cpc: int
    primary_time_bin: str
    max_chaos_points: int
    max_lyapunov_windows: int
    burst_quantile: float
    min_burst_events: int
    limit_subjects: int | None


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Run first-wave experimental coma geometry pilots on the part1 I-CARE H5 bundle: "
            "0-1 chaos, linearized Lyapunov, MNJ burstiness, and non-normal/transient summaries."
        )
    )
    parser.add_argument(
        "--processed-root",
        type=Path,
        action="append",
        default=None,
        help=(
            "Processed H5 root to search when remapping timeline paths. "
            "Repeat for pooled cohorts that mix part1 and part2 bundles."
        ),
    )
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--good-cpc", type=int, default=GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=POOR_CPC)
    parser.add_argument("--primary-time-bin", type=str, default=PRIMARY_TIME_BIN)
    parser.add_argument(
        "--max-chaos-points",
        type=int,
        default=4000,
        help="Evenly downsampled 9D trajectory length used for the 0-1 chaos test.",
    )
    parser.add_argument(
        "--max-lyapunov-windows",
        type=int,
        default=2500,
        help="Evenly downsampled Jacobian windows used for the linearized Lyapunov estimate.",
    )
    parser.add_argument(
        "--burst-quantile",
        type=float,
        default=0.90,
        help="Upper quantile used to define Jacobian spike events for burstiness.",
    )
    parser.add_argument(
        "--min-burst-events",
        type=int,
        default=4,
        help="Minimum spike count required before burstiness is reported.",
    )
    parser.add_argument("--limit-subjects", type=int, default=None)
    args = parser.parse_args()
    processed_roots = tuple(args.processed_root) if args.processed_root else (DEFAULT_PROCESSED_ROOT,)
    return Config(
        processed_roots=processed_roots,
        timeline_dir=args.timeline_dir,
        output_dir=args.output_dir,
        good_cpc=int(args.good_cpc),
        poor_cpc=int(args.poor_cpc),
        primary_time_bin=str(args.primary_time_bin),
        max_chaos_points=max(int(args.max_chaos_points), MIN_CHAOS_POINTS),
        max_lyapunov_windows=max(int(args.max_lyapunov_windows), MIN_JACOBIAN_WINDOWS),
        burst_quantile=float(args.burst_quantile),
        min_burst_events=max(int(args.min_burst_events), 3),
        limit_subjects=args.limit_subjects,
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize_path(value: Any) -> str:
    return str(Path(str(value))).replace("\\", "/").lower()


def path_tail_key(value: Any, *, depth: int = 2) -> str:
    normalized = normalize_path(value)
    parts = [part for part in normalized.split("/") if part]
    return "/".join(parts[-depth:]) if parts else ""


def build_h5_lookup(processed_roots: tuple[Path, ...]) -> dict[str, Path]:
    lookup: dict[str, Path] = {}
    ambiguous: set[str] = set()
    for processed_root in processed_roots:
        for h5_path in sorted(processed_root.rglob("*.h5")):
            key = path_tail_key(h5_path)
            if not key:
                continue
            previous = lookup.get(key)
            if previous is not None and previous != h5_path:
                ambiguous.add(key)
                continue
            lookup[key] = h5_path
    for key in ambiguous:
        lookup.pop(key, None)
    return lookup


def load_run_table(config: Config) -> pd.DataFrame:
    path = config.timeline_dir / "run_timing_metadata.csv"
    frame = pd.read_csv(path, low_memory=False)
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[
        (frame["time_bin"] == config.primary_time_bin)
        & (frame["cpc_numeric"].isin([float(config.good_cpc), float(config.poor_cpc)]))
    ].copy()
    frame["label"] = np.where(frame["cpc_numeric"] == float(config.good_cpc), 1, 0)
    frame["label_name"] = np.where(frame["label"] == 1, f"CPC{config.good_cpc}", f"CPC{config.poor_cpc}")

    lookup = build_h5_lookup(config.processed_roots)
    frame["processed_h5_path_original"] = frame["processed_h5_path"].astype(str)
    frame["processed_h5_path"] = frame["processed_h5_path"].map(
        lambda value: str(lookup.get(path_tail_key(value), Path(str(value))))
    )
    frame["processed_h5_exists"] = frame["processed_h5_path"].map(lambda value: Path(value).exists())
    frame = frame[frame["processed_h5_exists"]].copy()

    frame["run_start_from_anchor_sec"] = pd.to_numeric(frame["run_start_from_anchor_sec"], errors="coerce")
    frame["run_midpoint_from_anchor_sec"] = pd.to_numeric(frame["run_midpoint_from_anchor_sec"], errors="coerce")
    frame["n_windows"] = pd.to_numeric(frame["n_windows"], errors="coerce")
    frame["run_key"] = (
        frame["subject"].astype(str)
        + "_run-"
        + frame["run"].astype(str).str.zfill(3)
        + "_acq-"
        + frame["acq"].astype(str)
    )
    frame = frame.sort_values(["subject", "run_start_from_anchor_sec", "run", "acq"]).reset_index(drop=True)

    if config.limit_subjects:
        keep_subjects = frame["subject"].astype(str).drop_duplicates().tolist()[: int(config.limit_subjects)]
        frame = frame[frame["subject"].astype(str).isin(keep_subjects)].copy()
    return frame


def resolve_dataset_path(h5: h5py.File, candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if candidate in h5:
            return candidate
    return None


def read_run_arrays(run_row: pd.Series) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    processed_h5_path = Path(str(run_row["processed_h5_path"]))
    if not processed_h5_path.exists():
        return np.empty((0, 9)), np.empty(0), np.empty((0, 9, 9)), np.empty(0)

    with h5py.File(processed_h5_path, "r") as h5:
        coords_path = resolve_dataset_path(h5, COORDS_9D_PATHS)
        if coords_path is None or JACOBIAN_9D_PATH not in h5 or JACOBIAN_9D_CENTERS_PATH not in h5:
            return np.empty((0, 9)), np.empty(0), np.empty((0, 9, 9)), np.empty(0)
        coords = np.asarray(h5[coords_path], dtype=float)
        jacobians = np.asarray(h5[JACOBIAN_9D_PATH], dtype=float)
        centers = np.asarray(h5[JACOBIAN_9D_CENTERS_PATH], dtype=int)
        if "time" in h5:
            time = np.asarray(h5["time"], dtype=float)
        elif "window_start" in h5 and "window_end" in h5:
            starts = np.asarray(h5["window_start"], dtype=float)
            ends = np.asarray(h5["window_end"], dtype=float)
            time = 0.5 * (starts + ends)
        else:
            time = np.arange(coords.shape[0], dtype=float)

    coords = np.asarray(coords, dtype=float)
    time = np.asarray(time, dtype=float)
    if coords.ndim != 2 or coords.shape[1] < 9:
        return np.empty((0, 9)), np.empty(0), np.empty((0, 9, 9)), np.empty(0)
    coords = coords[:, :9]
    limit = min(len(coords), len(time))
    coords = coords[:limit]
    time = time[:limit]

    finite_coord_mask = np.isfinite(time) & np.isfinite(coords).all(axis=1)
    coords = coords[finite_coord_mask]
    time = time[finite_coord_mask]
    if len(coords) == 0:
        return np.empty((0, 9)), np.empty(0), np.empty((0, 9, 9)), np.empty(0)

    valid_center_mask = (centers >= 0) & (centers < limit)
    centers = centers[valid_center_mask]
    jacobians = jacobians[: len(centers)]
    finite_jac_mask = np.isfinite(jacobians).all(axis=(1, 2))
    jacobians = jacobians[finite_jac_mask]
    centers = centers[finite_jac_mask]
    if len(jacobians) == 0:
        return coords, time, np.empty((0, 9, 9)), np.empty(0)

    jacobian_time = time[centers]
    return coords, time, jacobians, jacobian_time


def sample_evenly(values: np.ndarray, max_points: int) -> np.ndarray:
    if len(values) <= max_points:
        return values
    indices = np.linspace(0, len(values) - 1, num=max_points, dtype=int)
    return values[indices]


def sample_evenly_pair(values: np.ndarray, time: np.ndarray, max_points: int) -> tuple[np.ndarray, np.ndarray]:
    if len(values) <= max_points:
        return values, time
    indices = np.linspace(0, len(values) - 1, num=max_points, dtype=int)
    return values[indices], time[indices]


def subject_series_from_runs(subject_runs: pd.DataFrame) -> dict[str, Any]:
    coord_blocks: list[np.ndarray] = []
    coord_time_blocks: list[np.ndarray] = []
    jac_blocks: list[np.ndarray] = []
    jac_time_blocks: list[np.ndarray] = []

    n_runs_with_9d = 0
    n_runs_with_jacobian = 0
    for _, run_row in subject_runs.iterrows():
        coords, time, jacobians, jacobian_time = read_run_arrays(run_row)
        run_start = float(run_row["run_start_from_anchor_sec"])
        if len(coords):
            coord_blocks.append(coords)
            coord_time_blocks.append(run_start + time)
            n_runs_with_9d += 1
        if len(jacobians):
            jac_blocks.append(jacobians)
            jac_time_blocks.append(run_start + jacobian_time)
            n_runs_with_jacobian += 1

    coords = np.concatenate(coord_blocks, axis=0) if coord_blocks else np.empty((0, 9))
    coord_time = np.concatenate(coord_time_blocks, axis=0) if coord_time_blocks else np.empty(0)
    jacobians = np.concatenate(jac_blocks, axis=0) if jac_blocks else np.empty((0, 9, 9))
    jacobian_time = np.concatenate(jac_time_blocks, axis=0) if jac_time_blocks else np.empty(0)

    if len(coord_time):
        order = np.argsort(coord_time)
        coords = coords[order]
        coord_time = coord_time[order]
    if len(jacobian_time):
        order = np.argsort(jacobian_time)
        jacobians = jacobians[order]
        jacobian_time = jacobian_time[order]

    return {
        "coords": coords,
        "coord_time": coord_time,
        "jacobians": jacobians,
        "jacobian_time": jacobian_time,
        "n_runs_with_9d": int(n_runs_with_9d),
        "n_runs_with_jacobian": int(n_runs_with_jacobian),
    }


def batch_jacobian_series_metrics(jacobians: np.ndarray) -> dict[str, np.ndarray]:
    eigenvalues = np.linalg.eigvals(jacobians)
    spectral_radius = np.max(np.abs(eigenvalues), axis=1)
    rotational_power = np.sum(np.abs(eigenvalues.imag), axis=1)
    max_real_eig = np.max(eigenvalues.real, axis=1)
    fro_sq = np.sum(jacobians * jacobians, axis=(1, 2))
    eig_sq = np.sum(np.abs(eigenvalues) ** 2, axis=1)
    henrici_departure = np.sqrt(np.clip(fro_sq - eig_sq, 0.0, None))

    transpose = np.swapaxes(jacobians, 1, 2)
    commutator = jacobians @ transpose - transpose @ jacobians
    non_normality = np.linalg.norm(commutator, ord="fro", axis=(1, 2))

    symmetric = 0.5 * (jacobians + transpose)
    reactivity = np.linalg.eigvalsh(symmetric)[:, -1]
    reactivity_gap = reactivity - max_real_eig

    return {
        "spectral_radius": spectral_radius,
        "rotational_power": rotational_power,
        "henrici_departure": henrici_departure,
        "non_normality": non_normality,
        "reactivity": reactivity,
        "reactivity_gap": reactivity_gap,
    }


def burstiness_from_events(values: np.ndarray, event_time: np.ndarray, *, quantile: float, min_events: int) -> float:
    values = np.asarray(values, dtype=float)
    event_time = np.asarray(event_time, dtype=float)
    finite_mask = np.isfinite(values) & np.isfinite(event_time)
    values = values[finite_mask]
    event_time = event_time[finite_mask]
    if len(values) < min_events:
        return float("nan")
    threshold = float(np.quantile(values, quantile))
    spike_times = np.unique(event_time[values >= threshold])
    if len(spike_times) < min_events:
        return float("nan")
    intervals = np.diff(np.sort(spike_times))
    if len(intervals) < 2:
        return float("nan")
    mean_interval = float(np.mean(intervals))
    std_interval = float(np.std(intervals, ddof=1))
    if not np.isfinite(mean_interval + std_interval) or (mean_interval + std_interval) <= 0:
        return float("nan")
    return float((std_interval - mean_interval) / (std_interval + mean_interval))


def zero_one_chaos_single(series: np.ndarray, *, n_c: int = 32, seed: int = RNG_SEED) -> float:
    series = np.asarray(series, dtype=float)
    series = series[np.isfinite(series)]
    if len(series) < MIN_CHAOS_POINTS:
        return float("nan")
    centered = series - float(np.mean(series))
    scale = float(np.std(centered))
    if not np.isfinite(scale) or scale <= 0:
        return float("nan")
    centered = centered / scale

    n = np.arange(1, len(centered) + 1, dtype=float)
    rng = np.random.default_rng(seed)
    c_values = rng.uniform(np.pi / 5.0, 4.0 * np.pi / 5.0, size=n_c)
    k_values: list[float] = []
    for c_value in c_values:
        phase = c_value * n
        p = np.cumsum(centered * np.cos(phase))
        q = np.cumsum(centered * np.sin(phase))
        displacement = p * p + q * q
        if float(np.std(displacement)) <= EPS:
            continue
        corr = np.corrcoef(n, displacement)[0, 1]
        if np.isfinite(corr):
            k_values.append(float(abs(corr)))
    if not k_values:
        return float("nan")
    return float(np.median(k_values))


def zero_one_chaos_multivariate(coords_9d: np.ndarray, *, max_points: int) -> dict[str, float]:
    coords_9d = np.asarray(coords_9d, dtype=float)
    if len(coords_9d) < MIN_CHAOS_POINTS:
        return {
            "mnps_chaos_index_median": float("nan"),
            "mnps_chaos_index_iqr": float("nan"),
        }
    sampled = sample_evenly(coords_9d, max_points)
    chaos_values = np.asarray(
        [zero_one_chaos_single(sampled[:, idx], seed=RNG_SEED + idx) for idx in range(sampled.shape[1])],
        dtype=float,
    )
    chaos_values = chaos_values[np.isfinite(chaos_values)]
    if len(chaos_values) == 0:
        return {
            "mnps_chaos_index_median": float("nan"),
            "mnps_chaos_index_iqr": float("nan"),
        }
    q25, q75 = np.quantile(chaos_values, [0.25, 0.75])
    return {
        "mnps_chaos_index_median": float(np.median(chaos_values)),
        "mnps_chaos_index_iqr": float(q75 - q25),
    }


def linearized_lyapunov_metrics(jacobians: np.ndarray, jacobian_time: np.ndarray, *, max_windows: int) -> dict[str, float]:
    jacobians = np.asarray(jacobians, dtype=float)
    jacobian_time = np.asarray(jacobian_time, dtype=float)
    if len(jacobians) < MIN_JACOBIAN_WINDOWS:
        return {
            "largest_lyapunov_per_hour": float("nan"),
            "lyapunov_positive_sum_per_hour": float("nan"),
            "kaplan_yorke_dimension": float("nan"),
        }

    jacobians, jacobian_time = sample_evenly_pair(jacobians, jacobian_time, max_windows)
    q_matrix = np.eye(jacobians.shape[1], dtype=float)
    log_diag = np.zeros(jacobians.shape[1], dtype=float)
    total_dt_hours = 0.0

    for idx in range(len(jacobians) - 1):
        dt_sec = float(jacobian_time[idx + 1] - jacobian_time[idx])
        if not np.isfinite(dt_sec) or dt_sec <= 0:
            continue
        transition = np.eye(jacobians.shape[1], dtype=float) + jacobians[idx] * dt_sec
        z_matrix = transition @ q_matrix
        q_matrix, r_matrix = np.linalg.qr(z_matrix)
        diag = np.clip(np.abs(np.diag(r_matrix)), EPS, None)
        log_diag += np.log(diag)
        total_dt_hours += dt_sec / 3600.0

    if not np.isfinite(total_dt_hours) or total_dt_hours <= 0:
        return {
            "largest_lyapunov_per_hour": float("nan"),
            "lyapunov_positive_sum_per_hour": float("nan"),
            "kaplan_yorke_dimension": float("nan"),
        }

    lambdas = np.sort(log_diag / total_dt_hours)[::-1]
    positive_sum = float(np.sum(lambdas[lambdas > 0]))
    cumulative = np.cumsum(lambdas)
    non_negative_idx = np.where(cumulative >= 0)[0]
    if len(non_negative_idx) == 0:
        ky_dimension = 0.0
    else:
        k_idx = int(non_negative_idx[-1])
        if k_idx >= len(lambdas) - 1 or lambdas[k_idx + 1] >= 0:
            ky_dimension = float(k_idx + 1)
        else:
            ky_dimension = float(k_idx + 1 + cumulative[k_idx] / abs(lambdas[k_idx + 1]))

    return {
        "largest_lyapunov_per_hour": float(lambdas[0]),
        "lyapunov_positive_sum_per_hour": positive_sum,
        "kaplan_yorke_dimension": ky_dimension,
    }


def summarize_finite(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    return float(np.median(values)) if len(values) else float("nan")


def compute_subject_row(subject_runs: pd.DataFrame, config: Config) -> dict[str, Any]:
    anchor_row = subject_runs.iloc[0]
    subject_series = subject_series_from_runs(subject_runs)
    coords = subject_series["coords"]
    jacobians = subject_series["jacobians"]
    jacobian_time = subject_series["jacobian_time"]

    chaos_metrics = zero_one_chaos_multivariate(coords, max_points=config.max_chaos_points)
    lyapunov_metrics = linearized_lyapunov_metrics(
        jacobians,
        jacobian_time,
        max_windows=config.max_lyapunov_windows,
    )

    if len(jacobians):
        jacobian_series = batch_jacobian_series_metrics(jacobians)
        rho_burstiness = burstiness_from_events(
            jacobian_series["spectral_radius"],
            jacobian_time,
            quantile=config.burst_quantile,
            min_events=config.min_burst_events,
        )
        rotational_burstiness = burstiness_from_events(
            jacobian_series["rotational_power"],
            jacobian_time,
            quantile=config.burst_quantile,
            min_events=config.min_burst_events,
        )
        non_normality_median = summarize_finite(jacobian_series["non_normality"])
        henrici_departure_median = summarize_finite(jacobian_series["henrici_departure"])
        reactivity_median = summarize_finite(jacobian_series["reactivity"])
        reactivity_gap_median = summarize_finite(jacobian_series["reactivity_gap"])
    else:
        rho_burstiness = float("nan")
        rotational_burstiness = float("nan")
        non_normality_median = float("nan")
        henrici_departure_median = float("nan")
        reactivity_median = float("nan")
        reactivity_gap_median = float("nan")

    return {
        "subject": str(anchor_row["subject"]),
        "label": int(anchor_row["label"]),
        "label_name": str(anchor_row["label_name"]),
        "cpc": int(anchor_row["cpc_numeric"]),
        "hospital": str(anchor_row["hospital"]),
        "age": pd.to_numeric(anchor_row["age"], errors="coerce"),
        "sex": anchor_row["sex"],
        "rosc_minutes": pd.to_numeric(anchor_row["rosc_minutes"], errors="coerce"),
        "ttm_celsius": pd.to_numeric(anchor_row["ttm_celsius"], errors="coerce"),
        "n_runs": int(len(subject_runs)),
        "n_runs_with_9d": int(subject_series["n_runs_with_9d"]),
        "n_runs_with_jacobian": int(subject_series["n_runs_with_jacobian"]),
        "n_coord_points": int(len(coords)),
        "n_jacobian_windows": int(len(jacobians)),
        **chaos_metrics,
        **lyapunov_metrics,
        "mnj_rho_burstiness": rho_burstiness,
        "mnj_rotational_burstiness": rotational_burstiness,
        "mnj_non_normality_median": non_normality_median,
        "mnj_henrici_departure_median": henrici_departure_median,
        "mnj_reactivity_median": reactivity_median,
        "mnj_reactivity_gap_median": reactivity_gap_median,
    }


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    good = np.asarray(good, dtype=float)
    poor = np.asarray(poor, dtype=float)
    good = good[np.isfinite(good)]
    poor = poor[np.isfinite(poor)]
    if len(good) < 2 or len(poor) < 2:
        return float("nan")
    pooled = ((len(good) - 1) * np.var(good, ddof=1) + (len(poor) - 1) * np.var(poor, ddof=1)) / (
        len(good) + len(poor) - 2
    )
    if pooled <= 0 or not np.isfinite(pooled):
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled))


def cliffs_delta(good: np.ndarray, poor: np.ndarray) -> float:
    good = np.asarray(good, dtype=float)
    poor = np.asarray(poor, dtype=float)
    good = good[np.isfinite(good)]
    poor = poor[np.isfinite(poor)]
    if len(good) == 0 or len(poor) == 0:
        return float("nan")
    comparisons = np.subtract.outer(good, poor)
    return float((np.sum(comparisons > 0) - np.sum(comparisons < 0)) / comparisons.size)


def summarize_metric_contrasts(subject_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    labels = subject_metrics["label"].astype(int).to_numpy()
    for metric in OUTPUT_METRICS:
        values = pd.to_numeric(subject_metrics[metric], errors="coerce")
        metric_frame = pd.DataFrame({"value": values, "label": labels}).dropna()
        if metric_frame.empty:
            continue
        good = metric_frame.loc[metric_frame["label"] == 1, "value"].to_numpy(dtype=float)
        poor = metric_frame.loc[metric_frame["label"] == 0, "value"].to_numpy(dtype=float)
        if len(good) == 0 or len(poor) == 0:
            continue
        try:
            mw_p = float(mannwhitneyu(good, poor, alternative="two-sided").pvalue)
        except ValueError:
            mw_p = float("nan")
        try:
            direct_auroc = float(roc_auc_score(metric_frame["label"].astype(int), metric_frame["value"].astype(float)))
        except ValueError:
            direct_auroc = float("nan")
        rows.append(
            {
                "metric": metric,
                "cpc1_median": float(np.median(good)),
                "cpc5_median": float(np.median(poor)),
                "cohens_d": cohens_d(good, poor),
                "cliffs_delta": cliffs_delta(good, poor),
                "mann_whitney_p": mw_p,
                "direct_auroc": direct_auroc,
                "best_direction_auroc": float(max(direct_auroc, 1.0 - direct_auroc)) if np.isfinite(direct_auroc) else np.nan,
                "good_outcome_higher": bool(direct_auroc >= 0.5) if np.isfinite(direct_auroc) else None,
                "n_cpc1": int(len(good)),
                "n_cpc5": int(len(poor)),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values(["best_direction_auroc", "cohens_d"], ascending=[False, False]).reset_index(drop=True)


def build_summary_markdown(subject_metrics: pd.DataFrame, contrasts: pd.DataFrame, config: Config) -> str:
    n_subjects = int(subject_metrics["subject"].nunique())
    n_good = int((subject_metrics["label"] == 1).sum())
    n_poor = int((subject_metrics["label"] == 0).sum())
    top_rows = contrasts.head(6)

    lines = [
        "# Wave 1 Geometry Pilots Summary",
        "",
        f"- processed roots: `{', '.join(str(path) for path in config.processed_roots)}`",
        f"- timeline dir: `{config.timeline_dir}`",
        f"- primary time bin: `{config.primary_time_bin}`",
        f"- subjects: `{n_subjects}` (`CPC{config.good_cpc}` = `{n_good}`, `CPC{config.poor_cpc}` = `{n_poor}`)",
        f"- max chaos points per subject: `{config.max_chaos_points}`",
        f"- max Lyapunov windows per subject: `{config.max_lyapunov_windows}`",
        f"- burst quantile: `{config.burst_quantile:.2f}`",
        "",
        "## Top Metrics",
        "",
        "| Metric | CPC1 median | CPC5 median | Cohen's d | Best-direction AUROC |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in top_rows.iterrows():
        lines.append(
            "| {metric} | {cpc1:.4f} | {cpc5:.4f} | {d:.3f} | {auc:.3f} |".format(
                metric=row["metric"],
                cpc1=float(row["cpc1_median"]),
                cpc5=float(row["cpc5_median"]),
                d=float(row["cohens_d"]),
                auc=float(row["best_direction_auroc"]),
            )
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- The Lyapunov output is a pilot-style linearized discrete approximation built from `I + J_t * dt` rather than a fully re-estimated trajectory Jacobian flow.",
            "- The non-normal block reports cheap transient proxies (`non_normality`, Henrici departure, numerical-abscissa-style reactivity) instead of a full epsilon-pseudospectrum sweep.",
            "- These outputs are internal exploratory summaries on the selected cohort/timeline, not frozen validation results.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    ensure_dir(config.output_dir)

    run_table = load_run_table(config)
    if run_table.empty:
        raise RuntimeError("No eligible CPC1/CPC5 runs were found after filtering and path remapping.")

    subjects = run_table["subject"].astype(str).drop_duplicates().tolist()
    subject_rows: list[dict[str, Any]] = []
    for idx, subject in enumerate(subjects, start=1):
        subject_runs = run_table[run_table["subject"].astype(str) == subject].copy()
        subject_rows.append(compute_subject_row(subject_runs, config))
        if idx % 10 == 0 or idx == len(subjects):
            print(f"Processed {idx}/{len(subjects)} subjects.", flush=True)

    subject_metrics = pd.DataFrame(subject_rows).sort_values("subject").reset_index(drop=True)
    contrasts = summarize_metric_contrasts(subject_metrics)

    run_inventory_columns = [
        "subject",
        "run_key",
        "run",
        "acq",
        "cpc_numeric",
        "label_name",
        "hospital",
        "run_start_from_anchor_sec",
        "run_midpoint_from_anchor_sec",
        "n_windows",
        "processed_h5_path",
    ]
    run_inventory = run_table[run_inventory_columns].rename(columns={"cpc_numeric": "cpc"}).copy()

    subject_metrics.to_csv(config.output_dir / "subject_wave1_metrics.csv", index=False)
    contrasts.to_csv(config.output_dir / "wave1_metric_contrasts.csv", index=False)
    run_inventory.to_csv(config.output_dir / "run_inventory.csv", index=False)
    (config.output_dir / "wave1_summary.md").write_text(
        build_summary_markdown(subject_metrics, contrasts, config),
        encoding="utf-8",
    )

    manifest = {
        "pilot_family": "wave1_geometry",
        "processed_roots": [str(path) for path in config.processed_roots],
        "timeline_dir": str(config.timeline_dir),
        "output_dir": str(config.output_dir),
        "cohort": config.timeline_dir.name,
        "primary_time_bin": config.primary_time_bin,
        "good_cpc": config.good_cpc,
        "poor_cpc": config.poor_cpc,
        "n_subjects": int(subject_metrics["subject"].nunique()),
        "n_runs": int(len(run_table)),
        "max_chaos_points": int(config.max_chaos_points),
        "max_lyapunov_windows": int(config.max_lyapunov_windows),
        "burst_quantile": float(config.burst_quantile),
        "min_burst_events": int(config.min_burst_events),
        "metrics": list(OUTPUT_METRICS),
        "notes": [
            "Lyapunov output uses a linearized discrete approximation based on I + J_t * dt.",
            "Non-normal outputs are pilot-style transient proxies, not a full epsilon-pseudospectrum sweep.",
        ],
        "config": {
            key: (
                [str(item) for item in value]
                if key == "processed_roots"
                else (str(value) if isinstance(value, Path) else value)
            )
            for key, value in asdict(config).items()
        },
    }
    (config.output_dir / "wave1_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote outputs to {config.output_dir}", flush=True)


if __name__ == "__main__":
    main()
