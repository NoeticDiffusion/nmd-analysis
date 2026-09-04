#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary Quality Control and Robustness",
  short-title: "APPLESEED QC",
  subtitle: "Export-contract audit and sensitivity checks",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S3.1 Contract and coverage audit
The frozen run manifest and wrapper audit both identified 48 H5 files, 13 unique children, and 11 complete four-session children. All recordings had valid cohort-anchored 3D coordinates and 3D Jacobians; 38 geometry contracts were `ok` and 10 were `adjusted`. The 9D Jacobian was available in 46/48 sessions. `sub-10/ses-4` retained zero 9D Jacobian windows after 140 invalid windows, and `sub-13/ses-2` retained zero after 155 invalid windows; they are excluded only from 9D-Jacobian analyses. This supports computation of the exported session summaries, but does not validate a biological or developmental interpretation of them.

The H5 contract contains subject- and cohort-anchored 3D/9D layers. The common cohort scale uses anchor `ds003710_global_cohort_all_timepoints_iqr_v2_1` (hash `cb876d...d7a6fd7`), subject-balanced over 8,179 epochs. Cohort-anchored coordinate comparisons are therefore valid descriptive comparisons within this export; because the anchor includes all study ages, they are not held-out-age or predictive claims.

= S3.2 Session-level aggregation
The wrapper writes exactly one metric row per child-session. Epochs, windows, and local-neighborhood fits affect the within-session median only. The test--retest and longitudinal statistics consequently use 13 and 11 independent child rows, respectively, rather than treating thousands of windows as independent observations.

= S3.3 Reachability configuration
The frozen configuration was:

```text
coordinate contract: cohort_anchored
space: 3d
k: 12
horizon: 3
estimator: ridge (alpha 0.001)
aggregation: median
```

This fixed configuration guards against choosing a $k$ or horizon after inspecting outcome contrasts. It does not establish that other local-scale settings would have the same behavior.

= S3.4 Bootstrap and retest baseline sensitivity
ICC uncertainty used 2,000 bootstrap draws that resampled children as clusters. The primary four-month-mean contrasts are not labelled as sensitivity analyses. The stored retest-mean output applies one pooled 18-test BH family to those same nine-endpoint session 3 and session 4 contrasts and produced no FDR-significant result (minimum adjusted p=0.618). Session-1-only and Friedman outputs are the secondary baseline sensitivities; the nominal Friedman result for `tube_d_eff` was raw p=0.020 and nine-test FDR p=0.177, with no session-1 contrast FDR-supported.

= S3.5 Exploratory event analysis
The event wrapper reads the H5 `event_windows` mapping for object, water, speech, and face labels. It computes per-event contrasts against the `pre_near` bin, averages them across available sessions within child, and performs a 2,000-draw sign-flip test. The 12 event-by-axis tests use a separate family. The water-deviation contrast had raw p=0.0055 and BH p=0.066. This output is separated from the primary reliability family; ages are pooled and session counts differ. Three low-label sessions (`sub-08/ses-2`, 0.5%; `sub-13/ses-2`, 0.6%; and `sub-07/ses-2`, 2.5%) contributed no usable event/pre-near pair to the exported tests; the minimum stage-label fraction among contributing event sessions was 15.3%. Any nominal event effect is therefore only a prompt for a confirmatory study.

= S3.6 Machine-readable outputs
`01_session_metrics/session_metrics.csv` contains the session endpoints; `session_qc.csv` contains the contract/QC audit; `02_reliability_longitudinal/` contains all reliability and paired-contrast estimates; and `03_event_locked_exploratory/` contains the optional event analysis. The `export_manifest.json` records input path, exact cohort counts, contract, and reachability settings.
