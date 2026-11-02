import Noetic.CovarianceLicensing

/-!
# L9: inverse quadratic forms and licensed covariance ellipsoids

This module makes the inverse-based reachability surface proof-carrying.  A
positive-definite covariance supplies a positive inverse quadratic form and a
set-valued ellipsoid.  The ellipsoid license carries the `PosDef` witness, so
the degenerate PSD boundary has no ordinary inverse-ellipsoid object.  The
statements are finite real linear algebra only; they add no probability
coverage, empirical reachability, numerical regularization, or biological
interpretation.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

local instance covarianceEllipsoidDecidableEq : DecidableEq n :=
  Classical.decEq n

/-! ## L9A: positive inverse quadratic form -/

/-- The inverse quadratic form associated with a positive-definite matrix. -/
def inverseQuadraticFormOfPosDef
    (M : Matrix n n ℝ) (hM : M.PosDef) (v : n → ℝ) : ℝ :=
  let _ := hM
  star v ⬝ᵥ (M⁻¹ *ᵥ v)

/-- Every nonzero direction has strictly positive inverse quadratic form under
an explicit positive-definiteness witness. -/
theorem inverseQuadraticFormOfPosDef_pos
    (M : Matrix n n ℝ) (hM : M.PosDef) {v : n → ℝ} (hv : v ≠ 0) :
    0 < inverseQuadraticFormOfPosDef M hM v := by
  exact hM.inv.2 v hv

/-! ## L9B: proof-carrying ellipsoids -/

/-- The closed inverse ellipsoid for a positive-definite matrix. -/
def inverseEllipsoidOfPosDef
    (M : Matrix n n ℝ) (hM : M.PosDef) : Set (n → ℝ) :=
  {v | inverseQuadraticFormOfPosDef M hM v ≤ 1}

/-- A licensed inverse ellipsoid stores the positive-definiteness proof that
permits its inverse-based carrier. -/
structure LicensedInverseEllipsoid (M : Matrix n n ℝ) where
  posDef : M.PosDef

/-- The carrier of a licensed inverse ellipsoid. -/
def LicensedInverseEllipsoid.carrier
    {M : Matrix n n ℝ} (E : LicensedInverseEllipsoid M) : Set (n → ℝ) :=
  inverseEllipsoidOfPosDef M E.posDef

/-- Zero belongs to every positive-definite inverse ellipsoid. -/
theorem zero_mem_inverseEllipsoidOfPosDef
    (M : Matrix n n ℝ) (hM : M.PosDef) :
    (0 : n → ℝ) ∈ inverseEllipsoidOfPosDef M hM := by
  simp [inverseEllipsoidOfPosDef, inverseQuadraticFormOfPosDef]

/-- The fixed-transition reachability ellipsoid, available only with an
explicit positive-definiteness proof for the finite-horizon covariance. -/
def reachabilityEllipsoidOfPosDef
    (A B : Matrix n n ℝ) (h : ℕ)
    (hPos : (covariance A (B * B.transpose) h).PosDef) : Set (n → ℝ) :=
  inverseEllipsoidOfPosDef (covariance A (B * B.transpose) h) hPos

/-- The origin is contained in every licensed fixed-transition reachability
ellipsoid. -/
theorem zero_mem_reachabilityEllipsoidOfPosDef
    (A B : Matrix n n ℝ) (h : ℕ)
    (hPos : (covariance A (B * B.transpose) h).PosDef) :
    (0 : n → ℝ) ∈ reachabilityEllipsoidOfPosDef A B h hPos := by
  exact zero_mem_inverseEllipsoidOfPosDef
    (covariance A (B * B.transpose) h) hPos

/-- Full block-column span supplies the `PosDef` witness needed to construct a
fixed-transition reachability ellipsoid. -/
def reachabilityEllipsoidOfFixedTransition_blockSpan
    (A B : Matrix n n ℝ) (h : ℕ)
    (hspan :
      blockColumnSpan
          (fun k : Fin h => fixedTransitionFactors A B k) = ⊤) :
    Set (n → ℝ) :=
  reachabilityEllipsoidOfPosDef A B h
    ((covariance_posDef_iff_fixedTransition_blockSpan A B h).mpr hspan)

/-- Full block rank supplies the `PosDef` witness needed to construct a
fixed-transition reachability ellipsoid. -/
def reachabilityEllipsoidOfFixedTransition_blockRank
    (A B : Matrix n n ℝ) (h : ℕ)
    (hrank :
      (blockFactorMatrix
          (fun k : Fin h => fixedTransitionFactors A B k)).rank =
        Fintype.card n) :
    Set (n → ℝ) :=
  reachabilityEllipsoidOfPosDef A B h
    ((covariance_posDef_iff_fixedTransition_blockRank A B h).mpr hrank)

/-! ## L9C: degenerate boundary -/

/-- A covariance without positive definiteness has no licensed ordinary
inverse-ellipsoid object. -/
theorem no_licensedInverseEllipsoid_of_not_posDef
    (M : Matrix n n ℝ) (hnotPD : ¬ M.PosDef) :
    IsEmpty (LicensedInverseEllipsoid M) := by
  constructor
  intro E
  exact hnotPD E.posDef

/-- Failure of the fixed-transition block-span gate means that no ordinary
inverse-ellipsoid license exists for the corresponding covariance. -/
theorem no_reachabilityEllipsoid_of_fixedTransition_blockSpan_ne_top
    (A B : Matrix n n ℝ) (h : ℕ)
    (hspan :
      blockColumnSpan
          (fun k : Fin h => fixedTransitionFactors A B k) ≠ ⊤) :
    IsEmpty (LicensedInverseEllipsoid
      (covariance A (B * B.transpose) h)) := by
  apply no_licensedInverseEllipsoid_of_not_posDef
  intro hPos
  exact hspan ((covariance_posDef_iff_fixedTransition_blockSpan A B h).mp hPos)

/-- Failure of the fixed-transition full-rank gate means that no ordinary
inverse-ellipsoid license exists for the corresponding covariance. -/
theorem no_reachabilityEllipsoid_of_fixedTransition_blockRank_ne_card
    (A B : Matrix n n ℝ) (h : ℕ)
    (hrank :
      (blockFactorMatrix
          (fun k : Fin h => fixedTransitionFactors A B k)).rank ≠
        Fintype.card n) :
    IsEmpty (LicensedInverseEllipsoid
      (covariance A (B * B.transpose) h)) := by
  apply no_licensedInverseEllipsoid_of_not_posDef
  intro hPos
  exact hrank ((covariance_posDef_iff_fixedTransition_blockRank A B h).mp hPos)

end

end NoeticDiffusion
