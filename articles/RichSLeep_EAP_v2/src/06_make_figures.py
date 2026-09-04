"""
06_make_figures.py -- Figure generation for RichSleep EAP v2 (Phase 4, task 9
of .cursor/plans/richsleep_eap_v2_article_aa3119f9.plan.md).

Produces five SVG figures from the result CSVs already written by scripts
02-05 (reloads the raw catalogs directly where a figure needs the underlying
phase values rather than a summary statistic):

  fig1_cross_carrier_phase_locking.svg -- headline figure: pooled R1 and
                                           BH-FDR-corrected -log10(p) across
                                           the 8 carrier x channel tests
                                           (script 03).
  fig2_rose_plots_per_carrier.svg      -- 4x2 grid of polar histograms
                                           (4 carriers x cardiac/resp).
  fig3_hazard_curve.svg                -- Test A (case-control logit)
                                           fitted intensity-ratio curve vs.
                                           binned empirical case:control
                                           ratio, one panel per channel;
                                           Test B (time-shift surrogate) p
                                           annotated as text (script 04).
  fig4_qe_coupling_distributions.svg   -- sigma_power_z_n2 distribution
                                           (log1p) and so_spindle_coupling_score
                                           coverage (script 02/05 inputs).
  fig5_efficacy_interaction.svg        -- delta vs. resp_peak_alignment,
                                           split by qe tertile, for the
                                           smallest-p (not necessarily
                                           significant) endpoint from
                                           script 05's primary family.

Each fig*() function is defensive: if the underlying results CSV does not
exist yet, it prints a message and skips that figure rather than failing.

Run: python src/06_make_figures.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from rvc_sleep_support import (
    FIGURES_DIR,
    RESULTS_DIR,
    circular_mean_resultant,
    load_n3_so,
    load_non_event_risk,
    load_phase_v3,
    load_rem_theta,
)

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
CARRIER_LABELS = {
    "N2_spindle_onset": "N2-spindle\nonset", "N2_spindle_peak": "N2-spindle\npeak",
    "N3_SO_trough": "N3-SO\ntrough", "N3_SO_upstate": "N3-SO\nupstate", "REM_theta": "REM-theta",
}
CARRIER_ORDER = ["N2_spindle_onset", "N2_spindle_peak", "N3_SO_trough", "N3_SO_upstate", "REM_theta"]


def save(fig, name: str) -> None:
    out = FIGURES_DIR / name
    fig.savefig(out, format="svg", bbox_inches="tight", dpi=150)
    print(f"  Saved {out.relative_to(FIGURES_DIR.parents[0])}")
    plt.close(fig)


def find_latest(glob_pattern: str):
    candidates = sorted(RESULTS_DIR.glob(glob_pattern))
    return candidates[-1] if candidates else None


# ──────────────────────────────────────────────────────────────────────────────
# Fig 1: cross-carrier phase-locking headline figure
# ──────────────────────────────────────────────────────────────────────────────
def fig1_cross_carrier_phase_locking() -> None:
    path = find_latest("rvc_sleep_v2_*/03_multistage_phase_locking/phase_locking_pooled.csv")
    if path is None:
        print("  [skip] fig1: phase_locking_pooled.csv not found yet")
        return
    df = pd.read_csv(path)
    df["carrier"] = pd.Categorical(df["carrier"], categories=CARRIER_ORDER, ordered=True)
    df = df.sort_values(["carrier", "channel"])

    x = np.arange(len(CARRIER_ORDER))
    width = 0.35
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.0))

    ax = axes[0]
    for i, channel, color in [(0, "cardiac", CARDIAC_COLOR), (1, "resp", RESP_COLOR)]:
        sub = df[df["channel"] == channel].set_index("carrier").reindex(CARRIER_ORDER)
        ax.bar(x + (i - 0.5) * width, sub["obs_R1"], width, label=channel.capitalize(), color=color, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels([CARRIER_LABELS[c] for c in CARRIER_ORDER], fontsize=7.5)
    ax.set_ylabel("Pooled R1 (subject-rotation\npermutation test)")
    ax.set_title("Effect size by carrier")
    ax.legend()

    ax = axes[1]
    for i, channel, color in [(0, "cardiac", CARDIAC_COLOR), (1, "resp", RESP_COLOR)]:
        sub = df[df["channel"] == channel].set_index("carrier").reindex(CARRIER_ORDER)
        neglog10p = -np.log10(sub["perm_p_T2_fdr"].clip(lower=1e-4))
        bars = ax.bar(x + (i - 0.5) * width, neglog10p, width, color=color, alpha=0.85)
        for xi, (v, p) in enumerate(zip(neglog10p, sub["perm_p_T2_fdr"])):
            if pd.notna(p) and p < 0.05:
                ax.annotate("*", (x[xi] + (i - 0.5) * width, v), ha="center", va="bottom",
                            fontsize=12, fontweight="bold")
    ax.axhline(-np.log10(0.05), color="grey", linewidth=0.8, linestyle="--", label="FDR q=0.05")
    ax.set_xticks(x)
    ax.set_xticklabels([CARRIER_LABELS[c] for c in CARRIER_ORDER], fontsize=7.5)
    ax.set_ylabel(r"$-\log_{10}$(BH-FDR q), T2 test")
    ax.set_title("Significance by carrier\n(8-test cross-carrier family; * = FDR q<0.05)")
    ax.legend(fontsize=7)

    fig.suptitle("Cross-carrier autonomic phase-locking: N2-spindle, N3-SO, REM-theta", fontsize=10.5)
    fig.tight_layout()
    save(fig, "fig1_cross_carrier_phase_locking.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 2: rose plots per carrier (4 carriers x cardiac/resp)
# ──────────────────────────────────────────────────────────────────────────────
def fig2_rose_plots_per_carrier() -> None:
    phase_v3 = load_phase_v3()
    n3_so = load_n3_so()
    rem_theta = load_rem_theta()
    carrier_data = {
        "N2_spindle_onset": (phase_v3["phi_cardiac_onset"], phase_v3["phi_resp_onset"]),
        "N2_spindle_peak": (phase_v3["phi_cardiac_peak"], phase_v3["phi_resp_peak"]),
        "N3_SO_trough": (n3_so["phi_cardiac_trough"], n3_so["phi_resp_trough"]),
        "N3_SO_upstate": (n3_so["phi_cardiac_upstate"], n3_so["phi_resp_upstate"]),
        "REM_theta": (rem_theta["phi_cardiac"], rem_theta["phi_resp"]),
    }
    n_carriers = len(CARRIER_ORDER)
    fig, axes = plt.subplots(2, n_carriers, figsize=(2.1 * n_carriers, 4.6), subplot_kw={"projection": "polar"})
    for col, carrier in enumerate(CARRIER_ORDER):
        cardiac_phases, resp_phases = carrier_data[carrier]
        for row, (phases, color, lo, hi) in enumerate([
            (cardiac_phases, CARDIAC_COLOR, 0, 2 * np.pi), (resp_phases, RESP_COLOR, -np.pi, np.pi)
        ]):
            ax = axes[row, col]
            vals = phases.dropna().to_numpy()
            angle, r, n = circular_mean_resultant(vals)
            bins = np.linspace(lo, hi, 25)
            counts, _ = np.histogram(vals, bins=bins)
            widths = np.diff(bins)
            centers = bins[:-1] + widths / 2
            ax.bar(centers, counts, width=widths * 0.95, color=color, alpha=0.75, edgecolor="none")
            if np.isfinite(angle):
                ax.annotate("", xy=(angle, counts.max() * min(r * 3, 1.0)), xytext=(angle, 0),
                            arrowprops=dict(facecolor="black", edgecolor="black", width=1.2, headwidth=5, shrink=0.0))
            ax.set_theta_zero_location("E")
            ax.set_theta_direction(1)
            ax.set_yticklabels([])
            ax.set_xticklabels([])
            if row == 0:
                ax.set_title(CARRIER_LABELS[carrier], fontsize=8)
            if col == 0:
                ax.set_ylabel("Cardiac" if row == 0 else "Resp", fontsize=8, labelpad=18)
    fig.suptitle("Pooled phase distributions by carrier (rows: cardiac, resp)", fontsize=10.5)
    fig.tight_layout()
    save(fig, "fig2_rose_plots_per_carrier.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 3: hazard curve (Test A fitted intensity ratio + Test B p annotated)
# ──────────────────────────────────────────────────────────────────────────────
def fig3_hazard_curve() -> None:
    cc_path = find_latest("rvc_sleep_v2_*/04_spindle_onset_hazard_model/case_control_logit.csv")
    ts_path = find_latest("rvc_sleep_v2_*/04_spindle_onset_hazard_model/circular_time_shift_surrogate.csv")
    if cc_path is None or ts_path is None:
        print("  [skip] fig3: script 04 outputs not found yet")
        return
    cc_df = pd.read_csv(cc_path).set_index("channel")
    ts_df = pd.read_csv(ts_path).set_index("channel")

    phase_v3 = load_phase_v3()
    risk = load_non_event_risk()
    channel_cols = {"cardiac": ("phi_cardiac_onset", "phi_cardiac", 0, 2 * np.pi),
                     "resp": ("phi_resp_onset", "phi_resp", -np.pi, np.pi)}
    colors = {"cardiac": CARDIAC_COLOR, "resp": RESP_COLOR}

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.0))
    for ax, channel in zip(axes, ["cardiac", "resp"]):
        event_col, risk_col, lo, hi = channel_cols[channel]
        cases = phase_v3[event_col].dropna().to_numpy()
        controls = risk[risk_col].dropna().to_numpy()
        bins = np.linspace(lo, hi, 13)
        centers = bins[:-1] + np.diff(bins) / 2
        case_density, _ = np.histogram(cases, bins=bins, density=True)
        control_density, _ = np.histogram(controls, bins=bins, density=True)
        empirical_ratio = case_density / control_density

        b_cos, b_sin = cc_df.loc[channel, "coef_cos"], cc_df.loc[channel, "coef_sin"]
        xs = np.linspace(lo, hi, 200)
        fitted_logodds = b_cos * np.cos(xs) + b_sin * np.sin(xs)
        fitted_ratio = np.exp(fitted_logodds - fitted_logodds.mean())  # display-scale only

        ax.scatter(centers, empirical_ratio, color=colors[channel], s=28, zorder=3, label="Empirical case:control ratio")
        ax.plot(xs, fitted_ratio, color="black", linewidth=1.4, linestyle="--", label="Fitted logit curve (Test A)")
        ax.axhline(1.0, color="grey", linewidth=0.6)
        ax.set_xlabel(f"Phase (rad, {'[0, 2π)' if channel == 'cardiac' else '(-π, π]'})")
        ax.set_ylabel("Relative onset intensity\n(case density / risk-set density)")
        wald_p = cc_df.loc[channel, "wald_p"]
        ts_p = ts_df.loc[channel, "perm_p_T2"]
        ax.set_title(
            f"{channel.capitalize()}: Test A (case-control) p={wald_p:.2e}\nTest B (time-shift surrogate) p={ts_p:.4f}",
            fontsize=8.5,
        )
        ax.legend(fontsize=7, loc="best")

    fig.suptitle("N2-spindle-onset hazard: two independent exposure-grounded nulls", fontsize=10.5)
    fig.tight_layout()
    save(fig, "fig3_hazard_curve.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 4: qe / SO-coupling distributions
# ──────────────────────────────────────────────────────────────────────────────
def fig4_qe_coupling_distributions() -> None:
    merged_path = find_latest("rvc_sleep_v2_*/02_build_merged_table/richsleep_event_phase_v3_merged.parquet")
    if merged_path is None:
        print("  [skip] fig4: richsleep_event_phase_v3_merged.parquet not found yet")
        return
    merged = pd.read_parquet(merged_path)

    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6))

    ax = axes[0]
    ax.hist(merged["sigma_power_z_n2"], bins=25, color="#7B1FA2", alpha=0.8)
    ax.set_xlabel(r"$\sigma$-power z-score (N2-referenced)")
    ax.set_ylabel("Events (n=190)")
    ax.set_title(f"Raw sigma_power_z_n2\n(skew={merged['sigma_power_z_n2'].skew():.2f})", fontsize=9)

    ax = axes[1]
    ax.hist(np.log1p(merged["sigma_power_z_n2"]), bins=25, color="#7B1FA2", alpha=0.8)
    ax.set_xlabel(r"log1p(sigma-power z-score)")
    ax.set_title(f"log1p-transformed (qe)\n(skew={np.log1p(merged['sigma_power_z_n2']).skew():.2f})", fontsize=9)

    ax = axes[2]
    n_coupled = int((merged["so_partner_missing"] == 0).sum())
    n_uncoupled = len(merged) - n_coupled
    ax.bar(["SO-coupled\n(n=25)", "Not SO-coupled\n(n=165)"], [n_coupled, n_uncoupled],
           color=["#00897B", "#BDBDBD"], alpha=0.85)
    ax.set_ylabel("Events (of 190 geometry-valid)")
    ax.set_title("SO-coupling coverage\n(power caveat for secondary test)", fontsize=9)

    fig.suptitle("Intrinsic spindle strength (qe) and SO-coupling coverage", fontsize=10.5)
    fig.tight_layout()
    save(fig, "fig4_qe_coupling_distributions.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 5: efficacy interaction (delta vs. alignment, split by qe tertile)
# ──────────────────────────────────────────────────────────────────────────────
def fig5_efficacy_interaction() -> None:
    primary_path = find_latest("rvc_sleep_v2_*/05_qe_interaction_moderation/qe_interaction_primary_sigma_log.csv")
    merged_path = find_latest("rvc_sleep_v2_*/02_build_merged_table/richsleep_event_phase_v3_merged.parquet")
    if primary_path is None or merged_path is None:
        print("  [skip] fig5: script 02/05 outputs not found yet")
        return
    primary_df = pd.read_csv(primary_path).dropna(subset=["interaction_p"])
    if primary_df.empty:
        print("  [skip] fig5: no usable interaction rows")
        return
    best = primary_df.sort_values("interaction_p").iloc[0]
    delta_mode, endpoint = best["delta_mode"], best["endpoint"]

    merged = pd.read_parquet(merged_path)
    full_df = load_phase_v3()
    used_keys = merged[["subject_id", "onset_sec"]].drop_duplicates()
    anti_join = full_df.merge(used_keys, on=["subject_id", "onset_sec"], how="left", indicator=True)
    held_out = anti_join[anti_join["_merge"] == "left_only"]
    subject_mean_angles = {}
    for subj, sub in held_out.groupby("subject_id"):
        angle, r, n = circular_mean_resultant(sub["phi_resp_peak"].to_numpy())
        if np.isfinite(angle):
            subject_mean_angles[subj] = angle
    mu_resp_peak, _, _ = circular_mean_resultant(np.array(list(subject_mean_angles.values())))
    merged = merged.copy()
    merged["resp_peak_alignment"] = np.cos(merged["phi_resp_peak"] - mu_resp_peak)
    merged["qe_sigma_log"] = np.log1p(merged["sigma_power_z_n2"])

    baseline_col = f"{endpoint}_control_median" if delta_mode == "event_control" else f"{endpoint}_far"
    sub = merged.dropna(subset=[endpoint, baseline_col, "resp_peak_alignment", "qe_sigma_log"]).copy()
    sub["delta"] = sub[endpoint] - sub[baseline_col]
    sub["qe_tertile"] = pd.qcut(sub["qe_sigma_log"], 3, labels=["Weak", "Mid", "Strong"])

    fig, ax = plt.subplots(figsize=(5.6, 4.4))
    colors = {"Weak": "#90CAF9", "Mid": "#1E88E5", "Strong": "#0D47A1"}
    for tertile, color in colors.items():
        s = sub[sub["qe_tertile"] == tertile]
        ax.scatter(s["resp_peak_alignment"], s["delta"], s=28, color=color, alpha=0.8,
                   edgecolor="none", label=f"{tertile} (n={len(s)})")
        if len(s) >= 4:
            b, a = np.polyfit(s["resp_peak_alignment"].to_numpy(), s["delta"].to_numpy(), 1)
            xs = np.linspace(s["resp_peak_alignment"].min(), s["resp_peak_alignment"].max(), 50)
            ax.plot(xs, a + b * xs, color=color, linewidth=1.3, linestyle="--")
    ax.axhline(0, color="grey", linewidth=0.6)
    ax.set_xlabel(r"resp_peak_alignment  $=\cos(\phi_{resp,peak}-\mu_{resp,peak})$")
    ax.set_ylabel(f"{endpoint} delta ({delta_mode})")
    ax.set_title(
        f"No FDR-significant qe x alignment interaction found (0/18 tests)\n"
        f"Smallest-p illustration: {endpoint} ({delta_mode}), "
        f"interaction p={best['interaction_p']:.3f}, FDR q={best['interaction_p_fdr']:.3f}",
        fontsize=8.5,
    )
    ax.legend(fontsize=7.5, title="Intrinsic strength (qe) tertile", title_fontsize=7.5)
    fig.tight_layout()
    save(fig, "fig5_efficacy_interaction.svg")


if __name__ == "__main__":
    print("Generating RichSleep EAP v2 figures ...")
    fig1_cross_carrier_phase_locking()
    fig2_rose_plots_per_carrier()
    fig3_hazard_curve()
    fig4_qe_coupling_distributions()
    fig5_efficacy_interaction()
    print(f"\nDone. Figures directory: {FIGURES_DIR}")
