import Noetic.CovarianceEllipsoidFixedTransitionLicensing

/-!
# L10E: common licensing API for fixed-transition affine ellipsoids

The L10D span and rank constructors expose the same downstream affine
ellipsoid and membership theorem.  This module packages their shared
positive-definiteness witness in one validity-gate structure.  The gate can be
constructed from either the propagated-factor block-column span condition or
the equivalent full-row-rank condition, while the affine map remains guarded
by an explicit `IsUnit F` witness and the affine centre remains explicit.

These are finite real linear-algebra statements only.  The common gate does
not add a probability, occupancy, empirical, or biological interpretation to
the ellipsoid.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

local instance covarianceEllipsoidFixedTransitionCommonDecidableEq :
    DecidableEq n :=
  Classical.decEq n

/-- The common positive-definiteness gate for a fixed-transition covariance.

The field stores exactly the witness needed by the L10C affine ellipsoid
constructor.  The span and rank constructors below provide the two L10D
scientific gate interfaces without duplicating the downstream affine API.
-/
structure FixedTransitionCovarianceGate
    (A B : Matrix n n ℝ) (h : ℕ) where
  posDef : (covariance A (B * B.transpose) h).PosDef

/-- Build the common fixed-transition gate from full propagated-factor span. -/
def FixedTransitionCovarianceGate.of_blockSpan
    (A B : Matrix n n ℝ) (h : ℕ)
    (hspan :
      blockColumnSpan
          (fun k : Fin h => fixedTransitionFactors A B k) = ⊤) :
    FixedTransitionCovarianceGate A B h :=
  ⟨(covariance_posDef_iff_fixedTransition_blockSpan A B h).mpr hspan⟩

/-- Build the common fixed-transition gate from full propagated-factor rank. -/
def FixedTransitionCovarianceGate.of_blockRank
    (A B : Matrix n n ℝ) (h : ℕ)
    (hrank :
      (blockFactorMatrix
          (fun k : Fin h => fixedTransitionFactors A B k)).rank =
        Fintype.card n) :
    FixedTransitionCovarianceGate A B h :=
  ⟨(covariance_posDef_iff_fixedTransition_blockRank A B h).mpr hrank⟩

/-- The common affine fixed-transition inverse ellipsoid API.

`gate` supplies the covariance license; `hF` supplies the affine-map
invertibility license; and `c` is the explicit affine centre. -/
def affineFixedTransitionReachabilityEllipsoid_of_gate
    (F : Matrix n n ℝ) (c : n → ℝ)
    (A B : Matrix n n ℝ) (h : ℕ)
    (gate : FixedTransitionCovarianceGate A B h)
    (hF : IsUnit F) : Set (n → ℝ) :=
  affineFixedTransitionReachabilityEllipsoid F c A B h gate.posDef hF

/-- Membership in the common-gate affine ellipsoid is exactly membership in
the centred inverse ellipsoid of its pushed-forward covariance. -/
theorem affineFixedTransitionReachabilityEllipsoid_of_gate_mem_iff_centeredInverseEllipsoid
    (F : Matrix n n ℝ) (c : n → ℝ)
    (A B : Matrix n n ℝ) (h : ℕ)
    (gate : FixedTransitionCovarianceGate A B h)
    (hF : IsUnit F) (y : n → ℝ) :
    y ∈ affineFixedTransitionReachabilityEllipsoid_of_gate
      F c A B h gate hF ↔
      y ∈ centeredInverseEllipsoidOfPosDef
        (pushForwardCovariance F (covariance A (B * B.transpose) h))
        (pushForwardCovariance_posDef F
          (covariance A (B * B.transpose) h) hF gate.posDef) c := by
  exact affineFixedTransitionReachabilityEllipsoid_mem_iff_centeredInverseEllipsoid
    F c A B h gate.posDef hF y

/-- The span-licensed L10D constructor is the common-gate constructor for the
span gate. -/
theorem affineFixedTransitionReachabilityEllipsoid_of_blockSpan_eq_of_gate
    (F : Matrix n n ℝ) (c : n → ℝ)
    (A B : Matrix n n ℝ) (h : ℕ)
    (hspan :
      blockColumnSpan
          (fun k : Fin h => fixedTransitionFactors A B k) = ⊤)
    (hF : IsUnit F) :
    affineFixedTransitionReachabilityEllipsoid_of_blockSpan
      F c A B h hspan hF =
      affineFixedTransitionReachabilityEllipsoid_of_gate
        F c A B h (FixedTransitionCovarianceGate.of_blockSpan A B h hspan) hF := by
  rfl

/-- The rank-licensed L10D constructor is the common-gate constructor for the
rank gate. -/
theorem affineFixedTransitionReachabilityEllipsoid_of_blockRank_eq_of_gate
    (F : Matrix n n ℝ) (c : n → ℝ)
    (A B : Matrix n n ℝ) (h : ℕ)
    (hrank :
      (blockFactorMatrix
          (fun k : Fin h => fixedTransitionFactors A B k)).rank =
        Fintype.card n)
    (hF : IsUnit F) :
    affineFixedTransitionReachabilityEllipsoid_of_blockRank
      F c A B h hrank hF =
      affineFixedTransitionReachabilityEllipsoid_of_gate
        F c A B h (FixedTransitionCovarianceGate.of_blockRank A B h hrank) hF := by
  rfl

end

end NoeticDiffusion
