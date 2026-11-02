"""LOR/ROR labels on frozen occupancy. Occupancy is joined, not recomputed."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from apollo_c3_panel import BOOTSTRAP_N, BOOTSTRAP_SEED, MIN_TESTABLE_N
from apollo_common import ARTICLE_DIR, json_safe, sha256_file, write_json
from apollo_lor import N_TRIALS, binomial_ci, lor_status, ror_status
from apollo_lor_panel import (
    ANALYSIS_ID,
    BASELINE_PHASE,
    CHENNU_N_IMPAIRED,
    CHENNU_N_RESPONSIVE,
    CONFIRMATORY_STATUS,
    FIRST_PHASE,
    MODERATE_PHASE,
    OCCUPANCY_SUBJECT,
    PHASE_COLUMNS,
    PREDICTION_PRIMARY,
    PRIMARY_CONTRAST_ID,
    RECOVERY_PHASE,
)
from apollo_occupancy_figures import _style, save_figure
from apollo_stage_part1 import LABELS_DEFAULT
from apollo_stats import (
    cohens_d,
    mannwhitney_p,
    percentile_bootstrap_median_diff,
    spearman_rho_p,
)

OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_lor_20260921"
OCCUPANCY_DEFAULT = ARTICLE_DIR / OCCUPANCY_SUBJECT
LOR_COLORS = {
    "lor_impaired": "#E45756",
    "responsive": "#4C78A8",
    "missing": "#888888",
}


def _fmt(value: float, digits: int = 4) -> str:
    if value is None or not np.isfinite(value):
        return "nan"
    return f"{value:.{digits}g}"


def phase_wide(labels: pd.DataFrame, column: str) -> pd.DataFrame:
    work = labels.copy()
    work[column] = pd.to_numeric(work[column], errors="coerce")
    table = (
        work.groupby(["subject_id", "protocol_phase_label"], as_index=False)[column]
        .median()
        .pivot(index="subject_id", columns="protocol_phase_label", values=column)
    )
    return table.reindex(columns=list(PHASE_COLUMNS))


def assign_behaviour(labels: pd.DataFrame) -> pd.DataFrame:
    hits = phase_wide(labels, "n_correct_responses")
    conc = phase_wide(labels, "measured_concentration")
    rt = phase_wide(labels, "mean_reaction_time_ms")
    rows = []
    for subject in sorted(hits.index):
        k_base = float(hits.loc[subject, BASELINE_PHASE]) if BASELINE_PHASE in hits.columns else float("nan")
        k_first = float(hits.loc[subject, FIRST_PHASE]) if FIRST_PHASE in hits.columns else float("nan")
        k_mod = float(hits.loc[subject, MODERATE_PHASE]) if MODERATE_PHASE in hits.columns else float("nan")
        k_rec = float(hits.loc[subject, RECOVERY_PHASE]) if RECOVERY_PHASE in hits.columns else float("nan")
        base_lo, base_hi = binomial_ci(k_base)
        mod_lo, mod_hi = binomial_ci(k_mod)
        rec_lo, rec_hi = binomial_ci(k_rec)
        lor = lor_status(k_base, k_mod)
        row = {
            "subject_id": subject,
            "n_correct_pre_drug_baseline": k_base,
            "n_correct_first_protocol_sedation": k_first,
            "n_correct_later_protocol_sedation": k_mod,
            "n_correct_recovery": k_rec,
            "hit_rate_pre_drug_baseline": k_base / N_TRIALS if np.isfinite(k_base) else float("nan"),
            "hit_rate_later_protocol_sedation": k_mod / N_TRIALS if np.isfinite(k_mod) else float("nan"),
            "ci_baseline_lo": base_lo,
            "ci_baseline_hi": base_hi,
            "ci_later_lo": mod_lo,
            "ci_later_hi": mod_hi,
            "ci_recovery_lo": rec_lo,
            "ci_recovery_hi": rec_hi,
            "lor_status": lor,
            "ror_status": ror_status(k_base, k_rec, lor),
            "concentration_pre_drug_baseline": float(conc.loc[subject, BASELINE_PHASE]) if subject in conc.index else float("nan"),
            "concentration_first_protocol_sedation": float(conc.loc[subject, FIRST_PHASE]) if subject in conc.index else float("nan"),
            "concentration_later_protocol_sedation": float(conc.loc[subject, MODERATE_PHASE]) if subject in conc.index else float("nan"),
            "concentration_recovery": float(conc.loc[subject, RECOVERY_PHASE]) if subject in conc.index else float("nan"),
            "rt_later_protocol_sedation": float(rt.loc[subject, MODERATE_PHASE]) if subject in rt.index else float("nan"),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def occupancy_delta(joined: pd.DataFrame, later_phase: str) -> pd.Series:
    later = pd.to_numeric(joined[f"occupancy_{later_phase}"], errors="coerce")
    earlier = pd.to_numeric(joined[f"occupancy_{BASELINE_PHASE}"], errors="coerce")
    return later - earlier


def group_contrast(
    joined: pd.DataFrame,
    *,
    contrast_id: str,
    later_phase: str,
    value: pd.Series,
    primary: bool,
    prediction: str,
    metric: str,
) -> dict[str, Any]:
    lor = value[joined["lor_status"] == "lor_impaired"]
    resp = value[joined["lor_status"] == "responsive"]
    lor_f = lor[np.isfinite(lor)]
    resp_f = resp[np.isfinite(resp)]
    n_lor = int(len(lor_f))
    n_resp = int(len(resp_f))
    med_diff = float(np.median(lor_f) - np.median(resp_f)) if n_lor and n_resp else float("nan")
    lo, hi, n_boot = percentile_bootstrap_median_diff(
        lor_f.to_numpy(), resp_f.to_numpy(), n_boot=BOOTSTRAP_N, seed=BOOTSTRAP_SEED
    )
    testable = n_lor >= MIN_TESTABLE_N and n_resp >= MIN_TESTABLE_N
    return {
        "family": "occupancy_lor",
        "metric": metric,
        "contrast_id": contrast_id,
        "later_phase": later_phase,
        "earlier_phase": BASELINE_PHASE,
        "primary_contrast": primary,
        "prediction": prediction,
        "n_lor_impaired": n_lor,
        "n_responsive": n_resp,
        "median_lor_impaired": float(np.median(lor_f)) if n_lor else float("nan"),
        "median_responsive": float(np.median(resp_f)) if n_resp else float("nan"),
        "median_difference_lor_minus_responsive": med_diff,
        "median_diff_ci_lo": lo,
        "median_diff_ci_hi": hi,
        "cohens_d": cohens_d(lor_f, resp_f),
        "mannwhitney_p": mannwhitney_p(lor_f, resp_f),
        "family_testable": testable,
        "test_status": "TESTABLE" if testable else "NOT_TESTABLE",
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "n_boot_used": n_boot,
        "confirmatory_status": CONFIRMATORY_STATUS,
    }


def figure_lor_trajectory(joined: pd.DataFrame, output_dir: Path) -> list[Path]:
    phases = PHASE_COLUMNS
    x = np.arange(len(phases), dtype=float)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for status, color in (("responsive", LOR_COLORS["responsive"]), ("lor_impaired", LOR_COLORS["lor_impaired"])):
        block = joined[joined["lor_status"] == status]
        values = block[[f"occupancy_{phase}" for phase in phases]].to_numpy(dtype=float)
        for row in values:
            ax.plot(x, row, color=color, alpha=0.28, lw=1.1)
        if len(values):
            ax.plot(
                x,
                np.nanmedian(values, axis=0),
                color=color,
                lw=2.2,
                marker="o",
                ms=6,
                label=f"{status.replace('_', ' ')} (n={len(block)})",
            )
    ax.set_xticks(x, ("Baseline", "First sedation", "Later sedation", "Recovery"))
    ax.set_ylabel(r"Occupancy median $\|z\|_2$")
    ax.set_title("Occupancy trajectory by Chennu LOR status")
    ax.legend(frameon=False, loc="upper left")
    _style(ax)
    fig.tight_layout()
    return save_figure(fig, output_dir / "fig_lor_occupancy_trajectory")


def write_part1(
    path: Path,
    behaviour: pd.DataFrame,
    joined: pd.DataFrame,
    contrasts: pd.DataFrame,
    associations: pd.DataFrame,
) -> None:
    n_lor = int((behaviour["lor_status"] == "lor_impaired").sum())
    n_resp = int((behaviour["lor_status"] == "responsive").sum())
    n_missing = int((behaviour["lor_status"] == "missing").sum())
    n_returned = int((behaviour["ror_status"] == "returned").sum())
    n_not_returned = int((behaviour["ror_status"] == "not_returned").sum())
    primary = contrasts[contrasts["primary_contrast"] == True]  # noqa: E712
    lines = [
        f"# Apollo occupancy × LOR/ROR ({ANALYSIS_ID})",
        "",
        "Behavioural labels from exact binomial 95% Clopper–Pearson intervals on "
        f"`n_correct_responses` / {N_TRIALS} at later protocol sedation versus baseline. "
        "Occupancy is the frozen unmatched baseline-z scalar; it is joined, not recomputed. "
        f"Status: `{CONFIRMATORY_STATUS}`. Not consciousness. Not protocol-3-as-LOR.",
        "",
        "## Occupancy-blind label audit",
        "",
        f"LOR-impaired {n_lor} / responsive {n_resp} / missing {n_missing} "
        f"(Chennu 2016 reported {CHENNU_N_IMPAIRED} drowsy and {CHENNU_N_RESPONSIVE} responsive).",
        f"Among LOR-impaired, ROR returned {n_returned}, not returned {n_not_returned}.",
        "",
        "| Subject | k base | k first | k later | k recovery | LOR | ROR |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for _, row in behaviour.sort_values("subject_id").iterrows():
        lines.append(
            "| {sid} | {b} | {f} | {l} | {r} | {lor} | {ror} |".format(
                sid=row["subject_id"],
                b=_fmt(row["n_correct_pre_drug_baseline"], 3),
                f=_fmt(row["n_correct_first_protocol_sedation"], 3),
                l=_fmt(row["n_correct_later_protocol_sedation"], 3),
                r=_fmt(row["n_correct_recovery"], 3),
                lor=row["lor_status"],
                ror=row["ror_status"],
            )
        )
    lines.extend(
        [
            "",
            "## Primary: occupancy Δ (later sedation − baseline) by LOR",
            "",
            "| Status | n_LOR | n_resp | med LOR | med resp | Δ med | d | MW p | test |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for _, row in contrasts.iterrows():
        lines.append(
            "| {role} | {nl} | {nr} | {ml} | {mr} | {md} | {d} | {p} | {st} |".format(
                role="primary" if bool(row["primary_contrast"]) else row["contrast_id"],
                nl=int(row["n_lor_impaired"]),
                nr=int(row["n_responsive"]),
                ml=_fmt(row["median_lor_impaired"]),
                mr=_fmt(row["median_responsive"]),
                md=_fmt(row["median_difference_lor_minus_responsive"]),
                d=_fmt(row["cohens_d"], 3),
                p=_fmt(row["mannwhitney_p"]),
                st=row["test_status"],
            )
        )
    lines.extend(
        [
            "",
            "## Associations (later protocol sedation)",
            "",
            "| Pair | n | Spearman ρ | p |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for _, row in associations.iterrows():
        lines.append(
            "| {pair} | {n} | {rho} | {p} |".format(
                pair=row["pair"],
                n=int(row["n"]),
                rho=_fmt(row["spearman_rho"], 3),
                p=_fmt(row["spearman_p"]),
            )
        )
    if not primary.empty:
        p = primary.iloc[0]
        lines.extend(
            [
                "",
                f"Primary prediction: `{PREDICTION_PRIMARY}`. Gate is ≥{MIN_TESTABLE_N} per arm. "
                "Protocol phase 3 remains a protocol label. Package `unresponsive` is not used.",
                "",
                f"Primary MW p = {_fmt(p['mannwhitney_p'])}, d = {_fmt(p['cohens_d'], 3)}, "
                f"status `{p['test_status']}`.",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(*, labels_path: Path, occupancy_path: Path, output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    labels = pd.read_csv(labels_path)
    behaviour = assign_behaviour(labels)
    behaviour.to_csv(output_root / "lor_behaviour_labels.csv", index=False)

    occupancy = pd.read_csv(occupancy_path)
    joined = occupancy.merge(behaviour, on="subject_id", how="left")
    later_delta = occupancy_delta(joined, MODERATE_PHASE)
    later_delta.name = "occupancy_later_minus_baseline"
    first_delta = occupancy_delta(joined, FIRST_PHASE)
    first_delta.name = "occupancy_first_minus_baseline"
    rec_delta = occupancy_delta(joined, RECOVERY_PHASE)
    rec_delta.name = "occupancy_recovery_minus_baseline"
    joined["occupancy_later_minus_baseline"] = later_delta
    joined["occupancy_first_minus_baseline"] = first_delta
    joined["occupancy_recovery_minus_baseline"] = rec_delta
    joined.to_csv(output_root / "lor_occupancy_joined.csv", index=False)

    contrast_rows = [
        group_contrast(
            joined,
            contrast_id=PRIMARY_CONTRAST_ID,
            later_phase=MODERATE_PHASE,
            value=later_delta,
            primary=True,
            prediction=PREDICTION_PRIMARY,
            metric="unmatched_occupancy_delta",
        ),
        group_contrast(
            joined,
            contrast_id="first_sedation_minus_baseline_lor_vs_responsive",
            later_phase=FIRST_PHASE,
            value=first_delta,
            primary=False,
            prediction="two-sided descriptive",
            metric="unmatched_occupancy_delta",
        ),
        group_contrast(
            joined,
            contrast_id="recovery_minus_baseline_lor_vs_responsive",
            later_phase=RECOVERY_PHASE,
            value=rec_delta,
            primary=False,
            prediction="two-sided descriptive",
            metric="unmatched_occupancy_delta",
        ),
        group_contrast(
            joined,
            contrast_id="later_sedation_concentration_lor_vs_responsive",
            later_phase=MODERATE_PHASE,
            value=pd.to_numeric(joined["concentration_later_protocol_sedation"], errors="coerce"),
            primary=False,
            prediction="confounder check: drug exposure at the same protocol phase",
            metric="measured_concentration",
        ),
    ]
    contrasts = pd.DataFrame(contrast_rows)
    occupancy_later = pd.to_numeric(joined["occupancy_later_protocol_sedation"], errors="coerce")
    hits_later = pd.to_numeric(joined["n_correct_later_protocol_sedation"], errors="coerce")
    conc_later = pd.to_numeric(joined["concentration_later_protocol_sedation"], errors="coerce")
    rho_hits, p_hits = spearman_rho_p(occupancy_later, hits_later)
    rho_conc, p_conc = spearman_rho_p(occupancy_later, conc_later)
    associations = pd.DataFrame(
        [
            {
                "pair": "occupancy vs n_correct at later sedation",
                "n": int((np.isfinite(occupancy_later) & np.isfinite(hits_later)).sum()),
                "spearman_rho": rho_hits,
                "spearman_p": p_hits,
            },
            {
                "pair": "occupancy vs concentration at later sedation",
                "n": int((np.isfinite(occupancy_later) & np.isfinite(conc_later)).sum()),
                "spearman_rho": rho_conc,
                "spearman_p": p_conc,
            },
        ]
    )
    contrasts.to_csv(output_root / "lor_contrasts.csv", index=False)
    associations.to_csv(output_root / "lor_associations.csv", index=False)
    write_part1(output_root / "lor_part1.md", behaviour, joined, contrasts, associations)
    figure_lor_trajectory(joined, output_root)

    n_lor = int((behaviour["lor_status"] == "lor_impaired").sum())
    n_resp = int((behaviour["lor_status"] == "responsive").sum())
    primary = contrasts[contrasts["contrast_id"] == PRIMARY_CONTRAST_ID].iloc[0]
    manifest = {
        "schema": "apollo_propofol_ndt_v1.occupancy_lor.v1",
        "analysis_id": ANALYSIS_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_status": "no_biological_claim",
        "scientific_qualification": "not_assessed",
        "confirmatory_status": CONFIRMATORY_STATUS,
        "confirmatory_contrasts": False,
        "n_lor_impaired": n_lor,
        "n_responsive": n_resp,
        "n_missing": int((behaviour["lor_status"] == "missing").sum()),
        "n_ror_returned": int((behaviour["ror_status"] == "returned").sum()),
        "n_ror_not_returned": int((behaviour["ror_status"] == "not_returned").sum()),
        "chennu_2016_impaired": CHENNU_N_IMPAIRED,
        "chennu_2016_responsive": CHENNU_N_RESPONSIVE,
        "labels_sha256": sha256_file(labels_path) if labels_path.is_file() else None,
        "occupancy_sha256": sha256_file(occupancy_path) if occupancy_path.is_file() else None,
        "primary": {
            "contrast_id": PRIMARY_CONTRAST_ID,
            "n_lor_impaired": int(primary["n_lor_impaired"]),
            "n_responsive": int(primary["n_responsive"]),
            "median_difference_lor_minus_responsive": float(primary["median_difference_lor_minus_responsive"]),
            "cohens_d": float(primary["cohens_d"]),
            "mannwhitney_p": float(primary["mannwhitney_p"]),
            "test_status": str(primary["test_status"]),
        },
        "associations": associations.to_dict("records"),
        "note": (
            "Chennu binomial-CI LOR on n_correct/40; frozen occupancy joined. "
            "G3/G4 not locked. Protocol 3 is not LOR."
        ),
    }
    write_json(output_root / "lor_part1_manifest.json", json_safe(manifest))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=LABELS_DEFAULT)
    parser.add_argument("--occupancy", type=Path, default=OCCUPANCY_DEFAULT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args(argv)
    manifest = run(labels_path=args.labels, occupancy_path=args.occupancy, output_root=args.output_root)
    print(json.dumps({
        "output_root": str(args.output_root),
        "n_lor_impaired": manifest.get("n_lor_impaired"),
        "n_responsive": manifest.get("n_responsive"),
        "primary": manifest.get("primary"),
        "associations": manifest.get("associations"),
        "confirmatory_status": manifest.get("confirmatory_status"),
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
