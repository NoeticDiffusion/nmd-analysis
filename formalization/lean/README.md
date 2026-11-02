# Noetic: a bounded Lean formalization

This project formalizes a finite reduced-state counterexample, a general
chart-fibre sufficiency criterion, and fixed-coefficient, finite-horizon
covariance algebra from the NDT v2 article and compendium.
It adds mathematical proofs without changing measurement code, canonical MNPS
[m,d,e] / 9D definitions, missingness, validity gates, or empirical claims.

## Reduced state

The latent state is a pair of Booleans (observed, hidden). Observation keeps the
first component; the deterministic transition sends (o,h) to (h,h). Two states
have the same current observation but different next observations. Consequently
no function of the current observation alone reproduces the next observation
for every latent state.

This is an existence example of information loss under observation, not a proof
that every projection loses predictive information or empirical MNPS violates a
Markov property. Deterministic transitions are represented directly; no general
stochastic kernel or conditional probability theorem is claimed.

### Chart-fibre sufficiency

For a surjective chart `π : X → Z` and deterministic future map `K : X → Y`,
`K` factors through the chart exactly when `K` is constant on every chart fibre.
The factor map is constructed by choosing a representative of each fibre. The
surjectivity assumption is explicit: without it, a codomain `Y` with no default
value leaves the factor map undefined outside the image of `π`. This is a
set-theoretic theorem, not a factorization theorem for probability kernels.

The Bool countermodel is connected to this criterion by a corollary: its
`nextChart` is not constant on the fibres of `chart`, so no deterministic chart
factorization exists.

Source: articles/NoeticDiffusionTheory_v2/Noetic Diffusion Theory - Neural State,
Dynamical Accessibility, and the Geometry of Possible Futures.typ, sections
"Dynamical accessibility as a transition law" and NDT-C1-C3.

## Covariance algebra

For finite real square matrices, with fixed A and positive semidefinite Q,
define C(0) = 0 and C(h+1) = A C(h) transpose(A) + Q. The results concern
symmetry, positive semidefiniteness, and the finite-sum representation
C(h) = sum_{k<h} A^k Q transpose(A)^k. No stability assumption on A is needed
for these finite-horizon statements.

The recursion is a definition in matrix algebra. The concrete one-step theorem
`Noetic/StochasticCovarianceConcrete.lean` now derives the corresponding identity
from Mathlib's scalar `ProbabilityTheory.covariance`: for a finite family of
real-valued random variables, a probability measure, coordinatewise `MemLp 2`
assumptions, specified innovation covariance, and zero state--innovation
cross-covariance,

`Cov(A X + b + ε) = A * Cov(X) * A.transpose + Q`.

`Noetic/StochasticCovariance.lean` retains an abstract covariance interface as a
separate L3a adapter layer. Its covariance-additivity and linearity laws are
explicit structure fields, so that module is useful for algebraic composition
but is method-limited until instantiated by a concrete probability model.
`Noetic/StochasticCovarianceHorizon.lean` supplies the L3b finite-horizon lift:
an explicitly indexed process is proved by induction to follow an arbitrary
covariance sequence satisfying the one-step recurrence, with a zero-initial
specialization to the algebraic `covariance A Q` sequence.

`Noetic/StochasticCovarianceTimeVarying.lean` supplies the next bounded lift:
the transition matrix `A h` and innovation covariance `Q h` may vary with the
step, and the same induction proves the corresponding covariance recurrence.
`Noetic/StochasticCovarianceTimeVaryingGramian.lean` then proves the matching
closed finite-sum form using an explicit transition product.

`Noetic/StochasticCovarianceTimeVaryingNondegeneracy.lean` is L11.  For
step-dependent square innovation factors `B h`, it defines the propagated
factor `Φ(T,h+1) * B h`, identifies its finite factor Gramian with the existing
time-varying covariance, and proves equivalent positive-definiteness,
detection, common-kernel, block-span and full-row-rank criteria.  The result is
finite and algebraic; it does not add stability, probability, empirical
reachability or biological claims.  This gate takes explicit factors as input;
selecting factors for an arbitrary positive-semidefinite `Q h` remains a
separate bridge.

`Noetic/CovarianceNondegeneracy.lean` adds the singular-covariance gate at the
finite factor level.  For `factorGramian B = sum_k B k * B k.transpose`,
`factorGramian_posDef_iff` proves that positive definiteness is equivalent to
every nonzero direction being detected by at least one factor transpose.  The
module also identifies the fixed-transition covariance with factors `A^k * B`
when `Q = B * B.transpose` and gives the corresponding finite-horizon
positive-definiteness criterion.  These are exact directional results and
introduce no regularization.  The equivalent rank/span formulation remains a
separate L7c block gate documented below.

`Noetic/CovarianceFixedTransitionFactor.lean` makes the L7d factorization
usable in that fixed-transition chain.  For `Q.PosSemidef`, it gives one
factor `B` satisfying both `Q = B * B.transpose` and the finite-horizon
identity `covariance A Q h = factorGramian (fun k : Fin h => A^k * B)`.  This is
an exact algebraic bridge; it does not select a numerical factorization or
make a reachability or empirical claim.

`Noetic/CovarianceFixedTransitionChain.lean` instantiates the L7b/L7c
 detection, common-kernel, block-span, and rank equivalences for the same
 `A^k * B` family.  It gives a direct detection-to-span equivalence,
 positive-definiteness equivalences for full block-column span and for
 `Matrix.rank = Fintype.card n`, plus an existential `Q.PosSemidef` corollary
carrying one factor through both characterizations.  These are finite
algebraic statements and do not establish empirical controllability or
reachability.  The interface also covers the zero horizon and empty state
index without adding a `Nonempty n` assumption.

`Noetic/CovarianceLicensing.lean` is L8.  It exposes the licensed-use
boundary for inverse-based covariance objects: positive definiteness implies
`IsUnit` and a strictly positive determinant, and therefore validates the
proof-carrying `logDetOfPosDef` inverse law.  The log-determinant object
cannot be constructed through this API without a `PosDef` witness.  Conversely,
positive semidefiniteness together with failed positive definiteness implies a
zero determinant.  The fixed-transition corollaries connect failed block-span
or full-rank gates to this singular boundary, both with an explicit PSD premise
and with PSD discharged internally for `B * B.transpose`.  These are algebraic
licenses only; no numerical regularization, empirical reachability, probability
coverage, or biological interpretation is added.

`Noetic/CovarianceEllipsoid.lean` is L9.  It defines a positive inverse
quadratic form and closed inverse ellipsoid only under an explicit `PosDef`
witness.  `LicensedInverseEllipsoid` carries that witness, while the
fixed-transition constructors obtain it from full block span or full block
rank.  The degenerate branch is represented by `IsEmpty`: failed
positive-definiteness produces no ordinary inverse-ellipsoid license.  This is
a validity boundary for the algebraic covariance object, not a claim about
probability coverage or empirical reachable sets.

`Noetic/CovarianceEllipsoidScaling.lean` is L10A.  It proves that positive
scalar scaling preserves `PosDef` and that the inverse quadratic form scales by
the reciprocal scalar.  `scaledReachabilityEllipsoid` keeps the same explicit
proof-carrying construction for a scaled fixed-transition covariance.  This
is an algebraic scaling law; it does not introduce a new normalization or an
empirical radius estimate.  The membership theorem
`mem_inverseEllipsoidOfPosDef_smul_iff` also identifies the scaled ellipsoid's
unit threshold with the original inverse quadratic form threshold `a`.

`Noetic/CovarianceEllipsoidPushForward.lean` is L10B.  It defines the affine
image `x ↦ F *ᵥ x + c` of a licensed inverse ellipsoid and the transported
covariance `F * M * Fᵀ`.  An explicit `IsUnit F` witness proves that the
transported covariance remains positive definite and constructs its
proof-carrying inverse-ellipsoid license.  The affine-image constructor also
requires that same invertibility witness, and the center-membership theorem
shows that the affine center is retained.  The full membership theorem proves
that the affine image is exactly the inverse ellipsoid of the transported
covariance translated to that center.  This is an algebraic identity; it does
not add a probability-support or empirical reachability claim.

`Noetic/CovarianceEllipsoidFixedTransition.lean` is L10C.  It specializes the
L10B equivalence to the fixed-transition finite-horizon covariance
`covariance A (B * Bᵀ) h`.  The affine fixed-transition constructor requires an
explicit `PosDef` witness for that covariance and an `IsUnit` witness for the
map; its membership theorem identifies the resulting set exactly with the
centered inverse ellipsoid of `F * covariance A (B * Bᵀ) h * Fᵀ`.  This remains
an algebraic specialization and does not establish empirical reachability or
probability coverage.

`Noetic/CovarianceEllipsoidFixedTransitionLicensing.lean` is L10D.  It derives
the fixed-transition `PosDef` witness internally from either the propagated
factor block-column span or the equivalent full-row-rank gate.  The affine map
still requires explicit `IsUnit F`, and each derived constructor has a full
membership equivalence with the centered inverse ellipsoid of the transformed
covariance.  This closes the proof-carrying composition from the earlier span
and rank gates without adding an empirical reachability claim.

`Noetic/CovarianceEllipsoidFixedTransitionCommon.lean` is L10E.  It packages
the shared covariance `PosDef` witness in `FixedTransitionCovarianceGate`, with
constructors for the block-span and full-rank validity gates.  A single affine
fixed-transition ellipsoid constructor and membership theorem then serve both
routes, while explicit `IsUnit F` and center `c` remain part of the API.  The
two L10D constructors are connected to this common API by exact equality
theorems.

`Noetic/CovarianceNondegeneracyRectangular.lean` is L7a: it generalizes the
factor criterion to `B : ι → Matrix n m ℝ`, so the state dimension `n` and the
number of innovation channels `m` may differ.  Its Gramian is still `n × n`,
while each detected factor direction is `m`-dimensional.  The exact
  positive-definiteness/detection equivalence is preserved; this module does
  not itself add a rectangular factorization theorem for `Q`.

`Noetic/CovarianceKernelEquivalence.lean` is L7b.  It names the rectangular
detection predicate and proves its exact equivalence with triviality of the
common kernel of all transpose factors.  The module also restates the result
directly as a positive-definiteness criterion for the rectangular Gramian.
No rank or block-span theorem is introduced at this stage.

`Noetic/CovarianceBlockSpan.lean` is L7c's bounded block-operator core.  It
concatenates the columns of all rectangular factors into a single matrix with
column index `ι × m` and proves that its transpose annihilates a state vector
exactly when every individual factor transpose does.  Common-kernel triviality
and all-direction detection are therefore equivalent to the corresponding
block-transpose statements.  The classical `Matrix.rank`/column-span bridge
is completed in the finite-index module below; this module itself makes no
rank or empirical controllability claim.

`Noetic/CovarianceBlockRank.lean` completes L7c's finite span/rank bridge.  For
finite factor and channel indices it defines the state-space column span and
proves that full span is equivalent to `Matrix.rank = Fintype.card n`, and
that both are equivalent to triviality of the block-transpose kernel.  The
result is a pure linear-algebra statement; it introduces no covariance,
reachability, or empirical controllability interpretation.

Source: articles/compendium/Noetic Diffusion Theory Compendium.typ,
"Local Stochastic Linearization" and "Covariance Recursion and Reachable Sets"
(lines 922-968 at implementation time); also v2's "Stochastic short-horizon
reachability" section.

Positive semidefinite matrices may be singular, including C(0) = 0. An inverse
ellipsoid needs additional nondegeneracy conditions. A covariance ellipsoid
alone does not specify probability coverage, distributional support, control
reachability, or consciousness. The fixed-transition block assembly, inverse
ellipsoids, SDEs, and slow-branch dynamics are outside this package.

## Round-2 gates (2026-09-12)

The modules below were specified in `project/lean/fable_ideas/` and
implemented in parallel batches; the statements remain finite, exact, and
model-internal.

`Noetic/StochasticCovarianceTimeVaryingFactor.lean` is L11b-1/L11b-2. It closes
the bridge left open by L11: an arbitrary positive-semidefinite step-indexed
innovation sequence `Q h` is assigned a factor sequence `B h` with
`Q h = B h * (B h)ᵀ`, chosen existentially from the L7d factorization at each
step (`exists_timeVarying_factor_sequence`). Composing that selection with the
four L11 nondegeneracy equivalences yields existential detection, common-kernel,
block-span, and block-rank criteria stated directly for `Q`, together with the
singular boundary `covarianceTimeVarying_det_eq_zero_of_not_posDef`, which
needed the new induction lemma `covarianceTimeVarying_posSemidef`. The factor is
existential, not computed: no Cholesky, no numerical algorithm, no
regularization.

`Noetic/CovarianceEllipsoidTimeVarying.lean` is L11b-3. It refactors the L10E
fixed-transition gate into a covariance-agnostic `CovarianceGate` (field `cov`
plus an explicit `PosDef` witness), with constructors from the L10E gate and
from the L11 time-varying block-span and block-rank criteria. One affine
ellipsoid constructor and membership theorem serve every route, and exact
equalities tie the L10D/L10E affine-ellipsoid API to the new one. Together with
L11b-1/2 this closes S7 inventory row 10.

`Noetic/JacobianReactivity.lean` is L12. It formalizes the algebraic core of the
spectral-abscissa/numerical-abscissa distinction: `symPart J = (J + Jᵀ)/2`
alone governs the Rayleigh quotient `v ↦ vᵀJv`, the antisymmetric part
contributes exactly zero, and any numerical-abscissa bound `w`
(`IsNumAbscissaBound J w`) upper-bounds every real eigenvalue, giving a
nonnegative reactivity gap. `numAbscissa J` (top Hermitian eigenvalue of the
symmetric part) is proved to be the least such bound and collapses for
symmetric `J`. Four exact `2 × 2` witnesses — the shear family
`[[-1,k],[0,-1]]`, the simulator-frozen pair `J1 = [[-1,6],[0,-3]]` and
`R1 = [[-2,-3/2],[3/2,-2]]`, and the discrete-time shear `[[1/2,c],[0,1/2]]` —
machine-check that negative eigenvalues (or modulus below one) do not exclude
instantaneous or single-step growth. No ODE, no `exp(tJ)`, no Lyapunov
argument, no MNJ-recovery or chart-invariance claim.

`Noetic/FuturesNonEquivalence.lean` and `Noetic/FuturesNonEquivalenceMaps.lean`
are L14, the finite counterexample catalogue for the manuscript's
"non-equivalent questions" table (all declarations carry an `L14_` prefix). Two
`Fin 2` chains share a stationary occupancy law but differ as one-step laws
(W2); the horizon-one identity `covariance A Q 1 = Q` gives
same-drift/different-diffusion and same-diffusion/different-drift pairs (W3);
two full-support `Fin 2 → ℝ` probability vectors with different mass witness
support-versus-mass (W1, replacing the `PMF.bernoulli` route, which left
unresolved `ℝ≥0` side conditions); a harmonic-vector committor predicate on
`Fin 3` and `Fin 4` absorbing chains gives a same-committor/different-spread
pair and a same-one-step-law/different-committor pair (W4, no uniqueness
claim); and two one-dimensional maps share `deriv` at `0` but differ in global
contraction versus escape, with the general neighbourhood-agreement lemma
`L14_agree_nhds_deriv_eq` (W5, W5′). The optional W6 stage-label witness was
not attempted.

`Noetic/KernelSufficiency.lean` is L13. It restates the surjective chart-fibre
criterion for `PMF`- and `Measure`-valued future laws
(`kernel_exists_factorization_iff_of_surjective`,
`kernel_measure_exists_factorization_iff_of_surjective`) and connects it back
to the deterministic case via the `PMF.pure` lift. A genuinely stochastic
countermodel upgrades the L0 Bool example: the two chart-matched hidden states
carry distinct `PMF Bool` next-observation laws (`PMF.bernoulli (3/4)` versus
`(1/4)`), and no chart-only stochastic kernel reproduces both. Two finite
protocol- and history-augmented models then certify the finite face of NDT-C3
and P6: a two-constructor `L13_Protocol` type (or a one-step "previous observed
bit") makes the chart-conditional future law depend on more than the chart, so
the plain chart is provably insufficient while (chart, protocol) or (chart,
history) is sufficient by construction. The protocol and history laws are
deterministic `Bool → Bool` maps; the criterion is pointwise law equality, with
no Markov, filtration, kernel-measurability, or path-space statement.

`Noetic/CovarianceSummaries.lean` is L16. It proves that the finite-horizon
covariance is Loewner-monotone in the innovation covariance
(`covariance_mono_Q`) and in the horizon (`covariance_horizon_mono`), with
trace inheriting the same monotonicity; that trace, determinant,
characteristic polynomial, the whole recursion, and the scalar effective
dimension `dEff M = (trace M)² / trace (M * M)` are invariant under orthogonal
conjugation `Uᵀ * M * U`; and that nonuniform rescaling is not such a symmetry
(`diag(2,1)` changes both trace and `dEff` of the identity). `dEff` is
scale-invariant, equals `Fintype.card n` on the identity and `1` on
`diag(1,0)`, with bounds `1 ≤ dEff ≤ card n` (upper bound eigenvalue-free for
symmetric `M`; lower bound via the spectral theorem for PSD `M`). Scaling laws
for trace, determinant, and `logDetOfPosDef` are included. Determinant
monotonicity under the Loewner order is not proved (no ready Mathlib lemma in
this snapshot). The module formalizes the `ε = 0` summary; no estimator,
regularization, coverage, or empirical-cone claim is added.

`Noetic/AccessOperators.lean` is L19. Reusing L12's `symPart`/`antisymPart`/
`IsNumAbscissaBound`, it proves that a scalar access gain `-(g•1) + K` on a
symmetric `K` is symmetric with Rayleigh quotient `-g * (v ⬝ᵥ v)`, hence an
exact numerical-abscissa bound and strict negative-definiteness for `g > 0` —
the algebraic reason scalar gain alone cannot realize the non-normal regime
exhibited by L12's shear witnesses. The congruence `M * H * Mᵀ` preserves
symmetry for any `M`, while plain `M * H` need not (`diag(2,1)` and
`[[1,1],[1,1]]`). Orthogonal conjugation preserves `trace` and `charpoly` by
pure ring algebra, while the defined `orientation` functional changes under an
orthogonal swap gate at matched total power (`9/10` to `1/10`). The eigenvalue
equation transports under any similarity (`alpha_similarity_invariant`), while
`IsNumAbscissaBound` does not: `P = diag(1/8, 1)` flips the Rayleigh quotient
of the shear at `![1,1]` from `2` to `-3/2` with the eigenvalue unchanged;
orthogonal similarity preserves any bound. No thalamic, committor-bias,
finite-time-gain, or empirical claim is added.

`Noetic/DriftSplitJacobian.lean` is L17. For symmetric mobility `M` and
curvature `H`, `M * H` is symmetric iff `M` and `H` commute
(`mulIsSymm_iff_commute`), with antisymmetric part exactly `(M*H - H*M)/2`;
the L19 witness `diag(2,1)`, `[[1,1],[1,1]]` gives a gradient system with
anisotropic constant mobility, zero non-conservative field and nonzero
rotational part, while isotropic mobility always yields a symmetric product.
The metric-variation remainder's index bookkeeping is pinned exactly and
vanishes for constant mobility or at a critical point; under a commuting
mobility the drift Jacobian's antisymmetric part equals the remainder's. A
`Fin 2` witness shows the split `(M, u)` is not identifiable from the drift
`b = -(M *ᵥ g) + u` and gradient `g` alone, while fixing `M` recovers `u`. The
polynomial witness `Φ = (x₀² + x₁²)/2`, `G = diag(1 + x₁², 1)` has an
asymmetric Jacobian at `(1,1)`, certified by two coordinate-slice `deriv`
computations (`-2 ≠ 0`). No Riemannian geometry, Itô correction, general
Clairaut theorem, or empirical claim is added.

`Noetic/SlowBranchModel.lean` is L18, a simulator-internal module (no S7
rows). It fixes `clip lo hi x = max lo (min hi x)` and proves its order facts
and the induction invariant that repeated clamping into `[0, Mmax]` stays there
(`slowBranch_clip_bounds`); the logistic `sigmoidGate k θ x` lies strictly in
`(0,1)`, is monotone in `x` for `k > 0`, antitone in `θ`, and equals `1/2` at
threshold. Zero-write and zero-coupling identities pin the simulator's
"zero coupling ⇒ baseline" finding as algebra; `guard_GC1`/`guard_GC2` are
exact single-branch guard inequalities (margin gate bound; bounded increments
⇒ at least `Mmax/(η·Δmax)` steps to saturate); `linking_ge_hub_term` and
companions give the finite-sum hub over-linking fact; `capHomogeneity_clip`
gives degree-one homogeneity of the cap. Multi-branch guards, the `fderiv`
corollary, and the front-loading rearrangement were not attempted.

`Noetic/ClosureEpochOperator.lean` is L20a–c, simulator-internal. A singular
factor (zero determinant, zero row or column) makes any product singular, with
an explicit zero-row propagation for the composite `E = Wout * D * Win`; the
`deriv` of the saturating clip is `0` on the open saturated sets and `1` on the
open interior (boundary points excluded); a two-block lag-embedding shift has
identity shift rows for every dynamics and its pure form squares to zero (the
three-block form was not attempted).

`Noetic/ObservabilityLevels.lean` is L20d–f. `L20_blockDiag_covariance` proves
that block-diagonal `A` and `Q` keep the finite-horizon recursion
block-diagonal at every horizon (with possibly different block index types);
`privateRatio M b = (b ⬝ᵥ (M *ᵥ b)) / ((b ⬝ᵥ b) * trace M / card n)` collapses
to `1` on isotropic covariance and takes `8/5` versus `2/5` on `diag(4,1)`
versus `diag(1,4)` at matched trace; and the four inferential claim classes,
modelled as abstract labels over a four-world Bool table, are proved pairwise
non-implicative by `decide`. The concrete chart/mechanism instantiation of the
claim classes was not attempted.

`Noetic/CovarianceSummariesTimeVarying.lean` closes four L16/L14 follow-ups.
It lifts Loewner monotonicity in the innovation covariance to the time-varying
recursion (`covarianceTimeVarying_mono_Q`), states the correct time-varying
horizon-increment fact (the innovation increment alone is PSD), and records an
explicit `Fin 1` counterexample showing that the naive time-varying horizon
monotonicity fails once `A` varies with the step
(`covarianceTimeVarying_horizon_not_mono`). It adds the orthogonal gauge
criterion `(Uᵀ * M * U).PosDef ↔ M.PosDef` and the unconditional congruence
`orthogonalConj_posSemidef`, a `Fin 2` witness that equal trace and
determinant do not force per-direction agreement, and the previously skipped
W6 witness: two `Fin 3` absorbing chains with the same one-step self-loop
occupancy at `mid` but different committor values. The same session replaced
`ClosureEpochOperator.lean`'s private clip copy by the shared `clip` from
`SlowBranchModel.lean`.

`Noetic/CommittorFinite.lean` is L15. It formalizes the finite-chain committor
as a harmonic boundary-value specification `L15_IsCommittor P A B q` with
`Finset`-valued destinations and proves its algebra: the complementary
committor under destination swap, the `mulVec` harmonic form, the degenerate
covering case, and closure under arbitrary real affine combinations (which is
exactly why an absorption hypothesis is needed for uniqueness). Explicit
closed-form committors are proved for the gambler's-ruin chain on `Fin (N+1)`,
symmetric (`i/N`) and biased (`(1 - rⁱ)/(1 - rᴺ)`, `r = (1-p)/p`), against
directly defined row-stochastic matrices. The difference of two committors is
harmonic and boundary-zero in general, and uniqueness is proved for the
symmetric gambler's-ruin chain by explicit induction. The general
finite-absorption uniqueness and maximum-principle theorems are not proved.

`Noetic/JacobianConversion.lean` is L21, the matrix-exponential layer over
L12/L19. It exhibits the exact similarity `P⁻¹ * J1 * P = diag(-1,-3)` with
self-inverse `P = [[1,3],[0,-1]]` and transports eigenvectors via L19's
`alpha_similarity_invariant`; proves the strict discrete-to-continuous
conversion bias `log a / dt < (a - 1)/dt`; proves `NormedSpace.exp ℝ N = 1 + N`
for square-zero `N` from the defining series and `exp (c • 1) = exp c • 1`,
combining them into the fully machine-checked shear propagator
`shearExp t k = exp(-t) • (1 + t • (k • E12))` with its semigroup law; certifies
`finiteTimeGain_gt_one` (`10/e > 1` at `k = 6`, `t = 1/2`) against the true
exponential; and proves `(exp Ω)ᵀ * exp Ω = 1` for antisymmetric `Ω`, so
`exp (t • R1) = exp(-2t) • exp (t • antisymPart R1)` with an exactly orthogonal
rotational factor. No `Matrix.log`, spectral norm, or ODE theory beyond these
identities is used.

The NDT-TRANS P0 set in `formalization/science_lead/sl_lean_001.md` is three
modules, T1–T6. `Noetic/TransGeometry.lean` holds the local transition `A`
fixed and varies the innovation: horizon-one covariance is exactly `Q` (T1),
Loewner order on `Q` propagates to every finite horizon (T2, a named re-export
of `covariance_mono_Q`), inverse Loewner order gives inverse-ellipsoid nesting
(T3a), and a swapped-diagonal pair `diag(2,1)` versus `diag(1,2)` shares trace
and determinant while a named direction lies in one unit gate and not the
other (T3b). `Noetic/TransHitting.lean` is a deterministic `Fin 3` path
`0 → 1 → 2 → 2 → ⋯`: terminal occupancy is not finite first-hit, they coincide
when the destination sets are disjoint and absorbing (T4), and finite first-hit
is monotone, implied by eventual hitting, and strictly weaker on a one-step
horizon (T5). `Noetic/TransKernelFunctionals.lean` records that kernel equality
implies every set-mass functional agrees, while two explicit three-state rows
share mass on `{0}` and differ on `{1}` (T6). Astra TRANS runs are
computational background, not hypotheses: the theorems are finite matrix and
path facts. No `ProbabilityTheory.Kernel` object, no Gaussian law, and no
empirical MNPS claim is introduced.

## Build and audit

Lean 4.24.0 and mathlib v4.24.0 are pinned by `lean-toolchain`, `lakefile.toml`,
and `lake-manifest.json` (including transitive Git revisions). With Lean/Elan
available on PATH, run from this directory:

```powershell
lake exe cache get Mathlib.LinearAlgebra.Matrix.PosDef
lake exe cache get Mathlib.Analysis.Matrix.Order
.\check.ps1
```

The cache command fetches this module's compiled dependency closure. Keep the
manifest when reproducing a build. `check.ps1` runs `lake build`, compiles
`Audit.lean`, and rejects missing theorem reports or axiom dependencies other
than Lean's standard `propext`, `Classical.choice`, and `Quot.sound`.
Warnings are errors. Source modules use a single `NoeticDiffusion` namespace;
the inventory check recognizes their public `theorem` declarations. If the
namespace or declaration style changes, update that check explicitly.

For this Windows checkout the portable runtime and dependency directory are
stored on H: and reached through ignored `.tools` and `.lake` junctions. This
is a local disk-space arrangement, not a dependency of the tracked sources.
The normal commands above also work in a fresh checkout with an installed
pinned toolchain. To use the local portable runtime:

```powershell
$env:PATH = (Resolve-Path '.tools\lean-dist\lean-4.24.0-windows\bin').Path + ';' + $env:PATH
.\check.ps1
```

Runtime downloads, dependencies, and build products are ignored by Git.

## Verified surface

- `Noetic/ReducedState.lean`: eight public theorems, including the same-present /
  different-future witness and impossibility of deterministic chart factorization.
- `Noetic/ReducedSufficiency.lean`: two public theorems, the general surjective
  chart-fibre factorization criterion and its Bool countermodel corollary.
- `Noetic/Covariance.lean`: thirteen public theorems covering the recurrence,
  real transpose identity, PSD and symmetry, positive definiteness for positive
  horizons when Q is positive definite, finite Gramian formula, zero cases,
  and PSD horizon increments.
- `Noetic/StochasticCovariance.lean`: two L3a abstract-interface theorems for
  the affine covariance step, with all algebraic laws exposed as assumptions.
- `Noetic/StochasticCovarianceConcrete.lean`: one measure-based L3 theorem,
  `covMatrix_affineNoise`, using Mathlib's scalar covariance and coordinatewise
  `MemLp 2` hypotheses.
- `Noetic/StochasticCovarianceHorizon.lean`: two L3b finite-horizon theorems,
  including the generic recurrence lift and its zero-initial specialization.
- `Noetic/StochasticCovarianceTimeVarying.lean`: two algebraic recurrence
  identities and two L4 time-varying finite-horizon theorems.
- `Noetic/StochasticCovarianceTimeVaryingGramian.lean`: two transition-product
  identities and the closed time-varying Gramian theorem.
- `Noetic/StochasticCovarianceTimeVaryingNondegeneracy.lean`: five exact L11
  theorems identifying the propagated-factor Gramian and its detection,
  kernel, span and rank positive-definiteness criteria.
- `Noetic/CovarianceNondegeneracy.lean`: three exact singular-covariance
  theorems for finite factor Gramians and the fixed-transition specialization.
- `Noetic/CovarianceNondegeneracyRectangular.lean`: one exact L7a theorem for
  rectangular factor Gramians with separate state and noise dimensions.
- `Noetic/CovarianceKernelEquivalence.lean`: two exact L7b theorems linking
  directional detection, common-kernel triviality and Gramian positive
  definiteness.
- `Noetic/CovarianceBlockSpan.lean`: three exact L7c block-operator theorems
  linking the common factor kernel and directional detection to one explicit
  block transpose.
- `Noetic/CovarianceBlockRank.lean`: two exact L7c finite span/rank theorems
  identifying full state-space column span and full row rank with the
  block-transpose kernel condition.
- `Noetic/CovariancePSD.lean`: one exact L7d factorization theorem: every
  finite real `Matrix.PosSemidef` square matrix admits `Q = B * B.transpose`.
  It uses Mathlib's modern C*-algebra factorization API and makes no
  numerical or empirical claim.
- `Noetic/CovarianceFixedTransitionFactor.lean`: one exact L7d bridge theorem
  carrying that factorization into the fixed-transition factors `A^k * B` and
  the finite-horizon covariance Gramian.
- `Noetic/CovarianceFixedTransitionChain.lean`: four exact fixed-transition
  corollaries connecting propagated-factor detection to block column span and
  covariance positive definiteness to span and full row rank, including a
  `Q.PosSemidef` existential bridge.
- `Noetic/CovarianceLicensing.lean`: eight exact L8 licensing theorems covering
  positive-definite `IsUnit`, determinant positivity and proof-carrying
  `logDetOfPosDef`, plus the PSD singular boundary and explicit/derived
  fixed-transition span/rank corollaries.
- `Noetic/CovarianceEllipsoid.lean`: six exact L9 theorems covering positivity
  of the inverse quadratic form, origin membership, proof-carrying
  fixed-transition ellipsoids, and the empty degenerate boundary.
- `Noetic/CovarianceEllipsoidScaling.lean`: two exact L10A theorems proving the
  reciprocal scaling law and the corresponding scaled-ellipsoid membership
  equivalence for a positive-definite inverse quadratic form.
- `Noetic/CovarianceEllipsoidPushForward.lean`: three exact L10B theorems
  proving positive-definiteness under an explicit invertible push-forward,
  affine center membership, and the full affine-image/centered-ellipsoid
  membership equivalence.
- `Noetic/CovarianceEllipsoidFixedTransition.lean`: one exact L10C theorem
  specializing the affine-image/centered-ellipsoid equivalence to the
  fixed-transition covariance.
- `Noetic/CovarianceEllipsoidFixedTransitionLicensing.lean`: two exact L10D
  theorems deriving the covariance license from block span and full rank, each
  with the corresponding affine-image/centered-ellipsoid equivalence.
- `Noetic/CovarianceEllipsoidFixedTransitionCommon.lean`: three exact L10E
  theorems for the common gate membership equivalence and the span/rank API
  equalities.
- `Noetic/StochasticCovarianceTimeVaryingFactor.lean`: seven exact L11b
  theorems: existential factor selection for PSD sequences, time-varying
  positive semidefiniteness, four existential nondegeneracy equivalences, and
  the singular determinant boundary.
- `Noetic/CovarianceEllipsoidTimeVarying.lean`: four exact L11b-3 theorems for
  the covariance-agnostic gate membership equivalence and the three equalities
  with the L10D/L10E affine-ellipsoid API.
- `Noetic/JacobianReactivity.lean`: twenty exact L12 theorems covering the
  symmetric/antisymmetric decomposition, Rayleigh-quotient bounds, the exact
  numerical abscissa and its tightness, and the shear/`J1`/`R1`/discrete-shear
  witnesses.
- `Noetic/FuturesNonEquivalence.lean` and `Noetic/FuturesNonEquivalenceMaps.lean`:
  twenty-seven exact L14 theorems (twenty-three finite-chain and vector
  witnesses, four one-dimensional-map facts).
- `Noetic/KernelSufficiency.lean`: eleven exact L13 theorems (kernel-fibre
  criteria, stochastic Bool countermodel, protocol and history augmentation).
- `Noetic/CovarianceSummaries.lean`: nineteen exact L16 theorems (Loewner and
  horizon monotonicity, orthogonal gauge invariance, `dEff` identities and
  bounds, rescaling laws and the rescaling counterexample).
- `Noetic/AccessOperators.lean`: twenty-seven exact L19 theorems (scalar gain,
  congruence, orthogonal gating and orientation, similarity covariance).
- `Noetic/DriftSplitJacobian.lean`: twenty-five exact L17 theorems
  (symmetric-product criterion, remainder algebra, non-identifiability
  witness, polynomial asymmetry witness with `deriv`).
- `Noetic/SlowBranchModel.lean`: twenty-four exact L18 theorems (clip, sigmoid
  gate, zero-coupling identities, guards, hub over-linking, cap homogeneity;
  simulator-internal).
- `Noetic/ClosureEpochOperator.lean`: fourteen exact L20a–c theorems
  (singularity propagation, clip derivative, lag shift; simulator-internal).
- `Noetic/ObservabilityLevels.lean`: five exact L20d–f theorems
  (block-diagonal invariance, private ratio, claim-class non-implication).
- `Noetic/CovarianceSummariesTimeVarying.lean`: eleven exact follow-up
  theorems (time-varying Loewner monotonicity, innovation increment, horizon
  counterexample, orthogonal `PosDef`/`PosSemidef` gauge, calibration witness,
  W6 witness).
- `Noetic/CommittorFinite.lean`: twenty-two exact L15 theorems (committor
  algebra, symmetric and biased gambler's ruin, uniqueness core and
  gambler's-ruin uniqueness).
- `Noetic/JacobianConversion.lean`: twenty exact L21 theorems (similarity
  witness, conversion bias, nilpotent and scalar exponentials, shear propagator,
  finite-time gain, rotation-pair orthogonality).
- `Noetic/TransGeometry.lean`: fourteen exact TRANS P0 theorems (T1 horizon-one
  covariance, T2 Loewner propagation, T3 inverse order and swapped-diagonal
  gate witness).
- `Noetic/TransHitting.lean`: thirteen exact TRANS P0 theorems (T4 occupancy
  versus finite first-hit, T5 monotone finite/eventual committor predicates).
- `Noetic/TransKernelFunctionals.lean`: six exact TRANS P0 theorems (T6 kernel
  equality versus one set-mass functional).
- `Audit.lean`: 353 dependency reports, one per public theorem (33 added by
  the TRANS P0 set). The reduced-state proofs have no axiom dependencies; all
  other proofs use only `propext`, `Classical.choice`, and `Quot.sound` from
  the standard foundation.

The pinned build and complete audit passed on 2026-09-09 (through L11), on
2026-09-12 (round-2 gates; 2,750 build jobs, 320 audit reports), and on
2026-09-14 (TRANS P0; 2,753 build jobs, 353 audit reports). Theorem names
must be ASCII because `check.ps1` matches `[A-Za-z0-9_.]`; dotted names such
as `CovarianceGate.mem_affineEllipsoid_iff` are audited under their full
qualified name. See the local diaries
`project/diary/300_20260909_lean_timevarying_nondegeneracy.md`,
`project/diary/332_20260912_lean_round2_implementation.md`, and
`project/diary/342_20260914_lean_trans_hierarchy.md` at the repository
root for exact commands, source hashes, environment handling, and review
evidence.

The acceptance gate requires successful Lean compilation of all project modules,
no proof placeholders or project-defined axioms, and independent review of the
statements and their relationship to the source articles. Numerical simulations
and real-data tests are not substitutes for this gate and are not required for
these purely mathematical examples.
