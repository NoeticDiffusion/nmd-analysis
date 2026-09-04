from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List

import numpy as np
import pandas as pd

from laguerre_subject_pilot_v2 import (
    ARTICLE_DIR,
    Config,
    compute_direction_coherence,
    compute_legacy_change,
    compute_shape_change,
    compute_shape_entropy,
    compute_state_space_gradients,
    fit_local_quadratic_patch,
    summarize_distribution,
)


DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "laguerre_synthetic_controls_20260525"
DEFAULT_N_POINTS = 900
DEFAULT_NEIGHBORHOOD_SIZE = 25
DEFAULT_GRADIENT_NEIGHBORS = 8
DEFAULT_TIME_CHANGE_WINDOW = 6
DEFAULT_SHAPE_HIST_BINS = 12
DEFAULT_S3_OVER_S2_MAX = 0.75
DEFAULT_SURFACE_FIT_R2_MIN = 0.02
DEFAULT_NOISE_LEVELS = (0.0, 0.01, 0.03)
DEFAULT_REPEATS = 4
EPS = 1e-9


@dataclass(frozen=True)
class SyntheticConfig:
    output_dir: Path
    n_points: int
    noise_levels: tuple[float, ...]
    repeats: int
    laguerre_config: Config


def parse_args() -> SyntheticConfig:
    parser = argparse.ArgumentParser(
        description="Run synthetic geometry controls for the current Laguerre v2 estimator."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--n-points", type=int, default=DEFAULT_N_POINTS)
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    parser.add_argument("--noise-levels", type=float, nargs="*", default=list(DEFAULT_NOISE_LEVELS))
    parser.add_argument("--neighborhood-size", type=int, default=DEFAULT_NEIGHBORHOOD_SIZE)
    parser.add_argument("--gradient-neighbors", type=int, default=DEFAULT_GRADIENT_NEIGHBORS)
    parser.add_argument("--time-change-window", type=int, default=DEFAULT_TIME_CHANGE_WINDOW)
    parser.add_argument("--shape-hist-bins", type=int, default=DEFAULT_SHAPE_HIST_BINS)
    parser.add_argument("--s3-over-s2-max", type=float, default=DEFAULT_S3_OVER_S2_MAX)
    parser.add_argument("--surface-fit-r2-min", type=float, default=DEFAULT_SURFACE_FIT_R2_MIN)
    args = parser.parse_args()

    laguerre_config = Config(
        timeline_dir=ARTICLE_DIR,
        mnps_dir=ARTICLE_DIR,
        output_dir=args.output_dir,
        primary_time_bin="synthetic",
        cohort_tag="synthetic",
        good_cpc=1,
        poor_cpc=5,
        subjects_per_group=0,
        min_runs=1,
        max_points_per_run=max(8, int(args.n_points)),
        neighborhood_size=max(8, int(args.neighborhood_size)),
        gradient_neighbors=max(1, int(args.gradient_neighbors)),
        time_change_window=max(1, int(args.time_change_window)),
        shape_hist_bins=max(4, int(args.shape_hist_bins)),
        s3_over_s2_max=float(args.s3_over_s2_max),
        surface_fit_r2_min=float(args.surface_fit_r2_min),
        workers=1,
    )
    return SyntheticConfig(
        output_dir=args.output_dir,
        n_points=max(100, int(args.n_points)),
        noise_levels=tuple(float(x) for x in args.noise_levels),
        repeats=max(1, int(args.repeats)),
        laguerre_config=laguerre_config,
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sample_disk_points(n_points: int, rng: np.random.Generator, radius: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    theta = rng.uniform(0.0, 2.0 * np.pi, size=n_points)
    r = radius * np.sqrt(rng.uniform(0.0, 1.0, size=n_points))
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return x, y


def make_sphere_patch(n_points: int, rng: np.random.Generator, noise_sigma: float) -> np.ndarray:
    x, y = sample_disk_points(n_points, rng, radius=0.55)
    z = np.sqrt(np.clip(1.0 - x * x - y * y, 0.0, None))
    pts = np.column_stack([x, y, z])
    return pts + rng.normal(scale=noise_sigma, size=pts.shape)


def make_saddle_patch(n_points: int, rng: np.random.Generator, noise_sigma: float) -> np.ndarray:
    x, y = sample_disk_points(n_points, rng, radius=0.9)
    z = 0.65 * (x * x - y * y)
    pts = np.column_stack([x, y, z])
    return pts + rng.normal(scale=noise_sigma, size=pts.shape)


def make_cylinder_patch(n_points: int, rng: np.random.Generator, noise_sigma: float) -> np.ndarray:
    x, y = sample_disk_points(n_points, rng, radius=0.9)
    z = 0.8 * x * x
    pts = np.column_stack([x, y, z])
    return pts + rng.normal(scale=noise_sigma, size=pts.shape)


def make_plane_patch(n_points: int, rng: np.random.Generator, noise_sigma: float) -> np.ndarray:
    x, y = sample_disk_points(n_points, rng, radius=1.0)
    z = np.zeros_like(x)
    pts = np.column_stack([x, y, z])
    return pts + rng.normal(scale=noise_sigma, size=pts.shape)


def make_noise_blob(n_points: int, rng: np.random.Generator, noise_sigma: float) -> np.ndarray:
    scale = max(0.25, 0.55 + noise_sigma)
    return rng.normal(scale=scale, size=(n_points, 3))


SURFACE_GENERATORS: Dict[str, Callable[[int, np.random.Generator, float], np.ndarray]] = {
    "sphere_patch": make_sphere_patch,
    "saddle_patch": make_saddle_patch,
    "cylinder_patch": make_cylinder_patch,
    "plane_patch": make_plane_patch,
    "noise_blob": make_noise_blob,
}


SURFACE_EXPECTATIONS: Dict[str, str] = {
    "sphere_patch": "low saddle fraction, high |shape index|, nonzero curvedness",
    "saddle_patch": "high saddle fraction, shape index near 0",
    "cylinder_patch": "intermediate |shape index|, lower curvedness than sphere",
    "plane_patch": "near-zero curvedness and near-zero grad-II",
    "noise_blob": "poor valid fraction or unstable geometry",
}


def analyze_surface(points: np.ndarray, cfg: Config, *, surface_name: str, noise_sigma: float, repeat_idx: int) -> tuple[pd.DataFrame, Dict[str, float]]:
    anchor_frame = pd.DataFrame(
        {
            "surface": surface_name,
            "noise_sigma": noise_sigma,
            "repeat_idx": repeat_idx,
            "time_hour": np.arange(len(points), dtype=float),
            "run_key": [f"{surface_name}_rep{repeat_idx}"] * len(points),
            "m_coord": points[:, 0],
            "d_coord": points[:, 1],
            "e_coord": points[:, 2],
        }
    )
    patch_rows = [fit_local_quadratic_patch(points, idx, cfg) for idx in range(len(points))]
    anchor_frame = pd.concat([anchor_frame, pd.DataFrame(patch_rows)], axis=1)
    valid = anchor_frame[anchor_frame["status"] == "ok"].copy().reset_index(drop=True)

    summary: Dict[str, float] = {
        "surface": surface_name,
        "noise_sigma": float(noise_sigma),
        "repeat_idx": int(repeat_idx),
        "n_points": int(len(anchor_frame)),
        "laguerre_anchor_count": int(len(valid)),
        "laguerre_valid_fraction": float(len(valid) / max(len(anchor_frame), 1)),
        "laguerre_surface_fit_r2_median": float(np.nanmedian(pd.to_numeric(anchor_frame["surface_fit_r2"], errors="coerce"))),
        "laguerre_s3_over_s2_median": float(np.nanmedian(pd.to_numeric(anchor_frame["s3_over_s2"], errors="coerce"))),
    }
    if valid.empty:
        for key in (
            "laguerre_curvedness_median",
            "laguerre_curvedness_p95",
            "laguerre_shape_index_median",
            "laguerre_shape_index_abs_median",
            "laguerre_saddle_fraction",
            "laguerre_direction_coherence",
            "laguerre_shape_entropy",
            "laguerre_grad_ii_norm_median",
            "laguerre_grad_ii_norm_p95",
            "laguerre_shape_change_norm_median",
            "laguerre_shape_change_norm_p95",
            "laguerre_legacy_change_norm_median",
            "laguerre_legacy_change_norm_p95",
        ):
            summary[key] = float("nan")
        return anchor_frame, summary

    valid["laguerre_grad_ii_norm"] = compute_state_space_gradients(valid, cfg)
    valid["laguerre_shape_change_norm"] = compute_shape_change(valid, cfg)
    valid["laguerre_legacy_change_norm"] = compute_legacy_change(valid, cfg)
    anchor_frame = anchor_frame.merge(
        valid[["time_hour", "laguerre_grad_ii_norm", "laguerre_shape_change_norm", "laguerre_legacy_change_norm"]],
        on="time_hour",
        how="left",
    )

    summary.update(
        {
            "laguerre_shape_index_median": float(np.nanmedian(pd.to_numeric(valid["shape_index"], errors="coerce"))),
            "laguerre_shape_index_abs_median": float(np.nanmedian(np.abs(pd.to_numeric(valid["shape_index"], errors="coerce").to_numpy(dtype=float)))),
            "laguerre_saddle_fraction": float(np.nanmean(pd.to_numeric(valid["saddle_indicator"], errors="coerce"))),
            "laguerre_direction_coherence": compute_direction_coherence(valid),
            "laguerre_shape_entropy": compute_shape_entropy(
                pd.to_numeric(valid["shape_index"], errors="coerce").to_numpy(dtype=float),
                cfg.shape_hist_bins,
            ),
        }
    )
    summary.update(
        summarize_distribution(
            pd.to_numeric(valid["curvedness"], errors="coerce").to_numpy(dtype=float),
            "laguerre_curvedness",
        )
    )
    summary.update(
        summarize_distribution(
            pd.to_numeric(valid["laguerre_grad_ii_norm"], errors="coerce").to_numpy(dtype=float),
            "laguerre_grad_ii_norm",
        )
    )
    summary.update(
        summarize_distribution(
            pd.to_numeric(valid["laguerre_shape_change_norm"], errors="coerce").to_numpy(dtype=float),
            "laguerre_shape_change_norm",
        )
    )
    summary.update(
        summarize_distribution(
            pd.to_numeric(valid["laguerre_legacy_change_norm"], errors="coerce").to_numpy(dtype=float),
            "laguerre_legacy_change_norm",
        )
    )
    return anchor_frame, summary


def write_summary_markdown(summary: pd.DataFrame) -> str:
    lines = [
        "# Laguerre Synthetic Controls",
        "",
        "These controls run the current Laguerre v2b estimator on known synthetic geometries.",
        "",
        "## Expected Patterns",
        "",
    ]
    for surface, expectation in SURFACE_EXPECTATIONS.items():
        lines.append(f"- `{surface}`: {expectation}")
    lines.extend(
        [
            "",
            "## Aggregated Results",
            "",
            "| Surface | Noise | Valid frac | Saddle frac | |Shape index| median | Curvedness median | Grad-II median | Shape entropy |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['surface']} | {row['noise_sigma']:.3f} | {row['laguerre_valid_fraction']:.3f} | "
            f"{row['laguerre_saddle_fraction']:.3f} | {row['laguerre_shape_index_abs_median']:.3f} | "
            f"{row['laguerre_curvedness_median']:.3f} | {row['laguerre_grad_ii_norm_median']:.3f} | "
            f"{row['laguerre_shape_entropy']:.3f} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    synthetic_cfg = parse_args()
    ensure_dir(synthetic_cfg.output_dir)

    anchor_frames: List[pd.DataFrame] = []
    summary_rows: List[Dict[str, float]] = []
    for surface_name, generator in SURFACE_GENERATORS.items():
        for noise_sigma in synthetic_cfg.noise_levels:
            for repeat_idx in range(synthetic_cfg.repeats):
                rng = np.random.default_rng(20260525 + 1000 * repeat_idx + 17 * int(round(noise_sigma * 1000)) + hash(surface_name) % 997)
                points = generator(synthetic_cfg.n_points, rng, noise_sigma)
                anchor_frame, summary = analyze_surface(
                    points,
                    synthetic_cfg.laguerre_config,
                    surface_name=surface_name,
                    noise_sigma=noise_sigma,
                    repeat_idx=repeat_idx,
                )
                anchor_frames.append(anchor_frame)
                summary_rows.append(summary)

    per_repeat = pd.DataFrame(summary_rows)
    aggregate = (
        per_repeat.groupby(["surface", "noise_sigma"], as_index=False)
        .agg(
            laguerre_valid_fraction=("laguerre_valid_fraction", "median"),
            laguerre_surface_fit_r2_median=("laguerre_surface_fit_r2_median", "median"),
            laguerre_s3_over_s2_median=("laguerre_s3_over_s2_median", "median"),
            laguerre_saddle_fraction=("laguerre_saddle_fraction", "median"),
            laguerre_shape_index_median=("laguerre_shape_index_median", "median"),
            laguerre_shape_index_abs_median=("laguerre_shape_index_abs_median", "median"),
            laguerre_curvedness_median=("laguerre_curvedness_median", "median"),
            laguerre_curvedness_p95=("laguerre_curvedness_p95", "median"),
            laguerre_grad_ii_norm_median=("laguerre_grad_ii_norm_median", "median"),
            laguerre_grad_ii_norm_p95=("laguerre_grad_ii_norm_p95", "median"),
            laguerre_shape_change_norm_median=("laguerre_shape_change_norm_median", "median"),
            laguerre_shape_change_norm_p95=("laguerre_shape_change_norm_p95", "median"),
            laguerre_legacy_change_norm_median=("laguerre_legacy_change_norm_median", "median"),
            laguerre_legacy_change_norm_p95=("laguerre_legacy_change_norm_p95", "median"),
            laguerre_direction_coherence=("laguerre_direction_coherence", "median"),
            laguerre_shape_entropy=("laguerre_shape_entropy", "median"),
        )
        .sort_values(["surface", "noise_sigma"])
        .reset_index(drop=True)
    )
    summary_markdown = write_summary_markdown(aggregate)
    manifest = {
        "n_points": synthetic_cfg.n_points,
        "noise_levels": list(synthetic_cfg.noise_levels),
        "repeats": synthetic_cfg.repeats,
        "laguerre_config": {
            "neighborhood_size": synthetic_cfg.laguerre_config.neighborhood_size,
            "gradient_neighbors": synthetic_cfg.laguerre_config.gradient_neighbors,
            "time_change_window": synthetic_cfg.laguerre_config.time_change_window,
            "shape_hist_bins": synthetic_cfg.laguerre_config.shape_hist_bins,
            "s3_over_s2_max": synthetic_cfg.laguerre_config.s3_over_s2_max,
            "surface_fit_r2_min": synthetic_cfg.laguerre_config.surface_fit_r2_min,
        },
        "surfaces": list(SURFACE_GENERATORS),
    }

    pd.concat(anchor_frames, ignore_index=True).to_csv(synthetic_cfg.output_dir / "laguerre_synthetic_anchor_metrics.csv", index=False)
    per_repeat.to_csv(synthetic_cfg.output_dir / "laguerre_synthetic_controls_per_repeat.csv", index=False)
    aggregate.to_csv(synthetic_cfg.output_dir / "laguerre_synthetic_controls_summary.csv", index=False)
    (synthetic_cfg.output_dir / "laguerre_synthetic_controls_summary.md").write_text(summary_markdown, encoding="utf-8")
    (synthetic_cfg.output_dir / "laguerre_synthetic_controls_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote synthetic summary to {synthetic_cfg.output_dir / 'laguerre_synthetic_controls_summary.csv'}")
    print(f"Wrote synthetic markdown to {synthetic_cfg.output_dir / 'laguerre_synthetic_controls_summary.md'}")


if __name__ == "__main__":
    main()
