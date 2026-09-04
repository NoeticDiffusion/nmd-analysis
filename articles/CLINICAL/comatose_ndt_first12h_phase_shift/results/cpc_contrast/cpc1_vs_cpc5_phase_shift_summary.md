# CPC1 vs CPC5 first-12h phase-shift contrast

- good_cpc=1 (Good), poor_cpc=5 (Poor)
- n_cells_tested=72

Caveat: `d_n` here is the I-CARE EEG-contract alias for `eeg_gamma`, not the RVC_SLEEP heat-kernel network-diffusivity `d_n`. See `coma_phase_shift_support.py` module docstring.

## FDR-significant cells (q < 0.05): 1

- `e_m__mean_shift_quality`: delta_median=2.259, cohens_d=0.131, mannwhitney_p=0.0004196, q_bh=0.03021

## Top 10 cells by raw p-value (uncorrected, for context only)

- `e_m__mean_shift_quality`: delta_median=2.259, mannwhitney_p=0.0004196, q_bh=0.03021
- `e_m__median_shift_quality`: delta_median=2.222, mannwhitney_p=0.001616, q_bh=0.05817
- `e_e__mean_shift_quality`: delta_median=1.641, mannwhitney_p=0.004923, q_bh=0.09388
- `d_s__median_shift_magnitude`: delta_median=-0.133, mannwhitney_p=0.006979, q_bh=0.09388
- `e_m__mean_shift_magnitude`: delta_median=0.2564, mannwhitney_p=0.00962, q_bh=0.09388
- `d_n__mean_shift_quality`: delta_median=2.017, mannwhitney_p=0.0105, q_bh=0.09388
- `e_m__median_shift_magnitude`: delta_median=0.1643, mannwhitney_p=0.01061, q_bh=0.09388
- `d_n__median_shift_quality`: delta_median=1.372, mannwhitney_p=0.01501, q_bh=0.09388
- `e_e__median_shift_quality`: delta_median=1.473, mannwhitney_p=0.01639, q_bh=0.09388
- `m_e__shift_rate_per_hour`: delta_median=-0.8044, mannwhitney_p=0.0168, q_bh=0.09388
