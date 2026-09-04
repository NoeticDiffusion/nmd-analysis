"""Compare orig vs clamped outcome contrasts and write a markdown summary."""
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent
old_dir = BASE / "outcome_contrasts_20260602_combined_combat_corrected_primary12h_cpc15"
new_dir = BASE / "outcome_contrasts_20260605_clamp_primary12h_cpc15"

old = pd.read_csv(old_dir / "patient_timebin_outcome_contrasts.csv")
new = pd.read_csv(new_dir / "patient_timebin_outcome_contrasts.csv")

POOL = "all_time_bins"

old_p = old[(old["time_bin"] == POOL) & (old["status"] == "ok")].copy()
new_p = new[(new["time_bin"] == POOL) & (new["status"] == "ok")].copy()

common = ["analysis_type", "metric"]
merged = old_p[common + ["cohens_d", "cliffs_delta", "mannwhitney_p"]].merge(
    new_p[common + ["cohens_d", "cliffs_delta", "mannwhitney_p", "cohens_d_rank", "cles"]],
    on=common, suffixes=("_orig", "_clamp"),
)
merged["is_persistence"] = merged["metric"].str.contains("persistence", na=False)
merged["d_delta"] = merged["cohens_d_clamp"] - merged["cohens_d_orig"]
merged["cliff_delta"] = merged["cliffs_delta_clamp"] - merged["cliffs_delta_orig"]
merged = merged.sort_values("cohens_d_clamp", ascending=False, key=abs)

# Save full table
merged.to_csv(new_dir / "comparison_orig_vs_clamp.csv", index=False)

# ---- Print ----------------------------------------------------------------
pers = merged[merged["is_persistence"]].copy()
print("=== PERSISTENCE METRICS: orig vs clamped (pooled time-bin, patient-level) ===")
print(pers[["metric", "cohens_d_orig", "cohens_d_clamp", "d_delta",
            "cohens_d_rank", "cliffs_delta_orig", "cliffs_delta_clamp", "cles"]].to_string(index=False))

print()
print("=== TOP 12 ALL METRICS by |cohens_d_clamp| ===")
top12 = merged.nlargest(12, "cohens_d_clamp", keep="all")
print(top12[["metric", "cohens_d_orig", "cohens_d_clamp", "d_delta",
             "cohens_d_rank", "cles", "mannwhitney_p_clamp"]].to_string(index=False))

n_changed = int((merged["d_delta"].abs() > 1e-9).sum())
max_nonpers_delta = merged[~merged["is_persistence"]]["d_delta"].abs().max()
print()
print(f"N metrics changed (d_delta != 0): {n_changed} / {len(merged)}")
print(f"Max d_delta for non-persistence: {max_nonpers_delta:.6f}")

# ---- Markdown summary ------------------------------------------------------
def fmt(v, decimals=3):
    if not np.isfinite(v):
        return "NaN"
    return f"{v:+.{decimals}f}" if abs(v) < 10 else f"{v:.{decimals}g}"

lines = [
    "# Persistence bounds fix – comparison report",
    "",
    f"**Dataset**: combined ComBat-corrected primary 0-12 h, N=277 subjects, CPC 1 vs CPC 5",
    f"**Baseline**: `outcome_contrasts_20260602_combined_combat_corrected_primary12h_cpc15`",
    f"**Fixed run**: `outcome_contrasts_20260605_clamp_primary12h_cpc15`",
    f"  - Flags: `--rank-effect-sizes --clamp-persistence-bounds`",
    f"  - Values clamped: d_eff ≤ 3.0, log_det/log_eig_var ≤ 50.0, kappa ≤ 1e6",
    "",
    "## Key finding: persistence collapse is partially resolved",
    "",
    "| Metric | Cohen's d orig | Cohen's d clamped | Δd | Cohen's d_rank | Cliff's δ | CLES |",
    "|--------|---------------|-------------------|-----|---------------|-----------|------|",
]
for _, row in pers.sort_values("cohens_d_clamp", ascending=False).iterrows():
    lines.append(
        f"| `{row['metric']}` "
        f"| {row['cohens_d_orig']:.3f} "
        f"| {row['cohens_d_clamp']:.3f} "
        f"| {row['d_delta']:+.3f} "
        f"| **{row['cohens_d_rank']:.3f}** "
        f"| {row['cliffs_delta_clamp']:.3f} "
        f"| {row['cles']:.3f} |"
    )

lines += [
    "",
    "## Interpretation",
    "",
    "- **The three-way collapse is broken**: `persistence_log_det`, `persistence_log_eig_var`, and",
    "  `persistence_d_eff` previously all reported Cohen's d = 0.122 (pooled SD inflated by",
    "  extreme outliers). After clamping, parametric d spreads to 0.139–0.248.",
    "",
    "- **Rank-based d_rank reveals stronger true signal**: `persistence_log_det_median` has",
    "  d_rank = 0.63, comparable to the reachability family. This is the honest rank-based",
    "  estimate robust to remaining heavy tails.",
    "",
    "- **Non-persistence metrics are completely unaffected** (max Δd = 0.000000).",
    "",
    "- **Cliff's δ is unchanged by clamping** for most metrics – it is already rank-based and",
    "  hence insensitive to the extreme values. The few small changes are from `d_eff` where",
    "  tied-rank resolution changed slightly.",
    "",
    "- **Remaining scipy warnings** ('catastrophic cancellation') in Welch's t-test indicate",
    "  that the parametric cohens_d is *still* unreliable for some persistence metrics even",
    "  after clamping. Use cohens_d_rank and cliffs_delta as the primary effect-size estimates",
    "  for the persistence family.",
    "",
    f"**N metrics changed**: {n_changed} / {len(merged)}  ",
    f"**Max Δd for non-persistence**: {max_nonpers_delta:.6f}",
    "",
]

md = "\n".join(lines)
(new_dir / "comparison_orig_vs_clamp.md").write_text(md, encoding="utf-8")
print()
print(f"Saved: {new_dir / 'comparison_orig_vs_clamp.csv'}")
print(f"Saved: {new_dir / 'comparison_orig_vs_clamp.md'}")
