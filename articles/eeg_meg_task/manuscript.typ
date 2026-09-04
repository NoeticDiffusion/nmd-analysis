#import "template_eLife.typ": *

#show: netn-template.with(
  title: "EEG--MEG Concordance of Neural-Manifold Feature Surfaces in Healthy Adults",
  short-title: "Healthy EEG--MEG Concordance",
  subtitle: "A paired analysis of simultaneous MEEG FacePerception recordings",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "[keyword 1]",
    "[keyword 2]",
    "[keyword 3]",
    "[keyword 4]",
    "[keyword 5]",
    "[keyword 6]",
  ),
  article-type: "Research Article",
  abstract: [
    [We evaluated agreement between EEG and MEG feature surfaces in the healthy simultaneous-MEEG FacePerception cohort ds003645. The analysis included 18 participants and 108 participant-run H5 exports. Matched feature families were compared within subject at global and topographic regional levels. Temporal concordance varied substantially by feature family and topology, whereas subject-level feature means retained modality-dependent offsets. At the global level, alpha/theta, high-frequency power, sample entropy, and theta differences survived within-family FDR correction; regional effects varied by topology. The currently exported global MNPS trajectory is MEG-primary shadow mapping, rather than an independent EEG global chart. A QC audit also found that all six EEG regional MNPS trajectories are identical within each run; they were not treated as six independent regional geometry measurements. This report therefore establishes an auditable feature-level concordance analysis and identifies a regional EEG export limitation that must be repaired before symmetric regional MNPS or reachability inference.]
  ],
  author-summary: [
[Simultaneously recorded EEG and MEG show feature- and topology-dependent temporal agreement while retaining differences in average feature values. The analysis also exposes an export-level regional EEG collapse, preventing overinterpretation of apparently regional EEG manifold results.]
  ],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted at submission.],
  data-availability: [The ds003645 H5 exports are under `data/raw/neuralmanifolddynamics_ds003645_20260722_215042`; article-local code and outputs are under this article directory.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")

= Introduction <sec:intro>

[EEG and MEG provide complementary sensor-level views of neural population activity. A shared feature contract enables a direct paired question: which dynamics agree across modalities, and which remain modality dependent? This analysis is deliberately descriptive and healthy-only; it does not test a clinical group contrast.]

#netn-box(title: [Core question])[
  [Within healthy simultaneous MEEG recordings, do matched EEG and MEG feature surfaces agree across time and across participants at global and regional levels?]
]

= Theory <sec:theory>

== Theoretical framework and primary metric

[NeuralManifoldDynamics exports feature surfaces and low-dimensional chart summaries as operational measurement objects. The H5 contract contains matched `eeg_*` and `meg_*` features, alongside 3D and 9D chart exports. Concordance is evaluated on the matched feature surfaces, not interpreted as direct access to a latent neural state.]

$ r_i = "corr"(E E G_i(t), M E G_i(t)) $ <eq:concordance>

[For participant-run $i$ and one matched feature family, $r_i$ is Pearson or Spearman temporal concordance. Run-level correlations are Fisher-transformed before participant-level aggregation. Subject-level paired mean differences are EEG minus MEG and use paired Cohen's $d_z$.]

= Methods <sec:methods>

== Dataset

[The analysis reads 108 participant-run H5 exports from `neuralmanifolddynamics_ds003645_20260722_215042`: 18 healthy adults, six FacePerception recording runs per source subject and paired EEG/MEG feature channels. Empty-room recordings are excluded. All H5 participant mappings label the cohort Healthy.]

== NMD pipeline

[The supplied H5 export is the analytic input. `features_projection_z` is the primary feature surface because the H5 contract records degenerate MEG robust-z power slots. The article-local wrappers call `ndt_analysis` for generic cleaned exports and reachability summaries; they do not reimplement core manifold estimation.]

== Primary endpoints

[The primary endpoints are paired EEG--MEG feature-family temporal correlation and participant-aggregated feature mean differences. Global feature families exclude `__g_*` suffixes. Regional feature families are paired by six shared labels: left/right, anterior/posterior, and midline. MEG regional MNPS and reachability remain supplementary context.]

== Statistical design

[The inferential unit is participant. Run-level values are averaged within participant. Two-sided Wilcoxon signed-rank tests and 5,000 sign-flip permutations test paired mean differences; Cohen's $d_z$ describes their magnitude. Benjamini--Hochberg correction is applied separately to global and regional feature families.]

== Robustness protocol

[QC verifies coverage, finite global charts, source-modality flags, regional feature availability, and equality of regional MNPS trajectories. The full paired participant set is retained for every reported matched feature family. The permutation test is an independent test of the signed paired mean difference.]

= Results <sec:results>

== R1: Data quality and coverage <sec:r1>

[All 108 participant-run H5 files had finite global 3D and 9D values (median 244 time points) and mapped to Healthy. The key QC finding is structural: the six EEG `regional_mnps/*/mnps` trajectories were identical within every run, whereas MEG regional trajectories were not. The regional EEG chart output is therefore not used as independent topology-specific evidence.]

== R2: Global feature-level concordance <sec:r2>

[Matched global EEG and MEG feature time courses showed feature-dependent temporal concordance. Mean-level agreement was not complete: alpha/theta ($d_z = 1.28$, permutation $q = 0.0024$), high-frequency power ($d_z = 1.10$, $q = 0.0024$), sample entropy ($d_z = 0.68$, $q = 0.014$), and theta ($d_z = -0.73$, $q = 0.014$) differed after global-family FDR correction.]

== R3: Regional feature-level concordance and divergence <sec:r3>

[Regional feature-level comparisons retain the paired topographic structure because `__g_eeg_*` and `__g_meg_*` feature columns vary by location. Figure @fig-regional shows topology- and feature-specific temporal concordance and effect sizes. These results are feature-level, not symmetric regional MNPS evidence.]

#figure(
  image("figures/fig1_regional_eeg_meg_concordance.png", width: 100%),
  caption: [Regional EEG--MEG feature concordance (left) and paired feature-mean differences (right). Effects are participant-level EEG minus MEG Cohen's $d_z$.]
) <fig-regional>

== R4: Robustness and confound audit <sec:r4>

[The concordance and paired tests use the same 18-subject intersection. The sign-flip results agree closely with Wilcoxon results for globally FDR-significant feature families. Regional reachability is generated only for non-collapsed MEG regional trajectories; EEG reachability is intentionally skipped.]

= Discussion <sec:discussion>

== Primary finding

[Simultaneous EEG and MEG show heterogeneous temporal alignment in matched feature surfaces while retaining stable between-modality mean offsets. The findings establish a feature-level comparison framework, not equivalence of all measurement scales or latent biological generators.]

== Limitations

[The global MNPS trajectory is MEG-primary shadow mapping and cannot serve as an independent EEG global chart. The identical EEG regional MNPS exports prevent a symmetric regional MNPS or regional reachability comparison. Feature-level results also remain specific to this healthy FacePerception cohort and its export contract.]

== Conclusion

[The ds003645 H5 exports support a reproducible healthy paired EEG--MEG feature-concordance analysis. They also identify a concrete export defect that must be addressed before claims about modality agreement of regional manifold geometry.]

= Acknowledgements

[We acknowledge the ds003645 dataset contributors and the NeuralManifoldDynamics/ndt-analysis developers.]

#bibliography("references.bib", style: "apa")
