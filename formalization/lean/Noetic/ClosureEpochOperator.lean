import Mathlib.LinearAlgebra.Matrix.Determinant.Basic
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.Data.Matrix.Block
import Mathlib.Analysis.Calculus.Deriv.Basic
import Noetic.SlowBranchModel

/-!
# L20a–c: closure-epoch singularity propagation, clamp derivative, lag-embedding shift

NDT source: `project/lean/fable_ideas/10_closure_epoch_rank_and_observability_levels.md`,
`## L20a — Singular factor ⇒ singular product`, `## L20b — Clamp derivative is zero on
the saturated set`, `## L20c — Lag-embedding shift structure`. These formalize failure
diagnoses from the simulator articles: `dev_canonical`'s composed epoch operator
`A_epoch = J_{H-1}⋯J_0` was rank-deficient in every sample because `_clamp01`
saturation makes a state derivative exactly zero, giving a zero Jacobian row and a
singular product (`results/m3_e038r_cue_inclusive_epoch_audit/zero_row_diagnostic.md`;
`research_map.md:108-134`); *Separable Levels of Observability*'s lag-embedded chart has
a response block that is structurally null with shift rows that are the identity for
every dynamics (typ ~85-100, ~260).

## Claim boundary

Finite real matrix algebra only. `L20a` states determinant/row/column singularity
propagation for square (`det`) and rectangular (row/column) real matrices — no rank
tolerance, no SVD threshold, no probability. `L20b` proves `deriv` facts for L18's public
`clip lo hi x := max lo (min hi x)` (`Noetic/SlowBranchModel.lean`) **only on the open
saturated sets** `{x | x > hi}` and `{x | x < lo}` and on the open interior
`{x | lo < x < hi}`; boundary points `x = lo`, `x = hi` are excluded (the one-sided
derivative does not exist there in general) and this is not claimed. An earlier draft of
this module used a private local copy `L20_clip` of that definition because L18 was not
yet built in that run; now that `Noetic.SlowBranchModel` is a built dependency, `L20b`
imports and uses the shared public `clip` directly, and no private copy remains. `L20c`
proves an exact block-algebra identity for a **two-block** lag-embedding
shift operator on `n ⊕ n` (the idea file explicitly permits reducing general lag depth
`k` to two blocks for bounded effort); the resulting nilpotency degree is `2`, not the
`3` suggested by the three-block informal sketch in the idea file — this is recorded
below as a deviation, not silently narrowed. No ODE, no numerical clamp threshold
(`1e-8`), no empirical epoch-operator claim. This module is simulator-internal: no S7
inventory rows are added for it (per the idea file's acceptance-gate note).
-/

namespace NoeticDiffusion

open scoped Matrix

/-! ## L20a: singular factor ⇒ singular product -/

section L20a

variable {n : Type*} [Fintype n] [DecidableEq n]

/-- If the left factor of a square real matrix product has determinant zero,
so does the product (`Matrix.det_mul`). -/
theorem L20_det_mul_eq_zero_of_det_left_eq_zero (W X : Matrix n n ℝ) (hW : W.det = 0) :
    (W * X).det = 0 := by
  rw [Matrix.det_mul, hW, zero_mul]

/-- If the right factor of a square real matrix product has determinant zero,
so does the product. -/
theorem L20_det_mul_eq_zero_of_det_right_eq_zero (W X : Matrix n n ℝ) (hX : X.det = 0) :
    (W * X).det = 0 := by
  rw [Matrix.det_mul, hX, mul_zero]

/-- A real square matrix with determinant zero is not a unit. -/
theorem L20_not_isUnit_of_det_eq_zero {A : Matrix n n ℝ} (hA : A.det = 0) : ¬ IsUnit A := by
  rw [Matrix.isUnit_iff_isUnit_det, hA]
  exact not_isUnit_zero

/-- Singular left factor ⇒ singular product, as a non-invertibility statement. -/
theorem L20_not_isUnit_mul_of_det_left_eq_zero {W : Matrix n n ℝ} (X : Matrix n n ℝ)
    (hW : W.det = 0) : ¬ IsUnit (W * X) :=
  L20_not_isUnit_of_det_eq_zero (L20_det_mul_eq_zero_of_det_left_eq_zero W X hW)

/-- Singular right factor ⇒ singular product, as a non-invertibility statement. -/
theorem L20_not_isUnit_mul_of_det_right_eq_zero (W : Matrix n n ℝ) {X : Matrix n n ℝ}
    (hX : X.det = 0) : ¬ IsUnit (W * X) :=
  L20_not_isUnit_of_det_eq_zero (L20_det_mul_eq_zero_of_det_right_eq_zero W X hX)

omit [Fintype n] [DecidableEq n] in
/-- A zero row of the left factor propagates to a zero row of the product:
if row `i` of `W` vanishes as a function, so does row `i` of `W * X`. Stated
for rectangular `W : Matrix n l ℝ`, `X : Matrix l m ℝ`. -/
theorem L20_zero_row_mul {l m : Type*} [Fintype l] {W : Matrix n l ℝ} {X : Matrix l m ℝ}
    {i : n} (hWi : W i = 0) : (W * X) i = 0 := by
  funext j
  have h0 : ∀ k, W i k = 0 := fun k => congrFun hWi k
  simp [Matrix.mul_apply, h0]

omit [Fintype n] [DecidableEq n] in
/-- A zero column of the right factor propagates to a zero entry of the
product in that column, for every row — the column companion of
`L20_zero_row_mul`. -/
theorem L20_zero_col_mul {l m : Type*} [Fintype l] (W : Matrix n l ℝ) {X : Matrix l m ℝ}
    {j : m} (hXj : ∀ k, X k j = 0) (i : n) : (W * X) i j = 0 := by
  simp [Matrix.mul_apply, hXj]

/-- Square case: a zero row of the left factor forces the product to be
singular. -/
theorem L20_det_mul_eq_zero_of_row_eq_zero {W X : Matrix n n ℝ} {i : n} (hWi : ∀ j, W i j = 0) :
    (W * X).det = 0 :=
  L20_det_mul_eq_zero_of_det_left_eq_zero W X (Matrix.det_eq_zero_of_row_eq_zero i hWi)

/-- The composite closure-epoch operator `E := Wout * D * Win` (output map,
diagonal/gain stage, input map). -/
def L20_closureEpoch (Wout D Win : Matrix n n ℝ) : Matrix n n ℝ := Wout * D * Win

/-- A zero row of `Wout` propagates through both factors to the same zero row
of the composite closure-epoch operator `E = Wout * D * Win`, and (square
case) forces `det E = 0`. This is the exact "clamp saturation ⇒ singular
composed epoch operator" diagnosis. -/
theorem L20_closureEpoch_zero_row_and_det_eq_zero
    (Wout D Win : Matrix n n ℝ) {i : n} (hi : Wout i = 0) :
    (L20_closureEpoch Wout D Win) i = 0 ∧ (L20_closureEpoch Wout D Win).det = 0 := by
  have h1 : (Wout * D) i = 0 := L20_zero_row_mul hi
  have h2 : (L20_closureEpoch Wout D Win) i = 0 := L20_zero_row_mul h1
  exact ⟨h2, Matrix.det_eq_zero_of_row_eq_zero i (fun j => congrFun h2 j)⟩

end L20a

/-! ## L20b: clamp derivative is zero on the saturated open sets -/

section L20b

/-- On the open upper-saturated set `{x | hi < x}`, L18's public `clip lo hi`
(`Noetic.SlowBranchModel.clip`) is locally constant (equal to `hi`), so its
derivative is zero there. -/
theorem L20_deriv_clip_eq_zero_of_gt {lo hi x : ℝ} (hlohi : lo ≤ hi) (hx : hi < x) :
    deriv (clip lo hi) x = 0 := by
  have heq : clip lo hi =ᶠ[nhds x] (fun _ => hi) := by
    filter_upwards [Ioi_mem_nhds hx] with y hy
    exact clip_eq_hi_of_ge lo hi y hlohi hy.le
  rw [heq.deriv_eq]
  simp

/-- On the open lower-saturated set `{x | x < lo}`, `clip lo hi` is locally
constant (equal to `lo`), so its derivative is zero there. -/
theorem L20_deriv_clip_eq_zero_of_lt {lo hi x : ℝ} (hlohi : lo ≤ hi) (hx : x < lo) :
    deriv (clip lo hi) x = 0 := by
  have heq : clip lo hi =ᶠ[nhds x] (fun _ => lo) := by
    filter_upwards [Iio_mem_nhds hx] with y hy
    exact clip_eq_lo_of_le lo hi y hlohi hy.le
  rw [heq.deriv_eq]
  simp

/-- On the open interior `{x | lo < x < hi}`, `clip lo hi` agrees with the
identity, so its derivative is `1`. -/
theorem L20_deriv_clip_eq_one_of_mem_Ioo {lo hi x : ℝ} (hx1 : lo < x) (hx2 : x < hi) :
    deriv (clip lo hi) x = 1 := by
  have heq : clip lo hi =ᶠ[nhds x] id := by
    filter_upwards [Ioo_mem_nhds hx1 hx2] with y hy
    exact clip_of_mem lo hi y hy.1.le hy.2.le
  rw [heq.deriv_eq]
  simp

end L20b

/-! ## L20c: lag-embedding shift structure (two blocks) -/

section L20c

variable {n : Type*} [Fintype n] [DecidableEq n]

/-- Two-block lag-embedding one-step operator: on state `(a, b)` (most
recent, previous lag), maps to `(Aresp *ᵥ a + Bresp *ᵥ b, a)` — i.e. the
Jacobian block form `[[Aresp, Bresp], [1, 0]]` for arbitrary response blocks
`Aresp`, `Bresp`. -/
def L20_lagShift (Aresp Bresp : Matrix n n ℝ) : Matrix (n ⊕ n) (n ⊕ n) ℝ :=
  Matrix.fromBlocks Aresp Bresp 1 0

/-- The shift rows are the identity **regardless of the dynamics**: for any
response blocks `Aresp`, `Bresp`, applying `L20_lagShift` to `(a, b)` always
places the old top block `a` unchanged into the new bottom block — the exact
sense in which "the shift rows of the block Jacobian are the identity
regardless of dynamics". -/
theorem L20_lagShift_mulVec (Aresp Bresp : Matrix n n ℝ) (a b : n → ℝ) :
    L20_lagShift Aresp Bresp *ᵥ Sum.elim a b
      = Sum.elim (Aresp *ᵥ a + Bresp *ᵥ b) a := by
  unfold L20_lagShift
  rw [Matrix.fromBlocks_mulVec]
  simp

/-- The **pure** shift operator: both response blocks vanish, so the whole
top block row of the Jacobian is structurally null. -/
def L20_lagShiftPure (n : Type*) [Fintype n] [DecidableEq n] : Matrix (n ⊕ n) (n ⊕ n) ℝ :=
  L20_lagShift (0 : Matrix n n ℝ) 0

/-- If the response blocks vanish, the two-block shift register empties after
two compositions: `L20_lagShiftPure ^ 2 = 0`. This is the two-block instance
of "a null response block makes the observed operator structurally null"
(the general `k`-block shift register is nilpotent of degree `k`; the idea
file's three-block sketch is reduced to two blocks here, giving nilpotency
degree `2` rather than `3` — see DEVIATIONS in the implementer report). -/
theorem L20_lagShiftPure_sq_eq_zero :
    L20_lagShiftPure n * L20_lagShiftPure n = 0 := by
  simp [L20_lagShiftPure, L20_lagShift, Matrix.fromBlocks_multiply]

end L20c

end NoeticDiffusion
