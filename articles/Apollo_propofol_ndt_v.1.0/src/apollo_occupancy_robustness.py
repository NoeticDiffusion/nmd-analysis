"""Pre-specified robustness branch for the frozen Apollo occupancy scalar.

This module deliberately reuses the frozen feature contract and reference
eligibility mask. It writes to a fresh dated output root and never modifies the
frozen occupancy outputs.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from apollo_c3_anchor_part1 import anchored_series, load_recording
from apollo_c3_match import eligible_mask
from apollo_c3_panel import MAD_FLOOR, SPECTRAL_FEATURES
from apollo_common import (
    ARTICLE_DIR,
    DEFAULT_CONFIG,
    DEFAULT_H5_ROOT,
    json_safe,
    sha256_file,
    write_json,
)
from apollo_c3_match import baseline_center_scale
from apollo_occupancy_panel import BASELINE_PHASE, ORDERED_LATERS
from apollo_stage_part1 import LABELS_DEFAULT, SUPPORT_DEFAULT, load_cohort
from apollo_stats import cohens_dz, exact_sign_test_p, wilcoxon_p

ANALYSIS_VERSION = "apollo_occupancy_robustness_20260922_v1"
OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_occupancy_robustness_20260922_reviewfix"
IQR_NORMAL_CONSISTENCY = 1.3489795003921634
VARIANT_REFERENCE = "full_mad"
SCALE_VARIANTS = ("scale_sd", "scale_iqr")
REFERENCE_REPRO_TOLERANCE = 1e-10
FROZEN_OCCUPANCY_COLUMNS = {
    "occupancy_pre_drug_baseline": BASELINE_PHASE,
    "occupancy_first_protocol_sedation": "first_protocol_sedation",
    "occupancy_later_protocol_sedation": "later_protocol_sedation",
    "occupancy_recovery": "recovery",
}


def _finite_median(values: np.ndarray) -> float:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    return float(np.median(finite)) if finite.size else float("nan")


def _scale_alternative(raw: np.ndarray, method: str) -> np.ndarray:
    array = np.asarray(raw, dtype=float)
    if method == VARIANT_REFERENCE:
        _, scale = baseline_center_scale(array)
        return scale
    if method == "scale_sd":
        return np.nanstd(array, axis=0, ddof=1)
    if method == "scale_iqr":
        q75 = np.nanpercentile(array, 75, axis=0)
        q25 = np.nanpercentile(array, 25, axis=0)
        return (q75 - q25) / IQR_NORMAL_CONSISTENCY
    raise ValueError(f"unknown scale method: {method}")


def _valid_scale(scale: np.ndarray) -> np.ndarray:
    values = np.asarray(scale, dtype=float)
    return np.isfinite(values) & (values > MAD_FLOOR)


def _radius(points: np.ndarray) -> float:
    values = np.asarray(points, dtype=float)
    if values.ndim != 2 or values.shape[0] == 0:
        return float("nan")
    norms = np.linalg.norm(values, axis=1)
    return _finite_median(norms)


def _z_from_scale(raw: np.ndarray, centre: np.ndarray, scale: np.ndarray) -> np.ndarray:
    safe = np.where(_valid_scale(scale), scale, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        return (np.asarray(raw, dtype=float) - centre) / safe


def _phase_row(
    *,
    subject_id: str,
    phase: str,
    source_h5: str | None,
    raw: np.ndarray | None,
    time: np.ndarray | None,
    centre: np.ndarray | None,
    reference_scale: np.ndarray | None,
    alternative_scales: dict[str, np.ndarray] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Return variant rows, feature contributions, and a support audit row."""
    variants: list[dict[str, Any]] = []
    contributions: list[dict[str, Any]] = []
    audit: dict[str, Any] = {
        "subject_id": subject_id,
        "phase": phase,
        "source_h5": source_h5,
        "n_reference_eligible": 0,
        "reference_status": "failure",
        "failure_reason": None,
    }
    if raw is None or time is None or centre is None or reference_scale is None:
        audit["failure_reason"] = "missing_recording_or_baseline_frame"
        for variant in (VARIANT_REFERENCE, *SCALE_VARIANTS, *(f"loo_{name}" for name in SPECTRAL_FEATURES)):
            variants.append(_variant_row(subject_id, phase, source_h5, variant, audit, float("nan"), 0, "failure", audit["failure_reason"]))
        return variants, contributions, audit

    raw_values = np.asarray(raw, dtype=float)
    ref_z_series = anchored_series(raw_values, np.asarray(time, dtype=float), centre, reference_scale)
    ref_mask = eligible_mask(ref_z_series["z"], ref_z_series["dxdt"], ref_z_series["valid"], ref_z_series["dt"])
    n_reference = int(ref_mask.sum())
    audit["n_reference_eligible"] = n_reference
    audit["reference_status"] = "ok" if n_reference else "failure"
    if not n_reference:
        audit["failure_reason"] = "no_reference_eligible_rows"

    ref_points = ref_z_series["z"][ref_mask]
    full_value = _radius(ref_points)
    full_status = "ok" if np.isfinite(full_value) else "failure"
    full_reason = None if full_status == "ok" else "no_finite_reference_radius"
    variants.append(_variant_row(subject_id, phase, source_h5, VARIANT_REFERENCE, audit, full_value, n_reference, full_status, full_reason))

    # Feature decomposition is defined only in the frozen full-MAD frame.
    if n_reference:
        squared = ref_points * ref_points
        radius_squared = np.sum(squared, axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            shares = squared / radius_squared[:, None]
        for index, feature in enumerate(SPECTRAL_FEATURES):
            feature_shares = shares[:, index]
            defined = np.isfinite(feature_shares)
            contributions.append(
                {
                    "subject_id": subject_id,
                    "phase": phase,
                    "feature": feature,
                    "n_reference_eligible": n_reference,
                    "n_share_defined": int(defined.sum()),
                    "median_squared_contribution": _finite_median(squared[:, index]),
                    "mean_squared_share": float(np.mean(feature_shares[defined])) if defined.any() else float("nan"),
                    "median_squared_share": _finite_median(feature_shares),
                    "full_mad_occupancy": full_value,
                }
            )

    # Scale alternatives retain the centre and the exact reference eligibility mask.
    for variant in SCALE_VARIANTS:
        scale = (alternative_scales or {}).get(variant)
        if scale is None:
            variants.append(_variant_row(subject_id, phase, source_h5, variant, audit, float("nan"), 0, "failure", "missing_baseline_scale"))
            continue
        z_variant = _z_from_scale(raw_values, centre, scale)
        points = z_variant[ref_mask]
        finite_rows = np.isfinite(points).all(axis=1) if points.ndim == 2 else np.zeros(n_reference, dtype=bool)
        if not _valid_scale(scale).all():
            value = float("nan")
            status = "failure"
            reason = "invalid_alternative_scale"
        elif not finite_rows.all():
            value = float("nan")
            status = "failure"
            reason = "nonfinite_on_reference_eligible_rows"
        else:
            value = _radius(points)
            status = "ok" if np.isfinite(value) else "failure"
            reason = None if status == "ok" else "no_finite_alternative_radius"
        variants.append(_variant_row(subject_id, phase, source_h5, variant, audit, value, int(finite_rows.sum()), status, reason))

    # LOO diagnostics use the same reference eligible rows and cannot rescue missingness.
    for index, feature in enumerate(SPECTRAL_FEATURES):
        loo_points = np.delete(ref_points, index, axis=1)
        value = _radius(loo_points)
        status = "ok" if np.isfinite(value) else "failure"
        reason = None if status == "ok" else "no_finite_leave_one_out_radius"
        variants.append(_variant_row(subject_id, phase, source_h5, f"loo_{feature}", audit, value, n_reference, status, reason))
    return variants, contributions, audit


def _variant_row(subject_id: str, phase: str, source_h5: str | None, variant: str, audit: dict[str, Any], value: float, n_finite: int, status: str, reason: str | None) -> dict[str, Any]:
    return {
        "analysis_version": ANALYSIS_VERSION,
        "subject_id": subject_id,
        "phase": phase,
        "source_h5": source_h5,
        "variant": variant,
        "occupancy": value,
        "n_reference_eligible": int(audit.get("n_reference_eligible", 0)),
        "n_variant_finite": int(n_finite),
        "status": status,
        "failure_reason": reason,
    }


def _contrast_rows(subject_phase: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for variant in sorted(subject_phase["variant"].unique()):
        subset = subject_phase[subject_phase["variant"] == variant]
        wide = subset.pivot(index="subject_id", columns="phase", values="occupancy")
        for phase in ORDERED_LATERS:
            if BASELINE_PHASE not in wide.columns or phase not in wide.columns:
                pairs = np.array([], dtype=float)
            else:
                pairs = (wide[phase] - wide[BASELINE_PHASE]).to_numpy(dtype=float)
                pairs = pairs[np.isfinite(pairs)]
            rows.append(
                {
                    "analysis_version": ANALYSIS_VERSION,
                    "variant": variant,
                    "phase": phase,
                    "n_pairs": int(pairs.size),
                    "n_positive": int(np.sum(pairs > 0)),
                    "n_negative": int(np.sum(pairs < 0)),
                    "n_zero": int(np.sum(pairs == 0)),
                    "median_paired_difference": _finite_median(pairs),
                    "mean_paired_difference": float(np.mean(pairs)) if pairs.size else float("nan"),
                    "cohens_dz": cohens_dz(pairs),
                    "sign_test_p": exact_sign_test_p(pairs),
                    "wilcoxon_p": wilcoxon_p(pairs),
                    "participant_unit": True,
                    "reference_eligibility_preserved": True,
                    "scientific_status": "exploratory_descriptive_not_confirmatory",
                }
            )
    return pd.DataFrame(rows)


def reference_reproduction(
    subject_phase: pd.DataFrame,
    frozen_path: Path,
    *,
    tolerance: float = REFERENCE_REPRO_TOLERANCE,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Compare full-MAD values to every finite cell in the frozen subject table."""
    frozen = pd.read_csv(frozen_path)
    available = frozen[["subject_id", *FROZEN_OCCUPANCY_COLUMNS]].melt(
        id_vars="subject_id", var_name="frozen_column", value_name="frozen_occupancy"
    )
    available["phase"] = available["frozen_column"].map(FROZEN_OCCUPANCY_COLUMNS)
    available["frozen_occupancy"] = pd.to_numeric(available["frozen_occupancy"], errors="coerce")
    available = available[np.isfinite(available["frozen_occupancy"].to_numpy(dtype=float))].copy()
    current = subject_phase[subject_phase["variant"] == VARIANT_REFERENCE][
        ["subject_id", "phase", "occupancy", "status"]
    ].copy()
    current["occupancy"] = pd.to_numeric(current["occupancy"], errors="coerce")
    compared = available.merge(current, on=["subject_id", "phase"], how="left", validate="one_to_one")
    compared["abs_diff"] = np.abs(compared["frozen_occupancy"] - compared["occupancy"])
    compared["within_tolerance"] = np.isfinite(compared["abs_diff"]) & (compared["abs_diff"] <= tolerance)
    expected = int(len(compared))
    n_compared = int(np.isfinite(compared["abs_diff"].to_numpy(dtype=float)).sum())
    max_abs_diff = float(np.nanmax(compared["abs_diff"].to_numpy(dtype=float))) if n_compared else float("nan")
    passed = bool(expected == n_compared and np.all(compared["within_tolerance"].to_numpy(dtype=bool)))
    summary = {
        "frozen_path": str(frozen_path),
        "frozen_sha256": sha256_file(frozen_path),
        "tolerance": tolerance,
        "n_expected_cells": expected,
        "n_compared_cells": n_compared,
        "max_abs_diff": max_abs_diff,
        "pass": passed,
        "status": "PASS" if passed else "FAIL",
    }
    return compared, summary


def _source_hashes(labels_path: Path, support_path: Path, output_root: Path, plan_path: Path) -> dict[str, Any]:
    frozen_names = (
        "occupancy_subject.csv",
        "occupancy_contrasts.csv",
        "occupancy_part1_manifest.json",
    )
    frozen_root = ARTICLE_DIR / "results" / "v1_occupancy_20260921"
    frozen = {
        name: sha256_file(frozen_root / name) if (frozen_root / name).is_file() else None
        for name in frozen_names
    }
    source_paths = sorted({Path(path) for path in pd.read_csv(labels_path)["source_h5"].dropna().unique()})
    return {
        "labels": {"path": str(labels_path), "sha256": sha256_file(labels_path)},
        "support": {"path": str(support_path), "sha256": sha256_file(support_path)},
        "config": {"path": str(DEFAULT_CONFIG), "sha256": sha256_file(DEFAULT_CONFIG)},
        "preanalysis_plan": {"path": str(plan_path), "sha256": sha256_file(plan_path)},
        "frozen_occupancy_inputs": {"root": str(frozen_root), "files": frozen},
        "h5_files": [
            {"path": str(path), "relative_to_h5_root": str(path.relative_to(DEFAULT_H5_ROOT)), "sha256": sha256_file(path)}
            for path in source_paths
        ],
    }


def _write_summary(path: Path, subject_phase: pd.DataFrame, contrasts: pd.DataFrame, contributions: pd.DataFrame, audits: pd.DataFrame, reproduction: dict[str, Any]) -> None:
    ok = subject_phase[subject_phase["status"] == "ok"]
    lines = [
        f"# Apollo occupancy robustness ({ANALYSIS_VERSION})",
        "",
        "Computational robustness branch for the frozen exploratory occupancy scalar. "
        "All variants reuse the original full-eight-feature reference eligibility mask "
        "and participant-level pairing. This is not a confirmatory lock.",
        "",
        f"Rows with successful participant-phase values: {len(ok)}/{len(subject_phase)}.",
        f"Feature contribution rows: {len(contributions)}; support-audit rows: {len(audits)}.",
        f"Reference reproduction: {reproduction['status']} ({reproduction['n_compared_cells']}/{reproduction['n_expected_cells']} cells; "
        f"max absolute difference {reproduction['max_abs_diff']:.3g}; tolerance {reproduction['tolerance']:.3g}).",
        "",
        "## Paired contrasts",
        "",
        "| Variant | Phase | n | median Δ | d_z | + | − | sign p | Wilcoxon p |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in contrasts.iterrows():
        def fmt(value: Any, digits: int = 4) -> str:
            return "NA" if value is None or not np.isfinite(value) else f"{float(value):.{digits}g}"
        lines.append(
            f"| `{row['variant']}` | {row['phase']} | {int(row['n_pairs'])} | {fmt(row['median_paired_difference'])} | "
            f"{fmt(row['cohens_dz'], 3)} | {int(row['n_positive'])} | {int(row['n_negative'])} | "
            f"{fmt(row['sign_test_p'])} | {fmt(row['wilcoxon_p'])} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The branch quantifies feature and scaling dependence of the frozen scalar. "
            "It does not establish biological robustness, LOR specificity, consciousness, "
            "NDT-C3, or a confirmatory effect. Invalid variants and unsupported rows remain "
            "explicit in the CSV outputs.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(*, labels_path: Path, support_path: Path, output_root: Path) -> dict[str, Any]:
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"robustness output must be fresh and empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    plan_path = ARTICLE_DIR / "preregistration" / "addendum_20260922_occupancy_robustness.md"
    cohort = load_cohort(labels_path, support_path)
    baseline = cohort[cohort["protocol_phase_label"] == BASELINE_PHASE]
    subjects = sorted(baseline["subject_id"].dropna().unique())
    variant_rows: list[dict[str, Any]] = []
    contribution_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    for subject in subjects:
        base_row = baseline[baseline["subject_id"] == subject].iloc[0]
        base_rec = load_recording(str(base_row["source_h5"]))
        base_raw = np.asarray(base_rec["raw"], dtype=float)
        finite_base = np.isfinite(base_raw).all(axis=1)
        centre, reference_scale = baseline_center_scale(base_raw[finite_base])
        alternative_scales = {
            variant: _scale_alternative(base_raw[finite_base], variant) for variant in SCALE_VARIANTS
        }
        for phase in (BASELINE_PHASE, *ORDERED_LATERS):
            phase_rows = cohort[(cohort["subject_id"] == subject) & (cohort["protocol_phase_label"] == phase)]
            if phase_rows.empty:
                result = _phase_row(subject_id=subject, phase=phase, source_h5=None, raw=None, time=None, centre=centre, reference_scale=reference_scale, alternative_scales=alternative_scales)
            else:
                rec = load_recording(str(phase_rows.iloc[0]["source_h5"]))
                result = _phase_row(subject_id=subject, phase=phase, source_h5=str(phase_rows.iloc[0]["source_h5"]), raw=rec["raw"], time=rec["time"], centre=centre, reference_scale=reference_scale, alternative_scales=alternative_scales)
            variants, contributions, audit = result
            variant_rows.extend(variants)
            contribution_rows.extend(contributions)
            audit_rows.append(audit)

    subject_phase = pd.DataFrame(variant_rows)
    contributions = pd.DataFrame(contribution_rows)
    audits = pd.DataFrame(audit_rows)
    contrasts = _contrast_rows(subject_phase)
    frozen_subject_path = ARTICLE_DIR / "results" / "v1_occupancy_20260921" / "occupancy_subject.csv"
    reproduction_table, reproduction = reference_reproduction(subject_phase, frozen_subject_path)
    subject_phase.to_csv(output_root / "robustness_subject_phase.csv", index=False)
    contributions.to_csv(output_root / "feature_contributions.csv", index=False)
    audits.to_csv(output_root / "support_audit.csv", index=False)
    reproduction_table.to_csv(output_root / "reference_reproduction.csv", index=False)
    contrasts.to_csv(output_root / "robustness_contrasts.csv", index=False)
    _write_summary(output_root / "robustness_part1.md", subject_phase, contrasts, contributions, audits, reproduction)

    source_code_paths = [
        ARTICLE_DIR / "src" / "apollo_occupancy_robustness.py",
        ARTICLE_DIR / "src" / "apollo_occupancy_part1.py",
        ARTICLE_DIR / "src" / "apollo_c3_anchor_part1.py",
        ARTICLE_DIR / "src" / "apollo_c3_match.py",
        ARTICLE_DIR / "src" / "apollo_c3_panel.py",
        ARTICLE_DIR / "src" / "apollo_occupancy_panel.py",
        ARTICLE_DIR / "src" / "apollo_stage_part1.py",
        ARTICLE_DIR / "src" / "apollo_stats.py",
    ]
    output_files = sorted(path for path in output_root.iterdir() if path.is_file())
    manifest = {
        "schema": "apollo_propofol_ndt_v1.occupancy_robustness_lock.v1",
        "analysis_version": ANALYSIS_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "computational_lock": {"status": "LOCKED", "criteria": "inputs, source code, plan, outputs hashed; tests and bounded run complete"},
        "scientific_confirmatory_lock": {"status": "OPEN", "reason": "post-hoc exploratory branch; independent G3 review and confirmatory G4 remain outstanding"},
        "measurement_boundary": "existing eight spectral features and original baseline-fixed occupancy eligibility; no MNPS definition change",
        "variants": {
            "reference": VARIANT_REFERENCE,
            "leave_one_feature_out": [f"loo_{name}" for name in SPECTRAL_FEATURES],
            "scale_alternatives": list(SCALE_VARIANTS),
        },
        "parameters": {
            "features": list(SPECTRAL_FEATURES),
            "baseline_phase": BASELINE_PHASE,
            "ordered_later_phases": list(ORDERED_LATERS),
            "dt_min": 3.8,
            "dt_max": 4.2,
            "mad_floor": MAD_FLOOR,
            "iqr_normal_consistency": IQR_NORMAL_CONSISTENCY,
            "randomness": "none",
            "participant_unit": True,
            "eligibility_policy": "reference full-MAD mask reused by every variant",
        },
        "inputs": _source_hashes(labels_path, support_path, output_root, plan_path),
        "reference_reproduction": reproduction,
        "source_code_sha256": {str(path.relative_to(ARTICLE_DIR)): sha256_file(path) for path in source_code_paths if path.is_file()},
        "outputs_sha256": {path.name: sha256_file(path) for path in output_files},
        "summary": {
            "n_subjects": int(len(subjects)),
            "n_subject_phase_rows": int(len(subject_phase)),
            "n_successful_variant_rows": int((subject_phase["status"] == "ok").sum()),
            "n_failed_variant_rows": int((subject_phase["status"] != "ok").sum()),
            "n_contribution_rows": int(len(contributions)),
            "n_support_audit_rows": int(len(audits)),
        },
        "claim_boundary": "descriptive computational robustness only; not G3/G4 and no biological claim",
    }
    write_json(output_root / "robustness_lock_manifest.json", json_safe(manifest))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=LABELS_DEFAULT)
    parser.add_argument("--support", type=Path, default=SUPPORT_DEFAULT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args(argv)
    manifest = run(labels_path=args.labels, support_path=args.support, output_root=args.output_root)
    print(json.dumps({"output_root": str(args.output_root), "analysis_version": manifest["analysis_version"], "summary": manifest["summary"], "computational_lock": manifest["computational_lock"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
