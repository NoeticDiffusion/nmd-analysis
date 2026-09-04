// Noetic Diffusion Theory — meso-to-macro theory manuscript.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Noetic Diffusion Theory: A Meso-to-Macro Geometry of Neural State Reconstruction",
  short-title: "Noetic Diffusion Theory from meso to macro",
  subtitle: [A bottom-up, rhythmically gated framework with explicit measurement boundaries],
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "consciousness",
    "neural dynamics",
    "cross-scale coupling",
    "rhythmic variance control",
    "neural manifolds",
    "metabolic constraint",
  ),
  article-type: "Research Article — theoretical framework",
  abstract: [
    Noetic Diffusion Theory (NDT) proposes that neural-state reconstruction can be studied as rhythmically gated stochastic flow on a measured state-space chart. This first meso-to-macro version separates a proposed mechanism from the strength of evidence available for observing it. At the mesoscopic scale, thalamocortical gating and population activity provide candidate implementation and measurement layers; at the macroscopic scale, EEG/MEG/fMRI features define a Meta--Noetic Phase Space (MNPS) chart. A companion Neuropixels--surface-EEG analysis establishes bounded meso--macro associations under temporal and statistical nulls, but its EEG-only local-linear chart does not support a Jacobian or reachability inference. A truth-known simulator further distinguishes association, mechanism discrimination, latent-order preservation, and dynamical-operator identification. We use these boundaries to formulate a minimal rhythmic diffusion model, an embodied anchoring extension, and a slow metabolic-adequacy gate. The framework predicts observable rhythm-locked changes in state-space geometry while rejecting the inference that any single coordinate, rhythm, or cross-scale correlation measures consciousness. The proposed equations and biological mappings remain hypotheses to be tested against simpler alternatives.
  ],
  author-summary: [
    NDT describes a possible way that neural rhythms could alternate between exploration and stabilisation. This version begins with local population signals and their measured relationship to EEG before introducing whole-brain geometry. It distinguishes what cross-scale measurements show from stronger claims about mechanisms, latent states, or consciousness, and treats metabolic and bodily signals as constraints on the proposed dynamics rather than as consciousness meters.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Writing, and Editing.],
  funding-info: [Funding information will be inserted at submission.],
  data-availability: [This theoretical manuscript will link to the public datasets, simulator code, analysis contracts, and permanent archives supporting each bounded empirical claim.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")

= Scope and epistemic status <sec:scope>

This article advances NDT as a theory and measurement framework, not as a
completed theory of consciousness. The central empirical object is a measured
neural trajectory, whereas the proposed mechanism concerns an unobserved,
multiscale process generating that trajectory. The distinction is consequential:
an MNPS coordinate is not a consciousness measurement; a cross-scale association
does not identify a mechanism; and the metabolic equations below are proposals
for testing, not established physiology.

We use four evidence labels throughout. *Established external results* are
findings supported outside this programme. *Companion empirical or methodological
results* are auditable analyses that constrain the framework but are not
independent validation of it. *Plausible interpretations* are readings compatible
with present evidence. *Speculative extensions* include the precise MNDM, TRN,
and metabolic-gating mechanisms. This structure prevents an attractive analogy
from being promoted into a biological result.

= Introduction <sec:intro>

Neural dynamics are measured at nested but non-equivalent scales. Local spiking
and field potentials, surface electrophysiology, imaging signals, bodily
physiology, and subjective report cannot be assumed to be interchangeable
descriptions of one state. A theory that begins with a low-dimensional EEG or
fMRI chart must therefore explain what supports that chart, what it omits, and
what inferential burden its downstream geometry can bear.

This version builds the argument upward. It begins with metabolic availability
and candidate mesoscopic variance gating, then asks whether population-scale
features can be bridged to surface EEG under strict null tests. Only after these
constraints are in place does it introduce MNDM, RVC, MNPS, and embodied
anchoring. The intended contribution is not that this chain has been demonstrated
end-to-end. Rather, it is a concrete route by which each link can be tested,
revised, or rejected.

#netn-box(title: [Core question])[
  Which mesoscopic mechanisms and measurement conditions could support a
  falsifiable meso-to-macro account of rhythmically gated neural-state
  reconstruction, without mistaking observable association for a unique latent
  geometry or a theory of consciousness?
]

= Scale ladder and observability ruler <sec:ladder>

== From latent process to measured chart

Let $X_t$ denote a latent neural state, $Y_t$ a measurement, $Psi$ a
modality-specific observation map, and $C$ a feature/chart construction:

#math.equation(
  $ Y_t = g(X_t) + epsilon_t, quad z_t = B(X_t) = C(Psi(X_t)) $
) <eq:observation-map>

Equation @eq:observation-map separates the target of inference from its
measurement. The chart coordinate $z_t$ is an operational summary of the
measurement, not $X_t$ itself. Different modalities, preprocessing decisions,
and feature definitions can yield different charts, and their uncertainty
propagates into every later estimate of flow, Jacobian, or reachability.

#figure(
  image("figures/conceptual/fig1_scale_ladder.svg", width: 96%),
  caption: [
    Conceptual scale ladder. Metabolic adequacy and candidate mesoscopic
    mechanisms constrain an observable meso--macro bridge; MNPS and derived
    dynamics are downstream measurement objects. Arrows denote proposed
    dependencies, not established causal pathways.
  ],
) <fig:scale-ladder>

== Four levels of measurement recoverability

The companion truth-known simulator motivates a hierarchy that governs the
claim strength throughout this article:

1. *Association:* an observable covaries with a mesoscopic or latent quantity.
2. *Mechanism discrimination:* observations separate alternatives with matched
   task outputs.
3. *Latent-order preservation:* an observable ordering tracks a predefined
   ordering of a latent summary.
4. *Dynamical-operator identification:* a chart supports a nontrivial,
   response-generating local operator.

These levels are not a general nonlinear-observability theorem. They are an
operational claim ladder. In particular, success at association says nothing
about whether an observable preserves latent ordering or supports a local
operator. Jacobian and reachability claims therefore require Level 4 together
with residual-quality diagnostics, adequate local sampling, and robustness
checks; they are not justified by an appealing embedding or a correlation.

#figure(
  image("figures/conceptual/fig2_recoverability_ladder.svg", width: 94%),
  caption: [
    Conceptual observation and recoverability ladder. Each upward step adds a
    stronger requirement. A meso--macro correlation establishes association,
    not mechanism discrimination, latent recovery, or local-operator
    identification.
  ],
) <fig:recoverability-ladder>

= Metabolic constraint on embodied dynamics <sec:metabolic>

== Slow metabolic boundary condition

Fast cardiac, respiratory, and heartbeat-evoked signals can time embodied
conditioning. Metabolic availability changes more slowly and is instead proposed
as a boundary condition on which costly neural trajectories remain available.
It is therefore not treated as another rhythmic anchor comparable with cardiac
or respiratory phase, and it is not a direct variable of conscious level. The
minimal formulation below is a speculative future extension. Its role is to
prevent the framework from mistaking low-complexity physiological failure for
successful state reconstruction.

For a minimal extension, let $z_t^"met" = (g_t^p, dot(g)_t^p, a_t^"hypo")$,
where $g_t^p$ is plasma/interstitial glucose, $dot(g)_t^p$ its rate of change,
and $a_t^"hypo"$ a represented metabolic-warning signal. A fuller state, including
latent cerebral availability, insulin, ketones, and crisis load, belongs in
Supplement S1.

#math.equation(
  $
    H_"met"(z_t^"met")
    = eta_L op("softplus")((theta_L - g_t^b) / s_L)^2
      + eta_"dot g" abs(dot(g)_t^p)
      + eta_o o_t
  $
) <eq:metabolic-strain>

#math.equation(
  $ q_t^"met" = exp(- H_"met"(z_t^"met")) $
) <eq:metabolic-adequacy>

$q_t^"met"$ is a proposed metabolic-adequacy gate, not a scalar consciousness
score and not an identified variable in the current measurement contract. A
future model could test whether it conditions the potential, effective geometry,
or efficacy of rhythmic control. This article makes no commitment to a specific
geometric mixing rule until such a model can be distinguished from simpler
metabolic-covariate, arousal, and autonomic alternatives.

The low-glucose penalty is intentionally asymmetric: ordinary hyperglycaemia is
not the mirror image of acute substrate shortage, whereas hyperosmolar or
acidotic crises require additional variables. If adequacy declines, the model
predicts a possible reduction in the dynamics that can be stabilised, but this
is a hypothesis rather than a demonstrated change in MNPS geometry or
reachability.

== Metabolic version of the hypersynchrony paradox

In hypoglycaemia, slow rhythmic power can increase while complexity, connectivity,
and cognition deteriorate. Therefore low entropy or strong slow rhythm cannot
alone be read as successful denoising. This is the metabolic analogue of the
seizure/hypersynchrony boundary: functional reconstruction requires capacity and
flexible accessibility, not order alone.

#figure(
  image("figures/conceptual/fig3_rvc_metabolic_gate.svg", width: 92%),
  caption: [
    Conceptual rhythmic variance-control cycle. The observed rhythm proxy is
    proposed, in a future metabolic-constraint extension, to be converted to
    effective control only when metabolic adequacy is sufficient. High rhythmic
    structure under low adequacy is therefore not interpreted as successful
    denoising.
  ],
) <fig:rvc-metabolic-gate>

= Meso layer: variance gating and population observables <sec:meso>

== Candidate variance-gate mechanism

NDT proposes that thalamocortical gating, with the thalamic reticular nucleus
(TRN) as a candidate executor, controls the timing and depth of effective
variance reduction. The mapping is a phenomenological ansatz, not a directly
identified biophysical law. In this division of labour, cortical and
subcortical systems supply context and candidate descent direction, whereas
TRN-mediated inhibition is proposed to alter the timing and depth of a variance
clamp:

#math.equation(
  $
    sigma(t)
    = sigma_"min"
      + (sigma_0 - sigma_"min") exp(- kappa g_"TRN"(t))
  $
) <eq:trn-variance>

$g_"TRN"$ and $kappa$ are not directly recovered from standard scalp EEG.
Consequently, Eq. @eq:trn-variance should be read as a model component to be
tested by convergent measurement and perturbation, not as a scalar derivable
from the macro chart. Calibration, cellular assumptions, and alternative
mechanisms are assigned to S1.

== Operational mesoscopic observables

The DANDI 000458 companion analysis operationalises a mesoscopic layer by using
a post-artifact LFP-variance proxy, quality-filtered spike rate, and
population dimensionality (participation ratio). These are observables, not
synonyms for the latent variables in Eq. @eq:trn-variance.

The important point is methodological rather than taxonomic. Valid channels,
trial windows, unit quality thresholds, and subject-level aggregation belong to
the feature contract. LFP variance and spike rate are candidate population-level
measurements; they do not establish a unique mesoscale state variable. The
companion association evidence is therefore a bridge constraint for NDT, not
evidence that its potential, metric, or biological implementation has been
identified.

= Meso-to-macro measurement bridge <sec:bridge>

== Bounded cross-scale test

For a mesoscopic feature $u$ and macro feature $v$, the bridge begins with a
within-session association. Session estimates are aggregated within subject so
that trials do not masquerade as independent participants, after which both
sign and temporal specificity are evaluated:

#math.equation(
  $
    rho_s = op("median")_i
      [op("mean")_(j in s_i)
        rho(u_(i j), v_(i j))]
  $
) <eq:bridge-effect>

The primary nulls are a subject-level sign-flip test and a circular
within-session time-shift test. A prespecified feature-pair family is corrected
with Benjamini--Hochberg FDR, while leave-one-subject-out and extraction
sensitivity analyses bound dependence on individual subjects and feature choices.

The companion mouse analysis found LFP-variance-proxy--EEG-variance and
spike-rate--EEG-spectral-entropy associations with median subject correlations
near $0.4$ under both null families. These are bounded association-level
findings. They neither identify directionality nor prove a common manifold,
TRN mechanism, or NDT process.

== Negative estimator-quality result

The same companion analysis found a median local-linear residual-variance
fraction of $0.856$ for its EEG-only chart. Its Jacobian and reachability
interpretation was therefore rejected. This is a required negative control for
the present framework: a visually plausible chart or a cross-scale correlation
is insufficient for Level-4 dynamical-operator inference. The failure is
scientifically useful because it prevents the bridge result from being used as a
shortcut to a macro-dynamical claim.

= Meta--Noetic Diffusion Model <sec:mndm>

== Minimal formulation

The minimal MNDM represents state evolution as diffusion on a potential whose
variance is rhythmically controlled:

#math.equation(
  $
    d X_t = - nabla F_"min"(X_t) d t + sigma(t) d W_t,
    quad
    F_"min"(X) = e(X) - m(X),
    quad
    sigma(t) = sigma_"min" + sigma_0 (1 - r(t))
  $
) <eq:min-mndm>

$e$ denotes an entropy/complexity-pressure family and $m$ a mobility or
rhythmic-coordination family. $r(t) in [0,1]$ is a control proxy: high values
reduce proposed effective variance but do not by themselves prove improved
function. Minimal MNDM is the first falsifiable comparator, not a complete
classifier of pathological or conscious regimes. Its central empirical question
is whether event-locked scheduling improves prediction over stationary-noise and
smooth-control alternatives.

== Extended geometry and meta-regulation

#math.equation(
  $
    d X_t = - bold(G)_t(X_t) nabla Phi(X_t, t) d t + sigma(t) d W_t,
    quad
    Phi(X,t) = alpha(t)e(X) - beta(t)m(X) + gamma(t)d(X)
      - delta(t) phi_"meta"(t)
  $
) <eq:extended-mndm>

$bold(G)_t$ is a proposed effective geometry or attention tensor and must not be
identified with a measured covariance or connectivity matrix. The $d(X)$ term
penalises deviation from a viable integration--segregation corridor, avoiding
the inference that maximum synchrony is necessarily desirable. The extended
model is warranted only if it improves held-out prediction beyond the minimal
model and its structured nulls; otherwise its additional flexibility is a
liability rather than an advance.

= Rhythmic Variance Control <sec:rvc>

== Observable rhythm proxy

#math.equation(
  $
    hat(r)(t) = op("sigm")(
      w_"PAC" "PAC"_(theta -> gamma)(t)
      + w_"SO" A_"SO"(t) "Prec"_("SO-spindle")(t)
      + w_phi Phi_"coh"(t) + b
    )
  $
) <eq:rvc-proxy>

$hat(r)(t)$ is an observable proxy rather than the latent control schedule.
Wake, NREM, and REM can require different observable constructions and
timescales. This flexibility must be constrained before analysis: event-locked
schedules must be compared against smooth-rhythm and rhythm-free null models,
not re-fitted post hoc to the target outcome.

== Sleep as a two-timescale curriculum

Within a sleep cycle, the model predicts that NREM tightens variance and
centralises trajectories, whereas REM loosens variance and permits exploration.
Across cycles, it predicts a declining exploration--consolidation amplitude as
the trajectory approaches a refined regime. These are model predictions that
require longitudinal sleep testing; they are not results of the present theory
article.

= Macro measurement layer: MNPS <sec:mnps>

== Three-coordinate chart

The macro chart is the measured vector

#math.equation(
  $ x_t^"MNPS" = [m(t), d(t), e(t)]^T $
) <eq:mnps-chart>

where $e$ indexes entropy/complexity features, $m$ indexes rhythmic coordination,
and $d$ indexes deviation from a metastability or integration--segregation
corridor. A stratified 9D chart and release-fixed projection are optional
extensions, not prerequisites for the 3D model.

#math.equation(
  $
    e(t) = - sum_f P_f(t) log P_f(t),
    quad
    m(t) = w_"PAC" "PAC"(t) + w_"PLV" overline("PLV")(t)
      + w_"pow" P_theta(t),
    quad
    d(t) = abs(Q(t) - Q^*)
  $
) <eq:mnps-features>

Each coordinate is a feature family, so an implementation defines a chart rather
than a unique ontology. Feature variants require a prespecified multiverse and
chart-stability checks. Algorithmic detail, preprocessing, and the stratified
9D extension are assigned to S1 so that the main text keeps the distinction
between theory, feature contract, and empirical estimate visible.

== Local flow, Jacobian, and reachability boundary

#math.equation(
  $
    dot(x) approx A(x - bar(x)) + b,
    quad
    hat(J) = A,
    quad
    Sigma_t^(h + 1) = A_t Sigma_t^(h) A_t^T + Q_t
  $
) <eq:local-operator>

$hat(J)$ and short-horizon reachability are conditional local estimators. They
require Level-4 recoverability, residual-quality diagnostics, sufficient local
sampling, and sensitivity analysis. Cone size is not occupancy, entropy,
controllability, or consciousness; it is only a model-based description of
short-horizon accessible variation under stated assumptions.

= Fast embodied anchoring <sec:eap>

== Self-prior and phase-resolved modulation

The fast EAP extension conditions the potential on cardiac phase, respiratory
phase, and heartbeat-evoked cortical response:

#math.equation(
  $
    Phi_"EAP"(X,t)
    = Phi(X,t) + lambda_"self"(t) F_"self"(X, s_t^"fast"),
    quad
    s_t^"fast" = (phi_"cardiac"(t), phi_"resp"(t), A_"HEP"(t))
  $
) <eq:eap-potential>

For completeness, one possible *future* coupling of the slow metabolic
constraint to the fast schedule is

#math.equation(
  $
    r_"eff"(t)
    = q_t^"met" hat(r)(t)
      [1 + gamma_"entrain"
        cos(phi_"cardiac" - phi_theta)
        cos(phi_"resp" - phi_alpha)]
  $
) <eq:eap-effective-rvc>

Equation @eq:eap-effective-rvc is not part of the current core model and is not
estimated in the present measurement contract. It states a testable hypothesis:
fast variables condition timing and context, while metabolic adequacy may
constrain whether rhythmic coordination is functionally effective. Any future
implementation must bound $r_"eff"$ and compare it against metabolic-covariate,
autonomic-arousal, movement, and generic-state alternatives. The full phase
landscape and a self-prior index belong in S1/S5 until they have a stable
measurement contract.

= Relation to current theories of consciousness <sec:comparisons>

== Different theories answer different questions

Theories of consciousness do not all explain the same target. Some propose a
constituent of experience, some specify access or representational conditions,
and others describe state transitions or their measurement. NDT is situated in
the latter category: a rhythm-sensitive neural-dynamics and measurement
framework. It is not, in its present form, an identity theory of consciousness
or a model of report, meta-representation, or global broadcast. This layered
reading is compatible with integrative multiscale accounts that treat leading
theories as partly complementary rather than simple rivals @storm2024integrative.

The comparison must distinguish conscious level, momentary content, access and
report, meta-awareness, bodily selfhood, and dynamical capacity. A state-level
discriminator need not identify experience at a moment, and NDT cannot select a
philosophical theory of experience merely by supplying a measurement surface for
other theories.

#figure(
  image("figures/conceptual/fig4_cross_theory_map.svg", width: 96%),
  caption: [
    Conceptual explanatory-layer map. NDT is placed with state-space dynamics
    and measurement, where it may interface with but does not replace theories
    of inference, recurrence, access, or meta-representation.
  ],
) <fig:cross-theory-map>

== Comparison map and bridge boundaries

#figure(
  kind: table,
  clean-table(
    columns: (1.25fr, 1.9fr, 1.15fr, 2.0fr),
    align: (left, left, left, left),
    inset: 3pt,
    table.header(
      [*Framework*],
      [*Primary explanatory target*],
      [*Bridge to NDT*],
      [*Non-equivalence / boundary*],
    ),
    [Predictive Processing / FEP],
      [Inference, content formation, and precision],
      [Functional analogy: landscape descent and precision-like scheduling],
      [MNDM is not a hierarchical generative model with explicit priors or prediction errors],
    [Integrated Information Theory],
      [Intrinsic integrated causal structure],
      [No direct analogue],
      [NDT has no scalar equivalent to $Phi$ and makes no identity claim],
    [Global Neuronal Workspace],
      [Global access and broadcast],
      [Possible state-transition readout],
      [MNPS stability is not ignition, competition, or broadcast],
    [Higher-Order Theories / Attention Schema Theory],
      [Meta-representation and awareness attribution],
      [Possible future inputs from attention or confidence features],
      [NDT does not model representation of a representation or an attention schema],
    [Recurrent Processing Theory],
      [Local sensory recurrence],
      [Flow rotation can be compatible with recurrence],
      [Chart-level rotation does not establish anatomical feedback or sufficiency],
    [Dynamical landscapes / metastability],
      [Attractors, transitions, and coordination regime],
      [Closest family: partial mechanistic relation],
      [NDT adds the proposed rhythmic variance schedule and an explicit measurement contract],
    [Network Control Theory],
      [Structural constraints on transition costs],
      [Partial mathematical bridge through local reachability],
      [NDT lacks a full control-input model, control matrix, and control-energy account],
  ),
  caption: [
    Cross-theory map. Bridge labels state only the strength of a proposed
    relation, not an equivalence. NDT is closest to dynamical landscape and
    metastability accounts, while interfacing more loosely with theories of
    access, recurrence, and self-modeling.
  ],
) <tab:theory-bridges>

The adjacent frameworks are surveyed in their own terms: predictive-processing
accounts model inference and precision @friston2010free; IIT proposes an
intrinsic causal-structure account @tononi2016integrated; GNWT models global
availability @dehaene2011experimental; HOT models higher-order representation
@brown2019understanding; AST models attention representation @webb2015attention;
and RPT emphasises recurrent sensory processing @lamme2006towards. Dynamical
landscapes, metastability, and network-control approaches supply the closest
formal neighbours for NDT @deco2017dynamics @tognoli2014metastable
@gu2015controllability.

== NDT discriminant and adversarial comparison

The claim that brain states have geometry is not distinctive to NDT. Its
specific, falsifiable addition is the proposed *rhythmic schedule*: variability
should change at predicted events or phases in a way that explains trajectories
beyond stationary dynamics, spectral power, generic criticality, and
unconstrained state-space models. This claim requires four jointly specified
tests:

1. *Event specificity:* changes occur at the predicted event or phase.
2. *Schedule specificity:* an event-locked variance model outperforms
   stationary-noise and smooth-control alternatives.
3. *Incremental value:* the schedule predicts future trajectory change beyond
   power, event density, autocorrelation, complexity, and criticality.
4. *Null specificity:* effects fail under phase-shuffle, time-shift,
   wrong-event, wrong-subject, and power-matched controls.

The appropriate next comparison is adversarial rather than rhetorical. A
preregistered multimodal altered-state design should separate physiological
state, responsiveness, access, and reported experience; then ask whether NDT's
event-locked schedule adds prediction beyond theory-relevant alternatives.
The recent adversarial IIT--GNWT collaboration illustrates the standard: a
theory gains scientific force by exposing a specified prediction to possible
failure @cogitate2025adversarial.

= Predictions and falsification <sec:predictions>

== Tier-1: measurement and rhythmic-dynamics tests

The first prediction concerns the bridge itself. Meso--macro feature
associations should survive prespecified temporal and statistical nulls,
including time shifts that preserve each signal's marginal structure. Even when
they do, they remain Level-1 results unless an experiment demonstrates
mechanism discrimination or stronger recoverability.

The second prediction is the core rhythmic claim. Event-locked changes in
entropy and trajectory geometry should outperform matched smooth-precision and
rhythm-free models in held-out prediction. The relevant outcome is not a
descriptive difference between sleep stages, but incremental prediction of
future trajectory change after accounting for power, event density, and
autocorrelation.

The third prediction concerns local dynamics. A chart that supports a
Jacobian or reachability interpretation must pass residual-quality,
perturbation, and response-generating-operator checks. Failure of any one of
these checks limits the result to lower-level association or descriptive
geometry.

== Tier-2: embodied and metabolic tests

The metabolic extension predicts that hypoglycaemic strain can increase
low-frequency rhythmic structure while reducing complexity, effective
dimensionality, or reachability. It further predicts that represented metabolic
warning and metabolic adequacy can dissociate, particularly where awareness of
hypoglycaemia is impaired. Recovery need not retrace induction because
metabolic, autonomic, and neural processes can have different time constants.
These are Tier-2 hypotheses pending comparison with glucose-as-covariate,
autonomic-arousal, and potential-only alternatives.

== Falsification criteria

NDT's rhythmic mechanism is narrowed or rejected if no reproducible
event-locked advantage remains after smooth and rhythm-free nulls; if
cross-scale associations fail temporal specificity or extraction sensitivity;
if local operators fail residual-quality, response-block, or perturbation
validation; or if a simpler covariate, arousal, or autonomic model explains the
effects equally well or better. These outcomes would not imply that neural
geometry is uninformative; they would reject the specific rhythmic-gating
interpretation.

= Discussion <sec:discussion>

== Contribution

The contribution is a scale-aware research programme rather than a completed
theory of consciousness. The meso--macro bridge constrains what macro
measurements may be asked to establish, while the recoverability ladder prevents
association, latent ordering, and local dynamics from being collapsed into one
claim. The framework's practical value lies in making its dependencies
inspectable: each mechanism, proxy, and derived metric carries a distinct
failure condition.

== Limitations and next tests

No single dataset currently bridges metabolic state, TRN activity, mesoscopic
population dynamics, macro recordings, and first-person report. DANDI 000458
is a stimulation-aligned mouse measurement bridge, not a consciousness
experiment. The metabolic equations, TRN mapping, and EAP coupling remain
speculative until dedicated studies compare them with simpler alternatives.
The next tests should be preregistered cross-scale replications, multimodal
estimator-quality validation, controlled metabolic EEG studies, and
perturbational rhythm experiments that separate state, access, responsiveness,
and reported experience.

== Conclusion

NDT is most defensible as a falsifiable proposal about rhythmically gated neural
state dynamics measured through imperfect, scale-specific charts. The proposed
meso-to-macro chain makes its dependencies explicit: metabolic adequacy and
population mechanisms may constrain observable rhythms; cross-scale association
may justify a measurement bridge; and only validated local dynamics can justify
stronger geometry and reachability claims. This is a narrower but more testable
contribution than claiming that a particular neural coordinate constitutes
consciousness.

= Supplement allocation

- *S1 Supplementary Methods:* full metabolic state, TRN calibration,
  preprocessing/feature contracts, MNPS algorithms, and estimator diagnostics.
- *S2 Supplementary Data:* companion-analysis tables, parameter ranges, and
  provenance mappings.
- *S3 Supplementary QC:* temporal nulls, feature multiverse, residual-quality,
  perturbation, and leave-one-out checks.
- *S4 Supplementary Clinical:* bounded clinical interpretation; no biomarker or
  individual diagnostic claim.
- *S5 Glossary:* MNDM, RVC, MNPS, observability levels, metabolic adequacy, and
  reachability.
- *S6 Changelog:* theory-version and claim-ledger changes.

= Acknowledgements

This manuscript builds on companion meso--macro and truth-known-simulator
analyses, and on the metabolic-anchoring research plan. Their results are used
as explicit constraints on claim strength, not as evidence that the complete
NDT mechanism has been validated.

#bibliography("references.bib", style: "apa")
