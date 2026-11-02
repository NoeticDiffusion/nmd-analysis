import Noetic.CovarianceEllipsoidPushForward

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

local instance scratchDecidableEq : DecidableEq n := Classical.decEq n

def centeredInverseEllipsoidOfPosDef
    (M : Matrix n n ℝ) (hM : M.PosDef) (c : n → ℝ) : Set (n → ℝ) :=
  {y | inverseQuadraticFormOfPosDef M hM (y - c) ≤ 1}

lemma pushForward_inv_identity
    (F M : Matrix n n ℝ) (hF : IsUnit F) (hM : M.PosDef) :
    F.transpose * (pushForwardCovariance F M)⁻¹ * F = M⁻¹ := by
  letI : Invertible F := hF.invertible
  letI : Invertible M := hM.isUnit.invertible
  have hQ : IsUnit (pushForwardCovariance F M) :=
    (pushForwardCovariance_posDef F M hF hM).isUnit
  rw [show (pushForwardCovariance F M)⁻¹ =
      (F.transpose)⁻¹ * M⁻¹ * F⁻¹ by
    simp [pushForwardCovariance, Matrix.mul_inv_rev, Matrix.transpose_nonsing_inv,
      Matrix.mul_assoc]]
  have hFt : IsUnit F.transpose := (Matrix.isUnit_transpose F).mpr hF
  calc
    F.transpose * ((F.transpose)⁻¹ * M⁻¹ * F⁻¹) * F =
        (F.transpose * (F.transpose)⁻¹) * M⁻¹ * (F⁻¹ * F) := by
          noncomm_ring
    _ = M⁻¹ := by
      rw [Matrix.mul_nonsing_inv F.transpose
        ((Matrix.isUnit_iff_isUnit_det F.transpose).mp hFt), one_mul,
        Matrix.nonsing_inv_mul F ((Matrix.isUnit_iff_isUnit_det F).mp hF)]
      simp

lemma pushForward_quadratic_identity
    (F M : Matrix n n ℝ) (hF : IsUnit F) (hM : M.PosDef)
    (v : n → ℝ) :
    inverseQuadraticFormOfPosDef (pushForwardCovariance F M)
      (pushForwardCovariance_posDef F M hF hM) (F *ᵥ v) =
      inverseQuadraticFormOfPosDef M hM v := by
  letI : Invertible F := hF.invertible
  letI : Invertible M := hM.isUnit.invertible
  dsimp [inverseQuadraticFormOfPosDef]
  have hmatrix := pushForward_inv_identity F M hF hM
  have hstar : star (F *ᵥ v) = star v ᵥ* F.transpose := by
    simpa [real_conjTranspose] using (Matrix.star_mulVec F v)
  rw [hstar]
  rw [Matrix.mulVec_mulVec]
  calc
    (star v ᵥ* F.transpose) ⬝ᵥ ((pushForwardCovariance F M)⁻¹ * F) *ᵥ v =
        star v ⬝ᵥ F.transpose *ᵥ (((pushForwardCovariance F M)⁻¹ * F) *ᵥ v) := by
          exact (Matrix.dotProduct_mulVec (star v) F.transpose
            (((pushForwardCovariance F M)⁻¹ * F) *ᵥ v)).symm
    _ = star v ⬝ᵥ (F.transpose * (pushForwardCovariance F M)⁻¹ * F) *ᵥ v := by
          simp [Matrix.mul_assoc]
    _ = star v ⬝ᵥ M⁻¹ *ᵥ v := by rw [hmatrix]

theorem affinePushForwardEllipsoid_mem_iff_centeredInverseEllipsoid
    {M : Matrix n n ℝ} (F : Matrix n n ℝ) (c : n → ℝ)
    (E : LicensedInverseEllipsoid M) (hF : IsUnit F) (y : n → ℝ) :
    y ∈ affinePushForwardEllipsoid F c E hF ↔
      y ∈ centeredInverseEllipsoidOfPosDef (pushForwardCovariance F M)
        (pushForwardCovariance_posDef F M hF E.posDef) c := by
  letI : Invertible F := hF.invertible
  constructor
  · rintro ⟨x, hx, rfl⟩
    change inverseQuadraticFormOfPosDef (pushForwardCovariance F M)
      (pushForwardCovariance_posDef F M hF E.posDef) ((F *ᵥ x + c) - c) ≤ 1
    rw [add_sub_cancel_right]
    rw [pushForward_quadratic_identity F M hF E.posDef x]
    simpa [LicensedInverseEllipsoid.carrier, inverseEllipsoidOfPosDef] using hx
  · intro hy
    change inverseQuadraticFormOfPosDef (pushForwardCovariance F M)
      (pushForwardCovariance_posDef F M hF E.posDef) (y - c) ≤ 1 at hy
    let x : n → ℝ := F⁻¹ *ᵥ (y - c)
    have hxmap : F *ᵥ x = y - c := by
      dsimp [x]
      rw [Matrix.mulVec_mulVec, Matrix.mul_inv_of_invertible, Matrix.one_mulVec]
    have hxq : inverseQuadraticFormOfPosDef M E.posDef x ≤ 1 := by
      rw [← pushForward_quadratic_identity F M hF E.posDef x]
      rw [hxmap]
      exact hy
    have hx : x ∈ E.carrier := by
      simpa [LicensedInverseEllipsoid.carrier, inverseEllipsoidOfPosDef] using hxq
    refine ⟨x, hx, ?_⟩
    change F *ᵥ x + c = y
    rw [hxmap]
    exact sub_add_cancel y c

theorem affinePushForwardEllipsoid_zero_mem_iff_inverseEllipsoid
    {M : Matrix n n ℝ} (F : Matrix n n ℝ)
    (E : LicensedInverseEllipsoid M) (hF : IsUnit F) (y : n → ℝ) :
    y ∈ affinePushForwardEllipsoid F 0 E hF ↔
      y ∈ inverseEllipsoidOfPosDef (pushForwardCovariance F M)
        (pushForwardCovariance_posDef F M hF E.posDef) := by
  simpa [centeredInverseEllipsoidOfPosDef] using
    (affinePushForwardEllipsoid_mem_iff_centeredInverseEllipsoid F 0 E hF y)

end

end NoeticDiffusion
