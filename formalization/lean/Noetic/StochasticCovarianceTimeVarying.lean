import Mathlib.Probability.Moments.Covariance
import Noetic.Covariance
import Noetic.StochasticCovarianceConcrete

/-!
# Finite-horizon stochastic covariance propagation with time-varying data

This module extends the bounded result in
`Noetic.StochasticCovarianceHorizon` to a transition matrix and innovation
covariance that may vary with the step.  The process is represented by finite
families of real-valued random variables
`x h : n → Ω → ℝ`, with innovation `ε h` and deterministic offset `b h`.

The concrete theorem uses Mathlib's scalar `ProbabilityTheory.covariance`,
assembled coordinatewise into `covMatrix`.  At every step it assumes
coordinatewise finite second moments, `Cov (ε h) = Q h`, and zero raw
state--innovation cross-covariance.  The state update and the covariance
recurrence are explicit hypotheses.  The finite-horizon result is proved by
induction from the actual one-step moment theorem; it introduces no process
axiom and does not replace independence by an implicit assumption.

The scope is one discrete finite horizon.  This file does not formalize a
transition-product or time-varying Gramian closed form, an SDE, an empirical
estimator, reachability probability, or a biological interpretation.
-/

namespace NoeticDiffusion

open MeasureTheory
open ProbabilityTheory
open scoped BigOperators Matrix ProbabilityTheory

variable {Ω n : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [Fintype n]

/-! ## Algebraic time-varying covariance sequence -/

/--
The algebraic covariance sequence driven by step-dependent `A h` and `Q h`.
The initial covariance is zero, matching `NoeticDiffusion.covariance`.
-/
def covarianceTimeVarying (A Q : ℕ → Matrix n n ℝ) : ℕ → Matrix n n ℝ
  | 0 => 0
  | Nat.succ h => covStep (A h) (covarianceTimeVarying A Q h) (Q h)

@[simp] theorem covarianceTimeVarying_zero (A Q : ℕ → Matrix n n ℝ) :
    covarianceTimeVarying A Q 0 = 0 := rfl

@[simp] theorem covarianceTimeVarying_succ (A Q : ℕ → Matrix n n ℝ) (h : ℕ) :
    covarianceTimeVarying A Q (Nat.succ h) =
      covStep (A h) (covarianceTimeVarying A Q h) (Q h) := rfl

/-! ## Generic finite-horizon result -/

/--
For a time-indexed affine stochastic process, the covariance matrix follows a
prescribed recurrence with step-dependent transition matrix and innovation
covariance.

The sequence `C` is supplied explicitly so the theorem also covers a
nonzero, nonstationary initial covariance.  All moment and cross-covariance
conditions are stated for every step used by the induction.
-/
theorem covMatrix_finite_horizon_time_varying
    [IsProbabilityMeasure μ]
    (T : ℕ) (A Q : ℕ → Matrix n n ℝ) (b : ℕ → n → ℝ)
    (x ε : ℕ → n → Ω → ℝ) (C : ℕ → Matrix n n ℝ)
    (hX : ∀ h i, MemLp (x h i) 2 μ)
    (hε : ∀ h i, MemLp (ε h i) 2 μ)
    (hεcov : ∀ h, covMatrix (ε h) μ = Q h)
    (hXε : ∀ h i j, cov[x h i, ε h j; μ] = 0)
    (hstep : ∀ h,
      x (Nat.succ h) = affineNoise (A h) (b h) (x h) (ε h))
    (hC0 : covMatrix (x 0) μ = C 0)
    (hCstep : ∀ h,
      C (Nat.succ h) = covStep (A h) (C h) (Q h)) :
    covMatrix (x T) μ = C T := by
  induction T with
  | zero => exact hC0
  | succ h ih =>
      calc
        covMatrix (x (Nat.succ h)) μ =
            covMatrix (affineNoise (A h) (b h) (x h) (ε h)) μ := by
              rw [hstep h]
        _ = A h * covMatrix (x h) μ * (A h).transpose + Q h := by
              exact covMatrix_affineNoise (A h) (b h) (x h) (ε h) (Q h)
                (hX h) (hε h) (hεcov h) (hXε h)
        _ = covStep (A h) (C h) (Q h) := by
              rw [ih]
              simp [covStep]
        _ = C (Nat.succ h) := (hCstep h).symm

/-! ## Zero-initial covariance specialization -/

/--
With zero initial state covariance, the stochastic finite-horizon covariance
equals the step-dependent algebraic sequence `covarianceTimeVarying A Q`.
-/
theorem covMatrix_finite_horizon_time_varying_zero_initial
    [IsProbabilityMeasure μ]
    (T : ℕ) (A Q : ℕ → Matrix n n ℝ) (b : ℕ → n → ℝ)
    (x ε : ℕ → n → Ω → ℝ)
    (hX : ∀ h i, MemLp (x h i) 2 μ)
    (hε : ∀ h i, MemLp (ε h i) 2 μ)
    (hεcov : ∀ h, covMatrix (ε h) μ = Q h)
    (hXε : ∀ h i j, cov[x h i, ε h j; μ] = 0)
    (hstep : ∀ h,
      x (Nat.succ h) = affineNoise (A h) (b h) (x h) (ε h))
    (hX0 : covMatrix (x 0) μ = 0) :
    covMatrix (x T) μ = covarianceTimeVarying A Q T := by
  apply covMatrix_finite_horizon_time_varying T A Q b x ε
    (covarianceTimeVarying A Q) hX hε hεcov hXε hstep
  · simpa using hX0
  · intro h
    exact covarianceTimeVarying_succ A Q h

end NoeticDiffusion
