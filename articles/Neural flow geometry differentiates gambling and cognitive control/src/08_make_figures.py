"""
08_make_figures.py — Figure generation for "Neural flow geometry differentiates
gambling and cognitive control despite matched sympathetic arousal" (ds004511).

Fills the figure-coverage gap identified when drafting the main article and
supplements S1-S5 (no figures had yet been produced for this article, unlike
the sister articles `embodied_anchoring` and `embodied_anchoring_follow_up`).

Produces six SVG figures from the result CSVs already on disk
(results/ds004511_20260701/*):

  fig1_mnps_vs_mnj_dissociation.svg  — R2 vs R3: null MNPS / strong MNJ
  fig2_mnj_effect_sizes.svg          — Cohen's d heatmap, 6 metrics x 3 pairs
  fig3_bootstrap_robustness.svg      — forest plot, bootstrap 95% CI (R4)
  fig4_eda_dissociation.svg          — tonic SCL by task, GG=CC vs Rest (R5)
  fig5_eap_resp_coupling.svg         — resp_anchor x m (CC) and x frobenius (GG)
  fig6_qc_coverage.svg               — QC pass-rate by modality x task (S3)

Usage:
    python "articles/Neural flow geometry differentiates gambling and cognitive control/src/08_make_figures.py"
"""
import pathlib
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

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

REPO = pathlib.Path(__file__).resolve().parents[3]
ARTICLE = REPO / "articles" / "Neural flow geometry differentiates gambling and cognitive control"
RES = ARTICLE / "results" / "ds004511_20260701"
FIGDIR = ARTICLE / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

TASK_ORDER = ["gambling", "cognitive_control", "rest"]
TASK_LABELS = ["Gambling\n(GG)", "Cognitive\nControl (CC)", "Rest"]
TASK_COLORS = {"gambling": "#E53935", "cognitive_control": "#1E88E5", "rest": "#43A047"}


def save(fig, name):
    out = FIGDIR / name
    fig.savefig(out, format="svg", bbox_inches="tight", dpi=150)
    print(f"  Saved {out.relative_to(REPO)}")
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────────────────
# Fig 1: MNPS null vs MNJ dissociation
# ──────────────────────────────────────────────────────────────────────────────
def fig1_mnps_vs_mnj():
    medians = pd.read_csv(RES / "01_cross_task_mnps" / "mnps_cross_task_global.csv")
    mnj = pd.read_csv(RES / "03_mnj_reachability" / "subject_mnj_summary.csv")
    mnj_pivot = mnj.pivot_table(index="subject_id", columns="task_label",
                                 values="frobenius_norm_median")

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))

    ax = axes[0]
    data = [medians[f"m_median_{t}"].dropna().values for t in TASK_ORDER]
    bp = ax.boxplot(data, positions=range(3), widths=0.55, patch_artist=True,
                     showfliers=False)
    for patch, t in zip(bp["boxes"], TASK_ORDER):
        patch.set_facecolor(TASK_COLORS[t]); patch.set_alpha(0.55)
    for i, d in enumerate(data):
        jitter = np.random.default_rng(0).normal(0, 0.05, len(d))
        ax.scatter(np.full(len(d), i) + jitter, d, s=6, color="black", alpha=0.35, zorder=3)
    ax.set_xticks(range(3)); ax.set_xticklabels(TASK_LABELS)
    ax.set_ylabel("MNPS mobility $m$ (session median)")
    ax.set_title("R2: global MNPS — null\n(Friedman $p=0.64$)")
    ax.axhline(0, color="grey", lw=0.6, ls=":")

    ax = axes[1]
    data = [mnj_pivot[t].dropna().values for t in TASK_ORDER]
    bp = ax.boxplot(data, positions=range(3), widths=0.55, patch_artist=True,
                     showfliers=False)
    for patch, t in zip(bp["boxes"], TASK_ORDER):
        patch.set_facecolor(TASK_COLORS[t]); patch.set_alpha(0.55)
    for i, d in enumerate(data):
        jitter = np.random.default_rng(1).normal(0, 0.05, len(d))
        ax.scatter(np.full(len(d), i) + jitter, d, s=6, color="black", alpha=0.35, zorder=3)
    ax.set_xticks(range(3)); ax.set_xticklabels(TASK_LABELS)
    ax.set_ylabel("MNJ Frobenius norm $||J||_F$ (session median)")
    ax.set_title("R3: MNJ flow geometry — strong\n(GG vs CC $d=1.58$, $p<10^{-11}$)")
    ax.plot([0, 1], [0.205, 0.205], color="black", lw=1)
    ax.text(0.5, 0.208, "***", ha="center", fontsize=10)

    fig.suptitle("Global manifold position is null while local flow geometry is strongly task-selective",
                 fontsize=9, y=1.03)
    save(fig, "fig1_mnps_vs_mnj_dissociation.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 2: MNJ effect-size heatmap
# ──────────────────────────────────────────────────────────────────────────────
def fig2_mnj_effect_sizes():
    df = pd.read_csv(RES / "03_mnj_reachability" / "mnj_cross_task_wilcoxon.csv")
    metrics = ["frobenius_norm", "spectral_radius", "rotation_norm",
               "rotational_power", "aci", "mdr"]
    pairs = [("gambling", "cognitive_control"), ("gambling", "rest"),
             ("cognitive_control", "rest")]
    pair_labels = ["GG vs CC", "GG vs Rest", "CC vs Rest"]

    mat = np.full((len(metrics), len(pairs)), np.nan)
    sig = np.zeros((len(metrics), len(pairs)), dtype=bool)
    for i, m in enumerate(metrics):
        for j, (t1, t2) in enumerate(pairs):
            row = df[(df["mnj_metric"] == m) & (df["task1"] == t1) & (df["task2"] == t2)]
            if len(row):
                mat[i, j] = row["cohen_d"].values[0]
                sig[i, j] = bool(row["sig_fdr05"].values[0])

    fig, ax = plt.subplots(figsize=(4.6, 4.0))
    vmax = np.nanmax(np.abs(mat))
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(pairs))); ax.set_xticklabels(pair_labels)
    ax.set_yticks(range(len(metrics)))
    ax.set_yticklabels(["Frobenius norm", "Spectral radius", "Rotation norm",
                         "Rotational power", "ACI", "MDR"])
    for i in range(len(metrics)):
        for j in range(len(pairs)):
            if np.isfinite(mat[i, j]):
                marker = "*" if sig[i, j] else ""
                ax.text(j, i, f"{mat[i, j]:.2f}{marker}", ha="center", va="center",
                         fontsize=8, color="black")
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Cohen's $d$")
    ax.set_title("MNJ cross-task effect sizes\n(* = survives BH-FDR 5%)")
    save(fig, "fig2_mnj_effect_sizes.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 3: Bootstrap robustness forest plot
# ──────────────────────────────────────────────────────────────────────────────
def fig3_bootstrap():
    boot = pd.read_csv(RES / "05_mnj_confound_audit" / "mnj_bootstrap.csv")
    looso = pd.read_csv(RES / "05_mnj_confound_audit" / "mnj_looso.csv")
    order = ["frobenius_norm", "spectral_radius", "rotational_power", "aci"]
    labels = ["Frobenius norm", "Spectral radius", "Rotational power", "ACI"]

    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    for i, key in enumerate(order):
        row = boot[boot["mnj_metric"] == key].iloc[0]
        lo_row = looso[looso["mnj_metric"] == key]
        ax.plot([row["ci_lo"], row["ci_hi"]], [i, i], color="#1E88E5", lw=2, zorder=2)
        ax.scatter([row["cohen_d"]], [i], color="#0D47A1", s=40, zorder=3)
        if len(lo_row):
            lo = lo_row.iloc[0]
            ax.scatter([lo["loo_min_d"], lo["loo_max_d"]], [i, i], color="grey",
                       marker="|", s=80, zorder=1)
    ax.axvline(0, color="black", lw=0.8, ls=":")
    ax.set_yticks(range(len(order))); ax.set_yticklabels(labels)
    ax.set_xlabel("Cohen's $d$ (GG vs CC)")
    ax.set_title("Bootstrap 95% CI (blue) and LOOSO range (grey ticks), $N=42$")
    ax.invert_yaxis()
    save(fig, "fig3_bootstrap_robustness.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 4: EDA dissociation
# ──────────────────────────────────────────────────────────────────────────────
def fig4_eda_dissociation():
    eda = pd.read_parquet(RES / "06_eda_extraction" / "eda_features.parquet")
    eda_ok = eda[eda["qc_ok_eda"] == 1]
    sub_eda = eda_ok.groupby(["subject_id", "task_label"])["eda_tonic_scl"].median().unstack()

    mnj = pd.read_csv(RES / "03_mnj_reachability" / "subject_mnj_summary.csv")
    mnj_pivot = mnj.pivot_table(index="subject_id", columns="task_label",
                                 values="frobenius_norm_median")

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))

    ax = axes[0]
    data = [sub_eda[t].dropna().values for t in TASK_ORDER]
    bp = ax.boxplot(data, positions=range(3), widths=0.55, patch_artist=True, showfliers=False)
    for patch, t in zip(bp["boxes"], TASK_ORDER):
        patch.set_facecolor(TASK_COLORS[t]); patch.set_alpha(0.55)
    for i, d in enumerate(data):
        jitter = np.random.default_rng(2).normal(0, 0.05, len(d))
        ax.scatter(np.full(len(d), i) + jitter, d, s=6, color="black", alpha=0.3, zorder=3)
    ax.set_xticks(range(3)); ax.set_xticklabels(TASK_LABELS)
    ax.set_ylabel("Tonic EDA (SCL, µS)")
    ax.set_title("Peripheral arousal:\nGG $\\approx$ CC $>$ Rest ($d_{GG-CC}=-0.08$, ns)")

    ax = axes[1]
    common = sub_eda[["gambling", "cognitive_control"]].dropna().index
    common = common.intersection(mnj_pivot.index)
    eda_diff = sub_eda.loc[common, "gambling"] - sub_eda.loc[common, "cognitive_control"]
    frob_diff = mnj_pivot.loc[common, "gambling"] - mnj_pivot.loc[common, "cognitive_control"]
    ax.scatter(eda_diff, frob_diff, s=18, color="#6A1B9A", alpha=0.7)
    ax.axhline(0, color="grey", lw=0.6, ls=":")
    ax.axvline(0, color="grey", lw=0.6, ls=":")
    ax.set_xlabel("EDA tonic SCL difference (GG$-$CC, µS)")
    ax.set_ylabel("MNJ Frobenius difference (GG$-$CC)")
    ax.set_title("No confound relationship\n($r_s=-0.10$, $p=0.53$, $N=42$)")

    fig.suptitle("EDA-MNJ dissociation: matched peripheral arousal, divergent neural flow geometry",
                 fontsize=9, y=1.03)
    save(fig, "fig4_eda_dissociation.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 5: EAP respiratory-anchoring coupling (secondary/exploratory)
# ──────────────────────────────────────────────────────────────────────────────
def fig5_eap_coupling():
    feat_medians = pd.read_csv(RES / "00_sanity_check" / "subject_task_physio_medians.csv")
    mnps = pd.read_csv(RES / "01_cross_task_mnps" / "mnps_cross_task_global.csv")
    mnj = pd.read_csv(RES / "03_mnj_reachability" / "subject_mnj_summary.csv")

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))

    # CC: resp_anchor_index vs m
    ax = axes[0]
    resp_cc = feat_medians.set_index("subject_id")["cognitive_control"] if False else None
    resp = pd.read_csv(RES / "00_sanity_check" / "resp_qc_by_subject_task.csv")  # placeholder unused
    # Build from subject_task_physio_medians is not resp_anchor; use resp_qc source instead:
    physio = pd.read_csv(RES / "02_eap_physio_coupling" / "coupling_per_task.csv")
    # Use mnj summary which already carries resp_anchor_index_median per subject/task
    resp_m = mnj[mnj["task_label"] == "cognitive_control"].set_index("subject_id")
    mnps_m = mnps.set_index("subject_id")["m_median_cognitive_control"]
    common = resp_m.index.intersection(mnps_m.dropna().index)
    x = resp_m.loc[common, "resp_anchor_index_median"]
    y = mnps_m.loc[common]
    ax.scatter(x, y, s=18, color="#1E88E5", alpha=0.7)
    if len(x) > 2:
        b, a = np.polyfit(x, y, 1)
        xs = np.linspace(x.min(), x.max(), 50)
        ax.plot(xs, a + b * xs, color="#0D47A1", lw=1.5)
    ax.set_xlabel("Respiratory anchor index (session median)")
    ax.set_ylabel("MNPS mobility $m$")
    ax.set_title("Cognitive control\npartial $r=-0.41$, $p=0.006$ (ctrl. HRV)")

    # GG: resp_anchor_index vs frobenius
    ax = axes[1]
    resp_g = mnj[mnj["task_label"] == "gambling"].set_index("subject_id")
    xg = resp_g["resp_anchor_index_median"]
    yg = resp_g["frobenius_norm_median"]
    common_g = xg.dropna().index.intersection(yg.dropna().index)
    ax.scatter(xg.loc[common_g], yg.loc[common_g], s=18, color="#E53935", alpha=0.7)
    if len(common_g) > 2:
        b, a = np.polyfit(xg.loc[common_g], yg.loc[common_g], 1)
        xs = np.linspace(xg.loc[common_g].min(), xg.loc[common_g].max(), 50)
        ax.plot(xs, a + b * xs, color="#B71C1C", lw=1.5)
    ax.set_xlabel("Respiratory anchor index (session median)")
    ax.set_ylabel("MNJ Frobenius norm")
    ax.set_title("Gambling\n$r=-0.23$, LOOSO sign-consistent (42/42)")

    fig.suptitle("Secondary EAP-compatible respiratory-anchoring associations (exploratory, $N\\approx42$)",
                 fontsize=9, y=1.03)
    save(fig, "fig5_eap_resp_coupling.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 6: QC coverage
# ──────────────────────────────────────────────────────────────────────────────
def fig6_qc_coverage():
    resp_qc = pd.read_csv(RES / "00_sanity_check" / "resp_qc_by_subject_task.csv")
    eda_qc = pd.read_csv(RES / "06_eda_extraction" / "eda_qc_summary.csv")

    resp_means = resp_qc[["gambling", "cognitive_control", "rest"]].mean()
    eda_means = eda_qc.groupby("task_label")["qc_ok_frac"].mean().reindex(TASK_ORDER)

    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    width = 0.35
    x = np.arange(3)
    ax.bar(x - width / 2, resp_means.reindex(TASK_ORDER).values * 100, width,
           label="Respiration QC", color="#43A047")
    ax.bar(x + width / 2, eda_means.values * 100, width,
           label="EDA QC", color="#8E24AA")
    ax.set_xticks(x); ax.set_xticklabels(TASK_LABELS)
    ax.set_ylabel("% epochs QC-OK")
    ax.set_ylim(0, 105)
    ax.legend(loc="lower right")
    ax.set_title("Physiological data quality by task and modality")
    save(fig, "fig6_qc_coverage.svg")


if __name__ == "__main__":
    print("Generating figures for ds004511 GG/CC/Rest article ...")
    fig1_mnps_vs_mnj()
    fig2_mnj_effect_sizes()
    fig3_bootstrap()
    fig4_eda_dissociation()
    fig5_eap_coupling()
    fig6_qc_coverage()
    print(f"\nAll figures saved to {FIGDIR.relative_to(REPO)}")
