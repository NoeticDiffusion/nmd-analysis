# TAC 6 / 8 / 10 — Σ dynamics and block-shear flux

- cohort: `281` subjects (`141` CPC1, `140` CPC5)
- sigma window: `40` MNPS points, step: `10`

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

- `tac10_9d_within_band_flux_median` [TAC 10]: CPC1 med `0.5255` vs CPC5 med `0.5978`, Cohen's `d = -0.657`, MW `p = 1.53e-05`, AUROC `0.316`, n = `95/91`
- `tac10_9d_cross_band_flux_median` [TAC 10]: CPC1 med `1.049` vs CPC5 med `1.191`, Cohen's `d = -0.642`, MW `p = 1.96e-05`, AUROC `0.319`, n = `95/91`
- `tac8_3d_cone_twist_median` [TAC 8]: CPC1 med `0.07442` vs CPC5 med `0.06532`, Cohen's `d = 0.289`, MW `p = 0.00374`, AUROC `0.600`, n = `141/140`
- `tac6_9d_sigma_velocity_median` [TAC 6]: CPC1 med `0.1281` vs CPC5 med `0.1315`, Cohen's `d = -0.163`, MW `p = 0.108`, AUROC `0.444`, n = `141/140`
- `tac6_3d_sigma_velocity_median` [TAC 6]: CPC1 med `0.04957` vs CPC5 med `0.04915`, Cohen's `d = 0.114`, MW `p = 0.353`, AUROC `0.532`, n = `141/140`
- `tac8_9d_cone_twist_median` [TAC 8]: CPC1 med `0.1493` vs CPC5 med `0.1519`, Cohen's `d = 0.060`, MW `p = 0.793`, AUROC `0.509`, n = `141/140`
- `tac10_9d_cross_band_ratio_median` [TAC 10]: CPC1 med `2.018` vs CPC5 med `2.023`, Cohen's `d = -0.047`, MW `p = 0.408`, AUROC `0.465`, n = `95/91`

## Notes

- TAC 6/8 use a sliding-window covariance over MNPS coordinate sequences. Each H5 row = one EEG time window. Results are sensitive to `--sigma-window`.
- TAC 10 requires `jacobian_9D/J_hat` (or `jacobian_9D_subject_anchored/J_hat`). Runs without 9D Jacobians contribute NaN for TAC 10 only.
- The 3×3 block decomposition assumes dims 0-2 = δ-band MNPS, 3-5 = θ-band, 6-8 = α-band. This is the standard NDT 9D layout.