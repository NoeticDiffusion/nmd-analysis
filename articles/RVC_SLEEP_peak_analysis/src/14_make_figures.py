"""
14_make_figures.py -- Figure generation for the RVC_SLEEP_peak_analysis
follow-up article (peak-phase respiratory/cardiac coupling + alignment
moderation; diary 241/242/243).

Produces five SVG figures from the result CSVs / raw catalog already
written by scripts 11-13 (reads the most recent `results/rvc_sleep_<date>/
<phase>/` outputs found, or reloads the raw `event_phase_v2` catalog where a
figure needs the underlying phase values rather than a summary statistic):

  fig1_resp_peak_rose_plot.svg        -- pooled circular histogram of
                                          phi_resp_peak (23,029 events),
                                          mean direction + R1 annotated
  fig2_per_subject_resp_vs_cardiac.svg -- per-subject mean-direction scatter
                                          (24 points), phi_resp_peak vs.
                                          phi_cardiac_peak side by side
  fig3_duration_tercile_robustness.svg -- R1 and significance per duration
                                          tercile, both channels
  fig4_split_half_replication.svg     -- half A vs. half B pooled + second-
                                          order R, both channels
  fig5_alignment_moderation_scatter.svg -- resp_peak_alignment vs. geometry
                                          delta for the strongest endpoint
                                          found by script 13, with a display
                                          trend line

Each fig*() function is defensive: if the underlying results CSV does not
exist yet (script not run), it prints a message and skips that figure
rather than failing the whole script.

Run: python src/14_make_figures.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from rvc_sleep_support import ARTICLE_DIR, FIGURES_DIR, RESULTS_DIR, circular_mean_resultant

matplotlib.use("Agg")
matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "svg.fonttype": "none",
})

RESP_COLOR = "#1E88E5"
CARDIAC_COLOR = "#E53935"
CHANNEL_COLORS = {"phi_resp_peak": RESP_COLOR, "phi_cardiac_peak": CARDIAC_COLOR}
CHANNEL_LABELS = {"phi_resp_peak": "Respiratory (peak)", "phi_cardiac_peak": "Cardiac (peak)"}
PHASE_V2_DIR = ARTICLE_DIR / "RichSleep_resolved" / "phase_resolved_v2"


def save(fig, name: str) -> None:
    out = FIGURES_DIR / name
    fig.savefig(out, format="svg", bbox_inches="tight", dpi=150)
    print(f"  Saved {out.relative_to(FIGURES_DIR.parents[0])}")
    plt.close(fig)


def find_latest(glob_pattern: str):
    candidates = sorted(RESULTS_DIR.glob(glob_pattern))
    return candidates[-1] if candidates else None


def load_full_catalog() -> pd.DataFrame:
    phase_files = sorted(PHASE_V2_DIR.glob("*_event_phase_v2.parquet"))
    frames = []
    for p in phase_files:
        d = pd.read_parquet(p)
        d["subject_id"] = f"sub-{p.stem.replace('_event_phase_v2', '')}"
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


# ──────────────────────────────────────────────────────────────────────────────
# Fig 1: pooled rose plot of phi_resp_peak
# ──────────────────────────────────────────────────────────────────────────────
def fig1_resp_peak_rose_plot(full_df: pd.DataFrame) -> None:
    phases = full_df["phi_resp_peak"].dropna().to_numpy()
    if len(phases) == 0:
        print("  [skip] fig1: no phi_resp_peak values in full catalog")
        return
    angle, r, n = circular_mean_resultant(phases)

    n_bins = 32
    bins = np.linspace(-np.pi, np.pi, n_bins + 1)
    counts, _ = np.histogram(phases, bins=bins)
    widths = np.diff(bins)
    centers = bins[:-1] + widths / 2

    fig = plt.figure(figsize=(4.6, 4.6))
    ax = fig.add_subplot(111, projection="polar")
    ax.bar(centers, counts, width=widths * 0.95, bottom=0.0, color=RESP_COLOR,
           alpha=0.75, edgecolor="white", linewidth=0.3)
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(1)
    ax.annotate(
        "", xy=(angle, counts.max() * min(r * 3, 1.0)), xytext=(angle, 0),
        arrowprops=dict(facecolor="black", edgecolor="black", width=1.5, headwidth=7, shrink=0.0),
    )
    ax.set_title(
        f"Spindle-peak respiratory phase (n={n} events, pooled)\n"
        f"mean direction = {np.degrees(angle):.1f} deg, R1 = {r:.3f}",
        fontsize=9,
    )
    ax.set_yticklabels([])
    fig.tight_layout()
    save(fig, "fig1_resp_peak_rose_plot.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 2: per-subject mean-direction scatter, resp vs. cardiac
# ──────────────────────────────────────────────────────────────────────────────
def fig2_per_subject_resp_vs_cardiac() -> None:
    path = find_latest("rvc_sleep_*/11_richsleep_maalb_corrected/molB_per_subject_rayleigh.csv")
    if path is None:
        print("  [skip] fig2: molB_per_subject_rayleigh.csv not found yet")
        return
    df = pd.read_csv(path)
    df = df[df["sample"] == "full_catalog"]
    if df.empty:
        print("  [skip] fig2: no full_catalog rows")
        return

    channels = ["phi_resp_peak", "phi_cardiac_peak"]
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 4.2), subplot_kw={"projection": "polar"})
    for ax, channel in zip(axes, channels):
        sub = df[df["channel"] == channel].dropna(subset=["mean_angle_rad", "R"])
        ax.scatter(sub["mean_angle_rad"], sub["R"], s=45, color=CHANNEL_COLORS[channel],
                   alpha=0.8, edgecolor="black", linewidth=0.4, zorder=3)
        pop_angle, pop_r, pop_n = circular_mean_resultant(sub["mean_angle_rad"].to_numpy())
        ax.annotate(
            "", xy=(pop_angle, min(pop_r, 1.0)), xytext=(pop_angle, 0),
            arrowprops=dict(facecolor="black", edgecolor="black", width=1.5, headwidth=7, shrink=0.0),
            zorder=4,
        )
        ax.set_theta_zero_location("E")
        ax.set_theta_direction(1)
        ax.set_ylim(0, 1.0)
        ax.set_title(
            f"{CHANNEL_LABELS[channel]}\n(n={len(sub)} subjects; "
            f"2nd-order R={pop_r:.3f})",
            fontsize=9,
        )
    fig.suptitle("Per-subject mean peak-phase direction (radius = within-subject R)", fontsize=10)
    fig.tight_layout()
    save(fig, "fig2_per_subject_resp_vs_cardiac.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 3: duration-tercile robustness
# ──────────────────────────────────────────────────────────────────────────────
def fig3_duration_tercile_robustness() -> None:
    path = find_latest("rvc_sleep_*/12_richsleep_maalb_peak_phase_deepdive/check2_duration_tercile_stratified.csv")
    if path is None:
        print("  [skip] fig3: check2_duration_tercile_stratified.csv not found yet")
        return
    df = pd.read_csv(path)
    if df.empty:
        print("  [skip] fig3: no usable rows")
        return

    terciles = ["short", "mid", "long"]
    channels = ["phi_resp_peak", "phi_cardiac_peak"]
    x = np.arange(len(terciles))
    width = 0.35
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    for i, channel in enumerate(channels):
        sub = df[df["channel"] == channel].set_index("duration_tercile").reindex(terciles)
        bars = ax.bar(x + (i - 0.5) * width, sub["obs_R1"], width,
                       label=CHANNEL_LABELS[channel], color=CHANNEL_COLORS[channel], alpha=0.85)
        for xi, (r1, p) in enumerate(zip(sub["obs_R1"], sub["perm_p_R1"])):
            if pd.notna(r1) and pd.notna(p) and p < 0.05:
                ax.annotate("*", (x[xi] + (i - 0.5) * width, r1), ha="center", va="bottom",
                            fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([t.capitalize() for t in terciles])
    ax.set_xlabel("Spindle-duration tercile")
    ax.set_ylabel("Pooled R1 (subject-rotation\npermutation test)")
    ax.set_title("Duration-tercile-stratified robustness\n(* = perm p<0.05, within-tercile)")
    ax.legend()
    fig.tight_layout()
    save(fig, "fig3_duration_tercile_robustness.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 4: split-half replication
# ──────────────────────────────────────────────────────────────────────────────
def fig4_split_half_replication() -> None:
    path = find_latest("rvc_sleep_*/12_richsleep_maalb_peak_phase_deepdive/check4_split_half_replication.csv")
    if path is None:
        print("  [skip] fig4: check4_split_half_replication.csv not found yet")
        return
    df = pd.read_csv(path)
    if df.empty:
        print("  [skip] fig4: no usable rows")
        return

    halves = ["half_A_first12", "half_B_last12"]
    half_labels = {"half_A_first12": "Half A\n(sub-xn001..012)", "half_B_last12": "Half B\n(sub-xn013..024)"}
    channels = ["phi_resp_peak", "phi_cardiac_peak"]
    x = np.arange(len(halves))
    width = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6), sharey=True)
    for ax, (metric, metric_label) in zip(
        axes, [("pooled_R1", "Pooled R1"), ("second_order_R", "Second-order R\n(24 subject means)")]
    ):
        for i, channel in enumerate(channels):
            sub = df[df["channel"] == channel].set_index("half").reindex(halves)
            p_col = "pooled_perm_p_R1" if metric == "pooled_R1" else "second_order_p"
            bars = ax.bar(x + (i - 0.5) * width, sub[metric], width,
                           label=CHANNEL_LABELS[channel], color=CHANNEL_COLORS[channel], alpha=0.85)
            for xi, (val, p) in enumerate(zip(sub[metric], sub[p_col])):
                if pd.notna(val) and pd.notna(p) and p < 0.05:
                    ax.annotate("*", (x[xi] + (i - 0.5) * width, val), ha="center", va="bottom",
                                fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([half_labels[h] for h in halves], fontsize=7.5)
        ax.set_ylabel(metric_label)
        ax.set_title(metric_label)
    axes[-1].legend(loc="upper right", fontsize=7.5)
    fig.suptitle("Deterministic split-half self-replication (* = p<0.05)", fontsize=10)
    fig.tight_layout()
    save(fig, "fig4_split_half_replication.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 5: alignment-moderation scatter (strongest endpoint from script 13)
# ──────────────────────────────────────────────────────────────────────────────
def fig5_alignment_moderation_scatter() -> None:
    align_path = find_latest("rvc_sleep_*/13_peak_phase_alignment_moderation/resp_peak_alignment_moderation.csv")
    mu_path = find_latest("rvc_sleep_*/13_peak_phase_alignment_moderation/held_out_mu_resp_peak.csv")
    merged_path = find_latest("rvc_sleep_*/10_richsleep_phase_resolved_eap/richsleep_event_phase_merged.parquet")
    if align_path is None or mu_path is None or merged_path is None:
        print("  [skip] fig5: script 10/13 outputs not found yet")
        return

    align_df = pd.read_csv(align_path).dropna(subset=["alignment_p_fdr"])
    if align_df.empty:
        print("  [skip] fig5: no usable alignment-moderation rows")
        return
    best = align_df.sort_values("alignment_p_fdr").iloc[0]
    delta_mode, endpoint = best["delta_mode"], best["endpoint"]

    mu_resp_peak = pd.read_csv(mu_path)["mu_resp_peak_rad"].iloc[0]
    merged = pd.read_parquet(merged_path)
    merged["resp_peak_alignment"] = np.cos(merged["phi_resp_peak"] - mu_resp_peak)

    baseline_col = f"{endpoint}_control_median" if delta_mode == "event_control" else f"{endpoint}_far"
    sub = merged.dropna(subset=[endpoint, baseline_col, "resp_peak_alignment"]).copy()
    sub["delta"] = sub[endpoint] - sub[baseline_col]

    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    subjects = sorted(sub["subject_id"].unique())
    cmap = plt.get_cmap("tab20")
    for i, subj in enumerate(subjects):
        s = sub[sub["subject_id"] == subj]
        ax.scatter(s["resp_peak_alignment"], s["delta"], s=22, color=cmap(i % 20), alpha=0.75,
                   edgecolor="none", label=None)

    b, a = np.polyfit(sub["resp_peak_alignment"].to_numpy(), sub["delta"].to_numpy(), 1)
    xs = np.linspace(sub["resp_peak_alignment"].min(), sub["resp_peak_alignment"].max(), 100)
    ax.plot(xs, a + b * xs, color="black", linewidth=1.6, linestyle="--",
            label=f"display trend (slope={b:.3f})")
    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_xlabel(r"$\cos(\phi_{resp,peak} - \mu_{resp,peak})$  (resp_peak_alignment)")
    ax.set_ylabel(f"{endpoint} delta ({delta_mode})")
    p_fdr = best["alignment_p_fdr"]
    ax.set_title(
        f"Strongest alignment-moderation result: {endpoint} ({delta_mode})\n"
        f"WLS-cluster coef={best['alignment_coef']:.3f}, p={best['alignment_p']:.4f}, "
        f"BH-FDR q={p_fdr:.4f} (18-test family)",
        fontsize=8.5,
    )
    ax.legend(fontsize=7.5, loc="best")
    fig.tight_layout()
    save(fig, "fig5_alignment_moderation_scatter.svg")


if __name__ == "__main__":
    print("Generating RVC_SLEEP_peak_analysis figures ...")
    full_catalog = load_full_catalog()
    fig1_resp_peak_rose_plot(full_catalog)
    fig2_per_subject_resp_vs_cardiac()
    fig3_duration_tercile_robustness()
    fig4_split_half_replication()
    fig5_alignment_moderation_scatter()
    print(f"\nDone. Figures directory: {FIGURES_DIR}")
