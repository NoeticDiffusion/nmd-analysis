"""G0: complete SHA-256 inventory. No outcome arrays, no task contrasts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import h5py
import pandas as pd

from ds04511_common import canonical_index, parse_run_stem, scalar, sha256_file

try:
    from nmd_analysis.legacy_adapters import _base_h5_metadata_from_handle
except ImportError:  # pragma: no cover - path is injected by ds04511_common
    _base_h5_metadata_from_handle = None


def inspect_file(path: Path, *, root: Path) -> dict[str, Any]:
    parsed = parse_run_stem(path.stem)
    row: dict[str, Any] = {
        "source_h5": str(path.resolve()),
        "relative_path": str(path.relative_to(root)).replace("\\", "/"),
        "stem": path.stem,
        "sha256": sha256_file(path),
        "bytes": int(path.stat().st_size),
        "read_ok": False,
        "read_error": None,
        **parsed,
        "h5_condition": None,
        "h5_task": None,
        "h5_group": None,
        "dataset_id": None,
        "schema_version": None,
        "mndm_version": None,
        "primary_coordinate_layer": None,
        "primary_coordinate_contract": None,
        "n_timepoints": None,
        "time_start_sec": None,
        "time_end_sec": None,
        "identity_source": "filename_stem",
    }
    try:
        with h5py.File(path, "r") as handle:
            if _base_h5_metadata_from_handle is not None:
                meta = _base_h5_metadata_from_handle(handle, path)
                if meta.get("session") and row.get("session") is None:
                    row["session"] = meta.get("session")
                row["h5_condition"] = meta.get("condition")
                row["h5_task"] = meta.get("task")
                row["h5_group"] = meta.get("group")
                row["dataset_id"] = meta.get("dataset_id")
                if meta.get("subject_id") and row.get("subject_id") is None:
                    row["subject_id"] = meta.get("subject_id")
                    row["identity_source"] = "h5_attrs_or_participant_mapped_json"
                if meta.get("run"):
                    run_index, run_label = canonical_index(meta.get("run"), prefix="run")
                    if run_index is not None and row.get("run_index") is None:
                        row["run_index"] = run_index
                        row["run"] = run_label
            attrs = handle.attrs
            row["schema_version"] = scalar(attrs.get("schema_version"))
            row["mndm_version"] = scalar(attrs.get("mndm_version"))
            row["primary_coordinate_layer"] = scalar(attrs.get("primary_coordinate_layer"))
            row["primary_coordinate_contract"] = scalar(attrs.get("primary_coordinate_contract"))
            if "time" in handle:
                time = handle["time"][()]
                row["n_timepoints"] = int(time.size)
                if time.size:
                    row["time_start_sec"] = float(time[0])
                    row["time_end_sec"] = float(time[-1])
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001 - inventory must keep going
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def build_inventory(files: list[Path], *, root: Path) -> pd.DataFrame:
    rows = [inspect_file(path, root=root) for path in files]
    return pd.DataFrame(rows)
