"""Thin, policy-pinned wrapper for recording-parent stage descriptions."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

EPOCH_SUPPORT = Path(__file__).with_name("epoch_support.py")
DESCRIPTIVE_DEFAULT = Path(__file__).with_name("descriptive_epoch_analysis.py")
POLICY_SCHEMA = "ndt.sleep.stage_dependency_policy.v1"
MASKS = ("coverage_ok", "retained_after_qc", "geometry_valid", "coords_9d_valid")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_module(path: Path, name: str):
    if not path.is_file():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_policy(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != POLICY_SCHEMA:
        raise ValueError("unsupported stage dependency policy schema")
    if value.get("status") != "allowed_description_with_limitations":
        raise ValueError("description policy does not allow bounded summaries")
    if value.get("scientific_qualification") != "not_assessed" or value.get("stage_purity_status") != "not_assessed":
        raise ValueError("policy qualification was relaxed")
    norm = value.get("allowed_descriptive_association", {}).get("normalization", {})
    if norm.get("fit_once_across_labels") is not True or norm.get("per_stage_fit") is not False:
        raise ValueError("policy permits stage-specific fitting")
    if value.get("intrinsic_stage_dynamics", {}).get("recording_q_wq_to_stage") is not False:
        raise ValueError("policy permits recording Q/W_Q to stage")
    return value


def _mask_states(frame: pd.DataFrame) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for name in MASKS:
        column = f"producer_mask_{name}"
        if column not in frame:
            result[name] = {"true": 0, "false": 0, "unknown": len(frame), "invalid": 0}
            continue
        series = frame[column]
        numeric = pd.to_numeric(series, errors="coerce")
        finite = numeric.notna()
        missing = series.isna()
        invalid = ~missing & ~numeric.isin([0, 1])
        result[name] = {"true": int((finite & (numeric == 1)).sum()), "false": int((finite & (numeric == 0)).sum()),
                        "unknown": int(missing.sum()), "invalid": int(invalid.sum())}
    return result


def _stage_counts(frame: pd.DataFrame) -> list[dict[str, Any]]:
    catalog = [(0, "Wake"), (1, "N1"), (2, "N2"), (3, "N3"), (4, "REM"), (8, "unknown_source_code8")]
    values = pd.to_numeric(frame["stage_code"], errors="coerce")
    rows = []
    for code, label in catalog:
        selected = values == code
        rows.append({"stage_code": code, "stage_label": label, "n_rows": int(selected.sum())})
    rows.append({"stage_code": None, "stage_label": "other_or_invalid", "n_rows": int((~values.isin([x[0] for x in catalog])).sum())})
    return rows


def _mask_states_by_stage(frame: pd.DataFrame) -> list[dict[str, Any]]:
    values = pd.to_numeric(frame["stage_code"], errors="coerce")
    rows = []
    for code, label in ((0, "Wake"), (1, "N1"), (2, "N2"), (3, "N3"), (4, "REM"), (8, "unknown_source_code8")):
        subset = frame.loc[values == code]
        state = _mask_states(subset)
        rows.append({"stage_code": code, "stage_label": label, "n_rows": int(len(subset)), "mask_states": state})
    other = frame.loc[~values.isin([0, 1, 2, 3, 4, 8])]
    rows.append({"stage_code": None, "stage_label": "other_or_invalid", "n_rows": len(other), "mask_states": _mask_states(other)})
    return rows


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if hasattr(value, "item"):
        return _json_safe(value.item())
    if isinstance(value, float) and not pd.notna(value):
        return None
    return value


def run_fullnight_description(source_h5: str | Path, output: str | Path, export_config: str | Path,
                              policy: str | Path, *, epoch_support_path: str | Path = EPOCH_SUPPORT,
                              descriptive_path: str | Path = DESCRIPTIVE_DEFAULT) -> dict[str, Any]:
    """Export one H5 through the reviewed reader and summarize its table."""
    source, destination = Path(source_h5).resolve(), Path(output).resolve()
    config, policy_path = Path(export_config).resolve(), Path(policy).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError("output must be fresh and empty")
    policy_value = _load_policy(policy_path)
    config_before = sha256(config)
    policy_before = sha256(policy_path)
    epoch_path = Path(epoch_support_path).resolve()
    epoch = _load_module(epoch_path, "stage_epoch_support")
    descriptive = _load_module(Path(descriptive_path).resolve(), "stage_descriptive_helpers")
    audit_path = Path(descriptive_path).with_name("stage_dependency_audit.py")
    audit = _load_module(audit_path, "stage_dependency_audit")
    before = sha256(source)
    audit_root = destination.parent / (destination.name + ".stage_audit")
    if audit_root.exists():
        raise FileExistsError("stage-audit output must be fresh")
    audit_result = audit.audit([source], policy_path, audit_root)
    if audit_result.get("status") != "audited":
        raise ValueError("stage dependency audit did not pass")
    export_manifest = epoch.run_epoch_export(source, destination, config)
    after = sha256(source)
    if before != after:
        raise ValueError("source changed during read-only export")
    if config_before != sha256(config) or policy_before != sha256(policy_path):
        raise ValueError("configuration or policy changed during read-only export")
    table = destination / "epoch_coordinates.parquet"
    frame = pd.read_parquet(table)
    if len(frame) != export_manifest.get("n_epochs"):
        raise ValueError("export table row count mismatch")
    summaries: dict[str, Any] = {}
    for representation in ("3d", "9d"):
        eligible, reasons = descriptive.eligibility(frame, representation)
        by_stage = []
        for row in _stage_counts(frame):
            selected = frame["stage_code"].eq(row["stage_code"]) if row["stage_code"] is not None else ~frame["stage_code"].isin([0, 1, 2, 3, 4, 8])
            by_stage.append({**row, "n_eligible": int(eligible[selected].sum()),
                             "reason_true_counts": {k: int(v[selected].sum()) for k, v in reasons.items()}})
        summaries[representation] = {"eligibility_by_stage": by_stage, "eligibility_reason_counts": {k: int(v.sum()) for k, v in reasons.items()},
            "summary": _json_safe(descriptive.coordinate_summary(frame, representation, eligible, "primary").to_dict(orient="records"))}
    result = {"schema": "ndt_v3_sleep.fullnight_stage_description.v1", "status": "descriptive_development_pilot",
        "claim_status": "no_biological_claim", "source": {"path": str(source), "sha256_before": before, "sha256_after": after},
        "export_manifest": {"path": str(destination / "epoch_manifest.json"), "sha256": sha256(destination / "epoch_manifest.json")},
        "stage_dependency_audit": {"path": str(audit_root), "result": _json_safe(audit_result)},
        "config": {"path": str(config), "sha256_before": config_before, "sha256_after": sha256(config)},
        "policy": {"path": str(policy_path), "sha256_before": policy_before, "sha256_after": sha256(policy_path), "schema": policy_value["schema"]},
        "code": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve()),
                 "epoch_support": {"path": str(Path(epoch_support_path).resolve()), "sha256": sha256(Path(epoch_support_path).resolve())},
                 "descriptive_helpers": {"path": str(Path(descriptive_path).resolve()), "sha256": sha256(Path(descriptive_path).resolve())}},
        "n_rows": int(len(frame)), "stage_counts": _stage_counts(frame), "mask_state_counts": _mask_states(frame),
        "mask_state_counts_by_stage": _mask_states_by_stage(frame), "representations": summaries,
        "normalization": {"scope": "recording_parent_global", "fit_performed": False, "per_stage_fit": False},
        "source_quality_code8": "preserved_by_export_and_not_relabelled", "stage_purity_status": "not_assessed",
        "scientific_qualification": "not_assessed", "q_wq_stage_summary": False}
    (destination / "fullnight_stage_summary.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-h5", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--export-config", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--epoch-support", type=Path, default=EPOCH_SUPPORT)
    parser.add_argument("--descriptive-helper", type=Path, default=DESCRIPTIVE_DEFAULT)
    args = parser.parse_args()
    run_fullnight_description(args.source_h5, args.output, args.export_config, args.policy,
                              epoch_support_path=args.epoch_support, descriptive_path=args.descriptive_helper)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
