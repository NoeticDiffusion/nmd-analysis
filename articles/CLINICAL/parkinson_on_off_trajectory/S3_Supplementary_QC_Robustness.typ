#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness - Disease-State and Paired Pharmacology Geometry in Parkinson ON/OFF Auditory Oddball EEG",
  short-title: "Parkinson Supplementary QC",
  subtitle: "Mixed-contract defensibility, event-window consequences, and negative-result boundaries",
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

This supplement collects the robustness and cautionary material that is important for review but intentionally compressed in the main paper:

- why the mixed-contract design is more defensible,
- why the geometry rows remain stronger than the conventional EEG sidecars,
- what changed after switching to `event_windows/*`,
- how stable the focal rows remain under leave-one-subject-out omission,
- what happens under a circular time-shift null for the event-/stage-locked rows,
- how weak the paired pharmacology layer remains,
- why trajectory ESB is still negative,
- and what unresolved limitations remain in the bundle.

= Why the mixed-contract design is stronger

The most important robustness improvement in this project is inferential rather than numerical. The main paper no longer uses one coordinate contract for all questions.

#figure(
  kind: table,
  table(
    columns: (1.9fr, 1.0fr, 2.8fr),
    align: left,
    inset: 5pt,
    table.header([*Question*], [*Primary contract*], [*Why this improves defensibility*]),
    [`Control vs Parkinson OFF`], [`cohort_anchored`], [Shared-reference geometry is appropriate for between-subject disease-state inference.],
    [`Control vs Parkinson ON`], [`cohort_anchored`], [Still a disease-facing between-subject question, even though the Parkinson subjects are medicated.],
    [`Parkinson OFF vs ON`], [`subject_anchored`], [Paired medication inference remains in a within-subject frame rather than being diluted by cohort re-referencing.],
  ),
  caption: [Mixed-contract selection rule used to build the primary article-facing inventories.]
) <tab-s3-contract-rationale>

This change is the main reason the new manuscript is more review-stable than the old one-contract version. It aligns the geometry question with the correct comparison frame instead of relying on a post hoc appendix repair.

= Conventional EEG comparators do not replace the geometry layer

The article now includes classical EEG sidecars so that the NDT/NMD rows are not presented without clinically familiar reference surfaces. That comparison was useful, but it did not overturn the geometric story.

#figure(
  kind: table,
  table(
    columns: (1.45fr, 1.85fr, 0.8fr, 1.75fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Best geometry row*], [*`q`*], [*Best classical row*], [*`q`*], [*`|d|` gap*]),
    [`Control vs Parkinson OFF`], [`eyes_closed speed_median (3D)`], [`0.0025`], [`theta/alpha ratio median`], [`0.4937`], [`0.7399`],
    [`Control vs Parkinson ON`], [`global 9D mdr_median`], [`0.0095`], [`theta/alpha ratio median`], [`0.2985`], [`0.5390`],
    [`Parkinson OFF vs ON`], [`temporal anisotropy_abs_eig_mean`], [`0.038`], [`relative theta median`], [`0.9870`], [`0.1980`],
  ),
  caption: [Best article-facing geometry row versus best article-facing conventional EEG comparator row for each primary contrast. The absolute-effect gap remained in favor of the geometry layer for all three contrasts.]
) <tab-s3-classical-vs-geometry>

No conventional EEG comparator row survived `BH-FDR q < 0.1` in the article-facing median-valued comparator inventory. The sidecars therefore improve interpretability, but not headline inferential strength.

The next reviewer-facing question is whether the focal NDT/NMD rows are merely restatements of the classical panel. To test that directly, we matched each focal row against the strongest subject-level classical median correlate within the same contrast inventory. For the between-subject contrasts, we report both pooled subject-level `rho` and a simple group-adjusted `rho` after median-centering within the two contrast strata. For the paired `OFF vs ON` branch, we instead correlate subject-level `ON - OFF` deltas.

#figure(
  kind: table,
  table(
    columns: (2.3fr, 1.75fr, 0.85fr, 0.95fr, 1.45fr),
    align: left,
    inset: 4pt,
    table.header([*Focal NMD row*], [*Strongest classical correlate*], [*`rho`*], [*Adjusted `rho`*], [*Interpretation*]),
    [`frontal 9D d_n_std (Control vs OFF)`], [`permutation entropy median`], [`-0.047`], [`0.198`], [`contrast-aligned but not reducible in this check`],
    [`eyes_closed speed_median 3D (Control vs OFF)`], [`Hjorth complexity median`], [`0.364`], [`0.408`], [`partial alignment, but not reducible in this check`],
    [`eyes_closed noetic_action_kinetic 9D (Control vs OFF)`], [`slowing-index ratio median`], [`0.172`], [`0.220`], [`contrast-aligned but not reducible in this check`],
    [`global 9D mdr_median (Control vs ON)`], [`theta/alpha ratio median`], [`-0.344`], [`-0.334`], [`partial alignment, but not reducible in this check`],
    [`novel_tone hysteresis_area_me (Control vs ON)`], [`peak median frequency median`], [`-0.507`], [`-0.464`], [`partial alignment, but not reducible in this check`],
    [`standard_tone hysteresis_area_me (Control vs ON)`], [`peak median frequency median`], [`-0.496`], [`-0.461`], [`partial alignment, but not reducible in this check`],
    [`signed_divergence_balance_mean_neg (OFF vs ON)`], [`Hjorth mobility median`], [`0.295`], [--], [`limited paired alignment`],
  ),
  caption: [Direct focal-row sensitivity against classical EEG sidecars. None of the focal geometry rows show a near-one-to-one correspondence with the classical panel, and the paired branch remains weak even under delta-based comparison.]
) <tab-s3-focal-vs-classical>

This does not prove that the focal NDT/NMD rows are independent of all classical EEG structure. It does show, however, that the strongest retained geometry rows are not well described as simple one-to-one restatements of the most familiar sidecars.

= Event-window consequence

The rerun moved from nearest-time onset mapping to exact processed-window event spans when `event_windows/*` was present. That makes the event contract cleaner, but it did not increase the number of retained tone-centered rows.

#figure(
  kind: table,
  table(
    columns: (2.55fr, 1.2fr, 2.0fr),
    align: left,
    inset: 5pt,
    table.header([*Run*], [*Retained tone rows*], [*Where the retained rows appeared*]),
    [Previous one-contract run with nearest-time event mapping], [`13`], [`Control vs Parkinson OFF` only: `6 novel`, `4 standard`, `3 target`],
    [Current mixed-contract run with `event_windows/*`], [`3`], [`Control vs Parkinson ON` only: `1 novel`, `1 standard`, `1 target`],
  ),
  caption: [Retained tone-row inventory before and after the event-window update.]
) <tab-s3-tone-shift>

The important point is that the event contract is now better specified, not that it magically rescued the oddball pharmacology question. Tone-row identity changed, but the total retained tone inventory became smaller.

One observation worth flagging for future work: the directional shift was not merely a reduction in count but a complete inversion of which contrast carried the retained tone rows. The previous run concentrated tone retention in `Control vs Parkinson OFF`; the current run concentrates it in `Control vs Parkinson ON`. Whether this reflects a genuine analytical interaction between event-window precision and the coordinate contract, or whether it reflects the instability of a small corrected tone inventory, cannot be resolved from the present bundle. Raw single-trial ERP reconstruction would be needed to settle the question.

= Leave-one-subject-out stability

The focal geometry rows remained directionally stable when one subject was omitted at a time. This does not prove transportability, but it does argue against the main rows being driven by one idiosyncratic subject.

#figure(
  kind: table,
  table(
    columns: (2.25fr, 0.8fr, 0.95fr, 1.35fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Focal geometry row*], [*Full `d`*], [*Full `p`*], [*Leave-one-out `d` range*], [*Sign consistency*]),
    [`frontal 9D d_n_std (Control vs OFF)`], [`-1.268`], [`6.4e-05`], [`-1.432` to `-1.225`], [`1.00`],
    [`eyes_closed speed_median 3D (Control vs OFF)`], [`-1.212`], [`4.7e-05`], [`-1.386` to `-1.167`], [`1.00`],
    [`eyes_closed noetic_action_kinetic 9D (Control vs OFF)`], [`-1.085`], [`7.2e-05`], [`-1.167` to `-1.034`], [`1.00`],
    [`global 9D mdr_median (Control vs ON)`], [`1.167`], [`5.0e-04`], [`1.117` to `1.380`], [`1.00`],
    [`novel_tone hysteresis_area_me (Control vs ON)`], [`-1.039`], [`3.8e-04`], [`-1.118` to `-0.990`], [`1.00`],
    [`standard_tone hysteresis_area_me (Control vs ON)`], [`-0.990`], [`0.0016`], [`-1.120` to `-0.939`], [`1.00`],
    [`temporal anisotropy_abs_eig_mean (OFF vs ON)`], [-0.483#super[z]], [`5.0e-04`], [-0.515#super[z] to `-0.433`#super[z]], [`1.00`],
  ),
  caption: [Leave-one-subject-out stability for the focal geometry rows. All retained rows preserved effect direction under every single-subject omission.]
) <tab-s3-geometry-loo>

The same omission analysis was also run on the strongest classical comparator row per contrast.

#figure(
  kind: table,
  table(
    columns: (2.2fr, 0.8fr, 0.95fr, 1.35fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Best classical row*], [*Full `d`*], [*Full `p`*], [*Leave-one-out `d` range*], [*Sign consistency*]),
    [`theta/alpha ratio median (Control vs OFF)`], [`-0.472`], [`0.187`], [`-0.591` to `-0.382`], [`1.00`],
    [`theta/alpha ratio median (Control vs ON)`], [`-0.628`], [`0.168`], [`-0.689` to `-0.555`], [`1.00`],
    [`relative theta median (OFF vs ON)`], [`0.285`], [`0.474`], [`0.205` to `0.361`], [`1.00`],
  ),
  caption: [Leave-one-subject-out stability for the strongest conventional EEG comparator row in each primary contrast. These rows were stable in sign, but remained materially smaller and non-corrected.]
) <tab-s3-classical-loo>

The relevant review-facing point is therefore not merely stability. Both the geometry and comparator layers are reasonably stable under omission, but only the geometry rows remain both large and correction-surviving.

= Circular time-shift null

Inspired by the coma article's temporal-null logic, we added a Parkinson-specific circular time-shift null for the retained event-/stage-locked trajectory rows. Within each run, the exported trajectory was circularly rolled relative to the original block labels, preserving within-run autocorrelation and block counts while destroying true label alignment.

#figure(
  kind: table,
  table(
    columns: (2.2fr, 0.8fr, 0.95fr, 0.95fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Row*], [*Observed `d`*], [*Null mean `|d|`*], [*Null p95 `|d|`*], [*Empirical `p`*]),
    [`eyes_closed speed_median 3D (Control vs OFF)`], [`-1.212`], [`0.359`], [`0.700`], [`0.08`],
    [`eyes_closed noetic_action_kinetic 9D (Control vs OFF)`], [`-1.085`], [`0.286`], [`0.718`], [`0.04`],
    [`novel_tone hysteresis_area_me (Control vs ON)`], [`-1.039`], [`0.557`], [`0.881`], [`0.08`],
    [`standard_tone hysteresis_area_me (Control vs ON)`], [`-0.990`], [`0.621`], [`0.906`], [`0.04`],
  ),
  caption: [Circular time-shift null summary over `24` permutations. The observed rows remained larger than the `95th` percentile of the null in all four cases, with empirical `p = 0.04` for two rows and `p = 0.08` for the other two.]
) <tab-s3-time-shift-null>

This is not a raw-ERP permutation analysis, so it should not be oversold. Still, it is a useful defensibility check: the retained trajectory rows do not look like generic consequences of arbitrary label placement on the exported state series.

The null was applied only to the event- and stage-locked trajectory wrapper rows. The primary standard rows (`d_n_std`, `mdr_median`, and related `MNPS` / Jacobian summaries) are computed as summaries across *all* valid windows in a run, without segment-level labeling. A circular label shift therefore has no well-defined application to them. Their robustness is instead supported by the leave-one-subject-out stability analysis above, which shows that all six focal standard rows preserve effect direction under every single-subject omission.

= Paired pharmacology remains the weak branch

The paired `Parkinson OFF vs ON` contrast is still the narrowest part of the paper. The retained and near-retained rows are summarized below.

#figure(
  kind: table,
  table(
    columns: (1.65fr, 1.05fr, 1.15fr, 1.75fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Family*], [*Segment*], [*Network*], [*Metric*], [*OFF med*], [*ON med*], [*`d`*], [*`q`*]),
    [`retained standard`], [--], [`temporal`], [`anisotropy_abs_eig_mean`], [`0.0311`], [`0.0232`], [`-0.483`], [`0.038`],
    [`near-miss standard`], [--], [`global`], [`signed_divergence_balance_mean_neg`], [`-0.0440`], [`-0.0503`], [`-0.711`], [`0.066`],
    [`near-miss standard`], [--], [`frontal`], [`trace_median`], [`-0.0374`], [`0.0337`], [`0.650`], [`0.133`],
    [`near-miss event`], [`eyes_open`], [`central`], [`noetic_action_jerk (9D)`], [`0.0442`], [`0.0248`], [`-0.641`], [`0.226`],
    [`near-miss event`], [`eyes_open`], [`central`], [`path_length (9D)`], [`40.329`], [`33.455`], [`-0.714`], [`0.390`],
    [`near-miss event`], [`novel_tone`], [`global`], [`noetic_action`], [`0.0653`], [`0.1457`], [`0.424`], [`0.839`],
  ),
  caption: [The paired pharmacology branch remains limited. `anisotropy_abs_eig_mean` is the new retained row following correction of persistence-based metrics; `signed_divergence_balance_mean_neg` is now a near-miss at `q = 0.066`.]
) <tab-s3-paired-weakness>

This is why the rewritten article no longer overpromises a broad medication-response story. The pharmacology effect is present, but narrow.

= Trajectory ESB remains negative

Trajectory ESB remains a bounded exploratory layer. It produced `0` retained rows at `BH-FDR q < 0.1`. The best rows are shown below so that the negative result is explicit rather than hidden.

#figure(
  kind: table,
  table(
    columns: (1.65fr, 1.05fr, 1.2fr, 1.6fr, 0.95fr, 0.95fr, 0.8fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header([*Contrast*], [*Segment*], [*Network*], [*Metric*], [*Left med*], [*Right med*], [*`d`*], [*`q`*]),
    [`OFF vs ON`], [`novel_tone`], [`frontal`], [`trajectory_esb2`], [`1.259`], [`0.782`], [`-0.498`], [`0.601`],
    [`OFF vs ON`], [`standard_tone`], [`temporal`], [`trajectory_esb2`], [`1.250`], [`0.931`], [`-0.384`], [`0.601`],
    [`Control vs OFF`], [`target_tone`], [`global`], [`z_recovery`], [`0.000`], [`0.000`], [`-0.523`], [`0.359`],
    [`Control vs ON`], [`standard_tone`], [`frontal`], [`z_tortuosity`], [`0.000`], [`0.000`], [`0.835`], [`0.294`],
  ),
  caption: [Representative non-retained ESB rows. The layer remains exploratory and negative in the current rerun.]
) <tab-s3-esb-negative>

The operational conclusion is therefore straightforward: the current dataset supports direct disease-state geometry more strongly than it supports a control-template ESB score.

= Review-facing caution points

The rerun improves the manuscript, but it does not remove every boundary.

1. The main text is now restricted to `BH-FDR q < 0.05`, while the broader `q < 0.1` inventory is retained only in `S2` for auditability.
2. `event_windows/*` improves event definition, but the wrapper still analyzes processed windows rather than raw single-trial ERP data.
3. The conventional EEG sidecars improve interpretability, but no article-facing classical comparator row survives `q < 0.1`.
4. The time-shift null is helpful but limited: it is a circular shift of exported trajectories, not a full upstream re-estimation from permuted raw EEG, and should be read as a low-resolution sanity null rather than as definitive permutation evidence.
5. Important disease-severity covariates remain absent or incomplete, including `LEDD`, `UPDRS`, and disease duration.
6. The bundle does not expose a reliable site / hospital variable for this article-facing cohort, so leave-one-site-out was not feasible here.
7. Direct focal-row sensitivity against the classical sidecars supports partial alignment at most, not simple reducibility, but it still does not replace the need for external replication.
8. The strongest paired medication branch still contains only one retained row, so the main disease-state story remains stronger than the medication story.
9. One retained event row runs counter to the dominant direction: `regional_event_locked_trajectory_3d / eyes_open / frontal / curvature_median` shows *elevated* curvature in `Parkinson OFF` relative to controls (`d = 1.012`, `q = 0.037`), whereas all other focal disease-state rows show reductions. This row is not discussed in the main text. Its interpretation — whether it reflects a genuine compensatory or attention-regulation mechanism in the frontal network during eyes-open transitions, or a regional artifact — remains unresolved.
10. The `e_m_mean`, `e_m_median`, and `e_m_std` subcoordinate metrics are global quantities replicated identically across all regional network rows by the NeuralManifoldDynamics export. The raw retained standard-row count of `35` at `q < 0.05` includes `12` such regional replications of `2` distinct global observations; the corresponding deduplicated distinct count is `23`. This does not affect any focal-row claim in the main text, because the main text does not cite `e_m`-family rows as focal effects, but it does affect the total retained inventory size reported in Table 1.

= Files

The robustness claims in this supplement are backed mainly by:

- `results/parkinson_on_off_dual_contract_20260602/primary_standard_contrasts.csv`
- `results/parkinson_on_off_dual_contract_20260602/primary_event_contrasts.csv`
- `results/parkinson_on_off_dual_contract_20260602/primary_trajectory_esb_contrasts.csv`
- `results/parkinson_on_off_dual_contract_20260602/eeg_classical_primary_contrasts.csv`
- `results/parkinson_on_off_dual_contract_20260602/additional_qc_20260603_classical_shuffle/qc_classical_comparator_summary.csv`
- `results/parkinson_on_off_dual_contract_20260602/additional_qc_20260603_classical_shuffle/qc_focal_nmd_vs_classical_summary.csv`
- `results/parkinson_on_off_dual_contract_20260602/additional_qc_20260603_classical_shuffle/qc_focal_nmd_vs_classical_all.csv`
- `results/parkinson_on_off_dual_contract_20260602/additional_qc_20260603_classical_shuffle/qc_leave_one_subject_out_metrics.csv`
- `results/parkinson_on_off_dual_contract_20260602/additional_qc_20260603_classical_shuffle/qc_time_shift_summary.csv`
- `results/parkinson_on_off_dual_contract_20260602/additional_qc_20260603_classical_shuffle/qc_time_shift_null_draws.csv`
- `results/parkinson_on_off_dual_contract_20260602/additional_qc_20260603_classical_shuffle/additional_qc_summary.md`
- `results/parkinson_on_off_dual_contract_20260602/exploratory_summary.md`
- `results/parkinson_on_off_exploratory_20260601/event_contrasts.csv`

#bibliography("parkinson_on_off_trajectory_geometry.bib")
