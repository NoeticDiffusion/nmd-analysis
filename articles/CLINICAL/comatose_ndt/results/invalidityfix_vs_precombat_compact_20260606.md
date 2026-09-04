# Invalidity-Fix vs pre_combat (Compact)

This compact note compares frozen pooled `pre_combat` anchors against the pooled
invalidity-fix bundle used in the June 2026 manuscript refresh.

## Anchors

- Pooled analyzable subjects: `301` -> `301`
- Pooled H5 runs: `5316` -> `5322`
- `tube_d_eff_median`: `d = +0.513`, `q = 1.39e-04` -> `d = +0.838`, `q = 4.87e-05`
- `persistence_log_eig_var_median`: `d = +0.123`, `q = 1.60e-04` -> `d = +0.736`, `q = 1.14e-04`
- `persistence_kappa_median`: `d = +0.119`, `q = 0.0512` -> `d = +0.147`, `q = 0.913`
- `tube_capture_gate_median`: `d = -0.142`, `q = 0.133` -> `d = -0.558`, `q = 0.0142`
- `tube_a_operator_norm_median`: `d = -0.064`, `q = 0.132` -> `d = -0.124`, `q = 0.886`
- Geometry delta AUROC: `+0.088` -> `+0.036`
- Geometry delta AUPRC: `+0.081` -> `+0.046`
- Geometry delta Brier: `-0.0226` -> `-0.00483`

## Interpretation

The invalidity-fix update preserves pooled cohort size, slightly increases run
coverage, materially strengthens `tube_d_eff_median`, `persistence_log_eig_var_median`,
and `tube_capture_gate_median`, but weakens `persistence_kappa_median` support.
Predictive geometry increments remain positive but are smaller than in the frozen
`pre_combat` comparator.
