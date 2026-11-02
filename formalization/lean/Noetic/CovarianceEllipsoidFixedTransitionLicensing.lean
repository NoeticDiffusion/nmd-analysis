import Noetic.CovarianceEllipsoidFixedTransition

/-!
# L10D: derived licensing for affine fixed-transition ellipsoids

The L10C constructor requires an explicit positive-definiteness witness for
the finite-horizon fixed-transition covariance.  This module derives that
witness internally from either the propagated-factor block-column span gate
or the equivalent full-row-rank gate.  The affine map remains guarded by an
explicit `IsUnit F` witness, and the affine centre remains an explicit input.

The membership results are direct specializations of the L10C equivalence.
They are finite real linear-algebra statements and do not add a probability,
occupancy, empirical, or biological interpretation to the ellipsoid.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

local instance covarianceEllipsoidFixedTransitionLicensingDecidableEq :
    DecidableEq n :=
  Classical.decEq n

/-! ## Block-column span licensing -/

/-- Affine fixed-transition ellipsoid whose covariance license is derived
from the propagated-factor block-column span gate. -/
def affineFixedTransitionReachabilityEllipsoid_of_blockSpan
    (F : Matrix n n ℝ) (c : n → ℝ)
    (A B : Matrix n n ℝ) (h : ℕ)
    (hspan :
      blockColumnSpan
          (fun k : Fin h => fixedTransitionFactors A B k) = ⊤)
    (hF : IsUnit F) : Set (n → ℝ) :=
  affineFixedTransitionReachabilityEllipsoid F c A B h
    ((covariance_posDef_iff_fixedTransition_blockSpan A B h).mpr hspan) hF

/-- Membership in the block-span-licensed affine fixed-transition ellipsoid
is equivalent to membership in the centred inverse ellipsoid of its pushed-
forward covariance. -/
theorem affineFixedTransitionReachabilityEllipsoid_of_blockSpan_mem_iff_centeredInverseEllipsoid
    (F : Matrix n n ℝ) (c : n → ℝ)
    (A B : Matrix n n ℝ) (h : ℕ)
    (hspan :
      blockColumnSpan
          (fun k : Fin h => fixedTransitionFactors A B k) = ⊤)
    (hF : IsUnit F) (y : n → ℝ) :
    y ∈ affineFixedTransitionReachabilityEllipsoid_of_blockSpan
      F c A B h hspan hF ↔
      y ∈ centeredInverseEllipsoidOfPosDef
        (pushForwardCovariance F (covariance A (B * B.transpose) h))
        (pushForwardCovariance_posDef F
          (covariance A (B * B.transpose) h) hF
          ((covariance_posDef_iff_fixedTransition_blockSpan A B h).mpr hspan)) c := by
  exact affineFixedTransitionReachabilityEllipsoid_mem_iff_centeredInverseEllipsoid
    F c A B h
    ((covariance_posDef_iff_fixedTransition_blockSpan A B h).mpr hspan) hF y

/-! ## Full-row-rank licensing -/

/-- Affine fixed-transition ellipsoid whose covariance license is derived
from the propagated-factor block matrix's full-row-rank gate. -/
def affineFixedTransitionReachabilityEllipsoid_of_blockRank
    (F : Matrix n n ℝ) (c : n → ℝ)
    (A B : Matrix n n ℝ) (h : ℕ)
    (hrank :
      (blockFactorMatrix
          (fun k : Fin h => fixedTransitionFactors A B k)).rank =
        Fintype.card n)
    (hF : IsUnit F) : Set (n → ℝ) :=
  affineFixedTransitionReachabilityEllipsoid F c A B h
    ((covariance_posDef_iff_fixedTransition_blockRank A B h).mpr hrank) hF

/-- Membership in the full-rank-licensed affine fixed-transition ellipsoid
is equivalent to membership in the centred inverse ellipsoid of its pushed-
forward covariance. -/
theorem affineFixedTransitionReachabilityEllipsoid_of_blockRank_mem_iff_centeredInverseEllipsoid
    (F : Matrix n n ℝ) (c : n → ℝ)
    (A B : Matrix n n ℝ) (h : ℕ)
    (hrank :
      (blockFactorMatrix
          (fun k : Fin h => fixedTransitionFactors A B k)).rank =
        Fintype.card n)
    (hF : IsUnit F) (y : n → ℝ) :
    y ∈ affineFixedTransitionReachabilityEllipsoid_of_blockRank
      F c A B h hrank hF ↔
      y ∈ centeredInverseEllipsoidOfPosDef
        (pushForwardCovariance F (covariance A (B * B.transpose) h))
        (pushForwardCovariance_posDef F
          (covariance A (B * B.transpose) h) hF
          ((covariance_posDef_iff_fixedTransition_blockRank A B h).mpr hrank)) c := by
  exact affineFixedTransitionReachabilityEllipsoid_mem_iff_centeredInverseEllipsoid
    F c A B h
    ((covariance_posDef_iff_fixedTransition_blockRank A B h).mpr hrank) hF y

end

end NoeticDiffusion
