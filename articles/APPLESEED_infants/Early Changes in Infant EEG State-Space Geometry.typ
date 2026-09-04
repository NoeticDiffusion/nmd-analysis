#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Early Changes in Infant EEG State-Space Geometry: An Exploratory Longitudinal Reanalysis",
  short-title: "Infant EEG state-space geometry",
  subtitle: "An exploratory longitudinal reanalysis of an EEG-derived feature chart",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("infant EEG", "test--retest reliability", "longitudinal development", "neural dynamics", "Jacobian", "reachability"),
  article-type: "Research Article",
  abstract: [
    We assessed the reproducibility and early longitudinal change of EEG-derived state-space and local-flow summaries in 48 longitudinal EEG recordings from 13 infants. A shared global IQR anchor, fitted subject-balanced across 8,179 epochs, placed all recordings in a common cohort-anchored coordinate scale, while inference used one summary per child-session. Primary endpoints were three-dimensional Meta-Noetic Jacobian (MNJ) summaries and short-horizon reachability measures. Test--retest ICC estimates were heterogeneous and imprecise, with broad child-bootstrap intervals. In the balanced 11-child panel, no primary 3D dynamical endpoint survived the stated BH-FDR sensitivity correction at either eight or twelve months. An exploratory cohort-coordinate mobility contrast at twelve months decreased in all 11 children ($d_z=-1.51$, raw p=0.00098; coordinate-family FDR p=0.0029). This is a chart-level common-scale result, not evidence of a latent neural or maturational mechanism; the all-ages anchor and small sample preclude normative or predictive claims.
  ],
  author-summary: [
    Infant EEG measures must be stable enough to interpret but sensitive enough to change with development. We use repeated APPLESEED recordings to quantify short-interval agreement and to describe, without claiming confirmation, how EEG-derived chart summaries vary within the same children over the first year.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [No dedicated funding supported this secondary analysis.],
  data-availability: [The APPLESEED example dataset is publicly available through OpenNeuro: ds003710, version 1.0.2 @OpenNeuroDS003710. Analysis wrappers and derived tables are contained in this repository.],
  competing-interests: [The author declares no competing interests.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")

= Introduction
Repeated EEG measurements are essential for developmental neuroscience, but a feature is useful only if its short-interval variation can be distinguished from measurement instability. APPLESEED was developed to make pediatric EEG preprocessing and scale-wise entropy estimation more reproducible @Puglia2022. Its example dataset offers a compact test case: two recordings at approximately four months and, for most children, additional recordings at approximately eight and twelve months @OpenNeuroDS003710.

Entropy-based EEG measures have roots in sample- and multiscale-entropy methods @Richman2000 @Costa2002, but their interpretation depends on preprocessing, available data, and temporal scale @Grandy2016 @Kosciessa2020. The example recordings belong to a broader infant social-EEG research program @Puglia2020. Other infant EEG/MEG studies have reported age-associated changes in signal complexity or variability @DeWel2017 @Pelc2022, including a longitudinal infant MEG study @Hasegawa2018, while pediatric reviews document applications across several entropy algorithms and clinical contexts @Chu2017. Here we evaluate operational summaries derived from an existing NeuralManifoldDynamics export. Measured EEG is mapped to a three-coordinate chart and a stratified nine-coordinate chart; local flow is then summarized through a Jacobian and through short-horizon reachability. In this article, *state-space geometry* means the geometry of this EEG-derived feature chart, not a directly observed neural state space or latent neural manifold. Its reliability and developmental sensitivity must therefore be tested empirically.

#netn-box(title: [Core question])[
  What short-interval agreement do session-level MNJ and reachability summaries show at four months, and which within-child age contrasts are sufficiently stable to motivate follow-up studies?
]

= Theory
Let $x_t = [m_t, d_t, e_t]^T$ denote the exported three-dimensional EEG-derived state-space chart, whose coordinates operationally summarize mobility, deviation/diffusivity, and entropy-related variation. The local flow is summarized by:

$ J(x,t) = partial dot(x)_t / partial x_t $. <eq:mnj>

We summarize $J$ by its trace, Frobenius norm, antisymmetric rotation norm, and spectral radius. Separately, a local linear model yields a short-horizon covariance recursion:

$ Sigma_t^(h+1) = A_t Sigma_t^(h) A_t^T + Q_t $. <eq:reachability>

Its log-determinant, effective dimension, condition number, directional entropy, and rotation proxy summarize reachable local variation. For a covariance with eigenvalues $lambda_i$, effective dimension is $(sum_i lambda_i)^2 / sum_i lambda_i^2$, condition number is the largest-to-smallest eigenvalue ratio, and directional entropy is the normalized entropy of the eigenvalue proportions. These are features of the fitted measurement chart and local model, not direct estimates of a latent state.

= Methods
== Dataset
We analyzed the APPLESEED Example Dataset, OpenNeuro ds003710 version 1.0.2 @OpenNeuroDS003710, whose primary associated publication is the APPLESEED preprocessing paper @Puglia2022. The dataset has 48 EEG recordings from 13 infants (7 male and 6 female in the exported participant metadata). All contributed sessions 1 and 2 within approximately one week at four months; 11 children also contributed session 3 at eight months and session 4 at twelve months. Ages are nominal strata supplied by the file naming convention, not individually measured ages in this reanalysis. The release follows the BIDS organizing convention and its EEG extension @Gorgolewski2016 @Pernet2019. The dataset is public and de-identified; no new participant contact or intervention was undertaken, and the original data-collection ethics are reported in the source publication @Puglia2022.

== Export contract
We used the frozen cohort-anchor export `neuralmanifolddynamics_ds003710_20260804_153346`. Its shared IQR anchor (`ds003710_global_cohort_all_timepoints_iqr_v2_1`; hash `cb876d...d7a6fd7`) was fitted subject-balanced over all usable epochs and timepoints. Cohort-anchored 3D coordinates and 3D Jacobians are available in all 48 recordings; the 9D Jacobian is available in 46/48. The cohort-anchored 3D layer is the primary common-scale measurement layer; the subject-anchored layer is retained only for within-session event contrasts. The global anchor includes all ages, so it is a descriptive common reference frame rather than a held-out-age or predictive normalization.

== Endpoints and inference
The primary family contains nine endpoints: MNJ Frobenius norm, rotation norm, trace, spectral radius, reachability log-determinant, effective dimension, condition number, directional entropy, and reachability rotation. We used the shared `ndt-analysis` reachability implementation with within-session $k=12$ neighbors and horizon $h=3$; neighbors were never pooled across visits or children.

The statistical unit was a child-session, never an epoch or Jacobian window. Test--retest analysis paired sessions 1 and 2 for all 13 children. We report ICC(A,1), Pearson correlation, bootstrap intervals, standard error of measurement, minimum detectable change, paired Wilcoxon tests, and paired $d_z$ @ShroutFleiss1979 @McGrawWong1996 @BlandAltman1986 @KooLi2016. The primary longitudinal estimands are the four-month mean (sessions 1 and 2) versus session 3 at eight months and versus session 4 at twelve months, each evaluated across the nine-endpoint dynamical family in the 11-child panel. We report exact two-sided Wilcoxon signed-rank p-values using SciPy's `zero_method="wilcox"`, paired $d_z$, and 2,000-draw child-cluster bootstrap intervals for mean differences. The 9D Jacobian analysis is a separate complete-case sensitivity analysis (n=10 at 8 months and n=9 at 12 months) because 9D windows were not retained for `sub-13/ses-2` and `sub-10/ses-4`. Coordinate-position and conventional-EEG reliability are descriptive comparator families. Benjamini--Hochberg values are reported separately for the named 9-endpoint dynamical, 3-endpoint coordinate, 4-endpoint conventional, 18-test retest-mean, and 9D sensitivity families; they are transparency sensitivities rather than preregistered discovery thresholds @BenjaminiHochberg1995.

The reliability design is motivated by infant EEG connectivity work showing that agreement depends on the metric, network scale, and how available data are segmented or aggregated @VanDerVelde2019 @Haartsen2020. Adult MSE work likewise shows that reliability can vary across temporal scales and recording conditions @Kaur2019. Longitudinal infant EEG research highlights that developmental change can coexist with imperfect trait stability and practical recruitment or retention constraints @Anaya2021 @GabardDurnam2019 @Noreika2020.

== Robustness and exploratory analysis
We checked H5 availability, subject/session counts, geometry-contract status, retained Jacobian windows, and finite primary values. Bootstrap intervals resample children, not epochs. Session-1-only contrasts and Friedman tests are secondary baseline sensitivities. The stored retest-mean output applies one pooled 18-test BH family to the two primary four-month-mean contrasts; it does not change the primary estimand. Event-locked object, water, speech, and face contrasts are exploratory, age-pooled across available sessions, and not used to support the primary claims.

= Results
== R1: Coverage and validity
The final run included 48 H5 recordings: 13 children at sessions 1--2 and 11 children at sessions 3--4. Cohort-anchored 3D coordinates and 3D Jacobians were available in all 48 recordings. The 9D Jacobian was available in 46/48 recordings; 38 contracts were `ok` and 10 were `adjusted` because of 9D condition-number handling. Coverage and the complete geometry-contract audit are reported in S3.

#figure(
  kind: table,
  clean-table(
    columns: (1fr, 1fr, 1fr, 2fr),
    align: (center, center, center, left),
    table.header([*Session*], [*Children*], [*Nominal age*], [*Analytic role*]),
    [1], [13], [4 months], [Reliability baseline],
    [2], [13], [4 months], [Retest],
    [3], [11], [8 months], [Longitudinal follow-up],
    [4], [11], [12 months], [Longitudinal follow-up],
  ),
  caption: [APPLESEED longitudinal design. The two children without sessions 3--4 remain in the reliability analysis.]
)

== R2: Test--retest reliability
Test--retest agreement varied by endpoint. Cohort-anchored reachability log-determinant (ICC(A,1)=0.779; bootstrap 95% CI 0.216 to 0.942), condition number (0.946; CI -0.132 to 0.990), and directional entropy (0.535; CI -0.160 to 0.826) had the largest point estimates. The condition-number point estimate is therefore not a precise reliability claim; only the log-determinant interval excluded zero in this sample. Coordinate and conventional-EEG comparator reliabilities are reported separately in S2. No paired session difference was supported by the 9-endpoint, 13-child FDR sensitivity analysis. Complete estimates are in S2.

#figure(
  image("results/appleseed_cohort_20260805/04_figures/fig2_reliability_icc.svg", width: 90%),
  caption: [Absolute-agreement test--retest ICCs with child-bootstrap 95% intervals. The broad intervals and endpoint heterogeneity preclude a strong reliability claim in this example sample.]
)

== R3: Exploratory 4-to-8-month developmental comparison
We restricted this analysis to the 11 children with both four- and eight-month recordings, excluding the two reliability-only children. For each child, the four-month value was the mean of sessions 1 and 2. The smallest raw p-values in the nine-endpoint family were for lower reachability effective dimension (mean difference -0.096, paired $d_z=-0.48$, raw p=0.102) and lower directional entropy (mean difference -0.0425, $d_z=-0.39$, raw p=0.102); their separate nine-test BH sensitivity values were 0.309. Spectral radius increased modestly (mean difference 0.00493, $d_z=0.47$, raw p=0.175). In the shared coordinate frame, mobility decreased (mean difference -0.554, $d_z=-0.48$, raw p=0.206), while deviation and entropy-related coordinates increased (0.594, $d_z=0.44$, p=0.175; and 0.504, $d_z=0.42$, p=0.278). These are ranked descriptive contrasts, not multiplicity-corrected discoveries.

The same 11-child 4-month mean to 12-month comparison showed no raw-p signal among the nine 3D dynamical endpoints (smallest p=0.365 for directional entropy). In contrast, the cohort-anchored mobility coordinate decreased in all 11 children (mean difference -1.365, $d_z=-1.51$, raw p=0.00098; BH p=0.0029 within the three-coordinate family; child-bootstrap 95% CI -1.940 to -0.888), whereas the deviation and entropy-related coordinate contrasts were not supported. The sign of a within-child coordinate change is invariant to a global positive affine IQR map, but its magnitude and any Jacobian/reachability summary are anchor-dependent. This large coordinate shift is therefore an exploratory common-scale chart result, not a direct neural-state or maturational mechanism.

#figure(
  kind: table,
  clean-table(
    columns: (2.1fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center),
    table.header([*Endpoint*], [*4-month to 8-month difference*], [*Paired $d_z$*], [*Raw p*]),
    [`tube_d_eff`], [-0.096], [-0.48], [0.102],
    [`spectral_radius`], [0.00493], [0.47], [0.175],
    [`tube_dir_entropy`], [-0.0425], [-0.39], [0.102],
  ),
  caption: [Three post-hoc display endpoints with the largest absolute paired $d_z$ values among the nine exploratory 4-to-8-month dynamical tests. Four-month values are each child's mean of sessions 1 and 2; all tests use the same 11 children. Raw p-values are descriptive, not multiplicity-corrected confirmatory tests.]
)

#figure(
  image("results/appleseed_cohort_20260805/04_figures/fig3_exploratory_4to8_effects.svg", width: 88%),
  caption: [Exploratory paired effect sizes for the three highlighted 4-to-8-month contrasts. Labels give raw p-values; neither color nor annotation denotes multiplicity-corrected significance.]
)

#figure(
  image("results/appleseed_cohort_20260805/04_figures/fig4_paired_4to8_slopes.svg", width: 100%),
  caption: [Within-child 4-to-8-month trajectories for the same three exploratory endpoints. Each line is one child; the four-month value is the mean of sessions 1 and 2.]
)

#figure(
  image("results/appleseed_cohort_20260805/04_figures/fig6_cohort_coordinate_4to8_slopes.svg", width: 100%),
  caption: [Exploratory paired shifts in the common cohort-anchored 3D coordinate scale. The coordinates are EEG-derived chart summaries, not directly observed neural states.]
)

#figure(
  image("results/appleseed_cohort_20260805/04_figures/fig7_paired_4to12_slopes.svg", width: 100%),
  caption: [Within-child 4-to-12-month trajectories for the three post-hoc display dynamical endpoints. No 3D dynamical contrast was supported after the raw-p exploratory screen.]
)

#figure(
  image("results/appleseed_cohort_20260805/04_figures/fig8_cohort_coordinate_4to12_slopes.svg", width: 100%),
  caption: [Exploratory paired 4-to-12-month changes in the common cohort-anchored coordinate scale. The mobility-coordinate change is large but remains a chart-level, not mechanistic, result.]
)

== R4: Robustness and event exploration
All primary analyses aggregate epochs and Jacobian windows before inference. The pooled 18-test BH sensitivity applied to the two primary age contrasts produced no FDR-significant session 3 or 4 contrast (minimum adjusted p=0.618). In the separate age-pooled event analysis, the water-deviation contrast had raw permutation p=0.0055 and 12-test BH p=0.066; this remains exploratory, with heterogeneous event coverage and some sessions having very low stage-label coverage. Neither analysis changes the primary endpoint family or its correction scope.

= Discussion
The contribution of this study is an auditable, session-level evaluation surface for infant EEG state-space geometry. Reliability must be interpreted endpoint by endpoint: correlation alone is not absolute agreement, and agreement alone is not developmental sensitivity. The balanced 11-child panel did not provide FDR-supported evidence for change in the nine primary 3D dynamical endpoints at either follow-up. The all-children directional decrease in the twelve-month mobility coordinate is a useful hypothesis for replication, but it is a chart-level coordinate result with only moderate coordinate reliability and no claim to be a validated developmental marker.

The present analysis extends the public dataset's original use rather than reproducing its primary claim: Puglia, Slobin, and Williams developed and validated APPLESEED for pediatric preprocessing and scale-wise entropy estimation @Puglia2022. Other infant studies have reported developmental variation in entropy, EEG/MEG variability, or EEG power @DeWel2017 @Hasegawa2018 @Pelc2022 @GabardDurnam2019, but those studies used different cohorts, sensors, preprocessing contracts, endpoints, and estimands. Their findings therefore provide context for the present reliability question, not external validation of MNJ or reachability.

MNJ and reachability summaries are local-model outputs on an operational chart. The analysis does not establish that any coordinate is a latent neural variable, that the chart is unique, or that within-child changes are caused by maturation rather than recording-context differences. The small sample gives low precision for signed-rank contrasts; the nominal age strata are not measured ages, the global anchor is fitted using all study ages, event coverage is unequal, and 9D-Jacobian loss/adjustment leaves unmatched sensitivity samples (n=10 and n=9). Coordinate and conventional-EEG comparators are descriptive rather than validation benchmarks.

This work separates reliability, within-child change, and exploratory event effects in a public longitudinal infant EEG dataset, providing a reproducible template for more highly powered developmental studies.

= Acknowledgements
We thank the APPLESEED authors and OpenNeuro for releasing the example dataset. This secondary analysis used the public de-identified ds003710 release and involved no new data collection, intervention, or individual-level clinical inference.

#bibliography("references.bib", style: "apa")
