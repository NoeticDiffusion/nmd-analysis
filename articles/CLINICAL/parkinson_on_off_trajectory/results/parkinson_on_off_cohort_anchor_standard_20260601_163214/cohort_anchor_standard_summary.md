# Cohort-anchor standard-layer exploratory

- Cohort contrast file: `J:\repos\NoeticDiffusion\articles\CLINICAL\parkinson_on_off_trajectory\results\parkinson_on_off_cohort_anchor_standard_20260601_163214\standard_analysis\ds003490_contrast_results_20260601_165029.parquet`
- Subject-anchor reference: `J:\repos\NoeticDiffusion\articles\CLINICAL\parkinson_on_off_trajectory\results\parkinson_on_off_exploratory_20260601\standard_analysis\ds003490_contrast_results_20260601_123955.parquet`
- Requested contract: `cohort_anchored`
- Cleaned blocks available: ds003490_global_mnps_3d_20260601_163215, ds003490_global_mnps_9d_20260601_163219, ds003490_global_mnps_9d_block_jacobian_20260601_163224, ds003490_global_mnps_jacobian_3d_20260601_163218, ds003490_global_mnps_jacobian_9d_20260601_163222, ds003490_global_mnps_jacobian_9d_block_jacobian_20260601_163226, ds003490_reachability_cones_20260601_163623, ds003490_regional_3d_20260601_163235, ds003490_regional_9d_20260601_163236, ds003490_regional_mnps_jacobian_3d_20260601_163231, ds003490_regional_mnps_jacobian_9d_20260601_163233

## Headline

- Total q<=0.05 rows: subject-anchor=3, cohort-anchor=14.

## Control_vs_Parkinson_OFF

Best q-value shifts toward cohort-anchor:
- `adaptive_collapse`: min q 0.8536 -> 0.476; max |d| 0.2785 -> 0.3015.
- `global_mnps_jacobian_3d`: min q 0.9321 -> 0.6742; max |d| 0.5135 -> 0.5046.
- `global_mnps_9d`: min q 0.1316 -> 0.01349; max |d| 0.7411 -> 1.194.
- `regional_mnps_jacobian_9d`: min q 0.1462 -> 0.06297; max |d| 0.6391 -> 0.7179.
- `regional_9d`: min q 0.05397 -> 0.02699; max |d| 1.163 -> 1.163.

Largest effect-size gains toward cohort-anchor:
- `global_mnps_9d`: max |d| 0.7411 -> 1.194; min q 0.1316 -> 0.01349.
- `regional_mnps_jacobian_9d`: max |d| 0.6391 -> 0.7179; min q 0.1462 -> 0.06297.
- `global_mnps_jacobian_9d_block_jacobian`: max |d| 0.6391 -> 0.7179; min q 0.1349 -> 0.1169.
- `adaptive_collapse`: max |d| 0.2785 -> 0.3015; min q 0.8536 -> 0.476.
- `regional_9d`: max |d| 1.163 -> 1.163; min q 0.05397 -> 0.02699.

## Control_vs_Parkinson_ON

Best q-value shifts toward cohort-anchor:
- `adaptive_collapse`: min q 0.4498 -> 0.03148; max |d| 0.3939 -> 0.7454.
- `regional_mnps_jacobian_9d`: min q 0.6355 -> 0.4183; max |d| 0.5122 -> 0.5318.
- `global_mnps_jacobian_9d_block_jacobian`: min q 0.6053 -> 0.443; max |d| 0.5122 -> 0.5318.
- `global_mnps_9d`: min q 0.1754 -> 0.01349; max |d| 0.8349 -> 1.122.
- `reachability_cones`: min q 0.17 -> 0.03848; max |d| 0.8281 -> 0.9923.

Largest effect-size gains toward cohort-anchor:
- `adaptive_collapse`: max |d| 0.3939 -> 0.7454; min q 0.4498 -> 0.03148.
- `global_mnps_9d`: max |d| 0.8349 -> 1.122; min q 0.1754 -> 0.01349.
- `global_mnps_jacobian_9d`: max |d| 1.258 -> 1.478; min q 0.004748 -> 0.009495.
- `reachability_cones`: max |d| 0.8281 -> 0.9923; min q 0.17 -> 0.03848.
- `global_mnps_3d`: max |d| 0.7282 -> 0.8291; min q 0.1169 -> 0.02249.

## Parkinson_OFF_vs_ON

Best q-value shifts toward cohort-anchor:
- `global_mnps_jacobian_3d`: min q 1 -> 0.3893; max |d| 0.3487 -> 0.4737.
- `adaptive_collapse`: min q 0.7228 -> 0.4468; max |d| 0.2457 -> 0.2986.
- `reachability_cones`: min q 1 -> 0.887; max |d| 0.4385 -> 0.4385.
- `global_mnps_9d_block_jacobian`: min q 0.4378 -> 0.4078; max |d| 0.4519 -> 0.4519.
- `regional_3d`: min q 0.05397 -> 0.05397; max |d| 0.7526 -> 0.7526.

Largest effect-size gains toward cohort-anchor:
- `global_mnps_jacobian_3d`: max |d| 0.3487 -> 0.4737; min q 1 -> 0.3893.
- `adaptive_collapse`: max |d| 0.2457 -> 0.2986; min q 0.7228 -> 0.4468.
- `global_mnps_jacobian_9d`: max |d| 0.5919 -> 0.5965; min q 0.1234 -> 0.1329.
- `reachability_cones`: max |d| 0.4385 -> 0.4385; min q 1 -> 0.887.
- `regional_3d`: max |d| 0.7526 -> 0.7526; min q 0.05397 -> 0.05397.
