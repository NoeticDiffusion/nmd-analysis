# Parkinson walking trajectory efficiency exploration

This note checks whether the `analysis_pipeline.py` trajectory-efficiency quantity

`endpoint_dist / path_length`

differs between healthy controls (`HC`) and Parkinson disease (`PD`) during walking in the `ds007526_20260610_121725` bundle.

## Setup

- Coordinate frame: cohort anchored
- Primary check: `3D` trajectory efficiency, matching the pipeline formulation most directly
- Supportive check: analogous `9D` ratio
- Group test: two-sided Mann-Whitney
- Effect direction: `PD - HC`

## Main result

There is no detectable `HC` vs `PD` difference in walking trajectory efficiency.

- `3D` walk trajectory efficiency:
  - `HC` median = `0.03093`
  - `PD` median = `0.02997`
  - median delta (`PD - HC`) = `-0.00096`
  - Cohen's `d` = `0.065`
  - `p = 0.870`
- `9D` walk trajectory efficiency:
  - `HC` median = `0.02895`
  - `PD` median = `0.03030`
  - median delta (`PD - HC`) = `0.00135`
  - Cohen's `d` = `0.020`
  - `p = 0.619`

So the intuitive hypothesis that the Parkinson group would trace a less efficient walking path is not supported in this bundle.

## Why the null is informative

For this dataset, all runs retained all finite windows and every retained run was contiguous (`277 / 277` runs). Under that condition, trajectory efficiency is numerically equal to inverse tortuosity:

- max absolute difference vs `1 / tortuosity` across all runs = `2.78e-17`

So this exploration is not discovering a new orthogonal walking-shape signal. It is a more interpretable restatement of the same path-shape information already implicit in the trajectory export.

## Context

The null trajectory-efficiency result sits alongside a modest, non-significant tendency for `PD` walking to have longer paths:

- `3D` path length: `HC` median = `36.69`, `PD` median = `38.81`, `p = 0.594`
- `9D` path length: `HC` median = `121.30`, `PD` median = `127.40`, `p = 0.313`

This suggests that any extra dynamical "work" in `PD` walking is not showing up here as a clean efficiency loss in endpoint-over-path geometry.

## PD walk clinical hints

Within `PD` walking, lower `3D` trajectory efficiency trends weakly with worse clinical burden, but nothing survives FDR:

- `UPDRS total`: `rho = -0.220`, `p = 0.022`, `q = 0.286`
- `LEDD`: `rho = -0.193`, `p = 0.044`, `q = 0.286`
- `UPDRS part III`: `rho = -0.187`, `p = 0.052`, `q = 0.286`
- `PIGD score`: `rho = -0.179`, `p = 0.063`, `q = 0.286`

These are better treated as severity-aligned hints than as article-facing results.

## Saved outputs

- `trajectory_efficiency_run_metrics.csv`
- `trajectory_efficiency_group_summary.csv`
- `trajectory_efficiency_pd_walk_rho.csv`
- `trajectory_efficiency_pd_walk_rho_fdr.csv`
