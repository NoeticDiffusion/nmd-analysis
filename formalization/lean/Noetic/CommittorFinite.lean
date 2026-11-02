import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.Data.Matrix.Mul
import Mathlib.LinearAlgebra.Matrix.PosDef

/-! # L15: Committor on finite absorbing chains (algebra, gambler's ruin, uniqueness)

This file formalizes the finite-Markov-chain committor `q(x) = P_x(τ_B < τ_A)`
as an exact, checkable object: `IsCommittor` states the harmonic
(martingale) boundary-value equations relative to two disjoint declared
destination sets, and the theorems below cover its basic algebra, an
explicit closed form for the (biased) gambler's-ruin chain, and uniqueness
of that closed form under the chain's own harmonic recursion.

Source article:
  `J:\repos\nmd-analysis\articles\NoeticDiffusionTheory_v2\Noetic Diffusion Theory - Neural State, Dynamical Accessibility, and the Geometry of Possible Futures.typ`,
  committor geometry: lines 625--640; limitations: line 1336--1337. Compact
  summary §5 "COMMITTOR GEOMETRY" and §9 "do not treat stage labels as
  committor truth".
Idea file: `J:\repos\nmd-analysis\project\lean\fable_ideas\04_committor_finite_chain.md`.
Reuses the L14 harmonic-vector committor discipline from
`Noetic/FuturesNonEquivalence.lean` (`L14_IsCommittorVec`), generalized here
from a single named absorbing state on each side to a `Finset`-valued
destination pair `A B : Finset n`.

## Claim boundary

- `IsCommittor` (named `L15_IsCommittor` below) is a *specification*: `q = 0`
  on `A`, `q = 1` on `B`, and `q` harmonic (the `P`-weighted average of
  itself) off `A ∪ B`. Finite state space, discrete time, exact transition
  matrix given. No estimator, no continuous-time diffusion, no
  transition-path theory beyond this harmonic characterization.
- L15a is pure algebra: boundary/harmonic conditions transport through the
  complementary committor (`1 - q`, destinations swapped), through the
  `Matrix.mulVec` form, degenerate when `A ∪ B` is everything, and through
  *any* real affine combination `t • q₁ + (1 - t) • q₂` of two committors for
  the same data (not only convex `t ∈ [0,1]`, since the boundary values `0`
  and `1` are absorbed by `t + (1 - t) = 1` regardless of sign) — this last
  fact is exactly why an absorption hypothesis is needed for uniqueness, and
  no such hypothesis is used or claimed in L15a. The bounds theorem
  (`L15_committor_bounds`) is the deliberately weaker, non-overclaiming form
  the idea file allows: it needs `0 ≤ q ≤ 1` already assumed off the
  boundary and only propagates it onto `A ∪ B`; the general finite-chain
  maximum principle (deriving `0 ≤ q ≤ 1` from harmonicity and absorption
  alone, with no interior hypothesis) is **not proved** here.
- L15b gives the explicit closed-form committor for the discrete gambler's
  ruin chain on `Fin (N+1)` with absorbing endpoints `0` and `N`: the
  symmetric walk (`L15_gamblersRuinQ i = i / N`) and, bounded effort, the
  biased walk `p ≠ 1/2` (`L15_biasedRuinQ i = (1 - r^i) / (1 - r^N)`,
  `r = (1 - p) / p`). Both are proved to be genuine `L15_IsCommittor`
  witnesses for their respective row-stochastic chains.
- L15c ships two things and is explicit about the rest. First, the
  **linear-algebraic core** the idea file offers as a fallback: the
  difference of two committors for the same data is itself harmonic and
  vanishes on `A ∪ B` (`L15_committor_diff_boundary_zero`,
  `L15_committor_diff_harmonic`) — this isolates exactly what an absorption
  argument would need to close to zero, without assuming or proving that
  closure in general. Second, the chain-specific fallback the idea file also
  sanctions: `L15_gamblersRuinQ_unique` proves, by explicit induction on the
  constant-increment structure of the harmonic recursion (not by a
  substochastic-power/norm argument), that *every* committor for the
  symmetric gambler's-ruin chain equals `i / N`. The general finite-chain
  uniqueness theorem (from a `∃ k, ‖T^k‖∞ < 1` finite-absorption hypothesis
  on the transient block, as sketched in the idea file) is **not proved**
  here and is recorded as such below.
- Nothing here says stage labels are destinations, that MNPS emits
  destinations, or licenses `mndm.committor.v1`; that schema stays gated.
-/

namespace NoeticDiffusion

open scoped BigOperators Matrix

/-! ## L15a — committor algebra -/

/-- A real matrix is row-stochastic when every entry is nonnegative and every
row sums to `1`. -/
def L15_RowStochastic {n : Type*} [Fintype n] (P : Matrix n n ℝ) : Prop :=
  (∀ i j, 0 ≤ P i j) ∧ (∀ i, ∑ j, P i j = 1)

/-- `q` is a committor for the chain `P` relative to disjoint destination
sets `A` (value `0`) and `B` (value `1`): `q` vanishes on `A`, equals `1` on
`B`, and is harmonic (the `P`-weighted average of itself) at every other
state. Generalizes the single-state `L14_IsCommittorVec` predicate from
`Noetic/FuturesNonEquivalence.lean` to `Finset`-valued destinations; no
disjointness hypothesis is imposed on `A`/`B` in the definition itself since
none of the algebra below needs it (the singleton case reduces to
`L14_IsCommittorVec` exactly when `A`, `B` are disjoint singletons — the two
value conditions would otherwise conflict on a shared state). -/
def L15_IsCommittor {n : Type*} [Fintype n] [DecidableEq n]
    (P : Matrix n n ℝ) (A B : Finset n) (q : n → ℝ) : Prop :=
  (∀ a ∈ A, q a = 0) ∧ (∀ b ∈ B, q b = 1) ∧
  (∀ i, i ∉ A → i ∉ B → q i = ∑ j, P i j * q j)

/-- The complementary function `1 - q` is a committor for the same
row-stochastic chain with the destinations swapped. -/
theorem L15_isCommittor_swap {n : Type*} [Fintype n] [DecidableEq n]
    {P : Matrix n n ℝ} (hP : L15_RowStochastic P) {A B : Finset n} {q : n → ℝ}
    (hq : L15_IsCommittor P A B q) :
    L15_IsCommittor P B A (fun i => 1 - q i) := by
  obtain ⟨hA, hB, hharm⟩ := hq
  refine ⟨?_, ?_, ?_⟩
  · intro b hb
    simp [hB b hb]
  · intro a ha
    simp [hA a ha]
  · intro i hiB hiA
    have h := hharm i hiA hiB
    have hsum : ∑ j, P i j = 1 := hP.2 i
    simp only
    have hexp : ∑ j, P i j * (1 - q j) = (∑ j, P i j) - ∑ j, P i j * q j := by
      rw [← Finset.sum_sub_distrib]
      exact Finset.sum_congr rfl (fun j _ => by ring)
    rw [hexp, hsum, ← h]

/-- The harmonic equation restated in `Matrix.mulVec` form off the
boundary. -/
theorem L15_isCommittor_mulVec {n : Type*} [Fintype n] [DecidableEq n]
    {P : Matrix n n ℝ} {A B : Finset n} {q : n → ℝ} (hq : L15_IsCommittor P A B q)
    {i : n} (hiA : i ∉ A) (hiB : i ∉ B) :
    (P *ᵥ q) i = q i := by
  have h := hq.2.2 i hiA hiB
  simp [Matrix.mulVec, dotProduct, h]

/-- Degenerate case: if `A ∪ B` already exhausts every state, the harmonic
condition is vacuous, and *any* function with the right boundary values is a
committor. This documents that the harmonic clause is only informative on a
nonempty transient region. -/
theorem L15_isCommittor_of_union_eq_univ {n : Type*} [Fintype n] [DecidableEq n]
    (P : Matrix n n ℝ) (A B : Finset n) (h : A ∪ B = Finset.univ) (q : n → ℝ)
    (hA : ∀ a ∈ A, q a = 0) (hB : ∀ b ∈ B, q b = 1) :
    L15_IsCommittor P A B q := by
  refine ⟨hA, hB, ?_⟩
  intro i hiA hiB
  exfalso
  have hmem : i ∈ A ∪ B := h ▸ Finset.mem_univ i
  rcases Finset.mem_union.mp hmem with h1 | h1
  · exact hiA h1
  · exact hiB h1

/-- Any real affine combination of two committors for the same data
(`A`, `B`, `P`) is again a committor for that data: the boundary values `0`
and `1` are preserved for *every* real `t`, not only `t ∈ [0, 1]`, because
`t * 0 + (1 - t) * 0 = 0` and `t * 1 + (1 - t) * 1 = 1` unconditionally. This
is exactly why an extra absorption hypothesis is needed to rule out
non-uniqueness; no such hypothesis is used here. -/
theorem L15_isCommittor_combo {n : Type*} [Fintype n] [DecidableEq n]
    {P : Matrix n n ℝ} {A B : Finset n} {q1 q2 : n → ℝ} (t : ℝ)
    (hq1 : L15_IsCommittor P A B q1) (hq2 : L15_IsCommittor P A B q2) :
    L15_IsCommittor P A B (fun i => t * q1 i + (1 - t) * q2 i) := by
  obtain ⟨hA1, hB1, hH1⟩ := hq1
  obtain ⟨hA2, hB2, hH2⟩ := hq2
  refine ⟨?_, ?_, ?_⟩
  · intro a ha
    simp [hA1 a ha, hA2 a ha]
  · intro b hb
    simp [hB1 b hb, hB2 b hb]
  · intro i hiA hiB
    have h1 := hH1 i hiA hiB
    have h2 := hH2 i hiA hiB
    simp only
    rw [h1, h2, Finset.mul_sum, Finset.mul_sum, ← Finset.sum_add_distrib]
    exact Finset.sum_congr rfl (fun j _ => by ring)

/-- Weak (non-overclaiming) bounds theorem: if a committor is already known
to lie in `[0, 1]` off the boundary, it lies in `[0, 1]` everywhere, since
the boundary values `0` and `1` are themselves in `[0, 1]`. The unconditional
maximum principle (deriving the interior bound from harmonicity and
absorption alone) is not proved here; see the claim boundary above. -/
theorem L15_committor_bounds {n : Type*} [Fintype n] [DecidableEq n]
    {P : Matrix n n ℝ} {A B : Finset n} {q : n → ℝ} (hq : L15_IsCommittor P A B q)
    (hbdd : ∀ i, i ∉ A → i ∉ B → 0 ≤ q i ∧ q i ≤ 1) (i : n) :
    0 ≤ q i ∧ q i ≤ 1 := by
  by_cases hA : i ∈ A
  · simp [hq.1 i hA]
  · by_cases hB : i ∈ B
    · simp [hq.2.1 i hB]
    · exact hbdd i hA hB

/-! ## L15b — gambler's ruin: symmetric walk -/

/-- The simple symmetric random walk on `Fin (N+1)` with absorbing endpoints
`0` and `N`: interior states step to their neighbours with probability
`1/2` each; the endpoints are absorbing (self-loop with probability `1`). -/
noncomputable def L15_gamblersRuinP (N : ℕ) : Matrix (Fin (N+1)) (Fin (N+1)) ℝ :=
  Matrix.of fun i j =>
    if h0 : (i:ℕ) = 0 then (if j = i then (1:ℝ) else 0)
    else if hN : (i:ℕ) = N then (if j = i then (1:ℝ) else 0)
    else
      (if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1/2:ℝ) else 0) +
      (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1/2:ℝ) else 0)

theorem L15_gamblersRuinP_nonneg (N : ℕ) : ∀ i j, 0 ≤ L15_gamblersRuinP N i j := by
  intro i j
  unfold L15_gamblersRuinP
  dsimp only [Matrix.of_apply]
  split_ifs <;> norm_num

theorem L15_gamblersRuinP_rowSum (N : ℕ) : ∀ i, ∑ j, L15_gamblersRuinP N i j = 1 := by
  intro i
  by_cases h0 : (i:ℕ) = 0
  · have heq : ∀ j, L15_gamblersRuinP N i j = (if j = i then (1:ℝ) else 0) := by
      intro j
      unfold L15_gamblersRuinP
      dsimp only [Matrix.of_apply]
      rw [dif_pos h0]
    calc ∑ j, L15_gamblersRuinP N i j = ∑ j, (if j = i then (1:ℝ) else 0) :=
          Finset.sum_congr rfl (fun j _ => heq j)
      _ = 1 := Fintype.sum_ite_eq' i (fun _ => (1:ℝ))
  · by_cases hN : (i:ℕ) = N
    · have heq : ∀ j, L15_gamblersRuinP N i j = (if j = i then (1:ℝ) else 0) := by
        intro j
        unfold L15_gamblersRuinP
        dsimp only [Matrix.of_apply]
        rw [dif_neg h0, dif_pos hN]
      calc ∑ j, L15_gamblersRuinP N i j = ∑ j, (if j = i then (1:ℝ) else 0) :=
            Finset.sum_congr rfl (fun j _ => heq j)
        _ = 1 := Fintype.sum_ite_eq' i (fun _ => (1:ℝ))
    · have heq : ∀ j, L15_gamblersRuinP N i j =
          (if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1/2:ℝ) else 0) +
          (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1/2:ℝ) else 0) := by
        intro j
        unfold L15_gamblersRuinP
        dsimp only [Matrix.of_apply]
        rw [dif_neg h0, dif_neg hN]
      calc ∑ j, L15_gamblersRuinP N i j
          = ∑ j, ((if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1/2:ℝ) else 0) +
              (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1/2:ℝ) else 0)) :=
            Finset.sum_congr rfl (fun j _ => heq j)
        _ = (∑ j, (if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1/2:ℝ) else 0)) +
              (∑ j, (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1/2:ℝ) else 0)) :=
            Finset.sum_add_distrib
        _ = 1/2 + 1/2 := by
            rw [Fintype.sum_ite_eq' (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) (fun _ => (1/2:ℝ)),
                Fintype.sum_ite_eq' (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) (fun _ => (1/2:ℝ))]
        _ = 1 := by norm_num

theorem L15_gamblersRuinP_rowStochastic (N : ℕ) : L15_RowStochastic (L15_gamblersRuinP N) :=
  ⟨L15_gamblersRuinP_nonneg N, L15_gamblersRuinP_rowSum N⟩

/-- The absorbing left endpoint `{0}`. -/
def L15_gamblersRuinA (N : ℕ) : Finset (Fin (N+1)) := {(0 : Fin (N+1))}

/-- The absorbing right endpoint `{N}`. -/
def L15_gamblersRuinB (N : ℕ) : Finset (Fin (N+1)) := {Fin.last N}

/-- The explicit closed-form committor `q(i) = i / N` for the symmetric
gambler's-ruin chain. -/
noncomputable def L15_gamblersRuinQ (N : ℕ) : Fin (N+1) → ℝ := fun i => (i : ℝ) / (N : ℝ)

theorem L15_gamblersRuinQ_boundaryA (N : ℕ) :
    ∀ a ∈ L15_gamblersRuinA N, L15_gamblersRuinQ N a = 0 := by
  intro a ha
  simp [L15_gamblersRuinA] at ha
  simp [L15_gamblersRuinQ, ha]

theorem L15_gamblersRuinQ_boundaryB (N : ℕ) (hN : N ≠ 0) :
    ∀ b ∈ L15_gamblersRuinB N, L15_gamblersRuinQ N b = 1 := by
  intro b hb
  simp [L15_gamblersRuinB] at hb
  subst hb
  simp only [L15_gamblersRuinQ, Fin.val_last]
  have : (N : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr hN
  field_simp

theorem L15_gamblersRuinQ_harmonic (N : ℕ) (i : Fin (N+1))
    (hiA : i ∉ L15_gamblersRuinA N) (hiB : i ∉ L15_gamblersRuinB N) :
    L15_gamblersRuinQ N i = ∑ j, L15_gamblersRuinP N i j * L15_gamblersRuinQ N j := by
  simp only [L15_gamblersRuinA, Finset.mem_singleton] at hiA
  simp only [L15_gamblersRuinB, Finset.mem_singleton] at hiB
  have h0 : (i:ℕ) ≠ 0 := fun h => hiA (Fin.ext h)
  have hN : (i:ℕ) ≠ N := fun h => hiB (Fin.ext (by simpa [Fin.val_last] using h))
  have heq : ∀ j, L15_gamblersRuinP N i j =
      (if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1/2:ℝ) else 0) +
      (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1/2:ℝ) else 0) := by
    intro j
    unfold L15_gamblersRuinP
    dsimp only [Matrix.of_apply]
    rw [dif_neg h0, dif_neg hN]
  symm
  calc ∑ j, L15_gamblersRuinP N i j * L15_gamblersRuinQ N j
      = ∑ j, ((if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1))
            then (1/2:ℝ) * L15_gamblersRuinQ N j else 0) +
          (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1))
            then (1/2:ℝ) * L15_gamblersRuinQ N j else 0)) :=
        Finset.sum_congr rfl (fun j _ => by rw [heq j]; split_ifs <;> ring)
    _ = (∑ j, (if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1))
            then (1/2:ℝ) * L15_gamblersRuinQ N j else 0)) +
          (∑ j, (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1))
            then (1/2:ℝ) * L15_gamblersRuinQ N j else 0)) :=
        Finset.sum_add_distrib
    _ = (1/2:ℝ) * L15_gamblersRuinQ N (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) +
          (1/2:ℝ) * L15_gamblersRuinQ N (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) := by
        rw [Fintype.sum_ite_eq' (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1))
              (fun j => (1/2:ℝ) * L15_gamblersRuinQ N j),
            Fintype.sum_ite_eq' (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1))
              (fun j => (1/2:ℝ) * L15_gamblersRuinQ N j)]
    _ = L15_gamblersRuinQ N i := by
        simp only [L15_gamblersRuinQ]
        have hcast : ((((i:ℕ) - 1 : ℕ) : ℝ)) = (i:ℝ) - 1 := by
          have h1 : (1:ℕ) ≤ (i:ℕ) := Nat.one_le_iff_ne_zero.mpr h0
          rw [Nat.cast_sub h1]
          norm_num
        have hcast2 : ((((i:ℕ) + 1 : ℕ) : ℝ)) = (i:ℝ) + 1 := by push_cast; ring
        simp only [hcast, hcast2]
        ring

theorem L15_gamblersRuinQ_isCommittor (N : ℕ) (hN : N ≠ 0) :
    L15_IsCommittor (L15_gamblersRuinP N) (L15_gamblersRuinA N) (L15_gamblersRuinB N)
      (L15_gamblersRuinQ N) :=
  ⟨L15_gamblersRuinQ_boundaryA N, L15_gamblersRuinQ_boundaryB N hN,
    fun i hiA hiB => L15_gamblersRuinQ_harmonic N i hiA hiB⟩

/-! ## L15b — gambler's ruin: biased walk (`p ≠ 1/2`) -/

/-- The biased random walk on `Fin (N+1)`: interior states step down with
probability `1 - p` and up with probability `p`; the endpoints `0` and `N`
remain absorbing. -/
noncomputable def L15_biasedRuinP (N : ℕ) (p : ℝ) : Matrix (Fin (N+1)) (Fin (N+1)) ℝ :=
  Matrix.of fun i j =>
    if h0 : (i:ℕ) = 0 then (if j = i then (1:ℝ) else 0)
    else if hN : (i:ℕ) = N then (if j = i then (1:ℝ) else 0)
    else
      (if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1-p) else 0) +
      (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) then p else 0)

theorem L15_biasedRuinP_nonneg (N : ℕ) (p : ℝ) (hp0 : 0 ≤ p) (hp1 : p ≤ 1) :
    ∀ i j, 0 ≤ L15_biasedRuinP N p i j := by
  intro i j
  unfold L15_biasedRuinP
  dsimp only [Matrix.of_apply]
  split_ifs <;> linarith

theorem L15_biasedRuinP_rowSum (N : ℕ) (p : ℝ) : ∀ i, ∑ j, L15_biasedRuinP N p i j = 1 := by
  intro i
  by_cases h0 : (i:ℕ) = 0
  · have heq : ∀ j, L15_biasedRuinP N p i j = (if j = i then (1:ℝ) else 0) := by
      intro j
      unfold L15_biasedRuinP
      dsimp only [Matrix.of_apply]
      rw [dif_pos h0]
    calc ∑ j, L15_biasedRuinP N p i j = ∑ j, (if j = i then (1:ℝ) else 0) :=
          Finset.sum_congr rfl (fun j _ => heq j)
      _ = 1 := Fintype.sum_ite_eq' i (fun _ => (1:ℝ))
  · by_cases hN : (i:ℕ) = N
    · have heq : ∀ j, L15_biasedRuinP N p i j = (if j = i then (1:ℝ) else 0) := by
        intro j
        unfold L15_biasedRuinP
        dsimp only [Matrix.of_apply]
        rw [dif_neg h0, dif_pos hN]
      calc ∑ j, L15_biasedRuinP N p i j = ∑ j, (if j = i then (1:ℝ) else 0) :=
            Finset.sum_congr rfl (fun j _ => heq j)
        _ = 1 := Fintype.sum_ite_eq' i (fun _ => (1:ℝ))
    · have heq : ∀ j, L15_biasedRuinP N p i j =
          (if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1-p) else 0) +
          (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) then p else 0) := by
        intro j
        unfold L15_biasedRuinP
        dsimp only [Matrix.of_apply]
        rw [dif_neg h0, dif_neg hN]
      calc ∑ j, L15_biasedRuinP N p i j
          = ∑ j, ((if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1-p:ℝ) else 0) +
              (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (p:ℝ) else 0)) :=
            Finset.sum_congr rfl (fun j _ => heq j)
        _ = (∑ j, (if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1-p:ℝ) else 0)) +
              (∑ j, (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (p:ℝ) else 0)) :=
            Finset.sum_add_distrib
        _ = (1-p) + p := by
            rw [Fintype.sum_ite_eq' (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) (fun _ => (1-p:ℝ)),
                Fintype.sum_ite_eq' (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) (fun _ => (p:ℝ))]
        _ = 1 := by ring

theorem L15_biasedRuinP_rowStochastic (N : ℕ) (p : ℝ) (hp0 : 0 ≤ p) (hp1 : p ≤ 1) :
    L15_RowStochastic (L15_biasedRuinP N p) :=
  ⟨L15_biasedRuinP_nonneg N p hp0 hp1, L15_biasedRuinP_rowSum N p⟩

/-- The ratio `r = (1-p)/p` used in the biased gambler's-ruin committor. -/
noncomputable def L15_biasedRuinR (p : ℝ) : ℝ := (1 - p) / p

/-- The explicit closed-form committor `q(i) = (1 - r^i) / (1 - r^N)` for the
biased gambler's-ruin chain, `r = (1 - p) / p`. -/
noncomputable def L15_biasedRuinQ (N : ℕ) (p : ℝ) : Fin (N+1) → ℝ :=
  fun i => (1 - (L15_biasedRuinR p) ^ (i:ℕ)) / (1 - (L15_biasedRuinR p) ^ N)

private lemma L15_biased_r_coeff (p : ℝ) (hp0 : p ≠ 0) :
    (1 - p) + p * (L15_biasedRuinR p) ^ 2 = L15_biasedRuinR p := by
  unfold L15_biasedRuinR
  field_simp
  ring

private lemma L15_biased_r_identity (p : ℝ) (hp0 : p ≠ 0) (k : ℕ) :
    (1 - p) * (L15_biasedRuinR p) ^ k + p * (L15_biasedRuinR p) ^ (k+2) =
      (L15_biasedRuinR p) ^ (k+1) := by
  set r : ℝ := L15_biasedRuinR p with hr_def
  have hc : (1 - p) + p * r ^ 2 = r := L15_biased_r_coeff p hp0
  have expand : r ^ (k+2) = r ^ k * r ^ 2 := by rw [pow_add]
  have expand2 : r ^ (k+1) = r ^ k * r := by rw [pow_add, pow_one]
  rw [expand, expand2]
  have factor : (1 - p) * r ^ k + p * (r ^ k * r ^ 2) = r ^ k * ((1 - p) + p * r ^ 2) := by ring
  rw [factor, hc]

theorem L15_biasedRuinQ_boundaryA (N : ℕ) (p : ℝ) :
    ∀ a ∈ L15_gamblersRuinA N, L15_biasedRuinQ N p a = 0 := by
  intro a ha
  simp [L15_gamblersRuinA] at ha
  simp [L15_biasedRuinQ, ha]

private lemma L15_biased_r_pow_ne_one (p : ℝ) (hp0 : 0 < p) (hp1 : p < 1) (hphalf : p ≠ 1/2)
    (N : ℕ) (hN : N ≠ 0) : (L15_biasedRuinR p) ^ N ≠ 1 := by
  have hrpos : 0 < L15_biasedRuinR p := by
    unfold L15_biasedRuinR
    have h1p : 0 < 1 - p := by linarith
    exact div_pos h1p hp0
  rcases lt_trichotomy p (1/2) with h | h | h
  · have hr1 : 1 < L15_biasedRuinR p := by
      unfold L15_biasedRuinR
      rw [lt_div_iff₀ hp0]
      linarith
    have : 1 < (L15_biasedRuinR p) ^ N := one_lt_pow₀ hr1 hN
    linarith
  · exact absurd h hphalf
  · have hr1 : L15_biasedRuinR p < 1 := by
      unfold L15_biasedRuinR
      rw [div_lt_iff₀ hp0]
      linarith
    have : (L15_biasedRuinR p) ^ N < 1 := pow_lt_one₀ hrpos.le hr1 hN
    linarith

theorem L15_biasedRuinQ_boundaryB (N : ℕ) (p : ℝ) (hp0 : 0 < p) (hp1 : p < 1)
    (hphalf : p ≠ 1/2) (hN : N ≠ 0) :
    ∀ b ∈ L15_gamblersRuinB N, L15_biasedRuinQ N p b = 1 := by
  intro b hb
  simp [L15_gamblersRuinB] at hb
  subst hb
  have hne : (1 : ℝ) - (L15_biasedRuinR p) ^ N ≠ 0 := by
    have := L15_biased_r_pow_ne_one p hp0 hp1 hphalf N hN
    intro hcontra
    apply this
    linarith
  simp only [L15_biasedRuinQ, Fin.val_last]
  field_simp

theorem L15_biasedRuinQ_harmonic (N : ℕ) (p : ℝ) (hp0 : p ≠ 0) (i : Fin (N+1))
    (hiA : i ∉ L15_gamblersRuinA N) (hiB : i ∉ L15_gamblersRuinB N) :
    L15_biasedRuinQ N p i = ∑ j, L15_biasedRuinP N p i j * L15_biasedRuinQ N p j := by
  simp only [L15_gamblersRuinA, Finset.mem_singleton] at hiA
  simp only [L15_gamblersRuinB, Finset.mem_singleton] at hiB
  have h0 : (i:ℕ) ≠ 0 := fun h => hiA (Fin.ext h)
  have hN : (i:ℕ) ≠ N := fun h => hiB (Fin.ext (by simpa [Fin.val_last] using h))
  have heq : ∀ j, L15_biasedRuinP N p i j =
      (if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (1-p:ℝ) else 0) +
      (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) then (p:ℝ) else 0) := by
    intro j
    unfold L15_biasedRuinP
    dsimp only [Matrix.of_apply]
    rw [dif_neg h0, dif_neg hN]
  symm
  calc ∑ j, L15_biasedRuinP N p i j * L15_biasedRuinQ N p j
      = ∑ j, ((if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1))
            then (1-p:ℝ) * L15_biasedRuinQ N p j else 0) +
          (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1))
            then (p:ℝ) * L15_biasedRuinQ N p j else 0)) :=
        Finset.sum_congr rfl (fun j _ => by rw [heq j]; split_ifs <;> ring)
    _ = (∑ j, (if j = (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1))
            then (1-p:ℝ) * L15_biasedRuinQ N p j else 0)) +
          (∑ j, (if j = (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1))
            then (p:ℝ) * L15_biasedRuinQ N p j else 0)) :=
        Finset.sum_add_distrib
    _ = (1-p:ℝ) * L15_biasedRuinQ N p (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1)) +
          (p:ℝ) * L15_biasedRuinQ N p (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1)) := by
        rw [Fintype.sum_ite_eq' (⟨(i:ℕ) - 1, by have := i.isLt; omega⟩ : Fin (N+1))
              (fun j => (1-p:ℝ) * L15_biasedRuinQ N p j),
            Fintype.sum_ite_eq' (⟨(i:ℕ) + 1, by have := i.isLt; omega⟩ : Fin (N+1))
              (fun j => (p:ℝ) * L15_biasedRuinQ N p j)]
    _ = L15_biasedRuinQ N p i := by
        simp only [L15_biasedRuinQ]
        have e1 : (i:ℕ) - 1 + 2 = (i:ℕ) + 1 := by have := i.isLt; omega
        have e2 : (i:ℕ) - 1 + 1 = (i:ℕ) := by have := i.isLt; omega
        have hid := L15_biased_r_identity p hp0 ((i:ℕ) - 1)
        rw [e1, e2] at hid
        have hnum : (1-p) * (1 - (L15_biasedRuinR p) ^ ((i:ℕ) - 1)) +
            p * (1 - (L15_biasedRuinR p) ^ ((i:ℕ) + 1)) =
            1 - (L15_biasedRuinR p) ^ (i:ℕ) := by linear_combination -hid
        rw [← mul_div_assoc, ← mul_div_assoc, ← add_div, hnum]

theorem L15_biasedRuinQ_isCommittor (N : ℕ) (p : ℝ) (hp0 : 0 < p) (hp1 : p < 1)
    (hphalf : p ≠ 1/2) (hN : N ≠ 0) :
    L15_IsCommittor (L15_biasedRuinP N p) (L15_gamblersRuinA N) (L15_gamblersRuinB N)
      (L15_biasedRuinQ N p) :=
  ⟨L15_biasedRuinQ_boundaryA N p, L15_biasedRuinQ_boundaryB N p hp0 hp1 hphalf hN,
    fun i hiA hiB => L15_biasedRuinQ_harmonic N p (ne_of_gt hp0) i hiA hiB⟩

/-! ## L15c — linear-algebraic core and gambler's-ruin uniqueness -/

/-- The difference of two committors for the same data vanishes on the
boundary `A ∪ B`. -/
theorem L15_committor_diff_boundary_zero {n : Type*} [Fintype n] [DecidableEq n]
    {P : Matrix n n ℝ} {A B : Finset n} {q1 q2 : n → ℝ}
    (hq1 : L15_IsCommittor P A B q1) (hq2 : L15_IsCommittor P A B q2) :
    (∀ x ∈ A ∪ B, q1 x - q2 x = 0) := by
  intro x hx
  rcases Finset.mem_union.mp hx with hxA | hxB
  · rw [hq1.1 x hxA, hq2.1 x hxA]; ring
  · rw [hq1.2.1 x hxB, hq2.2.1 x hxB]; ring

/-- The difference of two committors for the same data is harmonic off the
boundary. Together with `L15_committor_diff_boundary_zero`, this is the
linear-algebraic core an absorption argument needs to force to zero; that
final step is not proved in general here (see the claim boundary). -/
theorem L15_committor_diff_harmonic {n : Type*} [Fintype n] [DecidableEq n]
    {P : Matrix n n ℝ} {A B : Finset n} {q1 q2 : n → ℝ}
    (hq1 : L15_IsCommittor P A B q1) (hq2 : L15_IsCommittor P A B q2) :
    ∀ i, i ∉ A → i ∉ B → (q1 i - q2 i) = ∑ j, P i j * (q1 j - q2 j) := by
  intro i hiA hiB
  have h1 := hq1.2.2 i hiA hiB
  have h2 := hq2.2.2 i hiA hiB
  rw [h1, h2, ← Finset.sum_sub_distrib]
  exact Finset.sum_congr rfl (fun j _ => by ring)

/-- Clamped extension of a function on `Fin (N+1)` to all of `ℕ`, agreeing
with the original on `0..N`. Used only to run a plain `ℕ`-indexed induction
for the gambler's-ruin uniqueness proof below; it carries no independent
mathematical content. -/
private def L15_clamp (N : ℕ) (f : Fin (N+1) → ℝ) (k : ℕ) : ℝ :=
  f ⟨min k N, Nat.lt_succ_of_le (min_le_right k N)⟩

private lemma L15_clamp_eq {N : ℕ} (f : Fin (N+1) → ℝ) {k : ℕ} (hk : k ≤ N) :
    L15_clamp N f k = f ⟨k, Nat.lt_succ_of_le hk⟩ := by
  unfold L15_clamp
  congr 1
  exact Fin.ext (min_eq_left hk)

/-- Concrete natural-number form of the gambler's-ruin harmonic equation at
interior index `m+1`, with predecessor `m` and successor `m+2` given
directly as natural-number literals (avoids symbolic `Fin` subtraction
inside the induction below). -/
private lemma L15_gamblersRuinP_harmonic_nat (N m : ℕ) (hm : m + 2 ≤ N) (f : Fin (N+1) → ℝ) :
    ∑ j, L15_gamblersRuinP N (⟨m+1, by omega⟩ : Fin (N+1)) j * f j =
      (1/2:ℝ) * f (⟨m, by omega⟩ : Fin (N+1)) + (1/2:ℝ) * f (⟨m+2, by omega⟩ : Fin (N+1)) := by
  have h0 : (((⟨m+1, by omega⟩ : Fin (N+1)) : ℕ)) ≠ 0 := by simp
  have hNne : (((⟨m+1, by omega⟩ : Fin (N+1)) : ℕ)) ≠ N := by simp; omega
  have heq : ∀ j, L15_gamblersRuinP N (⟨m+1, by omega⟩ : Fin (N+1)) j =
      (if j = (⟨m, by omega⟩ : Fin (N+1)) then (1/2:ℝ) else 0) +
      (if j = (⟨m+2, by omega⟩ : Fin (N+1)) then (1/2:ℝ) else 0) := by
    intro j
    unfold L15_gamblersRuinP
    dsimp only [Matrix.of_apply]
    rw [dif_neg h0, dif_neg hNne]
    simp only [show (m+1:ℕ) - 1 = m from by omega, show (m+1:ℕ) + 1 = m+2 from by omega]
  calc ∑ j, L15_gamblersRuinP N (⟨m+1, by omega⟩ : Fin (N+1)) j * f j
      = ∑ j, ((if j = (⟨m, by omega⟩ : Fin (N+1)) then (1/2:ℝ) * f j else 0) +
          (if j = (⟨m+2, by omega⟩ : Fin (N+1)) then (1/2:ℝ) * f j else 0)) :=
        Finset.sum_congr rfl (fun j _ => by rw [heq j]; split_ifs <;> ring)
    _ = (∑ j, (if j = (⟨m, by omega⟩ : Fin (N+1)) then (1/2:ℝ) * f j else 0)) +
          (∑ j, (if j = (⟨m+2, by omega⟩ : Fin (N+1)) then (1/2:ℝ) * f j else 0)) :=
        Finset.sum_add_distrib
    _ = (1/2:ℝ) * f (⟨m, by omega⟩ : Fin (N+1)) + (1/2:ℝ) * f (⟨m+2, by omega⟩ : Fin (N+1)) := by
        rw [Fintype.sum_ite_eq' (⟨m, by omega⟩ : Fin (N+1)) (fun j => (1/2:ℝ) * f j),
            Fintype.sum_ite_eq' (⟨m+2, by omega⟩ : Fin (N+1)) (fun j => (1/2:ℝ) * f j)]

/-- The increment sequence of a gambler's-ruin committor is constant on
`0..N-1`: harmonicity forces `q(k+1) - q(k)` to be independent of `k`. -/
private lemma L15_gamblersRuin_increment_const (N : ℕ) (q' : Fin (N+1) → ℝ)
    (hq' : L15_IsCommittor (L15_gamblersRuinP N) (L15_gamblersRuinA N) (L15_gamblersRuinB N) q') :
    ∀ k, k ≤ N - 1 →
      L15_clamp N q' (k+1) - L15_clamp N q' k = L15_clamp N q' 1 - L15_clamp N q' 0 := by
  intro k
  induction k with
  | zero => intro _; rfl
  | succ m ih =>
    intro hbound
    have hm : m ≤ N - 1 := by omega
    have hm2 : m + 2 ≤ N := by omega
    have hmem : (⟨m+1, by omega⟩ : Fin (N+1)) ∉ L15_gamblersRuinA N := by
      simp [L15_gamblersRuinA, Fin.ext_iff]
    have hmemB : (⟨m+1, by omega⟩ : Fin (N+1)) ∉ L15_gamblersRuinB N := by
      simp only [L15_gamblersRuinB, Finset.mem_singleton, Fin.ext_iff, Fin.val_last]
      omega
    have hharm := hq'.2.2 (⟨m+1, by omega⟩ : Fin (N+1)) hmem hmemB
    rw [L15_gamblersRuinP_harmonic_nat N m hm2 q'] at hharm
    have hc1 : L15_clamp N q' m = q' (⟨m, by omega⟩ : Fin (N+1)) := L15_clamp_eq q' (by omega)
    have hc2 : L15_clamp N q' (m+1) = q' (⟨m+1, by omega⟩ : Fin (N+1)) := L15_clamp_eq q' (by omega)
    have hc3 : L15_clamp N q' (m+2) = q' (⟨m+2, by omega⟩ : Fin (N+1)) := L15_clamp_eq q' (by omega)
    rw [hc2, hc3]
    have ihm := ih hm
    rw [hc1, hc2] at ihm
    linarith [hharm, ihm]

/-- Telescoping the constant increment: every clamped value is an exact
multiple of the base increment. -/
private lemma L15_gamblersRuin_telescope (N : ℕ) (q' : Fin (N+1) → ℝ)
    (hq' : L15_IsCommittor (L15_gamblersRuinP N) (L15_gamblersRuinA N) (L15_gamblersRuinB N) q') :
    ∀ k, k ≤ N → L15_clamp N q' k - L15_clamp N q' 0 =
      (k:ℝ) * (L15_clamp N q' 1 - L15_clamp N q' 0) := by
  intro k
  induction k with
  | zero => intro _; simp
  | succ m ih =>
    intro hbound
    have hm : m ≤ N := by omega
    have hm1 : m ≤ N - 1 := by omega
    have hinc := L15_gamblersRuin_increment_const N q' hq' m hm1
    have ihm := ih hm
    have goal_eq : L15_clamp N q' (m+1) - L15_clamp N q' 0 =
        (L15_clamp N q' (m+1) - L15_clamp N q' m) + (L15_clamp N q' m - L15_clamp N q' 0) := by
      ring
    rw [goal_eq, hinc, ihm]
    push_cast
    ring

/-- Uniqueness of the gambler's-ruin committor: any committor for the
symmetric gambler's-ruin chain must equal the explicit affine solution
`i / N`. Proved by explicit induction on the constant-increment structure
of the harmonic equation — the idea file's chain-specific fallback route,
not the general finite-absorption / substochastic-power argument (which is
not proved here; see the claim boundary). -/
theorem L15_gamblersRuinQ_unique (N : ℕ) (hN : N ≠ 0) (q' : Fin (N+1) → ℝ)
    (hq' : L15_IsCommittor (L15_gamblersRuinP N) (L15_gamblersRuinA N) (L15_gamblersRuinB N) q') :
    q' = L15_gamblersRuinQ N := by
  have hN0 : (0:ℝ) < (N:ℝ) := by
    have : 0 < N := Nat.pos_of_ne_zero hN
    exact_mod_cast this
  have hq0 : L15_clamp N q' 0 = 0 := by
    rw [L15_clamp_eq q' (by omega : (0:ℕ) ≤ N)]
    have hmem : (⟨0, by omega⟩ : Fin (N+1)) ∈ L15_gamblersRuinA N := by
      simp [L15_gamblersRuinA]
    exact hq'.1 (⟨0, by omega⟩ : Fin (N+1)) hmem
  have hqN : L15_clamp N q' N = 1 := by
    rw [L15_clamp_eq q' (le_refl N)]
    have hmem : (⟨N, by omega⟩ : Fin (N+1)) ∈ L15_gamblersRuinB N := by
      simp [L15_gamblersRuinB, Fin.ext_iff, Fin.val_last]
    exact hq'.2.1 (⟨N, by omega⟩ : Fin (N+1)) hmem
  have htel := L15_gamblersRuin_telescope N q' hq' N (le_refl N)
  rw [hq0, hqN] at htel
  have he0 : L15_clamp N q' 1 - L15_clamp N q' 0 = 1 / (N:ℝ) := by
    rw [hq0]
    rw [eq_div_iff (ne_of_gt hN0)]
    linear_combination -htel
  funext i
  have hi : i.val ≤ N := by omega
  have htel_i := L15_gamblersRuin_telescope N q' hq' i.val hi
  rw [he0] at htel_i
  rw [hq0] at htel_i
  have hclamp_i : L15_clamp N q' i.val = q' i := by
    rw [L15_clamp_eq q' hi]
  rw [hclamp_i] at htel_i
  simp only [L15_gamblersRuinQ]
  rw [mul_one_div, sub_zero] at htel_i
  exact_mod_cast htel_i

end NoeticDiffusion
