# 156 · 2026-07-01 · ds004511: Full NMD Pipeline Complete

## Summary

Full NMD pipeline for `ds004511` (EEG + BioPac physio, Gambling/Cognitive-Control/Rest)
completed successfully end-to-end. Feature extraction: 55,772 epochs across 44 subjects.
Summarize: per-session HDF5 + JSON + cohort-level CSVs written.

---

## Run Timeline

| Step | Start | End | Duration |
|------|-------|-----|----------|
| Smoke test (S200116, 1 worker) | 30 Jun 19:19 | 30 Jun 19:26 | ~7 min |
| Feature extraction (44 subjects, 4 workers) | 30 Jun 19:27 | 01 Jul 01:00 | ~5.5 h |
| Summarize | 01 Jul 01:00 | 01 Jul 01:45 | ~45 min |

---

## Feature Extraction Results

- **Total epochs**: 55,772
- **Files processed**: 131 EEG EDF files (44 subjects × 3 tasks; minus 3 already done from smoke test)
- **Failed sessions**: 1 (`sub-S210317` GG session — empty features, likely short/corrupt EDF)
- **Output**: `J:\processed\openneuro\ds004511\features.{csv,parquet}` (107 MB CSV, 45 MB Parquet)
- **Workers**: 4; observed peak RSS ≤ 1.4 GB/worker

### Per-session modality profile (confirmed on all successful sessions)

```
Preprocessed: ['eeg', 'eog', 'ecg', 'resp']
```

- ICA: 1–2 components removed, always using `ecg=['ECG']` (injected BioPac ECG)
- ECG epochs computed for all sessions
- RESP epochs computed (qc_ok fraction varies: ~0.17–0.79 for Rest, ~0.63–1.0 for CC/GG)
- Cardioresp coupling computed (qc_ok fraction consistently 1.0)
- EOG features computed (qc_ok fraction = 1.0 for all)

---

## Summarize Results

- **Output directory**: `J:\processed\openneuro\ds004511\neuralmanifolddynamics_ds004511_20260701_010029\`
Robin: I copied the folder to J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_ds004511_20260701_010029 - use this folder instead.
- **Total files**: 536

### Cohort-level files

| File | Contents |
|------|----------|
| `features_snapshot.json` | Feature statistics across cohort |
| `normalization_report.json` | Robust-Z normalization parameters |
| `regional_mnps_subjects_010029.csv` | Regional MNPS per subject/task/region |
| `regional_block_jacobians_subjects_010029.csv` | Block Jacobians per subject/region/network |
| `stratified_block_jacobians_subjects_010029.csv` | Stratified block Jacobians |
| `run_manifest.json` | Full run provenance |
| `config_ingest_ds004511.yaml` | Config snapshot |

### Per-session outputs (for each subject × task)

Each session folder contains:
- `summary.json` — MNPS coordinates, Jacobian eigenvalues, anchor state
- `qc_summary.json` — per-feature QC metrics
- `qc_reliability.json` — test-retest reliability metrics
- `<session>.h5` — MNPS HDF5 trajectory file (3.6 MB example for GG)

---

## Electrode Regions (4 groups)

| Region | Channels |
|--------|----------|
| frontal | Fp1/2, F3/4/z/7/8, AF3/4/7/8 |
| central | FC1/2/3/4/z, C3/z/4 |
| parietal_occipital | P3/4/z/7/8, O1/2, PO3/4/z, Oz |
| temporal | T7/8, TP7/8 |

Block Jacobians computed for all 4 regions × 3 tasks per subject (9D conditioning
κ values: typically 10–16, well-conditioned).

---

## Known Issues / Follow-up

1. **CSD disabled**: No digitization points in EDF headers → CSD computation skipped
   for all sessions. This is expected for TruScan data without electrode position files.

2. **RESP qc_ok low for Rest**: Rest sessions show 0.17–0.79 RESP qc_ok fraction.
   Likely reflects breathing irregularity at rest vs. task-evoked rhythmic breathing.
   Not a blocker; respiration features are still computed.

3. **sub-S210317 GG empty**: One gambling session produced 0 features. Cause unknown
   (could be a corrupt or truncated EDF). The CC and Rest sessions for this subject
   completed normally.

4. **EDA not extracted**: EDA channel is injected and typed `misc`, but no EDA
   feature extractor exists yet. SCR peaks / tonic level would complete the EAP feature
   set for this dataset.

---

## Next Steps

- Handover to NoeticDiffusion analysis repo (`J:\repos\NoeticDiffusion\`)
- Cross-task analysis: Rest vs. CC vs. GG on MNPS, HRV, RESP anchor indices
- EAP test: correlation between interoceptive features (HRV RMSSD, RESP anchor_index,
  cardioresp RSA/PLV) and EEG manifold dimensionality / Jacobian coupling
- Control condition: compare gambling-win vs. gambling-loss epochs (events.tsv available)
