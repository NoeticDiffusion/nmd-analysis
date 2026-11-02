from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import sklearn
import scipy


ANALYSIS_DIR = Path(__file__).resolve().parent
H1_SCRIPT = ANALYSIS_DIR / "analyze_h1.py"
NMD_DEFAULT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
BENCH_DIR = NMD_DEFAULT / "project" / "new_mnps_v.3.1" / "bench_001"
DEFAULT_FREEZE = BENCH_DIR / "h1_analysis_freeze_v3.json"
DEFAULT_SELECTION = BENCH_DIR / "selection_manifest_outcome_blind.json"
DEFAULT_EXECUTION = BENCH_DIR / "h1_execution_manifest.json"
DEFAULT_PROTOCOL = ANALYSIS_DIR / "legacy_loss_001_protocol.md"
DEFAULT_OUTPUT = BENCH_DIR / "outputs" / "legacy_loss_001_20261007_v1"

STAGES = (
    ("raw_v2_inputs", "RAW_INPUT_FEATURES"),
    ("projection_z_inputs", "RAW_INPUT_FEATURES"),
    ("legacy_9d", "LEGACY_FEATURES"),
    ("legacy_3d_from_v2", ("m", "d", "e")),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_h1_module():
    spec = importlib.util.spec_from_file_location("bench001_analyze_h1", H1_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load H1 helpers from {H1_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def decode_scalar(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def read_projection_z_features(
    path: Path,
    h1: Any,
    *,
    subject: str,
    state: str,
) -> tuple[dict[str, float], list[dict[str, Any]], dict[str, dict[str, Any]], bool]:
    coverage: list[dict[str, Any]] = []
    feature_values: dict[str, float] = {}
    with h5py.File(path, "r") as h5:
        starts = np.asarray(h5["window_start"], dtype=np.float64).reshape(-1)
        ends = np.asarray(h5["window_end"], dtype=np.float64).reshape(-1)
        if starts.shape != ends.shape:
            raise ValueError(f"Window bounds mismatch in {path}")
        intervals = list(zip(starts.tolist(), ends.tolist(), strict=True))
        names = h1._decode_names(h5["features_projection_z/names"])
        values = np.asarray(h5["features_projection_z/values"], dtype=np.float64)
        if values.ndim != 2 or values.shape != (len(intervals), len(names)):
            raise ValueError(f"projection_z shape mismatch in {path}")
        positions = {name: index for index, name in enumerate(names)}
        for feature in h1.RAW_INPUT_FEATURES:
            if feature not in positions:
                raise ValueError(f"Required projection_z input {feature!r} is missing in {path}")
            aggregate, support = h1._supported_aggregate(
                feature,
                values[:, positions[feature]].tolist(),
                intervals,
                subject=subject,
                state=state,
                arm="projection_z_inputs",
            )
            feature_values[feature] = float(aggregate[0])
            coverage.append(support)

        payload_raw = h5["manifest_json"][()]
        payload = json.loads(decode_scalar(payload_raw))
        transform_metadata: dict[str, dict[str, Any]] = {}
        baselines = payload.get("feature_baselines", {})
        for feature in h1.RAW_INPUT_FEATURES:
            baseline = baselines.get(feature, {})
            transform_metadata[feature] = {
                "transformation_applied": baseline.get("transformation_applied"),
                "anchor_applied": baseline.get("anchor_applied"),
                "fit_scope": baseline.get("fit_scope"),
                "fit_population_count": baseline.get("fit_population_count"),
            }

        mnps_3d_info = payload.get("mnps_3d", {})
        from_v2 = (
            mnps_3d_info.get("mode_requested") == "from_v2"
            and mnps_3d_info.get("mode_effective") == "from_v2"
            and mnps_3d_info.get("from_v2", {}).get("fallback_reason") is None
        )
        if not from_v2:
            axes = ("m", "d", "e")
            for axis in axes:
                feature_values[f"3d_{axis}"] = math.nan
                coverage.append({
                    "subject": subject,
                    "state": state,
                    "arm": "legacy_3d_from_v2",
                    "feature": axis,
                    "finite_window_count": 0,
                    "total_window_count": len(intervals),
                    "supported_seconds": 0.0,
                    "minimum_supported_seconds": h1.MIN_SUPPORTED_SEC,
                    "support_pass": False,
                    "reason": "mnps_3d_not_effective_from_v2_without_fallback",
                })
            return feature_values, coverage, transform_metadata, False

        axes = payload.get("mnps_axes", {}).get("names", [])
        if axes != ["m", "d", "e"]:
            raise ValueError(f"Unexpected MNPS 3D axis order in {path}: {axes}")
        values_3d = np.asarray(h5["mnps_3d"], dtype=np.float64)
        valid = np.asarray(h5["qc/windows/mnps_3d_valid"], dtype=bool).reshape(-1)
        if values_3d.shape != (len(intervals), 3) or valid.shape != (len(intervals),):
            raise ValueError(f"MNPS 3D shape mismatch in {path}")
        for index, axis in enumerate(axes):
            aggregate, support = h1._supported_aggregate(
                axis,
                values_3d[:, index].tolist(),
                intervals,
                subject=subject,
                state=state,
                arm="legacy_3d_from_v2",
                prevalidated=valid,
            )
            feature_values[f"3d_{axis}"] = float(aggregate[0])
            coverage.append(support)

    return feature_values, coverage, transform_metadata, True


def feature_map_for_stage(
    stage: str,
    subject: str,
    state: str,
    records: dict[tuple[str, str], Any],
    extra: dict[tuple[str, str], dict[str, float]],
) -> dict[str, float]:
    key = (subject, state)
    if stage == "raw_v2_inputs":
        return records[key].features["raw_v2_inputs"]
    if stage == "legacy_9d":
        return records[key].features["legacy_v2"]
    if stage == "projection_z_inputs":
        return extra[key]["projection_z_inputs"]
    if stage == "legacy_3d_from_v2":
        return {axis: extra[key][f"3d_{axis}"] for axis in ("m", "d", "e")}
    raise KeyError(stage)


def complete_common_subjects(
    subjects: list[str],
    records: dict[tuple[str, str], Any],
    extra: dict[tuple[str, str], dict[str, float]],
    h1: Any,
) -> tuple[list[str], dict[str, tuple[str, ...]]]:
    stage_features = {
        "raw_v2_inputs": h1.RAW_INPUT_FEATURES,
        "projection_z_inputs": h1.RAW_INPUT_FEATURES,
        "legacy_9d": h1.LEGACY_FEATURES,
        "legacy_3d_from_v2": ("m", "d", "e"),
    }
    incomplete: dict[str, tuple[str, ...]] = {}
    complete: list[str] = []
    for subject in subjects:
        failed: list[str] = []
        for state in h1.STATES:
            for stage, names in stage_features.items():
                values = feature_map_for_stage(stage, subject, state, records, extra)
                if any(name not in values or not np.isfinite(values[name]) for name in names):
                    failed.append(f"{state}:{stage}")
        if failed:
            incomplete[subject] = tuple(failed)
        else:
            complete.append(subject)
    return complete, incomplete


def build_matrix(
    stage: str,
    subjects: list[str],
    records: dict[tuple[str, str], Any],
    extra: dict[tuple[str, str], dict[str, float]],
    h1: Any,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[tuple[str, str, int]]]:
    feature_names = {
        "raw_v2_inputs": h1.RAW_INPUT_FEATURES,
        "projection_z_inputs": h1.RAW_INPUT_FEATURES,
        "legacy_9d": h1.LEGACY_FEATURES,
        "legacy_3d_from_v2": ("m", "d", "e"),
    }[stage]
    rows: list[list[float]] = []
    labels: list[int] = []
    groups: list[str] = []
    row_keys: list[tuple[str, str, int]] = []
    for subject in subjects:
        for state, label in (("EyesClosed", 0), ("EyesOpen", 1)):
            values = feature_map_for_stage(stage, subject, state, records, extra)
            rows.append([float(values[name]) for name in feature_names])
            labels.append(label)
            groups.append(subject)
            row_keys.append((subject, state, label))
    return (
        np.asarray(rows, dtype=np.float64),
        np.asarray(labels, dtype=np.int8),
        np.asarray(groups),
        row_keys,
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {args.out_dir}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    h1 = load_h1_module()

    frozen = json.loads(args.freeze_manifest.read_text(encoding="utf-8"))
    run_dir = Path(frozen["run_dir"])
    h1.validate_analysis_freeze(
        args.freeze_manifest,
        run_dir,
        args.selection_manifest,
        args.execution_manifest,
    )
    if sha256(H1_SCRIPT) != frozen["analysis_script"]["sha256"]:
        raise ValueError("H1 analysis helper script differs from the H1 freeze")

    expected_inputs = {
        str(Path(item["path"]).resolve()): item["sha256"]
        for item in frozen["input_h5_sha256"]
    }
    files = sorted(run_dir.rglob("*.h5"))
    if {str(path.resolve()) for path in files} != set(expected_inputs):
        raise ValueError("H1 HDF5 file set differs from its frozen manifest")
    selected = h1.load_selected_subjects(args.selection_manifest)
    if len(files) != len(selected) * 2:
        raise ValueError(f"Expected {len(selected) * 2} HDF5 files, found {len(files)}")

    records: dict[tuple[str, str], Any] = {}
    extra: dict[tuple[str, str], dict[str, Any]] = {}
    support_rows: list[dict[str, Any]] = []
    transform_contracts: dict[str, dict[str, set[str]]] = {
        feature: {
            "transformation_applied": set(),
            "anchor_applied": set(),
            "fit_scope": set(),
        }
        for feature in h1.RAW_INPUT_FEATURES
    }
    from_v2_count = 0

    for path in files:
        base = h1.load_h1_recording(path)
        key = (base.subject, base.state)
        if key in records:
            raise ValueError(f"Duplicate H1 recording: {key}")
        records[key] = base
        stage_values, stage_support, transform_metadata, from_v2 = read_projection_z_features(
            path, h1, subject=base.subject, state=base.state,
        )
        from_v2_count += int(from_v2)
        extra[key] = {
            "projection_z_inputs": {
                feature: stage_values[feature] for feature in h1.RAW_INPUT_FEATURES
            },
            "3d_m": stage_values["3d_m"],
            "3d_d": stage_values["3d_d"],
            "3d_e": stage_values["3d_e"],
        }
        support_rows.extend(
            row for row in base.coverage if row["arm"] in {"raw_v2_inputs", "legacy_v2"}
        )
        support_rows.extend(stage_support)
        for feature, metadata in transform_metadata.items():
            for field, value in metadata.items():
                if field in transform_contracts[feature]:
                    transform_contracts[feature][field].add(str(value))

    expected_keys = {
        (subject, state)
        for subject in selected
        for state in h1.STATES
    }
    if set(records) != expected_keys:
        raise ValueError(
            f"H1 paired file set differs from selection; "
            f"missing={sorted(expected_keys - set(records))[:5]}, "
            f"extra={sorted(set(records) - expected_keys)[:5]}"
        )

    common_subjects, incomplete = complete_common_subjects(selected, records, extra, h1)
    if len(common_subjects) < h1.MIN_COHORT:
        raise ValueError(
            f"Only {len(common_subjects)} complete participants across all stages; "
            f"frozen minimum is {h1.MIN_COHORT}"
        )
    schedule = h1.make_split_schedule(common_subjects)
    result_rows: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    choice_rows: list[dict[str, Any]] = []
    aggregate_rows: list[dict[str, Any]] = []
    previous_scores: dict[str, float] | None = None

    for stage, _ in STAGES:
        matrix, labels, groups, row_keys = build_matrix(stage, common_subjects, records, extra, h1)
        fit = h1.nested_grouped_cv(matrix, labels, groups, schedule)
        scores = fit["participant_auc"]
        delta = math.nan
        ci_low = math.nan
        ci_high = math.nan
        if previous_scores is not None:
            diffs = [
                float(scores[subject]) - float(previous_scores[subject])
                for subject in common_subjects
            ]
            delta = float(np.mean(diffs))
            ci_low, ci_high = h1.paired_bootstrap_interval(
                diffs, n_draws=2000, seed=20261008,
            )
        result_rows.append({
            "stage": stage,
            "n_participants": len(common_subjects),
            "n_features": int(matrix.shape[1]),
            "paired_participant_auc": float(np.mean(list(scores.values()))),
            "balanced_accuracy": fit["balanced_accuracy"],
            "sensitivity": fit["sensitivity"],
            "specificity": fit["specificity"],
            "delta_auc_vs_previous_stage": delta,
            "conditional_participant_bootstrap_95_low": ci_low,
            "conditional_participant_bootstrap_95_high": ci_high,
        })
        for index, (subject, state, label) in enumerate(row_keys):
            prediction_rows.append({
                "stage": stage,
                "subject": subject,
                "state": state,
                "label": label,
                "mean_oof_probability": float(fit["mean_probability"][index]),
                "paired_participant_auc": float(scores[subject]),
            })
            values = feature_map_for_stage(stage, subject, state, records, extra)
            for feature, value in values.items():
                aggregate_rows.append({
                    "stage": stage,
                    "subject": subject,
                    "state": state,
                    "feature": feature,
                    "value": float(value),
                })
        for choice in fit["c_choices"]:
            choice_rows.append({"stage": stage, **choice})
        previous_scores = scores

    for feature, fields in transform_contracts.items():
        for field, values in fields.items():
            if len(values) > 1:
                raise ValueError(
                    f"Projection transform contract varies across H1 files for "
                    f"{feature}.{field}: {sorted(values)}"
                )
    transform_summary = {
        feature: {field: sorted(values) for field, values in fields.items()}
        for feature, fields in transform_contracts.items()
    }

    summary = {
        "schema": "mnps_bench_001_legacy_loss_001_summary.v1",
        "status": "exploratory_complete",
        "benchmark": "MNPS-BENCH-001",
        "diagnostic": "LEGACY-LOSS-001",
        "h1_freeze": str(args.freeze_manifest.resolve()),
        "h1_run_dir": str(run_dir.resolve()),
        "selected_participants": len(selected),
        "common_complete_participants": common_subjects,
        "n_common_complete_participants": len(common_subjects),
        "incomplete_participant_count": len(incomplete),
        "incomplete_participants_by_stage": {
            subject: list(reasons) for subject, reasons in incomplete.items()
        },
        "from_v2_without_fallback_recordings": from_v2_count,
        "total_recordings": len(records),
        "stages": result_rows,
        "projection_z_transform_contract": transform_summary,
        "cv_contract": {
            "outer_folds": h1.OUTER_FOLDS,
            "outer_repeats": h1.OUTER_REPEATS,
            "inner_folds": h1.INNER_FOLDS,
            "C_grid": list(h1.C_GRID),
            "split_schedule_reused_across_stages": True,
            "scoring": "paired_participant_auc",
            "bootstrap_draws_for_adjacent_stage_differences": 2000,
            "bootstrap_seed": 20261008,
        },
        "support_contract": {
            "minimum_unique_supported_seconds": h1.MIN_SUPPORTED_SEC,
            "window_aggregation": "median",
            "3d_validity": "qc/windows/mnps_3d_valid",
            "9d_validity": "qc/windows/coords_9d_valid",
        },
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "h5py": h5py.__version__,
            "scikit_learn": sklearn.__version__,
            "scipy": scipy.__version__,
        },
    }

    write_csv(args.out_dir / "stage_results.csv", result_rows)
    write_csv(args.out_dir / "stage_predictions.csv", prediction_rows)
    write_csv(args.out_dir / "stage_model_choices.csv", choice_rows)
    write_csv(args.out_dir / "stage_feature_values.csv", aggregate_rows)
    write_csv(args.out_dir / "stage_support.csv", support_rows)
    (args.out_dir / "analysis_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8",
    )

    for path, expected in expected_inputs.items():
        if sha256(Path(path)) != expected:
            raise ValueError(f"H1 source HDF5 changed during analysis: {path}")
    output_hashes = {
        path.name: sha256(path)
        for path in sorted(args.out_dir.iterdir())
        if path.is_file()
    }
    run_manifest = {
        "schema": "mnps_bench_001_legacy_loss_001_run_manifest.v1",
        "analysis_script": str(Path(__file__).resolve()),
        "analysis_script_sha256": sha256(Path(__file__).resolve()),
        "h1_analysis_script": str(H1_SCRIPT.resolve()),
        "h1_analysis_script_sha256": sha256(H1_SCRIPT),
        "protocol": str(args.protocol.resolve()),
        "protocol_sha256": sha256(args.protocol),
        "h1_freeze_manifest": str(args.freeze_manifest.resolve()),
        "h1_freeze_sha256": sha256(args.freeze_manifest),
        "selection_manifest": str(args.selection_manifest.resolve()),
        "selection_manifest_sha256": sha256(args.selection_manifest),
        "execution_manifest": str(args.execution_manifest.resolve()),
        "execution_manifest_sha256": sha256(args.execution_manifest),
        "input_h5_sha256": [
            {"path": path, "sha256": digest}
            for path, digest in sorted(expected_inputs.items())
        ],
        "output_file_sha256": output_hashes,
    }
    (args.out_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nmd-root", type=Path, default=NMD_DEFAULT)
    parser.add_argument("--freeze-manifest", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--selection-manifest", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--execution-manifest", type=Path, default=DEFAULT_EXECUTION)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = run(args)
    print(json.dumps({
        "status": summary["status"],
        "n_common_complete_participants": summary["n_common_complete_participants"],
        "stages": summary["stages"],
        "out_dir": str(args.out_dir.resolve()),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
