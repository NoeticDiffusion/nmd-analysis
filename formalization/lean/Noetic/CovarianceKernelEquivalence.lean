import Noetic.CovarianceNondegeneracyRectangular

/-!
# L7b: kernel equivalence for rectangular covariance factors

For a family `B k : Matrix n m ℝ`, L7a expresses positive definiteness of
the factor Gramian through detection of every nonzero state direction by some
transpose factor.  This module rewrites that detection condition as the
triviality of the common kernel:

`∀ v ≠ 0, ∃ k, (B k)ᵀ *ᵥ v ≠ 0`
is equivalent to
`∀ v, (∀ k, (B k)ᵀ *ᵥ v = 0) → v = 0`.

The equivalence is logical and exact.  The final theorem transfers it to
`Matrix.PosDef` through L7a.  No rank theorem, invertibility assumption,
regularization, probabilistic claim, or empirical interpretation is added.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n m ι : Type*} [Fintype n] [Fintype m] [Fintype ι]

/-! ## Detection and common-kernel predicates -/

/-- Every nonzero state direction is detected by some transpose factor. -/
def factorDetectsAllDirections (B : ι → Matrix n m ℝ) : Prop :=
  ∀ v : n → ℝ, v ≠ 0 → ∃ k : ι, (B k).transpose *ᵥ v ≠ 0

/-- The common kernel of all transpose factors is trivial. -/
def commonTransposeKernelTrivial (B : ι → Matrix n m ℝ) : Prop :=
  ∀ v : n → ℝ, (∀ k : ι, (B k).transpose *ᵥ v = 0) → v = 0

/-! ## Logical kernel equivalence -/

/-- Detection of every nonzero direction is equivalent to trivial common
kernel of the transpose factors. -/
theorem factorDetectsAllDirections_iff_commonTransposeKernelTrivial
    (B : ι → Matrix n m ℝ) :
    factorDetectsAllDirections B ↔ commonTransposeKernelTrivial B := by
  classical
  constructor
  · intro h v hv
    by_contra hv0
    obtain ⟨k, hk⟩ := h v hv0
    exact hk (hv k)
  · intro h v hv
    by_contra hnone
    push_neg at hnone
    exact hv (h v hnone)

/-! ## PosDef restatement -/

/-- The rectangular factor Gramian is positive definite exactly when its
transpose-factor common kernel is trivial. -/
theorem rectangularFactorGramian_posDef_iff_commonTransposeKernelTrivial
    (B : ι → Matrix n m ℝ) :
    (rectangularFactorGramian B).PosDef ↔
      commonTransposeKernelTrivial B := by
  rw [rectangularFactorGramian_posDef_iff]
  exact factorDetectsAllDirections_iff_commonTransposeKernelTrivial B

end

end NoeticDiffusion
