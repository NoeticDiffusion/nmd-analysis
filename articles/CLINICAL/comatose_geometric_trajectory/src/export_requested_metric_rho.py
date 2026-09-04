from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from scipy import stats

from trajectory_support import PATIENT_TIMEBIN_METRICS_CSV, bh_fdr, ensure_dir, resolve_metric_dir


REQUESTED_METRICS: tuple[str, ...] = (
    "entropy_rate",
    "irreversibility",
    "noetic_action_jerk",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute Spearman rho summaries for requested coma trajectory metrics."
    )
    parser.add_argument("--part1-dir", type=Path, default=resolve_metric_dir("part1"))
    parser.add_argument("--part2-dir", type=Path, default=resolve_metric_dir("part2"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "J:/repos/NoeticDiffusion/articles/CLINICAL/comatose_geometric_trajectory/results/rho_requested_metrics_20260601"
        ),
    )
    return parser.parse_args()


def load_metric_frame(input_dir: Path, *, cohort_tag: str) -> pd.DataFrame:
    frame = pd.read_csv(input_dir / PATIENT_TIMEBIN_METRICS_CSV, low_memory=False)
    frame = frame[frame["metric"].isin(REQUESTED_METRICS)].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame["label"] = pd.to_numeric(frame["label"], errors="coerce")
    frame = frame[frame["value"].notna() & frame["label"].notna()].copy()
    frame["cohort_tag"] = cohort_tag
    return frame.reset_index(drop=True)


def summarize_rho(frame: pd.DataFrame, *, cohort_tag: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (analysis_type, metric), group in frame.groupby(["analysis_type", "metric"], dropna=False):
        work = group[["value", "label"]].dropna().copy()
        if len(work) < 3 or work["label"].nunique() < 2:
            rho = float("nan")
            p_value = float("nan")
        else:
            rho, p_value = stats.spearmanr(work["value"], work["label"])
            rho = float(rho) if pd.notna(rho) else float("nan")
            p_value = float(p_value) if pd.notna(p_value) else float("nan")
        rows.append(
            {
                "cohort_tag": cohort_tag,
                "analysis_type": analysis_type,
                "metric": metric,
                "spearman_rho": rho,
                "p_value": p_value,
                "n": int(len(work)),
                "cpc1_median": float(group.loc[group["label"] == 1, "value"].median()),
                "cpc5_median": float(group.loc[group["label"] == 0, "value"].median()),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["q_value"] = out.groupby("cohort_tag", dropna=False)["p_value"].transform(bh_fdr)
    out["abs_spearman_rho"] = out["spearman_rho"].abs()
    return out.sort_values(["cohort_tag", "abs_spearman_rho"], ascending=[True, False]).reset_index(drop=True)


def build_markdown(summary: pd.DataFrame) -> str:
    lines = [
        "# Requested metric rho summary",
        "",
        "This summary reports Spearman rho versus the binary `CPC1`/`CPC5` label (`1 = CPC1`, `0 = CPC5`) for the three requested candidate metrics:",
        "",
        "- `entropy_rate`",
        "- `irreversibility`",
        "- `noetic_action_jerk`",
        "",
    ]
    if summary.empty:
        lines.extend(["No estimable rho rows were available.", ""])
        return "\n".join(lines)

    for cohort_tag, block in summary.groupby("cohort_tag", dropna=False):
        lines.extend([f"## {cohort_tag}", ""])
        ordered = block.sort_values("abs_spearman_rho", ascending=False)
        for _, row in ordered.iterrows():
            lines.append(
                "- "
                + f"`{row['analysis_type']}` / `{row['metric']}`: "
                + f"rho={float(row['spearman_rho']):.3f}, "
                + f"p={float(row['p_value']):.4g}, "
                + f"q={float(row['q_value']):.4g}, "
                + f"n={int(row['n'])}, "
                + f"CPC1 median={float(row['cpc1_median']):.5f}, "
                + f"CPC5 median={float(row['cpc5_median']):.5f}"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)

    part1 = load_metric_frame(args.part1_dir, cohort_tag="part1")
    part2 = load_metric_frame(args.part2_dir, cohort_tag="part2")
    pooled = pd.concat([part1, part2], ignore_index=True)
    pooled["cohort_tag"] = "pooled_part1_part2"

    summary = pd.concat(
        [
            summarize_rho(part1, cohort_tag="part1"),
            summarize_rho(part2, cohort_tag="part2"),
            summarize_rho(pooled, cohort_tag="pooled_part1_part2"),
        ],
        ignore_index=True,
    )
    summary.to_csv(args.output_dir / "requested_metric_rho_summary.csv", index=False)
    (args.output_dir / "requested_metric_rho_summary.md").write_text(build_markdown(summary), encoding="utf-8")


if __name__ == "__main__":
    main()
