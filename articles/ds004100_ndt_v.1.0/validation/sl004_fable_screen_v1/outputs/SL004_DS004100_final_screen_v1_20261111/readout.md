# SL-004 final candidate screen — ds004100

**Exploratory, unqualified measurement screen. MNPS v2 remains frozen.** Candidate values and paired contrasts were computed under the frozen experimental realization.

- Snapshot DOI: `doi:10.18112/openneuro.ds004100.v1.1.3`; BIDS specification: `1.4.0`; DataLad UUID: `85849071-ea4a-4026-9371-bbadce626464`.
- Eligible pair support before signal QC: {'ecog': 19, 'seeg': 33} (10 s margins; SEEG and ECoG kept separate).
- Screened recordings: 295; candidate window rows across both reference realizations: 10946; processing errors: 0.
- Primary tests are exact two-sided sign tests on participant-level SEEG contrasts under `recorded_reference_unknown`, Holm-adjusted across the three candidates. The sign test assesses direction consistency; effect magnitude is reported by the median contrast and participant-bootstrap interval.
- ECoG is a separate sensitivity analysis, with its own Holm family. It is not pooled with SEEG.
- Both reference realizations use identical contact sets and windows. Reference sensitivity is reported descriptively; it does not recover the physical hardware reference.
- Comparator correlations are diagnostics only. No patient-held-out prediction test was run, so this screen cannot establish incremental predictive value or superiority over omitted MNPS coordinates.

## SEEG primary: recorded reference unknown

| acq | reference | metric | n_participants | median_participant_delta | mean_participant_delta | bootstrap_95_low_median | bootstrap_95_high_median | n_positive | n_negative | n_zero | positive_fraction_nonzero | exact_two_sided_sign_test_p | holm_p_primary_family |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seeg | recorded_reference_unknown | burst_alpha | 33 | -0.01157 | -0.008113 | -0.02041 | -0.006301 | 8 | 25 | 0 | 0.2424 | 0.004551 | 0.01365 |
| seeg | recorded_reference_unknown | paf_cog | 33 | 0.04155 | 0.07178 | -0.1407 | 0.3077 | 19 | 14 | 0 | 0.5758 | 0.4869 | 0.4869 |
| seeg | recorded_reference_unknown | sp_disp | 33 | 0.02007 | 0.01291 | -0.002034 | 0.0565 | 21 | 12 | 0 | 0.6364 | 0.1628 | 0.3255 |

## SEEG reference sensitivity: common-contact average reference

| acq | reference | metric | n_participants | median_participant_delta | mean_participant_delta | bootstrap_95_low_median | bootstrap_95_high_median | n_positive | n_negative | n_zero | positive_fraction_nonzero | exact_two_sided_sign_test_p | holm_p_primary_family |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seeg | common_contact_average_reference | burst_alpha | 33 | -0.01233 | -0.009311 | -0.02166 | -0.005805 | 10 | 23 | 0 | 0.303 |  |  |
| seeg | common_contact_average_reference | paf_cog | 33 | 0.09583 | 0.06849 | -0.01649 | 0.2195 | 19 | 14 | 0 | 0.5758 |  |  |
| seeg | common_contact_average_reference | sp_disp | 33 | 0.006424 | 0.002961 | -0.009302 | 0.02102 | 20 | 13 | 0 | 0.6061 |  |  |

## ECoG separate modality analysis

| acq | reference | metric | n_participants | median_participant_delta | mean_participant_delta | bootstrap_95_low_median | bootstrap_95_high_median | n_positive | n_negative | n_zero | positive_fraction_nonzero | exact_two_sided_sign_test_p | holm_p_primary_family |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ecog | common_contact_average_reference | burst_alpha | 19 | -0.01699 | -0.02282 | -0.03847 | 0.0007171 | 6 | 13 | 0 | 0.3158 |  |  |
| ecog | common_contact_average_reference | paf_cog | 19 | 0.2236 | 0.1869 | -0.03247 | 0.3466 | 13 | 6 | 0 | 0.6842 |  |  |
| ecog | common_contact_average_reference | sp_disp | 19 | 0.01802 | 0.04397 | -0.03408 | 0.1194 | 10 | 9 | 0 | 0.5263 |  |  |
| ecog | recorded_reference_unknown | burst_alpha | 19 | -0.009956 | -0.009499 | -0.02389 | 0.01281 | 7 | 12 | 0 | 0.3684 | 0.3593 | 0.7186 |
| ecog | recorded_reference_unknown | paf_cog | 19 | 0.1161 | 0.03888 | -0.04745 | 0.2273 | 12 | 7 | 0 | 0.6316 | 0.3593 | 0.7186 |
| ecog | recorded_reference_unknown | sp_disp | 19 | 0.01663 | 0.03634 | 0.001977 | 0.04808 | 14 | 5 | 0 | 0.7368 | 0.06357 | 0.1907 |

## Reference effect shifts

| acq | metric | n_matched_participants | median_delta_recorded_reference_unknown | median_delta_common_contact_average_reference | median_reference_effect_shift_average_minus_recorded | bootstrap_95_low_reference_effect_shift | bootstrap_95_high_reference_effect_shift | direction_agreement_fraction_nonzero | n_direction_reversals |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ecog | burst_alpha | 19 | -0.009956 | -0.01699 | -0.01025 | -0.01988 | 0.004808 | 0.8421 | 3 |
| ecog | paf_cog | 19 | 0.1161 | 0.2236 | 0.1748 | 0.0006819 | 0.2599 | 0.9474 | 1 |
| ecog | sp_disp | 19 | 0.01663 | 0.01802 | 0.002059 | -0.04285 | 0.06421 | 0.5789 | 8 |
| seeg | burst_alpha | 33 | -0.01157 | -0.01233 | -0.001244 | -0.007076 | 0.00201 | 0.697 | 10 |
| seeg | paf_cog | 33 | 0.04155 | 0.09583 | 0.02604 | -0.05295 | 0.03914 | 0.8788 | 4 |
| seeg | sp_disp | 33 | 0.02007 | 0.006424 | -0.009161 | -0.03659 | 0.00644 | 0.6061 | 13 |

## Candidate–comparator change correlations (SEEG, recorded reference unknown)

| candidate | comparator | n_participants | spearman_rho | bootstrap_95_low | bootstrap_95_high |
| --- | --- | --- | --- | --- | --- |
| burst_alpha | alpha_power_log10 | 33 | -0.4629 | -0.6764 | -0.1721 |
| burst_alpha | broadband_power_log10 | 33 | -0.3914 | -0.6657 | -0.04028 |
| burst_alpha | broad_spectral_centroid | 33 | -0.3305 | -0.6411 | 0.03236 |
| sp_disp | alpha_power_log10 | 33 | 0.2343 | -0.1128 | 0.5543 |
| sp_disp | broadband_power_log10 | 33 | 0.1013 | -0.2376 | 0.4488 |
| sp_disp | broad_spectral_centroid | 33 | 0.0498 | -0.3208 | 0.4022 |
| paf_cog | alpha_power_log10 | 33 | 0.1487 | -0.2369 | 0.5024 |
| paf_cog | broadband_power_log10 | 33 | -0.09559 | -0.4661 | 0.2817 |
| paf_cog | broad_spectral_centroid | 33 | 0.4215 | 0.05902 | 0.7286 |

## Limits and next decision

`paf_cog` remains a 7–13 Hz band centroid unless a resolved peak diagnostic supports a peak interpretation. `sp_disp` is a spread across patient-specific implanted contacts. `burst_alpha` uses an event/run-local Hilbert transform; it is a state descriptor, not prospective forecasting. A consistent paired difference supports a regime descriptor, not unique information. If a candidate is considered for experimental MNPS 3.4, assess whether its participant changes overlap the simple spectral comparators and then require a separate patient-held-out predictive-value study. This screen has no aligned, comparable MNPS v2 baseline and cannot support a claim that candidates outperform coordinates proposed for removal.

## Reproducibility artifacts

See `manifest.json` for the frozen protocol/script hashes and software versions; `window_features.csv` and `run_support.csv` preserve window-level values and support; `participant_contrasts.csv` preserves one participant contrast per metric/reference/modality.

## Post-run support audit

- Run command: `H:\SourceRepo2\NeuralManifoldDynamics\.venv\Scripts\python.exe J:\repos\nmd-analysis\articles\ds004100_ndt_v.1.0\validation\sl004_fable_screen_v1\screen_sl004_ds004100.py --mode full`. Software: Python 3.12.0, MNE 1.6.1, NumPy 2.1.1, pandas 2.3.3, SciPy 1.14.1, threadpoolctl 3.6.0.
- All 52 eligible patient–modality pairs contributed participant contrasts for all six metrics under both references (624 rows total). There were 295 source recordings: 271 had at least one guarded window and 24 had none; there were zero processing errors.
- The two reference arms contained exactly the same 5,473 source windows (10,946 rows total). All six metrics were finite on every window in both references.
- A row-level audit found no ictal event-edge or interictal recording-edge guard violations. Each patient–modality pair had one fixed contact-set hash across runs; common contact counts ranged from 36 to 176.
- The minimum native sampling rate is 256 Hz (Nyquist 128 Hz). Analysis resampling is to 250 Hz (Nyquist 125 Hz); the highest analyzed band edge is 45 Hz.
- The local DataLad snapshot has DOI `10.18112/openneuro.ds004100.v1.1.3`, while `BIDSVersion: 1.4.0` identifies the BIDS specification. The local copy has no `.git` directory, so a local repository commit SHA cannot be reported.
