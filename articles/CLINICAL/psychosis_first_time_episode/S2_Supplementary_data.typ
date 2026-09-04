#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "Psychosis Supplementary Data",
  subtitle: "Subgroup tables, pooled sensitivity, baseline comparators, and phenotype summaries",
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

This supplement collects the data-heavy material moved out of the main psychosis manuscript:

- subgroup composition and medication split,
- compact primary contrast anchors,
- pooled `Healthy vs FEP` sensitivity tables,
- reachability sensitivity summaries,
- reviewer-facing baseline-comparator anchors,
- and exploratory clinical-phenotype summaries.

= Subgroup composition

#figure(
  kind: table,
  table(
    columns: (1.0fr, 1.35fr, 0.7fr, 0.85fr, 0.85fr, 1.0fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Dataset*],
      [*Group*],
      [*N*],
      [*Age mean*],
      [*Age SD*],
      [*Female n (%)*],
      [*CPZ median*],
    ),
    [ds003944], [Healthy], [32], [21.61], [3.97], [12 (37.5%)], [--],
    [ds003944], [FEP unmedicated], [19], [22.33], [4.21], [5 (26.3%)], [`0 / n.a.`],
    [ds003944], [FEP medicated], [31], [22.34], [5.41], [11 (35.5%)], [`227.3`],
    [ds003947], [Healthy], [30], [24.20], [5.13], [14 (46.7%)], [--],
    [ds003947], [FEP unmedicated], [8], [25.01], [5.06], [2 (25.0%)], [`0 / n.a.`],
    [ds003947], [FEP medicated], [23], [22.82], [4.57], [7 (30.4%)], [`303.0`],
  ),
  caption: [Article-facing subgroup table reconstructed from participant and medication metadata. Medicated CPZ medians are chlorpromazine-equivalent summaries for the subgroup-defining `CPZ_at_scan` export.]
) <tab-s2-subgroups>

= Compact primary anchors

#figure(
  kind: table,
  table(
    columns: (1.0fr, 1.45fr, 1.55fr, 0.75fr, 0.75fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Dataset*],
      [*Contrast*],
      [*Anchor*],
      [*`d`*],
      [*`p`*],
      [*`q`*],
    ),
    [ds003944], [FEP medicated vs Healthy], [`3D MNPS m_mean`], [0.881], [0.0035], [0.0157],
    [ds003944], [FEP medicated vs Healthy], [`9D MNPS m_o_mean`], [0.814], [0.0020], [0.0270],
    [ds003944], [FEP medicated vs FEP unmedicated], [`3D MNPS m_std`], [0.972], [0.0020], [0.0180],
    [ds003944], [FEP unmedicated vs Healthy], [`Trajectory m_delta_mean_median`], [-0.715], [0.0120], [0.2399],
    [ds003947], [FEP unmedicated vs Healthy], [`Trajectory m_delta_mean_median`], [-1.385], [0.0020], [0.0400],
    [ds003947], [FEP medicated vs Healthy], [`9D MNPS d_l_median`], [0.815], [0.0050], [0.0742],
    [ds003947], [FEP medicated vs Healthy], [`9D MNJ mdr_mean`], [0.789], [0.0050], [0.0950],
  ),
  caption: [Compact article-facing anchors showing that `ds003944` is more location-dominated while `ds003947` is led by an unmedicated trajectory effect.]
) <tab-s2-primary>

= Pooled `Healthy vs FEP` sensitivity

#figure(
  kind: table,
  table(
    columns: (1.0fr, 1.4fr, 0.75fr, 0.75fr, 0.75fr, 1.8fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Dataset*],
      [*Block / feature*],
      [*`d`*],
      [*`p`*],
      [*`q`*],
      [*Interpretation*],
    ),
    [ds003944], [`3D MNPS m_mean`], [0.688], [0.0050], [0.0225], [pooled psychosis signal remains corrected-significant],
    [ds003944], [`9D MNPS m_e_mean`], [0.720], [0.0020], [0.0472], [stratified `m` subfamily also survives pooling],
    [ds003947], [`Trajectory m_delta_mean_median`], [-0.629], [0.0125], [0.2499], [main dynamic effect weakens after pooling],
    [ds003947], [`9D MNJ mdr_mean`], [0.771], [0.0045], [0.0712], [second-order trend remains but misses correction],
  ),
  caption: [Pooled `Healthy vs FEP` sensitivity anchors. The key contrast is between pooling-robust `ds003944` effects and pooling-sensitive `ds003947` dynamics.]
) <tab-s2-pooled>

The pooled pass should be read as a robustness check rather than as the primary inferential view. It confirms a broader psychosis-related signal in `ds003944`, but it dilutes the strongest `ds003947` subgroup-specific dynamic effect.

= Reachability sensitivity

#figure(
  kind: table,
  table(
    columns: (1.0fr, 0.9fr, 1.55fr, 1.35fr, 0.7fr, 1.25fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Dataset*],
      [*View*],
      [*Contrast*],
      [*Reachability feature*],
      [*`d`*],
      [*`p / q`*],
    ),
    [ds003944], [stratified], [FEP medicated vs Healthy], [`tube_capture_gate_median`], [0.765], [`0.0045 / 0.115`],
    [ds003944], [stratified], [FEP unmedicated vs Healthy], [`tube_q_ratio_h4_mean`], [-0.741], [`0.0115 / 0.471`],
    [ds003944], [pooled], [Healthy vs FEP], [`tube_capture_gate_median`], [0.685], [`0.0021 / 0.0606`],
    [ds003944], [pooled], [Healthy vs FEP], [`tube_q_ratio_h4_mean`], [-0.728], [`0.0036 / 0.0606`],
    [ds003947], [stratified], [FEP medicated vs FEP unmedicated], [`persistence_tau_kappa_median`], [1.144], [`0.0060 / 0.456`],
    [ds003947], [stratified], [FEP unmedicated vs Healthy], [`persistence_tau_d_eff_median`], [-1.092], [`0.0190 / 1.000`],
    [ds003947], [pooled], [Healthy vs FEP], [`cone_kappa_mean`], [0.458], [`0.0789 / 0.981`],
  ),
  caption: [Reachability sensitivity summary. `ds003944` shows a coherent pooled family that nearly reaches correction; `ds003947` shows larger isolated subgroup excursions but little stable pooled structure.]
) <tab-s2-reachability>

= Reviewer-facing baseline comparators

#figure(
  kind: table,
  table(
    columns: (1.0fr, 1.4fr, 1.3fr, 1.3fr, 1.25fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Dataset*],
      [*Contrast*],
      [*Best spectral baseline*],
      [*Best complexity baseline*],
      [*Best simple dynamics baseline*],
    ),
    [ds003944], [FEP unmedicated vs Healthy], [`alpha` power (`d = -0.549`, `q = 0.124`)], [permutation entropy (`d = 0.417`)], [speed median (`d = -0.322`)],
    [ds003944], [FEP medicated vs Healthy], [`beta/alpha` (`d = 0.768`, `q = 0.021`)], [Hjorth mobility (`d = 0.307`)], [speed mean (`d = 0.372`)],
    [ds003944], [FEP medicated vs FEP unmedicated], [`beta/alpha` (`d = 0.463`)], [Hjorth complexity (`d = -0.389`)], [speed mean (`d = 0.436`)],
    [ds003947], [FEP unmedicated vs Healthy], [`alpha` power (`d = -0.817`, `q = 0.025`)], [permutation entropy (`d = 0.669`)], [speed mean (`d = 0.360`)],
    [ds003947], [FEP medicated vs Healthy], [`delta` power (`d = -0.539`)], [Hjorth complexity (`d = -0.765`, `q = 0.025`)], [speed mean (`d = 0.364`)],
    [ds003947], [FEP medicated vs FEP unmedicated], [`alpha` power (`d = 0.466`)], [Hjorth complexity (`d = -0.371`)], [curvature median (`d = -0.377`)],
  ),
  caption: [Compact conventional-EEG comparator panel. Simple spectral or complexity baselines recover part of the subgroup separation, but generic speed / curvature baselines do not reproduce the strongest `ds003947` trajectory-level result.]
) <tab-s2-baselines>

= Exploratory phenotype anchors

#figure(
  kind: table,
  table(
    columns: (1.0fr, 1.15fr, 1.35fr, 0.75fr, 0.75fr, 0.75fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Dataset*],
      [*Phenotype split*],
      [*Block / feature*],
      [*`d`*],
      [*`p`*],
      [*`q`*],
    ),
    [ds003944], [`SAPS_Q7` high vs low], [`3D MNPS e_median`], [0.897], [0.0080], [0.0454],
    [ds003944], [`BPRST19` high vs low], [`3D MNPS m_mean`], [0.815], [0.0075], [0.0355],
    [ds003944], [`BPRST19` high vs low], [`9D MNPS e_m_mean`], [-0.940], [0.0019], [0.0251],
    [ds003944], [`BPRST19` high vs low], [`Block-MNJ c_rot_mean`], [0.482], [0.0001], [0.0004],
    [ds003947], [`SAPS_Q7` high vs low], [`9D MNPS d_s_std`], [0.891], [0.0504], [0.8686],
    [ds003947], [`BPRST19` high vs low], [`Block-MNJ c_rot_mean`], [0.476], [0.0015], [0.0076],
  ),
  caption: [Exploratory FEP-only phenotype anchors. These rows add clinical texture, but they are not part of the paper's primary inferential claim set.]
) <tab-s2-phenotypes>

The phenotype rows are intentionally retained as exploratory. The most interpretable pattern is that `ds003944` symptom burden expresses itself through both first-order displacement and block-coupling structure, whereas `ds003947` provides only selective support.

= Files

The tables in this supplement are backed by the psychosis article outputs under `articles/CLINICAL/psychosis_first_time_episode/results/`, especially:

- `demography_summary.csv`
- `psychosis_metric_family_detail.csv`
- `pooled_fep_reachability_summary.md`
- `psychosis_baseline_comparator_summary.csv`
- `clinical_phenotype_summary.csv`
- `clinical_phenotype_detail.csv`

#bibliography("psychosis.bib", style: "apa")
