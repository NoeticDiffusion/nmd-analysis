"""Export QC-audited, visit-level MNPS/MNJ summaries for Figshare infant EEG."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from figshare_infant_support import (
    COORDINATE_CONTRACT,
    SUBJECT_COORDINATE_CONTRACT,
    DEFAULT_DATA_ROOT,
    DEFAULT_RESULTS_ROOT,
    PRIMARY_ENDPOINTS,
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


def export_one(h5_path: Path) -> tuple[dict, dict]:
    with h5py.File(h5_path, "r") as handle:
        participant = participant_metadata(handle)
        identity = session_identity(h5_path, participant)
        contract = read_geometry_contract_state(handle)
        coords_3d = resolve_coords_3d(handle, COORDINATE_CONTRACT)
        coords_9d = resolve_coords_9d(handle, COORDINATE_CONTRACT)
        subject_coords_3d = resolve_coords_3d(handle, SUBJECT_COORDINATE_CONTRACT)
        subject_coords_9d = resolve_coords_9d(handle, SUBJECT_COORDINATE_CONTRACT)
        resolved = resolve_jacobian_3d(handle, COORDINATE_CONTRACT)
        if resolved is None or coords_3d is None:
            raise ValueError(f"Missing {COORDINATE_CONTRACT} 3D Jacobian/coordinates: {h5_path}")
        base = _base_h5_metadata_from_handle(handle, h5_path)
        base.update(resolved.provenance())
        mnj = _summarize_global_mnps_jacobian_row(
            base, resolved.j_hat, resolved.j_dot, source_dataset_path=resolved.dataset_path, dims=3
        )
        if mnj is None:
            raise ValueError(f"Could not summarize 3D MNJ: {h5_path}")
        resolved_9d = resolve_jacobian_9d(handle, COORDINATE_CONTRACT)
        mnj_9d = None
        if resolved_9d is not None:
            base_9d = _base_h5_metadata_from_handle(handle, h5_path)
            base_9d.update(resolved_9d.provenance())
            mnj_9d = _summarize_global_mnps_jacobian_row(
                base_9d, resolved_9d.j_hat, resolved_9d.j_dot, source_dataset_path=resolved_9d.dataset_path, dims=9
            )
        row = {
            **identity,
            "sex": participant.get("sex"),
            "source_group": participant.get("group", "TD"),
            "bayley_total_raw_score": participant.get("bayley_total_raw_score"),
            "n_timepoints": int(coords_3d.values.shape[0]),
            "geometry_contract_status": contract.status,
            "geometry_invalidity_policy": contract.invalidity_policy,
            "geometry_jacobian_9d_windows_retained": contract.jacobian_9d_windows_retained,
            "geometry_jacobian_9d_invalid_windows": contract.jacobian_9d_invalid_windows,
            "requested_coordinate_contract": COORDINATE_CONTRACT,
            "resolved_coordinate_contract": resolved.resolved_coordinate_contract,
            "jacobian_9d_available": bool(mnj_9d is not None),
        }
        anchor_group = handle.get("feature_anchors/spec")
        anchor_id = anchor_group.attrs.get("anchor_id") if anchor_group is not None else None
        anchor_hash = anchor_group.attrs.get("anchor_hash") if anchor_group is not None else None
        row["cohort_anchor_id"] = anchor_id.decode() if isinstance(anchor_id, bytes) else anchor_id
        row["cohort_anchor_hash"] = anchor_hash.decode() if isinstance(anchor_hash, bytes) else anchor_hash
        if subject_coords_3d is not None:
            for index, axis in enumerate(("m", "d", "e")):
                row[f"subject_{axis}_median"] = finite_median(subject_coords_3d.values[:, index])
        if subject_coords_9d is not None:
            for index, name in enumerate(subject_coords_9d.names):
                row[f"subject_9d_{name}_median"] = finite_median(subject_coords_9d.values[:, index])
        if coords_3d is not None:
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
            "jacobian_9d_available": bool(mnj_9d is not None),
            "epochs_raw": int(handle.attrs.get("epochs_raw", 0)),
            "epochs_after_qc": int(handle.attrs.get("epochs_after_qc", 0)),
            "dropped_geometry_invalid_epochs": int(handle.attrs.get("dropped_geometry_invalid_epochs", 0)),
        }
    reachability = summarize_reachability_h5(h5_path, REACHABILITY_CONFIG, coordinate_contract=COORDINATE_CONTRACT)["flat"]
    for key in ("tube_log_det_median", "tube_d_eff_median", "tube_kappa_median", "tube_dir_entropy_median", "tube_rotation_median", "near_singular_rate", "finite_ok", "not_testable"):
        row[key] = reachability.get(key, np.nan)
    return row, qc


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    paths = h5_paths(args.data_root)
    if args.limit_sessions:
        paths = paths[: args.limit_sessions]
    rows, qc_rows = zip(*(export_one(path) for path in paths))
    metrics = pd.DataFrame(rows).sort_values(["subject_id", "visit"])
    qc = pd.DataFrame(qc_rows).sort_values(["subject_id", "visit"])
    metrics.to_csv(args.output_dir / "session_metrics.csv", index=False)
    qc.to_csv(args.output_dir / "session_qc.csv", index=False)
    manifest = {
        "data_root": str(args.data_root),
        "n_h5": len(paths),
        "n_subjects": int(metrics.subject_id.nunique()),
        "n_subjects_with_two_or_more_visits": int((metrics.groupby("subject_id").size() >= 2).sum()),
        "coordinate_contract": COORDINATE_CONTRACT,
        "primary_endpoints": list(PRIMARY_ENDPOINTS),
        "reachability_config": REACHABILITY_CONFIG.__dict__,
        "geometry_status_counts": qc.geometry_contract_status.value_counts(dropna=False).to_dict(),
        "jacobian_9d_available_sessions": int(qc.jacobian_9d_available.sum()),
    }
    (args.output_dir / "export_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
