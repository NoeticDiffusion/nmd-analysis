"""Shared paths, pins and identity helpers for Apollo propofol collection."""
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
    REPO_ROOT / "data" / "raw" / "neuralmanifolddynamics_Sedation-RestingState_20260918_075713"
)
DEFAULT_CONFIG = ARTICLE_DIR / "config" / "ndt-analysis-apollo-propofol-v1.yaml"
DEFAULT_DATAINFO = ARTICLE_DIR / "metadata" / "datainfo.mat"
STEM_RE = re.compile(
    r"^(?P<subject>sub-\d+)_sedation_rest_(?P<run>run-\d+)_(?P<acq>acq-\d+)$"
)
# Original Cambridge names: "02-2010-anest 20100210 135.003"
# (subject-year-anest, YYYYMMDD, acq.run). Join uses subject + acq + run only.
DATAINFO_SUBJECT_RE = re.compile(r"^(?P<subject>\d+)-")
DATAINFO_ACQ_RUN_RE = re.compile(r"^(?P<acq>\d+)\.(?P<run>\d+)$")
DATAINFO_DATE_RE = re.compile(r"^\d{8}$")

EXPECTED_N_H5 = 80
EXPECTED_N_SUBJECTS = 20
PINNED_RELATIVE = "sub-002_sedation_rest_run-003_acq-135/sub-002_sedation_rest_run-003_acq-135.h5"
PINNED_SHA256 = "1635513f690ae01807a9495d920052ddc2a2c9a568d3b8a76bb04139bca993ba"
PINNED_DATAINFO_SHA256 = "ea8824f3ca9bd2eef0cdee3a7e1402dcc9e599f9688290cc382ae8e1a21f5608"
SIDECAR_SHA256 = {
    "command_used.txt": "8ba99da28999672064fa2032973218698e4c11c301a8d67593b0475de377b2e4",
    "config_ingest_apollo_sedation_restingstate_dynamical_families.yaml": (
        "7b9a84280960722ccf2a9501a254cec36546d8a8989aff99e03ed08455547c4a"
    ),
    "features_snapshot.json": "110a2e59d7971ca8ad93e5121206fb582a97828edc6398373af4faf36bc05da4",
    "normalization_report.json": "f03b1224b6c1b4ce66d4db216e3d7cb470b42b463aa252de1ef255fd36e5635e",
    "run_manifest.json": "52a412071444d210b71dfabc17e7e40944ebafbb3294fe1356427fea2f0edb12",
}

# Protocol phases from datainfo.mat column 2 (Chennu 2016 order). These are
# protocol labels, not consciousness claims. Not inferred from run/acq order.
PROTOCOL_PHASE_FROM_DATAINFO_ORDER = {
    1: "pre_drug_baseline",
    2: "first_protocol_sedation",
    3: "later_protocol_sedation",
    4: "recovery",
}
PROTOCOL_PHASE_SOURCE = (
    "Cambridge Apollo datainfo.mat column 2 (1=baseline, 2=mild sedation, "
    "3=moderate sedation, 4=recovery); not inferred from H5 run/acq order; "
    "moderate sedation is not automatically unresponsiveness"
)
# nmd_analysis.propofol_depth names columns 3-5 as window start/stop/score.
# The Cambridge table is: concentration µg/L, mean RT ms, n correct / 40.
DATAINFO_PACKAGE_COLUMN_REMAP = {
    "depth_window_start": "measured_concentration_ug_per_l",
    "depth_window_stop": "mean_reaction_time_ms",
    "depth_score": "n_correct_responses",
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


def parse_datainfo_name(raw_name: object) -> dict[str, Any]:
    text = str(raw_name or "").strip()
    text = text.replace("-anest-", "-anest ")
    collapsed = re.sub(r"\s+", " ", text)
    parts = collapsed.split(" ")
    empty = {
        "depth_raw_name": text,
        "subject_id": None,
        "run": None,
        "acq": None,
        "run_index": None,
        "acq_index": None,
        "datainfo_session_date": None,
        "name_parse_status": "unparsed",
    }
    if len(parts) < 2:
        return empty
    subject_match = DATAINFO_SUBJECT_RE.match(parts[0])
    acq_run_match = DATAINFO_ACQ_RUN_RE.match(parts[-1])
    if subject_match is None or acq_run_match is None:
        return empty
    subject = int(subject_match.group("subject"))
    run_index = int(acq_run_match.group("run"))
    acq_index = int(acq_run_match.group("acq"))
    session_date = None
    if len(parts) >= 3 and DATAINFO_DATE_RE.match(parts[-2]):
        session_date = parts[-2]
    return {
        "depth_raw_name": text,
        "subject_id": f"sub-{subject:03d}",
        "run": f"run-{run_index:03d}",
        "acq": f"acq-{acq_index:03d}",
        "run_index": run_index,
        "acq_index": acq_index,
        "datainfo_session_date": session_date,
        "name_parse_status": "parsed",
    }


def resolve_article_datainfo(datainfo_path: str | Path | None = None) -> Path | None:
    candidates: list[Path] = []
    if datainfo_path is not None:
        candidates.append(Path(datainfo_path))
    candidates.append(DEFAULT_DATAINFO)
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved
    from nmd_analysis.propofol_depth import resolve_datainfo_path

    fallback = resolve_datainfo_path(None)
    return fallback if fallback is not None and fallback.is_file() else None


def parse_run_stem(stem: str) -> dict[str, Any]:
    match = STEM_RE.match(stem)
    if match is None:
        return {
            "subject_id": None,
            "run": None,
            "acq": None,
            "run_index": None,
            "acq_index": None,
            "stem": stem,
            "stem_parse_status": "unparsed",
        }
    run_index = int(match.group("run").split("-", 1)[1])
    acq_index = int(match.group("acq").split("-", 1)[1])
    return {
        "subject_id": match.group("subject"),
        "run": f"run-{run_index:03d}",
        "acq": f"acq-{acq_index:03d}",
        "run_index": run_index,
        "acq_index": acq_index,
        "stem": stem,
        "stem_parse_status": "parsed",
    }


def canonical_index(token: Any, *, prefix: str) -> tuple[int | None, str | None]:
    if token is None or (isinstance(token, float) and not np.isfinite(token)):
        return None, None
    text = str(token).strip()
    match = re.search(r"(\d+)", text)
    if match is None:
        return None, None
    index = int(match.group(1))
    width = 3 if prefix in {"run", "acq"} else 0
    label = f"{prefix}-{index:0{width}d}" if width else f"{prefix}-{index}"
    return index, label


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
