"""COMA-PRED-INC-L1-001: incremental value of frozen L1 over clinical+qEEG (sl_017).

Uses the exact previously frozen restricted clinical + qEEG block from the
coma incremental-validity analysis. qEEG is joined from the part1 timeline
export because conventional_eeg is absent from the 3.0.1 H5 dump. Part2
timeline and part2 H5 are not opened.

Same folds for every model. Primary estimand is Delta AUROC of
M1 = clinical+qEEG+L1 versus M0 = clinical+qEEG, with paired subject-level
bootstrap on mean OOF probabilities. No L1 feature reselection.
"""
from __future__ import annotations

import argparse
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut, RepeatedStratifiedKFold
from sklearn.preprocessing import StandardScaler

from icare_v2_common import ARTICLE_DIR, add_common_args, resolve_pipeline_config, write_csv, write_json
from icare_v2_v301_pred_l1_part1 import (
    BOOT_N,
    BOOT_SEED,
    CORE,
    CV_REPEATS,
    CV_SEED,
    CV_SPLITS,
    EPS,
    RIDGE_C,
    _bootstrap_ci,
    _bootstrap_delta,
    _metrics,
    _ridge,
)

PART1_TIMELINE = (
    ARTICLE_DIR.parent
    / "comatose_ndt"
    / "results"
    / "timeline_analysis_20260606_part1_invalidityfix_primary12h"
    / "patient_timebin_summaries.csv"
)
EEG_COLS = (
    "rawfeat_eeg_delta_median",
    "rawfeat_eeg_theta_median",
    "rawfeat_eeg_alpha_median",
    "rawfeat_eeg_beta_median",
    "rawfeat_eeg_gamma_median",
    "rawfeat_eeg_highfreq_power_30_45_median",
    "rawfeat_eeg_alpha_theta_median",
    "rawfeat_eeg_beta_alpha_median",
    "rawfeat_eeg_hjorth_mobility_median",
    "rawfeat_eeg_hjorth_complexity_median",
    "rawfeat_eeg_permutation_entropy_median",
    "rawfeat_eeg_sample_entropy_median",
)
CLINICAL_NUM = ("age", "rosc_minutes", "ttm_celsius", "channel_count_median", "channel_coverage_frac_median")
CLINICAL_BOOL = ("shockable_rhythm", "ohca")
FROZEN_CLINICAL_QEEG = (
    "cat__hospital_A",
    "cat__hospital_B",
    "cat__hospital_D",
    "cat__hospital_E",
    "cat__hospital_F",
    "cat__sex_Female",
    "cat__sex_Male",
    "clinical__age",
    "clinical__channel_count_median",
    "clinical__channel_coverage_frac_median",
    "clinical__ohca",
    "clinical__rosc_minutes",
    "clinical__shockable_rhythm",
    "clinical__ttm_celsius",
    "eeg__rawfeat_eeg_alpha_median",
    "eeg__rawfeat_eeg_alpha_theta_median",
    "eeg__rawfeat_eeg_beta_alpha_median",
    "eeg__rawfeat_eeg_beta_median",
    "eeg__rawfeat_eeg_delta_median",
    "eeg__rawfeat_eeg_gamma_median",
    "eeg__rawfeat_eeg_highfreq_power_30_45_median",
    "eeg__rawfeat_eeg_hjorth_complexity_median",
    "eeg__rawfeat_eeg_hjorth_mobility_median",
    "eeg__rawfeat_eeg_permutation_entropy_median",
    "eeg__rawfeat_eeg_sample_entropy_median",
    "eeg__rawfeat_eeg_theta_median",
)
HOSPITAL_DUMMY = tuple(name for name in FROZEN_CLINICAL_QEEG if name.startswith("cat__hospital_"))


def _bool01(series: pd.Series) -> pd.Series:
    mapping = {"true": 1.0, "false": 0.0, "1": 1.0, "0": 0.0, "yes": 1.0, "no": 0.0}
    mapped = series.astype(str).str.strip().str.lower().map(mapping)
    numeric = pd.to_numeric(series, errors="coerce")
    return mapped.fillna(numeric)


def _load_clinical_qeeg(subjects: list[str]) -> pd.DataFrame:
    # FROZEN AS RUN for COMA-PRED-INC-L1-001. Numeric/bool columns keep the
    # filtered timeline index while `out` is RangeIndex, so most values become
    # NaN and are median-imputed. See m0_shockable_audit.md. Do not silent-patch.
    raw = pd.read_csv(PART1_TIMELINE)
    raw = raw[raw["time_bin"] == "0_12h"].copy()
    raw["subject_id"] = raw["subject"].astype(str)
    raw = raw[raw["subject_id"].isin(subjects)].copy()
    out = pd.DataFrame({"subject_id": raw["subject_id"].to_numpy(), "hospital": raw["hospital"].astype(str).to_numpy()})
    for col in CLINICAL_NUM:
        out[f"clinical__{col}"] = pd.to_numeric(raw[col], errors="coerce")
    for col in CLINICAL_BOOL:
        out[f"clinical__{col}"] = _bool01(raw[col])
    sex = pd.get_dummies(raw["sex"].fillna("missing").astype(str), prefix="cat__sex", dtype=float)
    hosp = pd.get_dummies(raw["hospital"].fillna("missing").astype(str), prefix="cat__hospital", dtype=float)
    for col in EEG_COLS:
        out[f"eeg__{col}"] = pd.to_numeric(raw[col], errors="coerce")
    out = pd.concat([out.reset_index(drop=True), sex.reset_index(drop=True), hosp.reset_index(drop=True)], axis=1)
    for col in FROZEN_CLINICAL_QEEG:
        if col not in out.columns:
            out[col] = 0.0
    return out


def _splits(y: np.ndarray) -> list[tuple[np.ndarray, np.ndarray]]:
    n_splits = min(CV_SPLITS, int(np.bincount(y).min()))
    cv = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=CV_REPEATS, random_state=CV_SEED)
    dummy = np.zeros((len(y), 1))
    return list(cv.split(dummy, y))


def _prepare_block(train: np.ndarray, test: np.ndarray, *, log_mask: np.ndarray | None, impute: bool) -> tuple[np.ndarray, np.ndarray]:
    tr = np.array(train, dtype=float, copy=True)
    te = np.array(test, dtype=float, copy=True)
    if impute:
        imputer = SimpleImputer(strategy="median")
        tr = imputer.fit_transform(tr)
        te = imputer.transform(te)
    if log_mask is not None and log_mask.any():
        tr[:, log_mask] = np.log(np.clip(tr[:, log_mask], 0.0, None) + EPS)
        te[:, log_mask] = np.log(np.clip(te[:, log_mask], 0.0, None) + EPS)
    return tr, te


def _oof_from_splits(
    blocks: list[tuple[np.ndarray, np.ndarray | None, bool]],
    y: np.ndarray,
    splits: list[tuple[np.ndarray, np.ndarray]],
) -> np.ndarray:
    total = np.zeros(len(y), dtype=float)
    count = np.zeros(len(y), dtype=float)
    for train_idx, test_idx in splits:
        pieces_tr = []
        pieces_te = []
        for x, log_mask, impute in blocks:
            tr, te = _prepare_block(x[train_idx], x[test_idx], log_mask=log_mask, impute=impute)
            pieces_tr.append(tr)
            pieces_te.append(te)
        train_x = np.column_stack(pieces_tr)
        test_x = np.column_stack(pieces_te)
        scaler = StandardScaler()
        train_z = scaler.fit_transform(train_x)
        test_z = scaler.transform(test_x)
        model = _ridge()
        model.fit(train_z, y[train_idx])
        total[test_idx] += model.predict_proba(test_z)[:, 1]
        count[test_idx] += 1.0
    out = np.full(len(y), np.nan)
    ok = count > 0
    out[ok] = total[ok] / count[ok]
    return out


def _loho(
    blocks: list[tuple[np.ndarray, np.ndarray | None, bool]],
    y: np.ndarray,
    groups: np.ndarray,
) -> np.ndarray:
    oof = np.full(len(y), np.nan)
    for train_idx, test_idx in LeaveOneGroupOut().split(np.zeros((len(y), 1)), y, groups):
        if len(np.unique(y[train_idx])) < 2:
            continue
        pieces_tr = []
        pieces_te = []
        for x, log_mask, impute in blocks:
            tr, te = _prepare_block(x[train_idx], x[test_idx], log_mask=log_mask, impute=impute)
            pieces_tr.append(tr)
            pieces_te.append(te)
        scaler = StandardScaler()
        model = _ridge()
        model.fit(scaler.fit_transform(np.column_stack(pieces_tr)), y[train_idx])
        oof[test_idx] = model.predict_proba(scaler.transform(np.column_stack(pieces_te)))[:, 1]
    return oof


def _delta_scores(y: np.ndarray, p0: np.ndarray, p1: np.ndarray) -> dict[str, float]:
    auc = _bootstrap_delta(y, p0, p1)
    m0 = _metrics(y, p0)
    m1 = _metrics(y, p1)
    rng = np.random.default_rng(BOOT_SEED)
    mask = np.isfinite(p0) & np.isfinite(p1)
    yy, a, b = y[mask], p0[mask], p1[mask]
    brier_boot = []
    auprc_boot = []
    n = yy.size
    for _ in range(BOOT_N):
        idx = rng.integers(0, n, n)
        if len(np.unique(yy[idx])) < 2:
            continue
        brier_boot.append(float(brier_score_loss(yy[idx], b[idx]) - brier_score_loss(yy[idx], a[idx])))
        auprc_boot.append(float(average_precision_score(yy[idx], b[idx]) - average_precision_score(yy[idx], a[idx])))
    brier_arr = np.asarray(brier_boot, dtype=float)
    auprc_arr = np.asarray(auprc_boot, dtype=float)
    return {
        "auc_m0": m0["auroc"],
        "auc_m1": m1["auroc"],
        "delta_auc": auc["delta_auroc"],
        "delta_auc_ci_lo": auc["ci_lo"],
        "delta_auc_ci_hi": auc["ci_hi"],
        "auprc_m0": m0["auprc"],
        "auprc_m1": m1["auprc"],
        "delta_auprc": float(m1["auprc"] - m0["auprc"]),
        "delta_auprc_ci_lo": float(np.percentile(auprc_arr, 2.5)) if auprc_arr.size else float("nan"),
        "delta_auprc_ci_hi": float(np.percentile(auprc_arr, 97.5)) if auprc_arr.size else float("nan"),
        "brier_m0": m0["brier"],
        "brier_m1": m1["brier"],
        "delta_brier": float(m1["brier"] - m0["brier"]),
        "delta_brier_ci_lo": float(np.percentile(brier_arr, 2.5)) if brier_arr.size else float("nan"),
        "delta_brier_ci_hi": float(np.percentile(brier_arr, 97.5)) if brier_arr.size else float("nan"),
        "n": m0["n"],
        "n_cpc1": m0["n_cpc1"],
        "n_cpc5": m0["n_cpc5"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    if not PART1_TIMELINE.is_file():
        raise FileNotFoundError(f"part1 timeline not found: {PART1_TIMELINE}")
    ddc = pd.read_csv(cfg.output_dir / "ddc_patient_primary.csv")
    ht = pd.read_csv(cfg.output_dir / "htilde_patient_primary.csv")[["subject_id", "h_tilde_cohort_reknn_median"]]
    l1 = ddc.merge(ht, on="subject_id", how="inner")
    l1 = l1[l1["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    for _, src, _ in CORE:
        l1[src] = pd.to_numeric(l1[src], errors="coerce")
    l1 = l1.dropna(subset=[src for _, src, _ in CORE]).reset_index(drop=True)
    clin = _load_clinical_qeeg(l1["subject_id"].astype(str).tolist())
    frame = l1.merge(clin, on="subject_id", how="inner")
    if "hospital_y" in frame.columns:
        frame["hospital"] = frame["hospital_y"]
    y = (frame["contrast_group"] == cfg.good_label).to_numpy(dtype=int)
    groups = frame["hospital"].fillna("missing").astype(str).to_numpy()
    subjects = frame["subject_id"].astype(str).to_numpy()
    x_l1 = np.column_stack([frame[src].to_numpy(dtype=float) for _, src, _ in CORE])
    x_tr = frame["tr_a_median"].to_numpy(dtype=float).reshape(-1, 1)
    x_clin = frame.loc[:, list(FROZEN_CLINICAL_QEEG)].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    x_clin_noso = frame.loc[:, [c for c in FROZEN_CLINICAL_QEEG if c not in HOSPITAL_DUMMY]].apply(
        pd.to_numeric, errors="coerce"
    ).to_numpy(dtype=float)
    log_l1 = np.array([log for _, _, log in CORE], dtype=bool)
    log_tr = np.array([True], dtype=bool)
    splits = _splits(y)

    models = {
        "tr_a_alone": [(x_tr, log_tr, False)],
        "l1_four": [(x_l1, log_l1, False)],
        "clinical_qeeg": [(x_clin, None, True)],
        "clinical_qeeg_plus_l1": [(x_clin, None, True), (x_l1, log_l1, False)],
    }
    oof = {name: _oof_from_splits(blocks, y, splits) for name, blocks in models.items()}
    loho_blocks = {
        "clinical_qeeg": [(x_clin_noso, None, True)],
        "clinical_qeeg_plus_l1": [(x_clin_noso, None, True), (x_l1, log_l1, False)],
        "l1_four": [(x_l1, log_l1, False)],
        "tr_a_alone": [(x_tr, log_tr, False)],
    }
    loho = {name: _loho(blocks, y, groups) for name, blocks in loho_blocks.items()}

    rows = []
    for name in ("tr_a_alone", "l1_four", "clinical_qeeg", "clinical_qeeg_plus_l1"):
        met = _metrics(y, oof[name])
        lo, hi, nboot = _bootstrap_ci(y, oof[name])
        loho_met = _metrics(y, loho[name])
        rows.append(
            {
                "model": name,
                **met,
                "auroc_ci_lo": lo,
                "auroc_ci_hi": hi,
                "n_boot": nboot,
                "loho_auroc": loho_met["auroc"],
            }
        )
    summary = pd.DataFrame(rows)
    delta = _delta_scores(y, oof["clinical_qeeg"], oof["clinical_qeeg_plus_l1"])
    delta_tr = _delta_scores(y, oof["tr_a_alone"], oof["l1_four"])
    preds = pd.DataFrame(
        {
            "subject_id": subjects,
            "contrast_group": np.where(y == 1, cfg.good_label, cfg.poor_label),
            "hospital": groups,
            **{f"oof_{name}": oof[name] for name in models},
        }
    )
    out = cfg.output_dir
    lock = {
        "experiment": "COMA-PRED-INC-L1-001",
        "part2_opened": False,
        "timeline": str(PART1_TIMELINE),
        "clinical_qeeg_features": list(FROZEN_CLINICAL_QEEG),
        "l1_features": [name for name, _, _ in CORE],
        "cv_seed": CV_SEED,
        "oof_aggregation": "mean_probability_per_subject_then_auroc",
        "same_folds": True,
        "loso_drops_hospital_dummies": True,
        "no_l1_reselection": True,
        "C": RIDGE_C,
        "prediction_branch_frozen_after_this": True,
    }
    write_json(out / "l1_pred_inc_lock.json", lock)
    write_json(out / "l1_pred_inc_delta.json", {"m1_minus_m0": delta, "l1_minus_tr_a": delta_tr})
    write_csv(out / "l1_pred_inc_summary.csv", summary)
    write_csv(out / "l1_pred_inc_oof.csv", preds)
    lines = [
        "# COMA-PRED-INC-L1-001 part1 (sl_017)",
        "",
        "Does frozen L1 add anything beyond the previously frozen restricted clinical+qEEG block?",
        "Part2 is not opened. No L1 feature reselection. Same folds for every model.",
        "qEEG joined from part1 timeline export; conventional_eeg is absent from the 3.0.1 dump.",
        "",
        "## Models (same 0-12h subjects)",
        "",
        "| Model | n | OOF AUROC | CI | AUPRC | Brier | LOSO AUROC |",
        "| --- | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| `{row['model']}` | {int(row['n'])} | {row['auroc']:.3f} | "
            f"[{row['auroc_ci_lo']:.3f}, {row['auroc_ci_hi']:.3f}] | "
            f"{row['auprc']:.3f} | {row['brier']:.3f} | {row['loho_auroc']:.3f} |"
        )
    lines += [
        "",
        "## Primary: Delta AUC (clinical+qEEG+L1 minus clinical+qEEG)",
        "",
        f"- n = {int(delta['n'])} ({int(delta['n_cpc1'])} CPC1, {int(delta['n_cpc5'])} CPC5)",
        f"- AUC(M0) = {delta['auc_m0']:.3f}",
        f"- AUC(M1) = {delta['auc_m1']:.3f}",
        f"- Delta AUC = {delta['delta_auc']:.3f} [{delta['delta_auc_ci_lo']:.3f}, {delta['delta_auc_ci_hi']:.3f}]",
        f"- Delta AUPRC = {delta['delta_auprc']:.3f} [{delta['delta_auprc_ci_lo']:.3f}, {delta['delta_auprc_ci_hi']:.3f}]",
        f"- Delta Brier = {delta['delta_brier']:.3f} [{delta['delta_brier_ci_lo']:.3f}, {delta['delta_brier_ci_hi']:.3f}] (negative is better)",
        "",
        "## Frozen geometry-only comparison on the same rows",
        "",
        f"- Tr(a) alone vs four-axis Delta AUC = {delta_tr['delta_auc']:.3f} [{delta_tr['delta_auc_ci_lo']:.3f}, {delta_tr['delta_auc_ci_hi']:.3f}]",
        "",
        "Manuscript 0.599 was pooled part1+part2 (n=281) with fold-mean AUROC and is not the M0 number here.",
        "Prediction branch is frozen after this experiment. Do not open part2 from these numbers.",
        "",
    ]
    (out / "l1_pred_inc_part1.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out / 'l1_pred_inc_part1.md'}", flush=True)
    print(summary[["model", "n", "auroc", "loho_auroc"]].to_string(index=False), flush=True)
    print(f"delta AUC {delta['delta_auc']:.3f} [{delta['delta_auc_ci_lo']:.3f}, {delta['delta_auc_ci_hi']:.3f}]", flush=True)


if __name__ == "__main__":
    main()
