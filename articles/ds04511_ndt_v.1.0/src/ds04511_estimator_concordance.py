"""Common-support concordance of chart and one-step task contrasts.

This is a descriptive, frozen-output analysis.  It consumes the subject-level
task contrasts already written by ``ds04511_estimator_task_interaction.py``;
it never refits an estimator, changes support, or recalibrates an endpoint.
The two axes are the declared estimator-specific robust-z task contrasts, so
the plot is not a comparison of the raw endpoint units.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from ds04511_common import ARTICLE_DIR, json_safe, sha256_file, write_json


INPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_estimator_task_interaction_20260922" / "interaction_pairs.csv"
OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_estimator_concordance_20260922"
PLOT_DEFAULT = ARTICLE_DIR / "figures" / "results" / "ds004511_common_support_concordance_20260922"
BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 20260923
CONTRAST_ORDER = ("gambling_minus_rest", "cognitive_control_minus_rest", "gambling_minus_cognitive_control")
LABELS = {
    "gambling_minus_rest": "GG − Rest",
    "cognitive_control_minus_rest": "CC − Rest",
    "gambling_minus_cognitive_control": "GG − CC",
}


def _finite_pair(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    x = pd.to_numeric(frame["chart_task_difference"], errors="coerce").to_numpy(float)
    y = pd.to_numeric(frame["l3_task_difference"], errors="coerce").to_numpy(float)
    mask = np.isfinite(x) & np.isfinite(y) & frame["common_complete"].astype(bool).to_numpy()
    return x[mask], y[mask]


def sign_agreement(x: Any, y: Any) -> tuple[int, int, float]:
    """Return agreeing nonzero signs, denominator, and proportion."""
    xa = np.asarray(x, dtype=float).reshape(-1)
    ya = np.asarray(y, dtype=float).reshape(-1)
    mask = np.isfinite(xa) & np.isfinite(ya) & (xa != 0.0) & (ya != 0.0)
    denominator = int(mask.sum())
    agreeing = int(np.sum(np.signbit(xa[mask]) == np.signbit(ya[mask])))
    return agreeing, denominator, float(agreeing / denominator) if denominator else float("nan")


def _bootstrap_statistic(x: np.ndarray, y: np.ndarray, statistic, *, seed: int) -> tuple[float, float, int]:
    if x.size < 2:
        return float("nan"), float("nan"), 0
    rng = np.random.default_rng(seed)
    draws = np.empty(BOOTSTRAP_N, dtype=float)
    for index in range(BOOTSTRAP_N):
        indices = rng.integers(0, x.size, size=x.size)
        draws[index] = float(statistic(x[indices], y[indices]))
    draws = draws[np.isfinite(draws)]
    if draws.size < max(50, BOOTSTRAP_N // 2):
        return float("nan"), float("nan"), int(draws.size)
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)), int(draws.size)


def _rho(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 2 or np.unique(x).size < 2 or np.unique(y).size < 2:
        return float("nan")
    return float(stats.spearmanr(x, y).statistic)


def _agreement(x: np.ndarray, y: np.ndarray) -> float:
    return sign_agreement(x, y)[2]


def concordance_table(pairs: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for index, contrast_id in enumerate(CONTRAST_ORDER):
        frame = pairs[pairs["contrast_id"].eq(contrast_id)]
        x, y = _finite_pair(frame)
        agreeing, sign_n, agreement = sign_agreement(x, y)
        rho = _rho(x, y)
        rho_lo, rho_hi, rho_n = _bootstrap_statistic(x, y, _rho, seed=BOOTSTRAP_SEED + index)
        agreement_lo, agreement_hi, agreement_boot_n = _bootstrap_statistic(
            x, y, _agreement, seed=BOOTSTRAP_SEED + 100 + index
        )
        if x.size >= 3 and np.unique(x).size > 1 and np.unique(y).size > 1:
            rho_p = float(stats.spearmanr(x, y).pvalue)
        else:
            rho_p = float("nan")
        rows.append(
            {
                "analysis_id": "estimator_concordance_common_support_20260922",
                "contrast_id": contrast_id,
                "n_subject_pairs": int(x.size),
                "spearman_rho": rho,
                "spearman_p": rho_p,
                "spearman_bootstrap_ci_lo": rho_lo,
                "spearman_bootstrap_ci_hi": rho_hi,
                "spearman_bootstrap_n": rho_n,
                "sign_agree_n": agreeing,
                "sign_nonzero_n": sign_n,
                "sign_agreement": agreement,
                "sign_agreement_bootstrap_ci_lo": agreement_lo,
                "sign_agreement_bootstrap_ci_hi": agreement_hi,
                "sign_agreement_bootstrap_n": agreement_boot_n,
                "bootstrap_n": BOOTSTRAP_N,
                "bootstrap_seed": BOOTSTRAP_SEED,
                "estimand": "Spearman and nonzero-sign agreement of standardized estimator task contrasts",
                "support": "common production estimator-supported subject-task contrasts",
                "raw_unit_comparison": False,
            }
        )
    return pd.DataFrame(rows)


def write_report(path: Path, results: pd.DataFrame, input_path: Path) -> None:
    lines = [
        "# ds004511 common-support chart-versus-L3 concordance",
        "",
        "This descriptive analysis consumes `interaction_pairs.csv` from the frozen estimator-by-task interaction run. It performs no refit, interpolation, recalibration, or support change.",
        "",
        "The axes are the estimator-specific robust-z task contrasts declared in the interaction analysis. Spearman correlation describes subject-level rank concordance; sign agreement is the fraction of nonzero common pairs with the same contrast direction. Percentile bootstrap intervals resample complete subject pairs within each contrast (10,000 draws; seed 20260923 plus fixed offsets).",
        "",
        "Common support is recording/subject-task support under the existing production gates, not pointwise temporal alignment of chart and one-step time series. These descriptors do not establish raw-unit equality, estimator equivalence, biological mechanism, or causal task effects.",
        "",
        "| contrast | n | Spearman rho | rho 95% CI | rho p | same-sign / nonzero | agreement 95% CI |",
        "| --- | ---: | ---: | --- | ---: | ---: | --- |",
    ]
    for _, row in results.iterrows():
        lines.append(
            f"| {LABELS[row['contrast_id']]} | {int(row['n_subject_pairs'])} | {row['spearman_rho']:.4g} | [{row['spearman_bootstrap_ci_lo']:.4g}, {row['spearman_bootstrap_ci_hi']:.4g}] | {row['spearman_p']:.4g} | {int(row['sign_agree_n'])}/{int(row['sign_nonzero_n'])} ({row['sign_agreement']:.3f}) | [{row['sign_agreement_bootstrap_ci_lo']:.3f}, {row['sign_agreement_bootstrap_ci_hi']:.3f}] |"
        )
    lines.extend(["", f"Input: `{input_path.name}`; SHA256 `{sha256_file(input_path)}`.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def plot_concordance(pairs: pd.DataFrame, results: pd.DataFrame, output_stem: Path) -> None:
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.6), sharex=False, sharey=False)
    colors = {"gambling_minus_rest": "#007c83", "cognitive_control_minus_rest": "#5c5aa8", "gambling_minus_cognitive_control": "#c26b2b"}
    for ax, contrast_id in zip(axes, CONTRAST_ORDER):
        frame = pairs[pairs["contrast_id"].eq(contrast_id)]
        x, y = _finite_pair(frame)
        row = results[results["contrast_id"].eq(contrast_id)].iloc[0]
        ax.scatter(x, y, s=22, alpha=0.72, color=colors[contrast_id], edgecolor="white", linewidth=0.35)
        finite = np.concatenate([x, y]) if x.size else np.asarray([0.0])
        bound = max(1.0, float(np.max(np.abs(finite))) * 1.08)
        ax.plot([-bound, bound], [-bound, bound], linestyle="--", color="#777777", linewidth=0.8)
        ax.axhline(0, color="#dddddd", linewidth=0.6)
        ax.axvline(0, color="#dddddd", linewidth=0.6)
        ax.set_xlim(-bound, bound)
        ax.set_ylim(-bound, bound)
        ax.set_title(f"{LABELS[contrast_id]}\n$n={int(row['n_subject_pairs'])}$, $\u03c1_s={row['spearman_rho']:.2f}$")
        ax.set_xlabel("Chart-Jacobian α task contrast (robust z)")
        if ax is axes[0]:
            ax.set_ylabel("One-step L3 α task contrast (robust z)")
        ax.set_aspect("equal", adjustable="box")
        ax.tick_params(labelsize=8)
    fig.suptitle("Common-support concordance of estimator task contrasts", y=1.02)
    fig.text(0.5, -0.03, "Dashed line: equal standardized contrast; common support is not pointwise temporal alignment.", ha="center", fontsize=8.5)
    fig.tight_layout()
    for suffix in (".svg", ".png"):
        fig.savefig(output_stem.with_suffix(suffix), dpi=300, bbox_inches="tight")
    plt.close(fig)


def run(*, input_path: Path, output_root: Path, plot_stem: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    pairs = pd.read_csv(input_path)
    required = {"contrast_id", "chart_task_difference", "l3_task_difference", "common_complete"}
    missing = required.difference(pairs.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    results = concordance_table(pairs)
    results.to_csv(output_root / "concordance_results.csv", index=False)
    pairs.loc[pairs["contrast_id"].isin(CONTRAST_ORDER)].to_csv(output_root / "concordance_pairs.csv", index=False)
    write_report(output_root / "concordance_report.md", results, input_path)
    plot_concordance(pairs, results, plot_stem)
    manifest = {
        "schema": "ds004511_ndt_v1.estimator_concordance.v1",
        "analysis_id": "estimator_concordance_common_support_20260922",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_status": "descriptive_common_support_only",
        "input": {"path": str(input_path), "sha256": sha256_file(input_path)},
        "n_input_rows": int(len(pairs)),
        "n_results": int(len(results)),
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "raw_unit_comparison": False,
        "no_refit_interpolation_or_support_change": True,
        "pointwise_temporal_alignment": False,
        "plot": str(plot_stem),
    }
    write_json(output_root / "concordance_manifest.json", json_safe(manifest))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_DEFAULT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--plot-stem", type=Path, default=PLOT_DEFAULT)
    args = parser.parse_args(argv)
    manifest = run(input_path=args.input, output_root=args.output_root, plot_stem=args.plot_stem)
    print(json.dumps({"output_root": str(args.output_root), "n_input_rows": manifest["n_input_rows"], "n_results": manifest["n_results"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
