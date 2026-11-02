# LEGACY-LOSS-002 — Feature-transform ablation

Date: 2026-10-08  
Status: exploratory post-hoc mechanism analysis; protocol frozen before the new
transform-arm AUCs are computed.

## Question

Within the ten saved BENCH-001 raw-v2 inputs, how do the feature-specific
logarithm, within-recording robust-z, and ±6 clipping operations relate to the
EC/EO information loss previously localized to the combined transformation
block by LEGACY-LOSS-001?

This is a post-hoc decomposition of a historical pipeline. It does not repair
MNPS 2.0, redefine its comparator, or establish why the original H1 result
occurred biologically.

## Frozen source and feature contract

Read only the 200 H1 processed HDF5 files identified by
`h1_analysis_freeze_v3.json`. Verify their hashes and the H1 freeze dependencies
before and after analysis. Do not read EDFs or recompute EEG features.

Use the same ten ordered `RAW_INPUT_FEATURES` as H1. Their transform contract is
read from each saved HDF5 `feature_baselines` entry and must be constant across
the frozen files. The `log10` factor applies only where that saved contract
contains `log10` (expected: delta, theta, alpha, and gamma power). The local
robust-z and clipping procedures are those represented by the saved HDF5
surfaces and the frozen NMD `projection.py` implementation. Clipping threshold
is 6.0.

## Transform arms

All arms retain the same ten feature identities and order. Transforms operate
on each recording's saved windows before the existing 60-second unique-support
median aggregation.

| Arm | Window-level operation |
|---|---|
| `raw` | Saved `features_raw` values |
| `R` | Saved strict `features_robust_z` values; raw feature scale, local robust-z, no log or clip |
| `LR` | Feature-specific `log10` where configured, then local robust-z; no clipping |
| `RC` | Saved `R` values clipped to `[-6, 6]`; no log |
| `LRC` | Saved historical `features_projection_z` values: configured log, local robust-z, then clipping |

`LR` and `LRC` are reconstructed from the saved raw windows using the exact
frozen transform helper. Before fitting, verify that reconstructed `LRC`
matches the stored `features_projection_z` values within absolute tolerance
`1e-6`, including missing-value positions. Non-log columns in `LR` must match
`R`, and non-log columns in `LRC` must match `RC` to the same tolerance. Stop on
a contract or reconstruction mismatch.

## Comparisons

Run all five arms on the intersection of participants with complete paired EC
and EO support for every feature in every arm. Use the exact H1 aggregation,
participant-grouped nested-CV helper, model grid, and a single split schedule
reused across arms: 5 outer folds × 20 repeats, 4 inner folds,
`C={0.01,0.1,1,10,100}`, training-fold standardization, and paired participant
AUC. Do not tune any transform or model setting from these results.

Prespecified paired participant-score contrasts are:

1. `R - raw`: adding within-recording robust-z to raw inputs.
2. `LR - R`: adding the configured log before robust-z, without clipping.
3. `RC - R`: adding clipping without log.
4. `LRC - LR`: clipping effect with the configured log.
5. `LRC - RC`: log effect when clipping is present.
6. `(LRC - LR) - (RC - R)`: difference in clipping effects, the log-by-clip interaction on paired participant AUC.

Report mean paired differences and participant-bootstrap 95% intervals (2,000
draws, fixed and distinct seeds by contrast), conditional on the repeated-CV
predictions. These intervals do not include refitting variability and are not
confirmatory inference. Also report clipping counts/fractions, log-invalid
window counts, feature support, exact common participants, and all output
hashes.

## Interpretation limits

Transforms are applied locally to each recording as in the historical H1
contract; this does not represent a deployable transform fitted without access
to the test recording. AUC changes are operational stage effects under this
classifier and aggregation. The factorial contrasts can identify where
discrimination changes in this benchmark, but cannot establish a causal or
biological mechanism, remove post-hoc selection, or generalize beyond the
exposed ds005385 cohorts. Do not replace the historical MNPS 2.0 comparator
with any ablated arm.
