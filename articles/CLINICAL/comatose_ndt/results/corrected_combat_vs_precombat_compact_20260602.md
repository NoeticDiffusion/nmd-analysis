# Corrected ComBat vs pre_combat compact comparison

## Coverage and provenance

- Corrected-ComBat pooled bundle: `298` analyzable subjects (`140 CPC 1`, `10 CPC 2`, `7 CPC 3`, `3 CPC 4`, `138 CPC 5`) across `4667` H5 runs, with `0` subject overlap and `0` run overlap between `part1` and `part2`.
- Frozen `pre_combat` pooled bundle: `301` analyzable subjects (`141 CPC 1`, `10 CPC 2`, `7 CPC 3`, `3 CPC 4`, `140 CPC 5`) across `5316` H5 runs.
- The corrected-ComBat refresh therefore changes both the effect sizes and the article-facing cohort itself; it is not just a same-cohort numeric repair.

## Direct pooled anchors preserved in `pre_combat`

### Reachability

- `tube_d_eff_median`: old `d = 0.513`, `p = 1.85e-05`, `q = 1.39e-04`; new `d = 0.638`, `p = 1.02e-06`, `q = 1.23e-05`.
- `persistence_log_eig_var_median`: old `d = 0.123`, `p = 3.46e-05`, `q = 1.60e-04`; new `d = 0.122`, `p = 2.39e-05`, `q = 5.30e-05`.
- `persistence_kappa_median`: old `d = 0.119`, `p = 0.0196`, `q = 0.0512`; new `d = 0.127`, `p = 0.0145`, `q = 0.0249`.
- `tube_capture_gate_median`: old `d = -0.142`, `p = 0.0862`, `q = 0.133`; new `d = -0.348`, `p = 0.0183`, `q = 0.0305`.
- `tube_a_operator_norm_median`: old `d = -0.064`, `p = 0.0838`, `q = 0.132`; new `d = -0.129`, `p = 0.413`, `q = 0.486`.

### Incremental validity

- Restricted `clinical + qEEG` comparator `AUROC`: old `0.583`; new `0.595`.
- `clinical + qEEG + geometry` `AUROC`: old `0.672`; new `0.687`.
- Geometry delta `AUROC` versus `clinical + qEEG`: old `+0.088`; new `+0.092`.
- Geometry delta `AUPRC` versus `clinical + qEEG`: old `+0.081`; new `+0.086`.
- Geometry delta Brier versus `clinical + qEEG`: old `-0.0226`; new `-0.0226`.

## New corrected-ComBat anchors without exact pooled `pre_combat` analogues

The frozen `pre_combat` folder does not preserve exact pooled outcome-contrast tables for the classical `MNPS` / `MNJ` families. The old comparator note explicitly marks those pooled fields as unavailable, so the rows below should be treated as new corrected-ComBat anchors rather than as direct old-vs-new replacements.

- `MNPS 3D` / `m_std`: `d = -0.409`, `p = 0.00553`, medians `0.844` vs `0.936`.
- `MNPS 9D` / `m_e_std`: `d = -0.436`, `p = 9.05e-05`, medians `1.104` vs `1.273`.
- `MNJ 3D` / `spectral_radius_median`: `d = -0.536`, `p = 1.70e-08`, medians `0.0715` vs `0.0775`.
- `MNJ 9D` / `spectral_radius_median`: `d = -0.138`, `p = 2.75e-09`, medians `0.0982` vs `0.1090`.
- `MNJ 9D` / `frobenius_norm_median`: `d = -0.126`, `p = 5.23e-05`, medians `0.555` vs `0.624`.

## Interpretation

- The corrected-ComBat pooled reachability story is more capacity-led than the frozen `pre_combat` draft: `tube_d_eff_median` strengthens materially and remains the clearest article-facing lead.
- The persistence pair stays small but reproducible, with `persistence_kappa_median` now crossing the pooled BH-FDR threshold that it narrowly missed in `pre_combat`.
- The capture layer is redistributed rather than uniformly lost: `tube_capture_gate_median` strengthens and becomes BH-FDR-positive, while `tube_a_operator_norm_median` remains directionally negative but loses statistical support.
- The pooled predictive comparison is at least as favorable to the geometry layer as in `pre_combat`, despite the corrected-ComBat bundle being smaller (`298` vs `301` subjects).
- The pooled corrected-ComBat rerun also restores classical anchors that `pre_combat` did not preserve as exact pooled tables, especially `MNJ 3D` spectral radius and a more modest but still highly significant `MNJ 9D` Jacobian layer.
