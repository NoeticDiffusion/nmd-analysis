# Trajectory efficiency exploratory note

Date: 2026-06-12

After adding `traj_efficiency` to `ndt-analysis`, we reran the psychosis
cohort-anchor analysis and refreshed the article-facing exports.

## Short result

- `traj_efficiency` now flows correctly through the real psychosis pipeline.
- In this dataset, it does **not** emerge as a strong or corrected signal.
- If any of the new simple path metrics are worth mentioning later,
  `endpoint_dist` looks more promising in `ds003944` and `path_length` looks
  more promising in `ds003947`.
- Neither of those metrics is strong enough to replace the current trajectory
  headline `m_delta_mean_median`.

## Practical conclusion

For now, the psychosis manuscript should stay as it is:

- keep `m_delta_mean_median` as the trajectory-facing result,
- treat `endpoint_dist` / `path_length` as exploratory side observations,
- and do not promote `traj_efficiency` in the article text at this stage.
