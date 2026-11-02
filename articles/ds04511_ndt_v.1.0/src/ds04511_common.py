"""Shared paths, pins and identity helpers for ds004511 NDT v1.0 collection."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np

ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[1]
NMD_ANALYSIS_ROOT = REPO_ROOT / "nmd-analysis"
DEFAULT_H5_ROOT = (
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_ds004511_20260921_050009"
)
DEFAULT_CONFIG = ARTICLE_DIR / "config" / "ndt-analysis-ds004511-v1.yaml"
STEM_RE = re.compile(
    r"^(?P<subject>sub-\w+)_ses-(?P<session>\w+)_"
    r"(?P<task>gambling|cognitive_control|rest)_run-(?P<run>\w+)$"
)

TASKS = ("rest", "cognitive_control", "gambling")
TASK_DISPLAY = {
    "rest": "Rest",
    "cognitive_control": "Cognitive Control (CC)",
    "gambling": "Gambling (GG)",
}
TASK_SHORT = {
    "rest": "Rest",
    "cognitive_control": "CC",
    "gambling": "GG",
}
TASK_SOURCE = (
    "BIDS-style NMD folder/H5 stem "
    "(sub-*_ses-*_{gambling|cognitive_control|rest}_run-*); "
    "not inferred from within-subject run order; "
    "H5 participant mapped_json task is an audit field only"
)
DOCUMENTED_MISSING_TASKS = {
    ("sub-S200203", "gambling"): (
        "OpenNeuro ds004511 README: sub-S200203 has no Gambling Game EEG acquisition"
    ),
}

EXPECTED_N_H5 = 134
EXPECTED_N_SUBJECTS = 45
EXPECTED_N_REST = 45
EXPECTED_N_CC = 45
EXPECTED_N_GG = 44
PINNED_RELATIVE = (
    "sub-S200116_ses-01_cognitive_control_run-01/"
    "sub-S200116_ses-01_cognitive_control_run-01.h5"
)
PINNED_SHA256 = "bcdafda337f7ad0e1e9e41378de41ee2e90118a358132bd328e74aae06a0109f"
SIDECAR_SHA256 = {
    "command_used.txt": "5f9a333b57e6e470281f8f2fcfc22599935196166a9035e69cd29d20377a8ef3",
    "config_ingest_ds004511_dynamical_families.yaml": (
        "8051b277dd15f8a23a97404abc44f9336a71467083beb24136603b2cf4343eee"
    ),
    "features_snapshot.json": "bb19d3d2db5c8b83c010120a4577914a66ac3e7f7c59946506aa46fa4ddbe9b4",
    "normalization_report.json": "af9195cc1e368807dbbde06eb9ddebc329b42325783146c7907161581a4e6341",
    "run_manifest.json": "abbadf8902e6a6ad35daab8a6ed0648397df2e0d44e2f2d420819fd4f6ef659f",
}

MIN_VALID_TIMEPOINTS = 30
MIN_VALID_FRACTION = 0.5


def ensure_nmd_analysis_on_path() -> Path:
    root = str(NMD_ANALYSIS_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    return NMD_ANALYSIS_ROOT


ensure_nmd_analysis_on_path()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (bytes, np.bytes_)):
        return value.decode("utf-8")
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(payload), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return path


def scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bytes, np.bytes_)):
        return value.decode("utf-8")
    if isinstance(value, np.generic):
        return scalar(value.item())
    if isinstance(value, np.ndarray) and value.ndim == 0:
        return scalar(value.item())
    return value


def canonical_index(token: Any, *, prefix: str) -> tuple[int | None, str | None]:
    if token is None or (isinstance(token, float) and not np.isfinite(token)):
        return None, None
    text = str(token).strip()
    match = re.search(r"(\d+)", text)
    if match is None:
        return None, None
    index = int(match.group(1))
    width = 2 if prefix in {"run", "session"} else 0
    label = f"{prefix}-{index:0{width}d}" if width else f"{prefix}-{index}"
    return index, label


def parse_run_stem(stem: str) -> dict[str, Any]:
    match = STEM_RE.match(stem)
    empty = {
        "subject_id": None,
        "session": None,
        "session_index": None,
        "run": None,
        "run_index": None,
        "task_label": None,
        "stem": stem,
        "stem_parse_status": "unparsed",
    }
    if match is None:
        return empty
    run_index, run_label = canonical_index(match.group("run"), prefix="run")
    session_index, session_label = canonical_index(match.group("session"), prefix="ses")
    return {
        "subject_id": match.group("subject"),
        "session": session_label,
        "session_index": session_index,
        "run": run_label,
        "run_index": run_index,
        "task_label": match.group("task"),
        "stem": stem,
        "stem_parse_status": "parsed",
    }


def discover_h5_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.h5") if path.is_file())


def assert_fresh_output(output_root: Path) -> None:
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"collection output must be fresh and empty: {output_root}")


def pin_source_bundle(root: Path) -> dict[str, Any]:
    files = discover_h5_files(root)
    pinned = root / PINNED_RELATIVE
    actual = sha256_file(pinned) if pinned.is_file() else "missing"
    sidecar = {}
    mismatches = []
    for name, expected in SIDECAR_SHA256.items():
        path = root / name
        if not path.is_file():
            mismatches.append(f"missing sidecar {name}")
            continue
        digest = sha256_file(path)
        sidecar[name] = digest
        if digest != expected:
            mismatches.append(f"sidecar hash changed: {name}")
    if len(files) != EXPECTED_N_H5:
        mismatches.append(f"expected {EXPECTED_N_H5} H5 files, found {len(files)}")
    if actual != PINNED_SHA256:
        mismatches.append("pinned first H5 hash or path changed")
    if mismatches:
        raise RuntimeError("source bundle pin failed: " + "; ".join(mismatches))
    return {
        "h5_root": str(root.resolve()),
        "n_h5": len(files),
        "files": files,
        "pinned_relative": PINNED_RELATIVE,
        "pinned_sha256": actual,
        "sidecar_sha256": sidecar,
    }
