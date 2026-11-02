import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
import Mathlib.Analysis.Normed.Algebra.MatrixExponential
import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Analysis.SpecialFunctions.Exponential
import Mathlib.Analysis.Complex.ExponentialBounds
import Noetic.JacobianReactivity
import Noetic.AccessOperators

/-!
# L21: discrete/continuous Jacobian conversion and finite-time gain

This module formalizes the matrix-exponential layer of NDT v2's discrete/
continuous conversion contract `A_d = exp(J_c * Δt)`, `J_c ≈ (A_d - 1)/Δt`
for small `Δt` (compact summary §4 "EMPIRICAL LOCAL LINEAR ESTIMATION"), and
the finite-time amplification claim that `G_peak(T)` is "a different object
again" from the spectral abscissa `alpha` (manuscript v2 lines 550-560).
Simulator anchors: Gate J1 hard conversion contract
(`results/orthogonal_dynamics_stage_j1_gate/effect_summary.json`,
`claim_ledger.md:102`, `tests/orthogonal_dynamics/test_gate_j1_mnj_reactivity.py:110-127`)
and TA-4 (`results/thalamic_access_ta4/effect_summary.json`,
`G_max(C0) = 0.9512 < 1 < 1.0764 = G_max(CR)`); NDT source anchor
`project/lean/fable_ideas/11_jacobian_conversion_and_finite_time_gain.md`.

## Claim boundary

This module proves four disjoint algebraic facts about `NormedSpace.exp ℝ`
on fixed real square matrices (`Mathlib.Analysis.Normed.Algebra.MatrixExponential`),
reusing `J1`, `R1`, `symPart`, `antisymPart`, `symPart_add_antisymPart`,
`symPart_R1_eq`, `antisymPart_transpose` from `Noetic.JacobianReactivity` (L12)
and `alpha_similarity_invariant` from `Noetic.AccessOperators` (L19), adding no
new definitions of those objects:

* **L21a (similarity witness, no `exp`).** `J1 = P * D * P` with
  `D = diag(-1,-3)`, `P = [[1,3],[0,-1]]`, and `P * P = 1` (so `P⁻¹ = P`);
  `alpha_similarity_invariant` then transports `D`'s trivial eigenvectors
  `e0`, `e1` to `J1`'s eigenvectors `(1,0)` (eigenvalue `-1`) and `(3,-1)`
  (eigenvalue `-3`). Separately, the naive discrete-to-continuous conversion
  `A ≈ 1 + Δt J` is strictly biased at every finite step: `1 + x < exp x` for
  `x ≠ 0` (`Real.add_one_lt_exp`), giving `log a / Δt < (a - 1) / Δt` for
  `a > 0`, `a ≠ 1`, `Δt > 0` (naive rate strictly exceeds the true rate).
* **L21b (shear exponential).** For a square-zero `N` (`N * N = 0`),
  `NormedSpace.exp ℝ N = 1 + N` is proved directly from the defining series
  (`NormedSpace.exp_eq_tsum`, truncated at the vanishing second term via
  `tsum_eq_sum`) -- a fully machine-checked identification, not the
  unidentified closed-form fallback the source idea file allows. Combined
  with the analogous direct proof that `NormedSpace.exp ℝ (c • 1) = exp c • 1`
  (via `Matrix.exp_diagonal` and `Pi.exp_def`) and `Matrix.exp_add_of_commute`,
  this gives the exact closed form
  `NormedSpace.exp ℝ (t • (-(1) + k • E12)) = shearExp t k` where
  `shearExp t k := exp(-t) • (1 + t • (k • E12))`, plus the semigroup laws
  `shearExp 0 k = 1` and `shearExp (s + t) k = shearExp s k * shearExp t k`
  proved directly from the closed form (`E12 * E12 = 0`).
* **L21c (finite-time gain, given L21b).** For `k = 6`, `t = 1/2`,
  `v = (0,1)`: `(shearExp (1/2) 6 *ᵥ v) ⬝ᵥ (shearExp (1/2) 6 *ᵥ v) = exp(-1) * 10`,
  and `10 > exp 1` (`Real.exp_one_lt_d9`, `2.7182818286 < 10`), so this
  quantity exceeds `1` -- the continuous-time "all eigenvalues `-1` yet
  transient growth" witness, machine-checked against the true matrix
  exponential via `shearExp`'s L21b identification, not merely the closed
  form in isolation.
* **L21d (rotation-pair orthogonality).** For any antisymmetric `Ω`
  (`Ωᵗ = -Ω`), `(exp Ω)ᵗ * exp Ω = 1`, via `Matrix.exp_transpose`,
  `Matrix.exp_neg`, `Matrix.isUnit_exp` and `Matrix.nonsing_inv_mul` (no
  trigonometric closed form for `exp Ω` is proved or needed). Consequently,
  for `R1 = -2 • 1 + antisymPart R1` (`symPart_R1_eq`), the propagator
  factors exactly as `exp(t * R1) = exp(-2t) • exp(t * antisymPart R1)`
  (`Matrix.exp_add_of_commute`, scalar-identity commutes with anything), with
  the second factor's transpose-times-itself equal to `1` at every `t`: the
  rotational part changes the operator but not the exact `e^{-2t}` energy
  decay rate.

Out of scope: no ODE solution theory beyond the algebraic identities above;
no `Matrix.log`; no spectral/operator norm (gains are certified on an
explicit unit vector, a lower bound, sufficient for "> 1" claims); no
estimator, empirical recovery, or biological interpretation. `shearExp`'s
identification with `NormedSpace.exp` is fully proved here (not merely
asserted), in contrast to the idea file's stated fallback of leaving that
identification unchecked.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix
open NormedSpace

variable {n : Type*} [Fintype n] [DecidableEq n]

/-! ## L21a: exact similarity/eigen-decomposition witness for `J1`, and the
naive discrete-to-continuous conversion bias -/

/-- Similarity witness `P = [[1,3],[0,-1]]` for `J1`. -/
def L21_P : Matrix (Fin 2) (Fin 2) ℝ := !![1, 3; 0, -1]

/-- Diagonal target `D = diag(-1,-3)`, the shared spectrum of `J1`. -/
def L21_D : Matrix (Fin 2) (Fin 2) ℝ := !![-1, 0; 0, -3]

/-- `P` is its own inverse: `P * P = 1`. -/
theorem L21_P_mul_self : L21_P * L21_P = 1 := by
  ext i j
  fin_cases i <;> fin_cases j <;> simp [L21_P, Matrix.mul_apply, Fin.sum_univ_two]

/-- Consequently `P⁻¹ = P`. -/
theorem L21_P_inv_eq : L21_P⁻¹ = L21_P := Matrix.inv_eq_right_inv L21_P_mul_self

/-- `P` is invertible (its determinant is `-1 ≠ 0`). -/
theorem L21_P_isUnit : IsUnit L21_P := by
  rw [Matrix.isUnit_iff_isUnit_det]
  have hdet : L21_P.det = -1 := by simp [L21_P, Matrix.det_fin_two_of]
  rw [hdet]
  exact isUnit_iff_ne_zero.mpr (by norm_num)

/-- **L21a exact similarity.** `P⁻¹ * J1 * P = D`: `J1` and `diag(-1,-3)` are
similar via the explicit, self-inverse witness `P`. -/
theorem L21_conj_J1_eq_D : L21_P⁻¹ * J1 * L21_P = L21_D := by
  rw [L21_P_inv_eq]
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [L21_P, L21_D, J1, Matrix.mul_apply, Fin.sum_univ_two]
  all_goals norm_num

/-- **L21a eigenvector transport.** Via `alpha_similarity_invariant` (L19),
`D`'s eigenvector equation transports exactly to `J1`'s along `v ↦ P *ᵥ v`. -/
theorem L21_eigenvector_transport (w : Fin 2 → ℝ) (lam : ℝ) :
    L21_D *ᵥ w = lam • w ↔ J1 *ᵥ (L21_P *ᵥ w) = lam • (L21_P *ᵥ w) := by
  rw [← L21_conj_J1_eq_D]
  exact alpha_similarity_invariant L21_P_isUnit w lam

/-- Concrete instance: `(1,0)` is an eigenvector of `J1` with eigenvalue
`-1` (the image of `D`'s first standard basis vector under `P`). -/
theorem L21_eigenvector_e0 : J1 *ᵥ (![1, 0] : Fin 2 → ℝ) = (-1 : ℝ) • ![1, 0] := by
  ext i
  fin_cases i <;> simp [J1, Matrix.mulVec, dotProduct, Fin.sum_univ_two]

/-- Concrete instance: `(3,-1)` (the second column of `P`) is an eigenvector
of `J1` with eigenvalue `-3` (the image of `D`'s second standard basis
vector under `P`). -/
theorem L21_eigenvector_col : J1 *ᵥ (![3, -1] : Fin 2 → ℝ) = (-3 : ℝ) • ![3, -1] := by
  ext i
  fin_cases i <;> simp [J1, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
  all_goals norm_num

/-- **Naive-conversion bias, scalar form.** `1 + x < exp x` for `x ≠ 0`
(reprise of `Real.add_one_lt_exp` with the summands reordered to match the
`A ≈ 1 + Δt J` linearization form). -/
theorem naiveConversion_lt_exp {x : ℝ} (hx : x ≠ 0) : 1 + x < Real.exp x := by
  have h := Real.add_one_lt_exp hx
  linarith

/-- **Naive-conversion bias, rate form.** For `a > 0`, `a ≠ 1`, `Δt > 0`, the
naive first-order rate `(a - 1)/Δt` strictly exceeds the true logarithmic
rate `log a / Δt`: the discrete-to-continuous conversion `J_c ≈ (A_d - 1)/Δt`
is biased at every finite step, in the direction dictated by strict
convexity of `exp`. -/
theorem naiveConversion_rate_lt_trueRate {a dt : ℝ} (ha : 0 < a) (ha1 : a ≠ 1) (hdt : 0 < dt) :
    Real.log a / dt < (a - 1) / dt := by
  have hx : Real.log a ≠ 0 := by
    intro h
    exact ha1 (by
      have hexp := Real.exp_log ha
      rw [h] at hexp
      simpa using hexp.symm)
  have hlt : Real.log a + 1 < Real.exp (Real.log a) := Real.add_one_lt_exp hx
  rw [Real.exp_log ha] at hlt
  have hlog : Real.log a < a - 1 := by linarith
  gcongr

/-! ## L21b: exact matrix-exponential identities and the shear closed form -/

/-- **Nilpotent exponential.** For any square-zero real matrix `N`
(`N * N = 0`), `NormedSpace.exp ℝ N = 1 + N`. Proved directly from
`NormedSpace.exp_eq_tsum`: all terms of index `≥ 2` in the series vanish
(`N ^ k = N ^ 2 * N ^ (k - 2) = 0`), so the sum truncates to `1 + N` via
`tsum_eq_sum`. A fully machine-checked identification, not an unproved
closed-form assertion. -/
theorem matExp_of_sq_eq_zero {N : Matrix n n ℝ} (hN : N * N = 0) :
    NormedSpace.exp ℝ N = 1 + N := by
  rw [NormedSpace.exp_eq_tsum]
  show ∑' k : ℕ, (k.factorial : ℝ)⁻¹ • N ^ k = 1 + N
  have hz : ∀ k : ℕ, 2 ≤ k → N ^ k = 0 := by
    intro k hk
    obtain ⟨m, rfl⟩ := Nat.exists_eq_add_of_le hk
    rw [pow_add]
    have hsq : N ^ 2 = 0 := by rw [sq]; exact hN
    rw [hsq, zero_mul]
  rw [tsum_eq_sum (s := Finset.range 2) (by
    intro b hb
    rw [Finset.mem_range, not_lt] at hb
    rw [hz b hb, smul_zero])]
  rw [Finset.sum_range_succ, Finset.sum_range_one]
  simp

/-- **Scalar-identity exponential.** `NormedSpace.exp ℝ (c • 1) = exp c • 1`
for any real scalar `c`, proved via `Matrix.exp_diagonal` (a scalar matrix is
`diagonal (fun _ => c)`) and the pointwise Pi-algebra identity `Pi.exp_def`,
identifying the scalar-Pi exponential with `Real.exp` via `Real.exp_eq_exp_ℝ`. -/
theorem matExp_smul_one (c : ℝ) :
    NormedSpace.exp ℝ (c • (1 : Matrix n n ℝ)) = Real.exp c • (1 : Matrix n n ℝ) := by
  have hdiag : c • (1 : Matrix n n ℝ) = Matrix.diagonal (fun _ : n => c) := by
    ext i j
    simp [Matrix.diagonal, Matrix.one_apply, Matrix.smul_apply]
  rw [hdiag, Matrix.exp_diagonal, Pi.exp_def, Real.exp_eq_exp_ℝ]
  ext i j
  simp [Matrix.diagonal, Matrix.one_apply, Matrix.smul_apply]

/-- Jordan-shear nilpotent generator `E12 = [[0,1],[0,0]]` (reused verbatim
in shape from `Noetic.JacobianReactivity`'s `shear k = -1 + k • E12`, but not
imported from there since that module defines only the packaged `shear k`,
not `E12` itself). -/
def L21_E12 : Matrix (Fin 2) (Fin 2) ℝ := !![0, 1; 0, 0]

/-- `E12` is square-zero. -/
theorem L21_E12_mul_self : L21_E12 * L21_E12 = 0 := by
  ext i j
  fin_cases i <;> fin_cases j <;> simp [L21_E12, Matrix.mul_apply, Fin.sum_univ_two]

/-- **Closed-form candidate for the shear exponential.**
`shearExp t k := exp(-t) • (1 + t • (k • E12))`. -/
noncomputable def shearExp (t k : ℝ) : Matrix (Fin 2) (Fin 2) ℝ :=
  Real.exp (-t) • (1 + t • (k • L21_E12))

/-- **L21b main identity.** `shearExp t k` is exactly the matrix exponential
of the shear generator `t • (-(1) + k • E12)`: combines `matExp_smul_one` (for
the `-(t•1)` scalar factor) and `matExp_of_sq_eq_zero` (for the nilpotent
`t • (k • E12)` factor) via `Matrix.exp_add_of_commute` (scalar-identity
matrices commute with anything). This is the full, machine-checked
identification with `NormedSpace.exp` -- not the unidentified fallback the
source idea file allows for. -/
theorem shearExp_eq_matExp (t k : ℝ) :
    NormedSpace.exp ℝ (t • (-(1 : Matrix (Fin 2) (Fin 2) ℝ) + k • L21_E12)) = shearExp t k := by
  have hexpand : t • (-(1 : Matrix (Fin 2) (Fin 2) ℝ) + k • L21_E12)
      = (-t) • (1 : Matrix (Fin 2) (Fin 2) ℝ) + t • (k • L21_E12) := by
    rw [smul_add, smul_neg, neg_smul]
  rw [hexpand]
  have hcomm : Commute ((-t) • (1 : Matrix (Fin 2) (Fin 2) ℝ)) (t • (k • L21_E12)) := by
    unfold Commute SemiconjBy
    rw [Matrix.smul_mul, Matrix.one_mul, Matrix.mul_smul, Matrix.mul_one]
  rw [Matrix.exp_add_of_commute ℝ _ _ hcomm, matExp_smul_one]
  have hN0 : (t • (k • L21_E12)) * (t • (k • L21_E12)) = 0 := by
    have heq : t • (k • L21_E12) = (t * k) • L21_E12 := by rw [smul_smul]
    rw [heq, Matrix.smul_mul, Matrix.mul_smul, L21_E12_mul_self, smul_zero, smul_zero]
  rw [matExp_of_sq_eq_zero hN0, smul_mul_assoc, one_mul]
  rfl

/-- `shearExp 0 k = 1`. -/
theorem shearExp_zero (k : ℝ) : shearExp 0 k = 1 := by
  unfold shearExp
  simp

/-- **Semigroup law.** `shearExp (s + t) k = shearExp s k * shearExp t k`,
proved directly from the closed form using `E12 * E12 = 0` (algebraic, not
re-derived from `NormedSpace.exp` -- it is a corollary of `shearExp_eq_matExp`
together with the general propagator semigroup property, but is checked here
directly on the closed form for a self-contained proof). -/
theorem shearExp_add (s t k : ℝ) : shearExp (s + t) k = shearExp s k * shearExp t k := by
  unfold shearExp
  rw [smul_mul_smul_comm, ← Real.exp_add]
  congr 1
  · congr 1; ring
  · have hE2 : (k • L21_E12) * (k • L21_E12) = 0 := by
      rw [Matrix.smul_mul, Matrix.mul_smul, L21_E12_mul_self, smul_zero, smul_zero]
    have hcross : (s • (k • L21_E12)) * (t • (k • L21_E12)) = 0 := by
      rw [Matrix.smul_mul, Matrix.mul_smul, hE2, smul_zero, smul_zero]
    have hexpand : (1 + (s + t) • (k • L21_E12)) = (1 + s • (k • L21_E12)) * (1 + t • (k • L21_E12)) := by
      simp only [mul_add, add_mul, one_mul, mul_one, hcross, add_zero, add_smul]
      abel
    exact hexpand

/-! ## L21c: finite-time gain exceeds 1 despite all eigenvalues equal to `-1` -/

/-- **L21c finite-time gain.** For `k = 6`, `t = 1/2`, and the unit vector
`v = (0,1)`, the squared norm of `shearExp (1/2) 6 *ᵥ v` strictly exceeds
`1`, although `shear 6` (`Noetic.JacobianReactivity`) has both eigenvalues
equal to `-1`: instantaneous/finite-time growth is not excluded by negative
eigenvalues, now certified against the exact continuous-time propagator
`shearExp` (itself identified with `NormedSpace.exp` by `shearExp_eq_matExp`),
not merely a discrete-step analogue. -/
theorem finiteTimeGain_gt_one :
    1 < (shearExp (1 / 2) 6 *ᵥ (![0, 1] : Fin 2 → ℝ)) ⬝ᵥ
        (shearExp (1 / 2) 6 *ᵥ (![0, 1] : Fin 2 → ℝ)) := by
  have hw : shearExp (1 / 2) 6 *ᵥ (![0, 1] : Fin 2 → ℝ)
      = ![Real.exp (-(1 / 2 : ℝ)) * 3, Real.exp (-(1 / 2 : ℝ))] := by
    unfold shearExp
    ext i
    fin_cases i <;>
      simp [L21_E12, Matrix.mulVec, dotProduct, Fin.sum_univ_two, Matrix.add_apply,
        Matrix.one_apply]
    norm_num
  rw [hw]
  simp only [dotProduct, Fin.sum_univ_two, Matrix.cons_val_zero, Matrix.cons_val_one]
  have he : Real.exp 1 < 10 := by
    have h9 := Real.exp_one_lt_d9
    linarith
  have he2 : Real.exp (-(1 / 2 : ℝ)) * Real.exp (-(1 / 2 : ℝ)) = Real.exp (-1) := by
    rw [← Real.exp_add]; norm_num
  have hpos : 0 < Real.exp (1 : ℝ) := Real.exp_pos 1
  have hval : Real.exp (-(1 / 2 : ℝ)) * 3 * (Real.exp (-(1 / 2 : ℝ)) * 3)
      + Real.exp (-(1 / 2 : ℝ)) * Real.exp (-(1 / 2 : ℝ)) = 10 * Real.exp (-1) := by
    rw [← he2]; ring
  rw [hval, show (10 : ℝ) * Real.exp (-1) = 10 / Real.exp 1 by rw [Real.exp_neg]; ring,
    lt_div_iff₀ hpos]
  linarith [he]

/-! ## L21d: rotation-pair orthogonality and the exact `e^{-2t}` decay for `R1` -/

/-- **L21d orthogonality.** For any antisymmetric real square matrix `Ω`
(`Ωᵗ = -Ω`), `(exp Ω)ᵗ * exp Ω = 1`: proved from `Matrix.exp_transpose`
(giving `(exp Ω)ᵗ = exp Ωᵗ = exp(-Ω)`), `Matrix.exp_neg`
(`exp(-Ω) = (exp Ω)⁻¹`), and `Matrix.isUnit_exp`/`Matrix.nonsing_inv_mul`
(`(exp Ω)⁻¹ * exp Ω = 1`). No trigonometric closed form for `exp Ω` is
needed or proved. -/
theorem rotationPair_orthogonal {Omega : Matrix n n ℝ} (hOmega : Omega.transpose = -Omega) :
    (NormedSpace.exp ℝ Omega).transpose * NormedSpace.exp ℝ Omega = 1 := by
  have h1 : (NormedSpace.exp ℝ Omega).transpose = NormedSpace.exp ℝ (-Omega) := by
    rw [← Matrix.exp_transpose ℝ Omega, hOmega]
  rw [h1, Matrix.exp_neg ℝ Omega]
  have hunit : IsUnit (NormedSpace.exp ℝ Omega) := Matrix.isUnit_exp ℝ Omega
  have hdet : IsUnit (NormedSpace.exp ℝ Omega).det := (Matrix.isUnit_iff_isUnit_det _).mp hunit
  exact Matrix.nonsing_inv_mul _ hdet

/-- `R1`'s decomposition `R1 = -2 • 1 + antisymPart R1` (from L12's
`symPart_add_antisymPart` and `symPart_R1_eq`). -/
theorem L21_R1_eq_decomp : R1 = (-2 : ℝ) • (1 : Matrix (Fin 2) (Fin 2) ℝ) + antisymPart R1 := by
  conv_lhs => rw [← symPart_add_antisymPart R1]
  rw [symPart_R1_eq]

/-- **L21d propagator factorization for `R1`.** `exp(t * R1)` factors exactly
as `exp(-2t) • exp(t * antisymPart R1)`: the scalar contraction `-2 • 1`
commutes with everything, so `Matrix.exp_add_of_commute` applies to the
decomposition `R1 = -2 • 1 + antisymPart R1`, and `matExp_smul_one` evaluates
the scalar factor. -/
theorem rotationPair_R1_decomp (t : ℝ) :
    NormedSpace.exp ℝ (t • R1) = Real.exp (-2 * t) • NormedSpace.exp ℝ (t • antisymPart R1) := by
  conv_lhs => rw [L21_R1_eq_decomp]
  have hexpand : t • ((-2 : ℝ) • (1 : Matrix (Fin 2) (Fin 2) ℝ) + antisymPart R1)
      = (-2 * t) • (1 : Matrix (Fin 2) (Fin 2) ℝ) + t • antisymPart R1 := by
    rw [smul_add, smul_smul, mul_comm]
  rw [hexpand]
  have hcomm : Commute ((-2 * t) • (1 : Matrix (Fin 2) (Fin 2) ℝ)) (t • antisymPart R1) := by
    unfold Commute SemiconjBy
    rw [Matrix.smul_mul, Matrix.one_mul, Matrix.mul_smul, Matrix.mul_one]
  rw [Matrix.exp_add_of_commute ℝ _ _ hcomm, matExp_smul_one, smul_mul_assoc, one_mul]

/-- **L21d rotational factor is exactly orthogonal at every `t`.** The second
factor of `rotationPair_R1_decomp` satisfies `(exp(t * Ω))ᵗ * exp(t * Ω) = 1`
for `Ω = antisymPart R1`, so `R1`'s propagator decays with exactly the scalar
rate `e^{-2t}` (its norm equals `e^{-2t}` times the norm of the initial
vector) regardless of the rotational component -- rotation is not
reactivity, now at the level of the exact continuous-time propagator rather
than only the frozen symmetric part (`Noetic.JacobianReactivity`'s L12c). -/
theorem rotationPair_R1_orthogonal (t : ℝ) :
    (NormedSpace.exp ℝ (t • antisymPart R1)).transpose * NormedSpace.exp ℝ (t • antisymPart R1) = 1 :=
  rotationPair_orthogonal (by rw [Matrix.transpose_smul, antisymPart_transpose, smul_neg])

end

end NoeticDiffusion
