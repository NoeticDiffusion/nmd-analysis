#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods - Walking-State Geometry in Parkinson Disease",
  short-title: "Walking Supplementary Methods",
  subtitle: "Bundle contract, mixed-anchor logic, and article-local support stack for ds007526",
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

This supplement records the extended methods for the Parkinson walking article. It focuses on:

1. the processed bundle contract,
2. the participant and run structure,
3. the mixed-anchor design logic,
4. the exact article-local analysis stack,
5. the statistical reporting boundary,
6. and the explicit absence of classical EEG comparator sidecars in the present export.

= Processed bundle contract

The article uses the refreshed walking bundle:

- `data/raw/neuralmanifolddynamics_ds007526_20260610_121725`

The local participant metadata under `articles/CLINICAL/parkinson_walking/metadata/participants.tsv` lists `144` unique participants:

- `116` Parkinson disease (`PD`) participants,
- `28` healthy controls (`HC`).

The bundle contributes `277` processed runs:

- `144` rest runs,
- `133` walk runs.

The article-facing walk disease-state contrast therefore uses `23` `HC` walk runs and `110` `PD` walk runs. The paired task branch uses `110` `PD` rest/walk pairs and `23` `HC` rest/walk pairs.

The H5 export exposes both anchor-specific global layers and anchor-specific regional layers, including:

- `coords_3d_cohort_anchored/values`
- `coords_3d_subject_anchored/values`
- `coords_9d_cohort_anchored/values`
- `coords_9d_subject_anchored/values`
- `jacobian_cohort_anchored/J_hat`
- `jacobian_subject_anchored/J_hat`
- `jacobian_9D_cohort_anchored/J_hat`
- `jacobian_9D_subject_anchored/J_hat`
- `regional_mnps/<network>/cohort_anchored/...`
- `regional_mnps/<network>/subject_anchored/...`

The article-local support layer resolves these paths explicitly rather than assuming one default contract.

= Noetic Diffusion and NeuralManifoldDynamics framing

The article uses two nested levels of description.

- Noetic Diffusion Theory supplies the broader dynamical framing.@langell2025_6
- NeuralManifoldDynamics supplies the versioned measurement contract that fixes the chart basis, Jacobian summaries, and reachability interface.@langell2026_mndm @langell2026_reachability

The operational state chart is treated as inherited from the export rather than re-estimated inside the article. In that inherited contract, the canonical `3D` chart is `x_t = [m_t, d_t, e_t]`, while the stratified chart is a fixed `9D` decomposition. The article uses those exported coordinates as auditable measurement objects, not as proof that one unique latent biological mechanism has been discovered.

= Mixed-anchor design

The core design rule is shown in @tab-s1-contracts.

#figure(
  kind: table,
  clean-table(
    columns: (1.7fr, 1.0fr, 2.6fr),
    align: left,
    inset: 4pt,
    table.header([*Question*], [*Primary contract*], [*Why this is the article-facing contract*]),
    [`PD walk vs HC walk`], [`cohort_anchored`], [A between-subject disease-state comparison requires a shared cohort reference frame.],
    [`PD walk vs rest`], [`subject_anchored`], [A within-subject task-reconfiguration question should preserve subject-centered alignment.],
    [`HC walk vs rest`], [`subject_anchored`], [Same paired logic as the Parkinson branch, but retained only as context.],
  ),
  caption: [Mixed-anchor selection rule used throughout the article.]
) <tab-s1-contracts>

This means the manuscript does *not* claim that one anchor is globally superior. It claims that the inferential question determines the correct anchor.

= Article-local analysis stack

The article draws from four linked layers.

== Standard run-level layer

The standard layer uses `src/parkinson_walking_support.py`, `src/run_parkinson_walking_contrasts.py`, and `src/run_parkinson_walking_clinical_associations.py` to produce global run-level summaries and their contrast tables. The output folders used in the article are:

- `results/parkinson_walking_20260610/contrasts_cohort_121725`
- `results/parkinson_walking_20260610/contrasts_subject_121725`
- `results/parkinson_walking_20260610/clinical_cohort_121725`
- `results/parkinson_walking_20260610/clinical_subject_121725`

The standard retained rows discussed in the main article come only from:

- `contrasts_cohort_121725/group_contrasts.csv`
- `contrasts_subject_121725/paired_task_contrasts.csv`

== Regional layer

The regional layer extends the same logic to frontal, central, temporal, and parietal-occipital sensor groups. The relevant article-facing folder is:

- `results/parkinson_walking_20260610/regional_cohort_121725`

and, for the subject rerun used mainly to complete the evidence map,

- `results/parkinson_walking_20260610/regional_subject_121725`

Regional findings are treated as topographic support, not as source-localized anatomical claims.

== Reachability wrapper layer

The article-local reachability wrapper calls into the repository implementation via:

- `src/run_parkinson_walking_reachability_wrappers.py`
- `ndt-analysis/ndt_analysis/reachability_cones.py`
- `ndt-analysis/ndt_analysis/reachability_core.py`

The article-facing cohort outputs used in the supplement are:

- `results/parkinson_walking_20260610/reachability_cohort_121725`

These tables summarize short-horizon future-capacity geometry under local linearization. In the current dataset, the strongest corrected reachability rows are concentrated in the rest branch rather than the walk branch.

== Exploratory trajectory layer

The compact-summary trajectory layer is produced via:

- `src/run_parkinson_walking_trajectory_geometry.py`

with article-facing outputs in:

- `results/parkinson_walking_20260610/trajectory_cohort_121725`
- `results/parkinson_walking_20260610/trajectory_subject_121725`

This layer implements exploratory metrics such as:

- `entropy_rate`
- `irreversibility`
- `noetic_action`
- `noetic_action_kinetic`
- `noetic_action_jerk`
- `noetic_action_potential`
- `curvature_median`
- `tortuosity`
- `path_length`

In the current article, trajectory geometry is retained only as exploratory context because it remains rest-dominant and does not outrun the standard walk disease-state rows.

= Article exports and figure build

To prevent number drift across the main manuscript and the supplements, the article uses one dedicated export layer:

- `src/build_parkinson_walking_article_exports.py`
- `results/parkinson_walking_20260610/article_exports_121725`

This export layer writes:

- `focal_rows.csv`
- `context_rows.csv`
- `supportive_rows.csv`
- `exploratory_rows.csv`
- `evidence_ledger.csv`
- `retained_counts.csv`
- `manuscript_numbers.json`
- `article_evidence_summary.md`

The figure layer is built separately via:

- `src/build_parkinson_walking_figures.py`
- `figures/20260610_article/cohort_walk_focals.png`
- `figures/20260610_article/pd_walk_vs_rest_focals.png`
- `figures/20260610_article/hc_walk_vs_rest_context.png`

= Statistical and interpretive boundary

All group contrasts and association scans use `BH-FDR` within their script-defined families. The main-text threshold is `q < 0.05`; the `q < 0.1` layer is retained only in `S2` for transparency. No focal row was preregistered, so the retained rows should be read as corrected article-facing representatives rather than as confirmatory endpoints.

= Classical comparator boundary

The repository also contains an article-local classical EEG wrapper:

- `src/run_parkinson_walking_classical_wrappers.py`
- `ndt-analysis/ndt_analysis/eeg_classical_comparators.py`

However, the present `ds007526` bundle does not expose the `conventional_eeg` extension. The wrapper therefore correctly reports the classical panel as unavailable in this export. The article accordingly does *not* make claims of superiority or incremental validity relative to classical EEG measures.

= Files

The methods claims in this supplement are backed mainly by:

- `metadata/readme.md`
- `metadata/participants.tsv`
- `src/parkinson_walking_support.py`
- `src/run_parkinson_walking_contrasts.py`
- `src/run_parkinson_walking_clinical_associations.py`
- `src/run_parkinson_walking_regional_analysis.py`
- `src/run_parkinson_walking_reachability_wrappers.py`
- `src/run_parkinson_walking_trajectory_geometry.py`
- `src/build_parkinson_walking_article_exports.py`
- `src/build_parkinson_walking_figures.py`
- `results/parkinson_walking_20260610/article_exports_121725/*`

#bibliography("parkinson_walking_geometry.bib")
