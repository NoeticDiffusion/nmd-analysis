# TAC Incremental Validity over NDT-5

- CV: 20x5 repeated stratified
- n_subjects: 281

| Model | n feat | AUROC mean | AUROC sd | Delta AUROC | Delta p |
|---|---|---|---|---|---|
| `clinical_plus_eeg` | 26 | 0.600 | 0.065 | +0.000 | — |
| `clinical_plus_eeg_plus_NDT5` | 31 | 0.662 | 0.065 | +0.062 | 1.77e-26 |
| `clinical_plus_eeg_plus_NDT5_plus_TAC10` | 33 | 0.659 | 0.066 | +0.059 | 3.26e-24 |
| `clinical_plus_eeg_plus_NDT5_plus_TACAll` | 38 | 0.647 | 0.064 | +0.047 | 2.68e-17 |
| `TAC10_only` | 2 | 0.630 | 0.066 | +0.031 | 6.66e-04 |
| `NDT5_only` | 5 | 0.633 | 0.054 | +0.034 | 9.63e-05 |
| `NDT5_plus_TAC10` | 7 | 0.630 | 0.052 | +0.031 | 2.37e-04 |