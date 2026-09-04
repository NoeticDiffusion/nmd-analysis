#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "Trajectory Psychosis Supplementary Methods",
  subtitle: "Subject-anchored contract, repertoire metrics, and noetic action derivation",
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

This supplement expands the methods compressed in the main trajectory-geometry manuscript. It covers:

1. the relationship between the subject-anchored and cohort-anchored coordinate contracts,
2. the full repertoire-flow metric derivation,
3. the noetic action formulation and its jerk component,
4. the codebook fitting procedure and the choice of codebook size,
5. the statistical design and multiplicity-control approach,
6. and the known limitations of the current implementation.

= Subject-anchored vs cohort-anchored coordinates

The companion static-geometry paper uses cohort-anchored coordinates for its primary between-subject contrasts. The present trajectory study uses subject-anchored coordinates. This is a deliberate design decision.

Cohort-anchored coordinates transform each feature relative to a fixed population reference:

$
tilde(phi)_(t,j)^"cohort" = frac(phi_(t,j) - c_j^"pop", s_j^"pop" + epsilon),
$

where $c_j^"pop"$ and $s_j^"pop"$ are the population center and scale. This places all subjects in one shared inter-subject space and supports between-subject positional comparisons.

Subject-anchored coordinates transform relative to the subject's own statistics:

$
tilde(phi)_(t,j)^"subject" = frac(phi_(t,j) - c_j^"sub", s_j^"sub" + epsilon).
$

Subject-anchored trajectories are centered and scaled within each subject, so inter-subject differences in global dynamic range do not inflate or deflate the trajectory metrics. This is preferable when the scientific question is about the *shape* of temporal movement rather than the *location* of average state.

Both coordinate layers are provided in the NeuralManifoldDynamics 2.1 H5 export under `coords_3d_subject_anchored/values` and `coords_9d_subject_anchored/values`. The article reads these directly for each subject H5 file.

= Repertoire-flow metrics

Let $bold(z)_t in RR^k$ ($k = 3$ or $k = 9$) be the subject-anchored coordinate at window $t$, with windows indexed by real time $tau_t$ from the `time` dataset in each H5 file.

== Codebook and state discretisation

A shared codebook is fitted once per dataset per dimension using Mini-Batch K-Means on pooled data from all subjects:

- Per subject, up to 256 windows are sampled evenly.
- All subjects' samples are concatenated and then subsampled to at most $40{,}000$ points (3D) or $60{,}000$ points (9D).
- The codebook has $N_S = 12$ states (3D) or $N_S = 24$ states (9D).
- Random seed is fixed at 20260607 for reproducibility.

Each subject's windows are then labelled $s_t = arg min_i ||bold(z)_t - bold(mu)_i||$ where $bold(mu)_i$ are the codebook centroids. This yields a discrete state sequence ${s_t}_{t=1}^T$.

Subjects with fewer than 16 valid windows after finite-value masking are excluded. Runs with fewer than 9 transitions ($T < 10$) also receive NaN metrics.

== Transition matrix and stationary distribution

From the state sequence, the one-step transition count matrix is

$
C_(i j) = sum_{t=1}^{T-1} bb(1)[s_t = i, s_(t+1) = j].
$

The row-normalised transition probability matrix is

$
P_(i j) = frac(C_(i j), sum_k C_(i k) + epsilon cdot bb(1)[sum_k C_(i k) = 0]).
$

The empirical stationary distribution is

$
pi_i = frac(N_i, sum_j N_j), quad N_i = sum_t bb(1)[s_t = i].
$

== Article-facing repertoire metrics

*Entropy rate* measures trajectory unpredictability:

$
H_"rate" = -sum_i pi_i sum_j P_(i j) log(P_(i j) + epsilon).
$

Higher $H_"rate"$: more uniform or more random transitions. Lower: more stereotyped, predictable movement.

*Temporal irreversibility* measures asymmetry of the probability flow:

$
I = 1/2 sum_(i,j) |pi_i P_(i j) - pi_j P_(j i)|.
$

A time-reversible trajectory would have $pi_i P_(i j) = pi_j P_(j i)$ for all pairs ($I = 0$). Higher $I$ indicates directed, non-equilibrium flow.

*Entropy production* is the thermodynamic irreversibility rate:

$
E_"prod" = sum_(i,j) pi_i P_(i j) log frac(pi_i P_(i j) + epsilon, pi_j P_(j i) + epsilon).
$

This is always $>= 0$ and equals zero for a reversible Markov chain.

*Self-loop rate* (supportive):

$
R_"self" = sum_i pi_i P_(i i).
$

High self-loop rate indicates slow, persistent movement that rarely advances to a new state.

*Transition sparsity* (supportive): fraction of zero entries in $C$.

= Noetic action metrics

The noetic action is a path-integral approximation to the cost of traversal through state space @langell2026_trajectory. It is computed at the interior windows $t = 2, dots, T-1$ where both a forward and backward interval are available.

== Finite-difference terms

$
Delta bold(z)_t = bold(z)_(t+1) - bold(z)_t, quad Delta^2 bold(z)_t = bold(z)_(t+1) - 2 bold(z)_t + bold(z)_(t-1).
$

Time intervals:

$
Delta t_"prev" = tau_t - tau_{t-1}, quad Delta t_"next" = tau_{t+1} - tau_t, quad Delta t_"center" = 1/2(Delta t_"prev" + Delta t_"next").
$

Windows where $Delta t_"prev" <= 0$ or $Delta t_"next" <= 0$ are excluded.

== Metric-weighted quadratic form

The diagonal metric matrix is $M = "diag"(m_j)$ where $m_j = (sigma_j^2 + epsilon)^{-1}$ and $sigma_j^2$ is the pooled variance of coordinate $j$ across all subjects' sampled points. This makes all axes comparably scaled before the energy calculation.

$
||bold(u)||_M^2 = bold(u)^T M bold(u) = sum_j m_j u_j^2.
$

== Lagrangian density

At each interior window $t$:

$
L_t = underbrace(1/2 frac(||Delta bold(z)_t||_M^2, Delta t_"next"^2), L_t^"kin") +
      underbrace(eta frac(||Delta^2 bold(z)_t||_M^2, Delta t_"center"^4), L_t^"jerk") +
      underbrace(lambda Phi(bold(z)_t), L_t^"pot"),
$

with $eta = lambda = 1$.

== Potential function

For the 3D chart:

$
Phi(bold(z)_t) = e_t - m_t + d_t.
$

For the 9D chart:

$
Phi(bold(z)_t^{(9)}) = bar(e)_t - bar(m)_t + bar(d)_t, quad bar(m)_t = (m_a + m_e + m_o)/3, dots
$

The potential encodes a heuristic energetic interpretation of the MNPS axes: high entropy ($e$) and diffusivity ($d$) raise the potential, high metastability ($m$) lowers it. This is a modelling choice, not a derived quantity.

== Subject-level summaries

All four Lagrangian components are summarised as median over valid interior windows:

$
"noetic_action" = "med"_t(L_t), quad "noetic_action_kinetic" = "med"_t(L_t^"kin"),
$
$
"noetic_action_jerk" = "med"_t(L_t^"jerk"), quad "noetic_action_potential" = "med"_t(L_t^"pot").
$

The jerk component $L_t^"jerk"$ measures resistance to acceleration: it is small when the trajectory changes direction smoothly and large when acceleration itself changes rapidly. This is the term most directly linked to the aberrant-salience prediction.

= Statistical design

All contrasts use Mann-Whitney U (two-sided). Cohen's $d$ is computed as the difference in group means divided by the pooled standard deviation. BH-FDR is applied within each combination of {dataset, contrast label, analysis type (3D or 9D)}. This is family-local multiplicity control; no manuscript-wide correction is applied across the full metric and contrast universe.

Effect sizes are signed such that the first-named group minus the second-named group gives the sign of $d$. For example, `FEP unmedicated vs Healthy` gives positive $d$ when unmedicated FEP exceeds healthy controls.

= Implementation

The article-local computation is in `articles/CLINICAL/psychosis_first_time_geometric_trajectory/src/run_psychosis_trajectory_geometry.py`. It uses no NDT-core dependencies beyond `h5py`, `numpy`, `pandas`, `scipy`, and `sklearn`. The codebook is fitted once per dataset and dimension and applied to all subjects. H5 files are read from `data/raw/neuralmanifolddynamics_ds003944_20260520_121126/` and `data/raw/neuralmanifolddynamics_ds003947_20260520_114135/`.

= Known limitations

*Temporal resolution.* Each subject has approximately 75 windows at 4-second spacing. The jerk metric at this resolution is a coarse approximation; genuine millisecond-scale aberrant salience spikes would not be resolvable.

*Codebook sensitivity.* The discrete state labels depend on the codebook. Different random seeds or codebook sizes may change the exact values of $H_"rate"$ and $I$, though the directions should be robust.

*Potential function.* The noetic action potential is a modelling assumption, not a derived quantity from the data. The $e - m + d$ functional form is interpretable but arbitrary; alternative choices would give different potential-component values.

*Subject-anchored centering.* By centering within subject, we remove inter-subject mean differences from the trajectory analysis. This is the intended design for trajectory metrics, but it means the trajectory results are not directly comparable to the cohort-anchored positional contrasts in the companion paper.

*Temporal shuffled null.* The present analysis does not include a window-order permutation test to verify that the metrics depend on real temporal structure. This is the most important outstanding validation step.

#bibliography("psychosis.bib", style: "apa")
