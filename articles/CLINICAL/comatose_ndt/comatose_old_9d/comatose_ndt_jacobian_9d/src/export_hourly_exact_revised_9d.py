from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from jacobian_9d_support import (
    HOURLY_BINS,
    HOURLY_EXACT_DIR,
    MAIN_ARTICLE_METRICS,
    PART1_HOURLY_9D_MNPS_DIR,
    PART2_HOURLY_9D_MNPS_DIR,
    bh_fdr,
    cohens_d,
    load_metric_long_bins,
)


DISPLAY_NAMES = {
    "spectral_radius_median": "Spectral radius",
    "anisotropy_abs_eig_median": "Anisotropy |eig|",
    "frobenius_norm_median": "Frobenius norm",
    "mdr_median": "MDR",
    "rotational_power_mean": "Rotational power mean",
    "rotational_power_median": "Rotational power median",
}


def load_hourly_metric_rows(input_dir: Path, *, cohort_tag: str) -> pd.DataFrame:
    frame = load_metric_long_bins(
        input_dir,
        analysis_type="global_mnps_jacobian_9d",
        metrics=MAIN_ARTICLE_METRICS,
        time_bins=HOURLY_BINS,
    )
    frame["cohort_tag"] = cohort_tag
    return frame


def load_hourly_cohort() -> pd.DataFrame:
    part1 = load_hourly_metric_rows(PART1_HOURLY_9D_MNPS_DIR, cohort_tag="part1")
    part2 = load_hourly_metric_rows(PART2_HOURLY_9D_MNPS_DIR, cohort_tag="part2")
    overlap = set(
        zip(
            part1["subject"].astype(str),
            part1["time_bin"].astype(str),
            part1["metric"].astype(str),
        )
    ) & set(
        zip(
            part2["subject"].astype(str),
            part2["time_bin"].astype(str),
            part2["metric"].astype(str),
        )
    )
    if overlap:
        sample = sorted(overlap)[:10]
        raise ValueError(f"Unexpected overlap between part1 and part2 hourly 9D rows: {sample}")
    return pd.concat([part1, part2], ignore_index=True)


def summarize_metric_hour(frame: pd.DataFrame, metric: str, time_bin: str) -> dict[str, Any]:
    sub = frame[(frame["metric"] == metric) & (frame["time_bin"] == time_bin)].copy()
    values = pd.to_numeric(sub["value"], errors="coerce")
    good = values[sub["label"] == 1].dropna().to_numpy(dtype=float)
    poor = values[sub["label"] == 0].dropna().to_numpy(dtype=float)
    row: dict[str, Any] = {
        "metric": metric,
        "label": DISPLAY_NAMES.get(metric, metric),
        "time_bin": time_bin,
        "hour_start": int(time_bin.split("_")[0]),
        "hour_end": int(time_bin.split("_")[1].replace("h", "")),
        "n_cpc1": int(good.size),
        "n_cpc5": int(poor.size),
        "cpc1_median": float(np.median(good)) if good.size else float("nan"),
        "cpc5_median": float(np.median(poor)) if poor.size else float("nan"),
        "cohens_d": cohens_d(good, poor),
    }
    if good.size and poor.size:
        _, p_value = stats.mannwhitneyu(good, poor, alternative="two-sided")
        row["mannwhitney_p"] = float(p_value)
    else:
        row["mannwhitney_p"] = float("nan")
    return row


def build_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for metric in MAIN_ARTICLE_METRICS:
        for time_bin in HOURLY_BINS:
            rows.append(summarize_metric_hour(frame, metric, time_bin))
    summary = pd.DataFrame(rows)
    summary["bh_fdr_q"] = np.nan
    for metric, group in summary.groupby("metric", sort=False):
        summary.loc[group.index, "bh_fdr_q"] = bh_fdr(group["mannwhitney_p"]).to_numpy(dtype=float)
    summary["abs_d"] = pd.to_numeric(summary["cohens_d"], errors="coerce").abs()
    summary["direction"] = np.where(summary["cohens_d"] >= 0.0, "higher in CPC1", "higher in CPC5")
    return summary


def build_markdown(summary: pd.DataFrame) -> str:
    lines = [
        "# Hourly Exact Revised 9D Metrics",
        "",
        "These outputs come from a fresh hourly rerun of `global_mnps_jacobian_9d` for the repaired `part1` and `part2` bundles.",
        "They therefore summarize the exact article-facing revised 9D metrics rather than the earlier best-available hourly proxies.",
        "",
    ]
    for metric in MAIN_ARTICLE_METRICS:
        sub = summary[summary["metric"] == metric].copy()
        strongest = sub.sort_values("abs_d", ascending=False).iloc[0]
        first_sig = sub[pd.to_numeric(sub["bh_fdr_q"], errors="coerce") < 0.05]
        first_sig_label = first_sig.sort_values("hour_start").iloc[0]["time_bin"] if not first_sig.empty else "none"
        lines.extend(
            [
                f"## `{metric}`",
                "",
                f"- strongest absolute effect bin: `{strongest['time_bin']}` (`d = {strongest['cohens_d']:+.3f}`)",
                f"- first FDR-significant bin: `{first_sig_label}`",
                "",
                "| Time bin | n CPC1 | n CPC5 | CPC1 median | CPC5 median | d | p | q |",
                "|---|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for _, row in sub.iterrows():
            lines.append(
                f"| {row['time_bin']} | {int(row['n_cpc1'])} | {int(row['n_cpc5'])} | "
                f"{row['cpc1_median']:.3f} | {row['cpc5_median']:.3f} | "
                f"{row['cohens_d']:+.3f} | {row['mannwhitney_p']:.3g} | {row['bh_fdr_q']:.3g} |"
            )
        lines.append("")
    return "\n".join(lines)


def write_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    matrix = summary.pivot(index="metric", columns="time_bin", values="cohens_d").reindex(
        index=list(MAIN_ARTICLE_METRICS),
        columns=list(HOURLY_BINS),
    )
    sig = summary.pivot(index="metric", columns="time_bin", values="bh_fdr_q").reindex(
        index=list(MAIN_ARTICLE_METRICS),
        columns=list(HOURLY_BINS),
    )
    fig, ax = plt.subplots(figsize=(12.5, 5.1))
    im = ax.imshow(matrix.to_numpy(dtype=float), cmap="coolwarm_r", vmin=-0.8, vmax=0.8, aspect="auto")
    ax.set_xticks(np.arange(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(matrix.index)))
    ax.set_yticklabels([DISPLAY_NAMES.get(metric, metric) for metric in matrix.index])
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix.iloc[i, j]
            q_value = sig.iloc[i, j]
            label = f"{value:.2f}"
            if np.isfinite(q_value) and q_value < 0.05:
                label += "*"
            ax.text(j, i, label, ha="center", va="center", fontsize=8, color="#111827")
    ax.set_title("Hourly outcome separation for exact revised 9D Jacobian metrics")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Cohen's d")
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    HOURLY_EXACT_DIR.mkdir(parents=True, exist_ok=True)
    cohort = load_hourly_cohort()
    summary = build_summary(cohort)
    cohort.to_csv(HOURLY_EXACT_DIR / "hourly_exact_revised_9d_patient_timebin_combined.csv", index=False)
    summary.to_csv(HOURLY_EXACT_DIR / "hourly_exact_revised_9d_summary.csv", index=False)
    (HOURLY_EXACT_DIR / "hourly_exact_revised_9d_summary.md").write_text(build_markdown(summary), encoding="utf-8")
    write_heatmap(summary, HOURLY_EXACT_DIR / "hourly_exact_revised_9d_heatmap.png")
    manifest = {
        "part1_mnps_dir": str(PART1_HOURLY_9D_MNPS_DIR),
        "part2_mnps_dir": str(PART2_HOURLY_9D_MNPS_DIR),
        "analysis_type": "global_mnps_jacobian_9d",
        "selected_metrics": list(MAIN_ARTICLE_METRICS),
        "hourly_bins": list(HOURLY_BINS),
        "note": "Fresh hourly rerun for the exact revised article-facing 9D Jacobian metrics.",
    }
    (HOURLY_EXACT_DIR / "hourly_exact_revised_9d_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote hourly exact revised 9D outputs to {HOURLY_EXACT_DIR}")


if __name__ == "__main__":
    main()
