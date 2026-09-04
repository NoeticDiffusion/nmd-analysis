# NeuroComBat reachability audit 20260601

## Question

Why do almost all `reachability_cones` metrics become unusable in the NeuroComBat-cleaned I-CARE `part1` export?

## Short answer

The collapse is caused upstream by the NeuroComBat-cleaned `9D` subject-anchored coordinates, not by the article-level contrast script.

Across the rerun used for `comatose_ndt`:

- all `1508/1508` reachability H5 inputs had `coords_9d_subject_anchored/values`
- all `1508/1508` had **zero fully finite `9D` rows**
- in all `1508/1508`, the ninth `9D` axis was entirely missing
- the missing axis is `e_m`

Because reachability currently resolves subject-anchored `9D` first, the analysis consumes those broken `9D` coordinates instead of the still-usable `3D` coordinates.

## Evidence

### 1. The handoff collapse is real and happens before outcome contrasts

Primary reachability handoff sizes:

- non-ComBat `part1`: `82` usable reachability metrics
- NeuroComBat-cleaned `part1`: `3` usable reachability metrics

Hourly reachability handoff sizes:

- non-ComBat `part1`: `83`
- NeuroComBat-cleaned `part1`: `3`

The surviving metrics were only:

- `near_singular_rate`
- `tube_d_eff_split_half_n`
- `tube_log_det_split_half_n`

Those are numerics/QC-style fields that can remain finite even when the actual geometry series are all `NaN`.

### 2. Run-level reachability rows show total numeric collapse

For the NeuroComBat-cleaned primary rerun:

- old reachability rows with `finite_ok = true`: `1668/1668`
- NeuroComBat-cleaned reachability rows with `finite_ok = false`: `1508/1508`

Examples of metrics that were fully finite in the non-ComBat rerun and fully `NaN` in the NeuroComBat-cleaned rerun:

- `tube_log_det_median`
- `tube_d_eff_median`
- `tube_capture_gate_median`
- `cone_log_det_h1_median`
- `persistence_log_det_median`

At the same time:

- `near_singular_rate` changed from a median near `0.0` to a median of `1.0`
- split-half counts collapsed from hundreds of valid windows per run to `0`

### 3. The break is already present in the input `9D` coordinates

For a matched example run:

- baseline source: `/coords_9d_subject_anchored/values`
- NeuroComBat source: `/coords_9d_subject_anchored/values`

Baseline example:

- shape `788 x 9`
- fully finite row fraction `1.0`

NeuroComBat-cleaned example:

- shape `788 x 9`
- fully finite row fraction `0.0`
- axis 8 is entirely `NaN`

The `9D` axis names in the file are:

- `m_a`
- `m_e`
- `m_o`
- `d_n`
- `d_l`
- `d_s`
- `e_e`
- `e_s`
- `e_m`

The axis that disappears is therefore `e_m`.

### 4. This is global in the rerun, not an isolated run

Scanning all `1508` reachability H5 inputs used in the NeuroComBat-cleaned primary rerun:

- `1508/1508` had no fully finite `9D` rows
- `1508/1508` had dimension index `8` fully `NaN`
- `0/1508` had any other dimension fully `NaN`

By contrast, in a matched baseline scan over `1508` runs:

- `1508/1508` had fully finite `9D` rows
- `0/1508` had any all-`NaN` `9D` dimension

### 5. The pipeline prefers broken `9D` over usable `3D`

The reachability loader resolves subject-anchored `9D` first and only falls back to `3D` if `9D` is absent, not if it exists but is numerically broken.

That matters here because the same NeuroComBat-cleaned H5 files still contain usable `3D` subject-anchored coordinates:

- `1508/1508` had at least one fully finite `3D` row

For the same example run:

- default reachability on NeuroComBat `9D` produced `tube_log_det_median = NaN`, `tube_d_eff_median = NaN`, `near_singular_rate = 1.0`
- forcing `/coords_3d_subject_anchored/values` immediately restored valid geometry, including finite `tube_log_det_median`, finite `tube_d_eff_median`, and `near_singular_rate = 0.0`

## Interpretation

The primary failure mode is:

1. NeuroComBat-cleaned export writes `coords_9d_subject_anchored` with `e_m` entirely missing.
2. That makes every `9D` row non-finite.
3. Reachability still chooses `9D` because the dataset exists.
4. Local linear fits and propagated covariances become unusable.
5. Tube/cone/persistence metrics become all `NaN`.
6. The article handoff then drops those all-`NaN` metrics, leaving only a few QC-style numerics.

So the main issue is upstream export integrity for subject-anchored `9D`, with a secondary robustness gap in reachability fallback behavior.

## Secondary note

The current reachability flat rows set `finite_ok = false` correctly on these NeuroComBat-cleaned runs, but `not_testable` still remains `false`. That means the QC flagging underreports the severity of the failure mode even though the metric columns themselves already reveal it.

## Recommended next steps

1. Audit the NeuroComBat export step that writes subject-anchored `9D` coordinates and specifically why `e_m` becomes all `NaN`.
2. Add a defensive reachability fallback: if resolved `9D` exists but has no fully finite rows, fall back to subject-anchored `3D` rather than continuing with broken `9D`.
3. Optionally fix reachability QC semantics so `not_testable` follows `finite_ok`.
