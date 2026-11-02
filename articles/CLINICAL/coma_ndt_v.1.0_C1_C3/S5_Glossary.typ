// S5 Glossary — coma_ndt_v.1.0 (I-CARE 2.1 CPC1 vs CPC5)

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S5 - Glossary",
  short-title: "Glossary - coma_ndt_v1.0",
  subtitle: "Terminology used in the I-CARE 2.1 CPC1 vs CPC5 analysis",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("glossary", "NDT", "MNDM", "MNPS", "I-CARE", "coma"),
  article-type: "Supplementary Material",
  abstract: [
    Terminology used across `coma_ndt_v.1.0`. Reflects MNDM v3.0.0 / `mnps_tensor_spec_v2_4` as
    ingested 2026-09-11. Entries distinguish (1) *Implemented* - the exact pipeline computation;
    (2) *Interpretation* - the most defensible empirical reading; (3) *Speculative / Not
    established* - theoretical mappings not yet directly confirmed.
  ],
)

#set heading(numbering: none)

= A - D

*CPC (Cerebral Performance Category)* - Clinical outcome scale, 1 (good recovery) to 5
(death/vegetative). This article contrasts CPC1 vs CPC5 only.

*ComBat* - Empirical-Bayes batch-effect harmonization applied post-feature-extraction,
`batch_key = hospital`, with age and sex as covariates. *Implemented*: reduces
batch-associated feature variance ($eta^2$) while validation probes show CPC-associated
variance preserved or increased (S3.2).

*Diffusion tensor $a(x,t)$* - Local stochastic-accessibility tensor, $a = Sigma Sigma^top$
where $Sigma$ is the diffusion coefficient of the local Itô decomposition
$d X_t = b(X_t,t) d t + Sigma(X_t,t) d W_t$. *Implemented*: estimated per window as
`local_increment_covariance` on subject-anchored MNPS-3D coordinates.

*$d_"eff"^((a))$ (H1)* - Participation-ratio effective dimensionality of the diffusion tensor's
eigenvalue spectrum: $(sum lambda_i)^2 / sum lambda_i^2$. *Interpretation*: how many local
directions of stochastic accessibility are effectively in play (1 = all diffusion on one axis,
3 = isotropic). *Result*: higher in CPC1, replicated across two independent cohorts (main text
R2-R3).

*Fit-fidelity gate* - Ingest-side quality gate on the local Jacobian linear fit
(`rel_mse_baseline_median < 0.9`); windows failing it get `computation_status =
insufficient_support`. *Implemented* 2026-09-11 in response to
`handover/ingest_jacobian_fidelity_handover.md`; verified active on both bundles (S1.3).

= E - L

*$E_perp$ (H3, candidate)* - Fraction of total diffusion power orthogonal to the local drift
direction, $(op("Tr")(a) - hat(b)^top a hat(b)) / op("Tr")(a)$. *Not established*: the stored
chart-velocity `mnps_3d_dot` is an ingest Savitzky-Golay derivative (window 7, polyorder 3, plus
`derivative_robust`), not an independently qualified Itô drift (`drift_source = not_supplied`);
stored $A_"bD"$ is empty, so the metric is computed article-side from $a_"hat"$ plus
`mnps_3d_dot`. *Result*: did not replicate with `/mnps_3d_dot` (sign reversed). A post-hoc
article-local Savitzky-Golay 11/2 estimator replicated in both cohorts (S2.10) and is labeled
promising, not confirmed.

*Family A* - The diffusion-geometry hypothesis family: H1 ($d_"eff"^((a))$), H2
($tilde(H)_a$), H3 ($E_perp$, candidate), H4 ($op("Tr")(a)$, control, not required to differ).
Primary H1/H2/H4 numbers are from the 2026-09-11 bundles; a paired 2026-09-12 audit found
bit-identical tensors (S2.12).

*Family B* - The local-generator hypothesis family: $alpha$ (spectral abscissa), $omega$
(numerical abscissa), $F_"reactive" = P(alpha<0<omega)$, $F_"contract" = P(omega<0)$,
$F_"unstable" = P(alpha>0)$. *Not currently testable* on this dataset/window/estimator once the
fit-fidelity gate is applied (S1.3, S2.3).

*Grain* - Contract field describing the native unit of a measurement (`window`) and its
biological aggregation unit (`subject`), with
`direct_between_subject_inference = "forbidden"` at the raw-window level; all contrasts in this
article aggregate to per-patient, per-time-bin medians before any between-subject test.

= M - R

*MNDM (NeuralManifoldDynamics)* - The ingest pipeline producing HDF5 tensor-contract exports
from raw physiological recordings; version 3.0.0 used here.

*MNPS (Mnps tensor spec)* - The tensor-contract schema for exported coordinates and derived
metrics; `mnps_tensor_spec_v2_4` used here. 3D (`mnps_3d`) and 9D (`coords_9d`) charts both
present; only 3D is used for any hypothesis test in this article.

*Reachability cone* - A local kNN-based estimate of the reachable-set covariance at horizon $h$
steps, summarized by an effective-dimensionality functional (`cone_d_eff_h`) and, across a run,
a persistence-smoothed `tube_d_eff`. *Implemented* article-side (`nmd_analysis.reachability_core`),
independent of the Jacobian fit and its gate.

*Subject-anchored / cohort-anchored coordinate contract* - Two parallel coordinate charts:
subject-anchored (per-patient reference, used for all Family A and reachability metrics here)
and cohort-anchored (population-level reference, added at ingest 2026-09-11, not used for any
primary hypothesis test in this article to avoid conflating within-subject dynamics with
between-subject scale).

= S - Z

*AUROC (direct, CPC1-high)* - Area under the ROC curve treating the patient-median metric as
a score and CPC1 as the positive class. Equals the Mann-Whitney rank probability
$U/(n_1 n_5)$ and $(delta + 1)/2$ for Cliff's $delta$. *Not* a fitted prognostic model.
Reported with independent-arm bootstrap 95% CIs (S2.13).

*AUPRC* - Average precision (area under the precision-recall curve) with CPC1 as the
positive class. Chance equals CPC1 prevalence ($approx 0.50$ in these balanced contrasts).

*BH-FDR (Benjamini-Hochberg false discovery rate)* - Multiple-comparison correction applied
within the H1-H3 diffusion family only, $q < 0.05$ threshold.

*`family_testable`* - Article-local flag: `"False"` when either CPC arm has fewer than 10
evaluable patients for a given metric, to prevent an underpowered small-$n$ contrast from being
read as a positive or null finding. Introduced 2026-09-11 specifically because the fit-fidelity
gate collapses Family B to near-zero testable $n$ (S1.5, S2.3).

*TTM (targeted temperature management)* - 33 degrees C vs 36 degrees C post-arrest cooling
protocol; used here only as a subgroup-sensitivity stratum (S2.4), not a primary contrast.

#bibliography("references.bib", style: "apa")
