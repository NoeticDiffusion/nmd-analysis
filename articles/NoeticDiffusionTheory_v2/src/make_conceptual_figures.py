"""Reusable conceptual-figure generator for the NDT article.

Schematics, not empirical plots. Labels, panel order, and claim-status colours
are defined in code so PNG and SVG stay reproducible.

Science-lead figure set (`sciencelead/sl_001.md`, `sl_1.md`):

    fig1  Architecture: x_t neighbourhood, control above, measurement below
    fig2  Inference ladder with where current results stop
    fig3  Non-equivalent dynamical questions (one state, six objects)
    fig4  Accessibility control acting on distinct slots
    fig5  Empirical evidence map (status-coded cells)

S4 conceptual decoder (plain-language companion; keep panels sparse):

    s4a  Same place, different futures (C1 / C2)
    s4b  One state, several questions (hiker objects)
    s4c  Control can change futures at matched state (C3)
    s4d  The map is not the land (X → Y → x)
    s4e  Story strip: present → local law → futures → control

Usage:
    python src/make_conceptual_figures.py
    python src/make_conceptual_figures.py --only s4a,s4b,s4c,s4d,s4e
    python src/make_conceptual_figures.py --formats svg --dpi 200
    python src/make_conceptual_figures.py --list

The drawing helpers (save_figure, add_box, add_arrow, add_band, ...) are
intentional public API: add a new builder, register it in FIGURES, and the
CLI will emit PNG/SVG without further wiring.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import (
    Circle,
    Ellipse,
    FancyBboxPatch,
    Polygon,
    Rectangle,
    Wedge,
)
from matplotlib.figure import Figure

ARTICLE = Path(__file__).resolve().parents[1]
DEFAULT_OUTDIR = ARTICLE / "figures" / "conceptual"

# Layer colours follow the article hierarchy, not the NDT_2 meso/macro palette.
COLORS = {
    "ink": "#1F2933",
    "muted": "#546E7A",
    "paper": "#FAFBFC",
    "band": "#F4F6F8",
    "control": "#6A1B9A",
    "state": "#1565C0",
    "futures": "#00897B",
    "diffusion": "#EF6C00",
    "measure": "#455A64",
    "latent": "#90A4AE",
    "basin_a": "#90CAF9",
    "basin_b": "#FFCC80",
    "validated": "#2E7D32",
    "bounded": "#F9A825",
    "null": "#C62828",
    "untested": "#ECEFF1",
    "speculative": "#7E57C2",
}

STATUS = {
    "V": ("validated", COLORS["validated"], "white"),
    "B": ("bounded", COLORS["bounded"], COLORS["ink"]),
    "N": ("null / fail", COLORS["null"], "white"),
    "—": ("not tested", COLORS["untested"], COLORS["muted"]),
    "S": ("speculative", COLORS["speculative"], "white"),
}


# ---------------------------------------------------------------------------
# Style and primitives (reuse these when adding figures)
# ---------------------------------------------------------------------------


def apply_style() -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "text.usetex": False,
        }
    )


def save_figure(
    fig: Figure,
    stem: str,
    *,
    outdir: Path = DEFAULT_OUTDIR,
    formats: Sequence[str] = ("png", "svg"),
    dpi: int = 300,
) -> list[Path]:
    """Write matching raster/vector outputs and close the figure."""
    outdir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for extension in formats:
        path = outdir / f"{stem}.{extension}"
        fig.savefig(
            path,
            format=extension,
            dpi=None if extension == "svg" else dpi,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        written.append(path)
        print(f"Saved {path.relative_to(ARTICLE)}")
    plt.close(fig)
    return written


def clean_axes(ax: plt.Axes, xlim: tuple[float, float] = (0.0, 1.0), ylim: tuple[float, float] = (0.0, 1.0)) -> None:
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")


def add_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    text: str,
    color: str,
    *,
    fontsize: float = 8.0,
    face: str = "white",
    weight: str = "normal",
    lw: float = 1.2,
    ls: str = "-",
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.008,rounding_size=0.02",
        linewidth=lw,
        linestyle=ls,
        edgecolor=color,
        facecolor=face,
    )
    ax.add_patch(patch)
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=COLORS["ink"],
        weight=weight,
        wrap=True,
    )
    return patch


def add_band(
    ax: plt.Axes,
    y0: float,
    y1: float,
    label: str,
    color: str,
    *,
    x0: float = 0.02,
    x1: float = 0.98,
) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x0, y0),
            x1 - x0,
            y1 - y0,
            boxstyle="round,pad=0.004,rounding_size=0.012",
            linewidth=1.0,
            linestyle=(0, (4, 3)),
            edgecolor=color,
            facecolor=COLORS["band"],
            alpha=0.55,
            zorder=0,
        )
    )
    ax.text(
        x0 + 0.012,
        y1 - 0.018,
        label,
        ha="left",
        va="top",
        fontsize=7.5,
        color=color,
        weight="bold",
        zorder=2,
    )


def add_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str | None = None,
    *,
    lw: float = 1.2,
    style: str = "->",
    ls: str = "-",
    rad: float = 0.0,
) -> None:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={
            "arrowstyle": style,
            "lw": lw,
            "color": color or COLORS["muted"],
            "linestyle": ls,
            "connectionstyle": f"arc3,rad={rad}",
            "shrinkA": 0,
            "shrinkB": 0,
        },
        zorder=3,
    )


def add_label(
    ax: plt.Axes,
    x: float,
    y: float,
    text: str,
    *,
    color: str | None = None,
    fontsize: float = 8.0,
    ha: str = "center",
    va: str = "center",
    weight: str = "normal",
) -> None:
    ax.text(
        x,
        y,
        text,
        ha=ha,
        va=va,
        fontsize=fontsize,
        color=color or COLORS["ink"],
        weight=weight,
        zorder=5,
    )


def _rotate(vec: np.ndarray, degrees: float) -> np.ndarray:
    theta = np.deg2rad(degrees)
    rot = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    return rot @ vec


def add_cone(
    ax: plt.Axes,
    origin: tuple[float, float],
    direction: tuple[float, float],
    length: float,
    half_angle: float,
    color: str,
    *,
    alpha: float = 0.28,
) -> None:
    origin_arr = np.array(origin, dtype=float)
    direction_arr = np.array(direction, dtype=float)
    direction_arr = direction_arr / np.linalg.norm(direction_arr)
    left = origin_arr + _rotate(direction_arr, half_angle) * length
    right = origin_arr + _rotate(direction_arr, -half_angle) * length
    ax.add_patch(
        Polygon(
            [origin_arr, left, right],
            closed=True,
            facecolor=color,
            edgecolor=color,
            linewidth=1.0,
            alpha=alpha,
            zorder=1,
        )
    )


# ---------------------------------------------------------------------------
# Figure 1 — architecture
# ---------------------------------------------------------------------------


def make_architecture() -> Figure:
    fig, ax = plt.subplots(figsize=(11.2, 8.4))
    clean_axes(ax)
    fig.patch.set_facecolor("white")

    add_label(
        ax,
        0.50,
        0.97,
        r"State  $\rightarrow$  local dynamical geometry  $\rightarrow$  "
        r"possible futures  $\rightarrow$  control of accessibility",
        fontsize=11,
        weight="bold",
    )

    add_band(ax, 0.78, 0.93, "Control of accessibility  (candidate mechanisms)", COLORS["control"])
    controllers = [
        (0.05, "Rhythm\nRVC  $r(t)\\!\\to\\!\\sigma(t)$"),
        (0.24, "Thalamus\naccess / gates"),
        (0.43, "History\nHELS-A / replay"),
        (0.62, "Body\nEAP context"),
        (0.81, "Metabolism\nfeasibility"),
    ]
    for x, text in controllers:
        add_box(ax, x, 0.805, 0.155, 0.10, text, COLORS["control"], fontsize=7.2)

    add_band(ax, 0.26, 0.76, "Latent neighbourhood of  $x_t$  (not the chart)", COLORS["state"])

    # Attractor wells / committor basins (background).
    ax.add_patch(
        Ellipse((0.22, 0.46), 0.28, 0.22, facecolor=COLORS["basin_a"], edgecolor="none", alpha=0.35, zorder=1)
    )
    ax.add_patch(
        Ellipse((0.68, 0.52), 0.30, 0.24, facecolor=COLORS["basin_b"], edgecolor="none", alpha=0.35, zorder=1)
    )
    add_label(ax, 0.18, 0.46, r"$q \approx 0$" + "\nbasin A", fontsize=7.5, color=COLORS["state"])
    add_label(ax, 0.78, 0.58, r"$q \approx 1$" + "\nbasin B", fontsize=7.5, color=COLORS["diffusion"])

    cx, cy = 0.46, 0.50

    # Diffusion tensor a.
    ax.add_patch(
        Ellipse(
            (cx, cy),
            0.22,
            0.12,
            angle=28,
            facecolor=COLORS["diffusion"],
            edgecolor=COLORS["diffusion"],
            alpha=0.18,
            lw=1.4,
            zorder=2,
        )
    )
    add_label(ax, cx + 0.01, cy - 0.095, r"diffusion  $a=\Sigma\Sigma^{\top}$", fontsize=7.5, color=COLORS["diffusion"])

    # Reachability cone.
    add_cone(ax, (cx, cy), (1.0, 0.18), 0.28, 18, COLORS["futures"], alpha=0.30)
    add_label(ax, 0.72, 0.44, "reachability", fontsize=7.5, color=COLORS["futures"])

    # Drift b.
    add_arrow(ax, (cx, cy), (cx + 0.16, cy + 0.11), COLORS["state"], lw=1.8)
    add_label(ax, cx + 0.18, cy + 0.13, r"drift  $b$", fontsize=8, color=COLORS["state"], ha="left")

    # Jacobian: undeformed neighbourhood vs local linear deformation.
    ax.add_patch(
        Circle((cx, cy), 0.07, fill=False, edgecolor=COLORS["control"], lw=1.0, ls=(0, (2, 2)), zorder=3)
    )
    ax.add_patch(
        Ellipse((cx, cy), 0.20, 0.10, angle=40, fill=False, edgecolor=COLORS["control"], lw=1.5, zorder=3)
    )
    add_label(ax, cx - 0.20, cy + 0.13, r"Jacobian  $J$", fontsize=8, color=COLORS["control"])

    # FAR: finite perturbation out and a recovery arrow.
    add_arrow(ax, (cx, cy), (cx - 0.14, cy + 0.18), COLORS["futures"], lw=1.3, ls=(0, (3, 2)))
    add_arrow(ax, (cx - 0.14, cy + 0.18), (cx - 0.03, cy + 0.05), COLORS["futures"], lw=1.0, ls=(0, (3, 2)), rad=0.25)
    add_label(ax, cx - 0.22, cy + 0.20, "FAR", fontsize=8, color=COLORS["futures"], ha="right")

    ax.add_patch(Circle((cx, cy), 0.016, facecolor=COLORS["ink"], edgecolor="white", lw=1.2, zorder=6))
    add_label(ax, cx, cy + 0.038, r"$x_t$", fontsize=11, weight="bold")

    # Control arrows hit distinct slots (rhythm→a, thalamus→cone, history→Φ/basins,
    # body→state, metabolism→feasibility of basin B).
    add_arrow(ax, (0.127, 0.805), (cx + 0.06, cy - 0.04), COLORS["control"], lw=0.9, ls=(0, (3, 2)))
    add_arrow(ax, (0.317, 0.805), (cx + 0.16, cy + 0.02), COLORS["control"], lw=0.9, ls=(0, (3, 2)))
    add_arrow(ax, (0.507, 0.805), (0.68, 0.58), COLORS["control"], lw=0.9, ls=(0, (3, 2)))
    add_arrow(ax, (0.697, 0.805), (cx, cy + 0.09), COLORS["control"], lw=0.9, ls=(0, (3, 2)))
    add_arrow(ax, (0.887, 0.805), (0.78, 0.54), COLORS["control"], lw=0.9, ls=(0, (3, 2)))

    add_band(ax, 0.03, 0.24, "Observation and chart  (measurement, not the theory)", COLORS["measure"])
    add_box(ax, 0.05, 0.07, 0.22, 0.11, "EEG / MEG / fMRI\nLFP / spikes", COLORS["measure"], fontsize=7.5)
    add_box(ax, 0.34, 0.07, 0.28, 0.11, r"Observation" + "\n" + r"$Y_t = g(X_t)+\epsilon_t$", COLORS["measure"], fontsize=7.5)
    add_box(ax, 0.69, 0.07, 0.26, 0.11, "NMD / MNPS chart" + "\n" + r"$x_t = [m_t,\, d_t,\, e_t]^{\top}$", COLORS["measure"], fontsize=7.5)
    add_arrow(ax, (0.275, 0.125), (0.335, 0.125), COLORS["measure"])
    add_arrow(ax, (0.625, 0.125), (0.685, 0.125), COLORS["measure"])
    add_arrow(ax, (cx, cy - 0.12), (0.48, 0.24), COLORS["latent"], lw=1.0, ls=(0, (4, 3)))

    add_label(
        ax,
        0.50,
        0.012,
        "Dashed bands separate control, latent neighbourhood, and measurement. Inference strength is Fig. 2.",
        fontsize=7.5,
        color=COLORS["muted"],
    )
    return fig


# ---------------------------------------------------------------------------
# Figure 2 — inference ladder
# ---------------------------------------------------------------------------


def make_ladder() -> Figure:
    fig, ax = plt.subplots(figsize=(11.4, 8.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    add_label(ax, 0.50, 0.965, "Observation chain and inferential claim classes", fontsize=13, weight="bold")

    chain = [
        (0.02, r"Latent" + "\n" + r"$X_t$", COLORS["state"]),
        (0.22, r"Measurement" + "\n" + r"$Y_t$", COLORS["measure"]),
        (0.42, "Features\n" + r"$z_t$", COLORS["measure"]),
        (0.62, "Chart\n" + r"$x_t$", COLORS["futures"]),
        (0.82, "Local dynamics\n" + r"$b,\, J,\, a$", COLORS["control"]),
    ]
    for x, text, color in chain:
        add_box(ax, x, 0.80, 0.16, 0.13, text, color, fontsize=9.5)
    for index in range(len(chain) - 1):
        add_arrow(ax, (chain[index][0] + 0.165, 0.865), (chain[index + 1][0] - 0.005, 0.865), COLORS["muted"])

    levels = [
        ("1", "Association", "An observable covaries with another\nquantity under stated nulls.", "DANDI 000458 meso–macro contact\nstops here ($r=0.406$ / $0.395$).", COLORS["futures"]),
        ("2", "Mechanism discrimination", "Observations separate alternatives\nwith matched task-level output.", "Not claimed for the empirical\nanchors in this article.", COLORS["latent"]),
        ("3", "Latent-order preservation", "Measured ordering tracks a\npredefined latent summary.", "Not claimed for MNPS as unique\nlatent identification.", COLORS["latent"]),
        ("4", "Operator identification", "A local operator is recovered\nunder residual checks.", "EEG-only chart residual $0.856$: fail.\nSimulator $a,\\alpha,\\omega$: envelopes only.", COLORS["null"]),
    ]
    for index, (number, title, detail, stop, color) in enumerate(levels):
        y = 0.62 - index * 0.135
        ax.text(
            0.055,
            y + 0.045,
            number,
            ha="center",
            va="center",
            fontsize=11,
            weight="bold",
            color="white",
            bbox={"boxstyle": "circle,pad=0.30", "fc": color, "ec": color},
        )
        add_label(ax, 0.11, y + 0.062, title, fontsize=10, ha="left", weight="bold")
        add_label(ax, 0.11, y + 0.018, detail, fontsize=8.5, ha="left", color=COLORS["muted"], va="center")
        add_box(ax, 0.60, y, 0.36, 0.11, "Where results stop\n" + stop, color, fontsize=8.2, face="#FFF8F0" if number == "4" else "white")

    add_label(
        ax,
        0.50,
        0.075,
        "Independent readout: IBL population decoder can pass while a discrete-flow operator stops.",
        fontsize=8.5,
        color=COLORS["muted"],
    )
    add_label(
        ax,
        0.50,
        0.030,
        "A claim-class-1 association does not license a stronger class. A plausible chart remains class 1 until residual and perturbation tests pass.",
        fontsize=8.5,
        color=COLORS["muted"],
    )
    return fig


# ---------------------------------------------------------------------------
# Figure 3 — orthogonal questions
# ---------------------------------------------------------------------------


def _mini_state(ax: plt.Axes, cx: float, cy: float) -> None:
    ax.add_patch(Circle((cx, cy), 0.03, facecolor=COLORS["ink"], edgecolor="white", lw=0.8, zorder=4))


def make_orthogonal() -> Figure:
    fig, axes = plt.subplots(2, 3, figsize=(11.0, 6.8))
    panels = [
        (r"Spectral abscissa  $\alpha$", "Do infinitesimal modes grow?", "alpha"),
        (r"Numerical abscissa  $\omega$", "Can perturbations initially amplify?", "omega"),
        (r"Diffusion tensor  $a$", "How does random variation spread?", "diff"),
        ("Stochastic short-horizon reachability", "How does nearby future mass spread?", "reach"),
        (r"Committor  $q(x)$", "Which destination is favoured?", "comm"),
        ("Finite-amplitude resilience", "Can a finite kick dislodge the state?", "far"),
    ]
    for ax, (title, question, kind) in zip(axes.ravel(), panels):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=10, pad=8)
        add_label(ax, 0.50, 0.08, question, fontsize=7.5, color=COLORS["muted"])
        cx, cy = 0.50, 0.52
        if kind == "alpha":
            add_arrow(ax, (cx, cy), (cx + 0.28, cy + 0.12), COLORS["null"], lw=1.6)
            add_arrow(ax, (cx, cy), (cx - 0.22, cy - 0.16), COLORS["state"], lw=1.6)
            add_label(ax, 0.78, 0.72, r"$\alpha>0$", fontsize=8, color=COLORS["null"])
            add_label(ax, 0.22, 0.28, r"$\alpha<0$", fontsize=8, color=COLORS["state"])
        elif kind == "omega":
            xs = np.linspace(0.22, 0.78, 40)
            ys = 0.52 + 0.18 * xs * np.exp(-6 * (xs - 0.22)) * np.sin(18 * (xs - 0.22))
            ax.plot(xs, ys, color=COLORS["control"], lw=1.8)
            add_label(ax, 0.72, 0.72, "transient\ngrowth", fontsize=7.5, color=COLORS["control"])
        elif kind == "diff":
            ax.add_patch(
                Ellipse((cx, cy), 0.46, 0.22, angle=30, facecolor=COLORS["diffusion"], edgecolor=COLORS["diffusion"], alpha=0.25, lw=1.4)
            )
        elif kind == "reach":
            add_cone(ax, (cx, cy), (1.0, 0.15), 0.38, 20, COLORS["futures"])
        elif kind == "comm":
            ax.add_patch(Wedge((0.32, 0.52), 0.28, 40, 320, facecolor=COLORS["basin_a"], edgecolor=COLORS["state"], alpha=0.7))
            ax.add_patch(Wedge((0.68, 0.52), 0.28, 220, 140, facecolor=COLORS["basin_b"], edgecolor=COLORS["diffusion"], alpha=0.7))
            add_label(ax, 0.28, 0.52, "A", fontsize=9, weight="bold")
            add_label(ax, 0.72, 0.52, "B", fontsize=9, weight="bold")
        elif kind == "far":
            ax.add_patch(Ellipse((cx, cy), 0.28, 0.18, facecolor=COLORS["band"], edgecolor=COLORS["state"], lw=1.2))
            add_arrow(ax, (cx, cy), (cx + 0.32, cy + 0.18), COLORS["futures"], lw=1.5, ls=(0, (3, 2)))
            add_arrow(ax, (cx + 0.32, cy + 0.18), (cx + 0.06, cy + 0.04), COLORS["futures"], lw=1.1, ls=(0, (3, 2)), rad=0.25)
        _mini_state(ax, cx, cy)
        add_label(ax, cx, cy + 0.07, r"$x_t$", fontsize=8, weight="bold")

    fig.suptitle(
        "Non-equivalent dynamical questions: the same state, six non-interchangeable objects",
        fontsize=12,
        weight="bold",
        y=0.98,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


# ---------------------------------------------------------------------------
# Figure 4 — accessibility control
# ---------------------------------------------------------------------------


def make_control() -> Figure:
    fig, ax = plt.subplots(figsize=(10.8, 6.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    add_label(ax, 0.50, 0.96, "Candidate controls act on different slots of the local law", fontsize=12, weight="bold")
    add_label(
        ax,
        0.50,
        0.91,
        r"$dX_t = b(X_t, t\,|\,c_t)\,dt + \Sigma(X_t, t\,|\,c_t)\,dW_t"
        r"\qquad b = -M\nabla V + u_{\mathrm{nc}}$",
        fontsize=9,
    )

    slots = [
        (0.04, r"drift  $b$", COLORS["state"]),
        (0.23, r"diffusion  $a$", COLORS["diffusion"]),
        (0.42, r"landscape  $V$", COLORS["control"]),
        (0.61, r"mobility  $M$", COLORS["futures"]),
        (0.80, "transition\ngates", COLORS["measure"]),
    ]
    for x, text, color in slots:
        add_box(ax, x, 0.14, 0.16, 0.12, text, color, fontsize=8, weight="bold")
    add_label(ax, 0.50, 0.08, "Local dynamical object  (what can still happen)", fontsize=8, color=COLORS["muted"])

    controllers = [
        ("Body / EAP", "body context; spindle\ngeometry efficacy rejected", 0.04, [(0.12, 0.26)]),
        ("Rhythm / RVC", "minimal special case\n" + r"$r(t)\to\sigma(t)$", 0.23, [(0.31, 0.26)]),
        ("History / HELS-A", r"$A_H$ on frozen $V$" + "\nwriting remains open", 0.42, [(0.50, 0.26)]),
        ("Metabolism", "feasibility bound;\nnot a consciousness axis", 0.61, [(0.69, 0.26)]),
        ("Thalamic access", "synthetic operators;\nbiology is association", 0.80, [(0.88, 0.26)]),
    ]
    for title, ceiling, x, targets in controllers:
        add_box(ax, x, 0.68, 0.16, 0.16, title, COLORS["control"], fontsize=8, weight="bold")
        add_label(ax, x + 0.08, 0.62, ceiling, fontsize=6.6, color=COLORS["muted"])
        for tx, ty in targets:
            add_arrow(ax, (x + 0.08, 0.68), (tx, ty), COLORS["control"], lw=1.15)

    add_label(
        ax,
        0.50,
        0.34,
        "A failure in one slot revises that implementation. It does not falsify accessibility control as a modelling class.",
        fontsize=8,
        color=COLORS["muted"],
    )
    return fig


# ---------------------------------------------------------------------------
# Figure 5 — evidence map
# ---------------------------------------------------------------------------

# Status codes follow summaries/04 and 01/03. Anesthesia and epilepsy rows are
# kept because sciencelead listed them; they are unpaid (not tested), not implied support.
EVIDENCE_ROWS: list[tuple[str, list[str]]] = [
    ("Truth-known simulator", ["—", "B", "B", "N", "N", "S"]),
    ("Meso → macro\n(DANDI 000458)", ["B", "N", "—", "N", "—", "—"]),
    ("N2 spindles", ["B", "—", "—", "—", "—", "S"]),
    ("Anesthesia", ["—", "—", "—", "—", "—", "—"]),
    ("Cardiac-arrest coma", ["B", "B", "—", "B", "—", "—"]),
    ("Epilepsy", ["—", "—", "—", "—", "—", "—"]),
    ("Depressive-symptom rest", ["B", "V", "—", "V", "—", "—"]),
    ("First-episode psychosis", ["B", "B", "—", "B", "—", "—"]),
    ("Expected-stimulus\nomission (VISp)", ["B", "—", "—", "—", "—", "—"]),
    ("IBL chart readout", ["B", "N", "—", "—", "—", "—"]),
    ("Human MTL–scalp\n(DANDI 000574)", ["N", "—", "—", "—", "—", "—"]),
]
EVIDENCE_COLS = [
    "State geometry",
    "Local dynamics",
    "Diffusion a",
    "Reachability",
    "Dest. / FAR",
    "Mechanism",
]


def make_evidence_map() -> Figure:
    n_rows = len(EVIDENCE_ROWS)
    n_cols = len(EVIDENCE_COLS)
    fig, ax = plt.subplots(figsize=(12.2, 9.6))
    ax.set_xlim(-3.6, n_cols + 0.2)
    ax.set_ylim(-1.7, n_rows + 1.55)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    add_label(
        ax,
        n_cols / 2,
        n_rows + 1.22,
        "Empirical evidence map",
        fontsize=13,
        weight="bold",
    )
    add_label(
        ax,
        n_cols / 2,
        n_rows + 0.92,
        "Which layer moves, under frozen contracts",
        fontsize=9,
        color=COLORS["muted"],
    )

    header_y = n_rows + 0.22
    ax.add_patch(
        Rectangle(
            (-0.02, n_rows - 0.02),
            n_cols + 0.04,
            0.72,
            facecolor=COLORS["band"],
            edgecolor="none",
            zorder=1,
        )
    )
    for j, col in enumerate(EVIDENCE_COLS):
        ax.text(
            j + 0.5,
            header_y,
            col,
            ha="center",
            va="center",
            fontsize=9,
            weight="bold",
            zorder=2,
        )

    for i, (row_name, cells) in enumerate(EVIDENCE_ROWS):
        y = n_rows - 1 - i
        ax.text(-0.14, y + 0.5, row_name.replace("\n", " "), ha="right", va="center", fontsize=9)
        for j, code in enumerate(cells):
            _name, face, text_color = STATUS[code]
            ax.add_patch(
                Rectangle(
                    (j + 0.10, y + 0.10),
                    0.80,
                    0.80,
                    facecolor=face,
                    edgecolor="white",
                    lw=1.6,
                    zorder=2,
                )
            )
            ax.text(
                j + 0.5,
                y + 0.5,
                code,
                ha="center",
                va="center",
                fontsize=12,
                weight="bold",
                color=text_color,
                zorder=3,
            )

    legend_y = -0.95
    for index, (code, (name, face, text_color)) in enumerate(STATUS.items()):
        x = index * 1.85
        ax.add_patch(Rectangle((x, legend_y - 0.12), 0.32, 0.32, facecolor=face, edgecolor="white", lw=1.0))
        ax.text(x + 0.42, legend_y + 0.04, f"{code}  {name}", ha="left", va="center", fontsize=8.5, color=COLORS["ink"])

    add_label(
        ax,
        n_cols / 2,
        -1.45,
        "Internal status under frozen contracts, not independent replication. Empty anesthesia and epilepsy rows are untested, not hidden positives.",
        fontsize=8,
        color=COLORS["muted"],
    )
    return fig


# ---------------------------------------------------------------------------
# S4 helpers — sparse terrain / pin / gate motifs
# ---------------------------------------------------------------------------


def add_state_pin(
    ax: plt.Axes,
    cx: float,
    cy: float,
    label: str = r"$x_t$",
    *,
    radius: float = 0.018,
) -> None:
    ax.add_patch(
        Circle((cx, cy), radius, facecolor=COLORS["ink"], edgecolor="white", lw=1.2, zorder=6)
    )
    if label:
        add_label(ax, cx, cy + radius + 0.04, label, fontsize=10, weight="bold")


def add_terrain(
    ax: plt.Axes,
    cx: float,
    cy: float,
    *,
    angle: float = -18.0,
    muted: bool = False,
) -> None:
    edge = COLORS["latent"] if muted else COLORS["measure"]
    for width, height, _alpha in ((0.62, 0.46, 0.16), (0.42, 0.30, 0.20), (0.24, 0.17, 0.28)):
        ax.add_patch(
            Ellipse(
                (cx, cy),
                width,
                height,
                angle=angle,
                fill=False,
                edgecolor=edge,
                lw=1.05,
                alpha=0.85 if not muted else 0.45,
                zorder=1,
            )
        )


def add_two_basins(
    ax: plt.Axes,
    a_xy: tuple[float, float],
    b_xy: tuple[float, float],
    *,
    highlight: str | None = None,
) -> None:
    specs = [
        (a_xy, COLORS["basin_a"], COLORS["state"], "A", "a"),
        (b_xy, COLORS["basin_b"], COLORS["diffusion"], "B", "b"),
    ]
    for (cx, cy), face, edge, name, key in specs:
        alpha = 0.72 if highlight in (None, key) else 0.22
        ax.add_patch(
            Ellipse((cx, cy), 0.22, 0.16, facecolor=face, edgecolor=edge, alpha=alpha, lw=1.1, zorder=1)
        )
        add_label(ax, cx, cy, name, fontsize=9, weight="bold", color=edge)


def add_gate(
    ax: plt.Axes,
    x: float,
    y: float,
    *,
    open_gate: bool,
    color: str,
) -> None:
    if open_gate:
        ax.add_patch(
            Rectangle((x, y), 0.018, 0.09, facecolor="white", edgecolor=color, lw=1.1, zorder=4)
        )
        add_label(ax, x + 0.009, y + 0.11, "open", fontsize=6.5, color=color)
    else:
        ax.add_patch(
            Rectangle((x - 0.01, y), 0.038, 0.09, facecolor=color, edgecolor=color, lw=0.6, alpha=0.85, zorder=4)
        )
        add_label(ax, x + 0.009, y + 0.11, "restricted", fontsize=6.5, color=color)


# ---------------------------------------------------------------------------
# S4-1 — same place, different futures (C1 / C2)
# ---------------------------------------------------------------------------


def make_s4_same_place() -> Figure:
    fig, axes = plt.subplots(1, 3, figsize=(11.6, 4.35))
    fig.patch.set_facecolor("white")
    titles = (
        "Present pin\nmatched location",
        "Future law A\nnarrow corridor",
        "Future law B\nbroad anisotropic spread",
    )
    pin = (0.46, 0.48)
    a_xy, b_xy = (0.22, 0.28), (0.78, 0.62)

    for ax, title in zip(axes, titles):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=10, pad=10)
        add_terrain(ax, 0.50, 0.48)

    add_two_basins(axes[0], a_xy, b_xy, highlight=None)
    add_state_pin(axes[0], *pin, label=r"$x_t = x^{\ast}$")
    add_label(axes[0], 0.50, 0.08, "Same GPS pin.\nThe map of now.", fontsize=8, color=COLORS["muted"])

    add_two_basins(axes[1], a_xy, b_xy, highlight="a")
    add_cone(axes[1], pin, (0.85, -0.35), 0.34, 12, COLORS["futures"], alpha=0.38)
    axes[1].add_patch(
        Ellipse(
            pin, 0.16, 0.08, angle=-22, facecolor=COLORS["diffusion"],
            edgecolor=COLORS["diffusion"], alpha=0.22, lw=1.2, zorder=2,
        )
    )
    add_arrow(axes[1], pin, (0.62, 0.38), COLORS["state"], lw=1.7)
    add_state_pin(axes[1], *pin, label=r"$x^{\ast}$")
    add_label(axes[1], 0.50, 0.08, "Favoured route toward A.", fontsize=8, color=COLORS["muted"])

    add_two_basins(axes[2], a_xy, b_xy, highlight="b")
    add_cone(axes[2], pin, (0.95, 0.55), 0.40, 26, COLORS["futures"], alpha=0.32)
    axes[2].add_patch(
        Ellipse(
            pin, 0.30, 0.12, angle=28, facecolor=COLORS["diffusion"],
            edgecolor=COLORS["diffusion"], alpha=0.22, lw=1.2, zorder=2,
        )
    )
    add_arrow(axes[2], pin, (0.58, 0.62), COLORS["state"], lw=1.7)
    add_state_pin(axes[2], *pin, label=r"$x^{\ast}$")
    add_label(axes[2], 0.50, 0.08, "Mass leans toward B.", fontsize=8, color=COLORS["muted"])

    fig.suptitle(
        "Same measured state, different future law",
        fontsize=13,
        weight="bold",
        y=1.02,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


# ---------------------------------------------------------------------------
# S4-2 — one state, several questions
# ---------------------------------------------------------------------------


def make_s4_questions() -> Figure:
    fig, axes = plt.subplots(2, 4, figsize=(12.2, 6.4))
    fig.patch.set_facecolor("white")
    panels = [
        ("Location", r"$x_t$", "Where is the pin?", "loc"),
        ("Drift", r"$b$", "Which way does the ground slope?", "drift"),
        ("Local deformation", r"$J$", "What happens to a small nudge?", "jac"),
        ("Diffusion", r"$a$", "How does uncertainty spread?", "diff"),
        ("Possible futures", r"$K^h$", "What nearby futures remain likely?", "kh"),
        ("Destination", r"$q$", "Which valley is favoured?", "comm"),
        ("Finite perturbation", "FAR", "Can a larger shove change the regime?", "far"),
        ("Not one score", "", "These questions are not interchangeable.", "note"),
    ]
    for ax, (title, symbol, question, kind) in zip(axes.ravel(), panels):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title if not symbol else f"{title}   {symbol}", fontsize=10, pad=8)
        add_label(ax, 0.50, 0.10, question, fontsize=7.4, color=COLORS["muted"])
        cx, cy = 0.50, 0.52
        if kind == "loc":
            add_terrain(ax, cx, cy)
            add_state_pin(ax, cx, cy, label="GPS")
        elif kind == "drift":
            add_arrow(ax, (cx, cy), (cx + 0.28, cy + 0.10), COLORS["state"], lw=2.0)
            add_state_pin(ax, cx, cy, label="")
        elif kind == "jac":
            ax.add_patch(Circle((cx, cy), 0.12, fill=False, edgecolor=COLORS["latent"], lw=1.0, ls=(0, (2, 2))))
            ax.add_patch(
                Ellipse((cx, cy), 0.34, 0.16, angle=38, fill=False, edgecolor=COLORS["control"], lw=1.6)
            )
            add_state_pin(ax, cx, cy, label="")
        elif kind == "diff":
            ax.add_patch(
                Ellipse(
                    (cx, cy), 0.44, 0.20, angle=28, facecolor=COLORS["diffusion"],
                    edgecolor=COLORS["diffusion"], alpha=0.25, lw=1.4,
                )
            )
            add_state_pin(ax, cx, cy, label="")
        elif kind == "kh":
            add_cone(ax, (cx, cy), (1.0, 0.18), 0.38, 20, COLORS["futures"])
            add_state_pin(ax, cx, cy, label="")
        elif kind == "comm":
            add_two_basins(ax, (0.30, 0.50), (0.72, 0.54))
            add_state_pin(ax, cx, cy, label="")
        elif kind == "far":
            ax.add_patch(Ellipse((cx, cy), 0.26, 0.16, facecolor=COLORS["band"], edgecolor=COLORS["state"], lw=1.1))
            add_arrow(ax, (cx, cy), (cx + 0.30, cy + 0.18), COLORS["futures"], lw=1.5, ls=(0, (3, 2)))
            add_state_pin(ax, cx, cy, label="")
        elif kind == "note":
            add_label(
                ax,
                0.50,
                0.55,
                "Location is not drift.\nDrift is not spread.\nSpread is not destination.\nA kick is not a nudge.",
                fontsize=8.2,
                color=COLORS["ink"],
            )
            add_label(ax, 0.50, 0.22, "C1 / C2", fontsize=9, weight="bold", color=COLORS["control"])

    fig.suptitle(
        "The same moment supports non-equivalent dynamical questions",
        fontsize=13,
        weight="bold",
        y=0.98,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


# ---------------------------------------------------------------------------
# S4-3 — control changes futures at matched state (C3)
# ---------------------------------------------------------------------------


def make_s4_control() -> Figure:
    fig = plt.figure(figsize=(11.4, 5.6))
    fig.patch.set_facecolor("white")
    gs = fig.add_gridspec(2, 2, height_ratios=(0.22, 1.0), hspace=0.08, wspace=0.10)
    ax_icons = fig.add_subplot(gs[0, :])
    ax_l = fig.add_subplot(gs[1, 0])
    ax_r = fig.add_subplot(gs[1, 1])
    ax_icons.set_xlim(0, 1)
    ax_icons.set_ylim(0, 1)
    ax_icons.axis("off")
    add_label(ax_icons, 0.50, 0.82, "Candidate inputs to the same abstract operation", fontsize=9, color=COLORS["muted"])
    icons = [
        (0.10, "Rhythm"),
        (0.34, "Thalamus"),
        (0.58, "History"),
        (0.82, "Physiology"),
    ]
    for x, text in icons:
        add_box(ax_icons, x - 0.08, 0.12, 0.16, 0.48, text, COLORS["control"], fontsize=8)

    pin = (0.46, 0.46)
    a_xy, b_xy = (0.22, 0.26), (0.78, 0.64)
    for ax, title, toward, open_a, highlight in (
        (ax_l, r"Condition  $\gamma_1$" + "\naccess toward A", (-0.55, -0.25), True, "a"),
        (ax_r, r"Condition  $\gamma_2$" + "\naccess toward B", (0.85, 0.55), False, "b"),
    ):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=11, pad=8)
        add_terrain(ax, 0.50, 0.48)
        add_two_basins(ax, a_xy, b_xy, highlight=highlight)
        add_cone(ax, pin, toward, 0.36, 16, COLORS["futures"], alpha=0.36)
        add_arrow(ax, pin, (pin[0] + 0.14 * toward[0], pin[1] + 0.14 * toward[1]), COLORS["state"], lw=1.7)
        add_gate(ax, 0.30, 0.34, open_gate=open_a, color=COLORS["state"])
        add_gate(ax, 0.62, 0.52, open_gate=not open_a, color=COLORS["diffusion"])
        add_state_pin(ax, *pin, label=r"$x_t$  (unchanged)")
        add_label(ax, 0.50, 0.06, r"Landscape $V$ held fixed", fontsize=8, color=COLORS["muted"])

    fig.suptitle(
        "Conditional accessibility: control can reshape futures without moving the present point",
        fontsize=12,
        weight="bold",
        y=0.98,
    )
    return fig


# ---------------------------------------------------------------------------
# S4-4 — the map is not the land
# ---------------------------------------------------------------------------


def make_s4_map() -> Figure:
    fig, ax = plt.subplots(figsize=(10.4, 7.2))
    clean_axes(ax)
    fig.patch.set_facecolor("white")
    add_label(ax, 0.50, 0.97, "The map is useful precisely because it is not the land", fontsize=12, weight="bold")

    add_band(ax, 0.68, 0.92, "Latent neural dynamics   $X_t$", COLORS["state"])
    add_terrain(ax, 0.50, 0.80, angle=-22)
    add_two_basins(ax, (0.28, 0.76), (0.72, 0.84), highlight=None)
    add_state_pin(ax, 0.50, 0.80, label=r"$X_t$", radius=0.014)
    add_label(ax, 0.50, 0.70, "Rich, curved process — not fully seen", fontsize=8, color=COLORS["muted"])

    add_arrow(ax, (0.50, 0.68), (0.50, 0.62), COLORS["measure"], lw=1.3)
    add_label(ax, 0.62, 0.65, "observation", fontsize=7.5, color=COLORS["measure"], ha="left")

    add_band(ax, 0.40, 0.61, "Recording   $Y_t$", COLORS["measure"])
    sensors = [
        (0.08, "EEG"),
        (0.30, "spikes"),
        (0.52, "LFP"),
        (0.74, "MEG"),
    ]
    for x, text in sensors:
        add_box(ax, x, 0.44, 0.18, 0.11, text, COLORS["measure"], fontsize=8)

    add_arrow(ax, (0.50, 0.40), (0.50, 0.34), COLORS["measure"], lw=1.3)
    add_label(ax, 0.62, 0.37, "chart construction", fontsize=7.5, color=COLORS["measure"], ha="left")

    add_band(ax, 0.05, 0.33, "Operational map   $x_t=(m,d,e)$", COLORS["futures"])
    nodes = [(0.22, 0.18), (0.50, 0.22), (0.78, 0.16)]
    ax.plot([n[0] for n in nodes], [n[1] for n in nodes], color=COLORS["futures"], lw=2.2, zorder=2)
    for (x, y), lab in zip(nodes, (r"$m$", r"$d$", r"$e$")):
        ax.add_patch(Circle((x, y), 0.028, facecolor="white", edgecolor=COLORS["futures"], lw=1.6, zorder=4))
        add_label(ax, x, y, lab, fontsize=8, weight="bold", color=COLORS["futures"])
    add_cone(ax, (0.50, 0.22), (1.0, 0.05), 0.22, 14, COLORS["diffusion"], alpha=0.28)
    add_label(ax, 0.72, 0.28, r"estimates of $J$, $a$, $K^h$ live here", fontsize=7.5, color=COLORS["diffusion"], ha="left")
    add_label(
        ax,
        0.50,
        0.08,
        "A subway map is invaluable for travel. It is a poor geological survey.",
        fontsize=8,
        color=COLORS["muted"],
    )
    return fig


# ---------------------------------------------------------------------------
# S4-5 — uncrowded story strip (not a packed infographic)
# ---------------------------------------------------------------------------


def make_s4_story() -> Figure:
    fig, axes = plt.subplots(1, 4, figsize=(13.2, 3.8))
    fig.patch.set_facecolor("white")
    pin = (0.46, 0.50)
    labels = (
        "Where am I?",
        "What is the local law?",
        "What can happen?",
        "What changes that?",
    )
    kinds = ("present", "local", "futures", "control")
    for ax, title, kind in zip(axes, labels, kinds):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=10, pad=8)
        add_terrain(ax, 0.50, 0.50)
        if kind == "present":
            add_state_pin(ax, *pin, label="pin")
        elif kind == "local":
            ax.add_patch(
                Ellipse(
                    pin, 0.28, 0.12, angle=24, facecolor=COLORS["diffusion"],
                    edgecolor=COLORS["diffusion"], alpha=0.22, lw=1.2, zorder=2,
                )
            )
            add_arrow(ax, pin, (0.68, 0.60), COLORS["state"], lw=1.8)
            add_state_pin(ax, *pin, label="")
        elif kind == "futures":
            add_two_basins(ax, (0.24, 0.30), (0.76, 0.66))
            add_cone(ax, pin, (0.9, 0.35), 0.36, 18, COLORS["futures"])
            add_state_pin(ax, *pin, label="")
        elif kind == "control":
            add_two_basins(ax, (0.24, 0.30), (0.76, 0.66), highlight="b")
            add_cone(ax, pin, (0.9, 0.45), 0.36, 16, COLORS["control"])
            add_gate(ax, 0.60, 0.52, open_gate=True, color=COLORS["control"])
            add_state_pin(ax, *pin, label="same pin")

    fig.suptitle(
        "Present  →  local law  →  possible futures  →  control of access",
        fontsize=12,
        weight="bold",
        y=1.04,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.90))
    fig.text(
        0.50,
        0.02,
        "A map of the present is not the law governing what happens next.",
        ha="center",
        fontsize=8.5,
        color=COLORS["muted"],
    )
    return fig


# ---------------------------------------------------------------------------
# Registry and CLI
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FigureSpec:
    """One named schematic. Add entries here to extend the generator."""

    fig_id: str
    stem: str
    title: str
    builder: Callable[[], Figure]
    figsize_note: str = ""


FIGURES: tuple[FigureSpec, ...] = (
    FigureSpec("fig1", "fig1_ndt_architecture", "NDT architecture around $x_t$", make_architecture),
    FigureSpec("fig2", "fig2_inference_ladder", "Observation and claim levels", make_ladder),
    FigureSpec("fig3", "fig3_orthogonal_questions", "Non-equivalent dynamical questions", make_orthogonal),
    FigureSpec("fig4", "fig4_accessibility_control", "Accessibility control slots", make_control),
    FigureSpec("fig5", "fig5_evidence_map", "Empirical evidence map", make_evidence_map),
    FigureSpec("s4a", "fig_s4_1_same_place_different_futures", "Same place, different futures", make_s4_same_place),
    FigureSpec("s4b", "fig_s4_2_one_state_questions", "One state, several questions", make_s4_questions),
    FigureSpec("s4c", "fig_s4_3_control_matched_state", "Control at matched state", make_s4_control),
    FigureSpec("s4d", "fig_s4_4_map_not_land", "The map is not the land", make_s4_map),
    FigureSpec("s4e", "fig_s4_5_story_strip", "Present to control story strip", make_s4_story),
)


def get_spec(fig_id: str) -> FigureSpec:
    lookup = {spec.fig_id: spec for spec in FIGURES}
    lookup.update({spec.stem: spec for spec in FIGURES})
    try:
        return lookup[fig_id]
    except KeyError as exc:
        known = ", ".join(spec.fig_id for spec in FIGURES)
        raise SystemExit(f"Unknown figure {fig_id!r}. Known: {known}") from exc


def render(
    fig_ids: Sequence[str] | None = None,
    *,
    outdir: Path = DEFAULT_OUTDIR,
    formats: Sequence[str] = ("png", "svg"),
    dpi: int = 300,
) -> list[Path]:
    apply_style()
    selected = FIGURES if not fig_ids else tuple(get_spec(item) for item in fig_ids)
    written: list[Path] = []
    for spec in selected:
        print(f"Building {spec.fig_id}: {spec.title}")
        written.extend(save_figure(spec.builder(), spec.stem, outdir=outdir, formats=formats, dpi=dpi))
    return written


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("Usage:")[0].strip())
    parser.add_argument("--only", help="Comma-separated figure ids (fig1,fig2,...) or stems.")
    parser.add_argument("--formats", default="png,svg", help="Output formats (default: png,svg).")
    parser.add_argument("--dpi", type=int, default=300, help="Raster DPI (default: 300).")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR, help="Output directory.")
    parser.add_argument("--list", action="store_true", help="List registered figures and exit.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list:
        for spec in FIGURES:
            print(f"{spec.fig_id:6}  {spec.stem:28}  {spec.title}")
        return 0
    fig_ids = None if not args.only else [item.strip() for item in args.only.split(",") if item.strip()]
    formats = [item.strip() for item in args.formats.split(",") if item.strip()]
    written = render(fig_ids, outdir=args.outdir, formats=formats, dpi=args.dpi)
    print(f"Wrote {len(written)} files to {args.outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
