#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "Parkinson 10B Supplementary QC",
  subtitle: "Residual-label exclusion, outlier follow-up, winsorization, and shuffle-null checks",
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

This supplement collects the focused robustness material for the disease-first article:

- exclusion of subjects with residual `raw_nan_onset_sec`,
- explicit `sub-112` follow-up,
- winsorized sensitivity,
- circular-shift family shuffle null for selected `10B-5` rows,
- and the remaining validity boundaries.

= Residual-label exclusion and outlier follow-up

The final bundle contains `26` subjects with positive residual `raw_nan_onset_sec` labels. The article-local wrapper excludes those events by construction, but a stricter subject-level exclusion was also rerun for the selected disease-facing rows.

The main event-facing trends remain present after exclusion, although not equally strongly across all families. In particular:

- `3D auditory_response asymmetry_me_tau2` strengthens from `d = +0.375` to `d = +0.576`,
- `9D auditory_arrowcue hysteresis_area_md` strengthens from `d = -0.397` to `d = -0.638`,
- `9D auditory_arrowcue noetic_action_jerk` strengthens from `d = -0.343` to `d = -0.553`.

#figure(
  kind: table,
  table(
    columns: (2.55fr, 1.15fr, 1.2fr, 1.15fr, 1.15fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*All subjects*], [*Exclude raw `nan`*], [*Exclude `sub-112`*], [*Winsorized*]),
    [`3D auditory_arrowcue coupling_dm_tau2`], [`d = +0.492`, `p = 0.0094`], [`d = +0.460`, `p = 0.0406`], [`d = +0.498`, `p = 0.0089`], [`d = +0.483`, `p = 0.0093`],
    [`3D auditory_response asymmetry_me_tau2`], [`d = +0.375`, `p = 0.0324`], [`d = +0.576`, `p = 0.0088`], [`d = +0.381`, `p = 0.0301`], [`d = +0.400`, `p = 0.0319`],
    [`9D auditory_arrowcue hysteresis_area_md`], [`d = -0.397`, `p = 0.0236`], [`d = -0.638`, `p = 0.0066`], [`d = -0.359`, `p = 0.0360`], [`d = -0.420`, `p = 0.0236`],
    [`9D auditory_all return_probability_tau2`], [`d = -0.333`, `p = 0.0218`], [`d = -0.278`, `p = 0.125`], [`d = -0.327`, `p = 0.0275`], [`d = -0.340`, `p = 0.0217`],
    [`9D auditory_arrowcue noetic_action_jerk`], [`d = -0.343`, `p = 0.0736`], [`d = -0.553`, `p = 0.0033`], [`d = -0.312`, `p = 0.107`], [`d = -0.314`, `p = 0.0753`],
  ),
  caption: [Selected disease-facing wrapper rows under residual-label exclusion, `sub-112` exclusion, and pooled winsorization.]
) <tab-s3-wrapper-stability>

The asymmetry and hysteresis rows are therefore directionally stable across all follow-up passes. The jerk row is more fragile: it strengthens after residual-label exclusion but weakens after explicit outlier follow-up.

= Shuffle-null control for family coupling

The new `10B-5` layer needs a control that breaks cross-family lag structure without destroying each family trace individually. For this purpose the robustness script applies independent circular shifts to `(bar(m), bar(d), bar(e))` inside each selected segment, repeats the null `32` times per segment, and aggregates the null values by medians.

The results split the candidate coupling rows into two classes.

1. `3D auditory_response asymmetry_me_tau2` collapses under the null (`d = +0.039`, `p = 0.848`), which argues that its observed direction depends on the real lag choreography.
2. Raw coupling-amplitude rows such as `3D auditory_arrowcue coupling_dm_tau2` and `9D auditory_all coupling_me_tau1` still show group differences under the null. Those rows are therefore not specific enough to carry a strong mechanistic claim by themselves.

#figure(
  kind: table,
  table(
    columns: (2.55fr, 1.15fr, 1.15fr, 1.1fr, 1.1fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Observed exclude raw `nan`*], [*Shuffle null*], [*Observed direction*], [*Interpretation*]),
    [`3D auditory_arrowcue coupling_dm_tau2`], [`d = +0.460`, `p = 0.0406`], [`d = +0.638`, `p = 0.0107`], [Parkinson `>` Control], [null-sensitive specificity not established],
    [`3D auditory_response asymmetry_me_tau2`], [`d = +0.576`, `p = 0.0088`], [`d = +0.039`, `p = 0.848`], [Parkinson `>` Control], [direction depends on true lag structure],
    [`9D auditory_all coupling_me_tau1`], [`d = +0.331`, `p = 0.0884`], [`d = -0.531`, `p = 0.0153`], [Parkinson `>` Control observed], [raw amplitude unstable under null],
  ),
  caption: [Circular-shift family shuffle null for selected `10B-5` rows. The asymmetry row is the cleanest signal because it collapses under the null, unlike the raw coupling amplitudes.]
) <tab-s3-shuffle-null>

= Supportive global disease layer remains stable

The retained standard-layer anchors remain directionally stable after `sub-112` exclusion and winsorization.

#figure(
  kind: table,
  table(
    columns: (2.35fr, 1.2fr, 1.2fr, 1.2fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Full cohort*], [*Exclude `sub-112`*], [*Winsorized*]),
    [`global 3D m_median`], [`d = -0.602`, `p = 0.0041`], [`d = -0.644`, `p = 0.0022`], [`d = -0.589`, `p = 0.0041`],
    [`reachability tube_q_ratio_h4_mean`], [`d = +0.557`, `p = 0.0025`], [`d = +0.565`, `p = 0.0022`], [`d = +0.559`, `p = 0.0025`],
  ),
  caption: [Supportive global anchors remain stable across the targeted outlier and winsorization follow-up.]
) <tab-s3-global-stability>

= Remaining boundaries

The current robustness package still leaves four open boundaries.

1. No event-facing wrapper row survives BH-FDR.
2. Some raw coupling amplitudes remain non-specific under the shuffle null.
3. The bundle has no regional outputs or external replication cohort.
4. The event geometry is still dominated by `auditory vs standard`, not by diagnosis.

= Files

The tables in this supplement are backed by:

- `results/parkinson_oddball_geometric_trajectory_20260602/selected_metric_robustness.csv`
- `results/parkinson_oddball_geometric_trajectory_20260602/selected_metric_robustness.md`
- `results/parkinson_oddball_geometric_trajectory_20260602/event_contrasts.csv`
