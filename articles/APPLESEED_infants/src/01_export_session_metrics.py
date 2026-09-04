"""Export one QC-audited NDT metric row per APPLESEED subject and session."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from appleseed_support import (
    CONVENTIONAL_ENDPOINTS,
    COORDINATE_CONTRACT,
    DEFAULT_DATA_ROOT,
    DEFAULT_RESULTS_ROOT,
    NDT_ANALYSIS_ROOT,
    finite_median,
    h5_paths,
    participant_metadata,
    session_identity,
)

from ndt_analysis.h5_contract import read_geometry_contract_state, resolve_coords_3d, resolve_coords_9d, resolve_jacobian_3d, resolve_jacobian_9d
from ndt_analysis.legacy_adapters import _base_h5_metadata_from_handle, _summarize_global_mnps_jacobian_row
from ndt_analysis.reachability_cones import ReachabilityConfig, summarize_reachability_h5

REACHABILITY_CONFIG = ReachabilityConfig(space="3d", k=12, horizon=3, standardize="none")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RESULTS_ROOT / "01_session_metrics")
    parser.add_argument("--limit-sessions", type=int, default=None)
    return parser.parse_args()


def _feature_medians(handle: h5py.File) -> dict[str, float]:
    if "features_raw/values" not in handle or "features_raw/names" not in handle:
        return {key: np.nan for key in CONVENTIONAL_ENDPOINTS}
    names = [item.decode() if isinstance(item, bytes) else str(item) for item in handle["features_raw/names"][:]]
    values = np.asarray(handle["features_raw/values"][:], dtype=float)
    output = {}
    for endpoint in CONVENTIONAL_ENDPOINTS:
        try:
            output[endpoint] = finite_median(values[:, names.index(endpoint)])
        except ValueError:
            output[endpoint] = np.nan
    return output


def export_one(h5_path: Path) -> tuple[dict, dict]:
    """Read NDT metrics and their supporting contract/QC from one H5."""
    identity = session_identity(h5_path)
    with h5py.File(h5_path, "r") as handle:
        contract = read_geometry_contract_state(handle)
        coords_3d = resolve_coords_3d(handle, COORDINATE_CONTRACT)
        coords_9d = resolve_coords_9d(handle, COORDINATE_CONTRACT)
        resolved = resolve_jacobian_3d(handle, COORDINATE_CONTRACT)
        if resolved is None or coords_3d is None:
            raise ValueError(f"Could not resolve 3D Jacobian: {h5_path}")
        base = _base_h5_metadata_from_handle(handle, h5_path)
        base.update(resolved.provenance())
        mnj = _summarize_global_mnps_jacobian_row(
            base,
            resolved.j_hat,
            resolved.j_dot,
            source_dataset_path=resolved.dataset_path,
            dims=3,
        )
        if mnj is None:
            raise ValueError(f"Could not summarize Jacobian: {h5_path}")
        resolved_9d = resolve_jacobian_9d(handle, COORDINATE_CONTRACT)
        mnj_9d = None
        if resolved_9d is not None:
            base_9d = _base_h5_metadata_from_handle(handle, h5_path)
            base_9d.update(resolved_9d.provenance())
            mnj_9d = _summarize_global_mnps_jacobian_row(
                base_9d,
                resolved_9d.j_hat,
                resolved_9d.j_dot,
                source_dataset_path=resolved_9d.dataset_path,
                dims=9,
            )
        participant = participant_metadata(handle)
        anchor_group = handle.get("feature_anchors/spec")
        anchor_id = anchor_group.attrs.get("anchor_id") if anchor_group is not None else None
        anchor_hash = anchor_group.attrs.get("anchor_hash") if anchor_group is not None else None
        row = {
            **identity,
            "sex": participant.get("sex"),
            "source_group": participant.get("group"),
            "n_timepoints": int(handle["/coords_3d_cohort_anchored/values"].shape[0])
            if "/coords_3d_cohort_anchored/values" in handle
            else np.nan,
            "geometry_contract_status": contract.status,
            "geometry_invalidity_policy": contract.invalidity_policy,
            "geometry_coords_9d_degenerate_axes": ",".join(contract.coords_9d_degenerate_axes),
            "geometry_jacobian_9d_windows_retained": contract.jacobian_9d_windows_retained,
            "geometry_jacobian_9d_invalid_windows": contract.jacobian_9d_invalid_windows,
            "requested_coordinate_contract": COORDINATE_CONTRACT,
            "resolved_coordinate_contract": resolved.resolved_coordinate_contract,
            "cohort_anchor_id": anchor_id.decode() if isinstance(anchor_id, bytes) else anchor_id,
            "cohort_anchor_hash": anchor_hash.decode() if isinstance(anchor_hash, bytes) else anchor_hash,
            "jacobian_9d_available": bool(mnj_9d is not None),
            **_feature_medians(handle),
        }
        for index, axis in enumerate(("m", "d", "e")):
            row[f"cohort_{axis}_median"] = finite_median(coords_3d.values[:, index])
        if coords_9d is not None:
            for index, name in enumerate(coords_9d.names):
                row[f"cohort_9d_{name}_median"] = finite_median(coords_9d.values[:, index])
        row.update({key: value for key, value in mnj.items() if key.endswith(("_median", "_mean"))})
        if mnj_9d is not None:
            row.update({f"mn9d_{key}": value for key, value in mnj_9d.items() if key.endswith(("_median", "_mean"))})
        qc = {
            **identity,
            "geometry_contract_status": contract.status,
            "geometry_jacobian_9d_invalid_windows": contract.jacobian_9d_invalid_windows,
            "jacobian_9d_available": bool(mnj_9d is not None),
            "n_bad_eeg_channels": int(handle.attrs.get("n_bad_eeg_channels", 0)),
            "epochs_raw": int(handle.attrs.get("epochs_raw", 0)),
            "epochs_after_qc": int(handle.attrs.get("epochs_after_qc", 0)),
            "dropped_geometry_invalid_epochs": int(handle.attrs.get("dropped_geometry_invalid_epochs", 0)),
            "stage_fraction_labeled": float(handle.attrs.get("stage_frac_labeled", np.nan)),
        }

    reachability = summarize_reachability_h5(
        h5_path,
        REACHABILITY_CONFIG,
        coordinate_contract=COORDINATE_CONTRACT,
    )["flat"]
    for key in (
        "tube_log_det_median",
        "tube_d_eff_median",
        "tube_kappa_median",
        "tube_dir_entropy_median",
        "tube_rotation_median",
        "near_singular_rate",
        "finite_ok",
        "not_testable",
    ):
        row[key] = reachability.get(key, np.nan)
    return row, qc


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    paths = h5_paths(args.data_root)
    if args.limit_sessions:
        paths = paths[: args.limit_sessions]
    rows, qc_rows = zip(*(export_one(path) for path in paths))
    metrics = pd.DataFrame(rows).sort_values(["subject_id", "session"])
    qc = pd.DataFrame(qc_rows).sort_values(["subject_id", "session"])
    metrics.to_csv(args.output_dir / "session_metrics.csv", index=False)
    qc.to_csv(args.output_dir / "session_qc.csv", index=False)
    manifest = {
        "data_root": str(args.data_root),
        "n_h5": len(paths),
        "n_subjects": int(metrics["subject_id"].nunique()),
        "complete_subjects": int((metrics.groupby("subject_id").size() == 4).sum()),
        "coordinate_contract": COORDINATE_CONTRACT,
        "reachability_config": REACHABILITY_CONFIG.__dict__,
        "geometry_status_counts": qc["geometry_contract_status"].value_counts(dropna=False).to_dict(),
        "jacobian_9d_available_sessions": int(qc["jacobian_9d_available"].sum()),
        "cohort_anchor_ids": sorted(metrics["cohort_anchor_id"].dropna().unique().tolist()),
        "cohort_anchor_hashes": sorted(metrics["cohort_anchor_hash"].dropna().unique().tolist()),
    }
    (args.output_dir / "export_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
