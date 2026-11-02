import Noetic.CovarianceFixedTransitionFactor
import Noetic.CovarianceBlockRank

/-!
# Fixed-transition detection, span, and rank chain

This module instantiates the L7b/L7c equivalences with the fixed-transition
factor family `k ↦ A^k * B`.  It records the positive-definiteness bridge to
the block column span and to full row rank.  The statements are finite and
algebraic; they make no empirical controllability, reachability, numerical,
or biological claim.  The quantification includes the zero horizon `h = 0`
and the empty state index; no `Nonempty n` assumption is hidden in the API.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

local instance fixedTransitionChainDecidableEq : DecidableEq n :=
  Classical.decEq n

/-! ## Fixed-transition span and rank corollaries -/

/-- For a fixed transition, detection by the propagated factors is equivalent
to full column span of their block matrix. -/
theorem fixedTransition_factorDetects_iff_blockSpan
    (A B : Matrix n n ℝ) (h : ℕ) :
    factorDetectsAllDirections
        (fun k : Fin h => fixedTransitionFactors A B k) ↔
      blockColumnSpan
          (fun k : Fin h => fixedTransitionFactors A B k) = ⊤ := by
  rw [factorDetectsAllDirections_iff_commonTransposeKernelTrivial,
    commonTransposeKernelTrivial_iff_blockTransposeKernelTrivial,
    blockTransposeKernelTrivial_iff_blockColumnSpan_eq_top]

/-- Positive definiteness of the fixed-transition covariance is equivalent to
the propagated innovation factors spanning the state space. -/
theorem covariance_posDef_iff_fixedTransition_blockSpan
    (A B : Matrix n n ℝ) (h : ℕ) :
    (covariance A (B * B.transpose) h).PosDef ↔
      blockColumnSpan
          (fun k : Fin h => fixedTransitionFactors A B k) = ⊤ := by
  rw [covariance_posDef_iff_fixedTransition_detects A B h]
  exact fixedTransition_factorDetects_iff_blockSpan A B h

/-- Positive definiteness of the fixed-transition covariance is equivalent to
full row rank of the assembled propagated-factor matrix. -/
theorem covariance_posDef_iff_fixedTransition_blockRank
    (A B : Matrix n n ℝ) (h : ℕ) :
    (covariance A (B * B.transpose) h).PosDef ↔
      (blockFactorMatrix
          (fun k : Fin h => fixedTransitionFactors A B k)).rank =
        Fintype.card n := by
  rw [covariance_posDef_iff_fixedTransition_blockSpan A B h]
  exact blockColumnSpan_eq_top_iff_rank_eq_card _

/-! ## PSD innovation covariance bridge -/

/-- A positive-semidefinite innovation covariance admits one factor whose
fixed-transition covariance has both the span and rank characterizations. -/
theorem exists_fixedTransition_chain_of_posSemidef
    (A Q : Matrix n n ℝ) (hQ : Q.PosSemidef) (h : ℕ) :
    ∃ B : Matrix n n ℝ,
      Q = B * B.transpose ∧
        ((covariance A Q h).PosDef ↔
          blockColumnSpan
              (fun k : Fin h => fixedTransitionFactors A B k) = ⊤) ∧
        ((covariance A Q h).PosDef ↔
          (blockFactorMatrix
              (fun k : Fin h => fixedTransitionFactors A B k)).rank =
            Fintype.card n) := by
  obtain ⟨B, hB, _⟩ :=
    exists_fixedTransition_factorGramian_of_posSemidef A Q hQ h
  refine ⟨B, hB, ?_, ?_⟩
  · rw [hB]
    exact covariance_posDef_iff_fixedTransition_blockSpan A B h
  · rw [hB]
    exact covariance_posDef_iff_fixedTransition_blockRank A B h

/-! ## Degenerate-index coverage -/

-- These specializations keep the zero-horizon and empty-state cases inside
-- the same theorem interface; the propositions reduce according to the
-- corresponding empty sums and zero-dimensional span/rank.
example (A B : Matrix n n ℝ) :
    (covariance A (B * B.transpose) 0).PosDef ↔
      blockColumnSpan
          (fun k : Fin 0 => fixedTransitionFactors A B k) = ⊤ :=
  covariance_posDef_iff_fixedTransition_blockSpan A B 0

example (A B : Matrix Empty Empty ℝ) :
    (covariance A (B * B.transpose) 0).PosDef ↔
      (blockFactorMatrix
          (fun k : Fin 0 => fixedTransitionFactors A B k)).rank =
        Fintype.card Empty :=
  covariance_posDef_iff_fixedTransition_blockRank A B 0

end

end NoeticDiffusion
