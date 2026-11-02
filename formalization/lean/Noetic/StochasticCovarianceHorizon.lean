import Mathlib.Probability.Moments.Covariance
import Noetic.Covariance
import Noetic.StochasticCovarianceConcrete

/-!
# L3b: finite-horizon stochastic covariance propagation

This module lifts the concrete one-step result in
`Noetic.StochasticCovarianceConcrete` to a finite horizon.  The process is
represented by finite families of real-valued random variables
`x h : n → Ω → ℝ`, and the innovation at step `h` by `ε h`.  The transition
matrix is fixed, while the deterministic offset `b h` may vary with time.

The result is deliberately bounded to a discrete finite-horizon argument.
It assumes coordinatewise finite second moments, the innovation covariance
`Q` at every step, and zero state--innovation cross-covariance at every step.
The state update and the covariance recurrence are explicit hypotheses.  The
proof is induction on the horizon and uses the actual `Measure`/`MemLp`
covariance theorem from the concrete L3a module; no stochastic process axiom
or hidden independence assumption is introduced.

The result establishes a finite-horizon one-step recursion.  It does not
establish an SDE, an empirical estimator, reachability probability, or a
biological interpretation.  A zero initial covariance is only needed by the
specialized corollary for the algebraic `covariance A Q` sequence; the general
result permits an arbitrary initial covariance matrix.
-/

namespace NoeticDiffusion

open MeasureTheory
open ProbabilityTheory
open scoped BigOperators Matrix ProbabilityTheory

variable {Ω n : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [Fintype n]

/-! ## Generic finite-horizon result -/

/--
For a time-indexed affine stochastic process, the covariance matrix follows
the prescribed finite-horizon recurrence.

The recurrence is stated for an arbitrary matrix sequence `C`.  This keeps
the theorem useful when the initial state has nonzero covariance and makes
the induction's mathematical contract visible in the statement.
-/
theorem covMatrix_finite_horizon
    [IsProbabilityMeasure μ]
    (T : ℕ) (A : Matrix n n ℝ) (b : ℕ → n → ℝ)
    (x ε : ℕ → n → Ω → ℝ) (Q : Matrix n n ℝ)
    (C : ℕ → Matrix n n ℝ)
    (hX : ∀ h i, MemLp (x h i) 2 μ)
    (hε : ∀ h i, MemLp (ε h i) 2 μ)
    (hεcov : ∀ h, covMatrix (ε h) μ = Q)
    (hXε : ∀ h i j, cov[x h i, ε h j; μ] = 0)
    (hstep : ∀ h, x (Nat.succ h) = affineNoise A (b h) (x h) (ε h))
    (hC0 : covMatrix (x 0) μ = C 0)
    (hCstep : ∀ h, C (Nat.succ h) = covStep A (C h) Q) :
    covMatrix (x T) μ = C T := by
  induction T with
  | zero => exact hC0
  | succ h ih =>
      calc
        covMatrix (x (Nat.succ h)) μ =
            covMatrix (affineNoise A (b h) (x h) (ε h)) μ := by
              rw [hstep h]
        _ = A * covMatrix (x h) μ * A.transpose + Q := by
              exact covMatrix_affineNoise A (b h) (x h) (ε h) Q
                (hX h) (hε h) (hεcov h) (hXε h)
        _ = covStep A (C h) Q := by
              rw [ih]
              simp [covStep]
        _ = C (Nat.succ h) := (hCstep h).symm

/-! ## Corollary for the zero-initial covariance sequence -/

/--
The common local-spread specialization: if the initial state covariance is
zero, the finite-horizon stochastic covariance equals the algebraic sequence
`covariance A Q` from `Noetic.Covariance`.
-/
theorem covMatrix_finite_horizon_zero_initial
    [IsProbabilityMeasure μ]
    (T : ℕ) (A : Matrix n n ℝ) (b : ℕ → n → ℝ)
    (x ε : ℕ → n → Ω → ℝ) (Q : Matrix n n ℝ)
    (hX : ∀ h i, MemLp (x h i) 2 μ)
    (hε : ∀ h i, MemLp (ε h i) 2 μ)
    (hεcov : ∀ h, covMatrix (ε h) μ = Q)
    (hXε : ∀ h i j, cov[x h i, ε h j; μ] = 0)
    (hstep : ∀ h, x (Nat.succ h) = affineNoise A (b h) (x h) (ε h))
    (hX0 : covMatrix (x 0) μ = 0) :
    covMatrix (x T) μ = covariance A Q T := by
  apply covMatrix_finite_horizon T A b x ε Q (covariance A Q)
    hX hε hεcov hXε hstep
  · simpa using hX0
  · intro h
    exact covariance_succ A Q h

end NoeticDiffusion
