// S1 Supplementary Methods — coma_ndt_v.1.0 (I-CARE 2.1 CPC1 vs CPC5)

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "S1 Methods - coma_ndt_v1.0",
  subtitle: "Measurement contract, primary metric computation, the Jacobian fit-fidelity gate, and the statistical design",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S1.0 Dataset and measurement contract

PhysioNet I-CARE 2.1 (International Cardiac Arrest REsearch consortium; DOI
10.13026/m33r-bj81), continuous scalp EEG from comatose adults after cardiac arrest, with CPC
(Cerebral Performance Category, 1-5) outcome. Two NeuralManifoldDynamics (MNDM v3.0.0,
`mnps_tensor_spec_v2_4`, git revision `eb0ff86bec842682c60f631a986cbaffc93e27d5`) bundles are
used, both restricted at ingest to filename hours 000-012:

- Discovery: `neuralmanifolddynamics_physionet_icare_2_1_20260911_125829` (161 subjects, 1815
  recordings). Ingest overlay: `config_ingest_physionet_i-care_2_1_part1_0_12h_dynamical_families.yaml`,
  importing the (fixed) base `config_ingest_physionet_i-care_2_1_dynamical_families.yaml`.
- Confirmatory: `neuralmanifolddynamics_physionet_icare_2_1_20260911_123135` (140 subjects,
  1838 recordings; pre-selected to CPC1/CPC5 only). Ingest overlay:
  `config_ingest_physionet_i-care_2_1_next_140_0_12h_dynamical_families.yaml`.

Subject-ID intersection between the two bundles is empty (verified directly from the raw
directory listings before any analysis).

All analyses should be read against the NMDM measurement contract rather than as direct
computations on raw voltage traces: per-window MNPS-3D/9D coordinates, per-window diffusion and
Jacobian derived metrics, and their `computation_status` / `grain` / `measurement_validity`
fields are all produced upstream by the ingest pipeline and consumed as-is here, with the two
exceptions noted in S1.2 (reachability cones, recomputed article-side).

= S1.1 Epoch structure and feature export

Each recording is windowed into 8 s epochs with a 4 s step (`nominal_dt_sec = 4.0`, confirmed
from `/jacobian/derived_metrics/v1/provenance`). Thirteen raw per-epoch EEG features are
exported (`eeg_delta`, `eeg_theta`, `eeg_alpha`, `eeg_beta`, `eeg_gamma`,
`eeg_highfreq_power_30_45`, `eeg_alpha_theta`, `eeg_beta_alpha`, `eeg_hjorth_mobility`,
`eeg_hjorth_complexity`, `eeg_permutation_entropy`, `eeg_sample_entropy`,
`embodied_arousal_proxy`), ComBat-harmonized post-feature (`batch_key=hospital`), then projected
to MNPS-3D (`mnps_3d`) and MNPS-9D (`coords_9d`) coordinates under both a subject-anchored and a
cohort-anchored contract. Per-window outputs consumed here: `dynamical_families/diffusion/v1`
(`a_hat`, `d_diff`, `D_total`, `drift_diffusion_alignment`, validity flag), `mnps_3d_dot`
(configured MNPS chart derivative; see S1.2), `jacobian/derived_metrics/v1` (per-window `spectral_abscissa`,
`numerical_abscissa`, `reactivity_gap`, plus run-level `computation_status` /
`failure_reason` / fit-fidelity provenance), `coords_3d_subject_anchored`, and
`extensions/time_reference`.

The `conventional_eeg` comparator pack (`tier1`, `complexity`, `coma`) is enabled in both
overlays but is not materialized in either export (no `eeg_conventional_*` columns, no
`/extensions/conventional_eeg` group); per the overlay's own comment this requires a
features-stage ingest rerun in addition to `summarize`, which was not done for these two
bundles. No qEEG-comparator analysis is therefore possible on this data version.

= S1.2 Primary metric definitions

From the local diffusion tensor $a(x,t)$ (eigenvalues $lambda_1,...,lambda_3 >= 0$):

$ d_"eff"^((a)) = frac((sum_i lambda_i)^2, sum_i lambda_i^2), quad
  tilde(H)_a = frac(-sum_i p_i log p_i, log 3), quad p_i = frac(lambda_i, sum_j lambda_j + epsilon), quad
  "Tr"(a) = sum_i lambda_i, quad epsilon = 10^(-12). $ <eq:s1-fama>

*Implemented*: read per-window `a_hat` (subject-anchored MNPS-3D), eigendecompose
(`numpy.linalg.eigvalsh`), clip eigenvalues to $>= 0$, apply @eq:s1-fama, aggregate to per-run
medians then per-patient/time-bin medians. Recomputed $d_"eff"^((a))$ matches the ingest-stored
`d_diff` (same formula, computed upstream) to a median absolute difference of
$4.1 times 10^(-8)$ (discovery) / $3.6 times 10^(-8)$ (confirmatory) - this is a
reimplementation cross-check, not an independent estimator.

Candidate drift-orthogonal fraction, using the stored MNPS chart-velocity
$hat(b) = "mnps\_3d\_dot" / norm("mnps\_3d\_dot")$:

$ E_perp = frac("Tr"(a) - hat(b)^top a hat(b), "Tr"(a) + epsilon). $ <eq:s1-eperp>

*Not established*: `mnps_3d_dot` is the MNPS chart derivative (`derivative.method = sav_gol`,
window 7, polyorder 3, plus `derivative_robust`), not an independently qualified Itô drift
(`translation_qualification.qualified = false`; diffusion provenance
`drift_source = not_supplied`). Stored `A_bD` / `drift_diffusion_alignment` is all-NaN on
sampled files, so $E_perp$ is computed article-side from `a_hat` + `mnps_3d_dot`. H3 remains
a candidate metric.

Local generator (Family B), from `/jacobian/derived_metrics/v1/series`:

$ alpha = max "Re" thin lambda(J), quad omega = lambda_max ((J+J^top)/2), quad
  F_"reactive" = P(alpha<0<omega), quad F_"contract" = P(omega<0), quad F_"unstable" = P(alpha>0). $

*Implemented, gated*: $J$ is a continuous-time-generator local-linear fit
(`operator_semantics = continuous_time_generator`); the fit is only accepted when
`rel_mse_baseline_median < 0.9` (S1.3). Where not accepted, the entire per-window series is
NaN, not partially populated.

= S1.3 The Jacobian fit-fidelity gate

An earlier predecessor bundle (`20260904_225047`) computed Family B metrics on effectively all
windows regardless of local-linear-fit quality, with `rel_mse_baseline_median` typically
$approx 0.96$-$0.98$ (fit not better than a trivial baseline). This was flagged in
`handover/ingest_jacobian_fidelity_handover.md` as an ingest-contract gap. Both bundles used in
this article carry the fix, verified directly in `/jacobian/derived_metrics/v1/provenance`:

#figure(
  clean-table(
    columns: (1.8fr, 1.6fr),
    table.header([*Provenance field*], [*Value*]),
    [`fit_fidelity_gate`], [`rel_mse_baseline_median`],
    [`fit_fidelity_gate_version`], [`provisional_icare_20260911`],
    [`fit_fidelity_threshold`], [`0.9`],
    [`operator_semantics`], [`continuous_time_generator`],
    [`nominal_dt_sec`], [`4.0`],
    [`abscissa_units`], [`1/second`],
  ),
  caption: [Jacobian fit-fidelity gate provenance, verified on sampled files from both bundles.]
) <tab-s1-gate>

Windows failing the gate get `computation_status = insufficient_support`,
`failure_reason = local_linear_fit_not_better_than_baseline` (the dominant reason in
$>= 97%$ of gated windows in both cohorts), `summary/fit_identified = "False"`. Stochastic
reachability inherits the gate (`computation_status = unavailable` on $>97%$ of windows, rather
than the pre-gate `invalid` from `expm` overflow); this is why reachability cones are
recomputed article-side (S1.4) rather than read from the stored family.

= S1.4 Reachability cones (article-local recomputation)

Recomputed from `coords_3d_subject_anchored` using `nmd_analysis.reachability_core`: kNN
$k=25$, ridge regression ($alpha_"ridge" = 10^(-3)$), super-window size 3, horizons
$h in {1,2,4}$ steps, jitter $10^(-6)$, `persistence_mode = "stability"`. Outputs
`cone_d_eff_h1`, `cone_d_eff_h2`, `cone_d_eff_h4` (effective dimensionality of the reachable-set
covariance at each horizon) and `tube_d_eff` (persistence-smoothed summary across the run). This
does not depend on the Jacobian fit or its gate.

= S1.5 Statistical design

Unit of analysis: one row per patient in the primary 0-12h EEG-anchor window (patient-level
median across runs and windows). Primary test: two-sided Mann-Whitney U, CPC1 vs CPC5. Secondary:
Welch's $t$-test. Effect sizes: Cohen's $d$ (pooled SD) and Cliff's $delta$. Multiple-comparison
correction: Benjamini-Hochberg FDR at $alpha = 0.05$, applied *within* the diffusion H1-H3 family
only (H4, reachability, and Family B are reported individually/descriptively, per the
pre-registration in `handover/hypothesis.md`). A `family_testable` flag (`"False"` when either
arm has $< 10$ evaluable patients) is computed for every contrast row to prevent an
underpowered small-$n$ result from being read as either a positive or a null finding; this
applies almost exclusively to Family B contrasts (S1.3).

= S1.6 Robustness and confound audit protocol

1. *Independent-cohort replication* (primary design, not a follow-up check): identical,
  unmodified pipeline on two non-overlapping subject sets.
2. *TTM subgroup sensitivity*: separate H1-H3 contrasts within the 33 degrees C and 36 degrees C
  targeted-temperature-management strata.
3. *Recomputed-vs-stored cross-check*: article-local $d_"eff"^((a))$ vs ingest-stored `d_diff`.
4. *ComBat validation probes* (ingest-computed): batch(hospital) and target(CPC) $eta^2$,
  pre- vs post-harmonization, on raw features.
5. *`family_testable` gating*: minimum 10 patients per arm before a contrast is interpreted.
6. *Bootstrap CIs*: percentile bootstrap (2000 resamples, arms resampled independently, fixed
  seed `20260912`) 95% CI on Cohen's $d$ and Cliff's $delta$ for every contrast row.
7. *Leave-one-subject-out (LOSO)*: for H1-H3, drop each single patient in turn and recompute the
  patient-level Mann-Whitney $p$ and Cohen's $d$; report whether nominal ($alpha=0.05$)
  significance and effect-size sign survive every single-patient removal
  (`icare_v2_loso_sensitivity.py`). This is a robustness check on nominal significance, not a
  replacement for the BH-corrected primary test.
8. *Run-level mixed-effects cross-check*: `value ~ C(contrast_group)` with a subject random
  intercept (`statsmodels.formula.api.mixedlm`, REML, `lbfgs`), fit on the pre-collapse per-run
  medians in the primary window (not further collapsed to one value per patient), for H1-H3
  (`icare_v2_mixed_effects_check.py`).
9. *Post-hoc residual batch-effect diagnostic*: one-way $eta^2$ of hospital on the *derived*
  H1-H4 metrics (not just the raw upstream features), flagged against a 0.06 medium-effect
  convention (`icare_v2_combat_diagnostic.py`).
10. *Family A ingest-identity audit*: paired recording-level comparison of diffusion tensors and
  `/mnps_3d_dot` on the 2026-09-12 summarize re-runs versus the 2026-09-11 predecessors used for
  all primary contrasts (`icare_v2_diffusion_drift_ingest_comparison.py`; S2.12). Not a re-test
  of H1-H4.
11. *Rank discrimination (AUROC / AUPRC)*: direct CPC1-high AUROC and average precision on the
  same patient-medians, with independent-arm bootstrap 95% CIs, plus univariate logistic
  repeated stratified CV (5x20) and hospital `LeaveOneGroupOut` (`icare_v2_auroc_analysis.py`;
  S2.13). Not a prognostic model; no clinical or conventional-qEEG covariates.
12. *Local-dynamics coverage audit*: run- and window-level scan of diffusion, chart-velocity,
  $A_"bD"$, Jacobian 3D/9D, FTR, stored reachability, transition residuals, destination, and
  resilience on every H5 in both article bundles (`icare_v2_local_dynamics_coverage.py`; S2.14).
  Not a CPC re-test.

= S1.7 Qualified-drift estimator for $E_perp$ (post-hoc robustness check)

The stored drift proxy `mnps_3d_dot` used for the primary $E_perp$ result (S1.2) is the
ingest MNPS chart derivative (`sav_gol` window 7, polyorder 3), still unqualified as an Itô
drift (`drift_source = not_supplied`). A 2026-09-13 paired audit (S2.12) shows it is much
closer to a matching Savitzky-Golay derivative of `coords_3d_subject_anchored` than to a
raw one-step $Delta x / Delta t$ (median MAE 0.057 vs 0.11; closer to Savitzky-Golay on
99.9% of recordings), with a residual that is consistent with ingest's extra
`derivative_robust` jump filter. The article-local robustness check below is therefore a
*different Savitzky-Golay implementation and bandwidth* (window 11, polyorder 2, no ingest
robust filter), not a contrast of "raw one-step vs smoothed." Procedure:

1. Read `coords_3d_subject_anchored/values` (the same coordinate series `mnps_3d_dot` is derived
  from) and `/time` for each recording.
2. Compute a Savitzky-Golay smoothed first derivative (`scipy.signal.savgol_filter`,
  `deriv=1`, `delta=dt`, window length 11 samples $approx$ 44 s at the observed 4 s cadence,
  2nd-order polynomial, `mode="interp"`), per coordinate axis. Windows with fewer than 5 usable
  samples are skipped (`e_perp_qualified_median = NaN`).
3. Recombine this smoothed drift with the *unmodified*, ingest-stored `a_hat` tensor via
  @eq:s1-eperp to get a per-window, per-run, per-patient `e_perp_qualified_median`, aggregated
  identically to the primary pipeline (median across windows, then across runs).
4. A sensitivity sweep over the Savitzky-Golay window length (7, 11, 15, 21 samples) checks that
  the result is not an artifact of the specific smoothing bandwidth chosen.
5. LOSO (S1.6.7) is additionally run on the qualified-drift metric.

This estimator choice is *post-hoc*: it was made after observing that H3 was weak/non-replicating
with the original proxy, so a positive result here is reported as a promising robustness finding
requiring prospective confirmation (main text §4.7), not as a second pre-registered test of H3.
It does not modify `mnps_3d_dot`, `a_hat`, or any ingest-side artifact; it is purely an
article-local re-derivation from already-exported coordinates and tensors.

= S1.8 Secondary analysis

Family B (local generator: $alpha$, $omega$, $F_"reactive"$, $F_"contract"$, $F_"unstable"$) is
pre-specified in `handover/hypothesis.md` but its testability is treated as an empirical
question, not an assumption, given S1.3. CPC5 "majority-regime" subtyping
(`f_contract`/`f_unstable`/`f_reactive`, whichever is numerically largest per patient) is
reported descriptively only; under the fidelity gate the large majority of CPC5 patients are
`unassigned` (no finite Family B value at all) in both cohorts, so this subtyping is not
currently informative.

= S1.9 Rank discrimination (AUROC / AUPRC)

Direct AUROC is computed on the same patient-median table as the primary Mann-Whitney
contrasts, with CPC1 as the positive class and the metric used as the score (higher =
more CPC1-like). It equals $U/(n_1 n_5)$ and $(delta + 1)/2$ for Cliff's $delta$. AUPRC is
sklearn `average_precision_score` on the same labels and scores; chance AUPRC is CPC1
prevalence ($approx 0.50$ here). Bootstrap CIs resample the two arms independently (2000
draws, seed `20260912`), matching the Cohen's $d$ CIs. Univariate logistic repeated-CV
and hospital-LOSO follow the older coma article's Jacobian exploratory summary
(`jacobian_exploratory_summary.py`): `StandardScaler` + balanced `LogisticRegression`,
5x20 `RepeatedStratifiedKFold`, and `LeaveOneGroupOut` by hospital. These checks ask
whether a monotone transform of the same scalar discriminates out of sample; they are
not a multivariate prognostic model.

#bibliography("references.bib", style: "apa")
