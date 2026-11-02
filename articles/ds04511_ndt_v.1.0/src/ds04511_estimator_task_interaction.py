"""Exploratory estimator-by-task interaction for chart and one-step L3 alpha.

This runner compares task contrasts only on subjects with both exported
estimators available for the relevant tasks. Endpoint units are not compared
raw: each estimator is standardized once, outcome-blind, using a pooled
recording-level robust location and scale before any task contrasts are formed.
No estimator is refit and no missing value is filled.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ds04511_common import ARTICLE_DIR, json_safe, sha256_file, write_json
from ds04511_level_panel import LEVEL_METRICS
from ds04511_panel import BOOTSTRAP_N, BOOTSTRAP_SEED, CONTRASTS
from ds04511_stats import (
    bh_fdr,
    cohens_dz,
    exact_sign_test_p,
    percentile_bootstrap,
    wilcoxon_p,
)
from ds04511_task_part1 import LABELS_DEFAULT, SUPPORT_DEFAULT, extract_recordings, load_cohort


ANALYSIS_ID = "estimator_task_interaction_alpha_20260922"
OUTPUT_DEFAULT = ARTICLE_DIR / "results" / "v1_estimator_task_interaction_20260922"
CHART_METRIC_ID = "jacobian_alpha"
L3_METRIC_ID = "one_step_spectral_abscissa"
ALPHA_METRIC_IDS = (CHART_METRIC_ID, L3_METRIC_ID)
PERMUTATION_N = 100_000
PERMUTATION_SEED = 20260922
ROBUST_MAD_CONSTANT = 1.4826
ROBUST_IQR_CONSTANT = 1.3489795

METRIC_BY_ID = {spec.metric_id: spec for spec in LEVEL_METRICS}
ALPHA_METRICS = tuple(METRIC_BY_ID[metric_id] for metric_id in ALPHA_METRIC_IDS)


def _finite(values: Any) -> np.ndarray:
    array = np.asarray(values, dtype=float).reshape(-1)
    return array[np.isfinite(array)]


def robust_location_scale(values: Any) -> dict[str, Any]:
    """Return pre-specified outcome-blind robust center and scale.

    The primary scale is 1.4826*MAD. Deterministic IQR and standard-deviation
    fallbacks only handle a degenerate MAD; none uses task labels or contrasts.
    """
    finite = _finite(values)
    result: dict[str, Any] = {
        "n": int(finite.size),
        "center": float("nan"),
        "scale": float("nan"),
        "method": "unavailable",
    }
    if finite.size == 0:
        return result
    center = float(np.median(finite))
    mad = float(np.median(np.abs(finite - center)))
    scale = ROBUST_MAD_CONSTANT * mad
    method = "median_1.4826_mad"
    if not np.isfinite(scale) or scale <= 0.0:
        q25, q75 = np.percentile(finite, [25.0, 75.0])
        scale = float((q75 - q25) / ROBUST_IQR_CONSTANT)
        method = "median_iqr_1.3489795_fallback"
    if not np.isfinite(scale) or scale <= 0.0:
        scale = float(np.std(finite, ddof=1)) if finite.size >= 2 else float("nan")
        method = "median_sd_fallback"
    if not np.isfinite(scale) or scale <= 0.0:
        return result | {"center": center, "method": "degenerate_scale"}
    result.update({"center": center, "scale": scale, "method": method})
    return result


def standardize(values: Any, calibration: dict[str, Any]) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    center = float(calibration.get("center", np.nan))
    scale = float(calibration.get("scale", np.nan))
    if not np.isfinite(center) or not np.isfinite(scale) or scale <= 0.0:
        return np.full(array.shape, np.nan, dtype=float)
    result = (array - center) / scale
    result[~np.isfinite(array)] = np.nan
    return result


def _support_columns(support_path: Path) -> pd.DataFrame:
    support = pd.read_csv(support_path)
    wanted = [
        "source_h5",
        "jacobian__derived_metrics__v1__computation_status",
        "one_step_computation_status",
        "one_step_support_status",
        "one_step_qualification_status",
        "one_step_measurement_validity",
        "one_step_failure_reason",
    ]
    columns = [column for column in wanted if column in support.columns]
    return support[columns].drop_duplicates("source_h5")


def _production_reason(row: pd.Series, metric_id: str) -> str:
    included = bool(row.get(f"{metric_id}_included", False))
    value = row.get(f"{metric_id}_median", np.nan)
    h5_status = str(row.get(f"{metric_id}_computation_status", ""))
    if h5_status != "computed":
        return "metric_computation_not_computed"
    if metric_id == CHART_METRIC_ID:
        if str(row.get("jacobian__derived_metrics__v1__computation_status", "")) != "computed":
            return "production_jacobian_not_computed"
    if metric_id == L3_METRIC_ID:
        if str(row.get("one_step_computation_status", "")) != "computed":
            return "production_one_step_not_computed"
        if str(row.get("one_step_support_status", "")) != "sufficient":
            return "production_one_step_support_insufficient"
        if str(row.get("one_step_qualification_status", "")) != "one_step_identified":
            return "production_one_step_not_identified"
    if not included or not np.isfinite(float(value)):
        return "missing_or_nonfinite_median"
    return "ok"


def extract_alpha_recordings(
    labels_path: Path,
    support_path: Path,
    *,
    workers: int,
) -> pd.DataFrame:
    cohort = load_cohort(labels_path, support_path)
    cohort = cohort.merge(_support_columns(support_path), on="source_h5", how="left", suffixes=("", "_support"))
    recordings = extract_recordings(cohort, workers=workers, metrics=ALPHA_METRICS)
    for metric_id in ALPHA_METRIC_IDS:
        recordings[f"{metric_id}_reason"] = recordings.apply(
            _production_reason, axis=1, metric_id=metric_id
        )
        recordings[f"{metric_id}_usable"] = recordings[f"{metric_id}_reason"] == "ok"
    recordings["common_estimator_support"] = recordings[
        [f"{metric_id}_usable" for metric_id in ALPHA_METRIC_IDS]
    ].all(axis=1)
    return recordings


def subject_task_table(recordings: pd.DataFrame, calibrations: dict[str, dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (subject_id, task_label), group in recordings.groupby(["subject_id", "task_label"], dropna=False):
        row: dict[str, Any] = {
            "subject_id": subject_id,
            "task_label": task_label,
            "n_recordings": int(len(group)),
        }
        for metric_id in ALPHA_METRIC_IDS:
            usable = group.loc[group[f"{metric_id}_usable"], f"{metric_id}_median"]
            values = pd.to_numeric(usable, errors="coerce").dropna()
            row[metric_id] = float(values.median()) if len(values) else float("nan")
            row[f"{metric_id}_n_recordings_included"] = int(len(values))
            row[f"{metric_id}_z"] = float(
                standardize(np.asarray([row[metric_id]], dtype=float), calibrations[metric_id])[0]
            )
        row["common_estimator_support"] = bool(
            np.isfinite(row[f"{CHART_METRIC_ID}_z"])
            and np.isfinite(row[f"{L3_METRIC_ID}_z"])
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _sign_flip_p(values: Any, *, n_permutations: int = PERMUTATION_N, seed: int = PERMUTATION_SEED) -> float:
    array = _finite(values)
    if array.size == 0:
        return float("nan")
    observed = abs(float(np.mean(array)))
    if array.size <= 16:
        n_patterns = 1 << array.size
        count = 0
        for pattern in range(n_patterns):
            signs = np.where(((pattern >> np.arange(array.size)) & 1) == 1, 1.0, -1.0)
            count += abs(float(np.mean(array * signs))) >= observed - 1e-15
        return float(count / n_patterns)
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.asarray([-1.0, 1.0]), size=(n_permutations, array.size))
    permuted = np.abs(np.mean(signs * array[None, :], axis=1))
    count = int(np.sum(permuted >= observed - 1e-15))
    return float((count + 1) / (n_permutations + 1))


def interaction_pairs(subjects: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for contrast in CONTRASTS:
        later = subjects[subjects["task_label"] == contrast.later_task][
            [
                "subject_id",
                f"{CHART_METRIC_ID}_z",
                f"{L3_METRIC_ID}_z",
            ]
        ].rename(
            columns={
                f"{CHART_METRIC_ID}_z": "chart_later",
                f"{L3_METRIC_ID}_z": "l3_later",
            }
        )
        earlier = subjects[subjects["task_label"] == contrast.earlier_task][
            [
                "subject_id",
                f"{CHART_METRIC_ID}_z",
                f"{L3_METRIC_ID}_z",
            ]
        ].rename(
            columns={
                f"{CHART_METRIC_ID}_z": "chart_earlier",
                f"{L3_METRIC_ID}_z": "l3_earlier",
            }
        )
        pair = later.merge(earlier, on="subject_id", how="inner")
        for column in ["chart_later", "chart_earlier", "l3_later", "l3_earlier"]:
            pair[column] = pd.to_numeric(pair[column], errors="coerce")
        pair["chart_task_difference"] = pair["chart_later"] - pair["chart_earlier"]
        pair["l3_task_difference"] = pair["l3_later"] - pair["l3_earlier"]
        pair["interaction_difference"] = pair["chart_task_difference"] - pair["l3_task_difference"]
        pair["contrast_id"] = contrast.contrast_id
        pair["later_task"] = contrast.later_task
        pair["earlier_task"] = contrast.earlier_task
        pair["common_complete"] = np.isfinite(pair["interaction_difference"])
        frames.append(pair)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def interaction_results(pairs: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for index, (contrast_id, group) in enumerate(pairs.groupby("contrast_id", sort=False)):
        values = _finite(group.loc[group["common_complete"], "interaction_difference"])
        median_ci_lo, median_ci_hi, n_boot_used = percentile_bootstrap(
            values,
            np.median,
            n_boot=BOOTSTRAP_N,
            seed=BOOTSTRAP_SEED + 10_000 + index,
        )
        row: dict[str, Any] = {
            "analysis_id": ANALYSIS_ID,
            "contrast_id": contrast_id,
            "later_task": str(group["later_task"].iloc[0]),
            "earlier_task": str(group["earlier_task"].iloc[0]),
            "n_subject_pairs": int(values.size),
            "n_nonzero": int(np.sum(values != 0.0)),
            "n_positive": int(np.sum(values > 0.0)),
            "n_negative": int(np.sum(values < 0.0)),
            "median_interaction_difference": float(np.median(values)) if values.size else float("nan"),
            "mean_interaction_difference": float(np.mean(values)) if values.size else float("nan"),
            "cohens_dz": cohens_dz(values),
            "median_bootstrap_ci_lo": median_ci_lo,
            "median_bootstrap_ci_hi": median_ci_hi,
            "bootstrap_n": BOOTSTRAP_N,
            "bootstrap_seed": BOOTSTRAP_SEED + 10_000 + index,
            "n_boot_used": n_boot_used,
            "wilcoxon_p": wilcoxon_p(values),
            "sign_test_p": exact_sign_test_p(values),
            "sign_flip_mean_p": _sign_flip_p(values, seed=PERMUTATION_SEED + index),
            "sign_flip_n": PERMUTATION_N if values.size > 16 else 1 << values.size,
            "sign_flip_seed": PERMUTATION_SEED + index,
            "primary_p_family": "wilcoxon_3_contrast_interaction_family",
            "test_scope": "exploratory_estimator_task_interaction",
            "standardization": "estimator-specific common-set pooled recording median / 1.4826*MAD",
        }
        rows.append(row)
    table = pd.DataFrame(rows)
    if not table.empty:
        table["wilcoxon_bh_q_3_family"] = bh_fdr(table["wilcoxon_p"].to_numpy())
    return table


def _fmt(value: Any, digits: int = 5) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "nan"
    return "nan" if not np.isfinite(number) else f"{number:.{digits}g}"


def missingness_table(recordings: pd.DataFrame, subjects: pd.DataFrame, pairs: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for metric_id in ALPHA_METRIC_IDS:
        reason = recordings[f"{metric_id}_reason"].astype(str)
        for task, group in recordings.groupby("task_label", dropna=False):
            task_reason = group[f"{metric_id}_reason"].astype(str)
            rows.append(
                {
                    "stage": "recording",
                    "metric": metric_id,
                    "task_label": task,
                    "n_total": int(len(group)),
                    "n_ok": int((task_reason == "ok").sum()),
                    "n_missing_or_unsupported": int((task_reason != "ok").sum()),
                    "n_common_both_estimators": int(
                        group.loc[task_reason == "ok", "common_estimator_support"].sum()
                        if metric_id == L3_METRIC_ID
                        else group.loc[task_reason == "ok", "common_estimator_support"].sum()
                    ),
                    "reason_counts": json.dumps(task_reason.value_counts().to_dict(), sort_keys=True),
                }
            )
    for task, group in subjects.groupby("task_label", dropna=False):
        rows.append(
            {
                "stage": "subject_task",
                "metric": "common_estimator_support",
                "task_label": task,
                "n_total": int(len(group)),
                "n_ok": int(group["common_estimator_support"].sum()),
                "n_missing_or_unsupported": int((~group["common_estimator_support"]).sum()),
                "n_common_both_estimators": int(group["common_estimator_support"].sum()),
                "reason_counts": "",
            }
        )
    for contrast_id, group in pairs.groupby("contrast_id", sort=False):
        rows.append(
            {
                "stage": "subject_contrast",
                "metric": "common_estimator_support",
                "task_label": contrast_id,
                "n_total": int(len(group)),
                "n_ok": int(group["common_complete"].sum()),
                "n_missing_or_unsupported": int((~group["common_complete"]).sum()),
                "n_common_both_estimators": int(group["common_complete"].sum()),
                "reason_counts": "",
            }
        )
    return pd.DataFrame(rows)


def write_report(
    path: Path,
    results: pd.DataFrame,
    recordings: pd.DataFrame,
    subjects: pd.DataFrame,
    calibrations: dict[str, dict[str, Any]],
) -> None:
    lines = [
        "# ds004511 estimator × task interaction: chart alpha vs one-step L3 alpha",
        "",
        f"Analysis id: `{ANALYSIS_ID}`. Exploratory interaction only; production measurements and Typst sources are unchanged.",
        "",
        "Interaction estimand: for each subject and task contrast, (standardized chart-Jacobian α later−earlier) minus (standardized one-step L3 α later−earlier). The primary null is zero interaction.",
        "",
        "Outcome-blind standardization was fixed before task contrasts: each estimator was centered by its pooled recording-level median and scaled by 1.4826×MAD on the common estimator-supported recording set; IQR and sample-SD fallbacks were used only for a degenerate MAD. No task labels, outcome p-values, refit, interpolation, or zero filling entered calibration.",
        "",
        "The chart and one-step series do not expose a shared per-window validity path with identical indexing. Common support therefore means common exported recording/subject-task support under the existing production computation/support gates, not pointwise temporal alignment.",
        "",
        "## Production support and calibration",
        "",
        "| estimator | recording n usable | calibration n | center | robust scale | method |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for metric_id in ALPHA_METRIC_IDS:
        calibration = calibrations[metric_id]
        lines.append(
            f"| `{metric_id}` | {int(recordings[f'{metric_id}_usable'].sum())} | {int(calibration['n'])} | {_fmt(calibration['center'])} | {_fmt(calibration['scale'])} | `{calibration['method']}` |"
        )
    lines.extend(
        [
            "",
            f"One-step L3 support is restricted to the existing production `one_step_support_status=sufficient` and `one_step_qualification_status=one_step_identified` rows. Chart alpha requires its existing computed status and finite production median. Subject/task aggregation is median over retained recordings.",
            "",
            "## Interaction tests",
            "",
            "Wilcoxon p is primary and BH-corrected across the three pre-existing task contrasts in one separate exploratory family. A deterministic paired sign-flip permutation of the mean interaction and a percentile bootstrap CI for the interaction median are reported as robustness quantities.",
            "",
            "| contrast | n | median interaction | 95% bootstrap CI | d_z | Wilcoxon p | BH q (3) | sign-flip p |",
            "| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in results.iterrows():
        lines.append(
            f"| `{row['contrast_id']}` | {int(row['n_subject_pairs'])} | {_fmt(row['median_interaction_difference'])} | [{_fmt(row['median_bootstrap_ci_lo'])}, {_fmt(row['median_bootstrap_ci_hi'])}] | {_fmt(row['cohens_dz'], 4)} | {_fmt(row['wilcoxon_p'])} | {_fmt(row['wilcoxon_bh_q_3_family'])} | {_fmt(row['sign_flip_mean_p'])} |"
        )
    lines.extend(
        [
            "",
            "## Missingness ceiling",
            "",
            f"There are {len(recordings)} recordings and {subjects['subject_id'].nunique()} subjects. The complete subject-contrast counts are shown in `interaction_missingness.csv`; only subjects with both estimators in both tasks enter each interaction row. No missing endpoint is replaced by zero.",
            "",
            "Interpretation ceiling: a nonzero interaction indicates a difference between standardized estimator task contrasts, not equality or disagreement of the raw endpoint units. This exploratory result cannot establish estimator equivalence, causal task effects, biological mechanism, temporal stationarity, or invariance to a different normalization/calibration rule.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(
    *,
    labels_path: Path,
    support_path: Path,
    output_root: Path,
    workers: int,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    recordings = extract_alpha_recordings(labels_path, support_path, workers=workers)
    common_recordings = recordings[recordings["common_estimator_support"]]
    calibrations = {
        metric_id: robust_location_scale(common_recordings[f"{metric_id}_median"])
        for metric_id in ALPHA_METRIC_IDS
    }
    recordings.to_csv(output_root / "interaction_run_level.csv", index=False)
    subjects = subject_task_table(recordings, calibrations)
    subjects.to_csv(output_root / "interaction_subject_task.csv", index=False)
    pairs = interaction_pairs(subjects)
    pairs.to_csv(output_root / "interaction_pairs.csv", index=False)
    results = interaction_results(pairs)
    results.to_csv(output_root / "interaction_results.csv", index=False)
    missingness = missingness_table(recordings, subjects, pairs)
    missingness.to_csv(output_root / "interaction_missingness.csv", index=False)
    write_report(output_root / "interaction_report.md", results, recordings, subjects, calibrations)

    manifest = {
        "schema": "ds004511_ndt_v1.estimator_task_interaction.v1",
        "analysis_id": ANALYSIS_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_status": "no_biological_claim",
        "scientific_qualification": "exploratory_method_limited",
        "confirmatory_contrasts": False,
        "estimators": list(ALPHA_METRIC_IDS),
        "interaction_estimand": "standardized_chart_task_contrast_minus_standardized_one_step_l3_task_contrast",
        "standardization": {
            "calibration_unit": "recording_level",
            "scope": "all finite common-estimator-supported recordings, before task contrasts",
            "center": "pooled_median",
            "primary_scale": "1.4826*MAD",
            "fallbacks": ["IQR/1.3489795", "sample_SD"],
            "outcome_blind": True,
        },
        "primary_test": "two-sided Wilcoxon signed-rank on subject-level interaction differences",
        "primary_bh_family": "three task contrasts only; separate exploratory family",
        "secondary_test": "paired sign-flip permutation of mean interaction",
        "permutation_n": PERMUTATION_N,
        "permutation_seed": PERMUTATION_SEED,
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "n_recordings": int(len(recordings)),
        "n_subjects": int(recordings["subject_id"].nunique()),
        "n_results": int(len(results)),
        "n_recording_common_estimator_support": int(recordings["common_estimator_support"].sum()),
        "n_subject_task_common_estimator_support": int(subjects["common_estimator_support"].sum()),
        "production_measurements_changed": False,
        "typst_files_changed": False,
        "no_refit_interpolation_or_zero_fill": True,
        "input_sha256": {
            "labels": sha256_file(labels_path),
            "support": sha256_file(support_path),
            "script": sha256_file(Path(__file__).resolve()),
        },
        "calibration": calibrations,
        "note": "Common support is recording/subject-task support under production gates; chart and L3 temporal series are not pointwise aligned.",
    }
    write_json(output_root / "interaction_manifest.json", json_safe(manifest))
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
    print(
        json.dumps(
            {
                "output_root": str(args.output_root),
                "n_recordings": manifest["n_recordings"],
                "n_recording_common_estimator_support": manifest["n_recording_common_estimator_support"],
                "n_results": manifest["n_results"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
