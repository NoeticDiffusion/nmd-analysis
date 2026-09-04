from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ARTICLE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTICLE_DIR.parents[3]
SIBLING_ARTICLE_DIR = ARTICLE_DIR.parent / "alzheimer_ftd_photonic"
SIBLING_SRC = SIBLING_ARTICLE_DIR / "src"
if str(SIBLING_SRC) not in sys.path:
    sys.path.insert(0, str(SIBLING_SRC))

from build_photonic_paper_exports import _bh_fdr, _cohens_d  # noqa: E402
from explore_esb_ds004504_baseline import (  # noqa: E402
    DEFAULT_PHOTIC_RAW_ROOT,
    DEFAULT_REST_RAW_ROOT,
    SPECS,
    STAGE_ORDER,
    add_ds004504_scores,
    build_photic_recovery_metrics,
    build_rest_baseline_metrics,
)
from explore_esb_proxy import (  # noqa: E402
    _safe_scale,
    _stage_rank,
    build_stage_response,
    build_window_inventory,
    load_metric_frame,
)

DEFAULT_PHOTIC_RESULTS_ROOT = SIBLING_ARTICLE_DIR / "results"
DEFAULT_REFERENCE_EFFECTS_PATH = (
    SIBLING_ARTICLE_DIR / "results" / "rest_vs_photic_reference" / "rest_vs_photic_mdr_ad_vs_healthy_effects.csv"
)
PRIMARY_SPEC = "posterior_capacity_global_guidance"
PRIMARY_STAGE = "photo_15hz"
N_PERMUTATIONS = 2000
RNG_SEED = 20260529


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build article-facing ESB, PRL, and QC outputs.")
    parser.add_argument("--photic-results-root", type=Path, default=DEFAULT_PHOTIC_RESULTS_ROOT)
    parser.add_argument("--photic-raw-root", type=Path, default=DEFAULT_PHOTIC_RAW_ROOT)
    parser.add_argument("--rest-raw-root", type=Path, default=DEFAULT_REST_RAW_ROOT)
    parser.add_argument("--reference-effects-path", type=Path, default=DEFAULT_REFERENCE_EFFECTS_PATH)
    parser.add_argument("--output-dir", type=Path, default=ARTICLE_DIR / "results")
    parser.add_argument("--n-permutations", type=int, default=N_PERMUTATIONS)
    parser.add_argument("--rng-seed", type=int, default=RNG_SEED)
    return parser.parse_args()


def _score_contrast(
    frame: pd.DataFrame,
    *,
    value_col: str,
    left_group: str,
    right_group: str,
) -> dict[str, float]:
    left = pd.to_numeric(frame.loc[frame["group_label"] == left_group, value_col], errors="coerce").dropna().to_numpy(dtype=float)
    right = pd.to_numeric(frame.loc[frame["group_label"] == right_group, value_col], errors="coerce").dropna().to_numpy(dtype=float)
    p_value = float("nan")
    if left.size and right.size:
        p_value = float(stats.mannwhitneyu(left, right, alternative="two-sided").pvalue)
    return {
        "left_n": int(left.size),
        "right_n": int(right.size),
        "left_mean": float(np.mean(left)) if left.size else float("nan"),
        "right_mean": float(np.mean(right)) if right.size else float("nan"),
        "effect_size": _cohens_d(left, right),
        "p_value": p_value,
    }


def build_esb_scores(args: argparse.Namespace) -> pd.DataFrame:
    metric_frame = load_metric_frame(args.photic_results_root)
    rest_baseline = build_rest_baseline_metrics(args.rest_raw_root)
    recovery = build_photic_recovery_metrics(args.photic_raw_root)

    all_scored: list[pd.DataFrame] = []
    for spec in SPECS:
        stage_response = build_stage_response(metric_frame, spec)
        sub_rest = rest_baseline[rest_baseline["spec_name"] == spec.name].copy()
        sub_recovery = recovery[recovery["spec_name"] == spec.name].copy()
        scored = add_ds004504_scores(stage_response, sub_rest, sub_recovery)
        all_scored.append(scored)

    scored_all = pd.concat(all_scored, ignore_index=True)
    scored_all["stage_rank"] = scored_all["stage_label"].map(_stage_rank)
    return scored_all


def build_esb_group_summary(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    value_cols = ["esb2_ds004504", "esb3_ds004504", "h_rest_raw"]
    group_cols = ["spec_name", "spec_label", "stage_label", "stage_rank", "group_label"]
    for keys, group in scored.groupby(group_cols, dropna=False):
        row = dict(zip(group_cols, keys))
        row["n_subjects"] = int(group["subject_id"].nunique())
        for value_col in value_cols:
            values = pd.to_numeric(group[value_col], errors="coerce").dropna()
            row[f"{value_col}_median"] = float(values.median()) if not values.empty else float("nan")
            row[f"{value_col}_mean"] = float(values.mean()) if not values.empty else float("nan")
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["spec_name", "stage_rank", "group_label"]).reset_index(drop=True)


def build_esb_contrasts(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    score_cols = ["esb2_ds004504", "esb3_ds004504", "h_rest_raw"]
    contrasts = [("AD_vs_Healthy", "AD", "Healthy"), ("FTD_vs_Healthy", "FTD", "Healthy"), ("AD_vs_FTD", "AD", "FTD")]
    group_cols = ["spec_name", "spec_label", "stage_label", "stage_rank"]
    for keys, group in scored.groupby(group_cols, dropna=False):
        base = dict(zip(group_cols, keys))
        for score_col in score_cols:
            for contrast_name, left_group, right_group in contrasts:
                row = dict(base)
                row["score_name"] = score_col
                row["contrast_name"] = contrast_name
                row["left_group"] = left_group
                row["right_group"] = right_group
                row.update(_score_contrast(group, value_col=score_col, left_group=left_group, right_group=right_group))
                rows.append(row)
    out = pd.DataFrame(rows)
    out["q_value"] = np.nan
    for _, group in out.groupby(["score_name", "contrast_name", "stage_label"], dropna=False):
        out.loc[group.index, "q_value"] = _bh_fdr(group["p_value"]).to_numpy(dtype=float)
    out["abs_effect"] = pd.to_numeric(out["effect_size"], errors="coerce").abs()
    return out.sort_values(["score_name", "contrast_name", "stage_rank", "q_value", "abs_effect"], na_position="last").reset_index(drop=True)


def build_axis_contrasts(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    value_cols = [
        ("delta_capacity_rest", "Delta capacity vs ds004504"),
        ("delta_guidance_rest", "Delta guidance vs ds004504"),
    ]
    contrasts = [("AD_vs_Healthy", "AD", "Healthy"), ("FTD_vs_Healthy", "FTD", "Healthy"), ("AD_vs_FTD", "AD", "FTD")]
    group_cols = ["spec_name", "spec_label", "stage_label", "stage_rank"]
    for keys, group in scored.groupby(group_cols, dropna=False):
        base = dict(zip(group_cols, keys))
        for value_col, label in value_cols:
            for contrast_name, left_group, right_group in contrasts:
                row = dict(base)
                row["axis_name"] = value_col
                row["axis_label"] = label
                row["contrast_name"] = contrast_name
                row["left_group"] = left_group
                row["right_group"] = right_group
                row.update(_score_contrast(group, value_col=value_col, left_group=left_group, right_group=right_group))
                rows.append(row)
    out = pd.DataFrame(rows)
    out["q_value"] = np.nan
    for _, group in out.groupby(["axis_name", "contrast_name", "stage_label"], dropna=False):
        out.loc[group.index, "q_value"] = _bh_fdr(group["p_value"]).to_numpy(dtype=float)
    out["abs_effect"] = pd.to_numeric(out["effect_size"], errors="coerce").abs()
    return out.sort_values(["axis_name", "contrast_name", "stage_rank", "q_value", "abs_effect"], na_position="last").reset_index(drop=True)


def build_cross_fitted_primary_scores(scored: pd.DataFrame) -> pd.DataFrame:
    primary = scored[(scored["spec_name"] == PRIMARY_SPEC) & (scored["stage_label"].isin(STAGE_ORDER))].copy()
    rows: list[dict[str, object]] = []
    for stage_label, stage_frame in primary.groupby("stage_label", dropna=False):
        healthy_all = stage_frame[stage_frame["group_label"] == "Healthy"].copy()
        if len(healthy_all) < 3:
            continue
        full_cap_med = float(np.nanmedian(healthy_all["delta_capacity_rest"]))
        full_gui_med = float(np.nanmedian(healthy_all["delta_guidance_rest"]))
        full_cap_scale = _safe_scale(healthy_all["delta_capacity_rest"])
        full_gui_scale = _safe_scale(healthy_all["delta_guidance_rest"])
        for _, row in stage_frame.iterrows():
            if str(row["group_label"]) == "Healthy":
                healthy = healthy_all[healthy_all["subject_id"] != row["subject_id"]].copy()
                if len(healthy) < 3:
                    continue
                cap_med = float(np.nanmedian(healthy["delta_capacity_rest"]))
                gui_med = float(np.nanmedian(healthy["delta_guidance_rest"]))
                cap_scale = _safe_scale(healthy["delta_capacity_rest"])
                gui_scale = _safe_scale(healthy["delta_guidance_rest"])
                template_mode = "leave_one_out_healthy"
            else:
                cap_med = full_cap_med
                gui_med = full_gui_med
                cap_scale = full_cap_scale
                gui_scale = full_gui_scale
                template_mode = "full_healthy_template"
            value = np.sqrt(
                ((float(row["delta_capacity_rest"]) - cap_med) / cap_scale) ** 2
                + ((float(row["delta_guidance_rest"]) - gui_med) / gui_scale) ** 2
            ) / np.sqrt(2.0)
            out_row = row.to_dict()
            out_row["esb2_crossfit_hc"] = float(value)
            out_row["template_mode"] = template_mode
            rows.append(out_row)
    return pd.DataFrame(rows).sort_values(["stage_rank", "group_label", "subject_id"]).reset_index(drop=True)


def build_cross_fitted_contrasts(crossfit_scores: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    contrasts = [("AD_vs_Healthy", "AD", "Healthy"), ("FTD_vs_Healthy", "FTD", "Healthy"), ("AD_vs_FTD", "AD", "FTD")]
    for keys, group in crossfit_scores.groupby(["stage_label", "stage_rank"], dropna=False):
        stage_label, stage_rank = keys
        for contrast_name, left_group, right_group in contrasts:
            row = {
                "spec_name": PRIMARY_SPEC,
                "score_name": "esb2_crossfit_hc",
                "contrast_name": contrast_name,
                "left_group": left_group,
                "right_group": right_group,
                "stage_label": stage_label,
                "stage_rank": stage_rank,
            }
            row.update(_score_contrast(group, value_col="esb2_crossfit_hc", left_group=left_group, right_group=right_group))
            rows.append(row)
    out = pd.DataFrame(rows)
    out["q_value"] = np.nan
    for _, group in out.groupby(["score_name", "contrast_name", "stage_label"], dropna=False):
        out.loc[group.index, "q_value"] = _bh_fdr(group["p_value"]).to_numpy(dtype=float)
    out["abs_effect"] = pd.to_numeric(out["effect_size"], errors="coerce").abs()
    return out.sort_values(["contrast_name", "stage_rank", "q_value", "abs_effect"], na_position="last").reset_index(drop=True)


def build_prl_scores(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for spec_name, spec_frame in scored.groupby("spec_name", dropna=False):
        healthy = spec_frame[spec_frame["group_label"] == "Healthy"].copy()
        template = (
            healthy.groupby("stage_label", dropna=False)["esb2_ds004504"]
            .median()
            .reindex(STAGE_ORDER)
        )
        template_values = template.to_numpy(dtype=float)
        for subject_id, subject_frame in spec_frame.groupby("subject_id", dropna=False):
            profile = (
                subject_frame.groupby("stage_label", dropna=False)["esb2_ds004504"]
                .mean()
                .reindex(STAGE_ORDER)
            )
            subject_values = profile.to_numpy(dtype=float)
            valid = np.isfinite(template_values) & np.isfinite(subject_values)
            prl_score = float("nan")
            pearson_r = float("nan")
            if int(valid.sum()) >= 3:
                tpl = template_values[valid]
                subj = subject_values[valid]
                if np.nanstd(tpl) > 0 and np.nanstd(subj) > 0:
                    pearson_r = float(np.corrcoef(tpl, subj)[0, 1])
                    prl_score = float(1.0 - pearson_r)
            first = subject_frame.iloc[0]
            rows.append(
                {
                    "subject_id": subject_id,
                    "spec_name": spec_name,
                    "spec_label": first["spec_label"],
                    "group_label": first["group_label"],
                    "group": first["group"],
                    "mmse": first.get("mmse"),
                    "n_frequencies_used": int(valid.sum()),
                    "prl_pearson_r": pearson_r,
                    "prl_score": prl_score,
                    "template_photo_5hz": template.get("photo_5hz"),
                    "template_photo_10hz": template.get("photo_10hz"),
                    "template_photo_15hz": template.get("photo_15hz"),
                    "template_photo_20hz": template.get("photo_20hz"),
                    "subject_photo_5hz": profile.get("photo_5hz"),
                    "subject_photo_10hz": profile.get("photo_10hz"),
                    "subject_photo_15hz": profile.get("photo_15hz"),
                    "subject_photo_20hz": profile.get("photo_20hz"),
                }
            )
    return pd.DataFrame(rows)


def build_prl_group_summary(prl_scores: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for keys, group in prl_scores.groupby(["spec_name", "spec_label", "group_label"], dropna=False):
        spec_name, spec_label, group_label = keys
        values = pd.to_numeric(group["prl_score"], errors="coerce").dropna()
        rows.append(
            {
                "spec_name": spec_name,
                "spec_label": spec_label,
                "group_label": group_label,
                "n_subjects": int(group["subject_id"].nunique()),
                "prl_score_median": float(values.median()) if not values.empty else float("nan"),
                "prl_score_mean": float(values.mean()) if not values.empty else float("nan"),
            }
        )
    return pd.DataFrame(rows).sort_values(["spec_name", "group_label"]).reset_index(drop=True)


def build_prl_contrasts(prl_scores: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    contrasts = [("AD_vs_Healthy", "AD", "Healthy"), ("FTD_vs_Healthy", "FTD", "Healthy"), ("AD_vs_FTD", "AD", "FTD")]
    for keys, group in prl_scores.groupby(["spec_name", "spec_label"], dropna=False):
        spec_name, spec_label = keys
        for contrast_name, left_group, right_group in contrasts:
            row = {
                "spec_name": spec_name,
                "spec_label": spec_label,
                "score_name": "prl_score",
                "contrast_name": contrast_name,
                "left_group": left_group,
                "right_group": right_group,
                "stage_label": "profile_all",
                "stage_rank": 999,
            }
            row.update(_score_contrast(group, value_col="prl_score", left_group=left_group, right_group=right_group))
            rows.append(row)
    out = pd.DataFrame(rows)
    out["q_value"] = np.nan
    for _, group in out.groupby(["score_name", "contrast_name"], dropna=False):
        out.loc[group.index, "q_value"] = _bh_fdr(group["p_value"]).to_numpy(dtype=float)
    out["abs_effect"] = pd.to_numeric(out["effect_size"], errors="coerce").abs()
    return out.sort_values(["contrast_name", "q_value", "abs_effect"], na_position="last").reset_index(drop=True)


def build_stage_coverage(scored: pd.DataFrame, inventory: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        scored.groupby(["spec_name", "spec_label", "stage_label", "stage_rank", "group_label"], dropna=False)["subject_id"]
        .nunique()
        .reset_index(name="n_subjects")
    )
    coverage = inventory[["subject_id", "post_windows_n", "post_eye_windows_n"]].copy()
    merged = scored[["subject_id", "spec_name", "spec_label", "stage_label", "stage_rank", "group_label"]].drop_duplicates().merge(
        coverage,
        on="subject_id",
        how="left",
    )
    summary = (
        merged.groupby(["spec_name", "spec_label", "stage_label", "stage_rank", "group_label"], dropna=False)
        .agg(
            n_subjects=("subject_id", "nunique"),
            n_with_post4=("post_windows_n", lambda s: int((pd.to_numeric(s, errors="coerce") >= 4).sum())),
            n_with_eye2=("post_eye_windows_n", lambda s: int((pd.to_numeric(s, errors="coerce") >= 2).sum())),
        )
        .reset_index()
    )
    return summary.sort_values(["spec_name", "stage_rank", "group_label"]).reset_index(drop=True)


def build_dataset_comparability(scored: pd.DataFrame) -> pd.DataFrame:
    primary = scored[scored["spec_name"] == PRIMARY_SPEC].copy()
    matched = primary[
        pd.to_numeric(primary["rest_capacity"], errors="coerce").notna()
        & pd.to_numeric(primary["rest_guidance"], errors="coerce").notna()
    ].copy()
    rows: list[dict[str, object]] = []
    total_group_counts = matched.groupby("group_label", dropna=False)["subject_id"].nunique().to_dict()
    stage_group_counts = (
        primary[primary["stage_label"] == PRIMARY_STAGE]
        .groupby("group_label", dropna=False)["subject_id"]
        .nunique()
        .to_dict()
    )
    rows.append(
        {
            "primary_spec": PRIMARY_SPEC,
            "primary_stage": PRIMARY_STAGE,
            "photic_subjects_total": int(primary["subject_id"].nunique()),
            "rest_matched_subjects_total": int(matched["subject_id"].nunique()),
            "healthy_total": int(total_group_counts.get("Healthy", 0)),
            "ad_total": int(total_group_counts.get("AD", 0)),
            "ftd_total": int(total_group_counts.get("FTD", 0)),
            "healthy_primary_stage_n": int(stage_group_counts.get("Healthy", 0)),
            "ad_primary_stage_n": int(stage_group_counts.get("AD", 0)),
            "ftd_primary_stage_n": int(stage_group_counts.get("FTD", 0)),
            "matching_note": (
                "Subject-level ds004504 baselines were available for all 88 photic subjects; "
                "comparisons remain bounded because ds004504 is a resting, eyes-closed dataset "
                "whereas the ds006036 photic surface is eyes-open and stimulus-evoked."
            ),
        }
    )
    return pd.DataFrame(rows)


def build_spec_sensitivity_summary(esb_contrasts: pd.DataFrame, metric_frame: pd.DataFrame) -> pd.DataFrame:
    available_specs = set(esb_contrasts["spec_name"].dropna().astype(str).unique().tolist())
    stage_metrics = set(
        metric_frame[["analysis_type", "network", "metric"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    rows: list[dict[str, object]] = []
    for spec in SPECS:
        spec_available = spec.name in available_specs
        availability_note = ""
        if not spec_available:
            needs = (spec.capacity_analysis_type, spec.capacity_network, spec.capacity_metric)
            if needs not in stage_metrics:
                availability_note = "Capacity component is not present as a stage-wise exported metric on the frozen article surface."
            else:
                availability_note = "Specification did not materialize as a finite contrast surface."
        for contrast_name in ("AD_vs_Healthy", "FTD_vs_Healthy"):
            row: dict[str, object] = {
                "spec_name": spec.name,
                "spec_label": spec.label,
                "contrast_name": contrast_name,
                "stage_label": PRIMARY_STAGE,
                "is_primary_spec": bool(spec.name == PRIMARY_SPEC),
                "available_in_surface": bool(spec_available),
                "availability_note": availability_note,
                "left_n": float("nan"),
                "right_n": float("nan"),
                "effect_size": float("nan"),
                "p_value": float("nan"),
                "q_value": float("nan"),
            }
            if spec_available:
                sub = esb_contrasts[
                    (esb_contrasts["score_name"] == "esb2_ds004504")
                    & (esb_contrasts["spec_name"] == spec.name)
                    & (esb_contrasts["contrast_name"] == contrast_name)
                    & (esb_contrasts["stage_label"] == PRIMARY_STAGE)
                ].copy()
                if not sub.empty:
                    top = sub.sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]
                    row.update(
                        {
                            "left_n": int(top["left_n"]),
                            "right_n": int(top["right_n"]),
                            "effect_size": float(top["effect_size"]),
                            "p_value": float(top["p_value"]),
                            "q_value": float(top["q_value"]),
                        }
                    )
            rows.append(row)
    return pd.DataFrame(rows)


def build_negative_results_summary(esb_contrasts: pd.DataFrame, prl_contrasts: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    esb2 = esb_contrasts[esb_contrasts["score_name"] == "esb2_ds004504"].copy()
    prl = prl_contrasts.copy()
    rows.append(
        {
            "result_family": "ESB2",
            "contrast_name": "AD_vs_FTD",
            "corrected_rows_q_lt_0_05": int(((esb2["contrast_name"] == "AD_vs_FTD") & (pd.to_numeric(esb2["q_value"], errors="coerce") < 0.05)).sum()),
            "best_stage_or_scope": (
                esb2[esb2["contrast_name"] == "AD_vs_FTD"].sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]["stage_label"]
                if not esb2[esb2["contrast_name"] == "AD_vs_FTD"].empty
                else ""
            ),
            "best_effect_size": (
                float(esb2[esb2["contrast_name"] == "AD_vs_FTD"].sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]["effect_size"])
                if not esb2[esb2["contrast_name"] == "AD_vs_FTD"].empty
                else float("nan")
            ),
            "best_q_value": (
                float(esb2[esb2["contrast_name"] == "AD_vs_FTD"].sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]["q_value"])
                if not esb2[esb2["contrast_name"] == "AD_vs_FTD"].empty
                else float("nan")
            ),
            "note": "No corrected disease-vs-disease ESB-2 row was retained on the article surface.",
        }
    )
    for contrast_name in ("AD_vs_Healthy", "FTD_vs_Healthy", "AD_vs_FTD"):
        sub = prl[prl["contrast_name"] == contrast_name].copy()
        rows.append(
            {
                "result_family": "PRL",
                "contrast_name": contrast_name,
                "corrected_rows_q_lt_0_05": int((pd.to_numeric(sub["q_value"], errors="coerce") < 0.05).sum()),
                "best_stage_or_scope": "profile_all",
                "best_effect_size": float(sub.sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]["effect_size"]) if not sub.empty else float("nan"),
                "best_q_value": float(sub.sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]["q_value"]) if not sub.empty else float("nan"),
                "note": "The first profile-based PRL implementation did not yield a corrected article-level group row.",
            }
        )
    return pd.DataFrame(rows)


def build_frequency_peak_audit(esb_contrasts: pd.DataFrame) -> pd.DataFrame:
    primary = esb_contrasts[
        (esb_contrasts["score_name"] == "esb2_ds004504")
        & (esb_contrasts["spec_name"] == PRIMARY_SPEC)
        & (esb_contrasts["contrast_name"].isin(["AD_vs_Healthy", "FTD_vs_Healthy"]))
    ].copy()
    primary["frequency_q_value"] = np.nan
    for _, group in primary.groupby("contrast_name", dropna=False):
        primary.loc[group.index, "frequency_q_value"] = _bh_fdr(group["p_value"]).to_numpy(dtype=float)
    primary["survives_frequency_q_lt_0_05"] = pd.to_numeric(primary["frequency_q_value"], errors="coerce") < 0.05
    return primary.sort_values(["contrast_name", "stage_rank"]).reset_index(drop=True)


def build_reproducibility_commands() -> str:
    lines = [
        "# Reproducibility commands",
        "",
        "Regenerate local article outputs:",
        "",
        "```powershell",
        "python articles/CLINICAL/alzheimer_ftd_photonic_esb/src/build_esb_article_outputs.py",
        "```",
        "",
        "Regenerate the conventional comparator panel:",
        "",
        "```powershell",
        "python articles/CLINICAL/alzheimer_ftd_photonic_esb/src/build_esb_comparator_panel.py",
        "```",
        "",
        "Regenerate article figures:",
        "",
        "```powershell",
        "python articles/CLINICAL/alzheimer_ftd_photonic_esb/src/build_esb_figures.py",
        "```",
        "",
        "Run the full local pipeline:",
        "",
        "```powershell",
        "python articles/CLINICAL/alzheimer_ftd_photonic_esb/src/run_esb_followup_pipeline.py",
        "```",
        "",
        "Compile the manuscript:",
        "",
        "```powershell",
        "typst compile \"articles/CLINICAL/alzheimer_ftd_photonic_esb/Evoked Structural Brittleness Under Photic Stimulation in Alzheimer Disease and Frontotemporal Dementia.typ\"",
        "```",
        "",
    ]
    return "\n".join(lines)


def build_leave_one_out_qc(scored: pd.DataFrame, prl_scores: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    primary = scored[(scored["spec_name"] == PRIMARY_SPEC)].copy()
    primary = primary[primary["stage_label"].isin(STAGE_ORDER)].copy()
    healthy_ids = sorted(primary.loc[primary["group_label"] == "Healthy", "subject_id"].dropna().astype(str).unique().tolist())
    loo_rows: list[dict[str, object]] = []
    loo_prl_rows: list[dict[str, object]] = []

    for held_out in healthy_ids:
        work = primary.copy()
        stage_scores: list[pd.DataFrame] = []
        for stage_label, stage_frame in work.groupby("stage_label", dropna=False):
            healthy = stage_frame[(stage_frame["group_label"] == "Healthy") & (stage_frame["subject_id"] != held_out)].copy()
            if len(healthy) < 3:
                continue
            cap_med = float(np.nanmedian(healthy["delta_capacity_rest"]))
            gui_med = float(np.nanmedian(healthy["delta_guidance_rest"]))
            cap_scale = _safe_scale(healthy["delta_capacity_rest"])
            gui_scale = _safe_scale(healthy["delta_guidance_rest"])
            temp = stage_frame.copy()
            temp["esb2_loo"] = np.sqrt(
                ((temp["delta_capacity_rest"] - cap_med) / cap_scale) ** 2
                + ((temp["delta_guidance_rest"] - gui_med) / gui_scale) ** 2
            ) / np.sqrt(2.0)
            stage_scores.append(temp)
        if not stage_scores:
            continue
        rescored = pd.concat(stage_scores, ignore_index=True)
        peak = rescored[rescored["stage_label"] == PRIMARY_STAGE].copy()
        for contrast_name, left_group, right_group in (("AD_vs_Healthy", "AD", "Healthy"), ("FTD_vs_Healthy", "FTD", "Healthy")):
            row = {
                "held_out_healthy_id": held_out,
                "score_name": "esb2_loo",
                "contrast_name": contrast_name,
                "stage_label": PRIMARY_STAGE,
            }
            row.update(_score_contrast(peak, value_col="esb2_loo", left_group=left_group, right_group=right_group))
            loo_rows.append(row)

        template = (
            rescored[rescored["group_label"] == "Healthy"].groupby("stage_label", dropna=False)["esb2_loo"].median().reindex(STAGE_ORDER)
        )
        template_values = template.to_numpy(dtype=float)
        prl_rows: list[dict[str, object]] = []
        for subject_id, subject_frame in rescored.groupby("subject_id", dropna=False):
            profile = subject_frame.groupby("stage_label", dropna=False)["esb2_loo"].mean().reindex(STAGE_ORDER)
            subject_values = profile.to_numpy(dtype=float)
            valid = np.isfinite(template_values) & np.isfinite(subject_values)
            score = float("nan")
            corr = float("nan")
            if int(valid.sum()) >= 3:
                tpl = template_values[valid]
                subj = subject_values[valid]
                if np.nanstd(tpl) > 0 and np.nanstd(subj) > 0:
                    corr = float(np.corrcoef(tpl, subj)[0, 1])
                    score = float(1.0 - corr)
            first = subject_frame.iloc[0]
            prl_rows.append(
                {
                    "subject_id": subject_id,
                    "group_label": first["group_label"],
                    "prl_loo": score,
                }
            )
        prl_frame = pd.DataFrame(prl_rows)
        for contrast_name, left_group, right_group in (("AD_vs_Healthy", "AD", "Healthy"), ("FTD_vs_Healthy", "FTD", "Healthy")):
            row = {
                "held_out_healthy_id": held_out,
                "score_name": "prl_loo",
                "contrast_name": contrast_name,
                "stage_label": "profile_all",
            }
            row.update(_score_contrast(prl_frame, value_col="prl_loo", left_group=left_group, right_group=right_group))
            loo_prl_rows.append(row)

    return pd.DataFrame(loo_rows), pd.DataFrame(loo_prl_rows)


def _permutation_effect(values: np.ndarray, labels: np.ndarray, left_label: str, right_label: str) -> float:
    left = values[labels == left_label]
    right = values[labels == right_label]
    return _cohens_d(left, right)


def build_permutation_qc(scored: pd.DataFrame, prl_scores: pd.DataFrame, *, n_permutations: int, rng_seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(rng_seed)
    rows: list[dict[str, object]] = []
    primary_stage = scored[(scored["spec_name"] == PRIMARY_SPEC) & (scored["stage_label"] == PRIMARY_STAGE)].copy()
    for score_name in ("esb2_ds004504",):
        for contrast_name, left_group, right_group in (("AD_vs_Healthy", "AD", "Healthy"), ("FTD_vs_Healthy", "FTD", "Healthy")):
            sub = primary_stage[primary_stage["group_label"].isin([left_group, right_group])].copy()
            values = pd.to_numeric(sub[score_name], errors="coerce").to_numpy(dtype=float)
            labels = sub["group_label"].astype(str).to_numpy()
            valid = np.isfinite(values)
            values = values[valid]
            labels = labels[valid]
            observed = _permutation_effect(values, labels, left_group, right_group)
            perm = np.empty((n_permutations,), dtype=float)
            for idx in range(n_permutations):
                perm_labels = rng.permutation(labels)
                perm[idx] = _permutation_effect(values, perm_labels, left_group, right_group)
            p_emp = float((np.abs(perm) >= abs(observed)).mean()) if np.isfinite(observed) else float("nan")
            rows.append(
                {
                    "score_name": score_name,
                    "spec_name": PRIMARY_SPEC,
                    "stage_label": PRIMARY_STAGE,
                    "contrast_name": contrast_name,
                    "observed_effect_size": observed,
                    "empirical_p_value": p_emp,
                    "n_permutations": int(n_permutations),
                }
            )

    primary_prl = prl_scores[prl_scores["spec_name"] == PRIMARY_SPEC].copy()
    for contrast_name, left_group, right_group in (("AD_vs_Healthy", "AD", "Healthy"), ("FTD_vs_Healthy", "FTD", "Healthy")):
        sub = primary_prl[primary_prl["group_label"].isin([left_group, right_group])].copy()
        values = pd.to_numeric(sub["prl_score"], errors="coerce").to_numpy(dtype=float)
        labels = sub["group_label"].astype(str).to_numpy()
        valid = np.isfinite(values)
        values = values[valid]
        labels = labels[valid]
        observed = _permutation_effect(values, labels, left_group, right_group)
        perm = np.empty((n_permutations,), dtype=float)
        for idx in range(n_permutations):
            perm_labels = rng.permutation(labels)
            perm[idx] = _permutation_effect(values, perm_labels, left_group, right_group)
        p_emp = float((np.abs(perm) >= abs(observed)).mean()) if np.isfinite(observed) else float("nan")
        rows.append(
            {
                "score_name": "prl_score",
                "spec_name": PRIMARY_SPEC,
                "stage_label": "profile_all",
                "contrast_name": contrast_name,
                "observed_effect_size": observed,
                "empirical_p_value": p_emp,
                "n_permutations": int(n_permutations),
            }
        )
    return pd.DataFrame(rows)


def build_recovery_subset_stability(scored: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    primary = scored[(scored["spec_name"] == PRIMARY_SPEC) & (scored["stage_label"] == PRIMARY_STAGE)].copy()
    subsets = {
        "all_subjects": primary.copy(),
        "recovery_eye2_only": primary[pd.to_numeric(primary["recovery_eye_window_n"], errors="coerce") >= 2].copy(),
    }
    for subset_name, subset in subsets.items():
        for contrast_name, left_group, right_group in (("AD_vs_Healthy", "AD", "Healthy"), ("FTD_vs_Healthy", "FTD", "Healthy")):
            row = {
                "subset_name": subset_name,
                "spec_name": PRIMARY_SPEC,
                "stage_label": PRIMARY_STAGE,
                "score_name": "esb2_ds004504",
                "contrast_name": contrast_name,
            }
            row.update(_score_contrast(subset, value_col="esb2_ds004504", left_group=left_group, right_group=right_group))
            rows.append(row)
    return pd.DataFrame(rows)


def build_reference_comparison(contrasts: pd.DataFrame, reference_effects_path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    primary = contrasts[
        (contrasts["score_name"] == "esb2_ds004504")
        & (contrasts["contrast_name"] == "AD_vs_Healthy")
        & (contrasts["spec_name"] == PRIMARY_SPEC)
    ].copy()
    if not primary.empty:
        peak = primary.sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]
        rows.append(
            {
                "analysis_family": "ESB2",
                "metric": "esb2_ds004504",
                "spec_name": peak["spec_name"],
                "stage_label": peak["stage_label"],
                "effect_size": peak["effect_size"],
                "p_value": peak["p_value"],
                "q_value": peak["q_value"],
                "note": "Primary ESB-2 AD vs Healthy row in follow-up article workflow",
            }
        )
    if reference_effects_path.exists():
        ref = pd.read_csv(reference_effects_path)
        ref = ref[(ref["contrast_name"] == "AD_vs_Healthy")].copy() if "contrast_name" in ref.columns else ref
        if not ref.empty:
            if "abs_effect" not in ref.columns and "abs_effect_size" in ref.columns:
                ref["abs_effect"] = pd.to_numeric(ref["abs_effect_size"], errors="coerce")
            sort_cols = [col for col in ("q_value", "p_value", "abs_effect") if col in ref.columns]
            peak = ref.sort_values(sort_cols, na_position="last").iloc[0] if sort_cols else ref.iloc[0]
            rows.append(
                {
                    "analysis_family": "MNJ_reference",
                    "metric": peak.get("metric"),
                    "spec_name": peak.get("analysis_label", peak.get("analysis_key")),
                    "stage_label": peak.get("stage_label"),
                    "effect_size": peak.get("effect_size"),
                    "p_value": peak.get("p_value"),
                    "q_value": peak.get("q_value"),
                    "note": "Matched sibling photic article reference from resting-vs-photic bundle",
                }
            )
    return pd.DataFrame(rows)


def build_summary_markdown(
    esb_contrasts: pd.DataFrame,
    crossfit_contrasts: pd.DataFrame,
    prl_contrasts: pd.DataFrame,
    axis_contrasts: pd.DataFrame,
    reference_comparison: pd.DataFrame,
    spec_sensitivity: pd.DataFrame,
    dataset_comparability: pd.DataFrame,
    negative_results: pd.DataFrame,
    frequency_peak_audit: pd.DataFrame,
) -> str:
    lines = [
        "# ESB article summary",
        "",
        "## Main ESB-2 result",
        "",
    ]
    primary = esb_contrasts[
        (esb_contrasts["score_name"] == "esb2_ds004504")
        & (esb_contrasts["contrast_name"] == "AD_vs_Healthy")
    ].copy()
    if not primary.empty:
        top = primary.sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]
        lines.append(
            f"- Strongest `AD vs Healthy` ESB-2 row: `{top['spec_name']}` / `{top['stage_label']}` with "
            f"`d = {float(top['effect_size']):.3f}`, `p = {float(top['p_value']):.4g}`, `q = {float(top['q_value']):.4g}`."
        )
    ftd = esb_contrasts[
        (esb_contrasts["score_name"] == "esb2_ds004504")
        & (esb_contrasts["contrast_name"] == "FTD_vs_Healthy")
    ].copy()
    if not ftd.empty:
        top = ftd.sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]
        lines.append(
            f"- Strongest `FTD vs Healthy` ESB-2 row: `{top['spec_name']}` / `{top['stage_label']}` with "
            f"`d = {float(top['effect_size']):.3f}`, `p = {float(top['p_value']):.4g}`, `q = {float(top['q_value']):.4g}`."
        )
    if not crossfit_contrasts.empty:
        lines.extend(["", "## Cross-fitted healthy-template check", ""])
        for contrast_name in ("AD_vs_Healthy", "FTD_vs_Healthy"):
            sub = crossfit_contrasts[
                (crossfit_contrasts["contrast_name"] == contrast_name)
                & (crossfit_contrasts["stage_label"] == PRIMARY_STAGE)
            ].copy()
            if sub.empty:
                continue
            row = sub.sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]
            lines.append(
                f"- `{contrast_name}` / `{PRIMARY_STAGE}` / `esb2_crossfit_hc`: "
                f"d={float(row['effect_size']):.3f}, p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
            )

    lines.extend(["", "## PRL", ""])
    prl = prl_contrasts[prl_contrasts["contrast_name"] == "AD_vs_Healthy"].copy()
    if not prl.empty:
        top = prl.sort_values(["q_value", "p_value", "abs_effect"], na_position="last").iloc[0]
        lines.append(
            f"- Strongest `AD vs Healthy` PRL row: `{top['spec_name']}` with "
            f"`d = {float(top['effect_size']):.3f}`, `p = {float(top['p_value']):.4g}`, `q = {float(top['q_value']):.4g}`."
        )

    lines.extend(["", "## Axis decomposition", ""])
    axis = axis_contrasts[
        (axis_contrasts["contrast_name"] == "AD_vs_Healthy")
        & (axis_contrasts["spec_name"] == PRIMARY_SPEC)
    ].copy()
    if not axis.empty:
        for _, row in axis.sort_values(["q_value", "p_value", "abs_effect"], na_position="last").head(4).iterrows():
            lines.append(
                f"- `{row['axis_name']}` / `{row['stage_label']}`: d={float(row['effect_size']):.3f}, "
                f"p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
            )

    if not reference_comparison.empty:
        lines.extend(["", "## Comparison to MNJ reference", ""])
        for _, row in reference_comparison.iterrows():
            lines.append(
                f"- `{row['analysis_family']}` / `{row['stage_label']}` / `{row['metric']}`: "
                f"d={float(row['effect_size']):.3f}, p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}"
            )
    if not spec_sensitivity.empty:
        lines.extend(["", "## Specification sensitivity", ""])
        realized = spec_sensitivity[spec_sensitivity["available_in_surface"]].copy()
        if not realized.empty:
            for _, row in realized.sort_values(["contrast_name", "q_value", "effect_size"], na_position="last").iterrows():
                lines.append(
                    f"- `{row['contrast_name']}` / `{row['spec_name']}` at `{row['stage_label']}`: "
                    f"d={float(row['effect_size']):.3f}, q={float(row['q_value']):.4g}"
                )
        missing = spec_sensitivity[~spec_sensitivity["available_in_surface"]].drop_duplicates(subset=["spec_name"])
        for _, row in missing.iterrows():
            lines.append(f"- Missing planned spec `{row['spec_name']}`: {row['availability_note']}")
    if not dataset_comparability.empty:
        row = dataset_comparability.iloc[0]
        lines.extend(
            [
                "",
                "## Dataset comparability",
                "",
                f"- Matched ds004504 baselines were available for `{int(row['rest_matched_subjects_total'])}` / `{int(row['photic_subjects_total'])}` photic subjects.",
                f"- Group totals on the matched surface were `Healthy={int(row['healthy_total'])}`, `AD={int(row['ad_total'])}`, `FTD={int(row['ftd_total'])}`.",
                f"- Primary-stage analyzable counts were `Healthy={int(row['healthy_primary_stage_n'])}`, `AD={int(row['ad_primary_stage_n'])}`, `FTD={int(row['ftd_primary_stage_n'])}`.",
            ]
        )
    if not negative_results.empty:
        lines.extend(["", "## Negative findings", ""])
        for _, row in negative_results.iterrows():
            lines.append(
                f"- `{row['result_family']}` / `{row['contrast_name']}`: corrected rows={int(row['corrected_rows_q_lt_0_05'])}, "
                f"best scope=`{row['best_stage_or_scope']}`, best d={float(row['best_effect_size']):.3f}, best q={float(row['best_q_value']):.4g}"
            )
    if not frequency_peak_audit.empty:
        lines.extend(["", "## Frequency audit for primary ESB-2 spec", ""])
        for _, row in frequency_peak_audit.iterrows():
            lines.append(
                f"- `{row['contrast_name']}` / `{row['stage_label']}`: "
                f"d={float(row['effect_size']):.3f}, p={float(row['p_value']):.4g}, "
                f"frequency-wise q={float(row['frequency_q_value']):.4g}"
            )
    return "\n".join(lines) + "\n"


def build_qc_summary_markdown(
    loo_esb: pd.DataFrame,
    loo_prl: pd.DataFrame,
    permutation_qc: pd.DataFrame,
    stability_qc: pd.DataFrame,
    crossfit_contrasts: pd.DataFrame,
) -> str:
    lines = [
        "# ESB QC summary",
        "",
        "## Leave-one-out healthy template sensitivity",
        "",
    ]
    for name, frame in (("ESB-2", loo_esb), ("PRL", loo_prl)):
        if frame.empty:
            continue
        summary = (
            frame.groupby("contrast_name", dropna=False)["effect_size"]
            .agg(["median", "min", "max"])
            .reset_index()
        )
        lines.append(f"### {name}")
        lines.append("")
        for _, row in summary.iterrows():
            lines.append(
                f"- `{row['contrast_name']}` effect-size range under leave-one-out: "
                f"median={float(row['median']):.3f}, min={float(row['min']):.3f}, max={float(row['max']):.3f}"
            )
        lines.append("")

    if not permutation_qc.empty:
        lines.extend(["## Permutation tests", ""])
        for _, row in permutation_qc.iterrows():
            lines.append(
                f"- `{row['score_name']}` / `{row['contrast_name']}` / `{row['stage_label']}`: "
                f"observed d={float(row['observed_effect_size']):.3f}, empirical p={float(row['empirical_p_value']):.4g}"
            )
        lines.append("")

    if not stability_qc.empty:
        lines.extend(["## Recovery-coverage subset stability", ""])
        for _, row in stability_qc.iterrows():
            lines.append(
                f"- `{row['subset_name']}` / `{row['contrast_name']}`: "
                f"d={float(row['effect_size']):.3f}, p={float(row['p_value']):.4g}, "
                f"n=({int(row['left_n'])},{int(row['right_n'])})"
            )
    if not crossfit_contrasts.empty:
        lines.extend(["", "## Cross-fitted healthy-template contrasts", ""])
        for _, row in crossfit_contrasts[
            crossfit_contrasts["stage_label"] == PRIMARY_STAGE
        ].sort_values(["contrast_name", "q_value", "p_value"], na_position="last").iterrows():
            lines.append(
                f"- `{row['contrast_name']}` / `{row['stage_label']}`: "
                f"d={float(row['effect_size']):.3f}, p={float(row['p_value']):.4g}, q={float(row['q_value']):.4g}, "
                f"n=({int(row['left_n'])},{int(row['right_n'])})"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    metric_frame = load_metric_frame(args.photic_results_root)
    scored = build_esb_scores(args)
    inventory = build_window_inventory(args.photic_raw_root)
    esb_group_summary = build_esb_group_summary(scored)
    esb_contrasts = build_esb_contrasts(scored)
    axis_contrasts = build_axis_contrasts(scored)
    crossfit_scores = build_cross_fitted_primary_scores(scored)
    crossfit_contrasts = build_cross_fitted_contrasts(crossfit_scores)
    prl_scores = build_prl_scores(scored)
    prl_group_summary = build_prl_group_summary(prl_scores)
    prl_contrasts = build_prl_contrasts(prl_scores)
    stage_coverage = build_stage_coverage(scored, inventory)
    loo_esb, loo_prl = build_leave_one_out_qc(scored, prl_scores)
    permutation_qc = build_permutation_qc(
        scored,
        prl_scores,
        n_permutations=args.n_permutations,
        rng_seed=args.rng_seed,
    )
    recovery_subset_stability = build_recovery_subset_stability(scored)
    reference_comparison = build_reference_comparison(esb_contrasts, args.reference_effects_path)
    spec_sensitivity = build_spec_sensitivity_summary(esb_contrasts, metric_frame)
    dataset_comparability = build_dataset_comparability(scored)
    negative_results = build_negative_results_summary(esb_contrasts, prl_contrasts)
    frequency_peak_audit = build_frequency_peak_audit(esb_contrasts)
    repro_commands = build_reproducibility_commands()

    summary_md = build_summary_markdown(
        esb_contrasts,
        crossfit_contrasts,
        prl_contrasts,
        axis_contrasts,
        reference_comparison,
        spec_sensitivity,
        dataset_comparability,
        negative_results,
        frequency_peak_audit,
    )
    qc_summary_md = build_qc_summary_markdown(loo_esb, loo_prl, permutation_qc, recovery_subset_stability, crossfit_contrasts)

    esb_scores_path = args.output_dir / "esb_subject_scores.csv"
    esb_group_path = args.output_dir / "esb_group_summary.csv"
    esb_contrasts_path = args.output_dir / "esb_contrasts.csv"
    axis_contrasts_path = args.output_dir / "esb_axis_contrasts.csv"
    crossfit_scores_path = args.output_dir / "qc_cross_fitted_esb2_scores.csv"
    crossfit_contrasts_path = args.output_dir / "qc_cross_fitted_esb2_contrasts.csv"
    prl_scores_path = args.output_dir / "prl_subject_scores.csv"
    prl_group_path = args.output_dir / "prl_group_summary.csv"
    prl_contrasts_path = args.output_dir / "prl_contrasts.csv"
    coverage_path = args.output_dir / "stage_coverage_summary.csv"
    loo_esb_path = args.output_dir / "qc_leave_one_out_esb2.csv"
    loo_prl_path = args.output_dir / "qc_leave_one_out_prl.csv"
    permutation_path = args.output_dir / "qc_permutation_tests.csv"
    stability_path = args.output_dir / "qc_recovery_subset_stability.csv"
    reference_path = args.output_dir / "qc_reference_comparison.csv"
    spec_sensitivity_path = args.output_dir / "qc_spec_sensitivity_summary.csv"
    comparability_path = args.output_dir / "dataset_comparability_summary.csv"
    negative_results_path = args.output_dir / "negative_results_summary.csv"
    frequency_peak_audit_path = args.output_dir / "qc_frequency_peak_audit.csv"
    summary_md_path = args.output_dir / "esb_article_summary.md"
    qc_md_path = args.output_dir / "esb_qc_summary.md"
    repro_commands_path = args.output_dir / "reproducibility_commands.md"
    manifest_path = args.output_dir / "esb_article_manifest.json"

    scored.to_csv(esb_scores_path, index=False)
    esb_group_summary.to_csv(esb_group_path, index=False)
    esb_contrasts.to_csv(esb_contrasts_path, index=False)
    axis_contrasts.to_csv(axis_contrasts_path, index=False)
    crossfit_scores.to_csv(crossfit_scores_path, index=False)
    crossfit_contrasts.to_csv(crossfit_contrasts_path, index=False)
    prl_scores.to_csv(prl_scores_path, index=False)
    prl_group_summary.to_csv(prl_group_path, index=False)
    prl_contrasts.to_csv(prl_contrasts_path, index=False)
    stage_coverage.to_csv(coverage_path, index=False)
    loo_esb.to_csv(loo_esb_path, index=False)
    loo_prl.to_csv(loo_prl_path, index=False)
    permutation_qc.to_csv(permutation_path, index=False)
    recovery_subset_stability.to_csv(stability_path, index=False)
    reference_comparison.to_csv(reference_path, index=False)
    spec_sensitivity.to_csv(spec_sensitivity_path, index=False)
    dataset_comparability.to_csv(comparability_path, index=False)
    negative_results.to_csv(negative_results_path, index=False)
    frequency_peak_audit.to_csv(frequency_peak_audit_path, index=False)
    summary_md_path.write_text(summary_md, encoding="utf-8")
    qc_md_path.write_text(qc_summary_md, encoding="utf-8")
    repro_commands_path.write_text(repro_commands, encoding="utf-8")

    manifest = {
        "article_dir": str(ARTICLE_DIR),
        "source_photic_results_root": str(args.photic_results_root),
        "source_photic_raw_root": str(args.photic_raw_root),
        "source_rest_raw_root": str(args.rest_raw_root),
        "reference_effects_path": str(args.reference_effects_path),
        "primary_spec": PRIMARY_SPEC,
        "primary_stage": PRIMARY_STAGE,
        "n_permutations": int(args.n_permutations),
        "rng_seed": int(args.rng_seed),
        "output_files": {
            "esb_subject_scores": str(esb_scores_path),
            "esb_group_summary": str(esb_group_path),
            "esb_contrasts": str(esb_contrasts_path),
            "esb_axis_contrasts": str(axis_contrasts_path),
            "qc_cross_fitted_esb2_scores": str(crossfit_scores_path),
            "qc_cross_fitted_esb2_contrasts": str(crossfit_contrasts_path),
            "prl_subject_scores": str(prl_scores_path),
            "prl_group_summary": str(prl_group_path),
            "prl_contrasts": str(prl_contrasts_path),
            "stage_coverage_summary": str(coverage_path),
            "qc_leave_one_out_esb2": str(loo_esb_path),
            "qc_leave_one_out_prl": str(loo_prl_path),
            "qc_permutation_tests": str(permutation_path),
            "qc_recovery_subset_stability": str(stability_path),
            "qc_reference_comparison": str(reference_path),
            "qc_spec_sensitivity_summary": str(spec_sensitivity_path),
            "dataset_comparability_summary": str(comparability_path),
            "negative_results_summary": str(negative_results_path),
            "qc_frequency_peak_audit": str(frequency_peak_audit_path),
            "summary_markdown": str(summary_md_path),
            "qc_summary_markdown": str(qc_md_path),
            "reproducibility_commands": str(repro_commands_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote ESB article outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
