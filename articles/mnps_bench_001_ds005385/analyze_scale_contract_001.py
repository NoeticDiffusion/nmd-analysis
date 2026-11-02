"""Exploratory SCALE-CONTRACT-001 derived-scale comparison.

Reads only the frozen V3-STRUCTURE-001 recording-level table. It does not
reopen HDF5/EDF data or recompute MNPS estimators.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import platform
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import scipy
import sklearn
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold

import analyze_h1 as h1


ARTICLE_DIR = Path(__file__).resolve().parent
PROTOCOL = ARTICLE_DIR / "scale_contract_protocol_v1_20261008.md"
UPSTREAM_DIR = Path(r"I:\AAA_PYTHON_REPOS_BACKUP\homepages\_mnps_v3_structure_001")
UPSTREAM_RUN = UPSTREAM_DIR / "run_manifest.json"
UPSTREAM_FREEZE = UPSTREAM_DIR / "v3_structure_freeze_v1_20261008.json"
RECORDING_TABLE = UPSTREAM_DIR / "recording_features.csv"
OUT_DIR = Path(r"I:\AAA_PYTHON_REPOS_BACKUP\homepages\_mnps_scale_contract_001")
FREEZE_NAME = "scale_contract_freeze_v1_20261008.json"
COHORTS = ("H1", "H1R")
SCALES = ("x_native", "T_log1p", "z_fixed_reference")
BOOTSTRAP_DRAWS = 2000
BOOTSTRAP_SEED = 20261008
TRANSFER_SEED = 20261008


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def verify_hash(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {label}: {path}")
    observed = sha256_file(path)
    if observed.lower() != str(expected).lower():
        raise ValueError(f"SHA256 mismatch for {label}: expected {expected}, got {observed}")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _software() -> dict[str, str]:
    return {
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
    }


def _verify_upstream() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    run = read_json(UPSTREAM_RUN)
    freeze_ref = run.get("analysis_freeze", {})
    verify_hash(UPSTREAM_FREEZE, freeze_ref.get("sha256", ""), "upstream analysis freeze")
    freeze = read_json(UPSTREAM_FREEZE)
    if freeze.get("schema") != "mnps_v3_structure_001_freeze.v1":
        raise ValueError("Unexpected upstream structure-freeze schema")
    expected_table_hash = None
    for output in run.get("outputs", []):
        if output.get("path") == "recording_features.csv":
            expected_table_hash = output.get("sha256")
            break
    if not expected_table_hash:
        raise ValueError("Upstream run manifest does not bind recording_features.csv")
    verify_hash(RECORDING_TABLE, str(expected_table_hash), "upstream recording feature table")
    # The upstream source extraction already checked the 400 HDF5 hashes. This
    # derived-scale analysis binds that completed freeze and does not reopen them.
    dependency_refs: list[dict[str, str]] = []
    for label, ref in freeze.get("dependencies", {}).items():
        dependency_refs.append({
            "label": str(label),
            "path": str(ref["path"]),
            "sha256": str(ref["sha256"]),
        })
    return run, freeze, dependency_refs


def _read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"cohort", "subject", "state", *h1.H1_V3_FEATURES}
        if not required.issubset(set(reader.fieldnames or ())):
            raise ValueError("Upstream recording table is missing canonical feature columns")
        rows: list[dict[str, Any]] = []
        for row in reader:
            clean: dict[str, Any] = {
                "cohort": str(row["cohort"]),
                "subject": str(row["subject"]),
                "state": str(row["state"]),
            }
            for name in h1.H1_V3_FEATURES:
                clean[name] = float(row[name])
            rows.append(clean)
    return rows


def _validate_rows(rows: Sequence[Mapping[str, Any]], freeze: Mapping[str, Any]) -> dict[str, list[str]]:
    if len(rows) != 400:
        raise ValueError(f"Expected exactly 400 upstream recordings; got {len(rows)}")
    subjects_by_cohort: dict[str, list[str]] = {}
    keys: set[tuple[str, str, str]] = set()
    by_cohort_subject: dict[tuple[str, str], set[str]] = {}
    domain_rows = []
    for row in rows:
        cohort, subject, state = str(row["cohort"]), str(row["subject"]), str(row["state"])
        key = (cohort, subject, state)
        if key in keys:
            raise ValueError(f"Duplicate recording key: {key}")
        keys.add(key)
        if cohort not in COHORTS or state not in h1.STATES:
            raise ValueError(f"Unexpected cohort or state: {key}")
        by_cohort_subject.setdefault((cohort, subject), set()).add(state)
    for cohort in COHORTS:
        expected = [str(s) for s in freeze["sources"][cohort]["subjects"]]
        subjects_by_cohort[cohort] = expected
        if len(expected) != 100 or len(set(expected)) != 100:
            raise ValueError(f"Upstream freeze must bind 100 unique {cohort} participants")
        if {s for c, s in by_cohort_subject if c == cohort} != set(expected):
            raise ValueError(f"Recording table subject set differs from frozen {cohort} selection")
    h1_subjects = set(subjects_by_cohort["H1"])
    h1r_subjects = set(subjects_by_cohort["H1R"])
    if h1_subjects & h1r_subjects:
        raise ValueError("H1 and H1R participant sets are not disjoint")
    if len(keys) != 400 or any(states != set(h1.STATES) for states in by_cohort_subject.values()):
        raise ValueError("Input does not contain exactly one EC and EO recording per participant")

    for cohort in COHORTS:
        cohort_rows = [row for row in rows if row["cohort"] == cohort]
        for name in h1.H1_V3_FEATURES:
            values = np.asarray([float(row[name]) for row in cohort_rows], dtype=np.float64)
            if not np.isfinite(values).all():
                raise ValueError(f"Non-finite value in complete-case input: {cohort}/{name}")
            if np.any(values < 0.0):
                minimum = float(np.min(values))
                raise ValueError(f"log1p domain gate failed for {cohort}/{name}: minimum={minimum}")
            domain_rows.append({
                "cohort": cohort,
                "feature": name,
                "n_recordings": int(values.size),
                "minimum": float(np.min(values)),
                "maximum": float(np.max(values)),
                "zero_count": int(np.count_nonzero(values == 0.0)),
                "negative_count": int(np.count_nonzero(values < 0.0)),
                "finite_count": int(np.count_nonzero(np.isfinite(values))),
                "log1p_domain_pass": True,
            })
    return subjects_by_cohort


def make_freeze() -> Path:
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise FileExistsError(f"Output directory is not empty; preserving existing contents: {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    run, upstream_freeze, inherited_dependencies = _verify_upstream()
    rows = _read_rows(RECORDING_TABLE)
    subjects = _validate_rows(rows, upstream_freeze)
    dependencies = {
        "protocol": {"path": str(PROTOCOL), "sha256": sha256_file(PROTOCOL)},
        "analysis_script": {"path": str(Path(__file__).resolve()), "sha256": sha256_file(Path(__file__).resolve())},
        "h1_analysis_helper": {
            "path": str(ARTICLE_DIR / "analyze_h1.py"),
            "sha256": sha256_file(ARTICLE_DIR / "analyze_h1.py"),
        },
        "upstream_run_manifest": {"path": str(UPSTREAM_RUN), "sha256": sha256_file(UPSTREAM_RUN)},
        "upstream_analysis_freeze": {"path": str(UPSTREAM_FREEZE), "sha256": sha256_file(UPSTREAM_FREEZE)},
        "upstream_recording_features": {"path": str(RECORDING_TABLE), "sha256": sha256_file(RECORDING_TABLE)},
    }
    freeze = {
        "schema": "mnps_scale_contract_001_freeze.v1",
        "created_utc": utc_now(),
        "status": "exploratory_precalculation_frozen",
        "protocol": dependencies["protocol"],
        "dependencies": dependencies,
        "inherited_upstream_dependencies": inherited_dependencies,
        "upstream": {
            "run_manifest": dependencies["upstream_run_manifest"],
            "analysis_freeze": dependencies["upstream_analysis_freeze"],
            "recording_features": dependencies["upstream_recording_features"],
            "inherited_processed_hdf5_count": len(upstream_freeze["inputs"]),
            "hdf5_reopened_by_this_analysis": False,
            "upstream_dependencies_reverified_here": False,
            "source_complete_participants": {cohort: len(items) for cohort, items in subjects.items()},
        },
        "analysis_contract": {
            "features_canonical_order": list(h1.H1_V3_FEATURES),
            "states": list(h1.STATES),
            "cohorts": list(COHORTS),
            "scales": list(SCALES),
            "log_transform": "natural_log1p_after_recording_median_aggregation",
            "fixed_reference": "native_feature_mean_and_population_sd_fit_on_training_participants_only",
            "within_cohort_outer_repeats": h1.OUTER_REPEATS,
            "within_cohort_outer_folds": h1.OUTER_FOLDS,
            "within_cohort_inner_folds": h1.INNER_FOLDS,
            "C_grid": list(h1.C_GRID),
            "bootstrap_draws": BOOTSTRAP_DRAWS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "transport_train_cohort": "H1",
            "transport_test_cohort": "H1R",
            "transport_inner_folds": 4,
            "transport_seed": TRANSFER_SEED,
        },
        "software": _software(),
        "input_validation": {
            "recording_rows": 400,
            "complete_participant_pairs": {cohort: 100 for cohort in COHORTS},
            "cohorts_participant_disjoint": True,
            "nonnegative_domain_gate_passed": True,
            "all_values_finite": True,
        },
    }
    path = OUT_DIR / FREEZE_NAME
    path.write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Created pre-calculation freeze: {path}")
    print(f"Verified upstream recording rows: {len(rows)}; H1=100; H1R=100")
    print(f"Analysis script SHA256: {dependencies['analysis_script']['sha256']}")
    return path


def verify_freeze(path: Path) -> dict[str, Any]:
    freeze = read_json(path)
    if freeze.get("schema") != "mnps_scale_contract_001_freeze.v1":
        raise ValueError("Unexpected SCALE-CONTRACT freeze schema")
    for label, ref in freeze["dependencies"].items():
        verify_hash(Path(ref["path"]), str(ref["sha256"]), label)
    current_software = _software()
    if freeze.get("software") != current_software:
        raise ValueError("Runtime differs from the pre-calculation freeze")
    _verify_upstream()
    return freeze


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def matrix_for_cohort(
    rows: Sequence[Mapping[str, Any]], cohort: str, subjects: Sequence[str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    by_key = {(str(r["subject"]), str(r["state"])): r for r in rows if r["cohort"] == cohort}
    x_rows: list[list[float]] = []
    labels: list[int] = []
    groups: list[str] = []
    for subject in subjects:
        for state, label in (("EyesClosed", 0), ("EyesOpen", 1)):
            row = by_key[(str(subject), state)]
            x_rows.append([float(row[name]) for name in h1.H1_V3_FEATURES])
            labels.append(label)
            groups.append(str(subject))
    x = np.asarray(x_rows, dtype=np.float64)
    y = np.asarray(labels, dtype=np.int8)
    group_array = np.asarray(groups)
    if x.shape != (2 * len(subjects), len(h1.H1_V3_FEATURES)) or not np.isfinite(x).all():
        raise ValueError(f"Invalid complete matrix for cohort {cohort}: {x.shape}")
    return x, y, group_array


def _reference_parameters(x_train: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = np.mean(x_train, axis=0)
    variance = np.var(x_train, axis=0, ddof=0)
    scale = np.sqrt(variance)
    # Match sklearn 1.8 StandardScaler's float64 two-pass variance error bound
    # for constant-feature detection. Its training-fold mean/scale is the
    # reference being compared, so exact-zero-only handling would be too weak.
    eps = np.finfo(np.float64).eps
    upper_bound = len(x_train) * eps * variance + (len(x_train) * mean * eps) ** 2
    constant = variance <= upper_bound
    scale = np.where(constant, 1.0, scale)
    return mean, scale


def _reference_transform(
    x_train: np.ndarray, x_valid: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mean, scale = _reference_parameters(x_train)
    return (x_train - mean) / scale, (x_valid - mean) / scale, mean, scale


def _logistic(c_value: float) -> LogisticRegression:
    return LogisticRegression(
        C=float(c_value),
        penalty="l2",
        class_weight=None,
        solver="lbfgs",
        max_iter=5000,
    )


def nested_reference_cv(
    matrix: np.ndarray,
    labels: np.ndarray,
    groups: np.ndarray,
    schedule: Sequence[Sequence[h1.OuterFold]],
) -> dict[str, Any]:
    """Nested grouped CV for z_fixed_reference with fold-local mean/SD."""
    prediction_repeats = np.full((len(schedule), len(labels)), np.nan, dtype=np.float64)
    choices: list[dict[str, Any]] = []
    for repeat_index, folds in enumerate(schedule):
        for outer_fold_index, fold in enumerate(folds):
            best_c, best_score = h1.C_GRID[0], -np.inf
            for c_value in h1.C_GRID:
                inner_predictions = np.full(len(fold.train), np.nan, dtype=np.float64)
                for inner in fold.inner:
                    train_global = fold.train[inner.train_local]
                    valid_global = fold.train[inner.valid_local]
                    x_train, x_valid, _, _ = _reference_transform(matrix[train_global], matrix[valid_global])
                    estimator = _logistic(c_value)
                    estimator.fit(x_train, labels[train_global])
                    inner_predictions[inner.valid_local] = estimator.predict_proba(x_valid)[:, 1]
                if not np.isfinite(inner_predictions).all():
                    raise ValueError("Reference inner CV did not predict each training row")
                score = float(np.mean(list(h1.paired_auc_by_subject(
                    labels[fold.train], groups[fold.train], inner_predictions,
                ).values())))
                if score > best_score:
                    best_c, best_score = c_value, score
            x_train, x_test, mean, scale = _reference_transform(matrix[fold.train], matrix[fold.test])
            estimator = _logistic(best_c)
            estimator.fit(x_train, labels[fold.train])
            prediction_repeats[repeat_index, fold.test] = estimator.predict_proba(x_test)[:, 1]
            choices.append({
                "repeat_index": repeat_index,
                "outer_fold": outer_fold_index,
                "selected_C": float(best_c),
                "inner_participant_paired_auc": float(best_score),
                "training_reference_mean": json.dumps(mean.tolist(), separators=(",", ":")),
                "training_reference_population_sd": json.dumps(scale.tolist(), separators=(",", ":")),
            })
    if not np.isfinite(prediction_repeats).all():
        raise ValueError("Reference outer CV did not predict every row in every repeat")
    probabilities = np.mean(prediction_repeats, axis=0)
    return {
        "predictions_by_repeat": prediction_repeats,
        "mean_probability": probabilities,
        "participant_auc": h1.paired_auc_by_subject(labels, groups, probabilities),
        "c_choices": choices,
    }


def feature_scale_summaries(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    feature_rows: list[dict[str, Any]] = []
    domain_rows: list[dict[str, Any]] = []
    for cohort in COHORTS:
        cohort_rows = [r for r in rows if r["cohort"] == cohort]
        by_subject_state = {(str(r["subject"]), str(r["state"])): r for r in cohort_rows}
        subjects = list(dict.fromkeys(str(r["subject"]) for r in cohort_rows))
        for feature in h1.H1_V3_FEATURES:
            native_closed = np.asarray([float(by_subject_state[(s, "EyesClosed")][feature]) for s in subjects])
            native_open = np.asarray([float(by_subject_state[(s, "EyesOpen")][feature]) for s in subjects])
            transformed_closed = np.log1p(native_closed)
            transformed_open = np.log1p(native_open)
            native_delta = native_open - native_closed
            transformed_delta = transformed_open - transformed_closed
            native_midpoint = (native_open + native_closed) / 2.0
            transformed_midpoint = (transformed_open + transformed_closed) / 2.0
            rank = float(stats.spearmanr(native_delta, transformed_delta).statistic)
            observed = np.concatenate((native_closed, native_open))
            domain_rows.append({
                "cohort": cohort,
                "feature": feature,
                "n_recordings": int(observed.size),
                "minimum": float(np.min(observed)),
                "maximum": float(np.max(observed)),
                "zero_count": int(np.count_nonzero(observed == 0.0)),
                "negative_count": int(np.count_nonzero(observed < 0.0)),
                "finite_count": int(np.count_nonzero(np.isfinite(observed))),
                "log1p_domain_pass": bool(np.all(observed >= 0.0)),
            })
            feature_rows.append({
                "cohort": cohort,
                "feature": feature,
                "n_participants": len(subjects),
                "native_mean_EC": float(np.mean(native_closed)),
                "native_mean_EO": float(np.mean(native_open)),
                "native_mean_EO_minus_EC": float(np.mean(native_delta)),
                "native_sd_EO_minus_EC": float(np.std(native_delta, ddof=1)),
                "native_median_abs_EO_minus_EC": float(np.median(np.abs(native_delta))),
                "native_between_participant_sd_midpoint": float(np.std(native_midpoint, ddof=1)),
                "native_change_to_between_sd_ratio": float(
                    np.std(native_delta, ddof=1) / np.std(native_midpoint, ddof=1)
                ) if np.std(native_midpoint, ddof=1) > 0 else math.nan,
                "log1p_mean_EC": float(np.mean(transformed_closed)),
                "log1p_mean_EO": float(np.mean(transformed_open)),
                "log1p_mean_EO_minus_EC": float(np.mean(transformed_delta)),
                "log1p_sd_EO_minus_EC": float(np.std(transformed_delta, ddof=1)),
                "log1p_median_abs_EO_minus_EC": float(np.median(np.abs(transformed_delta))),
                "log1p_between_participant_sd_midpoint": float(np.std(transformed_midpoint, ddof=1)),
                "log1p_change_to_between_sd_ratio": float(
                    np.std(transformed_delta, ddof=1) / np.std(transformed_midpoint, ddof=1)
                ) if np.std(transformed_midpoint, ddof=1) > 0 else math.nan,
                "spearman_native_vs_log1p_participant_change": rank,
                "participant_change_sign_agreement": float(np.mean(np.sign(native_delta) == np.sign(transformed_delta))),
                "zero_native_change_count": int(np.count_nonzero(native_delta == 0.0)),
            })
    return feature_rows, domain_rows


def _split_schedule_payload(schedule: Sequence[Sequence[h1.OuterFold]], groups: np.ndarray) -> dict[str, Any]:
    payload = []
    for repeat_index, folds in enumerate(schedule):
        for fold_index, fold in enumerate(folds):
            payload.append({
                "repeat": repeat_index,
                "outer_fold": fold_index,
                "train_subjects": sorted(set(groups[fold.train].tolist())),
                "test_subjects": sorted(set(groups[fold.test].tolist())),
                "inner_folds": [
                    {
                        "train_subjects": sorted(set(groups[fold.train][inner.train_local].tolist())),
                        "validation_subjects": sorted(set(groups[fold.train][inner.valid_local].tolist())),
                    }
                    for inner in fold.inner
                ],
            })
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"sha256": hashlib.sha256(encoded).hexdigest(), "folds": payload}


def _train_predict(
    scale: str,
    c_value: float,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    if scale == "x_native":
        estimator = h1._model(c_value)
        estimator.fit(x_train, y_train)
        return estimator.predict_proba(x_test)[:, 1], {}
    if scale == "T_log1p":
        transformed_train, transformed_test = np.log1p(x_train), np.log1p(x_test)
        estimator = h1._model(c_value)
        estimator.fit(transformed_train, y_train)
        return estimator.predict_proba(transformed_test)[:, 1], {}
    if scale == "z_fixed_reference":
        transformed_train, transformed_test, mean, scale_values = _reference_transform(x_train, x_test)
        estimator = _logistic(c_value)
        estimator.fit(transformed_train, y_train)
        return estimator.predict_proba(transformed_test)[:, 1], {
            "reference_mean": mean.tolist(),
            "reference_population_sd": scale_values.tolist(),
        }
    raise ValueError(scale)


def select_transfer_c(
    x_train: np.ndarray,
    y_train: np.ndarray,
    groups_train: np.ndarray,
    scale: str,
) -> tuple[float, float]:
    splitter = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=TRANSFER_SEED)
    dummy = np.zeros((len(y_train), 1), dtype=np.float64)
    splits = list(splitter.split(dummy, y_train, groups_train))
    if any(set(groups_train[a]) & set(groups_train[b]) for a, b in splits):
        raise AssertionError("Transfer C-selection split leaked participant groups")
    best_c, best_score = h1.C_GRID[0], -np.inf
    for c_value in h1.C_GRID:
        probabilities = np.full(len(y_train), np.nan, dtype=np.float64)
        for train_index, valid_index in splits:
            fitted, _ = _train_predict(scale, c_value, x_train[train_index], y_train[train_index], x_train[valid_index])
            probabilities[valid_index] = fitted
        if not np.isfinite(probabilities).all():
            raise ValueError("Transfer C selection did not predict each H1 row")
        score = float(np.mean(list(h1.paired_auc_by_subject(
            y_train, groups_train, probabilities,
        ).values())))
        if score > best_score:
            best_c, best_score = c_value, score
    return float(best_c), float(best_score)


def _prediction_rows(
    cohort: str,
    scale: str,
    subjects: Sequence[str],
    probabilities: np.ndarray,
    participant_auc: Mapping[str, float],
    *,
    evaluation: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, subject in enumerate(subjects):
        rows.append({
            "evaluation": evaluation,
            "cohort": cohort,
            "scale": scale,
            "subject": str(subject),
            "p_EC": float(probabilities[2 * index]),
            "p_EO": float(probabilities[2 * index + 1]),
            "participant_paired_auc": float(participant_auc[str(subject)]),
        })
    return rows


def run_analysis(freeze_path: Path) -> None:
    freeze = verify_freeze(freeze_path)
    rows = _read_rows(RECORDING_TABLE)
    subjects_by_cohort = _validate_rows(rows, read_json(UPSTREAM_FREEZE))
    feature_summaries, domain_rows = feature_scale_summaries(rows)

    cv_metrics: list[dict[str, Any]] = []
    cv_predictions: list[dict[str, Any]] = []
    cv_choices: list[dict[str, Any]] = []
    feature_cv_metrics: list[dict[str, Any]] = []
    feature_cv_predictions: list[dict[str, Any]] = []
    feature_cv_choices: list[dict[str, Any]] = []
    split_manifest: dict[str, Any] = {}
    nested_results: dict[tuple[str, str], dict[str, Any]] = {}
    cohort_inputs: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, Sequence[Sequence[h1.OuterFold]]]] = {}

    for cohort_index, cohort in enumerate(COHORTS):
        subjects = subjects_by_cohort[cohort]
        matrix, labels, groups = matrix_for_cohort(rows, cohort, subjects)
        if len(subjects) < 80:
            raise ValueError(f"{cohort} has fewer than 80 complete participants")
        schedule = h1.make_split_schedule(subjects)
        cohort_inputs[cohort] = (matrix, labels, groups, schedule)
        split_manifest[cohort] = _split_schedule_payload(schedule, groups)
        matrices = {
            "x_native": matrix,
            "T_log1p": np.log1p(matrix),
            "z_fixed_reference": matrix,
        }
        for scale_index, scale in enumerate(SCALES):
            if scale == "z_fixed_reference":
                result = nested_reference_cv(matrix, labels, groups, schedule)
            else:
                result = h1.nested_grouped_cv(matrices[scale], labels, groups, schedule)
            nested_results[(cohort, scale)] = result
            scores = result["participant_auc"]
            score_values = [float(scores[s]) for s in subjects]
            auc_ci = h1.paired_bootstrap_interval(
                score_values,
                n_draws=BOOTSTRAP_DRAWS,
                seed=BOOTSTRAP_SEED + 100 * cohort_index + scale_index,
            )
            if scale == "x_native":
                delta, delta_ci = 0.0, (0.0, 0.0)
                max_probability_difference = 0.0
            else:
                native_scores = nested_results[(cohort, "x_native")]["participant_auc"]
                differences = [float(scores[s] - native_scores[s]) for s in subjects]
                delta = float(np.mean(differences))
                delta_ci = h1.paired_bootstrap_interval(
                    differences,
                    n_draws=BOOTSTRAP_DRAWS,
                    seed=BOOTSTRAP_SEED + 1000 + 100 * cohort_index + scale_index,
                )
                max_probability_difference = math.nan
                if scale == "z_fixed_reference":
                    max_probability_difference = float(np.max(np.abs(
                        result["mean_probability"] - nested_results[(cohort, "x_native")]["mean_probability"]
                    )))
            choices = result["c_choices"]
            selected_counts = Counter(float(row["selected_C"]) for row in choices)
            cv_metrics.append({
                "cohort": cohort,
                "scale": scale,
                "n_participants": len(subjects),
                "participant_paired_auc": float(np.mean(score_values)),
                "auc_ci95_low": float(auc_ci[0]),
                "auc_ci95_high": float(auc_ci[1]),
                "delta_vs_x_native": delta,
                "delta_ci95_low": float(delta_ci[0]),
                "delta_ci95_high": float(delta_ci[1]),
                "max_abs_probability_difference_vs_x_native": max_probability_difference,
                "selected_C_counts_json": json.dumps(dict(sorted(selected_counts.items())), separators=(",", ":")),
            })
            cv_predictions.extend(_prediction_rows(
                cohort, scale, subjects, result["mean_probability"], scores,
                evaluation="within_cohort_repeated_nested_cv",
            ))
            for choice in choices:
                cv_choices.append({"cohort": cohort, "scale": scale, **choice})

    # Coordinate-wise prediction audit: retain each of the nine AR/M3
    # components separately and reuse the exact cohort schedule above.
    for cohort in COHORTS:
        subjects = subjects_by_cohort[cohort]
        matrix, labels, groups, schedule = cohort_inputs[cohort]
        for feature_index, feature in enumerate(h1.H1_V3_FEATURES):
            feature_results: dict[str, dict[str, Any]] = {}
            feature_matrices = {
                "x_native": matrix[:, feature_index:feature_index + 1],
                "T_log1p": np.log1p(matrix[:, feature_index:feature_index + 1]),
            }
            for scale_index, scale in enumerate(("x_native", "T_log1p")):
                result = h1.nested_grouped_cv(feature_matrices[scale], labels, groups, schedule)
                feature_results[scale] = result
                scores = result["participant_auc"]
                score_values = [float(scores[s]) for s in subjects]
                auc_ci = h1.paired_bootstrap_interval(
                    score_values,
                    n_draws=BOOTSTRAP_DRAWS,
                    seed=BOOTSTRAP_SEED + 10000 + COHORTS.index(cohort) * 1000 + feature_index * 10 + scale_index,
                )
                if scale == "x_native":
                    delta, delta_ci = 0.0, (0.0, 0.0)
                else:
                    native_scores = feature_results["x_native"]["participant_auc"]
                    differences = [float(scores[s] - native_scores[s]) for s in subjects]
                    delta = float(np.mean(differences))
                    delta_ci = h1.paired_bootstrap_interval(
                        differences,
                        n_draws=BOOTSTRAP_DRAWS,
                        seed=BOOTSTRAP_SEED + 20000 + COHORTS.index(cohort) * 1000 + feature_index * 10 + scale_index,
                    )
                selected_counts = Counter(float(row["selected_C"]) for row in result["c_choices"])
                feature_cv_metrics.append({
                    "cohort": cohort,
                    "feature": feature,
                    "scale": scale,
                    "n_participants": len(subjects),
                    "participant_paired_auc": float(np.mean(score_values)),
                    "auc_ci95_low": float(auc_ci[0]),
                    "auc_ci95_high": float(auc_ci[1]),
                    "delta_vs_x_native": delta,
                    "delta_ci95_low": float(delta_ci[0]),
                    "delta_ci95_high": float(delta_ci[1]),
                    "selected_C_counts_json": json.dumps(dict(sorted(selected_counts.items())), separators=(",", ":")),
                })
                feature_cv_predictions.extend(_prediction_rows(
                    cohort, f"{feature}:{scale}", subjects, result["mean_probability"], scores,
                    evaluation="within_cohort_single_coordinate_nested_cv",
                ))
                for choice in result["c_choices"]:
                    feature_cv_choices.append({
                        "cohort": cohort,
                        "feature": feature,
                        "scale": scale,
                        **choice,
                    })

    # A one-way participant-disjoint transport check: all transform fitting and
    # C selection use H1. H1R is read only after those choices are fixed.
    transfer_metrics: list[dict[str, Any]] = []
    transfer_predictions: list[dict[str, Any]] = []
    x_h1, y_h1, groups_h1 = matrix_for_cohort(rows, "H1", subjects_by_cohort["H1"])
    x_h1r, y_h1r, groups_h1r = matrix_for_cohort(rows, "H1R", subjects_by_cohort["H1R"])
    for scale in SCALES:
        selected_c, selection_auc = select_transfer_c(x_h1, y_h1, groups_h1, scale)
        probabilities, ref = _train_predict(scale, selected_c, x_h1, y_h1, x_h1r)
        participant_auc = h1.paired_auc_by_subject(y_h1r, groups_h1r, probabilities)
        scores = [float(participant_auc[s]) for s in subjects_by_cohort["H1R"]]
        ci = h1.paired_bootstrap_interval(
            scores,
            n_draws=BOOTSTRAP_DRAWS,
            seed=BOOTSTRAP_SEED + 5000 + SCALES.index(scale),
        )
        transfer_metrics.append({
            "train_cohort": "H1",
            "test_cohort": "H1R",
            "scale": scale,
            "n_train_participants": 100,
            "n_test_participants": 100,
            "selected_C": selected_c,
            "H1_C_selection_paired_auc": selection_auc,
            "H1R_participant_paired_auc": float(np.mean(scores)),
            "auc_ci95_low": float(ci[0]),
            "auc_ci95_high": float(ci[1]),
            "reference_mean_json": json.dumps(ref.get("reference_mean"), separators=(",", ":")) if ref else "",
            "reference_population_sd_json": json.dumps(ref.get("reference_population_sd"), separators=(",", ":")) if ref else "",
        })
        transfer_predictions.extend(_prediction_rows(
            "H1R", scale, subjects_by_cohort["H1R"], probabilities, participant_auc,
            evaluation="H1_to_H1R_disjoint_cohort_transport",
        ))

    (OUT_DIR / "scale_feature_summary.csv").write_text("", encoding="utf-8")
    write_csv(OUT_DIR / "scale_feature_summary.csv", feature_summaries)
    write_csv(OUT_DIR / "feature_domains.csv", domain_rows)
    write_csv(OUT_DIR / "cv_metrics.csv", cv_metrics)
    write_csv(OUT_DIR / "cv_predictions.csv", cv_predictions)
    write_csv(OUT_DIR / "cv_c_choices.csv", cv_choices)
    write_csv(OUT_DIR / "feature_prediction_metrics.csv", feature_cv_metrics)
    write_csv(OUT_DIR / "feature_prediction_predictions.csv", feature_cv_predictions)
    write_csv(OUT_DIR / "feature_prediction_c_choices.csv", feature_cv_choices)
    write_csv(OUT_DIR / "transfer_metrics.csv", transfer_metrics)
    write_csv(OUT_DIR / "transfer_predictions.csv", transfer_predictions)
    schedule_path = OUT_DIR / "split_schedule.json"
    schedule_path.write_text(json.dumps(split_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    native_ref_gaps = {
        cohort: next(
            float(row["max_abs_probability_difference_vs_x_native"])
            for row in cv_metrics if row["cohort"] == cohort and row["scale"] == "z_fixed_reference"
        )
        for cohort in COHORTS
    }
    summary = {
        "schema": "mnps_scale_contract_001_summary.v1",
        "generated_utc": utc_now(),
        "freeze_path": str(freeze_path),
        "freeze_sha256": sha256_file(freeze_path),
        "runtime": _software(),
        "upstream_v3_structure_runtime": read_json(UPSTREAM_FREEZE)["software"],
        "source_complete_participants": {"H1": 100, "H1R": 100},
        "feature_count": 16,
        "candidate_family_count": 8,
        "nonnegative_log1p_domain_gate": "passed",
        "hdf5_reopened": False,
        "short_term_test_retest_estimable": False,
        "nuisance_robustness_identifiable": False,
        "z_fixed_reference_max_probability_gap_by_cohort": native_ref_gaps,
        "within_cohort_metrics": cv_metrics,
        "single_coordinate_metrics": feature_cv_metrics,
        "h1_to_h1r_transport_metrics": transfer_metrics,
        "split_schedule_sha256_by_cohort": {
            cohort: split_manifest[cohort]["sha256"] for cohort in COHORTS
        },
    }
    (OUT_DIR / "analysis_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(OUT_DIR, summary)

    output_paths = [
        OUT_DIR / FREEZE_NAME,
        OUT_DIR / "scale_feature_summary.csv",
        OUT_DIR / "feature_domains.csv",
        OUT_DIR / "cv_metrics.csv",
        OUT_DIR / "cv_predictions.csv",
        OUT_DIR / "cv_c_choices.csv",
        OUT_DIR / "feature_prediction_metrics.csv",
        OUT_DIR / "feature_prediction_predictions.csv",
        OUT_DIR / "feature_prediction_c_choices.csv",
        OUT_DIR / "transfer_metrics.csv",
        OUT_DIR / "transfer_predictions.csv",
        schedule_path,
        OUT_DIR / "analysis_summary.json",
        OUT_DIR / "results.md",
    ]
    run_manifest = {
        "schema": "mnps_scale_contract_001_run_manifest.v1",
        "created_utc": utc_now(),
        "freeze": {"path": str(freeze_path), "sha256": sha256_file(freeze_path)},
        "source_recording_rows": 400,
        "outputs": [
            {"path": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in output_paths
        ],
    }
    (OUT_DIR / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Completed SCALE-CONTRACT-001. Output directory: {OUT_DIR}")
    print(f"z-reference vs native maximum probability gaps: {native_ref_gaps}")


def write_report(out_dir: Path, summary: Mapping[str, Any]) -> None:
    lines = [
        "# SCALE-CONTRACT-001 results",
        "",
        f"Generated {summary['generated_utc']} from frozen analysis {Path(str(summary['freeze_path'])).name}.",
        "",
        "## Scope",
        "",
        "Exploratory post-hoc analysis of exposed ds005385 H1/H1R recordings. It reads only the existing V3-STRUCTURE-001 recording-level median table. It does not reopen HDF5 or EDF files, recompute windows, change v3.1 values, or modify support.",
        "",
        "The ordered nine-coordinate AR/M3 block remains intact within the canonical 16-column table. log1p was applied only to the saved recording medians after the support-qualified aggregation. The nonnegative domain gate passed.",
        "",
        "## Within-cohort repeated nested CV",
        "",
        "| Cohort | Scale | n | Paired AUC [95% participant bootstrap CI] | Delta vs native [95% CI] | Max probability gap vs native |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in summary["within_cohort_metrics"]:
        gap = row["max_abs_probability_difference_vs_x_native"]
        gap_text = "—" if not np.isfinite(gap) else f"{gap:.3g}"
        lines.append(
            f"| {row['cohort']} | {row['scale']} | {row['n_participants']} | "
            f"{row['participant_paired_auc']:.3f} [{row['auc_ci95_low']:.3f}, {row['auc_ci95_high']:.3f}] | "
            f"{row['delta_vs_x_native']:.3f} [{row['delta_ci95_low']:.3f}, {row['delta_ci95_high']:.3f}] | {gap_text} |"
        )
    single_by_key = {
        (row["cohort"], row["feature"], row["scale"]): row
        for row in summary["single_coordinate_metrics"]
    }
    lines += [
        "",
        "## Single-coordinate prediction audit",
        "",
        "| Cohort | Feature | Native paired AUC | log1p paired AUC | Delta log1p minus native [95% paired bootstrap CI] |",
        "|---|---|---:|---:|---:|",
    ]
    for cohort in COHORTS:
        for feature in h1.H1_V3_FEATURES:
            native = single_by_key[(cohort, feature, "x_native")]
            transformed = single_by_key[(cohort, feature, "T_log1p")]
            lines.append(
                f"| {cohort} | {feature} | {native['participant_paired_auc']:.3f} | "
                f"{transformed['participant_paired_auc']:.3f} | "
                f"{transformed['delta_vs_x_native']:.3f} "
                f"[{transformed['delta_ci95_low']:.3f}, {transformed['delta_ci95_high']:.3f}] |"
            )
    lines += [
        "",
        "## H1-to-H1R transport check",
        "",
        "| Train | Test | Scale | Selected C | Test paired AUC [95% participant bootstrap CI] |",
        "|---|---|---|---:|---:|",
    ]
    for row in summary["h1_to_h1r_transport_metrics"]:
        lines.append(
            f"| H1 | H1R | {row['scale']} | {row['selected_C']:g} | "
            f"{row['H1R_participant_paired_auc']:.3f} [{row['auc_ci95_low']:.3f}, {row['auc_ci95_high']:.3f}] |"
        )
    lines += [
        "",
        "The fixed-reference representation is fit on training participants only. It is expected to reproduce the ordinary training-fold standardization used by the native model. See the probability-gap column for the numerical check.",
        "",
        "## Criteria and limits",
        "",
        "scale_feature_summary.csv reports all 16 feature-specific EC-to-EO changes and participant midpoint dispersion on native and log1p scales. feature_domains.csv records the observed log1p input ranges. feature_prediction_metrics.csv compares each of the 16 coordinates separately under native and log1p scaling, with the nine AR/M3 components kept distinct. cv_predictions.csv and cv_c_choices.csv retain full-vector out-of-fold results and selected penalties. transfer_predictions.csv retains the disjoint-cohort predictions.",
        "",
        "Short-term test-retest reliability is not estimable because there is no repeated same-state session. Nuisance robustness is not identified because this source table has no prespecified nuisance strata. H1-to-H1R is only a same-dataset disjoint-participant transport check, not independent external validation.",
        "",
        "These are exploratory, descriptive comparisons on exposed outcomes. They do not qualify the measurements, establish a biological mechanism, establish nuisance adjustment, or support prospective performance. Recorded EC always preceded EO.",
        "",
        f"Runtime: Python {summary['runtime']['python'].split()[0]}, NumPy {summary['runtime']['numpy']}, SciPy {summary['runtime']['scipy']}, scikit-learn {summary['runtime']['scikit_learn']}.",
        f"The upstream V3-STRUCTURE-001 freeze records NumPy {summary['upstream_v3_structure_runtime']['numpy']} and scikit-learn {summary['upstream_v3_structure_runtime']['scikit_learn']}; do not compare absolute AUC values across those runs.",
    ]
    (out_dir / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--make-freeze", action="store_true", help="validate inputs and write the pre-calculation freeze")
    parser.add_argument("--run", action="store_true", help="run analysis from the frozen inputs")
    parser.add_argument("--freeze", type=Path, help="freeze JSON path, defaults to the output directory")
    args = parser.parse_args()
    if args.make_freeze == args.run:
        parser.error("choose exactly one of --make-freeze or --run")
    if args.make_freeze:
        make_freeze()
    else:
        run_analysis(args.freeze or (OUT_DIR / FREEZE_NAME))


if __name__ == "__main__":
    main()
