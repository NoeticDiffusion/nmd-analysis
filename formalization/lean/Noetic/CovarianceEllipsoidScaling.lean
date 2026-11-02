import Noetic.CovarianceEllipsoid

/-!
# L10: positive covariance scaling for licensed ellipsoids

Positive scalar scaling preserves positive definiteness and gives the expected
inverse-quadratic scaling law.  The construction remains proof-carrying: the
scaled matrix receives an explicit `PosDef` witness.  This is finite real
linear algebra only and does not add a probabilistic or empirical claim.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

local instance covarianceEllipsoidScalingDecidableEq : DecidableEq n :=
  Classical.decEq n

/-- Positive scaling of a positive-definite matrix remains positive definite. -/
def scaledPosDefWitness
    (a : ℝ) (ha : 0 < a) (M : Matrix n n ℝ) (hM : M.PosDef) :
    (a • M).PosDef :=
  hM.smul ha

/-- The inverse quadratic form scales by the reciprocal of a positive scalar. -/
theorem inverseQuadraticFormOfPosDef_smul
    (a : ℝ) (ha : 0 < a) (M : Matrix n n ℝ) (hM : M.PosDef)
    (v : n → ℝ) :
    inverseQuadraticFormOfPosDef (a • M) (scaledPosDefWitness a ha M hM) v =
      a⁻¹ * inverseQuadraticFormOfPosDef M hM v := by
  letI : Invertible a := invertibleOfNonzero ha.ne'
  dsimp [inverseQuadraticFormOfPosDef]
  rw [Matrix.inv_smul M a ((Matrix.isUnit_iff_isUnit_det M).mp hM.isUnit)]
  simp [Matrix.smul_mulVec, dotProduct_smul, invOf_eq_inv]

/-- Membership in the ellipsoid of a positively scaled covariance is
equivalent to the original inverse quadratic form having threshold `a`. -/
theorem mem_inverseEllipsoidOfPosDef_smul_iff
    (a : ℝ) (ha : 0 < a) (M : Matrix n n ℝ) (hM : M.PosDef)
    (v : n → ℝ) :
    v ∈ inverseEllipsoidOfPosDef
        (a • M) (scaledPosDefWitness a ha M hM) ↔
      inverseQuadraticFormOfPosDef M hM v ≤ a := by
  change inverseQuadraticFormOfPosDef
      (a • M) (scaledPosDefWitness a ha M hM) v ≤ 1 ↔ _
  rw [inverseQuadraticFormOfPosDef_smul a ha M hM v]
  have ha0 : a ≠ 0 := ne_of_gt ha
  constructor
  · intro h
    have h' : a⁻¹ * inverseQuadraticFormOfPosDef M hM v ≤ a⁻¹ * a := by
      simpa [inv_mul_cancel₀ ha0] using h
    exact (mul_le_mul_iff_right₀ (inv_pos.mpr ha)).mp h'
  · intro h
    have h' : a⁻¹ * inverseQuadraticFormOfPosDef M hM v ≤ a⁻¹ * a :=
      (mul_le_mul_iff_right₀ (inv_pos.mpr ha)).mpr h
    simpa [inv_mul_cancel₀ ha0] using h'

/-- Scaling the covariance by a positive scalar scales the licensed
fixed-transition ellipsoid through the same proof-carrying constructor. -/
def scaledReachabilityEllipsoid
    (a : ℝ) (ha : 0 < a) (A B : Matrix n n ℝ) (h : ℕ)
    (hPos : (covariance A (B * B.transpose) h).PosDef) : Set (n → ℝ) :=
  inverseEllipsoidOfPosDef
    (a • covariance A (B * B.transpose) h)
    (scaledPosDefWitness a ha _ hPos)

end

end NoeticDiffusion
