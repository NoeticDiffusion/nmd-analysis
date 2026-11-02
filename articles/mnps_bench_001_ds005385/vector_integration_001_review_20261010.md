# VECTOR-INTEGRATION-001 independent implementation review

The independent reviewer found no execution blocker in the bounded protocol,
runner and five focused tests before pilot execution. The review checked the
following scientific and implementation risks:

- B/C/D use exactly the same eligible held-out origins. Both 20 s contexts lie
  inside the actual 96 s history span available to B, including the 16 s stale
  context control. Intermediate horizon-2 gaps and missing coordinates exclude
  forecast rows without changing stored candidate-local measurements.
- Standardization and all learned models fit only training participants in each
  leave-one-participant-out fold. Participant paired bootstrap avoids treating
  overlapping forecast origins as independent inference units.
- The scalp-six realization is explicit. The full original eight-signal raw
  prefix is hash-checked before selection; original sensor/estimator/reference
  and support information is retained in measurement JSONL.
- AR's analysis median has an explicit reduction name. The original vector of
  nine adjacent activity changes remains stored.
- Window-local PCV is available at the window right edge, with unknown boundary
  fidelity. The upstream FIR has 2 s past support and 1 s group delay; immediate
  four-second targets share raw filter support with origin features.

Two interpretations must accompany the results. The conventional comparison
uses conventional descriptors plus the current fast-state persistence anchor;
it is not a conventional-only predictor. The fast-input ablations remove a
coordinate's historical predictors while retaining that coordinate's current
value as its target persistence anchor. They do not remove the entire construct.

The wrong-time context is one prespecified past displacement, not evidence from
a randomized context distribution. Positive C gains would show complementarity
of this fixed representation and support scale, not an effect of granting more
elapsed history. All axes, models and descriptive intervals must be reported.
None of these implementation checks establishes biological qualification.

## Final saved-artifact review

After execution, the independent reviewer verified extraction and analysis
hashes, 780 fast and 240 context windows, all selected vectors, the six-sensor
and reference contract, raw nine-value AR outputs and future-perturbation pass.
All 15 models share 300 origin/horizon cases (160 at 4 s and 140 at 8 s).
Prediction truth and persistence anchors match the saved trajectories.
Every participant/per-axis RMSE, pooled/macro RMSE and paired effect was
recomputed without an aggregation or serialization discrepancy.

No axis establishes an improvement of current context C over both B and D.
At 4 s all primary per-axis intervals cross zero; at 8 s TP and SC are worse
than B while PCV/OI remain inconclusive, and all D comparisons cross zero.
AR2 has the lowest pooled error. The final review found no blocker and limits
the negative finding to this fixed architecture and bounded pilot.
