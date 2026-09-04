"""Generate the NDT flow/mechanism figures for NoeticDiffusionTheory.typ.

This script produces reproducible, code-generated versions of the diagrams
that illustrate how the core NDT flow works:

    neural rhythm -> r(t) -> variance schedule sigma(t)
        -> MNDM state trajectory (denoising vs. exploration)
        -> MNPS measurement chart (m, d, e)

It replaces the previously hand-exported `fig2_mndm_dynamics.jpg`, which had
a rendering bug (panel C displayed raw LaTeX/escape sequences such as
literal "\\n" instead of typeset equations). All math here is rendered with
matplotlib's built-in mathtext, so no external LaTeX installation is
required.

Usage:
    python src/make_figures.py

Outputs (written to ../figures/, i.e. articles/NDT/figures/):
    fig2_mndm_dynamics.png        Simulated minimal/extended MNDM dynamics
                                   (state-space trajectory, schedules, the
                                   minimal equation, and the "symphony" of
                                   extended-model schedules).
    fig_flow_overview.png         Box-and-arrow overview of the full NDT
                                   flow: rhythm -> r(t) -> sigma(t) -> MNDM
                                   -> MNPS -> Stage-1 tests.
    fig_rvc_gating_loop.png       Close-up of the RVC gating loop: how a
                                   rhythmic phase signal is translated into
                                   the variance schedule that alternates
                                   exploration and denoising epochs.

All simulations here are illustrative/synthetic (they exist to visualize the
*mechanism* the equations describe) and are not fits to empirical data. This
matches how these figures are captioned in the main article.
"""

from __future__ import annotations

import pathlib

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

FIGURES_DIR = pathlib.Path(__file__).resolve().parent.parent / "figures"

RNG_SEED = 20260809


# --------------------------------------------------------------------------
# Simulation helpers
# --------------------------------------------------------------------------


def simulate_minimal_mndm(
    n_steps: int = 6000,
    dt: float = 0.01,
    rhythm_hz: float = 0.5,
    sigma_min: float = 0.05,
    sigma_0: float = 1.0,
    seed: int = RNG_SEED,
):
    """Simulate the minimal MNDM SDE: dX = -grad F(X) dt + sigma(t) dW.

    F is a simple radial potential (single attractor) so trajectories can be
    seen descending towards low potential during low-variance ("denoising")
    epochs and exploring outward during high-variance ("exploration")
    epochs. r(t) is an event-locked rhythmic pulse train, and
    sigma(t) = sigma_min + sigma_0 * (1 - r(t)) as in the main text.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(n_steps) * dt
    total_time = n_steps * dt

    # Event-locked rhythmic control: a smoothed square pulse train.
    duty_cycle = 0.35
    phase = (t * rhythm_hz) % 1.0
    r_t = (phase < duty_cycle).astype(float)
    # Smooth the pulse edges slightly so the schedule is not perfectly
    # discontinuous (illustrative only).
    kernel = np.ones(15) / 15
    r_t = np.convolve(r_t, kernel, mode="same")

    sigma_t = sigma_min + sigma_0 * (1 - r_t)

    x = np.zeros((n_steps, 2))
    x[0] = [2.0, 1.5]
    for i in range(1, n_steps):
        pos = x[i - 1]
        drift = -pos  # gradient of a quadratic potential F(X) = 0.5 * ||X||^2
        noise = rng.normal(size=2) * np.sqrt(dt)
        x[i] = pos + drift * dt + sigma_t[i - 1] * noise

    potential = 0.5 * np.sum(x**2, axis=1)
    return {
        "t": t,
        "total_time": total_time,
        "x": x,
        "r_t": r_t,
        "sigma_t": sigma_t,
        "potential": potential,
    }


def simulate_extended_schedules(t: np.ndarray, rhythm_hz: float = 0.5):
    """Illustrative time-varying schedules for the extended MNDM.

    sigma(t), alpha(t), beta(t), gamma(t), delta(t) all carry a small
    rhythm-locked oscillation on top of a baseline, and Trace(G_t) tracks
    their combined attention-geometry weight. These are synthetic
    illustrations of Eq. 2 in the main article, not fitted parameters.
    """
    omega = 2 * np.pi * rhythm_hz
    sigma_t = 0.25 + 0.06 * np.sin(omega * t)
    alpha_t = 0.95 + 0.03 * np.sin(omega * t + 1.2)
    beta_t = 0.30 + 0.05 * np.sin(omega * t + 0.6)
    gamma_t = 0.08 + 0.05 * np.sin(omega * t + 2.1)
    delta_t = 0.06 + 0.04 * np.sin(omega * t + 4.0)
    trace_g = alpha_t + beta_t + gamma_t + delta_t
    return {
        "sigma_t": sigma_t,
        "alpha_t": alpha_t,
        "beta_t": beta_t,
        "gamma_t": gamma_t,
        "delta_t": delta_t,
        "trace_g": trace_g,
    }


# --------------------------------------------------------------------------
# Figure 2: MNDM dynamics (fixes the raw-LaTeX panel-C rendering bug)
# --------------------------------------------------------------------------


def plot_fig2_mndm_dynamics(outpath: pathlib.Path) -> None:
    sim = simulate_minimal_mndm()
    t, x, r_t, sigma_t, potential = (
        sim["t"],
        sim["x"],
        sim["r_t"],
        sim["sigma_t"],
        sim["potential"],
    )
    ext = simulate_extended_schedules(t)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    fig.suptitle("MNDM Dynamics \u2014 The Core Mechanism", fontsize=13, fontweight="bold")

    # --- Panel A: state-space trajectory, colored by local sigma(t) ---
    ax = axes[0, 0]
    theta = np.linspace(0, 2 * np.pi, 100)
    for radius in np.arange(0.5, 3.0, 0.5):
        ax.plot(radius * np.cos(theta), radius * np.sin(theta), color="0.85", lw=0.8, zorder=0)
        ax.annotate(
            f"{0.5 * radius**2:.1f}",
            (radius * np.cos(np.pi / 4), radius * np.sin(np.pi / 4)),
            fontsize=6,
            color="0.6",
        )
    points = x.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    from matplotlib.collections import LineCollection

    lc = LineCollection(segments, cmap="viridis_r", linewidths=0.8)
    lc.set_array(sigma_t[:-1])
    ax.add_collection(lc)
    ax.scatter(*x[0], color="green", s=60, zorder=5, label="Start")
    ax.scatter(*x[-1], color="red", s=60, zorder=5, label="End")
    ax.set_xlim(-1.5, 3)
    ax.set_ylim(-1.5, 2.5)
    ax.set_xlabel(r"$X_1$")
    ax.set_ylabel(r"$X_2$")
    ax.set_title("(A) State-space trajectory, colored by $\\sigma(t)$", fontsize=10)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax.annotate(
        "High $\\sigma$: exploration",
        xy=(1.6, 1.1),
        fontsize=8,
        bbox=dict(boxstyle="round", fc="lightyellow", ec="0.5"),
    )
    ax.annotate(
        "Low $\\sigma$: denoising",
        xy=(-1.3, -0.4),
        fontsize=8,
        bbox=dict(boxstyle="round", fc="honeydew", ec="0.5"),
    )
    ax.set_aspect("equal", adjustable="box")

    # --- Panel B: time series of schedules ---
    ax = axes[0, 1]
    on = r_t > 0.5
    edges = np.flatnonzero(np.diff(on.astype(int)))
    starts = t[edges[::2]] if on[0] else t[np.r_[0, edges[1::2]]]
    for s in np.arange(0, t[-1], 1 / 0.5):
        ax.axvspan(s, s + 0.35 / 0.5, color="navajowhite", alpha=0.4, lw=0)
    ax.plot(t, r_t, color="tab:blue", lw=1.2, label="$r(t)$ \u2014 Rhythmic control")
    ax.plot(t, sigma_t, color="tab:red", lw=1.2, label="$\\sigma(t)$ \u2014 Variance schedule")
    ax.plot(
        t,
        -(potential - potential.min()) / max(potential.max() - potential.min(), 1e-9) * 1.0,
        color="tab:green",
        lw=1.0,
        label="$-F(t)$ (normalized) \u2014 Potential descent",
    )
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Value")
    ax.set_title("(B) Time series of schedules", fontsize=10)
    ax.legend(loc="upper right", fontsize=7, framealpha=0.9)

    # --- Panel C: the minimal equation, cleanly typeset (fixes the bug) ---
    ax = axes[1, 0]
    ax.axis("off")
    ax.set_title("(C) The minimal equation", fontsize=10)
    ax.annotate(
        "Denoising drift",
        xy=(0.30, 0.60),
        xytext=(0.05, 0.92),
        fontsize=8,
        ha="left",
        bbox=dict(boxstyle="round", fc="lightsteelblue", ec="0.5"),
        arrowprops=dict(arrowstyle="->", color="tab:blue"),
    )
    ax.annotate(
        "Exploration noise",
        xy=(0.62, 0.60),
        xytext=(0.62, 0.92),
        fontsize=8,
        ha="left",
        bbox=dict(boxstyle="round", fc="mistyrose", ec="0.5"),
        arrowprops=dict(arrowstyle="->", color="tab:red"),
    )
    equation_lines = (
        r"$dX_t = -\nabla F(X_t,t)\,dt + \sigma(t)\,dW_t$"
        + "\n"
        + r"$F(X,t) = E(X) - R(X)$"
        + "\n"
        + r"$\sigma(t) = \sigma_{\min} + \sigma_0\,(1 - r(t))$"
    )
    ax.text(
        0.5,
        0.45,
        equation_lines,
        fontsize=11,
        ha="center",
        va="center",
        linespacing=2.0,
        bbox=dict(boxstyle="round,pad=0.6", fc="whitesmoke", ec="0.4"),
        transform=ax.transAxes,
    )
    ax.annotate(
        "",
        xy=(0.5, 0.30),
        xytext=(0.5, 0.05),
        arrowprops=dict(arrowstyle="->", color="tab:green", lw=1.5),
    )
    ax.text(
        0.5,
        0.02,
        "Rhythmic control",
        fontsize=8,
        ha="center",
        bbox=dict(boxstyle="round", fc="honeydew", ec="0.5"),
    )

    # --- Panel D: symphony of schedules (extended model) ---
    ax = axes[1, 1]
    ax.plot(t, ext["sigma_t"], color="tab:red", lw=1.1, label=r"$\sigma(t)$")
    ax.plot(t, ext["alpha_t"], color="tab:blue", lw=1.1, label=r"$\alpha(t)$")
    ax.plot(t, ext["beta_t"], color="tab:green", lw=1.1, label=r"$\beta(t)$")
    ax.plot(t, ext["gamma_t"], color="magenta", lw=1.1, label=r"$\gamma(t)$")
    ax.plot(t, ext["delta_t"], color="tab:cyan", lw=1.1, label=r"$\delta(t)$")
    ax.plot(
        t,
        ext["trace_g"],
        color="black",
        lw=1.4,
        ls="--",
        label=r"Trace($\mathbf{G}_t$)",
    )
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Value")
    ax.set_ylim(-0.05, 1.65)
    ax.set_title("(D) Symphony of schedules (extended model)", fontsize=10)
    ax.legend(loc="upper right", fontsize=7, framealpha=0.9, ncol=2)

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(outpath, dpi=200)
    plt.close(fig)


# --------------------------------------------------------------------------
# Flow overview: rhythm -> r(t) -> sigma(t) -> MNDM -> MNPS -> Stage-1 tests
# --------------------------------------------------------------------------


def _box(ax, xy, w, h, text, fc="whitesmoke", ec="0.3", fontsize=9.5):
    x, y = xy
    box = mpatches.FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=1.2,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize, wrap=True)
    return (x, y, w, h)


def _arrow(ax, box_a, box_b, label=None, label_fontsize=8):
    ax_, ay_, aw_, ah_ = box_a
    bx_, by_, bw_, bh_ = box_b
    start = (ax_ + aw_, ay_ + ah_ / 2)
    end = (bx_, by_ + bh_ / 2)
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(arrowstyle="-|>", color="0.2", lw=1.6, shrinkA=2, shrinkB=2),
    )
    if label:
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        ax.text(mx, my + 0.03, label, ha="center", va="bottom", fontsize=label_fontsize, color="0.25")


def plot_fig_flow_overview(outpath: pathlib.Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 3.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    w, h = 0.155, 0.5
    gap = 0.045
    xs = [0.01 + i * (w + gap) for i in range(5)]
    y = 0.25

    b1 = _box(
        ax,
        (xs[0], y),
        w,
        h,
        "Neural rhythm\n(theta\u2013gamma PAC,\nSO\u2013spindle coupling)",
        fc="#eef4fb",
    )
    b2 = _box(ax, (xs[1], y), w, h, r"Rhythmic control" + "\n" + r"$r(t)$", fc="#e8f3e8")
    b3 = _box(
        ax,
        (xs[2], y),
        w,
        h,
        "Variance schedule\n" + r"$\sigma(t)=\sigma_{\min}+\sigma_0(1-r(t))$",
        fc="#fdecec",
        fontsize=8.5,
    )
    b4 = _box(
        ax,
        (xs[3], y),
        w,
        h,
        "MNDM trajectory\n" + r"$dX_t=-\nabla F\,dt+\sigma(t)\,dW_t$" + "\n(explore \u2194 denoise)",
        fc="#fff6e0",
        fontsize=8,
    )
    b5 = _box(
        ax,
        (xs[4], y),
        w,
        h,
        "MNPS chart\n$(m, d, e)$\n\u2192 Stage-1 tests",
        fc="#f1eaf9",
    )

    _arrow(ax, b1, b2)
    _arrow(ax, b2, b3, label="gates")
    _arrow(ax, b3, b4, label="modulates")
    _arrow(ax, b4, b5, label="measured as")

    ax.text(
        0.5,
        0.95,
        "Core NDT flow: from rhythm to a measurable geometric chart",
        ha="center",
        va="top",
        fontsize=11.5,
        fontweight="bold",
    )
    ax.text(
        0.5,
        0.06,
        "Illustrative schematic \u2014 not a fit to data. See main text Eq. 1\u20132 and the MNPS construction (S1).",
        ha="center",
        va="bottom",
        fontsize=7.5,
        color="0.35",
    )

    fig.savefig(outpath, dpi=200, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# RVC gating loop close-up
# --------------------------------------------------------------------------


def plot_fig_rvc_gating_loop(outpath: pathlib.Path) -> None:
    t = np.linspace(0, 4, 800)
    rhythm_hz = 1.0
    phase = 2 * np.pi * rhythm_hz * t
    oscillation = 0.5 * (1 + np.sin(phase))
    duty_cycle = 0.35
    pulse = (((t * rhythm_hz) % 1.0) < duty_cycle).astype(float)
    sigma_t = 0.1 + 0.9 * (1 - pulse)

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw={"width_ratios": [1.1, 1]})

    # Left: conceptual loop diagram.
    ax = axes[0]
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("RVC gating loop", fontsize=11, fontweight="bold")

    centers = {
        "rhythm": (0.5, 0.85),
        "r_t": (0.85, 0.5),
        "sigma_t": (0.5, 0.15),
        "state": (0.15, 0.5),
    }
    labels = {
        "rhythm": "Observed\nneural rhythm",
        "r_t": r"$r(t)$" + "\nevent-locked\npulse",
        "sigma_t": r"$\sigma(t)$" + "\nvariance\nschedule",
        "state": "MNDM state\n(explore/denoise)",
    }
    colors = {"rhythm": "#eef4fb", "r_t": "#e8f3e8", "sigma_t": "#fdecec", "state": "#fff6e0"}
    boxes = {}
    for key, (cx, cy) in centers.items():
        w, hh = 0.30, 0.22
        boxes[key] = _box(ax, (cx - w / 2, cy - hh / 2), w, hh, labels[key], fc=colors[key], fontsize=8)

    order = ["rhythm", "r_t", "sigma_t", "state", "rhythm"]
    for a_key, b_key in zip(order[:-1], order[1:]):
        ax_, ay_, aw_, ah_ = boxes[a_key]
        bx_, by_, bw_, bh_ = boxes[b_key]
        start = (ax_ + aw_ / 2, ay_ + ah_ / 2)
        end = (bx_ + bw_ / 2, by_ + bh_ / 2)
        # shrink towards box edges roughly
        ax.annotate(
            "",
            xy=end,
            xytext=start,
            arrowprops=dict(arrowstyle="-|>", color="0.25", lw=1.4, shrinkA=28, shrinkB=28,
                              connectionstyle="arc3,rad=0.15"),
        )
    ax.text(
        0.5,
        -0.06,
        "Closes back through denoising quality \u2192 measured MNPS geometry \u2192 rhythm re-estimation",
        ha="center",
        va="top",
        fontsize=7,
        color="0.35",
    )

    # Right: example rhythm -> r(t) -> sigma(t) traces.
    ax = axes[1]
    ax.plot(t, oscillation, color="0.6", lw=1.0, ls=":", label="Neural rhythm (schematic)")
    ax.plot(t, pulse, color="tab:blue", lw=1.3, label=r"$r(t)$")
    ax.plot(t, sigma_t, color="tab:red", lw=1.3, label=r"$\sigma(t)$")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Value (a.u.)")
    ax.set_title("Illustrative rhythm \u2192 schedule mapping", fontsize=10)
    ax.legend(loc="upper right", fontsize=7.5, framealpha=0.9)

    fig.tight_layout()
    fig.savefig(outpath, dpi=200)
    plt.close(fig)


# --------------------------------------------------------------------------


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig2_path = FIGURES_DIR / "fig2_mndm_dynamics.png"
    plot_fig2_mndm_dynamics(fig2_path)
    print(f"Wrote {fig2_path}")

    flow_path = FIGURES_DIR / "fig_flow_overview.png"
    plot_fig_flow_overview(flow_path)
    print(f"Wrote {flow_path}")

    rvc_loop_path = FIGURES_DIR / "fig_rvc_gating_loop.png"
    plot_fig_rvc_gating_loop(rvc_loop_path)
    print(f"Wrote {rvc_loop_path}")


if __name__ == "__main__":
    main()
