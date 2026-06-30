from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yaml

try:
    from .plotting import set_global_style
except ImportError:
    from plotting import set_global_style


COORDINATE_ALIASES: Dict[str, Dict[str, Sequence[str]]] = {
    "M": {
        "metric": ("M", "M_mean", "M_median", "m_mean", "m_median", "mnps_M_mean", "mnps_M_median"),
        "mean": ("M_mean", "m_mean", "mnps_M_mean", "m_mean_from_v2"),
        "std": ("M_std", "m_std", "mnps_M_std"),
    },
    "D": {
        "metric": ("D", "D_mean", "D_median", "d_mean", "d_median", "mnps_D_mean", "mnps_D_median"),
        "mean": ("D_mean", "d_mean", "mnps_D_mean", "d_mean_from_v2"),
        "std": ("D_std", "d_std", "mnps_D_std"),
    },
    "E": {
        "metric": (
            "E",
            "E_mean",
            "E_median",
            "e_mean",
            "e_median",
            "mnps_E_mean",
            "mnps_E_median",
            "R",
            "R_mean",
            "R_median",
            "r_mean",
            "r_median",
            "mnps_R_mean",
            "mnps_R_median",
        ),
        "mean": ("E_mean", "e_mean", "mnps_E_mean", "e_mean_from_v2", "R_mean", "r_mean", "mnps_R_mean"),
        "std": ("E_std", "e_std", "mnps_E_std", "R_std", "r_std", "mnps_R_std"),
    },
}

COORDINATE_TITLES = {
    "M": "M Coordinate",
    "D": "D Coordinate",
    "E": "E Coordinate",
}

ENDPOINT_LABELS = {
    "tube_log_det_median": "Tube Log-Det",
    "frobenius_norm_median": "Frobenius Norm",
    "mnps_M_mean": "MNPS M Mean",
    "v2_e_s_mean": "Stratified e_s Mean",
}

STAGE_ORDER = ["Wake", "awake", "N1", "n1", "N2", "n2", "N3", "n3", "REM", "rem", "SleepPooled", "sleeppooled"]
SUBJECT_COLUMNS = ("subject_id", "subject", "participant_id", "participant")
SUBGROUP_COLUMNS = ("night", "session", "run")
STAGE_COLUMNS = ("stage", "condition")
DEFAULT_CATEGORY_COLUMNS = ("condition", "stage", "group", "task")


class MNPSViolinPlots:
    """Violin-plot generator for legacy JSON and nmd-analysis tables."""

    def __init__(self, output_format: str = "png") -> None:
        set_global_style()
        self.output_format = output_format.lower()
        self.color_config = self._load_color_schemes()
        self.sleep_stage_colors = self._rgb_to_hex(self.color_config.get("sleep_stage_colors", {}))
        self.group_colors = self._rgb_to_hex(self.color_config.get("group_colors", {}))
        self.dataset_colors = self._rgb_to_hex(self.color_config.get("dataset_colors", {}))

    def _save_optimized(self, fig: plt.Figure, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = output_path.with_name(f"{output_path.stem}_temp{output_path.suffix}")
        if self.output_format == "png":
            fig.savefig(temp_path, dpi=145, bbox_inches="tight", format="png", transparent=False)
        else:
            fig.savefig(temp_path, dpi=145, bbox_inches="tight", format="jpg")
        plt.close(fig)
        try:
            from PIL import Image

            with Image.open(temp_path) as img:
                if self.output_format == "png":
                    img.save(output_path, format="PNG", optimize=True)
                else:
                    img.save(output_path, format="JPEG", quality=85, optimize=True)
            temp_path.unlink()
        except ImportError:
            shutil.move(str(temp_path), str(output_path))

    def _load_color_schemes(self) -> Dict[str, Any]:
        config_path = Path(__file__).with_name("color_schemes.yaml")
        if not config_path.exists():
            return {}
        with config_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    @staticmethod
    def _rgb_to_hex(color_dict: Dict[str, Any]) -> Dict[str, str]:
        hex_colors: Dict[str, str] = {}
        for key, rgb in color_dict.items():
            if isinstance(rgb, list) and len(rgb) == 3:
                hex_colors[key] = f"#{int(rgb[0] * 255):02x}{int(rgb[1] * 255):02x}{int(rgb[2] * 255):02x}"
            else:
                hex_colors[key] = str(rgb)
        return hex_colors

    def _category_palette(self, categories: Sequence[str]) -> Dict[str, str]:
        fallback = sns.color_palette("Set2", n_colors=max(3, len(categories)))
        palette_map: Dict[str, str] = {}
        fallback_idx = 0
        for category in categories:
            if category in self.sleep_stage_colors:
                palette_map[category] = self.sleep_stage_colors[category]
            elif category in self.group_colors:
                palette_map[category] = self.group_colors[category]
            else:
                color = fallback[fallback_idx % len(fallback)]
                palette_map[category] = "#{:02x}{:02x}{:02x}".format(
                    int(color[0] * 255),
                    int(color[1] * 255),
                    int(color[2] * 255),
                )
                fallback_idx += 1
        return palette_map

    def plot_coordinate_distributions(
        self,
        frame: pd.DataFrame,
        category_col: str,
        output_path: Path,
        *,
        title: str,
        category_order: Optional[Sequence[str]] = None,
    ) -> None:
        if frame.empty:
            return

        coords = _ordered_coordinates(frame["Coordinate"].unique().tolist())
        if not coords:
            return

        categories = _ordered_categories(frame, category_col, category_order)
        palette_map = self._category_palette(categories)

        fig, axes = plt.subplots(1, len(coords), figsize=(4.6 * len(coords), 4.5))
        if len(coords) == 1:
            axes = [axes]

        for idx, coord in enumerate(coords):
            coord_data = frame[frame["Coordinate"] == coord].copy()
            coord_data[category_col] = coord_data[category_col].astype(str)
            if coord_data.empty:
                continue
            sns.violinplot(
                data=coord_data,
                x=category_col,
                hue=category_col,
                y="Value",
                ax=axes[idx],
                order=categories,
                hue_order=categories,
                palette=palette_map,
                inner="box",
                cut=0,
                linewidth=1.0,
                saturation=0.95,
                legend=False,
            )
            means = coord_data.groupby(category_col)["Value"].mean()
            for point_idx, category in enumerate(categories):
                if category in means.index:
                    axes[idx].scatter(point_idx, means[category], color="#8b1e3f", s=28, zorder=5)
            axes[idx].set_title(COORDINATE_TITLES.get(coord, f"{coord} Coordinate"))
            axes[idx].set_xlabel("")
            axes[idx].set_ylabel("value")
            axes[idx].grid(True, axis="y", alpha=0.25)
            axes[idx].tick_params(axis="x", rotation=35 if any(cat in STAGE_ORDER for cat in categories) else 25)

        fig.suptitle(title, fontsize=15, fontweight="bold")
        fig.tight_layout()
        self._save_optimized(fig, output_path)

    def plot_endpoint_distributions(
        self,
        frame: pd.DataFrame,
        category_col: str,
        output_path: Path,
        *,
        title: str,
        category_order: Optional[Sequence[str]] = None,
    ) -> None:
        if frame.empty:
            return

        metrics = _metric_order(frame["Metric"].unique().tolist())
        categories = _ordered_categories(frame, category_col, category_order)
        palette_map = self._category_palette(categories)

        fig, axes = plt.subplots(1, len(metrics), figsize=(4.2 * len(metrics), 4.7))
        if len(metrics) == 1:
            axes = [axes]

        for idx, metric in enumerate(metrics):
            metric_data = frame[frame["Metric"] == metric].copy()
            metric_data[category_col] = metric_data[category_col].astype(str)
            sns.violinplot(
                data=metric_data,
                x=category_col,
                hue=category_col,
                y="Value",
                ax=axes[idx],
                order=categories,
                hue_order=categories,
                palette=palette_map,
                inner="box",
                cut=0,
                linewidth=1.0,
                saturation=0.95,
                legend=False,
            )
            axes[idx].set_title(_metric_display_name(metric))
            axes[idx].set_xlabel("")
            axes[idx].set_ylabel("value")
            axes[idx].grid(True, axis="y", alpha=0.25)
            axes[idx].tick_params(axis="x", rotation=35)

        fig.suptitle(title, fontsize=15, fontweight="bold")
        fig.tight_layout()
        self._save_optimized(fig, output_path)

    def plot_subject_distributions_grouped(
        self,
        frame: pd.DataFrame,
        output_path: Path,
        *,
        title: str,
    ) -> None:
        if frame.empty or "Subject_ID" not in frame.columns or "Subgroup" not in frame.columns:
            return

        coords = _ordered_coordinates(frame["Coordinate"].unique().tolist())
        subjects = _natural_sort(frame["Subject_ID"].dropna().astype(str).unique().tolist())
        subgroups = _natural_sort(frame["Subgroup"].dropna().astype(str).unique().tolist())
        if not coords or not subjects or len(subgroups) <= 1:
            return

        palette = sns.color_palette("Set2", n_colors=len(subgroups))
        palette_map = dict(zip(subgroups, palette))

        fig, axes = plt.subplots(1, len(coords), figsize=(4.75 * len(coords), 4.75))
        if len(coords) == 1:
            axes = [axes]

        for idx, coord in enumerate(coords):
            coord_data = frame[frame["Coordinate"] == coord].copy()
            coord_data["Subject_ID"] = coord_data["Subject_ID"].astype(str)
            coord_data["Subgroup"] = coord_data["Subgroup"].astype(str)
            sns.violinplot(
                data=coord_data,
                x="Subject_ID",
                y="Value",
                hue="Subgroup",
                ax=axes[idx],
                order=subjects,
                hue_order=subgroups,
                palette=palette_map,
                inner="box",
                cut=0,
            )
            axes[idx].set_title(COORDINATE_TITLES.get(coord, f"{coord} Coordinate"))
            axes[idx].set_xticklabels(subjects, rotation=45, ha="right")
            axes[idx].grid(True, alpha=0.3)
            axes[idx].legend(title="Run/Night", loc="upper right", frameon=True)

        fig.suptitle(title, fontsize=16, fontweight="bold")
        fig.tight_layout()
        self._save_optimized(fig, output_path)


def _ordered_coordinates(coords: Sequence[str]) -> List[str]:
    order = ["M", "D", "E"]
    unique = [str(item) for item in coords if item]
    if set(unique).issubset(set(order)):
        return [item for item in order if item in unique]
    return _natural_sort(unique)


def _metric_order(metrics: Sequence[str]) -> List[str]:
    preferred = list(ENDPOINT_LABELS.keys())
    unique = [str(item) for item in metrics if item]
    ordered = [item for item in preferred if item in unique]
    return ordered + [item for item in _natural_sort(unique) if item not in ordered]


def _ordered_categories(
    frame: pd.DataFrame,
    category_col: str,
    category_order: Optional[Sequence[str]] = None,
) -> List[str]:
    categories = frame[category_col].dropna().astype(str).unique().tolist()
    if category_order:
        preferred = [item for item in category_order if item in categories]
        return preferred + [item for item in categories if item not in preferred]
    stage_preferred = [item for item in STAGE_ORDER if item in categories]
    if stage_preferred:
        return stage_preferred + [item for item in categories if item not in stage_preferred]
    return _natural_sort(categories)


def _natural_sort(values: Iterable[str]) -> List[str]:
    def key(value: str) -> Tuple[Any, ...]:
        parts: List[Any] = []
        chunk = ""
        for char in str(value):
            if char.isdigit():
                chunk += char
            else:
                if chunk:
                    parts.append(int(chunk))
                    chunk = ""
                parts.append(char.lower())
        if chunk:
            parts.append(int(chunk))
        return tuple(parts)

    return sorted(values, key=key)


def _first_existing(columns: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
    available = set(columns)
    for candidate in candidates:
        if candidate in available:
            return candidate
    return None


def _dataset_name(frame: Optional[pd.DataFrame], input_path: Path, dataset_arg: Optional[str]) -> str:
    if dataset_arg:
        return dataset_arg
    if frame is not None:
        for column in ("dataset", "dataset_id"):
            if column in frame.columns:
                values = frame[column].dropna().astype(str)
                if not values.empty:
                    first = values.iloc[0]
                    if ":" in first:
                        return first.split(":", 1)[0]
                    return first
    return input_path.stem


def _metric_to_coordinate(metric: Any) -> Optional[str]:
    metric_text = str(metric)
    for coord, spec in COORDINATE_ALIASES.items():
        if metric_text in spec["metric"]:
            return coord
    return None


def _metric_display_name(metric: str) -> str:
    if metric in ENDPOINT_LABELS:
        return ENDPOINT_LABELS[metric]
    return str(metric).replace("_", " ")


def _mean_std_for_coordinate(row: pd.Series, coord: str) -> Tuple[Optional[float], Optional[float]]:
    spec = COORDINATE_ALIASES[coord]
    mean_column = _first_existing(row.index.tolist(), spec["mean"])
    std_column = _first_existing(row.index.tolist(), spec["std"])
    mean_value = pd.to_numeric(pd.Series([row.get(mean_column)]), errors="coerce").iloc[0] if mean_column else np.nan
    std_value = pd.to_numeric(pd.Series([row.get(std_column)]), errors="coerce").iloc[0] if std_column else np.nan
    if not np.isfinite(mean_value):
        return None, None
    if not np.isfinite(std_value) or std_value <= 0:
        std_value = 0.05
    return float(mean_value), float(std_value)


def _sample_count(row: pd.Series, default: int) -> int:
    for column in ("n_windows", "n_timepoints", "windows"):
        value = pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").iloc[0]
        if np.isfinite(value) and value > 0:
            return max(24, min(int(value), 250))
    return default


def _split_csv_arg(value: Optional[str]) -> Optional[List[str]]:
    if value is None:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def _resolve_category_column(frame: pd.DataFrame, preferred: Optional[str]) -> Optional[str]:
    if preferred and preferred in frame.columns:
        return preferred
    for candidate in DEFAULT_CATEGORY_COLUMNS:
        if candidate in frame.columns:
            return candidate
    return None


def _apply_filters(
    frame: pd.DataFrame,
    *,
    groups: Optional[Sequence[str]],
    conditions: Optional[Sequence[str]],
    tasks: Optional[Sequence[str]],
) -> pd.DataFrame:
    work = frame.copy()
    filter_specs = (
        ("group", groups),
        ("condition", conditions),
        ("stage", conditions),
        ("task", tasks),
    )
    for column, allowed in filter_specs:
        if allowed and column in work.columns:
            work = work[work[column].astype(str).isin(allowed)]
    return work


def _load_input(path: Path) -> Tuple[Optional[pd.DataFrame], Optional[List[Dict[str, Any]]]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            return None, data
        raise ValueError(f"Expected a JSON list in {path}")
    if suffix == ".parquet":
        return pd.read_parquet(path), None
    if suffix == ".csv":
        return pd.read_csv(path), None
    raise ValueError(f"Unsupported input format: {path.suffix}")


def _long_frame_from_json_sleep_stages(data: List[Dict[str, Any]], rng: np.random.Generator) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for entry in data:
        sleep_stages = entry.get("sleep_stages")
        if not isinstance(sleep_stages, dict):
            continue
        for stage, stage_info in sleep_stages.items():
            if not isinstance(stage_info, dict):
                continue
            n_samples = max(24, min(int(stage_info.get("n_windows", 100)), 250))
            for coord in ("M", "D", "E"):
                mean_value, std_value = _mean_std_for_coordinate(pd.Series(stage_info), coord)
                if mean_value is None or std_value is None:
                    continue
                sampled = rng.normal(mean_value, std_value, n_samples)
                for value in sampled:
                    rows.append({"Category": str(stage), "Coordinate": coord, "Value": float(value)})
    return pd.DataFrame(rows)


def _long_frame_from_json_subjects(data: List[Dict[str, Any]], rng: np.random.Generator) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for entry in data:
        stats = entry.get("mnps_stats")
        if not isinstance(stats, dict):
            continue
        subject = str(entry.get("subject_id") or entry.get("subject") or "unknown")
        subgroup = entry.get("night")
        subject_key = f"{subject}_night{subgroup}" if subgroup is not None else subject
        for coord in ("M", "D", "E"):
            mean_value, std_value = _mean_std_for_coordinate(pd.Series(stats), coord)
            if mean_value is None or std_value is None:
                continue
            sampled = rng.normal(mean_value, std_value, 200)
            for value in sampled:
                rows.append(
                    {
                        "Category": subject_key,
                        "Coordinate": coord,
                        "Value": float(value),
                        "Subject_ID": subject,
                        "Subgroup": f"night{subgroup}" if subgroup is not None else "run1",
                    }
                )
    return pd.DataFrame(rows)


def _long_frame_from_metric_table(frame: pd.DataFrame, category_col: str) -> pd.DataFrame:
    work = frame.copy()
    work["Coordinate"] = work["metric"].map(_metric_to_coordinate)
    work = work[work["Coordinate"].notna() & work[category_col].notna()].copy()
    if work.empty:
        return pd.DataFrame()
    work["Category"] = work[category_col].astype(str)
    work["Value"] = pd.to_numeric(work["value"], errors="coerce")
    work = work[np.isfinite(work["Value"])]
    keep = ["Category", "Coordinate", "Value"]
    if "Subject_ID" in work.columns:
        keep.append("Subject_ID")
    if "Subgroup" in work.columns:
        keep.append("Subgroup")
    return work[keep]


def _long_frame_from_wide_table(frame: pd.DataFrame, category_col: str, rng: np.random.Generator) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for _, row in frame.iterrows():
        category = row.get(category_col)
        if pd.isna(category):
            continue
        n_samples = _sample_count(row, default=120)
        for coord in ("M", "D", "E"):
            mean_value, std_value = _mean_std_for_coordinate(row, coord)
            if mean_value is None or std_value is None:
                continue
            sampled = rng.normal(mean_value, std_value, n_samples)
            for value in sampled:
                rows.append({"Category": str(category), "Coordinate": coord, "Value": float(value)})
    return pd.DataFrame(rows)


def _table_subject_frame(frame: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    subject_col = _first_existing(frame.columns.tolist(), SUBJECT_COLUMNS)
    if subject_col is None:
        return pd.DataFrame()
    subgroup_col = _first_existing(frame.columns.tolist(), SUBGROUP_COLUMNS)

    work = frame.copy()
    work["Subject_ID"] = work[subject_col].astype(str)
    if subgroup_col is not None:
        work["Subgroup"] = work[subgroup_col].astype(str)
        work["Category"] = work["Subject_ID"] + "_" + work["Subgroup"]
    else:
        work["Subgroup"] = "run1"
        work["Category"] = work["Subject_ID"]

    if {"metric", "value"}.issubset(work.columns):
        return _long_frame_from_metric_table(work, "Category")

    rows: List[Dict[str, Any]] = []
    group_cols = ["Category", "Subject_ID", "Subgroup"]
    for _, group in work.groupby(group_cols, dropna=False):
        sample_row = group.iloc[0]
        n_samples = _sample_count(sample_row, default=160)
        for coord in ("M", "D", "E"):
            values: List[float] = []
            stds: List[float] = []
            for _, row in group.iterrows():
                mean_value, std_value = _mean_std_for_coordinate(row, coord)
                if mean_value is not None and std_value is not None:
                    values.append(mean_value)
                    stds.append(std_value)
            if not values:
                continue
            sampled = rng.normal(float(np.mean(values)), float(np.mean(stds)), n_samples)
            for value in sampled:
                rows.append(
                    {
                        "Category": str(sample_row["Category"]),
                        "Coordinate": coord,
                        "Value": float(value),
                        "Subject_ID": str(sample_row["Subject_ID"]),
                        "Subgroup": str(sample_row["Subgroup"]),
                    }
                )
    return pd.DataFrame(rows)


def _table_stage_frame(frame: pd.DataFrame, rng: np.random.Generator) -> Tuple[pd.DataFrame, Optional[str]]:
    stage_col = _first_existing(frame.columns.tolist(), STAGE_COLUMNS)
    if stage_col is None:
        return pd.DataFrame(), None
    if {"metric", "value"}.issubset(frame.columns):
        return _long_frame_from_metric_table(frame, stage_col), stage_col
    return _long_frame_from_wide_table(frame, stage_col, rng), stage_col


def _with_subject_metadata(long_frame: pd.DataFrame) -> pd.DataFrame:
    if long_frame.empty or "Category" not in long_frame.columns:
        return long_frame
    if {"Subject_ID", "Subgroup"}.issubset(long_frame.columns):
        return long_frame
    if long_frame["Category"].str.contains("_").any():
        subject_group = long_frame["Category"].str.rsplit("_", n=1, expand=True)
        if subject_group.shape[1] == 2:
            out = long_frame.copy()
            out["Subject_ID"] = subject_group[0]
            out["Subgroup"] = subject_group[1]
            return out
    return long_frame


def _long_frame_from_selected_metrics(
    frame: pd.DataFrame,
    *,
    metrics: Sequence[str],
    category_col: str,
) -> pd.DataFrame:
    if not metrics or category_col not in frame.columns:
        return pd.DataFrame()

    rows: List[Dict[str, Any]] = []
    if {"metric", "value"}.issubset(frame.columns):
        work = frame[frame["metric"].astype(str).isin(metrics)].copy()
        work["Value"] = pd.to_numeric(work["value"], errors="coerce")
        work = work[work[category_col].notna() & np.isfinite(work["Value"])]
        if work.empty:
            return pd.DataFrame()
        return pd.DataFrame(
            {
                "Category": work[category_col].astype(str),
                "Metric": work["metric"].astype(str),
                "Value": work["Value"].astype(float),
            }
        )

    for _, row in frame.iterrows():
        category = row.get(category_col)
        if pd.isna(category):
            continue
        for metric in metrics:
            if metric not in row.index:
                continue
            value = pd.to_numeric(pd.Series([row.get(metric)]), errors="coerce").iloc[0]
            if np.isfinite(value):
                rows.append(
                    {
                        "Category": str(category),
                        "Metric": metric,
                        "Value": float(value),
                    }
                )
    return pd.DataFrame(rows)


def generate_violin_outputs(
    input_paths: Sequence[Path],
    *,
    output_root: Path,
    dataset: Optional[str],
    output_format: str,
    seed: int,
    plot_mode: str,
    metrics: Optional[Sequence[str]],
    category_column: Optional[str],
    category_order: Optional[Sequence[str]],
    groups: Optional[Sequence[str]],
    conditions: Optional[Sequence[str]],
    tasks: Optional[Sequence[str]],
    include_subject_plots: bool,
    title: Optional[str],
    filename: Optional[str],
) -> List[Path]:
    rng = np.random.default_rng(seed)
    plotter = MNPSViolinPlots(output_format=output_format)
    written: List[Path] = []

    frames: List[pd.DataFrame] = []
    json_payloads: List[Tuple[List[Dict[str, Any]], Path]] = []
    dataset_name = dataset or input_paths[0].stem

    for input_path in input_paths:
        frame, data = _load_input(input_path)
        if frame is not None:
            filtered = _apply_filters(frame, groups=groups, conditions=conditions, tasks=tasks)
            frames.append(filtered)
            dataset_name = _dataset_name(filtered, input_path, dataset)
        elif data is not None:
            json_payloads.append((data, input_path))

    target_dir = output_root / dataset_name / "violin"

    endpoint_mode = plot_mode == "endpoints" or (plot_mode == "auto" and metrics)
    if endpoint_mode:
        selected_metrics = list(metrics or [])
        if not selected_metrics:
            discovered: List[str] = []
            for frame in frames:
                for metric in ENDPOINT_LABELS:
                    if ({"metric", "value"}.issubset(frame.columns) and metric in frame["metric"].astype(str).unique()) or (
                        metric in frame.columns
                    ):
                        discovered.append(metric)
            selected_metrics = _metric_order(discovered)
        endpoint_frames: List[pd.DataFrame] = []
        for frame in frames:
            resolved_category_col = _resolve_category_column(frame, category_column)
            if resolved_category_col is None:
                continue
            long_frame = _long_frame_from_selected_metrics(
                frame,
                metrics=selected_metrics,
                category_col=resolved_category_col,
            )
            if not long_frame.empty:
                endpoint_frames.append(long_frame)

        endpoint_frame = pd.concat(endpoint_frames, ignore_index=True) if endpoint_frames else pd.DataFrame()
        if endpoint_frame.empty:
            return written

        output_name = filename or "endpoint_violin"
        endpoint_output = target_dir / f"{output_name}.{plotter.output_format}"
        plotter.plot_endpoint_distributions(
            endpoint_frame,
            "Category",
            endpoint_output,
            title=title or f"{dataset_name}: Endpoint Distributions",
            category_order=category_order,
        )
        written.append(endpoint_output)
        return written

    stage_frame = pd.DataFrame()
    subject_frame = pd.DataFrame()

    if json_payloads:
        stage_rows = []
        subject_rows = []
        for data, _ in json_payloads:
            stage_rows.append(_long_frame_from_json_sleep_stages(data, rng))
            subject_rows.append(_with_subject_metadata(_long_frame_from_json_subjects(data, rng)))
        stage_frame = pd.concat(stage_rows, ignore_index=True) if stage_rows else pd.DataFrame()
        subject_frame = pd.concat(subject_rows, ignore_index=True) if subject_rows else pd.DataFrame()
    elif frames:
        stage_rows = []
        subject_rows = []
        for frame in frames:
            current_stage_frame, _ = _table_stage_frame(frame, rng)
            if not current_stage_frame.empty:
                stage_rows.append(current_stage_frame)
            if include_subject_plots:
                current_subject_frame = _with_subject_metadata(_table_subject_frame(frame, rng))
                if not current_subject_frame.empty:
                    subject_rows.append(current_subject_frame)
        stage_frame = pd.concat(stage_rows, ignore_index=True) if stage_rows else pd.DataFrame()
        subject_frame = pd.concat(subject_rows, ignore_index=True) if subject_rows else pd.DataFrame()

    if not stage_frame.empty:
        stage_output = target_dir / f"{filename or 'mnps_sleep_stages_violin'}.{plotter.output_format}"
        plotter.plot_coordinate_distributions(
            stage_frame,
            "Category",
            stage_output,
            title=title or f"{dataset_name}: MNPS Coordinates by Sleep Stage",
            category_order=category_order or STAGE_ORDER,
        )
        written.append(stage_output)

    if include_subject_plots and not subject_frame.empty:
        subject_output = target_dir / f"mnps_subjects_violin.{plotter.output_format}"
        plotter.plot_coordinate_distributions(
            subject_frame,
            "Category",
            subject_output,
            title=f"{dataset_name}: MNPS Coordinates by Subject",
        )
        written.append(subject_output)

        if {"Subject_ID", "Subgroup"}.issubset(subject_frame.columns) and subject_frame["Subgroup"].nunique() > 1:
            grouped_output = target_dir / f"mnps_subjects_grouped_violin.{plotter.output_format}"
            plotter.plot_subject_distributions_grouped(
                subject_frame,
                grouped_output,
                title=f"{dataset_name}: MNPS Coordinates by Subject (Grouped)",
            )
            written.append(grouped_output)

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate violin plots under visuals/output/<dataset>/violin.")
    parser.add_argument(
        "--input-path",
        action="append",
        required=True,
        help="Path to JSON, CSV, or Parquet input. Repeat the flag to combine multiple files.",
    )
    parser.add_argument("--dataset", help="Override dataset folder name.")
    parser.add_argument(
        "--output-root",
        default=str(Path(__file__).resolve().parent / "output"),
        help="Root output directory. Dataset and violin subfolders are added automatically.",
    )
    parser.add_argument("--output-format", choices=("png", "jpg"), default="png")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--plot-mode", choices=("auto", "coordinates", "endpoints"), default="auto")
    parser.add_argument("--metrics", help="Comma-separated endpoint metrics, e.g. tube_log_det_median,frobenius_norm_median.")
    parser.add_argument("--category-column", help="Column to use on the x-axis, e.g. condition, stage, group, or task.")
    parser.add_argument("--category-order", help="Comma-separated preferred order for x-axis categories.")
    parser.add_argument("--group-filter", help="Comma-separated group filter.")
    parser.add_argument("--condition-filter", help="Comma-separated condition/stage filter.")
    parser.add_argument("--task-filter", help="Comma-separated task filter.")
    parser.add_argument("--subject-plots", action="store_true", help="Also render subject-level violin plots.")
    parser.add_argument("--title", help="Optional figure title override.")
    parser.add_argument("--filename", help="Optional output filename stem.")
    args = parser.parse_args()

    input_paths = [Path(path).resolve() for path in args.input_path]
    output_root = Path(args.output_root).resolve()
    written = generate_violin_outputs(
        input_paths=input_paths,
        output_root=output_root,
        dataset=args.dataset,
        output_format=args.output_format,
        seed=args.seed,
        plot_mode=args.plot_mode,
        metrics=_split_csv_arg(args.metrics),
        category_column=args.category_column,
        category_order=_split_csv_arg(args.category_order),
        groups=_split_csv_arg(args.group_filter),
        conditions=_split_csv_arg(args.condition_filter),
        tasks=_split_csv_arg(args.task_filter),
        include_subject_plots=args.subject_plots,
        title=args.title,
        filename=args.filename,
    )
    if written:
        print("Generated violin plots:")
        for path in written:
            print(f" - {path}")
    else:
        print("No compatible stage or endpoint data found in the provided input.")


if __name__ == "__main__":
    main()
