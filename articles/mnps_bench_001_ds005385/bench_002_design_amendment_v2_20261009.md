# BENCH-002 design amendment v2 — separate full and fast-core benchmarks

**Status:** post-pilot design amendment. BENCH-002 pilot outputs and the
published task result were already inspected. This is exploratory external
dataset evidence, not untouched prospective confirmation.

## Shared scope

- Dataset: OpenNeuro ds003838 v1.0.6.
- Conditions: source task's memory and passive-control trials. Fixed block order
  remains a time/order confound and must be reported.
- Unit of inference: participant. Trial windows are aggregated within trial;
  no window is treated as an independent participant.
- Native63 and Core19 are separate realizations, never silently substituted.
- Compare each v3 arm with conventional spectral features and the raw v2 input
  baseline. The historical mapped v2.0 9D arm is reported separately with its
  actual feature mapping and degenerate robust-scale behavior documented in
  the legacy mapping audit.
- No classifier run or full-cohort execution is authorized by this amendment.
  The six pilot participants are outcome-exposed. Consider the remaining cohort
  only after the multiscale fidelity protocol and BENCH-002-QC-001 are reviewed
  and the analysis contract is frozen.

## BENCH-002A — full representation, load 13

**Question:** under the existing 20-second contract, does the full v3.1
representation discriminate memory from passive-control trials better than
the historical v2.0 9D realization?

- Realization: [PCV, TP, AR(9), NIE, RD, OI, SC, ED] at 20 seconds.
- Primary endpoint, if later executed: participant-held-out AUROC difference,
  full-v3 minus historical-v2, with one paired participant-level contrast.
- Conventional and raw-v2 input models are required comparators. Their
  comparisons are secondary and use Holm correction as one named comparator
  family.
- No coordinate is silently dropped or filled with zero. Unsupported values
  remain missing and support is reported per realization.

## BENCH-002B — fast representation, 4 seconds

**Question:** does the independent fast-core realization carry memory/control
discrimination across loads 5, 9, and 13?

- Realization: [PCV, TP, OI, SC] at four seconds, computed independently of
  20-second full-v3 support.
- Primary endpoint, if later executed: macro-average of the three
  participant-held-out load-specific AUROCs. Compare fast-core with raw-v2
  input features as the single primary paired contrast.
- Conventional spectral comparison is secondary. Load-specific contrasts are
  secondary and use Holm correction across the three loads.
- The full-v3 model is not a comparator for loads 5 or 9 because its frozen
  20-second support does not exist there.

## Shared validation and reporting contract

- If the study proceeds, use outer grouped cross-validation by participant;
  all label-informed fitting and hyperparameter selection stays inside training
  participants. Report per-participant held-out scores and the participant
  distribution, not only pooled windows.
- Keep trial aggregation, feature order, missing-data policy, random seeds,
  tuning grid, and comparator feature sets frozen before a new classifier fit.
- Report support counts and task order alongside AUROC. No result from the
  fixed block order alone establishes a causal memory effect or prospective
  replication.
- No benchmark result qualifies the measurement for biological use or proves
  equivalence across durations, references, or channel sets.

## Current decision

BENCH-002A has structural 20-second support only for load 13. BENCH-002B has a
separate computable four-second path across all three loads. Neither path is
yet scientifically qualified, and no 65-participant run should start until
fidelity/QC review and a final design freeze.
