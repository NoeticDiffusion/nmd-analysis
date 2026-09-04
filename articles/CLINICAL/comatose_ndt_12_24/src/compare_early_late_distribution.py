from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.mixture import GaussianMixture


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = (
    ARTICLE_DIR
    / "results"
    / "mnps_summary_20260525_combined_cpc15_hourly12h"
    / "patient_timebin_signal_metrics.csv"
)
DEFAULT_OUTPUT_DIR = ARTICLE_DIR / "results" / "distribution_windows_20260528_early14_vs_late812"
EARLY_BINS = ("1_2h", "2_3h", "3_4h")
LATE_BINS = ("8_9h", "9_10h", "10_11h", "11_12h")
ARTICLE_METRICS = (
    "persistence_log_eig_var_median",
    "persistence_kappa_median",
    "tube_d_eff_median",
    "tube_a_operator_norm_median",
    "tube_capture_gate_median",
)


@dataclass(frozen=True)
class Config:
    input_path: Path
    output_dir: Path
    early_bins: tuple[str, ...]
    late_bins: tuple[str, ...]
    metrics: tuple[str, ...]
    analysis_type: str = "reachability_cones"


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Compare early (1-4 h) versus late (8-12 h) patient-level reachability distributions."
    )
    parser.add_argument("--input-path", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--early-bins", nargs="+", default=list(EARLY_BINS))
    parser.add_argument("--late-bins", nargs="+", default=list(LATE_BINS))
    parser.add_argument("--metrics", nargs="+", default=list(ARTICLE_METRICS))
    args = parser.parse_args()
    return Config(
        input_path=args.input_path,
        output_dir=args.output_dir,
        early_bins=tuple(args.early_bins),
        late_bins=tuple(args.late_bins),
        metrics=tuple(args.metrics),
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_subject_window_values(config: Config) -> pd.DataFrame:
    frame = pd.read_csv(config.input_path, low_memory=False)
    frame = frame[
        (frame["analysis_type"] == config.analysis_type)
        & (frame["metric"].isin(config.metrics))
        & (frame["time_bin"].isin(set(config.early_bins).union(config.late_bins)))
    ].copy()
    frame["cpc_numeric"] = pd.to_numeric(frame["cpc"], errors="coerce")
    frame = frame[frame["cpc_numeric"].isin([1.0, 5.0])].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["value"].notna()].copy()
    frame["window"] = np.where(frame["time_bin"].isin(config.early_bins), "early", "late")
    aggregated = (
        frame.groupby(["subject", "outcome", "cpc_numeric", "metric", "window"], as_index=False)["value"]
        .median()
        .sort_values(["metric", "subject", "window"])
        .reset_index(drop=True)
    )
    return aggregated


def summarize_distribution(values: np.ndarray) -> dict[str, Any]:
    clean = np.asarray(values, dtype=float)
    clean = clean[np.isfinite(clean)]
    if clean.size == 0:
        return {
            "n": 0,
            "median": np.nan,
            "q25": np.nan,
            "q75": np.nan,
            "bic_gain_2_vs_1": np.nan,
            "component_separation_sigma": np.nan,
            "low_component_mean": np.nan,
            "high_component_mean": np.nan,
            "low_component_weight": np.nan,
            "high_component_weight": np.nan,
        }

    summary = {
        "n": int(clean.size),
        "median": float(np.median(clean)),
        "q25": float(np.quantile(clean, 0.25)),
        "q75": float(np.quantile(clean, 0.75)),
        "bic_gain_2_vs_1": np.nan,
        "component_separation_sigma": np.nan,
        "low_component_mean": np.nan,
        "high_component_mean": np.nan,
        "low_component_weight": np.nan,
        "high_component_weight": np.nan,
    }
    if clean.size < 20:
        return summary

    x = clean.reshape(-1, 1)
    model_1 = GaussianMixture(n_components=1, random_state=0).fit(x)
    model_2 = GaussianMixture(n_components=2, random_state=0, n_init=10).fit(x)
    means = model_2.means_.ravel()
    variances = model_2.covariances_.reshape(-1)
    weights = model_2.weights_.ravel()
    order = np.argsort(means)
    means = means[order]
    variances = variances[order]
    weights = weights[order]
    pooled_sigma = float(np.sqrt((variances[0] + variances[1]) / 2.0))
    separation = float(abs(means[1] - means[0]) / pooled_sigma) if pooled_sigma > 0 else np.nan
    summary.update(
        {
            "bic_gain_2_vs_1": float(model_1.bic(x) - model_2.bic(x)),
            "component_separation_sigma": separation,
            "low_component_mean": float(means[0]),
            "high_component_mean": float(means[1]),
            "low_component_weight": float(weights[0]),
            "high_component_weight": float(weights[1]),
        }
    )
    return summary


def build_distribution_summary(aggregated: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for metric in sorted(aggregated["metric"].unique()):
        metric_frame = aggregated[aggregated["metric"] == metric].copy()
        for window in ("early", "late"):
            window_frame = metric_frame[metric_frame["window"] == window].copy()
            for group_label, group_frame in (
                ("all", window_frame),
                ("CPC1", window_frame[window_frame["cpc_numeric"] == 1.0].copy()),
                ("CPC5", window_frame[window_frame["cpc_numeric"] == 5.0].copy()),
            ):
                row = {"metric": metric, "window": window, "group": group_label}
                row.update(summarize_distribution(group_frame["value"].to_numpy(dtype=float)))
                rows.append(row)
    return pd.DataFrame(rows)


def build_paired_window_frame(aggregated: pd.DataFrame) -> pd.DataFrame:
    paired = (
        aggregated.pivot_table(
            index=["subject", "outcome", "cpc_numeric", "metric"],
            columns="window",
            values="value",
            aggfunc="first",
        )
        .reset_index()
        .dropna(subset=["early", "late"])
        .reset_index(drop=True)
    )
    paired["delta_late_minus_early"] = paired["late"] - paired["early"]
    return paired


def build_shift_summary(paired: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for metric in sorted(paired["metric"].unique()):
        metric_frame = paired[paired["metric"] == metric].copy()
        for group_label, group_frame in (
            ("all", metric_frame),
            ("CPC1", metric_frame[metric_frame["cpc_numeric"] == 1.0].copy()),
            ("CPC5", metric_frame[metric_frame["cpc_numeric"] == 5.0].copy()),
        ):
            deltas = group_frame["delta_late_minus_early"].to_numpy(dtype=float)
            p_value = np.nan
            if len(group_frame) >= 10:
                try:
                    p_value = float(wilcoxon(group_frame["late"], group_frame["early"]).pvalue)
                except ValueError:
                    p_value = np.nan
            rows.append(
                {
                    "metric": metric,
                    "group": group_label,
                    "n_pairs": int(len(group_frame)),
                    "median_delta_late_minus_early": float(np.median(deltas)) if len(deltas) else np.nan,
                    "mean_delta_late_minus_early": float(np.mean(deltas)) if len(deltas) else np.nan,
                    "wilcoxon_p": p_value,
                }
            )
    return pd.DataFrame(rows)


def build_transition_summary(paired: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    subject_modes = paired.copy()
    subject_modes["early_mode"] = None
    subject_modes["late_mode"] = None
    subject_modes["component_low_mean"] = np.nan
    subject_modes["component_high_mean"] = np.nan

    for metric in sorted(paired["metric"].unique()):
        metric_mask = subject_modes["metric"] == metric
        metric_frame = subject_modes.loc[metric_mask].copy()
        stacked = np.concatenate(
            [
                metric_frame["early"].to_numpy(dtype=float),
                metric_frame["late"].to_numpy(dtype=float),
            ]
        ).reshape(-1, 1)
        model = GaussianMixture(n_components=2, random_state=0, n_init=10).fit(stacked)
        means = model.means_.ravel()
        order = np.argsort(means)
        low_component = int(order[0])
        high_component = int(order[1])
        early_comp = model.predict(metric_frame["early"].to_numpy(dtype=float).reshape(-1, 1))
        late_comp = model.predict(metric_frame["late"].to_numpy(dtype=float).reshape(-1, 1))
        subject_modes.loc[metric_mask, "early_mode"] = np.where(early_comp == low_component, "low", "high")
        subject_modes.loc[metric_mask, "late_mode"] = np.where(late_comp == low_component, "low", "high")
        subject_modes.loc[metric_mask, "component_low_mean"] = float(means[low_component])
        subject_modes.loc[metric_mask, "component_high_mean"] = float(means[high_component])

        updated = subject_modes.loc[metric_mask].copy()
        for group_label, group_frame in (
            ("all", updated),
            ("CPC1", updated[updated["cpc_numeric"] == 1.0].copy()),
            ("CPC5", updated[updated["cpc_numeric"] == 5.0].copy()),
        ):
            counts = group_frame.groupby(["early_mode", "late_mode"]).size().to_dict()
            n_pairs = int(len(group_frame))
            early_high_frac = float((group_frame["early_mode"] == "high").mean()) if n_pairs else np.nan
            late_high_frac = float((group_frame["late_mode"] == "high").mean()) if n_pairs else np.nan
            rows.append(
                {
                    "metric": metric,
                    "group": group_label,
                    "n_pairs": n_pairs,
                    "component_low_mean": float(means[low_component]),
                    "component_high_mean": float(means[high_component]),
                    "low_to_low": int(counts.get(("low", "low"), 0)),
                    "low_to_high": int(counts.get(("low", "high"), 0)),
                    "high_to_low": int(counts.get(("high", "low"), 0)),
                    "high_to_high": int(counts.get(("high", "high"), 0)),
                    "early_high_frac": early_high_frac,
                    "late_high_frac": late_high_frac,
                    "high_frac_delta_late_minus_early": late_high_frac - early_high_frac
                    if np.isfinite(early_high_frac) and np.isfinite(late_high_frac)
                    else np.nan,
                }
            )
    return pd.DataFrame(rows), subject_modes


def build_summary_markdown(
    config: Config,
    distribution_summary: pd.DataFrame,
    shift_summary: pd.DataFrame,
    transition_summary: pd.DataFrame,
) -> str:
    lines = [
        "# Early-versus-late distribution summary",
        "",
        "This summary compares patient-level median summaries over two time windows built from the latest pooled hourly reachability bundle.",
        "",
        "## Inputs",
        "",
        f"- input: `{config.input_path}`",
        f"- early bins: `{', '.join(config.early_bins)}`",
        f"- late bins: `{', '.join(config.late_bins)}`",
        f"- metrics: `{', '.join(config.metrics)}`",
        "",
        "## Reading guide",
        "",
        "- `bic_gain_2_vs_1 > 0` means the two-component Gaussian mixture fit outperformed a one-component fit by BIC.",
        "- `component_separation_sigma` is the distance between the two fitted component means in pooled-sigma units.",
        "- Transition rows track whether paired subjects stay in the low/high mode or switch between windows.",
        "",
        "## Metric notes",
        "",
    ]

    for metric in config.metrics:
        all_early = distribution_summary[
            (distribution_summary["metric"] == metric)
            & (distribution_summary["group"] == "all")
            & (distribution_summary["window"] == "early")
        ].iloc[0]
        all_late = distribution_summary[
            (distribution_summary["metric"] == metric)
            & (distribution_summary["group"] == "all")
            & (distribution_summary["window"] == "late")
        ].iloc[0]
        shift_all = shift_summary[
            (shift_summary["metric"] == metric) & (shift_summary["group"] == "all")
        ].iloc[0]
        trans_all = transition_summary[
            (transition_summary["metric"] == metric) & (transition_summary["group"] == "all")
        ].iloc[0]
        lines.extend(
            [
                f"### `{metric}`",
                "",
                f"- early BIC gain: `{all_early['bic_gain_2_vs_1']:.3f}`; late BIC gain: `{all_late['bic_gain_2_vs_1']:.3f}`",
                f"- early separation: `{all_early['component_separation_sigma']:.3f}` sigma; late separation: `{all_late['component_separation_sigma']:.3f}` sigma",
                f"- paired median late-minus-early shift: `{shift_all['median_delta_late_minus_early']:.6g}` (Wilcoxon `p={shift_all['wilcoxon_p']:.4g}`)",
                f"- transition counts: low->low `{int(trans_all['low_to_low'])}`, low->high `{int(trans_all['low_to_high'])}`, high->low `{int(trans_all['high_to_low'])}`, high->high `{int(trans_all['high_to_high'])}`",
                f"- high-mode fraction: early `{trans_all['early_high_frac']:.3f}` -> late `{trans_all['late_high_frac']:.3f}`",
                "",
            ]
        )

    return "\n".join(lines) + "\n"


def write_outputs(
    config: Config,
    subject_modes: pd.DataFrame,
    distribution_summary: pd.DataFrame,
    shift_summary: pd.DataFrame,
    transition_summary: pd.DataFrame,
) -> None:
    ensure_dir(config.output_dir)
    subject_modes.to_csv(config.output_dir / "subject_window_metrics.csv", index=False)
    distribution_summary.to_csv(config.output_dir / "distribution_summary.csv", index=False)
    shift_summary.to_csv(config.output_dir / "paired_shift_summary.csv", index=False)
    transition_summary.to_csv(config.output_dir / "transition_summary.csv", index=False)

    payload = {
        "config": {
            **asdict(config),
            "input_path": str(config.input_path),
            "output_dir": str(config.output_dir),
        },
        "distribution_summary": distribution_summary.to_dict(orient="records"),
        "paired_shift_summary": shift_summary.to_dict(orient="records"),
        "transition_summary": transition_summary.to_dict(orient="records"),
    }
    (config.output_dir / "window_distribution_summary.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    (config.output_dir / "window_distribution_summary.md").write_text(
        build_summary_markdown(config, distribution_summary, shift_summary, transition_summary),
        encoding="utf-8",
    )


def main() -> None:
    config = parse_args()
    aggregated = load_subject_window_values(config)
    distribution_summary = build_distribution_summary(aggregated)
    paired = build_paired_window_frame(aggregated)
    shift_summary = build_shift_summary(paired)
    transition_summary, subject_modes = build_transition_summary(paired)
    write_outputs(config, subject_modes, distribution_summary, shift_summary, transition_summary)
    print(f"Wrote early/late distribution outputs to {config.output_dir}")


if __name__ == "__main__":
    main()
