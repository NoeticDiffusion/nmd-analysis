from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = REPO_ROOT / "data" / "analysis" / "psychosis_cohort_anchor_20260520"
META_ROOT = REPO_ROOT / "articles" / "psychosis_first_time_episode" / "metadata"
RESULTS_ROOT = REPO_ROOT / "articles" / "psychosis_first_time_episode" / "results"


def _load_phenotypes(dataset: str) -> pd.DataFrame:
    dataset_dir = (
        META_ROOT / "ds003944_psychosis_eeg_phenotyped"
        if dataset == "ds003944"
        else META_ROOT / "ds003947_psychosis_eeg"
    )
    participants = pd.read_csv(dataset_dir / "participants.tsv", sep="\t")
    saps = pd.read_csv(dataset_dir / "phenotype" / "saps.tsv", sep="\t")
    bprs = pd.read_csv(dataset_dir / "phenotype" / "bprs.tsv", sep="\t")

    participants["age"] = pd.to_numeric(participants["age"], errors="coerce")
    participants["female"] = participants["gender"].astype(str).eq("F")
    saps["SAPS_Q7"] = pd.to_numeric(saps["SAPS_Q7"], errors="coerce")
    bprs["BPRST19"] = pd.to_numeric(bprs["BPRST19"], errors="coerce")

    phenos = participants[["participant_id", "type", "age", "gender", "female"]].merge(
        saps[["participant_id", "SAPS_Q7"]],
        on="participant_id",
        how="left",
    )
    phenos = phenos.merge(
        bprs[["participant_id", "BPRST19"]],
        on="participant_id",
        how="left",
    )

    phenos["saps_q7_group"] = pd.Series([None] * len(phenos), dtype=object)
    phenos.loc[phenos["SAPS_Q7"] <= 1, "saps_q7_group"] = "Low hallucinations"
    phenos.loc[phenos["SAPS_Q7"] >= 3, "saps_q7_group"] = "High hallucinations"

    fep_bprs = phenos.loc[phenos["type"].astype(str) == "Psychosis", "BPRST19"].dropna()
    bprs_median = float(fep_bprs.median()) if not fep_bprs.empty else float("nan")
    phenos["bprst19_group"] = pd.Series([None] * len(phenos), dtype=object)
    phenos.loc[phenos["BPRST19"] <= bprs_median, "bprst19_group"] = "Lower total severity"
    phenos.loc[phenos["BPRST19"] > bprs_median, "bprst19_group"] = "Higher total severity"

    return phenos


def _write_demography_summary(dataset: str, phenos: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for group_label, mask in (
        ("Healthy", phenos["type"].astype(str) == "Control"),
        ("FEP", phenos["type"].astype(str) == "Psychosis"),
    ):
        sub = phenos.loc[mask].copy()
        rows.append(
            {
                "dataset": dataset,
                "group": group_label,
                "n": int(len(sub)),
                "age_mean": round(float(sub["age"].mean()), 3),
                "age_sd": round(float(sub["age"].std()), 3),
                "female_n": int(sub["female"].sum()),
                "female_pct": round(float(sub["female"].mean() * 100.0), 1),
            }
        )
    return rows


def _subject_metrics_path(dataset: str) -> Path:
    matches = sorted(ANALYSIS_ROOT.glob(f"{dataset}_subject_metrics_*.parquet"))
    if not matches:
        raise FileNotFoundError(f"No subject_metrics parquet for {dataset} under {ANALYSIS_ROOT}")
    return matches[-1]


def _sorted_results(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["abs_effect"] = out["effect_size"].abs()
    out["sig_rank"] = np.where(out["q_value"].fillna(np.inf) <= 0.05, 0, 1)
    return out.sort_values(
        by=["sig_rank", "q_value", "p_value", "abs_effect", "metric"],
        ascending=[True, True, True, False, True],
        na_position="last",
    ).reset_index(drop=True)


def _pick_metric(frame: pd.DataFrame, preferred: list[str] | None = None) -> pd.Series:
    ordered = _sorted_results(frame)
    for metric in preferred or []:
        match = ordered[ordered["metric"] == metric]
        if not match.empty:
            return match.iloc[0]
    return ordered.iloc[0]


def _cohens_d(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 2 or right.size < 2:
        return float("nan")
    left_var = left.var(ddof=1)
    right_var = right.var(ddof=1)
    pooled_var = ((left.size - 1) * left_var + (right.size - 1) * right_var) / (left.size + right.size - 2)
    if not np.isfinite(pooled_var) or pooled_var <= 0:
        return float("nan")
    return float((right.mean() - left.mean()) / np.sqrt(pooled_var))


def _bh_fdr(values: pd.Series) -> pd.Series:
    arr = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    valid = np.isfinite(arr)
    if not valid.any():
        return pd.Series(out, index=values.index)
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
    return pd.Series(out, index=values.index)


def _sig_tier(row: pd.Series) -> str:
    if pd.notna(row.get("q_value")) and float(row["q_value"]) <= 0.05:
        return "q<=0.05"
    if pd.notna(row.get("p_value")) and float(row["p_value"]) < 0.05:
        return "p<0.05"
    if pd.notna(row.get("p_value")) and float(row["p_value"]) < 0.1:
        return "p<0.1"
    return "ns"


def _run_split_tests(dataset: str, split_name: str, frame: pd.DataFrame, split_column: str) -> pd.DataFrame:
    contrast_name = {
        "saps_q7_group": "High_vs_Low_SAPS_Q7",
        "bprst19_group": "High_vs_Low_BPRST19",
    }[split_column]
    left_label, right_label = {
        "saps_q7_group": ("Low hallucinations", "High hallucinations"),
        "bprst19_group": ("Lower total severity", "Higher total severity"),
    }[split_column]

    rows: list[dict[str, object]] = []
    work = frame[frame["group"] == "FEP"].copy()
    work = work[work[split_column].isin([left_label, right_label])].copy()

    for (analysis_type, metric), sub in work.groupby(["analysis_type", "metric"], dropna=False):
        left = pd.to_numeric(
            sub.loc[sub[split_column] == left_label, "value"],
            errors="coerce",
        ).dropna()
        right = pd.to_numeric(
            sub.loc[sub[split_column] == right_label, "value"],
            errors="coerce",
        ).dropna()
        if len(left) < 3 or len(right) < 3:
            continue
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Precision loss occurred in moment calculation due to catastrophic cancellation.*",
                category=RuntimeWarning,
            )
            t_stat, p_value = stats.ttest_ind(
                left.to_numpy(),
                right.to_numpy(),
                equal_var=False,
                nan_policy="omit",
            )
        rows.append(
            {
                "dataset": dataset,
                "split_name": split_name,
                "contrast_name": contrast_name,
                "analysis_type": analysis_type,
                "metric": metric,
                "left_group": left_label,
                "right_group": right_label,
                "left_n": int(len(left)),
                "right_n": int(len(right)),
                "left_mean": float(left.mean()),
                "right_mean": float(right.mean()),
                "effect_estimate": float(right.mean() - left.mean()),
                "effect_size": _cohens_d(left.to_numpy(), right.to_numpy()),
                "t_stat": float(t_stat) if np.isfinite(t_stat) else np.nan,
                "p_value": float(p_value) if np.isfinite(p_value) else np.nan,
            }
        )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["q_value"] = result.groupby("analysis_type", dropna=False)["p_value"].transform(_bh_fdr)
    result["sig_tier"] = result.apply(_sig_tier, axis=1)
    return result


def _summarize_split_results(dataset: str, split_name: str, frame: pd.DataFrame, phenos: pd.DataFrame) -> list[dict[str, object]]:
    block_specs = [
        ("mnps_3d", "global_mnps_3d", ["m_mean", "m_median", "m_std"]),
        ("mnps_9d", "global_mnps_9d", ["m_e_mean", "m_e_median", "m_o_mean", "m_o_median", "m_a_mean", "m_a_median"]),
        ("trajectory", "trajectory_dynamics", ["m_delta_mean_median", "d_delta_mean_median", "e_delta_mean_median"]),
        ("mnj_9d", "global_mnps_jacobian_9d", ["mdr_mean", "mdr_median", "aci_mean", "aci_median"]),
        ("block_mnj", "global_mnps_jacobian_9d_block_jacobian", ["block_trace_mean", "block_frobenius_mean"]),
    ]

    if split_name == "saps_q7":
        counts = phenos["saps_q7_group"].value_counts(dropna=False).to_dict()
    else:
        counts = phenos["bprst19_group"].value_counts(dropna=False).to_dict()

    rows: list[dict[str, object]] = []
    for block_key, analysis_type, preferred in block_specs:
        sub = frame[frame["analysis_type"] == analysis_type].copy()
        if sub.empty:
            continue
        pick = _pick_metric(sub, None)
        rows.append(
            {
                "dataset": dataset,
                "split_name": split_name,
                "block_key": block_key,
                "analysis_type": analysis_type,
                "metric": pick["metric"],
                "effect_size": float(pick["effect_size"]),
                "p_value": float(pick["p_value"]),
                "q_value": float(pick["q_value"]) if pd.notna(pick["q_value"]) else np.nan,
                "left_n": int(pick["left_n"]) if pd.notna(pick["left_n"]) else None,
                "right_n": int(pick["right_n"]) if pd.notna(pick["right_n"]) else None,
                "left_mean": float(pick["left_mean"]) if pd.notna(pick["left_mean"]) else np.nan,
                "right_mean": float(pick["right_mean"]) if pd.notna(pick["right_mean"]) else np.nan,
                "sig_tier": _sig_tier(pick),
                "group_counts": json.dumps({str(k): int(v) for k, v in counts.items() if k is not None}, sort_keys=True),
            }
        )
    return rows


def main() -> None:
    demography_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    detail_frames: list[pd.DataFrame] = []
    manifest: dict[str, object] = {"runs": []}

    for dataset in ("ds003944", "ds003947"):
        phenos = _load_phenotypes(dataset)
        demography_rows.extend(_write_demography_summary(dataset, phenos))
        subject_metrics = pd.read_parquet(_subject_metrics_path(dataset))
        subject_metrics = subject_metrics.merge(
            phenos[
                [
                    "participant_id",
                    "age",
                    "gender",
                    "female",
                    "SAPS_Q7",
                    "BPRST19",
                    "saps_q7_group",
                    "bprst19_group",
                ]
            ],
            left_on="subject_id",
            right_on="participant_id",
            how="left",
        ).drop(columns=["participant_id"], errors="ignore")

        saps_results = _run_split_tests(dataset, "saps_q7", subject_metrics, "saps_q7_group")
        bprs_results = _run_split_tests(dataset, "bprst19", subject_metrics, "bprst19_group")
        if not saps_results.empty:
            detail_frames.append(saps_results)
            summary_rows.extend(_summarize_split_results(dataset, "saps_q7", saps_results, phenos))
        if not bprs_results.empty:
            detail_frames.append(bprs_results)
            summary_rows.extend(_summarize_split_results(dataset, "bprst19", bprs_results, phenos))

        manifest["runs"].append(
            {
                "dataset": dataset,
                "subject_metrics_path": str(_subject_metrics_path(dataset)),
                "saps_q7_groups": {
                    str(k): int(v)
                    for k, v in phenos["saps_q7_group"].value_counts(dropna=False).to_dict().items()
                    if k is not None
                },
                "bprst19_groups": {
                    str(k): int(v)
                    for k, v in phenos["bprst19_group"].value_counts(dropna=False).to_dict().items()
                    if k is not None
                },
            }
        )

    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(demography_rows).to_csv(RESULTS_ROOT / "demography_summary.csv", index=False)
    pd.DataFrame(summary_rows).to_csv(RESULTS_ROOT / "clinical_phenotype_summary.csv", index=False)
    if detail_frames:
        pd.concat(detail_frames, ignore_index=True).to_csv(
            RESULTS_ROOT / "clinical_phenotype_detail.csv",
            index=False,
        )
    (RESULTS_ROOT / "clinical_phenotype_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
