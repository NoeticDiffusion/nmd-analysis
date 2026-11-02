#import "template_eLife.typ": *

#set page(numbering: "1")

#show: netn-template.with(
  title: text(hyphenate: false)[Neural State Geometry and Dynamical Measurement Families Across Sleep],
  short-title: "Neural State Geometry Across Sleep",
  subtitle: "A support-audited descriptive development study",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("sleep", "neural state", "MNPS", "diffusion geometry", "EEG", "measurement"),
  article-type: "Research Article",
  abstract: [
    We describe local-Jacobian and diffusion measurement families in two ds005555 sleep recordings using fixed recording-parent representations and exact center/query label mapping. All preselected endpoints were retained: spectral and numerical abscissa and their gap in 3D and 9D, and D_total, d_diff and c_diff in canonical 3D diffusion. Relative to Wake, N2 had lower D_total, higher effective diffusion dimension and lower concentration in both recordings. Both 9D abscissae decreased, while the 3D abscissa contrasts reversed direction between recordings; reactivity-gap agreement also depended on representation. All 90 known-stage summary rows and 18 within-recording contrasts were independently reconstructed. These are label associations of existing global estimators, not stage-conditioned refits. Source nonequivalence, unknown full temporal support and the two-recording development design prevent population, biomarker or consciousness-theory validation. Independent drift remains unavailable in the current surfaces.
  ],
  author-summary: [The new metrics give a mixed but informative first result. Diffusion magnitude and anisotropy changed in the same direction between Wake and N2 in two recordings, while local growth and reactivity depended on representation and recording. We retain all outcomes and their support limitations instead of treating a shared direction as validation.],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be reported after source and grant records are verified.],
  data-availability: [The source dataset and analysis artifacts will be identified by their public source records, local manifests, and cryptographic hashes. Raw HDF5 files are not stored in this article directory.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

#set heading(numbering: "1.")

= Introduction <sec:intro>

Sleep recordings provide repeated observations of changing neural states, but temporal gaps, window support, and repeated-measure structure can make a computed endpoint unsuitable for a stage comparison. This pilot therefore treats support and measurement status as part of the result.

#netn-box(title: [Core question])[
  How do local fitted growth, Euclidean reactivity and chart-increment diffusion geometry associate with recorded sleep labels under fixed, explicitly supported measurement contracts?
]

= Theory and measurement contract <sec:theory>

MNPS coordinates describe a state representation used by the NeuralManifoldDynamics pipeline. Diffusion geometry is considered when its canonical family status, coordinate contract, and support are valid. A transition covariance proxy and its propagated W_Q summaries retain recording grain; they are not treated as stage-native or individual-level noise measurements.

The 9D volume statistic `v_norm` is currently method-limited: the pilot shows sensitivity, but does not isolate conditioning, projection, and eigenvalue-arithmetic contributions. It remains outside biological interpretation pending an independent numerical reference.

= Methods <sec:methods>

== Dataset and staged support

The reference support analyses use the verified ds005555 sub-99 recording; the separately specified extension uses sub-1. The read-only epoch export retains source, configuration, code, and output hashes. Recorded window labels are aligned to MNPS coordinates using exact source IDs and time bounds. These labels do not establish containment of the full filter support or diffusion neighborhood within one stage. Any future stage-conditioned endpoint requires a separate full-support assessment.

A bounded annotation audit compares the epoch table with the authoritative
human-scored `stage_hum` source. It verifies row-to-epoch mapping, onset and 30-second
duration, and the 256-Hz sample clock from the pinned EEG metadata. Code 8 is
retained as an unresolved PSG-disconnection status; `stage_ai` is not used as a
replacement. The raw recording lasts 32,064 seconds while the accepted epoch
bounds end at 32,040 seconds, leaving a 24-second tail outside the epoch
table. These checks establish annotation and table alignment only; full
filter support and diffusion-neighborhood purity remain unassessed.

== Descriptive development experiment

We summarize the recorded global coordinate representation by window label, without estimating separate stage-conditioned geometries. Eligibility is evaluated separately for 3D and 9D: a known stage, a finite complete vector, true coverage and retained-after-QC masks, and the corresponding producer geometry-valid or 9D-coordinate-valid mask. Missing masks cannot pass. Counts and coordinate medians with 25th and 75th percentiles are retained for every stage under both analysis policies.

The fixed label-boundary sensitivity subset additionally requires the preceding and following windows to share the same known label, with consecutive IDs and touching time bounds. Endpoints, gaps and unknown labels cannot pass this rule. It is a three-window label diagnostic, not proof of full temporal support or neighborhood purity. The policy was written after the source support audit, before inspecting the new descriptive outputs; it is not a preregistration.

The source uses a PPG-rate fallback for `e_m`, with `semantic_equivalence=false`, and the composite e-axis has mixed source provenance. This prevents interpreting the representation as an exclusively EEG-derived layer. Complete anchor identifiers and full filter-support metadata have not been verified.

== Primary endpoints

A separate candidate-neighborhood audit reuses the stored 3D coordinates,
timestamps, source-file segmentation and pinned diffusion settings (k = 20).
Candidate membership is exported only after exact agreement with stored tensor
values at their stored dtype, support counts and validity, followed by an exact
selected-increment covariance check. Source snapshots and before/after hashes
are retained. Diffusion is window-native with a recording parent; its global
neighbor pool is not restricted by stage. Matching tensors do not prove unique
historical neighbor identities, which were not persisted in the original HDF5.

The earlier MNPS coordinate summaries provide descriptive context. The current family analysis reports local-Jacobian spectral and numerical abscissa, their reactivity gap, and canonical 3D diffusion magnitude and anisotropy under the fixed versioned analysis plan. Q/W_Q, destination, resilience, and DF-DRIFT-C1 are recorded with their native status and grain; unavailable or method-limited outputs remain unavailable or descriptive.

== Statistical design

The initial two-recording pass is descriptive and within recording. The full local cohort extension uses the September 12 delivery contract, fixed before executing its cohort contrasts. Windows, transitions and repeated nights are never counted as independent participants; the extension calculates no p-values or confirmatory population inference.

== Full local cohort delivery and participant aggregation

The local raw inventory contains 128 PSG nights, named sub-1 through sub-128. The accompanying `participants.json` explicitly defines the BIDS `participant_id` as a recording identifier and `pid` as the identifier shared by all sessions of one person. The local participant table contains 100 unique pid values: 80 people with one night, 12 with two nights and eight with three nights. The dataset README states 108 people; the reproducible local mapping governs this analysis, and this metadata discrepancy remains documented. Simultaneously acquired headband files are excluded under the established PSG configuration.

The delivery uses fresh continuous 30-second epochs with a 30-second step and disabled stage sampling, retaining the existing canonical coordinate definitions, producer validity rules and recording-global reference fits. Historical stage-sampled H5 files do not enter this extension. The old two-recording artifacts remain development history; fresh recordings sub-1 and sub-99 are included in the 128-night inventory, and their respective people, pid 89 and 66, remain flagged as previously inspected development participants.

For each of the nine E1/E2 endpoints, the analysis first calculates a median within each recording and label. It then takes the median of available night-level medians within each pid and finally reports the median and quartiles across people, with the contributing-person count. The N2-minus-Wake contrast is calculated within each night with usable rows in both labels, reduced to one median contrast per pid, and then summarized across people. This avoids overweighting people with repeated nights and avoids pairing stages from different nights. Missing endpoints and unpaired nights retain explicit denominators and null results. Code 8 and other unknown labels remain separate categories. Recording-level FTR, Q/W_Q, destination, resilience and unqualified drift remain outside the stage-associated endpoint set.

== Independent-participant descriptive extension

Before inspecting the new participant's coordinates, the numerically selected
sub-1 recording (participant pid 89) was fixed against the sub-99 reference
(pid 66) by the external selection protocol. The existing epoch exporter was
generalized only to accept the configured subject leaf; coordinate contracts,
producer masks, source-quality handling, and recording-parent normalization
remain unchanged. For every canonical 3D and 9D coordinate, the extension
reports stage denominators and the signed N2-minus-Wake median under the same
eligibility rules. The comparison is descriptive, uses no p-values or pooled
estimate, and cannot establish participant or population generalization before
review.

== Local-Jacobian and diffusion family analyses

The versioned E1/E2 development plan specifies spectral abscissa, numerical abscissa and their difference separately in 3D and 9D, plus D_total, d_diff and c_diff from the existing canonical 3D diffusion tensor. Spectral abscissa is the largest real eigenvalue part of J; numerical abscissa is the largest eigenvalue of its symmetric part; the reactivity gap is their difference. The Euclidean numerical abscissa and gap depend on the coordinate metric. The diffusion scalars describe covariance magnitude, effective dimension and concentration; aliases are not additional endpoints.

Each Jacobian center is validated as an explicit epoch array position and mapped to the actual ID, timestamp and recorded stage. Different 3D/9D center grids remain separate. Diffusion query rows retain their exact epoch mapping, producer validity, support counts and PSD-floor indicators. Unknown labels are counted separately. Full temporal support and scientific qualification remain unknown; a valid row does not imply a stage-pure estimator.

All five known stages receive counts, medians and quartiles for every specified metric. The fixed descriptive contrast is N2 median minus Wake median within each recording and representation. Missing or unsupported groups produce null contrasts. No estimator is refitted by stage, no between-recording magnitudes are pooled, and no p-values or population inference are calculated. The two recordings were already development material when the E1/E2 plan was frozen; this is not preregistration.

== Robustness and missingness

The audit reports temporal gaps, irregular sampling, insufficient support, nonfinite values, coordinate contracts, computation status, measurement validity, and missingness by stage and endpoint. No refusal is converted to zero. All preselected diagnostic horizons remain visible.

= Results <sec:results>

== Verified export and coverage

The accepted epoch export contains 1,068 non-overlapping 30-second windows spanning 32,040 seconds. Nine labels are unknown. All coordinate vectors are finite and all four recorded producer masks are true, giving 1,059 eligible windows in each representation after excluding unknown labels. Re-running the integrated exporter produced a byte-identical Parquet table. Independent recomputation reproduced all 120 coordinate-by-stage summary rows across the two representations and two policies.

The run-support audit identifies 84 contiguous label/status bouts: 83
known-stage bouts and one unresolved code-8 disconnection bout. Known-stage
counts are Wake 17 bouts/275 windows, N1 16/20, N2 33/642, N3 15/15, and REM
2/107. All 15 N3 bouts are single 30-second windows, which accounts for the
loss of N3 under the fixed two-sided boundary diagnostic. This is a support
limitation in one recording, not evidence of annotation error or absent N3
physiology.

#figure(
  clean-table(
    columns: (1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    header: ([Stage], [Primary n], [Boundary n], [m median], [d median], [e median]),
    [Wake], [275], [249], [0.922], [1.769], [0.336],
    [N1], [20], [2], [0.679], [1.354], [0.132],
    [N2], [642], [581], [-0.344], [-0.255], [-0.121],
    [N3], [15], [0], [-1.392], [-1.007], [-0.255],
    [REM], [107], [103], [0.701], [0.190], [0.121],
  ),
  kind: table,
  caption: [Recorded-label counts and primary 3D medians. Counts are windows from one recording, not participants. The boundary rule requires both immediate labels to match. Unknown labels (n = 9) remain in the audit. Full quartiles and both-policy summaries for all 12 coordinates are retained in the accepted run.],
) <tab:coverage>

== Coordinate summaries and label-boundary sensitivity

Primary m and d medians differ descriptively among the recorded labels (@tab:coverage). The sensitivity subset retains 935 windows: 249 Wake, 2 N1, 581 N2, no N3, and 103 REM. N3 sensitivity statistics therefore remain unavailable, rather than zero. The two remaining N1 windows do not provide a stable basis for a stage summary.

For transparency, boundary-subset medians (m, d, e) are (1.019, 1.775, 0.333) for Wake, (-0.334, -0.253, -0.116) for N2, and (0.702, 0.189, 0.131) for REM. N1 values are retained in the complete tables with n = 2. These are window distributions in one global representation; no population test, classification performance, or separate stage-conditioned estimator is reported.

#figure(
  image("results/descriptive_epoch_sub99_20260907_r10/trajectory_3d_and_stage.png", width: 100%),
  caption: [Global MNPS coordinates over time and recorded sleep labels in sub-99. Unknown-label windows are omitted from coordinate traces and retained in the label panel. Trace colors distinguish contiguous plotted segments, not stages. The composite e-axis includes mixed provenance and the 9D e_m source is a non-equivalent PPG fallback. Aligned labels do not establish full filter support or stage purity.],
) <fig:trajectory>

== Dynamical-family availability

The earlier accepted import audit retained 1,068 computed diffusion tensor rows, with finite D_total, d_diff and c_diff. Drift-dependent A_bD and R_b_over_a remain unavailable because drift was not supplied. These are availability findings from the import audit; the present experiment does not add sleep-stage diffusion contrasts. Q/W_Q retains recording grain, and the method-limited 9D volume endpoint remains outside biological interpretation.

== Candidate diffusion support

The candidate reconstruction matched all 1,068 stored tensors and exported
21,360 selected-increment rows, with no exact-distance cutoff ties detected.
For 281 of 1,059 known-stage queries (26.5%), all 20 selected increments have
both endpoints in the query's stage. Across all queries, 88 selected-increment
rows touch a code-8 disconnection endpoint; 33 known-stage queries include at
least one such increment. These are repeated selections, not independent
events or participants. An independent direct calculation reproduced every
selection and tensor without importing the producer or reconstruction runner.
This establishes consistency of the candidate reconstruction with the stored
global estimator. It does not establish historical membership, complete
feature/filter support, or separately estimated stage-conditioned diffusion.

== Full-night rerun with executed support provenance

A fresh full-night sub-99 rerun retained all 1,068 windows, including nine source-code-8 windows. All 531 shared numeric datasets were exactly equal to the verified reference. The twelve normalization populations were independently reconstructed from the fresh feature table, with matching hashes and counts; referenced EDF and events-TSV hashes also matched. Recorded whole-stream PPG thresholding and recording-parent normalization remain distinct dependencies, and effective filter support remains unknown.

Using the unchanged descriptive eligibility rules, 1,059 known-stage windows were eligible for coordinate summaries in both 3D and 9D (Wake 275, N1 20, N2 642, N3 15, REM 107). Their medians and quartiles reproduced the accepted descriptive outputs within 4.4e-16. This rerun improves provenance and reproduces the single-recording description; it is not an independent participant replication. Producer masks do not establish stage purity, and no stage-conditioned Q/W_Q or diffusion qualification is introduced.

== Preselected second-participant description

The sub-1 full-night run retained 915 windows: Wake 200, N1 57, N2 398, N3 172, REM 87, and one source-code-8 window. All four producer masks were true and both coordinate vectors were finite, leaving 914 known-stage windows eligible under the unchanged primary rule. All twelve reference-population hashes and counts were reconstructed from the fresh feature table; recorded EDF and events-TSV hashes matched. No sampled feature cache or stage-specific fit was used.

For the predefined N2-minus-Wake median comparison, seven of twelve coordinate directions matched sub-99. Four changed sign (3D m and e; 9D m_e and m_o), and 9D e_m was exactly zero in sub-1. The remaining matching coordinates were 3D d and 9D m_a, d_n, d_l, d_s, e_e, and e_s. The twelve coordinates are dependent representations, not twelve independent replications. All twelve contrasts, denominators and source pins are retained in `results/independent_sub1_20260910/parent_direction_comparison.json`; no coordinate was removed or retuned after inspection.

#table(
  columns: 3,
  [3D coordinate], [Sub-99: N2 minus Wake], [Sub-1: N2 minus Wake],
  [m], [-1.2661], [0.5380],
  [d], [-2.0240], [-1.1562],
  [e], [-0.4569], [0.0937],
)

These are recording-relative coordinate differences, not calibrated between-person effect sizes. A subsequent, explicitly post-comparison source audit found that e_m used `ppg_rate_bpm` for sub-99 but `eog_blink_rate` for sub-1; both fallbacks carried `semantic_equivalence=false`. Thus e_m and composite e cannot be interpreted as source-equivalent measurements across these recordings. Sub-1 e_m was variable (21 distinct coordinate values), with equal Wake and N2 medians of -0.337245; the zero contrast is not an all-constant coordinate or missing-value replacement. The audit does not establish that the source difference caused any sign reversal.

== Executed local-Jacobian and diffusion family analysis

The frozen E1/E2 plan was executed on the same two development recordings. Sub-99 supplied 1066 finite Jacobian windows in each representation (1057 known labels) and 1068 valid diffusion queries (1059 known labels). Sub-1 supplied 913 3D Jacobian windows (912 known), 856 9D windows (855 known), and 915 diffusion queries (914 known). Nine and one source-code-8 rows respectively remain separate. Every diffusion query had producer valid=1, support count 20 and no PSD-floor application. Unknown scientific qualification remains null. The smaller sub-1 9D grid is mapped by its explicit centers, without padding or interpolation across gaps.

For the fixed N2-minus-Wake median contrast, all three diffusion scalars had the same direction in the two recordings: D_total decreased, d_diff increased and c_diff decreased. Both 9D abscissae decreased, whereas both 3D abscissae decreased in sub-99 and increased in sub-1. The 3D reactivity gap decreased in both; the 9D gap decreased in sub-99 and increased in sub-1. The complete contrast table is retained below, including the small sub-1 9D numerical-abscissa difference.

#table(
  columns: (1.7fr, 1fr, 1fr),
  [Representation / endpoint], [Sub-99: N2 minus Wake], [Sub-1: N2 minus Wake],
  [3D `spectral_abscissa`], [-0.00102044], [+0.00123961],
  [3D `numerical_abscissa`], [-0.0039051], [+0.00211499],
  [3D `reactivity_gap`], [-0.00180783], [-0.000115554],
  [9D `spectral_abscissa`], [-0.00341974], [-0.00144539],
  [9D `numerical_abscissa`], [-0.0108178], [-0.000357904],
  [9D `reactivity_gap`], [-0.00571622], [+0.00148238],
  [3D `D_total`], [-0.0263619], [-0.0406145],
  [3D `d_diff`], [+0.0937614], [+0.123157],
  [3D `c_diff`], [-0.0239958], [-0.0396286],
 )

Jacobian endpoints have inverse-second units: the producer trace records a measured 30-second step, passed to derivative and Jacobian estimation, with j_dot_dt=30 in the 3D diagnostics of both recordings. The 9D producer path uses the same measured dt, although a separate 9D diagnostics group is not stored. The generic configuration interval is not used to infer units. D_total is in recording-relative coordinate-squared per second; d_diff and c_diff are dimensionless. The gap contrast uses the median of individual gaps, not the difference between group abscissa medians. No between-recording magnitude calibration is implied.

The complete output contains 90 known-stage summary rows with counts, medians and quartiles, separate unknown categories and 18 contrasts. Independent direct-HDF5 reconstruction reproduced all known-stage statistics and contrasts after using float64 summary arithmetic. Source hashes remained unchanged. Figures preserve separate recordings and representations; actual-center timelines do not connect missing windows. Support and floor panels count each diffusion query once.

= Discussion <sec:discussion>

The subsequent fixed increment-support audit separates structural validity,
same-known-stage endpoint labels, and full signal support. All 1,067 adjacent
pairs satisfy the structural rule, including the stored 30-second nominal dt
and 0.05 relative-deviation limit. Of these, 976 have matching known-stage
endpoints: 258 Wake, 4 N1, 609 N2, 0 N3 and 105 REM. Ten adjacent pairs touch
a code-8 disconnection. These pool counts differ from repeated candidate
neighbor selections. Full-support-qualified counts remain unavailable, not zero;
no tensor was refitted from the restricted pool.

Feature-support inspection identifies a recording-global robust-z reference
fit over 1,068 rows. The 30-second feature input intervals do not establish
the effective support of preceding filters or resampling. Effective filter lengths, padding dependencies and a complete per-feature
dependency graph remain unqualified despite the new execution records.
The embedded time-grid audit resolves the generic 8/4 settings to the actual
30/30-second epoch profile; this distinction is not a detected time-axis error.
Reference-fit dependence and raw temporal support must remain separate.

The original support analyses describe one global representation and dependent
windows within sub-99; the second-participant extension gives mixed descriptive
direction agreement under the same primary analysis. They cannot isolate sleep-stage effects from time of night,
preprocessing or mixed feature provenance. The absence of supported N3
increments is not evidence of absent N3 physiology or incorrect annotations.

The E1/E2 result supports a narrow descriptive observation: reduced total increment covariance with less concentrated diffusion at N2-labeled queries in both recordings. It does not establish a stage-intrinsic diffusion process or a common biological mechanism. Abscissa and reactivity contrasts are representation-dependent; positive group abscissa medians and mixed contrast directions do not establish stable N2 dynamics. Overlapping distributions, time-of-night dependencies, unequal stage support and recording-relative charts remain relevant. The results should be retained without tuning measurement definitions toward agreement.

The separate E3 candidate experiment reuses the existing cross-fitting estimator and M3 benchmark evidence. Its original reference contract computes candidate chart velocities for sub-99 and records an explicit source-contract refusal for sub-1. A subsequent, separately specified coordinate-support policy permits candidate computations for both recordings while retaining that original refusal. These are bounded engineering results; they do not supply independent drift to the canonical diffusion surfaces. The PPG/EOG mismatch remains a scoped interpretation limitation for the representations. It does not invalidate the numeric extraction, but neither is it resolved by shared diffusion directions.
The local participant table has 128 rows and 100 distinct pid values, whereas
the README reports 108 people; this discrepancy remains unresolved. Q/W_Q
and method-limited 9D volume remain outside biological conclusions. No
consciousness-theory or clinical-biomarker validation is established.

== E3: bounded drift-candidate support

E1/E2 are executed descriptive analyses; the original versioned plan remains a historical development specification. E3 applies the existing local-mean and local-linear candidate estimators separately to the explicit 3D and 9D coordinate paths. The frozen split uses training increment indices 0--599 and evaluation indices 700--799, with 32 neighbors, minimum support 12, nominal dt 30 seconds and a 60-second embargo. The closest recorded epoch-support boundaries are 2,970 seconds apart, with no shared train/evaluation endpoints.

For sub-99, all four estimator/representation combinations produced 100 finite candidate vectors each. The coordinator independently reconstructed all 400 vectors and their held-out increments directly from HDF5 without importing the runner or estimator; the vectors matched exactly in the verification runtime. For sub-1, all four planned combinations are explicitly refused with null predictions because the existing M3 reference requires geometry-contract status `ok`, whereas this source records `adjusted` and 57 condition-number-invalid 9D Jacobian windows. This is a source-contract refusal, not evidence that the selected coordinate arrays are nonfinite or that drift is absent.

The explicit candidate coordinate paths equal the subject-anchored arrays in these two files. However, robust-z reference fits use all 1,068 or 915 recording rows, including evaluation rows, and effective upstream filter support remains unknown. Thus only the supplied velocity-fit increments and recorded epoch supports are separated; coordinate construction and the full processing chain are not independently held out. The outcome is partial input support with `candidate_not_qualified` and no biological claim. No sleep-stage contrast, empirical drift identification or new drift--diffusion coupling was performed. Current A_bD and R_b_over_a surfaces remain untestable because independent drift was not supplied. Recording-horizon finite-time response and recording-level Q/W_Q remain outside this family-label report.

=== Coordinate-support continuation

The 2026-09-12 follow-up separates candidate coordinate support from the overall geometry status. The policy was fixed before this follow-up's primary execution, after the development sources and an exploratory sub-1 candidate had already been inspected; it is not a preregistration or an unseen-data validation. An `adjusted` source is admitted only when the 3D Jacobian is clean, the 9D Jacobian's positive invalid-window count is fully accounted for by condition-number filtering, and all coordinate, time-grid and shared-row checks pass. Unknown reasons, missing or inconsistent evidence, nonfinite coordinates, degenerate axes and dropped epochs are refused. The observed count of 57 is provenance, not an acceptance threshold.

Both pinned recordings satisfy this scoped policy. Local-mean and local-linear candidates each produce 100 finite vectors in both 3D and 9D, giving 800 vectors across the two recordings. Direct HDF5 reconstruction reproduces all 800 exactly; the 400 sub-99 vectors are unchanged from the original E3 run. These are four candidate calculations at the same 100 evaluation increments per recording, not 800 independent observations. Sub-1 retains its original strict-reference refusal and file-level `adjusted` status alongside the new coordinate-support acceptance. Neither the original gate nor the stored source status is rewritten.

This closes the bounded coordinate-support question for these two development artifacts. It does not qualify the drift estimator or establish upstream independence: whole-record reference fitting and unknown effective filter support remain. Stronger drift or drift--diffusion claims would require a separately specified treatment of these dependencies. The current delivery priority is the complete continuous local PSG cohort and its descriptive analysis; independent-drift qualification is not a prerequisite for that descriptive report.

= Data and code availability

Accepted article artifacts are descriptive r10, stage audit r7, diffusion
candidate r9, and increment-support audit `increment_support_sub99_20260908_r2`.
The full-night rerun adds `results/fullnight_support_sub99_20260910`, with its
entry point `src/fullnight_stage_description.py` and exact commands in
`handover/20260910_fullnight_commands.md`. Their results directories retain
source, code, configuration and output hashes,
complete tables, independent reviews and coordinator recomputation evidence.
The second-participant extension is stored in `results/independent_sub1_20260910`,
with its frozen selection protocol, exact commands, and source-comparability
diagnostic. Independent review is recorded in `peer_review/13_independent_sleep_review.md`.
The new-family run is retained in `results/new_family_sleep_20260910`, including complete row-level data, summaries, all contrasts and provenance. Figures are in `results/new_family_sleep_20260910/figures`. Entry points are `src/new_family_sleep_analysis.py` and `src/plot_new_family_sleep.py`; independent review is recorded in `peer_review/15_new_family_sleep_results_review.md`. Earlier development candidates are preserved. Raw HDF5 files remain outside
the article directory. Public source citation and submission metadata still
require verification before submission.

// Public source references remain to be verified; do not render an empty bibliography.

The E3 candidate runner is `src/sleep_drift_candidate.py`, with the fixed specification in `config/sleep_drift_candidate_20260910.json`. Candidate vectors, held-out increments, refusals and provenance are retained under `results/sleep_drift_candidate_20260910`; the accepted run and reproduction commands are identified in `handover/20260910_sleep_drift_candidate_commands.md`. Independent support and final code reviews are recorded in `peer_review/16_sleep_drift_candidate_support_audit.md` and `peer_review/17_sleep_drift_candidate_final_review.md`.

The coordinate-support continuation is specified in `coordinate_support_policy_20260912.md` and `config/sleep_drift_coordinate_gate_20260912.json`. Its runner and outputs are `src/sleep_drift_coordinate_gate.py` and `results/sleep_drift_coordinate_gate_20260912`; the accepted revision is identified in `handover/20260912_sleep_drift_coordinate_gate_commands.md`. Reviews 18 and 19 retain the policy and final verification findings. Earlier E3 outputs are preserved.

= New-family distribution figures

Boxplots show medians and interquartile ranges, with whiskers at 1.5 IQR; outlier points are omitted from these distribution panels but retained in the data and Jacobian timelines. Unknown labels are shown separately and never combined with known stages.

#figure(image("results/new_family_sleep_20260910/figures/abscissa_distributions_sub-99_Sleep_acq-psg_3d.png", width: 100%), caption: [sub-99, 3D local-Jacobian endpoints. Descriptive recorded-label associations under a fixed recording-parent estimator.])

#figure(image("results/new_family_sleep_20260910/figures/abscissa_distributions_sub-1_Sleep_acq-psg_3d.png", width: 100%), caption: [sub-1, 3D local-Jacobian endpoints. Descriptive recorded-label associations under a fixed recording-parent estimator.])

#figure(image("results/new_family_sleep_20260910/figures/abscissa_distributions_sub-99_Sleep_acq-psg_9d.png", width: 100%), caption: [sub-99, 9D local-Jacobian endpoints. Descriptive recorded-label associations under a fixed recording-parent estimator.])

#figure(image("results/new_family_sleep_20260910/figures/abscissa_distributions_sub-1_Sleep_acq-psg_9d.png", width: 100%), caption: [sub-1, 9D local-Jacobian endpoints. Descriptive recorded-label associations under a fixed recording-parent estimator.])

#figure(image("results/new_family_sleep_20260910/figures/diffusion_distributions_sub-99_Sleep_acq-psg_3d.png", width: 100%), caption: [sub-99, 3D diffusion endpoints and producer diagnostics. Descriptive recorded-label associations under a fixed recording-parent estimator.])

#figure(image("results/new_family_sleep_20260910/figures/diffusion_distributions_sub-1_Sleep_acq-psg_3d.png", width: 100%), caption: [sub-1, 3D diffusion endpoints and producer diagnostics. Descriptive recorded-label associations under a fixed recording-parent estimator.])

