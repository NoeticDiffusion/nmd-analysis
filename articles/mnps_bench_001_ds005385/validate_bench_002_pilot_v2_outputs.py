from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ARTICLE_ROOT = Path(r"J:\repos\nmd-analysis\articles\mnps_bench_001_ds005385")
OLD = ARTICLE_ROOT / "outputs" / "bench_002_pilot_v1_20261008"
NEW = ARTICLE_ROOT / "outputs" / "bench_002_pilot_v2_fast_gate_fix_20261009"
OUT = ARTICLE_ROOT / "outputs" / "bench_002_pilot_v2_fast_gate_fix_validation_20261009"
EXPECTED_SUBJECTS = ("sub-032", "sub-033", "sub-034", "sub-035", "sub-036", "sub-038")
EXPECTED_FAST_COUNT = 7776
EXPECTED_V3_COUNT = 648
FAST_CANDIDATES = {"M1": "PCV", "M2": "TP", "E1": "OI", "E2": "SC"}
V3_COMPONENTS = (
    "PCV", "TP", *(f"AR_pair_{i:02d}" for i in range(1, 10)),
    "NIE", "RD", "OI", "SC", "ED",
)
PARITY_RTOL = 1e-12
PARITY_ATOL = 1e-14


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check(name: str, passed: bool, details: Any = None) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "details": details}


def main() -> None:
    started = time.perf_counter()
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite post-run validation: {OUT}")
    OUT.mkdir(parents=True, exist_ok=False)

    old_manifest = json.loads((OLD / "run_manifest.json").read_text(encoding="utf-8"))
    new_manifest = json.loads((NEW / "run_manifest.json").read_text(encoding="utf-8"))
    checks: list[dict[str, Any]] = []

    old_subjects = tuple(old_manifest.get("participants", []))
    new_subjects = tuple(new_manifest.get("participants", []))
    checks.append(check("six_frozen_participants", old_subjects == EXPECTED_SUBJECTS and new_subjects == EXPECTED_SUBJECTS,
                        {"old": old_subjects, "new": new_subjects}))
    checks.append(check("run_completed_without_classifier_or_full_cohort",
                        new_manifest.get("status") == "complete"
                        and new_manifest.get("full_cohort_run") is False
                        and new_manifest.get("classifier_fit") is False,
                        {key: new_manifest.get(key) for key in ("status", "full_cohort_run", "classifier_fit")}))

    old_inputs = old_manifest.get("input_file_sha256", {})
    new_inputs = new_manifest.get("input_file_sha256", {})
    input_keys_match = set(old_inputs) == set(new_inputs)
    input_hashes_match = input_keys_match and all(old_inputs[key] == new_inputs[key] for key in old_inputs)
    checks.append(check("raw_and_metadata_inputs_match_frozen_run", input_hashes_match,
                        {"old_file_count": len(old_inputs), "new_file_count": len(new_inputs),
                         "same_path_set": input_keys_match}))

    recorded_outputs = new_manifest.get("outputs", {})
    hash_mismatches: list[dict[str, str]] = []
    missing_outputs: list[str] = []
    for name, expected in recorded_outputs.items():
        path = NEW / name
        if not path.is_file():
            missing_outputs.append(name)
            continue
        actual = sha256_file(path)
        if actual != expected.get("sha256") or path.stat().st_size != expected.get("bytes"):
            hash_mismatches.append({"file": name, "expected": str(expected.get("sha256")), "actual": actual})
    present_output_names = {path.name for path in NEW.iterdir() if path.is_file() and path.name != "run_manifest.json"}
    checks.append(check("new_run_output_hashes_match_manifest",
                        not missing_outputs and not hash_mismatches and present_output_names == set(recorded_outputs),
                        {"manifest_file_count": len(recorded_outputs), "present_file_count": len(present_output_names),
                         "missing": missing_outputs, "mismatches": hash_mismatches}))

    # Compare the untouched historical 20-second export against the rerun.
    old_v3_path = OLD / "v3_window_values.csv"
    new_v3_path = NEW / "v3_window_values.csv"
    old_v3 = pd.read_csv(old_v3_path)
    new_v3 = pd.read_csv(new_v3_path)
    keys = ["subject", "surface", "trial_id", "window_index", "window_start_sample_250hz",
            "window_end_sample_250hz_exclusive"]
    merged = old_v3.merge(new_v3, on=keys, how="outer", suffixes=("_old", "_new"), indicator=True,
                          validate="one_to_one")
    key_match = bool(merged["_merge"].eq("both").all()) and len(old_v3) == len(new_v3) == EXPECTED_V3_COUNT
    component_summaries: list[dict[str, Any]] = []
    per_window: dict[tuple[Any, ...], dict[str, Any]] = {}
    v3_all_close = key_match
    for component in V3_COMPONENTS:
        old_values = pd.to_numeric(merged[f"{component}_old"], errors="coerce").to_numpy(dtype=np.float64)
        new_values = pd.to_numeric(merged[f"{component}_new"], errors="coerce").to_numpy(dtype=np.float64)
        finite = np.isfinite(old_values) & np.isfinite(new_values)
        differences = np.abs(new_values[finite] - old_values[finite])
        close = finite.all() and bool(np.allclose(old_values, new_values, rtol=PARITY_RTOL, atol=PARITY_ATOL))
        component_summaries.append({
            "component": component,
            "finite_pairs": int(finite.sum()),
            "nonzero_exact_differences": int(np.count_nonzero(differences)),
            "max_absolute_difference": float(differences.max()) if differences.size else None,
            "all_within_tolerance": bool(close),
        })
        v3_all_close &= bool(close)
    checks.append(check("historical_20s_keys_and_full_vector_unchanged",
                        key_match and v3_all_close,
                        {"old_rows": len(old_v3), "new_rows": len(new_v3), "key_pairs": int(merged["_merge"].eq("both").sum()),
                         "load_values_new": sorted(pd.to_numeric(new_v3["load"]).dropna().astype(int).unique().tolist()),
                         "rtol": PARITY_RTOL, "atol": PARITY_ATOL, "components": component_summaries}))
    merged.loc[:, keys + [f"{component}_old" for component in V3_COMPONENTS]
               + [f"{component}_new" for component in V3_COMPONENTS]].to_csv(OUT / "v3_20s_parity.csv", index=False)

    fast_path = NEW / "fast_core_4s_window_values.csv"
    fast = pd.read_csv(fast_path)
    fast_count_ok = len(fast) == EXPECTED_FAST_COUNT == int(new_manifest.get("fast_core_4s_window_count", -1))
    finite_components = fast.loc[:, list(FAST_CANDIDATES.values())].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float64)
    fast_values_finite = bool(np.isfinite(finite_components).all())
    group_counts = (fast.groupby(["subject", "surface", "load"], as_index=False)
                    .agg(window_count=("trial_id", "size"), participant_count=("subject", "nunique")))
    group_counts.to_csv(OUT / "fast_core_support_by_participant_surface_load.csv", index=False)
    expected_groups = {(s, surface, load) for s in EXPECTED_SUBJECTS for surface in ("native", "core19") for load in (5, 9, 13)}
    actual_groups = {(str(row.subject), str(row.surface), int(row.load)) for row in group_counts.itertuples()}
    checks.append(check("fast_core_four_second_support_all_subject_surface_loads",
                        fast_count_ok and actual_groups == expected_groups and bool((group_counts.window_count > 0).all()),
                        {"window_count": len(fast), "expected_window_count": EXPECTED_FAST_COUNT,
                         "group_count": len(actual_groups), "expected_group_count": len(expected_groups),
                         "groups_missing": sorted(expected_groups - actual_groups)}))
    checks.append(check("fast_core_csv_values_finite", fast_values_finite,
                        {"rows": len(fast), "component_columns": list(FAST_CANDIDATES.values()),
                         "finite_value_count": int(np.isfinite(finite_components).sum()),
                         "expected_value_count": int(finite_components.size)}))

    support = pd.read_csv(NEW / "trial_support.csv")
    support_key = ["subject", "surface", "trial_id"]
    fast_support = support.loc[:, support_key + ["source_start_sample", "source_end_sample_exclusive",
                                                   "fast_core_four_second_window_count", "twenty_second_window_count"]]
    joined = fast.merge(fast_support, on=support_key, how="left", validate="many_to_one", indicator=True)
    trial_start_250 = (pd.to_numeric(joined["source_start_sample"], errors="coerce") + 3) // 4
    trial_end_250 = pd.to_numeric(joined["source_end_sample_exclusive"], errors="coerce") // 4
    within_trial = (joined["_merge"].eq("both")
                    & (pd.to_numeric(joined["window_start_sample_250hz"], errors="coerce") >= trial_start_250)
                    & (pd.to_numeric(joined["window_end_sample_250hz_exclusive"], errors="coerce") <= trial_end_250)
                    & ((pd.to_numeric(joined["window_end_sample_250hz_exclusive"], errors="coerce")
                        - pd.to_numeric(joined["window_start_sample_250hz"], errors="coerce")) == 1000)
                    & (pd.to_numeric(joined["sample_count"], errors="coerce") == 1000))
    counts_by_trial = fast.groupby(support_key, as_index=False).size().rename(columns={"size": "observed_fast_core_windows"})
    count_check = counts_by_trial.merge(fast_support, on=support_key, how="outer", validate="one_to_one", indicator=True)
    observed_count = pd.to_numeric(count_check["observed_fast_core_windows"], errors="coerce").fillna(0)
    declared_count = pd.to_numeric(count_check["fast_core_four_second_window_count"], errors="coerce").fillna(0)
    count_check["count_matches_support"] = (
        ~count_check["_merge"].eq("left_only")
        & (observed_count == declared_count)
    )
    count_check.to_csv(OUT / "fast_core_trial_support_check.csv", index=False)
    checks.append(check("fast_core_windows_within_declared_trial_bounds_and_support",
                        bool(within_trial.all()) and bool(count_check["count_matches_support"].all()),
                        {"window_rows": len(fast), "within_trial_rows": int(within_trial.sum()),
                         "trial_groups": len(count_check), "matching_support_counts": int(count_check["count_matches_support"].sum())}))

    # Inspect the four requested candidates' own emitted status in the full JSONL.
    status_counts: dict[str, dict[str, int]] = {name: {"rows": 0, "computed": 0, "valid": 0, "qualified": 0,
                                                        "finite": 0, "missing": 0} for name in FAST_CANDIDATES.values()}
    jsonl_rows = 0
    with (NEW / "fast_core_4s_measurements.jsonl").open("r", encoding="utf-8") as stream:
        for line in stream:
            jsonl_rows += 1
            record = json.loads(line)
            for measurement in record.get("result", {}).get("measurements", []):
                candidate_id = str(measurement.get("candidate_id", ""))
                if candidate_id not in FAST_CANDIDATES:
                    continue
                name = FAST_CANDIDATES[candidate_id]
                counts = status_counts[name]
                counts["rows"] += 1
                counts["computed"] += int(bool(measurement.get("computed")))
                counts["valid"] += int(bool(measurement.get("valid")))
                counts["qualified"] += int(bool(measurement.get("qualified")))
                value = measurement.get("value")
                try:
                    finite = value is not None and math.isfinite(float(value))
                except (TypeError, ValueError, OverflowError):
                    finite = False
                counts["finite"] += int(finite)
                counts["missing"] += int(value is None)
    expected_candidate_rows = EXPECTED_FAST_COUNT
    candidate_status_ok = all(
        counts["rows"] == expected_candidate_rows
        and counts["computed"] == expected_candidate_rows
        and counts["valid"] == expected_candidate_rows
        and counts["finite"] == expected_candidate_rows
        and counts["qualified"] == 0
        and counts["missing"] == 0
        for counts in status_counts.values()
    )
    checks.append(check("fast_core_measurements_computed_valid_finite_unqualified",
                        jsonl_rows == EXPECTED_FAST_COUNT and candidate_status_ok,
                        {"jsonl_window_rows": jsonl_rows, "expected_window_rows": EXPECTED_FAST_COUNT,
                         "candidate_status": status_counts}))

    v3_loads = sorted(pd.to_numeric(new_v3["load"], errors="coerce").dropna().astype(int).unique().tolist())
    checks.append(check("full_v3_20s_remains_load_13_only",
                        len(new_v3) == EXPECTED_V3_COUNT and v3_loads == [13],
                        {"v3_window_count": len(new_v3), "loads": v3_loads}))

    all_pass = all(item["passed"] for item in checks)
    summary = {
        "schema": "bench_002_pilot_v2_postrun_validation.v1",
        "status": "pass" if all_pass else "issues_detected",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "old_run_manifest_sha256": sha256_file(OLD / "run_manifest.json"),
        "new_run_manifest_sha256": sha256_file(NEW / "run_manifest.json"),
        "new_output_path": str(NEW),
        "parity_tolerance": {"rtol": PARITY_RTOL, "atol": PARITY_ATOL},
        "checks": checks,
        "elapsed_seconds": time.perf_counter() - started,
    }
    (OUT / "validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = [
        "# BENCH-002 corrected six-participant extraction — post-run validation",
        "",
        f"Status: **{summary['status']}**.",
        "",
        f"Corrected output: `{NEW}`.",
        "",
        "## Checks",
        "",
        "| Check | Result |",
        "| --- | --- |",
    ]
    for item in checks:
        lines.append(f"| {item['check']} | {'PASS' if item['passed'] else 'FAIL'} |")
    lines += [
        "",
        f"The run emitted {new_manifest.get('fast_core_4s_window_count')} independent 4-second fast-core windows and {new_manifest.get('v3_window_count_20s')} full-v3 20-second windows. The latter is compared against the historical V1 export using `rtol={PARITY_RTOL}` and `atol={PARITY_ATOL}` across all 16 numeric components.",
        "",
        "No classifier or full-cohort run was executed. The six pilot participants had already been outcome-exposed. Results remain an exploratory support and implementation check, not a scientific qualification or biological conclusion.",
        "",
        "See `v3_20s_parity.csv`, `fast_core_support_by_participant_surface_load.csv`, `fast_core_trial_support_check.csv`, and `validation_summary.json`.",
    ]
    (OUT / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary["results_sha256"] = sha256_file(OUT / "results.md")
    (OUT / "validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"status": summary["status"], "output": str(OUT),
                      "checks": [{"name": item["check"], "passed": item["passed"]} for item in checks],
                      "elapsed_seconds": summary["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
