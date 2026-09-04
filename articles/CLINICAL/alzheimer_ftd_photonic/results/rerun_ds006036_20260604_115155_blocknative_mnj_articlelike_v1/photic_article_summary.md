# Photonic article summary

- This export uses exact block-native `/blocks` intervals and keeps original analysis windows whose centers fall inside photic block boundaries.
- This is an MNJ-focused exact-block export; reachability rows were not rebuilt because the current ds006036 block-native root still lacks the state-space contract expected by the legacy reachability helper.
- Block-interval selection contributed `1757` original windows across `397` photic block instances in `88` subjects.


## Strongest selected contrast rows

### AD_vs_Healthy

- `PHOTO 5 Hz` / `Regional 3D MNJ` / `spectral_radius_median` (`frontal`): d=0.500, p=0.0453, q=0.3748
- `PHOTO 10 Hz` / `Regional 3D MNJ` / `spectral_radius_median` (`temporal`): d=0.311, p=0.2039, q=0.9238
- `PHOTO 15 Hz` / `Regional 3D MNJ` / `spectral_radius_median` (`central`): d=0.300, p=0.1599, q=0.7615
- `PHOTO 20 Hz` / `Regional 3D MNJ` / `spectral_radius_median` (`central`): d=0.191, p=0.2701, q=0.9221

### FTD_vs_Healthy

- `PHOTO 5 Hz` / `Regional 3D MNJ` / `spectral_radius_median` (`temporal`): d=0.549, p=0.0798, q=0.6533
- `PHOTO 10 Hz` / `Regional 3D MNJ` / `spectral_radius_median` (`temporal`): d=0.496, p=0.07202, q=0.4321
- `PHOTO 15 Hz` / `Regional 3D MNJ` / `spectral_radius_median` (`temporal`): d=0.746, p=0.03071, q=0.2457
- `PHOTO 20 Hz` / `Regional 3D MNJ` / `spectral_radius_median` (`central`): d=0.448, p=0.3406, q=1

### AD_vs_FTD

- `PHOTO 5 Hz` / `Regional 3D MNJ` / `spectral_radius_median` (`frontal`): d=0.447, p=0.05855, q=0.3513
- `PHOTO 10 Hz` / `Regional 3D MNJ` / `spectral_radius_median` (`central`): d=-0.256, p=0.3784, q=0.8339
- `PHOTO 15 Hz` / `Regional 3D MNJ` / `spectral_radius_median` (`frontal`): d=0.121, p=0.2904, q=0.6075
- `PHOTO 20 Hz` / `Regional 3D MNJ` / `spectral_radius_median` (`temporal`): d=-0.400, p=0.3338, q=0.89

## MMSE overview

- `Dementia_all` strongest row: `PHOTO 10 Hz` / `Regional 3D MNJ` / `trace_median` (`frontal`), rho=0.489, p=0.0001295, q=0.003108
- `AD_only` strongest row: `PHOTO 5 Hz` / `Regional 3D MNJ` / `rotational_power_median` (`temporal`), rho=0.344, p=0.04315, q=0.3637
- `FTD_only` strongest row: `PHOTO 10 Hz` / `Regional 3D MNJ` / `anisotropy_abs_eig_median` (`frontal`), rho=0.731, p=0.0001127, q=0.002704

## Notes

- Regional photic outputs span `central`, `frontal`, `parietal_occipital`, and `temporal` in the current H5 contracts.
- Reachability rows use the shared `ndt-analysis` 3D reachability definition on recovered photic windows.
- Frequency labels are restricted to `PHOTO 5/10/15/20 Hz` in this export pass.