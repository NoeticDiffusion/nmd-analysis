#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "S3 QC - MEEG concordance",
  subtitle: "H5 coverage, modality-source checks, and regional MNPS audit",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S3.0 Sample and epoch coverage overview

[The audit found 108 participant-run H5 files from 18 Healthy participants. All global 3D and 9D arrays were finite; median run length was 244 time points. The complete per-run audit is `results/eeg_meg_ds003645_20260723/00_sanity_check/run_coverage_and_regional_audit.csv`.]

= S3.1 Modality source coverage

[All exported windows have both modality-specific feature surfaces available in the paired H5 contract. `row_source` flags make clear that individual rows originate from modality-native source files; paired feature matching is performed on aligned exported time grids, not by declaring every original row a simultaneous sensor sample.]

= S3.2 Regional MNPS collapse

[For every audited run, all six EEG `/regional_mnps/<topology>/mnps` arrays were equal to one another within numerical tolerance. In contrast, no MEG run showed a collapsed six-region set. This is an export limitation rather than biological evidence of EEG regional homogeneity. The article excludes the collapsed EEG regional MNPS arrays from regional geometric and reachability tests.]

= S3.3 Robustness summary

[The same 18 participants contribute to each matched feature test. Temporal correlations use finite concurrent samples; participant means aggregate run-level values. Wilcoxon and sign-flip permutation tests provide two independent paired tests, and BH correction is applied by global versus regional family.]

= S3.5 Reviewer-facing robustness summary

#netn-box(title: [Robustness summary])[
  [The report supports feature-level EEG--MEG concordance and feature-mean differences. It does not support a claim of EEG--MEG concordance for regional MNPS geometry until the collapsed EEG export surface is repaired.]
]

#bibliography("references.bib", style: "apa")
