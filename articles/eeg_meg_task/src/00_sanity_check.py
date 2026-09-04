"""Audit ds003645 MEEG coverage and the regional EEG-collapse limitation."""

from __future__ import annotations

import argparse

import h5py
import numpy as np
import pandas as pd

from eeg_meg_support import DATASET_ROOT, RESULTS_DIR, feature_names_and_values, h5_metadata, list_h5_paths, write_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", default=DATASET_ROOT)
    parser.add_argument("--output-dir", default=RESULTS_DIR / "00_sanity_check")
    return parser.parse_args()


def _collapse_status(handle: h5py.File, modality: str) -> tuple[bool, float]:
    names = sorted(name for name in handle["regional_mnps"] if name.startswith(f"{modality}_"))
    if not names:
        return False, float("nan")
    arrays = [np.asarray(handle[f"regional_mnps/{name}/mnps"][:], dtype=float) for name in names]
    reference = arrays[0]
    max_abs_delta = max(
        float(np.nanmax(np.abs(reference - candidate))) for candidate in arrays[1:]
    ) if len(arrays) > 1 else 0.0
    return bool(max_abs_delta <= 1e-7), max_abs_delta


def main() -> None:
    args = parse_args()
    h5_paths = list_h5_paths(args.dataset_root)
    if not h5_paths:
        raise FileNotFoundError(f"No participant H5 files found under {args.dataset_root}")

    rows: list[dict[str, object]] = []
    for h5_path in h5_paths:
        with h5py.File(h5_path, "r") as handle:
            row = h5_metadata(handle, h5_path)
            _, values = feature_names_and_values(handle)
            eeg_collapsed, eeg_delta = _collapse_status(handle, "eeg")
            meg_collapsed, meg_delta = _collapse_status(handle, "meg")
            row.update(
                n_timepoints=int(handle["mnps_3d"].shape[0]),
                mnps_finite=bool(np.isfinite(handle["mnps_3d"][:]).all()),
                coords9d_finite=bool(np.isfinite(handle["coords_9d/values"][:]).all()),
                has_eeg_fraction=float(np.mean(handle["row_source/has_eeg"][:] > 0)),
                has_meg_fraction=float(np.mean(handle["row_source/has_meg"][:] > 0)),
                eeg_feature_count=sum(name.startswith("eeg_") for name in feature_names_and_values(handle)[0]),
                meg_feature_count=sum(name.startswith("meg_") for name in feature_names_and_values(handle)[0]),
                feature_rows=int(values.shape[0]),
                eeg_regional_mnps_collapsed=eeg_collapsed,
                eeg_regional_mnps_max_abs_delta=eeg_delta,
                meg_regional_mnps_collapsed=meg_collapsed,
                meg_regional_mnps_max_abs_delta=meg_delta,
            )
            rows.append(row)

    runs = pd.DataFrame(rows).sort_values(["subject_id", "run"])
    summary = pd.DataFrame(
        [
            {
                "n_runs": len(runs),
                "n_subjects": runs["subject_id"].nunique(),
                "all_group_healthy": bool((runs["group"] == "Healthy").all()),
                "median_timepoints": float(runs["n_timepoints"].median()),
                "all_global_mnps_finite": bool(runs["mnps_finite"].all()),
                "all_coords9d_finite": bool(runs["coords9d_finite"].all()),
                "runs_with_eeg_regional_mnps_collapsed": int(runs["eeg_regional_mnps_collapsed"].sum()),
                "runs_with_meg_regional_mnps_collapsed": int(runs["meg_regional_mnps_collapsed"].sum()),
            }
        ]
    )
    write_csv(runs, args.output_dir / "run_coverage_and_regional_audit.csv")
    write_csv(summary, args.output_dir / "sanity_summary.csv")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
