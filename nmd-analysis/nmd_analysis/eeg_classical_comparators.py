from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

import h5py
import numpy as np
import pandas as pd


CONVENTIONAL_EEG_PATH = "extensions/conventional_eeg/families"
SELECTED_STATS: tuple[str, ...] = (
    "mean",
    "median",
    "std",
    "iqr",
    "mad_sigma",
    "delta_mean_median",
)


def _to_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray, np.bytes_)):
        try:
            return bytes(value).decode("utf-8")
        except Exception:
            return str(value)
    return str(value)


def _dataset_scalar(group: h5py.Group, name: str) -> float:
    if name not in group:
        return float("nan")
    value = np.asarray(group[name][()]).reshape(-1)
    if value.size == 0:
        return float("nan")
    try:
        return float(value[0])
    except (TypeError, ValueError):
        return float("nan")


def _metric_name(family_name: str, comparator_name: str, stat_name: str) -> str:
    safe_family = str(family_name).strip().lower().replace("-", "_")
    safe_metric = str(comparator_name).strip().lower().replace("-", "_")
    safe_stat = str(stat_name).strip().lower().replace("-", "_")
    return f"eeg_classical_{safe_family}_{safe_metric}_{safe_stat}"


def build_eeg_classical_comparators_frame(
    h5_paths: Sequence[Path],
    *,
    coordinate_contract: str,
    base_metadata_builder: Callable[[h5py.File, Path], Dict[str, Any]],
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for h5_path in h5_paths:
        with h5py.File(h5_path, "r") as handle:
            if CONVENTIONAL_EEG_PATH not in handle:
                continue
            families_group = handle[CONVENTIONAL_EEG_PATH]
            base = dict(base_metadata_builder(handle, h5_path))
            base["block_export_kind"] = "h5_extension"
            base["block_scope"] = "global"
            base["block_space"] = "classical_eeg"
            base["space"] = "classical_eeg"
            base["network"] = "global"
            base["region_group"] = "global"
            base["requested_coordinate_contract"] = str(coordinate_contract)
            base["resolved_coordinate_contract"] = str(coordinate_contract)
            base["source_dataset_path"] = f"/{CONVENTIONAL_EEG_PATH}"

            found_metrics = 0
            n_values: List[float] = []
            nan_frac_values: List[float] = []

            for family_name, family_group in families_group.items():
                if not isinstance(family_group, h5py.Group):
                    continue
                for comparator_name, comparator_group in family_group.items():
                    if not isinstance(comparator_group, h5py.Group):
                        continue
                    family_label = _to_text(family_name) or "unknown_family"
                    comparator_label = _to_text(comparator_name) or "unknown_metric"
                    n_values.append(_dataset_scalar(comparator_group, "n"))
                    nan_frac_values.append(_dataset_scalar(comparator_group, "nan_frac"))
                    for stat_name in SELECTED_STATS:
                        metric_name = _metric_name(family_label, comparator_label, stat_name)
                        base[metric_name] = _dataset_scalar(comparator_group, stat_name)
                        found_metrics += 1

            finite_n = np.asarray([value for value in n_values if np.isfinite(value)], dtype=float)
            finite_nan_frac = np.asarray([value for value in nan_frac_values if np.isfinite(value)], dtype=float)
            min_n = float(np.min(finite_n)) if finite_n.size else float("nan")
            max_nan_frac = float(np.max(finite_nan_frac)) if finite_nan_frac.size else 0.0
            base["n_windows"] = int(min_n) if np.isfinite(min_n) else float("nan")
            base["finite_ok"] = bool(found_metrics > 0 and np.isfinite(min_n) and min_n >= 3 and max_nan_frac < 1.0)
            base["not_testable"] = bool(found_metrics == 0 or (np.isfinite(min_n) and min_n < 3))
            if found_metrics == 0:
                base["not_testable_reason"] = "missing_conventional_eeg_extension"
            elif np.isfinite(min_n) and min_n < 3:
                base["not_testable_reason"] = "lt3_windows"
            else:
                base["not_testable_reason"] = None
            rows.append(base)
    return pd.DataFrame(rows)
