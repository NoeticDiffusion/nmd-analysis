"""Post-hoc PR-01 geometric dissection; separate from frozen occupancy results."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from apollo_c3_anchor_part1 import anchored_series, load_recording
from apollo_c3_match import eligible_mask, greedy_match, median_loo_nn
from apollo_c3_panel import SPECTRAL_FEATURES
from apollo_common import ARTICLE_DIR, json_safe, sha256_file, write_json
from apollo_occupancy_panel import BASELINE_PHASE, ORDERED_LATERS
from apollo_stage_part1 import LABELS_DEFAULT, SUPPORT_DEFAULT, load_cohort
from apollo_stats import cohens_dz, percentile_bootstrap, spearman_rho_p

ANALYSIS_VERSION = "apollo_pr01_geometric_20260922_v1"
OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_pr01_geometric_20260922_final2"
PLAN_PATH = ARTICLE_DIR / "preregistration" / "addendum_20260922_pr01_geometric_dissection.md"
BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 20260922
SHRINKAGE = 0.10
CALIPER_MULTIPLIERS = (0.5, 1.0, 1.5, 2.0)
MIN_PAIRS = 20
MIN_SUBJECTS = 10


def _finite_median(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float).reshape(-1)
    values = values[np.isfinite(values)]
    return float(np.median(values)) if values.size else float("nan")


def _frame_points(raw: np.ndarray, time: np.ndarray, centre: np.ndarray, scale: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    series = anchored_series(raw, time, centre, scale)
    mask = eligible_mask(series["z"], series["dxdt"], series["valid"], series["dt"])
    return np.asarray(series["z"][mask], dtype=float), mask


def _whitener(baseline_points: np.ndarray) -> np.ndarray:
    """Deterministic 10% diagonal-shrinkage baseline inverse square root."""
    points = np.asarray(baseline_points, dtype=float)
    if points.ndim != 2 or points.shape[0] < 2 or not np.isfinite(points).all():
        raise ValueError("baseline covariance requires at least two finite eligible points")
    covariance = np.atleast_2d(np.cov(points, rowvar=False, ddof=1))
    d = covariance.shape[0]
    target = np.eye(d) * (np.trace(covariance) / d)
    shrunk = (1.0 - SHRINKAGE) * covariance + SHRINKAGE * target
    eigvals, eigvecs = np.linalg.eigh(shrunk)
    floor = np.finfo(float).eps * max(1.0, float(np.max(np.abs(eigvals))))
    eigvals = np.maximum(eigvals, floor)
    return (eigvecs * (1.0 / np.sqrt(eigvals))) @ eigvecs.T


def _phase_summary(points: np.ndarray, whitener: np.ndarray) -> dict[str, float | int]:
    points = np.asarray(points, dtype=float)
    median = np.median(points, axis=0)
    centred = points - median
    white = points @ whitener
    return {
        "n_eligible": int(points.shape[0]),
        "radial_displacement": _finite_median(np.linalg.norm(points, axis=1)),
        "centre_displacement": float(np.linalg.norm(median)),
        "within_phase_dispersion": _finite_median(np.linalg.norm(centred, axis=1)),
        "whitened_radial_displacement": _finite_median(np.linalg.norm(white, axis=1)),
    }


def _paired_effects(table: pd.DataFrame) -> pd.DataFrame:
    metrics = ("radial_displacement", "centre_displacement", "within_phase_dispersion", "whitened_radial_displacement")
    rows: list[dict[str, Any]] = []
    for metric in metrics:
        wide = table.pivot(index="subject_id", columns="phase", values=metric)
        for phase in ORDERED_LATERS:
            diffs = (wide[phase] - wide[BASELINE_PHASE]).to_numpy(dtype=float)
            diffs = diffs[np.isfinite(diffs)]
            dz_lo, dz_hi, n_used = percentile_bootstrap(diffs, cohens_dz, n_boot=BOOTSTRAP_N, seed=BOOTSTRAP_SEED)
            med_lo, med_hi, _ = percentile_bootstrap(diffs, lambda v: float(np.median(v)), n_boot=BOOTSTRAP_N, seed=BOOTSTRAP_SEED)
            rows.append({
                "metric": metric, "phase": phase, "n_pairs": int(diffs.size),
                "median_paired_difference": _finite_median(diffs), "median_ci_lo": med_lo, "median_ci_hi": med_hi,
                "cohens_dz": cohens_dz(diffs), "dz_ci_lo": dz_lo, "dz_ci_hi": dz_hi,
                "bootstrap_n": BOOTSTRAP_N, "bootstrap_seed": BOOTSTRAP_SEED, "n_boot_used": n_used,
                "scientific_status": "post_hoc_exploratory_descriptive",
            })
    return pd.DataFrame(rows)


def _spearman_bootstrap(x: np.ndarray, y: np.ndarray) -> dict[str, float | int]:
    valid = np.isfinite(x) & np.isfinite(y)
    x, y = x[valid], y[valid]
    rho, p = spearman_rho_p(x, y)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    values = np.empty(BOOTSTRAP_N, dtype=float)
    for i in range(BOOTSTRAP_N):
        idx = rng.integers(0, x.size, size=x.size)
        values[i], _ = spearman_rho_p(x[idx], y[idx])
    values = values[np.isfinite(values)]
    return {"n": int(x.size), "rho": rho, "p": p, "ci_lo": float(np.percentile(values, 2.5)), "ci_hi": float(np.percentile(values, 97.5)), "bootstrap_n": BOOTSTRAP_N, "bootstrap_seed": BOOTSTRAP_SEED}


def _caliper_curve(cohort: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    base = cohort[cohort["protocol_phase_label"] == BASELINE_PHASE]
    later = cohort[cohort["protocol_phase_label"] == "first_protocol_sedation"]
    for subject in sorted(base["subject_id"].unique()):
        b = load_recording(str(base[base["subject_id"] == subject].iloc[0]["source_h5"]))
        l = load_recording(str(later[later["subject_id"] == subject].iloc[0]["source_h5"]))
        valid_base = np.isfinite(b["raw"]).all(axis=1)
        centre = np.median(b["raw"][valid_base], axis=0)
        mad = 1.4826 * np.median(np.abs(b["raw"][valid_base] - centre), axis=0)
        b_points, _ = _frame_points(b["raw"], b["time"], centre, mad)
        l_points, _ = _frame_points(l["raw"], l["time"], centre, mad)
        base_caliper = median_loo_nn(b_points)
        for multiplier in CALIPER_MULTIPLIERS:
            _, _, distances = greedy_match(l_points, b_points, multiplier * base_caliper)
            n_pairs = int(distances.size)
            rows.append({"subject_id": subject, "caliper_multiplier": multiplier, "base_caliper": base_caliper, "caliper": multiplier * base_caliper, "n_pairs": n_pairs, "included_at_20_pairs": n_pairs >= MIN_PAIRS})
    return pd.DataFrame(rows)


def _write_summary(path: Path, effects: pd.DataFrame, support: pd.DataFrame, association: dict[str, Any]) -> None:
    first = effects[(effects.metric == "radial_displacement") & (effects.phase == "first_protocol_sedation")].iloc[0]
    centre = effects[(effects.metric == "centre_displacement") & (effects.phase == "first_protocol_sedation")].iloc[0]
    dispersion = effects[(effects.metric == "within_phase_dispersion") & (effects.phase == "first_protocol_sedation")].iloc[0]
    white = effects[(effects.metric == "whitened_radial_displacement") & (effects.phase == "first_protocol_sedation")].iloc[0]
    lines = [
        f"# PR-01 geometric dissection ({ANALYSIS_VERSION})", "",
        "Post-hoc exploratory branch. It does not replace the frozen radial-displacement analysis or open G3/G4.", "",
        "## First-sedation versus baseline", "",
        f"Frozen-frame radial displacement: median delta {first.median_paired_difference:.3g}, d_z {first.cohens_dz:.3g}.",
        f"Phase-cloud centre displacement: median delta {centre.median_paired_difference:.3g}, d_z {centre.cohens_dz:.3g}.",
        f"Within-phase dispersion: median delta {dispersion.median_paired_difference:.3g}, d_z {dispersion.cohens_dz:.3g}.",
        f"10% shrinkage-whitened radial displacement: median delta {white.median_paired_difference:.3g}, d_z {white.cohens_dz:.3g}.", "",
        "## C3 caliper support diagnostic", "",
        "| Multiplier | participants with >=20 pairs |", "| ---: | ---: |",
    ]
    for mult, grp in support.groupby("caliper_multiplier", sort=True):
        lines.append(f"| {mult:g} | {int(grp['included_at_20_pairs'].sum())}/{len(grp)} |")
    lines.extend(["", "## Behaviour association uncertainty", "", f"Spearman rho={association['rho']:.3g}, 95% bootstrap CI [{association['ci_lo']:.3g}, {association['ci_hi']:.3g}], n={association['n']}. This interval is descriptive and does not test equivalence.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(*, labels_path: Path, support_path: Path, output_root: Path) -> dict[str, Any]:
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"output root must be new and empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    cohort = load_cohort(labels_path, support_path)
    base = cohort[cohort["protocol_phase_label"] == BASELINE_PHASE]
    rows: list[dict[str, Any]] = []
    feature_rows: list[dict[str, Any]] = []
    for subject in sorted(base["subject_id"].unique()):
        baseline = load_recording(str(base[base["subject_id"] == subject].iloc[0]["source_h5"]))
        finite = np.isfinite(baseline["raw"]).all(axis=1)
        centre = np.median(baseline["raw"][finite], axis=0)
        scale = 1.4826 * np.median(np.abs(baseline["raw"][finite] - centre), axis=0)
        baseline_points, _ = _frame_points(baseline["raw"], baseline["time"], centre, scale)
        whitener = _whitener(baseline_points)
        for phase in (BASELINE_PHASE, *ORDERED_LATERS):
            recrow = cohort[(cohort["subject_id"] == subject) & (cohort["protocol_phase_label"] == phase)].iloc[0]
            rec = load_recording(str(recrow["source_h5"]))
            points, _ = _frame_points(rec["raw"], rec["time"], centre, scale)
            rows.append({"subject_id": subject, "phase": phase, "source_h5": rec["source_h5"], **_phase_summary(points, whitener)})
            point_median = np.median(points, axis=0)
            for feature, value in zip(SPECTRAL_FEATURES, point_median, strict=True):
                feature_rows.append({"subject_id": subject, "phase": phase, "feature": feature, "phase_median_baseline_z": float(value), "n_eligible": int(points.shape[0])})
    phases = pd.DataFrame(rows)
    feature_subject = pd.DataFrame(feature_rows)
    feature_cohort = feature_subject.groupby(["phase", "feature"], as_index=False).agg(
        cohort_median_baseline_z=("phase_median_baseline_z", "median"),
        n_subjects=("subject_id", "nunique"),
    )
    effects = _paired_effects(phases)
    support = _caliper_curve(cohort)
    lor = pd.read_csv(ARTICLE_DIR / "results" / "v1_lor_20260921" / "lor_occupancy_joined.csv")
    association = _spearman_bootstrap(pd.to_numeric(lor["occupancy_later_protocol_sedation"], errors="coerce").to_numpy(), pd.to_numeric(lor["n_correct_later_protocol_sedation"], errors="coerce").to_numpy())
    phases.to_csv(output_root / "geometric_subject_phase.csv", index=False)
    feature_subject.to_csv(output_root / "feature_phase_subject_medians.csv", index=False)
    feature_cohort.to_csv(output_root / "feature_phase_cohort_medians.csv", index=False)
    effects.to_csv(output_root / "geometric_paired_effects.csv", index=False)
    support.to_csv(output_root / "caliper_sensitivity.csv", index=False)
    pd.DataFrame([association]).to_csv(output_root / "behaviour_association_uncertainty.csv", index=False)
    _write_summary(output_root / "pr01_geometric_summary.md", effects, support, association)
    output_files = sorted(path for path in output_root.iterdir() if path.is_file())
    manifest = {"schema": "apollo_propofol_ndt_v1.pr01_geometric.v1", "analysis_version": ANALYSIS_VERSION, "created_at": datetime.now(timezone.utc).isoformat(), "status": "post_hoc_exploratory", "measurement_boundary": "frozen eight-feature baseline robust-z frame and source eligibility preserved", "parameters": {"shrinkage": SHRINKAGE, "caliper_multipliers": CALIPER_MULTIPLIERS, "bootstrap_n": BOOTSTRAP_N, "bootstrap_seed": BOOTSTRAP_SEED, "participant_unit": True}, "inputs": {"labels": {"path": str(labels_path), "sha256": sha256_file(labels_path)}, "support": {"path": str(support_path), "sha256": sha256_file(support_path)}, "plan": {"path": str(PLAN_PATH), "sha256": sha256_file(PLAN_PATH)}, "frozen_occupancy": {"path": str(ARTICLE_DIR / 'results' / 'v1_occupancy_20260921' / 'occupancy_subject.csv'), "sha256": sha256_file(ARTICLE_DIR / 'results' / 'v1_occupancy_20260921' / 'occupancy_subject.csv')}}, "code_sha256": sha256_file(Path(__file__)), "outputs_sha256": {path.name: sha256_file(path) for path in output_files}, "claim_boundary": "centre/spread and whitening are chart-level exploratory sensitivity results; neither proves latent relocation or a changed future law"}
    write_json(output_root / "pr01_geometric_manifest.json", json_safe(manifest))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=LABELS_DEFAULT)
    parser.add_argument("--support", type=Path, default=SUPPORT_DEFAULT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args(argv)
    print(json.dumps(run(labels_path=args.labels, support_path=args.support, output_root=args.output_root), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
