import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.LinearAlgebra.Matrix.Symmetric
import Mathlib.LinearAlgebra.Matrix.Spectrum

/-!
# L12: spectral abscissa, numerical abscissa, and the reactivity gap

This module formalizes the algebraic core of NDT v2's distinction between the
*spectral abscissa* `alpha(J) = max_i Re lambda_i(J)` and the *numerical
abscissa* `omega(J) = lambda_max((J + Jᵗ)/2)` of a real square Jacobian `J`,
and the derived *reactivity gap* `Delta_react = omega - alpha`.

NDT source: `articles/NoeticDiffusionTheory_v2/Noetic Diffusion Theory - Neural
State, Dynamical Accessibility, and the Geometry of Possible Futures.typ`,
lines 531-560 (alpha, omega, reactivity gap, `G_peak`), 561-568 (coordinate
boundary), table lines 658-677; `articles/aa_basicinfo/ndt_compact_summary,md`
§4 "MODAL GROWTH / REACTIVITY FAMILY" and "FINITE-TIME AMPLIFICATION";
manuscript lines 764-767 (thalamic-access claim).

## Claim boundary

This module proves, for real square matrices, the elementary Rayleigh-quotient
algebra separating the symmetric part `S = (J + Jᵗ)/2` (which alone determines
whether the quadratic form `v ↦ vᵗ J v` can grow) from the antisymmetric part
`Ω = (J - Jᵗ)/2` (which contributes nothing to that quadratic form). It proves
the resulting real-eigenvalue bound `lam ≤ w` for any numerical-abscissa bound
`w`, and it exhibits four concrete 2×2 witnesses -- a shear family `J_k`, the
simulator-frozen pair `J₁`/`R₁`, and a discrete-time shear `A` -- certifying
machine-checked, eigenvalue-free proofs that "all eigenvalues have negative
real part" does not imply "no instantaneous or finite-time growth". `numAbscissa`
(the top eigenvalue of the symmetric part, via `Matrix.IsHermitian.eigenvalues`
and the spectral theorem) is defined and proved to be a numerical-abscissa
bound.

Out of scope: no continuous-time ODE solution, no `exp(tJ)`, no Lyapunov
argument; the differential identity `d/dt ‖x‖² = 2 xᵗ S x` is *not* proved,
only the algebraic Rayleigh inequality. Complex eigenvalues are handled only
for the specific real triangular witnesses (excluded by the determinant
computation), not in general. No claim that MNJ estimates recover `alpha`,
`omega`; no chart-invariance claim. Not a complete non-normality measure.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

/-! ## L12a: symmetric/antisymmetric decomposition and the Rayleigh bound -/

variable {n : Type*} [Fintype n]

/-- Symmetric part `S = (J + Jᵗ)/2` of a real square matrix. -/
def symPart (J : Matrix n n ℝ) : Matrix n n ℝ := (1 / 2 : ℝ) • (J + J.transpose)

/-- Antisymmetric part `Ω = (J - Jᵗ)/2` of a real square matrix. -/
def antisymPart (J : Matrix n n ℝ) : Matrix n n ℝ := (1 / 2 : ℝ) • (J - J.transpose)

/-- `w` is a numerical-abscissa bound for `J`: the Rayleigh quotient of `J`
(equivalently of `symPart J`) never exceeds `w` times `v ⬝ᵥ v`. -/
def IsNumAbscissaBound (J : Matrix n n ℝ) (w : ℝ) : Prop :=
  ∀ v : n → ℝ, v ⬝ᵥ (J *ᵥ v) ≤ w * (v ⬝ᵥ v)

omit [Fintype n] in
/-- **Theorem 1 (decomposition).** `symPart J + antisymPart J = J`. -/
theorem symPart_add_antisymPart (J : Matrix n n ℝ) :
    symPart J + antisymPart J = J := by
  ext i j
  simp only [symPart, antisymPart, Matrix.add_apply, Matrix.sub_apply, Matrix.smul_apply,
    Matrix.transpose_apply, smul_eq_mul]
  ring

omit [Fintype n] in
/-- **Theorem 2a (symmetry).** `symPart J` is symmetric. -/
theorem symPart_isSymm (J : Matrix n n ℝ) : (symPart J).IsSymm := by
  apply Matrix.IsSymm.ext
  intro i j
  simp only [symPart, Matrix.smul_apply, Matrix.add_apply, Matrix.transpose_apply, smul_eq_mul]
  ring

omit [Fintype n] in
/-- **Theorem 2b (antisymmetry).** `antisymPart J` is antisymmetric. -/
theorem antisymPart_transpose (J : Matrix n n ℝ) :
    (antisymPart J).transpose = -(antisymPart J) := by
  ext i j
  simp only [antisymPart, Matrix.transpose_apply, Matrix.smul_apply, Matrix.sub_apply,
    Matrix.neg_apply, smul_eq_mul]
  ring

/-- **Theorem 3.** The antisymmetric part does no "work": its Rayleigh quotient
is identically zero. -/
theorem dotProduct_antisymPart_mulVec (J : Matrix n n ℝ) (v : n → ℝ) :
    v ⬝ᵥ (antisymPart J *ᵥ v) = 0 := by
  set x : ℝ := v ⬝ᵥ (antisymPart J *ᵥ v) with hx
  have h1 : x = (antisymPart J).transpose *ᵥ v ⬝ᵥ v := by
    rw [hx, Matrix.dotProduct_mulVec, Matrix.mulVec_transpose]
  have h2 : (antisymPart J).transpose *ᵥ v ⬝ᵥ v = -x := by
    rw [antisymPart_transpose, Matrix.neg_mulVec, neg_dotProduct, dotProduct_comm, ← hx]
  have hxx : x = -x := h1.trans h2
  linarith

/-- **Theorem 4.** The Rayleigh quotient of `J` equals that of its symmetric
part. -/
theorem dotProduct_mulVec_eq_symPart (J : Matrix n n ℝ) (v : n → ℝ) :
    v ⬝ᵥ (J *ᵥ v) = v ⬝ᵥ (symPart J *ᵥ v) := by
  conv_lhs => rw [← symPart_add_antisymPart J]
  rw [Matrix.add_mulVec, dotProduct_add, dotProduct_antisymPart_mulVec J v, add_zero]

/-- For a nonzero real vector, the self dot product is strictly positive. -/
private lemma dotProduct_self_pos_of_ne_zero {v : n → ℝ} (hv : v ≠ 0) :
    0 < v ⬝ᵥ v := by
  have hex : ∃ i, v i ≠ 0 := by
    by_contra h
    push_neg at h
    exact hv (funext h)
  obtain ⟨i, hi⟩ := hex
  have hpos : 0 < v i * v i := mul_self_pos.mpr hi
  have hle : v i * v i ≤ v ⬝ᵥ v := by
    unfold dotProduct
    exact Finset.single_le_sum (fun j _ => mul_self_nonneg (v j)) (Finset.mem_univ i)
  linarith

/-- **Theorem 5 (real eigenvalue bound).** If `v` is a real eigenvector of `J`
with eigenvalue `lam`, and `w` is any numerical-abscissa bound for `J`, then
`lam ≤ w`. -/
theorem le_of_isNumAbscissaBound_of_mulVec_eq_smul
    {J : Matrix n n ℝ} {w lam : ℝ} {v : n → ℝ} (hbound : IsNumAbscissaBound J w)
    (hv : v ≠ 0) (heig : J *ᵥ v = lam • v) : lam ≤ w := by
  have hvv : 0 < v ⬝ᵥ v := dotProduct_self_pos_of_ne_zero hv
  have hb : lam * (v ⬝ᵥ v) ≤ w * (v ⬝ᵥ v) := by
    have hb0 := hbound v
    rwa [heig, dotProduct_smul, smul_eq_mul] at hb0
  by_contra hcon
  push_neg at hcon
  have hlt : w * (v ⬝ᵥ v) < lam * (v ⬝ᵥ v) := mul_lt_mul_of_pos_right hcon hvv
  linarith

/-- **Theorem 6 (nonnegative gap).** For every real eigenvalue `lam` of `J`
witnessed by a nonzero eigenvector, and every numerical-abscissa bound `w`,
`0 ≤ w - lam`. -/
theorem sub_nonneg_of_isNumAbscissaBound_of_mulVec_eq_smul
    {J : Matrix n n ℝ} {w lam : ℝ} {v : n → ℝ} (hbound : IsNumAbscissaBound J w)
    (hv : v ≠ 0) (heig : J *ᵥ v = lam • v) : 0 ≤ w - lam := by
  linarith [le_of_isNumAbscissaBound_of_mulVec_eq_smul hbound hv heig]

/-! ## L12b: exact numerical abscissa via the Hermitian spectral theorem

`numAbscissa J` is the top eigenvalue of `symPart J` (via
`Matrix.IsHermitian.eigenvalues`, real matrices being `TrivialStar`). The
spectral theorem gives both directions: `numAbscissa J` is itself a
numerical-abscissa bound, and it is the *least* such bound. When `J` is
already symmetric, `symPart J = J`, so this bound is computed directly from
`J`'s own Hermitian eigenvalues (the reactivity gap collapses). -/

section L12b

variable [DecidableEq n]

omit [Fintype n] [DecidableEq n] in
/-- `symPart J` is Hermitian (real symmetric matrices are Hermitian, since `ℝ`
has trivial star). -/
theorem symPart_isHermitian (J : Matrix n n ℝ) : (symPart J).IsHermitian := by
  show (symPart J).transpose = symPart J
  rw [← Matrix.conjTranspose_eq_transpose_of_trivial (symPart J)]
  exact symPart_isSymm J

/-- The numerical abscissa: the top eigenvalue of `symPart J`. -/
noncomputable def numAbscissa (J : Matrix n n ℝ) [Nonempty n] : ℝ :=
  Finset.univ.sup' Finset.univ_nonempty (symPart_isHermitian J).eigenvalues

/-- **`numAbscissa J` is a numerical-abscissa bound.** Proved via the
spectral theorem `symPart J = Q * D * Qᴴ` (`Q` the eigenvector-basis unitary,
`D` the diagonal of Hermitian eigenvalues), transporting the Rayleigh
quotient of `J` at `v` into the orthonormal eigenbasis coordinate
`u = Qᵗ *ᵥ v` (which preserves `u ⬝ᵥ u = v ⬝ᵥ v`, `Q` being orthogonal), then
bounding each diagonal term `eigenvalues i * (u i)²` by
`numAbscissa J * (u i)²`. -/
theorem isNumAbscissaBound_numAbscissa (J : Matrix n n ℝ) [Nonempty n] :
    IsNumAbscissaBound J (numAbscissa J) := by
  intro v
  rw [dotProduct_mulVec_eq_symPart J v]
  have hA := symPart_isHermitian J
  have hspec := hA.spectral_theorem
  set Q : Matrix n n ℝ := (Matrix.IsHermitian.eigenvectorUnitary hA : Matrix n n ℝ) with hQdef
  have hDeq :
      Matrix.diagonal (RCLike.ofReal ∘ hA.eigenvalues) = Matrix.diagonal hA.eigenvalues := by
    congr 1
  rw [hDeq] at hspec
  set D : Matrix n n ℝ := Matrix.diagonal hA.eigenvalues with hDdef
  set u : n → ℝ := star Q *ᵥ v with hu
  have hstarQ_eq : (star Q : Matrix n n ℝ) = Q.transpose :=
    Matrix.conjTranspose_eq_transpose_of_trivial Q
  have hQQ : Q * star Q = 1 :=
    (Matrix.mem_unitaryGroup_iff).mp (Matrix.IsHermitian.eigenvectorUnitary hA).2
  have hleft : symPart J *ᵥ v = Q *ᵥ (D *ᵥ u) := by
    rw [hspec, hu]
    simp only [Matrix.mulVec_mulVec, mul_assoc]
  rw [hleft]
  have hstep : v ⬝ᵥ (Q *ᵥ (D *ᵥ u)) = u ⬝ᵥ (D *ᵥ u) := by
    rw [Matrix.dotProduct_mulVec, ← Matrix.mulVec_transpose, ← hstarQ_eq, ← hu]
  rw [hstep]
  have hQQt : Q * Q.transpose = 1 := by rw [← hstarQ_eq]; exact hQQ
  have huu : u ⬝ᵥ u = v ⬝ᵥ v := by
    have hu' : u = Q.transpose *ᵥ v := by rw [hu, hstarQ_eq]
    rw [hu', Matrix.dotProduct_mulVec, Matrix.vecMul_transpose, Matrix.mulVec_mulVec, hQQt,
      Matrix.one_mulVec]
  have hbound : u ⬝ᵥ (D *ᵥ u) ≤ numAbscissa J * (u ⬝ᵥ u) := by
    unfold dotProduct
    have hterm : ∀ i, u i * (D *ᵥ u) i ≤ numAbscissa J * (u i * u i) := by
      intro i
      rw [hDdef, Matrix.mulVec_diagonal]
      have hle : hA.eigenvalues i ≤ numAbscissa J :=
        Finset.le_sup' hA.eigenvalues (Finset.mem_univ i)
      have hsq : 0 ≤ u i * u i := mul_self_nonneg (u i)
      calc u i * (hA.eigenvalues i * u i) = hA.eigenvalues i * (u i * u i) := by ring
        _ ≤ numAbscissa J * (u i * u i) := mul_le_mul_of_nonneg_right hle hsq
    calc ∑ i, u i * (D *ᵥ u) i ≤ ∑ i, numAbscissa J * (u i * u i) :=
          Finset.sum_le_sum (fun i _ => hterm i)
      _ = numAbscissa J * ∑ i, u i * u i := by rw [Finset.mul_sum]
  rwa [huu] at hbound

/-- **Tightness.** `numAbscissa J` is the *least* numerical-abscissa bound:
any other bound `w` satisfies `numAbscissa J ≤ w`. Proved at the top
eigenvector of `symPart J` (a unit vector in the orthonormal eigenbasis). -/
theorem numAbscissa_le_of_isNumAbscissaBound {J : Matrix n n ℝ} [Nonempty n] {w : ℝ}
    (hbound : IsNumAbscissaBound J w) : numAbscissa J ≤ w := by
  have hA := symPart_isHermitian J
  apply Finset.sup'_le
  intro j _
  set v : n → ℝ := (hA.eigenvectorBasis j : EuclideanSpace ℝ n) with hv
  have hvv : v ⬝ᵥ v = 1 := by
    have hnorm : ‖(hA.eigenvectorBasis j : EuclideanSpace ℝ n)‖ = 1 :=
      hA.eigenvectorBasis.orthonormal.1 j
    have hsq : ‖(hA.eigenvectorBasis j : EuclideanSpace ℝ n)‖ ^ 2 = 1 := by
      rw [hnorm]; norm_num
    rw [EuclideanSpace.norm_eq] at hsq
    rw [Real.sq_sqrt (by positivity)] at hsq
    rw [← hsq]
    unfold dotProduct
    apply Finset.sum_congr rfl
    intro i _
    rw [Real.norm_eq_abs, sq_abs, sq]
  have heig : symPart J *ᵥ v = hA.eigenvalues j • v := hA.mulVec_eigenvectorBasis j
  have hb := hbound v
  rw [dotProduct_mulVec_eq_symPart J v, heig, dotProduct_smul, smul_eq_mul, hvv, mul_one,
    mul_one] at hb
  exact hb

omit [Fintype n] [DecidableEq n] in
/-- **Symmetric-case collapse.** If `J` is already symmetric, its symmetric
part is `J` itself, so the numerical abscissa is computed directly from `J`'s
own Hermitian eigenvalues and the reactivity gap collapses (no distinct
antisymmetric contribution remains to separate `alpha` from `omega`). -/
theorem symPart_eq_self_of_isSymm {J : Matrix n n ℝ} (hJ : J.IsSymm) : symPart J = J := by
  unfold symPart
  rw [show J.transpose = J from hJ]
  ext i j
  simp only [Matrix.smul_apply, Matrix.add_apply, smul_eq_mul]
  ring

end L12b

/-! ## L12c: machine-checked non-equivalence `alpha < 0 ∧ omega > 0`

Concrete 2×2 witnesses. `shear k` is a Jordan-type shear with both
eigenvalues `-1` (triangular) but, for `k > 2`, a positive Rayleigh quotient
at `![1, 1]`. `J1`/`R1` are the simulator-frozen witnesses reused verbatim
from `results/orthogonal_dynamics_mnj_reactivity_scouting/README.md`,
`project/orthagonal_dynamics/006.md`, `claim_ledger.md:101`. -/

/-- Jordan-type shear witness `J_k = [[-1, k], [0, -1]]`. -/
def shear (k : ℝ) : Matrix (Fin 2) (Fin 2) ℝ := !![-1, k; 0, -1]

/-- All real eigenvalues of `shear k` equal `-1` (triangular structure), for
every `k`. This needs no determinant or eigenvalue machinery beyond
row-by-row elimination. -/
theorem shear_all_eigenvalues_neg (k : ℝ) :
    ∀ lam : ℝ, (∃ v : Fin 2 → ℝ, v ≠ 0 ∧ shear k *ᵥ v = lam • v) → lam = -1 := by
  rintro lam ⟨v, hv, heig⟩
  have h0 : -(v 0) + k * v 1 = lam * v 0 := by
    have h := congrFun heig 0
    simpa [shear, Matrix.mulVec, dotProduct, Fin.sum_univ_two] using h
  have h1 : -(v 1) = lam * v 1 := by
    have h := congrFun heig 1
    simpa [shear, Matrix.mulVec, dotProduct, Fin.sum_univ_two] using h
  by_cases hv1 : v 1 = 0
  · have hv0 : v 0 ≠ 0 := by
      intro hz
      exact hv (funext fun i => by fin_cases i <;> simp [hz, hv1])
    have h0' : -(v 0) = lam * v 0 := by simpa [hv1] using h0
    have hfac : (-1 - lam) * v 0 = 0 := by nlinarith [h0']
    have := (mul_eq_zero.mp hfac).resolve_right hv0
    linarith
  · have hfac : (-1 - lam) * v 1 = 0 := by nlinarith [h1]
    have := (mul_eq_zero.mp hfac).resolve_right hv1
    linarith

/-- For `k > 2`, no nonpositive `w` is a numerical-abscissa bound for
`shear k`: the witness `![1, 1]` gives a positive Rayleigh quotient although
every eigenmode decays (`shear_all_eigenvalues_neg`). -/
theorem shear_not_isNumAbscissaBound_of_nonpos (k : ℝ) (hk : 2 < k) (w : ℝ) (hw : w ≤ 0) :
    ¬ IsNumAbscissaBound (shear k) w := by
  intro hbound
  have hb := hbound ![1, 1]
  have hlhs : (![1, 1] : Fin 2 → ℝ) ⬝ᵥ (shear k *ᵥ ![1, 1]) = -2 + k := by
    simp [shear, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
    ring
  have hrhs : (![1, 1] : Fin 2 → ℝ) ⬝ᵥ (![1, 1] : Fin 2 → ℝ) = 2 := by
    simp [dotProduct, Fin.sum_univ_two]
    norm_num
  rw [hlhs, hrhs] at hb
  linarith

/-- Simulator-frozen witness `J₁ = [[-1, 6], [0, -3]]`. -/
def J1 : Matrix (Fin 2) (Fin 2) ℝ := !![-1, 6; 0, -3]

/-- The real eigenvalues of `J1` are exactly `-1` and `-3` (same spectrum as
`diag(-1, -3)`). -/
theorem J1_eigenvalue_eq (lam : ℝ) (v : Fin 2 → ℝ) (hv : v ≠ 0)
    (heig : J1 *ᵥ v = lam • v) : lam = -1 ∨ lam = -3 := by
  have h0 : -(v 0) + 6 * v 1 = lam * v 0 := by
    have h := congrFun heig 0
    simpa [J1, Matrix.mulVec, dotProduct, Fin.sum_univ_two] using h
  have h1 : -3 * v 1 = lam * v 1 := by
    have h := congrFun heig 1
    simpa [J1, Matrix.mulVec, dotProduct, Fin.sum_univ_two] using h
  by_cases hv1 : v 1 = 0
  · have hv0 : v 0 ≠ 0 := by
      intro hz
      exact hv (funext fun i => by fin_cases i <;> simp [hz, hv1])
    have h0' : -(v 0) = lam * v 0 := by simpa [hv1] using h0
    have hfac : (-1 - lam) * v 0 = 0 := by nlinarith [h0']
    have := (mul_eq_zero.mp hfac).resolve_right hv0
    left; linarith
  · have hfac : (-3 - lam) * v 1 = 0 := by nlinarith [h1]
    have := (mul_eq_zero.mp hfac).resolve_right hv1
    right; linarith

/-- No nonpositive `w` is a numerical-abscissa bound for `J1`: the witness
`![1, 1]` gives Rayleigh quotient `-1 + 6 - 3 = 2 > 0` although both
eigenvalues (`-1`, `-3`) are negative (`J1_eigenvalue_eq`). -/
theorem J1_not_isNumAbscissaBound_of_nonpos (w : ℝ) (hw : w ≤ 0) :
    ¬ IsNumAbscissaBound J1 w := by
  intro hbound
  have hb := hbound ![1, 1]
  have hlhs : (![1, 1] : Fin 2 → ℝ) ⬝ᵥ (J1 *ᵥ ![1, 1]) = 2 := by
    simp [J1, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
    norm_num
  have hrhs : (![1, 1] : Fin 2 → ℝ) ⬝ᵥ (![1, 1] : Fin 2 → ℝ) = 2 := by
    simp [dotProduct, Fin.sum_univ_two]
    norm_num
  rw [hlhs, hrhs] at hb
  linarith

/-- Simulator-frozen witness `R₁ = [[-2, -3/2], [3/2, -2]]` ("rotation is not
reactivity": a purely rotational antisymmetric part on top of a scalar
contraction). Exact rationals, not decimals. -/
def R1 : Matrix (Fin 2) (Fin 2) ℝ := !![-2, -3/2; 3/2, -2]

/-- `symPart R1` is the scalar matrix `-2 • 1`: the rotational part of `R1`
contributes nothing to the symmetric part. -/
theorem symPart_R1_eq : symPart R1 = (-2 : ℝ) • (1 : Matrix (Fin 2) (Fin 2) ℝ) := by
  have ht : R1.transpose = !![(-2 : ℝ), 3 / 2; -3 / 2, -2] := by
    ext i j
    fin_cases i <;> fin_cases j <;> simp [R1]
  have hsum : R1 + R1.transpose = !![(-4 : ℝ), 0; 0, -4] := by
    rw [ht]
    ext i j
    fin_cases i <;> fin_cases j <;> simp [R1] <;> norm_num
  show (1 / 2 : ℝ) • (R1 + R1.transpose) = (-2 : ℝ) • (1 : Matrix (Fin 2) (Fin 2) ℝ)
  rw [hsum]
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Matrix.smul_apply] <;> norm_num

/-- Consequently `-2` is a (tight, in fact exact) numerical-abscissa bound
for `R1`, matching `alpha = omega = -2` for this witness. -/
theorem isNumAbscissaBound_R1 : IsNumAbscissaBound R1 (-2) := by
  intro v
  rw [dotProduct_mulVec_eq_symPart R1 v, symPart_R1_eq, Matrix.smul_mulVec, Matrix.one_mulVec,
    dotProduct_smul, smul_eq_mul]

/-- The antisymmetric part of `R1` is nonzero: `R1` is genuinely non-normal
even though its symmetric part is a pure scalar contraction. -/
theorem antisymPart_R1_ne_zero : antisymPart R1 ≠ 0 := by
  intro h
  have h01 : antisymPart R1 0 1 = (0 : Matrix (Fin 2) (Fin 2) ℝ) 0 1 := by rw [h]
  simp only [antisymPart, R1, Matrix.smul_apply, Matrix.sub_apply, Matrix.transpose_apply,
    Matrix.zero_apply, smul_eq_mul] at h01
  norm_num at h01

/-! ## L12d: discrete-time analogue — spectral radius vs finite-time peak gain

Discrete witness `A = [[1/2, c], [0, 1/2]]`: both eigenvalues are `1/2 < 1`
(eigenvalue-driven asymptotic decay), yet for `c ≥ 1` a single step from a
unit vector can more than double its squared norm. This certifies
"eigenvalue-driven decay does not license finite-time gain ≤ 1". -/

/-- Discrete-time shear witness `A = [[1/2, c], [0, 1/2]]`. -/
def discreteShear (c : ℝ) : Matrix (Fin 2) (Fin 2) ℝ := !![1/2, c; 0, 1/2]

/-- All real eigenvalues of `discreteShear c` equal `1/2`. -/
theorem discreteShear_all_eigenvalues_eq_half (c : ℝ) :
    ∀ lam : ℝ, (∃ v : Fin 2 → ℝ, v ≠ 0 ∧ discreteShear c *ᵥ v = lam • v) → lam = 1 / 2 := by
  rintro lam ⟨v, hv, heig⟩
  have h0 : (1 / 2) * v 0 + c * v 1 = lam * v 0 := by
    have h := congrFun heig 0
    simpa [discreteShear, Matrix.mulVec, dotProduct, Fin.sum_univ_two] using h
  have h1 : (1 / 2) * v 1 = lam * v 1 := by
    have h := congrFun heig 1
    simpa [discreteShear, Matrix.mulVec, dotProduct, Fin.sum_univ_two] using h
  by_cases hv1 : v 1 = 0
  · have hv0 : v 0 ≠ 0 := by
      intro hz
      exact hv (funext fun i => by fin_cases i <;> simp [hz, hv1])
    have h0' : (1 / 2) * v 0 = lam * v 0 := by simpa [hv1] using h0
    have hfac : (1 / 2 - lam) * v 0 = 0 := by nlinarith [h0']
    have := (mul_eq_zero.mp hfac).resolve_right hv0
    linarith
  · have hfac : (1 / 2 - lam) * v 1 = 0 := by nlinarith [h1]
    have := (mul_eq_zero.mp hfac).resolve_right hv1
    linarith

/-- For `c ≥ 1`, `discreteShear c` maps some unit vector to a vector of
squared norm `> 1` in a single step, although every eigenvalue is `1/2 < 1`:
eigenvalue-driven asymptotic decay does not bound the finite-time peak gain. -/
theorem discreteShear_finite_time_gain_gt_one (c : ℝ) (hc : 1 ≤ c) :
    ∃ v : Fin 2 → ℝ, v ⬝ᵥ v = 1 ∧
      1 < (discreteShear c *ᵥ v) ⬝ᵥ (discreteShear c *ᵥ v) := by
  refine ⟨![0, 1], ?_, ?_⟩
  · simp [dotProduct, Fin.sum_univ_two]
  · have hAv : discreteShear c *ᵥ (![0, 1] : Fin 2 → ℝ) = ![c, 1 / 2] := by
      ext i
      fin_cases i <;>
        simp [discreteShear, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
    rw [hAv]
    simp only [dotProduct, Fin.sum_univ_two, Matrix.cons_val_zero, Matrix.cons_val_one]
    nlinarith [hc]

end

end NoeticDiffusion
