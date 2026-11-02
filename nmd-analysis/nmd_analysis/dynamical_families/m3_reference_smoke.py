"""Read-only support smoke check; no empirical drift or M3 qualification."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform

import h5py
import numpy as np

from nmd_analysis.dynamical_families import drift


SPEC = {
    "version": "m3_reference_support.v1",
    "train_increment_range": [0, 600],
    "evaluation_increment_range": [700, 800],
    "embargo_sec": 60.0,
    "n_neighbors": 32,
    "min_train_support": 12,
    "estimators": ["local_mean", "local_linear"],
    "coordinate_paths": ["mnps_3d", "coords_9d/values"],
    "support": "contiguous union of validated 30-second source and destination epoch windows",
    "claim_status": "no_biological_claim",
    "qualification": "candidate_not_qualified",
}


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def scalar(handle, path):
    if path not in handle:
        return "not_recorded"
    value = handle[path][()]
    if isinstance(value, bytes):
        return value.decode()
    return value.item() if isinstance(value, np.generic) else value


def run_reference(source: Path) -> dict:
    before = digest(source)
    report = {
        "spec": SPEC,
        "spec_hash": hashlib.sha256(json.dumps(SPEC, sort_keys=True).encode()).hexdigest(),
        "source": str(source.resolve()), "source_sha256": before,
        "drift_code_sha256": digest(Path(drift.__file__)),
        "runner_sha256": digest(Path(__file__)),
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "h5py": h5py.__version__},
        "rows": [],
    }
    with h5py.File(source, "r") as f:
        t = np.asarray(f["time"], dtype=float)
        starts, ends = np.asarray(f["window_start"]), np.asarray(f["window_end"])
        if len(t) <= 800 or starts.shape != t.shape or ends.shape != t.shape:
            raise ValueError("Reference does not support the frozen split/epoch contract")
        if not (np.isfinite(starts).all() and np.isfinite(ends).all()
                and np.all(starts <= t) and np.all(ends >= t)):
            raise ValueError("Invalid raw epoch support")
        if not (np.all(np.diff(t) == 30.0) and np.all(ends - starts == 30.0)
                and np.all(ends[:-1] == starts[1:])):
            raise ValueError("Reference requires a contiguous 30-second grid and raw epoch support")
        report["n_epochs"] = len(t)
        report["unique_dt_sec"] = np.unique(np.diff(t)).tolist()
        schema = f.attrs.get("schema_version")
        if isinstance(schema, bytes):
            schema = schema.decode()
        if schema != "mnps_tensor_spec_v2_4":
            raise ValueError("Unexpected reference chart schema")
        if scalar(f, "provenance/geometry_contract/status") != "ok":
            raise ValueError("Reference geometry contract is not ok")
        report["source_chart_contract"] = {
            "schema_version": schema,
            "export_contract_version": scalar(f, "provenance/contract/export_contract_version"),
            "primary_coordinate_contract": str(f.attrs.get("primary_coordinate_contract", "not_recorded")),
            "primary_coordinate_layer": str(f.attrs.get("primary_coordinate_layer", "not_recorded")),
            "selection": "explicit dataset paths in SPEC; not automatic primary-layer selection",
            "nmd_code_revision": None,
            "revision_reason": "not recorded in source HDF5 attributes; source bytes are hashed",
        }
        paths = ["dynamical_families/diffusion/v1/computation_status",
                 "dynamical_families/diffusion/v1/measurement_validity",
                 "provenance/geometry_contract/status",
                 "provenance/geometry_contract/time_grid/status",
                 "stochastic_reachability/v1/primary/computation_status",
                 "stochastic_reachability/v1/primary/failure_reason",
                 "stochastic_reachability/v1/stratified_9d/computation_status",
                 "stochastic_reachability/v1/stratified_9d/failure_reason"]
        report["source_status"] = {p: scalar(f, p) for p in paths}
        train, evaluation = np.arange(600), np.arange(700, 800)

        def support(indices):
            return np.column_stack((np.minimum(starts[indices], starts[indices + 1]),
                                    np.maximum(ends[indices], ends[indices + 1])))

        for coord in SPEC["coordinate_paths"]:
            x = np.asarray(f[coord], dtype=float)
            expected_names = (["m", "d", "e"] if coord == "mnps_3d" else
                              ["m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"])
            names = f.attrs.get("mnps_axis_names", []) if coord == "mnps_3d" else f["coords_9d/names"][()]
            names = [n.decode() if isinstance(n, bytes) else str(n) for n in names]
            if x.shape != (len(t), len(expected_names)) or names != expected_names:
                raise ValueError(f"Unexpected coordinate dimension/order for {coord}")
            for estimator in SPEC["estimators"]:
                row = {"coordinates": coord, "estimator": estimator}
                try:
                    result = drift.crossfit_local_chart_b(
                        x, t, train, evaluation, estimator=estimator, n_neighbors=32,
                        min_train_support=12, embargo=60.0,
                        train_window_support=support(train), evaluation_window_support=support(evaluation),
                        source_artifact_hash=before,
                        source_nmd_schema=schema,
                        nmd_code_revision=None,
                    )
                    row.update(status="computed_candidate", n_predictions=len(result.b_hat),
                               finite=bool(np.isfinite(result.b_hat).all()), provenance=result.provenance)
                except drift.DriftContractError as exc:
                    row.update(status="refused", reason=str(exc), n_predictions=0)
                report["rows"].append(row)
            # Altered copies are failure controls, never substituted for the source.
            gapped = t.copy()
            gapped[750:] += 30.0
            for label, xx, tt in [("gap", x, gapped), ("nonfinite", x.copy(), t)]:
                if label == "nonfinite":
                    xx[750, 0] = np.nan
                try:
                    drift.crossfit_local_chart_b(xx, tt, train, evaluation, n_neighbors=32)
                except drift.DriftContractError as exc:
                    report["rows"].append({"coordinates": coord, "control": label,
                                           "status": "expected_refusal", "reason": str(exc)})
                else:
                    raise AssertionError(f"Reference {label} control did not fail closed")
    report["source_unchanged"] = digest(source) == before
    if not report["source_unchanged"]:
        raise RuntimeError("Source changed during the read-only check")
    candidates = [r for r in report["rows"] if "estimator" in r]
    report["support_status"] = ("computed_candidate_support" if all(
        r["status"] == "computed_candidate" and r["finite"] for r in candidates)
        else "partial_support" if any(r["status"] == "computed_candidate" for r in candidates)
        else "support_not_testable")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = run_reference(args.source)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
