import Noetic.Covariance
import Noetic.StochasticCovarianceTimeVarying

/-!
# Time-varying finite-horizon covariance Gramian

This module gives a closed finite-sum form for the algebraic recurrence with
step-dependent transition matrices and innovation covariances:

`C (h + 1) = A h * C h * (A h)ᵀ + Q h`.

The transition product is defined by its length.  Thus
`transitionProduct A s k` is
`A (s + k - 1) * ... * A (s + 1) * A s`, with the empty product equal to the
identity matrix.  The contribution of the innovation at step `h` to horizon
`T` is transported by
`transitionProduct A (h + 1) (T - (h + 1))`.

The main theorem proves the finite-sum identity by induction on `T`.  The
scope is algebraic: no rank, positive-definiteness characterization,
transition-product stability result, SDE, empirical estimator, or biological
interpretation is claimed here.
-/

namespace NoeticDiffusion

noncomputable section

open scoped BigOperators Matrix

variable {n : Type*} [Fintype n]

local instance : DecidableEq n := Classical.decEq n

/-! ## Transition products and Gramian terms -/

/-- A transition product of the specified length, ordered from old to new. -/
def transitionProduct (A : ℕ → Matrix n n ℝ) (start : ℕ) : ℕ → Matrix n n ℝ
  | 0 => 1
  | Nat.succ k => A (start + k) * transitionProduct A start k

@[simp] theorem transitionProduct_zero (A : ℕ → Matrix n n ℝ) (start : ℕ) :
    transitionProduct A start 0 = 1 := rfl

@[simp] theorem transitionProduct_succ (A : ℕ → Matrix n n ℝ)
    (start k : ℕ) :
    transitionProduct A start (Nat.succ k) =
      A (start + k) * transitionProduct A start k := rfl

/-- The transported contribution of innovation step `h` at horizon `T`. -/
def timeVaryingGramianTerm (A Q : ℕ → Matrix n n ℝ) (T h : ℕ) :
    Matrix n n ℝ :=
  let P := transitionProduct A (h + 1) (T - (h + 1))
  P * Q h * P.transpose

/-- The finite-horizon time-varying covariance Gramian. -/
def timeVaryingGramian (A Q : ℕ → Matrix n n ℝ) (T : ℕ) : Matrix n n ℝ :=
  ∑ h ∈ Finset.range T, timeVaryingGramianTerm A Q T h

private lemma transitionProduct_succ_horizon
    (A : ℕ → Matrix n n ℝ) (T h : ℕ) (hh : h < T) :
    transitionProduct A (h + 1) (Nat.succ T - (h + 1)) =
      A T * transitionProduct A (h + 1) (T - (h + 1)) := by
  have hsub : Nat.succ T - (h + 1) =
      Nat.succ (T - (h + 1)) := by
    omega
  rw [hsub, transitionProduct_succ]
  have hle : h + 1 ≤ T := by omega
  rw [Nat.add_sub_of_le hle]

private lemma timeVaryingGramianTerm_succ
    (A Q : ℕ → Matrix n n ℝ) (T h : ℕ) (hh : h < T) :
    timeVaryingGramianTerm A Q (Nat.succ T) h =
      A T * timeVaryingGramianTerm A Q T h * (A T).transpose := by
  unfold timeVaryingGramianTerm
  rw [transitionProduct_succ_horizon A T h hh]
  simp only [Matrix.transpose_mul]
  simp [Matrix.mul_assoc]

private lemma timeVaryingGramianTerm_last
    (A Q : ℕ → Matrix n n ℝ) (T : ℕ) :
    timeVaryingGramianTerm A Q (Nat.succ T) T = Q T := by
  unfold timeVaryingGramianTerm
  simp

private lemma timeVaryingGramian_sum_succ
    (A Q : ℕ → Matrix n n ℝ) (T : ℕ) :
    (∑ h ∈ Finset.range T,
        timeVaryingGramianTerm A Q (Nat.succ T) h) =
      A T * (∑ h ∈ Finset.range T, timeVaryingGramianTerm A Q T h) *
        (A T).transpose := by
  calc
    (∑ h ∈ Finset.range T,
        timeVaryingGramianTerm A Q (Nat.succ T) h) =
        ∑ h ∈ Finset.range T,
          A T * timeVaryingGramianTerm A Q T h * (A T).transpose := by
            apply Finset.sum_congr rfl
            intro h hh
            exact timeVaryingGramianTerm_succ A Q T h
              (Finset.mem_range.mp hh)
    _ = A T * (∑ h ∈ Finset.range T,
          timeVaryingGramianTerm A Q T h) * (A T).transpose := by
            simp [Finset.mul_sum, Finset.sum_mul, Matrix.mul_assoc]

/-! ## Closed-form theorem -/

/--
The time-varying covariance recurrence equals its explicit transition-product
Gramian sum.

The empty horizon is zero.  At successor horizon `T + 1`, every earlier
innovation contribution acquires the left factor `A T` and the right factor
`(A T)ᵀ`, while the new innovation contributes `Q T`.
-/
theorem covarianceTimeVarying_eq_timeVaryingGramian
    (A Q : ℕ → Matrix n n ℝ) (T : ℕ) :
    covarianceTimeVarying A Q T = timeVaryingGramian A Q T := by
  induction T with
  | zero =>
      simp [covarianceTimeVarying, timeVaryingGramian]
  | succ T ih =>
      rw [covarianceTimeVarying_succ, ih]
      unfold timeVaryingGramian
      rw [Finset.sum_range_succ, timeVaryingGramian_sum_succ,
        timeVaryingGramianTerm_last]
      simp [covStep]

end

end NoeticDiffusion
