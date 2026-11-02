import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.LinearAlgebra.Matrix.Charpoly.Basic
import Mathlib.LinearAlgebra.Matrix.SemiringInverse
import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.Algebra.Order.Chebyshev
import Noetic.Covariance
import Noetic.CovarianceLicensing

/-!
# L16: predictive-spread summaries — Loewner monotonicity, gauge invariance, `dEff`

NDT source: `articles/compendium/Noetic Diffusion Theory Compendium.typ`, compact
summary §5 "PRIMARY CONE METRICS" / "SECONDARY CONE METRICS" / "INTERPRETATION
DISCIPLINE" (manuscript v2 lines 583--588 gauge, 596--623 "large `Q_t` inflates
cones without implying richer controllable geometry", 610--614 eigenvalue
summaries); `project/lean/fable_ideas/06_reachability_summaries_and_gauge.md`.

This module adds three families of exact algebraic facts about the
fixed-transition finite-horizon covariance `covariance` already defined in
`Noetic/Covariance.lean`, plus a scalar effective-dimension summary
`dEff Σ := (trace Σ)^2 / trace (Σ * Σ)` (written `M`/`M1`/`M2` in the Lean
statements below, since `Σ` is a reserved token and cannot be used as an
identifier in this toolchain).

* **L16a (Loewner monotonicity).** A larger innovation covariance, in the
  Loewner order `(Q2 - Q1).PosSemidef`, can only enlarge the finite-horizon
  covariance in the same order, at every horizon and telescoped over any
  horizon increment. Trace inherits the same monotonicity. This is the exact
  content of the "large `Q_t` inflates cones" warning: a bigger predictive
  ellipsoid is not by itself evidence of richer controllable geometry.
* **L16b (orthogonal gauge invariance).** Conjugating a covariance by an
  orthogonal matrix (`Uᵀ * U = 1`) leaves trace, determinant, and
  characteristic polynomial unchanged, and pushes the whole finite-horizon
  covariance recursion through the same conjugation
  (`Uᵀ * covariance A Σ₀ h * U = covariance (Uᵀ*A*U) (Uᵀ*Σ₀*U) h`). An
  explicit `diag(2,1)` witness shows nonuniform rescaling is *not* such a
  symmetry: it changes both trace and `dEff` of the identity covariance.
* **L16c (effective dimension).** `dEff` is scale-invariant, equals
  `Fintype.card n` on the identity and `1` on a rank-one diagonal witness, and
  satisfies `1 ≤ dEff Σ ≤ Fintype.card n` for nonzero positive semidefinite
  `Σ` (upper bound is a pure finite-sum/Cauchy–Schwarz argument on entries and
  needs only symmetry; the lower bound is proved through the spectral
  theorem and needs positive semidefiniteness). Scaling laws for trace,
  determinant, and the proof-carrying `logDetOfPosDef` are included.

**Claim boundary.** All results are finite matrix algebra on the model
covariance `covariance A Q h` and on the scalar summary `dEff`. No estimator
(`Q̂`, `Â`), no `ε`-regularization (the compact summary's `κ` and `p_i`
include an `ε`; this module formalizes the `ε = 0` object and states so
explicitly), no probability coverage, and no claim that empirical cones are
gauge-fixed. The rescaling counterexample proves that a chart change alters
summaries; it does not say which chart is "right". Determinant monotonicity
under the Loewner order is **not proved** here: this Mathlib snapshot has no
ready `Matrix.PosDef.det_le_det`-type lemma, and a from-scratch proof (via
`Σ2 = Σ1^{1/2}(I + Σ1^{-1/2} D Σ1^{-1/2})Σ1^{1/2}` or eigenvalue interlacing)
was judged out of the bounded-effort budget for this gate; it is recorded
below as dropped.
-/

namespace NoeticDiffusion

open scoped Matrix

variable {n : Type*} [Fintype n]

/-- Local proof-carrying decidability instance for this module's matrix
identity/determinant/charpoly statements, matching the pattern used in
`Noetic.CovarianceLicensing`. -/
noncomputable local instance covarianceSummariesDecidableEq : DecidableEq n := Classical.decEq n

/-! ## L16a: Loewner monotonicity -/

/-- Increasing the innovation covariance in the Loewner order
(`(Q2 - Q1).PosSemidef`) can only increase the finite-horizon covariance in
the same order, at every horizon `h`. Induction on `h`, using
`covariance_succ` and `Matrix.PosSemidef.mul_mul_conjTranspose_same`. -/
theorem covariance_mono_Q (A Q1 Q2 : Matrix n n ℝ) (hQ : (Q2 - Q1).PosSemidef) (h : ℕ) :
    (covariance A Q2 h - covariance A Q1 h).PosSemidef := by
  induction h with
  | zero => simpa using Matrix.PosSemidef.zero
  | succ h ih =>
      have hstep : covariance A Q2 (h + 1) - covariance A Q1 (h + 1)
          = A * (covariance A Q2 h - covariance A Q1 h) * Aᴴ + (Q2 - Q1) := by
        simp only [covariance_succ, covStep, Matrix.mul_sub, Matrix.sub_mul]
        abel
      rw [hstep]
      exact (ih.mul_mul_conjTranspose_same A).add hQ

/-- Telescoped horizon monotonicity: the finite-horizon covariance only grows
(in the Loewner order) as the horizon increases by any amount `k`. The
one-step case is already `covariance_succ_sub_posSemidef` in
`Noetic.Covariance`; this restates the telescoped form by induction on `k`. -/
theorem covariance_horizon_mono (A Q : Matrix n n ℝ) (hQ : Q.PosSemidef) (h k : ℕ) :
    (covariance A Q (h + k) - covariance A Q h).PosSemidef := by
  induction k with
  | zero => simpa using Matrix.PosSemidef.zero
  | succ k ih =>
      have hidentity : covariance A Q (h + (k + 1)) - covariance A Q h
          = (covariance A Q (h + k + 1) - covariance A Q (h + k))
            + (covariance A Q (h + k) - covariance A Q h) := by
        rw [show h + (k + 1) = h + k + 1 from by ring]
        abel
      rw [hidentity]
      exact (covariance_succ_sub_posSemidef A Q hQ (h + k)).add ih

/-- Trace is monotone under the Loewner order: if `M2 - M1` is positive
semidefinite then `trace M1 ≤ trace M2`. Direct consequence of
`Matrix.PosSemidef.trace_nonneg` applied to the difference. -/
theorem loewner_trace_mono {M1 M2 : Matrix n n ℝ} (h : (M2 - M1).PosSemidef) :
    Matrix.trace M1 ≤ Matrix.trace M2 := by
  have ht := h.trace_nonneg
  rw [Matrix.trace_sub] at ht
  linarith

/-- Specialization of `loewner_trace_mono` to the finite-horizon covariance
under a Loewner-ordered innovation covariance pair. -/
theorem covariance_trace_mono_Q (A Q1 Q2 : Matrix n n ℝ) (hQ : (Q2 - Q1).PosSemidef) (h : ℕ) :
    Matrix.trace (covariance A Q1 h) ≤ Matrix.trace (covariance A Q2 h) :=
  loewner_trace_mono (covariance_mono_Q A Q1 Q2 hQ h)

/-! ## L16b: orthogonal gauge invariance -/

/-- Trace is invariant under orthogonal conjugation `Uᵀ * M * U` for
`Uᵀ * U = 1`. Uses `Matrix.trace_mul_comm` to cycle `U` past the conjugated
matrix and `Matrix.mul_eq_one_comm` to obtain the matching right inverse
`U * Uᵀ = 1`. -/
theorem orthogonalConj_trace {U M : Matrix n n ℝ} (hU : Uᵀ * U = 1) :
    Matrix.trace (Uᵀ * M * U) = Matrix.trace M := by
  have hUU : U * Uᵀ = 1 := Matrix.mul_eq_one_comm.mp hU
  calc Matrix.trace (Uᵀ * M * U)
      = Matrix.trace (U * (Uᵀ * M)) := Matrix.trace_mul_comm (Uᵀ * M) U
    _ = Matrix.trace ((U * Uᵀ) * M) := by rw [Matrix.mul_assoc]
    _ = Matrix.trace M := by rw [hUU, Matrix.one_mul]

/-- Determinant is invariant under orthogonal conjugation. Uses
`Matrix.det_mul` and commutativity of real multiplication rather than any
inverse/unit machinery. -/
theorem orthogonalConj_det {U M : Matrix n n ℝ} (hU : Uᵀ * U = 1) :
    Matrix.det (Uᵀ * M * U) = Matrix.det M := by
  have hd : Matrix.det Uᵀ * Matrix.det U = 1 := by
    rw [← Matrix.det_mul, hU, Matrix.det_one]
  calc Matrix.det (Uᵀ * M * U)
      = Matrix.det Uᵀ * Matrix.det M * Matrix.det U := by rw [Matrix.det_mul, Matrix.det_mul]
    _ = Matrix.det M * (Matrix.det Uᵀ * Matrix.det U) := by ring
    _ = Matrix.det M := by rw [hd, mul_one]

/-- The characteristic polynomial is invariant under orthogonal conjugation.
Uses `Matrix.charpoly_mul_comm` the same way `orthogonalConj_trace` uses
`Matrix.trace_mul_comm`. Since the roots of `charpoly` are exactly the
eigenvalues (with multiplicity), this also certifies invariance of every
purely eigenvalue-based summary (anisotropy, `dEff`, ...). -/
theorem orthogonalConj_charpoly {U M : Matrix n n ℝ} (hU : Uᵀ * U = 1) :
    (Uᵀ * M * U).charpoly = M.charpoly := by
  have hUU : U * Uᵀ = 1 := Matrix.mul_eq_one_comm.mp hU
  calc (Uᵀ * M * U).charpoly
      = (U * (Uᵀ * M)).charpoly := Matrix.charpoly_mul_comm (Uᵀ * M) U
    _ = ((U * Uᵀ) * M).charpoly := by rw [Matrix.mul_assoc]
    _ = M.charpoly := by rw [hUU, Matrix.one_mul]

/-- The finite-horizon covariance recursion pushes forward exactly through an
orthogonal change of basis: conjugating the whole recursion by `U` is the
same as running the recursion on the conjugated transition and innovation
covariance. Proved by induction on the horizon using a single reusable
cancellation fact `U * (Uᵀ * X) = X` derived from `U * Uᵀ = 1`. -/
theorem orthogonalConj_covariance (A Q0 U : Matrix n n ℝ) (hU : Uᵀ * U = 1) (h : ℕ) :
    Uᵀ * covariance A Q0 h * U = covariance (Uᵀ * A * U) (Uᵀ * Q0 * U) h := by
  have hUU : U * Uᵀ = 1 := Matrix.mul_eq_one_comm.mp hU
  have hcancel : ∀ X : Matrix n n ℝ, U * (Uᵀ * X) = X := fun X => by
    rw [← Matrix.mul_assoc, hUU, Matrix.one_mul]
  induction h with
  | zero => simp [covariance]
  | succ h ih =>
      simp only [covariance_succ, covStep, real_conjTranspose]
      rw [Matrix.mul_add, Matrix.add_mul]
      congr 1
      · rw [← ih, Matrix.transpose_mul, Matrix.transpose_mul, Matrix.transpose_transpose]
        simp only [Matrix.mul_assoc, hcancel]

/-! ## L16c: effective dimension `dEff` -/

/-- Effective dimension of a covariance matrix, `dEff Σ = (trace Σ)² /
trace (Σ * Σ)`. For symmetric `Σ` this equals `(Σλᵢ)² / Σλᵢ²` over the
eigenvalues; both traces are conjugation-invariant
(`orthogonalConj_trace`), so `dEff` is an orthogonal-gauge invariant. No
`ε`-regularization is included: this is the `ε = 0` object. -/
noncomputable def dEff (M : Matrix n n ℝ) : ℝ :=
  (Matrix.trace M) ^ 2 / Matrix.trace (M * M)

/-- `dEff` is invariant under orthogonal conjugation, since both `trace` and
`trace (M*M)` are (`orthogonalConj_trace`). This is the trace-based route to
"anisotropy and `dEff` are invariant under rotation" from the source
manuscript, without going through eigenvalues or `charpoly` roots. -/
theorem orthogonalConj_dEff {U M : Matrix n n ℝ} (hU : Uᵀ * U = 1) :
    dEff (Uᵀ * M * U) = dEff M := by
  have hUU : U * Uᵀ = 1 := Matrix.mul_eq_one_comm.mp hU
  have hcancel : ∀ X : Matrix n n ℝ, U * (Uᵀ * X) = X := fun X => by
    rw [← Matrix.mul_assoc, hUU, Matrix.one_mul]
  have hMM : (Uᵀ * M * U) * (Uᵀ * M * U) = Uᵀ * (M * M) * U := by
    simp only [Matrix.mul_assoc, hcancel]
  unfold dEff
  rw [orthogonalConj_trace hU, hMM, orthogonalConj_trace hU]

/-- `dEff` is invariant under positive scalar rescaling `Σ ↦ c • Σ`: both
`trace` and `trace (Σ*Σ)` scale, by `c` and `c²` respectively, and the ratio
cancels. This is the formal counterpart of "`dEff` is scale-insensitive,
unlike `Vol = 1/2 log det`". -/
theorem dEff_smul (M : Matrix n n ℝ) {c : ℝ} (hc : 0 < c) :
    dEff (c • M) = dEff M := by
  have hmul : (c • M) * (c • M) = c ^ 2 • (M * M) := by
    rw [smul_mul_assoc, mul_smul_comm, smul_smul, sq]
  unfold dEff
  rw [Matrix.trace_smul, hmul, Matrix.trace_smul, smul_eq_mul, smul_eq_mul,
    mul_pow, mul_div_mul_left _ _ (pow_ne_zero 2 hc.ne')]

/-- The effective dimension of the identity covariance is the ambient
dimension `Fintype.card n` (including the degenerate `n` empty case, where
both sides are `0`). -/
theorem dEff_one : dEff (1 : Matrix n n ℝ) = (Fintype.card n : ℝ) := by
  unfold dEff
  rw [Matrix.one_mul, Matrix.trace_one]
  by_cases hcard : (Fintype.card n : ℝ) = 0
  · simp [hcard]
  · field_simp

/-- Witness: a rank-one diagonal covariance `diag(1, 0)` on `Fin 2` has
effective dimension exactly `1`, matching the informal reading of `dEff` as
"how many independent directions carry variance". -/
theorem dEff_diagonal_one_zero :
    dEff (Matrix.diagonal (![1, 0] : Fin 2 → ℝ)) = 1 := by
  unfold dEff
  rw [Matrix.diagonal_mul_diagonal]
  simp [Matrix.trace_diagonal, Fin.sum_univ_two]

/-- Upper bound `dEff Σ ≤ Fintype.card n`, proved by a pure finite-sum
Cauchy–Schwarz argument on the entries of a symmetric matrix
(`sq_sum_le_card_mul_sum_sq` on the diagonal, then dropping to the full
double sum `trace (Σ*Σ) = Σᵢⱼ Σᵢⱼ²`). Needs only `M.IsSymm` and a nonzero
denominator, not positive semidefiniteness or eigenvalues. -/
theorem dEff_le_card {M : Matrix n n ℝ} (hM : M.IsSymm) (h0 : Matrix.trace (M * M) ≠ 0) :
    dEff M ≤ (Fintype.card n : ℝ) := by
  have htrMM : Matrix.trace (M * M) = ∑ i, ∑ k, (M i k) ^ 2 := by
    simp only [Matrix.trace, Matrix.diag, Matrix.mul_apply]
    refine Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun k _ => ?_
    rw [hM.apply i k]
    ring
  have hcs : (∑ i, M i i) ^ 2 ≤ (Fintype.card n : ℝ) * ∑ i, (M i i) ^ 2 := by
    have := sq_sum_le_card_mul_sum_sq (s := (Finset.univ : Finset n)) (f := fun i => M i i)
    simpa [Finset.card_univ] using this
  have hdrop : ∑ i, (M i i) ^ 2 ≤ ∑ i, ∑ k, (M i k) ^ 2 :=
    Finset.sum_le_sum fun i _ =>
      Finset.single_le_sum (fun k _ => sq_nonneg (M i k)) (Finset.mem_univ i)
  have htrM : Matrix.trace M = ∑ i, M i i := rfl
  have hfinal : (Matrix.trace M) ^ 2 ≤ (Fintype.card n : ℝ) * Matrix.trace (M * M) := by
    rw [htrM, htrMM]
    calc (∑ i, M i i) ^ 2 ≤ (Fintype.card n : ℝ) * ∑ i, (M i i) ^ 2 := hcs
      _ ≤ (Fintype.card n : ℝ) * ∑ i, ∑ k, (M i k) ^ 2 :=
          mul_le_mul_of_nonneg_left hdrop (by positivity)
  have htrMM_nonneg : 0 ≤ Matrix.trace (M * M) := by rw [htrMM]; positivity
  have hpos : 0 < Matrix.trace (M * M) := lt_of_le_of_ne htrMM_nonneg (Ne.symm h0)
  unfold dEff
  rw [div_le_iff₀ hpos]
  linarith [hfinal]

/-- Lower bound `1 ≤ dEff Σ` for nonzero positive semidefinite `Σ`. Proved
through the spectral theorem: `Σ = V * diag(eigenvalues) * Vᵀ` for an
orthogonal `V`, so `trace Σ = Σᵢ λᵢ` and `trace (Σ*Σ) = Σᵢ λᵢ²`
(via `orthogonalConj_trace`), and `Σᵢ λᵢ² ≤ (Σᵢ λᵢ)²` for nonnegative `λᵢ`
(`Finset.sum_sq_le_sq_sum_of_nonneg`, using `Matrix.PosSemidef.eigenvalues_nonneg`).
This direction genuinely needs positive semidefiniteness: a symmetric
matrix with both a positive and a negative eigenvalue can have `dEff < 1`. -/
theorem dEff_ge_one {M : Matrix n n ℝ} (hM : M.PosSemidef) (h0 : Matrix.trace (M * M) ≠ 0) :
    1 ≤ dEff M := by
  have hHerm : M.IsHermitian := hM.isHermitian
  set V : Matrix n n ℝ := (hHerm.eigenvectorUnitary : Matrix n n ℝ) with hVdef
  have hmemV : (hHerm.eigenvectorUnitary : Matrix n n ℝ) ∈ Matrix.unitaryGroup n ℝ :=
    (hHerm.eigenvectorUnitary).2
  have hVV : V * Vᵀ = 1 := by
    have h := (Matrix.mem_unitaryGroup_iff).mp hmemV
    rwa [Matrix.star_eq_conjTranspose, real_conjTranspose] at h
  have hVtV : Vᵀ * V = 1 := by
    have h := (Matrix.mem_unitaryGroup_iff').mp hmemV
    rwa [Matrix.star_eq_conjTranspose, real_conjTranspose] at h
  have hspec : M = V * Matrix.diagonal hHerm.eigenvalues * Vᵀ := by
    have h := hHerm.spectral_theorem
    rw [Matrix.star_eq_conjTranspose, real_conjTranspose,
      show (RCLike.ofReal ∘ hHerm.eigenvalues) = hHerm.eigenvalues from by
        rw [RCLike.ofReal_real_eq_id]; rfl] at h
    exact h
  have hcancel : ∀ X : Matrix n n ℝ, Vᵀ * (V * X) = X := fun X => by
    rw [← Matrix.mul_assoc, hVtV, Matrix.one_mul]
  have hMM : M * M
      = V * (Matrix.diagonal hHerm.eigenvalues * Matrix.diagonal hHerm.eigenvalues) * Vᵀ := by
    conv_lhs => rw [hspec]
    simp only [Matrix.mul_assoc, hcancel]
  have htrMM : Matrix.trace (M * M) = ∑ i, (hHerm.eigenvalues i) ^ 2 := by
    have hUV : (Vᵀ)ᵀ * Vᵀ = 1 := by rwa [Matrix.transpose_transpose]
    have htr := orthogonalConj_trace
      (U := Vᵀ) (M := Matrix.diagonal hHerm.eigenvalues * Matrix.diagonal hHerm.eigenvalues) hUV
    rw [Matrix.transpose_transpose] at htr
    rw [hMM, htr, Matrix.diagonal_mul_diagonal, Matrix.trace_diagonal]
    exact Finset.sum_congr rfl fun i _ => by ring
  have htrM : Matrix.trace M = ∑ i, hHerm.eigenvalues i := hHerm.trace_eq_sum_eigenvalues
  have hnonneg : ∀ i, 0 ≤ hHerm.eigenvalues i := fun i => hM.eigenvalues_nonneg i
  have hle : ∑ i, (hHerm.eigenvalues i) ^ 2 ≤ (∑ i, hHerm.eigenvalues i) ^ 2 :=
    Finset.sum_sq_le_sq_sum_of_nonneg fun i _ => hnonneg i
  have hpos : 0 < ∑ i, (hHerm.eigenvalues i) ^ 2 := by
    rw [← htrMM]
    have hnn : 0 ≤ Matrix.trace (M * M) := by
      rw [htrMM]; exact Finset.sum_nonneg fun i _ => sq_nonneg _
    exact lt_of_le_of_ne hnn (Ne.symm h0)
  unfold dEff
  rw [htrM, htrMM, le_div_iff₀ hpos]
  linarith [hle]

/-! ## Scaling laws -/

/-- Trace scales linearly under scalar rescaling. -/
theorem rescaling_trace_smul (M : Matrix n n ℝ) (c : ℝ) :
    Matrix.trace (c • M) = c * Matrix.trace M := by
  rw [Matrix.trace_smul, smul_eq_mul]

/-- Determinant scales by `c ^ Fintype.card n` under scalar rescaling
(`Matrix.det_smul`, restated with the L16 naming convention). -/
theorem rescaling_det_smul (M : Matrix n n ℝ) (c : ℝ) :
    Matrix.det (c • M) = c ^ Fintype.card n * Matrix.det M :=
  Matrix.det_smul M c

/-- The proof-carrying `logDetOfPosDef` (from `Noetic.CovarianceLicensing`)
shifts additively by `Fintype.card n * log c` under positive scalar
rescaling — the exact sense in which `Vol = 1/2 log det` is scale-sensitive,
in contrast to `dEff_smul`. -/
theorem rescaling_logDetOfPosDef_smul
    (M : Matrix n n ℝ) (hM : M.PosDef) {c : ℝ} (hc : 0 < c) :
    logDetOfPosDef (c • M) (hM.smul hc)
      = (Fintype.card n : ℝ) * Real.log c + logDetOfPosDef M hM := by
  unfold logDetOfPosDef
  rw [Matrix.det_smul,
    Real.log_mul (pow_ne_zero _ hc.ne') (ne_of_gt (posDef_det_pos_licence M hM)), Real.log_pow]

/-! ## Rescaling counterexample: nonuniform rescaling is not a gauge symmetry -/

/-- Witness that `D = diag(2, 1)` changes the trace of the identity
covariance under `Σ ↦ D * Σ * Dᵀ`: `5 ≠ 2`. This is the exact counterpoint
to `orthogonalConj_trace`: `D` is not orthogonal (`Dᵀ * D ≠ 1`), and
conjugating by it is not a gauge symmetry. -/
theorem rescaling_changes_trace :
    Matrix.trace
        (Matrix.diagonal (![2, 1] : Fin 2 → ℝ) * (1 : Matrix (Fin 2) (Fin 2) ℝ)
          * (Matrix.diagonal (![2, 1] : Fin 2 → ℝ))ᵀ)
      ≠ Matrix.trace (1 : Matrix (Fin 2) (Fin 2) ℝ) := by
  simp [Matrix.trace_diagonal, Fin.sum_univ_two, Matrix.diagonal_transpose,
    Matrix.diagonal_mul_diagonal, Matrix.trace_one]
  norm_num

/-- Witness that `D = diag(2, 1)` also changes the trace-based `dEff` of the
identity covariance: `dEff (D * 1 * Dᵀ) = 25/17 ≠ 2 = dEff 1`. Together with
`rescaling_changes_trace`, this shows nonuniform rescaling changes both the
volume-type and shape-type summaries, unlike an orthogonal conjugation. -/
theorem rescaling_changes_dEff :
    dEff
        (Matrix.diagonal (![2, 1] : Fin 2 → ℝ) * (1 : Matrix (Fin 2) (Fin 2) ℝ)
          * (Matrix.diagonal (![2, 1] : Fin 2 → ℝ))ᵀ)
      ≠ dEff (1 : Matrix (Fin 2) (Fin 2) ℝ) := by
  have h1 : dEff (1 : Matrix (Fin 2) (Fin 2) ℝ) = 2 := by
    unfold dEff
    rw [Matrix.one_mul, Matrix.trace_one]
    norm_num
  rw [h1]
  unfold dEff
  simp [Matrix.diagonal_transpose, Matrix.diagonal_mul_diagonal, Matrix.trace_diagonal,
    Fin.sum_univ_two]
  norm_num

end NoeticDiffusion
