# Figshare infant cohort-anchor follow-up

- Input: `neuralmanifolddynamics_figshare_infant_eeg_20260805_102438`.
- Anchor: `figshare_infant_eeg_global_cohort_all_visits_iqr_v2_1`, subject-balanced IQR fit over 22 children and 6,929 epochs.
- QC: 70 sessions; 68 `ok`, 2 `adjusted`; all retained under the export invalidity policy and all provide 9D MNJ.
- Cohort-coordinate GEE: all 12 3D/9D coordinate spline omnibus tests are FDR-supported across 70 visits/22 children. The independent local wrapper reproduces the supplied GEE results exactly.
- Direct-age sensitivity: 11/12 coordinates remain FDR-supported; only 9D `m_e` is not (p=0.053).
- Complementary within-child MNJ/reachability: no supported endpoint; smallest raw p=0.173 for effective dimension.

Interpret cohort-coordinate trajectories as common EEG-derived chart-position associations, distinct from local flow geometry and not a neural mechanism or normative-age reference.
