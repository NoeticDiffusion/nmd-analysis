#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Trajectory Grammar of First-Episode Psychosis: Noetic Action, Entropy Rate, and Temporal Irreversibility in Resting EEG",
  short-title: "Trajectory Geometry in First-Episode Psychosis",
  subtitle: "NeuralManifoldDynamics 2.1 trajectory geometry analysis of ds003944 and ds003947",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "first-episode psychosis",
    "EEG",
    "trajectory geometry",
    "noetic action",
    "entropy rate",
    "temporal irreversibility",
    "NeuralManifoldDynamics",
    "medication stratification",
  ),
  article-type: "Research Article / Exploratory Methods Report",
  abstract: [
    We analysed resting-state trajectories from two first-episode psychosis EEG cohorts (`ds003944` and `ds003947`) using NeuralManifoldDynamics 2.1 subject-anchored coordinates within a Noetic Diffusion Theory (NDT) framework. Rather than asking where subjects occupy a shared state space, this companion study asks how they move through it: by computing repertoire-flow and noetic-action metrics — entropy rate, temporal irreversibility, and total noetic action including a jerk component — from each subject's 3D and 9D MNPS trajectory. The primary design retains the same three-group medication stratification (`Healthy`, `FEP unmedicated`, `FEP medicated`) as the companion static-geometry study. In `ds003944` (`32` healthy, `19` unmedicated, `31` medicated), `FEP unmedicated vs Healthy` produced the strongest trajectory signal: 3D `noetic_action` ($d = 0.774$, $p = 0.006$, $q = 0.052$) and `noetic_action_potential` ($d = 0.728$, $p = 0.012$, $q = 0.052$), both narrowly above the BH-FDR threshold but representing the largest effects in this cohort. In `ds003947` (`30` healthy, `8` unmedicated, `23` medicated), a directional `entropy_rate` trend was observed for `FEP medicated vs FEP unmedicated` ($d = -0.769$, $p = 0.082$), indicating reduced transition entropy in the medicated subgroup, but no contrast reached correction with that sample size. Across both cohorts, the medicinaton dissociation is reversed relative to the companion static-geometry report: here, unmedicated FEP carries the clearest trajectory-level signal in the powered cohort, while medicated FEP shows only weak trajectory effects despite its clear static coordinate displacement. This double dissociation — unmedicated FEP elevated in trajectory action, medicated FEP elevated in static position — is consistent with a model in which antipsychotic exposure normalises the dynamic grammar of state-space traversal while introducing a residual positional shift. The jerk component of noetic action (resistance to acceleration) is directionally lower in medicated vs unmedicated FEP, partially consistent with a jerk-dampening account of antipsychotic action on aberrant salience dynamics, but this comparison does not survive correction. These results should be read as exploratory: they establish that trajectory-level NDT metrics expose a medication-sensitive FEP signature that is complementary to, and partially dissociated from, the static coordinate separation reported in the companion study, but the primary `noetic_action` result narrows misses the FDR threshold and the `ds003947` effects are power-limited.
  ],
  data-availability: [
    All article-facing outputs were generated from the 2026-05-20 NeuralManifoldDynamics 2.1 subject-anchored exports for `ds003944` and `ds003947`, processed by the article-local trajectory pipeline in `articles/CLINICAL/psychosis_first_time_geometric_trajectory/src/run_psychosis_trajectory_geometry.py`. Results are written under `articles/CLINICAL/psychosis_first_time_geometric_trajectory/results/trajectory_geometry_20260607_full/`. The primary files used for this draft are `ds003944_subject_trajectory_metrics.csv`, `ds003944_trajectory_contrasts.csv`, `ds003947_subject_trajectory_metrics.csv`, `ds003947_trajectory_contrasts.csv`, and `manifest.json`.
  ],
  competing-interests: [
    No competing interests are declared in this manuscript draft.
  ],
)

= Introduction

A fixed shared-reference state-space can organize first-episode psychosis (FEP) heterogeneity into medication-stratified coordinate separations @langell2026_psychosis. The companion study to the present report established that, across two resting-state EEG cohorts (`ds003944` and `ds003947`), NeuralManifoldDynamics 2.1 exposes clinically meaningful geometry in a common cross-subject MNPS coordinate frame. In `ds003944`, the corrected signal was dominated by a static displacement of the `m`-family coordinate in medicated FEP. In `ds003947`, the single corrected effect appeared instead in a first-order trajectory descriptor — `m_delta_mean_median` — for unmedicated FEP.

That trajectory effect motivates the present study. If a static-geometry paper finds that trajectory drift (`m_delta_mean_median`) is the strongest effect in one cohort, then a deeper trajectory analysis might reveal further medication-sensitive structure that static summaries cannot expose. The present report therefore applies the full repertoire-flow and noetic-action pipeline @langell2026_trajectory to the same two FEP cohorts, computing entropy rate, temporal irreversibility, and total noetic action (including a jerk-weighted term) from each subject's 3D and 9D subject-anchored trajectory.

The theoretical motivation is as follows. Static coordinates describe where the brain's state tends to sit. Trajectory geometry describes how it moves: how predictably, how reversibly, and with what "effort" or path cost per unit time. In first-episode psychosis, aberrant salience models predict episodic, abrupt redirections of neural state that may not be visible in averaged coordinates but should appear in higher-order path descriptors @kapur2003psychosis. Antipsychotic drugs target dopaminergic aberrant salience specifically, which predicts a selective normalization of these dynamic descriptors in medicated patients, even if a residual positional shift persists. This leads to a testable double dissociation: medicated FEP should show attenuated trajectory action relative to unmedicated FEP, while retaining its static coordinate displacement.

The noetic action metric used here is a path-integral summary of trajectory effort, combining kinetic energy, a jerk-weighted acceleration cost, and a manifold-position potential @langell2026_trajectory. Jerk — the rate of change of acceleration — is the specific term predicted to be most sensitive to episodic aberrant redirections, because it captures abrupt rather than sustained deviations. The entropy rate and temporal irreversibility metrics capture a complementary view: how unpredictably and directionally the trajectory visits discrete state-space regions.

This paper does not aim to replace or supersede the companion static-geometry report. Its goal is narrower: to establish whether trajectory metrics add a complementary layer of medication-sensitive separation, and to test whether the jerk-related predictions are directionally supported in the available FEP data. Given that ds003947 has only eight unmedicated participants, the main inferential weight rests on ds003944; ds003947 is treated as a directional replication target.

= Methods

== Datasets and group definition

Both datasets are the same resting-state FEP EEG cohorts as the companion study: OpenNeuro `ds003944` and `ds003947` @ds003944_openneuro @ds003947_openneuro @phalen2020alpha. Group assignment uses the same medication split as the companion: `CPZ_at_scan > 0` defines `FEP medicated`, and `CPZ_at_scan = 0` or `n/a` defines `FEP unmedicated`.

#table(
  columns: (1.1fr, 1.35fr, 0.7fr, 0.9fr, 0.9fr, 1.0fr, 0.95fr),
  inset: 6pt,
  align: (left, left, center, center, center, center, center),
  table.header(
    [*Dataset*],
    [*Group*],
    [*N*],
    [*Age mean*],
    [*Age SD*],
    [*Female n (%)*],
    [*CPZ median*],
  ),
  [ds003944], [Healthy], [32], [21.61], [3.97], [12 (37.5%)], [--],
  [ds003944], [FEP unmedicated], [19], [22.33], [4.21], [5 (26.3%)], [`0 / n.a.`],
  [ds003944], [FEP medicated], [31], [22.34], [5.41], [11 (35.5%)], [`227.3`],
  [ds003947], [Healthy], [30], [24.20], [5.13], [14 (46.7%)], [--],
  [ds003947], [FEP unmedicated], [8], [25.01], [5.06], [2 (25.0%)], [`0 / n.a.`],
  [ds003947], [FEP medicated], [23], [22.82], [4.57], [7 (30.4%)], [`303.0`],
)

#v(6pt)

== Subject-anchored coordinate contract

This study uses subject-anchored MNPS coordinates rather than the cohort-anchored contract used in the companion static-geometry paper. The distinction matters here because trajectory metrics (entropy rate, irreversibility, noetic action) are computed from within-subject temporal sequences, so what counts is the local geometry of each subject's trajectory rather than its absolute position in a shared inter-subject space. The subject-anchored coordinates are centered and scaled per subject, which normalises between-subject differences in global dynamic range and allows the trajectory metrics to reflect the structural grammar of movement rather than merely its average position.

Formally, the subject-anchored feature transform uses per-subject center and scale terms derived from the subject's own trajectory. The resulting `coords_3d_subject_anchored` and `coords_9d_subject_anchored` datasets are read from the NeuralManifoldDynamics 2.1 H5 exports for each subject, with time stamps from the `time` dataset.

== Trajectory metric pipeline

Each subject's coordinate time series $bold(z)_t in RR^k$ (with $k=3$ or $k=9$) is processed through two complementary metric families.

=== Repertoire-flow metrics

The trajectory is discretised by assigning each time window to a state bin using a shared codebook fitted by Mini-Batch K-Means on the pooled data from all subjects in the same dataset. For $k=3$, the codebook has $N_S = 12$ states; for $k=9$, it has $N_S = 24$ states. The fitted codebook is identical across all subjects in one dataset, ensuring that the discrete state labels are comparable between groups.

From the discrete state sequence ${s_t}$, we compute the one-step transition matrix

$
P_(i j) = Pr(s_(t+1) = j | s_t = i)
$

and the empirical stationary distribution $pi_i$. Repertoire metrics are then

$
H_"rate" = -sum_i pi_i sum_j P_(i j) log(P_(i j) + epsilon), quad
I = 1/2 sum_(i,j) |pi_i P_(i j) - pi_j P_(j i)|, quad
E_"prod" = sum_(i,j) pi_i P_(i j) log frac(pi_i P_(i j) + epsilon, pi_j P_(j i) + epsilon),
$

where $H_"rate"$ is the entropy rate, $I$ is temporal irreversibility, and $E_"prod"$ is entropy production. Supplementary descriptors are self-loop rate and transition sparsity.

=== Noetic action metrics

The noetic action is a path-integral summary of trajectory cost @langell2026_trajectory. For consecutive windows with times $t-1, t, t+1$ and intervals $Delta t_"prev" = t - (t-1)$, $Delta t_"next" = (t+1) - t$:

$
Delta bold(z)_t = bold(z)_(t+1) - bold(z)_t, quad
Delta^2 bold(z)_t = bold(z)_(t+1) - 2 bold(z)_t + bold(z)_(t-1),
$

$
L_t = underbrace(1/2 frac(||Delta bold(z)_t||^2_M, Delta t_"next"^2), "kinetic") +
      underbrace(eta frac(||Delta^2 bold(z)_t||^2_M, Delta t_"center"^4), "jerk cost") +
      underbrace(lambda Phi(bold(z)_t), "potential"),
$

where $||dot||^2_M = dot^T M dot$ uses the diagonal metric $M = "diag"(1/sigma^2_j)$ computed from pooled trajectory variance, and $Phi(bold(z)_t)$ is the manifold potential. For the 3D chart, $Phi = e_t - m_t + d_t$; for the 9D chart, $Phi = bar(e)_t - bar(m)_t + bar(d)_t$ with subfamily means. The jerk weight $eta = 1$ and potential weight $lambda = 1$ are held fixed. The subject summary is the median of $L_t$ across valid windows. Kinetic, jerk, and potential components are also reported separately.

== Statistical design

Contrasts are run for `FEP unmedicated vs Healthy`, `FEP medicated vs Healthy`, and `FEP medicated vs FEP unmedicated`, within each dataset. The test statistic is Mann-Whitney U (two-sided), with Cohen's $d$ as the standardised effect-size summary. BH-FDR is applied within each contrast and analysis type (3D, 9D). Effect sizes use the sign convention positive = first group higher, consistent with the contrast label order (e.g., `FEP unmedicated vs Healthy` gives positive $d$ when FEP unmedicated exceeds healthy).

The endpoint hierarchy below follows the same discipline as the companion study:

#table(
  columns: (auto, auto, auto),
  inset: 6pt,
  align: (left, center, left),
  table.header(
    [*Layer*],
    [*Status*],
    [*Reason*],
  ),
  [3D repertoire-flow: entropy rate, irreversibility, noetic action], [Primary], [pre-specified article-facing metrics; highest interpretability],
  [3D noetic action components (kinetic, jerk, potential)], [Secondary], [mechanistic decomposition; noisier but theoretically motivated],
  [9D versions of all metrics], [Secondary / sensitivity], [higher-dimensional decomposition using same pipeline],
  [Entropy production, self-loop rate, transition sparsity], [Exploratory], [useful diagnostics; not primary inferential targets],
)

#v(4pt)
#text(size: 9pt, style: "italic")[
  Claim hierarchy: primary claims concern the 3D article-facing metrics with BH-FDR correction; secondary claims concern 9D replication and jerk decomposition; exploratory claims concern supplementary descriptors and the ds003947 directional patterns.
]

= Results

== ds003944

The clearest `ds003944` trajectory result appeared for `FEP unmedicated vs Healthy`. In the 3D analysis, `noetic_action` showed a positive effect ($d = 0.774$, $p = 0.006$, $q = 0.052$) and the potential component `noetic_action_potential` showed a closely related effect ($d = 0.728$, $p = 0.012$, $q = 0.052$). Both narrowly missed the BH-FDR threshold of $q <= 0.05$. The 9D layer produced a directionally consistent but weaker trend for `noetic_action` ($d = 0.441$, $p = 0.096$). The direction of the effect is unambiguous: unmedicated FEP traverses the subject-anchored manifold with higher path cost than healthy controls.

#table(
  columns: (auto, auto, auto, auto, auto, auto),
  inset: 6pt,
  align: (left, left, center, center, center, left),
  table.header(
    [*Contrast*],
    [*Block / feature*],
    [*Cohen $d$*],
    [*$p$*],
    [*$q$*],
    [*Tier*],
  ),
  [FEP unmedicated vs Healthy], [3D `noetic_action`], [+0.774], [0.0062], [0.0524], [`p<0.05`],
  [FEP unmedicated vs Healthy], [3D `noetic_action_potential`], [+0.728], [0.0116], [0.0524], [`p<0.05`],
  [FEP unmedicated vs Healthy], [9D `noetic_action`], [+0.441], [0.0958], [0.6847], [`p<0.1`],
  [FEP medicated vs FEP unmedicated], [3D `irreversibility`], [-0.499], [0.2504], [0.4508], [`ns`],
  [FEP medicated vs FEP unmedicated], [3D `noetic_action_jerk`], [-0.351], [0.3792], [0.5488], [`ns`],
  [FEP medicated vs FEP unmedicated], [3D `noetic_action_potential`], [-0.362], [0.0932], [0.4061], [`p<0.1`],
  [FEP medicated vs Healthy], [3D `noetic_action`], [+0.362], [0.1757], [0.5520], [`ns`],
)

#v(4pt)
#text(size: 9pt, style: "italic")[
  Interpretation: unmedicated FEP shows higher trajectory cost than healthy controls; medicated FEP sits between the two groups on most metrics, with directionally lower jerk and irreversibility relative to unmedicated FEP. No contrast reached BH-FDR correction. Note that the `ds003944` companion static-geometry result placed the primary corrected signal in medicated FEP (`m_mean` $d=0.881$, $q=0.016$); here the trajectory signal reverses to unmedicated FEP, consistent with a medication-stratified dissociation rather than a universal psychosis signature.
]

The `FEP medicated vs Healthy` comparison showed only weak trajectory effects ($d <= 0.38$, all ns after correction), confirming that the static `m`-axis displacement seen in the companion study is not mirrored by a trajectory-level displacement in medicated FEP. The `FEP medicated vs FEP unmedicated` comparison was directionally consistent with the dissociation: medicated FEP tended toward lower `noetic_action_jerk` ($d = -0.351$) and lower `irreversibility` ($d = -0.499$) than unmedicated FEP, which is the predicted direction if antipsychotics dampen trajectory jerkiness. Neither effect survived correction.

== ds003947

In `ds003947`, the primary power limitation is the small unmedicated subgroup ($n = 8$). No contrast reached correction. The most notable trend was a `FEP medicated vs FEP unmedicated` difference in 3D `entropy_rate` ($d = -0.769$, $p = 0.082$), indicating that medicated FEP has lower transition entropy than unmedicated FEP. This is directionally consistent with the `ds003944` pattern: antipsychotics appear to reduce trajectory unpredictability (entropy rate) and by implication jerkiness, while unmedicated FEP retains higher dynamic complexity. The 9D `entropy_rate` showed a similar trend for unmedicated vs healthy ($d = +0.519$, $p = 0.130$).

#table(
  columns: (auto, auto, auto, auto, auto, auto),
  inset: 6pt,
  align: (left, left, center, center, center, left),
  table.header(
    [*Contrast*],
    [*Block / feature*],
    [*Cohen $d$*],
    [*$p$*],
    [*$q$*],
    [*Tier*],
  ),
  [FEP medicated vs FEP unmedicated], [3D `entropy_rate`], [-0.769], [0.0822], [0.7106], [`p<0.1`],
  [FEP unmedicated vs Healthy], [9D `entropy_rate`], [+0.519], [0.1299], [0.6772], [`ns`],
  [FEP unmedicated vs Healthy], [3D `entropy_rate`], [+0.591], [0.3316], [0.5968], [`ns`],
  [FEP unmedicated vs Healthy], [9D transition sparsity], [-0.881], [0.1505], [0.6772], [`ns`],
  [FEP medicated vs Healthy], [3D `noetic_action_potential`], [-0.377], [0.1994], [0.9071], [`ns`],
)

#v(4pt)
#text(size: 9pt, style: "italic")[
  Interpretation: the `ds003947` results are directionally consistent with `ds003944` but power-limited. The `entropy_rate` trend is the clearest directional signal: medicated FEP has more predictable state-space transitions than unmedicated FEP, paralleling the `ds003944` finding that trajectory action is elevated in unmedicated FEP.
]

== Cross-dataset synthesis

The two cohorts converge on a consistent directional theme despite neither producing a clean corrected replication. Across both datasets:

1. Unmedicated FEP tends toward higher trajectory action and entropy rate than healthy controls.
2. Medicated FEP tends toward lower trajectory action and entropy rate than unmedicated FEP.
3. Medicated FEP shows only weak trajectory effects relative to healthy controls, despite its clear static `m`-axis displacement in the companion study.

This pattern is the reverse of what the companion static-geometry paper found at the corrected level: there, medicated FEP was the group with the clearest separation from healthy controls, driven by static `m`-coordinate displacement. Here, unmedicated FEP is the group with the clearest trajectory-level signal. The two results are therefore not simply redundant, and they are not in contradiction. They expose two different geometrical signatures of medication-stratified psychosis: a static attractor shift in medicated FEP, and a dynamic grammar elevation in unmedicated FEP.

The jerk component contributes to the noetic action signal in ds003944 but is not the dominant term. The primary driver of the `noetic_action` elevation is a combination of kinetic and potential terms. The `noetic_action_jerk` component is directionally lower in medicated vs unmedicated FEP ($d = -0.351$), consistent with the prediction that antipsychotics dampen abrupt state-space redirections, but this remains uncorrected.

= Discussion

This exploratory study supports three bounded conclusions.

First, trajectory-level NDT metrics expose a medication-sensitive psychosis signature that is complementary to the static coordinate separation reported in the companion study. The key result — elevated `noetic_action` in unmedicated FEP in `ds003944` ($d = 0.774$, $p = 0.006$, $q = 0.052$) — is the largest effect in this dataset and represents a different layer of information than the companion paper's corrected `m_mean` displacement. The fact that the trajectory signal is strongest in the group whose static signal is weakest (unmedicated FEP) suggests that the two layers are genuinely complementary rather than redundant.

Second, the double dissociation supports a qualitative model of antipsychotic action on neural geometry. Antipsychotics appear to normalise the dynamic grammar of state-space traversal — reducing noetic action, entropy rate, and jerk toward healthy levels — while introducing a residual positional shift in the `m`-axis coordinate. This is broadly consistent with the clinical picture of antipsychotic drugs: they dampen the episodic, aberrant-salience-driven disruptions of attention and neural activity @kapur2003psychosis while not restoring the full resting neurophysiology of a never-ill brain @ozaki2021qEEG_antipsychotics. The present geometry provides a low-dimensional description of that same asymmetry. Whether the jerk component specifically links to aberrant salience dynamics remains speculative; the jerk result is directionally consistent but uncorrected.

Third, the results are explicitly exploratory and should be read with clear caveats. The primary `noetic_action` result in `ds003944` ($q = 0.052$) is a near-miss, not a corrected finding. The `ds003947` effects are directional tendencies with small unmedicated $n$, not inferential results. The jerk decomposition is a hypothesis-generating observation, not a tested mechanism. The use of subject-anchored coordinates means that trajectory metrics here reflect within-subject dynamic structure; they are not directly comparable to the between-subject positional contrasts in the companion paper. Finally, noetic action and entropy rate are sensitive to the codebook, the time-window resolution, and the choice of potential function; none of these have been exhaustively validated for resting EEG data.

The most important next step is a time-shuffled null test (permuting window order within subject) to verify that the trajectory metrics depend on real temporal structure rather than only on the marginal distribution of coordinate values. This would validate the temporal specificity of the noetic action signal. A second priority is residualising `noetic_action_potential` against static subject-level MNPS coordinate means, to confirm that the potential contribution is not simply a restatement of the companion paper's static positional effect.

= Supplement overview

Extended material has been moved to keep the claim hierarchy explicit:

1. `S1` gives the expanded methods, including the subject-anchored coordinate contract and repertoire metric derivation.
2. `S2` collects the full contrast tables for both datasets and both dimensions.
3. `S3` collects QC notes including the temporal shuffled-null recommendation and dataset coverage.
4. `S4` gives a cautious clinician-facing interpretation.

#bibliography("psychosis.bib", style: "apa")
