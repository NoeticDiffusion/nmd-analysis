from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Optional

import numpy as np
import pandas as pd
from scipy.io import loadmat

DEFAULT_DATAINFO_PATHS = [
    Path(r"G:\Science_Datasets_longtime_storage\apollo\sedation-restingstate\Sedation-RestingState\datainfo.mat"),
]

ORDER_TO_CONDITION = {
    1: "awake",
    2: "sedated",
    3: "unresponsive",
    4: "recovery",
}

SEDATION_DATASET_HINTS = {
    "sedation-restingstate",
    "sedation_restingstate",
    "sedation",
}


def _candidate_datainfo_paths() -> Iterable[Path]:
    env_path = os.environ.get("NDT_SEDATION_DATAINFO_MAT")
    if env_path:
        yield Path(env_path)
    yield from DEFAULT_DATAINFO_PATHS


def resolve_datainfo_path(explicit_path: str | Path | None = None) -> Optional[Path]:
    if explicit_path is not None:
        candidate = Path(explicit_path)
        return candidate if candidate.exists() else None
    for candidate in _candidate_datainfo_paths():
        if candidate.exists():
            return candidate
    return None


def _normalize_datainfo_name(raw_name: object) -> Optional[tuple[str, str, str]]:
    text = str(raw_name or "").strip()
    if not text:
        return None
    text = text.replace("-anest-", "-anest ")
    parts = text.split()
    if len(parts) < 3:
        return None
    subject_match = re.match(r"^(?P<subject>\d+)-", parts[0])
    run_match = re.match(r"^(?P<acq>\d+)\.(?P<run>\d+)$", parts[-1])
    if subject_match is None or run_match is None:
        return None
    subject = f"sub-{int(subject_match.group('subject')):03d}"
    run = f"run-{run_match.group('run')}"
    acq = f"acq-{run_match.group('acq')}"
    return subject, run, acq


@lru_cache(maxsize=4)
def load_propofol_depth_table(path: str) -> pd.DataFrame:
    raw = loadmat(path, squeeze_me=True, struct_as_record=False).get("datainfo")
    if raw is None:
        return pd.DataFrame()
    rows = np.asarray(raw, dtype=object).tolist()
    table_rows = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        key = _normalize_datainfo_name(row[0])
        if key is None:
            continue
        subject_id, run, acq = key
        try:
            depth_order = int(row[1])
        except (TypeError, ValueError):
            continue
        table_rows.append(
            {
                "subject_id": subject_id,
                "run": run,
                "acq": acq,
                "depth_order": depth_order,
                "depth_condition": ORDER_TO_CONDITION.get(depth_order, f"order_{depth_order}"),
                "depth_raw_name": str(row[0]),
                "depth_window_start": float(row[2]) if len(row) > 2 else float("nan"),
                "depth_window_stop": float(row[3]) if len(row) > 3 else float("nan"),
                "depth_score": float(row[4]) if len(row) > 4 else float("nan"),
            }
        )
    if not table_rows:
        return pd.DataFrame()
    return pd.DataFrame(table_rows).drop_duplicates(subset=["subject_id", "run", "acq"])


def looks_like_propofol_dataset(dataset: str | None) -> bool:
    text = str(dataset or "").strip().lower()
    return any(token in text for token in SEDATION_DATASET_HINTS)


def _extract_subject_run_acq(frame: pd.DataFrame) -> pd.DataFrame:
    if "dataset_id" not in frame.columns:
        return pd.DataFrame(index=frame.index)
    extracted = frame["dataset_id"].astype(str).str.extract(
        r"(?P<subject_id>sub-[^:]+).*?(?P<run>run-\d+).*?(?P<acq>acq-[^:_]+)"
    )
    return extracted.reindex(frame.index)


def annotate_propofol_depth(
    frame: pd.DataFrame,
    *,
    dataset: str | None = None,
    datainfo_path: str | Path | None = None,
    override_condition: bool = True,
) -> pd.DataFrame:
    if frame.empty:
        return frame
    dataset_hint = dataset
    if dataset_hint is None and "dataset_id" in frame.columns:
        sample_ids = frame["dataset_id"].dropna().astype(str)
        if not sample_ids.empty:
            dataset_hint = sample_ids.iloc[0]
    if not looks_like_propofol_dataset(dataset_hint):
        return frame
    resolved_path = resolve_datainfo_path(datainfo_path)
    if resolved_path is None:
        return frame
    depth_table = load_propofol_depth_table(str(resolved_path.resolve()))
    if depth_table.empty:
        return frame
    required = {"subject_id", "run", "acq"}
    if not required.issubset(frame.columns):
        return frame
    out = frame.copy()
    extracted = _extract_subject_run_acq(out)
    for column in ("subject_id", "run", "acq"):
        if column in extracted.columns:
            out[column] = out[column].combine_first(extracted[column])
    # Drop any columns that depth_table would contribute so the merge never
    # produces _x/_y suffixes on re-annotation (parquet rows may already carry
    # these columns from a prior annotation pass with acq = None, which leaves
    # them as null and prevents the override check from firing).
    depth_side_cols = (set(depth_table.columns) - {"subject_id", "run", "acq"}) | {"condition_original"}
    out = out.drop(columns=[c for c in depth_side_cols if c in out.columns], errors="ignore")
    merged = out.merge(depth_table, on=["subject_id", "run", "acq"], how="left")
    if "condition" in merged.columns:
        merged["condition_original"] = merged["condition"]
    if override_condition and "depth_condition" in merged.columns:
        merged["condition"] = merged["depth_condition"].combine_first(merged.get("condition"))
    return merged
