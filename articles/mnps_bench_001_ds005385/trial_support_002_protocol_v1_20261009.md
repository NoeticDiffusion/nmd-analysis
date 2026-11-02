# TRIAL-SUPPORT-002 protocol v1 — 2026-10-09

## Scope and support grid

Apply the frozen FILTER-SUPPORT-001 operational guard and BAD-INTERVAL-QC-001 fields to all six pilot participants, both conditions, and loads 5/9/13. Keep Core19 average as the primary realization and native63 average separately identified. Do not read outcome labels in the QC logic; condition/load are used only after screen results to report balance.

Define the source trial interval as the first digit sample through `last_digit_sample + 3000` at 1000 Hz, following the existing BENCH-002 event contract. For each trial, retain only full windows wholly inside `[trial_start + g, trial_end - g]`, where `g` is the operational guard from FILTER-SUPPORT-001. Snap bounds inward to the existing 250 Hz sample grid. Fast-core uses 4-second windows and 4-second steps. Full v3.1 uses 20-second windows and 20-second steps, load 13 only. Do not bridge trials, impute missing support, or change estimators.

Count both nominal and guarded windows, then compute hard-QC-pass and spectral-review counts. `effective_filter_support_pass` is independent of `signal_qc_pass` and source annotation status. `measurement_qualified` remains false.

## Pilot readiness gate

For this six-person support pilot, a participant × condition × load cell is support-eligible when it retains at least four distinct trials with at least one eligible window. Apply this to fast-core at all loads and full v3.1 at load 13 only. This is an operational minimum for this bounded readiness check, not a general statistical or scientific qualification threshold. Report counts by participant, condition, load, realization, and duration, and disclose participant-level condition differences. Never treat windows within one trial or participant as independent subjects.

If a guarded window grid differs from the historical grid, recompute the bounded six-person measurements on that grid with unchanged estimators and preprocessing, then rerun fixed-window preprocessing parity checks before reconsidering cohort readiness. Do not launch the 65-person run as part of this protocol.
