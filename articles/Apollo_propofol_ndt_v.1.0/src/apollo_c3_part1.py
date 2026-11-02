"""Matched-state first-sedation vs baseline increment test (NDT-C3 analogue).

Exploratory; G4 not locked. Chart matching is outcome-blind.
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

from apollo_c3_match import baseline_center_scale, decode_names, eligible_mask, match_subject, robust_z
from apollo_c3_panel import (
    ANALYSIS_ID,
    BOOTSTRAP_N,
    BOOTSTRAP_SEED,
    CONFIRMATORY_STATUS,
    CONTRAST_ID,
    COORD_PATH,
    DXDT_DT_PATH,
    DXDT_PATH,
    DXDT_VALID_PATH,
    EARLIER_PHASE,
    FEATURE_NAMES_PATH,
    FEATURE_VALUES_PATH,
    LATER_PHASE,
    MIN_TESTABLE_N,
    PRIMARY_ENDPOINTS,
    SPECTRAL_FEATURES,
)
from apollo_common import ARTICLE_DIR, DEFAULT_H5_ROOT, json_safe, sha256_file, write_json
from apollo_stage_part1 import LABELS_DEFAULT, SUPPORT_DEFAULT, load_cohort
from apollo_stats import cohens_dz, exact_sign_test_p, holm, percentile_bootstrap, wilcoxon_p

OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_c3_20260921"


def _read(handle: h5py.File, path: str) -> np.ndarray:
    return np.asarray(handle[path][()])


def load_recording(path: str) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        names = decode_names(_read(handle, FEATURE_NAMES_PATH))
        features = np.asarray(_read(handle, FEATURE_VALUES_PATH), dtype=float)
        columns = [names.index(name) for name in SPECTRAL_FEATURES]
        return {
            "source_h5": path,
            "x": np.asarray(_read(handle, COORD_PATH), dtype=float),
            "dxdt": np.asarray(_read(handle, DXDT_PATH), dtype=float),
            "valid": np.asarray(_read(handle, DXDT_VALID_PATH), dtype=float),
            "dt": np.asarray(_read(handle, DXDT_DT_PATH), dtype=float),
            "spectral": features[:, columns],
        }


def _fmt(value: float, digits: int = 4) -> str:
    if value is None or not np.isfinite(value):
        return "nan"
    return f"{value:.{digits}g}"


def contrast_from_subjects(table: pd.DataFrame, later_col: str, earlier_col: str, metric: str, family: str) -> dict[str, Any]:
    later = pd.to_numeric(table[later_col], errors="coerce")
    earlier = pd.to_numeric(table[earlier_col], errors="coerce")
    diffs = later - earlier
    finite = diffs[np.isfinite(diffs)]
    n_pairs = int(len(finite))
    testable = n_pairs >= MIN_TESTABLE_N
    dz = cohens_dz(finite.to_numpy())
    dz_lo, dz_hi, _ = percentile_bootstrap(finite.to_numpy(), cohens_dz, n_boot=BOOTSTRAP_N, seed=BOOTSTRAP_SEED)
    med_lo, med_hi, n_boot = percentile_bootstrap(
        finite.to_numpy(), lambda sample: float(np.median(sample)), n_boot=BOOTSTRAP_N, seed=BOOTSTRAP_SEED
    )
    return {
        "family": family,
        "metric": metric,
        "contrast_id": CONTRAST_ID,
        "later_phase": LATER_PHASE,
        "earlier_phase": EARLIER_PHASE,
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
        "family_testable": testable,
        "confirmatory_status": CONFIRMATORY_STATUS,
        "prediction": "later < earlier",
    }


def write_part1(path: Path, subjects: pd.DataFrame, contrasts: pd.DataFrame) -> None:
    primary = contrasts[contrasts["family"] == "matched_mnps"]
    lines = [
        f"# Apollo matched-state C3 ({ANALYSIS_ID})",
        "",
        "First protocol sedation minus pre-drug baseline at greedy caliper-matched "
        "present MNPS locations. Matching is outcome-blind. Status: "
        f"`{CONFIRMATORY_STATUS}`. Not consciousness. Not confirmatory amplitude. "
        "Not identified Itô drift/diffusion.",
        "",
        f"Subjects included: {int(subjects['included'].sum())}/20. "
        f"Caliper = median baseline LOO nearest-neighbour distance. "
        f"Minimum {20} matched pairs. Bootstrap {BOOTSTRAP_N}, seed {BOOTSTRAP_SEED}.",
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
            "## Contrasts (Holm only on matched MNPS speed and spread)",
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
            "Random-match ignores present x but keeps the matched pair count. "
            "Unmatched uses all eligible sources. Spectral matching concatenates "
            "baseline-robust-z MNPS-used EEG features.",
            "",
            "Local recording fits mean this is same-chart-coordinate matching, not a "
            "documented cross-phase physical anchor.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(*, labels_path: Path, support_path: Path, output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    cohort = load_cohort(labels_path, support_path)
    later = cohort[cohort["protocol_phase_label"] == LATER_PHASE].copy()
    earlier = cohort[cohort["protocol_phase_label"] == EARLIER_PHASE].copy()
    subjects = sorted(set(later["subject_id"]) & set(earlier["subject_id"]))
    rows = []
    spectral_rows = []
    for subject in subjects:
        later_path = str(later.loc[later["subject_id"] == subject, "source_h5"].iloc[0])
        earlier_path = str(earlier.loc[earlier["subject_id"] == subject, "source_h5"].iloc[0])
        rec_l = load_recording(later_path)
        rec_e = load_recording(earlier_path)
        mnps = match_subject(
            rec_l["x"], rec_e["x"], rec_l["dxdt"], rec_e["dxdt"],
            rec_l["valid"], rec_e["valid"], rec_l["dt"], rec_e["dt"],
        )
        mnps["subject_id"] = subject
        mnps["later_h5"] = later_path
        mnps["earlier_h5"] = earlier_path
        rows.append(mnps)

        later_ok = eligible_mask(rec_l["x"], rec_l["dxdt"], rec_l["valid"], rec_l["dt"])
        earlier_ok = eligible_mask(rec_e["x"], rec_e["dxdt"], rec_e["valid"], rec_e["dt"])
        center, scale = baseline_center_scale(rec_e["spectral"][earlier_ok])
        later_spec = np.concatenate(
            [rec_l["x"][later_ok], robust_z(rec_l["spectral"][later_ok], center, scale)],
            axis=1,
        )
        earlier_spec = np.concatenate(
            [rec_e["x"][earlier_ok], robust_z(rec_e["spectral"][earlier_ok], center, scale)],
            axis=1,
        )
        spec = match_subject(
            rec_l["x"], rec_e["x"], rec_l["dxdt"], rec_e["dxdt"],
            rec_l["valid"], rec_e["valid"], rec_l["dt"], rec_e["dt"],
            later_match=later_spec,
            earlier_match=earlier_spec,
        )
        spec["subject_id"] = subject
        spectral_rows.append(spec)

    subjects_mnps = pd.DataFrame(rows)
    subjects_spec = pd.DataFrame(spectral_rows)
    subjects_mnps.to_csv(output_root / "c3_subject_mnps.csv", index=False)
    subjects_spec.to_csv(output_root / "c3_subject_spectral.csv", index=False)

    contrast_rows = [
        contrast_from_subjects(subjects_mnps, "matched_speed_later", "matched_speed_earlier", "matched_speed", "matched_mnps"),
        contrast_from_subjects(subjects_mnps, "matched_spread_later", "matched_spread_earlier", "matched_spread", "matched_mnps"),
        contrast_from_subjects(subjects_mnps, "unmatched_speed_later", "unmatched_speed_earlier", "unmatched_speed", "unmatched"),
        contrast_from_subjects(subjects_mnps, "unmatched_spread_later", "unmatched_spread_earlier", "unmatched_spread", "unmatched"),
        contrast_from_subjects(subjects_mnps, "random_speed_later", "random_speed_earlier", "random_speed", "random_match"),
        contrast_from_subjects(subjects_mnps, "random_spread_later", "random_spread_earlier", "random_spread", "random_match"),
        contrast_from_subjects(subjects_spec, "matched_speed_later", "matched_speed_earlier", "matched_speed", "matched_mnps_spectral"),
        contrast_from_subjects(subjects_spec, "matched_spread_later", "matched_spread_earlier", "matched_spread", "matched_mnps_spectral"),
    ]
    table = pd.DataFrame(contrast_rows)
    table["holm_p"] = np.nan
    primary_idx = table.index[table["family"].eq("matched_mnps") & table["metric"].isin(PRIMARY_ENDPOINTS)]
    if len(primary_idx):
        table.loc[list(primary_idx), "holm_p"] = holm(table.loc[list(primary_idx), "sign_test_p"].to_numpy())
    table.to_csv(output_root / "c3_contrasts.csv", index=False)
    write_part1(output_root / "c3_part1.md", subjects_mnps, table)

    primary = table[table["family"] == "matched_mnps"]
    manifest = {
        "schema": "apollo_propofol_ndt_v1.matched_state_c3.v1",
        "analysis_id": ANALYSIS_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "confirmatory_status": CONFIRMATORY_STATUS,
        "confirmatory_contrasts": False,
        "n_subjects": int(len(subjects_mnps)),
        "n_included": int(subjects_mnps["included"].sum()),
        "n_holm_lt_0_05": int(((primary["holm_p"] < 0.05) & (primary["n_pairs"] >= MIN_TESTABLE_N)).sum()),
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "labels_sha256": sha256_file(labels_path) if labels_path.is_file() else None,
        "h5_root": str(DEFAULT_H5_ROOT),
        "primary": primary[
            ["metric", "n_pairs", "median_paired_difference", "cohens_dz", "sign_test_p", "wilcoxon_p", "holm_p"]
        ].to_dict("records"),
        "note": (
            "Matched-state one-step increment speed and spread. G3/G4 not locked. "
            "Local chart matching, not a documented cross-phase physical anchor."
        ),
    }
    write_json(output_root / "c3_part1_manifest.json", json_safe(manifest))
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
        "confirmatory_status": manifest.get("confirmatory_status"),
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
