/-
  A finite C1 countermodel for Noetic Diffusion Theory (NDT) v2.

  This file formalizes the narrow mathematical claim that a reduced observed
  chart need not determine the next transition law. It uses an exact
  deterministic successor; the corresponding Dirac law is represented by its
  successor point, without probability-measure infrastructure.

  Source article:
    J:\repos\nmd-analysis\articles\NoeticDiffusionTheory_v2\Noetic Diffusion Theory - Neural State, Dynamical Accessibility, and the Geometry of Possible Futures.typ
    - latent process, observation, and chart: lines 210--228
    - transition laws and latent/chart distinction: lines 301--348
    - NDT-C1: lines 365--380

  Claim boundary: this is an existential finite countermodel. It does not
  assert that an empirical MNPS chart is insufficient, prove generic
  non-Markovianity, or address C2, C3, or biological interpretation.
-/

namespace NoeticDiffusion

/- The latent state has one observed bit and one hidden bit. -/
abbrev State := Bool × Bool

/- The reduced chart forgets the second (hidden) coordinate. -/
def chart : State → Bool := Prod.fst

/- The next latent state copies the hidden bit into both coordinates. -/
def transition : State → State
  | (_, hidden) => (hidden, hidden)

/- Exact one-step observed future induced by the deterministic transition. -/
def nextChart (s : State) : Bool := chart (transition s)

/- Two latent states that agree in the reduced chart. -/
def stateA : State := (false, false)
def stateB : State := (false, true)

@[simp] theorem chart_stateA : chart stateA = false := by
  rfl

@[simp] theorem chart_stateB : chart stateB = false := by
  rfl

/- These compute the exact successor points of this deterministic model. -/
@[simp] theorem transition_stateA : transition stateA = (false, false) := by
  rfl

@[simp] theorem transition_stateB : transition stateB = (true, true) := by
  rfl

@[simp] theorem nextChart_stateA : nextChart stateA = false := by
  rfl

@[simp] theorem nextChart_stateB : nextChart stateB = true := by
  rfl

/- Same present observation, different observed one-step future. -/
theorem same_present_different_observed_future :
    chart stateA = chart stateB ∧ nextChart stateA ≠ nextChart stateB := by
  constructor
  · rfl
  · decide

/-
  No deterministic function of the reduced chart can reproduce the next
  observed future for every latent state. The two states above have the same
  chart input but force different output bits.
-/
theorem no_deterministic_chart_factorization :
    ¬ ∃ g : Bool → Bool, ∀ s : State, nextChart s = g (chart s) := by
  rintro ⟨g, hg⟩
  have hA : nextChart stateA = g false := by
    simpa [stateA, chart] using hg stateA
  have hB : nextChart stateB = g false := by
    simpa [stateB, chart] using hg stateB
  have hEq : nextChart stateA = nextChart stateB := hA.trans hB.symm
  exact (by decide : nextChart stateA ≠ nextChart stateB) hEq

end NoeticDiffusion
