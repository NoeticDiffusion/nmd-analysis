#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "Parkinson Supplementary QC",
  subtitle: "Mixed-contract defensibility, event-window consequences, and negative-result boundaries",
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

This supplement records the review-facing caution and robustness layer for the combined cognitive workload article.

The core aim is to show that the final manuscript is not simply reusing one task pattern twice, but is instead testing how much disease-state geometry remains recoverable across two task contexts under one fixed inferential policy. The observed result pattern is asymmetric rather than dual-positive: Simon conflict carries the broader corrected signal, reinforcement learning carries a thinner and more classically exposed signal, and the event wrapper is negative in both datasets.

The current robustness outputs are written under:

- `results/parkinson_simon_conflict_20260605/additional_qc_20260605/`
- `results/parkinson_reinforcement_learning_20260605/additional_qc_20260605/`

= Robustness blocks

== Contract defensibility

The mixed-contract rule remained defensible after the full result pass.

- `cohort_anchored` remained the correct primary frame for disease-state contrasts because essentially all retained rows against controls lived in the cohort-anchor standard layer.
- `subject_anchored` remained the correct primary frame for the paired medication contrast even though the paired branch was weak, because the relevant question is still within-subject change rather than between-subject separation.

The robustness summaries strengthened that split rather than undermining it. In both datasets, focal standard-layer rows showed leave-one-subject-out sign consistency of `1.0`. The main disease-state rows also remained stronger than their permutation nulls:

- `ds003509`: `global e_m_median`, `q_ratio_h4`, and `persistence_log_eig_var_median` each survived the standard permutation null with empirical `p` values between `0.0078` and `0.0155`.
- `ds003506`: retained alpha and global `d_s` rows each survived the standard permutation null with empirical `p = 0.0078`.

The two datasets therefore differed in strength, not in which contract best matched the inferential problem. `ds003509` retained a broad cohort-anchor disease-state inventory and only a small subject-anchor paired inventory at `q < 0.1`. `ds003506` retained a thinner cohort-anchor disease-state inventory and no subject-anchor paired inventory at `q < 0.1`. That asymmetry argues for keeping the mixed-contract policy rather than collapsing all questions into one coordinate frame.

== Event-window consequences

The article-local wrapper depends on `event_windows/*` and therefore asks a stricter question than the standard layer: whether task-bounded trajectory summaries survive multiplicity correction on top of the standard exports.

The answer in this manuscript is negative. No event-wrapper row survived `q < 0.1` in either `ds003509` or `ds003506`. The best raw event-layer q-values were still far from the standard retained range:

- `ds003509`: best event row `q = 0.473` (`Control vs Parkinson ON`, temporal `hysteresis_area_de`, `test_response_all`),
- `ds003506`: best event row `q = 0.399` (`Control vs Parkinson OFF`, global `hysteresis_area_de`, `match_feedback_punishment`).

The circular time-shift null reinforces that caution rather than rescuing the event story:

- `ds003509`: `test_response_all / hysteresis_area_de` had observed `d = 1.002`, but the empirical time-shift null remained non-supportive (`p = 0.2`).
- `ds003506`: `match_feedback_punishment / hysteresis_area_de` had observed `d = 0.604`, but again failed the time-shift null (`p = 0.2`).

The key caution is therefore twofold. First, the wrapper operates on processed trajectory windows, not raw single-trial ERP reconstructions. Second, even the best exploratory event rows did not survive a null that preserves within-run autocorrelation while destroying event alignment.

== Negative-result boundaries

This manuscript requires explicit restraint in three places.

1. `ds003509` yields broad disease-state geometry but only weak paired medication rows. The paired Simon story should therefore remain secondary and hypothesis-generating.
2. `ds003506` yields a meaningful OFF-state signal, but it is much thinner than Simon conflict and partially dominated by classical alpha-sensitive rows. That bounds any claim that reinforcement learning exposes a comparably broad geometric Parkinson state axis.
3. Both tasks fail to retain event-wrapper rows after correction. Those rows may still be useful for exploratory follow-up, but they should not be written as validated task-dynamic endpoints.

== Sidecar checks

The current stamped result pass already includes four concrete sidecar observations.

1. `ds003509` geometry remained modestly stronger than the best classical sidecars.
   - `Control vs Parkinson OFF`: geometry minus classical `|d|` gap `= 0.242`
   - `Control vs Parkinson ON`: geometry minus classical `|d|` gap `= 0.068`
2. `ds003506` was more classically exposed.
   - `Control vs Parkinson OFF`: geometry minus classical `|d|` gap `= -0.049`, meaning the best alpha row slightly exceeded the best geometry row
3. Several focal rows in both datasets aligned strongly with classical sidecars even when they remained geometrically interesting.
   - `ds003509`: `q_ratio_h4` and `persistence_log_eig_var_median` both showed strong correlations with classical metrics
   - `ds003506`: global `d_s_mean` and `d_s_median` aligned very strongly with theta/alpha-ratio sidecars
4. The exploratory reachability-like RL rows were not pure noise.
   - `persistence_tau_log_det_median` and `tube_log_det_split_half_a_median` both had leave-one-subject-out sign consistency `= 1.0`, and both outperformed their standard permutation nulls (`p = 0.0155`)

These sidecars matter because they sharpen the asymmetry between the tasks. Simon conflict remains a geometry-first result with secondary classical overlap. Reinforcement learning remains a real OFF-state result, but one whose strongest disease-state axis is at least partly shareable with conventional EEG summaries. Cross-fit was not attempted, because the present cohort size would make that check more fragile than clarifying.
