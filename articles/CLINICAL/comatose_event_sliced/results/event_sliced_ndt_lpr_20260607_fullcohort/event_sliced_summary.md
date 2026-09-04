# Event-Sliced NDT / Latent Perturbation Reactivity

## Cohort

- processed roots: `2`
- runs analyzed: `4441`
- subjects analyzed: `261`
- detector threshold: `E_t > 3`
- Jacobian weight eta: `0.5`
- regional support: `>= 2` of `frontal, central, parietal_occipital, temporal` above robust-z `1.5`
- episode merge gap: `<= 1` window(s)
- minimum aligned windows per run: `80`

| label | n_subjects |
|---|---:|
| CPC1 | 130 |
| CPC5 | 131 |

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

- `run_median_spec_9d`: AUC `0.692` (higher_in_CPC5), CPC1 median `0.1`, CPC5 median `0.114`, Spearman rho vs `run_median_spec` `+0.531`
- `run_median_spec`: AUC `0.689` (higher_in_CPC5), CPC1 median `0.0721`, CPC5 median `0.0757`, Spearman rho vs `run_median_spec` `+1.000`
- `median_recovery_half_time_min`: AUC `0.658` (higher_in_CPC1), CPC1 median `0.267`, CPC5 median `0.233`, Spearman rho vs `run_median_spec` `-0.338`
- `median_amp`: AUC `0.651` (higher_in_CPC5), CPC1 median `1.43`, CPC5 median `1.68`, Spearman rho vs `run_median_spec` `+0.537`
- `frac_recovered`: AUC `0.643` (higher_in_CPC5), CPC1 median `0.329`, CPC5 median `0.4`, Spearman rho vs `run_median_spec` `+0.333`
- `median_peak_spec`: AUC `0.621` (higher_in_CPC5), CPC1 median `0.0664`, CPC5 median `0.0728`, Spearman rho vs `run_median_spec` `+0.469`
- `episode_rate_per_min`: AUC `0.563` (higher_in_CPC5), CPC1 median `0.418`, CPC5 median `0.676`, Spearman rho vs `run_median_spec` `+0.076`
- `median_residual`: AUC `0.503` (higher_in_CPC1), CPC1 median `0.942`, CPC5 median `0.927`, Spearman rho vs `run_median_spec` `+0.173`

## Repeated CV

- `run_median_spec_only`: AUROC `0.688 +/- 0.065`, AUPRC `0.729 +/- 0.064`, Brier `0.224 +/- 0.016`
- `lpr_profile_only`: AUROC `0.672 +/- 0.080`, AUPRC `0.719 +/- 0.073`, Brier `0.227 +/- 0.023`
- `run_median_spec_plus_lpr_profile`: AUROC `0.696 +/- 0.077`, AUPRC `0.739 +/- 0.072`, Brier `0.221 +/- 0.025`

## Interpretation Guardrail

This output is exploratory and implementation-facing. It tests whether event-sliced latent perturbation reactivity carries outcome signal beyond a run-level median Jacobian metric, but it is not yet a frozen confirmatory specification.
