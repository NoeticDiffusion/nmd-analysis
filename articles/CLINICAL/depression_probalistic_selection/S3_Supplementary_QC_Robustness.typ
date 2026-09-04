#import "network_neuroscience_template.typ": *
  
#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness - Depressive Symptom Geometry Across Rest and Probabilistic Selection",
  short-title: "Depression Probabilistic Selection QC",
  subtitle: "Denominators, event coverage, and leave-one-subject-out checks for the paired article surface",
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

This supplement records the most practical review-facing QC and robustness checks for the paired depression PST article:

1. selected block denominators,
2. event-family coverage across subjects,
3. leave-one-subject-out omission for the selected task and paired rows,
4. and the main interpretive boundaries that remain even after those checks.

The aim is not to overstate robustness. The aim is to show where the article is well supported and where it is still bounded by denominator and design limits.

= Denominator visibility

The main manuscript compresses a heterogeneous export surface into a small number of selected block rows. Those rows do not all sit on the same denominator.

#figure(
  kind: table,
  table(
    columns: (1.35fr, 1.35fr, 0.9fr, 0.8fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Scope*], [*Block*], [*Total*], [*Low*], [*Mid*], [*High*]),
    [`task_only`], [`Task 3D MNPS`], [`122`], [`76`], [`15`], [`30`],
    [`task_only`], [`Task 9D MNPS`], [`122`], [`76`], [`15`], [`30`],
    [`task_only`], [`Task 3D MNJ`], [`122`], [`76`], [`15`], [`30`],
    [`task_only`], [`Task 9D MNJ`], [`70`], [`38`], [`12`], [`20`],
    [`task_only`], [`Task 9x9 block MNJ`], [`70`], [`38`], [`12`], [`20`],
    [`task_only`], [`Task reachability`], [`69`], [`37`], [`12`], [`20`],
    [`task_only`], [`Task tier-2 EMMI`], [`122`], [`76`], [`15`], [`30`],
    [`task_only`], [`Task distribution summary`], [`122`], [`76`], [`15`], [`30`],
    [`paired_delta`], [`Reachability`], [`69`], [`37`], [`12`], [`20`],
    [`paired_delta`], [`Block MNJ m->m`], [`70`], [`38`], [`12`], [`20`],
  ),
  caption: [Selected block coverage from `results/additional_qc_20260609/qc_selected_block_coverage.csv`.]
) <tab-s3-coverage>

Two points matter most:

1. the coarse `3D` layers, `tier2_emmi`, and distribution rows retain near-complete cohort support;
2. the selected task `9D` Jacobian, block-MNJ, and reachability rows operate on smaller valid subsets, so their corrected significance should always be read with those denominators visible.

At the raw analysis-family level, the task-root parquets still contain `122` subjects for most families, but the specific selected `9D` Jacobian and reachability metrics become effectively narrower once missing values and selected metric filters are applied.

= Event coverage

The event-window layer is exploratory, but it is at least well populated across the cohort. Every article-facing family is represented in all `122` subjects.

#figure(
  kind: table,
  table(
    columns: (1.45fr, 0.8fr, 0.9fr, 1.0fr, 1.0fr),
    align: left,
    inset: 4pt,
    table.header([*Event family*], [*Bin*], [*Subjects*], [*Median events*], [*Median rows*]),
    [`feedback_correct`], [`event`], [`122`], [`94.5`], [`94.5`],
    [`feedback_incorrect`], [`event`], [`122`], [`78.5`], [`78.5`],
    [`train_stim_any`], [`event`], [`122`], [`177`], [`177`],
    [`test_stim_any`], [`event`], [`122`], [`90`], [`90`],
    [`left_response`], [`event`], [`122`], [`144`], [`144`],
    [`right_response`], [`event`], [`122`], [`143.5`], [`143.5`],
  ),
  caption: [Event-bin coverage from `results/additional_qc_20260609/qc_event_coverage_summary.csv`.]
) <tab-s3-event-coverage>

The broader peri-event bins are even denser. For example:

1. `train_stim_any / post_far` has median `240` events and median `1200` contributing rows per subject,
2. `left_response / post_far` has median `190` events and median `936.5` rows,
3. `feedback_correct / post_far` has median `126` events and median `630` rows.

This means the weakness of the event-window results is unlikely to be explained simply by gross coverage failure. The more plausible interpretation is that the symptom effect on these coarse event summaries is genuinely modest.

= Leave-one-subject-out omission

The main selected task rows were directionally stable under leave-one-subject-out omission.

#figure(
  kind: table,
  table(
    columns: (1.6fr, 1.55fr, 0.85fr, 1.25fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Scope*], [*Row*], [*Full `d`*], [*Leave-one-out `d` range*], [*Sign consistency*]),
    [`task_only`], [`Task 9x9 block MNJ / block_frobenius_mean`], [`-0.778`], [`-0.866` to `-0.741`], [`1.00`],
    [`task_only`], [`Task reachability / tube_log_eig_var_mean`], [`-0.719`], [`-0.756` to `-0.683`], [`1.00`],
    [`task_only`], [`Task distribution / e_m_mad_sigma`], [`0.506`], [`0.442` to `0.699`], [`1.00`],
    [`paired_delta`], [`Tier-2 EMMI / mv_median`], [`0.337`], [`0.233` to `0.405`], [`1.00`],
    [`paired_delta`], [`Reachability / tube_log_eig_var_mean`], [`-0.130`], [`-0.262` to `0.016`], [`0.986`],
    [`paired_delta`], [`3D MNJ / spectral_radius_median`], [`0.036`], [`-0.029` to `0.126`], [`0.967`],
  ),
  caption: [Representative leave-one-subject-out rows from `results/additional_qc_20260609/qc_leave_one_subject_out.csv`.]
) <tab-s3-loo>

The review-facing lesson is uneven.

- The strongest task-only rows are stable in sign under every omission.
- The paired null rows remain weak not because one subject dominates them, but because the effect itself stays small.
- The paired reachability and `3D` MNJ rows are especially useful caution examples: they already look weak in the full sample and remain weak under omission.

= What the QC pass does and does not show

The additional QC pass strengthens the article in three specific ways:

1. it makes the smaller `9D` / reachability denominators explicit,
2. it confirms that the exploratory event families are densely represented across subjects,
3. it shows that the strongest task-only block effects are not one-subject artifacts.

It does *not* do the following:

1. it does not create new corrected findings for the event-window layer,
2. it does not rescue the paired `task - rest` surface from being broadly null,
3. it does not substitute for independent replication.

= Practical interpretation boundary

The main paper is strongest when read as follows:

1. depressive symptom burden is visible in the task-state export,
2. the clearest task-state signal sits in reachability and block-resolved `9D` dynamics,
3. broad event summaries remain exploratory,
4. and the paired rest-task delta story remains weaker than the separate rest-only and task-only stories.

The QC pass is consistent with that reading. It supports the article's defended hierarchy of claims rather than overturning it.

= Files

The robustness material in this supplement is backed mainly by:

- `results/additional_qc_20260609/qc_selected_block_coverage.csv`
- `results/additional_qc_20260609/qc_event_coverage_summary.csv`
- `results/additional_qc_20260609/qc_leave_one_subject_out.csv`
- `results/additional_qc_20260609/additional_qc_summary.md`
