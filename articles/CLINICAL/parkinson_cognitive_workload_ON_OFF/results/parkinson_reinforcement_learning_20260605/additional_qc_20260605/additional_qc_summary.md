# Additional Parkinson cognitive workload QC summary (`ds003506`)

This QC pass adds four checks to the cognitive workload article-facing results:

1. geometry versus classical EEG comparison,
2. focal geometry-versus-classical association checks,
3. leave-one-subject-out and standard-metric permutation robustness,
4. and a circular time-shift null for focal event rows.

## Geometry versus classical EEG

- `Control_vs_Parkinson_OFF`: best geometry row `regional_9d / d_s_mean` (`d = 1.064`, `q = 0.02699`) vs best classical row `eeg_classical_relative_alpha_mean` (`d = 1.113`, `q = 0.01599`); `|d|` gap = `-0.04929`.
- `Control_vs_Parkinson_ON`: best geometry row `global_mnps_9d_block_jacobian / block_frobenius_mean` (`d = -0.7136`, `q = 0.08996`) vs best classical row `eeg_classical_relative_alpha_iqr` (`d = 0.5908`, `q = 0.9945`); `|d|` gap = `0.1228`.
- `Parkinson_OFF_vs_ON`: best geometry row `regional_3d / e_median` (`d = -0.5108`, `q = 0.2249`) vs best classical row `eeg_classical_peak_spectral_edge_95_delta_mean_median` (`d = 0.4574`, `q = 0.3309`); `|d|` gap = `0.05339`.

## Focal geometry versus classical alignment

- `Global d_s_mean`: strongest classical correlate `eeg_classical_ratio_theta_alpha_median` (pooled rho = -0.9738, p = 2.009e-36; group-adjusted rho = -0.9056, p = 9.112e-22; n = `56`), interpreted as `strong alignment; reducibility remains possible`.
- `Global d_s_median`: strongest classical correlate `eeg_classical_ratio_theta_alpha_median` (pooled rho = -1, p = 0; group-adjusted rho = -0.9444, p = 9.244e-28; n = `56`), interpreted as `strong alignment; reducibility remains possible`.
- `a_operator_norm (exploratory)`: strongest classical correlate `eeg_classical_peak_spectral_edge_95_iqr` (pooled rho = -0.5537, p = 9.566e-06; group-adjusted rho = -0.5607, p = 6.977e-06; n = `56`), interpreted as `partial alignment, but not reducible in this check`.
- `capture_gate (exploratory)`: strongest classical correlate `eeg_classical_complexity_hjorth_complexity_std` (pooled rho = 0.5366, p = 2.013e-05; group-adjusted rho = 0.5548, p = 9.136e-06; n = `56`), interpreted as `partial alignment, but not reducible in this check`.
- `persistence_tau_log_det (exploratory)`: strongest classical correlate `eeg_classical_peak_spectral_edge_95_std` (pooled rho = -0.4206, p = 0.00154; group-adjusted rho = -0.4226, p = 0.001456; n = `54`), interpreted as `partial alignment, but not reducible in this check`.
- `tube_log_det_split_half_a (exploratory)`: strongest classical correlate `eeg_classical_complexity_hjorth_mobility_iqr` (pooled rho = 0.7003, p = 1.889e-09; group-adjusted rho = 0.6823, p = 7.002e-09; n = `56`), interpreted as `strong alignment; reducibility remains possible`.

## Leave-one-subject-out stability

- `Alpha mean`: full `d = 1.113`, full `p = 0.001018`, leave-one-out `d` range `1.071` to `1.238`, median `1.095`, sign consistency `1`.
- `Alpha median`: full `d = 1.113`, full `p = 0.0007585`, leave-one-out `d` range `1.071` to `1.238`, median `1.096`, sign consistency `1`.
- `Alpha IQR`: full `d = 0.9559`, full `p = 0.001798`, leave-one-out `d` range `0.9098` to `1.055`, median `0.9466`, sign consistency `1`.
- `Alpha MAD-sigma`: full `d = 0.9384`, full `p = 0.001798`, leave-one-out `d` range `0.8917` to `1.047`, median `0.9287`, sign consistency `1`.
- `PSE95 delta mean-median (OFF vs ON, exploratory)`: full `d = 0.4574`, full `p = 0.02636`, leave-one-out `d` range `0.4089` to `0.6121`, median `0.4574`, sign consistency `1`.
- `Gamma MAD-sigma (OFF vs ON, exploratory)`: full `d = -0.4393`, full `p = 0.02636`, leave-one-out `d` range `-0.5641` to `-0.3935`, median `-0.4393`, sign consistency `1`.
- `Global d_s_mean`: full `d = 0.8476`, full `p = 0.007379`, leave-one-out `d` range `0.7981` to `0.978`, median `0.8366`, sign consistency `1`.
- `Global d_s_median`: full `d = 0.8926`, full `p = 0.004029`, leave-one-out `d` range `0.8444` to `1.052`, median `0.8802`, sign consistency `1`.
- `a_operator_norm (exploratory)`: full `d = 0.559`, full `p = 0.0629`, leave-one-out `d` range `0.4888` to `0.6754`, median `0.5552`, sign consistency `1`.
- `capture_gate (exploratory)`: full `d = 0.5418`, full `p = 0.103`, leave-one-out `d` range `0.476` to `0.6196`, median `0.5383`, sign consistency `1`.
- `tube_log_det_split_half_a (exploratory)`: full `d = 0.6076`, full `p = 0.09303`, leave-one-out `d` range `0.5503` to `0.6752`, median `0.6085`, sign consistency `1`.
- `persistence_tau_log_det (exploratory)`: full `d = -0.5744`, full `p = 0.01811`, leave-one-out `d` range `-0.6539` to `-0.5015`, median `-0.5689`, sign consistency `1`.

## Standard permutation null

- `Alpha IQR`: observed `d = 0.9559`, null mean `|d| = 0.1897`, null p95 `|d| = 0.4764`, empirical `p = 0.007752`.
- `Alpha MAD-sigma`: observed `d = 0.9384`, null mean `|d| = 0.1916`, null p95 `|d| = 0.4512`, empirical `p = 0.007752`.
- `Alpha mean`: observed `d = 1.113`, null mean `|d| = 0.2223`, null p95 `|d| = 0.5963`, empirical `p = 0.007752`.
- `Alpha median`: observed `d = 1.113`, null mean `|d| = 0.2196`, null p95 `|d| = 0.4834`, empirical `p = 0.007752`.
- `a_operator_norm (exploratory)`: observed `d = 0.559`, null mean `|d| = 0.2265`, null p95 `|d| = 0.5054`, empirical `p = 0.04651`.
- `capture_gate (exploratory)`: observed `d = 0.5418`, null mean `|d| = 0.2321`, null p95 `|d| = 0.5927`, empirical `p = 0.07752`.
- `Global d_s_mean`: observed `d = 0.8476`, null mean `|d| = 0.1875`, null p95 `|d| = 0.4444`, empirical `p = 0.007752`.
- `Global d_s_median`: observed `d = 0.8926`, null mean `|d| = 0.2296`, null p95 `|d| = 0.5482`, empirical `p = 0.007752`.
- `persistence_tau_log_det (exploratory)`: observed `d = -0.5744`, null mean `|d| = 0.2182`, null p95 `|d| = 0.5`, empirical `p = 0.0155`.
- `tube_log_det_split_half_a (exploratory)`: observed `d = 0.6076`, null mean `|d| = 0.2008`, null p95 `|d| = 0.4991`, empirical `p = 0.0155`.
- `PSE95 delta mean-median (OFF vs ON, exploratory)`: observed `d = 0.4574`, null mean `|d| = 0.1494`, null p95 `|d| = 0.39`, empirical `p = 0.03876`.
- `Gamma MAD-sigma (OFF vs ON, exploratory)`: observed `d = -0.4393`, null mean `|d| = 0.1565`, null p95 `|d| = 0.4303`, empirical `p = 0.05426`.

## Circular time-shift null

- `match_feedback_punishment hysteresis_area_de (best event, exploratory)`: observed `d = 0.6042`, null mean `|d| = 0.4098`, null p95 `|d| = 0.5375`, empirical `p = 0.2`.

## Boundaries

- Cross-fit / split validation was intentionally not used because the current cohort is too small for that to be a strong primary robustness claim.
- The time-shift null preserves within-run autocorrelation and segment counts while destroying the original event-to-trajectory alignment.
- Exploratory rows remain explicitly exploratory even when they are visually or robustly interesting.
