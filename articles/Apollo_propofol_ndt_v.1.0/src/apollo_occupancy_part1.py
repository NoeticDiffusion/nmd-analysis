"""Occupancy / state relocation in the frozen baseline-z frame.

Promotes the exact unmatched occupancy scalar from the C3-anchor pipeline.
No new metrics. Exploratory; G4 not locked.
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
from apollo_c3_match import baseline_center_scale, match_subject
from apollo_c3_panel import BOOTSTRAP_N, BOOTSTRAP_SEED, MIN_TESTABLE_N
from apollo_common import ARTICLE_DIR, DEFAULT_H5_ROOT, json_safe, sha256_file, write_json
from apollo_occupancy_panel import (
    ANALYSIS_ID,
    BASELINE_PHASE,
    C3_ANCHOR_SUBJECTS,
    CONFIRMATORY_STATUS,
    ORDERED_LATERS,
    PREDICTION_PRIMARY,
    PRIMARY_CONTRAST_ID,
    PRIMARY_LATER_PHASE,
)
from apollo_stage_part1 import LABELS_DEFAULT, SUPPORT_DEFAULT, load_cohort
from apollo_stats import cohens_dz, exact_sign_test_p, percentile_bootstrap, wilcoxon_p

OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_occupancy_20260921"
CONTRAST_IDS = {
    "first_protocol_sedation": "first_sedation_minus_baseline",
    "later_protocol_sedation": "later_sedation_minus_baseline",
    "recovery": "recovery_minus_baseline",
}


def _fmt(value: float, digits: int = 4) -> str:
    if value is None or not np.isfinite(value):
        return "nan"
    return f"{value:.{digits}g}"


def occupancy_contrast(
    table: pd.DataFrame,
    later_col: str,
    earlier_col: str,
    *,
    contrast_id: str,
    later_phase: str,
    primary: bool,
) -> dict[str, Any]:
    later = pd.to_numeric(table[later_col], errors="coerce")
    earlier = pd.to_numeric(table[earlier_col], errors="coerce")
    diffs = later - earlier
    finite = diffs[np.isfinite(diffs)]
    n_pairs = int(len(finite))
    dz = cohens_dz(finite.to_numpy())
    dz_lo, dz_hi, _ = percentile_bootstrap(finite.to_numpy(), cohens_dz, n_boot=BOOTSTRAP_N, seed=BOOTSTRAP_SEED)
    med_lo, med_hi, n_boot = percentile_bootstrap(
        finite.to_numpy(), lambda sample: float(np.median(sample)), n_boot=BOOTSTRAP_N, seed=BOOTSTRAP_SEED
    )
    return {
        "family": "occupancy_relocation",
        "metric": "unmatched_occupancy",
        "contrast_id": contrast_id,
        "later_phase": later_phase,
        "earlier_phase": BASELINE_PHASE,
        "primary_contrast": primary,
        "prediction": PREDICTION_PRIMARY if primary else "two-sided descriptive",
        "n_pairs": n_pairs,
        "n_negative": int(np.sum(finite.to_numpy() < 0)),
        "n_positive": int(np.sum(finite.to_numpy() > 0)),
        "n_zero": int(np.sum(finite.to_numpy() == 0)),
        "later_median": float(np.median(later.dropna())) if later.notna().any() else float("nan"),
        "earlier_median": float(np.median(earlier.dropna())) if earlier.notna().any() else float("nan"),
        "median_paired_difference": float(np.median(finite)) if n_pairs else float("nan"),
        "mean_paired_difference": float(np.mean(finite)) if n_pairs else float("nan"),
        "median_diff_ci_lo": med_lo,
        "median_diff_ci_hi": med_hi,
        "cohens_dz": dz,
        "cohens_dz_ci_lo": dz_lo,
        "cohens_dz_ci_hi": dz_hi,
        "sign_test_p": exact_sign_test_p(finite.to_numpy()),
        "wilcoxon_p": wilcoxon_p(finite.to_numpy()),
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "n_boot_used": n_boot,
        "family_testable": n_pairs >= MIN_TESTABLE_N,
        "confirmatory_status": CONFIRMATORY_STATUS,
    }


def write_part1(path: Path, subjects: pd.DataFrame, contrasts: pd.DataFrame, support: pd.DataFrame) -> None:
    primary = contrasts[contrasts["primary_contrast"] == True]  # noqa: E712
    lines = [
        f"# Apollo occupancy / state relocation ({ANALYSIS_ID})",
        "",
        "Median Euclidean radius in the baseline-only robust-z frame of the eight "
        "MNPS-used features_raw columns. Exact scalar from the C3-anchor pipeline. "
        f"Status: `{CONFIRMATORY_STATUS}`. Promoted after sl_003/sl_004. "
        "Not consciousness. Not NDT-C3. Not confirmatory local-chart b/a.",
        "",
        f"n subjects = {int(len(subjects))}. Bootstrap {BOOTSTRAP_N}, seed {BOOTSTRAP_SEED}.",
        "",
        "## Occupancy by protocol phase",
        "",
        "| Subject | baseline | first sedation | later sedation | recovery |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for _, row in subjects.sort_values("subject_id").iterrows():
        lines.append(
            "| {sid} | {b} | {f} | {l} | {r} |".format(
                sid=row["subject_id"],
                b=_fmt(row["occupancy_pre_drug_baseline"]),
                f=_fmt(row["occupancy_first_protocol_sedation"]),
                l=_fmt(row["occupancy_later_protocol_sedation"]),
                r=_fmt(row["occupancy_recovery"]),
            )
        )
    lines.extend(
        [
            "",
            "## Contrasts versus baseline",
            "",
            "| Role | Contrast | n | later med | base med | Δ med | d_z | n+ | n− | sign p | Wilcoxon p |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in contrasts.iterrows():
        lines.append(
            "| {role} | `{cid}` | {n} | {later} | {base} | {delta} | {d} | {npos} | {nneg} | {sp} | {wp} |".format(
                role="primary" if bool(row["primary_contrast"]) else "secondary",
                cid=row["contrast_id"],
                n=int(row["n_pairs"]),
                later=_fmt(row["later_median"]),
                base=_fmt(row["earlier_median"]),
                delta=_fmt(row["median_paired_difference"]),
                d=_fmt(row["cohens_dz"], 3),
                npos=int(row["n_positive"]),
                nneg=int(row["n_negative"]),
                sp=_fmt(row["sign_test_p"]),
                wp=_fmt(row["wilcoxon_p"]),
            )
        )
    if not support.empty:
        n_included = int(support["included"].sum()) if "included" in support.columns else 0
        lines.extend(
            [
                "",
                "## Why C3 is NOT_TESTABLE (baseline-anchor match support)",
                "",
                f"Subjects with ≥20 caliper-matched pairs: {n_included}/20. "
                "This table is copied from the frozen C3-anchor run; occupancy is not rematched.",
                "",
                "| Subject | n pairs | match frac | included |",
                "| --- | ---: | ---: | --- |",
            ]
        )
        for _, row in support.sort_values("subject_id").iterrows():
            lines.append(
                "| {sid} | {npairs} | {frac} | {inc} |".format(
                    sid=row["subject_id"],
                    npairs=int(row["n_pairs"]),
                    frac=_fmt(row["match_fraction"], 3),
                    inc="yes" if bool(row["included"]) else "no",
                )
            )
    if not primary.empty:
        p = primary.iloc[0]
        lines.extend(
            [
                "",
                "Primary prediction is later > earlier (relocation away from the awake "
                "neighbourhood). Local-chart L1 b/a remains discovery. NDT-C3 remains OPEN.",
                "",
                f"Primary sign test: p = {_fmt(p['sign_test_p'])}, d_z = {_fmt(p['cohens_dz'], 3)}, "
                f"{int(p['n_positive'])}/20 increase.",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(*, labels_path: Path, support_path: Path, output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    cohort = load_cohort(labels_path, support_path)
    baseline = cohort[cohort["protocol_phase_label"] == BASELINE_PHASE]
    subjects = sorted(baseline["subject_id"].unique())
    rows = []
    for subject in subjects:
        rec_e = load_recording(str(baseline.loc[baseline["subject_id"] == subject, "source_h5"].iloc[0]))
        finite_base = np.isfinite(rec_e["raw"]).all(axis=1)
        center, scale = baseline_center_scale(rec_e["raw"][finite_base])
        anchored_e = anchored_series(rec_e["raw"], rec_e["time"], center, scale)
        row: dict[str, Any] = {
            "subject_id": subject,
            "baseline_h5": rec_e["source_h5"],
        }
        for later_phase in ORDERED_LATERS:
            later = cohort[
                (cohort["subject_id"] == subject) & (cohort["protocol_phase_label"] == later_phase)
            ]
            if later.empty:
                row[f"occupancy_{later_phase}"] = float("nan")
                continue
            rec_l = load_recording(str(later["source_h5"].iloc[0]))
            anchored_l = anchored_series(rec_l["raw"], rec_l["time"], center, scale)
            matched = match_subject(
                anchored_l["z"],
                anchored_e["z"],
                anchored_l["dxdt"],
                anchored_e["dxdt"],
                anchored_l["valid"],
                anchored_e["valid"],
                anchored_l["dt"],
                anchored_e["dt"],
            )
            row[f"occupancy_{later_phase}"] = matched["unmatched_occupancy_later"]
            row["occupancy_pre_drug_baseline"] = matched["unmatched_occupancy_earlier"]
            row[f"n_eligible_{later_phase}"] = matched["n_later_eligible"]
        row["n_eligible_pre_drug_baseline"] = matched["n_earlier_eligible"]
        rows.append(row)
    table = pd.DataFrame(rows)
    table.to_csv(output_root / "occupancy_subject.csv", index=False)

    contrast_rows = [
        occupancy_contrast(
            table,
            f"occupancy_{phase}",
            "occupancy_pre_drug_baseline",
            contrast_id=CONTRAST_IDS[phase],
            later_phase=phase,
            primary=phase == PRIMARY_LATER_PHASE,
        )
        for phase in ORDERED_LATERS
        if f"occupancy_{phase}" in table.columns
    ]
    contrasts = pd.DataFrame(contrast_rows)
    contrasts.to_csv(output_root / "occupancy_contrasts.csv", index=False)

    support_path_c3 = ARTICLE_DIR / C3_ANCHOR_SUBJECTS
    support = pd.read_csv(support_path_c3) if support_path_c3.is_file() else pd.DataFrame()
    if not support.empty:
        support.to_csv(output_root / "c3_anchor_match_support.csv", index=False)
    write_part1(output_root / "occupancy_part1.md", table, contrasts, support)

    primary = contrasts[contrasts["contrast_id"] == PRIMARY_CONTRAST_ID].iloc[0]
    manifest = {
        "schema": "apollo_propofol_ndt_v1.occupancy_relocation.v1",
        "analysis_id": ANALYSIS_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "confirmatory_status": CONFIRMATORY_STATUS,
        "confirmatory_contrasts": False,
        "promoted_after": ["sl_003", "sl_004"],
        "n_subjects": int(len(table)),
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "labels_sha256": sha256_file(labels_path) if labels_path.is_file() else None,
        "h5_root": str(DEFAULT_H5_ROOT),
        "primary": {
            "contrast_id": PRIMARY_CONTRAST_ID,
            "n_pairs": int(primary["n_pairs"]),
            "n_positive": int(primary["n_positive"]),
            "n_negative": int(primary["n_negative"]),
            "median_paired_difference": float(primary["median_paired_difference"]),
            "cohens_dz": float(primary["cohens_dz"]),
            "sign_test_p": float(primary["sign_test_p"]),
            "wilcoxon_p": float(primary["wilcoxon_p"]),
            "family_testable": bool(primary["family_testable"]),
        },
        "secondaries": contrasts.loc[
            contrasts["primary_contrast"] == False,  # noqa: E712
            ["contrast_id", "n_pairs", "median_paired_difference", "cohens_dz", "sign_test_p", "wilcoxon_p"],
        ].to_dict("records"),
        "c3_n_included": int(support["included"].sum()) if not support.empty else None,
        "note": (
            "Exact unmatched occupancy scalar from the baseline-anchor pipeline, "
            "promoted to the article primary line. G3/G4 not locked. NDT-C3 OPEN."
        ),
    }
    write_json(output_root / "occupancy_part1_manifest.json", json_safe(manifest))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=LABELS_DEFAULT)
    parser.add_argument("--support", type=Path, default=SUPPORT_DEFAULT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args(argv)
    manifest = run(labels_path=args.labels, support_path=args.support, output_root=args.output_root)
    print(json.dumps({
        "output_root": str(args.output_root),
        "primary": manifest.get("primary"),
        "secondaries": manifest.get("secondaries"),
        "c3_n_included": manifest.get("c3_n_included"),
        "confirmatory_status": manifest.get("confirmatory_status"),
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
