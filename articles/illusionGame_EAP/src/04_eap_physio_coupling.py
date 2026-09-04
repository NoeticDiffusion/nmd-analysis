"""Direct and HRV-adjusted anchor--geometry coupling analysis for ds004587."""
from __future__ import annotations

from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ds004587_support import (MNJ_COLUMNS, MNPS_COLUMNS, apply_documented_physio_exclusions,
    bh_fdr, concurrent_subject_condition_medians, load_analysis_table, make_results_subdir, spearman,
    subject_condition_medians, valid_anchor_columns, write_metadata)

RNG = np.random.default_rng(4587)

def partial_rank(x: pd.Series, y: pd.Series, z: pd.Series) -> dict:
    data = pd.DataFrame({"x": x, "y": y, "z": z}).dropna()
    if len(data) < 6:
        return {"n": len(data), "partial_spearman_r": np.nan, "p": np.nan}
    ranked = data.rank()
    fit_x = stats.linregress(ranked.z, ranked.x)
    fit_y = stats.linregress(ranked.z, ranked.y)
    rx = ranked.x - (fit_x.intercept + fit_x.slope * ranked.z)
    ry = ranked.y - (fit_y.intercept + fit_y.slope * ranked.z)
    r, p = stats.pearsonr(rx, ry)
    return {"n": len(data), "partial_spearman_r": float(r), "p": float(p)}

def main() -> None:
    frame, source = load_analysis_table(("subject_id", "condition"))
    frame = apply_documented_physio_exclusions(frame, context="04_eap_physio_coupling")
    anchors = valid_anchor_columns(frame)
    mnps_geometry = [column for column in MNPS_COLUMNS if column in frame]
    mnj_geometry = [column for column in MNJ_COLUMNS if column in frame]
    geometry = [*mnps_geometry, *mnj_geometry]
    if not anchors or not geometry:
        raise ValueError("EAP coupling requires at least one observed anchor and one MNPS/MNJ metric.")

    out = make_results_subdir("04_eap_physio_coupling")

    # Whole-session per-subject summary, kept for descriptive/back-compat
    # export. MNPS columns (m/d/e) are defined at every window, so a
    # whole-session anchor median is already time-matched to them. MNJ
    # (Jacobian) columns are populated only at sparse Jacobian centres, so
    # this table's MNJ medians describe fewer, different windows than its
    # anchor medians here and must NOT be read off directly for anchor x MNJ
    # correlation; see the concurrent pairing used below instead.
    med = subject_condition_medians(frame, [*anchors, *geometry])
    med.to_csv(out / "subject_condition_medians.csv", index=False)

    rows = []
    for condition, sub in med.groupby("condition", dropna=False):
        for anchor in anchors:
            for metric in mnps_geometry:
                row = spearman(sub[anchor], sub[metric])
                row.update(condition=condition, anchor=anchor, geometry=metric,
                            concurrent_with_jacobian_centers=False)
                rows.append(row)
    for condition, window_rows in frame.groupby("condition", dropna=False):
        for anchor in anchors:
            for metric in mnj_geometry:
                # MNJ metrics exist only at sparse Jacobian centres. Use the
                # anchor value observed at those same windows rather than a
                # whole-session anchor summary, which would otherwise compare
                # geometry from a handful of windows against physiology
                # averaged over many windows the Jacobian never described.
                pair = concurrent_subject_condition_medians(window_rows, anchor, metric)
                row = spearman(pair[anchor], pair[metric])
                row.update(condition=condition, anchor=anchor, geometry=metric,
                           concurrent_with_jacobian_centers=True)
                rows.append(row)
    direct = pd.DataFrame(rows)
    direct["p_bh_condition"] = direct.groupby("condition")["p"].transform(bh_fdr)
    direct.to_csv(out / "direct_coupling.csv", index=False)

    hrv = "ecg_hrv_rmssd_ms"
    adjusted = []
    if hrv in med:
        for condition, sub in med.groupby("condition", dropna=False):
            for anchor in [a for a in anchors if a != hrv]:
                for metric in mnps_geometry:
                    row = partial_rank(sub[anchor], sub[metric], sub[hrv])
                    row.update(condition=condition, anchor=anchor, geometry=metric, control=hrv,
                               concurrent_with_jacobian_centers=False)
                    adjusted.append(row)
    if hrv in frame.columns:
        for condition, window_rows in frame.groupby("condition", dropna=False):
            for anchor in [a for a in anchors if a != hrv]:
                for metric in mnj_geometry:
                    pair = concurrent_subject_condition_medians(window_rows, anchor, metric, extra_columns=(hrv,))
                    row = partial_rank(pair[anchor], pair[metric], pair[hrv])
                    row.update(condition=condition, anchor=anchor, geometry=metric, control=hrv,
                               concurrent_with_jacobian_centers=True)
                    adjusted.append(row)
    partial = pd.DataFrame(adjusted)
    if not partial.empty:
        partial["p_bh_condition"] = partial.groupby("condition")["p"].transform(bh_fdr)
    partial.to_csv(out / "hrv_controlled_coupling.csv", index=False)

    # Stability is restricted to the predeclared core family plus any FDR survivor;
    # bootstrapping every exploratory cross-product would add computation without
    # strengthening a claim.
    core_anchors = {"anchor_index", "resp_anchor_index", "ecg_hrv_rmssd_ms"}
    core_geometry = {"m", "d", "e", "frobenius_norm"}
    stability_targets = direct[
        (direct.anchor.isin(core_anchors) & direct.geometry.isin(core_geometry))
        | (direct.p_bh_condition < .05)
    ]
    stability = []
    for row in stability_targets.itertuples():
        if row.geometry in mnj_geometry:
            window_rows = frame[frame.condition.eq(row.condition)]
            group = concurrent_subject_condition_medians(window_rows, row.anchor, row.geometry)[
                ["subject_id", row.anchor, row.geometry]].dropna()
        else:
            group = med[med.condition.eq(row.condition)][["subject_id", row.anchor, row.geometry]].dropna()
        if len(group) < 6:
            continue
        full = row.spearman_r
        loo = [spearman(group.loc[group.subject_id.ne(sub), row.anchor],
                        group.loc[group.subject_id.ne(sub), row.geometry])["spearman_r"]
               for sub in group.subject_id]
        bootstrap = []
        for _ in range(1000):
            sampled = group.iloc[RNG.integers(0, len(group), len(group))]
            bootstrap.append(spearman(sampled[row.anchor], sampled[row.geometry])["spearman_r"])
        stability.append({"condition": row.condition, "anchor": row.anchor, "geometry": row.geometry,
                          "full_r": full, "looso_min_r": np.nanmin(loo), "looso_max_r": np.nanmax(loo),
                          "looso_sign_consistent": bool(np.all(np.sign(loo) == np.sign(full))),
                          "bootstrap_ci_low": np.nanpercentile(bootstrap, 2.5),
                          "bootstrap_ci_high": np.nanpercentile(bootstrap, 97.5),
                          "concurrent_with_jacobian_centers": row.geometry in mnj_geometry})
    pd.DataFrame(stability).to_csv(out / "coupling_stability.csv", index=False)
    write_metadata(out, script=Path(__file__).name, source=source,
                   extra={"anchor_columns": anchors, "geometry_columns": geometry,
                          "mnj_geometry_columns_using_jacobian_center_concurrent_anchors": mnj_geometry})
    print(f"Wrote EAP coupling outputs to {out}")

if __name__ == "__main__":
    main()
