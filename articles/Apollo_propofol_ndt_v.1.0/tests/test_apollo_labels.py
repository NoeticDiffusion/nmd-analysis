"""G1: protocol phases come from datainfo keys, never from run order."""
from __future__ import annotations

import pandas as pd

from apollo_common import PROTOCOL_PHASE_FROM_DATAINFO_ORDER, canonical_index, parse_datainfo_name, parse_run_stem
from apollo_g1_labels import assign_labels, label_audit


def test_filename_run_acq_are_canonicalized_but_are_not_phases():
    parsed = parse_run_stem("sub-002_sedation_rest_run-003_acq-135")
    assert parsed["subject_id"] == "sub-002"
    assert parsed["run_index"] == 3
    assert parsed["acq_index"] == 135
    assert parsed["run"] == "run-003"
    assert "protocol_phase" not in parsed


def test_datainfo_run_3_joins_h5_run_003():
    inventory = pd.DataFrame(
        [
            {
                "subject_id": "sub-002",
                "run": "run-003",
                "acq": "acq-135",
                "run_index": 3,
                "acq_index": 135,
                "source_h5": "a.h5",
                "h5_condition": "sedation",
            }
        ]
    )
    labels = pd.DataFrame(
        [
            {
                "subject_id": "sub-002",
                "run_index": canonical_index("run-3", prefix="run")[0],
                "acq_index": canonical_index("acq-135", prefix="acq")[0],
                "protocol_phase_id": 1,
                "protocol_phase_label": PROTOCOL_PHASE_FROM_DATAINFO_ORDER[1],
                "protocol_phase_source": "datainfo.mat",
                "datainfo_legacy_condition": "awake",
                "responsiveness_score": 0.0,
                "concentration_status": "not_recorded",
            }
        ]
    )
    joined = assign_labels(inventory, labels)
    assert joined.loc[0, "label_join_status"] == "matched"
    assert joined.loc[0, "protocol_phase_label"] == "pre_drug_baseline"
    assert joined.loc[0, "h5_condition"] == "sedation"


def test_package_window_columns_are_remapped_to_concentration_and_behaviour():
    labels = pd.DataFrame(
        [
            {
                "subject_id": "sub-002",
                "run": "run-3",
                "acq": "acq-135",
                "depth_order": 2,
                "depth_condition": "sedated",
                "depth_raw_name": "002-anest 135.3",
                "depth_window_start": 0.62,
                "depth_window_stop": 480.0,
                "depth_score": 38.0,
            }
        ]
    )
    labels["run_index"] = 3
    labels["acq_index"] = 135
    labels["protocol_phase_id"] = 2
    labels["protocol_phase_label"] = "first_protocol_sedation"
    labels["protocol_phase_source"] = "datainfo.mat"
    labels["datainfo_legacy_condition"] = "sedated"
    labels["measured_concentration"] = 0.62
    labels["mean_reaction_time_ms"] = 480.0
    labels["n_correct_responses"] = 38.0
    labels["responsiveness_score"] = 38.0
    labels["concentration_status"] = "recorded"
    labels["behavioural_task_status"] = "recorded"
    inventory = pd.DataFrame(
        [
            {
                "subject_id": "sub-002",
                "run": "run-003",
                "acq": "acq-135",
                "run_index": 3,
                "acq_index": 135,
                "source_h5": "a.h5",
                "h5_condition": "sedation",
            }
        ]
    )
    joined = assign_labels(inventory, labels)
    assert joined.loc[0, "protocol_phase_label"] == "first_protocol_sedation"
    assert joined.loc[0, "measured_concentration"] == 0.62
    assert joined.loc[0, "mean_reaction_time_ms"] == 480.0
    assert joined.loc[0, "n_correct_responses"] == 38.0
    assert "depth_window_start" not in joined.columns


def test_missing_datainfo_does_not_invent_phases_from_run_order():
    inventory = pd.DataFrame(
        [
            {
                "subject_id": "sub-002",
                "run": f"run-{index:03d}",
                "acq": "acq-001",
                "run_index": index,
                "acq_index": 1,
                "source_h5": f"f{index}.h5",
                "h5_condition": "sedation",
            }
            for index in (1, 2, 3, 4)
        ]
    )
    joined = assign_labels(inventory, pd.DataFrame())
    assert (joined["protocol_phase_status"] == "missing").all()
    assert joined["protocol_phase_label"].isna().all()
    assert (joined["label_join_status"] == "unmatched").all()
    report = label_audit(joined, {"status": "blocked", "failure_reason": "datainfo.mat not found"})
    assert report["n_matched"] == 0
    assert report["n_unmatched"] == 4
    assert report["confirmatory_contrasts"] is False


def test_two_token_cambridge_name_is_subject_acq_run():
    parsed = parse_datainfo_name("02-anest 135.3")
    assert parsed["name_parse_status"] == "parsed"
    assert parsed["subject_id"] == "sub-002"
    assert parsed["run_index"] == 3
    assert parsed["acq_index"] == 135
    assert parsed["run"] == "run-003"
    assert parsed["acq"] == "acq-135"


def test_cambridge_name_with_session_date_and_padded_run():
    parsed = parse_datainfo_name("02-2010-anest 20100210 135.003")
    assert parsed["name_parse_status"] == "parsed"
    assert parsed["subject_id"] == "sub-002"
    assert parsed["run_index"] == 3
    assert parsed["acq_index"] == 135
    assert parsed["run"] == "run-003"
    assert parsed["datainfo_session_date"] == "20100210"


def test_double_space_and_unpadded_acq_still_parse():
    parsed = parse_datainfo_name("02-2010-anest  20100210 16.003")
    assert parsed["name_parse_status"] == "parsed"
    assert parsed["acq_index"] == 16
    assert parsed["run_index"] == 3
    assert parsed["acq"] == "acq-016"


def test_three_token_cambridge_name_still_parses():
    parsed = parse_datainfo_name("002-anest rest 135.3")
    assert parsed["name_parse_status"] == "parsed"
    assert parsed["subject_id"] == "sub-002"
    assert parsed["run_index"] == 3
    assert parsed["acq_index"] == 135


def test_default_datainfo_is_article_metadata():
    from apollo_common import ARTICLE_DIR, DEFAULT_DATAINFO

    assert DEFAULT_DATAINFO == ARTICLE_DIR / "metadata" / "datainfo.mat"


def test_article_datainfo_mat_parses_eighty_rows():
    import pytest

    from apollo_common import DEFAULT_DATAINFO
    from apollo_g1_labels import load_source_labels

    if not DEFAULT_DATAINFO.is_file():
        pytest.skip("article metadata/datainfo.mat is not present")
    labels, report = load_source_labels(DEFAULT_DATAINFO)
    assert report["n_mat_rows"] == 80
    assert report["n_unparsed_names"] == 0
    assert report["n_datainfo_rows"] == 80
    assert report["n_subjects"] == 20
    assert report["status"] == "labels_loaded"
    assert report["datainfo_sha256"] == "ea8824f3ca9bd2eef0cdee3a7e1402dcc9e599f9688290cc382ae8e1a21f5608"
    assert set(report["depth_order_counts"]) == {"1", "2", "3", "4"}
    assert labels["datainfo_session_date"].notna().all()
