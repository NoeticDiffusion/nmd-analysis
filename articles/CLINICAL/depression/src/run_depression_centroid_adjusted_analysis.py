from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats


DATASET = "ds003478"
REPO_ROOT = Path(__file__).resolve().parents[4]
ARTICLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "depression_ds003478_20260521"
FALLBACK_ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis"
RESULTS_ROOT = ARTICLE_DIR / "results"
PARTICIPANTS_PATH = ARTICLE_DIR / "metadata" / "participants.tsv"

LOW_BDI_LABEL = "BDI 0-13"
HIGH_BDI_LABEL = "BDI 20-63"
BDI_BAND_ORDER = [LOW_BDI_LABEL, "BDI 14-19", HIGH_BDI_LABEL]

COORDS_3D = ["m_mean", "d_mean", "e_mean"]
COORDS_9D = [
    "d_l_mean",
    "d_n_mean",
    "d_s_mean",
    "e_e_mean",
    "e_m_mean",
    "e_s_mean",
    "m_a_mean",
    "m_e_mean",
    "m_o_mean",
]

BASELINE_METRICS = {
    "3d": ["m_mean", "m_median", "d_mean", "d_median", "e_mean", "e_median"],
    "9d": [
        "d_l_mean",
        "d_l_median",
        "d_n_mean",
        "d_n_median",
        "d_s_mean",
        "d_s_median",
        "e_e_mean",
        "e_e_median",
        "e_m_mean",
        "e_m_median",
        "e_s_mean",
        "e_s_median",
        "m_a_mean",
        "m_a_median",
        "m_e_mean",
        "m_e_median",
        "m_o_mean",
        "m_o_median",
    ],
}


@dataclass(frozen=True)
class TargetSpec:
    block_key: str
    title: str
    analysis_type: str
    metric: str
    centroid_family: str
    source_group: str | None = None
    target_group: str | None = None


TARGET_SPECS = (
    TargetSpec(
        block_key="mnj_3d",
        title="Global 3D MNJ",
        analysis_type="global_mnps_jacobian_3d",
        metric="spectral_radius_median",
        centroid_family="3d",
    ),
    TargetSpec(
        block_key="mnj_9d",
        title="Global 9D MNJ",
        analysis_type="global_mnps_jacobian_9d",
        metric="rotational_power_mean",
        centroid_family="9d",
    ),
    TargetSpec(
        block_key="block_mnj_m_to_m",
        title="Block MNJ m->m",
        analysis_type="global_mnps_jacobian_9d_block_jacobian",
        metric="block_frobenius_mean",
        centroid_family="9d",
        source_group="m",
        target_group="m",
    ),
    TargetSpec(
        block_key="block_mnj_m_to_d",
        title="Block MNJ m->d",
        analysis_type="global_mnps_jacobian_9d_block_jacobian",
        metric="block_frobenius_mean",
        centroid_family="9d",
        source_group="m",
        target_group="d",
    ),
    TargetSpec(
        block_key="reachability",
        title="Reachability cones",
        analysis_type="reachability_cones",
        metric="tube_log_eig_var_mean",
        centroid_family="9d",
    ),
    TargetSpec(
        block_key="emmi",
        title="Tier-2 EMMI",
        analysis_type="tier2_emmi",
        metric="mv_median",
        centroid_family="3d",
    ),
    TargetSpec(
        block_key="distribution",
        title="Distribution summary",
        analysis_type="dist_summary",
        metric="e_m_mad_sigma",
        centroid_family="9d",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run centroid-adjusted depression analyses for ds003478.")
    parser.add_argument("--analysis-root", type=Path, default=None)
    parser.add_argument("--results-root", type=Path, default=RESULTS_ROOT)
    return parser.parse_args()


def _analysis_roots(preferred: Path | None) -> list[Path]:
    ordered: list[Path] = []
    for root in (preferred, DEFAULT_ANALYSIS_ROOT, FALLBACK_ANALYSIS_ROOT):
        if root is None:
            continue
        if root not in ordered:
            ordered.append(root)
    return ordered


def _latest_parquet(roots: Iterable[Path], stem: str) -> Path:
    for root in roots:
        matches = sorted(root.glob(f"{DATASET}_{stem}_*.parquet"))
        if matches:
            return matches[-1]
    searched = ", ".join(str(root) for root in roots)
    raise FileNotFoundError(f"No {stem} parquet found for {DATASET} under: {searched}")


def _bh_fdr(values: pd.Series) -> pd.Series:
    arr = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    valid = np.isfinite(arr)
    if not valid.any():
        return pd.Series(out, index=values.index, dtype=float)
    p = arr[valid]
    order = np.argsort(p)
    ranked = p[order]
    n = ranked.size
    adjusted = ranked * n / np.arange(1, n + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    out_valid = np.empty_like(adjusted)
    out_valid[order] = adjusted
    out[valid] = out_valid
    return pd.Series(out, index=values.index, dtype=float)


def _cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 2 or right.size < 2:
        return float("nan")
    left_var = left.var(ddof=1)
    right_var = right.var(ddof=1)
    pooled_var = ((left.size - 1) * left_var + (right.size - 1) * right_var) / (left.size + right.size - 2)
    if not np.isfinite(pooled_var) or pooled_var <= 0:
        return float("nan")
    return float((right.mean() - left.mean()) / np.sqrt(pooled_var))


def _sig_tier(p_value: float | None, q_value: float | None) -> str:
    if q_value is not None and np.isfinite(q_value) and q_value <= 0.05:
        return "q<=0.05"
    if p_value is not None and np.isfinite(p_value) and p_value < 0.05:
        return "p<0.05"
    if p_value is not None and np.isfinite(p_value) and p_value < 0.1:
        return "p<0.1"
    return "ns"


def _add_constant(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if x.ndim == 1:
        x = x[:, None]
    return np.column_stack([np.ones(x.shape[0], dtype=float), x])


def _ols_fit(y: np.ndarray, x: np.ndarray) -> dict[str, np.ndarray | float]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float).reshape(-1)
    xtx_inv = np.linalg.pinv(x.T @ x)
    beta = xtx_inv @ x.T @ y
    fitted = x @ beta
    resid = y - fitted
    tss = float(np.sum((y - y.mean()) ** 2))
    rss = float(np.sum(resid**2))
    n, p = x.shape
    r2 = float(1.0 - rss / tss) if tss > 0 else 0.0
    r2_adj = float(1.0 - (1.0 - r2) * (n - 1) / max(n - p, 1))
    return {
        "beta": beta,
        "fitted": fitted,
        "resid": resid,
        "xtx_inv": xtx_inv,
        "r2": r2,
        "r2_adj": r2_adj,
        "n": float(n),
        "p": float(p),
    }


def _ols_hc3_inference(y: np.ndarray, x: np.ndarray) -> dict[str, np.ndarray | float]:
    fit = _ols_fit(y, x)
    beta = np.asarray(fit["beta"], dtype=float)
    resid = np.asarray(fit["resid"], dtype=float)
    xtx_inv = np.asarray(fit["xtx_inv"], dtype=float)
    n = int(fit["n"])
    p = int(fit["p"])
    leverage = np.einsum("ij,jk,ik->i", x, xtx_inv, x)
    denom = np.clip(1.0 - leverage, 1e-8, None)
    scale = (resid / denom) ** 2
    meat = (x.T * scale) @ x
    cov_hc3 = xtx_inv @ meat @ xtx_inv
    se = np.sqrt(np.clip(np.diag(cov_hc3), 0.0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        t_values = beta / se
    df = max(n - p, 1)
    p_values = 2.0 * stats.t.sf(np.abs(t_values), df)
    return {
        **fit,
        "cov_hc3": cov_hc3,
        "se": se,
        "t_values": t_values,
        "p_values": p_values,
        "df_resid": float(df),
    }


def load_participants() -> pd.DataFrame:
    phenos = pd.read_csv(PARTICIPANTS_PATH, sep="\t")
    phenos["BDI"] = pd.to_numeric(phenos["BDI"], errors="coerce")
    phenos["age"] = pd.to_numeric(phenos["age"], errors="coerce")
    phenos["female"] = pd.to_numeric(phenos["sex"], errors="coerce").eq(1)
    phenos["bdi_band"] = pd.cut(
        phenos["BDI"],
        bins=[-0.1, 13, 19, 63],
        labels=BDI_BAND_ORDER,
        include_lowest=True,
    )
    phenos["bdi_band"] = phenos["bdi_band"].astype(object)
    return phenos


def _subject_metric_series(
    subject_metrics: pd.DataFrame,
    *,
    analysis_type: str,
    metric: str,
    source_group: str | None = None,
    target_group: str | None = None,
) -> pd.DataFrame:
    frame = subject_metrics[
        (subject_metrics["analysis_type"] == analysis_type)
        & (subject_metrics["metric"] == metric)
    ].copy()
    if source_group is not None:
        frame = frame[frame["source_group"] == source_group].copy()
    if target_group is not None:
        frame = frame[frame["target_group"] == target_group].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["value"].notna()].copy()
    if frame.empty:
        return pd.DataFrame(columns=["subject_id", "value"])
    return frame.groupby("subject_id", as_index=False).agg(value=("value", "mean"))


def _subject_metric_wide(
    subject_metrics: pd.DataFrame,
    *,
    analysis_type: str,
    metrics: list[str],
) -> pd.DataFrame:
    frame = subject_metrics[
        (subject_metrics["analysis_type"] == analysis_type)
        & (subject_metrics["metric"].isin(metrics))
    ].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["value"].notna()].copy()
    if frame.empty:
        return pd.DataFrame(columns=["subject_id"] + metrics)
    grouped = frame.groupby(["subject_id", "metric"], as_index=False).agg(value=("value", "mean"))
    wide = grouped.pivot(index="subject_id", columns="metric", values="value").reset_index()
    return wide


def build_baseline_centroid_summary(
    subject_metrics: pd.DataFrame,
    phenos: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    band_lookup = phenos[["participant_id", "bdi_band"]].rename(columns={"participant_id": "subject_id"})
    for family, metrics in BASELINE_METRICS.items():
        analysis_type = "global_mnps_3d" if family == "3d" else "global_mnps_9d"
        wide = _subject_metric_wide(subject_metrics, analysis_type=analysis_type, metrics=metrics)
        merged = wide.merge(band_lookup, on="subject_id", how="left")
        merged = merged[merged["bdi_band"].isin([LOW_BDI_LABEL, HIGH_BDI_LABEL])].copy()
        for metric in metrics:
            work = merged[["subject_id", "bdi_band", metric]].dropna().copy()
            if work.empty:
                continue
            low = work.loc[work["bdi_band"] == LOW_BDI_LABEL, metric].to_numpy(dtype=float)
            high = work.loc[work["bdi_band"] == HIGH_BDI_LABEL, metric].to_numpy(dtype=float)
            if low.size < 3 or high.size < 3:
                continue
            t_stat, p_value = stats.ttest_ind(low, high, equal_var=False, nan_policy="omit")
            rows.append(
                {
                    "dataset": DATASET,
                    "centroid_family": family,
                    "analysis_type": analysis_type,
                    "metric": metric,
                    "left_group": LOW_BDI_LABEL,
                    "right_group": HIGH_BDI_LABEL,
                    "left_n": int(low.size),
                    "right_n": int(high.size),
                    "left_mean": float(low.mean()),
                    "right_mean": float(high.mean()),
                    "effect_estimate": float(high.mean() - low.mean()),
                    "effect_size": _cohens_d(low, high),
                    "t_stat": float(t_stat) if np.isfinite(t_stat) else np.nan,
                    "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
                }
            )
    baseline = pd.DataFrame(rows)
    if baseline.empty:
        return baseline
    baseline["q_value"] = baseline.groupby("centroid_family", dropna=False)["p_value"].transform(_bh_fdr)
    baseline["sig_tier"] = [
        _sig_tier(float(p) if pd.notna(p) else None, float(q) if pd.notna(q) else None)
        for p, q in zip(baseline["p_value"], baseline["q_value"])
    ]
    baseline["abs_effect"] = pd.to_numeric(baseline["effect_size"], errors="coerce").abs()
    return baseline.sort_values(
        ["centroid_family", "q_value", "p_value", "abs_effect", "metric"],
        ascending=[True, True, True, False, True],
        na_position="last",
    ).reset_index(drop=True)


def build_centroid_adjusted_summary(
    subject_metrics: pd.DataFrame,
    phenos: pd.DataFrame,
) -> pd.DataFrame:
    band_lookup = (
        phenos[["participant_id", "BDI", "bdi_band", "age", "female"]]
        .rename(columns={"participant_id": "subject_id"})
        .copy()
    )
    band_lookup = band_lookup[band_lookup["bdi_band"].isin([LOW_BDI_LABEL, HIGH_BDI_LABEL])].copy()
    band_lookup["group_high_bdi"] = band_lookup["bdi_band"].eq(HIGH_BDI_LABEL).astype(int)

    coords_3d = _subject_metric_wide(subject_metrics, analysis_type="global_mnps_3d", metrics=COORDS_3D)
    coords_9d = _subject_metric_wide(subject_metrics, analysis_type="global_mnps_9d", metrics=COORDS_9D)

    rows: list[dict[str, object]] = []
    for spec in TARGET_SPECS:
        metric_frame = _subject_metric_series(
            subject_metrics,
            analysis_type=spec.analysis_type,
            metric=spec.metric,
            source_group=spec.source_group,
            target_group=spec.target_group,
        ).rename(columns={"value": "target_value"})
        if metric_frame.empty:
            continue

        covariates = coords_3d if spec.centroid_family == "3d" else coords_9d
        covariate_names = COORDS_3D if spec.centroid_family == "3d" else COORDS_9D
        merged = (
            band_lookup.merge(metric_frame, on="subject_id", how="inner")
            .merge(covariates, on="subject_id", how="inner")
            .copy()
        )
        merged["target_value"] = pd.to_numeric(merged["target_value"], errors="coerce")
        merged = merged.dropna(subset=["target_value"] + covariate_names).copy()
        if len(merged) < len(covariate_names) + 8:
            continue

        low = merged.loc[merged["group_high_bdi"] == 0, "target_value"].to_numpy(dtype=float)
        high = merged.loc[merged["group_high_bdi"] == 1, "target_value"].to_numpy(dtype=float)
        unadj_t, unadj_p = stats.ttest_ind(low, high, equal_var=False, nan_policy="omit")

        x = _add_constant(merged[["group_high_bdi"] + covariate_names].to_numpy(dtype=float))
        robust = _ols_hc3_inference(merged["target_value"].to_numpy(dtype=float), x)
        group_idx = 1
        adjusted_beta = float(np.asarray(robust["beta"])[group_idx])
        adjusted_t = float(np.asarray(robust["t_values"])[group_idx])
        adjusted_p = float(np.asarray(robust["p_values"])[group_idx])
        adjusted_se = float(np.asarray(robust["se"])[group_idx])

        cov_only_x = _add_constant(merged[covariate_names].to_numpy(dtype=float))
        cov_only = _ols_fit(merged["target_value"].to_numpy(dtype=float), cov_only_x)
        residual = merged["target_value"].to_numpy(dtype=float) - np.asarray(cov_only["fitted"], dtype=float)
        group_mask = merged["group_high_bdi"].to_numpy(dtype=int)
        resid_low = np.asarray(residual[group_mask == 0], dtype=float)
        resid_high = np.asarray(residual[group_mask == 1], dtype=float)
        residual_d = _cohens_d(resid_low, resid_high)

        df_resid = float(robust["df_resid"])
        partial_r2 = float(adjusted_t * adjusted_t / (adjusted_t * adjusted_t + df_resid)) if np.isfinite(adjusted_t) else np.nan

        rows.append(
            {
                "dataset": DATASET,
                "block_key": spec.block_key,
                "block_title": spec.title,
                "analysis_type": spec.analysis_type,
                "metric": spec.metric,
                "source_group": spec.source_group,
                "target_group": spec.target_group,
                "centroid_family": spec.centroid_family,
                "covariates": json.dumps(covariate_names),
                "n_subjects": int(len(merged)),
                "left_group": LOW_BDI_LABEL,
                "right_group": HIGH_BDI_LABEL,
                "left_n": int((merged["group_high_bdi"] == 0).sum()),
                "right_n": int((merged["group_high_bdi"] == 1).sum()),
                "raw_left_mean": float(low.mean()),
                "raw_right_mean": float(high.mean()),
                "raw_effect_estimate": float(high.mean() - low.mean()),
                "raw_effect_size": _cohens_d(low, high),
                "raw_p_value": float(unadj_p) if np.isfinite(unadj_p) else np.nan,
                "adjusted_group_beta": adjusted_beta,
                "adjusted_group_se": adjusted_se,
                "adjusted_group_t": adjusted_t,
                "adjusted_p_value": adjusted_p,
                "residualized_effect_size": residual_d,
                "partial_r2": partial_r2,
                "model_r2": float(robust["r2"]),
                "model_r2_adj": float(robust["r2_adj"]),
            }
        )

    detail = pd.DataFrame(rows)
    if detail.empty:
        return detail
    detail["adjusted_q_value"] = _bh_fdr(detail["adjusted_p_value"])
    detail["sig_tier"] = [
        _sig_tier(float(p) if pd.notna(p) else None, float(q) if pd.notna(q) else None)
        for p, q in zip(detail["adjusted_p_value"], detail["adjusted_q_value"])
    ]
    detail["abs_adjusted_beta"] = pd.to_numeric(detail["adjusted_group_beta"], errors="coerce").abs()
    return detail.sort_values(
        ["adjusted_q_value", "adjusted_p_value", "abs_adjusted_beta", "block_key"],
        ascending=[True, True, False, True],
        na_position="last",
    ).reset_index(drop=True)


def _build_markdown(baseline: pd.DataFrame, adjusted: pd.DataFrame) -> str:
    lines = [
        "# Centroid-adjusted depression summary",
        "",
        f"- Dataset: `{DATASET}`",
        f"- Primary comparison: `{LOW_BDI_LABEL}` vs `{HIGH_BDI_LABEL}`",
        f"- Dynamic models are fit on subject-averaged values with centroid covariates from the matching coordinate family.",
        "",
        "## Baseline centroid shifts",
        "",
    ]
    if baseline.empty:
        lines.extend(["No centroid baseline summary was estimable.", ""])
    else:
        for family in ("3d", "9d"):
            sub = baseline[baseline["centroid_family"] == family].head(5).copy()
            if sub.empty:
                continue
            lines.extend([f"### {family.upper()}", ""])
            for _, row in sub.iterrows():
                lines.append(
                    f"- `{row['metric']}`: d={float(row['effect_size']):.3f}, "
                    f"delta={float(row['effect_estimate']):.3f}, p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
                )
            lines.append("")

    lines.extend(["## Centroid-adjusted dynamics", ""])
    if adjusted.empty:
        lines.extend(["No centroid-adjusted models were estimable.", ""])
        return "\n".join(lines)

    for _, row in adjusted.iterrows():
        extra = []
        if pd.notna(row.get("source_group")) or pd.notna(row.get("target_group")):
            extra.append(f"block={row.get('source_group')}->{row.get('target_group')}")
        suffix = f" ({', '.join(extra)})" if extra else ""
        lines.append(
            f"- `{row['block_title']}` / `{row['metric']}`{suffix}: "
            f"raw d={float(row['raw_effect_size']):.3f}, "
            f"adjusted beta={float(row['adjusted_group_beta']):.3f}, "
            f"residual d={float(row['residualized_effect_size']):.3f}, "
            f"p={float(row['adjusted_p_value']):.4g}, q={float(row['adjusted_q_value']):.4g}, "
            f"partial R2={float(row['partial_r2']):.3f}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    roots = _analysis_roots(args.analysis_root)
    results_root = args.results_root
    results_root.mkdir(parents=True, exist_ok=True)

    subject_metrics_path = _latest_parquet(roots, "subject_metrics")
    subject_metrics = pd.read_parquet(subject_metrics_path)
    phenos = load_participants()

    baseline = build_baseline_centroid_summary(subject_metrics, phenos)
    adjusted = build_centroid_adjusted_summary(subject_metrics, phenos)

    if not baseline.empty:
        baseline.to_csv(results_root / "centroid_baseline_summary.csv", index=False)
    if not adjusted.empty:
        adjusted.to_csv(results_root / "centroid_adjusted_dynamic_summary.csv", index=False)
    (results_root / "centroid_adjusted_summary.md").write_text(
        _build_markdown(baseline, adjusted),
        encoding="utf-8",
    )

    manifest = {
        "dataset": DATASET,
        "subject_metrics_path": str(subject_metrics_path),
        "participants_path": str(PARTICIPANTS_PATH),
        "results_root": str(results_root),
        "low_group": LOW_BDI_LABEL,
        "high_group": HIGH_BDI_LABEL,
        "target_specs": [
            {
                "block_key": spec.block_key,
                "title": spec.title,
                "analysis_type": spec.analysis_type,
                "metric": spec.metric,
                "centroid_family": spec.centroid_family,
                "source_group": spec.source_group,
                "target_group": spec.target_group,
            }
            for spec in TARGET_SPECS
        ],
    }
    (results_root / "centroid_adjusted_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote centroid baseline summary to {results_root / 'centroid_baseline_summary.csv'}")
    print(f"Wrote centroid-adjusted dynamic summary to {results_root / 'centroid_adjusted_dynamic_summary.csv'}")


if __name__ == "__main__":
    main()
