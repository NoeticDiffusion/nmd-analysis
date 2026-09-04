from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from jacobian_9d_support import ALL_ARTICLE_METRICS, FORMAL_CONTRAST_DIR, RESULT_LEDGER_DIR, REVISED_CORE_METRICS


DISPLAY_NAMES = {
    "spectral_radius_median": "Spectral radius",
    "anisotropy_abs_eig_median": "Anisotropy abs eig",
    "mdr_median": "MDR",
    "rotational_power_mean": "Rotational power mean",
    "rotational_power_median": "Rotational power median",
    "a_operator_norm_median": "A-operator norm",
    "frobenius_norm_median": "Frobenius norm",
    "rotation_norm_median": "Rotation norm",
}
TIER_MAP = {
    "spectral_radius_median": "primary_lead",
    "anisotropy_abs_eig_median": "secondary_replicated",
    "mdr_median": "pooled_promoted",
    "rotational_power_mean": "pooled_promoted",
    "rotational_power_median": "pooled_promoted",
    "a_operator_norm_median": "legacy_supportive",
    "frobenius_norm_median": "legacy_supportive",
    "rotation_norm_median": "legacy_supportive",
}


def _load_ranking(cohort: str) -> pd.DataFrame:
    path = FORMAL_CONTRAST_DIR / cohort / "article_candidate_ranking.csv"
    frame = pd.read_csv(path)
    frame["cohort"] = cohort
    return frame


def _lookup(frame: pd.DataFrame, metric: str) -> pd.Series:
    row = frame[frame["metric"] == metric]
    if row.empty:
        raise KeyError(f"Missing metric `{metric}` in {frame['cohort'].iloc[0]} ranking.")
    return row.iloc[0]


def build_result_ledger() -> pd.DataFrame:
    part1 = _load_ranking("part1")
    part2 = _load_ranking("part2")
    pooled = _load_ranking("pooled")
    rows = []
    for order_idx, metric in enumerate(ALL_ARTICLE_METRICS, start=1):
        row1 = _lookup(part1, metric)
        row2 = _lookup(part2, metric)
        rowp = _lookup(pooled, metric)
        signs = [np.sign(float(row1["cohens_d"])), np.sign(float(row2["cohens_d"])), np.sign(float(rowp["cohens_d"]))]
        rows.append(
            {
                "article_order": order_idx,
                "metric": metric,
                "display_name": DISPLAY_NAMES.get(metric, metric),
                "tier": TIER_MAP[metric],
                "is_revised_core_metric": metric in REVISED_CORE_METRICS,
                "part1_rank": int(row1["candidate_rank"]),
                "part1_d": float(row1["cohens_d"]),
                "part1_p": float(row1["mannwhitney_p"]),
                "part1_q": float(row1["bh_fdr_q"]),
                "part2_rank": int(row2["candidate_rank"]),
                "part2_d": float(row2["cohens_d"]),
                "part2_p": float(row2["mannwhitney_p"]),
                "part2_q": float(row2["bh_fdr_q"]),
                "pooled_rank": int(rowp["candidate_rank"]),
                "pooled_d": float(rowp["cohens_d"]),
                "pooled_p": float(rowp["mannwhitney_p"]),
                "pooled_q": float(rowp["bh_fdr_q"]),
                "sign_stable_part1_part2_pooled": bool(len(set(signs)) == 1),
                "legacy_manuscript_candidate": bool(rowp["is_manuscript_candidate"]),
                "selection_note": (
                    "revised core panel"
                    if metric in REVISED_CORE_METRICS
                    else "legacy replication-support metric retained below revised pooled-promoted signals"
                ),
            }
        )
    return pd.DataFrame(rows)


def build_summary_markdown(ledger: pd.DataFrame) -> str:
    lines = [
        "# 9D Jacobian Result Ledger",
        "",
        "This ledger freezes the article-facing metric hierarchy against the formal `20260525_cpc15_primary12h` bundle.",
        "",
        "## Frozen hierarchy",
        "",
    ]
    for tier in ("primary_lead", "secondary_replicated", "pooled_promoted", "legacy_supportive"):
        subset = ledger[ledger["tier"] == tier].copy()
        lines.append(f"### `{tier}`")
        lines.append("")
        for _, row in subset.iterrows():
            lines.append(
                f"- `{row['metric']}`: pooled rank `{int(row['pooled_rank'])}`, pooled `d = {row['pooled_d']:.3f}`, "
                f"part1 `d = {row['part1_d']:.3f}`, part2 `d = {row['part2_d']:.3f}`"
            )
        lines.append("")
    lines.extend(
        [
            "## Interpretation",
            "",
            "- `spectral_radius_median` remains the cleanest primary lead because it is the strongest pooled effect and stays strong in both cohorts.",
            "- `anisotropy_abs_eig_median` remains the best replicated secondary signal, but is no longer the only non-legacy metric worth foregrounding.",
            "- `mdr_median`, `rotational_power_mean`, and `rotational_power_median` are now frozen as pooled-promoted signals that must be stress-tested in robustness and prediction analyses.",
            "- `a_operator_norm_median`, `frobenius_norm_median`, and `rotation_norm_median` are retained as legacy replication-support metrics rather than as the paper's main pooled hierarchy.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    RESULT_LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    ledger = build_result_ledger()
    ledger.to_csv(RESULT_LEDGER_DIR / "metric_result_ledger.csv", index=False)
    (RESULT_LEDGER_DIR / "metric_result_ledger.md").write_text(build_summary_markdown(ledger), encoding="utf-8")
    (RESULT_LEDGER_DIR / "metric_result_ledger.json").write_text(
        json.dumps(ledger.to_dict(orient="records"), indent=2),
        encoding="utf-8",
    )
    manifest = {
        "source_contrast_dir": str(FORMAL_CONTRAST_DIR),
        "output_dir": str(RESULT_LEDGER_DIR),
        "revised_core_metrics": list(REVISED_CORE_METRICS),
        "all_article_metrics": list(ALL_ARTICLE_METRICS),
        "tier_map": TIER_MAP,
    }
    (RESULT_LEDGER_DIR / "metric_result_ledger_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote result ledger to {RESULT_LEDGER_DIR}")


if __name__ == "__main__":
    main()
