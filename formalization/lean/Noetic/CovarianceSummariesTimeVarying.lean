import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.LinearAlgebra.Matrix.Notation
import Noetic.Covariance
import Noetic.StochasticCovarianceTimeVarying
import Noetic.FuturesNonEquivalence

/-!
# L16 follow-ups: time-varying Loewner monotonicity, orthogonal `PosDef` gauge, a
calibration/specificity witness, and the optional W6 stage-label witness

NDT source: `articles/compendium/Noetic Diffusion Theory Compendium.typ`, the same
"PRIMARY CONE METRICS" / "INTERPRETATION DISCIPLINE" material as
`Noetic/CovarianceSummaries.lean` (L16), now carried over to the time-varying
covariance `covarianceTimeVarying` from `Noetic/StochasticCovarianceTimeVarying.lean`;
`project/lean/fable_ideas/06_reachability_summaries_and_gauge.md` item 3
("time-varying versions"); and the W6 optional item of
`project/lean/fable_ideas/03_futures_layer_nonequivalences.md`.

This module closes four small follow-ups left open by the round-2 L16 and L14
gates:

* **Time-varying Loewner monotonicity in `Q`.** `covarianceTimeVarying_mono_Q`
  mirrors `covariance_mono_Q` exactly, by induction on the horizon, for a
  step-indexed innovation covariance pair `Q1 h`, `Q2 h`.
* **Time-varying horizon increment.** For *fixed* `A`, `covariance_succ_sub_posSemidef`
  in `Noetic.Covariance` shows `covariance A Q (h+1) - covariance A Q h` is PSD, i.e.
  the covariance only grows with the horizon. For *time-varying* `A h` this naive
  statement is false: `Σ_{T+1} = A_T Σ_T A_Tᵀ + Q_T` need not dominate `Σ_T` in the
  Loewner order, because `A_T Σ_T A_Tᵀ` can be *smaller* than `Σ_T` (a contraction
  step) even though `Q_T` is added. The correct statement that *does* hold for
  time-varying `A` is the innovation increment alone:
  `covarianceTimeVarying_innovation_increment_posSemidef` proves
  `(covarianceTimeVarying A Q (T+1) - A T * covarianceTimeVarying A Q T * (A T)ᵀ).PosSemidef`,
  which is immediate from the recursion (`covStep`) and `hQ T` and needs no
  algebra beyond that. `covarianceTimeVarying_horizon_not_mono` then gives the
  promised `Fin 1` counterexample to the naive horizon-monotonicity statement:
  with `A h = (1/2) • 1` for every `h` and `Q h = 1` at `h = 0`, `0` elsewhere,
  `Σ_1 = 1` but `Σ_2 = 1/4`, so `Σ_2 - Σ_1 = -3/4 • 1` is not positive
  semidefinite. The fixed-transition case escapes this failure exactly because
  `covariance_succ_sub_posSemidef` isolates the *added* Gramian term
  `A^h * Q * (A^h)ᵀ`, which is manifestly PSD; the time-varying recursion does
  not have a single fixed `A` to run that argument on the *old* horizon's worth
  of accumulated covariance, only on the newest step.
* **Orthogonal `PosDef` gauge.** `orthogonalConj_posDef_iff` proves
  `(Uᵀ * M * U).PosDef ↔ M.PosDef` for `Uᵀ * U = 1` (companion to
  `Noetic.CovarianceSummaries`'s `orthogonalConj_trace`/`orthogonalConj_det`/
  `orthogonalConj_charpoly`, which do not by themselves give a `PosDef`
  criterion). `orthogonalConj_posSemidef` is the unconditional one-directional
  fact that any conjugation `Uᵀ * M * U` (no orthogonality needed) preserves
  `PosSemidef`.
* **Calibration without specificity.** `L16_calibration_without_specificity` is a
  `Fin 2` witness that trace and determinant (the two most common scalar
  "cone size" calibration summaries) can agree on genuinely different matrices
  that disagree sharply in one specific direction: `diag(4,1)` and `diag(1,4)`
  have equal trace (`5`) and equal determinant (`4`) but differ as matrices and
  give different values `e_1 ⬝ᵥ (M *ᵥ e_1)` (`4` vs `1`) along the first
  coordinate direction. Scalar summaries calibrated to match do not certify
  directional (per-coordinate) agreement.
* **Optional W6 (stage labels are not committor truth).** Two `Fin 3` absorbing
  chains sharing the identical self-loop probability at `mid` (hence identical
  one-step "occupancy" `(P^1) mid mid = 1/2`, matching the idea file's stated
  W6 witness) but with different exit splits (`1/4 : 1/4` vs `3/8 : 1/8`) give
  different committor values at `mid` (`1/2` vs `1/4`). Reuses
  `Noetic.FuturesNonEquivalence`'s `L14_IsCommittorVec` predicate; no new
  committor definition is introduced.

## Claim boundary

All results are finite matrix algebra on `covarianceTimeVarying` (already
defined in `Noetic.StochasticCovarianceTimeVarying`) or on explicit finite
matrices/chains. No estimator, no `ε`-regularization, no probability coverage,
no stability, and no empirical-reachability claim is added.
`covarianceTimeVarying_horizon_not_mono` is a genuine counterexample to a
*stronger* statement than what is proved elsewhere in this project: it is
recorded here precisely so that no future module states unconditional
time-varying horizon monotonicity. `L16_calibration_without_specificity` is a
finite witness about two named `2 × 2` diagonal matrices; it does not claim
that trace/determinant calibration is generally insufficient for every
possible use of those summaries, only that matching them does not force
matrix equality or per-direction agreement. The W6 witness is a finite toy
absorbing chain pair; it certifies a logical non-implication between "same
one-step self-transition probability" and "same committor value", not that any
specific empirical stage-labelling scheme is wrong, and makes no uniqueness
claim about committors (uniqueness for absorbing finite chains is a separate
result, matching the boundary already stated in `Noetic.FuturesNonEquivalence`).
-/

namespace NoeticDiffusion

open scoped Matrix

variable {n : Type*} [Fintype n]

/-- Local proof-carrying decidability instance for this module's matrix
identity statements, matching the pattern used in `Noetic.CovarianceSummaries`
and `Noetic.CovarianceLicensing`. -/
noncomputable local instance covarianceSummariesTimeVaryingDecidableEq : DecidableEq n :=
  Classical.decEq n

/-! ## Time-varying Loewner monotonicity in `Q` -/

/-- Time-varying analogue of `Noetic.CovarianceSummaries.covariance_mono_Q`: if
the step-indexed innovation covariance `Q2 h` dominates `Q1 h` in the Loewner
order at every step `h`, the time-varying covariance inherits the same order at
every horizon `T`. Proved by induction on `T`, exactly mirroring the
fixed-transition proof with `A` replaced by `A T` at each step. -/
theorem covarianceTimeVarying_mono_Q (A Q1 Q2 : ℕ → Matrix n n ℝ)
    (hQ : ∀ h, (Q2 h - Q1 h).PosSemidef) (T : ℕ) :
    (covarianceTimeVarying A Q2 T - covarianceTimeVarying A Q1 T).PosSemidef := by
  induction T with
  | zero => simpa using Matrix.PosSemidef.zero
  | succ T ih =>
      have hstep : covarianceTimeVarying A Q2 (T + 1) - covarianceTimeVarying A Q1 (T + 1)
          = A T * (covarianceTimeVarying A Q2 T - covarianceTimeVarying A Q1 T) * (A T)ᴴ
              + (Q2 T - Q1 T) := by
        simp only [covarianceTimeVarying_succ, covStep, Matrix.mul_sub, Matrix.sub_mul]
        abel
      rw [hstep]
      exact (ih.mul_mul_conjTranspose_same (A T)).add (hQ T)

/-! ## Time-varying horizon increment: correct statement and a counterexample
to the naive one -/

/-- The correct time-varying horizon-increment fact: the *innovation*
increment alone is positive semidefinite, for any positive-semidefinite
step-indexed `Q`. This is immediate from `covStep`; unlike the fixed-transition
case (`Noetic.Covariance.covariance_succ_sub_posSemidef`), the plain difference
`covarianceTimeVarying A Q (T+1) - covarianceTimeVarying A Q T` need **not** be
positive semidefinite when `A` varies with the step — see
`covarianceTimeVarying_horizon_not_mono` below for an explicit `Fin 1`
counterexample. -/
theorem covarianceTimeVarying_innovation_increment_posSemidef
    (A Q : ℕ → Matrix n n ℝ) (hQ : ∀ h, (Q h).PosSemidef) (T : ℕ) :
    (covarianceTimeVarying A Q (T + 1) - A T * covarianceTimeVarying A Q T * (A T)ᵀ).PosSemidef := by
  have heq : covarianceTimeVarying A Q (T + 1) - A T * covarianceTimeVarying A Q T * (A T)ᵀ
      = Q T := by
    simp only [covarianceTimeVarying_succ, covStep, real_conjTranspose]
    abel
  rw [heq]
  exact hQ T

/-- Constant transition sequence `A h = (1/2) • 1` on `Fin 1`, used for the
horizon-non-monotonicity counterexample. -/
private noncomputable def L16_ctrA : ℕ → Matrix (Fin 1) (Fin 1) ℝ :=
  fun _ => ((1 : ℝ) / 2) • (1 : Matrix (Fin 1) (Fin 1) ℝ)

/-- Step-indexed innovation covariance on `Fin 1`: `1` at step `0`, `0`
otherwise, used for the horizon-non-monotonicity counterexample. -/
private noncomputable def L16_ctrQ : ℕ → Matrix (Fin 1) (Fin 1) ℝ :=
  fun h => if h = 0 then (1 : Matrix (Fin 1) (Fin 1) ℝ) else 0

private lemma L16_ctrQ_zero : L16_ctrQ 0 = 1 := by simp [L16_ctrQ]

private lemma L16_ctrQ_one : L16_ctrQ 1 = 0 := by simp [L16_ctrQ]

private lemma L16_ctr_sigma1 :
    covarianceTimeVarying L16_ctrA L16_ctrQ 1 = (1 : Matrix (Fin 1) (Fin 1) ℝ) := by
  simp [covarianceTimeVarying_succ, covarianceTimeVarying_zero, covStep, L16_ctrQ_zero]

private lemma L16_ctr_sigma2 :
    covarianceTimeVarying L16_ctrA L16_ctrQ 2
      = ((1 : ℝ) / 4) • (1 : Matrix (Fin 1) (Fin 1) ℝ) := by
  have hstep : covarianceTimeVarying L16_ctrA L16_ctrQ 2
      = covStep (L16_ctrA 1) (covarianceTimeVarying L16_ctrA L16_ctrQ 1) (L16_ctrQ 1) := by
    simp only [show (2 : ℕ) = 1 + 1 from rfl, covarianceTimeVarying_succ]
  have hmul : (((1 : ℝ) / 2) • (1 : Matrix (Fin 1) (Fin 1) ℝ))
      * (((1 : ℝ) / 2) • (1 : Matrix (Fin 1) (Fin 1) ℝ))
      = (((1 : ℝ) / 2) ^ 2) • ((1 : Matrix (Fin 1) (Fin 1) ℝ) * 1) := by
    rw [smul_mul_assoc, mul_smul_comm, smul_smul, sq]
  rw [hstep, L16_ctr_sigma1, L16_ctrQ_one]
  unfold covStep L16_ctrA
  rw [add_zero, real_conjTranspose, Matrix.transpose_smul, Matrix.transpose_one, Matrix.mul_one,
    hmul, Matrix.one_mul]
  congr 1
  norm_num

/-- Counterexample to the naive time-varying horizon monotonicity: with
`A h = (1/2) • 1` at every step and `Q 0 = 1`, `Q h = 0` for `h ≠ 0` on `Fin 1`,
`covarianceTimeVarying A Q 1 = 1` but `covarianceTimeVarying A Q 2 = 1/4`, so the
difference `Σ_2 - Σ_1 = -3/4` fails to be positive semidefinite. This is the
promised failure of the statement
`(covarianceTimeVarying A Q (T+1) - covarianceTimeVarying A Q T).PosSemidef`
once `A` is allowed to vary with the step: the contraction `A_1 = 1/2` shrinks
the propagated covariance faster than the (here zero) new innovation `Q_1`
can compensate. -/
theorem covarianceTimeVarying_horizon_not_mono :
    ¬ (covarianceTimeVarying L16_ctrA L16_ctrQ 2
        - covarianceTimeVarying L16_ctrA L16_ctrQ 1).PosSemidef := by
  rw [L16_ctr_sigma1, L16_ctr_sigma2]
  intro h
  have htr := h.trace_nonneg
  rw [Matrix.trace_sub, Matrix.trace_smul, Matrix.trace_one] at htr
  simp only [Fintype.card_fin] at htr
  norm_num at htr

/-! ## Orthogonal `PosDef` gauge -/

/-- Helper direction: conjugating a `PosDef` matrix by `V` with `Vᵀ * V = 1`
gives a `PosDef` matrix. Uses `Matrix.PosDef.conjTranspose_mul_mul_same` with
injectivity of `V.mulVec` derived directly from `Vᵀ * V = 1`. -/
private lemma orthogonalConj_posDef_of_posDef {V X : Matrix n n ℝ}
    (hX : X.PosDef) (hV : Vᵀ * V = 1) : (Vᵀ * X * V).PosDef := by
  have hinj : Function.Injective (Matrix.mulVec V) := by
    intro x y hxy
    have h : Vᵀ *ᵥ V *ᵥ x = Vᵀ *ᵥ V *ᵥ y := by rw [hxy]
    rwa [Matrix.mulVec_mulVec, Matrix.mulVec_mulVec, hV, Matrix.one_mulVec,
      Matrix.one_mulVec] at h
  have h := hX.conjTranspose_mul_mul_same hinj
  simpa [real_conjTranspose] using h

/-- Orthogonal conjugation `Uᵀ * M * U` (for `Uᵀ * U = 1`) preserves and
reflects positive definiteness: `(Uᵀ * M * U).PosDef ↔ M.PosDef`. The forward
direction is `orthogonalConj_posDef_of_posDef`; the converse applies the same
helper to `V := Uᵀ` (using `Matrix.mul_eq_one_comm` to get `U * Uᵀ = 1`) and
cancels the resulting `U * Uᵀ` factors. Companion to
`Noetic.CovarianceSummaries.orthogonalConj_trace` / `orthogonalConj_det` /
`orthogonalConj_charpoly`, which do not by themselves give a `PosDef`
criterion. -/
theorem orthogonalConj_posDef_iff {U M : Matrix n n ℝ} (hU : Uᵀ * U = 1) :
    (Uᵀ * M * U).PosDef ↔ M.PosDef := by
  have hUU : U * Uᵀ = 1 := Matrix.mul_eq_one_comm.mp hU
  constructor
  · intro hPD
    have hV : (Uᵀ)ᵀ * Uᵀ = 1 := by rw [Matrix.transpose_transpose]; exact hUU
    have hfwd := orthogonalConj_posDef_of_posDef hPD hV
    have hcancel : (Uᵀ)ᵀ * (Uᵀ * M * U) * Uᵀ = M := by
      rw [Matrix.transpose_transpose]
      have hassoc : U * (Uᵀ * M * U) * Uᵀ = (U * Uᵀ) * M * (U * Uᵀ) := by
        simp only [Matrix.mul_assoc]
      rw [hassoc, hUU, Matrix.one_mul, Matrix.mul_one]
    rwa [hcancel] at hfwd
  · exact fun hM => orthogonalConj_posDef_of_posDef hM hU

/-- Any conjugation `Uᵀ * M * U` preserves positive semidefiniteness — no
orthogonality hypothesis on `U` is needed, unlike `orthogonalConj_posDef_iff`.
Direct instance of `Matrix.PosSemidef.conjTranspose_mul_mul_same` together with
`real_conjTranspose`. -/
theorem orthogonalConj_posSemidef {U M : Matrix n n ℝ} (hM : M.PosSemidef) :
    (Uᵀ * M * U).PosSemidef := by
  have h := hM.conjTranspose_mul_mul_same U
  simpa [real_conjTranspose] using h

/-! ## Calibration without specificity -/

/-- The first diagonal calibration witness on `Fin 2`: `diag(4, 1)`. -/
private noncomputable def L16_diag41 : Matrix (Fin 2) (Fin 2) ℝ :=
  Matrix.diagonal (![4, 1] : Fin 2 → ℝ)

/-- The second diagonal calibration witness on `Fin 2`: `diag(1, 4)`. -/
private noncomputable def L16_diag14 : Matrix (Fin 2) (Fin 2) ℝ :=
  Matrix.diagonal (![1, 4] : Fin 2 → ℝ)

/-- Calibration without specificity: `diag(4,1)` and `diag(1,4)` on `Fin 2`
have equal trace (`5`) and equal determinant (`4`), so two of the most common
scalar "cone size" summaries agree, yet the matrices are different and the
directional value `e_1 ⬝ᵥ (M *ᵥ e_1)` along the first coordinate direction
disagrees sharply (`4` vs `1`). Matching scalar calibration summaries does not
certify per-direction (specific) agreement. -/
theorem L16_calibration_without_specificity :
    Matrix.trace L16_diag41 = Matrix.trace L16_diag14 ∧
    Matrix.det L16_diag41 = Matrix.det L16_diag14 ∧
    L16_diag41 ≠ L16_diag14 ∧
    (![1, 0] : Fin 2 → ℝ) ⬝ᵥ (L16_diag41 *ᵥ (![1, 0] : Fin 2 → ℝ))
      ≠ (![1, 0] : Fin 2 → ℝ) ⬝ᵥ (L16_diag14 *ᵥ (![1, 0] : Fin 2 → ℝ)) := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · simp only [L16_diag41, L16_diag14, Matrix.trace_diagonal, Fin.sum_univ_two,
      Matrix.cons_val_zero, Matrix.cons_val_one]
    norm_num
  · simp [L16_diag41, L16_diag14, Matrix.det_diagonal, Fin.prod_univ_two]
  · intro h
    have hc : L16_diag41 0 0 = L16_diag14 0 0 := congrArg (fun M => M 0 0) h
    simp [L16_diag41, L16_diag14, Matrix.diagonal_apply_eq] at hc
  · simp [L16_diag41, L16_diag14, Matrix.mulVec_diagonal, dotProduct, Fin.sum_univ_two]

/-! ## Optional W6 — stage labels are not committor truth (equal self-loop
occupancy, different committor) -/

/-- Occupancy of state `j` from state `i` after `h` steps under a
row-stochastic matrix `P`: the `(i, j)` entry of `P ^ h`. -/
def L14_W6_occupancy {m : Type*} [Fintype m] [DecidableEq m] (P : Matrix m m ℝ)
    (h : ℕ) (i j : m) : ℝ :=
  (P ^ h) i j

/-- The first `Fin 3` absorbing chain `{A = 0, mid = 1, B = 2}`: from `mid`,
the chain self-loops with probability `1/2` and otherwise exits evenly
(`1/4` to each of `A`, `B`). -/
noncomputable def L14_W6_Chain1 : Matrix (Fin 3) (Fin 3) ℝ :=
  Matrix.of ![![1, 0, 0], ![1 / 4, 1 / 2, 1 / 4], ![0, 0, 1]]

/-- The second `Fin 3` absorbing chain on the same states: from `mid`, the
same `1/2` self-loop probability, but an uneven exit split (`3/8` to `A`,
`1/8` to `B`). -/
noncomputable def L14_W6_Chain2 : Matrix (Fin 3) (Fin 3) ℝ :=
  Matrix.of ![![1, 0, 0], ![3 / 8, 1 / 2, 1 / 8], ![0, 0, 1]]

/-- The committor vector for `L14_W6_Chain1`: `q(mid) = 1/2`, from solving the
harmonic equation `q(mid) = 1/4 * 0 + 1/2 * q(mid) + 1/4 * 1`. -/
noncomputable def L14_W6_q1 : Fin 3 → ℝ := ![0, 1 / 2, 1]

/-- The committor vector for `L14_W6_Chain2`: `q(mid) = 1/4`, from solving the
harmonic equation `q(mid) = 3/8 * 0 + 1/2 * q(mid) + 1/8 * 1`. -/
noncomputable def L14_W6_q2 : Fin 3 → ℝ := ![0, 1 / 4, 1]

theorem L14_W6_Chain1_isCommittorVec :
    L14_IsCommittorVec L14_W6_Chain1 0 2 L14_W6_q1 := by
  refine ⟨by simp [L14_W6_q1], by simp [L14_W6_q1], ?_⟩
  intro i hA hB
  fin_cases i
  · exact absurd rfl hA
  · norm_num [L14_W6_Chain1, L14_W6_q1, Matrix.of_apply, Fin.sum_univ_succ, Fin.sum_univ_zero]
  · exact absurd rfl hB

theorem L14_W6_Chain2_isCommittorVec :
    L14_IsCommittorVec L14_W6_Chain2 0 2 L14_W6_q2 := by
  refine ⟨by simp [L14_W6_q2], by simp [L14_W6_q2], ?_⟩
  intro i hA hB
  fin_cases i
  · exact absurd rfl hA
  · norm_num [L14_W6_Chain2, L14_W6_q2, Matrix.of_apply, Fin.sum_univ_succ, Fin.sum_univ_zero]
  · exact absurd rfl hB

/-- The two chains share the identical one-step self-loop probability at
`mid`: `(P^1) mid mid = 1/2` for both, matching the idea file's stated W6
witness ("same self-loop 1/2"). -/
theorem L14_W6_occupancy_mid_mid_eq :
    L14_W6_occupancy L14_W6_Chain1 1 1 1 = L14_W6_occupancy L14_W6_Chain2 1 1 1 := by
  simp only [L14_W6_occupancy, pow_one]
  norm_num [L14_W6_Chain1, L14_W6_Chain2, Matrix.of_apply]

theorem L14_W6_committor_ne : L14_W6_q1 1 ≠ L14_W6_q2 1 := by
  norm_num [L14_W6_q1, L14_W6_q2]

/-- W6: two absorbing `Fin 3` chains with identical one-step self-loop
occupancy at `mid` (`(P^1) mid mid = 1/2` for both) but different committor
values there (`1/2` vs `1/4`). Stage-level self-transition frequency does not
determine committor truth. -/
theorem L14_W6_same_occupancy_diff_committor :
    L14_IsCommittorVec L14_W6_Chain1 0 2 L14_W6_q1 ∧
    L14_IsCommittorVec L14_W6_Chain2 0 2 L14_W6_q2 ∧
    L14_W6_occupancy L14_W6_Chain1 1 1 1 = L14_W6_occupancy L14_W6_Chain2 1 1 1 ∧
    L14_W6_q1 1 ≠ L14_W6_q2 1 :=
  ⟨L14_W6_Chain1_isCommittorVec, L14_W6_Chain2_isCommittorVec, L14_W6_occupancy_mid_mid_eq,
    L14_W6_committor_ne⟩

end NoeticDiffusion
