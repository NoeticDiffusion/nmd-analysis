// S7 Supplementary Note — selected NDT mathematics under kernel-checked proofs.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S7 Formal Verification of Selected NDT Mathematical Components",
  short-title: "S7 Formal Verification - NDT",
  subtitle: "Machine-checked boundaries from reduced state to licensed finite-horizon geometry",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("formal verification", "Lean", "NDT", "dynamical accessibility", "covariance"),
  article-type: "Supplement",
  abstract: [
    This note records a bounded Lean formalization of selected mathematical
    components used by Noetic Diffusion Theory (NDT). The formal development
    starts with a finite counterexample for reduced-state insufficiency and
    continues through covariance propagation, finite-horizon nondegeneracy,
    positive-semidefinite factorization, and proof-carrying inverse ellipsoids.
    The theorems are exact under their stated finite-dimensional assumptions.
    They support the architecture and claim discipline of NDT; they do not
    validate empirical accessibility, identify a biological mechanism, or
    establish that an MNPS chart is a latent neural state.
  ],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(S7.1)")

= Scope and epistemic status <sec:s7-scope>

This supplement is a formal verification record for selected mathematical
objects in the NDT v2 article. It is an infrastructure note, not a new
empirical results section and not a claim that the whole theory has been
formalized. The source is the Lean project at the repository-relative path
`formalization/lean`. Its Lean namespace is
`NoeticDiffusion`.

The formal results answer questions of the following form: given explicit
finite-dimensional assumptions, does a stated algebraic identity or logical
equivalence follow? They do not answer whether the assumptions hold for neural
recordings. A kernel-checked theorem can certify a conditional mathematical
claim while leaving model selection, measurement validity, residual quality,
and biological interpretation open.

#netn-box(title: [Reading rule])[ 
  *Proved* means that the named proposition is accepted by Lean's kernel under
  the hypotheses in its declaration. *Not proved* means that the current
  project deliberately does not claim the statement. Neither label is an
  empirical pass or a biological explanation.
]

= The formal architecture <sec:s7-architecture>

The development follows the same separation used in the main article: a
measurement chart is an observation interface, while accessibility concerns a
future transition law. The mathematical chain is:

#figure(
  kind: table,
  clean-table(
    columns: (1.1fr, 2.0fr, 2.9fr),
    align: (left, left, left),
    inset: 4.5pt,
    table.header([*Stage*], [*Object*], [*Formal content and claim ceiling*]),
    [1], [Reduced chart], [A chart $pi : X -> Z$ can identify present observations while losing future-relevant information. A finite Boolean counterexample and a general fibre criterion are proved.],
    [2], [Affine stochastic step], [For a concrete finite family of real random variables, $A X + b + epsilon$ has covariance $A "Cov"(X) A^top + Q$ under explicit integrability, innovation covariance, and zero cross-covariance hypotheses.],
    [3], [Finite-horizon covariance], [$C(0) = 0$ and $C(h+1) = A C(h) A^top + Q$ have a finite Gramian form. The time-varying extension allows $A(h)$ and $Q(h)$ to change with the step.],
    [4], [Innovation factors], [For explicit factors $B(h)$, the propagated factors are $Phi(T,h+1) B(h)$. For fixed transitions and $Q = B B^top$, the factors are $A^k B$.],
    [5], [Nondegeneracy gate], [Positive definiteness is equivalent to directional detection, trivial common transpose kernel, full block-column span, and full row rank, with the relevant finite index assumptions.],
    [6], [Licensed geometry], [An inverse quadratic form and inverse ellipsoid require a `PosDef` witness. Affine push-forward additionally requires an explicit `IsUnit F`; failed nondegeneracy gives no ordinary inverse-ellipsoid license.],
  ),
  caption: [The formal chain from reduced state to licensed finite-horizon geometry. Each arrow carries assumptions; no arrow licenses an empirical or biological interpretation.],
) <tab:s7-architecture>

The chain has two distinct uses in NDT. The reduced-state results formalize a
possibility claim: a present chart need not be sufficient for a future law.
The covariance results formalize an algebraic construction: a finite-horizon
predictive-spread object can be defined and manipulated when its transition,
noise, and nondegeneracy assumptions are explicit. The latter object remains a
covariance-based approximation to future spread, rather than classical
control-theoretic reachability or a probability coverage statement.

= Theorem inventory and status <sec:s7-inventory>

The table reports the current status at the level of mathematical statements.
The file names and theorem names are included so that a reader can inspect the
kernel-checked source directly.

#figure(
  kind: table,
  clean-table(
    columns: (1.55fr, 1.15fr, 3.8fr),
    align: (left, left, left),
    inset: 4.5pt,
    table.header([*NDT-related statement*], [*Status*], [*Lean evidence or explicit boundary*]),
    [A reduced chart can lose future-relevant information.], [Proved], [`ReducedState.lean`: `same_present_different_observed_future` and `no_deterministic_chart_factorization`; finite counterexample.],
    [Exact criterion for deterministic factorization through a surjective chart.], [Proved], [`ReducedSufficiency.lean`: `exists_factorization_iff_of_surjective`; constancy on chart fibres is equivalent to factorization.],
    [An affine stochastic update induces the covariance recursion.], [Proved under hypotheses], [`StochasticCovarianceConcrete.lean`: `covMatrix_affineNoise`; the abstract interface exposes covariance additivity and linearity as assumptions.],
    [Finite-horizon covariance has a Gramian representation.], [Proved], [`Covariance.lean`, `StochasticCovarianceHorizon.lean`, and `StochasticCovarianceTimeVaryingGramian.lean`; finite algebra only, with no stability assumption.],
    [A time-varying factor chain can be characterized as nondegenerate through collectively detecting propagated factors.], [Proved], [`StochasticCovarianceTimeVaryingNondegeneracy.lean` for explicit factors; `StochasticCovarianceTimeVaryingFactor.lean` extends the detection, kernel, span, and rank equivalences to arbitrary PSD $Q(h)$ by existential factor selection, with the singular boundary `covarianceTimeVarying_det_eq_zero_of_not_posDef`.],
    [Positive definiteness, detection, common-kernel triviality, span, and full rank are equivalent in the finite factor construction.], [Proved], [`CovarianceNondegeneracyRectangular.lean`, `CovarianceKernelEquivalence.lean`, `CovarianceBlockSpan.lean`, and `CovarianceBlockRank.lean`.],
    [Every finite real positive-semidefinite square matrix admits a factor $Q = B B^top$.], [Proved], [`CovariancePSD.lean`: `posSemidef_exists_factor_mul_transpose`; this selects an existential factor, not a numerical algorithm.],
    [Positive definiteness licenses inverse and determinant geometry.], [Proved], [`CovarianceLicensing.lean`: `posDef_isUnit_licence`, `posDef_det_pos_licence`, and `logDetOfPosDef`; the license carries its witness.],
    [Affine, scaled, and fixed-transition inverse-ellipsoid identities are exact.], [Proved under hypotheses], [`CovarianceEllipsoidScaling.lean`, `CovarianceEllipsoidPushForward.lean`, and `CovarianceEllipsoidFixedTransitionCommon.lean`; scaling is positive, and affine maps carry `IsUnit F`.],
    [An arbitrary time-varying PSD sequence is automatically assigned the factors needed by the nondegeneracy chain.], [Proved], [`StochasticCovarianceTimeVaryingFactor.lean`: `exists_timeVarying_factor_sequence` selects factors existentially for every PSD $Q(h)$ (no numerical algorithm); `CovarianceEllipsoidTimeVarying.lean` packages the covariance-agnostic `CovarianceGate` and its affine ellipsoid.],
    [Chart-fibre sufficiency extends to PMF- and measure-valued future laws; a chart-matched pair can carry different stochastic laws.], [Proved], [`KernelSufficiency.lean`: `kernel_exists_factorization_iff_of_surjective`, `kernel_measure_exists_factorization_iff_of_surjective`, `stochastic_no_kernel_chart_factorization`; pointwise law equality, no kernel-measurability or path-space claim.],
    [Protocol or one-step history augmentation restores chart sufficiency in a finite model where the plain chart fails (finite face of NDT-C3 and P6).], [Proved], [`KernelSufficiency.lean`: `unaugmented_chart_insufficient`, `augmented_chart_sufficient`, `history_unaugmented_chart_insufficient`, `history_augmented_chart_sufficient`; deterministic finite models.],
    [Negative real eigenvalues (or modulus below one) do not exclude instantaneous or single-step growth; the numerical abscissa is the least Rayleigh bound.], [Proved], [`JacobianReactivity.lean`: `shear_not_isNumAbscissaBound_of_nonpos`, `J1_not_isNumAbscissaBound_of_nonpos`, `discreteShear_finite_time_gain_gt_one`, `isNumAbscissaBound_numAbscissa`, `numAbscissa_le_of_isNumAbscissaBound`; finite algebra, no ODE.],
    [Finite-time gain exceeds one for the true matrix exponential of a stable shear; rotation changes the operator but not the exact decay rate.], [Proved], [`JacobianConversion.lean`: `shearExp_eq_matExp`, `finiteTimeGain_gt_one` ($10/e > 1$), `rotationPair_R1_decomp`, `rotationPair_R1_orthogonal`; also the naive conversion bias `naiveConversion_rate_lt_trueRate`.],
    [Spectral abscissa is similarity-invariant while the numerical abscissa is not; scalar access gain cannot produce the non-normal regime; orthogonal gating preserves trace and spectrum but not orientation.], [Proved], [`AccessOperators.lean`: `alpha_similarity_invariant`, `L19_witness_omega_not_similarity_invariant`, `scalarGain_isNumAbscissaBound`, `gating_trace_eq`, `gating_charpoly_eq`, `orientation_changes_under_orthogonal_gating`.],
    [Jacobian asymmetry is not sufficient evidence for a non-conservative mechanism; the drift split is not identifiable from drift and gradient alone.], [Proved], [`DriftSplitJacobian.lean`: `mulIsSymm_iff_commute`, `mulIsSymm_witness_antisymPart_ne_zero`, `driftSplit_nonidentifiable`, `L17_polyB_partials_ne`; coordinate-slice derivatives, no general Clairaut theorem.],
    [Predictive-spread covariance is Loewner-monotone in innovation covariance and horizon; trace, determinant, characteristic polynomial, and $d_"eff"$ are orthogonal gauge invariants but not rescaling invariants.], [Proved], [`CovarianceSummaries.lean`, `CovarianceSummariesTimeVarying.lean`: `covariance_mono_Q`, `covariance_horizon_mono`, `covarianceTimeVarying_mono_Q`, `orthogonalConj_*`, `dEff_le_card`, `dEff_ge_one`, `rescaling_changes_dEff`; the time-varying horizon monotonicity is disproved by `covarianceTimeVarying_horizon_not_mono`. Determinant monotonicity under the Loewner order is not proved.],
    [Block-diagonal transition and innovation keep the finite-horizon covariance block-diagonal; matched aggregate summaries do not force matched directional ratios; the four inferential claim classes are pairwise non-implicative.], [Proved], [`ObservabilityLevels.lean`: `L20_blockDiag_covariance`, `L20_privateRatio_isotropic`, `L20_privateRatio_diag_witness`, `L20_claimClass_not_implies`; the claim classes are modelled as an abstract four-world table, not as chart/mechanism predicates.],
    [Occupancy, one-step law, spread, committor, support, mass, and local linearization are pairwise non-equivalent (finite witnesses).], [Proved], [`FuturesNonEquivalence.lean`, `FuturesNonEquivalenceMaps.lean`, `CovarianceSummariesTimeVarying.lean` (W6): `L14_occupancy_ne_reachability`, `L14_same_support_different_mass`, `L14_covariance_eq_committor_ne`, `L14_deriv_eq_at_zero` with `L14_f2_escape`, `L14_W6_same_occupancy_diff_committor`; finite toy chains and one-dimensional maps only.],
    [Finite-chain committor algebra and explicit gambler's-ruin committors; committor uniqueness under finite absorption.], [Proved in part], [`CommittorFinite.lean`: `L15_isCommittor_swap`, `L15_isCommittor_combo`, `L15_gamblersRuinQ_isCommittor`, `L15_biasedRuinQ_isCommittor`, `L15_gamblersRuinQ_unique`; the general finite-absorption uniqueness and maximum-principle theorems are not proved.],
    [Empirical NDT accessibility is established by the formal development.], [Not proved], [Lean proves finite mathematical propositions. It does not validate an estimator, residual gate, dataset, or out-of-sample accessibility contrast.],
    [A biological mechanism for context, history, rhythm, thalamic access, or embodiment is established.], [Not proved], [Mechanistic identification is outside this package and requires independent experimental and statistical evidence.],
  ),
  caption: [The status ledger separates conditional mathematical proof from empirical and biological claims.],
) <tab:s7-inventory>

The rows labelled *proved under hypotheses* or *proved in part* are
intentionally qualified. The formal result is stronger than an informal analogy
because the hypotheses are visible in the declaration, but it does not remove
the need to establish those hypotheses for a scientific application. Two
further modules, `SlowBranchModel.lean` and `ClosureEpochOperator.lean`,
formalize simulator-internal toy-model invariants and are deliberately omitted
from this inventory.

= Assumptions behind the proofs <sec:s7-assumptions>

The core covariance and ellipsoid modules work with finite index types and
finite real matrices. The horizon is a natural number, so every Gramian is a
finite sum. The fixed-transition chain uses a square state matrix $A$ and an
explicit innovation factor $B$; the rectangular modules allow the state and
innovation dimensions to differ. These choices make the statements precise
without claiming that a neural state is finite, linear, or fully observed.

The concrete affine covariance theorem carries the probabilistic assumptions
that an algebraic recurrence would otherwise hide: a probability measure,
coordinatewise second-moment integrability, a specified covariance for the
innovation, and zero state--innovation cross-covariance. The separate abstract
interface is useful for composition, but its covariance laws are structure
fields. It should therefore be read as an adapter boundary rather than as an
independent derivation from probability theory.

Positive semidefiniteness is enough for the covariance recursion and Gramian
identities. It is not enough for inverse geometry. An inverse ellipsoid is
constructed only after a `Matrix.PosDef` witness is supplied or derived from a
finite block-span or full-rank gate. The affine image also requires `IsUnit F`.
This proof-carrying design prevents a singular matrix from silently entering an
inverse or log-determinant expression.

No long-time stability condition is needed for the finite-horizon identities.
Conversely, the absence of a stability assumption does not establish a
stationary law, asymptotic accessibility, or a valid infinite-horizon limit.

= Reproducibility and axiom audit <sec:s7-repro>

The project pins Lean 4.24.0 and its Mathlib dependency closure through
`lean-toolchain`, `lakefile.toml`, and `lake-manifest.json`. From the
repository root, the reproducibility gate on Windows is:

```powershell
cd formalization/lean
lake exe cache get Mathlib.LinearAlgebra.Matrix.PosDef
lake exe cache get Mathlib.Analysis.Matrix.Order
.\check.ps1 -LakeExe lake
```

The recorded run on 2026-09-09 completed the full build with 2,698 jobs and
reported 81 public theorem audits; the run on 2026-09-12, after the round-2
gates, completed 2,750 jobs and reported 320 audits. Warnings are treated as
errors. The audit
rejects proof placeholders and project-defined axioms; the accepted reports
use only Lean's standard foundational axioms `propext`, `Classical.choice`,
and `Quot.sound`. The audit is evidence about the source and environment at
that revision. It is not evidence that the scientific assumptions have been
measured.

The formal source is deliberately separated from the measurement pipeline.
It does not change the canonical MNPS $[m,d,e]$ or 9D definitions, missingness,
validity gates, provenance, estimator selection, or empirical outputs. A future
integration must preserve the distinction between a computed object and a
scientifically qualified object.

= Explicit boundaries <sec:s7-boundaries>

The following conclusions remain outside the formal claim:

- An inverse covariance ellipsoid is not a probability contour unless a
  distribution and a coverage convention are separately supplied.
- A covariance Gramian is not structural controllability, a classical control
  reachable set, or a demonstrated set of biologically reachable neural
  states.
- A theorem about a finite real chart does not identify that chart with a
  latent neural state, nor does it establish a Markov property for MNPS.
- A formal covariance recurrence does not validate residual quality, temporal
  sampling, condition separation, neighbourhood support, or out-of-sample
  prediction in a recording.
- Nondegeneracy of a model covariance does not prove that an empirical
  accessibility contrast is non-redundant, reproducible, or mechanistically
  informative.
- The formalization does not establish consciousness, experience, or any
  unique biological implementation of NDT control.

These limits are part of the result. In the terminology of the main article,
the development supports the mathematical architecture while leaving the
measurement and biological gates open.

= Toward a standalone formalization paper <sec:s7-future>

The present work is best placed as a substantial supplement because its
immediate contribution is to make the NDT architecture auditable. Much of the
covariance algebra is classical. Its value here is that the assumptions,
nondegeneracy conditions, and inverse-geometry licenses are explicit and
machine checked alongside the theory's distinction between measured state and
future law.

A later standalone paper would need a broader mathematical question. A useful
direction is: *which dynamical descriptors can be proved equivalent, and which
non-equivalences are essential, in a formal theory of accessibility?* Three
theorem families provide a natural route:

1. *Reduced observation and dynamical sufficiency:* the fibre criterion now
   covers PMF- and measure-valued kernels and finite protocol- and
   history-augmented states (`KernelSufficiency.lean`); the open step is a
   measurable-kernel and path-space version.
2. *Finite-horizon accessibility geometry:* the time-varying factor bridge for
   arbitrary PSD innovation sequences is closed
   (`StochasticCovarianceTimeVaryingFactor.lean`); the open step is to connect
   the licensed covariance object to declared estimator assumptions.
3. *Formal non-equivalences:* machine-checked counterexamples now separate
   occupancy from reachability, support from mass, covariance spread from
   committor, local linearization from finite-amplitude behaviour, and
   asymptotic stability from transient amplification
   (`FuturesNonEquivalence.lean`, `JacobianReactivity.lean`,
   `JacobianConversion.lean`); the open step is a general committor
   uniqueness theorem under finite absorption and the concrete
   chart/mechanism instantiation of the four inferential claim classes.

The NDT article can therefore cite this supplement for the bounded formal
infrastructure while a future paper develops the general theory of formally
certified dynamical descriptors. That separation preserves the immediate
credibility benefit without presenting mathematical verification as validation
of the biology.

#netn-box(title: [Suggested main-text sentence])[ 
  Selected mathematical components of NDT have been formalized and
  kernel-checked in Lean 4 under explicit finite-dimensional and
  nondegeneracy assumptions; the formalization supports the theory's
  architecture but does not validate empirical accessibility or biological
  mechanism (Supplementary Note S7).
]

= Data and source availability <sec:s7-availability>

The formal source, pinned build metadata, complete theorem inventory, and audit
script are in the project at `formalization/lean`. Their public availability
has not yet been verified; an accessible, revision-pinned source release is
needed for independent reproduction. The source-level diary records the L11
gate and its validation evidence at
`project/diary/300_20260909_lean_timevarying_nondegeneracy.md`.
The present note does not introduce a dataset, fitted parameter, or empirical
result.
