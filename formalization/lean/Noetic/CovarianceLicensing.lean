import Mathlib.Analysis.Matrix.Order
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
import Noetic.CovarianceFixedTransitionChain

/-!
# L8: licensing inverse and determinant objects

This module records the algebraic boundary for inverse-based covariance
objects.  Positive definiteness licenses matrix invertibility and a positive
determinant, hence the ordinary real log-determinant law.  At the degenerate
boundary, positive semidefiniteness together with failure of positive
definiteness forces a zero determinant.  No numerical regularization,
empirical reachability, or biological interpretation is introduced here.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

local instance covarianceLicensingDecidableEq : DecidableEq n :=
  Classical.decEq n

/-! ## Positive-definite licensing -/

/-- A real positive-definite square matrix is a unit in the matrix ring. -/
theorem posDef_isUnit_licence
    (M : Matrix n n ℝ) (hM : M.PosDef) : IsUnit M := by
  exact hM.isUnit

/-- A real positive-definite square matrix has positive determinant. -/
theorem posDef_det_pos_licence
    (M : Matrix n n ℝ) (hM : M.PosDef) : 0 < Matrix.det M := by
  exact hM.det_pos

/-- The ordinary real log-determinant is proof-carrying: constructing the
object requires a positive-definiteness witness. -/
def logDetOfPosDef (M : Matrix n n ℝ) (hM : M.PosDef) : ℝ :=
  let _ := hM
  Real.log (Matrix.det M)

/-- For a positive-definite matrix, exponentiating `logDetOfPosDef` recovers the
determinant. -/
theorem exp_logDetOfPosDef
    (M : Matrix n n ℝ) (hM : M.PosDef) :
    Real.exp (logDetOfPosDef M hM) = Matrix.det M := by
  unfold logDetOfPosDef
  exact Real.exp_log (posDef_det_pos_licence M hM)

/-! ## Singular PSD boundary -/

/-- A positive-semidefinite matrix which is not positive definite is
singular.  The PSD hypothesis is essential: failure of positive
definiteness alone does not imply a zero determinant. -/
theorem posSemidef_det_eq_zero_of_not_posDef
    (M : Matrix n n ℝ) (hPSD : M.PosSemidef) (hnotPD : ¬ M.PosDef) :
    Matrix.det M = 0 := by
  have hnotUnit : ¬ IsUnit M := by
    intro hunit
    exact hnotPD (hPSD.posDef_iff_isUnit.mpr hunit)
  have hnotUnitDet : ¬ IsUnit (Matrix.det M) := by
    intro hdet
    apply hnotUnit
    exact (Matrix.isUnit_iff_isUnit_det M).mpr hdet
  have hnotNe : ¬ Matrix.det M ≠ 0 := by
    intro hne
    exact hnotUnitDet (isUnit_iff_ne_zero.mpr hne)
  exact Classical.not_not.mp hnotNe

/-- If the fixed-transition block-span gate fails, a PSD covariance is
singular and its determinant is zero. -/
theorem covariance_det_eq_zero_of_fixedTransition_blockSpan_ne_top
    (A B : Matrix n n ℝ) (h : ℕ)
    (hPSD : (covariance A (B * B.transpose) h).PosSemidef)
    (hspan :
      blockColumnSpan
          (fun k : Fin h => fixedTransitionFactors A B k) ≠ ⊤) :
    Matrix.det (covariance A (B * B.transpose) h) = 0 := by
  apply posSemidef_det_eq_zero_of_not_posDef _ hPSD
  intro hPD
  exact hspan ((covariance_posDef_iff_fixedTransition_blockSpan A B h).mp hPD)

/-- If the fixed-transition block matrix fails the full-row-rank gate, a PSD
covariance is singular and its determinant is zero. -/
theorem covariance_det_eq_zero_of_fixedTransition_blockRank_ne_card
    (A B : Matrix n n ℝ) (h : ℕ)
    (hPSD : (covariance A (B * B.transpose) h).PosSemidef)
    (hrank :
      (blockFactorMatrix
          (fun k : Fin h => fixedTransitionFactors A B k)).rank ≠
        Fintype.card n) :
    Matrix.det (covariance A (B * B.transpose) h) = 0 := by
  apply posSemidef_det_eq_zero_of_not_posDef _ hPSD
  intro hPD
  exact hrank ((covariance_posDef_iff_fixedTransition_blockRank A B h).mp hPD)

/-! ## Fully composed fixed-transition gates -/

private lemma covariance_factor_posSemidef
    (A B : Matrix n n ℝ) (h : ℕ) :
    (covariance A (B * B.transpose) h).PosSemidef := by
  apply covariance_posSemidef A (B * B.transpose) ?_ h
  simpa [real_conjTranspose] using
    (Matrix.PosSemidef.mul_mul_conjTranspose_same
      (A := (1 : Matrix n n ℝ)) Matrix.PosSemidef.one B)

/-- The fixed-transition span failure gate discharges covariance PSD
internally for a factorized innovation covariance. -/
theorem covariance_det_eq_zero_of_fixedTransition_blockSpan_ne_top_derived
    (A B : Matrix n n ℝ) (h : ℕ)
    (hspan :
      blockColumnSpan
          (fun k : Fin h => fixedTransitionFactors A B k) ≠ ⊤) :
    Matrix.det (covariance A (B * B.transpose) h) = 0 := by
  exact covariance_det_eq_zero_of_fixedTransition_blockSpan_ne_top A B h
    (covariance_factor_posSemidef A B h) hspan

/-- The fixed-transition rank failure gate discharges covariance PSD internally
for a factorized innovation covariance. -/
theorem covariance_det_eq_zero_of_fixedTransition_blockRank_ne_card_derived
    (A B : Matrix n n ℝ) (h : ℕ)
    (hrank :
      (blockFactorMatrix
          (fun k : Fin h => fixedTransitionFactors A B k)).rank ≠
        Fintype.card n) :
    Matrix.det (covariance A (B * B.transpose) h) = 0 := by
  exact covariance_det_eq_zero_of_fixedTransition_blockRank_ne_card A B h
    (covariance_factor_posSemidef A B h) hrank

end

end NoeticDiffusion
