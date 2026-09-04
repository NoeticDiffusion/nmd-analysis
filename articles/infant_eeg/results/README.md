# results/

## Canonical export

`figshare_infant_cohort_20260805_132612/` is the **canonical, artifact-masked** export. All numbers, tables, and figures cited in the manuscript and Supplements S1-S4/S6 (`peer_review/pr_02.md` changelog) come from this directory. It reflects the ingest pipeline masking 715 publicly released BAD\_-interval artifact annotations before epoching (5,265 of 6,929 candidate epochs retained) and the corresponding refrozen cohort anchor (hash `45bbfa21...c301a89e`).

### `06_conventional_eeg_age/` provenance note

`06_conventional_eeg_age/` inside the canonical directory is copied from a second, separate H5 re-extraction, `figshare_infant_cohort_20260806_122539/` (raw H5s under `data/raw/neuralmanifolddynamics_figshare_infant_eeg_20260806_122539/`), run one day later with the same 5,265-epoch artifact mask and `conventional_eeg` (tier1/complexity/connectivity) enabled, and a montage/coverage fix so the `connectivity` comparator pack (previously 100% missing) now has 80-96% per-endpoint coverage. Before copying this subfolder over, every shared numeric MNPS/MNJ/reachability column in `01_session_metrics/session_metrics.csv` (including all 12 primary cohort-coordinate endpoints and the cohort anchor's fitted values, despite a different anchor *hash* string) was checked bit-identical between the two exports (max abs difference 0.0). Only the `06_conventional_eeg_age/` outputs come from the `_122539` export; everything else in this directory is unchanged from `_132612`.

## Superseded exports (retained for provenance, not cited anywhere in the article)

- `figshare_infant_20260805/` - earliest export; subject-anchored only, no cohort-coordinate GEE, no cohort-pooled reachability, and predates artifact masking. Superseded by both later exports below.
- `figshare_infant_cohort_20260805/` - first cohort-anchored export with the full pipeline (GEE, within/between decomposition, cluster-permutation check, cohort-pooled reachability), but **predates artifact masking** (BAD\_-interval segments were not yet masked before epoching; anchor hash differs; epoch pool was 6,929, not 5,265). Its numbers are quoted only descriptively, inline, in a few places in S2/S3/`pr_01.md` for before/after comparison — never as the article's primary result.

Each export directory also contains a `smoke_export/` subfolder from pipeline smoke-testing; these are not analysis outputs and can be ignored/pruned independently of the rest of the tree.

R1-R5 can be reproduced from `figshare_infant_cohort_20260805_132612/`. Reproducing R6 additionally requires the coverage-fixed `_20260806_122539` source export and its separate result tree; the two exports must not be silently merged because only the R6 comparator outputs come from `_122539`. The two superseded trees are kept here only so the artifact-masking before/after comparisons in S2.5-S2.8, S3.1-S3.4, and `peer_review/pr_01.md` remain independently checkable.
