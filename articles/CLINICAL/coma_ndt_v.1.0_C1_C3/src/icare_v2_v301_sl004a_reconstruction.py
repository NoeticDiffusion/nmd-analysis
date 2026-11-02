"""SL-004A reconstruction gate: registered L1 formulas on both charts.

Reconstructs stored subject-anchored G90 and d_diff from the MNDM
estimators, then applies the same estimators to
`coords_3d_cohort_anchored` (re-kNN in that chart). Does not open part2.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

from icare_v2_common import (
    add_common_args,
    as_scalar,
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
from icare_v2_v301_l1_estimators import (
    _segment_id,
    estimate_diffusion,
    estimate_g90,
    series_mae,
    series_median,
)
from icare_v2_v301_l1_panel import _annotate, _s
from icare_v2_v301_l1_prepart2_gates import _holm

MAE_FAIL = 1e-6
PROTOCOL = "SL-004A"


def _scalar_path(handle: h5py.File, path: str) -> Any:
    if path not in handle:
        return None
    return as_scalar(handle[path][()])


def extract_one(path: str) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "read_ok": False,
        "read_error": None,
        "recon_pass": False,
        "recon_eligible": False,
    }
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            timing = time_reference_from_handle(handle)
            row.update({k: meta[k] for k in ("cpc", "outcome", "hospital", "ttm", "age", "sex")})
            row.update(timing)
            xs = np.asarray(handle["/coords_3d_subject_anchored/values"][:], dtype=float)
            xc = np.asarray(handle["/coords_3d_cohort_anchored/values"][:], dtype=float)
            time = np.asarray(handle["/time"][:], dtype=float)
            raw = handle["/row_source/raw_file"][:] if "/row_source/raw_file" in handle else None
            seg = _segment_id(raw, xs.shape[0])
            stored_g = (
                np.asarray(handle["/dynamical_families/amplification/v1/neighbor_gain_q90_level1/series/neighbor_gain_q90"][:], dtype=float)
                if "/dynamical_families/amplification/v1/neighbor_gain_q90_level1/series/neighbor_gain_q90" in handle
                else None
            )
            stored_d = (
                np.asarray(handle["/dynamical_families/diffusion/v1/series/d_diff"][:], dtype=float)
                if "/dynamical_families/diffusion/v1/series/d_diff" in handle
                else None
            )
            row["family_coordinate_layer"] = _s(
                _scalar_path(handle, "/dynamical_families/amplification/v1/neighbor_gain_q90_level1/provenance/coordinate_layer")
            )
            row["primary_coordinate_layer"] = _s(handle.attrs.get("primary_coordinate_layer"))
            row["neighborhood_k"] = _scalar_path(
                handle, "/dynamical_families/amplification/v1/neighbor_gain_q90_level1/provenance/settings/neighborhood_k"
            )
            row["q"] = _scalar_path(handle, "/dynamical_families/amplification/v1/neighbor_gain_q90_level1/provenance/settings/q")
            row["stored_g90_median"] = median_finite(stored_g)
            row["stored_d_eff_median"] = median_finite(stored_d)
            g_s = estimate_g90(xs, time, segment_id=seg, chart_name="coords_3d_subject_anchored")
            d_s = estimate_diffusion(xs, time, segment_id=seg, chart_name="coords_3d_subject_anchored")
            row["g90_subject_status"] = g_s.get("computation_status")
            row["d_eff_subject_status"] = d_s.get("computation_status")
            recon_g = np.asarray((g_s.get("series") or {}).get("neighbor_gain_q90"), dtype=float) if g_s.get("series") else None
            recon_d = np.asarray((d_s.get("series") or {}).get("d_diff"), dtype=float) if d_s.get("series") else None
            g_mae, g_max, g_n = series_mae(recon_g, stored_g)
            d_mae, d_max, d_n = series_mae(recon_d, stored_d)
            row["g90_recon_mae"] = g_mae
            row["g90_recon_maxabs"] = g_max
            row["g90_recon_n"] = g_n
            row["d_eff_recon_mae"] = d_mae
            row["d_eff_recon_maxabs"] = d_max
            row["d_eff_recon_n"] = d_n
            row["g90_subject_recompute_median"] = series_median(g_s, "neighbor_gain_q90")
            row["d_eff_subject_recompute_median"] = series_median(d_s, "d_diff")
            g_c = estimate_g90(xc, time, segment_id=seg, chart_name="coords_3d_cohort_anchored")
            d_c = estimate_diffusion(xc, time, segment_id=seg, chart_name="coords_3d_cohort_anchored")
            row["g90_cohort_status"] = g_c.get("computation_status")
            row["d_eff_cohort_status"] = d_c.get("computation_status")
            row["g90_cohort_reknn_median"] = series_median(g_c, "neighbor_gain_q90")
            row["d_eff_cohort_reknn_median"] = series_median(d_c, "d_diff")
            has_g = stored_g is not None and np.isfinite(np.asarray(stored_g, dtype=float)).any()
            has_d = stored_d is not None and np.isfinite(np.asarray(stored_d, dtype=float)).any()
            g_ok = (not has_g) or (g_s.get("computation_status") == "computed" and np.isfinite(g_mae) and g_mae <= MAE_FAIL)
            d_ok = (not has_d) or (d_s.get("computation_status") == "computed" and np.isfinite(d_mae) and d_mae <= MAE_FAIL)
            row["recon_eligible"] = bool(has_g or has_d)
            row["recon_pass"] = bool(g_ok and d_ok)
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _patient(runs: pd.DataFrame, cfg) -> pd.DataFrame:
    work = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    if work.empty:
        return work
    metrics = [
        "stored_g90_median",
        "stored_d_eff_median",
        "g90_subject_recompute_median",
        "d_eff_subject_recompute_median",
        "g90_cohort_reknn_median",
        "d_eff_cohort_reknn_median",
        "g90_recon_mae",
        "d_eff_recon_mae",
    ]
    agg: dict[str, Any] = {
        "cpc": ("cpc", "first"),
        "contrast_group": ("contrast_group", "first"),
        "n_runs": ("source_h5", "nunique"),
        "n_recon_pass": ("recon_pass", "sum"),
    }
    for metric in metrics:
        if metric in work.columns:
            agg[metric] = (metric, "median")
    return work.groupby("subject_id", as_index=False).agg(**agg)


def _render(*, cfg, recon: dict, contrasts: pd.DataFrame, determ: dict, provenance: dict) -> str:
    lines = [
        "# SL-004A reconstruction gate",
        "",
        f"Bundle `{cfg.bundle_id}`. Protocol `{PROTOCOL}`. Part2 is not opened.",
        "",
        "Confirmatory readout: recompute `d_eff` and `G_90` on",
        "`coords_3d_cohort_anchored` with kNN selected in that same chart.",
        "Subject-anchored stored families remain discovery.",
        "",
        "## Reconstruction vs stored (subject-anchored producer)",
        "",
        f"- files: {recon['n_files']}",
        f"- recon pass: {recon['n_pass']}/{recon['n_files']} (eligible {recon.get('n_eligible')})",
        f"- G90 MAE median / max: `{recon['g90_mae_median']:.3g}` / `{recon['g90_mae_max']:.3g}`",
        f"- d_eff MAE median / max: `{recon['d_mae_median']:.3g}` / `{recon['d_mae_max']:.3g}`",
        f"- determinism max abs (G90, d_eff): `{determ.get('g90_maxabs')}` / `{determ.get('d_maxabs')}`",
        "",
        "## Part1 producer cohort re-kNN (prospective expectation, not part2)",
        "",
        "| Metric | Frame | n CPC1 | n CPC5 | CPC1 med | CPC5 med | d | MW p | Holm p |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    if contrasts.empty:
        lines.append("| - | - | - | - | - | - | - | - | - |")
    else:
        for _, row in contrasts.iterrows():
            holm = row.get("holm_p", float("nan"))
            holm_s = "-" if not np.isfinite(holm) else f"{holm:.3g}"
            lines.append(
                f"| `{row['metric']}` | {row['family']} | {int(row['n_cpc1'])} | {int(row['n_cpc5'])} | "
                f"{row['cpc1_median']:.4g} | {row['cpc5_median']:.4g} | {row['cohens_d_cpc1_minus_cpc5']:.3g} | "
                f"{row['mannwhitney_p']:.3g} | {holm_s} |"
            )
    lines += [
        "",
        "## Frozen outcome language (before any part2 dump)",
        "",
        "- Joint confirmation: both Holm-adjusted tests pass and both directions match.",
        "- Partial confirmation: one endpoint passes Holm in the frozen direction.",
        "- Directional but unconfirmed: neither passes Holm; both point in the frozen directions.",
        "- Failure/reversal: one or both materially reverse direction.",
        "",
        f"- MNDM src: `{provenance.get('mndm_src')}`",
        f"- part2_opened: false",
        f"- part2_protocol_ready: {str(recon['gate_pass']).lower()}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    paths = discover_h5_files(cfg.raw_root, subject_allowlist=cfg.subject_allowlist, limit_h5=cfg.limit_h5)
    print(f"{cfg.bundle_id}: SL-004A reconstruct {len(paths)} files", flush=True)
    rows = parallel_map(extract_one, [str(p) for p in paths], workers=cfg.workers, desc="sl004a")
    runs = _annotate(pd.DataFrame(rows), cfg)
    determ = {"n": 0, "g90_maxabs": float("nan"), "d_maxabs": float("nan")}
    ok = runs[runs["read_ok"] == True]  # noqa: E712
    if not ok.empty:
        sample = str(ok.iloc[0]["source_h5"])
        a = extract_one(sample)
        b = extract_one(sample)
        determ = {
            "n": 2,
            "path": sample,
            "g90_maxabs": float(
                abs(float(a.get("g90_cohort_reknn_median") or 0) - float(b.get("g90_cohort_reknn_median") or 0))
            ),
            "d_maxabs": float(
                abs(float(a.get("d_eff_cohort_reknn_median") or 0) - float(b.get("d_eff_cohort_reknn_median") or 0))
            ),
        }
    patients = _patient(runs, cfg)
    contrast_specs = [
        ("stored_discovery", "stored_d_eff_median", "A_breadth", "CPC1 > CPC5"),
        ("stored_discovery", "stored_g90_median", "C_gain_q90", "CPC1 < CPC5"),
        ("cohort_reknn_producer", "d_eff_cohort_reknn_median", "A_breadth", "CPC1 > CPC5"),
        ("cohort_reknn_producer", "g90_cohort_reknn_median", "C_gain_q90", "CPC1 < CPC5"),
    ]
    contrast_rows = []
    for family, metric, hyp, pred in contrast_specs:
        if metric in patients.columns:
            contrast_rows.append(_contrast_row(patients, metric, cfg=cfg, family=family, hypothesis=hyp, prediction=pred))
    contrasts = pd.DataFrame(contrast_rows)
    if not contrasts.empty:
        for family in contrasts["family"].unique():
            idx = contrasts.index[contrasts["family"] == family].tolist()
            holm = _holm([float(contrasts.loc[i, "mannwhitney_p"]) for i in idx])
            for i, value in zip(idx, holm):
                contrasts.loc[i, "holm_p"] = value
    g_mae = pd.to_numeric(runs.get("g90_recon_mae"), errors="coerce")
    d_mae = pd.to_numeric(runs.get("d_eff_recon_mae"), errors="coerce")
    n_pass = int(runs["recon_pass"].fillna(False).astype(bool).sum()) if "recon_pass" in runs else 0
    n_eligible = int(runs["recon_eligible"].fillna(False).astype(bool).sum()) if "recon_eligible" in runs else 0
    determ_ok = bool(
        np.isfinite(determ.get("g90_maxabs", float("nan")))
        and np.isfinite(determ.get("d_maxabs", float("nan")))
        and float(determ["g90_maxabs"]) <= MAE_FAIL
        and float(determ["d_maxabs"]) <= MAE_FAIL
    )
    recon = {
        "n_files": int(len(runs)),
        "n_eligible": n_eligible,
        "n_pass": n_pass,
        "g90_mae_median": float(g_mae.median()) if g_mae.notna().any() else float("nan"),
        "g90_mae_max": float(g_mae.max()) if g_mae.notna().any() else float("nan"),
        "d_mae_median": float(d_mae.median()) if d_mae.notna().any() else float("nan"),
        "d_mae_max": float(d_mae.max()) if d_mae.notna().any() else float("nan"),
        "gate_pass": bool(n_eligible > 0 and n_pass == int(len(runs)) and determ_ok),
    }
    from icare_v2_v301_l1_estimators import DEFAULT_MNDM_SRC, ensure_mndm

    mndm_src = str(ensure_mndm())
    provenance = {
        "protocol": PROTOCOL,
        "confirmatory_frame": "coords_3d_cohort_anchored",
        "neighborhood": "reknn_in_same_frame",
        "k": 20,
        "q": 0.90,
        "eps": 1e-12,
        "aggregation": "subject_median_0_12h",
        "confirmatory_endpoints": ["d_eff_a_level1", "neighbor_gain_q90_level1"],
        "supportive_endpoints": ["neighbor_separation_rate_level1"],
        "exploratory_endpoints": [
            "cloud_volume_change_rate_level1",
            "b_norm_pooled_level1",
            "history_predictive_gain_level1",
            "f_perp_crossfit_level1",
        ],
        "outcome_language": [
            "joint_confirmation",
            "partial_confirmation",
            "directional_but_unconfirmed",
            "failure_reversal",
        ],
        "part2_opened": False,
        "part2_protocol_ready": recon["gate_pass"],
        "mndm_src": mndm_src,
        "amplification_write_gate": "producer refuses cohort layer name; analysis feeds cohort values into the registered estimator",
        "bundle_id": cfg.bundle_id,
        "default_mndm_src": str(DEFAULT_MNDM_SRC),
    }
    out = cfg.output_dir
    write_csv(out / "sl004a_run_level.csv", runs)
    write_csv(out / "sl004a_patient_primary.csv", patients)
    write_csv(out / "sl004a_contrasts.csv", contrasts)
    write_json(out / "l1_confirmatory_lock.json", provenance)
    md = _render(cfg=cfg, recon=recon, contrasts=contrasts, determ=determ, provenance=provenance)
    (out / "sl004a_reconstruction.md").write_text(md, encoding="utf-8")
    write_json(out / "sl004a_reconstruction_manifest.json", {"recon": recon, "determ": determ, "provenance": provenance})
    print(f"wrote {out / 'sl004a_reconstruction.md'}", flush=True)
    print(f"recon_pass {n_pass}/{len(runs)} gate_pass={recon['gate_pass']}", flush=True)
    if not contrasts.empty:
        print(contrasts[["family", "metric", "n_cpc1", "n_cpc5", "cohens_d_cpc1_minus_cpc5", "mannwhitney_p"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
