import Mathlib.Probability.Moments.Covariance
import Noetic.Covariance

/-!
# Concrete one-step stochastic covariance propagation

This module instantiates the one-step covariance calculation with Mathlib's
scalar `ProbabilityTheory.covariance`.  A random vector is represented by a
finite family of real-valued random variables `X : n → Ω → ℝ`; this keeps the
probabilistic assumptions coordinatewise and avoids introducing a separate
matrix-valued covariance interface.

The source model is the compendium's local stochastic linearization
`x_(t+1) = A x_t + b + ε` and its covariance recursion
`Σ_(t+1) = A Σ_t Aᵀ + Q` (Noetic Diffusion Theory Compendium, lines
932--935 and 945--952 at implementation time).  The theorem below is one
step only.  It assumes coordinatewise finite second moments, an innovation
covariance `Q`, and zero state--innovation cross-covariance.  The latter is
weaker than independence and is stated explicitly so the calculation does not
hide a probabilistic assumption.

The result is a stochastic derivation of the algebraic `covStep` identity.  It
does not claim an empirical MNPS result, a finite-horizon process theorem,
probability coverage, reachability, or biological interpretation.  In
particular, no zero-mean assumption is needed for centered covariance; it would
be needed for an uncentered second-moment recursion or for a mean recursion.
-/

namespace NoeticDiffusion

open MeasureTheory
open ProbabilityTheory
open scoped BigOperators Matrix ProbabilityTheory

variable {Ω n : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [Fintype n]

/-- The covariance matrix of a finite family of scalar random variables. -/
noncomputable def covMatrix (X : n → Ω → ℝ) (μ : Measure Ω) : Matrix n n ℝ :=
  fun i j => cov[X i, X j; μ]

/-- The coordinatewise linear part `A X`. -/
def linearPart (A : Matrix n n ℝ) (X : n → Ω → ℝ) (i : n) : Ω → ℝ :=
  fun ω => ∑ k, A i k * X k ω

/-- The coordinatewise affine stochastic update `A X + b + ε`. -/
def affineNoise (A : Matrix n n ℝ) (b : n → ℝ)
    (X ε : n → Ω → ℝ) (i : n) : Ω → ℝ :=
  fun ω => linearPart A X i ω + b i + ε i ω

private lemma memLp_linearPart
    [IsFiniteMeasure μ] (A : Matrix n n ℝ) (X : n → Ω → ℝ)
    (hX : ∀ i, MemLp (X i) 2 μ) (i : n) :
    MemLp (linearPart A X i) 2 μ := by
  unfold linearPart
  have hsum :=
    memLp_finset_sum' Finset.univ (fun k _ => (hX k).const_mul (A i k))
  convert hsum using 1
  ext ω
  simp

private lemma cov_linearPart_left
    [IsFiniteMeasure μ] (A : Matrix n n ℝ) (X : n → Ω → ℝ)
    (hX : ∀ i, MemLp (X i) 2 μ) (Y : Ω → ℝ) (hY : MemLp Y 2 μ)
    (i : n) :
    cov[linearPart A X i, Y; μ] =
      ∑ k, A i k * cov[X k, Y; μ] := by
  unfold linearPart
  rw [covariance_fun_sum_left (fun k => (hX k).const_mul (A i k)) hY]
  simp_rw [covariance_mul_left]

private lemma cov_linearPart_right
    [IsFiniteMeasure μ] (A : Matrix n n ℝ) (X : n → Ω → ℝ)
    (hX : ∀ i, MemLp (X i) 2 μ) (Y : Ω → ℝ) (hY : MemLp Y 2 μ)
    (i : n) :
    cov[Y, linearPart A X i; μ] =
      ∑ k, A i k * cov[Y, X k; μ] := by
  unfold linearPart
  rw [covariance_fun_sum_right (fun k => (hX k).const_mul (A i k)) hY]
  simp_rw [covariance_mul_right]

private lemma cov_linearPart_noise_zero
    [IsFiniteMeasure μ] (A : Matrix n n ℝ) (X ε : n → Ω → ℝ)
    (hX : ∀ i, MemLp (X i) 2 μ) (hε : ∀ i, MemLp (ε i) 2 μ)
    (hXε : ∀ i j, cov[X i, ε j; μ] = 0) (i j : n) :
    cov[linearPart A X i, ε j; μ] = 0 := by
  rw [cov_linearPart_left A X hX (ε j) (hε j) i]
  simp_rw [hXε]
  simp

private lemma cov_noise_linearPart_zero
    [IsFiniteMeasure μ] (A : Matrix n n ℝ) (X ε : n → Ω → ℝ)
    (hX : ∀ i, MemLp (X i) 2 μ) (hε : ∀ i, MemLp (ε i) 2 μ)
    (hXε : ∀ i j, cov[X i, ε j; μ] = 0) (i j : n) :
    cov[ε i, linearPart A X j; μ] = 0 := by
  rw [covariance_comm, cov_linearPart_left A X hX (ε i) (hε i) j]
  simp_rw [hXε]
  simp

private lemma cov_linearPart_linearPart
    [IsFiniteMeasure μ] (A : Matrix n n ℝ) (X : n → Ω → ℝ)
    (hX : ∀ i, MemLp (X i) 2 μ) (i j : n) :
    cov[linearPart A X i, linearPart A X j; μ] =
      ∑ k, ∑ l, A i k * A j l * cov[X k, X l; μ] := by
  unfold linearPart
  rw [covariance_fun_sum_fun_sum
    (fun k => (hX k).const_mul (A i k))
    (fun l => (hX l).const_mul (A j l))]
  simp_rw [covariance_mul_left, covariance_mul_right]
  apply Finset.sum_congr rfl
  intro k hk
  apply Finset.sum_congr rfl
  intro l hl
  ring

private lemma cov_affine_entry
    [IsProbabilityMeasure μ] (A : Matrix n n ℝ) (b : n → ℝ)
    (X ε : n → Ω → ℝ) (hX : ∀ i, MemLp (X i) 2 μ)
    (hε : ∀ i, MemLp (ε i) 2 μ) (i j : n) :
    cov[affineNoise A b X ε i, affineNoise A b X ε j; μ] =
      cov[linearPart A X i, linearPart A X j; μ] +
        cov[ε i, ε j; μ] +
        cov[linearPart A X i, ε j; μ] +
        cov[ε i, linearPart A X j; μ] := by
  have hLi : MemLp (linearPart A X i) 2 μ := memLp_linearPart A X hX i
  have hLj : MemLp (linearPart A X j) 2 μ := memLp_linearPart A X hX j
  have hLiεi : MemLp (fun ω => linearPart A X i ω + ε i ω) 2 μ :=
    hLi.add (hε i)
  have hLjεj : MemLp (fun ω => linearPart A X j ω + ε j ω) 2 μ :=
    hLj.add (hε j)
  calc
    cov[affineNoise A b X ε i, affineNoise A b X ε j; μ] =
        cov[fun ω => linearPart A X i ω + ε i ω,
          fun ω => linearPart A X j ω + ε j ω; μ] := by
      change cov[fun ω => (linearPart A X i ω + b i) + ε i ω,
        fun ω => (linearPart A X j ω + b j) + ε j ω; μ] = _
      rw [show (fun ω => (linearPart A X i ω + b i) + ε i ω) =
          (fun ω => linearPart A X i ω + ε i ω + b i) by
            funext ω; ring]
      rw [show (fun ω => (linearPart A X j ω + b j) + ε j ω) =
          (fun ω => linearPart A X j ω + ε j ω + b j) by
            funext ω; ring]
      rw [covariance_add_const_left (hLiεi.integrable (by norm_num)) (b i),
        covariance_add_const_right (hLjεj.integrable (by norm_num)) (b j)]
    _ = (cov[linearPart A X i, linearPart A X j; μ] +
          cov[linearPart A X i, ε j; μ]) +
        (cov[ε i, linearPart A X j; μ] + cov[ε i, ε j; μ]) := by
      have hleft :
          cov[fun ω => linearPart A X i ω + ε i ω,
            fun ω => linearPart A X j ω + ε j ω; μ] =
            cov[linearPart A X i, fun ω => linearPart A X j ω + ε j ω; μ] +
              cov[ε i, fun ω => linearPart A X j ω + ε j ω; μ] := by
        simpa only [Pi.add_apply] using
          (covariance_add_left hLi (hε i) hLjεj)
      have hrightL :
          cov[linearPart A X i, fun ω => linearPart A X j ω + ε j ω; μ] =
            cov[linearPart A X i, linearPart A X j; μ] +
              cov[linearPart A X i, ε j; μ] := by
        simpa only [Pi.add_apply] using
          (covariance_add_right hLi hLj (hε j))
      have hrightE :
          cov[ε i, fun ω => linearPart A X j ω + ε j ω; μ] =
            cov[ε i, linearPart A X j; μ] + cov[ε i, ε j; μ] := by
        simpa only [Pi.add_apply] using
          (covariance_add_right (hε i) hLj (hε j))
      rw [hleft, hrightL, hrightE]
    _ = cov[linearPart A X i, linearPart A X j; μ] +
        cov[ε i, ε j; μ] +
        cov[linearPart A X i, ε j; μ] +
        cov[ε i, linearPart A X j; μ] := by ring

/--
The concrete one-step covariance rule for `x_next = A x + b + ε`.

All covariance symbols in the statement are Mathlib's scalar covariance,
assembled entrywise into a finite matrix.  The cross-covariance hypothesis is
coordinatewise; the reverse orientation is obtained from covariance symmetry.
-/
theorem covMatrix_affineNoise
    [IsProbabilityMeasure μ] (A : Matrix n n ℝ) (b : n → ℝ)
    (X ε : n → Ω → ℝ) (Q : Matrix n n ℝ)
    (hX : ∀ i, MemLp (X i) 2 μ)
    (hε : ∀ i, MemLp (ε i) 2 μ)
    (hεcov : covMatrix ε μ = Q)
    (hXε : ∀ i j, cov[X i, ε j; μ] = 0) :
    covMatrix (affineNoise A b X ε) μ =
      A * covMatrix X μ * A.transpose + Q := by
  ext i j
  change cov[affineNoise A b X ε i, affineNoise A b X ε j; μ] =
    (A * covMatrix X μ * A.transpose + Q) i j
  have hentry := cov_affine_entry A b X ε hX hε i j
  have hεcovij : cov[ε i, ε j; μ] = Q i j := by
    exact congrFun (congrFun hεcov i) j
  rw [hentry, cov_linearPart_linearPart A X hX i j,
    hεcovij]
  simp_rw [cov_linearPart_noise_zero A X ε hX hε hXε,
    cov_noise_linearPart_zero A X ε hX hε hXε]
  simp only [add_zero]
  simp only [covMatrix, Matrix.add_apply, Matrix.mul_apply, Matrix.transpose_apply]
  rw [Finset.sum_comm]
  congr 1
  simp_rw [Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro k hk
  apply Finset.sum_congr rfl
  intro l hl
  ring

end NoeticDiffusion
