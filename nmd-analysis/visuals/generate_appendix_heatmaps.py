from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

try:
    from .plotting import set_global_style
except ImportError:
    from plotting import set_global_style


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_DIR = REPO_ROOT / "articles" / "Exteme_NDT" / "results"
LEGACY_RESULTS_DIR = REPO_ROOT / "articles" / "Exteme_NDT" / "v.1.2" / "results"

AXIS_COLUMNS = ["Mean", "Median", "Delta MM", "IQR", "MAD", "Tau"]
STRAT_AXES = ["d_s", "d_l", "d_n", "m_a", "m_e", "m_o", "e_e", "e_s", "e_m"]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _get_stat(data: dict[str, Any] | None, feature: str, stat: str = "p") -> float:
    if data is None or "features" not in data:
        return np.nan
    feature_data = data["features"].get(feature)
    if not isinstance(feature_data, dict):
        return np.nan
    value = feature_data.get(stat, np.nan)
    if isinstance(value, list):
        return np.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def _feature_candidates(prefix: str, axis: str, suffix: str) -> list[str]:
    if prefix == "mnps":
        legacy_axis_map = {"d": "D", "m": "M", "e": "R"}
        candidates = [f"{prefix}_{axis}_{suffix}"]
        legacy_axis = legacy_axis_map.get(axis)
        if legacy_axis:
            candidates.append(f"{prefix}_{legacy_axis}_{suffix}")
        return candidates
    return [f"{prefix}_{axis}_{suffix}"]


def _feature_candidates_for_suffixes(prefix: str, axis: str, suffixes: list[str]) -> list[str]:
    candidates: list[str] = []
    for suffix in suffixes:
        for candidate in _feature_candidates(prefix, axis, suffix):
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates


def _resolve_json(ds_dir: Path, basename: str, contrast: str) -> dict[str, Any] | None:
    candidates = [
        ds_dir / f"{basename}_{contrast}.json",
        ds_dir / f"{basename}_Healthy_{contrast}.json",
    ]
    for candidate in candidates:
        data = _load_json(candidate)
        if data is not None:
            return data
    return None


def _row_data(json_data: dict[str, Any] | None, prefix: str, axis: str) -> dict[str, dict[str, float]]:
    mapping = {
        "Mean": _feature_candidates_for_suffixes(prefix, axis, ["mean"]),
        "Median": _feature_candidates_for_suffixes(prefix, axis, ["median"]),
        "Delta MM": _feature_candidates_for_suffixes(prefix, axis, ["delta_mean_median", "delta_mean_median_manifest"]),
        "IQR": _feature_candidates_for_suffixes(prefix, axis, ["iqr"]),
        "MAD": _feature_candidates_for_suffixes(prefix, axis, ["mad_sigma", "mad_sigma_manifest", "mad"]),
        "Tau": _feature_candidates_for_suffixes(prefix, axis, ["tau_sec", "tau_sec_manifest"]),
    }

    row: dict[str, dict[str, float]] = {}
    for column, candidates in mapping.items():
        p_value = np.nan
        effect_size = np.nan
        for candidate in candidates:
            p_value = _get_stat(json_data, candidate, "p")
            effect_size = _get_stat(json_data, candidate, "cohens_d")
            if not np.isnan(p_value):
                break
        row[column] = {"p": p_value, "d": effect_size}
    return row


def _jacobian_row_data(json_data: dict[str, Any] | None, axis: str) -> dict[str, dict[str, float]]:
    mapping = {
        "Mean": f"block_{axis}_{axis}_frobenius_norm_mean",
        "Median": f"block_{axis}_{axis}_frobenius_norm_median",
        "IQR": f"block_{axis}_{axis}_frobenius_norm_iqr",
        "MAD": f"block_{axis}_{axis}_frobenius_norm_mad",
    }
    return {
        column: {
            "p": _get_stat(json_data, feature, "p"),
            "d": _get_stat(json_data, feature, "cohens_d"),
        }
        for column, feature in mapping.items()
    }


def _annotation_frame(effects: pd.DataFrame, p_values: pd.DataFrame) -> pd.DataFrame:
    annot = pd.DataFrame("", index=effects.index, columns=effects.columns)
    for row in effects.index:
        for column in effects.columns:
            p_value = p_values.loc[row, column]
            effect = effects.loc[row, column]
            if not np.isfinite(p_value):
                continue
            stars = ""
            if p_value < 0.001:
                stars = "***"
            elif p_value < 0.01:
                stars = "**"
            elif p_value < 0.05:
                stars = "*"
            elif p_value < 0.1:
                stars = "dag"
            annot.loc[row, column] = stars if not np.isfinite(effect) else f"{effect:+.2f}{stars}"
    return annot


def generate_heatmap_file(
    data_map: dict[str, dict[str, dict[str, float]]],
    rows: list[str],
    columns: list[str],
    title: str,
    output_path: Path,
    *,
    bold_rows: list[str] | None = None,
) -> Path | None:
    if not data_map:
        print(f"Skipping empty heatmap: {title}")
        return None

    p_frame = pd.DataFrame(index=rows, columns=columns, dtype=float)
    d_frame = pd.DataFrame(index=rows, columns=columns, dtype=float)
    for row in rows:
        for column in columns:
            entry = data_map.get(row, {}).get(column, {})
            p_frame.loc[row, column] = entry.get("p", np.nan)
            d_frame.loc[row, column] = entry.get("d", np.nan)

    annot = _annotation_frame(d_frame, p_frame)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 1.5 + 0.5 * len(rows)))
    sns.heatmap(
        d_frame,
        annot=annot,
        fmt="",
        cmap=sns.diverging_palette(220, 20, as_cmap=True),
        center=0.0,
        linewidths=0.5,
        cbar_kws={"label": "Cohen's d"},
        mask=d_frame.isna(),
    )
    plt.yticks(rotation=0)
    ax = plt.gca()
    if bold_rows:
        for idx, label in enumerate(rows):
            if label in bold_rows:
                ax.get_yticklabels()[idx].set_weight("bold")
                ax.get_yticklabels()[idx].set_fontsize(11)
    plt.title(title, fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Heatmap saved to {output_path}")
    return output_path


def _regional_files(ds_dir: Path, contrast: str) -> list[Path]:
    direct = sorted(ds_dir.glob(f"regional_*{contrast}*.json"))
    if direct:
        return direct
    files = sorted(ds_dir.glob("regional_*.json"))
    return [path for path in files if contrast in path.stem or path.stem.replace("regional_", "") in contrast]


def process_contrast(ds_dir: Path, ds_name: str, contrast: str, output_dir: Path | None = None) -> list[Path]:
    mnps_json = _resolve_json(ds_dir, "mnps", contrast)
    strat_json = _resolve_json(ds_dir, "stratified", contrast)
    block_mnj_json = _resolve_json(ds_dir, "block_mnj", contrast)
    dataset_output_dir = (output_dir / ds_name) if output_dir else ds_dir

    written: list[Path] = []
    global_labels = {
        "MNPS: d": ("mnps", "d", mnps_json),
        "MNPS: m": ("mnps", "m", mnps_json),
        "MNPS: e": ("mnps", "e", mnps_json),
        "Jacobian: d": ("block", "d", block_mnj_json),
        "Jacobian: m": ("block", "m", block_mnj_json),
        "Jacobian: e": ("block", "e", block_mnj_json),
    }
    global_data = {}
    for label, (kind, axis, data) in global_labels.items():
        global_data[label] = _row_data(data, "mnps", axis) if kind == "mnps" else _jacobian_row_data(data, axis)
    out_global = dataset_output_dir / f"heatmap_global_{ds_name}_{contrast}.png"
    result = generate_heatmap_file(
        global_data,
        list(global_labels.keys()),
        AXIS_COLUMNS,
        f"Global Meta-Noetic Dissociations: {contrast}\n({ds_name})",
        out_global,
        bold_rows=["MNPS: d", "Jacobian: d"],
    )
    if result is not None:
        written.append(result)

    strat_rows: list[str] = []
    strat_data: dict[str, dict[str, dict[str, float]]] = {}
    for axis in STRAT_AXES:
        label = f"Stratified: {axis}"
        strat_rows.append(label)
        strat_data[label] = _row_data(strat_json, "v2", axis)
    out_strat = dataset_output_dir / f"heatmap_stratified_{ds_name}_{contrast}.png"
    result = generate_heatmap_file(
        strat_data,
        strat_rows,
        AXIS_COLUMNS,
        f"Stratified Meta-Noetic Dissociations: {contrast}\n({ds_name})",
        out_strat,
    )
    if result is not None:
        written.append(result)

    for regional_file in _regional_files(ds_dir, contrast):
        regional_json = _load_json(regional_file)
        if not regional_json:
            continue
        networks = regional_json.get("networks", [])
        if not networks:
            continue
        regional_columns = ["d_mean", "m_mean", "e_mean", "trace_mean", "frobenius_mean", "rotation_norm_mean", "anisotropy_mean"]
        display_map = {
            "d_mean": "d",
            "m_mean": "m",
            "e_mean": "e",
            "trace_mean": "Trace",
            "frobenius_mean": "Frob",
            "rotation_norm_mean": "Rot",
            "anisotropy_mean": "Aniso",
        }
        regional_data: dict[str, dict[str, dict[str, float]]] = {}
        for network in networks:
            regional_data[network] = {}
            for column in regional_columns:
                feature = f"{network}:{column}"
                feature_data = regional_json.get("features", {}).get(feature, {})
                regional_data[network][display_map[column]] = {
                    "p": feature_data.get("p", np.nan),
                    "d": feature_data.get("cohens_d", np.nan),
                }
        out_regional = dataset_output_dir / f"heatmap_regional_{ds_name}_{regional_file.stem}.png"
        result = generate_heatmap_file(
            regional_data,
            list(networks),
            [display_map[column] for column in regional_columns],
            f"Regional Meta-Noetic Dissociations: {contrast}\n({ds_name})",
            out_regional,
        )
        if result is not None:
            written.append(result)

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate appendix MNPS heatmaps from stable JSON exports.")
    parser.add_argument("--results-dir", type=Path, default=LEGACY_RESULTS_DIR, help="Base results directory containing per-dataset JSON exports.")
    parser.add_argument("--dataset", default="all", help="Dataset folder name or 'all'.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output root. If omitted, heatmaps are written next to the dataset JSON files.",
    )
    args = parser.parse_args()

    set_global_style()
    results_root = args.results_dir.resolve()
    datasets = sorted(path.name for path in results_root.iterdir() if path.is_dir()) if args.dataset == "all" else [args.dataset]

    written = 0
    for dataset in datasets:
        ds_dir = results_root / dataset
        if not ds_dir.is_dir():
            continue
        mnps_files = sorted(path.name for path in ds_dir.glob("mnps_*.json"))
        for filename in mnps_files:
            contrast = filename[5:-5]
            print(f"Processing {dataset} - {contrast}...")
            written += len(process_contrast(ds_dir, dataset, contrast, args.output_dir.resolve() if args.output_dir else None))

    print(f"Generated {written} appendix heatmap files.")


if __name__ == "__main__":
    main()
