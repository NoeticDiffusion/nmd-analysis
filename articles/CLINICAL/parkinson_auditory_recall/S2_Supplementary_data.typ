#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "Parkinson Supplementary Data",
  subtitle: "Auditory oddball anchor tables, group-supportive rows, and null visual comparison",
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

- compact auditory-primary anchors,
- detailed `auditory vs standard` rows,
- detailed `auditory vs pooled other_mean` rows,
- supportive `Control vs Parkinson` global rows,
- and the focused `auditory vs visual` negative-control note.

= Primary auditory anchors

#figure(
  kind: table,
  table(
    columns: (2.1fr, 1.5fr, 1.0fr, 1.0fr, 0.85fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Comparison*], [*Left med*], [*Right med*], [*`d`*], [*BH-FDR `q`*]),
    [`3D transition_sparsity`], [`other_mean` vs `auditory_all`], [`0.8767`], [`0.9514`], [`+3.376`], [`4.05e-25`],
    [`9D entropy_rate`], [`other_mean` vs `auditory_all`], [`0.7881`], [`0.4332`], [`-2.941`], [`4.14e-25`],
    [`9D peak_displacement`], [`other_mean` vs `auditory_all`], [`2.498`], [`1.512`], [`-2.096`], [`4.14e-25`],
    [`9D entropy_rate`], [`standard_arrowcue` vs `auditory_arrowcue`], [`1.127`], [`0.432`], [`-4.731`], [`3.97e-25`],
    [`global 3D m_median`], [`Control` vs `Parkinson`], [`0.0347`], [`0.0201`], [`-0.602`], [`0.0135`],
    [`reachability tube_q_ratio_h4_mean`], [`Control` vs `Parkinson`], [`0.2474`], [`0.2821`], [`+0.557`], [`0.0308`],
  ),
  caption: [Compact article-facing anchor set. The first four rows are event-primary; the final two are the supportive global Parkinson-control layer.]
) <tab-s2-primary-anchors>

= Detailed `auditory vs standard` rows

#figure(
  kind: table,
  table(
    columns: (2.05fr, 1.05fr, 1.05fr, 0.9fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Standard med*], [*Auditory med*], [*`d`*], [*BH-FDR `q`*]),
    [`3D transition_sparsity`], [`0.8021`], [`0.9514`], [`+3.461`], [`3.97e-25`],
    [`9D transition_sparsity`], [`0.8920`], [`0.9784`], [`+2.659`], [`3.97e-25`],
    [`3D entropy_rate`], [`1.2076`], [`0.5118`], [`-4.012`], [`3.97e-25`],
    [`9D entropy_rate`], [`1.1373`], [`0.4332`], [`-3.913`], [`3.97e-25`],
    [`3D peak_displacement`], [`3.306`], [`1.543`], [`-2.019`], [`3.97e-25`],
    [`9D peak_displacement`], [`3.516`], [`1.512`], [`-2.261`], [`3.97e-25`],
    [`3D path_length`], [`48.37`], [`6.147`], [`-1.898`], [`3.97e-25`],
    [`9D path_length`], [`130.82`], [`16.34`], [`-1.901`], [`3.97e-25`],
    [`3D tortuosity`], [`26.83`], [`4.577`], [`-1.123`], [`3.97e-25`],
    [`9D tortuosity`], [`26.28`], [`4.454`], [`-1.554`], [`3.97e-25`],
    [`9D hysteresis_area_mean`], [`1.386`], [`0.2956`], [`-1.544`], [`9.40e-25`],
    [`9D hysteresis_area_md`], [`2.074`], [`0.4352`], [`-1.246`], [`9.40e-25`],
  ),
  caption: [Highest-ranked subtype-collapsed `auditory vs standard` rows. The dominant pattern is lower entropy, shorter paths, smaller displacement, and more sparse transitions in auditory windows.]
) <tab-s2-auditory-standard>

The standard arm is therefore the main non-auditory comparator driving the article story. The same direction also appears consistently in the control-only and Parkinson-only stratified reruns reported in `S3`.

= Detailed `auditory vs pooled other_mean` rows

#figure(
  kind: table,
  table(
    columns: (2.1fr, 1.05fr, 1.05fr, 0.9fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*`other_mean` med*], [*Auditory med*], [*`d`*], [*BH-FDR `q`*]),
    [`3D transition_sparsity`], [`0.8767`], [`0.9514`], [`+3.376`], [`4.05e-25`],
    [`9D transition_sparsity`], [`0.9352`], [`0.9784`], [`+2.661`], [`4.14e-25`],
    [`3D entropy_rate`], [`0.8534`], [`0.5118`], [`-2.993`], [`4.05e-25`],
    [`9D entropy_rate`], [`0.7881`], [`0.4332`], [`-2.941`], [`4.14e-25`],
    [`3D peak_displacement`], [`2.486`], [`1.543`], [`-1.853`], [`4.05e-25`],
    [`9D peak_displacement`], [`2.498`], [`1.512`], [`-2.096`], [`4.14e-25`],
    [`3D path_length`], [`27.41`], [`6.147`], [`-1.893`], [`4.05e-25`],
    [`9D path_length`], [`73.47`], [`16.34`], [`-1.895`], [`4.14e-25`],
    [`3D hysteresis_area_mean`], [`1.063`], [`0.3320`], [`-1.566`], [`1.03e-24`],
    [`9D hysteresis_area_mean`], [`0.8802`], [`0.2956`], [`-1.532`], [`1.05e-24`],
  ),
  caption: [Top `auditory vs pooled other_mean` rows. The pooled non-auditory comparison remains strongly positive because the standard arm contributes much of the non-auditory baseline.]
) <tab-s2-auditory-other>

= Supportive `Control vs Parkinson` global rows

#figure(
  kind: table,
  table(
    columns: (2.35fr, 1.0fr, 1.0fr, 0.9fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Control med*], [*Parkinson med*], [*`d`*], [*BH-FDR `q`*]),
    [`global 3D m_median`], [`0.0347`], [`0.0201`], [`-0.602`], [`0.0135`],
    [`adaptive collapse q_ratio_h4`], [`0.2312`], [`0.2752`], [`+0.518`], [`0.0200`],
    [`reachability tube_q_ratio_h4_mean`], [`0.2474`], [`0.2821`], [`+0.557`], [`0.0308`],
    [`reachability q_ratio_h2_median`], [`0.5177`], [`0.5469`], [`+0.552`], [`0.0308`],
    [`reachability cone_q_ratio_h2_median`], [`0.5177`], [`0.5469`], [`+0.552`], [`0.0308`],
    [`reachability cone_q_ratio_h3_median`], [`0.3321`], [`0.3721`], [`+0.539`], [`0.0308`],
    [`reachability q_ratio_h4_median`], [`0.2312`], [`0.2752`], [`+0.518`], [`0.0308`],
    [`reachability tube_q_ratio_h4_median`], [`0.2312`], [`0.2752`], [`+0.518`], [`0.0433`],
    [`reachability median_min_eig_over_median_eig`], [`0.0207`], [`0.0169`], [`-0.473`], [`0.0433`],
    [`tier2_jacobian rel_mse_baseline_iqr`], [`0.0590`], [`0.0557`], [`-0.454`], [`0.0660`],
  ),
  caption: [Top global `Control vs Parkinson` rows from the standard layer. The disease effect is smaller than the event-primary layer and is concentrated in global `m` and reachability ratios.]
) <tab-s2-group-supportive>

= Focused negative-control note: `auditory vs visual`

The file `event_contrasts.csv` was also queried for `All_Auditory_vs_Visual`. No row survived `q < 0.1`. The best near-miss values remained broad and weak rather than concentrated into one dominant feature family.

#figure(
  kind: table,
  table(
    columns: (2.1fr, 1.0fr, 1.0fr, 0.9fr, 0.95fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Visual med*], [*Auditory med*], [*`d`*], [*BH-FDR `q`*]),
    [`3D noetic_action`], [`0.4817`], [`0.5078`], [`+0.050`], [`0.849`],
    [`3D noetic_action_potential`], [`0.3030`], [`0.3015`], [`+0.038`], [`0.849`],
    [`3D curvature_median`], [`2.827`], [`2.972`], [`+0.085`], [`0.849`],
    [`3D self_loop_rate`], [`0.02115`], [`0.01995`], [`-0.102`], [`0.849`],
    [`3D hysteresis_area_de`], [`0.2009`], [`0.2232`], [`-0.085`], [`0.849`],
    [`3D peak_displacement`], [`1.532`], [`1.543`], [`-0.106`], [`0.849`],
  ),
  caption: [Best `auditory vs visual` rows. The absence of BH-FDR-positive visual differences bounds the event story to a primarily `auditory vs standard` geometry shift.]
) <tab-s2-auditory-visual-null>

= Files

The tables in this supplement are backed by:

- `results/parkinson_auditory_recall_20260602/event_contrasts.csv`
- `results/parkinson_auditory_recall_20260602/article_metric_ranking.csv`
- `results/parkinson_auditory_recall_20260602/article_metric_summary.md`
- `results/parkinson_auditory_recall_20260602/standard_analysis/ds004574_contrast_results_20260602_120537.parquet`
