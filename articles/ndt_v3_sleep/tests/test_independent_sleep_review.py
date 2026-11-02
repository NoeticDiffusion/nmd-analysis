"""Independent checks for the frozen two-participant descriptive pilot.

These tests read the produced H5, epoch tables, and comparison artifact.  They
recompute eligibility and medians from the row-level export rather than
trusting the comparison JSON alone.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import pytest

ARTICLE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ARTICLE_ROOT / "src"))
from compare_parent_stage_direction import contrasts


ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
PROJECT = ROOT / "project" / "v3" / "independent_sleep_20260910"
PROTOCOL = PROJECT / "frozen_selection_protocol.json"
PARTICIPANTS = Path(r"K:\ExternalReceivedDatasets\openneuro\ds005555\participants.tsv")
REFERENCE_SUMMARY = (
    ROOT
    / "project"
    / "v3"
    / "fullnight_support_20260910"
    / "description_final"
    / "fullnight_stage_summary.json"
)
REFERENCE_TABLE = REFERENCE_SUMMARY.parent / "epoch_coordinates.parquet"
CANDIDATE_SUMMARY = PROJECT / "description_final" / "fullnight_stage_summary.json"
CANDIDATE_TABLE = CANDIDATE_SUMMARY.parent / "epoch_coordinates.parquet"
COMPARISON = PROJECT / "comparison_r1" / "parent_direction_comparison.json"
CANDIDATE_H5 = (
    PROJECT
    / "processed"
    / "ds005555"
    / "neuralmanifolddynamics_ds005555_20260910_114609"
    / "sub-1_Sleep_acq-psg"
    / "sub-1_Sleep_acq-psg.h5"
)
REFERENCE_H5 = (
    ROOT
    / "project"
    / "v3"
    / "fullnight_support_20260910"
    / "processed"
    / "ds005555"
    / "neuralmanifolddynamics_ds005555_20260910_112127"
    / "sub-99_Sleep_acq-psg"
    / "sub-99_Sleep_acq-psg.h5"
)

PARTICIPANTS_SHA256 = (
    "0591b6323bd101af1c6871053aea4351a6cdd12e08f2aeff9a084b4692a03110"
)
CANDIDATE_H5_SHA256 = (
    "1eba1d7d9a470647992ab729f26a4ee5cea9249586e7e98cbad814759cff94db"
)
REFERENCE_H5_SHA256 = "217991681011397acd4493cd97cc74e7a982d361a04e6e94d29b40c8261ef8a1"
EDF_SHA256 = "871ad6c6f0245cd1f295881729a6b74e744621f34a51b1931fd35f105bfcc6bf"
EVENTS_SHA256 = "007020f9ff341f8fa418d30a23c2a2c6b4517c2dc6080d3e911f76b49810a5a4"

COORDINATES = {
    "3d": ("m", "d", "e"),
    "9d": ("m_a", "m_e", "m_o", "d_n", "d_l", "d_s", "e_e", "e_s", "e_m"),
}
MASK_COLUMNS = (
    "producer_mask_coverage_ok",
    "producer_mask_retained_after_qc",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _eligible(frame: pd.DataFrame, representation: str, coordinate: str) -> pd.Series:
    finite = frame[f"coordinate_finite_{representation}"].astype(bool)
    masks = np.logical_and.reduce(
        [
            *(frame[column].to_numpy() == 1 for column in MASK_COLUMNS),
            frame[
                "producer_mask_geometry_valid"
                if representation == "3d"
                else "producer_mask_coords_9d_valid"
            ].to_numpy()
            == 1,
        ]
    )
    return (
        frame["stage_label_status"].eq("recorded")
        & frame["stage_code"].isin((0, 2))
        & finite
        & masks
        & np.isfinite(frame[f"mnps_{coordinate}"])
    )


def _independent_contrasts(table: Path) -> dict[tuple[str, str], dict[str, float | int | None]]:
    frame = pd.read_parquet(table)
    result: dict[tuple[str, str], dict[str, float | int | None]] = {}
    for representation, names in COORDINATES.items():
        for name in names:
            coordinate = f"{representation}_{name}"
            selected = {}
            for stage in (0, 2):
                rows = frame[frame["stage_code"].eq(stage) & _eligible(frame, representation, coordinate)]
                values = rows[f"mnps_{coordinate}"]
                selected[stage] = {
                    "n": int(values.shape[0]),
                    "median": float(values.median()) if len(values) else None,
                }
            if all(selected[stage]["n"] > 0 for stage in (0, 2)):
                delta = selected[2]["median"] - selected[0]["median"]
                direction = 1 if delta > 0 else -1 if delta < 0 else 0
            else:
                delta = None
                direction = None
            result[(representation, f"mnps_{coordinate}")] = {
                "n_wake": selected[0]["n"],
                "n_n2": selected[2]["n"],
                "n2_minus_wake_median": delta,
                "direction": direction,
            }
    return result


def test_frozen_selection_and_embedded_participant_identity_are_distinct():
    protocol = _json(PROTOCOL)
    assert _sha256(PARTICIPANTS) == PARTICIPANTS_SHA256
    with PARTICIPANTS.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    by_subject = {row["participant_id"]: row for row in rows}
    assert by_subject[protocol["selected_subject"]]["pid"] == protocol["participant_pid"]
    assert by_subject[protocol["reference_subject"]]["pid"] == protocol["reference_pid"]
    assert protocol["participant_pid"] != protocol["reference_pid"]

    for source, subject_key, pid_key, expected_hash in (
        (CANDIDATE_H5, "selected_subject", "participant_pid", CANDIDATE_H5_SHA256),
        (REFERENCE_H5, "reference_subject", "reference_pid", REFERENCE_H5_SHA256),
    ):
        assert _sha256(source) == expected_hash
        with h5py.File(source, "r") as handle:
            row = json.loads(handle["participant/row_json"][()].decode("utf-8"))
            clinical = json.loads(handle["participant/clinical_json"][()].decode("utf-8"))
        assert row["participant_id"] == protocol[subject_key]
        assert str(row["pid"]) == protocol[pid_key]
        assert clinical["participant"]["participant_id"] == protocol[subject_key]
        assert str(clinical["participant"]["pid"]) == protocol[pid_key]


def test_candidate_h5_geometry_masks_labels_and_source_provenance():
    assert _sha256(CANDIDATE_H5) == CANDIDATE_H5_SHA256
    with h5py.File(CANDIDATE_H5, "r") as handle:
        n = handle["epoch_id"].shape[0]
        assert n == 915
        epoch_id = np.asarray(handle["epoch_id"][:])
        time = np.asarray(handle["time"][:], dtype=float)
        start = np.asarray(handle["window_start"][:], dtype=float)
        end = np.asarray(handle["window_end"][:], dtype=float)
        assert np.array_equal(epoch_id, np.arange(n, dtype=epoch_id.dtype))
        assert np.all(np.isfinite(time)) and np.all(np.diff(time) == 30.0)
        assert np.all(np.isfinite(start)) and np.all(np.isfinite(end))
        assert np.all(end - start == 30.0)
        assert np.array_equal(start, np.arange(n, dtype=float) * 30.0)
        assert np.array_equal(end, start + 30.0)
        stage = np.asarray(handle["labels/stage"][:])
        unique, counts = np.unique(stage, return_counts=True)
        assert dict(zip(unique.tolist(), counts.tolist())) == {0: 200, 1: 57, 2: 398, 3: 172, 4: 87, 8: 1}
        for path in (
            "qc/windows/coverage_ok",
            "qc/windows/retained_after_qc",
            "qc/windows/geometry_valid",
            "qc/windows/coords_9d_valid",
        ):
            values = np.asarray(handle[path][:])
            assert values.shape == (n,)
            assert np.array_equal(values, np.ones(n, dtype=values.dtype))
        provenance = handle["provenance/signal_support_provenance"]
        assert provenance["temporal_support_status"][()].decode() == "unknown"
        assert provenance["source_quality_status"][()].decode() == "recorded"
        source = json.loads(provenance["source_quality_intervals_json"][()].decode("utf-8"))
        assert len(source) == 1
        assert source[0]["stage_code"] == 8
        assert source[0]["source_sha256"] == EVENTS_SHA256
        record = json.loads(provenance["execution_records_json"][()].decode("utf-8"))[0]["record"]
        assert record["source"]["sha256"] == EDF_SHA256
        assert record["source"]["sha256_after"] == EDF_SHA256
        extents = json.loads(provenance["per_epoch_input_extent_json"][()].decode("utf-8"))
        assert len(extents) == n
        assert {x["support_status"] for x in extents} == {"unknown"}


def test_epoch_export_retains_unknown_code8_and_does_not_claim_support():
    manifest = _json(PROJECT / "description_final" / "epoch_manifest.json")
    assert manifest["source_sha256_before"] == CANDIDATE_H5_SHA256
    assert manifest["source_sha256_after"] == CANDIDATE_H5_SHA256
    assert manifest["n_epochs"] == 915
    assert manifest["source_leaf_assertion"] == {"expected_name": "sub-1_Sleep_acq-psg.h5", "matched": True}
    assert manifest["stage_purity_status"] == "not_assessed"
    assert manifest["feature_filter_full_support"] == "not_assessed"
    assert manifest["diffusion_neighbor_stage_purity"] == "not_assessed"
    assert manifest["recording_wq_exported"] is False
    frame = pd.read_parquet(CANDIDATE_TABLE)
    assert int(frame["stage_code"].eq(8).sum()) == 1
    assert frame.loc[frame["stage_code"].eq(8), "stage_label_status"].eq("missing_or_unknown").all()
    assert frame["stage_purity_status"].eq("not_assessed").all()


def test_cross_participant_e_m_source_signatures_are_explicitly_non_equivalent():
    def signature(path: Path) -> dict[str, str]:
        with h5py.File(path, "r") as handle:
            group = handle["support_signature/v1/coordinates/e_m"]
            return {key: group[key][()].decode("utf-8") for key in group}

    candidate = signature(CANDIDATE_H5)
    reference = signature(REFERENCE_H5)
    assert candidate == {
        "fallback_feature": "eog_blink_rate",
        "semantic_equivalence": "false",
        "source": "fallback",
    }
    assert reference == {
        "fallback_feature": "ppg_rate_bpm",
        "semantic_equivalence": "false",
        "source": "fallback",
    }
    assert candidate["fallback_feature"] != reference["fallback_feature"]
    diagnostic = _json(PROJECT / "ingest" / "e_m_diagnostic.json")
    assert diagnostic["status"] == "diagnostic_only"
    assert diagnostic["raw_feature"] == "embodied_arousal_proxy"
    assert diagnostic["support_signature"] == candidate
    assert diagnostic["raw_unique_n"] > 1
    assert diagnostic["n2_wake_median_delta_coordinate"] == 0.0


def test_all_twelve_direction_rows_match_independent_epoch_table_recomputation():
    reference = _json(REFERENCE_SUMMARY)
    candidate = _json(CANDIDATE_SUMMARY)
    assert reference["scientific_qualification"] == candidate["scientific_qualification"] == "not_assessed"
    assert reference["stage_purity_status"] == candidate["stage_purity_status"] == "not_assessed"
    expected_reference = _independent_contrasts(REFERENCE_TABLE)
    expected_candidate = _independent_contrasts(CANDIDATE_TABLE)
    observed = _json(COMPARISON)
    assert len(observed["rows"]) == 12
    assert observed["pooling"] == "not_performed"
    assert observed["p_values"] == "not_computed"
    assert observed["scientific_qualification"] == "not_assessed"
    for row in observed["rows"]:
        key = (row["representation"], row["coordinate"])
        assert row["reference"] == expected_reference[key]
        assert row["candidate"] == expected_candidate[key]
        assert row["direction_agreement"] == (
            row["reference"]["direction"] == row["candidate"]["direction"]
            if row["reference"]["direction"] is not None and row["candidate"]["direction"] is not None
            else None
        )
    assert sum(row["direction_agreement"] is True for row in observed["rows"]) == 7
    assert sum(row["direction_agreement"] is False for row in observed["rows"]) == 5
    assert sum(row["candidate"]["direction"] == 0 for row in observed["rows"]) == 1


def test_contrast_parser_rejects_duplicate_rows_and_preserves_empty_as_null():
    base = {
        "scientific_qualification": "not_assessed",
        "representations": {
            "3d": {"summary": []},
            "9d": {"summary": []},
        },
    }
    for representation, names in COORDINATES.items():
        for name in names:
            for stage in (0, 2):
                base["representations"][representation]["summary"].append(
                    {
                        "coordinate": f"mnps_{representation}_{name}",
                        "stage_code": stage,
                        "n": 0,
                        "median": None,
                    }
                )
    empty = contrasts(base)
    assert len(empty) == 12
    assert all(value["n2_minus_wake_median"] is None for value in empty.values())

    duplicate = json.loads(json.dumps(base))
    duplicate["representations"]["3d"]["summary"].append(
        {"coordinate": "mnps_3d_m", "stage_code": 0, "n": 1, "median": 0.0}
    )
    with pytest.raises(ValueError, match="missing or duplicate"):
        contrasts(duplicate)
