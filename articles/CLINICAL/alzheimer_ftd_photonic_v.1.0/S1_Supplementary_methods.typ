// S1 Supplementary Methods — generic template.
// Rename and replace placeholders per article.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "S1 Methods - [short article tag]",
  subtitle: "Measurement contract, primary metric computation, auxiliary extraction, and the robustness/confound audit protocol",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S1.0 Dataset and measurement contract

[Placeholder. Describe the dataset (source, DOI, license), sample size and any version-specific discrepancies, the within-subject conditions, recording hardware and sampling rates, and the NMD run identifier. State that analyses should be read against the NMD measurement contract rather than as direct computations on raw tables.]

= S1.1 Epoch structure and feature export

[Placeholder. Describe the epoch window and step, and list the per-epoch features exported by the pipeline (coordinates, Jacobian tensor, physiological indices, regional summaries, block-level summaries).]

= S1.2 Primary metric definitions

[Placeholder. Give the exact formulas for every primary/secondary metric computed from the raw tensor. For each metric, state what it measures and the direction of interpretation.]

$ J(t) = nabla_X [-nabla F(X_t, t)] $ <eq:mnj>

= S1.3 Auxiliary feature extraction

[Placeholder. Describe any standalone extraction script (e.g. for EDA/EMG) not produced by the main pipeline: column source, downsampling, decomposition method, quality gates.]

= S1.4 Physiological confound and secondary feature definitions

[Placeholder. Define every physiological / temporal-structure confound candidate and every secondary-analysis feature (anchor indices, HRV metrics, etc.).]

= S1.5 Statistical design

[Placeholder. Specify session-level aggregation, the contrast test, the effect-size measure, the multiple-comparison family and correction, and the $alpha$ threshold.]

= S1.6 Robustness and confound audit protocol

[Placeholder. List the robustness/confound audit parts with their numbering, matching the main-text Methods and R4. Typical parts: (1) intersection sample, (2) epoch-count matching, (3) LOOSO, (4) bootstrap CIs, (5) within-subject permutation, (6) artifact balance, (7) physiological confounds, (8) additional confound checks, (9) conventional-feature baseline, (10) event/response-rate sensitivity.]

= S1.7 Secondary analysis

[Placeholder. Describe the secondary/exploratory analysis plan (e.g. EAP partial-correlation family), the test family size, and the correction applied.]

#bibliography("references.bib", style: "apa")
