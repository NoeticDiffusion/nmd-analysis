# Conventional comparator summary

This panel compares ESB-2 against conventional exported EEG features available on the frozen ds006036/ds004504 article surface.

Comparator set:

- `Stage-matched posterior band-power proxy`: Direct stimulation-frequency SSVEP amplitude is not available on the frozen feature surface, so the closest posterior band-power proxy is used: theta for 5 Hz, alpha for 10 Hz, and beta for 15/20 Hz.
- `Posterior alpha power`: Parietal-occipital eeg_alpha feature.
- `Posterior alpha/theta ratio`: Parietal-occipital eeg_alpha_theta feature from the exported contract.
- `Posterior sample entropy`: Parietal-occipital eeg_sample_entropy feature used as the closest available conventional irregularity proxy.

## Group contrasts at PHOTO 15 Hz

### AD_vs_Healthy

- `Stage-matched posterior band-power proxy`: d=0.606, p=0.001208, q=0.002416
- `Posterior alpha power`: d=0.619, p=0.001208, q=0.002416
- `Posterior alpha/theta ratio`: d=-0.024, p=0.1915, q=0.2221
- `Posterior sample entropy`: d=-0.325, p=0.2221, q=0.2221

### FTD_vs_Healthy

- `Posterior alpha power`: d=0.463, p=0.03395, q=0.1358
- `Stage-matched posterior band-power proxy`: d=0.161, p=0.08568, q=0.1714
- `Posterior alpha/theta ratio`: d=-0.215, p=0.7707, q=0.8486
- `Posterior sample entropy`: d=-0.133, p=0.8486, q=0.8486

## Correlation with ESB-2 at PHOTO 15 Hz

- `Posterior sample entropy`: rho=-0.120, p=0.2781, q=0.8033, n=84
- `Posterior alpha/theta ratio`: rho=0.093, p=0.4016, q=0.8033, n=84
- `Posterior alpha power`: rho=0.043, p=0.6981, q=0.9215, n=84
- `Stage-matched posterior band-power proxy`: rho=0.011, p=0.9215, q=0.9215, n=84
