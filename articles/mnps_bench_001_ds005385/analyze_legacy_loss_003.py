"""Freeze and run the LEGACY-LOSS-003 transform ablation on saved H1 HDF5."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import scipy
import sklearn

ARTICLE_DIR = Path(__file__).resolve().parent
NMD_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
BENCH_DIR = NMD_ROOT / "project" / "new_mnps_v.3.1" / "bench_001"
H1_FREEZE = BENCH_DIR / "h1_analysis_freeze_v3.json"
SELECTION = BENCH_DIR / "selection_manifest_outcome_blind.json"
EXECUTION = BENCH_DIR / "h1_execution_manifest.json"
PROTOCOL = ARTICLE_DIR / "legacy_loss_003_protocol_v1_20261008.md"
OUT_DIR = Path(r"I:\AAA_PYTHON_REPOS_BACKUP\homepages\_mnps_legacy_loss_003")
FREEZE_PATH = OUT_DIR / "legacy_loss_003_freeze_v1_20261008.json"
H1_SCRIPT = ARTICLE_DIR / "analyze_h1.py"
PRIOR_RUN_DIR = BENCH_DIR / "outputs" / "legacy_loss_001_20261007_v1"
ARMS = ("raw", "L", "R", "LR", "RC", "LRC")
CLIP_THRESHOLD = 6.0
BOOTSTRAP_DRAWS = 2000
BOOTSTRAP_SEED = 20261009
RECONSTRUCTION_ATOL = 1e-6


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def load_h1_and_projection():
    sys.path.insert(0, str(ARTICLE_DIR))
    sys.path.insert(0, str(NMD_ROOT / "mndm" / "src"))
    h1 = importlib.import_module("analyze_h1")
    projection = importlib.import_module("mndm.projection")
    return h1, projection


def validate_h1_freeze(h1: Any, freeze_path: Path) -> dict[str, Any]:
    frozen = read_json(freeze_path)
    if frozen.get("schema") != "mnps_bench_001_h1_analysis_freeze.v1":
        raise ValueError("Unexpected H1 freeze schema")
    if sha256_file(H1_SCRIPT) != frozen["analysis_script"]["sha256"]:
        raise ValueError("H1 helper code differs from frozen H1 analysis")
    nmd_projection = frozen.get("nmd_pipeline_code", {}).get("mndm/src/mndm/projection.py")
    projection_path = NMD_ROOT / "mndm" / "src" / "mndm" / "projection.py"
    if not nmd_projection or sha256_file(projection_path) != nmd_projection["sha256"]:
        raise ValueError("NMD projection helper differs from frozen H1 dependency")
    h1.validate_analysis_freeze(
        freeze_path,
        Path(frozen["run_dir"]),
        Path(frozen["selection_manifest"]["path"]),
        Path(frozen["execution_manifest"]["path"]),
    )
    return frozen


def make_freeze(out_dir: Path) -> Path:
    h1, _projection = load_h1_and_projection()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty; preserving it: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    h1_frozen = validate_h1_freeze(h1, H1_FREEZE)
    run_dir = Path(h1_frozen["run_dir"])
    expected = {
        str(Path(row["path"]).resolve()): str(row["sha256"])
        for row in h1_frozen["input_h5_sha256"]
    }
    files = sorted(run_dir.rglob("*.h5"))
    if {str(path.resolve()) for path in files} != set(expected):
        raise ValueError("H1 file set differs from its frozen input list")
    input_rows: list[dict[str, str]] = []
    for path in files:
        key = str(path.resolve())
        observed = sha256_file(path)
        if observed.lower() != expected[key].lower():
            raise ValueError(f"Frozen H1 input hash mismatch: {path}")
        input_rows.append({"path": str(path.resolve()), "sha256": observed})

    deps = {
        "analysis_script": {"path": str(Path(__file__).resolve()), "sha256": sha256_file(Path(__file__).resolve())},
        "protocol": {"path": str(PROTOCOL.resolve()), "sha256": sha256_file(PROTOCOL)},
        "h1_analysis_script": {"path": str(H1_SCRIPT.resolve()), "sha256": sha256_file(H1_SCRIPT)},
        "h1_freeze": {"path": str(H1_FREEZE.resolve()), "sha256": sha256_file(H1_FREEZE)},
        "selection_manifest": {"path": str(SELECTION.resolve()), "sha256": sha256_file(SELECTION)},
        "execution_manifest": {"path": str(EXECUTION.resolve()), "sha256": sha256_file(EXECUTION)},
        "nmd_projection": {
            "path": str((NMD_ROOT / "mndm" / "src" / "mndm" / "projection.py").resolve()),
            "sha256": sha256_file(NMD_ROOT / "mndm" / "src" / "mndm" / "projection.py"),
        },
    }
    freeze = {
        "schema": "mnps_legacy_loss_003_freeze.v1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "frozen_before_transform_arm_auc_analysis",
        "protocol_sha256": deps["protocol"]["sha256"],
        "dependencies": deps,
        "h1_source_freeze_sha256": deps["h1_freeze"]["sha256"],
        "input_h5_sha256": input_rows,
        "arm_order": list(ARMS),
        "clip_threshold": CLIP_THRESHOLD,
        "reconstruction_absolute_tolerance": RECONSTRUCTION_ATOL,
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "bootstrap_seed_base": BOOTSTRAP_SEED,
        "prior_legacy_loss_001_run_manifest": {
            "path": str((PRIOR_RUN_DIR / "run_manifest.json").resolve()),
            "sha256": sha256_file(PRIOR_RUN_DIR / "run_manifest.json"),
        },
        "software": {
            "python_executable": sys.executable,
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "h5py": h5py.__version__,
        },
    }
    FREEZE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FREEZE_PATH.write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return FREEZE_PATH


def verify_freeze(h1: Any, freeze_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    freeze = read_json(freeze_path)
    if freeze.get("schema") != "mnps_legacy_loss_003_freeze.v1":
        raise ValueError("Unexpected LEGACY-LOSS-003 freeze schema")
    for label, dep in freeze["dependencies"].items():
        path = Path(dep["path"])
        if sha256_file(path).lower() != dep["sha256"].lower():
            raise ValueError(f"Frozen dependency hash mismatch: {label}")
    current_software = {
        "python_executable": sys.executable,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "h5py": h5py.__version__,
    }
    for package, observed in current_software.items():
        if freeze["software"].get(package) != observed:
            raise ValueError(
                f"LEGACY-LOSS-003 runtime mismatch for {package}: "
                f"frozen={freeze['software'].get(package)!r}, current={observed!r}"
            )
    h1_frozen = validate_h1_freeze(h1, H1_FREEZE)
    if sha256_file(H1_FREEZE) != freeze["h1_source_freeze_sha256"]:
        raise ValueError("H1 source freeze changed since LEGACY-LOSS-003 freeze")
    expected = {str(Path(row["path"]).resolve()): row["sha256"] for row in freeze["input_h5_sha256"]}
    current = {str(Path(row["path"]).resolve()): row["sha256"] for row in h1_frozen["input_h5_sha256"]}
    if expected != current:
        raise ValueError("LEGACY-LOSS-003 inputs no longer match frozen H1 inputs")
    return freeze, h1_frozen


def normalize_pipeline(metadata: dict[str, Any]) -> list[str]:
    applied = str(metadata.get("transformation_applied") or "none")
    if applied == "none":
        return []
    steps = []
    for raw_step in applied.split("->"):
        step = raw_step.strip().lower()
        if step.startswith("clip_"):
            steps.append("clip")
        elif step in {"log10", "robust_z", "robust"}:
            steps.append("robust_z" if step == "robust" else step)
        else:
            raise ValueError(f"Unrecognized frozen feature transform step: {raw_step!r}")
    return steps


def assert_close_surface(observed: np.ndarray, expected: np.ndarray, *, label: str) -> float:
    observed = np.asarray(observed, dtype=np.float64)
    expected = np.asarray(expected, dtype=np.float64)
    if observed.shape != expected.shape:
        raise ValueError(f"{label} shape mismatch: {observed.shape} != {expected.shape}")
    finite_match = np.isfinite(observed) == np.isfinite(expected)
    if not finite_match.all():
        raise ValueError(f"{label} finite/missing support mismatch")
    finite = np.isfinite(observed) & np.isfinite(expected)
    max_abs = float(np.max(np.abs(observed[finite] - expected[finite]))) if finite.any() else 0.0
    if max_abs > RECONSTRUCTION_ATOL:
        raise ValueError(f"{label} reconstruction mismatch: max abs error {max_abs}")
    return max_abs


def load_recording(path: Path, expected_hash: str, h1: Any, projection: Any) -> tuple[str, str, dict[str, dict[str, float]], list[dict[str, Any]], list[dict[str, Any]]]:
    if sha256_file(path).lower() != expected_hash.lower():
        raise ValueError(f"Frozen H1 source hash mismatch: {path}")
    with h5py.File(path, "r") as h5file:
        raw_file = h1._row_source_file(h5file)
        match = h1.FILE_PATTERN.search(Path(raw_file).name)
        if not match:
            raise ValueError(f"Unexpected H1 source recording name: {raw_file}")
        subject = match.group("subject")
        state = "EyesClosed" if match.group("state").lower() == "eyesclosed" else "EyesOpen"
        starts = np.asarray(h5file["window_start"], dtype=np.float64).reshape(-1)
        ends = np.asarray(h5file["window_end"], dtype=np.float64).reshape(-1)
        if starts.shape != ends.shape:
            raise ValueError(f"Window-grid shape mismatch in {path}")
        intervals = list(zip(starts.tolist(), ends.tolist(), strict=True))

        surfaces: dict[str, tuple[list[str], np.ndarray]] = {}
        for surface in ("features_raw", "features_robust_z", "features_projection_z"):
            names = h1._decode_names(h5file[f"{surface}/names"])
            values = np.asarray(h5file[f"{surface}/values"], dtype=np.float32)
            if values.shape != (len(intervals), len(names)):
                raise ValueError(f"{surface} is misaligned with the saved legacy windows: {path}")
            surfaces[surface] = (names, values)
        raw_names, raw_matrix = surfaces["features_raw"]
        robust_names, robust_matrix = surfaces["features_robust_z"]
        projection_names, projection_matrix = surfaces["features_projection_z"]
        positions = {
            surface: {name: index for index, name in enumerate(names)}
            for surface, (names, _values) in surfaces.items()
        }
        manifest = json.loads(h1._decode(h5file["manifest_json"][()]))
        baselines = manifest.get("feature_baselines", {})
        arm_windows: dict[str, dict[str, np.ndarray]] = {arm: {} for arm in ARMS}
        transform_qc: list[dict[str, Any]] = []

        for feature in h1.RAW_INPUT_FEATURES:
            if any(feature not in positions[surface] for surface in surfaces):
                raise ValueError(f"Required feature {feature!r} is missing from a saved surface in {path}")
            raw = np.asarray(raw_matrix[:, positions["features_raw"][feature]], dtype=np.float32)
            robust = np.asarray(robust_matrix[:, positions["features_robust_z"][feature]], dtype=np.float32)
            stored_projection = np.asarray(projection_matrix[:, positions["features_projection_z"][feature]], dtype=np.float32)
            metadata = baselines.get(feature)
            if not isinstance(metadata, dict):
                raise ValueError(f"Missing per-feature transform metadata for {feature!r}: {path}")
            pipeline = normalize_pipeline(metadata)
            if ("robust_z" not in pipeline) or (pipeline.count("robust_z") != 1):
                raise ValueError(f"Expected one local robust-z operation for {feature}: {pipeline}")
            has_log = "log10" in pipeline
            if pipeline.count("log10") > 1 or pipeline.count("clip") > 1:
                raise ValueError(f"Unexpected repeated transform step for {feature}: {pipeline}")
            if "clip" in pipeline and pipeline.index("clip") < pipeline.index("robust_z"):
                raise ValueError(f"Clip precedes robust-z for {feature}: {pipeline}")

            reconstructed_full = projection._apply_column_pipeline(raw, pipeline, CLIP_THRESHOLD)
            full_error = assert_close_surface(
                stored_projection, reconstructed_full, label=f"stored LRC {feature} {path.name}",
            )
            no_clip_pipeline = [step for step in pipeline if step != "clip"]
            reconstructed_no_clip = projection._apply_column_pipeline(raw, no_clip_pipeline, CLIP_THRESHOLD)
            log_only = (
                projection._apply_column_pipeline(raw, ["log10"], CLIP_THRESHOLD)
                if has_log else raw.copy()
            )
            r_from_helper = projection._apply_column_pipeline(raw, ["robust_z"], CLIP_THRESHOLD)
            r_error = assert_close_surface(robust, r_from_helper, label=f"stored R {feature} {path.name}")
            if not has_log:
                assert_close_surface(log_only, raw, label=f"non-log L/raw {feature} {path.name}")
                assert_close_surface(reconstructed_no_clip, robust, label=f"non-log LR/R {feature} {path.name}")
                assert_close_surface(stored_projection, np.clip(robust, -CLIP_THRESHOLD, CLIP_THRESHOLD), label=f"non-log LRC/RC {feature} {path.name}")

            arm_windows["raw"][feature] = raw
            arm_windows["L"][feature] = log_only
            arm_windows["R"][feature] = robust
            arm_windows["LR"][feature] = reconstructed_no_clip
            arm_windows["RC"][feature] = np.where(
                np.isfinite(robust), np.clip(robust, -CLIP_THRESHOLD, CLIP_THRESHOLD), robust,
            ).astype(np.float32)
            arm_windows["LRC"][feature] = stored_projection

            finite_raw = np.isfinite(raw)
            finite_log_only = np.isfinite(log_only)
            finite_r = np.isfinite(robust)
            finite_lr = np.isfinite(reconstructed_no_clip)
            log_invalid = int(np.count_nonzero(finite_raw & (raw <= 0))) if has_log else 0
            r_clip_count = int(np.count_nonzero(finite_r & (np.abs(robust) > CLIP_THRESHOLD)))
            lr_clip_count = int(np.count_nonzero(finite_lr & (np.abs(reconstructed_no_clip) > CLIP_THRESHOLD)))
            transform_qc.append({
                "subject": subject,
                "state": state,
                "feature": feature,
                "pipeline": " -> ".join(pipeline),
                "feature_specific_log": has_log,
                "raw_finite_window_count": int(finite_raw.sum()),
                "raw_nonpositive_window_count": log_invalid,
                "log_only_finite_window_count": int(finite_log_only.sum()),
                "robust_z_finite_window_count": int(finite_r.sum()),
                "robust_z_abs_gt_6_window_count": r_clip_count,
                "robust_z_clip_fraction": r_clip_count / int(finite_r.sum()) if finite_r.any() else math.nan,
                "log_robust_z_finite_window_count": int(finite_lr.sum()),
                "log_robust_z_abs_gt_6_window_count": lr_clip_count,
                "log_robust_z_clip_fraction": lr_clip_count / int(finite_lr.sum()) if finite_lr.any() else math.nan,
                "stored_robust_z_reconstruction_max_abs_error": r_error,
                "stored_projection_z_reconstruction_max_abs_error": full_error,
                "support_grid_window_count": len(intervals),
            })

        # Recompute support-preserving recording medians for each transform arm.
        aggregated: dict[str, dict[str, float]] = {arm: {} for arm in ARMS}
        support_rows: list[dict[str, Any]] = []
        for arm in ARMS:
            for feature in h1.RAW_INPUT_FEATURES:
                values = arm_windows[arm][feature]
                aggregate, support = h1._supported_aggregate(
                    feature, values.tolist(), intervals,
                    subject=subject, state=state, arm=arm,
                )
                aggregated[arm][feature] = float(aggregate[0])
                support_rows.append({
                    **support,
                    "arm": arm,
                    "source_h5": str(path.resolve()),
                    "feature_specific_log": "log10" in normalize_pipeline(baselines[feature]),
                })
    return subject, state, aggregated, support_rows, transform_qc


def run_analysis(freeze_path: Path) -> dict[str, Any]:
    h1, projection = load_h1_and_projection()
    freeze, h1_frozen = verify_freeze(h1, freeze_path)
    out_dir = freeze_path.parent
    generated_names = {
        "arm_results.csv", "paired_contrasts.csv", "stage_predictions.csv",
        "stage_model_choices.csv", "stage_feature_values.csv", "stage_support.csv",
        "transform_reconstruction_qc.csv", "prior_stage_crosscheck.csv", "clipping_summary.csv",
        "results.md", "analysis_summary.json", "run_manifest.json",
    }
    existing_generated = [name for name in generated_names if (out_dir / name).exists()]
    if existing_generated:
        raise FileExistsError(f"Preserving existing partial/final output files: {sorted(existing_generated)}")

    expected_hashes = {str(Path(row["path"]).resolve()): row["sha256"] for row in freeze["input_h5_sha256"]}
    files = sorted(Path(h1_frozen["run_dir"]).rglob("*.h5"))
    if {str(path.resolve()) for path in files} != set(expected_hashes):
        raise ValueError("Current H1 HDF5 file set differs from the frozen set")
    selected = h1.load_selected_subjects(SELECTION)
    records: dict[tuple[str, str], dict[str, dict[str, float]]] = {}
    support_rows: list[dict[str, Any]] = []
    reconstruction_rows: list[dict[str, Any]] = []
    for index, path in enumerate(files, start=1):
        subject, state, aggregated, support, transform_qc = load_recording(
            path, expected_hashes[str(path.resolve())], h1, projection,
        )
        key = (subject, state)
        if key in records:
            raise ValueError(f"Duplicate subject-state recording: {key}")
        records[key] = aggregated
        support_rows.extend(support)
        reconstruction_rows.extend(transform_qc)
        if index % 40 == 0 or index == len(files):
            print(f"Loaded {index}/{len(files)} frozen H1 HDF5 files", flush=True)

    expected_keys = {(subject, state) for subject in selected for state in h1.STATES}
    if set(records) != expected_keys:
        raise ValueError(f"H1 paired file set mismatch: missing={sorted(expected_keys-set(records))[:5]}")

    # Check the raw and full historical transformed summaries against the completed LEGACY-LOSS-001 run.
    previous_values_path = PRIOR_RUN_DIR / "stage_feature_values.csv"
    if sha256_file(PRIOR_RUN_DIR / "run_manifest.json") != freeze["prior_legacy_loss_001_run_manifest"]["sha256"]:
        raise ValueError("Prior LEGACY-LOSS-001 run manifest changed after the protocol freeze")
    prior_values: dict[tuple[str, str, str, str], float] = {}
    with previous_values_path.open("r", newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["stage"] in {"raw_v2_inputs", "projection_z_inputs"}:
                prior_values[(row["stage"], row["subject"], row["state"], row["feature"])] = float(row["value"])
    crosscheck_rows: list[dict[str, Any]] = []
    for subject, state in sorted(expected_keys):
        for feature in h1.RAW_INPUT_FEATURES:
            comparisons = (
                ("raw_v2_inputs", "raw"),
                ("projection_z_inputs", "LRC"),
            )
            for prior_stage, arm in comparisons:
                old_value = prior_values[(prior_stage, subject, state, feature)]
                new_value = records[(subject, state)][arm][feature]
                if not (np.isfinite(old_value) and np.isfinite(new_value)) or abs(old_value - new_value) > 1e-12:
                    raise ValueError(f"Legacy stage cross-check failed: {prior_stage} {subject} {state} {feature}")
                crosscheck_rows.append({
                    "prior_stage": prior_stage,
                    "arm": arm,
                    "subject": subject,
                    "state": state,
                    "feature": feature,
                    "prior_value": old_value,
                    "recomputed_value": new_value,
                    "absolute_difference": abs(old_value - new_value),
                })

    complete: list[str] = []
    incomplete: dict[str, list[str]] = {}
    for subject in selected:
        failed = []
        for state in h1.STATES:
            for arm in ARMS:
                for feature in h1.RAW_INPUT_FEATURES:
                    value = records[(subject, state)][arm][feature]
                    if not np.isfinite(value):
                        failed.append(f"{state}:{arm}:{feature}")
        if failed:
            incomplete[subject] = failed
        else:
            complete.append(subject)
    if len(complete) < h1.MIN_COHORT:
        raise ValueError(f"Only {len(complete)} complete participants remain; minimum is {h1.MIN_COHORT}")

    schedule = h1.make_split_schedule(complete)
    score_by_arm: dict[str, dict[str, float]] = {}
    arm_rows: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    model_choice_rows: list[dict[str, Any]] = []
    for arm in ARMS:
        matrix: list[list[float]] = []
        labels: list[int] = []
        groups: list[str] = []
        row_keys: list[tuple[str, str, int]] = []
        for subject in complete:
            for state, label in (("EyesClosed", 0), ("EyesOpen", 1)):
                matrix.append([records[(subject, state)][arm][feature] for feature in h1.RAW_INPUT_FEATURES])
                labels.append(label)
                groups.append(subject)
                row_keys.append((subject, state, label))
        fit = h1.nested_grouped_cv(
            np.asarray(matrix, dtype=np.float64),
            np.asarray(labels, dtype=np.int8),
            np.asarray(groups),
            schedule,
        )
        score_by_arm[arm] = {subject: float(score) for subject, score in fit["participant_auc"].items()}
        arm_rows.append({
            "arm": arm,
            "n_participants": len(complete),
            "n_features": len(h1.RAW_INPUT_FEATURES),
            "mean_paired_participant_auc": float(np.mean(list(score_by_arm[arm].values()))),
            "balanced_accuracy": fit["balanced_accuracy"],
            "sensitivity": fit["sensitivity"],
            "specificity": fit["specificity"],
        })
        for row_index, (subject, state, label) in enumerate(row_keys):
            prediction_rows.append({
                "arm": arm,
                "subject": subject,
                "state": state,
                "label": label,
                "mean_oof_probability": float(fit["mean_probability"][row_index]),
                "paired_participant_auc": score_by_arm[arm][subject],
            })
        for choice in fit["c_choices"]:
            model_choice_rows.append({"arm": arm, **choice})
        print(f"Fitted arm {arm}: mean participant AUC={arm_rows[-1]['mean_paired_participant_auc']:.4f}", flush=True)

    contrast_specs = (
        ("L_minus_raw_log_only", "L", "raw"),
        ("R_minus_raw_robust_z_only", "R", "raw"),
        ("LR_minus_L_robust_z_after_log", "LR", "L"),
        ("LR_minus_R_log_after_robust_z", "LR", "R"),
        ("RC_minus_R_clip_without_log", "RC", "R"),
        ("LRC_minus_LR_clip_with_log", "LRC", "LR"),
        ("LRC_minus_RC_log_with_clip", "LRC", "RC"),
        ("LRC_minus_raw_full_historical", "LRC", "raw"),
    )
    contrasts: list[dict[str, Any]] = []
    contrast_vectors: dict[str, dict[str, float]] = {}
    for index, (name, left, right) in enumerate(contrast_specs):
        values = {subject: score_by_arm[left][subject] - score_by_arm[right][subject] for subject in complete}
        low, high = h1.paired_bootstrap_interval(
            [values[subject] for subject in complete], n_draws=BOOTSTRAP_DRAWS,
            seed=BOOTSTRAP_SEED + index,
        )
        contrast_vectors[name] = values
        contrasts.append({
            "contrast": name,
            "left_arm": left,
            "right_arm": right,
            "mean_paired_auc_difference": float(np.mean(list(values.values()))),
            "participant_bootstrap_95_low": low,
            "participant_bootstrap_95_high": high,
            "n_participants": len(complete),
            "bootstrap_draws": BOOTSTRAP_DRAWS,
            "bootstrap_seed": BOOTSTRAP_SEED + index,
        })
    robust_z_interaction = {
        subject: contrast_vectors["LR_minus_L_robust_z_after_log"][subject]
        - contrast_vectors["R_minus_raw_robust_z_only"][subject]
        for subject in complete
    }
    robust_z_interaction_low, robust_z_interaction_high = h1.paired_bootstrap_interval(
        [robust_z_interaction[subject] for subject in complete], n_draws=BOOTSTRAP_DRAWS,
        seed=BOOTSTRAP_SEED + len(contrast_specs),
    )
    contrasts.append({
        "contrast": "robust_z_effect_interaction_with_log",
        "left_arm": "(LR-L)",
        "right_arm": "(R-raw)",
        "mean_paired_auc_difference": float(np.mean(list(robust_z_interaction.values()))),
        "participant_bootstrap_95_low": robust_z_interaction_low,
        "participant_bootstrap_95_high": robust_z_interaction_high,
        "n_participants": len(complete),
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "bootstrap_seed": BOOTSTRAP_SEED + len(contrast_specs),
    })

    clip_interaction = {
        subject: contrast_vectors["LRC_minus_LR_clip_with_log"][subject]
        - contrast_vectors["RC_minus_R_clip_without_log"][subject]
        for subject in complete
    }
    clip_interaction_low, clip_interaction_high = h1.paired_bootstrap_interval(
        [clip_interaction[subject] for subject in complete], n_draws=BOOTSTRAP_DRAWS,
        seed=BOOTSTRAP_SEED + len(contrast_specs) + 1,
    )
    contrasts.append({
        "contrast": "clip_effect_interaction_log_by_clip",
        "left_arm": "(LRC-LR)",
        "right_arm": "(RC-R)",
        "mean_paired_auc_difference": float(np.mean(list(clip_interaction.values()))),
        "participant_bootstrap_95_low": clip_interaction_low,
        "participant_bootstrap_95_high": clip_interaction_high,
        "n_participants": len(complete),
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "bootstrap_seed": BOOTSTRAP_SEED + len(contrast_specs) + 1,
    })

    feature_value_rows: list[dict[str, Any]] = []
    for subject in selected:
        for state in h1.STATES:
            for arm in ARMS:
                for feature in h1.RAW_INPUT_FEATURES:
                    feature_value_rows.append({
                        "arm": arm,
                        "subject": subject,
                        "state": state,
                        "feature": feature,
                        "value": records[(subject, state)][arm][feature],
                    })

    clipping_summary = []
    for feature in h1.RAW_INPUT_FEATURES:
        feature_rows = [row for row in reconstruction_rows if row["feature"] == feature]
        raw_windows = sum(int(row["raw_finite_window_count"]) for row in feature_rows)
        log_invalid = sum(int(row["raw_nonpositive_window_count"]) for row in feature_rows)
        r_finite = sum(int(row["robust_z_finite_window_count"]) for row in feature_rows)
        r_clipped = sum(int(row["robust_z_abs_gt_6_window_count"]) for row in feature_rows)
        lr_finite = sum(int(row["log_robust_z_finite_window_count"]) for row in feature_rows)
        lr_clipped = sum(int(row["log_robust_z_abs_gt_6_window_count"]) for row in feature_rows)
        clipping_summary.append({
            "feature": feature,
            "feature_specific_log": bool(feature_rows[0]["feature_specific_log"]),
            "recordings": len(feature_rows),
            "raw_finite_windows": raw_windows,
            "raw_nonpositive_windows_for_log": log_invalid,
            "robust_z_values_clipped_in_RC": r_clipped,
            "robust_z_finite_values": r_finite,
            "RC_clip_fraction": r_clipped / r_finite if r_finite else math.nan,
            "log_robust_z_values_clipped_in_LRC": lr_clipped,
            "log_robust_z_finite_values": lr_finite,
            "LRC_clip_fraction": lr_clipped / lr_finite if lr_finite else math.nan,
        })

    arm_table = "\n".join(
        f"| {row['arm']} | {row['n_participants']} | {row['mean_paired_participant_auc']:.4f} | {row['balanced_accuracy']:.4f} |"
        for row in arm_rows
    )
    contrast_table = "\n".join(
        f"| {row['contrast']} | {row['mean_paired_auc_difference']:.4f} | [{row['participant_bootstrap_95_low']:.4f}, {row['participant_bootstrap_95_high']:.4f}] |"
        for row in contrasts
    )
    clip_table = "\n".join(
        f"| {row['feature']} | {'yes' if row['feature_specific_log'] else 'no'} | {row['raw_nonpositive_windows_for_log']} | {row['RC_clip_fraction']:.4%} | {row['LRC_clip_fraction']:.4%} |"
        for row in clipping_summary
    )
    results_md = f"""# LEGACY-LOSS-003 results

Generated {dt.datetime.now(dt.timezone.utc).isoformat()} from frozen protocol
`{PROTOCOL.name}` and source freeze `legacy_loss_003_freeze_v1_20261008.json`.

## Scope

This is a post-hoc transformation mechanism analysis of the 100 selected
ds005385 H1 participants using previously saved HDF5 windows only. No EDF was
read and no EEG features were recomputed. All six arms use the same ten
historical raw-v2 feature identities, 60-second support aggregation, complete
paired participant set, nested participant-grouped CV schedule, and pinned
runtime.

## Arm results

| Arm | Complete participants | Mean paired participant AUC | Balanced accuracy |
|---|---:|---:|---:|
{arm_table}

## Paired transformation contrasts

Positive values mean the left-hand arm has higher participant AUC. Intervals
are 2,000-draw participant bootstraps conditional on the repeated-CV
predictions; they do not include model-refitting variability.

| Contrast | Mean paired ΔAUC | Participant bootstrap 95% interval |
|---|---:|---:|
{contrast_table}

`robust_z_effect_interaction_with_log` is `(LR-L) - (R-raw)`: the change in
the robust-z effect when the feature-specific log transform is present.
`clip_effect_interaction_log_by_clip` is `(LRC-LR) - (RC-R)`: the change in
the clipping effect when the feature-specific log transform is present.

## Transform support and clipping

| Feature | Log configured | Nonpositive raw windows | RC values clipped / finite | LRC values clipped / finite |
|---|---:|---:|---:|---:|
{clip_table}

The LRC values were reconstructed with the frozen NMD projection helper and
matched saved `features_projection_z` within absolute tolerance
`{RECONSTRUCTION_ATOL:g}` for every frozen recording and feature. The raw and
LRC recording medians also matched the corresponding LEGACY-LOSS-001 saved
stages exactly. Full per-recording transform checks, clipping counts, feature
support, participant predictions, and model choices are retained in the CSV
artifacts; their hashes are in `run_manifest.json`.

## Interpretation limits

These contrasts describe how each operation relates to discrimination under
this fixed classifier, support rule, and exposed dataset. They do not prove a
biological mechanism or establish a general reason for the historical H1
result. Local robust-z uses each recording's windows, matching the historical
contract, so these arms are not a deployable transform learned without access
to the test recording. The ablated arms remain diagnostic only and do not
replace historical MNPS 2.0 in H1.

Complete participant count: {len(complete)}/100. Incomplete participants are
listed in `analysis_summary.json`. No new EEG processing or tests were run.
"""

    write_csv(out_dir / "arm_results.csv", arm_rows)
    write_csv(out_dir / "paired_contrasts.csv", contrasts)
    write_csv(out_dir / "stage_predictions.csv", prediction_rows)
    write_csv(out_dir / "stage_model_choices.csv", model_choice_rows)
    write_csv(out_dir / "stage_feature_values.csv", feature_value_rows)
    write_csv(out_dir / "stage_support.csv", support_rows)
    write_csv(out_dir / "transform_reconstruction_qc.csv", reconstruction_rows)
    write_csv(out_dir / "prior_stage_crosscheck.csv", crosscheck_rows)
    write_csv(out_dir / "clipping_summary.csv", clipping_summary)
    (out_dir / "results.md").write_text(results_md, encoding="utf-8")

    summary = {
        "schema": "mnps_legacy_loss_003_summary.v1",
        "status": "exploratory_complete",
        "protocol": str(PROTOCOL.resolve()),
        "protocol_sha256": sha256_file(PROTOCOL),
        "freeze_path": str(freeze_path.resolve()),
        "freeze_sha256": sha256_file(freeze_path),
        "h1_freeze_path": str(H1_FREEZE.resolve()),
        "h1_freeze_sha256": sha256_file(H1_FREEZE),
        "selected_participants": len(selected),
        "complete_common_participants": complete,
        "incomplete_participants_by_reason": incomplete,
        "feature_order": list(h1.RAW_INPUT_FEATURES),
        "feature_specific_log_set": sorted({
            row["feature"] for row in reconstruction_rows if row["feature_specific_log"]
        }),
        "arms": arm_rows,
        "paired_contrasts": contrasts,
        "prior_stage_crosscheck_count": len(crosscheck_rows),
        "max_prior_stage_crosscheck_abs_error": max(
            (row["absolute_difference"] for row in crosscheck_rows), default=0.0,
        ),
        "transform_reconstruction_max_abs_error": max(
            (max(row["stored_robust_z_reconstruction_max_abs_error"], row["stored_projection_z_reconstruction_max_abs_error"])
             for row in reconstruction_rows), default=0.0,
        ),
        "clipping_summary": clipping_summary,
        "cv_contract": {
            "outer_folds": h1.OUTER_FOLDS,
            "outer_repeats": h1.OUTER_REPEATS,
            "inner_folds": h1.INNER_FOLDS,
            "C_grid": list(h1.C_GRID),
            "same_split_schedule_reused_across_arms": True,
            "model": "training-fold standardized L2 logistic regression via frozen H1 helper",
            "paired_participant_auc": True,
            "participant_bootstrap_draws": BOOTSTRAP_DRAWS,
            "participant_bootstrap_seed_base": BOOTSTRAP_SEED,
        },
        "support_contract": {
            "aggregation": "median of finite transformed windows",
            "minimum_unique_supported_seconds": h1.MIN_SUPPORTED_SEC,
            "common_participant_set_across_all_arms": True,
        },
        "software": {
            "python_executable": sys.executable,
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "h5py": h5py.__version__,
        },
    }
    (out_dir / "analysis_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for path_text, expected in expected_hashes.items():
        if sha256_file(Path(path_text)).lower() != expected.lower():
            raise ValueError(f"H1 source HDF5 changed during the analysis: {path_text}")
    output_hashes = {
        path.name: sha256_file(path)
        for path in sorted(out_dir.iterdir())
        if path.is_file() and path.name != "run_manifest.json"
    }
    run_manifest = {
        "schema": "mnps_legacy_loss_003_run_manifest.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "analysis_script": str(Path(__file__).resolve()),
        "analysis_script_sha256": sha256_file(Path(__file__).resolve()),
        "protocol": str(PROTOCOL.resolve()),
        "protocol_sha256": sha256_file(PROTOCOL),
        "analysis_freeze": str(freeze_path.resolve()),
        "analysis_freeze_sha256": sha256_file(freeze_path),
        "h1_freeze": str(H1_FREEZE.resolve()),
        "h1_freeze_sha256": sha256_file(H1_FREEZE),
        "input_h5_sha256": freeze["input_h5_sha256"],
        "outputs_sha256": output_hashes,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "run"))
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--freeze", type=Path, default=None)
    args = parser.parse_args()
    if args.command == "freeze":
        path = make_freeze(args.out_dir)
        print(json.dumps({"status": "frozen", "path": str(path), "sha256": sha256_file(path)}, indent=2))
        return 0
    freeze_path = args.freeze or (args.out_dir / FREEZE_PATH.name)
    summary = run_analysis(freeze_path)
    print(json.dumps({
        "status": summary["status"],
        "n_complete_participants": len(summary["complete_common_participants"]),
        "arms": summary["arms"],
        "paired_contrasts": summary["paired_contrasts"],
        "out_dir": str(args.out_dir.resolve()),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
