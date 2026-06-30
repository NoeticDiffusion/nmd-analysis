from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import cm  # noqa: E402
from scipy.ndimage import gaussian_filter  # noqa: E402


SUBCOORDINATE_GRID = [
    [("m_a", "Attentional mobility"), ("m_e", "Affective mobility"), ("m_o", "Oscillatory flexibility")],
    [("d_n", "Network diffusivity"), ("d_l", "Local coupling"), ("d_s", "Semantic spread")],
    [("e_e", "Dynamic entropy"), ("e_s", "Phase entropy"), ("e_m", "Efficiency proxy")],
]
SUBCOORDINATE_SPECS = [item for row in SUBCOORDINATE_GRID for item in row]
AXIS_ROW_LABELS = ["Metastability (m)", "Diffusivity (d)", "Entropy (e)"]
AXIS_ROW_BACKGROUNDS = ["#f2f6fd", "#fdf5f0", "#f5f3fd"]
GROUP_STYLES = {"A": {"color": "#2b6cb0", "accent": "#1a4c7a"}, "B": {"color": "#d97706", "accent": "#9c5a04"}}


def _ensure_out(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _slug(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_\-]+", "_", value)
    token = re.sub(r"_+", "_", token).strip("_")
    return token.lower() or "unknown"


def _parse_groups(groups: str) -> Tuple[Dict[str, Optional[str]], Dict[str, Optional[str]]]:
    parts = [part.strip() for part in groups.split(",") if part.strip()]
    if len(parts) != 2:
        raise ValueError("Expected --groups in format 'Group[:Condition],Group[:Condition]'.")

    def _parse(spec: str) -> Dict[str, Optional[str]]:
        tokens = spec.split(":")
        return {"group": tokens[0], "condition": None if len(tokens) == 1 else tokens[1]}

    return _parse(parts[0]), _parse(parts[1])


def _display_name(spec: Dict[str, Optional[str]]) -> str:
    return str(spec["group"]) if spec.get("condition") in (None, "") else f"{spec['group']}:{spec['condition']}"


def _subset_for_spec(df: pd.DataFrame, spec: Dict[str, Optional[str]]) -> pd.DataFrame:
    frame = df[df["group"] == spec["group"]]
    condition = spec.get("condition")
    if condition is not None and "condition" in frame.columns:
        candidate = frame[frame["condition"] == condition]
        if not candidate.empty:
            return candidate
    return frame


def _comparison_label(data: Dict) -> str:
    contrast = data.get("contrast", [])
    return f"{contrast[0]} vs {contrast[1]}" if isinstance(contrast, (list, tuple)) and len(contrast) == 2 else "stratified_mnps"


def _dataset_name(dataset: Optional[str], csv_path: Path, groupdiff_path: Path) -> str:
    if dataset:
        return dataset
    return csv_path.parent.name or groupdiff_path.stem.replace("_group_diff", "")


def _prepare_coordinates(df: pd.DataFrame) -> np.ndarray:
    cols = ["m_mean_from_v2", "d_mean_from_v2", "e_mean_from_v2"]
    if not all(column in df.columns for column in cols):
        cols = ["m_mean", "d_mean", "e_mean"]
    arr = df[cols].to_numpy(dtype=float, copy=True)
    return arr[np.isfinite(arr).all(axis=1)]


def create_density_field(coordinates: np.ndarray, grid_size: int = 32, sigma: float = 0.12) -> np.ndarray:
    if coordinates.size == 0:
        return np.zeros((grid_size, grid_size, grid_size), dtype=float)
    coords_min = coordinates.min(axis=0)
    coords_max = coordinates.max(axis=0)
    coords = (coordinates - coords_min) / (coords_max - coords_min + 1e-9)
    hist, _ = np.histogramdd(coords, bins=grid_size, range=[(0, 1)] * 3)
    return gaussian_filter(hist, sigma=sigma * grid_size, mode="nearest")


def save_slices(vol: np.ndarray, title: str, out_path: Path) -> Path:
    mid = vol.shape[0] // 2
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    planes = [(vol[mid, :, :], "Axial (e)"), (vol[:, mid, :], "Coronal (d)"), (vol[:, :, mid], "Sagittal (m)")]
    for ax, (img, label) in zip(axes, planes):
        im = ax.imshow(img.T, origin="lower", interpolation="bilinear")
        ax.set_title(label)
        ax.axis("off")
    fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.8)
    fig.suptitle(title)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path


def save_voxels(vol: np.ndarray, title: str, out_path: Path, threshold: float = 0.6, reference_volume: Optional[np.ndarray] = None, signed_volume: Optional[np.ndarray] = None) -> Path:
    factor = max(1, int(math.ceil(vol.shape[0] / 48)))
    vol_ds = vol[::factor, ::factor, ::factor]
    signed_ds = signed_volume[::factor, ::factor, ::factor] if signed_volume is not None else None
    base_field = np.abs(signed_ds) if signed_ds is not None else vol_ds
    filled = base_field > threshold
    if not filled.any():
        filled = base_field > max(0.3, threshold - 0.1)
    colors = np.zeros((*vol_ds.shape, 4), dtype=float)
    colorbar_cfg = None
    if signed_ds is not None:
        max_mag = float(np.max(np.abs(signed_ds))) or 1.0
        cmap = matplotlib.colormaps["RdYlBu_r"]
        norm = mcolors.TwoSlopeNorm(vcenter=0.0, vmin=-max_mag, vmax=max_mag)
        colors = cmap(norm(signed_ds))
        colors[..., 3] = np.where(filled, np.clip(np.abs(signed_ds) / max_mag, 0.35, 0.95), 0.0)
        colorbar_cfg = (norm, cmap, "Group B – Group A density")
    elif reference_volume is not None:
        ref_ds = reference_volume[::factor, ::factor, ::factor]
        distance = np.abs(vol_ds - ref_ds)
        max_dist = float(np.max(distance)) or 1.0
        cmap = matplotlib.colormaps["YlOrRd"]
        norm = mcolors.Normalize(vmin=0.0, vmax=max_dist)
        colors = cmap(norm(distance))
        colors[..., 3] = np.where(filled, np.clip(0.35 + 0.55 * (distance / max_dist), 0.35, 0.95), 0.0)
        colorbar_cfg = (norm, cmap, "Distance from comparison")
    else:
        max_val = float(np.max(vol_ds)) or 1.0
        cmap = matplotlib.colormaps["YlGn"]
        norm = mcolors.Normalize(vmin=0.0, vmax=max_val)
        colors = cmap(norm(vol_ds))
        colors[..., 3] = np.where(filled, np.clip(0.35 + 0.55 * (vol_ds / max_val), 0.35, 0.95), 0.0)
    fig = plt.figure(figsize=(7.5, 7.2))
    ax = fig.add_subplot(111, projection="3d")
    ax.voxels(filled, facecolors=colors, edgecolor="k", linewidth=0.1)
    ax.set_title(title, pad=14)
    ax.set_xlabel("m")
    ax.set_ylabel("d")
    ax.set_zlabel("e")
    ax.set_box_aspect(filled.shape)
    ax.view_init(elev=24, azim=-45)
    if colorbar_cfg is not None:
        norm, cmap_obj, label = colorbar_cfg
        sm = cm.ScalarMappable(norm=norm, cmap=cmap_obj)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.1)
        cbar.set_label(label)
        fig.tight_layout(rect=[0.02, 0.02, 0.9, 0.98])
    else:
        fig.tight_layout(rect=[0.02, 0.02, 0.98, 0.98])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return out_path


def _darken_color(color: str, factor: float = 0.8) -> str:
    r, g, b = mcolors.to_rgb(color)
    return mcolors.to_hex((max(min(r * factor, 1.0), 0.0), max(min(g * factor, 1.0), 0.0), max(min(b * factor, 1.0), 0.0)))


def _extract_subcoordinate_values(frame: pd.DataFrame, key: str) -> np.ndarray:
    column = f"v2_{key}_mean"
    if column not in frame.columns:
        return np.zeros(0, dtype=float)
    arr = frame[column].to_numpy(dtype=float, copy=True)
    return arr[np.isfinite(arr)]


def _auto_bins(values: np.ndarray) -> int:
    return 5 if values.size <= 1 else max(6, min(24, int(np.ceil(np.sqrt(values.size)))))


def _compute_value_ranges(frames: Sequence[pd.DataFrame]) -> Dict[str, Tuple[float, float]]:
    ranges: Dict[str, Tuple[float, float]] = {}
    for key, _ in SUBCOORDINATE_SPECS:
        values = [vals for frame in frames if (vals := _extract_subcoordinate_values(frame, key)).size]
        if not values:
            continue
        combined = np.concatenate(values)
        lo = float(np.nanmin(combined))
        hi = float(np.nanmax(combined))
        pad = 0.08 * (hi - lo) if hi > lo else 0.5
        ranges[key] = (lo - pad, hi + pad)
    return ranges


def _render_group_profile_grid(frame: pd.DataFrame, label: str, comparison: str, out_dir: Path, style_key: str, value_ranges: Dict[str, Tuple[float, float]]) -> Optional[Path]:
    style = GROUP_STYLES.get(style_key, GROUP_STYLES["A"])
    color = style["color"]
    accent = _darken_color(style["accent"])
    fig, axes = plt.subplots(3, 3, figsize=(15, 11), sharey=False)
    any_data = False
    for row_idx, row_specs in enumerate(SUBCOORDINATE_GRID):
        for col_idx, (key, title) in enumerate(row_specs):
            ax = axes[row_idx][col_idx]
            vals = _extract_subcoordinate_values(frame, key)
            ax.set_facecolor(AXIS_ROW_BACKGROUNDS[row_idx])
            if vals.size == 0:
                ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center", va="center", fontsize=9, color="#666666")
                ax.set_xticks([])
                ax.set_yticks([])
                continue
            any_data = True
            ax.hist(vals, bins=_auto_bins(vals), color=color, alpha=0.78, edgecolor="#ffffff", linewidth=0.7)
            mean_val = float(np.mean(vals))
            median_val = float(np.median(vals))
            std_val = float(np.std(vals, ddof=1)) if vals.size > 1 else 0.0
            ax.axvline(mean_val, color=accent, linewidth=2.0)
            ax.axvline(median_val, color=accent, linewidth=1.4, linestyle="--")
            ax.text(0.02, 0.95, f"μ={mean_val:.2f}\nmed={median_val:.2f}\nσ={std_val:.2f}\nn={vals.size}", transform=ax.transAxes, ha="left", va="top", fontsize=8, bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "none", "alpha": 0.9})
            if key in value_ranges:
                ax.set_xlim(*value_ranges[key])
            ax.set_title(title, fontsize=11, pad=10.0)
            ax.grid(axis="y", alpha=0.25)
            if col_idx == 0:
                ax.set_ylabel(AXIS_ROW_LABELS[row_idx])
            if row_idx == len(SUBCOORDINATE_GRID) - 1:
                ax.set_xlabel("Feature value")
    if not any_data:
        plt.close(fig)
        return None
    fig.suptitle(f"Stratified MNPS – {label}\n{comparison}", fontsize=16, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out_path = out_dir / f"stratified_mnps_profile_grid_{_slug(comparison)}_{_slug(label)}.png"
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return out_path


def _render_subcoordinate_comparison_grid(frame_a: pd.DataFrame, frame_b: pd.DataFrame, label_a: str, label_b: str, comparison: str, out_dir: Path, value_ranges: Dict[str, Tuple[float, float]], effect_map: Dict[str, Dict]) -> Optional[Path]:
    fig, axes = plt.subplots(3, 3, figsize=(15, 11), sharey=False)
    any_data = False
    style_a = GROUP_STYLES["A"]
    style_b = GROUP_STYLES["B"]
    for row_idx, row_specs in enumerate(SUBCOORDINATE_GRID):
        for col_idx, (key, title) in enumerate(row_specs):
            ax = axes[row_idx][col_idx]
            vals_a = _extract_subcoordinate_values(frame_a, key)
            vals_b = _extract_subcoordinate_values(frame_b, key)
            ax.set_facecolor(AXIS_ROW_BACKGROUNDS[row_idx])
            if vals_a.size == 0 and vals_b.size == 0:
                ax.text(0.5, 0.5, "No data", transform=ax.transAxes, ha="center", va="center", fontsize=9, color="#666666")
                ax.set_xticks([])
                ax.set_yticks([])
                continue
            any_data = True
            groups = [(vals_a, 0.0, style_a), (vals_b, 1.0, style_b)]
            groups = [item for item in groups if item[0].size]
            violin = ax.violinplot([item[0] for item in groups], positions=[item[1] for item in groups], widths=0.82, showmeans=False, showextrema=False, showmedians=False)
            for body, item in zip(violin["bodies"], groups):
                body.set_facecolor(item[2]["color"])
                body.set_alpha(0.4)
                body.set_edgecolor("none")
            box = ax.boxplot([item[0] for item in groups], positions=[item[1] for item in groups], widths=0.28, patch_artist=True, boxprops={"facecolor": "white", "alpha": 0.9, "linewidth": 1.0}, medianprops={"linewidth": 1.4})
            for patch, item in zip(box["boxes"], groups):
                patch.set_edgecolor(item[2]["accent"])
            for median, item in zip(box["medians"], groups):
                median.set_color(item[2]["accent"])
            for values, xpos, style in groups:
                jitter = np.linspace(-0.12, 0.12, values.size) if values.size > 1 else np.array([0.0])
                ax.scatter(np.full(values.size, xpos) + jitter, values, color=style["color"], edgecolors="#ffffff", linewidths=0.4, alpha=0.85, s=18)
            if key in value_ranges:
                ax.set_ylim(*value_ranges[key])
            ax.set_xlim(-0.5, 1.5)
            ax.set_xticks([0, 1])
            ax.set_xticklabels([label_a, label_b], rotation=15, ha="right", fontsize=9)
            ax.grid(axis="y", alpha=0.25)
            if col_idx == 0:
                ax.set_ylabel(AXIS_ROW_LABELS[row_idx])
            effect = effect_map.get(f"v2_{key}_mean", {})
            text = []
            if effect.get("cohens_d") is not None:
                text.append(f"d={float(effect['cohens_d']):.2f}")
            if effect.get("p") is not None:
                text.append(f"p={float(effect['p']):.3g}")
            if text:
                ax.text(0.5, 0.92, "\n".join(text), transform=ax.transAxes, ha="center", va="top", fontsize=8, bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "none", "alpha": 0.85})
            ax.set_title(title, fontsize=11, pad=10.0)
    if not any_data:
        plt.close(fig)
        return None
    fig.suptitle(f"Stratified MNPS comparison\n{comparison}", fontsize=16, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out_path = out_dir / f"stratified_mnps_profile_comparison_{_slug(comparison)}.png"
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return out_path


def generate_outputs(csv_path: Path, group_diff_json: Path, groups: str, dataset: Optional[str], output_root: Path, grid_size: int, sigma: float, voxel_threshold: float) -> List[Path]:
    df = pd.read_csv(csv_path)
    diff = json.loads(group_diff_json.read_text(encoding="utf-8"))
    spec_a, spec_b = _parse_groups(groups)
    frame_a = _subset_for_spec(df, spec_a)
    frame_b = _subset_for_spec(df, spec_b)
    if frame_a.empty or frame_b.empty:
        raise ValueError("One of the requested groups has zero rows after filtering.")
    label_a = _display_name(spec_a)
    label_b = _display_name(spec_b)
    comparison = _comparison_label(diff)
    dataset_name = _dataset_name(dataset, csv_path, group_diff_json)
    density_dir = _ensure_out(output_root / dataset_name / "density")
    voxels_dir = _ensure_out(output_root / dataset_name / "voxels")
    profiles_dir = _ensure_out(output_root / dataset_name / "profile-grid")

    coords_a = _prepare_coordinates(frame_a)
    coords_b = _prepare_coordinates(frame_b)
    vol_a = create_density_field(coords_a, grid_size=grid_size, sigma=sigma)
    vol_b = create_density_field(coords_b, grid_size=grid_size, sigma=sigma)
    if vol_a.max() > 0:
        vol_a = vol_a / vol_a.max()
    if vol_b.max() > 0:
        vol_b = vol_b / vol_b.max()
    diff_vol = vol_b - vol_a
    diff_abs = np.abs(diff_vol)
    if diff_abs.max() > 0:
        diff_abs = diff_abs / diff_abs.max()

    written = [
        save_slices(vol_a, f"{comparison}\nDensity – {label_a}", density_dir / f"stratified_mnps_density_slices_{_slug(comparison)}_{_slug(label_a)}.png"),
        save_slices(vol_b, f"{comparison}\nDensity – {label_b}", density_dir / f"stratified_mnps_density_slices_{_slug(comparison)}_{_slug(label_b)}.png"),
        save_slices(diff_abs, f"{comparison}\nDensity difference (B – A)", density_dir / f"stratified_mnps_density_slices_{_slug(comparison)}_difference.png"),
        save_voxels(vol_a, f"{comparison}\nVoxel density – {label_a}", voxels_dir / f"stratified_mnps_density_voxels_{_slug(comparison)}_{_slug(label_a)}.png", threshold=voxel_threshold),
        save_voxels(vol_b, f"{comparison}\nVoxel density – {label_b}", voxels_dir / f"stratified_mnps_density_voxels_{_slug(comparison)}_{_slug(label_b)}.png", threshold=voxel_threshold, reference_volume=vol_a),
        save_voxels(diff_abs, f"{comparison}\nVoxel density difference (B – A)", voxels_dir / f"stratified_mnps_density_voxels_{_slug(comparison)}_difference.png", threshold=max(0.25, voxel_threshold * 0.6), signed_volume=diff_vol),
    ]

    value_ranges = _compute_value_ranges([frame_a, frame_b])
    for candidate in (
        _render_group_profile_grid(frame_a, label_a, comparison, profiles_dir, "A", value_ranges),
        _render_group_profile_grid(frame_b, label_b, comparison, profiles_dir, "B", value_ranges),
        _render_subcoordinate_comparison_grid(frame_a, frame_b, label_a, label_b, comparison, profiles_dir, value_ranges, diff.get("features", {})),
    ):
        if candidate is not None:
            written.append(candidate)
    summary = {
        "comparison": comparison,
        "dataset": dataset_name,
        "groups": {"A": label_a, "B": label_b},
        "inputs": {"csv": str(csv_path), "group_diff_json": str(group_diff_json)},
        "parameters": {"grid_size": grid_size, "sigma": sigma, "voxel_threshold": voxel_threshold},
        "outputs": [str(path) for path in written],
    }
    summary_path = profiles_dir / f"stratified_mnps_density_summary_{_slug(comparison)}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    written.append(summary_path)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate density/voxel/profile-grid figures under visuals/output/<dataset>/...")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--group-diff-json", required=True)
    parser.add_argument("--groups", required=True)
    parser.add_argument("--dataset")
    parser.add_argument("--grid-size", type=int, default=32)
    parser.add_argument("--sigma", type=float, default=0.12)
    parser.add_argument("--voxel-threshold", type=float, default=0.6)
    parser.add_argument("--output-root", default=str(Path(__file__).resolve().parent / "output"))
    args = parser.parse_args()
    written = generate_outputs(
        csv_path=Path(args.csv).resolve(),
        group_diff_json=Path(args.group_diff_json).resolve(),
        groups=args.groups,
        dataset=args.dataset,
        output_root=Path(args.output_root).resolve(),
        grid_size=args.grid_size,
        sigma=args.sigma,
        voxel_threshold=args.voxel_threshold,
    )
    for path in written:
        print(f" - {path}")


if __name__ == "__main__":
    main()
