# Additional Parkinson cognitive workload QC summary (`ds003509`)

This QC pass adds four checks to the cognitive workload article-facing results:

1. geometry versus classical EEG comparison,
2. focal geometry-versus-classical association checks,
3. leave-one-subject-out and standard-metric permutation robustness,
4. and a circular time-shift null for focal event rows.

## Geometry versus classical EEG

- `Control_vs_Parkinson_OFF`: best geometry row `regional_9d / d_s_mean` (`d = 1.166`, `q = 0.01349`) vs best classical row `eeg_classical_relative_alpha_std` (`d = 0.9238`, `q = 0.09595`); `|d|` gap = `0.2424`.
- `Control_vs_Parkinson_ON`: best geometry row `regional_9d / e_m_mean` (`d = -0.9908`, `q = 0.01349`) vs best classical row `eeg_classical_relative_alpha_std` (`d = 0.9227`, `q = 0.09595`); `|d|` gap = `0.06808`.
- `Parkinson_OFF_vs_ON`: best geometry row `global_mnps_3d / m_median` (`d = 0.5154`, `q = 0.07196`) vs best classical row `eeg_classical_relative_alpha_mean` (`d = -0.3641`, `q = 0.6973`); `|d|` gap = `0.1513`.

## Focal geometry versus classical alignment

- `Global e_m_median`: strongest classical correlate `eeg_classical_relative_beta_std` (pooled rho = -0.747, p = 3.803e-11; group-adjusted rho = -0.6765, p = 1.048e-08; n = `56`), interpreted as `strong alignment; reducibility remains possible`.
- `Persistence hysteresis d_eff`: strongest classical correlate `eeg_classical_complexity_spectral_entropy_mad_sigma` (pooled rho = 0.4146, p = 0.00149; group-adjusted rho = 0.3528, p = 0.007661; n = `56`), interpreted as `partial alignment, but not reducible in this check`.
- `Persistence log-eig variance`: strongest classical correlate `eeg_classical_relative_beta_std` (pooled rho = -0.7218, p = 3.447e-10; group-adjusted rho = -0.6403, p = 1.074e-07; n = `56`), interpreted as `strong alignment; reducibility remains possible`.
- `capture_gate`: strongest classical correlate `eeg_classical_ratio_delta_alpha_delta_mean_median` (pooled rho = 0.717, p = 5.127e-10; group-adjusted rho = 0.6869, p = 5.035e-09; n = `56`), interpreted as `strong alignment; reducibility remains possible`.
- `q_ratio_h4`: strongest classical correlate `eeg_classical_peak_spectral_edge_95_std` (pooled rho = -0.8362, p = 1.044e-15; group-adjusted rho = -0.8057, p = 6.968e-14; n = `56`), interpreted as `strong alignment; reducibility remains possible`.

## Leave-one-subject-out stability

- `Alpha SD (Control vs ON, exploratory)`: full `d = 0.9227`, full `p = 0.002242`, leave-one-out `d` range `0.8769` to `1.035`, median `0.9054`, sign consistency `1`.
- `Alpha SD (Control vs OFF, exploratory)`: full `d = 0.9238`, full `p = 0.001357`, leave-one-out `d` range `0.8788` to `1.018`, median `0.9085`, sign consistency `1`.
- `Alpha mean (Control vs OFF, exploratory)`: full `d = 0.7965`, full `p = 0.04648`, leave-one-out `d` range `0.744` to `0.8751`, median `0.7845`, sign consistency `1`.
- `Alpha median (Control vs OFF, exploratory)`: full `d = 0.7246`, full `p = 0.1101`, leave-one-out `d` range `0.668` to `0.7956`, median `0.7137`, sign consistency `1`.
- `Relative alpha mean (OFF vs ON, exploratory)`: full `d = -0.3641`, full `p = 0.03368`, leave-one-out `d` range `-0.5783` to `-0.3067`, median `-0.3641`, sign consistency `1`.
- `PSE95 SD (OFF vs ON, exploratory)`: full `d = 0.34`, full `p = 0.1569`, leave-one-out `d` range `0.2787` to `0.4125`, median `0.34`, sign consistency `1`.
- `Global e_m_median`: full `d = -0.9848`, full `p = 0.001354`, leave-one-out `d` range `-1.14` to `-0.9391`, median `-0.9744`, sign consistency `1`.
- `q_ratio_h4`: full `d = -0.6316`, full `p = 0.007025`, leave-one-out `d` range `-0.7741` to `-0.5778`, median `-0.6192`, sign consistency `1`.
- `capture_gate`: full `d = 0.6162`, full `p = 0.02226`, leave-one-out `d` range `0.5589` to `0.7535`, median `0.6079`, sign consistency `1`.
- `Persistence log-eig variance`: full `d = -0.9188`, full `p = 0.0009056`, leave-one-out `d` range `-1.07` to `-0.8766`, median `-0.9025`, sign consistency `1`.
- `Persistence hysteresis d_eff`: full `d = 0.7039`, full `p = 0.008536`, leave-one-out `d` range `0.646` to `0.8228`, median `0.6972`, sign consistency `1`.

## Standard permutation null

- `Alpha mean (Control vs OFF, exploratory)`: observed `d = 0.7965`, null mean `|d| = 0.2146`, null p95 `|d| = 0.5322`, empirical `p = 0.02326`.
- `Alpha median (Control vs OFF, exploratory)`: observed `d = 0.7246`, null mean `|d| = 0.2274`, null p95 `|d| = 0.5259`, empirical `p = 0.007752`.
- `Alpha SD (Control vs OFF, exploratory)`: observed `d = 0.9238`, null mean `|d| = 0.2131`, null p95 `|d| = 0.5239`, empirical `p = 0.007752`.
- `Alpha SD (Control vs ON, exploratory)`: observed `d = 0.9227`, null mean `|d| = 0.2279`, null p95 `|d| = 0.5317`, empirical `p = 0.007752`.
- `capture_gate`: observed `d = 0.6162`, null mean `|d| = 0.2187`, null p95 `|d| = 0.5277`, empirical `p = 0.05426`.
- `q_ratio_h4`: observed `d = -0.6316`, null mean `|d| = 0.1991`, null p95 `|d| = 0.497`, empirical `p = 0.0155`.
- `Global e_m_median`: observed `d = -0.9848`, null mean `|d| = 0.2318`, null p95 `|d| = 0.5484`, empirical `p = 0.007752`.
- `Persistence hysteresis d_eff`: observed `d = 0.7039`, null mean `|d| = 0.2093`, null p95 `|d| = 0.4942`, empirical `p = 0.007752`.
- `Persistence log-eig variance`: observed `d = -0.9188`, null mean `|d| = 0.2044`, null p95 `|d| = 0.5252`, empirical `p = 0.0155`.
- `PSE95 SD (OFF vs ON, exploratory)`: observed `d = 0.34`, null mean `|d| = 0.1569`, null p95 `|d| = 0.3612`, empirical `p = 0.06977`.
- `Relative alpha mean (OFF vs ON, exploratory)`: observed `d = -0.3641`, null mean `|d| = 0.153`, null p95 `|d| = 0.3861`, empirical `p = 0.07752`.

## Circular time-shift null

- `test_response_all hysteresis_area_de (best event, exploratory)`: observed `d = 1.002`, null mean `|d| = 0.3667`, null p95 `|d| = 0.5671`, empirical `p = 0.07692`.
- `test_all hysteresis_area_de (exploratory)`: observed `d = 0.9605`, null mean `|d| = 0.2986`, null p95 `|d| = 0.4918`, empirical `p = 0.07692`.
- `training_feedback_reward tortuosity (exploratory)`: observed `d = 0.6953`, null mean `|d| = 0.4098`, null p95 `|d| = 0.5881`, empirical `p = 0.07692`.

## Boundaries

- Cross-fit / split validation was intentionally not used because the current cohort is too small for that to be a strong primary robustness claim.
- The time-shift null preserves within-run autocorrelation and segment counts while destroying the original event-to-trajectory alignment.
- Exploratory rows remain explicitly exploratory even when they are visually or robustly interesting.
