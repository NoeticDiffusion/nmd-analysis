"""G1: protocol-phase labels from original datainfo.mat only.

Run/acq order and H5 condition=sedation never fill missing phases.
No dynamical outcome arrays are read.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.io import loadmat

from apollo_common import (
    PROTOCOL_PHASE_FROM_DATAINFO_ORDER,
    PROTOCOL_PHASE_SOURCE,
    DEFAULT_DATAINFO,
    PINNED_DATAINFO_SHA256,
    parse_datainfo_name,
    resolve_article_datainfo,
    scalar,
    sha256_file,
)

from nmd_analysis.propofol_depth import ORDER_TO_CONDITION


def _cell_float(value: Any) -> float:
    if value is None:
        return float("nan")
    try:
        number = float(scalar(value))
    except (TypeError, ValueError):
        return float("nan")
    return number


def _iter_datainfo_rows(raw: Any) -> list[list[Any]]:
    if raw is None:
        return []
    array = np.asarray(raw, dtype=object)
    if array.size == 0:
        return []
    if array.ndim == 1:
        rows = []
        for item in array.tolist():
            if isinstance(item, (list, tuple)):
                rows.append(list(item))
            else:
                nested = np.asarray(item, dtype=object)
                rows.append(nested.tolist() if nested.ndim else [scalar(item)])
        return rows
    return [list(row) for row in array.tolist()]


def load_source_labels(datainfo_path: str | Path | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    resolved = resolve_article_datainfo(datainfo_path)
    report: dict[str, Any] = {
        "gate": "G1",
        "status": "blocked",
        "datainfo_path": str(resolved.resolve()) if resolved is not None else None,
        "datainfo_sha256": sha256_file(resolved) if resolved is not None and resolved.is_file() else None,
        "datainfo_sha256_expected": PINNED_DATAINFO_SHA256,
        "default_datainfo_path": str(DEFAULT_DATAINFO),
        "label_source": PROTOCOL_PHASE_SOURCE,
        "legacy_alias_map": dict(ORDER_TO_CONDITION),
        "n_datainfo_rows": 0,
        "n_unparsed_names": 0,
        "unparsed_names": [],
        "duplicate_keys": [],
        "note": (
            "H5 condition=sedation is not a protocol phase. Missing labels stay missing. "
            "nmd_analysis.propofol_depth.ORDER_TO_CONDITION maps order 3 to 'unresponsive'; "
            "the Cambridge table encodes moderate sedation there. Package columns "
            "depth_window_start/stop/score are remapped to concentration, mean RT, and "
            "n_correct_responses. Article G1 parses names such as "
            "'02-2010-anest 20100210 135.003' as subject + acq.run; the date token is "
            "kept as metadata and is not a join key. The package name parser is not "
            "used as the join source."
        ),
        "package_column_remap": {
            "depth_window_start": "measured_concentration_ug_per_l",
            "depth_window_stop": "mean_reaction_time_ms",
            "depth_score": "n_correct_responses",
        },
    }
    if resolved is None:
        report["failure_reason"] = "datainfo.mat not found; protocol phases cannot be assigned"
        return pd.DataFrame(), report
    if resolved.resolve() == DEFAULT_DATAINFO.resolve() and report["datainfo_sha256"] != PINNED_DATAINFO_SHA256:
        report["failure_reason"] = "article metadata/datainfo.mat hash differs from pin"
        return pd.DataFrame(), report
    loaded = loadmat(str(resolved.resolve()), squeeze_me=True, struct_as_record=False)
    raw = loaded.get("datainfo")
    report["mat_keys"] = sorted(str(key) for key in loaded if not str(key).startswith("__"))
    rows = _iter_datainfo_rows(raw)
    report["n_mat_rows"] = int(len(rows))
    table_rows: list[dict[str, Any]] = []
    unparsed: list[str] = []
    for row in rows:
        if not row:
            continue
        parsed = parse_datainfo_name(scalar(row[0]))
        if parsed["name_parse_status"] != "parsed":
            unparsed.append(parsed["depth_raw_name"])
            continue
        try:
            depth_order = int(scalar(row[1])) if len(row) > 1 else None
        except (TypeError, ValueError):
            unparsed.append(parsed["depth_raw_name"])
            continue
        concentration = _cell_float(row[2]) if len(row) > 2 else float("nan")
        mean_rt = _cell_float(row[3]) if len(row) > 3 else float("nan")
        n_correct = _cell_float(row[4]) if len(row) > 4 else float("nan")
        table_rows.append(
            {
                "subject_id": parsed["subject_id"],
                "run": parsed["run"],
                "acq": parsed["acq"],
                "run_index": parsed["run_index"],
                "acq_index": parsed["acq_index"],
                "protocol_phase_id": depth_order,
                "protocol_phase_label": PROTOCOL_PHASE_FROM_DATAINFO_ORDER.get(depth_order),
                "protocol_phase_source": PROTOCOL_PHASE_SOURCE,
                "datainfo_legacy_condition": ORDER_TO_CONDITION.get(depth_order, f"order_{depth_order}"),
                "depth_raw_name": parsed["depth_raw_name"],
                "datainfo_session_date": parsed["datainfo_session_date"],
                "measured_concentration": concentration,
                "mean_reaction_time_ms": mean_rt,
                "n_correct_responses": n_correct,
                "responsiveness_score": n_correct,
                "concentration_status": "recorded" if np.isfinite(concentration) else "not_recorded",
                "behavioural_task_status": "recorded" if np.isfinite(n_correct) else "not_recorded",
            }
        )
    report["n_unparsed_names"] = int(len(unparsed))
    report["unparsed_names"] = unparsed
    if not table_rows:
        report["failure_reason"] = "datainfo.mat produced no joinable rows"
        return pd.DataFrame(), report
    out = pd.DataFrame(table_rows)
    key_cols = ["subject_id", "run_index", "acq_index"]
    duplicated = out.duplicated(subset=key_cols, keep=False)
    report["n_datainfo_rows"] = int(len(out))
    report["duplicate_keys"] = out.loc[duplicated, key_cols].to_dict("records") if duplicated.any() else []
    report["n_subjects"] = int(out["subject_id"].nunique())
    report["depth_order_counts"] = {
        str(key): int(value) for key, value in out["protocol_phase_id"].value_counts(dropna=False).items()
    }
    if report["duplicate_keys"]:
        report["failure_reason"] = "duplicate datainfo subject/run/acq keys"
        return out, report
    if unparsed:
        report["status"] = "partial_parse"
        report["failure_reason"] = "some datainfo names could not be parsed"
        return out, report
    report["status"] = "labels_loaded"
    return out, report


def assign_labels(inventory: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    """Left-join original labels. Never infer phase from within-subject run order."""
    empty_fields = {
        "protocol_phase_id": pd.NA,
        "protocol_phase_label": pd.NA,
        "protocol_phase_status": "missing",
        "protocol_phase_source": "not_recorded",
        "datainfo_legacy_condition": pd.NA,
        "responsiveness_score": pd.NA,
        "measured_concentration": pd.NA,
        "mean_reaction_time_ms": pd.NA,
        "n_correct_responses": pd.NA,
        "concentration_status": "not_recorded",
        "behavioural_task_status": "not_recorded",
        "label_join_status": "unmatched",
        "depth_raw_name": pd.NA,
        "datainfo_session_date": pd.NA,
    }
    out = inventory.copy()
    for column, value in empty_fields.items():
        if column not in out.columns:
            out[column] = value
    if labels is None or labels.empty:
        return out
    keep = [
        "subject_id",
        "run_index",
        "acq_index",
        "protocol_phase_id",
        "protocol_phase_label",
        "protocol_phase_source",
        "datainfo_legacy_condition",
        "responsiveness_score",
        "measured_concentration",
        "mean_reaction_time_ms",
        "n_correct_responses",
        "concentration_status",
        "behavioural_task_status",
        "depth_raw_name",
        "datainfo_session_date",
    ]
    present = [column for column in keep if column in labels.columns]
    right = labels[present].copy()
    out = out.drop(columns=[column for column in present if column not in {"subject_id", "run_index", "acq_index"}], errors="ignore")
    merged = out.merge(right, on=["subject_id", "run_index", "acq_index"], how="left")
    matched = merged["protocol_phase_label"].notna()
    merged["protocol_phase_status"] = matched.map(lambda ok: "recorded" if ok else "missing")
    merged.loc[~matched, "protocol_phase_source"] = "not_recorded"
    merged["label_join_status"] = matched.map(lambda ok: "matched" if ok else "unmatched")
    if "concentration_status" not in merged.columns:
        merged["concentration_status"] = "not_recorded"
    merged.loc[~matched, "concentration_status"] = "not_recorded"
    return merged


def label_audit(labeled: pd.DataFrame, source_report: dict[str, Any]) -> dict[str, Any]:
    report = dict(source_report)
    report["n_recordings"] = int(len(labeled))
    report["n_matched"] = int((labeled.get("label_join_status") == "matched").sum()) if not labeled.empty else 0
    report["n_unmatched"] = int((labeled.get("label_join_status") == "unmatched").sum()) if not labeled.empty else 0
    if labeled.empty:
        report["h1_h2_phase_coverage"] = "not_assessed"
        return report
    by_subject = labeled.groupby("subject_id")["protocol_phase_id"].agg(lambda values: set(pd.to_numeric(values, errors="coerce").dropna().astype(int)))
    has_primary = by_subject.map(lambda phases: 1 in phases and 2 in phases)
    report["n_subjects_with_baseline_and_first_sedation"] = int(has_primary.sum())
    report["subjects_missing_primary_phases"] = sorted(by_subject.index[~has_primary].astype(str))
    report["h5_condition_values"] = sorted(labeled["h5_condition"].dropna().astype(str).unique().tolist()) if "h5_condition" in labeled else []
    if report.get("status") == "labels_loaded" and report["n_unmatched"] == 0 and report["n_matched"] == report["n_recordings"]:
        report["status"] = "labels_joined"
    elif report.get("status") == "labels_loaded":
        report["status"] = "partial_join"
        report["failure_reason"] = "some recordings have no datainfo phase"
    report["confirmatory_contrasts"] = False
    return report
