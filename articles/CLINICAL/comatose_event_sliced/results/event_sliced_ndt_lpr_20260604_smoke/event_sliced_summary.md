# Event-Sliced NDT / Latent Perturbation Reactivity

## Cohort

- processed roots: `2`
- runs analyzed: `9`
- subjects analyzed: `9`
- detector threshold: `E_t > 3`
- Jacobian weight eta: `0.5`
- regional support: `>= 2` of `frontal, central, parietal_occipital, temporal` above robust-z `2`
- episode merge gap: `<= 1` window(s)
- minimum aligned windows per run: `60`

| label | n_subjects |
|---|---:|
| CPC1 | 4 |
| CPC5 | 5 |

## Detector

```text
E_t = robz(||mnps_3d_dot||) + robz(||d signed_log1p(features_raw)||)
    + 0.5 * robz(|d spectral_radius(J)|)
episodes = supra-threshold windows clustered with short-gap merging
run features = rate/min, median amplitude, recovery half-time, residual,
               fraction recovered, and peak Jacobian spectral radius
subject features = median over runs
```

## Single Features

- `median_peak_spec`: AUC `0.850` (higher_in_CPC5), CPC1 median `0.0897`, CPC5 median `0.124`, Spearman rho vs `run_median_spec` `+0.783`
- `run_median_spec`: AUC `0.700` (higher_in_CPC5), CPC1 median `0.0743`, CPC5 median `0.103`, Spearman rho vs `run_median_spec` `+1.000`
- `median_recovery_half_time_min`: AUC `0.550` (higher_in_CPC5), CPC1 median `0.4`, CPC5 median `0.4`, Spearman rho vs `run_median_spec` `+0.153`
- `median_residual`: AUC `0.550` (higher_in_CPC1), CPC1 median `2.36`, CPC5 median `2.29`, Spearman rho vs `run_median_spec` `+0.383`
- `frac_recovered`: AUC `0.550` (higher_in_CPC1), CPC1 median `0.169`, CPC5 median `0.106`, Spearman rho vs `run_median_spec` `-0.333`
- `median_amp`: AUC `0.500` (higher_in_CPC5), CPC1 median `3.64`, CPC5 median `3.81`, Spearman rho vs `run_median_spec` `-0.400`
- `episode_rate_per_min`: AUC `0.500` (higher_in_CPC1), CPC1 median `0.496`, CPC5 median `0.613`, Spearman rho vs `run_median_spec` `+0.433`

## Repeated CV

- `run_median_spec_only`: AUROC `0.688 +/- 0.142`, AUPRC `0.842 +/- 0.070`, Brier `0.217 +/- 0.025`
- `lpr_profile_only`: AUROC `0.438 +/- 0.185`, AUPRC `0.704 +/- 0.153`, Brier `0.285 +/- 0.040`
- `run_median_spec_plus_lpr_profile`: AUROC `0.562 +/- 0.185`, AUPRC `0.787 +/- 0.076`, Brier `0.259 +/- 0.076`

## Interpretation Guardrail

This output is exploratory and implementation-facing. It tests whether event-sliced latent perturbation reactivity carries outcome signal beyond a run-level median Jacobian metric, but it is not yet a frozen confirmatory specification.
