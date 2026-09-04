#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "Parkinson 10B Supplementary Data",
  subtitle: "Disease-facing 10B rows, supportive global anchors, and task-boundary tables",
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

This supplement collects the data-heavy material moved out of the main article:

- exploratory disease-facing wrapper rows,
- retained global Parkinson-control anchors,
- the dominant subtype-boundary rows,
- and a focused note on `auditory vs visual`.

= Compact disease-facing anchors

#figure(
  kind: table,
  table(
    columns: (2.35fr, 1.0fr, 1.0fr, 0.85fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Control med*], [*Parkinson med*], [*`d`*], [*BH-FDR `q`*]),
    [`3D auditory_arrowcue coupling_dm_tau2`], [`-0.0399`], [`0.0884`], [`+0.492`], [`0.643`],
    [`3D auditory_response asymmetry_me_tau2`], [`-0.0592`], [`0.0183`], [`+0.375`], [`0.643`],
    [`9D auditory_all coupling_me_tau1`], [`0.0994`], [`0.1728`], [`+0.412`], [`0.718`],
    [`9D auditory_arrowcue hysteresis_area_md`], [`0.4656`], [`0.3860`], [`-0.397`], [`0.718`],
    [`9D auditory_all return_probability_tau2`], [`0.1429`], [`0.1215`], [`-0.333`], [`0.718`],
    [`9D auditory_arrowcue noetic_action_jerk`], [`0.03459`], [`0.03036`], [`-0.343`], [`0.742`],
    [`global 3D m_median`], [`0.0347`], [`0.0201`], [`-0.602`], [`0.0090`],
    [`reachability tube_q_ratio_h4_mean`], [`0.2474`], [`0.2821`], [`+0.557`], [`0.0385`],
  ),
  caption: [Compact anchor set for the disease-first article. The first six rows are exploratory event-facing candidates; the final two are retained supportive global anchors.]
) <tab-s2-disease-anchors>

= Detailed disease-facing wrapper rows

#figure(
  kind: table,
  table(
    columns: (2.4fr, 1.0fr, 1.0fr, 0.9fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Control med*], [*Parkinson med*], [*`d`*], [*BH-FDR `q`*]),
    [`3D auditory_arrowcue coupling_dm_tau2`], [`-0.0399`], [`0.0884`], [`+0.492`], [`0.643`],
    [`3D auditory_all coupling_dm_tau2`], [`-0.0117`], [`0.0764`], [`+0.473`], [`0.643`],
    [`3D auditory_response asymmetry_me_tau2`], [`-0.0592`], [`0.0183`], [`+0.375`], [`0.643`],
    [`9D auditory_all coupling_me_tau1`], [`0.0994`], [`0.1728`], [`+0.412`], [`0.718`],
    [`9D auditory_arrowcue hysteresis_area_md`], [`0.4656`], [`0.3860`], [`-0.397`], [`0.718`],
    [`9D auditory_all hysteresis_area_md`], [`0.4949`], [`0.4051`], [`-0.371`], [`0.718`],
    [`9D auditory_all return_probability_tau2`], [`0.1429`], [`0.1215`], [`-0.333`], [`0.718`],
    [`9D auditory_response return_probability_tau2`], [`0.1429`], [`0.1305`], [`-0.361`], [`0.718`],
    [`9D auditory_arrowcue noetic_action_jerk`], [`0.03459`], [`0.03036`], [`-0.343`], [`0.742`],
    [`9D auditory_all noetic_action_jerk`], [`0.03423`], [`0.03143`], [`-0.312`], [`0.742`],
  ),
  caption: [Top disease-facing wrapper rows restricted to `auditory_all`, `auditory_arrowcue`, and `auditory_response`. None retain BH-FDR, but the leading families are coupling, recurrence, hysteresis, and jerk.]
) <tab-s2-disease-detail>

= Retained global Parkinson-control rows

#figure(
  kind: table,
  table(
    columns: (2.35fr, 1.0fr, 1.0fr, 0.9fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Control med*], [*Parkinson med*], [*`d`*], [*BH-FDR `q`*]),
    [`global 3D m_median`], [`0.0347`], [`0.0201`], [`-0.602`], [`0.0090`],
    [`adaptive collapse q_ratio_h4`], [`0.2312`], [`0.2752`], [`+0.518`], [`0.0200`],
    [`reachability q_ratio_h2_median`], [`0.5177`], [`0.5469`], [`+0.552`], [`0.0385`],
    [`reachability cone_q_ratio_h2_median`], [`0.5177`], [`0.5469`], [`+0.552`], [`0.0385`],
    [`reachability cone_q_ratio_h3_median`], [`0.3321`], [`0.3721`], [`+0.539`], [`0.0385`],
    [`reachability tube_q_ratio_h4_mean`], [`0.2474`], [`0.2821`], [`+0.557`], [`0.0385`],
    [`reachability tube_q_ratio_h4_median`], [`0.2312`], [`0.2752`], [`+0.518`], [`0.0513`],
    [`reachability median_min_eig_over_median_eig`], [`0.02067`], [`0.01685`], [`-0.473`], [`0.0513`],
  ),
  caption: [Top retained or near-retained global Parkinson-control rows from the standard layer.]
) <tab-s2-global-support>

= Task-boundary rows: `auditory vs standard`

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
    [`9D entropy_rate`], [`standard_all` vs `auditory_all`], [`1.137`], [`0.4332`], [`-3.913`], [`8.56e-25`],
    [`3D transition_sparsity`], [`standard_all` vs `auditory_all`], [`0.8021`], [`0.9514`], [`+3.461`], [`8.56e-25`],
    [`9D transition_sparsity`], [`standard_all` vs `auditory_all`], [`0.8920`], [`0.9784`], [`+2.659`], [`8.56e-25`],
    [`9D path_length`], [`standard_arrowcue` vs `auditory_arrowcue`], [`44.09`], [`4.907`], [`-2.461`], [`8.56e-25`],
    [`3D path_length`], [`standard_arrowcue` vs `auditory_arrowcue`], [`17.44`], [`1.913`], [`-2.445`], [`8.56e-25`],
  ),
  caption: [The task-boundary rows remain much stronger than the disease-facing wrapper rows. This is the main empirical reason the disease-first claims must stay bounded.]
) <tab-s2-task-boundary>

= Focused note: `auditory vs visual`

The negative-control picture remains largely unchanged. No `auditory vs visual` row reaches `q < 0.1`. The best new near-miss is now a coupling-asymmetry row rather than a classic path or entropy row.

#figure(
  kind: table,
  table(
    columns: (2.2fr, 1.0fr, 1.0fr, 0.9fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Visual med*], [*Auditory med*], [*`d`*], [*BH-FDR `q`*]),
    [`9D asymmetry_me_tau2`], [`0.0930`], [`0.0180`], [`-0.202`], [`0.630`],
    [`9D path_hysteresis`], [`0.8339`], [`0.7547`], [`-0.116`], [`0.956`],
    [`9D coupling_dm_tau2`], [`-0.0142`], [`0.0048`], [`+0.090`], [`0.956`],
    [`9D hysteresis_area_md`], [`0.4573`], [`0.4051`], [`-0.141`], [`0.956`],
    [`9D return_probability_tau3`], [`0.0500`], [`0.0417`], [`-0.086`], [`0.956`],
  ),
  caption: [Best `auditory vs visual` rows. None retain BH-FDR, so the event story remains primarily `auditory vs standard`.]
) <tab-s2-auditory-visual>

= Files

The tables in this supplement are backed by:

- `results/parkinson_oddball_geometric_trajectory_20260602/event_contrasts.csv`
- `results/parkinson_oddball_geometric_trajectory_20260602/article_metric_ranking.csv`
- `results/parkinson_oddball_geometric_trajectory_20260602/article_metric_summary.md`
- `results/parkinson_oddball_geometric_trajectory_20260602/standard_analysis/`
