# 001 - 2026-09-11 - I-CARE 2.1 bundle 20260904_225047: CPC1 vs CPC5 Family A/B pipeline

## Summary

Built and ran an article-local I-CARE v2 pipeline under `articles/CLINICAL/coma_ndt_v.1.0/src` that reads the single available processed bundle `data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260904_225047` (161 subjects, 3484 H5 files). The pipeline extracts Family A diffusion-geometry metrics (H1–H4) and Family B MNJ-v3 regime fractions from fields already stored in the H5 files, recomputes reachability cones at h=1/2/4 from `coords_3d_subject_anchored`, and compares CPC 1 vs CPC 5 in the 0–12 h EEG-anchor window.

Status: **exploratory, pending part2**. No held-out confirmatory cohort is available in this dump. Do not treat the contrast table as a frozen manuscript result.

Smoke test (5 CPC1 + 5 CPC5, 315 runs) was run first into `results/smoke/`. After a diffusion `bytes` status-field bug was fixed, the chain ran cleanly. The full run wrote `results/full/`.

## Run Timeline

| Step | Smoke (10 subjects, 315 H5) | Full (161 subjects, 3484 H5) |
|---|---:|---:|
| inventory | 31.9 s | 253.5 s |
| timebin | 1.0 s | 1.2 s |
| qc inventory | 0.9 s | 1.1 s |
| diffusion | 9.0 s (after bugfix) | 68.2 s |
| mnj-v3 | 6.9 s | 41.4 s |
| reachability recompute | 170.4 s | 1284.5 s |
| merge / qc / contrasts / figures | ~6 s | ~6 s |

Commands (repo venv):

```text
.venv\Scripts\python.exe articles\CLINICAL\coma_ndt_v.1.0\src\icare_v2_run_pipeline.py --smoke --workers 6
.venv\Scripts\python.exe articles\CLINICAL\coma_ndt_v.1.0\src\icare_v2_run_pipeline.py --workers 8
```

Config: `config/icare_v2_analysis_config.yaml`, smoke allowlist `config/icare_v2_smoke_subjects.yaml`.

## Feature Extraction Results

### Coverage (full bundle)

- 161 subjects (CPC1=71, CPC2=10, CPC3=7, CPC4=3, CPC5=70), 3484 readable H5 files, 17 empty run directories.
- Primary window `0_12h`: 1980 runs; all 161 subjects have at least one primary-window run.
- CPC1 vs CPC5 primary contrast n = **71 / 70**.
- 156 runs unassigned (`time_reference_status=missing_or_invalid_start_end`); they are excluded from timed bins, not imputed. Cause is WFDB HH≥24 clocks (I-CARE recording hour), CPC5-skewed; see ingest handover.
- Diffusion `computed` on 3419/3484 runs; Jacobian metrics 3D `computed` on 3443/3484.
- Stored `/stochastic_reachability/v1` is mostly `invalid` (2906/3484). Horizon cones were therefore recomputed from MNPS, not read from that group.
- Destination/committor and resilience remain `not_testable` on every file, as expected.
- Sedation/medication/WLST are absent from the export.

### Family A (diffusion geometry), 0–12 h, patient medians

Internal exploratory associations on this part1-equivalent bundle. BH-FDR applied inside H1–H3 only.

| Hypothesis | Metric | CPC1 median | CPC5 median | d (1−5) | MW p | BH q |
|---|---|---:|---:|---:|---:|---:|
| H1 | `d_eff_a_median` | 2.188 | 1.946 | +0.76 | 3.5e-7 | 5.2e-7 |
| H2 | `h_tilde_a_median` | 0.822 | 0.747 | +0.57 | 2.3e-7 | 5.2e-7 |
| H3 | `e_perp_median` | 0.613 | 0.591 | +0.49 | 2.3e-5 | 2.3e-5 |
| H4 control | `d_total_median` | 0.233 | 0.260 | −0.57 | 0.0049 | not in family |

H1–H3 match the predicted CPC1 > CPC5 direction. Recomputed `d_eff^(a)` agrees with stored `d_diff` to median absolute difference ~4.6e-8. H4 was not required to differ; on this bundle CPC5 has *higher* total diffusion power, so the CPC1 advantage is geometric (richer / less canalized), not “more noise”.

H3 uses `E_perp` computed from `a_hat` plus `/mnps_3d_dot` as a chart-velocity proxy. Stored `A_bD` / `drift_diffusion_alignment` is not usable as a cross-check here (`e_perp_from_stored_abd` is missing for all 161 primary rows), consistent with the ingest contract that `A_bD` is `not_testable` without an independently supplied drift. Treat H3 as a candidate axis with that validity limit.

TTM=33 subset (n=55/49) keeps H1–H3 sign. TTM=36 is too small (7/11) for a strong claim.

### Reachability localization

`cone_d_eff` CPC1 > CPC5 already at **h=1** (d=+0.81) and still at **h=4** (d=+0.79). This is Case A in `hypothesis.md`: the historical `tube_d_eff` advantage is already present in instantaneous innovation geometry, not something that only appears after multi-step propagation. `tube_d_eff_median` d=+0.82, same sign as the old article.

### Family B (MNJ-v3)

Primary prediction `F_reactive` CPC1 > CPC5 is **not supported** on this bundle: CPC1 0.102 vs CPC5 0.104, d=−0.46, p=0.0125 (opposite sign, small). Both groups have high `F_unstable` (~0.88). The CPC5 “majority-regime” split is currently uninformative (70/70 labeled unstable). Mean α was not preregistered; it is slightly lower in CPC1 (d=−0.46). Conditional `R_g | α<0` is *lower* in CPC1, not higher.

Plausible interpretation, not a mechanism claim: the exported spectral/numerical abscissa series live in a chart/estimator where most windows have α>0, so the hypothesis’s “stable-but-reactive window” (`α<0<ω`) is a rare occupancy (~10%) in both outcome groups. Do not promote Family B until part2 exists and the discrete-vs-continuous Jacobian time semantics are audited.

Finite-time `g_peak` was extracted for QC only and was not tested.

## Next steps (superseded by section below — kept for provenance)

1. Drop in a non-overlapping part2 bundle and rerun through `icare_v2_run_pipeline.py` without `--smoke`, then merge with a zero-overlap audit (the old `merge_coma_cohort_results.py` pattern).
2. Audit Jacobian time semantics (continuous J vs discrete A) before treating `F_reactive` as a failed hypothesis rather than an estimator-contract mismatch. Ingest packet: `handover/ingest_jacobian_fidelity_handover.md` (Jacobian gate plus other first-v3 issues).
3. Keep H3 labeled candidate until an independent drift field exists or `mnps_3d_dot` is separately qualified.
4. Do not start committor / FAR; those families are `not_testable` in this dump.
5. Sedation remains an uncontrolled confound for Family B.

---

## 002 - 2026-09-11 - part1-corrected vs part2-confirmatory (post ingest fix)

Ingest delivered two new bundles responding to `handover/ingest_jacobian_fidelity_handover.md` (details:
`handover/ingest_response_confirmation.md`):

- **part1-corrected** = `20260911_125829`, same 161-subject population as `20260904_225047`, re-ingested with
  the Jacobian fit-fidelity gate (threshold 0.9 on `rel_mse_baseline_median`), ComBat (`batch_key=hospital`),
  cohort-anchored coords, and restricted to filename hours 000–012. Config:
  `config/icare_v2_part1_corrected_config.yaml`. Output: `results/part1_corrected/`.
- **part2-confirmatory** = `20260911_123135`, **141 subjects with zero overlap** with part1. Same fixed
  contract. Config: `config/icare_v2_part2_confirmatory_config.yaml`. Output: `results/part2_confirmatory/`.

Ran the unmodified `src/` pipeline against both (only change: a `family_testable` flag, ≥10 patients/arm,
added to `icare_v2_outcome_contrast_analysis.py`). Built a joint table:
`results/replication/replication_summary.{csv,md}`.

### Coverage

| | part1-corrected | part2-confirmatory |
|---|---:|---:|
| subjects | 161 | 140 |
| H5 files | 1815 | 1838 |
| primary `0_12h` CPC1/CPC5 n | 71 / 70 | 70 / 70 |
| time_reference `ok` | 1815/1815 | 1838/1838 |
| diffusion `computed` | 1778/1815 | 1797/1838 |
| Jacobian 3D `computed` (fidelity-gated) | 22/1815 | 53/1838 |

### Family A (H1–H3), diffusion geometry, subject-anchored, ComBat-harmonized — replicated for H1/H2

| hyp | metric | part1 d (1−5) | part1 BH q | part2 d (1−5) | part2 BH q | call |
|---|---|---:|---:|---:|---:|---|
| H1 | `d_eff_a_median` | +0.76 | 2.0e-6 | +0.61 | 1.6e-3 | **replicated** |
| H2 | `h_tilde_a_median` | +0.58 | 2.0e-6 | +0.48 | 7.2e-3 | **replicated** |
| H3 | `e_perp_median` | +0.098 | 0.043 | **−0.099** | 0.134 (n.s.) | **did not replicate** |
| H4 (control) | `d_total_median` | −0.47 | n/a | −0.36 | n/a | same direction, not both sig. |

Reachability cones (recomputed from `coords_3d_subject_anchored`, bypassing the still-mostly-`unavailable`
stored `/stochastic_reachability/v1`): `cone_d_eff_h1`, `cone_d_eff_h4`, and `tube_d_eff` are all individually
significant (p<0.001) in **both** cohorts with the same sign (d≈0.66–0.82 part1, 0.66–0.74 part2). Case A
(advantage already at h=1) replicates.

**H1 and H2 are the first genuinely confirmatory (non-overlapping, independent-cohort) result in this article.**
H3 (`E_perp`) flips sign in part2 and is not BH-significant there; keep it a candidate metric, not a finding —
it depends on the unqualified `mnps_3d_dot` drift proxy (see `ingest_jacobian_fidelity_handover.md` §4/§16).

### Family B — confirmed not testable under the fidelity gate

Only 13/163 (part1) and 24/215 (part2) patient-timebins have any finite `alpha_mean`; primary contrast n is
7 vs 6 (part1, below `min_testable_group_n=10`) and 11 vs 11 (part2, borderline). `family_testable=False` /
borderline-`True` respectively. This is not a null result — it means the estimator cannot be applied here once
gated honestly. It also retroactively confirms the concern raised about the `20260904_225047` `F_reactive`
result: that earlier signal was an artifact of an ungated near-null fit.

### TTM sensitivity

TTM 33 °C subgroup (majority of both cohorts) reproduces the H1 direction in both bundles (part1 p=0.0013,
part2 p=0.032). TTM 36 °C subgroup is <10 per arm in both cohorts — not testable.

## Next steps

1. Manuscript: `manuscript.typ` now uses these numbers as the primary result; Family A H1/H2 are the headline,
   H3 and Family B are explicitly scoped as not-yet-established.
2. `conventional_eeg` pack is enabled in the overlay but not materialized in either new bundle's H5 files —
   needs a features-stage rerun at ingest before a qEEG-comparator secondary analysis is possible.
3. Sedation/WLST remain uncontrolled confounds; not addressable from this export.
4. `E_perp` needs an independently qualified drift field before H3 can be retested meaningfully.
