# V3-MULTISCALE-FIDELITY-002 — continuous-input implementation amendment

**Applies only to the continuous empirical stage.** The frozen synthetic and
stationary-surrogate stages remain governed by
v3_multiscale_fidelity_002_protocol_v1_20261009.md.

## Reason and timing

The installed MNE package did not finish importing after two minutes of
continuous CPU use in the Windows runtime, so the continuous pilot could not
use the BENCH-002 MNE preprocessing branch. This was discovered before any
continuous empirical candidate values were computed. The amendment is an
execution/preprocessing accommodation, not an estimator or threshold change.
No task outcome, condition contrast, or classifier was examined to choose it.

## Frozen continuous input branch

- Use the same six V001 participants' BIDS task-rest EEG files. Read the
  declared ordered EEG channel labels, units, sample rate, and recording type.
  Do not read or use event labels to choose, exclude, or group windows.
- Convert the declared microvolt signal to volts and resample the continuous
  signal from its declared 1000 Hz sampling rate to 250 Hz with
  scipy.signal.resample_poly(up=1, down=4) and its default Kaiser antialias
  filter.
- Do not apply the BENCH-002 50 Hz notch or 1–45 Hz upstream bandpass in this
  branch. PCV retains its own frozen window-local 8–13 Hz filter/Hilbert
  estimator. For the PCV context comparison, apply that same 8–13 Hz filter
  and Hilbert transform once to the full resampled recording, then score the
  identical sample intervals.
- Compute separate native63 average-reference and Core19 average-reference
  realizations. Also compute native63 linked-mastoid reference where both TP9
  and TP10 are present; retain the reference identity and reference-set hash.
- Use nonoverlapping 20 s anchor starts, with a 5 s margin from each recording
  boundary. At each anchor, compute nested 4/8/12/20 s windows. Mark the
  earliest, middle, and latest anchors for descriptive equal-duration
  comparisons.
- Report flat-channel fraction, robust amplitude, peak-to-peak range,
  30–45 Hz power, and 48–52 Hz/1–45 Hz power ratio as window QC. These values
  do not reject, qualify, or impute measurements. Source bad_interval_free
  remains unknown, and the polyphase filter's recording-edge support remains
  separately identified.

## Interpretation boundary

This is a raw-resampled empirical realization and is not preprocessing-matched
to the BENCH-002 MNE-filtered pilot. It may characterize within-recording
duration, local PCV edge sensitivity, and reference sensitivity under this
declared branch. It cannot establish direct comparability with the existing
648 MNE-preprocessed 20 s measurements. No task contrast, classifier,
qualification decision, or full-cohort run is in scope.
