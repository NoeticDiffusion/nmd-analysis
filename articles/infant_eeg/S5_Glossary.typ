#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S5 - Glossary",
  short-title: "S5 Infant EEG glossary",
  subtitle: "Operational terms used in this reanalysis",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("glossary", "infant EEG", "MNPS", "MNJ", "reachability", "GEE"),
  article-type: "Supplement",
)

#set heading(numbering: none)

= Terms

*MNPS (Meta-Noetic Pattern Space).* The exported feature chart used as input to downstream summaries: a 3D or 9D coordinate built from spectral/connectivity-like features of an EEG epoch. It is an operational representation of processed EEG, not a demonstrated latent neural state or observed brain state.

*Cohort-anchored coordinate.* An MNPS coordinate expressed relative to the frozen, subject-balanced global IQR anchor `figshare_infant_eeg_global_cohort_all_visits_iqr_v2_1` (anchor hash `45bbfa21...c301a89e`), which places every child's recordings on the same common numeric scale. This is what makes cross-child, cross-visit comparison meaningful in this dataset; it is a pipeline-internal reference scale, not an independent normative or held-out developmental reference (S3.2).

*Subject-anchored coordinate.* The same MNPS construction, but normalized relative to a subject's own reference instead of the cohort. Useful for within-child description; not comparable in absolute level across children.

*3D coordinate family (m, d, e).* The three primary MNPS coordinates, referred to informally in the main text as: *mobility* ($m$, how much the state moves), *deviation* ($d$, how far it strays from a typical/central pattern), and the *entropy-related coordinate* ($e$, how unpredictable/disordered the trajectory pattern is).

*9D coordinate family.* A more detailed, nine-coordinate version of the same three ideas, splitting each of $m$, $d$, $e$ into three further sub-facets. The codes used throughout the manuscript and supplements are versioned operational labels from the upstream export contract, not biological names:
- $m_a$ - attentional mobility component; $m_e$ - affective mobility component; $m_o$ - oscillatory-flexibility mobility component.
- $d_n$ - network-diffusivity deviation component; $d_l$ - local-coupling deviation component; $d_s$ - representational-dispersion deviation component.
- $e_e$ - efficiency-related entropy component; $e_s$ - state-related entropy component; $e_m$ - meta-entropy component.
This document reports which 9D codes are strongest/weakest per analysis (e.g., 9D $m_o$ is the single strongest cohort-coordinate result; 9D $d_s$ the weakest); it does not itself re-derive the exact per-code feature formula, which is versioned in the upstream pipeline export contract rather than this article.

*MNJ (Meta-Noetic Jacobian).* The local derivative $J(x,t) = partial f/partial x$ of the fitted MNPS chart flow, estimated from short windows of epoch-to-epoch transitions. This analysis summarizes its Frobenius norm, trace, antisymmetric rotation norm, and spectral radius per session (3D primary family) and, as a secondary sensitivity family, the same summaries in the 9D chart.

*Reachability.* A local, model-based short-horizon description of the variation reachable from a chart location, derived from the local linear (ridge-regression) flow model at that location. Summarized here by covariance log-volume, effective dimension, anisotropy/condition-number-like measures, directional entropy, and a rotation proxy.

*Within-child (session-level) reachability.* Each visit's reachability estimate computed using only that same session's own epoch-to-epoch transitions as neighbors (S1.2, S1.3) — a trajectory of independent, single-session local-flow estimates, not a pooled or cross-visit estimate.

*Cohort-pooled reachability.* A distinct, genuinely cohort-level reachability estimate: at each visit's own cohort-anchored coordinate, the local flow model is fit from the $k=12$ nearest epoch-to-epoch transitions drawn from every *other* child's epochs (leave-one-child-out), never from the visit's own child (S1.7). This is a different estimand from within-child reachability, not simply a larger-sample version of it.

*GEE (Generalized Estimating Equations).* The regression framework used for the primary cohort-coordinate family: a Gaussian GEE with exchangeable child-clustering and a 3-df cubic B-spline of age, one model per endpoint, testing the omnibus spline term with a Wald chi-squared statistic.

*Within/between-child decomposition.* A diagnostic refit of the primary GEE that replaces the raw age spline with a linear child-mean ("between-child") age term plus a cubic spline of centered ("within-child") age, so that cross-sectional (between-child) and longitudinal (within-child) age association can be tested separately in the same model (S1.6, M3).

*Child-cluster row-permutation check.* A finite-sample-robust robustness check of the same omnibus GEE Wald statistic: age values are permuted across all visit-rows (breaking the age-outcome association while preserving clustering and sample size), the identical GEE is refit, and this is repeated 500 times per endpoint to build a permutation null distribution (S1.6, M4). Used specifically because 22 child clusters is a known regime for anti-conservative GEE sandwich-covariance inference.

*BH-FDR (Benjamini-Hochberg false discovery rate).* The multiple-comparison correction applied across the 12-endpoint cohort-coordinate family, and separately across each robustness family's own endpoints, following @benjamini1995fdr. FDR correction of the 12 cluster-permutation p-values is a distinct, second application of BH-FDR from the primary family's own correction, since the two answer different questions (asymptotic vs. finite-sample-robust significance).

*Direct-age (spreadsheet-direct) sensitivity.* A restriction of any given family to only those visits whose age value was recorded directly in the source spreadsheet, rather than derived from first-visit age plus recording date, used as a robustness check on age-metadata quality (S1.5).

*Nominal vs. FDR-supported.* "Nominal" (or "raw p") refers to an uncorrected p-value below the conventional 0.05 threshold; "FDR-supported" means the same endpoint remains significant after Benjamini-Hochberg correction across its family. An endpoint can be nominal without being FDR-supported, and this distinction is load-bearing throughout this article's robustness reporting (e.g., Results R5, S2.8, S3.4).

*Conventional-EEG (qEEG) comparator family.* A separate, purely descriptive 34-endpoint family (Results R6, S1.8, S2.10-S2.12) of classical quantitative-EEG measures -- relative band power, band-power ratios, spectral peak/edge frequencies, entropy/complexity, and inter-channel coherence -- extracted from the same artifact-masked epochs and tested with the identical estimators used for the primary cohort-coordinate and local-dynamics families. It exists to check whether well-established, non-MNPS EEG maturation signal is detectable in this cohort, not to replace or be pooled with any other family in this article.

*Tier1 / complexity / connectivity packs.* The three upstream ingest-pipeline comparator packs that together produce the 34 `eeg_conventional_*` columns: `tier1` (relative band power, band ratios, spectral peak/edge frequencies), `complexity` (permutation entropy, spectral entropy, Hjorth complexity), and `connectivity` (alpha/theta inter-channel coherence at four electrode pairs).

*Exploratory analysis.* A result-generating analysis reported for transparency and robustness triangulation, not treated as a standalone confirmatory claim. All local-dynamics families (within-child and cohort-pooled) and all sensitivity subsets in this article are exploratory in this sense.

#bibliography("references.bib", style: "apa")
