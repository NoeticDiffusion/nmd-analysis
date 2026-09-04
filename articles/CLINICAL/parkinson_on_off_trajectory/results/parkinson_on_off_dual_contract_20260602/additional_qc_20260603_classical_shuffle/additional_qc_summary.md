# Additional Parkinson QC / robustness summary

This supplement-facing QC pass adds three checks to the mixed-contract Parkinson rerun:

1. direct comparison against the best article-facing conventional EEG comparator rows,
2. leave-one-subject-out stability for focal geometry and classical rows,
3. and a circular time-shift null for the retained event-/stage-locked trajectory rows.

## Geometry versus conventional EEG comparators

- `Control_vs_Parkinson_OFF`: best geometry row `speed_median` (`d = -1.212`, `q = 0.002539`) vs best classical row `eeg_classical_ratio_theta_alpha_median` (`d = -0.4718`, `q = 0.4937`); `|d|` gap = `0.7398`.
- `Control_vs_Parkinson_ON`: best geometry row `mdr_median` (`d = 1.478`, `q = 0.009495`) vs best classical row `eeg_classical_ratio_theta_alpha_median` (`d = -0.6278`, `q = 0.2985`); `|d|` gap = `0.8502`.
- `Parkinson_OFF_vs_ON`: best geometry row `signed_divergence_balance_mean_neg` (`d = -0.711`, `q = 0.04398`) vs best classical row `eeg_classical_relative_theta_median` (`d = 0.2855`, `q = 0.987`); `|d|` gap = `0.4255`.

## Focal NMD rows versus classical sidecars

- `Control vs OFF / eyes_closed noetic_action_kinetic (9D)`: strongest classical correlate `eeg_classical_ratio_slowing_index_median` (pooled rho = 0.1716, p = 0.2383; group-adjusted rho = 0.2196, p = 0.1295; n = `49`), interpreted as `contrast-aligned but not reducible in this check`.
- `Control vs OFF / eyes_closed speed_median (3D)`: strongest classical correlate `eeg_classical_complexity_hjorth_complexity_median` (pooled rho = 0.3645, p = 0.01003; group-adjusted rho = 0.4085, p = 0.003571; n = `49`), interpreted as `partial alignment, but not reducible in this check`.
- `Control vs OFF / frontal 9D d_n_std`: strongest classical correlate `eeg_classical_complexity_permutation_entropy_median` (pooled rho = -0.0472, p = 0.7448; group-adjusted rho = 0.198, p = 0.1681; n = `50`), interpreted as `contrast-aligned but not reducible in this check`.
- `Control vs ON / global 9D mdr_median`: strongest classical correlate `eeg_classical_ratio_theta_alpha_median` (pooled rho = -0.3442, p = 0.0144; group-adjusted rho = -0.3337, p = 0.01785; n = `50`), interpreted as `partial alignment, but not reducible in this check`.
- `Control vs ON / novel_tone hysteresis_area_me`: strongest classical correlate `eeg_classical_peak_median_frequency_median` (pooled rho = -0.5071, p = 0.0001709; group-adjusted rho = -0.4642, p = 0.0006841; n = `50`), interpreted as `partial alignment, but not reducible in this check`.
- `Control vs ON / standard_tone hysteresis_area_me`: strongest classical correlate `eeg_classical_peak_median_frequency_median` (pooled rho = -0.496, p = 0.0002494; group-adjusted rho = -0.4609, p = 0.0007569; n = `50`), interpreted as `partial alignment, but not reducible in this check`.
- `OFF vs ON / signed_divergence_balance_mean_neg`: strongest classical correlate `eeg_classical_complexity_hjorth_mobility_median` (delta rho = 0.2946, p = 0.1528; n = `25`), interpreted as `limited paired alignment`.

## Leave-one-subject-out stability

- `Control vs OFF / frontal 9D d_n_std`: full `d = -1.268`, full `p = 6.415e-05`, leave-one-out `d` range `-1.432` to `-1.225`, median `-1.259`, sign consistency `1`.
- `Control vs OFF / eyes_closed speed_median (3D)`: full `d = -1.212`, full `p = 4.701e-05`, leave-one-out `d` range `-1.386` to `-1.167`, median `-1.207`, sign consistency `1`.
- `Control vs OFF / eyes_closed noetic_action_kinetic (9D)`: full `d = -1.085`, full `p = 7.187e-05`, leave-one-out `d` range `-1.167` to `-1.034`, median `-1.077`, sign consistency `1`.
- `Control vs ON / global 9D mdr_median`: full `d = 1.478`, full `p = 1.385e-05`, leave-one-out `d` range `1.435` to `1.682`, median `1.453`, sign consistency `1`.
- `Control vs ON / novel_tone hysteresis_area_me`: full `d = -1.039`, full `p = 0.0003842`, leave-one-out `d` range `-1.118` to `-0.99`, median `-1.038`, sign consistency `1`.
- `Control vs ON / standard_tone hysteresis_area_me`: full `d = -0.9899`, full `p = 0.001563`, leave-one-out `d` range `-1.12` to `-0.9391`, median `-0.975`, sign consistency `1`.
- `OFF vs ON / signed_divergence_balance_mean_neg`: full `d = -0.711`, full `p = 0.003419`, leave-one-out `d` range `-0.799` to `-0.6683`, median `-0.711`, sign consistency `1`.
- `Classical best / Control vs OFF / theta-alpha ratio median`: full `d = -0.4718`, full `p = 0.187`, leave-one-out `d` range `-0.5911` to `-0.3825`, median `-0.4586`, sign consistency `1`.
- `Classical best / Control vs ON / theta-alpha ratio median`: full `d = -0.6278`, full `p = 0.1683`, leave-one-out `d` range `-0.689` to `-0.5553`, median `-0.6148`, sign consistency `1`.
- `Classical best / OFF vs ON / relative theta median`: full `d = 0.2855`, full `p = 0.4742`, leave-one-out `d` range `0.2046` to `0.3609`, median `0.2855`, sign consistency `1`.

## Time-shift null for event/stage-locked rows

- `Control vs OFF / eyes_closed speed_median (3D)`: observed `d = -1.212`, null mean `|d| = 0.359`, null p95 `|d| = 0.7`, empirical `p = 0.08`.
- `Control vs OFF / eyes_closed noetic_action_kinetic (9D)`: observed `d = -1.085`, null mean `|d| = 0.2857`, null p95 `|d| = 0.7176`, empirical `p = 0.04`.
- `Control vs ON / novel_tone hysteresis_area_me`: observed `d = -1.039`, null mean `|d| = 0.5568`, null p95 `|d| = 0.8809`, empirical `p = 0.08`.
- `Control vs ON / standard_tone hysteresis_area_me`: observed `d = -0.9899`, null mean `|d| = 0.6209`, null p95 `|d| = 0.9058`, empirical `p = 0.04`.

## Boundaries

- Leave-one-site-out was not run because the article-facing ds003490 bundle does not expose a reliable site / hospital variable for this cohort.
- The time-shift null rolls the exported trajectory relative to the original block labels, preserving within-run autocorrelation and block counts while destroying true label alignment.
