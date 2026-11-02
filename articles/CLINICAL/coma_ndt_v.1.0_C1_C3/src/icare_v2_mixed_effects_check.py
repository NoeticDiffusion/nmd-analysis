"""Run-level mixed-effects robustness check for Family A H1-H3.

The primary analysis (outcome_contrasts.csv) collapses each patient's runs
in the primary window to a single per-patient median before the CPC1 vs
CPC5 Mann-Whitney test. This script instead fits, per metric, a linear
mixed model on the (pre-collapse) run-level values:

    metric ~ C(contrast_group), random intercept per subject_id

using all runs in the primary window rather than one number per patient.
This uses more of the within-subject variance and is a cross-check on
whether the patient-median collapse is hiding or manufacturing an effect.
It is a robustness check, not a replacement for the pre-specified primary
test.
"""
from __future__ import annotations

import argparse
import warnings
from typing import Any

import numpy as np
import pandas as pd

from icare_v2_common import (
    add_common_args,
    outcome_label,
    resolve_pipeline_config,
    write_csv,
    write_json,
)

METRICS = (
    ("d_eff_a_median", "H1"),
    ("h_tilde_a_median", "H2"),
    ("e_perp_median", "H3"),
)


def _fit_mixed(frame: pd.DataFrame, metric: str, cfg) -> dict[str, Any]:
    import statsmodels.formula.api as smf

    work = frame[["subject_id", "contrast_group", metric]].copy()
    work[metric] = pd.to_numeric(work[metric], errors="coerce")
    work = work[np.isfinite(work[metric])]
    work = work[work["contrast_group"].isin([cfg.good_label, cfg.poor_label])]
    n_subjects = work["subject_id"].nunique()
    n_rows = len(work)
    runs_per_subject = work.groupby("subject_id").size()
    out: dict[str, Any] = {
        "metric": metric,
        "n_runs": int(n_rows),
        "n_subjects": int(n_subjects),
        "mean_runs_per_subject": float(runs_per_subject.mean()) if n_subjects else float("nan"),
        "max_runs_per_subject": int(runs_per_subject.max()) if n_subjects else 0,
        "n_subjects_with_gt1_run": int((runs_per_subject > 1).sum()),
        "coef_cpc1_minus_cpc5": float("nan"),
        "se": float("nan"),
        "z": float("nan"),
        "p_value": float("nan"),
        "converged": False,
        "error": None,
    }
    if n_rows < 4 or work["contrast_group"].nunique() < 2:
        out["error"] = "insufficient_data"
        return out
    work = work.rename(columns={metric: "value"})
    # good_label is the reference so the coefficient reads as CPC1 minus CPC5,
    # matching the sign convention of cohens_d_cpc1_minus_cpc5 in outcome_contrasts.csv.
    work["contrast_group"] = pd.Categorical(work["contrast_group"], categories=[cfg.poor_label, cfg.good_label])
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = smf.mixedlm("value ~ C(contrast_group)", work, groups=work["subject_id"])
            result = model.fit(reml=True, method="lbfgs")
        coef_name = [c for c in result.params.index if c != "Intercept" and "Group Var" not in c]
        if coef_name:
            name = coef_name[0]
            out["coef_cpc1_minus_cpc5"] = float(result.params[name])
            out["se"] = float(result.bse[name])
            out["z"] = float(result.tvalues[name])
            out["p_value"] = float(result.pvalues[name])
        out["converged"] = bool(getattr(result, "converged", True))
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = resolve_pipeline_config(args)
    in_dir = args.input_dir or cfg.output_dir
    out_dir = cfg.output_dir
    runs = pd.read_csv(in_dir / "diffusion_geometry_run_level.csv")
    runs = runs[runs.get("in_primary_window", False) == True]  # noqa: E712
    runs["contrast_group"] = [outcome_label(v, cfg) for v in runs.get("cpc", [])]

    rows = []
    for metric, hyp in METRICS:
        if metric not in runs.columns:
            continue
        row = _fit_mixed(runs, metric, cfg)
        row["hypothesis"] = hyp
        rows.append(row)
    frame = pd.DataFrame(rows)
    write_csv(out_dir / "mixed_effects_check.csv", frame)
    write_json(
        out_dir / "mixed_effects_check_manifest.json",
        {
            "note": (
                "Run-level linear mixed model (subject random intercept) as a robustness "
                "cross-check on the patient-median Mann-Whitney primary test. Positive "
                "coef_cpc1_minus_cpc5 matches the H1-H3 prediction direction (CPC1 > CPC5)."
            ),
            "bundle_id": cfg.bundle_id,
            "confirmatory_status": cfg.confirmatory_status,
        },
    )
    print(f"Wrote mixed-effects check for {len(rows)} metrics to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
