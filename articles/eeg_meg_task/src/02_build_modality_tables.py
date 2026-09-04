"""Build article-local global and regional EEG--MEG summary tables from H5."""

from __future__ import annotations

import argparse
from collections import defaultdict

import h5py
import numpy as np
import pandas as pd

from eeg_meg_support import (
    DATASET_ROOT,
    MNPS_AXES,
    RESULTS_DIR,
    TOPOLOGIES,
    family_from_name,
    feature_names_and_values,
    h5_metadata,
    list_h5_paths,
    nan_summary,
    topography_from_name,
    write_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", default=DATASET_ROOT)
    parser.add_argument("--output-dir", default=RESULTS_DIR / "02_modality_tables")
    return parser.parse_args()


def _feature_rows(
    metadata: dict[str, object], names: list[str], values: np.ndarray
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, name in enumerate(names):
        topo = topography_from_name(name)
        if name.startswith("eeg_"):
            modality = "EEG"
        elif name.startswith("meg_"):
            modality = "MEG"
        else:
            continue
        # The sensor-combined meg_* surface is the directly paired shadow surface.
        if modality == "MEG" and name.startswith(("meg_mag_", "meg_grad_")):
            continue
        location = "regional" if topo is not None else "global"
        if location == "global" and "__g_" in name:
            continue
        summary = nan_summary(values[:, index])
        rows.append(
            {
                **metadata,
                "modality": modality,
                "level": location,
                "topology": topo or "global",
                "feature": name,
                "feature_family": family_from_name(name),
                **summary,
                "n_timepoints": int(values.shape[0]),
            }
        )
    return rows


def _regional_mnps_rows(handle: h5py.File, metadata: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for modality in ("EEG", "MEG"):
        prefix = modality.lower()
        for topo in TOPOLOGIES:
            name = f"{prefix}_{topo}"
            path = f"regional_mnps/{name}/mnps"
            if path not in handle:
                continue
            values = np.asarray(handle[path][:], dtype=float)
            for axis_idx, axis in enumerate(MNPS_AXES):
                rows.append(
                    {
                        **metadata,
                        "modality": modality,
                        "topology": topo,
                        "axis": axis,
                        **nan_summary(values[:, axis_idx]),
                        "n_timepoints": int(values.shape[0]),
                    }
                )
    return rows


def _pair_feature_rows(feature_table: pd.DataFrame) -> pd.DataFrame:
    keys = ["subject_id", "run", "level", "topology", "feature_family"]
    pivot = feature_table.pivot_table(index=keys, columns="modality", values="mean", aggfunc="first")
    paired = pivot.dropna(subset=["EEG", "MEG"]).reset_index()
    paired["eeg_minus_meg"] = paired["EEG"] - paired["MEG"]
    return paired


def main() -> None:
    args = parse_args()
    feature_rows: list[dict[str, object]] = []
    regional_rows: list[dict[str, object]] = []
    global_mnps_rows: list[dict[str, object]] = []

    for h5_path in list_h5_paths(args.dataset_root):
        with h5py.File(h5_path, "r") as handle:
            metadata = h5_metadata(handle, h5_path)
            names, values = feature_names_and_values(handle)
            feature_rows.extend(_feature_rows(metadata, names, values))
            regional_rows.extend(_regional_mnps_rows(handle, metadata))
            mnps = np.asarray(handle["mnps_3d"][:], dtype=float)
            for axis_idx, axis in enumerate(MNPS_AXES):
                global_mnps_rows.append(
                    {
                        **metadata,
                        "modality": "MEG_primary",
                        "axis": axis,
                        **nan_summary(mnps[:, axis_idx]),
                        "n_timepoints": int(mnps.shape[0]),
                        "mapping_primary_surface": str(handle.attrs.get("mapping_primary_surface", "")),
                    }
                )

    features = pd.DataFrame(feature_rows)
    regional_mnps = pd.DataFrame(regional_rows)
    global_mnps = pd.DataFrame(global_mnps_rows)
    paired_features = _pair_feature_rows(features)

    # A collapsed EEG regional MNPS cannot form six independent regional tests.
    regional_collapse = (
        regional_mnps.pivot_table(
            index=["subject_id", "run", "axis", "topology"],
            columns="modality",
            values="mean",
            aggfunc="first",
        )
        .reset_index()
    )
    write_csv(features, args.output_dir / "feature_summary_long.csv")
    write_csv(paired_features, args.output_dir / "paired_feature_means.csv")
    write_csv(regional_mnps, args.output_dir / "regional_mnps_summary_long.csv")
    write_csv(regional_collapse, args.output_dir / "regional_mnps_paired_audit.csv")
    write_csv(global_mnps, args.output_dir / "global_meg_primary_mnps_summary.csv")
    print(
        f"Wrote {len(features)} feature rows, {len(paired_features)} paired feature rows, "
        f"and {len(regional_mnps)} regional MNPS rows."
    )


if __name__ == "__main__":
    main()
