# Coordinate-support policy for the sleep drift candidate gate

Date: 2026-09-12  
Policy: `coordinate_support_policy_20260912`  
Config: `config/sleep_drift_coordinate_gate_20260912.json`

This is a bounded development protocol for candidate-coordinate support. It
does not reopen the strict M3 reference gate, qualify a chart, identify Itô
drift, establish a sleep-stage effect, or authorize a diffusion coupling. The
candidate remains `candidate_not_qualified` with `claim_status=
no_biological_claim`.

## Question and boundary

The question is whether a selected, explicitly named coordinate array can be
checked for finite values and valid endpoint support when the file-level
geometry status is `adjusted` solely because an unrelated 9D Jacobian-window
condition filter removed windows. A Jacobian derivative surface and a
coordinate value surface are separate serialized objects. This policy carries
the file-level `adjusted` status forward and records a separate coordinate-gate
decision; it never relabels the file as `ok`.

The policy applies to either configured candidate chart:

| name | HDF5 path | dimension | canonical order |
| --- | --- | ---: | --- |
| `mnps_3d` | `mnps_3d` | 3 | `m,d,e` |
| `coords_9d` | `coords_9d/values` | 9 | `m_a,m_e,m_o,d_n,d_l,d_s,e_e,e_s,e_m` |

The runner must select the chart explicitly for each row. Subject identity is
not an acceptance criterion, and the policy contains no subject-specific
allowlist.

## Pinned inputs and source-era evidence

The only accepted inputs for this gate are the two exact E1/E2 development H5
files. Their SHA-256 values must be checked before and after reading:

| recording | SHA-256 | observed file status |
| --- | --- | --- |
| sub-99 | `217991681011397acd4493cd97cc74e7a982d361a04e6e94d29b40c8261ef8a1` | `ok` |
| sub-1 | `1eba1d7d9a470647992ab729f26a4ee5cea9249586e7e98cbad814759cff94db` | `adjusted` |

Direct inspection of the pinned files found the following evidence:

| field | sub-99 | sub-1 |
| --- | ---: | ---: |
| time-grid status | `ok` | `ok` |
| shared epochs before / retained / dropped | 1068 / 1068 / 0 | 915 / 915 / 0 |
| 3D Jacobian raw / retained / invalid | 1066 / 1066 / 0 | 913 / 913 / 0 |
| 9D Jacobian raw / retained / invalid | 1066 / 1066 / 0 | 913 / 856 / 57 |
| sub-1 9D invalid reasons | — | condition-number 57, nonfinite 0 |

The count 57 is recorded evidence about this pinned artifact. It is not a
policy threshold. The general adjusted branch requires a positive integer
invalid-window count that is exactly accounted for by the condition-number
reason, with zero nonfinite invalid windows and raw-minus-retained equal to the
invalid count.

The selected coordinate values in both pinned files are finite, have the
configured canonical shapes and orders, and align to the source time rows.
Those observations do not establish that upstream filters, resampling or
normalization were held out. The source signal-support status remains
`unknown`, and the whole-recording robust-z fit remains a stated limitation.

## Acceptance state machine

Every required HDF5 path must exist with a recognized scalar or array type.
Unknown, missing, malformed, inconsistent or unaccounted metadata causes a
refusal. The runner records both the original strict-reference decision and
the coordinate-support decision.

For overall `ok`, the runner requires all of the following:

1. `provenance/geometry_contract/status` is exactly `ok` and
   `time_grid/status` is exactly `ok`.
2. The shared time grid has no dropped epochs and its drop-reason mapping has
   exactly the two recognized keys `coords_9d_nonfinite_rows_affecting_primary`
   and `mnps_3d_nonfinite_rows`, both with integer value zero. Unknown keys
   are unaccounted causes and force refusal.
3. Neither coordinate surface has degenerate or all-NaN axes or nonfinite
   rows; the 9D surface is available, shape-matched to the time grid, and has
   zero `nonfinite_rows_retained_on_shared_grid`.
4. The 3D and 9D Jacobian statuses are `ok`, each invalid-window count is the
   integer zero, and each raw count equals its retained count. Both condition-
   number and nonfinite invalid-reason counts are zero.
5. The selected chart has the exact configured path, layer, dimension and axis
   order; its array is two-dimensional, row-aligned, numeric and entirely
   finite.
6. Time is finite and strictly increasing with exact `dt=30` seconds. Window
   starts and ends are finite, ordered, contiguous and exactly 30 seconds long.
   The selected candidate's increment support is the validated union of source
   and destination windows, with the frozen 60-second embargo checked.

For overall `adjusted`, the same checks apply, except the file-level adjusted
status is allowed only with this explicit evidence:

1. The 3D Jacobian is `ok` with zero invalid windows and zero invalid-reason
   counts.
2. The 9D Jacobian is `adjusted` with a positive integer invalid-window count.
3. The 9D raw-minus-retained count equals its invalid-window count.
4. The 9D condition-number invalid-reason count equals its invalid-window
   count, and the nonfinite invalid-reason count is zero. Both Jacobian
   invalid-reason maps must contain exactly the recognized keys
   `condition_number_windows` and `nonfinite_windows`; unknown keys are an
   unaccounted reason and cause refusal.
5. Shared-grid drops, coordinate degeneracy/nonfiniteness and time-grid
   problems are absent as described above. No other adjusted cause is present
   or left unaccounted for.

This adjusted branch can therefore be evaluated for either explicitly
configured chart. It is a chart-support continuation around an unrelated
Jacobian-window adjustment, not a waiver of any coordinate, time or support
failure.

The strict reference rule remains unchanged: the existing reference smoke
requires overall geometry status `ok`; an `adjusted` source is serialized as a
strict-reference refusal even when this coordinate-support gate accepts its
selected chart. A coordinate-gate acceptance cannot be used to rewrite that
refusal.

## Frozen candidate and scientific limits

The E3 split remains train increments `[0,600)`, evaluation increments
`[700,800)`, 32 neighbors, minimum 12 training observations, local-mean and
local-linear estimators, and a 60-second embargo. This policy does not alter
the estimator, thresholds, coordinate definitions, normalization, or source
files. It does not tune or refit any upstream transform.

The runner must retain source hashes, selected coordinate path/layer/order/
shape/dtype/hash, geometry evidence, adjustment-reason evidence, time and
support arrays/hashes, strict-reference status and coordinate-gate status.
Missing values remain missing and are refused; no imputation or zero
substitution is allowed.

No candidate vector may be inserted into `a_hat`, `D_total`, `d_diff`,
`c_diff`, `A_bD` or `R_b_over_a`. No stage contrast, biological comparison,
Itô interpretation, qualification or publication claim follows from this
gate.
