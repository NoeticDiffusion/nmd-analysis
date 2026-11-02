"""Run the frozen MNJ-INFORMATION-001 diagnostic on saved H2/H2R trajectories."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import h5py
import numpy as np
import scipy
import sklearn
from scipy import stats
from sklearn.linear_model import Ridge

import analyze_h1 as h1
import analyze_h2 as h2


NMD_ROOT = Path(r"H:\SourceRepo2\NeuralManifoldDynamics")
BENCH_DIR = NMD_ROOT / "project" / "new_mnps_v.3.1" / "bench_001"
ARTICLE_DIR = Path(__file__).resolve().parent
OUT_DIR_DEFAULT = Path(r"I:\AAA_PYTHON_REPOS_BACKUP\homepages\_mnps_mnj_information_001")
PROTOCOL_DEFAULT = ARTICLE_DIR / "mnj_information_protocol_v1_20261008.md"
H2_FREEZE_DEFAULT = BENCH_DIR / "h2_analysis_freeze_v1_20261007.json"
H2R_FREEZE_DEFAULT = BENCH_DIR / "h2r_analysis_freeze_v1_20261008.json"
FREEZE_NAME = "mnj_information_freeze_v1_20261008.json"
COHORTS = ("H2", "H2R")
MNJ_FIELDS = ("mnj_frobenius_norm", "mnj_antisymmetric_frobenius_norm", "mnj_symmetric_frobenius_norm", "mnj_singular_value_anisotropy")
FAST_FIELDS = tuple(h2.FAST_FEATURES)
ALL_FIELDS = FAST_FIELDS + MNJ_FIELDS
N_BOOTSTRAP = 2000
BOOTSTRAP_SEED = 20261008
RIDGE_ALPHA = 1.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return result


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def verify_hash(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {label}: {path}")
    observed = sha256_file(path)
    if observed.lower() != expected.lower():
        raise ValueError(f"SHA256 mismatch for {label}: {path}")


def validate_source_freeze(freeze_path: Path, nmd_root: Path) -> dict[str, Any]:
    frozen = read_json(freeze_path)
    if frozen.get("schema") != "mnps_bench_001_h2_analysis_freeze.v1":
        raise ValueError(f"Unexpected H2 source-freeze schema: {freeze_path}")
    run_dir = Path(frozen["run_dir"])
    selection = Path(frozen["selection_manifest"]["path"])
    execution = Path(frozen["execution_manifest"]["path"])
    h2.validate_analysis_freeze(freeze_path, run_dir, selection, execution, nmd_root)
    return frozen


def make_freeze(args: argparse.Namespace) -> Path:
    out_dir: Path = args.out_dir
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty; preserving existing contents: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    source_freezes: dict[str, dict[str, Any]] = {}
    for cohort, path in (("H2", args.h2_freeze), ("H2R", args.h2r_freeze)):
        source_freezes[cohort] = validate_source_freeze(path, args.nmd_root)

    subjects_by_cohort: dict[str, list[str]] = {}
    input_rows: list[dict[str, str]] = []
    dependencies: dict[str, dict[str, str]] = {}

    def bind(label: str, path: Path, expected: str | None = None) -> None:
        digest = expected or sha256_file(path)
        verify_hash(path, digest, label)
        dependencies[label] = {"path": str(path), "sha256": digest}

    for cohort, frozen in source_freezes.items():
        selection_path = Path(frozen["selection_manifest"]["path"])
        subjects = h2.load_selected_subjects(selection_path)
        subjects_by_cohort[cohort] = subjects
        if len(frozen.get("input_h5_sha256", [])) != 200:
            raise ValueError(f"Expected 200 source inputs for {cohort}")
        input_rows.extend({"cohort": cohort, "path": str(row["path"]), "sha256": str(row["sha256"])} for row in frozen["input_h5_sha256"])
        bind(f"{cohort}_source_freeze", args.h2_freeze if cohort == "H2" else args.h2r_freeze)
        for ref_key in ("selection_manifest", "execution_manifest", "protocol", "amendment_1", "h2_config", "h2_index", "h2_analysis_script", "h2_analysis_test", "h1_cv_script_dependency", "h1_cv_test_dependency"):
            ref = frozen.get(ref_key)
            if isinstance(ref, dict) and "path" in ref and "sha256" in ref:
                label = f"{cohort}_{ref_key}"
                bind(label, Path(ref["path"]), str(ref["sha256"]))
        for relpath, ref in frozen.get("nmd_pipeline_code", {}).items():
            bind(f"NMD_{relpath}", Path(ref["path"]), str(ref["sha256"]))

    if set(subjects_by_cohort["H2"]) & set(subjects_by_cohort["H2R"]):
        raise ValueError("H2 and H2R participant sets overlap")
    if len(input_rows) != 400 or len({row["path"].lower() for row in input_rows}) != 400:
        raise ValueError("Expected 400 unique frozen H2/H2R HDF5 inputs")
    bind("mnj_information_protocol", args.protocol)
    bind("mnj_information_analysis_script", Path(__file__).resolve())

    software = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "h5py": h5py.__version__,
    }
    freeze_payload = {
        "schema": "mnps_mnj_information_001_freeze.v1",
        "created_utc": utc_now(),
        "protocol_status": "exploratory_protocol_frozen_before_matrix_diagnostics",
        "protocol": dependencies["mnj_information_protocol"],
        "sources": {
            cohort: {
                "freeze": dependencies[f"{cohort}_source_freeze"],
                "subjects": subjects_by_cohort[cohort],
                "source_software": source_freezes[cohort].get("software", {}),
            }
            for cohort in COHORTS
        },
        "dependencies": dependencies,
        "inputs": input_rows,
        "estimator_contract": {
            "fast_coordinates_order": list(FAST_FIELDS),
            "window_seconds": h2.WINDOW_SEC,
            "step_seconds": h2.STEP_SEC,
            "max_time_gap_seconds": h2.MAX_TIME_GAP_SEC,
            "max_jump_sigma": h2.MAX_JUMP_SIGMA,
            "savgol_window": h2.SAVGOL_WINDOW,
            "savgol_polyorder": h2.SAVGOL_POLYORDER,
            "knn_k": h2.KNN_K,
            "super_window": h2.SUPER_WINDOW,
            "ridge_alpha_for_jacobians": h2.RIDGE_ALPHA,
            "distance_weighted": h2.DISTANCE_WEIGHTED,
            "minimum_finite_centers": h2.MIN_MNJ_CENTERS,
            "minimum_finite_center_fraction": h2.MIN_MNJ_CENTER_FRACTION,
            "minimum_unique_support_seconds": h2.MIN_SUPPORTED_SEC,
        },
        "static_predictability_contract": {
            "model": "multi-output Ridge(alpha=1.0)",
            "target_fields": list(MNJ_FIELDS),
            "predictors": list(FAST_FIELDS),
            "outer_folds": h1.OUTER_FOLDS,
            "outer_repeats": h1.OUTER_REPEATS,
            "scaling": "training-fold StandardScaler for predictors and targets",
            "participant_bootstrap_draws": N_BOOTSTRAP,
            "participant_bootstrap_seed": BOOTSTRAP_SEED,
            "minimum_complete_participants": h1.MIN_COHORT,
        },
        "temporal_order_control": "reverse all finite/gap/jump-delimited trajectory segments, re-label on increasing 4-second grid, then re-estimate with same kernels",
        "input_validation": "H2 and H2R source freezes validated against their embedded file/code/dependency hashes before analysis freeze creation",
        "software": software,
    }
    out_path = out_dir / FREEZE_NAME
    out_path.write_text(json.dumps(freeze_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Created MNJ analysis freeze: {out_path}")
    print(f"Verified source inputs: {len(input_rows)}; participants H2={len(subjects_by_cohort['H2'])}, H2R={len(subjects_by_cohort['H2R'])}")
    return out_path


def verify_analysis_freeze(freeze_path: Path, nmd_root: Path) -> dict[str, Any]:
    frozen = read_json(freeze_path)
    if frozen.get("schema") != "mnps_mnj_information_001_freeze.v1":
        raise ValueError("Unexpected MNJ-INFORMATION freeze schema")
    for label, ref in frozen["dependencies"].items():
        verify_hash(Path(ref["path"]), str(ref["sha256"]), label)
    if len(frozen["inputs"]) != 400:
        raise ValueError("MNJ-INFORMATION freeze must contain exactly 400 HDF5 files")
    source_freezes: dict[str, dict[str, Any]] = {}
    for cohort in COHORTS:
        path = Path(frozen["sources"][cohort]["freeze"]["path"])
        source_freezes[cohort] = validate_source_freeze(path, nmd_root)
    for row in frozen["inputs"]:
        verify_hash(Path(row["path"]), str(row["sha256"]), f"{row['cohort']} source HDF5")
    return frozen


def _finite_spearman(x: Sequence[float], y: Sequence[float]) -> tuple[float, int]:
    pair = np.column_stack((np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)))
    keep = np.isfinite(pair).all(axis=1)
    n = int(keep.sum())
    if n < 3 or np.ptp(pair[keep, 0]) == 0 or np.ptp(pair[keep, 1]) == 0:
        return math.nan, n
    return float(stats.spearmanr(pair[keep, 0], pair[keep, 1]).statistic), n


def _matrix_columns(prefix: str) -> list[str]:
    return [f"{prefix}_{i}{j}" for i in range(4) for j in range(4)]


def _matrix_payload(matrix: np.ndarray) -> dict[str, Any]:
    jmat = np.asarray(matrix, dtype=np.float64)
    symmetric = 0.5 * (jmat + jmat.T)
    antisymmetric = 0.5 * (jmat - jmat.T)
    singular = np.linalg.svd(jmat, compute_uv=False)
    eigenvalues = sorted(np.linalg.eigvals(jmat), key=lambda value: (abs(value), value.real, value.imag))
    rank = int(np.linalg.matrix_rank(jmat))
    condition = float(np.linalg.cond(jmat))
    metrics = h2.matrix_mnj_metrics(jmat)
    pythagorean_lhs = float(metrics["mnj_frobenius_norm"] ** 2)
    pythagorean_rhs = float(metrics["mnj_symmetric_frobenius_norm"] ** 2 + metrics["mnj_antisymmetric_frobenius_norm"] ** 2)
    payload: dict[str, Any] = {
        **metrics,
        "trace": float(np.trace(jmat)),
        "determinant": float(np.linalg.det(jmat)),
        "spectral_radius": float(max(abs(value) for value in eigenvalues)),
        "max_eigenvalue_real_part": float(max(value.real for value in eigenvalues)),
        "numerical_rank": rank,
        "condition_number": condition,
        "pythagorean_abs_residual": abs(pythagorean_lhs - pythagorean_rhs),
        "pythagorean_relative_residual": abs(pythagorean_lhs - pythagorean_rhs) / max(pythagorean_lhs, np.finfo(float).tiny),
    }
    payload.update({f"singular_value_{index + 1}": float(value) for index, value in enumerate(singular)})
    for index, value in enumerate(eigenvalues, start=1):
        payload[f"eigenvalue_{index}_real"] = float(value.real)
        payload[f"eigenvalue_{index}_imag"] = float(value.imag)
    for prefix, value in (("J", jmat), ("S", symmetric), ("A", antisymmetric)):
        for i in range(4):
            for j in range(4):
                payload[f"{prefix}_{i}{j}"] = float(value[i, j])
    return payload


def estimate_matrices(
    values: np.ndarray,
    starts: np.ndarray,
    ends: np.ndarray,
    *,
    subject: str,
    state: str,
    cohort: str,
    source_h5: str,
    projection: Any,
    jacobian_module: Any,
    reverse: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    x = np.asarray(values, dtype=np.float64)
    t = np.asarray(starts, dtype=np.float64).reshape(-1)
    e = np.asarray(ends, dtype=np.float64).reshape(-1)
    intervals = list(zip(t.tolist(), e.tolist(), strict=True))
    segments = h2._trajectory_segments(x, t, projection=projection)
    rows: list[dict[str, Any]] = []
    attempted_centers = 0
    underdetermined_centers = 0
    finite_matrices = 0
    for segment_id, absolute_rows in enumerate(segments):
        if absolute_rows.size < 3:
            continue
        forward_absolute_rows = np.asarray(absolute_rows, dtype=np.int64)
        map_rows = forward_absolute_rows[::-1] if reverse else forward_absolute_rows
        segment_values = np.asarray(x[map_rows], dtype=np.float32)
        local_starts = t[map_rows]
        centers = np.arange(h2.SUPER_WINDOW // 2, segment_values.shape[0] - h2.SUPER_WINDOW // 2, dtype=np.int32)
        attempted_centers += int(centers.size)
        if centers.size == 0:
            continue
        derivative = projection.estimate_derivatives_segmented(
            segment_values,
            h2.STEP_SEC,
            method="sav_gol",
            max_jump=h2.MAX_JUMP_SIGMA,
            min_seg=h2.MIN_SEGMENT,
            savgol_window=h2.SAVGOL_WINDOW,
            polyorder=h2.SAVGOL_POLYORDER,
        )
        nn_indices = projection.build_knn_indices(segment_values, k=h2.KNN_K, metric="euclidean", whiten=True)
        underdetermined_centers += h2._finite_center_under_determined_count(
            centers, nn_indices, jacobian_module, total=segment_values.shape[0],
        )
        gather = getattr(jacobian_module, "_gather_indices")
        matrices = jacobian_module.estimate_local_jacobians(
            segment_values,
            derivative,
            nn_indices,
            super_window=h2.SUPER_WINDOW,
            ridge_alpha=h2.RIDGE_ALPHA,
            distance_weighted=h2.DISTANCE_WEIGHTED,
            j_dot_dt=h2.STEP_SEC,
            knn_k=h2.KNN_K,
            require_determined_support=False,
        )
        for local_center, jmat in zip(np.asarray(matrices.centers, dtype=np.int64), matrices.j_hat, strict=True):
            jmat = np.asarray(jmat, dtype=np.float64)
            if jmat.shape != (4, 4) or not np.isfinite(jmat).all():
                continue
            finite_matrices += 1
            local_center = int(local_center)
            support_indices = np.asarray(gather(local_center, nn_indices, h2.SUPER_WINDOW, segment_values.shape[0]))
            underdetermined = support_indices.size < 4 * (4 + 1)
            source_row = int(map_rows[local_center])
            payload = _matrix_payload(jmat)
            payload.update({
                "cohort": cohort,
                "subject": subject,
                "state": state,
                "source_h5": source_h5,
                "segment_id": segment_id,
                "window_row": source_row,
                "window_start_sec": float(t[source_row]),
                "window_end_sec": float(e[source_row]),
                "center_time_sec": float((t[source_row] + e[source_row]) / 2),
                "attempted_center_count_recording": int(centers.size),
                "neighborhood_fit_row_count": int(support_indices.size),
                "underdetermined_center": bool(underdetermined),
                "time_reversed": bool(reverse),
            })
            payload.update({f"x_{name}": float(x[source_row, index]) for index, name in enumerate(FAST_FIELDS)})
            rows.append(payload)
    support_summary: dict[str, Any] = {
        "cohort": cohort,
        "subject": subject,
        "state": state,
        "source_h5": source_h5,
        "attempted_center_count": attempted_centers,
        "finite_jacobian_center_count": finite_matrices,
        "underdetermined_center_count": underdetermined_centers,
        "finite_center_fraction": finite_matrices / attempted_centers if attempted_centers else 0.0,
        "time_reversed": bool(reverse),
    }
    for metric in MNJ_FIELDS:
        finite = [row for row in rows if math.isfinite(float(row[metric]))]
        support_seconds = h1.union_duration((row["window_start_sec"], row["window_end_sec"]) for row in finite)
        fraction = len(finite) / attempted_centers if attempted_centers else 0.0
        passed = len(finite) >= h2.MIN_MNJ_CENTERS and fraction >= h2.MIN_MNJ_CENTER_FRACTION and support_seconds >= h2.MIN_SUPPORTED_SEC
        support_summary[f"{metric}_finite_centers"] = len(finite)
        support_summary[f"{metric}_support_seconds"] = support_seconds
        support_summary[f"{metric}_support_pass"] = passed
        support_summary[f"{metric}_median"] = float(np.median([row[metric] for row in finite])) if passed else math.nan
    return rows, support_summary


def extract_all(freeze: Mapping[str, Any], projection: Any, jacobian_module: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[tuple[str, str, str], np.ndarray]]:
    recording_rows: list[dict[str, Any]] = []
    center_rows: list[dict[str, Any]] = []
    support_rows: list[dict[str, Any]] = []
    reverse_rows: list[dict[str, Any]] = []
    matrix_cache: dict[tuple[str, str, str], np.ndarray] = {}
    input_by_cohort = {cohort: [row for row in freeze["inputs"] if row["cohort"] == cohort] for cohort in COHORTS}
    for cohort in COHORTS:
        for index, input_row in enumerate(input_by_cohort[cohort], start=1):
            path = Path(input_row["path"])
            with h5py.File(path, "r") as h5file:
                raw_file = h1._row_source_file(h5file)
                match = h2.H2_FILE_PATTERN.search(Path(raw_file).name)
                if not match:
                    raise ValueError(f"Not a selected H2/H2R session-1 acq-pre recording: {path}")
                subject = match.group("subject")
                state = "EyesClosed" if match.group("state").lower() == "eyesclosed" else "EyesOpen"
                payloads = h1._json_dataset(h5file["measurements/v3_1/recordings_json"])
                if len(payloads) != 1:
                    raise ValueError(f"Expected one v3.1 recording payload: {path}")
                windows = payloads[0]["measurement_payload"].get("windows", [])
                starts = np.asarray([float(window["window_start_sec"]) for window in windows], dtype=np.float64)
                ends = np.asarray([float(window["window_end_sec"]) for window in windows], dtype=np.float64)
                candidate_rows = {name: [] for name in FAST_FIELDS}
                for window in windows:
                    for feature, candidate in h2.FAST_CANDIDATES.items():
                        candidate_rows[feature].append(h2._candidate_value(window.get("measurements", []), candidate))
                intervals = list(zip(starts.tolist(), ends.tolist(), strict=True))
                fast_values: dict[str, float] = {}
                for feature in FAST_FIELDS:
                    aggregate, support = h1._supported_aggregate(
                        feature, candidate_rows[feature], intervals,
                        subject=subject, state=state, arm=h2.FAST_ARM,
                    )
                    fast_values[feature] = float(aggregate[0])
                    support.update({"cohort": cohort, "source_h5": str(path)})
                    support_rows.append(support)
                trajectory = np.asarray([
                    [np.nan if value is None else float(value) for value in candidate_rows[feature]]
                    for feature in FAST_FIELDS
                ], dtype=np.float64).T
                original_centers, original_support = estimate_matrices(
                    trajectory, starts, ends, subject=subject, state=state, cohort=cohort,
                    source_h5=str(path), projection=projection, jacobian_module=jacobian_module,
                )
                reversed_centers, reversed_support = estimate_matrices(
                    trajectory, starts, ends, subject=subject, state=state, cohort=cohort,
                    source_h5=str(path), projection=projection, jacobian_module=jacobian_module, reverse=True,
                )
            metric_values = {name: original_support[f"{name}_median"] for name in MNJ_FIELDS}
            recording_rows.append({
                "cohort": cohort,
                "subject": subject,
                "state": state,
                "source_h5": str(path),
                "source_h5_sha256": input_row["sha256"],
                **fast_values,
                **metric_values,
                **{key: value for key, value in original_support.items() if key.endswith(("_finite_centers", "_support_seconds", "_support_pass"))},
            })
            center_rows.extend(original_centers)
            support_rows.append(original_support)
            original_by_key = {(row["segment_id"], row["window_row"]): row for row in original_centers}
            reverse_by_key = {(row["segment_id"], row["window_row"]): row for row in reversed_centers}
            matched = sorted(set(original_by_key) & set(reverse_by_key))
            differences: dict[str, list[float]] = {name: [] for name in MNJ_FIELDS}
            j_rel_errors: list[float] = []
            j_abs_errors: list[float] = []
            for key in matched:
                left, right = original_by_key[key], reverse_by_key[key]
                left_matrix = np.asarray([left[f"J_{i}{j}"] for i in range(4) for j in range(4)])
                right_matrix = np.asarray([right[f"J_{i}{j}"] for i in range(4) for j in range(4)])
                j_error = float(np.linalg.norm(left_matrix + right_matrix))
                j_abs_errors.append(j_error)
                j_rel_errors.append(j_error / max(float(np.linalg.norm(left_matrix)), np.finfo(float).tiny))
                for name in MNJ_FIELDS:
                    differences[name].append(abs(float(left[name]) - float(right[name])))
            reverse_rows.append({
                "cohort": cohort,
                "subject": subject,
                "state": state,
                "matched_center_count": len(matched),
                "original_finite_center_count": original_support["finite_jacobian_center_count"],
                "reversed_finite_center_count": reversed_support["finite_jacobian_center_count"],
                "median_frobenius_norm_J_plus_J_reverse": float(np.median(j_abs_errors)) if j_abs_errors else math.nan,
                "max_frobenius_norm_J_plus_J_reverse": float(np.max(j_abs_errors)) if j_abs_errors else math.nan,
                "median_relative_J_sign_reversal_error": float(np.median(j_rel_errors)) if j_rel_errors else math.nan,
                "max_relative_J_sign_reversal_error": float(np.max(j_rel_errors)) if j_rel_errors else math.nan,
                **{f"median_abs_difference_{name}": float(np.median(values)) if values else math.nan for name, values in differences.items()},
                **{f"max_abs_difference_{name}": float(np.max(values)) if values else math.nan for name, values in differences.items()},
                "reversed_support_summary_json": json.dumps(reversed_support, allow_nan=True),
            })
            matrix_cache[(cohort, subject, state)] = trajectory
            if index % 20 == 0 or index == len(input_by_cohort[cohort]):
                print(f"{cohort}: processed {index}/{len(input_by_cohort[cohort])} recordings", flush=True)

    # H2/H2R must contain exactly one processed EC and EO recording per frozen participant.
    keys = {(row["cohort"], row["subject"], row["state"]) for row in recording_rows}
    if len(recording_rows) != 400 or len(keys) != 400:
        raise ValueError("H2/H2R records do not form 400 unique recording keys")
    for cohort in COHORTS:
        expected = {(cohort, subject, state) for subject in freeze["sources"][cohort]["subjects"] for state in h1.STATES}
        if expected != {key for key in keys if key[0] == cohort}:
            raise ValueError(f"{cohort} recordings do not match frozen selection and EC/EO pairing")
    return recording_rows, center_rows, support_rows, reverse_rows, matrix_cache


def _r2(y: np.ndarray, pred: np.ndarray) -> float:
    denominator = float(np.sum((y - np.mean(y)) ** 2))
    return float(1.0 - np.sum((y - pred) ** 2) / denominator) if denominator > 0 else math.nan


def _bootstrap_r2(y: np.ndarray, pred: np.ndarray, subjects: Sequence[str], *, seed: int) -> tuple[float, float]:
    unique = list(dict.fromkeys(subjects))
    rows_by_subject = {subject: np.flatnonzero(np.asarray(subjects) == subject) for subject in unique}
    rng = np.random.default_rng(seed)
    samples = np.full(N_BOOTSTRAP, np.nan, dtype=np.float64)
    for draw in range(N_BOOTSTRAP):
        chosen = rng.choice(unique, size=len(unique), replace=True)
        indices = np.concatenate([rows_by_subject[subject] for subject in chosen])
        samples[draw] = _r2(y[indices], pred[indices])
    return tuple(float(value) for value in np.nanpercentile(samples, [2.5, 97.5]))


def static_predictability(
    rows: Sequence[Mapping[str, Any]], freeze: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    results: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    complete_counts: dict[str, int] = {}
    for cohort in COHORTS:
        selected_subjects = list(freeze["sources"][cohort]["subjects"])
        by_key = {(row["subject"], row["state"]): row for row in rows if row["cohort"] == cohort}
        complete = [
            subject for subject in selected_subjects
            if all(np.isfinite(np.asarray([[by_key[(subject, state)][name] for name in ALL_FIELDS] for state in h1.STATES], dtype=np.float64)).all(axis=1))
        ]
        complete_counts[cohort] = len(complete)
        if len(complete) < h1.MIN_COHORT:
            results.append({"cohort": cohort, "n_participants": len(complete), "target": "ALL", "status": "coverage_only_below_80"})
            continue
        ordered = [by_key[(subject, state)] for subject in complete for state in h1.STATES]
        x = np.asarray([[row[name] for name in FAST_FIELDS] for row in ordered], dtype=np.float64)
        y = np.asarray([[row[name] for name in MNJ_FIELDS] for row in ordered], dtype=np.float64)
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError(f"Unexpected missing value in complete static-predictability set for {cohort}")
        labels = np.tile(np.asarray([0, 1], dtype=np.int8), len(complete))
        groups = np.repeat(np.asarray(complete), 2)
        schedule = h1.make_split_schedule(complete)
        prediction_repeats = np.full((h1.OUTER_REPEATS, len(ordered), len(MNJ_FIELDS)), np.nan, dtype=np.float64)
        for repeat_index, folds in enumerate(schedule):
            for fold in folds:
                x_train, x_test = x[fold.train], x[fold.test]
                y_train = y[fold.train]
                x_mean = np.mean(x_train, axis=0)
                x_scale = np.std(x_train, axis=0, ddof=0)
                x_scale = np.where(x_scale > 0, x_scale, 1.0)
                y_mean = np.mean(y_train, axis=0)
                y_scale = np.std(y_train, axis=0, ddof=0)
                y_scale = np.where(y_scale > 0, y_scale, 1.0)
                model = Ridge(alpha=RIDGE_ALPHA)
                model.fit((x_train - x_mean) / x_scale, (y_train - y_mean) / y_scale)
                prediction_repeats[repeat_index, fold.test] = model.predict((x_test - x_mean) / x_scale) * y_scale + y_mean
        if not np.isfinite(prediction_repeats).all():
            raise ValueError(f"Incomplete repeated held-out predictions for {cohort}")
        predictions = np.mean(prediction_repeats, axis=0)
        for target_index, target in enumerate(MNJ_FIELDS):
            y_target = y[:, target_index]
            yhat = predictions[:, target_index]
            ci_low, ci_high = _bootstrap_r2(y_target, yhat, [str(row["subject"]) for row in ordered], seed=BOOTSTRAP_SEED + target_index)
            results.append({
                "cohort": cohort,
                "target": target,
                "n_participants": len(complete),
                "n_recordings": len(ordered),
                "n_predictors": len(FAST_FIELDS),
                "n_outputs": len(MNJ_FIELDS),
                "linear_coefficients_and_intercepts_total": len(FAST_FIELDS) * len(MNJ_FIELDS) + len(MNJ_FIELDS),
                "ridge_alpha": RIDGE_ALPHA,
                "out_of_fold_r2": _r2(y_target, yhat),
                "ci95_low_conditional_on_repeated_cv": ci_low,
                "ci95_high_conditional_on_repeated_cv": ci_high,
                "status": "computed",
            })
        for index, row in enumerate(ordered):
            for target_index, target in enumerate(MNJ_FIELDS):
                prediction_rows.append({
                    "cohort": cohort,
                    "subject": row["subject"],
                    "state": row["state"],
                    "target": target,
                    "observed": float(y[index, target_index]),
                    "mean_repeated_oof_prediction": float(predictions[index, target_index]),
                })
        print(f"{cohort}: static predictability CV complete, n={len(complete)}", flush=True)
    return results, prediction_rows, complete_counts


def summarize_recordings(
    rows: Sequence[Mapping[str, Any]], centers: Sequence[Mapping[str, Any]], support: Sequence[Mapping[str, Any]],
    reversal: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    scalar_corr: list[dict[str, Any]] = []
    position_assoc: list[dict[str, Any]] = []
    matrix_summary: list[dict[str, Any]] = []
    for cohort in COHORTS:
        for state in h1.STATES:
            group = [row for row in rows if row["cohort"] == cohort and row["state"] == state]
            for left_index, left in enumerate(MNJ_FIELDS):
                for right in MNJ_FIELDS[left_index:]:
                    rho, n = _finite_spearman([r[left] for r in group], [r[right] for r in group])
                    scalar_corr.append({"cohort": cohort, "state": state, "summary_left": left, "summary_right": right, "n_pair": n, "spearman_rho": rho})
            center_group = [row for row in centers if row["cohort"] == cohort and row["state"] == state]
            for coordinate in FAST_FIELDS:
                xname = f"x_{coordinate}"
                for metric in MNJ_FIELDS:
                    per_recording: list[float] = []
                    for subject in dict.fromkeys(str(row["subject"]) for row in group):
                        local = [row for row in center_group if row["subject"] == subject]
                        rho, n = _finite_spearman([r[xname] for r in local], [r[metric] for r in local])
                        if n >= 3 and math.isfinite(rho):
                            per_recording.append(rho)
                    position_assoc.append({
                        "cohort": cohort,
                        "state": state,
                        "coordinate": coordinate,
                        "local_mnj_summary": metric,
                        "n_recordings_with_defined_rho": len(per_recording),
                        "median_recording_spearman_rho": float(np.median(per_recording)) if per_recording else math.nan,
                        "p25_recording_spearman_rho": float(np.percentile(per_recording, 25)) if per_recording else math.nan,
                        "p75_recording_spearman_rho": float(np.percentile(per_recording, 75)) if per_recording else math.nan,
                    })
            selected_centers = [row for row in center_group]
            selected_support = [
                row for row in support
                if row.get("cohort") == cohort and row.get("state") == state
                and not row.get("time_reversed") and "attempted_center_count" in row
            ]
            selected_reversal = [row for row in reversal if row.get("cohort") == cohort and row.get("state") == state]
            all_four_supported = [
                row for row in selected_support
                if sum(bool(row[f"{metric}_support_pass"]) for metric in MNJ_FIELDS) == 4
            ]
            matrix_summary.append({
                "cohort": cohort,
                "state": state,
                "n_recordings": len(group),
                "n_finite_jacobian_centers": len(selected_centers),
                "median_n_centers_per_recording": float(np.median([r["finite_jacobian_center_count"] for r in selected_support])) if selected_support else math.nan,
                "median_underdetermined_center_count": float(np.median([r["underdetermined_center_count"] for r in selected_support])) if selected_support else math.nan,
                "fraction_centers_rank_4": float(np.mean([int(r["numerical_rank"]) == 4 for r in selected_centers])) if selected_centers else math.nan,
                "n_recordings_all_four_mnj_supported": len(all_four_supported),
                "median_time_reversal_relative_sign_error": float(np.median([float(r["median_relative_J_sign_reversal_error"]) for r in selected_reversal])) if selected_reversal else math.nan,
                "median_max_abs_existing_summary_reversal_difference": float(np.median([max(float(r[f"max_abs_difference_{metric}"]) for metric in MNJ_FIELDS) for r in selected_reversal])) if selected_reversal else math.nan,
            })
    return scalar_corr, position_assoc, matrix_summary


def algebraic_summary(centers: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cohort in COHORTS:
        for state in h1.STATES:
            selected = [row for row in centers if row["cohort"] == cohort and row["state"] == state]
            abs_values = np.asarray([row["pythagorean_abs_residual"] for row in selected], dtype=np.float64)
            rel_values = np.asarray([row["pythagorean_relative_residual"] for row in selected], dtype=np.float64)
            rows.append({
                "cohort": cohort,
                "state": state,
                "n_finite_centers": len(selected),
                "median_absolute_identity_residual": float(np.median(abs_values)) if len(abs_values) else math.nan,
                "maximum_absolute_identity_residual": float(np.max(abs_values)) if len(abs_values) else math.nan,
                "median_relative_identity_residual": float(np.median(rel_values)) if len(rel_values) else math.nan,
                "maximum_relative_identity_residual": float(np.max(rel_values)) if len(rel_values) else math.nan,
            })
    return rows


def counterexample() -> dict[str, Any]:
    j1 = np.diag([4.0, 3.0, 2.0, 1.0])
    j2 = np.diag([-4.0, 3.0, 2.0, 1.0])
    m1 = h2.matrix_mnj_metrics(j1)
    m2 = h2.matrix_mnj_metrics(j2)
    return {
        "status": "constructed_algebraic_illustration_not_dataset_observation",
        "J1": j1.tolist(),
        "J2": j2.tolist(),
        "matrix_frobenius_distance": float(np.linalg.norm(j1 - j2, ord="fro")),
        "J1_existing_summaries": m1,
        "J2_existing_summaries": m2,
        "summary_max_abs_difference": max(abs(m1[name] - m2[name]) for name in MNJ_FIELDS),
        "interpretation": "The scalar summaries discard sign/orientation information even though the matrices differ.",
    }


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    out_dir: Path,
    freeze: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    support: Sequence[Mapping[str, Any]],
    algebraic: Sequence[Mapping[str, Any]],
    correlations: Sequence[Mapping[str, Any]],
    predictability: Sequence[Mapping[str, Any]],
    structure: Sequence[Mapping[str, Any]],
    reversal: Sequence[Mapping[str, Any]],
    complete_counts: Mapping[str, int],
) -> None:
    lines = [
        "# MNJ-INFORMATION-001 results",
        "",
        f"Generated {utc_now()} from frozen protocol {Path(freeze['protocol']['path']).name}.",
        "",
        "## Scope and limitations",
        "",
        "This is an exploratory diagnostic on previously exposed ds005385 H2/H2R data. EC always preceded EO, so state and recording order are confounded. No EC/EO classifier or condition-tuned model was fitted in this experiment. All Jacobians were recomputed only from the saved 4-second PCV/TP/OI/SC trajectories with the frozen H2 kernels; no EDF was read.",
        "",
        "## Support",
        "",
        "| Cohort | State | Recordings with all four MNJ summaries supported | Median finite centers | Median underdetermined centers |",
        "|---|---|---:|---:|---:|",
    ]
    for row in structure:
        lines.append(f"| {row['cohort']} | {row['state']} | {int(row['n_recordings_all_four_mnj_supported'])}/100 | {row['median_n_centers_per_recording']:.0f} | {row['median_underdetermined_center_count']:.0f} |")

    lines += ["", "## A. Algebraic dependence", "", "The maximum relative numerical residual in the identity ||J||² = ||S||² + ||A||² was:"]
    for row in algebraic:
        lines.append(f"- {row['cohort']} {row['state']}: {row['maximum_relative_identity_residual']:.3g} across {row['n_finite_centers']} finite centers.")
    lines += [
        "",
        "Therefore the Frobenius, symmetric-Frobenius, and antisymmetric-Frobenius summaries are not three independent scalar measurements; one is exactly determined by the other two after squaring. Singular-value anisotropy is an additional scale-free quantity. The constructed example in synthetic_counterexample.json has different signed matrices but identical four existing summaries, illustrating information discarded by the scalar summaries.",
        "",
        "Recording-level pairwise Spearman correlations and pair counts among the four summaries are in summary_correlations.csv. These descriptive correlations do not establish construct redundancy.",
        "",
        "## B. Predictability from static measurements",
        "",
        "A fixed multi-output Ridge model (alpha=1.0; training-fold scaling; four predictors per output) predicts each recording-level MNJ summary from PCV, TP, OI, and SC. Both states from a participant stayed in the same outer fold. Out-of-fold R-squared intervals bootstrap participants and are conditional on the repeated-CV predictions.",
        "",
        "| Cohort | Target | n participants | Held-out R² [participant bootstrap 95% CI] |",
        "|---|---|---:|---:|",
    ]
    for row in predictability:
        if row.get("status") == "computed":
            lines.append(f"| {row['cohort']} | {row['target']} | {row['n_participants']} | {row['out_of_fold_r2']:.3f} [{row['ci95_low_conditional_on_repeated_cv']:.3f}, {row['ci95_high_conditional_on_repeated_cv']:.3f}] |")
    lines += [
        "",
        "This quantifies prediction by one low-complexity fixed linear model. High R² would indicate predictable overlap under this model, not mathematical redundancy; low R² would not prove independence.",
        "",
        "## C. Matrix structure and state-space position",
        "",
        "jacobian_centers.csv retains signed J entries, symmetric and antisymmetric components, singular values, complex eigenvalues, numerical rank, condition number, center time, and the four-coordinate state vector for every finite center. state_position_associations.csv summarizes within-recording rank correlations between each coordinate and each local MNJ summary; center windows are not treated as independent participants. Full distributions remain available in the center-level file.",
        "",
        "## D. Time reversal",
        "",
        "Every finite trajectory segment was reversed and relabeled on the same increasing 4-second grid. time_reversal_control.csv pairs the same coordinate rows and compares J_reverse with -J_original plus each scalar summary. This tests temporal direction under the frozen estimator; it does not cover every temporal-order surrogate.",
        "",
        "## Provisional diagnosis",
        "",
        "The current summaries have a confirmed algebraic redundancy and discard signed matrix orientation. The predictability and local-structure tables indicate whether the remaining scalar variation overlaps with static measurements in these cohorts. None of these diagnostics establishes that retained matrix information improves scientific inference. Treat the current limitation as a mixture until the output tables are considered together; retain the four-summary MNJ as a comparator while any challenger is developed.",
        "",
        "Complete participant counts for static predictability: " + ", ".join(f"{cohort}={complete_counts.get(cohort, 0)}/100" for cohort in COHORTS) + ".",
        "",
        "Output hashes and all frozen source hashes are recorded in run_manifest.json and mnj_information_freeze_v1_20261008.json.",
    ]
    (out_dir / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze(args: argparse.Namespace) -> None:
    out_dir: Path = args.out_dir
    freeze_path = args.freeze or (out_dir / FREEZE_NAME)
    freeze = verify_analysis_freeze(freeze_path, args.nmd_root)
    print("Verified MNJ analysis freeze and all 400 H2/H2R source hashes.", flush=True)
    projection, jacobian_module = h2.load_nmd_kernels(args.nmd_root)
    rows, centers, support, reversal, _trajectory_cache = extract_all(freeze, projection, jacobian_module)
    print(f"Re-estimated {len(centers)} finite original center Jacobians from {len(rows)} recordings.", flush=True)

    scalar_corr, position_assoc, matrix_summary = summarize_recordings(rows, centers, support, reversal)
    identity = algebraic_summary(centers)
    static_results, static_predictions, complete_counts = static_predictability(rows, freeze)
    _write_csv(out_dir / "recording_summaries.csv", rows)
    _write_csv(out_dir / "jacobian_centers.csv", centers)
    _write_csv(out_dir / "center_support.csv", support)
    _write_csv(out_dir / "algebraic_identity.csv", identity)
    _write_csv(out_dir / "summary_correlations.csv", scalar_corr)
    _write_csv(out_dir / "static_predictability.csv", static_results)
    _write_csv(out_dir / "static_predictability_oof.csv", static_predictions)
    _write_csv(out_dir / "state_position_associations.csv", position_assoc)
    _write_csv(out_dir / "matrix_structure_summary.csv", matrix_summary)
    _write_csv(out_dir / "time_reversal_control.csv", reversal)
    (out_dir / "synthetic_counterexample.json").write_text(json.dumps(counterexample(), indent=2, ensure_ascii=False, allow_nan=True) + "\n", encoding="utf-8")
    write_report(out_dir, freeze, rows, support, identity, scalar_corr, static_results, matrix_summary, reversal, complete_counts)

    output_files = sorted(path for path in out_dir.iterdir() if path.is_file() and path.name != "run_manifest.json")
    run_manifest = {
        "schema": "mnps_mnj_information_001_run_manifest.v1",
        "created_utc": utc_now(),
        "analysis_freeze": {"path": str(freeze_path), "sha256": sha256_file(freeze_path)},
        "recordings": len(rows),
        "finite_center_jacobians": len(centers),
        "complete_static_predictability_participants": complete_counts,
        "outputs": [{"path": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size} for path in output_files],
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Completed MNJ-INFORMATION-001: {out_dir / 'results.md'}", flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze_parser = subparsers.add_parser("freeze")
    freeze_parser.add_argument("--h2-freeze", type=Path, default=H2_FREEZE_DEFAULT)
    freeze_parser.add_argument("--h2r-freeze", type=Path, default=H2R_FREEZE_DEFAULT)
    freeze_parser.add_argument("--protocol", type=Path, default=PROTOCOL_DEFAULT)
    freeze_parser.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT)
    freeze_parser.add_argument("--nmd-root", type=Path, default=NMD_ROOT)
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT)
    analyze_parser.add_argument("--freeze", type=Path, default=None)
    analyze_parser.add_argument("--nmd-root", type=Path, default=NMD_ROOT)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "freeze":
        make_freeze(args)
    else:
        analyze(args)


if __name__ == "__main__":
    main()
