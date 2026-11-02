from dataclasses import replace

import numpy as np
import pytest

from primary_contrasts import (
    ContrastContractError,
    RecordingSummary,
    build_endpoint_contrast,
    exact_upper_tail,
    h1_recording_median,
    h2_recording_median,
    holm_adjust,
    primary_family_verdicts,
)


def _row(subject, label, value, *, session="ses-a", acq="acq-seeg", gates=None, source=None):
    return RecordingSummary(
        endpoint="H1", subject_id=subject, session=session, acquisition=acq, label=label,
        source_recording_id=source or f"{subject}-{session}-{acq}-{label}",
        original_recording_id=source or f"{subject}-{session}-{acq}-{label}",
        export_sha256=f"hash-{source or f'{subject}-{session}-{acq}-{label}'}", crop_resolution="unique", median=value,
        valid_centers=30, native_centers=40, metadata_eligible=True,
        gates=gates or {"G1": True, "G2": True, "G3": True, "G4": True},
        computation_status="computed", support_status="sufficient",
        measurement_validity="not_assessed", claim_status="no_biological_claim",
        temporal_support_status="unknown", comparability_verdict="passed",
        normalization_signature="frozen-signature", feature_signature="feature-signature",
        fallback_signature="fallback-signature", contact_signature="contact-signature",
        reference_provenance="qualified-reference",
    )


def test_h1_keeps_valid_terminal_native_query():
    median, count = h1_recording_median([1.0] * 40, [1] * 40)
    assert median == 1.0 and count == 40


def test_h2_uses_source_indices_once_and_rejects_duplicates():
    values = np.r_[np.ones(30), np.nan, np.nan]
    median, count = h2_recording_median(values, np.arange(30), np.r_[np.ones(30), 0, 0])
    assert median == 1.0 and count == 30
    with pytest.raises(ContrastContractError, match="duplicates"):
        h2_recording_median(values, [0, 0], np.r_[np.ones(30), 0, 0])


def test_stratum_selection_precedes_endpoint_aggregation_and_ties_stay_in_n():
    rows = [
        _row("s1", "ictal", 2.0, session="ses-z"), _row("s1", "interictal", 1.0, session="ses-z"),
        _row("s1", "ictal", 1.0, session="ses-a"), _row("s1", "interictal", 3.0, session="ses-a"),
        _row("s1", "ictal", 2.0, session="ses-a", source="extra-ictal"),
        _row("s2", "ictal", 1.0), _row("s2", "interictal", 1.0),
    ]
    contrast = build_endpoint_contrast(rows, "H1")
    assert contrast.selected_strata["s1"] == ("ses-a", "acq-seeg")
    assert contrast.participant_differences == {"s1": -1.5, "s2": 0.0}
    assert contrast.n == 2 and contrast.k_negative == 1 and contrast.ties == 1
    assert contrast.raw_p is None and not contrast.confirmatory_test_run


def test_gates_and_minimum_n_prevent_confirmatory_p_value():
    rows = []
    for i in range(20):
        gates = {"G1": True, "G2": i != 0, "G3": True, "G4": True}
        rows += [_row(f"s{i}", "ictal", 0.0, gates=gates), _row(f"s{i}", "interictal", 1.0, gates=gates)]
    contrast = build_endpoint_contrast(rows, "H1")
    assert contrast.descriptive_n == 20 and contrast.n == 19 and contrast.k_negative == 19
    assert contrast.raw_p is None and contrast.test_status == "NOT_RUN_METHOD_LIMITED"


def test_duplicate_source_export_is_refused_before_aggregation():
    rows = [
        _row("s1", "ictal", 0.0, source="same-source"),
        _row("s1", "interictal", 1.0, source="same-source"),
    ]
    with pytest.raises(ContrastContractError, match="Duplicate export"):
        build_endpoint_contrast(rows, "H1")


def test_exact_tail_and_two_member_holm_bookkeeping():
    assert exact_upper_tail(15, 20) <= 0.025
    base = build_endpoint_contrast([_row("only", "ictal", 0), _row("only", "interictal", 1)], "H1")
    h1 = replace(base, raw_p=0.01, confirmatory_test_run=True, test_status="RUN_PENDING_HOLM")
    h2 = replace(base, endpoint="H2", raw_p=1.0)
    adjusted = holm_adjust([h1, h2])
    assert adjusted == {"H1": 0.02, "H2": 1.0}
    assert primary_family_verdicts([h1, h2]) == {"H1": "PASS", "H2": "METHOD-LIMITED"}
