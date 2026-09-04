"""
02b_pass_a1_heterogeneity_audit.py — Estimand/influence audit for Pass A1.

Context (2026-07-02): the Pass A1 primary test (OLS, cluster-robust SE by
subject) is FDR-significant for 6/9 endpoints in ANPHY but 0/9 in
ds005555/BOAS, even though BOAS is overwhelmingly significant on the
subject-level t-test / Wilcoxon / sign-flip permutation sensitivities (which
weight every subject equally regardless of event count). ANPHY has ~40
events/subject (range 3-66); BOAS has ~5-6 events/subject (range 1-18,
median 5) — a much sparser, more uneven design. This script audits whether
the BOAS discrepancy is driven by (a) uneven event counts giving a handful of
subjects outsized leverage in the event-weighted OLS, or (b) genuine
subject-level effect heterogeneity that cluster-robust SE is correctly
picking up.

This is a DIAGNOSTIC / INFLUENCE AUDIT ONLY. It does not touch or overwrite
the frozen Pass A1 primary table (02_pass_a1_rvc_specificity.py /
pass_a1_rvc_specificity.csv). Nothing here changes the pre-registered
decision rule; it exists to inform whether that rule's null result in BOAS
should be trusted, and whether Pass B/C should proceed on ANPHY alone,
both datasets, or wait for a design fix.

Produces (per dataset, all 9 frozen endpoints; BOAS is the primary target,
ANPHY is included throughout as a reference comparison):
  1. event_count_per_subject.csv       — event-count distribution per subject
  2. subject_mean_deltas.csv           — per-subject mean delta, wide by endpoint
  3. event_count_delta_correlation.csv — Spearman/Pearson r(n_events, subject delta)
  4. loso_coefficients.csv             — leave-one-subject-out OLS intercept shifts
  5. top_event_subject_exclusion.csv   — OLS refit after dropping top event-count subjects
  6. event_balanced_resampling.csv     — OLS intercept distribution under equal-events-per-subject subsampling
  7. subject_bootstrap_ci.csv          — cluster (subject-level) bootstrap CIs for the OLS intercept
                                          AND for the equal-weight grand-mean-of-subject-means statistic

Run: python src/02b_pass_a1_heterogeneity_audit.py
Requires: 01_build_event_level_tables.py to have been run first.
"""
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from rvc_sleep_support import (
    DATASETS,
    FIGURES_DIR,
    GEOMETRY_COLS,
    RESULTS_DIR,
    available_covariates,
    fit_ols_cluster,
    make_results_subdir,
)

matplotlib.rcParams.update({
    "font.family": "sans-serif", "font.size": 9, "axes.titlesize": 10,
    "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "legend.fontsize": 8, "svg.fonttype": "none",
})
AUDIT_FIGURES_DIR = FIGURES_DIR / "audit"
AUDIT_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
HIGHLIGHT_ENDPOINTS = ["d_n", "e_s", "d_s", "m"]  # RVC-relevant + the one showing a sign conflict

OUT = make_results_subdir("02b_pass_a1_heterogeneity_audit")

CANDIDATE_COVARIATES = [
    "event_duration_sec", "frequency_hz", "window_center_sec",
    "match_distance", "anchor_quality",
]

RNG_SEED = 42
N_BOOT = 2000
N_RESAMPLE = 500
TOP_EXCLUSION_LEVELS = {  # dataset -> list of "top-N subjects by event count to drop"
    "ANPHY": [1, 3, 5],
    "ds005555": [1, 3, 5, 10, 20],
}
BALANCE_CAPS = {  # dataset -> list of per-subject event caps to test
    "ANPHY": [10, 20, 29],
    "ds005555": [2, 3, 5],
}


def find_latest_event_level_primary() -> Path:
    candidates = sorted(RESULTS_DIR.glob("rvc_sleep_*/01_build_event_level_tables/event_level_primary.parquet"))
    if not candidates:
        raise FileNotFoundError("No event_level_primary.parquet found. Run 01_build_event_level_tables.py first.")
    return candidates[-1]


def build_design(sub: pd.DataFrame, covariates: list) -> tuple:
    X = np.column_stack([np.ones(len(sub))] + [sub[c].to_numpy(dtype=float) for c in covariates])
    y = sub["y_event_control"].to_numpy(dtype=float)
    return X, y


def ols_intercept_fast(X: np.ndarray, y: np.ndarray) -> float:
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return float(coef[0])


print(f"Loading {find_latest_event_level_primary()} ...")
event_level = pd.read_parquet(find_latest_event_level_primary())
event_rows = event_level[event_level["bin_label"] == "event"].copy()

# ── 1. Event-count distribution per subject ────────────────────────────────
count_rows = []
for dataset in DATASETS:
    sub_ds = event_rows[event_rows["dataset_id"] == dataset]
    counts = sub_ds.groupby("subject_id").size().rename("n_events").reset_index()
    counts.insert(0, "dataset", dataset)
    count_rows.append(counts)
event_count_per_subject = pd.concat(count_rows, ignore_index=True)
event_count_per_subject.to_csv(OUT / "event_count_per_subject.csv", index=False)

print("\n--- 1. Event-count distribution per subject ---")
for dataset in DATASETS:
    c = event_count_per_subject.loc[event_count_per_subject["dataset"] == dataset, "n_events"]
    print(f"  [{dataset}] n_subjects={len(c)} mean={c.mean():.1f} median={c.median():.0f} "
          f"min={c.min()} max={c.max()} q10={c.quantile(.1):.1f} q90={c.quantile(.9):.1f}")

# ── 2. Subject mean deltas for the 9 frozen endpoints (wide table) ─────────
subject_delta_rows = []
for dataset in DATASETS:
    sub_ds = event_rows[event_rows["dataset_id"] == dataset]
    wide = event_count_per_subject[event_count_per_subject["dataset"] == dataset].set_index("subject_id")[["n_events"]].copy()
    for endpoint in GEOMETRY_COLS:
        ctrl_col = f"{endpoint}_control_median"
        if endpoint not in sub_ds.columns or ctrl_col not in sub_ds.columns:
            continue
        y = (sub_ds[endpoint] - sub_ds[ctrl_col]).rename("y")
        tmp = pd.concat([sub_ds["subject_id"], y], axis=1).dropna()
        wide[f"delta_{endpoint}"] = tmp.groupby("subject_id")["y"].mean()
    wide.insert(0, "dataset", dataset)
    subject_delta_rows.append(wide.reset_index())
subject_mean_deltas = pd.concat(subject_delta_rows, ignore_index=True)
subject_mean_deltas.to_csv(OUT / "subject_mean_deltas.csv", index=False)
print("\n--- 2. Subject mean deltas written ---")
print(f"  {OUT / 'subject_mean_deltas.csv'}")

# ── 3. Correlation between event count and subject delta ───────────────────
corr_rows = []
for dataset in DATASETS:
    wide = subject_mean_deltas[subject_mean_deltas["dataset"] == dataset]
    for endpoint in GEOMETRY_COLS:
        col = f"delta_{endpoint}"
        if col not in wide.columns:
            continue
        pair = wide[["n_events", col]].dropna()
        if len(pair) < 5:
            continue
        sp_r, sp_p = stats.spearmanr(pair["n_events"], pair[col])
        pe_r, pe_p = stats.pearsonr(pair["n_events"], pair[col])
        corr_rows.append({
            "dataset": dataset, "endpoint": endpoint, "n_subjects": len(pair),
            "spearman_r": sp_r, "spearman_p": sp_p,
            "pearson_r": pe_r, "pearson_p": pe_p,
        })
corr_df = pd.DataFrame(corr_rows)
corr_df.to_csv(OUT / "event_count_delta_correlation.csv", index=False)
print("\n--- 3. Correlation: event count vs subject delta ---")
print(corr_df.to_string(index=False))

# ── Shared per-endpoint event-level tables (used by 4-7) ───────────────────
endpoint_tables = {}
for dataset in DATASETS:
    sub_ds = event_rows[event_rows["dataset_id"] == dataset]
    covariates = available_covariates(sub_ds, CANDIDATE_COVARIATES)
    for endpoint in GEOMETRY_COLS:
        ctrl_col = f"{endpoint}_control_median"
        if endpoint not in sub_ds.columns or ctrl_col not in sub_ds.columns:
            continue
        sub = sub_ds.dropna(subset=[endpoint, ctrl_col, "subject_id", *covariates]).copy()
        if len(sub) < 10:
            continue
        sub["y_event_control"] = sub[endpoint] - sub[ctrl_col]
        endpoint_tables[(dataset, endpoint)] = (sub.reset_index(drop=True), covariates)

# ── 4. Leave-one-subject-out (LOSO) coefficients ────────────────────────────
loso_rows = []
for (dataset, endpoint), (sub, covariates) in endpoint_tables.items():
    X_full, y_full = build_design(sub, covariates)
    fit_full = fit_ols_cluster(
        "y_event_control ~ 1" + "".join(f" + {c}" for c in covariates), sub, groups_col="subject_id"
    )
    coef_full = float(fit_full.params.get("Intercept", np.nan)) if fit_full is not None else np.nan
    se_full = float(fit_full.bse.get("Intercept", np.nan)) if fit_full is not None else np.nan

    subj_ids = sub["subject_id"].to_numpy()
    n_events_by_subj = sub.groupby("subject_id").size()
    for subject in sub["subject_id"].unique():
        mask = subj_ids != subject
        if mask.sum() < 10:
            continue
        coef_without = ols_intercept_fast(X_full[mask], y_full[mask])
        loso_rows.append({
            "dataset": dataset, "endpoint": endpoint, "excluded_subject": subject,
            "n_events_excluded_subject": int(n_events_by_subj.get(subject, 0)),
            "coef_full": coef_full, "se_full": se_full,
            "coef_without": coef_without,
            "delta_coef": coef_without - coef_full,
            "delta_coef_studentized": (coef_without - coef_full) / se_full if se_full and np.isfinite(se_full) and se_full > 0 else np.nan,
        })
loso_df = pd.DataFrame(loso_rows)
loso_df.to_csv(OUT / "loso_coefficients.csv", index=False)
print("\n--- 4. LOSO: most influential subjects (|studentized delta| top 10) ---")
if len(loso_df):
    top_influence = loso_df.reindex(loso_df["delta_coef_studentized"].abs().sort_values(ascending=False).index).head(10)
    print(top_influence[["dataset", "endpoint", "excluded_subject", "n_events_excluded_subject",
                          "coef_full", "coef_without", "delta_coef_studentized"]].to_string(index=False))

# ── 5. Top-event-subject exclusion ──────────────────────────────────────────
exclusion_rows = []
for (dataset, endpoint), (sub, covariates) in endpoint_tables.items():
    counts = sub.groupby("subject_id").size().sort_values(ascending=False)
    for top_n in TOP_EXCLUSION_LEVELS.get(dataset, []):
        excluded_subjects = set(counts.index[:top_n])
        remaining = sub[~sub["subject_id"].isin(excluded_subjects)]
        if len(remaining) < 10 or remaining["subject_id"].nunique() < 5:
            continue
        fit = fit_ols_cluster(
            "y_event_control ~ 1" + "".join(f" + {c}" for c in covariates), remaining, groups_col="subject_id"
        )
        exclusion_rows.append({
            "dataset": dataset, "endpoint": endpoint, "top_n_excluded": top_n,
            "n_events_excluded": int(len(sub) - len(remaining)),
            "n_subjects_remaining": remaining["subject_id"].nunique(),
            "n_events_remaining": len(remaining),
            "coef": float(fit.params.get("Intercept", np.nan)) if fit is not None else np.nan,
            "se": float(fit.bse.get("Intercept", np.nan)) if fit is not None else np.nan,
            "p": float(fit.pvalues.get("Intercept", np.nan)) if fit is not None else np.nan,
        })
exclusion_df = pd.DataFrame(exclusion_rows)
exclusion_df.to_csv(OUT / "top_event_subject_exclusion.csv", index=False)
print("\n--- 5. Top-event-subject exclusion (BOAS) ---")
print(exclusion_df[exclusion_df["dataset"] == "ds005555"].to_string(index=False))

# ── 6. Event-balanced resampling ────────────────────────────────────────────
rng = np.random.default_rng(RNG_SEED)
resample_rows = []
for (dataset, endpoint), (sub, covariates) in endpoint_tables.items():
    counts = sub.groupby("subject_id").size()
    for cap in BALANCE_CAPS.get(dataset, []):
        eligible_subjects = counts[counts >= cap].index
        if len(eligible_subjects) < 5:
            continue
        idx_by_subject = {s: sub.index[sub["subject_id"] == s].to_numpy() for s in eligible_subjects}
        coefs = np.empty(N_RESAMPLE)
        for b in range(N_RESAMPLE):
            chosen_idx = np.concatenate([
                rng.choice(idx_by_subject[s], size=cap, replace=False) for s in eligible_subjects
            ])
            bal = sub.loc[chosen_idx]
            X_bal, y_bal = build_design(bal, covariates)
            coefs[b] = ols_intercept_fast(X_bal, y_bal)
        resample_rows.append({
            "dataset": dataset, "endpoint": endpoint, "cap_per_subject": cap,
            "n_subjects_retained": len(eligible_subjects),
            "n_events_per_resample": len(eligible_subjects) * cap,
            "coef_mean": float(coefs.mean()), "coef_median": float(np.median(coefs)),
            "coef_ci_lo": float(np.percentile(coefs, 2.5)), "coef_ci_hi": float(np.percentile(coefs, 97.5)),
            "frac_positive": float((coefs > 0).mean()),
        })
resample_df = pd.DataFrame(resample_rows)
resample_df.to_csv(OUT / "event_balanced_resampling.csv", index=False)
print("\n--- 6. Event-balanced resampling (BOAS) ---")
print(resample_df[resample_df["dataset"] == "ds005555"].to_string(index=False))

# ── 7. Subject-bootstrap CIs (cluster bootstrap) ────────────────────────────
boot_rows = []
for (dataset, endpoint), (sub, covariates) in endpoint_tables.items():
    subjects = sub["subject_id"].unique()
    n_subjects = len(subjects)
    idx_by_subject = {s: sub.index[sub["subject_id"] == s].to_numpy() for s in subjects}
    subj_mean_delta = sub.groupby("subject_id")["y_event_control"].mean()
    # sub.index is a 0..n-1 RangeIndex (endpoint_tables built with reset_index),
    # so idx_by_subject values are already valid positional indices into X_full/y_full.
    X_full, y_full = build_design(sub, covariates)

    ols_boot = np.empty(N_BOOT)
    mean_boot = np.empty(N_BOOT)
    for b in range(N_BOOT):
        chosen = rng.choice(subjects, size=n_subjects, replace=True)
        chosen_rows = np.concatenate([idx_by_subject[s] for s in chosen])
        ols_boot[b] = ols_intercept_fast(X_full[chosen_rows], y_full[chosen_rows])
        mean_boot[b] = subj_mean_delta.loc[chosen].mean()

    boot_rows.append({
        "dataset": dataset, "endpoint": endpoint, "n_subjects": n_subjects, "n_boot": N_BOOT,
        "ols_coef_boot_mean": float(ols_boot.mean()), "ols_coef_boot_se": float(ols_boot.std(ddof=1)),
        "ols_coef_ci_lo": float(np.percentile(ols_boot, 2.5)), "ols_coef_ci_hi": float(np.percentile(ols_boot, 97.5)),
        "subj_mean_boot_mean": float(mean_boot.mean()), "subj_mean_boot_se": float(mean_boot.std(ddof=1)),
        "subj_mean_ci_lo": float(np.percentile(mean_boot, 2.5)), "subj_mean_ci_hi": float(np.percentile(mean_boot, 97.5)),
    })
boot_df = pd.DataFrame(boot_rows)
boot_df.to_csv(OUT / "subject_bootstrap_ci.csv", index=False)
print("\n--- 7. Subject-bootstrap CIs (BOAS) ---")
print(boot_df[boot_df["dataset"] == "ds005555"].to_string(index=False))


# ── Diagnostic figures (BOAS focus; saved to figures/audit/, not the ────────
# manuscript figure set from 08_make_figures.py) ────────────────────────────
BOAS = "ds005555"

fig, axes = plt.subplots(1, len(HIGHLIGHT_ENDPOINTS), figsize=(4 * len(HIGHLIGHT_ENDPOINTS), 3.2), sharey=False)
wide_boas = subject_mean_deltas[subject_mean_deltas["dataset"] == BOAS]
for ax, endpoint in zip(axes, HIGHLIGHT_ENDPOINTS):
    col = f"delta_{endpoint}"
    pair = wide_boas[["n_events", col]].dropna()
    ax.scatter(pair["n_events"], pair[col], s=14, alpha=0.6, color="#E53935")
    if len(pair) > 2:
        b, a = np.polyfit(pair["n_events"], pair[col], 1)
        xs = np.linspace(pair["n_events"].min(), pair["n_events"].max(), 50)
        ax.plot(xs, a + b * xs, color="black", linewidth=1)
    r = corr_df[(corr_df["dataset"] == BOAS) & (corr_df["endpoint"] == endpoint)]
    if len(r):
        ax.set_title(f"{endpoint}: Spearman r={r['spearman_r'].iloc[0]:.2f} (p={r['spearman_p'].iloc[0]:.2f})")
    ax.axhline(0, color="grey", linewidth=0.6, linestyle="--")
    ax.set_xlabel("n_events (subject)")
    ax.set_ylabel("subject mean delta")
fig.suptitle("BOAS: event count vs. subject-level event−control delta")
fig.tight_layout()
fig.savefig(AUDIT_FIGURES_DIR / "audit_A_event_count_vs_delta.svg", format="svg", bbox_inches="tight")
plt.close(fig)
print(f"\n  Saved {AUDIT_FIGURES_DIR / 'audit_A_event_count_vs_delta.svg'}")

fig, ax = plt.subplots(figsize=(6.5, 3.4))
excl_boas = exclusion_df[exclusion_df["dataset"] == BOAS]
for endpoint in HIGHLIGHT_ENDPOINTS:
    sub = excl_boas[excl_boas["endpoint"] == endpoint].sort_values("top_n_excluded")
    ax.errorbar(sub["top_n_excluded"], sub["coef"], yerr=sub["se"], marker="o", capsize=2, label=endpoint)
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xlabel("# top event-count subjects excluded")
ax.set_ylabel("OLS intercept (event\u2212control)")
ax.set_title("BOAS: top-event-subject exclusion sensitivity")
ax.legend()
fig.tight_layout()
fig.savefig(AUDIT_FIGURES_DIR / "audit_B_top_exclusion_sensitivity.svg", format="svg", bbox_inches="tight")
plt.close(fig)
print(f"  Saved {AUDIT_FIGURES_DIR / 'audit_B_top_exclusion_sensitivity.svg'}")

fig, ax = plt.subplots(figsize=(6.5, 3.4))
resample_boas = resample_df[resample_df["dataset"] == BOAS]
width = 0.2
caps = sorted(resample_boas["cap_per_subject"].unique())
x = np.arange(len(HIGHLIGHT_ENDPOINTS))
for i, cap in enumerate(caps):
    sub = resample_boas[resample_boas["cap_per_subject"] == cap].set_index("endpoint").reindex(HIGHLIGHT_ENDPOINTS)
    yerr = np.vstack([sub["coef_median"] - sub["coef_ci_lo"], sub["coef_ci_hi"] - sub["coef_median"]])
    ax.errorbar(x + (i - (len(caps) - 1) / 2) * width, sub["coef_median"], yerr=yerr,
                fmt="o", capsize=3, label=f"cap={cap}")
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xticks(x)
ax.set_xticklabels(HIGHLIGHT_ENDPOINTS)
ax.set_ylabel("OLS intercept (event-balanced resampling, median + 95% CI)")
ax.set_title("BOAS: event-balanced (equal events/subject) resampling")
ax.legend()
fig.tight_layout()
fig.savefig(AUDIT_FIGURES_DIR / "audit_C_event_balanced_resampling.svg", format="svg", bbox_inches="tight")
plt.close(fig)
print(f"  Saved {AUDIT_FIGURES_DIR / 'audit_C_event_balanced_resampling.svg'}")

print("\n=== Pass A1 heterogeneity audit complete (Pass A1 primary table untouched) ===")
print(f"All outputs in: {OUT}")
print(f"Figures in: {AUDIT_FIGURES_DIR}")
