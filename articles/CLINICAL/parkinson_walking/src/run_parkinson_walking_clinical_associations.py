from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from parkinson_walking_support import (
    CLINICAL_DIR,
    DATASET_ROOT,
    PARTICIPANTS_PATH,
    PD_CLINICAL_COLUMNS,
    RUN_METRIC_COLUMNS,
    RUN_METRICS_CSV,
    TASK_ORDER,
    bh_fdr,
    ensure_dir,
    fmt,
    load_or_build_run_metrics,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run simple PD clinical associations for the Parkinson walking dataset.")
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--participants-tsv", type=Path, default=PARTICIPANTS_PATH)
    parser.add_argument("--output-dir", type=Path, default=CLINICAL_DIR)
    parser.add_argument("--anchor", choices=("auto", "cohort", "subject"), default="auto")
    parser.add_argument("--rebuild-run-metrics", action="store_true")
    return parser.parse_args()


def association_rows(run_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    pd_runs = run_metrics[run_metrics["group"] == "PD"].copy()
    metric_columns = [metric for metric in RUN_METRIC_COLUMNS if metric in run_metrics.columns]
    for task in TASK_ORDER:
        task_frame = pd_runs[pd_runs["task"] == task].copy()
        for variable in PD_CLINICAL_COLUMNS:
            x = pd.to_numeric(task_frame[variable], errors="coerce")
            if x.notna().sum() < 8 or x.nunique(dropna=True) < 3:
                continue
            for metric in metric_columns:
                y = pd.to_numeric(task_frame[metric], errors="coerce")
                valid = x.notna() & y.notna()
                if valid.sum() < 8:
                    continue
                if x[valid].nunique(dropna=True) < 3 or y[valid].nunique(dropna=True) < 3:
                    continue
                rho, p_value = stats.spearmanr(x[valid], y[valid])
                rows.append(
                    {
                        "task": task,
                        "group": "PD",
                        "clinical_variable": variable,
                        "metric": metric,
                        "n_subjects": int(valid.sum()),
                        "rho": float(rho) if np.isfinite(rho) else np.nan,
                        "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
                    }
                )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["q_value"] = frame.groupby(["task", "clinical_variable"], dropna=False)["p_value"].transform(bh_fdr)
    frame["abs_rho"] = pd.to_numeric(frame["rho"], errors="coerce").abs()
    return frame.sort_values(["task", "clinical_variable", "q_value", "p_value", "abs_rho"], ascending=[True, True, True, True, False]).reset_index(drop=True)


def build_markdown(associations: pd.DataFrame, *, anchor: str) -> str:
    lines = [
        "# Parkinson walking clinical associations",
        "",
        "This pass keeps the associations deliberately simple:",
        "",
        f"- Anchor mode: `{anchor}`",
        "- PD participants only",
        "- Spearman correlations",
        "- Separate `rest` and `walk` tables",
        "- BH-FDR within each task x clinical-variable block",
        "",
    ]
    if associations.empty:
        lines.extend(["No clinical associations were estimable.", ""])
        return "\n".join(lines)
    for task in TASK_ORDER:
        task_frame = associations[associations["task"] == task]
        if task_frame.empty:
            continue
        lines.extend([f"## {task}", ""])
        for variable in PD_CLINICAL_COLUMNS:
            block = task_frame[task_frame["clinical_variable"] == variable].head(5)
            if block.empty:
                continue
            lines.extend([f"### {variable}", ""])
            for _, row in block.iterrows():
                lines.append(
                    f"- `{row['metric']}`: rho={fmt(row['rho'])}, p={fmt(row['p_value'])}, q={fmt(row['q_value'])}, n={int(row['n_subjects'])}"
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

    associations = association_rows(run_metrics)
    if not associations.empty:
        associations.to_csv(args.output_dir / "pd_clinical_associations.csv", index=False)
    (args.output_dir / "clinical_association_summary.md").write_text(build_markdown(associations, anchor=args.anchor), encoding="utf-8")

    manifest = {
        "dataset_root": str(args.dataset_root),
        "participants_tsv": str(args.participants_tsv),
        "output_dir": str(args.output_dir),
        "anchor": args.anchor,
        "run_metrics_csv": str(run_metrics_path),
        "group": "PD",
        "tasks": list(TASK_ORDER),
        "clinical_variables": list(PD_CLINICAL_COLUMNS),
        "n_rows": int(len(associations)),
    }
    write_json(args.output_dir / "clinical_association_manifest.json", manifest)

    print(f"Wrote clinical associations to {args.output_dir}")
    print(f"Association rows: {len(associations)}")


if __name__ == "__main__":
    main()
