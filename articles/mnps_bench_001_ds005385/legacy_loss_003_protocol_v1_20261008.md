# LEGACY-LOSS-003 — Historical transform component ablation

Date: 2026-10-08  
Status: exploratory, post-hoc method analysis; freeze inputs, code, protocol,
and runtime before computing the new arm predictions.

## Question and scope

Using the same 200 saved H1 recordings from 100 selected ds005385 participants,
estimate how feature-specific log transformation, recording-local robust-z,
and the historical clipping step relate to EC/EO discrimination under the
frozen H1 classifier and participant-grouped split schedule. This follows
LEGACY-LOSS-002 and adds a log-only arm so the log operation is directly
observable without robust-z.

This is a post-hoc methodological decomposition of exposed outcomes. It does
not establish a biological mechanism, repair or replace the historical MNPS
2.0 comparator, or support a confirmatory claim.

## Frozen inputs and transforms

Read only the 200 H1 HDF5 files named in the frozen H1 analysis manifest. Verify
all source hashes before and after the run. Do not read EDFs or recompute EEG
features. Use H1's ten ordered `RAW_INPUT_FEATURES`, saved per-window feature
surfaces, per-feature transform metadata, `[start, end)` window grid, and
60-second unique-support median aggregation.

For a feature whose saved contract includes `log10`, apply base-10 logarithm;
non-positive finite values become missing as in the frozen NMD transform
helper. For other features the log-only arm is the saved raw surface. Use the
frozen strict local robust-z operation, and the historical clipping threshold
of 6 after robust-z. The six arms are:

| Arm | Window-level operation |
|---|---|
| `raw` | Saved `features_raw` values |
| `L` | Configured `log10` only; no robust-z or clipping |
| `R` | Raw-scale local robust-z only; no log or clipping |
| `LR` | Configured `log10`, then local robust-z; no clipping |
| `RC` | Local robust-z, then clipping to `[-6, 6]`; no log |
| `LRC` | Frozen historical surface: configured log, local robust-z, then clipping |

`RC` is retained as a sixth diagnostic arm in addition to the five requested
arms. It permits a direct comparison of clipping with and without the
feature-specific log and identifies the log-by-clipping interaction; without
it that interaction is not estimable. It is already part of the preceding
LEGACY-LOSS-002 design.

Before model fitting, reconstruct `R`, `LR`, `RC`, and `LRC` from saved raw
windows with the exact frozen transform helper. Require `R` and `LRC` to match
their stored HDF5 surfaces to absolute tolerance `1e-6`, including finite/missing
positions. Require non-log `L` to match raw, non-log `LR` to match `R`, and
non-log `LRC` to match `RC` to the same tolerance. Stop on any mismatch.

## Evaluation

Use one common participant-complete set across all arms and both states; report
support and incomplete participants before restriction. Preserve all ten
feature identities and order. Use the frozen H1 model and nested participant-
grouped schedule: 5 outer folds × 20 repeats, 4 inner folds, and
`C={0.01,0.1,1,10,100}`. Standardize within training folds. Generate the split
schedule once and reuse it unchanged for all six arms. The participant is the
inference unit; each participant's EC and EO recordings remain in the same
fold.

Report participant-paired AUC and 2,000-draw participant-bootstrap 95%
intervals conditional on repeated-CV predictions. Prespecified paired
contrasts are:

1. `L - raw`: log effect without robust-z.
2. `R - raw`: robust-z effect without log.
3. `LR - L`: robust-z effect after log.
4. `LR - R`: log effect after robust-z.
5. `(LR - L) - (R - raw)`: log-by-robust-z interaction.
6. `RC - R`: clipping effect without log.
7. `LRC - LR`: clipping effect after log.
8. `LRC - RC`: log effect with clipping.
9. `(LRC - LR) - (RC - R)`: log-by-clipping interaction.
10. `LRC - raw`: full historical transform versus raw.

Use a fixed and distinct bootstrap seed for each contrast. These intervals do
not include model-refitting uncertainty and are not confirmatory inference.
Also report configured log features, non-positive windows before log,
clipping counts/fractions, window support, common participants, all source and
output hashes, and the exact runtime versions.

## Interpretation limits

Recording-local robust-z uses the full recording's windows, matching the
historical transform contract; it is not a transform fitted only on training
participants. Contrast effects describe this exposed dataset, support rule,
aggregation, classifier, split schedule, and pinned runtime. They cannot
establish causality, biological mechanism, cross-dataset behavior, or whether a
transform is generally beneficial. Do not tune the estimator, transforms,
model grid, support rule, or claim based on these outcomes.
