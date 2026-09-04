"""Create publication SVGs exclusively from generated ds004587 result files."""
from __future__ import annotations

from pathlib import Path
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ds004587_support import FIGURES_DIR, RESULTS_DIR

def latest_result(name: str) -> Path:
    matches = sorted(RESULTS_DIR.glob(f"ds004587_*/{name}"))
    if not matches:
        raise FileNotFoundError(
            f"Cannot make figures: no generated {name} result directory exists. "
            "Run the relevant analysis script first."
        )
    return matches[-1]

def main() -> None:
    primary_dir = latest_result("03_rest_vs_ig_geometry")
    primary_path = primary_dir / "rest_vs_illusion_paired_tests.csv"
    if not primary_path.exists():
        raise FileNotFoundError(f"Required source result is missing: {primary_path}")
    primary = pd.read_csv(primary_path)
    required = {"metric", "cohen_dz", "p_bh_family"}
    if not required <= set(primary):
        raise ValueError(f"Primary result lacks figure fields: {sorted(required - set(primary))}")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plot = primary.sort_values("cohen_dz").dropna(subset=["cohen_dz"])
    if plot.empty:
        raise ValueError("Primary result contains no finite effect sizes; no figure will be invented.")
    fig, ax = plt.subplots(figsize=(7, max(3, .35 * len(plot) + 1)))
    colors = ["#b2182b" if q < .05 else "#4d4d4d" for q in plot.p_bh_family]
    ax.barh(plot.metric, plot.cohen_dz, color=colors)
    ax.axvline(0, color="black", linewidth=.8)
    ax.set_xlabel("Paired Cohen's $d_z$ (illusion − rest)")
    ax.set_title("Rest-versus-illusion neural geometry")
    fig.text(.01, .01, f"Source: {primary_path.relative_to(RESULTS_DIR)}; red: BH-FDR q < 0.05.",
             fontsize=7)
    fig.tight_layout(rect=(0, .04, 1, 1))
    svg = FIGURES_DIR / "fig_rest_vs_illusion_geometry.svg"
    fig.savefig(svg, format="svg", bbox_inches="tight")
    plt.close(fig)
    manifest = pd.DataFrame([{"figure": svg.name, "source_result": str(primary_path),
                              "caption_source_note": "Effect sizes and BH-FDR status from source result."}])
    manifest.to_csv(FIGURES_DIR / "figure_source_manifest.csv", index=False)
    print(f"Wrote {svg} and figure_source_manifest.csv")

if __name__ == "__main__":
    main()
