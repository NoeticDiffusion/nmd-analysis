# Event-Sliced NDT / Latent Perturbation Reactivity

## Cohort

- processed roots: `2`
- runs analyzed: `192`
- subjects analyzed: `16`
- detector threshold: `E_t > 3`
- Jacobian weight eta: `0.5`
- regional support: `>= 2` of `frontal, central, parietal_occipital, temporal` above robust-z `1.5`
- episode merge gap: `<= 1` window(s)
- minimum aligned windows per run: `80`

| label | n_subjects |
|---|---:|
| CPC1 | 8 |
| CPC5 | 8 |

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

- `run_median_spec`: AUC `0.906` (higher_in_CPC5), CPC1 median `0.0745`, CPC5 median `0.0842`, Spearman rho vs `run_median_spec` `+1.000`
- `median_peak_spec`: AUC `0.734` (higher_in_CPC5), CPC1 median `0.062`, CPC5 median `0.0728`, Spearman rho vs `run_median_spec` `+0.862`
- `run_median_spec_9d`: AUC `0.690` (higher_in_CPC5), CPC1 median `0.105`, CPC5 median `0.122`, Spearman rho vs `run_median_spec` `+0.604`
- `episode_rate_per_min`: AUC `0.680` (higher_in_CPC5), CPC1 median `0.256`, CPC5 median `0.346`, Spearman rho vs `run_median_spec` `+0.216`
- `median_residual`: AUC `0.656` (higher_in_CPC5), CPC1 median `1.01`, CPC5 median `1.16`, Spearman rho vs `run_median_spec` `+0.056`
- `median_amp`: AUC `0.641` (higher_in_CPC5), CPC1 median `1.6`, CPC5 median `1.87`, Spearman rho vs `run_median_spec` `+0.006`
- `frac_recovered`: AUC `0.594` (higher_in_CPC5), CPC1 median `0.28`, CPC5 median `0.322`, Spearman rho vs `run_median_spec` `-0.094`
- `median_recovery_half_time_min`: AUC `0.531` (higher_in_CPC1), CPC1 median `0.25`, CPC5 median `0.217`, Spearman rho vs `run_median_spec` `+0.230`

## Repeated CV

- `run_median_spec_only`: AUROC `0.902 +/- 0.207`, AUPRC `0.946 +/- 0.130`, Brier `0.188 +/- 0.056`
- `lpr_profile_only`: AUROC `0.685 +/- 0.367`, AUPRC `0.826 +/- 0.219`, Brier `0.237 +/- 0.106`
- `run_median_spec_plus_lpr_profile`: AUROC `0.752 +/- 0.325`, AUPRC `0.866 +/- 0.198`, Brier `0.202 +/- 0.096`

## Interpretation Guardrail

This output is exploratory and implementation-facing. It tests whether event-sliced latent perturbation reactivity carries outcome signal beyond a run-level median Jacobian metric, but it is not yet a frozen confirmatory specification.
