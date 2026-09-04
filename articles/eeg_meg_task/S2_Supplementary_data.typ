#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "S2 Data - MEEG concordance",
  subtitle: "Complete matched EEG--MEG feature concordance and difference tables",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S2.0 Complete global coordinate contrast table

[The global MNPS export is MEG-primary shadow mapping and is not tested as a modality contrast. The full MEG-primary summary is `results/eeg_meg_ds003645_20260723/02_modality_tables/global_meg_primary_mnps_summary.csv`.]

= S2.1 Complete paired feature contrast table

[The complete participant-level matched mean tests, including Wilcoxon and 5,000-permutation $p$ values, $d_z$, and separate global/regional FDR $q$ values, are written to `results/eeg_meg_ds003645_20260723/03_concordance/paired_feature_difference_tests.csv`.]

= S2.2 Complete temporal-concordance table

[Run-level and Fisher-aggregated participant-level Pearson and Spearman correlations are written to `run_level_feature_correlations.csv` and `subject_level_feature_concordance.csv` in the same result directory.]

= S2.3 Regional MNPS audit

[The raw regional MNPS summary and the paired audit table are written under `02_modality_tables/`. The EEG entries are retained for audit transparency but must not be interpreted as six independent regional trajectories.]

#bibliography("references.bib", style: "apa")
