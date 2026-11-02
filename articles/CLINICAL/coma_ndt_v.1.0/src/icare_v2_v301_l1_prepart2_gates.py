"""Part1 pre-part2 gates from sciencelead/sl_004.md.

Closes four technical gates on the 3.0.1 discovery dump without opening
part2: cohort-anchor sensitivity, G90 floor/support QC, temporal/support
balance, and artifact/signal-quality association. Freezes confirmatory
endpoints as d_eff_a + G90.
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
from sklearn.neighbors import NearestNeighbors

from icare_v2_common import (
    add_common_args,
    as_scalar,
    assign_time_bin,
    discover_h5_files,
    median_finite,
    outcome_label,
    parallel_map,
    parse_run_stem,
    participant_meta_from_handle,
    resolve_pipeline_config,
    time_reference_from_handle,
    write_csv,
    write_json,
)
from icare_v2_outcome_contrast_analysis import _contrast_row
from icare_v2_v301_l1_panel import _annotate, _s

K = 20
MIN_NEIGH = 10
Q90 = 0.90
EPS = 1e-12
FLOOR_MULT = 10.0

CONFIRMATORY = (
    ("d_eff_a_level1_median", "A_breadth", "CPC1 > CPC5"),
    ("neighbor_gain_q90_level1_median", "C_gain_q90", "CPC1 < CPC5"),
)
SUPPORTIVE = (
    ("neighbor_separation_rate_level1_median", "B_separation", "CPC1 < CPC5; supportive, not confirmatory"),
)


def _series(handle: h5py.File, group: str, name: str) -> np.ndarray | None:
    path = f"{group}/series/{name}"
    if path not in handle:
        return None
    return np.asarray(handle[path][:])


def _lag1_knn(coords: np.ndarray, *, k: int = K) -> np.ndarray | None:
    work = np.asarray(coords, dtype=float)
    if work.ndim != 2 or work.shape[0] < k + 2:
        return None
    sources = np.arange(work.shape[0] - 1)
    x = work[sources]
    finite = np.isfinite(x).all(axis=1)
    if int(finite.sum()) < k + 1:
        return None
    valid_pos = np.flatnonzero(finite)
    valid_src = sources[finite]
    nn = NearestNeighbors(n_neighbors=min(k + 1, int(valid_src.size)), algorithm="kd_tree")
    nn.fit(x[finite])
    _, ind = nn.kneighbors(x[finite])
    out = np.full((work.shape[0], k), -1, dtype=int)
    for row, src in enumerate(valid_src):
        chosen: list[int] = []
        for j in ind[row]:
            neigh = int(valid_src[int(j)])
            if neigh == int(src):
                continue
            chosen.append(neigh)
            if len(chosen) >= k:
                break
        if chosen:
            out[int(src), : len(chosen)] = np.asarray(chosen, dtype=int)
    return out


def _pair_gains(coords: np.ndarray, neigh: np.ndarray, eps: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(coords, dtype=float)
    t = neigh.shape[0]
    g90 = np.full(t, np.nan)
    d0_med = np.full(t, np.nan)
    frac_floor = np.full(t, np.nan)
    n_pair = np.zeros(t, dtype=int)
    for src in range(t - 1):
        js = neigh[src]
        js = js[(js >= 0) & (js < t - 1) & (js != src)]
        if js.size < MIN_NEIGH:
            continue
        d0 = np.linalg.norm(x[src] - x[js], axis=1)
        d1 = np.linalg.norm(x[src + 1] - x[js + 1], axis=1)
        ok = np.isfinite(d0) & np.isfinite(d1)
        if int(ok.sum()) < MIN_NEIGH:
            continue
        d0 = d0[ok]
        d1 = d1[ok]
        g90[src] = float(np.quantile((d1 + eps) / (d0 + eps), Q90))
        d0_med[src] = float(np.median(d0))
        frac_floor[src] = float(np.mean(d0 <= FLOOR_MULT * eps))
        n_pair[src] = int(d0.size)
    return g90, d0_med, frac_floor, n_pair


def _local_deff(coords: np.ndarray, neigh: np.ndarray, dt: float, eps: float) -> np.ndarray:
    x = np.asarray(coords, dtype=float)
    t = neigh.shape[0]
    out = np.full(t, np.nan)
    if not np.isfinite(dt) or dt <= 0:
        return out
    for src in range(t - 1):
        js = neigh[src]
        js = js[(js >= 0) & (js < t - 1) & (js != src)]
        if js.size < MIN_NEIGH:
            continue
        inc = x[js + 1] - x[js]
        if not np.isfinite(inc).all():
            finite = np.isfinite(inc).all(axis=1)
            inc = inc[finite]
        if inc.shape[0] < MIN_NEIGH:
            continue
        inc = inc - inc.mean(axis=0)
        cov = (inc.T @ inc) / max(inc.shape[0] - 1, 1) / dt
        evals = np.clip(np.linalg.eigvalsh(cov), 0.0, None)
        total = float(evals.sum())
        sq = float(np.square(evals).sum())
        out[src] = float(total**2 / (sq + eps)) if sq > eps else float("nan")
    return out


def _feature_median(handle: h5py.File, token: str) -> float:
    if "/features_raw/names" not in handle or "/features_raw/values" not in handle:
        return float("nan")
    names = [
        item.decode("utf-8", errors="replace") if isinstance(item, (bytes, np.bytes_)) else str(item)
        for item in handle["/features_raw/names"][:]
    ]
    if token not in names:
        return float("nan")
    values = np.asarray(handle["/features_raw/values"][:, names.index(token)], dtype=float)
    return median_finite(values)


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
            row["primary_coordinate_layer"] = _s(handle.attrs.get("primary_coordinate_layer"))
            row["primary_coordinate_contract"] = _s(handle.attrs.get("primary_coordinate_contract"))
            family_layer = "/dynamical_families/amplification/v1/neighbor_gain_q90_level1/provenance/coordinate_layer"
            row["family_coordinate_layer"] = _s(as_scalar(handle[family_layer][()]) if family_layer in handle else None)
            a_sem = "/dynamical_families/diffusion/v1/summary/a_semantics"
            row["a_semantics"] = _s(as_scalar(handle[a_sem][()]) if a_sem in handle else None)
            eps = float(as_scalar(handle["/dynamical_families/amplification/v1/neighbor_gain_q90_level1/summary/distance_epsilon"][()])) if "/dynamical_families/amplification/v1/neighbor_gain_q90_level1/summary/distance_epsilon" in handle else EPS
            row["distance_epsilon"] = eps
            stored_g = _series(handle, "/dynamical_families/amplification/v1/neighbor_gain_q90_level1", "neighbor_gain_q90")
            stored_n = _series(handle, "/dynamical_families/amplification/v1/neighbor_gain_q90_level1", "n_neighbor_pairs")
            stored_d = _series(handle, "/dynamical_families/diffusion/v1", "d_diff")
            stored_support = _series(handle, "/dynamical_families/diffusion/v1", "support_n")
            row["neighbor_gain_q90_level1_median"] = median_finite(stored_g)
            row["d_eff_a_level1_median"] = median_finite(stored_d)
            row["n_neighbor_pairs_median"] = median_finite(stored_n)
            row["diffusion_support_n_median"] = median_finite(stored_support)
            dt_path = "/dynamical_families/diffusion/v1/summary/nominal_dt_sec"
            row["nominal_dt_sec"] = float(as_scalar(handle[dt_path][()])) if dt_path in handle else float("nan")
            ninc = "/dynamical_families/diffusion/v1/summary/n_increment_pairs"
            row["n_increment_pairs"] = float(as_scalar(handle[ninc][()])) if ninc in handle else float("nan")
            cross = "/dynamical_families/drift/v1/conditional_mean_rate_level1/blocked_crossfit/series/source_idx"
            row["crossfit_source_n"] = int(handle[cross].shape[0]) if cross in handle else 0
            if "/qc/windows/qc_ok_eeg" in handle:
                eeg = np.asarray(handle["/qc/windows/qc_ok_eeg"][:]).reshape(-1)
                row["qc_ok_eeg_frac_not_assessed"] = float(np.mean(eeg == -1)) if eeg.size else float("nan")
                row["qc_ok_eeg_frac_pass"] = float(np.mean(eeg == 1)) if eeg.size else float("nan")
            else:
                row["qc_ok_eeg_frac_not_assessed"] = float("nan")
                row["qc_ok_eeg_frac_pass"] = float("nan")
            if "/coverage/axis_fraction" in handle:
                frac = np.asarray(handle["/coverage/axis_fraction"][:], dtype=float)
                row["min_axis_fraction"] = float(np.nanmin(frac)) if frac.size else float("nan")
            else:
                row["min_axis_fraction"] = float("nan")
            row["eeg_gamma_median"] = _feature_median(handle, "eeg_gamma")
            row["eeg_highfreq_30_45_median"] = _feature_median(handle, "eeg_highfreq_power_30_45")
            row["eeg_beta_median"] = _feature_median(handle, "eeg_beta")
            xs = np.asarray(handle["/coords_3d_subject_anchored/values"][:], dtype=float) if "/coords_3d_subject_anchored/values" in handle else None
            xc = np.asarray(handle["/coords_3d_cohort_anchored/values"][:], dtype=float) if "/coords_3d_cohort_anchored/values" in handle else None
            neigh = _lag1_knn(xs) if xs is not None else None
            if neigh is not None and xs is not None:
                g_s, d0_s, floor_s, n_s = _pair_gains(xs, neigh, eps)
                row["g90_subject_recompute_median"] = median_finite(g_s)
                row["d0_over_eps_median"] = median_finite(d0_s / max(eps, 1e-30))
                row["d0_floor_frac"] = median_finite(floor_s)
                row["g90_n_pairs_recompute_median"] = median_finite(n_s)
                if stored_g is not None:
                    n = min(len(g_s), len(stored_g))
                    mask = np.isfinite(g_s[:n]) & np.isfinite(np.asarray(stored_g[:n], dtype=float))
                    row["g90_recompute_mae"] = float(np.mean(np.abs(g_s[:n][mask] - np.asarray(stored_g[:n], dtype=float)[mask]))) if mask.any() else float("nan")
                dt = row["nominal_dt_sec"] if np.isfinite(row["nominal_dt_sec"]) else 4.0
                row["d_eff_subject_recompute_median"] = median_finite(_local_deff(xs, neigh, dt, eps))
            else:
                row["g90_subject_recompute_median"] = float("nan")
                row["d0_over_eps_median"] = float("nan")
                row["d0_floor_frac"] = float("nan")
                row["g90_n_pairs_recompute_median"] = float("nan")
                row["g90_recompute_mae"] = float("nan")
                row["d_eff_subject_recompute_median"] = float("nan")
            if neigh is not None and xc is not None:
                g_c, _, _, _ = _pair_gains(xc, neigh, eps)
                dt = row["nominal_dt_sec"] if np.isfinite(row["nominal_dt_sec"]) else 4.0
                # Same neighbor identities, distances in the cohort frame.
                row["g90_cohort_samepair_median"] = median_finite(g_c)
                row["d_eff_cohort_samepair_median"] = median_finite(_local_deff(xc, neigh, dt, eps))
                neigh_c = _lag1_knn(xc)
                if neigh_c is not None:
                    g_cc, _, _, _ = _pair_gains(xc, neigh_c, eps)
                    row["g90_cohort_reknn_median"] = median_finite(g_cc)
                    row["d_eff_cohort_reknn_median"] = median_finite(_local_deff(xc, neigh_c, dt, eps))
                else:
                    row["g90_cohort_reknn_median"] = float("nan")
                    row["d_eff_cohort_reknn_median"] = float("nan")
            else:
                row["g90_cohort_samepair_median"] = float("nan")
                row["d_eff_cohort_samepair_median"] = float("nan")
                row["g90_cohort_reknn_median"] = float("nan")
                row["d_eff_cohort_reknn_median"] = float("nan")
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _patient_gate(runs: pd.DataFrame, cfg) -> pd.DataFrame:
    work = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    if work.empty:
        return work
    metrics = [
        "neighbor_gain_q90_level1_median",
        "d_eff_a_level1_median",
        "neighbor_separation_rate_level1_median",
        "g90_subject_recompute_median",
        "d_eff_subject_recompute_median",
        "g90_cohort_samepair_median",
        "d_eff_cohort_samepair_median",
        "g90_cohort_reknn_median",
        "d_eff_cohort_reknn_median",
        "d0_over_eps_median",
        "d0_floor_frac",
        "n_neighbor_pairs_median",
        "diffusion_support_n_median",
        "n_increment_pairs",
        "nominal_dt_sec",
        "crossfit_source_n",
        "min_axis_fraction",
        "eeg_gamma_median",
        "eeg_highfreq_30_45_median",
        "qc_ok_eeg_frac_not_assessed",
        "g90_recompute_mae",
    ]
    agg: dict[str, Any] = {
        "cpc": ("cpc", "first"),
        "contrast_group": ("contrast_group", "first"),
        "hospital": ("hospital", "first"),
        "ttm": ("ttm", "first"),
        "n_runs": ("source_h5", "nunique"),
    }
    for metric in metrics:
        if metric in work.columns:
            agg[metric] = (metric, "median")
    return work.groupby("subject_id", as_index=False).agg(**agg)


def _holm(p_values: list[float]) -> list[float]:
    p = np.asarray(p_values, dtype=float)
    m = p.size
    out = np.full(m, np.nan)
    order = np.argsort(p)
    running = 0.0
    for rank, idx in enumerate(order):
        if not np.isfinite(p[idx]):
            continue
        adj = min(1.0, float(p[idx]) * (m - rank))
        running = max(running, adj)
        out[idx] = running
    return [float(v) for v in out]


def _spearman(frame: pd.DataFrame, a: str, b: str) -> dict[str, float]:
    x = pd.to_numeric(frame[a], errors="coerce")
    y = pd.to_numeric(frame[b], errors="coerce")
    mask = x.notna() & y.notna()
    if int(mask.sum()) < 10:
        return {"n": float(mask.sum()), "rho": float("nan"), "p": float("nan")}
    rho, p = stats.spearmanr(x[mask], y[mask])
    return {"n": float(mask.sum()), "rho": float(rho), "p": float(p)}


def _hour_mix(runs: pd.DataFrame, cfg) -> pd.DataFrame:
    work = runs[runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    work["hour_bin"] = [
        assign_time_bin(value, "hourly_12h") for value in pd.to_numeric(work.get("run_midpoint_from_anchor_hours"), errors="coerce")
    ]
    rows = []
    for hour, block in work.groupby("hour_bin"):
        for metric, hyp, pred in CONFIRMATORY:
            if metric not in block.columns:
                continue
            row = _contrast_row(block, metric, cfg=cfg, family="hourly_audit", hypothesis=hyp, prediction=pred)
            row["hour_bin"] = hour
            rows.append(row)
    return pd.DataFrame(rows)


def _render(*, cfg, provenance: dict, recon: dict, missing_support: pd.DataFrame, contrasts: pd.DataFrame, hourly: pd.DataFrame, assoc: dict) -> str:
    lines = [
        "# Part1 pre-part2 gates (sl_004)",
        "",
        f"Bundle `{cfg.bundle_id}`. Confirmatory endpoints frozen: `d_eff_a` and `G_90`.",
        "Median separation stays supportive. Cloud-volume stays exploratory.",
        "Aggregation remains subject-median in 0-12h. Part2 is not opened.",
        "",
        "## Provenance freeze",
        "",
        f"- config: `{provenance.get('config_yaml')}`",
        f"- config digest: `{provenance.get('config_digest')}`",
        f"- git_rev: `{provenance.get('git_rev')}`",
        f"- q={Q90}, k={K}, eps={EPS}, neighborhood among lag-1 sources",
        f"- family coordinate layer: `{provenance.get('family_coordinate_layer')}`",
        f"- file primary coordinate layer: `{provenance.get('primary_coordinate_layer')}`",
        f"- a_semantics: `{provenance.get('a_semantics')}` (raw increment covariance, not residual innovation)",
        "",
        "## Gate 1. Cohort-anchor sensitivity",
        "",
        f"G90 subject recompute vs stored MAE (median across files): `{recon.get('g90_mae_median'):.3g}`.",
        "",
        "| Metric | Frame | n CPC1 | n CPC5 | CPC1 med | CPC5 med | d | MW p | Holm p |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
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
        "Same-pair cohort frame keeps neighbor identities from the subject-anchored kNN",
        "and re-evaluates distances in `coords_3d_cohort_anchored`. Re-kNN reselects",
        "neighbors in the cohort frame. Stored families remain the discovery objects.",
        "",
        "## Gate 2. G90 floor / support",
        "",
        "| Flag | CPC1 vs CPC5 median | d | MW p |",
        "| --- | --- | ---: | ---: |",
    ]
    for _, row in missing_support.iterrows():
        lines.append(
            f"| `{row['metric']}` | {row['cpc1_median']:.4g} vs {row['cpc5_median']:.4g} | "
            f"{row['cohens_d_cpc1_minus_cpc5']:.3g} | {row['mannwhitney_p']:.3g} |"
        )
    lines += [
        "",
        "## Gate 3. Hour mix (audit only; 0-12h median stays frozen)",
        "",
        "| Hour | Metric | n CPC1 | n CPC5 | d | MW p |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    if hourly.empty:
        lines.append("| - | - | - | - | - | - |")
    else:
        for _, row in hourly.iterrows():
            lines.append(
                f"| {row['hour_bin']} | `{row['metric']}` | {int(row['n_cpc1'])} | {int(row['n_cpc5'])} | "
                f"{row['cohens_d_cpc1_minus_cpc5']:.3g} | {row['mannwhitney_p']:.3g} |"
            )
    lines += [
        "",
        "## Gate 4. Artifact / signal (CPC-blind associations)",
        "",
        f"- qc_ok_eeg not-assessed fraction (median file): `{assoc.get('qc_not_assessed_median'):.3g}`",
        f"- G90 vs eeg_gamma Spearman rho={assoc['g90_gamma']['rho']:.3g}, p={assoc['g90_gamma']['p']:.3g}",
        f"- G90 vs highfreq 30-45 rho={assoc['g90_hf']['rho']:.3g}, p={assoc['g90_hf']['p']:.3g}",
        f"- G90 vs min_axis_fraction rho={assoc['g90_cov']['rho']:.3g}, p={assoc['g90_cov']['p']:.3g}",
        f"- G90 CPC contrast after dropping gamma > file-level 99th percentile: d={assoc.get('g90_d_after_gamma_clip')}, MW p={assoc.get('g90_p_after_gamma_clip')}",
        "",
        "## Freeze for part2",
        "",
        "- Confirmatory pair: `d_eff_a_level1` (CPC1 > CPC5) and `neighbor_gain_q90_level1` (CPC1 < CPC5), Holm-adjusted.",
        "- Supportive: median `neighbor_separation_rate_level1`.",
        "- Exploratory: cloud volume, `||b||`, history, `f_perp`.",
        "- Grain: subject median inside 0-12h. Do not pick an hour from this audit.",
        "- Language: broader **conditional increment-covariance geometry**, not innovation geometry.",
        "",
    ]
    return "\n".join(lines)


def _load_provenance(raw_root: Path, sample_row: pd.Series | None) -> dict[str, Any]:
    root = Path(raw_root)
    command = (root / "command_used.txt").read_text(encoding="utf-8") if (root / "command_used.txt").exists() else ""
    manifest = json.loads((root / "run_manifest.json").read_text(encoding="utf-8")) if (root / "run_manifest.json").exists() else {}
    config = manifest.get("config") or {}
    env = manifest.get("environment") or {}
    return {
        "config_yaml": "config_ingest_physionet_i-care_2_1_part1_0_12h_dynamical_families.yaml",
        "config_digest": config.get("digest_sha256"),
        "git_rev": env.get("git_rev"),
        "command": command.strip().splitlines()[3] if command else None,
        "family_coordinate_layer": None if sample_row is None else sample_row.get("family_coordinate_layer"),
        "primary_coordinate_layer": None if sample_row is None else sample_row.get("primary_coordinate_layer"),
        "a_semantics": None if sample_row is None else sample_row.get("a_semantics"),
        "q": Q90,
        "k": K,
        "eps": EPS,
        "aggregation": "subject_median_0_12h",
        "confirmatory_endpoints": ["d_eff_a_level1", "neighbor_gain_q90_level1"],
        "supportive_endpoints": ["neighbor_separation_rate_level1"],
        "exploratory_endpoints": ["cloud_volume_change_rate_level1", "b_norm_pooled_level1", "history_predictive_gain_level1", "f_perp_crossfit_level1"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    paths = discover_h5_files(cfg.raw_root, subject_allowlist=cfg.subject_allowlist, limit_h5=cfg.limit_h5)
    print(f"{cfg.bundle_id}: gate extract {len(paths)} files", flush=True)
    rows = parallel_map(extract_one, [str(p) for p in paths], workers=cfg.workers, desc="l1-gates")
    runs = _annotate(pd.DataFrame(rows), cfg)
    panel_path = cfg.output_dir / "l1_panel_run_level.csv"
    if panel_path.exists():
        panel = pd.read_csv(panel_path)
        keep = ["source_h5", "neighbor_separation_rate_level1_median"]
        extra = [c for c in keep if c in panel.columns and c != "source_h5"]
        if extra:
            runs = runs.merge(panel[["source_h5", *extra]], on="source_h5", how="left")
    patients = _patient_gate(runs, cfg)
    contrast_specs = [
        ("stored", "d_eff_a_level1_median", "A_breadth", "CPC1 > CPC5"),
        ("stored", "neighbor_gain_q90_level1_median", "C_gain_q90", "CPC1 < CPC5"),
        ("cohort_samepair", "d_eff_cohort_samepair_median", "A_breadth", "CPC1 > CPC5"),
        ("cohort_samepair", "g90_cohort_samepair_median", "C_gain_q90", "CPC1 < CPC5"),
        ("cohort_reknn", "d_eff_cohort_reknn_median", "A_breadth", "CPC1 > CPC5"),
        ("cohort_reknn", "g90_cohort_reknn_median", "C_gain_q90", "CPC1 < CPC5"),
    ]
    contrast_rows = []
    for family, metric, hyp, pred in contrast_specs:
        if metric in patients.columns:
            row = _contrast_row(patients, metric, cfg=cfg, family=family, hypothesis=hyp, prediction=pred)
            contrast_rows.append(row)
    contrasts = pd.DataFrame(contrast_rows)
    if not contrasts.empty:
        for family in contrasts["family"].unique():
            idx = contrasts.index[contrasts["family"] == family].tolist()
            holm = _holm([float(contrasts.loc[i, "mannwhitney_p"]) for i in idx])
            for i, value in zip(idx, holm):
                contrasts.loc[i, "holm_p"] = value
    support_metrics = (
        ("d0_over_eps_median", "d0/eps"),
        ("d0_floor_frac", "d0<=10eps"),
        ("n_neighbor_pairs_median", "n_neighbor_pairs"),
        ("diffusion_support_n_median", "diffusion_support_n"),
        ("n_increment_pairs", "n_increment_pairs"),
        ("nominal_dt_sec", "dt"),
        ("crossfit_source_n", "crossfit_source_n"),
        ("min_axis_fraction", "min_axis_fraction"),
    )
    support_rows = []
    for metric, _name in support_metrics:
        if metric in patients.columns:
            support_rows.append(_contrast_row(patients, metric, cfg=cfg, family="support_qc", hypothesis=_name, prediction="CPC1 ~ CPC5"))
    support = pd.DataFrame(support_rows)
    hourly = _hour_mix(runs, cfg)
    primary_runs = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])]
    assoc = {
        "qc_not_assessed_median": float(pd.to_numeric(primary_runs.get("qc_ok_eeg_frac_not_assessed"), errors="coerce").median()) if not primary_runs.empty else float("nan"),
        "g90_gamma": _spearman(primary_runs, "neighbor_gain_q90_level1_median", "eeg_gamma_median"),
        "g90_hf": _spearman(primary_runs, "neighbor_gain_q90_level1_median", "eeg_highfreq_30_45_median"),
        "g90_cov": _spearman(primary_runs, "neighbor_gain_q90_level1_median", "min_axis_fraction"),
    }
    gamma = pd.to_numeric(patients.get("eeg_gamma_median"), errors="coerce")
    clip = float(gamma.quantile(0.99)) if gamma.notna().any() else float("nan")
    clipped = patients[~(gamma > clip)].copy() if np.isfinite(clip) else patients
    g90_clip = _contrast_row(clipped, "neighbor_gain_q90_level1_median", cfg=cfg, family="artifact_clip", hypothesis="C_gain_q90", prediction="CPC1 < CPC5")
    assoc["g90_d_after_gamma_clip"] = g90_clip["cohens_d_cpc1_minus_cpc5"]
    assoc["g90_p_after_gamma_clip"] = g90_clip["mannwhitney_p"]
    assoc["gamma_clip"] = clip
    recon = {
        "g90_mae_median": float(pd.to_numeric(runs.get("g90_recompute_mae"), errors="coerce").median()) if "g90_recompute_mae" in runs else float("nan"),
    }
    sample = runs.iloc[0] if not runs.empty else None
    provenance = _load_provenance(cfg.raw_root, sample)
    out = cfg.output_dir
    write_csv(out / "l1_gate_run_level.csv", runs)
    write_csv(out / "l1_gate_patient_primary.csv", patients)
    write_csv(out / "l1_gate_contrasts.csv", contrasts)
    write_csv(out / "l1_gate_support_contrasts.csv", support)
    write_csv(out / "l1_gate_hourly_audit.csv", hourly)
    write_json(out / "l1_confirmatory_lock.json", provenance)
    md = _render(cfg=cfg, provenance=provenance, recon=recon, missing_support=support, contrasts=contrasts, hourly=hourly, assoc=assoc)
    (out / "l1_prepart2_gates.md").write_text(md, encoding="utf-8")
    write_json(out / "l1_prepart2_gates_manifest.json", {"n_runs": int(len(runs)), "n_patients": int(len(patients)), "recon": recon, "assoc": assoc})
    print(f"wrote {out / 'l1_prepart2_gates.md'}", flush=True)
    if not contrasts.empty:
        print(contrasts[["family", "metric", "n_cpc1", "n_cpc5", "cohens_d_cpc1_minus_cpc5", "mannwhitney_p"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
