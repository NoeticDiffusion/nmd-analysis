"""Shared helpers for the I-CARE v2 CPC1 vs CPC5 article pipeline."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import numpy as np
import pandas as pd
import yaml
from scipy.stats import f_oneway as stats_f_oneway

ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
NMD_ANALYSIS_ROOT = REPO_ROOT / "nmd-analysis"
DEFAULT_CONFIG_PATH = ARTICLE_DIR / "config" / "icare_v2_analysis_config.yaml"
DEFAULT_SMOKE_CONFIG_PATH = ARTICLE_DIR / "config" / "icare_v2_smoke_subjects.yaml"

RUN_ID_RE = re.compile(
    r"^sub-(?P<subject>\d+)_post_cardiac_arrest_coma_continuous_eeg_"
    r"run-(?P<run>\d+)_acq-(?P<acq>\d+)$"
)

PRIMARY_12H_BINS: tuple[tuple[float, float, str], ...] = (
    (0.0, 12.0, "0_12h"),
    (12.0, 24.0, "12_24h"),
    (24.0, 48.0, "24_48h"),
    (48.0, 72.0, "48_72h"),
    (72.0, float("inf"), "72h_plus"),
)
HOURLY_12H_BINS: tuple[tuple[float, float, str], ...] = tuple(
    (float(hour), float(hour + 1), f"{hour}_{hour + 1}h") for hour in range(12)
) + (
    (12.0, 24.0, "12_24h"),
    (24.0, 48.0, "24_48h"),
    (48.0, 72.0, "48_72h"),
    (72.0, float("inf"), "72h_plus"),
)
TIME_BIN_SCHEMES = {
    "primary_12h": PRIMARY_12H_BINS,
    "hourly_12h": HOURLY_12H_BINS,
}


def ensure_nmd_analysis_on_path() -> Path:
    root = str(NMD_ANALYSIS_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    return NMD_ANALYSIS_ROOT


ensure_nmd_analysis_on_path()


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def normalize_subject_id(value: Any) -> str:
    text = str(value).strip()
    if text.startswith("sub-"):
        return text
    digits = re.sub(r"\D", "", text)
    if digits:
        return f"sub-{int(digits):04d}"
    return text


def parse_run_stem(stem: str) -> dict[str, Any]:
    match = RUN_ID_RE.match(stem)
    if match is None:
        return {"subject_id": None, "run": None, "acq": None, "stem": stem}
    return {
        "subject_id": f"sub-{int(match.group('subject')):04d}",
        "run": int(match.group("run")),
        "acq": int(match.group("acq")),
        "stem": stem,
    }


def as_scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        return bytes(value).decode("utf-8", errors="replace")
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lower() in {"nan", "none", ""}:
            return None
        return stripped
    if value is None:
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def parse_jsonish(value: Any) -> Any:
    value = as_scalar(value)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") or text.startswith("["):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return value
    return value


def finite_array(values: Any) -> np.ndarray:
    arr = np.asarray(values, dtype=float).reshape(-1)
    return arr[np.isfinite(arr)]


def median_finite(values: Any) -> float:
    arr = finite_array(values)
    return float(np.median(arr)) if arr.size else float("nan")


def mean_finite(values: Any) -> float:
    arr = finite_array(values)
    return float(np.mean(arr)) if arr.size else float("nan")


def fraction_true(mask: Any) -> float:
    arr = np.asarray(mask, dtype=bool).reshape(-1)
    return float(arr.mean()) if arr.size else float("nan")


def assign_time_bin(hours: float, scheme: str) -> str:
    if hours is None or not np.isfinite(hours):
        return "unassigned"
    bins = TIME_BIN_SCHEMES[scheme]
    for lo, hi, label in bins:
        if lo <= float(hours) < hi:
            return label
    return "unassigned"


def discover_h5_files(
    raw_root: Path,
    *,
    subject_allowlist: Sequence[str] | None = None,
    limit_h5: int | None = None,
) -> list[Path]:
    allow = {normalize_subject_id(item) for item in subject_allowlist} if subject_allowlist else None
    paths = sorted(raw_root.glob("sub-*/*.h5"))
    if allow is not None:
        filtered: list[Path] = []
        for path in paths:
            parsed = parse_run_stem(path.stem)
            if parsed["subject_id"] in allow:
                filtered.append(path)
        paths = filtered
    if limit_h5 is not None:
        paths = paths[: int(limit_h5)]
    return paths


def empty_run_directories(raw_root: Path, *, subject_allowlist: Sequence[str] | None = None) -> list[Path]:
    allow = {normalize_subject_id(item) for item in subject_allowlist} if subject_allowlist else None
    empty: list[Path] = []
    for directory in sorted(p for p in raw_root.glob("sub-*") if p.is_dir()):
        parsed = parse_run_stem(directory.name)
        if allow is not None and parsed["subject_id"] not in allow:
            continue
        if not any(directory.glob("*.h5")):
            empty.append(directory)
    return empty


def bh_fdr(p_values: Sequence[float]) -> np.ndarray:
    p = np.asarray(p_values, dtype=float)
    q = np.full(p.shape, np.nan, dtype=float)
    valid = np.isfinite(p)
    if not valid.any():
        return q
    work = p[valid]
    order = np.argsort(work)
    ranks = np.arange(1, work.size + 1, dtype=float)
    raw = (work[order] * work.size) / ranks
    adjusted = np.minimum.accumulate(raw[::-1])[::-1]
    q_valid = np.empty_like(work)
    q_valid[order] = np.clip(adjusted, 0.0, 1.0)
    q[valid] = q_valid
    return q


def cliffs_delta(good: np.ndarray, poor: np.ndarray) -> float:
    good = finite_array(good)
    poor = finite_array(poor)
    if good.size == 0 or poor.size == 0:
        return float("nan")
    diff = np.subtract.outer(good, poor)
    return float((np.sum(diff > 0) - np.sum(diff < 0)) / diff.size)


def cohens_d(good: np.ndarray, poor: np.ndarray) -> float:
    good = finite_array(good)
    poor = finite_array(poor)
    if good.size < 2 or poor.size < 2:
        return float("nan")
    pooled = ((good.size - 1) * np.var(good, ddof=1) + (poor.size - 1) * np.var(poor, ddof=1)) / (
        good.size + poor.size - 2
    )
    if pooled <= 0 or not np.isfinite(pooled):
        return float("nan")
    return float((np.mean(good) - np.mean(poor)) / np.sqrt(pooled))


def bootstrap_two_sample_ci(
    good: np.ndarray,
    poor: np.ndarray,
    stat_fn: Callable[[np.ndarray, np.ndarray], float],
    *,
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 20260912,
) -> tuple[float, float, int]:
    """Percentile bootstrap CI for a two-sample statistic (e.g. cohens_d, cliffs_delta).

    Resamples each arm independently with replacement, n_boot times. Returns
    (ci_lo, ci_hi, n_boot_used). Deterministic given `seed` so results are
    reproducible across reruns. Returns (nan, nan, 0) if either arm has < 2
    finite values.
    """
    good = finite_array(good)
    poor = finite_array(poor)
    if good.size < 2 or poor.size < 2:
        return float("nan"), float("nan"), 0
    rng = np.random.default_rng(seed)
    stats_boot = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        g_sample = good[rng.integers(0, good.size, size=good.size)]
        p_sample = poor[rng.integers(0, poor.size, size=poor.size)]
        stats_boot[b] = stat_fn(g_sample, p_sample)
    stats_boot = stats_boot[np.isfinite(stats_boot)]
    if stats_boot.size < max(50, int(0.5 * n_boot)):
        return float("nan"), float("nan"), int(stats_boot.size)
    lo = float(np.percentile(stats_boot, 100 * (alpha / 2)))
    hi = float(np.percentile(stats_boot, 100 * (1 - alpha / 2)))
    return lo, hi, int(stats_boot.size)


def eta_squared_oneway(values: np.ndarray, groups: Sequence[Any]) -> dict[str, Any]:
    """One-way eta^2 (proportion of variance explained) of `groups` on `values`.

    Used as a post-hoc residual-batch-effect diagnostic (e.g. hospital) on
    already-harmonized derived metrics. Groups with <2 finite observations
    are dropped. Returns eta_squared=nan if fewer than 2 usable groups.
    """
    values = np.asarray(values, dtype=float).reshape(-1)
    groups = np.asarray(groups).reshape(-1)
    mask = np.isfinite(values) & (groups != None) & (groups.astype(str) != "nan")  # noqa: E711
    values = values[mask]
    groups = groups[mask]
    if values.size < 4:
        return {"eta_squared": float("nan"), "n_groups": 0, "n_total": int(values.size), "f_stat": float("nan"), "p_value": float("nan")}
    uniq = pd.unique(groups)
    samples = [values[groups == g] for g in uniq if (groups == g).sum() >= 2]
    if len(samples) < 2:
        return {"eta_squared": float("nan"), "n_groups": len(samples), "n_total": int(values.size), "f_stat": float("nan"), "p_value": float("nan")}
    grand_mean = float(np.mean(values))
    ss_total = float(np.sum((values - grand_mean) ** 2))
    ss_between = float(sum(s.size * (np.mean(s) - grand_mean) ** 2 for s in samples))
    eta2 = float(ss_between / ss_total) if ss_total > 0 else float("nan")
    f_stat = p_value = float("nan")
    try:
        f_res = stats_f_oneway(*samples)
        f_stat = float(f_res.statistic)
        p_value = float(f_res.pvalue)
    except Exception:  # noqa: BLE001
        pass
    return {
        "eta_squared": eta2,
        "n_groups": len(samples),
        "n_total": int(sum(s.size for s in samples)),
        "f_stat": f_stat,
        "p_value": p_value,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def parallel_map(
    fn: Callable[[Any], Any],
    items: Sequence[Any],
    *,
    workers: int = 1,
    desc: str = "items",
) -> list[Any]:
    if not items:
        return []
    n_workers = max(1, int(workers))
    results: list[Any] = [None] * len(items)
    if n_workers == 1:
        for i, item in enumerate(items):
            results[i] = fn(item)
            if (i + 1) % 25 == 0 or i + 1 == len(items):
                print(f"{desc}: {i + 1}/{len(items)}", flush=True)
        return results
    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = {pool.submit(fn, item): i for i, item in enumerate(items)}
        done = 0
        for future in as_completed(futures):
            idx = futures[future]
            results[idx] = future.result()
            done += 1
            if done % 25 == 0 or done == len(items):
                print(f"{desc}: {done}/{len(items)}", flush=True)
    return results


@dataclass(frozen=True)
class PipelineConfig:
    bundle_id: str
    dataset_id: str
    confirmatory_status: str
    coordinate_contract: str
    raw_root: Path
    output_dir: Path
    good_cpc: int
    poor_cpc: int
    good_label: str
    poor_label: str
    primary_scheme: str
    hourly_scheme: str
    primary_window: str
    reachability: dict[str, Any]
    diffusion_eps: float
    bh_alpha: float
    min_group_n: int
    min_testable_group_n: int
    smoke: bool
    subject_allowlist: tuple[str, ...] | None
    workers: int
    limit_h5: int | None


def add_common_args(parser: argparse.ArgumentParser, *, default_output_name: str | None = None) -> None:
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--smoke-config", type=Path, default=DEFAULT_SMOKE_CONFIG_PATH)
    parser.add_argument("--smoke", action="store_true", help="Restrict to the smoke-subject allowlist.")
    parser.add_argument("--subject-allowlist", nargs="*", default=None)
    parser.add_argument("--subject-limit", type=int, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--input-dir", type=Path, default=None)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--limit-h5", type=int, default=None)
    parser.add_argument("--default-output-name", type=str, default=default_output_name, help=argparse.SUPPRESS)


def resolve_pipeline_config(args: argparse.Namespace) -> PipelineConfig:
    raw = load_yaml(args.config)
    smoke = bool(getattr(args, "smoke", False))
    allowlist: list[str] | None = None
    if args.subject_allowlist:
        allowlist = [normalize_subject_id(item) for item in args.subject_allowlist]
    elif smoke:
        smoke_cfg = load_yaml(args.smoke_config)
        allowlist = [
            normalize_subject_id(item)
            for item in list(smoke_cfg.get("subjects", {}).get("cpc1", []))
            + list(smoke_cfg.get("subjects", {}).get("cpc5", []))
        ]
    if args.subject_limit is not None and allowlist is not None:
        allowlist = allowlist[: int(args.subject_limit)]
    elif args.subject_limit is not None:
        allowlist = None
    paths = raw.get("paths", {})
    output_root = Path(paths.get("smoke_output_root") if smoke else paths.get("output_root"))
    output_dir = Path(args.output_dir) if args.output_dir else output_root
    cohort = raw.get("cohort", {})
    timing = raw.get("timing", {})
    stats = raw.get("statistics", {})
    return PipelineConfig(
        bundle_id=str(raw.get("bundle_id")),
        dataset_id=str(raw.get("dataset_id")),
        confirmatory_status=str(raw.get("confirmatory_status")),
        coordinate_contract=str(raw.get("coordinate_contract", "subject_anchored")),
        raw_root=Path(paths["raw_root"]),
        output_dir=output_dir,
        good_cpc=int(cohort.get("good_cpc", 1)),
        poor_cpc=int(cohort.get("poor_cpc", 5)),
        good_label=str(cohort.get("good_label", "CPC1")),
        poor_label=str(cohort.get("poor_label", "CPC5")),
        primary_scheme=str(timing.get("primary_scheme", "primary_12h")),
        hourly_scheme=str(timing.get("hourly_scheme", "hourly_12h")),
        primary_window=str(timing.get("primary_window", "0_12h")),
        reachability=dict(raw.get("reachability") or {}),
        diffusion_eps=float((raw.get("diffusion") or {}).get("epsilon", 1e-12)),
        bh_alpha=float(stats.get("bh_alpha", 0.05)),
        min_group_n=int(stats.get("min_group_n", 2)),
        min_testable_group_n=int(stats.get("min_testable_group_n", 10)),
        smoke=smoke,
        subject_allowlist=tuple(allowlist) if allowlist else None,
        workers=int(args.workers),
        limit_h5=args.limit_h5 if args.limit_h5 is not None else args.subject_limit if allowlist is None else None,
    )


def outcome_label(cpc: Any, cfg: PipelineConfig) -> str | None:
    try:
        value = int(float(cpc))
    except (TypeError, ValueError):
        return None
    if value == cfg.good_cpc:
        return cfg.good_label
    if value == cfg.poor_cpc:
        return cfg.poor_label
    return None


def h5_scalar(handle: Any, path: str, default: Any = None) -> Any:
    if path not in handle:
        return default
    obj = handle[path]
    if hasattr(obj, "shape") and obj.shape == ():
        return as_scalar(obj[()])
    return default


def participant_meta_from_handle(handle: Any) -> dict[str, Any]:
    raw = parse_jsonish(handle.attrs.get("participant_meta"))
    if not isinstance(raw, dict):
        raw = {}
        if "/participant/row_json" in handle:
            raw = parse_jsonish(handle["/participant/row_json"][()]) or {}
    meta = {
        "subject_id": normalize_subject_id(raw.get("participant_id") or handle.attrs.get("subject_id") or handle.attrs.get("meta_participant_id")),
        "patient": as_scalar(raw.get("patient", handle.attrs.get("meta_patient"))),
        "hospital": as_scalar(raw.get("hospital", handle.attrs.get("meta_hospital"))),
        "age": as_scalar(raw.get("age", handle.attrs.get("meta_age"))),
        "sex": as_scalar(raw.get("sex", handle.attrs.get("meta_sex"))),
        "rosc": as_scalar(raw.get("rosc", handle.attrs.get("meta_rosc"))),
        "ohca": as_scalar(raw.get("ohca", handle.attrs.get("meta_ohca"))),
        "shockable_rhythm": as_scalar(raw.get("shockable_rhythm", handle.attrs.get("meta_shockable_rhythm"))),
        "ttm": as_scalar(raw.get("ttm", handle.attrs.get("meta_ttm"))),
        "outcome": as_scalar(raw.get("outcome", handle.attrs.get("meta_outcome"))),
        "cpc": as_scalar(raw.get("cpc", handle.attrs.get("meta_cpc"))),
    }
    try:
        meta["cpc"] = int(float(meta["cpc"])) if meta["cpc"] is not None else None
    except (TypeError, ValueError):
        meta["cpc"] = None
    return meta


def time_reference_from_handle(handle: Any) -> dict[str, Any]:
    out = {
        "time_reference_status": h5_scalar(handle, "/extensions/time_reference/run/status"),
        "anchor_mode": h5_scalar(handle, "/extensions/time_reference/run/anchor_mode"),
        "subject_anchor_start_sec": h5_scalar(handle, "/extensions/time_reference/run/subject_anchor_start_sec"),
        "run_start_from_anchor_sec": float("nan"),
        "run_end_from_anchor_sec": float("nan"),
        "run_midpoint_from_anchor_hours": float("nan"),
        "n_windows": 0,
    }
    starts = None
    ends = None
    if "/extensions/time_reference/windows/window_start_from_anchor_sec" in handle:
        starts = np.asarray(handle["/extensions/time_reference/windows/window_start_from_anchor_sec"][:], dtype=float)
        ends = np.asarray(handle["/extensions/time_reference/windows/window_end_from_anchor_sec"][:], dtype=float)
    elif "/time" in handle:
        time = np.asarray(handle["/time"][:], dtype=float)
        starts = time
        ends = time
    if starts is not None and starts.size:
        finite_starts = starts[np.isfinite(starts)]
        finite_ends = ends[np.isfinite(ends)] if ends is not None else finite_starts
        if finite_starts.size:
            out["run_start_from_anchor_sec"] = float(np.min(finite_starts))
            out["run_end_from_anchor_sec"] = float(np.max(finite_ends)) if finite_ends.size else float(np.max(finite_starts))
            midpoint_sec = 0.5 * (out["run_start_from_anchor_sec"] + out["run_end_from_anchor_sec"])
            out["run_midpoint_from_anchor_hours"] = float(midpoint_sec / 3600.0)
            out["n_windows"] = int(starts.size)
    elif "/time" in handle:
        out["n_windows"] = int(handle["/time"].shape[0])
    return out


def diffusion_geometry_from_tensor(
    tensor: np.ndarray,
    drift: np.ndarray | None = None,
    *,
    eps: float = 1e-12,
) -> dict[str, float]:
    values = np.linalg.eigvalsh(np.asarray(tensor, dtype=float))
    values = np.clip(values, 0.0, None)
    d_total = float(np.sum(values))
    sq = float(np.sum(values**2))
    d_eff = float(d_total**2 / (sq + eps)) if sq > eps else float("nan")
    p = values / (d_total + eps)
    entropy = float(-np.sum(p * np.log(p + eps)))
    h_tilde = float(entropy / (np.log(float(values.size)) + eps)) if values.size else float("nan")
    e_perp = float("nan")
    a_bd = float("nan")
    if drift is not None:
        drift = np.asarray(drift, dtype=float).reshape(-1)
        if drift.size == values.size and np.isfinite(drift).all():
            norm = float(np.linalg.norm(drift))
            if norm > eps and d_total > 0:
                bhat = drift / norm
                d_parallel = float(bhat @ np.asarray(tensor, dtype=float) @ bhat)
                a_bd = float(d_parallel / (d_total + eps))
                e_perp = float((d_total - d_parallel) / (d_total + eps))
    return {
        "d_eff_a": d_eff,
        "h_tilde_a": h_tilde,
        "d_total": d_total,
        "e_perp": e_perp,
        "a_bd": a_bd,
    }
