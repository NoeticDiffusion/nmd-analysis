from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import h5py
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
NDT_ANALYSIS_ROOT = REPO_ROOT / "ndt-analysis"
if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.h5_contract import DEFAULT_COORDINATE_CONTRACT, resolve_coords_3d  # noqa: E402


ARTICLE_DIR = Path(__file__).resolve().parents[1]
INPUT_ROOT = ARTICLE_DIR.parents[1] / "data" / "raw" / "neuralmanifolddynamics_ds005555_20260508_164627"
RESULT_DIR = ARTICLE_DIR / "results" / "temporal_nulls"
FIG_DIR = ARTICLE_DIR / "figures"
COORDINATE_CONTRACT = DEFAULT_COORDINATE_CONTRACT

CHANNELS = ("psg_c3", "psg_f3")
CHANNEL_LABELS = {"psg_c3": "PSG_C3", "psg_f3": "PSG_F3"}
CHANNEL_COLORS = {"psg_c3": "#1f77b4", "psg_f3": "#d62728"}
PRIMARY_METRICS = ("m", "d", "e")
SHIFT_SECONDS = (-300, -180, -120, 120, 180, 300)
N_PERMUTATIONS = 1000


@dataclass(frozen=True)
class SubjectPaths:
    subject_dir: Path
    h5_path: Path
    parquet_paths: Dict[str, Path]


def discover_subject_paths() -> List[SubjectPaths]:
    subjects: List[SubjectPaths] = []
    for subject_dir in sorted(INPUT_ROOT.glob("sub-*")):
        h5_paths = list(subject_dir.glob("*.h5"))
        if not h5_paths:
            continue
        parquet_paths = {
            channel: next(iter(subject_dir.glob(f"*event_locked_v1_{channel}.parquet")), None)
            for channel in CHANNELS
        }
        if all(path is not None for path in parquet_paths.values()):
            subjects.append(SubjectPaths(subject_dir, h5_paths[0], parquet_paths))  # type: ignore[arg-type]
    return subjects


def load_h5_arrays(path: Path) -> Dict[str, np.ndarray]:
    with h5py.File(path, "r") as handle:
        resolved = resolve_coords_3d(handle, COORDINATE_CONTRACT)
        if resolved is None:
            raise ValueError(f"No 3D coordinates available for coordinate_contract={COORDINATE_CONTRACT!r} in {path}")
        mnps = np.asarray(resolved.values, dtype=float)
        stage = np.asarray(handle["labels/stage"], dtype=int)
    return {
        "stage": stage,
        "m": mnps[:, 0],
        "d": mnps[:, 1],
        "e": mnps[:, 2],
    }


def safe_take(values: np.ndarray, idx: np.ndarray) -> np.ndarray:
    valid = (idx >= 0) & (idx < len(values))
    out = np.full(idx.shape, np.nan, dtype=float)
    out[valid] = values[idx[valid]]
    return out


def n2_fraction(stage: np.ndarray, idx: np.ndarray) -> float:
    valid = (idx >= 0) & (idx < len(stage))
    if not np.any(valid):
        return float("nan")
    return float(np.mean(stage[idx[valid]] == 2))


def summarize_values(values: Iterable[float]) -> Dict[str, float]:
    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {
            "n_subjects": 0,
            "n_positive": 0,
            "mean_delta": np.nan,
            "median_delta": np.nan,
            "cohens_dz": np.nan,
            "p": np.nan,
            "binom_p": np.nan,
        }
    positive = int(np.sum(arr > 0))
    negative = int(np.sum(arr < 0))
    nonzero = positive + negative
    sd = float(np.std(arr, ddof=1)) if arr.size > 1 else np.nan
    t_stat, p_value = stats.ttest_1samp(arr, 0.0, nan_policy="omit") if arr.size > 1 else (np.nan, np.nan)
    return {
        "n_subjects": int(arr.size),
        "n_positive": positive,
        "mean_delta": float(np.mean(arr)),
        "median_delta": float(np.median(arr)),
        "cohens_dz": float(np.mean(arr) / sd) if np.isfinite(sd) and sd > 0 else np.nan,
        "p": float(p_value),
        "binom_p": float(stats.binomtest(positive, nonzero, 0.5).pvalue) if nonzero else np.nan,
    }


def build_time_shift_subject_rows(subject: SubjectPaths) -> List[Dict[str, object]]:
    arrays = load_h5_arrays(subject.h5_path)
    rows: List[Dict[str, object]] = []
    for channel, parquet_path in subject.parquet_paths.items():
        frame = pd.read_parquet(
            parquet_path,
            columns=["subject_id", "condition", "event_id", "bin_label", "window_id"],
        )
        event_frame = frame[(frame["condition"] == "spindle_event") & frame["bin_label"].isin(["event", "pre_far"])]
        if event_frame.empty:
            continue
        subject_id = str(event_frame["subject_id"].iloc[0])
        true_event_windows = set(
            pd.to_numeric(
                event_frame.loc[event_frame["bin_label"] == "event", "window_id"],
                errors="coerce",
            )
            .dropna()
            .astype(int)
            .tolist()
        )
        by_event = {
            (int(event_id), str(bin_label)): group["window_id"].to_numpy(dtype=int)
            for (event_id, bin_label), group in event_frame.groupby(["event_id", "bin_label"], sort=False)
        }
        event_ids = sorted({key[0] for key in by_event if (key[0], "event") in by_event and (key[0], "pre_far") in by_event})
        for shift_sec in SHIFT_SECONDS:
            shift_windows = int(round(shift_sec / 2.0))
            shifted_event_indices: List[np.ndarray] = []
            shifted_pre_far_indices: List[np.ndarray] = []
            excluded_overlap = 0
            for event_id in event_ids:
                event_idx = by_event[(event_id, "event")] + shift_windows
                pre_far_idx = by_event[(event_id, "pre_far")] + shift_windows
                if any(int(idx) in true_event_windows for idx in event_idx):
                    excluded_overlap += 1
                    continue
                if n2_fraction(arrays["stage"], event_idx) < 0.8 or n2_fraction(arrays["stage"], pre_far_idx) < 0.8:
                    continue
                shifted_event_indices.append(event_idx)
                shifted_pre_far_indices.append(pre_far_idx)
            if not shifted_event_indices or not shifted_pre_far_indices:
                continue
            event_idx_all = np.concatenate(shifted_event_indices)
            pre_far_idx_all = np.concatenate(shifted_pre_far_indices)
            row: Dict[str, object] = {
                "subject": subject_id,
                "channel": channel,
                "shift_sec": shift_sec,
                "n_events_used": len(shifted_event_indices),
                "n_events_excluded_overlap": excluded_overlap,
            }
            for metric in PRIMARY_METRICS:
                event_values = safe_take(arrays[metric], event_idx_all)
                pre_values = safe_take(arrays[metric], pre_far_idx_all)
                row[f"{metric}_pseudo_event_minus_prefar"] = float(np.nanmean(event_values) - np.nanmean(pre_values))
            rows.append(row)
    return rows


def build_observed_and_label_data(subject: SubjectPaths) -> tuple[List[Dict[str, object]], Dict[str, Dict[str, List[tuple[np.ndarray, np.ndarray]]]]]:
    rows: List[Dict[str, object]] = []
    label_data: Dict[str, Dict[str, List[tuple[np.ndarray, np.ndarray]]]] = {
        channel: {metric: [] for metric in PRIMARY_METRICS} for channel in CHANNELS
    }
    for channel, parquet_path in subject.parquet_paths.items():
        columns = ["subject_id", "condition", "bin_label", *PRIMARY_METRICS]
        frame = pd.read_parquet(parquet_path, columns=columns)
        event = frame[(frame["condition"] == "spindle_event") & (frame["bin_label"] == "event")]
        control = frame[(frame["condition"] == "matched_control") & (frame["bin_label"] == "control")]
        if event.empty or control.empty:
            continue
        subject_id = str(frame["subject_id"].iloc[0])
        row: Dict[str, object] = {"subject": subject_id, "channel": channel}
        for metric in PRIMARY_METRICS:
            event_values = pd.to_numeric(event[metric], errors="coerce").dropna().to_numpy(dtype=float)
            control_values = pd.to_numeric(control[metric], errors="coerce").dropna().to_numpy(dtype=float)
            if event_values.size == 0 or control_values.size == 0:
                continue
            row[f"{metric}_event_minus_control"] = float(np.mean(event_values) - np.mean(control_values))
            label_data[channel][metric].append((event_values, control_values))
        rows.append(row)
    return rows, label_data


def summarize_time_shift(rows: pd.DataFrame) -> pd.DataFrame:
    out: List[Dict[str, object]] = []
    for channel in CHANNELS:
        for shift_sec in SHIFT_SECONDS:
            sub = rows[(rows["channel"] == channel) & (rows["shift_sec"] == shift_sec)]
            for metric in PRIMARY_METRICS:
                col = f"{metric}_pseudo_event_minus_prefar"
                summary = summarize_values(pd.to_numeric(sub[col], errors="coerce").dropna().to_numpy())
                out.append({"channel": channel, "shift_sec": shift_sec, "metric": metric, **summary})
    return pd.DataFrame(out)


def run_label_permutations(
    observed: pd.DataFrame,
    label_data: Dict[str, Dict[str, List[tuple[np.ndarray, np.ndarray]]]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(20260509)
    summary_rows: List[Dict[str, object]] = []
    null_rows: List[Dict[str, object]] = []
    for channel in CHANNELS:
        observed_channel = observed[observed["channel"] == channel]
        for metric in PRIMARY_METRICS:
            observed_values = pd.to_numeric(observed_channel[f"{metric}_event_minus_control"], errors="coerce").dropna().to_numpy()
            if observed_values.size == 0:
                continue
            observed_median = float(np.median(observed_values))
            null_medians = np.empty(N_PERMUTATIONS, dtype=float)
            for perm_idx in range(N_PERMUTATIONS):
                subject_deltas = []
                for event_values, control_values in label_data[channel][metric]:
                    combined = np.concatenate([event_values, control_values])
                    n_event = event_values.size
                    chosen = rng.choice(combined.size, size=n_event, replace=False)
                    mask = np.zeros(combined.size, dtype=bool)
                    mask[chosen] = True
                    subject_deltas.append(float(np.mean(combined[mask]) - np.mean(combined[~mask])))
                null_medians[perm_idx] = np.median(subject_deltas)
            p_emp = (1.0 + float(np.sum(np.abs(null_medians) >= abs(observed_median)))) / (N_PERMUTATIONS + 1.0)
            summary_rows.append(
                {
                    "channel": channel,
                    "metric": metric,
                    "n_subjects": int(observed_values.size),
                    "observed_median": observed_median,
                    "observed_mean": float(np.mean(observed_values)),
                    "null_median_mean": float(np.mean(null_medians)),
                    "null_median_p025": float(np.quantile(null_medians, 0.025)),
                    "null_median_p975": float(np.quantile(null_medians, 0.975)),
                    "empirical_p_two_sided": p_emp,
                    "n_permutations": N_PERMUTATIONS,
                }
            )
            null_rows.extend(
                {
                    "channel": channel,
                    "metric": metric,
                    "permutation": int(idx),
                    "null_median": float(value),
                }
                for idx, value in enumerate(null_medians)
            )
    return pd.DataFrame(summary_rows), pd.DataFrame(null_rows)


def write_figures(time_summary: pd.DataFrame, permutation_summary: pd.DataFrame, permutation_nulls: pd.DataFrame) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(10.0, 3.8), sharey=True)
    for ax, channel in zip(axes, CHANNELS):
        sub = time_summary[(time_summary["channel"] == channel) & (time_summary["metric"] == "d")]
        ax.axhline(0, color="#777777", linewidth=0.9, linestyle="--")
        ax.plot(sub["shift_sec"], sub["median_delta"], marker="o", color=CHANNEL_COLORS[channel])
        ax.set_title(CHANNEL_LABELS[channel])
        ax.set_xlabel("Pseudo-event shift (s)")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Median pseudo-event minus pre_far MNPS-d")
    fig.suptitle("Time-shifted pseudo-event nulls")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_temporal_null_shifted_events.svg", format="svg", bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10.0, 3.8), sharey=True)
    for ax, channel in zip(axes, CHANNELS):
        nulls = permutation_nulls[(permutation_nulls["channel"] == channel) & (permutation_nulls["metric"] == "d")]
        summary = permutation_summary[(permutation_summary["channel"] == channel) & (permutation_summary["metric"] == "d")].iloc[0]
        ax.hist(nulls["null_median"], bins=40, color="#dddddd", edgecolor="#ffffff")
        ax.axvline(summary["observed_median"], color=CHANNEL_COLORS[channel], linewidth=2.0, label="observed")
        ax.axvline(0, color="#777777", linewidth=0.9, linestyle="--")
        ax.set_title(CHANNEL_LABELS[channel])
        ax.set_xlabel("Permuted median event-control MNPS-d")
        ax.legend(frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Permutation count")
    fig.suptitle("Label-permutation nulls for matched-control contrast")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_temporal_null_label_permutation.svg", format="svg", bbox_inches="tight")
    plt.close(fig)


def write_markdown(time_summary: pd.DataFrame, permutation_summary: pd.DataFrame) -> None:
    d_time = time_summary[time_summary["metric"] == "d"].copy()
    d_perm = permutation_summary[permutation_summary["metric"] == "d"].copy()
    lines = [
        "# Temporal Null Analysis Summary",
        "",
        "This analysis adds two null checks to the ds005555 spindle-event result.",
        "",
        "1. Time-shifted pseudo-events: true event and pre_far window IDs were shifted by +/-120, +/-180, and +/-300 s, restricted to N2 windows, and compared as pseudo-event minus pseudo-pre_far.",
        "2. Label permutation: event and matched-control row labels were permuted within subject/channel while preserving event counts; the null statistic was the across-subject median event-control delta.",
        "",
        "## Time-Shifted Pseudo-Events: MNPS-d",
        "",
        "| Channel | Shift (s) | Subjects | Positive | Median delta | dz | Sign-test p |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in d_time.iterrows():
        lines.append(
            f"| {CHANNEL_LABELS[row['channel']]} | {int(row['shift_sec'])} | {int(row['n_subjects'])} | "
            f"{int(row['n_positive'])}/{int(row['n_subjects'])} | {row['median_delta']:+.4f} | "
            f"{row['cohens_dz']:.3f} | {row['binom_p']:.3g} |"
        )
    lines.extend(
        [
            "",
            "## Label-Permutation Null: MNPS-d",
            "",
            "| Channel | Observed median | Null 95% interval | Empirical p | Permutations |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for _, row in d_perm.iterrows():
        lines.append(
            f"| {CHANNEL_LABELS[row['channel']]} | {row['observed_median']:+.4f} | "
            f"[{row['null_median_p025']:+.4f}, {row['null_median_p975']:+.4f}] | "
            f"{row['empirical_p_two_sided']:.4g} | {int(row['n_permutations'])} |"
        )
    (RESULT_DIR / "temporal_null_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    subject_paths = discover_subject_paths()
    time_rows: List[Dict[str, object]] = []
    observed_rows: List[Dict[str, object]] = []
    label_data: Dict[str, Dict[str, List[tuple[np.ndarray, np.ndarray]]]] = {
        channel: {metric: [] for metric in PRIMARY_METRICS} for channel in CHANNELS
    }

    for subject in subject_paths:
        time_rows.extend(build_time_shift_subject_rows(subject))
        obs, subject_label_data = build_observed_and_label_data(subject)
        observed_rows.extend(obs)
        for channel in CHANNELS:
            for metric in PRIMARY_METRICS:
                label_data[channel][metric].extend(subject_label_data[channel][metric])

    time_subjects = pd.DataFrame(time_rows)
    observed = pd.DataFrame(observed_rows)
    time_summary = summarize_time_shift(time_subjects)
    permutation_summary, permutation_nulls = run_label_permutations(observed, label_data)

    time_subjects.to_csv(RESULT_DIR / "time_shift_subject_deltas.csv", index=False)
    time_summary.to_csv(RESULT_DIR / "time_shift_summary.csv", index=False)
    observed.to_csv(RESULT_DIR / "observed_event_control_subject_deltas.csv", index=False)
    permutation_summary.to_csv(RESULT_DIR / "label_permutation_summary.csv", index=False)
    permutation_nulls.to_csv(RESULT_DIR / "label_permutation_null_medians.csv", index=False)
    write_figures(time_summary, permutation_summary, permutation_nulls)
    write_markdown(time_summary, permutation_summary)

    payload = {
        "n_subject_runs": len(subject_paths),
        "shift_seconds": list(SHIFT_SECONDS),
        "n_permutations": N_PERMUTATIONS,
        "primary_time_shift_d": time_summary[time_summary["metric"] == "d"].to_dict(orient="records"),
        "primary_label_permutation_d": permutation_summary[permutation_summary["metric"] == "d"].to_dict(orient="records"),
    }
    (RESULT_DIR / "temporal_null_claim_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote temporal null outputs to {RESULT_DIR}")


if __name__ == "__main__":
    main()
