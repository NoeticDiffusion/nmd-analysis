"""Window- and run-level coverage of local dynamics, beyond spectral abscissa.

Scans the article bundles (2026-09-11), not the 09-12 identity re-runs.

For each recording, records computation_status / failure_reason and cheap
window-level finite fractions for:

- Family A diffusion (`a_hat`, `d_diff`, `D_total`, `A_bD`, `R_b_over_a`)
- chart velocity `/mnps_3d_dot` and subject-anchored coordinates
- Jacobian derived metrics (3D and 9D)
- finite-time response, stored stochastic reachability, transition residuals
- destination / resilience (expected `not_testable`)

This is a measurement-coverage audit. It does not re-test H1-H4 or Family B.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

from icare_v2_common import (
    ARTICLE_DIR,
    as_scalar,
    discover_h5_files,
    parallel_map,
    parse_run_stem,
    write_csv,
    write_json,
)

COHORTS = (
    {
        "label": "part1_discovery",
        "display": "Discovery",
        "bundle_id": "20260911_125829",
        "raw_root": Path(r"J:/repos/nmd-analysis/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260911_125829"),
        "out_dir": ARTICLE_DIR / "results" / "part1_corrected",
    },
    {
        "label": "part2_confirmatory",
        "display": "Confirmatory",
        "bundle_id": "20260911_123135",
        "raw_root": Path(r"J:/repos/nmd-analysis/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260911_123135"),
        "out_dir": ARTICLE_DIR / "results" / "part2_confirmatory",
    },
)

STATUS_PATHS = (
    ("diffusion", "/dynamical_families/diffusion/v1"),
    ("destination", "/dynamical_families/destination/v1"),
    ("resilience", "/dynamical_families/resilience/v1"),
    ("jacobian_3d", "/jacobian/derived_metrics/v1"),
    ("jacobian_9d", "/jacobian_9D/derived_metrics/v1"),
    ("ftr_3d", "/finite_time_response/v1/primary"),
    ("ftr_9d", "/finite_time_response/v1/stratified_9d"),
    ("reach_3d", "/stochastic_reachability/v1/primary"),
    ("reach_9d", "/stochastic_reachability/v1/stratified_9d"),
    ("transition_3d", "/transition_residuals/v1/primary"),
    ("qproxy_3d", "/transition_residual_covariance_proxy/v1/primary"),
)


def _s(value: Any) -> str | None:
    if value is None:
        return None
    text = str(as_scalar(value))
    return text if text not in {"", "None", "nan"} else None


def _finite_frac(arr: np.ndarray) -> float:
    if arr.size == 0:
        return float("nan")
    if arr.dtype.kind not in "fiu":
        return float("nan")
    return float(np.mean(np.isfinite(arr)))


def _row_finite_frac(arr: np.ndarray) -> float:
    if arr.size == 0:
        return float("nan")
    work = np.asarray(arr, dtype=float)
    if work.ndim == 1:
        return _finite_frac(work)
    rows = work.reshape(work.shape[0], -1)
    return float(np.mean(np.all(np.isfinite(rows), axis=1)))


def _scalar(handle: h5py.File, path: str) -> Any:
    if path not in handle:
        return None
    obj = handle[path]
    if not isinstance(obj, h5py.Dataset) or obj.shape != ():
        return None
    return as_scalar(obj[()])


def _group_status(handle: h5py.File, path: str) -> dict[str, Any]:
    out = {
        "present": path in handle,
        "status": "missing",
        "failure_reason": None,
        "measurement_validity": None,
        "claim_status": None,
        "validation_level": None,
    }
    if path not in handle:
        return out
    group = handle[path]
    out["status"] = _s(_scalar(handle, f"{path}/computation_status")) or "not_recorded"
    out["failure_reason"] = _s(_scalar(handle, f"{path}/failure_reason"))
    out["measurement_validity"] = _s(_scalar(handle, f"{path}/measurement_validity"))
    out["claim_status"] = _s(_scalar(handle, f"{path}/claim_status"))
    out["validation_level"] = _s(_scalar(handle, f"{path}/validation_level"))
    if out["validation_level"] is None and "provenance" in group:
        out["validation_level"] = _s(_scalar(handle, f"{path}/provenance/validation_level"))
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
        "n_time": 0,
        "coords_3d_row_finite_frac": float("nan"),
        "mnps_3d_dot_row_finite_frac": float("nan"),
        "a_hat_row_finite_frac": float("nan"),
        "d_diff_finite_frac": float("nan"),
        "d_total_finite_frac": float("nan"),
        "a_bd_finite_frac": float("nan"),
        "r_b_over_a_finite_frac": float("nan"),
        "diff_n_timepoints": float("nan"),
        "diff_n_valid_timepoints": float("nan"),
        "diff_drift_source": None,
        "diff_a_bd_status": None,
        "diff_r_b_status": None,
        "diff_alignment_failure": None,
        "jac3_n_windows": float("nan"),
        "jac3_n_metrics_valid": float("nan"),
        "jac3_n_fit_unidentified": float("nan"),
        "jac3_alpha_finite_frac": float("nan"),
        "jac3_rel_mse_median": float("nan"),
        "jac3_fit_identified": None,
        "jac9_n_windows": float("nan"),
        "jac9_n_metrics_valid": float("nan"),
        "jac9_alpha_finite_frac": float("nan"),
        "jac9_rel_mse_median": float("nan"),
        "ftr3_h1_n_candidate": float("nan"),
        "ftr3_h1_n_valid": float("nan"),
        "ftr3_g_peak": float("nan"),
        "trans_series_finite_frac": float("nan"),
        "qc_ok_eeg_mode": None,
        "qc_ok_eeg_not_assessed_frac": float("nan"),
        "has_conventional_eeg": False,
    }
    try:
        with h5py.File(path, "r") as handle:
            if "/time" in handle:
                row["n_time"] = int(np.asarray(handle["/time"]).reshape(-1).size)
            for name, gpath in STATUS_PATHS:
                info = _group_status(handle, gpath)
                row[f"{name}_present"] = bool(info["present"])
                row[f"{name}_status"] = info["status"]
                row[f"{name}_failure"] = info["failure_reason"]
                row[f"{name}_validity"] = info["measurement_validity"]
                row[f"{name}_claim"] = info["claim_status"]
                row[f"{name}_validation_level"] = info["validation_level"]

            if "/coords_3d_subject_anchored/values" in handle:
                row["coords_3d_row_finite_frac"] = _row_finite_frac(
                    np.asarray(handle["/coords_3d_subject_anchored/values"][:], dtype=float)
                )
            if "/mnps_3d_dot" in handle:
                row["mnps_3d_dot_row_finite_frac"] = _row_finite_frac(
                    np.asarray(handle["/mnps_3d_dot"][:], dtype=float)
                )

            dpath = "/dynamical_families/diffusion/v1"
            if dpath in handle:
                series = handle[dpath]["series"] if "series" in handle[dpath] else None
                if series is not None:
                    if "a_hat" in series:
                        row["a_hat_row_finite_frac"] = _row_finite_frac(np.asarray(series["a_hat"][:], dtype=float))
                    if "d_diff" in series:
                        row["d_diff_finite_frac"] = _finite_frac(np.asarray(series["d_diff"][:], dtype=float))
                    if "D_total" in series:
                        row["d_total_finite_frac"] = _finite_frac(np.asarray(series["D_total"][:], dtype=float))
                    if "A_bD" in series:
                        row["a_bd_finite_frac"] = _finite_frac(np.asarray(series["A_bD"][:], dtype=float))
                    if "R_b_over_a" in series:
                        row["r_b_over_a_finite_frac"] = _finite_frac(np.asarray(series["R_b_over_a"][:], dtype=float))
                row["diff_n_timepoints"] = _scalar(handle, f"{dpath}/summary/n_timepoints")
                row["diff_n_valid_timepoints"] = _scalar(handle, f"{dpath}/summary/n_valid_timepoints")
                row["diff_drift_source"] = _s(_scalar(handle, f"{dpath}/provenance/settings/drift_source"))
                row["diff_a_bd_status"] = _s(_scalar(handle, f"{dpath}/summary/A_bD_computation_status"))
                row["diff_r_b_status"] = _s(_scalar(handle, f"{dpath}/summary/R_b_over_a_computation_status"))
                row["diff_alignment_failure"] = _s(_scalar(handle, f"{dpath}/summary/drift_alignment_failure_reason"))

            j3 = "/jacobian/derived_metrics/v1"
            if j3 in handle:
                row["jac3_n_windows"] = _scalar(handle, f"{j3}/summary/n_windows_total")
                row["jac3_n_metrics_valid"] = _scalar(handle, f"{j3}/summary/n_windows_metrics_valid")
                row["jac3_n_fit_unidentified"] = _scalar(handle, f"{j3}/summary/n_windows_fit_unidentified")
                row["jac3_rel_mse_median"] = _scalar(handle, f"{j3}/summary/rel_mse_baseline_median")
                row["jac3_fit_identified"] = _s(_scalar(handle, f"{j3}/summary/fit_identified"))
                if f"{j3}/series/spectral_abscissa" in handle:
                    row["jac3_alpha_finite_frac"] = _finite_frac(
                        np.asarray(handle[f"{j3}/series/spectral_abscissa"][:], dtype=float)
                    )
            j9 = "/jacobian_9D/derived_metrics/v1"
            if j9 in handle:
                row["jac9_n_windows"] = _scalar(handle, f"{j9}/summary/n_windows_total")
                row["jac9_n_metrics_valid"] = _scalar(handle, f"{j9}/summary/n_windows_metrics_valid")
                row["jac9_rel_mse_median"] = _scalar(handle, f"{j9}/summary/rel_mse_baseline_median")
                if f"{j9}/series/spectral_abscissa" in handle:
                    row["jac9_alpha_finite_frac"] = _finite_frac(
                        np.asarray(handle[f"{j9}/series/spectral_abscissa"][:], dtype=float)
                    )

            h1 = "/finite_time_response/v1/primary/horizons/h1"
            if h1 in handle:
                row["ftr3_h1_n_candidate"] = _scalar(handle, f"{h1}/n_sequences_candidate")
                row["ftr3_h1_n_valid"] = _scalar(handle, f"{h1}/n_sequences_valid")
            row["ftr3_g_peak"] = _scalar(handle, "/finite_time_response/v1/primary/summary/g_peak_over_horizons")

            tpath = "/transition_residuals/v1/primary/series"
            if tpath in handle:
                fracs = []
                for name in handle[tpath].keys():
                    obj = handle[tpath][name]
                    if isinstance(obj, h5py.Dataset) and obj.dtype.kind in "fiu":
                        fracs.append(_finite_frac(np.asarray(obj[:], dtype=float)))
                if fracs:
                    work = np.asarray(fracs, dtype=float)
                    work = work[np.isfinite(work)]
                    row["trans_series_finite_frac"] = float(work.mean()) if work.size else float("nan")

            if "/qc/windows/qc_ok_eeg" in handle:
                eeg = np.asarray(handle["/qc/windows/qc_ok_eeg"][:]).reshape(-1)
                row["qc_ok_eeg_not_assessed_frac"] = float(np.mean(eeg == -1)) if eeg.size else float("nan")
                if eeg.size:
                    vals, counts = np.unique(eeg, return_counts=True)
                    row["qc_ok_eeg_mode"] = str(vals[int(np.argmax(counts))])
            row["has_conventional_eeg"] = "/extensions/conventional_eeg" in handle
            row["read_ok"] = True
    except Exception as exc:  # noqa: BLE001
        row["read_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _status_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if column not in frame.columns:
        return {}
    return {str(k): int(v) for k, v in frame[column].value_counts(dropna=False).items()}


def _mean(frame: pd.DataFrame, column: str) -> float:
    return float(pd.to_numeric(frame[column], errors="coerce").mean())


def _summarize(frame: pd.DataFrame, spec: dict[str, Any]) -> dict[str, Any]:
    n = int(len(frame))
    computed = {name: int((frame[f"{name}_status"] == "computed").sum()) for name, _ in STATUS_PATHS}
    payload: dict[str, Any] = {
        "cohort": spec["label"],
        "display": spec["display"],
        "bundle_id": spec["bundle_id"],
        "n_files": n,
        "n_read_ok": int(frame["read_ok"].sum()),
        "coords_3d_row_finite_mean": _mean(frame, "coords_3d_row_finite_frac"),
        "mnps_3d_dot_row_finite_mean": _mean(frame, "mnps_3d_dot_row_finite_frac"),
        "a_hat_row_finite_mean": _mean(frame, "a_hat_row_finite_frac"),
        "d_diff_finite_mean": _mean(frame, "d_diff_finite_frac"),
        "a_bd_finite_mean": _mean(frame, "a_bd_finite_frac"),
        "r_b_over_a_finite_mean": _mean(frame, "r_b_over_a_finite_frac"),
        "jac3_alpha_finite_mean": _mean(frame, "jac3_alpha_finite_frac"),
        "jac9_alpha_finite_mean": _mean(frame, "jac9_alpha_finite_frac"),
        "conventional_eeg_n": int(frame["has_conventional_eeg"].sum()),
        "qc_ok_eeg_not_assessed_mean": _mean(frame, "qc_ok_eeg_not_assessed_frac"),
        "diff_drift_source_mode": (
            str(frame["diff_drift_source"].mode().iloc[0]) if frame["diff_drift_source"].notna().any() else None
        ),
        "ftr3_validation_mode": (
            str(frame["ftr_3d_validation_level"].mode().iloc[0])
            if frame["ftr_3d_validation_level"].notna().any()
            else None
        ),
        "destination_failure_mode": (
            str(frame["destination_failure"].mode().iloc[0]) if frame["destination_failure"].notna().any() else None
        ),
        "resilience_failure_mode": (
            str(frame["resilience_failure"].mode().iloc[0]) if frame["resilience_failure"].notna().any() else None
        ),
        "reach_3d_failure_mode": (
            str(frame["reach_3d_failure"].mode().iloc[0]) if frame["reach_3d_failure"].notna().any() else None
        ),
    }
    for name, _ in STATUS_PATHS:
        payload[f"{name}_computed_n"] = computed[name]
        payload[f"{name}_computed_frac"] = computed[name] / n if n else float("nan")
        payload[f"{name}_status_counts"] = _status_counts(frame, f"{name}_status")
    # FTR computed while 3D jacobian is gated
    if "ftr_3d_status" in frame.columns and "jacobian_3d_status" in frame.columns:
        payload["ftr3_computed_while_jac3_gated_n"] = int(
            ((frame["ftr_3d_status"] == "computed") & (frame["jacobian_3d_status"] != "computed")).sum()
        )
    return payload


def _fmt_frac(n: int, d: int) -> str:
    if d <= 0:
        return "n/a"
    return f"{n}/{d} ({n / d:.1%})"


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _render(summaries: list[dict[str, Any]]) -> str:
    lines = [
        "# Local-dynamics coverage audit (beyond spectral abscissa)",
        "",
        "Run- and window-level coverage on the 2026-09-11 article bundles.",
        "Not an ingest-identity check and not a CPC re-test.",
        "",
        "Usable here means *populated under the current contract*, not independently",
        "qualified as an Itô object.",
        "",
    ]
    for row in summaries:
        n = int(row["n_files"])
        lines += [
            f"## {row['display']} (`{row['cohort']}`, bundle `{row['bundle_id']}`)",
            "",
            f"- files read: {row['n_read_ok']}/{n}",
            f"- subject-anchored coords row-finite (mean): `{_fmt(row['coords_3d_row_finite_mean'])}`",
            f"- `/mnps_3d_dot` row-finite (mean): `{_fmt(row['mnps_3d_dot_row_finite_mean'])}`",
            f"- diffusion `a_hat` row-finite (mean): `{_fmt(row['a_hat_row_finite_mean'])}`",
            f"- stored `A_bD` finite (mean): `{_fmt(row['a_bd_finite_mean'])}` "
            f"(status mode from files; drift_source=`{row['diff_drift_source_mode']}`)",
            f"- Jacobian-3D spectral abscissa finite (mean): `{_fmt(row['jac3_alpha_finite_mean'])}`",
            f"- Jacobian-9D spectral abscissa finite (mean): `{_fmt(row['jac9_alpha_finite_mean'])}`",
            f"- `qc_ok_eeg = -1` fraction (mean): `{_fmt(row['qc_ok_eeg_not_assessed_mean'])}`",
            f"- `conventional_eeg` extension present: `{row['conventional_eeg_n']}/{n}`",
            "",
            "| Object | Run `computed` | Window/series notes | Call |",
            "| --- | --- | --- | --- |",
            f"| Diffusion `a_hat` / `d_diff` | {_fmt_frac(row['diffusion_computed_n'], n)} | "
            f"a_hat finite `{_fmt(row['a_hat_row_finite_mean'])}`; "
            f"A_bD finite `{_fmt(row['a_bd_finite_mean'])}` | **usable for H1/H2/H4**; "
            "alignment empty (`drift_source=not_supplied`) |",
            f"| Chart velocity `/mnps_3d_dot` | n/a (always exported) | "
            f"row-finite `{_fmt(row['mnps_3d_dot_row_finite_mean'])}` | present, **not** a qualified Itô drift |",
            f"| Jacobian 3D (`alpha`) | {_fmt_frac(row['jacobian_3d_computed_n'], n)} | "
            f"alpha finite `{_fmt(row['jac3_alpha_finite_mean'])}` | Family B **not testable** |",
            f"| Jacobian 9D (`alpha`) | {_fmt_frac(row['jacobian_9d_computed_n'], n)} | "
            f"alpha finite `{_fmt(row['jac9_alpha_finite_mean'])}` | populated more often; 9D `e_m` is a "
            "non-equivalent fallback — **do not use as Family B** |",
            f"| FTR 3D | {_fmt_frac(row['ftr_3d_computed_n'], n)} | "
            f"validation=`{row['ftr3_validation_mode']}`; "
            f"computed while Jac3 gated: {row.get('ftr3_computed_while_jac3_gated_n', 0)} | "
            "**computed but model-derived** (uses the generator even when derived metrics fail the gate) |",
            f"| Stored reachability 3D | {_fmt_frac(row['reach_3d_computed_n'], n)} | "
            f"failure mode `{row['reach_3d_failure_mode']}` | **not usable**; article recomputes cones from coords |",
            f"| Stored reachability 9D | {_fmt_frac(row['reach_9d_computed_n'], n)} | 9D chart | not used in this article |",
            f"| Transition residuals 3D | {_fmt_frac(row['transition_3d_computed_n'], n)} | — | populated; not a primary endpoint here |",
            f"| Q-proxy 3D | {_fmt_frac(row['qproxy_3d_computed_n'], n)} | — | populated; not a primary endpoint here |",
            f"| Destination (committor) | {_fmt_frac(row['destination_computed_n'], n)} | "
            f"`{row['destination_failure_mode']}` | contract **not_testable** |",
            f"| Resilience (FAR) | {_fmt_frac(row['resilience_computed_n'], n)} | "
            f"`{row['resilience_failure_mode']}` | contract **not_testable** |",
            "",
        ]
    lines += [
        "## Interpretation",
        "",
        "- **Diffusion geometry is the only Family-A object with honest, high coverage.**",
        "  ~98% of recordings are `computed`, and `a_hat` / `d_diff` are finite on those windows.",
        "- **Drift is not covered as an Itô field.** `/mnps_3d_dot` is almost fully populated as a",
        "  chart derivative, but `drift_source = not_supplied`, so `A_bD` and `R_b/a` stay empty.",
        "  H3 therefore cannot be a clean drift-orthogonal diffusion fraction.",
        "- **Spectral abscissa remains the coverage failure for local linear dynamics (3D).**",
        "  9D Jacobian/reachability look 'better' only because that chart is not the article chart",
        "  and `e_m` is a documented non-equivalent fallback.",
        "- **FTR run-status is not a Jacobian-gate pass.** Many files are FTR-`computed` while",
        "  3D Jacobian derived metrics are `insufficient_support`; FTR is `model_derived`.",
        "- Destination and resilience are empty by contract, not by a silent ingest miss.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit-h5", type=int, default=None)
    parser.add_argument("--output-dir", type=Path, default=ARTICLE_DIR / "results" / "replication")
    args = parser.parse_args()
    summaries = []
    frames = []
    for spec in COHORTS:
        paths = discover_h5_files(spec["raw_root"], limit_h5=args.limit_h5)
        print(f"{spec['label']}: {len(paths)} files", flush=True)
        rows = parallel_map(inspect_h5, [str(p) for p in paths], workers=args.workers, desc=spec["label"])
        frame = pd.DataFrame(rows)
        frame["cohort"] = spec["label"]
        frame["bundle_id"] = spec["bundle_id"]
        write_csv(spec["out_dir"] / "local_dynamics_coverage.csv", frame)
        frames.append(frame)
        summaries.append(_summarize(frame, spec))
    out_dir = args.output_dir
    write_csv(out_dir / "local_dynamics_coverage_all.csv", pd.concat(frames, ignore_index=True))
    write_json(out_dir / "local_dynamics_coverage_summary.json", summaries)
    md = _render(summaries)
    (out_dir / "local_dynamics_coverage.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
