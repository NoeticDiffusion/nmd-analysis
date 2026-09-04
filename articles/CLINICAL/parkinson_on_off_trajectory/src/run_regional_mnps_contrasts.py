"""
run_regional_mnps_contrasts.py
================================
Standalone analysis of regional MNPS summary statistics from a NeuralManifoldDynamics
bundle export — no legacy adapters, no ndt-analysis pipeline dependency.

Reads the pre-computed per-subject aggregate CSV (`regional_mnps_subjects_*.csv`) that
the MNDM exporter writes to the bundle root, applies the three Parkinson ON/OFF contrasts,
applies BH-FDR correction, and writes `regional_mnps_contrasts.csv` to the results
directory alongside the other primary contrast CSVs.

Metrics covered
---------------
  Coordinate statistics (m, d, e):  mean, std, median, IQR, MAD
  Matrix statistics:                 trace_mean, trace_std, frobenius_mean,
                                     rotation_norm_mean, anisotropy_mean
  Stratified chart (9D):             strat9_condition_number, strat9_pc1_var,
                                     strat9_pc2_var, strat9_pc3_var,
                                     strat9_pc1_3_cumulative_var

Coordinate note
---------------
The m/d/e values in the bundle CSV are computed in the bundle's primary coordinate
contract (cohort-anchored for ds003490).  For between-group contrasts this is
appropriate.  The matrix-derived metrics (frobenius, rotation_norm, anisotropy, strat9)
are anchor-invariant.

Usage
-----
  python run_regional_mnps_contrasts.py                         # auto-detects latest bundle
  python run_regional_mnps_contrasts.py --bundle PATH/TO/BUNDLE
  python run_regional_mnps_contrasts.py --output-dir PATH/TO/OUT
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[2]
DATA_RAW = REPO_ROOT / "data" / "raw"
DATASET_ID = "ds003490"

# ---------------------------------------------------------------------------
# Analysis configuration
# ---------------------------------------------------------------------------

ANALYSIS_TYPE = "regional_mnps_3d"

NUMERIC_METRICS: list[str] = [
    "m_mean", "m_std", "m_median", "m_iqr", "m_mad",
    "d_mean", "d_std", "d_median", "d_iqr", "d_mad",
    "e_mean", "e_std", "e_median", "e_iqr", "e_mad",
    "trace_mean", "trace_std",
    "frobenius_mean",
    "rotation_norm_mean",
    "anisotropy_mean",
    "strat9_condition_number",
    "strat9_pc1_var",
    "strat9_pc2_var",
    "strat9_pc3_var",
    "strat9_pc1_3_cumulative_var",
]

# Columns that are flags, not numeric measurements
_SKIP_COLS: set[str] = {"strat9_falsified"}

CONTRASTS: list[dict[str, Any]] = [
    {
        "name": "Control_vs_Parkinson_OFF",
        "type": "unpaired",
        "left_group": "Control",
        "left_condition": "not_applicable",
        "right_group": "Parkinson",
        "right_condition": "OFF",
    },
    {
        "name": "Control_vs_Parkinson_ON",
        "type": "unpaired",
        "left_group": "Control",
        "left_condition": "not_applicable",
        "right_group": "Parkinson",
        "right_condition": "ON",
    },
    {
        "name": "Parkinson_OFF_vs_ON",
        "type": "paired",
        "left_condition": "OFF",
        "right_condition": "ON",
        "pair_group": "Parkinson",
    },
]

MIN_GROUP_N = 3


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def _bh_fdr(p_values: pd.Series) -> pd.Series:
    arr = pd.to_numeric(p_values, errors="coerce").to_numpy(dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    mask = np.isfinite(arr)
    if not mask.any():
        return pd.Series(out, index=p_values.index, dtype=float)
    valid = arr[mask]
    order = np.argsort(valid)
    ranks = np.arange(1, len(valid) + 1, dtype=float)
    q_sorted = np.minimum.accumulate((valid[order] * len(valid) / ranks)[::-1])[::-1]
    q = np.empty_like(q_sorted)
    q[order] = np.clip(q_sorted, 0.0, 1.0)
    out[np.where(mask)[0]] = q
    return pd.Series(out, index=p_values.index, dtype=float)


def _cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    """Unpaired Cohen's d = (mean_right - mean_left) / pooled_SD."""
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    left = left[np.isfinite(left)]
    right = right[np.isfinite(right)]
    if left.size < 2 or right.size < 2:
        return float("nan")
    pooled = (
        (left.size - 1) * np.var(left, ddof=1) + (right.size - 1) * np.var(right, ddof=1)
    ) / (left.size + right.size - 2)
    if not np.isfinite(pooled) or pooled <= 0:
        return float("nan")
    return float((np.mean(right) - np.mean(left)) / math.sqrt(pooled))


def _cohens_dz(diff: np.ndarray) -> float:
    """Paired Cohen's d_z = mean(diff) / SD(diff)."""
    diff = np.asarray(diff, dtype=float)
    diff = diff[np.isfinite(diff)]
    if diff.size < 2:
        return float("nan")
    sd = float(np.std(diff, ddof=1))
    if not np.isfinite(sd) or sd <= 0:
        return float("nan")
    return float(np.mean(diff) / sd)


# ---------------------------------------------------------------------------
# Bundle / CSV discovery
# ---------------------------------------------------------------------------

def find_latest_bundle(data_raw: Path, dataset_id: str = DATASET_ID) -> Path:
    candidates = sorted(
        [d for d in data_raw.iterdir() if d.is_dir() and dataset_id in d.name],
        key=lambda p: p.name,
    )
    if not candidates:
        raise FileNotFoundError(f"No {dataset_id} bundle found under {data_raw}")
    return candidates[-1]


def find_bundle_csv(bundle_root: Path) -> Path:
    matches = sorted(bundle_root.glob("regional_mnps_subjects_*.csv"))
    if not matches:
        raise FileNotFoundError(
            f"No regional_mnps_subjects_*.csv found in {bundle_root}\n"
            f"This file is exported by the MNDM bundle and should be present for ds003490."
        )
    return matches[-1]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # Derive group from condition_label (Controls have condition not_applicable)
    df["group"] = df["condition_label"].apply(
        lambda c: "Control" if c == "not_applicable" else "Parkinson"
    )

    # Replace inf/-inf with NaN so dropna / isfinite work uniformly
    numeric_cols = [c for c in NUMERIC_METRICS if c in df.columns]
    df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)

    return df


# ---------------------------------------------------------------------------
# Contrast execution
# ---------------------------------------------------------------------------

def _run_unpaired_contrast(
    df: pd.DataFrame,
    contrast: dict[str, Any],
    metrics: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for network in sorted(df.network_label.unique()):
        net_df = df[df.network_label == network]
        left_df = net_df[
            (net_df.group == contrast["left_group"])
            & (net_df.condition_label == contrast["left_condition"])
        ]
        right_df = net_df[
            (net_df.group == contrast["right_group"])
            & (net_df.condition_label == contrast["right_condition"])
        ]
        for metric in metrics:
            lv = left_df[metric].dropna().to_numpy(dtype=float)
            rv = right_df[metric].dropna().to_numpy(dtype=float)
            lv = lv[np.isfinite(lv)]
            rv = rv[np.isfinite(rv)]
            if lv.size < MIN_GROUP_N or rv.size < MIN_GROUP_N:
                continue
            _, p = mannwhitneyu(lv, rv, alternative="two-sided")
            rows.append({
                "contrast_name": contrast["name"],
                "contrast_type": "unpaired",
                "analysis_type": ANALYSIS_TYPE,
                "network": network,
                "metric": metric,
                "left_n": int(lv.size),
                "right_n": int(rv.size),
                "left_median": float(np.median(lv)),
                "right_median": float(np.median(rv)),
                "effect_size": _cohens_d(lv, rv),
                "p_value": float(p),
                "q_value": float("nan"),
            })
    return rows


def _run_paired_contrast(
    df: pd.DataFrame,
    contrast: dict[str, Any],
    metrics: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for network in sorted(df.network_label.unique()):
        net_df = df[(df.network_label == network) & (df.group == contrast["pair_group"])]
        left_by_sub = (
            net_df[net_df.condition_label == contrast["left_condition"]]
            .set_index("subject_id")
        )
        right_by_sub = (
            net_df[net_df.condition_label == contrast["right_condition"]]
            .set_index("subject_id")
        )
        paired_ids = sorted(set(left_by_sub.index) & set(right_by_sub.index))
        if len(paired_ids) < MIN_GROUP_N:
            continue
        for metric in metrics:
            lv_raw = np.array(
                [float(left_by_sub.loc[s, metric]) for s in paired_ids], dtype=float
            )
            rv_raw = np.array(
                [float(right_by_sub.loc[s, metric]) for s in paired_ids], dtype=float
            )
            valid = np.isfinite(lv_raw) & np.isfinite(rv_raw)
            lv = lv_raw[valid]
            rv = rv_raw[valid]
            diffs = rv - lv
            if diffs.size < MIN_GROUP_N or np.all(diffs == 0):
                continue
            _, p = wilcoxon(diffs, alternative="two-sided")
            rows.append({
                "contrast_name": contrast["name"],
                "contrast_type": "paired",
                "analysis_type": ANALYSIS_TYPE,
                "network": network,
                "metric": metric,
                "left_n": int(diffs.size),
                "right_n": int(diffs.size),
                "left_median": float(np.median(lv)),
                "right_median": float(np.median(rv)),
                "effect_size": _cohens_dz(diffs),
                "p_value": float(p),
                "q_value": float("nan"),
            })
    return rows


def run_all_contrasts(df: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    all_rows: list[dict[str, Any]] = []
    for contrast in CONTRASTS:
        if contrast["type"] == "unpaired":
            all_rows.extend(_run_unpaired_contrast(df, contrast, metrics))
        else:
            all_rows.extend(_run_paired_contrast(df, contrast, metrics))
    return pd.DataFrame(all_rows)


def apply_fdr(results: pd.DataFrame) -> pd.DataFrame:
    """BH-FDR within each contrast_name × analysis_type group."""
    corrected: list[pd.DataFrame] = []
    for _, grp in results.groupby(["contrast_name", "analysis_type"], sort=False):
        grp = grp.copy()
        grp["q_value"] = _bh_fdr(grp["p_value"])
        corrected.append(grp)
    return pd.concat(corrected, ignore_index=True)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_summary(results: pd.DataFrame) -> None:
    for contrast_name, grp in results.groupby("contrast_name"):
        n05 = (grp.q_value < 0.05).sum()
        n10 = (grp.q_value < 0.10).sum()
        print(f"\n  {contrast_name}  (q<0.05={n05}, q<0.1={n10})")
        sig = grp[grp.q_value < 0.05].copy()
        sig["abs_d"] = sig["effect_size"].abs()
        for _, r in sig.sort_values("abs_d", ascending=False).head(8).iterrows():
            print(
                f"    {r.network:20s}  {r.metric:35s}"
                f"  d={r.effect_size:+.3f}  q={r.q_value:.4f}"
            )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle",
        type=Path,
        default=None,
        help="Path to MNDM bundle root. Defaults to the latest ds003490 bundle.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to results/parkinson_on_off_dual_contract_<stamp>/.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    bundle_root = args.bundle or find_latest_bundle(DATA_RAW)
    print(f"Bundle : {bundle_root.name}")

    csv_path = find_bundle_csv(bundle_root)
    print(f"Input  : {csv_path.name}")

    df = load_data(csv_path)
    metrics = [m for m in NUMERIC_METRICS if m in df.columns and m not in _SKIP_COLS]
    networks = sorted(df.network_label.unique())
    print(f"Metrics: {len(metrics)}  |  Networks: {networks}")
    print(
        f"Subjects: {df.subject_id.nunique()} "
        f"(Controls={df[df.group=='Control'].subject_id.nunique()}, "
        f"Parkinson={df[df.group=='Parkinson'].subject_id.nunique()})"
    )

    results = run_all_contrasts(df, metrics)
    results = apply_fdr(results)
    results = results.sort_values(["contrast_name", "q_value", "p_value"]).reset_index(drop=True)

    if args.output_dir is not None:
        output_dir = args.output_dir
    else:
        # Mirror the naming convention from run_parkinson_pipeline.py
        bundle_stamp = "_".join(bundle_root.name.split("_")[-2:])
        results_slug = f"parkinson_on_off_dual_contract_{bundle_stamp}"
        output_dir = ARTICLE_DIR / "results" / results_slug

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "regional_mnps_contrasts.csv"
    results.to_csv(out_path, index=False)
    print(f"\nSaved {len(results)} rows -> {out_path.relative_to(REPO_ROOT)}")

    print("\nSummary by contrast:")
    print_summary(results)


if __name__ == "__main__":
    main()
