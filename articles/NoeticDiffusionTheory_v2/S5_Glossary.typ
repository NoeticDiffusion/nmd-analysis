// S5 Glossary — NDT terms as used in this article.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S5 Glossary",
  short-title: "Glossary - NDT",
  subtitle: "Terms as used in this article, with claim ceilings",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("glossary", "NDT", "MNPS", "NMD", "accessibility"),
  article-type: "Supplementary Material",
  abstract: [
    Definitions for Noetic Diffusion Theory 1.0. Where relevant, entries
    distinguish the theoretical object, the operational chart estimator, and
    what is not established.
  ],
)

#set heading(numbering: none)

_Reading guide._ *Object* = theoretical quantity. *Implemented* = what a
current contract actually computes. *Not established* = common over-reading.

= A -- D

*Accessibility (dynamical / noetic).* Object: the geometry of the family of
protocol-conditional kernels ${K^h}_(h > 0)$ over future *states at horizon
$h$*. The latent process has a transition law $K^X$; experiments generally
estimate projections or chart-conditional approximations $K^x$. Unadorned
$K^h$ means $K^x$ unless a latent argument is explicit. Path-dependent
quantities (committors, routes) are defined under the corresponding process,
not by a single endpoint kernel. Not workspace ignition, not report, not a
consciousness scalar.

*Attractor / basin.* Object: long-run organization of the transition law.
Implemented: not recovered as unique wells on MNPS here. Visual
clustering is not evidence of an attractor.

*Committor $q$.* Object: probability of hitting $B$ before $A$. Implemented:
conceptual in NMD; 2-D finite-sample recovery closed in companion simulation.

*Control $c_t$ / protocol $gamma$.* Object: anything allowed to change $b$,
$a$, mobility $M$, potential $V$, or gates, including a path of $c$ or
history $H_t$. RVC is the minimal special case. Not a unique biological
executor.

*Diffusion tensor $a$.* Object: local second-moment geometry of stochastic
spread, $a = Sigma Sigma^top$. Implemented: truth-known envelopes in
restricted linear SDEs; not a default empirical NMD export without residual
gates.

= E -- L

*Embodied Anchoring Principle (EAP).* Object: bodily context may condition
accessibility. Implemented: bounded timing (e.g. SO/respiratory phase);
spindle-geometry *efficacy* rejected. Not a third MNPS axis.

*FAR (finite-amplitude resilience).* Object: whether a finite kick dislodges
the state. Implemented: not an empirical NMD export here.

*Generator $cal(L)_(t | c)$.* Object: infinitesimal description of the
controlled diffusion (main text and S1). Implemented: not fitted to neural
data.

*HELS / HELS-A / HELS-A1.* HELS asks whether history writes $V$. HELS-A asks
whether access can change on frozen $V$. HELS-A1 is the biological
eligibility/estimator gap. Do not collapse the three.

*Jacobian $J$ / MNJ.* Object: local derivative of drift. MNJ means that
Jacobian *on an MNPS chart*. Implemented: operational chart Jacobian. Not an
intrinsic manifold tensor; $alpha$ and $omega$ inherit chart dependence.

= M -- R

*Mobility tensor $M$.* Object: SPD matrix converting a Euclidean gradient into
potential-driven drift, $b_"pot" = - M nabla V$. If a metric $g$ is declared,
$M = g^(-1)$. Not the diffusion tensor $a$; no fluctuation--dissipation link
is currently assumed.

*MNPS (3D / stratified 9D).* Implemented: versioned observation chart
$(m, d, e)$ and a nine-dimensional refinement. Not the latent state, not NDT.

*NeuralManifoldDynamics (NMD).* Implemented: versioned measurement contract
for charts and selected estimators. Not the theory.

*Noetic.* Scope marker: mind-level state dynamics. Not a claim that
coordinates constitute experience.

*Potential $V$.* Object: NDT state-dependent landscape in the drift split.
Not IIT's $Phi$.

*Reachability (stochastic short-horizon).* Object: covariance-based
approximation to finite-horizon *predictive spread* under $K^h$, summarized
by a predictive-spread ellipsoid. Implemented in companions as covariance-tube
summaries (e.g. effective dimensionality, persistence). Not classical
control-theoretic reachability and not Gramian controllability.

*Chart-speed coupling.* Object: Pearson (or similar) correlation between
regional sequences of epoch-to-epoch chart speed. Implemented in one Allen
companion as a CA1--VISam omission-minus-expected contrast. Not stochastic
short-horizon reachability, not $Sigma^((h))$, and not a Gramian.

*RVC (Rhythmic Variance Control).* Object: $r(t) -> sigma(t)$ as minimal
accessibility control. Not proven spindle denoising.

= S -- Z

*Spectral / numerical abscissa ($alpha$, $omega$).* Chart-level summaries of
local linearization (growth of modes; transient amplification). Stable
$alpha < 0$ is not a phenotype if $omega > 0$.

*Thalamic access.* Candidate architecture for changing $K^x$ on frozen $V$.
Synthetic operators exist; biology is association, not identification.

#bibliography("references.bib", style: "apa")
