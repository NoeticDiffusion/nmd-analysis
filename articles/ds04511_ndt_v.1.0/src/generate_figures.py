"""Generate reproducible SVG/PNG figures from the frozen ds004511 result tables.

This script is descriptive: it never recomputes estimators or changes the
eligible samples.  It keeps chart-Jacobian, identified one-step L2/L3, and L4
certificate QC visually separate.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ARTICLE = Path(__file__).resolve().parents[1]
LEVEL = ARTICLE / "results" / "v1_level_20260921"
L4 = ARTICLE / "results" / "v1_l4_qc_20260921"
OUT = ARTICLE / "figures" / "results"

COLORS = {"jacobian_alpha": "#007c83", "L2": "#5c5aa8", "L3": "#c26b2b"}


def save(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for suffix in ("svg", "png"):
        fig.savefig(OUT / f"{stem}.{suffix}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def contrast_dissociation() -> None:
    df = pd.read_csv(LEVEL / "level_contrasts.csv")
    gg = df[df["contrast_id"].eq("gambling_minus_rest")].copy()
    selected = gg[gg["metric"].isin([
        "jacobian_alpha", "one_step_spectral_abscissa",
        "operator_rotation_rate", "one_step_generator_rotation_norm",
    ])].copy()
    order = ["jacobian_alpha", "one_step_spectral_abscissa", "operator_rotation_rate", "one_step_generator_rotation_norm"]
    selected["metric"] = pd.Categorical(selected["metric"], categories=order, ordered=True)
    selected = selected.sort_values("metric")
    label_map = {
        "jacobian_alpha": "Chart-Jacobian α\n(local chart; n=44)",
        "one_step_spectral_abscissa": "One-step L3 α\n(generator proxy; n=32)",
        "operator_rotation_rate": "L2 rotation\n(identified; n=32)",
        "one_step_generator_rotation_norm": "L3 generator rotation\n(identified; n=32)",
    }
    selected["label"] = selected["metric"].map(label_map)
    colors = [COLORS["jacobian_alpha"], COLORS["L3"], COLORS["L2"], COLORS["L3"]]
    fig, ax = plt.subplots(figsize=(11.2, 5.6))
    bars = ax.barh(selected["label"], selected["cohens_dz"], color=colors)
    ax.axvline(0, color="#222222", lw=0.8)
    ax.set_xlabel("Paired effect size $d_z$ (Gambling − Rest)")
    ax.set_title("Exploratory estimator dissociation: separate complete-case samples")
    for bar, (_, row) in zip(bars, selected.iterrows()):
        value = bar.get_width()
        if value < 0:
            # Keep negative-bar annotations inside their own bars so they do
            # not collide with the L2/L3 category labels on the left.
            x, ha, color = value / 2, "center", "white"
            annotation = f"q={row.bh_q:.3g}"
        else:
            x, ha, color = value + 0.04, "left", "#111111"
            annotation = f"n={int(row.n_pairs)}, q={row.bh_q:.3g}"
        ax.text(x, bar.get_y() + bar.get_height() / 2,
                annotation,
                va="center", ha=ha, fontsize=8.5, color=color, fontweight="medium")
    ax.text(0.01, -0.19,
            "Chart-Jacobian α and one-step L3 α are distinct estimators. The bars do not test an effect-size difference.\n"
            "L3 α is the spectral abscissa of log(Φ)/dt on identified lag-1 support; q is the global 36-test Wilcoxon family.",
            transform=ax.transAxes, fontsize=8.5, va="top")
    fig.subplots_adjust(left=0.30, right=0.95, bottom=0.25, top=0.90)
    save(fig, "ds004511_gg_rest_estimator_dissociation_20260921")


def l4_qc() -> None:
    missing = pd.read_csv(L4 / "l4_missing_certificates.csv")
    task = missing["stem"].str.extract(r"_(rest|cognitive_control|gambling)_", expand=False)
    counts = task.value_counts().reindex(["rest", "cognitive_control", "gambling"], fill_value=0)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.8), gridspec_kw={"width_ratios": [1, 1.35]})
    ax1.bar(["Rest", "CC", "GG"], counts.values, color="#c26b2b")
    ax1.set_ylim(0, 1.25)
    ax1.set_ylabel("Invalid L4 certificates")
    ax1.set_title("One invalid record per task")
    for i, value in enumerate(counts.values):
        ax1.text(i, value + 0.04, str(int(value)), ha="center")
    ax2.axis("off")
    ax2.text(0, 0.83, "L4 QC boundary", fontsize=15, fontweight="bold", color="#c26b2b")
    ax2.text(0, 0.59, "3 / 134 missing finite reach_a_q", fontsize=12)
    ax2.text(0, 0.41, "All: post_dtype_psd_failure at gate F\nDifferent subjects; not a task dropout.", fontsize=10)
    ax2.text(0, 0.13, "reach_d_eff is not plotted as a task contrast:\n109 / 131 finite values are within 1e-6 of 1.", fontsize=10, color="#333333")
    fig.suptitle("L4 certificate audit — exploratory QC, not reachability validation", x=0.43, y=1.02)
    save(fig, "ds004511_l4_certificate_qc_20260921")


def main() -> None:
    contrast_dissociation()
    l4_qc()
    print(f"Wrote SVG and PNG figures to {OUT}")


if __name__ == "__main__":
    main()
