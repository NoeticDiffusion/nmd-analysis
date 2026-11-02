"""Within-subject contrasts for Chart-Jacobian α plus L1/L2/L3 identities with values.

Complete-case pairs only. Exploratory; G4 not locked. Jacobian α is not one-step L3.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from apollo_common import ARTICLE_DIR, DEFAULT_H5_ROOT, json_safe, sha256_file, write_json
from apollo_level_panel import (
    ANALYSIS_ID,
    CONFIRMATORY_STATUS,
    LEVEL_CONTRASTS,
    LEVEL_METRICS,
)
from apollo_panel import BOOTSTRAP_N, BOOTSTRAP_SEED, MetricSpec
from apollo_stage_part1 import (
    LABELS_DEFAULT,
    SUPPORT_DEFAULT,
    _metric_columns,
    contrast_row,
    extract_recordings,
    load_cohort,
    paired_differences,
    subject_phase_table,
)
from apollo_stats import bh_fdr

OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_level_20260921"


def _fmt(value: float, digits: int = 4) -> str:
    if value is None or not np.isfinite(value):
        return "nan"
    return f"{value:.{digits}g}"


def write_level_md(path: Path, contrasts: pd.DataFrame, missing: pd.DataFrame) -> None:
    primary = contrasts[contrasts["contrast_id"] == "first_sedation_minus_baseline"].copy()
    usable = contrasts[contrasts["n_pairs"] >= 10].copy()
    sig = usable[usable["bh_q"] < 0.05].copy()
    sig = sig.reindex(sig["cohens_dz"].abs().sort_values(ascending=False).index)
    top = usable.reindex(usable["cohens_dz"].abs().sort_values(ascending=False).index).head(12)
    lines = [
        f"# Apollo Jacobian-α + L1/L2/L3 stage contrasts ({ANALYSIS_ID})",
        "",
        "Paired later-minus-earlier on subject/phase medians, complete-case only. "
        "BH-FDR is across finite Wilcoxon tests in this panel. "
        f"Status: `{CONFIRMATORY_STATUS}`. Chart-Jacobian α is not one-step L3. "
        "Not consciousness. Not confirmatory amplitude.",
        "",
        f"Bootstrap {BOOTSTRAP_N}, seed {BOOTSTRAP_SEED}. L2/L3 n is smaller because one-step identification is partial.",
        "",
        "## Missingness (recordings with a finite included median)",
        "",
        "| Level | Metric | n finite / 80 |",
        "| --- | --- | ---: |",
    ]
    for _, row in missing.iterrows():
        lines.append(
            f"| {row['level']} | `{row['metric']}` | {int(row['n_finite'])}/{int(row['n_recordings'])} |"
        )
    order = ("jacobian_alpha", "L1", "L2", "L3")
    for level in order:
        block = primary[primary["role"] == level]
        if block.empty:
            continue
        lines.extend(
            [
                "",
                f"## Primary contrast by {level}: first sedation − baseline",
                "",
                "| Metric | n | later med | base med | Δ med | d_z | Wilcoxon p | BH q | BH q within level |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for _, row in block.iterrows():
            lines.append(
                "| `{metric}` | {n} | {later} | {base} | {delta} | {d} | {p} | {q} | {ql} |".format(
                    metric=row["metric"],
                    n=int(row["n_pairs"]),
                    later=_fmt(row["later_median"]),
                    base=_fmt(row["earlier_median"]),
                    delta=_fmt(row["median_paired_difference"]),
                    d=_fmt(row["cohens_dz"], 3),
                    p=_fmt(row["wilcoxon_p"]),
                    q=_fmt(row["bh_q"]),
                    ql=_fmt(row["bh_q_within_level"]),
                )
            )
    lines.extend(["", "## FDR-significant rows (n≥10, |d_z| order)", ""])
    if sig.empty:
        lines.append("No Wilcoxon BH q < 0.05 among complete-case tests with n≥10.")
    else:
        lines.extend(
            [
                "| Level | Contrast | Metric | n | Δ med | d_z | Wilcoxon p | BH q |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for _, row in sig.iterrows():
            lines.append(
                "| {level} | `{contrast}` | `{metric}` | {n} | {delta} | {d} | {p} | {q} |".format(
                    level=row["role"],
                    contrast=row["contrast_id"],
                    metric=row["metric"],
                    n=int(row["n_pairs"]),
                    delta=_fmt(row["median_paired_difference"]),
                    d=_fmt(row["cohens_dz"], 3),
                    p=_fmt(row["wilcoxon_p"]),
                    q=_fmt(row["bh_q"]),
                )
            )
    lines.extend(
        [
            "",
            "## Largest |d_z| with n≥10",
            "",
            "| Level | Contrast | Metric | n | d_z | Wilcoxon p | BH q | BH q within level |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in top.iterrows():
        lines.append(
            "| {level} | `{contrast}` | `{metric}` | {n} | {d} | {p} | {q} | {ql} |".format(
                level=row["role"],
                contrast=row["contrast_id"],
                metric=row["metric"],
                n=int(row["n_pairs"]),
                d=_fmt(row["cohens_dz"], 3),
                p=_fmt(row["wilcoxon_p"]),
                q=_fmt(row["bh_q"]),
                ql=_fmt(row["bh_q_within_level"]),
            )
        )
    lines.extend(
        [
            "",
            "One-step L2/L3 pairs exist only when the lag-1 map is identified in both phases.",
            "Do not read protocol phase 3 as unresponsiveness. Export is `subject_anchored`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(*, labels_path: Path, support_path: Path, output_root: Path, workers: int) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    metrics = LEVEL_METRICS
    contrasts_spec = LEVEL_CONTRASTS
    cohort = load_cohort(labels_path, support_path)
    recordings = extract_recordings(cohort, workers=workers, metrics=metrics)
    recordings.to_csv(output_root / "level_run_level.csv", index=False)
    subjects = subject_phase_table(recordings, metrics=metrics)
    subjects.to_csv(output_root / "level_subject_phase.csv", index=False)

    pair_frames = []
    contrast_rows = []
    for contrast in contrasts_spec:
        for spec in metrics:
            paired = paired_differences(subjects, contrast, spec.metric_id)
            pair_frames.append(paired)
            row = contrast_row(paired, spec, contrast)
            row["role"] = spec.level or spec.role
            contrast_rows.append(row)
    pairs = pd.concat(pair_frames, ignore_index=True)
    pairs.to_csv(output_root / "level_paired_differences.csv", index=False)
    table = pd.DataFrame(contrast_rows)
    table["bh_q"] = bh_fdr(table["wilcoxon_p"].to_numpy())
    table["bh_q_within_contrast"] = np.nan
    table["bh_q_within_level"] = np.nan
    for _, index in table.groupby("contrast_id").groups.items():
        table.loc[list(index), "bh_q_within_contrast"] = bh_fdr(
            table.loc[list(index), "wilcoxon_p"].to_numpy()
        )
    for _, index in table.groupby("role").groups.items():
        table.loc[list(index), "bh_q_within_level"] = bh_fdr(
            table.loc[list(index), "wilcoxon_p"].to_numpy()
        )
    table.to_csv(output_root / "level_contrasts.csv", index=False)

    missing_rows = []
    for spec in metrics:
        median_col, included_col = _metric_columns(spec)
        finite = pd.to_numeric(
            recordings.loc[recordings[included_col] == True, median_col],  # noqa: E712
            errors="coerce",
        )
        missing_rows.append(
            {
                "level": spec.level or spec.role,
                "metric": spec.metric_id,
                "n_recordings": int(len(recordings)),
                "n_finite": int(finite.notna().sum()),
            }
        )
    missing = pd.DataFrame(missing_rows)
    missing.to_csv(output_root / "level_missingness.csv", index=False)
    write_level_md(output_root / "level_part1.md", table, missing)

    usable = table[table["n_pairs"] >= 10]
    top = usable.reindex(usable["cohens_dz"].abs().sort_values(ascending=False).index).head(12)
    manifest = {
        "schema": "apollo_propofol_ndt_v1.level_contrasts.v1",
        "analysis_id": ANALYSIS_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "confirmatory_status": CONFIRMATORY_STATUS,
        "confirmatory_contrasts": False,
        "n_recordings": int(len(recordings)),
        "n_subjects": int(recordings["subject_id"].nunique()),
        "n_metrics": int(len(metrics)),
        "n_contrasts": int(len(contrasts_spec)),
        "n_tests_in_bh_family": int(table["wilcoxon_p"].notna().sum()),
        "n_bh_q_lt_0_05": int(((table["bh_q"] < 0.05) & (table["n_pairs"] >= 10)).sum()),
        "n_bh_q_within_level_lt_0_05": int(
            ((table["bh_q_within_level"] < 0.05) & (table["n_pairs"] >= 10)).sum()
        ),
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "labels_sha256": sha256_file(labels_path) if labels_path.is_file() else None,
        "h5_root": str(DEFAULT_H5_ROOT),
        "largest_abs_dz": top[
            ["role", "contrast_id", "metric", "n_pairs", "cohens_dz", "wilcoxon_p", "bh_q", "bh_q_within_level"]
        ].to_dict("records"),
        "note": (
            "Complete-case within-subject contrasts on Chart-Jacobian α and L1/L2/L3 identities "
            "that have finite values. G3/G4 not locked."
        ),
    }
    write_json(output_root / "level_part1_manifest.json", json_safe(manifest))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=LABELS_DEFAULT)
    parser.add_argument("--support", type=Path, default=SUPPORT_DEFAULT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)
    manifest = run(
        labels_path=args.labels,
        support_path=args.support,
        output_root=args.output_root,
        workers=args.workers,
    )
    print(json.dumps({
        "output_root": str(args.output_root),
        "n_bh_q_lt_0_05": manifest.get("n_bh_q_lt_0_05"),
        "n_bh_q_within_level_lt_0_05": manifest.get("n_bh_q_within_level_lt_0_05"),
        "n_tests_in_bh_family": manifest.get("n_tests_in_bh_family"),
        "largest_abs_dz": manifest.get("largest_abs_dz")[:10],
        "confirmatory_status": manifest.get("confirmatory_status"),
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
