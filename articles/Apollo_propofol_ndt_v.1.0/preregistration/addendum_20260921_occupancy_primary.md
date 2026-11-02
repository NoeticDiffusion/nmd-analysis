# Addendum 2026-09-21: occupancy / state relocation as Apollo primary line

Status: dated freeze after `sl_003.md` and `sl_004.md`. Occupancy for first
sedation − baseline and recovery − baseline was already inspected as a
descriptive QC in `results/v1_c3_anchor_20260921/`. This addendum **promotes
that exact scalar** to the article primary line. It is therefore
exploratory/post-hoc relative to the 2026-09-20 preregistration. G3
independent review and G4 lock were not completed. This is not a
confirmatory H1/H2 lock and does not reopen the 132-test panel.

Do not search for an improved state-distance. Do not lower the matched-state
n=10 gate. NDT-C3 remains OPEN / NOT_TESTABLE.

## Scalar (frozen)

Unmatched occupancy from the baseline-anchor pipeline:

- eight MNPS-used `features_raw` columns as in
  `addendum_20260921_c3_baseline_anchor.md`;
- baseline-only median and 1.4826·MAD, applied unchanged to later phases;
- eligible sources: finite \(z_t\) and a valid one-step successor
  (\(\Delta t\in[3.8,4.2]\) s);
- occupancy = median Euclidean radius \(\mathrm{median}\|z\|_2\) over those
  sources.

This is “where is the system relative to this person’s awake reference?”,
not identified MNPS, not Itô dynamics, not consciousness.

## Contrasts

1. **Primary:** first_protocol_sedation − pre_drug_baseline.
   Prediction: later > earlier. Exact two-sided sign test; Wilcoxon
   reported. One primary, so no Holm. Reporting gate: ≥10 subjects with a
   nonzero difference. Effect: paired Cohen \(d_z\) and median difference
   with 10 000-subject percentile bootstrap, seed 20260920.
2. **Ordered secondary (not replacements):** later_protocol_sedation −
   baseline; recovery − baseline. Same scalar and grain. Two-sided.
3. **C3 support exhibit (already computed, not a new test):** match
   fraction and pair counts from `v1_c3_anchor_20260921`. Reported because
   common-support collapse is why C3 is NOT_TESTABLE, not because matching
   is being reopened.

## Not in this freeze

New metrics; L2/L3; Jacobian α as primary; confirmatory local-chart
`b`/`a`; LOR/ROR segmentation; lowering the matched n=10 gate;
reinterpreting C3 as falsified.
