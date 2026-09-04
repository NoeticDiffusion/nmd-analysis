#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "S1 Methods - MEEG concordance",
  subtitle: "Measurement contract and paired EEG--MEG feature analysis",
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

[This report uses the healthy simultaneous-MEEG FacePerception H5 release `neuralmanifolddynamics_ds003645_20260722_215042`. Participant H5 files are parsed by subject and run, with empty-room files excluded. The analysis reads the H5 measurement contract and does not redo sensor preprocessing.]

= S1.1 Epoch structure and feature export

[Each H5 exports `features_raw`, `features_robust_z`, and `features_projection_z`; the last is used for paired features because the H5 metadata documents degenerate robust-z MEG power slots. Exports also include `mnps_3d`, `coords_9d`, Jacobian layers, source flags, and twelve regional MNPS groups.]

= S1.2 Primary metric definitions

[For a matched EEG/MEG feature family, temporal agreement is Pearson or Spearman correlation over valid concurrent time points. Run correlations are Fisher-transformed and averaged within participant. Mean-level difference is EEG mean minus MEG mean; its paired standardized effect is $d_z$.]

$ r_i = "corr"(E E G_i(t), M E G_i(t)) $ <eq:concordance>

= S1.3 Statistical design

[Participant is the inference unit. Run means are averaged within participant. We use two-sided Wilcoxon signed-rank tests and 5,000 sign-flip permutations, with Benjamini--Hochberg FDR correction separately over global and regional feature families.]

= S1.4 Regional geometry safeguard

[The six EEG regional MNPS arrays are numerically equivalent within each run, so they cannot estimate regional heterogeneity. Regional paired inference instead uses varying `__g_eeg_*` and `__g_meg_*` feature columns. The reachability wrapper reports MEG regional reachability only and records each skipped collapsed EEG run.]

#bibliography("references.bib", style: "apa")
