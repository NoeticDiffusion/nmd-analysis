import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Order.Basic
import Mathlib.Algebra.Order.Field.Basic
import Mathlib.Algebra.Order.Ring.Unbundled.Basic

/-! # L18: Slow-branch accessibility model — clip invariants, sigmoid-gate
monotonicity, zero-coupling identities, guards, and hub over-linking

This module is **simulator-internal**. It formalizes exact algebraic facts
about the discrete-time toy update rule implemented in the frozen
`cytodend_accessmodel` package (per the idea file, vendored outside
`ndt-simulator`, reported at
`I:\AAA_PYTHON_REPOS_BACKUP\cytodendaccessmodel\src\cytodend_accessmodel`; the
exact package path was not independently re-verified from this session, in
line with the idea file's fallback instruction). No theorem here says
anything about dendrites, neurons, or biology.

Source of the equations (as stated in the idea file, to be taken as the
self-contained specification for this Lean module):
`J:\repos\nmd-analysis\project\lean\fable_ideas\08_slow_branch_gate_invariants.md`,
§2 "The implemented update", §3 items L18a-L18e. The per-branch slow-memory
update there is (explicit Euler, discrete time)

  `M_{t+1} = clip(0, M_max, M_t + η · (write_t - decay · M_t))`

with `clip(lo, hi, x) = max(lo, min(hi, x))`, and the multiplicative access
gate uses a logistic/sigmoid gate `sigmoid(k, θ, x) = 1 / (1 + exp(-(k·(x-θ))))`
gating on `M_t` (`slow_access_b = sigmoid(g_s · M_b)`, a `θ = 0` special case
of the general two-parameter gate formalized here as `sigmoidGate`). Simulator
evidence for these facts is catalogued in the idea file §1 (test file line
numbers were not independently re-run from this session; the Lean statements
below are self-contained algebraic claims about the equations as written, not
claims about the Python code or its test suite).

## Claim boundary

Theorems about a discrete-time toy model with explicit real parameters. No
biology, no claim about dendrites or memory, no probability (noise/write
terms are arbitrary real inputs, not random variables), no continuous-time
ODE. `clip`, `sigmoidGate`, and the slow-branch update are definitions fixed
by this file; every theorem states its real-valued hypotheses explicitly
(`0 ≤ η`, `0 ≤ Mmax`, `0 < k`, sign conditions on `g`/`write`/`decay`, guard
inequalities `G-C1`/`G-C2`). The hub over-linking and cap-homogeneity results
are pure finite-sum/algebra facts about nonnegative weighted sums and the
`clip` definition; they say nothing about which trace-to-branch allocations
`a` or memory profiles `M` actually occur in the simulator. This module
produces **no S7 rows** (see `README.md` build section): it is not part of
the NDT v2 core inventory.

`clip` is owned by this module for the whole `fable_ideas` batch: it is
defined exactly as `def clip (lo hi x : ℝ) : ℝ := max lo (min hi x)`, with a
deliberately light import set, so that the parallel L20 gate can import
`Noetic.SlowBranchModel` for this one definition without pulling in the rest
of the slow-branch model.
-/

namespace NoeticDiffusion

/-! ## L18a — clip invariants

`clip lo hi x = max lo (min hi x)` clamps `x` into `[lo, hi]` when `lo ≤ hi`.
The discrete update invariant `slowBranch_clip_bounds` shows that any
sequence built by repeatedly clamping into `[0, Mmax]` stays in `[0, Mmax]`
forever, regardless of the increment sequence `Δ` or the gain `η` — the
clamp alone enforces the bound at every step. -/

/-- Clamp `x` into `[lo, hi]`. Canonical owner: this declaration is shared
across the `fable_ideas` L18/L20 batch; do not redefine it elsewhere. -/
def clip (lo hi x : ℝ) : ℝ := max lo (min hi x)

/-- `clip lo hi x ≤ hi` whenever `lo ≤ hi`. -/
theorem clip_le (lo hi x : ℝ) (h : lo ≤ hi) : clip lo hi x ≤ hi :=
  max_le h (min_le_left hi x)

/-- `lo ≤ clip lo hi x`, unconditionally (no hypothesis on `lo`, `hi` is
needed for this direction). -/
theorem clip_ge_lo (lo hi x : ℝ) : lo ≤ clip lo hi x := le_max_left lo (min hi x)

/-- `clip` is the identity on `[lo, hi]`. -/
theorem clip_of_mem (lo hi x : ℝ) (h1 : lo ≤ x) (h2 : x ≤ hi) : clip lo hi x = x := by
  unfold clip
  rw [min_eq_right h2, max_eq_right h1]

/-- `clip` is idempotent once `lo ≤ hi`. -/
theorem clip_idem (lo hi x : ℝ) (h : lo ≤ hi) : clip lo hi (clip lo hi x) = clip lo hi x :=
  clip_of_mem lo hi (clip lo hi x) (clip_ge_lo lo hi x) (clip_le lo hi x h)

/-- `clip lo hi` is monotone in its third argument. -/
theorem clip_mono (lo hi x y : ℝ) (hxy : x ≤ y) : clip lo hi x ≤ clip lo hi y := by
  unfold clip
  exact max_le_max le_rfl (min_le_min le_rfl hxy)

/-- `clip` saturates to `lo` once `x ≤ lo` (given `lo ≤ hi`). -/
theorem clip_eq_lo_of_le (lo hi x : ℝ) (h : lo ≤ hi) (hx : x ≤ lo) : clip lo hi x = lo := by
  unfold clip
  rw [min_eq_right (hx.trans h), max_eq_left hx]

/-- `clip` saturates to `hi` once `hi ≤ x` (given `lo ≤ hi`). -/
theorem clip_eq_hi_of_ge (lo hi x : ℝ) (h : lo ≤ hi) (hx : hi ≤ x) : clip lo hi x = hi := by
  unfold clip
  rw [min_eq_left hx, max_eq_right h]

/-- Helper for `guard_GC2_bound`: `clip 0 Mmax y ≤ z` whenever `y ≤ z` and
`0 ≤ z` (no sign hypothesis on `y` itself is needed, since `clip` can only
raise a very negative `y` up to `0 ≤ z`). -/
private lemma clip_le_of_le (Mmax y z : ℝ) (h : y ≤ z) (hz : 0 ≤ z) :
    clip 0 Mmax y ≤ z := by
  unfold clip
  have h2 : max 0 (min Mmax y) ≤ max 0 y := max_le_max le_rfl (min_le_right Mmax y)
  have h3 : max 0 y ≤ max 0 z := max_le_max le_rfl h
  have h4 : max 0 z = z := max_eq_right hz
  linarith [h2, h3, h4]

/-- Discrete update invariant: for **any** sequence `M : ℕ → ℝ` satisfying
`M (t+1) = clip 0 Mmax (M t + η * Δ t)` for every `t`, with `M 0 ∈ [0, Mmax]`,
we have `M t ∈ [0, Mmax]` for every `t`. Proved by induction on `t`; the
inductive step does not even need the induction hypothesis, since the clamp
re-enforces the bound at every single step regardless of the previous
state. -/
theorem slowBranch_clip_bounds (Mmax η : ℝ) (hMmax : 0 ≤ Mmax) (Δ M : ℕ → ℝ)
    (hM0 : 0 ≤ M 0 ∧ M 0 ≤ Mmax)
    (hstep : ∀ t, M (t + 1) = clip 0 Mmax (M t + η * Δ t)) :
    ∀ t, 0 ≤ M t ∧ M t ≤ Mmax := by
  intro t
  induction t with
  | zero => exact hM0
  | succ t _ih =>
      rw [hstep t]
      exact ⟨clip_ge_lo 0 Mmax _, clip_le 0 Mmax _ hMmax⟩

/-! ## L18b — sigmoid gate monotonicity

`sigmoidGate k θ x = 1 / (1 + exp(-(k·(x-θ))))` is the model's logistic
access gate (`fast_access_b`, `slow_access_b` in the idea file are both
instances of this two-parameter family, `θ = 0` for the slow-access gate). -/

/-- Logistic gate with slope `k` and threshold `θ`. -/
noncomputable def sigmoidGate (k θ x : ℝ) : ℝ := 1 / (1 + Real.exp (-(k * (x - θ))))

/-- The gate value is always strictly positive. -/
theorem sigmoidGate_pos (k θ x : ℝ) : 0 < sigmoidGate k θ x := by
  unfold sigmoidGate
  positivity

/-- The gate value is always strictly below `1`. -/
theorem sigmoidGate_lt_one (k θ x : ℝ) : sigmoidGate k θ x < 1 := by
  unfold sigmoidGate
  rw [div_lt_one (by positivity)]
  linarith [Real.exp_pos (-(k * (x - θ)))]

/-- For a positive slope `k`, the gate is monotone (nondecreasing) in `x`. -/
theorem sigmoidGate_mono (k θ : ℝ) (hk : 0 < k) {x y : ℝ} (hxy : x ≤ y) :
    sigmoidGate k θ x ≤ sigmoidGate k θ y := by
  unfold sigmoidGate
  have hexp : Real.exp (-(k * (y - θ))) ≤ Real.exp (-(k * (x - θ))) :=
    Real.exp_le_exp.mpr (by nlinarith)
  have ha : (0 : ℝ) < 1 + Real.exp (-(k * (y - θ))) := by positivity
  have hab : 1 + Real.exp (-(k * (y - θ))) ≤ 1 + Real.exp (-(k * (x - θ))) := by linarith
  exact one_div_le_one_div_of_le ha hab

/-- For a positive slope `k`, the gate is antitone (nonincreasing) in the
threshold `θ`: raising the threshold never raises the gate value at a fixed
input. -/
theorem sigmoidGate_anti (k x : ℝ) (hk : 0 < k) {θ1 θ2 : ℝ} (hθ : θ1 ≤ θ2) :
    sigmoidGate k θ2 x ≤ sigmoidGate k θ1 x := by
  unfold sigmoidGate
  have hexp : Real.exp (-(k * (x - θ1))) ≤ Real.exp (-(k * (x - θ2))) :=
    Real.exp_le_exp.mpr (by nlinarith)
  have ha : (0 : ℝ) < 1 + Real.exp (-(k * (x - θ1))) := by positivity
  have hab : 1 + Real.exp (-(k * (x - θ1))) ≤ 1 + Real.exp (-(k * (x - θ2))) := by linarith
  exact one_div_le_one_div_of_le ha hab

/-- The gate takes value `1/2` exactly at its own threshold, for every slope
`k` (including `k = 0`). -/
theorem sigmoidGate_eq_half (k θ : ℝ) : sigmoidGate k θ θ = 1 / 2 := by
  unfold sigmoidGate
  rw [sub_self, mul_zero, neg_zero, Real.exp_zero]
  norm_num

/-! ## L18c — zero-write / zero-coupling identities

The slow-branch write update `M_{t+1} = clip 0 Mmax (M_t + η·(write_t -
decay·M_t))`: `slowBranch_step_of_eta_zero` and
`slowBranch_step_of_write_decay_zero` are the two hypotheses under which the
write vanishes and the step reduces to a pure clamp of the previous state;
`slowBranch_const_of_step_zero` then shows that clamp is the identity once
the state is already in range, matching the "zero coupling ⇒ baseline
identity" simulator finding (idea file §1, `test_v3_0_guards.py:110-113,
201-212`, t6_4). `slowBranch_coupling_term_zero` is the corresponding
algebraic fact for the tree-coupled fast-branch input term. -/

/-- If the learning rate `η` is zero, the write step collapses to a pure
clamp of the previous state, regardless of `write` and `decay`. -/
theorem slowBranch_step_of_eta_zero (Mmax η write decay M Mnext : ℝ) (hη : η = 0)
    (hstep : Mnext = clip 0 Mmax (M + η * (write - decay * M))) :
    Mnext = clip 0 Mmax M := by
  subst hη
  simp only [zero_mul, add_zero] at hstep
  exact hstep

/-- If both the write drive and the decay are zero, the write step collapses
to a pure clamp of the previous state, regardless of `η`. -/
theorem slowBranch_step_of_write_decay_zero (Mmax η write decay M Mnext : ℝ)
    (hwrite : write = 0) (hdecay : decay = 0)
    (hstep : Mnext = clip 0 Mmax (M + η * (write - decay * M))) :
    Mnext = clip 0 Mmax M := by
  subst hwrite; subst hdecay
  simp only [zero_mul, sub_zero, mul_zero, add_zero] at hstep
  exact hstep

/-- Once the state is in range, a pure clamp step is the identity: combined
with either zero hypothesis above, the memory `M` stays constant. -/
theorem slowBranch_const_of_step_zero (Mmax M Mnext : ℝ)
    (hmem : 0 ≤ M ∧ M ≤ Mmax) (hstep : Mnext = clip 0 Mmax M) :
    Mnext = M := by
  rw [hstep]
  exact clip_of_mem 0 Mmax M hmem.1 hmem.2

/-- If the tree-coupling gain `g` is zero, the fast-branch input term
`g * M * s` contributed by the slow memory vanishes identically. -/
theorem slowBranch_coupling_term_zero (g M s : ℝ) (hg : g = 0) : g * M * s = 0 := by
  subst hg; ring

/-! ## L18d — guards G-C1 / G-C2

`G-C1`-style guard: if the gate input is below threshold by margin `δ`, the
gate value is bounded away from `1/2` by an explicit exponential factor.
`G-C2`-style guard: with increments bounded by `Δmax` and starting from
`M 0 = 0`, the memory after `t` steps is bounded by `t·η·Δmax`, so reaching
saturation `Mmax` needs at least `Mmax / (η·Δmax)` steps — the exact
"bounded increments ⇒ bounded number of steps to saturate" statement from
the idea file, specialized to the algebraic clamp/gain structure (not the
full tree-coupled guard inequalities `κ_coop Σ K_bc ≤ 1` /
`(κ_comp/Mmax)·Σ K_bc·max(0,drive) < 1`, which are recorded under "Not
proved" below). -/

/-- G-C1-style guard: if `x` is below the threshold `θ` by margin `δ > 0`
(`x ≤ θ - δ`) and the slope `k > 0`, the gate value is bounded by the exact
value the gate takes at the margin, `1 / (1 + exp(k·δ))` (which is `< 1/2`
for `δ > 0`). -/
theorem guard_GC1 (k θ δ x : ℝ) (hk : 0 < k) (_hδ : 0 < δ) (hx : x ≤ θ - δ) :
    sigmoidGate k θ x ≤ 1 / (1 + Real.exp (k * δ)) := by
  have hmono : sigmoidGate k θ x ≤ sigmoidGate k θ (θ - δ) :=
    sigmoidGate_mono k θ hk hx
  have heq : sigmoidGate k θ (θ - δ) = 1 / (1 + Real.exp (k * δ)) := by
    unfold sigmoidGate
    have hexp_eq : -(k * (θ - δ - θ)) = k * δ := by ring
    rw [hexp_eq]
  rwa [heq] at hmono

/-- G-C2-style bound: for any sequence `M` starting at `0` and updated by
`M (t+1) = clip 0 Mmax (M t + η * Δ t)` with `0 ≤ η`, increments bounded by
`Δ t ≤ Δmax` (`0 ≤ Δmax`), the state after `t` steps is bounded by the
linear-growth envelope `t * (η * Δmax)`, and stays nonnegative. Proved by
induction; the clamp can only *help* (never hurts) this upper bound. -/
theorem guard_GC2_bound (Mmax η Δmax : ℝ) (hη : 0 ≤ η) (hΔmax : 0 ≤ Δmax)
    (Δ M : ℕ → ℝ) (hΔ : ∀ t, Δ t ≤ Δmax) (hM0 : M 0 = 0)
    (hstep : ∀ t, M (t + 1) = clip 0 Mmax (M t + η * Δ t)) :
    ∀ t : ℕ, M t ≤ (t : ℝ) * (η * Δmax) ∧ 0 ≤ M t := by
  intro t
  induction t with
  | zero => simp [hM0]
  | succ t ih =>
      obtain ⟨ihb, ihnn⟩ := ih
      have hprod : (0 : ℝ) ≤ η * Δmax := mul_nonneg hη hΔmax
      have hz : (0 : ℝ) ≤ M t + η * Δmax := by linarith
      have hy : M t + η * Δ t ≤ M t + η * Δmax := by
        have hstepΔ : η * Δ t ≤ η * Δmax := mul_le_mul_of_nonneg_left (hΔ t) hη
        linarith
      have hbound : M (t + 1) ≤ M t + η * Δmax := by
        rw [hstep t]
        exact clip_le_of_le Mmax _ _ hy hz
      have hnn : 0 ≤ M (t + 1) := by
        rw [hstep t]
        exact clip_ge_lo 0 Mmax _
      refine ⟨?_, hnn⟩
      push_cast
      calc M (t + 1) ≤ M t + η * Δmax := hbound
        _ ≤ (t : ℝ) * (η * Δmax) + η * Δmax := by linarith
        _ = ((t : ℝ) + 1) * (η * Δmax) := by ring

/-- G-C2 corollary: if the state has reached saturation (`M t = Mmax`) by
step `t`, and the per-step gain `η * Δmax` is strictly positive, then at
least `Mmax / (η * Δmax)` steps were needed — the exact "steps to saturate"
bound from the idea file. -/
theorem guard_GC2 (Mmax η Δmax : ℝ) (hη : 0 ≤ η) (hΔmax : 0 ≤ Δmax)
    (Δ M : ℕ → ℝ) (hΔ : ∀ t, Δ t ≤ Δmax) (hM0 : M 0 = 0)
    (hstep : ∀ t, M (t + 1) = clip 0 Mmax (M t + η * Δ t))
    (t : ℕ) (hsat : M t = Mmax) (hpos : 0 < η * Δmax) :
    Mmax / (η * Δmax) ≤ (t : ℝ) := by
  have hbound := (guard_GC2_bound Mmax η Δmax hη hΔmax Δ M hΔ hM0 hstep t).1
  rw [hsat] at hbound
  rw [div_le_iff₀ hpos]
  exact hbound

/-! ## L18e — hub over-linking and cap-homogeneity

`linking_ge_hub_term` is the exact finite-sum fact behind the "hub-overlap
motifs failed specificity" finding (idea file §1, article *Slow Branch-Level
Accessibility…* `draft.md` ~line 262): a linking score that sums nonnegative
per-branch terms is at least any single one of those terms, in particular
the term contributed by one shared hub branch. `capHomogeneity_clip` is the
degree-one homogeneity of `clip` under simultaneously scaling the cap and the
input by the same positive factor, the algebraic core of the "finite-resource
cap has an exact null direction" finding (idea file §1, article
*Coupled_Resource_Reachability_over_Closure_Epoch* ~line 130). -/

/-- Hub over-linking: for nonnegative allocations `a` and nonnegative memory
`M`, the linking score `Σ_j a μ j * a ν j * M j` is at least the contribution
of any single branch `h` (in particular a shared hub). -/
theorem linking_ge_hub_term {Tr Br : Type*} [Fintype Br] (a : Tr → Br → ℝ) (M : Br → ℝ)
    (ha : ∀ i j, 0 ≤ a i j) (hM : ∀ j, 0 ≤ M j) (μ ν : Tr) (h : Br) :
    a μ h * a ν h * M h ≤ ∑ j, a μ j * a ν j * M j :=
  Finset.single_le_sum (f := fun j => a μ j * a ν j * M j)
    (fun j _ => mul_nonneg (mul_nonneg (ha μ j) (ha ν j)) (hM j)) (Finset.mem_univ h)

/-- If every one of two traces has positive allocation on a hub branch `h`
with positive structural accessibility `M h`, the two traces are linked
(`0 < linking score`): specificity is impossible through the hub alone. -/
theorem linking_pos_of_hub_pos {Tr Br : Type*} [Fintype Br] (a : Tr → Br → ℝ) (M : Br → ℝ)
    (ha : ∀ i j, 0 ≤ a i j) (hM : ∀ j, 0 ≤ M j) (μ ν : Tr) (h : Br)
    (hμ : 0 < a μ h) (hν : 0 < a ν h) (hMh : 0 < M h) :
    0 < ∑ j, a μ j * a ν j * M j := by
  have hterm : 0 < a μ h * a ν h * M h := by positivity
  exact lt_of_lt_of_le hterm (linking_ge_hub_term a M ha hM μ ν h)

/-- Optional sharpening: at a saturated hub (`M h = Mmax`), the linking score
is bounded below by `a μ h * a ν h * Mmax`, independent of every other
branch. -/
theorem linking_ge_hub_saturated {Tr Br : Type*} [Fintype Br] (a : Tr → Br → ℝ) (M : Br → ℝ)
    (Mmax : ℝ) (ha : ∀ i j, 0 ≤ a i j) (hM : ∀ j, 0 ≤ M j) (μ ν : Tr) (h : Br)
    (hMh : M h = Mmax) :
    a μ h * a ν h * Mmax ≤ ∑ j, a μ j * a ν j * M j := by
  rw [← hMh]
  exact linking_ge_hub_term a M ha hM μ ν h

/-- Cap-homogeneity null direction: scaling both the cap `Mmax` and the input
`x` by the same positive factor `c` scales `clip 0 Mmax x` by exactly `c`.
This is the exact algebraic fact behind "the finite-resource cap map is
homogeneous of degree `0` on the cap-active region, hence has a singular
derivative along `P` itself" (idea file §3, L18f); only the `clip`-level
homogeneity identity is proved here, not the `fderiv` corollary (see "Not
proved" below). -/
theorem capHomogeneity_clip (Mmax x c : ℝ) (hc : 0 < c) :
    clip 0 (c * Mmax) (c * x) = c * clip 0 Mmax x := by
  unfold clip
  have hmin : min (c * Mmax) (c * x) = c * min Mmax x :=
    (mul_min_of_nonneg Mmax x hc.le).symm
  have hmax : c * max 0 (min Mmax x) = max 0 (c * min Mmax x) := by
    rw [mul_max_of_nonneg 0 (min Mmax x) hc.le, mul_zero]
  rw [hmin, ← hmax]

end NoeticDiffusion
