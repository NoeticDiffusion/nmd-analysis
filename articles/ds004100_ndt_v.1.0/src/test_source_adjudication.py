import pytest

from source_adjudication import merge_source_evidence


def _primary():
    return {"rows": [{"relative_path": "a/b.h5", "label": "ictal", "gates": {"G1": False, "G2": False, "G3": True, "G4": False}}]}


def _source():
    return {"summary": {}, "rows": [{"h5": "a\\b.h5", "subject_id": "sub-1", "session": "ses-1", "task": "ictal", "acq": "acq-seeg", "run": "run-1", "source_ieeg_json": True, "source_channels_tsv": True, "TaskName": "ictal", "h5_end_within_one_source_sample": True, "iEEGReference": "n/a", "channel_name_type_status_hash": "raw-hash", "n_source_channels": 4}]}


def test_sidecar_identity_evidence_does_not_upgrade_g1_or_g2():
    ledger = merge_source_evidence(_primary(), _source())
    row = ledger["rows"][0]
    assert row["g1_source_identity_evidence"]
    assert row["gates"] == {"G1": False, "G2": False, "G3": True, "G4": False}
    assert row["source_sidecar_evidence"]["crop_resolution"] == "not_certified_from_sidecars"


def test_inventory_mismatch_is_rejected():
    source = _source(); source["rows"][0]["h5"] = "other.h5"
    with pytest.raises(ValueError, match="inventories differ"):
        merge_source_evidence(_primary(), source)
