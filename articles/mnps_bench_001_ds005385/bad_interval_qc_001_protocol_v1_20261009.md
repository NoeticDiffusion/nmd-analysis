# BAD-INTERVAL-QC-001 protocol v1 — 2026-10-09

## Scope

Audit available BIDS/EEGLAB source annotation and channel-status evidence for the six frozen pilot participants. Perform a metadata-only availability audit for the 65 source-table participants marked `EEG_excluded=no`; do not read their EEG sample arrays or compute features in that roster scan. Apply the signal screen to the six pilot recordings only, after the FILTER-SUPPORT-001 policy is frozen.

## Source-annotation semantics

Emit separate fields:

- `source_bad_annotations_available`: true only when a usable source annotation mechanism is present; false when the audited exports contain no usable bad-interval annotation.
- `source_channel_status_available`: whether BIDS `channels.tsv` supplies channel `status`/`status_description` values.
- `source_bad_interval_free`: `false` when a source bad interval overlaps the requested support; `true` only when explicit source evidence marks the full support interval clean; otherwise `unknown`.

Absence of annotations, an empty EEGLAB reject mask, or an absent BIDS channel-status column must never be translated into `source_bad_interval_free=true`. An unknown source status remains unknown even if the signal screen passes.

## Frozen condition-blind signal screen

Screen each current and guarded candidate window separately for Core19-average and native63-average realizations. Compute QC from the 250 Hz resampled data before the 50 Hz notch and 1–45 Hz bandpass, after applying the named surface's average reference. Do not use condition labels in thresholds or decisions.

Hard signal-integrity checks, expressed in µV:

- non-finite input sample in any realization channel;
- channel peak-to-peak `<= 0.5 µV` across the candidate window (flat/near-flat channel);
- channel maximum absolute amplitude `> 500 µV` or peak-to-peak `> 1000 µV`;
- adjacent-sample absolute step `> 200 µV` at 250 Hz.

`signal_qc_pass` means only that none of these frozen hard checks fired. It does not mean artifact-free, qualified, or source-annotation-clean. Preserve measurements and record the specific flags; do not zero or silently remove a computable value.

Also emit descriptive spectral review flags using Welch PSD with 2-second Hann segments, 50% overlap, constant detrending, and mean power over inclusive frequency bands:

- `upper_beta_ratio = P(30–45 Hz) / P(1–45 Hz)`;
- `emg_band_ratio = P(70–100 Hz) / P(1–100 Hz)`;
- `line_ratio = P(48–52 Hz) / P(1–100 Hz)`.

Set the corresponding review flag if at least 5 of 19 Core19 channels exceed, respectively, 0.80, 0.20, or 0.50. These are frozen project screening cutoffs, not universal artifact definitions. They are reported separately as `signal_qc_review_required`; by themselves they do not change `signal_qc_pass` or delete values. Report their frequency by participant, condition, load, realization, and window length so differential flagging is visible.

The BIDS specification makes channel `status` optional; a missing status is not a clean-channel attestation ([EEG BIDS specification](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/03-electroencephalography.html)). MNE's amplitude annotations likewise take user-specified peak/flat thresholds, and its epoch-quality example notes that the choice varies with the dataset and analysis ([MNE amplitude annotation](https://mne.tools/1.6/generated/mne.preprocessing.annotate_amplitude.html), [MNE epoch-quality example](https://mne.tools/stable/auto_examples/preprocessing/plot_epoch_quality.html)). The numerical cutoffs above are therefore operational and are not described as validated universal thresholds.

## Required output fields

At minimum preserve source annotation availability/status, BIDS channel-status availability, hard `signal_qc_pass`, each hard flag, `signal_qc_review_required`, each spectral flag and ratio, `effective_filter_support_pass`, actual channel realization, window support, and `measurement_qualified=false`. Keep all four statuses independent; no successful technical field implies qualification.
