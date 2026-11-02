# FILTER-SUPPORT-001 protocol v1 — 2026-10-09

## Question and claim ceiling

Characterize the exact preprocessing path used by BENCH-002 for recording-edge effects and for signal from immediately outside trial windows. In particular, test whether a perturbation beginning at the scheduled recall boundary can influence samples retained for fast-core and full-v3 measurements. This is an implementation sensitivity experiment. A synthetic perturbation is not evidence that speech contamination occurred in the source recordings.

## Frozen preprocessing path

Use the BENCH-002 `preprocess_eeg` calls with MNE 1.6.1, 1000 Hz input, and 250 Hz output, in this order:

1. `Raw.resample(250, n_jobs=1)` with MNE 1.6.1 defaults: FFT/frequency-domain resampling, `window='boxcar'`, `npad='auto'`, `pad='reflect_limited'`.
2. `Raw.notch_filter([50.0], picks='eeg', n_jobs=1)` with defaults: FIR, zero-phase, Hamming/firwin, automatic length, 1 Hz transition bandwidth, reflect-limited padding.
3. `Raw.filter(1.0, 45.0, picks='eeg', n_jobs=1)` with defaults: FIR, zero-phase, Hamming/firwin, automatic length/transitions, reflect-limited padding.

The installed MNE 1.6.1 design yields 825 taps for each FIR filter at 250 Hz, or 1.648 seconds of half-length per filter. The cascade of those two finite FIR operations therefore has a 3.296-second local half-support after resampling. This does **not** bound the complete chain: MNE 1.6.1's default resampler operates in the frequency domain over the complete recording and has no finite local-support guarantee. Report its observed tails separately; never label the composite chain as exactly finite-support.

MNE's 1.6.1 [`resample` documentation](https://mne.tools/1.6/generated/mne.filter.resample.html) describes frequency-domain windowing and padding. The [`filter_data` documentation](https://mne.tools/1.6/generated/mne.filter.filter_data.html) describes zero-phase FIR filtering and padding. The exact installed runtime and defaults are also recorded in the run manifest.

## Frozen perturbations and numerical tolerance

Use the six frozen BENCH-002 participants and their task-memory recording lengths and first complete load-13 control and memory event intervals. Work from BIDS event samples; the scheduled recall boundary is `last_digit_sample + 3000` at 1000 Hz. There is no source marker for the participant's realized voice onset.

At the trial start and scheduled trial end, test a 100 µV one-sample impulse and deterministic 100 µV-peak, 1-second Hann-windowed 10 Hz, 30 Hz, and 80 Hz sinusoids. Inject at the outside side of the boundary. Also test perturbations at the first and last recording samples for recording-edge behavior. Apply the same MNE chain to each test input; retain stage outputs after resampling, after notch, and after bandpass. Apply the planned Core19 average reference when reporting surface-level effects.

For a 100 µV stimulus, an operationally negligible influence is defined as both maximum absolute output change and RMS output change no greater than `1e-4` of the corresponding input peak/RMS (0.01 µV for the peak criterion). This is an engineering screen, not a biological or estimator-validity threshold. Evaluate retained samples at guard margins `0, 1, 2, 3, 3.296, 4, 5, 6, 7, 8, 10, 12, 15, 20` seconds. Define the operational guard as the smallest tested margin passing for every frozen case and both boundary directions. If none passes by 20 seconds, report that no finite operational guard was established in the tested range; do not relax the tolerance or extrapolate.

For the actual load-13 windows, separately report the measured interval between each current 20-second window end and the scheduled recall boundary, then evaluate the synthetic response at that exact gap. Record signal-level leakage ratios. A bounded sub-032 Core19 measurement replay with the same burst before and after perturbation may report candidate-value changes descriptively; it has no pass/fail threshold and cannot establish actual speech contamination.

## Outputs

Preserve exact coefficients/defaults, input file hashes, event samples, impulse and burst definitions, stage-by-stage leakage curves, recording-edge results, operational guard result, and any bounded measurement replay. No estimator formula, window duration, or feature threshold may be altered.
