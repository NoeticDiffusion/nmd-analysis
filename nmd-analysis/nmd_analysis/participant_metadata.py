from __future__ import annotations

import json
from typing import Any, Dict, Optional

import h5py
import numpy as np


def to_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return to_text(value.item())
        return json.dumps([to_text(item) for item in value.tolist()], ensure_ascii=True)
    if isinstance(value, (list, tuple)):
        return json.dumps([to_text(item) for item in value], ensure_ascii=True)
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        try:
            return bytes(value).decode("utf-8")
        except Exception:
            return str(value)
    return str(value)


def read_json_dataset(handle: h5py.File, dataset_path: str) -> Dict[str, Any]:
    if dataset_path not in handle:
        return {}
    try:
        raw = handle[dataset_path][()]
        if isinstance(raw, (bytes, bytearray, np.bytes_)):
            raw = bytes(raw).decode("utf-8")
        parsed = json.loads(str(raw))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def coerce_optional_float(value: Any) -> float:
    if value is None:
        return float("nan")
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in {"", "n/a", "na", "nan", "none", "null"}:
            return float("nan")
        value = cleaned
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def derive_medication_metadata(group_value: Any, row_json: Dict[str, Any]) -> Dict[str, Any]:
    group_text = (to_text(group_value) or "").strip()
    group_norm = group_text.lower()
    cpz_at_scan = coerce_optional_float(row_json.get("CPZ_at_scan"))

    medication_group: Optional[str]
    if group_norm == "control":
        medication_group = "Healthy"
    elif group_norm == "fep":
        medication_group = "FEP medicated" if np.isfinite(cpz_at_scan) and cpz_at_scan > 0 else "FEP unmedicated"
    else:
        medication_group = None

    return {
        "cpz_at_scan": cpz_at_scan,
        "medication_group": medication_group,
    }
