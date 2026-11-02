import Mathlib.LinearAlgebra.Matrix.Rank
import Noetic.CovarianceBlockSpan

/-!
# L7c (span/rank bridge): column-span and rank for the block factor operator

This module is finite-dimensional linear algebra only.  For a family of
rectangular factors `B k`, `blockFactorMatrix B` concatenates their columns.
The common transpose-kernel condition from L7c is equivalent to the column
span of this block matrix being the whole state space, and therefore to full
row rank.  No covariance, reachability, or empirical interpretation is used
here.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix
open Module

variable {n m ι : Type*}
variable [Fintype n] [Fintype m] [Fintype ι]

/-- The column span of the matrix obtained by concatenating all factor
columns. -/
def blockColumnSpan (B : ι → Matrix n m ℝ) : Submodule ℝ (n → ℝ) :=
  Submodule.span ℝ (Set.range (blockFactorMatrix B).col)

/-- The block factor matrix has full row rank exactly when its columns span
the state space. -/
theorem blockColumnSpan_eq_top_iff_rank_eq_card
    (B : ι → Matrix n m ℝ) :
    blockColumnSpan B = ⊤ ↔ (blockFactorMatrix B).rank = Fintype.card n := by
  constructor
  · intro h
    calc
      (blockFactorMatrix B).rank = finrank ℝ (blockColumnSpan B) := by
        simpa [blockColumnSpan] using
          (Matrix.rank_eq_finrank_span_cols (blockFactorMatrix B))
      _ = finrank ℝ (n → ℝ) := by rw [h, finrank_top]
      _ = Fintype.card n := by simp
  · intro h
    apply Submodule.eq_top_of_finrank_eq
    calc
      finrank ℝ (blockColumnSpan B) = (blockFactorMatrix B).rank := by
        simpa [blockColumnSpan] using
          (Matrix.rank_eq_finrank_span_cols (blockFactorMatrix B)).symm
      _ = Fintype.card n := h
      _ = finrank ℝ (n → ℝ) := by simp

/-- Triviality of the block transpose kernel is equivalent to spanning all
state directions by the block matrix columns. -/
theorem blockTransposeKernelTrivial_iff_blockColumnSpan_eq_top
    (B : ι → Matrix n m ℝ) :
    blockTransposeKernelTrivial B ↔ blockColumnSpan B = ⊤ := by
  constructor
  · intro h
    have hker :
        LinearMap.ker (blockFactorMatrix B).transpose.mulVecLin = ⊥ := by
      apply Matrix.ker_mulVecLin_eq_bot_iff.mpr
      intro v hv
      exact h v hv
    have hinj :
        Function.Injective (blockFactorMatrix B).transpose.mulVecLin :=
      LinearMap.ker_eq_bot.mp hker
    have hrankT :
        (blockFactorMatrix B).transpose.rank = Fintype.card n := by
      unfold Matrix.rank
      rw [LinearMap.finrank_range_of_inj hinj]
      simp
    have hrank : (blockFactorMatrix B).rank = Fintype.card n := by
      calc
        (blockFactorMatrix B).rank = (blockFactorMatrix B).transpose.rank := by
          symm
          exact Matrix.rank_transpose (blockFactorMatrix B)
        _ = Fintype.card n := hrankT
    exact (blockColumnSpan_eq_top_iff_rank_eq_card B).mpr hrank
  · intro h
    have hrank : (blockFactorMatrix B).rank = Fintype.card n :=
      (blockColumnSpan_eq_top_iff_rank_eq_card B).mp h
    have hrankT :
        (blockFactorMatrix B).transpose.rank = Fintype.card n := by
      calc
        (blockFactorMatrix B).transpose.rank = (blockFactorMatrix B).rank :=
          Matrix.rank_transpose (blockFactorMatrix B)
        _ = Fintype.card n := hrank
    have hrange :
        finrank ℝ (LinearMap.range (blockFactorMatrix B).transpose.mulVecLin) =
          Fintype.card n := by
      simpa [Matrix.rank] using hrankT
    have hdomain : finrank ℝ (n → ℝ) = Fintype.card n := by simp
    have hkerfin :
        finrank ℝ (LinearMap.ker (blockFactorMatrix B).transpose.mulVecLin) = 0 := by
      have hsum :=
        LinearMap.finrank_range_add_finrank_ker
          ((blockFactorMatrix B).transpose.mulVecLin)
      rw [hrange, hdomain] at hsum
      omega
    have hker :
        LinearMap.ker (blockFactorMatrix B).transpose.mulVecLin = ⊥ :=
      Submodule.finrank_eq_zero.mp hkerfin
    apply Matrix.ker_mulVecLin_eq_bot_iff.mp hker

end

end NoeticDiffusion
