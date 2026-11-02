#import "template_eLife.typ": *
#set page(numbering: "1")
#show: netn-template.with(
  title: text(hyphenate: false)[Neural State Geometry and Dynamical Measurement Families Across Sleep],
  short-title: "Neural State Geometry Across Sleep",
  subtitle: "A descriptive analysis of 128 nights from 100 people",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("sleep", "neural state", "MNPS", "diffusion geometry", "EEG", "measurement"),
  article-type: "Research Article",
  abstract: [
    We describe local-Jacobian and diffusion measurement families across the entire locally available PSG cohort of OpenNeuro ds005555: 128 nights from 100 people. Continuous 30-second processing yielded 120,091 epochs with exact alignment to human-scored sleep labels. Nine fixed endpoints were summarized within each night, then within person, before calculating cohort medians and quartiles. N2-minus-Wake contrasts were available for 100 people in canonical 3D and 98 in 9D. Total diffusion magnitude was lower in N2 in 97 of 100 people, with a cohort median contrast of -0.033018 recording-relative coordinate-squared per second. Numerical abscissa and reactivity-gap contrasts had negative medians and quartile intervals in both representations. Effective diffusion dimension and concentration showed more heterogeneous directions. All selected endpoints and missing results were retained. These are label associations of existing recording-parent estimators. Recording-relative coordinates, global reference fitting and unknown effective temporal support preclude interpreting the contrasts as isolated stage effects, independently identified diffusion mechanisms or clinical validation.
  ],
  author-summary: [We extended the development analysis to every locally available PSG night and counted repeated nights within the same person. Lower total diffusion magnitude in N2 was common across people; changes in its dimensionality and concentration were less consistent. The analysis keeps missing measurements visible and separates descriptive label associations from claims about underlying biological mechanisms.],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [Funding information has not been finalized for this working manuscript.],
  data-availability: [The local ds005555 source inventory, H5 identities, analysis configuration and verification records are bound by SHA-256 manifests. HDF5 data are retained separately from the article source; complete descriptive tables accompany this manuscript.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)
#set heading(numbering: "1.")

= Introduction

Sleep recordings allow a measurement framework to be examined across changing recorded states. An endpoint can nevertheless depend on its coordinate representation, the reference used to normalize the recording and the temporal or neighborhood support of its estimator. A change associated with a sleep label therefore need not identify a stage-specific dynamical mechanism.

This study reports the complete locally available PSG cohort of ds005555 using the existing NeuralManifoldDynamics measurement contract. It extends the earlier two-recording development analysis to 128 nights from 100 people. The primary comparison is the within-night difference between N2 and Wake medians, summarized once per person before cohort aggregation. All nine prespecified Jacobian and diffusion endpoints remain in the report, including heterogeneous directions and unsupported outputs.

= Methods

== Cohort and recording identity

The local inventory contains PSG recordings sub-1 through sub-128 and a simultaneously acquired headband recording for each night. The established configuration selects PSG and excludes the headband acquisitions. The participant metadata explicitly define BIDS `participant_id` as a recording identifier and `pid` as the person shared across sessions. The 128 nights map to 100 unique people: 80 with one night, 12 with two nights and eight with three nights. The dataset README reports 108 people; the local participant table governs this analysis and the discrepancy remains unresolved.

Fresh outputs for sub-1 and sub-99 are included. Their people, pid 89 and 66, remain marked as previously inspected development participants. The earlier development H5 files and historical stage-sampled cohort are excluded from the current input manifest. The cohort plan was fixed before this full-cohort contrast run, after inspection of the development recordings; it is not a preregistration or an unseen-data confirmation.

== Continuous measurement and label mapping

The delivery uses 30-second epochs with a 30-second step, stage sampling disabled and the configured full recording extent. It preserves canonical MNPS `[m,d,e]` and 9D definitions, missingness, producer validity and recording-global reference fitting. The coordinates retain their recorded multimodal and fallback provenance; they are not assumed to be exclusively EEG-derived or universally calibrated between people.

Every exported epoch was checked against the executed crop support and raw EDF duration. Epoch identities are consecutive from zero, window bounds touch without gaps and timestamps equal window centers. The human annotation field `stage_hum`, described in the source metadata as the majority vote of three expert scorers, was independently matched by onset to every exported label. AI labels were not substituted. Wake, N1, N2, N3 and REM remain separate; code 8 is retained separately as an unresolved disconnection label. Other unknown labels have their own category.

Four recordings (sub-36, sub-57, sub-104 and sub-126) end at an exact 30-second raw boundary. The existing crop implementation excludes a final sample, causing the last full 30-second window to fall outside executed support in these recordings. These four windows were not padded or reconstructed. Other trailing remainders remain outside the complete epoch grid. Continuous coverage here means the full grid supported by the executed crop, not retention of every raw sample.

== Fixed endpoint definitions

The six local-Jacobian endpoints are spectral abscissa, numerical abscissa and their gap, separately in 3D and 9D. Spectral abscissa is the largest real part of an eigenvalue of $J$. Numerical abscissa is the largest eigenvalue of $(J + J^T)/2$. Reactivity gap is numerical minus spectral abscissa for the same stored window. The numerical abscissa and gap depend on the coordinate metric. They have inverse-second units under the measured 30-second derivative interval.

For canonical 3D diffusion, the stored conditional increment-covariance tensor $a$ supplies total magnitude `D_total = trace(a)`, effective dimension `d_diff = trace(a)^2 / sum(lambda_i^2)` and concentration `c_diff = lambda_max / (trace(a) + epsilon)`, using the producer's existing numerical guard and validity rules. `D_total` has recording-relative coordinate-squared-per-second units; dimension and concentration are dimensionless. These objects remain chart-dependent covariance measurements, without an independently qualified SDE drift or latent Ito-tensor interpretation.

Jacobian rows are attached to labels through explicit center positions on their own 3D or 9D grids. Diffusion rows use their explicit query-to-epoch mapping. Stored computation status, finite arrays and producer validity determine usable rows; scientific qualification remains unevaluated. Missing centers are not interpolated. No estimator is refitted by stage, and a label at a center or query does not establish that the estimator's full support lies within that stage.

== Aggregation and missingness

For each endpoint and label, we calculate the median and quartiles within each night. Available night-level medians are reduced to one median per pid, then summarized by the median and quartiles across people. The fixed N2-minus-Wake contrast is calculated only within a night with usable values in both labels. Night-level contrasts are reduced to a median contrast per pid before cohort aggregation. This avoids pairing stages across different nights and avoids giving people with more nights extra weight.

Counts accompany every endpoint and stage. Missing or unsupported measurements remain null; no zero substitution or imputation is performed. Code 8 and other unknown labels are never pooled with a known stage. The participant development marker depends on all of that person's recording metadata, independently of endpoint availability. Epochs and repeated nights are not independent participants. For presentation, negative and positive person-level contrasts are additionally counted for all nine endpoints. These descriptive direction counts supplement the fixed median/quartile summaries. No p-values, confidence intervals, causal effects or confirmatory population inference are calculated; reported quartiles describe between-person variation.

== Verification and execution provenance

A separate coordinator implementation reads HDF5 arrays directly, without importing the analysis runner or its endpoint reader. It checks raw support, human annotations, coordinate shapes, producer masks and manifest identities, and reconstructs recording, person and cohort summaries. The article test suite contains 172 passing tests, including seven focused cohort-delivery tests. These checks establish implementation and arithmetic behavior rather than biological validity.

Operational recovery preserved full-precision feature tables and explicitly retained failed attempts. During the final run, a separate I-CARE task changed four CLI/orchestration files to add `--resume-run`. The sleep job had already loaded its summary module and used a shared thread pool without that flag or a module reload. Retention of the already loaded code is an execution inference, documented with the timeline and hash differences. The observed filesystem flag `source_hashes_stable=false` is preserved. Analysis uses a separately reviewed manifest of all 128 H5 identities; it does not convert that flag into a claim of a frozen source tree.

= Results

== Complete delivery and endpoint availability

The delivered dataset contains 128 H5 recordings, 100 people and 120,091 consecutive epochs, corresponding to 1,000.758 hours of exported support. All exported human-scored labels match the raw annotations. The label counts are shown in @tab:stage-counts; these are coverage counts, not independent statistical observations.

#figure(
  table(columns: (1fr, 1fr), inset: 5pt,
    table.header([*Recorded label*], [*Epochs*]),
    [Wake], [19,133], [N1], [4,462], [N2], [72,181],
    [N3], [5,225], [REM], [18,754], [Code 8], [336], [Other unknown], [0],
  ),
  caption: [Coverage of the executed 30-second grid across all 128 nights. Missing endpoint measurements are handled separately from label coverage.],
) <tab:stage-counts>

3D Jacobian and diffusion families are recorded as computed in all 128 nights. The 9D Jacobian branch is absent in sub-3 and sub-4; their 9D summaries and contrasts remain null, while their available 3D results remain included. The N2-minus-Wake contrast therefore includes 100 people for 3D Jacobian and diffusion endpoints and 98 people for 9D Jacobian endpoints. Unknown effective temporal support is recorded for every H5 source.

== Within-person N2-minus-Wake contrasts

The complete endpoint comparison is retained in @tab:cohort-contrasts and @fig:cohort-contrasts. `D_total` decreases in 97 of 100 people. Its median contrast is -0.033018, with quartiles -0.061145 and -0.017320. Effective dimension has a positive median contrast of 0.066915, but decreases in 36 people and increases in 64. Concentration has a negative median contrast of -0.019379, with 59 decreases and 41 increases. The dimension and concentration quartile intervals span zero.

Both numerical-abscissa contrasts and both reactivity-gap contrasts have negative medians and negative quartile intervals. Numerical abscissa decreases in 90/100 people in 3D and 81/98 in 9D; the gap decreases in 86/100 and 74/98 respectively. Spectral-abscissa medians are also negative in both representations, but their quartile intervals span zero. A lower abscissa contrast does not itself establish that either stage has a negative absolute abscissa or stable dynamics.

#figure(
  { set text(size: 8pt)
    table(columns: (1.5fr, .4fr, .4fr, 1fr, 1.75fr, .65fr), inset: 4pt,
    table.header([*Endpoint*], [*D*], [*n*], [*Median*], [*Q25, Q75*], [*-/+*]),
    [Spectral abscissa], [3], [100], [-0.000548], [-0.001740, 0.000559], [64/36],
    [Numerical abscissa], [3], [100], [-0.002415], [-0.004762, -0.001024], [90/10],
    [Reactivity gap], [3], [100], [-0.001519], [-0.002682, -0.000511], [86/14],
    [Spectral abscissa], [9], [98], [-0.001558], [-0.003079, 0.000034], [72/26],
    [Numerical abscissa], [9], [98], [-0.008233], [-0.015480, -0.002711], [81/17],
    [Reactivity gap], [9], [98], [-0.006188], [-0.013053, -0.000215], [74/24],
    [D_total], [3], [100], [-0.033018], [-0.061145, -0.017320], [97/3],
    [d_diff], [3], [100], [0.066915], [-0.051590, 0.171578], [36/64],
    [c_diff], [3], [100], [-0.019379], [-0.050428, 0.015149], [59/41],
    )
  },
  caption: [N2-minus-Wake contrasts after within-night and within-person aggregation. D denotes coordinate dimension; n counts people with a usable paired contrast. -/+ gives the numbers of negative and positive person-level contrasts; none is exactly zero. Jacobian endpoints have inverse-second units. Diffusion units are defined in Methods. Quartiles are descriptive intervals, not confidence intervals.],
) <tab:cohort-contrasts>

The small two-recording development comparison is thus replaced as the main evidence by the complete local cohort. Its diffusion-magnitude direction is common across people, whereas dimension and concentration show substantial heterogeneity. All nine endpoints remain reported; no measurement was selected or retuned to strengthen direction agreement.

= Discussion

The most consistent descriptive observation is lower total conditional increment-covariance magnitude at N2-labeled queries than at Wake-labeled queries. Numerical abscissa and reactivity gap also tend to decrease in both coordinate representations. The less uniform dimensionality and concentration changes show that lower magnitude does not imply one common change in diffusion shape across people.

These contrasts describe existing recording-parent estimators. Their neighborhoods are not stage-restricted, recording-global reference fits use the whole night, and effective upstream filter support remains unknown. Time of night, unequal stage support, coordinate normalization and multimodal provenance can contribute to the observed associations. The analysis does not isolate a stage-specific mechanism, identify an independent stochastic drift, or validate a biomarker or consciousness theory.

The local dataset's person-count discrepancy, four crop-boundary window losses and absent 9D exports in two nights are retained as limitations. Operational source-file changes prevent a claim that the working tree stayed frozen. The final sub-99 export also differs numerically from its earlier fresh pilot despite identical retained feature values: the maximum absolute coordinate difference is 4.77e-7 and the maximum 9D Jacobian-entry difference is 5.64e-5. Exact bitwise equivalence is not claimed. Final-artifact arithmetic is checked against the actual pinned H5 values.

Independent drift, drift-diffusion coupling, recording-horizon finite-time response, Q/W_Q volume, destination and resilience are outside this stage-associated endpoint set. Their stored availability or method-limited status is inventoried separately. Expanding their scientific interpretation is not a prerequisite for delivering and describing the present cohort.

= Data and code availability

The analysis entry point is `src/sleep_cohort_analysis.py`, with the fixed cohort configuration and the coordinator-reviewed input manifest dated 2026-09-12. Complete endpoint rows, 8,064 recording-stage rows, 1,152 recording contrasts, 6,300 person-stage rows, 900 person contrasts, 63 cohort-stage rows and all nine cohort contrasts are retained under `results/sleep_cohort_20260912`. Missing rows remain part of these tables. The figure is generated by `src/plot_sleep_cohort.py` from person-level contrasts.

Source inventories, H5 SHA-256 identities, failed-run records, exact feature-preservation checks, raw-annotation checks and execution reviews are retained in the delivery manifests. Independent review is recorded in `peer_review/20_sleep_cohort_delivery_review.md` and the coordinator review in `peer_review/21_sleep_cohort_final_review.md`. The previous manuscript is preserved as `Development history before full cohort 20260912.typ`; its development outputs remain separate. This working manuscript has not been submitted or published.

#pagebreak()
#figure(
  image("results/sleep_cohort_20260912/figures/sleep_cohort_pid_n2_minus_wake_contrasts.svg", width: 100%),
  caption: [Person-level N2-minus-Wake contrasts for all nine fixed endpoints. Each point is one person's median within-night contrast; the diamond and bar show the cohort median and interquartile range. Panels retain their own numerical scales and report available-person counts. The two people without 9D Jacobian exports remain missing in those panels. The intervals do not represent inferential uncertainty.],
) <fig:cohort-contrasts>
