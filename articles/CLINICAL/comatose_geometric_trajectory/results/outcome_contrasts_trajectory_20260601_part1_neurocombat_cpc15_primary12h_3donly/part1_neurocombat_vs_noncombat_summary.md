# Part1 NeuroComBat vs non-ComBat trajectory comparison

## Scope

This comparison asks whether the new `part1` NeuroComBat-cleaned root improves the same trajectory outcome contrasts that were previously measured on the original `part1` export.

The intended full `3D + 9D` rerun was **not** possible on the NeuroComBat root in its current form. The timeline export shows `coords_9d_row_valid_fraction = 0.0` for all `3104` runs, so the current trajectory pipeline has no usable finite `9D` rows to fit or score. The comparison below is therefore a strict `3D` comparison only.

## Cohort support

- Non-ComBat `part1 3D`: `71 CPC1` vs `70 CPC5`
- NeuroComBat `part1 3D`: `70 CPC1` vs `69 CPC5`
- Subjects missing from the NeuroComBat comparison set: `sub-0512` (`CPC5`, hospital `E`) and `sub-0977` (`CPC1`, hospital `D`)

## Main comparison

- `3D noetic_action` improved under NeuroComBat. It moved from `d = -0.278`, `p = 0.290` in the original `part1` export to `d = -0.339`, `p = 0.0209` after NeuroComBat cleaning. This is the clearest sign that the cleaned root may be reducing nuisance variance for the broad action / friction signal.
- `3D irreversibility` did **not** improve. It weakened from `d = -0.429`, `p = 0.081` to `d = -0.330`, `p = 0.254`. So the cleaner `time-arrow`-like readout in the original analysis does not appear to be strengthened by NeuroComBat.
- `3D entropy_rate` remained weak in both versions and is still not a lead candidate.

## Supportive rows

- `3D noetic_action_jerk` became somewhat stronger in absolute effect size (`d = -0.355` to `-0.451`), but still did not become a clean primary row.
- `3D noetic_action_potential` also strengthened modestly (`d = -0.098` to `-0.216`) and moved closer to nominal significance.
- `3D entropy_production` weakened substantially (`d = -0.362` to `-0.171`), which again points away from a simple "cleaner temporal asymmetry" story.

## Bottom line

- If the question is whether NeuroComBat makes the broad `3D` trajectory separator cleaner, the answer is provisionally **yes for `3D noetic_action`**.
- If the question is whether NeuroComBat strengthens the more order-sensitive asymmetry story, the answer is **no for `3D irreversibility`**.
- Right now the cleaned root supports the existing interpretation shift rather than reversing it: the action / friction family benefits more than the narrow time-arrow family.
- A proper `9D` comparison will require either a repaired NeuroComBat export or an explicit downstream policy for handling the currently all-invalid `9D` rows.
