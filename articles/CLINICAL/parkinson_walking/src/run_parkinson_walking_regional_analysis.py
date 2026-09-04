from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy import stats

from parkinson_walking_support import (
    DATASET_ROOT,
    GROUP_ORDER,
    NETWORK_ORDER,
    PARTICIPANTS_PATH,
    PD_CLINICAL_COLUMNS,
    REGIONAL_RUN_METRIC_COLUMNS,
    RESULTS_DIR,
    TASK_ORDER,
    bh_fdr,
    cohens_d,
    ensure_dir,
    fmt,
    list_h5_paths,
    load_or_build_regional_run_metrics,
    write_json,
)


REGIONAL_DIR = RESULTS_DIR / "regional_analysis"
REGIONAL_RUN_METRICS_CSV = "regional_run_metrics.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run regional cohort/subject analyses for the Parkinson walking dataset."
    )
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--participants-tsv", type=Path, default=PARTICIPANTS_PATH)
    parser.add_argument("--output-dir", type=Path, default=REGIONAL_DIR)
    parser.add_argument("--anchor", choices=("auto", "cohort", "subject"), default="auto")
    parser.add_argument("--rebuild-run-metrics", action="store_true")
    return parser.parse_args()


def detect_reachability_presence(dataset_root: Path) -> bool:
    manifest_path = dataset_root / "run_manifest.json"
    if manifest_path.exists() and "reach" in manifest_path.read_text(encoding="utf-8", errors="ignore").lower():
        return True
    h5_paths = list_h5_paths(dataset_root)
    if not h5_paths:
        return False
    matches: list[str] = []
    with h5py.File(h5_paths[0], "r") as handle:
        handle.visit(matches.append)
    return any("reach" in name.lower() for name in matches)


def regional_group_rows(run_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for task in TASK_ORDER:
        task_frame = run_metrics[run_metrics["task"] == task].copy()
        for network in NETWORK_ORDER:
            network_frame = task_frame[task_frame["network"] == network].copy()
            left_frame = network_frame[network_frame["group"] == "HC"].copy()
            right_frame = network_frame[network_frame["group"] == "PD"].copy()
            for metric in REGIONAL_RUN_METRIC_COLUMNS:
                left = pd.to_numeric(left_frame[metric], errors="coerce").dropna().to_numpy(dtype=float)
                right = pd.to_numeric(right_frame[metric], errors="coerce").dropna().to_numpy(dtype=float)
                if left.size < 3 or right.size < 3:
                    continue
                stat, p_value = stats.mannwhitneyu(left, right, alternative="two-sided")
                rows.append(
                    {
                        "contrast_name": f"HC_vs_PD_{task}_regional",
                        "task": task,
                        "network": network,
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


def regional_clinical_rows(run_metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    pd_runs = run_metrics[run_metrics["group"] == "PD"].copy()
    for task in TASK_ORDER:
        task_frame = pd_runs[pd_runs["task"] == task].copy()
        for variable in PD_CLINICAL_COLUMNS:
            x_all = pd.to_numeric(task_frame[variable], errors="coerce")
            if x_all.notna().sum() < 8 or x_all.nunique(dropna=True) < 3:
                continue
            for network in NETWORK_ORDER:
                network_frame = task_frame[task_frame["network"] == network].copy()
                x = pd.to_numeric(network_frame[variable], errors="coerce")
                if x.notna().sum() < 8 or x.nunique(dropna=True) < 3:
                    continue
                for metric in REGIONAL_RUN_METRIC_COLUMNS:
                    y = pd.to_numeric(network_frame[metric], errors="coerce")
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
                            "network": network,
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


def build_markdown(group_contrasts: pd.DataFrame, clinical_associations: pd.DataFrame, *, anchor: str, reachability_present: bool) -> str:
    lines = [
        "# Parkinson walking regional analysis",
        "",
        f"- Anchor mode: `{anchor}`",
        f"- Reachability present in bundle: `{reachability_present}`",
        "- Regional source spaces: 3D MNPS, 9D stratified coordinates, and regional 3D Jacobian summaries",
        "- Group test: HC vs PD within task via Mann-Whitney U",
        "- Clinical test: PD-only Spearman rho per task",
        "",
    ]
    lines.extend(["## Top HC vs PD regional rows", ""])
    if group_contrasts.empty:
        lines.extend(["No regional group contrasts were estimable.", ""])
    else:
        for _, row in group_contrasts.head(12).iterrows():
            lines.append(
                f"- `{row['task']}` / `{row['network']}` / `{row['metric']}`: "
                f"HC median={fmt(row['left_median'])}, PD median={fmt(row['right_median'])}, "
                f"d={fmt(row['effect_size'])}, p={fmt(row['p_value'])}, q={fmt(row['q_value'])}"
            )
        lines.append("")
    lines.extend(["## Top rho rows", ""])
    if clinical_associations.empty:
        lines.extend(["No regional clinical rho rows were estimable.", ""])
    else:
        hits = clinical_associations[clinical_associations["q_value"] < 0.1].copy()
        source = hits if not hits.empty else clinical_associations.head(12)
        for _, row in source.head(12).iterrows():
            lines.append(
                f"- `{row['task']}` / `{row['clinical_variable']}` / `{row['network']}` / `{row['metric']}`: "
                f"rho={fmt(row['rho'])}, p={fmt(row['p_value'])}, q={fmt(row['q_value'])}, n={int(row['n_subjects'])}"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    run_metrics_filename = REGIONAL_RUN_METRICS_CSV if args.anchor == "auto" else f"regional_run_metrics_{args.anchor}.csv"
    run_metrics_path = args.output_dir / run_metrics_filename
    run_metrics = load_or_build_regional_run_metrics(
        run_metrics_path,
        dataset_root=args.dataset_root,
        participants_path=args.participants_tsv,
        rebuild=args.rebuild_run_metrics,
        anchor=args.anchor,
    )
    group_contrasts = regional_group_rows(run_metrics)
    clinical_associations = regional_clinical_rows(run_metrics)
    if not group_contrasts.empty:
        group_contrasts.to_csv(args.output_dir / "regional_group_contrasts.csv", index=False)
    if not clinical_associations.empty:
        clinical_associations.to_csv(args.output_dir / "regional_pd_clinical_associations.csv", index=False)
    reachability_present = detect_reachability_presence(args.dataset_root)
    (args.output_dir / "regional_summary.md").write_text(
        build_markdown(group_contrasts, clinical_associations, anchor=args.anchor, reachability_present=reachability_present),
        encoding="utf-8",
    )
    manifest = {
        "dataset_root": str(args.dataset_root),
        "participants_tsv": str(args.participants_tsv),
        "output_dir": str(args.output_dir),
        "anchor": args.anchor,
        "regional_run_metrics_csv": str(run_metrics_path),
        "n_regional_rows": int(len(run_metrics)),
        "n_group_rows": int(len(group_contrasts)),
        "n_clinical_rows": int(len(clinical_associations)),
        "reachability_present_in_bundle": bool(reachability_present),
        "networks": list(NETWORK_ORDER),
    }
    write_json(args.output_dir / "regional_manifest.json", manifest)
    print(f"Wrote regional analysis to {args.output_dir}")
    print(f"Regional rows: {len(run_metrics)} | group rows: {len(group_contrasts)} | rho rows: {len(clinical_associations)}")


if __name__ == "__main__":
    main()
