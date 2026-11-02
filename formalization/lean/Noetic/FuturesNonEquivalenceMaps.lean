import Mathlib.Analysis.Calculus.Deriv.Pow
import Mathlib.Analysis.Calculus.Deriv.Add
import Mathlib.Analysis.Calculus.Deriv.Mul

/-! # L14: Non-equivalences in the futures layer (finite witnesses, part 2)

This file continues `Noetic.FuturesNonEquivalence` with the local-Jacobian
row of the manuscript's "Non-equivalent questions in NDT" table: an identical
linearization at a fixed point does not fix finite-amplitude behaviour.

Source article:
  `J:\repos\nmd-analysis\articles\NoeticDiffusionTheory_v2\Noetic Diffusion Theory - Neural State, Dynamical Accessibility, and the Geometry of Possible Futures.typ`
  - attractors and finite-amplitude resilience (FAR): lines 642--651
  - the "Non-equivalent questions in NDT" table: lines 653--677
Idea file: `J:\repos\nmd-analysis\project\lean\fable_ideas\03_futures_layer_nonequivalences.md`
(witnesses W5, W5').

## Claim boundary

- `L14_f1` and `L14_f2` are one-dimensional deterministic maps sharing the
  same derivative at the fixed point `0`. `L14_f1_contraction` and
  `L14_f2_escape` are exact algebraic facts about these two named maps; they
  do not define finite-amplitude resilience (FAR) in general, which the
  source article ties to an explicit perturbation protocol, not to a
  Jacobian or finite-time tangent gain.
- `L14_agree_nhds_deriv_eq` (W5') is a direct restatement of Mathlib's
  `Filter.EventuallyEq.deriv_eq`: any two functions that agree on a
  neighbourhood of a point have the same derivative there. It is the exact
  counterpart of the simulator's "local match" half of the double-well
  scouting dissociation (compactly-supported-bump pairs agreeing near a
  reference point but diverging in Monte-Carlo committor and escape
  amplitude); the "global divergence" half is covered here only by the
  fully checked `L14_f1`/`L14_f2` polynomial pair, not by the simulator
  numbers themselves.
-/

namespace NoeticDiffusion

/-! ## W5 — same local Jacobian, different basin structure

`L14_f1` and `L14_f2` agree to first order at `0` (`deriv f 0 = 1/2` for
both) but diverge globally: `L14_f1` is a global contraction toward `0`,
while `L14_f2` can send a point of norm at most `1` outside the unit ball. -/

/-- A globally contracting linear map. -/
noncomputable def L14_f1 (x : ℝ) : ℝ := x / 2

/-- A cubic perturbation of `L14_f1`, agreeing with it to first order at `0`
but able to escape the unit ball. -/
noncomputable def L14_f2 (x : ℝ) : ℝ := x / 2 + x ^ 3

private lemma L14_f1_hasDerivAt : HasDerivAt L14_f1 (1 / 2) 0 := by
  simpa [L14_f1] using (hasDerivAt_id (0 : ℝ)).div_const 2

private lemma L14_f2_hasDerivAt : HasDerivAt L14_f2 (1 / 2) 0 := by
  have hpow : HasDerivAt (fun x : ℝ => x ^ 3) (3 * (0 : ℝ) ^ 2) 0 := hasDerivAt_pow 3 0
  have hsum : HasDerivAt (fun x => L14_f1 x + x ^ 3) (1 / 2 + 3 * (0 : ℝ) ^ 2) 0 :=
    L14_f1_hasDerivAt.add hpow
  have heq : (1 / 2 + 3 * (0 : ℝ) ^ 2 : ℝ) = 1 / 2 := by norm_num
  rw [heq] at hsum
  simpa [L14_f1, L14_f2] using hsum

/-- W5 (derivative part): `L14_f1` and `L14_f2` share the same derivative,
`1/2`, at `0`. -/
theorem L14_deriv_eq_at_zero : deriv L14_f1 0 = deriv L14_f2 0 := by
  rw [L14_f1_hasDerivAt.deriv, L14_f2_hasDerivAt.deriv]

/-- W5 (contraction part): `L14_f1` is a global contraction toward `0`. -/
theorem L14_f1_contraction : ∀ x : ℝ, |L14_f1 x| ≤ |x| / 2 := by
  intro x
  rw [L14_f1, abs_div]
  norm_num

/-- W5 (escape part): `L14_f2` can send a point of norm at most `1` outside
the (open) unit ball, unlike `L14_f1`. -/
theorem L14_f2_escape : ∃ x : ℝ, |x| ≤ 1 ∧ 1 < |L14_f2 x| := by
  refine ⟨1, by norm_num, ?_⟩
  norm_num [L14_f2]

/-! ## W5′ — local agreement forces equal derivatives

The exact, general counterpart of "the same local Jacobian" used above: any
two functions that agree on a neighbourhood of a point already have the same
derivative there, regardless of what they do further away. This is the
checked half of the simulator's double-well "local match, global
divergence" scouting result (`results/orthogonal_dynamics_axis_b_scouting`,
`…axis_c_scouting`); the numerical committor/escape divergence there remains
a numerical, not machine-checked, observation. -/

/-- W5′: functions agreeing on a neighbourhood of `x` have the same
derivative at `x` (`Filter.EventuallyEq.deriv_eq`). -/
theorem L14_agree_nhds_deriv_eq {f g : ℝ → ℝ} {x : ℝ} (h : f =ᶠ[nhds x] g) :
    deriv f x = deriv g x := h.deriv_eq

end NoeticDiffusion
