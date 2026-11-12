# SL-004 ds004100 candidate screen — frozen protocol v1

**Status:** frozen before candidate extraction. Experimental, descriptive screen; it does not change canonical MNPS v2 or qualify a candidate for MNPS 3.4.

## Dataset snapshot

- Local root: `K:\ExternalReceivedDatasets\openneuro\ds004100`.
- Dataset DOI: `doi:10.18112/openneuro.ds004100.v1.1.3` (OpenNeuro snapshot v1.1.3).
- `BIDSVersion: 1.4.0` is the BIDS specification version, not the dataset snapshot version.
- DataLad dataset UUID: `85849071-ea4a-4026-9371-bbadce626464`.
- The local copy contains `.datalad/config` but no `.git` directory, so no local repository commit SHA is available. The run manifest records metadata-file SHA-256 values and an ordered EDF path/size inventory hash.
- Citation: Bernabei JM, Li A, Revell AY, Smith RJ, Gunnarsdottir KM, Ong IZ, Davis KA, Sinha N, Sarma S, Litt B. *HUP iEEG Epilepsy Dataset*. OpenNeuro ds004100 (2022). doi:10.18112/openneuro.ds004100.v1.1.3.

## Question and scope

Test whether the three frozen FABLE descriptors show reproducible, within-patient ictal–interictal changes in this dataset. SEEG is primary; ECoG is a separate modality analysis. Do not pool modalities. A paired contrast establishes a regime difference only; it does not establish information beyond the existing coordinates or predictive value.

Existing ds004100 MNPS exports are not used as comparators because the audited exports do not provide verified event-contained source windows and comparable fixed contact/reference support. A separate patient-held-out prediction experiment would be required to claim incremental predictive value. This screen reports only participant-level paired-change correlations with the prespecified simple spectral comparators as diagnostics.

## Eligible data and windows

- Use BIDS task `ictal` with its one `sz onset`–`sz offset` event interval; use task `interictal` as the labeled interval for the full recording.
- Fix the contact set separately for each patient and modality to the exact intersection of `status=good` SEEG or ECoG labels across all included ictal and interictal runs. Preserve the ordered labels and hash. Do not pool contact sets across patients.
- Use non-overlapping 8 s windows anchored at each EDF run start: `[k×8,(k+1)×8)`. Keep a window only when it is wholly within the labeled interval and at least 10 s from both recording edges and, for ictal, both event edges.
- A patient–modality pair is eligible only when the fixed contact set is nonempty and at least one guarded window exists in each task. Runs/events without an eligible window remain in support/QC output and contribute no run summary.
- Current metadata-only eligibility under this rule is 33/35 SEEG pairs and 19/20 ECoG pairs. Regenerate and store the final support counts with the candidate run.

## Reference realizations

Compute all candidates and comparators twice on exactly the same contacts, windows, preprocessing, and support:

1. **Primary:** recorded values as delivered, labeled `recorded_reference_unknown` because the source hardware reference is absent from BIDS metadata.
2. **Required sensitivity:** common-contact average reference over the fixed patient–modality contact set, labeled `common_contact_average_reference`.

Report both realizations side-by-side. Report participant-level direction agreement and the paired change in the estimated ictal–interictal contrast between references. A direction reversal or substantial effect shift is evidence of reference dependence. Do not interpret either as recovering the physical acquisition reference.

## Boundary-safe preprocessing and support

Use experimental realization ID `FABLE_DS004100_BOUNDARY_SAFE_v1`:

1. Read only the fixed good contacts and convert to microvolts.
2. Resample to 250 Hz with `scipy.signal.resample_poly` using its default finite Kaiser FIR. For interictal recordings, resample the full run; its output grid starts at EDF time zero. For ictal recordings, first isolate the raw samples from the BIDS onset sample through the offset sample, add reflected padding from that event only, and choose the left pad so the resampled event segment aligns to the EDF-anchored 250 Hz grid. The polyphase half-support is at most 0.040 s for source rates 256, 500, 512, and 1024 Hz. No samples from outside an ictal event enter its resampling filter.
3. Apply the primary or average-reference transform on the fixed contact set, then filter each labeled segment separately with reflected same-segment padding. No filter call may contain samples from both ictal and nonictal intervals.
4. Apply MNE 1.6.1's zero-phase FIR notch at the dataset's 60 Hz line frequency, then its zero-phase 1–45 Hz FIR bandpass. Use the library defaults (`notch_widths=None`, 1 Hz notch transition; automatic FIR length and transition bands; Hamming/firwin; reflected-limited padding). Do not use the scalp pipeline's 50 Hz notch.
5. For `burst_alpha`, apply the fourth-order 8–12 Hz Butterworth SOS zero-phase filter separately within each ictal-event/interictal-run segment. Add 10 s reflected same-segment padding, compute the analytic Hilbert transform, and crop the padding before calculating window values. The FFT Hilbert transform has no finite support, so it must never receive a segment spanning two labels. Its value within a window may depend on other samples in that same event/run; treat it as a state descriptor, not a prospective forecast.
6. Use the 10 s recording/event margins for every candidate and comparator. The synthetic impulse audit in the frozen environment (MNE 1.6.1, 250 Hz) measured effective half-support at relative amplitude `1e-6` of 3.300 s for the 60 Hz notch, 1.648 s for the 1–45 Hz FIR, and 3.192 s for the 8–12 Hz SOS filter. Adding the maximum 0.040 s resampling support gives 8.180 s; 10 s leaves 1.820 s for sample-grid alignment and edge effects.

## Frozen measurements

Compute per 8 s window from the same preprocessed contact matrix:

- **`burst_alpha`:** per-contact standard deviation divided by mean of the 8–12 Hz Hilbert envelope within the 8 s window; median across contacts. Filter and Hilbert are run on the separate labeled segment, with 10 s reflected padding for the Hilbert transform.
- **`paf_cog`:** Welch PSD per contact (4 s Hann segments, 50% overlap, constant detrend), median PSD across contacts at each frequency, then the power-weighted centroid over 7–13 Hz. Name/report it as a band centroid; do not interpret it as an alpha peak without a separate resolved-peak diagnostic.
- **`sp_disp`:** `1.4826 × MAD` across contacts of `log10` per-contact variance of the 1–45 Hz window.

Same-window comparators, frozen before candidate extraction:

- `alpha_power_log10`: `log10` of the median across contacts of 8–12 Hz analytic-envelope mean-square power.
- `broadband_power_log10`: median across contacts of `log10` 1–45 Hz window variance.
- `broad_spectral_centroid`: power-weighted centroid of the median-contact Welch PSD over 1–45 Hz, using the same Welch settings.

Do not standardize within recording or tune any estimator, support rule, or threshold after viewing candidate values.

## Aggregation and inference

1. For every candidate/comparator, reference realization, and run/event, summarize its finite eligible windows by the median. Retain window values and support.
2. Within participant and task, take the median across eligible run/event summaries. Compute one participant-level `ictal − interictal` contrast; participants receive equal weight regardless of run or window count.
3. Primary tests are two-sided exact sign tests on the nonzero participant contrasts in SEEG `recorded_reference_unknown`; Holm-adjust the three candidate p-values as one family. Report median participant contrast, 95% participant-bootstrap percentile interval (10,000 resamples; seed 20261111), fraction of patients in each direction, and all participant contrasts.
4. ECoG is reported separately with the same summaries and a separate Holm family; do not pool it with SEEG.
5. For reference sensitivity, report the same effect/interval/direction summaries under common-contact average reference and the participant-level difference between the two reference-specific contrasts. Do not use the sensitivity as an extra primary test family.
6. Correlate participant-level candidate changes with the three simple-comparator changes in primary SEEG/reference. Report Spearman correlations with participant-bootstrap intervals as diagnostics only. Do not claim incremental value from these correlations or paired contrasts.
7. No classifier or patient-held-out prediction model is part of this screen.

## Required outputs

Preserve a separate experimental output root with: input/protocol/code hashes; per-recording support and filter-QC; per-window values and support; run/event medians; participant contrasts; reference comparison; primary/secondary statistics; comparator-change correlations; and a concise report. Keep MNPS v2 frozen.
