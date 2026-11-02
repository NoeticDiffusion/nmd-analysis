import Mathlib.Data.Finset.Basic
import Mathlib.Data.Fintype.Basic
import Mathlib.Tactic.NormNum

/-!
# TRANS P0 hitting: occupancy ≠ finite first-hit ≠ eventual committor

This module is the finite-path half of the NDT-TRANS Lean P0 set in
`formalization/science_lead/sl_lean_001.md` (T4 and T5). It uses a
deterministic successor on a finite type, which is enough for the
constructive non-equivalences and for the absorbing collapse.

* **T4.** Terminal occupancy `O_T(x;B) := (f^[T] x ∈ B)` is not the
  finite-horizon first-hit `q_T(x;A,B)`. On the path `x → b → c` with
  `B = {b}` and `T = 2` the process has hit `B` (`q₂ = true`) but is no
  longer in `B` at the endpoint (`O₂ = false`). If `A` and `B` are disjoint
  and both absorbing, the two predicates coincide.
* **T5.** Finite-horizon first-hit is monotone in the horizon and is
  implied by eventual hitting. On `x → c → B` with `T = 1` the finite
  predicate is false while the eventual predicate is true.

Computational background (not a hypothesis of any theorem here): Astra
TRANS-PRED records unresolved finite-grid paths as distinct from eventual
destination truth, and treats endpoint occupancy as a different object from
first-hit (`eventual_committor: false`, `endpoint_occupancy: false` in the
PRED-002 spec). Those are experimental-discipline facts; the theorems below
are exact statements about deterministic iterates.

## Claim boundary

Deterministic finite-state paths only. Occupancy and first-hit are
Booleans (0-1 laws of a Dirac kernel), not real-valued probabilities on a
random walk. No continuous-time hitting time, no PDE committor, and no
claim that an empirical TRANS ledger recovers `q_∞`. The absorbing
equality is the exact collapse hypothesis; without absorption the T4
counterexample applies.
-/

namespace NoeticDiffusion

/-! ## Deterministic occupancy and finite first-hit -/

variable {n : Type*}

/-- `S` is absorbing for the successor `f` when every point of `S` is a
fixed point of `f`. -/
def Trans_IsAbsorbing (f : n → n) (S : Finset n) : Prop :=
  ∀ s ∈ S, f s = s

/-- Terminal occupancy: the iterate at horizon `T` lands in `B`. -/
def Trans_occupancy (f : n → n) (T : ℕ) (x : n) (B : Finset n) : Prop :=
  f^[T] x ∈ B

/-- Finite-horizon first-hit committor predicate: some time `t ≤ T` lands in
`B` before any visit to `A`. Matches `q_T(x;A,B) = 1{τ_B < τ_A, τ_B ≤ T}`
on a deterministic path, with `τ_S = inf{t ≥ 0 : f^[t] x ∈ S}`. -/
def Trans_finiteCommittor (f : n → n) (T : ℕ) (x : n) (A B : Finset n) : Prop :=
  ∃ t : ℕ, t ≤ T ∧ f^[t] x ∈ B ∧ ∀ s : ℕ, s < t → f^[s] x ∉ A

/-- Eventual first-hit: some finite horizon succeeds. -/
def Trans_eventualCommittor (f : n → n) (x : n) (A B : Finset n) : Prop :=
  ∃ T : ℕ, Trans_finiteCommittor f T x A B

/-- Absorbing points are fixed by every iterate. -/
theorem Trans_iterate_eq_of_absorbing {f : n → n}
    {S : Finset n} (hf : Trans_IsAbsorbing f S) {x : n} (hx : x ∈ S)
    (t : ℕ) : f^[t] x = x := by
  induction t with
  | zero => rfl
  | succ t ih =>
      rw [Function.iterate_succ_apply', ih, hf x hx]

/-- **T5a.** Finite first-hit is monotone in the horizon. -/
theorem TransT5_finiteCommittor_mono {f : n → n} {T1 T2 : ℕ} {x : n}
    {A B : Finset n} (hT : T1 ≤ T2)
    (hq : Trans_finiteCommittor f T1 x A B) :
    Trans_finiteCommittor f T2 x A B := by
  obtain ⟨t, ht, hB, hA⟩ := hq
  exact ⟨t, le_trans ht hT, hB, hA⟩

/-- **T5a.** A successful finite-horizon first-hit is an eventual first-hit. -/
theorem TransT5_finite_le_eventual {f : n → n} {T : ℕ} {x : n}
    {A B : Finset n} (hq : Trans_finiteCommittor f T x A B) :
    Trans_eventualCommittor f x A B :=
  ⟨T, hq⟩

/-- **T4+.** If `A` and `B` are disjoint and both absorbing, terminal
occupancy at `T` coincides with finite first-hit of `B` before `A`. -/
theorem TransT4_occupancy_eq_finiteCommittor_of_absorbing
    {f : n → n} {A B : Finset n}
    (hfA : Trans_IsAbsorbing f A) (hfB : Trans_IsAbsorbing f B)
    (hdisj : Disjoint A B) (x : n) (T : ℕ) :
    Trans_occupancy f T x B ↔ Trans_finiteCommittor f T x A B := by
  constructor
  · intro hOcc
    refine ⟨T, le_rfl, hOcc, ?_⟩
    intro s hs hsA
    have hsT : s ≤ T := Nat.le_of_lt hs
    have hstay : f^[T] x = f^[s] x := by
      have hT : T = (T - s) + s := (Nat.sub_add_cancel hsT).symm
      rw [hT, Function.iterate_add_apply, Trans_iterate_eq_of_absorbing hfA hsA]
    have hA : f^[T] x ∈ A := by
      rw [hstay]
      exact hsA
    exact (Finset.disjoint_left.mp hdisj) hA hOcc
  · intro ⟨t, ht, htB, _hA⟩
    have hstay : f^[T] x = f^[t] x := by
      have hT : T = (T - t) + t := (Nat.sub_add_cancel ht).symm
      rw [hT, Function.iterate_add_apply, Trans_iterate_eq_of_absorbing hfB htB]
    change f^[T] x ∈ B
    rw [hstay]
    exact htB

/-! ## T4 counterexample: `x → b → c`, `B = {b}`, `T = 2` -/

/-- Deterministic path `0 → 1 → 2 → 2 → ⋯` on `Fin 3`. -/
def Trans_pathNext : Fin 3 → Fin 3
  | ⟨0, _⟩ => 1
  | ⟨1, _⟩ => 2
  | ⟨2, _⟩ => 2

theorem Trans_pathNext_zero : Trans_pathNext 0 = 1 := rfl
theorem Trans_pathNext_one : Trans_pathNext 1 = 2 := rfl
theorem Trans_pathNext_two : Trans_pathNext 2 = 2 := rfl

private lemma Trans_path_iterate_zero : Trans_pathNext^[0] 0 = 0 := rfl

private lemma Trans_path_iterate_one : Trans_pathNext^[1] 0 = 1 :=
  Trans_pathNext_zero

private lemma Trans_path_iterate_two : Trans_pathNext^[2] 0 = 2 := by
  rw [Function.iterate_succ_apply', Trans_path_iterate_one, Trans_pathNext_one]

/-- The unused / unreached destination `A` in the T4 counterexample. -/
def Trans_T4_A : Finset (Fin 3) := ∅

/-- Transient set `B = {b}` on the path `x → b → c`. -/
def Trans_T4_B : Finset (Fin 3) := {1}

/-- Occupancy at `T = 2` fails: the path sits at `c`, not at `b`. -/
theorem TransT4_occupancy_false :
    ¬ Trans_occupancy Trans_pathNext 2 0 Trans_T4_B := by
  simp only [Trans_occupancy, Trans_T4_B, Trans_path_iterate_two]
  decide

/-- Finite first-hit at `T = 2` succeeds: the path visits `b` at time `1`. -/
theorem TransT4_finiteCommittor_true :
    Trans_finiteCommittor Trans_pathNext 2 0 Trans_T4_A Trans_T4_B := by
  refine ⟨1, Nat.succ_le_succ (Nat.zero_le _), ?_, ?_⟩
  · simpa [Trans_T4_B] using Trans_path_iterate_one
  · intro s hs
    have hs0 : s = 0 := Nat.lt_one_iff.mp hs
    subst hs0
    simp [Trans_T4_A]

/-- **T4.** Terminal occupancy and finite first-hit are not the same
predicate: on `x → b → c` with `B = {b}` and `T = 2` the first-hit is true
and occupancy is false. -/
theorem TransT4_occupancy_ne_finiteCommittor :
    Trans_finiteCommittor Trans_pathNext 2 0 Trans_T4_A Trans_T4_B ∧
    ¬ Trans_occupancy Trans_pathNext 2 0 Trans_T4_B :=
  ⟨TransT4_finiteCommittor_true, TransT4_occupancy_false⟩

/-! ## T5 strict counterexample: `x → c → B`, `T = 1` -/

/-- Eventual destination `{B}` on the same three-point path. -/
def Trans_T5_B : Finset (Fin 3) := {2}

private lemma Trans_path_iterate_two_from_zero_mem :
    Trans_pathNext^[2] 0 ∈ Trans_T5_B := by
  simp [Trans_T5_B, Trans_path_iterate_two]

/-- At horizon `1` the path has only reached `c`, not `B`. -/
theorem TransT5_finite_false :
    ¬ Trans_finiteCommittor Trans_pathNext 1 0 Trans_T4_A Trans_T5_B := by
  intro ⟨t, ht, htB, _⟩
  cases t with
  | zero => simp [Trans_T5_B] at htB
  | succ t =>
      cases t with
      | zero =>
          simp [Trans_T5_B, Trans_pathNext_zero] at htB
      | succ t =>
          exact Nat.not_succ_le_zero t (Nat.le_of_succ_le_succ ht)

/-- The same path does hit `B` at time `2`, so the eventual committor is true. -/
theorem TransT5_eventual_true :
    Trans_eventualCommittor Trans_pathNext 0 Trans_T4_A Trans_T5_B := by
  refine ⟨2, 2, le_rfl, Trans_path_iterate_two_from_zero_mem, ?_⟩
  intro s hs
  simp [Trans_T4_A]

/-- **T5b.** Finite-horizon destination probability is not eventual
commitment: `q_1 = false` while `q_∞ = true` on `x → c → B`. -/
theorem TransT5_finite_lt_eventual :
    ¬ Trans_finiteCommittor Trans_pathNext 1 0 Trans_T4_A Trans_T5_B ∧
    Trans_eventualCommittor Trans_pathNext 0 Trans_T4_A Trans_T5_B :=
  ⟨TransT5_finite_false, TransT5_eventual_true⟩

end NoeticDiffusion
