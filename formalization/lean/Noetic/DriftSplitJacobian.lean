import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.LinearAlgebra.Matrix.Symmetric
import Mathlib.Analysis.Calculus.Deriv.Pow
import Mathlib.Analysis.Calculus.Deriv.Add
import Noetic.JacobianReactivity
import Noetic.AccessOperators

/-!
# L17: drift split, mobility tensor, and "Jacobian asymmetry is not evidence of
non-conservative flow"

This module formalizes the manuscript's warning that a state-dependent (or even
constant, anisotropic) mobility tensor `M` can by itself make the drift Jacobian
`J` non-symmetric, so that `J ≠ Jᵗ` is *not* sufficient evidence of a
non-conservative mechanism `u_nc ≠ 0`.

NDT source: `articles/NoeticDiffusionTheory_v2/Noetic Diffusion Theory - Neural
State, Dynamical Accessibility, and the Geometry of Possible Futures.typ`,
lines 414-431 (drift split `b = -M ∇V + u_nc`, remainder
`J = -G ∇²Φ - R`, `R_ij = Σ_k (∂_j G_ik)(∂_k Φ)`, and "Jacobian asymmetry is
therefore not sufficient evidence for a non-conservative mechanism"), 547-548
(`Ω`), 764-767 (scalar contraction); `articles/aa_basicinfo/ndt_compact_summary.md`
§1 "DRIFT SPLIT", §4 "RELATION TO POTENTIAL CURVATURE", §9; and
`project/lean/fable_ideas/07_drift_split_mobility_nonidentifiability.md`.

## Claim boundary

This module proves four disjoint algebraic/elementary-calculus facts about
real square matrices and vectors on `Fin 2`:

* **L17a (constant mobility can break symmetry).** For symmetric `M`, `H`, the
  product `M * H` is symmetric iff `M` and `H` commute
  (`mulIsSymm_iff_commute`), and in general its antisymmetric part is exactly
  `(M*H - H*M)/2` (`mulIsSymm_antisymPart_eq`, reusing `Noetic.JacobianReactivity`'s
  `antisymPart`). The `Noetic.AccessOperators` congruence witness
  `M = diag(2,1)`, `H = [[1,1],[1,1]]` gives a symmetric, non-commuting pair
  with nonzero antisymmetric product part
  (`mulIsSymm_witness_antisymPart_ne_zero`), i.e. an anisotropic-constant-mobility
  gradient system (`u_nc = 0`) with `Ω ≠ 0`. The positive complement,
  isotropic (scalar) mobility `M = c • 1`, is always symmetric and contributes
  zero antisymmetric part for any symmetric `H`
  (`mobility_isotropic_isSymm`, `mobility_isotropic_antisymPart_eq_zero`),
  matching the manuscript's "a scalar contraction cannot produce
  `alpha < 0 < omega`" remark for gradient systems (lines 764-767).
* **L17b (bookkeeping algebra of the remainder).** `driftSplitJacobian M H R :=
  -(M*H) + R` satisfies `R = driftSplitJacobian M H R + M*H`
  (`driftSplitJacobian_remainder_eq`) and the trivial restatement
  `driftSplitJacobian_isSymm_iff`; its antisymmetric part is exactly
  `antisymPart R - antisymPart (M*H)` (`driftSplitJacobian_antisymPart_eq`), so
  when `M*H` is symmetric (e.g. `M`, `H` commute) the antisymmetric part of the
  drift Jacobian equals that of the remainder alone
  (`driftSplitJacobian_antisymPart_eq_of_mulIsSymm`): under a commuting
  mobility the non-conservative remainder alone carries the rotational part.
  The index-level remainder `remainder dG gradΦ i j := Σ_k (dG j) i k * gradΦ k`
  (`R_ij = Σ_k (∂_j G_ik)(∂_k Φ)`) satisfies the pinned sign/index bookkeeping
  identity `remainder_jacobian_eq` and vanishes when `dG = 0` (constant
  mobility, `remainder_eq_zero_of_dG_eq_zero`) or when `gradΦ = 0` (a critical
  point of `Φ`, `remainder_eq_zero_of_gradPhi_eq_zero`) — in either case
  `J ≈ -G∇²Φ` is exact, not approximate.
* **L17c (non-identifiability of the drift split).** For `driftSplitB M g u :=
  -(M *ᵥ g) + u`, the pair `(M, u)` is not identifiable from `(b, g)` alone: an
  explicit `Fin 2` witness with `M₁ = 1 ≠ M₂ = 2 • 1` and adjusted `u₁ ≠ u₂`
  produces the identical `b` for the same `g`
  (`driftSplit_nonidentifiable`, built from `driftSplit_witness_same_b` and
  `driftSplit_witnessM1_ne_witnessM2`). The positive complement,
  `driftSplitB_u_eq`, shows that if `M` (hence the split point) is fixed, the
  remainder `u` *is* determined exactly by `b`, `g`, `M`: `u = b + M *ᵥ g`.
* **L17d (polynomial witness with genuine derivatives).** For `Φ(x) =
  (x₀²+x₁²)/2`, `G(x) = diag(1+x₁², 1)` (`L17_polyG`, diagonal entries proved
  positive for every `x` by `L17_polyG_diag_pos`) and `∇Φ(x) = x`
  (`L17_polyGradPhi`), the drift `L17_polyB x := -(G(x) *ᵥ ∇Φ(x))`
  (`L17_polyB_eq_neg_mulVec`) has zero non-conservative remainder by
  construction. Its two off-diagonal mixed partials at `x = (1,1)` are
  computed as genuine one-variable derivatives along coordinate slices via
  `deriv`/`HasDerivAt` (`Function.update` freezing the other coordinate):
  `∂b₀/∂x₁ = -2` (`L17_polyB_deriv_x1_component0`) and `∂b₁/∂x₀ = 0`
  (`L17_polyB_deriv_x0_component1`), hence unequal (`L17_polyB_partials_ne`).
  These machine-checked derivative values coincide with the corresponding
  entries of the explicit polynomial Jacobian `L17_polyJacobian x =
  [[-(1+x₁²), -2x₀x₁],[0,-1]]` (`L17_polyJacobian_apply_01_eq_deriv`,
  `L17_polyJacobian_apply_10_eq_deriv`), whose asymmetry at `(1,1)` is proved
  directly (`L17_polyJacobian_not_isSymm`). This exhibits a smooth,
  potential-driven drift with positive-definite state-dependent mobility, zero
  non-conservative residual, and a non-symmetric Jacobian.

Out of scope: no Riemannian geometry, no Itô correction, no general Clairaut/
Schwarz symmetry-of-mixed-partials theorem connecting L17d's asymmetry to "not
the gradient of any C² potential" (that implication is the informal
justification for the witness, not machine-checked here — only the two
one-variable slice derivatives and the explicit polynomial Jacobian's entries
are); no full multivariable `fderiv`/`HasFDerivAt` computation on `b` (route
(i) of the idea file); no `Matrix.PosDef` instance for `L17_polyG` (only
positivity of its diagonal entries); no claim about identifiability from real
data beyond the finite-dimensional algebraic non-identifiability witness; no
MNJ estimate or biological interpretation.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]

/-! ## L17a: constant mobility can break symmetry -/

/-- **Symmetric-product criterion.** For symmetric `M`, `H`, the product
`M * H` is symmetric iff `M` and `H` commute. -/
theorem mulIsSymm_iff_commute (M H : Matrix n n ℝ) (hM : M.IsSymm) (hH : H.IsSymm) :
    (M * H).IsSymm ↔ M * H = H * M := by
  constructor
  · intro h
    have ht : (M * H).transpose = M * H := h
    rw [Matrix.transpose_mul, show H.transpose = H from hH, show M.transpose = M from hM] at ht
    exact ht.symm
  · intro h
    show (M * H).transpose = M * H
    rw [Matrix.transpose_mul, show H.transpose = H from hH, show M.transpose = M from hM, ← h]

/-- **Corollary.** For symmetric `M`, `H` (no commuting assumption needed), the
antisymmetric part of the product `M * H` is exactly `(M*H - H*M)/2`. -/
theorem mulIsSymm_antisymPart_eq (M H : Matrix n n ℝ) (hM : M.IsSymm) (hH : H.IsSymm) :
    antisymPart (M * H) = (1 / 2 : ℝ) • (M * H - H * M) := by
  show (1 / 2 : ℝ) • (M * H - (M * H).transpose) = (1 / 2 : ℝ) • (M * H - H * M)
  rw [Matrix.transpose_mul, show H.transpose = H from hH, show M.transpose = M from hM]

/-- The `Noetic.AccessOperators` congruence witness `M = diag(2,1) ≻ 0`,
`H = [[1,1],[1,1]] ⪰ 0` (both symmetric) does not commute: reuses
`gating_congruenceWitness_mul_not_isSymm` via `mulIsSymm_iff_commute`. -/
theorem mulIsSymm_witness_not_commute :
    gating_congruenceWitnessM * gating_congruenceWitnessH ≠
      gating_congruenceWitnessH * gating_congruenceWitnessM := by
  intro h
  exact gating_congruenceWitness_mul_not_isSymm
    ((mulIsSymm_iff_commute gating_congruenceWitnessM gating_congruenceWitnessH
        gating_congruenceWitnessM_isSymm gating_congruenceWitnessH_isSymm).2 h)

/-- Consequently the rotational proxy `Ω = antisymPart (M * H)` is nonzero for
this witness: an anisotropic constant-mobility gradient flow (`u_nc = 0`) with
a genuinely non-symmetric Jacobian. -/
theorem mulIsSymm_witness_antisymPart_ne_zero :
    antisymPart (gating_congruenceWitnessM * gating_congruenceWitnessH) ≠ 0 := by
  rw [mulIsSymm_antisymPart_eq gating_congruenceWitnessM gating_congruenceWitnessH
    gating_congruenceWitnessM_isSymm gating_congruenceWitnessH_isSymm]
  intro h
  have hx : gating_congruenceWitnessM * gating_congruenceWitnessH -
      gating_congruenceWitnessH * gating_congruenceWitnessM = 0 := by
    have h2 : (2 : ℝ) • ((1 / 2 : ℝ) •
        (gating_congruenceWitnessM * gating_congruenceWitnessH -
          gating_congruenceWitnessH * gating_congruenceWitnessM)) =
        (2 : ℝ) • (0 : Matrix (Fin 2) (Fin 2) ℝ) := by rw [h]
    rwa [smul_smul, show (2 : ℝ) * (1 / 2 : ℝ) = 1 by norm_num, one_smul, smul_zero] at h2
  exact mulIsSymm_witness_not_commute (sub_eq_zero.mp hx)

omit [Fintype n] in
/-- A symmetric matrix has zero antisymmetric part (reuses
`Noetic.JacobianReactivity`'s `symPart_add_antisymPart`/`symPart_eq_self_of_isSymm`). -/
private lemma antisymPart_eq_zero_of_isSymm {J : Matrix n n ℝ} (hJ : J.IsSymm) :
    antisymPart J = 0 := by
  have hsp := symPart_add_antisymPart J
  rw [symPart_eq_self_of_isSymm hJ] at hsp
  have h2 : J + antisymPart J = J + 0 := by rw [hsp, add_zero]
  exact add_left_cancel h2

section Isotropic

variable [DecidableEq n]

/-- **Positive complement.** Isotropic (scalar) mobility `M = c • 1` always
commutes with any `H`, so `(c • 1) * H` inherits `H`'s symmetry exactly. -/
theorem mobility_isotropic_isSymm (c : ℝ) (H : Matrix n n ℝ) (hH : H.IsSymm) :
    ((c • (1 : Matrix n n ℝ)) * H).IsSymm := by
  have heq : (c • (1 : Matrix n n ℝ)) * H = c • H := by
    rw [Matrix.smul_mul, one_mul]
  show ((c • (1 : Matrix n n ℝ)) * H).transpose = (c • (1 : Matrix n n ℝ)) * H
  rw [heq, Matrix.transpose_smul, show H.transpose = H from hH]

/-- Consequently a scalar mobility contributes zero antisymmetric part for any
symmetric `H`: `Ω = 0` exactly, matching the manuscript's "a scalar
contraction cannot produce `alpha < 0 < omega`" remark (lines 764-767) at the
gradient-system level. -/
theorem mobility_isotropic_antisymPart_eq_zero (c : ℝ) (H : Matrix n n ℝ) (hH : H.IsSymm) :
    antisymPart ((c • (1 : Matrix n n ℝ)) * H) = 0 :=
  antisymPart_eq_zero_of_isSymm (mobility_isotropic_isSymm c H hH)

end Isotropic

/-! ## L17b: bookkeeping algebra of the metric-variation remainder -/

/-- The drift Jacobian `J = -(M*H) + R` for a mobility `M`, curvature `H`, and
non-conservative remainder `R`. -/
def driftSplitJacobian (M H R : Matrix n n ℝ) : Matrix n n ℝ := -(M * H) + R

/-- `R` is recovered exactly from `J`, `M`, `H`: `R = J + M*H`. -/
theorem driftSplitJacobian_remainder_eq (M H R : Matrix n n ℝ) :
    R = driftSplitJacobian M H R + M * H := by
  unfold driftSplitJacobian
  abel

/-- Trivial restatement of `driftSplitJacobian_remainder_eq` at the level of
`IsSymm`: `R` is symmetric iff `J + M*H` is. -/
theorem driftSplitJacobian_isSymm_iff (M H R : Matrix n n ℝ) :
    R.IsSymm ↔ (driftSplitJacobian M H R + M * H).IsSymm := by
  constructor
  · intro h; rwa [← driftSplitJacobian_remainder_eq]
  · intro h; rwa [← driftSplitJacobian_remainder_eq] at h

/-- The antisymmetric part of the drift Jacobian splits exactly as the
antisymmetric part of the remainder minus that of the mobility-curvature
product: `antisymPart J = antisymPart R - antisymPart (M*H)`. -/
theorem driftSplitJacobian_antisymPart_eq (M H R : Matrix n n ℝ) :
    antisymPart (driftSplitJacobian M H R) = antisymPart R - antisymPart (M * H) := by
  unfold driftSplitJacobian antisymPart
  ext i j
  simp only [Matrix.sub_apply, Matrix.add_apply, Matrix.neg_apply, Matrix.smul_apply,
    Matrix.transpose_apply, smul_eq_mul]
  ring

/-- **Commuting-mobility corollary.** If `M * H` is symmetric (in particular
if `M`, `H` commute), the antisymmetric part of the drift Jacobian equals that
of the remainder alone: under a commuting mobility the non-conservative
remainder alone carries the rotational part. -/
theorem driftSplitJacobian_antisymPart_eq_of_mulIsSymm (M H R : Matrix n n ℝ)
    (hMH : (M * H).IsSymm) :
    antisymPart (driftSplitJacobian M H R) = antisymPart R := by
  rw [driftSplitJacobian_antisymPart_eq, antisymPart_eq_zero_of_isSymm hMH, sub_zero]

/-- The index-level metric-variation remainder `R_ij = Σ_k (∂_j G_ik)(∂_k Φ)`,
given the state-dependent-mobility derivative field `dG j = ∂_j G` and the
gradient `gradΦ = ∇Φ`, as pure matrix/vector algebra (no calculus). -/
def remainder (dG : n → Matrix n n ℝ) (gradΦ : n → ℝ) : Matrix n n ℝ :=
  Matrix.of fun i j => ∑ k, dG j i k * gradΦ k

/-- Bookkeeping identity pinning the sign/index convention of `remainder`
against the explicit sum form of `-(G*H)`. -/
theorem remainder_jacobian_eq (G H : Matrix n n ℝ) (dG : n → Matrix n n ℝ) (gradΦ : n → ℝ) :
    -(G * H) - remainder dG gradΦ =
      Matrix.of fun i j => -(∑ k, G i k * H k j) - ∑ k, dG j i k * gradΦ k := by
  ext i j
  simp [remainder, Matrix.of_apply, Matrix.mul_apply, Matrix.sub_apply, Matrix.neg_apply]

/-- Constant mobility (`dG = 0`) makes the remainder vanish. -/
theorem remainder_eq_zero_of_dG_eq_zero (dG : n → Matrix n n ℝ) (gradΦ : n → ℝ)
    (h : dG = fun _ => (0 : Matrix n n ℝ)) : remainder dG gradΦ = 0 := by
  subst h
  ext i j
  simp [remainder, Matrix.of_apply]

/-- At a critical point of `Φ` (`gradΦ = 0`) the remainder vanishes even for
state-dependent mobility: `J ≈ -G∇²Φ` is exact there. -/
theorem remainder_eq_zero_of_gradPhi_eq_zero (dG : n → Matrix n n ℝ) (gradΦ : n → ℝ)
    (h : gradΦ = 0) : remainder dG gradΦ = 0 := by
  subst h
  ext i j
  simp [remainder, Matrix.of_apply]

/-! ## L17c: non-identifiability of the drift split -/

/-- The observed drift `b = -(M *ᵥ g) + u` from a mobility `M`, potential
gradient `g = ∇V`, and non-conservative field `u`. -/
def driftSplitB (M : Matrix n n ℝ) (g u : n → ℝ) : n → ℝ := -(M *ᵥ g) + u

/-- **Positive complement.** If the mobility `M` is fixed (known), the
non-conservative remainder `u` *is* determined exactly by the observed drift
`b` and the potential gradient `g`: `u = b + M *ᵥ g`. -/
theorem driftSplitB_u_eq (M : Matrix n n ℝ) (g u : n → ℝ) :
    u = driftSplitB M g u + M *ᵥ g := by
  funext i
  simp only [driftSplitB, Pi.add_apply, Pi.neg_apply]
  ring

/-- Non-identifiability witness mobility `M₁ = 1` (isotropic, unit gain). -/
def driftSplit_witnessM1 : Matrix (Fin 2) (Fin 2) ℝ := (1 : Matrix (Fin 2) (Fin 2) ℝ)

/-- Non-identifiability witness mobility `M₂ = 2 • 1` (isotropic, double
gain), distinct from `M₁`. -/
def driftSplit_witnessM2 : Matrix (Fin 2) (Fin 2) ℝ := (2 : ℝ) • (1 : Matrix (Fin 2) (Fin 2) ℝ)

/-- Non-identifiability witness potential gradient `g = ![1, 1]`. -/
def driftSplit_witnessG : Fin 2 → ℝ := ![1, 1]

/-- Non-identifiability witness non-conservative field `u₁ = ![0, 0]` paired
with `M₁`. -/
def driftSplit_witnessU1 : Fin 2 → ℝ := ![0, 0]

/-- Non-identifiability witness non-conservative field `u₂ = ![1, 1]`,
adjusted so that `M₂` together with `u₂` reproduces the same drift `b` as
`M₁` together with `u₁` for the shared `g`. -/
def driftSplit_witnessU2 : Fin 2 → ℝ := ![1, 1]

/-- The two witness mobilities are distinct. -/
theorem driftSplit_witnessM1_ne_witnessM2 : driftSplit_witnessM1 ≠ driftSplit_witnessM2 := by
  intro h
  have h00 : (driftSplit_witnessM1 : Matrix (Fin 2) (Fin 2) ℝ) 0 0
      = driftSplit_witnessM2 0 0 := by rw [h]
  simp only [driftSplit_witnessM1, driftSplit_witnessM2, Matrix.one_apply_eq,
    Matrix.smul_apply, smul_eq_mul, mul_one] at h00
  norm_num at h00

/-- The two witness pairs `(M₁, u₁)` and `(M₂, u₂)` produce the identical
observed drift `b` for the shared `g`. -/
theorem driftSplit_witness_same_b :
    driftSplitB driftSplit_witnessM1 driftSplit_witnessG driftSplit_witnessU1 =
    driftSplitB driftSplit_witnessM2 driftSplit_witnessG driftSplit_witnessU2 := by
  unfold driftSplitB driftSplit_witnessM1 driftSplit_witnessM2
  rw [Matrix.one_mulVec, Matrix.smul_mulVec, Matrix.one_mulVec]
  funext i
  fin_cases i <;> simp [driftSplit_witnessG, driftSplit_witnessU1, driftSplit_witnessU2] <;>
    norm_num

/-- **Non-identifiability of the drift split.** There exist two distinct
mobility/non-conservative-field pairs `(M₁,u₁) ≠ (M₂,u₂)` producing the same
observed drift `b` for the same potential gradient `g`: the split
`(M, u)` is not identifiable from `(b, g)` alone. -/
theorem driftSplit_nonidentifiable :
    ∃ (M₁ M₂ : Matrix (Fin 2) (Fin 2) ℝ) (u₁ u₂ g : Fin 2 → ℝ),
      M₁ ≠ M₂ ∧ driftSplitB M₁ g u₁ = driftSplitB M₂ g u₂ :=
  ⟨driftSplit_witnessM1, driftSplit_witnessM2, driftSplit_witnessU1, driftSplit_witnessU2,
    driftSplit_witnessG, driftSplit_witnessM1_ne_witnessM2, driftSplit_witness_same_b⟩

/-! ## L17d: polynomial witness with genuine derivatives

`Φ(x) = (x₀² + x₁²)/2`, `G(x) = diag(1 + x₁², 1)` (positive-definite diagonal
entries for every `x`), `b(x) = -(G(x) *ᵥ ∇Φ(x))`. The two off-diagonal mixed
partials of `b` at `x = (1,1)` are computed as genuine `deriv` values along
coordinate slices and shown to disagree, matching the explicit polynomial
Jacobian `[[-(1+x₁²), -2x₀x₁],[0,-1]]`'s asymmetry there. -/

/-- The drift field `b(x) = ![-(1+x₁²)x₀, -x₁]`. -/
def L17_polyB (x : Fin 2 → ℝ) : Fin 2 → ℝ := ![-(1 + (x 1) ^ 2) * (x 0), -(x 1)]

/-- The state-dependent mobility `G(x) = diag(1 + x₁², 1)`. -/
def L17_polyG (x : Fin 2 → ℝ) : Matrix (Fin 2) (Fin 2) ℝ := !![1 + (x 1) ^ 2, 0; 0, 1]

/-- The gradient `∇Φ(x) = x` of `Φ(x) = (x₀² + x₁²)/2`. -/
def L17_polyGradPhi (x : Fin 2 → ℝ) : Fin 2 → ℝ := ![x 0, x 1]

/-- `b(x)` is exactly `-(G(x) *ᵥ ∇Φ(x))`: zero non-conservative remainder by
construction. -/
theorem L17_polyB_eq_neg_mulVec (x : Fin 2 → ℝ) :
    L17_polyB x = -(L17_polyG x *ᵥ L17_polyGradPhi x) := by
  funext i
  fin_cases i <;> simp [L17_polyB, L17_polyG, L17_polyGradPhi]
  ring

/-- `G(x)`'s diagonal entries are strictly positive for every `x` (the sense
in which `G(x)` is positive-definite here; no `Matrix.PosDef` instance is
constructed). -/
theorem L17_polyG_diag_pos (x : Fin 2 → ℝ) : (0 : ℝ) < 1 + (x 1) ^ 2 ∧ (0 : ℝ) < 1 :=
  ⟨by positivity, by norm_num⟩

/-- The explicit polynomial Jacobian `J(x) = [[-(1+x₁²), -2x₀x₁],[0,-1]]`. -/
def L17_polyJacobian (x : Fin 2 → ℝ) : Matrix (Fin 2) (Fin 2) ℝ :=
  !![-(1 + (x 1) ^ 2), -2 * (x 0) * (x 1); 0, -1]

/-- `L17_polyJacobian` is not symmetric at `x = (1,1)`: entries `(0,1) = -2`
and `(1,0) = 0` differ. -/
theorem L17_polyJacobian_not_isSymm : ¬ (L17_polyJacobian ![1, 1]).IsSymm := by
  intro h
  have hEq := congrFun (congrFun h 0) 1
  simp [L17_polyJacobian, Matrix.transpose_apply] at hEq

/-- `∂b₀/∂x₁` at `x = (1,1)`, computed as a genuine one-variable `deriv` along
the coordinate slice `x₁ ↦ b((1, x₁))`, equals `-2`. -/
theorem L17_polyB_deriv_x1_component0 :
    deriv (fun t : ℝ => L17_polyB (Function.update ![1, 1] 1 t) 0) 1 = -2 := by
  have hf : (fun t : ℝ => L17_polyB (Function.update ![1, 1] 1 t) 0) =
      fun t : ℝ => -(1 + t ^ 2) := by
    funext t
    have hupd : Function.update (![1, 1] : Fin 2 → ℝ) 1 t = ![1, t] := by
      funext i; fin_cases i <;> simp
    rw [hupd]
    simp [L17_polyB]
  rw [hf]
  have h1 : HasDerivAt (fun t : ℝ => (1 : ℝ) + t ^ 2) (2 * (1 : ℝ) ^ (2 - 1)) 1 :=
    (hasDerivAt_const_add_iff (1 : ℝ)).2 (hasDerivAt_pow 2 (1 : ℝ))
  have h2 : HasDerivAt (fun t : ℝ => -(1 + t ^ 2)) (-(2 * (1 : ℝ) ^ (2 - 1))) 1 := h1.neg
  rw [h2.deriv]
  norm_num

/-- `∂b₁/∂x₀` at `x = (1,1)`, computed as a genuine one-variable `deriv` along
the coordinate slice `x₀ ↦ b((x₀, 1))`, equals `0` (`b₁` does not depend on
`x₀`). -/
theorem L17_polyB_deriv_x0_component1 :
    deriv (fun s : ℝ => L17_polyB (Function.update ![1, 1] 0 s) 1) 1 = 0 := by
  have hf : (fun s : ℝ => L17_polyB (Function.update ![1, 1] 0 s) 1) =
      fun _ : ℝ => (-1 : ℝ) := by
    funext s
    have hupd : Function.update (![1, 1] : Fin 2 → ℝ) 0 s = ![s, 1] := by
      funext i; fin_cases i <;> simp
    rw [hupd]
    simp [L17_polyB]
  rw [hf, deriv_const]

/-- **The two mixed partials disagree.** `∂b₀/∂x₁ = -2 ≠ 0 = ∂b₁/∂x₀` at
`x = (1,1)`: the drift field's Jacobian is genuinely asymmetric there, even
though `b` is exactly `-(G∇Φ)` with zero non-conservative remainder. -/
theorem L17_polyB_partials_ne :
    deriv (fun t : ℝ => L17_polyB (Function.update ![1, 1] 1 t) 0) 1 ≠
    deriv (fun s : ℝ => L17_polyB (Function.update ![1, 1] 0 s) 1) 1 := by
  rw [L17_polyB_deriv_x1_component0, L17_polyB_deriv_x0_component1]
  norm_num

/-- The explicit Jacobian's `(0,1)` entry at `(1,1)` equals the machine-checked
derivative `∂b₀/∂x₁`. -/
theorem L17_polyJacobian_apply_01_eq_deriv :
    L17_polyJacobian ![1, 1] 0 1 =
      deriv (fun t : ℝ => L17_polyB (Function.update ![1, 1] 1 t) 0) 1 := by
  rw [L17_polyB_deriv_x1_component0]
  simp [L17_polyJacobian]

/-- The explicit Jacobian's `(1,0)` entry at `(1,1)` equals the machine-checked
derivative `∂b₁/∂x₀`. -/
theorem L17_polyJacobian_apply_10_eq_deriv :
    L17_polyJacobian ![1, 1] 1 0 =
      deriv (fun s : ℝ => L17_polyB (Function.update ![1, 1] 0 s) 1) 1 := by
  rw [L17_polyB_deriv_x0_component1]
  simp [L17_polyJacobian]

end

end NoeticDiffusion
