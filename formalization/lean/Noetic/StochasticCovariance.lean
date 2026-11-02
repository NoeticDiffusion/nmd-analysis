import Noetic.Covariance

/-!
# L3a: abstract one-step covariance propagation

The NDT compendium gives the local discrete model

```text
x_(t + 1) = A_t x_t + b_t + epsilon_t
Sigma_t^(h + 1) = A_t Sigma_t^(h) A_t^top + W_(Q,t).
```

The source equations are `Noetic Diffusion Theory Compendium.typ`,
`eq:compendium-reachability-model` (lines 932--935) and
`eq:compendium-reachability-recursion` (lines 945--952).

This file makes the algebraic adapter step explicit.  A
`StochasticCovarianceInterface` is a named interface for finite-dimensional
random vectors: it supplies a finite-second-moment predicate, covariance and
cross-covariance maps, and the standard covariance laws needed below.  Its
fields are assumptions supplied by a concrete probability model; they are not
project axioms.  No probability-space implementation is claimed in this
abstract module; the concrete `Measure`/`MemLp` instantiation is in
`Noetic/StochasticCovarianceConcrete.lean`.

The main theorem uses deterministic `A` and `b`, finite second moments for the
state and innovation, `Cov epsilon = Q`, and zero state--innovation
cross-covariance in both orientations.  Independence is a sufficient way to
establish the latter condition in a concrete model, but is not needed by the
algebraic proof.  The theorem establishes the abstract one-step covariance
propagation; it does not establish an empirical MNPS claim, probability
coverage, or a
biological interpretation.  Those claim boundaries are the same as in the
Lean README and the preceding covariance module.
-/

namespace NoeticDiffusion

open scoped Matrix

variable {Ω n : Type*} [Fintype n]

/-- A finite-dimensional random vector represented by its sample-wise values. -/
abbrev RandomVector (Ω n : Type*) := Ω → n → ℝ

/-- A deterministic vector lifted to a random vector. -/
def constantVector (b : n → ℝ) : RandomVector Ω n :=
  fun _ => b

/-- The deterministic linear image of a random vector. -/
def linearImage (A : Matrix n n ℝ) (X : RandomVector Ω n) : RandomVector Ω n :=
  fun ω => A *ᵥ X ω

/-- The affine discrete stochastic update from the compendium model. -/
def stochasticLinearStep (A : Matrix n n ℝ) (b : n → ℝ)
    (X ε : RandomVector Ω n) : RandomVector Ω n :=
  fun ω => linearImage A X ω + constantVector b ω + ε ω

/-!
## Explicit algebraic stochastic interface

The interface separates the probabilistic input from the theorem.  A concrete
probability-space construction can instantiate `finiteSecondMoment`,
`covariance`, and `crossCovariance` and prove these fields from expectations.
The laws are stated as structure fields so their assumptions remain visible at
each use site; this file does not declare any `axiom`.
-/

structure StochasticCovarianceInterface (Ω n : Type*) [Fintype n] where
  /-- The supplied finite-second-moment predicate for random vectors. -/
  finiteSecondMoment : RandomVector Ω n → Prop
  /-- Matrix covariance of a random vector. -/
  covariance : RandomVector Ω n → Matrix n n ℝ
  /-- Matrix cross-covariance, in the two displayed argument orientations. -/
  crossCovariance : RandomVector Ω n → RandomVector Ω n → Matrix n n ℝ
  /-- Finite second moments are closed under adding random vectors. -/
  finiteSecondMoment_add :
    ∀ (X Y : RandomVector Ω n), finiteSecondMoment X → finiteSecondMoment Y →
      finiteSecondMoment (fun ω => X ω + Y ω)
  /-- Finite second moments are closed under deterministic linear maps. -/
  finiteSecondMoment_linear :
    ∀ (A : Matrix n n ℝ) (X : RandomVector Ω n), finiteSecondMoment X →
      finiteSecondMoment (linearImage A X)
  /-- Deterministic vectors have finite second moments. -/
  finiteSecondMoment_const : ∀ (b : n → ℝ), finiteSecondMoment (constantVector b)
  /-- A deterministic vector has zero covariance. -/
  covariance_const :
    ∀ (b : n → ℝ), covariance (constantVector b) = 0
  /-- Cross-covariance vanishes when its left argument is deterministic. -/
  crossCovariance_const_left :
    ∀ (b : n → ℝ) (X : RandomVector Ω n),
      crossCovariance (constantVector b) X = 0
  /-- Cross-covariance vanishes when its right argument is deterministic. -/
  crossCovariance_const_right :
    ∀ (X : RandomVector Ω n) (b : n → ℝ),
      crossCovariance X (constantVector b) = 0
  /-- Cross-covariance is additive in its left argument. -/
  crossCovariance_add_left :
    ∀ (X Y Z : RandomVector Ω n),
      crossCovariance (fun ω => X ω + Y ω) Z =
        crossCovariance X Z + crossCovariance Y Z
  /-- Cross-covariance is additive in its right argument. -/
  crossCovariance_add_right :
    ∀ (X Y Z : RandomVector Ω n),
      crossCovariance X (fun ω => Y ω + Z ω) =
        crossCovariance X Y + crossCovariance X Z
  /-- Covariance of a sum, with both cross terms shown explicitly. -/
  covariance_add :
    ∀ (X Y : RandomVector Ω n), finiteSecondMoment X → finiteSecondMoment Y →
      covariance (fun ω => X ω + Y ω) =
        covariance X + covariance Y + crossCovariance X Y + crossCovariance Y X
  /-- Covariance under a deterministic linear map. -/
  covariance_linear :
    ∀ (A : Matrix n n ℝ) (X : RandomVector Ω n), finiteSecondMoment X →
      covariance (linearImage A X) =
        A * covariance X * Aᴴ

/-! ## One-step covariance propagation -/

/--
From the explicit affine stochastic update

`X_next = A X + b + ε`,

finite second moments, `Cov ε = Q`, and zero state--innovation
cross-covariance imply the NDT covariance step

`Cov X_next = A * Cov X * Aᴴ + Q`.

The zero cross-covariance hypotheses are stated for the transformed state
`A X`; a concrete model may derive them from zero `Cov(X, ε)` by bilinearity,
or from independence of `X` and `ε`.
-/
theorem covariance_stochastic_linear_step
    (I : StochasticCovarianceInterface Ω n)
    (A : Matrix n n ℝ) (b : n → ℝ)
    (X ε : RandomVector Ω n) (Q : Matrix n n ℝ)
    (hX : I.finiteSecondMoment X)
    (hε : I.finiteSecondMoment ε)
    (hεcov : I.covariance ε = Q)
    (hXε : I.crossCovariance (linearImage A X) ε = 0)
    (hεX : I.crossCovariance ε (linearImage A X) = 0) :
    I.covariance (stochasticLinearStep A b X ε) =
      covStep A (I.covariance X) Q := by
  let L : RandomVector Ω n := linearImage A X
  let B : RandomVector Ω n := constantVector b
  have hL : I.finiteSecondMoment L := by
    exact I.finiteSecondMoment_linear A X hX
  have hB : I.finiteSecondMoment B := by
    exact I.finiteSecondMoment_const b
  have hLB : I.finiteSecondMoment (fun ω => L ω + B ω) := by
    exact I.finiteSecondMoment_add L B hL hB
  have hInner := I.covariance_add L B hL hB
  have hInnerReduced :
      I.covariance (fun ω => L ω + B ω) = I.covariance L := by
    calc
      I.covariance (fun ω => L ω + B ω) =
          I.covariance L + I.covariance B +
            I.crossCovariance L B + I.crossCovariance B L := hInner
      _ = I.covariance L := by
        rw [I.covariance_const b,
          I.crossCovariance_const_right L b,
          I.crossCovariance_const_left b L]
        simp
  have hCrossLeft :
      I.crossCovariance (fun ω => L ω + B ω) ε = 0 := by
    rw [I.crossCovariance_add_left L B ε]
    change I.crossCovariance (linearImage A X) ε +
      I.crossCovariance (constantVector b) ε = 0
    rw [hXε, I.crossCovariance_const_left b ε]
    simp
  have hCrossRight :
      I.crossCovariance ε (fun ω => L ω + B ω) = 0 := by
    rw [I.crossCovariance_add_right ε L B]
    change I.crossCovariance ε (linearImage A X) +
      I.crossCovariance ε (constantVector b) = 0
    rw [hεX, I.crossCovariance_const_right ε b]
    simp
  have hOuter := I.covariance_add
    (fun ω => L ω + B ω) ε hLB hε
  have hOuterReduced :
      I.covariance (fun ω => (L ω + B ω) + ε ω) =
        I.covariance (fun ω => L ω + B ω) + I.covariance ε := by
    calc
      I.covariance (fun ω => (L ω + B ω) + ε ω) =
          I.covariance (fun ω => L ω + B ω) + I.covariance ε +
            I.crossCovariance (fun ω => L ω + B ω) ε +
              I.crossCovariance ε (fun ω => L ω + B ω) := hOuter
      _ = I.covariance (fun ω => L ω + B ω) + I.covariance ε := by
        rw [hCrossLeft, hCrossRight]
        simp
  change I.covariance (fun ω => (L ω + B ω) + ε ω) = _
  calc
    I.covariance (fun ω => (L ω + B ω) + ε ω) =
        I.covariance (fun ω => L ω + B ω) + I.covariance ε := hOuterReduced
    _ = I.covariance L + I.covariance ε := by rw [hInnerReduced]
    _ = A * I.covariance X * Aᴴ + Q := by
      rw [show I.covariance L = I.covariance (linearImage A X) by rfl,
        I.covariance_linear A X hX, hεcov]
    _ = covStep A (I.covariance X) Q := by rfl

/-- The same propagation identity with the ordinary transpose notation used
in the compendium.  Over `ℝ`, this is definitionally the same real matrix
identity as `covariance_stochastic_linear_step` after `real_conjTranspose`. -/
theorem covariance_stochastic_linear_step_transpose
    (I : StochasticCovarianceInterface Ω n)
    (A : Matrix n n ℝ) (b : n → ℝ)
    (X ε : RandomVector Ω n) (Q : Matrix n n ℝ)
    (hX : I.finiteSecondMoment X)
    (hε : I.finiteSecondMoment ε)
    (hεcov : I.covariance ε = Q)
    (hXε : I.crossCovariance (linearImage A X) ε = 0)
    (hεX : I.crossCovariance ε (linearImage A X) = 0) :
    I.covariance (stochasticLinearStep A b X ε) =
      A * I.covariance X * A.transpose + Q := by
  simpa [covStep, real_conjTranspose] using
    (covariance_stochastic_linear_step I A b X ε Q hX hε hεcov hXε hεX)

end NoeticDiffusion
