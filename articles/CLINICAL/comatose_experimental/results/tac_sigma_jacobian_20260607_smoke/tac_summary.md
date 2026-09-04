# TAC 6 / 8 / 10 — Σ dynamics and block-shear flux

- cohort: `6` subjects (`0` CPC1, `6` CPC5)
- sigma window: `20` MNPS points, step: `5`

## TAC 6 — Σ log-Euclidean velocity

Measures how fast the local reachability covariance changes on the SPD manifold.
High velocity = rapidly evolving ellipsoid (burst-suppression transients expected to dominate).

## TAC 8 — Cone-field twist

Measures how much the orientation of Σ's eigenvectors rotates between consecutive
windows. Orthogonal to volume (velocity); captures directionality changes.

## TAC 10 — 9D block-shear flux

Decomposes the 9×9 Jacobian into 3×3 blocks (bands δ/θ/α). Cross-band flux
= how much the bands couple to each other. Within-band flux = intra-band norm.
High cross-band ratio = inter-band coupling dominates (potentially less structured).

## CPC1 vs CPC5 contrasts

No contrast rows available.

## Notes

- TAC 6/8 use a sliding-window covariance over MNPS coordinate sequences. Each H5 row = one EEG time window. Results are sensitive to `--sigma-window`.
- TAC 10 requires `jacobian_9D/J_hat` (or `jacobian_9D_subject_anchored/J_hat`). Runs without 9D Jacobians contribute NaN for TAC 10 only.
- The 3×3 block decomposition assumes dims 0-2 = δ-band MNPS, 3-5 = θ-band, 6-8 = α-band. This is the standard NDT 9D layout.