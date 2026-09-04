// Noetic Diffusion Theory — Typst version (work in progress)
// Converted from LaTeX, section by section.

#import "template_eLife.typ": elife-template

#show: doc => elife-template(
  title: [
    Noetic Diffusion Theory: A Rhythmic, Geometric Framework for Neural
    State Reconstruction and Conscious Correlates
  ],
  authors: [Robin Langell],
  affiliations: [Independent Researcher],
  correspondence: [Robin Langell — hello(at)noeticdiffusion.com],
  contributor_notes: [
    #align(center)[
      #text(size: 9pt)[
        Version 0.8 · 10.5281/zenodo.20112950 ·
        #datetime.today().display("[month repr:long] [day], [year]")
      ]
    ]
  ],
  page-margin: (
    left: 3cm,
    right: 3cm,
    top: 2.5cm,
    bottom: 2.5cm,
  ),
  body-size: 10.5pt,
  body-leading: 0.8em,
  body-spacing: 0.6em,
  heading-numbering: "1.",
  styled-headings: true,
  doc,
)

// Local override (this file only): the shared template's default equation
// supplement is "Equation", which duplicates the word when prose already
// writes "Eq. @label" (producing "Eq. Equation (N)"). Suppressing the
// supplement here keeps "Eq. @label" reading as "Eq. N".
#set math.equation(supplement: none)

#v(0.8em)

#heading(level: 1, numbering: none)[Abstract]

We present Noetic Diffusion Theory (NDT) as a testable framework for neural
state dynamics: conscious-state correlates are modeled as time-resolved
denoising on a learned geometric manifold. The Meta–Noetic Diffusion Model
(MNDM) formalizes this process as a guided stochastic differential equation with
a rhythmic variance schedule, and Rhythmic Variance Control (RVC) links that
schedule to measurable neural rhythms. The core empirical target is not a
complete theory of subjective experience, but a constrained set of dynamical
signatures that can be tested in neural recordings.

To make the framework measurable, we define the Meta–Noetic Phase Space (MNPS)
as the canonical Stage-1 coordinate system; optional Noetic Atlas readouts are
specified in Appendix @sec:noetic-atlas. The first-stage analysis focuses on
three primary claims: event-locked entropy changes around
slow-oscillation–spindle complexes, sleep-stage transformations in MNPS topology
(NREM centralization and REM expansion), and bounded disorder-related geometry
contrasts that must survive preregistered multiverse controls. A composite
Noetic Diffusion Health Index (NDHI) is retained only as an exploratory
visualization and summary index, not as a clinical biomarker or consciousness
score.

The article therefore offers a staged research program: a minimal dynamical
model, a reproducible measurement layer, explicit null models, and falsifiable
public-dataset tests. Speculative extensions—embodied anchoring, detailed TRN
biophysics, landscape learning, second-order Jacobian analyses, reachability,
and clinical translation—are treated as appendices or follow-on work rather
than prerequisites for the core NDT claim.

#v(1.5em)

= Scope and Epistemic Status

NDT provides a mechanistic framework for neural dynamics associated with
conscious-state reports, but we carefully distinguish three levels of claim:

*Strong claims (empirically testable):*

- Neural rhythms (theta–gamma PAC, SO–spindle coupling) implement variance
  scheduling that produces measurable entropy dynamics.
- Manifold topology in Meta–Noetic Phase Space (MNPS) systematically varies
  with sleep stage, task context, and some clinical contrasts.
- Null models without event-locked variance scheduling should fail to reproduce
  the strongest rhythmic and topological signatures.

*Moderate claims (hypothesized correlations):*

- These neural geometric signatures correlate with reported conscious states
  (presence, clarity, embodiment).
- First-person phenomenology is hypothesized to exhibit structure (pulsed
  quality, discrete epochs) aligned with neural rhythmic events.
- Clinical groups may show characteristic manifold deformations, but these are
  treated as bounded, dataset-specific hypotheses rather than diagnostic
  categories.

*Speculative claims (philosophical):*

- The geometric flow described by MNDM may be constitutive of consciousness
  (experience is the intrinsic character of rhythmic denoising).
- This constitutive hypothesis does not generate empirical predictions beyond
  those of the correlational dynamical model; it is a metaphysical stance on
  what the already-specified denoising dynamics amount to. All concrete
  predictions in this manuscript bear on the presence or absence of the
  denoising/geometric signatures themselves; if those are supported, one may
  choose to read them either in a purely correlational or in a more
  constitutive spirit, but no behavioural or neural test uniquely adjudicates
  between these readings.

*Extension-status rule.* Later NDT work includes synthetic recoverability
audits, subsystem hypotheses, and measurement-layer companion analyses. These
have distinct evidentiary roles: a truth-known simulator can validate an
estimator under its frozen synthetic contract without validating an empirical
MNJ; an observational body--brain association can constrain EAP without
identifying causal entrainment; and a circuit proposal remains a hypothesis
until its own causal test succeeds. We do not promote any of these extensions
to the Stage-1 claim set by inclusion in this article.

Throughout, we use "conscious state reconstruction" as shorthand for "neural
dynamics exhibiting systematic correlates with conscious states." The hard
problem of why any neural process is accompanied by subjective experience
remains unaddressed.

#v(1.5em)

= Introduction

This paper introduces a formal, testable account of how neural systems may
rhythmically alternate between exploration and denoising, and how those dynamics
become visible as geometric structure in neural state space. We use Noetic
Diffusion Theory (NDT) as the scientific umbrella, the Meta–Noetic Diffusion
Model (MNDM) as the mathematical core, and the Meta–Noetic Phase Space (MNPS)
as the measurement layer. Here, "noetic" denotes
knowledge-bearing or intelligible structure: latent neural states whose
organization can be measured in a principled way. Our framing complements
predictive coding/active inference perspectives @friston2010 @clark2013 and
draws on neurophilosophical accounts of state-space representation
@churchland1986 @churchland1990 @churchland2005 and real patterns @dennett1991.

#quote(block: true)[
  *When you wake from a dream, the world reconstructs itself in seconds.
  Chaotic imagery resolves into your bedroom; formless unease crystallizes
  into the memory of today's deadline. This transition—from noise to
  meaning—is neither instantaneous nor continuous, but iterative, rhythmic,
  and geometrically structured.*
]

The motivating phenomenological intuition is that some conscious episodes may
feel like progressive reconstruction: vague, noisy structure becomes a usable
world model over short time windows. This intuition motivates the language of
denoising, but the core tests in this manuscript are third-person dynamical
tests: event-locked entropy, MNPS topology, recurrence, and model comparison
against non-rhythmic nulls. First-person anchoring, embodiment, and high-
resolution neurophenomenology are treated as Tier-2 extensions rather than
requirements for the initial validation of NDT.

Reading guide. Readers mainly interested in the formal core can focus on
Section "The Meta–Noetic Diffusion Model (MNDM)", the RVC section, and the
Predictions/Identifiability sections. Readers planning empirical analyses should
prioritize the MNPS methods and public-dataset plan. The appendix collects
extensions that are useful for later work but not required for the core claim:
embodied anchoring, TRN biophysical detail, landscape learning, and related
theory comparisons.

#figure(
  image("figures/fig1_mndm_core_flow.svg", width: 100%),
  caption: [
    Core NDT flow. Rhythmic control $r(t)$ modulates the variance schedule
    $sigma(t)$, which gates denoising and exploration in the MNDM state
    trajectory. MNPS then supplies the Stage‑1 measurement chart used for
    empirical tests.
  ],
)

= The Meta–Noetic Diffusion Model (MNDM)

Intuition. The brain maintains a noetic state $X$ that balances exploration
(maintaining uncertainty to sample alternatives, consider possibilities)
against coherence (collapsing uncertainty into stable, actionable meaning).
Too much exploration yields confusion; too much coherence yields rigidity.
Rhythms set when to explore vs. cohere, implementing a dynamic schedule that
navigates this trade-off. The MNDM formalizes this as a guided diffusion on a
learned potential landscape $F$ (acquired through development and experience):
trajectories descend where meaning is strong, pause or re-explore when rhythms
loosen variance, and re-stabilize when variance tightens. We now formalize this
intuition mathematically, beginning with a minimal system capturing the
essential dynamics.

== Minimal formulation

We begin with a minimal, citable system capturing the essence of time-resolved
denoising modulated by rhythm before introducing the full extended potential.
Three ingredients define it: a diffusion equation for the noetic state, a
potential trading off disorder against coherence, and a rhythm-gated variance
schedule.

*State update.* The noetic state $X_t$ descends a potential $F$ under
rhythm-gated noise:

#math.equation(block: true,
  $ d X_t = - nabla F(X_t, t) d t + sigma(t) d W_t $
) <eq:min-mndm>

*Minimal potential.* $F$ trades off disorder against coherence, using the
same $(m, d, e)$ coordinates as the MNPS measurement chart (see the notation
snapshot below):

#math.equation(block: true,
  $ F_min(X) = e(X) - m(X) $
) <eq:min-mndm-potential>

*Variance schedule.* Rhythmic control $r(t) in [0,1]$ gates the diffusion
variance between a floor $sigma_min$ and a ceiling $sigma_min + sigma_0$:

#math.equation(block: true,
  $ sigma(t) = sigma_min + sigma_0 (1 - r(t)) $
) <eq:min-mndm-sigma>

Here $e$ measures disorder (for example, entropic complexity), $m$ measures
rhythmic coherence/structure, and $W_t$ is Brownian motion (modeling fast
fluctuations as isotropic noise for tractability, though biological noise is
likely colored and signal-dependent). In this minimal case, $F$ has no
explicit time dependence (though $X_t$ evolves); the extended formulation
(Eq. @eq:ext-mndm) will add time-varying schedules. The minimal SDE mirrors
score-based diffusion formalisms in machine learning @song2021 @ho2020,
adapted here with a biologically grounded variance schedule.

*Notation snapshot (minimal vs. extended potential and MNPS axes).* Throughout
the manuscript we keep the MNPS axes in the unified notation $(m, d, e)$, where
$e$ is an entropy/disorder coordinate, $m$ is a mobility / rhythmic-coherence
coordinate, and $d$ is a diffusivity / deviation-from-metastability coordinate.
In older drafts these same feature-families were denoted $(E, R, D)$; here we
use $(m, d, e)$ throughout for consistency across manuscripts.

We use two closely related forms of the noetic potential:
$F_min(X) = e(X) - m(X)$ in the minimal model (Eq. @eq:min-mndm-potential) and
$F(X, t) = alpha(t) e(X) - beta(t) m(X) + gamma(t) d(X) - delta(t) Phi(t)$
in the extended model (Eq. @eq:ext-mndm-potential). The 3D MNPS chart $(m, d, e)$ is
defined at the measurement layer irrespective of which terms currently enter
the potential; in the strict minimal MNDM we can view the dynamics as evolving
in the $(m, e)$ subspace (with $gamma = 0$) while still tracking $d$ as an
additional diagnostic coordinate. When we compare minimal and extended models
empirically, we therefore treat the minimal model as a 2D projection of the
full $(m, d, e)$ manifold that ignores feedback from $d$ into $F$ but allows
its geometry to be measured.

Intuitively, when rhythmic control $r(t)$ is *high* (for example, during a
theta–gamma burst or SO–spindle complex), variance $sigma(t)$ is *low*, making
denoising aggressive—the system descends $F$ rapidly. When $r(t)$ is *low*
(between rhythmic events or during REM), variance $sigma(t)$ is *high*,
enabling exploration—the system can climb $F$ to escape poor local minima or
sample alternatives. This anti-phasic relationship (high $r$ versus low
$sigma$) is the core of rhythmic variance control, conceptually analogous to
precision scheduling in inference and noise schedules in diffusion models
@song2019.

*Limiting cases.* If $r(t) equiv 1$ (constant maximal rhythm), $sigma(t) ->
sigma_min$ and the system approaches (near-)deterministic gradient descent on
$F$. If $r(t) equiv 0$ (no rhythmic control), $sigma(t) = sigma_min + sigma_0$
is maximal and the system performs largely unguided exploration. Healthy
cognition requires $r(t)$ to *vary*, alternating denoising and exploration.

=== Note on pathological extremes (the Grand Mal boundary) <sec:grand-mal>

A critical limitation of the minimal potential $F_min = e - m$ is that it can
mistake low entropy plus high rhythmic structure for successful denoising. Taken
to its logical extreme, a generalized tonic-clonic seizure—with hypersynchronous
high-amplitude oscillations and reduced signal complexity—could look like a
maximally coherent state. This is phenomenologically false and clinically
absurd.

The resolution is to treat the minimal model as a *physiological-corridor*
approximation, not as a complete regime classifier. As Churchland (1986, 1995)
emphasizes, awareness requires functional differentiation as well as
integration @churchland1986 @churchland2005. Later NDT work makes the same point
operationally: reduced capacity must be decomposed into capacity collapse,
transport-innovation balance, and pathological lock-in rather than collapsed
into a single scalar @langell2026_capacity_unconsciousness. A seizure-like
regime is not merely "low entropy"; it is transport-captured, canalized, and
pathologically locked.

The extended potential therefore includes the deviation term $d(X)$ (Eq.
@eq:ext-mndm-potential), which penalizes departures from an integration-segregation
corridor. In the full model, meaningful coherence is metastable and
traversable; pathological hypersynchrony is a degenerate attractor outside the
valid operating range of Minimal-MNDM.

*Term-by-term interpretation.*

#block(width: 100%, breakable: true)[
  #table(
    columns: (auto, 1fr, 1fr),
    inset: 8pt,
    align: horizon,
    stroke: none,
    table.header(
      [*Symbol*], [*Neurobiological interpretation*], [*Empirical signature*],
    ),
    [$X_t$], [Noetic state (latent neural/phenomenal configuration)],
      [High-dimensional neural activity (EEG/fMRI)],
    [$e(X)$], [Disorder/uncertainty],
      [Spectral entropy, sample entropy, Lempel–Ziv complexity],
    [$m(X)$], [Mobility / rhythmic coherence/structure],
      [PAC, PLV/wPLI, spectral power in bands],
    [$F(X)$], [Noetic potential ($e - m$)],
      [Composite: $e$ minus normalized $m$],
    [$r(t)$], [Rhythmic control (theta, SO–spindle)],
      [Power envelope of theta/SO, spindle density],
    [$sigma(t)$], [Effective variance schedule],
      [$sigma_0 (1 - r(t))$, estimated from $r(t)$],
    [$W_t$], [Fast stochastic fluctuations],
      [High-frequency broadband noise],
  )
  #v(4pt)
  #text(size: 9pt, style: "italic")[
    MNDM variables with neurobiological interpretation and measurable signatures.
  ]
]

*Note on scales.* $e$ and $m$ are normalized to comparable ranges (for example,
$[0, 1]$) so their difference $F = e - m$ is well-defined. The specific
normalization is part of MNPS coordinate construction discussed later in the
measurement section.

*Assumptions and invariances.*

- *Coordinate choice:* The features $(e, m, dots)$ defining MNPS are *charts*
  on the underlying noetic manifold—local coordinate systems. Different choices
  (for example, different entropy measures, PAC vs. PLV for $m$) define
  different charts. Our predictions concern *intrinsic geometric properties*
  (trajectory curvature, geodesic distance, manifold topology) that are
  invariant under smooth coordinate transformations. This allows empirical
  flexibility while maintaining theoretical precision.
- *Monotone transforms:* Replacing $e$ or $m$ with monotone equivalents
  preserves qualitative flows (order relations matter, not absolute scales).
- *Discrete vs. continuous dynamics:* While the SDE formalism is formally
  continuous time, the *biological implementation* via rhythms creates
  *discrete denoising epochs* (theta cycles, spindle events). This discreteness
  is essential to NDT's step-wise predictions and distinguishes it from
  continuous-variance frameworks. While standard ML diffusion solvers (e.g.,
  Euler-Maruyama) are numerically discrete, NDT posits that the discreteness is
  *biologically imposed* by the rhythm $r(t)$ itself, not merely an artifact of
  integration steps @song2021 @ho2020.
- *State invariance:* The MNDM form (Eq. @eq:min-mndm) applies across wake,
  NREM, and REM; only the *schedules* $r(t)$ and the landscape weights change.
  This invariance allows us to use the same measurement framework (MNPS)
  across states while predicting state-specific geometry.

== Observation model and score estimation

We explicitly distinguish latent noetic state dynamics from measurements. Let

$Y_t = g(X_t) + epsilon_t,$

where $g: RR^d -> RR^p$ is a locally $C^1$ observation map (for example, from
latent state to multichannel EEG/fMRI) and $epsilon_t$ is zero-mean,
finite-variance noise. The MNPS coordinates $(m, d, e)$ are computed from short
windows of $Y_t$; differentiability of $g$ ensures that, under the chain rule
and mild regularity of feature functionals, gradients with respect to $X$ exist
almost everywhere.

In empirical settings $nabla F(X, t)$ is not available in closed form. We
therefore estimate it via one of two routes:

1. *Direct potential parameterization:* Posit $F(X, t; theta)$ and learn
   $theta$ by fitting trajectory statistics or via contrastive/energy-based
   objectives on MNPS embeddings; use $nabla_X F(X, t; theta)$ during
   simulation.
2. *Score-based route:* Learn a score field
   $s_phi(X, t) approx nabla_X log p_t(X)$ (for example, via score matching on
   MNPS embeddings of $Y_t$ @song2019 @song2021), and set
   $nabla F(X, t) prop - s_phi(X, t)$ up to state-dependent rescaling that
   enforces the $e - m$ structure. This identifies the *direction* of descent
   without requiring closed-form $F$.

Assumptions used throughout: (i) $g$ is locally Lipschitz; (ii) feature maps
used to build MNPS are Fréchet-differentiable almost everywhere (or *weakly
differentiable* in the distributional sense); (iii) empirical gradients are
estimated in the MNPS chart, which we use as coordinates for $X$ when learning
from data. In practice, the score-based route relies on smoothness *in
distribution* rather than pointwise differentiability, aided by temporal
windowing and regularization.

#figure(
  image("figures/fig2_mndm_dynamics.png", width: 100%),
  caption: [
    (Simulated) MNDM dynamics with rhythmic variance control, generated by
    `src/make_figures.py`.
    *A* State-space trajectory of the minimal model, colored by the local
    variance schedule $sigma(t)$; contour lines represent the potential
    landscape $F(X)$.
    *B* Anti-phasic relationship between rhythmic control $r(t)$ (blue
    pulses) and variance schedule $sigma(t)$ (red, inverse relationship),
    with the potential's descent (green) tracking low-variance denoising
    epochs (shaded). This panel directly visualizes Eq. @eq:min-mndm.
    *C* The minimal MNDM equation with visual annotations showing the
    interplay between denoising drift, exploration noise, and rhythmic control.
    *D* Coordination of schedules in the extended formulation (Eq. @eq:ext-mndm):
    illustrative evolution of landscape weights $(alpha, beta, gamma, delta)$,
    with Trace($bold(G)_t$) summarizing the attention geometry tensor.
  ],
)

== Extended formulation (geometry and meta-field)

*Why extend the minimal model?* The minimal formulation (Eq. @eq:min-mndm)
assumes uniform attention across the noetic manifold and fixed balance between
entropy and coherence. But the brain clearly modulates *what* to denoise
(attention) and *when* different pressures dominate (varying schedules).

We hypothesize that the *neural correlates of consciousness* are orchestrated
by multiple coordinated schedules operating at different timescales—variance
$sigma(t)$ setting the tempo, landscape weights $alpha, beta, gamma, delta$
composing the score, geometry $bold(G)_t$ directing attention, and embodied
anchoring providing the somatic foundation. The extended formulation formalizes
this multi-schedule architecture, adding three capabilities and linking to
metastability/criticality regimes @tognoli2014 @deco2017 @shew2013:

1. *Adaptive geometry* ($bold(G)_t$): Attention reshapes the manifold,
   stretching some dimensions (amplifying relevant features) and compressing
   others.
2. *Time-varying schedules* ($alpha, beta, gamma, delta$): Different moments
   prioritize entropy reduction, coherence, homeostasis, or meta-regulation
   differently.
3. *Meta-field* ($Phi$): A slow regulatory variable that adapts based on how
   well denoising is working—a form of “confidence” or “meta-cognitive
   monitoring”.

We now extend Eq. @eq:min-mndm to incorporate these mechanisms. The extended
system adds four ingredients to the minimal state update: a geometry tensor
that reshapes the descent direction, an adaptation rule for that geometry, an
adaptation rule for the meta-field, and a richer, time-varying potential. The
variance schedule keeps the same form as Eq. @eq:min-mndm-sigma.

*State update with adaptive geometry.* The descent direction is now reshaped
by a state-dependent metric $bold(G)_t$:

#math.equation(block: true,
  $ d X_t = - bold(G)_t(X_t) nabla F(X_t, t) d t + sigma(t) d W_t $
) <eq:ext-mndm>

*Geometry adaptation.* $bold(G)_t$ evolves slowly in response to the local
gradient, the meta-field, and rhythmic control:

#math.equation(block: true,
  $ dot(bold(G)_t) = cal(A)(bold(G)_t, nabla F, Phi, r(t)) $
) <eq:ext-mndm-geometry>

*Meta-field adaptation.* The meta-field $Phi$ tracks how well denoising is
currently working, via the metric-weighted gradient norm:

#math.equation(block: true,
  $ dot(Phi) = cal(B)(Phi, ⟨ nabla F, bold(G)_t nabla F ⟩, r(t)) $
) <eq:ext-mndm-metafield>

*Extended potential.* Landscape weights $(alpha, beta, gamma, delta)$ are now
allowed to vary in time and to depend on the meta-field:

#math.equation(block: true,
  $ F(X, t) = alpha(t) e(X) - beta(t) m(X) + gamma(t) d(X) - delta(t) Phi(t) $
) <eq:ext-mndm-potential>

Here $bold(G)_t$ is a *state-dependent Riemannian metric tensor* on the noetic
manifold—essentially a positive-definite matrix that defines local distances
and determines how gradient descent operates. It represents *attention* in
geometric terms: directions with large eigenvalues are “attended to” (steeper
descent), directions with small eigenvalues are “ignored” (shallow descent).
Connections to manifold learning and information geometry provide
complementary estimation tools @brehmer2020.

== Well-posedness and stability

To guarantee existence/uniqueness and numerical stability, we assume:

- *(A1) Lipschitz/linear growth:* $nabla_X F(·, t)$ is globally Lipschitz
  with at most linear growth uniformly in $t$; schedules $alpha, beta, gamma,
  delta$ are piecewise-$C^1$ and bounded.
- *(A2) Non-degenerate diffusion:* $sigma(t) in [sigma_min, sigma_max]$ with
  $sigma_min > 0$, piecewise continuous.
- *(A3) SPD geometry:* $bold(G)_t$ is symmetric positive-definite with
  eigenvalues in $[lambda_min, lambda_max]$ and dynamics $cal(A)$ preserve SPD.
- *(A4) Timescale separation:* To prevent overfitting where geometry chases noise,
  we assume $|| dot(bold(G))_t || << || dot(X)_t ||$ on the timescale of single
  denoising steps. $bold(G)_t$ evolves as a slow variable (plasticity) relative
  to the fast state dynamics $X_t$.
- *(A5) Regular meta-dynamics:* $cal(A)$ and $cal(B)$ are locally Lipschitz in
  their arguments.

Under (A1)–(A5) the SDE in Eq. @eq:ext-mndm admits a unique strong solution and
preserves $bold(G)_t succ 0$; $sigma_min > 0$ avoids degeneracy in long
intervals. These conditions anchor empirical estimation and simulation choices.

*New terms in the potential.*

- $d(X)$: Deviation from optimal metastability (for example, $|Q - Q^*|$ where
  $Q$ is integration/segregation balance). Penalizes extreme states (too
  integrated or too segregated). *Crucially, this term prevents the landscape from directing the system toward pathological hypersynchrony (seizures), distinguishing "meaningful" structure from "hyper-ordered" collapse.*
- $Phi(t)$: Meta-regulatory field, increases when denoising is effective (low
  $⟨ nabla F, bold(G) nabla F ⟩$), decreases otherwise. Acts as
  adaptive damping.
- Schedules $alpha, beta, gamma, delta$: Time-varying weights. Example: During
  focused tasks, $alpha$ and $beta$ increase (entropy reduction and coherence
  priority); during REM, $alpha$ and $beta$ decrease (explore freely), while
  $delta$ increases (meta-regulation dominant).

== Coherence and quasi-stability

We define a *coherence functional*

#math.equation(block: true,
  $ Omega(X, t) = e^(-F(X, t)) $
) <eq:coherence-def>

which increases as the system achieves lower potential $F$.

*Note on monotonicity:* Since $F$ typically includes the deviation term $d(X)$
(Eq. @eq:ext-mndm-potential), minimizing $F$ does not imply seeking a "dead," static
equilibrium. Rather, it implies seeking the *optimal balance* defined by the
landscape (e.g., critical integration-segregation). Thus, high coherence $Omega$
reflects proximity to this optimal metastable regime, not thermodynamic freeze.

We emphasize that $Omega$ is *not* a Lyapunov function in the strict
sense—we do not claim monotonic increase—because:

1. Stochasticity $sigma(t)$ allows uphill movements (exploration).
2. Time-varying schedules $alpha(t), beta(t), gamma(t), delta(t)$ can increase
   $F$ temporarily.
3. Adaptive geometry $bold(G)_t$ evolves, changing the landscape.

Instead, $Omega$ serves as an *instantaneous coherence measure*: Higher $Omega$
indicates a currently more meaningful state. Over a denoising epoch (a window
where $sigma$ decreases), we expect *cycle-averaged coherence*

#math.equation(block: true,
  $
    bar(Omega)_T = (1 / T) ∫_0^T Omega(X_t, t) d t
  $
)

to increase on average. This quasi-stability—*stability on average with
fluctuations*—is the hallmark of healthy cognitive dynamics.

*Reporting and normalization.* Because $Omega$ can span orders of magnitude,
for empirical plots we typically work with a stabilized and normalized version,
such as the within-subject $z$-score of $log Omega(X, t)$, and equivalently a
normalized potential $tilde(F)$ when comparing groups. This enforces
commensurate scales for $e$, $m$, and $d$ and avoids unit-driven dominance.

*Pathological extremes.* Excessive stability ($Omega$ always high, $F$ always
low) creates rigid cognition; excessive instability ($Omega$ highly volatile,
$F$ flat) creates chaotic cognition. The framework predicts an *optimal
regime* of moderate $Omega$ variability around a healthy mean.

== Model variants for Tier‑1 testing

For the first empirical wave we use Minimal‑MNDM as the default model: global
$(m,d,e)$ MNPS coordinates, fixed geometry, no meta‑field, and a rhythm-derived
variance schedule. The main comparator is a continuous‑precision/rhythm‑smoothed
null, which tests whether event‑locked variance is actually needed to explain
step‑wise entropy signatures.

More elaborate variants—fixed-geometry, no-meta, continuous-rhythm, and
extended-geometry forms—are part of the model-comparison toolkit but are moved
to Appendix @sec:model-variants. The practical rule is hierarchical: start with
Minimal‑MNDM, add complexity only if simpler rhythm and null models fail under
held-out prediction and preregistered robustness criteria.

== Neurophenomenology as a Tier-2 extension <sec:phenomenology-hypotheses>

NDT is motivated by the possibility that first-person reports of clarity,
presence, and temporal organization covary with neural denoising dynamics.
However, current experience-sampling methods are generally too slow and noisy to
adjudicate sub-second claims about pulsed experience. We therefore treat
neurophenomenological links as Tier-2: useful for future validation, but not
part of the Stage-1 evidence required for the core MNDM/RVC/MNPS tests.

The immediate empirical program uses third-person signatures only: event-locked
entropy, rhythm proxies, MNPS topology, recurrence, and null-model comparison.
Claims about embodiment, presence, insight, depersonalization, or self-prior
strength are reserved for appendix-level EAP work and later studies with direct
first-person measurement.

== Landscape learning as a follow-on module <sec:learning>

The MNDM specifies denoising dynamics given a potential landscape $F(X,t)$ and,
in the extended model, an attention geometry $bold(G)_t$. How those structures
are acquired is an important but separate question. In this core article we
therefore treat landscape learning as a *follow-on module*, not as a prerequisite
for testing Minimal-MNDM, RVC, or MNPS signatures.

A plausible extension is that wake prediction errors sculpt local basins,
NREM replay stabilizes task-relevant regions, and REM-like high-variance periods
regularize over-sharp minima. These ideas motivate later experiments on replay,
consolidation, and development, but the Tier-1 tests below require only the
observable trajectory, rhythm proxy $hat(r)(t)$, and MNPS features. Failure of a
specific wake/NREM/REM learning rule would therefore revise the learning module
without falsifying the core rhythmic-geometry claim.

Detailed learning equations, replay kernels, and developmental hypotheses are
best handled in dedicated follow-up manuscripts or appendix material once the
Stage-1 measurement contract has been validated across public datasets.

The Hippocampal--Entorhinal Landscape System (HELS) is one such prospective
contact point: replay and history may update a context-conditioned landscape
$F_c$, with primary future endpoints defined as later transition probabilities,
dwell, corridor reachability, or hysteresis rather than a mean shift in
$(m,d,e)$. Current HELS work validates analysis infrastructure and eligibility
contracts, not a landscape-writing mechanism. It therefore remains distinct
from both the online MNDM dynamics and the Stage-1 measurement claim.

= Rhythmic Variance Control (RVC) and TRN gating <sec:rvc>

The variance schedule $r(t)$ is not an abstract control parameter but a
measurable neural signature: cross-frequency coupling (CFC) in wake and sleep
provides candidate timing structure for discrete denoising epochs @canolty2010.
The thalamic reticular nucleus (TRN) is a plausible anatomical substrate for
state-dependent thalamocortical gating @halassa2016 @halassaKastner2017, but
it is not identified here as the executor of NDT's variance schedule. This
functional RVC formulation yields testable
predictions: Denoising should occur in discrete “steps” time-locked to specific
oscillatory events, not as smooth continuous processes.

#figure(
  image("figures/fig_rvc_gating_loop.png", width: 100%),
  caption: [
    The RVC gating loop, generated by `src/make_figures.py`. An observed
    neural rhythm is summarized into the event-locked control $r(t)$, which
    sets the variance schedule $sigma(t)$ that alternates the MNDM between
    exploration and denoising; the resulting state and its measured MNPS
    geometry feed back into how $r(t)$ is estimated in later windows. The
    right panel shows an illustrative (non-fitted) rhythm-to-schedule mapping
    for a single oscillatory band; empirical constructions use
    Eq. @eq:r-construction.
  ],
)

== Biological implementation of r(t)

*Distinct implementations across states.* The mapping from rhythms to $r(t)$
differs qualitatively between wake and sleep:

- *During wake:* Theta–gamma PAC provides *continuous modulation*—$r(t)$ varies
  smoothly with task demands (high during focused attention, lower during
  mind-wandering). Within each theta cycle (∼100–200 ms), high-gamma content is
  gated into and out of local circuits, creating rapid variance oscillations
  that implement moment-to-moment denoising during perception and action.
- *During NREM:* SO → spindle → ripple nesting creates *discrete, event-locked
  denoising epochs*. Here $r(t)$ is approximately piecewise constant:
  $r approx 1$ during SO–spindle–ripple complexes (strong denoising),
  $r approx 0.2$ between complexes (consolidation pause).
- *During REM:* $r(t)$ decreases globally (elevated $sigma(t)$) while theta
  coordinates exploratory search, enabling escape from local minima and
  integration across contexts.

*Formal construction from data.* For empirical work, $r(t)$ can be constructed
as a weighted combination of measurable rhythmic features:

#math.equation(block: true,
  $
    r(t)
      = op("sigm")(
          w_theta "PAC"_(theta -> gamma)(t)
          + w_("SO") A_("SO")(t) "Prec"_("SO-spindle")(t)
          + w_phi Phi_("coh")(t)
          + b
        )
  $
) <eq:r-construction>

*Important.* This parametrization is *not* required by the theory—MNDM only
requires that $r(t) in [0, 1]$ varies with neural rhythms. The specific form
above is a *practical implementation* that makes $r(t)$ directly measurable
from EEG/MEG/LFP. Alternative constructions (for example, state-specific with
separate wake/sleep weights, or purely event-detection-based during sleep) are
equally valid and may better capture the continuous vs. discrete distinction
noted above.

*Section takeaway (RVC for Tier‑1 tests).* For Tier‑1 analyses, RVC enters in
two ways: (i) we construct a proxy $hat(r)(t)$ via Eq. @eq:r-construction (or
closely related variants) to test for event‑locked, step‑wise entropy changes
relative to rhythms; and (ii) we use the same proxy to define schedule null
models (for example, smooth vs. event‑locked variants) when contrasting
Minimal‑MNDM against continuous‑precision alternatives. Strong evidence for NDT
requires that step‑like signatures are tied specifically to event‑locked
portions of $hat(r)(t)$ rather than to any smooth envelope.

#figure(
  image("figures/fig2_rvc_schedule.svg", width: 100%),
  caption: [
    Rhythmic Variance Control. Event‑locked increases in rhythmic control
    $r(t)$ are predicted to lower $sigma(t)$ anti‑phasically and produce
    step‑wise entropy reductions relative to phase‑shuffled or smooth‑precision
    null models.
  ],
)

*Candidate TRN contribution (summary).* Rhythmic proxies $hat(r)(t)$ derived
from PAC, SO--spindle coupling, and phase coherence can be evaluated by
convergent and predictive validity without identifying a unique anatomical
controller. TRN physiology motivates one candidate substrate, but the dedicated
PV/SOM auditory TRN reanalysis recorded in Zenodo 21774408 supports only a
bounded PV-linked contraction of MGB population noise dimensionality; it did
not validate a general single-unit variance-gating mechanism. Consequently,
TRN causality, $r_("true")(t)$, and a conductance-to-$sigma(t)$ mapping remain
Tier-2 hypotheses. Appendix @sec:trn-appendix records their status and the
context-conditional transition-geometry alternative
@langell2026_trn_population_geometry.

== Sleep as curriculum and wake as online control

*Sleep architecture: Two complementary patterns.* Sleep implements denoising
through two nested schedules operating at different timescales:

*Pattern 1 — Within-cycle dynamics* (∼90‑minute timescale):

- *NREM phase:* High SO–spindle precision ($r(t) approx 0.8$–0.9) ⇒ tight
  variance windows that *centralize* trajectories in MNPS (manifold contraction
  toward hubs, consolidation of replayed content).
- *REM phase:* Loose variance with elevated theta ($r(t) approx 0.2$–0.4) ⇒
  controlled *exploration* away from local minima (manifold expansion,
  connector reconfiguration, landscape smoothing).

*Pattern 2 — Across-cycle curriculum* (full-night timescale):

- *Early cycles (first 2–3):* NREM phases achieve strong centralization (deep
  hub formation), but trajectories start from *dispersed initial states*
  post-wake. This creates *large-amplitude oscillations* in $F$: deep descents
  during NREM, substantial rebounds during REM as the system explores broadly.
  *Exploration dominates the cycle envelope*—the landscape is still being
  surveyed.
- *Late cycles (last 2–3):* NREM phases refine already-centralized topology
  (hub strengthening), starting from *near-optimal states* left by previous
  cycles. This creates *small-amplitude oscillations* in $F$: modest descents
  during NREM (fine-tuning), limited REM excursions (local refinement).
  *Integration dominates*—the landscape is nearly settled.

*Resolving the apparent paradox.* “Early NREM centralizes” and “early cycles
explore” are both true but at different levels. *Within* the first cycle, NREM
centralizes trajectories; *across* cycles, the first cycle exhibits larger $F$
range (exploration–consolidation amplitude) because it operates on an unrefined
landscape. Late cycles show smaller $F$ range because the system is already
near target configuration—less distance to consolidate, less benefit to
explore.

*Quantitative amplitude decay.* Let the per-cycle amplitude be

#math.equation(block: true,
  $
    Delta F_n
      = F_("REM-peak")(n) - F_("NREM-trough")(n)
  $
)

where $n = 1, 2, dots$ indexes sleep cycles. NDT predicts an exponential
envelope:

#math.equation(block: true,
  $
    Delta F_n
      = Delta F_0 e^(- n / tau_("curriculum")) + Delta F_min,
      quad tau_("curriculum") in [2, 3] text(" cycles (typ.)")
  $
)

*Estimation.* Compute subject-wise $Delta F_n$ from event-aligned $F$ (or its
normalized proxy $tilde(F)$), fit $(Delta F_0, tau_(text("curriculum")),
Delta F_min)$ via robust nonlinear least squares with bootstrap confidence
intervals; control for total sleep time and stage proportions.
*Individual differences:* The decay rate $1 / tau_("curriculum")$ should
positively correlate with overnight learning gains (bidirectional prediction:
better learning drives efficiency, or efficient consolidation drives learning)
and with baseline MNPS component profiles.

*Wake.* During tasks, theta–gamma PAC is a candidate marker for short
denoising epochs aligned to behavioral sampling @lisman2013. Frontopulvinar,
mediodorsal-thalamic, and TRN circuits are plausible contributors to
state-dependent control @halassaKastner2017, but the controller of $r(t)$ is
not identified by the present framework.

== Geometric and behavioral signatures

RVC predicts specific, testable mappings between rhythms and MNPS
geometry:

- *Local curvature smoothing:* Increases in theta–gamma PAC strength/consistency
  ⇒ reduced local curvature and more stable geodesics along task-aligned
  trajectories (inverted-U with performance under load).
- *Hub accessibility:* Higher SO–spindle phase precision ⇒ greater access to
  consolidation hubs (higher hub betweenness/centrality) and steeper overnight
  entropy drops in relevant subnetworks.
- *Connectivity and flow:* Stronger cross-regional phase coherence ⇒ improved
  manifold connectivity (fewer fragmented components) and more reliable
  transition connectors.

== Measurement and perturbation plan

*Measurement strategy.* We estimate $r(t)$ from EEG/MEG/LFP using validated
methods: (i) phase–amplitude coupling via modulation index or mean vector
length (Tort et al., 2010; see also @canolty2010 @tort2009); (ii) SO/spindle
 detection via amplitude thresholding or wavelet transforms, with phase
 precision quantified by circular statistics (for example, Mölle et al., 2011);
 (iii) cross-regional phase coherence via weighted phase lag index (wPLI) or
 phase-locking value (PLV); and (iv) coupling within SO–spindle–ripple
 coordination in intracranial and scalp data @staresina2023 @latchoumane2017_triple
 @ngo2020.

*Operational definitions and multiple-comparisons control.* For event-locked
analyses we use pre-registered windows (baseline: $[-1.0, 0]$ s; post-event:
$[0, 1.5]$ s relative to SO–spindle onset), sliding-window entropy (500 ms,
50 % overlap), and alignment latencies constrained to biologically plausible
ranges (spindle onset within ±200 ms of SO up-state). Detection thresholds
follow literature priors (SO: 0.5–1 Hz band, amplitude >75th percentile;
spindles: 11–16 Hz, duration 0.5–2 s). Family-wise error is controlled with
Benjamini–Hochberg FDR across channels and parameter multiverse. Effect-size
priors from recent syntheses (for example, @ng2024) set expectations of
$Delta e approx 15$–30 % and medium effects ($d ~ 0.4$–0.6) for coupled
events.

For step-wise entropy analysis: Compute spectral/sample entropy in sliding
windows (for example, 500 ms), detect SO–spindle or theta peaks, align entropy
time series to these events, and test for systematic *drops* time-locked to
events (permutation testing against phase-shuffled controls). *Key
prediction:* Entropy should drop *after* event onset with timing that scales
with event duration (longer spindles → deeper/longer entropy reduction).

*Perturbation strategy.* Closed-loop stimulation provides causal tests:
(i) tACS at theta or SO frequencies can enhance or disrupt natural coupling;
(ii) stimulation at anti-phase (for example, 180° relative to detected SO)
should specifically disrupt *temporal ordering* of denoising steps (NDT
predicts items encoded during anti-phase show false temporal associations),
while in-phase stimulation enhances them; (iii) in animals, optogenetic
manipulation of TRN sectors tests whether variance control is necessary and
sufficient for the predicted geometric changes.

*Failure modes and perturbation roadmap.* Schedule dissonance—weak,
desynchronized, or pathologically rigid rhythm control—should alter recurrence,
connectors, and manifold accessibility. Pharmacological and stimulation studies
may eventually test this causal chain, but such intervention claims are Tier‑2
and require dedicated safety, dosing, and preregistration. In this core article
they serve only as a roadmap for future perturbation work, with readouts at the
level of component readouts rather than a single health score.

*Falsifiable contrasts.* If RVC genuinely implements *discrete* steps, entropy
declines should be step-wise and event-locked; anti-phase disruption should
scramble *order* (temporal misbinding), not just reduce overall precision.
Smooth, monotonic entropy changes and insensitivity to timing would falsify
this mechanism.

*Embodied Anchoring Principle (EAP; Tier‑2 extension).* EAP treats denoising as
conditioned on interoceptive state via a self‑prior and body‑synchronized
variance gating. The full formalization, interoceptive pipeline, and
phenomenology (including equations and operationalization details) are moved
to Appendix @sec:eap.

= Measurement layer: MNPS

The MNDM specifies dynamics in an abstract noetic state space $X$. To make
these dynamics empirically observable, we construct the *Meta–Noetic Phase
Space (MNPS)*—a measurable coordinate system derived from neural recordings.
The Noetic Atlas readouts built on top of MNPS are described in Appendix
@sec:noetic-atlas so the main text can focus on the canonical Stage-1
trajectory and rhythm tests.

== From neural data to MNPS coordinates

We extract three families of features from EEG/MEG/fMRI time series,
corresponding to the core MNPS axes $(m, d, e)$ and MNDM terms:

*Entropy/Disorder ($e$):* Quantifies local uncertainty and signal complexity.

- *EEG/MEG:* Spectral entropy (Shannon entropy of power spectrum, 1–40 Hz),
  sample entropy, Lempel–Ziv complexity, multiscale entropy.
- *fMRI:* BOLD signal variance per parcel, sample entropy of BOLD time courses,
  regional activation dispersion.

*Mobility / rhythmic coherence ($m$):* Quantifies structured oscillatory organization and coordination.

- *EEG/MEG:* Phase–amplitude coupling (theta–gamma, alpha–gamma),
  phase‑locking value (PLV) or weighted PLI (wPLI) across regions, spectral
  power in canonical bands (theta, alpha, beta, gamma).
- *fMRI:* Ultra‑slow oscillation amplitude (0.01–0.1 Hz), quasi‑periodic pattern
  (QPP) strength, BOLD–respiratory coupling.

*Diffusivity / deviation from metastability ($d$):* Quantifies distance from optimal
integration–segregation balance.

- *EEG/MEG:* Participation ratio (inverse concentration of power across
  channels/components), graph modularity $Q$.
- *fMRI:* Integration index (for example, $|Q - Q^*|$ where
  $Q^* approx 0.3$–0.5 is near‑optimal), global efficiency, synchrony variance.

These features are computed in sliding temporal windows (for example, 2 s for
EEG, TR‑matched for fMRI) and $z$‑scored within subject to yield comparable
$(m, d, e)$ time series that define MNPS coordinates.

*Note on spatial scope (global vs. regional).* In this first NDT manuscript we
primarily treat $X_t$ as a *global* noetic state, so $m$ aggregates rhythmic
structure across the brain (for example, mean PLV/wPLI across channel pairs,
and pooled band‑power indices). This inevitably mixes spatial scales but keeps
the minimal MNDM tractable; regional heterogeneity is addressed in separate
work on Regional MNPS, where each network has its own local $(m, d, e)$ chart
and block‑Jacobian. When we use pairwise measures such as PLV in the present
3D MNPS, they are explicitly summarized (for example, robust mean across
pairs) rather than attributed to single regions, and the resulting global $X_t$
should be read as a coarse, whole‑brain state variable.

*Definition vs. implementation.* At the theory level, $e$, $m$, and $d$ denote
*classes* of entropic, mobility/rhythmic‑coherence, and metastability‑deviation
measures: any choice within these classes that respects basic regularity
assumptions defines a valid MNPS chart. In this manuscript, we instantiate
$e$, $m$, and $d$ with spectral entropy, composite PAC/PLV/power indices, and
modularity‑based deviation, but our primary predictions target properties that
should be stable across this class: topological organization (component
fragmentation, hub structure), the timing of event‑locked entropy changes
relative to rhythms, and the qualitative structure of flows in MNPS.
Chart‑dependent quantities (exact $Delta e$ magnitudes in a given dataset, or
absolute composite scores) are always reported together with the specific
implementation choices used to compute them.

An extended, 9‑dimensional *Stratified MNPS* framework that decomposes the
core $(m, d, e)$ axes into sub‑coordinates (for example, attentional vs.
limbic mobility, local vs. network diffusivity) is developed in a separate
working paper @langell2025_stratified. The present manuscript restricts itself
to the 3D MNPS needed for the core NDT predictions, but all constructions here
are designed to remain compatible with that stratified extension.

*Measurement contract and later extensions.* For this article, the canonical
object is the 3D trajectory $bold(X)_("MNPS")(t) = [e(t), m(t), d(t)]^T$ plus
its rhythm proxy $hat(r)(t)$. Atlas component readouts are optional appendix
summaries. Stratified 9D MNPS,
Meta‑Noetic Jacobians, reachability cones, regional MNPS, and cytoskeletal or
dendritic accessibility models are later extensions. They may refine mechanism
and regime interpretation, but they should not be treated as assumptions needed
to evaluate the Stage‑1 MNDM/RVC/MNPS predictions.

=== Algorithmic specification for MNPS construction <sec:mnps-algorithm>

To ensure reproducibility, we provide explicit computational steps for
constructing MNPS coordinates from neural data.

*Step 1: Preprocessing.*

1. *EEG/MEG:* Band‑pass filter 0.5–100 Hz, notch‑filter 50/60 Hz, artifact
   rejection (ICA or robust averaging), re‑reference to average.
2. *fMRI:* Standard preprocessing (motion correction, spatial normalization,
   parcellation via Glasser‑360 or Schaefer‑400), temporal filtering
   0.01–0.1 Hz.

*Step 2: Feature extraction with explicit formulas (EEG/MEG).*

- *Entropy $e(t)$:*

  #math.equation(block: true,
    $
      e_("spectral")(t)
        = - sum_(f = 1)^(40) P_f(t) log P_f(t),
        quad
        P_f(t) = S_f(t) / sum_(f') S_(f')(t)
    $
  )

  where $S_f(t)$ is power spectral density at frequency $f$ in a window
  centered at $t$ (estimated via Welch’s method; window 2 s, 50 % overlap).

- *Rhythmic coherence $m(t)$:*

  #math.equation(block: true,
    $
      m(t)
        = w_("PAC") "PAC"_(theta -> gamma)(t)
          + w_("PLV") overline("PLV")_(theta)(t)
          + w_("pow") P_("theta")(t)
    $
  )

  where $"PAC"$ is a modulation index @tort2009, $overline("PLV")$ the mean
  phase‑locking value across electrode pairs, and $P_("theta")$ theta‑band
  power; default weights might be $w_("PAC") = 0.5$, $w_("PLV") = 0.3$,
  $w_("pow") = 0.2$.

- *Deviation from metastability $d(t)$:*

  #math.equation(block: true,
    $
      d(t) = | Q(t) - Q^* |,
      quad
      Q^* approx 0.4
    $
  )

  where $Q(t)$ is graph modularity at time $t$, computed on a thresholded
  phase‑coherence matrix (for example, top 10 % of connections).

*Step 3: Normalization and MNPS assembly.*

1. $z$‑score each feature within subject:
   $e_("norm")(t) = (e(t) - mu_e) / sigma_e$ etc.
2. Construct coordinate vector
   $bold(X)_("MNPS")(t) = [e_("norm")(t), m_("norm")(t), d_("norm")(t)]^T$.
3. Optionally expand with higher‑order features (for example, band‑specific
   PAC, regional entropy) for a higher‑dimensional MNPS.

*Pseudocode.*

1. *Preprocess.* Filter and clean the neural data according to
   `params.filter_specs` to obtain `data_clean`.
2. *Windowing.* Extract overlapping windows of length
   `params.window_s` with 50 % overlap, yielding `windows`.
3. *Feature extraction.* For each window:
   - Compute spectral entropy $e[t]$ from the Welch PSD.
   - Estimate theta–gamma coupling (`pac`), mean PLV (`plv`), and
     theta-band power (`theta_pow`) to form $m[t]$.
   - Build the phase-coherence matrix, compute modularity $Q$, and derive
     $d[t] = | Q - 0.4 |$.
4. *Normalization.* $e$, $m$, and $d$ are $z$-scored within subject to
   yield $e_(norm)$, $m_(norm)$, and $d_(norm)$.
5. *Return.* The MNPS coordinates are
   $"MNPS"_("coords")(t) = [e_(norm)(t), m_(norm)(t), d_(norm)(t)]^T$.

*Coordinate invariance and robustness.* While specific choices for $e$, $m$,
and $d$ define a particular MNPS chart, we explicitly define *invariance classes*—
predictions that must hold across all valid coordinate charts to be considered
robust:

1.  *Topological Invariance:* Qualitative features like component fragmentation
    (in psychosis) or collapsed manifold volume (in depression) must remain
    statistically significant regardless of whether $e$ is Spectral or Sample entropy.
2.  *Temporal Invariance:* The *timing* of step-wise entropy drops relative to
    spindles must be preserved across feature choices, even if absolute magnitudes shift.
3.  *Gradient Invariance:* The direction of flow ($d X / d t$) in local regions
    should correlate ($r > 0.7$) across chart choices after Procrustes alignment.

Primary claims target these intrinsic properties; chart-level metrics are used
comparatively within fixed pipelines.

*Appendix pointer.* The Noetic Atlas applies embedding, topology, recurrence,
and metastability tools to MNPS trajectories; those component definitions,
along with the optional Stage-1 NDHI composite, are provided in Appendix
@sec:noetic-atlas. The core predictions below depend on the MNPS trajectory,
rhythm proxy, and prespecified component-level contrasts rather than on the
Atlas as an additional theory layer.

#figure(
  image("figures/fig3_mnps_measurement_pipeline.svg", width: 100%),
  caption: [
    MNPS measurement pipeline. Neural recordings are windowed into the three
    Stage‑1 coordinate families $(m,d,e)$; appendix Atlas tools and NDHI are
    downstream summaries rather than additional assumptions of the core model.
  ],
)

= Predictions and falsifiable claims

NDT makes specific, testable predictions that distinguish it from alternative
frameworks. We organize these by type: *signature predictions* (novel patterns
NDT uniquely predicts), *competitive predictions* (where NDT and alternatives
make different predictions), and *falsification criteria* (observations that
would disprove core claims).

For empirical planning we distinguish a small *Tier‑1 primary test set* from
longer‑horizon or more speculative *Tier‑2* predictions. The Tier‑1 set
comprises: (P1) Signature Prediction 1 (step‑wise NREM entropy drops
time‑locked to SO–spindle events), (P2) Signature Prediction 3 (sleep
curriculum with NREM centralization and REM expansion in MNPS topology), and
(P3) bounded clinical geometry contrasts such as collapsed, over‑recurrent
trajectories versus fragmented, shallow‑recurrence trajectories. EAP‑specific,
neurophenomenological, therapy, and detailed disorder-subtype predictions are
Tier‑2: they guide future work but are *not* required to succeed in the first
wave of empirical tests for NDT to be considered supported.

*Subsequent empirical evaluations.* Later NDT manuscripts report provisional
support for traversability dissociation, MNJ flattening under propofol,
regional MNPS signatures in fMRI, and extreme‑regime dissociations. These
results are treated as follow‑on empirical tests that inform effect‑size
priors and model refinement @langell2026_extreme @langell2026_traversability
@langell2025_propofol @langell2025_regional_mnps.

A paired hypoglycemia--euglycemia EEG reanalysis adds a complementary boundary:
it reports a reproducible stratified MNPS condition shift but no
FDR-supported reachability collapse. That study contains no continuous glucose,
autonomic, interoceptive, recovery, or behavioural measurement and therefore
does not test an EAP metabolic gate or a consciousness readout.

*Current boundary from later work.* Subsequent analyses sharpen an important
interpretive constraint: reduced dynamical capacity should not be equated with
unconsciousness. Physiological sleep, pharmacological suppression, and seizure
states can all reduce accessible dynamics, but they may differ in
transport‑innovation balance and pathological lock‑in. The core NDT article
therefore avoids a single scalar "consciousness level" readout. When later work
uses reachability, traversability, or Meta‑Noetic Jacobians, those measures are
treated as second‑order extensions that decompose capacity, transport capture,
and canalization rather than replacing the Stage‑1 MNDM/RVC/MNPS tests.

#figure(
  image("figures/fig4_regime_boundaries.svg", width: 100%),
  caption: [
    Boundary inherited from later NDT work. Reduced capacity or traversability
    should not be collapsed into a single consciousness score; later extensions
    separate capacity, transport capture, and pathological lock‑in.
  ],
)

*Effect size priors and thresholds.* Where we quote specific effect sizes (for
example, $Delta e approx 20$–35 % or $d > 0.6$), these are grounded in a
combination of (i) literature‑based priors—especially recent syntheses on
SO–spindle mechanisms and sleep‑dependent entropy changes (for example,
@ng2024)—and (ii) simulation results using the minimal MNDM that indicate the
scale at which predicted topology/entropy signatures become reliably
detectable under realistic noise and sample sizes. We therefore treat
thresholds such as $d >= 0.6$ or $r >= 0.3$ as conservative targets for
*strong support*, while smaller but consistent effects are still informative as
*moderate* or *exploratory* evidence, provided they meet the preregistered
robustness criteria described in the methods section.

*Overview.* The five predictions below are summarized here for quick
reference; each is unpacked in its own subsection.

#block(width: 100%, breakable: true)[
  #table(
    columns: (0.6fr, 0.7fr, 1.6fr, 2.3fr),
    inset: 8pt,
    align: (center, center, left, left),
    stroke: none,
    table.header([*\#*], [*Tier*], [*Prediction*], [*Primary test*]),
    [1], [Tier 1],
    [Step-wise entropy locked to rhythmic events],
    [NREM entropy drops time-locked to SO–spindle events, not smooth decay.],
    [2], [Tier 2],
    [Phase-specific denoising during wake],
    [Theta-phase-locked modulation of recall accuracy and local entropy.],
    [3], [Tier 1],
    [Sleep as geometric curriculum],
    [NREM centralization vs. REM expansion in MNPS topology across the night.],
    [4], [Tier 1],
    [Bounded clinical geometry contrasts],
    [Reproducible manifold deformation across a clinical contrast exists
      (observed: medication-stratified FEP $m$/path-cost shift; BDI-linked
      depression reachability and 9D MNJ); original Mapper/DET and
      volume-collapse operationalizations remain open, untested-as-stated
      Tier-2 targets.],
    [5], [Tier 2],
    [Anti-phase disruption affects temporal order (competitive prediction)],
    [Order errors are disproportionately elevated relative to item-memory
      errors under anti-phase rhythmic stimulation.],
  )
  #v(4pt)
  #text(size: 9pt, style: "italic")[
    Overview of NDT's signature and competitive predictions, with tier and
    primary test. See the falsification-criteria table below (Section 6.6)
    for the corresponding falsifiers.
  ]
]

== Signature Prediction 1: Step-wise entropy locked to rhythmic events

*Claim.* During NREM sleep, neural entropy should decline in *discrete steps*
time‑locked to SO–spindle (and ripple) events, not smoothly.

*Operationalization.* Detect SO–spindle complexes in sleep EEG; compute
spectral/sample entropy in 500 ms windows; align entropy time series to event
onsets; test for systematic drops within 100–1000 ms post‑onset.

*Predicted pattern.* Entropy drops $Delta e approx 15$–30 % within one spindle
duration (∼0.5–1.5 s) after complex onset, with effect size
$d > 0.6$ vs. pre‑event baseline. Longer/higher‑amplitude spindles → deeper
drops; non‑nested spindles or isolated SOs show weaker effects.

*Consequence.* SO–spindle precision (phase consistency) should predict:
(i) magnitude of overnight entropy reduction ($r ~ 0.3$–0.5),
(ii) next‑day memory performance ($r ~ 0.2$–0.4), and (iii) component-level
MNPS changes from pre‑sleep to post‑sleep.

== Signature Prediction 2: Phase-specific denoising during wake

*Claim.* Items encoded at different theta phases undergo denoising at different
depths, affecting encoding quality @bahramisharif2018.

*Operationalization.* Present stimuli at controlled theta phases; measure
encoding success and neural entropy as a function of presentation phase.

*Predicted pattern.* Items near theta peak show better recall and lower
entropy. Theta–gamma PAC strength shows an inverted‑U with task performance
(optimal at intermediate coupling; too weak → insufficient denoising, too
strong → over‑rigid).

== Signature Prediction 3: Sleep as geometric curriculum

*Claim.* Manifold topology transforms systematically: NREM centralization,
REM expansion, progressive overnight refinement.

*Predicted patterns:*

- *NREM:* Hub betweenness ↑ ($d > 0.5$), manifold volume ↓ (20–40 %), recurrence
  rate ↑.
- *REM:* Opposite pattern (expansion, decreased centrality).
- *Overnight:* Net centralization with oscillations; late > early NREM in hub
  coherence.
- *TMR:* Cued content shows increased local Mapper density and steeper local
  entropy drops.

== Signature Prediction 4: Bounded clinical geometry contrasts

*Claim.* Some clinical contrasts should produce reproducible manifold
deformations, but these are bounded dataset-level hypotheses rather than
diagnostic categories.

*Observed signatures (internal, dataset-bounded).* Two companion analyses
report FDR-surviving manifold deformations that support the *existence* half
of this claim, though not in the form originally sketched below:

- *First-episode psychosis (medication-stratified):* Across two independent
  resting-state cohorts, shared-reference MNPS geometry separates FEP from
  controls, but as a medication-dependent double dissociation rather than a
  single universal signature: medicated FEP shows a static shift in the
  mobility/coherence coordinate ($m$; $d = 0.881$, $q = 0.016$, cohort
  ds003944), while unmedicated FEP instead shows elevated trajectory cost
  ($d approx 0.77$, FDR-borderline, cohort ds003947)—a static-geometry
  signature under medication versus a path-cost signature without it.
- *Depression (symptom burden):* In a resting-state cohort split by BDI
  symptom burden ($n = 121$), the clearest FDR-surviving deformations are in
  the reachability coordinates (log-determinant and eigenvalue-variance,
  $|d| approx 0.68$–$0.74$) and 9D Meta-Noetic Jacobian rotational power
  ($d = 0.569$), not in coarse 3D volume.

These results confirm that reproducible, bounded manifold deformation exists
across a clinical contrast, while falsifying the specific illustrative
operationalizations first proposed here (Mapper fragmentation for psychosis;
3D volume collapse for depression), which remain open, untested-as-stated
Tier-2 targets:

- *Depression (original target):* Collapsed volume ($d > 0.6$ vs. controls),
  over‑recurrence, flattened curvature, reduced hub access @palaniyappan2021.
- *Psychosis (original target):* Fragmented Mapper (high component count),
  shallow recurrence (low DET), unstable geodesics @sanz2023.

Negative and null results bound both signatures further: psychosis turning-angle/geodesic
disruption is FDR-null under a medication-stratified design, and depression's
paired task–rest deltas are broadly null despite state-level signal. The full
evidence ledger—cohorts, effect sizes, and all negative results—is maintained
in `articles/NDT/parts/008_20260809_clinical_disorder_evidence_survey.md`.

PTSD, anxiety, neurodegeneration, and anesthesia are not primary claims of this
paper. They are better handled as follow‑on regime tests where capacity,
traversability, transport capture, and pathological lock‑in can be analyzed
separately; companion Parkinson and Alzheimer/FTD analyses are cataloged in the
same evidence ledger as Tier‑2 material.

== Competitive Prediction 5: Anti-phase disruption affects temporal order

*NDT prediction.* Anti‑phase rhythmic stimulation disrupts *temporal ordering*
of denoising steps, leading to temporal binding errors and false associations.

*Predictive‑coding prediction.* Disruption reduces overall precision, leading
to proportional impairment of all memory.

*Distinguisher.* Order errors become disproportionately elevated vs. item
memory under anti‑phase stimulation.

== Falsification criteria

NDT would be falsified or require major revision if:

#block(width: 100%, breakable: true)[
  #table(
    columns: (0.4fr, 3.2fr, 2fr),
    inset: 8pt,
    align: (center, left, left),
    stroke: none,
    table.header([*\#*], [*Observation*], [*Implication*]),
    [1],
    [Entropy declines are smooth/continuous, not event-locked.],
    [Contradicts rhythmic variance control.],
    [2],
    [Manifold geometry is invariant across wake/sleep/pathology.],
    [Contradicts geometry–dynamics coupling.],
    [3],
    [Anti-phase disruption affects only magnitude, not temporal structure.],
    [Contradicts discrete-step denoising.],
    [4],
    [All effects are derivable from precision-only models without discrete
      steps or geometry.],
    [NDT adds nothing beyond existing precision-scheduling accounts.],
    [5],
    [Tier-2 phenomenological variables remain unrelated to $(m,d,e)$ or
      $Omega$ under adequate temporal alignment.],
    [Constrains the phenomenological extension only; does not by itself
      falsify the Stage-1 dynamical model.],
  )
  #v(4pt)
  #text(size: 9pt, style: "italic")[
    Falsification criteria for NDT's Stage-1 and Tier-2 claims.
  ]
]


== Failure modes, confounds, and unfalsifiability patterns

We enumerate concrete failure modes and how the preregistered analysis
circumvents unfalsifiability:

- *Chart‑flexibility inflation:* Post‑hoc switching of MNPS features
  $(m, d, e)$ could manufacture effects. *Guardrail:* Predefine a multiverse
  grid that explicitly includes *mechanistically distinct* feature
  implementations (for example, spectral vs. Lempel–Ziv entropy, PAC‑heavy vs.
  PLV‑heavy $m$) rather than only parameter tweaks of a single measure, and
  require directional consistency across ≥80 % of specifications with FDR
  control; report Procrustes alignment between MNPS variants (target
  $R^2 > 0.7$). Core topology (for example, depression‑like manifold collapse)
  must survive across these distinct implementations to count as robust.
- *Schedule over‑flexibility:* Allowing $r(t)$ to be freely re‑fit risks
  tautology. *Guardrail:* Construct $hat(r)(t)$ from observables with fixed
  methods and cross‑validated weights; treat $sigma(t)$ amplitude as the only
  free scalar in Stage 1 estimation.
- *Event‑detection circularity:* Using entropy changes to define events would
  guarantee step‑like drops. *Guardrail:* Detect SO/spindles with canonical
  band‑limited criteria and circular statistics independent of entropy, then
  test entropy time‑locked to those events.
- *Parameter overfitting:* Rich parameterizations (for example, adaptive
  $bold(G)_t$) may fit noise. *Guardrail:* Nested model comparison with BIC and
  held‑out prediction; accept added complexity only with
  $Delta "BIC" > 10$ and >10 % test‑set error reduction.
- *Hidden confounds:* Vigilance, motion, and medication can mimic topology
  changes. *Guardrail:* Regress standardized confounds, analyze within‑subject
  stage contrasts, and verify absence of effects in phase‑randomized
  surrogates.
- *Unfalsifiability pattern A (moving targets):* Redefining predictions after
  seeing data. *Guardrail:* Preregister operationalizations, parameter grids,
  and success thresholds.
- *Unfalsifiability pattern B (equivalence classes):* Claiming success under
  transformations that preserve ordering. *Guardrail:* Use interventions that
  break equivalences (anti‑phase rhythmic stimulation; TRN‑targeted
  pharmacology) and require order‑specific effects.

In addition, we include *null‑model controls* (random‑walk trajectories and
continuous‑precision models) alongside Minimal‑MNDM in simulations and
empirical fits; step‑wise, event‑locked entropy drops and rhythm‑locked
topology changes must exceed these nulls under identical preprocessing and FDR
control.

= Simulated demonstrations

To demonstrate that the MNDM can reproduce key theoretical predictions, we
simulate the minimal formulation (Eq. @eq:min-mndm) under several scenarios
capturing core dynamics: wake‑to‑sleep transitions, sleep cycling with
curriculum structure, and disorder‑typical perturbations. All simulations use
Euler–Maruyama integration; predictor–corrector samplers from score‑based
diffusion can be used analogously for improved stability @song2021pc.

*Minimal worked example and null models.* Before complex scenarios, we present
a worked example contrasting Minimal‑MNDM against two nulls:

- *Minimal‑MNDM (event‑locked variance):* $d X_t = - nabla F d t + sigma(t) d W_t$,
  $F = E - R$, with $sigma(t) = sigma_min + sigma_0 (1 - r(t))$ and
  piecewise‑constant $r(t)$ (1.0 during detected events, 0.2 otherwise). This
  square‑wave idealization is best read as an analytically convenient limit case
  corresponding to strongly pulsatile gating; in later scenarios we also
  consider smooth rhythm proxies passed through the non‑linear construction in
  Eq. @eq:r-construction to assess whether step‑like entropy dynamics can
  *emerge* from graded inputs rather than being assumed.
- *Null A (random walk in MNPS):* $d X_t = sigma_("RW") d W_t$ with identical
  preprocessing, feature extraction, and windowing; no coupling to $r(t)$.
- *Null B (continuous‑precision PC‑like):*
  $d X_t = - nabla F d t + sigma_c(t) d W_t$ with smooth $sigma_c(t)$ obtained
  by low‑pass filtering $hat(r)(t)$ (no event steps).

*Readouts:* (i) event‑triggered spectral entropy $e(t)$ (500 ms windows),
(ii) Mapper fragmentation index, (iii) RQA determinism (DET). *Expected
pattern:* Minimal‑MNDM shows step‑wise post‑event $Delta e$ and rhythm‑locked
topology changes; Null A shows no event‑locked structure; Null B shows smooth
entropy drifts without discrete steps.

== Scenario 1: Wake‑to‑sleep transition

*Setup.* We simulate a single trajectory over $T = 3600$ s (1 h) with $r(t)$
transitioning from wake‑like continuous modulation to sleep‑like discrete
epochs.

*Parameters (illustrative):*

- $X in RR^(50)$ (low‑dimensional noetic manifold).
- $e(X) = (1 / 2) | X |^2$ (quadratic entropy surrogate).
- $m(X) = sum_(i < j) cos(X_i - X_j)$ (pairwise coherence).
- $sigma_0 approx 0.5$ (chosen to match empirical EEG‑feature variability).
- $r(t)$ decreases from 0.4 (wake) to 0.9 (deep sleep) over the hour.

*Results.* Trajectories show (i) progressive descent in $F(X, t)$ as variance
decreases, (ii) manifold‑volume contraction (lower participation ratio), and
(iii) increased recurrence to low‑$F$ basins. Entropy $e(X)$ drops from
∼15 (wake‑like) to ∼5 (sleep‑like), while coherence $m(X)$ increases from
∼0.3 to ∼0.8, consistent with “centralization” during NREM.

== Scenario 2: NREM/REM cycling

*Setup.* We simulate an 8‑hour sleep night with four 90‑min cycles, each
containing NREM (tight variance) and REM (loose variance) phases.

*Parameters (schematic):* $r_("NREM") approx 0.85$, $r_("REM") approx 0.3$, with
gradual ramps; NREM duration decreases across cycles, REM increases.

*Results.* Trajectories exhibit the dual‑timescale curriculum architecture:

- *Within‑cycle pattern:* Manifold contracts during NREM, expands during REM,
  visible as oscillations in participation ratio and geodesic distances.
- *Across‑cycle pattern:* Early cycles show large‑amplitude $F$ oscillations
  (exploration‑dominated), late cycles small‑amplitude oscillations
  (integration‑dominated). Final REM ends at much lower $F$ than initial wake,
  confirming net overnight consolidation despite REM‑driven exploration.
- *Entropy dynamics:* Step‑wise drops during NREM epochs (20–30 % per
  spindle‑dense period), partial rebounds in REM (10–15 %), with overall
  downward trend—matching the dual‑schedule architecture.

== Scenario 3: Bounded parameter perturbations

Starting from a reference baseline, we perturb parameters to emulate two broad
geometry regimes:

- *Depression simulation:* Flatten $nabla F$ (weaker score) and reduce
  exploratory variance ($sigma_0$ small) with normal $r(t)$.
  Result: Trajectory becomes trapped in a high‑$F$ local minimum; manifold
  shows collapsed volume, excessive recurrence, and flattened curvature—
  matching predicted depression topology.
- *Psychosis simulation:* Elevate noise ($sigma_0$ large), weaken gradient, and
  desynchronize $r(t)$ by adding noise. Result: Trajectory wanders chaotically,
  rarely settling into coherent basins; manifold shows fragmented structure,
  shallow recurrence, and unstable geodesics.

== Scenario 4: Learning‑module placeholder

Learning-induced changes in $F$ and $bold(G)_t$ are not simulated as a primary
claim in this core article. They are reserved for follow-on work once the
Stage‑1 trajectory, rhythm, and component readouts have been validated.

= Methods and analysis plan (public datasets) <sec:datasets>

We outline a preregistered analysis plan for testing NDT predictions on public
datasets. By specifying methods, parameters, and success criteria in advance,
we aim for transparent, hypothesis‑driven evaluation. For fMRI, we focus on
topology/dynamics (centralization, fragmentation, hubs) rather than sub‑second
step‑wise effects; EEG/MEG datasets test the temporal predictions.

== Target datasets

#block(width: 100%, breakable: true)[
  #table(
    columns: (1.3fr, 1.1fr, 2.6fr),
    inset: 8pt,
    align: (left, left, left),
    stroke: none,
    table.header([*Dataset*], [*Modality*], [*What it tests*]),
    [HCP],
    [Resting-state and task fMRI],
    [Manifold topology predictions and exploratory composite stability in
      healthy cognition (e.g., component profiles vs. fluid
      intelligence/working memory; task-dependent centralization vs.
      expansion).],
    [Sleep-EDF],
    [Polysomnography],
    [Step-wise entropy and sleep-curriculum predictions: NREM
      centralization, REM expansion, SO–spindle precision vs. entropy drops
      and next-day performance.],
    [OpenNeuro clinical datasets],
    [EEG/fMRI (e.g., depression, schizophrenia)],
    [Disorder-specific topology predictions (collapsed volume and
      over-recurrence in depression; fragmented Mapper and shallow
      recurrence in psychosis, etc.).],
  )
  #v(4pt)
  #text(size: 9pt, style: "italic")[
    Public datasets targeted for Stage-1 and exploratory NDT tests.
  ]
]

Subsequent subsections adapt the MNPS pipeline and Atlas summaries (S1) to
these datasets (feature extraction, Mapper/RQA settings, component summaries) and
specify effect‑size thresholds, power analyses, and multiverse‑analysis
strategies much as in the LaTeX version.


= Limitations and future work

We explicitly acknowledge key limitations:

- *Learning problem:* MNDM specifies dynamics given $F$ and $bold(G)_t$ but does
  not yet derive how they are learned from synaptic/circuit plasticity. A
  simulator-first candidate mechanism—replay-dependent slow branch-level
  accessibility—reproduces a joint linking/perturbation/rescue signature not
  matched by nine tested simpler comparators @langell2026_slowbranch, and a
  follow-on truth-known observability audit separately maps which measurement
  objects can and cannot recover that mechanism under partial, non-oracle
  observation (Appendix @sec:simulator-recoverability)
  @langell2026_observability_simulator. Both remain synthetic
  model-discrimination and measurement-recoverability results, not validated
  biological plasticity or a fitted NDT learning rule; the tri‑phase learning
  architecture and HELS remain the open bridge to direct, content-specific
  transition or reachability tests on real circuits. Existing HELS
  analyses validate infrastructure, not a mechanism.
- *Measurement and identifiability:* Coordinate choices for MNPS introduce
  ambiguity; robust multiverse analysis and targeted perturbations are needed
  to disambiguate models (see below).
- *Phenomenological methods:* Claims about pulsed experience, presence, and
  embodiment require high‑resolution neurophenomenology that is still under
  development. Operational content sections and fibre language
  (Appendix @sec:ndt-q-fibres) organize hypotheses, and a dedicated
  measurement-precursor program has now started: in mouse visual cortex,
  population decoders trained only on real, orientation-matched edges
  generalize to illusory-contour trials beyond shuffled-label and
  region-specificity controls. This is a genuinely blind, frozen
  content-generalization decoding result, not a phenomenal-report measurement;
  it neither measures qualia nor closes the hard problem.
- *Clinical translation:* Geometric pharmacology and intervention design are
  explicitly future‑work goals; any clinical pathway claims are provisional
  until replicated with preregistered, dataset‑specific validation.
- *Hard‑problem scope:* NDT addresses *when/how* denoising unfolds and what
  geometry it leaves, not why denoising is accompanied by subjective
  experience. This is a permanent scope boundary: no measurement-recoverability
  audit or content-decoding result above is intended or able to close it.

== Identifiability of landscape, geometry, and schedule

At the level of observables, $(F, bold(G)_t, r(t))$ are partially
non-identifiable: different combinations of potential shape, attention geometry,
and variance schedule can yield similar trajectories in MNPS. Our strategy is
threefold. First, chart-level ambiguity is addressed by the multiverse
guardrails above, which require that qualitative patterns (for example,
step‑wise NREM entropy drops, depression‑like manifold collapse) be consistent
across many reasonable $(m, d, e)$ definitions. Second, we rely on *targeted
perturbations* that preferentially modulate one component: TRN-focused
manipulations can test candidate circuit contributions but cannot be presumed
to identify $sigma(t)$; attentional tasks and fronto‑parietal lesions should
primarily affect $bold(G)_t$; and interventions on plasticity or replay should
reshape $F$ itself. Third, we explicitly compare Minimal‑MNDM against
null models (for example, continuous‑precision “Null B”) in both simulations
and data: patterns such as discrete, event‑locked entropy steps or tightly
coupled topology changes must be reproducible by Minimal‑MNDM but *not* by
plausible precision‑only models if they are to count as evidence specifically
for rhythmic, geometry‑coupled denoising.

Future work should unify score‑learning with predictive‑error plasticity,
incorporate action and active inference, model development and lifespan
changes in schedules, extend to multi‑agent settings, and explore laminar
implementations in detail.

= Conclusion

We summarize the thesis that conscious-state correlates may be studied as
*rhythmic, step‑wise denoising on a learned manifold*. The core advances are
discrete timing via RVC, a minimal MNDM that can be compared against nulls, and
geometry‑first visibility through MNPS and the appendix Noetic Atlas. NDT is offered as a staged
research program with concrete next steps: public‑dataset analyses, stricter
multiverse controls, and later perturbation experiments once the Stage‑1
measurement layer is stable.

= Acknowledgments

This work emerged through structured correspondence among human and AI
collaborators; large language models (GPT‑5, Claude, Gemini, Grok) assisted in
literature synthesis, drafting, and editorial refinement.

= Contact

Robin Langell — hello(at)noeticdiffusion.com

= Licensing

This manuscript provides only a brief licensing summary; full terms and
conditions are available via the Mychainos multi‑layer licensing framework
(`https://mychainos.org/licence/`). In short, the conceptual content is released
under CC BY‑SA 4.0, software under GPLv3, and relevant hardware/biological
artifacts under open hardware/biological licences (for example, CERN OHL v2 and
OpenMTA). Unified ethical guardrails apply: no coercive, military, or
surveillance applications; no patenting or black‑boxing of core methods; and
derived works should remain accessible, attributed, and shared with care.

= Data and Code Availability

Reference implementations and analysis pipelines will be released at
`https://github.com/ruppi86/NoeticDiffusion` (public upon acceptance), with
licensing following the Mychainos policy.

= Trademark Notice

Certain terms used in this manuscript (including *Noetic Diffusion*, *Noetic
Diffusion Theory*, *Noetic Diffusion Mapping*, *Noetic Diffusion Health Index*,
and *Noetic Atlas*) are used as project names and are the subject of ongoing
trademark applications. A concise description of the stewardship rationale,
current registration status, and how this interacts with open scientific use is
available at `http://noeticdiffusion.com/license.html`. These trademark aspects
do not affect the scientific content, reproducibility, or licensing of the
methods described here.

#pagebreak()

= Appendix

The formal core above (Minimal-MNDM, functional RVC, MNPS) is self-contained
for Stage-1 testing. The following Tier-2 extensions, methodological audits,
and comparative framing are developed in full in dedicated supplements
(*Supplementary Methods S1-S4*); only their status ceilings and testable
content are summarized here.

== Model variants and comparators <sec:model-variants>

The MNDM can be systematically simplified into five hierarchical variants
(Minimal-MNDM, fixed-geometry, no-meta, continuous-rhythm, and
extended-geometry) to test whether adaptive geometry, the meta-field, or
discrete rhythm-locking are actually necessary for the observed signatures. A
variant is accepted only when it improves held-out prediction beyond simpler
rhythm/precision models. Full variant definitions and comparison logic are
given in *Supplementary Methods S1*.

== Noetic Atlas: geometric and topological readouts <sec:noetic-atlas>

The Noetic Atlas applies four complementary readout streams to MNPS-embedded
trajectories: manifold embedding/geodesic flow, topological data analysis
(Mapper/persistent homology), recurrence quantification analysis, and
metastability/criticality indices. Together they form a geometric portrait of
denoising dynamics; full stream definitions are given in *Supplementary
Methods S1*.

== Stage-1 composite summary (NDHI)

The Noetic Diffusion Health Index (NDHI) is an *exploratory* Stage-1 composite
of Atlas readouts, always reported with its component scores and
weight-perturbation sensitivity; it is not a clinical biomarker, diagnostic
label, or consciousness score. The full construct definition and reporting
requirements are given in *Supplementary Methods S1*.

== Truth-known simulator audits: recoverability and reachability <sec:simulator-recoverability>

A truth-known synthetic simulator programme, forked from a Slow Branch
candidate mechanism for memory linking @langell2026_slowbranch, audits
measurement recoverability rather than biology, asking which latent
distinctions survive a specified observation map and estimator. The Slow
Branch source model shows that replay-dependent slow branch-level
accessibility reproduces a joint profile of overlap strengthening, linking
gain, perturbation loss, and targeted rescue not matched by nine simpler
comparators—a model-*discrimination* result, not evidence that dendrites
store memory content. The corrected simulator ladder recovered aggregate
reachability calibration under its frozen contract, but its directional Gate R
test failed, and a lag-embedded local-operator test was structurally null;
neither result validates empirical MNJ estimates or a micro-to-macro neural
mechanism. Full recoverability-level definitions and the epoch-operator/
reachability recursion are given in *Supplementary Methods S1*
@langell2026_observability_simulator.

== Subsystem extensions: CCTG and HELS <sec:subsystem-extensions>

Context-Conditional Transition Geometry (CCTG) is a speculative, context- and
circuit-dependent replacement for universal TRN-variance-gate language. The
Hippocampal-Entorhinal Landscape System (HELS) is orthogonal: it proposes that
replay/history may update a context-conditioned landscape $F_c$. Neither is a
Stage-1 result; HELS currently has validated infrastructure but no validated
mechanism result, and CCTG must earn support through dedicated reversal/causal
tests. Full equations and status are given in *Supplementary Methods S2*.

== NDT-Q: operational content sections <sec:ndt-q-fibres>

MNPS characterizes a global dynamical regime, not the identity of an
experienced or represented content. NDT-Q separates content as an operational
readout problem via a regime base $pi_B$, content readout $rho_b$, and content
sections, supporting a measurable episode profile
$P_t = (c_t, chi_t, S_t, R_t, V_t)$. This is an explanatory mathematical
architecture, not a claim that neural tissue instantiates a literal fibre
bundle or that current decoding measures qualia. A first, genuinely blind
precursor test now exists in mouse visual cortex (public electrophysiology
data): decoders trained only on real, orientation-matched edges generalize to
illusory-contour trials beyond a temporal circular-shift null, a non-visual
control-region check, and label-shuffled and behavioral-state controls. This
targets content-generalization decoding only—no trajectory geometry, content
section, or closure signature is computed, no phenomenal report exists in
mice, and the result does not itself test or validate NDT-Q, CSQ, or MNPS. The
full formalism and evidence ledger are given in *Supplementary Methods S2*.

== Embodied Anchoring Principle (EAP) <sec:eap>

EAP states that denoising is conditioned on interoceptive/body state via a
self-prior term $F_("self")$ and rhythmic entrainment of $r(t)$; it is a
Tier-2 extension intended for a later wave of interoception-focused studies.
Current companion evidence supports bounded, condition-level autonomic/MNPS
co-modulation in wake and carrier-specific (SO-trough-dominant) autonomic
phase-locking in sleep, but not causal body-to-manifold gating, phase-resolved
entrainment, or a metabolic consciousness gate (a related hypoglycemia clamp
contrast shows a stratified MNPS shift without a confirmed reachability
collapse). The full formal integration, neural-substrate hypotheses,
phase-landscape model, and Self-Prior Index measurement plan are given in
*Supplementary Methods S3*.

== Candidate TRN substrates and CCTG <sec:trn-appendix>

This records a candidate TRN contribution and a phenomenological simulation
mapping without identifying TRN as the biological implementation of NDT's
variance schedule: the auditory PV/SOM TRN reanalysis (Zenodo 21774408)
supports a dataset-bounded PV-linked contraction of MGB population noise
dimensionality, not a full single-unit variance-gating mechanism or
identification of $r(t)$/$sigma(t)$ with TRN firing. The candidate circuit
sketch, simulation ansatz, and CCTG successor hypothesis are given in
*Supplementary Methods S2*.

== Related work

NDT's relationship to dynamical-systems/landscape accounts of brain activity,
predictive-processing/active-inference frameworks, and integrated-
information/network-control approaches is discussed in *Supplementary Methods
S4*.

#pagebreak()


#bibliography("references.bib")