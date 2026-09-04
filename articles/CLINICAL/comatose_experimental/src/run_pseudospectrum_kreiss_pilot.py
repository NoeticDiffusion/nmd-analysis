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

DEFAULT_PROCESSED_ROOTS = (
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260523_173059_part1_141sub",
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_physionet_icare_2_1_20260522_095945_part2_140sub",
)
DEFAULT_TIMELINE_DIR = COMA_DIR / "results" / "timeline_analysis_20260525_combined_cpc15_primary12h"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "pseudospectrum_kreiss_pilot_20260526_pooled_cpc15"

GOOD_CPC = 1
POOR_CPC = 5
PRIMARY_TIME_BIN = "0_12h"
JACOBIAN_9D_PATH = "/jacobian_9D/J_hat"
JACOBIAN_9D_CENTERS_PATH = "/jacobian_9D/centers"
EPS = 1e-12
MIN_JACOBIAN_WINDOWS = 40

OUTPUT_METRICS: tuple[str, ...] = (
    "kreiss_realaxis_lower_median",
    "kreiss_realaxis_lower_p95",
    "resolvent_peak_realaxis_median",
    "pseudospec_abscissa_rel01_median",
    "pseudospec_abscissa_rel05_median",
    "pseudospec_headroom_rel05_median",
)


@dataclass(frozen=True)
class Config:
    processed_roots: tuple[Path, ...]
    timeline_dir: Path
    output_dir: Path
    good_cpc: int
    poor_cpc: int
    primary_time_bin: str
    max_jacobian_windows: int
    grid_points: int
    rel_eps_small: float
    rel_eps_large: float
    limit_subjects: int | None


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Run a pooled pseudospectrum/Kreiss coma pilot using coarse real-axis "
            "resolvent scans over the 9D Jacobian sequence."
        )
    )
    parser.add_argument(
        "--processed-root",
        type=Path,
        action="append",
        default=None,
        help="Processed H5 root to search. Repeat for pooled cohorts.",
    )
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--good-cpc", type=int, default=GOOD_CPC)
    parser.add_argument("--poor-cpc", type=int, default=POOR_CPC)
    parser.add_argument("--primary-time-bin", type=str, default=PRIMARY_TIME_BIN)
    parser.add_argument(
        "--max-jacobian-windows",
        type=int,
        default=400,
        help="Maximum evenly sampled 9D Jacobian windows per subject used for the scan.",
    )
    parser.add_argument(
        "--grid-points",
        type=int,
        default=14,
        help="Number of positive real-axis probe points per Jacobian window.",
    )
    parser.add_argument(
        "--rel-eps-small",
        type=float,
        default=0.01,
        help="Smaller relative epsilon used for pseudospectral abscissa.",
    )
    parser.add_argument(
        "--rel-eps-large",
        type=float,
        default=0.05,
        help="Larger relative epsilon used for pseudospectral abscissa.",
    )
    parser.add_argument("--limit-subjects", type=int, default=None)
    args = parser.parse_args()
    processed_roots = tuple(args.processed_root) if args.processed_root else DEFAULT_PROCESSED_ROOTS
    return Config(
        processed_roots=processed_roots,
        timeline_dir=args.timeline_dir,
        output_dir=args.output_dir,
        good_cpc=int(args.good_cpc),
        poor_cpc=int(args.poor_cpc),
        primary_time_bin=str(args.primary_time_bin),
        max_jacobian_windows=max(int(args.max_jacobian_windows), MIN_JACOBIAN_WINDOWS),
        grid_points=max(int(args.grid_points), 6),
        rel_eps_small=float(args.rel_eps_small),
        rel_eps_large=float(args.rel_eps_large),
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


def read_jacobian_arrays(run_row: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    processed_h5_path = Path(str(run_row["processed_h5_path"]))
    if not processed_h5_path.exists():
        return np.empty((0, 9, 9)), np.empty(0)

    with h5py.File(processed_h5_path, "r") as h5:
        if JACOBIAN_9D_PATH not in h5 or JACOBIAN_9D_CENTERS_PATH not in h5:
            return np.empty((0, 9, 9)), np.empty(0)
        jacobians = np.asarray(h5[JACOBIAN_9D_PATH], dtype=float)
        centers = np.asarray(h5[JACOBIAN_9D_CENTERS_PATH], dtype=int)
        if "time" in h5:
            time = np.asarray(h5["time"], dtype=float)
        elif "window_start" in h5 and "window_end" in h5:
            starts = np.asarray(h5["window_start"], dtype=float)
            ends = np.asarray(h5["window_end"], dtype=float)
            time = 0.5 * (starts + ends)
        else:
            return np.empty((0, 9, 9)), np.empty(0)

    limit = min(len(time), int(np.max(centers) + 1) if len(centers) else 0)
    if limit <= 0:
        return np.empty((0, 9, 9)), np.empty(0)
    valid_center_mask = (centers >= 0) & (centers < len(time))
    centers = centers[valid_center_mask]
    jacobians = jacobians[: len(centers)]
    finite_mask = np.isfinite(jacobians).all(axis=(1, 2))
    jacobians = jacobians[finite_mask]
    centers = centers[finite_mask]
    if len(jacobians) == 0:
        return np.empty((0, 9, 9)), np.empty(0)
    jacobian_time = np.asarray(time[centers], dtype=float)
    return jacobians, jacobian_time


def sample_evenly_pair(values: np.ndarray, time: np.ndarray, max_points: int) -> tuple[np.ndarray, np.ndarray]:
    if len(values) <= max_points:
        return values, time
    indices = np.linspace(0, len(values) - 1, num=max_points, dtype=int)
    return values[indices], time[indices]


def subject_jacobians_from_runs(subject_runs: pd.DataFrame) -> dict[str, Any]:
    jac_blocks: list[np.ndarray] = []
    jac_time_blocks: list[np.ndarray] = []
    n_runs_with_jacobian = 0
    for _, run_row in subject_runs.iterrows():
        jacobians, jacobian_time = read_jacobian_arrays(run_row)
        if len(jacobians) == 0:
            continue
        run_start = float(run_row["run_start_from_anchor_sec"])
        jac_blocks.append(jacobians)
        jac_time_blocks.append(run_start + jacobian_time)
        n_runs_with_jacobian += 1
    jacobians = np.concatenate(jac_blocks, axis=0) if jac_blocks else np.empty((0, 9, 9))
    jacobian_time = np.concatenate(jac_time_blocks, axis=0) if jac_time_blocks else np.empty(0)
    if len(jacobian_time):
        order = np.argsort(jacobian_time)
        jacobians = jacobians[order]
        jacobian_time = jacobian_time[order]
    return {
        "jacobians": jacobians,
        "jacobian_time": jacobian_time,
        "n_runs_with_jacobian": int(n_runs_with_jacobian),
    }


def kreiss_scan_window(
    jacobian: np.ndarray,
    *,
    grid_points: int,
    rel_eps_small: float,
    rel_eps_large: float,
) -> dict[str, float]:
    eigvals = np.linalg.eigvals(jacobian)
    max_real_eig = float(np.max(eigvals.real))
    spectral_scale = float(max(np.max(np.abs(eigvals)), 1.0))
    fro_norm = float(np.linalg.norm(jacobian, ord="fro"))
    scale = max(spectral_scale, fro_norm / np.sqrt(jacobian.shape[0]), 1.0)
    probe_points = np.geomspace(scale * 1e-3, scale * 2.0, num=grid_points)

    kreiss_lower = 0.0
    resolvent_peak = 0.0
    abscissa_small = 0.0
    abscissa_large = 0.0
    eps_small = rel_eps_small * max(fro_norm, 1.0)
    eps_large = rel_eps_large * max(fro_norm, 1.0)
    identity = np.eye(jacobian.shape[0], dtype=float)

    for x_value in probe_points:
        shifted = (x_value * identity) - jacobian
        singular_values = np.linalg.svd(shifted, compute_uv=False)
        sigma_min = float(max(np.min(singular_values), EPS))
        kreiss_lower = max(kreiss_lower, float(x_value / sigma_min))
        resolvent_peak = max(resolvent_peak, float(1.0 / sigma_min))
        if sigma_min <= eps_small:
            abscissa_small = float(x_value)
        if sigma_min <= eps_large:
            abscissa_large = float(x_value)

    return {
        "kreiss_realaxis_lower": kreiss_lower,
        "resolvent_peak_realaxis": resolvent_peak,
        "pseudospec_abscissa_rel01": abscissa_small,
        "pseudospec_abscissa_rel05": abscissa_large,
        "pseudospec_headroom_rel05": float(abscissa_large - max_real_eig),
    }


def summarize_subject_pseudospectrum(subject_runs: pd.DataFrame, config: Config) -> dict[str, Any]:
    anchor_row = subject_runs.iloc[0]
    payload = subject_jacobians_from_runs(subject_runs)
    jacobians = payload["jacobians"]
    jacobian_time = payload["jacobian_time"]
    if len(jacobians) < MIN_JACOBIAN_WINDOWS:
        return {
            "subject": str(anchor_row["subject"]),
            "label": int(anchor_row["label"]),
            "label_name": str(anchor_row["label_name"]),
            "cpc": int(anchor_row["cpc_numeric"]),
            "hospital": str(anchor_row["hospital"]),
            "n_runs": int(len(subject_runs)),
            "n_runs_with_jacobian": int(payload["n_runs_with_jacobian"]),
            "n_jacobian_windows": int(len(jacobians)),
            **{metric: float("nan") for metric in OUTPUT_METRICS},
        }

    jacobians, jacobian_time = sample_evenly_pair(jacobians, jacobian_time, config.max_jacobian_windows)
    rows = [
        kreiss_scan_window(
            jacobian,
            grid_points=config.grid_points,
            rel_eps_small=config.rel_eps_small,
            rel_eps_large=config.rel_eps_large,
        )
        for jacobian in jacobians
    ]
    window_frame = pd.DataFrame(rows)
    return {
        "subject": str(anchor_row["subject"]),
        "label": int(anchor_row["label"]),
        "label_name": str(anchor_row["label_name"]),
        "cpc": int(anchor_row["cpc_numeric"]),
        "hospital": str(anchor_row["hospital"]),
        "n_runs": int(len(subject_runs)),
        "n_runs_with_jacobian": int(payload["n_runs_with_jacobian"]),
        "n_jacobian_windows": int(len(jacobians)),
        "kreiss_realaxis_lower_median": float(window_frame["kreiss_realaxis_lower"].median()),
        "kreiss_realaxis_lower_p95": float(window_frame["kreiss_realaxis_lower"].quantile(0.95)),
        "resolvent_peak_realaxis_median": float(window_frame["resolvent_peak_realaxis"].median()),
        "pseudospec_abscissa_rel01_median": float(window_frame["pseudospec_abscissa_rel01"].median()),
        "pseudospec_abscissa_rel05_median": float(window_frame["pseudospec_abscissa_rel05"].median()),
        "pseudospec_headroom_rel05_median": float(window_frame["pseudospec_headroom_rel05"].median()),
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
        "# Pseudospectrum/Kreiss Pilot Summary",
        "",
        f"- processed roots: `{', '.join(str(path) for path in config.processed_roots)}`",
        f"- timeline dir: `{config.timeline_dir}`",
        f"- primary time bin: `{config.primary_time_bin}`",
        f"- subjects: `{n_subjects}` (`CPC{config.good_cpc}` = `{n_good}`, `CPC{config.poor_cpc}` = `{n_poor}`)",
        f"- max Jacobian windows per subject: `{config.max_jacobian_windows}`",
        f"- real-axis probe points: `{config.grid_points}`",
        f"- relative epsilons: `{config.rel_eps_small:.3f}`, `{config.rel_eps_large:.3f}`",
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
            "- This pilot uses a coarse positive-real-axis resolvent scan, so Kreiss is reported as a lower-bound style proxy rather than an exact complex-plane supremum.",
            "- The pseudospectral abscissa is likewise a coarse real-axis approximation using relative epsilon thresholds tied to Jacobian Frobenius scale.",
            "- These outputs are exploratory pooled summaries rather than a full epsilon-pseudospectrum contour analysis.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    config = parse_args()
    ensure_dir(config.output_dir)
    run_table = load_run_table(config)
    if run_table.empty:
        raise RuntimeError("No eligible CPC1/CPC5 pooled runs were found after remapping processed paths.")

    subjects = run_table["subject"].astype(str).drop_duplicates().tolist()
    subject_rows: list[dict[str, Any]] = []
    for idx, subject in enumerate(subjects, start=1):
        subject_runs = run_table[run_table["subject"].astype(str) == subject].copy()
        subject_rows.append(summarize_subject_pseudospectrum(subject_runs, config))
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
        "processed_h5_path",
    ]
    run_inventory = run_table[run_inventory_columns].rename(columns={"cpc_numeric": "cpc"}).copy()

    subject_metrics.to_csv(config.output_dir / "subject_pseudospectrum_metrics.csv", index=False)
    contrasts.to_csv(config.output_dir / "pseudospectrum_metric_contrasts.csv", index=False)
    run_inventory.to_csv(config.output_dir / "run_inventory.csv", index=False)
    (config.output_dir / "pseudospectrum_summary.md").write_text(
        build_summary_markdown(subject_metrics, contrasts, config),
        encoding="utf-8",
    )

    manifest = {
        "pilot_family": "pseudospectrum_kreiss",
        "processed_roots": [str(path) for path in config.processed_roots],
        "timeline_dir": str(config.timeline_dir),
        "output_dir": str(config.output_dir),
        "cohort": config.timeline_dir.name,
        "primary_time_bin": config.primary_time_bin,
        "good_cpc": config.good_cpc,
        "poor_cpc": config.poor_cpc,
        "n_subjects": int(subject_metrics["subject"].nunique()),
        "n_runs": int(len(run_table)),
        "max_jacobian_windows": int(config.max_jacobian_windows),
        "grid_points": int(config.grid_points),
        "rel_eps_small": float(config.rel_eps_small),
        "rel_eps_large": float(config.rel_eps_large),
        "metrics": list(OUTPUT_METRICS),
        "notes": [
            "Kreiss is a coarse positive-real-axis lower-bound style proxy rather than an exact complex-plane supremum.",
            "Pseudospectral abscissa is a coarse real-axis approximation using relative epsilon thresholds.",
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
    (config.output_dir / "pseudospectrum_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote outputs to {config.output_dir}", flush=True)


if __name__ == "__main__":
    main()
