"""Summarize non-collapsed regional trajectories with ndt-analysis reachability."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from eeg_meg_support import (
    DATASET_ROOT,
    NDT_ANALYSIS_ROOT,
    RESULTS_DIR,
    TOPOLOGIES,
    h5_metadata,
    list_h5_paths,
    write_csv,
)

if str(NDT_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(NDT_ANALYSIS_ROOT))

from ndt_analysis.reachability_cones import ReachabilityConfig, summarize_reachability_h5  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", default=DATASET_ROOT)
    parser.add_argument("--output-dir", default=RESULTS_DIR / "04_regional_reachability")
    parser.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help="Optional smoke-test limit on participant-run H5 files.",
    )
    return parser.parse_args()


def _is_collapsed(handle: h5py.File, modality: str) -> bool:
    arrays = [
        np.asarray(handle[f"regional_mnps/{modality}_{topology}/mnps"][:], dtype=float)
        for topology in TOPOLOGIES
    ]
    return all(np.allclose(arrays[0], candidate, equal_nan=True) for candidate in arrays[1:])


def main() -> None:
    args = parse_args()
    config = ReachabilityConfig(
        space="3d",
        k=15,
        horizon=2,
        max_points=300,
        persistence_window=7,
        standardize="zscore",
    )
    rows: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []

    h5_paths = list_h5_paths(args.dataset_root)
    if args.max_runs is not None:
        h5_paths = h5_paths[: args.max_runs]
    for run_index, h5_path in enumerate(h5_paths, start=1):
        print(f"Reachability run {run_index}/{len(h5_paths)}: {h5_path.name}", flush=True)
        with h5py.File(h5_path, "r") as handle:
            metadata = h5_metadata(handle, h5_path)
            eeg_collapsed = _is_collapsed(handle, "eeg")
        for modality in ("eeg", "meg"):
            if modality == "eeg" and eeg_collapsed:
                skipped.append({**metadata, "modality": "EEG", "reason": "regional_mnps_collapsed"})
                continue
            for topology in TOPOLOGIES:
                summary = summarize_reachability_h5(
                    h5_path,
                    config=config,
                    coordinate_contract="subject_anchored",
                    dataset_path=f"/regional_mnps/{modality}_{topology}/mnps",
                    used_space_override="regional_mnps_3d",
                    flat_overrides={
                        "modality": modality.upper(),
                        "topology": topology,
                        "source_dataset_path": f"/regional_mnps/{modality}_{topology}/mnps",
                    },
                )
                rows.append({**metadata, **summary["flat"]})

    write_csv(pd.DataFrame(rows), Path(args.output_dir) / "regional_reachability_meg.csv")
    write_csv(pd.DataFrame(skipped), Path(args.output_dir) / "regional_reachability_skipped.csv")
    print(f"Wrote {len(rows)} reachability rows; skipped {len(skipped)} collapsed EEG runs.")


if __name__ == "__main__":
    main()
