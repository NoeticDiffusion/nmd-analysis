# Part2 validation summary

This note compares the full `part2` validation-side trajectory export against the earlier `part1` discovery-side pass.

## Validation cohort

- source root: `neuralmanifolddynamics_physionet_icare_2_1_20260522_144827_part2_140sub_9d`
- analyzable `0_12h` runs: `1679`
- analyzable extreme-outcome patients: `140`
- `CPC1 = 70`
- `CPC5 = 70`

## Main comparison

### 3D subject-anchored

- `noetic_action`
  - `part1`: `d = -0.278`, `p = 0.290`
  - `part2`: `d = -0.319`, `p = 0.048`
  - read: directional replication with a somewhat cleaner validation-side separation

- `irreversibility`
  - `part1`: `d = -0.429`, `p = 0.081`
  - `part2`: `d = -0.234`, `p = 0.105`
  - read: same direction, but weaker in `part2`

- `entropy_rate`
  - `part1`: `d = 0.027`, `p = 0.540`
  - `part2`: `d = 0.114`, `p = 0.454`
  - read: still weak and not article-facing on present evidence

- `noetic_action_jerk`
  - `part1`: `d = -0.355`, `p = 0.242`
  - `part2`: `d = -0.224`, `p = 0.439`
  - read: same direction, but not a cleaner validation signal than full `3D noetic_action`

- `entropy_production`
  - `part1`: `d = -0.362`, `p = 0.061`
  - `part2`: `d = -0.014`, `p = 0.435`
  - read: failed to validate as a stable `3D` supportive candidate

### 9D subject-anchored

- `noetic_action`
  - `part1`: `d = -0.465`, `p = 0.012`
  - `part2`: `d = -0.253`, `p = 0.536`
  - read: directionally consistent but substantially attenuated in validation

- `noetic_action_jerk`
  - `part1`: `d = -0.375`, `p = 0.136`
  - `part2`: `d = -0.245`, `p = 0.228`
  - read: same direction, still modest, not cleaner than total `9D noetic_action`

- `entropy_rate`
  - `part1`: `d = 0.141`, `p = 0.142`
  - `part2`: `d = 0.186`, `p = 0.163`
  - read: weak but more stable than the other `9D` repertoire-side candidate

- `irreversibility`
  - `part1`: `d = -0.146`, `p = 0.596`
  - `part2`: `d = -0.085`, `p = 0.879`
  - read: weak and not convincing in either cohort

## Bottom line

The clearest validation-side result is now `3D noetic_action`, not `9D noetic_action`.

Current ranking after seeing both cohorts:

1. `3D noetic_action` -> best validation-side support
2. `3D irreversibility` -> directionally replicated but weaker than discovery
3. `9D noetic_action` -> still directionally aligned, but attenuated
4. `9D entropy_rate` -> weak, but more stable than `9D irreversibility`
5. `3D/9D noetic_action_jerk` -> supportive only

Practical implication:

- If the manuscript wants one trajectory-led candidate after `part2`, `3D noetic_action` is now the cleanest choice.
- If the manuscript wants a second, more "time-arrow" flavored companion, `3D irreversibility` is more defensible than `9D irreversibility`.
- The hoped-for `repertoire_entropy_rate` / `irreversible_flux` story is not currently the strongest coma message.
