"""Read one deterministic H5; export schema/certificates, never outcome arrays."""
from pathlib import Path
import hashlib
import json
import h5py
import numpy as np

ROOT = Path(r"J:\repos\nmd-analysis\data\raw\neuralmanifolddynamics_Sedation-RestingState_20260918_075713")
OUT = Path(__file__).resolve().parent
files = sorted(ROOT.rglob("*.h5"))
RELATIVE = "sub-002_sedation_rest_run-003_acq-135/sub-002_sedation_rest_run-003_acq-135.h5"
EXPECTED_SHA256 = "1635513f690ae01807a9495d920052ddc2a2c9a568d3b8a76bb04139bca993ba"
selected = ROOT / RELATIVE
def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()
def value(group, key):
    if key not in group:
        return "not_recorded"
    v = group[key][()]
    if isinstance(v, bytes):
        return v.decode()
    return v.tolist() if isinstance(v, np.ndarray) else v.item() if isinstance(v, np.generic) else v

actual_sha256 = digest(selected)
if actual_sha256 != EXPECTED_SHA256 or len(files) != 80:
    raise RuntimeError("Pinned source hash or expected 80-file inventory changed; do not overwrite audit.")
manifest = json.loads((ROOT / "run_manifest.json").read_text(encoding="utf-8"))
report = {"selection": "originally lexicographically first; now pinned by relative path and SHA256", "file": str(selected),
          "sha256": actual_sha256, "n_h5_filenames": len(files),
          "run_metadata": {k: manifest[k] for k in ("counts", "subjects_index")},
          "scope": "one H5 schema, certificate and time-grid inspection; no condition contrasts",
          "sidecar_sha256": {p.name: digest(p) for p in sorted(ROOT.glob('*')) if p.is_file()},
          "datasets": {}, "certificates": {}}
with h5py.File(selected, "r") as f:
    embedded = json.loads(f.attrs["manifest"])
    report["embedded_metadata"] = {"mnps": embedded["mnps"], "mnps_axis_names": embedded["mnps_axes"]["names"],
        "feature_fit_scopes": sorted({v["fit_scope"] for v in embedded["feature_baselines"].values() if "fit_scope" in v})}
    metadata_paths = [
        "provenance/anchoring/primary_coordinate_layer", "provenance/anchoring/primary_coordinate_contract",
        "provenance/normalization/status", "provenance/normalization/method",
        "support_signature/v1/coordinates/e_m/source", "support_signature/v1/coordinates/e_m/fallback_feature",
        "support_signature/v1/coordinates/e_m/semantic_equivalence", "support_signature/v1/axes_3d/e/source",
        "provenance/signal_support_provenance/temporal_support_status",
        "provenance/signal_support_provenance/temporal_support_reason",
        "provenance/signal_support_provenance/source_quality_status",
        "stochastic_reachability/v1/primary/n_propagator_steps"]
    report["audited_metadata"] = {"/" + k: value(f, k) for k in metadata_paths}
    report["root_groups"] = list(f)
    report["n_timepoints"] = int(f["time"].size)
    dt, counts = np.unique(np.diff(f["time"][()]), return_counts=True)
    report["observed_dt_sec_counts"] = list(zip(dt.tolist(), counts.tolist()))
    def visit(name, obj):
        if isinstance(obj, h5py.Dataset):
            report["datasets"]["/" + name] = {"shape": list(obj.shape), "dtype": str(obj.dtype)}
        if isinstance(obj, h5py.Group) and "computation_status" in obj:
            report["certificates"]["/" + name] = {k: value(obj, k) for k in (
                "computation_status", "support_status", "qualification_status",
                "measurement_validity", "claim_status", "failure_reason")}
    f.visititems(visit)
path = OUT / "h5_inventory_20260920.json"
path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"output": str(path), "file": str(selected), "sha256": report["sha256"],
                  "datasets": len(report["datasets"]), "certificates": len(report["certificates"])}, indent=2))
