# Reachability Main Findings

## Scope

This note summarizes the locked `CPC 1` vs `CPC 5` reachability results for the primary `0-12 h` window and the hourly `0-1 h` through `11-12 h` bins.

Analyzed primary cohort:

- `141` patients total
- `71` later `CPC 1`
- `70` later `CPC 5`

## High-level takeaways

The new locked cohort changes the story relative to the older pilot.

- `tube_log_det_median` is **not** the main signal in the mature `CPC 1` vs `CPC 5` cohort.
- The strongest article-facing reachability effects are instead:
  - `persistence_log_eig_var_median`
  - `persistence_kappa_median`
  - `tube_d_eff_median`
  - `tube_a_operator_norm_median`
  - `tube_capture_gate_median`
- `q_ratio_h4_median` trends in the expected direction but is much weaker than the metrics above.
- The hourly structure is not just "first hour vs rest". The clearest and most sustained separation sits in the early-to-mid `1-9 h` interval.

## Recommended article-facing metric families

### 1. Capacity / dimensionality

These are strong and consistent.

- `tube_d_eff_median`
- `cone_d_eff_h1_median`
- `cone_d_eff_h2_median`
- `cone_d_eff_h3_median`
- `cone_d_eff_h4_median`
- `tube_d_eff_split_half_a_median`
- `tube_d_eff_split_half_b_median`

Interpretation:

- `CPC 1` tends to have a broader effective reachable dimensionality than `CPC 5`.
- This is one of the most stable signal families across both the aggregate `0-12 h` window and the hourly bins.

### 2. Persistence / retained reachability structure

These are also very strong and probably deserve headline status in the new article.

- `persistence_kappa_median`
- `persistence_log_eig_var_median`
- `persistence_log_det_median`

Interpretation:

- `CPC 1` tends to retain larger and more persistent reachable structure over time.
- These metrics are among the cleanest group separators in the locked cohort.

### 3. Capture / contraction

These are strong in the opposite direction and complement the capacity metrics well.

- `tube_a_operator_norm_median`
- `tube_capture_gate_median`
- `tube_kappa_median`
- `tube_log_eig_var_median`

Interpretation:

- `CPC 5` tends to show stronger contraction / tighter local capture.
- `tube_capture_gate_median` is useful because it is conceptually simple and article-readable.
- `tube_a_operator_norm_median` is statistically very strong and may be the best contraction-style companion metric.

### 4. Secondary / weaker context metrics

- `q_ratio_h4_median`
- `tube_log_det_median`

Interpretation:

- These can remain in the article as context, but they should not anchor the paper.
- `tube_log_det_median` in particular should be discussed honestly as weak in the locked cohort.

## Aggregate `0-12 h` ranking

### Strongest article-facing metrics in the full `0-12 h` window

- `tube_a_operator_norm_median`
  - `CPC 1` median: `1.039`
  - `CPC 5` median: `1.175`
  - delta: `-0.136`
  - Cohen's `d = -0.816`
  - Mann-Whitney `p = 4.83e-7`

- `persistence_kappa_median`
  - `CPC 1` median: `0.433`
  - `CPC 5` median: `0.178`
  - delta: `+0.255`
  - Cohen's `d = 0.884`
  - Mann-Whitney `p = 4.94e-7`

- `persistence_log_eig_var_median`
  - `CPC 1` median: `4.516`
  - `CPC 5` median: `2.612`
  - delta: `+1.905`
  - Cohen's `d = 0.892`
  - Mann-Whitney `p = 8.96e-7`

- `tube_d_eff_median`
  - `CPC 1` median: `1.966`
  - `CPC 5` median: `1.717`
  - delta: `+0.248`
  - Cohen's `d = 0.863`
  - Mann-Whitney `p = 2.14e-6`

- `tube_capture_gate_median`
  - `CPC 1` median: `0.339`
  - `CPC 5` median: `0.381`
  - delta: `-0.0417`
  - Cohen's `d = -0.586`
  - Mann-Whitney `p = 0.00176`

### Metrics to de-emphasize

- `q_ratio_h4_median`
  - delta: `+0.0229`
  - Cohen's `d = 0.234`
  - Mann-Whitney `p = 0.188`

- `tube_log_det_median`
  - delta: `-0.0485`
  - Cohen's `d = -0.140`
  - Mann-Whitney `p = 0.329`

## Hour-by-hour summary (`0-12 h`)

### Capacity / dimensionality

#### `tube_d_eff_median`

Pattern:

- positive in every hourly bin
- already present in `0-1 h`
- strongest and most sustained article-facing hourly signal

Most informative bins:

- `1-2 h`: delta `+0.356`, `d = 0.650`, `p = 1.04e-4`
- `3-4 h`: delta `+0.233`, `d = 0.760`, `p = 9.21e-5`
- `5-6 h`: delta `+0.292`, `d = 0.776`, `p = 1.77e-5`
- `6-7 h`: delta `+0.375`, `d = 0.799`, `p = 1.39e-5`
- `7-8 h`: delta `+0.385`, `d = 0.798`, `p = 2.22e-5`
- `8-9 h`: delta `+0.309`, `d = 0.754`, `p = 4.29e-5`

Conclusion:

- this is probably the best single "capacity" readout to build the new article around

#### `cone_d_eff_h1_median`

Pattern:

- mirrors `tube_d_eff_median`
- positive in every hourly bin
- strongest bins cluster in `1-9 h`

Conclusion:

- useful as a within-family replication of the same capacity story

### Persistence

#### `persistence_kappa_median`

Pattern:

- positive in every hourly bin
- strong from `1-2 h` onward
- especially strong around `4-9 h`

Most informative bins:

- `1-2 h`: delta `+0.229`, `d = 0.724`, `p = 3.32e-5`
- `4-5 h`: delta `+0.207`, `d = 0.778`, `p = 1.64e-5`
- `6-7 h`: delta `+0.263`, `d = 0.834`, `p = 5.76e-6`
- `7-8 h`: delta `+0.375`, `d = 0.890`, `p = 2.26e-6`
- `8-9 h`: delta `+0.310`, `d = 0.789`, `p = 2.00e-5`

Conclusion:

- one of the best metrics in the whole reachability stack
- deserves main-text status, not supplement-only status

#### `persistence_log_eig_var_median`

Pattern:

- positive in every hourly bin
- strong and very stable from `1-2 h` through `11-12 h`
- strongest around `6-8 h`

Most informative bins:

- `3-4 h`: delta `+1.748`, `d = 0.817`, `p = 1.20e-5`
- `4-5 h`: delta `+1.471`, `d = 0.822`, `p = 8.87e-6`
- `6-7 h`: delta `+2.259`, `d = 0.903`, `p = 1.51e-6`
- `7-8 h`: delta `+2.521`, `d = 0.900`, `p = 1.81e-6`

Conclusion:

- this is probably the strongest "retained reachability structure" summary in the locked cohort

### Capture / contraction

#### `tube_a_operator_norm_median`

Pattern:

- negative in every hourly bin
- strongest between `2-7 h`
- especially compelling contraction-style companion metric

Most informative bins:

- `2-3 h`: delta `-0.101`, `d = -0.656`, `p = 4.65e-6`
- `3-4 h`: delta `-0.133`, `d = -0.924`, `p = 2.97e-6`
- `4-5 h`: delta `-0.131`, `d = -0.778`, `p = 5.27e-6`
- `6-7 h`: delta `-0.108`, `d = -0.670`, `p = 2.02e-6`

Conclusion:

- this is the cleanest contraction/capture metric in the current bundle

#### `tube_capture_gate_median`

Pattern:

- negative in most early-to-mid bins
- weaker than `tube_a_operator_norm_median`, but simpler and easier to explain in prose

Most informative bins:

- `2-3 h`: delta `-0.0405`, `d = -0.575`, `p = 0.00220`
- `3-4 h`: delta `-0.0631`, `d = -0.753`, `p = 5.00e-4`
- `4-5 h`: delta `-0.0486`, `d = -0.561`, `p = 0.00438`
- `5-6 h`: delta `-0.0490`, `d = -0.551`, `p = 0.00765`
- `6-7 h`: delta `-0.0434`, `d = -0.494`, `p = 0.0137`

Conclusion:

- good candidate for the main capture-style metric in the article

### Secondary context metrics

#### `q_ratio_h4_median`

Pattern:

- mostly weak
- best bin is `3-4 h`

Best hourly bin:

- `3-4 h`: delta `+0.0305`, `d = 0.450`, `p = 0.0203`

Conclusion:

- keep as supporting context, not as a core pillar

#### `tube_log_det_median`

Pattern:

- inconsistent direction across hours
- mostly weak
- only modest hourly signal, strongest around `7-8 h`

Best hourly bin:

- `7-8 h`: delta `-0.128`, `d = -0.207`, `p = 0.0104`

Conclusion:

- do not build the new article around this metric
- if included, use it explicitly as a weaker contextual metric that did not scale with the locked cohort

## Recommended article build

### Best central story

The new article should be built around this reachability logic:

1. `CPC 1` shows broader effective reachable dimensionality.
2. `CPC 1` shows stronger persistence / retained reachability structure.
3. `CPC 5` shows stronger contraction / capture.
4. These effects are visible early, but most clearly across the early-to-mid `1-9 h` period rather than as a single first-hour phenomenon.

### Recommended main metrics

Primary article-facing set:

- `tube_d_eff_median`
- `persistence_kappa_median`
- `persistence_log_eig_var_median`
- `tube_a_operator_norm_median`
- `tube_capture_gate_median`

Secondary context:

- `q_ratio_h4_median`
- `tube_log_det_median`

### Recommendation for prose

Avoid saying:

- that `tube_log_det_median` is the main result
- that the strongest effect is in the first hour
- that the result is mainly about a single endpoint

Prefer saying:

- the reachability family separates `CPC 1` from `CPC 5`
- the strongest effects lie in capacity, persistence, and contraction/capture summaries
- the hourly structure suggests a coherent early-to-mid `1-9 h` divergence pattern
