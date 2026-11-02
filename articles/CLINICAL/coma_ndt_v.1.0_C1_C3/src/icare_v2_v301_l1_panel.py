"""Part1 L0/L1 CPC coverage audit, then CPC1 vs CPC5 contrasts.

Frozen panel follows sciencelead/sl_001.md and sl_002.md. Missingness by
outcome is reported before metric contrasts. This is exploratory discovery
on bundle 20260917_194039. It does not license Family B, Ito, or part2.
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
from icare_v2_outcome_contrast_analysis import _apply_family_fdr, _contrast_row

EPS = 1e-12

# Primary L1 family (sl_002). Directional predictions are pre-frozen, not selected
# from these data.
PRIMARY_L1 = (
    ("d_eff_a_level1_median", "A_breadth", "CPC1 > CPC5"),
    ("neighbor_separation_rate_level1_median", "B_separation", "CPC1 < CPC5"),
    ("neighbor_gain_q90_level1_median", "C_gain_q90", "CPC1 < CPC5"),
    ("b_norm_pooled_level1_median", "b_norm", "no directional preregistration"),
    ("history_predictive_gain_level1_median", "history_gain", "no directional preregistration"),
)
L0_ANCHORS = (
    ("realized_speed_level0_median", "speed", "descriptive anchor"),
    ("turning_rate_level0_median", "turning", "no directional preregistration"),
)
SECONDARY_L1 = (
    ("f_perp_crossfit_level1_median", "D_f_perp", "CPC1 > CPC5; analysis-owned from crossfit b_hat + a_hat"),
    ("b_norm_crossfit_level1_median", "b_norm_crossfit", "robustness vs pooled"),
    ("cloud_volume_change_rate_level1_median", "cloud_volume", "not in primary family"),
)

L1_COMMON_FLAGS = (
    "elig_d_eff_a_level1",
    "elig_b_norm_pooled_level1",
    "elig_neighbor_separation_rate_level1",
    "elig_neighbor_gain_q90_level1",
    "elig_history_predictive_gain_level1",
)


def _s(value: Any) -> str | None:
    text = str(as_scalar(value)) if value is not None else None
    return text if text not in {"", "None", "nan"} else None


def _status(handle: h5py.File, path: str) -> str:
    if path not in handle:
        return "missing"
    group = handle[path]
    if "computation_status" in group:
        return _s(as_scalar(group["computation_status"][()])) or "not_recorded"
    return "not_recorded"


def _series(handle: h5py.File, group: str, name: str) -> np.ndarray | None:
    path = f"{group}/series/{name}"
    if path not in handle:
        return None
    return np.asarray(handle[path][:])


def _valid_mask(handle: h5py.File, group: str, n: int) -> np.ndarray:
    raw = _series(handle, group, "valid")
    if raw is None:
        return np.ones(n, dtype=bool)
    mask = np.asarray(raw).reshape(-1)[:n] == 1
    if mask.size < n:
        out = np.zeros(n, dtype=bool)
        out[: mask.size] = mask
        return out
    return mask


def _row_norm(arr: np.ndarray) -> np.ndarray:
    work = np.asarray(arr, dtype=float)
    if work.ndim == 1:
        return work
    return np.linalg.norm(work.reshape(work.shape[0], -1), axis=1)


def _median_valid(arr: np.ndarray | None, valid: np.ndarray | None = None) -> float:
    if arr is None:
        return float("nan")
    values = np.asarray(arr, dtype=float)
    if values.ndim > 1:
        values = _row_norm(values)
    if valid is not None:
        n = min(values.size, valid.size)
        values = np.where(valid[:n], values[:n], np.nan)
    return median_finite(values)


def _d_eff_median(a_hat: np.ndarray | None, valid: np.ndarray | None, eps: float) -> float:
    if a_hat is None or a_hat.ndim != 3 or a_hat.shape[-1] != 3:
        return float("nan")
    tensor = np.asarray(a_hat, dtype=float)
    finite = np.isfinite(tensor).all(axis=(1, 2))
    if valid is not None:
        n = min(finite.size, valid.size)
        finite = finite[:n] & np.asarray(valid[:n], dtype=bool)
        tensor = tensor[:n]
    evals = np.clip(np.linalg.eigvalsh(tensor), 0.0, None)
    d_total = evals.sum(axis=1)
    sq = np.square(evals).sum(axis=1)
    d_eff = np.where(sq > eps, np.square(d_total) / (sq + eps), np.nan)
    d_eff = np.where(finite, d_eff, np.nan)
    return median_finite(d_eff)


def _f_perp_median(a_hat: np.ndarray | None, b_hat: np.ndarray | None, eps: float) -> float:
    if a_hat is None or b_hat is None:
        return float("nan")
    tensor = np.asarray(a_hat, dtype=float)
    drift = np.asarray(b_hat, dtype=float)
    n = min(tensor.shape[0], drift.shape[0])
    tensor = tensor[:n]
    drift = drift[:n]
    finite = np.isfinite(tensor).all(axis=(1, 2)) & np.isfinite(drift).all(axis=1)
    evals = np.clip(np.linalg.eigvalsh(tensor), 0.0, None)
    d_total = evals.sum(axis=1)
    norm = np.linalg.norm(drift, axis=1)
    direction = drift / (norm[:, None] + eps)
    d_parallel = np.einsum("ni,nij,nj->n", direction, tensor, direction)
    f_perp = (d_total - d_parallel) / (d_total + eps)
    f_perp = np.where(finite & (norm > eps) & (d_total > 0), f_perp, np.nan)
    return median_finite(f_perp)


def extract_one(item: tuple[str, float]) -> dict[str, Any]:
    path, eps = item
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "stem": Path(path).stem,
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
            row["mndm_version"] = _s(handle.attrs.get("mndm_version"))

            dpath = "/dynamical_families/diffusion/v1"
            vpath = "/dynamical_families/drift/v1/realized_velocity_level0"
            pooled = "/dynamical_families/drift/v1/conditional_mean_rate_level1/pooled"
            cross = "/dynamical_families/drift/v1/conditional_mean_rate_level1/blocked_crossfit"
            sep = "/dynamical_families/amplification/v1/neighbor_separation_rate_level1"
            gain = "/dynamical_families/amplification/v1/neighbor_gain_q90_level1"
            cloud = "/dynamical_families/amplification/v1/cloud_volume_change_rate_level1"
            hist = "/dynamical_families/history/v1/history_predictive_gain_level1"
            turn = "/dynamical_families/turning/v1/turning_rate_level0"

            row["diffusion_status"] = _status(handle, dpath)
            row["realized_velocity_status"] = _status(handle, vpath)
            row["b_hat_pooled_status"] = _status(handle, pooled)
            row["b_hat_crossfit_status"] = _status(handle, cross)
            row["separation_status"] = _status(handle, sep)
            row["gain_q90_status"] = _status(handle, gain)
            row["history_status"] = _status(handle, hist)
            row["turning_status"] = _status(handle, turn)

            a_hat = _series(handle, dpath, "a_hat")
            a_valid = _valid_mask(handle, dpath, a_hat.shape[0]) if a_hat is not None else None
            dx_dt = _series(handle, vpath, "dx_dt")
            b_pooled = _series(handle, pooled, "b_hat")
            b_cross = _series(handle, cross, "b_hat")
            sep_s = _series(handle, sep, "neighbor_separation_rate")
            gain_s = _series(handle, gain, "neighbor_gain_q90")
            cloud_s = _series(handle, cloud, "cloud_volume_change_rate")
            hist_s = _series(handle, hist, "history_predictive_gain")
            turn_s = _series(handle, turn, "turning_rate")

            row["realized_speed_level0_median"] = _median_valid(
                dx_dt, _valid_mask(handle, vpath, dx_dt.shape[0]) if dx_dt is not None else None
            )
            row["turning_rate_level0_median"] = _median_valid(
                turn_s, _valid_mask(handle, turn, turn_s.shape[0]) if turn_s is not None else None
            )
            row["b_norm_pooled_level1_median"] = _median_valid(
                b_pooled, _valid_mask(handle, pooled, b_pooled.shape[0]) if b_pooled is not None else None
            )
            row["b_norm_crossfit_level1_median"] = _median_valid(
                b_cross, _valid_mask(handle, cross, b_cross.shape[0]) if b_cross is not None else None
            )
            row["d_eff_a_level1_median"] = _d_eff_median(a_hat, a_valid, eps)
            row["d_eff_a_stored_median"] = _median_valid(_series(handle, dpath, "d_diff"), a_valid)
            row["neighbor_separation_rate_level1_median"] = _median_valid(
                sep_s, _valid_mask(handle, sep, sep_s.shape[0]) if sep_s is not None else None
            )
            row["neighbor_gain_q90_level1_median"] = _median_valid(
                gain_s, _valid_mask(handle, gain, gain_s.shape[0]) if gain_s is not None else None
            )
            row["history_predictive_gain_level1_median"] = _median_valid(
                hist_s, _valid_mask(handle, hist, hist_s.shape[0]) if hist_s is not None else None
            )
            row["cloud_volume_change_rate_level1_median"] = _median_valid(
                cloud_s, _valid_mask(handle, cloud, cloud_s.shape[0]) if cloud_s is not None else None
            )
            row["f_perp_crossfit_level1_median"] = _f_perp_median(a_hat, b_cross, eps)
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    for name in (
        "realized_speed_level0_median",
        "turning_rate_level0_median",
        "b_norm_pooled_level1_median",
        "b_norm_crossfit_level1_median",
        "d_eff_a_level1_median",
        "neighbor_separation_rate_level1_median",
        "neighbor_gain_q90_level1_median",
        "history_predictive_gain_level1_median",
        "cloud_volume_change_rate_level1_median",
        "f_perp_crossfit_level1_median",
    ):
        row[f"elig_{name.replace('_median', '')}"] = bool(np.isfinite(row.get(name, float("nan"))))
    row["l1_common_eligible"] = all(bool(row.get(flag, False)) for flag in L1_COMMON_FLAGS)
    row["l1_crossfit_eligible"] = bool(row.get("elig_b_norm_crossfit_level1", False))
    return row


def _annotate(frame: pd.DataFrame, cfg) -> pd.DataFrame:
    out = frame.copy()
    hours = pd.to_numeric(out.get("run_midpoint_from_anchor_hours"), errors="coerce")
    out["time_bin_primary"] = [assign_time_bin(value, cfg.primary_scheme) for value in hours]
    out["in_primary_window"] = out["time_bin_primary"].eq(cfg.primary_window)
    out["contrast_group"] = [outcome_label(value, cfg) for value in out.get("cpc", [])]
    out["bundle_id"] = cfg.bundle_id
    out["confirmatory_status"] = cfg.confirmatory_status
    return out


def _missingness_row(frame: pd.DataFrame, flag: str, *, grain: str, window: str, cfg) -> dict[str, Any]:
    work = frame[frame["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    good = work[work["contrast_group"] == cfg.good_label]
    poor = work[work["contrast_group"] == cfg.poor_label]
    g_yes = int(good[flag].fillna(False).astype(bool).sum()) if flag in good else 0
    p_yes = int(poor[flag].fillna(False).astype(bool).sum()) if flag in poor else 0
    g_n = int(len(good))
    p_n = int(len(poor))
    table = np.array([[g_yes, g_n - g_yes], [p_yes, p_n - p_yes]], dtype=int)
    fisher_p = float("nan")
    if table.min() >= 0 and table.sum() > 0 and (table > 0).any():
        try:
            fisher_p = float(stats.fisher_exact(table)[1])
        except ValueError:
            pass
    g_rate = g_yes / g_n if g_n else float("nan")
    p_rate = p_yes / p_n if p_n else float("nan")
    return {
        "grain": grain,
        "window": window,
        "flag": flag,
        "n_cpc1": g_n,
        "n_cpc5": p_n,
        "n_cpc1_eligible": g_yes,
        "n_cpc5_eligible": p_yes,
        "rate_cpc1": g_rate,
        "rate_cpc5": p_rate,
        "rate_cpc1_minus_cpc5": (g_rate - p_rate) if np.isfinite(g_rate) and np.isfinite(p_rate) else float("nan"),
        "fisher_p": fisher_p,
    }


def _audit_missingness(runs: pd.DataFrame, patients: pd.DataFrame, cfg) -> pd.DataFrame:
    flags = (
        "l1_common_eligible",
        "l1_crossfit_eligible",
        *L1_COMMON_FLAGS,
        "elig_realized_speed_level0",
        "elig_turning_rate_level0",
        "elig_f_perp_crossfit_level1",
    )
    rows = []
    for window, subset in (
        ("all_runs", runs),
        ("primary_window", runs[runs["in_primary_window"]]),
    ):
        for flag in flags:
            if flag in subset.columns:
                rows.append(_missingness_row(subset, flag, grain="recording", window=window, cfg=cfg))
    for flag in flags:
        if flag in patients.columns:
            rows.append(_missingness_row(patients, flag, grain="subject_primary", window=cfg.primary_window, cfg=cfg))
    return pd.DataFrame(rows)


def _patient_primary(runs: pd.DataFrame, cfg) -> pd.DataFrame:
    work = runs[runs["in_primary_window"] & runs["contrast_group"].isin([cfg.good_label, cfg.poor_label])].copy()
    if work.empty:
        return work
    metrics = [
        "realized_speed_level0_median",
        "turning_rate_level0_median",
        "b_norm_pooled_level1_median",
        "b_norm_crossfit_level1_median",
        "d_eff_a_level1_median",
        "neighbor_separation_rate_level1_median",
        "neighbor_gain_q90_level1_median",
        "history_predictive_gain_level1_median",
        "cloud_volume_change_rate_level1_median",
        "f_perp_crossfit_level1_median",
        "d_eff_a_stored_median",
    ]
    agg: dict[str, Any] = {
        "cpc": ("cpc", "first"),
        "contrast_group": ("contrast_group", "first"),
        "outcome": ("outcome", "first"),
        "hospital": ("hospital", "first"),
        "ttm": ("ttm", "first"),
        "n_runs": ("source_h5", "nunique"),
        "l1_common_eligible": ("l1_common_eligible", "any"),
        "l1_crossfit_eligible": ("l1_crossfit_eligible", "any"),
    }
    for flag in L1_COMMON_FLAGS:
        if flag in work.columns:
            agg[flag] = (flag, "any")
    for extra in ("elig_realized_speed_level0", "elig_turning_rate_level0", "elig_f_perp_crossfit_level1"):
        if extra in work.columns:
            agg[extra] = (extra, "any")
    for metric in metrics:
        agg[metric] = (metric, "median")
    return work.groupby("subject_id", as_index=False).agg(**agg)


def _fmt_rate(row: pd.Series) -> str:
    def _one(n_yes: int, n: int, rate: float) -> str:
        if n <= 0:
            return "n/a"
        return f"{int(n_yes)}/{int(n)} ({rate:.1%})"

    return f"{_one(row['n_cpc1_eligible'], row['n_cpc1'], row['rate_cpc1'])} vs {_one(row['n_cpc5_eligible'], row['n_cpc5'], row['rate_cpc5'])}"


def _render(missing: pd.DataFrame, contrasts: pd.DataFrame, *, cfg, n_runs: int, n_patients: int) -> str:
    lines = [
        "# I-CARE part1 v3.0.1 L0/L1 CPC coverage and contrasts",
        "",
        f"Bundle `{cfg.bundle_id}`. Status: `{cfg.confirmatory_status}`.",
        f"Recordings extracted: {n_runs}. Primary-window CPC1/CPC5 subjects: {n_patients}.",
        "",
        "Panel frozen in `sciencelead/sl_001.md` and `sl_002.md` before this readout.",
        "Missingness is the first result. Metric contrasts do not license Family B, Ito,",
        "or a confirmatory claim. Part2 is locked out of this script.",
        "",
        "## 1. Coverage by CPC (before metric values)",
        "",
        "Recording-level rates use files with CPC 1 or 5. Subject-level eligibility is",
        "true if any primary-window run for that subject is eligible.",
        "",
        "| Grain | Window | Flag | CPC1 vs CPC5 eligible | Rate difference | Fisher p |",
        "| --- | --- | --- | --- | ---: | ---: |",
    ]
    if missing.empty:
        lines.append("| - | - | - | empty | n/a | n/a |")
    else:
        show = missing[
            missing["flag"].isin(
                [
                    "l1_common_eligible",
                    "l1_crossfit_eligible",
                    "elig_f_perp_crossfit_level1",
                    "elig_realized_speed_level0",
                    "elig_turning_rate_level0",
                ]
            )
        ]
        for _, row in show.iterrows():
            diff = row["rate_cpc1_minus_cpc5"]
            diff_s = "n/a" if not np.isfinite(diff) else f"{diff:+.1%}"
            p = row["fisher_p"]
            p_s = "n/a" if not np.isfinite(p) else f"{p:.3g}"
            lines.append(
                f"| {row['grain']} | {row['window']} | `{row['flag']}` | {_fmt_rate(row)} | {diff_s} | {p_s} |"
            )
    lines += [
        "",
        "If CPC1 and CPC5 eligibility stay within a couple of percentage points, the L1",
        "surface can be treated as approximately whole-cohort. A large gap would mean",
        "informative missingness and would block naive CPC contrasts.",
        "",
        "## 2. Frozen panel",
        "",
        "Primary L1 (FDR within this family): `d_eff_a`, `neighbor_separation_rate`,",
        "`neighbor_gain_q90`, `b_norm` (pooled), `history_predictive_gain`.",
        "",
        "L0 anchors: realized speed and turning rate. Secondary: `f_perp` from crossfit",
        "`b_hat` + `a_hat` (not stored `A_bD`, not `/mnps_3d_dot`).",
        "",
        "## 3. CPC1 vs CPC5 contrasts (subject median in 0-12h)",
        "",
        "| Family | Hypothesis | Metric | Prediction | n CPC1 | n CPC5 | CPC1 median | CPC5 median | d | delta | MW p | BH q |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    if contrasts.empty:
        lines.append("| - | - | - | - | - | - | - | - | - | - | - | - |")
    else:
        for _, row in contrasts.iterrows():
            q = row.get("bh_q_within_family", float("nan"))
            q_s = "-" if not np.isfinite(q) else f"{q:.3g}"
            lines.append(
                f"| {row['family']} | {row['hypothesis']} | `{row['metric']}` | {row['prediction']} | "
                f"{int(row['n_cpc1'])} | {int(row['n_cpc5'])} | {row['cpc1_median']:.4g} | "
                f"{row['cpc5_median']:.4g} | {row['cohens_d_cpc1_minus_cpc5']:.3g} | "
                f"{row['cliffs_delta_cpc1_minus_cpc5']:.3g} | {row['mannwhitney_p']:.3g} | {q_s} |"
            )
    lines += [
        "",
        "## How to read this",
        "",
        "- Subject grain, primary 0-12h window, CPC1 vs CPC5 only.",
        "- BH FDR applies only inside the five-metric primary L1 family.",
        "- `f_perp` is secondary and uses embargoed chart-drift, not Itô b.",
        "- One-step L3 alpha and Jacobian alpha are out of this panel.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    out = cfg.output_dir
    paths = discover_h5_files(cfg.raw_root, subject_allowlist=cfg.subject_allowlist, limit_h5=cfg.limit_h5)
    print(f"{cfg.bundle_id}: extracting {len(paths)} files", flush=True)
    rows = parallel_map(extract_one, [(str(p), cfg.diffusion_eps) for p in paths], workers=cfg.workers, desc="l1-panel")
    runs = _annotate(pd.DataFrame(rows), cfg)
    patients = _patient_primary(runs, cfg)
    missing = _audit_missingness(runs, patients, cfg)
    contrast_rows = []
    for metric, hyp, pred in PRIMARY_L1:
        contrast_rows.append(_contrast_row(patients, metric, cfg=cfg, family="l1_primary", hypothesis=hyp, prediction=pred))
    for metric, hyp, pred in L0_ANCHORS:
        contrast_rows.append(_contrast_row(patients, metric, cfg=cfg, family="l0_anchor", hypothesis=hyp, prediction=pred))
    for metric, hyp, pred in SECONDARY_L1:
        contrast_rows.append(_contrast_row(patients, metric, cfg=cfg, family="l1_secondary", hypothesis=hyp, prediction=pred))
    contrasts = pd.DataFrame(contrast_rows)
    if not contrasts.empty:
        contrasts = _apply_family_fdr(contrasts, "l1_primary")
        contrasts["bh_alpha"] = cfg.bh_alpha
        primary = contrasts["family"] == "l1_primary"
        contrasts["bh_significant"] = np.where(
            primary & contrasts["bh_q_within_family"].notna(),
            contrasts["bh_q_within_family"] < cfg.bh_alpha,
            pd.NA,
        )
    write_csv(out / "l1_panel_run_level.csv", runs)
    write_csv(out / "l1_panel_patient_primary.csv", patients)
    write_csv(out / "l1_panel_missingness_by_cpc.csv", missing)
    write_csv(out / "l1_panel_contrasts.csv", contrasts)
    md = _render(missing, contrasts, cfg=cfg, n_runs=int(len(runs)), n_patients=int(len(patients)))
    (out / "l1_panel_contrasts.md").write_text(md, encoding="utf-8")
    write_json(
        out / "l1_panel_manifest.json",
        {
            "bundle_id": cfg.bundle_id,
            "confirmatory_status": cfg.confirmatory_status,
            "n_runs": int(len(runs)),
            "n_read_ok": int(runs["read_ok"].sum()) if not runs.empty else 0,
            "n_primary_cpc15_subjects": int(len(patients)),
            "n_cpc1": int((patients["contrast_group"] == cfg.good_label).sum()) if not patients.empty else 0,
            "n_cpc5": int((patients["contrast_group"] == cfg.poor_label).sum()) if not patients.empty else 0,
            "note": "Exploratory discovery. Missingness audited before interpreting metric contrasts.",
        },
    )
    print(f"wrote {out / 'l1_panel_contrasts.md'}", flush=True)
    if not missing.empty:
        key = missing[(missing["flag"] == "l1_common_eligible") & (missing["grain"] == "recording")]
        print(key.to_string(index=False), flush=True)
    if not contrasts.empty:
        print(contrasts[["family", "hypothesis", "metric", "n_cpc1", "n_cpc5", "mannwhitney_p"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
