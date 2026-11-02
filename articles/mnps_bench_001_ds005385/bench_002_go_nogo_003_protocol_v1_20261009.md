# BENCH-002 GO/NO-GO-003 protocol v1 — 2026-10-09

## Decision question

Decide whether the unchanged BENCH-002 measurement contracts can support a future exploratory cohort comparison under the frozen filter-support and signal-QC evidence. This gate does not authorize or launch the 65-person computation.

## Decision rules

- **HOLD** if FILTER-SUPPORT-001 finds no operational guard within 20 seconds; if the planned load-13 20-second windows fail the measured recall-boundary tolerance; if fewer than four eligible trials remain in any six-person participant × condition × load cell required by TRIAL-SUPPORT-002; or if preprocessing/value parity fails after the support grid changes.
- **GO for an exploratory run only** if the frozen support and hard signal-QC gates pass, load/condition support meets the minimum above, no unresolved differential QC issue makes the paired comparison uninterpretable, and the altered bounded six-person grid has been replayed with unchanged estimators and parity checks.
- Source annotations may remain unavailable. In that case preserve `source_bad_annotations_available=false` and `source_bad_interval_free=unknown`; a GO would be explicitly exploratory and signal-screened, never an artifact-free or qualified claim.
- Spectral review flags are not silently reclassified as artifacts. Report their condition/load balance and retain them as QC; unresolved consequential imbalance means HOLD.
- `measurement_qualified` remains false regardless of the technical gate. The fixed control→memory→control order, lack of actual voice-onset labels, and the six-person pilot's outcome exposure remain limitations.

Keep Core19 average as the primary named realization and preserve other references/surfaces separately. No full cohort, classifier, estimator tuning, or biological interpretation is part of this decision step.
