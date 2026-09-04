# Psychosis Surface B Testshot

Short article-local pilot using per-window reachability covariance deformation on raw psychosis H5 trajectories.

## ds003944 / Healthy_vs_FEP

- groups: `Healthy` vs `FEP`
- n: `32` vs `50`
- top raw Surface B: `surface_b_logeuc_temporal_grad_p95` (Cliff's delta `0.268`, AUROC `0.634`)
- top residualized Surface B: `surface_b_logeuc_temporal_grad_p95_asinh_resid_reachability` (Cliff's delta `0.274`, AUROC `0.637`)

## ds003944 / Healthy_vs_FEP_medicated

- groups: `Healthy` vs `FEP medicated`
- n: `32` vs `31`
- top raw Surface B: `surface_b_logeuc_temporal_grad_p95` (Cliff's delta `0.383`, AUROC `0.692`)
- top residualized Surface B: `surface_b_logeuc_temporal_grad_p95_asinh_resid_reachability` (Cliff's delta `0.387`, AUROC `0.694`)

## ds003944 / Healthy_vs_FEP_unmedicated

- groups: `Healthy` vs `FEP unmedicated`
- n: `32` vs `19`
- top raw Surface B: `surface_b_spectral_temporal_grad_median` (Cliff's delta `-0.122`, AUROC `0.561`)
- top residualized Surface B: `surface_b_logeuc_spatial_grad_p95_asinh_resid_reachability` (Cliff's delta `0.191`, AUROC `0.595`)

## ds003944 / FEP_medicated_vs_FEP_unmedicated

- groups: `FEP unmedicated` vs `FEP medicated`
- n: `19` vs `31`
- top raw Surface B: `surface_b_spectral_temporal_grad_median` (Cliff's delta `0.338`, AUROC `0.669`)
- top residualized Surface B: `surface_b_logeuc_temporal_grad_p95_asinh_resid_reachability` (Cliff's delta `0.331`, AUROC `0.666`)

## ds003947 / Healthy_vs_FEP

- groups: `Healthy` vs `FEP`
- n: `30` vs `31`
- top raw Surface B: `surface_b_spectral_spatial_grad_p95` (Cliff's delta `-0.120`, AUROC `0.560`)
- top residualized Surface B: `surface_b_spectral_spatial_grad_p95_asinh_resid_reachability` (Cliff's delta `-0.125`, AUROC `0.562`)

## ds003947 / Healthy_vs_FEP_medicated

- groups: `Healthy` vs `FEP medicated`
- n: `30` vs `23`
- top raw Surface B: `surface_b_spectral_spatial_grad_p95` (Cliff's delta `-0.133`, AUROC `0.567`)
- top residualized Surface B: `surface_b_logeuc_temporal_grad_median_asinh_resid_reachability` (Cliff's delta `-0.139`, AUROC `0.570`)

## ds003947 / Healthy_vs_FEP_unmedicated

- groups: `Healthy` vs `FEP unmedicated`
- n: `30` vs `8`
- top raw Surface B: `surface_b_logeuc_temporal_grad_median` (Cliff's delta `0.208`, AUROC `0.604`)
- top residualized Surface B: `surface_b_logeuc_temporal_grad_median_asinh_resid_reachability` (Cliff's delta `0.183`, AUROC `0.592`)

## ds003947 / FEP_medicated_vs_FEP_unmedicated

- groups: `FEP unmedicated` vs `FEP medicated`
- n: `8` vs `23`
- top raw Surface B: `surface_b_spectral_temporal_grad_median` (Cliff's delta `-0.283`, AUROC `0.641`)
- top residualized Surface B: `surface_b_spectral_temporal_grad_median_asinh_resid_reachability` (Cliff's delta `-0.283`, AUROC `0.641`)
