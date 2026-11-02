"""Run the frozen, exploratory V3-STRUCTURE-001 analysis on H1/H1R outputs.

The script consumes only the processed H1/H1R HDF5 files and the existing H1
analysis helper. It does not reopen source EDF files or fit MNPS estimators.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import platform
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import h5py
import numpy as np
import scipy
import sklearn
from scipy import stats

import analyze_h1 as h1


BENCH_DIR = Path(r"H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001")
ARTICLE_DIR = Path(__file__).resolve().parent
DEFAULT_OUT_DIR = Path(r"I:\AAA_PYTHON_REPOS_BACKUP\homepages\_mnps_v3_structure_001")
DEFAULT_PROTOCOL = ARTICLE_DIR / "v3_structure_protocol_v1_20261008.md"
DEFAULT_H1_FREEZE = BENCH_DIR / "h1_analysis_freeze_v3.json"
DEFAULT_H1R_FREEZE = BENCH_DIR / "h1r_analysis_freeze.json"
DEFAULT_H1_SELECTION = BENCH_DIR / "selection_manifest_outcome_blind.json"
DEFAULT_H1R_SELECTION = BENCH_DIR / "selection_manifest_bench_001r_outcome_blind.json"
FREEZE_NAME = "v3_structure_freeze_v1_20261008.json"

FAMILY_COLUMNS: dict[str, tuple[str, ...]] = {
    "PCV": ("PCV",),
    "TP": ("TP",),
    "AR_M3": tuple(h1.AR_FEATURES),
    "NIE": ("NIE",),
    "RD": ("RD",),
    "OI": ("OI",),
    "SC": ("SC",),
    "ED": ("ED",),
}
FAMILY_ORDER = tuple(FAMILY_COLUMNS)
SCOPE_ORDER = ("EyesClosed", "EyesOpen", "EO_minus_EC")
COHORTS = ("H1", "H1R")
N_BOOTSTRAP = 2000
BOOTSTRAP_SEED = 20261008


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


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _artifact_refs(value: Any, key_path: str = "") -> Iterable[tuple[str, Path, str]]:
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            yield key_path or "artifact", Path(value["path"]), str(value["sha256"])
        for key, child in value.items():
            yield from _artifact_refs(child, f"{key_path}.{key}" if key_path else str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _artifact_refs(child, f"{key_path}[{index}]")


def _verify_hash(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {label}: {path}")
    observed = sha256_file(path)
    if observed.lower() != expected.lower():
        raise ValueError(f"SHA256 mismatch for {label}: {path}; expected {expected}, got {observed}")


def verify_source_freeze(freeze_path: Path) -> dict[str, Any]:
    freeze = read_json(freeze_path)
    refs = list(_artifact_refs(freeze))
    seen: set[tuple[str, str]] = set()
    for label, path, expected in refs:
        identity = (str(path).lower(), expected.lower())
        if identity in seen:
            continue
        seen.add(identity)
        _verify_hash(path, expected, f"{freeze_path.name}:{label}")
    inputs = freeze.get("input_h5_sha256")
    if not isinstance(inputs, list) or len(inputs) != 200:
        raise ValueError(f"{freeze_path} must bind exactly 200 processed HDF5 inputs")
    return freeze


def selection_subjects(path: Path) -> list[str]:
    manifest = read_json(path)
    subjects = manifest.get("selection", {}).get("subjects")
    if not isinstance(subjects, list) or len(subjects) != 100:
        raise ValueError(f"Selection manifest must contain exactly 100 subjects: {path}")
    result = [str(item) for item in subjects]
    if len(set(result)) != 100:
        raise ValueError(f"Selection manifest contains duplicate subjects: {path}")
    return result


def make_freeze(args: argparse.Namespace) -> Path:
    out_dir: Path = args.out_dir
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty; preserving existing contents: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    h1_freeze = verify_source_freeze(args.h1_freeze)
    h1r_freeze = verify_source_freeze(args.h1r_freeze)
    h1_subjects = selection_subjects(args.h1_selection)
    h1r_subjects = selection_subjects(args.h1r_selection)
    if set(h1_subjects) & set(h1r_subjects):
        raise ValueError("Frozen H1 and H1R participant sets overlap")

    def input_map(freeze: Mapping[str, Any], cohort: str, subjects: Sequence[str]) -> list[dict[str, str]]:
        rows = freeze["input_h5_sha256"]
        if len(rows) != 200:
            raise ValueError(f"{cohort} freeze did not contain 200 HDF5 hashes")
        result = [{"cohort": cohort, "path": str(row["path"]), "sha256": str(row["sha256"])} for row in rows]
        paths = [Path(row["path"]) for row in result]
        if len({path.resolve().as_posix().lower() for path in paths}) != 200:
            raise ValueError(f"Duplicate HDF5 input paths in {cohort}")
        path_subjects = {
            match.group(1)
            for path in paths
            if (match := re.match(r"(sub-\d+)_ses-1_", path.name, flags=re.IGNORECASE))
        }
        if len(path_subjects) != 100 or path_subjects != set(subjects):
            raise ValueError(f"{cohort} HDF5 input subject folders do not match its selection manifest")
        return result

    inputs = input_map(h1_freeze, "H1", h1_subjects) + input_map(h1r_freeze, "H1R", h1r_subjects)
    # Source-freeze verification above includes the exact hash check for each HDF5.
    dependencies: dict[str, dict[str, str]] = {}

    def bind(label: str, path: Path) -> None:
        dependencies[label] = {"path": str(path), "sha256": sha256_file(path)}

    for label, path in (
        ("source_h1_freeze", args.h1_freeze),
        ("source_h1r_freeze", args.h1r_freeze),
        ("h1_selection", args.h1_selection),
        ("h1r_selection", args.h1r_selection),
        ("protocol", args.protocol),
        ("h1_analysis_helper", ARTICLE_DIR / "analyze_h1.py"),
        ("h1_analysis_test", ARTICLE_DIR / "test_analyze_h1.py"),
        ("structure_analysis_script", Path(__file__).resolve()),
    ):
        bind(label, path)

    for cohort, freeze in (("H1", h1_freeze), ("H1R", h1r_freeze)):
        for ref_name in ("execution_manifest", "amendment_1", "h1_config"):
            ref = freeze.get(ref_name)
            if isinstance(ref, dict) and "path" in ref and "sha256" in ref:
                path = Path(ref["path"])
                _verify_hash(path, str(ref["sha256"]), f"{cohort} {ref_name}")
                dependencies[f"{cohort}_{ref_name}"] = {"path": str(path), "sha256": str(ref["sha256"])}
        for code_name, ref in freeze.get("nmd_pipeline_code", {}).items():
            path = Path(ref["path"])
            _verify_hash(path, str(ref["sha256"]), f"{cohort} NMD code {code_name}")
            dependencies.setdefault(f"NMD_{code_name}", {"path": str(path), "sha256": str(ref["sha256"])})

    software = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "h5py": h5py.__version__,
    }
    freeze_payload = {
        "schema": "mnps_v3_structure_001_freeze.v1",
        "created_utc": utc_now(),
        "protocol_status": "exploratory_and_precalculation_frozen",
        "protocol": dependencies["protocol"],
        "sources": {
            "H1": {"freeze": dependencies["source_h1_freeze"], "subjects": h1_subjects},
            "H1R": {"freeze": dependencies["source_h1r_freeze"], "subjects": h1r_subjects},
        },
        "dependencies": dependencies,
        "inputs": inputs,
        "analysis_contract": {
            "features": list(h1.H1_V3_FEATURES),
            "families": {key: list(value) for key, value in FAMILY_COLUMNS.items()},
            "states": list(h1.STATES),
            "supported_window_minimum_seconds": h1.MIN_SUPPORTED_SEC,
            "complete_cohort_minimum": h1.MIN_COHORT,
            "minimum_assessed_subjects": 80,
            "outer_repeats": h1.OUTER_REPEATS,
            "outer_folds": h1.OUTER_FOLDS,
            "inner_folds": h1.INNER_FOLDS,
            "C_grid": list(h1.C_GRID),
            "bootstrap_draws": N_BOOTSTRAP,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "scope_order": list(SCOPE_ORDER),
        },
        "software": software,
        "input_validation": "all source-freeze artifact references and all 400 HDF5 SHA256 hashes matched before analysis",
    }
    out_path = out_dir / FREEZE_NAME
    out_path.write_text(json.dumps(freeze_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Created frozen analysis manifest: {out_path}")
    print(f"Verified input files: {len(inputs)}; participants H1={len(h1_subjects)}, H1R={len(h1r_subjects)}")
    print(f"Analysis script SHA256: {dependencies['structure_analysis_script']['sha256']}")
    return out_path


def verify_analysis_freeze(freeze_path: Path) -> dict[str, Any]:
    freeze = read_json(freeze_path)
    if freeze.get("schema") != "mnps_v3_structure_001_freeze.v1":
        raise ValueError("Unexpected V3-STRUCTURE freeze schema")
    for label, ref in freeze["dependencies"].items():
        _verify_hash(Path(ref["path"]), str(ref["sha256"]), label)
    if len(freeze["inputs"]) != 400:
        raise ValueError("Analysis freeze must bind exactly 400 HDF5 inputs")
    for row in freeze["inputs"]:
        _verify_hash(Path(row["path"]), str(row["sha256"]), f"{row['cohort']} HDF5")
    return freeze


def extract_features(freeze: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows: list[dict[str, Any]] = []
    all_support: list[dict[str, Any]] = []
    for row in freeze["inputs"]:
        path = Path(row["path"])
        coverage: list[dict[str, Any]] = []
        with h5py.File(path, "r") as h5:
            raw_file = h1._row_source_file(h5)
            match = h1.FILE_PATTERN.search(Path(raw_file).name)
            if not match:
                raise ValueError(f"HDF5 is not a selected session-1 EyesClosed/EyesOpen acq-pre file: {path}")
            subject = match.group("subject")
            state = "EyesClosed" if match.group("state").lower() == "eyesclosed" else "EyesOpen"
            features = h1._get_v3_features(h5, subject=subject, state=state, coverage_rows=coverage)
        if len(features) != 16 or set(features) != set(h1.H1_V3_FEATURES):
            raise ValueError(f"Unexpected v3.1 feature set or width in {path}")
        # Keep the canonical frozen order, including the contiguous nine-column
        # M3 block, even though the legacy helper inserts scalar keys first.
        features = {name: float(features[name]) for name in h1.H1_V3_FEATURES}
        expected_subjects = set(freeze["sources"][row["cohort"]]["subjects"])
        if subject not in expected_subjects:
            raise ValueError(f"Non-selected participant in frozen input: {subject}")
        all_rows.append({
            "cohort": row["cohort"],
            "subject": subject,
            "state": state,
            "source_h5": str(path),
            "source_h5_sha256": row["sha256"],
            **features,
        })
        for item in coverage:
            copy = dict(item)
            copy["cohort"] = row["cohort"]
            copy["source_h5"] = str(path)
            copy["family"] = "AR_M3" if copy["feature"] == "AR_vector" else copy["feature"]
            all_support.append(copy)

    by_key = {(row["cohort"], row["subject"], row["state"]): row for row in all_rows}
    if len(by_key) != len(all_rows) or len(all_rows) != 400:
        raise ValueError("Duplicate or missing processed recording keys")
    for cohort in COHORTS:
        subjects = freeze["sources"][cohort]["subjects"]
        expected = {(cohort, subject, state) for subject in subjects for state in h1.STATES}
        observed = {key for key in by_key if key[0] == cohort}
        if expected != observed:
            raise ValueError(f"{cohort} processed recordings do not form exact EC/EO pairs")
    return all_rows, all_support


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def data_matrix(rows: Sequence[Mapping[str, Any]], features: Sequence[str]) -> np.ndarray:
    return np.asarray([[row[name] for name in features] for row in rows], dtype=np.float64)


def scoped_data(
    rows: Sequence[Mapping[str, Any]], cohort: str, scope: str, features: Sequence[str],
) -> tuple[list[str], np.ndarray]:
    selected = [row for row in rows if row["cohort"] == cohort]
    by_pair = {(str(row["subject"]), str(row["state"])): row for row in selected}
    subjects = list(dict.fromkeys(str(row["subject"]) for row in selected))
    if scope in h1.STATES:
        scope_rows = [by_pair[(subject, scope)] for subject in subjects]
        return subjects, data_matrix(scope_rows, features)
    if scope != "EO_minus_EC":
        raise ValueError(scope)
    differences = []
    for subject in subjects:
        closed = data_matrix([by_pair[(subject, "EyesClosed")]], features)[0]
        opened = data_matrix([by_pair[(subject, "EyesOpen")]], features)[0]
        differences.append(opened - closed)
    return subjects, np.asarray(differences, dtype=np.float64)


def describe_structure(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    correlations: list[dict[str, Any]] = []
    spectra: list[dict[str, Any]] = []
    descriptives: list[dict[str, Any]] = []
    names = list(h1.H1_V3_FEATURES)
    for cohort in COHORTS:
        for scope in SCOPE_ORDER:
            subjects, matrix = scoped_data(rows, cohort, scope, names)
            for column, name in enumerate(names):
                values = matrix[:, column]
                finite = values[np.isfinite(values)]
                descriptives.append({
                    "cohort": cohort,
                    "scope": scope,
                    "feature": name,
                    "n": int(finite.size),
                    "mean": float(np.mean(finite)) if finite.size else math.nan,
                    "sd": float(np.std(finite, ddof=1)) if finite.size > 1 else math.nan,
                    "median": float(np.median(finite)) if finite.size else math.nan,
                    "p25": float(np.percentile(finite, 25)) if finite.size else math.nan,
                    "p75": float(np.percentile(finite, 75)) if finite.size else math.nan,
                    "iqr": float(np.percentile(finite, 75) - np.percentile(finite, 25)) if finite.size else math.nan,
                })

            for left_index, left in enumerate(names):
                for right_index in range(left_index, len(names)):
                    right = names[right_index]
                    pair = matrix[:, [left_index, right_index]]
                    keep = np.isfinite(pair).all(axis=1)
                    n_pair = int(keep.sum())
                    rho = math.nan
                    if n_pair >= 2 and np.ptp(pair[keep, 0]) > 0 and np.ptp(pair[keep, 1]) > 0:
                        rho = float(stats.spearmanr(pair[keep, 0], pair[keep, 1]).statistic)
                    correlations.append({
                        "cohort": cohort,
                        "scope": scope,
                        "feature_left": left,
                        "feature_right": right,
                        "n_pair": n_pair,
                        "spearman_rho": rho,
                    })

            complete = np.isfinite(matrix).all(axis=1)
            x = matrix[complete]
            n_complete = int(len(x))
            if n_complete >= 2:
                means = np.mean(x, axis=0)
                standard_deviations = np.std(x, axis=0, ddof=1)
                zero_variance = [name for name, value in zip(names, standard_deviations, strict=True) if value == 0]
                safe_scale = np.where(standard_deviations > 0, standard_deviations, 1.0)
                z = (x - means) / safe_scale
                if zero_variance:
                    z[:, [names.index(name) for name in zero_variance]] = 0.0
                covariance = z.T @ z / (n_complete - 1)
                eigenvalues = np.linalg.eigvalsh(covariance)[::-1]
                eigenvalues = np.maximum(eigenvalues, 0.0)
                total = float(np.sum(eigenvalues))
                fractions = eigenvalues / total if total > 0 else np.full_like(eigenvalues, math.nan)
                effective_rank = float(total * total / np.sum(eigenvalues ** 2)) if np.sum(eigenvalues ** 2) > 0 else math.nan
                cumulative = np.cumsum(fractions) if np.isfinite(fractions).all() else np.full_like(fractions, math.nan)
                for rank, (value, fraction, cumulative_fraction) in enumerate(zip(eigenvalues, fractions, cumulative, strict=True), start=1):
                    spectra.append({
                        "cohort": cohort,
                        "scope": scope,
                        "n_complete": n_complete,
                        "component_rank": rank,
                        "eigenvalue": float(value),
                        "explained_fraction": float(fraction),
                        "cumulative_fraction": float(cumulative_fraction),
                        "participation_ratio_effective_rank": effective_rank,
                        "zero_variance_columns_json": json.dumps(zero_variance),
                    })
            else:
                spectra.append({
                    "cohort": cohort,
                    "scope": scope,
                    "n_complete": n_complete,
                    "component_rank": None,
                    "eigenvalue": math.nan,
                    "explained_fraction": math.nan,
                    "cumulative_fraction": math.nan,
                    "participation_ratio_effective_rank": math.nan,
                    "zero_variance_columns_json": "[]",
                })
    return correlations, spectra, descriptives


def feature_sets() -> dict[str, tuple[str, ...]]:
    all_features = tuple(h1.H1_V3_FEATURES)
    result: dict[str, tuple[str, ...]] = {"all_16": all_features}
    for family in FAMILY_ORDER:
        result[f"single_{family}"] = FAMILY_COLUMNS[family]
    for omitted in FAMILY_ORDER:
        result[f"leave_out_{omitted}"] = tuple(
            name for family in FAMILY_ORDER if family != omitted for name in FAMILY_COLUMNS[family]
        )
    if len(result) != 17:
        raise AssertionError("Expected 17 frozen feature-set arms")
    return result


def run_cv(
    rows: Sequence[Mapping[str, Any]], freeze: Mapping[str, Any], out_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    metrics: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    choices_rows: list[dict[str, Any]] = []
    complete_counts: dict[str, int] = {}
    sets = feature_sets()

    for cohort in COHORTS:
        selected_subjects = list(freeze["sources"][cohort]["subjects"])
        by_key = {(row["subject"], row["state"]): row for row in rows if row["cohort"] == cohort}
        complete_subjects: list[str] = []
        for subject in selected_subjects:
            pair = [by_key[(subject, state)] for state in h1.STATES]
            if all(np.isfinite(data_matrix(pair, h1.H1_V3_FEATURES)).all(axis=1)):
                complete_subjects.append(subject)
        complete_counts[cohort] = len(complete_subjects)
        print(f"{cohort}: {len(complete_subjects)}/100 participants complete across all 16 features and both states")
        if len(complete_subjects) < 80:
            metrics.append({"cohort": cohort, "arm": "ALL", "n_participants": len(complete_subjects), "status": "skipped_below_80_complete"})
            continue

        ordered_rows = [by_key[(subject, state)] for subject in complete_subjects for state in h1.STATES]
        labels = np.tile(np.asarray([0, 1], dtype=np.int8), len(complete_subjects))
        groups = np.repeat(np.asarray(complete_subjects), 2)
        schedule = h1.make_split_schedule(complete_subjects)
        outputs: dict[str, dict[str, Any]] = {}
        for arm_index, (arm, features) in enumerate(sets.items(), start=1):
            matrix = data_matrix(ordered_rows, features)
            if not np.isfinite(matrix).all():
                raise ValueError(f"Unexpected missing feature in complete-case CV matrix: {cohort}/{arm}")
            print(f"{cohort}: CV arm {arm_index}/17: {arm} ({len(features)} columns)", flush=True)
            result = h1.nested_grouped_cv(matrix, labels, groups, schedule)
            outputs[arm] = result
            for choice in result["c_choices"]:
                choices_rows.append({"cohort": cohort, "arm": arm, **choice})
            for row_index, row in enumerate(ordered_rows):
                predictions.append({
                    "cohort": cohort,
                    "arm": arm,
                    "subject": row["subject"],
                    "state": row["state"],
                    "true_label": int(labels[row_index]),
                    "mean_oof_probability_EO": float(result["mean_probability"][row_index]),
                    "participant_paired_auc": float(result["participant_auc"][row["subject"]]),
                })
            participant_scores = result["participant_auc"]
            score_values = [float(participant_scores[subject]) for subject in complete_subjects]
            ci_low, ci_high = h1.paired_bootstrap_interval(
                score_values, n_draws=N_BOOTSTRAP, seed=BOOTSTRAP_SEED,
            )
            metrics.append({
                "cohort": cohort,
                "arm": arm,
                "n_participants": len(complete_subjects),
                "n_features": len(features),
                "features_json": json.dumps(list(features)),
                "status": "computed",
                "participant_paired_auc": float(result["paired_auc"]),
                "auc_ci95_low": ci_low,
                "auc_ci95_high": ci_high,
                "balanced_accuracy": float(result["balanced_accuracy"]),
                "sensitivity": float(result["sensitivity"]),
                "specificity": float(result["specificity"]),
                "paired_auc_delta_vs_all_16": 0.0 if arm == "all_16" else math.nan,
                "delta_ci95_low": 0.0 if arm == "all_16" else math.nan,
                "delta_ci95_high": 0.0 if arm == "all_16" else math.nan,
            })

        full_scores = outputs["all_16"]["participant_auc"]
        metric_by_arm = {row["arm"]: row for row in metrics if row["cohort"] == cohort and row.get("status") == "computed"}
        for arm in sets:
            if arm == "all_16" or arm not in outputs:
                continue
            arm_scores = outputs[arm]["participant_auc"]
            differences = [float(arm_scores[subject] - full_scores[subject]) for subject in complete_subjects]
            delta_ci = h1.paired_bootstrap_interval(differences, n_draws=N_BOOTSTRAP, seed=BOOTSTRAP_SEED)
            metric_by_arm[arm]["paired_auc_delta_vs_all_16"] = float(np.mean(differences))
            metric_by_arm[arm]["delta_ci95_low"] = delta_ci[0]
            metric_by_arm[arm]["delta_ci95_high"] = delta_ci[1]

    return metrics, predictions, choices_rows, complete_counts


def write_report(
    out_dir: Path,
    freeze: Mapping[str, Any],
    support: Sequence[Mapping[str, Any]],
    spectra: Sequence[Mapping[str, Any]],
    metrics: Sequence[Mapping[str, Any]],
    complete_counts: Mapping[str, int],
) -> None:
    coverage_summary: list[dict[str, Any]] = []
    groups: dict[tuple[str, str, str], list[Mapping[str, Any]]] = {}
    for row in support:
        groups.setdefault((row["cohort"], row["family"], row["state"]), []).append(row)
    for (cohort, family, state), rows in sorted(groups.items()):
        passing = sum(bool(row["support_pass"]) for row in rows)
        coverage_summary.append({
            "cohort": cohort,
            "family": family,
            "feature": rows[0]["feature"],
            "state": state,
            "n_recordings": len(rows),
            "n_support_pass": passing,
            "support_pass_fraction": passing / len(rows) if rows else math.nan,
            "median_supported_seconds": float(np.median([row["supported_seconds"] for row in rows])) if rows else math.nan,
            "median_finite_windows": float(np.median([row["finite_window_count"] for row in rows])) if rows else math.nan,
        })
    _write_csv(out_dir / "support_coverage.csv", coverage_summary)

    lines = [
        "# V3-STRUCTURE-001 results",
        "",
        f"Generated from frozen protocol `{Path(freeze['protocol']['path']).name}` on {utc_now()}.",
        "",
        "## Scope and interpretation",
        "",
        "This is an exploratory, descriptive analysis of the already exposed ds005385 H1/H1R cohorts. It describes recorded EC-versus-EO state, not a causal eye-closure effect; EC always preceded EO. Correlations and feature-set ablations do not establish measurement redundancy, construct validity, or prospective performance.",
        "",
        "Only full v3.1 20-second H1/H1R exports were read. The ordered nine-column AR/M3 vector was retained as one family. Values are medians of finite, computed, valid windows only when unique support reaches 60 seconds; unsupported values remain missing. No EDFs were reprocessed and no values were imputed.",
        "",
        "## Participant support",
        "",
        "| Cohort | Complete across 16 features and both states | CV status |",
        "|---|---:|---|",
    ]
    for cohort in COHORTS:
        count = complete_counts.get(cohort, 0)
        status = "computed" if count >= 80 else "coverage only (<80)"
        lines.append(f"| {cohort} | {count}/100 | {status} |")

    lines += ["", "## Repeated nested-CV summary", "", "| Cohort | Feature set | n | Paired AUC [participant bootstrap 95% CI] | Δ AUC vs all 16 [95% CI] |", "|---|---|---:|---:|---:|"]
    for cohort in COHORTS:
        for row in metrics:
            if row.get("cohort") != cohort or row.get("status") != "computed":
                continue
            lines.append(
                f"| {cohort} | {row['arm']} | {row['n_participants']} | "
                f"{row['participant_paired_auc']:.3f} [{row['auc_ci95_low']:.3f}, {row['auc_ci95_high']:.3f}] | "
                f"{row['paired_auc_delta_vs_all_16']:.3f} [{row['delta_ci95_low']:.3f}, {row['delta_ci95_high']:.3f}] |"
            )

    lines += [
        "",
        "## Structure outputs",
        "",
        "`correlations_spearman.csv` contains pairwise-complete Spearman correlations and pair counts for EC, EO, and paired EO−EC. `covariance_spectrum.csv` contains eigenvalues and explained fractions from standardized 16-column complete cases, with the participation-ratio effective rank. `descriptives.csv` contains participant-level means, standard deviations, medians, and IQRs. `support_coverage.csv` reports support before any complete-case restriction.",
        "",
        "## Classification outputs",
        "",
        "`cv_metrics.csv` reports the full 16-column set, eight single-family sets, and eight leave-one-family-out sets. All arms within a cohort reuse one participant-complete set and the same frozen grouped nested split schedule. AUC intervals resample participants from the repeated-CV participant scores; paired delta intervals resample the within-participant score differences. They are conditional on these fitted repeated-CV predictions and are descriptive, unadjusted intervals.",
        "",
        "`cv_predictions.csv` contains mean repeated out-of-fold probabilities and participant-paired AUC scores. `cv_c_choices.csv` retains selected C for each repeat and outer fold. The complete input hashes and dependency hashes are in the analysis freeze; output hashes are in `run_manifest.json`.",
        "",
        "## Limits",
        "",
        "These already exposed cohorts do not provide independent prospective validation. The reported structure is conditional on the frozen v3.1 realization, its 20-second grid, its support rule, and complete-case availability. Matching correlations or reduced AUC after ablation is not sufficient evidence that two families measure the same construct or can be substituted.",
    ]
    (out_dir / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze(args: argparse.Namespace) -> None:
    out_dir: Path = args.out_dir
    freeze_path = args.freeze or (out_dir / FREEZE_NAME)
    freeze = verify_analysis_freeze(freeze_path)
    print("Verified analysis freeze dependencies and all 400 source HDF5 hashes.", flush=True)
    rows, support = extract_features(freeze)
    _write_csv(out_dir / "recording_features.csv", rows)
    _write_csv(out_dir / "feature_support.csv", support)
    print(f"Extracted v3.1 features from {len(rows)} HDF5 recordings.", flush=True)

    correlations, spectra, descriptives = describe_structure(rows)
    _write_csv(out_dir / "correlations_spearman.csv", correlations)
    _write_csv(out_dir / "covariance_spectrum.csv", spectra)
    _write_csv(out_dir / "descriptives.csv", descriptives)
    print("Saved correlations, spectra, descriptive summaries, and support.", flush=True)

    metrics, predictions, choices, complete_counts = run_cv(rows, freeze, out_dir)
    _write_csv(out_dir / "cv_metrics.csv", metrics)
    _write_csv(out_dir / "cv_predictions.csv", predictions)
    _write_csv(out_dir / "cv_c_choices.csv", choices)
    write_report(out_dir, freeze, support, spectra, metrics, complete_counts)

    output_files = sorted(path for path in out_dir.iterdir() if path.is_file() and path.name != "run_manifest.json")
    run_manifest = {
        "schema": "mnps_v3_structure_001_run_manifest.v1",
        "created_utc": utc_now(),
        "analysis_freeze": {"path": str(freeze_path), "sha256": sha256_file(freeze_path)},
        "source_recordings_extracted": len(rows),
        "complete_subjects_by_cohort": complete_counts,
        "outputs": [{"path": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size} for path in output_files],
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Completed V3-STRUCTURE-001; results: {out_dir / 'results.md'}", flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze_parser = subparsers.add_parser("freeze", help="verify and write the pre-analysis dependency/input freeze")
    freeze_parser.add_argument("--h1-freeze", type=Path, default=DEFAULT_H1_FREEZE)
    freeze_parser.add_argument("--h1r-freeze", type=Path, default=DEFAULT_H1R_FREEZE)
    freeze_parser.add_argument("--h1-selection", type=Path, default=DEFAULT_H1_SELECTION)
    freeze_parser.add_argument("--h1r-selection", type=Path, default=DEFAULT_H1R_SELECTION)
    freeze_parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    freeze_parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    analyze_parser = subparsers.add_parser("analyze", help="run the frozen descriptive structure and CV analysis")
    analyze_parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    analyze_parser.add_argument("--freeze", type=Path, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "freeze":
        make_freeze(args)
    elif args.command == "analyze":
        analyze(args)
    else:
        raise AssertionError(args.command)


if __name__ == "__main__":
    main()
