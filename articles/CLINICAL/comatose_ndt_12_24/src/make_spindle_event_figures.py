from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ARTICLE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = ARTICLE_DIR / "results"
WINDOW_DIR = RESULTS_DIR / "window_event_locked"
FIG_DIR = ARTICLE_DIR / "figures"

BINS = ["pre_far", "pre_near", "event", "post_near", "post_far"]
CHANNELS = ["psg_c3", "psg_f3"]
CHANNEL_LABELS = {"psg_c3": "PSG_C3", "psg_f3": "PSG_F3"}
CHANNEL_COLORS = {"psg_c3": "#1f77b4", "psg_f3": "#d62728"}


def p_stars(p_value: float) -> str:
    if not np.isfinite(p_value):
        return ""
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    return ""


def save(fig: plt.Figure, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / name, format="svg", bbox_inches="tight")
    plt.close(fig)


def event_locking_schema() -> None:
    rng = np.random.default_rng(20260509)
    t = np.linspace(-35, 35, 1600)
    sigma = np.sin(2 * np.pi * 13.5 * t)
    envelope = np.exp(-0.5 * ((t - 0.6) / 1.0) ** 2)
    slow = 0.18 * np.sin(2 * np.pi * 0.8 * t + 0.4)
    noise = 0.08 * rng.normal(size=t.size)
    signal = slow + 0.75 * envelope * sigma + noise

    bins = [
        ("pre_far", -30, -10, "#dce9f8"),
        ("pre_near", -10, 0, "#e7f2ff"),
        ("event", 0, 3, "#ffd8bf"),
        ("post_near", 3, 10, "#fff0df"),
        ("post_far", 10, 30, "#eeeeee"),
    ]

    fig, ax = plt.subplots(figsize=(10.5, 3.0))
    for label, lo, hi, color in bins:
        ax.axvspan(lo, hi, color=color, alpha=0.82, linewidth=0)
        ax.text((lo + hi) / 2, 1.35, label, ha="center", va="center", fontsize=9)
    ax.plot(t, signal, color="#222222", linewidth=0.9)
    ax.axvline(0, color="#d62728", linewidth=1.4)
    ax.text(0, -1.35, "spindle peak alignment", ha="center", va="center", color="#d62728", fontsize=9)
    ax.set_xlim(-32, 32)
    ax.set_ylim(-1.55, 1.55)
    ax.set_xlabel("Time relative to spindle peak (s)")
    ax.set_ylabel("schematic EEG")
    ax.set_title("Event-locked sleep spindle design")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "fig_event_locking_schema_sleep_spindle.svg")


def subject_delta_dbc() -> None:
    deltas = pd.read_csv(RESULTS_DIR / "subject_deltas.csv")
    data = deltas[
        (deltas["metric"] == "d")
        & (deltas["contrast"] == "event_minus_export_baseline")
        & (deltas["target_qc_pass"])
    ].copy()
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    rng = np.random.default_rng(7)
    positions = {"psg_c3": 0, "psg_f3": 1}
    for channel in CHANNELS:
        vals = data[data["channel"] == channel]["delta"].to_numpy(dtype=float)
        x = positions[channel] + rng.normal(0, 0.045, size=vals.size)
        ax.scatter(x, vals, s=18, alpha=0.62, color=CHANNEL_COLORS[channel], edgecolor="none")
        median = float(np.median(vals))
        lo, hi = np.quantile(
            np.median(rng.choice(vals, size=(5000, vals.size), replace=True), axis=1),
            [0.025, 0.975],
        )
        ax.plot([positions[channel] - 0.18, positions[channel] + 0.18], [median, median],
                color="#111111", linewidth=2.0)
        ax.vlines(positions[channel], lo, hi, color="#111111", linewidth=1.3)
        ax.text(positions[channel], hi + 0.035, f"{int((vals > 0).sum())}/{vals.size} positive",
                ha="center", va="bottom", fontsize=9)
    ax.axhline(0, color="#777777", linestyle="--", linewidth=0.9)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["PSG_C3\nprimary", "PSG_F3\nsensitivity"])
    ax.set_ylabel("Event-bin Delta d_bc")
    ax.set_title("Subject-level spindle event shift in MNPS-d")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "fig_subject_delta_dbc_qc_pass.svg")


def mnps_line_profiles() -> None:
    profile = pd.read_csv(RESULTS_DIR / "event_profile_summary.csv")
    metrics = ["m", "d", "e"]
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.4), sharex=True)
    for ax, metric in zip(axes, metrics):
        for channel in CHANNELS:
            sub = profile[
                (profile["scenario"] == "all_subjects")
                & (profile["value_kind"] == "bc")
                & (profile["metric"] == metric)
                & (profile["channel"] == channel)
            ].set_index("bin").loc[BINS].reset_index()
            x = np.arange(len(BINS))
            y = sub["median"].to_numpy(dtype=float)
            lo = sub["median_boot_ci_low"].to_numpy(dtype=float)
            hi = sub["median_boot_ci_high"].to_numpy(dtype=float)
            ax.plot(x, y, marker="o", linewidth=1.7, color=CHANNEL_COLORS[channel],
                    label=CHANNEL_LABELS[channel])
            ax.fill_between(x, lo, hi, color=CHANNEL_COLORS[channel], alpha=0.16, linewidth=0)
        ax.axhline(0, color="#777777", linestyle="--", linewidth=0.8)
        ax.axvline(2, color="#bbbbbb", linestyle=":", linewidth=0.8)
        ax.set_title(f"{metric}_bc")
        ax.set_xticks(np.arange(len(BINS)))
        ax.set_xticklabels(BINS, rotation=35, ha="right")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Baseline-corrected median")
    axes[0].legend(frameon=False)
    fig.suptitle("Event-locked MNPS profiles around detected N2 spindles", y=1.03)
    save(fig, "fig_mnps_event_locked_line_profiles.svg")


def d_profile_with_pre_post() -> None:
    profile = pd.read_csv(RESULTS_DIR / "event_profile_summary.csv")
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    for channel in CHANNELS:
        sub = profile[
            (profile["scenario"] == "qc_pass_only")
            & (profile["value_kind"] == "bc")
            & (profile["metric"] == "d")
            & (profile["channel"] == channel)
        ].set_index("bin").loc[BINS].reset_index()
        x = np.arange(len(BINS))
        y = sub["median"].to_numpy(dtype=float)
        lo = sub["median_boot_ci_low"].to_numpy(dtype=float)
        hi = sub["median_boot_ci_high"].to_numpy(dtype=float)
        ax.plot(x, y, marker="o", linewidth=2.2, color=CHANNEL_COLORS[channel],
                label=CHANNEL_LABELS[channel])
        ax.fill_between(x, lo, hi, color=CHANNEL_COLORS[channel], alpha=0.16, linewidth=0)
    ax.axhline(0, color="#777777", linestyle="--", linewidth=0.9)
    ax.axvline(2, color="#d62728", linestyle=":", linewidth=1.0)
    ax.set_xticks(np.arange(len(BINS)))
    ax.set_xticklabels(BINS, rotation=30, ha="right")
    ax.set_ylabel("Median Delta d_bc")
    ax.set_title("Primary event-locked MNPS-d profile")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "fig_primary_d_event_locked_line.svg")


def stratified_9d_bar_overview() -> None:
    summary = pd.read_csv(WINDOW_DIR / "event_minus_pre_far_test_summary.csv")
    sub = summary[(summary["family"] == "mnps9d")].copy()
    metric_order = ["m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2), sharey=True)
    for ax, channel in zip(axes, CHANNELS):
        s = sub[sub["channel"] == channel].set_index("metric").loc[metric_order].reset_index()
        colors = ["#d62728" if v > 0 else "#1f77b4" for v in s["cohens_dz"]]
        ax.barh(np.arange(len(metric_order)), s["cohens_dz"], color=colors, alpha=0.82)
        ax.axvline(0, color="#333333", linewidth=0.8)
        ax.set_yticks(np.arange(len(metric_order)))
        ax.set_yticklabels(metric_order)
        ax.set_xlabel("Cohen dz (event - pre_far)")
        ax.set_title(CHANNEL_LABELS[channel])
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Stratified 9D MNPS effect-size overview")
    save(fig, "fig_stratified_9d_effect_bars.svg")


def stratified_9d_profiles_3x3() -> None:
    profile = pd.read_csv(WINDOW_DIR / "window_9d_profile_summary.csv")
    metric_order = ["m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"]
    fig, axes = plt.subplots(3, 3, figsize=(10.8, 8.2), sharex=True)
    for ax, metric in zip(axes.ravel(), metric_order):
        for channel in CHANNELS:
            sub = profile[
                (profile["metric"] == metric)
                & (profile["channel"] == channel)
            ].set_index("bin").loc[BINS].reset_index()
            x = np.arange(len(BINS))
            y = sub["median"].to_numpy(dtype=float)
            ax.plot(
                x,
                y,
                marker="o",
                linewidth=1.5,
                markersize=4,
                color=CHANNEL_COLORS[channel],
                label=CHANNEL_LABELS[channel],
            )
        ax.axhline(0, color="#777777", linestyle="--", linewidth=0.7)
        ax.axvline(2, color="#bbbbbb", linestyle=":", linewidth=0.7)
        ax.set_title(metric, fontsize=10)
        ax.set_xticks(np.arange(len(BINS)))
        ax.set_xticklabels(BINS, rotation=35, ha="right", fontsize=8)
        ax.tick_params(axis="y", labelsize=8)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0, 0].set_ylabel("Median bin mean")
    axes[1, 0].set_ylabel("Median bin mean")
    axes[2, 0].set_ylabel("Median bin mean")
    axes[0, 0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Event-locked Stratified 9D MNPS profiles (3x3 layout)", y=0.995)
    fig.tight_layout()
    save(fig, "fig_9d_event_locked_profiles_3x3.svg")


def cohen_heatmap_with_pstars() -> None:
    summary = pd.read_csv(WINDOW_DIR / "event_minus_pre_far_test_summary.csv")
    keep_metrics = [
        "m", "d", "e", "mnps_speed",
        "m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m",
        "jac_spectral_radius", "jac_dot_frobenius", "jac_frobenius", "jac_rotation_ratio",
    ]
    labels = []
    matrix = []
    ann = []
    for metric in keep_metrics:
        rows = []
        ann_rows = []
        for channel in CHANNELS:
            hit = summary[(summary["metric"] == metric) & (summary["channel"] == channel)]
            if hit.empty:
                rows.append(np.nan)
                ann_rows.append("")
            else:
                r = hit.iloc[0]
                rows.append(float(r["cohens_dz"]))
                ann_rows.append(f"{float(r['cohens_dz']):.2f}{p_stars(float(r['p']))}")
        labels.append(metric)
        matrix.append(rows)
        ann.append(ann_rows)
    arr = np.asarray(matrix, dtype=float)
    vmax = max(2.0, float(np.nanmax(np.abs(arr))))
    fig, ax = plt.subplots(figsize=(5.9, 8.6))
    im = ax.imshow(arr, cmap="coolwarm", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(CHANNELS)))
    ax.set_xticklabels([CHANNEL_LABELS[c] for c in CHANNELS])
    ax.set_yticks(np.arange(len(labels)))
    ax.set_yticklabels(labels)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            text_color = "white" if np.isfinite(arr[i, j]) and abs(arr[i, j]) > vmax * 0.45 else "#111111"
            ax.text(j, i, ann[i][j], ha="center", va="center", fontsize=8.5, color=text_color)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Cohen dz")
    ax.set_title("Event-minus-pre_far effect sizes with p-value stars")
    ax.text(
        0.5, -0.065,
        "* p<0.05, ** p<0.01, *** p<0.001",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=8,
    )
    save(fig, "fig_cohen_dz_heatmap_with_pstars.svg")


def main() -> None:
    event_locking_schema()
    subject_delta_dbc()
    mnps_line_profiles()
    d_profile_with_pre_post()
    stratified_9d_profiles_3x3()
    stratified_9d_bar_overview()
    cohen_heatmap_with_pstars()
    print(f"Wrote figures to {FIG_DIR}")


if __name__ == "__main__":
    main()
