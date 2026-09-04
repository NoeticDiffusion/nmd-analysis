#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Recovery-Linked Neural Geometry After Cardiac-Arrest Coma",
  short-title: "Recovery-Linked Neural Geometry",
  subtitle: "Reachability and Jacobian evidence in early post-arrest EEG",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "cardiac-arrest coma",
    "I-CARE",
    "EEG",
    "reachability",
    "Jacobian",
    "NeuralManifoldDynamics",
    "NeuroComBat",
  ),
  article-type: "Research Article",
  abstract: [
    Early electroencephalography (EEG) after cardiac arrest is typically read for static severity, and it remains unclear whether clinically relevant geometric structure is already present within the first few post-arrest hours, before enough recording time has accumulated for conventional summary features to stabilize. We address this gap directly: rather than pooling across the full `0-12 h` window and reporting only an average effect, we test explicitly whether short-horizon neural geometry already separates later good (`CPC 1`) from poor (`CPC 5`) outcome in the earliest analyzable hour. What is new here relative to prior single-cohort work is a layered, two-cohort design: we pooled invalidity-fixed I-CARE exports from two independently processed, non-overlapping cohorts (`301` analyzable patients, `281` in the extreme-outcome contrast) and jointly evaluated short-horizon reachability, local Jacobian deformation (`MNJ 3D` and invalidity-corrected `MNJ 9D`), and between-run temporal stability, so that any early signal must survive pooling and cross-cohort heterogeneity checks rather than resting on one metric in one sample. All five prespecified reachability metrics were BH-FDR significant in the pooled cohort, led by `persistence_hysteresis_log_det_median` (`d = -0.909`) and `persistence_log_det_median` (`d = 0.896`), with `MNJ 3D`/`MNJ 9D` directionally aligned but cohort-heterogeneous in magnitude. The lead reachability separator, `tube_d_eff_median`, was already significant in the very first analyzable hour (`0-1 h`: `d = 0.786`, `p = 1.2e-04`) and stayed positive across all `12` hourly bins, supporting early presence of the geometric signal; this should be read narrowly, however, because a subject-wise circular-shift null did not support a precise claim about which hour shows the strongest separation, so the safe reading is "detectable early," not "sharply localized in time." Between-run instability in the subset with `≥3` qualifying recordings (`n = 130`) added a further, complementary axis of separation. Adding the five-metric geometry layer to a feature-limited (`limited_clinical_only`) baseline raised internal AUROC from `0.599` to `0.662`, a bounded increment that should not be read as outperforming full multimodal clinical prognostication. Because WLST, time-to-death, and sedation annotations were unavailable, the `CPC 1` versus `CPC 5` contrast should be interpreted as recovery-linked geometry rather than as a pure assay of neural viability.
  ],
  author-summary: [
    After cardiac arrest, doctors currently have very little to go on in the first hours of EEG monitoring beyond how severe the recording looks at a glance. This article asks a more specific question: is there already a measurable difference in the underlying short-horizon dynamics of the EEG — not just its severity level — between patients who go on to recover well and those who do not, and is that difference present early enough to matter? Using two independently processed cardiac-arrest EEG cohorts pooled together, we find that the answer is yes on both counts. Patients with later good outcome showed broader and more stable short-horizon "reachability" (how much nearby future brain-state movement remains possible) and lower local instability (how sharply nearby states pull apart), and this separation was already present in the very first analyzable hour rather than only emerging later. We are careful, however, not to overstate the timing claim: while the signal is clearly present early, our data do not let us pin down one specific hour as uniquely decisive. Adding this geometric information to the limited clinical and EEG variables available in our dataset modestly improved outcome prediction, but that comparison is against a feature-poor baseline, not against the fuller information a treating team has in practice, so this remains a research finding about early recovery-linked brain dynamics rather than a ready-to-use bedside tool.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted in the submission version.],
  data-availability: [All result bundles backing the tables and figures in this article are available under `articles/CLINICAL/comatose_ndt/results/` with the date tag `20260606_combined_invalidityfix`. A frozen manuscript release for this article line is archived on Zenodo.@langell2026_coma_v011 The underlying I-CARE dataset is available through PhysioNet version `2.1`, and the processing framework is available via `https://github.com/NoeticDiffusion`.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

= Introduction

Cardiac-arrest coma remains a useful test case for geometry-centered EEG analysis because the clinical problem is not only whether the record is slow, discontinuous, or suppressed at one instant. The more dynamical question is whether early neural activity still retains locally reachable structure and whether that structure is accompanied by more or less expansive local linear deformation.@sandroni2021european, @nolan2025postresuscitation, @amorim2023icare

The analysis therefore takes a layered approach: coordinate spread (`MNPS 3D` and `MNPS 9D`), local linear deformation (`MNJ 3D` and `MNJ 9D`), and short-horizon reachability are evaluated jointly in the pooled cohort rather than treating any single family as the sole primary outcome.

This article therefore asks one bounded question: during the first `12 h` after EEG-anchor, do later `CPC 1` and later `CPC 5` patients differ in early geometry, and if so which layers remain most defensible after pooling?

#netn-box(title: [Core question])[
  In harmonized I-CARE bundles, does later good versus poor outcome separate along a layered early geometry story rather than along one isolated metric family?
]

= Cohort and analysis design

The analysis drew from two independently processed cohort roots, `part1` and `part2`, and primary `0-12 h` summaries, rebinned hourly bundles, and the pooled merge were all computed after verifying zero subject overlap and zero run overlap between roots. `part1` contributes `161` analyzable subjects (`71 CPC 1`, `10 CPC 2`, `7 CPC 3`, `3 CPC 4`, `70 CPC 5`) across `3484` H5 runs; `part2` contributes `140` analyzable subjects (`70 CPC 1`, `70 CPC 5`) across `1838` H5 runs. The pooled bundle therefore contains `301` analyzable subjects across `5322` H5 runs, with `281` subjects in the primary extreme-outcome contrast. Full provenance tables and old-vs-new comparison material are moved to `S2`.

#figure(
  kind: table,
  clean-table(
    columns: (2.8fr, 1.45fr, 1.45fr, 1.55fr),
    align: left,
    inset: 5pt,
    table.header([*Bundle item*], [*`part1`*], [*`part2`*], [*Pooled*]),
    [Analyzable subjects], [161], [140], [301],
    [Extreme-outcome `CPC 1 / CPC 5` subset], [141 (`71 / 70`)], [140 (`70 / 70`)], [281 (`141 / 140`)],
    [Intermediate `CPC 2-4` retained outside main contrast], [20], [0], [20],
    [H5 runs in dated bundle], [3484], [1838], [5322],
    [Hospital counts], [A:73, B:30, D:23, E:18, F:17], [A:76, B:18, D:14, E:14, F:18], [A:149, B:48, D:37, E:32, F:35],
    [Bundle overlap audit], [reference bundle], [`0` subjects / `0` runs], [dedup resolved via `prefer_part2`],
  ),
  caption: [Bundle summary for the discovery-side `part1`, the second cohort, and the merged pooled synthesis.]
) <tab-cohort-bundles>

#figure(
  kind: table,
  clean-table(
    columns: (2.45fr, 1.45fr, 1.45fr),
    align: left,
    inset: 5pt,
    table.header([*Pooled cohort item*], [*`CPC 1`*], [*`CPC 5`*]),
    [Patients in analyzed pooled extreme-outcome cohort], [141], [140],
    [Age, mean / median], [59.5 / 59.0], [61.7 / 64.0],
    [Sex], [104 Male / 37 Female], [96 Male / 44 Female],
    [Site], [A:73, B:22, D:20, F:17, E:9], [A:64, B:23, E:22, F:16, D:15],
    [Out-of-hospital / in-hospital / missing], [103 / 27 / 11], [104 / 27 / 9],
    [Shockable / non-shockable / missing], [99 / 33 / 9], [69 / 63 / 8],
    [Targeted temperature management `33 / 36 / missing`], [105 / 15 / 21], [99 / 19 / 22],
    [ROSC minutes, median], [17.0], [20.0],
  ),
  caption: [Pooled `0-12 h` `CPC 1` versus `CPC 5` cohort summary for the main analysis set.]
) <tab-pooled-cohort>

#figure(
  kind: table,
  clean-table(
    columns: (2.8fr, 1.3fr, 1.3fr, 1.8fr),
    align: left,
    inset: 5pt,
    table.header([*Timing / coverage item*], [*`CPC 1`*], [*`CPC 5`*], [*Site audit*]),
    [Recording start after EEG-anchor, mean / median `h`], [`0.011 / 0.000`], [`0.007 / 0.000`], [site means `0.000` to `0.029`],
    [Recording end after EEG-anchor, mean / median `h`], [`11.560 / 12.001`], [`11.559 / 11.977`], [site means `11.413` to `11.920`],
    [Channel coverage fraction, mean / median], [`0.935 / 0.952`], [`0.940 / 0.952`], [site medians `0.905` to `0.952`],
    [ROSC minutes, mean / median], [`21.6 / 17.0`], [`23.6 / 20.0`], [severity covariate, not a monitoring clock],
    [Primary hourly interpretation], [`0_1h` through `11_12h` after anchor], [same], [not a validated post-ROSC phase map],
  ),
  caption: [Main-text timing and coverage audit for the pooled extreme-outcome cohort. The locked export supports anchor-relative timing, not a direct ROSC-to-EEG-anchor clock.]
) <tab-timing-audit>

#figure(
  image("figures/20260606_combined_invalidityfix/fig1_cohort_coverage_overview.svg", width: 100%),
  caption: [Site distribution and timing/coverage overview for the pooled primary cohort.]
) <fig-cohort>

The analysis clock is therefore defined by EEG-anchor, not by ROSC. The locked export preserves ROSC duration as a clinical severity covariate, but not a direct elapsed time from ROSC to EEG-anchor. Accordingly, the `0-12 h` primary window and all hourly bins should be read as anchor-relative measurement windows. Intermediate `CPC 2-4` patients were retained for cohort accounting but were not used for the primary inferential contrast, so ordinal generalization remains unproven.

= Methods

The manuscript pipeline consisted of timeline reconstruction, `mnps_summary` extraction, partwise and pooled outcome contrasts, reviewer-style selection audits, repeated-CV incremental-validity analysis, robustness/QC summaries, horizon sensitivity, early-versus-late distribution diagnostics, and figure generation. The primary analysis window remained `0-12 h` after EEG-anchor, and the primary inferential contract remained the patient-level `CPC 1` versus `CPC 5` comparison.

== NeuralManifoldDynamics primer: `MNPS`, `MNJ`, and reachability

The pooled analysis consumes trajectories exported under the versioned `NeuralManifoldDynamics` (`NMD`) measurement contract rather than fitting chart coordinates inside this manuscript.@langell2026_mndm Every EEG record is summarized as a canonical `3D` chart $x_t = [m_t, d_t, e_t]$ and a stratified `9D` chart built from fixed EEG feature families (full mapping and derivation in `S1`). Three metric families recur throughout the article and are illustrated schematically in @fig-mnj-primer:

- `MNPS` (state-space spread): plain dispersion of the exported `3D`/`9D` coordinates, e.g. `m_std` or `m_e_std`. `MNPS` answers "how spread out is the trajectory," independent of its short-horizon dynamics, and is treated as a restored descriptive anchor rather than a mechanistic claim.
- `MNJ` (local Jacobian): the estimated local linear operator $A_t$ (the local Jacobian $J_t$) governing how nearby trajectory points are pulled together or pushed apart over one step. Higher `MNJ` spectral radius or Frobenius norm indicates stronger local expansion or deformation.
- Reachability (`tube_d_eff`, `persistence_*`, `tube_capture_gate`): properties of the short-horizon forward-reachable set built by propagating local covariance under $A_t$ and $Q_t$ (exact definitions in `S1`). `tube_d_eff_median` summarizes how many effectively independent directions remain reachable; the `persistence_*` metrics summarize how stable that reachable shape stays across neighboring time windows; `tube_capture_gate_median` summarizes whether nearby futures are funneled into a narrow captured region or remain relatively open.

These three families are not interchangeable. `MNPS` is a static spread summary, `MNJ` is a one-step local-deformation summary, and reachability is a multi-step forward-propagated summary that depends jointly on $A_t$ and $Q_t$. A chart can therefore show unremarkable `MNPS` while still differing sharply in `MNJ` or reachability, which is why the article reports all three layers jointly rather than collapsing them into a single index.

#figure(
  grid(
    columns: 2,
    gutter: 8pt,
    image("figures/conceptual_figures/tube_d_eff_median.png", width: 100%),
    image("figures/conceptual_figures/Jacobian_frobenius_norm.png", width: 100%),
  ),
  caption: [Schematic intuition for two of the three recurring metric families. Left: `tube_d_eff_median` — low values indicate short-horizon movement confined to few directions (canalized futures), high values indicate broad, effectively independent reachable directions. Right: Jacobian Frobenius norm $norm(J)_F$ — low values indicate weak local deformation (nearby trajectories stay close and parallel), high values indicate strong local deformation (nearby trajectories are twisted or redirected). Schematic illustrations for methodological intuition only; not derived from I-CARE data. Additional conceptual figures for the persistence and capture-gating families are given in `S1`.]
) <fig-mnj-primer>

The five-feature reachability layer used in the predictive comparison comprises `tube_d_eff_median`, `persistence_log_det_median`, `persistence_log_eig_var_median`, `persistence_hysteresis_log_det_median`, and `tube_capture_gate_median`. Briefly, `tube_d_eff_median` summarizes effective reachable dimensionality, `persistence_log_det_median` tracks stability of reachable-volume scale (log-det) across neighboring windows, `persistence_log_eig_var_median` tracks stability of eigenspectrum spread, `persistence_hysteresis_log_det_median` captures persistence of signed log-det trajectory changes, and `tube_capture_gate_median` summarizes the transport-versus-innovation gating balance in the short-horizon tube. This layer was defined before the pooled outcome contrasts were examined and is treated as an internally validated post-selection set rather than an externally frozen biomarker panel. The Jacobian material is reported as pooled anchors across both `MNJ 3D` and repaired `MNJ 9D`, with explicit cohort-heterogeneity checks and without assuming one Jacobian space should dominate all contrasts. Metric-wise medians and pooled effect sizes are tabulated in `S2`, while full mathematical definitions and processing contracts are moved to `S1`.

A post-hoc between-run temporal variability analysis was conducted for the same five reachability metrics, computing the between-run median absolute deviation (MAD) and interquartile range (IQR) of per-run metric values across each patient's qualifying recordings in the `0-12 h` window. This analysis required at least `3` finite per-run values per patient, yielding a recording-complete subset of `130` subjects (`70 CPC 1` / `60 CPC 5`). MAD results are reported in the main article as a complementary dimension; IQR results are moved to `S2`.

The endpoint should be interpreted as an extreme-outcome association contrast rather than as a neural-viability label. `CPC 5` can absorb mortality-process, systemic illness, treatment-limitation, and site-pathway effects in addition to brain injury severity. Because WLST, time-to-death, and sedation burden are unavailable in the locked export, this analysis cannot separate recovery-linked geometry from those clinical pathway effects and should not be read as an early neuroprognostication study.@rajajee2023neuroprognostication, @sandroni2021european

#netn-box(title: [Upstream processing contract and validation boundary])[
  The analyses did not refit upstream harmonization or invalidity policies inside the manuscript code. Instead, they consumed two already processed H5 export roots as a fixed upstream layer, then ran all contrasts and predictive models on those locked exports. Repeated-CV, leave-one-site-out, and leave-one-subject-out results should therefore be read as internal validation after external preprocessing, not as fold-nested deployment-style preprocessing. The manuscript can audit overlap, coverage, and downstream stability, but it cannot independently reconstruct every upstream processing design matrix from the locked export.
]

Clinical covariates in the predictive ladder come from the timeline metadata layer, whereas the qEEG and geometry blocks are extracted from the same corrected export stack. Statistical summaries emphasize Cohen's `d`, Mann-Whitney tests, and BH-FDR inside the prespecified five-metric reachability family. Predictive analyses use repeated stratified cross-validation plus leave-one-site-out sensitivity under a fixed logistic-regression pipeline, with additional leave-one-subject-out and train-fold-only cross-fitted sensitivity analyses reported in `S3`.

#netn-box(title: [Inferential contract])[
  Primary confirmatory family: the five main-text reachability metrics, with BH-FDR applied inside that family. Secondary anchors: exact main-text `MNPS 3D`, `MNPS 9D`, `MNJ 3D`, and compact `MNJ 9D` rows listed in the pooled anchor table, treated as descriptive anchors rather than as a discovery family. Exploratory material: hourly localization, additional Jacobian rows, subset robustness, and old-vs-new comparisons. No main claim rests on exploratory rows alone unless accompanied by stronger internal support.
]

Full tables, hourly rows, and extended QC/robustness outputs are moved to `S2` and `S3`.

= Results

== Layered primary synthesis

The pooled analysis strengthens the main geometry story rather than collapsing it to a single repaired metric. Better-outcome patients retain broader reachability dimensionality, lower `MNPS` spread, and lower local Jacobian expansion. What changes is the hierarchy among those layers: `tube_d_eff_median` and `persistence_log_eig_var_median` now form a stronger reachability pair, while both `MNJ 3D` and repaired `MNJ 9D` contribute sizable pooled standardized separation.

#figure(
  kind: table,
  clean-table(
    columns: (2.35fr, 1.7fr, 0.95fr, 0.95fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Family / metric*], [*Interpretation*], [*`part1` `d`*], [*`part2` `d`*], [*Pooled `d`*], [*Pooled `p`*]),
    [`MNPS 3D / m_std`], [lower pooled `3D` spread in `CPC 1`], [`-0.249`], [`-0.309`], [`-0.279`], [`0.0296`],
    [`MNPS 9D / m_e_std`], [lower pooled `9D` spread in `CPC 1`], [`-0.270`], [`-0.336`], [`-0.302`], [`0.00153`],
    [`Reachability / tube_d_eff_median`], [broader reachability dimensionality in `CPC 1`], [`+0.780`], [`+1.003`], [`+0.838`], [`9.24e-06`],
    [`MNJ 3D / spectral_radius_median`], [lower dominant local expansion in `CPC 1`], [`-0.461`], [`-0.642`], [`-0.521`], [`7.31e-08`],
    [`MNJ 3D / frobenius_norm_median`], [lower overall local deformation in `CPC 1`], [`-0.581`], [`-0.422`], [`-0.499`], [`1.85e-07`],
    [`MNJ 9D / spectral_radius_median`], [lower repaired `9D` expansion in `CPC 1`], [`-0.777`], [`-0.400`], [`-0.603`], [`4.90e-07`],
    [`MNJ 9D / frobenius_norm_median`], [lower repaired `9D` deformation scale in `CPC 1`], [`-0.886`], [`-0.317`], [`-0.592`], [`1.72e-06`],
  ),
  caption: [Compact primary anchors across the main geometry families. Positive Cohen's `d` indicates higher values in `CPC 1`; negative values indicate higher values in `CPC 5`.]
) <tab-layered-primary>

The pooled interpretation is therefore more specific than a single-family reading: later recovery is associated with broader chart-level short-horizon reachability dimensionality, stronger persistence log-eigenvalue separation, lower local Jacobian expansion, and lower total local deformation. The invalidity-corrected `MNJ 9D` layer is not only directionally stable but also sizable in pooled standardized magnitude, although its strongest effect sizes occur in `part1` rather than `part2`, highlighting cohort heterogeneity rather than a single-cohort dependency.

== Reachability family and hourly localization

Within the five main-text reachability summaries, all five are BH-FDR positive in the pooled cohort. `tube_d_eff_median` is the lead effective-dimensionality separator (`d = 0.838`, `q = 1.54e-05`), `persistence_log_eig_var_median` provides a strong companion reachability anchor (`d = 0.736`, `q = 6.63e-05`), `persistence_log_det_median` contributes a strong tube-volume separator (`d = 0.896`, `q = 3.73e-06`), `persistence_hysteresis_log_det_median` adds a persistent tube-dynamics anchor (`d = -0.909`, `q = 5.70e-07`), and `tube_capture_gate_median` completes the family (`d = -0.558`, `q = 8.04e-03`). The full reachability table is moved to `S2`, and robustness/QC context to `S3`.

#figure(
  image("figures/20260606_combined_invalidityfix/fig2_primary_reachability_panel.svg", width: 100%),
  caption: [Pooled effect-size panel for the five main-text reachability metrics.]
) <fig-primary-reachability>

The hourly map remains useful as exploratory localization rather than as a null-defeating peak-timing result. For `tube_d_eff_median`, outcome separation is already visible in `0_1h` (`d = 0.786`, `p = 1.22e-04`), remains positive across all hourly bins (`d = 0.740` to `0.950`), and peaks at `2_3h` (`d = 0.950`, with `3_4h` nearly identical at `d = 0.950`). `tube_capture_gate_median` stays negative across the same window (`d = -0.399` to `-0.711`), peaking at `3_4h`. The Jacobian layers localize similarly even though their full hourly tables are moved to `S2`: `MNJ 3D spectral_radius_median` peaks at `3_4h` (`d = -0.657`) and `MNJ 9D spectral_radius_median` peaks at `2_3h` (`d = -0.849`). However, a subject-wise circular-shift null in `S3` did not show these observed hourly peak `|d|` values to be clearly above shifted-anchor maxima (`tube_d_eff_median empirical p = 0.947`; `tube_capture_gate_median empirical p = 0.836`; `MNJ 3D empirical p = 0.312`; `MNJ 9D empirical p = 0.765`). The safer reading is therefore broad early structure with descriptive localization, not a robust claim of precise peak timing.

#figure(
  image("figures/20260606_combined_invalidityfix/fig3_hourly_reachability_core_heatmap.svg", width: 100%),
  caption: [Exploratory hourly reachability effect-size map across `0_1h` through `11_12h`.]
) <fig-hourly>

== Between-run temporal variability

In the recording-complete subset (subjects with ≥`3` qualifying runs in `0-12 h`; `n = 130`, `70 CPC 1` / `60 CPC 5`), between-run temporal variability showed a complementary and in one case stronger dimension than central tendency. The between-run MAD of `tube_capture_gate_median` was the strongest discriminator in this analysis (`d = -1.033`, `p = 3.79e-06`), exceeding its own central tendency in the same recording-complete subset (`d = -0.484`). The between-run MAD of `persistence_hysteresis_log_det_median` also showed significant separation (`d = -0.687`, `p = 1.92e-05`), alongside its central-tendency signal (`d = -0.921`). In both cases the negative sign indicates that CPC5 subjects exhibited greater within-patient geometric fluctuation across recording sessions, pointing to reduced attractor stability rather than a uniformly shifted trajectory level.

#figure(
  kind: table,
  clean-table(
    columns: (2.55fr, 1.0fr, 1.0fr, 0.9fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric (MAD)*], [*`CPC 1` med*], [*`CPC 5` med*], [*Cohen's `d`*], [*M-W `p`*]),
    [`tube_capture_gate_median` MAD], [`0.0896`], [`0.1535`], [`-1.033`], [`3.79e-06`],
    [`persistence_hysteresis_log_det_median` MAD], [`0.2224`], [`0.4957`], [`-0.687`], [`1.92e-05`],
  ),
  caption: [Between-run MAD contrasts in the recording-complete subset (`n = 130`, `70 CPC 1` / `60 CPC 5`; subjects with ≥3 qualifying `0-12 h` runs). The MAD of `tube_capture_gate_median` exceeds its own central-tendency effect in this subset. Between-run IQR results and full coverage details are in `S2`.]
) <tab-between-run-mad>

== Incremental validity and robustness

The pooled prediction ladder is compatible with a bounded complementarity claim, limited to the restricted clinical+qEEG feature set available in the locked export. The restricted clinical+qEEG baseline achieves `AUROC = 0.599` under repeated 5×20 stratified CV. Adding the five-feature geometry layer (`persistence_hysteresis_log_det_median`, `persistence_log_det_median`, `persistence_log_eig_var_median`, `tube_capture_gate_median`, `tube_d_eff_median`) raises the internal AUROC to `0.662` (delta `+0.062`, 95% bootstrap CI `+0.054` to `+0.071`, paired `p = 1.5e-26`). Leave-one-site-out and leave-one-subject-out designs are run under the same protocol.

The `clinical only` label in @tab-incremental-validity should be read as `limited_clinical_only`: its `14` features are exactly what the locked export preserves (age, sex, ROSC time, shockable rhythm, OHCA/IHCA, targeted temperature management, hospital, channel count, channel coverage; full list in `S1`), and it omits variables that are standard in contemporary multimodal neuroprognostication, including SSEP, quantitative pupillometry, motor score, neuron-specific enolase, and structural neuroimaging. Published multimodal clinical prognostication models that include those variables typically report substantially higher discrimination than the `0.596`-`0.599` range seen here.@rajajee2023neuroprognostication The `+0.062` AUROC increment should therefore be read as geometry-versus-restricted-baseline complementarity within this locked export, not as evidence that the geometry layer outperforms state-of-the-art multimodal clinical prognostication.

#figure(
  kind: table,
  clean-table(
    columns: (2.2fr, 1.0fr, 1.05fr, 1.05fr, 0.95fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header([*Model (locked-export features only)*], [*Features*], [*AUROC*], [*AUPRC*], [*Brier*], [*Delta AUC*]),
    [`limited_clinical_only`], [14], [`0.596`], [`0.583`], [`0.248`], [`-0.003`],
    [`Restricted qEEG`], [12], [`0.521`], [`0.527`], [`0.260`], [`-0.079`],
    [`limited_clinical + qEEG`], [26], [`0.599`], [`0.596`], [`0.251`], [`+0.000`],
    [`limited_clinical + qEEG + geometry`], [31], [`0.662`], [`0.668`], [`0.240`], [`+0.062`],
  ),
  caption: [Repeated-CV summary for the pooled prediction ladder (5×20 repeated stratified CV). All four rows share the same locked-export feature ceiling; `limited_clinical_only` is feature-restricted relative to conventional multimodal clinical prognostication (SSEP, pupillometry, motor score, NSE, neuroimaging are unavailable here) and should not be read as a full clinical-practice comparator. Additional confidence intervals and site-aware summaries are moved to `S2`.]
) <tab-incremental-validity>

#figure(
  image("figures/20260606_combined_invalidityfix/fig_incremental_validity_auc.svg", width: 100%),
  caption: [Pooled ROC AUC comparison across the four main-text model tiers. All tiers share the same locked-export feature ceiling; see caption of @tab-incremental-validity for the `limited_clinical_only` caveat.]
) <fig-incremental-validity>

The supplementary robustness package sharpens the interpretation rather than overturning it. `tube_d_eff_median` remains positive in both shockable-only (`d = 0.690`, `p = 0.00522`) and non-shockable-only (`d = 0.966`, `p = 0.00672`) subsets. `tube_capture_gate_median` keeps the same direction but is weaker in the non-shockable subset (`d = -0.475`, `p = 0.200`). The two new log-determinant metrics are fully significant across both rhythm strata: `persistence_log_det_median` achieves `d = 0.689` (shockable) and `d = 1.152` (non-shockable); `persistence_hysteresis_log_det_median` achieves `d = -0.762` (shockable) and `d = -0.924` (non-shockable). The QC-only proxy model remains modest (`AUROC = 0.543`). Label permutation confirms all five metrics are well above the null (empirical `p ≤ 0.0015` for all). Additional omission checks in `S3` show that the primary pooled anchors remain sign-stable under both leave-one-subject-out and leave-one-site-out perturbations, and train-fold-only cross-fitted reachability reselection converges on the same persistence log-determinant and effective-dimensionality neighborhood (`persistence_hysteresis_log_det_median` selected in 100 folds, `persistence_log_det_median` in 91 folds). Horizon sensitivity and early-versus-late distribution summaries are moved to `S3`.

= Discussion

The pooled analysis does not flatten the coma geometry program into one repaired metric. Instead it makes the layered structure more legible. Better outcome is associated with broader chart-level short-horizon reachability and with lower local linear expansion and lower total local deformation. That joint pattern is compatible with a conservative interpretation in which better-outcome patients retain broader measurable local reachability while occupying a less locally explosive linear regime.

The merged analysis also clarifies the status of the invalidity-corrected `9D` Jacobian layer. The layer clearly contains meaningful signal in both cohorts, but with asymmetric magnitudes (`part1` stronger than `part2` for the pooled anchor rows). In the pooled result, `MNJ 9D` no longer appears as a faint appendage; its standardized effects are comparable to or larger than the corresponding `MNJ 3D` rows for several anchors. The defensible reading is therefore not "supportive but tiny," but "material and cohort-heterogeneous."

The reachability family now distributes its evidence more evenly. All five BH-FDR-corrected metrics show significant pooled separation: `persistence_hysteresis_log_det_median` and `persistence_log_det_median` provide the two strongest individual effect sizes (|d|≈0.91 and 0.90 respectively), `tube_d_eff_median` and `persistence_log_eig_var_median` anchor the effective-dimensionality dimension, and `tube_capture_gate_median` retains transport-dynamics complementarity. That all five metrics now clear BH-FDR correction is a materially different result than the previous two-strong-three-directional reading. At the same time, the subject-wise circular-shift null means that hourly peak localization should be treated as exploratory rather than as a validated timing biomarker.

The between-run temporal variability analysis in the recording-complete subset adds an orthogonal dimension. For `tube_capture_gate_median`, the between-run instability (MAD) is a stronger separator than the central-tendency level: `d = -1.033` versus `d = -0.484` in the same `n = 130` subset. This suggests that attractor stability — how consistently the capture gate is maintained across a patient's recording sessions — carries distinct outcome-relevant information beyond the metric's average level. The same pattern holds for `persistence_hysteresis_log_det_median`, where the MAD contributes independently alongside a strong central-tendency separation. Both MAD effects indicate that CPC5 subjects fluctuate more, rather than simply occupying a different mean position.

The incremental-validity result also needs a data-completeness caveat that is easy to miss when reading the AUROC numbers alone. The `limited_clinical_only` baseline is not a proxy for full clinical judgment: it is bounded by exactly what the locked export retains, and it omits SSEP, pupillometry, motor score, NSE, and neuroimaging, all of which are standard inputs to contemporary multimodal neuroprognostication and are associated with substantially higher discrimination in the published literature than the `0.596`-`0.599` range reported here.@rajajee2023neuroprognostication The geometry layer is evaluated on the same restricted footing, so the `+0.062` AUROC gain is internally comparable, but it licenses only the narrower claim that geometry adds information beyond this restricted feature set, not the broader claim that geometry adds information beyond current clinical practice.

The lead reachability result cannot yet be fully separated from residual artifact burden. The current export preserves only coarse QC proxies such as channel coverage and channel count, while direct artifact indices are unavailable because the detector is off. The available evidence argues against simple coverage confounding, but it does not prove artifact independence, and the I-CARE release itself allows residual channel contamination inside otherwise selected windows.@amorim2023icare

Several competing interpretations therefore remain live. One is a genuine recovery-linked preservation of chart-level short-horizon reachability and lower local deformation. Another is that better-outcome patients contributed smoother or less artifact-loaded trajectories, which could lower Jacobian expansion and alter reachability summaries without proving a specific mechanism. A third is that site or treatment-pathway differences still contribute, although the leave-one-site-out stability checks argue against a single-site explanation. A fourth is that timing, sedation, temperature management, and unobserved care-pathway variables contribute to the pooled contrast. The present analyses support a robust association signal in the pooled corrected exports, but they do not fully distinguish among these mechanisms.

#netn-box(title: [Claim hierarchy])[
  Internal empirical result: pooled harmonized I-CARE exports show `CPC 1` versus `CPC 5` separation across all five article-facing reachability metrics, including two persistence log-determinant metrics with pooled |d| ≈ 0.90, in addition to `MNJ 3D` expansion summaries with consistent partwise direction. Plausible interpretation: later better outcome is associated with broader chart-level short-horizon reachability, more stable persistence-eigenspectrum structure, and lower local deformation. Not established here: a bedside biomarker, a pure neural-viability assay, WLST-independent prognostication, or external prospective performance.
]

The best framing is therefore a corrected-export measurement study on recovery-linked EEG geometry, not a deployment-ready neuroprognostic biomarker paper.

= Limitations

This manuscript has ten main limitations.

1. The pooled analysis contains `301` analyzable subjects and `5322` H5 runs across two independently processed cohort roots. Invalidity-gated metric availability varies at the patient level, meaning some cells in the `9D` reachability and Jacobian families are filtered rather than measured, and comparisons across different preprocessing boundaries mix processing repair with coverage or availability shifts.
2. The primary endpoint remains `CPC 1` versus `CPC 5`, which sharpens separation but does not isolate a pure neural endpoint. WLST and time-of-death annotations are not available in the locked bundle.
3. The five reachability features used in prediction were selected via data-driven cross-fitted reselection before the pooled outcome contrasts were examined. All five clear BH-FDR correction in the pooled cohort, but the layer remains a post-selection article set rather than an externally frozen biomarker panel.
4. The repaired `MNJ 9D` layer is cohort-heterogeneous (`part1` stronger than `part2` for several anchor rows), so pooled interpretation must report both strength and heterogeneity rather than extrapolating a single mechanism.
5. Direct artifact burden is unavailable because the detector is off in the relevant export layer; the current QC checks only address coarser proxies such as channel coverage and channel count.
6. The subject-wise circular-shift null does not support a strong precise peak-timing claim, so the hourly localization map should be treated as exploratory rather than as a robust timing biomarker.
7. The locked export does not preserve a direct ROSC-to-EEG-anchor clock, so hourly bins are anchor-relative rather than validated post-ROSC phases.
8. Intermediate `CPC 2-4` categories were not used for the primary inferential contrast, so ordinal generalization remains untested.
9. The between-run temporal variability analysis is restricted to the `130` subjects with ≥`3` qualifying runs in the `0-12 h` window (`70 CPC 1` / `60 CPC 5`), representing roughly `46%` of the full extreme-outcome cohort. This is a recording-coverage-selected subset, and coverage selectivity may differ by outcome group or site, so MAD and IQR contrasts should not be extrapolated as whole-cohort effects.
10. The `limited_clinical_only` baseline used in the incremental-validity ladder is restricted to the `14` variables preserved in the locked export and omits SSEP, pupillometry, motor score, NSE, and neuroimaging that are standard in contemporary multimodal neuroprognostication. The `+0.062` AUROC increment from adding the geometry layer is therefore evidence of complementarity within this restricted feature set, not evidence that the geometry layer outperforms state-of-the-art multimodal clinical prognostication.

= Conclusion

In the pooled updated analysis, the most defensible coma geometry story is layered rather than single-family. All five article-facing reachability metrics clear BH-FDR correction — led by persistence log-determinant and persistence hysteresis log-determinant anchors (|d| ≈ 0.90) alongside effective dimensionality, log-eigenvalue spread, and capture gate — while Jacobian anchors (`MNJ 3D` and `MNJ 9D`) provide convergent support, and cohort heterogeneity is explicitly quantified rather than hidden. The geometry layer raises repeated-CV AUROC from `0.599` to `0.662` (delta `+0.062`), with leave-one-subject-out AUROC `0.668` reported in `S3`. In the recording-complete subset (`n = 130`), between-run temporal variability reveals an additional dimension: the MAD of `tube_capture_gate_median` separates outcomes with `d = -1.033`, exceeding its own central-tendency signal in the same subset, and `persistence_hysteresis_log_det_median` MAD likewise remains significant (`d = -0.687`). Together, the central-tendency and variability evidence suggest that better-outcome patients not only maintain broader average reachability but also sustain that geometry more stably across recordings. Relative to the exploratory `12_24h` global-pool audit summarized in `S2`, this early-window (`0_12h`) hierarchy is more stable under its prespecified family-wise correction: the five prespecified rows are jointly corrected-positive in `0_12h`, whereas late-window global correction reweights toward cone/tube log-eigenvalue and kappa branches with greater multiplicity sensitivity of the prespecified five-row set. The article should therefore be read as an early-window corrected-export measurement study with explicit endpoint, timing, coverage, and artifact boundaries rather than as a bedside prognostic biomarker report.

= Acknowledgements

This work emerged through structured correspondence among human and AI collaborators; large language models from OpenAI, Anthropic, and Google assisted in literature synthesis, drafting, peer review, and editorial refinement. We also gratefully acknowledge the original investigators, clinical teams, participants, and data stewards who created, curated, and shared the public datasets and metadata that made these analyses possible.

= Contact

Robin Langell - hello(at)noeticdiffusion.com

= Licensing

Licensing, stewardship, and any related trademark notes are summarized at `https://noeticdiffusion.com/license.html` and do not alter the scientific claims or reproducibility boundaries discussed here.

= Data and Code Availability

Reference implementations and analysis pipelines:
`https://github.com/NoeticDiffusion`

Datasets and related public bundles:
`https://github.com/NoeticDiffusion/NeuralManifoldDynamics-dataset`

Frozen article release:
`https://doi.org/10.5281/zenodo.20410486`

= References

#bibliography("cardiac_arrest_comatose_references.bib")
