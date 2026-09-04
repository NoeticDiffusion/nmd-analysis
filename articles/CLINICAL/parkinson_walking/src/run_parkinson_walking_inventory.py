from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from parkinson_walking_support import (
    DATASET_ROOT,
    INVENTORY_DIR,
    NUMERIC_PARTICIPANT_COLUMNS,
    PARTICIPANTS_PATH,
    RUN_METRICS_CSV,
    TASK_ORDER,
    ensure_dir,
    fmt,
    load_or_build_run_metrics,
    load_participants,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a simple inventory for the Parkinson walking dataset.")
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--participants-tsv", type=Path, default=PARTICIPANTS_PATH)
    parser.add_argument("--output-dir", type=Path, default=INVENTORY_DIR)
    parser.add_argument("--rebuild-run-metrics", action="store_true")
    return parser.parse_args()


def subject_task_availability(run_metrics: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        run_metrics.groupby(["participant_id", "group"], observed=True)["task"]
        .agg(lambda values: sorted({str(value) for value in values if pd.notna(value)}))
        .reset_index()
    )
    grouped["has_rest"] = grouped["task"].map(lambda values: "rest" in values)
    grouped["has_walk"] = grouped["task"].map(lambda values: "walk" in values)
    grouped["task_availability"] = grouped.apply(
        lambda row: "both" if row["has_rest"] and row["has_walk"] else ("rest_only" if row["has_rest"] else "walk_only"),
        axis=1,
    )
    return grouped.sort_values(["group", "participant_id"]).reset_index(drop=True)


def participant_numeric_summary(participants: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for group, group_frame in participants.groupby("group", dropna=False, observed=True):
        for column in NUMERIC_PARTICIPANT_COLUMNS:
            values = pd.to_numeric(group_frame[column], errors="coerce")
            rows.append(
                {
                    "group": group,
                    "variable": column,
                    "n_non_missing": int(values.notna().sum()),
                    "mean": float(values.mean()) if values.notna().any() else float("nan"),
                    "median": float(values.median()) if values.notna().any() else float("nan"),
                    "std": float(values.std(ddof=1)) if values.notna().sum() >= 2 else float("nan"),
                    "min": float(values.min()) if values.notna().any() else float("nan"),
                    "max": float(values.max()) if values.notna().any() else float("nan"),
                }
            )
    return pd.DataFrame(rows)


def metadata_coverage(participants: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for column in ("sex", *NUMERIC_PARTICIPANT_COLUMNS):
        for group, group_frame in participants.groupby("group", dropna=False, observed=True):
            rows.append(
                {
                    "variable": column,
                    "group": group,
                    "n_total": int(len(group_frame)),
                    "n_non_missing": int(group_frame[column].notna().sum()),
                }
            )
    return pd.DataFrame(rows)


def build_markdown(
    run_metrics: pd.DataFrame,
    group_task_counts: pd.DataFrame,
    availability_counts: pd.DataFrame,
    metadata_summary: pd.DataFrame,
) -> str:
    lines = [
        "# Parkinson walking inventory",
        "",
        f"- Runs in bundle: `{len(run_metrics)}`",
        f"- Unique participants in bundle: `{run_metrics['participant_id'].nunique()}`",
        "",
        "## Group x task counts",
        "",
    ]
    for _, row in group_task_counts.iterrows():
        lines.append(f"- `{row['group']}` / `{row['task']}`: `{int(row['n_runs'])}` runs")
    lines.extend(["", "## Task availability by group", ""])
    for _, row in availability_counts.iterrows():
        lines.append(f"- `{row['group']}` / `{row['task_availability']}`: `{int(row['n_subjects'])}` participants")
    lines.extend(["", "## Numeric metadata coverage", ""])
    for variable in NUMERIC_PARTICIPANT_COLUMNS:
        subset = metadata_summary[metadata_summary["variable"] == variable]
        if subset.empty:
            continue
        parts = [f"{row['group']}: {int(row['n_non_missing'])}/{int(row['n_total'])}" for _, row in subset.iterrows()]
        lines.append(f"- `{variable}` -> {', '.join(parts)}")
    lines.extend(["", "## Quick read", ""])
    both = availability_counts[availability_counts["task_availability"] == "both"]
    for _, row in both.iterrows():
        lines.append(f"- `{row['group']}` has `{int(row['n_subjects'])}` participants with both `rest` and `walk`.")
    return "\n".join(lines) + "\n"


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
    participants = load_participants(args.participants_tsv)

    inventory_columns = [
        "participant_id",
        "source_subject_code",
        "group",
        "task",
        "sex",
        "age",
        "h5_path",
        "n_timepoints",
        "n_jacobian_windows",
        "coverage_seconds_effective",
        "epochs_raw",
        "epochs_after_qc",
    ]
    run_inventory = run_metrics[inventory_columns].copy()
    group_task_counts = (
        run_metrics.groupby(["group", "task"], observed=True)
        .size()
        .reset_index(name="n_runs")
        .sort_values(["group", "task"])
        .reset_index(drop=True)
    )
    availability = subject_task_availability(run_metrics)
    availability_counts = (
        availability.groupby(["group", "task_availability"], observed=True)
        .size()
        .reset_index(name="n_subjects")
        .sort_values(["group", "task_availability"])
        .reset_index(drop=True)
    )
    metadata_summary = metadata_coverage(participants)
    numeric_summary = participant_numeric_summary(participants)

    run_inventory.to_csv(args.output_dir / "bundle_run_inventory.csv", index=False)
    group_task_counts.to_csv(args.output_dir / "group_task_counts.csv", index=False)
    availability.to_csv(args.output_dir / "subject_task_availability.csv", index=False)
    availability_counts.to_csv(args.output_dir / "subject_task_availability_counts.csv", index=False)
    metadata_summary.to_csv(args.output_dir / "participant_metadata_coverage.csv", index=False)
    numeric_summary.to_csv(args.output_dir / "participant_numeric_summary.csv", index=False)
    (args.output_dir / "inventory_summary.md").write_text(
        build_markdown(run_metrics, group_task_counts, availability_counts, metadata_summary),
        encoding="utf-8",
    )

    manifest = {
        "dataset_root": str(args.dataset_root),
        "participants_tsv": str(args.participants_tsv),
        "output_dir": str(args.output_dir),
        "run_metrics_csv": str(run_metrics_path),
        "n_runs": int(len(run_metrics)),
        "n_unique_participants": int(run_metrics["participant_id"].nunique()),
        "group_task_counts": group_task_counts.to_dict(orient="records"),
        "subject_task_availability_counts": availability_counts.to_dict(orient="records"),
        "mean_coverage_seconds_by_task": {
            str(task): float(
                pd.to_numeric(run_metrics.loc[run_metrics["task"] == task, "coverage_seconds_effective"], errors="coerce").mean()
            )
            for task in TASK_ORDER
        },
    }
    write_json(args.output_dir / "inventory_manifest.json", manifest)

    print(f"Wrote inventory to {args.output_dir}")
    print(f"Runs: {len(run_metrics)} | participants: {run_metrics['participant_id'].nunique()}")
    print(
        "Coverage seconds means: "
        + ", ".join(
            f"{task}={fmt(pd.to_numeric(run_metrics.loc[run_metrics['task'] == task, 'coverage_seconds_effective'], errors='coerce').mean())}"
            for task in TASK_ORDER
        )
    )


if __name__ == "__main__":
    main()
