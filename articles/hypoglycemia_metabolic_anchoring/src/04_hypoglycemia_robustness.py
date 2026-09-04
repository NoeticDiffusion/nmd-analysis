"""Paired label-swap null and adjusted-geometry sensitivity analyses."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
ARTICLE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_ROOT = (
    REPO_ROOT
    / "data"
    / "raw"
    / "neuralmanifolddynamics_hypoglycemia_t1d_20260723_180515"
)
DEFAULT_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "hypoglycemia_t1d_20260723"
DEFAULT_OUTPUT_ROOT = (
    ARTICLE_ROOT / "results" / "hypoglycemia_t1d_20260723" / "04_hypoglycemia_robustness"
)
PRIMARY_METRICS = {
    "global_mnps_9d": [
        "m_a_median",
        "m_e_median",
        "d_n_median",
        "d_l_median",
        "e_e_median",
        "e_m_median",
    ],
    "reachability_cones": [
        "tube_log_det_median",
        "tube_d_eff_median",
        "tube_kappa_median",
        "tube_dir_entropy_median",
        "tube_rotation_median",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--analysis-root", type=Path, default=DEFAULT_ANALYSIS_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--permutations", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260723)
    return parser.parse_args()


def latest_parquet(root: Path, token: str) -> Path:
    matches = sorted(root.glob(f"*{token}*.parquet"), key=lambda path: path.stat().st_mtime)
    if not matches:
        raise FileNotFoundError(f"No {token} parquet found in {root}.")
    return matches[-1]


def adjusted_hypoglycemia_subjects(raw_root: Path) -> pd.DataFrame:
    records = []
    for path in sorted(raw_root.glob("sub-*_hypoglycemia/qc_summary.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        status = payload.get("geometry_contract", {}).get("status")
        if status == "adjusted":
            records.append(
                {
                    "subject_id": payload["subject"],
                    "condition": "hypoglycemia",
                    "geometry_contract_status": status,
                    "source_qc_summary": str(path),
                }
            )
    return pd.DataFrame(records)


def bh_fdr(values: pd.Series) -> np.ndarray:
    p = values.to_numpy(dtype=float)
    order = np.argsort(p)
    ranked = p[order]
    adjusted = np.minimum.accumulate((ranked * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1]
    result = np.empty_like(adjusted)
    result[order] = np.clip(adjusted, 0.0, 1.0)
    return result


def paired_deltas(subject_metrics: pd.DataFrame) -> pd.DataFrame:
    selected = []
    for analysis_type, metrics in PRIMARY_METRICS.items():
        selected.append(
            subject_metrics[
                (subject_metrics["analysis_type"] == analysis_type)
                & subject_metrics["metric"].isin(metrics)
            ]
        )
    selected_frame = pd.concat(selected, ignore_index=True)
    records = []
    for (analysis_type, metric), frame in selected_frame.groupby(["analysis_type", "metric"]):
        pivot = frame.pivot(index="subject_id", columns="condition", values="value")
        if not {"euglycemia", "hypoglycemia"}.issubset(pivot.columns):
            continue
        pairs = pivot[["euglycemia", "hypoglycemia"]].dropna()
        for subject_id, row in pairs.iterrows():
            records.append(
                {
                    "analysis_type": analysis_type,
                    "metric": metric,
                    "subject_id": subject_id,
                    "euglycemia": row["euglycemia"],
                    "hypoglycemia": row["hypoglycemia"],
                    "delta_hypo_minus_eu": row["hypoglycemia"] - row["euglycemia"],
                }
            )
    return pd.DataFrame(records)


def label_swap_null(deltas: pd.DataFrame, permutations: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    records = []
    for (analysis_type, metric), frame in deltas.groupby(["analysis_type", "metric"]):
        values = frame["delta_hypo_minus_eu"].to_numpy(dtype=float)
        observed = float(values.mean())
        signs = rng.choice(np.array([-1.0, 1.0]), size=(permutations, len(values)))
        null = (signs * values).mean(axis=1)
        p_value = float((1 + np.count_nonzero(np.abs(null) >= abs(observed))) / (permutations + 1))
        records.append(
            {
                "analysis_type": analysis_type,
                "metric": metric,
                "n_pairs": len(values),
                "observed_delta": observed,
                "null_mean": float(null.mean()),
                "null_sd": float(null.std(ddof=1)),
                "null_p_two_sided": p_value,
                "permutations": permutations,
                "seed": seed,
            }
        )
    result = pd.DataFrame(records)
    result["null_q_value"] = bh_fdr(result["null_p_two_sided"])
    return result


def sensitivity_excluding_adjusted(deltas: pd.DataFrame, excluded_subjects: set[str]) -> pd.DataFrame:
    records = []
    for (analysis_type, metric), frame in deltas.groupby(["analysis_type", "metric"]):
        all_values = frame["delta_hypo_minus_eu"].to_numpy(dtype=float)
        kept = frame[~frame["subject_id"].isin(excluded_subjects)]
        kept_values = kept["delta_hypo_minus_eu"].to_numpy(dtype=float)
        records.append(
            {
                "analysis_type": analysis_type,
                "metric": metric,
                "n_full": len(all_values),
                "n_sensitivity": len(kept_values),
                "delta_full": float(all_values.mean()),
                "delta_excluding_adjusted": float(kept_values.mean()),
                "direction_preserved": bool(np.sign(all_values.mean()) == np.sign(kept_values.mean())),
            }
        )
    return pd.DataFrame(records)


def write_report(
    output_path: Path,
    adjusted: pd.DataFrame,
    null_results: pd.DataFrame,
    sensitivity: pd.DataFrame,
) -> None:
    lines = [
        "# Hypoglycemia robustness analyses",
        "",
        "## Design",
        "",
        "- Label-swap null: independently swap euglycemia/hypoglycemia labels within each paired participant.",
        "- Sensitivity: exclude participants whose hypoglycemia H5 geometry contract is marked `adjusted`.",
        "- This tests the stability of condition association; it does not create an euglycemia-only feature anchor or establish a glucose dose-response.",
        "",
        "## Excluded in adjusted-geometry sensitivity",
        "",
    ]
    for subject_id in adjusted["subject_id"].tolist():
        lines.append(f"- `{subject_id}`")
    lines += [
        "",
        "## Paired label-swap null",
        "",
        "| analysis | metric | n | observed HYPO-EU | null p | null q |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, row in null_results.sort_values(["analysis_type", "metric"]).iterrows():
        lines.append(
            f"| {row['analysis_type']} | {row['metric']} | {row['n_pairs']} | "
            f"{row['observed_delta']:.4g} | {row['null_p_two_sided']:.4g} | {row['null_q_value']:.4g} |"
        )
    lines += [
        "",
        "## Excluding adjusted-geometry participants",
        "",
        "| analysis | metric | n full -> sensitivity | full delta | sensitivity delta | direction preserved |",
        "|---|---|---:|---:|---:|---|",
    ]
    for _, row in sensitivity.sort_values(["analysis_type", "metric"]).iterrows():
        lines.append(
            f"| {row['analysis_type']} | {row['metric']} | {row['n_full']} -> {row['n_sensitivity']} | "
            f"{row['delta_full']:.4g} | {row['delta_excluding_adjusted']:.4g} | {row['direction_preserved']} |"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    subject_metrics = pd.read_parquet(latest_parquet(args.analysis_root, "subject_metrics"))
    adjusted = adjusted_hypoglycemia_subjects(args.raw_root)
    if adjusted.empty:
        raise ValueError("No adjusted hypoglycemia geometry sessions detected.")
    deltas = paired_deltas(subject_metrics)
    null_results = label_swap_null(deltas, args.permutations, args.seed)
    sensitivity = sensitivity_excluding_adjusted(deltas, set(adjusted["subject_id"]))

    adjusted.to_csv(args.output_root / "adjusted_hypoglycemia_sessions.csv", index=False)
    deltas.to_csv(args.output_root / "primary_paired_deltas.csv", index=False)
    null_results.to_csv(args.output_root / "paired_label_swap_null.csv", index=False)
    sensitivity.to_csv(args.output_root / "sensitivity_excluding_adjusted.csv", index=False)
    write_report(args.output_root / "04_hypoglycemia_robustness.md", adjusted, null_results, sensitivity)
    print(f"output_root={args.output_root}")


if __name__ == "__main__":
    main()
