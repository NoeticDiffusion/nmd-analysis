import Mathlib.Data.Real.Basic
import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.Data.Matrix.Mul

/-!
# TRANS P0 kernels: one functional does not identify the kernel

This module is T6 of the NDT-TRANS Lean P0 set in
`formalization/science_lead/sl_lean_001.md`.

If two Markov rows are equal as functions, every set-mass functional agrees.
The converse fails: two explicit three-state rows can put the same mass on a
nominated target `B` and different mass on another set `C`, so they are
distinct kernels. Equality of a single reachability scalar is therefore not
kernel equality.

Computational background (not a hypothesis of any theorem here): Astra
TRANS-PRED evaluates one declared finite-grid event and explicitly does not
recover the transition kernel, continuous first-hit field, or eventual
committor. The theorems below are the exact finite-row form of that
inference rule.

## Claim boundary

Finite real matrices, used as one-step rows. No `ProbabilityTheory.Kernel`
measurability, no path-space measure, and no claim that an empirical Brier
score identifies `K_h`. The sufficiency direction is function extensionality;
it is recorded as a named theorem because that is the TRANS inference
discipline, not because the algebra is deep.
-/

namespace NoeticDiffusion

open scoped BigOperators Matrix

variable {n : Type*}

/-- Endpoint mass of a one-step kernel row on a nominated set. -/
def Trans_kernelMass (K : Matrix n n ℝ) (x : n) (S : Finset n) : ℝ :=
  ∑ j ∈ S, K x j

/-- **T6a.** Kernel equality implies equality of every set-mass functional,
and of every function of the kernel. -/
theorem TransT6_kernel_eq_mass_eq {K1 K2 : Matrix n n ℝ}
    (h : K1 = K2) (x : n) (S : Finset n) :
    Trans_kernelMass K1 x S = Trans_kernelMass K2 x S := by
  rw [h]

theorem TransT6_kernel_eq_functional_eq {α : Type*} (F : Matrix n n ℝ → α)
    {K1 K2 : Matrix n n ℝ} (h : K1 = K2) : F K1 = F K2 :=
  congrArg F h

/-- First one-step kernel on `Fin 3`: from state `0` the mass is
`(1/2, 1/2, 0)`. -/
noncomputable def Trans_K1 : Matrix (Fin 3) (Fin 3) ℝ :=
  Matrix.of ![![1 / 2, 1 / 2, 0], ![0, 1, 0], ![0, 0, 1]]

/-- Second one-step kernel on `Fin 3`: from state `0` the mass is
`(1/2, 1/4, 1/4)`. Same mass on `{0}`, different mass on `{1}`. -/
noncomputable def Trans_K2 : Matrix (Fin 3) (Fin 3) ℝ :=
  Matrix.of ![![1 / 2, 1 / 4, 1 / 4], ![0, 1, 0], ![0, 0, 1]]

def Trans_T6_B : Finset (Fin 3) := {0}
def Trans_T6_C : Finset (Fin 3) := {1}

theorem TransT6_same_mass_on_B :
    Trans_kernelMass Trans_K1 0 Trans_T6_B =
      Trans_kernelMass Trans_K2 0 Trans_T6_B := by
  simp [Trans_kernelMass, Trans_T6_B, Trans_K1, Trans_K2, Matrix.of_apply]

theorem TransT6_diff_mass_on_C :
    Trans_kernelMass Trans_K1 0 Trans_T6_C ≠
      Trans_kernelMass Trans_K2 0 Trans_T6_C := by
  simp [Trans_kernelMass, Trans_T6_C, Trans_K1, Trans_K2, Matrix.of_apply]

theorem TransT6_K1_ne_K2 : Trans_K1 ≠ Trans_K2 := by
  intro h
  have hc : Trans_K1 0 1 = Trans_K2 0 1 := congrArg (fun M => M 0 1) h
  simp [Trans_K1, Trans_K2, Matrix.of_apply] at hc

/-- **T6b.** Equality of one nominated set-mass does not identify the
one-step kernel: the two rows agree on `B = {0}` and disagree on `C = {1}`. -/
theorem TransT6_one_mass_not_kernel_eq :
    Trans_kernelMass Trans_K1 0 Trans_T6_B =
      Trans_kernelMass Trans_K2 0 Trans_T6_B ∧
    Trans_kernelMass Trans_K1 0 Trans_T6_C ≠
      Trans_kernelMass Trans_K2 0 Trans_T6_C ∧
    Trans_K1 ≠ Trans_K2 :=
  ⟨TransT6_same_mass_on_B, TransT6_diff_mass_on_C, TransT6_K1_ne_K2⟩

end NoeticDiffusion
