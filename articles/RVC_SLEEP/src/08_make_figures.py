"""
08_make_figures.py — Figure generation for the RVC_SLEEP article, mirroring
the sister article's "articles/Neural flow geometry differentiates gambling
and cognitive control/src/08_make_figures.py" in structure and style.

Produces five SVG figures from the result CSVs written by scripts 00/02-05
(reads the most recent `results/rvc_sleep_<date>/<phase>/` outputs found):

  fig1_pass_a1_specificity.svg     — event-vs-control geometry delta per
                                      endpoint x dataset (Pass A1-original,
                                      pre-amendment sensitivity)
  fig1r_pass_a1r_specificity.svg   — corrected primary, subject-weighted
                                      event-vs-control delta (Pass A1r,
                                      sciencelead/001.md)
  fig2_peri_spindle_profile.svg    — peri-event bin contrasts vs pre_far,
                                      per endpoint x dataset (Pass A2)
  fig2r_pass_a2r_profile.svg       — subject-balanced event-vs-pre_far
                                      companion check (Pass A2r,
                                      sciencelead/001.md)
  fig3_surface_sensitivity.svg     — primary vs anchor-augmented surface
                                      comparison per endpoint x dataset (Pass B)
  fig4_eap_moderation.svg          — anchor-coefficient forest plot per
                                      endpoint x dataset x model (Pass C)
  fig5_qc_coverage.svg             — condition x bin_label row coverage per
                                      dataset (00_sanity_check)

Usage:
    python "articles/RVC_SLEEP/src/08_make_figures.py"

Each fig*() function is defensive: if the underlying results CSV does not
exist yet (pass not run), it prints a message and skips that figure rather
than failing the whole script.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from rvc_sleep_support import DATASETS, FIGURES_DIR, RESULTS_DIR

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

DATASET_COLORS = {"ANPHY": "#1E88E5", "ds005555": "#E53935"}


def save(fig, name: str) -> None:
    out = FIGURES_DIR / name
    fig.savefig(out, format="svg", bbox_inches="tight", dpi=150)
    print(f"  Saved {out.relative_to(FIGURES_DIR.parents[0])}")
    plt.close(fig)


def find_latest(glob_pattern: str) -> Path | None:
    candidates = sorted(RESULTS_DIR.glob(glob_pattern))
    return candidates[-1] if candidates else None


# ──────────────────────────────────────────────────────────────────────────────
# Fig 1: Pass A1 specificity (event vs matched-control delta)
# ──────────────────────────────────────────────────────────────────────────────
def fig1_pass_a1_specificity() -> None:
    """A1-primary result: OLS intercept (cluster-robust SE by subject) for the
    event-vs-matched-control delta, with FDR-significance markers. This is the
    pre-registered decision-rule estimate (see 02_pass_a1_rvc_specificity.py
    fallback-hierarchy docstring), not the naive unweighted mean."""
    path = find_latest("rvc_sleep_*/02_pass_a1_rvc_specificity/pass_a1_rvc_specificity.csv")
    if path is None:
        print("  [skip] fig1: 02_pass_a1_rvc_specificity.csv not found yet")
        return
    df = pd.read_csv(path)
    if "ols_intercept_coef" not in df.columns:
        print("  [skip] fig1: pass_a1_rvc_specificity.csv is from an older script version (no ols_intercept_coef)")
        return
    df = df.dropna(subset=["ols_intercept_coef"])
    if df.empty:
        print("  [skip] fig1: no usable rows")
        return

    endpoints = sorted(df["endpoint"].unique())
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    width = 0.35
    x = np.arange(len(endpoints))
    for i, dataset in enumerate(DATASETS):
        sub = df[df["dataset"] == dataset].set_index("endpoint").reindex(endpoints)
        bars = ax.bar(x + (i - 0.5) * width, sub["ols_intercept_coef"], width,
                       yerr=sub["ols_intercept_se"], capsize=2,
                       label=dataset, color=DATASET_COLORS.get(dataset), alpha=0.8)
        for xi, (coef, q) in enumerate(zip(sub["ols_intercept_coef"], sub.get("ols_intercept_p_fdr", pd.Series(dtype=float)))):
            if pd.notna(coef) and pd.notna(q) and q < 0.05:
                ax.annotate("*", (x[xi] + (i - 0.5) * width, coef), ha="center",
                            va="bottom" if coef >= 0 else "top", fontsize=11, fontweight="bold")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(endpoints, rotation=45, ha="right")
    ax.set_ylabel("Event − matched-control\n(OLS intercept, cluster-robust SE)")
    ax.set_title("Pass A1-original (pre-amendment sensitivity, event-weighted)\n(* = BH-FDR q<0.05, 18-test family)")
    ax.legend()
    fig.tight_layout()
    save(fig, "fig1_pass_a1_specificity.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 1r: Pass A1r — corrected primary, subject-weighted specificity
# (sciencelead/001.md protocol amendment, 2026-07-03)
# ──────────────────────────────────────────────────────────────────────────────
def fig1r_pass_a1r_specificity() -> None:
    path = find_latest("rvc_sleep_*/02c_pass_a1r_subject_weighted_specificity/pass_a1r_subject_weighted_specificity.csv")
    if path is None:
        print("  [skip] fig1r: pass_a1r_subject_weighted_specificity.csv not found yet")
        return
    df = pd.read_csv(path).dropna(subset=["subject_mean_delta"])
    if df.empty:
        print("  [skip] fig1r: no usable rows")
        return

    endpoints = sorted(df["endpoint"].unique())
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    width = 0.35
    x = np.arange(len(endpoints))
    for i, dataset in enumerate(DATASETS):
        sub = df[df["dataset"] == dataset].set_index("endpoint").reindex(endpoints)
        yerr = np.vstack([sub["subject_mean_delta"] - sub["ci95_lo"], sub["ci95_hi"] - sub["subject_mean_delta"]])
        ax.bar(x + (i - 0.5) * width, sub["subject_mean_delta"], width, yerr=yerr, capsize=2,
               label=dataset, color=DATASET_COLORS.get(dataset), alpha=0.8)
        for xi, (val, q) in enumerate(zip(sub["subject_mean_delta"], sub.get("perm_p_fdr", pd.Series(dtype=float)))):
            if pd.notna(val) and pd.notna(q) and q < 0.05:
                ax.annotate("*", (x[xi] + (i - 0.5) * width, val), ha="center",
                            va="bottom" if val >= 0 else "top", fontsize=11, fontweight="bold")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(endpoints, rotation=45, ha="right")
    ax.set_ylabel("Event − matched-control\n(subject mean delta, 95% CI)")
    ax.set_title("Pass A1r: corrected primary, subject-weighted specificity\n(* = BH-FDR q<0.05 on sign-flip permutation, 18-test family)")
    ax.legend()
    fig.tight_layout()
    save(fig, "fig1r_pass_a1r_specificity.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 2: Pass A2 peri-spindle profile
# ──────────────────────────────────────────────────────────────────────────────
def fig2_peri_spindle_profile() -> None:
    path = find_latest("rvc_sleep_*/03_pass_a2_peri_spindle_profile/pass_a2_peri_spindle_profile.csv")
    if path is None:
        print("  [skip] fig2: 03_pass_a2_peri_spindle_profile.csv not found yet")
        return
    raw = pd.read_csv(path)
    df = raw.dropna(subset=["coef"]) if "coef" in raw.columns else pd.DataFrame()
    if df.empty:
        print("  [skip] fig2: no usable rows")
        return

    fig, axes = plt.subplots(1, len(DATASETS), figsize=(7.2, 3.2), sharey=True)
    if len(DATASETS) == 1:
        axes = [axes]
    for ax, dataset in zip(axes, DATASETS):
        sub = df[df["dataset"] == dataset]
        for endpoint, grp in sub.groupby("endpoint"):
            ax.plot(grp["contrast"], grp["coef"], marker="o", label=endpoint, alpha=0.7)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title(dataset)
        ax.tick_params(axis="x", rotation=45)
    axes[0].set_ylabel("Coefficient vs. pre_far")
    axes[-1].legend(fontsize=6, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.suptitle("Pass A2: peri-spindle profile")
    fig.tight_layout()
    save(fig, "fig2_peri_spindle_profile.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 2r: Pass A2r — subject-balanced companion, event-vs-pre_far headline
# (sciencelead/001.md protocol amendment, 2026-07-03)
# ──────────────────────────────────────────────────────────────────────────────
def fig2r_pass_a2r_profile() -> None:
    path = find_latest("rvc_sleep_*/03b_pass_a2r_subject_balanced_profile/pass_a2r_subject_balanced_profile.csv")
    if path is None:
        print("  [skip] fig2r: pass_a2r_subject_balanced_profile.csv not found yet")
        return
    df = pd.read_csv(path).dropna(subset=["subject_mean_delta"])
    if df.empty:
        print("  [skip] fig2r: no usable rows")
        return

    endpoints = sorted(df["endpoint"].unique())
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    width = 0.35
    x = np.arange(len(endpoints))
    for i, dataset in enumerate(DATASETS):
        sub = df[df["dataset"] == dataset].set_index("endpoint").reindex(endpoints)
        yerr = np.vstack([sub["subject_mean_delta"] - sub["ci95_lo"], sub["ci95_hi"] - sub["subject_mean_delta"]])
        ax.bar(x + (i - 0.5) * width, sub["subject_mean_delta"], width, yerr=yerr, capsize=2,
               label=dataset, color=DATASET_COLORS.get(dataset), alpha=0.8)
        for xi, (val, q) in enumerate(zip(sub["subject_mean_delta"], sub.get("perm_p_fdr", pd.Series(dtype=float)))):
            if pd.notna(val) and pd.notna(q) and q < 0.05:
                ax.annotate("*", (x[xi] + (i - 0.5) * width, val), ha="center",
                            va="bottom" if val >= 0 else "top", fontsize=11, fontweight="bold")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(endpoints, rotation=45, ha="right")
    ax.set_ylabel("Event − pre_far\n(subject mean delta, 95% CI)")
    ax.set_title("Pass A2r: subject-balanced timing check\n(* = BH-FDR q<0.05 on sign-flip permutation, 18-test family)")
    ax.legend()
    fig.tight_layout()
    save(fig, "fig2r_pass_a2r_profile.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 3: Pass B surface sensitivity
# ──────────────────────────────────────────────────────────────────────────────
def fig3_surface_sensitivity() -> None:
    """Pass B, sensitivity-only (sciencelead/003.md): does the anchor-
    augmented surface change the subject-weighted A1r/A2r deltas? Faceted by
    delta mode; per the guardrail, a nonzero surface_delta means the surface
    is sensitive to injected body signals, NOT that EAP moderation exists."""
    path = find_latest("rvc_sleep_*/04_pass_b_surface_sensitivity/pass_b_surface_sensitivity.csv")
    if path is None:
        print("  [skip] fig3: 04_pass_b_surface_sensitivity.csv not found yet")
        return
    df = pd.read_csv(path).dropna(subset=["surface_delta"])
    if df.empty:
        print("  [skip] fig3: no usable rows")
        return

    delta_modes = sorted(df["delta_mode"].unique())
    endpoints = sorted(df["endpoint"].unique())
    fig, axes = plt.subplots(1, len(delta_modes), figsize=(6.5 * len(delta_modes), 3.2), sharey=True)
    if len(delta_modes) == 1:
        axes = [axes]
    x = np.arange(len(endpoints))
    width = 0.35
    for ax, mode in zip(axes, delta_modes):
        sub_mode = df[df["delta_mode"] == mode]
        for i, dataset in enumerate(DATASETS):
            sub = sub_mode[sub_mode["dataset"] == dataset].set_index("endpoint").reindex(endpoints)
            ax.bar(x + (i - 0.5) * width, sub["surface_delta"], width,
                   label=dataset, color=DATASET_COLORS.get(dataset), alpha=0.8)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(endpoints, rotation=45, ha="right")
        ax.set_title(mode)
    axes[0].set_ylabel("Anchor-aug − primary\n(paired subject-mean delta)")
    axes[-1].legend()
    fig.suptitle("Pass B: surface sensitivity (does NOT test EAP moderation)")
    fig.tight_layout()
    save(fig, "fig3_surface_sensitivity.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 4: Pass C EAP moderation (forest plot)
# ──────────────────────────────────────────────────────────────────────────────
def fig4_eap_moderation() -> None:
    """Pass C forest plot, faceted by delta mode (sciencelead/002.md guardrail
    #1: event-matched_control vs. event-pre_far are run and reported
    separately, since the A1/A2 decomposition showed they ask different
    questions)."""
    path = find_latest("rvc_sleep_*/05_pass_c_eap_moderation/pass_c_eap_moderation.csv")
    if path is None:
        print("  [skip] fig4: 05_pass_c_eap_moderation.csv not found yet")
        return
    raw = pd.read_csv(path)
    df = raw.dropna(subset=["anchor_coef"]) if "anchor_coef" in raw.columns else pd.DataFrame()
    if df.empty:
        print("  [skip] fig4: no usable rows")
        return

    delta_modes = sorted(df["delta_mode"].unique()) if "delta_mode" in df.columns else [None]
    fig, axes = plt.subplots(1, len(delta_modes), figsize=(6.0 * len(delta_modes), max(3.0, 0.22 * len(df) / max(len(delta_modes), 1))), sharex=True)
    if len(delta_modes) == 1:
        axes = [axes]
    for ax, mode in zip(axes, delta_modes):
        sub = df[df["delta_mode"] == mode] if mode is not None else df
        sub = sub.assign(label=sub["dataset"] + " · " + sub["model"] + " · " + sub["endpoint"])
        sub = sub.sort_values("anchor_coef")
        colors = ["#1E88E5" if q < 0.05 else "#999999" for q in sub.get("anchor_p_fdr", pd.Series([np.nan] * len(sub)))]
        ax.errorbar(sub["anchor_coef"], np.arange(len(sub)), xerr=sub["anchor_se"], fmt="o", ecolor="#cccccc", color="#333333")
        for yi, c in enumerate(colors):
            ax.plot(sub["anchor_coef"].iloc[yi], yi, "o", color=c)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_yticks(np.arange(len(sub)))
        ax.set_yticklabels(sub["label"], fontsize=6)
        ax.set_xlabel("Anchor coefficient")
        ax.set_title(mode or "")
    fig.suptitle("Pass C: EAP x RVC moderation (blue = BH-FDR q<0.05)")
    fig.tight_layout()
    save(fig, "fig4_eap_moderation.svg")


# ──────────────────────────────────────────────────────────────────────────────
# Fig 5: QC coverage (condition x bin_label)
# ──────────────────────────────────────────────────────────────────────────────
def fig5_qc_coverage() -> None:
    path = find_latest("rvc_sleep_*/00_sanity_check/event_locked_coverage.csv")
    if path is None:
        print("  [skip] fig5: event_locked_coverage.csv not found yet")
        return
    df = pd.read_csv(path)
    if df.empty:
        print("  [skip] fig5: no usable rows")
        return

    pivot = df.pivot_table(index=["dataset_id", "bin_label"], columns="condition", values="n_rows", fill_value=0)
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    pivot.plot(kind="bar", stacked=False, ax=ax)
    ax.set_ylabel("N rows")
    ax.set_title("QC: condition x bin_label coverage")
    ax.tick_params(axis="x", rotation=60)
    fig.tight_layout()
    save(fig, "fig5_qc_coverage.svg")


if __name__ == "__main__":
    print("Generating RVC_SLEEP figures ...")
    fig1_pass_a1_specificity()
    fig1r_pass_a1r_specificity()
    fig2_peri_spindle_profile()
    fig2r_pass_a2r_profile()
    fig3_surface_sensitivity()
    fig4_eap_moderation()
    fig5_qc_coverage()
    print(f"\nDone. Figures directory: {FIGURES_DIR}")
