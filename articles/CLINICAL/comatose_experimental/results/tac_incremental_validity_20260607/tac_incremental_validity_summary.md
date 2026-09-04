# TAC Incremental Validity over NDT-5

- CV: 20x5 repeated stratified
- n_subjects: 281

| Model | n feat | AUROC mean | AUROC sd | Delta AUROC | Delta p |
|---|---|---|---|---|---|
| `clinical_plus_eeg` | 26 | 0.600 | 0.065 | +0.000 | — |
| `clinical_plus_eeg_plus_NDT5` | 31 | 0.662 | 0.065 | +0.062 | 1.77e-26 |
| `clinical_plus_eeg_plus_NDT5_plus_TAC10` | 33 | 0.668 | 0.068 | +0.069 | 9.03e-25 |
| `clinical_plus_eeg_plus_NDT5_plus_TACAll` | 38 | 0.662 | 0.064 | +0.062 | 4.26e-21 |
| `TAC10_only` | 2 | 0.645 | 0.067 | +0.045 | 2.52e-06 |
| `NDT5_only` | 5 | 0.633 | 0.054 | +0.034 | 9.63e-05 |
| `NDT5_plus_TAC10` | 7 | 0.663 | 0.060 | +0.064 | 2.06e-11 |