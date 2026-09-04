#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness - Evoked Structural Brittleness Under Photic Stimulation in Alzheimer Disease and Frontotemporal Dementia",
  short-title: "ESB Supplementary QC",
  subtitle: "Leave-one-out, permutation, frequency audit, and comparator caveats",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope

This supplement collects the robustness material intentionally compressed in the main ESB paper:

- leave-one-out Healthy-template stability,
- permutation support for the headline row,
- recovery-subset sensitivity,
- the frequency-only audit,
- and the main comparator / interpretation caveats.

= Leave-one-out template stability

#figure(
  kind: table,
  table(
    columns: (1.6fr, 1.25fr, 1.0fr, 1.0fr, 1.0fr),
    align: (left, left, center, center, center),
    inset: 5pt,
    table.header(
      [*Score*],
      [*Contrast*],
      [*Median `d`*],
      [*Min `d`*],
      [*Max `d`*],
    ),
    [ESB-2 leave-one-out], [AD vs Healthy], [0.818], [0.793], [0.843],
    [ESB-2 leave-one-out], [FTD vs Healthy], [1.013], [0.925], [1.091],
    [PRL leave-one-out], [AD vs Healthy], [-0.295], [-0.513], [0.028],
    [PRL leave-one-out], [FTD vs Healthy], [-0.435], [-0.568], [-0.170],
  ),
  caption: [Leave-one-out Healthy-template sensitivity from `qc_leave_one_out_esb2.csv` and `qc_leave_one_out_prl.csv`. ESB-2 remains stable, whereas PRL stays negative and unstable.]
) <tab-s3-loo>

= Permutation and recovery-subset checks

#figure(
  kind: table,
  table(
    columns: (1.65fr, 1.25fr, 0.95fr, 0.95fr, 1.4fr),
    align: (left, left, center, center, left),
    inset: 5pt,
    table.header(
      [*Check*],
      [*Contrast*],
      [*Observed `d`*],
      [*Empirical `p`*],
      [*Interpretation*],
    ),
    [Permutation], [AD vs Healthy at PHOTO 15 Hz], [0.821], [0.0015], [The headline AD row remains well below the permutation null.],
    [Permutation], [FTD vs Healthy at PHOTO 15 Hz], [1.038], [0], [No exceedance in `2000` draws on the headline FTD row.],
    [Recovery subset], [AD vs Healthy at PHOTO 15 Hz], [0.561], [0.0765], [Recovery-restricted subset weakens the row materially.],
    [Recovery subset], [FTD vs Healthy at PHOTO 15 Hz], [0.652], [0.1101], [The same weakening is present for FTD.],
  ),
  caption: [Permutation and recovery-subset summary from `qc_permutation_tests.csv` and `qc_recovery_subset_stability.csv`.]
) <tab-s3-perm-recovery>

These checks motivate the article boundary:

1. the main ESB-2 claim does not depend on the recovery-restricted subset,
2. the recovery-weighted branch is therefore kept secondary,
3. the permutation support strengthens the headline `PHOTO 15 Hz` row despite the development-stage metric status.

= Frequency-only audit

#figure(
  kind: table,
  table(
    columns: (1.35fr, 1.0fr, 0.9fr, 0.8fr, 0.8fr, 0.8fr),
    align: (left, left, center, center, center, center),
    inset: 5pt,
    table.header(
      [*Contrast*],
      [*Frequency*],
      [*Left n*],
      [*Right n*],
      [*`d`*],
      [*Frequency `q`*],
    ),
    [AD vs Healthy], [PHOTO 5 Hz], [33], [25], [0.472], [0.0615],
    [AD vs Healthy], [PHOTO 10 Hz], [34], [27], [0.493], [0.0615],
    [AD vs Healthy], [PHOTO 15 Hz], [34], [27], [0.821], [0.0125],
    [FTD vs Healthy], [PHOTO 5 Hz], [22], [25], [0.692], [0.0276],
    [FTD vs Healthy], [PHOTO 10 Hz], [22], [27], [0.760], [0.0276],
    [FTD vs Healthy], [PHOTO 15 Hz], [22], [27], [1.038], [0.0054],
  ),
  caption: [Frequency-only BH audit for the primary ESB-2 specification from `qc_frequency_peak_audit.csv`. `PHOTO 15 Hz` is the strongest shared peak, but the `FTD` branch remains positive at `PHOTO 5` and `PHOTO 10 Hz` as well.]
) <tab-s3-frequency-audit>

= Comparator caveats

The comparator panel improves interpretability, but it does not collapse the ESB-2 signal.

The strongest all-subject ESB-comparator correlation at `PHOTO 15 Hz` is only:

- posterior alpha power, `rho = 0.182`, `q = 0.241`

On the disease-only subset, the strongest absolute correlation is:

- posterior alpha/theta ratio, `rho = 0.228`, `q = 0.366`

This means:

1. conventional posterior alpha-linked change overlaps with ESB-2,
2. but the overlap is modest,
3. and it weakens rather than strengthens once Healthy subjects are removed.

= Review-facing caution points

1. The primary comparison still uses a resting, eyes-closed ds004504 anchor against an eyes-open evoked ds006036 surface.
2. The headline ESB-2 specification was selected from exploratory work before the article-local rerun.
3. The frozen primary surface retains `86` matched subjects rather than all `88` photic participants.
4. The planned global-capacity branch did not yield analyzable primary-stage contrasts.
5. PRL was tested over only four frequencies and remained negative.
6. Direct narrowband stimulation-frequency SSVEP amplitude was not available on the frozen comparator contract.
7. Coverage drops at `PHOTO 20 Hz`, especially in `FTD` and the matched Healthy subset.

= Files

The robustness claims in this supplement are backed mainly by:

- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/qc_leave_one_out_esb2.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/qc_leave_one_out_prl.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/qc_permutation_tests.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/qc_recovery_subset_stability.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/qc_frequency_peak_audit.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/conventional_comparator_summary.md`
- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/conventional_comparator_esb2_correlations.csv`
- `articles/CLINICAL/alzheimer_ftd_photonic_esb/results/negative_results_summary.csv`


#bibliography("alzheimer_ftd_reference_list.bib", title: [References])