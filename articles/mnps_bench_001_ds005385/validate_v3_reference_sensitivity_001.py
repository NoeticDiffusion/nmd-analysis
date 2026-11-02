from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

ARTICLE = Path(r"J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385")
OUT = ARTICLE / "outputs" / "v3_reference_sensitivity_001_mne_pilot_v1_20261009"
SUMMARY = OUT / "validation_summary.json"
EXPECTED_CANDIDATES = {"M1", "M2", "M3", "D1", "D3", "E1", "E2", "E3"}
SCALAR_NAMES = {"M1": "PCV", "M2": "TP", "D1": "NIE", "D3": "RD", "E1": "OI", "E2": "SC", "E3": "ED"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expand_components(candidate: str, value: Any) -> dict[str, float] | None:
    if value is None:
        return None
    if candidate == "M3":
        if not isinstance(value, list) or len(value) != 9:
            return None
        parts = {f"AR_pair_{i:02d}": float(v) for i, v in enumerate(value, 1)}
    else:
        parts = {SCALAR_NAMES[candidate]: float(value)}
    return parts if all(math.isfinite(v) for v in parts.values()) else None


def main() -> None:
    manifest_path = OUT / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    input_manifest = json.loads((OUT / "input_manifest.json").read_text(encoding="utf-8"))
    anchor_map = pd.read_csv(OUT / "anchor_map.csv")
    measurements = pd.read_csv(OUT / "reference_measurements.csv")
    paired = pd.read_csv(OUT / "paired_anchor_differences.csv")
    participant_summary = pd.read_csv(OUT / "reference_sensitivity_by_participant.csv")

    checks: dict[str, bool] = {}
    checks["protocol_estimator_runner_hashes_match"] = (
        sha256(Path(manifest["protocol_path"])) == manifest["protocol_sha256"]
        and sha256(Path(manifest["estimator_path"])) == manifest["estimator_sha256"]
        and sha256(Path(manifest["runner_path"])) == manifest["runner_sha256"]
    )
    output_hash_checks = {
        name: sha256(OUT / name) == expected
        for name, expected in manifest["outputs_sha256"].items() if name != SUMMARY.name
    }
    checks["run_output_hashes_match"] = bool(output_hash_checks) and all(output_hash_checks.values())
    expected_anchor_counts = {"sub-032": 10, "sub-033": 8, "sub-034": 10, "sub-035": 12, "sub-036": 11, "sub-038": 10}
    anchor_counts = anchor_map.groupby("subject").size().to_dict()
    checks["frozen_anchor_map_exact"] = anchor_counts == expected_anchor_counts and len(anchor_map) == 61
    checks["all_anchor_windows_fit_mne_output"] = all(
        int(row.window_start_sample_250hz) + 20 * 250 <= int(input_manifest["participants"][row.subject]["mne_resampled_sample_count_250hz"])
        for row in anchor_map.itertuples(index=False)
    )

    expected_measurements = 61 * 2 * 2 * 4 * 8
    measurement_keys = ["subject", "surface_id", "reference", "anchor_index", "duration_sec", "candidate_id"]
    checks["complete_unique_measurement_grid"] = (
        len(measurements) == expected_measurements
        and measurements[measurement_keys].drop_duplicates().shape[0] == expected_measurements
        and set(measurements["candidate_id"]) == EXPECTED_CANDIDATES
        and set(measurements["reference"]) == {"average", "linked_mastoid"}
        and set(measurements["surface_id"]) == {"core19", "native63"}
    )
    checks["all_rows_computed_valid_unqualified"] = (
        measurements["computed"].astype(bool).all()
        and measurements["valid"].astype(bool).all()
        and not measurements["qualified"].astype(bool).any()
        and manifest["all_values_unqualified"] is True
    )
    checks["bad_interval_status_retained_unknown"] = measurements["bad_interval_free"].isna().all() and manifest["bad_interval_free"] == "unknown"

    numeric_values_finite = True
    component_map: dict[tuple[Any, ...], dict[str, dict[str, float]]] = {}
    for row in measurements.itertuples(index=False):
        value = json.loads(row.value_json)
        components = expand_components(row.candidate_id, value)
        if value is None:
            numeric_values_finite = False
            continue
        if isinstance(value, list):
            numeric_values_finite = numeric_values_finite and all(math.isfinite(float(v)) for v in value)
        else:
            numeric_values_finite = numeric_values_finite and math.isfinite(float(value))
        if components is not None:
            key = (row.subject, row.surface_id, int(row.anchor_index), int(row.duration_sec), row.candidate_id)
            component_map.setdefault(key, {})[row.reference] = components
    checks["serialized_values_finite"] = numeric_values_finite

    comparison_keys = ["subject", "surface_id", "anchor_index", "duration_sec", "candidate_id"]
    metadata_columns = ["window_start_sample_250hz", "window_start_sec", "sample_count", "channel_count", "channel_order_sha256", "channel_set_sha256", "source_set_sha256"]
    pair_metadata_mismatches = 0
    reference_coverage_errors = 0
    for key, group in measurements.groupby(comparison_keys, sort=False):
        if set(group["reference"]) != {"average", "linked_mastoid"}:
            reference_coverage_errors += 1
        if any(group[column].nunique(dropna=False) != 1 for column in metadata_columns):
            pair_metadata_mismatches += 1
        if group["reference_set_sha256"].nunique(dropna=False) != 2:
            pair_metadata_mismatches += 1
    checks["paired_window_channel_and_reference_metadata_match"] = pair_metadata_mismatches == 0 and reference_coverage_errors == 0

    expected_paired_rows = 7 * 61 * 2 * 4 + 9 * 61 * 2
    paired_keys = ["subject", "surface_id", "anchor_index", "duration_sec", "candidate_id", "component"]
    checks["complete_unique_paired_components"] = (
        len(paired) == expected_paired_rows == 4514
        and not paired.duplicated(paired_keys).any()
        and set(paired["average_reference_set_sha256"]) != set(paired["linked_reference_set_sha256"])
        and set(paired.loc[paired["candidate_id"].eq("M3"), "duration_sec"]) == {20}
    )
    paired_value_errors = 0
    for row in paired.itertuples(index=False):
        key = (row.subject, row.surface_id, int(row.anchor_index), int(row.duration_sec), row.candidate_id)
        variants = component_map.get(key, {})
        avg = variants.get("average", {}).get(row.component)
        linked = variants.get("linked_mastoid", {}).get(row.component)
        if avg is None or linked is None:
            paired_value_errors += 1
            continue
        if not math.isclose(float(row.average_reference_value), avg, rel_tol=1e-12, abs_tol=1e-12):
            paired_value_errors += 1
        if not math.isclose(float(row.linked_mastoid_value), linked, rel_tol=1e-12, abs_tol=1e-12):
            paired_value_errors += 1
        if not math.isclose(float(row.signed_difference_average_minus_linked), avg - linked, rel_tol=1e-12, abs_tol=1e-12):
            paired_value_errors += 1
        if not math.isclose(float(row.absolute_difference), abs(avg - linked), rel_tol=1e-12, abs_tol=1e-12):
            paired_value_errors += 1
    checks["paired_values_recompute_from_measurement_table"] = paired_value_errors == 0
    checks["participant_summary_rows_complete"] = len(participant_summary) == 444 and set(participant_summary["paired_anchor_count"]) == {8, 10, 11, 12}

    sensitivity: dict[str, Any] = {}
    for surface in ("core19", "native63"):
        sensitivity[surface] = {}
        subset = participant_summary[participant_summary["surface_id"].eq(surface)]
        for (candidate, duration, component), group in subset.groupby(["candidate_id", "duration_sec", "component"], sort=True):
            values = group["median_absolute_difference"].to_numpy(dtype=float)
            sensitivity[surface].setdefault(candidate, {})[str(int(duration)) + "s/" + component] = {
                "median_of_participant_medians": float(pd.Series(values).median()),
                "participant_median_min": float(values.min()),
                "participant_median_max": float(values.max()),
                "participant_count": int(values.size),
            }

    sample_deltas = {
        subject: int(record["mne_minus_v002_sample_count"])
        for subject, record in input_manifest["participants"].items()
    }
    checks["mne_and_v002_branches_not_pooled_terminal_sample_delta_recorded"] = set(sample_deltas.values()) == {-1}
    checks["six_subjects_and_no_task_or_classifier_use"] = (
        set(manifest["participants"]) == set(expected_anchor_counts)
        and manifest["task_labels_or_classifier_used"] is False
        and manifest["independent_unit"].startswith("participant")
    )

    summary = {
        "schema": "v3_reference_sensitivity_001_validation.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "counts": {
            "participants": len(expected_anchor_counts),
            "anchors": len(anchor_map),
            "measurement_rows": len(measurements),
            "paired_component_rows": len(paired),
            "participant_summary_rows": len(participant_summary),
            "computed_rows": int(measurements["computed"].astype(bool).sum()),
            "valid_rows": int(measurements["valid"].astype(bool).sum()),
            "qualified_rows": int(measurements["qualified"].astype(bool).sum()),
            "pair_metadata_mismatches": pair_metadata_mismatches,
            "reference_coverage_errors": reference_coverage_errors,
            "paired_value_errors": paired_value_errors,
        },
        "anchor_count_by_participant": {str(k): int(v) for k, v in anchor_counts.items()},
        "mne_minus_v002_sample_count_by_participant": sample_deltas,
        "core19_and_native63_reference_sensitivity": sensitivity,
        "source_run_manifest_sha256_before_validation": sha256(manifest_path),
        "outputs_sha256_verified_before_validation": output_hash_checks,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    manifest["post_run_validation"] = {
        "status": summary["status"],
        "path": str(SUMMARY),
        "script_path": str(Path(__file__).resolve()),
        "script_sha256": sha256(Path(__file__).resolve()),
        "check_count": len(checks),
        "failed_checks": summary["failed_checks"],
    }
    manifest["outputs_sha256"][SUMMARY.name] = sha256(SUMMARY)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "checks": len(checks), "failed_checks": summary["failed_checks"], "summary": str(SUMMARY)}, indent=2))
    if summary["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
