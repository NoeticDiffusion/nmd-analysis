from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from parkinson_walking_support import (
    DATASET_ROOT,
    PARTICIPANTS_PATH,
    RESULTS_DIR,
    RUN_METRIC_COLUMNS,
    RUN_METRICS_CSV,
    bh_fdr,
    cohens_d,
    ensure_dir,
    fmt,
    load_or_build_run_metrics,
    write_json,
)


DELTA_DIR = RESULTS_DIR / "delta_contrasts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run walk-minus-rest delta contrasts between HC and PD for the Parkinson walking dataset."
    )
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--participants-tsv", type=Path, default=PARTICIPANTS_PATH)
    parser.add_argument("--output-dir", type=Path, default=DELTA_DIR)
    parser.add_argument("--rebuild-run-metrics", action="store_true")
    return parser.parse_args()


def build_delta_frame(run_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    metric_columns = [metric for metric in RUN_METRIC_COLUMNS if metric in run_metrics.columns]
    base = run_metrics[["participant_id", "group", "task", *metric_columns]].copy()
    for metric in metric_columns:
        wide = (
            base[["participant_id", "group", "task", metric]]
            .pivot_table(index=["participant_id", "group"], columns="task", values=metric, aggfunc="mean", observed=True)
        )
        if not {"rest", "walk"}.issubset(wide.columns):
            continue
        paired = wide[["rest", "walk"]].dropna().reset_index()
        if paired.empty:
            continue
        paired["delta_walk_minus_rest"] = paired["walk"] - paired["rest"]
        for _, row in paired.iterrows():
            rows.append(
                {
                    "participant_id": row["participant_id"],
                    "group": row["group"],
                    "metric": metric,
                    "rest_value": float(row["rest"]),
                    "walk_value": float(row["walk"]),
                    "delta_walk_minus_rest": float(row["delta_walk_minus_rest"]),
                }
            )
    frame = pd.DataFrame(rows)
    return frame.sort_values(["metric", "group", "participant_id"]).reset_index(drop=True) if not frame.empty else frame


def delta_group_contrasts(delta_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for metric, metric_frame in delta_frame.groupby("metric", dropna=False):
        hc = pd.to_numeric(
            metric_frame.loc[metric_frame["group"] == "HC", "delta_walk_minus_rest"],
            errors="coerce",
        ).dropna()
        pd_group = pd.to_numeric(
            metric_frame.loc[metric_frame["group"] == "PD", "delta_walk_minus_rest"],
            errors="coerce",
        ).dropna()
        if len(hc) < 3 or len(pd_group) < 3:
            continue
        stat, p_value = stats.mannwhitneyu(hc.to_numpy(), pd_group.to_numpy(), alternative="two-sided")

        hc_rows = metric_frame.loc[metric_frame["group"] == "HC"]
        pd_rows = metric_frame.loc[metric_frame["group"] == "PD"]
        rows.append(
            {
                "contrast_name": "HC_vs_PD_task_delta",
                "metric": metric,
                "left_label": "HC",
                "right_label": "PD",
                "left_n": int(len(hc)),
                "right_n": int(len(pd_group)),
                "hc_rest_median": float(pd.to_numeric(hc_rows["rest_value"], errors="coerce").median()),
                "hc_walk_median": float(pd.to_numeric(hc_rows["walk_value"], errors="coerce").median()),
                "pd_rest_median": float(pd.to_numeric(pd_rows["rest_value"], errors="coerce").median()),
                "pd_walk_median": float(pd.to_numeric(pd_rows["walk_value"], errors="coerce").median()),
                "left_delta_median": float(hc.median()),
                "right_delta_median": float(pd_group.median()),
                "effect_estimate": float(pd_group.median() - hc.median()),
                "effect_size": float(cohens_d(hc.to_numpy(), pd_group.to_numpy())),
                "test_stat": float(stat),
                "p_value": float(p_value),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["q_value"] = bh_fdr(frame["p_value"])
    frame["abs_effect_size"] = pd.to_numeric(frame["effect_size"], errors="coerce").abs()
    return frame.sort_values(["q_value", "p_value", "abs_effect_size"], ascending=[True, True, False]).reset_index(drop=True)


def build_markdown(contrasts: pd.DataFrame) -> str:
    lines = [
        "# Parkinson walking task-delta contrasts",
        "",
        "This pass compares `walk - rest` deltas between `HC` and `PD` for each run-level metric.",
        "",
        "- Delta per participant: `walk value - rest value`",
        "- Group test: Mann-Whitney U on delta distributions",
        "- Effect size: Cohen's `d` on the delta distributions",
        "- Correction: BH-FDR across the full delta metric table",
        "",
    ]
    if contrasts.empty:
        lines.extend(["No task-delta contrasts were estimable.", ""])
        return "\n".join(lines)
    for _, row in contrasts.head(12).iterrows():
        lines.append(
            f"- `{row['metric']}`: HC delta median={fmt(row['left_delta_median'])}, "
            f"PD delta median={fmt(row['right_delta_median'])}, "
            f"d={fmt(row['effect_size'])}, p={fmt(row['p_value'])}, q={fmt(row['q_value'])}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)

    run_metrics_path = args.output_dir / RUN_METRICS_CSV
    run_metrics = load_or_build_run_metrics(
        run_metrics_path,
        dataset_root=args.dataset_root,
        participants_path=args.participants_tsv,
        rebuild=args.rebuild_run_metrics,
    )
    delta_frame = build_delta_frame(run_metrics)
    contrasts = delta_group_contrasts(delta_frame)

    if not delta_frame.empty:
        delta_frame.to_csv(args.output_dir / "participant_task_deltas.csv", index=False)
    if not contrasts.empty:
        contrasts.to_csv(args.output_dir / "hc_vs_pd_task_delta_contrasts.csv", index=False)
    (args.output_dir / "task_delta_summary.md").write_text(build_markdown(contrasts), encoding="utf-8")

    manifest = {
        "dataset_root": str(args.dataset_root),
        "participants_tsv": str(args.participants_tsv),
        "output_dir": str(args.output_dir),
        "run_metrics_csv": str(run_metrics_path),
        "n_participant_metric_rows": int(len(delta_frame)),
        "n_contrast_rows": int(len(contrasts)),
        "delta_definition": "walk_minus_rest",
        "group_test": "mannwhitneyu",
        "multiple_testing": "BH-FDR across all delta metrics",
    }
    write_json(args.output_dir / "task_delta_manifest.json", manifest)

    print(f"Wrote task-delta contrasts to {args.output_dir}")
    print(f"Participant-delta rows: {len(delta_frame)} | contrast rows: {len(contrasts)}")


if __name__ == "__main__":
    main()
