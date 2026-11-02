"""CPC1 vs CPC5 contrasts for Family A (H1-H4) and Family B (F_reactive)."""
from __future__ import annotations

import argparse
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from icare_v2_common import (
    add_common_args,
    bh_fdr,
    bootstrap_two_sample_ci,
    cliffs_delta,
    cohens_d,
    resolve_pipeline_config,
    write_csv,
    write_json,
)

N_BOOT = 2000
BOOT_SEED = 20260912


H1_H3 = (
    ("d_eff_a_median", "H1", "CPC1 > CPC5"),
    ("h_tilde_a_median", "H2", "CPC1 > CPC5"),
    ("e_perp_median", "H3", "CPC1 > CPC5"),
)
H4 = ("d_total_median", "H4", "not required to differ")
MNJ_PRIMARY = ("f_reactive", "F_reactive", "CPC1 > CPC5")
MNJ_SECONDARY = (
    ("alpha_mean", "mean_alpha", "no directional preregistration"),
    ("omega_mean", "mean_omega", "descriptive"),
    ("f_contract", "F_contract", "CPC5 subtype / CPC1 < CPC5 expected"),
    ("f_unstable", "F_unstable", "CPC5 subtype / CPC1 < CPC5 expected"),
    ("reactivity_gap_given_alpha_neg_mean", "R_g|alpha<0", "CPC1 elevated inside alpha<0"),
)
REACH = (
    ("cone_d_eff_h1_median", "reach_d_eff_h1", "Case A if CPC1 > CPC5 already at h=1"),
    ("cone_d_eff_h4_median", "reach_d_eff_h4", "Case B if advantage appears only at h=4"),
    ("tube_d_eff_median", "tube_d_eff", "historical comparator"),
)


def _contrast_row(frame: pd.DataFrame, metric: str, *, cfg, family: str, hypothesis: str, prediction: str) -> dict[str, Any]:
    good = pd.to_numeric(frame.loc[frame["contrast_group"] == cfg.good_label, metric], errors="coerce").to_numpy(dtype=float)
    poor = pd.to_numeric(frame.loc[frame["contrast_group"] == cfg.poor_label, metric], errors="coerce").to_numpy(dtype=float)
    good = good[np.isfinite(good)]
    poor = poor[np.isfinite(poor)]
    mw_p = welch_p = float("nan")
    mw_u = t_stat = float("nan")
    if good.size and poor.size:
        try:
            mw = stats.mannwhitneyu(good, poor, alternative="two-sided")
            mw_u = float(mw.statistic)
            mw_p = float(mw.pvalue)
        except ValueError:
            pass
    if good.size >= 2 and poor.size >= 2:
        try:
            tt = stats.ttest_ind(good, poor, equal_var=False)
            t_stat = float(tt.statistic)
            welch_p = float(tt.pvalue)
        except ValueError:
            pass
    d_lo = d_hi = delta_lo = delta_hi = float("nan")
    n_boot_d = n_boot_delta = 0
    if good.size >= 2 and poor.size >= 2:
        d_lo, d_hi, n_boot_d = bootstrap_two_sample_ci(good, poor, cohens_d, n_boot=N_BOOT, seed=BOOT_SEED)
    if good.size >= 1 and poor.size >= 1:
        delta_lo, delta_hi, n_boot_delta = bootstrap_two_sample_ci(good, poor, cliffs_delta, n_boot=N_BOOT, seed=BOOT_SEED)
    return {
        "family": family,
        "hypothesis": hypothesis,
        "metric": metric,
        "prediction": prediction,
        "n_cpc1": int(good.size),
        "n_cpc5": int(poor.size),
        "cpc1_mean": float(np.mean(good)) if good.size else float("nan"),
        "cpc1_median": float(np.median(good)) if good.size else float("nan"),
        "cpc5_mean": float(np.mean(poor)) if poor.size else float("nan"),
        "cpc5_median": float(np.median(poor)) if poor.size else float("nan"),
        "cohens_d_cpc1_minus_cpc5": cohens_d(good, poor),
        "cohens_d_ci_lo": d_lo,
        "cohens_d_ci_hi": d_hi,
        "cliffs_delta_cpc1_minus_cpc5": cliffs_delta(good, poor),
        "cliffs_delta_ci_lo": delta_lo,
        "cliffs_delta_ci_hi": delta_hi,
        "bootstrap_n": N_BOOT,
        "bootstrap_seed": BOOT_SEED,
        "mannwhitney_u": mw_u,
        "mannwhitney_p": mw_p,
        "welch_t": t_stat,
        "welch_p": welch_p,
        "family_testable": bool(good.size >= cfg.min_testable_group_n and poor.size >= cfg.min_testable_group_n),
        "min_testable_group_n": cfg.min_testable_group_n,
        "confirmatory_status": cfg.confirmatory_status,
        "smoke": cfg.smoke,
        "primary_window": cfg.primary_window,
    }


def _apply_family_fdr(frame: pd.DataFrame, family: str) -> pd.DataFrame:
    out = frame.copy()
    mask = out["family"] == family
    q = np.full(len(out), np.nan)
    if mask.any():
        q_vals = bh_fdr(out.loc[mask, "mannwhitney_p"].to_numpy(dtype=float))
        q[np.where(mask)[0]] = q_vals
    out["bh_q_within_family"] = q
    return out


def _cpc5_subtypes(frame: pd.DataFrame, cfg) -> pd.DataFrame:
    poor = frame[frame["contrast_group"] == cfg.poor_label].copy()
    if poor.empty or not {"f_contract", "f_unstable", "f_reactive"}.issubset(poor.columns):
        return pd.DataFrame()
    def _label(row: pd.Series) -> str:
        values = {
            "contract": row.get("f_contract", np.nan),
            "unstable": row.get("f_unstable", np.nan),
            "reactive": row.get("f_reactive", np.nan),
        }
        finite = {k: v for k, v in values.items() if pd.notna(v)}
        if not finite:
            return "unassigned"
        return max(finite, key=finite.get)

    poor["cpc5_majority_regime"] = poor.apply(_label, axis=1)
    counts = poor["cpc5_majority_regime"].value_counts(dropna=False).rename_axis("majority_regime").reset_index(name="n")
    counts["fraction"] = counts["n"] / counts["n"].sum()
    return counts


def _ttm_sensitivity(frame: pd.DataFrame, cfg) -> pd.DataFrame:
    rows = []
    ttm = pd.to_numeric(frame.get("ttm"), errors="coerce")
    work = frame.copy()
    work["ttm_num"] = ttm
    for value in sorted(v for v in work["ttm_num"].dropna().unique()):
        subset = work[work["ttm_num"] == value]
        if subset["contrast_group"].nunique() < 2:
            continue
        for metric, hyp, pred in H1_H3:
            if metric not in subset.columns:
                continue
            row = _contrast_row(subset, metric, cfg=cfg, family="diffusion_H1H3_ttm", hypothesis=hyp, prediction=pred)
            row["ttm"] = float(value)
            rows.append(row)
    return pd.DataFrame(rows)


def _frame_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    columns = [str(c) for c in frame.columns]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for _, row in frame.iterrows():
        cells = []
        for column in frame.columns:
            value = row[column]
            if isinstance(value, float):
                cells.append("nan" if pd.isna(value) else f"{value:.4g}")
            else:
                cells.append("" if pd.isna(value) else str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_markdown(contrasts: pd.DataFrame, subtypes: pd.DataFrame, cfg) -> str:
    lines = [
        "# I-CARE v2 CPC1 vs CPC5 contrasts",
        "",
        f"- bundle_id: `{cfg.bundle_id}`",
        f"- confirmatory_status: `{cfg.confirmatory_status}`",
        f"- smoke: `{cfg.smoke}`",
        f"- primary_window: `{cfg.primary_window}`",
        "",
        "These results are **exploratory pending part2**. Do not treat smoke-sample numbers as evidence.",
        "",
        "## Contrasts",
        "",
        _frame_markdown(contrasts),
        "",
        "## CPC5 majority-regime subtypes",
        "",
        _frame_markdown(subtypes),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    in_dir = args.input_dir or cfg.output_dir
    out_dir = cfg.output_dir
    table = pd.read_csv(in_dir / "icare_v2_primary_cpc15_table.csv")
    rows: list[dict[str, Any]] = []
    for metric, hyp, pred in H1_H3:
        if metric in table.columns:
            rows.append(_contrast_row(table, metric, cfg=cfg, family="diffusion_H1H3", hypothesis=hyp, prediction=pred))
    if H4[0] in table.columns:
        rows.append(_contrast_row(table, H4[0], cfg=cfg, family="diffusion_H4_control", hypothesis=H4[1], prediction=H4[2]))
    if MNJ_PRIMARY[0] in table.columns:
        rows.append(
            _contrast_row(
                table,
                MNJ_PRIMARY[0],
                cfg=cfg,
                family="mnj_v3_primary",
                hypothesis=MNJ_PRIMARY[1],
                prediction=MNJ_PRIMARY[2],
            )
        )
    for metric, hyp, pred in MNJ_SECONDARY:
        if metric in table.columns:
            rows.append(_contrast_row(table, metric, cfg=cfg, family="mnj_v3_secondary", hypothesis=hyp, prediction=pred))
    for metric, hyp, pred in REACH:
        if metric in table.columns:
            rows.append(_contrast_row(table, metric, cfg=cfg, family="reachability_horizon", hypothesis=hyp, prediction=pred))
    contrasts = pd.DataFrame(rows)
    if not contrasts.empty:
        contrasts = _apply_family_fdr(contrasts, "diffusion_H1H3")
        contrasts["bh_alpha"] = cfg.bh_alpha
        h1h3 = contrasts["family"] == "diffusion_H1H3"
        contrasts["bh_significant"] = np.where(
            h1h3 & contrasts["bh_q_within_family"].notna(),
            contrasts["bh_q_within_family"] < cfg.bh_alpha,
            pd.NA,
        )
    subtypes = _cpc5_subtypes(table, cfg)
    ttm = _ttm_sensitivity(table, cfg)
    write_csv(out_dir / "outcome_contrasts.csv", contrasts)
    write_csv(out_dir / "cpc5_regime_subtypes.csv", subtypes)
    write_csv(out_dir / "ttm_sensitivity_contrasts.csv", ttm)
    markdown = render_markdown(contrasts, subtypes, cfg)
    (out_dir / "outcome_contrasts.md").write_text(markdown, encoding="utf-8")
    write_json(
        out_dir / "outcome_contrasts_manifest.json",
        {
            "n_primary_rows": int(len(table)),
            "n_cpc1": int((table["contrast_group"] == cfg.good_label).sum()) if not table.empty else 0,
            "n_cpc5": int((table["contrast_group"] == cfg.poor_label).sum()) if not table.empty else 0,
            "confirmatory_status": cfg.confirmatory_status,
            "smoke": cfg.smoke,
            "note": "Exploratory pending part2. Smoke-sample contrasts are not interpretable.",
        },
    )
    print(f"Wrote contrasts for n={len(table)} primary CPC1/5 rows", flush=True)


if __name__ == "__main__":
    main()
