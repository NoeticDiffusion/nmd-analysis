from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd
from scipy import stats


CHANNEL_FILES: dict[str, str] = {
    "psg_c3": "baseline_corrected_all_psg_c3.csv",
    "psg_f3": "baseline_corrected_all_psg_f3.csv",
}

DEFAULT_METRICS: tuple[str, ...] = ("m", "d", "e")
DEFAULT_BINS: tuple[str, ...] = ("pre_far", "pre_near", "event", "post_near", "post_far")


@dataclass(frozen=True)
class CsvAnalysisConfig:
    input_root: Path
    output_dir: Path
    channels: tuple[str, ...] = ("psg_c3", "psg_f3")
    metrics: tuple[str, ...] = DEFAULT_METRICS
    event_bin: str = "event"
    primary_metric: str = "d"
    primary_channel: str = "psg_c3"
    bootstrap_samples: int = 10000
    bootstrap_seed: int = 20260509
    extreme_rate_quantile: float = 0.99


def _as_bool_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.lower().isin({"true", "1", "yes", "y"})


def load_channel_csv(input_root: Path, channel: str) -> pd.DataFrame:
    filename = CHANNEL_FILES.get(channel, f"baseline_corrected_all_{channel}.csv")
    path = Path(input_root) / filename
    frame = pd.read_csv(path)
    required = {
        "subject",
        "bin",
        "n",
        "qc_pass",
        "rate_per_min",
        "m_mean",
        "m_bc",
        "d_mean",
        "d_bc",
        "e_mean",
        "e_bc",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    frame = frame.copy()
    frame["channel"] = channel
    frame["qc_pass"] = _as_bool_series(frame["qc_pass"])
    return frame


def load_all_channels(config: CsvAnalysisConfig) -> pd.DataFrame:
    frames = [load_channel_csv(config.input_root, channel) for channel in config.channels]
    return pd.concat(frames, ignore_index=True, sort=False)


def _wide_by_subject(frame: pd.DataFrame, value_columns: Sequence[str]) -> pd.DataFrame:
    wide = frame.pivot_table(
        index=["channel", "subject"],
        columns="bin",
        values=list(value_columns),
        aggfunc="first",
    )
    wide.columns = [f"{value}_{bin_label}" for value, bin_label in wide.columns]
    return wide.reset_index()


def build_subject_deltas(frame: pd.DataFrame, metrics: Iterable[str]) -> pd.DataFrame:
    value_columns = []
    for metric in metrics:
        value_columns.extend([f"{metric}_mean", f"{metric}_bc"])
    wide = _wide_by_subject(frame, value_columns + ["qc_pass", "rate_per_min", "n"])
    rows: List[Dict[str, object]] = []
    baseline_bins = ("pre_far", "pre_near")
    target_bins = ("event", "post_near", "post_far")
    for _, row in wide.iterrows():
        for metric in metrics:
            for target_bin in target_bins:
                target_mean = row.get(f"{metric}_mean_{target_bin}")
                if pd.notna(target_mean):
                    for baseline_bin in baseline_bins:
                        baseline_mean = row.get(f"{metric}_mean_{baseline_bin}")
                        if pd.notna(baseline_mean):
                            rows.append(
                                {
                                    "channel": row["channel"],
                                    "subject": row["subject"],
                                    "metric": metric,
                                    "target_bin": target_bin,
                                    "baseline": baseline_bin,
                                    "contrast": f"{target_bin}_minus_{baseline_bin}",
                                    "delta": float(target_mean - baseline_mean),
                                    "target_mean": float(target_mean),
                                    "baseline_mean": float(baseline_mean),
                                    "target_n": row.get(f"n_{target_bin}"),
                                    "baseline_n": row.get(f"n_{baseline_bin}"),
                                    "target_qc_pass": bool(row.get(f"qc_pass_{target_bin}", False)),
                                    "baseline_qc_pass": bool(row.get(f"qc_pass_{baseline_bin}", False)),
                                    "rate_per_min": row.get(f"rate_per_min_{target_bin}"),
                                }
                            )
            # The CSV's *_bc columns are already baseline-corrected by the ingest export.
            bc_value = row.get(f"{metric}_bc_event")
            if pd.notna(bc_value):
                rows.append(
                    {
                        "channel": row["channel"],
                        "subject": row["subject"],
                        "metric": metric,
                        "target_bin": "event",
                        "baseline": "export_bc",
                        "contrast": "event_minus_export_baseline",
                        "delta": float(bc_value),
                        "target_mean": row.get(f"{metric}_mean_event"),
                        "baseline_mean": np.nan,
                        "target_n": row.get("n_event"),
                        "baseline_n": np.nan,
                        "target_qc_pass": bool(row.get("qc_pass_event", False)),
                        "baseline_qc_pass": True,
                        "rate_per_min": row.get("rate_per_min_event"),
                    }
                )
    return pd.DataFrame(rows)


def _bootstrap_median_ci(
    values: np.ndarray,
    *,
    samples: int,
    seed: int,
    ci: float = 0.95,
) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(samples, values.size), replace=True)
    medians = np.median(draws, axis=1)
    alpha = (1.0 - ci) / 2.0
    return (
        float(np.quantile(medians, alpha)),
        float(np.quantile(medians, 1.0 - alpha)),
    )


def sign_and_bootstrap_tests(deltas: pd.DataFrame, config: CsvAnalysisConfig) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    group_cols = ["channel", "metric", "contrast", "baseline"]
    for keys, group in deltas.groupby(group_cols, dropna=False):
        values = pd.to_numeric(group["delta"], errors="coerce").to_numpy(dtype=float)
        values = values[np.isfinite(values)]
        positive = int(np.sum(values > 0))
        negative = int(np.sum(values < 0))
        zero = int(np.sum(values == 0))
        nonzero_n = positive + negative
        p_two_sided = (
            float(stats.binomtest(positive, nonzero_n, 0.5, alternative="two-sided").pvalue)
            if nonzero_n > 0
            else float("nan")
        )
        ci_low, ci_high = _bootstrap_median_ci(
            values,
            samples=config.bootstrap_samples,
            seed=config.bootstrap_seed + len(rows),
        )
        row = dict(zip(group_cols, keys))
        row.update(
            {
                "n_subjects": int(values.size),
                "n_positive": positive,
                "n_negative": negative,
                "n_zero": zero,
                "median_delta": float(np.median(values)) if values.size else float("nan"),
                "mean_delta": float(np.mean(values)) if values.size else float("nan"),
                "sd_delta": float(np.std(values, ddof=1)) if values.size > 1 else float("nan"),
                "positive_fraction": float(positive / nonzero_n) if nonzero_n else float("nan"),
                "binom_p_two_sided": p_two_sided,
                "median_boot_ci_low": ci_low,
                "median_boot_ci_high": ci_high,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def channel_agreement(deltas: pd.DataFrame, *, metric: str, contrast: str) -> pd.DataFrame:
    event = deltas[(deltas["metric"] == metric) & (deltas["contrast"] == contrast)].copy()
    if event.empty:
        return pd.DataFrame()
    wide = event.pivot_table(index="subject", columns="channel", values="delta", aggfunc="first")
    if not {"psg_c3", "psg_f3"}.issubset(wide.columns):
        return pd.DataFrame()
    out = wide[["psg_c3", "psg_f3"]].dropna().copy()
    out["sign_c3"] = np.sign(out["psg_c3"])
    out["sign_f3"] = np.sign(out["psg_f3"])
    out["same_sign"] = out["sign_c3"] == out["sign_f3"]
    out["both_positive"] = (out["sign_c3"] > 0) & (out["sign_f3"] > 0)
    n = int(len(out))
    same = int(out["same_sign"].sum())
    both_positive = int(out["both_positive"].sum())
    return pd.DataFrame(
        [
            {
                "metric": metric,
                "contrast": contrast,
                "n_subjects": n,
                "same_sign": same,
                "same_sign_fraction": float(same / n) if n else float("nan"),
                "same_sign_binom_p_two_sided": float(
                    stats.binomtest(same, n, 0.5, alternative="two-sided").pvalue
                )
                if n
                else float("nan"),
                "both_positive": both_positive,
                "both_positive_fraction": float(both_positive / n) if n else float("nan"),
            }
        ]
    )


def baseline_robustness(summary: pd.DataFrame, *, metric: str) -> pd.DataFrame:
    keep = summary[
        (summary["metric"] == metric)
        & (summary["contrast"].isin(["event_minus_pre_far", "event_minus_pre_near", "event_minus_export_baseline"]))
    ].copy()
    return keep.sort_values(["channel", "contrast"]).reset_index(drop=True)


def correlation_checks(deltas: pd.DataFrame, *, metric: str, contrast: str) -> pd.DataFrame:
    event = deltas[(deltas["metric"] == metric) & (deltas["contrast"] == contrast)].copy()
    rows: List[Dict[str, object]] = []
    for channel, group in event.groupby("channel", dropna=False):
        for covariate in ["rate_per_min", "target_n"]:
            x = pd.to_numeric(group[covariate], errors="coerce").to_numpy(dtype=float)
            y = pd.to_numeric(group["delta"], errors="coerce").to_numpy(dtype=float)
            mask = np.isfinite(x) & np.isfinite(y)
            if int(mask.sum()) >= 3:
                rho, p_value = stats.spearmanr(x[mask], y[mask])
            else:
                rho, p_value = (float("nan"), float("nan"))
            rows.append(
                {
                    "channel": channel,
                    "metric": metric,
                    "contrast": contrast,
                    "covariate": covariate,
                    "n_subjects": int(mask.sum()),
                    "spearman_rho": float(rho),
                    "spearman_p": float(p_value),
                }
            )
    return pd.DataFrame(rows)


def event_profile_summary(frame: pd.DataFrame, config: CsvAnalysisConfig) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    bin_order = {label: idx for idx, label in enumerate(DEFAULT_BINS)}
    scenarios = {
        "all_subjects": frame,
        "qc_pass_only": frame[frame["qc_pass"]],
    }
    for scenario, scenario_frame in scenarios.items():
        for (channel, bin_label), group in scenario_frame.groupby(["channel", "bin"], dropna=False):
            for metric in config.metrics:
                for value_kind in ("mean", "bc"):
                    column = f"{metric}_{value_kind}"
                    values = pd.to_numeric(group[column], errors="coerce").dropna().to_numpy(dtype=float)
                    ci_low, ci_high = _bootstrap_median_ci(
                        values,
                        samples=config.bootstrap_samples,
                        seed=config.bootstrap_seed + len(rows) + 2000,
                    )
                    rows.append(
                        {
                            "scenario": scenario,
                            "channel": channel,
                            "bin": bin_label,
                            "bin_order": bin_order.get(str(bin_label), 999),
                            "metric": metric,
                            "value_kind": value_kind,
                            "n_subjects": int(values.size),
                            "mean": float(np.mean(values)) if values.size else float("nan"),
                            "median": float(np.median(values)) if values.size else float("nan"),
                            "sd": float(np.std(values, ddof=1)) if values.size > 1 else float("nan"),
                            "sem": float(stats.sem(values)) if values.size > 1 else float("nan"),
                            "median_boot_ci_low": ci_low,
                            "median_boot_ci_high": ci_high,
                        }
                    )
    return pd.DataFrame(rows).sort_values(
        ["scenario", "channel", "metric", "value_kind", "bin_order"]
    )


def channel_profile_difference(frame: pd.DataFrame, config: CsvAnalysisConfig) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for metric in config.metrics:
        for value_kind in ("mean", "bc"):
            column = f"{metric}_{value_kind}"
            wide = frame.pivot_table(
                index=["subject", "bin"],
                columns="channel",
                values=column,
                aggfunc="first",
            )
            if not {"psg_c3", "psg_f3"}.issubset(wide.columns):
                continue
            diff = (wide["psg_f3"] - wide["psg_c3"]).dropna()
            for bin_label, values in diff.groupby(level="bin"):
                arr = values.to_numpy(dtype=float)
                rows.append(
                    {
                        "metric": metric,
                        "value_kind": value_kind,
                        "bin": bin_label,
                        "n_subjects": int(arr.size),
                        "median_f3_minus_c3": float(np.median(arr)) if arr.size else float("nan"),
                        "mean_f3_minus_c3": float(np.mean(arr)) if arr.size else float("nan"),
                        "sd_f3_minus_c3": float(np.std(arr, ddof=1)) if arr.size > 1 else float("nan"),
                    }
                )
    return pd.DataFrame(rows)


def feasibility_report(config: CsvAnalysisConfig) -> Dict[str, object]:
    event_like = list(config.input_root.rglob("*event*")) + list(config.input_root.rglob("*spindle*"))
    parquet_files = list(config.input_root.rglob("*.parquet"))
    h5_files = list(config.input_root.rglob("*.h5"))
    return {
        "input_root": str(config.input_root),
        "n_h5_files": len(h5_files),
        "n_event_or_spindle_named_files": len(event_like),
        "n_parquet_files": len(parquet_files),
        "mnps_event_locked_from_csv": True,
        "mnj_event_locked_available": False,
        "reachability_event_locked_available": False,
        "reason": (
            "The available baseline_corrected_all_*.csv files contain subject/bin MNPS aggregates "
            "only. They do not contain window_id, window_start_sec, event_id, or event/control "
            "window mappings needed to join spindle bins to H5 Jacobian or reachability time series."
        ),
        "needed_for_mnj_reachability": [
            "window-level event_locked export with subject, channel, event_id, bin, window_start_sec or window_id",
            "matched-control event/window labels if matched-control baseline is required",
            "or an /events/spindles/... derived group inside each subject H5",
        ],
    }


def sensitivity_checks(deltas: pd.DataFrame, config: CsvAnalysisConfig) -> pd.DataFrame:
    event = deltas[
        (deltas["metric"] == config.primary_metric)
        & (deltas["contrast"] == "event_minus_export_baseline")
    ].copy()
    rows: List[Dict[str, object]] = []
    for channel, group in event.groupby("channel", dropna=False):
        scenarios = {
            "all_subjects": group,
            "qc_pass_only": group[group["target_qc_pass"]],
        }
        rate = pd.to_numeric(group["rate_per_min"], errors="coerce")
        if rate.notna().any():
            lo = float(rate.quantile(1.0 - config.extreme_rate_quantile))
            hi = float(rate.quantile(config.extreme_rate_quantile))
            scenarios["exclude_extreme_rate"] = group[(rate >= lo) & (rate <= hi)]
            scenarios["qc_pass_and_exclude_extreme_rate"] = group[
                group["target_qc_pass"] & (rate >= lo) & (rate <= hi)
            ]
        for scenario, sub in scenarios.items():
            values = pd.to_numeric(sub["delta"], errors="coerce").dropna().to_numpy(dtype=float)
            positive = int(np.sum(values > 0))
            negative = int(np.sum(values < 0))
            nonzero_n = positive + negative
            ci_low, ci_high = _bootstrap_median_ci(
                values,
                samples=config.bootstrap_samples,
                seed=config.bootstrap_seed + len(rows) + 1000,
            )
            rows.append(
                {
                    "channel": channel,
                    "scenario": scenario,
                    "metric": config.primary_metric,
                    "contrast": "event_minus_export_baseline",
                    "n_subjects": int(values.size),
                    "n_positive": positive,
                    "n_negative": negative,
                    "mean_delta": float(np.mean(values)) if values.size else float("nan"),
                    "sd_delta": float(np.std(values, ddof=1)) if values.size > 1 else float("nan"),
                    "median_delta": float(np.median(values)) if values.size else float("nan"),
                    "median_boot_ci_low": ci_low,
                    "median_boot_ci_high": ci_high,
                    "positive_fraction": float(positive / nonzero_n) if nonzero_n else float("nan"),
                    "binom_p_two_sided": float(
                        stats.binomtest(positive, nonzero_n, 0.5, alternative="two-sided").pvalue
                    )
                    if nonzero_n
                    else float("nan"),
                }
            )
    return pd.DataFrame(rows)


def build_claim_summary(
    summary: pd.DataFrame,
    agreement: pd.DataFrame,
    sensitivity: pd.DataFrame,
    config: CsvAnalysisConfig,
) -> Dict[str, object]:
    primary = summary[
        (summary["metric"] == config.primary_metric)
        & (summary["contrast"] == "event_minus_export_baseline")
    ].copy()
    payload: Dict[str, object] = {
        "primary_metric": config.primary_metric,
        "primary_contrast": "event_minus_export_baseline",
        "promoted_qc_pass_claim": {},
        "all_subject_audit": {},
    }
    for _, row in primary.iterrows():
        payload["all_subject_audit"][str(row["channel"])] = {
            "n_subjects": int(row["n_subjects"]),
            "n_positive": int(row["n_positive"]),
            "n_negative": int(row["n_negative"]),
            "median_delta": float(row["median_delta"]),
            "median_boot_ci_low": float(row["median_boot_ci_low"]),
            "median_boot_ci_high": float(row["median_boot_ci_high"]),
            "binom_p_two_sided": float(row["binom_p_two_sided"]),
        }
    qc = sensitivity[sensitivity["scenario"] == "qc_pass_only"].copy()
    for _, row in qc.iterrows():
        payload["promoted_qc_pass_claim"][str(row["channel"])] = {
            "n_subjects": int(row["n_subjects"]),
            "n_positive": int(row["n_positive"]),
            "n_negative": int(row["n_negative"]),
            "median_delta": float(row["median_delta"]),
            "median_boot_ci_low": float(row["median_boot_ci_low"]),
            "median_boot_ci_high": float(row["median_boot_ci_high"]),
            "binom_p_two_sided": float(row["binom_p_two_sided"]),
        }
    if not agreement.empty:
        payload["channel_agreement"] = agreement.iloc[0].to_dict()
    payload["notes"] = [
        "QC-pass rows are the promoted measurement-layer claim.",
        "F3 is a detector-source sensitivity analysis, not independent MNPS replication.",
        "Matched-control baseline is not present in baseline_corrected_all_*.csv and requires a window-level event/control export.",
    ]
    return payload


def run_analysis(config: CsvAnalysisConfig) -> Dict[str, object]:
    frame = load_all_channels(config)
    deltas = build_subject_deltas(frame, config.metrics)
    summary = sign_and_bootstrap_tests(deltas, config)
    profile = event_profile_summary(frame, config)
    channel_difference = channel_profile_difference(frame, config)
    agreement = channel_agreement(
        deltas,
        metric=config.primary_metric,
        contrast="event_minus_export_baseline",
    )
    robustness = baseline_robustness(summary, metric=config.primary_metric)
    correlations = correlation_checks(
        deltas,
        metric=config.primary_metric,
        contrast="event_minus_export_baseline",
    )
    sensitivity = sensitivity_checks(deltas, config)
    claim = build_claim_summary(summary, agreement, sensitivity, config)
    return {
        "input_rows": frame,
        "subject_deltas": deltas,
        "sign_bootstrap_summary": summary,
        "event_profile_summary": profile,
        "channel_profile_difference": channel_difference,
        "channel_agreement": agreement,
        "baseline_robustness": robustness,
        "correlations": correlations,
        "sensitivity": sensitivity,
        "claim_summary": claim,
        "event_locked_feasibility": feasibility_report(config),
    }


def write_outputs(outputs: Dict[str, object], output_dir: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: Dict[str, str] = {}
    for name, value in outputs.items():
        if isinstance(value, pd.DataFrame):
            path = output_dir / f"{name}.csv"
            value.to_csv(path, index=False)
            written[name] = str(path)
        elif isinstance(value, dict):
            path = output_dir / f"{name}.json"
            path.write_text(json.dumps(value, indent=2), encoding="utf-8")
            written[name] = str(path)
    return written


def write_figures(outputs: Dict[str, object], output_dir: Path) -> Dict[str, str]:
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    written: Dict[str, str] = {}
    profile = outputs["event_profile_summary"]
    if not isinstance(profile, pd.DataFrame) or profile.empty:
        return written

    bin_labels = list(DEFAULT_BINS)
    colors = {"psg_c3": "#1f77b4", "psg_f3": "#d62728"}
    labels = {"psg_c3": "PSG_C3", "psg_f3": "PSG_F3"}

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), sharex=True)
    for ax, metric in zip(axes, DEFAULT_METRICS):
        for channel in ("psg_c3", "psg_f3"):
            sub = profile[
                (profile["scenario"] == "all_subjects")
                & (profile["value_kind"] == "bc")
                & (profile["metric"] == metric)
                & (profile["channel"] == channel)
            ].sort_values("bin_order")
            x = [bin_labels.index(str(item)) for item in sub["bin"]]
            y = sub["median"].to_numpy(dtype=float)
            lo = sub["median_boot_ci_low"].to_numpy(dtype=float)
            hi = sub["median_boot_ci_high"].to_numpy(dtype=float)
            ax.plot(x, y, marker="o", color=colors[channel], label=labels[channel])
            ax.fill_between(x, lo, hi, color=colors[channel], alpha=0.16, linewidth=0)
        ax.axhline(0, color="#777777", linewidth=0.8, linestyle="--")
        ax.set_title(f"{metric}_bc")
        ax.set_xticks(range(len(bin_labels)))
        ax.set_xticklabels(bin_labels, rotation=35, ha="right")
        ax.set_ylabel("Baseline-corrected MNPS")
    axes[0].legend(frameon=False)
    fig.tight_layout()
    path = output_dir / "mnps_event_locked_profiles.svg"
    fig.savefig(path)
    plt.close(fig)
    written["mnps_event_locked_profiles"] = str(path)

    fig = plt.figure(figsize=(6.2, 5.2))
    ax = fig.add_subplot(111, projection="3d")
    for channel in ("psg_c3", "psg_f3"):
        coords = []
        for bin_label in bin_labels:
            values = []
            for metric in DEFAULT_METRICS:
                sub = profile[
                    (profile["scenario"] == "all_subjects")
                    & (profile["value_kind"] == "bc")
                    & (profile["metric"] == metric)
                    & (profile["channel"] == channel)
                    & (profile["bin"] == bin_label)
                ]
                values.append(float(sub["median"].iloc[0]) if not sub.empty else np.nan)
            coords.append(values)
        arr = np.asarray(coords, dtype=float)
        ax.plot(arr[:, 0], arr[:, 1], arr[:, 2], marker="o", color=colors[channel], label=labels[channel])
        for idx, bin_label in enumerate(bin_labels):
            ax.text(arr[idx, 0], arr[idx, 1], arr[idx, 2], bin_label, fontsize=8)
    ax.set_xlabel("m_bc")
    ax.set_ylabel("d_bc")
    ax.set_zlabel("e_bc")
    ax.set_title("Median Event-Locked MNPS Trajectory")
    ax.legend(frameon=False)
    fig.tight_layout()
    path = output_dir / "mnps_event_locked_3d_trajectory.svg"
    fig.savefig(path)
    plt.close(fig)
    written["mnps_event_locked_3d_trajectory"] = str(path)
    return written


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze ds005555 baseline-corrected spindle MNPS CSV exports."
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path(r"M:\datasets\processed\openneuro\ds005555"),
        help="Directory containing baseline_corrected_all_psg_c3/f3.csv.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "csv_analysis",
        help="Directory for analysis outputs.",
    )
    parser.add_argument("--bootstrap-samples", type=int, default=10000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260509)
    parser.add_argument("--extreme-rate-quantile", type=float, default=0.99)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    config = CsvAnalysisConfig(
        input_root=args.input_root,
        output_dir=args.output_dir,
        bootstrap_samples=args.bootstrap_samples,
        bootstrap_seed=args.bootstrap_seed,
        extreme_rate_quantile=args.extreme_rate_quantile,
    )
    outputs = run_analysis(config)
    written = write_outputs(outputs, config.output_dir)
    written.update(write_figures(outputs, config.output_dir))
    print(json.dumps({"output_dir": str(config.output_dir), "written": written}, indent=2))


if __name__ == "__main__":
    main()
