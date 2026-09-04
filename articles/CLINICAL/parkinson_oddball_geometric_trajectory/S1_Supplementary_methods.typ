#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "Parkinson 10B Supplementary Methods",
  subtitle: "ds004574 disease-first provenance, 10B-5 definitions, and validation boundary",
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

This supplement records the extended methods for the disease-first Parkinson oddball manuscript. It focuses on six items that are intentionally compressed in the main article:

1. the fixed `ds004574` bundle contract,
2. the event-label boundary and residual-label handling,
3. the forked article-local trajectory wrapper,
4. the added `10B-5` family temporal coupling layer,
5. the disease-first ranking logic,
6. the robustness and null-model boundary.

= Bundle contract

The manuscript uses the processed NeuralManifoldDynamics export:

- `J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_ds004574_20260602_062756`

The relevant sidecars in the same run root are:

- `run_manifest.json`
- `stage_mapping_qc.json`
- `features_snapshot.json`
- `normalization_report.json`

The active ingest provenance points to a behavior-enriched staging rather than a raw OpenNeuro root. The final processed cohort contains `146` analyzable H5 files:

- `48` Control
- `98` Parkinson

The bundle provides:

- subject-anchored `3D` coordinates,
- subject-anchored `9D` coordinates,
- `3D` Jacobian / MNJ,
- `9D` Jacobian,
- raw and robust-z features,
- subtype-aware `raw_*` label provenance.

The bundle does *not* provide:

- cohort-anchored coordinates,
- ComBat normalization,
- regional outputs,
- external validation splits.

= Event contract and residual-label handling

The meaningful event surface for this article is the behavior-enriched `raw_*` namespace:

- `raw_standard_precue_onset_sec`
- `raw_standard_arrowcue_onset_sec`
- `raw_standard_response_onset_sec`
- `raw_oddball_auditory_precue_onset_sec`
- `raw_oddball_auditory_arrowcue_onset_sec`
- `raw_oddball_auditory_response_onset_sec`
- `raw_oddball_visual_precue_onset_sec`
- `raw_oddball_visual_arrowcue_onset_sec`
- `raw_oddball_visual_response_onset_sec`

These arrays are treated as the article's experimental event surface. `labels/stage` is intentionally ignored because in this dataset it is largely `-1` and is not a reliable trial-state annotation.

Residual `raw_nan_onset_sec` is treated as unmatched join residue rather than as a real task condition. The article-local wrapper excludes such events by construction, and the robustness pass separately excludes all subjects with positive residual `raw_nan` labels (`26` subjects in the final bundle).

The wrapper exports three granularities:

1. exact phase-locked rows such as `auditory_arrowcue`,
2. subtype-collapsed rows such as `auditory_all`,
3. phase-collapsed rows such as `all_response`.

= Analysis stack

== Standard layer

The standard disease-support layer uses repository `ndt-analysis` with:

- `ndt-analysis/config/ndt-analysis-ds004574.yaml`
- `ndt-analysis/config/analysis-ds004574.yaml`

Enabled blocks are restricted to what the bundle actually exposes:

- global `MNPS 3D`,
- global `MNPS 9D`,
- global Jacobian `3D`,
- global Jacobian `9D`,
- global reachability,
- `trajectory_dynamics`,
- `tier2_jacobian`,
- `tau_summary`,
- `adaptive_collapse`.

== Article-local disease-first wrapper

The forked code lives under `articles/CLINICAL/parkinson_oddball_geometric_trajectory/src/`:

- `parkinson_oddball_support.py`
- `compute_parkinson_oddball_event_metrics.py`
- `export_parkinson_oddball_contrasts.py`
- `run_parkinson_oddball_pipeline.py`
- `run_parkinson_oddball_robustness.py`

This wrapper reuses the earlier `ds004574` event architecture but reranks the outputs around `Control vs Parkinson` instead of around subtype contrasts. Each event block is summarized in local windows with `2` pre-event and `3` post-event windows.

= Coordinate and metric definitions

== `MNPS 3D` and `MNPS 9D`

The `3D` chart uses the family axes `(m, d, e)`. The `9D` chart uses the fixed order:

- `m_a`, `m_e`, `m_o`
- `d_n`, `d_l`, `d_s`
- `e_e`, `e_s`, `e_m`

Whenever family-level summaries are needed, the wrapper collapses `9D` back to family means

$
bar(m)_t = (m_a + m_e + m_o) / 3,
quad
bar(d)_t = (d_n + d_l + d_s) / 3,
quad
bar(e)_t = (e_e + e_s + e_m) / 3.
$

== Retained trajectory metrics

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

*Repertoire-flow summaries.*
After k-means quantization to states `$s_t$` with occupancy `$pi_i$` and transition matrix `$P$`,
$
H = - sum_i pi_i sum_j P_(i j) log(P_(i j) + epsilon),
$
$
I = (1 / 2) sum_i sum_j | pi_i P_(i j) - pi_j P_(j i) |,
$
$
E = sum_i sum_j pi_i P_(i j) log((pi_i P_(i j) + epsilon) / (pi_j P_(j i) + epsilon)).
$

*Noetic action.*
With diagonal metric `$M$`,
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
A_t = K_t + J_t + V_t.
$

The wrapper reports medians of `noetic_action`, `noetic_action_kinetic`, `noetic_action_jerk`, and `noetic_action_potential`.

*Planar hysteresis.*
The `(m,d)`, `(m,e)`, and `(d,e)` planes are summarized by polygon loop area
$
H_(i j) = (1 / 2) | sum_t z_i(t) z_j(t+1) - z_j(t) z_i(t+1) |.
$

The exported `hysteresis_area_mean` is the robust median across the three family planes.

== Added `10B-5` family temporal coupling

The genuinely new article-local layer is lagged family coupling. For families `a` and `b` in `{m, d, e}` and lag `$tau$`,

$
C_(a b)(tau) = "corr"(Delta bar(a)_t, bar(b)_(t - tau)).
$

The wrapper exports directed rows such as:

- `coupling_md_tau1`
- `coupling_dm_tau1`
- `coupling_me_tau2`
- `coupling_ed_tau2`

and directional asymmetry rows

$
A_(a b)(tau) = C_(a b)(tau) - C_(b a)(tau),
$

for example:

- `asymmetry_md_tau1`
- `asymmetry_me_tau2`
- `asymmetry_de_tau2`

The lag grid is intentionally compact:

- `tau = 1`
- `tau = 2`

This keeps the disease-first layer exploratory but not combinatorially unbounded.

== Additional exploratory trajectory variants

Three smaller exploratory variants were added in the same fork:

1. `path_hysteresis`, defined as the mean separation between forward and reversed recovery paths after common arc-length resampling,
2. `torsion_median`, computed from the family-projected `3D` path,
3. `return_probability_tau2` and `return_probability_tau3`, defined as delayed state return rates after repertoire quantization.

These rows are reported as exploratory only.

= Disease-first ranking and inference

The ranking logic is deliberately different from the earlier event-first article.

1. Rows are first prioritized by `Control vs Parkinson`.
2. Within the wrapper, `auditory_all`, `auditory_arrowcue`, and `auditory_response` are given the highest disease-first priority.
3. Standard global rows remain in the combined ranking as supportive disease anchors.
4. Subtype rows such as `auditory vs standard` are retained only as boundary-setting secondary context.

Wrapper group rows use Mann-Whitney tests and Cohen's `d`. Paired subtype rows use Wilcoxon tests and Cohen's `d_z`. BH-FDR is applied within `(contrast_name, analysis_type)` blocks.

The article uses `q < 0.1` as the exploratory retention threshold. In the final disease-first rerun no event-centered wrapper row survives that threshold, while several global standard rows do.

= Robustness and null-model boundary

The robustness package lives in:

- `results/parkinson_oddball_geometric_trajectory_20260602/selected_metric_robustness.csv`
- `results/parkinson_oddball_geometric_trajectory_20260602/selected_metric_robustness.md`

The main follow-up passes are:

- exclusion of subjects with positive residual `raw_nan_onset_sec`,
- exclusion of `sub-112`,
- pooled `2.5% / 97.5%` winsorization,
- circular-shift family shuffle null for selected `10B-5` rows.

In the shuffle null, the family traces `(bar(m), bar(d), bar(e))` inside each selected event segment are circularly shifted independently, preserving each family's marginal path while destroying the true cross-family lag alignment. The null is repeated `32` times per segment, summarized by the segment-median null value, and then aggregated to subject level by medians over blocks.

This null does not validate every coupling row equally. In the final run, `asymmetry_me_tau2` collapses under the shuffle control while some raw coupling amplitudes do not, which is why the main manuscript treats asymmetry rows as cleaner mechanistic candidates than amplitude-only coupling rows.

= Files

The manuscript-facing files for this article are:

- `results/parkinson_oddball_geometric_trajectory_20260602/event_contrasts.csv`
- `results/parkinson_oddball_geometric_trajectory_20260602/article_metric_ranking.csv`
- `results/parkinson_oddball_geometric_trajectory_20260602/article_metric_summary.md`
- `results/parkinson_oddball_geometric_trajectory_20260602/selected_metric_robustness.csv`
- `results/parkinson_oddball_geometric_trajectory_20260602/analysis_summary.md`
