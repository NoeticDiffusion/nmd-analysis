"""COMA-STAB-ADJ-001: level-adjusted between-run MAD (sl_012).

Frozen before CPC coefficient inspection:

    log(MAD_i + eps) ~ log(median_i + eps) + I(CPC1) + n_runs

HC3 SE. Holm only across the two STAB primaries (G90, R_b/a). Hospital
is sensitivity, not primary. RD = MAD/median is sensitivity.
Part2 stays sealed. Separate family from SL-004A.
"""
from __future__ import annotations

import argparse
import warnings
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from icare_v2_common import add_common_args, resolve_pipeline_config, write_csv, write_json
from icare_v2_outcome_contrast_analysis import _contrast_row
from icare_v2_v301_l1_prepart2_gates import _holm

EPS = 1e-12
MIN_RUNS = 2
RD_LEVEL_FLOOR = 1e-8
PRIMARY = (
    ("g90_cohort_reknn_median", "G90"),
    ("r_ba_median", "R_ba"),
)
EXPLORATORY = (
    ("f_perp_median", "F_perp"),
    ("d_eff_cohort_reknn_median", "d_eff"),
)


def _mad(values: np.ndarray) -> float:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size < MIN_RUNS:
        return float("nan")
    return float(np.median(np.abs(finite - np.median(finite))))


def _patient_level(runs: pd.DataFrame, cfg, metrics: tuple[str, ...]) -> pd.DataFrame:
    work = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    rows = []
    for subject, block in work.groupby("subject_id"):
        row: dict[str, Any] = {
            "subject_id": subject,
            "cpc": block["cpc"].iloc[0],
            "contrast_group": block["contrast_group"].iloc[0],
            "hospital": block["hospital"].iloc[0] if "hospital" in block.columns else None,
            "n_runs": int(block["source_h5"].nunique()),
        }
        for metric in metrics:
            if metric not in block.columns:
                continue
            values = pd.to_numeric(block[metric], errors="coerce").to_numpy(dtype=float)
            finite = values[np.isfinite(values)]
            row[f"{metric}_n"] = int(finite.size)
            row[f"{metric}_level"] = float(np.median(finite)) if finite.size else float("nan")
            row[f"{metric}_mad"] = _mad(values)
            level = row[f"{metric}_level"]
            mad = row[f"{metric}_mad"]
            if np.isfinite(level) and np.isfinite(mad) and level > RD_LEVEL_FLOOR:
                row[f"{metric}_rd"] = float(mad / level)
            else:
                row[f"{metric}_rd"] = float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def _fit_adj(frame: pd.DataFrame, *, level: str, mad: str, cfg, extra: str | None = None) -> dict[str, Any]:
    import statsmodels.formula.api as smf

    work = frame[["contrast_group", "n_runs", "hospital", level, mad]].copy()
    work["level"] = pd.to_numeric(work[level], errors="coerce")
    work["mad"] = pd.to_numeric(work[mad], errors="coerce")
    work["n_runs"] = pd.to_numeric(work["n_runs"], errors="coerce")
    work["is_cpc1"] = (work["contrast_group"] == cfg.good_label).astype(int)
    work = work[np.isfinite(work["level"]) & np.isfinite(work["mad"]) & np.isfinite(work["n_runs"])]
    work["log_mad"] = np.log(work["mad"] + EPS)
    work["log_level"] = np.log(np.clip(work["level"], 0.0, None) + EPS)
    out: dict[str, Any] = {
        "metric": mad,
        "n": int(len(work)),
        "n_cpc1": int((work["is_cpc1"] == 1).sum()),
        "n_cpc5": int((work["is_cpc1"] == 0).sum()),
        "formula": "log_mad ~ log_level + is_cpc1 + n_runs",
        "beta_cpc1": float("nan"),
        "se_cpc1": float("nan"),
        "p_cpc1": float("nan"),
        "beta_log_level": float("nan"),
        "p_log_level": float("nan"),
        "beta_n_runs": float("nan"),
        "p_n_runs": float("nan"),
        "r2": float("nan"),
        "error": None,
    }
    if extra == "hospital":
        out["formula"] = "log_mad ~ log_level + is_cpc1 + n_runs + C(hospital)"
    if len(work) < 10 or work["is_cpc1"].nunique() < 2:
        out["error"] = "insufficient_data"
        return out
    formula = out["formula"]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = smf.ols(formula, data=work).fit(cov_type="HC3")
        out["beta_cpc1"] = float(fit.params["is_cpc1"])
        out["se_cpc1"] = float(fit.bse["is_cpc1"])
        out["p_cpc1"] = float(fit.pvalues["is_cpc1"])
        out["beta_log_level"] = float(fit.params["log_level"])
        out["p_log_level"] = float(fit.pvalues["log_level"])
        out["beta_n_runs"] = float(fit.params["n_runs"])
        out["p_n_runs"] = float(fit.pvalues["n_runs"])
        out["r2"] = float(fit.rsquared)
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def _spearman_level_mad(frame: pd.DataFrame, level: str, mad: str, group: str | None = None) -> dict[str, Any]:
    work = frame if group is None else frame[frame["contrast_group"] == group]
    x = pd.to_numeric(work[level], errors="coerce")
    y = pd.to_numeric(work[mad], errors="coerce")
    mask = np.isfinite(x) & np.isfinite(y)
    out = {"metric": mad, "group": group or "all", "n": int(mask.sum()), "rho": float("nan"), "p": float("nan")}
    if int(mask.sum()) >= 10:
        rho, p = stats.spearmanr(x[mask], y[mask])
        out["rho"] = float(rho)
        out["p"] = float(p)
    return out


def _render(*, adj: pd.DataFrame, rd: pd.DataFrame, spearman: pd.DataFrame) -> str:
    lines = [
        "# COMA-STAB-ADJ-001 part1 (sl_012)",
        "",
        "Does CPC5 retain greater between-run MAD after accounting for higher central level?",
        "Primary: `log(MAD+eps) ~ log(level+eps) + I(CPC1) + n_runs`, HC3.",
        "beta_cpc1 < 0 means CPC1 is more stable after level adjustment.",
        "RD = MAD/level is sensitivity. Hospital is sensitivity. Part2 not opened.",
        "",
        "## Level-adjusted models",
        "",
        "| Role | Metric | Formula | n CPC1 | n CPC5 | beta_cpc1 | SE | p | Holm p | beta_log_level | R2 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |",
    ]
    for _, row in adj.iterrows():
        holm = row.get("holm_p", float("nan"))
        holm_s = "-" if not np.isfinite(holm) else f"{holm:.3g}"
        lines.append(
            f"| {row['role']} | `{row['metric']}` | {row['formula']} | {int(row['n_cpc1'])} | "
            f"{int(row['n_cpc5'])} | {row['beta_cpc1']:.3g} | {row['se_cpc1']:.3g} | "
            f"{row['p_cpc1']:.3g} | {holm_s} | {row['beta_log_level']:.3g} | {row['r2']:.3g} |"
        )
    lines += [
        "",
        "## Relative dispersion (MAD / level)",
        "",
        "| Family | Metric | n CPC1 | n CPC5 | CPC1 med | CPC5 med | d | MW p |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    if rd.empty:
        lines.append("| - | - | - | - | - | - | - | - |")
    else:
        for _, row in rd.iterrows():
            lines.append(
                f"| {row['family']} | `{row['metric']}` | {int(row['n_cpc1'])} | {int(row['n_cpc5'])} | "
                f"{row['cpc1_median']:.4g} | {row['cpc5_median']:.4g} | "
                f"{row['cohens_d_cpc1_minus_cpc5']:.3g} | {row['mannwhitney_p']:.3g} |"
            )
    lines += [
        "",
        "## Spearman MAD vs level (mechanical-coupling diagnostic)",
        "",
        "| Metric | Group | n | rho | p |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for _, row in spearman.iterrows():
        lines.append(f"| `{row['metric']}` | {row['group']} | {int(row['n'])} | {row['rho']:.3g} | {row['p']:.3g} |")
    lines += ["", "Not added to the SL-004A Holm family.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    runs = pd.read_csv(cfg.output_dir / "ddc_run_level.csv")
    metrics = tuple(m for m, _ in PRIMARY + EXPLORATORY)
    patients = _patient_level(runs, cfg, metrics)
    adj_rows = []
    for role, specs, extra in (
        ("primary", PRIMARY, None),
        ("sensitivity_hospital", PRIMARY, "hospital"),
        ("exploratory", EXPLORATORY, None),
    ):
        for metric, hyp in specs:
            row = _fit_adj(patients, level=f"{metric}_level", mad=f"{metric}_mad", cfg=cfg, extra=extra)
            row["role"] = role
            row["hypothesis"] = hyp
            adj_rows.append(row)
    adj = pd.DataFrame(adj_rows)
    idx = adj.index[adj["role"] == "primary"].tolist()
    holm = _holm([float(adj.loc[i, "p_cpc1"]) for i in idx])
    for i, value in zip(idx, holm):
        adj.loc[i, "holm_p"] = value
    rd_rows = []
    for metric, hyp in PRIMARY:
        col = f"{metric}_rd"
        if col in patients.columns:
            rd_rows.append(
                _contrast_row(
                    patients,
                    col,
                    cfg=cfg,
                    family="stab_adj_rd",
                    hypothesis=hyp,
                    prediction="CPC1 < CPC5 after scaling by level",
                )
            )
    rd = pd.DataFrame(rd_rows)
    spearman_rows = []
    for metric, _ in PRIMARY + EXPLORATORY:
        for group in (None, cfg.good_label, cfg.poor_label):
            spearman_rows.append(_spearman_level_mad(patients, f"{metric}_level", f"{metric}_mad", group))
    spearman = pd.DataFrame(spearman_rows)
    out = cfg.output_dir
    write_csv(out / "stab_adj_patient.csv", patients)
    write_csv(out / "stab_adj_models.csv", adj)
    write_csv(out / "stab_adj_rd_contrasts.csv", rd)
    write_csv(out / "stab_adj_spearman.csv", spearman)
    md = _render(adj=adj, rd=rd, spearman=spearman)
    (out / "stab_adj_part1.md").write_text(md, encoding="utf-8")
    write_json(
        out / "stab_adj_part1_manifest.json",
        {
            "experiment": "COMA-STAB-ADJ-001",
            "formula": "log_mad ~ log_level + is_cpc1 + n_runs",
            "covariance": "HC3",
            "eps": EPS,
            "part2_opened": False,
            "not_added_to": ["SL-004A"],
        },
    )
    print(f"wrote {out / 'stab_adj_part1.md'}", flush=True)
    print(adj[["role", "metric", "n_cpc1", "n_cpc5", "beta_cpc1", "p_cpc1"]].to_string(index=False), flush=True)
    if not rd.empty:
        print(rd[["metric", "n_cpc1", "n_cpc5", "cohens_d_cpc1_minus_cpc5", "mannwhitney_p"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
