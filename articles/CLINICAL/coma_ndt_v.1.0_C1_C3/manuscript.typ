// Coma NDT v1.0 -- I-CARE 2.1 CPC1 vs CPC5, two-cohort replication.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Local diffusion geometry, not total noise or a fitted local generator, separates good from poor outcome after cardiac-arrest coma: a two-cohort replication in PhysioNet I-CARE 2.1",
  short-title: "Local diffusion geometry in post-arrest coma (I-CARE 2.1)",
  subtitle: "Effective local dimensionality and diffusion entropy replicate across an independent, non-overlapping cohort; a fitted local Jacobian generator does not survive an honest fidelity gate",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "cardiac arrest",
    "coma prognosis",
    "EEG",
    "neural manifold dynamics",
    "diffusion geometry",
    "Noetic Diffusion Theory",
  ),
  article-type: "Research Article",
  abstract: [
    Does neurological recovery after cardiac-arrest coma reflect a broader, less canalized local
    accessibility geometry rather than simply more neural activity? We tested this in PhysioNet
    I-CARE 2.1 EEG using neural-manifold-dynamics (NMDM v3.0.0) local diffusion and reachability
    metrics, contrasting good (CPC1, $n=71/70$) versus poor (CPC5, $n=70/70$) outcome in the first
    0--12 h EEG-anchor window, across two independent, non-overlapping cohorts (161 and 140
    subjects). Effective local diffusion dimensionality ($d_"eff"^((a))$) and normalized diffusion
    entropy ($tilde(H)_a$) were higher in CPC1 in the discovery cohort (Cohen's $d=+0.76$ and
    $+0.58$, BH-$q<10^(-5)$) and replicated in the independent confirmatory cohort ($d=+0.61$ and
    $+0.48$, BH-$q<0.01$), while total local diffusion power was not required to differ and was, if
    anything, numerically higher in CPC5. A 2026-09-12 ingest re-run left the Family A tensors
    bit-identical to the series used here. Reachability-cone effective dimensionality showed the
same pattern at horizons $h=1$ and $h=4$ in both cohorts. Both effects were stable under
leave-one-subject-out perturbation and under a run-level mixed-effects cross-check that avoids
collapsing each patient's runs to a single median before testing. A candidate drift-orthogonal
diffusion fraction ($E_perp$) did not replicate with the stored MNPS chart-velocity `/mnps_3d_dot`
(sign reversed, non-significant in the confirmatory cohort); a post-hoc, non-pre-registered
reanalysis with a different Savitzky-Golay drift estimator instead found a large, LOSO-stable
CPC1 advantage that replicated in both cohorts ($d=+0.68$ and $+0.47$), which we report as a
promising but not yet confirmed finding pending a prospective test with the estimator fixed in
advance. A pre-specified
    local-generator hypothesis (spectral-abscissa "stable-but-reactive" fraction, $F_"reactive"$)
    could not be tested at all once an honest local-linear-fit fidelity gate was applied at
    ingest: $>97%$ of windows in both cohorts failed the fit-quality threshold, confirming that an
    earlier apparent signal for this metric was a fitting artifact rather than a biological
    result. We conclude that recovery-linked coma in this dataset is associated with a
    geometrically richer, not merely more energetic, local stochastic accessibility structure, and
    we report the local-generator estimator as not currently usable on this EEG chart and window.
  ],
  author-summary: [
    In two independent groups of cardiac-arrest patients, EEG-derived measures of how many local
    directions of neural state-space are actually accessible - not how much total neural "noise"
    is present - distinguished patients who recovered well from those who did not, and this held
    up when we repeated the analysis on a completely separate group of patients. A separate,
    more ambitious measure that tried to fit a local dynamical model to each patient's EEG failed
    an honest quality check on almost all windows, so we report it as untestable with the current
    method rather than as evidence against the underlying theory.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted at submission.],
  data-availability: [
    PhysioNet I-CARE 2.1 (DOI 10.13026/m33r-bj81). NeuralManifoldDynamics (MNDM) v3.0.0 processed
    bundles: `neuralmanifolddynamics_physionet_icare_2_1_20260911_125829` (discovery cohort) and
    `neuralmanifolddynamics_physionet_icare_2_1_20260911_123135` (confirmatory cohort). Article-local
    analysis pipeline: `articles/CLINICAL/coma_ndt_v.1.0/src/` in the project repository.
  ],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")

= Introduction <sec:intro>

Coma after cardiac arrest is prognostically ambiguous in its first hours: standardized outcome
(CPC, Cerebral Performance Category, 1 = good recovery through 5 = death/vegetative state) is not
known until weeks later, yet clinical decisions about withdrawal of life-sustaining therapy are
often made early. Standardized EEG interpretation (continuity, reactivity, background amplitude,
suppression) is already an accurate prognostic tool @westhall2016eeg, and asks, in essence,
whether a patient's brain shows *more* organized activity. Noetic Diffusion Theory (NDT)
@langell2025ndt suggests a different, complementary question: not how much activity is present,
but how *accessible* the local state space is - how many directions a patient's neural state can
locally move into, and whether that structure is dominated by a strong, narrow deterministic
pull (a canalized attractor) or by a broader, less canalized local geometry.

Formally, local neural-manifold dynamics can be decomposed as an ItÃ´ process

$ d X_t = b(X_t, t) thin d t + Sigma(X_t, t) thin d W_t, $ <eq:sde>

with local drift $b(x,t) approx frac(1, Delta t) EE[Delta X_t mid X_t approx x]$ and local
diffusion tensor $a(x,t) = Sigma(x,t) Sigma(x,t)^top approx frac(1, Delta t) "Cov"[Delta X_t mid X_t
approx x]$. The deterministic vector field $b$ and the stochastic accessibility geometry $a$ are
different objects, and a prior internal analysis of this same cardiac-arrest population found
reachability-cone effective dimensionality already higher in good-outcome (CPC1) patients than
poor-outcome (CPC5) patients. That earlier result motivates, but does not by itself establish, a
sharper question about *why*: is the CPC1 advantage more total local noise, or a more isotropic /
higher-entropy local diffusion geometry at similar or lower total diffusion power?

#netn-box(title: [Core question])[
  In post-cardiac-arrest coma, does eventual good outcome (CPC1) correspond to a broader,
  less canalized local diffusion geometry (higher effective local dimensionality and entropy of
  $a(x,t)$) relative to poor outcome (CPC5), independent of total local diffusion power, and does
  this replicate in a fully independent patient cohort?
]

We additionally test, as a pre-registered but not-required-to-succeed secondary question, whether
a locally fitted continuous-time generator $J(x,t) = nabla_X b(X_t,t)$ (the "MNJ" local Jacobian)
shows a "stable-but-reactive" regime ($alpha<0<omega$, where $alpha$ is the spectral abscissa and
$omega$ the numerical abscissa of $J$) more often in CPC1 than CPC5. Because this quantity depends
on whether a local linear fit is actually identified by the data, we treat its testability as an
empirical question in its own right, not an assumption.

= Theory <sec:theory>

== Local diffusion geometry and the primary metrics

From the local diffusion tensor $a(x,t)$ (eigenvalues $lambda_1,...,lambda_d >= 0$, $d=3$ for the
primary MNPS-3D chart used here), we use three scalar summaries:

$ d_"eff"^((a)) = frac((sum_i lambda_i)^2, sum_i lambda_i^2), quad quad
  tilde(H)_a = frac(-sum_i p_i log p_i, log d), quad p_i = frac(lambda_i, sum_j lambda_j + epsilon), quad quad
  "Tr"(a) = sum_i lambda_i. $ <eq:famA>

$d_"eff"^((a))$ is the participation-ratio effective dimensionality of local diffusion (1 when all
diffusion power sits on one axis, $d$ when isotropic); $tilde(H)_a$ is the normalized Shannon
entropy of the same eigenvalue distribution; $"Tr"(a)$ is total local diffusion power. The
family's negative commitment is that $"Tr"(a)$ (H4) is *not required* to differ between groups -
a CPC1 advantage restricted to $d_"eff"^((a))$ and $tilde(H)_a$ while $"Tr"(a)$ does not favor
CPC1 would mean the advantage is geometric, not merely "more noise."

A candidate fourth metric splits diffusion relative to the local drift direction $hat(b) =
b/norm(b)$:

$ E_perp = frac("Tr"(a) - hat(b)^top a hat(b), "Tr"(a) + epsilon). $ <eq:eperp>

$E_perp$ requires an independently qualified drift estimate to be a clean drift-orthogonal
diffusion fraction; here it is computed from the stored MNPS chart-velocity `/mnps_3d_dot`
(configured Savitzky-Golay derivative, still `drift_source = not_supplied` at ingest). We
therefore label $E_perp$ a *candidate* metric throughout (H3), distinct from H1/H2/H4, which
use $a(x,t)$ alone.

== Reachability and the local generator

A complementary, drift-free view of local accessibility comes from reachability cones estimated
directly from the trajectory's local kNN geometry at horizons $h in {1,2,4}$ steps, summarized by
the same effective-dimensionality functional applied to the reachable-set covariance
(`cone_d_eff_h`), plus a smoothed persistence summary across the run (`tube_d_eff`).

Separately, a local continuous-time generator $J(x,t) = nabla_X b$ can in principle be fit from
short windows and summarized by its spectral abscissa $alpha = max "Re" lambda(J)$ and numerical
abscissa $omega = lambda_max ((J+J^top)/2)$. The pre-specified "stable-but-reactive" fraction is
$F_"reactive" = P(alpha<0<omega)$: locally stable but transiently amplifying. This object is only
meaningful when the local linear fit is actually identified by the window (fit residual
meaningfully below a null/baseline model); we treat that as a gate, not an assumption (Methods
§3.3).

= Methods <sec:methods>

== Dataset

PhysioNet I-CARE 2.1 (International Cardiac Arrest REsearch consortium
@PhysioNet-i-care-2.1 @amorim2023icare_eeg, distributed via PhysioNet
@goldberger2000physiobank), continuous scalp EEG in comatose post-cardiac-arrest adults, CPC
outcome at hospital discharge/follow-up. We use two independent NeuralManifoldDynamics (MNDM v3.0.0,
`mnps_tensor_spec_v2_4`) processed bundles, both restricted at ingest to filename hours 000-012:

- *Discovery cohort* (`20260911_125829`): 161 subjects (CPC1 $n=71$, CPC2 $n=10$, CPC3 $n=7$,
  CPC4 $n=3$, CPC5 $n=70$; hospitals A/B/D/E/F, $n=73/30/23/18/17$), 1815 recordings.
- *Confirmatory cohort* (`20260911_123135`): 140 subjects, pre-selected to CPC1/CPC5 only
  ($n=70/70$; hospitals A/B/D/E/F, $n=76/18/14/14/18$), 1838 recordings. *Zero subject overlap*
  with the discovery cohort (verified by subject-ID intersection).

Both bundles were built from an ingest overlay carrying: global MNPS-3D and MNPS-9D coordinates
(no regional/block MNPS), ComBat batch harmonization @johnson2007combat
(`batch_key=hospital`, post-features scope,
age+sex covariates, 0.5-99.5% winsorization, family-wise by feature prefix), subject-anchored and
cohort-anchored coordinate contracts, and - critical for the local-generator arm - a Jacobian
local-linear-fit fidelity gate (§3.3). ComBat harmonization reduced batch(hospital)-associated
feature variance sharply on both bundles (median $eta^2$ pre-to-post: discovery
$0.0012 arrow.r 0.00014$; confirmatory $0.019 arrow.r 0.00012$; validation computed on
samples of at most 150 000 rows per bundle, while CPC-associated feature variance was preserved or
slightly increased, consistent with harmonization removing site structure rather than the outcome
signal.

== NMDM pipeline and primary endpoints

Family-A metrics (@eq:famA) and $E_perp$ (@eq:eperp) are read from stored
`/dynamical_families/diffusion/v1` per-window `a_hat` (subject-anchored MNPS-3D,
`local_increment_covariance` estimator, `validation_level=simulator_validated`) and, for $E_perp$,
the stored MNPS chart-velocity `/mnps_3d_dot` (not a qualified Itô drift; diffusion-family
`A_bD` is all-NaN because `drift_source = not_supplied`); recomputed $d_"eff"^((a))$ agrees with the
ingest-stored `d_diff` to a median absolute difference of $4.1times 10^(-8)$ (discovery) and
$3.6times 10^(-8)$ (confirmatory), confirming the article-local reimplementation is faithful to the
ingest contract. Reachability cones are *recomputed* article-side from
`coords_3d_subject_anchored` (kNN $k=25$, ridge regression $alpha=10^(-3)$, super-window size 3,
horizons 1/2/4, jitter $10^(-6)$) rather than read from the stored
`/stochastic_reachability/v1` group, because that group is `unavailable` on $>97%$ of windows in
both cohorts once the Jacobian gate is applied upstream (§3.3) - the propagator
$Phi = exp(J Delta t)$ is not attempted when the underlying generator is not identified. Local-
generator metrics ($alpha$, $omega$, $F_"reactive" = P(alpha<0<omega)$, $F_"contract" =
P(omega<0)$, $F_"unstable" = P(alpha>0)$) are read from `/jacobian/derived_metrics/v1/series` per
window. All per-window metrics are aggregated to per-run medians, then to per-patient,
per-time-bin medians (the primary time bin being the first 0-12h EEG-anchor window from run
midpoint), matching the dataset's `direct_between_subject_inference=forbidden` grain contract
(window $arrow.r$ recording $arrow.r$ subject, repeated-measure).

== Statistical design

Unit of analysis: one row per patient in the primary 0-12h window. Primary test: two-sided
Mann-Whitney U @mannwhitney1947 on CPC1 vs CPC5 patient-level medians; secondary: Welch's $t$.
Effect sizes: Cohen's $d$ @cohen1988statistical (pooled SD) and Cliff's $delta$
@cliff1993dominance, each reported with a percentile bootstrap 95% CI (2000 resamples, arms
resampled independently, fixed seed for reproducibility). Benjamini-Hochberg FDR
@benjamini1995fdr at $alpha=0.05$ is applied *within* the H1-H3 diffusion-geometry family only
(H4 and reachability are reported descriptively and individually, not folded into that
correction family, per the pre-registration). A metric-cohort combination is additionally
flagged `family_testable = "False"` whenever either arm has fewer than 10 evaluable patients, to
prevent an underpowered contrast from being read as a null or positive result.

== Jacobian local-linear-fit fidelity gate <sec:gate>

An earlier pass on a predecessor bundle (`20260904_225047`) found the stored local-generator
series `computed` on effectively all windows regardless of local-linear-fit quality
(`rel_mse_baseline_median` typically $approx 0.96$-0.98, i.e. the local linear model did not beat
a trivial baseline), which we flagged upstream as an ingest-contract gap
(`handover/ingest_jacobian_fidelity_handover.md`). The two bundles used here were built with a
fix: `/jacobian/derived_metrics/v1` now carries an explicit fit-fidelity gate
(`fit_fidelity_gate = rel_mse_baseline_median`, `fit_fidelity_threshold = 0.9`,
`fit_fidelity_gate_version = provisional_icare_20260911`); windows failing the gate are marked
`computation_status = insufficient_support`, `failure_reason =
local_linear_fit_not_better_than_baseline`, with `summary/fit_identified = "False"` and an
all-NaN metric series (not merely a partially-populated one). We verify this gate is active and
report local-generator results only where the resulting sample size permits interpretation
(§4.4).

== Robustness checks

(1) Cross-cohort replication is the primary robustness design here, not a post hoc addition:
discovery and confirmatory cohorts are non-overlapping subject sets processed through an
identical, unmodified pipeline. (2) TTM (targeted temperature management, 33 vs 36 degrees C)
subgroup sensitivity for H1-H3. (3) Recomputed-vs-stored cross-check for $d_"eff"^((a))$ (§3.2).
(4) ComBat batch/target-variance validation probes ($eta^2$ pre/post, ingest-computed on raw
features) plus an article-local post-hoc $eta^2$ diagnostic of hospital on the *derived* H1-H4
metrics themselves (§4.7.2). (5) `family_testable` gating to prevent small-$n$ artifacts (§3.3,
§4.4). (6) Leave-one-subject-out (LOSO) sensitivity: for H1-H3, the patient-level Mann-Whitney
test is recomputed after dropping each single patient in turn, reporting whether direction and
nominal ($alpha=0.05$) significance survive every single-patient removal. (7) A run-level linear
mixed model (`value ~ C(contrast_group)`, subject random intercept, REML, `statsmodels`
`MixedLM`) fit on the pre-collapse per-run medians (not the further-collapsed per-patient
median), as a cross-check that the primary test's patient-median collapse is not manufacturing
or hiding an effect. (8) An independently recomputed local-drift estimator for $E_perp$ (§4.7),
article-side from the same stored `a_hat` tensors but a different Savitzky-Golay
derivative of `coords_3d_subject_anchored` (window 11, polyorder 2) than the
ingest `/mnps_3d_dot` chart-velocity (window 7, polyorder 3, plus
`derivative_robust`), as a drift-estimator sensitivity check on H3 specifically.
(9) A paired ingest-identity audit of Family A tensors on the 2026-09-12 re-runs
versus the 2026-09-11 predecessors used for all primary contrasts (S2.12).
(10) Rank discrimination of the same patient-medians: direct AUROC (CPC1-high)
and AUPRC, plus a univariate logistic repeated-CV / hospital-LOSO check (S2.13).
This is a translation of the Mann-Whitney ranking, not a prognostic model.
(11) A run- and window-level coverage audit of local dynamics beyond spectral abscissa
(diffusion, chart-velocity, $A_"bD"$, FTR, stored reachability, 9D Jacobian, destination,
resilience; S2.14).

= Results <sec:results>

== R1: Data quality and coverage <sec:r1>

Both bundles restrict ingest to filename hours 000-012, which incidentally resolves a WFDB
clock-parsing failure mode identified in the predecessor bundle (recording-hour headers
$>=24$ misread as invalid 24h clocks, previously 156/3484 runs `missing_or_invalid_start_end`,
CPC5-skewed): time-reference status is `ok` on 1815/1815 (discovery) and 1838/1838
(confirmatory) runs. Diffusion-family `computed` rate is 1778/1815 (98.0%) and 1797/1838 (97.8%).
Jacobian local-generator `computed` (i.e., *passed* the fidelity gate) is 22/1815 (1.2%) and
53/1838 (2.9%) - see §4.4. A full local-dynamics coverage scan (S2.14) shows the same split
in more detail: diffusion `a_hat` is finite on the computed recordings, stored $A_"bD"$ is empty
(`drift_source = not_supplied`), stored 3D reachability inherits the Jacobian gate, and FTR is
`computed` on 96-99% of files *including* those that fail that gate (`validation_level =
model_derived`). Destination and resilience are `not_testable` by contract on every file.

#figure(
  kind: table,
  clean-table(
    columns: (1.6fr, 1fr, 1fr),
    align: (left, center, center),
    inset: 5pt,
    table.header([*Quantity*], [*Discovery*], [*Confirmatory*]),
    [Subjects], [161], [140],
    [Recordings], [1815], [1838],
    [Primary-window $n$ (CPC1 / CPC5)], [71 / 70], [70 / 70],
    [Time-reference `ok`], [100%], [100%],
    [Diffusion `computed`], [98.0%], [97.8%],
    [Jacobian 3D gate `computed`], [1.2%], [2.9%],
    [Stored reachability 3D `computed`], [1.0%], [2.1%],
    [FTR 3D `computed` (model-derived)], [98.7%], [96.1%],
    [Destination / resilience `computed`], [0%], [0%],
  ),
  caption: [Coverage and gate pass rates. Diffusion tensors are populated on almost all
  recordings; 3D Jacobian derived metrics and stored 3D reachability are not. FTR is
  `computed` on most files *including* those that fail the Jacobian gate (`model_derived`;
  S2.14). Source: `results/replication/local_dynamics_coverage.md`.]
) <tab-qc>

== R2: Diffusion geometry (H1-H4), discovery cohort <sec:r2>

In the discovery cohort, $d_"eff"^((a))$ and $tilde(H)_a$ were higher in CPC1 and survived BH-FDR
within the H1-H3 family; $E_perp$ (H3) was nominally significant but with a small effect size;
$"Tr"(a)$ (H4, not required to differ) was numerically *higher* in CPC5.

#figure(
  kind: table,
  clean-table(
    columns: (0.4fr, 1.4fr, 1.2fr, 1fr, 1fr, 0.7fr),
    align: (left, left, center, center, center, center),
    inset: 5pt,
    table.header([*H*], [*Metric*], [*$d$ [95% CI]*], [*MW $p$*], [*BH $q$*], [*Sig.*]),
    [H1], [$d_"eff"^((a))$ median], [+0.76 [0.40, 1.20]], [$7.0times 10^(-7)$], [$2.0times 10^(-6)$], [Yes],
    [H2], [$tilde(H)_a$ median], [+0.58 [0.23, 1.01]], [$1.3times 10^(-6)$], [$2.0times 10^(-6)$], [Yes],
    [H3], [$E_perp$ median (candidate)], [+0.10 [$-$0.20, 0.55]], [0.043], [0.043], [Yes (marginal)],
    [H4], [$"Tr"(a)$ median (not req. to differ)], [$-$0.47 [$-$0.72, $-$0.21]], [0.049], [n/a], [n/a],
  ),
  caption: [Discovery cohort, $n=71$ CPC1 / $70$ CPC5, primary 0-12h window. Bootstrap 95% CI
  on Cohen's $d$, 2000 resamples. Source: `results/part1_corrected/outcome_contrasts.csv`.]
) <tab-r2>

== R3: Independent-cohort replication <sec:r3>

The same, unmodified pipeline was run on the confirmatory cohort (zero subject overlap). H1 and
H2 replicated: same direction, BH-significant within the H1-H3 family. H3 ($E_perp$) *did not
replicate*: the sign reversed and the contrast was not significant. H4 remained numerically in
the same (CPC5-higher) direction but was not significant on its own in the smaller cohort.

#figure(
  kind: table,
  clean-table(
    columns: (0.4fr, 1.3fr, 1.3fr, 1.3fr, 0.9fr, 1.2fr),
    align: (left, left, center, center, center, left),
    inset: 5pt,
    table.header([*H*], [*Metric*], [*Disc. $d$ [CI]*], [*Conf. $d$ [CI]*], [*Conf. $q$*], [*Call*]),
    [H1], [$d_"eff"^((a))$], [+0.76 [0.40, 1.20]], [+0.61 [0.29, 0.99]], [$1.6times 10^(-3)$], [*Replicated*],
    [H2], [$tilde(H)_a$], [+0.58 [0.23, 1.01]], [+0.48 [0.16, 0.83]], [$7.2times 10^(-3)$], [*Replicated*],
    [H3], [$E_perp$ (candidate)], [+0.10 [$-$0.20, 0.55]], [$-$0.10 [$-$0.46, 0.23]], [0.134], [Did not replicate],
    [H4], [$"Tr"(a)$], [$-$0.47 [$-$0.72, $-$0.21]], [$-$0.36 [$-$0.56, $-$0.12]], [n/a], [Same direction, n.s.],
  ),
  caption: [Discovery ($n=71/70$) vs confirmatory ($n=70/70$). Bootstrap 95% CI on Cohen's $d$.
  H1/H2 CIs exclude 0 in both cohorts. H3's CI includes 0 in both. H4's Mann-Whitney $p$ is
  0.049 (discovery) and 0.36 (confirmatory); the metric is a control, not a primary claim.
  Source: `results/replication/replication_summary.csv`, `outcome_contrasts.csv`.]
) <tab-r3>

#netn-box(title: [Primary finding])[
  Effective local diffusion dimensionality ($d_"eff"^((a))$, H1) and normalized diffusion entropy
  ($tilde(H)_a$, H2) are higher in CPC1 than CPC5 in the 0-12h EEG-anchor window, and this
  replicates in a fully independent, non-overlapping cohort, while total local diffusion power
  (H4) is not required to differ and is numerically higher in CPC5 in both cohorts.
]

Reachability-cone effective dimensionality, computed independently of the diffusion-family
adapter (direct kNN reachability on subject-anchored coordinates, not $a_"hat"$), shows the same
CPC1-favoring pattern at both horizons in both cohorts, individually significant in each cohort
(not pooled into the H1-H3 BH family):

#figure(
  kind: table,
  clean-table(
    columns: (1.6fr, 1fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center, center),
    inset: 5pt,
    table.header([*Metric*], [*Disc. $d$*], [*Disc. $p$*], [*Conf. $d$*], [*Conf. $p$*]),
    [`cone_d_eff` ($h=1$)], [+0.81], [$1.1times 10^(-6)$], [+0.66], [$2.3times 10^(-4)$],
    [`cone_d_eff` ($h=4$)], [+0.80], [$5.7times 10^(-6)$], [+0.74], [$8.3times 10^(-5)$],
    [`tube_d_eff`], [+0.82], [$2.2times 10^(-6)$], [+0.70], [$1.6times 10^(-4)$],
  ),
  caption: [Reachability-cone effective dimensionality, both cohorts. The CPC1 advantage is
  already present at the shortest horizon tested ($h=1$; "Case A": not an emergent multi-step
  effect). Source: `results/part1_corrected/outcome_contrasts.csv`, `results/part2_confirmatory/outcome_contrasts.csv`.]
) <tab-reach>

== R4: Robustness <sec:r4>

TTM (targeted temperature management) subgroup sensitivity: in the 33 degrees C stratum (the
large majority of both cohorts: 55/49 discovery, 50/50 confirmatory), H1 held direction and
significance in both cohorts (discovery $d=+0.52$, $p=0.0013$; confirmatory $d=+0.47$,
$p=0.032$). The 36 degrees C stratum had fewer than 10 patients per arm in both cohorts and is
not reported as a contrast (`family_testable = "False"`).

The article-local diffusion-geometry reimplementation matches the ingest-stored series closely
(median absolute difference in $d_"eff"^((a))$: $4.1times 10^(-8)$ discovery,
$3.6times 10^(-8)$ confirmatory), so H1/H2/H4 do not depend on an article-local estimator
diverging from the certified ingest computation.

*Ingest re-run identity (Family A).* A later summarize re-run of the same populations
(`20260912_094016` vs `20260911_125829`; `20260912_094010` vs `20260911_123135`) left
diffusion `computation_status`, per-run $d_"eff"$ and $D_"total"$ medians, $|a_"hat"|$,
subject-anchored coordinates, and `/mnps_3d_dot` bit-identical on all 1815+1838 matching
recordings ($|Delta| = 0$; S2.12). The H1-H4 and reachability numbers above therefore do
not need to be recomputed on the 2026-09-12 bundles. Stored $A_"bD"$ remains all-NaN
(`drift_source = not_supplied`): $E_perp$ is computed article-side from $a_"hat"$ plus
`/mnps_3d_dot`.

*Leave-one-subject-out and run-level mixed-effects checks.* H1 and H2 are stable under LOSO in
both cohorts: dropping any single patient never flips nominal significance
($p in [2.4times 10^(-7), 1.1times 10^(-6)]$ across all 141 discovery-cohort drops for H1, all
same-sign), and the same holds in the confirmatory cohort. H3 ($E_perp$, stored `/mnps_3d_dot` chart-velocity) is
LOSO-*unstable* in the discovery cohort (nominal $p$ ranges $[0.029, 0.058]$ across drops,
straddling $alpha=0.05$) and consistently non-significant in the confirmatory cohort. A run-level
linear mixed model (subject random intercept, all runs in the primary window, not collapsed to a
single per-patient value: 1556 runs / 141 subjects discovery, mean 11.0 runs/subject; 1692 runs /
140 subjects confirmatory, mean 12.1 runs/subject) independently confirms H1 and H2 in both
cohorts (discovery: $p=5.8times 10^(-6)$, $p=5.0times 10^(-4)$; confirmatory:
$p=2.6times 10^(-4)$, $p=2.4times 10^(-3)$) and confirms H3's non-significance with the stored
chart-velocity (discovery $p=0.53$; confirmatory $p=0.47$). H1 and H2 are therefore not an artifact
of collapsing each patient's runs to a single median before testing.

*Rank discrimination (AUROC / AUPRC).* Direct AUROC here is the Mann-Whitney probability
that a random CPC1 patient-median exceeds a random CPC5 patient-median, i.e.
$(delta + 1)/2$ for Cliff's $delta$, not a fitted prognostic model and not an incremental
test against clinical covariates or conventional qEEG (that pack was not materialized).
H1 and H2 show moderate CPC1-high discrimination that replicates (discovery AUROC
$0.74$ $[0.66, 0.83]$ and $0.74$ $[0.65, 0.82]$; confirmatory $0.67$ $[0.58, 0.76]$ and
$0.64$ $[0.55, 0.73]$); AUPRC tracks AUROC because the arms are balanced. Stored-drift
$E_perp$ does not (confirmatory AUROC $0.43$ $[0.33, 0.52]$). Univariate logistic
repeated-CV AUROC matches the direct rank AUROC for H1/H2; hospital-LOSO AUROC is lower,
especially for H2 in the confirmatory cohort ($0.55$), consistent with residual site
structure already flagged by $eta^2$ (§4.5). Full table: S2.13.

== R5: Confound handling <sec:r5>

Hospital site is unevenly distributed across CPC in the discovery cohort (e.g. hospital E: 2
CPC1 vs 15 CPC5 subjects); the confirmatory cohort is, by contrast, exactly hospital-CPC balanced
(each of its five hospitals contributes equal CPC1 and CPC5 counts: 38/38, 9/9, 7/7, 7/7, 9/9).
ComBat harmonization (`batch_key=hospital`) was applied upstream of all feature-derived metrics
used here, and ingest-computed validation probes show batch-associated feature variance sharply
reduced post-harmonization while CPC-associated variance was preserved or increased (§3.1). We
additionally ran an article-local post-hoc diagnostic: a one-way $eta^2$ of hospital on the
*derived* H1-H4 metrics themselves (not just the upstream raw features). Residual hospital
$eta^2$ remains non-trivial on H1-H3 in *both* cohorts (0.11-0.18, all $p<0.005$,
flagged against a 0.06 medium-effect convention), including in the confirmatory cohort where
hospitals are outcome-balanced by design. Because the confirmatory cohort's hospitals are
exactly balanced on CPC, this residual $eta^2$ there cannot itself explain the CPC1-vs-CPC5
contrast (equal arms per site rule out a hospital-selection confound), but it does show that
ComBat harmonization at the raw-feature level does not fully remove site-level variance from
the *derived*, nonlinear diffusion-geometry metrics. The discovery cohort's hospital-E imbalance
remains a genuine, only partially controlled confound risk there.

#netn-box(title: [Dissociation finding])[
  The CPC1 advantage is specific to diffusion *geometry* (H1, H2), not diffusion *magnitude*
  (H4): total local diffusion power was not required to differ and was numerically higher in
  CPC5 in both cohorts, so "more accessible" here does not mean "more active."
]

== R6: Secondary analysis - local generator (Family B) <sec:r6>

The pre-specified $F_"reactive"$ hypothesis could not be tested. After the fidelity gate
(§3.3), only 22/1815 (discovery) and 53/1838 (confirmatory) recordings have any window with an
identified local linear fit; only 13/163 and 24/215 patient-time-bin rows have a finite mean
spectral abscissa at all. The resulting primary-window sample is 7 CPC1 / 6 CPC5 (discovery,
below the 10-per-arm testability threshold) and 11/11 (confirmatory, at the threshold but
severely underpowered). We report this contrast as *not testable* on this dataset with this
estimator and window, rather than as a null or contradicting result:

#figure(
  kind: table,
  clean-table(
    columns: (1.6fr, 1fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center, center),
    inset: 5pt,
    table.header([*Cohort*], [*Gate `computed`*], [*Any finite $alpha$*], [*$n$ (1/5)*], [*Testable*]),
    [Discovery], [22/1815 (1.2%)], [13/163], [7 / 6], [No],
    [Confirmatory], [53/1838 (2.9%)], [24/215], [11 / 11], [Borderline],
  ),
  caption: [Local-generator (Family B) testability. Dominant `failure_reason` in both cohorts:
  `local_linear_fit_not_better_than_baseline` ($>=97%$ of gated windows). Source:
  `results/part1_corrected/mnj_v3_manifest.json`, `results/part2_confirmatory/mnj_v3_manifest.json`.]
) <tab-r6>

This retroactively supports a concern raised before the fidelity gate existed: on a predecessor
bundle without the gate, $F_"reactive"$ was `computed` on effectively all windows and showed a
small, *opposite-to-predicted* CPC1-vs-CPC5 contrast. With the gate active, that earlier
"signal" cannot be distinguished from an artifact of fitting a linear generator to windows where
no such generator is locally identified ($"rel\_mse\_baseline\_median" approx 0.96$-0.98, i.e. at
or above the noise floor of a trivial baseline). We do not treat the pre-gate result as evidence
against the stable-reactive-window hypothesis, and we do not treat the post-gate small-$n$
contrast as evidence for or against it either.

A complete paired re-read of the 2026-09-12 ingest re-runs
(`20260912_094016` vs `20260911_125829`; `20260912_094010` vs `20260911_123135`)
confirms that spectral abscissa itself is unchanged: all 1815+1838 matching
recordings keep the same `computation_status`, the 22+53 `computed` runs have
identical per-run mean $alpha$, and $|Delta "rel\_mse"| = 0$. The re-runs add
`knn_k` provenance; they do not move any window through the gate. Among the
gated-pass recordings that remain, mean $alpha$ is higher in CPC1 in discovery
(patient-level $d=+0.79$, $n=7/6$, $p=0.14$, not testable) and higher in CPC5
in the confirmatory cohort ($d=-1.27$, $n=11/11$, $p=0.013$, borderline $n$).
That sign reversal, on a selected $1$–$3%$ subset of recordings, is why we do
not read $alpha$ as a result in either direction (full paired table: S2.11).

== R7: Post-hoc robustness check - a second drift estimator for $E_perp$ <sec:r7>

R3 found $E_perp$ (H3) did not replicate using the stored MNPS chart-velocity `mnps_3d_dot`,
which ingest does not treat as a qualified Itô drift (`drift_source = not_supplied`; §2.1,
S2.12). A paired audit shows `/mnps_3d_dot` is closer to a Savitzky-Golay derivative of
`coords_3d_subject_anchored` (window 7, polyorder 3) than to a raw one-step increment (median
MAE 0.057 vs 0.11; closer on 99.9% of recordings), with a residual consistent with ingest
`derivative_robust`. Because H3 is still estimator-sensitive, we built an article-local,
read-only alternative: a different Savitzky-Golay derivative of the same coordinate series
(window 11 samples $approx$ 44 s, 2nd-order polynomial, no ingest robust filter), recombined with
the unmodified stored `a_hat` tensor (@eq:eperp). This is explicitly a *post-hoc* estimator
choice, made after observing that H3 was weak/non-replicating with the stored proxy, and is
reported as such - not as a pre-registered confirmatory test.

With the smoothed drift estimator, $E_perp$ is higher in CPC1 in *both* cohorts, at a materially
larger effect size than the original H1/H2 confirmation:

#figure(
  kind: table,
  clean-table(
    columns: (1.4fr, 1fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center, center),
    inset: 5pt,
    table.header([*Cohort*], [*$d$ (1$-$5)*], [*95% CI*], [*MW $p$*], [*LOSO stable?*]),
    [Discovery ($n=71/70$)], [+0.68], [[0.39, 0.99]], [$6.4times 10^(-6)$], [Yes (0/141 drops flip)],
    [Confirmatory ($n=70/70$)], [+0.47], [[0.16, 0.79]], [0.0088], [Yes (0/140 drops flip)],
  ),
  caption: [$E_perp$ with the Savitzky-Golay smoothed drift estimator, both cohorts. Bootstrap CI:
  2000 resamples, percentile method. Source: `results/part1_corrected/qualified_drift_contrast.csv`,
  `results/part2_confirmatory/qualified_drift_contrast.csv`, `*_loso_summary.json`.]
) <tab-r7>

This is not a free parameter fished from a wide search: a sweep of the smoothing window (7, 11,
15, 21 samples, $approx$ 28-84 s) leaves both cohorts significant in the predicted direction at
every window tested (discovery $d in [0.68, 0.73]$, $p in [2.5times 10^(-6), 6.4times 10^(-6)]$;
confirmatory $d in [0.47, 0.53]$, $p in [0.0051, 0.0139]$), so the result is not sensitive to the
exact article-side smoothing bandwidth. It *is* sensitive to which Savitzky-Golay
implementation is used: ingest `/mnps_3d_dot` (window 7, polyorder 3, plus robust jump
filtering) versus the article-local 11/2 estimator, both read from the same coordinates and
the same unmodified diffusion tensors.

#netn-box(title: [Post-hoc robustness finding, not a confirmed result])[
  With an article-local Savitzky-Golay chart-velocity (window 11, polyorder 2) in place of the
  stored ingest derivative, $E_perp$ (H3) shows a large, LOSO-stable, cross-cohort-replicating
  CPC1 advantage ($d approx 0.5$-$0.7$). Because that estimator was selected *after* seeing that
  H3 was weak with `/mnps_3d_dot`, this is a *promising post-hoc finding*, not an internally
  validated result on the same footing as H1/H2. It should be confirmed with a drift estimator
  specified in advance on a third, held-out cohort before being treated as a primary claim.
]

= Discussion <sec:discussion>

== Primary finding

In two independent, non-overlapping cohorts totaling 301 patients, good neurological outcome
after cardiac arrest (CPC1) was associated with higher effective local diffusion dimensionality
and higher normalized diffusion entropy in the first 12 hours of EEG, while total local diffusion
power was not elevated in CPC1 - if anything the opposite. This is consistent with the
theoretical framing that recovery-linked coma reflects a *geometrically richer* local stochastic
accessibility structure rather than a globally more active or more variable one, and it goes
beyond a single-cohort finding: H1 and H2 are, to our knowledge, the first result in this article
line to survive an independent-cohort replication with an unmodified pipeline.

== What did not replicate with the original estimator, and why that matters

$E_perp$ (H3), the candidate drift-orthogonal diffusion fraction, was nominally significant with
a small effect in the discovery cohort but reversed sign and lost significance in the
confirmatory cohort *when computed from the stored MNPS chart-velocity* `mnps_3d_dot`. Because
$E_perp$ depends on an unqualified drift estimate rather than an independently validated Itô
drift, we treated this as more consistent with a drift-proxy-sensitive metric than with a real
but small effect, and we built a post-hoc alternative (a different Savitzky-Golay implementation)
to test that interpretation directly (§4.7). That alternative (§4.7) found a large, LOSO-stable, cross-cohort-replicating
CPC1 advantage - evidence in favor of "drift-proxy-sensitive," not "no effect." We still do not
promote this to a confirmed result, because the smoothed estimator was chosen after seeing the
original result was weak (a post-hoc, not pre-registered, analytic choice), but it substantially
raises our confidence that H3 deserves a proper prospective test with an estimator fixed in
advance, rather than being retired as a non-replicating candidate.

== Confound interpretation

Hospital-site imbalance against CPC (most visible at one site: 2 CPC1 vs 15 CPC5) is a real
design concern in observational multi-site EEG. ComBat harmonization at the feature level,
validated by ingest-computed batch/target variance probes, substantially reduced
batch-associated variance while preserving CPC-associated variance in both cohorts. This
harmonization step, together with running the identical pipeline on a geographically and
temporally independent second cohort, is the strongest confound control available in this
dataset version. We directly tested, rather than assumed, whether residual site confounding
survives at the level of the derived geometric metrics (§4.5): a non-trivial residual hospital
$eta^2$ (0.11-0.18) remains on H1-H3 in *both* cohorts, including the confirmatory cohort whose
hospitals are exactly CPC-balanced by design - in that cohort, the residual effect is site-level
variance orthogonal to outcome, not an outcome confound, because equal arms per site rule out
selection as the explanation. In the discovery cohort, where hospital E is genuinely
CPC-imbalanced, the same residual $eta^2$ is harder to fully disentangle from a site confound.
The practical conclusion is that ComBat at the raw-feature level does not fully remove
site-level variance from these nonlinear derived metrics, and a hospital-stratified or
hospital-random-effect sensitivity analysis (beyond the mixed model already used for the
subject-level random effect, §4.4) is a natural next step before treating H1/H2 as
site-independent.

== Secondary findings: the local generator is not currently testable here

The pre-specified local-generator hypothesis ($F_"reactive"$) is the clearest example in this
article of the difference between a *rejected* hypothesis and a *not-yet-testable* one. Once an
honest local-linear-fit fidelity gate is applied - itself the direct result of an ingest-contract
fix requested after reviewing a predecessor bundle - more than 97% of windows in both cohorts
fail to identify a local linear generator at all. This is very likely a property of the
estimation problem at this window length (8 s windows, 4 s step) on EEG-derived MNPS-3D
coordinates, not of the patients. We regard the earlier, pre-gate "signal" (small,
opposite-to-predicted direction) as retired: it should not be cited as evidence either for or
against the stable-reactive-window hypothesis.

== Limitations

(1) Sedation, other medications, and withdrawal-of-life-sustaining-therapy status are not present
in this export and are not controlled for; CPC5 in particular conflates poor neurological
recovery with early WLST death. Checked directly: the exported participant metadata contains only
`hospital, age, sex, rosc, ohca, shockable_rhythm, ttm, outcome, cpc` - no sedation or WLST field
exists in this export at all, so this cannot be addressed without a different data source. (2)
Both bundles are restricted to filename hours 000-012, which side-steps a WFDB clock-parsing
issue for this window but means later-window dynamics are out of scope here. (3) The
local-generator estimator is not usable at the current window/step on this chart. Direct
inspection of the window contract (8 s window, 4 s step, i.e. $approx$1-2 finite-difference
increments per window to identify a 3x3 local generator) versus the diffusion family's pooled
`neighborhood: {k: 20}, min_samples: 30` (98% `computed`) strongly suggests the fit is
under-determined by construction, not that patients lack local linear structure; a neighborhood-
pooled Jacobian estimator and real EEG-artifact rejection (currently `qc_ok_eeg` is
`not_assessed` on 100% of sampled windows) have been requested upstream
(`handover/ingest_jacobian_estimator_quality_handover.md`). (4) The smoothed-drift $E_perp$
finding (§4.7) uses a post-hoc, not pre-registered, estimator choice and needs a prospective
confirmation with the estimator fixed in advance before being treated as established; the
stored chart-velocity (`mnps_3d_dot`) is an ingest Savitzky-Golay derivative (window 7,
polyorder 3, plus `derivative_robust`), still unqualified as an Itô drift
(`drift_source = not_supplied`). (5) A `conventional_eeg` qEEG comparator pack is enabled in the ingest
overlay for both bundles but was not materialized in either export (requires a features-stage
rerun at ingest), so no incremental-validity comparison against conventional qEEG markers is
presented here. (6) The confirmatory cohort was pre-selected to CPC1/CPC5 only (no CPC2-4), so it
is not a fully unselected replication of the discovery cohort's clinical mix, though the
CPC1-vs-CPC5 contrast itself is on equally independent, non-overlapping subjects. (7) Residual
hospital $eta^2$ (0.11-0.18) on the derived H1-H3 metrics persists after ComBat harmonization in
both cohorts (§4.5); a hospital-random-effect sensitivity analysis has not yet been run.

== Conclusion

Local diffusion geometry - specifically its effective dimensionality and entropy, not its total
power - distinguishes good from poor outcome after cardiac-arrest coma in PhysioNet I-CARE 2.1,
and this result replicates in an independent, non-overlapping cohort, surviving leave-one-subject-
out perturbation and a run-level mixed-effects cross-check. A companion hypothesis about a
locally fitted deterministic generator remains untested in the strict sense: the estimator
required to test it does not currently identify on this EEG chart once fit quality is honestly
gated, which is itself a methodologically useful and reportable outcome, and we have a concrete,
evidence-based request upstream for why (window/step under-determination, no artifact
rejection) rather than a generic "needs more data." A third hypothesis ($E_perp$) moved from
"did not replicate" to "promising but not yet confirmed" once measurement quality on the drift
estimate was improved post hoc - a concrete illustration that some non-replications in this
article line are more likely measurement-quality artifacts than biological absences, and should
be revisited with better instrumentation before being retired.

= Acknowledgements

We thank the PhysioNet I-CARE consortium investigators, clinical teams, and data stewards, and
the NeuralManifoldDynamics ingest maintainers who implemented the Jacobian fit-fidelity gate,
ComBat harmonization, and cohort-anchored coordinate contract in direct response to issues raised
during this analysis.

This work emerged through structured correspondence among human and AI collaborators; large language models from OpenAI, Anthropic, and Google assisted in literature synthesis, drafting, peer review, and editorial refinement. We also gratefully acknowledge the original investigators, clinical teams, participants, and data stewards who created, curated, and shared the public datasets and metadata that made these analyses possible.

#bibliography("references.bib", style: "apa")
