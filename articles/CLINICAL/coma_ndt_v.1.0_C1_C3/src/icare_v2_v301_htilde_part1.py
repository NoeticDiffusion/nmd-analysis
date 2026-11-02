"""Cohort-frame H_tilde robustness (sl_013).

Exploratory construct-validation of spread-shape richness. Cannot become
a new confirmatory primary (H2 already seen on part1). Compare cohort
re-kNN H_tilde with cohort d_eff. Subject-stored H_tilde is the same
discovery family as old H2, not independent replication.
Part2 stays sealed.
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
    as_scalar,
    diffusion_geometry_from_tensor,
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
from icare_v2_v301_l1_estimators import _segment_id, estimate_diffusion, series_median
from icare_v2_v301_l1_panel import _annotate, _s

EPS = 1e-12
A_PATH = "/dynamical_families/diffusion/v1/series/a_hat"
VALID_PATH = "/dynamical_families/diffusion/v1/series/valid"


def _shape_medians(tensors: np.ndarray, valid: np.ndarray | None) -> tuple[float, float]:
    a = np.asarray(tensors, dtype=float)
    if a.ndim != 3 or a.shape[1:] != (3, 3):
        return float("nan"), float("nan")
    n = a.shape[0]
    ok = np.ones(n, dtype=bool)
    if valid is not None:
        ok &= np.asarray(valid, dtype=float).reshape(-1)[:n] > 0
    h = np.full(n, np.nan)
    d = np.full(n, np.nan)
    for i in np.flatnonzero(ok):
        tensor = a[i]
        if not np.isfinite(tensor).all():
            continue
        metrics = diffusion_geometry_from_tensor(tensor, eps=EPS)
        h[i] = metrics["h_tilde_a"]
        d[i] = metrics["d_eff_a"]
    return median_finite(h), median_finite(d)


def algebraic_gate() -> list[dict[str, Any]]:
    rows = []
    iso = diffusion_geometry_from_tensor(np.eye(3), eps=EPS)
    rows.append(
        {
            "name": "isotropic_h_tilde_1",
            "pass": abs(iso["h_tilde_a"] - 1.0) < 1e-10 and abs(iso["d_eff_a"] - 3.0) < 1e-8,
            **iso,
        }
    )
    rank1 = diffusion_geometry_from_tensor(np.diag([1.0, 0.0, 0.0]), eps=EPS)
    rows.append(
        {
            "name": "rank1_low_entropy",
            "pass": rank1["h_tilde_a"] < 0.05 and abs(rank1["d_eff_a"] - 1.0) < 1e-6,
            **rank1,
        }
    )
    rank2 = diffusion_geometry_from_tensor(np.diag([1.0, 1.0, 0.0]), eps=EPS)
    expected_h = float(np.log(2.0) / np.log(3.0))
    rows.append(
        {
            "name": "rank2_h_tilde_log2_over_log3",
            "pass": abs(rank2["h_tilde_a"] - expected_h) < 1e-6 and abs(rank2["d_eff_a"] - 2.0) < 1e-6,
            **rank2,
        }
    )
    scaled = diffusion_geometry_from_tensor(4.0 * np.eye(3), eps=EPS)
    rows.append(
        {
            "name": "scale_invariant_h_tilde",
            "pass": abs(scaled["h_tilde_a"] - iso["h_tilde_a"]) < 1e-12,
            **scaled,
        }
    )
    return rows


def extract_one(path: str) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "read_ok": False,
        "read_error": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            timing = time_reference_from_handle(handle)
            row.update({k: meta[k] for k in ("cpc", "outcome", "hospital", "ttm", "age", "sex")})
            row.update(timing)
            stored_h = stored_d = float("nan")
            if A_PATH in handle:
                tensors = np.asarray(handle[A_PATH][:], dtype=float)
                valid = np.asarray(handle[VALID_PATH][:], dtype=float) if VALID_PATH in handle else None
                stored_h, stored_d = _shape_medians(tensors, valid)
            row["h_tilde_subject_stored_median"] = stored_h
            row["d_eff_from_stored_a_median"] = stored_d
            if "/coords_3d_cohort_anchored/values" not in handle or "/time" not in handle:
                row["cohort_status"] = "missing_chart"
                row["read_ok"] = True
                return row
            xc = np.asarray(handle["/coords_3d_cohort_anchored/values"][:], dtype=float)
            time = np.asarray(handle["/time"][:], dtype=float)
            raw = handle["/row_source/raw_file"][:] if "/row_source/raw_file" in handle else None
            diff = estimate_diffusion(xc, time, segment_id=_segment_id(raw, xc.shape[0]), chart_name="coords_3d_cohort_anchored")
            row["cohort_status"] = diff.get("computation_status")
            series = diff.get("series") or {}
            tensors = series.get("a_hat")
            valid = series.get("valid")
            if tensors is None:
                row["h_tilde_cohort_reknn_median"] = float("nan")
                row["d_eff_cohort_from_a_median"] = float("nan")
            else:
                h_c, d_c = _shape_medians(np.asarray(tensors, dtype=float), None if valid is None else np.asarray(valid))
                row["h_tilde_cohort_reknn_median"] = h_c
                row["d_eff_cohort_from_a_median"] = d_c
            row["d_eff_cohort_estimator_median"] = series_median(diff, "d_diff")
            row["family_coordinate_layer"] = _s(as_scalar(handle.attrs.get("primary_coordinate_layer")))
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _patient(runs: pd.DataFrame, cfg) -> pd.DataFrame:
    work = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    if work.empty:
        return work
    agg = {
        "cpc": ("cpc", "first"),
        "contrast_group": ("contrast_group", "first"),
        "n_runs": ("source_h5", "nunique"),
        "h_tilde_subject_stored_median": ("h_tilde_subject_stored_median", "median"),
        "d_eff_from_stored_a_median": ("d_eff_from_stored_a_median", "median"),
        "h_tilde_cohort_reknn_median": ("h_tilde_cohort_reknn_median", "median"),
        "d_eff_cohort_from_a_median": ("d_eff_cohort_from_a_median", "median"),
        "d_eff_cohort_estimator_median": ("d_eff_cohort_estimator_median", "median"),
    }
    present = {k: v for k, v in agg.items() if v[0] in work.columns or k in {"cpc", "contrast_group", "n_runs"}}
    return work.groupby("subject_id", as_index=False).agg(**present)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    gate = algebraic_gate()
    write_json(cfg.output_dir / "htilde_algebraic_gate.json", {"n_pass": int(sum(r["pass"] for r in gate)), "n": len(gate), "rows": gate})
    if not all(row["pass"] for row in gate):
        failed = [row["name"] for row in gate if not row["pass"]]
        raise SystemExit(f"H_tilde algebraic gate failed: {failed}")
    paths = discover_h5_files(cfg.raw_root, subject_allowlist=cfg.subject_allowlist, limit_h5=cfg.limit_h5)
    print(f"{cfg.bundle_id}: H_tilde extract {len(paths)} files", flush=True)
    rows = parallel_map(extract_one, [str(p) for p in paths], workers=cfg.workers, desc="htilde")
    runs = _annotate(pd.DataFrame(rows), cfg)
    patients = _patient(runs, cfg)
    specs = (
        ("htilde_subject_stored", "h_tilde_subject_stored_median", "H2_subject", "CPC1 > CPC5; discovery family, not independent"),
        ("htilde_cohort_reknn", "h_tilde_cohort_reknn_median", "H2_cohort", "exploratory robustness vs cohort d_eff"),
        ("deff_cohort_from_a", "d_eff_cohort_from_a_median", "d_eff_from_same_tensors", "should match SL-004A d_eff"),
        ("deff_subject_from_a", "d_eff_from_stored_a_median", "d_eff_subject_from_a", "stored-tensor companion"),
    )
    missing_rows = []
    contrast_rows = []
    for family, metric, hyp, pred in specs:
        good = patients[patients["contrast_group"] == cfg.good_label]
        poor = patients[patients["contrast_group"] == cfg.poor_label]
        g_yes = int(pd.to_numeric(good.get(metric), errors="coerce").notna().sum()) if metric in good else 0
        p_yes = int(pd.to_numeric(poor.get(metric), errors="coerce").notna().sum()) if metric in poor else 0
        table = np.array([[g_yes, max(len(good) - g_yes, 0)], [p_yes, max(len(poor) - p_yes, 0)]], dtype=int)
        fisher_p = float(stats.fisher_exact(table)[1]) if table.sum() else float("nan")
        missing_rows.append(
            {
                "metric": metric,
                "n_cpc1_finite": g_yes,
                "n_cpc1": int(len(good)),
                "n_cpc5_finite": p_yes,
                "n_cpc5": int(len(poor)),
                "fisher_p": fisher_p,
            }
        )
        if metric in patients.columns:
            contrast_rows.append(_contrast_row(patients, metric, cfg=cfg, family=family, hypothesis=hyp, prediction=pred))
    missing = pd.DataFrame(missing_rows)
    contrasts = pd.DataFrame(contrast_rows)
    rho_rows = []
    pair = patients[["h_tilde_cohort_reknn_median", "d_eff_cohort_from_a_median"]].apply(pd.to_numeric, errors="coerce")
    mask = pair.notna().all(axis=1)
    if int(mask.sum()) >= 10:
        rho, p = stats.spearmanr(pair.loc[mask, "h_tilde_cohort_reknn_median"], pair.loc[mask, "d_eff_cohort_from_a_median"])
        rho_rows.append({"pair": "cohort_h_tilde_vs_d_eff", "n": int(mask.sum()), "rho": float(rho), "p": float(p)})
    rho = pd.DataFrame(rho_rows)
    lines = [
        "# Cohort-frame H_tilde (sl_013)",
        "",
        "Exploratory. Not a new confirmatory primary. Algebraic gate must pass first.",
        "Part2 is not opened.",
        "",
        "## Missingness",
        "",
        "| Metric | CPC1 | CPC5 | Fisher p |",
        "| --- | --- | --- | ---: |",
    ]
    for _, row in missing.iterrows():
        lines.append(
            f"| `{row['metric']}` | {int(row['n_cpc1_finite'])}/{int(row['n_cpc1'])} | "
            f"{int(row['n_cpc5_finite'])}/{int(row['n_cpc5'])} | {row['fisher_p']:.3g} |"
        )
    lines += [
        "",
        "## Contrasts",
        "",
        "| Family | Metric | n CPC1 | n CPC5 | CPC1 med | CPC5 med | d | MW p |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    if contrasts.empty:
        lines.append("| - | - | - | - | - | - | - | - |")
    else:
        for _, row in contrasts.iterrows():
            lines.append(
                f"| {row['family']} | `{row['metric']}` | {int(row['n_cpc1'])} | {int(row['n_cpc5'])} | "
                f"{row['cpc1_median']:.4g} | {row['cpc5_median']:.4g} | "
                f"{row['cohens_d_cpc1_minus_cpc5']:.3g} | {row['mannwhitney_p']:.3g} |"
            )
    lines += ["", "## Cohort H_tilde vs d_eff Spearman", ""]
    if rho.empty:
        lines.append("insufficient n")
    else:
        for _, row in rho.iterrows():
            lines.append(f"- `{row['pair']}`: rho={row['rho']:.3g}, p={row['p']:.3g}, n={int(row['n'])}")
    lines += [
        "",
        "If cohort d_eff weakens but H_tilde remains separated, spread-richness is not only a participation-ratio artifact.",
        "If both collapse, the subject-frame shape result is more frame/normalization-dependent.",
        "",
    ]
    out = cfg.output_dir
    write_csv(out / "htilde_run_level.csv", runs)
    write_csv(out / "htilde_patient_primary.csv", patients)
    write_csv(out / "htilde_missingness_by_cpc.csv", missing)
    write_csv(out / "htilde_contrasts.csv", contrasts)
    write_csv(out / "htilde_spearman.csv", rho)
    (out / "htilde_part1.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(
        out / "htilde_part1_manifest.json",
        {"experiment": "COMA-H2-COHORT-001", "part2_opened": False, "confirmatory": False},
    )
    print(f"wrote {out / 'htilde_part1.md'}", flush=True)
    print(missing.to_string(index=False), flush=True)
    if not contrasts.empty:
        print(contrasts[["family", "metric", "n_cpc1", "n_cpc5", "cohens_d_cpc1_minus_cpc5", "mannwhitney_p"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
