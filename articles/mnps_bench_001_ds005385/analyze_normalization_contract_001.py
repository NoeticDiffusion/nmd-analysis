from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ARTICLE = Path(__file__).resolve().parent
SOURCE = ARTICLE / "outputs" / "_mnps_legacy_loss_003" / "stage_feature_values.csv"
PROTOCOL = ARTICLE / "normalization_contract_001_protocol_v1_20261008.md"
PROJECTION = Path(
    r"H:\SourceRepo2\NeuralManifoldDynamics\mndm\src\mndm\projection.py"
)
OUTPUT = ARTICLE / "outputs" / "_mnps_normalization_contract_001"
SEED = 20261008
ATOL = 1e-6


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_projection_helper():
    spec = importlib.util.spec_from_file_location(
        "mnps_normalization_contract_projection", PROJECTION
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("projection_helper_load_failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module._apply_column_pipeline


def robust_z(values: np.ndarray, apply_pipeline) -> np.ndarray:
    return np.asarray(
        apply_pipeline(np.asarray(values, dtype=np.float64), ["robust_z"]),
        dtype=np.float64,
    )


def lag1(values: np.ndarray) -> float:
    return float(np.corrcoef(values[:-1], values[1:])[0, 1])


def synthetic_audit(apply_pipeline) -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    base = rng.normal(size=401) + 0.2 * np.sin(np.linspace(0, 8 * np.pi, 401))
    base_z = robust_z(base, apply_pipeline)
    offset_z = robust_z(base + 3.25, apply_pipeline)
    scaled_z = robust_z(base * 4.5, apply_pipeline)

    state_a = rng.normal(loc=0.0, scale=1.0, size=401)
    state_b = rng.normal(loc=1.75, scale=1.0, size=401)
    shared_z = robust_z(np.concatenate((state_a, state_b)), apply_pipeline)
    shared_a_median = float(np.median(shared_z[: state_a.size]))
    shared_b_median = float(np.median(shared_z[state_a.size :]))
    local_a_median = float(np.median(robust_z(state_a, apply_pipeline)))
    local_b_median = float(np.median(robust_z(state_b, apply_pipeline)))

    # A deterministic AR(1) series makes temporal ordering visible after
    # applying the same pointwise robust-z transform.
    innovations = rng.normal(size=501)
    ar = np.empty_like(innovations)
    ar[0] = innovations[0]
    for index in range(1, ar.size):
        ar[index] = 0.85 * ar[index - 1] + innovations[index]
    ar_z = robust_z(ar, apply_pipeline)
    shuffled_z = robust_z(ar[rng.permutation(ar.size)], apply_pipeline)
    ar_median_delta = float(np.median(ar_z) - np.median(shuffled_z))
    ar_variance_delta = float(np.var(ar_z) - np.var(shuffled_z))
    ar_lag1 = lag1(ar_z)
    shuffled_lag1 = lag1(shuffled_z)

    reference = rng.normal(loc=0.0, scale=1.0, size=501)
    reference_center = float(np.median(reference))
    reference_scale = float(1.4826 * np.median(np.abs(reference - reference_center)))
    target = rng.normal(loc=0.0, scale=1.0, size=501)
    target_offset = target + 2.75
    fixed_target = (target - reference_center) / reference_scale
    fixed_offset = (target_offset - reference_center) / reference_scale
    fixed_reference_median_shift = float(
        np.median(fixed_offset) - np.median(fixed_target)
    )

    checks = {
        "local_offset_invariance": bool(
            np.allclose(base_z, offset_z, atol=ATOL, rtol=0.0)
        ),
        "local_positive_scale_invariance": bool(
            np.allclose(base_z, scaled_z, atol=ATOL, rtol=0.0)
        ),
        "same_support_median_centered": bool(abs(float(np.median(base_z))) <= ATOL),
        "shared_transform_preserves_state_median_difference": bool(
            abs(shared_b_median - shared_a_median) > 0.25
        ),
        "separate_local_transforms_center_each_state": bool(
            abs(local_a_median) <= ATOL and abs(local_b_median) <= ATOL
        ),
        "permutation_preserves_median_and_variance": bool(
            abs(ar_median_delta) <= ATOL and abs(ar_variance_delta) <= ATOL
        ),
        "permutation_changes_lag1_structure": bool(
            abs(ar_lag1 - shuffled_lag1) > 0.25
        ),
        "fixed_reference_retains_offset": bool(
            fixed_reference_median_shift > 1.0
        ),
    }
    if not all(checks.values()):
        raise AssertionError(f"synthetic_invariant_failed: {checks}")

    return {
        "schema": "mnps_normalization_contract_001_synthetic.v1",
        "seed": SEED,
        "robust_z": {
            "helper": "mndm.projection._apply_column_pipeline",
            "pipeline": ["robust_z"],
            "mad_multiplier": 1.4826,
            "degenerate_scale_policy": "eps_floor",
            "comparison_atol": ATOL,
        },
        "checks": checks,
        "measurements": {
            "local_offset_max_abs_difference": float(np.max(np.abs(base_z - offset_z))),
            "local_positive_scale_max_abs_difference": float(
                np.max(np.abs(base_z - scaled_z))
            ),
            "same_support_median": float(np.median(base_z)),
            "shared_state_a_normalized_median": shared_a_median,
            "shared_state_b_normalized_median": shared_b_median,
            "shared_state_median_difference": float(shared_b_median - shared_a_median),
            "state_a_separately_normalized_median": local_a_median,
            "state_b_separately_normalized_median": local_b_median,
            "ar1_normalized_median": float(np.median(ar_z)),
            "permuted_ar1_normalized_median": float(np.median(shuffled_z)),
            "ar1_normalized_variance": float(np.var(ar_z)),
            "permuted_ar1_normalized_variance": float(np.var(shuffled_z)),
            "ar1_lag1_autocorrelation_after_robust_z": ar_lag1,
            "permuted_lag1_autocorrelation_after_robust_z": shuffled_lag1,
            "fixed_reference_center": reference_center,
            "fixed_reference_scale": reference_scale,
            "fixed_reference_offset_median_shift": fixed_reference_median_shift,
            "fixed_reference_expected_shift": float(2.75 / reference_scale),
        },
    }


def main() -> None:
    for required in (SOURCE, PROTOCOL, PROJECTION):
        if not required.is_file():
            raise FileNotFoundError(required)
    if OUTPUT.exists():
        if any(OUTPUT.iterdir()):
            raise FileExistsError(f"refusing_to_overwrite_nonempty_output: {OUTPUT}")
    else:
        OUTPUT.mkdir(parents=True, exist_ok=False)

    frame = pd.read_csv(SOURCE)
    required_columns = {"arm", "subject", "state", "feature", "value"}
    if not required_columns.issubset(frame.columns):
        raise ValueError("legacy_loss_003_source_schema_mismatch")
    empirical = frame.loc[frame["arm"].eq("R")].copy()
    values = pd.to_numeric(empirical["value"], errors="raise").to_numpy(dtype=np.float64)
    if values.size != 2000 or not np.isfinite(values).all():
        raise ValueError(f"expected_2000_finite_R_values_got_{values.size}")
    if empirical["subject"].nunique() != 100 or empirical["state"].nunique() != 2:
        raise ValueError("legacy_loss_003_R_population_mismatch")
    if empirical["feature"].nunique() != 10:
        raise ValueError("legacy_loss_003_R_feature_count_mismatch")

    thresholds = (0.0, 1e-12, 1e-6, 1e-5)
    feature_rows: list[dict[str, Any]] = []
    for feature, group in empirical.groupby("feature", sort=True):
        feature_values = pd.to_numeric(group["value"], errors="raise").to_numpy(
            dtype=np.float64
        )
        row: dict[str, Any] = {
            "feature": str(feature),
            "n": int(feature_values.size),
            "max_abs_value": float(np.max(np.abs(feature_values))),
            "distinct_values": int(np.unique(feature_values).size),
        }
        for threshold in thresholds:
            key = "exact_zero" if threshold == 0 else f"abs_le_{threshold:g}"
            row[key] = int(np.count_nonzero(np.abs(feature_values) <= threshold))
        feature_rows.append(row)
    feature_csv = OUTPUT / "empirical_feature_audit.csv"
    pd.DataFrame(feature_rows).to_csv(feature_csv, index=False, quoting=csv.QUOTE_MINIMAL)

    global_counts = {
        "n": int(values.size),
        "exact_zero": int(np.count_nonzero(values == 0.0)),
        "abs_le_1e-12": int(np.count_nonzero(np.abs(values) <= 1e-12)),
        "abs_le_1e-6": int(np.count_nonzero(np.abs(values) <= 1e-6)),
        "abs_le_1e-5": int(np.count_nonzero(np.abs(values) <= 1e-5)),
        "max_abs_value": float(np.max(np.abs(values))),
        "distinct_values": int(np.unique(values).size),
    }
    if global_counts["abs_le_1e-5"] != values.size:
        raise AssertionError("empirical_values_exceed_prespecified_near_zero_bound")
    empirical_json = {
        "schema": "mnps_normalization_contract_001_empirical.v1",
        "arm": "R",
        "source_rows": global_counts,
        "population": {
            "participants": int(empirical["subject"].nunique()),
            "states": sorted(str(x) for x in empirical["state"].unique()),
            "features": sorted(str(x) for x in empirical["feature"].unique()),
            "aggregation": "saved participant x state x feature values",
        },
        "per_feature_csv": feature_csv.name,
    }

    apply_pipeline = load_projection_helper()
    synthetic = synthetic_audit(apply_pipeline)
    (OUTPUT / "empirical_audit.json").write_text(
        json.dumps(empirical_json, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (OUTPUT / "synthetic_invariants.json").write_text(
        json.dumps(synthetic, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    measurements = synthetic["measurements"]
    report = f"""# NORMALIZATION-CONTRACT-001 results

Generated {datetime.now(timezone.utc).isoformat()} from the frozen protocol.

## Empirical LEGACY-LOSS-003 audit

Only the saved R-arm rows in stage_feature_values.csv were read; no EEG,
EDF, or HDF5 processing was rerun.

| Quantity | Result |
|---|---:|
| Saved aggregate values | {global_counts['n']} |
| Exactly zero | {global_counts['exact_zero']} |
| Absolute value ≤ 1e-12 | {global_counts['abs_le_1e-12']} |
| Absolute value ≤ 1e-6 | {global_counts['abs_le_1e-6']} |
| Absolute value ≤ 1e-5 | {global_counts['abs_le_1e-5']} |
| Maximum absolute value | {global_counts['max_abs_value']:.9g} |
| Distinct saved values | {global_counts['distinct_values']} |

The per-feature counts are in empirical_feature_audit.csv. The residual
values are finite-precision outputs around the median-zero result predicted
for recording-local robust-z followed by a median over the same windows.

## Synthetic invariant audit

All eight prespecified assertions passed using the repository projection
helper (robust_z, float32, 1.4826 × MAD, epsilon-floor compatibility mode).

| Invariant | Measurement |
|---|---:|
| Maximum local offset difference | {measurements['local_offset_max_abs_difference']:.3g} |
| Maximum local positive-scale difference | {measurements['local_positive_scale_max_abs_difference']:.3g} |
| Same-support robust-z median | {measurements['same_support_median']:.3g} |
| Shared-transform state median difference | {measurements['shared_state_median_difference']:.6g} |
| Separately normalized state medians | {measurements['state_a_separately_normalized_median']:.3g}, {measurements['state_b_separately_normalized_median']:.3g} |
| AR(1) lag-1 after robust-z | {measurements['ar1_lag1_autocorrelation_after_robust_z']:.3f} |
| Permuted lag-1 after robust-z | {measurements['permuted_lag1_autocorrelation_after_robust_z']:.3f} |
| Fixed-reference median shift after offset | {measurements['fixed_reference_offset_median_shift']:.6g} |

Local normalization removes a constant recording offset and positive scale
within the declared tolerance. A single transform shared across both states
retains their relative median difference, while transforming each state
locally centers each separately. Robust-z preserves the AR(1) sample values
and their distribution under permutation but not their ordering statistic.
A fixed reference leaves the offset visible because its center and scale are
not recomputed on the target.

## Limits

This audit confirms algebraic behavior for the specified implementation and
describes the saved LEGACY-LOSS-003 aggregate values. It does not establish
that local, shared, or fixed-reference normalization is preferable for a
scientific use. It does not change canonical v3.1 measurements, historical
v2 outputs, support, or validity.
"""
    report_path = OUTPUT / "results.md"
    report_path.write_text(report, encoding="utf-8")

    artifacts = (
        feature_csv,
        OUTPUT / "empirical_audit.json",
        OUTPUT / "synthetic_invariants.json",
        report_path,
    )
    manifest = {
        "schema": "mnps_normalization_contract_001_manifest.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_script": str(Path(__file__).resolve()),
        "analysis_script_sha256": sha256_file(Path(__file__).resolve()),
        "protocol": str(PROTOCOL),
        "protocol_sha256": sha256_file(PROTOCOL),
        "source_table": str(SOURCE),
        "source_table_sha256": sha256_file(SOURCE),
        "projection_helper": str(PROJECTION),
        "projection_helper_sha256": sha256_file(PROJECTION),
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "seed": SEED,
        "outputs": {path.name: sha256_file(path) for path in artifacts},
    }
    (OUTPUT / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "empirical": global_counts,
                "synthetic_checks": synthetic["checks"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
