# Handover from NMD — RichSleep EAP v2 delivery received and validated

**Date:** 2026-07-13
**From:** NeuralManifoldDynamics
**To:** NoeticDiffusion analysis / `RichSLeep_EAP_v2`
**Status:** delivery received, schema/coverage validated (script
`src/01_validate_v3_delivery.py`, all checks pass); follow-up to
`articles/Rythmic_Variance_Control_in_Sleep_theory/handover/handover_To_nmd_sleep_eap_phase2_data_requirements.md`

## Summary

NMD delivered six new RichSleep data products, addressing every open item
raised in the phase-2 data-requirements handover except cross-dataset
(ANPHY/BOAS) replication (RichSleep-only, as expected — ANPHY is ECG-only,
BOAS mostly lacks respiration). Five were copied into
[data/](../data) directly; a sixth, `non_event_risk_v1/`, was present
alongside the others on `K:/ExternalReceivedDatasets/RichSleep/` (per each
subject's `xnNNN_sleep_eap_phase2_meta.json`, `non_event_risk_contract:
"non_event_risk_v1"`) but had not been copied into the article folder yet —
copied in during Phase 1 of this article's implementation (2026-07-13). All
six were validated against the 24-subject RichSleep cohort; results in
`results/rvc_sleep_v2_20260713/01_validate_v3_delivery/`.

| Requested (phase-2 handover) | Delivered | Status |
|---|---|---|
| SO-amplitude, spindle amplitude/sigma-power, SO-spindle coupling index, spindle frequency | `phase_resolved_v3/` | delivered in full |
| Continuous phase time series | `phase_continuous_v1/` | delivered in full |
| Genuine non-event risk set | `non_event_risk_v1/` | delivered in full (see §6) |
| Multi-stage extension (N3 slow oscillations, REM theta) | `event_phase_n3_so_v1/`, `event_phase_rem_theta_v1/` | delivered in full |
| Cross-dataset replication (ANPHY/BOAS) | — | not delivered (expected; RichSleep-only) |

## 1. `phase_resolved_v3/` — the real qz(t)/bqg-test inputs

Same 23,029-event N2-spindle catalog as the old `event_phase_v2`
(RVC_SLEEP_peak_analysis) — confirmed by an exact bit-identity check on all
13 shared columns after sorting by `(subject, onset_sec)` — extended from
14 to 33 columns. New columns: `frequency_hz`, `amplitude`, `sigma_power`,
`sigma_power_z_n2`, `sigma_reference_median`, `sigma_reference_mad_scale`,
`strength_qc_flag`, `so_onset_sec`, `so_upstate_sec`, `so_amplitude`,
`so_phase_at_spindle_peak`, `so_spindle_latency_sec`,
`so_spindle_coupling_score`, `so_partner_missing`, `so_coupling_qc_flag`,
`event_phase_contract`, `strength_source_path`, `onset_match_tolerance_sec`.

**Coverage caveat:** only 11.8% of all 23,029 spindles (2,708) have a
matched SO partner (`so_partner_missing == 0`); of the 190 geometry-valid
events used in the efficacy test, only **25 events across 15 subjects**
are SO-coupled. The true SO-coupling-score test is therefore only usable
as a small, explicitly-labeled exploratory check, not a primary,
adequately-powered family — the well-powered primary efficacy proxy is
intrinsic spindle strength (`sigma_power_z_n2`/`amplitude`), available for
essentially all 190 events. `sigma_power_z_n2` is heavily right-skewed
(mean 42.4, median 27.9, max 764.7) and will need a log1p or rank
transform before use in a linear model.

## 2. `slow_oscillation_v1/` — raw SO catalog, N2+N3

68,386 SO events (26,377 N2, 42,009 N3), no phase columns (this is the
detector output that `phase_resolved_v3`'s SO-coupling and
`event_phase_n3_so_v1` are both built from). All QC flags `ok`.

## 3. `phase_continuous_v1/` — continuous phase stream

24 subjects, 8,834,120 rows total (~10.2 h/night/subject) at a confirmed
10 Hz sampling rate, columns `phi_cardiac`/`phi_resp`/`phi_rem_theta` +
validity flags. `cardiac_phase_valid`/`resp_phase_valid` ≈ 100%;
`rem_theta_valid` ≈ 8.2% (REM-only, as expected). This is the genuine
background/risk-set stream the phase-2 handover asked for — enables a
proper phase-binned hazard model for spindle-onset timing (exposure = time
spent in each phase bin) and a circular time-shift surrogate null, instead
of only a subject-rotation permutation test on discrete event phases.

## 4. `event_phase_n3_so_v1/` — N3 slow oscillations, phase-resolved

42,009 events (exactly the N3 subset of `slow_oscillation_v1` — confirmed
by count match), phase-resolved against cardiac and respiration at **both**
the SO trough and the SO upstate (36 columns: `phi_cardiac_trough`,
`phi_resp_trough`, `phi_cardiac_upstate`, `phi_resp_upstate`, plus RR
interval, inhale flag, QC flags per anchor point). 100% valid / QC-ok
across all rows.

## 5. `event_phase_rem_theta_v1/` — REM theta, phase-resolved

2,412 REM-theta 30 s epochs, phase-resolved against cardiac, respiration,
and theta itself. 100% valid on all phase columns, but per-subject N is
uneven (min 2, median 84, max 219; 1 subject has <5 epochs and will be
excluded from any per-subject-only test arm).

## 6. `non_event_risk_v1/` — the genuine non-event risk set

24 files, 66,827 rows total (492–7,698/subject), matched-sampling design:
100% `stage == 2` (N2), 100% `selection_status == "selected"`, 100%
`cardiac_phase_valid`/`resp_phase_valid`, stratified across four
`time_of_night_quartile` bins, sampled with a fixed per-subject `seed` and
excluding a 30 s margin (`exclusion_margin_sec`) around every real spindle
onset. Ratio to real spindle counts is ≈2.9:1 overall (confirmed per-subject,
e.g. xn001: 669 risk rows / 223 spindles ≈ 3.0).

This is a properly-constructed case-control risk set, not a raw continuous
exposure stream — it directly supports the hazard-model test as "real onsets
(cases) vs. matched N2 non-event timepoints (controls), do their
cos(phase)/sin(phase) distributions differ" via cluster-robust logistic
regression, without needing a separate continuous-hypnogram exposure
calculation.

### Caveat discovered while integrating this: the geometry H5's `labels/stage` is not a continuous hypnogram

While building the exposure denominator for the hazard model, we first tried
using each subject's per-window `labels/stage` array in the existing
geometry H5 (`data/raw/neuralmanifolddynamics_RichSleep_20260709_100219/sub-
xnNNN_sleep_sleep/sub-xnNNN_sleep_sleep.h5`, `window_start`/`window_end` +
`labels/stage`). This turned out to be **sparse, not continuous**: only 177
of each subject's 1,190 30 s windows carry a real stage value (the rest
default to `-1`), and 177 is exactly the count of that subject's
`jacobian_9d_centers` — i.e. `labels/stage` is populated only at the
windows where a local Jacobian fit succeeded, not across the full night.
Treating it as a continuous hypnogram undercounted true N2 exposure by
roughly two orders of magnitude (~0.3 h/subject vs. a physiologically
plausible ~1–2 h). We are not requesting a fix (the properly-built
`non_event_risk_v1` risk set already solves the same problem better), but
flagging it in case `labels/stage` is ever relied on elsewhere as if it were
continuous.

## Net effect for `RichSLeep_EAP_v2`

This delivery unblocks the full plan in
`.cursor/plans/richsleep_eap_v2_article_aa3119f9.plan.md`: a cross-carrier
phase-locking comparison (N2-spindle onset/peak, N3-SO trough/upstate,
REM-theta), a hazard-model strengthening of the spindle-onset test, and the
N2-spindle intrinsic-strength × phase-alignment efficacy test. No further
NMD re-run is required for the current plan's scope.

## Still open (not requested in the current plan)

Cross-dataset (ANPHY/BOAS) replication of any of the above remains
unavailable and is not expected to become available (ANPHY: ECG-only;
BOAS: respiration mostly missing) — any future replication attempt would
need a different dataset entirely, not a RichSleep re-run.
