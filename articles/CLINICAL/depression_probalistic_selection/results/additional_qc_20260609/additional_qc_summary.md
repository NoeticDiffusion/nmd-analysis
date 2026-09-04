# Depression PST supplementary QC / robustness summary

This supplement-facing QC pass focuses on three practical review questions:

1. how many usable subjects support each selected task and paired block,
2. how stable the event-family coverage is across subjects,
3. and whether the selected rows preserve direction under leave-one-subject-out omission.

## Selected block coverage

- `task_only` / `Task 3D MNPS` / `d_median`: total `122`, low `76`, mid `15`, high `30`.
- `task_only` / `Task 9D MNPS` / `d_s_mean`: total `122`, low `76`, mid `15`, high `30`.
- `task_only` / `Task 3D MNJ` / `spectral_radius_median`: total `122`, low `76`, mid `15`, high `30`.
- `task_only` / `Task 9D MNJ` / `rotational_power_mean`: total `70`, low `38`, mid `12`, high `20`.
- `task_only` / `Task 9x9 block MNJ` / `block_frobenius_mean`: total `70`, low `38`, mid `12`, high `20`.
- `task_only` / `Task reachability` / `tube_log_eig_var_mean`: total `69`, low `37`, mid `12`, high `20`.
- `task_only` / `Task tier-2 EMMI` / `mv_median`: total `122`, low `76`, mid `15`, high `30`.
- `task_only` / `Task distribution summary` / `e_m_mad_sigma`: total `122`, low `76`, mid `15`, high `30`.
- `paired_delta` / `Block MNJ m->m` / `block_frobenius_mean`: total `70`, low `38`, mid `12`, high `20`.
- `paired_delta` / `Distribution summary` / `e_m_mad_sigma`: total `122`, low `76`, mid `15`, high `30`.
- `paired_delta` / `Tier-2 EMMI` / `mv_median`: total `122`, low `76`, mid `15`, high `30`.
- `paired_delta` / `3D MNJ` / `spectral_radius_median`: total `122`, low `76`, mid `15`, high `30`.
- `paired_delta` / `9D MNJ` / `rotational_power_mean`: total `70`, low `38`, mid `12`, high `20`.
- `paired_delta` / `3D MNPS` / `d_median`: total `122`, low `76`, mid `15`, high `30`.
- `paired_delta` / `9D MNPS` / `d_s_mean`: total `122`, low `76`, mid `15`, high `30`.
- `paired_delta` / `Reachability` / `tube_log_eig_var_mean`: total `69`, low `37`, mid `12`, high `20`.

## Event coverage

- `feedback_correct` / `event`: `n_subjects = 122`, median events `94.5`, median rows `94.5`.
- `feedback_correct` / `post_far`: `n_subjects = 122`, median events `126`, median rows `630`.
- `feedback_correct` / `post_near`: `n_subjects = 122`, median events `126`, median rows `220`.
- `feedback_correct` / `pre_far`: `n_subjects = 122`, median events `126`, median rows `630`.
- `feedback_correct` / `pre_near`: `n_subjects = 122`, median events `126`, median rows `316.5`.
- `feedback_incorrect` / `event`: `n_subjects = 122`, median events `78.5`, median rows `78.5`.
- `feedback_incorrect` / `post_far`: `n_subjects = 122`, median events `106`, median rows `530`.
- `feedback_incorrect` / `post_near`: `n_subjects = 122`, median events `106`, median rows `185.5`.
- `feedback_incorrect` / `pre_far`: `n_subjects = 122`, median events `106`, median rows `530`.
- `feedback_incorrect` / `pre_near`: `n_subjects = 122`, median events `106`, median rows `265.5`.
- `left_response` / `event`: `n_subjects = 122`, median events `144`, median rows `144`.
- `left_response` / `post_far`: `n_subjects = 122`, median events `190`, median rows `936.5`.
- `left_response` / `post_near`: `n_subjects = 122`, median events `192`, median rows `341`.
- `left_response` / `pre_far`: `n_subjects = 122`, median events `192.5`, median rows `962.5`.
- `left_response` / `pre_near`: `n_subjects = 122`, median events `192.5`, median rows `481.5`.
- `right_response` / `event`: `n_subjects = 122`, median events `143.5`, median rows `143.5`.
- `right_response` / `post_far`: `n_subjects = 122`, median events `189`, median rows `939`.
- `right_response` / `post_near`: `n_subjects = 122`, median events `192`, median rows `334`.
- `right_response` / `pre_far`: `n_subjects = 122`, median events `188.5`, median rows `942.5`.
- `right_response` / `pre_near`: `n_subjects = 122`, median events `191.5`, median rows `473`.
- `test_stim_any` / `event`: `n_subjects = 122`, median events `90`, median rows `90`.
- `test_stim_any` / `post_far`: `n_subjects = 122`, median events `116`, median rows `559`.
- `test_stim_any` / `post_near`: `n_subjects = 122`, median events `119`, median rows `207`.
- `test_stim_any` / `pre_far`: `n_subjects = 122`, median events `120`, median rows `600`.
- `test_stim_any` / `pre_near`: `n_subjects = 122`, median events `120`, median rows `299`.
- `train_stim_any` / `event`: `n_subjects = 122`, median events `177`, median rows `177`.
- `train_stim_any` / `post_far`: `n_subjects = 122`, median events `240`, median rows `1200`.
- `train_stim_any` / `post_near`: `n_subjects = 122`, median events `240`, median rows `418`.
- `train_stim_any` / `pre_far`: `n_subjects = 122`, median events `240`, median rows `1200`.
- `train_stim_any` / `pre_near`: `n_subjects = 122`, median events `240`, median rows `598.5`.

## Leave-one-subject-out stability

- `task_only` / `Task 3D MNPS` / `d_median`: full `d = -0.1448`, leave-one-out `d` range `-0.1976` to `-0.09328`, sign consistency `1`; full `rho = -0.04143`, leave-one-out `rho` range `-0.06143` to `-0.01783`.
- `task_only` / `Task 9D MNPS` / `d_s_mean`: full `d = -0.09868`, leave-one-out `d` range `-0.176` to `-0.0566`, sign consistency `1`; full `rho = -0.05524`, leave-one-out `rho` range `-0.07921` to `-0.03319`.
- `task_only` / `Task 3D MNJ` / `spectral_radius_median`: full `d = 0.06927`, leave-one-out `d` range `-0.00632` to `0.1469`, sign consistency `0.9918`; full `rho = 0.08148`, leave-one-out `rho` range `0.06141` to `0.1046`.
- `task_only` / `Task 9D MNJ` / `rotational_power_mean`: full `d = 0.2139`, leave-one-out `d` range `0.1289` to `0.2602`, sign consistency `1`; full `rho = 0.0108`, leave-one-out `rho` range `-0.02907` to `0.03827`.
- `task_only` / `Task 9x9 block MNJ` / `block_frobenius_mean`: full `d = -0.7785`, leave-one-out `d` range `-0.8662` to `-0.7415`, sign consistency `1`; full `rho = -0.3447`, leave-one-out `rho` range `-0.3969` to `-0.3201`.
- `task_only` / `Task reachability` / `tube_log_eig_var_mean`: full `d = -0.7185`, leave-one-out `d` range `-0.7558` to `-0.683`, sign consistency `1`; full `rho = -0.3977`, leave-one-out `rho` range `-0.4529` to `-0.3754`.
- `task_only` / `Task tier-2 EMMI` / `mv_median`: full `d = -0.00448`, leave-one-out `d` range `-0.07876` to `0.07893`, sign consistency `0.8361`; full `rho = -0.002192`, leave-one-out `rho` range `-0.02277` to `0.0191`.
- `task_only` / `Task distribution summary` / `e_m_mad_sigma`: full `d = 0.506`, leave-one-out `d` range `0.4415` to `0.6989`, sign consistency `1`; full `rho = 0.3125`, leave-one-out `rho` range `0.2954` to `0.3318`.
- `paired_delta` / `3D MNPS` / `d_median`: full `d = -0.1653`, leave-one-out `d` range `-0.2231` to `-0.1108`, sign consistency `1`; full `rho = -0.009809`, leave-one-out `rho` range `-0.03128` to `0.01134`.
- `paired_delta` / `9D MNPS` / `d_s_mean`: full `d = 0.1259`, leave-one-out `d` range `0.05725` to `0.1905`, sign consistency `1`; full `rho = 0.0564`, leave-one-out `rho` range `0.03642` to `0.07551`.
- `paired_delta` / `3D MNJ` / `spectral_radius_median`: full `d = 0.03553`, leave-one-out `d` range `-0.02942` to `0.1261`, sign consistency `0.9672`; full `rho = 0.09588`, leave-one-out `rho` range `0.07684` to `0.1199`.
- `paired_delta` / `9D MNJ` / `rotational_power_mean`: full `d = -0.147`, leave-one-out `d` range `-0.2731` to `-0.07277`, sign consistency `1`; full `rho = 0.03136`, leave-one-out `rho` range `-0.007629` to `0.06637`.
- `paired_delta` / `Block MNJ m->m` / `block_frobenius_mean`: full `d = 0.08499`, leave-one-out `d` range `0.02754` to `0.2052`, sign consistency `1`; full `rho = 0.1332`, leave-one-out `rho` range `0.0996` to `0.1729`.
- `paired_delta` / `Reachability` / `tube_log_eig_var_mean`: full `d = -0.13`, leave-one-out `d` range `-0.2621` to `0.01605`, sign consistency `0.9855`; full `rho = -0.06085`, leave-one-out `rho` range `-0.1029` to `-0.0243`.
- `paired_delta` / `Tier-2 EMMI` / `mv_median`: full `d = 0.3368`, leave-one-out `d` range `0.2331` to `0.4051`, sign consistency `1`; full `rho = 0.04015`, leave-one-out `rho` range `0.01643` to `0.06087`.
- `paired_delta` / `Distribution summary` / `e_m_mad_sigma`: full `d = -0.2603`, leave-one-out `d` range `-0.3243` to `-0.1388`, sign consistency `1`; full `rho = -0.009908`, leave-one-out `rho` range `-0.03347` to `0.009664`.

## Notes

- The `9D` Jacobian, block-MNJ, and reachability rows use smaller valid denominators than the full cohort and should be read with those denominators visible.
- Leave-one-subject-out omission is a directional stability check only; it is not an external replication test.
