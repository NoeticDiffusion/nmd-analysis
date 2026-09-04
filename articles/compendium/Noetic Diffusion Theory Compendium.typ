#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Noetic Diffusion Theory Compendium",
  short-title: "NDT Compendium",
  subtitle: [A unified mathematical formalization of the NDT article family],
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Independent Researcher",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "controlled diffusion",
    "dynamical accessibility",
    "local dynamics",
    "MNPS",
    "NeuralManifoldDynamics",
    "committor geometry",
  ),
  article-type: "Compendium — mathematical framework",
  abstract: [
    This compendium consolidates the mathematical backbone of the Noetic
    Diffusion Theory article family into one notation. It distinguishes the
    controlled transition law from its non-equivalent local-dynamics families:
    drift, diffusion geometry, chart Jacobians, finite-time response,
    stochastic short-horizon predictive spread, destination probabilities,
    attractor structure, and finite-amplitude resilience. It also records the
    base and stratified Meta–Noetic Phase Space (MNPS), the
    NeuralManifoldDynamics measurement contract, and the speculative
    micro-to-meso accessibility bridge. The goal is not to reproduce each
    paper verbatim, but to provide one dependency-ordered reference in which
    latent theory, measurement charts, local estimators, and validity
    boundaries remain distinct [@langell2025_6; @langell2025_stratified;
    @langell2025_mnj; @langell2026_mndm].
  ],
)

#set heading(numbering: "1.")
#set math.equation(block: true, numbering: "(1)", supplement: none)

= Global Notation and Layering

We fix one canonical notation throughout. The latent noetic process evolves on
a manifold $cal(M)$, while empirical analyses work in local coordinates derived
from EEG, iEEG, or fMRI measurements. This opening section therefore serves as
the common dictionary for the rest of the compendium: first the latent object,
then the chart, then the empirical observation layer, and only after that the
local dynamical operators that act on the charted state.

#math.equation(
  $ X_t in cal(M), quad x_t = [m_t, d_t, e_t]^T in RR^3 $
) <eq:base-chart>

#math.equation(
  $ x_t^((9)) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m]^T in RR^9 $
) <eq:strat-chart>

The observational layer is separated from the latent dynamics:

#math.equation(
  $ Y_t = g(X_t) + epsilon_t $
) <eq:obs-model>

Equations @eq:base-chart and @eq:strat-chart define the canonical and
stratified chart coordinates, while @eq:obs-model places both charts below the
measurement map. Here $Y_t$ denotes measured neural data, $g$ is a measurement
map, and $epsilon_t$ is observation noise. Theoretical dynamics live in
$X_t$; MNPS and Stratified MNPS are empirical charts constructed from short
windows of $Y_t$.

To minimize cross-paper ambiguity, the canonical axes are:

- $m$: metastability / mobility / rhythmic coordination.
- $d$: deviation from an optimal integration–segregation balance.
- $e$: entropy / entropic energy / complexity pressure.

Legacy triplets such as $(E, R, D)$ are treated as manuscript-local precursors
that are monotonically aligned to $(m, d, e)$ at the compendium level. This is
not merely cosmetic. A major source of friction across the article family is
that the same conceptual roles are sometimes named differently depending on
whether a manuscript is emphasizing latent theory, empirical measurement, or a
transitional draft vocabulary.

We also separate five layers that are sometimes blended in the source papers:

- *Latent theory*: stochastic dynamics on $cal(M)$.
- *Microstructural substrate*: branch/spine access, slow structural
  accessibility, and eligibility-like consolidation variables.
- *Meso export*: lower-dimensional accessibility charts exported from
  branch-resolved microstates.
- *Measurement chart*: exported 3D or 9D coordinates used in analysis.
- *Operational contract*: release-fixed projections, derivatives, local
  dynamics, dynamical-family exports, and validity constraints used by
  `NeuralManifoldDynamics`.

= Core NDT Dynamics

== Controlled diffusion as a modelling class

The working process class of current NDT is a controlled diffusion, not a pure
gradient flow and not a fitted neural stochastic differential equation. Let
$c_t$ denote a contextual or control state:

#math.equation(
  $ d X_t = b(X_t, t | c_t) d t + Sigma(X_t, t | c_t) d W_t $
) <eq:canonical-diffusion>

Here $b$ is local deterministic drift, $Sigma$ determines the amplitude and
orientation of stochastic forcing, and $W_t$ is Brownian motion. This is an
effective continuous-state approximation represented by
@eq:canonical-diffusion. It does not assert that neural
fluctuations are literally Brownian or that all relevant dynamics are Markovian.
Hybrid, coloured-noise, delayed, and non-Markov formulations remain compatible
when required by the observation scale.

== Transition-law family

The central object is the control-dependent transition law, not a single
accessibility scalar. The generator of @eq:canonical-diffusion, acting on a
test function $f$, is

#math.equation(
  $ cal(L)_(t | c) f(xi) = b(xi, t | c) dot nabla f(xi)
    + frac(1, 2) op("tr")(a(xi, t | c) nabla^2 f(xi)) $
) <eq:compendium-generator>

with

#math.equation(
  $ a(xi, t | c) = Sigma(xi, t | c) Sigma(xi, t | c)^top $
) <eq:compendium-diffusion>

The diffusion tensor in @eq:compendium-diffusion is the covariance-rate term
appearing in the generator @eq:compendium-generator. The dummy variable $xi$ is
a realization of the latent state $X_t$. For a control or history protocol
$gamma$ over a finite interval, define

#math.equation(
  $ K_(t : t+h)^(X | gamma) (xi, A)
    = P(X_(t+h) in A | X_t = xi "and" gamma_([t : t+h])) $
) <eq:compendium-kernel-latent>

Empirical work generally estimates the chart-conditional counterpart

#math.equation(
  $ K_(t : t+h)^(x | gamma) (x, B)
    = P(x_(t+h) in B | x_t = x "and" gamma_([t : t+h])) $
) <eq:compendium-kernel-chart>

The latent law @eq:compendium-kernel-latent and chart law
@eq:compendium-kernel-chart are therefore separate objects linked by the
measurement/chart contract. When this compendium writes $K^h$ without a
superscript, it means the
chart-conditional law $K^x$ unless a latent argument is explicit. $K^h$ is the
law of the state at horizon $h$, not the full path-space measure. The family
${K^h}_(h > 0)$ is the primary finite-horizon object. A snapshot-conditioned
kernel with fixed $c_t$ is only a special case; history may instead require an
augmented state or protocol-path conditioning.

The named local-dynamics families answer different questions:

- $b$ is the infinitesimal conditional mean rate.
- $a$ is the infinitesimal conditional covariance rate.
- $J$ is the local derivative of drift in a declared chart.
- Finite-time response follows a local Jacobian field over a stated horizon.
- Stochastic short-horizon reachability summarizes finite-horizon predictive
  spread.
- The committor $q$ is a destination or hitting probability.
- Attractors describe long-time organization.
- FAR describes response to a finite displacement.

These are different kinds of object, not interchangeable views of one endpoint
distribution. Rhythm, thalamus, history, body, and metabolism are candidate
changes to $cal(L)$ or $K$, not additional definitions of NDT.

== Three core commitments

The current theory separates three commitments that should not be merged:

- *NDT-C1 (reduced-state insufficiency):* current location in a reduced
  measurement chart $x_t$ need not determine the latent future law $K^X$.
- *NDT-C2 (non-redundant accessibility):* in at least some neural regimes,
  functionals of the chart-conditional law provide reproducible out-of-sample
  information not contained in current chart location or standard static and
  spectral summaries.
- *NDT-C3 (conditional control):* context, history, or physiology can alter
  $K_h^(x | gamma) (dot | x)$ among observations matched on current chart state.

C1 is a sufficiency claim about a reduced chart and is not distinctive by
itself. The empirical content is C2 and C3: whether future-law quantities add
reproducible information, and whether predefined controls systematically
reshape those futures at matched measured state. C3 is not the generic fact
that adding any covariate can improve prediction.

== Drift split and diffusion geometry

The diffusion tensor is not restricted to a scalar noise amplitude. Its
orientation, effective dimensionality, anisotropy, and magnitude can vary
independently of the local mean drift. A structured potential component may be
written as @eq:compendium-drift-split:

#math.equation(
  $ b(xi, t | c) = - M(xi, t | c) nabla V(xi, t | c)
    + u_"nc"(xi, t | c) $
) <eq:compendium-drift-split>

Here $M succ 0$ is a mobility tensor and $V$ is an NDT potential. The residual
$u_"nc"$ permits circulation-like or asymmetric flow. Equation
@eq:compendium-drift-split changes the drift term $b$ in
@eq:canonical-diffusion; it does not replace the diffusion tensor
@eq:compendium-diffusion. This decomposition is not uniquely identified from
trajectories, and NDT does not impose a
fluctuation–dissipation relation between $M$ and $a$. A state-dependent
mobility can itself produce non-symmetric chart Jacobians; asymmetry is not
sufficient evidence for a non-conservative mechanism.

== Rhythmic variance control as a special case

Rhythmic Variance Control (RVC) is the minimal isotropic accessibility-control
case. For an operational rhythmic proxy $r(t) in [0,1]$,

#math.equation(
  $ sigma(t) = sigma_"min" + sigma_0 (1 - r(t)) $
) <eq:compendium-rvc>

High $r(t)$ reduces isotropic stochastic amplitude in this special case, while
lower $r(t)$ permits broader exploration. The general control hypothesis is
broader:

#math.equation(
  $ r(t), c(t) -> {b_t, Sigma_t, M_t, "transition gates"} $
) <eq:compendium-access-control>

Equation @eq:compendium-rvc is the scalar-variance limit of the broader control
map @eq:compendium-access-control. RVC therefore occupies one entry in the
control layer; it is not the definition of NDT and does not establish causal
denoising.

== Formalization boundary

Regularity assumptions are local and contract-specific. Smoothness, finite
moments, support, time-step, and observation-noise conditions must be declared
before a generator or estimator is treated as well posed. The compendium
provides notation for those objects; it does not claim that every theoretical
quantity has a validated empirical estimator.

= Measurement Layer: Base MNPS and Stratified MNPS

== Base 3D Chart

The base measurement chart is the 3D MNPS coordinate vector in
@eq:base-chart. The stratified vector introduced in @eq:strat-chart resolves
subcoordinate masking, while @eq:obs-model makes explicit that both are
measurement-layer objects. The source papers consistently motivate the base
chart as the minimal
low-dimensional summary of noetic state, while also warning that composite 3D
coordinates can mask compensatory shifts among latent mechanisms
[@langell2025_6; @langell2025_stratified]. The practical payoff of starting
with 3D is interpretability; the practical cost is that opposite subcoordinate
movements can cancel one another and leave the composite apparently unchanged.

== Canonical 9D Stratified Chart

To resolve that masking, the stratified chart expands each axis into three
sub-coordinates. This is the key move that turns MNPS from a coarse state map
into a mechanism-sensitive chart: the question shifts from “where is the system
in $(m,d,e)$?” to “which sub-processes are pushing that position?” The vector
in @eq:strat-chart is unpacked into the nine operational families below.
[@langell2025_stratified].

- $m$ family: $m_a, m_e, m_o$.
- $d$ family: $d_n, d_l, d_s$.
- $e$ family: $e_e, e_s, e_m$.

The principal definitions collected from the Stratified MNPS manuscript are:

#math.equation(
  $ m_a = "SR" * "alpha_attn_mean" $
) <eq:ma>

#math.equation(
  $ m_e = "SR" * (max(z_L(w), 0))_W $
) <eq:me>

#math.equation(
  $ "SC"(w) = frac(sum_f f P(f,w), sum_f P(f,w)), quad
    m_o = frac("std"_W("SC"), "avg"_W("SC")) $
) <eq:mo>

#math.equation(
  $ H(t_h,w) = e^(- t_h L(w)), quad
    d_n = 1 - "norm"("avg"_W(frac("Tr"(H(t_h,w)), |V|))) $
) <eq:dn>

#math.equation(
  $ d_l = "avg"_W(C_i(w)) $
) <eq:dl>

#math.equation(
  $ d_s = "std"_u("proj"(b_u))
    quad "or" quad
    d_s = "avg"_W(1 - rho("RDM"(s), "RDM"(b(w)))) $
) <eq:ds>

#math.equation(
  $ e_e = frac(1, S) sum_(s = 1)^S "SampEn"_s $
) <eq:ee>

#math.equation(
  $ e_s = "H"_"perm"(phi, m_p, tau) $
) <eq:es>

#math.equation(
  $ e_m = z(frac("P"_"beta" + "P"_"gamma", "P"_"alpha" + "P"_"theta"))
    quad "or" quad
    e_m = z("avg"_W(E_g(w))) $
) <eq:em>

Interpretively:

- $m_a$ tracks attentional state-switch mobility.
- $m_e$ tracks affective or limbic mobility.
- $m_o$ tracks oscillatory flexibility.
- $d_n$ tracks network-level diffusivity via graph heat propagation.
- $d_l$ tracks local coupling or clustering.
- $d_s$ tracks representational spread or dispersion.
- $e_e$ tracks multiscale entropy.
- $e_s$ tracks phase-order entropy.
- $e_m$ tracks an efficiency or energetic proxy.

Several of these objects are explicitly tied to established signal-processing
families in the source paper: multiscale sample entropy for $e_e$
[@richman2000], graph connectivity measures such as wPLI or related phase
locking summaries for network-sensitive coordinates [@vinck2011; @lachaux1999],
and spectral-centroid variability for oscillatory flexibility
[@langell2025_stratified].

== Recomposition to 3D

The theoretical default is a robust recomposition. This is where the
stratified manuscript deliberately departs from naive averaging: if the 9D
chart exists to expose masked redistributions, recomposition back to 3D should
not reintroduce avoidable sensitivity to outliers or unstable subaxes
[@langell2025_stratified].

#math.equation(
  $ m = "robust_mean"(m_a, m_e, m_o), quad
    d = "robust_mean"(d_n, d_l, d_s), quad
    e = "robust_mean"(e_e, e_s, e_m) $
) <eq:robust-recompose>

with a weighted alternative

#math.equation(
  $ m = w_a m_a + w_e m_e + w_o m_o, quad
    d = w_n d_n + w_l d_l + w_s d_s, quad
    e = w_"ee" e_e + w_"es" e_s + w_"em" e_m $
) <eq:weighted-recompose>

under nonnegative weights summing to one within each family.

Equations @eq:robust-recompose and @eq:weighted-recompose make the
recomposition rule explicit: robustness is the default, while weighted
recomposition is an auditable alternative. Neither rule changes the fact that
the underlying measurements originate in the stratified chart.

The common statistical discipline across the papers is:

- compute inferences on within-subject robust z-values,
- reserve $[0,1]$ scaling for reporting and visualization,
- treat monotone transforms as preserving order but not absolute scale.

== Mapping from Latent Theory to Measurement

The stratified article and Churchland appendix propose schematic monotone
bridges from latent NDT quantities to measured coordinates. These are
legacy conceptual bridges, not identified NDT 1.0 estimators. They are useful
only when they prevent the measurement layer from floating free of the theory:
they make explicit how empirical feature families are supposed to stand in for
latent NDT quantities without claiming one-to-one identity
[@langell2025_stratified; @churchland1986; @churchland2005].

#math.equation(
  $ e_e(X_t) approx h_e(E(X_t)), quad
    e_s(X_t) approx h_s(r(X_t)), quad
    d_n(X_t) approx "norm"("Tr"(G_t(X_t))) $
) <eq:latent-bridges>

and, more qualitatively,

#math.equation(
  $ d_l(X_t) approx h_l(kappa(X_t)), quad
    m_o(t) approx "Var"_W("SC"(sigma(t))), quad
    m_a(t) approx h_a("precision pulses aligned to theta") $
) <eq:bridge-extensions>

These bridge functions are not themselves directly identified from data; they
formalize a monotone link between latent dynamics and measurement-layer
coordinates.

== NeuralManifoldDynamics as a measurement contract

NeuralManifoldDynamics (NMD) implements selected MNPS and local-dynamics
quantities through versioned preprocessing, feature construction, chart
projection, and estimator contracts. NMD is an operational measurement layer,
not NDT itself. The theory specifies latent $X_t$, the law $cal(L)$, the
transition kernels, and the questions asked of them; NMD specifies particular
observation charts, serialized paths, estimators, and validity diagnostics
[@langell2026_mndm].

The path and schema inventory below is an implementation snapshot and may be
ahead of the cited contract manuscript. In the nomenclature used here,
`mndm.dynamics` denotes Jacobian-derived local-dynamics surfaces, whereas
`mndm.dynamical_families` denotes the separate diffusion, destination, and
resilience families. Neither namespace identifies a latent biological process.

#math.equation(
  $ cal(X)_t = [m_t, d_t, e_t], quad
    cal(X)_t^((9)) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m] $
) <eq:operational-exports>

Equation @eq:operational-exports restates the chart families at the
measurement-contract boundary. The current release treats 3D coordinates as a
deterministic weighted projection of the 9D chart:

#math.equation(
  $ x_t = P_"fixed" x_t^((9)) $
) <eq:fixed-projection>

with one active EEG-style policy instance summarized as

#math.equation(
  $ m = 0.62 m_a + 0.55 m_e + 0.45 m_o $
) <eq:proj-m>

#math.equation(
  $ d = 0.50 d_n + 0.82 d_l + 0.28 d_s $
) <eq:proj-d>

#math.equation(
  $ e = 0.85 e_e + 0.62 e_s + 0.03 e_m $
) <eq:proj-e>

Equations @eq:proj-m, @eq:proj-d, and @eq:proj-e instantiate
@eq:fixed-projection for one policy. These coefficients are best read as one
explicit policy example, not as
universal modality-independent constants. In the implemented pipeline,
`mnps_3d` is produced by a deterministic config-resolved projection from
`coords_9d`: runtime configuration supplies a `v1_mapping`, feature-level
weights are mapped onto available 9D subcoordinates, and the projection is
renormalized over finite support when some subcoordinates are missing. The
result is still a fixed auditable linear contract within a run, but its exact
matrix may vary across modality or dataset policies [@langell2026_mndm].

The operational contract additionally fixes a serialized derivative
`mnps_3d_dot`, coverage-aware renormalization when subcoordinates are missing,
validity thresholds for local estimation, and explicit separation between
`mnps_3d` and `coords_9d`. The derivative is a chart-level estimator; it is not
automatically the latent drift $b$ in @eq:canonical-diffusion.

This release-fixed projection is not claimed to be the unique true ontology of
the manifold; it is an auditable measurement contract chosen to reduce silent
chart drift across analyses. In that sense the compendium distinguishes clearly
between a mathematical chart and a versioned export contract: the former is a
theoretical coordinate system, the latter is a reproducibility device.

The public reference implementation for this measurement layer is
`https://github.com/NoeticDiffusion/NeuralManifoldDynamics`. At the compendium
level this matters because the object being standardized is not merely a set of
names but a release-fixed ingest contract: feature normalization, coordinate
export, derivative serialization, local neighborhoods, local-dynamics families,
and validity diagnostics must be auditable before downstream claims can be
compared across datasets.

== Local-dynamics families in the contract

The local-dynamics surface is organized into two related groups. The first group
contains Jacobian-derived families built from the chart flow or from one-step
transition residuals:

- `mndm.jacobian_metrics.v1` stores chart-level metrics derived from
  `J_hat`, including spectral abscissa $alpha$, numerical abscissa $omega$,
  reactivity gap $Delta_"react" = omega - alpha$, symmetric-rate summaries,
  rotation, and stable-reactive flags.
- `mndm.finite_time_response.v1` propagates a declared local Jacobian field
  over finite horizons. Its peak-gain analogue is
  `g_peak_over_horizons`; it is a model-derived tangent-map summary, not a
  perturbational FAR measurement or a held-out predictor.
- `mndm.residual_covariance_proxy.v1` records a residual covariance proxy.
  Derivative-residual covariance is not the diffusion tensor $a$ and is not
  an admissible $W_Q$ without an explicit conversion contract.
- `mndm.stochastic_reachability.v1` is reserved for covariance propagation
  driven by admissible one-step transition innovation $W_Q$. No silent
  derivative-residual-to-$Q$ conversion is permitted, so this surface remains
  gated rather than implied by the presence of `J_hat`.

The second group is the separate `mndm.dynamical_families` surface:

- `mndm.diffusion_geometry.v1` estimates a chart-dependent increment-covariance
  object. It does not become an Itô tensor merely because it is called
  diffusion, and it does not establish drift--diffusion alignment when an
  independently qualified drift is absent.
- `mndm.committor.v1` represents destination or hitting-probability analyses.
  It requires declared competing regimes, disjoint support, sufficient
  independent segments, and an estimator qualification; stage labels alone
  are not committor truth.
- `mndm.finite_amplitude_resilience.v1` represents observed response to a
  finite perturbation. It requires a declared perturbation protocol and cannot
  be inferred from Jacobian, finite-time-response, or spontaneous-trajectory
  summaries.

The Jacobian surface is the operational counterpart of the chart derivative
defined in @eq:compendium-jacobian and estimated locally as
@eq:compendium-jhat. The diffusion and destination families instead refer to
the covariance and hitting-probability objects in @eq:compendium-diffusion and
@eq:compendium-committor; they are not derived automatically from a Jacobian.

The two groups must not be collapsed into one chain. In particular, FTR is not
FAR, a Jacobian residual is not $a$, and an NMD reachability export is not the
same object as a study-specific predictive-spread analysis.

== Implemented HDF5 surfaces

The canonical H5 write path serializes a measurement-layer contract rather than
the full theoretical stack. This matters because many downstream discussions
implicitly assume that every mathematically named object in the article family
already exists as a standard serialized dataset. The ingest-side revision makes
clear that this is not yet true: the H5 contract is narrower than the full
compendium, and that narrowing should be stated explicitly
[@langell2026_mndm].

On the main path the following objects are written as first-class datasets or
groups:

- root series `time`, `mnps_3d`, and `mnps_3d_dot`,
- feature surfaces `features_raw` and `features_robust_z`,
- optional alignment/support datasets such as `z`, `window_start`,
  `window_end`, `events/*`, and `nn/indices`,
- labels under `labels/stage` and additional `labels/*`,
- primary dynamics under `jacobian/J_hat`, `jacobian/J_dot`,
  `jacobian/centers`, and optional `jacobian/diagnostics/*`,
- stratified outputs under `coords_9d/values`, `coords_9d/names`, and
  optional `jacobian_9D/*`,
- Jacobian-derived surfaces under `jacobian/derived_metrics/v1`,
  `jacobian_9D/derived_metrics/v1`, `finite_time_response/v1/{primary,
  stratified_9d}`, `transition_residuals/v1/{primary,stratified_9d}`, and
  `transition_residual_covariance_proxy/v1/{primary,stratified_9d}`,
- gated `stochastic_reachability/v1/{primary,stratified_9d}` surfaces driven
  only by an admissible one-step innovation covariance,
- separate dynamical-family surfaces under
  `dynamical_families/{diffusion,destination,resilience}/v1` when their
  configuration and qualification gates are satisfied,
- optional supporting groups such as `extensions`, `regions`,
  `regional_mnps`, and `manifest_json`.

This implemented contract is deliberately narrower than the theoretical
compendium. Many paths are opt-in or gated, and a missing surface means
unavailable rather than measured zero. In particular, stochastic reachability
requires an admissible one-step transition covariance, committor requires
declared destinations and estimator qualification, and FAR requires a finite
perturbation protocol. All downstream inferences inherit raw-measurement,
preprocessing, feature, chart, and estimator validity limits.

Family groups may also carry explicit `computation_status`,
`measurement_validity`, and `claim_status` certificates. A computed value is
not thereby a valid regime inference, and a valid measurement is not a
biological claim. The operational contract does not promote these surfaces to
an `ndt_licensed` result.

= Cytoskeletal-Dendritic Accessibility Bridge

== Role in the Layer Stack

The cytoskeletal-dendritic accessibility model adds a microstructural layer
beneath MNPS without identifying dendrites with the noetic manifold itself. The
updated Slow Branch article makes the bridge simulator-first: a slow,
phenomenological branch variable $M_b$ is written by eligibility, replay, and
consolidation support, and is tested through memory-linking, perturbation, and
rescue signatures @langell2026_slow_branch. The restricted claim is that this
is an executable model-discrimination hypothesis, not an established
biological foundation or an additional premise required for macro-level MNPS
or local-dynamics inference. The current NDT evidence rests on the measurement
stack, chart-level local dynamics, and bounded empirical accessibility
analyses. Earlier C/TI/P summaries remain an optional reporting layer.

The layered dependency is:

- *Micro*: branch activity, fast access, eligibility traces,
  replay/consolidation support, and slow structural accessibility.
- *Meso*: a lower-dimensional accessibility geometry summarizing how branch
  support is distributed, concentrated, or canalised.
- *Chart*: provisional memory/accessibility coordinates, potentially 3D or
  stratified 9D, that can be analyzed with MNPS-style tools.
- *Macro*: local flow, MNJ structure, predictive-spread geometry, and optional
  regime reporting
  on the exported chart.

== Branch-resolved simulator state

Let $b$ index dendritic branches and $mu, nu$ index memory traces. The updated
simulator separates fast branch access from slow structural accessibility:

#math.equation(
  $ Z_t = {x_b(t), A_b^f(t), A_b^s(t), E_b(t), P_b(t), M_b(t),
    R_mu(t), L_(mu nu)(t)}_(b,mu,nu) $
) <eq:microstate-z>

Here $x_b(t)$ is fast branch activity, $A_b^f(t)$ is fast access,
$A_b^s(t)$ is slow access derived from $M_b(t)$, $E_b(t)$ is eligibility,
$P_b(t)$ is replay- and consolidation support, and $M_b(t)$ is the slow
structural accessibility variable. $R_mu(t)$ is trace-level recall support and
$L_(mu nu)(t)$ is a pairwise linking output. None of these variables is claimed
to be a direct molecular memory code.

The effective branch access factor is

#math.equation(
  $ A_b(t) = A_b^f(t) A_b^s(t) $
) <eq:access-factor>

This factorization is a gain-like simulator abstraction: fast cue and context
can open a branch momentarily, while $M_b$ biases how readily that opening is
stabilized or reused.

At the fast timescale, branch activity follows

#math.equation(
  $ tau_x dot(x)_b = -x_b + A_b(t)[I_b(t) + R_b(t)] $
) <eq:fast-access-dynamics>

where $I_b(t)$ is cue input and $R_b(t)$ is replay or recurrent recruitment.
Eligibility and consolidation support follow

#math.equation(
  $ tau_E dot(E)_b = -E_b + phi(x_b, I_b) $
) <eq:eligibility-dynamics>

and

#math.equation(
  $ tau_P dot(P)_b = -P_b + rho_"replay" r_b(t) + rho_nu nu(t) $
) <eq:consolidation-support>

respectively. Slow structural writing is then

#math.equation(
  $ dot(M)_b = eta E_b(t) P_b(t) W(t)(M_"max" - M_b)
    - lambda_M M_b + epsilon_b(t) $
) <eq:slow-structural-update>

The bounded term expresses finite local capacity, $W(t)$ is the replay or
writing window, $lambda_M$ captures structural decay, and $epsilon_b(t)$ is
structural noise. The update is phenomenological: it is an executable
model-discrimination rule, not a complete biochemical law.

For an individual trace and a pair of traces, the exported outputs are

#math.equation(
  $ R_mu(t) = sum_b a_(mu b) A_b(t) x_b(t) $
) <eq:recall-support>

and

#math.equation(
  $ L_(mu nu)(t) = sum_b a_(mu b) a_(nu b) M_b(t) $
) <eq:linking-output>

where $a_(mu b)$ describes the allocation of trace $mu$ to branch $b$. The
simulator's joint profile is overlap-branch writing, linking gain,
perturbation-sensitive loss, targeted rescue, and topology-dependent
specificity @langell2026_slow_branch. It does not establish that dendrites or
cytoskeletal structures directly store memory content.

== Export to Mesoscopic Accessibility Geometry

The bridge to NDT begins by exporting the branch-resolved microstate to a
mesoscopic memory/accessibility chart:

#math.equation(
  $ Psi: Z_t -> x_t^("mem") $
) <eq:psi-export>

Equation @eq:psi-export is the explicit micro-to-meso interface. On that
exported chart, one can define a local flow and Jacobian:

#math.equation(
  $ dot(x)_t^("mem") = f_"mem"(x_t^("mem"), t) + epsilon_t, quad
    J_t^("mem") = frac(partial f_"mem", partial x)(x_t^("mem"), t) $
) <eq:mem-flow-jacobian>

The local flow in @eq:mem-flow-jacobian can then be paired with the same
short-horizon reachability recursion used for the measurement chart:

#math.equation(
  $ Sigma_t^((h + 1)) = A_t Sigma_t^((h)) A_t^top + W_(Q,t) $
) <eq:mem-reachability>

The important boundary condition is that $Psi(Z_t)$ is an exported chart, not a
claim that the branch microstate literally is the noetic manifold. Structural
accessibility is hypothesized to shape the mesoscopic geometry that later
appears as MNPS, MNJ, or reachability structure, while the macro measurement
apparatus remains separable from any one molecular implementation. Until
branch-resolved perturbation data directly link changes in $Z_t$ or $M_b$ to
MNPS/MNJ/reachability shifts, this micro-to-NDT coupling remains speculative.

== Coupling to Macro Metrics and Potentials

Let $P$ be a projection from branch-level accessibility geometry into the
regional or global MNPS chart. As a hypothesis-level extension, structural
accessibility can enter macro geometry through effective mobility, diffusion,
and potential terms:

#math.equation(
  $ M_"MNPS"(X, Z) approx P^top M_"access"(Psi(Z)) P, quad
    a(X, t, Z) = a_0(X, t) + a_"access"(X, t, Psi(Z)) $
) <eq:access-metric-potential>

Equation @eq:access-metric-potential is not an identified biological law; it
specifies where a future branch-resolved perturbation experiment could test
the bridge.

In regional stratified notation, with regions $r,s$, chart coordinates
$alpha,beta$, and dendritic indices $a,b$:

#math.equation(
  $ M_"block"(r, s, alpha, beta; X, Z)
    approx sum_a sum_b
    attach(P, tr: r, br: (a, alpha))
    attach(M_"access"(Psi(Z)), br: (a, b))
    attach(P, tr: s, br: (b, beta)) $
) <eq:access-block-metric>

The corresponding drift split is

#math.equation(
  $ b(xi, t | c, Z) = -M(xi, t | c, Z) nabla V(xi, t | c, Z)
    + u_"nc"(xi, t | c, Z) $
) <eq:access-drift-split>

and the block-wise chart Jacobian is obtained by differentiating this full
drift, not by assuming a gradient-only flow:

#math.equation(
  $ hat(J)_(x,"block")(r, s, alpha, beta)
    = frac(partial hat(b)_(x,r,alpha), partial x_(s,beta)) $
) <eq:access-block-jacobian>

Equations @eq:access-block-metric and @eq:access-block-jacobian lift the same
hypothesis to regional family blocks. This is the compendium-level bridge from
micro to macro: slow
branch-level accessibility may alter effective mobility, diffusion orientation,
potential curvature, or transition gates, and those changes may then appear as
altered MNJ blocks or predictive-spread geometry. The biological connection
remains speculative until branch-resolved perturbation data identify it.

= Meta–Noetic Jacobian (MNJ)

== Definition

Empirical local flow is estimated on a declared measurement chart. Let
$hat(b)_x$ denote a chart-level drift estimate. The empirical Jacobian is

#math.equation(
  $ hat(J)_x(x,t) = frac(partial hat(b)_x(x,t), partial x) $
) <eq:compendium-jacobian>

The corresponding latent derivative is $nabla_xi b(xi,t)$. The term MNJ is
reserved for a Jacobian estimated in an MNPS chart; an unadorned empirical $J$
in this section means $hat(J)_x$ unless a latent argument is explicit. Equation
@eq:compendium-jacobian is the chart-level derivative used throughout this
section: it asks how nearby perturbations change under the local chart flow.
MNJ does not by itself describe state location, stochastic spread, destination
probability, or finite-amplitude resilience [@langell2025_mnj].

#math.equation(
  $ hat(J)_(i j),x(x,t)
    = frac(partial hat(b)_(x,i)(x,t), partial x_j) $
) <eq:compendium-jacobian-components>

For the base 3D chart,

#math.equation(
  $ hat(J)_x(x,t) = mat(
    (frac(partial hat(b)_(x,m), partial m), frac(partial hat(b)_(x,m), partial d), frac(partial hat(b)_(x,m), partial e)),
    (frac(partial hat(b)_(x,d), partial m), frac(partial hat(b)_(x,d), partial d), frac(partial hat(b)_(x,d), partial e)),
    (frac(partial hat(b)_(x,e), partial m), frac(partial hat(b)_(x,e), partial d), frac(partial hat(b)_(x,e), partial e))
  ) $
) <eq:compendium-mnj-matrix>

Equation @eq:compendium-mnj-matrix is the explicit 3D expansion of the
component definition @eq:compendium-jacobian-components. The symmetric and
antisymmetric parts are

#math.equation(
  $ S_x = frac(1,2)(hat(J)_x + hat(J)_x^top), quad
    Omega_x = frac(1,2)(hat(J)_x - hat(J)_x^top) $
) <eq:compendium-s-omega>

where $S_x$ captures symmetric expansion and shear, while $Omega_x$ captures
an antisymmetric rotational component. Thus @eq:compendium-s-omega decomposes
the same chart Jacobian; it does not introduce a second local flow. Neither
component should be interpreted as a unique biological mechanism.

== Modal growth and reactivity families

The current local-dynamics vocabulary keeps modal stability and instantaneous
reactivity separate:

#math.equation(
  $ alpha(J) = max_i Re[lambda_i(J)] $
) <eq:compendium-alpha>

#math.equation(
  $ omega(J) = lambda_"max"((J + J^top) / 2) $
) <eq:compendium-omega>

#math.equation(
  $ Delta_"react"(J) = omega(J) - alpha(J) $
) <eq:compendium-reactivity-gap>

Equations @eq:compendium-alpha and @eq:compendium-omega define the two
summaries, and @eq:compendium-reactivity-gap records their difference. The
spectral abscissa $alpha$ is the dominant modal growth or decay rate.
The numerical abscissa $omega$ is the maximal instantaneous growth rate. Thus
$alpha < 0$ and $omega > 0$ can coexist: all eigenmodes decay while some
perturbations initially grow. The reactivity gap is a derived, non-normality-
sensitive summary of this separation, not a complete non-normality measure.
The trace, spectral radius, Frobenius norm, rotation norm, and Henrici
departure are additional summaries, not substitutes for $alpha$ or $omega$.

Finite-time amplification is a separate family. A peak gain
$G_"peak"(T)$ is computed from a local propagator over a declared horizon and
does not follow from an instantaneous eigenvalue summary. Truth-known simulator
recovery of $alpha$, $omega$, and $Delta_"react"$ under restricted linear
systems is a methodological qualification; it is not empirical chart or
biological validation [@langell2026_mndm].

== Local Linear Estimation

The empirical MNJ estimator is based on a local linear flow model. A
neighbourhood-wise fit over a declared chart and short analysis window takes
the form [@langell2025_mnj; @hoerl1970_ridge; @ljung1999_sysid]

#math.equation(
  $ dot(x) approx A(x - x_"ref") + b_x $
) <eq:compendium-local-linear>

with

#math.equation(
  $ hat(J)_x = A $
) <eq:compendium-jhat>

The fitted matrix in @eq:compendium-local-linear is identified with the
Jacobian estimate by @eq:compendium-jhat. In the NMD contract this is a
chart-level estimate, typically regularized over
local neighbours or short super-windows. The serialized `mnps_3d_dot` is an
input or derivative surface, not by itself an independently identified
latent drift. A temporal difference of $J$ is likewise not automatically the
latent derivative $dot(J)$.

For discrete-time maps one also uses the continuous/discrete relation

#math.equation(
  $ J_d = e^(J_c Delta t), quad
    J_c approx frac(J_d - I, Delta t) $
) <eq:compendium-jc-jd>

Equation @eq:compendium-jc-jd relates discrete and continuous local operators
only in the small-$Delta t$ regime, subject to the declared sampling and model
contract.

== Conditional relation to potential curvature

If the drift split in @eq:compendium-drift-split is declared and $M$ is
locally constant, the potential component contributes a Hessian-shaped term.
In the general state-dependent case, differentiating

#math.equation(
  $ b = - M nabla V + u_"nc" $
) <eq:compendium-gradient-drift>

gives schematically

#math.equation(
  $ J_b = - M nabla^2 V - (partial M) nabla V + partial u_"nc" $
) <eq:compendium-mnj-hessian>

where $(partial M) nabla V$ denotes the collection of mobility-variation
terms. Therefore

#math.equation(
  $ J approx - M nabla^2 V $
) <eq:compendium-constant-m-approx>

is only a conditional approximation. Chart Jacobian asymmetry does not by
itself identify $u_"nc"$ because state-dependent mobility can also produce it.

== 9D Jacobians and Family Blocks

On the stratified chart the Jacobian becomes a $9 times 9$ local linearization.
The $m$, $d$, and $e$ coordinate families can be grouped into a $3 times 3$
family-block matrix, as shown in @eq:compendium-block-j:

#math.equation(
  $ J^((9)) = mat(
    J_("m","m"), J_("m","d"), J_("m","e");
    J_("d","m"), J_("d","d"), J_("d","e");
    J_("e","m"), J_("e","d"), J_("e","e")
  ) $
) <eq:compendium-block-j>

where each $J_("out","in") in RR^(3 times 3)$ describes how in-family variation
drives out-family rates of change. This block view is useful when global 3D
coordinates appear unchanged but mechanism-specific subcoordinates redistribute.
The blocks are chart-level summaries and do not establish anatomical coupling.

= Geometry of Possible Futures and Local Capacity

== Local Stochastic Linearization

Stochastic short-horizon reachability formalizes how probability mass spreads
around a state over a finite horizon, rather than describing the state’s
current location alone. It is a covariance-based approximation to predictive
spread under the chart-conditional law @eq:compendium-kernel-chart, not
classical control-theoretic reachability and not a structural-connectome
Gramian. A local discrete-time model is
[@kalman1959_control; @kurzhanski1996_ellipsoidal].

#math.equation(
  $ x_(t + 1) = A_t x_t + b_t + epsilon_t, quad
    epsilon_t tilde (0, W_(Q,t)) $
) <eq:compendium-reachability-model>

In @eq:compendium-reachability-model, $A_t$ and $b_t$ are estimated locally in
chart-space neighbourhoods and $W_(Q,t)$ is an admissible one-step
transition-innovation covariance. MNPS asks
where the system is, MNJ asks how the local chart flow transforms nearby
states, and this family asks how finite-horizon predictive mass spreads.
Condition mixtures or poorly qualified residuals can inflate $W_Q$ without
establishing richer controllable geometry.

== Covariance Recursion and Reachable Sets

The reachability covariance is initialized and propagated by

#math.equation(
  $ Sigma_t^((0)) = 0, quad
    Sigma_t^((h + 1)) = A_t Sigma_t^((h)) A_t^top + W_(Q,t) $
) <eq:compendium-reachability-recursion>

Equation @eq:compendium-reachability-recursion propagates the covariance from
the one-step model @eq:compendium-reachability-model. The corresponding
predictive-spread ellipsoid at horizon $h$ is

#math.equation(
  $ cal(E)_t^((h))(alpha)
    = { z | z^top (Sigma_t^((h)))^(-1) z <= alpha } $
) <eq:compendium-ellipsoid>

These objects may be reported at fixed horizons or aggregated across several
horizons into a tube summary. They describe second-moment spread under a local
linearization, not the support of every admissible control. Horizon choice,
neighbourhood leakage, and innovation-residual quality are validity conditions.
An NMD reachability surface is therefore gated and is not implied by the
presence of a chart or Jacobian.

== Primary Cone Metrics

Let $lambda_1 >= dots >= lambda_d$ denote the eigenvalues of $Sigma_t^((h))$.
The primary metrics are:

#math.equation(
  $ "Vol"_t^((h)) = frac(1,2) log(det(Sigma_t^((h)))) $
) <eq:compendium-cone-vol>

#math.equation(
  $ kappa_t^((h)) = frac(lambda_1, lambda_d + epsilon) $
) <eq:compendium-cone-kappa>

#math.equation(
  $ d_("eff"),t^((h)) = frac((sum_i lambda_i)^2, sum_i lambda_i^2) $
) <eq:compendium-cone-deff>

For rotation, the cone article recommends a robust discrete proxy. If
$A_t = W Sigma V^T$ is the SVD of $A_t$, define $U_t = W V^T$ and

#math.equation(
  $ rho_t^("A") = scripts(norm(frac(U_t - U_t^T, 2)))_"F" $
) <eq:compendium-cone-rotation-a>

When a stable continuous-time MNJ exists, the optional Jacobian-based rotation
summary is

#math.equation(
  $ rho_t = scripts(norm(frac(J_t - J_t^T, 2)))_"F" $
) <eq:compendium-cone-rotation-j>

The minimal persistence formalization is expressed on a tube metric
$V_t = "tube_log_det"(t)$:

#math.equation(
  $ tau_"rec"(t)
    = inf_(Delta t > 0) { Delta t : V_(t + Delta t) >= V_"rec" } $
) <eq:compendium-cone-persistence>

with thresholds defined relative to a baseline quantile of the tube-volume
series. Taken together, these metrics decompose capacity into size, directional
concentration, effective rank, rotational structure, and recovery dynamics
[@kalman1959_control; @kurzhanski1996_ellipsoidal; @tikhonov1977_illposed;
@higham2002_accuracy; @noble2021_reliabilityguide].

== Secondary Cone Metrics

The reachability manuscript also defines two useful secondary summaries:

#math.equation(
  $ p_i = frac(lambda_i + epsilon, sum_j lambda_j + d epsilon), quad
    H_"dir" = - sum_i p_i log(p_i), quad
    tilde(H)_"dir" = frac(H_"dir", log(d) + epsilon) $
) <eq:compendium-directional-entropy>

#math.equation(
  $ r_"vol"(t) = exp("tube_log_det"(t) - "tube_log_det"(t - 1)) $
) <eq:compendium-transport-ratio>

Directional entropy summarizes how evenly reachability mass is distributed
across directions; the transport ratio summarizes local expansion or shrinkage
between adjacent windows.

== Interpretation Discipline

The cone layer is explicitly capacity-focused. It is not a direct predictor of
where the system will go, nor is it identical to occupancy, entropy, or speed.
The most important synthesis rule from the source papers is:

- occupancy and reachability can dissociate,
- traversability and reachability are related but not identical,
- heteroskedastic innovation covariance $W_(Q,t)$ can inflate cones without implying
  richer controllable geometry,
- horizon dependence and neighborhood leakage must be treated as validity
  conditions, not as afterthoughts.

== Committor geometry

For competing destinations $A$ and $B$, the committor is

#math.equation(
  $ q_(A B)(x) = P_x(tau_B < tau_A) $
) <eq:compendium-committor>

It is a path-dependent hitting probability and therefore destination geometry,
not local expansion, diffusion volume, or traversability. Empirical use
requires explicit disjoint destinations, independent segments reaching both
regimes, a reaction-coordinate contract, and estimator qualification. Stage
labels alone are not committor truth. Finite-sample two-dimensional recovery is
not a currently validated NMD export; `mndm.committor.v1` remains a gated
schema or adapter rather than a claim of committor identification
[@e2010transition; @metzner2009transition; @klus2018data].

== Attractors and finite-amplitude resilience

Attractors and basins describe longer-time organization: locations, boundaries,
metastability, escape, and preferred corridors. A visual cluster is not by
itself evidence for an attractor. Finite-amplitude resilience (FAR) asks how
large a declared perturbation the system can tolerate before leaving its
dynamical regime. It requires an observed perturbation protocol and amplitude
family. Local Jacobian stability, finite-time tangent gain, and spontaneous
trajectory variation cannot substitute for that protocol.

= Optional C/TI/P Regime Reporting

This section preserves an earlier regime-reporting layer in the article family.
It is not one of the core local-dynamics families in the current NDT article
and it must not be collapsed into a consciousness scalar.

The revised Churchland synthesis adds a regime-classification layer above MNPS,
MNJ, traversability, and reachability. The point is to avoid replacing one
scalar consciousness marker with another. Entropy, occupancy, speed, and local
capacity can all be informative, but none is sufficient on its own. The
relevant object is a three-axis regime geometry:

- *Capacity collapse (C)*: reduced local accessibility, traversal speed,
  reachability volume, effective dimensionality, rotational structure, or
  adaptive availability.
- *Transport-innovation balance (TI)*: whether low capacity remains
  innovation-dominated or becomes captured by local transport dynamics.
- *Pathological lock-in (P)*: whether the regime is rigid, canalised, and
  asymmetrically deformative in a pathology-like way rather than simply
  physiologically constrained.

In compact notation, define a regime descriptor

#math.equation(
  $ R_t^("CTIP") = (C_t, "TI"_t, P_t) $
) <eq:ctip-state>

Equation @eq:ctip-state defines the reporting tuple; each component is computed
from families of reported summaries rather than from a single privileged
scalar. A minimal operational reading is:

#math.equation(
  $ C_t = cal(C)("speed", "tube_log_det", d_"eff", rho), quad
    "TI"_t = cal("TI")("Q-ratio", "CaptureGate", "MDR"), quad
    P_t = cal(P)("ACI", "CFCA", "asymmetry") $
) <eq:ctip-components>

Equation @eq:ctip-components gives one compact decomposition of the three
components in @eq:ctip-state. The exact functions $cal(C)$, $cal("TI")$, and
$cal(P)$ are contract-level
reporting maps, not universal constants. Their role is to force every reduced
state claim to say whether it is reporting capacity loss, transport capture,
pathological deformation, or some mixture of the three.

== Core Regime Dissociation

The present article family uses sleep, propofol, and epilepsy as the main
stress test for the C/TI/P layer:

#figure(
  kind: table,
  supplement: "Table",
  clean-table(
    columns: (1fr, 1.25fr, 1.25fr, 1.25fr),
    align: (left, left, left, left),
    inset: 5pt,
    header: (
      [*Regime*],
      [*C: capacity*],
      [*TI: transport/innovation*],
      [*P: lock-in*],
    ),
    [Deep NREM sleep], [Low capacity relative to wake/REM],
      [Comparatively innovation-dominated in current analyses],
      [Weak or non-significant pathological lock-in],
    [Propofol], [Capacity separation, strongest for awake vs sedated],
      [No clean corrected transport-capture profile in present dose range],
      [No clean corrected pathological-lock profile],
    [Ictal epilepsy], [Strong collapse in speed, cone volume, and effective dimensionality],
      [Transport capture via lower `Q-ratio_H4` and higher `CaptureGate`],
      [Reachability-canalisation and cross-family coupling asymmetry increase],
  ),
  caption: [Core regime dissociation across capacity, transport/innovation, and pathological lock-in.],
) <tab:ctip-dissociation>

The rows in @tab:ctip-dissociation are a reporting matrix, not a new dynamical
family.

The key conclusion is not that capacity is irrelevant. It is that capacity
collapse is underdetermined. Deep sleep, propofol sedation, and ictal epilepsy
can all reduce local availability, but they do not imply the same biological or
consciousness-relevant state unless TI and P are also reported.

This distinction also resolves a potential anisotropy ambiguity. `ACI` in the
C/TI/P layer denotes reachability-canalisation: whether short-horizon reachable
futures concentrate into a narrow subset of directions. This is distinct from
dispersion of local Jacobian eigenvalues. A seizure regime can therefore show
uniformly contractive local Jacobian spectra while still exhibiting high
reachability-canalisation among the few futures that remain locally admissible.

= Traversability, Extensions, and Modality Boundaries

== Traversability Index

The Churchland paper packages speed and anisotropy into an operational
TraversabilityIndex:

#math.equation(
  $ T = v dot (1 - A_"norm") $
) <eq:traversability>

Equation @eq:traversability combines speed and normalized anisotropy, with
cohort-relative normalization

#math.equation(
  $ A_"norm" = frac(A - A_"min", A_"max" - A_"min") $
) <eq:anorm>

as defined in @eq:anorm. Low traversability can therefore arise from slow
motion, strong canalization,
or both. For this reason the compendium treats $T$ as a compact diagnostic, not
as a substitute for explicit Jacobian or reachability geometry. Its real value
in the article family is comparative: it gives a one-line summary that can be
reported alongside richer dynamical objects without pretending to replace them.

== Jump-Diffusion Extension

Several manuscripts sketch an enriched controlled dynamics with rare
discontinuous events:

#math.equation(
  $ d X_t = b(X_t,t | c_t) d t + Sigma(X_t,t | c_t) d W_t
    + integral_(RR^d) kappa(X_(t^-), z) tilde(N)(d t, d z) $
) <eq:jump-diffusion>

Equation @eq:jump-diffusion extends the backbone in
@eq:canonical-diffusion with a jump measure. This extension is kept secondary:
it can model abrupt regime shifts, spikes, or other rare transitions without
replacing the controlled-diffusion backbone.

== Modality-Specific Identifiability

The theoretical framework is modality-general, but its empirical second-order
layer is not equally identifiable across modalities:

- EEG and iEEG can support first-order and second-order estimation when the
  chart, sampling, residual quality, and neighbourhood contract are adequate;
  availability does not establish operator validity.
- fMRI generally resolves first-order geometry more reliably than second-order
  flow. MNJ and predictive-spread analyses in BOLD are boundary-condition
  probes that demand stronger validity checks.

This asymmetry is a core cross-paper discipline: weak or near-null second-order
effects in fMRI should not be overinterpreted as either strong confirmation or
strong falsification of the framework.

= Compact Synthesis

The formal dependency structure of the article family can be summarized as:

1. A latent stochastic process evolves on $cal(M)$ as a controlled diffusion
   (Eqs. @eq:canonical-diffusion–@eq:compendium-kernel-chart).
2. Measurements $Y_t$ are mapped into a base or stratified chart
   (Eqs. @eq:obs-model–@eq:proj-e).
3. Local chart derivatives define MNJ and its modal or reactivity summaries
   (Eqs. @eq:compendium-jacobian–@eq:compendium-block-j). When the
   cytodendritic bridge is active,
   branch-level accessibility can enter through exported metric/potential terms
   (Eqs. @eq:microstate-z–@eq:access-block-jacobian).
4. Local diffusion and one-step innovations define gated covariance propagation
   and short-horizon predictive-spread geometry
   (Eqs. @eq:compendium-diffusion–@eq:compendium-reachability-recursion).
5. Committor, attractor, and FAR families address destination, long-time, and
   finite-amplitude questions under separate protocols.
6. Candidate controls act on drift, diffusion, mobility, or transition gates;
   RVC is only the isotropic variance-control special case.
7. Optional C/TI/P and traversability summaries report combinations of these
   layers without replacing them.

Within this unified view, the family of papers converges on one central claim:
conscious-state analysis is not adequately described by entropy, coherence, or
position alone. The mathematically relevant objects are the joint structure of
state coordinates, local laws, diffusion geometry, chart derivatives,
finite-horizon predictive spread, destination geometry, and conditional
access control. Put slightly differently, the current article becomes more
informative as it moves from state location to local law, to non-equivalent
future-law families, and then to the controls that can reshape them
[@langell2025_6; @langell2025_stratified; @langell2025_mnj; @langell2026_mndm].

= Acknowledgements


This work emerged through structured correspondence among human and AI
collaborators; large language models (GPT‑5.4, Claude 4.6 Sonnet, Gemini 3.1 Pro) assisted in literature synthesis, drafting, peer review and editorial refinement.

= Contact

Robin Langell — hello(at)noeticdiffusion.com

= Licensing

This manuscript provides only a brief licensing summary; full terms and
conditions are available via the Mychainos multi‑layer licensing framework
(`https://noeticdiffusion.com/license.html`). In short, the conceptual content is released
under CC BY‑SA 4.0, software under GPLv3, and relevant hardware/biological
artifacts under open hardware/biological licences (for example, CERN OHL v2 and
OpenMTA). Unified ethical guardrails apply: no coercive, military, or
surveillance applications; no patenting or black‑boxing of core methods; and
derived works should remain accessible, attributed, and shared with care.

= Data and Code Availability

Reference implementation for the measurement layer:
`https://github.com/NoeticDiffusion/NeuralManifoldDynamics`

Related Noetic Diffusion repositories and manuscript sources:
`https://github.com/NoeticDiffusion/`

= Trademark Notice

Certain terms used in this manuscript (including Noetic Diffusion, Noetic
Diffusion Theory, Noetic Diffusion Mapping, Noetic Diffusion Health Index,
and Noetic Atlas) are used as project names and are the subject of ongoing
trademark applications. A concise description of the stewardship rationale,
current registration status, and how this interacts with open scientific use is
available at `https://noeticdiffusion.com/license.html`. These trademark aspects
do not affect the scientific content, reproducibility, or licensing of the
methods described here.

#pagebreak()

#bibliography("compendium_ndt.bib")
