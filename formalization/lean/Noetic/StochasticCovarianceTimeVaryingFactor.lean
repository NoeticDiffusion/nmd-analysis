import Noetic.CovariancePSD
import Noetic.StochasticCovarianceTimeVaryingNondegeneracy
import Noetic.CovarianceLicensing

/-!
# L11b-1/L11b-2: factor selection for an arbitrary time-varying PSD sequence

`Noetic.StochasticCovarianceTimeVaryingNondegeneracy` (L11) states its five
nondegeneracy equivalences for an innovation covariance that is already given
in factored form `Q h = B h * (B h)ᵀ`.  This module closes the remaining
bridge: an arbitrary positive-semidefinite sequence `Q h` is automatically
assigned such a factor sequence, existentially and step by step, using the
L7d factorization `posSemidef_exists_factor_mul_transpose` together with the
`choose` tactic.  Composing that selection with the L11 equivalences yields
existential nondegeneracy criteria stated directly for `Q`, and the matching
singular boundary for `covarianceTimeVarying`, which required the new
induction lemma `covarianceTimeVarying_posSemidef` (this module supplies it;
it was not present in `StochasticCovarianceTimeVaryingNondegeneracy`).

The factor is chosen existentially (`Classical.choice`), not computed: no
Cholesky, no numerical algorithm, no regularization.  The result is still a
finite, algebraic covariance object; it does not add stability, control
reachability, probability coverage, empirical reachability, or a statement
about which protocol produced `A h`, `Q h`.

Source: articles/NDT v2 S7 inventory table row 10 and section 7 item 2;
`project/diary/300_20260909_lean_timevarying_nondegeneracy.md`; manuscript
lines 596-623 (`Σ_t^{(h+1)} = A_t Σ A_tᵀ + Q_t`, time-indexed).
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

local instance timeVaryingFactorDecidableEq : DecidableEq n :=
  Classical.decEq n

/-! ## L11b-1: factor selection -/

/-- Every step-indexed positive-semidefinite sequence `Q h` admits a
step-indexed factor sequence `B h` with `Q h = B h * (B h)ᵀ`.  The factor is
chosen existentially by the `choose` tactic from the L7d factorization at
each step; it is not computed. -/
theorem exists_timeVarying_factor_sequence
    (Q : ℕ → Matrix n n ℝ) (hQ : ∀ h, (Q h).PosSemidef) :
    ∃ B : ℕ → Matrix n n ℝ, ∀ h, Q h = B h * (B h).transpose := by
  choose B hB using fun h => posSemidef_exists_factor_mul_transpose (Q h) (hQ h)
  exact ⟨B, hB⟩

/-! ## `covarianceTimeVarying` positive semidefiniteness -/

/-- The time-varying covariance sequence is positive semidefinite at every
horizon, for any positive-semidefinite step-indexed innovation covariance.
Proved by induction exactly like `covariance_posSemidef`; this lemma was not
present in `StochasticCovarianceTimeVaryingNondegeneracy`. -/
theorem covarianceTimeVarying_posSemidef
    (A Q : ℕ → Matrix n n ℝ) (hQ : ∀ h, (Q h).PosSemidef) (T : ℕ) :
    (covarianceTimeVarying A Q T).PosSemidef := by
  induction T with
  | zero => exact Matrix.PosSemidef.zero
  | succ T ih => exact covStep_posSemidef ih (hQ T)

/-! ## L11b-2: existential nondegeneracy criteria for arbitrary PSD `Q h` -/

private lemma covarianceTimeVarying_eq_of_factorSequence
    (A Q B : ℕ → Matrix n n ℝ) (hB : ∀ h, Q h = B h * (B h).transpose) :
    covarianceTimeVarying A Q = covarianceTimeVarying A (fun h => B h * (B h).transpose) := by
  have hQeq : Q = fun h => B h * (B h).transpose := funext hB
  rw [hQeq]

/-- Positive definiteness of the time-varying covariance for an arbitrary
positive-semidefinite innovation sequence is equivalent to the existence of a
factor sequence whose propagated factors detect every nonzero state
direction. -/
theorem covarianceTimeVarying_posDef_iff_exists_propagatedFactorDetects
    (A Q : ℕ → Matrix n n ℝ) (hQ : ∀ h, (Q h).PosSemidef) (T : ℕ) :
    (covarianceTimeVarying A Q T).PosDef ↔
      ∃ B : ℕ → Matrix n n ℝ, (∀ h, Q h = B h * (B h).transpose) ∧
        ∀ v : n → ℝ, v ≠ 0 → ∃ k : Fin T,
          (timeVaryingPropagatedFactor A B T k).transpose *ᵥ v ≠ 0 := by
  constructor
  · intro hPD
    obtain ⟨B, hB⟩ := exists_timeVarying_factor_sequence Q hQ
    refine ⟨B, hB, ?_⟩
    rw [covarianceTimeVarying_eq_of_factorSequence A Q B hB] at hPD
    exact (covarianceTimeVarying_posDef_iff_propagatedFactorDetects A B T).mp hPD
  · rintro ⟨B, hB, hdet⟩
    rw [covarianceTimeVarying_eq_of_factorSequence A Q B hB]
    exact (covarianceTimeVarying_posDef_iff_propagatedFactorDetects A B T).mpr hdet

/-- Positive definiteness of the time-varying covariance for an arbitrary
positive-semidefinite innovation sequence is equivalent to the existence of a
factor sequence whose propagated factors have trivial common transpose
kernel. -/
theorem covarianceTimeVarying_posDef_iff_exists_propagatedCommonTransposeKernelTrivial
    (A Q : ℕ → Matrix n n ℝ) (hQ : ∀ h, (Q h).PosSemidef) (T : ℕ) :
    (covarianceTimeVarying A Q T).PosDef ↔
      ∃ B : ℕ → Matrix n n ℝ, (∀ h, Q h = B h * (B h).transpose) ∧
        commonTransposeKernelTrivial
          (fun k : Fin T => timeVaryingPropagatedFactor A B T k) := by
  constructor
  · intro hPD
    obtain ⟨B, hB⟩ := exists_timeVarying_factor_sequence Q hQ
    refine ⟨B, hB, ?_⟩
    rw [covarianceTimeVarying_eq_of_factorSequence A Q B hB] at hPD
    exact (covarianceTimeVarying_posDef_iff_propagatedCommonTransposeKernelTrivial
      A B T).mp hPD
  · rintro ⟨B, hB, hker⟩
    rw [covarianceTimeVarying_eq_of_factorSequence A Q B hB]
    exact (covarianceTimeVarying_posDef_iff_propagatedCommonTransposeKernelTrivial
      A B T).mpr hker

/-- Positive definiteness of the time-varying covariance for an arbitrary
positive-semidefinite innovation sequence is equivalent to the existence of a
factor sequence whose propagated factors span the state space. -/
theorem covarianceTimeVarying_posDef_iff_exists_propagatedBlockSpan
    (A Q : ℕ → Matrix n n ℝ) (hQ : ∀ h, (Q h).PosSemidef) (T : ℕ) :
    (covarianceTimeVarying A Q T).PosDef ↔
      ∃ B : ℕ → Matrix n n ℝ, (∀ h, Q h = B h * (B h).transpose) ∧
        blockColumnSpan
            (fun k : Fin T => timeVaryingPropagatedFactor A B T k) = ⊤ := by
  constructor
  · intro hPD
    obtain ⟨B, hB⟩ := exists_timeVarying_factor_sequence Q hQ
    refine ⟨B, hB, ?_⟩
    rw [covarianceTimeVarying_eq_of_factorSequence A Q B hB] at hPD
    exact (covarianceTimeVarying_posDef_iff_propagatedBlockSpan A B T).mp hPD
  · rintro ⟨B, hB, hspan⟩
    rw [covarianceTimeVarying_eq_of_factorSequence A Q B hB]
    exact (covarianceTimeVarying_posDef_iff_propagatedBlockSpan A B T).mpr hspan

/-- Positive definiteness of the time-varying covariance for an arbitrary
positive-semidefinite innovation sequence is equivalent to the existence of a
factor sequence whose assembled propagated-factor matrix has full row rank. -/
theorem covarianceTimeVarying_posDef_iff_exists_propagatedBlockRank
    (A Q : ℕ → Matrix n n ℝ) (hQ : ∀ h, (Q h).PosSemidef) (T : ℕ) :
    (covarianceTimeVarying A Q T).PosDef ↔
      ∃ B : ℕ → Matrix n n ℝ, (∀ h, Q h = B h * (B h).transpose) ∧
        (blockFactorMatrix
            (fun k : Fin T => timeVaryingPropagatedFactor A B T k)).rank =
          Fintype.card n := by
  constructor
  · intro hPD
    obtain ⟨B, hB⟩ := exists_timeVarying_factor_sequence Q hQ
    refine ⟨B, hB, ?_⟩
    rw [covarianceTimeVarying_eq_of_factorSequence A Q B hB] at hPD
    exact (covarianceTimeVarying_posDef_iff_propagatedBlockRank A B T).mp hPD
  · rintro ⟨B, hB, hrank⟩
    rw [covarianceTimeVarying_eq_of_factorSequence A Q B hB]
    exact (covarianceTimeVarying_posDef_iff_propagatedBlockRank A B T).mpr hrank

/-! ## Singular boundary for `covarianceTimeVarying` -/

/-- The time-varying covariance is singular whenever it is not positive
definite, for any positive-semidefinite innovation sequence.  Mirrors L8's
`posSemidef_det_eq_zero_of_not_posDef` for the fixed-transition covariance. -/
theorem covarianceTimeVarying_det_eq_zero_of_not_posDef
    (A Q : ℕ → Matrix n n ℝ) (hQ : ∀ h, (Q h).PosSemidef) (T : ℕ)
    (hnot : ¬ (covarianceTimeVarying A Q T).PosDef) :
    Matrix.det (covarianceTimeVarying A Q T) = 0 :=
  posSemidef_det_eq_zero_of_not_posDef _
    (covarianceTimeVarying_posSemidef A Q hQ T) hnot

end

end NoeticDiffusion
