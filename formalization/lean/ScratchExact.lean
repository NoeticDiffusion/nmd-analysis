import Noetic.CovarianceEllipsoidPushForward
open scoped Matrix
open NoeticDiffusion

namespace NoeticDiffusion
noncomputable section
variable {n : Type*} [Fintype n]
local instance : DecidableEq n := Classical.decEq n

lemma pushForwardCovariance_inv_test (F M : Matrix n n ℝ) (hF : IsUnit F) (hM : M.PosDef) :
    (pushForwardCovariance F M)⁻¹ =
      (F.transpose)⁻¹ * M⁻¹ * F⁻¹ := by
  have hFdet : IsUnit F.det := (Matrix.isUnit_iff_isUnit_det F).mp hF
  have hMdet : IsUnit M.det := (Matrix.isUnit_iff_isUnit_det M).mp hM.isUnit
  have hFt : IsUnit F.transpose :=
    (Matrix.isUnit_transpose F).mpr hF
  have hFtDet : IsUnit F.transpose.det :=
    (Matrix.isUnit_iff_isUnit_det F.transpose).mp hFt
  have hFtInv : F.transpose * (F.transpose)⁻¹ = 1 :=
    Matrix.mul_nonsing_inv F.transpose hFtDet
  have hN : (pushForwardCovariance F M).PosDef :=
    pushForwardCovariance_posDef F M hF hM
  have hNdet : IsUnit (pushForwardCovariance F M).det :=
    (Matrix.isUnit_iff_isUnit_det _).mp hN.isUnit
  letI : Invertible (pushForwardCovariance F M) :=
    Classical.choice ((Matrix.isUnit_iff_isUnit_det _).mpr hNdet).nonempty_invertible
  have hprod :
      pushForwardCovariance F M *
          ((F.transpose)⁻¹ * M⁻¹ * F⁻¹) = 1 := by
    calc
      pushForwardCovariance F M * ((F.transpose)⁻¹ * M⁻¹ * F⁻¹) =
          F * M * (F.transpose * (F.transpose)⁻¹) * M⁻¹ * F⁻¹ := by
            simp only [pushForwardCovariance, Matrix.mul_assoc]
      _ = F * M * 1 * M⁻¹ * F⁻¹ := by rw [hFtInv]
      _ = F * (M * M⁻¹) * F⁻¹ := by simp [Matrix.mul_assoc]
      _ = F * 1 * F⁻¹ := by rw [Matrix.mul_nonsing_inv M hMdet]
      _ = 1 := by simp only [Matrix.mul_one, Matrix.mul_nonsing_inv F hFdet]
  have hNinv :
      pushForwardCovariance F M * (pushForwardCovariance F M)⁻¹ = 1 :=
    Matrix.mul_nonsing_inv _ hNdet
  exact (Matrix.mul_right_injective_of_invertible (pushForwardCovariance F M))
    (hNinv.trans hprod.symm)

example (F M : Matrix n n ℝ) (hF : IsUnit F) (hM : M.PosDef)
    (x : n → ℝ) :
    inverseQuadraticFormOfPosDef (pushForwardCovariance F M)
        (pushForwardCovariance_posDef F M hF hM) (F *ᵥ x) =
      inverseQuadraticFormOfPosDef M hM x := by
  dsimp [inverseQuadraticFormOfPosDef]
  rw [pushForwardCovariance_inv_test F M hF hM]
  rw [Matrix.mulVec_mulVec]
  have hFdet : IsUnit F.det := (Matrix.isUnit_iff_isUnit_det F).mp hF
  have hFt : IsUnit F.transpose := (Matrix.isUnit_transpose F).mpr hF
  have hFtDet : IsUnit F.transpose.det :=
    (Matrix.isUnit_iff_isUnit_det F.transpose).mp hFt
  have hFtInv : F.transpose * (F.transpose)⁻¹ = 1 :=
    Matrix.mul_nonsing_inv F.transpose hFtDet
  have hFleft : F⁻¹ * F = 1 := Matrix.nonsing_inv_mul F hFdet
  have hmat : (F.transpose)⁻¹ * M⁻¹ * F⁻¹ * F =
      (F.transpose)⁻¹ * M⁻¹ := by
    calc
      (F.transpose)⁻¹ * M⁻¹ * F⁻¹ * F =
          (F.transpose)⁻¹ * M⁻¹ * (F⁻¹ * F) := by
            simp [Matrix.mul_assoc]
      _ = (F.transpose)⁻¹ * M⁻¹ := by rw [hFleft, Matrix.mul_one]
  rw [hmat]
  rw [Matrix.dotProduct_mulVec]
  rw [Matrix.star_mulVec]
  rw [real_conjTranspose]
  rw [Matrix.vecMul_vecMul]
  rw [hFtInv]
  simp

end
end NoeticDiffusion
