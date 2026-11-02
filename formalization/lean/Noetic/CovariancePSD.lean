import Mathlib.Analysis.Matrix.Order

/-!
# L7d: positive-semidefinite matrix factorization

This module records the finite-dimensional algebraic factorization needed for
later covariance constructions.  A real positive-semidefinite square matrix
has a square factor whose product with its transpose is the original matrix.
The proof uses Mathlib's C*-algebra factorization theorem; it makes no claim
about covariance, reachability, numerical computation, or empirical data.
-/

namespace NoeticDiffusion

noncomputable section

open scoped Matrix
open scoped MatrixOrder

variable {n : Type*} [Fintype n]

/-- Every finite real positive-semidefinite matrix has a square factorization
`Q = B * Bᵀ`. -/
theorem posSemidef_exists_factor_mul_transpose
    (Q : Matrix n n ℝ) (hQ : Q.PosSemidef) :
    ∃ B : Matrix n n ℝ, Q = B * B.transpose := by
  classical
  have hQnonneg : (0 : Matrix n n ℝ) ≤ Q :=
    (Matrix.nonneg_iff_posSemidef (A := Q)).mpr hQ
  obtain ⟨B, hB⟩ :=
    CStarAlgebra.nonneg_iff_eq_mul_star_self.mp hQnonneg
  refine ⟨B, ?_⟩
  simpa only [Matrix.star_eq_conjTranspose,
    Matrix.conjTranspose_eq_transpose_of_trivial] using hB

end

end NoeticDiffusion
