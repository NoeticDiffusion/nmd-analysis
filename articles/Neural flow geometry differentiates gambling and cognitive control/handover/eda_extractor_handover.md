# EDA Feature Extraction — Handover Note
## ds004511 · GG / CC / Rest · 2026-07-01

This note documents `06_eda_extraction.py`, a standalone EDA feature extractor
written for this article because the NMD pipeline does not yet have an EDA
extractor module (see `handover.md` known issue #4).

---

## Why a separate script

The NMD pipeline ingests the BioPac EDA channel as a `misc` EEG channel but
does not decompose it into tonic/phasic components or compute SCR events.
This script reads the raw `_physio.tsv.gz` files directly, processes EDA with
neurokit2, and produces an `eda_features.parquet` aligned to the existing
`features.parquet` epoch grid.

---

## Input data

| Item | Value |
|------|-------|
| Raw physio files | `M:\datasets\received\openneuro\ds004511\sub-*\ses-01\*_physio.tsv.gz` |
| EDA column | Column index **5** (0-indexed): "EDA, Y, PPGED-R" |
| BioPac sampling rate | **4000 Hz** |
| Physio columns | time · ECG · RSP · EMG\_A · EMG\_B · **EDA** · Digital |
| Epoch alignment source | `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_ds004511_20260701_010029\features.parquet` |
| Sessions | 136 (45 subjects × 3 tasks; 1 GG session missing from NMD pipeline) |

The `StartTime` offset (seconds before EEG recording onset) is read from each
`*_physio.json` sidecar and applied when mapping epoch timestamps to physio
sample indices.

---

## Algorithm

```
1. Stream-read column 5 from physio.tsv.gz
   - Python gzip.open line iterator, split('\t', 6)  [no pandas — files are 25–220 MB]
   - Result: eda_4k  (float32 array at 4000 Hz)

2. Downsample 4000 Hz → 50 Hz
   - scipy.signal.decimate(eda_4k, q=8,  zero_phase=True)   → 500 Hz
   - scipy.signal.decimate(…,       q=10, zero_phase=True)   → 50 Hz
   - Anti-aliased; avoids aliasing of any 5-50 Hz EDA artefacts

3. Quality check (session level)
   - Reject if range < 0.01 µS or mean outside (0, 100) µS

4. Decompose full session (one neurokit2 call per session)
   - nk.eda_process(eda_ds, sampling_rate=50, method="neurokit")
   - Outputs: EDA_Tonic, EDA_Phasic, SCR_Peaks, SCR_Amplitude

5. Per-epoch feature extraction (8-second windows, aligned to features.parquet)
   - Map epoch [t_start, t_end] → sample indices in downsampled array
   - Skip windows < 2 s
```

---

## Output features

| Feature | Description |
|---------|-------------|
| `eda_tonic_scl` | Mean tonic SCL in epoch (µS) |
| `eda_tonic_slope` | Linear slope of tonic component (µS/s) |
| `eda_phasic_scr_rate` | SCR events per minute |
| `eda_phasic_scr_amp` | Mean SCR peak amplitude in epoch (µS) |
| `eda_phasic_scr_count` | SCR count in epoch |
| `eda_phasic_auc` | Mean absolute phasic signal |
| `eda_arousal_index` | `scr_rate + |tonic_slope|` (unnormalised) |
| `qc_ok_eda` | 1 = passed QC, 0 = rejected |

Merge key: `(file, t_start)` — matches the schema of `features.parquet`.

---

## Output files

```
articles/Neural flow geometry differentiates gambling and cognitive control/results/06_eda_extraction/
  eda_features.parquet    — epoch-level features, all sessions
  eda_qc_summary.csv      — per-session QC stats (n_epochs, n_ok, qc_ok_frac)
```

---

## QC summary (run 2026-07-01, 44.5 min, exit 0)

**Total epochs extracted: 54,149** across 136 sessions (45 subjects × 3 tasks minus 1 failed NMD session).

| Task | Mean epochs/session | Mean QC pass rate | Median tonic SCL (µS) |
|------|--------------------|--------------------|----------------------|
| rest | 126 | 99.7% | 2.06 |
| cognitive_control | 262 | 98.3% | 3.22 |
| gambling | 911 | 98.8% | 3.10 |

**Cross-task Wilcoxon on subject-median tonic SCL:**

| Contrast | Cohen's d | p | n |
|----------|-----------|---|---|
| gambling vs rest | 0.53 | 0.0006 | 39 |
| cognitive_control vs rest | 0.67 | <0.0001 | 42 |
| gambling vs cognitive_control | -0.08 | 0.51 | 41 |

Both active tasks show significantly higher tonic SCL than Rest (moderate effects).
GG and CC are **not** differentiated by EDA — sustained sympathetic arousal is
similar across the two cognitively demanding task types.

**Known bad sessions (EDA QC fail — full session rejected):**
- `sub-S201222` Rest — flat/saturated signal
- `sub-S201210` Rest — flat/saturated signal
- `sub-S200303` CC (ses-01 and ses-02) — consistently noisy EDA

Runtime: 44.5 min on Windows workstation reading from M:\ network drive.

---

## Reproducing from scratch

```powershell
# From repo root
python "articles/Neural flow geometry differentiates gambling and cognitive control/src/06_eda_extraction.py"
```

Requirements (beyond standard scientific Python stack):
- `neurokit2 >= 0.2` (`pip install neurokit2`)
- Access to `M:\datasets\received\openneuro\ds004511` (raw physio)
- Access to `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_ds004511_20260701_010029\` (NMD outputs)

Runtime: ~35 minutes on a Windows workstation reading from a network drive
(GG files are 160–220 MB compressed; Rest ~25 MB; CC ~50 MB).

---

## What should go into NMD instead

The algorithm above is dataset-agnostic. A proper NMD EDA extractor module
should:

1. Accept `physio.tsv.gz` + `physio.json` sidecar as inputs (already read by
   the NMD ingest pipeline).
2. Identify the EDA channel by name from the sidecar
   (`column_names` → look for "EDA" or "GSR"), not by hard-coded column index.
3. Downsample to 50 Hz using `scipy.decimate` (same as above).
4. Call `nk.eda_process` on the full session.
5. Write epoch-level tonic SCL / phasic AUC / SCR rate to the per-epoch
   features dict, using the same schema as existing ECG / RESP extractors.
6. Add `qc_ok_eda` to the QC report.

The signal-processing logic in `06_eda_extraction.py:process_session_eda()`
and `epoch_features()` can be lifted directly into an NMD extractor class.
