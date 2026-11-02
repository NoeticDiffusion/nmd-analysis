from pathlib import Path

import h5py
import numpy as np

from primary_ledger import inspect_record


def _scalar(group, name, value):
    group.create_dataset(name, data=np.bytes_(value))


def _record(path: Path, *, duplicate_h2=False):
    with h5py.File(path, "w") as f:
        f.attrs.update(subject_id="sub-X", session="ses-a", acq="acq-seeg", run="run-01", task="ictal", primary_coordinate_contract="subject_anchored", primary_coordinate_layer="coords_3d_subject_anchored", feature_export_names_hash="feature-hash", mnps_9d_constructs="direct")
        f.create_dataset("time", data=np.arange(40, dtype=float) * 4)
        norm = f.create_group("provenance/normalization")
        for name, value in {"status": "disabled", "method": "combat", "scope": "post_features"}.items(): _scalar(norm, name, value)
        support = f.create_group("provenance/signal_support_provenance")
        _scalar(support, "temporal_support_status", "unknown")
        _scalar(support, "reference_fit_population", "not_recorded")
        for endpoint, product in [("H1", "dynamical_families/diffusion/v1"), ("H2", "dynamical_families/amplification/v1/neighbor_gain_q90_level1")]:
            group = f.create_group(product)
            for name, value in {"computation_status": "computed", "support_status": "sufficient", "measurement_validity": "not_assessed", "claim_status": "no_biological_claim"}.items(): _scalar(group, name, value)
            series = group.create_group("series")
            if endpoint == "H1":
                series.create_dataset("diffusion_effective_dimension", data=np.ones(40))
                series.create_dataset("valid", data=np.ones(40, dtype=np.int8))
            else:
                series.create_dataset("neighbor_gain_q90", data=np.r_[np.ones(39), np.nan])
                series.create_dataset("n_neighbor_pairs", data=np.r_[np.ones(39), 0])
                series.create_dataset("source_idx", data=np.r_[np.arange(38), 0] if duplicate_h2 else np.arange(39))


def test_ledger_collects_support_without_endpoint_medians(tmp_path):
    path = tmp_path / "a.h5"; _record(path)
    row = inspect_record(path, {"sha256": "frozen", "filename_task": "ictal", "source_raw_files": "source.edf", "feature_fit_population_hashes": "fit", "feature_fit_scopes": "local", "support_signature": "sig"})
    assert row["g1_label_identity_evidence"]
    assert row["gates"] == {"G1": False, "G2": False, "G3": True, "G4": False}
    assert row["endpoint_evidence"]["H1"]["valid_centers"] == 40
    assert "median" not in str(row)


def test_ledger_preserves_invalid_h2_as_failed_support_not_zero(tmp_path):
    path = tmp_path / "a.h5"; _record(path, duplicate_h2=True)
    row = inspect_record(path, {"sha256": "frozen", "filename_task": "ictal", "source_raw_files": "source.edf"})
    assert not row["endpoint_evidence"]["H2"]["structurally_eligible"]
    assert "duplicate" in row["endpoint_evidence"]["H2"]["failure"]
