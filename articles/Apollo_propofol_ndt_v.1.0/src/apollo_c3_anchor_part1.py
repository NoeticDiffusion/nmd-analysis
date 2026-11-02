"""Baseline-anchored matched-state C3. Exploratory; G4 not locked.

Uses features_raw with a baseline-only robust-z frame, then the same
caliper matching rule as the local-chart C3 run.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

from apollo_c3_match import (
    baseline_center_scale,
    decode_names,
    feature_increments,
    match_subject,
    robust_z,
)
from apollo_c3_panel import (
    BOOTSTRAP_N,
    BOOTSTRAP_SEED,
    CONFIRMATORY_STATUS,
    EARLIER_PHASE,
    FEATURE_NAMES_PATH,
    FEATURE_VALUES_PATH,
    LATER_PHASE,
    MIN_TESTABLE_N,
    PRIMARY_ENDPOINTS,
    SPECTRAL_FEATURES,
)
from apollo_c3_part1 import _fmt, contrast_from_subjects
from apollo_common import ARTICLE_DIR, DEFAULT_H5_ROOT, json_safe, sha256_file, write_json
from apollo_stage_part1 import LABELS_DEFAULT, SUPPORT_DEFAULT, load_cohort
from apollo_stats import holm

ANALYSIS_ID = "matched_state_c3_baseline_anchor_20260921"
OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_c3_anchor_20260921"
RECOVERY_PHASE = "recovery"
TIME_PATH = "time"


def _read(handle: h5py.File, path: str) -> np.ndarray:
    return np.asarray(handle[path][()])


def load_recording(path: str) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        names = decode_names(_read(handle, FEATURE_NAMES_PATH))
        features = np.asarray(_read(handle, FEATURE_VALUES_PATH), dtype=float)
        columns = [names.index(name) for name in SPECTRAL_FEATURES]
        return {
            "source_h5": path,
            "raw": features[:, columns],
            "time": np.asarray(_read(handle, TIME_PATH), dtype=float),
        }


def anchored_series(raw: np.ndarray, time: np.ndarray, center: np.ndarray, scale: np.ndarray) -> dict[str, np.ndarray]:
    z = robust_z(raw, center, scale)
    dxdt, valid, dt = feature_increments(z, time)
    return {"z": z, "dxdt": dxdt, "valid": valid, "dt": dt}


def write_part1(path: Path, subjects: pd.DataFrame, recovery: pd.DataFrame, contrasts: pd.DataFrame) -> None:
    lines = [
        f"# Apollo baseline-anchored matched-state C3 ({ANALYSIS_ID})",
        "",
        "First protocol sedation minus pre-drug baseline in a baseline-only robust-z "
        "frame of the eight MNPS-used features_raw columns. Matching is outcome-blind. "
        f"Status: `{CONFIRMATORY_STATUS}`. Not consciousness. Not confirmatory amplitude.",
        "",
        f"Subjects included: {int(subjects['included'].sum())}/20. "
        f"Bootstrap {BOOTSTRAP_N}, seed {BOOTSTRAP_SEED}.",
        "",
        "## Support",
        "",
        "| Subject | n later eligible | n baseline eligible | n pairs | match frac | caliper | median d | included |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in subjects.sort_values("subject_id").iterrows():
        lines.append(
            "| {sid} | {nl} | {ne} | {npairs} | {frac} | {cal} | {md} | {inc} |".format(
                sid=row["subject_id"],
                nl=int(row["n_later_eligible"]),
                ne=int(row["n_earlier_eligible"]),
                npairs=int(row["n_pairs"]),
                frac=_fmt(row["match_fraction"], 3),
                cal=_fmt(row["caliper"], 3),
                md=_fmt(row["median_match_distance"], 3),
                inc="yes" if bool(row["included"]) else "no",
            )
        )
    lines.extend(
        [
            "",
            "## Contrasts (Holm only on matched speed and spread)",
            "",
            "| Family | Metric | n | later med | base med | Δ med | d_z | sign p | Wilcoxon p | Holm p |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in contrasts.iterrows():
        holm_txt = _fmt(row["holm_p"]) if pd.notna(row.get("holm_p")) else "-"
        lines.append(
            "| {fam} | `{metric}` | {n} | {later} | {base} | {delta} | {d} | {sp} | {wp} | {hp} |".format(
                fam=row["family"],
                metric=row["metric"],
                n=int(row["n_pairs"]),
                later=_fmt(row["later_median"]),
                base=_fmt(row["earlier_median"]),
                delta=_fmt(row["median_paired_difference"]),
                d=_fmt(row["cohens_dz"], 3),
                sp=_fmt(row["sign_test_p"]),
                wp=_fmt(row["wilcoxon_p"]),
                hp=holm_txt,
            )
        )
    lines.extend(
        [
            "",
            "Occupancy is median Euclidean radius in baseline-z. Unmatched occupancy "
            "asks whether sedation leaves the awake neighbourhood. Matched occupancy "
            "is a QC that the paired states are similarly far from origin.",
            "",
            f"Recovery unmatched is available for {int(len(recovery))} subjects and is not Holm.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(*, labels_path: Path, support_path: Path, output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    cohort = load_cohort(labels_path, support_path)
    later = cohort[cohort["protocol_phase_label"] == LATER_PHASE]
    earlier = cohort[cohort["protocol_phase_label"] == EARLIER_PHASE]
    recovery = cohort[cohort["protocol_phase_label"] == RECOVERY_PHASE]
    subjects = sorted(set(later["subject_id"]) & set(earlier["subject_id"]))
    rows = []
    recovery_rows = []
    for subject in subjects:
        rec_l = load_recording(str(later.loc[later["subject_id"] == subject, "source_h5"].iloc[0]))
        rec_e = load_recording(str(earlier.loc[earlier["subject_id"] == subject, "source_h5"].iloc[0]))
        finite_base = np.isfinite(rec_e["raw"]).all(axis=1)
        center, scale = baseline_center_scale(rec_e["raw"][finite_base])
        anchored_l = anchored_series(rec_l["raw"], rec_l["time"], center, scale)
        anchored_e = anchored_series(rec_e["raw"], rec_e["time"], center, scale)
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
        matched["subject_id"] = subject
        matched["later_h5"] = rec_l["source_h5"]
        matched["earlier_h5"] = rec_e["source_h5"]
        rows.append(matched)

        rec_r = recovery.loc[recovery["subject_id"] == subject]
        if len(rec_r):
            rec_rec = load_recording(str(rec_r["source_h5"].iloc[0]))
            anchored_r = anchored_series(rec_rec["raw"], rec_rec["time"], center, scale)
            rec_match = match_subject(
                anchored_r["z"],
                anchored_e["z"],
                anchored_r["dxdt"],
                anchored_e["dxdt"],
                anchored_r["valid"],
                anchored_e["valid"],
                anchored_r["dt"],
                anchored_e["dt"],
            )
            rec_match["subject_id"] = subject
            recovery_rows.append(rec_match)

    subjects_tbl = pd.DataFrame(rows)
    recovery_tbl = pd.DataFrame(recovery_rows)
    subjects_tbl.to_csv(output_root / "c3_anchor_subject.csv", index=False)
    recovery_tbl.to_csv(output_root / "c3_anchor_recovery.csv", index=False)

    contrast_rows = [
        contrast_from_subjects(subjects_tbl, "matched_speed_later", "matched_speed_earlier", "matched_speed", "matched_anchor"),
        contrast_from_subjects(subjects_tbl, "matched_spread_later", "matched_spread_earlier", "matched_spread", "matched_anchor"),
        contrast_from_subjects(subjects_tbl, "unmatched_speed_later", "unmatched_speed_earlier", "unmatched_speed", "unmatched_anchor"),
        contrast_from_subjects(subjects_tbl, "unmatched_spread_later", "unmatched_spread_earlier", "unmatched_spread", "unmatched_anchor"),
        contrast_from_subjects(subjects_tbl, "unmatched_occupancy_later", "unmatched_occupancy_earlier", "unmatched_occupancy", "unmatched_anchor"),
        contrast_from_subjects(subjects_tbl, "matched_occupancy_later", "matched_occupancy_earlier", "matched_occupancy", "matched_anchor_qc"),
        contrast_from_subjects(subjects_tbl, "random_speed_later", "random_speed_earlier", "random_speed", "random_anchor"),
        contrast_from_subjects(subjects_tbl, "random_spread_later", "random_spread_earlier", "random_spread", "random_anchor"),
    ]
    if len(recovery_tbl):
        for metric in ("unmatched_speed", "unmatched_spread", "unmatched_occupancy"):
            row = contrast_from_subjects(
                recovery_tbl, f"{metric}_later", f"{metric}_earlier", metric, "unmatched_recovery"
            )
            row["later_phase"] = RECOVERY_PHASE
            row["contrast_id"] = "recovery_minus_baseline"
            contrast_rows.append(row)
    table = pd.DataFrame(contrast_rows)
    table["holm_p"] = np.nan
    primary_idx = table.index[table["family"].eq("matched_anchor") & table["metric"].isin(PRIMARY_ENDPOINTS)]
    if len(primary_idx):
        table.loc[list(primary_idx), "holm_p"] = holm(table.loc[list(primary_idx), "sign_test_p"].to_numpy())
    table.to_csv(output_root / "c3_anchor_contrasts.csv", index=False)
    write_part1(output_root / "c3_anchor_part1.md", subjects_tbl, recovery_tbl, table)

    primary = table[table["family"] == "matched_anchor"]
    unmatched = table[table["family"] == "unmatched_anchor"]
    manifest = {
        "schema": "apollo_propofol_ndt_v1.matched_state_c3_baseline_anchor.v1",
        "analysis_id": ANALYSIS_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "confirmatory_status": CONFIRMATORY_STATUS,
        "confirmatory_contrasts": False,
        "n_subjects": int(len(subjects_tbl)),
        "n_included": int(subjects_tbl["included"].sum()),
        "n_holm_lt_0_05": int(((primary["holm_p"] < 0.05) & (primary["n_pairs"] >= MIN_TESTABLE_N)).sum()),
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "labels_sha256": sha256_file(labels_path) if labels_path.is_file() else None,
        "h5_root": str(DEFAULT_H5_ROOT),
        "primary": primary[
            ["metric", "n_pairs", "median_paired_difference", "cohens_dz", "sign_test_p", "wilcoxon_p", "holm_p"]
        ].to_dict("records"),
        "unmatched": unmatched[
            ["metric", "n_pairs", "median_paired_difference", "cohens_dz", "sign_test_p", "wilcoxon_p"]
        ].to_dict("records"),
        "note": (
            "Baseline-only robust-z frame on features_raw. Same caliper matching "
            "as local-chart C3. G3/G4 not locked."
        ),
    }
    write_json(output_root / "c3_anchor_part1_manifest.json", json_safe(manifest))
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
        "n_included": manifest.get("n_included"),
        "n_holm_lt_0_05": manifest.get("n_holm_lt_0_05"),
        "primary": manifest.get("primary"),
        "unmatched": manifest.get("unmatched"),
        "confirmatory_status": manifest.get("confirmatory_status"),
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
