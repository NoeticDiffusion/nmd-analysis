# Event-Sliced NDT / Latent Perturbation Reactivity

## Cohort

- processed roots: `2`
- runs analyzed: `4218`
- subjects analyzed: `278`
- detector threshold: `E_t > 3`
- Jacobian weight eta: `0.5`
- regional support: `>= 2` of `frontal, central, parietal_occipital, temporal` above robust-z `1.5`
- episode merge gap: `<= 1` window(s)
- minimum aligned windows per run: `80`

| label | n_subjects |
|---|---:|
| CPC1 | 140 |
| CPC5 | 138 |

## Detector

```text
E_t = robz(||d mnps_3d||) + robz(||d log(abs(features_raw) + eps)||)
    + 0.5 * robz(|d spectral_radius(J)|)
episodes = supra-threshold windows clustered with short-gap merging
run features = rate/min, median amplitude, recovery half-time, residual,
               fraction recovered, and peak Jacobian spectral radius
subject features = median over runs
```

## Single Features

- `run_median_spec`: AUC `0.679` (higher_in_CPC5), CPC1 median `0.0715`, CPC5 median `0.0757`, Spearman rho vs `run_median_spec` `+1.000`
- `median_amp`: AUC `0.653` (higher_in_CPC5), CPC1 median `1.4`, CPC5 median `1.66`, Spearman rho vs `run_median_spec` `+0.648`
- `median_recovery_half_time_min`: AUC `0.641` (higher_in_CPC1), CPC1 median `0.267`, CPC5 median `0.2`, Spearman rho vs `run_median_spec` `-0.274`
- `frac_recovered`: AUC `0.631` (higher_in_CPC5), CPC1 median `0.333`, CPC5 median `0.402`, Spearman rho vs `run_median_spec` `+0.300`
- `median_peak_spec`: AUC `0.624` (higher_in_CPC5), CPC1 median `0.0661`, CPC5 median `0.0731`, Spearman rho vs `run_median_spec` `+0.429`
- `episode_rate_per_min`: AUC `0.543` (higher_in_CPC5), CPC1 median `0.745`, CPC5 median `0.834`, Spearman rho vs `run_median_spec` `-0.005`
- `median_residual`: AUC `0.510` (higher_in_CPC5), CPC1 median `0.937`, CPC5 median `0.922`, Spearman rho vs `run_median_spec` `+0.354`

## Repeated CV

- `run_median_spec_only`: AUROC `0.678 +/- 0.072`, AUPRC `0.715 +/- 0.075`, Brier `0.236 +/- 0.013`
- `lpr_profile_only`: AUROC `0.676 +/- 0.066`, AUPRC `0.708 +/- 0.066`, Brier `0.224 +/- 0.018`
- `run_median_spec_plus_lpr_profile`: AUROC `0.678 +/- 0.065`, AUPRC `0.709 +/- 0.066`, Brier `0.225 +/- 0.019`

## Interpretation Guardrail

This output is exploratory and implementation-facing. It tests whether event-sliced latent perturbation reactivity carries outcome signal beyond a run-level median Jacobian metric, but it is not yet a frozen confirmatory specification.
