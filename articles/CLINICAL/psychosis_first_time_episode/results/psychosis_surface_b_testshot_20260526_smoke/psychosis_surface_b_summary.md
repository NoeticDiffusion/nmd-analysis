# Psychosis Surface B Testshot

Short article-local pilot using per-window reachability covariance deformation on raw psychosis H5 trajectories.

## ds003944 / Healthy_vs_FEP

- groups: `Healthy` vs `FEP`
- n: `32` vs `50`
- top raw Surface B: `surface_b_logeuc_temporal_grad_p95` (Cliff's delta `0.268`, AUROC `0.366`)
- top residualized Surface B: `surface_b_logeuc_temporal_grad_p95_asinh_resid_reachability` (Cliff's delta `0.236`, AUROC `0.382`)

## ds003944 / Healthy_vs_FEP_medicated

- groups: `Healthy` vs `FEP medicated`
- n: `32` vs `31`
- top raw Surface B: `surface_b_logeuc_temporal_grad_p95` (Cliff's delta `0.383`, AUROC `0.308`)
- top residualized Surface B: `surface_b_logeuc_temporal_grad_p95_asinh_resid_reachability` (Cliff's delta `0.325`, AUROC `0.338`)

## ds003944 / Healthy_vs_FEP_unmedicated

- groups: `Healthy` vs `FEP unmedicated`
- n: `32` vs `19`
- top raw Surface B: `surface_b_spectral_temporal_grad_median` (Cliff's delta `-0.122`, AUROC `0.439`)
- top residualized Surface B: `surface_b_logeuc_spatial_grad_p95_asinh_resid_reachability` (Cliff's delta `0.217`, AUROC `0.391`)

## ds003944 / FEP_medicated_vs_FEP_unmedicated

- groups: `FEP unmedicated` vs `FEP medicated`
- n: `19` vs `31`
- top raw Surface B: `surface_b_spectral_temporal_grad_median` (Cliff's delta `0.338`, AUROC `0.331`)
- top residualized Surface B: `surface_b_spectral_temporal_grad_median_asinh_resid_reachability` (Cliff's delta `0.260`, AUROC `0.370`)
