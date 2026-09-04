# 9D Jacobian Result Ledger

This ledger freezes the article-facing metric hierarchy against the formal `20260525_cpc15_primary12h` bundle.

## Frozen hierarchy

### `primary_lead`

- `spectral_radius_median`: pooled rank `1`, pooled `d = -0.620`, part1 `d = -0.632`, part2 `d = -0.617`

### `secondary_replicated`

- `anisotropy_abs_eig_median`: pooled rank `2`, pooled `d = -0.337`, part1 `d = -0.348`, part2 `d = -0.641`

### `pooled_promoted`

- `mdr_median`: pooled rank `3`, pooled `d = -0.287`, part1 `d = -0.223`, part2 `d = -0.397`
- `rotational_power_mean`: pooled rank `4`, pooled `d = -0.285`, part1 `d = -0.300`, part2 `d = -0.388`
- `rotational_power_median`: pooled rank `5`, pooled `d = -0.260`, part1 `d = -0.282`, part2 `d = -0.235`

### `legacy_supportive`

- `a_operator_norm_median`: pooled rank `8`, pooled `d = -0.227`, part1 `d = -0.276`, part2 `d = -0.500`
- `frobenius_norm_median`: pooled rank `7`, pooled `d = -0.230`, part1 `d = -0.280`, part2 `d = -0.464`
- `rotation_norm_median`: pooled rank `6`, pooled `d = -0.232`, part1 `d = -0.282`, part2 `d = -0.451`

## Interpretation

- `spectral_radius_median` remains the cleanest primary lead because it is the strongest pooled effect and stays strong in both cohorts.
- `anisotropy_abs_eig_median` remains the best replicated secondary signal, but is no longer the only non-legacy metric worth foregrounding.
- `mdr_median`, `rotational_power_mean`, and `rotational_power_median` are now frozen as pooled-promoted signals that must be stress-tested in robustness and prediction analyses.
- `a_operator_norm_median`, `frobenius_norm_median`, and `rotation_norm_median` are retained as legacy replication-support metrics rather than as the paper's main pooled hierarchy.
