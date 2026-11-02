import Noetic.CovarianceKernelEquivalence

/-!
# L7c: block-operator form of the common factor kernel

For rectangular factors `B k : Matrix n m ℝ`, concatenate all factor
columns into one block matrix with column index `ι × m`:

`blockFactorMatrix B i (k,j) = B k i j`.

The transpose of this block operator annihilates a state vector exactly when
every individual transpose factor annihilates it.  Consequently, the common
transpose kernel is trivial exactly when the block operator detects every
nonzero state direction.  This is an exact block/kernel statement (with a
finite state index in the matrix products); rank and column-span
reformulations, which require the corresponding finite factor and channel
index assumptions, are left to a later gate.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix

variable {n : Type*} [Fintype n]
variable {m ι : Type*}

/-! ## Explicit block matrix -/

/-- The block matrix obtained by concatenating the columns of all factors. -/
def blockFactorMatrix (B : ι → Matrix n m ℝ) : Matrix n (ι × m) ℝ :=
  fun i p => B p.1 i p.2

/-- The block transpose annihilates `v` exactly when every factor transpose
annihilates `v`. -/
theorem blockFactorMatrix_transpose_mulVec_eq_zero_iff
    (B : ι → Matrix n m ℝ) (v : n → ℝ) :
    (blockFactorMatrix B).transpose *ᵥ v = 0 ↔
      ∀ k : ι, (B k).transpose *ᵥ v = 0 := by
  constructor
  · intro h k
    funext j
    have hj := congrFun h (k, j)
    simpa [blockFactorMatrix, Matrix.mulVec, dotProduct] using hj
  · intro h
    funext p
    rcases p with ⟨k, j⟩
    have hj := congrFun (h k) j
    simpa [blockFactorMatrix, Matrix.mulVec, dotProduct] using hj

/-! ## Kernel and detection restatements -/

/-- The block transpose has trivial kernel on state vectors. -/
def blockTransposeKernelTrivial (B : ι → Matrix n m ℝ) : Prop :=
  ∀ v : n → ℝ, (blockFactorMatrix B).transpose *ᵥ v = 0 → v = 0

/-- The block transpose detects every nonzero state direction. -/
def blockTransposeDetectsAllDirections (B : ι → Matrix n m ℝ) : Prop :=
  ∀ v : n → ℝ, v ≠ 0 → (blockFactorMatrix B).transpose *ᵥ v ≠ 0

/-- The individual-factor common kernel is equivalent to the block transpose
kernel being trivial. -/
theorem commonTransposeKernelTrivial_iff_blockTransposeKernelTrivial
    (B : ι → Matrix n m ℝ) :
    commonTransposeKernelTrivial B ↔ blockTransposeKernelTrivial B := by
  constructor
  · intro h v hv
    apply h v
    intro k
    exact (blockFactorMatrix_transpose_mulVec_eq_zero_iff B v).1 hv k
  · intro h v hv
    apply h v
    exact (blockFactorMatrix_transpose_mulVec_eq_zero_iff B v).2 hv

/-- The individual-factor detection condition is equivalent to block
operator detection of every nonzero state direction. -/
theorem factorDetectsAllDirections_iff_blockTransposeDetectsAllDirections
    (B : ι → Matrix n m ℝ) :
    factorDetectsAllDirections B ↔ blockTransposeDetectsAllDirections B := by
  constructor
  · intro h v hv hblock
    obtain ⟨k, hk⟩ := h v hv
    exact hk ((blockFactorMatrix_transpose_mulVec_eq_zero_iff B v).1
      hblock k)
  · intro h v hv
    by_contra hnone
    push_neg at hnone
    exact (h v hv) ((blockFactorMatrix_transpose_mulVec_eq_zero_iff B v).2
      hnone)

end

end NoeticDiffusion
