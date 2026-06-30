from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
import yaml  # noqa: E402

try:
    from .plotting import set_global_style
except ImportError:
    from plotting import set_global_style


REPO_ROOT = Path(__file__).resolve().parents[2]
FIGURES_DIR = (
    REPO_ROOT
    / "articles"
    / "Reachability Cones as Local Capacity Geometry in Noetic Diffusion Theory"
    / "figures"
)
DEFAULT_INPUT_ROOTS = [
    REPO_ROOT / "data" / "analysis",
    REPO_ROOT / "data" / "cleaned",
    REPO_ROOT / "nmd-analysis" / "outputs",
]


def _load_color_schemes() -> Dict[str, Any]:
    config_path = Path(__file__).with_name("color_schemes.yaml")
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _rgb_to_hex(color_dict: Dict[str, Any]) -> Dict[str, str]:
    hex_colors: Dict[str, str] = {}
    for key, rgb in color_dict.items():
        if isinstance(rgb, list) and len(rgb) == 3:
            hex_colors[key] = f"#{int(rgb[0] * 255):02x}{int(rgb[1] * 255):02x}{int(rgb[2] * 255):02x}"
        else:
            hex_colors[key] = str(rgb)
    return hex_colors


COLOR_CONFIG = _load_color_schemes()
GROUP_COLORS = _rgb_to_hex(COLOR_CONFIG.get("group_colors", {}))
STAGE_COLORS = _rgb_to_hex(COLOR_CONFIG.get("sleep_stage_colors", {}))


SPECS: List[Dict[str, Any]] = [
    {
        "dataset": "ds003059",
        "search": [
            "reachability_cones_subjects_ds003059_nomusic.csv",
            "*ds003059*reachability*.csv",
            "*ds003059*reachability*.parquet",
        ],
        "category_col": "condition",
        "category_order": ["PLCB", "LSD"],
        "title": "ds003059: Reachability shape panel (LSD vs placebo; no music)",
        "output": "reachability_shape_panel_ds003059.png",
    },
    {
        "dataset": "ds003478",
        "search": [
            "reachability_cones_subjects_ds003478.csv",
            "*ds003478*reachability*.csv",
            "*ds003478*reachability*.parquet",
        ],
        "category_col": "category",
        "category_order": ["BDI_0_13", "BDI_20_63"],
        "title": "ds003478: Reachability shape panel (BDI bins)",
        "output": "reachability_shape_panel_ds003478.png",
    },
    {
        "dataset": "ds003947",
        "search": [
            "reachability_cones_subjects_ds003947.csv",
            "*ds003947*reachability*.csv",
            "*ds003947*reachability*.parquet",
        ],
        "category_col": "group",
        "category_order": ["Healthy", "FEP"],
        "title": "ds003947: Reachability shape panel (FEP vs Healthy)",
        "output": "reachability_shape_panel_ds003947.png",
    },
    {
        "dataset": "ds004100",
        "search": [
            "reachability_cones_subjects_ds004100_subject_agg.csv",
            "reachability_cones_subjects_ds004100*.csv",
            "*ds004100*reachability*.parquet",
        ],
        "category_col": "condition",
        "category_order": ["interictal", "ictal"],
        "title": "ds004100: Reachability shape panel (ictal vs interictal)",
        "output": "reachability_shape_panel_ds004100.png",
    },
    {
        "dataset": "ds004504",
        "search": [
            "reachability_cones_subjects_ds004504.csv",
            "*ds004504*reachability*.csv",
            "*ds004504*reachability*.parquet",
        ],
        "category_col": "group",
        "category_order": ["Healthy", "AD", "FTD"],
        "title": "ds004504: Reachability shape panel (AD/FTD/Healthy)",
        "output": "reachability_shape_panel_ds004504.png",
    },
    {
        "dataset": "ds004511",
        "search": [
            "reachability_cones_subjects_ds004511_conditioned.csv",
            "reachability_cones_subjects_ds004511*.csv",
            "*ds004511*reachability*.parquet",
        ],
        "category_col": "condition",
        "category_order": ["Rest", "GG", "CC"],
        "title": "ds004511: Reachability shape panel (Rest vs tasks)",
        "output": "reachability_shape_panel_ds004511.png",
    },
    {
        "dataset": "ds005555",
        "search": [
            "reachability_cones_subjects_ds005555_psg_k75_mp3000.csv",
            "reachability_cones_subjects_ds005555*.csv",
            "*ds005555*reachability*.parquet",
        ],
        "category_col": "condition",
        "category_order": ["awake", "nrem2", "nrem3", "rem"],
        "title": "ds005555: Reachability shape panel (sleep stages; PSG-only)",
        "output": "reachability_shape_panel_ds005555.png",
    },
    {
        "dataset": "ds005917",
        "search": [
            "reachability_cones_subjects_ds005917.csv",
            "*ds005917*reachability*.csv",
            "*ds005917*reachability*.parquet",
        ],
        "category_col": "category",
        "category_order": ["Healthy:baseline", "Healthy:ketamine_d2", "MDD:baseline", "MDD:ketamine_d2"],
        "title": "ds005917: Reachability shape panel (Healthy + MDD; baseline vs ketamine_d2)",
        "output": "reachability_shape_panel_ds005917.png",
    },
    {
        "dataset": "ds006623",
        "search": ["ds006623_reachability_cones_*.parquet"],
        "category_col": "condition",
        "category_order": ["awake", "unresponsive", "recovery"],
        "title": "ds006623: Reachability shape panel (awake/unresponsive/recovery)",
        "output": "reachability_shape_panel_ds006623.png",
    },
]


def _final_horizon(df: pd.DataFrame) -> int:
    horizons = []
    for column in df.columns:
        if column.startswith("cone_kappa_h") and column.endswith("_median"):
            horizon = column.replace("cone_kappa_h", "").replace("_median", "")
            if horizon.isdigit():
                horizons.append(int(horizon))
    if not horizons:
        raise ValueError("No cone_kappa_h*_median columns found.")
    return max(horizons)


def _bubble_sizes(series: pd.Series) -> np.ndarray:
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    mask = np.isfinite(values)
    if not mask.any():
        return np.full(values.shape, 120.0)
    lo = float(np.nanmin(values[mask]))
    hi = float(np.nanmax(values[mask]))
    if hi <= lo:
        return np.full(values.shape, 160.0)
    scaled = (values - lo) / (hi - lo)
    return 70.0 + 220.0 * np.clip(scaled, 0.0, 1.0)


def _category_palette(categories: Sequence[str]) -> Dict[str, str]:
    fallback = sns.color_palette("Set2", n_colors=max(3, len(categories)))
    palette: Dict[str, str] = {}
    fallback_idx = 0
    for category in categories:
        if category in STAGE_COLORS:
            palette[category] = STAGE_COLORS[category]
        elif category in GROUP_COLORS:
            palette[category] = GROUP_COLORS[category]
        else:
            color = fallback[fallback_idx % len(fallback)]
            palette[category] = "#{:02x}{:02x}{:02x}".format(
                int(color[0] * 255),
                int(color[1] * 255),
                int(color[2] * 255),
            )
            fallback_idx += 1
    return palette


def _resolve_input_path(spec: Dict[str, Any], input_roots: Sequence[Path]) -> Path:
    input_path = spec.get("csv")
    if input_path is not None:
        candidate = Path(input_path)
        if candidate.is_absolute() and candidate.exists():
            return candidate
        for root in input_roots:
            resolved = (root / candidate).resolve()
            if resolved.exists():
                return resolved
        raise FileNotFoundError(f"Configured input file does not exist for {spec['dataset']}: {candidate}")

    matches: List[Path] = []
    for pattern in spec.get("search", []):
        for root in input_roots:
            if not root.exists():
                continue
            matches.extend(path for path in root.rglob(pattern) if path.is_file())
    if not matches:
        raise FileNotFoundError(
            f"No input file found for {spec['dataset']} under roots: {', '.join(str(p) for p in input_roots)}"
        )
    matches.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0]


def _prepare_frame(spec: Dict[str, Any], input_path: Path) -> pd.DataFrame:
    if input_path.suffix.lower() == ".parquet":
        df = pd.read_parquet(input_path)
    else:
        df = pd.read_csv(input_path)

    if spec["dataset"] == "ds003478":
        # Legacy exports sometimes store raw BDI scores in `group`,
        # while newer subject summaries already store the bin labels.
        scores = pd.to_numeric(df["group"], errors="coerce")
        if scores.notna().any():
            category = pd.Series(pd.NA, index=df.index, dtype="object")
            category.loc[scores <= 13] = "BDI_0_13"
            category.loc[scores >= 20] = "BDI_20_63"
            df = df.assign(category=category)
        else:
            df = df.assign(category=df["group"].astype(str))
        df = df[df["category"].notna()].copy()
    elif spec["dataset"] == "ds003947":
        df = df.copy()
        df["group"] = df["group"].replace({"Control": "Healthy"})
    elif spec["dataset"] == "ds005917":
        df = df[df["group"].isin(["Healthy", "MDD"]) & df["condition"].isin(["baseline", "ketamine_d2"])].copy()
        df["category"] = df["group"].astype(str) + ":" + df["condition"].astype(str)

    category_col = spec["category_col"]
    order = list(spec["category_order"])
    df = df[df[category_col].astype(str).isin(order)].copy()
    df[category_col] = pd.Categorical(df[category_col].astype(str), categories=order, ordered=True)
    return df.sort_values(category_col).reset_index(drop=True)


def _derive_shape_frame(df: pd.DataFrame, final_horizon: int) -> pd.DataFrame:
    endpoint_kappa_col = f"cone_kappa_h{final_horizon}_median"
    endpoint_deff_col = f"cone_d_eff_h{final_horizon}_median"
    required = [endpoint_kappa_col, endpoint_deff_col, "tube_kappa_median", "tube_d_eff_median", "tube_log_det_median", "dims"]
    for column in required:
        if column not in df.columns:
            raise ValueError(f"Missing required column: {column}")

    work = df.copy()
    dims = pd.to_numeric(work["dims"], errors="coerce").clip(lower=1.0)
    endpoint_kappa = pd.to_numeric(work[endpoint_kappa_col], errors="coerce").clip(lower=1.0)
    endpoint_deff = pd.to_numeric(work[endpoint_deff_col], errors="coerce")
    tube_kappa = pd.to_numeric(work["tube_kappa_median"], errors="coerce").clip(lower=1.0)
    tube_deff = pd.to_numeric(work["tube_d_eff_median"], errors="coerce")
    tube_log_det = pd.to_numeric(work["tube_log_det_median"], errors="coerce")

    work["endpoint_ovality_index"] = np.log10(endpoint_kappa)
    work["tube_compactness_ratio"] = np.clip(tube_deff / dims, 0.0, 1.0)
    work["tube_elongation_index"] = np.log10(tube_kappa)
    work["tube_likeness_index"] = work["tube_elongation_index"] * (1.0 - work["tube_compactness_ratio"])
    work["reachability_size"] = tube_log_det
    work["endpoint_compactness_ratio"] = np.clip(endpoint_deff / dims, 0.0, 1.0)
    return work


def _summary_rows(frame: pd.DataFrame, category_col: str, categories: Sequence[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for category in categories:
        sub = frame[frame[category_col].astype(str) == str(category)]
        if sub.empty:
            continue
        rows.append(
            {
                "label": str(category),
                "n": int(len(sub)),
                "endpoint_ovality_index": float(pd.to_numeric(sub["endpoint_ovality_index"], errors="coerce").median()),
                "tube_compactness_ratio": float(pd.to_numeric(sub["tube_compactness_ratio"], errors="coerce").median()),
                "tube_likeness_index": float(pd.to_numeric(sub["tube_likeness_index"], errors="coerce").median()),
                "reachability_size": float(pd.to_numeric(sub["reachability_size"], errors="coerce").median()),
            }
        )
    return rows


def _plot_panel(spec: Dict[str, Any], figures_dir: Path, input_roots: Sequence[Path]) -> Dict[str, Any]:
    input_path = _resolve_input_path(spec, input_roots)
    df = _prepare_frame(spec, input_path)
    final_horizon = _final_horizon(df)
    shape = _derive_shape_frame(df, final_horizon)
    category_col = spec["category_col"]
    categories = [item for item in spec["category_order"] if item in shape[category_col].astype(str).unique()]
    palette = _category_palette(categories)
    sizes = _bubble_sizes(shape["reachability_size"])

    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.25], hspace=0.35, wspace=0.28)
    ax_ovality = fig.add_subplot(gs[0, 0])
    ax_tube = fig.add_subplot(gs[0, 1])
    ax_scatter = fig.add_subplot(gs[1, 0])
    ax_text = fig.add_subplot(gs[1, 1])

    for ax, column, ylabel, title in (
        (ax_ovality, "endpoint_ovality_index", "log10(kappa_H)", f"Endpoint ovality at H={final_horizon}"),
        (ax_tube, "tube_likeness_index", "tube-likeness index", "Tube-like vs compact geometry"),
    ):
        sns.violinplot(
            data=shape,
            x=category_col,
            y=column,
            hue=category_col,
            order=categories,
            hue_order=categories,
            ax=ax,
            inner="box",
            cut=0,
            linewidth=1.0,
            saturation=0.95,
            palette=palette,
            legend=False,
        )
        rng = np.random.default_rng(42)
        for idx, category in enumerate(categories):
            sub = shape[shape[category_col].astype(str) == category]
            values = pd.to_numeric(sub[column], errors="coerce").dropna().to_numpy(dtype=float)
            if values.size == 0:
                continue
            ax.scatter(
                np.full(values.size, idx) + rng.normal(0.0, 0.035, size=values.size),
                values,
                s=18,
                color=palette[category],
                alpha=0.75,
                edgecolor="white",
                linewidth=0.4,
                zorder=4,
            )
        ax.set_title(title)
        ax.set_xlabel("")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", linestyle=":", alpha=0.3)
        ax.tick_params(axis="x", rotation=25)

    for idx, category in enumerate(categories):
        sub = shape[shape[category_col].astype(str) == category]
        if sub.empty:
            continue
        ax_scatter.scatter(
            sub["endpoint_ovality_index"],
            sub["tube_compactness_ratio"],
            s=sizes[sub.index.to_numpy()],
            color=palette[category],
            alpha=0.6,
            edgecolor="white",
            linewidth=0.6,
            label=category,
        )
        ax_scatter.scatter(
            [float(pd.to_numeric(sub["endpoint_ovality_index"], errors="coerce").median())],
            [float(pd.to_numeric(sub["tube_compactness_ratio"], errors="coerce").median())],
            s=220,
            color=palette[category],
            edgecolor="black",
            linewidth=1.2,
            marker="X",
            zorder=5,
        )

    ax_scatter.axhline(0.5, color="#999999", linestyle="--", linewidth=1.0)
    ax_scatter.set_xlabel("Endpoint ovality index: log10(kappa_H)")
    ax_scatter.set_ylabel("Tube compactness ratio: d_eff / dims")
    ax_scatter.set_title("Group shape map\nHigher y = more compact, lower y = more tube-like")
    ax_scatter.grid(True, linestyle=":", alpha=0.25)
    handles, labels = ax_scatter.get_legend_handles_labels()
    if handles:
        ax_scatter.legend(frameon=True, fontsize=9)

    summaries = _summary_rows(shape, category_col, categories)
    ax_text.axis("off")
    notes = [
        f"Final horizon: H={final_horizon}",
        "Ovality index: higher means more anisotropic/oval cone-end.",
        "Compactness ratio: higher means fuller/more isotropic tube volume.",
        "Tube-likeness index: heuristic = log10(tube_kappa) * (1 - compactness).",
        "Bubble size in scatter: median tube_log_det reachability size.",
        "",
    ]
    for row in summaries:
        notes.append(
            f"{row['label']}: n={row['n']}, ovality={row['endpoint_ovality_index']:.2f}, compactness={row['tube_compactness_ratio']:.2f}, tube-likeness={row['tube_likeness_index']:.2f}"
        )
    font_size = 10 if len(summaries) <= 4 else 9
    if len(summaries) >= 6:
        font_size = 8
    ax_text.text(0.0, 1.0, "\n".join(notes), ha="left", va="top", fontsize=font_size)

    fig.suptitle(spec["title"], fontsize=16, y=0.98)
    figures_dir.mkdir(parents=True, exist_ok=True)
    image_path = figures_dir / spec["output"]
    fig.savefig(image_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    payload = {
        "dataset": spec["dataset"],
        "title": spec["title"],
        "input_csv": str(input_path),
        "category_column": category_col,
        "category_order": categories,
        "final_horizon": final_horizon,
        "metric_notes": {
            "endpoint_ovality_index": "log10(cone_kappa_hH_median)",
            "tube_compactness_ratio": "tube_d_eff_median / dims",
            "tube_likeness_index": "log10(tube_kappa_median) * (1 - tube_d_eff_median / dims)",
            "reachability_size": "tube_log_det_median",
        },
        "group_medians": summaries,
        "output_image": str(image_path),
    }
    json_path = image_path.with_suffix(".json")
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"image": str(image_path), "json": str(json_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sleep-style reachability shape panels for manuscript datasets.")
    parser.add_argument("--figures-dir", default=str(FIGURES_DIR))
    parser.add_argument(
        "--input-root",
        action="append",
        default=[],
        help="Optional root directory for dataset table discovery. Can be specified multiple times.",
    )
    args = parser.parse_args()

    set_global_style()
    figures_dir = Path(args.figures_dir).resolve()
    input_roots = [Path(p).resolve() for p in args.input_root] if args.input_root else DEFAULT_INPUT_ROOTS
    written: List[Dict[str, Any]] = []
    for spec in SPECS:
        written.append(_plot_panel(spec, figures_dir, input_roots))

    print("Generated reachability shape panels:")
    for item in written:
        print(f" - {item['image']}")


if __name__ == "__main__":
    main()
