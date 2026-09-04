from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PRIMARY_SUMMARY_DIR = ARTICLE_DIR / "results" / "mnps_summary_20260526_regional_primary12h"
DEFAULT_HOURLY_SUMMARY_DIR = ARTICLE_DIR / "results" / "mnps_summary_20260526_regional_hourly12h"
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "article_exports_20260526_regional_cpc15"
DEFAULT_FIGURE_DIR = ARTICLE_DIR / "figures" / "20260526_regional_cpc15"

GOOD_CPC = 1
POOR_CPC = 5
PRIMARY_TIME_BIN = "0_12h"
HOURLY_BINS: tuple[str, ...] = tuple(f"{hour}_{hour + 1}h" for hour in range(12))
REGION_ORDER: tuple[str, ...] = (
    "frontal",
    "central",
    "parietal_occipital",
    "temporal",
    "midline",
    "left_hemisphere",
    "right_hemisphere",
)
REACHABILITY_ANALYSIS = "regional_reachability_cones_3d"
MNJ_ANALYSIS = "regional_mnps_jacobian_3d"
REACHABILITY_METRICS: tuple[str, ...] = (
    "tube_d_eff_median",
    "persistence_kappa_median",
    "persistence_log_eig_var_median",
    "tube_a_operator_norm_median",
    "tube_capture_gate_median",
)
MNJ_METRICS: tuple[str, ...] = (
    "spectral_radius_median",
    "anisotropy_abs_eig_median",
    "mdr_median",
    "rotational_power_mean",
    "rotational_power_median",
    "frobenius_norm_median",
)
PRIMARY_REACHABILITY_LABELS: dict[str, str] = {
    "tube_d_eff_median": "d_eff",
    "persistence_kappa_median": "Pers. kappa",
    "persistence_log_eig_var_median": "Pers. log eig var",
    "tube_a_operator_norm_median": "A-op norm",
    "tube_capture_gate_median": "Capture gate",
}
PRIMARY_MNJ_LABELS: dict[str, str] = {
    "spectral_radius_median": "Spectral radius",
    "anisotropy_abs_eig_median": "Anisotropy |eig|",
    "mdr_median": "MDR",
    "rotational_power_mean": "Rot power mean",
    "rotational_power_median": "Rot power median",
    "frobenius_norm_median": "Frobenius norm",
}
FAMILY_METRICS: dict[str, tuple[str, ...]] = {
    "d_eff": ("tube_d_eff_median",),
    "persistence": ("persistence_kappa_median", "persistence_log_eig_var_median"),
    "capture": ("tube_a_operator_norm_median", "tube_capture_gate_median"),
}
HOURLY_LEAD_METRICS: tuple[str, ...] = (
    "tube_d_eff_median",
    "persistence_kappa_median",
    "tube_a_operator_norm_median",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build manuscript-facing regional coma exports from patient/time-bin summary files."
    )
    parser.add_argument("--primary-summary-dir", type=Path, default=DEFAULT_PRIMARY_SUMMARY_DIR)
    parser.add_argument("--hourly-summary-dir", type=Path, default=DEFAULT_HOURLY_SUMMARY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    return parser.parse_args()


def bh_fdr(p_values: pd.Series) -> pd.Series:
    values = pd.to_numeric(p_values, errors="coerce").to_numpy(dtype=float)
    out = np.full(values.shape, np.nan, dtype=float)
    mask = np.isfinite(values)
    if not mask.any():
        return pd.Series(out, index=p_values.index, dtype=float)
    valid = values[mask]
    order = np.argsort(valid)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(valid) + 1)
    q = valid * len(valid) / ranks
    q_sorted = np.minimum.accumulate(q[order][::-1])[::-1]
    q_final = np.empty_like(q_sorted)
    q_final[order] = np.clip(q_sorted, 0.0, 1.0)
    out[np.where(mask)[0]] = q_final
    return pd.Series(out, index=p_values.index, dtype=float)


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    good = np.asarray(good, dtype=float)
    poor = np.asarray(poor, dtype=float)
    good = good[np.isfinite(good)]
    poor = poor[np.isfinite(poor)]
    if good.size < 2 or poor.size < 2:
        return float("nan")
    pooled = ((good.size - 1) * np.var(good, ddof=1) + (poor.size - 1) * np.var(poor, ddof=1)) / (
        good.size + poor.size - 2
    )
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled))


def format_q(value: float) -> str:
    if not np.isfinite(value):
        return "NA"
    if value < 1e-3:
        return f"{value:.2e}"
    return f"{value:.3f}"


def format_dq(d_value: float, q_value: float) -> str:
    if not np.isfinite(d_value):
        return "NA"
    return f"{d_value:+.2f} (q={format_q(q_value)})"


def hour_start(time_bin: str) -> int:
    return int(str(time_bin).split("_")[0])


def load_metric_rows(
    summary_dir: Path,
    *,
    analysis_type: str,
    metrics: Iterable[str],
    time_bins: Iterable[str],
) -> pd.DataFrame:
    frame = pd.read_csv(summary_dir / "patient_timebin_signal_metrics.csv", low_memory=False)
    frame = frame[
        (frame["analysis_type"] == analysis_type)
        & (frame["metric"].isin(tuple(metrics)))
        & (frame["time_bin"].isin(tuple(time_bins)))
    ].copy()
    if frame.empty:
        return frame
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([float(GOOD_CPC), float(POOR_CPC)])].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["value"].notna()].copy()
    if "network" not in frame.columns:
        frame["network"] = frame.get("block_scope")
    frame["network"] = frame["network"].astype(str)
    frame["outcome_label"] = np.where(frame["cpc_numeric"] == float(GOOD_CPC), "CPC1", "CPC5")
    frame["hour_start"] = frame["time_bin"].astype(str).map(hour_start)
    return frame.reset_index(drop=True)


def build_contrasts(frame: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for (analysis_type, network, metric, time_bin), group in frame.groupby(
        ["analysis_type", "network", "metric", "time_bin"], sort=False, dropna=False
    ):
        good = pd.to_numeric(group.loc[group["outcome_label"] == "CPC1", "value"], errors="coerce").dropna().to_numpy(dtype=float)
        poor = pd.to_numeric(group.loc[group["outcome_label"] == "CPC5", "value"], errors="coerce").dropna().to_numpy(dtype=float)
        row: Dict[str, Any] = {
            "analysis_type": str(analysis_type),
            "network": str(network),
            "metric": str(metric),
            "time_bin": str(time_bin),
            "hour_start": hour_start(str(time_bin)),
            "n_cpc1": int(good.size),
            "n_cpc5": int(poor.size),
            "cpc1_mean": float(np.mean(good)) if good.size else float("nan"),
            "cpc5_mean": float(np.mean(poor)) if poor.size else float("nan"),
            "cpc1_median": float(np.median(good)) if good.size else float("nan"),
            "cpc5_median": float(np.median(poor)) if poor.size else float("nan"),
            "delta_median_cpc1_minus_cpc5": float(np.median(good) - np.median(poor)) if good.size and poor.size else float("nan"),
            "cohens_d": cohens_d(good, poor),
            "status": "ok",
        }
        if good.size and poor.size:
            _, p_value = stats.mannwhitneyu(good, poor, alternative="two-sided")
            row["mannwhitney_p"] = float(p_value)
        else:
            row["mannwhitney_p"] = float("nan")
            row["status"] = "insufficient_groups"
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["bh_fdr_q"] = np.nan
    for keys, group in out.groupby(["analysis_type", "time_bin"], sort=False):
        out.loc[group.index, "bh_fdr_q"] = bh_fdr(group["mannwhitney_p"]).to_numpy(dtype=float)
    out["abs_d"] = pd.to_numeric(out["cohens_d"], errors="coerce").abs()
    out["direction"] = np.where(out["cohens_d"] < 0.0, "CPC1<CPC5", "CPC1>CPC5")
    return out.sort_values(["analysis_type", "time_bin", "network", "metric"]).reset_index(drop=True)


def build_primary_table(contrasts: pd.DataFrame, *, metrics: tuple[str, ...], labels: dict[str, str]) -> pd.DataFrame:
    sub = contrasts[(contrasts["time_bin"] == PRIMARY_TIME_BIN) & (contrasts["metric"].isin(metrics))].copy()
    if sub.empty:
        return pd.DataFrame()
    sub["metric_label"] = sub["metric"].map(labels)
    sub["article_cell"] = [
        format_dq(d_value, q_value)
        for d_value, q_value in zip(pd.to_numeric(sub["cohens_d"], errors="coerce"), pd.to_numeric(sub["bh_fdr_q"], errors="coerce"))
    ]
    score = (
        sub.groupby("network", as_index=False)
        .agg(mean_abs_d=("abs_d", "mean"), n_q_lt_0_05=("bh_fdr_q", lambda x: int((pd.to_numeric(x, errors="coerce") < 0.05).sum())))
    )
    pivot = sub.pivot(index="network", columns="metric_label", values="article_cell").reset_index()
    out = pd.DataFrame({"network": list(REGION_ORDER)}).merge(pivot, on="network", how="left")
    out = out.merge(score, on="network", how="left")
    out["mean_abs_d"] = pd.to_numeric(out["mean_abs_d"], errors="coerce")
    out["n_q_lt_0_05"] = pd.to_numeric(out["n_q_lt_0_05"], errors="coerce")
    return out.sort_values(["mean_abs_d", "network"], ascending=[False, True]).reset_index(drop=True)


def _family_effect(contrasts: pd.DataFrame, region: str, metrics: Iterable[str]) -> float:
    sub = contrasts[
        (contrasts["time_bin"] == PRIMARY_TIME_BIN)
        & (contrasts["network"] == region)
        & (contrasts["metric"].isin(tuple(metrics)))
    ].copy()
    return float(pd.to_numeric(sub["cohens_d"], errors="coerce").mean()) if not sub.empty else float("nan")


def build_lateralization_summary(contrasts: pd.DataFrame) -> pd.DataFrame:
    notes = []
    left_capacity = _family_effect(contrasts, "left_hemisphere", FAMILY_METRICS["d_eff"])
    right_capacity = _family_effect(contrasts, "right_hemisphere", FAMILY_METRICS["d_eff"])
    left_persistence = _family_effect(contrasts, "left_hemisphere", FAMILY_METRICS["persistence"])
    right_persistence = _family_effect(contrasts, "right_hemisphere", FAMILY_METRICS["persistence"])
    left_capture = _family_effect(contrasts, "left_hemisphere", FAMILY_METRICS["capture"])
    right_capture = _family_effect(contrasts, "right_hemisphere", FAMILY_METRICS["capture"])
    left_right_gap = np.nanmean(
        np.abs(
            np.asarray(
                [
                    left_capacity - right_capacity,
                    left_persistence - right_persistence,
                    left_capture - right_capture,
                ],
                dtype=float,
            )
        )
    )
    if np.isfinite(left_right_gap) and left_right_gap < 0.15:
        lr_note = "largely bilateral pattern"
    elif np.nanmean([left_capacity, left_persistence, left_capture]) < np.nanmean([right_capacity, right_persistence, right_capture]):
        lr_note = "slight right-weighted separation"
    else:
        lr_note = "slight left-weighted separation"
    notes.append(
        {
            "comparison": "Left vs right overall pattern",
            "d_eff": f"L {left_capacity:+.2f} / R {right_capacity:+.2f}",
            "persistence": f"L {left_persistence:+.2f} / R {right_persistence:+.2f}",
            "capture": f"L {left_capture:+.2f} / R {right_capture:+.2f}",
            "interpretive_note": lr_note,
        }
    )

    mid_capacity = _family_effect(contrasts, "midline", FAMILY_METRICS["d_eff"])
    mid_persistence = _family_effect(contrasts, "midline", FAMILY_METRICS["persistence"])
    mid_capture = _family_effect(contrasts, "midline", FAMILY_METRICS["capture"])
    bilateral_capacity = float(np.nanmean([left_capacity, right_capacity]))
    bilateral_persistence = float(np.nanmean([left_persistence, right_persistence]))
    bilateral_capture = float(np.nanmean([left_capture, right_capture]))
    midline_gap = np.nanmean(
        np.abs(
            np.asarray(
                [
                    mid_capacity - bilateral_capacity,
                    mid_persistence - bilateral_persistence,
                    mid_capture - bilateral_capture,
                ],
                dtype=float,
            )
        )
    )
    mid_note = "midline-emphasized" if np.isfinite(midline_gap) and midline_gap >= 0.15 else "midline similar to bilateral"
    notes.append(
        {
            "comparison": "Midline vs bilateral pattern",
            "d_eff": f"M {mid_capacity:+.2f} / Bil {bilateral_capacity:+.2f}",
            "persistence": f"M {mid_persistence:+.2f} / Bil {bilateral_persistence:+.2f}",
            "capture": f"M {mid_capture:+.2f} / Bil {bilateral_capture:+.2f}",
            "interpretive_note": mid_note,
        }
    )
    return pd.DataFrame(notes)


def build_hourly_summary(contrasts: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for network in REGION_ORDER:
        net = contrasts[(contrasts["network"] == network) & (contrasts["metric"].isin(HOURLY_LEAD_METRICS))].copy()
        if net.empty:
            continue
        lead = net[net["metric"] == "tube_d_eff_median"].copy().sort_values("hour_start")
        significant = lead[pd.to_numeric(lead["bh_fdr_q"], errors="coerce") < 0.05]
        earliest = significant.iloc[0]["time_bin"] if not significant.empty else "none"
        peak = lead.iloc[lead["abs_d"].fillna(-np.inf).to_numpy().argmax()]["time_bin"] if not lead.empty else "none"
        late = lead[(lead["hour_start"] >= 6) & (pd.to_numeric(lead["bh_fdr_q"], errors="coerce") < 0.05)]
        late_label = late.iloc[-1]["time_bin"] if not late.empty else "none"
        strongest_metric_row = net.iloc[net["abs_d"].fillna(-np.inf).to_numpy().argmax()]
        strongest_metric = strongest_metric_row["metric"]
        support_metrics = net[(net["time_bin"] == peak) & (net["metric"] != strongest_metric) & (net["direction"] == strongest_metric_row["direction"])]
        note = PRIMARY_REACHABILITY_LABELS.get(strongest_metric, str(strongest_metric))
        if len(support_metrics):
            note += " with same-direction support"
        rows.append(
            {
                "network": network,
                "earliest_coherent_bin": str(earliest),
                "peak_interval": str(peak),
                "late_persistence": str(late_label),
                "notes": note,
            }
        )
    return pd.DataFrame(rows)


def build_article_summary(
    reachability_table: pd.DataFrame,
    mnj_table: pd.DataFrame,
    lateralization: pd.DataFrame,
    hourly_summary: pd.DataFrame,
    primary_reachability: pd.DataFrame,
) -> str:
    reach_top = reachability_table.iloc[0]["network"] if not reachability_table.empty else "unavailable"
    mnj_top = mnj_table.iloc[0]["network"] if not mnj_table.empty else "unavailable"
    metric_strength = (
        primary_reachability.groupby("metric", as_index=False)
        .agg(mean_abs_d=("abs_d", "mean"))
        .sort_values("mean_abs_d", ascending=False)
    )
    lead_metric = metric_strength.iloc[0]["metric"] if not metric_strength.empty else "unavailable"
    lead_metric_label = PRIMARY_REACHABILITY_LABELS.get(str(lead_metric), str(lead_metric))
    hourly_top = hourly_summary.iloc[0]["network"] if not hourly_summary.empty else "unavailable"
    lines = [
        "# Regional article summary",
        "",
        f"- strongest pooled regional reachability signal by mean absolute effect: `{reach_top}`",
        f"- strongest pooled regional MNJ signal by mean absolute effect: `{mnj_top}`",
        f"- reachability family lead across regions: `{lead_metric_label}`",
        f"- first hourly summary row in table order: `{hourly_top}`",
        "",
        "## Lateralization note",
        "",
    ]
    for _, row in lateralization.iterrows():
        lines.append(
            f"- `{row['comparison']}`: {row['interpretive_note']} "
            f"(d_eff {row['d_eff']}; persistence {row['persistence']}; capture {row['capture']})"
        )
    lines.extend(
        [
            "",
            "## Output files",
            "",
            "- `regional_primary_metric_contrasts.csv`: all primary regional reachability and MNJ contrasts.",
            "- `regional_hourly_reachability_contrasts.csv`: hourly regional reachability contrasts.",
            "- `regional_reachability_ranking_table.csv`: article-facing Table 3 source.",
            "- `regional_lateralization_summary.csv`: article-facing Table 4 source.",
            "- `regional_hourly_summary.csv`: article-facing Table 5 source.",
            "- `regional_mnj_primary_table.csv`: article-facing MNJ appendix/source table.",
        ]
    )
    return "\n".join(lines)


def write_primary_heatmap(frame: pd.DataFrame, *, metrics: tuple[str, ...], labels: dict[str, str], output_path: Path, title: str) -> None:
    sub = frame[(frame["time_bin"] == PRIMARY_TIME_BIN) & (frame["metric"].isin(metrics))].copy()
    if sub.empty:
        return
    matrix = sub.pivot(index="network", columns="metric", values="cohens_d").reindex(index=list(REGION_ORDER), columns=list(metrics))
    qvals = sub.pivot(index="network", columns="metric", values="bh_fdr_q").reindex(index=list(REGION_ORDER), columns=list(metrics))
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    im = ax.imshow(matrix.to_numpy(dtype=float), cmap="coolwarm_r", vmin=-1.0, vmax=1.0, aspect="auto")
    ax.set_xticks(np.arange(len(matrix.columns)))
    ax.set_xticklabels([labels.get(metric, metric) for metric in matrix.columns], rotation=45, ha="right")
    ax.set_yticks(np.arange(len(matrix.index)))
    ax.set_yticklabels(matrix.index.tolist())
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix.iloc[i, j]
            q_value = qvals.iloc[i, j]
            label = "NA" if not np.isfinite(value) else f"{value:+.2f}"
            if np.isfinite(q_value) and q_value < 0.05:
                label += "*"
            ax.text(j, i, label, ha="center", va="center", fontsize=7.5, color="#111827")
    ax.set_title(title)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Cohen's d (CPC1 - CPC5)")
    fig.tight_layout()
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def write_hourly_heatmap(frame: pd.DataFrame, output_path: Path) -> None:
    if frame.empty:
        return
    fig, axes = plt.subplots(1, len(HOURLY_LEAD_METRICS), figsize=(14.5, 4.6), sharey=True)
    if len(HOURLY_LEAD_METRICS) == 1:
        axes = [axes]
    for ax, metric in zip(axes, HOURLY_LEAD_METRICS):
        sub = frame[frame["metric"] == metric].copy()
        matrix = sub.pivot(index="network", columns="time_bin", values="cohens_d").reindex(
            index=list(REGION_ORDER), columns=list(HOURLY_BINS)
        )
        qvals = sub.pivot(index="network", columns="time_bin", values="bh_fdr_q").reindex(
            index=list(REGION_ORDER), columns=list(HOURLY_BINS)
        )
        im = ax.imshow(matrix.to_numpy(dtype=float), cmap="coolwarm_r", vmin=-1.0, vmax=1.0, aspect="auto")
        ax.set_title(PRIMARY_REACHABILITY_LABELS.get(metric, metric))
        ax.set_xticks(np.arange(len(matrix.columns)))
        ax.set_xticklabels(matrix.columns, rotation=45, ha="right", fontsize=7)
        ax.set_yticks(np.arange(len(matrix.index)))
        ax.set_yticklabels(matrix.index.tolist())
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                value = matrix.iloc[i, j]
                q_value = qvals.iloc[i, j]
                label = "" if not np.isfinite(value) else f"{value:+.1f}"
                if np.isfinite(q_value) and q_value < 0.05:
                    label += "*"
                ax.text(j, i, label, ha="center", va="center", fontsize=5.6, color="#111827")
    cbar = fig.colorbar(im, ax=axes, fraction=0.021, pad=0.02)
    cbar.set_label("Cohen's d (CPC1 - CPC5)")
    fig.suptitle("Regional hourly reachability separation")
    fig.tight_layout()
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.figure_dir.mkdir(parents=True, exist_ok=True)

    primary_reachability_rows = load_metric_rows(
        args.primary_summary_dir,
        analysis_type=REACHABILITY_ANALYSIS,
        metrics=REACHABILITY_METRICS,
        time_bins=(PRIMARY_TIME_BIN,),
    )
    primary_mnj_rows = load_metric_rows(
        args.primary_summary_dir,
        analysis_type=MNJ_ANALYSIS,
        metrics=MNJ_METRICS,
        time_bins=(PRIMARY_TIME_BIN,),
    )
    hourly_reachability_rows = load_metric_rows(
        args.hourly_summary_dir,
        analysis_type=REACHABILITY_ANALYSIS,
        metrics=REACHABILITY_METRICS,
        time_bins=HOURLY_BINS,
    )

    primary_contrasts = build_contrasts(pd.concat([primary_reachability_rows, primary_mnj_rows], ignore_index=True))
    hourly_contrasts = build_contrasts(hourly_reachability_rows)

    reachability_table = build_primary_table(
        primary_contrasts[primary_contrasts["analysis_type"] == REACHABILITY_ANALYSIS].copy(),
        metrics=REACHABILITY_METRICS,
        labels=PRIMARY_REACHABILITY_LABELS,
    )
    mnj_table = build_primary_table(
        primary_contrasts[primary_contrasts["analysis_type"] == MNJ_ANALYSIS].copy(),
        metrics=MNJ_METRICS,
        labels=PRIMARY_MNJ_LABELS,
    )
    lateralization = build_lateralization_summary(primary_contrasts[primary_contrasts["analysis_type"] == REACHABILITY_ANALYSIS].copy())
    hourly_summary = build_hourly_summary(hourly_contrasts)

    primary_contrasts.to_csv(args.output_dir / "regional_primary_metric_contrasts.csv", index=False)
    hourly_contrasts.to_csv(args.output_dir / "regional_hourly_reachability_contrasts.csv", index=False)
    reachability_table.to_csv(args.output_dir / "regional_reachability_ranking_table.csv", index=False)
    mnj_table.to_csv(args.output_dir / "regional_mnj_primary_table.csv", index=False)
    lateralization.to_csv(args.output_dir / "regional_lateralization_summary.csv", index=False)
    hourly_summary.to_csv(args.output_dir / "regional_hourly_summary.csv", index=False)

    summary_md = build_article_summary(
        reachability_table,
        mnj_table,
        lateralization,
        hourly_summary,
        primary_contrasts[primary_contrasts["analysis_type"] == REACHABILITY_ANALYSIS].copy(),
    )
    (args.output_dir / "regional_article_summary.md").write_text(summary_md, encoding="utf-8")
    manifest = {
        "primary_summary_dir": str(args.primary_summary_dir),
        "hourly_summary_dir": str(args.hourly_summary_dir),
        "primary_time_bin": PRIMARY_TIME_BIN,
        "hourly_bins": list(HOURLY_BINS),
        "regions": list(REGION_ORDER),
        "reachability_metrics": list(REACHABILITY_METRICS),
        "mnj_metrics": list(MNJ_METRICS),
    }
    (args.output_dir / "regional_article_export_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    write_primary_heatmap(
        primary_contrasts[primary_contrasts["analysis_type"] == REACHABILITY_ANALYSIS].copy(),
        metrics=REACHABILITY_METRICS,
        labels=PRIMARY_REACHABILITY_LABELS,
        output_path=args.figure_dir / "regional_primary_reachability_heatmap.svg",
        title="Regional reachability separation in the 0-12 h window",
    )
    write_primary_heatmap(
        primary_contrasts[primary_contrasts["analysis_type"] == MNJ_ANALYSIS].copy(),
        metrics=MNJ_METRICS,
        labels=PRIMARY_MNJ_LABELS,
        output_path=args.figure_dir / "regional_primary_mnj_heatmap.svg",
        title="Regional MNJ separation in the 0-12 h window",
    )
    write_hourly_heatmap(hourly_contrasts, args.figure_dir / "regional_hourly_reachability_panels.svg")

    print(f"Wrote regional article exports to {args.output_dir}")
    print(f"Wrote regional figures to {args.figure_dir}")


if __name__ == "__main__":
    main()
