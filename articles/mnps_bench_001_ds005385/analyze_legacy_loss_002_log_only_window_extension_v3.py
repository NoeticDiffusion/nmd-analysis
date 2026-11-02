"""Post-run, log-only extension to LEGACY-LOSS-002 using saved H1 summaries."""

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

import numpy as np
import h5py
import sklearn

ARTICLE_DIR = Path(__file__).resolve().parent
NMD_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
BENCH_DIR = NMD_ROOT / "project" / "new_mnps_v.3.1" / "bench_001"
H1_FREEZE = BENCH_DIR / "h1_analysis_freeze_v3.json"
SELECTION = BENCH_DIR / "selection_manifest_outcome_blind.json"
PROTOCOL = ARTICLE_DIR / "legacy_loss_002_log_only_window_extension_v3_20261008.md"
PRIMARY_DIR = Path(r"I:\AAA_PYTHON_REPOS_BACKUP\homepages\_mnps_legacy_loss_002")
V2_DIR = PRIMARY_DIR / "log_only_extension"
V2_MANIFEST = V2_DIR / "run_manifest.json"
OUT_DIR = PRIMARY_DIR / "log_only_window_extension_v3"
FREEZE_PATH = OUT_DIR / "log_only_window_extension_freeze_v3_20261008.json"
H1_SCRIPT = ARTICLE_DIR / "analyze_h1.py"
PRIMARY_FREEZE = PRIMARY_DIR / "legacy_loss_002_freeze_v1_20261008.json"
PRIMARY_SUMMARY = PRIMARY_DIR / "analysis_summary.json"
PRIMARY_MANIFEST = PRIMARY_DIR / "run_manifest.json"
RAW_VALUES = PRIMARY_DIR / "stage_feature_values.csv"
PRIMARY_PREDICTIONS = PRIMARY_DIR / "stage_predictions.csv"
BOOTSTRAP_DRAWS = 2000
BOOTSTRAP_SEED = 20261015
RAW_REPLAY_ATOL = 1e-15


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_h1():
    sys.path.insert(0, str(ARTICLE_DIR))
    h1 = importlib.import_module("analyze_h1")
    return h1


def verify_primary(h1: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    primary_freeze = read_json(PRIMARY_FREEZE)
    primary_summary = read_json(PRIMARY_SUMMARY)
    primary_manifest = read_json(PRIMARY_MANIFEST)
    if primary_summary.get("status") != "exploratory_complete":
        raise ValueError("Primary LEGACY-LOSS-002 summary is not complete")
    if sha256_file(H1_SCRIPT) != primary_freeze["dependencies"]["h1_analysis_script"]["sha256"]:
        raise ValueError("H1 analysis helper changed since the primary freeze")
    if sha256_file(H1_FREEZE) != primary_freeze["dependencies"]["h1_freeze"]["sha256"]:
        raise ValueError("H1 source freeze changed since the primary freeze")
    if primary_summary.get("freeze_sha256") != sha256_file(PRIMARY_FREEZE):
        raise ValueError("Primary summary points to a different primary freeze")
    outputs = primary_manifest.get("outputs_sha256", {})
    for name, expected in outputs.items():
        path = PRIMARY_DIR / name
        if not path.is_file() or sha256_file(path).lower() != str(expected).lower():
            raise ValueError(f"Primary output hash mismatch: {path}")
    if len(primary_summary.get("complete_common_participants", [])) != 100:
        raise ValueError("Unexpected primary complete-participant count")
    if list(primary_summary.get("feature_order", [])) != list(h1.RAW_INPUT_FEATURES):
        raise ValueError("Primary feature order differs from H1")
    return primary_freeze, primary_summary, outputs


def make_freeze() -> Path:
    h1 = load_h1()
    primary_freeze, primary_summary, _ = verify_primary(h1)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if any(OUT_DIR.iterdir()):
        raise FileExistsError(f"Output directory is not empty; preserving it: {OUT_DIR}")
    v2_manifest = read_json(V2_MANIFEST)
    for name, expected in v2_manifest.get("outputs_sha256", {}).items():
        path = V2_DIR / name
        if sha256_file(path).lower() != str(expected).lower():
            raise ValueError(f"Prior extension output changed: {path}")
    dependencies = {
        "protocol": {"path": str(PROTOCOL.resolve()), "sha256": sha256_file(PROTOCOL)},
        "analysis_script": {"path": str(Path(__file__).resolve()), "sha256": sha256_file(Path(__file__).resolve())},
        "primary_freeze": {"path": str(PRIMARY_FREEZE.resolve()), "sha256": sha256_file(PRIMARY_FREEZE)},
        "primary_summary": {"path": str(PRIMARY_SUMMARY.resolve()), "sha256": sha256_file(PRIMARY_SUMMARY)},
        "primary_run_manifest": {"path": str(PRIMARY_MANIFEST.resolve()), "sha256": sha256_file(PRIMARY_MANIFEST)},
        "primary_raw_values": {"path": str(RAW_VALUES.resolve()), "sha256": sha256_file(RAW_VALUES)},
        "primary_predictions": {"path": str(PRIMARY_PREDICTIONS.resolve()), "sha256": sha256_file(PRIMARY_PREDICTIONS)},
        "prior_log_after_aggregate_run_manifest": {"path": str(V2_MANIFEST.resolve()), "sha256": sha256_file(V2_MANIFEST)},
        "h1_helper": {"path": str(H1_SCRIPT.resolve()), "sha256": sha256_file(H1_SCRIPT)},
        "h1_freeze": {"path": str(H1_FREEZE.resolve()), "sha256": sha256_file(H1_FREEZE)},
        "selection_manifest": {"path": str(SELECTION.resolve()), "sha256": sha256_file(SELECTION)},
    }
    freeze = {
        "schema": "mnps_legacy_loss_002_log_only_window_extension_freeze.v3",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": "post_run_exploratory_v3_after_v1_v2_outcomes_observed",
        "outcome_blind": False,
        "reason_not_outcome_blind": "The primary five-arm results and v1/v2 log-after-aggregation results were observed before the window-level v3 correction.",
        "prior_v2_log_after_aggregation_delta_auc": -0.01,
        "primary_scikit_learn_version": primary_freeze["software"]["scikit_learn"],
        "current_scikit_learn_version": sklearn.__version__,
        "contrast": "window-level feature-specific log10 only on configured four columns versus untransformed raw windows, both aggregated with the frozen support-median helper",
        "feature_order": list(h1.RAW_INPUT_FEATURES),
        "log_features": list(primary_summary["feature_specific_log_set"]),
        "participants": list(primary_summary["complete_common_participants"]),
        "primary_run_manifest_sha256": dependencies["primary_run_manifest"]["sha256"],
        "source_h5_manifest_sha256": primary_freeze["h1_source_freeze_sha256"],
        "input_h5_sha256": primary_freeze["input_h5_sha256"],
        "dependencies": dependencies,
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "raw_replay_absolute_tolerance": RAW_REPLAY_ATOL,
        "software": {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "scikit_learn": sklearn.__version__},
    }
    FREEZE_PATH.write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return FREEZE_PATH


def verify_extension_freeze(h1: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    freeze = read_json(FREEZE_PATH)
    if freeze.get("schema") != "mnps_legacy_loss_002_log_only_window_extension_freeze.v3":
        raise ValueError("Unexpected extension freeze schema")
    for name, dep in freeze["dependencies"].items():
        path = Path(dep["path"])
        if sha256_file(path).lower() != dep["sha256"].lower():
            raise ValueError(f"Frozen extension dependency changed: {name}")
    primary_freeze, primary_summary, outputs = verify_primary(h1)
    if freeze["source_h5_manifest_sha256"] != primary_freeze["h1_source_freeze_sha256"]:
        raise ValueError("Source H5 freeze identity changed")
    if freeze["participants"] != primary_summary["complete_common_participants"]:
        raise ValueError("Participant list differs from primary frozen set")
    return freeze, primary_summary


def load_window_level_arms(
    h1: Any,
    freeze: dict[str, Any],
    participants: list[str],
    features: list[str],
    log_features: set[str],
) -> tuple[dict[str, dict[tuple[str, str, str], float]], list[dict[str, Any]], dict[str, str]]:
    expected_hashes = {
        str(Path(row["path"]).resolve()): str(row["sha256"])
        for row in freeze["input_h5_sha256"]
    }
    if len(expected_hashes) != len(freeze["input_h5_sha256"]):
        raise ValueError("Duplicate source HDF5 paths in extension freeze")
    arms: dict[str, dict[tuple[str, str, str], float]] = {"raw": {}, "L_window": {}}
    qc_rows: list[dict[str, Any]] = []
    input_hashes: dict[str, str] = {}
    for path_text, expected_hash in sorted(expected_hashes.items()):
        path = Path(path_text)
        observed_hash = sha256_file(path)
        if observed_hash.lower() != expected_hash.lower():
            raise ValueError(f"Frozen processed HDF5 hash mismatch: {path}")
        input_hashes[path_text] = observed_hash
        with h5py.File(path, "r") as h5file:
            raw_file = h1._row_source_file(h5file)
            match = h1.FILE_PATTERN.search(Path(raw_file).name)
            if not match:
                raise ValueError(f"Unexpected frozen source recording name: {raw_file}")
            subject = match.group("subject")
            state = "EyesClosed" if match.group("state").lower() == "eyesclosed" else "EyesOpen"
            starts = np.asarray(h5file["window_start"], dtype=np.float64).reshape(-1)
            ends = np.asarray(h5file["window_end"], dtype=np.float64).reshape(-1)
            if starts.shape != ends.shape:
                raise ValueError(f"Window-grid shape mismatch: {path}")
            intervals = list(zip(starts.tolist(), ends.tolist(), strict=True))
            raw_names = h1._decode_names(h5file["features_raw/names"])
            raw_matrix = np.asarray(h5file["features_raw/values"], dtype=np.float32)
            if raw_matrix.shape != (len(intervals), len(raw_names)):
                raise ValueError(f"Saved raw-window matrix misaligned with window grid: {path}")
            positions = {name: index for index, name in enumerate(raw_names)}
            if any(feature not in positions for feature in features):
                raise ValueError(f"Required raw-window feature absent from {path}")
            if subject not in participants:
                raise ValueError(f"Unselected participant in frozen source set: {subject}")
            for feature in features:
                raw = np.asarray(raw_matrix[:, positions[feature]], dtype=np.float64)
                finite = np.isfinite(raw)
                nonpositive = int(np.count_nonzero(finite & (raw <= 0))) if feature in log_features else 0
                if nonpositive:
                    raise ValueError(f"Nonpositive window for configured log feature: {subject} {state} {feature}")
                logged = raw.copy()
                if feature in log_features:
                    logged[finite] = np.log10(raw[finite])
                raw_aggregate, raw_support = h1._supported_aggregate(
                    feature, raw.tolist(), intervals, subject=subject, state=state, arm="raw",
                )
                log_aggregate, log_support = h1._supported_aggregate(
                    feature, logged.tolist(), intervals, subject=subject, state=state, arm="L_window",
                )
                key = (subject, state, feature)
                if key in arms["raw"]:
                    raise ValueError(f"Duplicate subject/state/feature source row: {key}")
                arms["raw"][key] = float(raw_aggregate[0])
                arms["L_window"][key] = float(log_aggregate[0])
                if raw_support["supported_seconds"] != log_support["supported_seconds"]:
                    raise ValueError(f"Log transform changed support geometry: {key}")
                qc_rows.append({
                    "subject": subject, "state": state, "feature": feature,
                    "source_h5": path_text, "source_h5_sha256": observed_hash,
                    "log10_applied_per_window": feature in log_features,
                    "window_count": len(raw), "finite_raw_window_count": int(finite.sum()),
                    "nonpositive_raw_window_count_for_log": nonpositive,
                    "raw_supported_seconds": raw_support["supported_seconds"],
                    "log_supported_seconds": log_support["supported_seconds"],
                    "raw_support_pass": raw_support["support_pass"],
                    "log_support_pass": log_support["support_pass"],
                })
    expected_keys = {
        (participant, state, feature)
        for participant in participants for state in h1.STATES for feature in features
    }
    if set(arms["raw"]) != expected_keys or set(arms["L_window"]) != expected_keys:
        raise ValueError("Frozen source HDF5 files do not cover the exact participant/state/feature set")
    for path_text, expected_hash in expected_hashes.items():
        if sha256_file(Path(path_text)).lower() != expected_hash.lower():
            raise ValueError(f"Frozen processed HDF5 changed during window transform: {path_text}")
    return arms, qc_rows, input_hashes


def run_analysis() -> dict[str, Any]:
    h1 = load_h1()
    freeze, primary_summary = verify_extension_freeze(h1)
    output_names = {
        "arm_results.csv", "paired_contrast.csv", "stage_predictions.csv",
        "stage_model_choices.csv", "transformed_feature_values.csv", "window_transform_qc.csv",
        "analysis_summary.json", "results.md", "run_manifest.json",
    }
    existing = sorted(name for name in output_names if (OUT_DIR / name).exists())
    if existing:
        raise FileExistsError(f"Preserving existing extension outputs: {existing}")

    participants = list(freeze["participants"])
    selected = h1.load_selected_subjects(SELECTION)
    if selected != participants:
        raise ValueError("Frozen participant order differs from H1 selection order")
    features = list(freeze["feature_order"])
    log_features = set(freeze["log_features"])
    raw_rows = read_csv(RAW_VALUES)
    saved_raw_values: dict[tuple[str, str, str], float] = {}
    for row in raw_rows:
        if row["arm"] != "raw":
            continue
        key = (row["subject"], row["state"], row["feature"])
        if key in saved_raw_values:
            raise ValueError(f"Duplicate primary raw feature row: {key}")
        saved_raw_values[key] = float(row["value"])
    expected_keys = {(p, state, feature) for p in participants for state in h1.STATES for feature in features}
    if set(saved_raw_values) != expected_keys or not all(math.isfinite(v) for v in saved_raw_values.values()):
        raise ValueError("Primary raw feature-value table has missing, extra, or non-finite rows")
    window_arms, window_qc_rows, source_hashes = load_window_level_arms(
        h1, freeze, participants, features, log_features,
    )
    values = window_arms["raw"]
    log_values = window_arms["L_window"]
    raw_aggregate_max_abs_error = max(
        abs(values[key] - saved_raw_values[key]) for key in expected_keys
    )
    if raw_aggregate_max_abs_error > 1e-12:
        raise ValueError(f"Window-level raw medians differ from the primary saved raw summaries: {raw_aggregate_max_abs_error}")

    schedule = h1.make_split_schedule(participants)
    primary_prediction_rows = [row for row in read_csv(PRIMARY_PREDICTIONS) if row["arm"] == "raw"]
    primary_probability = {(row["subject"], row["state"]): float(row["mean_oof_probability"]) for row in primary_prediction_rows}
    if len(primary_probability) != len(participants) * len(h1.STATES):
        raise ValueError("Primary raw prediction table has duplicate or missing subject/state rows")

    arm_scores: dict[str, dict[str, float]] = {}
    arm_rows: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    choices: list[dict[str, Any]] = []
    transformed_rows: list[dict[str, Any]] = []
    max_raw_replay_error = 0.0
    for arm, table in (("raw", values), ("L_window", log_values)):
        X: list[list[float]] = []
        y: list[int] = []
        groups: list[str] = []
        row_keys: list[tuple[str, str, int]] = []
        for participant in participants:
            for state, label in (("EyesClosed", 0), ("EyesOpen", 1)):
                X.append([table[(participant, state, feature)] for feature in features])
                y.append(label)
                groups.append(participant)
                row_keys.append((participant, state, label))
                for feature in features:
                    transformed_rows.append({
                        "arm": arm, "subject": participant, "state": state,
                        "feature": feature, "value": table[(participant, state, feature)],
                    })
        fit = h1.nested_grouped_cv(np.asarray(X, dtype=np.float64), np.asarray(y, dtype=np.int8), np.asarray(groups), schedule)
        arm_scores[arm] = {subject: float(score) for subject, score in fit["participant_auc"].items()}
        arm_rows.append({
            "arm": arm, "n_participants": len(participants), "n_features": len(features),
            "mean_paired_participant_auc": float(np.mean(list(arm_scores[arm].values()))),
            "balanced_accuracy": float(fit["balanced_accuracy"]),
            "sensitivity": float(fit["sensitivity"]), "specificity": float(fit["specificity"]),
        })
        for row_index, (participant, state, label) in enumerate(row_keys):
            probability = float(fit["mean_probability"][row_index])
            if arm == "raw":
                max_raw_replay_error = max(max_raw_replay_error, abs(probability - primary_probability[(participant, state)]))
            predictions.append({
                "arm": arm, "subject": participant, "state": state, "label": label,
                "mean_oof_probability": probability,
                "paired_participant_auc": arm_scores[arm][participant],
            })
        for choice in fit["c_choices"]:
            choices.append({"arm": arm, **choice})
        print(f"Fitted {arm}: mean participant AUC={arm_rows[-1]['mean_paired_participant_auc']:.4f}", flush=True)

    differences = {p: arm_scores["L_window"][p] - arm_scores["raw"][p] for p in participants}
    ci_low, ci_high = h1.paired_bootstrap_interval(
        [differences[p] for p in participants], n_draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED,
    )
    contrast = {
        "contrast": "L_window_minus_raw",
        "left_arm": "L_window", "right_arm": "raw",
        "mean_paired_auc_difference": float(np.mean(list(differences.values()))),
        "participant_bootstrap_95_low": ci_low, "participant_bootstrap_95_high": ci_high,
        "n_participants": len(participants), "bootstrap_draws": BOOTSTRAP_DRAWS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "conditional_on_repeated_cv_predictions": True,
    }
    summary = {
        "schema": "mnps_legacy_loss_002_log_only_window_extension_summary.v3",
        "status": "exploratory_complete_post_run_window_level_extension",
        "outcome_blind": False,
        "protocol": str(PROTOCOL.resolve()), "protocol_sha256": sha256_file(PROTOCOL),
        "freeze_path": str(FREEZE_PATH.resolve()), "freeze_sha256": sha256_file(FREEZE_PATH),
        "primary_run_manifest_sha256": freeze["primary_run_manifest_sha256"],
        "n_participants": len(participants), "participants": participants,
        "feature_order": features, "log_features": sorted(log_features),
        "arms": arm_rows, "paired_contrast": contrast,
        "raw_prediction_replay_max_abs_error": max_raw_replay_error,
        "raw_aggregate_max_abs_error_vs_primary": raw_aggregate_max_abs_error,
        "primary_scikit_learn_version": read_json(PRIMARY_FREEZE)["software"]["scikit_learn"],
        "current_scikit_learn_version": sklearn.__version__,
        "source_nonpositive_window_count_for_log_features": 0,
        "source_h5_file_count": len(source_hashes),
        "source_h5_sha256": source_hashes,
        "window_transform_qc_row_count": len(window_qc_rows),
        "bootstrap_intervals_condition_on_repeated_cv_predictions": True,
        "aggregation_order": "feature-specific log10 is applied per finite saved raw window before the frozen support-median aggregation",
        "interpretation": "Post-hoc operational window-transform contrast; does not establish mechanism or replace historical MNPS 2.0.",
    }
    arm_markdown = "\n".join(
        "| {arm} | {n_participants} | {auc:.4f} | {balanced_accuracy:.4f} |".format(
            arm=row["arm"], n_participants=row["n_participants"],
            auc=row["mean_paired_participant_auc"], balanced_accuracy=row["balanced_accuracy"],
        )
        for row in arm_rows
    )
    report = f"""# LEGACY-LOSS-002 window-level log-only extension — results

Generated {dt.datetime.now(dt.timezone.utc).isoformat()} UTC. This is a
post-run exploratory extension, specified after the primary five-arm results
were inspected; it is not outcome-blind or confirmatory.

## Scope

The `L_window` arm applies feature-specific log10 to each finite saved raw
window for {', '.join(sorted(log_features))}, then applies the exact H1
support-preserving median aggregation. It applies no recording-level robust-z
or clipping; the other historical raw-v2 features remain unchanged. The raw
window matrices, window grid and support are read from the 200 frozen processed
HDF5 files. Recomputed raw summaries match the primary H1 values within
{raw_aggregate_max_abs_error:.3g}. No EDF was read and no EEG features were
recomputed. The analysis uses the same ten features, complete paired
participant set, nested grouped-CV helper, split schedule, model grid,
training-fold standardization, and row order as H1.

## Arm results

| Arm | Participants | Mean paired participant AUC | Balanced accuracy |
|---|---:|---:|---:|
{arm_markdown}

## Prespecified paired contrast

`L_window - raw` = **{contrast['mean_paired_auc_difference']:+.4f}** participant AUC
(95% participant-bootstrap interval [{ci_low:+.4f}, {ci_high:+.4f}],
{BOOTSTRAP_DRAWS:,} draws, seed {BOOTSTRAP_SEED}). The interval is conditional
on repeated-CV predictions and excludes model-refitting variability. The
re-fitted raw arm differs from the primary saved raw probabilities by a
maximum absolute value of **{max_raw_replay_error:.6f}**. The primary run used
scikit-learn {read_json(PRIMARY_FREEZE)["software"]["scikit_learn"]}; this
extension uses {sklearn.__version__}. Exact cross-run probabilities are not
expected across this version change. Both paired arms in the extension were
fitted under the same current runtime and shared split schedule.

All configured log-source windows were positive; the per-window log transform
preserved the exact support geometry. This order is material: with an even
number of windows, the ordinary median averages the two middle observations,
so applying log after the median need not equal the median after log. The
earlier v2 result is therefore a separate, narrower log-after-aggregation
contrast and is not a substitute for this window-level analysis. The saved
window-transform QC table records support and nonpositive counts for each
participant/state/feature.

## Interpretation limits

This post-hoc contrast measures the standalone log operation under this exact
feature set, aggregation, classifier and exposed ds005385 cohort. It cannot
establish a biological mechanism or generalize beyond the cohort, and it does
not replace the historical MNPS 2.0 comparator. Output and dependency hashes
are recorded in `run_manifest.json`.
"""

    # All outputs are written after fitting and validations finish.
    write_csv(OUT_DIR / "arm_results.csv", arm_rows)
    write_csv(OUT_DIR / "paired_contrast.csv", [contrast])
    write_csv(OUT_DIR / "stage_predictions.csv", predictions)
    write_csv(OUT_DIR / "stage_model_choices.csv", choices)
    write_csv(OUT_DIR / "transformed_feature_values.csv", transformed_rows)
    write_csv(OUT_DIR / "window_transform_qc.csv", window_qc_rows)
    (OUT_DIR / "analysis_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT_DIR / "results.md").write_text(report, encoding="utf-8")
    outputs = {
        path.name: sha256_file(path)
        for path in sorted(OUT_DIR.iterdir())
        if path.is_file() and path.name != "run_manifest.json"
    }
    manifest = {
        "schema": "mnps_legacy_loss_002_log_only_window_extension_run_manifest.v3",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "freeze_sha256": sha256_file(FREEZE_PATH),
        "dependencies": freeze["dependencies"],
        "outputs_sha256": outputs,
    }
    (OUT_DIR / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("freeze", "run"))
    args = parser.parse_args()
    if args.action == "freeze":
        print(make_freeze())
    else:
        print(json.dumps(run_analysis(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
