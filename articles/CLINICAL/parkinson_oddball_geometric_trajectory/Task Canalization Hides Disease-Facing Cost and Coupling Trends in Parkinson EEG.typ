#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Task Canalization Hides Disease-Facing Cost and Coupling Trends in Parkinson EEG",
  short-title: "Parkinson Oddball 10B",
  subtitle: "A disease-first ds004574 analysis of hidden trajectory cost, recovery asymmetry, and family temporal coupling",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "Parkinson disease",
    "EEG",
    "oddball",
    "trajectory geometry",
    "Noetic Diffusion",
    "temporal coupling",
  ),
  article-type: "Research Article",
  abstract: [
    We revisited the NeuralManifoldDynamics `ds004574` oddball bundle (`146` subjects; `98` Parkinson, `48` controls) with a disease-first question: can Parkinson-control structure become clearer when the oddball trajectory is treated as a hidden cost, recovery, and coupling problem rather than as a pure route-choice problem? The analysis kept `ds004574` fixed and reused the event-centered wrapper architecture from the earlier auditory manuscript, but reranked the full `10B` trajectory family around `Control vs Parkinson` instead of around subtype separation. In addition to the previously implemented noetic-action, hysteresis, repertoire-flow, curvature, and tortuosity layers, we added `10B-5` stratified family temporal coupling on the `9D` family triplets `(bar(m), bar(d), bar(e))`. The strongest exploratory disease-facing wrapper rows were no longer entropy-collapse rows but lagged family-coupling and recovery rows, including `3D auditory_arrowcue coupling_dm_tau2` (`d = 0.492`, `p = 0.0094`, `q = 0.643`), `3D auditory_response asymmetry_me_tau2` (`d = 0.375`, `p = 0.0324`, `q = 0.643`), and `9D auditory_arrowcue hysteresis_area_md` (`d = -0.397`, `p = 0.0236`, `q = 0.718`). A `9D` jerk row tightened after residual-label exclusion (`d = -0.553`, `p = 0.0033`) but did not retain the same strength after outlier follow-up. No event-locked Parkinson-control row survived BH-FDR. The stable disease support remained global, with lower `3D m_median` (`d = -0.602`, `q = 0.0090`) and higher reachability `tube_q_ratio_h4_mean` (`d = 0.557`, `q = 0.0385`) in Parkinson. Meanwhile the subtype boundary stayed dominant: `auditory vs standard` entropy and transition-sparsity rows remained orders of magnitude stronger than any disease-facing wrapper row. The bounded conclusion is therefore that `ds004574` does not yield a retained event-locked Parkinson biomarker even after the disease-first `10B` rerun, but the most interpretable disease-facing trends now sit in coupling asymmetry, recovery geometry, and hidden cost rather than in route choice alone.
  ],
  author-summary: [
    The previous `ds004574` article showed that auditory oddball windows collapse both groups into a sharply canalized trajectory corridor. This follow-up asks whether disease information appears not in which route the brain takes, but in how hard it is to travel that route and how the system returns afterward. The answer is mixed but informative. The strongest Parkinson-control wrapper trends shift toward lagged family coupling, recovery asymmetry, and hidden cost, especially around `auditory_arrowcue` and `auditory_response`. Yet those rows remain exploratory because none survive BH-FDR and the strongest raw coupling amplitudes are not specific under a shuffle-null test. The stable disease layer is still global, while the dominant event result remains the old subtype canalization. The most conservative interpretation is therefore that the disease-first `10B` rerun improves mechanistic targeting, but not enough to overturn the task-first geometry that dominates this bundle.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted in the submission version.],
  data-availability: [
    Data were analyzed from the local NeuralManifoldDynamics export at `data/raw/neuralmanifolddynamics_ds004574_20260602_062756`. Disease-first article outputs are stored under `articles/CLINICAL/parkinson_oddball_geometric_trajectory/results/parkinson_oddball_geometric_trajectory_20260602`, including `event_metrics/`, `event_contrasts.csv`, `article_metric_ranking.csv`, `selected_metric_robustness.csv`, and the companion supplementary summaries. Article-local code is stored under `articles/CLINICAL/parkinson_oddball_geometric_trajectory/src/`.
  ],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

= Introduction

The earlier `ds004574` oddball manuscript established a strong event-first result: auditory windows are markedly more compact and less entropic than the rest of the run, and that subtype geometry is stronger than any event-locked Parkinson-control contrast. That result remains important, but it also creates a design problem. If the task forces both groups through the same low-entropy corridor, then route-choice metrics alone may underestimate disease structure. A canalized trajectory can be shared while the cost of traveling it, the timing of internal family coordination, and the geometry of the return path still differ.

That possibility motivates a disease-first rerun of the same fixed bundle. The question is no longer whether the auditory oddball defines a distinct route; that was already shown. The question is whether Parkinson-control differences become more legible when the oddball is interpreted as hidden cost, recovery asymmetry, and lagged family coupling. In the language of the `10B` trajectory program, the relevant candidates are noetic action, hysteresis, recurrence, and especially the missing `10B-5` layer of stratified family temporal coupling.

#netn-box(title: [Core question])[
  In the fixed `ds004574` oddball bundle, does a disease-first `10B` rerun reveal Parkinson-control structure in hidden trajectory cost, recovery asymmetry, or family-level temporal coupling even when subtype canalization still dominates the route itself?
]

= Cohort and design

The analyzed dataset is the same processed NeuralManifoldDynamics `ds004574` bundle used in the prior article. It contains `146` subject H5 files with `48` controls and `98` Parkinson subjects, all with `task = oddball` and `condition = not_applicable`. The bundle exposes subject-anchored `3D` coordinates, subject-anchored `9D` coordinates, `3D` and `9D` Jacobian layers, and behavior-enriched `raw_*` event provenance.

The event surface remains the same and is critical for interpretation. Exact blocks are built from:

- `raw_standard_*`
- `raw_oddball_auditory_*`
- `raw_oddball_visual_*`

As in the earlier article, `labels/stage` is intentionally not used as an inferential event surface. Residual `raw_nan_onset_sec` is treated as unmatched provenance rather than as a meaningful event class. A focused robustness pass detects `26` subjects with remaining positive `raw_nan` labels and reruns the selected disease-facing rows after subject exclusion.

#figure(
  kind: table,
  table(
    columns: (2.55fr, 1.15fr, 1.15fr, 1.7fr),
    align: left,
    inset: 5pt,
    table.header([*Design item*], [*Control*], [*Parkinson*], [*Bundle status*]),
    [Unique subjects], [48], [98], [`146` total H5 files],
    [Task label], [`oddball`], [`oddball`], [behavior-enriched subtype staging],
    [Condition label], [`not_applicable`], [`not_applicable`], [single-condition cohort],
    [Coordinate contract], [subject_anchored], [subject_anchored], [`3D` and `9D` available],
    [Main event surface], [`standard`, `auditory`, `visual`], [`standard`, `auditory`, `visual`], [`raw_*` labels used directly],
    [Residual `raw_nan` subjects], [`26` flagged], [`26` flagged], [used only in robustness exclusion],
    [Regional outputs], [none], [none], [global layers only],
    [ComBat normalization], [none], [none], [disabled in run manifest],
  ),
  caption: [Cohort and bundle design summary for the disease-first `ds004574` oddball rerun.]
) <tab-design>

= Analysis framework

The study keeps the earlier two-layer architecture but changes the inferential order.

1. *Standard global layer.* Repository `ndt-analysis` was rerun with the same `ds004574` configs to obtain global `MNPS`, Jacobian, reachability, adaptive-collapse, and tier-2 summaries under `Control vs Parkinson`.
2. *Article-local event wrapper.* The earlier auditory wrapper was forked into `parkinson_oddball_geometric_trajectory/src/`, retaining path length, curvature, repertoire-flow, noetic action, and hysteresis summaries while adding:
   - `10B-5` family temporal coupling, with rows such as `coupling_md_tau1`, `coupling_dm_tau2`, and `asymmetry_me_tau2`,
   - exploratory `path_hysteresis`,
   - exploratory `torsion_median`,
   - exploratory `return_probability_tau2` and `return_probability_tau3`.

For the coupling layer, the `9D` triplets are first collapsed to family means

$
bar(m)_t = (m_a + m_e + m_o) / 3,
quad
bar(d)_t = (d_n + d_l + d_s) / 3,
quad
bar(e)_t = (e_e + e_s + e_m) / 3.
$

Lagged directed coupling is then summarized as

$
C_(a b)(tau) = "corr"(Delta bar(a)_t, bar(b)_(t - tau)),
$

with directional asymmetry

$
A_(a b)(tau) = C_(a b)(tau) - C_(b a)(tau).
$

The inferential hierarchy is explicit.

1. *Primary:* `Control vs Parkinson` on event-centered `10B` rows, especially `auditory_all`, `auditory_arrowcue`, and `auditory_response`.
2. *Secondary:* the older within-subject subtype contrasts, used only to define the task canalization boundary.
3. *Supportive:* global disease rows from the standard pipeline.

= Results

== Disease-facing event rows shift toward coupling and recovery, not entropy collapse

When the wrapper is reranked around `Control vs Parkinson`, the strongest event-centered candidates move away from pure entropy-collapse rows and toward lagged family coordination and recovery geometry. The highest-ranked auditory rows are a positive `3D auditory_arrowcue coupling_dm_tau2`, a positive `3D auditory_response asymmetry_me_tau2`, and a negative `9D auditory_arrowcue hysteresis_area_md`. The directional reading is that Parkinson subjects show a stronger delayed `d -> m` coupling term, a more positive `m/e` asymmetry at `auditory_response`, and a smaller `m-d` recovery loop area at `auditory_arrowcue`.

The crucial limitation is that none of these event-centered disease rows survive BH-FDR. They are therefore interpretable trends rather than retained biomarkers. The disease-first rerun changes *where* the most interesting rows live, but not the formal retention boundary.

#figure(
  kind: table,
  table(
    columns: (2.45fr, 1.0fr, 1.0fr, 0.85fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Control med*], [*Parkinson med*], [*`d`*], [*BH-FDR `q`*]),
    [`3D auditory_arrowcue coupling_dm_tau2`], [`-0.0399`], [`0.0884`], [`+0.492`], [`0.643`],
    [`3D auditory_response asymmetry_me_tau2`], [`-0.0592`], [`0.0183`], [`+0.375`], [`0.643`],
    [`9D auditory_arrowcue hysteresis_area_md`], [`0.4656`], [`0.3860`], [`-0.397`], [`0.718`],
    [`9D auditory_arrowcue noetic_action_jerk`], [`0.03459`], [`0.03036`], [`-0.343`], [`0.742`],
  ),
  caption: [Exploratory disease-facing event rows. None survive BH-FDR, but the highest-ranked rows now sit in coupling, asymmetry, recovery, and hidden-cost families rather than in the old route-choice metrics.]
) <tab-disease-wrapper>

The hidden-cost row deserves a bounded comment. `9D auditory_arrowcue noetic_action_jerk` does not stand out in the full cohort (`p = 0.0736`), but it strengthens after residual-label exclusion (`d = -0.553`, `p = 0.0033`). That suggests the cost interpretation is not purely empty, although it is not stable enough across all follow-up passes to carry the article by itself.

== Coupling asymmetry is cleaner than raw coupling amplitude under shuffle-null follow-up

The strongest raw coupling amplitudes are not automatically the cleanest mechanistic signals. A circular-shift family shuffle null was run on the selected `10B-5` rows after excluding residual `raw_nan` subjects. Under that null, `3D auditory_response asymmetry_me_tau2` collapses to near zero (`d = 0.039`, `p = 0.848`), which argues that its observed direction depends on the real temporal choreography between family channels.

By contrast, raw coupling-amplitude rows such as `3D auditory_arrowcue coupling_dm_tau2` and `9D auditory_all coupling_me_tau1` still show sizable group differences even in the shuffled control. Those rows are therefore less specific than they first appear and should be described as hypothesis-generating rather than as validated coupling biomarkers.

== Stable disease support remains global

The standard global layer remains the only part of the disease-first story that survives BH-FDR cleanly. Parkinson subjects again show lower global `3D m_median` and higher reachability `tube_q_ratio_h4_mean`, matching the earlier article and providing a stable backdrop for the exploratory wrapper rows.

#figure(
  kind: table,
  table(
    columns: (2.15fr, 1.0fr, 1.0fr, 0.85fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Control med*], [*Parkinson med*], [*`d`*], [*BH-FDR `q`*]),
    [`global 3D m_median`], [`0.0347`], [`0.0201`], [`-0.602`], [`0.0090`],
    [`reachability tube_q_ratio_h4_mean`], [`0.2474`], [`0.2821`], [`+0.557`], [`0.0385`],
    [`adaptive collapse q_ratio_h4`], [`0.2312`], [`0.2752`], [`+0.518`], [`0.0200`],
    [`reachability q_ratio_h2_median`], [`0.5177`], [`0.5469`], [`+0.552`], [`0.0385`],
  ),
  caption: [Retained supportive disease rows from the standard global layer. These remain more statistically stable than the event-centered disease-first wrapper rows.]
) <tab-global-support>

The most conservative disease picture in `ds004574` is therefore still a layered one: robust global mobility and reachability shifts, with exploratory event-centered cost and coupling trends sitting on top.

== Task canalization remains the dominant boundary condition

The disease-first rerun does not erase the earlier task result. The subtype boundary remains dramatically stronger than any Parkinson-control wrapper row. `Auditory vs standard` still produces extreme entropy and transition-sparsity effects, especially at `arrowcue`, and these rows remain orders of magnitude stronger than the disease-facing event candidates.

#figure(
  kind: table,
  table(
    columns: (2.1fr, 1.45fr, 1.0fr, 1.0fr, 0.85fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Comparison*], [*Left med*], [*Right med*], [*`d`*], [*BH-FDR `q`*]),
    [`9D entropy_rate`], [`standard_arrowcue` vs `auditory_arrowcue`], [`1.127`], [`0.432`], [`-4.731`], [`8.56e-25`],
    [`3D transition_sparsity`], [`standard_arrowcue` vs `auditory_arrowcue`], [`0.7231`], [`0.9554`], [`+4.211`], [`8.56e-25`],
    [`3D entropy_rate`], [`standard_all` vs `auditory_all`], [`1.208`], [`0.5118`], [`-4.012`], [`8.56e-25`],
    [`3D transition_sparsity`], [`standard_all` vs `auditory_all`], [`0.8021`], [`0.9514`], [`+3.461`], [`8.56e-25`],
  ),
  caption: [Task-canalization backdrop. Auditory-standard subtype effects remain far stronger than any disease-facing wrapper row.]
) <tab-task-boundary>

This boundary is the reason the disease-first claims must remain bounded. The new `10B` rerun improves the mechanistic target family, but it does not overturn the empirical fact that the task itself dominates the event-centered geometry in this bundle.

= Discussion

Three conclusions follow.

First, the disease-first rerun does change the *type* of event-centered Parkinson-control row that rises to the top. The strongest exploratory candidates are no longer simple entropy-collapse rows. They live in lagged family coupling, response asymmetry, recovery geometry, recurrence, and hidden-cost families. That is exactly the direction suggested by the canalization hypothesis and therefore counts as a useful mechanistic refinement.

Second, the current bundle still does not support a retained event-locked Parkinson biomarker. None of the wrapper disease rows survive BH-FDR, and the strongest raw coupling amplitudes are not specific under shuffle-null follow-up. The cleaner signal is the asymmetry row, not the amplitude row, which suggests that directional family choreography may be more informative than raw coupling magnitude.

Third, the stable disease layer remains global. Lower `m` and higher reachability ratios in Parkinson survive the rerun with essentially the same strength as before. The disease-first article therefore does not replace the previous result; it sharpens its interpretation. The task still defines the corridor, while disease may change how the corridor is traversed and exited.

= Limitations

1. No event-centered `Control vs Parkinson` row survives BH-FDR, so the wrapper findings remain exploratory.
2. The coupling shuffle-null shows that some raw coupling amplitudes are not specific to the true family choreography.
3. The bundle exposes no regional outputs, no cohort-anchor layer, and no external replication cohort.
4. `labels/stage` remains intentionally unusable as an event surface in this dataset, so all event inference depends on the behavior-enriched `raw_*` labels.
5. The current article-local wrapper includes exploratory trajectory variants such as path hysteresis, torsion, and return probability that are not yet repository-wide frozen standards.

= Conclusion

The disease-first `10B` rerun of `ds004574` does not produce a retained event-locked Parkinson biomarker, but it does shift the most interpretable exploratory rows toward lagged family coupling, response asymmetry, recovery geometry, and hidden cost. The strongest global Parkinson-control structure remains lower `m` and higher reachability, while the strongest event structure remains the old auditory-standard canalization. The most conservative conclusion is therefore that the oddball task still hides most disease information by forcing both groups into the same route, but the remaining disease-facing signal, where it exists, is more likely to reflect cost, lag, and asymmetric recovery than route choice alone.
