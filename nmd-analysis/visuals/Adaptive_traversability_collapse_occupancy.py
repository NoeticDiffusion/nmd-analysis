#!/usr/bin/env python3
"""
mnps_regime_occupancy.py  –  3D C/TI/P phase-space occupancy visualization.

Renders voxelized occupancy of each brain-state regime in the derived
Capacity-collapse × Transport-innovation × Pathological-lock-in (C/TI/P)
phase space.  The three axes capture the central typological claim in
"Adaptive traversability collapse dissociates low-capacity sleep from
transport-captured unconsciousness".

Each (subject, condition) pair contributes one point.  A Gaussian density
field is built per condition and rendered as nested iso-surface shells.

Usage
-----
    python mnps_regime_occupancy.py
    python mnps_regime_occupancy.py --out path/to/output --grid-size 28 --sigma 0.12
    python mnps_regime_occupancy.py --conditions nrem3,wake,ictal,interictal,sedated,awake
"""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Suppress numexpr / bottleneck import warnings from the system Python
# ---------------------------------------------------------------------------
for _mod_name in ("numexpr", "bottleneck"):
    if _mod_name not in sys.modules:
        _stub = types.ModuleType(_mod_name)
        _stub.__version__ = "2.8.8"
        sys.modules[_mod_name] = _stub

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
pd.set_option("compute.use_bottleneck", False)
pd.set_option("compute.use_numexpr", False)
from scipy.ndimage import gaussian_filter  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = REPO_ROOT / "data" / "analysis"
OUTPUT_DIR = REPO_ROOT / "nmd-analysis" / "visuals" / "output" / "regime_occupancy"

# ---------------------------------------------------------------------------
# Axis definitions  (one representative metric per axis)
# ---------------------------------------------------------------------------
# C  –  Capacity collapse     : higher ATI = more capacity
# TI –  Transport-innovation  : higher Q-ratio = more innovation-dominated
#                                lower Q-ratio = transport-captured
# P  –  Pathological lock-in  : higher ACI = more canalized / locked

AXIS_METRICS = {
    "C":  "ati_reduced",
    "TI": "q_ratio_h4",
    "P":  "aci_median",
}

AXIS_LABELS = {
    "C":  "C  –  Capacity (ATI, z)",
    "TI": "TI  –  Transport-Innovation (Q-ratio H4, z)",
    "P":  "P  –  Pathological Lock-in (ACI, z)",
}

# ---------------------------------------------------------------------------
# Dataset definitions  (name, subject_metrics glob, condition column, optional remap)
#
# remap: dict mapping raw condition strings to display condition keys.
# Used when two datasets share the same condition label (e.g. ANPHY "awake"
# vs Sedation "awake") but should be shown with distinct styles.
# ---------------------------------------------------------------------------
DATASETS = [
    ("ANPHY",                 "ANPHY_subject_metrics_*.parquet",                 "condition",
     {"awake": "wake"}),          # ANPHY calls wakefulness "awake"; remap to "wake"
    ("Sedation-RestingState", "Sedation-RestingState_subject_metrics_*.parquet", "condition",
     {}),
    ("ds004100",              "ds004100_subject_metrics_*.parquet",              "condition",
     {}),
]

# ---------------------------------------------------------------------------
# Visual style  –  grouped by dataset family
# ---------------------------------------------------------------------------
# Blues  = ANPHY sleep stages
# Greens = propofol sedation depth
# Reds   = epilepsy ictal/interictal

CONDITION_STYLES: Dict[str, dict] = {
    # ── ANPHY sleep ──────────────────────────────────────────────────
    "wake":          {"color": (0.30, 0.65, 1.00), "label": "Sleep: Wake",             "marker_z": 0.7},
    "rem":           {"color": (0.10, 0.40, 0.90), "label": "Sleep: REM",              "marker_z": 0.6},
    "nrem2":         {"color": (0.04, 0.22, 0.68), "label": "Sleep: NREM2",            "marker_z": 0.55},
    "nrem3":         {"color": (0.00, 0.08, 0.45), "label": "Sleep: NREM3",            "marker_z": 0.50},
    # ── Propofol sedation ────────────────────────────────────────────
    "awake":         {"color": (0.20, 0.80, 0.35), "label": "Propofol: Awake",         "marker_z": 0.7},
    "sedated":       {"color": (0.08, 0.55, 0.18), "label": "Propofol: Sedated",       "marker_z": 0.6},
    "unresponsive":  {"color": (0.04, 0.32, 0.10), "label": "Propofol: Unresponsive",  "marker_z": 0.55},
    "recovery":      {"color": (0.15, 0.65, 0.28), "label": "Propofol: Recovery",      "marker_z": 0.5},
    # ── Epilepsy ─────────────────────────────────────────────────────
    "interictal":    {"color": (1.00, 0.55, 0.10), "label": "Epilepsy: Interictal",    "marker_z": 0.6},
    "ictal":         {"color": (0.85, 0.08, 0.05), "label": "Epilepsy: Ictal",         "marker_z": 0.75},
}

# Default rendering order (back to front for transparency)
DEFAULT_RENDER_ORDER = [
    "wake", "rem", "awake", "recovery", "nrem2", "interictal",
    "sedated", "nrem3", "unresponsive", "ictal",
]


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def _latest(pattern: str) -> Optional[Path]:
    files = sorted(ANALYSIS_DIR.glob(pattern))
    return files[-1] if files else None


def _pivot_metric(df: pd.DataFrame, metric: str, cond_col: str) -> pd.DataFrame:
    """Return per-(subject_id, condition) median of *metric*."""
    sub = df[df["metric"] == metric][["subject_id", cond_col, "value"]].copy()
    sub = sub.dropna(subset=["value", cond_col])
    return (
        sub.groupby(["subject_id", cond_col])["value"]
        .median()
        .reset_index()
        .rename(columns={"value": metric, cond_col: "condition"})
    )


def _load_dataset_points(
    dataset_name: str,
    glob_pattern: str,
    cond_col: str,
    remap: Optional[Dict[str, str]] = None,
) -> Optional[pd.DataFrame]:
    """Load per-subject C/TI/P coordinates for one dataset."""
    path = _latest(glob_pattern)
    if path is None:
        print(f"[WARN] No subject_metrics found for {dataset_name}  (pattern: {glob_pattern})")
        return None
    df = pd.read_parquet(path)

    # Keep signal rows only (exclude QC / reference roles)
    if "metric_role" in df.columns:
        df = df[df["metric_role"] == "signal"]

    # Coalesce condition from task wherever condition is null.
    # Needed for ds004100 where some analysis types leave condition=None
    # while task carries 'ictal' / 'interictal'.
    if cond_col in df.columns and "task" in df.columns:
        null_mask = df[cond_col].isna()
        if null_mask.any():
            df = df.copy()
            df.loc[null_mask, cond_col] = df.loc[null_mask, "task"]
    elif cond_col not in df.columns and "task" in df.columns:
        df = df.copy()
        df[cond_col] = df["task"]

    frames: List[pd.DataFrame] = []
    for axis_key, metric in AXIS_METRICS.items():
        pf = _pivot_metric(df, metric, cond_col)
        pf = pf.rename(columns={metric: axis_key})
        frames.append(pf)

    if not frames:
        return None

    merged = frames[0]
    for fdf in frames[1:]:
        merged = merged.merge(fdf, on=["subject_id", "condition"], how="inner")

    merged["dataset"] = dataset_name
    merged["condition"] = merged["condition"]
    if remap:
        merged["condition"] = merged["condition"].map(lambda c: remap.get(c, c))
    return merged[["subject_id", "dataset", "condition", "C", "TI", "P"]]


# ---------------------------------------------------------------------------
# Density / voxel helpers
# ---------------------------------------------------------------------------

def _build_density_field(
    pts: np.ndarray,
    grid_size: int,
    gl_min: np.ndarray,
    gl_max: np.ndarray,
    sigma_frac: float,
) -> np.ndarray:
    """
    Convert a point cloud [N, 3] into a smoothed 3-D density field.

    Points are normalized to [0, 1] using the global min/max, binned into a
    histogram, then convolved with a Gaussian.  Returns a (G, G, G) array.
    """
    span = gl_max - gl_min + 1e-9
    pts_norm = np.clip((pts - gl_min) / span, 0.0, 1.0)
    hist, _ = np.histogramdd(pts_norm, bins=grid_size, range=[(0.0, 1.0)] * 3)
    sigma_grid = max(sigma_frac * grid_size, 1.0)
    return gaussian_filter(hist.astype(float), sigma=sigma_grid, mode="nearest")


def _iso_threshold(density: np.ndarray, quantile: float) -> float:
    """Threshold value corresponding to *quantile* of the nonzero voxels."""
    nonzero = density[density > 0]
    if nonzero.size == 0:
        return 0.0
    return float(np.quantile(nonzero, quantile))


def _surface_only(mask: np.ndarray) -> np.ndarray:
    """
    Erode *mask* by one voxel and return only the outer shell.

    Reduces the number of rendered faces from O(N) to O(N^(2/3)),
    making matplotlib ax.voxels() tolerable for grids up to ~20^3.
    """
    from scipy.ndimage import binary_erosion
    interior = binary_erosion(mask, border_value=False)
    return mask & ~interior


def _scatter_coords_normalized(
    pts: np.ndarray,
    grid_size: int,
    gl_min: np.ndarray,
    gl_max: np.ndarray,
) -> np.ndarray:
    """Map raw data points into grid-space [0, grid_size]."""
    span = gl_max - gl_min + 1e-9
    return np.clip((pts - gl_min) / span, 0.0, 1.0) * grid_size


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _apply_axis_formatting(
    ax,
    gl_min: np.ndarray,
    gl_max: np.ndarray,
    grid_size: int,
    fontsize_ticks: int = 7,
    fontsize_labels: int = 8,
) -> None:
    g = grid_size
    ticks = [0, g // 2, g]

    def _lbl(lo: float, hi: float) -> List[str]:
        return [f"{lo:.2f}", f"{(lo + hi) / 2:.2f}", f"{hi:.2f}"]

    ax.set_xticks(ticks)
    ax.set_xticklabels(_lbl(gl_min[0], gl_max[0]), fontsize=fontsize_ticks)
    ax.set_yticks(ticks)
    ax.set_yticklabels(_lbl(gl_min[1], gl_max[1]), fontsize=fontsize_ticks)
    ax.set_zticks(ticks)
    ax.set_zticklabels(_lbl(gl_min[2], gl_max[2]), fontsize=fontsize_ticks)
    ax.set_xlim(0, g)
    ax.set_ylim(0, g)
    ax.set_zlim(0, g)


# Nested iso-surface colour scheme (shared across all conditions).
# Three named layers – each can be toggled via --layers on the CLI:
#   shell  = outermost ring  → green,  very transparent
#   flesh  = middle ring     → yellow, semi-transparent
#   core   = innermost blob  → red,    fully opaque
#
# Each tuple: (layer_name, quantile_boundary, rgb, alpha)
ALL_LAYERS: List[Tuple[str, float, Tuple[float, float, float], float]] = [
    ("shell", 0.40,  (0.22, 0.75, 0.22),  0.18),
    ("flesh", 0.68,  (0.95, 0.84, 0.04),  0.42),
    ("core",  0.88,  (0.85, 0.10, 0.05),  1.00),
]
# Default active layers (can be overridden via --layers shell,core etc.)
DEFAULT_LAYERS = {"shell", "flesh", "core"}


def _draw_condition(
    ax,
    cond: str,
    pts: np.ndarray,
    grid_size: int,
    gl_min: np.ndarray,
    gl_max: np.ndarray,
    sigma_frac: float,
    iso_quantile: float,   # kept for the combined panel (single-shell mode)
    legend_handles: list,
    nested: bool = False,
    active_layers: Optional[set] = None,
) -> None:
    """
    Draw one condition into *ax*.

    nested=False (combined panel): one surface-only shell in the condition colour.
    nested=True  (per-condition):  three nested shells in the shared
                                   green/yellow/red palette + subject scatter.
    """
    import matplotlib.patches as mpatches

    style = CONDITION_STYLES.get(cond, {"color": (0.5, 0.5, 0.5), "label": cond, "marker_z": 0.6})
    density = _build_density_field(pts, grid_size, gl_min, gl_max, sigma_frac)

    if nested:
        # ── non-overlapping annular rings, filtered by active_layers ─────────
        layers = active_layers if active_layers is not None else DEFAULT_LAYERS
        active = [(name, q, rgb, alpha)
                  for name, q, rgb, alpha in ALL_LAYERS
                  if name in layers]

        if not active:
            return

        # Build full masks for ALL layers (needed for ring subtraction even if
        # some layers are not rendered, so geometry stays correct).
        all_masks = {name: density > _iso_threshold(density, q)
                     for name, q, _, _ in ALL_LAYERS}

        # Each ring = its own mask minus the next-denser mask
        layer_names = [n for n, _, _, _ in ALL_LAYERS]
        for i, (name, q, rgb, alpha) in enumerate(ALL_LAYERS):
            if name not in layers:
                continue
            mask = all_masks[name]
            # Subtract denser (inner) mask if it exists
            next_name = layer_names[i + 1] if i + 1 < len(layer_names) else None
            if next_name:
                ring_mask = mask & ~all_masks[next_name]
            else:
                ring_mask = mask   # innermost: use full core
            shell_vox = _surface_only(ring_mask) if ring_mask.any() else ring_mask
            if shell_vox.any():
                rgba = np.zeros((*shell_vox.shape, 4), dtype=float)
                rgba[shell_vox] = [*rgb, alpha]
                ax.voxels(shell_vox, facecolors=rgba, edgecolor="none")

        # ── subject scatter (small, white-outlined) ───────────────────────────
        sc = _scatter_coords_normalized(pts, grid_size, gl_min, gl_max)
        ax.scatter(
            sc[:, 0], sc[:, 1], sc[:, 2],
            color="white", s=18, alpha=0.90,
            edgecolors="0.3", linewidths=0.5, zorder=5,
        )
    else:
        # ── single surface-only shell in condition colour ─────────────────────
        rgb  = style["color"]
        thr  = _iso_threshold(density, iso_quantile)
        shell = _surface_only(density > thr)
        if shell.any():
            rgba = np.zeros((*shell.shape, 4), dtype=float)
            rgba[shell] = [*rgb, 0.55]
            ax.voxels(shell, facecolors=rgba, edgecolor="none")

        sc = _scatter_coords_normalized(pts, grid_size, gl_min, gl_max)
        ax.scatter(sc[:, 0], sc[:, 1], sc[:, 2],
                   color=rgb, s=28, alpha=0.85,
                   edgecolors="white", linewidths=0.4, zorder=5)

        legend_handles.append(mpatches.Patch(color=rgb, label=style["label"], alpha=0.85))


def _render_combined(
    all_points: pd.DataFrame,
    out_path: Path,
    grid_size: int = 16,
    sigma_frac: float = 0.14,
    iso_quantile: float = 0.55,
    conditions_to_show: Optional[List[str]] = None,
    elev: float = 24,
    azim: float = -52,
) -> None:
    """Single 3-D panel: all conditions overlaid in C/TI/P space."""
    if conditions_to_show is None:
        conditions_to_show = [c for c in DEFAULT_RENDER_ORDER if c in all_points["condition"].unique()]

    arr = all_points[["C", "TI", "P"]].to_numpy(dtype=float)
    gl_min = np.nanpercentile(arr, 2, axis=0)
    gl_max = np.nanpercentile(arr, 98, axis=0)
    span = gl_max - gl_min
    gl_min -= 0.10 * span
    gl_max += 0.10 * span

    fig = plt.figure(figsize=(11, 9))
    ax = fig.add_subplot(111, projection="3d")

    legend_handles: List = []
    for cond in conditions_to_show:
        pts = all_points[all_points["condition"] == cond][["C", "TI", "P"]].dropna().to_numpy(dtype=float)
        if pts.shape[0] < 3:
            continue
        _draw_condition(ax, cond, pts, grid_size, gl_min, gl_max, sigma_frac, iso_quantile, legend_handles)

    _apply_axis_formatting(ax, gl_min, gl_max, grid_size)
    ax.set_xlabel(AXIS_LABELS["C"], fontsize=8.5, labelpad=9)
    ax.set_ylabel(AXIS_LABELS["TI"], fontsize=8.5, labelpad=9)
    ax.set_zlabel(AXIS_LABELS["P"], fontsize=8.5, labelpad=9)
    ax.set_title(
        "Regime occupancy in C / TI / P phase space\n(sleep  .  propofol  .  epilepsy)",
        fontsize=11,
        pad=14,
    )
    ax.view_init(elev=elev, azim=azim)
    ax.legend(handles=legend_handles, loc="upper left", bbox_to_anchor=(-0.08, 1.0),
              fontsize=7.5, framealpha=0.75, edgecolor="0.8")

    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved combined panel -> {out_path}")


def _render_per_condition(
    all_points: pd.DataFrame,
    out_dir: Path,
    grid_size: int = 20,
    sigma_frac: float = 0.12,
    iso_quantile: float = 0.55,
    elev: float = 24,
    azim: float = -52,
    active_layers: Optional[set] = None,
) -> None:
    """
    One figure per dataset; within each figure, one 3-D subplot per condition.

    Sleep EEG   → 4 panels: Wake | REM | NREM2 | NREM3
    Propofol    → 4 panels: Awake | Sedated | Unresponsive | Recovery
    Epilepsy    → 2 panels: Interictal | Ictal

    All subplots (and all figures) share the same global C/TI/P bounds so
    that position is directly comparable across stages, depths, and datasets.
    """
    dataset_specs = [
        {
            "dataset":    "ANPHY",
            "conditions": ["wake", "rem", "nrem2", "nrem3"],
            "title":      "Sleep EEG (ANPHY)  –  C / TI / P phase space",
            "filename":   "occupancy_sleep_eeg.png",
        },
        {
            "dataset":    "Sedation-RestingState",
            "conditions": ["awake", "sedated", "unresponsive", "recovery"],
            "title":      "Propofol EEG (Sedation)  –  C / TI / P phase space",
            "filename":   "occupancy_propofol_eeg.png",
        },
        {
            "dataset":    "ds004100",
            "conditions": ["interictal", "ictal"],
            "title":      "Epilepsy iEEG (ds004100)  –  C / TI / P phase space",
            "filename":   "occupancy_epilepsy_ieeg.png",
        },
    ]

    # Shared global bounds across all datasets and conditions
    arr = all_points[["C", "TI", "P"]].to_numpy(dtype=float)
    gl_min = np.nanpercentile(arr, 2, axis=0)
    gl_max = np.nanpercentile(arr, 98, axis=0)
    span = gl_max - gl_min
    gl_min -= 0.10 * span
    gl_max += 0.10 * span

    if active_layers is None:
        active_layers = DEFAULT_LAYERS

    for spec in dataset_specs:
        ds_name   = spec["dataset"]
        cond_list = spec["conditions"]
        n_conds   = len(cond_list)
        ds_pts    = all_points[all_points["dataset"] == ds_name]

        # Figure width scales with number of conditions; height is fixed
        fig = plt.figure(figsize=(5.5 * n_conds, 6))
        fig.suptitle(spec["title"], fontsize=12, y=1.01)

        for col_idx, cond in enumerate(cond_list, start=1):
            ax = fig.add_subplot(1, n_conds, col_idx, projection="3d")
            pts = ds_pts[ds_pts["condition"] == cond][["C", "TI", "P"]].dropna().to_numpy(dtype=float)

            style = CONDITION_STYLES.get(
                cond, {"color": (0.5, 0.5, 0.5), "label": cond, "marker_z": 0.6}
            )

            if pts.shape[0] >= 3:
                _draw_condition(ax, cond, pts, grid_size, gl_min, gl_max,
                                sigma_frac, iso_quantile,
                                legend_handles=[], nested=True,
                                active_layers=active_layers)
                subtitle = f"{style['label']}\n(n = {pts.shape[0]})"
            else:
                subtitle = f"{style['label']}\n(no data)"

            _apply_axis_formatting(ax, gl_min, gl_max, grid_size,
                                   fontsize_ticks=6, fontsize_labels=7)
            ax.set_xlabel("C (ATI, z)",         fontsize=7, labelpad=6)
            ax.set_ylabel("TI (Q-ratio H4, z)", fontsize=7, labelpad=6)
            ax.set_zlabel("P (ACI, z)",         fontsize=7, labelpad=6)
            ax.set_title(subtitle, fontsize=9, pad=6)
            ax.view_init(elev=elev, azim=azim)

            # Density legend on the first subplot only
            if col_idx == 1:
                import matplotlib.patches as mpatches
                layer_labels = {"shell": "Shell", "flesh": "Flesh", "core": "Core"}
                shell_legend = [
                    mpatches.Patch(color=rgb, alpha=min(alpha, 0.9),
                                   label=f"{layer_labels[name]} (p{int(q*100)})")
                    for name, q, rgb, alpha in ALL_LAYERS
                    if name in active_layers
                ]
                ax.legend(handles=shell_legend, loc="upper left",
                          bbox_to_anchor=(-0.15, 1.0), fontsize=6,
                          framealpha=0.75, title="Density", title_fontsize=6)

        plt.tight_layout()
        out_path = out_dir / spec["filename"]
        fig.savefig(out_path, dpi=220, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved {ds_name} panel -> {out_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="3-D C/TI/P regime occupancy visualization")
    p.add_argument("--out", type=str, default=None, help="Output directory (default: visuals/output/regime_occupancy)")
    p.add_argument("--grid-size", type=int, default=24, help="Voxel grid resolution along each axis (default: 24)")
    p.add_argument("--sigma", type=float, default=0.10, help="Gaussian smoothing as fraction of grid (default: 0.10)")
    p.add_argument("--iso-quantiles", type=str, default="0.55", help="Density iso-quantile for the occupancy shell (single float)")
    p.add_argument("--conditions", type=str, default=None, help="Comma-separated conditions to include in combined panel (default: all)")
    p.add_argument("--elev", type=float, default=24, help="Elevation angle for 3-D view")
    p.add_argument("--azim", type=float, default=-52, help="Azimuth angle for 3-D view")
    p.add_argument("--layers", type=str, default="shell,flesh,core",
                   help="Comma-separated density layers to render: shell, flesh, core (default: all three)")
    p.add_argument("--combined-only", action="store_true", help="Render only the combined panel (skip per-condition figures)")
    p.add_argument("--per-dataset-only", action="store_true", help="Render only the per-condition figures (skip combined)")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    out_dir = Path(args.out) if args.out else OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    iso_quantile = float(args.iso_quantiles.split(",")[0].strip())
    active_layers = {l.strip().lower() for l in args.layers.split(",") if l.strip()}
    conditions_filter = [c.strip() for c in args.conditions.split(",")] if args.conditions else None

    # ── Load data ────────────────────────────────────────────────────────────
    frames: List[pd.DataFrame] = []
    for ds_name, glob_pat, cond_col, remap in DATASETS:
        df = _load_dataset_points(ds_name, glob_pat, cond_col, remap=remap)
        if df is not None and not df.empty:
            print(f"  {ds_name}: {len(df)} subject x condition points, conditions={sorted(df['condition'].dropna().unique())}")
            frames.append(df)

    if not frames:
        print("[ERROR] No data loaded.  Check ANALYSIS_DIR:", ANALYSIS_DIR)
        return

    all_points = pd.concat(frames, ignore_index=True)
    all_points = all_points.dropna(subset=["C", "TI", "P"])
    print(f"\nTotal points: {len(all_points)}")

    # ── Z-score normalization across the full pooled sample ──────────────────
    # Puts EEG and iEEG on a common scale so that axis position reflects
    # deviation from the global mean, not raw metric magnitude.
    for axis in ("C", "TI", "P"):
        mu = all_points[axis].mean()
        sd = all_points[axis].std()
        if sd > 0:
            all_points[axis] = (all_points[axis] - mu) / sd
    print("  (axes z-scored across all subjects and datasets)")

    if conditions_filter:
        all_points = all_points[all_points["condition"].isin(conditions_filter)]

    # ── Render ───────────────────────────────────────────────────────────────
    if not args.per_dataset_only:
        _render_combined(
            all_points=all_points,
            out_path=out_dir / "regime_occupancy_combined.png",
            grid_size=args.grid_size,
            sigma_frac=args.sigma,
            iso_quantile=iso_quantile,
            conditions_to_show=conditions_filter,
            elev=args.elev,
            azim=args.azim,
        )

    if not args.combined_only:
        _render_per_condition(
            all_points=all_points,
            out_dir=out_dir,
            grid_size=args.grid_size,
            sigma_frac=args.sigma,
            iso_quantile=iso_quantile,
            elev=args.elev,
            azim=args.azim,
            active_layers=active_layers,
        )

    print("\nDone.")


if __name__ == "__main__":
    main()
