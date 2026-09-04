"""Generate conceptual SVG and PNG figures for the NDT_2 theory manuscript.

These are schematics, not empirical plots. They are intentionally generated
from code so their labels, panel ordering, and output formats remain
reproducible.

Usage:
    python articles/NDT_2/src/make_conceptual_figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


ARTICLE = Path(__file__).resolve().parents[1]
FIGURES = ARTICLE / "figures" / "conceptual"

COLORS = {
    "metabolic": "#2E7D32",
    "meso": "#1565C0",
    "bridge": "#6A1B9A",
    "macro": "#EF6C00",
    "eap": "#C62828",
    "neutral": "#455A64",
    "light": "#F4F6F8",
}

matplotlib.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 11,
        "svg.fonttype": "none",
    }
)


def save(fig: plt.Figure, name: str) -> None:
    """Write matching vector and raster outputs."""
    FIGURES.mkdir(parents=True, exist_ok=True)
    for extension, dpi in (("svg", None), ("png", 300)):
        output = FIGURES / f"{name}.{extension}"
        fig.savefig(output, format=extension, dpi=dpi, bbox_inches="tight")
        print(f"Saved {output.relative_to(ARTICLE)}")
    plt.close(fig)


def add_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    text: str,
    color: str,
    *,
    fontsize: float = 8.5,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.035",
        linewidth=1.25,
        edgecolor=color,
        facecolor="white",
    )
    ax.add_patch(patch)
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color="#1F2933",
        wrap=True,
    )


def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={"arrowstyle": "->", "lw": 1.25, "color": COLORS["neutral"]},
    )


def clean(ax: plt.Axes) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def make_scale_ladder() -> None:
    fig, ax = plt.subplots(figsize=(10, 3.8))
    clean(ax)
    nodes = [
        (0.03, "Metabolic adequacy\nslow boundary condition", "metabolic"),
        (0.225, "TRN / thalamocortical\ngating hypothesis", "meso"),
        (0.42, "Meso observables\nLFP, spiking, dimensionality", "meso"),
        (0.615, "Meso--macro bridge\nassociation + nulls", "bridge"),
        (0.81, "MNPS / MNDM\nmacro chart and dynamics", "macro"),
    ]
    for x, label, color in nodes:
        add_box(ax, x, 0.51, 0.155, 0.22, label, COLORS[color])
    for index in range(len(nodes) - 1):
        arrow(ax, (nodes[index][0] + 0.157, 0.62), (nodes[index + 1][0] - 0.003, 0.62))
    add_box(
        ax,
        0.395,
        0.12,
        0.22,
        0.18,
        "Fast EAP anchors\ncardiac, respiratory, HEP",
        COLORS["eap"],
    )
    arrow(ax, (0.505, 0.30), (0.505, 0.49))
    ax.text(
        0.5,
        0.91,
        "NDT_2 conceptual scale ladder: constraints, measurements, and inferred dynamics",
        ha="center",
        fontsize=11,
        weight="bold",
    )
    ax.text(
        0.5,
        0.39,
        "Arrows are proposed dependencies; only selected bridge associations are currently measured.",
        ha="center",
        fontsize=8,
        color=COLORS["neutral"],
    )
    save(fig, "fig1_scale_ladder")


def make_recoverability_ladder() -> None:
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    clean(ax)
    add_box(ax, 0.06, 0.67, 0.21, 0.17, "Latent process\n$X_t$", COLORS["neutral"])
    add_box(ax, 0.39, 0.67, 0.21, 0.17, "Measurement\n$Y_t = g(X_t)+\\epsilon_t$", COLORS["meso"])
    add_box(ax, 0.72, 0.67, 0.21, 0.17, "Operational chart\n$z_t=C(\\Psi(X_t))$", COLORS["macro"])
    arrow(ax, (0.275, 0.755), (0.385, 0.755))
    arrow(ax, (0.605, 0.755), (0.715, 0.755))
    levels = [
        ("1", "Association", "Observable covaries\nwith another quantity"),
        ("2", "Mechanism discrimination", "Observations separate\nmatched-output models"),
        ("3", "Latent-order preservation", "Observable ordering tracks\na declared latent summary"),
        ("4", "Operator identification", "Response-generating local\noperator is validated"),
    ]
    for index, (number, title, detail) in enumerate(levels):
        y = 0.49 - index * 0.12
        ax.text(0.08, y + 0.035, number, ha="center", va="center", weight="bold", color="white",
                bbox={"boxstyle": "circle,pad=0.32", "fc": COLORS["bridge"], "ec": COLORS["bridge"]})
        ax.text(0.15, y + 0.05, title, weight="bold", va="center")
        ax.text(0.42, y + 0.05, detail, va="center", color=COLORS["neutral"])
        if index < len(levels) - 1:
            arrow(ax, (0.08, y - 0.002), (0.08, y - 0.07))
    ax.text(
        0.5,
        0.08,
        "A correlation or visually plausible embedding licenses Level 1 only; Jacobian/reachability claims require Level 4 plus estimator-quality checks.",
        ha="center",
        fontsize=8,
        color=COLORS["neutral"],
    )
    ax.set_title("Observation and measurement-recoverability ladder", pad=10, weight="bold")
    save(fig, "fig2_recoverability_ladder")


def make_rvc_metabolic_gate() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.1), gridspec_kw={"width_ratios": [1.2, 1]})
    left, right = axes
    time = list(range(9))
    rhythm = [0.25, 0.4, 0.8, 0.55, 0.3, 0.75, 0.9, 0.5, 0.35]
    adequacy_high = 0.9
    adequacy_low = 0.35
    left.plot(time, rhythm, color=COLORS["meso"], lw=2, label=r"Observed proxy $\hat r(t)$")
    left.plot(time, [adequacy_high * value for value in rhythm], color=COLORS["metabolic"], lw=2,
              label=r"High adequacy: $r_{\mathrm{eff}}(t)$")
    left.plot(time, [adequacy_low * value for value in rhythm], color=COLORS["eap"], lw=2,
              label=r"Low adequacy: $r_{\mathrm{eff}}(t)$")
    left.set_xlabel("Conceptual time")
    left.set_ylabel("Control strength")
    left.set_ylim(0, 1.05)
    left.set_title("Metabolic adequacy gates effective control")
    left.legend(frameon=False, fontsize=8, loc="upper left")
    left.spines[["top", "right"]].set_visible(False)

    sigma_high = [0.2 + 0.8 * (1 - adequacy_high * value) for value in rhythm]
    sigma_low = [0.2 + 0.8 * (1 - adequacy_low * value) for value in rhythm]
    right.plot(time, sigma_high, color=COLORS["metabolic"], lw=2, label="High adequacy")
    right.plot(time, sigma_low, color=COLORS["eap"], lw=2, label="Low adequacy")
    right.fill_between(time, sigma_high, sigma_low, color="#FCE4EC", alpha=0.7,
                       label="Functional-control loss")
    right.set_xlabel("Conceptual time")
    right.set_ylabel(r"Effective variance $\sigma(t)$")
    right.set_ylim(0, 1.05)
    right.set_title("Same rhythmic proxy, different variance schedule")
    right.legend(frameon=False, fontsize=8)
    right.spines[["top", "right"]].set_visible(False)
    fig.suptitle(
        "Rhythmic variance control is proposed to require metabolic adequacy",
        fontsize=11,
        weight="bold",
        y=1.02,
    )
    fig.text(
        0.5,
        -0.02,
        "Conceptual illustration only: high slow-frequency power under low adequacy is not interpreted as successful denoising.",
        ha="center",
        fontsize=8,
        color=COLORS["neutral"],
    )
    fig.tight_layout()
    save(fig, "fig3_rvc_metabolic_gate")


def make_cross_theory_map() -> None:
    fig, ax = plt.subplots(figsize=(10, 5.1))
    clean(ax)
    layers = [
        (0.05, "Structural\nconstraints", "Network Control\nTheory", "neutral"),
        (0.235, "Local\nrecurrence", "Recurrent Processing\nTheory", "meso"),
        (0.42, "Inference /\ncontent", "Predictive Processing\n/ FEP", "bridge"),
        (0.605, "Global\naccess", "Global Neuronal\nWorkspace", "macro"),
        (0.79, "Meta-\nrepresentation", "HOT / Attention\nSchema Theory", "eap"),
    ]
    for x, layer, theory, color in layers:
        add_box(ax, x, 0.54, 0.15, 0.17, layer, COLORS["neutral"], fontsize=8)
        ax.text(x + 0.075, 0.43, theory, ha="center", va="center", fontsize=8, color=COLORS[color])
    for index in range(len(layers) - 1):
        arrow(ax, (layers[index][0] + 0.152, 0.625), (layers[index + 1][0] - 0.003, 0.625))
    add_box(ax, 0.31, 0.12, 0.38, 0.18, "NDT: rhythm-sensitive state-space dynamics\nand versioned measurement", COLORS["macro"], fontsize=9)
    arrow(ax, (0.50, 0.32), (0.50, 0.52))
    ax.text(0.5, 0.89, "Cross-theory explanatory-layer map", ha="center", weight="bold", fontsize=11)
    ax.text(
        0.5,
        0.04,
        "NDT can interface with each layer but does not replace an identity theory, an access theory, or a self-model theory.",
        ha="center",
        fontsize=8,
        color=COLORS["neutral"],
    )
    save(fig, "fig4_cross_theory_map")


def main() -> None:
    print("Generating NDT_2 conceptual figures...")
    make_scale_ladder()
    make_recoverability_ladder()
    make_rvc_metabolic_gate()
    make_cross_theory_map()
    print(f"All figures written to {FIGURES}")


if __name__ == "__main__":
    main()
