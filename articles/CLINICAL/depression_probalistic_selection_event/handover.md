Nu har jag all info. Här kommer handover:

---

## Handover: ds003474 — Probabilistic Selection Task EEG

**Pipeline-körning:** `neuralmanifolddynamics_ds003474_20260609_044822`  
**Mapp:** `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_ds003474_20260609_044822`  
**Datakälla:** OpenNeuro [ds003474 v1.1.0](https://openneuro.org/datasets/ds003474) · DOI `10.18112/openneuro.ds003474.v1.1.0`  
**Paper:** Cavanagh (2019) · PMID 31149639 · doi:10.1162/cpsy_a_00024

---

### Dataset i korthet

| | |
|---|---|
| Paradigm | Probabilistisk selektionsuppgift (Frank et al.-typ) |
| Lab | John J.B. Allen, University of Arizona |
| Insamlingsperiod | 2008–2010, Neuroscan Synamps2 |
| N | 122 college-age subjects (sub-001 – sub-122) |
| Klinisk variabel | Beck Depression Inventory (BDI) — **kontinuerlig**, 0–63. Ingen binär gruppkolumn i BIDS. |
| Sekundär variabel | STAI (State-Trait Anxiety Inventory), också kontinuerlig |
| Notera | sub-544 (original-ID) exkluderades av kuratorn p.g.a. instabilt BDI — syns ej i BIDS-data |

**EEG-setup:**  
64 kanaler (10-20 extended, HEOG + VEOG som sista 2), 500 Hz orig → resampleat till 250 Hz, 60 Hz notch, CAR-reref, EOG-regression (HEOG/VEOG), 8 s fönster / 4 s steg.

**Paradigm-struktur:**  
Klassisk Frank PST. Träningsfas: 6 stimulus-par (A/B, C/D, E/F) med probabilistisk feedback (A=80% rätt, B=20%, C=70%, D=30%, E=60%, F=40%). Testfas: alla 30 par-kombinationer utan feedback. ~700–1400 events per subject.

---

### Vad pipeline producerat

**498 filer, 661 MB** totalt.

```
neuralmanifolddynamics_ds003474_20260609_044822/
│
├── run_manifest.json                     ← körningsprovenance, alla capabilities
├── config_ingest_ds003474.yaml           ← exakt config som användes
├── command_used.txt                      ← CLI-kommando
├── normalization_report.json
├── stage_mapping_qc.json
├── features_snapshot.json
│
├── anchors/
│   └── ds003474_cohort_auto_v2_1.json   ← fryst kohort-ankar (IQR-skalning, n=122)
│
├── regional_mnps_subjects_044822.csv     ← 488 rader: 122 subjects × 4 regioner
├── regional_block_jacobians_subjects_044822.csv
├── stratified_block_jacobians_subjects_044822.csv
│
└── sub-NNN_task_probabilistic_selection/   (×122)
    ├── sub-NNN_task_probabilistic_selection.h5   ← huvud-HDF5
    ├── summary.json
    ├── qc_summary.json
    └── qc_reliability.json
```

---

### HDF5-innehåll per subject

Varje `.h5` innehåller (alla 122 subjects har samtliga lager):

| Sökväg | Innehåll |
|--------|----------|
| `/mnps` | MNPS 3D-trajektoria [T×3] |
| `/mnps_dot` | Derivata [T×3] |
| `/jacobian` | MNJ-tensor [W×3×3] |
| `/coords_9d` | Stratifierat 9D-koordinatsystem [T×9] |
| `/jacobian_9D` | 9D-Jacobian (**70/122 subjects** — resten föll ut på konditioneringströskel) |
| `/features_raw` | Rå features per epoch (bandpower, PE, Hjorth m.fl.) |
| `/features_robust_z` | Robust-z-normaliserade features |
| `/feature_anchors` | Kohortankare inbäddade per subject |
| `/regional_mnps/<region>/mnps` | Regionala trajektorier: frontal, central, parietal_occipital, temporal |
| `/regional_mnps/<region>/jacobian` | Regionala Jacobians |
| `/labels/stage` | Event-koder per tidsfönster (alla trial-typer) |
| `/event_windows` | Exakt event-till-fönster-alignment (rad-för-rad) |
| `/codebooks/stage` | Kodbok: train_stim_a_b=10 … test_stim_f_e=59, feedback_correct=16 … |

**Koordinat-kontrakt:**
- `coords_3d_subject_anchored` ✓ (alla 122)
- `coords_3d_cohort_anchored` ✓ (alla 122, ankar: `ds003474_cohort_auto_v2_1`)
- `coords_9d_subject_anchored` ✓ (alla 122)
- `coords_9d_cohort_anchored` ✓ (alla 122)

---

### regional_mnps_subjects_044822.csv

488 rader (122 × 4 regioner), 32 kolumner. Nyckelkolumner:

```
subject_id, condition_label, task_label, network_label, n_timepoints,
m_mean, m_std, m_median, m_iqr, m_mad,
d_mean, d_std, d_median, d_iqr, d_mad,
e_mean, e_std, e_median, e_iqr, e_mad,
trace_mean, trace_std, frobenius_mean, rotation_norm_mean, anisotropy_mean,
strat9_condition_number, strat9_pc1_var, strat9_pc2_var, strat9_pc3_var,
strat9_pc1_3_cumulative_var, strat9_falsified
```

Alla subjects fick 4 nätverk (0 droppade). Typisk konditionering: κ ≈ 10–15.

---

### Event-lager i HDF5

`/labels/stage` och `/event_windows` innehåller **alla trial-typer** som separata kanaler, inklusive:

- `train_stim_a_b`, `train_stim_b_a`, … (6 träningspar)  
- `test_stim_a_b` … `test_stim_f_e` (30 testpar-kombinationer)  
- `feedback_correct`, `feedback_incorrect`  
- `left_response`, `right_response`

Detta möjliggör direkt event-locked MNPS-analys: t.ex. MNPS-position vid `feedback_correct` vs `feedback_incorrect` som funktion av BDI.

---

### Viktiga begränsningar att känna till

1. **Ingen binär grupp i data.** BDI och STAI är kontinuerliga kovariater — ingen high/low-kolumn finns i BIDS. Gruppering måste göras analytiskt (t.ex. mediansplit, klinisk tröskel BDI ≥ 14).

2. **9D-Jacobian tillgänglig för 70/122 subjects.** De resterande 52 föll ut p.g.a. att 9D-koordinatrymden var dåligt konditionerad (troligen korta inspelningar eller låg variabilitet). Använd 3D-Jacobian som fallback för dessa.

3. **Inga stimulustidsstämplar i BIDS events.tsv för en del subjects.** Stimuli-events finns för sub-001 men bekräfta att alla subjects har train/test-stim events — det varierade i coverage under körningen.

4. **Pre-interpolerade kanaler.** Några subjects hade kanaler interpolerade redan i originaldata. Ingen möjlighet att revert — antalet berörda subjects är okänt.

5. **Companion-dataset ds003478** (viloläges-EEG, samma lab) finns på `G:/Science_Datasets_longtime_storage/ds003478`. Subject-överlappet är inte verifierat — original-ID:n i participants.tsv (507–628) kan användas för cross-dataset matching.

---

### Förslag på första analyser

```python
import h5py, pandas as pd, numpy as np

# 1. Ladda BDI från BIDS (N:\received\ds003474\participants.tsv)
ptsv = pd.read_csv(r"N:\received\ds003474\participants.tsv", sep="\t")
# Kolumner: participant_id, Original_ID, sex, age, BDI, STAI

# 2. Läs regional summary
reg = pd.read_csv(r"J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_ds003474_20260609_044822\regional_mnps_subjects_044822.csv")
reg["bids_id"] = reg["subject_id"]
merged = reg.merge(ptsv.rename(columns={"participant_id":"bids_id"}), on="bids_id")

# 3. BDI vs. frontal m_mean (MNPS metastabilitet)
frontal = merged[merged["network_label"]=="frontal"]
print(frontal[["BDI","m_mean","d_mean","e_mean"]].corr())

# 4. Per-subject event-locked analys via event_windows
with h5py.File(r"...\sub-001_task_probabilistic_selection.h5") as f:
    ew = {k: f["event_windows"][k][:] for k in f["event_windows"]}
    mnps = f["mnps"][:]
    # Välj rader för feedback_correct/incorrect
    ...
```