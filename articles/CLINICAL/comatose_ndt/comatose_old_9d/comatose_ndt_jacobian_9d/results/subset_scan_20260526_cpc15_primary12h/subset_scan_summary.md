# Exploratory Jacobian 9D Subset Scan

> This export is exploratory and post hoc. The same pooled cohort was used for subset search and evaluation, and no nested CV or external validation was added here.

- n_subjects: `281`
- CPC1: `141`
- CPC5: `140`
- full revised `9D` family: repeated-CV AUROC `0.676`
- full `clinical+qEEG+reachability+9D` ladder: repeated-CV AUROC `0.710`, LOSO AUROC `0.668`

## Best revised 9D-only subsets

### Singletons

- `anisotropy_abs_eig_median`, repeated-CV AUROC `0.703 [0.595, 0.823]`, AUPRC `0.647`, Brier `0.220`, LOSO AUROC `0.683`, delta vs base `+0.028`
- `spectral_radius_median`, repeated-CV AUROC `0.703 [0.583, 0.813]`, AUPRC `0.649`, Brier `0.224`, LOSO AUROC `0.670`, delta vs base `+0.027`
- `rotational_power_mean`, repeated-CV AUROC `0.640 [0.478, 0.748]`, AUPRC `0.605`, Brier `0.241`, LOSO AUROC `0.621`, delta vs base `-0.035`
- `mdr_median`, repeated-CV AUROC `0.624 [0.488, 0.759]`, AUPRC `0.587`, Brier `0.246`, LOSO AUROC `0.651`, delta vs base `-0.051`
- `rotational_power_median`, repeated-CV AUROC `0.599 [0.445, 0.727]`, AUPRC `0.573`, Brier `0.248`, LOSO AUROC `0.582`, delta vs base `-0.077`

### Pairs

- `spectral_radius_median+anisotropy_abs_eig_median`, repeated-CV AUROC `0.702 [0.590, 0.826]`, AUPRC `0.644`, Brier `0.221`, LOSO AUROC `0.672`, delta vs base `+0.026`
- `anisotropy_abs_eig_median+rotational_power_mean`, repeated-CV AUROC `0.698 [0.587, 0.822]`, AUPRC `0.640`, Brier `0.223`, LOSO AUROC `0.678`, delta vs base `+0.022`
- `anisotropy_abs_eig_median+rotational_power_median`, repeated-CV AUROC `0.695 [0.593, 0.819]`, AUPRC `0.636`, Brier `0.223`, LOSO AUROC `0.680`, delta vs base `+0.019`
- `anisotropy_abs_eig_median+mdr_median`, repeated-CV AUROC `0.693 [0.584, 0.804]`, AUPRC `0.634`, Brier `0.222`, LOSO AUROC `0.632`, delta vs base `+0.017`
- `spectral_radius_median+rotational_power_mean`, repeated-CV AUROC `0.692 [0.565, 0.809]`, AUPRC `0.635`, Brier `0.228`, LOSO AUROC `0.665`, delta vs base `+0.016`

### Triples

- `anisotropy_abs_eig_median+rotational_power_mean+rotational_power_median`, repeated-CV AUROC `0.696 [0.596, 0.826]`, AUPRC `0.634`, Brier `0.222`, LOSO AUROC `0.680`, delta vs base `+0.020`
- `spectral_radius_median+anisotropy_abs_eig_median+rotational_power_mean`, repeated-CV AUROC `0.693 [0.569, 0.815]`, AUPRC `0.633`, Brier `0.225`, LOSO AUROC `0.667`, delta vs base `+0.017`
- `spectral_radius_median+rotational_power_mean+rotational_power_median`, repeated-CV AUROC `0.687 [0.567, 0.807]`, AUPRC `0.633`, Brier `0.225`, LOSO AUROC `0.678`, delta vs base `+0.012`
- `spectral_radius_median+anisotropy_abs_eig_median+rotational_power_median`, repeated-CV AUROC `0.686 [0.566, 0.813]`, AUPRC `0.629`, Brier `0.223`, LOSO AUROC `0.671`, delta vs base `+0.011`
- `anisotropy_abs_eig_median+mdr_median+rotational_power_median`, repeated-CV AUROC `0.683 [0.581, 0.803]`, AUPRC `0.624`, Brier `0.223`, LOSO AUROC `0.623`, delta vs base `+0.007`

## Best revised 9D subsets added to `clinical+qEEG`

- `spectral_radius_median+anisotropy_abs_eig_median`, repeated-CV AUROC `0.698 [0.581, 0.806]`, AUPRC `0.643`, Brier `0.224`, LOSO AUROC `0.653`, delta vs base `+0.004`
- `spectral_radius_median+anisotropy_abs_eig_median+rotational_power_mean`, repeated-CV AUROC `0.698 [0.579, 0.808]`, AUPRC `0.642`, Brier `0.224`, LOSO AUROC `0.656`, delta vs base `+0.004`
- `anisotropy_abs_eig_median+rotational_power_mean`, repeated-CV AUROC `0.697 [0.569, 0.814]`, AUPRC `0.646`, Brier `0.223`, LOSO AUROC `0.654`, delta vs base `+0.004`
- `spectral_radius_median+anisotropy_abs_eig_median+rotational_power_mean+rotational_power_median`, repeated-CV AUROC `0.696 [0.566, 0.809]`, AUPRC `0.640`, Brier `0.225`, LOSO AUROC `0.658`, delta vs base `+0.002`
- `spectral_radius_median+anisotropy_abs_eig_median+rotational_power_median`, repeated-CV AUROC `0.696 [0.566, 0.808]`, AUPRC `0.639`, Brier `0.225`, LOSO AUROC `0.658`, delta vs base `+0.002`

## Best revised 9D subsets added to `clinical+qEEG+reachability`

- `anisotropy_abs_eig_median+rotational_power_mean`, repeated-CV AUROC `0.716 [0.584, 0.832]`, AUPRC `0.673`, Brier `0.220`, LOSO AUROC `0.679`, delta vs base `+0.006`
- `anisotropy_abs_eig_median+rotational_power_median`, repeated-CV AUROC `0.716 [0.592, 0.819]`, AUPRC `0.671`, Brier `0.220`, LOSO AUROC `0.674`, delta vs base `+0.005`
- `anisotropy_abs_eig_median+rotational_power_mean+rotational_power_median`, repeated-CV AUROC `0.716 [0.592, 0.817]`, AUPRC `0.671`, Brier `0.220`, LOSO AUROC `0.678`, delta vs base `+0.005`
- `spectral_radius_median+anisotropy_abs_eig_median+rotational_power_mean`, repeated-CV AUROC `0.714 [0.585, 0.824]`, AUPRC `0.668`, Brier `0.221`, LOSO AUROC `0.675`, delta vs base `+0.003`
- `spectral_radius_median+anisotropy_abs_eig_median+rotational_power_mean+rotational_power_median`, repeated-CV AUROC `0.714 [0.591, 0.824]`, AUPRC `0.667`, Brier `0.221`, LOSO AUROC `0.675`, delta vs base `+0.003`

## Best mixed cross-family pairs

- `anisotropy_abs_eig_median+persistence_log_eig_var_median`, repeated-CV AUROC `0.709 [0.595, 0.825]`, AUPRC `0.658`, Brier `0.219`, LOSO AUROC `0.692`
- `spectral_radius_median+persistence_log_eig_var_median`, repeated-CV AUROC `0.707 [0.584, 0.818]`, AUPRC `0.659`, Brier `0.223`, LOSO AUROC `0.678`
- `anisotropy_abs_eig_median+persistence_kappa_median`, repeated-CV AUROC `0.705 [0.541, 0.823]`, AUPRC `0.653`, Brier `0.220`, LOSO AUROC `0.691`
- `spectral_radius_median+persistence_kappa_median`, repeated-CV AUROC `0.705 [0.545, 0.817]`, AUPRC `0.655`, Brier `0.224`, LOSO AUROC `0.677`
- `rotational_power_mean+tube_d_eff_median`, repeated-CV AUROC `0.702 [0.577, 0.804]`, AUPRC `0.666`, Brier `0.215`, LOSO AUROC `0.679`

## Best mixed cross-family triples

- `anisotropy_abs_eig_median+persistence_kappa_median+persistence_log_eig_var_median`, repeated-CV AUROC `0.707 [0.595, 0.825]`, AUPRC `0.656`, Brier `0.220`, LOSO AUROC `0.691`
- `rotational_power_mean+tube_d_eff_median+persistence_log_eig_var_median`, repeated-CV AUROC `0.707 [0.575, 0.811]`, AUPRC `0.673`, Brier `0.214`, LOSO AUROC `0.689`
- `spectral_radius_median+anisotropy_abs_eig_median+persistence_log_eig_var_median`, repeated-CV AUROC `0.707 [0.591, 0.827]`, AUPRC `0.654`, Brier `0.220`, LOSO AUROC `0.681`
- `rotational_power_mean+tube_d_eff_median+persistence_kappa_median`, repeated-CV AUROC `0.706 [0.575, 0.811]`, AUPRC `0.671`, Brier `0.214`, LOSO AUROC `0.688`
- `spectral_radius_median+persistence_kappa_median+persistence_log_eig_var_median`, repeated-CV AUROC `0.706 [0.573, 0.818]`, AUPRC `0.657`, Brier `0.224`, LOSO AUROC `0.677`

## Best `clinical+qEEG` plus mixed cross-family subsets

- `anisotropy_abs_eig_median+tube_d_eff_median`, repeated-CV AUROC `0.709 [0.589, 0.823]`, AUPRC `0.667`, Brier `0.223`, LOSO AUROC `0.644`, delta vs base `+0.121`
- `rotational_power_mean+tube_d_eff_median`, repeated-CV AUROC `0.704 [0.589, 0.804]`, AUPRC `0.657`, Brier `0.225`, LOSO AUROC `0.634`, delta vs base `+0.116`
- `rotational_power_median+tube_d_eff_median`, repeated-CV AUROC `0.702 [0.584, 0.795]`, AUPRC `0.656`, Brier `0.226`, LOSO AUROC `0.636`, delta vs base `+0.114`
- `spectral_radius_median+tube_d_eff_median`, repeated-CV AUROC `0.699 [0.585, 0.804]`, AUPRC `0.649`, Brier `0.226`, LOSO AUROC `0.636`, delta vs base `+0.111`
- `anisotropy_abs_eig_median+persistence_log_eig_var_median`, repeated-CV AUROC `0.696 [0.557, 0.818]`, AUPRC `0.652`, Brier `0.225`, LOSO AUROC `0.650`, delta vs base `+0.107`
- `anisotropy_abs_eig_median+rotational_power_mean+tube_d_eff_median`, repeated-CV AUROC `0.714 [0.598, 0.818]`, AUPRC `0.668`, Brier `0.220`, LOSO AUROC `0.653`, delta vs base `+0.126`
- `anisotropy_abs_eig_median+rotational_power_median+tube_d_eff_median`, repeated-CV AUROC `0.713 [0.592, 0.811]`, AUPRC `0.666`, Brier `0.221`, LOSO AUROC `0.652`, delta vs base `+0.125`
- `anisotropy_abs_eig_median+tube_d_eff_median+tube_capture_gate_median`, repeated-CV AUROC `0.711 [0.595, 0.827]`, AUPRC `0.671`, Brier `0.222`, LOSO AUROC `0.655`, delta vs base `+0.123`
- `anisotropy_abs_eig_median+tube_d_eff_median+persistence_log_eig_var_median`, repeated-CV AUROC `0.711 [0.578, 0.838]`, AUPRC `0.670`, Brier `0.222`, LOSO AUROC `0.652`, delta vs base `+0.122`
- `anisotropy_abs_eig_median+tube_d_eff_median+persistence_kappa_median`, repeated-CV AUROC `0.710 [0.577, 0.838]`, AUPRC `0.670`, Brier `0.223`, LOSO AUROC `0.652`, delta vs base `+0.122`

## Appendix trio check

- `rotational_power_mean+tube_d_eff_median+persistence_log_eig_var_median`, repeated-CV AUROC `0.707 [0.575, 0.811]`, AUPRC `0.673`, Brier `0.214`, LOSO AUROC `0.689`

## Interpretation guardrails

- Treat the ranked subsets as exploratory search outputs, not frozen article claims.
- The cleanest manuscript-facing use is to support appendix language about complementarity and redundancy, not to replace the current frozen predictive ladder.
- If any subset is promoted beyond appendix status, the next step should be nested CV or a truly held-out evaluation.
