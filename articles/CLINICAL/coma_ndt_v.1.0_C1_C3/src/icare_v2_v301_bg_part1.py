"""COMA-BG-001: spectral/complexity-conditioned L1 geometry (sl_022).

At comparable EEG spectral/complexity background, does CPC-linked L1
geometry still separate CPC1 vs CPC5 on part1?

Covariates are recording-then-subject medians of features_raw. They are
not ACNS suppression, not raw EEG, and not Family B. L1 outcomes are
joined from existing part1 tables. Part2 stays sealed. SL-004A is not
modified.
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy import stats

from icare_v2_common import (
    ARTICLE_DIR,
    add_common_args,
    discover_h5_files,
    median_finite,
    parallel_map,
    parse_run_stem,
    participant_meta_from_handle,
    resolve_pipeline_config,
    time_reference_from_handle,
    write_csv,
    write_json,
)
from icare_v2_outcome_contrast_analysis import _contrast_row
from icare_v2_v301_l1_panel import _annotate

# Frozen before CPC-adjusted betas. Do not search combinations.
BG_TOKENS = (
    "eeg_delta",
    "eeg_alpha_theta",
    "eeg_hjorth_mobility",
    "eeg_hjorth_complexity",
)
ENTROPY_TOKEN = "eeg_permutation_entropy"
BG_COLS = tuple(f"{token}_median" for token in BG_TOKENS)
ENTROPY_COL = f"{ENTROPY_TOKEN}_median"
Z_COLS = tuple(f"z_{token}" for token in BG_TOKENS)

L1_PRIMARY = (
    ("tr_a_median", "Tr(a)", "log_if_all_positive"),
    ("h_tilde_cohort_reknn_median", "H_tilde", "identity"),
    ("g90_cohort_reknn_median", "G90", "identity"),
    ("r_ba_median", "R_b/a", "identity"),
)
L1_SECONDARY = (
    ("d_eff_cohort_reknn_median", "d_eff", "identity"),
)
L1_JOIN = {
    "ddc_patient_primary.csv": (
        "tr_a_median",
        "r_ba_median",
        "g90_cohort_reknn_median",
        "d_eff_cohort_reknn_median",
    ),
    "htilde_patient_primary.csv": ("h_tilde_cohort_reknn_median",),
    "sl004a_patient_primary.csv": (
        "g90_cohort_reknn_median",
        "d_eff_cohort_reknn_median",
    ),
}
NOT_COVARIATES = (
    "eeg_gamma",
    "eeg_highfreq_power_30_45",
    "embodied_arousal_proxy",
    "eeg_sample_entropy",
)
TERTILE_MIN_N = 10
HOLM_ALPHA = 0.05
CANONICAL_RESULTS = ARTICLE_DIR / "results" / "v3_0_1"


def _holm(p_values: list[float]) -> list[float]:
    p = np.asarray(p_values, dtype=float)
    m = p.size
    out = np.full(m, np.nan)
    order = np.argsort(p)
    running = 0.0
    for rank, idx in enumerate(order):
        if not np.isfinite(p[idx]):
            continue
        adj = min(1.0, float(p[idx]) * (m - rank))
        running = max(running, adj)
        out[idx] = running
    return [float(v) for v in out]


def _decode_names(handle: h5py.File) -> list[str]:
    if "/features_raw/names" not in handle:
        return []
    return [
        item.decode("utf-8", errors="replace") if isinstance(item, (bytes, np.bytes_)) else str(item)
        for item in handle["/features_raw/names"][:]
    ]


def _feature_median(handle: h5py.File, token: str, names: list[str] | None = None) -> float:
    if "/features_raw/values" not in handle:
        return float("nan")
    labels = names if names is not None else _decode_names(handle)
    if token not in labels:
        return float("nan")
    values = np.asarray(handle["/features_raw/values"][:, labels.index(token)], dtype=float)
    return median_finite(values)


def extract_one(path: str) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "read_ok": False,
        "read_error": None,
        "features_raw_present": False,
        "n_feature_rows": 0,
    }
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            timing = time_reference_from_handle(handle)
            row.update({k: meta[k] for k in ("cpc", "outcome", "hospital", "ttm", "age", "sex")})
            row.update(timing)
            names = _decode_names(handle)
            row["features_raw_present"] = bool(names) and "/features_raw/values" in handle
            if row["features_raw_present"]:
                row["n_feature_rows"] = int(handle["/features_raw/values"].shape[0])
            for token in BG_TOKENS + (ENTROPY_TOKEN,):
                row[f"{token}_median"] = _feature_median(handle, token, names)
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _missing_row(frame: pd.DataFrame, metric: str, *, grain: str, window: str, cfg) -> dict[str, Any]:
    work = frame[frame["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    good = work[work["contrast_group"] == cfg.good_label]
    poor = work[work["contrast_group"] == cfg.poor_label]
    g_yes = int(pd.to_numeric(good.get(metric), errors="coerce").notna().sum()) if metric in good else 0
    p_yes = int(pd.to_numeric(poor.get(metric), errors="coerce").notna().sum()) if metric in poor else 0
    g_n = int(len(good))
    p_n = int(len(poor))
    table = np.array([[g_yes, max(g_n - g_yes, 0)], [p_yes, max(p_n - p_yes, 0)]], dtype=int)
    fisher_p = float("nan")
    try:
        if table.sum() > 0:
            fisher_p = float(stats.fisher_exact(table)[1])
    except ValueError:
        pass
    return {
        "grain": grain,
        "window": window,
        "metric": metric,
        "n_cpc1_finite": g_yes,
        "n_cpc1": g_n,
        "rate_cpc1": g_yes / g_n if g_n else float("nan"),
        "n_cpc5_finite": p_yes,
        "n_cpc5": p_n,
        "rate_cpc5": p_yes / p_n if p_n else float("nan"),
        "fisher_p": fisher_p,
    }


def _patient(runs: pd.DataFrame, cfg) -> pd.DataFrame:
    work = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    if work.empty:
        return work
    agg: dict[str, Any] = {
        "cpc": ("cpc", "first"),
        "contrast_group": ("contrast_group", "first"),
        "hospital": ("hospital", "first"),
        "n_runs": ("source_h5", "nunique"),
        "n_feature_rows_sum": ("n_feature_rows", "sum"),
    }
    for col in list(BG_COLS) + [ENTROPY_COL]:
        if col in work.columns:
            agg[col] = (col, "median")
    return work.groupby("subject_id", as_index=False).agg(**agg)


def _join_l1(patients: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, list[str]]:
    out = patients.copy()
    used: list[str] = []
    search_dirs = []
    for directory in (output_dir, CANONICAL_RESULTS):
        if directory not in search_dirs:
            search_dirs.append(directory)
    for name, columns in L1_JOIN.items():
        path = next((directory / name for directory in search_dirs if (directory / name).exists()), None)
        if path is None:
            continue
        extra = pd.read_csv(path)
        if "subject_id" not in extra.columns:
            continue
        keep = ["subject_id"] + [c for c in columns if c in extra.columns and c not in out.columns]
        if len(keep) == 1:
            continue
        out = out.merge(extra[keep], on="subject_id", how="left")
        used.append(str(path.name))
    return out, used


def _zscore_from_sample(frame: pd.DataFrame, col: str) -> tuple[pd.Series, float, float]:
    raw = pd.to_numeric(frame[col], errors="coerce")
    finite = raw[np.isfinite(raw)]
    mu = float(finite.mean()) if finite.size else float("nan")
    sd = float(finite.std(ddof=0)) if finite.size else float("nan")
    if not np.isfinite(sd) or sd <= 0:
        z = pd.Series(np.where(np.isfinite(raw), 0.0, np.nan), index=frame.index, dtype=float)
        return z, mu, sd if np.isfinite(sd) else float("nan")
    return (raw - mu) / sd, mu, sd


def _outcome_transform(values: np.ndarray, rule: str) -> tuple[np.ndarray, str]:
    y = np.asarray(values, dtype=float)
    if rule == "identity":
        return y, "identity"
    finite = y[np.isfinite(y)]
    if rule == "log_if_all_positive" and finite.size and np.all(finite > 0):
        return np.log(y), "log"
    clipped = np.clip(y, 0.0, None)
    return np.log1p(clipped), "log1p"


def _fit_adjusted(frame: pd.DataFrame, *, metric: str, hypothesis: str, transform_rule: str, role: str, cfg) -> dict[str, Any]:
    import statsmodels.formula.api as smf

    cols = [metric, "contrast_group", "n_runs", *Z_COLS]
    work = frame.loc[:, [c for c in cols if c in frame.columns]].copy()
    for col in [metric, "n_runs", *Z_COLS]:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce")
    work["is_cpc1"] = (work["contrast_group"] == cfg.good_label).astype(int)
    finite_mask = np.isfinite(work[metric]) & np.isfinite(work["n_runs"])
    for col in Z_COLS:
        finite_mask &= np.isfinite(work[col])
    work = work.loc[finite_mask].copy()
    y, transform = _outcome_transform(work[metric].to_numpy(dtype=float), transform_rule)
    work["y"] = y
    formula = "y ~ z_eeg_delta + z_eeg_alpha_theta + z_eeg_hjorth_mobility + z_eeg_hjorth_complexity + is_cpc1 + n_runs"
    out: dict[str, Any] = {
        "role": role,
        "family": "bg_adjusted_primary" if role == "primary" else f"bg_adjusted_{role}",
        "metric": metric,
        "hypothesis": hypothesis,
        "y_transform": transform,
        "formula": formula,
        "cov_type": None,
        "n": int(len(work)),
        "n_cpc1": int((work["is_cpc1"] == 1).sum()),
        "n_cpc5": int((work["is_cpc1"] == 0).sum()),
        "beta_cpc1": float("nan"),
        "se_cpc1": float("nan"),
        "p_cpc1": float("nan"),
        "holm_p": float("nan"),
        "r2": float("nan"),
        "error": None,
    }
    for token in BG_TOKENS:
        out[f"beta_z_{token}"] = float("nan")
        out[f"p_z_{token}"] = float("nan")
    out["beta_n_runs"] = float("nan")
    out["p_n_runs"] = float("nan")
    if len(work) < 10 or work["is_cpc1"].nunique() < 2:
        out["error"] = "insufficient_data"
        return out
    last_error = None
    for cov_type in ("HC3", "HC1"):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fit = smf.ols(formula, data=work).fit(cov_type=cov_type)
            out["cov_type"] = cov_type
            out["beta_cpc1"] = float(fit.params["is_cpc1"])
            out["se_cpc1"] = float(fit.bse["is_cpc1"])
            out["p_cpc1"] = float(fit.pvalues["is_cpc1"])
            out["r2"] = float(fit.rsquared)
            out["beta_n_runs"] = float(fit.params["n_runs"])
            out["p_n_runs"] = float(fit.pvalues["n_runs"])
            for token in BG_TOKENS:
                key = f"z_{token}"
                out[f"beta_z_{token}"] = float(fit.params[key])
                out[f"p_z_{token}"] = float(fit.pvalues[key])
            return out
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
            continue
    out["error"] = last_error or "ols_failed"
    return out


def _spearman_row(frame: pd.DataFrame, metric: str, covariate: str, group: str) -> dict[str, Any]:
    x = pd.to_numeric(frame[covariate], errors="coerce")
    y = pd.to_numeric(frame[metric], errors="coerce")
    mask = np.isfinite(x) & np.isfinite(y)
    out = {
        "metric": metric,
        "covariate": covariate,
        "group": group,
        "n": int(mask.sum()),
        "rho": float("nan"),
        "p": float("nan"),
    }
    if int(mask.sum()) >= 10:
        rho, p = stats.spearmanr(x[mask], y[mask])
        out["rho"] = float(rho)
        out["p"] = float(p)
    return out


def _tertile_cuts(values: np.ndarray) -> tuple[float, float]:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    q1, q2 = np.quantile(finite, [1.0 / 3.0, 2.0 / 3.0])
    return float(q1), float(q2)


def _assign_tertile(value: float, q1: float, q2: float) -> str:
    if not np.isfinite(value):
        return "unassigned"
    if value <= q1:
        return "T1_low"
    if value <= q2:
        return "T2_mid"
    return "T3_high"


def _claim_status(adj: pd.DataFrame) -> str:
    primary = adj[adj["role"] == "primary"].copy()
    if primary.empty:
        return "insufficient"
    tra = primary[primary["metric"] == "tr_a_median"]
    if tra.empty or not np.isfinite(tra.iloc[0].get("holm_p", float("nan"))):
        return "insufficient"
    tra_pass = float(tra.iloc[0]["holm_p"]) < HOLM_ALPHA
    others = primary[primary["metric"] != "tr_a_median"]
    other_pass = [
        float(p) < HOLM_ALPHA for p in others["holm_p"] if np.isfinite(p)
    ]
    if tra_pass and other_pass and all(other_pass):
        return "PASS"
    if tra_pass:
        return "PASS_WITH_CAVEAT"
    return "NULL_AFTER_BACKGROUND"


def _fmt(value: Any, digits: int = 3) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if not np.isfinite(number):
        return "-"
    return f"{number:.{digits}g}"


def _render(
    *,
    cfg,
    missing: pd.DataFrame,
    bg_contrasts: pd.DataFrame,
    spearman: pd.DataFrame,
    adj: pd.DataFrame,
    tertile: pd.DataFrame,
    n_runs: int,
    n_patients: int,
    n_cpc1: int,
    n_cpc5: int,
    claim: str,
    z_stats: dict[str, Any],
) -> str:
    lines = [
        "# COMA-BG-001 part1 (sl_022 / sl_023)",
        "",
        f"Bundle `{cfg.bundle_id}`. Spectral/complexity background from",
        "`features_raw` recording-then-subject medians. Not ACNS suppression.",
        "Not raw EEG. Not Family B. L1 outcomes reused from existing part1",
        "tables; H1-H4 are not recomputed. Part2 is not opened. Holm is a new",
        "family of four background-adjusted CPC coefficients, not SL-004A.",
        "",
        f"Recordings extracted: {n_runs}. Patients in 0-12h CPC1/CPC5: {n_patients}",
        f"(CPC1 n={n_cpc1}, CPC5 n={n_cpc5}). Claim status: **{claim}**.",
        "",
        "Frozen covariates: `eeg_delta` (primary background axis),",
        "`eeg_alpha_theta`, `eeg_hjorth_mobility`, `eeg_hjorth_complexity`.",
        "Not used: gamma / highfreq / embodied_arousal_proxy (duplicated in the",
        "inventory sample) or both entropy columns.",
        "",
        "## Missingness by CPC (before metric values)",
        "",
        "| Grain | Window | Metric | CPC1 | CPC5 | Fisher p |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    if missing.empty:
        lines.append("| - | - | - | - | - | - |")
    else:
        for _, row in missing.iterrows():
            lines.append(
                f"| {row['grain']} | {row['window']} | `{row['metric']}` | "
                f"{int(row['n_cpc1_finite'])}/{int(row['n_cpc1'])} "
                f"({100 * row['rate_cpc1']:.1f}%) | "
                f"{int(row['n_cpc5_finite'])}/{int(row['n_cpc5'])} "
                f"({100 * row['rate_cpc5']:.1f}%) | "
                f"{_fmt(row['fisher_p'])} |"
            )
    lines += [
        "",
        "## Unadjusted background contrasts (0-12h subject median)",
        "",
        "| Metric | n CPC1 | n CPC5 | CPC1 med | CPC5 med | Cliff d | MW p |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    if bg_contrasts.empty:
        lines.append("| - | - | - | - | - | - | - |")
    else:
        for _, row in bg_contrasts.iterrows():
            lines.append(
                f"| `{row['metric']}` | {int(row['n_cpc1'])} | {int(row['n_cpc5'])} | "
                f"{_fmt(row['cpc1_median'], 4)} | {_fmt(row['cpc5_median'], 4)} | "
                f"{_fmt(row['cliffs_delta_cpc1_minus_cpc5'])} | "
                f"{_fmt(row['mannwhitney_p'])} |"
            )
    lines += [
        "",
        "## Spearman: L1 vs spectral/complexity background",
        "",
        "| Metric | Covariate | Group | n | rho | p |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    if spearman.empty:
        lines.append("| - | - | - | - | - | - |")
    else:
        for _, row in spearman.iterrows():
            lines.append(
                f"| `{row['metric']}` | `{row['covariate']}` | {row['group']} | "
                f"{int(row['n'])} | {_fmt(row['rho'])} | {_fmt(row['p'])} |"
            )
    z_bits = ", ".join(
        f"{k} mean={_fmt(v.get('mean'))} sd={_fmt(v.get('sd'))}" for k, v in z_stats.items()
    )
    lines += [
        "",
        "## Primary: background-adjusted OLS (HC3, subject grain)",
        "",
        "Frozen formula: `y ~ z(eeg_delta)+z(eeg_alpha_theta)+z(hjorth_mobility)"
        "+z(hjorth_complexity)+I(CPC1)+n_runs`.",
        f"z-scores from the CPC1+CPC5 analysis sample ({z_bits}).",
        "Primary y is log(Tr(a)) if all finite Tr(a)>0, else log1p.",
        "Holm is only across the four CPC coefficients.",
        "",
        "| Role | Metric | y | n CPC1 | n CPC5 | beta_CPC1 | SE | p | Holm p | R2 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    if adj.empty:
        lines.append("| - | - | - | - | - | - | - | - | - | - |")
    else:
        for _, row in adj.iterrows():
            holm = row.get("holm_p", float("nan"))
            holm_s = "-" if not np.isfinite(holm) else _fmt(holm)
            lines.append(
                f"| {row['role']} | `{row['metric']}` | {row['y_transform']} | "
                f"{int(row['n_cpc1'])} | {int(row['n_cpc5'])} | "
                f"{_fmt(row['beta_cpc1'])} | {_fmt(row['se_cpc1'])} | "
                f"{_fmt(row['p_cpc1'])} | {holm_s} | {_fmt(row['r2'])} |"
            )
    lines += [
        "",
        "## Sensitivity: Tr(a) within eeg_delta tertiles",
        "",
        "Cuts are pooled CPC1+CPC5 quantiles of subject-median `eeg_delta`,",
        "not CPC-optimized. A tertile is tested only if both arms have n>=10.",
        "",
        "| Tertile | Cut | n CPC1 | n CPC5 | CPC1 med Tr(a) | CPC5 med Tr(a) | Cliff d | MW p | Status |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    if tertile.empty:
        lines.append("| - | - | - | - | - | - | - | - | - |")
    else:
        for _, row in tertile.iterrows():
            lines.append(
                f"| {row['tertile']} | {row['cut_label']} | {int(row['n_cpc1'])} | "
                f"{int(row['n_cpc5'])} | {_fmt(row['cpc1_median'], 4)} | "
                f"{_fmt(row['cpc5_median'], 4)} | {_fmt(row['cliffs_delta_cpc1_minus_cpc5'])} | "
                f"{_fmt(row['mannwhitney_p'])} | {row['status']} |"
            )
    lines += [
        "",
        "No composite coma score is formed. This is not ACNS suppression",
        "conditioning. This Holm family is not added to SL-004A.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    paths = discover_h5_files(cfg.raw_root, subject_allowlist=cfg.subject_allowlist, limit_h5=cfg.limit_h5)
    print(f"{cfg.bundle_id}: BG extract {len(paths)} files", flush=True)
    rows = parallel_map(extract_one, [str(p) for p in paths], workers=cfg.workers, desc="bg")
    runs = _annotate(pd.DataFrame(rows), cfg)
    patients = _patient(runs, cfg)
    patients, joined = _join_l1(patients, cfg.output_dir)
    missing_rows = []
    rec_primary = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])]
    for metric in BG_COLS:
        missing_rows.append(_missing_row(rec_primary, metric, grain="recording", window="0_12h", cfg=cfg))
        missing_rows.append(_missing_row(patients, metric, grain="subject", window="0_12h", cfg=cfg))
    missing = pd.DataFrame(missing_rows)
    print("missingness by CPC (before contrasts)", flush=True)
    if not missing.empty:
        print(missing.to_string(index=False), flush=True)

    bg_contrast_rows = []
    for metric in BG_COLS:
        bg_contrast_rows.append(
            _contrast_row(
                patients,
                metric,
                cfg=cfg,
                family="bg_unadjusted",
                hypothesis=metric,
                prediction="descriptive spectral/complexity background",
            )
        )
    bg_contrasts = pd.DataFrame(bg_contrast_rows)

    l1_metrics = [item[0] for item in L1_PRIMARY + L1_SECONDARY]
    spearman_rows = []
    for metric in l1_metrics:
        if metric not in patients.columns:
            continue
        for covariate in BG_COLS:
            spearman_rows.append(_spearman_row(patients, metric, covariate, "all"))
            spearman_rows.append(
                _spearman_row(patients[patients["contrast_group"] == cfg.good_label], metric, covariate, cfg.good_label)
            )
            spearman_rows.append(
                _spearman_row(patients[patients["contrast_group"] == cfg.poor_label], metric, covariate, cfg.poor_label)
            )
    spearman = pd.DataFrame(spearman_rows)

    analysis = patients[patients["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    z_stats: dict[str, Any] = {}
    for token, col, zcol in zip(BG_TOKENS, BG_COLS, Z_COLS):
        analysis[zcol], mu, sd = _zscore_from_sample(analysis, col)
        z_stats[token] = {"mean": mu, "sd": sd}
        patients[zcol] = np.nan
        patients.loc[analysis.index, zcol] = analysis[zcol]

    adj_rows = []
    for metric, hyp, rule in L1_PRIMARY:
        if metric not in analysis.columns:
            adj_rows.append(
                {
                    "role": "primary",
                    "family": "bg_adjusted_primary",
                    "metric": metric,
                    "hypothesis": hyp,
                    "error": "missing_l1_column",
                    "p_cpc1": float("nan"),
                    "holm_p": float("nan"),
                    "n_cpc1": 0,
                    "n_cpc5": 0,
                    "beta_cpc1": float("nan"),
                    "se_cpc1": float("nan"),
                    "y_transform": rule,
                    "r2": float("nan"),
                }
            )
            continue
        adj_rows.append(
            _fit_adjusted(analysis, metric=metric, hypothesis=hyp, transform_rule=rule, role="primary", cfg=cfg)
        )
    for metric, hyp, rule in L1_SECONDARY:
        if metric in analysis.columns:
            adj_rows.append(
                _fit_adjusted(analysis, metric=metric, hypothesis=hyp, transform_rule=rule, role="secondary", cfg=cfg)
            )
    adj = pd.DataFrame(adj_rows)
    if not adj.empty:
        idx = adj.index[adj["role"] == "primary"].tolist()
        holm = _holm([float(adj.loc[i, "p_cpc1"]) for i in idx])
        for i, value in zip(idx, holm):
            adj.loc[i, "holm_p"] = value
    claim = _claim_status(adj)

    tertile_rows = []
    if "eeg_delta_median" in analysis.columns and "tr_a_median" in analysis.columns:
        q1, q2 = _tertile_cuts(analysis["eeg_delta_median"].to_numpy(dtype=float))
        analysis["eeg_delta_tertile"] = [
            _assign_tertile(value, q1, q2) for value in pd.to_numeric(analysis["eeg_delta_median"], errors="coerce")
        ]
        patients["eeg_delta_tertile"] = pd.Series(pd.NA, index=patients.index, dtype="object")
        patients.loc[analysis.index, "eeg_delta_tertile"] = analysis["eeg_delta_tertile"].astype("object")
        cut_labels = {
            "T1_low": f"delta <= {q1:.4g}",
            "T2_mid": f"{q1:.4g} < delta <= {q2:.4g}",
            "T3_high": f"delta > {q2:.4g}",
        }
        for tertile_name in ("T1_low", "T2_mid", "T3_high"):
            block = analysis[analysis["eeg_delta_tertile"] == tertile_name]
            n1 = int(
                np.isfinite(
                    pd.to_numeric(
                        block.loc[block["contrast_group"] == cfg.good_label, "tr_a_median"],
                        errors="coerce",
                    )
                ).sum()
            )
            n5 = int(
                np.isfinite(
                    pd.to_numeric(
                        block.loc[block["contrast_group"] == cfg.poor_label, "tr_a_median"],
                        errors="coerce",
                    )
                ).sum()
            )
            status = "tested" if n1 >= TERTILE_MIN_N and n5 >= TERTILE_MIN_N else "skipped_n<10"
            row = {
                "tertile": tertile_name,
                "cut_label": cut_labels[tertile_name],
                "q1": q1,
                "q2": q2,
                "n_cpc1": n1,
                "n_cpc5": n5,
                "cpc1_median": float("nan"),
                "cpc5_median": float("nan"),
                "cliffs_delta_cpc1_minus_cpc5": float("nan"),
                "mannwhitney_p": float("nan"),
                "status": status,
            }
            if status == "tested":
                contrast = _contrast_row(
                    block,
                    "tr_a_median",
                    cfg=cfg,
                    family="bg_tertile_tra",
                    hypothesis="Tr(a)_within_eeg_delta_tertile",
                    prediction="descriptive; skip if n<10 per arm",
                )
                row["cpc1_median"] = contrast["cpc1_median"]
                row["cpc5_median"] = contrast["cpc5_median"]
                row["cliffs_delta_cpc1_minus_cpc5"] = contrast["cliffs_delta_cpc1_minus_cpc5"]
                row["mannwhitney_p"] = contrast["mannwhitney_p"]
                row["n_cpc1"] = contrast["n_cpc1"]
                row["n_cpc5"] = contrast["n_cpc5"]
            tertile_rows.append(row)
    tertile = pd.DataFrame(tertile_rows)

    n_cpc1 = int((patients["contrast_group"] == cfg.good_label).sum()) if not patients.empty else 0
    n_cpc5 = int((patients["contrast_group"] == cfg.poor_label).sum()) if not patients.empty else 0
    out = cfg.output_dir
    write_csv(out / "bg_run_level.csv", runs)
    write_csv(out / "bg_patient_primary.csv", patients)
    write_csv(out / "bg_missingness_by_cpc.csv", missing)
    write_csv(out / "bg_background_contrasts.csv", bg_contrasts)
    write_csv(out / "bg_spearman.csv", spearman)
    write_csv(out / "bg_adjusted_ols.csv", adj)
    write_csv(out / "bg_tertile_tra.csv", tertile)
    md = _render(
        cfg=cfg,
        missing=missing,
        bg_contrasts=bg_contrasts,
        spearman=spearman,
        adj=adj,
        tertile=tertile,
        n_runs=int(len(runs)),
        n_patients=int(len(patients)),
        n_cpc1=n_cpc1,
        n_cpc5=n_cpc5,
        claim=claim,
        z_stats=z_stats,
    )
    (out / "bg_part1.md").write_text(md, encoding="utf-8")
    write_json(
        out / "bg_part1_manifest.json",
        {
            "experiment": "COMA-BG-001",
            "frame": "coords_3d_cohort_anchored_outcomes_joined",
            "background": "spectral_complexity_features_raw",
            "not": [
                "acns_suppression",
                "raw_eeg",
                "family_b_jacobian",
                "sl004a_holm",
                "part2",
                *NOT_COVARIATES,
            ],
            "frozen_covariates": list(BG_TOKENS),
            "optional_sensitivity_column": ENTROPY_TOKEN,
            "l1_sources_used": joined,
            "z_from": "cpc1_plus_cpc5_analysis_sample",
            "z_stats": z_stats,
            "holm_family": [item[0] for item in L1_PRIMARY],
            "holm_not": "SL-004A",
            "claim_status": claim,
            "part2_opened": False,
            "n_runs": int(len(runs)),
            "n_patients": int(len(patients)),
            "n_cpc1": n_cpc1,
            "n_cpc5": n_cpc5,
        },
    )
    print(f"wrote {out / 'bg_part1.md'}", flush=True)
    print(f"claim_status={claim} n_cpc1={n_cpc1} n_cpc5={n_cpc5}", flush=True)
    if not bg_contrasts.empty:
        print(
            bg_contrasts[["metric", "n_cpc1", "n_cpc5", "cliffs_delta_cpc1_minus_cpc5", "mannwhitney_p"]].to_string(
                index=False
            ),
            flush=True,
        )
    if not adj.empty:
        cols = [c for c in ("role", "metric", "y_transform", "n_cpc1", "n_cpc5", "beta_cpc1", "p_cpc1", "holm_p", "r2") if c in adj.columns]
        print(adj[cols].to_string(index=False), flush=True)
    if not tertile.empty:
        print(tertile.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
