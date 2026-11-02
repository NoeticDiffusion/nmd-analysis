# ds004100 NDT v1.0 September coverage report

Audit date: 2026-09-22T16:10:52.052806+00:00. The audited export is exactly
`J:\repos\nmd-analysis\data\raw\neuralmanifolddynamics_ds004100_20260918_083008`. This is the corrected September export; no August export
was read. The audit is read-only and covers all recursive `*.h5` files.

## Reproduction and scope

```powershell
& J:\repos\nmd-analysis\.venv\Scripts\python.exe `
  J:\repos\nmd-analysis\articles\ds004100_ndt_v.1.0\coverage_september\audit_ds004100_september_coverage.py `
  --data-root J:\repos\nmd-analysis\data\raw\neuralmanifolddynamics_ds004100_20260918_083008 `
  --output-dir J:\repos\nmd-analysis\articles\ds004100_ndt_v.1.0\coverage_september
```

Outputs are the reproducible [audit script](audit_ds004100_september_coverage.py),
the [per-file CSV manifest](ds004100_h5_manifest_september.csv), and the
[JSON manifest](ds004100_h5_manifest_september.json). The JSON and CSV record
shapes, finite counts, status fields, support signatures, and provenance. They
do not record endpoint means/effects, condition contrasts, or new fits.

## Inventory, labels, and pairability

The all-file audit read **319** of **319**
H5 files (739,229,963 bytes) from **57** subjects.
H5 task counts are `{"ictal":208,"interictal":111}` and filename task
counts are `{"ictal":208,"interictal":111}`; task/filename matches
are `{"True":319}`. There are
55 task-paired subjects and
55 task-paired subject/session/acquisition
keys. These are export-label pairability counts, not evidence of true seizure
intervals.

The first lexicographic exemplar is `sub-HUP060_ses-presurgery_ictal_run-01_acq-seeg/sub-HUP060_ses-presurgery_ictal_run-01_acq-seeg.h5`.
Its selected metadata are shown here only to distinguish exemplar inspection
from all-file counts: subject `sub-HUP060`, task
`ictal`, `93 time rows`, coverage
`376.0 effective seconds`, geometry
`ok`, and coordinate contract
`subject_anchored`. The complete per-file record
is in the manifests.

## Time, windows, coordinates, and finite support

Per-file `n_time` ranges from 45 to
326. Gap count distributions for the expected
step and the FTR 1.5x hard-break rule are recorded in the JSON manifest; the
audit found `{"0":319}` non-positive-step
counts. Window and coverage support are recorded per file without inferring
seizure onset/offset intervals.

Core-array presence counts are `{"J_3d":319,"J_3d_dot":319,"J_3d_subject":319,"J_3d_subject_dot":319,"J_9d":319,"J_9d_dot":319,"J_9d_subject":319,"J_9d_subject_dot":319,"coords_3d_subject":319,"coords_9d":319,"coords_9d_subject":319,"mnps_3d":319,"mnps_3d_dot":319}`.
Finite counts are per array and per file; no missing value is converted to
zero. The canonical MNPS and 9D coordinate definitions remain structural
exports, and their finite rows do not establish biological validity.

## Features and provenance

Normalization status is `{"disabled":319}`.
Feature-fit temporal support status is
`{"unknown":319}` and source-quality
status is `{"not_recorded":319}`. The H5
records local input-frame fit populations, hashes, scopes, chart coordinate
layers, distance metric identifiers, and family estimator/time semantics; the
manifest retains these provenance strings without exposing numerical endpoint
values. The mixed `{"acq-ecog":109,"acq-seeg":210}` acquisitions do not
carry a channel-level comparability certificate in this audit.

## Events and labels

Top-level events groups occur in 0/319
files and labels groups in 0/319.
Manifest event-count distribution is `{"0":319}`
and label-count distribution is `{"0":319}`.
The exported ictal/interictal task is therefore filename/H5 metadata here; a
true event-locked interval is not established. Absence of H5 `events`/`labels`
groups does not imply that source-side annotation files are absent; external
source metadata and alignment are a separate audit boundary. The coordinator's
[source-sidecar audit](../source_metadata/README.md) found all 208 ictal event
TSV files in the accessible K: source; nominal annotation containment is not
proof of filter support or event-pure estimator neighborhoods.

## Dynamical families and qualification status

Every family row keeps computation, measurement-validity, support, claim, and
qualification fields separate. All-file family summaries are:

- **amplification**: present in 319/319; computation `{"computed":319}`; support `{"sufficient":319}`; measurement validity `{"not_assessed":319}`; claim `{"no_biological_claim":319}`.
- **diffusion**: present in 319/319; computation `{"computed":319}`; support `{"sufficient":319}`; measurement validity `{"not_assessed":319}`; claim `{"no_biological_claim":319}`.
- **drift**: present in 319/319; computation `{"computed":319}`; support `{"":319}`; measurement validity `{"not_assessed":319}`; claim `{"no_biological_claim":319}`.
- **one_step**: present in 319/319; computation `{"computed":85,"insufficient_support":234}`; support `{"":161,"insufficient_local_support":73,"sufficient":85}`; measurement validity `{"not_applicable":234,"not_assessed":85}`; claim `{"no_biological_claim":319}`.
- **history**: present in 319/319; computation `{"computed":319}`; support `{"sufficient":319}`; measurement validity `{"not_assessed":319}`; claim `{"no_biological_claim":319}`.
- **turning**: present in 319/319; computation `{"computed":319}`; support `{"sufficient":319}`; measurement validity `{"not_assessed":319}`; claim `{"no_biological_claim":319}`.
- **destination**: present in 319/319; computation `{"not_testable":319}`; support `{"not_applicable":319}`; measurement validity `{"not_applicable":319}`; claim `{"no_biological_claim":319}`.
- **resilience**: present in 319/319; computation `{"not_testable":319}`; support `{"not_applicable":319}`; measurement validity `{"not_applicable":319}`; claim `{"no_biological_claim":319}`.

Nested metric-variant status counts (including absent variants) are:

- `drift/conditional_mean_rate_level1/blocked_crossfit` present 319/319; computation `{"computed":285,"insufficient_support":34}`; support `{"insufficient_local_support":34,"sufficient":285}`; validity `{"not_applicable":34,"not_assessed":285}`.
- `one_step/affine_one_step_map_level2` present 158/319 (absent 161); computation `{"computed":85,"insufficient_support":73}`; support `{"insufficient_local_support":73,"sufficient":85}`; validity `{"not_applicable":73,"not_assessed":85}`.
- `one_step/conditional_affine_mean_rate_level2` present 158/319 (absent 161); computation `{"computed":85,"insufficient_support":73}`; support `{"insufficient_local_support":73,"sufficient":85}`; validity `{"not_applicable":73,"not_assessed":85}`.
- `one_step/declared_lag_2/affine_one_step_map_level2` present 319/319; computation `{"computed":9,"insufficient_support":310}`; support `{"insufficient_local_support":310,"sufficient":9}`; validity `{"not_applicable":310,"not_assessed":9}`.
- `one_step/declared_lag_2/conditional_affine_mean_rate_level2` present 319/319; computation `{"computed":9,"insufficient_support":310}`; support `{"insufficient_local_support":310,"sufficient":9}`; validity `{"not_applicable":310,"not_assessed":9}`.
- `one_step/declared_lag_2/divergence_level3` present 319/319; computation `{"computed":8,"insufficient_support":164,"not_testable":147}`; support `{"insufficient_local_support":164,"not_applicable":147,"sufficient":8}`; validity `{"not_applicable":311,"not_assessed":8}`.
- `one_step/declared_lag_2/generator_rotation_norm_level3` present 319/319; computation `{"computed":8,"insufficient_support":164,"not_testable":147}`; support `{"insufficient_local_support":164,"not_applicable":147,"sufficient":8}`; validity `{"not_applicable":311,"not_assessed":8}`.
- `one_step/declared_lag_2/innovation_covariance_level2` present 319/319; computation `{"computed":9,"insufficient_support":310}`; support `{"insufficient_local_support":310,"sufficient":9}`; validity `{"not_applicable":310,"not_assessed":9}`.
- `one_step/declared_lag_2/numerical_abscissa_level3` present 319/319; computation `{"computed":8,"insufficient_support":164,"not_testable":147}`; support `{"insufficient_local_support":164,"not_applicable":147,"sufficient":8}`; validity `{"not_applicable":311,"not_assessed":8}`.
- `one_step/declared_lag_2/operator_max_gain_rate_level2` present 319/319; computation `{"computed":9,"insufficient_support":163,"not_testable":147}`; support `{"insufficient_local_support":163,"not_applicable":147,"sufficient":9}`; validity `{"not_applicable":310,"not_assessed":9}`.
- `one_step/declared_lag_2/operator_rotation_rate_level2` present 319/319; computation `{"computed":8,"insufficient_support":164,"not_testable":147}`; support `{"insufficient_local_support":164,"not_applicable":147,"sufficient":8}`; validity `{"not_applicable":311,"not_assessed":8}`.
- `one_step/declared_lag_2/operator_volume_gain_rate_level2` present 319/319; computation `{"computed":9,"insufficient_support":163,"not_testable":147}`; support `{"insufficient_local_support":163,"not_applicable":147,"sufficient":9}`; validity `{"not_applicable":310,"not_assessed":9}`.
- `one_step/declared_lag_2/spectral_abscissa_level3` present 319/319; computation `{"computed":8,"insufficient_support":164,"not_testable":147}`; support `{"insufficient_local_support":164,"not_applicable":147,"sufficient":8}`; validity `{"not_applicable":311,"not_assessed":8}`.
- `one_step/divergence_level3` present 158/319 (absent 161); computation `{"computed":85,"not_testable":73}`; support `{"not_applicable":73,"sufficient":85}`; validity `{"not_applicable":73,"not_assessed":85}`.
- `one_step/generator_rotation_norm_level3` present 158/319 (absent 161); computation `{"computed":85,"not_testable":73}`; support `{"not_applicable":73,"sufficient":85}`; validity `{"not_applicable":73,"not_assessed":85}`.
- `one_step/innovation_covariance_level2` present 158/319 (absent 161); computation `{"computed":85,"insufficient_support":73}`; support `{"insufficient_local_support":73,"sufficient":85}`; validity `{"not_applicable":73,"not_assessed":85}`.
- `one_step/iterated_one_step_horizon_map_level4` present 319/319; computation `{"computed":15,"insufficient_support":70,"not_testable":234}`; support `{"insufficient_local_support":70,"not_applicable":234,"sufficient":15}`; validity `{"not_applicable":304,"not_assessed":15}`.
- `one_step/numerical_abscissa_level3` present 158/319 (absent 161); computation `{"computed":85,"not_testable":73}`; support `{"not_applicable":73,"sufficient":85}`; validity `{"not_applicable":73,"not_assessed":85}`.
- `one_step/operator_max_gain_rate_level2` present 319/319; computation `{"computed":85,"not_testable":234}`; support `{"insufficient_local_support":161,"not_applicable":73,"sufficient":85}`; validity `{"not_applicable":234,"not_assessed":85}`.
- `one_step/operator_rotation_rate_level2` present 319/319; computation `{"computed":85,"not_testable":234}`; support `{"insufficient_local_support":161,"not_applicable":73,"sufficient":85}`; validity `{"not_applicable":234,"not_assessed":85}`.
- `one_step/operator_volume_gain_rate_level2` present 319/319; computation `{"computed":85,"not_testable":234}`; support `{"insufficient_local_support":161,"not_applicable":73,"sufficient":85}`; validity `{"not_applicable":234,"not_assessed":85}`.
- `one_step/spectral_abscissa_level3` present 158/319 (absent 161); computation `{"computed":85,"not_testable":73}`; support `{"not_applicable":73,"sufficient":85}`; validity `{"not_applicable":73,"not_assessed":85}`.
- `history/history_conditioned_operator_level2` present 319/319; computation `{"computed":72,"insufficient_support":247}`; support `{"insufficient_local_support":247,"sufficient":72}`; validity `{"not_applicable":247,"not_assessed":72}`.

Metric paths and finite counts are listed without aggregating or contrasting
their values. Native metric series and `source_idx` support indices are kept as
separate arrays; any length mismatch is an audit finding rather than a reason
to zip them positionally. Computed outputs and `support_status` are not
upgraded to qualified biological measurements.

## Native support gates used by the preregistration

The audit also records the two preregistered native-grid support gates without
calculating endpoint means or effects. H1 is the diffusion
`diffusion_effective_dimension` series on the native T grid. Its explicit
`valid` mask defines supported centers; the diffusion `source_idx` is retained
as a training increment-pool diagnostic and is explicitly not used as the H1
query mask. H2 is the amplification `neighbor_gain_q90` series on the native T
grid; its neighbour-count support is checked separately from its `source_idx`.
Neither series is positionally zipped to `source_idx`.

The per-file H1/H2 finite counts, supported counts, fractions, `>=30` and
`>=50%` flags, source-index finite counts, and finite metric values outside the
source-index set are in both manifests. Aggregate gate counts are:

- **H1**: 319/319 files meet >=30 centers and >=50% support; 55 structurally paired subjects.
- **H2**: 319/319 files meet >=30 centers and >=50% support; 55 structurally paired subjects.

These are structural eligibility
records only; they do not establish event purity, temporal filter support,
measurement validity, or a biological claim.

Finite-time response, transition-residual covariance (Q), transition residuals,
and stochastic reachability status/finite-count records are included when
present. The Q and reachability rows retain only structural finite counts and
support metadata. No means, effects, or condition comparisons are produced.

## Verdict and limitations

**PARTIAL PASS — structural coverage is reproducible for all 319
September H5 files.** The export supports complete inventory, task-pairability
counts, observed time/window support, canonical coordinate/J finite accounting,
family schema/status enumeration, support-signature enumeration, and provenance
hashes. It does not establish event-locked seizure intervals, channel
comparability, filter temporal support, scientific measurement validity, or
biological qualification. Scientific contrasts remain outside this audit.

Root sidecars are hashed in the JSON manifest. The script records its own hash
as `2661d482e6e826c4df513f397015f4cde6b38ee95200175989bd6d4a94cf00d6`.
