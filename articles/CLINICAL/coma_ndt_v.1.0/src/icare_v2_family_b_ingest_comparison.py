"""Paired Family-B / spectral-abscissa comparison across I-CARE ingest generations.

Compares the gated Jacobian metrics on matching recordings between:

- part1: 20260911_125829 (predecessor) vs 20260912_094016 (re-run)
- part2: 20260911_123135 (predecessor) vs 20260912_094010 (re-run)

and reports the already-extracted CPC1 vs CPC5 contrasts on the predecessor
bundles (the scientific contrast we actually have). The re-runs added
neighborhood provenance but did not change fit quality; this script checks
that claim on spectral abscissa specifically, not just gate counts.

Not a primary confirmatory test of H5/F_reactive. Family B remains
not-testable under the honest fit-fidelity gate.
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
    cliffs_delta,
    cohens_d,
    finite_array,
    mean_finite,
    parallel_map,
    parse_run_stem,
    participant_meta_from_handle,
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
        "contrasts": ARTICLE_DIR / "results" / "part1_corrected" / "outcome_contrasts.csv",
        "mnj_runs": ARTICLE_DIR / "results" / "part1_corrected" / "mnj_v3_run_level.csv",
    },
    {
        "cohort": "part2_confirmatory",
        "old_id": "20260911_123135",
        "new_id": "20260912_094010",
        "old_root": Path(r"J:/repos/nmd-analysis/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260911_123135"),
        "new_root": Path(r"J:/repos/nmd-analysis/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260912_094010"),
        "contrasts": ARTICLE_DIR / "results" / "part2_confirmatory" / "outcome_contrasts.csv",
        "mnj_runs": ARTICLE_DIR / "results" / "part2_confirmatory" / "mnj_v3_run_level.csv",
    },
)


def _sval(value: Any) -> Any:
    return as_scalar(value)


def _read_jacobian(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "exists": path.is_file(),
        "status": None,
        "failure_reason": None,
        "rel_mse": float("nan"),
        "knn_k": float("nan"),
        "min_samples": float("nan"),
        "n_neighborhood_samples_median": float("nan"),
        "n_windows": 0,
        "n_valid_alpha": 0,
        "alpha_mean": float("nan"),
        "omega_mean": float("nan"),
        "f_reactive": float("nan"),
        "cpc": None,
        "subject_id": parse_run_stem(path.stem)["subject_id"],
        "stem": path.stem,
    }
    if not out["exists"]:
        return out
    try:
        with h5py.File(path, "r") as handle:
            meta = participant_meta_from_handle(handle)
            out["cpc"] = meta.get("cpc")
            gpath = "/jacobian/derived_metrics/v1"
            if gpath not in handle:
                return out
            group = handle[gpath]
            if "computation_status" in group:
                out["status"] = str(_sval(group["computation_status"][()]))
            if "failure_reason" in group:
                out["failure_reason"] = str(_sval(group["failure_reason"][()]))
            prov = group["provenance"] if "provenance" in group else None
            if prov is not None:
                for key, dest in (
                    ("rel_mse_baseline_median", "rel_mse"),
                    ("knn_k", "knn_k"),
                    ("min_samples", "min_samples"),
                    ("n_neighborhood_samples_median", "n_neighborhood_samples_median"),
                ):
                    if key in prov.attrs:
                        out[dest] = float(_sval(prov.attrs[key])) if _sval(prov.attrs[key]) is not None else float("nan")
                    elif key in prov:
                        obj = prov[key]
                        if hasattr(obj, "shape") and obj.shape == ():
                            out[dest] = float(_sval(obj[()]))
            if "series" in group and "spectral_abscissa" in group["series"]:
                alpha = np.asarray(group["series"]["spectral_abscissa"][:], dtype=float)
                omega = (
                    np.asarray(group["series"]["numerical_abscissa"][:], dtype=float)
                    if "numerical_abscissa" in group["series"]
                    else np.full(alpha.shape, np.nan)
                )
                valid = np.isfinite(alpha)
                out["n_windows"] = int(alpha.size)
                out["n_valid_alpha"] = int(valid.sum())
                if valid.any():
                    a = alpha[valid]
                    w = omega[valid] if omega.size == alpha.size else np.full(a.size, np.nan)
                    out["alpha_mean"] = mean_finite(a)
                    out["omega_mean"] = mean_finite(w)
                    if np.isfinite(w).all():
                        out["f_reactive"] = float(np.mean((a < 0) & (w > 0)))
    except Exception as exc:  # noqa: BLE001
        out["read_error"] = f"{type(exc).__name__}: {exc}"
    return out


def _pair_one(item: tuple[str, str, str]) -> dict[str, Any]:
    stem, old_path, new_path = item
    old = _read_jacobian(Path(old_path))
    new = _read_jacobian(Path(new_path))
    mse_diff = (
        float(new["rel_mse"] - old["rel_mse"])
        if np.isfinite(old["rel_mse"]) and np.isfinite(new["rel_mse"])
        else float("nan")
    )
    alpha_diff = (
        float(new["alpha_mean"] - old["alpha_mean"])
        if np.isfinite(old["alpha_mean"]) and np.isfinite(new["alpha_mean"])
        else float("nan")
    )
    return {
        "stem": stem,
        "subject_id": old["subject_id"] or new["subject_id"],
        "cpc": old["cpc"] if old["cpc"] is not None else new["cpc"],
        "old_exists": old["exists"],
        "new_exists": new["exists"],
        "old_status": old["status"],
        "new_status": new["status"],
        "status_match": old["status"] == new["status"],
        "old_failure": old["failure_reason"],
        "new_failure": new["failure_reason"],
        "old_rel_mse": old["rel_mse"],
        "new_rel_mse": new["rel_mse"],
        "rel_mse_diff": mse_diff,
        "old_knn_k": old["knn_k"],
        "new_knn_k": new["knn_k"],
        "old_min_samples": old["min_samples"],
        "new_min_samples": new["min_samples"],
        "new_nhood_median": new["n_neighborhood_samples_median"],
        "old_n_valid_alpha": old["n_valid_alpha"],
        "new_n_valid_alpha": new["n_valid_alpha"],
        "old_alpha_mean": old["alpha_mean"],
        "new_alpha_mean": new["alpha_mean"],
        "alpha_mean_diff": alpha_diff,
        "old_f_reactive": old["f_reactive"],
        "new_f_reactive": new["f_reactive"],
        "old_n_windows": old["n_windows"],
        "new_n_windows": new["n_windows"],
    }


def _summarize_pair(frame: pd.DataFrame, spec: dict[str, Any]) -> dict[str, Any]:
    both = frame[frame["old_exists"] & frame["new_exists"]]
    mse = finite_array(both["rel_mse_diff"])
    alpha = finite_array(both["alpha_mean_diff"])
    old_computed = int((both["old_status"] == "computed").sum())
    new_computed = int((both["new_status"] == "computed").sum())
    return {
        "cohort": spec["cohort"],
        "old_bundle": spec["old_id"],
        "new_bundle": spec["new_id"],
        "n_paired_stems": int(len(both)),
        "n_old_only": int((frame["old_exists"] & ~frame["new_exists"]).sum()),
        "n_new_only": int((frame["new_exists"] & ~frame["old_exists"]).sum()),
        "status_agree_n": int(both["status_match"].sum()),
        "status_agree_frac": float(both["status_match"].mean()) if len(both) else float("nan"),
        "old_n_computed": old_computed,
        "new_n_computed": new_computed,
        "rel_mse_abs_diff_median": float(np.median(np.abs(mse))) if mse.size else float("nan"),
        "rel_mse_abs_diff_max": float(np.max(np.abs(mse))) if mse.size else float("nan"),
        "rel_mse_exact_match_n": int((np.abs(both["rel_mse_diff"]) < 1e-15).sum()) if len(both) else 0,
        "n_both_finite_alpha": int(alpha.size),
        "alpha_mean_abs_diff_median": float(np.median(np.abs(alpha))) if alpha.size else float("nan"),
        "alpha_mean_abs_diff_max": float(np.max(np.abs(alpha))) if alpha.size else float("nan"),
        "new_has_knn_k_n": int(np.isfinite(both["new_knn_k"]).sum()),
        "old_has_knn_k_n": int(np.isfinite(both["old_knn_k"]).sum()),
    }


def _cpc_alpha_from_existing(mnj_path: Path) -> dict[str, Any]:
    if not mnj_path.exists():
        return {}
    runs = pd.read_csv(mnj_path)
    computed = runs[runs["jacobian_metrics_3d_status"] == "computed"].copy()
    computed["alpha_mean"] = pd.to_numeric(computed["alpha_mean"], errors="coerce")
    computed = computed[np.isfinite(computed["alpha_mean"])]
    out: dict[str, Any] = {
        "n_computed_runs": int(len(computed)),
        "n_computed_subjects": int(computed["subject_id"].nunique()) if not computed.empty else 0,
    }
    if computed.empty or "cpc" not in computed.columns:
        return out
    good = finite_array(computed.loc[computed["cpc"] == 1, "alpha_mean"])
    poor = finite_array(computed.loc[computed["cpc"] == 5, "alpha_mean"])
    out.update(
        {
            "n_computed_runs_cpc1": int(good.size),
            "n_computed_runs_cpc5": int(poor.size),
            "alpha_cpc1_mean": float(np.mean(good)) if good.size else float("nan"),
            "alpha_cpc5_mean": float(np.mean(poor)) if poor.size else float("nan"),
            "alpha_cohens_d_run_level": cohens_d(good, poor),
            "alpha_cliffs_delta_run_level": cliffs_delta(good, poor),
        }
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ARTICLE_DIR / "results" / "replication",
    )
    args = parser.parse_args()
    out_dir = args.out_dir
    summaries: list[dict[str, Any]] = []
    all_pairs: list[pd.DataFrame] = []

    for spec in PAIRS:
        old_files = {p.stem: p for p in spec["old_root"].glob("sub-*/*.h5")}
        new_files = {p.stem: p for p in spec["new_root"].glob("sub-*/*.h5")}
        stems = sorted(set(old_files) | set(new_files))
        items = [
            (
                stem,
                str(old_files[stem]) if stem in old_files else "",
                str(new_files[stem]) if stem in new_files else "",
            )
            for stem in stems
        ]
        print(f"{spec['cohort']}: pairing {len(items)} stems", flush=True)
        rows = parallel_map(_pair_one, items, workers=args.workers, desc=spec["cohort"])
        frame = pd.DataFrame(rows)
        frame["cohort"] = spec["cohort"]
        all_pairs.append(frame)
        summary = _summarize_pair(frame, spec)
        summary.update(_cpc_alpha_from_existing(spec["mnj_runs"]))
        if spec["contrasts"].exists():
            contrasts = pd.read_csv(spec["contrasts"])
            alpha_row = contrasts[contrasts["metric"] == "alpha_mean"]
            f_row = contrasts[contrasts["metric"] == "f_reactive"]
            if not alpha_row.empty:
                r = alpha_row.iloc[0]
                summary.update(
                    {
                        "patient_alpha_n_cpc1": int(r["n_cpc1"]),
                        "patient_alpha_n_cpc5": int(r["n_cpc5"]),
                        "patient_alpha_cpc1_mean": float(r["cpc1_mean"]),
                        "patient_alpha_cpc5_mean": float(r["cpc5_mean"]),
                        "patient_alpha_cohens_d": float(r["cohens_d_cpc1_minus_cpc5"]),
                        "patient_alpha_mw_p": float(r["mannwhitney_p"]),
                        "patient_alpha_family_testable": bool(r["family_testable"]),
                    }
                )
            if not f_row.empty:
                r = f_row.iloc[0]
                summary.update(
                    {
                        "patient_f_reactive_n_cpc1": int(r["n_cpc1"]),
                        "patient_f_reactive_n_cpc5": int(r["n_cpc5"]),
                        "patient_f_reactive_cohens_d": float(r["cohens_d_cpc1_minus_cpc5"]),
                        "patient_f_reactive_mw_p": float(r["mannwhitney_p"]),
                    }
                )
        summaries.append(summary)
        write_csv(out_dir / f"family_b_ingest_pairs_{spec['cohort']}.csv", frame)

    summary_frame = pd.DataFrame(summaries)
    write_csv(out_dir / "family_b_abscissa_comparison_summary.csv", summary_frame)
    if all_pairs:
        write_csv(out_dir / "family_b_ingest_pairs_all.csv", pd.concat(all_pairs, ignore_index=True))

    lines = [
        "# Family B / spectral abscissa comparison",
        "",
        "Paired recording-level comparison of gated Jacobian metrics on the",
        "2026-09-12 re-runs vs the 2026-09-11 predecessor bundles, plus the",
        "already-computed CPC1 vs CPC5 patient-level contrasts on the",
        "predecessors. Family B is **not testable** under the honest",
        "fit-fidelity gate; numbers below are diagnostic, not a finding.",
        "",
    ]
    for row in summaries:
        lines += [
            f"## {row['cohort']}",
            "",
            f"- bundles: `{row['old_bundle']}` -> `{row['new_bundle']}`",
            f"- paired stems: {row['n_paired_stems']} (old-only {row['n_old_only']}, new-only {row['n_new_only']})",
            f"- computation_status agreement: {row['status_agree_n']}/{row['n_paired_stems']} ({row['status_agree_frac']:.4f})",
            f"- `computed` runs: old {row['old_n_computed']} / new {row['new_n_computed']}",
            f"- `|Δ rel_mse|` median/max: {row['rel_mse_abs_diff_median']:.3g} / {row['rel_mse_abs_diff_max']:.3g}",
            f"- both-finite α mean runs: {row['n_both_finite_alpha']}; `|Δ α_mean|` median/max: {row['alpha_mean_abs_diff_median']:.3g} / {row['alpha_mean_abs_diff_max']:.3g}",
            f"- new provenance has `knn_k`: {row['new_has_knn_k_n']}; old: {row['old_has_knn_k_n']}",
            "",
        ]
        if row.get("patient_alpha_n_cpc1") is not None:
            lines += [
                "Patient-level CPC contrast on predecessor bundle (gated α, primary 0-12h):",
                "",
                f"- α mean: n={row['patient_alpha_n_cpc1']}/{row['patient_alpha_n_cpc5']}, "
                f"CPC1={row['patient_alpha_cpc1_mean']:.4g}, CPC5={row['patient_alpha_cpc5_mean']:.4g}, "
                f"d={row['patient_alpha_cohens_d']:.3g}, p={row['patient_alpha_mw_p']:.3g}, "
                f"testable={row['patient_alpha_family_testable']}",
                f"- F_reactive: n={row['patient_f_reactive_n_cpc1']}/{row['patient_f_reactive_n_cpc5']}, "
                f"d={row['patient_f_reactive_cohens_d']:.3g}, p={row['patient_f_reactive_mw_p']:.3g}",
                "",
            ]
        if row.get("n_computed_runs"):
            lines += [
                "Run-level α among `computed` recordings on the predecessor extraction:",
                "",
                f"- computed runs: {row['n_computed_runs']} ({row.get('n_computed_runs_cpc1', 'n/a')} CPC1 / {row.get('n_computed_runs_cpc5', 'n/a')} CPC5)",
                f"- run-level α means: CPC1={row.get('alpha_cpc1_mean', float('nan')):.4g}, CPC5={row.get('alpha_cpc5_mean', float('nan')):.4g}, d={row.get('alpha_cohens_d_run_level', float('nan')):.3g}",
                "",
            ]
    lines += [
        "## Interpretation",
        "",
        "If `|Δ rel_mse|` and `|Δ α_mean|` are at numerical noise and `computed`",
        "counts match, the 2026-09-12 re-runs did not change the local-generator",
        "fit. The CPC1 vs CPC5 α contrast then remains the same gated, small-n",
        "descriptive comparison already reported (sign flips across cohorts;",
        "not a test of the hypothesis).",
        "",
    ]
    (out_dir / "family_b_abscissa_comparison.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(out_dir / "family_b_abscissa_comparison_manifest.json", {"pairs": summaries})
    print(f"Wrote Family B comparison to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
