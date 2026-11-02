#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "S3 QC - BOAS registered reanalysis",
  subtitle: "Coverage, boundary sensitivity, support failures, and qualification limits",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S3.0 Coverage overview

The source inventory contains 128 processed HDF5 recordings with no read errors. It contains 16,629 selected windows and 1,469 gaps totalling 2,318,850 omitted seconds. The median gap is 480 seconds and the maximum is 18,780 seconds. Window starts are strictly monotonic and no overlaps were found. The selected stage counts are Wake 4,695, N2 5,118, N3 1,854, and REM 4,962; N1 is absent.

= S3.1 Fallback and dimension coverage

PPG fallback is present for 99 recordings, EOG for 26, and EEG high-frequency power for 3. These are separate fallback strata, not interchangeable physiological channels. Both 3D and 9D outputs are retained where serialized. The complete coverage table is `results/article_tables_20260924_v5/table_1_coverage.csv`.

= S3.2 Boundary sensitivity

The boundary-only pass applies the registered same-stage, touching-neighbor rule and fails across gaps. It is a sensitivity reduction over the sampled data. It does not reconstruct a continuous recording, restore missing epochs, or establish effective full-signal support. In the PPG 3D primary table, the full pass has 599 available spectral recording contrasts and the boundary pass has 598.

= S3.3 Support and unavailable values

The A1 minimum support rule is five eligible centers per compared stage. The A2 rule requires finite nominated summaries, positive actual duration, and positive valid sequence support. The six exact 9D rows for `sub-3` and `sub-4` have zero valid sequences at all registered horizons and remain unavailable. No unsupported value is replaced with zero.

= S3.4 Family qualification audit

The A3 ledger keeps computed outputs separate from qualified objects. The diffusion parent is `not_testable` because increment timing is materially irregular. The increment covariance child is `computed`, has sufficient support and positive increment-pair counts, and is explicitly not divided by time and not called an Ito diffusion tensor. Other parent families and unavailable local-dynamics outputs retain their own statuses and failure reasons.

= S3.5 What the robustness checks do and do not show

The full and boundary-only A1 tables agree on the direction of the main descriptive contrasts but differ in exact medians and intervals. This supports arithmetic sensitivity reporting, not biological robustness. The review did not add p-values, permutation tests, leave-one-subject-out claims, or a continuous-support recovery. Fit fidelity and effective temporal signal support remain unevaluated or recorded only at the levels exposed by the source run.

#figure(
  image("figures/registered_v5/figure_2_coverage_and_status.png", width: 100%),
  caption: [Reviewer-facing overview of source coverage, gap durations, FTR usability, and overlapping A3 ledger statuses.]
) <s3-support>

= S3.6 Reviewer-facing verdict

#netn-box(title: [Robustness verdict])[ 
  The frozen package is PASS for reproducible descriptive reporting and METHOD-LIMITED for biological interpretation. It preserves gaps, fallback non-equivalence, unsupported values, and native family qualification limits. It does not establish continuous dynamics, causal sleep-stage effects, independent confirmation, or C1/C2/C3.
]
