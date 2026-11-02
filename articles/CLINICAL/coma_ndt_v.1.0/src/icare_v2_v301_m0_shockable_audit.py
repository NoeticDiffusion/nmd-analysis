"""Diagnostic audit of why M0 swamps shockable rhythm (sl_019).

Does not retune or replace M0. Does not open part2. Also writes the
frozen Tr(a)-alone part2 benchmark sidecar beside the existing four-axis
fit.
"""
from __future__ import annotations

import argparse
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from icare_v2_common import add_common_args, resolve_pipeline_config, write_csv, write_json
from icare_v2_v301_pred_inc_l1_part1 import (
    FROZEN_CLINICAL_QEEG,
    PART1_TIMELINE,
    _bool01,
    _load_clinical_qeeg,
    _oof_from_splits,
    _prepare_block,
    _splits,
)
from icare_v2_v301_pred_l1_part1 import CORE, _assemble, _complete, _fit_full, _metrics, _ridge

SHOCK = "clinical__shockable_rhythm"


def _direct_auroc(y: np.ndarray, x: np.ndarray) -> dict[str, float]:
    mask = np.isfinite(x)
    yy = y[mask]
    xx = x[mask]
    out = {"n": int(mask.sum()), "n_missing": int((~mask).sum()), "auroc": float("nan"), "auroc_flipped": float("nan")}
    if yy.size and len(np.unique(yy)) >= 2:
        out["auroc"] = float(roc_auc_score(yy, xx))
        out["auroc_flipped"] = float(roc_auc_score(yy, -xx))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    l1 = _complete(_assemble(cfg), CORE)
    clin = _load_clinical_qeeg(l1["subject_id"].astype(str).tolist())
    frame = l1.merge(clin, on="subject_id", how="inner")
    y = (frame["contrast_group"] == cfg.good_label).to_numpy(dtype=int)
    names = list(FROZEN_CLINICAL_QEEG)
    x = frame.loc[:, names].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    shock_idx = names.index(SHOCK)
    shock = x[:, shock_idx]
    polarity = _direct_auroc(y, shock)
    expected_sign = "+" if polarity["auroc"] >= polarity["auroc_flipped"] else "-"
    timeline = pd.read_csv(PART1_TIMELINE)
    timeline = timeline[timeline["time_bin"] == "0_12h"].copy()
    timeline["subject_id"] = timeline["subject"].astype(str)
    aligned = frame[["subject_id"]].merge(timeline[["subject_id", "shockable_rhythm"]], on="subject_id", how="left")
    aligned_shock = _bool01(aligned["shockable_rhythm"]).to_numpy(dtype=float)
    aligned_polarity = _direct_auroc(y, aligned_shock)
    splits = _splits(y)

    fold_rows = []
    for fold, (train_idx, test_idx) in enumerate(splits):
        tr_raw = x[train_idx]
        te_raw = x[test_idx]
        n_miss_tr = int(np.isnan(tr_raw[:, shock_idx]).sum())
        n_miss_te = int(np.isnan(te_raw[:, shock_idx]).sum())
        tr, te = _prepare_block(tr_raw, te_raw, log_mask=None, impute=True)
        scaler = StandardScaler()
        tr_z = scaler.fit_transform(tr)
        te_z = scaler.transform(te)
        model = _ridge()
        model.fit(tr_z, y[train_idx])
        coef = model.coef_.ravel()
        shock_coef = float(coef[shock_idx])
        abs_rank = int(1 + np.argsort(-np.abs(coef)).tolist().index(shock_idx))
        fold_auc = float("nan")
        if len(np.unique(y[test_idx])) >= 2:
            fold_auc = float(roc_auc_score(y[test_idx], model.predict_proba(te_z)[:, 1]))
        fold_rows.append(
            {
                "fold": fold,
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "shock_missing_train": n_miss_tr,
                "shock_missing_test": n_miss_te,
                "shock_train_mean_raw": float(np.nanmean(tr_raw[:, shock_idx])),
                "shock_scaler_mean": float(scaler.mean_[shock_idx]),
                "shock_scaler_scale": float(scaler.scale_[shock_idx]),
                "shock_coef": shock_coef,
                "shock_abs_rank": abs_rank,
                "shock_sign_matches_direct": bool(
                    (shock_coef > 0 and expected_sign == "+") or (shock_coef < 0 and expected_sign == "-")
                ),
                "max_abs_coef": float(np.max(np.abs(coef))),
                "mean_abs_coef": float(np.mean(np.abs(coef))),
                "fold_test_auroc": fold_auc,
            }
        )
    folds = pd.DataFrame(fold_rows)

    shock_oof = _oof_from_splits([(shock.reshape(-1, 1), None, True)], y, splits)
    m0_oof = _oof_from_splits([(x, None, True)], y, splits)
    shock_met = _metrics(y, shock_oof)
    m0_met = _metrics(y, m0_oof)

    imputer = SimpleImputer(strategy="median")
    x_imp = imputer.fit_transform(x)
    scaler = StandardScaler()
    z = scaler.fit_transform(x_imp)
    full = _ridge()
    full.fit(z, y)
    full_coef = pd.DataFrame(
        {
            "feature": names,
            "coef": full.coef_.ravel(),
            "abs_coef": np.abs(full.coef_.ravel()),
            "scaler_mean": scaler.mean_,
            "scaler_scale": scaler.scale_,
            "n_missing": np.isnan(x).sum(axis=0),
            "family": [
                "hospital"
                if n.startswith("cat__hospital_")
                else "sex"
                if n.startswith("cat__sex_")
                else "eeg"
                if n.startswith("eeg__")
                else "clinical"
                for n in names
            ],
        }
    ).sort_values("abs_coef", ascending=False)

    family = (
        full_coef.groupby("family", as_index=False)
        .agg(mean_abs_coef=("abs_coef", "mean"), max_abs_coef=("abs_coef", "max"), n=("feature", "size"))
        .sort_values("mean_abs_coef", ascending=False)
    )
    dummy_sex_sum = float(np.nanmean(x_imp[:, [names.index("cat__sex_Female"), names.index("cat__sex_Male")]].sum(axis=1)))
    hosp_idx = [i for i, n in enumerate(names) if n.startswith("cat__hospital_")]
    dummy_hosp_sum = float(np.nanmean(x_imp[:, hosp_idx].sum(axis=1)))

    index_bug = int(polarity["n_missing"]) >= 50 and int(aligned_polarity["n_missing"]) < 20
    if index_bug:
        verdict = "implementation_index_misalignment"
    elif polarity["auroc"] < 0.55 and polarity["auroc_flipped"] < 0.55:
        verdict = "shockable_signal_absent"
    elif not bool(folds["shock_sign_matches_direct"].mean() > 0.8):
        verdict = "possible_polarity_or_encoding_issue"
    elif shock_met["auroc"] < 0.60:
        verdict = "univariate_oof_also_weak_implementation_issue"
    elif m0_met["auroc"] >= shock_met["auroc"] - 0.03:
        verdict = "m0_preserves_shockable"
    else:
        verdict = "swamped_by_high_p_noisy_covariates"

    tr_spec = (("log_tr_a", "tr_a_median", True),)
    tr_x = frame[["tr_a_median"]].to_numpy(dtype=float)
    tr_y = y
    tr_fit = _fit_full(tr_x, tr_y, tr_spec)
    tr_fit["role"] = "part2_zero_refit_benchmark"
    tr_fit["primary_model"] = "four_axis_l1"
    write_json(cfg.output_dir / "l1_pred_tra_fit.json", tr_fit)
    write_json(
        cfg.output_dir / "l1_part2_zero_refit_lock.json",
        {
            "part2_opened": False,
            "primary": "l1_pred_core_fit.json",
            "benchmark": "l1_pred_tra_fit.json",
            "not_used": ["M1_clinical_qeeg_plus_l1", "STAB_extension"],
            "protocol": "zero_refit_on_sealed_part2",
        },
    )

    audit = {
        "m0_not_changed": True,
        "part2_opened": False,
        "shockable_direct_as_used_in_m0": polarity,
        "shockable_direct_index_aligned_diagnostic": aligned_polarity,
        "expected_coef_sign_for_P_CPC1": expected_sign,
        "shockable_missing_n": int(np.isnan(shock).sum()),
        "index_alignment_bug": bool(index_bug),
        "shockable_univariate_oof": shock_met,
        "m0_oof": m0_met,
        "fold_shock_coef_mean": float(folds["shock_coef"].mean()),
        "fold_shock_coef_min": float(folds["shock_coef"].min()),
        "fold_shock_coef_max": float(folds["shock_coef"].max()),
        "fold_sign_match_rate": float(folds["shock_sign_matches_direct"].mean()),
        "fold_mean_abs_rank": float(folds["shock_abs_rank"].mean()),
        "sex_dummy_row_sum": dummy_sex_sum,
        "hospital_dummy_row_sum": dummy_hosp_sum,
        "complete_dummy_trap": bool(abs(dummy_sex_sum - 1.0) < 1e-8 and abs(dummy_hosp_sum - 1.0) < 1e-8),
        "verdict": verdict,
    }
    out = cfg.output_dir
    write_csv(out / "m0_shockable_fold_audit.csv", folds)
    write_csv(out / "m0_full_coefficients.csv", full_coef)
    write_csv(out / "m0_coef_by_family.csv", family)
    write_json(out / "m0_shockable_audit.json", audit)

    lines = [
        "# M0 shockable-rhythm audit (sl_019)",
        "",
        "Diagnostic only. M0 is not changed. Part2 is not opened.",
        "",
        f"- M0-as-run shockable: n={polarity['n']}, missing={polarity['n_missing']}, direct AUROC={polarity['auroc']:.3f} (flipped {polarity['auroc_flipped']:.3f})",
        f"- index-aligned diagnostic (not a new M0): n={aligned_polarity['n']}, missing={aligned_polarity['n_missing']}, direct AUROC={aligned_polarity['auroc']:.3f}",
        f"- expected ridge sign for P(CPC1) from the *M0-as-run* column: {expected_sign}",
        f"- shockable-only OOF AUROC (diagnostic) = {shock_met['auroc']:.3f}",
        f"- frozen M0 OOF AUROC = {m0_met['auroc']:.3f}",
        f"- foldwise shockable coef: mean {audit['fold_shock_coef_mean']:.3f} [{audit['fold_shock_coef_min']:.3f}, {audit['fold_shock_coef_max']:.3f}]",
        f"- sign match vs direct polarity: {audit['fold_sign_match_rate']:.2%}",
        f"- mean |coef| rank of shockable among 26: {audit['fold_mean_abs_rank']:.1f}",
        f"- sex dummy row-sum = {dummy_sex_sum:.3f}; hospital dummy row-sum = {dummy_hosp_sum:.3f}",
        f"- complete dummy trap present: {audit['complete_dummy_trap']}",
        f"- verdict: `{verdict}`",
        "",
        "## Full-fit |coef| by family",
        "",
        "| Family | n | mean |coef| | max |coef| |",
        "| --- | ---: | ---: | ---: |",
    ]
    for _, row in family.iterrows():
        lines.append(f"| {row['family']} | {int(row['n'])} | {row['mean_abs_coef']:.3f} | {row['max_abs_coef']:.3f} |")
    lines += [
        "",
        "## Top full-fit coefficients",
        "",
        "| Feature | coef | |coef| | n missing |",
        "| --- | ---: | ---: | ---: |",
    ]
    for _, row in full_coef.head(8).iterrows():
        lines.append(f"| `{row['feature']}` | {row['coef']:.3f} | {row['abs_coef']:.3f} | {int(row['n_missing'])} |")
    lines += [
        "",
        "M0 is not repaired. The observed +0.138 is against this corrupted comparator.",
        "A correctly joined clinical+qEEG block would be a separate future analysis.",
        "",
    ]
    (out / "m0_shockable_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out / 'm0_shockable_audit.md'}", flush=True)
    print(f"verdict={verdict} shockable_oof={shock_met['auroc']:.3f} m0_oof={m0_met['auroc']:.3f}", flush=True)
    print(f"sign_match={audit['fold_sign_match_rate']:.2%} dummy_trap={audit['complete_dummy_trap']}", flush=True)


if __name__ == "__main__":
    main()
