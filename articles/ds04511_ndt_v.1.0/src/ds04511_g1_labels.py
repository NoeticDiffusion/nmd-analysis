"""G1: task labels from the NMD/BIDS stem only.

H5 participant mapped_json is audited, never used to fill a missing stem task.
Run order never fills a missing task. Documented missing GG stays missing.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from ds04511_common import (
    DOCUMENTED_MISSING_TASKS,
    EXPECTED_N_CC,
    EXPECTED_N_GG,
    EXPECTED_N_REST,
    TASK_SOURCE,
    TASKS,
)


TASK_STATUS_RECORDED = "recorded"
TASK_STATUS_MISSING = "missing"


def assign_labels(inventory: pd.DataFrame) -> pd.DataFrame:
    """Keep stem task as the analysis label. Audit H5 task; do not overwrite."""
    out = inventory.copy()
    parsed = out.get("stem_parse_status") == "parsed"
    has_task = out.get("task_label").notna() if "task_label" in out.columns else pd.Series(False, index=out.index)
    matched = parsed & has_task
    out["task_label_source"] = TASK_SOURCE
    out["task_label_status"] = matched.map(lambda ok: TASK_STATUS_RECORDED if ok else TASK_STATUS_MISSING)
    out["label_join_status"] = matched.map(lambda ok: "matched" if ok else "unmatched")
    if "h5_task" in out.columns:
        h5_task = out["h5_task"].astype("string")
        stem_task = out["task_label"].astype("string")
        out["h5_task_audit"] = h5_task
        out["h5_stem_task_agree"] = h5_task.isna() | (h5_task == stem_task)
    else:
        out["h5_task_audit"] = pd.NA
        out["h5_stem_task_agree"] = True
    return out


def label_audit(labeled: pd.DataFrame) -> dict[str, Any]:
    report: dict[str, Any] = {
        "gate": "G1",
        "status": "blocked",
        "label_source": TASK_SOURCE,
        "n_recordings": int(len(labeled)),
        "n_matched": int((labeled.get("label_join_status") == "matched").sum()) if not labeled.empty else 0,
        "n_unmatched": int((labeled.get("label_join_status") == "unmatched").sum()) if not labeled.empty else 0,
        "documented_missing_tasks": {
            f"{subject}:{task}": reason for (subject, task), reason in DOCUMENTED_MISSING_TASKS.items()
        },
        "note": (
            "Task identity is the stem token gambling|cognitive_control|rest. "
            "A missing H5 is not filled from another task of the same subject. "
            "H5 mapped_json task is audit-only."
        ),
        "confirmatory_contrasts": False,
    }
    if labeled.empty:
        report["failure_reason"] = "no inventory rows"
        return report
    counts = labeled["task_label"].value_counts(dropna=False).to_dict()
    report["task_counts"] = {str(key): int(value) for key, value in counts.items()}
    report["n_subjects"] = int(labeled["subject_id"].nunique())
    by_subject = labeled.groupby("subject_id")["task_label"].agg(
        lambda values: set(str(item) for item in values.dropna())
    )
    complete = by_subject.map(lambda tasks: set(TASKS).issubset(tasks))
    report["n_subjects_with_all_three_tasks"] = int(complete.sum())
    incomplete = []
    for subject, tasks in by_subject.items():
        missing = [task for task in TASKS if task not in tasks]
        if missing:
            incomplete.append({"subject_id": str(subject), "missing_tasks": missing})
    report["subjects_missing_tasks"] = incomplete
    expected_missing = {
        (subject, task) for subject, task in DOCUMENTED_MISSING_TASKS
    }
    unexpected = [
        row
        for row in incomplete
        for task in row["missing_tasks"]
        if (row["subject_id"], task) not in expected_missing
    ]
    report["unexpected_missing_tasks"] = unexpected
    n_disagree = int((~labeled["h5_stem_task_agree"].fillna(True).astype(bool)).sum())
    report["n_h5_stem_task_disagree"] = n_disagree
    rest_n = int((labeled["task_label"] == "rest").sum())
    cc_n = int((labeled["task_label"] == "cognitive_control").sum())
    gg_n = int((labeled["task_label"] == "gambling").sum())
    report["expected_task_counts"] = {
        "rest": EXPECTED_N_REST,
        "cognitive_control": EXPECTED_N_CC,
        "gambling": EXPECTED_N_GG,
    }
    counts_ok = rest_n == EXPECTED_N_REST and cc_n == EXPECTED_N_CC and gg_n == EXPECTED_N_GG
    if (
        report["n_unmatched"] == 0
        and report["n_matched"] == report["n_recordings"]
        and not unexpected
        and n_disagree == 0
        and counts_ok
    ):
        report["status"] = "labels_joined"
    elif report["n_unmatched"] == 0 and not unexpected:
        report["status"] = "partial_join"
        report["failure_reason"] = "task counts or H5/stem audit did not match the pin"
    else:
        report["status"] = "partial_join"
        report["failure_reason"] = "unmatched stems or unexpected missing tasks"
    return report
