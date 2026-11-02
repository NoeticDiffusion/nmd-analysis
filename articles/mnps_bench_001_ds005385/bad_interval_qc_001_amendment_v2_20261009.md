# BAD-INTERVAL-QC-001 amendment v2 — baseline-invariant amplitude screen

Date: 2026-10-09. The original v1 QC rule and its complete output are preserved. This amendment is based on a condition-blind diagnostic of the v1 hard-QC failures and is applied to the same 6,480 windows.

## Evidence motivating the amendment

Every window crossed the v1 absolute-amplitude limit when measured relative to zero. At the same time, median maximum channel peak-to-peak ranges were approximately 91–504 µV by participant/surface, and most windows had ordinary finite step sizes. A source-level diagnostic on sub-032 found median absolute channel-wise window means of 6.25–6.42 mV after average referencing, while the same window's largest channel peak-to-peak range was 245–269 µV. The BIDS channel unit is microV and the stored EEGLAB value range was about −19,433 to +23,437 microV. Thus raw max-absolute-to-zero confounds a large electrode/DC offset with transient amplitude excursion; the measurement preprocessing's 1–45 Hz bandpass removes DC before feature calculation.

The screen is not changed to improve a condition contrast. Its meaning is clarified: an amplitude excursion is measured around the channel's window median, while the uncentered offset is retained as a diagnostic field. The same threshold remains 500 µV.

## Frozen v2 hard screen

For each 250 Hz window after realization-specific average reference, before notch/bandpass:

- fail nonfinite samples;
- fail any channel peak-to-peak `<= 0.5 µV`;
- fail any channel peak-to-peak `> 1000 µV`;
- fail any adjacent-sample step `> 200 µV`;
- fail maximum absolute amplitude `> 500 µV` **after subtracting that channel's within-window median**.

Also record (without automatic failure) maximum absolute amplitude before median-centering, median and maximum absolute channel median/DC offset, and all hard-screen component counts. The 30–45, 70–100, and 48–52 Hz Welch flags and thresholds remain unchanged and are review-only. The absolute, peak-to-peak, and step criteria are condition-blind and unchanged across conditions.

`signal_qc_pass` uses only the v2 hard-screen rules. Spectral review remains separate. No window is deleted or zeroed; all calculated measurements remain available with QC. Source annotation status stays unknown for all participants, and `measurement_qualified=false`.

## Recalculation scope

Re-run only the six-pilot raw 250 Hz QC on the same guarded windows, then join the resulting QC flags to the already-computed 6,480 unchanged estimator windows. Do not recompute or alter features, filter support, estimators, or thresholds. Preserve all v1 tables and outputs.
