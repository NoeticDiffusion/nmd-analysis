# Addendum 2026-09-21: baseline-anchored matched-state C3

Status: dated exploratory addendum. Frozen after `sl_002.md` and before
`results/v1_c3_anchor_20260921/`. G3/G4 not locked. Does not reopen the
132-test panel or overwrite `v1_c3_20260921`.

The previous C3 run matched on locally fitted MNPS coordinates. That is
not a documented cross-phase physical state. This run applies a
**baseline-only** robust-z reference to the eight MNPS-used `features_raw`
columns and uses that common frame for both matching and increments.

## Question

In a within-subject frame fixed from pre-drug baseline, at approximately
the same present spectral state, does first-protocol sedation change the
one-step increment law?

Same NDT-C3 analogue as the local-chart run, now with a frozen awake
reference. Not consciousness. Not confirmatory amplitude.

## Frame (outcome-blind)

Columns: `eeg_delta`, `eeg_theta`, `eeg_alpha`, `eeg_beta`, `eeg_gamma`,
`eeg_alpha_theta`, `eeg_beta_alpha`, `eeg_sample_entropy` from
`features_raw`.

For each subject, median and 1.4826·MAD are estimated on **baseline
eligible sources only**, then applied unchanged to first-protocol
sedation and recovery. Matching and \(\Delta z/\Delta t\) use this \(z\).
Local MNPS coordinates are not concatenated (that 11-D match was too
sparse). Local `features_robust_z` is not used; it is recording-centred.

## Matching and endpoints

Same greedy 1–1 caliper rule, pair gate, Holm family, controls, seed, and
prediction as `addendum_20260921_matched_state_c3.md`, except the match
space and increments are this baseline-\(z\) 8-D frame.

Occupancy \(\mathrm{median}\|z\|_2\) is a QC/descriptive, not Holm:
unmatched occupancy tests whether sedation leaves the awake neighbourhood;
matched occupancy should be similar if matching worked.

Recovery is unmatched only in the same frame (reversibility of occupancy
and increment summaries). Recovery is not a Holm contrast.

## Not in this run

New metric families; L2/L3; LOR segmentation; confirmatory H1/H2; pooling
all phases to build the anchor.
