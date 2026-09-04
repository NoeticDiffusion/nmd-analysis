#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "Coma Supplementary Methods",
  subtitle: "Preprocessing boundary, metric definitions, and model ladders",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope

This supplement records the extended methods for the pooled coma geometry article. It focuses on five items that were intentionally compressed in the main paper:

1. the processed bundle contract and preprocessing boundary,
2. the NeuralManifoldDynamics chart contract inherited by the exported `3D` and `9D` coordinates,
3. the selection and validation boundary for the article-facing metric families,
4. compact mathematical definitions for the main reachability and Jacobian summaries,
5. the predictive model ladders and validation design.

The frozen manuscript release corresponding to this methods snapshot is archived on Zenodo.@langell2026_coma_v011

= Processed bundle contract

The article consumes two already harmonized processed roots:

- `part1`: a June 2026 I-CARE 2.1 export with invalidity-fix contract enforced
- `part2`: a second June 2026 I-CARE 2.1 export processed independently under the same contract

Sampled `coords_9d_subject_anchored` rows were checked directly and found to be fully finite in both processed roots, including the `e_m` dimension. The article-facing downstream stack then rebuilds:

- timeline reconstruction,
- primary `mnps_summary` extraction,
- hourly rebinned `mnps_summary`,
- partwise and pooled outcome contrasts,
- reviewer-facing selection audits,
- repeated-CV incremental-validity analysis,
- robustness/QC diagnostics,
- horizon sensitivity,
- early-versus-late window diagnostics,
- and manuscript-facing figures.

The pooled merge was performed only after verifying `0` subject overlap and `0` run overlap between the source bundles.

The main manuscript does *not* fit NeuroComBat inside its own code path. It consumes these locked processed exports as a fixed upstream preprocessing layer and then performs all contrast, prediction, and robustness analyses downstream. The locked export is sufficient to audit overlap, timing, coverage, and downstream stability, but it does not preserve enough information to reconstruct the full upstream NeuroComBat design matrix inside the manuscript itself. All predictive results should therefore be read as internal validation after external harmonization rather than as fold-nested deployment-style harmonization.

= Analysis stack

The article-facing analysis stack uses the scripts under `articles/CLINICAL/comatose_ndt/src/`:

- `icare_patient_timeline_analysis.py`
- `icare_mnps_summary_analysis.py`
- `icare_rebin_mnps_summary.py`
- `merge_coma_cohort_results.py`
- `icare_outcome_contrast_analysis.py`
- `incremental_validity_analysis.py`
- `reviewer_response_checks.py`
- `coma_robustness_checks.py`
- `horizon_sensitivity_summary.py`
- `compare_early_late_distribution.py`
- `make_coma_figures.py`

Pooled result directories follow the naming convention `<analysis_type>_20260606_combined_invalidityfix_<window>` and are documented in `S2` together with the figure manifest.

= Endpoint and timing boundary

The primary endpoint remains later `CPC 1` versus later `CPC 5` on the Cerebral Performance Category (`CPC`) scale, a 5-point ordinal outcome scale ranging from `1` (good cerebral performance) to `5` (death or brain death), with `2` (moderate disability), `3` (severe disability), and `4` (vegetative state/unresponsive wakefulness) as intermediate grades. The primary timing window remains the first `12 h` after EEG-anchor. The patient, not the run, is the primary unit of inference in the manuscript-facing tables.

This design maximizes endpoint contrast but does not isolate a pure neural viability signal. `CPC 5` intersects with death, treatment limitation, and likely withdrawal-of-life-sustaining-therapy pathways, while the manuscript-facing export does not preserve explicit WLST or time-of-death annotations.

The article-facing timing clock is defined by EEG-anchor, not by a direct ROSC-to-recording clock. The export preserves ROSC duration as a clinical covariate, but not a direct elapsed time from ROSC to EEG-anchor. Accordingly, the `0-12 h` primary window and the hourly bins should be read as anchor-relative measurement windows. Intermediate `CPC 2-4` cases are retained for cohort accounting but are not used for the primary inferential contrast, so ordinal generalization remains unproven.

= Selection and validation status

The paper uses different evidence tiers for the geometry families.

== Reachability

The five reachability summaries carried into the main paper and the prediction ladder are:

- `tube_d_eff_median`
- `persistence_log_det_median`
- `persistence_log_eig_var_median`
- `persistence_hysteresis_log_det_median`
- `tube_capture_gate_median`

This family was selected via data-driven cross-fitted reselection prior to examining the pooled outcome contrasts and is treated as the only main-text family with BH-FDR correction applied inside the family. All five metrics cleared BH-FDR correction in the pooled cohort (`q` range `5.70e-07` to `8.04e-03`). The manuscript carries this frozen five-metric layer into the prediction ladder without re-ranking inside the pooled cohort.

== Classical spread and Jacobian anchors

The article also reports `MNPS 3D`, `MNPS 9D`, `MNJ 3D`, and compact `MNJ 9D` summaries in the same article-facing stack. These layers are not all used with the same evidential force.

- `MNPS 3D` and `MNPS 9D` are treated as restored descriptive anchors.
- `MNJ 3D` is treated as a strong classical comparator and pooled anchor.
- Invalidity-corrected `MNJ 9D` is treated as a material but cohort-heterogeneous anchor: retained in the main paper and interpreted with explicit partwise heterogeneity rather than as a single-cohort artifact.

Hourly localization, additional `MNJ 9D` rows, subset robustness, and comparison tables are treated as exploratory or audit material rather than as a second confirmatory family.

= NeuralManifoldDynamics chart basis

The coma manuscript does not define `m`, `d`, and `e` de novo inside the downstream article code. Instead, it consumes H5 exports produced under a fixed `NeuralManifoldDynamics` measurement contract, so the coordinate definitions are inherited from that release rather than re-estimated from the pooled cohort.@langell2026_mndm

The canonical `3D` chart is

$ x_t = [m_t, d_t, e_t] $

and the stratified chart is

$ x_t^((9)) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m] $

where the `m`, `d`, and `e` labels should be read as fixed operational chart labels in the current release contract rather than as uniquely privileged latent biological variables.@langell2026_mndm

Under the active EEG contract used for the I-CARE article, the nine subcoordinates are built from fixed feature families before recomposition to `3D`:

#figure(
  kind: table,
  clean-table(
    columns: (0.9fr, 1.05fr, 2.3fr),
    align: left,
    inset: 4pt,
    table.header([*Family*], [*Subcoordinate*], [*EEG operational mapping in active contract*]),
    [`m`], [`m_a`], [`-0.5 * eeg_delta - 0.5 * eeg_theta`],
    [`m`], [`m_e`], [`-1.0 * eeg_alpha`],
    [`m`], [`m_o`], [`eeg_beta_alpha`],
    [`d`], [`d_n`], [`eeg_gamma`],
    [`d`], [`d_l`], [`eeg_hjorth_mobility`],
    [`d`], [`d_s`], [`eeg_alpha_theta`],
    [`e`], [`e_e`], [`eeg_permutation_entropy`],
    [`e`], [`e_s`], [`eeg_hjorth_complexity`],
    [`e`], [`e_m`], [`embodied_arousal_proxy`],
  ),
  caption: [Fixed EEG-side `9D` chart used by the `NeuralManifoldDynamics` release inherited in this manuscript.@langell2026_mndm]
) <tab-s1-nmdm-9d>

The exported `mnps_3d` trajectory is then derived from a fixed weighted `9D -> 3D` projection:

$ m_t = 0.62 m_a + 0.55 m_e + 0.45 m_o $

$ d_t = 0.50 d_n + 0.82 d_l + 0.28 d_s $

$ e_t = 0.85 e_e + 0.62 e_s + 0.03 e_m $

Operationally, the upstream contract standardizes the contributing feature columns, applies coverage-aware renormalization when some subcoordinate support is missing, and records the resulting `3D` and `9D` trajectories as serialized measurement objects rather than as article-specific fitted axes.@langell2026_mndm The spread, Jacobian, and reachability summaries analyzed in this manuscript therefore inherit a versioned chart definition from `NeuralManifoldDynamics`.

= Conceptual intuition for the three metric families

The main article introduces `MNPS`, `MNJ`, and reachability as three non-interchangeable summaries of the same underlying `NMD` trajectory: `MNPS` is a static spread summary, `MNJ` is a one-step local-deformation summary, and reachability is a multi-step forward-propagated summary of the reachable set built by iterating the local linear model below. The four schematic panels in this section give a plain-language visual anchor for the corresponding mathematical definitions that follow. All panels are schematic illustrations built for methodological intuition only and are not derived from I-CARE data.

#figure(
  image("figures/conceptual_figures/tube_d_eff_median.png", width: 92%),
  caption: [Conceptual visualization of effective reachable dimensionality (`tube_d_eff_median`). Left: low effective dimensionality — short-horizon movement stays confined to a small number of directions (canalized futures). Right: high effective dimensionality — movement can spread into many effectively independent accessible directions.]
) <fig-s1-tube-d-eff>

#figure(
  image("figures/conceptual_figures/persistence_log_eig_var_median.png", width: 92%),
  caption: [Conceptual visualization of persistence (`persistence_log_eig_var_median`, and by the same logic `persistence_log_det_median` and `persistence_hysteresis_log_det_median`). Left: low persistence — the reachable-shape structure changes quickly across neighboring time windows ($t_1, t_2, t_3$), so the local future geometry does not stay consistent. Right: high persistence — the reachable-shape structure stays similar across neighboring windows, so the local future geometry remains consistently organized.]
) <fig-s1-persistence>

#figure(
  image("figures/conceptual_figures/tube_capture_gate_median.png", width: 92%),
  caption: [Conceptual visualization of capture gating (`tube_capture_gate_median`). Left: weak capture gating — nearby futures remain relatively open and are not strongly funneled toward a local sink. Right: strong capture gating — nearby futures are funneled through a narrow gate and become trapped inside a captured local region.]
) <fig-s1-capture-gate>

#figure(
  image("figures/conceptual_figures/Jacobian_frobenius_norm.png", width: 92%),
  caption: [Conceptual visualization of the Jacobian Frobenius norm ($norm(J)_F$, the basis of `frobenius_norm_median` in both `MNJ 3D` and `MNJ 9D`). Left: low $norm(J)_F$ — weak local deformation, so nearby particle trajectories through the local flow field stay close and roughly parallel. Right: high $norm(J)_F$ — strong local deformation, so nearby trajectories are pulled apart, twisted, or redirected over a short distance.]
) <fig-s1-frobenius>

= Reachability metric definitions

Let the local short-horizon model be

$ x_(t + 1) = A_t x_t + b_t + epsilon_t, quad epsilon_t ~ (0, Q_t) $

with propagated covariance

$ Sigma_t^((0)) = sigma_0^2 I, quad Sigma_t^((h + 1)) = A_t Sigma_t^((h)) A_t^top + Q_t $

where $A_t$ is the local linear dynamics operator and $Q_t$ the innovation covariance. The article-facing summaries are formed window-wise and then aggregated at patient level.

== `tube_d_eff_median`

If $lambda_1, dots, lambda_d$ are the eigenvalues of $Sigma_t^((h))$, effective dimensionality is

$ d_("eff"),t^((h)) = frac((sum_i lambda_i)^2, sum_i lambda_i^2) $

Higher values indicate that the reachable cloud spans more effectively independent directions. `tube_d_eff_median` is the patient-level median of the tube summary.

== `persistence_log_eig_var_median`

Log-eigenvalue spread is

$ V_t^((h)) = "var"(log(lambda_i + epsilon)) $

and the persistence transform is applied:

$ P(V_t) = frac(1, "std"(V_(t-w:t+w)) + epsilon) $

Higher values mean more stable retained eigenspectrum structure across nearby windows.

== `persistence_log_det_median`

The log-determinant of the propagated covariance measures the total volume of the reachable tube in log-space:

$ L_t^((h)) = log det(Sigma_t^((h)) + epsilon I) = sum_i log(lambda_i + epsilon) $

The persistence transform is then applied:

$ P(L_t) = frac(1, "std"(L_(t-w:t+w)) + epsilon) $

Higher values indicate a more stable tube-volume signature across neighboring windows. In the pooled cohort, `CPC 1` patients show higher `persistence_log_det_median`, consistent with broader and more temporally stable reachable tube volume.

== `persistence_hysteresis_log_det_median`

The hysteresis form tracks the signed lag-one autocorrelation of the log-det series:

$ H_t = L_(t)^((h)) - L_(t-1)^((h)) $

The persistence hysteresis metric is

$ P_H(L_t) = frac(1, "std"(H_(t-w:t+w)) + epsilon) $

Higher values indicate a more stable signed trajectory of log-det changes (lower hysteresis). In the pooled cohort, `CPC 1` patients show *lower* `persistence_hysteresis_log_det_median` (Cohen's `d = -0.909`), indicating that better-outcome patients have more variable tube-volume trajectory rather than a locked high or low mode.

== `tube_capture_gate_median`

The innovation-versus-transport balance at horizon `h` is

$ q_t^((h)) = frac("tr"(Sigma_t^((h)) - A_t Sigma_t^((h - 1)) A_t^top), "tr"(Sigma_t^((h)))) $

The article-facing gate uses `h = 4`:

$ G_t = (1 - q_t^((4))) log(1 + norm(A_t)_2) $

Higher values indicate a stronger combination of transport-dominated evolution and locally strong linear dynamics. The `H = 1..4` sensitivity grid is reported in `S3`.

= Jacobian and spread definitions

== `MNPS` spread summaries

The restored `MNPS 3D` and `MNPS 9D` rows in the merged manuscript are simple dispersion summaries of exported coordinates. For example, `m_std` in `MNPS 3D` is the standard deviation of the `m` coordinate across valid windows, while `m_e_std` in `MNPS 9D` is the standard deviation of the `m_e` coordinate. These rows are treated as descriptive anchors rather than as mechanistic claims.

== Local Jacobian summaries

For each analyzable local window, let $J_t$ denote the estimated local Jacobian and let $lambda_(i,t)$ be its eigenvalues.

=== `spectral_radius_median`

$ rho_t = max_i |lambda_(i,t)| $

and the article-facing summary is the patient-level median of $rho_t$.

=== `anisotropy_abs_eig_median`

The anisotropy summary is the variance of the absolute eigenvalue magnitudes:

$ A_t = "var"_i(|lambda_(i,t)|) $

Higher values mean more uneven distribution of local Jacobian gain across directions.

=== `frobenius_norm_median`

$ F_t = norm(J_t)_F = sqrt("tr"(J_t^top J_t)) $

This functions as a compact summary of total local linear deformation strength.

=== `mdr_median`

When the time derivative of the Jacobian is available, let

$ D_t = frac(norm(dot(J)_t)_F, norm(J_t)_F + epsilon) $

The exported `mdr_median` is the patient-level median of $D_t$ and behaves like a normalized Jacobian-change ratio.

= Predictive model ladders

The prediction ladder compares four manuscript-facing model objects:

1. `clinical_only` — reported in the manuscript text and tables as `limited_clinical_only`
2. `eeg_only` — reported as `restricted qEEG`
3. `clinical_plus_eeg` — reported as `limited_clinical + qEEG`
4. `clinical_plus_eeg_plus_geometry` — reported as `limited_clinical + qEEG + geometry`

Clinical covariates include age, sex, ROSC time, shockable rhythm, OHCA/IHCA, targeted temperature management, hospital, channel count, and channel coverage. The qEEG block uses the exported EEG summary features. The geometry block is the fixed five-feature reachability layer listed above.

In the manuscript text, these are described as a `limited_clinical_only` block, a `restricted qEEG` block, a `limited_clinical + qEEG` baseline, and a `limited_clinical + qEEG + geometry` model. The `limited_clinical_only` label is used deliberately instead of a plain `clinical` label: the block is capped at the `14` variables preserved in the locked export and omits variables that are standard in contemporary multimodal neuroprognostication (SSEP, quantitative pupillometry, motor score, neuron-specific enolase, structural neuroimaging). Published multimodal clinical models that include those variables typically report substantially higher discrimination than the `limited_clinical_only` baseline reported here. All four model tiers share the same locked-export feature ceiling, so the incremental AUROC comparisons are internally consistent, but none of them should be read as a comparison against full contemporary clinical practice.

The classifier pipeline is:

- median imputation,
- z-scoring,
- balanced logistic regression (`liblinear`, `max_iter = 1000`).

Validation uses:

- `RepeatedStratifiedKFold(n_splits = 5, n_repeats = 20, random_state = 20260517)`
- `LeaveOneGroupOut()` with hospital as held-out site

No additional univariate screening or fold-wise feature selection is performed inside the CV loop.

= QC and sensitivity boundary

The manuscript-facing QC package is intentionally limited to what the processed export preserves:

- shockable / non-shockable subset contrasts,
- QC-only proxy prediction using `n_windows_total`, channel count, and channel coverage,
- geometry-versus-QC correlations,
- patient-label permutation,
- horizon sensitivity for the reachability family,
- early-versus-late distribution summaries,
- and subject-wise circular-shift nulls for hourly peak localization.

Direct artifact burden remains unavailable for quantitative use because the detector is off in the relevant export layer. The current time-order control is limited to subject-wise circular shifts of already-derived hourly summaries; a stricter upstream re-estimation from reordered trajectories was not run.

= References

#bibliography("cardiac_arrest_comatose_references.bib")
