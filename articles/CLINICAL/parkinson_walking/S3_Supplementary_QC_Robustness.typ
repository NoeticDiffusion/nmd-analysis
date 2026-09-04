#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness - Walking-State Geometry in Parkinson Disease",
  short-title: "Walking Supplementary QC",
  subtitle: "Mixed-contract defensibility, evidence ranking, and review-facing cautions for ds007526",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope

This supplement collects the review-facing material that is important for defensibility but intentionally compressed in the main article:

- why the mixed-anchor rule is methodologically stronger than a one-anchor writeup,
- how the article separates primary, supportive, secondary, and exploratory branches,
- what happens to the revised focal rows under leave-one-subject-out omission,
- what happens to the exploratory trajectory rows under a within-run time-reshuffle null,
- why the regional and reachability layers are kept below headline status,
- why the trajectory layer remains exploratory,
- and why no classical EEG comparison claim is made from the current export.

= Why the mixed-anchor design is stronger

The core robustness improvement is inferential rather than numerical. The article no longer asks the between-subject and within-subject questions in the same frame.

#figure(
  kind: table,
  clean-table(
    columns: (1.75fr, 1.0fr, 2.75fr),
    align: left,
    inset: 4pt,
    table.header([*Question*], [*Primary contract*], [*Why this improves defensibility*]),
    [`PD walk vs HC walk`], [`cohort_anchored`], [Shared-reference geometry is appropriate for the between-subject disease-state question.],
    [`PD walk vs rest`], [`subject_anchored`], [The paired task-reconfiguration question remains within-subject rather than being diluted by cohort re-referencing.],
    [`HC walk vs rest`], [`subject_anchored`], [The same paired logic is preserved for controls, but only as secondary context.],
  ),
  caption: [Mixed-anchor selection rule used to build the article-facing inventories.]
) <tab-s3-contract-rationale>

This is the main reason the manuscript is more review-stable than a one-anchor summary would be. It aligns the geometry question with the correct comparison frame before any focal-row selection is made.

= Evidence ranking used in the manuscript

The article deliberately ranks its evidence layers instead of presenting all corrected rows as equal. That ranking is shown in @tab-s3-ranking.

#figure(
  kind: table,
  clean-table(
    columns: (1.5fr, 1.0fr, 0.95fr, 2.3fr),
    align: left,
    inset: 4pt,
    table.header([*Branch*], [*Status*], [*`q < 0.05` rows*], [*Why this is the article-facing status*]),
    [`Cohort walk standard`], [`primary`], [`4`], [The walk disease-state question is the cleanest between-group result and all retained rows lie in one coherent family.],
    [`PD paired standard`], [`primary`], [`3`], [The paired Parkinson branch is the correct within-subject task comparison and retains three corrected rows.],
    [`HC paired context`], [`secondary`], [`1`], [Healthy-control walk-vs-rest change is real but not the paper's main question.],
    [`Cohort walk regional`], [`supportive`], [`2`], [Regional rows replicate the global walk signal but remain sensor-group support rather than independent anatomical claims.],
    [`Cohort rest reachability`], [`supportive`], [`9`], [Reachability is corrected and informative, but it is strongest in rest rather than in the main walk disease-state branch.],
    [`Cohort rest trajectory`], [`exploratory`], [`4`], [The compact-summary trajectory layer remains rest-dominant and does not outrun the standard walk headline.],
  ),
  caption: [Evidence ranking used to decide what belongs in the main article versus the supplements.]
) <tab-s3-ranking>

The key review-facing point is that more retained rows do not automatically imply higher headline value. The rest reachability and rest clinical layers are information-rich, but they answer a different part of the physiology question than the walk disease-state headline.

= Why regional rows are supportive, not independent headlines

The strongest regional walk replications are frontal `d_n_mean` (`d = 1.062`, `q = 0.0049`) and frontal `d_n_median` (`d = 1.051`, `q = 0.0049`). These are stronger than the global walk rows in raw effect size, but they are still sensor-group summaries. The article therefore treats them as support for topographic concentration of the walk disease-state effect rather than as separate anatomical discoveries.

This ranking is intentionally conservative. It avoids turning a four-row global walk story into a larger but less defensible localization story.

= Why reachability remains supplement-level support

The reachability wrapper is one of the stronger supportive layers in the current bundle. The problem is not weakness. The problem is placement. The corrected reachability branch is concentrated in `HC vs PD rest`, not in the primary `PD walk vs HC walk` headline. The leading rows are `pred_err_h2` (`d = -0.634`, `q = 0.023`) and `tube_log_det_mean` (`d = -0.557`, `q = 0.023`).

That makes reachability valuable for the broader manuscript interpretation, especially the claim that baseline geometry carries substantial disease-burden structure. It does *not* make reachability the correct lead figure for a paper whose main between-group question is framed during walking.

= Why trajectory geometry remains exploratory

The compact-summary trajectory layer does retain four rest `HC vs PD` rows at `q < 0.05`, led by `noetic_action_kinetic` (`d = -0.687`, `q = 0.012`) and `path_length` (`d = -0.671`, `q = 0.012`). That is enough to keep the layer visible in `S2`. It is not enough to promote it above the standard walk headline, because:

1. the retained trajectory rows are rest-dominant rather than walk-dominant,
2. the layer is article-local and explicitly exploratory,
3. and the main standard rows already provide a simpler and more review-resistant walk disease-state story.

The new time-reshuffle null reinforces that ranking rather than overturning it. The reshuffle test permutes exported window order within run and then recomputes the leading trajectory metrics. Under that null, the strongest row `noetic_action_kinetic` remains meaningfully above the reshuffled effect distribution (`empirical p = 0.0149`), but `path_length` is only borderline (`empirical p = 0.0896`) and `curvature_median` / `noetic_action_jerk` are not clearly separated from the reshuffled null. So the trajectory layer now has one stronger temporal-order check, but still not the kind of broad null-resistance that would justify headline promotion.

#figure(
  kind: table,
  clean-table(
    columns: (2.45fr, 0.9fr, 1.15fr, 1.15fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Trajectory row*], [*Observed `d`*], [*Null mean `|d|`*], [*Null p95 `|d|`*], [*Empirical `p`*]),
    [`noetic_action_kinetic (3D)`], [`-0.687`], [`0.431`], [`0.626`], [`0.0149`],
    [`curvature_median (3D)`], [`0.596`], [`0.540`], [`0.709`], [`0.338`],
    [`path_length (3D)`], [`-0.671`], [`0.606`], [`0.681`], [`0.0896`],
    [`noetic_action_jerk (3D)`], [`-0.530`], [`0.398`], [`0.557`], [`0.110`],
  ),
  caption: [Within-run time-reshuffle null for the four leading rest `HC vs PD` trajectory rows. Only `noetic_action_kinetic` clearly exceeds the reshuffled null distribution, while the other rows remain modest or borderline. This supports visibility of the exploratory trajectory layer, but not headline promotion.]
) <tab-s3-time-reshuffle>

= Classical comparator boundary

The repository contains article-local wrappers for classical EEG comparators, but the current `ds007526` export does not expose the `conventional_eeg` extension. The classical wrapper therefore reports the panel as unavailable rather than returning a valid sidecar table. The new QC rerun does not change that conclusion: the explicit availability pass again finds `0 / 277` H5 files with the required classical sidecar path.

#figure(
  kind: table,
  clean-table(
    columns: (1.65fr, 1.1fr, 2.45fr),
    align: left,
    inset: 4pt,
    table.header([*Layer*], [*Status*], [*Review-facing implication*]),
    [`Classical EEG sidecars`], [`unavailable in this bundle`], [No direct benchmark claim against relative power, Hjorth, or related classical summaries is justified from the current export.],
    [`Reachability wrappers`], [`available`], [Supportive interpretation is justified, but strongest rows are rest-facing rather than walk-facing.],
    [`Trajectory layer`], [`available`], [Exploratory interpretation is justified; headline promotion is not.],
  ),
  caption: [Availability boundary for the main non-standard layers in the present export.]
) <tab-s3-availability>

= Leave-one-subject-out stability of focal rows

The new omission pass materially strengthens the revised manuscript framing. Across all eight main-text focal rows and the single healthy-control context row, effect direction is preserved under every single-subject omission (`sign consistency = 1.00` throughout). That means the revised article is not being driven by one extreme participant in either the cohort-walk or paired Parkinson branch.

The cohort-walk branch remains especially stable under omission. For example, the primary `d_n_mean` row stays within `d = 0.710` to `0.832` under leave-one-out, and the companion `d_n_median`, `d_mean`, and `d_median` rows remain similarly bounded. The paired Parkinson rows are also tight: `d_n_mean` stays within `d_z = 0.396` to `0.450`, `m_a_iqr` within `0.460` to `0.508`, `d_iqr` within `0.390` to `0.445`, and `d_mad` within `0.400` to `0.454`.

#figure(
  kind: table,
  clean-table(
    columns: (2.1fr, 0.8fr, 1.35fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Row*], [*Full effect*], [*Leave-one-out range*], [*Sign consistency*]),
    [`Global walk d_n_mean`], [`0.766`], [`0.710 to 0.832`], [`1.00`],
    [`Global walk d_n_median`], [`0.746`], [`0.691 to 0.812`], [`1.00`],
    [`Global walk d_mean`], [`0.711`], [`0.640 to 0.805`], [`1.00`],
    [`Global walk d_median`], [`0.718`], [`0.650 to 0.807`], [`1.00`],
    [`PD paired d_n_mean`], [`0.409`#super[z]], [`0.396 to 0.450`], [`1.00`],
    [`PD paired m_a_iqr`], [`0.472`#super[z]], [`0.460 to 0.508`], [`1.00`],
    [`PD paired d_iqr`], [`0.403`#super[z]], [`0.390 to 0.445`], [`1.00`],
    [`PD paired d_mad`], [`0.412`#super[z]], [`0.400 to 0.454`], [`1.00`],
    [`HC context m_a_mean`], [`0.888`#super[z]], [`0.844 to 1.156`], [`1.00`],
  ),
  caption: [Leave-one-subject-out stability for the revised focal row set. Unpaired cohort-walk rows report Cohen's `d`; paired rows report Cohen's `d_z` (marked `z`). All rows preserve effect direction under every single-subject omission.]
) <tab-s3-loo>

= Review-facing caution points

1. The paper remains exploratory even though the main text is restricted to `BH-FDR q < 0.05`.
2. The focal rows are article-facing representatives, not preregistered endpoints.
3. Regional support rows are sensor-group summaries, not source-localized anatomical estimates.
4. The strongest reachability and clinical association surfaces are rest-weighted and should not be over-read as direct confirmations of the walk headline.
5. The compact-summary trajectory layer remains exploratory and rest-dominant in this dataset; the new time-reshuffle null supports only its strongest row clearly.
6. The classical comparator branch is unavailable in the current export because `conventional_eeg` is missing.
7. The leave-one-subject-out pass strengthens internal stability claims, but it does not substitute for external replication.
8. The results are bounded to one processed bundle and do not yet constitute external replication.

= Files

The review-facing claims in this supplement are backed mainly by:

- `results/parkinson_walking_20260610/article_exports_121725/retained_counts.csv`
- `results/parkinson_walking_20260610/article_exports_121725/supportive_rows.csv`
- `results/parkinson_walking_20260610/article_exports_121725/exploratory_rows.csv`
- `results/parkinson_walking_20260610/article_exports_121725/evidence_ledger.csv`
- `results/parkinson_walking_20260610/reachability_cohort_121725/reachability_group_contrasts.csv`
- `results/parkinson_walking_20260610/trajectory_cohort_121725/trajectory_group_contrasts.csv`
- `results/parkinson_walking_20260610/classical_cohort_121725/`
- `results/parkinson_walking_20260610/additional_qc_20260612_leaveoneout_shuffle/qc_classical_comparator_summary.csv`
- `results/parkinson_walking_20260610/additional_qc_20260612_leaveoneout_shuffle/qc_leave_one_subject_out_metrics.csv`
- `results/parkinson_walking_20260610/additional_qc_20260612_leaveoneout_shuffle/qc_time_reshuffle_summary.csv`
- `results/parkinson_walking_20260610/additional_qc_20260612_leaveoneout_shuffle/additional_qc_summary.md`

#bibliography("parkinson_walking_geometry.bib")
