import Noetic.CovarianceEllipsoidFixedTransitionCommon
import Noetic.CovarianceEllipsoidFixedTransitionLicensing
import Noetic.StochasticCovarianceTimeVaryingNondegeneracy

/-!
# L11b-3: covariance-agnostic gate and time-varying affine ellipsoid

`FixedTransitionCovarianceGate` (L10E) packages a `PosDef` witness for the
one specific covariance type `covariance A (B * Bᵀ) h`.  This module
introduces a covariance-agnostic gate, `CovarianceGate`, that stores an
arbitrary real square matrix together with a `PosDef` witness for that exact
matrix.  The L10E fixed-transition gate, and the time-varying block-span and
block-rank nondegeneracy criteria from L11 (`StochasticCovarianceTimeVaryingNondegeneracy`),
all become constructors of this common gate.  A single affine-ellipsoid
constructor and membership theorem then serve every one of them, and explicit
equality theorems tie the existing L10D/L10E fixed-transition affine-ellipsoid
API to the new covariance-agnostic API.

These are finite real linear-algebra statements only.  The gate does not add
a probability, occupancy, empirical, or biological interpretation to the
ellipsoid, and it does not itself select factors for a time-varying PSD
sequence (see `StochasticCovarianceTimeVaryingFactor` for that bridge).  The
affine map's invertibility is represented by an explicit `IsUnit F` witness;
no inverse-based object is constructed when that witness is absent.

Deviation from the idea file: the gate field is named `cov`, not `Σ`. The
`Σ` character collides with Lean's built-in sigma-type binder notation and
does not parse as a structure field name; `cov` is used instead with no
change in mathematical content.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

local instance covarianceEllipsoidTimeVaryingDecidableEq : DecidableEq n :=
  Classical.decEq n

/-! ## Covariance-agnostic gate -/

/-- A licensed covariance: any real square matrix with an explicit `PosDef`
witness for that exact matrix.  Unlike `FixedTransitionCovarianceGate`, the
underlying matrix is not restricted to the fixed-transition recurrence. -/
structure CovarianceGate (n : Type*) [Fintype n] where
  /-- The licensed covariance matrix. -/
  cov : Matrix n n ℝ
  /-- The positive-definiteness witness for `cov`. -/
  posDef : cov.PosDef

/-- Every L10E fixed-transition gate is a covariance-agnostic gate for its
underlying fixed-transition covariance. -/
def CovarianceGate.ofFixedTransition
    {A B : Matrix n n ℝ} {h : ℕ} (g : FixedTransitionCovarianceGate A B h) :
    CovarianceGate n :=
  ⟨covariance A (B * B.transpose) h, g.posDef⟩

/-- Full propagated-factor block-column span licenses a covariance-agnostic
gate for the time-varying covariance `covarianceTimeVarying A (B Bᵀ) T`. -/
def CovarianceGate.ofTimeVaryingBlockSpan
    (A B : ℕ → Matrix n n ℝ) (T : ℕ)
    (hspan :
      blockColumnSpan
          (fun k : Fin T => timeVaryingPropagatedFactor A B T k) = ⊤) :
    CovarianceGate n :=
  ⟨covarianceTimeVarying A (fun h => B h * (B h).transpose) T,
    (covarianceTimeVarying_posDef_iff_propagatedBlockSpan A B T).mpr hspan⟩

/-- Full propagated-factor block rank licenses a covariance-agnostic gate for
the time-varying covariance `covarianceTimeVarying A (B Bᵀ) T`. -/
def CovarianceGate.ofTimeVaryingBlockRank
    (A B : ℕ → Matrix n n ℝ) (T : ℕ)
    (hrank :
      (blockFactorMatrix
          (fun k : Fin T => timeVaryingPropagatedFactor A B T k)).rank =
        Fintype.card n) :
    CovarianceGate n :=
  ⟨covarianceTimeVarying A (fun h => B h * (B h).transpose) T,
    (covarianceTimeVarying_posDef_iff_propagatedBlockRank A B T).mpr hrank⟩

/-! ## Common affine ellipsoid API -/

/-- The affine ellipsoid licensed by a covariance-agnostic gate: the affine
image `x ↦ F x + c` of the licensed inverse ellipsoid of `g.cov`, guarded by
an explicit `IsUnit F` witness. -/
def CovarianceGate.affineEllipsoid
    (g : CovarianceGate n) (F : Matrix n n ℝ) (hF : IsUnit F) (c : n → ℝ) :
    Set (n → ℝ) :=
  affinePushForwardEllipsoid F c
    (⟨g.posDef⟩ : LicensedInverseEllipsoid g.cov) hF

/-- Membership in the covariance-agnostic gate's affine ellipsoid is exactly
membership in the centred inverse ellipsoid of the pushed-forward
covariance. -/
theorem CovarianceGate.mem_affineEllipsoid_iff
    (g : CovarianceGate n) (F : Matrix n n ℝ) (hF : IsUnit F) (c y : n → ℝ) :
    y ∈ g.affineEllipsoid F hF c ↔
      y ∈ centeredInverseEllipsoidOfPosDef (pushForwardCovariance F g.cov)
        (pushForwardCovariance_posDef F g.cov hF g.posDef) c :=
  affinePushForwardEllipsoid_mem_iff_centeredInverseEllipsoid F c
    (⟨g.posDef⟩ : LicensedInverseEllipsoid g.cov) hF y

/-! ## Equality theorems tying the L10D/L10E API to the new API -/

/-- The L10E common-gate affine ellipsoid equals the covariance-agnostic
gate's affine ellipsoid built from the same fixed-transition gate. -/
theorem fixedTransition_affineEllipsoid_eq_gate_affineEllipsoid
    (F : Matrix n n ℝ) (c : n → ℝ) (A B : Matrix n n ℝ) (h : ℕ)
    (gate : FixedTransitionCovarianceGate A B h) (hF : IsUnit F) :
    affineFixedTransitionReachabilityEllipsoid_of_gate F c A B h gate hF =
      (CovarianceGate.ofFixedTransition gate).affineEllipsoid F hF c :=
  rfl

/-- The L10D block-span-licensed affine ellipsoid equals the
covariance-agnostic gate's affine ellipsoid built from the corresponding
`FixedTransitionCovarianceGate.of_blockSpan` gate. -/
theorem fixedTransition_blockSpan_affineEllipsoid_eq_gate_affineEllipsoid
    (F : Matrix n n ℝ) (c : n → ℝ) (A B : Matrix n n ℝ) (h : ℕ)
    (hspan :
      blockColumnSpan
          (fun k : Fin h => fixedTransitionFactors A B k) = ⊤)
    (hF : IsUnit F) :
    affineFixedTransitionReachabilityEllipsoid_of_blockSpan F c A B h hspan hF =
      (CovarianceGate.ofFixedTransition
        (FixedTransitionCovarianceGate.of_blockSpan A B h hspan)).affineEllipsoid
        F hF c :=
  rfl

/-- The L10D full-rank-licensed affine ellipsoid equals the
covariance-agnostic gate's affine ellipsoid built from the corresponding
`FixedTransitionCovarianceGate.of_blockRank` gate. -/
theorem fixedTransition_blockRank_affineEllipsoid_eq_gate_affineEllipsoid
    (F : Matrix n n ℝ) (c : n → ℝ) (A B : Matrix n n ℝ) (h : ℕ)
    (hrank :
      (blockFactorMatrix
          (fun k : Fin h => fixedTransitionFactors A B k)).rank =
        Fintype.card n)
    (hF : IsUnit F) :
    affineFixedTransitionReachabilityEllipsoid_of_blockRank F c A B h hrank hF =
      (CovarianceGate.ofFixedTransition
        (FixedTransitionCovarianceGate.of_blockRank A B h hrank)).affineEllipsoid
        F hF c :=
  rfl

end

end NoeticDiffusion
