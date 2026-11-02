# V3-REFERENCE-SENSITIVITY-001 — MNE-matched reference branch

**Status:** frozen before new reference-branch values are computed. This is a
post-pilot method amendment, not prospective confirmation; earlier BENCH-002
and V002 outcomes are known.

## Question

How much do the candidate measurements change under average versus linked
mastoid rereferencing when the participant, time window, and measurement
channel labels are held fixed? Core19 is the primary sensor surface for
BENCH-002. Native63 is a separate sensitivity surface; native63-versus-Core19
differences will not be attributed to reference alone.

## Inputs and preprocessing

- Use the six frozen participants and exact 20-second anchor starts from
  `v3_multiscale_fidelity_002_pilot_v1_20261009/continuous_window_measurements.csv`.
  Anchors are selected independently of measurement values and task labels.
- Use each participant's continuous BIDS `task-rest` EEG file, its ordered
  `channels.tsv`, and the same full-recording MNE preprocessing as BENCH-002:
  microvolts to volts, 1,000-to-250 Hz `Raw.resample`, 50 Hz notch, then 1–45 Hz
  zero-phase FIR bandpass. The temporary Numba cache setting only makes the
  installed MNE import complete in this Windows environment; it does not change
  estimator or filter settings.
- MNE FFT resampling and the V002 polyphase amendment can differ by one terminal
  sample. Record both output counts, use the same saved 250 Hz anchor starts,
  require every full window to fit the MNE output, and do not pool the branches.
- These BIDS filenames and sidecars do not establish physiological rest: the
  sidecar TaskName is `mixed`. No events, condition labels, or task contrasts
  are read or analyzed.
- Preserve each 20-second anchor and compute nested 4/8/12/20-second windows.
  Emit the full eight-candidate measurement set and keep all QC/support status.

## Paired realizations

For each anchor and each surface, hold the ordered measurement channels fixed
between reference branches:

1. Core19, average reference over the same 19 Core19 channels.
2. Core19, subtract the mean of TP9 and TP10 from those same 19 channels.
3. Native63, average reference over the same 63 native channels.
4. Native63, subtract the mean of TP9 and TP10 from those same 63 channels.

TP9/TP10 are present in the recorded labels and are used as the linked-mastoid
reference pair. The Core19 set excludes them, so the primary Core19 comparison
uses a fixed 19-channel measurement set. Native63 retains TP9/TP10 in its
measurement labels; those two channels become zero in the linked-mastoid branch
by construction and that limitation is explicit in reporting.

## Analysis and limits

- The paired quantity is average-reference minus linked-mastoid value on the
  same window, summarized first across anchors within each participant. The
  six participants, not windows, are the independent units.
- Expand AR's nine ordered components separately. Report signed and absolute
  differences, support counts, channel/reference hashes, and QC.
- No equivalence margin, realization ranking, task contrast, classifier, or
  full-cohort analysis is applied. All values remain unqualified.
- Upstream filter edge safety and source bad-interval status remain unknown.
  They are retained as QC limitations and do not suppress otherwise computable
  comparisons.
- This MNE-matched branch is separate from the prior raw-polyphase V002
  continuous branch; do not pool their values.

Save the protocol, exact anchor map, source and code hashes, per-window paired
values, participant-level summaries, and output hashes in a new versioned
output directory.
