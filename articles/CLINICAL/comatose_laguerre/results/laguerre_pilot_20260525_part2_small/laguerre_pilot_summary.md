# Laguerre Pilot Summary

Pilot cohort: `part2` / `0_12h` with `12` selected subjects per endpoint where available.

## Design

- Subject selection comes from the existing timeline bundle, but the geometry layer is computed from subject-anchored 3D MNPS coordinates read directly from the referenced H5 files.
- Maximum sampled MNPS points per run: `60`
- Minimum runs with valid coordinate paths per subject: `8`
- Local patch neighborhood size: `25`
- Temporal change half-window: `6`

## Cohort Triage

- eligible CPC1 subjects: 67
- eligible CPC5 subjects: 70
- selected CPC1 subjects: 12
- selected CPC5 subjects: 12

## Selected Subjects

- CPC1: sub-0985, sub-0616, sub-0877, sub-0676, sub-0722, sub-0817, sub-0549, sub-0750, sub-0928, sub-0475, sub-0504, sub-0506
- CPC5: sub-0875, sub-0831, sub-0385, sub-0536, sub-0725, sub-0570, sub-0745, sub-0441, sub-0472, sub-0749, sub-0612, sub-0796

## Effect Sizes

| Metric | CPC1 median | CPC5 median | Cohen's d | Cliff's delta | Mann-Whitney p | Direct AUROC |
|---|---:|---:|---:|---:|---:|---:|
| Reachability d_eff median | 2.142 | 1.807 | 1.273 | 0.667 | 0.0061 | 0.833 |
| Reachability A-operator norm median | 1.014 | 1.089 | -1.019 | -0.556 | 0.0226 | 0.778 |
| Laguerre change norm p95 | 4.696 | 5.047 | -0.781 | -0.556 | 0.0226 | 0.778 |
| Laguerre change norm median | 1.889 | 1.908 | -0.723 | -0.431 | 0.0783 | 0.715 |
| Bending norm median | 2.124 | 2.213 | -0.579 | -0.264 | 0.285 | 0.632 |
| Reachability capture gate median | 0.334 | 0.359 | -0.541 | -0.347 | 0.157 | 0.674 |
| Laguerre hourly slope | -0.008 | -0.004 | 0.240 | 0.056 | 0.84 | 0.472 |
| Laguerre persistence | 0.075 | 0.079 | -0.202 | -0.090 | 0.729 | 0.545 |
| Laguerre anisotropy | 1.000 | 1.000 | -0.137 | -0.181 | 0.47 | 0.590 |

## Quick Read

- strongest Laguerre pilot metric: `laguerre_norm_p95` with Cohen's d `-0.781` and direct AUROC `0.778`.
- reachability reference (`tube_d_eff_median`) shows Cohen's d `1.273` and direct AUROC `0.833` in the same subset.
- This remains a bounded feasibility screen on a small subset; any apparent separation should be treated as motivation for the next, more exact pass rather than as a manuscript-ready claim.
