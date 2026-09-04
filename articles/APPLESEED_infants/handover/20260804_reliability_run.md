# APPLESEED reliability run handover

## Run
- Input: `data/raw/neuralmanifolddynamics_ds003710_20260804_123154`
- Command: `python articles/APPLESEED_infants/src/run_appleseed_analysis.py --output-dir articles/APPLESEED_infants/results/appleseed_reliability_20260804`
- Contract: 48 H5 files, 13 children, 11 complete longitudinal children, all geometry statuses `ok`.
- Coordinate constraint: only subject-anchored coordinate layers are available.

## Primary outcome
None of the nine primary endpoints showed FDR-significant session 1--2 difference or a strong ICC(A,1); confidence intervals were wide. None of the 18 prespecified longitudinal contrasts survived FDR correction. These are limited-sample findings, not evidence of no developmental change or universally poor reliability.

## Outputs
- `01_session_metrics/`: session rows, QC rows, provenance manifest.
- `02_reliability_longitudinal/`: reliability, longitudinal, and retest-mean sensitivity CSV/JSON.
- `03_event_locked_exploratory/`: child-aggregated optional event contrasts.
- `04_figures/`: coverage, ICC, and trajectory PNGs.

## Important implementation boundary
Inference is based on child-level paired session summaries. The event analysis additionally pools repeated sessions within child before sign-flip permutation, preventing repeated-session pseudo-replication.

## Next scientific step
Use a larger repeated-recording infant cohort to estimate reliability precisely, test reference/anchoring stability, and predefine a smaller endpoint set tied to independent developmental outcomes.
