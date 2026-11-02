# ds04511 NDT v1.0

Within-subject Rest / Cognitive Control (CC) / Gambling (GG) analysis of OpenNeuro
`ds004511` under Noetic Diffusion Theory (NDT) v1.0.

This is a new article branch. It is not a rewrite of
`articles/Neural flow geometry differentiates gambling and cognitive control`,
which asked a different question (embodied anchoring / MNJ Frobenius vs physiology).
The present branch starts from chart occupancy, Meta-Noetic Jacobian (MNJ) invariants,
L1 local law, and recording-level reachability summaries on the 21 September 2026
dynamical-families export.

## Data

- Accession: OpenNeuro `ds004511` (Makowski, Pham & Lau; CC0)
- NMD export: `data/raw/neuralmanifolddynamics_ds004511_20260921_050009`
- 134 H5 recordings, 45 subjects; Rest 45, CC 45, GG 44
- Documented gap: `sub-S200203` has no Gambling Game EEG
- Coordinate contract: `subject_anchored`

## How to run

From the repository root, with the project virtualenv:

```
python -m pytest articles/ds04511_ndt_v.1.0/tests -q
python articles/ds04511_ndt_v.1.0/src/ds04511_collect.py
python articles/ds04511_ndt_v.1.0/src/ds04511_task_part1.py
python articles/ds04511_ndt_v.1.0/src/ds04511_l4_qc.py
python articles/ds04511_ndt_v.1.0/src/ds04511_level_part1.py
python articles/ds04511_ndt_v.1.0/src/ds04511_duration_robustness.py
python articles/ds04511_ndt_v.1.0/src/ds04511_l1_duration_robustness.py
python articles/ds04511_ndt_v.1.0/src/ds04511_estimator_task_interaction.py
python articles/ds04511_ndt_v.1.0/src/ds04511_estimator_concordance.py
```

Collection refuses a non-empty output directory. Contrasts read H5 directly and
do not run parquet ingest. L4 QC audits the three invalid reachability
certificates and the degenerate `d_eff` readout. The L2/L3 panel is a separate
Wilcoxon family from occupancy / L1 / L4. In the corrected task panel,
`reach_d_eff` remains visible as QC but is excluded from the substantive BH and
Friedman families. The duration diagnostic re-aggregates exported chart-alpha
over a deterministic 400-s prefix and does not re-fit a measurement.

## Status

Exploratory. The 21 September 2026 article source and S1--S5 supplements are
complete and compile to `output/`; G4 lock and external replication are not
completed. Occupancy, MNJ, local law, one-step L2/L3, and reachability are not
interchangeable. Chart-Jacobian α is not one-step L3: L3 α is the spectral
abscissa of the matrix-log generator proxy `log(Phi)/dt` on its identified
lag-1 support, not of `Phi` itself. Lag-2 was attempted but is too sparse and
task-imbalanced for inference.

The bounded lag-1 QC identifies 13 reproducible fidelity-gate failures (12
Rest, 1 CC, 0 GG), not absent or irregular recordings. Read
`results/v1_lag1_qc_20260921/lag1_qc.md` before interpreting partial L2/L3
coverage. `reach_d_eff` is method-limited and must not be reported as a
dimension contrast. The corrected task panel and complete L1 supplement are in
`results/v1_task_20260922_d_eff_qc_excluded/`. The fixed-duration chart-alpha
sensitivity and L4 duration audit are in
`results/v1_duration_robustness_20260922/`; they do not establish a
duration-robust L4 effect. The complete fixed-prefix L1 sensitivity is in
`results/v1_l1_duration_robustness_20260922/`; it supports the drift-norm
pattern but shows attenuation of several diffusion results.
The exploratory common-support estimator-by-task interaction is in
`results/v1_estimator_task_interaction_20260922/`; it uses estimator-specific
pooled robust z calibration and must not be read as a raw-unit comparison.
The frozen common-support concordance diagnostic and scatter are in
`results/v1_estimator_concordance_20260922/` and
`figures/results/ds004511_common_support_concordance_20260922.svg`; its
Spearman/sign summaries are descriptive and use the same standardized axes.

## Figures

Generate the result-derived SVG/PNG figures with:

```powershell
J:\repos\nmd-analysis\.venv\Scripts\python.exe src\generate_figures.py
```

Outputs are written to `figures/results/`. The conceptual pipeline figure in
`figures/conceptual/` is explanatory only and contains no empirical result.
