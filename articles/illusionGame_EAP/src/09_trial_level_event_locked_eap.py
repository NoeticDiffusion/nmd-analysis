"""Trial-level Illusion Game geometry analysis, event-locked via LUX sync.

Unlike the earlier session-median screens in this article, this script uses
per-trial onsets recovered from the injected LUX photosensor channel
(`mndm.pipeline.ds004587_lux_sync`, `project/scripts/28_ds004587_lux_trial_sync.py`)
and joined to MNPS geometry via NMD's generic event-locked pipeline
(`event_locked.datasets.ds004587` in `config_ingest_ds004587.yaml`). This
lets trial-level behavioral fields (illusion strength/difference, trial
type, correctness, reaction time) be tested against the geometry (m/d/e) of
the single nearest ~8s MNPS window, instead of collapsing an entire ~15
minute recording to one session median.

What this still cannot do
--------------------------
* No rest-vs-illusion neural contrast: ds004587 has zero rest-EEG in the
  source BIDS release (confirmed on disk). This script only ever sees the
  Illusion Game condition.
* No true single-trial neural resolution: MNPS windows are 8s wide with a
  4s step, while trials occur every ~1-3s, so several trials commonly share
  the same underlying window (see
  `ds004587_support.load_event_locked_trial_table`). Trial-level here means
  "nearest-window-resolved", not "independent per-trial neural sample" --
  the within-subject/cluster-robust statistics below treat trials as
  repeated, correlated measurements accordingly.
* No Jacobian/MNJ trial-locking: `build_event_locked_table` only exports
  3D MNPS (m/d/e); Jacobian metrics remain session/window-level only.
* Only runs with `qc_ok_event_sync=True` and trials inside the
  landmark-bracketed sync interval ever reach this table (enforced upstream
  by `ds004587_lux_sync.build_ig_trial_event_table`); subjects whose LUX
  channel was flat or whose landmarks did not reproduce a clean offset are
  silently absent here, not guessed at.
"""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ds004587_support import (  # noqa: E402
    apply_documented_physio_exclusions,
    bh_fdr,
    load_event_locked_trial_table,
    make_results_subdir,
    write_metadata,
)

RNG = np.random.default_rng(4587_09)
GEOMETRY_COLUMNS = ("m", "d", "e")
# Primary continuous/binary predictors, in priority order. illusion_strength
# is intentionally listed after illusion_difference: see
# ds004587_support.ILLUSION_STRENGTH_PLAUSIBLE_ABS_MAX.
PREDICTOR_COLUMNS = ("illusion_difference", "illusion_strength", "rt", "correct")
N_BOOTSTRAP = 1000
MIN_TRIALS = 6
MIN_SUBJECTS = 3


def within_subject_correlation(x: pd.Series, y: pd.Series, subject: pd.Series) -> dict:
    """Repeated-measures correlation (rmcorr): partial correlation of x, y
    controlling for subject identity via within-subject centering.

    Equivalent to the partial correlation of x and y in an ANCOVA with
    subject as a categorical covariate (Bakdash & Marusich, 2017). Degrees
    of freedom follow the same reference: ``df = n - n_subjects - 2``.
    """
    data = pd.DataFrame({"x": x, "y": y, "subject": subject}).dropna()
    n = len(data)
    n_subjects = data["subject"].nunique()
    out = {"n": n, "n_subjects": n_subjects, "rmcorr_r": np.nan, "p": np.nan, "df": np.nan}
    if n < MIN_TRIALS or n_subjects < MIN_SUBJECTS:
        return out
    x_c = data["x"] - data.groupby("subject")["x"].transform("mean")
    y_c = data["y"] - data.groupby("subject")["y"].transform("mean")
    if np.isclose(x_c.std(ddof=1), 0) or np.isclose(y_c.std(ddof=1), 0):
        return out
    r, _ = stats.pearsonr(x_c, y_c)
    dof = n - n_subjects - 2
    out.update(rmcorr_r=float(r), df=int(dof) if dof > 0 else np.nan)
    if dof > 0:
        denom = max(1e-12, 1.0 - r ** 2)
        t_stat = r * np.sqrt(dof / denom)
        out["p"] = float(2.0 * (1.0 - stats.t.cdf(abs(t_stat), dof)))
    return out


def _stability(data: pd.DataFrame, predictor: str, geometry: str) -> dict:
    """LOSO and subject-level bootstrap stability for one rmcorr association.

    Bootstrap resamples *subjects* (with replacement, keeping all of a
    resampled subject's trials together) rather than individual trials, so
    the within-subject trial correlation structure is preserved -- resampling
    trials directly would badly underestimate uncertainty.
    """
    group = data[["subject_id", predictor, geometry]].dropna()
    group.columns = ["subject", "x", "y"]
    subjects = group["subject"].unique()
    full = within_subject_correlation(group["x"], group["y"], group["subject"])
    if not np.isfinite(full["rmcorr_r"]) or len(subjects) < MIN_SUBJECTS + 1:
        return {"full_r": full["rmcorr_r"], "loso_min_r": np.nan, "loso_max_r": np.nan,
                "loso_sign_consistent": None, "bootstrap_ci_low": np.nan, "bootstrap_ci_high": np.nan,
                "n_subjects": full["n_subjects"], "n_trials": full["n"]}

    loso_r = []
    for subject in subjects:
        held_out = group.loc[group["subject"].ne(subject)]
        loso_r.append(within_subject_correlation(held_out["x"], held_out["y"], held_out["subject"])["rmcorr_r"])
    loso_r = np.asarray(loso_r, dtype=float)

    bootstrap_r = []
    for _ in range(N_BOOTSTRAP):
        sampled_subjects = RNG.choice(subjects, size=len(subjects), replace=True)
        parts = [group.loc[group["subject"].eq(s)] for s in sampled_subjects]
        sampled = pd.concat(parts, ignore_index=True)
        # Bootstrap resamples of the *same* subject id would otherwise collide
        # in the groupby demeaning step; relabel each resampled draw uniquely.
        sampled["subject"] = np.repeat(np.arange(len(sampled_subjects)), [len(p) for p in parts])
        bootstrap_r.append(within_subject_correlation(sampled["x"], sampled["y"], sampled["subject"])["rmcorr_r"])
    bootstrap_r = np.asarray(bootstrap_r, dtype=float)

    return {
        "full_r": full["rmcorr_r"],
        "loso_min_r": float(np.nanmin(loso_r)) if np.isfinite(loso_r).any() else np.nan,
        "loso_max_r": float(np.nanmax(loso_r)) if np.isfinite(loso_r).any() else np.nan,
        "loso_sign_consistent": bool(np.all(np.sign(loso_r[np.isfinite(loso_r)]) == np.sign(full["rmcorr_r"])))
        if np.isfinite(loso_r).any() else None,
        "bootstrap_ci_low": float(np.nanpercentile(bootstrap_r, 2.5)) if np.isfinite(bootstrap_r).any() else np.nan,
        "bootstrap_ci_high": float(np.nanpercentile(bootstrap_r, 97.5)) if np.isfinite(bootstrap_r).any() else np.nan,
        "n_subjects": full["n_subjects"],
        "n_trials": full["n"],
    }


def main() -> None:
    frame, sources = load_event_locked_trial_table()
    frame = apply_documented_physio_exclusions(frame, context="09_trial_level_event_locked_eap")

    predictors = [p for p in PREDICTOR_COLUMNS if p in frame.columns]
    geometry = [g for g in GEOMETRY_COLUMNS if g in frame.columns]
    if not predictors or not geometry:
        raise ValueError(
            "Trial-level EAP requires at least one behavioral predictor and one MNPS geometry "
            f"column; found predictors={predictors}, geometry={geometry}."
        )

    out = make_results_subdir("09_trial_level_event_locked_eap")

    frame["correct_numeric"] = frame["correct"].astype(float) if "correct" in frame.columns else np.nan
    if "correct" in predictors:
        predictors = [p if p != "correct" else "correct_numeric" for p in predictors]

    coverage = (
        frame.groupby("subject_id", dropna=False)
        .agg(n_trials=("event_id", "nunique"),
             **{f"{p}_nonmissing": (p, lambda s: s.notna().sum()) for p in predictors})
        .reset_index()
    )
    coverage.to_csv(out / "trial_coverage_by_subject.csv", index=False)

    rows = []
    for predictor in predictors:
        for metric in geometry:
            result = within_subject_correlation(frame[predictor], frame[metric], frame["subject_id"])
            result.update(predictor=predictor, geometry=metric)
            rows.append(result)
    direct = pd.DataFrame(rows)
    direct["p_bh"] = bh_fdr(direct["p"].to_numpy())
    direct.to_csv(out / "trial_level_rmcorr.csv", index=False)

    # Stability is restricted to the predeclared core family plus any FDR
    # survivor -- matching the house convention in 04_eap_physio_coupling.py.
    core_predictors = {"illusion_difference", "rt"}
    core_geometry = {"m", "e"}
    stability_targets = direct[
        (direct.predictor.isin(core_predictors) & direct.geometry.isin(core_geometry))
        | (direct.p_bh < 0.05)
    ]
    stability_rows = []
    for row in stability_targets.itertuples():
        stability = _stability(frame, row.predictor, row.geometry)
        stability.update(predictor=row.predictor, geometry=row.geometry)
        stability_rows.append(stability)
    pd.DataFrame(stability_rows).to_csv(out / "trial_level_stability.csv", index=False)

    write_metadata(
        out, script=Path(__file__).name, source=sources[0] if sources else Path("unknown"),
        extra={
            "n_source_parquets": len(sources),
            "predictor_columns": predictors,
            "geometry_columns": geometry,
            "n_bootstrap": N_BOOTSTRAP,
            "granularity_note": (
                "Each row is one trial collapsed onto its single nearest MNPS "
                "window (8s window / 4s step); multiple trials commonly share "
                "a window. rmcorr/LOSO/bootstrap treat trials as repeated, "
                "subject-clustered measurements, not independent samples."
            ),
            "scope_note": (
                "No rest-vs-illusion contrast is possible (no rest EEG in "
                "ds004587); no Jacobian/MNJ trial-locking is available."
            ),
        },
    )
    print(f"Wrote trial-level event-locked EAP outputs to {out}")


if __name__ == "__main__":
    main()
