#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Registered descriptive reanalysis of BOAS sleep-stage geometry",
  short-title: "BOAS sleep-stage geometry",
  subtitle: "A method-limited audit of local metrics and dynamical measurement families",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("sleep", "neural geometry", "abscissa", "finite-time response", "measurement audit", "reanalysis"),
  article-type: "Research Article",
  abstract: [
    We report an exploratory registered reanalysis of the supplied stage-sampled BOAS sleep run derived from OpenNeuro ds005555 v1.1.1. The analysis asks which descriptive local-Jacobian, finite-time-response, and newer dynamical-family outputs are supported at their actual measurement levels. The run contains 128 recording IDs from 100 biological participants, 16,629 selected 30-second windows, and 1,469 sampling gaps. The preregistered primary contrast is target sleep stage minus Wake, summarized first within recording and then within person. In the largest fallback stratum (PPG, subject-anchored 3D), the N2-minus-Wake median was -0.000647 for spectral abscissa and -0.002557 for numerical abscissa; person-cluster percentile bootstrap intervals were [-0.001518, -0.000114] and [-0.004512, -0.001333], respectively. These are descriptive summaries in reported measurement units, not qualified biological effects. Finite-time response was available at all registered horizons for 3D and for 126 of 128 recordings in 9D. The diffusion parent remained not testable because of irregular increment timing, while its recording-level increment covariance child remained separately computed. This exploratory reanalysis is not an independent confirmation and does not test C1, C2, or C3. The interpretation ceiling is METHOD-LIMITED.
  ],
  author-summary: [
    We audited what a stage-sampled sleep measurement run can support without changing the measurement contract. The result is a reproducible descriptive package with explicit gaps, fallback strata, unavailable values, and family-level qualification limits; it is not a biological validation or a test of the theory's C1/C2/C3 claims.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted at submission.],
  data-availability: [The source dataset is OpenNeuro ds005555 v1.1.1 (DOI: 10.18112/openneuro.ds005555.v1.1.1). The registered source run, frozen v5 output, analysis scripts, derived tables, and review records are retained in the accompanying repository package.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")

= Introduction <sec:intro>

Neural state measurements are only as informative as their sampling, support, and qualification allow. This is especially important when a single analysis package contains local fitted-Jacobian summaries, model-derived finite-time responses, and newer dynamical families with different native grains and failure conditions. The present work therefore treats the supplied BOAS sleep run as a measurement audit and registered descriptive reanalysis rather than as a direct test of a biological theory.

The source run is stage-stratified and sampled rather than a continuous full-night recording. Its stored rows contain explicit gaps, and the original sampling-block identifiers are not available in the HDF5 output. A sequence of touching stored rows is therefore treated as an observed contiguous run, not as recovery of an unobserved continuous block.

#netn-box(title: [Core question])[ 
  What descriptive sleep-stage contrasts and dynamical-family outputs can be reported from the supplied run while preserving the measurement contract, missingness, support limits, provenance, and distinction between computed and scientifically qualified objects?
]

= Theory and measurement boundary <sec:theory>

The primary A1 quantities are the spectral abscissa and numerical abscissa of the supplied local fitted-Jacobian outputs. They are summarized descriptively within each eligible recording and then across recordings within biological `pid`. For a target stage $s$ and endpoint $q$, the registered direction is

$ Delta_(s - "Wake") (q) = M_(i in s)(q_i) - M_(i in "Wake")(q_i). $ <eq:contrast>

Here $M$ denotes the median over eligible centers.

The 3D and 9D coordinate representations remain separate. The reanalysis does not refit the Jacobian, select a new feature because it separates stages, impute missing values, or convert a computed family into a biological estimand. Reactivity gap is retained as a derived diagnostic; it is not promoted above the preregistered spectral and numerical abscissae.

= Methods <sec:methods>

== Dataset and source run

The run manifest identifies OpenNeuro ds005555 v1.1.1, 128 HDF5 recording IDs, 100 biological `pid` values, a 30-second epoch interval, stage-stratified sampling from configured five-minute blocks, and seed 42. The selected stages were Wake, N2, N3, and REM; N1 was absent from the selected run. The read-only audit found 16,629 selected windows and 1,469 gaps totalling 2,318,850 omitted seconds, with median gap 480 seconds and maximum gap 18,780 seconds.

== NMD pipeline and fallback strata

The reanalysis consumes the existing source run and keeps its subject-anchored canonical MNPS 3D `[m,d,e]` and 9D representations, validity fields, missingness, and provenance. Auxiliary fallback strata are reported separately: `ppg_rate_bpm` was available for 99 recordings, `eog_blink_rate` for 26, and `eeg_highfreq_power_30_45` for 3. These fallback variables are not treated as semantically interchangeable.

== Registered endpoints and support rules

The A1 primary descriptive endpoints were spectral and numerical abscissa, with N2-minus-Wake as the primary sleep-stage contrast and N3/REM as secondary contrasts. Recording-level contrasts required at least five eligible centers in each compared stage. Person-level summaries are medians across eligible recordings. Boundary sensitivity retained only eligible centers whose preceding, current, and following stored epochs had the same known stage and touched the current center; gaps fail this rule.

The A2 finite-time-response family was reported at h1, h2, and h4, with its native recording-horizon summaries and registered usability status. The A3 ledger retains the family role, computation status, support status, qualification status, failure reason, and claim status. The diffusion parent is not testable under materially irregular increment timing. The recording-level increment covariance child is a separate computed object and is not an Ito diffusion tensor.

== Statistical design

This is a descriptive analysis. No p-values, null-hypothesis tests, effect-size qualification, or multiple-comparison correction were introduced. For the registered A1 summaries, the reported uncertainty display is a 10,000-replicate person-cluster percentile bootstrap with seed 20260923. It is presented as a resampling interval around a descriptive median, not as evidence of a qualified biological effect.

== Review and freezing

The v5 output was independently audited by reconstructing A1 recording contrasts from the serialized eligible centers and checking person and summary reductions from the serialized lower-grain tables. The audit passed for the full and boundary passes, A2 usability counts, A3 status separation, and script identity. The v5 package was then copied to a separate frozen snapshot. Derived article tables and figures were generated from that snapshot without modifying it.

= Results <sec:results>

== Coverage and data quality <sec:r1>

The analysis retained the source gaps and did not join across them. The main coverage facts are shown in @tab-coverage and the stage/gap/FTR/family overview in @fig-support.

#figure(
  kind: table,
  clean-table(
    columns: (1.2fr, 2fr, .8fr, 2.4fr),
    align: (left, left, right, left),
    inset: 4pt,
    table.header([*Section*], [*Item*], [*Value*], [*Interpretation*]),
    [Coverage], [Recordings], [128], [HDF5 recording IDs],
    [Coverage], [Biological pids], [100], [Repeated recordings retained],
    [Coverage], [Selected windows], [16,629], [30-second sampled windows],
    [Coverage], [Sampling gaps], [1,469], [Omitted intervals retained as gaps],
    [Coverage], [Omitted seconds], [2,318,850], [Not imputed or joined],
    [Stage], [Wake], [4,695], [N1 absent from selected run],
    [Stage], [N2], [5,118], [Selected-window count],
    [Stage], [N3], [1,854], [Selected-window count],
    [Stage], [REM], [4,962], [Selected-window count],
    [Fallback], [PPG / EOG / EEG HF], [99 / 26 / 3], [Recordings per fallback stratum],
  ),
  caption: [Source-run coverage and fallback inventory. Complete machine-readable versions are retained in `results/article_tables_20260924_v5/table_1_coverage.csv` and `.md`.]
) <tab-coverage>

#figure(
  image("figures/registered_v5/figure_2_coverage_and_status.png", width: 100%),
  caption: [Coverage, gap-duration, finite-time-response usability, and A3 ledger status in the frozen v5 package. Statuses overlap across measurement families and are not mutually exclusive recording categories.]
) <fig-support>

== Primary descriptive contrasts <sec:r2>

For the largest and most consistently represented fallback stratum (PPG, subject-anchored 3D), the full-pass N2-minus-Wake median was negative for both primary endpoints: -0.000647 for spectral abscissa and -0.002557 for numerical abscissa. The corresponding person-cluster percentile intervals were [-0.001518, -0.000114] and [-0.004512, -0.001333]. N3-minus-Wake was also negative in this stratum, whereas REM-minus-Wake was positive for the spectral abscissa and close to zero in the numerical-abscissa interval. These values are descriptive contrasts in reported units, not biologically qualified effects.

#figure(
  kind: table,
  clean-table(
    columns: (1.35fr, .75fr, 1.25fr, .65fr, 1.15fr, 1.7fr),
    align: (left, center, left, right, right, right),
    inset: 3pt,
    table.header([*Contrast*], [*Pass*], [*Endpoint*], [*$n$ people*], [*Median*], [*Bootstrap q025--q975*]),
    [N2 minus Wake], [Full], [Spectral abscissa], [76], [-0.000647], [-0.001518 -- -0.000114],
    [N2 minus Wake], [Full], [Numerical abscissa], [76], [-0.002557], [-0.004512 -- -0.001333],
    [N3 minus Wake], [Full], [Spectral abscissa], [33], [-0.001872], [-0.003083 -- -0.000462],
    [N3 minus Wake], [Full], [Numerical abscissa], [33], [-0.005922], [-0.007751 -- -0.003335],
    [REM minus Wake], [Full], [Spectral abscissa], [75], [0.000720], [0.000164 -- 0.001588],
    [REM minus Wake], [Full], [Numerical abscissa], [75], [0.000761], [-0.000967 -- 0.002236],
  ),
  caption: [Primary PPG 3D descriptive summaries. The interval is a person-cluster percentile bootstrap display with 10,000 replicates; it is not an inferential qualification.]
) <tab-primary>

#figure(
  image("figures/registered_v5/figure_1_a1_primary_contrasts.png", width: 100%),
  caption: [PPG fallback, subject-anchored 3D A1 contrasts. Points are person-level medians; whiskers are the registered person-cluster percentile intervals. The boundary-only pass is a sensitivity reduction, not a continuous-recording reconstruction.]
) <fig-primary>

== Finite-time response and family-level status <sec:r3>

Finite-time response was usable at h1, h2, and h4 for all 128 recordings in 3D and for 126 of 128 recordings in 9D. The exact `sub-3` and `sub-4` 9D rows had zero valid sequences at all registered horizons and remain unavailable. The family ledger reports computed outputs only at their native measurement level. In particular, the diffusion parent is `not_testable` because increment timing is materially irregular, while the increment covariance child is `computed` with sufficient support and positive increment-pair counts. No family-level status is treated as a biological claim.

The complete FTR support table is `results/article_tables_20260924_v5/table_3_a2_ftr_support.csv`; the complete A3 status table is `results/article_tables_20260924_v5/table_4_a3_family_status.csv`.

= Discussion <sec:discussion>

== What this analysis establishes

The frozen package establishes a reproducible descriptive account of the supplied sampled run: its stage inventory, gap structure, fallback coverage, eligible A1 contrasts, registered boundary sensitivity, FTR usability, and family-specific computation/status ledger. The v5 direction correction also ensures that the named A1 contrasts are consistently target minus Wake at recording, person, summary, and bootstrap grains.

== What it does not establish

The measurements do not establish local fit fidelity, effective continuous signal support, a stage-intrinsic biological law, a causal sleep-stage effect, independent confirmation, or a test of C1/C2/C3. Sleep stage is an observational label, not an intervention or a report of experience. Computed finite-time responses, drift summaries, or increment covariances must not be promoted to qualified future laws or diffusion tensors without a separate qualification gate.

== Limitations and next gate

The run is stage-sampled and contains long gaps; N1 is absent; fallback strata are unequal and non-equivalent; the original sampling-block IDs are unavailable; fit fidelity is not evaluated; and the planned continuous-support pilot was not executed here. The next valid scientific step is a separately scoped continuous-support pilot with its own output root, source/config/code hashes, temporal-support audit, and qualification criteria. It must not be used to tune this registered reanalysis or silently replace the frozen result.

== Conclusion

This exploratory registered reanalysis is *PASS* for reproducible descriptive measurement reporting and *METHOD-LIMITED* for biological interpretation. The frozen v5 package preserves negative evidence and unsupported values as unavailable. It provides a stable basis for transparent tables and figures, not a confirmatory theory test.

= Data and code availability

The frozen result directory is `results/registered_reanalysis_20260923_frozen_v5`. The derived table and figure manifest is `results/article_tables_20260924_v5/article_outputs_manifest.json`. The independent review note is `peer_review/pr_01_registered_reanalysis_20260924.md`. The source run and all HDF5 inputs are retained read-only under the repository's data/raw provenance path.

= Acknowledgements

We acknowledge the original investigators, participants, data stewards, and the OpenNeuro infrastructure that made the source dataset available. This work was developed with computational assistance from language models; all analysis boundaries, artifact qualifications, and final claims remain the responsibility of the author.
