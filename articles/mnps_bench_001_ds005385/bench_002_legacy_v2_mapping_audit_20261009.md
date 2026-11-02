# BENCH-002 historical v2 9D mapping audit — 2026-10-09

## Question

The six-participant pilot has near-zero historical v2 subcoordinates. Are these
zeros caused by missing-feature fallback, or by mapped features that collapse
under the saved robust standardization?

## Frozen evidence inspected

- Six-participant BENCH-002 pilot output:
  outputs/bench_002_pilot_v1_20261008/event_window_features.csv
- Per-realization projection baselines:
  outputs/bench_002_pilot_v1_20261008/normalization_baselines.json
- Historical definition: config_ingest_common_eeg.yaml, MNPS 9D version 2.0.
- Projection implementation: project_features_v2 in mndm/projection.py.
- No original pilot output was edited.

## Findings

The pilot table contains 5,504 event windows across the six participants and
two surfaces. All nine historical 9D columns are finite for all 5,504 rows.
All ten features used by the configured v2.0 mappings appear in the recorded
projection baselines for all 12 participant/surface realizations. The mapping
does not use an unavailable-feature fallback in this pilot extraction.

The exported values and projection baselines show:

| Coordinate | Configured input | Exact zeros / rows | Baseline scale finding |
|---|---|---:|---|
| m_a | eeg_delta, eeg_theta | 5,503 / 5,504 | both features have zero robust scale in all 12 realizations |
| m_e | eeg_alpha | 5,504 / 5,504 | zero robust scale in all 12 realizations |
| m_o | eeg_beta_alpha | 0 / 5,504 | nonzero scale in all 12 |
| d_n | eeg_gamma | 5,504 / 5,504 | zero robust scale in all 12 realizations |
| d_l | eeg_hjorth_mobility | 0 / 5,504 | nonzero scale in all 12 |
| d_s | eeg_alpha_theta | 1 / 5,504 | nonzero scale in all 12 |
| e_e | eeg_permutation_entropy | 0 / 5,504 | nonzero scale in all 12 |
| e_s | eeg_hjorth_complexity | 0 / 5,504 | nonzero scale in all 12 |
| e_m | embodied_arousal_proxy | 0 / 5,504 | nonzero scale in all 12 |

The implicated input columns are present and finite in the event export. The
zero-coordinate pattern therefore indicates a degenerate/near-degenerate
standardization outcome for the mapped spectral features, not a missing-input
fallback. The one nonzero m_a row is retained as observed; this audit does not
replace it with a stronger claim of universal collapse.

## Interpretation

Historical v2 outputs in this pilot do not represent nine equally informative
streams: m_e and d_n are exactly zero throughout this export, and m_a is zero
for all but one row. This matters when describing the legacy-v2 comparison.
It does not authorize changing the frozen historical mapping or recomputing
the old benchmark with a new normalization contract. BENCH-002A/B remain
separate post-pilot analyses, and the historical arm should be labeled with
its actual saved v2.0 mapping and normalization behavior.

## Limits

This is a mapping and saved-baseline audit, not a new EEG ingest. It establishes
feature availability and zero-scale provenance recorded by the pilot; it does
not identify the biophysical meaning of those features or qualify the
alternative fast-core measurements.
