"""COMA-PRED-L1-001: frozen four-axis ridge logistic on part1 (sl_015).

Prespecified before combination search. Geometry-only. Part2 stays sealed.
Transforms (log of the three positive quantities, z-score) happen inside
training folds. Repeated 5x20 CV averages each subject's out-of-fold
probabilities before one patient-level AUROC.

Secondary model COMA-PRED-L1-STAB adds log MAD(G90) and log MAD(R_b/a).
Delta AUC is evaluated on the same complete-case intersection. STAB does
not become the primary model if its part1 AUC is higher.
"""
from __future__ import annotations

import argparse
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut, RepeatedStratifiedKFold
from sklearn.preprocessing import StandardScaler

from icare_v2_common import add_common_args, resolve_pipeline_config, write_csv, write_json

EPS = 1e-12
CV_SPLITS = 5
CV_REPEATS = 20
CV_SEED = 20260912
BOOT_N = 2000
BOOT_SEED = 20260912
RIDGE_C = 1.0
SUSPICIOUS_AUC = 0.80

# Frozen before seeing combination AUCs. Entirely cohort-anchored.
CORE = (
    ("h_tilde", "h_tilde_cohort_reknn_median", False),
    ("log_tr_a", "tr_a_median", True),
    ("log_r_ba", "r_ba_median", True),
    ("log_g90", "g90_cohort_reknn_median", True),
)
STAB_EXTRA = (
    ("log_mad_g90", "g90_cohort_reknn_median_mad", True),
    ("log_mad_rba", "r_ba_median_mad", True),
)
MISSING_RULE = "complete_case_finite_features"


def _lock_payload() -> dict[str, Any]:
    return {
        "experiment": "COMA-PRED-L1-001",
        "secondary": "COMA-PRED-L1-STAB",
        "part2_opened": False,
        "frame": "cohort_anchored",
        "window": "0_12h",
        "model": "ridge_logistic",
        "penalty": "l2",
        "C": RIDGE_C,
        "class_weight": "balanced",
        "solver": "lbfgs",
        "cv_splits": CV_SPLITS,
        "cv_repeats": CV_REPEATS,
        "cv_seed": CV_SEED,
        "oof_aggregation": "mean_probability_per_subject_then_auroc",
        "missing_value_rule": MISSING_RULE,
        "core_features": [
            {"name": name, "source": src, "log": log} for name, src, log in CORE
        ],
        "stab_extra_features": [
            {"name": name, "source": src, "log": log} for name, src, log in STAB_EXTRA
        ],
        "not_included": ["d_eff", "b_norm", "F_perp", "g_op", "Family_B", "A_dom"],
        "clinical_qeeg": "not_in_this_run",
        "suspicious_auc_flag": SUSPICIOUS_AUC,
    }


def _ridge() -> LogisticRegression:
    # Default penalty is L2; C=1.0 is the frozen ridge strength.
    return LogisticRegression(
        C=RIDGE_C,
        solver="lbfgs",
        class_weight="balanced",
        max_iter=2000,
        random_state=CV_SEED,
    )


def _log_mask(spec: tuple[tuple[str, str, bool], ...]) -> np.ndarray:
    return np.array([log for _, _, log in spec], dtype=bool)


def _transform(train: np.ndarray, test: np.ndarray, log_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    train_x = np.array(train, dtype=float, copy=True)
    test_x = np.array(test, dtype=float, copy=True)
    if log_mask.any():
        train_x[:, log_mask] = np.log(np.clip(train_x[:, log_mask], 0.0, None) + EPS)
        test_x[:, log_mask] = np.log(np.clip(test_x[:, log_mask], 0.0, None) + EPS)
    scaler = StandardScaler()
    train_z = scaler.fit_transform(train_x)
    test_z = scaler.transform(test_x)
    return train_z, test_z, scaler


def _repeated_oof(x: np.ndarray, y: np.ndarray, log_mask: np.ndarray) -> np.ndarray:
    n_splits = min(CV_SPLITS, int(np.bincount(y).min()))
    if n_splits < 2:
        return np.full(len(y), np.nan)
    cv = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=CV_REPEATS, random_state=CV_SEED)
    total = np.zeros(len(y), dtype=float)
    count = np.zeros(len(y), dtype=float)
    for train_idx, test_idx in cv.split(x, y):
        train_z, test_z, _ = _transform(x[train_idx], x[test_idx], log_mask)
        model = _ridge()
        model.fit(train_z, y[train_idx])
        total[test_idx] += model.predict_proba(test_z)[:, 1]
        count[test_idx] += 1.0
    out = np.full(len(y), np.nan)
    ok = count > 0
    out[ok] = total[ok] / count[ok]
    return out


def _loho_oof(x: np.ndarray, y: np.ndarray, groups: np.ndarray, log_mask: np.ndarray) -> tuple[np.ndarray, pd.DataFrame]:
    logo = LeaveOneGroupOut()
    oof = np.full(len(y), np.nan)
    rows = []
    for train_idx, test_idx in logo.split(x, y, groups):
        hospital = str(groups[test_idx][0])
        if len(np.unique(y[train_idx])) < 2:
            rows.append({"hospital": hospital, "n": int(len(test_idx)), "auroc": float("nan"), "skipped": True})
            continue
        train_z, test_z, _ = _transform(x[train_idx], x[test_idx], log_mask)
        model = _ridge()
        model.fit(train_z, y[train_idx])
        prob = model.predict_proba(test_z)[:, 1]
        oof[test_idx] = prob
        auroc = float("nan")
        if len(np.unique(y[test_idx])) >= 2:
            auroc = float(roc_auc_score(y[test_idx], prob))
        rows.append({"hospital": hospital, "n": int(len(test_idx)), "n_cpc1": int(y[test_idx].sum()), "auroc": auroc, "skipped": False})
    return oof, pd.DataFrame(rows)


def _metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    mask = np.isfinite(p)
    yy = y[mask]
    pp = p[mask]
    out = {
        "n": int(mask.sum()),
        "n_cpc1": int(yy.sum()),
        "n_cpc5": int((yy == 0).sum()),
        "auroc": float("nan"),
        "auprc": float("nan"),
        "brier": float("nan"),
        "prevalence": float(yy.mean()) if yy.size else float("nan"),
    }
    if yy.size and len(np.unique(yy)) >= 2:
        out["auroc"] = float(roc_auc_score(yy, pp))
        out["auprc"] = float(average_precision_score(yy, pp))
        out["brier"] = float(brier_score_loss(yy, pp))
    return out


def _bootstrap_ci(y: np.ndarray, p: np.ndarray) -> tuple[float, float, int]:
    rng = np.random.default_rng(BOOT_SEED)
    mask = np.isfinite(p)
    yy = y[mask]
    pp = p[mask]
    n = yy.size
    if n < 4:
        return float("nan"), float("nan"), 0
    stats_boot = []
    for _ in range(BOOT_N):
        idx = rng.integers(0, n, n)
        if len(np.unique(yy[idx])) < 2:
            continue
        stats_boot.append(float(roc_auc_score(yy[idx], pp[idx])))
    arr = np.asarray(stats_boot, dtype=float)
    if arr.size < max(50, int(0.5 * BOOT_N)):
        return float("nan"), float("nan"), int(arr.size)
    return float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5)), int(arr.size)


def _bootstrap_delta(y: np.ndarray, p_core: np.ndarray, p_stab: np.ndarray) -> dict[str, float]:
    rng = np.random.default_rng(BOOT_SEED)
    mask = np.isfinite(p_core) & np.isfinite(p_stab)
    yy = y[mask]
    a = p_core[mask]
    b = p_stab[mask]
    n = yy.size
    out = {"delta_auroc": float("nan"), "ci_lo": float("nan"), "ci_hi": float("nan"), "n_boot": 0}
    if n < 4 or len(np.unique(yy)) < 2:
        return out
    out["delta_auroc"] = float(roc_auc_score(yy, b) - roc_auc_score(yy, a))
    stats_boot = []
    for _ in range(BOOT_N):
        idx = rng.integers(0, n, n)
        if len(np.unique(yy[idx])) < 2:
            continue
        stats_boot.append(float(roc_auc_score(yy[idx], b[idx]) - roc_auc_score(yy[idx], a[idx])))
    arr = np.asarray(stats_boot, dtype=float)
    out["n_boot"] = int(arr.size)
    if arr.size >= max(50, int(0.5 * BOOT_N)):
        out["ci_lo"] = float(np.percentile(arr, 2.5))
        out["ci_hi"] = float(np.percentile(arr, 97.5))
    return out


def _fit_full(x: np.ndarray, y: np.ndarray, spec: tuple[tuple[str, str, bool], ...]) -> dict[str, Any]:
    log_mask = _log_mask(spec)
    dummy_test = np.array(x, dtype=float, copy=True)
    train_z, _, scaler = _transform(x, dummy_test, log_mask)
    model = _ridge()
    model.fit(train_z, y)
    names = [name for name, _, _ in spec]
    return {
        "feature_order": names,
        "log_mask": [bool(v) for v in log_mask],
        "scaler_mean": [float(v) for v in scaler.mean_],
        "scaler_scale": [float(v) for v in scaler.scale_],
        "coefficients": {name: float(coef) for name, coef in zip(names, model.coef_.ravel())},
        "intercept": float(model.intercept_.ravel()[0]),
        "penalty": "l2",
        "C": RIDGE_C,
        "missing_value_rule": MISSING_RULE,
        "part2_opened": False,
        "n_subjects": int(len(y)),
        "n_cpc1": int(y.sum()),
        "n_cpc5": int((y == 0).sum()),
    }


def _assemble(cfg) -> pd.DataFrame:
    ddc = pd.read_csv(cfg.output_dir / "ddc_patient_primary.csv")
    ht = pd.read_csv(cfg.output_dir / "htilde_patient_primary.csv")[
        ["subject_id", "h_tilde_cohort_reknn_median"]
    ]
    stab = pd.read_csv(cfg.output_dir / "stab_adj_patient.csv")[
        ["subject_id", "g90_cohort_reknn_median_mad", "r_ba_median_mad"]
    ]
    frame = ddc.merge(ht, on="subject_id", how="inner").merge(stab, on="subject_id", how="left")
    return frame[frame["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()


def _complete(frame: pd.DataFrame, spec: tuple[tuple[str, str, bool], ...]) -> pd.DataFrame:
    cols = [src for _, src, _ in spec]
    work = frame.copy()
    for col in cols:
        work[col] = pd.to_numeric(work[col], errors="coerce")
    return work.dropna(subset=cols).reset_index(drop=True)


def _xy(frame: pd.DataFrame, spec: tuple[tuple[str, str, bool], ...], cfg) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    x = np.column_stack([pd.to_numeric(frame[src], errors="coerce").to_numpy(dtype=float) for _, src, _ in spec])
    y = (frame["contrast_group"] == cfg.good_label).to_numpy(dtype=int)
    groups = frame["hospital"].fillna("missing").astype(str).to_numpy()
    subjects = frame["subject_id"].astype(str).to_numpy()
    return x, y, groups, subjects


def _univariate_direct(frame: pd.DataFrame, spec: tuple[tuple[str, str, bool], ...], cfg) -> pd.DataFrame:
    rows = []
    for name, src, _ in spec:
        good = pd.to_numeric(frame.loc[frame["contrast_group"] == cfg.good_label, src], errors="coerce").to_numpy(dtype=float)
        poor = pd.to_numeric(frame.loc[frame["contrast_group"] == cfg.poor_label, src], errors="coerce").to_numpy(dtype=float)
        good = good[np.isfinite(good)]
        poor = poor[np.isfinite(poor)]
        auroc = float("nan")
        if good.size and poor.size:
            y = np.concatenate([np.ones(good.size), np.zeros(poor.size)])
            score = np.concatenate([good, poor])
            auroc = float(roc_auc_score(y, score))
            flipped = float(roc_auc_score(y, -score))
            auroc = max(auroc, flipped)
        rows.append({"feature": name, "source": src, "n_cpc1": int(good.size), "n_cpc5": int(poor.size), "direct_auroc_max_direction": auroc})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    out = cfg.output_dir
    lock = _lock_payload()
    write_json(out / "l1_pred_lock.json", lock)

    frame = _assemble(cfg)
    core_frame = _complete(frame, CORE)
    stab_spec = CORE + STAB_EXTRA
    stab_frame = _complete(frame, stab_spec)

    core_x, core_y, core_g, core_subj = _xy(core_frame, CORE, cfg)
    core_log = _log_mask(CORE)
    core_oof = _repeated_oof(core_x, core_y, core_log)
    core_metrics = _metrics(core_y, core_oof)
    core_lo, core_hi, core_nb = _bootstrap_ci(core_y, core_oof)
    core_loho, core_hosp = _loho_oof(core_x, core_y, core_g, core_log)
    core_loho_metrics = _metrics(core_y, core_loho)
    core_fit = _fit_full(core_x, core_y, CORE)

    stab_x, stab_y, stab_g, stab_subj = _xy(stab_frame, stab_spec, cfg)
    stab_log = _log_mask(stab_spec)
    stab_oof = _repeated_oof(stab_x, stab_y, stab_log)
    # Core on the same STAB-complete rows for nested Delta AUC.
    core_on_stab_x = np.column_stack(
        [pd.to_numeric(stab_frame[src], errors="coerce").to_numpy(dtype=float) for _, src, _ in CORE]
    )
    core_on_stab_oof = _repeated_oof(core_on_stab_x, stab_y, core_log)
    stab_metrics = _metrics(stab_y, stab_oof)
    nested_core_metrics = _metrics(stab_y, core_on_stab_oof)
    delta = _bootstrap_delta(stab_y, core_on_stab_oof, stab_oof)
    stab_lo, stab_hi, stab_nb = _bootstrap_ci(stab_y, stab_oof)
    stab_loho, stab_hosp = _loho_oof(stab_x, stab_y, stab_g, stab_log)
    stab_loho_metrics = _metrics(stab_y, stab_loho)
    stab_fit = _fit_full(stab_x, stab_y, stab_spec)

    uni = _univariate_direct(core_frame, CORE, cfg)
    trans = np.array(core_x, dtype=float, copy=True)
    if core_log.any():
        trans[:, core_log] = np.log(np.clip(trans[:, core_log], 0.0, None) + EPS)
    corr = pd.DataFrame(trans, columns=[name for name, _, _ in CORE]).corr(method="spearman")

    core_pred = pd.DataFrame(
        {"subject_id": core_subj, "contrast_group": np.where(core_y == 1, cfg.good_label, cfg.poor_label), "hospital": core_g, "oof_p_cpc1": core_oof, "loho_p_cpc1": core_loho}
    )
    stab_pred = pd.DataFrame(
        {"subject_id": stab_subj, "contrast_group": np.where(stab_y == 1, cfg.good_label, cfg.poor_label), "hospital": stab_g, "oof_p_cpc1": stab_oof, "core_oof_on_same_rows": core_on_stab_oof, "loho_p_cpc1": stab_loho}
    )

    flag = bool(core_metrics["auroc"] >= SUSPICIOUS_AUC)
    summary = {
        "core": {**core_metrics, "auroc_ci_lo": core_lo, "auroc_ci_hi": core_hi, "n_boot": core_nb, "loho_auroc": core_loho_metrics["auroc"]},
        "stab": {**stab_metrics, "auroc_ci_lo": stab_lo, "auroc_ci_hi": stab_hi, "n_boot": stab_nb, "loho_auroc": stab_loho_metrics["auroc"]},
        "nested_core_on_stab_rows": nested_core_metrics,
        "delta_auc": delta,
        "suspicious_part1_auc": flag,
        "part2_opened": False,
    }
    write_json(out / "l1_pred_core_fit.json", core_fit)
    write_json(out / "l1_pred_stab_fit.json", stab_fit)
    write_json(out / "l1_pred_summary.json", summary)
    write_csv(out / "l1_pred_core_oof.csv", core_pred)
    write_csv(out / "l1_pred_stab_oof.csv", stab_pred)
    write_csv(out / "l1_pred_univariate_direct.csv", uni)
    write_csv(out / "l1_pred_core_spearman.csv", corr.reset_index())
    write_csv(out / "l1_pred_core_loho_hospitals.csv", core_hosp)
    write_csv(out / "l1_pred_stab_loho_hospitals.csv", stab_hosp)

    lines = [
        "# COMA-PRED-L1-001 part1 (sl_015)",
        "",
        "Geometry-only ridge logistic. Frozen four cohort-anchored axes.",
        "Part1 is model development / internal validation. Part2 is not opened.",
        "STAB is a prespecified extension; it does not replace the core model.",
        "",
        "## Core model",
        "",
        f"- n = {core_metrics['n']} ({core_metrics['n_cpc1']} CPC1, {core_metrics['n_cpc5']} CPC5)",
        f"- repeated 5x20 OOF AUROC = {core_metrics['auroc']:.3f} [{core_lo:.3f}, {core_hi:.3f}]",
        f"- AUPRC = {core_metrics['auprc']:.3f} (chance {core_metrics['prevalence']:.3f})",
        f"- Brier = {core_metrics['brier']:.3f}",
        f"- leave-one-hospital-out AUROC = {core_loho_metrics['auroc']:.3f}",
        f"- suspicious-AUC flag (>={SUSPICIOUS_AUC}): {flag}",
        "",
        "Illustrative independent-axes target from sl_015 was ~0.70-0.75, not an expected result.",
        "",
        "## COMA-PRED-L1-STAB (same-row nested comparison)",
        "",
        f"- n = {stab_metrics['n']} ({stab_metrics['n_cpc1']} CPC1, {stab_metrics['n_cpc5']} CPC5)",
        f"- core AUROC on those rows = {nested_core_metrics['auroc']:.3f}",
        f"- core+STAB AUROC = {stab_metrics['auroc']:.3f} [{stab_lo:.3f}, {stab_hi:.3f}]",
        f"- Delta AUC = {delta['delta_auroc']:.3f} [{delta['ci_lo']:.3f}, {delta['ci_hi']:.3f}]",
        f"- STAB LOSO AUROC = {stab_loho_metrics['auroc']:.3f}",
        "",
        "Full-part1 coefficients are saved for a future zero-refit part2 pass. They are not used here.",
        "",
        "## Univariate direct AUROC (not used for selection)",
        "",
        "| Feature | n CPC1 | n CPC5 | AUROC (max direction) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for _, row in uni.iterrows():
        lines.append(f"| `{row['feature']}` | {int(row['n_cpc1'])} | {int(row['n_cpc5'])} | {row['direct_auroc_max_direction']:.3f} |")
    lines += [
        "",
        "## Core Spearman (log-space for logged features)",
        "",
        corr.to_string(float_format=lambda v: f"{v:.2f}"),
        "",
        "## Leave-one-hospital-out (core)",
        "",
        "| Hospital | n | n CPC1 | AUROC |",
        "| --- | ---: | ---: | ---: |",
    ]
    for _, row in core_hosp.iterrows():
        auroc = row.get("auroc", float("nan"))
        auroc_s = "skipped" if row.get("skipped") or not np.isfinite(auroc) else f"{auroc:.3f}"
        n_cpc1 = row.get("n_cpc1", float("nan"))
        n_cpc1_s = "-" if not np.isfinite(n_cpc1) else str(int(n_cpc1))
        lines.append(f"| {row['hospital']} | {int(row['n'])} | {n_cpc1_s} | {auroc_s} |")
    lines += [
        "",
        f"Intercept {core_fit['intercept']:.3g}. Coefficients: "
        + ", ".join(f"{k}={v:.3g}" for k, v in core_fit["coefficients"].items())
        + ".",
        "",
    ]
    (out / "l1_pred_part1.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out / 'l1_pred_part1.md'}", flush=True)
    print(f"core AUROC {core_metrics['auroc']:.3f} [{core_lo:.3f}, {core_hi:.3f}] LOSO {core_loho_metrics['auroc']:.3f}", flush=True)
    print(f"delta AUC {delta['delta_auroc']:.3f} [{delta['ci_lo']:.3f}, {delta['ci_hi']:.3f}]", flush=True)


if __name__ == "__main__":
    main()
