import Noetic.CovarianceEllipsoid

/-!
# L10B: affine push-forwards of licensed covariance ellipsoids

An explicit invertible linear map transports a positive-definite covariance by
`F * M * Fᵀ`.  This module records that algebraic push-forward, the affine
image of a licensed inverse ellipsoid, and the exact membership equivalence
with the corresponding inverse ellipsoid translated to the affine center. The
map's invertibility is represented by an explicit `IsUnit F` witness; no
inverse-based object is constructed when that witness is absent.

These are finite real linear-algebra statements. They do not identify the
ellipsoid with a probability support, a control-reachable set, or an empirical
confidence region.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

local instance covarianceEllipsoidPushForwardDecidableEq : DecidableEq n :=
  Classical.decEq n

/-! ## Explicit affine push-forward -/

/-- Covariance transported by a linear map `F`. -/
def pushForwardCovariance
    (F M : Matrix n n ℝ) : Matrix n n ℝ :=
  F * M * F.transpose

/-- Affine image of a set of state vectors under `x ↦ F x + c`. -/
def affinePushForward
    (F : Matrix n n ℝ) (c : n → ℝ) (S : Set (n → ℝ)) : Set (n → ℝ) :=
  (fun x => F *ᵥ x + c) '' S

/-- Affine image of the carrier of a licensed inverse ellipsoid. -/
def affinePushForwardEllipsoid
    {M : Matrix n n ℝ} (F : Matrix n n ℝ) (c : n → ℝ)
    (E : LicensedInverseEllipsoid M) (hF : IsUnit F) : Set (n → ℝ) :=
  let _ := hF
  affinePushForward F c E.carrier

/-- The inverse ellipsoid for a covariance, translated to an explicit center. -/
def centeredInverseEllipsoidOfPosDef
    (M : Matrix n n ℝ) (hM : M.PosDef) (c : n → ℝ) : Set (n → ℝ) :=
  {y | inverseQuadraticFormOfPosDef M hM (y - c) ≤ 1}

/-! ## Positivity and proof-carrying transformed objects -/

/-- An explicit invertible linear map preserves positive definiteness under
the covariance push-forward `F * M * Fᵀ`. -/
theorem pushForwardCovariance_posDef
    (F M : Matrix n n ℝ) (hF : IsUnit F) (hM : M.PosDef) :
    (pushForwardCovariance F M).PosDef := by
  have hInjective : Function.Injective F.vecMul :=
    (Matrix.vecMul_injective_iff_isUnit).mpr hF
  simpa [pushForwardCovariance, real_conjTranspose] using
    hM.mul_mul_conjTranspose_same hInjective

/-- The transformed covariance receives a `PosDef` license explicitly, so its
inverse ellipsoid remains proof-carrying after push-forward. -/
def pushForwardLicensedEllipsoid
    (F M : Matrix n n ℝ) (hF : IsUnit F) (hM : M.PosDef) :
  LicensedInverseEllipsoid (pushForwardCovariance F M) :=
  ⟨pushForwardCovariance_posDef F M hF hM⟩

/-! ## Exact inverse and quadratic-form transport -/

/-- The inverse of a pushed-forward covariance satisfies the expected
congruence identity. -/
private lemma pushForward_inv_identity
    (F M : Matrix n n ℝ) (hF : IsUnit F) :
    F.transpose * (pushForwardCovariance F M)⁻¹ * F = M⁻¹ := by
  letI : Invertible F := hF.invertible
  rw [show (pushForwardCovariance F M)⁻¹ =
      (F.transpose)⁻¹ * M⁻¹ * F⁻¹ by
    simp [pushForwardCovariance, Matrix.mul_inv_rev, Matrix.mul_assoc]]
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

/- The inverse quadratic form is invariant under the linear push-forward. -/
private lemma pushForward_quadratic_identity
    (F M : Matrix n n ℝ) (hF : IsUnit F) (hM : M.PosDef)
    (v : n → ℝ) :
    inverseQuadraticFormOfPosDef (pushForwardCovariance F M)
      (pushForwardCovariance_posDef F M hF hM) (F *ᵥ v) =
      inverseQuadraticFormOfPosDef M hM v := by
  letI : Invertible F := hF.invertible
  letI : Invertible M := hM.isUnit.invertible
  dsimp [inverseQuadraticFormOfPosDef]
  have hmatrix := pushForward_inv_identity F M hF
  have hstar : star (F *ᵥ v) = star v ᵥ* F.transpose := by
    simpa [real_conjTranspose] using (Matrix.star_mulVec F v)
  rw [hstar]
  rw [Matrix.mulVec_mulVec]
  calc
    (star v ᵥ* F.transpose) ⬝ᵥ
        ((pushForwardCovariance F M)⁻¹ * F) *ᵥ v =
        star v ⬝ᵥ F.transpose *ᵥ
          (((pushForwardCovariance F M)⁻¹ * F) *ᵥ v) := by
      exact (Matrix.dotProduct_mulVec (star v) F.transpose
        (((pushForwardCovariance F M)⁻¹ * F) *ᵥ v)).symm
    _ = star v ⬝ᵥ
        (F.transpose * (pushForwardCovariance F M)⁻¹ * F) *ᵥ v := by
      simp [Matrix.mul_assoc]
    _ = star v ⬝ᵥ M⁻¹ *ᵥ v := by rw [hmatrix]

/-! ## Basic affine-image membership -/

/-- The affine center is in the affine image of every licensed ellipsoid. -/
theorem center_mem_affinePushForwardEllipsoid
    {M : Matrix n n ℝ} (F : Matrix n n ℝ) (c : n → ℝ)
    (E : LicensedInverseEllipsoid M) (hF : IsUnit F) :
    c ∈ affinePushForwardEllipsoid F c E hF := by
  have hzero : (0 : n → ℝ) ∈ E.carrier := by
    exact zero_mem_inverseEllipsoidOfPosDef M E.posDef
  refine ⟨0, hzero, ?_⟩
  simp

/-- Membership in an affine image is equivalent to membership in the centered
inverse ellipsoid of the transported covariance. -/
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
      (pushForwardCovariance_posDef F M hF E.posDef)
      ((F *ᵥ x + c) - c) ≤ 1
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

end

end NoeticDiffusion
