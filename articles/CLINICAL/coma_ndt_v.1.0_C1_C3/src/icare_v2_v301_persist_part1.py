"""COMA-PERSIST-Q25-001 on I-CARE part1 (sl_021 / sl_022 / sl_028).

Lower-quartile of cohort-frame shape over valid windows. No threshold, no
episode definition, no occupancy, no dwell. Gaps simply drop invalid samples;
they are not interpolated. Holm is a new two-test family on Q25(H_tilde) and
Q25(d_eff), not SL-004A. Occupancy B_i(c) waits until Q25 is scientifically
distinct from the median. Part2 stays sealed. Prediction is not restarted.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy import stats

from icare_v2_common import (
    add_common_args,
    diffusion_geometry_from_tensor,
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
from icare_v2_v301_l1_estimators import _segment_id, estimate_diffusion
from icare_v2_v301_l1_panel import _annotate
from icare_v2_v301_l1_prepart2_gates import _holm, _spearman

EPS = 1e-12
MIN_FINITE = 8

PRIMARY = (
    ("h_tilde_q25", "Q25_H_tilde", "CPC1 > CPC5"),
    ("d_eff_q25", "Q25_d_eff", "CPC1 > CPC5"),
)
SECONDARY = (
    ("h_tilde_median", "median_H_tilde", "descriptive companion of Q25"),
    ("d_eff_median", "median_d_eff", "descriptive companion of Q25"),
    ("tr_a_q25", "Q25_Tr_a", "descriptive magnitude tail"),
    ("tr_a_median", "median_Tr_a", "descriptive magnitude center"),
)


def _q25(values: np.ndarray) -> float:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size < MIN_FINITE:
        return float("nan")
    return float(np.percentile(finite, 25.0))


def _median(values: np.ndarray) -> float:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size < MIN_FINITE:
        return float("nan")
    return float(np.median(finite))


def _series_scalars(tensors: np.ndarray, valid: np.ndarray | None) -> dict[str, np.ndarray]:
    a = np.asarray(tensors, dtype=float)
    n = int(a.shape[0]) if a.ndim == 3 else 0
    out = {name: np.full(n, np.nan, dtype=float) for name in ("h_tilde", "d_eff", "tr_a")}
    if a.ndim != 3 or a.shape[1:] != (3, 3):
        return out
    ok = np.ones(n, dtype=bool)
    if valid is not None:
        ok &= np.asarray(valid, dtype=float).reshape(-1)[:n] > 0
    for i in np.flatnonzero(ok):
        tensor = a[i]
        if not np.isfinite(tensor).all():
            continue
        geo = diffusion_geometry_from_tensor(0.5 * (tensor + tensor.T), eps=EPS)
        out["h_tilde"][i] = geo["h_tilde_a"]
        out["d_eff"][i] = geo["d_eff_a"]
        out["tr_a"][i] = geo["d_total"]
    return out


def algebraic_gate() -> list[dict[str, Any]]:
    constant = np.full(40, 2.0)
    two_level = np.concatenate([np.full(10, 1.0), np.full(30, 3.0)])
    return [
        {"name": "constant_q25_eq_median", "pass": abs(_q25(constant) - _median(constant)) < 1e-12, "q25": _q25(constant), "median": _median(constant)},
        {"name": "q25_leq_median", "pass": _q25(two_level) <= _median(two_level) + 1e-12, "q25": _q25(two_level), "median": _median(two_level)},
        {"name": "two_level_q25_below_median", "pass": _q25(two_level) < _median(two_level) - 1e-12, "q25": _q25(two_level), "median": _median(two_level)},
    ]


def extract_one(path: str) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "read_ok": False,
        "read_error": None,
        "persist_status": None,
        "persist_failure": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            timing = time_reference_from_handle(handle)
            row.update({k: meta[k] for k in ("cpc", "outcome", "hospital", "ttm", "age", "sex")})
            row.update(timing)
            if "/coords_3d_cohort_anchored/values" not in handle or "/time" not in handle:
                row["persist_status"] = "missing_chart"
                row["read_ok"] = True
                return row
            xc = np.asarray(handle["/coords_3d_cohort_anchored/values"][:], dtype=float)
            time = np.asarray(handle["/time"][:], dtype=float)
            raw = handle["/row_source/raw_file"][:] if "/row_source/raw_file" in handle else None
            diff = estimate_diffusion(xc, time, segment_id=_segment_id(raw, xc.shape[0]), chart_name="coords_3d_cohort_anchored")
            row["persist_status"] = diff.get("computation_status")
            row["persist_failure"] = diff.get("failure_reason")
            series = diff.get("series") or {}
            tensors = series.get("a_hat")
            valid = series.get("valid")
            if tensors is None:
                row["read_ok"] = True
                return row
            scalars = _series_scalars(np.asarray(tensors, dtype=float), None if valid is None else np.asarray(valid))
            for name, values in scalars.items():
                row[f"{name}_q25"] = _q25(values)
                row[f"{name}_median"] = _median(values)
                row[f"{name}_n_finite"] = int(np.isfinite(values).sum())
            h_q, h_m = row.get("h_tilde_q25", float("nan")), row.get("h_tilde_median", float("nan"))
            row["q25_leq_median"] = bool(np.isfinite(h_q) and np.isfinite(h_m) and h_q <= h_m + 1e-8)
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
    metrics = [key for key, _, _ in PRIMARY + SECONDARY]
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


def _render(*, cfg, missing: pd.DataFrame, contrasts: pd.DataFrame, spearman: pd.DataFrame, n_runs: int, n_patients: int, gate: dict[str, Any]) -> str:
    lines = [
        "# COMA-PERSIST-Q25-001 part1 (sl_022 / sl_028)",
        "",
        f"Bundle `{cfg.bundle_id}`. Lower quartile of cohort-anchored local shape over",
        "valid windows. No threshold occupancy, no dwell, no gap bridging.",
        "Holm is only Q25(H_tilde) and Q25(d_eff), not SL-004A. Part2 is not opened.",
        "Prediction is not restarted. Occupancy waits until Q25 is distinct from the median.",
        "",
        f"Algebraic gate pass={gate.get('pass')} ({gate.get('n_checks')} checks).",
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
        "## Q25 vs median (subject grain, CPC1+CPC5)",
        "",
        "| Pair | n | rho | p |",
        "| --- | ---: | ---: | ---: |",
    ]
    if spearman.empty:
        lines.append("| - | - | - | - |")
    else:
        for _, row in spearman.iterrows():
            lines.append(f"| `{row['left']}` vs `{row['right']}` | {int(row['n'])} | {row['rho']:.3g} | {row['p']:.3g} |")
    lines += [
        "",
        "If Q25 is nearly collinear with the median, occupancy/dwell is not licensed.",
        "No composite coma score is formed. SL-004A is unchanged.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    gate_rows = algebraic_gate()
    gate = {"pass": all(row["pass"] for row in gate_rows), "n_checks": len(gate_rows), "rows": gate_rows}
    write_json(
        Path(__file__).resolve().parents[1] / "results" / "v3_0_1" / "persist_q25_algebraic_gate.json",
        gate,
    )
    if not gate["pass"]:
        raise SystemExit(f"persist Q25 algebraic gate failed: {[r['name'] for r in gate_rows if not r['pass']]}")
    cfg = resolve_pipeline_config(args)
    paths = discover_h5_files(cfg.raw_root, subject_allowlist=cfg.subject_allowlist, limit_h5=cfg.limit_h5)
    print(f"{cfg.bundle_id}: PERSIST-Q25 extract {len(paths)} files", flush=True)
    rows = parallel_map(extract_one, [str(p) for p in paths], workers=cfg.workers, desc="persist_q25")
    runs = _annotate(pd.DataFrame(rows), cfg)
    patients = _patient(runs, cfg)
    missing_rows = []
    rec_primary = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])]
    for metric, _, _ in PRIMARY:
        missing_rows.append(_missing_row(rec_primary, metric, grain="recording", window="0_12h", cfg=cfg))
        missing_rows.append(_missing_row(patients, metric, grain="subject", window="0_12h", cfg=cfg))
    missing = pd.DataFrame(missing_rows)
    contrast_rows = []
    for family, specs in (("persist_primary", PRIMARY), ("persist_secondary", SECONDARY)):
        for metric, hyp, pred in specs:
            if metric in patients.columns:
                contrast_rows.append(_contrast_row(patients, metric, cfg=cfg, family=family, hypothesis=hyp, prediction=pred))
    contrasts = pd.DataFrame(contrast_rows)
    if not contrasts.empty:
        idx = contrasts.index[contrasts["family"] == "persist_primary"].tolist()
        holm = _holm([float(contrasts.loc[i, "mannwhitney_p"]) for i in idx])
        for i, value in zip(idx, holm):
            contrasts.loc[i, "holm_p"] = value
    spearman_rows = []
    for left, right in (
        ("h_tilde_q25", "h_tilde_median"),
        ("d_eff_q25", "d_eff_median"),
        ("tr_a_q25", "tr_a_median"),
        ("h_tilde_q25", "d_eff_q25"),
    ):
        if left in patients.columns and right in patients.columns:
            spearman_rows.append({"left": left, "right": right, **_spearman(patients, left, right)})
    spearman = pd.DataFrame(spearman_rows)
    out = cfg.output_dir
    write_csv(out / "persist_q25_run_level.csv", runs)
    write_csv(out / "persist_q25_patient_primary.csv", patients)
    write_csv(out / "persist_q25_missingness_by_cpc.csv", missing)
    write_csv(out / "persist_q25_contrasts.csv", contrasts)
    write_csv(out / "persist_q25_spearman.csv", spearman)
    md = _render(cfg=cfg, missing=missing, contrasts=contrasts, spearman=spearman, n_runs=int(len(runs)), n_patients=int(len(patients)), gate=gate)
    (out / "persist_q25_part1.md").write_text(md, encoding="utf-8")
    write_json(
        out / "persist_q25_part1_manifest.json",
        {
            "experiment": "COMA-PERSIST-Q25-001",
            "frame": "coords_3d_cohort_anchored",
            "estimand": "valid_window_lower_quartile_no_occupancy",
            "not": ["threshold_occupancy", "dwell", "gap_bridging", "SL-004A", "prediction_restart"],
            "part2_opened": False,
            "sl004a_modified": False,
            "holm_family": "persist_primary",
            "algebraic_gate": {"pass": bool(gate["pass"])},
            "n_runs": int(len(runs)),
            "n_patients": int(len(patients)),
        },
    )
    print(f"wrote {out / 'persist_q25_part1.md'}", flush=True)
    if not missing.empty:
        print(missing.to_string(index=False), flush=True)
    if not contrasts.empty:
        cols = [c for c in ("family", "metric", "n_cpc1", "n_cpc5", "cpc1_median", "cpc5_median", "cohens_d_cpc1_minus_cpc5", "mannwhitney_p", "holm_p") if c in contrasts.columns]
        print(contrasts[cols].to_string(index=False), flush=True)
    if not spearman.empty:
        print(spearman.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
