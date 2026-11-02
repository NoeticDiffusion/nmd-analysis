/-
  Deterministic chart-fibre factorization for Noetic Diffusion Theory.

  This file formalizes the finite, deterministic sufficiency criterion suggested
  by NDT's distinction between a latent state and a reduced observation chart:
  a future-valued map factors through a chart exactly when it is constant on
  the chart's fibres.  Surjectivity is included so that the factor map is
  defined on every chart value.

  Source article:
    J:\repos\nmd-analysis\articles\NoeticDiffusionTheory_v2\Noetic Diffusion Theory - Neural State, Dynamical Accessibility, and the Geometry of Possible Futures.typ
    - latent process, observation, and chart: lines 210--228
    - transition laws and latent/chart distinction: lines 301--348
    - NDT-C1: lines 365--380

  Claim boundary: this is a deterministic set-theoretic factorization theorem
  and its finite Bool counterexample corollary.  It does not assert that an
  empirical MNPS chart is insufficient, establish a stochastic-kernel or
  conditional-probability factorization, prove generic non-Markovianity, or
  address C2, C3, or biological interpretation.
-/

import Noetic.ReducedState

namespace NoeticDiffusion

universe u v w

/- A map is constant on the fibres of a chart when equal chart values imply
   equal map values. -/
theorem exists_factorization_iff_of_surjective
    {X : Type u} {Z : Type v} {Y : Type w} (π : X → Z) (K : X → Y)
    (hπ : Function.Surjective π) :
    (∃ Kbar : Z → Y, ∀ x : X, K x = Kbar (π x)) ↔
      ∀ ⦃x₁ x₂ : X⦄, π x₁ = π x₂ → K x₁ = K x₂ := by
  constructor
  · rintro ⟨Kbar, hKbar⟩ x₁ x₂ hπ12
    rw [hKbar x₁, hKbar x₂, hπ12]
  · intro hconstant
    let Kbar : Z → Y := fun z => K (Classical.choose (hπ z))
    refine ⟨Kbar, ?_⟩
    intro x
    exact hconstant (Classical.choose_spec (hπ (π x))) |>.symm

/- The existing finite countermodel can be read through the general criterion:
   its next observed future is not constant on chart fibres. -/
theorem no_deterministic_chart_factorization_via_fiber_criterion :
    ¬ ∃ g : Bool → Bool, ∀ s : State, nextChart s = g (chart s) := by
  intro hfactor
  have hchart : Function.Surjective chart := by
    intro b
    exact ⟨(b, false), rfl⟩
  have hconstant :=
    (exists_factorization_iff_of_surjective chart nextChart hchart).mp
      hfactor
  have hfuture : nextChart stateA = nextChart stateB := by
    apply hconstant
    rfl
  exact (by decide : nextChart stateA ≠ nextChart stateB) hfuture

end NoeticDiffusion
