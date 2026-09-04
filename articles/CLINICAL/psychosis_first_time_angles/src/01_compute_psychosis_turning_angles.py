"""Extract subject-level turning-angle features for ds003944 and ds003947."""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

import psychosis_angle_support as support


ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RUN_TAG = "psychosis_angles_20260719"


@dataclass(frozen=True)
class Config:
    output_root: Path
    coordinate_contract: str
    datasets: tuple[str, ...]
    n_perms: int
    workers: int
    limit_subjects: int | None
    raw_roots: Dict[str, Path | None]


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Compute psychosis turning-angle features from NMD H5 exports.")
    parser.add_argument("--output-root", type=Path, default=ARTICLE_DIR / "results" / DEFAULT_RUN_TAG)
    parser.add_argument("--coordinate-contract", choices=["cohort_anchored", "subject_anchored"], default="cohort_anchored")
    parser.add_argument("--dataset", choices=["both", *support.DATASETS], default="both")
    parser.add_argument("--n-perms", type=int, default=support.N_PERMUTATIONS)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--limit-subjects", type=int, default=None)
    parser.add_argument("--raw-root-ds003944", type=Path, default=None)
    parser.add_argument("--raw-root-ds003947", type=Path, default=None)
    args = parser.parse_args()
    datasets = support.DATASETS if args.dataset == "both" else (args.dataset,)
    return Config(
        output_root=args.output_root,
        coordinate_contract=args.coordinate_contract,
        datasets=datasets,
        n_perms=max(0, args.n_perms),
        workers=max(1, args.workers),
        limit_subjects=args.limit_subjects,
        raw_roots={"ds003944": args.raw_root_ds003944, "ds003947": args.raw_root_ds003947},
    )


def load_subjects(dataset: str, config: Config) -> tuple[list[Dict[str, Any]], pd.DataFrame]:
    paths = support.discover_h5_files(dataset, config.raw_roots[dataset])
    if config.limit_subjects is not None:
        paths = paths[: config.limit_subjects]
    subjects: list[Dict[str, Any]] = []
    qc: list[Dict[str, Any]] = []
    for path in paths:
        try:
            subject = support.read_subject_h5(path, config.coordinate_contract)
            if subject is None:
                qc.append({"dataset": dataset, "path": str(path), "status": "missing_coordinate_layer"})
                continue
            if subject["group"] is None:
                qc.append({"dataset": dataset, "path": str(path), "status": "unrecognized_group"})
                continue
            charts = support.chart_arrays(subject)
            if len(charts) != len(support.CHARTS):
                qc.append({"dataset": dataset, "path": str(path), "status": "missing_chart_columns"})
                continue
            subject["dataset"] = dataset
            subject["charts"] = charts
            subject["segments"] = support.contiguous_segments(subject["time"])
            subjects.append(subject)
            qc.append(
                {
                    "dataset": dataset,
                    "subject": subject["subject"],
                    "path": str(path),
                    "group": subject["group"],
                    "status": "ok",
                    "n_epochs": int(subject["time"].size),
                    "n_contiguous_segments": len(subject["segments"]),
                }
            )
        except Exception as exc:
            qc.append({"dataset": dataset, "path": str(path), "status": "read_error", "detail": repr(exc)})
    return subjects, pd.DataFrame(qc)


def pooled_thresholds(subjects: list[Dict[str, Any]]) -> Dict[tuple[str, int], float]:
    values: Dict[tuple[str, int], list[np.ndarray]] = {
        (chart, lag): [] for chart in support.CHARTS for lag in support.LAGS
    }
    for subject in subjects:
        for chart, coords in subject["charts"].items():
            for lag in support.LAGS:
                steps = support.segment_step_lengths(coords, subject["segments"], lag)
                steps = steps[np.isfinite(steps)]
                if steps.size:
                    values[(chart, lag)].append(steps)
    return {
        key: float(np.percentile(np.concatenate(chunks), support.STEP_LENGTH_FILTER_PERCENTILE)) if chunks else 0.0
        for key, chunks in values.items()
    }


def process_subject(
    subject: Dict[str, Any], thresholds: Dict[tuple[str, int], float], n_perms: int
) -> list[Dict[str, Any]]:
    meta = {
        "dataset": subject["dataset"],
        "subject": subject["subject"],
        "source_h5_path": subject["path"],
        "group": subject["group"],
        "cpz_at_scan": subject["participant"].get("CPZ_at_scan"),
        "coordinate_contract": subject["coordinate_contract"],
        "n_epochs": int(subject["time"].size),
        "n_contiguous_segments": len(subject["segments"]),
    }
    rows: list[Dict[str, Any]] = []
    for chart, coords in subject["charts"].items():
        for lag in support.LAGS:
            threshold = thresholds[(chart, lag)]
            triples = support.compute_turning_triples(coords, subject["segments"], lag, threshold)
            base = {**meta, "chart": chart, "lag_epochs": lag, "step_length_threshold": threshold}
            if triples is None:
                rows.append({**base, "status": "insufficient_valid_angles"})
                continue
            theta = triples["theta_deg"]
            median = float(np.median(theta))
            z, null_mean, null_sd = support.permutation_null_z(
                triples["disp_units"],
                median,
                seed=support.stable_seed(subject["dataset"], subject["subject"], chart, lag, subject["coordinate_contract"]),
                n_perms=n_perms,
            )
            rows.append(
                {
                    **base,
                    "status": "ok",
                    "n_valid": triples["n_valid"],
                    "n_excluded_short_step": triples["n_excluded_short_step"],
                    "n_total_triples": triples["n_total_triples"],
                    "turn_cos_mean": float(np.mean(triples["cos_theta"])),
                    "turn_angle_median": median,
                    "turn_angle_mad": float(np.median(np.abs(theta - median))),
                    "turn_angle_iqr": float(np.percentile(theta, 75) - np.percentile(theta, 25)),
                    "turn_angle_p90": float(np.percentile(theta, 90)),
                    "turn_fraction_gt_90": float(np.mean(theta > 90.0)),
                    "turn_fraction_gt_120": float(np.mean(theta > 120.0)),
                    "turn_entropy": support.angle_entropy(theta),
                    "turn_length_coupling": support.turn_length_coupling(theta, triples["mean_step_length"]),
                    "null_z_median_angle": z,
                    "null_mean_median_angle": null_mean,
                    "null_sd_median_angle": null_sd,
                }
            )
    return rows


def run_dataset(dataset: str, config: Config) -> None:
    subjects, qc = load_subjects(dataset, config)
    out_dir = config.output_root / config.coordinate_contract / dataset
    out_dir.mkdir(parents=True, exist_ok=True)
    qc.to_csv(out_dir / "subject_read_qc.csv", index=False)
    if not subjects:
        raise FileNotFoundError(
            f"No usable {dataset} H5 subjects. Supply --raw-root-{dataset} or place exports under {support.RAW_ROOTS[dataset][0]}"
        )
    thresholds = pooled_thresholds(subjects)
    if config.workers == 1:
        rows = [row for subject in subjects for row in process_subject(subject, thresholds, config.n_perms)]
    else:
        rows = []
        with ProcessPoolExecutor(max_workers=config.workers) as executor:
            futures = [executor.submit(process_subject, subject, thresholds, config.n_perms) for subject in subjects]
            for index, future in enumerate(futures, 1):
                rows.extend(future.result())
                print(f"[{dataset}] Processed {index}/{len(futures)} subjects.", flush=True)
    features = pd.DataFrame(rows)
    features.to_csv(out_dir / "subject_turning_features.csv", index=False)
    (out_dir / "manifest.json").write_text(
        json.dumps(
            {
                "dataset": dataset,
                "coordinate_contract": config.coordinate_contract,
                "n_subjects_usable": len(subjects),
                "n_permutations": config.n_perms,
                "thresholds": {f"{chart}__lag{lag}": value for (chart, lag), value in thresholds.items()},
                "group_counts": pd.Series([subject["group"] for subject in subjects]).value_counts().to_dict(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[{dataset}] Wrote {len(features)} subject x chart x lag rows to {out_dir}")


def main() -> None:
    config = parse_args()
    for dataset in config.datasets:
        run_dataset(dataset, config)


if __name__ == "__main__":
    sys.exit(main())
