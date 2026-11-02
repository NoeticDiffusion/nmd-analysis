# LEGACY-LOSS-002 — log-only extension

Date: 2026-10-08  
Status: post-run exploratory extension; not confirmatory and not outcome-blind.

## Why this extension exists

The frozen five-arm LEGACY-LOSS-002 analysis estimates the log contrast only
conditional on within-recording robust-z (`LR - R`). It does not estimate a
standalone log-only contrast against raw inputs. This extension adds exactly
one arm to answer that narrower question. The five-arm results had already
been inspected when this extension was specified, so it is explicitly
post-hoc.

## Frozen contrast and implementation

Compare the saved raw arm with a `L` arm built from the same ten historical
features. Apply feature-specific `log10` only to the four columns identified
by the frozen transform contract (`eeg_delta`, `eeg_theta`, `eeg_alpha`,
`eeg_gamma`). Do not apply within-recording robust-z or clipping. Preserve the
other six columns unchanged.

The source arm values are the validated 60-second support medians from the
primary LEGACY-LOSS-002 run. Because every log-configured source window was
positive, and `log10` is strictly increasing, applying it to a median equals
the median of the logged values (including a support-weighted median). The
window-level nonpositive counts are rechecked as zero before creating `L`.

Use the exact complete 100-participant set, feature order, outer/inner split
schedule, nested grouped-CV helper, model grid, training-fold standardization,
and state row order from H1 / the primary five-arm analysis. Refit both `raw`
and `L` in the extension. The extension's re-fitted raw out-of-fold
probabilities must match the primary saved raw predictions exactly (within
absolute tolerance `1e-15`) before the contrast is reported.

The sole prespecified contrast is paired participant AUC `L - raw`, with a
2,000-draw participant bootstrap interval (seed 20261014), conditional on the
repeated-CV predictions. It does not include refitting variability. No
additional contrasts, feature selection, preprocessing changes, classifier
tuning, or EEG processing are permitted in this extension.

## Provenance and interpretation

Bind the extension freeze to this protocol and script, the primary
LEGACY-LOSS-002 freeze, summary, run manifest, raw feature-value table,
prediction table, and H1 helper/source freeze. Validate the primary output
hashes before use. Read no EDF and recompute no EEG features.

This is an operational, post-hoc contrast for the already exposed ds005385
cohort. It can estimate whether the configured logarithm alone changes
discrimination under this exact representation, aggregation, classifier and
split schedule. It cannot establish a biological mechanism, explain the
historical loss causally, or replace the MNPS 2.0 comparator.
