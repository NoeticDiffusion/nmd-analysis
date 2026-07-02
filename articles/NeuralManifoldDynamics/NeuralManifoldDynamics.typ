#set page(
  paper: "us-letter",
  margin: (x: 1in, y: 1in),
  numbering: "1",
)

#set text(
  font: "Times New Roman",
  size: 12pt,
)

#set par(
  justify: true,
  first-line-indent: 0.5in,
  leading: 1.8em,
)

#set heading(numbering: none)

#show table: it => {
  set text(size: 9pt)
  set par(
    first-line-indent: 0pt,
    leading: 1.2em,
  )
  it
}

#align(center)[
  #text(size: 10pt)[Article type: Methods]
  #v(1em)
  #text(size: 18pt, weight: "bold")[
    NeuralManifoldDynamics: A Measurement Model for Robust 3D and Stratified 9D Neural Manifold Dynamics
  ]
  #v(1em)
  #text(size: 10pt)[Short title: NeuralManifoldDynamics]
  #v(1em)
  #text(size: 11pt)[Robin Langell]
  #v(0.5em)
  #text(size: 9pt, style: "italic")[Noetic Diffusion Project]
  #v(1em)
  #text(size: 10pt)[Corresponding author: Robin]
  #v(1em)
  #text(size: 10pt)[Keywords: NeuralManifoldDynamics, MNPS, MNJ, EEG, fMRI, regional dynamics, CSD, robustness]
]

#v(2em)

= Abstract
#par(first-line-indent: 0pt)[
  NeuralManifoldDynamics 2.0 is a versioned ingest-layer measurement contract for deriving low-dimensional and stratified neural state trajectories, together with local Jacobian-based dynamical summaries, from EEG and fMRI. In the current release, this contract is explicitly NDT-aligned: it fixes a canonical 3D chart (`mnps_3d = [m, d, e]`), an optional stratified 9D chart (`coords_9d`), and a corresponding family of Jacobian exports. Relative to the older MNPS 1.2 generation, the updated contract introduces stricter coverage and estimator hygiene, explicit feature-standardization pipelines, improved handling of missing and non-finite support, self-describing HDF5 outputs, and regional manifold dynamics that now include EEG through channel-group trajectories in addition to fMRI network trajectories. For EEG, regionalization is coupled to optional Current Source Density preprocessing and topology-based electrode ensembles, making local regional summaries and block-Jacobian exports possible while preserving a shared export logic with regional fMRI outputs. The role of the ingest layer is operational rather than interpretive: it serializes a stable, auditable measurement object for downstream analysis.
]

= Author Summary
#par(first-line-indent: 0pt)[
  NeuralManifoldDynamics 2.0 describes how this repository now turns EEG and fMRI into auditable manifold measurements. The system no longer stops at a single 3D coordinate summary. It now supports a canonical 3D trajectory, a stratified 9D coordinate chart, regional manifold dynamics for both fMRI networks and EEG channel groups, stricter epoch-quality controls, and self-describing HDF5 outputs. The purpose is not to interpret cognition at ingest time, but to provide a stable and reproducible measurement contract for downstream analysis.
]

#v(2em)

= Introduction
NeuralManifoldDynamics is the current name for the ingest-layer measurement system that operationalizes *Meta-Noetic Phase Space* dynamics in this repository. It is grounded in the broader Noetic Diffusion Theory framework and its subsequent formalization of stratified coordinates and second-order local dynamics [@langell2025_6; @langell2025_stratified; @langell2025_mnj]. The central design choice is that ingest defines a fixed and reproducible measurement contract: it standardizes raw signals, extracts features, applies fixed coordinate mappings, estimates local dynamics, and exports auditable artifacts for downstream analysis. It does not adapt its behavior to contrasts of interest, and it does not interpret states, diagnoses, or conditions.

Version 2.0 replaces the older MNPS 1.2 style in which the primary emphasis was a weighted low-dimensional trajectory plus limited summary exports. The current implementation is more explicit about measurement support, coverage, failure modes, regionalization, and export semantics. It separates three related objects: the canonical 3D manifold trajectory, the stratified 9D coordinate system, and the family of Jacobian-derived dynamical summaries built on top of these trajectories, in line with the layered distinction between MNPS, stratified MNPS, and MNJ in the current theory stack [@langell2025_6; @langell2025_stratified; @langell2025_mnj]. Within this manuscript, the exported chart should therefore be read as an NDT-aligned, versioned measurement contract rather than as a claim that these axes are uniquely privileged latent neurobiological primitives.

#block(
  width: 100%,
  breakable: true,
  inset: 10pt,
  fill: luma(245),
  stroke: 0.5pt + luma(120),
  radius: 4pt,
)[
  *Claims and Non-Claims* \
  *Claims:* fixed export naming, deterministic feature preprocessing, explicit coverage handling, global and regional trajectory construction, local Jacobian serialization, and manifest-based self-description. \
  *Non-claims:* no diagnosis inference, no consciousness-level inference, no claim that `[m, d, e]` are uniquely privileged latent biological primitives, and no claim that EEG channel groups are direct homologues of fMRI networks. The chart labels should be read as operational labels within the current release contract.
]

#block(
  width: 100%,
  breakable: true,
  inset: 10pt,
  fill: luma(245),
  stroke: 0.5pt + luma(120),
  radius: 4pt,
)[
  *Chart Definition in Current Release* \
  `coords_9d` subcoordinates are fixed for this release. \
  `mnps_3d` is a derived canonical export from a fixed weighted projection of `coords_9d`. \
  Projection weights, axis names, and serialization paths are versioned and auditable. \
  They should not be read as claims of unique biological identifiability.
]

= Model Definition
The primary trajectory is the canonical 3D manifold:

$ cal(X)_t = [m_t, d_t, e_t] $

where:

- *m* operationalizes macrostate morphology and low-frequency arousal-tonus structure under the current contract.
- *d* operationalizes dispersion and network-binding structure under the current contract.
- *e* operationalizes nonlinear complexity and broadband energy-related structure under the current contract.

This trajectory is exported in HDF5 as `mnps_3d`, with its temporal derivative exported as `mnps_3d_dot`. The canonical axis order is fixed as `[m, d, e]` and is written explicitly into file-level metadata. Conceptually, this is the ingest-layer realization of the low-dimensional Meta-Noetic Phase Space used in the Noetic Diffusion Theory program [@langell2025_6].

The stratified coordinate system extends the model to nine sub-coordinates:

$ cal(X)_t^(9) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m] $

This stratified chart is exported as `coords_9d/values` together with `coords_9d/names`. The purpose of the 9D system is not to replace the 3D manifold, but to provide a finer-grained operational decomposition within the current chart version. The primary 3D trajectory and the stratified 9D chart therefore coexist as distinct measurement objects, matching the rationale of Stratified Meta-Noetic Phase Space while remaining operational and version-bound in this ingest contract [@langell2025_stratified].

Local dynamics are represented by Jacobian estimates. The primary Jacobian is written under `jacobian/J_hat`, while stratified dynamics are written under `jacobian_v2/J_hat` in the current codebase. Regional network-specific Jacobians are exported under `regional_mnps/<network>/jacobian`. This follows the role assigned to the Meta-Noetic Jacobian as the local second-order dynamical layer on top of MNPS coordinates [@langell2025_mnj].

== Rationale for the Stratified 9D Contract
The current `coords_9d` configuration is not presented here as a claim of uniquely privileged latent neurobiological ontology. Rather, it should be read as the current release's NDT-aligned measurement contract: a fixed, auditable decomposition chosen to balance increased resolution beyond coarse 3D composites, preserved recomposability into the canonical `mnps_3d` export, modality-level measurability in EEG and fMRI, and estimator-aware robustness at ingest time [@langell2025_stratified].

The main methodological motivation is dimensional masking. In a composite 3D summary, compensatory redistributions among subcoordinates can produce near-zero movement along a canonical axis even when the underlying signal family changes substantially. The stratified 9D chart exposes those redistributions directly and therefore reduces false-null behavior in the canonical 3D summary.

The nine subcoordinates were deliberately restricted to three families aligned with the canonical `[m, d, e]` topology. This grouping allows deterministic recomposition through a fixed weighted 9D->3D projection while keeping naming, provenance, and downstream serialization stable across datasets. The current weight values should therefore be read as release-fixed operational priors encoded in configuration, not as learned dataset-specific optima and not as claims of unique biological correctness. Full chart stability under feature substitutions, weight perturbations, and alternative projection families remains a future validation target rather than an established property of the current release.

= What Changed in Version 2.0
NeuralManifoldDynamics 2.0 introduces several changes relative to the older MNPS 1.2 implementation.

== Stronger Measurement Robustness
The updated measurement model enforces explicit bounds on estimator support. Epoch inclusion is no longer a minimal pass/fail step. Instead, the pipeline tracks coverage in terms of available seconds, available epochs, and direct axis support. Missing weighted features are handled by per-axis renormalization rather than silent zero-filling. Windows or trajectories with insufficient support, all-non-finite stratified coordinates, or inconsistent dimensionality are now surfaced explicitly rather than silently propagated.

Feature preprocessing is also deterministic rather than ad hoc. In the common EEG and fMRI contracts, the default sequence for weighted features is `log10 -> robust_z -> clip`, with clip threshold `+-6 sigma` in transformed space. Entropy-like and Hjorth-derived metrics are explicitly exempted from blind `log10` compression and instead use `robust_z -> clip`, as configured in `mnps_projection.feature_standardization`. The untransformed baselines used to produce these normalized values are retained as per-feature metadata (`abs_median`, `abs_mad`, and applied transformation string), so absolute scale is preserved for audit rather than destroyed by preprocessing.

== Improved Epoch Quality and Support
The current pipeline is designed to retain more usable epochs while improving quality control. Coverage policy is now computed explicitly, including effective coverage after masking and quality-control drops. This allows the system to preserve high-quality support where possible while rejecting windows that would otherwise degrade the Jacobian fit or distort anisotropy-related summaries.

The result is not only more data, but more defensible data. This matters because anisotropy, condition numbers, and local Jacobian estimates are highly sensitive to unstable or poorly supported neighborhoods.

== Derivative and Time-Base Contract
`mnps_3d_dot` is not an unspecified symbolic derivative. In the active contracts it is estimated with a Savitzky-Golay derivative on the epoch-time series, with EEG default `window = 7`, `polyorder = 3`, and fMRI default `window = 5`, `polyorder = 2`. When the sequence is too short for a valid Savitzky-Golay fit, the implementation falls back to central differences; when large jumps segment a trajectory, the robust segmented derivative path prevents smoothing across discontinuities. In the current implementation, Savitzky-Golay derivatives are evaluated with interpolation-based edge handling and are not post-trimmed at segment boundaries before export. Accordingly, boundary derivatives remain part of the serialized contract and should be treated as lower-confidence near short or recently split segments if a downstream analysis requires stricter edge control. These choices are part of the measurement contract because downstream Jacobian estimation depends directly on derivative stability.

== Formal 3D and 9D Separation
The older pipeline used naming that blurred low-dimensional and stratified outputs. Version 2.0 now makes the distinction explicit:

- `mnps_3d` is the canonical 3D trajectory.
- `coords_9d` is the stratified coordinate chart.
- `mnps_3d_dot` is the derivative of the canonical trajectory.

This separation makes the output contract more interpretable for human readers and for downstream tooling.

= Regional NeuralManifoldDynamics
Regional manifold dynamics are now a core part of the implemented model rather than an external post-processing idea. In theoretical terms, this extends the MNPS and MNJ framing from a single global chart to a set of network- or group-specific charts that can be compared within one measurement contract [@langell2025_stratified; @langell2025_mnj].

== Regional fMRI
The repository already supported regional fMRI through ROI-based or network-based aggregation. Version 2.0 preserves that path and continues to export regional fMRI signals and regional manifold summaries without changing the basic contract. Regional fMRI outputs remain embedded in the same HDF5 payload structure as before, and the code keeps modality-specific safeguards where stratified block Jacobians are not empirically justified for fMRI.

== Regional EEG via Channel Groups
The major new addition is regional EEG support. EEG features can now be grouped using topology-based channel ensembles, producing per-group feature columns with `__g_<group>` suffixes. These grouped feature tables are then converted into per-group manifold trajectories and optional stratified regional trajectories.

In practical terms, a channel group such as `frontal`, `central`, `parietal_occipital`, or `temporal` is treated as a topology-based regional surrogate used to support a shared export logic with regional fMRI, while preserving modality-specific interpretive limits. Each region can therefore produce:

- a regional 3D trajectory,
- a regional 3D Jacobian,
- an optional regional stratified trajectory,
- regional CSV-style summaries that are now also embedded into HDF5.

This brings EEG regional processing closer to the fMRI regional path while still keeping modality differences explicit.

== CSD / Surface Laplacian for EEG
Regional EEG is coupled to an optional *Current Source Density* preprocessing step. This is a critical methodological change because direct channel averaging in sensor space is otherwise vulnerable to volume conduction. In the active EEG reference configuration, the CSD transform uses `lambda2 = 1e-5`, `stiffness = 4.0`, `n_legendre_terms = 50`, and `min_eeg_channels = 16`, with failure behavior controlled by `on_error` (the current `ds004511` overlay uses `warn`). These parameters are written into preprocessing metadata so the exact spatial filter is auditable.

The important design point is that the measurement contract now acknowledges that regional EEG must be spatially filtered before inter-regional dynamical summaries are treated as meaningful.

= Modality Coverage
The current reference configurations, `ds000228` for fMRI and `ds004511` for EEG, support the following entities:

#table(
  columns: (auto, auto, auto),
  inset: 6pt,
  stroke: 0.5pt + black,
  align: (left, center, center),

  [*Data entity*], [*fMRI*], [*EEG/iEEG*],
  [Global `mnps_3d`], [Yes], [Yes],
  [Global `coords_9d`], [Yes], [Yes],
  [Global MNJ], 
  [
    Yes \
    `jacobian/J_hat` on `mnps_3d` \
    `jacobian_v2/J_hat` on `coords_9d`
  ],
  [
    Yes \
    `jacobian/J_hat` on `mnps_3d` \
    `jacobian_v2/J_hat` on `coords_9d`
  ],

  [Regional `mnps_3d`],
  [
    Yes \
    network-level 3D from regional fMRI features
  ],
  [
    Yes \
    channel-group 3D from `__g_<group>` EEG features
  ],

  [Regional `coords_9d`],
  [
    No in `ds000228` \
    code path exists, but `regional_mnps.stratified.enabled = false`
  ],
  [
    Yes in `ds004511` \
    `regional_mnps.stratified.enabled = true`
  ],

  [Regional `mnps_3d` + MNJ],
  [
    Yes \
    `regional_mnps/<network>/jacobian`
  ],
  [
    Yes \
    `regional_mnps/<network>/jacobian`
  ],

  [Regional `coords_9d` + MNJ / block structure],
  [
    No in `ds000228` \
    regional 9D disabled by config
  ],
  [
    Yes in `ds004511` \
    regional stratified trajectories enabled \
    regional block Jacobians enabled
  ],
)

#par(first-line-indent: 0pt)[
  Code check: this table reflects the active reference configs rather than only abstract code capability. For fMRI, `ds000228` keeps global `coords_9d` enabled because `mnps_3d` is derived from 9D, but disables regional 9D in config. For EEG, `ds004511` enables both global and regional stratified trajectories, together with regional block-Jacobian summaries. In the current repository, iEEG datasets are routed through the electrophysiology path using `modality: eeg`, so the rightmost column should be read as the current EEG-family implementation path.
]

= Axis Construction
The same reference configurations construct global `mnps_3d` and `coords_9d` as follows. The rows below should be read as modality-specific operationalizations under a shared chart family, not as claims of one-to-one physiological homology between EEG and fMRI features.

#table(
  columns: (auto, auto, auto),
  inset: 6pt,
  stroke: 0.5pt + black,
  align: (left, left, left),

  [*Subcoordinate / entity*], [*fMRI (`ds000228`)*], [*EEG (`ds004511`)*],
  [
    `mnps_3d`
  ],
  [
    `mnps_3d.mode = from_v2` \
    `x = coords_9d @ P_fixed` \
    `P_fixed` from `mnps_projection.v1_mapping` \
    weights resolved against `mnps_9d.subcoords` \
    runtime: L2-normalized columns + coverage-aware renormalization
  ],
  [
    `mnps_3d.mode = from_v2` \
    `m <- 0.62*m_a + 0.55*m_e + 0.45*m_o` \
    `d <- 0.50*d_n + 0.82*d_l + 0.28*d_s` \
    `e <- 0.85*e_e + 0.62*e_s + 0.03*e_m` \
    runtime: L2-normalized columns + coverage-aware renormalization
  ],

  [`m_a`], [`fmri_FC_mean`], [`-0.5*eeg_delta - 0.5*eeg_theta`],
  [`m_e`], [`fmri_gradient_ratio`], [`-1.0*eeg_alpha`],
  [`m_o`], [`fmri_modularity`], [`eeg_beta_alpha`],
  [`d_n`], [`fmri_variance_global`], [`eeg_gamma`],
  [`d_l`], [`fmri_dFC_variance`], [`eeg_hjorth_mobility`],
  [`d_s`], [`fmri_kuramoto_global`], [`eeg_alpha_theta`],
  [`e_e`], [`fmri_signal_power`], [`eeg_permutation_entropy`],
  [`e_s`], [`fmri_slow4_slow5_ratio`], [`eeg_hjorth_complexity`],
  [`e_m`], [`fmri_ar1_coefficient`], [`embodied_arousal_proxy`],
)

#par(first-line-indent: 0pt)[
  These rows summarize the active 9D-to-3D construction used by the current reference configs. The active runtime path is a fixed weighted projection from `coords_9d` to `mnps_3d`, not a trivial equal-weight mean over all subaxes. The projection weights should be read as release-fixed operational priors chosen to preserve recomposability, interpretability, modality-level measurability, and estimator robustness within the ingest contract. For fMRI, regional stratified construction is present in the dataset file but explicitly disabled. For EEG, the dataset overlay enables regional stratified MNPS and associated regional block-Jacobian summaries.
]

#par(first-line-indent: 0pt)[
  When subcoordinate support is incomplete, the implementation renormalizes over the weights that remain present and records per-axis coverage. This yields a degraded support class of `mnps_3d` estimates rather than a geometry that is automatically identical to the full-support case. Accordingly, scale-sensitive geometric summaries derived from full-support and degraded-support trajectories should be treated as support-conditioned and, where necessary, adjusted downstream using the exported coverage and provenance rather than assumed to be directly interchangeable.
]

= Jacobians, Block Jacobians, and Anisotropy
NeuralManifoldDynamics 2.0 extends the dynamical output family beyond a single primary Jacobian. This is directly aligned with the idea that first-order position in manifold space and second-order transformation structure should be reported separately rather than collapsed into one scalar summary [@langell2025_mnj].

The current implementation exports:

- primary 3D Jacobians on `mnps_3d`,
- stratified Jacobians on `coords_9d`,
- regional Jacobians for each network or EEG channel group,
- block-Jacobian summaries for stratified and regional outputs,
- embedded tabular exports of those summaries inside HDF5.

Anisotropy is now treated as a first-class quality and geometry descriptor. It appears in regional summaries and in block-Jacobian summaries, alongside Frobenius norms, trace-like quantities, and symmetric or rotational cross-block metrics where applicable. The practical effect is that version 2.0 provides a more discriminating description of local geometry than a pure trace-based summary.

== Jacobian Validity Domain
Jacobian export is conditional on support and numerical validity rather than guaranteed by name alone. The active implementation enforces or records at least the following constraints:

- minimum coverage in seconds and epochs before a segment is processed,
- minimum direct-axis support after projection renormalization (`min_axis_coverage`, default `0.3`),
- finite-valued `mnps_3d` rows before kNN/Jacobian estimation,
- finite-valued `coords_9d` rows before stratified Jacobian estimation,
- conditioning and anisotropy diagnostics in downstream summaries, including Jacobian condition-number summaries and regional `strat9_condition_number`,
- withholding or skipping of regional/block Jacobians when the modality/configuration is not empirically supportable, most notably regional 9D block Jacobians for fMRI, which are disabled by default because per-network trajectories are typically rank-deficient at available window counts.

Accordingly, Jacobian-derived exports should be read as valid only within these support constraints. The contract serializes the resulting diagnostics and provenance; it does not imply that every requested Jacobian is estimable for every dataset, modality, or regional decomposition.

== Chart Stability as Future Validation Target
The present manuscript defines the current release contract, not full embedding-family invariance. In particular, it fixes one NDT-aligned chart family, one set of subcoordinate definitions per release, and one auditable 9D->3D projection contract. Future validation should therefore assess chart stability under reasonable feature substitutions, weighting perturbations, and projection changes, so that release stability can be distinguished from calibration dependence.

= Output Contract and Self-Describing Artifacts
The export layer has also changed substantially.

== Run Directory and Naming
Runs are now written into directories named:

`neuralmanifolddynamics_<dataset>_<timestamp>`

This replaces the older `mnps_*` naming convention and makes the run purpose clearer.

== HDF5 Naming
The HDF5 contract is more explicit than before. Important paths now include:

- `mnps_3d`
- `mnps_3d_dot`
- `coords_9d/values`
- `coords_9d/names`
- `jacobian/J_hat`
- `regional_mnps/<network>/mnps`
- `regional_mnps/<network>/jacobian`
- `extensions/tabular_exports/*`

The previous ambiguity of short names such as `x` has been removed.

== Self-Description Through Manifests
Each run writes `run_manifest.json`, which now includes a field guide describing the meaning of key HDF5 paths. This is important because the export contract should be legible to both human users and automated readers without requiring separate source-code inspection.

Summary tables that were previously emitted only as CSV files are now also embedded into HDF5 as columnar exports under `extensions/tabular_exports`. This makes the HDF5 file a more self-contained artifact.

= Relation to Existing Frameworks
NeuralManifoldDynamics sits adjacent to several established software ecosystems rather than replacing them. For standardized preprocessing and data organization, the closest precedents are BIDS-oriented pipelines such as `fMRIPrep`, `MNE-BIDS`, and the `MNE-BIDS-Pipeline`, together with feature- and ROI-oriented toolkits such as `mne-features` and `Nilearn` [@Esteban2019FMRIPrep; @Appelhoff2019MNEBIDS; @MNEBIDSPipelineDocs; @MNEFeaturesPackage; @Abraham2014Nilearn]. These systems are stronger choices when the primary goal is modality-specific preprocessing maturity, BIDS interoperability, or extraction of clean modality-native time series. NeuralManifoldDynamics begins one layer downstream: it fixes a versioned chart contract, derives canonical and stratified trajectory objects, and serializes local Jacobian-based summaries with explicit provenance.

The manuscript should also be read against data-adaptive state-space and brain-state software. Methods such as `CEBRA` optimize latent embeddings from data [@Schneider2023CEBRA], while packages such as `Pycrostates` and `NeuroCAPs` operationalize states through discrete microstate segmentation or co-activation pattern clustering [@Ferat2022Pycrostates; @Smith2025NeuroCAPs]. More general neurodynamics and dynamic-connectivity toolboxes, including `OSL-Dynamics`, `dyconnmap`, and LEiDA-style state analyses, emphasize generative dynamic modeling, time-varying connectivity, or recurrent connectivity states rather than a fixed export contract [@Gohil2024OSLDynamics; @Marimpis2021Dyconnmap; @Cabral2017LEiDA; @shine2016]. Relative to these frameworks, NeuralManifoldDynamics trades some data-adaptive flexibility for cross-dataset commensurability: the axes, projection rules, derivative logic, and serialized outputs are intentionally version-bound and auditable.

Accordingly, the main claim of NeuralManifoldDynamics is not that every ingredient is novel in isolation. The narrower claim is that the repository combines multimodal ingest, a fixed 3D/9D chart family, local Jacobian exports, and self-describing HDF5 provenance into one operational measurement contract. This is a more defensible statement of need than positioning the system as a general replacement for preprocessing pipelines, clustering-based state software, or dynamic functional connectivity toolboxes.

= Relationship to the Older MNPS 1.2 Generation
The appropriate way to think about version 2.0 is not as a cosmetic rename, but as a stricter measurement model.

Compared with MNPS 1.2, the new system:

- formalizes the distinction between 3D and 9D coordinates,
- improves robustness and coverage handling,
- makes feature standardization explicit and auditable,
- supports regional EEG in addition to regional fMRI,
- couples EEG regionalization to optional CSD preprocessing,
- exports richer Jacobian and anisotropy-oriented summaries,
- writes more self-describing HDF5 and run-manifest outputs.

The theoretical object remains a manifold-based description of neural dynamics, but the implementation is now better aligned with estimator hygiene, provenance, and reproducible export semantics.

= Methods-Oriented Discussion
The most important conceptual shift in NeuralManifoldDynamics 2.0 is methodological rather than rhetorical. The ingest layer is no longer treated as a lightweight staging area before “real” analysis begins. Instead, it is treated as the place where the measurement contract is fixed.

This has several consequences. First, naming matters, because ambiguous path names lead to ambiguous downstream assumptions. Second, coverage matters, because local linear estimators fail silently when support is poor. Third, regional EEG cannot be justified merely by averaging channels; it must be coupled to a defensible preprocessing pathway. Fourth, regional fMRI and regional EEG should share a common export logic where possible, while still preserving their modality-specific limits.

Under this design, NeuralManifoldDynamics 2.0 is best understood as an auditable, NDT-aligned measurement contract. Downstream analysis may compare groups, estimate clinical effects, or test theoretical predictions, but those later steps should inherit a stable coordinate system rather than redefine it.

= Conclusions
NeuralManifoldDynamics 2.0 is the current implementation name for the manifold measurement model in this repository. It supersedes the older MNPS 1.2-style ingest contract by making the coordinate hierarchy, robustness logic, regionalization strategy, and output semantics substantially more explicit.

The model now has four defining properties:

1. a canonical 3D manifold trajectory, `mnps_3d`;
2. a stratified 9D coordinate chart, `coords_9d`;
3. regional manifold dynamics for both fMRI and EEG channel groups;
4. self-describing exports designed for auditability and downstream reproducibility.

This makes the system better suited for public release, external inspection, and downstream scientific use.

= References
#bibliography("NeuralManifoldReferences.bib")

= Technical Terms
#par(first-line-indent: 0pt)[*NeuralManifoldDynamics*: The current ingest-layer measurement model implemented in this repository for deriving manifold trajectories and Jacobian-based summaries from neural data.]
#par(first-line-indent: 0pt)[*mnps_3d*: The canonical three-dimensional manifold trajectory with fixed axis order [m, d, e].]
#par(first-line-indent: 0pt)[*coords_9d*: The stratified coordinate matrix containing nine sub-coordinates that refine the canonical 3D manifold.]
#par(first-line-indent: 0pt)[*Meta-Noetic Jacobian (MNJ)*: A local Jacobian estimate defined on manifold trajectories and used to summarize local dynamical structure.]
#par(first-line-indent: 0pt)[*Anisotropy*: A geometry-sensitive summary of directional imbalance in a Jacobian or block-Jacobian field.]
#par(first-line-indent: 0pt)[*Current Source Density (CSD)*: A spatial filtering transform for EEG intended to suppress broad field spread and emphasize local cortical activity.]
#par(first-line-indent: 0pt)[*Regional MNPS*: A regionalized manifold representation in which trajectories and Jacobians are computed separately for networks or channel groups.]
#par(first-line-indent: 0pt)[*Block Jacobian*: A Jacobian summary restricted to a block or family of coordinates, such as m-to-m or e-to-d interactions.]
#par(first-line-indent: 0pt)[*Coverage policy*: The explicit rule set that determines whether an epoch or trajectory has sufficient support to be retained for measurement.]
#par(first-line-indent: 0pt)[*Measurement contract*: The fixed export definition that specifies what is measured, how it is named, and how it is serialized for downstream use.]
