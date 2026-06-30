from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
import math
from pathlib import Path
import re
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd
from scipy import stats


DEFAULT_METRICS: tuple[str, ...] = (
    "m",
    "d",
    "e",
    "mnps_speed",
    "m_dot",
    "d_dot",
    "e_dot",
    "m_a",
    "m_e",
    "m_o",
    "d_n",
    "d_l",
    "d_s",
    "e_e",
    "e_s",
    "e_m",
)

DEFAULT_BASELINE_BIN = "pre_far"
DEFAULT_DELTA_BINS: tuple[str, ...] = ("pre_near", "event", "post_near", "post_far")


@dataclass(frozen=True)
class SpindleEventConfig:
    event_root: Path
    channel: str = "psg_c3"
    file_glob: str = "*event_locked_v1_{channel}.parquet"
    condition: str = "spindle_event"
    baseline_bin: str = DEFAULT_BASELINE_BIN
    delta_bins: tuple[str, ...] = DEFAULT_DELTA_BINS
    metrics: tuple[str, ...] = DEFAULT_METRICS
    min_subjects: int = 3


def _subject_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"sub-(\d+)", str(path))
    if not match:
        return (10**9, str(path))
    return (int(match.group(1)), str(path))


def discover_event_parquets(event_root: Path, channel: str, file_glob: str) -> List[Path]:
    pattern = file_glob.format(channel=channel)
    return sorted(Path(event_root).rglob(pattern), key=_subject_sort_key)


def _safe_float(value: object) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out if math.isfinite(out) else float("nan")


def _ensure_derived_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if {"m_dot", "d_dot", "e_dot"}.issubset(out.columns) and "mnps_speed" not in out.columns:
        dot = out[["m_dot", "d_dot", "e_dot"]].astype(float).to_numpy()
        out["mnps_speed"] = np.linalg.norm(dot, axis=1)
    if {"m", "d", "e"}.issubset(out.columns) and "mnps_norm" not in out.columns:
        coords = out[["m", "d", "e"]].astype(float).to_numpy()
        out["mnps_norm"] = np.linalg.norm(coords, axis=1)
    return out


def load_event_frames(paths: Sequence[Path], *, channel: str) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for path in paths:
        frame = pd.read_parquet(path)
        frame = _ensure_derived_metrics(frame)
        frame["event_parquet_path"] = str(path)
        frame["analysis_channel"] = str(channel).upper()
        frames.append(frame)
    return pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()


def _available_metrics(frame: pd.DataFrame, metrics: Iterable[str]) -> List[str]:
    return [metric for metric in metrics if metric in frame.columns and pd.api.types.is_numeric_dtype(frame[metric])]


def build_bin_descriptives(frame: pd.DataFrame, config: SpindleEventConfig) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    work = frame[frame["condition"].astype(str) == config.condition].copy()
    if work.empty:
        return pd.DataFrame()
    metrics = _available_metrics(work, config.metrics + ("mnps_norm",))
    group_cols = ["subject_id", "analysis_channel", "condition", "bin_label"]
    rows: List[Dict[str, object]] = []
    grouped = work.groupby(group_cols, dropna=False)
    for keys, group in grouped:
        row: Dict[str, object] = dict(zip(group_cols, keys))
        row["n_windows"] = int(len(group))
        row["n_events"] = int(group["event_id"].nunique()) if "event_id" in group.columns else np.nan
        row["n_finite_mnps"] = int(group["mnps_finite"].sum()) if "mnps_finite" in group.columns else np.nan
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce")
            row[f"{metric}_mean"] = float(values.mean())
            row[f"{metric}_median"] = float(values.median())
            row[f"{metric}_std"] = float(values.std(ddof=1))
        rows.append(row)
    return pd.DataFrame(rows)


def build_subject_deltas(
    descriptives: pd.DataFrame,
    config: SpindleEventConfig,
    *,
    statistic: str = "mean",
) -> pd.DataFrame:
    if descriptives.empty:
        return pd.DataFrame()
    id_cols = ["subject_id", "analysis_channel", "condition"]
    metric_cols = [
        col
        for col in descriptives.columns
        if col.endswith(f"_{statistic}") and col not in {"n_windows", "n_events"}
    ]
    rows: List[Dict[str, object]] = []
    for keys, subject_frame in descriptives.groupby(id_cols, dropna=False):
        by_bin = {str(row["bin_label"]): row for _, row in subject_frame.iterrows()}
        baseline = by_bin.get(config.baseline_bin)
        if baseline is None:
            continue
        for target_bin in config.delta_bins:
            target = by_bin.get(target_bin)
            if target is None:
                continue
            for col in metric_cols:
                metric = col[: -len(f"_{statistic}")]
                base_value = _safe_float(baseline.get(col))
                target_value = _safe_float(target.get(col))
                rows.append(
                    {
                        "subject_id": keys[0],
                        "analysis_channel": keys[1],
                        "condition": keys[2],
                        "baseline_bin": config.baseline_bin,
                        "target_bin": target_bin,
                        "contrast": f"{target_bin}_minus_{config.baseline_bin}",
                        "metric": metric,
                        "statistic": statistic,
                        "baseline_value": base_value,
                        "target_value": target_value,
                        "delta": target_value - base_value
                        if math.isfinite(base_value) and math.isfinite(target_value)
                        else float("nan"),
                        "baseline_n_windows": int(baseline.get("n_windows", 0)),
                        "target_n_windows": int(target.get("n_windows", 0)),
                        "baseline_n_events": int(baseline.get("n_events", 0)),
                        "target_n_events": int(target.get("n_events", 0)),
                    }
                )
    return pd.DataFrame(rows)


def paired_delta_tests(deltas: pd.DataFrame, *, min_subjects: int = 3) -> pd.DataFrame:
    if deltas.empty:
        return pd.DataFrame()
    rows: List[Dict[str, object]] = []
    group_cols = ["analysis_channel", "condition", "contrast", "metric", "statistic"]
    for keys, group in deltas.groupby(group_cols, dropna=False):
        vals = pd.to_numeric(group["delta"], errors="coerce").to_numpy(dtype=float)
        vals = vals[np.isfinite(vals)]
        n = int(vals.size)
        row: Dict[str, object] = dict(zip(group_cols, keys))
        row["n_subjects"] = n
        row["mean_delta"] = float(np.mean(vals)) if n else float("nan")
        row["median_delta"] = float(np.median(vals)) if n else float("nan")
        row["sd_delta"] = float(np.std(vals, ddof=1)) if n > 1 else float("nan")
        row["sem_delta"] = float(stats.sem(vals)) if n > 1 else float("nan")
        row["cohens_dz"] = (
            float(np.mean(vals) / np.std(vals, ddof=1))
            if n > 1 and np.std(vals, ddof=1) > 0
            else float("nan")
        )
        if n >= min_subjects:
            t_stat, p_value = stats.ttest_1samp(vals, popmean=0.0, nan_policy="omit")
            row["t"] = float(t_stat)
            row["p"] = float(p_value)
            try:
                w_stat, w_p = stats.wilcoxon(vals, zero_method="wilcox", alternative="two-sided")
                row["wilcoxon_w"] = float(w_stat)
                row["wilcoxon_p"] = float(w_p)
            except ValueError:
                row["wilcoxon_w"] = float("nan")
                row["wilcoxon_p"] = float("nan")
        else:
            row["t"] = float("nan")
            row["p"] = float("nan")
            row["wilcoxon_w"] = float("nan")
            row["wilcoxon_p"] = float("nan")
        rows.append(row)
    out = pd.DataFrame(rows)
    if not out.empty and "p" in out.columns:
        out["p_rank"] = out["p"].rank(method="first", na_option="bottom")
    return out


def run_spindle_event_locked(config: SpindleEventConfig) -> Dict[str, pd.DataFrame]:
    paths = discover_event_parquets(config.event_root, config.channel, config.file_glob)
    frame = load_event_frames(paths, channel=config.channel)
    descriptives = build_bin_descriptives(frame, config)
    deltas = build_subject_deltas(descriptives, config, statistic="mean")
    tests = paired_delta_tests(deltas, min_subjects=config.min_subjects)
    return {
        "event_windows": frame,
        "bin_descriptives": descriptives,
        "subject_deltas": deltas,
        "paired_tests": tests,
    }


def write_spindle_outputs(outputs: Dict[str, pd.DataFrame], out_dir: Path, *, channel: str) -> Dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: Dict[str, str] = {}
    for name, frame in outputs.items():
        if name == "event_windows":
            continue
        out = out_dir / f"spindle_event_locked_{channel}_{name}.csv"
        frame.to_csv(out, index=False)
        written[name] = str(out)
    return written


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run spindle event-locked baseline-delta analysis from event parquet exports."
    )
    parser.add_argument("--event-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--channel", default="psg_c3")
    parser.add_argument("--condition", default="spindle_event")
    parser.add_argument("--baseline-bin", default=DEFAULT_BASELINE_BIN)
    parser.add_argument("--min-subjects", type=int, default=3)
    args = parser.parse_args(argv)

    cfg = SpindleEventConfig(
        event_root=args.event_root,
        channel=args.channel,
        condition=args.condition,
        baseline_bin=args.baseline_bin,
        min_subjects=args.min_subjects,
    )
    outputs = run_spindle_event_locked(cfg)
    written = write_spindle_outputs(outputs, args.output_root, channel=args.channel)
    result = {
        "channel": args.channel,
        "condition": args.condition,
        "baseline_bin": args.baseline_bin,
        "n_event_windows": int(len(outputs["event_windows"])),
        "n_subject_delta_rows": int(len(outputs["subject_deltas"])),
        "written_files": written,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
