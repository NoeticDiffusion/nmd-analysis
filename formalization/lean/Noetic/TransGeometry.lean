import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.Data.Real.Sqrt
import Mathlib.Algebra.Group.Pi.Units
import Noetic.Covariance
import Noetic.CovarianceSummaries
import Noetic.CovarianceEllipsoid

/-!
# TRANS P0 geometry: same drift, different diffusion; Loewner gates

This module is the linear-algebra half of the NDT-TRANS Lean P0 set in
`formalization/science_lead/sl_lean_001.md`. It uses the existing
fixed-transition covariance `covariance A Q h` from `Noetic.Covariance`
and the licensed inverse ellipsoid from `Noetic.CovarianceEllipsoid`.

* **T1.** Holding the local transition `A` fixed, `Q₁ ≠ Q₂` already forces
  `covariance A Q₁ 1 ≠ covariance A Q₂ 1`, because the one-step covariance
  is exactly `Q`. Same deterministic local dynamics do not imply the same
  finite-horizon second-moment geometry.
* **T2.** Loewner order on the innovation covariance propagates to every
  horizon: `Q₁ ≼ Q₂` implies `Σ_h(A,Q₁) ≼ Σ_h(A,Q₂)`. Re-exported from
  `covariance_mono_Q` under the TRANS name.
* **T3.** Inverse Loewner order: `0 ≺ Σ₁ ≼ Σ₂` implies `Σ₂⁻¹ ≼ Σ₁⁻¹`, and
  therefore the inverse ellipsoids nest, `E(Σ₁,c) ⊆ E(Σ₂,c)`. A swapped
  diagonal pair `diag(2,1)` vs `diag(1,2)` has equal trace, determinant and
  characteristic polynomial, yet a named direction lies in one unit gate and
  not the other. Equal scalar summaries do not identify directional
  accessibility.

Computational background (not a hypothesis of any theorem here): Astra
TRANS treats finite-horizon predictive geometry as distinct from the local
generator, and refuses to collapse cones to volume or effective dimension.
See `H:\SourceRepo2\NeuralManifoldDynamics\project\astra` TRANS pilots.

## Claim boundary

Finite real matrix algebra on `covariance` and licensed inverse ellipsoids.
No Gaussian kernel object is introduced: T1 is a theorem about the
second-moment geometry of `K_h`, not a theorem in `ProbabilityTheory.Kernel`.
No estimator, no `ε`-regularization, no probability coverage, and no
empirical MNPS claim. The swapped-diagonal witness is a `Fin 2` toy pair;
it does not say which laboratory chart is “right”.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix BigOperators

section GeneralN

variable {n : Type*} [Fintype n]

noncomputable local instance transGeometryDecidableEq : DecidableEq n :=
  Classical.decEq n

/-! ## T1: same transition, different innovation ⇒ different horizon-one geometry -/

/-- Affine mean of `X_{k+1} = A X_k + b`. The recursion does not mention the
innovation covariance: the deterministic skeleton can be held fixed while
`Q` varies. -/
def affineMean (A : Matrix n n ℝ) (b : n → ℝ) (x : n → ℝ) : ℕ → n → ℝ
  | 0 => x
  | h + 1 => A *ᵥ affineMean A b x h + b

@[simp] theorem affineMean_zero (A : Matrix n n ℝ) (b x : n → ℝ) :
    affineMean A b x 0 = x := rfl

@[simp] theorem affineMean_succ (A : Matrix n n ℝ) (b x : n → ℝ) (h : ℕ) :
    affineMean A b x (h + 1) = A *ᵥ affineMean A b x h + b := rfl

/-- One-step predictive covariance equals the innovation, independently of
`A`. Restates `L14_covariance_horizon_one` from the covariance recursion
without importing the L14 module. -/
theorem TransT1_covariance_horizon_one (A Q : Matrix n n ℝ) :
    covariance A Q 1 = Q := by
  simp [covariance_succ, covariance_zero, covStep]

/-- **T1.** A shared transition matrix `A` does not force shared horizon-one
covariance: `Q₁ ≠ Q₂` implies `Σ₁(A,Q₁) ≠ Σ₁(A,Q₂)`. Combined with
`affineMean`, the deterministic operator (and offset `b`) can be identical
while the stochastic future geometry differs. -/
theorem TransT1_same_A_diff_Q_diff_covariance
    (A Q1 Q2 : Matrix n n ℝ) (hQ : Q1 ≠ Q2) :
    covariance A Q1 1 ≠ covariance A Q2 1 := by
  rw [TransT1_covariance_horizon_one, TransT1_covariance_horizon_one]
  exact hQ

/-! ## T2: Loewner order on `Q` propagates through time -/

/-- **T2.** If `Q₂ - Q₁` is positive semidefinite, the finite-horizon
covariance inherits the same Loewner order at every `h`. Named TRANS
re-export of `covariance_mono_Q`. -/
theorem TransT2_covariance_mono_Q (A Q1 Q2 : Matrix n n ℝ)
    (hQ : (Q2 - Q1).PosSemidef) (h : ℕ) :
    (covariance A Q2 h - covariance A Q1 h).PosSemidef :=
  covariance_mono_Q A Q1 Q2 hQ h

/-! ## T3: inverse Loewner order and gate inclusion -/

/-- Inverse ellipsoid at an arbitrary threshold `c`, matching the science-lead
set `E(Σ,c) = {z | zᵀ Σ⁻¹ z ≤ c}`. The licensed unit ellipsoid of L9 is the
special case `c = 1`. -/
def inverseEllipsoidAt (M : Matrix n n ℝ) (hM : M.PosDef) (c : ℝ) :
    Set (n → ℝ) :=
  {v | inverseQuadraticFormOfPosDef M hM v ≤ c}

theorem inverseEllipsoidAt_one (M : Matrix n n ℝ) (hM : M.PosDef) :
    inverseEllipsoidAt M hM 1 = inverseEllipsoidOfPosDef M hM :=
  rfl

omit [Fintype n] in
private lemma star_real_vec (v : n → ℝ) : star v = v := by
  funext i
  simp

private lemma herm_dotProduct_mulVec {A : Matrix n n ℝ}
    (hA : A.IsHermitian) (x y : n → ℝ) :
    x ⬝ᵥ (A *ᵥ y) = (A *ᵥ x) ⬝ᵥ y := by
  have hAT : A.transpose = A := by
    simpa [real_conjTranspose] using hA.eq
  rw [Matrix.dotProduct_mulVec, ← Matrix.mulVec_transpose, hAT]

private lemma posDef_mul_inv (A : Matrix n n ℝ) (hA : A.PosDef) :
    A * A⁻¹ = 1 :=
  Matrix.mul_nonsing_inv A ((Matrix.isUnit_iff_isUnit_det A).mp hA.isUnit)

/-- Unfold the licensed inverse quadratic form against the section inverse.
Both sides use `Classical.decEq`, so this rewrite stays valid when later
specialized to `Fin 2`. -/
lemma invQuad_eq_star_dot (A : Matrix n n ℝ) (hA : A.PosDef) (v : n → ℝ) :
    inverseQuadraticFormOfPosDef A hA v = v ⬝ᵥ (A⁻¹ *ᵥ v) := by
  simp [inverseQuadraticFormOfPosDef]

lemma inv_diagonal_eq (d : n → ℝ) :
    (Matrix.diagonal d)⁻¹ = Matrix.diagonal (Ring.inverse d) :=
  Matrix.inv_diagonal d

lemma invQuad_diagonal (d : n → ℝ) (hA : (Matrix.diagonal d).PosDef)
    (v : n → ℝ) :
    inverseQuadraticFormOfPosDef (Matrix.diagonal d) hA v
      = ∑ i, v i * ((d i)⁻¹ * v i) := by
  have hpos : ∀ i, 0 < d i := Matrix.posDef_diagonal_iff.mp hA
  have hU : IsUnit d :=
    Pi.isUnit_iff.mpr fun i => isUnit_iff_ne_zero.mpr (ne_of_gt (hpos i))
  rw [invQuad_eq_star_dot, inv_diagonal_eq]
  simp only [Matrix.mulVec_diagonal, dotProduct]
  refine Finset.sum_congr rfl fun i _ => ?_
  rw [Ring.inverse_of_isUnit hU, IsUnit.val_inv_apply hU i]
  simp [Units.val_inv_eq_inv_val]

/-- Completing-the-square bound: `2 yᵀ v − yᵀ A y ≤ vᵀ A⁻¹ v` for positive
definite `A`. Equality holds at `y = A⁻¹ v`. -/
private lemma invQuad_complete_sq (A : Matrix n n ℝ) (hA : A.PosDef)
    (v y : n → ℝ) :
    2 * (y ⬝ᵥ v) - y ⬝ᵥ (A *ᵥ y) ≤ inverseQuadraticFormOfPosDef A hA v := by
  have hAinv : A * A⁻¹ = 1 := posDef_mul_inv A hA
  set w : n → ℝ := A⁻¹ *ᵥ v - y
  have hpos : 0 ≤ star w ⬝ᵥ (A *ᵥ w) := hA.posSemidef.2 w
  have hAw : A *ᵥ w = v - A *ᵥ y := by
    dsimp [w]
    rw [Matrix.mulVec_sub, Matrix.mulVec_mulVec, hAinv, Matrix.one_mulVec]
  have hstarw : star w = A⁻¹ *ᵥ v - y := by
    dsimp [w]
    rw [star_sub, star_real_vec, star_real_vec]
  have hexpand : star w ⬝ᵥ (A *ᵥ w)
      = inverseQuadraticFormOfPosDef A hA v - (2 * (y ⬝ᵥ v) - y ⬝ᵥ (A *ᵥ y)) := by
    rw [hAw, hstarw]
    have hcross : (A⁻¹ *ᵥ v) ⬝ᵥ (A *ᵥ y) = v ⬝ᵥ y := by
      rw [herm_dotProduct_mulVec hA.isHermitian, Matrix.mulVec_mulVec, hAinv,
        Matrix.one_mulVec]
    have hstarv : star v = v := star_real_vec v
    have h1 :
        ((A⁻¹ *ᵥ v) - y) ⬝ᵥ (v - A *ᵥ y)
          = (A⁻¹ *ᵥ v) ⬝ᵥ v - (A⁻¹ *ᵥ v) ⬝ᵥ (A *ᵥ y)
              - y ⬝ᵥ v + y ⬝ᵥ (A *ᵥ y) := by
      rw [sub_dotProduct, dotProduct_sub, dotProduct_sub]
      ring
    rw [h1, hcross, dotProduct_comm (A⁻¹ *ᵥ v) v, dotProduct_comm y v]
    simp only [inverseQuadraticFormOfPosDef, hstarv, two_mul]
    ring
  have hgoal :
      inverseQuadraticFormOfPosDef A hA v - (2 * (y ⬝ᵥ v) - y ⬝ᵥ (A *ᵥ y)) ≥ 0 := by
    rwa [← hexpand]
  linarith

private lemma invQuad_eq_of_invVec (A : Matrix n n ℝ) (hA : A.PosDef)
    (v : n → ℝ) :
    2 * ((A⁻¹ *ᵥ v) ⬝ᵥ v) - (A⁻¹ *ᵥ v) ⬝ᵥ (A *ᵥ (A⁻¹ *ᵥ v)) =
      inverseQuadraticFormOfPosDef A hA v := by
  have hAinv : A * A⁻¹ = 1 := posDef_mul_inv A hA
  rw [Matrix.mulVec_mulVec, hAinv, Matrix.one_mulVec]
  have hstarv : star v = v := star_real_vec v
  simp only [inverseQuadraticFormOfPosDef, hstarv]
  have hcomm : (A⁻¹ *ᵥ v) ⬝ᵥ v = v ⬝ᵥ (A⁻¹ *ᵥ v) := dotProduct_comm _ _
  rw [hcomm]
  ring

/-- Inverse quadratic forms reverse the Loewner order of positive-definite
matrices: `0 ≺ A ≼ B` implies `vᵀ B⁻¹ v ≤ vᵀ A⁻¹ v` for every `v`. -/
theorem TransT3_invQuad_loewner {A B : Matrix n n ℝ}
    (hA : A.PosDef) (hB : B.PosDef) (hAB : (B - A).PosSemidef) (v : n → ℝ) :
    inverseQuadraticFormOfPosDef B hB v ≤
      inverseQuadraticFormOfPosDef A hA v := by
  set y : n → ℝ := B⁻¹ *ᵥ v
  have heqB := invQuad_eq_of_invVec B hB v
  have hAquad := invQuad_complete_sq A hA v y
  have hLoew : y ⬝ᵥ (A *ᵥ y) ≤ y ⬝ᵥ (B *ᵥ y) := by
    have hdiff : 0 ≤ star y ⬝ᵥ ((B - A) *ᵥ y) := hAB.2 y
    have hlin : (B - A) *ᵥ y = B *ᵥ y - A *ᵥ y := Matrix.sub_mulVec _ _ _
    have hstar : star y = y := star_real_vec y
    rw [hlin, hstar, dotProduct_sub] at hdiff
    linarith
  have hge : 2 * (y ⬝ᵥ v) - y ⬝ᵥ (A *ᵥ y)
      ≥ inverseQuadraticFormOfPosDef B hB v := by
    have : 2 * (y ⬝ᵥ v) - y ⬝ᵥ (B *ᵥ y)
        = inverseQuadraticFormOfPosDef B hB v := heqB
    linarith
  linarith

/-- **T3a.** Inverse Loewner order: `0 ≺ A ≼ B` implies `B⁻¹ ≼ A⁻¹`. -/
theorem TransT3_inv_loewner {A B : Matrix n n ℝ}
    (hA : A.PosDef) (hB : B.PosDef) (hAB : (B - A).PosSemidef) :
    (A⁻¹ - B⁻¹).PosSemidef := by
  refine ⟨?_, ?_⟩
  · have hAinv : A⁻¹.IsHermitian := hA.inv.isHermitian
    have hBinv : B⁻¹.IsHermitian := hB.inv.isHermitian
    rw [Matrix.IsHermitian, Matrix.conjTranspose_sub, hAinv.eq, hBinv.eq]
  · intro v
    have hstar : star v = v := star_real_vec v
    have hlin : (A⁻¹ - B⁻¹) *ᵥ v = A⁻¹ *ᵥ v - B⁻¹ *ᵥ v :=
      Matrix.sub_mulVec _ _ _
    have hdiff :
        star v ⬝ᵥ ((A⁻¹ - B⁻¹) *ᵥ v)
          = inverseQuadraticFormOfPosDef A hA v
            - inverseQuadraticFormOfPosDef B hB v := by
      rw [hlin, hstar, dotProduct_sub]
      simp only [inverseQuadraticFormOfPosDef, hstar]
    rw [hdiff]
    linarith [TransT3_invQuad_loewner hA hB hAB v]

/-- **T3a-gate.** Loewner-larger positive-definite covariances have larger
inverse ellipsoids at every threshold `c`. -/
theorem TransT3_gate_subset {A B : Matrix n n ℝ}
    (hA : A.PosDef) (hB : B.PosDef) (hAB : (B - A).PosSemidef) (c : ℝ) :
    inverseEllipsoidAt A hA c ⊆ inverseEllipsoidAt B hB c := by
  intro v hv
  change inverseQuadraticFormOfPosDef B hB v ≤ c
  exact le_trans (TransT3_invQuad_loewner hA hB hAB v) hv

theorem TransT3_unit_gate_subset {A B : Matrix n n ℝ}
    (hA : A.PosDef) (hB : B.PosDef) (hAB : (B - A).PosSemidef) :
    inverseEllipsoidOfPosDef A hA ⊆ inverseEllipsoidOfPosDef B hB := by
  simpa [← inverseEllipsoidAt_one] using TransT3_gate_subset hA hB hAB 1

/-! ## T3b: equal scalar summaries, different directional gates -/

set_option linter.unusedSectionVars false

/-- Pin `Fin 2` to the same `Classical.decEq` used by the generic inverse
lemmas. Otherwise `instDecidableEqFin` wins and `Matrix.diagonal` (which
takes `DecidableEq` as a parameter) will not unify with `invQuad_diagonal`. -/
noncomputable local instance (priority := high) transGeometryFin2DecidableEq :
    DecidableEq (Fin 2) :=
  Classical.decEq (Fin 2)

/-- First swapped-diagonal covariance: `diag(2, 1)`. -/
abbrev Trans_Q1 : Matrix (Fin 2) (Fin 2) ℝ :=
  Matrix.diagonal (![2, 1] : Fin 2 → ℝ)

/-- Second swapped-diagonal covariance: `diag(1, 2)`, same spectrum as
`Trans_Q1`, opposite orientation. -/
abbrev Trans_Q2 : Matrix (Fin 2) (Fin 2) ℝ :=
  Matrix.diagonal (![1, 2] : Fin 2 → ℝ)

/-- Direction `z = (√2, 0)` used as the gate witness. -/
def Trans_z : Fin 2 → ℝ := ![Real.sqrt 2, 0]

/-- Orthogonal swap matrix conjugating `Trans_Q1` to `Trans_Q2`. -/
def Trans_swapU : Matrix (Fin 2) (Fin 2) ℝ :=
  Matrix.of ![![0, 1], ![1, 0]]

private lemma Trans_diag_posDef {a b : ℝ} (ha : 0 < a) (hb : 0 < b) :
    (Matrix.diagonal (![a, b] : Fin 2 → ℝ)).PosDef := by
  refine ⟨?_, ?_⟩
  · rw [Matrix.IsHermitian, real_conjTranspose, Matrix.diagonal_transpose]
  · intro v hv
    have hstar : star v = v := by
      funext i
      simp
    rw [hstar]
    have hdot :
        v ⬝ᵥ (Matrix.diagonal (![a, b] : Fin 2 → ℝ) *ᵥ v)
          = a * (v 0) ^ 2 + b * (v 1) ^ 2 := by
      simp [Matrix.mulVec_diagonal, dotProduct, Fin.sum_univ_two]
      ring
    rw [hdot]
    have hnz : v 0 ≠ 0 ∨ v 1 ≠ 0 := by
      by_contra h
      push_neg at h
      apply hv
      ext i
      fin_cases i <;> simp [h]
    rcases hnz with h0 | h1
    · have : 0 < a * (v 0) ^ 2 := mul_pos ha (sq_pos_of_ne_zero h0)
      nlinarith [mul_nonneg hb.le (sq_nonneg (v 1))]
    · have : 0 < b * (v 1) ^ 2 := mul_pos hb (sq_pos_of_ne_zero h1)
      nlinarith [mul_nonneg ha.le (sq_nonneg (v 0))]

theorem Trans_Q1_posDef : (Matrix.diagonal (![2, 1] : Fin 2 → ℝ)).PosDef :=
  Trans_diag_posDef (by norm_num : (0 : ℝ) < 2) (by norm_num : (0 : ℝ) < 1)

theorem Trans_Q2_posDef : (Matrix.diagonal (![1, 2] : Fin 2 → ℝ)).PosDef :=
  Trans_diag_posDef (by norm_num : (0 : ℝ) < 1) (by norm_num : (0 : ℝ) < 2)

private lemma Trans_invQuad_Q1 :
    inverseQuadraticFormOfPosDef Trans_Q1 Trans_Q1_posDef Trans_z = 1 := by
  have h := invQuad_diagonal (![2, 1] : Fin 2 → ℝ) Trans_Q1_posDef Trans_z
  rw [h]
  simp [Trans_z, Fin.sum_univ_two]
  field_simp
  exact Real.sq_sqrt (by norm_num : (0 : ℝ) ≤ 2)

private lemma Trans_invQuad_Q2 :
    inverseQuadraticFormOfPosDef Trans_Q2 Trans_Q2_posDef Trans_z = 2 := by
  have h := invQuad_diagonal (![1, 2] : Fin 2 → ℝ) Trans_Q2_posDef Trans_z
  rw [h]
  simp [Trans_z, Fin.sum_univ_two]

private lemma Trans_swapU_orthogonal : Trans_swapUᵀ * Trans_swapU = 1 := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Trans_swapU, Matrix.of_apply, Matrix.mul_apply, Fin.sum_univ_two,
      Matrix.transpose_apply]

private lemma Trans_swapU_conj : Trans_swapUᵀ * Trans_Q1 * Trans_swapU = Trans_Q2 := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Trans_swapU, Trans_Q1, Trans_Q2, Matrix.of_apply, Matrix.mul_apply,
      Fin.sum_univ_two, Matrix.transpose_apply, Matrix.diagonal]

/-- The swapped diagonals are orthogonally conjugate, so they share every
orthogonal-gauge summary even though their inverse ellipsoids differ. -/
theorem TransT3_orthogonally_conjugate :
    Trans_swapUᵀ * Trans_swapU = 1 ∧
    Trans_swapUᵀ * Trans_Q1 * Trans_swapU = Trans_Q2 :=
  ⟨Trans_swapU_orthogonal, Trans_swapU_conj⟩

/-- **T3b.** `diag(2,1)` and `diag(1,2)` share trace and determinant (hence
the same 2×2 characteristic polynomial), yet the named direction
`z = (√2, 0)` lies in the unit inverse ellipsoid of the first and not of
the second. Same volume and same spectrum do not imply the same directional
gate. -/
theorem TransT3_same_summaries_diff_gate :
    Matrix.trace Trans_Q1 = Matrix.trace Trans_Q2 ∧
    Matrix.det Trans_Q1 = Matrix.det Trans_Q2 ∧
    Trans_Q1 ≠ Trans_Q2 ∧
    Trans_z ∈ inverseEllipsoidOfPosDef Trans_Q1 Trans_Q1_posDef ∧
    Trans_z ∉ inverseEllipsoidOfPosDef Trans_Q2 Trans_Q2_posDef := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · simp [Trans_Q1, Trans_Q2, Matrix.trace_diagonal, Fin.sum_univ_two]; ring
  · simp [Trans_Q1, Trans_Q2, Matrix.det_diagonal, Fin.prod_univ_two]
  · intro h
    have hc : Trans_Q1 0 0 = Trans_Q2 0 0 := congrArg (fun M => M 0 0) h
    simp [Trans_Q1, Trans_Q2, Matrix.diagonal_apply_eq] at hc
  · change inverseQuadraticFormOfPosDef Trans_Q1 Trans_Q1_posDef Trans_z ≤ 1
    rw [Trans_invQuad_Q1]
  · change ¬ inverseQuadraticFormOfPosDef Trans_Q2 Trans_Q2_posDef Trans_z ≤ 1
    rw [Trans_invQuad_Q2]
    norm_num

end GeneralN

end

end NoeticDiffusion
