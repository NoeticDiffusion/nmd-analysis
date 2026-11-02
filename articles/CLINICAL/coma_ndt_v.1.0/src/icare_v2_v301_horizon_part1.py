"""COMA-HORIZON-001 on I-CARE part1 (sl_027). Part2 stays sealed.

Empirical C_h for h in {2,4,8} on coords_3d_cohort_anchored. Primary is
common-support raw Tr(C_h). Max-support is sensitivity. Horizon-normalized
trace is a finite-horizon spread rate, not a diffusion coefficient.
Holm is a new family on common-support Tr(C_2), Tr(C_4), Tr(C_8), not SL-004A.
Do not restart prediction from these features.
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
from icare_v2_v301_horizon_metrics import HORIZONS, estimate_horizon_geometry
from icare_v2_v301_l1_estimators import _segment_id
from icare_v2_v301_l1_panel import _annotate
from icare_v2_v301_l1_prepart2_gates import _holm

GATE_PATH = ARTICLE_DIR / "results" / "v3_0_1" / "horizon_synthetic_gate.json"

PRIMARY = tuple((f"cs_tr_h{h}_median", f"cs_Tr_C{h}", "CPC1 < CPC5") for h in HORIZONS)
SHAPE = tuple(
    (f"cs_{name}_h{h}_median", f"cs_{name}_C{h}", "descriptive")
    for h in HORIZONS
    for name in ("d_eff", "h_tilde")
)
RATE = tuple((f"cs_rate_h{h}_median", f"cs_rate_C{h}", "descriptive finite-horizon spread rate") for h in HORIZONS)
EXPLORATORY = (
    ("cs_beta_s_median", "cs_beta_S", "exploratory scaling; inspect curves first"),
)
MAX_TR = tuple((f"ms_tr_h{h}_median", f"ms_Tr_C{h}", "sensitivity max-support") for h in HORIZONS)


def extract_one(path: str) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "read_ok": False,
        "read_error": None,
        "horizon_status": None,
        "horizon_failure": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            timing = time_reference_from_handle(handle)
            row.update({k: meta[k] for k in ("cpc", "outcome", "hospital", "ttm", "age", "sex")})
            row.update(timing)
            if "/coords_3d_cohort_anchored/values" not in handle or "/time" not in handle:
                row["horizon_status"] = "missing_chart"
                row["read_ok"] = True
                return row
            xc = np.asarray(handle["/coords_3d_cohort_anchored/values"][:], dtype=float)
            time = np.asarray(handle["/time"][:], dtype=float)
            raw = handle["/row_source/raw_file"][:] if "/row_source/raw_file" in handle else None
            result = estimate_horizon_geometry(xc, time, segment_id=_segment_id(raw, xc.shape[0]))
            row["horizon_status"] = result.get("status")
            row["horizon_failure"] = result.get("failure_reason")
            row["horizon_n_valid_cs"] = result.get("n_valid_cs")
            row["n_common"] = result.get("n_common")
            row["nominal_dt_sec"] = result.get("nominal_dt_sec")
            n_source = result.get("n_source") or {}
            n_valid_ms = result.get("n_valid_ms") or {}
            for h in HORIZONS:
                row[f"n_source_h{h}"] = n_source.get(h, n_source.get(str(h), float("nan")))
                row[f"n_valid_ms_h{h}"] = n_valid_ms.get(h, n_valid_ms.get(str(h), float("nan")))
            med = result.get("medians") or {}
            for key, value in med.items():
                row[f"{key}_median"] = value
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
    metrics = [key for key, _, _ in PRIMARY + SHAPE + RATE + MAX_TR + EXPLORATORY]
    agg: dict[str, Any] = {
        "cpc": ("cpc", "first"),
        "contrast_group": ("contrast_group", "first"),
        "hospital": ("hospital", "first"),
        "n_runs": ("source_h5", "nunique"),
        "n_common": ("n_common", "median"),
    }
    for metric in metrics:
        if metric in work.columns:
            agg[metric] = (metric, "median")
    return work.groupby("subject_id", as_index=False).agg(**agg)


def _require_gate() -> dict[str, Any]:
    if not GATE_PATH.is_file():
        raise SystemExit(f"synthetic gate missing: {GATE_PATH}. Run icare_v2_v301_horizon_synthetic_gate.py first.")
    payload = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    if not bool(payload.get("pass")):
        raise SystemExit(f"synthetic gate FAILED: {GATE_PATH}. CPC contrasts not run.")
    return payload


def _render(*, cfg, missing: pd.DataFrame, contrasts: pd.DataFrame, n_runs: int, n_patients: int, gate: dict[str, Any]) -> str:
    lines = [
        "# COMA-HORIZON-001 part1 (sl_027)",
        "",
        f"Bundle `{cfg.bundle_id}`. Empirical finite-horizon increment geometry on",
        "`coords_3d_cohort_anchored`. Primary: common-support raw C_h for h in {2,4,8}.",
        "Not C_h/(h dt) as primary. Not a diffusion coefficient. Not Jacobian. Not generator.",
        "Part2 is not opened. Holm is only across common-support Tr(C_h), not SL-004A.",
        "Prediction is not restarted from these features.",
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
        "Call the primary object **finite-horizon increment geometry**, never diffusion.",
        "beta_S is exploratory; inspect h=2,4,8 curves first. SL-004A is unchanged.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    parser.add_argument("--from-run-level", type=Path, default=None, help="Reuse an existing horizon_run_level.csv and skip H5 extract.")
    args = parser.parse_args()
    gate = _require_gate()
    cfg = resolve_pipeline_config(args)
    if args.from_run_level is not None:
        runs = pd.read_csv(args.from_run_level)
        print(f"{cfg.bundle_id}: HORIZON reuse {len(runs)} run-level rows", flush=True)
    else:
        paths = discover_h5_files(cfg.raw_root, subject_allowlist=cfg.subject_allowlist, limit_h5=cfg.limit_h5)
        print(f"{cfg.bundle_id}: HORIZON extract {len(paths)} files", flush=True)
        rows = parallel_map(extract_one, [str(p) for p in paths], workers=cfg.workers, desc="horizon")
        runs = _annotate(pd.DataFrame(rows), cfg)
    patients = _patient(runs, cfg)
    missing_rows = []
    rec_primary = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])]
    for metric, _, _ in PRIMARY:
        missing_rows.append(_missing_row(rec_primary, metric, grain="recording", window="0_12h", cfg=cfg))
        missing_rows.append(_missing_row(patients, metric, grain="subject", window="0_12h", cfg=cfg))
    missing = pd.DataFrame(missing_rows)
    contrast_rows = []
    families = (
        ("horizon_primary", PRIMARY),
        ("horizon_shape", SHAPE),
        ("horizon_rate", RATE),
        ("horizon_exploratory", EXPLORATORY),
        ("horizon_max_support", MAX_TR),
    )
    for family, specs in families:
        for metric, hyp, pred in specs:
            if metric in patients.columns:
                contrast_rows.append(_contrast_row(patients, metric, cfg=cfg, family=family, hypothesis=hyp, prediction=pred))
    contrasts = pd.DataFrame(contrast_rows)
    if not contrasts.empty:
        idx = contrasts.index[contrasts["family"] == "horizon_primary"].tolist()
        holm = _holm([float(contrasts.loc[i, "mannwhitney_p"]) for i in idx])
        for i, value in zip(idx, holm):
            contrasts.loc[i, "holm_p"] = value
    out = cfg.output_dir
    write_csv(out / "horizon_run_level.csv", runs)
    write_csv(out / "horizon_patient_primary.csv", patients)
    write_csv(out / "horizon_missingness_by_cpc.csv", missing)
    write_csv(out / "horizon_contrasts.csv", contrasts)
    md = _render(cfg=cfg, missing=missing, contrasts=contrasts, n_runs=int(len(runs)), n_patients=int(len(patients)), gate=gate)
    (out / "horizon_part1.md").write_text(md, encoding="utf-8")
    write_json(
        out / "horizon_part1_manifest.json",
        {
            "experiment": "COMA-HORIZON-001",
            "frame": "coords_3d_cohort_anchored",
            "horizons": list(HORIZONS),
            "primary": "common_support_raw_C_h",
            "sensitivity": "horizon_maximal_support",
            "k": 20,
            "not": [
                "diffusion_coefficient",
                "C_h_over_hdt_as_primary",
                "family_b_jacobian",
                "generator",
                "SL-004A",
                "prediction_restart",
            ],
            "part2_opened": False,
            "sl004a_modified": False,
            "holm_family": "horizon_primary",
            "synthetic_gate": {"path": str(GATE_PATH), "pass": bool(gate.get("pass"))},
            "n_runs": int(len(runs)),
            "n_patients": int(len(patients)),
        },
    )
    print(f"wrote {out / 'horizon_part1.md'}", flush=True)
    if not missing.empty:
        print(missing.to_string(index=False), flush=True)
    if not contrasts.empty:
        cols = [c for c in ("family", "metric", "n_cpc1", "n_cpc5", "cpc1_median", "cpc5_median", "cohens_d_cpc1_minus_cpc5", "mannwhitney_p", "holm_p") if c in contrasts.columns]
        print(contrasts[cols].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
