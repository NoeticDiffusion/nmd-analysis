/-
  L13: kernel-valued fibre sufficiency, protocol-augmented states, and a
  finite history-augmentation model for Noetic Diffusion Theory (NDT).

  This file extends the deterministic chart-fibre factorization criterion of
  `Noetic/ReducedSufficiency.lean` to stochastic kernels (`PMF`-valued and
  `Measure`-valued future laws), and gives two finite toy models built on the
  `State`/`chart` witnesses of `Noetic/ReducedState.lean`:

  * a genuinely stochastic countermodel (two hidden states with the same
    chart but different `PMF Bool` next-observation laws), upgrading the
    existing deterministic Dirac countermodel;
  * a protocol-augmented model instantiating NDT-C3 ("matched chart,
    different future law under different control protocols"): the plain
    chart is not sufficient when the protocol varies, but the pair
    (chart, protocol) is;
  * an optional one-step history-augmentation model of the same shape, with
    the "previous observed bit" playing the role of the protocol label.

  Source article:
    J:\repos\nmd-analysis\articles\NoeticDiffusionTheory_v2\Noetic Diffusion Theory - Neural State, Dynamical Accessibility, and the Geometry of Possible Futures.typ
    - transition laws, protocol γ, augmented state Z_t = (X_t, C_t, H_t, ...): lines 301--353, 370--400
    - NDT-C1--C3, "C3 is a statement about γ": lines 365--400
    - P6 (history-dependence table): lines 1226--1227
  Compact summary: §1 "TRANSITION-LAW / KERNEL FAMILY" and "THREE CORE
  COMMITMENTS".
  S7 §7 item 1 (extend the fibre criterion toward transition kernels and
  history-augmented states).

  Claim boundary: all models here are finite toy models. "Sufficient" means
  the future *law at horizon 1* factors through the (augmented) chart; no
  Markov property, filtration, or path-space statement is made. The kernel
  criterion is pointwise equality of laws (one `PMF`/`Measure` value per
  state), not a path-space measure statement, and no measurability of the
  factor map in the quotient variable is claimed (a
  `ProbabilityTheory.Kernel` version would need that and is not attempted
  here). Nothing here asserts that an empirical MNPS chart is insufficient,
  that a physiological variable is a protocol, or that C2 (non-redundant
  out-of-sample information, an empirical claim) holds. The protocol and
  history augmentations use deterministic `Bool → Bool` future maps rather
  than `PMF`-valued ones (see DEVIATIONS in the implementation report); this
  is the fallback the source idea file explicitly allows, and it does not
  weaken the "chart alone is insufficient / augmented chart is sufficient"
  conclusions, which are exact for the maps actually defined.
-/

import Mathlib.Probability.ProbabilityMassFunction.Constructions
import Mathlib.MeasureTheory.Measure.MeasureSpaceDef
import Noetic.ReducedState
import Noetic.ReducedSufficiency

namespace NoeticDiffusion

open scoped NNReal ENNReal

universe u v w

/-! ## L13a: kernel-valued fibre sufficiency -/

/-- Stochastic (`PMF`-valued) reading of the chart-fibre factorization
criterion: for a surjective chart `π` and a finite-support stochastic future
law `κ : X → PMF W`, `κ` factors through the chart (there is a chart-only law
`κbar` with `κ x = κbar (π x)` for every `x`) exactly when `κ` is constant on
every chart fibre. This is the case `Y := PMF W` of
`exists_factorization_iff_of_surjective`, stated explicitly so the stochastic
reading is a named theorem in its own right. -/
theorem kernel_exists_factorization_iff_of_surjective
    {X : Type u} {Z : Type v} {W : Type w} (π : X → Z) (κ : X → PMF W)
    (hπ : Function.Surjective π) :
    (∃ κbar : Z → PMF W, ∀ x : X, κ x = κbar (π x)) ↔
      ∀ ⦃x₁ x₂ : X⦄, π x₁ = π x₂ → κ x₁ = κ x₂ :=
  exists_factorization_iff_of_surjective π κ hπ

/-- Deterministic special case: a deterministic future map `K` factors
through the chart exactly when its Dirac (`PMF.pure`) lift does. This
connects the deterministic criterion of `ReducedSufficiency.lean` to the
stochastic one above: reading `K` as the degenerate kernel `x ↦ pure (K x)`
changes nothing about factorization. -/
theorem kernel_deterministic_pure_factorization_iff
    {X : Type u} {Z : Type v} {Y : Type w} (π : X → Z) (K : X → Y)
    (hπ : Function.Surjective π) :
    (∃ Kbar : Z → Y, ∀ x : X, K x = Kbar (π x)) ↔
      (∃ κbar : Z → PMF Y, ∀ x : X, PMF.pure (K x) = κbar (π x)) := by
  rw [exists_factorization_iff_of_surjective π K hπ,
    kernel_exists_factorization_iff_of_surjective π (fun x => PMF.pure (K x)) hπ]
  constructor
  · intro h x₁ x₂ hp
    rw [h hp]
  · intro h x₁ x₂ hp
    have heq := h hp
    have h1 : PMF.pure (K x₁) (K x₁) = PMF.pure (K x₂) (K x₁) := by rw [heq]
    by_contra hne
    rw [PMF.pure_apply_self, PMF.pure_apply_of_ne (K x₂) (K x₁) hne] at h1
    exact absurd h1 (by norm_num)

/-- `Measure`-valued reading of the same criterion: for a surjective chart
`π` and a (not necessarily normalized or measurable-in-the-chart) family of
measures `κ : X → MeasureTheory.Measure W`, `κ` factors through the chart
exactly when it is constant on chart fibres. No measurability of the factor
map `κbar` in `Z` is claimed; that would require a genuine
`ProbabilityTheory.Kernel Z W` and is out of scope here. -/
theorem kernel_measure_exists_factorization_iff_of_surjective
    {X : Type u} {Z : Type v} {W : Type w} [MeasurableSpace W]
    (π : X → Z) (κ : X → MeasureTheory.Measure W)
    (hπ : Function.Surjective π) :
    (∃ κbar : Z → MeasureTheory.Measure W, ∀ x : X, κ x = κbar (π x)) ↔
      ∀ ⦃x₁ x₂ : X⦄, π x₁ = π x₂ → κ x₁ = κ x₂ :=
  exists_factorization_iff_of_surjective π κ hπ

/-! ## L13b: a genuinely stochastic finite countermodel -/

/-- A stochastic upgrade of `ReducedState.State`'s deterministic transition:
the hidden bit sets the *probability* that the next observed bit is `true`
(`3/4` if hidden, `1/4` otherwise), instead of determining it outright. Any
two distinct values in `(0,1)` would serve the same purpose. -/
noncomputable def stochasticNextObsLaw (s : State) : PMF Bool :=
  PMF.bernoulli (cond s.2 (3 / 4 : ℝ≥0) (1 / 4 : ℝ≥0))
    (by cases s.2 <;> simp only [cond_true, cond_false] <;>
      rw [div_le_one₀ (by norm_num)] <;> norm_num)

/-- The two chart-matched hidden states of `ReducedState.lean` have distinct
next-observation *laws*, not just distinct next-observation values: their
`PMF Bool` laws disagree at the point `true`. -/
theorem stochastic_nextObsLaw_stateA_ne_stateB :
    stochasticNextObsLaw stateA ≠ stochasticNextObsLaw stateB := by
  intro h
  have h1 : stochasticNextObsLaw stateA true = stochasticNextObsLaw stateB true := by rw [h]
  simp only [stochasticNextObsLaw, stateA, stateB, PMF.bernoulli_apply, cond_true,
    cond_false] at h1
  have h2 : ((1 / 4 : ℝ≥0) : ℝ) = ((3 / 4 : ℝ≥0) : ℝ) := by exact_mod_cast h1
  norm_num at h2

/-- No chart-only stochastic kernel reproduces `stochasticNextObsLaw` for
every latent state: the chart is `Function.Surjective`, and by
`kernel_exists_factorization_iff_of_surjective` a chart-only factorization
would force the same law on every chart fibre, contradicting
`stochastic_nextObsLaw_stateA_ne_stateB`. This upgrades
`ReducedSufficiency.no_deterministic_chart_factorization_via_fiber_criterion`
from a deterministic (Dirac) countermodel to a genuinely stochastic one. -/
theorem stochastic_no_kernel_chart_factorization :
    ¬ ∃ κbar : Bool → PMF Bool, ∀ s : State, stochasticNextObsLaw s = κbar (chart s) := by
  intro hfactor
  have hchart : Function.Surjective chart := by
    intro b
    exact ⟨(b, false), rfl⟩
  have hconstant :=
    (kernel_exists_factorization_iff_of_surjective chart stochasticNextObsLaw hchart).mp
      hfactor
  have hlaw : stochasticNextObsLaw stateA = stochasticNextObsLaw stateB := by
    apply hconstant
    rfl
  exact stochastic_nextObsLaw_stateA_ne_stateB hlaw

/-! ## L13c: protocol augmentation (NDT-C3) -/

/-- Two control protocols, standing in for the manuscript's `γ` (an
instantaneous `c_t` or a longer protocol label). -/
inductive L13_Protocol
  | gamma1
  | gamma2
  deriving DecidableEq

/-- The chart-conditional future law under a protocol. Deterministic
`Bool → Bool` rather than `PMF`-valued (see the module docstring's claim
boundary): `gamma1` reproduces the chart value, `gamma2` flips it, so the two
protocols disagree at every chart value. -/
def protocolLaw : L13_Protocol → Bool → Bool
  | .gamma1, x => x
  | .gamma2, x => !x

/-- NDT-C3's premise in this finite model: the two protocols give different
future laws at a matched chart value. -/
theorem protocol_matched_chart_different_law :
    ∃ x : Bool, protocolLaw .gamma1 x ≠ protocolLaw .gamma2 x :=
  ⟨true, by decide⟩

/-- The future law of a full latent state `x : State` under protocol `γ`
depends only on `chart x` and `γ`, not on the hidden bit `x.2`. -/
def protocolLawOf (x : State) (γ : L13_Protocol) : Bool := protocolLaw γ (chart x)

/-- The protocol-augmented chart `x ↦ (chart x, γ)` is sufficient for
`protocolLawOf`: taking `Kbar (c, γ) := protocolLaw γ c` reproduces
`protocolLawOf x γ` exactly, by construction. This is the finite,
kernel-checked instance of "augmenting the state with the protocol restores
factorization". -/
theorem augmented_chart_sufficient :
    ∃ Kbar : Bool × L13_Protocol → Bool,
      ∀ (x : State) (γ : L13_Protocol), protocolLawOf x γ = Kbar (chart x, γ) := by
  refine ⟨fun p => protocolLaw p.2 p.1, ?_⟩
  intro x γ
  rfl

/-- The plain chart alone is not sufficient for `protocolLawOf`: fixing a
latent state with the witness chart value from
`protocol_matched_chart_different_law` and varying only the protocol changes
the law while the chart stays fixed, so no `Kbar : Bool → Bool` can
reproduce `protocolLawOf` for every `(x, γ)`. This is the finite,
kernel-checked instance of NDT-C3 ("matched chart, different future law under
different protocols") and certifies that C3 is a statement about `γ`, not a
violation of the canonical equation. -/
theorem unaugmented_chart_insufficient :
    ¬ ∃ Kbar : Bool → Bool,
      ∀ (x : State) (γ : L13_Protocol), protocolLawOf x γ = Kbar (chart x) := by
  rintro ⟨Kbar, hKbar⟩
  obtain ⟨x, hx⟩ := protocol_matched_chart_different_law
  have h1 : protocolLawOf (x, false) .gamma1 = Kbar (chart (x, false)) := hKbar (x, false) .gamma1
  have h2 : protocolLawOf (x, false) .gamma2 = Kbar (chart (x, false)) := hKbar (x, false) .gamma2
  have heq : protocolLawOf (x, false) .gamma1 = protocolLawOf (x, false) .gamma2 :=
    h1.trans h2.symm
  exact hx heq

/-! ## L13d: one-step history augmentation (P6) -/

/-- The chart-conditional future law under a one-step history label
(the previous observed bit, standing in for `H_t` in the manuscript's
augmented state `Z_t = (X_t, C_t, H_t, ...)`). Same shape as `protocolLaw`:
deterministic `Bool → Bool`, with the two history values disagreeing at
every chart value. -/
def historyLaw : Bool → Bool → Bool
  | hprev, c => if hprev then c else !c

/-- The history-augmentation premise: the two history labels give different
future laws at a matched chart value. -/
theorem history_matched_chart_different_law :
    ∃ c : Bool, historyLaw true c ≠ historyLaw false c :=
  ⟨true, by decide⟩

/-- The future law of a full latent state under a history label depends
only on `chart x` and the history label, not on the hidden bit. -/
def historyLawOf (x : State) (hprev : Bool) : Bool := historyLaw hprev (chart x)

/-- The history-augmented chart `x ↦ (chart x, hprev)` is sufficient for
`historyLawOf`, by the same direct construction as
`augmented_chart_sufficient`. -/
theorem history_augmented_chart_sufficient :
    ∃ Kbar : Bool × Bool → Bool,
      ∀ (x : State) (hprev : Bool), historyLawOf x hprev = Kbar (chart x, hprev) := by
  refine ⟨fun p => historyLaw p.2 p.1, ?_⟩
  intro x hprev
  rfl

/-- The plain chart alone is not sufficient for `historyLawOf`: fixing a
latent state with the witness chart value and varying only the history label
changes the law while the chart stays fixed. This is the finite face of P6:
one-step history restores sufficiency in a case where the plain chart does
not suffice. -/
theorem history_unaugmented_chart_insufficient :
    ¬ ∃ Kbar : Bool → Bool,
      ∀ (x : State) (hprev : Bool), historyLawOf x hprev = Kbar (chart x) := by
  rintro ⟨Kbar, hKbar⟩
  obtain ⟨c, hc⟩ := history_matched_chart_different_law
  have h1 : historyLawOf (c, false) true = Kbar (chart (c, false)) := hKbar (c, false) true
  have h2 : historyLawOf (c, false) false = Kbar (chart (c, false)) := hKbar (c, false) false
  have heq : historyLawOf (c, false) true = historyLawOf (c, false) false := h1.trans h2.symm
  exact hc heq

end NoeticDiffusion
