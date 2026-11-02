"""Walk the I-CARE v2 H5 root and write a run inventory plus subject index."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import h5py
import pandas as pd

from icare_v2_common import (
    add_common_args,
    as_scalar,
    discover_h5_files,
    empty_run_directories,
    h5_scalar,
    parse_run_stem,
    participant_meta_from_handle,
    resolve_pipeline_config,
    time_reference_from_handle,
    write_csv,
    write_json,
)


def _status(handle: h5py.File, path: str) -> str:
    return str(h5_scalar(handle, path, default="unavailable") or "unavailable")


def inspect_h5(path: str) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "stem": Path(path).stem,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "read_ok": False,
        "read_error": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            timing = time_reference_from_handle(handle)
            row.update(meta)
            row.update(timing)
            row["schema_version"] = as_scalar(handle.attrs.get("schema_version"))
            row["mndm_version"] = as_scalar(handle.attrs.get("mndm_version"))
            row["primary_coordinate_contract"] = as_scalar(handle.attrs.get("primary_coordinate_contract"))
            row["primary_coordinate_layer"] = as_scalar(handle.attrs.get("primary_coordinate_layer"))
            row["geometry_contract_status"] = as_scalar(handle.attrs.get("geometry_contract_status"))
            row["diffusion_computation_status"] = _status(handle, "/dynamical_families/diffusion/v1/computation_status")
            row["destination_computation_status"] = _status(handle, "/dynamical_families/destination/v1/computation_status")
            row["resilience_computation_status"] = _status(handle, "/dynamical_families/resilience/v1/computation_status")
            row["jacobian_metrics_3d_status"] = _status(handle, "/jacobian/derived_metrics/v1/computation_status")
            row["jacobian_metrics_9d_status"] = _status(handle, "/jacobian_9D/derived_metrics/v1/computation_status")
            row["ftr_3d_status"] = _status(handle, "/finite_time_response/v1/primary/computation_status")
            row["stochastic_reachability_3d_status"] = _status(handle, "/stochastic_reachability/v1/primary/computation_status")
            row["n_windows_jacobian_valid"] = h5_scalar(handle, "/jacobian/derived_metrics/v1/summary/n_windows_metrics_valid")
            row["n_windows_stable_reactive"] = h5_scalar(handle, "/jacobian/derived_metrics/v1/summary/n_windows_stable_reactive")
            row["stable_reactive_fraction_stored"] = h5_scalar(handle, "/jacobian/derived_metrics/v1/summary/stable_reactive_fraction")
            row["n_valid_diffusion_timepoints"] = h5_scalar(handle, "/dynamical_families/diffusion/v1/summary/n_valid_timepoints")
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001 - inventory must keep going
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    out_dir = cfg.output_dir
    h5_paths = discover_h5_files(
        cfg.raw_root,
        subject_allowlist=cfg.subject_allowlist,
        limit_h5=cfg.limit_h5,
    )
    empty_dirs = empty_run_directories(cfg.raw_root, subject_allowlist=cfg.subject_allowlist)
    print(f"Inventory: {len(h5_paths)} H5 files, {len(empty_dirs)} empty run dirs", flush=True)
    from icare_v2_common import parallel_map

    rows = parallel_map(inspect_h5, [str(path) for path in h5_paths], workers=cfg.workers, desc="inventory")
    run_frame = pd.DataFrame(rows)
    if not run_frame.empty:
        run_frame["bundle_id"] = cfg.bundle_id
        run_frame["confirmatory_status"] = cfg.confirmatory_status
        run_frame["smoke"] = cfg.smoke
    subject_frame = (
        run_frame.sort_values(["subject_id", "run", "acq"])
        .groupby("subject_id", as_index=False)
        .agg(
            cpc=("cpc", "first"),
            outcome=("outcome", "first"),
            age=("age", "first"),
            sex=("sex", "first"),
            hospital=("hospital", "first"),
            rosc=("rosc", "first"),
            ohca=("ohca", "first"),
            shockable_rhythm=("shockable_rhythm", "first"),
            ttm=("ttm", "first"),
            n_runs=("source_h5", "nunique"),
            n_runs_read_ok=("read_ok", "sum"),
            n_windows_total=("n_windows", "sum"),
        )
        if not run_frame.empty
        else pd.DataFrame()
    )
    write_csv(out_dir / "run_inventory.csv", run_frame)
    write_csv(out_dir / "subject_index.csv", subject_frame)
    write_json(
        out_dir / "run_inventory_manifest.json",
        {
            "bundle_id": cfg.bundle_id,
            "confirmatory_status": cfg.confirmatory_status,
            "smoke": cfg.smoke,
            "raw_root": str(cfg.raw_root),
            "n_h5": int(len(h5_paths)),
            "n_empty_dirs": int(len(empty_dirs)),
            "empty_dirs": [str(path) for path in empty_dirs],
            "n_subjects": int(subject_frame.shape[0]) if not subject_frame.empty else 0,
            "n_read_ok": int(run_frame["read_ok"].sum()) if not run_frame.empty else 0,
            "n_read_fail": int((~run_frame["read_ok"]).sum()) if not run_frame.empty else 0,
            "subject_allowlist": list(cfg.subject_allowlist or []),
        },
    )
    print(f"Wrote {out_dir / 'run_inventory.csv'} ({len(run_frame)} runs, {len(subject_frame)} subjects)", flush=True)


if __name__ == "__main__":
    main()
