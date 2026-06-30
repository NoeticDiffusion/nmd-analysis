from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

try:
    from .generate_appendix_heatmaps import LEGACY_RESULTS_DIR, process_contrast
    from .plotting import set_global_style
except ImportError:
    from generate_appendix_heatmaps import LEGACY_RESULTS_DIR, process_contrast
    from plotting import set_global_style


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "articles" / "Exteme_NDT" / "figures"
SOURCE_HEATMAP_DIR = REPO_ROOT / "nmd-analysis" / "visuals" / "output" / "appendix_heatmaps"


DATASET_SPECS = [
    {
        "dataset": "ds003059",
        "title": "ds003059 heatmap appendix",
        "rows": [
            {
                "label": "LSD vs PLCB",
                "contrast": "Healthy_LSD_vs_Healthy_PLCB",
            }
        ],
    },
    {
        "dataset": "ds003478",
        "title": "ds003478 heatmap appendix",
        "rows": [
            {
                "label": "BDI 0-13 vs BDI 20-63",
                "contrast": "BDI_0_13_vs_BDI_20_63",
            }
        ],
    },
    {
        "dataset": "ds003947",
        "title": "ds003947 heatmap appendix",
        "rows": [
            {
                "label": "Psychosis vs Healthy",
                "contrast": "Psychosis_vs_Healthy",
            }
        ],
    },
    {
        "dataset": "ds004100",
        "title": "ds004100 heatmap appendix",
        "rows": [
            {
                "label": "Ictal vs Interictal",
                "contrast": "Epilepsy_ictal_vs_Epilepsy_interictal",
            }
        ],
    },
    {
        "dataset": "ds004504",
        "title": "ds004504 heatmap appendix",
        "rows": [
            {
                "label": "AD vs Healthy",
                "contrast": "AD_vs_Healthy",
            },
            {
                "label": "FTD vs Healthy",
                "contrast": "FTD_vs_Healthy",
            },
            {
                "label": "AD vs FTD",
                "contrast": "AD_vs_FTD",
            },
        ],
    },
    {
        "dataset": "ds004511",
        "title": "ds004511 heatmap appendix",
        "rows": [
            {
                "label": "Rest vs GG",
                "contrast": "Rest_vs_GG",
            },
            {
                "label": "Rest vs CC",
                "contrast": "Rest_vs_CC",
            },
        ],
    },
    {
        "dataset": "ds005555",
        "title": "ds005555 heatmap appendix",
        "rows": [
            {
                "label": "Awake vs NREM3",
                "contrast": "Healthy_awake_vs_Healthy_nrem3",
            },
            {
                "label": "REM vs NREM3",
                "contrast": "Healthy_rem_vs_Healthy_nrem3",
            },
        ],
    },
    {
        "dataset": "ds005917",
        "title": "ds005917 heatmap appendix",
        "rows": [
            {
                "label": "Healthy baseline vs ketamine_d2",
                "contrast": "Healthy_baseline_vs_Healthy_ketamine_d2",
            },
            {
                "label": "MDD baseline vs ketamine_d2",
                "contrast": "MDD_baseline_vs_MDD_ketamine_d2",
            },
        ],
    },
    {
        "dataset": "ds006623",
        "title": "ds006623 heatmap appendix",
        "rows": [
            {
                "label": "Awake vs Unresponsive",
                "contrast": "Healthy_awake_vs_Healthy_unresponsive",
            },
            {
                "label": "Awake vs Recovery",
                "contrast": "Healthy_awake_vs_Healthy_recovery",
            },
            {
                "label": "Unresponsive vs Recovery",
                "contrast": "Healthy_unresponsive_vs_Healthy_recovery",
            },
        ],
    },
]


def _source_paths(source_root: Path, dataset: str, contrast: str) -> tuple[Path, Path]:
    dataset_dir = source_root / dataset
    return (
        dataset_dir / f"heatmap_global_{dataset}_{contrast}.png",
        dataset_dir / f"heatmap_stratified_{dataset}_{contrast}.png",
    )


def _load_image(image_path: Path):
    if not image_path.exists():
        raise FileNotFoundError(f"Missing source heatmap: {image_path}")
    return mpimg.imread(image_path)


def _wrap_label(value: str) -> str:
    return "\n".join(textwrap.wrap(value, width=26))


def build_panel(
    spec: dict,
    *,
    results_dir: Path,
    source_root: Path,
    output_dir: Path,
    regenerate_sources: bool = True,
) -> Path:
    rows = spec["rows"]
    n_rows = len(rows)
    fig, axes = plt.subplots(
        n_rows,
        2,
        figsize=(13.5, max(4.8 * n_rows, 5.2)),
        constrained_layout=True,
    )
    if n_rows == 1:
        axes = [axes]

    ds_dir = results_dir / spec["dataset"]
    for row_axes, row in zip(axes, rows):
        global_ax, strat_ax = row_axes
        if regenerate_sources:
            process_contrast(ds_dir, spec["dataset"], row["contrast"], source_root)
        global_path, stratified_path = _source_paths(source_root, spec["dataset"], row["contrast"])
        global_ax.imshow(_load_image(global_path))
        strat_ax.imshow(_load_image(stratified_path))
        global_ax.set_title(f"{_wrap_label(row['label'])}\nGlobal (3D)", fontsize=12, pad=8)
        strat_ax.set_title(f"{_wrap_label(row['label'])}\nStratified (9D)", fontsize=12, pad=8)
        global_ax.axis("off")
        strat_ax.axis("off")

    fig.suptitle(spec["title"], fontsize=16, y=1.01)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"mnps_heatmap_panel_{spec['dataset']}.png"
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate MNPS heatmap panels for Extreme NDT.")
    parser.add_argument("--dataset", default="all", help="Dataset id to render, or 'all'.")
    parser.add_argument("--results-dir", type=Path, default=LEGACY_RESULTS_DIR, help="Directory containing per-dataset JSON exports.")
    parser.add_argument("--source-heatmap-dir", type=Path, default=SOURCE_HEATMAP_DIR, help="Cache directory for generated source heatmaps.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Directory for rendered panel PNGs.")
    parser.add_argument("--no-regenerate-sources", action="store_true", help="Reuse existing generated source heatmaps instead of rebuilding them.")
    args = parser.parse_args()

    set_global_style()
    selected_specs = DATASET_SPECS
    if args.dataset != "all":
        selected_specs = [spec for spec in DATASET_SPECS if spec["dataset"] == args.dataset]
        if not selected_specs:
            raise SystemExit(f"Unknown dataset: {args.dataset}")

    written = []
    for spec in selected_specs:
        out_path = build_panel(
            spec,
            results_dir=args.results_dir.resolve(),
            source_root=args.source_heatmap_dir.resolve(),
            output_dir=args.output_dir.resolve(),
            regenerate_sources=not args.no_regenerate_sources,
        )
        written.append(out_path)
        print(f"Wrote {out_path}")

    print(f"Generated {len(written)} MNPS heatmap panels.")


if __name__ == "__main__":
    main()
