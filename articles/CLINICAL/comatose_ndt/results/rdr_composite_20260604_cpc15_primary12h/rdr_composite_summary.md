# Recovery Dynamical Reserve Composite

- primary time bin: `0_12h`
- joined subjects: `277`
- path regularization lambda: `0.25`
- score orientation: all score rows are oriented so higher values point toward CPC1.
- train/test discipline: CV and LOSO recompute RDR robust z-scaling from the training fold only; part2-test rows use part1-fitted scaling.

## Cohort Join

| source_cohort | CPC1 | CPC5 |
|---|---:|---:|
| part1 | 70 | 69 |
| part2 | 70 | 68 |

## Metric Formulae

```text
RDR_core = z(tube_d_eff_median) - z(tube_capture_gate_median)
           - z(MNJ3D_spectral_radius_median) - z(MNJ3D_frobenius_norm_median)
RDR_3    = z(tube_d_eff_median) - z(tube_capture_gate_median)
           - mean(z(MNJ3D_spectral_radius_median), z(MNJ3D_frobenius_norm_median))
RDR_path = RDR_core - 0.25 * z(trajectory_3D_noetic_action)
NRCA     = projection_to_recovery_ray / sqrt(1 + off_axis_distance^2)
```

`NRCA` uses the oriented four-vector `[z(d_eff), -z(capture), -z(spectral_radius), -z(frobenius)]`. The ideal recovery ray is `[1, 1, 1, 1] / 2`; off-axis distance penalizes subjects whose apparent advantage is carried by only one axis rather than by coherent reachability-with-low-deformation geometry.

## Pooled Oriented Contrasts

| Metric | n CPC1 | n CPC5 | CPC1 median | CPC5 median | d | Cliff delta | AUROC | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `nrca_cosine_part1fit` | 140 | 137 | 0.6725 | -0.1713 | +0.882 | +0.454 | 0.727 | 6.47e-11 |
| `nrca_part1fit` | 140 | 137 | 0.6019 | -0.146 | +0.821 | +0.428 | 0.714 | 7.46e-10 |
| `nrca_allfit` | 140 | 137 | 0.2528 | -0.4194 | +0.786 | +0.405 | 0.702 | 5.89e-09 |
| `nrca_cosine_allfit` | 140 | 137 | 0.3141 | -0.4978 | +0.776 | +0.416 | 0.708 | 2.27e-09 |
| `rdr_3_allfit` | 140 | 137 | 0.4545 | -0.9696 | +0.712 | +0.371 | 0.685 | 9.69e-08 |
| `rdr_3_part1fit` | 140 | 137 | 1.541 | 0.005583 | +0.696 | +0.361 | 0.681 | 2e-07 |
| `rdr_path_allfit` | 140 | 137 | 0.8964 | -1.311 | +0.675 | +0.379 | 0.690 | 4.8e-08 |
| `rdr_path_part1fit` | 140 | 137 | 1.939 | -0.2843 | +0.668 | +0.375 | 0.687 | 6.95e-08 |
| `rdr_core_allfit` | 140 | 137 | 0.7696 | -1.565 | +0.667 | +0.378 | 0.689 | 5.5e-08 |
| `nrca_projection_allfit` | 140 | 137 | 0.3848 | -0.7825 | +0.667 | +0.378 | 0.689 | 5.5e-08 |
| `nrca_projection_part1fit` | 140 | 137 | 0.9304 | -0.3004 | +0.660 | +0.372 | 0.686 | 8.78e-08 |
| `rdr_core_part1fit` | 140 | 137 | 1.861 | -0.6008 | +0.660 | +0.372 | 0.686 | 8.78e-08 |

## Part1-Fit / Part2-Test

- `rdr_core_p1test`: direct AUROC `0.688`, logistic AUROC `0.688`, AUPRC `0.640`, Brier `0.222` (n_test `138`)
- `rdr_3_p1test`: direct AUROC `0.684`, logistic AUROC `0.684`, AUPRC `0.640`, Brier `0.222` (n_test `138`)
- `rdr_path_p1test`: direct AUROC `0.690`, logistic AUROC `0.690`, AUPRC `0.643`, Brier `0.222` (n_test `138`)
- `nrca_p1test`: direct AUROC `0.723`, logistic AUROC `0.723`, AUPRC `0.687`, Brier `0.218` (n_test `138`)

## Repeated Stratified CV

- `clinical_plus_eeg`: AUROC `0.604 +/- 0.068`, AUPRC `0.604 +/- 0.063`, Brier `0.249 +/- 0.024`, delta AUROC vs clinical+EEG `+0.000`
- `rdr_core_only`: AUROC `0.688 +/- 0.063`, AUPRC `0.647 +/- 0.068`, Brier `0.224 +/- 0.013`, delta AUROC vs clinical+EEG `+0.084`
- `rdr_3_only`: AUROC `0.683 +/- 0.065`, AUPRC `0.642 +/- 0.067`, Brier `0.222 +/- 0.014`, delta AUROC vs clinical+EEG `+0.079`
- `nrca_only`: AUROC `0.702 +/- 0.064`, AUPRC `0.670 +/- 0.073`, Brier `0.218 +/- 0.018`, delta AUROC vs clinical+EEG `+0.098`
- `components_core_only`: AUROC `0.684 +/- 0.063`, AUPRC `0.656 +/- 0.066`, Brier `0.221 +/- 0.018`, delta AUROC vs clinical+EEG `+0.081`
- `clinical_plus_eeg_plus_rdr_core`: AUROC `0.695 +/- 0.060`, AUPRC `0.658 +/- 0.062`, Brier `0.224 +/- 0.024`, delta AUROC vs clinical+EEG `+0.091`
- `clinical_plus_eeg_plus_rdr_3`: AUROC `0.696 +/- 0.060`, AUPRC `0.663 +/- 0.064`, Brier `0.223 +/- 0.024`, delta AUROC vs clinical+EEG `+0.093`
- `clinical_plus_eeg_plus_nrca`: AUROC `0.710 +/- 0.058`, AUPRC `0.675 +/- 0.064`, Brier `0.221 +/- 0.024`, delta AUROC vs clinical+EEG `+0.106`
- `clinical_plus_eeg_plus_components_core`: AUROC `0.699 +/- 0.058`, AUPRC `0.677 +/- 0.060`, Brier `0.225 +/- 0.025`, delta AUROC vs clinical+EEG `+0.095`
- `rdr_path_only`: AUROC `0.688 +/- 0.063`, AUPRC `0.648 +/- 0.068`, Brier `0.223 +/- 0.013`, delta AUROC vs clinical+EEG `+0.085`
- `clinical_plus_eeg_plus_rdr_path`: AUROC `0.694 +/- 0.058`, AUPRC `0.660 +/- 0.061`, Brier `0.224 +/- 0.024`, delta AUROC vs clinical+EEG `+0.090`

## Leave-One-Site-Out

- `clinical_plus_eeg`: AUROC `0.603 +/- 0.118`, AUPRC `0.606 +/- 0.053`, Brier `0.271 +/- 0.055`
- `rdr_core_only`: AUROC `0.665 +/- 0.064`, AUPRC `0.619 +/- 0.047`, Brier `0.223 +/- 0.020`
- `rdr_3_only`: AUROC `0.660 +/- 0.087`, AUPRC `0.629 +/- 0.044`, Brier `0.221 +/- 0.027`
- `nrca_only`: AUROC `0.694 +/- 0.092`, AUPRC `0.669 +/- 0.080`, Brier `0.216 +/- 0.032`
- `components_core_only`: AUROC `0.669 +/- 0.096`, AUPRC `0.626 +/- 0.073`, Brier `0.226 +/- 0.030`
- `clinical_plus_eeg_plus_rdr_core`: AUROC `0.676 +/- 0.106`, AUPRC `0.655 +/- 0.089`, Brier `0.243 +/- 0.060`
- `clinical_plus_eeg_plus_rdr_3`: AUROC `0.665 +/- 0.116`, AUPRC `0.634 +/- 0.087`, Brier `0.248 +/- 0.062`
- `clinical_plus_eeg_plus_nrca`: AUROC `0.679 +/- 0.129`, AUPRC `0.656 +/- 0.090`, Brier `0.250 +/- 0.067`
- `clinical_plus_eeg_plus_components_core`: AUROC `0.668 +/- 0.105`, AUPRC `0.629 +/- 0.053`, Brier `0.258 +/- 0.057`
- `rdr_path_only`: AUROC `0.667 +/- 0.065`, AUPRC `0.617 +/- 0.044`, Brier `0.223 +/- 0.020`
- `clinical_plus_eeg_plus_rdr_path`: AUROC `0.677 +/- 0.106`, AUPRC `0.651 +/- 0.086`, Brier `0.241 +/- 0.060`

## Label Permutation

- `nrca_allfit`: observed |d| `0.786`, null p95 `0.242`, empirical p `0.0005`
- `rdr_core_allfit`: observed |d| `0.667`, null p95 `0.244`, empirical p `0.0005`
- `rdr_3_allfit`: observed |d| `0.712`, null p95 `0.240`, empirical p `0.0005`
- `rdr_path_allfit`: observed |d| `0.675`, null p95 `0.245`, empirical p `0.0005`
- `max_abs_cohens_d_across_rdr_metrics`: observed |d| `0.786`, null p95 `0.270`, empirical p `0.0005`

## Shockable / Nonshockable Stress Test

- `shockable_only` / `nrca_allfit`: d `+0.540`, AUROC `0.630`, p `0.00463`
- `shockable_only` / `rdr_3_allfit`: d `+0.478`, AUROC `0.609`, p `0.0181`
- `shockable_only` / `rdr_path_allfit`: d `+0.447`, AUROC `0.615`, p `0.0121`
- `shockable_only` / `rdr_core_allfit`: d `+0.442`, AUROC `0.612`, p `0.0148`
- `nonshockable_only` / `nrca_allfit`: d `+1.082`, AUROC `0.791`, p `3.37e-06`
- `nonshockable_only` / `rdr_3_allfit`: d `+1.017`, AUROC `0.781`, p `7.37e-06`
- `nonshockable_only` / `rdr_path_allfit`: d `+0.995`, AUROC `0.788`, p `4.07e-06`
- `nonshockable_only` / `rdr_core_allfit`: d `+0.990`, AUROC `0.791`, p `3.37e-06`

## Strongest QC Associations

- `score_tube_capture_gate_median` vs `n_runs`: rho `-0.297`, p `4.88e-07`, n `277`
- `score_tube_capture_gate_median` vs `metric_weight_total`: rho `-0.276`, p `3.22e-06`, n `277`
- `score_tube_d_eff_median` vs `n_runs`: rho `+0.215`, p `0.00031`, n `277`
- `score_mnj9d_spectral_radius_median` vs `n_runs`: rho `-0.191`, p `0.00141`, n `277`
- `score_tube_d_eff_median` vs `metric_weight_total`: rho `+0.180`, p `0.00267`, n `277`
- `score_mnj9d_spectral_radius_median` vs `metric_weight_total`: rho `-0.164`, p `0.00618`, n `277`
- `score_mnj3d_spectral_radius_median` vs `metric_weight_total`: rho `-0.163`, p `0.00666`, n `277`
- `score_tube_d_eff_median` vs `channel_count_median`: rho `-0.154`, p `0.0103`, n `277`
- `score_tube_d_eff_median` vs `channel_coverage_frac_median`: rho `-0.154`, p `0.0103`, n `277`
- `score_mnj3d_spectral_radius_median` vs `n_runs`: rho `-0.149`, p `0.0132`, n `277`

## Claim Status

`NRCA` is the new out-of-family geometric proposal: it asks whether a patient lies inside a coherent recovery cone rather than merely having a high linear sum. `RDR_core` remains an internally tested composite proposal, not a bedside biomarker. `RDR_path` remains exploratory because the trajectory layer is not yet a frozen confirmatory family and may mix path roughness with non-neural data quality effects.

## Limitations And Article Placement

- `NRCA` is post hoc and should be treated as a new exploratory geometry metric until frozen and externally or prospectively replicated.
- `RDR_3` may remain the strongest pooled linear-family contrast in this run, but it is also a post hoc composite over a cohort already used to characterize the component effects.
- The analysis inherits the manuscript-facing limitations: CPC5 is not a pure neural-viability endpoint, WLST/time-to-death are unavailable, and artifact burden is only represented by coarse coverage/run-count proxies.
- The recommended placement is a short exploratory supplement or Discussion paragraph after the layered reachability/Jacobian result, framed as a compact recovery-linked geometry index. It should not replace the existing primary reachability family unless it is frozen and externally or prospectively replicated.
