from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = REPO_ROOT / "data" / "analysis"
OUTPUT_DIR = REPO_ROOT / "articles" / "Exteme_NDT" / "figures"

TUBE_COLUMNS = ["log_det", "kappa", "log_eig_var", "d_eff"]
TUBE_ROWS = {
    "Tube": "tube_{col}_median",
    "Persistence": "persistence_{col}_median",
    "Pers. tau": "persistence_tau_{col}_median",
    "Pers. hyst.": "persistence_hysteresis_{col}_median",
}

CONE_COLUMNS = ["H1", "H2", "H3", "H4"]
CONE_ROWS = {
    "log_det": "cone_log_det_h{h}_median",
    "kappa": "cone_kappa_h{h}_median",
    "log_eig_var": "cone_log_eig_var_h{h}_median",
    "d_eff": "cone_d_eff_h{h}_median",
    "dir_entropy": "cone_dir_entropy_h{h}_median",
}

DATASET_SPECS = [
    {
        "dataset": "ds003059",
        "title": "ds003059 cone/tube heatmaps",
        "search": ["ds003059_contrast_results_*.parquet"],
        "contrasts": [("Healthy_LSD_vs_Healthy_PLCB", "LSD vs PLCB")],
    },
    {
        "dataset": "ds003478",
        "title": "ds003478 cone/tube heatmaps",
        "search": ["ds003478_contrast_results_*.parquet"],
        "contrasts": [("BDI_0_13_vs_BDI_20_63", "BDI 0-13 vs BDI 20-63")],
    },
    {
        "dataset": "ds003947",
        "title": "ds003947 cone/tube heatmaps",
        "search": ["ds003947_contrast_results_*.parquet"],
        "contrasts": [("Psychosis_vs_Healthy", "Psychosis vs Healthy")],
    },
    {
        "dataset": "ds004100",
        "title": "ds004100 cone/tube heatmaps",
        "search": ["ds004100_contrast_results_*.parquet"],
        "contrasts": [("Epilepsy_ictal_vs_Epilepsy_interictal", "Ictal vs Interictal")],
    },
    {
        "dataset": "ds004504",
        "title": "ds004504 cone/tube heatmaps",
        "search": ["ds004504_contrast_results_*.parquet"],
        "contrasts": [
            ("AD_vs_Healthy", "AD vs Healthy"),
            ("FTD_vs_Healthy", "FTD vs Healthy"),
            ("AD_vs_FTD", "AD vs FTD"),
        ],
    },
    {
        "dataset": "ds004511",
        "title": "ds004511 cone/tube heatmaps",
        "search": ["ds004511_contrast_results_*.parquet"],
        "contrasts": [
            ("Rest_vs_GG", "Rest vs GG"),
            ("Rest_vs_CC", "Rest vs CC"),
        ],
    },
    {
        "dataset": "ds005555",
        "title": "ds005555 cone/tube heatmaps",
        "search": ["ds005555_contrast_results_*.parquet"],
        "contrasts": [
            ("Awake_vs_NREM3", "Awake vs NREM3"),
            ("REM_vs_NREM3", "REM vs NREM3"),
        ],
    },
    {
        "dataset": "ds005917",
        "title": "ds005917 cone/tube heatmaps",
        "search": ["ds005917_contrast_results_*.parquet"],
        "contrasts": [
            ("Healthy_baseline_vs_ketamine_d2", "Healthy baseline vs ketamine_d2"),
            ("MDD_baseline_vs_ketamine_d2", "MDD baseline vs ketamine_d2"),
        ],
    },
    {
        "dataset": "ds006623",
        "title": "ds006623 cone/tube heatmaps",
        "search": [
            "ds006623_contrast_results_*.parquet",
            "*Sedation*contrast_results*.parquet",
            "*RestingState*contrast_results*.parquet",
        ],
        "contrasts": [
            ("Awake_vs_Unresponsive", "Awake vs Unresponsive"),
            ("Awake_vs_Recovery", "Awake vs Recovery"),
            ("Unresponsive_vs_Recovery", "Unresponsive vs Recovery"),
        ],
    },
]


def _candidate_paths(patterns: Iterable[str]) -> list[Path]:
    candidates: list[Path] = []
    for pattern in patterns:
        candidates.extend(sorted(ANALYSIS_DIR.glob(pattern), reverse=True))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in candidates:
        if path not in seen:
            unique.append(path)
            seen.add(path)
    return unique


def _pick_parquet(spec: dict) -> Path | None:
    required = {name for name, _ in spec["contrasts"]}
    for path in _candidate_paths(spec["search"]):
        frame = pd.read_parquet(path, columns=["analysis_type", "contrast_name"])
        reachability = frame[frame["analysis_type"] == "reachability_cones"]
        available = set(reachability["contrast_name"].dropna().astype(str))
        if required.issubset(available):
            return path
    return None


def _load_reachability_frame(parquet_path: Path) -> pd.DataFrame:
    columns = [
        "analysis_type",
        "contrast_name",
        "metric",
        "effect_size",
        "p_value",
        "q_value",
    ]
    frame = pd.read_parquet(parquet_path, columns=columns)
    frame = frame[frame["analysis_type"] == "reachability_cones"].copy()
    frame["contrast_name"] = frame["contrast_name"].astype(str)
    frame["metric"] = frame["metric"].astype(str)
    return frame


def _metric_lookup(frame: pd.DataFrame, contrast_name: str, metric: str) -> tuple[float, float]:
    hit = frame[(frame["contrast_name"] == contrast_name) & (frame["metric"] == metric)]
    if hit.empty:
        return np.nan, np.nan
    row = hit.iloc[0]
    effect = float(row["effect_size"]) if pd.notna(row["effect_size"]) else np.nan
    q_value = float(row["q_value"]) if pd.notna(row["q_value"]) else np.nan
    p_value = float(row["p_value"]) if pd.notna(row["p_value"]) else np.nan
    return effect, q_value if np.isfinite(q_value) else p_value


def _tube_matrix(frame: pd.DataFrame, contrast_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    effects = pd.DataFrame(index=list(TUBE_ROWS.keys()), columns=TUBE_COLUMNS, dtype=float)
    probs = pd.DataFrame(index=list(TUBE_ROWS.keys()), columns=TUBE_COLUMNS, dtype=float)
    for row_label, pattern in TUBE_ROWS.items():
        for col in TUBE_COLUMNS:
            metric = pattern.format(col=col)
            effect, prob = _metric_lookup(frame, contrast_name, metric)
            effects.loc[row_label, col] = effect
            probs.loc[row_label, col] = prob
    return effects, probs


def _cone_matrix(frame: pd.DataFrame, contrast_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    effects = pd.DataFrame(index=list(CONE_ROWS.keys()), columns=CONE_COLUMNS, dtype=float)
    probs = pd.DataFrame(index=list(CONE_ROWS.keys()), columns=CONE_COLUMNS, dtype=float)
    for row_label, pattern in CONE_ROWS.items():
        for horizon_idx, col in enumerate(CONE_COLUMNS, start=1):
            metric = pattern.format(h=horizon_idx)
            effect, prob = _metric_lookup(frame, contrast_name, metric)
            effects.loc[row_label, col] = effect
            probs.loc[row_label, col] = prob
    return effects, probs


def _build_annotation(effects: pd.DataFrame, probs: pd.DataFrame) -> pd.DataFrame:
    annot = pd.DataFrame("", index=effects.index, columns=effects.columns)
    for row in effects.index:
        for col in effects.columns:
            effect = effects.loc[row, col]
            prob = probs.loc[row, col]
            if not np.isfinite(effect):
                continue
            stars = ""
            if np.isfinite(prob):
                if prob < 0.001:
                    stars = "***"
                elif prob < 0.01:
                    stars = "**"
                elif prob < 0.05:
                    stars = "*"
                elif prob < 0.1:
                    stars = "dag"
            annot.loc[row, col] = f"{effect:+.2f}{stars}"
    return annot


def _plot_heatmap(
    ax: plt.Axes,
    effects: pd.DataFrame,
    probs: pd.DataFrame,
    *,
    title: str,
    vlim: float,
) -> None:
    annot = _build_annotation(effects, probs)
    sns.heatmap(
        effects,
        ax=ax,
        cmap=sns.diverging_palette(240, 20, as_cmap=True),
        center=0.0,
        vmin=-vlim,
        vmax=vlim,
        annot=annot,
        fmt="",
        mask=effects.isna(),
        linewidths=0.4,
        cbar=False,
    )
    ax.set_title(title, fontsize=11, pad=8)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)


def build_panel(spec: dict, output_dir: Path) -> Path | None:
    parquet_path = _pick_parquet(spec)
    if parquet_path is None:
        print(f"Skipping {spec['dataset']}: no contrast_results parquet with reachability_cones rows.")
        return None

    frame = _load_reachability_frame(parquet_path)
    contrasts = spec["contrasts"]
    n_rows = len(contrasts)
    fig, axes = plt.subplots(
        n_rows,
        2,
        figsize=(12.5, max(4.6 * n_rows, 5.4)),
        constrained_layout=True,
    )
    if n_rows == 1:
        axes = np.array([axes])

    max_abs = 1.0
    panel_data = []
    for contrast_name, display_label in contrasts:
        tube_effects, tube_probs = _tube_matrix(frame, contrast_name)
        cone_effects, cone_probs = _cone_matrix(frame, contrast_name)
        values = np.concatenate(
            [
                tube_effects.to_numpy(dtype=float).ravel(),
                cone_effects.to_numpy(dtype=float).ravel(),
            ]
        )
        finite = values[np.isfinite(values)]
        if finite.size:
            max_abs = max(max_abs, float(np.nanmax(np.abs(finite))))
        panel_data.append((display_label, tube_effects, tube_probs, cone_effects, cone_probs))

    vlim = min(max(1.0, np.ceil(max_abs * 1.05)), 4.0)

    for row_axes, (display_label, tube_effects, tube_probs, cone_effects, cone_probs) in zip(axes, panel_data):
        tube_ax, cone_ax = row_axes
        _plot_heatmap(
            tube_ax,
            tube_effects,
            tube_probs,
            title=f"{display_label}\nTube / persistence",
            vlim=vlim,
        )
        _plot_heatmap(
            cone_ax,
            cone_effects,
            cone_probs,
            title=f"{display_label}\nCone horizons",
            vlim=vlim,
        )

    sm = plt.cm.ScalarMappable(cmap=sns.diverging_palette(240, 20, as_cmap=True))
    sm.set_clim(-vlim, vlim)
    fig.colorbar(sm, ax=axes, shrink=0.92, pad=0.02, label="Effect size")
    fig.suptitle(spec["title"], fontsize=16, y=1.02)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"cone_tube_heatmap_panel_{spec['dataset']}.png"
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate cone/tube heatmap panels for Extreme NDT.")
    parser.add_argument("--dataset", default="all", help="Dataset id to render, or 'all'.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Directory for generated PNG panels.")
    args = parser.parse_args()

    selected_specs = DATASET_SPECS
    if args.dataset != "all":
        selected_specs = [spec for spec in DATASET_SPECS if spec["dataset"] == args.dataset]
        if not selected_specs:
            raise SystemExit(f"Unknown dataset: {args.dataset}")

    written = 0
    for spec in selected_specs:
        if build_panel(spec, args.output_dir) is not None:
            written += 1
    print(f"Generated {written} cone/tube heatmap panels.")


if __name__ == "__main__":
    main()
