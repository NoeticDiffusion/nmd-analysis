#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "Parkinson Supplementary Methods",
  subtitle: "ds004574 bundle provenance, event contract, and auditory oddball analysis stack",
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

This supplement records the extended methods for the Parkinson auditory oddball manuscript. It focuses on five items that were intentionally kept compact in the main paper:

1. the fixed `ds004574` bundle contract and provenance,
2. the event-label contract used for oddball subtype inference,
3. the two-layer analysis stack linking standard `ndt-analysis` exports and the article-local event wrapper,
4. compact mathematical definitions for the main coordinate, Jacobian, reachability, and trajectory summaries,
5. the inferential and robustness boundary for the article-facing metrics.

= Bundle contract

The manuscript uses the processed NeuralManifoldDynamics run:

- `J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_ds004574_20260602_062756`

Important sidecars in the same run root are:

- `run_manifest.json`
- `stage_mapping_qc.json`
- `features_snapshot.json`
- `normalization_report.json`

The active ingest provenance points to `config_ingest_ds004574.yaml`, but the dataset root used for this run is a behavior-enriched staging rather than the raw OpenNeuro root:

- `M:/datasets/received/openneuro/ds004574_behavior_enriched`

This staging was created to join subtype information from `beh.tsv` into the EEG event surface without changing the upstream MNDM code path. The resulting processed bundle contains `146` analyzable subject H5 files:

- `98` Parkinson
- `48` Control

The main contract features relevant for this manuscript are:

- subject-anchored `3D` coordinates,
- subject-anchored `9D` coordinates,
- `3D` Jacobian / MNJ,
- `9D` Jacobian,
- raw and robust-z feature exports,
- behavior-enriched `labels/raw_*` event provenance.

The bundle does *not* provide:

- cohort-anchored coordinates,
- ComBat normalization,
- regional MNPS exports,
- or time-reference extensions.

= Event contract and label boundary

The meaningful event surface in this dataset is the subtype-aware `raw_*` label namespace:

- `raw_standard_precue_onset_sec`
- `raw_standard_arrowcue_onset_sec`
- `raw_standard_response_onset_sec`
- `raw_oddball_auditory_precue_onset_sec`
- `raw_oddball_auditory_arrowcue_onset_sec`
- `raw_oddball_auditory_response_onset_sec`
- `raw_oddball_visual_precue_onset_sec`
- `raw_oddball_visual_arrowcue_onset_sec`
- `raw_oddball_visual_response_onset_sec`

These labels are treated as the article's experimental event surface. The wrapper therefore builds event blocks directly from the corresponding `labels/*` arrays and does not rely on `labels/stage` as a meaningful trial-state annotation. In this bundle `stage` is largely `-1` by design and is not used for clinical or event-related inference.

Residual `raw_nan_onset_sec` provenance is explicitly excluded from the article-local wrapper. It is treated as unmatched behavior-join residue rather than as a valid event subtype.

For reporting, the wrapper exports three event granularities:

1. exact phase-locked rows such as `auditory_precue` and `visual_response`,
2. subtype-collapsed rows such as `auditory_all`,
3. phase-collapsed rows such as `all_precue`.

= Analysis stack

The manuscript uses two linked layers.

== Standard layer

The standard path uses repository-level `ndt-analysis` with:

- `ndt-analysis/config/ndt-analysis-ds004574.yaml`
- `ndt-analysis/config/analysis-ds004574.yaml`

Enabled standard blocks are limited to what the bundle actually exposes:

- global `MNPS 3D`
- global `MNPS 9D`
- global Jacobian `3D`
- global Jacobian `9D`
- global reachability
- trajectory dynamics
- `tier2_jacobian`
- `tau_summary`

Regional and cohort-anchor blocks are disabled because the bundle does not expose those layers.

== Article-local event wrapper

The article-local code lives under `articles/CLINICAL/parkinson_auditory_recall/src/`:

- `parkinson_auditory_support.py`
- `compute_parkinson_auditory_event_metrics.py`
- `export_parkinson_auditory_contrasts.py`
- `run_parkinson_auditory_pipeline.py`

The wrapper reads the processed H5 files directly, resolves the subject-anchored `3D` and `9D` coordinate layers, constructs event blocks from `raw_*` label arrays, and summarizes each block with trajectory measures in local windows that include `2` pre-event windows and `3` post-event windows.

The main manuscript-facing result directories are:

- `results/parkinson_auditory_recall_20260602/standard_cleaned`
- `results/parkinson_auditory_recall_20260602/standard_analysis`
- `results/parkinson_auditory_recall_20260602/event_metrics`
- `results/parkinson_auditory_recall_20260602/event_contrasts.csv`
- `results/parkinson_auditory_recall_20260602/article_metric_ranking.csv`

= Endpoint and inference boundary

The primary article question is whether auditory oddball events show stronger or more distinctive noetic geometry than the other event types in the same run. The patient, not the epoch, is the primary unit of inference in all manuscript-facing tables.

This creates three inference tiers.

1. *Primary:* auditory oddball versus other event types, especially subtype-collapsed `auditory_all` against `standard_all`, `visual_all`, and their within-subject `other_mean`.
2. *Supportive:* `Control` versus `Parkinson` contrasts in the standard global layers and in event-specific trajectory rows.
3. *Exploratory:* phase-matched subtype contrasts (`precue`, `arrowcue`, `response`) and phase-collapsed summaries.

The article-facing metric set is therefore discovery-ranked rather than preregistered. Metrics are ranked by standardized effect size together with BH-FDR-adjusted `q` values, and the main paper carries only a compact subset of approximately `3-7` rows.

= Coordinate and metric definitions

== `MNPS 3D` and `MNPS 9D`

The `3D` coordinate export is the primary MNPS chart with axes `(m, d, e)`. The `9D` chart uses the fixed stratified order:

- `m_a`, `m_e`, `m_o`
- `d_n`, `d_l`, `d_s`
- `e_e`, `e_s`, `e_m`

When the wrapper needs a family-level projection from `9D` back to `3D`, it uses the simple family means

$
bar(m)_t = (m_a + m_e + m_o) / 3,
quad
bar(d)_t = (d_n + d_l + d_s) / 3,
quad
bar(e)_t = (e_e + e_s + e_m) / 3.
$

== Global Jacobian summaries

For each analyzable local window, let $J_t$ denote the exported Jacobian estimate.

*Spectral radius.*
$
rho_t = max_i |lambda_i(J_t)|.
$

*Frobenius norm.*
$
F_t = norm(J_t)_F = sqrt("tr"(J_t^top J_t)).
$

*Jacobian change ratio / `MDR`.*
If the temporal derivative is available,
$
D_t = norm(dot(J)_t)_F / (norm(J_t)_F + epsilon).
$

These are aggregated at subject level in the standard pipeline and then contrasted between `Control` and `Parkinson`.

== Reachability

For the local stochastic linearization

$
x_(t + 1) = A_t x_t + b_t + epsilon_t,
quad
epsilon_t ~ (0, Q_t),
$

the propagated covariance is

$
Sigma_t^((0)) = sigma_0^2 I,
quad
Sigma_t^((h + 1)) = A_t Sigma_t^((h)) A_t^top + Q_t.
$

The most relevant article-facing reachability quantities are compact summaries of:

- effective dimensionality,
- anisotropy,
- log-eigenvalue spread,
- transport versus innovation ratio,
- capture-gate style short-horizon summaries.

== Event-locked trajectory geometry

Let $z_t in R^k$ denote an event-centered coordinate path with $k = 3$ or $k = 9$.

*Path length.*
$
L = sum_t || z_(t+1) - z_t ||.
$

*Tortuosity.*
$
T = L / (|| z_T - z_1 || + epsilon).
$

*Curvature.*
With local velocity `$v_t$` and acceleration `$a_t$`,
$
kappa_t = sqrt(|| v_t ||^2 || a_t ||^2 - (v_t dot a_t)^2) / (|| v_t ||^3 + epsilon).
$

*Entropy rate* and *irreversibility.*
After k-means state quantization to `$s_t$` with occupancy mass `$pi_i$` and transition matrix `$P$`,
$
H = - sum_i pi_i sum_j P_(i j) log(P_(i j) + epsilon),
$
$
I = (1 / 2) sum_i sum_j | pi_i P_(i j) - pi_j P_(j i) |.
$

*Entropy production.*
$
E = sum_i sum_j pi_i P_(i j) log((pi_i P_(i j) + epsilon) / (pi_j P_(j i) + epsilon)).
$

*Noetic action.*
The wrapper defines pointwise kinetic, jerk, and potential terms
$
K_t = (1 / 2) || Delta z_t ||_M^2 / Delta t^2,
$
$
J_t = || Delta^2 z_t ||_M^2 / Delta t^4,
$
$
V_t = bar(e)_t - bar(m)_t + bar(d)_t,
$
$
A_t = K_t + J_t + V_t,
$
and reports the median over `$t$` of `$A_t$` as `noetic_action` together with its kinetic, jerk, and potential components. `$M$` is the diagonal variance-stabilized metric learned from pooled sampled event segments.

*Recovery residual.*
Distance between the pre-event baseline center and the late post-event recovery anchor in projected family space.

*Hysteresis.*
Pairwise polygon loop area between the forward and return paths in the `(m,d)`, `(m,e)`, and `(d,e)` planes. The exported `hysteresis_area_mean` is the robust median across these three family-plane loop areas.

= Statistical analysis

The standard and wrapper layers use separate inferential paths but the same reporting logic.

- The standard layer uses the repository analysis pipeline to produce `Control vs Parkinson` contrasts with permutation-based p-values, bootstrap intervals, standardized effect sizes, and BH-FDR grouped by `(contrast_name, analysis_type)`.
- The event wrapper uses paired Wilcoxon tests for within-subject auditory-versus-other comparisons and Mann-Whitney tests for `Control vs Parkinson` differences on the subject-level event summaries.
- Wrapper effect sizes are Cohen's `d_z` for paired contrasts and Cohen's `d` for unpaired group contrasts.

The primary reporting threshold is `q < 0.1`. This is an exploratory threshold chosen to map the most promising geometry rows in a medium-sized clinical dataset rather than to claim a frozen biomarker hierarchy.

= QC and robustness boundary

The manuscript-facing robustness package is intentionally bounded to the fixed bundle and article-local exports. The main checks are:

- exclusion of residual `raw_nan_onset_sec` events by construction,
- robust subject-level aggregation by medians rather than epoch-level pooling,
- explicit follow-up on extreme `9D` Jacobian subjects such as `sub-112`,
- winsorized sensitivity for selected group comparisons,
- transparent reporting of the absence of cohort-anchor, ComBat, and regional layers.

This package supports bounded internal validation of the article-facing rows, but it is not external validation of a frozen clinical biomarker set.
