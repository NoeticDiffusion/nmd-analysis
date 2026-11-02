# ds004100 NDT v1.0 English coverage report

Audit date: 2026-09-22. The audited export is exactly
`J:\repos\nmd-analysis\data\raw\neuralmanifolddynamics_ds004100_20260812_054004`.
The newer export was not substituted. The audit is read-only and covers all
recursive `*.h5` files in that directory.

## Reproduction and scope

Run from an environment with `h5py` and `numpy`:

```powershell
python J:\repos\nmd-analysis\articles\ds004100_ndt_v.1.0\coverage\audit_ds004100_h5_coverage.py `
  --data-root J:\repos\nmd-analysis\data\raw\neuralmanifolddynamics_ds004100_20260812_054004 `
  --output-dir J:\repos\nmd-analysis\articles\ds004100_ndt_v.1.0\coverage
```

The script inventories metadata and schema for every file, records selected
dataset shapes and finite-row counts, records time/window support and gaps,
records provenance/status fields, and computes a SHA-256 for every H5 input.
It does not calculate condition feature summaries, effect sizes, or hypothesis
outcomes. Structural finite checks are a full scan of selected exported arrays;
they are not a scientific validation of the underlying signal or seizure
annotations.

Outputs are [the reproducible audit script](audit_ds004100_h5_coverage.py),
[the per-file CSV manifest](ds004100_h5_coverage_manifest.csv), and
[the JSON manifest and aggregate](ds004100_h5_coverage_manifest.json).

## Inventory and pairing metadata

There are 319 H5 files (609,453,516 bytes) from 57 subjects. The exported
filename/task metadata contains 208 `ictal` and 111 `interictal` files, with
210 `acq-seeg` and 109 `acq-ecog` files. Fifty-five of 57
subject/session/acquisition groups contain both filename tasks. This is a
pairability count based on exported metadata only; it is not evidence that a
true seizure interval is present or correctly mapped.

All files have the same dataset id family and the `Epilepsy` group metadata.
The primary coordinate contract is cohort anchored in all files. Subject and
cohort anchored coordinate layers are both exported.

## Time, support, and missingness

The observed center-time grid is regular in all 319 files: median and maximum
center interval are 4 seconds, the configured expected step is 4 seconds, and
there are zero detected gaps or non-positive intervals. Window support is 8
seconds with 4-second overlap. Per-file `n_time` is 45–326, center-time span is
176–1300 seconds, and window-support span is 184–1308 seconds. These are
observed H5 intervals, not seizure-onset or seizure-offset intervals.

The canonical `/mnps_3d` array is `[T,3]` with axis order `[m,d,e]`. All 319
files have all rows finite in that array. The canonical `/coords_9d/values`
array is `[T,9]`, with the fixed exemplar order
`[m_a,m_e,m_o,d_n,d_l,d_s,e_e,e_s,e_m]`; all 319 files have all rows finite.
The subject-anchored and cohort-anchored 3D/9D coordinate layers are present
in all 319 files and retain the same time grid. Geometry contract status is
`ok` in 296 files and `adjusted` in 23. No missing values were replaced with
zero by this audit, and no computed output was upgraded to a qualified object.

## Features, normalization, and comparability

`/features_raw/values`, `/features_robust_z/values`, and
`/features_projection_z/values` are present in all 319 files, each with 224
feature columns. Each file embeds feature metadata and a feature-anchor table.
The anchor identity is `ds004100_all_subjects_iqr_v2_1` with hash
`d31b989970c7eb32713e8ccba17cebdda908f5c1bd11b9152f18dfb190a0b735`, sourced
from `all_subjects_features_table`. The embedded normalization provenance is
`status=disabled`, `method=combat`, `scope=post_features` for all files.

The export mixes `acq-seeg` and `acq-ecog`. The H5 files do not contain raw
region signals or an aligned channel-by-channel signal matrix; row-source
metadata reports `source_format=unknown` while source filenames are individual
`ieeg.edf` files. Therefore channel comparability across acquisitions is not
established by this export and requires source-level channel/derivation
metadata before a common-channel analysis.

## Events and labels

No top-level H5 `events` or `labels` group is present in any of the 319 files.
Every available `summary.json` inspected by the script has `events=[]` and
`labels=[]`. A stage codebook group is present, but there is no aligned stage
trajectory; the time-reference provenance is disabled in all files. The
`ictal`/`interictal` labels are therefore filename/task metadata only. A true
seizure interval, onset, offset, or event-locked window support cannot be
verified from this export.

## Local dynamics and qualification status

Finite-time response is present and marked `computed` in all 319 files at
requested horizons h1/h2/h4, corresponding to 4, 8, and 16 seconds on the
4-second center grid. Its validation level is `model_derived`. Transition
residuals and the transition-residual covariance proxy are both present and
marked `computed` in all 319 files. The stochastic-reachability path is absent
from all files.

The 3D Jacobian is present in all 319 files. The canonical unanchored 9D
Jacobian is present in 317 files; subject-anchored 9D Jacobian is present in
all 319 and cohort-anchored 9D Jacobian in 317. These are computed Jacobian,
finite-time-response, residual, and covariance exports. No scientific
qualification field was found, so the audit records them as computed/model
derived rather than scientifically qualified.

## Coverage verdict and limitation

**PARTIAL PASS — structural coverage is reproducible for all 319 H5 files.**
The export supports complete inventory, canonical 3D/9D coordinate presence,
finite-row accounting, regular observed windows, feature-anchor provenance,
and a bounded audit of computed local-dynamics paths. It does not establish
true seizure intervals, event-locked support, cross-acquisition channel
comparability, or scientific qualification of local-dynamics outputs. A
seizure-gated preregistration endpoint remains blocked until an independent
source of seizure onset/offset annotations is joined and its time alignment is
verified.
