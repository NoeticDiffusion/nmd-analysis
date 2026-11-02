# BENCH-002 fast-core label correction — 2026-10-09

The saved 2026-10-08 pilot table labeled an arm fast4_mnps_v3_1, but the runner derived those values from v3_rows inside the 20-second full-v3 loop. Those values are a 20-second subset of PCV, TP, OI, and SC, and therefore only have load-13 coverage in that pilot. They do not represent the independent four-second fast-core realization.

The runner now names that derived arm v3_1_fast_core_subset_20s. The historical pilot output is preserved unchanged.

The correct independent four-second calculation is in outputs/v3_coverage_001_pilot_v1_20261008/candidate_probe_status.csv and candidate_support_summary.csv. For each frozen participant/load/surface, PCV, TP, OI, and SC each computed a valid finite value on the first four-second trial window (324 windows per load and surface; 7,776 values across four candidates, three loads, six participants, and two surfaces). This is computability evidence only; no row was qualified, and no condition contrast or classifier was run.

The follow-up control-flow correction is in run_bench_002_pilot_v1.py. Its new v2 output root emits an independent four-second fast-core arm for every supported trial window while preserving the 20-second full-v3 loop and the separately labeled 20-second fast-core subset. The historical v1 output remains unchanged. See bench_002_fast_gate_fix_validation_20261009.md for the validation boundary: saved support is confirmed, but a fresh exact numerical parity re-computation was stopped because the all-candidate production call was too expensive.
