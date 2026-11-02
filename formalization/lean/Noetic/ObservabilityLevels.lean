import Mathlib.Data.Matrix.Block
import Mathlib.LinearAlgebra.Matrix.Notation
import Noetic.Covariance

/-!
# L20d–f: block-diagonal covariance invariance, private ratio, non-monotonic claim classes

NDT source: `project/lean/fable_ideas/10_closure_epoch_rank_and_observability_levels.md`,
`## L20d — Calibrated aggregate covariance ≠ directional specificity`,
`## L20e — Non-monotonicity of the four claim classes`; manuscript v2 lines 235–266
("the order is not monotonic"), 616–623 ("calibration is not destination geometry"),
1255–1262 (hierarchical failure); Gate R/RD/RC's E044R2 diagnosis that a calibrated
aggregate covariance (Frobenius error 0.06–0.10, coverage ≈ 0.9) coexisted with
target/other-private ratios pinned near `1` because the true per-branch Jacobian was
exactly block-diagonal (`claim_ledger.md:76-82`;
`tests/reachability_truth/test_e044r_r3_diagnostic.py:39-53`).

## Claim boundary

Finite real matrix algebra and finite combinatorics only.

`L20d` (`L20_blockDiag_covariance`) proves that a block-diagonal transition matrix
together with a block-diagonal innovation covariance keeps `Noetic.Covariance`'s
finite-horizon covariance recursion block-diagonal at every horizon — an exact
algebraic identity, not a claim about which real systems have block-diagonal
Jacobians.

`L20e` (`privateRatio`) is the single-direction ratio
`privateRatio M b := (b ⬝ᵥ (M *ᵥ b)) / ((b ⬝ᵥ b) * trace M / card n)` (the simplified
single-vector form offered as an alternative to the idea file's two-direction-family
ratio). It is proved to collapse to `1` on isotropic covariance for any unit vector,
and two exact-rational witnesses (`diag(4,1)` vs `diag(1,4)` at `b = e₁`, same trace
`5`, different ratios `8/5` and `2/5`) certify that equal trace does not force an equal
ratio. No probability coverage, no empirical Frobenius-error claim, no general
"aggregate summaries can always be matched while directional structure differs"
theorem — only these two exact facts.

`L20f` (`ClaimClass`) models the manuscript's four inferential claim classes
(association, discrimination, order-preservation, operator identification) only as
four abstract labels together with a four-world finite table (`Fin 4`), **not** as
the manuscript's concrete chart/mechanism/order predicates (that would need
`Noetic.ReducedSufficiency`'s fibre criterion instantiated on a concrete latent system,
judged out of the bounded MEDIUM-effort budget for this gate; recorded as a deviation
below). It proves, by `decide` on the explicit finite table, that for every ordered
pair of distinct classes there is a world where the first holds and the second fails —
the finite-witness core of "the order is not monotonic", at the abstract level of
non-implication between four labeled Boolean predicates.
-/

namespace NoeticDiffusion

open scoped Matrix

/-! ## L20d: block-diagonal transition and covariance keep the recursion block-diagonal -/

section L20d

variable {n1 n2 : Type*} [Fintype n1] [Fintype n2]

/-- If the transition matrix and the innovation covariance are both
block-diagonal (`fromBlocks A1 0 0 A2`, `fromBlocks Q1 0 0 Q2`), the whole
finite-horizon `covariance` recursion stays block-diagonal at every horizon,
with the two diagonal blocks following their own independent recursions.
This is E044R2's diagnosis — "replay acting on block 2 cannot change
target-1 reachability" — as an exact algebraic identity. -/
theorem L20_blockDiag_covariance (A1 Q1 : Matrix n1 n1 ℝ) (A2 Q2 : Matrix n2 n2 ℝ) (h : ℕ) :
    covariance (Matrix.fromBlocks A1 (0 : Matrix n1 n2 ℝ) 0 A2)
        (Matrix.fromBlocks Q1 (0 : Matrix n1 n2 ℝ) 0 Q2) h
      = Matrix.fromBlocks (covariance A1 Q1 h) 0 0 (covariance A2 Q2 h) := by
  induction h with
  | zero => simp [covariance_zero, Matrix.fromBlocks_zero]
  | succ h ih =>
      have hT : (Matrix.fromBlocks A1 (0 : Matrix n1 n2 ℝ) 0 A2)ᴴ
          = Matrix.fromBlocks A1ᴴ (0 : Matrix n1 n2 ℝ) 0 A2ᴴ := by
        rw [Matrix.fromBlocks_conjTranspose]
        simp
      simp only [covariance_succ]
      unfold covStep
      rw [ih, hT, Matrix.fromBlocks_multiply, Matrix.fromBlocks_multiply, Matrix.fromBlocks_add]
      simp

end L20d

/-! ## L20e: private ratio -/

section L20e

variable {n : Type*} [Fintype n] [DecidableEq n]

/-- Single-direction private/other ratio for a covariance `M` at a probe
vector `b`: the Rayleigh quotient `b ⬝ᵥ (M *ᵥ b)` normalized against the
isotropic baseline `(b ⬝ᵥ b) * trace M / card n` that `b` would see under a
scalar-multiple-of-identity covariance with the same trace. Simplified
single-vector form of the idea file's two-direction-family ratio. -/
noncomputable def privateRatio (M : Matrix n n ℝ) (b : n → ℝ) : ℝ :=
  (b ⬝ᵥ (M *ᵥ b)) / ((b ⬝ᵥ b) * Matrix.trace M / (Fintype.card n : ℝ))

/-- Scalar/isotropic degeneracy: for an isotropic covariance `c • 1` with
`c > 0` and a unit probe vector `b`, `privateRatio` collapses to `1` for
every direction — "aggregate summaries can match while directional
structure is trivial" in the degenerate isotropic case. -/
theorem L20_privateRatio_isotropic [Nonempty n]
    {c : ℝ} (hc : 0 < c) {b : n → ℝ} (hb : b ⬝ᵥ b = 1) :
    privateRatio (c • (1 : Matrix n n ℝ)) b = 1 := by
  have hcard : (Fintype.card n : ℝ) ≠ 0 := by exact_mod_cast Fintype.card_ne_zero
  have hcne : c ≠ 0 := hc.ne'
  unfold privateRatio
  rw [Matrix.smul_mulVec, Matrix.one_mulVec, dotProduct_smul, Matrix.trace_smul,
    Matrix.trace_one, hb]
  simp only [smul_eq_mul, one_mul, mul_one]
  field_simp

/-- Witness: two covariances with the **same trace** (`diag(4,1)` and
`diag(1,4)` on `Fin 2`, trace `5` in both cases) give **different** exact
`privateRatio` values at the same probe direction `b = e₁` (`8/5` vs `2/5`).
Matched aggregate trace does not force a matched directional ratio. -/
theorem L20_privateRatio_diag_witness :
    privateRatio (Matrix.diagonal (![4, 1] : Fin 2 → ℝ)) (![1, 0] : Fin 2 → ℝ) = 8 / 5 ∧
    privateRatio (Matrix.diagonal (![1, 4] : Fin 2 → ℝ)) (![1, 0] : Fin 2 → ℝ) = 2 / 5 := by
  constructor <;>
  · unfold privateRatio
    simp [Matrix.mulVec_diagonal, dotProduct, Fin.sum_univ_two, Matrix.trace_diagonal]
    norm_num

end L20e

/-! ## L20f: four inferential claim classes, pairwise non-implicative -/

section L20f

/-- The manuscript's four inferential claim classes (lines 235–266), modeled
as four abstract labels (not yet instantiated on a concrete chart/mechanism
system — see the module docstring). -/
inductive ClaimClass
  | assoc
  | discriminates
  | preservesOrder
  | identifiesOperator
  deriving DecidableEq

/-- A four-world finite table (`Fin 4`): world `k` is the dedicated witness
world for class `k` (in the constructor order above), where exactly that
class holds and the other three fail. -/
def L20_claimClassHolds : ClaimClass → Fin 4 → Bool
  | .assoc, w => decide (w = 0)
  | .discriminates, w => decide (w = 1)
  | .preservesOrder, w => decide (w = 2)
  | .identifiesOperator, w => decide (w = 3)

/-- The dedicated witness world for each class. -/
def L20_claimClassWorld : ClaimClass → Fin 4
  | .assoc => 0
  | .discriminates => 1
  | .preservesOrder => 2
  | .identifiesOperator => 3

/-- For every ordered pair of **distinct** claim classes `i ≠ j`, the
dedicated witness world for `i` is a world where `i` holds and `j` fails.
Finite `decide` check over the `4 × 4` table — the kernel-checked core of
"the order is not monotonic": no claim class implies another. -/
theorem L20_claimClass_not_implies {i j : ClaimClass} (hij : i ≠ j) :
    L20_claimClassHolds i (L20_claimClassWorld i) = true ∧
    L20_claimClassHolds j (L20_claimClassWorld i) = false := by
  cases i <;> cases j <;> first | exact absurd rfl hij | decide

/-- Restated directly as a non-implication: no claim class's truth at every
world forces another distinct class's truth. -/
theorem L20_claimClass_not_implies' {i j : ClaimClass} (hij : i ≠ j) :
    ¬ (∀ w : Fin 4, L20_claimClassHolds i w = true → L20_claimClassHolds j w = true) := by
  obtain ⟨h1, h2⟩ := L20_claimClass_not_implies hij
  intro hforall
  have h3 := hforall (L20_claimClassWorld i) h1
  rw [h3] at h2
  exact Bool.noConfusion h2

end L20f

end NoeticDiffusion
