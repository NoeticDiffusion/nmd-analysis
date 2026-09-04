# ComBat Harmonization Pilot

## Scope

- Baseline root: `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_physionet_icare_2_1_20260523_173059_part1_141sub`
- ComBat root: `J:\repos\NoeticDiffusion\data\raw\neuralmanifolddynamics_physionet_icare_2_1_20260526_164042_part1_ComBat`
- Common paired run directories: `3066`
- Common subjects after aggregation: `159`
- CPC1/CPC5 subjects after aggregation: `139`
- Evidence class: internal pilot using paired H5 exports and internal CV summaries only.

## Main readout

### Site dependence (lower is better if hospital effects are being removed)

- `baseline` / `raw_features`: median_eta2=0.050, p95_eta2=0.209, q<0.05 features=56/97
- `combat` / `raw_features`: median_eta2=0.028, p95_eta2=0.110, q<0.05 features=52/96
- `baseline` / `dynamics_metrics`: median_eta2=0.042, p95_eta2=0.168, q<0.05 features=3/4
- `combat` / `dynamics_metrics`: median_eta2=0.058, p95_eta2=0.120, q<0.05 features=4/4

### Site prediction from subject-level summaries (lower is better for de-batching)

- `baseline` / `raw_features`: balanced_accuracy=0.591, macro_f1=0.578, accuracy=0.656, chance=0.459
- `combat` / `raw_features`: balanced_accuracy=0.478, macro_f1=0.463, accuracy=0.496, chance=0.459
- `baseline` / `dynamics_metrics`: balanced_accuracy=0.262, macro_f1=0.235, accuracy=0.309, chance=0.459
- `combat` / `dynamics_metrics`: balanced_accuracy=0.358, macro_f1=0.273, accuracy=0.264, chance=0.459

### CPC1 vs CPC5 prediction (higher ROC AUC/AUPRC and lower Brier are better)

- `baseline` / `raw_features` / `repeated_stratified_cv`: roc_auc=0.748, auprc=0.727, brier=0.211, n_features=97
- `combat` / `raw_features` / `repeated_stratified_cv`: roc_auc=0.725, auprc=0.726, brier=0.230, n_features=96
- `baseline` / `raw_features` / `leave_one_site_out`: roc_auc=0.755, auprc=0.684, brier=0.259, n_features=97
- `combat` / `raw_features` / `leave_one_site_out`: roc_auc=0.696, auprc=0.650, brier=0.318, n_features=96
- `baseline` / `dynamics_metrics` / `repeated_stratified_cv`: roc_auc=0.664, auprc=0.640, brier=0.231, n_features=4
- `combat` / `dynamics_metrics` / `repeated_stratified_cv`: roc_auc=0.604, auprc=0.588, brier=0.246, n_features=4
- `baseline` / `dynamics_metrics` / `leave_one_site_out`: roc_auc=0.613, auprc=0.583, brier=0.238, n_features=4
- `combat` / `dynamics_metrics` / `leave_one_site_out`: roc_auc=0.620, auprc=0.592, brier=0.269, n_features=4

## Paired dynamics shifts

- `dyn__mnps_rms`: median pct change `+1.786%`, p95 abs pct `33.122%` over `3066` paired runs
- `dyn__mnps_speed`: median pct change `+1.206%`, p95 abs pct `30.281%` over `3066` paired runs
- `dyn__mnj_fro`: median pct change `+2.505%`, p95 abs pct `54.943%` over `3066` paired runs
- `dyn__mnjdot_fro`: median pct change `+2.560%`, p95 abs pct `56.575%` over `3066` paired runs

## Interpretation guardrails

- Reduced site dependence is direct evidence that ComBat is removing hospital-linked structure, but it does not by itself prove improved clinical utility.
- Improved CPC discrimination under leave-one-site-out is the strongest pilot signal that harmonization is helping generalization across hospitals rather than just reshaping feature marginals.
- These are internal retrospective checks on one paired export set and should be read as pilot evidence, not as a final theorem about harmonization.
