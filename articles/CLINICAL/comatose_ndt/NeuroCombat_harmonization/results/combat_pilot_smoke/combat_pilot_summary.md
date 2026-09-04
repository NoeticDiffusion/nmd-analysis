# ComBat Harmonization Pilot

## Scope

- Baseline root: `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_physionet_icare_2_1_20260523_173059_part1_141sub`
- ComBat root: `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_physionet_icare_2_1_20260526_164042_part1_ComBat`
- Common paired run directories: `533`
- Common subjects after aggregation: `71`
- Evidence class: internal pilot using paired H5 exports and internal CV summaries only.

## Main readout

### Site dependence (lower is better if hospital effects are being removed)

- `baseline` / `raw_features`: median_eta2=0.051, p95_eta2=0.230, q<0.05 features=39/97
- `combat` / `raw_features`: median_eta2=0.027, p95_eta2=0.089, q<0.05 features=48/96
- `baseline` / `dynamics_metrics`: median_eta2=0.063, p95_eta2=0.179, q<0.05 features=4/4
- `combat` / `dynamics_metrics`: median_eta2=0.063, p95_eta2=0.097, q<0.05 features=3/4

### Site prediction from subject-level summaries (lower is better for de-batching)

- `baseline` / `raw_features`: balanced_accuracy=0.586, macro_f1=0.572, accuracy=0.623, chance=0.462
- `combat` / `raw_features`: balanced_accuracy=0.468, macro_f1=0.442, accuracy=0.455, chance=0.462
- `baseline` / `dynamics_metrics`: balanced_accuracy=0.288, macro_f1=0.228, accuracy=0.251, chance=0.462
- `combat` / `dynamics_metrics`: balanced_accuracy=0.345, macro_f1=0.274, accuracy=0.307, chance=0.462

### CPC1 vs CPC5 prediction (higher ROC AUC/AUPRC and lower Brier are better)

- `baseline` / `raw_features` / `repeated_stratified_cv`: roc_auc=0.663, auprc=0.668, brier=0.264, n_features=97
- `combat` / `raw_features` / `repeated_stratified_cv`: roc_auc=0.556, auprc=0.579, brier=0.325, n_features=96
- `baseline` / `raw_features` / `leave_one_site_out`: roc_auc=0.702, auprc=0.623, brier=0.277, n_features=97
- `combat` / `raw_features` / `leave_one_site_out`: roc_auc=0.683, auprc=0.611, brier=0.341, n_features=96
- `baseline` / `dynamics_metrics` / `repeated_stratified_cv`: roc_auc=0.676, auprc=0.650, brier=0.228, n_features=4
- `combat` / `dynamics_metrics` / `repeated_stratified_cv`: roc_auc=0.663, auprc=0.647, brier=0.237, n_features=4
- `baseline` / `dynamics_metrics` / `leave_one_site_out`: roc_auc=0.668, auprc=0.602, brier=0.237, n_features=4
- `combat` / `dynamics_metrics` / `leave_one_site_out`: roc_auc=0.656, auprc=0.610, brier=0.232, n_features=4

## Paired dynamics shifts

- `dyn__mnps_rms`: median pct change `+1.717%`, p95 abs pct `30.407%` over `533` paired runs
- `dyn__mnps_speed`: median pct change `+1.027%`, p95 abs pct `29.737%` over `533` paired runs
- `dyn__mnj_fro`: median pct change `+2.409%`, p95 abs pct `53.712%` over `533` paired runs
- `dyn__mnjdot_fro`: median pct change `+2.300%`, p95 abs pct `52.691%` over `533` paired runs

## Interpretation guardrails

- Reduced site dependence is direct evidence that ComBat is removing hospital-linked structure, but it does not by itself prove improved clinical utility.
- Improved CPC discrimination under leave-one-site-out is the strongest pilot signal that harmonization is helping generalization across hospitals rather than just reshaping feature marginals.
- These are internal retrospective checks on one paired export set and should be read as pilot evidence, not as a final theorem about harmonization.
