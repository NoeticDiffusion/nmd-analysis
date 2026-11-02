# BENCH-002-QC-001 — continuous signal-screen addendum

This addendum updates the status recorded in bench_002_qc_001_status_20261009.md.

## New bounded evidence

The V3-MULTISCALE-FIDELITY-002 continuous pilot computed descriptive signal indicators on 732 windows from the six frozen ds003838 participants. The windows came from three separate realizations: native63 average reference, Core19 average reference, and native63 linked-mastoid reference. Indicators include exact-flat-channel fraction, robust amplitude, peak-to-peak range, 30–45 Hz power, and the 48–52 Hz / 1–45 Hz power ratio. No indicator was used as a window gate.

Across these windows, median exact-flat-channel fraction was 0, median robust MAD amplitude was 16.1 µV, median peak-to-peak range was 103.3 µV, and median line-noise ratio was 0.294. These descriptive summaries do not demonstrate absence of artifacts and do not establish an artifact-free interval.

The source BIDS annotation evidence remains insufficient to set bad_interval_free=true. The continuous run used a separately amended raw-resampled input branch (polyphase 1000-to-250 Hz, with no upstream notch or 1–45 Hz bandpass), so its values are not preprocessing-matched to the existing BENCH-002 rows. The 648 prior MNE-filtered 20-second measurements remain unqualified and unchanged.

PCV local-window versus full-recording-context alpha filtering was compared on identical sample intervals. Median absolute differences were small in this six-participant pilot, but the polyphase composite edge support remains unquantified and the PCV estimate remains unqualified. The five-second anchor margin is an analysis boundary policy, not a validated filter-edge safety interval.

## Outputs

See outputs/v3_multiscale_fidelity_002_pilot_v1_20261009/continuous_window_signal_qc.csv and continuous_pcv_local_vs_full_context.csv. Full provenance, preprocessing amendment, and checksums are in that run directory's continuous_input_manifest.json and run_manifest.json.

## Decision

Signal QC is now measured and preserved separately from source annotations and filter support. Do not mark windows clean or qualify the 648 existing measurements from these results.
