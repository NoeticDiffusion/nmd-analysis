"""Coverage matrix for the MNPS/NMDM 3.0.1 I-CARE dump.

Counts how many H5 files have a group present, `computation_status=computed`,
and at least one finite numeric value for each metric. This is a measurement
inventory, not a CPC contrast and not an Itô/Family-B license.

Default bundle:
  data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260917_194039
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

from icare_v2_common import (
    ARTICLE_DIR,
    REPO_ROOT,
    as_scalar,
    discover_h5_files,
    parallel_map,
    parse_run_stem,
    write_csv,
    write_json,
)

DEFAULT_BUNDLE = (
    REPO_ROOT
    / "data"
    / "raw"
    / "neuralmanifolddynamics_physionet_icare_2_1_20260917_194039"
)
DEFAULT_OUT = ARTICLE_DIR / "results" / "v3_0_1"

FAMILY_ORDER = (
    "chart",
    "diffusion",
    "chart_drift",
    "one_step",
    "amplification",
    "history",
    "turning",
    "destination",
    "resilience",
    "jacobian",
    "ftr",
    "reachability",
    "transition",
)

ONE_STEP_SERIES = (
    ("affine_one_step_map_level2", "phi_hat", "lag-1 3x3 map; not J_hat"),
    ("conditional_affine_mean_rate_level2", "affine_mean_rate", "not Ito b"),
    ("innovation_covariance_level2", "innovation_covariance", "not diffusion a_hat"),
    ("operator_max_gain_rate_level2", "operator_max_gain_rate", "not spectral abscissa / FTR Gmax"),
    ("operator_volume_gain_rate_level2", "operator_volume_gain_rate", "not volume rescue"),
    ("operator_rotation_rate_level2", "operator_rotation_rate", "not turning / generator rotation"),
    ("spectral_abscissa_level3", "spectral_abscissa", "not Family B / jacobian derived_metrics"),
    ("numerical_abscissa_level3", "numerical_abscissa", "not jacobian numerical abscissa"),
    ("divergence_level3", "divergence", "not Ito divergence"),
    ("generator_rotation_norm_level3", "generator_rotation_norm", "not turning"),
)
AMPLIFICATION_SERIES = (
    ("neighbor_gain_q90_level1", "neighbor_gain_q90", "not operator max gain"),
    ("neighbor_gain_rate_q90_level1", "neighbor_gain_rate_q90", "not operator_max_gain_rate_level2"),
    ("neighbor_separation_rate_level1", "neighbor_separation_rate", "not spectral abscissa"),
    ("cloud_volume_change_rate_level1", "cloud_volume_change_rate", "not operator volume"),
)

_EMPTY = {"n": 0, "n_finite": 0, "finite_frac": float("nan"), "ge1_finite": False}


def _metric(
    metric_id: str,
    family: str,
    group: str,
    *,
    series: str | None = None,
    value_path: str | None = None,
    note: str = "",
    lag: int | None = None,
) -> dict[str, Any]:
    return {
        "metric_id": metric_id,
        "family": family,
        "group": group,
        "series": series,
        "value_path": value_path,
        "note": note,
        "declared_lag": lag,
    }


def catalog() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = [
        _metric(
            "coords_3d_subject_anchored",
            "chart",
            "/coords_3d_subject_anchored/values",
            value_path="/coords_3d_subject_anchored/values",
            note="3D subject-anchored trajectory",
        ),
        _metric(
            "coords_9d_subject_anchored",
            "chart",
            "/coords_9d_subject_anchored/values",
            value_path="/coords_9d_subject_anchored/values",
            note="9D subject-anchored trajectory; not Family B",
        ),
        _metric(
            "mnps_3d_dot",
            "chart",
            "/mnps_3d_dot",
            value_path="/mnps_3d_dot",
            note="SG 7/3+robust; not Ito b; not realized_velocity_level0",
        ),
        _metric("diffusion_a_hat", "diffusion", "/dynamical_families/diffusion/v1", series="a_hat", note="Family A; not Ito tensor"),
        _metric("diffusion_d_diff", "diffusion", "/dynamical_families/diffusion/v1", series="d_diff", note="derived scalar of a_hat"),
        _metric("diffusion_D_total", "diffusion", "/dynamical_families/diffusion/v1", series="D_total", note="trace of a_hat"),
        _metric("diffusion_A_bD", "diffusion", "/dynamical_families/diffusion/v1", series="A_bD", note="expected empty; drift_source not_supplied"),
        _metric("diffusion_R_b_over_a", "diffusion", "/dynamical_families/diffusion/v1", series="R_b_over_a", note="expected empty"),
        _metric(
            "increment_covariance_level0",
            "diffusion",
            "/dynamical_families/diffusion/v1/increment_covariance_level0",
            series="increment_covariance",
            note="unconditional Cov(dx); not a_hat",
        ),
        _metric(
            "realized_velocity_level0",
            "chart_drift",
            "/dynamical_families/drift/v1/realized_velocity_level0",
            series="dx_dt",
            note="not mnps_3d_dot; not Ito",
        ),
        _metric(
            "chart_drift_b_hat_pooled",
            "chart_drift",
            "/dynamical_families/drift/v1/conditional_mean_rate_level1/pooled",
            series="b_hat",
            note="ito_not_qualified; not drift_source for A_bD",
        ),
        _metric(
            "chart_drift_b_hat_crossfit",
            "chart_drift",
            "/dynamical_families/drift/v1/conditional_mean_rate_level1/blocked_crossfit",
            series="b_hat",
            note="embargoed variant; still not Ito",
        ),
        _metric(
            "chart_drift_lag_diagnostics",
            "chart_drift",
            "/dynamical_families/drift/v1/conditional_mean_rate_level1/lag_diagnostics",
            series="b_hat",
            note="diagnostics; not ito_qualified",
        ),
    ]
    for identity, series, note in ONE_STEP_SERIES:
        items.append(_metric(
            f"one_step_lag1_{identity}",
            "one_step",
            f"/dynamical_families/one_step/v1/{identity}",
            series=series,
            note=note,
            lag=1,
        ))
        items.append(_metric(
            f"one_step_lag2_{identity}",
            "one_step",
            f"/dynamical_families/one_step/v1/declared_lag_2/{identity}",
            series=series,
            note=f"direct lag-2; {note}",
            lag=2,
        ))
    items.append(_metric(
        "one_step_lag1_iterated_horizon_map_level4",
        "one_step",
        "/dynamical_families/one_step/v1/iterated_one_step_horizon_map_level4",
        series="phi_composed",
        note="not direct lag-2 map",
        lag=1,
    ))
    for identity, series, note in AMPLIFICATION_SERIES:
        items.append(_metric(
            f"amplification_{identity}",
            "amplification",
            f"/dynamical_families/amplification/v1/{identity}",
            series=series,
            note=note,
        ))
    items += [
        _metric(
            "history_predictive_gain_level1",
            "history",
            "/dynamical_families/history/v1/history_predictive_gain_level1",
            series="history_predictive_gain",
            note="not Markov restoration",
        ),
        _metric(
            "history_conditioned_operator_level2",
            "history",
            "/dynamical_families/history/v1/history_conditioned_operator_level2",
            series="phi_hat",
            note="3x6 map; not lag-1 Phi",
        ),
        _metric(
            "turning_angle_level0",
            "turning",
            "/dynamical_families/turning/v1/turning_angle_level0",
            series="turning_angle",
            note="NaN if undefined displacement; not operator rotation",
        ),
        _metric(
            "turning_rate_level0",
            "turning",
            "/dynamical_families/turning/v1/turning_rate_level0",
            series="turning_rate",
            note="not generator_rotation_norm_level3",
        ),
        _metric("destination", "destination", "/dynamical_families/destination/v1", note="expected not_testable"),
        _metric("resilience", "resilience", "/dynamical_families/resilience/v1", note="expected not_testable"),
        _metric(
            "jacobian_3d_jhat",
            "jacobian",
            "/jacobian/J_hat",
            value_path="/jacobian/J_hat",
            note="local linear map; not one-step Phi; fit may still fail the 0.9 gate",
        ),
        _metric(
            "jacobian_3d_alpha",
            "jacobian",
            "/jacobian/derived_metrics/v1",
            series="spectral_abscissa",
            note="Family B; I-CARE fit-fidelity gate",
        ),
        _metric(
            "jacobian_3d_omega",
            "jacobian",
            "/jacobian/derived_metrics/v1",
            series="numerical_abscissa",
            note="Family B companion",
        ),
        _metric(
            "jacobian_3d_rel_mse_oos",
            "jacobian",
            "/jacobian/diagnostics",
            series="rel_mse_baseline_oos_windows",
            value_path="/jacobian/diagnostics/rel_mse_baseline_oos_windows",
            note="additive OOS; does not replace in-sample gate",
        ),
        _metric(
            "jacobian_9d_alpha",
            "jacobian",
            "/jacobian_9D/derived_metrics/v1",
            series="spectral_abscissa",
            note="canonical 9D derived-metrics path used on 09-11 dumps",
        ),
        _metric(
            "jacobian_9d_subject_anchored_jhat",
            "jacobian",
            "/jacobian_9D_subject_anchored/J_hat",
            value_path="/jacobian_9D_subject_anchored/J_hat",
            note="anchored 9D J_hat; empty group on the smoke file",
        ),
        _metric(
            "ftr_3d_g_peak",
            "ftr",
            "/finite_time_response/v1/primary",
            value_path="/finite_time_response/v1/primary/summary/g_peak_over_horizons",
            note="model_derived; not FAR",
        ),
        _metric(
            "ftr_9d_g_peak",
            "ftr",
            "/finite_time_response/v1/stratified_9d",
            value_path="/finite_time_response/v1/stratified_9d/summary/g_peak_over_horizons",
            note="9D FTR summary scalar",
        ),
        _metric(
            "reach_3d",
            "reachability",
            "/stochastic_reachability/v1/primary",
            value_path="/stochastic_reachability/v1/primary/w_q",
            note="gated by jacobian fit; not dynamical_families/spread",
        ),
        _metric(
            "reach_9d",
            "reachability",
            "/stochastic_reachability/v1/stratified_9d",
            value_path="/stochastic_reachability/v1/stratified_9d/w_q",
            note="independent of 3D branch",
        ),
        _metric(
            "transition_residuals_3d",
            "transition",
            "/transition_residuals/v1/primary",
            series="transition_residual",
            note="cross-fit residuals",
        ),
        _metric(
            "qproxy_3d",
            "transition",
            "/transition_residual_covariance_proxy/v1/primary",
            value_path="/transition_residual_covariance_proxy/v1/primary/covariance",
            note="Q for W_Q",
        ),
    ]
    return items


METRICS = catalog()


def _s(value: Any) -> str | None:
    if value is None:
        return None
    text = str(as_scalar(value))
    return text if text not in {"", "None", "nan"} else None


def _scalar(handle: h5py.File, path: str) -> Any:
    if path not in handle:
        return None
    obj = handle[path]
    if not isinstance(obj, h5py.Dataset) or obj.shape != ():
        return None
    return as_scalar(obj[()])


def _finite_stats(obj: Any) -> dict[str, Any]:
    if obj is None:
        return dict(_EMPTY)
    try:
        raw = obj[()] if isinstance(obj, h5py.Dataset) else obj
        arr = np.asarray(raw)
        if arr.dtype.kind not in "fc":
            if arr.dtype.kind not in "iu":
                return dict(_EMPTY)
            arr = arr.astype(float)
        else:
            arr = arr.astype(float, copy=False)
    except (TypeError, ValueError, OSError):
        return dict(_EMPTY)
    if arr.size == 0:
        return dict(_EMPTY)
    n_finite = int(np.isfinite(arr).sum())
    return {
        "n": int(arr.size),
        "n_finite": n_finite,
        "finite_frac": float(n_finite / arr.size),
        "ge1_finite": n_finite > 0,
    }


def _value_stats(handle: h5py.File, spec: dict[str, Any]) -> dict[str, Any]:
    group = spec["group"]
    candidates: list[str] = []
    if spec.get("value_path"):
        candidates.append(str(spec["value_path"]))
    series = spec.get("series")
    if series:
        candidates.append(f"{group}/series/{series}")
        candidates.append(f"{group}/{series}")
    elif spec.get("value_path") is None:
        candidates.append(f"{group}/summary/g_peak_over_horizons")
    candidates.append(group)
    seen: set[str] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        if path not in handle:
            continue
        obj = handle[path]
        if isinstance(obj, h5py.Dataset):
            stats = _finite_stats(obj)
            if stats["n"] > 0 or path == spec.get("value_path") or path == group:
                return stats
    return dict(_EMPTY)


def _status_fields(handle: h5py.File, path: str) -> dict[str, Any]:
    out = {
        "present": path in handle,
        "status": "missing",
        "qual": None,
        "failure": None,
    }
    if path not in handle:
        return out
    obj = handle[path]
    if isinstance(obj, h5py.Dataset):
        out["status"] = "exported"
        return out
    out["status"] = _s(_scalar(handle, f"{path}/computation_status")) or "not_recorded"
    out["qual"] = _s(_scalar(handle, f"{path}/qualification_status"))
    out["failure"] = _s(_scalar(handle, f"{path}/failure_reason"))
    return out


def inspect_h5(path: str) -> dict[str, Any]:
    parsed = parse_run_stem(Path(path).stem)
    row: dict[str, Any] = {
        "source_h5": path,
        "stem": Path(path).stem,
        "subject_id": parsed["subject_id"],
        "run": parsed["run"],
        "acq": parsed["acq"],
        "read_ok": False,
        "read_error": None,
        "mndm_version": None,
    }
    try:
        with h5py.File(path, "r") as handle:
            row["mndm_version"] = _s(handle.attrs.get("mndm_version"))
            for spec in METRICS:
                mid = spec["metric_id"]
                info = _status_fields(handle, spec["group"])
                row[f"{mid}__present"] = bool(info["present"])
                row[f"{mid}__status"] = info["status"]
                row[f"{mid}__qual"] = info["qual"]
                row[f"{mid}__failure"] = info["failure"]
                stats = _value_stats(handle, spec) if info["present"] else dict(_EMPTY)
                row[f"{mid}__ge1_finite"] = bool(stats["ge1_finite"])
                row[f"{mid}__finite_frac"] = stats["finite_frac"]
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _aggregate(frame: pd.DataFrame) -> pd.DataFrame:
    n = int(len(frame))
    rows = []
    for spec in METRICS:
        mid = spec["metric_id"]
        present = int(frame[f"{mid}__present"].fillna(False).astype(bool).sum())
        computed = int((frame[f"{mid}__status"].isin(["computed", "exported"])).sum())
        ge1 = int(frame[f"{mid}__ge1_finite"].fillna(False).astype(bool).sum())
        ge1_and_computed = int(
            (
                frame[f"{mid}__status"].isin(["computed", "exported"])
                & frame[f"{mid}__ge1_finite"].fillna(False).astype(bool)
            ).sum()
        )
        frac = pd.to_numeric(frame[f"{mid}__finite_frac"], errors="coerce")
        status_counts = Counter(str(v) for v in frame[f"{mid}__status"].tolist())
        qual_counts = Counter(
            str(v) for v in frame[f"{mid}__qual"].tolist() if pd.notna(v) and str(v) not in {"None", "nan"}
        )
        fail_counts = Counter(
            str(v) for v in frame[f"{mid}__failure"].tolist() if pd.notna(v) and str(v) not in {"None", "nan"}
        )
        rows.append({
            "metric_id": mid,
            "family": spec["family"],
            "declared_lag": spec["declared_lag"],
            "h5_group": spec["group"],
            "series": spec["series"],
            "n_files": n,
            "n_present": present,
            "n_computed": computed,
            "n_ge1_finite": ge1,
            "n_ge1_finite_and_computed": ge1_and_computed,
            "present_frac": present / n if n else float("nan"),
            "computed_frac": computed / n if n else float("nan"),
            "ge1_finite_frac": ge1 / n if n else float("nan"),
            "mean_series_finite_frac": float(frac.mean()) if frac.notna().any() else float("nan"),
            "status_mode": status_counts.most_common(1)[0][0] if status_counts else None,
            "qualification_mode": qual_counts.most_common(1)[0][0] if qual_counts else None,
            "failure_mode": fail_counts.most_common(1)[0][0] if fail_counts else None,
            "note": spec["note"],
        })
    return pd.DataFrame(rows)


HEADLINE_METRICS = (
    "coords_3d_subject_anchored",
    "mnps_3d_dot",
    "diffusion_a_hat",
    "diffusion_A_bD",
    "chart_drift_b_hat_pooled",
    "one_step_lag1_affine_one_step_map_level2",
    "one_step_lag1_spectral_abscissa_level3",
    "one_step_lag2_affine_one_step_map_level2",
    "amplification_neighbor_gain_q90_level1",
    "history_predictive_gain_level1",
    "turning_angle_level0",
    "destination",
    "jacobian_3d_alpha",
    "jacobian_9d_alpha",
    "ftr_3d_g_peak",
    "reach_3d",
    "reach_9d",
)


def _fmt_frac(n: int, d: int) -> str:
    if d <= 0:
        return "n/a"
    return f"{n}/{d} ({n / d:.1%})"


def _render(matrix: pd.DataFrame, *, bundle_id: str, n_files: int, n_ok: int) -> str:
    by_id = {row["metric_id"]: row for _, row in matrix.iterrows()}
    lines = [
        "# I-CARE 3.0.1 coverage matrix",
        "",
        f"Bundle `{bundle_id}`. Files read: {n_ok}/{n_files}.",
        "",
        "A file **has a value** when the primary series (or summary scalar) contains",
        "at least one finite number. `computed`/`exported` is the group certificate and can",
        "diverge from finite values (for example lag-2 maps written as",
        "`insufficient_support` with all-NaN `phi_hat`).",
        "",
        "This is a coverage inventory. It does not license Family B, Ito drift,",
        "or a CPC contrast. It does not overwrite the 09-11 local-dynamics coverage.",
        "",
        "## At a glance (>=1 finite file count)",
        "",
        "| Metric | >=1 finite | Computed/exported | Status mode |",
        "| --- | ---: | ---: | --- |",
    ]
    for mid in HEADLINE_METRICS:
        row = by_id[mid]
        n = int(row["n_files"])
        lines.append(
            f"| `{mid}` | {_fmt_frac(int(row['n_ge1_finite']), n)} | "
            f"{_fmt_frac(int(row['n_computed']), n)} | `{row['status_mode']}` |"
        )
    lines.append("")
    family_rank = {name: i for i, name in enumerate(FAMILY_ORDER)}
    ordered = matrix.copy()
    ordered["_rank"] = ordered["family"].map(lambda name: family_rank.get(name, 99))
    ordered = ordered.sort_values(["_rank"], kind="stable")
    for family, block in ordered.groupby("family", sort=False):
        lines += [
            f"## {family}",
            "",
            "| Metric | Present | Computed/exported | >=1 finite | >=1 finite and computed | Series finite (mean) | Status mode | Qual / failure | Note |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
        for _, row in block.iterrows():
            n = int(row["n_files"])
            qual = row["qualification_mode"] or row["failure_mode"] or "-"
            mean_f = row["mean_series_finite_frac"]
            mean_s = "n/a" if not np.isfinite(mean_f) else f"{mean_f:.3f}"
            lines.append(
                f"| `{row['metric_id']}` | {_fmt_frac(int(row['n_present']), n)} | "
                f"{_fmt_frac(int(row['n_computed']), n)} | "
                f"{_fmt_frac(int(row['n_ge1_finite']), n)} | "
                f"{_fmt_frac(int(row['n_ge1_finite_and_computed']), n)} | "
                f"{mean_s} | `{row['status_mode']}` | `{qual}` | {row['note']} |"
            )
        lines.append("")
    lines += [
        "## How to read this",
        "",
        "- **>=1 finite** is the column that answers how many H5 files have a value.",
        "- One-step series of length T are recording-level broadcasts, not T replicates.",
        "- Chart-drift `b_hat` being populated is not Ito identification and is not",
        "  a `drift_source` for `A_bD`.",
        "- Jacobian OOS (`rel_mse_baseline_oos_windows`) lives under `/jacobian/diagnostics`",
        "  with no `computation_status`; use >=1 finite, not computed.",
        "- One-step L3 abscissa being populated is not Family B.",
        "- Jacobian `J_hat` can be written while derived α is all-NaN after the 0.9 gate.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit-h5", type=int, default=None)
    args = parser.parse_args()
    raw_root = args.input_dir
    paths = discover_h5_files(raw_root, limit_h5=args.limit_h5)
    bundle_id = raw_root.name.replace("neuralmanifolddynamics_physionet_icare_2_1_", "")
    print(f"{bundle_id}: {len(paths)} files from {raw_root}", flush=True)
    rows = parallel_map(inspect_h5, [str(p) for p in paths], workers=args.workers, desc="v301-coverage")
    frame = pd.DataFrame(rows)
    matrix = _aggregate(frame)
    out = args.output_dir
    write_csv(out / "coverage_by_file.csv", frame)
    write_csv(out / "coverage_matrix.csv", matrix)
    write_json(out / "coverage_matrix.json", matrix.to_dict(orient="records"))
    md = _render(
        matrix,
        bundle_id=bundle_id,
        n_files=int(len(frame)),
        n_ok=int(frame["read_ok"].sum()) if "read_ok" in frame else 0,
    )
    (out / "coverage_matrix.md").write_text(md, encoding="utf-8")
    print(f"wrote {out / 'coverage_matrix.md'}", flush=True)
    print(matrix[["metric_id", "n_present", "n_computed", "n_ge1_finite"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
