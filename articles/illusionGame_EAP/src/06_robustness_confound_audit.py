"""Robustness audit for paired rest-versus-illusion geometry contrasts."""
from __future__ import annotations

from pathlib import Path
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ds004587_support import (MNJ_COLUMNS, MNPS_COLUMNS, QC_COLUMNS, bh_fdr, classify_condition,
    load_analysis_table, make_results_subdir, paired_wilcoxon, subject_condition_medians, write_metadata)

RNG = np.random.default_rng(4587)

def main() -> None:
    frame, source = load_analysis_table(("subject_id", "condition"))
    frame["condition"] = frame.condition.map(classify_condition)
    frame = frame[frame.condition.isin(("rest", "illusion"))].copy()
    metrics = [column for column in [*MNPS_COLUMNS, *MNJ_COLUMNS] if column in frame]
    if not metrics:
        raise ValueError("Robustness audit requires at least one MNPS/MNJ geometry metric.")
    out = make_results_subdir("06_robustness_confound_audit")
    counts = frame.groupby(["subject_id", "condition"]).size().rename("n_rows").reset_index()
    counts.to_csv(out / "epoch_count_by_subject_condition.csv", index=False)
    med = subject_condition_medians(frame, metrics)
    rows = []
    for metric in metrics:
        wide = med.pivot(index="subject_id", columns="condition", values=metric).dropna()
        if not {"rest", "illusion"} <= set(wide) or len(wide) < 5:
            continue
        base = paired_wilcoxon(wide.illusion, wide.rest)
        difference = (wide.illusion - wide.rest).to_numpy()
        boot = [np.mean(difference[RNG.integers(0, len(difference), len(difference))]) for _ in range(2000)]
        signs = RNG.choice((-1, 1), size=(5000, len(difference)))
        observed = abs(np.mean(difference))
        permutation_p = (np.abs((signs * difference).mean(axis=1)) >= observed).mean()
        looso = [np.mean(np.delete(difference, index)) for index in range(len(difference))]
        base.update(metric=metric, bootstrap_mean_ci_low=np.percentile(boot, 2.5),
                    bootstrap_mean_ci_high=np.percentile(boot, 97.5), permutation_p=permutation_p,
                    looso_sign_consistent=bool(np.all(np.sign(looso) == np.sign(np.mean(difference)))))
        rows.append(base)
    audit = pd.DataFrame(rows)
    if audit.empty:
        raise ValueError("No metrics had at least five paired rest/illusion subjects for robustness analysis.")
    audit["p_bh"] = bh_fdr(audit.p)
    audit.to_csv(out / "paired_robustness.csv", index=False)
    qc = [column for column in QC_COLUMNS if column in frame]
    if qc:
        frame.groupby("condition")[qc].mean(numeric_only=True).reset_index().to_csv(
            out / "artifact_qc_balance.csv", index=False)
    confounds = [column for column in ("eog_artifact_fraction", "eog_blink_rate", "resp_rate_bpm",
                 "ecg_hrv_hr_mean_bpm", "reaction_time", "rt") if column in frame]
    pd.DataFrame({"candidate_confound": confounds,
                  "available": True,
                  "note": "Available fields only; no adjusted effect is claimed without a pre-specified model."}).to_csv(
        out / "conventional_controls_inventory.csv", index=False)
    write_metadata(out, script=Path(__file__).name, source=source,
                   extra={"metrics": metrics, "qc_columns": qc, "confound_fields": confounds})
    print(f"Wrote robustness-audit outputs to {out}")

if __name__ == "__main__":
    main()
