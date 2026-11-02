"""COMA-RESID-001 on I-CARE part1 (sl_022). Part2 stays sealed.

Cross-fitted residual spread of lag-1 increments after an opposite-fold
kNN conditional mean. Not ingest transition_residual, not Family B, not
Ito. Missingness-by-CPC is reported before metric contrasts. Holm is only
across the new primary pair (tr_a_raw, tr_c_resid), not SL-004A.
"""
from __future__ import annotations

import argparse
import json
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
    parallel_map,
    parse_run_stem,
    participant_meta_from_handle,
    resolve_pipeline_config,
    time_reference_from_handle,
    write_csv,
    write_json,
)
from icare_v2_outcome_contrast_analysis import _contrast_row
from icare_v2_v301_l1_estimators import _segment_id
from icare_v2_v301_l1_panel import _annotate
from icare_v2_v301_l1_prepart2_gates import _holm
from icare_v2_v301_resid_metrics import estimate_crossfit_residual_spread

GATE_PATH = ARTICLE_DIR / "results" / "v3_0_1" / "resid_synthetic_gate.json"

PRIMARY = (
    ("tr_a_raw_median", "tr_a_raw", "CPC1 < CPC5"),
    ("tr_c_resid_median", "tr_c_resid", "CPC1 < CPC5"),
)
SECONDARY = (
    ("d_eff_resid_median", "d_eff_resid", "descriptive"),
    ("h_tilde_resid_median", "h_tilde_resid", "descriptive"),
)
DIAGNOSTIC = (
    ("tr_c_over_a_median", "tr_c_over_a", "descriptive ratio tr_c_resid/tr_a_raw"),
)


def extract_one(path: str) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "read_ok": False,
        "read_error": None,
        "resid_status": None,
        "resid_failure": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            timing = time_reference_from_handle(handle)
            row.update({k: meta[k] for k in ("cpc", "outcome", "hospital", "ttm", "age", "sex")})
            row.update(timing)
            if "/coords_3d_cohort_anchored/values" not in handle or "/time" not in handle:
                row["resid_status"] = "missing_chart"
                row["read_ok"] = True
                return row
            xc = np.asarray(handle["/coords_3d_cohort_anchored/values"][:], dtype=float)
            time = np.asarray(handle["/time"][:], dtype=float)
            raw = handle["/row_source/raw_file"][:] if "/row_source/raw_file" in handle else None
            result = estimate_crossfit_residual_spread(xc, time, segment_id=_segment_id(raw, xc.shape[0]))
            row["resid_status"] = result.get("status")
            row["resid_failure"] = result.get("failure_reason")
            row["resid_n_valid"] = result.get("n_valid")
            row["nominal_dt_sec"] = result.get("nominal_dt_sec")
            med = result.get("medians") or {}
            row["tr_a_raw_median"] = med.get("tr_a_raw", float("nan"))
            row["tr_c_resid_median"] = med.get("tr_c_resid", float("nan"))
            row["d_eff_resid_median"] = med.get("d_eff_resid", float("nan"))
            row["h_tilde_resid_median"] = med.get("h_tilde_resid", float("nan"))
            row["tr_c_over_a_median"] = med.get("tr_c_over_a", float("nan"))
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
    metrics = [
        "tr_a_raw_median",
        "tr_c_resid_median",
        "d_eff_resid_median",
        "h_tilde_resid_median",
        "tr_c_over_a_median",
    ]
    agg: dict[str, Any] = {
        "cpc": ("cpc", "first"),
        "contrast_group": ("contrast_group", "first"),
        "hospital": ("hospital", "first"),
        "n_runs": ("source_h5", "nunique"),
    }
    for metric in metrics:
        if metric in work.columns:
            agg[metric] = (metric, "median")
    return work.groupby("subject_id", as_index=False).agg(**agg)


def _require_gate() -> dict[str, Any]:
    if not GATE_PATH.is_file():
        raise SystemExit(f"synthetic gate missing: {GATE_PATH}. Run icare_v2_v301_resid_synthetic_gate.py first.")
    payload = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    if not bool(payload.get("pass")):
        raise SystemExit(f"synthetic gate FAILED: {GATE_PATH}. CPC contrasts not run.")
    return payload


def _render(*, cfg, missing: pd.DataFrame, contrasts: pd.DataFrame, n_runs: int, n_patients: int, gate: dict[str, Any]) -> str:
    lines = [
        "# COMA-RESID-001 part1 (sl_022)",
        "",
        f"Bundle `{cfg.bundle_id}`. Analysis-owned blocked crossfit residual spread on",
        "`coords_3d_cohort_anchored`. Not innovation. Not Ito. Not Family B.",
        "Not ingest `/transition_residuals/v1/primary/series/transition_residual`.",
        "Part2 is not opened. Holm is only across the two new primaries, not SL-004A.",
        "",
        f"Synthetic gate pass={gate.get('pass')} ({gate.get('n_checks')} checks).",
        f"Recordings extracted: {n_runs}. Patients in 0-12h CPC1/CPC5: {n_patients}.",
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
                f"{int(row['n_cpc1_finite'])}/{int(row['n_cpc1'])} ({100 * row['rate_cpc1']:.1f}%) | "
                f"{int(row['n_cpc5_finite'])}/{int(row['n_cpc5'])} ({100 * row['rate_cpc5']:.1f}%) | "
                f"{row['fisher_p']:.3g} |"
            )
    lines += [
        "",
        "## Contrasts (0-12h subject median)",
        "",
        "| Family | Hypothesis | Metric | Prediction | n CPC1 | n CPC5 | CPC1 med | CPC5 med | d | MW p | Holm p |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    if contrasts.empty:
        lines.append("| - | - | - | - | - | - | - | - | - | - | - |")
    else:
        for _, row in contrasts.iterrows():
            holm = row.get("holm_p", float("nan"))
            holm_s = "-" if not np.isfinite(holm) else f"{holm:.3g}"
            lines.append(
                f"| {row['family']} | {row['hypothesis']} | `{row['metric']}` | {row['prediction']} | "
                f"{int(row['n_cpc1'])} | {int(row['n_cpc5'])} | {row['cpc1_median']:.4g} | "
                f"{row['cpc5_median']:.4g} | {row['cohens_d_cpc1_minus_cpc5']:.3g} | "
                f"{row['mannwhitney_p']:.3g} | {holm_s} |"
            )
    lines += [
        "",
        "Call the primary object **cross-fitted residual spread**, never innovation or diffusion.",
        "No composite coma score is formed. SL-004A is unchanged.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    gate = _require_gate()
    cfg = resolve_pipeline_config(args)
    paths = discover_h5_files(cfg.raw_root, subject_allowlist=cfg.subject_allowlist, limit_h5=cfg.limit_h5)
    print(f"{cfg.bundle_id}: RESID extract {len(paths)} files", flush=True)
    rows = parallel_map(extract_one, [str(p) for p in paths], workers=cfg.workers, desc="resid")
    runs = _annotate(pd.DataFrame(rows), cfg)
    patients = _patient(runs, cfg)
    missing_rows = []
    rec_primary = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])]
    for metric, _, _ in PRIMARY + SECONDARY:
        missing_rows.append(_missing_row(rec_primary, metric, grain="recording", window="0_12h", cfg=cfg))
        missing_rows.append(_missing_row(patients, metric, grain="subject", window="0_12h", cfg=cfg))
    missing = pd.DataFrame(missing_rows)
    contrast_rows = []
    for family, specs in (
        ("resid_primary", PRIMARY),
        ("resid_secondary", SECONDARY),
        ("resid_diagnostic", DIAGNOSTIC),
    ):
        for metric, hyp, pred in specs:
            if metric in patients.columns:
                contrast_rows.append(_contrast_row(patients, metric, cfg=cfg, family=family, hypothesis=hyp, prediction=pred))
    contrasts = pd.DataFrame(contrast_rows)
    if not contrasts.empty:
        idx = contrasts.index[contrasts["family"] == "resid_primary"].tolist()
        holm = _holm([float(contrasts.loc[i, "mannwhitney_p"]) for i in idx])
        for i, value in zip(idx, holm):
            contrasts.loc[i, "holm_p"] = value
    out = cfg.output_dir
    write_csv(out / "resid_run_level.csv", runs)
    write_csv(out / "resid_patient_primary.csv", patients)
    write_csv(out / "resid_missingness_by_cpc.csv", missing)
    write_csv(out / "resid_contrasts.csv", contrasts)
    md = _render(cfg=cfg, missing=missing, contrasts=contrasts, n_runs=int(len(runs)), n_patients=int(len(patients)), gate=gate)
    (out / "resid_part1.md").write_text(md, encoding="utf-8")
    write_json(
        out / "resid_part1_manifest.json",
        {
            "experiment": "COMA-RESID-001",
            "frame": "coords_3d_cohort_anchored",
            "estimand": "cross_fitted_residual_spread",
            "crossfit": {"n_blocks": 2, "embargo_steps": 4, "k": 20, "weight_mode": "inverse_distance", "psd_floor": 1e-8},
            "not": [
                "innovation",
                "ito",
                "family_b_jacobian",
                "ingest_transition_residual",
                "SL-004A",
            ],
            "part2_opened": False,
            "sl004a_modified": False,
            "holm_family": "resid_primary",
            "synthetic_gate": {"path": str(GATE_PATH), "pass": bool(gate.get("pass"))},
            "n_runs": int(len(runs)),
            "n_patients": int(len(patients)),
        },
    )
    print(f"wrote {out / 'resid_part1.md'}", flush=True)
    if not missing.empty:
        print(missing.to_string(index=False), flush=True)
    if not contrasts.empty:
        cols = [c for c in ("family", "metric", "n_cpc1", "n_cpc5", "cohens_d_cpc1_minus_cpc5", "mannwhitney_p", "holm_p") if c in contrasts.columns]
        print(contrasts[cols].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
