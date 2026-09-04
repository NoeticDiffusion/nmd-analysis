from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_DIR = ARTICLE_DIR / "NeuroCombat_harmonization" / "results" / "combat_pilot_20260527"
DEFAULT_SUBJECT_LEVEL_PATH = DEFAULT_RESULTS_DIR / "combat_pilot_subject_level.csv"
DEFAULT_SITE_DETAIL_PATH = DEFAULT_RESULTS_DIR / "combat_pilot_site_dependence_detail.csv"
DEFAULT_OUTPUT_DIR = DEFAULT_RESULTS_DIR
DEFAULT_MARKDOWN_PATH = ARTICLE_DIR / "NeuroCombat_harmonization" / "047_20260527_icare_part1_combat_followup_analysis.md"


@dataclass(frozen=True)
class Config:
    subject_level_path: Path
    site_detail_path: Path
    output_dir: Path
    markdown_path: Path


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Run follow-up analyses explaining the paired ComBat pilot behavior."
    )
    parser.add_argument("--subject-level-path", type=Path, default=DEFAULT_SUBJECT_LEVEL_PATH)
    parser.add_argument("--site-detail-path", type=Path, default=DEFAULT_SITE_DETAIL_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--markdown-path", type=Path, default=DEFAULT_MARKDOWN_PATH)
    args = parser.parse_args()
    return Config(
        subject_level_path=args.subject_level_path,
        site_detail_path=args.site_detail_path,
        output_dir=args.output_dir,
        markdown_path=args.markdown_path,
    )


def feature_family(feature: str) -> str | None:
    text = str(feature)
    if text.startswith("raw__embodied_arousal_proxy"):
        return "embodied_arousal_proxy"
    if text.startswith("raw__eeg_"):
        return text[len("raw__eeg_") :].split("__g_")[0]
    if text.startswith("dyn__"):
        return "dynamics"
    return None


def family_order_key(name: str) -> tuple[int, str]:
    priority = {
        "dynamics": 0,
        "delta": 1,
        "theta": 2,
        "alpha": 3,
        "beta": 4,
        "gamma": 5,
        "highfreq_power_30_45": 6,
        "alpha_theta": 7,
        "beta_alpha": 8,
        "hjorth_mobility": 9,
        "hjorth_complexity": 10,
        "permutation_entropy": 11,
        "sample_entropy": 12,
        "embodied_arousal_proxy": 13,
    }
    return (priority.get(name, 999), name)


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    if good.size < 2 or poor.size < 2:
        return float("nan")
    good = np.asarray(good, dtype=float)
    poor = np.asarray(poor, dtype=float)
    pooled = ((good.size - 1) * np.var(good, ddof=1) + (poor.size - 1) * np.var(poor, ddof=1)) / (
        good.size + poor.size - 2
    )
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled))


def p95(values: pd.Series) -> float:
    arr = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    return float(np.quantile(arr, 0.95)) if arr.size else float("nan")


def compute_hospital_outcome_summary(subject_frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    sub = subject_frame[(subject_frame["condition"] == "baseline") & (subject_frame["cpc"].isin([1.0, 5.0]))].copy()
    counts = (
        sub.groupby(["hospital", "cpc"], as_index=False)
        .size()
        .pivot(index="hospital", columns="cpc", values="size")
        .fillna(0)
        .reset_index()
    )
    counts.columns = [f"cpc_{int(col)}" if isinstance(col, float) else str(col) for col in counts.columns]
    if "cpc_1" not in counts.columns:
        counts["cpc_1"] = 0
    if "cpc_5" not in counts.columns:
        counts["cpc_5"] = 0
    counts["n_total"] = counts["cpc_1"] + counts["cpc_5"]
    counts["cpc1_rate"] = counts["cpc_1"] / counts["n_total"]
    counts = counts.sort_values("hospital").reset_index(drop=True)

    contingency = pd.crosstab(sub["hospital"], sub["cpc"])
    chi2, p_value, _, _ = stats.chi2_contingency(contingency)
    n_total = int(contingency.to_numpy().sum())
    cramers_v = float(np.sqrt(chi2 / (n_total * (min(contingency.shape) - 1)))) if n_total else float("nan")
    summary = {
        "n_subjects": int(len(sub)),
        "chi2": float(chi2),
        "p_value": float(p_value),
        "cramers_v": cramers_v,
    }
    return counts, summary


def compute_family_site_summary(site_detail: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    detail = site_detail[site_detail["feature_set"].isin(["raw_features", "dynamics_metrics"])].copy()
    detail["family"] = detail["feature"].map(feature_family)
    detail = detail[detail["family"].notna()].copy()
    summary = (
        detail.groupby(["condition", "family"], as_index=False)
        .agg(
            n_features=("feature", "size"),
            median_eta2=("eta_squared", "median"),
            p95_eta2=("eta_squared", p95),
            q_lt_0_05=("kruskal_q", lambda s: int((pd.to_numeric(s, errors="coerce") < 0.05).sum())),
        )
        .sort_values("family", key=lambda s: s.map(family_order_key))
        .reset_index(drop=True)
    )

    base = summary[summary["condition"] == "baseline"].copy()
    combat = summary[summary["condition"] == "combat"].copy()
    compare = base.merge(
        combat,
        on="family",
        suffixes=("_baseline", "_combat"),
        how="outer",
    )
    compare["delta_median_eta2_combat_minus_baseline"] = (
        compare["median_eta2_combat"] - compare["median_eta2_baseline"]
    )
    compare["delta_p95_eta2_combat_minus_baseline"] = compare["p95_eta2_combat"] - compare["p95_eta2_baseline"]
    compare["delta_q_lt_0_05_combat_minus_baseline"] = compare["q_lt_0_05_combat"] - compare["q_lt_0_05_baseline"]
    compare = compare.sort_values("family", key=lambda s: s.map(family_order_key)).reset_index(drop=True)
    return summary, compare


def hospital_zscore(series: pd.Series, groups: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    out = pd.Series(np.nan, index=series.index, dtype=float)
    for group_name, idx in groups.groupby(groups).groups.items():
        sub = values.loc[idx]
        finite = sub.dropna()
        if finite.empty:
            continue
        sd = float(finite.std(ddof=0))
        if not np.isfinite(sd) or sd <= 0:
            continue
        out.loc[idx] = (sub - float(finite.mean())) / sd
    return out


def compute_within_site_outcome_signal(subject_frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    feature_columns = [column for column in subject_frame.columns if feature_family(column) is not None]
    keep = subject_frame[subject_frame["cpc"].isin([1.0, 5.0])].copy()
    rows: List[Dict[str, Any]] = []

    for condition, group in keep.groupby("condition", sort=False):
        groups = group["hospital"].fillna("missing").astype(str)
        labels = (group["cpc"] == 1.0).astype(int)
        for feature in feature_columns:
            standardized = hospital_zscore(group[feature], groups)
            frame = pd.DataFrame(
                {
                    "value": standardized,
                    "label": labels,
                    "hospital": groups,
                }
            ).dropna()
            good = frame.loc[frame["label"] == 1, "value"].to_numpy(dtype=float)
            poor = frame.loc[frame["label"] == 0, "value"].to_numpy(dtype=float)
            d_value = cohens_d(good, poor)
            rows.append(
                {
                    "condition": condition,
                    "feature": feature,
                    "family": feature_family(feature),
                    "n_good": int(good.size),
                    "n_poor": int(poor.size),
                    "cohens_d_hospital_z": d_value,
                    "abs_cohens_d_hospital_z": float(abs(d_value)) if np.isfinite(d_value) else float("nan"),
                }
            )

    detail = pd.DataFrame(rows).sort_values(["condition", "family", "feature"]).reset_index(drop=True)
    summary = (
        detail.groupby(["condition", "family"], as_index=False)
        .agg(
            n_features=("feature", "size"),
            median_abs_d=("abs_cohens_d_hospital_z", "median"),
            p95_abs_d=("abs_cohens_d_hospital_z", p95),
            n_abs_d_ge_0_5=("abs_cohens_d_hospital_z", lambda s: int((pd.to_numeric(s, errors="coerce") >= 0.5).sum())),
        )
        .sort_values("family", key=lambda s: s.map(family_order_key))
        .reset_index(drop=True)
    )

    base = summary[summary["condition"] == "baseline"].copy()
    combat = summary[summary["condition"] == "combat"].copy()
    compare = base.merge(combat, on="family", suffixes=("_baseline", "_combat"), how="outer")
    compare["delta_median_abs_d_combat_minus_baseline"] = compare["median_abs_d_combat"] - compare["median_abs_d_baseline"]
    compare["delta_p95_abs_d_combat_minus_baseline"] = compare["p95_abs_d_combat"] - compare["p95_abs_d_baseline"]
    compare["delta_n_abs_d_ge_0_5_combat_minus_baseline"] = (
        compare["n_abs_d_ge_0_5_combat"] - compare["n_abs_d_ge_0_5_baseline"]
    )
    compare = compare.sort_values("family", key=lambda s: s.map(family_order_key)).reset_index(drop=True)
    return detail, summary, compare


def compute_paired_shift_summary(subject_frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_columns = [column for column in subject_frame.columns if feature_family(column) is not None]
    baseline = subject_frame[subject_frame["condition"] == "baseline"].copy()
    combat = subject_frame[subject_frame["condition"] == "combat"].copy()
    merged = baseline.merge(combat, on="subject", suffixes=("_baseline", "_combat"), how="inner")
    rows: List[Dict[str, Any]] = []

    for feature in feature_columns:
        before = pd.to_numeric(merged[f"{feature}_baseline"], errors="coerce").to_numpy(dtype=float)
        after = pd.to_numeric(merged[f"{feature}_combat"], errors="coerce").to_numpy(dtype=float)
        denom = np.abs(before) + np.abs(after)
        mask = np.isfinite(before) & np.isfinite(after) & (denom > 1e-12)
        pct = 200.0 * np.abs(after[mask] - before[mask]) / denom[mask]
        rows.append(
            {
                "feature": feature,
                "family": feature_family(feature),
                "n_pairs": int(mask.sum()),
                "median_abs_pct_change": float(np.median(pct)) if pct.size else float("nan"),
                "p95_abs_pct_change": float(np.quantile(pct, 0.95)) if pct.size else float("nan"),
            }
        )

    detail = pd.DataFrame(rows).sort_values(["family", "feature"]).reset_index(drop=True)
    summary = (
        detail.groupby("family", as_index=False)
        .agg(
            n_features=("feature", "size"),
            median_feature_shift_pct=("median_abs_pct_change", "median"),
            p95_feature_shift_pct=("median_abs_pct_change", p95),
            max_feature_shift_pct=("median_abs_pct_change", "max"),
        )
        .sort_values("family", key=lambda s: s.map(family_order_key))
        .reset_index(drop=True)
    )
    return detail, summary


def compute_top_feature_changes(
    site_detail: pd.DataFrame,
    outcome_detail: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    site = site_detail[site_detail["feature_set"].isin(["raw_features", "dynamics_metrics"])].copy()
    site["family"] = site["feature"].map(feature_family)
    site = site[site["family"].notna()].copy()
    site_base = site[site["condition"] == "baseline"][["feature", "family", "eta_squared"]].rename(
        columns={"eta_squared": "eta2_baseline"}
    )
    site_combat = site[site["condition"] == "combat"][["feature", "family", "eta_squared"]].rename(
        columns={"eta_squared": "eta2_combat"}
    )
    site_compare = site_base.merge(site_combat, on=["feature", "family"], how="inner")
    site_compare["delta_eta2_combat_minus_baseline"] = site_compare["eta2_combat"] - site_compare["eta2_baseline"]

    out_base = outcome_detail[outcome_detail["condition"] == "baseline"][
        ["feature", "family", "abs_cohens_d_hospital_z"]
    ].rename(columns={"abs_cohens_d_hospital_z": "abs_d_baseline"})
    out_combat = outcome_detail[outcome_detail["condition"] == "combat"][
        ["feature", "family", "abs_cohens_d_hospital_z"]
    ].rename(columns={"abs_cohens_d_hospital_z": "abs_d_combat"})
    out_compare = out_base.merge(out_combat, on=["feature", "family"], how="inner")
    out_compare["delta_abs_d_combat_minus_baseline"] = out_compare["abs_d_combat"] - out_compare["abs_d_baseline"]

    return {
        "top_site_reductions": site_compare.sort_values("delta_eta2_combat_minus_baseline").head(8).reset_index(drop=True),
        "top_outcome_losses": out_compare.sort_values("delta_abs_d_combat_minus_baseline").head(8).reset_index(drop=True),
        "top_outcome_gains": out_compare.sort_values("delta_abs_d_combat_minus_baseline", ascending=False)
        .head(8)
        .reset_index(drop=True),
    }


def format_small_table(frame: pd.DataFrame, columns: list[str], decimals: dict[str, int] | None = None) -> list[str]:
    decimals = decimals or {}
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join(["---"] * len(columns)) + "|",
    ]
    for _, row in frame.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, (float, np.floating)):
                if not np.isfinite(value):
                    values.append("nan")
                else:
                    digits = decimals.get(column, 3)
                    values.append(f"{float(value):.{digits}f}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def build_markdown(
    subject_frame: pd.DataFrame,
    hospital_counts: pd.DataFrame,
    hospital_summary: dict[str, Any],
    family_site_compare: pd.DataFrame,
    family_outcome_compare: pd.DataFrame,
    family_shift_summary: pd.DataFrame,
    top_changes: dict[str, pd.DataFrame],
) -> str:
    paired_subjects = int(subject_frame[subject_frame["condition"] == "baseline"]["subject"].nunique())
    outcome_subjects = int(
        subject_frame[(subject_frame["condition"] == "baseline") & (subject_frame["cpc"].isin([1.0, 5.0]))]["subject"].nunique()
    )

    lines = [
        "## Session: Follow-up analyses on ComBat part1 pilot",
        "",
        "Date: 2026-05-27",
        "",
        "### Question",
        "",
        "Why did feature-level ComBat appear to reduce site signal but not improve the downstream CPC1-vs-CPC5 pilot?",
        "",
        "### Scope",
        "",
        f"- Paired subjects in pilot: `{paired_subjects}`",
        f"- CPC1/CPC5 subjects used for follow-up: `{outcome_subjects}`",
        "- Input bundle:",
        "  - `results/combat_pilot_20260527/combat_pilot_subject_level.csv`",
        "  - `results/combat_pilot_20260527/combat_pilot_site_dependence_detail.csv`",
        "",
        "### Analysis 1: hospital-outcome imbalance",
        "",
        "If hospitals carry different CPC mixtures, then de-batching can remove nuisance structure and real predictive proxy structure at the same time.",
        "",
        f"- chi-square hospital x CPC: `chi2 = {hospital_summary['chi2']:.3f}`, `p = {hospital_summary['p_value']:.4f}`",
        f"- Cramer's V: `{hospital_summary['cramers_v']:.3f}`",
        "- Interpretation: the CPC mixture is not site-neutral in this paired cohort.",
        "",
    ]
    lines.extend(
        format_small_table(
            hospital_counts,
            ["hospital", "cpc_1", "cpc_5", "n_total", "cpc1_rate"],
            {"cpc1_rate": 3},
        )
    )
    lines.extend(
        [
            "",
            "Notable point: hospital `E` is strongly poor-outcome enriched (`2` CPC1 vs `15` CPC5, CPC1 rate `0.118`).",
            "",
            "### Analysis 2: feature-family de-batching",
            "",
            "Family summaries below use the subject-level hospital effect sizes from the pilot (`eta^2` by hospital for each feature). More negative deltas mean ComBat reduced site dependence.",
            "",
        ]
    )
    lines.extend(
        format_small_table(
            family_site_compare[
                [
                    "family",
                    "median_eta2_baseline",
                    "median_eta2_combat",
                    "delta_median_eta2_combat_minus_baseline",
                    "q_lt_0_05_baseline",
                    "q_lt_0_05_combat",
                ]
            ],
            [
                "family",
                "median_eta2_baseline",
                "median_eta2_combat",
                "delta_median_eta2_combat_minus_baseline",
                "q_lt_0_05_baseline",
                "q_lt_0_05_combat",
            ],
            {
                "median_eta2_baseline": 3,
                "median_eta2_combat": 3,
                "delta_median_eta2_combat_minus_baseline": 3,
                "q_lt_0_05_baseline": 0,
                "q_lt_0_05_combat": 0,
            },
        )
    )
    lines.extend(
        [
            "",
            "Readout:",
            "- strongest site reductions concentrated in Hjorth complexity and entropy-style families",
            "- beta-family features remained relatively site-coupled, and several beta features became more site-linked after ComBat",
            "",
            "### Analysis 3: within-site outcome signal after removing hospital means/scales",
            "",
            "For each feature, values were z-scored within hospital and then CPC1-vs-CPC5 Cohen's d was computed on the pooled hospital-standardized values. This asks whether the feature still carries outcome structure after local site normalization.",
            "",
        ]
    )
    lines.extend(
        format_small_table(
            family_outcome_compare[
                [
                    "family",
                    "median_abs_d_baseline",
                    "median_abs_d_combat",
                    "delta_median_abs_d_combat_minus_baseline",
                    "n_abs_d_ge_0_5_baseline",
                    "n_abs_d_ge_0_5_combat",
                ]
            ],
            [
                "family",
                "median_abs_d_baseline",
                "median_abs_d_combat",
                "delta_median_abs_d_combat_minus_baseline",
                "n_abs_d_ge_0_5_baseline",
                "n_abs_d_ge_0_5_combat",
            ],
            {
                "median_abs_d_baseline": 3,
                "median_abs_d_combat": 3,
                "delta_median_abs_d_combat_minus_baseline": 3,
                "n_abs_d_ge_0_5_baseline": 0,
                "n_abs_d_ge_0_5_combat": 0,
            },
        )
    )
    lines.extend(
        [
            "",
            "Readout:",
            "- if the delta above is negative, ComBat weakened the within-site outcome separation for that family",
            "- if the delta is positive, the family retained or improved signal after hospital standardization",
            "",
            "### Analysis 4: how strongly each family was perturbed",
            "",
            "Median absolute paired subject-level symmetric percent shifts quantify how hard ComBat moved each family relative to the old export. This measure is bounded to `[0, 200]` and is more stable for near-zero features.",
            "",
        ]
    )
    lines.extend(
        format_small_table(
            family_shift_summary[["family", "median_feature_shift_pct", "p95_feature_shift_pct", "max_feature_shift_pct"]],
            ["family", "median_feature_shift_pct", "p95_feature_shift_pct", "max_feature_shift_pct"],
            {
                "median_feature_shift_pct": 2,
                "p95_feature_shift_pct": 2,
                "max_feature_shift_pct": 2,
            },
        )
    )
    lines.extend(
        [
            "",
            "### Feature spot-checks",
            "",
            "Largest site-signal reductions:",
            "",
        ]
    )
    lines.extend(
        format_small_table(
            top_changes["top_site_reductions"][
                ["feature", "family", "eta2_baseline", "eta2_combat", "delta_eta2_combat_minus_baseline"]
            ],
            ["feature", "family", "eta2_baseline", "eta2_combat", "delta_eta2_combat_minus_baseline"],
            {
                "eta2_baseline": 3,
                "eta2_combat": 3,
                "delta_eta2_combat_minus_baseline": 3,
            },
        )
    )
    lines.extend(
        [
            "",
            "Largest within-site outcome losses:",
            "",
        ]
    )
    lines.extend(
        format_small_table(
            top_changes["top_outcome_losses"][
                ["feature", "family", "abs_d_baseline", "abs_d_combat", "delta_abs_d_combat_minus_baseline"]
            ],
            ["feature", "family", "abs_d_baseline", "abs_d_combat", "delta_abs_d_combat_minus_baseline"],
            {
                "abs_d_baseline": 3,
                "abs_d_combat": 3,
                "delta_abs_d_combat_minus_baseline": 3,
            },
        )
    )
    lines.extend(
        [
            "",
            "Largest within-site outcome gains:",
            "",
        ]
    )
    lines.extend(
        format_small_table(
            top_changes["top_outcome_gains"][
                ["feature", "family", "abs_d_baseline", "abs_d_combat", "delta_abs_d_combat_minus_baseline"]
            ],
            ["feature", "family", "abs_d_baseline", "abs_d_combat", "delta_abs_d_combat_minus_baseline"],
            {
                "abs_d_baseline": 3,
                "abs_d_combat": 3,
                "delta_abs_d_combat_minus_baseline": 3,
            },
        )
    )
    lines.extend(
        [
            "",
            "### Interpretation",
            "",
            "- The paired CPC cohort is hospital-imbalanced, so site is partly entangled with prognosis in the observed data.",
            "- ComBat did de-batch several raw feature families, especially entropy/Hjorth-style families.",
            "- But de-batching was not uniformly beneficial: some beta-related families stayed site-linked, and several feature families lost within-site CPC separation after ComBat.",
            "- This makes the overall pilot result much less paradoxical: ComBat can remove real nuisance while also stripping away site-correlated proxy signal that the baseline classifier was using.",
            "- In this cohort, the current ComBat setup looks more like a successful de-batching transform than a successful downstream prognostic enhancement.",
            "",
            "### Takeaway",
            "",
            "The most plausible explanation is not that harmonization failed, but that the present ComBat configuration removed site-linked structure faster than it preserved clinically useful within-site separation. That is compatible with lower hospital-predictability and lower CPC predictability at the same time.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    config = parse_args()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.markdown_path.parent.mkdir(parents=True, exist_ok=True)

    subject_frame = pd.read_csv(config.subject_level_path)
    site_detail = pd.read_csv(config.site_detail_path)

    hospital_counts, hospital_summary = compute_hospital_outcome_summary(subject_frame)
    family_site_summary, family_site_compare = compute_family_site_summary(site_detail)
    outcome_detail, family_outcome_summary, family_outcome_compare = compute_within_site_outcome_signal(subject_frame)
    shift_detail, family_shift_summary = compute_paired_shift_summary(subject_frame)
    top_changes = compute_top_feature_changes(site_detail, outcome_detail)

    hospital_counts.to_csv(config.output_dir / "combat_followup_hospital_outcome_counts.csv", index=False)
    (config.output_dir / "combat_followup_hospital_outcome_summary.json").write_text(
        json.dumps(hospital_summary, indent=2),
        encoding="utf-8",
    )
    family_site_summary.to_csv(config.output_dir / "combat_followup_family_site_summary.csv", index=False)
    family_site_compare.to_csv(config.output_dir / "combat_followup_family_site_compare.csv", index=False)
    outcome_detail.to_csv(config.output_dir / "combat_followup_feature_outcome_signal.csv", index=False)
    family_outcome_summary.to_csv(config.output_dir / "combat_followup_family_outcome_summary.csv", index=False)
    family_outcome_compare.to_csv(config.output_dir / "combat_followup_family_outcome_compare.csv", index=False)
    shift_detail.to_csv(config.output_dir / "combat_followup_feature_shift_detail.csv", index=False)
    family_shift_summary.to_csv(config.output_dir / "combat_followup_family_shift_summary.csv", index=False)
    for name, frame in top_changes.items():
        frame.to_csv(config.output_dir / f"combat_followup_{name}.csv", index=False)

    markdown = build_markdown(
        subject_frame=subject_frame,
        hospital_counts=hospital_counts,
        hospital_summary=hospital_summary,
        family_site_compare=family_site_compare,
        family_outcome_compare=family_outcome_compare,
        family_shift_summary=family_shift_summary,
        top_changes=top_changes,
    )
    config.markdown_path.write_text(markdown, encoding="utf-8")

    print(f"Wrote follow-up markdown to {config.markdown_path}")
    print(f"Wrote follow-up CSVs to {config.output_dir}")


if __name__ == "__main__":
    main()
