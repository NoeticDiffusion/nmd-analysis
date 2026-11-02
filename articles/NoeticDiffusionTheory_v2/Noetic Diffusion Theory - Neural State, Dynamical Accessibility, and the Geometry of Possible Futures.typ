// Noetic Diffusion Theory v2 — theoretical framework.
// Main-text prose complete through discussion, limitations, and conclusion.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Noetic Diffusion Theory: Neural State, Dynamical Accessibility, and the Geometry of Possible Futures",
  short-title: "NDT: state, accessibility, and possible futures",
  subtitle: [A multiscale framework for rhythmically and contextually controlled neural dynamics],
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "neural dynamics",
    "dynamical accessibility",
    "state-space geometry",
    "stochastic diffusion",
    "consciousness",
    "measurement contracts",
  ),
  article-type: "Hypothesis and Theory — presubmission draft",
  abstract: [
    Noetic Diffusion Theory (NDT) proposes that neural states relevant to cognition and consciousness are characterized not only by their current configuration, but also by the structured distribution of futures available from that configuration. NDT formalizes this property as dynamical accessibility: a control-dependent stochastic law governing how neural activity tends to move, how fluctuations spread, which nearby states remain probable, which longer-term destinations are favoured, and how the system responds to perturbation. Deterministic drift, diffusion geometry, local stability and reactivity, short-horizon predictive spread, basin commitment, and finite-amplitude resilience therefore describe non-equivalent aspects of the same evolving system. These properties may dissociate even when present measured states are similar, because rhythm, context, history, thalamocortical interactions, bodily state, and slower physiological constraints can reshape future transition structure without simply relocating the system in state space. NDT accordingly predicts that reduced state coordinates need not be sufficient statistics for future neural dynamics, and that matched present states can exhibit different future laws under different control conditions. Measurement charts are treated as operational interfaces to latent dynamics rather than as the theory itself. NDT is intended as a falsifiable framework for neural organization across wakefulness, sleep, altered states and pathology; it does not define a scalar of consciousness or explain why neural activity is accompanied by experience. Its central question is therefore not only where the brain is, but what it can still become.
  ],
  author-summary: [
    Noetic Diffusion Theory is organized around a simple idea: a reduced chart of neural state is not, in general, a sufficient statistic for nearby futures. What matters scientifically is the control-dependent transition law --- which directions the system tends to move, how fluctuations spread, which destinations remain open, and what processes change those possibilities. We keep a measurable state-space chart, but we treat it as an observation map rather than as the theory itself.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Writing, and Editing.],
  funding-info: [No dedicated external grant supported this work.],
  data-availability: [Companion analyses cited in the empirical section are archived on Zenodo. Source datasets used there are cited with the corresponding anchors: ANPHY and BOAS/ds005555 (spindles), I-CARE (coma), and DANDI 000458 (meso--macro). This theoretical article does not release a new recording.],
  competing-interests: [The author declares no competing interests.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")
#set math.equation(supplement: none)

= Scope and epistemic status <sec:scope>

This article advances Noetic Diffusion Theory as a framework for neural dynamical
organization associated with conscious states and cognition, not as a completed
theory of why neural activity is accompanied by experience
@langell2025ndt @storm2024integrative. The scientifically relevant object is a
neural state's *dynamical accessibility*: the geometry of a control-dependent
law over possible futures, not merely a set of reachable points. A reduced
chart location is not assumed to be a sufficient statistic for that law.

Selected mathematical components of NDT have been formalized and kernel-checked
in Lean 4 under explicit finite-dimensional and nondegeneracy assumptions; the
formalization supports the theory's architecture but does not validate empirical
accessibility or biological mechanism (Supplementary Note S7).

That object is distinct from several things with which it is easily confused.
NDT is not a consciousness scalar. It is not identical to Meta--Noetic Phase
Space, which is a measurement chart. It is not identical to
NeuralManifoldDynamics, which is a versioned empirical implementation of
selected charts and estimators. It does not claim that one thalamic circuit,
one rhythm, or one diffusion parameter uniquely implements consciousness, nor
that every quantity named below currently has a validated empirical estimator.

== Evidence classes

Every major statement in this manuscript is intended to be readable as one of
five classes:

1. *Established external result* --- supported by peer-reviewed literature or
   other independent evidence outside the present theory.
2. *Internal validated result* --- supported by auditable companion code, tests,
   or frozen simulation/empirical contracts.
3. *Plausible interpretation* --- compatible with present evidence but not
   directly demonstrated.
4. *Speculative extension* --- a hypothesis, analogy, or forward model.
5. *Rejected or method-limited path* --- tested and not supported under the
   stated assumptions.

Evidence class and inferential claim class are orthogonal. An internally
validated result may remain only a claim-class-1 association, while a speculative
mechanism can concern a claim-class-4 operator question without being empirically
established.

#netn-box(title: [Promotion rule])[
  Success at one inferential level does not authorize a stronger claim at
  another. Correlation is not mechanism. Chart separation is not latent-state
  identification. Preserved latent ordering is not recovery of a local
  dynamical operator. Truth-known estimator recovery is not empirical
  biological validation.
]

The remainder of the article is organized by four layers: state geometry,
local dynamical geometry, geometry of possible futures, and control of
accessibility. MNPS belongs primarily to the first layer. Local Jacobians,
diffusion tensors, reachability, destination geometry, and finite-amplitude
questions belong to the latter three.

= Introduction <sec:intro>

Neural population activity is increasingly studied as trajectories through
lower-dimensional state spaces rather than as collections of independently
tuned variables @cunningham2014dimensionality @vyas2020computation
@breakspear2017dynamic. This dynamical perspective has revealed structured
population trajectories, metastable regimes, context-dependent recurrent
computations, and state repertoires associated with cognition and
consciousness @hancock2025metastability @hudson2014recovery
@barttfeld2015signature. Yet a coordinate or manifold description does not by
itself identify the law governing future evolution: two systems occupying
similar measured states may differ in local stability, stochastic spread,
transition probability, destination structure, or response to perturbation
@duncker2021dynamics.

Noetic Diffusion Theory begins from this distinction. It proposes that the
scientifically relevant description of a neural regime includes not only its
present measured location but its *dynamical accessibility* --- the
structured, context-dependent distribution of futures available from that
state. Recovery from anesthesia can traverse a network of metastable activity
states rather than a monotonic return to wakefulness @hudson2014recovery, and
wakefulness has been associated with a richer repertoire of functional
configurations than anesthesia @barttfeld2015signature. That literature
establishes the neighbourhood. NDT proposes a more explicit decomposition of
the conditional future law.

NDT combines this accessibility perspective with a specific hypothesis about
state-dependent control. Its minimal formulation describes rhythmically
modulated stochastic dynamics on a structured landscape: Rhythmic Variance
Control modulates exploratory variance, while Meta--Noetic Phase Space
provides one operational chart in which state reconfiguration can be measured
@langell2025ndt. In the broader formulation developed here, this scalar
variance schedule is one special case of accessibility control. Context and
physiology may also alter deterministic flow, diffusion orientation,
landscape mobility, or transition gates. The resulting architecture can be
summarized as

#quote(block: true)[
  state $->$ local dynamical law $->$ possible futures $->$ state-dependent
  control of those futures.
]

The central claim is that the functional significance of a neural state
depends partly on this transition structure, not only on its present location.

#figure(
  image("figures/conceptual/fig1_ndt_architecture_v2.png", width: 96%),
  caption: [The NDT architecture. A measured point $x_t$ is surrounded by local dynamical objects (drift, diffusion, Jacobian deformation, reachability, committor basins, finite-amplitude perturbation). Candidate controls act from above on different parts of that neighbourhood. EEG and related recordings enter only through an observation map and a versioned chart. Dashed bands separate control, latent dynamics, and measurement.],
) <fig:architecture>

#netn-box(title: [One state, several questions])[
  Imagine two hikers standing at the same GPS coordinate. Their present
  location is identical. But one may stand on stable rock and the other on
  loose scree; wind may spread them in different directions; one route may
  lead toward one valley and another toward a second; and gates or weather
  may change which routes remain available.

  NDT treats these as different scientific questions. State location describes
  where the system is. Drift describes its local tendency. Diffusion
  describes stochastic spread. Local deformation describes what happens to
  small perturbations. Predictive spread describes the distribution of nearby
  futures. Committors describe destination bias. Finite-amplitude resilience
  asks whether a larger displacement changes the regime. Context and
  physiology may alter these futures without necessarily changing the present
  measured location. A longer conceptual companion is Supplementary Note S4.
]

#netn-box(title: [Core question])[
  How should neural-state organization associated with cognition and conscious
  regimes be characterized if location and complexity are insufficient --- that
  is, if the scientifically relevant object includes local flow, stochastic
  spread, reachable futures, basin commitment, and the processes that reshape
  them --- without mistaking a measurement chart for the latent process or a
  correlation for a dynamical operator?
]

== Three questions

The framework is organized around three questions that later sections develop
in turn.

*Where is the system?* This is the measurement-chart question. A low-dimensional
representation

$ x_t = [m_t, d_t, e_t]^top $ <eq:mnps3>

or a stratified nine-dimensional refinement, reports an operational location.
It answers a *state* question.

*What can happen from here?* This is the dynamical core of NDT. It includes deterministic
drift, stochastic diffusion, transient amplification, short-horizon
reachability, basin commitment, and finite-amplitude resilience. These objects
answer different dynamical questions and are not interchangeable summaries of
one another.

*What changes what can happen?* This is the control layer: rhythms, candidate
thalamic access, attention and context, history and replay, bodily state,
metabolic feasibility, and --- as an explicitly speculative micro substrate ---
slow structural accessibility at dendritic scale. Control may act on drift,
diffusion, effective geometry, landscape, or transition gates, not only on a
scalar noise amplitude.

== Noetic accessibility

*Noetic accessibility* is the geometry of a control-dependent transition law
over future neural states and destinations. "Noetic" is retained as the
historical name of the theory and marks its intended domain of
mind-relevant neural dynamics; no semantic, epistemic, or phenomenal property
is inferred from the coordinates themselves @langell2025ndt. It does not mean
conscious access in the global-workspace sense @dehaene2011experimental.
Stochastic short-horizon spread is not workspace ignition. Chart-level
accessibility is not a report. A conceptual companion to this architecture
is Supplementary Note S4.

= The NDT scale and inferential claim classes <sec:ladder>

== Latent process, observation, and chart

Let $X_t$ denote a latent neural dynamical state. Its exact dimensionality and
biological substrate need not be known for the theory to be well posed as a
modelling class. Measurements arise through an observation map

$ Y_t = g(X_t) + epsilon_t, $ <eq:observation>

where $Y_t$ may be spikes, local field potentials, EEG, MEG, fMRI, or
physiological channels, and $epsilon_t$ is observation noise. A subsequent
feature and chart construction produces an operational representation

$ Y_t -> z_t -> x_t. $ <eq:chart>

The chart $x_t$ is a versioned summary of the measurement. It is not
automatically the latent manifold. Different modalities, preprocessing
decisions, neighbourhood definitions, and projections yield different charts,
and their uncertainty is inherited by every later estimate of drift, Jacobian,
diffusion, or reachability.

== Four claim levels

Companion studies of observability and local-operator recovery under known
ground-truth dynamics
motivate four *inferential claim classes* that govern strength throughout this
article. The numbering reflects increasing typical inferential burden, not a
strict logical ordering:

1. *Association.* Does an observable covary with another measured or latent
   quantity under stated nulls?
2. *Mechanism discrimination.* Can observations distinguish alternative
   mechanisms that produce similar task-level outputs?
3. *Latent-order preservation.* Does the measured representation preserve a
   predefined ordering of a latent summary?
4. *Dynamical-operator identification.* Can the representation recover a local
   operator that correctly predicts responses to perturbation or short-horizon
   evolution?

These levels are not a general nonlinear-observability theorem. They are claim
classes, and they are one of the paper's methodological contributions: an
operational chart can succeed for one scientific question while failing for
another. Detectable population information, chart association, local-operator
recovery, and mechanism identification are not interchangeable. Related
recent work likewise emphasizes that latent state-space fits can capture
statistical associations without automatically identifying dynamics that
predict responses to perturbation @nejatbakhsh2025issm, and that
low-dimensional manifold descriptions do not by themselves identify the
dynamical rule on that manifold @duncker2021dynamics
@cunningham2014dimensionality. The order is not monotonic: a chart can
discriminate mechanisms while failing to preserve order or to identify an
operator.

A companion meso-to-macro analysis illustrates the distinction: cross-scale
associations survive declared nulls, whereas the corresponding EEG chart fails
its local-operator estimability criterion @langell2026_dandi000458
@dandi000458. A complementary IBL analysis similarly finds decodable
population information without a valid nominated chart-transition operator
(@sec:empirical) @langell2026_ibl2. Failure of a dynamical readout need not
imply absence of information in the underlying population.

#netn-box(title: [Consequence])[
  MNPS separations can be meaningful at claim classes 1--3. Claims about Jacobians,
  diffusion tensors, reachability, committors, or finite-amplitude resilience
  require stronger validity conditions and are not licensed when those conditions
  are not met.
]

#figure(
  image("figures/conceptual/fig2_inference_ladder_v2.png", width: 100%),
  caption: [Observation chain and inferential claim classes. Companion meso--macro contact (DANDI 000458) is a claim-class-1 constraint; the same EEG chart fails operator identification. An independent IBL readout shows the same lesson: population decoding can succeed while a nominated chart-transition operator does not (@sec:empirical). Recovery of $a$, $alpha$, and $omega$ on systems with known ground-truth dynamics remains envelope-limited.],
) <fig:ladder>

= Core NDT dynamics <sec:dynamics>

== Canonical stochastic formulation

The working process class of the present theory is a controlled diffusion, not a pure
gradient flow. Let $c_t$ denote a contextual or control state. The latent
dynamics are written

$ d X_t = b(X_t, t | c_t) d t + Sigma(X_t, t | c_t) d W_t, $ <eq:canonical>

where $b$ is local deterministic drift, $Sigma$ determines the amplitude and
orientation of stochastic forcing, and $W_t$ is Brownian motion. Equation
@eq:canonical is a modelling class, not a fitted neural SDE. The diffusion
formulation is an effective continuous-state approximation, not a claim that
neural fluctuations are literally Brownian or that all relevant neural
dynamics are Markovian. Hybrid, colored-noise, delayed, or non-Markov
formulations remain compatible extensions when required by the observation
scale.

== Dynamical accessibility as a transition law

If $X_t$ were a complete Markov state and the future control protocol were
known, the present latent location would determine the conditional future
law. That is not the empirical situation. The load-bearing claim of NDT is that a
*reduced measurement chart* $x_t$ is generally not a sufficient statistic for
the latent future law $K^X$.

The infinitesimal generator of Eq. @eq:canonical, acting on a test function
$f$, is

$ cal(L)_(t | c) f(xi) = b(xi, t | c) dot nabla f(xi) + frac(1, 2) op("tr")(a(xi, t | c) nabla^2 f(xi)), $ <eq:generator>

with $a = Sigma Sigma^top$ as in Eq. @eq:diffusion. Dummy $xi$ is a realization
of the *latent* state $X_t$, not of the measurement chart $x_t$. Because $c_t$
and history may vary over a horizon, the latent protocol-conditional law is

$ K_(t : t+h)^(X | gamma) (xi, A) = P(X_(t+h) in A | X_t = xi "and" gamma_([t : t+h])), $ <eq:kernel-latent>

where $gamma_([t, t+h])$ is the control/history protocol on that interval
(an instantaneous $c_t$, a path of $c$, or an augmented state
$Z_t = (X_t, C_t, H_t, dots)$ made approximately Markov). Experiments generally
estimate a chart-conditional approximation

$ K_(t : t+h)^(x | gamma) (x, B) = P(x_(t+h) in B | x_t = x "and" gamma_([t : t+h])). $ <eq:kernel-chart>

The latent process has a transition law $K^X$; measured work generally
recovers projections or chart-conditional laws $K^x$. NDT-C1 states that a
reduced chart coordinate need not be sufficient for $K^X$. When the text
writes $K^h$ without a superscript, the intended object is $K^x$ unless a
latent argument is explicit. Conditioning only
on a frozen snapshot of $c_t$ is a special case, not the general theory.
History dependence (HELS-A, P6) is a statement about $gamma$, not a
violation of Eq. @eq:canonical.

$K^h$ is the law of the *state at horizon $h$*, not the full path-space
measure on $X_([t, t+h])$ or $x_([t, t+h])$. NDT uses the family ${K^h}_(h > 0)$ as its primary
finite-horizon object. Path-dependent quantities such as committors are
defined under the corresponding stochastic process
@e2010transition @metzner2009transition @klus2018data. A reachable *set* discards probability:
two systems can share support and still differ in mass.

These named summaries are different *kinds* of object, not interchangeable
views of one endpoint distribution. The generator $cal(L)$ is the
infinitesimal law; $K^h$ is the finite-horizon law of the state at $t+h$;
committors $q$ are path/hitting functionals; FAR is an interventional
finite-amplitude response. Calling them all accessibility does not identify
them.

The following are non-equivalent functionals or descriptors of the controlled
process and its transition laws, not rival theories:

- $b$ --- infinitesimal conditional mean rate;
- $a$ --- infinitesimal conditional covariance rate;
- $J$ --- local drift derivative in a declared chart;
- stochastic short-horizon reachability --- finite-horizon predictive spread;
- committor $q$ --- destination (hitting) probability;
- attractors --- long-time organization;
- FAR --- response to a finite displacement.

Rhythm, thalamus, history, body, and metabolism are candidate changes of $K$
or $cal(L)$, not extra definitions of NDT. The generator, Itô corrections, and
estimator validity conditions are spelled out further in Supplementary Methods S1.

#netn-box(title: [Three core commitments])[
  *NDT-C1 (reduced-state insufficiency).* Current location in a reduced
  measurement chart $x_t$ need not determine the latent future law $K^X$. \
  *NDT-C2 (non-redundant accessibility).* In at least some distinct neural
  regimes, functionals of the chart-conditional law provide reproducible
  out-of-sample information not contained in current chart location and
  standard static or spectral summaries. \
  *NDT-C3 (conditional control).* Context, history, or physiology can alter
  $K_h^x (dot | x, gamma)$ among observations matched on current chart state.
]

C1 alone is not distinctive: any coarse measurement chart may fail to be
sufficient for latent dynamics. The empirical content of NDT lies in C2 and
C3 --- whether structured future-law quantities add reproducible information
beyond present-state summaries, and whether context, history, or physiology
systematically reshape those futures at matched measured state.

The experimental statement of C3 is
$K_h^(x | gamma_1) (x, dot) != K_h^(x | gamma_2) (x, dot)$ at matched chart
$x$. That is not the generic observation that adding covariates improves
prediction. Its empirical content is that predefined physiological or
contextual variables systematically alter nominated features of the future
law at matched chart state, beyond standard state, spectral, and nuisance
covariates. That is the common form of rhythmic, thalamic, historical, and
embodied control. Context-dependent recurrent computation is an established
external precedent for such protocol-conditional dynamics; it does not test
NDT @mante2013context.

C1 asks whether present chart state determines nearby futures. C2 asks whether
accessibility quantities add non-redundant information. C3 asks whether
matched states can have different futures under different control conditions.

== Diffusion geometry

Diffusion in this theory is not a scalar noise amplitude. Define the local
diffusion tensor

$ a(xi, t) = Sigma(xi, t) Sigma(xi, t)^top. $ <eq:diffusion>

The tensor $a$ determines the magnitude, effective dimensionality, anisotropy,
and preferred directions of stochastic spread. Two states with identical mean
drift may differ profoundly in what fluctuations permit. Scalar $sigma(t)$ is
the isotropic special case.

== Potential-driven and non-conservative drift

Potential-driven dynamics form one structured component of the drift, not an
assumption that every neural trajectory is gradient descent:

$ b(xi, t | c) = - M(xi, t | c) nabla V(xi, t | c) + u_"nc" (xi, t | c). $ <eq:drift-split>

Here $V$ is a state-dependent potential (not IIT's $Phi$) and $M succ 0$ is a
*mobility tensor*: the matrix that converts a Euclidean gradient into
potential-driven drift. If a Riemannian metric $g$ is later declared,
$M = g^(-1)$. NDT does not currently assume a fluctuation--dissipation
relation linking $M$ to the diffusion tensor $a$. The residual $u_"nc"$ is
permitted because circulation-like, cyclic, or asymmetric flows need not be
gradient descent under the declared geometry. The decomposition is not
uniquely identified from trajectories: anisotropic or state-dependent
mobility can itself generate non-symmetric chart Jacobians and apparent
non-normality. Jacobian asymmetry is therefore not sufficient evidence for a
non-conservative mechanism.

Dummy $xi$ remains a realization of latent $X_t$. Later sections discuss
empirical counterparts as chart-level estimates $hat(b)_x$, $hat(a)_x$, and
$hat(J)_x$ on a declared measurement chart $x$.

== Rhythmic variance control as the minimal special case

Rhythmic Variance Control is the minimal isotropic accessibility-control
model @langell2025ndt. Let $r(t) in [0, 1]$ denote an operational
rhythmic-control proxy and

$ sigma(t) = sigma_min + sigma_0 (1 - r(t)). $ <eq:rvc>

High $r(t)$ therefore reduces stochastic amplitude and biases the process
toward stabilization, whereas lower $r(t)$ permits broader exploration. In the
general NDT process, rhythmic control need not act only on scalar variance:

$ r(t), c(t) -> {b_t, Sigma_t, M_t, "transition gates"}. $ <eq:access-control>

RVC is thus the isotropic variance-control limit of the broader
accessibility-control hypothesis. State- or event-dependent changes in neural
variability are themselves an established cortical phenomenon
@churchland2010stimulus. NDT's stronger claim concerns structured rhythmic
control of such variation, not the existence of variability quenching.
Stronger specificity claims are treated as control-layer hypotheses in
@sec:control, not as denoising proofs.

= Measured state: MNPS and the NeuralManifoldDynamics boundary <sec:measurement>

== Canonical and stratified charts

The three-dimensional observation chart is Eq. @eq:mnps3.
Operational families: $m$ indexes mobility, metastability, or rhythmic
coordination; $d$ indexes deviation from an integration--segregation balance;
$e$ indexes entropy or complexity pressure. These are chart semantics, not
unique biological axes.

A stratified nine-dimensional chart

$ x_t^((9)) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m]^top $ <eq:mnps9>

provides higher-resolution measurement, with recomposition into the three
families through a release-fixed projection $x_t = P_"fixed" x_t^((9))$. The
rationale is to reduce dimensional masking and to expose compensatory changes
hidden in 3D. $P_"fixed"$ is an auditable operational contract, not a claim of
unique ontology. Downstream local-dynamics claims inherit that contract.

== MNPS is not NDT

MNPS provides coordinates in which some NDT-related quantities can be
estimated. It does not exhaust NDT. The theory remains meaningful if another
valid chart replaces MNPS, if some dynamical objects are more identifiable than
the coordinates themselves, or if modality-specific charts differ. Identifying
the latent state $X_t$ with $(m, d, e)$ is rejected as a homology.
Dimensionality reduction supplies a parsimonious population description; it
does not automatically identify the underlying process
@cunningham2014dimensionality @duncker2021dynamics.

== NeuralManifoldDynamics as a measurement contract

NeuralManifoldDynamics (NMD) operationalizes selected MNPS and local-dynamics
quantities through versioned preprocessing, feature construction, chart
projection, and estimator contracts. MNPS is an observation chart through
which some NDT quantities can be estimated, not the theory itself.

NDT specifies latent interpretation, the objects $b$, $a$, $J$, reachability,
committor, and finite-amplitude questions, predicted dissociations, and
mechanism hypotheses, whereas NMD operationalizes the corresponding
measurement contracts.

A Jacobian estimated specifically in MNPS is termed an MNJ; its derived
quantities remain chart-level measurements. Diffusion, stochastic
reachability, committor, and finite-amplitude families require independent
estimator validation and are not implied merely by availability of an MNPS
chart or Jacobian. Simulator recovery of diffusion tensors and Jacobian
summaries on linear SDEs does not, by itself, license those quantities on
empirical charts. Current software status and estimator validity conditions
are documented in Supplementary Methods S1.

== Measurement inheritance rule

Any downstream inference inherits the validity limits of (i) raw measurement,
(ii) preprocessing, (iii) feature construction, (iv) chart definition, and
(v) local estimator. A plausible embedding does not cancel those limits.

= Local dynamical geometry <sec:local-j>

Empirical local flow is estimated on a declared measurement chart. Write
$hat(b)_x$ for a chart-level drift estimate. The empirical Jacobian is

$ hat(J)_x (x, t) = (partial hat(b)_x) / (partial x). $ <eq:jacobian>

The corresponding latent derivative is $nabla_xi b(xi, t)$. Unadorned $J$ in
later empirical sentences means $hat(J)_x$ unless a latent argument is
explicit. The term MNJ is reserved for a Jacobian estimated in an MNPS chart.
$hat(J)_x$ asks how nearby perturbations change under the local chart flow. It
does not ask where the system sits, how noise spreads, or which basin is
favoured.

Two derived summaries are conceptually distinct and must remain so. The
*spectral abscissa*

$ alpha(J) = max_i Re[lambda_i (J)] $ <eq:alpha>

is the dominant modal growth or decay rate. The *numerical abscissa*

$ omega(J) = lambda_max ((J + J^top) / 2) $ <eq:omega>

is the maximal instantaneous growth rate. A system can satisfy $alpha < 0$
while $omega > 0$: every eigenmode decays, yet some perturbations grow at
short times. Non-normal transient amplification of this kind is an established
property of neuronal networks, distinct from eigenvalue-driven slowing
@hennequin2012nonnormal @christodoulou2022regimes. The reactivity gap
$Delta_"react" = omega - alpha$ is a derived,
non-normality-sensitive summary of that separation. It is not a complete
measure of non-normality. The antisymmetric part $Omega = (J - J^top) / 2$
supplies a rotational component distinct from reactivity.

Finite-time amplification, for example a peak gain $G_"peak" (T)$ of a local
propagator over a horizon $T$, is a different object again. Companion
simulator studies with known ground-truth dynamics recover $alpha$, $omega$,
and $Delta_"react"$ on declared constant-linear systems under restricted
envelopes, and show that they are not interchangeable
@langell2026_truth_known. Instantaneous Jacobian
recovery does not automatically license ordered finite-time summaries, and
simulator success does not automatically transfer to empirical charts. Those
boundaries stay in force here: "stable" is not a sufficient dynamical
phenotype.

*Coordinate boundary.* The quantities $J$, $alpha$, $omega$, and $Omega$ used
here are local summaries in a declared measurement chart. Away from fixed
points they are not generally invariant under nonlinear reparametrization, and
an Itô SDE acquires an Itô correction under a nonlinear chart change. NDT
therefore treats current MNJ-derived quantities as *chart-level dynamical
measurements* rather than intrinsic manifold tensors. An intrinsic formulation
would require an explicitly declared geometric connection and a covariant
derivative; that object is not currently estimated and is not claimed.

= Local diffusion geometry <sec:diffusion>

Equation @eq:diffusion already makes diffusion a tensor. The questions it
answers are not interchangeable with those answered by $J$. Natural summaries include
total diffusion $D_"total" = tr(a)$, an effective diffusion dimensionality, a
concentration or anisotropy index, and orientation-specific alignments relative
to a declared probe direction.

Two states can share a similar $J$ and differ in $a$, or share a similar $a$
and differ in $J$. That dissociation is part of what "diffusion" is supposed to
mean in NDT. Companion studies with known ground-truth dynamics recover $a$
on linear SDEs as a mathematical measurement under inspectable envelopes
@langell2026_truth_known
(support, timestep, bandwidth, observation noise). Gauge matters: orthogonal rotations
leave tensor summaries invariant to numerical tolerance, whereas nonuniform
rescaling does not. Recovered $a$ is therefore chart-dependent unless a chart
is declared. Empirical interpretation through NMD remains a separate
translation problem; diffusion geometry is not implied by Jacobian residuals
alone.

= Geometry of possible futures <sec:futures>

Local linearization does not exhaust accessibility. This section collects
objects that ask what can happen over a finite horizon, toward which
destination, and after a perturbation that is no longer infinitesimal.

== Stochastic short-horizon reachability

*Stochastic short-horizon reachability* asks how probability mass over nearby
future states spreads under $K^h$. It is a covariance-based approximation to
finite-horizon *predictive spread*, not classical control-theoretic
reachability and not a Gramian of a structural connectome. A short-horizon,
locally frozen-coefficient stochastic linearization about the reference state
at time $t$ uses $A_t$, $b_t$, and $Q_t$ held fixed over the propagation
horizon:

$ x_(t+1) = A_t x_t + b_t + epsilon_t, quad epsilon_t tilde (0, Q_t) $ <eq:linearization>

induces the locally frozen-coefficient covariance recursion

$ Sigma_t^((h+1)) = A_t Sigma_t^((h)) A_t^top + Q_t, $ <eq:reachability>

with $Sigma_t^((0)) = 0$. This recursion approximates short-horizon covariance
propagation under the local linear model; it is not the general time-varying
transition law. Eigenvalues of $Sigma_t^((h))$ yield volume,
anisotropy, and effective-dimension summaries of a *predictive-spread
ellipsoid*. That ellipsoid is not an unqualified reachable set: it describes
second-moment spread under a local linearization, not the support of every
admissible control.

Predictive spread is not occupancy, entropy, traversability, controllability,
or consciousness. Large $Q_t$ can inflate the ellipsoid without richer
controllable geometry. Horizon and neighbourhood leakage are validity
conditions. Companion simulator work can calibrate aggregate covariance
propagation while failing tests of memory-specific or target-private
directional spread; calibration is not destination geometry. Empirical claims
that invoke accessible futures therefore require their own estimator
validation; they cannot be read off chart location.

== Committor geometry

For competing destinations $A$ and $B$, the committor

$ q(x) = P_x (tau_B < tau_A) $ <eq:committor>

is the probability of hitting $B$ before $A$. It is destination geometry, not
local expansion and not reachable volume. The object is theoretically central
and is the continuous-process counterpart of transition-path theory
@e2010transition @metzner2009transition. Its empirical and even finite-sample status is severely bounded. One-dimensional
local-law recovery can be qualified under restricted contracts; two-dimensional
finite-sample recovery has not been supported under the estimator families so
far tested. Current validation does not support empirical committor estimation
within the NMD pipeline. Stage labels are not committor truth. Committor
geometry is therefore retained as a theoretical target rather than treated as
a currently validated empirical measurement.

== Attractors and finite-amplitude resilience

Attractor and basin structure --- locations, depth, boundaries, corridors,
metastability, escape --- organize longer-run trajectories
@tognoli2014metastable @deco2017dynamics @hancock2025metastability. Visual clustering is not evidence of
an attractor. Finite-amplitude resilience (FAR) asks how large a perturbation
the system can tolerate before leaving its current dynamical regime. Local
stability does not imply FAR; Jacobian or finite-time tangent gain does not
substitute for an observed perturbation protocol. Without such a protocol, FAR
is not an empirical measurement.

== Non-equivalent dynamical questions

The point of this hierarchy is not to brand a new metric for each row. It is
to keep the questions distinct. They are non-equivalent in explanatory
target, not orthogonal in the linear-algebraic or statistical sense.

#figure(
  kind: table,
  clean-table(
    columns: (2.2fr, 1.4fr),
    align: (left, left),
    inset: 5pt,
    table.header([*Dynamical question*], [*Object*]),
    [Where is the system?], [chart state $x$],
    [Where is it locally moving?], [drift $b$],
    [Do infinitesimal modes grow?], [spectral abscissa $alpha$],
    [Can perturbations initially amplify?], [numerical abscissa $omega$],
    [How does random variation spread?], [diffusion tensor $a$],
    [How does short-horizon mass spread?], [predictive-spread ellipsoid],
    [Which destination is favoured?], [committor $q$],
    [Which basin organizes the trajectory?], [attractor geometry],
    [Can a finite perturbation dislodge it?], [FAR],
  ),
  caption: [Non-equivalent questions in NDT. No single local measure answers the others. Empirical availability of each object is a separate contract, not a consequence of having a chart.],
) <tab:orthogonal>

#figure(
  image("figures/conceptual/fig3_orthogonal_questions_v2.png", width: 96%),
  caption: [Non-equivalent dynamical questions. The same state $x_t$ supports six non-interchangeable objects. No single local measure answers the others.],
) <fig:orthogonal>

Formal neighbours --- network control, predictive processing, metastability, and
the major consciousness theories --- are compared in @sec:neighbours. The
present emphasis remains measured dynamical accessibility rather than control
energy, free-energy identity, workspace ignition, or integrated information.

= Biological control of accessibility <sec:control>

Equation @eq:canonical is incomplete until one says what $c_t$ is allowed to
change. The theory does not need a catalogue of subsystems. It needs candidate
implementations of C3: processes that can change $K_h^x (dot | x, gamma)$ at
matched chart location. The main text groups candidate implementations into
three broad classes. They occupy
different slots in ${b, Sigma, M, V, "gates"}$ and are not interchangeable.
Cortical gain itself can be reshaped by attention, arousal, motor state, and
neuromodulation through multiple cellular and circuit routes
@ferguson2020mechanisms; NDT's control layer is a candidate decomposition of
how such influences change $K_h^x$, not a claim that those routes are unique to
the present theory. A failure in one slot revises that implementation; it does not falsify
accessibility control as a modelling class.

#figure(
  kind: table,
  clean-table(
    columns: (1.4fr, 1.8fr, 1.6fr),
    align: (left, left, left),
    inset: 5pt,
    table.header([*Candidate*], [*Intended action*], [*Present ceiling*]),
    [RVC], [scalar $sigma(t)$], [minimal special case; event-gated write
      specificity not supported],
    [Thalamic access], [directional $A_"sig"$, $A_"noise"$ on frozen $V$],
      [synthetic operator existence; biology is association, not operator ID],
    [HELS-A], [context operator $A_H$ on frozen $V$], [synthetic access
      without landscape rewrite; empirical scoring not licensed],
    [HELS (legacy)], [$partial V \/ partial t$ from history], [landscape
      problem remains open; infrastructure is not writing],
    [Embodiment / metabolism], [context $c_t^"body"$; feasibility $q^"met"$],
      [conditioning and constraint; not consciousness coordinates],
  ),
  caption: [Control of accessibility. Each row changes a different part of the local dynamical object. None is licensed as *the* NDT mechanism.],
) <tab:control>

#pagebreak(weak: true)

#figure(
  image("figures/conceptual/fig4_accessibility_control_v3.png", width: 100%),
  caption: [Accessibility control. Each candidate mechanism is drawn as acting on a distinct slot of the local law. A failure in one slot revises that implementation; it does not falsify the modelling class.],
) <fig:control>

== Fast rhythmic and access control

Equation @eq:rvc is the isotropic variance-control limit: a rhythmic proxy
$r(t)$ schedules scalar noise amplitude and thereby the
exploration--stabilization trade-off. Event- or state-dependent quenching of
trial-to-trial variability is an established external phenomenon
@churchland2010stimulus. That does not establish RVC. The NDT claim is
stronger and narrower: structured rhythmic control of such variation, of
which Eq. @eq:rvc is the minimal special case. That is a claim about *one* entry in
${b, Sigma, M, V, "gates"}$. Companion tests of stronger write-gate timing
against energy-matched and shuffled-timing controls have not supported a
general rhythmic-necessity claim. Event-locking of a measurement chart, if
replicable, is a state-geometry constraint. Causal denoising remains
unsupported.

A stronger anatomical implementation would identify thalamoreticular circuitry
with the scalar variance-control term itself. Current evidence does not
license that identification. The broader hypothesis considered here is that
thalamocortical and thalamoreticular circuitry may contribute to
state-dependent access control through gating, gain, dimensionality,
diffusion geometry, or contextual routing --- none of which is required to be
scalar $sigma(t)$. Independent physiology already treats thalamus as a
modulator of functional cortical connectivity and distributed cognitive
control, not merely a relay of categorical content
@halassa2017thalamic @schmitt2017thalamic. That is the external foundation for
this access-control formulation. It is not identification of $A_"noise"$.

A companion two-operator specialization makes that distinction executable on a
frozen landscape,

$ d X_t = A_"sig" b_0(X_t) d t + A_"noise" Sigma_0 d W_t, $ <eq:ta-operators>

with $V$ held fixed. Under that contract, directional $A_"noise"$ can rotate
short-horizon dispersion at matched total diffusion power, and non-normal
$A_"sig"$ can produce $alpha < 0 < omega$ while a scalar contraction cannot
@langell2026_thalamic_access. Those are *operator-existence* results on a declared 2-D potential, not
thalamic physiology. Empirical TRN perturbation work currently reaches a lower
rung: PV-selective photoinhibition is associated with evoked
participation-ratio contraction, and both PV- and SST-family manipulations
associate with non-scalar residual-covariance shape after prestimulus
cleaning @langell2026_trn_geometry @langell2026_ta_rolon. That is a bounded contrast against scalar
rescaling, not identification of $A_"noise"$. Closed gates remain in S3. A direct
TRN $->$ mesoscopic $->$ surface-macro bridge is also not currently estimable
from the audited public archives: the available meso--macro and
TRN-perturbation resources do not contain all three links within a shared
preparation, and cross-dataset pooling would not identify the missing causal
chain. NDT has not found the thalamic mechanism.

== History-dependent control

The landscape problem is independent of thalamic routing. Equation
@eq:drift-split can specify motion given $V$. It does not say where $V$
came from. A history-conditioned landscape

$ V(x, t | H_t) $ <eq:phi-history>

is the natural object for later transition probabilities, basin depth, and
hysteresis. The Hippocampal--Entorhinal Landscape System (HELS) asks whether
replay *writes* that landscape. Current infrastructure does not constitute
evidence of writing. That HELS question remains speculative.

HELS-A is a different question. It asks whether a context-conditioned access
operator can change which routes remain available *while $V$ is held fixed*:

$ d X_t = - A_H nabla V(X_t) d t + sigma d W_t. $ <eq:hels-a>

Companion simulations with known ground-truth dynamics support that split on declared
geometries: directional $A_H$ can saturate first-passage toward a
context-matched target where speed-matched scalar gain does not, and an
unsaturated committor can be biased by context and collapsed by shuffle. A
neighbourhood robustness extension did not pass. The licensed statement is
narrow: $V$ fixed and $X_0$ fixed do not imply $q(X_0)$ fixed when $A_H$
changes @langell2026_hels_a. That is not a hippocampal, thalamic, memory, or MNPS result. HELS-A
shows that the landscape problem and the access problem can come apart.
The corresponding biological scoring gap is recorded in S3.

A separate observation --- that true recent history can improve linear
prediction of post-stimulation measured EEG beyond the current measured state
on one meso-to-macro contract --- is a P6-adjacent *measured-state*
constraint. It is not landscape writing and not a scored hippocampal mechanism.

== Physiological boundary conditions

Bodily signals are treated as context variables that may condition
accessibility, not as coordinates of consciousness. Companion work can support
bounded autonomic--chart co-modulation without identifying causal
body-to-manifold gating. Any such coupling belongs in $c_t^"body"$, not in
$(m, d, e)$ by default.

Slower physiology is a feasibility boundary. Let $q^"met"(t)$ denote metabolic
adequacy. A trajectory may be geometrically available in the abstract model
yet physiologically unavailable because the substrate cannot support it.
Metabolism is not a consciousness scalar, not an MNPS axis, and not equivalent
to arousal.

A slower dendritic mobility bias is a speculative microscale analogue of
access without landscape rewrite; it is not an empirical MNPS identity
@langell2026_slow_branch. Detail stays in S3.

= Empirical constraints <sec:empirical>

No companion result validates the NDT chain end to end. The role of evidence
here is to constrain layers, not to define the theory. Three anchors enter the
main text because they answer different questions in the hierarchy of
@tab:orthogonal. Everything else is summarized as structured dissociation
rather than narrated dataset by dataset. Every numerical claim below is bound
to one canonical companion artifact, listed in S2. Superseded intermediate
bundles are not used.

Companion simulations with known ground-truth dynamics, already used to bound $a$, $alpha$, and
$omega$ in @sec:local-j and @sec:diffusion, belong in this map as
*methodological qualification*: they ask whether nominated mathematical
objects recover known latent targets under inspectable envelopes. They do not
identify simulator coordinates with MNPS and they do not replace empirical
anchors.

== Anchor 1: spindle-locked state reconfiguration

The first question is whether a physiologically discrete rhythmic event
coincides with local chart reconfiguration --- not whether spindles prove
denoising, memory writing, or a thalamic variance clamp.

A companion overnight-EEG analysis of N2 spindles on a frozen stratified MNPS
export --- *Sleep Spindles Briefly Shift Cortical Network Geometry in Two
Independent Overnight EEG Datasets* --- finds a replicable within-event rise in the
network-deviation coordinate $d_n$ when the spindle window is compared with a
far pre-event baseline (ANPHY high-density EEG, $N = 27$; BOAS / OpenNeuro
ds005555, $N = 128$) @langell2026_rvc_spindles @wei2024_anphy_sleep @ds005555_1_1_1. Effect sizes on
that timing contrast are modest (ANPHY $+0.106$, $q = 0.009$; BOAS $+0.165$,
$q = 0.011$). A third overnight polysomnography sample (RichSleep, $N = 24$)
is underpowered for the same timing estimand and is treated as corroboration
via its event-versus-matched-control contrast, not as an independent timing
replication. Jacobian, diffusion-tensor, and reachability endpoints were not
the primary objects. Canonical sources are listed in S2.

Matched-control specificity is incomplete. Several family endpoints are
dominated by baseline differences rather than by the event increment, and the
event-versus-matched-control sign for $d_n$ conflicts across datasets for that
reason. Autonomic composites do not moderate the geometry effect under the
primary protocol. Sigma-band power residualization was not part of the frozen
schema.

#netn-box(title: [Anchor 1 ceiling])[
  Discrete spindle events coincide with a replicable, timing-locked rise in
  stratified $d_n$. That is chart-level state reconfiguration at a
  rhythm-defined micro-event (claim class 1). It is not causal
  denoising, not a pure spindle-versus-matched-N2 mechanism, not a reachability
  change, and not TRN identification.
]

== Anchor 2: recovery-linked geometry after cardiac-arrest coma

The second question is whether a clinically important state difference appears
more clearly in accessible futures and local flow than in static location
alone.

A companion pooled analysis --- *Recovery-Linked Neural Geometry After
Cardiac-Arrest Coma* --- uses the final corrected 301-patient I-CARE dataset
and evaluates MNPS spread, local Jacobian
deformation, and short-horizon predictive-spread summaries jointly in two independently
processed, non-overlapping cohorts ($301$ analyzable patients across $5322$
recordings; $281$ in the CPC 1 versus CPC 5 contrast, $141$/$140$; window
$0$--$12$ h after the EEG clock, not the ROSC clock) @langell2026_coma_v011 @amorim2023icare. All five
prespecified predictive-spread / short-horizon reachability summaries survive BH-FDR in the pooled sample. The
strongest individual effects are persistence/log-det volume proxies
($d = -0.909$ and $d = 0.896$); effective predictive-spread dimensionality is
$d = 0.838$ pooled and already $d = 0.786$ in the first analyzable hour. Local Jacobian summaries are directionally aligned ---
lower expansion and deformation in later-good-outcome patients --- but
heterogeneous in magnitude across cohorts. Static MNPS spread is lower in
better-outcome patients and is restored as a descriptive anchor, not as the
lead. A subject-wise circular-shift null does not support a claim about which
hour is uniquely strongest. Adding the geometry layer to a feature-limited
clinical-plus-qEEG baseline raises internal AUROC from $0.599$ to $0.662$, a
bounded increment that is not multimodal bedside prognostication. Canonical
sources are listed in S2. An earlier ComBat-corrected 298-patient merge is not the
source used here.

Because withdrawal-of-life-sustaining-therapy, time-to-death, and sedation
annotations were unavailable, the contrast is recovery-linked geometry, not a
pure viability assay and not a consciousness meter.

#netn-box(title: [Anchor 2 ceiling])[
  Early post-arrest EEG contains layered, recovery-linked geometry: short-horizon
  predictive-spread summaries and local deformation carry information that static
  severity/location does not exhaust. These are study-specific chart-level
  estimators.
  Residual quality and perturbation-response were not the study design, so the
  result motivates the accessible-futures layer. It does not constitute
  identification of a dynamical operator from known ground-truth dynamics.
]

== Anchor 3: meso-to-macro contact without operator recovery

The third question is methodological. Can mesoscopic population quantities predict macroscopic EEG
features under nulls, and does that contact license a local operator?

A companion analysis of simultaneous Neuropixels and surface EEG during cortical
electrical stimulation, continuing from wakefulness into isoflurane
@langell2026_dandi000458 @dandi000458, reports median subject associations $r = 0.406$ (LFP SD with EEG SD)
and $r = 0.395$ (spike rate with EEG spectral entropy), surviving sign-flip and
circular time-shift nulls. Event alignment remains incompletely validated, so
these are conditional trial-aligned associations. The same EEG-only
local-linear chart yields a median residual-variance fraction of $0.856$.
Jacobian and reachability inference on that chart are therefore rejected.

A complementary IBL analysis reaches a related boundary: raw population
decoding detects stimulus side under a pilot positive-control test, whereas a
predefined single-trial chart-transition model fails its held-out estimability
floor @langell2026_ibl2. Failure of a dynamical readout need not imply absence
of information in the underlying population.

The pair is the epistemic spine of the empirical map. Cross-scale contact is
real at association. It is not common latent-state identity, unique NDT
geometry, causal direction, TRN identification, or a validated MNJ. A visually
plausible chart plus a correlation does not license a different inferential
claim class.

#netn-box(title: [Anchor 3 ceiling])[
  Meso and macro observables can covary under stimulation-aligned windows after
  temporal and statistical nulls (claim class 1). The tested EEG chart does not
  recover a local flow, Jacobian, or reachability operator (claim class 4 fail).
]

== Structured dissociations, not a universal signature

NDT predicts that different conditions move different layers. Companion
clinical and task analyses are therefore kept as one constraint matrix rather
than as additional anchors.

#figure(
  kind: table,
  clean-table(
    columns: (1.4fr, 1.5fr, 1.5fr, 1.6fr),
    align: (left, left, left, left),
    inset: 4.5pt,
    table.header([*Setting*], [*What moves*], [*What does not*], [*Ceiling*]),
    [Depressive-symptom rest], [reachability; 9D rotational structure],
      [coarse 3D volume as lead], [symptom-burden geometry, one young cohort],
    [First-episode psychosis], [medication-stratified chart and trajectory
      splits], [one FEP signature], [bounded; not a universal deformation],
    [Gambling vs cognitive control], [local Jacobian / flow geometry],
      [MNPS location; matched EDA], [state-versus-flow dissociation],
    [Hypoglycaemic clamp], [3D/9D state; slow-rhythm increase],
      [confirmatory reachability collapse], [feasibility constraint, not
      $q^"met"$ identification],
    [Infant age], [chart coordinates and classical qEEG],
      [FDR-supported local-flow change], [development as state, not futures],
    [Expected-stimulus omission (mouse VISp) @langell2026_avb_omission], [event-locked chart separation],
      [Jacobian, diffusion, reachability, prediction-error ID], [AVB-adapted
      chart; state geometry only],
    [IBL chart readout @langell2026_ibl2], [population decoder, stimulus-side pilot],
      [single-trial discrete chart-transition operator], [information can be
      present while the nominated dynamical readout fails],
    [Human MTL--scalp (DANDI 000574) @langell2026_dandi000574], [neither primary frozen pair],
      [meso--macro association under that contract], [design-specific negative,
      not a replication of DANDI 000458],
  ),
  caption: [Selected dissociations. NDT is constrained by which layer moves, not by a single consciousness-shaped manifold shift. Full companion reports remain outside this article.],
) <tab:dissociations>

#figure(
  image("figures/conceptual/fig5_evidence_map.png", width: 100%),
  caption: [Evidence map for the present theory. Cells are status under frozen contracts, not independent replication. $V$ = validated; $B$ = bounded; $N$ = null or fail; dash = not tested; $S$ = speculative. Added matrix rows: Allen AVB (state geometry), IBL chart readout (decoder succeeds / flow fails), and DANDI 000574 (human MTL--scalp association fail). Empty anesthesia and epilepsy rows are not tested, not hidden positives.],
) <fig:evidence>

The pattern is the result. Reduced dynamical capacity is not itself reduced
consciousness. Sleep, anesthesia, seizure, coma, and affective or psychotic
regimes may all alter capacity-like summaries while differing in whether the
change is mainly location, local deformation, stochastic spread, reachable
volume, or canalized lock-in.

= Neighbouring frameworks <sec:neighbours>

NDT does not compete with constitutive or access theories of consciousness on
their own terms. Its defensible claim is narrower: it is a framework for
dynamical accessibility and a versioned measurement framework on which
predictions from several of those theories can be expressed and, in places,
cross-checked @storm2024integrative. The comparison that follows is therefore a
map of partly different questions, not a contest for a single title. A longer
thematic treatment of the same neighbourhood exists as a companion essay
@langell2026_ndt_theories; this
section imports only the bridges and non-equivalences that constrain the
present theory.

#netn-box(title: [Positioning])[
  IIT proposes what consciousness is claimed to be. GNWT proposes when content
  becomes globally available. NDT proposes how neural trajectories are locally
  generated, spread, gated, and made more or less reachable. Those are not
  interchangeable answers to one question.
]

The mathematical machinery --- generators, Markov semigroups, transition-path
theory and committors, transfer operators, and finite-horizon stochastic
spread --- is established
@metzner2009transition @klus2018data @deco2017dynamics @tognoli2014metastable.
NDT's proposed novelty is not the discovery of a transition kernel. It is a
neuroscientific synthesis: treating the geometry of a control-dependent
future law as a primary object of neural-state organization; decomposing that
law into non-equivalent empirical questions; separating measurement-chart
claims from latent-process claims; testing whether context, history, or
physiology changes the future law at matched chart state (C3); and applying
that synthesis to consciousness-relevant regimes. Generators, diffusion
tensors, committors, and related stochastic objects are established
mathematics. The proposed contribution is their joint organization into
present state, local law, future-law structure, and conditional access; the
requirement that those objects not be treated as interchangeable; the
measurement / latent-process separation; and the empirical commitments C2 and
C3. The established stochastic-process machinery provides the mathematical
scaffolding; the NDT claim lies in that decomposition, measurement discipline,
and conditional-accessibility hypotheses.

== Different questions, not rival scalars

"What does consciousness correspond to?" is not a single question. Neighbouring
frameworks answer at least six different ones: whether experience is present
(level); what is experienced (content); whether information is available to
report and action (access); whether the system represents itself as being in a
state (meta-awareness); whether experience is embodied; and what range of
neural transitions remains available (dynamical capacity). NDT addresses the
last of these. It does not currently identify NCC proper, and its charts are
closest to enabling state dynamics --- NCC prerequisites and the dynamical
context around experience --- rather than to report, confidence, or phenomenal
identity.

Theories can therefore be nested as explanatory layers without being jointly
validated @storm2024integrative. Predictive inference can supply candidate
content @friston2010free @clark2013whatever. Recurrent processing can stabilize
sensory representations @lamme2006towards @lamme2010neural. A workspace can
broadcast selected content @baars1988cognitive @dehaene2011experimental
@mashour2020conscious. Higher-order or attention-schema systems can represent
aspects of that access @lau2011empirical @brown2019understanding
@webb2015attention. Embodied inference can bias the background state
@seth2013interoceptive. Dynamical geometry can describe the trajectory through
which those processes unfold. Structural network control can constrain which
transitions are cheap or costly @gu2015controllability @tang2018control.
Compatibility of layers is not evidence that every theory is true.

== Closest family: landscapes, metastability, and control

NDT's nearest relatives are dynamical-landscape, metastability, and
network-control accounts @deco2011emerging @deco2017dynamics
@kelso2012multistability @tognoli2014metastable @hancock2025metastability
@breakspear2017dynamic @gu2015controllability. They
already deny that regional activity magnitude is a sufficient description.
A manifold visualization likewise does not identify the dynamical rule
@duncker2021dynamics. NDT inherits that denial and adds five commitments that those families do not
jointly require:

1. *Stochastic diffusion geometry* as a first-class local object $a(xi,t)$, not
   only noise around an attractor.
2. *Accessibility decomposition*: location, local flow, stochastic spread,
   reachability, commitment, and finite-amplitude resilience answer different
   questions (@tab:orthogonal).
3. *Explicit measurement contracts*: MNPS and NeuralManifoldDynamics are
   operational charts and estimators, not unique latent identification.
4. *State-dependent control*, of which rhythmic variance scheduling is the
   minimal special case, not the whole theory.
5. *Recoverability discipline*: association does not license a local operator
   (@sec:ladder).

Network control theory shares the concern with possible transitions. NDT does
not currently assume an explicit input matrix $B$ or minimize control energy.
Its reachability objects are empirical, chart-level, and short-horizon; they
are not Gramian controllability of a structural connectome. Metastability
shares the concern with a regime between lock-in and fragmentation. MNPS $m$
is an operational mobility/coordination proxy, not a Kuramoto order parameter
computed from pairwise phase relations. Landscape models share potential
descent. In NDT that descent is a structured component of drift, not the
general law: non-conservative flow, non-normal transients, and anisotropic
diffusion remain in $u_"nc"$ and $a$.

The claim "conscious states have geometry" is therefore not distinctive. The
testable NDT increment is that neural variability and transition structure are
systematically and state-dependently modulated, and that the resulting local
flow, diffusion, and accessible futures can contain information not recoverable
from location, power, or generic complexity alone.

== Constitutive, access, and inference theories

#figure(
  kind: table,
  clean-table(
    columns: (1.15fr, 1.7fr, 2.15fr),
    align: (left, left, left),
    inset: 4.5pt,
    table.header([*Framework*], [*Possible bridge*], [*Non-equivalence*]),
    [PP / FEP], [precision; landscape descent; state estimation],
      [fitted accessibility is not a generative model with explicit priors],
    [IIT], [both reject activity magnitude as sufficient],
      [NDT does not identify consciousness with $Phi$ or intrinsic causal
      structure],
    [GNWT], [access geometry may enable or disable global availability],
      [dynamical reachability is not workspace ignition],
    [RPT], [rotational / local recurrent flow $Omega$],
      [chart-level rotation is not anatomical feedback],
    [HOT], [none proposed],
      [NDT does not model representation-of-representation],
    [AST], [attention-related coordinates as possible inputs],
      [an attention proxy is not an attention schema],
    [Landscapes / metastability], [closest dynamical family],
      [NDT adds diffusion geometry, control, and measurement contracts],
    [Network control], [possible transitions; future state space],
      [no current $B$ matrix or control-energy objective],
  ),
  caption: [Bridges are analogies unless a shared formal object is identified. Superficial vocabulary overlap is not equivalence.],
) <tab:bridges>

*Predictive processing / free-energy principle.* Precision, inference, and
embodied prediction supply a neighbouring language for content and for
slow bodily context @friston2010free @clark2013whatever @seth2013interoceptive.
The relevant comparison is a specified generative model, not the umbrella
principle. NDT's emphasis is measured, state-dependent transition structure.
A fitted drift term is not variational free energy, and $r(t)$ is not
precision by another name.

*Integrated information.* IIT identifies consciousness with irreducible
intrinsic cause--effect structure, quantified as $Phi$
@tononi2016integrated @oizumi2014phenomenology. Perturbational complexity is
clinically important and IIT-inspired, but it is not an empirical calculation
of $Phi$ @casali2013theoretically. NDT refuses a structural "amount of
consciousness" scalar of that kind. Shared rejection of simple magnitude is
not a shared ontology.

*Global workspace.* GNWT targets access: information becomes globally available
after a competitive ignition-like transition @baars1988cognitive
@dehaene2011experimental @mashour2020conscious. Dynamical accessibility in NDT
may describe conditions that make such a transition more or less available. It
does not model broadcast, report, or workspace competition. Reachable volume
is not ignition.

*Recurrent processing.* RPT locates a threshold in recurrent sensory
processing rather than in global broadcast @lamme2006towards @lamme2010neural.
NDT's antisymmetric Jacobian $Omega$ is compatible with rotational or
recurrent flow. Compatibility is not anatomy: a chart rotation does not
establish feedback in sensory cortex, and recurrence is not treated as
sufficient for experience.

*Higher-order theories and attention schema theory.* These target
meta-representation and a simplified internal model of attention
@lau2011empirical @brown2019understanding @webb2015attention. NDT currently
has no corresponding state variable. Metacognitive sensitivity and awareness
attribution are neighbouring empirical programmes, not NDT objects.

== Lessons that apply across theories

Two external results discipline every framework in this neighbourhood,
including NDT.

The Cogitate Consortium's preregistered adversarial collaboration did not
declare a winner between IIT and GNWT @cogitate2025adversarial. Predicted
posterior synchronization and predicted prefrontal offset ignition were both
challenged in the specified form. The methodological lesson is prior
commitment: mature theories become stronger when they state in advance what
would count against them. NDT has not undergone an adversarial test of
comparable independence or scale.

State discrimination is not detection of experience. Complexity measures can
separate wakefulness from sedation while failing to distinguish reported
dreaming from no reported experience within the sedated condition
@bajwa2025repeated. PCI, ignition markers, and NDT reachability may all index
regimes that make experience more or less likely. None is licensed as a
consciousness meter by that fact. Companion coma geometry is
recovery-linked capacity (@sec:empirical), not a within-state experience
assay. Dynamic patterns of brain coordination also differ across conscious
and unconscious conditions, including disorders of consciousness
@demertzi2019human. Content or representational geometry --- for example no-report colour
similarity --- is a neighbouring question, not an accessibility measurement.

= Predictions and failure conditions <sec:predictions>

NDT is tested by layer, not as a single slogan. The predictions below are
theory-level. Companion anchors constrain some of them; none is a completed
adversarial result.

#figure(
  kind: table,
  clean-table(
    columns: (1.3fr, 1.7fr, 1.6fr),
    align: (left, left, left),
    inset: 4.5pt,
    table.header([*Prediction*], [*What would fail it*], [*Present constraint*]),
    [P1 Rhythmic control], [event structure adds nothing beyond power,
      autocorrelation, smooth precision, or event density],
      [spindle-locked $d_n$ timing; schedule specificity incomplete],
    [P2 State vs accessibility], [richer dynamics add no replicable
      information beyond chart location],
      [coma, gambling, and depression move different layers],
    [P3 Linear vs finite-amplitude], [FAR collapses onto validated local-linear
      summaries], [conceptual; not an empirical NMD export],
    [P4 Diffusion vs drift], [anisotropy / dimensionality add nothing once
      drift is controlled], [simulator envelopes only],
    [P5 Thalamic access], [thalamic variables add nothing beyond arousal /
      sensory gain], [association and synthetic operators; not biology ID],
    [P6 History dependence], [$P(Y_(t+h) | x_t, H_t) approx P(Y_(t+h) | x_t)$],
      [measured-state prediction constraint; not landscape writing],
    [P7 Embodied conditioning], [body-state effects vanish under autonomic /
      arousal controls], [timing support; spindle-geometry efficacy rejected],
    [P8 Within-state experience], [after matching state, responsiveness,
      arousal, power, and complexity, $K_h^x$ still fails to split reported
      experience from no reported experience],
      [not tested; Bajwa-type within-state designs are the template],
  ),
  caption: [Falsifiable predictions. Success or failure of one row revises that layer. It does not automatically ratify or refute the modelling class. P8 is the within-state experience test; it has not yet been tested.],
) <tab:predictions>

A stronger NDT discriminant would jointly require event specificity, schedule
specificity against stationary and smooth controls, incremental value beyond
power and generic complexity, and failure under phase-shuffle, time-shift,
wrong-event, and power-matched nulls. Current spindle evidence supports a
timing-locked chart change. It does not yet satisfy the full discriminant.

P8 is the headline within-state test if the article is read as a
consciousness paper. After matching global physiological state,
responsiveness, arousal, spectral power, and standard complexity, does

$ K_h^x (dot | x_t, "experience") != K_h^x (dot | x_t, "no experience") $ <eq:p8>

@bajwa2025repeated? A positive result would license a stronger claim about
mind-relevant accessibility. A negative result would constrain any stronger
claim about mind-relevant accessibility. The present manuscript does not
promote P8 as already answered by coma geometry or complexity scores
(@tab:orthogonal).

#netn-box(title: [Hierarchical failure])[
  Falsification of one subsystem does not falsify dynamical accessibility as a
  scientific object. TRN failure would drop a biological implementation. RVC
  failure would strongly constrain rhythmic scheduling. MNPS failure would
  retire that chart. Operator-recovery failure on a given recording, already
  observed on DANDI 000458, retires that estimator on that chart. None of those
  results implies that neural states have no structured futures.
]

NDT should be substantially narrowed if, across reasonable alternative charts
and nulls: rhythmic scheduling adds no held-out value; local-dynamics
estimators repeatedly fail ground-truth or residual-quality tests; diffusion,
reachability, or FAR reduce to redundant versions of simpler statistics;
history adds no conditional information; and apparent clinical or
altered-state effects are exhausted by power, movement, arousal, or
preprocessing artifacts. The constitutive reading that rhythmic reconstruction
*is* experience remains a labeled speculative extension. It currently adds no
discriminating empirical prediction beyond the dynamical model.

= Discussion <sec:discussion>

== Dynamical accessibility as the organizing principle

NDT treats neural-state location, local dynamics, possible futures, and their
control as distinct but coupled levels of description. Rhythmic variance
scheduling provides one experimentally specific control hypothesis; learned
landscapes provide one structured component of drift; MNPS provides one
measurement chart; and diffusion, Jacobian dynamics, reachability, committors,
and finite-amplitude resilience interrogate different aspects of the
conditional future law. None is individually synonymous with NDT. This
formulation subsumes the earlier rhythmically scheduled denoising model as a
restricted case in which control acts primarily through scalar stochastic
variance @langell2025ndt.

Companion constraints illustrate the decomposition rather than a single
signature: spindle events reconfigure a stratified chart without licensing
causal denoising; early post-arrest EEG separates more clearly on reachable
futures and local deformation than on static spread; meso-to-macro contact
does not recover a local operator (@sec:empirical). Charts and estimators can
fail without making dynamical accessibility meaningless, and they can succeed
as measurements without identifying the latent law. A consciousness scalar, a
universal clinical fingerprint, and any reading in which MNPS location *is*
the NDT claim remain outside the theory.

== Why this may matter

A conscious brain state may not be distinguished purely by complexity,
entropy, synchrony, occupancy, or global activity. Candidate regimes may also
differ in *what the system remains capable of becoming next*. That is a
hypothesis about the organization of neural states associated with
wakefulness, sleep, anesthesia, task engagement, and pathology. It is not an
identity claim about experience, not a meter of awareness, and not a solution
to the hard problem.

The hypothesis is useful only if the layers dissociate. If reachability, local
flow, and diffusion were redundant encodings of location or power, the
accessibility hypothesis would collapse. The present empirical map is not a validation
of the chain. It is evidence that the collapse has not already occurred in
every tested regime, and that different conditions move different layers
(@tab:dissociations). Consciousness research already contains neighbouring
theories of content, access, recurrence, and intrinsic causal structure
(@sec:neighbours). NDT's contribution, if it holds, is a measurement surface
for dynamical capacity and its control --- a surface on which those theories
can make distinct predictions, not a replacement for them.

The next informative experiment is therefore not another broad disease
contrast. It is a design that separates global state, responsiveness,
reportability, and momentary experience, and that asks whether
rhythm-locked or context-locked changes in local flow, diffusion, and
short-horizon reachability explain future trajectories beyond power,
generic complexity, and stationary dynamics (@sec:predictions). A positive
result would still support a neural mechanism, not the claim that
reconstruction is consciousness.

= Limitations <sec:limitations>

No dataset currently validates the NDT chain end to end. Many nominated
objects remain estimator-sensitive: MNPS is operational and chart-dependent;
drift and diffusion are identifiable only under explicit assumptions; local
linearization fails in important empirical regimes, including the EEG chart
tested on DANDI 000458; reachability depends on horizon and noise model;
committor estimation requires meaningful destinations that current
measurement contracts do not emit; and finite-amplitude resilience depends on
perturbation family and amplitude scale.

Biological bridges remain uneven. Rhythmic variance control is a distinctive
prediction, not a demonstrated executor. Thalamic access has synthetic
operator existence and associative biology, not circuit identification.
History-dependent landscape writing is open; access on a frozen landscape is
a computational existence result, not scored hippocampal mechanism.
Embodiment and metabolism are contextual and feasibility constraints, not
consciousness coordinates. Dendritic slow-branch accessibility is a
simulator discriminator and a speculative micro substrate.

Empirical companions are bounded. Sleep, coma, and meso-to-macro analyses
constrain selected layers in selected cohorts. Clinical fingerprints are not
biomarkers. Treatment-limitation and sedation confounds remain unresolved
where they were unavailable. NDT has not undergone an independent adversarial
test comparable to Cogitate. Apparent geometric effects must still survive
alternative charts, power-matched and temporally shuffled nulls, and standard
spectral, connectivity, and complexity baselines.

These limits are scope, not temporary embarrassment. NDT is a framework for
neural dynamical organization associated with conscious-state regimes. It
does not explain why those dynamics are accompanied by experience.

= Conclusion <sec:conclusion>

Noetic Diffusion Theory proposes that neural-state organization is
incompletely described by state position alone. A neural state also carries a
local dynamical structure: deterministic tendencies, stochastic directions,
transient sensitivities, reachable futures, basin commitments, and
finite-amplitude resilience. Those structures are themselves modulated by
rhythm, context, history, physiology, and candidate access-control systems.
MNPS supplies one measurable chart through which this organization can be
studied. NeuralManifoldDynamics supplies one implementation rather than the
definition of the theory. Rhythmic Variance Control supplies the minimal
control case rather than the whole mechanism.

The resulting framework predicts structured dissociations among location,
stability, diffusion, accessibility, commitment, and resilience, and treats
those dissociations as empirically testable correlates of changing neural
regimes --- not as a scalar of consciousness, and not as a complete
explanation of experience. What a neural state *is*, scientifically, includes
what it can still become.

= Acknowledgements

The empirical constraints in @sec:empirical depend on public sleep recordings
@wei2024_anphy_sleep @ds005555_1_1_1, the
I-CARE consortium EEG database @amorim2023icare, and DANDI 000458
@dandi000458.

This work emerged through structured correspondence among human and AI collaborators; large language models from OpenAI, Anthropic, and Google assisted in literature synthesis, drafting, peer review, and editorial refinement. We also gratefully acknowledge the original investigators, clinical teams, participants, and data stewards who created, curated, and shared the public datasets and metadata that made these analyses possible.


#bibliography("references.bib", style: "apa")
