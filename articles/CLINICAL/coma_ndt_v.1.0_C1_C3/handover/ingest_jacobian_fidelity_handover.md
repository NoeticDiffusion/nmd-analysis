# 002 - 2026-09-11 - ingest: I-CARE first MNPS-v3 dump — Jacobian gate plus other teething issues

## Summary

The I-CARE v2 CPC1 vs CPC5 analysis (`coma_ndt_v.1.0`, bundle `neuralmanifolddynamics_physionet_icare_2_1_20260904_225047`) is one of the first full I-CARE runs on MNPS v3 / MNDM 3.0.0 (`schema_version=mnps_tensor_spec_v2_4`). Overlay comment: *eligibility / refusal test, not a translation-qualified production analysis*. Family A (diffusion geometry) is usable. Family B (MNJ-v3 α/ω/`F_reactive`) is not, because `/jacobian/derived_metrics/v1` is marked `computed` on near-null local fits.

This note is the ingest packet. **Priority 1 remains the Jacobian fidelity gate.** The rest are first-v3 teething issues found on the same dump: some should be fixed before a production re-export, some are overlay/design choices, some are contract-correct `not_testable`.

Source: `data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260904_225047` (161 subjects, 3484 H5). Analysis outputs: `articles/CLINICAL/coma_ndt_v.1.0/results/full/`. Overlay: `config_ingest_physionet_i-care_2_1_dynamical_families.yaml`.

---

## Priority 1 — blocking for Family B

### 1. Local Jacobian fit does not beat baseline

On a random sample of 40 H5 files:

| `diagnostics.rel_mse_baseline_median` | value |
|---|---|
| min | 0.90 |
| median | 0.96 |
| max | 0.98 |
| fraction > 0.90 | 40/40 |

Worked example, `sub-0284` run-001 acq-004:

- `/jacobian/diagnostics` attrs: `rel_mse_baseline_median=0.973`, `local_fit_mse_median≈local_fit_mse_baseline_median≈0.010`, `j_dot_dt=4.0`
- stored `spectral_abscissa` equals `max Re eig(J_hat)` (median |diff| 7e-10) — the derived metric is algebraically correct
- 91% of windows have α>0, 99% have ω>0, `stable_reactive_fraction=0.081`
- `/jacobian/derived_metrics/v1/computation_status=computed`, `measurement_validity=not_assessed`, `claim_status=no_biological_claim`

Overlay comment currently says *“jacobian metrics: computed when J_hat exists”*. That is too weak. Downstream `F_reactive = P(α<0<ω)` is then a rare occupancy in *both* CPC groups (~0.10), and every CPC5 patient is majority-`unstable`. That is not a test of the NDT stable-reactive window.

FTR on the same file still reports `operator_semantics=continuous_time_generator`, `propagator_mode=time_ordered_expm`, `nominal_dt_sec=4.0`, `computation_status=computed`. Peak gain grows with horizon (`g_max` h1=1.42, h4=2.83) *because* α>0. That is consistent with an expanding generator, not evidence that the generator is identified.

### 2. Stochastic reachability overflow is the same operator

Full-bundle inventory:

| `/stochastic_reachability/v1/primary/computation_status` | n |
|---|---:|
| `invalid` | 2906 |
| `computed` | 428 |
| `unavailable` | 150 |

Typical `failure_reason=reachability_numerical_overflow`. Provenance: `propagator_source=gate_e_crossfit_expm_J_dt`, `q_source=transition_residual_covariance_proxy`.

If Φ = expm(J Δt) and α(J)>0 on most windows, the discrete recursion \(W \leftarrow \Phi W \Phi^\top + Q\) is expected to overflow. The 83% invalid rate is not an independent numerical accident; it is the expanding near-null `J_hat` pushed through `expm`. Certificates already say `capability/spread=gated` and `capability/diffusion=overlay_only`. The family should not be default-on for this overlay until the Jacobian gate exists.

Article-local code already bypasses this group and recomputes cones from `coords_3d_subject_anchored` via `nmd_analysis.reachability_core`.

### 3. Derived-metrics provenance is thinner than FTR

`/jacobian/derived_metrics/v1/provenance` currently carries: `dimension`, `metric_norm`, coordinate contract/layer, `stability_zero_tolerance=1e-8`, `reactivity_zero_tolerance=1e-8`.

It does **not** carry, though FTR on the same file does:

- `operator_semantics` (FTR: `continuous_time_generator`)
- `nominal_dt_sec` / time unit of α, ω (FTR: 4.0 s; Jacobian diagnostics have `j_dot_dt=4.0` but derived-metrics do not inherit it)
- any local-fit residual / `rel_mse_baseline` summary
- a fidelity class (`pass`/`warn`/`fail`) before `stable_reactive_flag` is written

α is therefore a chart number without a declared unit or operator class.

---

## Priority 2 — should fix before a production I-CARE re-export

### 4. WFDB clocks with hour ≥ 24 are rejected; CPC5 is hit harder

| `time_reference/run/status` | n |
|---|---:|
| `ok` | 3328 |
| `missing_or_invalid_start_end` | 156 |

Those 156 runs have **no finite** `window_start_from_anchor_sec`, so analysis left them `unassigned` rather than imputing. `window_start_from_run_sec` **is** finite on sampled files. This is not missing EEG; it is a parser refusal.

Mechanism (sampled headers):

| `run_start_clock_raw` | `header_path` (example) |
|---|---|
| `100:00:00` | `0332/0332_081_100_EEG.hea` |
| `101:00:00` | `0460/0460_091_101_EEG.hea` |
| `150:00:00` | `0522/0522_026_150_EEG.hea` |
| `206:00:00` | `0522/0522_084_206_EEG.hea` |

`parse_errors = [invalid_start_time, invalid_end_time]`. The hour field tracks the I-CARE `acq` / recording-hour index (often hours since ROSC), not a 24-hour wall clock. The WFDB parser treats HH≥24 as invalid, writes `run_duration_sec=nan`, and drops anchor-relative window times.

CPC split of the 156 runs: **25 CPC1 vs 131 CPC5**, hospitals A/E/D, 5 subjects. Those clocks are late (hour 100–206), so the primary **0–12 h** contrast still has n=71/70. What is lost is longitudinal binning: the recordings would have been `72h_plus` (or similar), not `0_12h`. CPC5 long-stay files are dropped from timed analyses disproportionately.

Requested ingest change: when HH≥24, treat the header time as elapsed hours (I-CARE recording-hour / hours-from-ROSC), not as a civil clock. Keep `window_start_from_run_sec`. Do not leave `window_start_from_anchor_sec` all-NaN if `subject_anchor_start_sec` and elapsed run time are known.

### 5. Empty run directories are silent

17 grouped run directories exist with no H5 (inventory `empty_dirs`). Overlay `grouping_collisions.count=0` and there is no per-dir `run_errors.json`. First-v3 grouping leftover. Please emit an explicit skip/error record so analysis does not have to rediscover empty stems.

### 6. `/provenance/signal_support_provenance` is absent

Guide documents `/provenance/signal_support_provenance/*` (`mndm.signal_support_export.v1`, `temporal_support_status`, source-quality intervals). Sampled files in this dump do not have the group. Continuity-sensitive families (diffusion increments, Jacobian local fits, FTR) therefore have no certified temporal-support status beyond epoch bounds. Analysis-side readers fail-close when the group is missing; ingest should write at least `temporal_support_status=unknown` rather than omitting the group.

### 7. FTR `validation_level=model_derived` only — F1 shuffle/frozen was not run

Every sampled FTR file is `validation_level=model_derived`. Overlay sets that explicitly. Hypothesis F1 (ordered Φ vs shuffled/frozen) is **not** licensed by `computed`. After the Jacobian gate, do not promote FTR peak-gain / horizon growth to an empirical NDT claim on this overlay until an ordered-vs-null check exists. `model_derived` is honest; it must stay visible and not be upgraded by analysis.

### 8. 9D Jacobian `geometry_contract_status=adjusted` is common, and `e_m` is still a fallback

- `geometry_contract_status=adjusted` on **1130/3484** files (~33% CPC1, ~35% CPC5). Sampled files: 3D Jacobian `ok`, `epochs_dropped=0`; adjustment is 9D Jacobian windows (`jacobian_9d/status=adjusted`, condition-number invalid centers). 3D Family A is not implied broken.
- 9D derived-metrics `unavailable` on **133** files (78 CPC1, 51 CPC5).
- `/support_signature/v1`: `coordinates/e_m/source=fallback`, `fallback_feature=eeg_highfreq_power_30_45`, `semantic_equivalence=false`. The old 9D `e_m` workaround is still in the signature even if `e_m` is now finite. Do not treat 9D MNJ as a second independent Family B until `e_m` is a real axis or the fallback is dropped from 9D Jacobian support.

### 9. EEG artifact / `qc_ok_eeg` path looks unused

Sampled `/qc/windows/qc_ok_eeg` is identically 1. Per-run `qc_summary.json` has `artifacts.methods: []`. Manifest lists `preprocess_ica` among unused methods. `features_snapshot.json` qEEG band powers have means orders of magnitude above medians (e.g. `eeg_delta` mean 835 vs median 0.87) — consistent with unclipped outliers if a conventional-EEG pack is later enabled. Not blocking for 3D diffusion on robust-z MNPS, but a production overlay should not advertise `qc_ok_eeg=1` as having passed an artifact detector.

---

## Priority 3 — overlay / design choices (not crashes; document or enable deliberately)

### 10. ComBat disabled; hospital × CPC is unbalanced

`normalization_report.json`: ComBat `enabled=false`, `status=disabled`. Subject counts:

| hospital | CPC1 | CPC5 |
|---|---:|---:|
| A | 35 | 26 |
| B | 13 | 14 |
| D | 13 | 8 |
| E | **2** | **15** |
| F | 8 | 7 |

Site E is almost a CPC5 hospital. The previous coma manuscript consumed ComBat-harmonized exports. This v3 dump does not. Between-subject CPC contrasts on unharmonized features can pick up site. Family A here is computed on **subject-anchored** charts, which limits but does not remove site effects on the *geometry summaries*. If ingest re-enables ComBat, keep a no-ComBat twin export.

### 11. No cohort-anchored coordinates

Overlay forces `coordinate_layer: subject_anchored`. Manifest: `coords_*_cohort_anchored` absent on all sampled files. Guide: subject-anchored is for within-subject dynamics; cohort-anchored is the contract intended for clinical group contrasts. Using within-subject charts for a CPC contrast is a **design limitation**, not a missing file. A production clinical overlay should either emit cohort-anchored coords or keep the limitation in the certificate (`direct_between_subject_inference=forbidden` is already set and is correct).

### 12. No `/extensions/conventional_eeg`

`conventional_eeg` is a top-level overlay key and exists in `features_raw` / `features_snapshot.json`, but `/extensions/conventional_eeg` is not written. The previous coma article used qEEG for incremental validity (NDT geometry vs conventional EEG). Enabling the pack is optional; if enabled, gate on artifact QC first (item 9) because band-power outliers are already visible in the snapshot.

### 13. `min_axis_coverage` is a policy floor, not a measurement

`/coverage/min_axis_coverage = 0.30` on sampled files while `/coverage/axis_fraction` is identically 1. Easy to misread as “this recording only covered 30% of axes”. Rename or document as a threshold attribute.

### 14. Sedation / WLST still absent

`qc_summary` sedation note: medication/WLST are not in this export. Family B confound audit cannot be done ingest-side without new clinical fields. Not an MNPS-v3 regression; still a blocking *scientific* gap for promoting Family B even after the Jacobian gate.

---

## By design — do not “fix” by inventing data

### Diffusion alignment / `E_perp`

`/dynamical_families/diffusion/v1`: `a_hat` / `d_diff` / `D_total` are `computed` (3419/3484). Recomputed `d_eff^(a)` matches stored `d_diff` to ~4.6e-8. This family is usable.

- `A_bD_computation_status=not_testable`, `R_b_over_a_computation_status=not_testable`
- `drift_alignment_failure_reason=independent_drift_not_supplied`
- `drift_source=not_supplied`

Contract-correct. Do not add a synthetic drift just to populate `A_bD`. Article-local `E_perp` uses `a_hat` + `/mnps_3d_dot` as a **candidate** only. `mnps_3d_dot` is not an Itô drift.

### Diffusion `not_testable` (58 files)

Sampled reason: `materially_irregular_increment_timestep`. Plus 7 `insufficient_support`. Fail-closed and correct.

### Destination / committor and resilience

`not_testable` on every file (empty A/B, no perturbation protocol). Overlay expected write states already say this. Grain on diffusion: `native=window`, `biological_unit=subject`, `direct_between_subject_inference=forbidden`. Analysis already aggregates to subject. Do not promote window rows to between-subject claims.

---

## Requested ingest changes

Priority 1 — Jacobian derived-metrics validity gate:

1. Classify local-fit fidelity from existing diagnostics (`rel_mse_baseline_median` and/or window `rel_mse_baseline_windows`) **before** writing `computation_status=computed` on `/jacobian/derived_metrics/v1`.
2. Suggested fail-closed rule for this chart: if recording `rel_mse_baseline_median` ≥ 0.9 (or a frozen threshold chosen on a non-I-CARE qualification set), set `computation_status=invalid` or `insufficient_support`, `failure_reason=local_linear_fit_not_better_than_baseline`, and either omit `stable_reactive_flag` / regime summaries or mark them `not_testable`.
3. Copy `rel_mse_baseline_median` into `derived_metrics/v1/summary/` so analysis repos do not have to reach into diagnostics attrs.
4. Copy FTR-style `operator_semantics` and `nominal_dt_sec` (or an explicit `abscissa_units=1/second`) into `derived_metrics/v1/provenance`.
5. Change the overlay comment from “computed when J_hat exists” to “computed when J_hat exists **and** local-fit fidelity passes”.

Priority 2 — stochastic reachability and first-v3 holes:

6. If the propagator is `expm(J dt)` and α>0 or `rel_mse` fails the gate above, do not attempt the W-recursion until overflow. Prefer `not_testable`/`invalid` with a reason that names the expanding/unidentified generator, or disable the family by default on EEG I-CARE overlays until the Jacobian gate exists.
7. Keep `reachability_numerical_overflow`, but it should become rare after (1)–(2), not the modal status (2906/3484).
8. WFDB time-reference: interpret HH≥24 as I-CARE elapsed/recording hour, populate `window_start_from_anchor_sec` from elapsed time. 156 files, CPC5-skewed, currently unassigned.
9. Write skip/error records for the 17 empty grouped run dirs.
10. Emit `/provenance/signal_support_provenance` (at least `unknown`) on every new write.
11. Do not silently treat 9D MNJ as available while `e_m` is a non-equivalent fallback; either restore a real `e_m` or mark 9D Jacobian `insufficient_support` / `capability/mnj_9d=conditional` in a way analysis cannot miss.
12. Do not report `qc_ok_eeg=1` unless an artifact method actually ran; empty `artifacts.methods` should yield `not_assessed`.

Priority 3 — optional / overlay policy:

13. Decide ComBat and cohort-anchored coords explicitly for the clinical overlay (current: both off).
14. Conventional EEG pack is optional; if enabled, gate on artifact QC because snapshot band powers are outlier-heavy.
15. Rename or document `min_axis_coverage` as a policy threshold.
16. Do not add a synthetic drift just to populate `A_bD`.
17. Leave FTR at `model_derived` until an ordered-vs-null (F1) check exists; do not let analysis upgrade it.

## What analysis already did / will not do

- Family A (`d_eff^(a)`, `tilde H_a`, `Tr(a)`) uses stored diffusion `a_hat` and is internally consistent. No ingest change required for H1/H2/H4 on this dump.
- Family B `F_reactive` was computed exactly from stored α/ω. The opposite-to-hypothesis CPC contrast should **not** be read as a biological rejection until ingest gates `J_hat`.
- Article-local cone recompute bypasses `/stochastic_reachability/v1`.
- `E_perp` was computed from `a_hat` + `mnps_3d_dot` as a candidate only.
- Timed bins use `window_start_from_anchor_sec` only; the 156 invalid-clock runs stay `unassigned`.
- Window-level rows are not used as between-subject claims (`grain` is respected).

## Pointers

- Bundle: `neuralmanifolddynamics_physionet_icare_2_1_20260904_225047`
- Overlay used at ingest: `config_ingest_physionet_i-care_2_1_dynamical_families.yaml` (in the dump root)
- Example file: `sub-0284_..._run-001_acq-004.h5`
- Invalid-clock example: `sub-0332_..._run-081_acq-100.h5` (`run_start_clock_raw=100:00:00`)
- Analysis QC: `articles/CLINICAL/coma_ndt_v.1.0/results/full/qc_summary.json`
- Analysis handover: `articles/CLINICAL/coma_ndt_v.1.0/handover/icare_v2_pipeline_handover.md`
- Guide already says derived-metrics are “mathematical provenance on `J_hat`, not S3-licensed empirical NDT α/ω”. The missing piece is a **fit-quality gate** so `computed` does not mean “J exists”, it means “J is identified enough to define α/ω regimes”.

## Next steps (ingest repo)

1. Reproduce `rel_mse_baseline_median` vs `computation_status` on this I-CARE dump.
2. Freeze a fidelity threshold on a *non-clinical* qualification set, then apply it to Jacobian derived-metrics and to the reachability enable path.
3. Fix HH≥24 WFDB elapsed-time parsing; write empty-dir errors and `signal_support_provenance`.
4. Re-export or patch certificates; analysis can then rerun Family B without changing the α/ω algebra.
