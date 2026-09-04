# PD-EEG: Resting-State & Walking EEG in Parkinson's Disease

## Overview

This dataset contains EEG recordings from Parkinson's disease (PD) patients and healthy controls (HC), collected under two behavioral conditions: resting state (sitting) and walking. The dataset was acquired at the Neurology Institute, Tel Aviv Sourasky Medical Center.

---

## Participants

- **Parkinsonâ€™s disease (PD):** 116 participants
- **Healthy controls (HC):** 28 participants

### Inclusion criteria (PD):
- Age 40â€“90  
- Hoehn & Yahr stage â‰¤ 3 
- MoCA â‰¥ 21  
- Able to walk independently  

### Exclusion criteria:
- History of stroke or major neurological disorder  
- Brain surgery  
- Significant head injury  
- Inability to walk independently  

All participants provided informed consent. The study was approved by the local ethics committee and conducted in accordance with the Declaration of Helsinki.

---

## Experimental Design

Each participant underwent EEG recording under two conditions:

1. **Resting State** (144 Recordings)
   - Sitting
   - Eyes open
   - Duration: ~4 minutes  

2. **Walking** (133 Recordings)
   - Walking on a treadmill at a comfortable speed while holding the handrails.
   - Duration: ~4 minutes  

Additional clinical data were collected, including:

- **Demographic data**
- **LEDD** (Levodopa Equivalent Daily Dose) - a measure of anti-parkinsonian medication dosage.
- **MoCA** (Montreal Cognitive Assessment) - a global measure of cognitive function.  
- **MDS-UPDRS**  - Movement Disorder Society Unified Parkinson's Disease Rating Scale - the gold standard clinical rating scale for Parkinson's Disease.
- **CTT** - Color Trails Test - a measure of executive function and processing speed.
---
## Additional Data

The `sourcedata\clinical_data` directory contains additional clinical files:

- `full_UPDRS_data.tsv`: item-level UPDRS data for all PD participants, including scores for each individual UPDRS item rather than only part-level summary scores.
- `longitudinal_clinical_data.tsv`: longitudinal clinical follow-up data, available for a subset of participants.
---

## EEG Acquisition

- **System:** 64-channel Geodesic EEG System 400 (EGI system)
- **Montage:** International 10â€“20 system  

---

## Data Organization

This dataset follows the **Brain Imaging Data Structure (BIDS)** specification.

Typical structure:

```
sub-001/
    eeg/
        sub-001_task-rest_eeg.*
        sub-001_task-walk_eeg.*

participants.tsv
participants.json
dataset_description.json
```

**Inbal Maidan, PhD**  
Tel Aviv Sourasky Medical Center  
Email: inbalm@tlvmc.gov.il

**Daniel Vered, BSc**
Tel Aviv Sourasky Medical Center  
Email: vereddan@tlvmc.gov.il