// S6 Internal Changelog — I-CARE v2 CPC1 vs CPC5 article.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S6 Internal Changelog",
  short-title: "S6 Changelog - I-CARE v2",
  subtitle: "Internal analysis provenance and manuscript revision history",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope and intent

Internal working document for the I-CARE v2 CPC 1 vs CPC 5 analysis. Public
Methods should cite the I-CARE 2.1 accession, the measurement-run identifier,
and the analysis configuration, not local paths.

= Analysis provenance

- Dataset: PhysioNet I-CARE 2.1 (`physionet_icare_2_1`).
- Measurement-run identifier: `neuralmanifolddynamics_physionet_icare_2_1_20260904_225047`
  (`mndm_version` 3.0.0, `schema_version` `mnps_tensor_spec_v2_4`,
  `primary_coordinate_contract=subject_anchored`).
- Analysis version: article-local `coma_ndt_v.1.0` pipeline, 2026-09-11.
- Configuration: `config/icare_v2_analysis_config.yaml`.
- Contrast: CPC = 1 vs CPC = 5, primary EEG-anchor window `0_12h`.
- Confirmatory status: `exploratory_pending_part2` (single bundle; 161 subjects).
- Software: repository `nmd_analysis` readers (`dynamical_families`,
  `local_dynamics` paths, `h5_contract`, `reachability_core`) plus article-local
  scripts under `src/`.

= Changelog

== 2026-09-11 — pipeline buildout and part1-equivalent run

- Implemented inventory, time-bin assignment, diffusion-geometry extraction
  (H1–H4), MNJ-v3 extraction (`F_reactive` / `F_contract` / `F_unstable`),
  reachability horizon recompute (h = 1, 2, 4), merge, QC, contrasts, and
  figures.
- Smoke-tested on 5 CPC 1 + 5 CPC 5 subjects (315 runs) before the full
  3484-file run. Fixed a diffusion status-field `bytes` decode bug found in
  the smoke test.
- Full-run coverage: 161 subjects, 3484 readable H5 files, 17 empty run
  directories, 141 CPC 1/5 patients in `0_12h` (71 / 70).
- Family A H1–H3 were BH-significant in the predicted CPC 1 > CPC 5
  direction on this bundle. H4 (total diffusion power) differed in the
  opposite direction and is reported as a control, not a primary claim.
- Family B primary `F_reactive` did not follow the predicted CPC 1 >
  CPC 5 direction; both groups occupy mostly `alpha > 0` windows. Left as
  an unresolved estimator/contract question, not a rejected biological
  hypothesis.
- Stored stochastic reachability was mostly `invalid`; cones were
  recomputed from subject-anchored 3D coordinates.
- Unresolved: part2 held-out bundle, sedation confound, independent-drift
  qualification for `E_perp`, Jacobian discrete-vs-continuous time
  semantics, committor/FAR (not testable in this dump).

== 2026-09-11 — first MNPS-v3 ingest audit (beyond Jacobian fidelity)

- Expanded `handover/ingest_jacobian_fidelity_handover.md` after a dump-wide
  check of other v3 teething issues. Jacobian local-fit gate remains
  Priority 1 for Family B.
- Additional ingest-side findings: WFDB clocks with hour $>= 24$ leave 156
  runs `unassigned` (25 CPC 1 vs 131 CPC 5); 17 empty grouped dirs with no
  error record; missing `/provenance/signal_support_provenance`; FTR
  `validation_level=model_derived` only; 9D `e_m` still a non-equivalent
  fallback; `qc_ok_eeg=1` with empty artifact methods; ComBat and
  cohort-anchored coords both off by overlay.
- Not treated as bugs: destination/resilience `not_testable`, diffusion
  alignment without independent drift, grain `direct_between_subject_inference=forbidden`.

== 2026-09-11 — ingest fix confirmed; part1-corrected + part2-confirmatory analysis

- Ingest delivered two new bundles responding to the Jacobian fidelity
  handover: `20260911_125829` (part1-corrected, same 161-subject population
  as `20260904_225047`) and `20260911_123135` (part2-confirmatory, 141
  subjects, zero overlap with part1). Both restricted to filename hours
  000-012, both with the Jacobian fit-fidelity gate (threshold 0.9 on
  `rel_mse_baseline_median`), ComBat (`batch_key=hospital`), and
  cohort-anchored coordinates added.
- Verified in `/jacobian/derived_metrics/v1/provenance` that all four
  Priority-1 ingest requests were implemented exactly as asked
  (`fit_fidelity_gate`, `fit_fidelity_threshold=0.9`, `operator_semantics`,
  `nominal_dt_sec`, `abscissa_units` all now present).
- Ran the unmodified pipeline on both bundles
  (`config/icare_v2_part1_corrected_config.yaml`,
  `config/icare_v2_part2_confirmatory_config.yaml`); added a
  `family_testable` (>=10 per arm) flag to the contrast script.
- *H1 ($d_"eff"^((a))$) and H2 ($tilde(H)_a$) replicate* in the independent,
  non-overlapping part2 cohort (BH-significant, same direction, d=+0.61
  and +0.48). *H3 ($E_perp$) does not replicate* (sign flips, n.s.).
  Reachability cones replicate directionally (individually significant,
  p < 0.001, both cohorts).
- *Family B ($F_"reactive"$, mean alpha) is confirmed not testable* once
  the fidelity gate is honest: only 13/163 and 24/215 patient-timebins
  have any finite alpha. This retroactively confirms the earlier
  `F_reactive` result on `20260904_225047` was a fitting artifact, not a
  biological finding against the hypothesis.
- `conventional_eeg` pack is enabled in the overlay but not materialized
  in either new bundle (needs a features-stage rerun at ingest).
- Manuscript now uses part1-corrected + part2-confirmatory as the primary
  result; the original `20260904_225047` full/smoke results are kept as a
  historical record, not deleted, and are superseded for Family B.

== 2026-09-11 — Jacobian estimator quality follow-up handover

- Diagnosed why the fidelity gate fails 97-99% of windows: sampled
  `/window_start`, `/window_end`, `/time` show only 1-2 finite-difference
  increments per Jacobian window (8 s window, 4 s step), versus the
  diffusion family's pooled `neighborhood: {k: 20}, min_samples: 30`
  (98% computed). The `local_dynamics.jacobian_metrics` overlay has no
  equivalent neighborhood/`min_samples` field.
- Also confirmed `qc/windows/qc_ok_eeg = -1` (not_assessed) and
  `rejected_flag = 0` on 100% of sampled windows in both new bundles: no
  EEG artifact rejection reaches the fit at all.
- Filed `handover/ingest_jacobian_estimator_quality_handover.md` requesting
  (1) a neighborhood/pooling scheme for the Jacobian fit analogous to
  diffusion's, (2) real artifact rejection before feature extraction, and
  (3) a small-sample re-check of the fit-fidelity distribution before a
  full re-ingest. Explicitly not asking to relax the 0.9 threshold itself.

== 2026-09-12 — Tier-2 measurement-quality robustness checks

- Added four article-local robustness analyses without touching any
  pre-registered primary result: (1) percentile bootstrap 95% CIs (2000
  resamples) on Cohen's $d$/Cliff's $delta$ for every contrast row; (2)
  leave-one-subject-out (LOSO) sensitivity for H1-H3 in both cohorts; (3) a
  run-level linear mixed model (subject random intercept, `statsmodels`) on
  pre-collapse per-run medians as a cross-check on the patient-median
  primary test; (4) a post-hoc one-way $eta^2$ diagnostic of hospital on
  the *derived* H1-H4 metrics (not just raw upstream features).
- H1/H2 confirmed stable under LOSO and the mixed model in both cohorts
  (mixed-model discovery $p=5.8 times 10^(-6)$/$5.0 times 10^(-4)$;
  confirmatory $p=2.6 times 10^(-4)$/$2.4 times 10^(-3)$), ruling out the
  patient-median collapse as the source of the signal.
- Found a non-trivial residual hospital $eta^2$ (0.11-0.18) on H1-H3 in
  *both* cohorts after ComBat, including the confirmatory cohort whose
  hospitals are exactly CPC-balanced by design (so there the residual
  effect is site variance orthogonal to outcome, not a demonstrated
  confound, but ComBat clearly does not fully remove site structure from
  the derived nonlinear metrics). New limitation/follow-up: a
  hospital-random-effect sensitivity analysis.
- Built a second, independent drift estimator for $E_perp$ (H3): a
  Savitzky-Golay smoothed derivative of `coords_3d_subject_anchored`
  (window 11 samples $approx$44s) instead of the raw one-step
  `mnps_3d_dot` proxy, recombined with the unmodified stored `a_hat`
  tensor. Result: $E_perp$ moves from "did not replicate" (original
  proxy: discovery $d=+0.10$ $p=0.043$, confirmatory $d=-0.10$ $p=0.134$)
  to a large, LOSO-stable, cross-cohort-replicating CPC1 advantage
  (discovery $d=+0.68$ $p=6.4 times 10^(-6)$; confirmatory $d=+0.47$
  $p=0.0088$), stable across a smoothing-window sweep (7/11/15/21
  samples). Reported as a *promising post-hoc finding requiring
  prospective confirmation*, not a confirmed result, because the
  estimator was chosen after seeing the original result was weak - a
  garden-of-forking-paths risk that a pre-registered test on a third
  cohort would resolve.
- New scripts: `icare_v2_loso_sensitivity.py`,
  `icare_v2_mixed_effects_check.py`, `icare_v2_combat_diagnostic.py`,
  `icare_v2_qualified_drift_extraction.py` (with `--savgol-window` for
  the sensitivity sweep); wired into `icare_v2_run_pipeline.py`. Added
  `statsmodels` as a project dependency.
- Manuscript, S1-S3 updated with a new Results §4.7 / Methods §3.4/§4.7 /
  Discussion subsections and full data tables (S2.6-S2.10, S3.6-S3.7) for
  all four checks.

== 2026-09-13 — spectral abscissa ingest identity + gated CPC comparison

- Rechecked bundles `20260912_094010` (part2) and `20260912_094016` (part1)
  against `20260911_123135` / `20260911_125829`. Overlay YAML and `git_rev`
  unchanged; Jacobian provenance now stamps `knn_k=20`, `min_samples=4`.
- Paired every matching recording (1815 + 1838 stems):
  `computation_status` agrees 100%, `|Delta rel_mse| = 0`, `|Delta alpha_mean|
  = 0` on all `computed` runs (22 + 53). Spectral abscissa is therefore
  identical to the predecessor gated series, not a new measurement.
- Gated CPC contrast (unchanged numbers): discovery patient $alpha$
  $d=+0.79$, $n=7/6$, $p=0.138$ (not testable); confirmatory $d=-1.27$,
  $n=11/11$, $p=0.013$ (borderline $n$, opposite sign). $F_"reactive"$ n.s.
  in both. Reported as diagnostic, not a Family B finding (S2.11).
- New script: `icare_v2_family_b_ingest_comparison.py`; outputs under
  `results/replication/family_b_*`.

== 2026-09-13 — diffusion + drift ingest audit

- Same paired stems as the $alpha$ check. Diffusion `computation_status`,
  $d_"eff"$, $D_"total"$, $|a_"hat"|$, `|mnps_3d_dot|`, and
  `|coords_3d|` are identical (median and max $|Delta| = 0$). H1-H4 do not
  need a recompute on the 2026-09-12 bundles.
- Stored `A_bD` / `drift_diffusion_alignment` is all-NaN (`drift_source =
  not_supplied`); article $E_perp$ is entirely from `a_hat` + `mnps_3d_dot`.
- `/mnps_3d_dot` matches a Savitzky-Golay derivative of subject-anchored
  coords (window 7, poly 3) much better than a raw one-step $Delta x/Delta t$
  (median MAE 0.057 vs 0.11; closer on 99.9% of recordings). Residual vs
  exact `scipy` Savitzky-Golay is consistent with ingest `derivative_robust`.
  Corrects an earlier article-local description of `mnps_3d_dot` as a raw
  one-step finite difference. R7 remains a post-hoc bandwidth/implementation
  check (article Savitzky-Golay 11/2 vs ingest 7/3+robust), not "smoothed vs
  raw."
- New script: `icare_v2_diffusion_drift_ingest_comparison.py`; S2.12.

== 2026-09-14 — Family A identity + CIs in main Results

- Moved the 2026-09-13 diffusion/drift audit into the public article surface:
  Methods robustness item (9), Results R4 ingest-identity paragraph, S2.12
  already present; S2.0/S2.1 captions, S3.6/S3.7, S5 glossary now point at it.
- R2/R3 tables now carry bootstrap 95% CIs on Cohen's $d$ (H1/H2 CIs exclude 0
  in both cohorts; H3 includes 0). H1-H4 were not recomputed on the 2026-09-12
  bundles ($|Delta| = 0$ on 1815+1838 paired files).
- Corrected remaining "one-step finite difference" wording in R7, Discussion,
  Limitations, and S3: `/mnps_3d_dot` is ingest Savitzky-Golay 7/3 + robust;
  R7 is article Savitzky-Golay 11/2 vs that stored derivative.

== 2026-09-15 — Family A AUROC / AUPRC

- Added `icare_v2_auroc_analysis.py` (pattern from
  `comatose_ndt/src/jacobian_exploratory_summary.py`): direct CPC1-high
  AUROC and AUPRC with bootstrap CIs, plus univariate logistic 5x20
  repeated-CV and hospital-LOSO. Not a prognostic model; no clinical/qEEG
  covariates.
- H1/H2 direct AUROC replicates at moderate discrimination (0.74 / 0.67
  and 0.74 / 0.64); stored H3 does not; H4 CPC1-high AUROC is at or below
  chance. Repeated-CV matches rank AUROC; hospital-LOSO is lower (H2
  confirmatory 0.55).
- Manuscript R4 paragraph, S1.9, S2.13, S3.6/S3.7, S5 glossary.

== 2026-09-15 — local-dynamics coverage beyond spectral abscissa

- Scanned every H5 in the 2026-09-11 article bundles
  (`icare_v2_local_dynamics_coverage.py`): diffusion, `/mnps_3d_dot`,
  $A_"bD"$, Jacobian 3D/9D, FTR, stored reachability, transition residuals,
  destination, resilience.
- Diffusion is the only Family A object with honest high coverage (~98%
  `computed`, `a_hat` finite). Chart-velocity is fully populated but is not
  an Itô drift (`A_bD` empty). 3D Jacobian / stored 3D reachability remain
  gated. FTR is `computed` on 96-99% of files including Jac3-gated ones
  (`model_derived`). 9D Jacobian coverage is higher (66% / 18%) but is not
  the article chart. Destination/resilience empty by contract.
- R1 table + S2.14; not a CPC re-test.
