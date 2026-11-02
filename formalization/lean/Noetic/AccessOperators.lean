import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.LinearAlgebra.Matrix.Symmetric
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
import Mathlib.LinearAlgebra.Matrix.Charpoly.Basic
import Mathlib.LinearAlgebra.Matrix.Trace
import Noetic.JacobianReactivity

/-!
# L19: access-control operators on a frozen landscape

This module formalizes NDT v2's specialization of the two-operator drift SDE
`dX = A_sig b0(X) dt + A_noise Sigma0 dW` (manuscript lines 759-768) and the
gradient-flow HELS-A form `dX = -A_H grad V(X) dt + sigma dW` (793-806) to the
algebraic contrast between a *scalar* access gain and a *directional* one, and
to the coordinate (chart) dependence of the numerical abscissa versus the
chart-independence of the spectral abscissa. It maps onto the simulator's
`thalamic_access` article's `eq:scalar-signal` (~128-135), `eq:m-self-adjoint`
(~197), the rotation-covariance claim (~171), and the metric-dependence table
(~626-634), and onto TA-1/TA-3 (`tests/thalamus/test_ta1_directional_diffusion.py:40-58`,
`hels_a/a0b/invariants.py:67-98,191-207`).

NDT source: `articles/NoeticDiffusionTheory_v2/...GoPF.typ` lines 759-768,
793-806, 561-568; `project/lean/fable_ideas/09_control_operators_thalamic_hels.md`.

## Claim boundary

This module proves four disjoint algebraic facts about real square matrices,
reusing `symPart`/`antisymPart`/`IsNumAbscissaBound` from `Noetic.JacobianReactivity`
(L12) and adding no new definitions of those objects:

* **L19a (scalar gain).** A pure or offset scalar gain `-(g*1) + K` on a
  symmetric `K` is itself symmetric (`antisymPart` vanishes identically), and
  the pure-gain Rayleigh quotient is exactly `-g * (v dot v)`, giving the
  exact numerical-abscissa bound `-g` and strict negative-definiteness for
  `g > 0`. This is the algebraic reason a *scalar* access operator can never
  produce the non-normal `alpha < 0 < omega` regime that L12c's shear
  witnesses exhibit for a directional operator.
* **L19b (congruence).** The congruence map `H -> M H Mᵗ` preserves symmetry
  for *any* square `M`, but plain left multiplication `M H` need not be
  symmetric even when both `M` and `H` are -- an explicit 2x2 witness
  (`M = diag(2,1)`, `H = [[1,1],[1,1]]`) exhibits `M H` non-symmetric while
  `M H M` is symmetric (`M` itself being symmetric here).
* **L19c (orthogonal gating).** Orthogonal conjugation `Qᵗ A Q` (`Qᵗ Q = 1`)
  preserves `trace` and `charpoly` exactly, for any square matrix `A` --
  proved by pure ring/trace-cycle algebra, no eigenvalue machinery. A defined
  `orientation b a := (b dot (a *ᵥ b)) / ((b dot b) * trace a)` nonetheless
  changes under an explicit orthogonal swap gate (`a = diag(9,1)`, the
  coordinate-swap `Q`, probe `b = e1`): orientation `9/10` before, `1/10`
  after, while trace (`10`) and characteristic polynomial are identical --
  the exact "matched total power, rotated dispersion" phenomenon.
* **L19d (coordinate covariance).** Similarity conjugation and the
  eigenvalue equation transport exactly for *any* invertible `P`
  (`(P⁻¹ J P) v = lam v <-> J (P v) = lam (P v)`) -- the spectral abscissa
  `alpha` is a genuine similarity invariant. `IsNumAbscissaBound` is not: an
  explicit non-orthogonal similarity (`P = diag(1/8,1)` conjugating L12c's
  `shear 4`) sends the Rayleigh quotient at the *same* probe vector `![1,1]`
  from `+2` to `-3/2`, although both `shear 4` and its conjugate have the
  identical eigenvalue `-1` (`shear_all_eigenvalues_neg`, reused unchanged
  from L12c). Conversely, orthogonal similarity (`Qᵗ Q = 1`) exactly
  preserves any numerical-abscissa bound, matching L19c's trace/charpoly
  invariance.

Out of scope: no thalamus/TRN/hippocampus/replay claim; no committor-bias or
Monte-Carlo result (HELS-A0B `q(H_R) ≠ q(H_L)` is not formalized); no
finite-time gain `G(tau) = sigma_max(exp(J tau))` (that is `Matrix.exp`,
deferred to a later gate); no PosDef square-root API (`M^(1/2)`) and no
general "`A_sig` symmetric-PD and `H` symmetric commute iff `A_sig H`
symmetric" theorem (L17a) -- the L19b witness is proved by direct 2x2
computation instead, so L17a's general commuting criterion is not needed and
is not proved here. No claim that any of these algebraic facts by itself
establishes empirical reachability, probability coverage, or a biological
interpretation.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

/-! ## L19a: scalar-gain operators cannot realize the stable-reactive regime -/

omit [Fintype n] in
/-- A scalar access gain `-(g*1)` offset by a symmetric operator `K` is
itself symmetric: `J = -(g*1) + K`. This is the algebraic content of
`eq:scalar-signal`: a *scalar* `A_sig` always commutes with any `H`, so
`J = -A_sig H` inherits `H`'s symmetry exactly. -/
theorem scalarGain_isSymm [DecidableEq n] (g : ℝ) (K : Matrix n n ℝ) (hK : K.IsSymm) :
    (-(g • (1 : Matrix n n ℝ)) + K).IsSymm := by
  show (-(g • (1 : Matrix n n ℝ)) + K).transpose = -(g • (1 : Matrix n n ℝ)) + K
  rw [Matrix.transpose_add, Matrix.transpose_neg, Matrix.transpose_smul, Matrix.transpose_one, hK]

omit [Fintype n] in
/-- General fact reused internally: a symmetric matrix has zero antisymmetric
part (via L12's `symPart_add_antisymPart` and `symPart_eq_self_of_isSymm`). -/
private lemma L19_isSymm_antisymPart_eq_zero {J : Matrix n n ℝ} (hJ : J.IsSymm) :
    antisymPart J = 0 := by
  have h := symPart_add_antisymPart J
  rw [symPart_eq_self_of_isSymm hJ] at h
  have h2 : J + antisymPart J = J + 0 := by rw [h, add_zero]
  exact add_left_cancel h2

omit [Fintype n] in
/-- Consequently the scalar-gain Jacobian has no antisymmetric ("rotational")
part at all: `alpha = omega` collapses exactly, as in L12b's symmetric case. -/
theorem scalarGain_antisymPart_eq_zero [DecidableEq n] (g : ℝ) (K : Matrix n n ℝ)
    (hK : K.IsSymm) : antisymPart (-(g • (1 : Matrix n n ℝ)) + K) = 0 :=
  L19_isSymm_antisymPart_eq_zero (scalarGain_isSymm g K hK)

/-- The Rayleigh quotient of a pure scalar gain `-(g*1)` is exactly
`-g * (v dot v)` for every `v`: scalar access gain scales the quadratic form
uniformly in every direction, with no directional structure at all. -/
theorem scalarGain_dotProduct_mulVec [DecidableEq n] (g : ℝ) (v : n → ℝ) :
    v ⬝ᵥ ((-(g • (1 : Matrix n n ℝ))) *ᵥ v) = -g * (v ⬝ᵥ v) := by
  have h1 : (-(g • (1 : Matrix n n ℝ))) *ᵥ v = -(g • v) := by
    rw [Matrix.neg_mulVec, Matrix.smul_mulVec, Matrix.one_mulVec]
  rw [h1, dotProduct_neg, dotProduct_smul, smul_eq_mul]
  ring

/-- Hence `-g` is an exact (not merely an upper) numerical-abscissa bound for
the pure scalar gain `-(g*1)`. -/
theorem scalarGain_isNumAbscissaBound [DecidableEq n] (g : ℝ) :
    IsNumAbscissaBound (-(g • (1 : Matrix n n ℝ))) (-g) :=
  fun v => le_of_eq (scalarGain_dotProduct_mulVec g v)

private lemma L19_dotProduct_self_pos_of_ne_zero {v : n → ℝ} (hv : v ≠ 0) :
    0 < v ⬝ᵥ v := by
  have hex : ∃ i, v i ≠ 0 := by
    by_contra h
    push_neg at h
    exact hv (funext h)
  obtain ⟨i, hi⟩ := hex
  have hpos : 0 < v i * v i := mul_self_pos.mpr hi
  have hle : v i * v i ≤ v ⬝ᵥ v := by
    unfold dotProduct
    exact Finset.single_le_sum (fun j _ => mul_self_nonneg (v j)) (Finset.mem_univ i)
  linarith

/-- For `g > 0`, the pure scalar-gain quadratic form is strictly negative on
every nonzero direction: an instantaneous Lyapunov-decreasing, non-reactive
regime with no exceptional growth direction whatsoever -- the stable-reactive
regime `alpha < 0 < omega` that a *directional* operator can realize (L12c's
`shear`/`J1` witnesses) is algebraically unreachable by scalar gain alone. -/
theorem scalarGain_negDef_of_pos [DecidableEq n] {g : ℝ} (hg : 0 < g) {v : n → ℝ}
    (hv : v ≠ 0) : v ⬝ᵥ ((-(g • (1 : Matrix n n ℝ))) *ᵥ v) < 0 := by
  rw [scalarGain_dotProduct_mulVec]
  have hvv : 0 < v ⬝ᵥ v := L19_dotProduct_self_pos_of_ne_zero hv
  nlinarith [mul_pos hg hvv]

/-! ## L19b: M-similarity / congruence and the hidden self-adjointness -/

/-- The congruence map `H -> M H Mᵗ` preserves symmetry for *any* square `M`
(no invertibility or definiteness of `M` needed for this direction). This is
`eq:m-self-adjoint`'s algebraic core: even when the plain product `M H` loses
symmetry, the *congruence* `M H Mᵗ` never does. -/
theorem gating_congruence_isSymm (M H : Matrix n n ℝ) (hH : H.IsSymm) :
    (M * H * M.transpose).IsSymm := by
  show (M * H * M.transpose).transpose = M * H * M.transpose
  rw [Matrix.transpose_mul, Matrix.transpose_mul, Matrix.transpose_transpose, hH, mul_assoc]

/-- Congruence witness `M`: `diag(2, 1)`, symmetric and positive definite. -/
def gating_congruenceWitnessM : Matrix (Fin 2) (Fin 2) ℝ := !![2, 0; 0, 1]

/-- Congruence witness `H`: the symmetric, positive-semidefinite (singular)
matrix `[[1,1],[1,1]]`. -/
def gating_congruenceWitnessH : Matrix (Fin 2) (Fin 2) ℝ := !![1, 1; 1, 1]

theorem gating_congruenceWitnessM_isSymm : gating_congruenceWitnessM.IsSymm := by
  apply Matrix.IsSymm.ext
  intro i j
  fin_cases i <;> fin_cases j <;> simp [gating_congruenceWitnessM]

theorem gating_congruenceWitnessH_isSymm : gating_congruenceWitnessH.IsSymm := by
  apply Matrix.IsSymm.ext
  intro i j
  fin_cases i <;> fin_cases j <;> simp [gating_congruenceWitnessH]

/-- The witness `M = diag(2,1)`, `H = [[1,1],[1,1]]`: `M H = [[2,2],[1,1]]` is
**not** symmetric, even though both factors are. -/
theorem gating_congruenceWitness_mul_not_isSymm :
    ¬ (gating_congruenceWitnessM * gating_congruenceWitnessH).IsSymm := by
  intro h
  have hEq : (gating_congruenceWitnessM * gating_congruenceWitnessH) 1 0
      = (gating_congruenceWitnessM * gating_congruenceWitnessH) 0 1 := by
    have := congrFun (congrFun h 0) 1
    simpa [Matrix.transpose_apply] using this
  simp [Matrix.mul_apply, Fin.sum_univ_two, gating_congruenceWitnessM, gating_congruenceWitnessH]
    at hEq

/-- The congruence `M H M` (`M` symmetric here, so `M H Mᵗ = M H M`) **is**
symmetric: `M H M = [[4,2],[2,1]]`. -/
theorem gating_congruenceWitness_congruence_isSymm :
    (gating_congruenceWitnessM * gating_congruenceWitnessH * gating_congruenceWitnessM).IsSymm := by
  have h := gating_congruence_isSymm gating_congruenceWitnessM gating_congruenceWitnessH
    gating_congruenceWitnessH_isSymm
  rwa [gating_congruenceWitnessM_isSymm] at h

/-! ## L19c: orthogonal gating preserves trace and spectrum, not orientation -/

/-- Orthogonal conjugation preserves trace exactly, for any square `A`: no
Hermitian/eigenvalue machinery, just the cyclic trace identity and
`Qᵗ Q = 1 => Q Qᵗ = 1` (`Matrix.mul_eq_one_comm`, valid for square matrices
over a commutative semiring). -/
theorem gating_trace_eq [DecidableEq n] {Q A : Matrix n n ℝ} (hQ : Q.transpose * Q = 1) :
    Matrix.trace (Q.transpose * A * Q) = Matrix.trace A := by
  have hQQ : Q * Q.transpose = 1 := Matrix.mul_eq_one_comm.mp hQ
  calc Matrix.trace (Q.transpose * A * Q) = Matrix.trace (Q * Q.transpose * A) :=
        Matrix.trace_mul_cycle Q.transpose A Q
    _ = Matrix.trace (1 * A) := by rw [hQQ]
    _ = Matrix.trace A := by rw [one_mul]

/-- Orthogonal conjugation preserves the characteristic polynomial exactly,
for any square `A`: pure Cayley-Hamilton-free ring algebra via
`Matrix.charpoly_mul_comm`, `(A B).charpoly = (B A).charpoly`. -/
theorem gating_charpoly_eq [DecidableEq n] {Q A : Matrix n n ℝ} (hQ : Q.transpose * Q = 1) :
    (Q.transpose * A * Q).charpoly = A.charpoly := by
  have hQQ : Q * Q.transpose = 1 := Matrix.mul_eq_one_comm.mp hQ
  calc (Q.transpose * A * Q).charpoly = (Q * (Q.transpose * A)).charpoly :=
        Matrix.charpoly_mul_comm (Q.transpose * A) Q
    _ = (Q * Q.transpose * A).charpoly := by rw [mul_assoc]
    _ = (1 * A).charpoly := by rw [hQQ]
    _ = A.charpoly := by rw [one_mul]

private lemma L19_dotProduct_mulVec_transpose_mulVec (A : Matrix n n ℝ) (u : n → ℝ) :
    u ⬝ᵥ ((A.transpose * A) *ᵥ u) = (A *ᵥ u) ⬝ᵥ (A *ᵥ u) := by
  rw [← Matrix.mulVec_mulVec, Matrix.dotProduct_mulVec, Matrix.vecMul_transpose]

/-- Orthogonal conjugation also preserves any numerical-abscissa bound
exactly: the norm-preserving change of variables `v -> Q v` carries the
Rayleigh quotient of `Qᵗ A Q` at `v` to the Rayleigh quotient of `A` at `Q v`.
Contrast with `L19_witness_omega_not_similarity_invariant` below, where a
*non*-orthogonal similarity changes the Rayleigh quotient's sign at a fixed
vector. -/
theorem gating_isNumAbscissaBound_orthogonal [DecidableEq n] {Q J : Matrix n n ℝ} {w : ℝ}
    (hQ : Q.transpose * Q = 1) (hbound : IsNumAbscissaBound J w) :
    IsNumAbscissaBound (Q.transpose * J * Q) w := by
  intro v
  have hlhs : v ⬝ᵥ ((Q.transpose * J * Q) *ᵥ v) = (Q *ᵥ v) ⬝ᵥ (J *ᵥ (Q *ᵥ v)) := by
    rw [← Matrix.mulVec_mulVec, ← Matrix.mulVec_mulVec, Matrix.dotProduct_mulVec,
      Matrix.vecMul_transpose]
  have hrhs : v ⬝ᵥ v = (Q *ᵥ v) ⬝ᵥ (Q *ᵥ v) := by
    have h := L19_dotProduct_mulVec_transpose_mulVec Q v
    rwa [hQ, Matrix.one_mulVec] at h
  rw [hlhs, hrhs]
  exact hbound (Q *ᵥ v)

/-- The orientation of a symmetric operator `a` relative to a probe direction
`b`: the Rayleigh quotient of `a` at `b`, normalized by `b`'s squared norm and
`a`'s trace (the simulator's `A_bD` without the regularizing `epsilon`). -/
def orientation {m : Type*} [Fintype m] (b : m → ℝ) (a : Matrix m m ℝ) : ℝ :=
  (b ⬝ᵥ (a *ᵥ b)) / ((b ⬝ᵥ b) * Matrix.trace a)

/-- Orientation witness `Q`: the 90-degree coordinate swap. -/
def orientation_witnessQ : Matrix (Fin 2) (Fin 2) ℝ := !![0, 1; 1, 0]

/-- Orientation witness `a`: the diagonal diffusion tensor `diag(9, 1)`. -/
def orientation_witnessA : Matrix (Fin 2) (Fin 2) ℝ := !![9, 0; 0, 1]

/-- Orientation witness probe direction: the first coordinate axis. -/
def orientation_witnessB : Fin 2 → ℝ := ![1, 0]

/-- `orientation_witnessQ` is orthogonal (`Qᵗ Q = 1`; it is in fact its own
transpose and its own inverse, being a coordinate swap). -/
theorem orientation_witnessQ_orthogonal :
    orientation_witnessQ.transpose * orientation_witnessQ = 1 := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [orientation_witnessQ, Matrix.mul_apply, Fin.sum_univ_two, Matrix.transpose_apply]

/-- Before gating: orientation of `diag(9,1)` along `e1` is `9/10`. -/
theorem orientation_witnessA_eq :
    orientation orientation_witnessB orientation_witnessA = 9 / 10 := by
  unfold orientation
  simp [orientation_witnessA, orientation_witnessB, Matrix.mulVec, dotProduct, Fin.sum_univ_two,
    Matrix.trace, Matrix.diag]
  norm_num

/-- After the orthogonal swap gate: orientation of the *same* diffusion power
along the *same* probe `e1` is `1/10`, although (by `gating_trace_eq`,
`gating_charpoly_eq` below) trace and characteristic polynomial are
unchanged -- "matched total power, rotated dispersion" (`eq:m-self-adjoint`,
TA-1 invariant 22). -/
theorem orientation_witnessA_gated_eq :
    orientation orientation_witnessB
      (orientation_witnessQ.transpose * orientation_witnessA * orientation_witnessQ) = 1 / 10 := by
  unfold orientation
  simp [orientation_witnessQ, orientation_witnessA, orientation_witnessB, Matrix.mulVec,
    dotProduct, Fin.sum_univ_two, Matrix.mul_apply, Matrix.trace, Matrix.diag,
    Matrix.transpose_apply]
  norm_num

/-- The explicit sign/value change: orientation is not gauge-invariant under
orthogonal gating even though trace and spectrum are. -/
theorem orientation_changes_under_orthogonal_gating :
    orientation orientation_witnessB
      (orientation_witnessQ.transpose * orientation_witnessA * orientation_witnessQ)
      ≠ orientation orientation_witnessB orientation_witnessA := by
  rw [orientation_witnessA_gated_eq, orientation_witnessA_eq]
  norm_num

/-- Trace is exactly preserved by the orthogonal swap gate on this witness
(explicit instance of `gating_trace_eq`). -/
theorem orientation_witness_trace_eq :
    Matrix.trace (orientation_witnessQ.transpose * orientation_witnessA * orientation_witnessQ)
      = Matrix.trace orientation_witnessA :=
  gating_trace_eq orientation_witnessQ_orthogonal

/-- The characteristic polynomial is exactly preserved by the orthogonal swap
gate on this witness (explicit instance of `gating_charpoly_eq`). -/
theorem orientation_witness_charpoly_eq :
    (orientation_witnessQ.transpose * orientation_witnessA * orientation_witnessQ).charpoly
      = orientation_witnessA.charpoly :=
  gating_charpoly_eq orientation_witnessQ_orthogonal

/-! ## L19d: coordinate covariance -- alpha is similarity-invariant, the
numerical-abscissa bound is not -/

private lemma L19_mulVec_assoc3 (A B C : Matrix n n ℝ) (v : n → ℝ) :
    (A * B * C) *ᵥ v = A *ᵥ (B *ᵥ (C *ᵥ v)) := by
  rw [← Matrix.mulVec_mulVec, ← Matrix.mulVec_mulVec]

/-- **Alpha is similarity-invariant.** For any invertible `P`, the eigenvalue
equation transports exactly between the similar operator `P⁻¹ J P` and `J`
itself: `w` is an eigenvector of `P⁻¹ J P` with eigenvalue `lam` iff `P w` is
an eigenvector of `J` with the same eigenvalue `lam`. This is the precise
algebraic sense in which the spectral abscissa `alpha` does not depend on the
coordinate chart -- contrast with `L19_witness_omega_not_similarity_invariant`
below. -/
theorem alpha_similarity_invariant [DecidableEq n] {J P : Matrix n n ℝ} (hP : IsUnit P)
    (w : n → ℝ) (lam : ℝ) :
    (P⁻¹ * J * P) *ᵥ w = lam • w ↔ J *ᵥ (P *ᵥ w) = lam • (P *ᵥ w) := by
  have hPdet : IsUnit P.det := (Matrix.isUnit_iff_isUnit_det P).mp hP
  have hL : (P⁻¹ * J * P) *ᵥ w = P⁻¹ *ᵥ (J *ᵥ (P *ᵥ w)) := L19_mulVec_assoc3 P⁻¹ J P w
  rw [hL]
  constructor
  · intro h
    have h2 : P *ᵥ (P⁻¹ *ᵥ (J *ᵥ (P *ᵥ w))) = P *ᵥ (lam • w) := by rw [h]
    have h3 : P *ᵥ (P⁻¹ *ᵥ (J *ᵥ (P *ᵥ w))) = (P * P⁻¹) *ᵥ (J *ᵥ (P *ᵥ w)) :=
      Matrix.mulVec_mulVec (J *ᵥ (P *ᵥ w)) P P⁻¹
    rw [h3, Matrix.mul_nonsing_inv P hPdet, Matrix.one_mulVec, Matrix.mulVec_smul] at h2
    exact h2
  · intro h
    have h2 : P⁻¹ *ᵥ (J *ᵥ (P *ᵥ w)) = P⁻¹ *ᵥ (lam • (P *ᵥ w)) := by rw [h]
    have h3 : P⁻¹ *ᵥ (lam • (P *ᵥ w)) = lam • ((P⁻¹ * P) *ᵥ w) := by
      rw [Matrix.mulVec_smul, Matrix.mulVec_mulVec]
    rw [h3, Matrix.nonsing_inv_mul P hPdet, Matrix.one_mulVec] at h2
    exact h2

/-- Similarity witness `P = diag(1/8, 1)`, deliberately non-orthogonal. -/
def L19_similarityWitnessP : Matrix (Fin 2) (Fin 2) ℝ := !![1 / 8, 0; 0, 1]

theorem L19_similarityWitnessP_isUnit : IsUnit L19_similarityWitnessP := by
  rw [Matrix.isUnit_iff_isUnit_det]
  have hdet : L19_similarityWitnessP.det = 1 / 8 := by
    simp [L19_similarityWitnessP, Matrix.det_fin_two_of]
  rw [hdet]
  exact isUnit_iff_ne_zero.mpr (by norm_num)

/-- Intertwining identity `P * shear 4 = shear (1/2) * P` (no inverse
needed): `P` conjugates L12c's shear-4 witness into the shear-1/2 witness. -/
theorem L19_similarityWitness_intertwine :
    L19_similarityWitnessP * shear 4 = shear (1 / 2) * L19_similarityWitnessP := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [L19_similarityWitnessP, shear, Matrix.mul_apply, Fin.sum_univ_two]
  all_goals norm_num

/-- Hence `P * shear 4 * P⁻¹ = shear (1/2)` exactly. -/
theorem L19_similarityWitness_conj :
    L19_similarityWitnessP * shear 4 * L19_similarityWitnessP⁻¹ = shear (1 / 2) := by
  rw [L19_similarityWitness_intertwine, mul_assoc,
    Matrix.mul_nonsing_inv L19_similarityWitnessP
      ((Matrix.isUnit_iff_isUnit_det _).mp L19_similarityWitnessP_isUnit), mul_one]

/-- The Rayleigh quotient of the original shear-4 witness at `![1,1]` is `2`
(reprise of L12c's computation). -/
theorem L19_similarityWitness_rayleigh_orig :
    (![1, 1] : Fin 2 → ℝ) ⬝ᵥ (shear 4 *ᵥ ![1, 1]) = 2 := by
  simp [shear, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
  norm_num

/-- The Rayleigh quotient of the *similar* operator `P * shear 4 * P⁻¹` at
the *same* vector `![1,1]` is `-3/2`: strictly negative, opposite sign. -/
theorem L19_similarityWitness_rayleigh_conj :
    (![1, 1] : Fin 2 → ℝ) ⬝ᵥ
      ((L19_similarityWitnessP * shear 4 * L19_similarityWitnessP⁻¹) *ᵥ ![1, 1]) = -3 / 2 := by
  rw [L19_similarityWitness_conj]
  simp [shear, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
  norm_num

/-- **`IsNumAbscissaBound` is not similarity-invariant.** The Rayleigh
quotient at the fixed probe vector `![1,1]` is strictly positive for
`shear 4` and strictly negative for the similar operator
`P * shear 4 * P⁻¹` (`P = diag(1/8,1)`, non-orthogonal): whether a given
vector is "reactive" is a chart-dependent fact, unlike membership in the
spectrum (see `L19_similarityWitness_alpha_unchanged` below). -/
theorem L19_witness_omega_not_similarity_invariant :
    0 < (![1, 1] : Fin 2 → ℝ) ⬝ᵥ (shear 4 *ᵥ ![1, 1]) ∧
    (![1, 1] : Fin 2 → ℝ) ⬝ᵥ
      ((L19_similarityWitnessP * shear 4 * L19_similarityWitnessP⁻¹) *ᵥ ![1, 1]) < 0 :=
  ⟨by rw [L19_similarityWitness_rayleigh_orig]; norm_num,
   by rw [L19_similarityWitness_rayleigh_conj]; norm_num⟩

/-- Meanwhile the eigenvalue set is exactly unchanged (`-1`, both directly
from L12c's `shear_all_eigenvalues_neg`, reused without modification): the
sign flip above is a numerical-abscissa/Rayleigh-quotient phenomenon, not a
spectral one, exactly as `alpha_similarity_invariant` predicts. -/
theorem L19_similarityWitness_alpha_unchanged :
    (∀ lam : ℝ, (∃ v : Fin 2 → ℝ, v ≠ 0 ∧ shear 4 *ᵥ v = lam • v) → lam = -1) ∧
    (∀ lam : ℝ, (∃ v : Fin 2 → ℝ, v ≠ 0 ∧
      (L19_similarityWitnessP * shear 4 * L19_similarityWitnessP⁻¹) *ᵥ v = lam • v) →
      lam = -1) := by
  refine ⟨shear_all_eigenvalues_neg 4, ?_⟩
  rw [L19_similarityWitness_conj]
  exact shear_all_eigenvalues_neg (1 / 2)

end

end NoeticDiffusion
