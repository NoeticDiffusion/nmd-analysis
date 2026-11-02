import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.Data.Matrix.Mul
import Noetic.Covariance

/-! # L14: Non-equivalences in the futures layer (finite witnesses, part 1)

This file formalizes finite counterexamples for four rows of the manuscript's
"Non-equivalent questions in NDT" table and the compact summary's "NON-EQUIVALENT
QUESTIONS" discipline: every "do not conflate" sentence about the futures layer
becomes a checked theorem on an explicit finite chain, probability vector, or
matrix pair, instead of prose.

Source article:
  `J:\repos\nmd-analysis\articles\NoeticDiffusionTheory_v2\Noetic Diffusion Theory - Neural State, Dynamical Accessibility, and the Geometry of Possible Futures.typ`
  - state-at-horizon law vs path space, support vs mass: lines 341--353
  - drift `J` vs diffusion `a` dissociation: lines 577--579
  - stochastic short-horizon reachability, predictive spread vs occupancy:
    lines 596--623
  - committor geometry, "stage labels are not committor truth": lines 625--640
  - the "Non-equivalent questions in NDT" table: lines 653--677
Idea file: `J:\repos\nmd-analysis\project\lean\fable_ideas\03_futures_layer_nonequivalences.md`
(witnesses W1--W4).

## Claim boundary

- Every witness below is a finite (`Fin 2`/`Fin 3`/`Fin 4`) toy chain, vector
  pair, or matrix pair. Each certifies a logical non-implication between two
  named objects (occupancy, one-step law, one-step displacement spread,
  committor, support, mass); none of them asserts that a specific empirical
  MNPS object dissociates, and none is an ergodic theorem, a stationary-law
  convergence result, or a uniqueness theorem for committors.
- `L14_IsCommittorVec` states the harmonic (martingale) boundary-value
  equations for a committor relative to a single named absorbing state `A`
  and a single named absorbing state `B`. It is satisfied by the exhibited
  vectors by direct computation; no uniqueness claim is made or needed here
  (uniqueness for absorbing finite chains is a separate result, see
  `04_committor_finite_chain.md`).
- W1 uses two explicit `Fin 2 → ℝ` probability vectors rather than
  `PMF.bernoulli`: the `ℝ≥0` arithmetic needed to discharge the `p ≤ 1` side
  conditions and to separate the two applied values was not closed by
  `norm_num` in this Mathlib snapshot, so the idea file's stated fallback is
  used instead and reported here as a deviation.
-/

namespace NoeticDiffusion

open scoped BigOperators Matrix

/-! ## W2 — same occupancy, different reachability

Two row-stochastic chains on `Fin 2` share the uniform stationary occupancy
`π = (1/2, 1/2)` (`L14_IsStationary π P := π ᵥ* P = π`) while one is frozen
(nothing reachable from elsewhere in one step) and the other swaps every
state into the other in one step. Occupancy therefore does not determine the
one-step reachability structure. -/

/-- A probability vector `π` is stationary for a row-stochastic matrix `P`
when one step of `P` returns the same law. -/
def L14_IsStationary {n : Type*} [Fintype n] (π : n → ℝ) (P : Matrix n n ℝ) : Prop :=
  π ᵥ* P = π

/-- The frozen chain on `Fin 2`: nothing is reachable from the other state in
one step. -/
def L14_P_id : Matrix (Fin 2) (Fin 2) ℝ := Matrix.of ![![1, 0], ![0, 1]]

/-- The swap chain on `Fin 2`: every state reaches the other one in one
step. -/
def L14_P_swap : Matrix (Fin 2) (Fin 2) ℝ := Matrix.of ![![0, 1], ![1, 0]]

/-- The uniform occupancy law shared by `L14_P_id` and `L14_P_swap`. -/
noncomputable def L14_pi2 : Fin 2 → ℝ := ![1 / 2, 1 / 2]

theorem L14_P_id_isStationary : L14_IsStationary L14_pi2 L14_P_id := by
  unfold L14_IsStationary
  ext j
  fin_cases j <;>
    norm_num [Matrix.vecMul, dotProduct, Fin.sum_univ_succ, Fin.sum_univ_zero, L14_pi2,
      L14_P_id, Matrix.of_apply]

theorem L14_P_swap_isStationary : L14_IsStationary L14_pi2 L14_P_swap := by
  unfold L14_IsStationary
  ext j
  fin_cases j <;>
    norm_num [Matrix.vecMul, dotProduct, Fin.sum_univ_succ, Fin.sum_univ_zero, L14_pi2,
      L14_P_swap, Matrix.of_apply]

private lemma L14_P_id_entry : L14_P_id 0 1 = 0 := by norm_num [L14_P_id, Matrix.of_apply]
private lemma L14_P_swap_entry : L14_P_swap 0 1 = 1 := by
  norm_num [L14_P_swap, Matrix.of_apply]

/-- The explicit entry witness behind `L14_P_id_ne_P_swap`:
`P_id 0 1 = 0 ≠ 1 = P_swap 0 1`. -/
theorem L14_P_id_ne_P_swap : L14_P_id ≠ L14_P_swap := by
  intro h
  have hc : L14_P_id 0 1 = L14_P_swap 0 1 := congrArg (fun M => M 0 1) h
  rw [L14_P_id_entry, L14_P_swap_entry] at hc
  norm_num at hc

/-- W2: occupancy does not determine reachability. Two chains share the same
stationary occupancy law and are themselves distinct as one-step transition
laws. -/
theorem L14_occupancy_ne_reachability :
    ∃ P₁ P₂ : Matrix (Fin 2) (Fin 2) ℝ,
      L14_IsStationary L14_pi2 P₁ ∧ L14_IsStationary L14_pi2 P₂ ∧ P₁ ≠ P₂ :=
  ⟨L14_P_id, L14_P_swap, L14_P_id_isStationary, L14_P_swap_isStationary, L14_P_id_ne_P_swap⟩

/-! ## W3 — same drift, different diffusion; same diffusion, different drift

Connects to `Noetic.Covariance`'s `covariance`/`covariance_zero`/
`covariance_succ`: at horizon `1`, `covariance A Q 1 = Q` for *every* `A`
(the one-step predictive spread is exactly the innovation covariance and does
not see the transition matrix at all at this horizon), which immediately
gives both directions of the dissociation. -/

/-- The one-step predictive-spread covariance equals the innovation
covariance regardless of the local transition matrix `A`. -/
theorem L14_covariance_horizon_one {n : Type*} [Fintype n] (A Q : Matrix n n ℝ) :
    covariance A Q 1 = Q := by
  simp [covariance_succ, covariance_zero, covStep]

/-- A fixed transition matrix (the identity on `Fin 2`) used for the
same-drift, different-diffusion witness. -/
def L14_A_id : Matrix (Fin 2) (Fin 2) ℝ := (1 : Matrix (Fin 2) (Fin 2) ℝ)

/-- A second transition matrix (minus the identity on `Fin 2`), sharing the
one-step covariance of `L14_A_id` with any fixed `Q` but differing from it as
a matrix, used for the same-diffusion, different-drift witness. -/
def L14_A_neg : Matrix (Fin 2) (Fin 2) ℝ := (-1 : Matrix (Fin 2) (Fin 2) ℝ)

/-- One innovation covariance on `Fin 2`. -/
def L14_Q1 : Matrix (Fin 2) (Fin 2) ℝ := Matrix.of ![![1, 0], ![0, 1]]

/-- A second, different, innovation covariance on `Fin 2`. -/
def L14_Q2 : Matrix (Fin 2) (Fin 2) ℝ := Matrix.of ![![2, 0], ![0, 2]]

private lemma L14_A_id_ne_A_neg : L14_A_id ≠ L14_A_neg := by
  intro h
  have hc : L14_A_id 0 0 = L14_A_neg 0 0 := congrArg (fun M => M 0 0) h
  norm_num [L14_A_id, L14_A_neg] at hc

private lemma L14_Q1_ne_Q2 : L14_Q1 ≠ L14_Q2 := by
  intro h
  have hc : L14_Q1 0 0 = L14_Q2 0 0 := congrArg (fun M => M 0 0) h
  norm_num [L14_Q1, L14_Q2, Matrix.of_apply] at hc

/-- W3a: same drift `L14_A_id`, different one-step diffusion. -/
theorem L14_same_drift_diff_diffusion :
    covariance L14_A_id L14_Q1 1 = L14_Q1 ∧
    covariance L14_A_id L14_Q2 1 = L14_Q2 ∧
    L14_Q1 ≠ L14_Q2 :=
  ⟨L14_covariance_horizon_one L14_A_id L14_Q1, L14_covariance_horizon_one L14_A_id L14_Q2,
    L14_Q1_ne_Q2⟩

/-- W3b: same one-step diffusion (`L14_Q1`) under two different drift
matrices that disagree even in sign. The one-step predictive spread cannot
see the drift. -/
theorem L14_same_diffusion_diff_drift :
    covariance L14_A_id L14_Q1 1 = covariance L14_A_neg L14_Q1 1 ∧
    L14_A_id ≠ L14_A_neg :=
  ⟨(L14_covariance_horizon_one L14_A_id L14_Q1).trans
      (L14_covariance_horizon_one L14_A_neg L14_Q1).symm,
    L14_A_id_ne_A_neg⟩

/-! ## W1 — same support, different mass

Two explicit probability vectors on `Fin 2`, both with full support (every
entry nonzero) and both summing to `1`, but differing as functions. A
reachable *set* (support) discards the probability mass carried by each
point.

Deviation from the idea file: the idea file's primary suggestion,
`PMF.bernoulli (1/4 : ℝ≥0) _` vs `PMF.bernoulli (3/4 : ℝ≥0) _`, was attempted
first; discharging the `ℝ≥0` side conditions `(1/4 : ℝ≥0) ≤ 1` and comparing
the two applied values via `norm_num` did not close in this Mathlib snapshot
(the goals were left as unresolved `ℝ≥0` (in)equalities). The idea file's own
fallback — two explicit `Fin 2 → ℝ` probability vectors with full support —
is used instead. -/

/-- The support of a real vector: the indices carrying nonzero mass. -/
def L14_w1_support (p : Fin 2 → ℝ) : Set (Fin 2) := {i | p i ≠ 0}

/-- A probability vector on `Fin 2` with full support. -/
noncomputable def L14_massA : Fin 2 → ℝ := ![1 / 4, 3 / 4]

/-- A second probability vector on `Fin 2`, sharing the full support of
`L14_massA` but carrying different mass at each point. -/
noncomputable def L14_massB : Fin 2 → ℝ := ![3 / 4, 1 / 4]

theorem L14_massA_isProb : (∑ i, L14_massA i) = 1 := by
  norm_num [L14_massA, Fin.sum_univ_succ, Fin.sum_univ_zero]

theorem L14_massB_isProb : (∑ i, L14_massB i) = 1 := by
  norm_num [L14_massB, Fin.sum_univ_succ, Fin.sum_univ_zero]

theorem L14_massA_support_eq_univ : L14_w1_support L14_massA = Set.univ := by
  ext i
  fin_cases i <;> simp [L14_w1_support, L14_massA]

theorem L14_massB_support_eq_univ : L14_w1_support L14_massB = Set.univ := by
  ext i
  fin_cases i <;> simp [L14_w1_support, L14_massB]

theorem L14_massA_ne_massB : L14_massA ≠ L14_massB := by
  intro h
  have hc : L14_massA 0 = L14_massB 0 := congrArg (fun f => f 0) h
  norm_num [L14_massA, L14_massB] at hc

/-- W1: two probability vectors on `Fin 2` share the same (full) support and
are different probability laws. -/
theorem L14_same_support_different_mass :
    L14_w1_support L14_massA = L14_w1_support L14_massB ∧ L14_massA ≠ L14_massB :=
  ⟨L14_massA_support_eq_univ.trans L14_massB_support_eq_univ.symm, L14_massA_ne_massB⟩

/-! ## W4 — same one-step displacement covariance, different committor
(covariance spread ≠ destination bias)

`L14_IsCommittorVec P A B q` states the harmonic (martingale) boundary-value
equations for a committor with absorbing states `A` (committor value `0`)
and `B` (committor value `1`): `q A = 0`, `q B = 1`, and `q i` is the
`P i`-weighted average of `q` at every other state `i`. -/

/-- The harmonic-vector definition of a committor relative to a single
absorbing state `A` (value `0`) and a single absorbing state `B` (value
`1`). No uniqueness claim: this only records the boundary-value equations
that a committor vector satisfies. -/
def L14_IsCommittorVec {n : Type*} [Fintype n] [DecidableEq n]
    (P : Matrix n n ℝ) (A B : n) (q : n → ℝ) : Prop :=
  q A = 0 ∧ q B = 1 ∧ ∀ i, i ≠ A → i ≠ B → q i = ∑ j, P i j * q j

/-- A three-state absorbing chain `{A = 0, mid = 1, B = 2}`: from `mid`,
`A` and `B` are equally likely in one step. -/
noncomputable def L14_Chain1 : Matrix (Fin 3) (Fin 3) ℝ :=
  Matrix.of ![![1, 0, 0], ![1 / 2, 0, 1 / 2], ![0, 0, 1]]

/-- A second three-state absorbing chain on the same states: from `mid`, the
chain may also stay at `mid`, but `A` and `B` remain equally likely
conditional on absorption. -/
noncomputable def L14_Chain2 : Matrix (Fin 3) (Fin 3) ℝ :=
  Matrix.of ![![1, 0, 0], ![1 / 4, 1 / 2, 1 / 4], ![0, 0, 1]]

/-- The shared committor vector for `L14_Chain1` and `L14_Chain2`: both give
`mid` committor value `1/2`. -/
noncomputable def L14_qMid : Fin 3 → ℝ := ![0, 1 / 2, 1]

theorem L14_Chain1_isCommittorVec : L14_IsCommittorVec L14_Chain1 0 2 L14_qMid := by
  refine ⟨by simp [L14_qMid], by simp [L14_qMid], ?_⟩
  intro i hA hB
  fin_cases i
  · exact absurd rfl hA
  · norm_num [L14_Chain1, L14_qMid, Matrix.of_apply, Fin.sum_univ_succ, Fin.sum_univ_zero]
  · exact absurd rfl hB

theorem L14_Chain2_isCommittorVec : L14_IsCommittorVec L14_Chain2 0 2 L14_qMid := by
  refine ⟨by simp [L14_qMid], by simp [L14_qMid], ?_⟩
  intro i hA hB
  fin_cases i
  · exact absurd rfl hA
  · norm_num [L14_Chain2, L14_qMid, Matrix.of_apply, Fin.sum_univ_succ, Fin.sum_univ_zero]
  · exact absurd rfl hB

/-- The embedding `A ↦ -1, mid ↦ 0, B ↦ 1` used to compute the one-step
displacement variance from `mid`. -/
noncomputable def L14_embed3 : Fin 3 → ℝ := ![-1, 0, 1]

/-- The one-step displacement variance from state `i` under the chain `P`
and the real-valued embedding `e`: `E[e(X₁)²] - E[e(X₁)]²` given `X₀ = i`. -/
noncomputable def L14_oneStepVariance {n : Type*} [Fintype n] (P : Matrix n n ℝ)
    (e : n → ℝ) (i : n) : ℝ :=
  (∑ j, P i j * (e j) ^ 2) - (∑ j, P i j * e j) ^ 2

theorem L14_Chain1_variance : L14_oneStepVariance L14_Chain1 L14_embed3 1 = 1 := by
  norm_num [L14_oneStepVariance, L14_Chain1, L14_embed3, Matrix.of_apply, Fin.sum_univ_succ,
    Fin.sum_univ_zero]

theorem L14_Chain2_variance : L14_oneStepVariance L14_Chain2 L14_embed3 1 = 1 / 2 := by
  norm_num [L14_oneStepVariance, L14_Chain2, L14_embed3, Matrix.of_apply, Fin.sum_univ_succ,
    Fin.sum_univ_zero]

/-- W4 (simpler pair): `L14_Chain1` and `L14_Chain2` have the same committor
value at `mid` (`1/2`) and different one-step displacement variance there
(`1` vs `1/2`). Same committor does not fix the local spread. -/
theorem L14_same_committor_diff_spread :
    L14_IsCommittorVec L14_Chain1 0 2 L14_qMid ∧ L14_IsCommittorVec L14_Chain2 0 2 L14_qMid ∧
    L14_oneStepVariance L14_Chain1 L14_embed3 1 ≠ L14_oneStepVariance L14_Chain2 L14_embed3 1 := by
  refine ⟨L14_Chain1_isCommittorVec, L14_Chain2_isCommittorVec, ?_⟩
  rw [L14_Chain1_variance, L14_Chain2_variance]
  norm_num

/-- A four-state absorbing chain `{A = 0, m1 = 1, m2 = 2, B = 3}`: from `m1`
the chain moves to `m2` with probability `1`; from `m2`, `A` and `B` are
equally likely. -/
noncomputable def L14_ChainX : Matrix (Fin 4) (Fin 4) ℝ :=
  Matrix.of ![![1, 0, 0, 0], ![0, 0, 1, 0], ![1 / 2, 0, 0, 1 / 2], ![0, 0, 0, 1]]

/-- A second four-state absorbing chain on the same states, agreeing with
`L14_ChainX` at `m1` (still moving to `m2` with probability `1`) but
favouring `B` from `m2`. -/
noncomputable def L14_ChainY : Matrix (Fin 4) (Fin 4) ℝ :=
  Matrix.of ![![1, 0, 0, 0], ![0, 0, 1, 0], ![1 / 4, 0, 0, 3 / 4], ![0, 0, 0, 1]]

/-- The committor vector for `L14_ChainX`. -/
noncomputable def L14_qX : Fin 4 → ℝ := ![0, 1 / 2, 1 / 2, 1]

/-- The committor vector for `L14_ChainY`. -/
noncomputable def L14_qY : Fin 4 → ℝ := ![0, 3 / 4, 3 / 4, 1]

theorem L14_ChainX_isCommittorVec : L14_IsCommittorVec L14_ChainX 0 3 L14_qX := by
  refine ⟨by simp [L14_qX], by simp [L14_qX], ?_⟩
  intro i hA hB
  fin_cases i
  · exact absurd rfl hA
  · norm_num [L14_ChainX, L14_qX, Matrix.of_apply, Fin.sum_univ_succ, Fin.sum_univ_zero]
  · norm_num [L14_ChainX, L14_qX, Matrix.of_apply, Fin.sum_univ_succ, Fin.sum_univ_zero]
  · exact absurd rfl hB

theorem L14_ChainY_isCommittorVec : L14_IsCommittorVec L14_ChainY 0 3 L14_qY := by
  refine ⟨by simp [L14_qY], by simp [L14_qY], ?_⟩
  intro i hA hB
  fin_cases i
  · exact absurd rfl hA
  · norm_num [L14_ChainY, L14_qY, Matrix.of_apply, Fin.sum_univ_succ, Fin.sum_univ_zero]
  · norm_num [L14_ChainY, L14_qY, Matrix.of_apply, Fin.sum_univ_succ, Fin.sum_univ_zero]
  · exact absurd rfl hB

/-- `L14_ChainX` and `L14_ChainY` have the identical one-step transition law
at the start state `m1`: both move to `m2` with probability `1`. -/
theorem L14_ChainX_row_one_eq_ChainY_row_one : ∀ j, L14_ChainX 1 j = L14_ChainY 1 j := by
  intro j
  fin_cases j <;> norm_num [L14_ChainX, L14_ChainY, Matrix.of_apply]

/-- The one-step displacement variance at a state depends only on the
one-step law (the row) at that state, for any real-valued embedding. -/
theorem L14_oneStepVariance_congr_row {n : Type*} [Fintype n] {P₁ P₂ : Matrix n n ℝ}
    (e : n → ℝ) (i : n) (h : ∀ j, P₁ i j = P₂ i j) :
    L14_oneStepVariance P₁ e i = L14_oneStepVariance P₂ e i := by
  have h1 : (∑ j, P₁ i j * (e j) ^ 2) = ∑ j, P₂ i j * (e j) ^ 2 :=
    Finset.sum_congr rfl (fun j _ => by rw [h j])
  have h2 : (∑ j, P₁ i j * e j) = ∑ j, P₂ i j * e j :=
    Finset.sum_congr rfl (fun j _ => by rw [h j])
  unfold L14_oneStepVariance
  rw [h1, h2]

/-- Consequently `L14_ChainX` and `L14_ChainY` have the same one-step
displacement covariance at `m1` for every embedding into `ℝ`. -/
theorem L14_ChainX_ChainY_same_variance_at_m1 (e : Fin 4 → ℝ) :
    L14_oneStepVariance L14_ChainX e 1 = L14_oneStepVariance L14_ChainY e 1 :=
  L14_oneStepVariance_congr_row e 1 L14_ChainX_row_one_eq_ChainY_row_one

theorem L14_qX_ne_qY_at_m1 : L14_qX 1 ≠ L14_qY 1 := by
  norm_num [L14_qX, L14_qY]

/-- W4 (main pair): `L14_ChainX` and `L14_ChainY` share the identical
one-step law at the start state `m1` (hence the same one-step displacement
covariance there, for every embedding), yet their committor values at `m1`
differ (`1/2` vs `3/4`). The one-step predictive spread does not determine
the destination bias. -/
theorem L14_covariance_eq_committor_ne :
    (∀ j, L14_ChainX 1 j = L14_ChainY 1 j) ∧
    (∀ e : Fin 4 → ℝ, L14_oneStepVariance L14_ChainX e 1 = L14_oneStepVariance L14_ChainY e 1) ∧
    L14_qX 1 ≠ L14_qY 1 :=
  ⟨L14_ChainX_row_one_eq_ChainY_row_one, L14_ChainX_ChainY_same_variance_at_m1,
    L14_qX_ne_qY_at_m1⟩

end NoeticDiffusion
