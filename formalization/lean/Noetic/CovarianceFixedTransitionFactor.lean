import Noetic.CovarianceNondegeneracy
import Noetic.CovariancePSD

/-!
# L7d bridge to fixed-transition factors

The PSD factorization of an innovation covariance can be used directly in the
existing fixed-transition Gramian identity.  This module records that bridge
as one existential algebraic theorem.  It introduces no numerical,
probabilistic, reachability, or empirical interpretation.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

/-- A PSD innovation covariance admits a factor whose fixed-transition factors
give the corresponding finite-horizon covariance Gramian. -/
theorem exists_fixedTransition_factorGramian_of_posSemidef
    (A Q : Matrix n n ℝ) (hQ : Q.PosSemidef) (h : ℕ) :
    ∃ B : Matrix n n ℝ,
      Q = B * B.transpose ∧
        covariance A Q h =
          factorGramian (fun k : Fin h => fixedTransitionFactors A B k) := by
  classical
  obtain ⟨B, hB⟩ := posSemidef_exists_factor_mul_transpose Q hQ
  refine ⟨B, hB, ?_⟩
  rw [covariance_eq_gramian A Q h, hB]
  exact (fixedTransitionGramian_eq_factorGramian A B h).symm

end

end NoeticDiffusion
