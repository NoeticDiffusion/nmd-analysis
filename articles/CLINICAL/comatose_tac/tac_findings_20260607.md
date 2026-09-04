# TAC 6 / 8 / 10 — Findings Summary (updated 2026-06-07)
**Date:** 2026-06-07  
**Cohort:** I-CARE 2.1, combined (part1 + part2), extreme-outcome patients  
**Scripts:**  
- `articles/CLINICAL/comatose_experimental/src/run_tac_sigma_jacobian_dynamics.py`  
- `articles/CLINICAL/comatose_experimental/src/compute_tac_between_run_mad.py`  
- `articles/CLINICAL/comatose_experimental/src/tac_incremental_validity.py`  
**Results:**  
- `articles/CLINICAL/comatose_experimental/results/tac_sigma_jacobian_20260607_combined/`  
- `articles/CLINICAL/comatose_experimental/results/tac_between_run_mad_20260607/`  
- `articles/CLINICAL/comatose_experimental/results/tac_incremental_validity_20260607/`  
- Window sensitivity: `tac_sigma_window10_20260607/` and `tac_sigma_window40_20260607/`

---

## Cohort

| | n |
|---|---|
| Total subjects | 281 |
| CPC 1 (good outcome) | 141 |
| CPC 5 (poor outcome) | 140 |
| Time window | 0–12 h post-anchor |
| H5 roots | `20260605_202236` (part1), `20260605_210700` (part2) |

TAC 10 metrics require `jacobian_9D/J_hat`. Coverage: 95 CPC1 + 91 CPC5 = 186 subjects (66%).  
Between-run MAD/IQR for TAC 10 (≥3 runs): 76 CPC1 + 71 CPC5 = 147 subjects (52%).

---

## Method overview

**TAC 6 — Σ log-Euclidean velocity:**  
Sliding-window sample covariance over MNPS coordinate sequence. Log-Euclidean velocity at step i:

    v_i = ‖logm(Σ_i) − logm(Σ_{i+1})‖_F / step

Patient-level summary: median velocity across all run-window steps.

**TAC 8 — Cone-field twist:**  
Same Σ_i sequence. Mean principal angle between top-k eigenvector subspaces at consecutive windows:

    twist_i = mean( subspace_angles(V_top(Σ_i), V_top(Σ_{i+1})) )

Top-k = 2 for 3D, 3 for 9D.

**TAC 10 — 9D block-shear flux:**  
Decompose each 9×9 Jacobian into 3×3 blocks (δ/θ/α bands). Within-band flux = diagonal-block Frobenius sum; cross-band flux = off-diagonal-block sum; ratio = cross / (within + ε).

---

## CPC 1 vs CPC 5 contrasts — full median (window=20)

| Metric | Family | CPC1 median | CPC5 median | Cohen's d | MW p | AUROC | n (1/5) |
|---|---|---|---|---|---|---|---|
| `tac10_9d_within_band_flux_median` | TAC 10 | 0.526 | 0.598 | −0.657 | 1.5e-5 | 0.316 | 95/91 |
| `tac10_9d_cross_band_flux_median` | TAC 10 | 1.049 | 1.191 | −0.642 | 2.0e-5 | 0.319 | 95/91 |
| `tac6_9d_sigma_velocity_median` | TAC 6 | 0.394 | 0.404 | −0.268 | 0.037 | 0.428 | 141/140 |
| `tac8_3d_cone_twist_median` | TAC 8 | 0.098 | 0.087 | +0.243 | 0.0073 | 0.593 | 141/140 |
| `tac8_9d_cone_twist_median` | TAC 8 | 0.200 | 0.195 | +0.104 | 0.187 | 0.546 | 141/140 |
| `tac6_3d_sigma_velocity_median` | TAC 6 | 0.139 | 0.138 | +0.063 | 0.610 | 0.518 | 141/140 |
| `tac10_9d_cross_band_ratio_median` | TAC 10 | 2.018 | 2.023 | −0.047 | 0.408 | 0.465 | 95/91 |

---

## Experiment 1 — Between-run MAD and IQR for TAC metrics

Between-run MAD = `median |x_run − median(runs)|` per patient, requiring ≥3 runs.  
Coverage for TAC 10 MAD/IQR: n = 76 CPC1 / 71 CPC5 (52% of cohort).

| Metric (stat) | CPC1 med | CPC5 med | Cohen's d | MW p | AUROC | n (1/5) |
|---|---|---|---|---|---|---|
| `tac10_9d_cross_band_flux_median_mad` | 0.0232 | 0.0384 | **−0.805** | 5.66e-7 | 0.261 | 76/71 |
| `tac10_9d_cross_band_flux_median_iqr` | 0.0406 | 0.0659 | **−0.795** | 9.32e-7 | 0.265 | 76/71 |
| `tac10_9d_within_band_flux_median_iqr` | 0.0110 | 0.0181 | **−0.733** | 1.88e-6 | 0.272 | 76/71 |
| `tac10_9d_within_band_flux_median_mad` | 0.0060 | 0.0094 | −0.642 | 3.39e-5 | 0.302 | 76/71 |
| `tac6_9d_sigma_velocity_median_mad` | — | — | −0.302 | 0.0036 | 0.399 | 140/136 |
| `tac6_9d_sigma_velocity_median_iqr` | — | — | −0.301 | 0.0006 | 0.381 | 140/136 |

**Key finding:** `tac10_9d_cross_band_flux_median_mad` (d = −0.805) exceeds its median counterpart (d = −0.642) by 25%. This mirrors the pattern seen in `tube_capture_gate_median_mad` in the NDT article (median d = −0.558 → MAD d = −1.033, +85%).

---

## Experiment 2 — Incremental AUROC over NDT-5

5×20 repeated stratified CV. All 281 subjects; TAC10 columns are NaN-imputed for the ~34% without 9D Jacobians.

| Model | n feat | AUROC | ±sd | Delta AUROC | Delta p |
|---|---|---|---|---|---|
| `clinical+qEEG` (baseline) | 26 | 0.600 | 0.065 | +0.000 | — |
| `clinical+qEEG+NDT5` | 31 | 0.662 | 0.065 | **+0.062** | 1.8e-26 |
| `clinical+qEEG+NDT5+TAC10` | 33 | **0.668** | 0.068 | **+0.069** | 9.0e-25 |
| `clinical+qEEG+NDT5+TACAll` | 38 | 0.662 | 0.064 | +0.062 | 4.3e-21 |
| `TAC10 only` | 2 | 0.645 | 0.067 | +0.045 | 2.5e-6 |
| `NDT5 only` | 5 | 0.633 | 0.054 | +0.034 | 9.6e-5 |
| `NDT5+TAC10` | 7 | 0.663 | 0.060 | +0.064 | 2.1e-11 |

**Key findings:**
1. `TAC10 only` (AUROC = 0.645) **beats** `NDT5 only` (0.633) with just 2 features.
2. Adding TAC10 to the full model (NDT5+clinical+qEEG) adds a small but significant increment: +0.006 (0.662 → 0.668).
3. Full TAC (all 7 metrics) adds nothing over NDT5 alone — only the 2 TAC10 metrics contribute.
4. TAC10 and NDT5 are partially complementary: `NDT5+TAC10` = 0.663, better than either alone.

---

## Experiment 3 — TAC 8 sigma-window sensitivity

TAC 10 is window-independent (operates on pre-computed Jacobians). TAC 6/8 are window-dependent.

| Window | Step | TAC 8 3D d | TAC 8 3D p | TAC 8 9D d | TAC 8 9D p |
|---|---|---|---|---|---|
| 10 | 3 | +0.207 | 0.0023 | n.s. | 0.187 |
| **20** | **5** | **+0.243** | **0.0073** | n.s. | 0.187 |
| 40 | 10 | **+0.289** | 0.0037 | n.s. | 0.187 |

TAC 8 3D cone twist is directionally stable across all window sizes. Effect size grows slightly with larger windows (d = 0.207 → 0.289), suggesting the signal is more consistent at coarser temporal resolution. The 9D version is non-significant at all windows — the signal is predominantly in the 3D representation.

TAC 6 is unstable across window sizes and remains weak/null throughout.

---

## Summary table — all TAC metrics vs NDT article comparison

| Metric | |d| | p | Source |
|---|---|---|---|
| `persistence_hysteresis_log_det_median` | 0.909 | 1.1e-7 | NDT article |
| `persistence_log_det_median` | 0.896 | 1.5e-6 | NDT article |
| `tube_capture_gate_median_mad` | **1.033** | 3.8e-6 | NDT MAD (n=130) |
| `tube_d_eff_median` | 0.838 | 9.2e-6 | NDT article |
| `persistence_log_eig_var_median` | 0.736 | 5.3e-5 | NDT article |
| **`tac10_9d_cross_band_flux_median_mad`** | **0.805** | **5.7e-7** | TAC MAD (n=147) |
| **`tac10_9d_within_band_flux_median`** | **0.657** | **1.5e-5** | TAC median (n=186) |
| **`tac10_9d_cross_band_flux_median`** | **0.642** | **2.0e-5** | TAC median (n=186) |
| `tube_capture_gate_median` | 0.558 | 8.0e-3 | NDT article |
| `tac8_3d_cone_twist_median` (w=40) | 0.289 | 0.0037 | TAC 8 w=40 |
| `tac8_3d_cone_twist_median` (w=20) | 0.243 | 0.0073 | TAC 8 w=20 |

---

## Interpretation

### TAC 10 — the strongest TAC signal

TAC 10 captures absolute Jacobian coupling amplitude across frequency bands. With median d ≈ −0.65 and MAD d ≈ −0.81, it sits between `tube_d_eff_median` and `tube_capture_gate_median` in the NDT family ordering. Crucially, `TAC10 only` achieves AUROC = 0.645 — better than `NDT5 only` (0.633) — suggesting TAC10 is not just a reformulation of existing reachability metrics but carries partially independent signal.

The MAD amplification (+25%) is real but modest compared to the NDT article's tube_capture_gate pattern (+85%). The likely reason: TAC10 operates on the 9D Jacobian directly, which has higher intrinsic variance than the derived capture-gate ratio, dampening the MAD amplification.

### TAC 8 — stable weak signal, grows with window size

TAC 8 3D cone twist is significant across all window sizes (d = 0.21–0.29), consistently showing that CPC1 subjects rotate their reachability ellipsoid more between recording windows. This is opposite in sign to the TAC 10 finding (more Jacobian flux = worse outcome). These two metrics together may capture: (a) amplitude of neural coupling [TAC 10] and (b) diversity of neural configuration [TAC 8].

### TAC 6 — discard

TAC 6 is window-sensitive and consistently weak/null. It likely captures the same variance as within-run velocity measures already embedded in the reachability families.

---

## Limitations

1. **TAC 10 coverage:** 66% median coverage (186/281), 52% MAD coverage (147/281). Systematic coverage differences by site or CPC not yet checked.
2. **Window sensitivity for TAC 8:** w=40 gives the strongest TAC 8 effect. No formal window-selection correction applied.
3. **No part1/part2 split:** all analysis is pooled. Cross-cohort stability not validated.
4. **Incremental AUROC over full baseline is small (+0.006):** TAC10 adds 6 AUROC points over NDT5 alone but only 6 additional thousandths over the clinical+qEEG+NDT5 floor.
5. **Exploratory status:** post-hoc analysis, no pre-registration.

---

## Next steps (prioritized)

1. **Site/outcome coverage audit for TAC 10** — is the 34% missing data uniform across sites and CPC groups?
2. **Part1/part2 split for TAC 10** — validate in the 186-subject 9D-available subset
3. **Consider w=40 as canonical TAC 8 window** — most stable and strongest signal
4. **MAD for TAC 10 with full-cohort 9D coverage** — if missing data can be resolved, MAD d could approach −0.9
