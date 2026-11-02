"""Join part1-corrected and part2-confirmatory outcome contrasts into one
replication table. Two independent, non-overlapping I-CARE 2.1 cohorts,
same fixed ingest contract (Jacobian fit-fidelity gate, ComBat by hospital,
subject-anchored coords, 0-12h EEG-anchor window).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from icare_v2_common import ARTICLE_DIR, write_csv


KEEP_COLS = [
    "family",
    "hypothesis",
    "metric",
    "prediction",
    "n_cpc1",
    "n_cpc5",
    "cohens_d_cpc1_minus_cpc5",
    "cliffs_delta_cpc1_minus_cpc5",
    "mannwhitney_p",
    "bh_q_within_family",
    "bh_significant",
    "family_testable",
]


def _load(path: Path, bundle_label: str) -> pd.DataFrame:
    frame = pd.read_csv(path)[KEEP_COLS].copy()
    frame = frame.add_suffix(f"__{bundle_label}")
    frame = frame.rename(
        columns={
            f"family__{bundle_label}": "family",
            f"hypothesis__{bundle_label}": "hypothesis",
            f"metric__{bundle_label}": "metric",
            f"prediction__{bundle_label}": "prediction",
        }
    )
    return frame


def _replicated(row: pd.Series) -> str:
    d1 = row.get("cohens_d_cpc1_minus_cpc5__part1")
    d2 = row.get("cohens_d_cpc1_minus_cpc5__part2")
    sig1 = row.get("bh_significant__part1")
    sig2 = row.get("bh_significant__part2")
    testable1 = row.get("family_testable__part1")
    testable2 = row.get("family_testable__part2")
    if not (bool(testable1) and bool(testable2)):
        return "not_testable"
    if pd.isna(d1) or pd.isna(d2):
        return "insufficient_data"
    same_sign = (d1 > 0) == (d2 > 0)
    both_family_sig = (sig1 is True) and (sig2 is True)
    if both_family_sig and same_sign:
        return "replicated"
    if same_sign:
        return "same_direction_not_both_bh_sig"
    return "did_not_replicate"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--part1",
        type=Path,
        default=ARTICLE_DIR / "results" / "part1_corrected" / "outcome_contrasts.csv",
    )
    parser.add_argument(
        "--part2",
        type=Path,
        default=ARTICLE_DIR / "results" / "part2_confirmatory" / "outcome_contrasts.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ARTICLE_DIR / "results" / "replication",
    )
    args = parser.parse_args()

    p1 = _load(args.part1, "part1")
    p2 = _load(args.part2, "part2")
    joined = p1.merge(p2, on=["family", "hypothesis", "metric", "prediction"], how="outer")
    joined["replication_call"] = joined.apply(_replicated, axis=1)

    out_dir = args.out_dir
    write_csv(out_dir / "replication_summary.csv", joined)

    try:
        table_text = joined.to_markdown(index=False)
    except ImportError:
        columns = [str(c) for c in joined.columns]
        rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
        for _, row in joined.iterrows():
            cells = []
            for column in joined.columns:
                value = row[column]
                cells.append("" if pd.isna(value) else str(value))
            rows.append("| " + " | ".join(cells) + " |")
        table_text = "\n".join(rows)

    lines = [
        "# I-CARE v2 CPC1 vs CPC5 — part1-corrected vs part2-confirmatory replication",
        "",
        "- part1 = bundle `20260911_125829` (161 subjects, same population as the original",
        "  `20260904_225047` dump, re-ingested with the Jacobian fit-fidelity gate + ComBat",
        "  + cohort-anchored coords; role = discovery/exploratory).",
        "- part2 = bundle `20260911_123135` (141 subjects, zero subject overlap with part1;",
        "  role = confirmatory).",
        "- `replicated` = family-BH-significant in both cohorts with the same sign.",
        "- `family_testable` requires >= 10 patients per CPC arm after the Jacobian gate;",
        "  Family B (`mnj_v3_*`) is `not_testable` in one or both cohorts on this dataset.",
        "",
        table_text,
        "",
    ]
    (out_dir / "replication_summary.md").write_text("\n".join(str(x) for x in lines), encoding="utf-8")
    print(f"Wrote replication summary to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
