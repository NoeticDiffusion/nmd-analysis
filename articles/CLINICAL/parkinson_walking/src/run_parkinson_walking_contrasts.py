from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from parkinson_walking_support import (
    CONTRASTS_DIR,
    DATASET_ROOT,
    GROUP_ORDER,
    PARTICIPANTS_PATH,
    RUN_METRIC_COLUMNS,
    RUN_METRICS_CSV,
    TASK_ORDER,
    bh_fdr,
    cohens_d,
    cohens_dz,
    ensure_dir,
    fmt,
    load_or_build_run_metrics,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run simple rest/walk and group contrasts for the Parkinson walking dataset.")
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--participants-tsv", type=Path, default=PARTICIPANTS_PATH)
    parser.add_argument("--output-dir", type=Path, default=CONTRASTS_DIR)
    parser.add_argument("--anchor", choices=("auto", "cohort", "subject"), default="auto")
    parser.add_argument("--rebuild-run-metrics", action="store_true")
    return parser.parse_args()


def unpaired_rows(run_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    metric_columns = [metric for metric in RUN_METRIC_COLUMNS if metric in run_metrics.columns]
    for task in TASK_ORDER:
        task_frame = run_metrics[run_metrics["task"] == task].copy()
        left_frame = task_frame[task_frame["group"] == "HC"].copy()
        right_frame = task_frame[task_frame["group"] == "PD"].copy()
        for metric in metric_columns:
            left = pd.to_numeric(left_frame[metric], errors="coerce").dropna().to_numpy(dtype=float)
            right = pd.to_numeric(right_frame[metric], errors="coerce").dropna().to_numpy(dtype=float)
            if left.size < 3 or right.size < 3:
                continue
            stat, p_value = stats.mannwhitneyu(left, right, alternative="two-sided")
            rows.append(
                {
                    "contrast_name": f"HC_vs_PD_{task}",
                    "contrast_kind": "unpaired_group",
                    "group": "all",
                    "task": task,
                    "metric": metric,
                    "left_label": "HC",
                    "right_label": "PD",
                    "left_n": int(left.size),
                    "right_n": int(right.size),
                    "left_median": float(np.median(left)),
                    "right_median": float(np.median(right)),
                    "effect_estimate": float(np.median(right) - np.median(left)),
                    "effect_size": float(cohens_d(left, right)),
                    "test_stat": float(stat),
                    "p_value": float(p_value),
                }
            )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["q_value"] = frame.groupby("contrast_name", dropna=False)["p_value"].transform(bh_fdr)
    frame["abs_effect_size"] = pd.to_numeric(frame["effect_size"], errors="coerce").abs()
    return frame.sort_values(["contrast_name", "q_value", "p_value", "abs_effect_size"], ascending=[True, True, True, False]).reset_index(drop=True)


def paired_rows(run_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    metric_columns = [metric for metric in RUN_METRIC_COLUMNS if metric in run_metrics.columns]
    for group in GROUP_ORDER:
        group_frame = run_metrics[run_metrics["group"] == group].copy()
        for metric in metric_columns:
            wide = (
                group_frame[["participant_id", "task", metric]]
                .copy()
                .pivot_table(index="participant_id", columns="task", values=metric, aggfunc="mean", observed=True)
            )
            if not {"rest", "walk"}.issubset(wide.columns):
                continue
            paired = wide[["rest", "walk"]].dropna().copy()
            if len(paired) < 3:
                continue
            diff = paired["walk"].to_numpy(dtype=float) - paired["rest"].to_numpy(dtype=float)
            if np.allclose(diff, 0.0, equal_nan=False):
                stat = 0.0
                p_value = 1.0
                effect_size = 0.0
            else:
                stat, p_value = stats.wilcoxon(paired["rest"], paired["walk"])
                effect_size = float(cohens_dz(diff))
            rows.append(
                {
                    "contrast_name": f"{group}_walk_vs_rest",
                    "contrast_kind": "paired_task",
                    "group": group,
                    "task": "paired",
                    "metric": metric,
                    "left_label": "rest",
                    "right_label": "walk",
                    "left_n": int(len(paired)),
                    "right_n": int(len(paired)),
                    "left_median": float(np.median(paired["rest"])),
                    "right_median": float(np.median(paired["walk"])),
                    "effect_estimate": float(np.median(diff)),
                    "effect_size": effect_size,
                    "test_stat": float(stat),
                    "p_value": float(p_value),
                }
            )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["q_value"] = frame.groupby("contrast_name", dropna=False)["p_value"].transform(bh_fdr)
    frame["abs_effect_size"] = pd.to_numeric(frame["effect_size"], errors="coerce").abs()
    return frame.sort_values(["contrast_name", "q_value", "p_value", "abs_effect_size"], ascending=[True, True, True, False]).reset_index(drop=True)


def build_markdown(unpaired: pd.DataFrame, paired: pd.DataFrame, *, anchor: str) -> str:
    lines = [
        "# Parkinson walking contrasts",
        "",
        "This pass keeps the design intentionally simple:",
        "",
        f"- Anchor mode: `{anchor}`",
        "- `HC vs PD` within `rest`",
        "- `HC vs PD` within `walk`",
        "- `rest vs walk` within `HC` and within `PD` for participants with both runs",
        "",
    ]
    for frame, title in ((unpaired, "## Group contrasts"), (paired, "## Paired task contrasts")):
        lines.extend([title, ""])
        if frame.empty:
            lines.extend(["No contrasts were estimable.", ""])
            continue
        for contrast_name in frame["contrast_name"].drop_duplicates():
            block = frame[frame["contrast_name"] == contrast_name].head(8)
            lines.extend([f"### {contrast_name}", ""])
            for _, row in block.iterrows():
                lines.append(
                    f"- `{row['metric']}`: "
                    f"{row['left_label']} median={fmt(row['left_median'])}, "
                    f"{row['right_label']} median={fmt(row['right_median'])}, "
                    f"d={fmt(row['effect_size'])}, p={fmt(row['p_value'])}, q={fmt(row['q_value'])}"
                )
            lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    run_metrics_filename = RUN_METRICS_CSV if args.anchor == "auto" else f"run_metrics_{args.anchor}.csv"
    run_metrics_path = args.output_dir / run_metrics_filename
    run_metrics = load_or_build_run_metrics(
        run_metrics_path,
        dataset_root=args.dataset_root,
        participants_path=args.participants_tsv,
        rebuild=args.rebuild_run_metrics,
        anchor=args.anchor,
    )

    unpaired = unpaired_rows(run_metrics)
    paired = paired_rows(run_metrics)
    combined = pd.concat([unpaired, paired], ignore_index=True) if (not unpaired.empty or not paired.empty) else pd.DataFrame()

    if not unpaired.empty:
        unpaired.to_csv(args.output_dir / "group_contrasts.csv", index=False)
    if not paired.empty:
        paired.to_csv(args.output_dir / "paired_task_contrasts.csv", index=False)
    if not combined.empty:
        combined.to_csv(args.output_dir / "all_contrasts.csv", index=False)
    (args.output_dir / "contrast_summary.md").write_text(build_markdown(unpaired, paired, anchor=args.anchor), encoding="utf-8")

    manifest = {
        "dataset_root": str(args.dataset_root),
        "participants_tsv": str(args.participants_tsv),
        "output_dir": str(args.output_dir),
        "anchor": args.anchor,
        "run_metrics_csv": str(run_metrics_path),
        "n_unpaired_rows": int(len(unpaired)),
        "n_paired_rows": int(len(paired)),
        "contrast_names": sorted(set(combined["contrast_name"])) if not combined.empty else [],
    }
    write_json(args.output_dir / "contrast_manifest.json", manifest)

    print(f"Wrote contrasts to {args.output_dir}")
    print(f"Unpaired rows: {len(unpaired)} | paired rows: {len(paired)}")


if __name__ == "__main__":
    main()
