#import "resuscitation_template.typ": *

#let blind-review = sys.inputs.at("blind", default: "false") == "true"

#show: resuscitation-template.with(
  title: "Early EEG dynamical features associated with neurological outcome after cardiac arrest: a pooled I-CARE analysis",
  short-title: "Early EEG dynamics after cardiac arrest",
  authors: if blind-review { () } else {
    ((name: "Robin Langell", affil: 1),)
  },
  affiliations: if blind-review { () } else {
    ("Langell Konsult AB, Vallentuna, Sweden",)
  },
  corresponding-author: if blind-review { "" } else { "Robin Langell, hello@noeticdiffusion.com" },
  keywords: (
    "cardiac arrest",
    "electroencephalography",
    "neurological outcome",
    "Cerebral Performance Category",
    "I-CARE",
    "post-resuscitation care",
  ),
  article-type: "Original paper",
  line-numbers: not blind-review,
  abstract: [
    *Aim:* To test whether derived short-horizon EEG dynamical features differ between patients with later Cerebral Performance Category (CPC) 1 and CPC 5 after cardiac arrest. *Methods:* We pooled two independently processed, non-overlapping I-CARE exports. Patient-level summaries from the first `12 h` after EEG-anchor were compared in `141` CPC 1 and `140` CPC 5 patients. Five prespecified dynamical features were tested with Benjamini-Hochberg correction; temporal, robustness, and restricted-feature prediction analyses were secondary. *Results:* All five prespecified features differed between outcome groups (`q = 5.70e-07` to `8.04e-03`); the largest standardized effects were for temporal persistence measures (absolute Cohen's `d` `0.896` and `0.909`). Effective dynamical dimensionality differed in the first anchor-relative hour (`d = 0.786`, `p = 1.22e-04`), although a circular-shift analysis did not support a precise peak-hour claim. In the recording-complete subset (`n = 130`), between-recording variability also differed. Adding the five features to a restricted clinical plus quantitative-EEG comparator increased repeated cross-validation AUROC from `0.599` to `0.662`. *Conclusions:* Early derived EEG dynamical features showed group-level associations with later extreme neurological outcome. The findings require external validation and do not establish individual prognostic utility, independence from withdrawal-of-life-sustaining therapy, or superiority to contemporary multimodal prognostication.
  ],
)

= Introduction

Early EEG is an important component of post-cardiac-arrest assessment, but interpretation and prognostication require a multimodal, time-aware approach.@sandroni2021european, @nolan2025postresuscitation Prospective cohorts show that conventional early EEG backgrounds are associated with outcome, while recent multicentre work also supports the value of non-highly malignant and reactive EEG for identifying good outcome.@ruijter2019early, @turella2024goodoutcome We asked whether derived properties of short-horizon EEG dynamics show group-level differences between patients with later good (`CPC 1`) and poor (`CPC 5`) neurological outcome in a public I-CARE secondary-analysis dataset.@amorim2023icare

The analysis evaluates three complementary derived feature families: static dispersion of fixed EEG-state coordinates, local short-step expansion/deformation, and short-horizon dynamical features. The latter family was prespecified as the primary corrected family; all technical definitions are provided in Supplementary Methods.

The primary question was whether these features differ during the first `12 h` after EEG-anchor. This is an association study, not a bedside neuroprognostic model: `CPC 5` is not a brain-specific endpoint, and the locked export does not contain withdrawal-of-life-sustaining therapy (WLST), time-of-death, or detailed sedation annotations.

= Methods

== Data source, cohort, and endpoint

We pooled two independently processed, non-overlapping I-CARE export roots after verifying zero subject and run overlap. The pooled bundle included `301` analyzable patients; the primary contrast comprised `281` patients (`141 CPC 1`, `140 CPC 5`). The patient was the unit of inference. Intermediate CPC categories were retained for cohort accounting but not used for the primary contrast. Detailed cohort provenance is provided in Supplementary Data.

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
    [EEG-anchor to recording start, median hours], [`0.000`], [`0.000`],
    [EEG-anchor to recording end, median hours], [`12.001`], [`11.977`],
    [Channel coverage fraction, median], [`0.952`], [`0.952`],
  ),
  caption: [Pooled `0-12 h` cohort used for the primary `CPC 1` versus `CPC 5` contrast. Time is relative to EEG-anchor; the export does not provide a direct ROSC-to-EEG clock.]
) <tab-pooled-cohort>

The analysis clock is defined by EEG-anchor, not ROSC. The locked export preserves ROSC duration as a clinical covariate but not a direct ROSC-to-EEG elapsed time. Thus, all `0-12 h` and hourly analyses are anchor-relative measurement windows rather than validated post-arrest physiological phases.

== Derived EEG features and statistical analysis

The analysis consumed fixed, previously processed EEG trajectories rather than fitting an article-specific coordinate system. The export provides a three-coordinate and a nine-coordinate representation constructed from fixed EEG feature families; the measurement contract and mathematical definitions are in Supplementary Methods.@langell2026_mndm We summarize static coordinate dispersion, local short-step expansion/deformation, and five prespecified short-horizon dynamical features. Their technical names are retained in @tab-primary-dynamics and Supplementary Methods to support reproducibility.

The primary feature family comprised `tube_d_eff_median`, `persistence_log_det_median`, `persistence_log_eig_var_median`, `persistence_hysteresis_log_det_median`, and `tube_capture_gate_median`. In plain terms, these quantify effective short-horizon dimensionality, temporal persistence of derived dynamics, and a transport/capture balance. The family was selected before pooled outcome contrasts and is an internally validated, post-selection feature set rather than an externally frozen biomarker panel. Full definitions, secondary local-dynamics measures, and cohort-specific results are in Supplementary Methods and Data.

A secondary between-recording analysis calculated the median absolute deviation (MAD) and interquartile range across qualifying recordings for each primary feature. It required at least `3` finite values per patient and therefore used a recording-complete subset of `130` patients (`70 CPC 1`, `60 CPC 5`).

The endpoint is an extreme-outcome association contrast, not a neural-viability label. `CPC 5` may reflect mortality, systemic illness, treatment limitation, and site pathways in addition to brain injury severity. WLST, time-to-death, and sedation burden were unavailable; the analysis cannot isolate these effects and should not be used for early neuroprognostic decisions.@rajajee2023neuroprognostication, @sandroni2021european

The analyses used locked processed exports and did not refit upstream harmonization inside cross-validation folds. Prediction and robustness analyses are therefore internal validations after external preprocessing, not deployment-like fold-nested preprocessing.

We report Cohen's `d`, Mann-Whitney tests, and Benjamini-Hochberg correction within the five-feature primary family. The restricted prediction comparison used repeated stratified cross-validation and a fixed logistic-regression pipeline. Leave-one-site-out, leave-one-subject-out, permutation, and train-fold-only selection analyses are reported in Supplementary QC and Robustness.

Static-dispersion and local-expansion measures are secondary descriptive anchors. Hourly localization, additional local-dynamics rows, subgroup analyses, and all robustness checks are exploratory or sensitivity material and are reported in Supplementary Data and Supplementary QC and Robustness.

= Results

== Primary dynamical-feature results

All five prespecified short-horizon dynamical features differed between outcome groups after Benjamini-Hochberg correction (@tab-primary-dynamics). The largest effects were observed for the two log-determinant persistence summaries (`d = 0.896` and `d = -0.909`). Effective dynamical dimensionality was higher in the CPC 1 group (`d = 0.838`). Secondary local-expansion and static-dispersion results were directionally consistent but are reported in Supplementary Data because they were not a second corrected discovery family.

#figure(
  kind: table,
  clean-table(
    columns: (2.3fr, 1.8fr, 0.9fr, 0.9fr, 0.95fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Derived feature*], [*Clinical description*], [*CPC 1 median*], [*CPC 5 median*], [*Cohen's `d`*], [*BH `q`*]),
    [`tube_d_eff_median`], [effective short-horizon dimensionality], [`2.990`], [`2.448`], [`+0.838`], [`1.54e-05`],
    [`persistence_log_det_median`], [persistence of derived dynamic volume], [`1.305`], [`0.832`], [`+0.896`], [`3.73e-06`],
    [`persistence_log_eig_var_median`], [persistence of eigenvalue spread], [`1.619`], [`1.017`], [`+0.736`], [`6.63e-05`],
    [`persistence_hysteresis_log_det_median`], [temporal variation in log-determinant changes], [`2.558`], [`3.718`], [`-0.909`], [`5.70e-07`],
    [`tube_capture_gate_median`], [transport/capture balance], [`1.835`], [`1.960`], [`-0.558`], [`8.04e-03`],
  ),
  caption: [Prespecified primary derived EEG dynamical features in the pooled `CPC 1` versus `CPC 5` cohort. Positive Cohen's `d` indicates higher values in CPC 1. Definitions are in Supplementary Methods.]
) <tab-primary-dynamics>

== Timing and secondary analyses

@fig-primary-reachability displays the standardized effects for the primary family. Results were stable in planned sensitivity analyses, but those analyses do not replace external validation (Supplementary QC and Robustness).

#figure(
  image(if blind-review {
    "../figures/20260606_combined_invalidityfix/fig2_primary_reachability_panel.png"
  } else {
    "../figures/20260606_combined_invalidityfix/fig2_primary_reachability_panel.svg"
  }, width: 100%),
  caption: [Pooled standardized effects for the five prespecified derived EEG dynamical features. Positive values indicate higher values in CPC 1.]
) <fig-primary-reachability>

Effective dynamical dimensionality differed in the first anchor-relative hour (`d = 0.786`, `p = 1.22e-04`) and remained positive across the 12 hourly bins (@fig-hourly). The hourly analyses are exploratory: a subject-wise circular-shift null did not support claims about a specific peak hour (`p = 0.947` for effective dimensionality). Thus, the results support early detectability in this dataset, not a time-specific physiological or prognostic window.

#figure(
  image(if blind-review {
    "../figures/20260606_combined_invalidityfix/fig3_hourly_reachability_core_heatmap.png"
  } else {
    "../figures/20260606_combined_invalidityfix/fig3_hourly_reachability_core_heatmap.svg"
  }, width: 100%),
  caption: [Exploratory anchor-relative hourly effect-size map. The circular-shift null did not support a precise peak-hour claim.]
) <fig-hourly>

== Between-recording variability

In the recording-complete subset (`n = 130`), between-recording MAD differed for two primary features. The largest difference was for `tube_capture_gate_median` (`d = -1.033`, `p = 3.79e-06`), followed by `persistence_hysteresis_log_det_median` (`d = -0.687`, `p = 1.92e-05`; @tab-between-run-mad). These selected-recording results describe variability of derived features, not a validated biological stability measure.

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
  caption: [Between-recording MAD contrasts in the recording-complete subset (`n = 130`, `70 CPC 1` / `60 CPC 5`; patients with at least three qualifying `0-12 h` recordings). IQR results and coverage details are in Supplementary Data.]
) <tab-between-run-mad>

== Restricted-feature prediction comparison

The restricted clinical plus quantitative-EEG comparator achieved AUROC `0.599` under repeated `5 × 20` stratified cross-validation. Adding the five derived features increased AUROC to `0.662` (difference `+0.062`, 95% bootstrap CI `+0.054` to `+0.071`; @fig-incremental-validity). This is an internal comparison, not a test against clinical practice. Published automated EEG studies and reviews illustrate both the potential of quantitative approaches and the need for robust external validation.@pham2022automatedeeg, @chen2024eegmlreview

The comparator includes only variables preserved in the locked export and omits somatosensory evoked potentials, quantitative pupillometry, motor examination, neuron-specific enolase, structural neuroimaging, and expert EEG interpretation. The observed increment therefore indicates information beyond this restricted comparator only; it does not establish superiority to contemporary multimodal neuroprognostication.@rajajee2023neuroprognostication

#figure(
  image(if blind-review {
    "../figures/20260606_combined_invalidityfix/fig_incremental_validity_auc.png"
  } else {
    "../figures/20260606_combined_invalidityfix/fig_incremental_validity_auc.svg"
  }, width: 100%),
  caption: [Repeated cross-validation comparison of restricted locked-export feature sets. This is not a comparison with multimodal clinical prognostication.]
) <fig-incremental-validity>

Sensitivity, QC-proxy, permutation, omission, horizon, and train-fold-only feature-selection analyses are reported in Supplementary QC and Robustness. They support internal stability of the reported associations but do not provide external or prospective validation.

= Discussion

This pooled secondary analysis found group-level differences in five prespecified derived short-horizon EEG dynamical features between patients with later CPC 1 and CPC 5. The largest standardized effects were observed for the two log-determinant persistence summaries, with effective dynamical dimensionality providing a complementary positive separator. Secondary static-dispersion and local-expansion summaries were directionally compatible with the primary family, but the corresponding `9D` estimates differed in magnitude between cohort roots. The evidence therefore supports a multifeature association in the processed exports, rather than a conclusion that one individual feature is a stable biomarker or that one specific biological mechanism has been identified.

The findings extend conventional early-EEG work in a deliberately limited way. Established clinical EEG interpretation emphasizes background continuity, suppression, burst-suppression, reactivity, seizures, and their evolution over time.@ruijter2019early, @turella2024goodoutcome The present features are derived from the same broad physiological signal but are not replacements for those clinically recognized patterns. Their potential value is as a quantitative description of variation that may not be fully captured by the restricted clinical and qEEG summaries retained in this export. Whether they add information beyond expert EEG interpretation, serial examination, or complete multimodal prognostication remains untested.

The internal sensitivity results make a single-patient or single-site explanation less likely, but do not change the validation status. The main effects retained their direction under single-subject and site omission, and label-permutation analyses placed all five observed effect sizes above the corresponding null distributions. Train-fold-only reselection repeatedly favored the two log-determinant persistence measures, reducing—without eliminating—concern that the final feature family is solely an artifact of the reported pooled ranking. These are useful internal checks, but they do not substitute for a prospectively frozen feature set tested in an independent cohort.

The timing analyses support the narrower statement that separation was detectable in the first anchor-relative hour. They do not identify a privileged post-arrest hour, because the observed hourly maxima did not exceed the subject-wise circular-shift null. The absence of a direct ROSC-to-EEG-anchor clock further limits physiological interpretation of the hourly bins. Similarly, the between-recording MAD findings suggest that selected CPC 5 patients had more variable derived features across recordings, but this analysis was restricted to the recording-complete subset and should not be generalized to all patients or interpreted as a validated measure of neural stability.

The restricted-feature prediction comparison suggests that the derived features contain information not captured by the variables retained in the locked export. It cannot be interpreted as a comparison with bedside prognostication: key predictors, including serial examination, SSEP, pupillometry, biomarkers, neuroimaging, and expert EEG interpretation, were unavailable. These modalities contribute to established multimodal assessment of good outcome.@sandroni2022goodoutcome Furthermore, upstream processing was fixed outside cross-validation, so the predictive analyses are internal rather than deployment-like validation. The observed AUROC increment should therefore be read as bounded complementarity with a feature-limited comparator, not evidence of superiority over contemporary clinical practice.

= Limitations

The primary endpoint maximizes separation but is not brain-specific. CPC 5 may reflect mortality, systemic illness, treatment limitation, and site-specific care pathways in addition to hypoxic-ischaemic brain injury. Because the locked export lacks WLST, time-of-death, and detailed sedation information, the study cannot distinguish these pathways from a recovery-linked EEG association.

Direct artifact burden was unavailable because the relevant detector was disabled in the processed export. Channel count, channel coverage, and usable-window summaries provide only coarse quality-control proxies. Their limited predictive performance and modest correlations with some primary features argue against a simple coverage-only explanation, but they do not demonstrate artifact independence. The dataset documentation also notes that noisy recordings may remain available, reinforcing this limitation.@physionet_icare_21

The five-feature family is a post-selection internal-validation object rather than an externally frozen biomarker panel. Although cross-fitted reselection and permutation analyses were supportive, preprocessing was completed before downstream validation and not refitted within each fold. Feature availability also varies with invalidity gating, which may mix biological separation with differences in measurement availability.

Finally, the primary analysis compares extreme outcomes only and does not establish an ordinal relationship across CPC 2–4. External prospective validation should use a prespecified feature set, direct artifact measures, a verified ROSC-to-recording clock, and outcome data that permit explicit accounting for sedation and treatment-limitation pathways.

= Conclusion

In pooled I-CARE exports, five prespecified derived early EEG dynamical features were associated with later extreme neurological outcome at group level, with internally stable but post-selection evidence across complementary sensitivity analyses. The results support further study of quantitative early-EEG dynamics as a research measurement layer. They do not establish a neural mechanism, a pure assay of brain viability, a specific post-arrest prognostic hour, or individual-patient utility. Independent prospective validation should use a frozen feature set, complete multimodal clinical comparators, direct artifact measures, a verified ROSC-to-recording clock, and treatment-pathway information including sedation and WLST.

= Acknowledgements

We thank the I-CARE investigators, participating clinical teams, participants, and data stewards for making the underlying data available.

= Ethics approval and consent to participate

This secondary analysis used de-identified, publicly available I-CARE data. No local ethics review was required for the present analysis, which involved no new data collection, participant contact, or intervention. The I-CARE dataset documentation reports that source data collection and analysis were conducted under independent Institutional Review Board approvals at participating hospitals, with a data-sharing agreement among sites. It further states that the source analysis was retrospective, used data obtained as part of usual care, and had a waiver of informed consent.@physionet_icare_21

= Funding

 No funding was received.

= Declaration of competing interests

No conflicts of interest were declared.

= CRediT authorship contribution statement

#if blind-review [
Author contributions are available to the editor and will be restored after peer review.
] else [
Robin Langell: Conceptualization, Methodology, Software, Formal analysis, Validation, Visualization, Writing – original draft, Writing – review & editing.
]

= Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During preparation of this work, the author used GPT-5.6 Terra and GPT-5.4, and Claude Sonnet 4.6 and Claude Sonnet 5, for literature organization, language editing, and editorial drafting. The author reviewed and edited all generated material and takes full responsibility for the content of the published article.

= Data and Code Availability

#if blind-review [
The underlying I-CARE dataset is available through PhysioNet, version `2.1`. The derived analysis outputs and code are available to the editor for review and will be openly identified after peer review, subject to the access conditions of the underlying dataset.
] else [
The underlying I-CARE dataset is available through PhysioNet, version `2.1`. Derived analysis outputs backing this manuscript are archived at `https://doi.org/10.5281/zenodo.20410486`. Analysis code is available at `https://github.com/NoeticDiffusion`, subject to the access conditions of the underlying dataset.
]

= References

#bibliography(
  if blind-review {
    "cardiac_arrest_comatose_references_blinded.bib"
  } else {
    "cardiac_arrest_comatose_references.bib"
  },
  style: "resuscitation-vancouver.csl",
  title: none,
)
