import Noetic.StochasticCovarianceTimeVaryingGramian
import Noetic.CovarianceNondegeneracy
import Noetic.CovarianceBlockRank

/-!
# L11: time-varying propagated-factor nondegeneracy

For step-dependent transition matrices `A h` and square innovation factors
`B h`, this module identifies the finite-horizon covariance

`covarianceTimeVarying A (fun h => B h * B hᵀ) T`

with the Gramian of the propagated factors

`Φ(T,h+1) * B h`,

where `Φ` is the existing length-indexed `transitionProduct`.  The resulting
positive-definiteness criterion is then restated through the existing factor,
common-kernel, block-span, and rank equivalences.

The horizon and innovation indices remain finite (`Fin T`); no infinite sum,
stability assumption, stochastic reachability claim, empirical estimator, or
biological interpretation is introduced.  The fixed-transition affine
ellipsoid gate is deliberately not imported here: its covariance type is the
separate fixed-`A`, fixed-`B` recurrence `covariance A (B Bᵀ) h`.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

local instance timeVaryingNondegeneracyDecidableEq : DecidableEq n :=
  Classical.decEq n

/-! ## Propagated factors and their Gramian -/

/-- The factor from innovation step `k` propagated to horizon `T`. -/
def timeVaryingPropagatedFactor
    (A B : ℕ → Matrix n n ℝ) (T : ℕ) (k : Fin T) : Matrix n n ℝ :=
  transitionProduct A (k.val + 1) (T - (k.val + 1)) * B k.val

/-- The finite Gramian of all time-varying propagated innovation factors. -/
def timeVaryingPropagatedFactorGramian
    (A B : ℕ → Matrix n n ℝ) (T : ℕ) : Matrix n n ℝ :=
  factorGramian (fun k : Fin T => timeVaryingPropagatedFactor A B T k)

private lemma timeVaryingGramianTerm_eq_propagatedFactor_term
    (A B : ℕ → Matrix n n ℝ) (T h : ℕ) (hh : h < T) :
    timeVaryingGramianTerm A (fun j => B j * (B j).transpose) T h =
      timeVaryingPropagatedFactor A B T ⟨h, hh⟩ *
        (timeVaryingPropagatedFactor A B T ⟨h, hh⟩).transpose := by
  unfold timeVaryingGramianTerm timeVaryingPropagatedFactor
  rw [Matrix.transpose_mul]
  simp [Matrix.mul_assoc]

/-! ## Time-varying factor/Gramian identity -/

/-- The time-varying covariance Gramian is the Gramian of its propagated
innovation factors. -/
theorem covarianceTimeVarying_eq_timeVaryingPropagatedFactorGramian
    (A B : ℕ → Matrix n n ℝ) (T : ℕ) :
    covarianceTimeVarying A (fun h => B h * (B h).transpose) T =
      timeVaryingPropagatedFactorGramian A B T := by
  rw [covarianceTimeVarying_eq_timeVaryingGramian]
  unfold timeVaryingGramian timeVaryingPropagatedFactorGramian factorGramian
  rw [Finset.sum_fin_eq_sum_range]
  apply Finset.sum_congr rfl
  intro h hh
  rw [dif_pos (Finset.mem_range.mp hh)]
  exact timeVaryingGramianTerm_eq_propagatedFactor_term A B T h
    (Finset.mem_range.mp hh)

/-! ## Exact nondegeneracy criteria -/

/-- Positive definiteness is equivalent to detection by one propagated factor
in every nonzero state direction. -/
theorem covarianceTimeVarying_posDef_iff_propagatedFactorDetects
    (A B : ℕ → Matrix n n ℝ) (T : ℕ) :
    (covarianceTimeVarying A (fun h => B h * (B h).transpose) T).PosDef ↔
      ∀ v : n → ℝ, v ≠ 0 → ∃ k : Fin T,
        (timeVaryingPropagatedFactor A B T k).transpose *ᵥ v ≠ 0 := by
  rw [covarianceTimeVarying_eq_timeVaryingPropagatedFactorGramian,
    timeVaryingPropagatedFactorGramian]
  exact factorGramian_posDef_iff _

/-- Positive definiteness is equivalent to triviality of the common transpose
kernel of all propagated factors. -/
theorem covarianceTimeVarying_posDef_iff_propagatedCommonTransposeKernelTrivial
    (A B : ℕ → Matrix n n ℝ) (T : ℕ) :
    (covarianceTimeVarying A (fun h => B h * (B h).transpose) T).PosDef ↔
      commonTransposeKernelTrivial
        (fun k : Fin T => timeVaryingPropagatedFactor A B T k) := by
  rw [covarianceTimeVarying_eq_timeVaryingPropagatedFactorGramian,
    timeVaryingPropagatedFactorGramian, factorGramian_posDef_iff]
  exact factorDetectsAllDirections_iff_commonTransposeKernelTrivial _

/-- Positive definiteness is equivalent to the propagated factors spanning the
state space through their assembled block matrix. -/
theorem covarianceTimeVarying_posDef_iff_propagatedBlockSpan
    (A B : ℕ → Matrix n n ℝ) (T : ℕ) :
    (covarianceTimeVarying A (fun h => B h * (B h).transpose) T).PosDef ↔
      blockColumnSpan
          (fun k : Fin T => timeVaryingPropagatedFactor A B T k) = ⊤ := by
  rw [covarianceTimeVarying_eq_timeVaryingPropagatedFactorGramian,
    timeVaryingPropagatedFactorGramian]
  exact (factorGramian_posDef_iff _).trans
    ((factorDetectsAllDirections_iff_commonTransposeKernelTrivial _).trans
      ((commonTransposeKernelTrivial_iff_blockTransposeKernelTrivial _).trans
        (blockTransposeKernelTrivial_iff_blockColumnSpan_eq_top _)))

/-- Positive definiteness is equivalent to full row rank of the assembled
propagated-factor matrix. -/
theorem covarianceTimeVarying_posDef_iff_propagatedBlockRank
    (A B : ℕ → Matrix n n ℝ) (T : ℕ) :
    (covarianceTimeVarying A (fun h => B h * (B h).transpose) T).PosDef ↔
      (blockFactorMatrix
          (fun k : Fin T => timeVaryingPropagatedFactor A B T k)).rank =
        Fintype.card n := by
  rw [covarianceTimeVarying_posDef_iff_propagatedBlockSpan,
    blockColumnSpan_eq_top_iff_rank_eq_card]

end

end NoeticDiffusion
