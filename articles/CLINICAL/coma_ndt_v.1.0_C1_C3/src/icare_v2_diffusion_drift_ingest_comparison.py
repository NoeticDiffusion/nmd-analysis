"""Paired diffusion + drift audit: 2026-09-11 predecessor vs 2026-09-12 re-run.

Same stem pairing as Family B (`icare_v2_family_b_ingest_comparison.py`):

- part1: 20260911_125829 vs 20260912_094016
- part2: 20260911_123135 vs 20260912_094010

Checks whether Family A tensors (`a_hat`, `d_diff`, `D_total`), the stored
alignment `A_bD` / `drift_diffusion_alignment`, and the drift proxy
`/mnps_3d_dot` changed. Also classifies `mnps_3d_dot` against a one-step
finite difference of `coords_3d_subject_anchored` vs a Savitzky-Golay
derivative (config claims `mnps.derivative.method=sav_gol`).

Does not re-test H1-H4. If the series are identical, the existing CPC
contrasts stand. If they differ, that is a measurement-change flag.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

from icare_v2_common import (
    ARTICLE_DIR,
    as_scalar,
    finite_array,
    median_finite,
    parallel_map,
    parse_run_stem,
    write_csv,
    write_json,
)

PAIRS = (
    {
        "cohort": "part1_discovery",
        "old_id": "20260911_125829",
        "new_id": "20260912_094016",
        "old_root": Path(r"J:/repos/nmd-analysis/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260911_125829"),
        "new_root": Path(r"J:/repos/nmd-analysis/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260912_094016"),
    },
    {
        "cohort": "part2_confirmatory",
        "old_id": "20260911_123135",
        "new_id": "20260912_094010",
        "old_root": Path(r"J:/repos/nmd-analysis/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260911_123135"),
        "new_root": Path(r"J:/repos/nmd-analysis/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260912_094010"),
    },
)

SAVGOL_WINDOW = 7
SAVGOL_POLY = 3


def _read_one(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "exists": path.is_file(),
        "stem": path.stem,
        "subject_id": parse_run_stem(path.stem)["subject_id"],
        "diff_status": None,
        "n_windows": 0,
        "n_valid": 0,
        "d_eff_median": float("nan"),
        "d_total_median": float("nan"),
        "abd_median": float("nan"),
        "e_perp_from_abd_median": float("nan"),
        "a_hat_abs_median": float("nan"),
        "dot_abs_median": float("nan"),
        "coords_abs_median": float("nan"),
        "dot_vs_step_mae": float("nan"),
        "dot_vs_savgol_mae": float("nan"),
        "drift_source": None,
        "neighborhood_k": float("nan"),
    }
    if not out["exists"]:
        return out
    try:
        with h5py.File(path, "r") as handle:
            gpath = "/dynamical_families/diffusion/v1"
            if gpath in handle:
                group = handle[gpath]
                if "computation_status" in group:
                    out["diff_status"] = str(as_scalar(group["computation_status"][()]))
                if "provenance" in group:
                    prov = group["provenance"]
                    if "settings/drift_source" in prov:
                        out["drift_source"] = str(as_scalar(prov["settings/drift_source"][()]))
                    if "settings/neighborhood_k" in prov:
                        out["neighborhood_k"] = float(as_scalar(prov["settings/neighborhood_k"][()]))
                series = group["series"] if "series" in group else None
                if series is not None:
                    valid = (
                        np.asarray(series["valid"][:], dtype=int).reshape(-1) == 1
                        if "valid" in series
                        else None
                    )
                    def _med(name: str) -> float:
                        if name not in series:
                            return float("nan")
                        arr = np.asarray(series[name][:], dtype=float).reshape(-1)
                        if valid is not None and valid.size == arr.size:
                            arr = arr[valid]
                        return median_finite(arr)

                    out["d_eff_median"] = _med("d_diff")
                    out["d_total_median"] = _med("D_total")
                    abd = _med("drift_diffusion_alignment")
                    if not np.isfinite(abd):
                        abd = _med("A_bD")
                    out["abd_median"] = abd
                    out["e_perp_from_abd_median"] = float(1.0 - abd) if np.isfinite(abd) else float("nan")
                    if "a_hat" in series:
                        a_hat = np.asarray(series["a_hat"][:], dtype=float)
                        out["n_windows"] = int(a_hat.shape[0])
                        mask = valid if valid is not None and valid.size == a_hat.shape[0] else np.ones(a_hat.shape[0], dtype=bool)
                        out["n_valid"] = int(np.asarray(mask).sum())
                        finite = np.isfinite(a_hat).all(axis=(1, 2)) & np.asarray(mask, dtype=bool)
                        out["a_hat_abs_median"] = median_finite(np.abs(a_hat[finite])) if finite.any() else float("nan")
            if "/mnps_3d_dot" in handle:
                dot = np.asarray(handle["/mnps_3d_dot"][:], dtype=float)
                out["dot_abs_median"] = median_finite(np.abs(dot))
            if "/coords_3d_subject_anchored/values" in handle:
                coords = np.asarray(handle["/coords_3d_subject_anchored/values"][:], dtype=float)
                out["coords_abs_median"] = median_finite(np.abs(coords))
            if "/mnps_3d_dot" in handle and "/coords_3d_subject_anchored/values" in handle and "/time" in handle:
                dot = np.asarray(handle["/mnps_3d_dot"][:], dtype=float)
                coords = np.asarray(handle["/coords_3d_subject_anchored/values"][:], dtype=float)
                time = np.asarray(handle["/time"][:], dtype=float)
                n = min(dot.shape[0], coords.shape[0], time.shape[0])
                if n >= 5:
                    dt = np.diff(time[:n])
                    dt_med = float(np.median(dt[np.isfinite(dt) & (dt > 0)])) if dt.size else float("nan")
                    if np.isfinite(dt_med) and dt_med > 0:
                        step = np.full_like(dot[:n], np.nan)
                        step[1:] = (coords[1:n] - coords[: n - 1]) / dt_med
                        out["dot_vs_step_mae"] = float(np.nanmean(np.abs(dot[:n] - step)))
                        window = min(SAVGOL_WINDOW, n if n % 2 == 1 else n - 1)
                        if window >= SAVGOL_POLY + 2:
                            sg = savgol_filter(
                                coords[:n],
                                window_length=window,
                                polyorder=SAVGOL_POLY,
                                deriv=1,
                                delta=dt_med,
                                axis=0,
                                mode="interp",
                            )
                            out["dot_vs_savgol_mae"] = float(np.nanmean(np.abs(dot[:n] - sg)))
    except Exception as exc:  # noqa: BLE001
        out["read_error"] = f"{type(exc).__name__}: {exc}"
    return out


def _pair_one(item: tuple[str, str, str]) -> dict[str, Any]:
    stem, old_path, new_path = item
    old = _read_one(Path(old_path)) if old_path else {"exists": False, "stem": stem}
    new = _read_one(Path(new_path)) if new_path else {"exists": False, "stem": stem}

    def _diff(key: str) -> float:
        a, b = old.get(key, float("nan")), new.get(key, float("nan"))
        try:
            a = float(a)
            b = float(b)
        except (TypeError, ValueError):
            return float("nan")
        if np.isfinite(a) and np.isfinite(b):
            return float(b - a)
        return float("nan")

    return {
        "stem": stem,
        "subject_id": old.get("subject_id") or new.get("subject_id"),
        "old_exists": bool(old.get("exists")),
        "new_exists": bool(new.get("exists")),
        "old_status": old.get("diff_status"),
        "new_status": new.get("diff_status"),
        "status_match": old.get("diff_status") == new.get("diff_status"),
        "old_n_valid": old.get("n_valid", 0),
        "new_n_valid": new.get("n_valid", 0),
        "old_d_eff": old.get("d_eff_median"),
        "new_d_eff": new.get("d_eff_median"),
        "d_eff_diff": _diff("d_eff_median"),
        "old_d_total": old.get("d_total_median"),
        "new_d_total": new.get("d_total_median"),
        "d_total_diff": _diff("d_total_median"),
        "old_abd": old.get("abd_median"),
        "new_abd": new.get("abd_median"),
        "abd_diff": _diff("abd_median"),
        "old_e_perp_abd": old.get("e_perp_from_abd_median"),
        "new_e_perp_abd": new.get("e_perp_from_abd_median"),
        "a_hat_abs_diff": _diff("a_hat_abs_median"),
        "old_dot_abs": old.get("dot_abs_median"),
        "new_dot_abs": new.get("dot_abs_median"),
        "dot_abs_diff": _diff("dot_abs_median"),
        "coords_abs_diff": _diff("coords_abs_median"),
        "old_dot_vs_step_mae": old.get("dot_vs_step_mae"),
        "new_dot_vs_step_mae": new.get("dot_vs_step_mae"),
        "old_dot_vs_savgol_mae": old.get("dot_vs_savgol_mae"),
        "new_dot_vs_savgol_mae": new.get("dot_vs_savgol_mae"),
        "old_drift_source": old.get("drift_source"),
        "new_drift_source": new.get("drift_source"),
        "old_neighborhood_k": old.get("neighborhood_k"),
        "new_neighborhood_k": new.get("neighborhood_k"),
    }


def _abs_med(series) -> float:
    arr = finite_array(np.abs(np.asarray(series, dtype=float)))
    return float(np.median(arr)) if arr.size else float("nan")


def _abs_max(series) -> float:
    arr = finite_array(np.abs(np.asarray(series, dtype=float)))
    return float(np.max(arr)) if arr.size else float("nan")


def _summarize(frame, spec: dict[str, Any]) -> dict[str, Any]:
    both = frame[frame["old_exists"] & frame["new_exists"]]
    step = finite_array(both["new_dot_vs_step_mae"])
    sg = finite_array(both["new_dot_vs_savgol_mae"])
    return {
        "cohort": spec["cohort"],
        "old_bundle": spec["old_id"],
        "new_bundle": spec["new_id"],
        "n_paired": int(len(both)),
        "status_agree_n": int(both["status_match"].sum()),
        "status_agree_frac": float(both["status_match"].mean()) if len(both) else float("nan"),
        "old_computed_n": int((both["old_status"] == "computed").sum()),
        "new_computed_n": int((both["new_status"] == "computed").sum()),
        "d_eff_abs_diff_median": _abs_med(both["d_eff_diff"]),
        "d_eff_abs_diff_max": _abs_max(both["d_eff_diff"]),
        "d_total_abs_diff_median": _abs_med(both["d_total_diff"]),
        "d_total_abs_diff_max": _abs_max(both["d_total_diff"]),
        "abd_abs_diff_median": _abs_med(both["abd_diff"]),
        "abd_abs_diff_max": _abs_max(both["abd_diff"]),
        "a_hat_abs_diff_median": _abs_med(both["a_hat_abs_diff"]),
        "dot_abs_diff_median": _abs_med(both["dot_abs_diff"]),
        "dot_abs_diff_max": _abs_max(both["dot_abs_diff"]),
        "coords_abs_diff_median": _abs_med(both["coords_abs_diff"]),
        "dot_vs_step_mae_median": float(np.median(step)) if step.size else float("nan"),
        "dot_vs_savgol_mae_median": float(np.median(sg)) if sg.size else float("nan"),
        "dot_closer_to_savgol_frac": float(np.mean(sg < step)) if step.size and sg.size and step.size == sg.size else float("nan"),
        "new_drift_source_mode": str(both["new_drift_source"].mode().iloc[0]) if both["new_drift_source"].notna().any() else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out-dir", type=Path, default=ARTICLE_DIR / "results" / "replication")
    args = parser.parse_args()
    out_dir = args.out_dir
    summaries: list[dict[str, Any]] = []
    all_frames = []
    for spec in PAIRS:
        old_files = {p.stem: p for p in spec["old_root"].glob("sub-*/*.h5")}
        new_files = {p.stem: p for p in spec["new_root"].glob("sub-*/*.h5")}
        stems = sorted(set(old_files) | set(new_files))
        items = [
            (stem, str(old_files.get(stem, "")), str(new_files.get(stem, "")))
            for stem in stems
        ]
        print(f"{spec['cohort']}: pairing {len(items)} stems (diffusion/drift)", flush=True)
        rows = parallel_map(_pair_one, items, workers=args.workers, desc=spec["cohort"])
        frame = pd.DataFrame(rows)
        frame["cohort"] = spec["cohort"]
        all_frames.append(frame)
        summary = _summarize(frame, spec)
        summaries.append(summary)
        write_csv(out_dir / f"diffusion_drift_ingest_pairs_{spec['cohort']}.csv", frame)

    write_csv(out_dir / "diffusion_drift_ingest_pairs_all.csv", pd.concat(all_frames, ignore_index=True))
    summary_frame = pd.DataFrame(summaries)
    write_csv(out_dir / "diffusion_drift_ingest_comparison_summary.csv", summary_frame)
    write_csv(out_dir / "diffusion_drift_ingest_pairs_all.csv", pd.concat(all_frames, ignore_index=True))

    lines = [
        "# Diffusion + drift ingest audit",
        "",
        "Paired recording-level comparison of Family A tensors and `/mnps_3d_dot`",
        "on the 2026-09-12 re-runs vs 2026-09-11 predecessors. Not a re-test of H1-H4.",
        "",
    ]
    for row in summaries:
        lines += [
            f"## {row['cohort']}",
            "",
            f"- `{row['old_bundle']}` -> `{row['new_bundle']}` ({row['n_paired']} paired stems)",
            f"- diffusion `computation_status` agree: {row['status_agree_n']}/{row['n_paired']} ({row['status_agree_frac']:.4f}); computed {row['old_computed_n']} vs {row['new_computed_n']}",
            f"- `|Δ d_eff median|` median/max: {row['d_eff_abs_diff_median']:.3g} / {row['d_eff_abs_diff_max']:.3g}",
            f"- `|Δ D_total median|` median/max: {row['d_total_abs_diff_median']:.3g} / {row['d_total_abs_diff_max']:.3g}",
            f"- `|Δ A_bD median|` median/max: {row['abd_abs_diff_median']:.3g} / {row['abd_abs_diff_max']:.3g}",
            f"- `|Δ |a_hat||` median: {row['a_hat_abs_diff_median']:.3g}",
            f"- `|Δ |mnps_3d_dot||` median/max: {row['dot_abs_diff_median']:.3g} / {row['dot_abs_diff_max']:.3g}",
            f"- `|Δ |coords_3d||` median: {row['coords_abs_diff_median']:.3g}",
            f"- `mnps_3d_dot` vs one-step Δx/Δt MAE (new, median): {row['dot_vs_step_mae_median']:.4g}",
            f"- `mnps_3d_dot` vs Savitzky-Golay (w={SAVGOL_WINDOW}, p={SAVGOL_POLY}) MAE (new, median): {row['dot_vs_savgol_mae_median']:.4g}",
            f"- fraction closer to Savitzky-Golay than one-step: {row['dot_closer_to_savgol_frac']:.3f}",
            f"- diffusion provenance `drift_source` (new, mode): `{row['new_drift_source_mode']}`",
            "",
        ]
    lines += [
        "## Interpretation",
        "",
        "If the Δ medians for `d_eff`, `D_total`, `A_bD`, `a_hat`, `mnps_3d_dot`,",
        "and coordinates sit at numerical noise, Family A on the 2026-09-12 re-runs",
        "is the same measurement as the 2026-09-11 predecessors and the existing",
        "H1-H4 / qualified-drift results do not need to be recomputed.",
        "",
        "`drift_source = not_supplied` means ingest still does not treat",
        "`mnps_3d_dot` as a qualified Itô drift for the diffusion family; `A_bD`",
        "is an alignment against that unqualified proxy. The MAE comparison",
        "says whether `/mnps_3d_dot` is closer to a raw one-step difference or",
        "to the configured Savitzky-Golay derivative.",
        "",
    ]
    (out_dir / "diffusion_drift_ingest_comparison.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(out_dir / "diffusion_drift_ingest_comparison_manifest.json", {"pairs": summaries, "savgol_window": SAVGOL_WINDOW, "savgol_poly": SAVGOL_POLY})
    print(f"Wrote diffusion/drift audit to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
