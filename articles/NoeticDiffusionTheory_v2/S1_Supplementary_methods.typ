// S1 Supplementary Methods — NDT mathematical definitions.
// Programme-level objects. Not a fitted neural SDE and not an NMD export list.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "S1 Methods - NDT",
  subtitle: "Transition law, local geometry, and estimator validity boundaries",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(S1.1)")

= Scope

This supplement records the mathematical objects named in the main text. It is
not a claim that every object currently has a validated empirical estimator.
NeuralManifoldDynamics implements selected chart-level functionals; it does
not define NDT.

= The transition law as the central object <sec:s1-math>

The working process class is the controlled diffusion of the main text. The
object that unifies drift, diffusion, reachability, committor, and control is
the *control-dependent transition law*, not any one derived scalar.

The main text now carries the generator $cal(L)_(t | c)$ and two related
kernels: the latent law $K_(t : t+h)^(X | gamma)$ and the chart-conditional
law $K_(t : t+h)^(x | gamma)$. This supplement records estimator and
chart-dependence limits that do not belong in the narrative.

The snapshot kernel
$K_c^(X, h) (xi, A) = P(X_(t+h) in A | X_t = xi "and" c_t = c)$
is a *special case* in which the protocol $gamma$ is constant on $[t : t+h]$.
If $c$ varies, or if history $H_t$ matters, either augment the state
$Z_t = (X_t, C_t, H_t, dots)$ until it is approximately Markov, or condition
on the protocol path as in the main-text kernels. HELS-A and P6 are statements
about $gamma$, not violations of the controlled diffusion.

When the text writes $K^h$ without a superscript, the intended object is the
chart-conditional law $K^x$ unless a latent argument is explicit. $K^h$ is the
law of the state at horizon $h$, not the path-space measure on
$X_([t : t+h])$ or $x_([t : t+h])$. The family ${K^h}_(h > 0)$ is the primary
finite-horizon object. Committors are path/hitting functionals of the
corresponding process @metzner2009transition @klus2018data.

Relation to named summaries (same mapping as the main text):

- Drift $b$ is the infinitesimal conditional mean rate.
- Diffusion $a$ is the infinitesimal conditional covariance rate.
- The empirical Jacobian $hat(J)_x$ is a chart-level derivative of $hat(b)_x$;
  the latent counterpart is $nabla_xi b$.
- Stochastic short-horizon reachability is a finite-horizon predictive-spread
  functional of $K^h$.
- The committor is a hitting probability under the same process.
- Attractors organize the long-time law.
- FAR is the response of the law to a finite displacement.
- Rhythm, thalamus, history, body, and metabolism are candidate changes of
  $K$ or $cal(L)$, not extra theories.

NDT-C1--C3 below match the main text. RVC, thalamic access, HELS, EAP, and
dendritic $M_b$ are candidate mechanisms for C3. They are not part of the
definition.

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

= Drift split and identifiability

Potential-driven drift supplies one structured component,
$b = - M nabla V + u_"nc"$, with mobility $M succ 0$ (and $M = g^(-1)$ if a
metric $g$ is declared). NDT does not currently assume a
fluctuation--dissipation relation linking $M$ to $a$. A residual
non-conservative term is permitted because cyclic or asymmetric flow need not
be gradient descent under the declared geometry. The split is *not* uniquely
identified from trajectories without extra structure. An anisotropic or
state-dependent $M$ can make a gradient flow look non-normal in Euclidean
coordinates. Chart Jacobian non-symmetry is therefore not proof of a genuine
$u_"nc"$ component. $V$ is the NDT potential, not IIT's $Phi$.

= Coordinate dependence

MNPS is an operational chart. Away from a fixed point, $J = partial b \/
partial x$ is not generally an intrinsic tensor under nonlinear
reparametrization. An Itô SDE acquires an Itô correction in the transformed
drift. Consequently $alpha$, $omega$, $Omega$, and local deformation summaries
are *chart-level measurements* unless a connection is declared and a covariant
derivative is used. NMD currently estimates the operational chart Jacobian.
An intrinsic $nabla b$ is not implemented and is not claimed.

= Stochastic short-horizon reachability

The ellipsoid constructed by propagating local covariance under a locally
linear stochastic model is *not* classical control-theoretic reachability and
not a Gramian of a structural connectome. Call it *stochastic short-horizon
reachability*: a covariance-based approximation to finite-horizon predictive
spread under $K^h$. Horizon, residual quality, and neighbourhood leakage are
validity conditions. NMD does not emit this object without an admissible
one-step residual. Condition mixtures can also inflate the innovation term
itself. In a companion Allen analysis, pooling expected and omission epochs
increased $op("Tr")(Q)$ in all $126$ examined session $times$ region
combinations, typically several-fold; residual degrees of freedom were $1$
throughout those six-epoch fits of $A$, $Q$, and $Sigma^((h))$. Condition-separated
fitting is therefore required before any predictive-spread interpretation.
Pearson coupling of regional chart-speed sequences is a different object and
is not this ellipsoid.

= Committor and finite-amplitude resilience

The committor $q_(A B)(x)$ is the probability of hitting $B$ before $A$. It is
destination geometry, not spread. Finite-sample 2-D recovery is not a current
empirical export. FAR asks whether a finite kick can dislodge the state; it
depends on perturbation family and amplitude and is not a local-linear
summary. Neither object is licensed as an NMD v2 export in the present
contract.

= What this supplement does not authorize

Success at claim class 1 does not license $cal(L)$ identification.
Simulator envelopes for $a$, $alpha$, and $omega$ are truth-known qualifications
under restricted linear SDEs. They do not identify MNPS coordinates with
latent $X_t$.

#bibliography("references.bib", style: "apa")
