# Conventional comparator summary

This panel compares ESB-2 against conventional exported EEG features available on the frozen ds006036/ds004504 article surface.

Comparator set:

- `Stage-matched posterior band-power proxy`: Direct stimulation-frequency SSVEP amplitude is not available on the frozen feature surface, so the closest posterior band-power proxy is used: theta for 5 Hz, alpha for 10 Hz, and beta for 15/20 Hz.
- `Posterior alpha power`: Parietal-occipital eeg_alpha feature.
- `Posterior alpha/theta ratio`: Parietal-occipital eeg_alpha_theta feature from the exported contract.
- `Posterior sample entropy`: Parietal-occipital eeg_sample_entropy feature used as the closest available conventional irregularity proxy.

## Group contrasts at PHOTO 15 Hz

### AD_vs_Healthy

- `Posterior alpha power`: d=0.681, p=0.0005636, q=0.001551
- `Stage-matched posterior band-power proxy`: d=0.619, p=0.0007754, q=0.001551
- `Posterior alpha/theta ratio`: d=0.042, p=0.1185, q=0.1292
- `Posterior sample entropy`: d=-0.399, p=0.1292, q=0.1292

### FTD_vs_Healthy

- `Posterior alpha power`: d=0.463, p=0.03395, q=0.1358
- `Stage-matched posterior band-power proxy`: d=0.161, p=0.08568, q=0.1714
- `Posterior sample entropy`: d=-0.165, p=0.7401, q=0.8016
- `Posterior alpha/theta ratio`: d=-0.180, p=0.8016, q=0.8016

## Correlation with ESB-2 at PHOTO 15 Hz

- `Posterior alpha power`: rho=0.182, p=0.09897, q=0.2414, n=83
- `Posterior alpha/theta ratio`: rho=0.169, p=0.1259, q=0.2414, n=83
- `Posterior sample entropy`: rho=-0.148, p=0.181, q=0.2414, n=83
- `Stage-matched posterior band-power proxy`: rho=0.098, p=0.3766, q=0.3766, n=83
