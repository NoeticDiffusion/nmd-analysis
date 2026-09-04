# Persistence bounds fix – comparison report

**Dataset**: combined ComBat-corrected primary 0-12 h, N=277 subjects, CPC 1 vs CPC 5
**Baseline**: `outcome_contrasts_20260602_combined_combat_corrected_primary12h_cpc15`
**Fixed run**: `outcome_contrasts_20260605_clamp_primary12h_cpc15`
  - Flags: `--rank-effect-sizes --clamp-persistence-bounds`
  - Values clamped: d_eff ≤ 3.0, log_det/log_eig_var ≤ 50.0, kappa ≤ 1e6

## Key finding: persistence collapse is partially resolved

| Metric | Cohen's d orig | Cohen's d clamped | Δd | Cohen's d_rank | Cliff's δ | CLES |
|--------|---------------|-------------------|-----|---------------|-----------|------|
| `persistence_tau_log_det_median` | 0.257 | 0.257 | +0.000 | **0.345** | 0.197 | 0.599 |
| `persistence_log_det_median` | 0.122 | 0.248 | +0.126 | **0.631** | 0.348 | 0.674 |
| `persistence_log_eig_var_median` | 0.122 | 0.247 | +0.124 | **0.524** | 0.294 | 0.647 |
| `persistence_kappa_median` | 0.127 | 0.169 | +0.041 | **0.297** | 0.170 | 0.585 |
| `persistence_d_eff_median` | 0.122 | 0.139 | +0.017 | **0.105** | 0.061 | 0.530 |
| `persistence_tau_d_eff_median` | 0.112 | 0.112 | +0.000 | **0.110** | 0.064 | 0.532 |
| `persistence_tau_kappa_median` | -0.003 | -0.003 | +0.000 | **0.011** | 0.006 | 0.503 |
| `persistence_tau_log_eig_var_median` | -0.056 | -0.056 | +0.000 | **0.101** | 0.059 | 0.529 |
| `persistence_hysteresis_kappa_median` | -0.140 | -0.140 | +0.000 | **-0.438** | -0.248 | 0.376 |
| `persistence_hysteresis_d_eff_median` | -0.175 | -0.175 | +0.000 | **-0.120** | -0.069 | 0.465 |
| `persistence_hysteresis_log_eig_var_median` | -0.484 | -0.484 | +0.000 | **-0.520** | -0.292 | 0.354 |
| `persistence_hysteresis_log_det_median` | -0.538 | -0.538 | +0.000 | **-0.619** | -0.343 | 0.329 |

## Interpretation

- **The three-way collapse is broken**: `persistence_log_det`, `persistence_log_eig_var`, and
  `persistence_d_eff` previously all reported Cohen's d = 0.122 (pooled SD inflated by
  extreme outliers). After clamping, parametric d spreads to 0.139–0.248.

- **Rank-based d_rank reveals stronger true signal**: `persistence_log_det_median` has
  d_rank = 0.63, comparable to the reachability family. This is the honest rank-based
  estimate robust to remaining heavy tails.

- **Non-persistence metrics are completely unaffected** (max Δd = 0.000000).

- **Cliff's δ is unchanged by clamping** for most metrics – it is already rank-based and
  hence insensitive to the extreme values. The few small changes are from `d_eff` where
  tied-rank resolution changed slightly.

- **Remaining scipy warnings** ('catastrophic cancellation') in Welch's t-test indicate
  that the parametric cohens_d is *still* unreliable for some persistence metrics even
  after clamping. Use cohens_d_rank and cliffs_delta as the primary effect-size estimates
  for the persistence family.

**N metrics changed**: 4 / 163  
**Max Δd for non-persistence**: 0.000000
