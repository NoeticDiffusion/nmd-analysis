# 004 - 2026-09-11 - ingest: why the Jacobian fidelity gate fails 97-99% of windows, and three concrete fixes

## Context

`handover/ingest_jacobian_fidelity_handover.md` (item 1-4) asked for an honest fit-fidelity gate
on `/jacobian/derived_metrics/v1`. Ingest implemented it exactly as requested
(`handover/ingest_response_confirmation.md`), and it works correctly. The consequence, confirmed
on both new bundles (`20260911_125829`, `20260911_123135`): **97-99% of windows now correctly
fail the gate** (`failure_reason=local_linear_fit_not_better_than_baseline`), which means Family
B (α, ω, `F_reactive`) is not testable on this dataset at all (see `S6_Changelog.typ`,
manuscript §4.6/R6).

This is not a request to relax or remove the gate - the gate is correct and should stay. This is
a request to fix the *input* to the Jacobian fit so it has a realistic chance of succeeding,
because the current estimator appears to be structurally under-determined by construction, not
merely noise-limited.

## Root-cause evidence

### 1. The Jacobian fit gets ~1-2 increments per window; diffusion gets a pooled k=20 neighborhood

Directly inspected `/window_start`, `/window_end`, `/time` on sampled files from both new
bundles:

```text
window_start[:5] = [ 0.  4.  8. 12. 16.]
window_end[:5]   = [ 8. 12. 16. 20. 24.]
time[:5]         = [ 4.  8. 12. 16. 20.]
```

Each window spans 8 s with a 4 s step (`nominal_dt_sec = 4.0`, confirmed in
`/jacobian/derived_metrics/v1/provenance`). At most 1-2 finite-difference increments are
available per window to identify a 3x3 local generator (up to 9 free parameters, or fewer with
structure, but still over-parameterized relative to 1-2 data points).

Compare this to the **diffusion family**, which is estimated successfully on ~98% of windows
in both new bundles. Its overlay section explicitly pools a neighborhood before fitting:

```yaml
dynamical_families:
  diffusion:
    estimator: local_increment_covariance
    neighborhood: {k: 20}
    min_samples: 30
    min_neighborhood_samples: 10
    max_dt_relative_deviation: 0.05
```

The `local_dynamics.jacobian_metrics` overlay section (both new bundles) has **no equivalent
neighborhood/`min_samples` field at all**:

```yaml
local_dynamics:
  jacobian_metrics:
    stability_zero_tolerance: 1.0e-8
    reactivity_zero_tolerance: 1.0e-8
    fit_fidelity_gate:
      enabled: true
      threshold: 0.9
```

This is a direct, in-repo, apples-to-apples contrast: the same pipeline, on the same recordings,
pools k=20 neighbors for diffusion (98% success) and appears to use a single narrow time window
for the Jacobian fit (1-2% success). We think this - not a biological absence of local linear
structure - is the primary reason for the gate failure rate, and it is directly actionable
without touching the gate itself.

### 2. Zero EEG artifact rejection reaches the fit

`qc/windows` on sampled files, both bundles:

```text
qc_ok_eeg          = -1  (not_assessed), on 100% of sampled windows
rejected_flag      =  0, on 100% of sampled windows
retained_after_qc  =  1, on 100% of sampled windows
```

No amplitude, muscle/movement, or electrode-artifact rejection is currently applied to I-CARE
EEG before any per-window feature or dynamics estimate is computed (this matches
`preprocess.artifacts.method = "none"` noted in the original 2026-09-10 audit). A local linear
fit is especially sensitive to a small number of contaminated points, more so than a robust
covariance-based diffusion estimator - this is a second, independent reason the Jacobian fit
would be expected to do worse than diffusion even before the sample-count issue above.

## Requested changes (priority order)

1. **Give the Jacobian fit a neighborhood, analogous to diffusion's `neighborhood: {k: 20},
   min_samples: 30, min_neighborhood_samples: 10`.** Concretely: either (a) pool a k-NN
   neighborhood in state space (as already implemented for `stochastic_reachability` and now
   requested here for symmetry), or (b) widen the time window / reduce the step so each window
   contains materially more than 1-2 increments, whichever is more consistent with
   `operator_semantics = continuous_time_generator`. Report the chosen `min_samples` /
   neighborhood size in `/jacobian/derived_metrics/v1/provenance`, next to
   `fit_fidelity_threshold`.
2. **Add real EEG artifact rejection before any per-window estimate** (amplitude threshold,
   muscle/movement detector, electrode-pop detector), and make `qc_ok_eeg` / `rejected_flag`
   actually reflect it (currently always `-1` / `0`). This should benefit diffusion, MNPS-3D/9D
   coordinates, and the Jacobian fit alike, not just Family B.
3. After (1)+(2), re-run `summarize` on a small sample and report the new
   `jacobian_metrics_3d_status` distribution and `rel_mse_baseline_median` histogram before a
   full re-ingest, so we can confirm the fix actually moves windows below the 0.9 threshold
   rather than just changing the failure mode.

## What we are *not* asking for

- Do not lower `fit_fidelity_threshold` below 0.9 or otherwise weaken the gate to manufacture a
  higher pass rate - that would reproduce the original problem this gate was built to catch.
- Do not change anything about the diffusion family (H1-H4); it is working well and is the basis
  of the one confirmed, replicated result in this article line (`manuscript.typ` R2/R3).
- Materializing the `conventional_eeg` pack (flagged in
  `handover/ingest_response_confirmation.md`) is a separate, lower-priority item, not bundled
  into this request.

## Addendum (2026-09-12): checked a new bundle, not yet a fix

A new bundle `neuralmanifolddynamics_physionet_icare_2_1_20260912_094010` appeared after this
handover was filed. Smoke-tested it (10 subjects, 137 runs, matched exactly against the same 10
subjects in `20260911_123135`) before assuming it was a response to this request. It is not: the
overlay config file is byte-identical (SHA-256 match) to the one used for `20260911_123135`, same
`git_rev = eb0ff86bec842682c60f631a986cbaffc93e27d5`, same population (140/140 subject-ID
overlap) - only `--n-jobs` and the timestamp differ. As expected for a deterministic re-run of
identical code on identical input, the Jacobian gate pass rate is exactly unchanged on the
matched 10-subject sample (9/137 `computed`, 128/137 `insufficient_support`, both bundles,
identical counts). This bundle is a duplicate/re-run, not a fix, and none of items (1)-(3) above
have been addressed yet. Config and smoke-test artifacts kept at
`config/icare_v2_20260912_estimator_check_config.yaml`,
`config/icare_v2_20260912_smoke_subjects.yaml`,
`results/estimator_check_20260912_smoke/` for future comparison once a real fix lands.

## Addendum (2026-09-13): both 094010 and 094016 re-checked

User reported both `20260912_094010` (part2 / next_140) and `20260912_094016`
(part1) as re-runs. Rechecked against the predecessor bundles
(`20260911_123135`, `20260911_125829`).

What actually changed:

- Overlay YAML files are still byte-identical to the predecessors. `git_rev`
  is still `eb0ff86bec842682c60f631a986cbaffc93e27d5`. The only resolved-config
  excerpt difference is the cohort-anchor *path* (new run directory).
- `/jacobian/derived_metrics/v1/provenance` now *documents* the existing MNPS
  Jacobian knobs that were previously omitted: `knn_k=20`, `min_samples=4`,
  `n_neighborhood_samples_median/min`, `ridge_alpha=1.0`, `super_window=3`,
  `distance_weighted=true`. Neighborhood size on sampled files is not tiny
  (median ~36-63 neighbors) - so a kNN neighborhood was already in use, just
  not stamped.
- `094016` was a `--resume-run` (1585 groupings skipped as complete, 237
  remaining at resume time).

What did **not** change (the actual quality request):

- Gate pass rate on a matched 80-file sample is identical old vs new in both
  cohorts: 1/80 `computed`, 79/80 `insufficient_support`. `rel_mse_baseline_median`
  distributions match to reported precision (part2 median 0.9751, p05 0.9558,
  p95 0.9892; part1 median 0.9686, p05 0.9378, p95 0.9760). Matched files have
  bit-identical `rel_mse_baseline_median` (e.g. sub-0378 run-001: 0.9904554486274719
  in both 123135 and 094010).
- `min_samples=4` is now visible, and is *not* analogous to diffusion's
  `min_samples: 30`. Provenance without a better estimator does not move windows
  under the 0.9 threshold.
- `qc_ok_eeg = -1` on 100% of sampled windows in both new bundles (item 2,
  artifact rejection: not done).
- `conventional_eeg` pack still not materialized (separate, lower-priority item).

Correction to the 2026-09-12 addendum: 094010 was a real re-summarize that added
Jacobian-neighborhood provenance, not a no-op duplicate of 123135. The
yesterday smoke-test conclusion "gate rate unchanged" was correct; the
inference "nothing in the H5 contract changed" was not - provenance grew,
fit quality did not.

Items (1)-(3) of the original request are therefore still open: documenting
`knn_k=20` is necessary but not sufficient. The fit still loses to baseline
on ~99% of windows, so Family B remains not testable.

## What this unblocks if fixed

If the Jacobian fit's `computed` rate rises materially (even to, say, 20-30% rather than 1-3%),
Family B's pre-specified hypothesis (`F_reactive`, H5 in `handover/hypothesis.md`) becomes
testable for the first time with an honest gate, on both the existing part1-corrected
(`20260911_125829`) and part2-confirmatory (`20260911_123135`) subject populations - no new raw
data collection needed, just a re-run of `summarize` on the same recordings.
