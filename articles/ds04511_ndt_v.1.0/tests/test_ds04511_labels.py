"""G1: task labels come from the stem, never from another task of the same subject."""
from __future__ import annotations

import pandas as pd

from ds04511_common import parse_run_stem
from ds04511_g1_labels import assign_labels, label_audit


def test_filename_task_is_parsed_and_is_not_inferred_from_run_order():
    parsed = parse_run_stem("sub-S200116_ses-01_cognitive_control_run-01")
    assert parsed["subject_id"] == "sub-S200116"
    assert parsed["task_label"] == "cognitive_control"
    assert parsed["run_index"] == 1
    assert parsed["session_index"] == 1
    rest = parse_run_stem("sub-S200116_ses-01_rest_run-01")
    assert rest["task_label"] == "rest"


def test_unparsed_stem_does_not_receive_a_task():
    parsed = parse_run_stem("sub-S200116_ses-01_unknown_run-01")
    assert parsed["stem_parse_status"] == "unparsed"
    assert parsed["task_label"] is None


def test_h5_task_disagreement_is_audited_not_overwritten():
    inventory = pd.DataFrame(
        [
            {
                "subject_id": "sub-S200116",
                "task_label": "rest",
                "stem_parse_status": "parsed",
                "source_h5": "a.h5",
                "h5_task": "gambling",
            }
        ]
    )
    labeled = assign_labels(inventory)
    assert labeled.loc[0, "task_label"] == "rest"
    assert labeled.loc[0, "label_join_status"] == "matched"
    assert bool(labeled.loc[0, "h5_stem_task_agree"]) is False


def test_documented_missing_gambling_is_expected_in_audit():
    inventory = pd.DataFrame(
        [
            {
                "subject_id": "sub-S200203",
                "task_label": "rest",
                "stem_parse_status": "parsed",
                "source_h5": "rest.h5",
                "h5_task": "rest",
            },
            {
                "subject_id": "sub-S200203",
                "task_label": "cognitive_control",
                "stem_parse_status": "parsed",
                "source_h5": "cc.h5",
                "h5_task": "cognitive_control",
            },
        ]
    )
    labeled = assign_labels(inventory)
    report = label_audit(labeled)
    assert report["subjects_missing_tasks"][0]["subject_id"] == "sub-S200203"
    assert report["subjects_missing_tasks"][0]["missing_tasks"] == ["gambling"]
    assert report["unexpected_missing_tasks"] == []
