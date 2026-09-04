#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "Parkinson Supplementary Methods",
  subtitle: "Bundle contract, mixed-anchor design, and event-window wrapper details",
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

This supplement records the extended methods for the combined Parkinson cognitive workload article built from:

- `ds003509` (`simon_conflict`), and
- `ds003506` (`reinforcement_learning`).

Its purpose is to keep the dual-dataset and mixed-contract design explicit before the final quantitative inventories are inserted into the main paper and `S2-S4`. The primary empirical question is not whether these tasks yield one unified Parkinson workload signature, but how much disease-state geometry remains recoverable across two task surfaces under the same inferential policy.

= Processed bundle contract

The manuscript consumes two local NeuralManifoldDynamics exports:

- `data/raw/neuralmanifolddynamics_ds003509_20260608_151832`
- `data/raw/neuralmanifolddynamics_ds003506_20260608_163629`

Each bundle contains `84` H5 runs from `56` subjects:

- `28` control runs,
- `28` Parkinson `OFF` runs,
- `28` Parkinson `ON` runs.

Both bundles now expose:

- `coords_3d_subject_anchored`
- `coords_3d_cohort_anchored`
- `coords_9d_subject_anchored`
- `coords_9d_cohort_anchored`
- `regional_mnps/<network>/subject_anchored/...`
- `regional_mnps/<network>/cohort_anchored/...`
- `event_windows/*`

This explicit contract availability is what permits the same mixed-anchor logic across both tasks.

= Mixed-contract policy

The article follows the same inferential split as the repository's Parkinson ON/OFF trajectory paper:

- `Control vs Parkinson OFF` -> primary in `cohort_anchored`
- `Control vs Parkinson ON` -> primary in `cohort_anchored`
- `Parkinson OFF vs ON` -> primary in `subject_anchored`

The reason is methodological rather than aesthetic. Disease-state contrasts are between-subject questions that benefit from a shared reference frame. The paired medication contrast is a within-subject question and should remain in a subject-shared frame. This same split is applied to both tasks so the article can compare recoverability across task context rather than let the analysis contract drift between datasets.

= Task-specific event surfaces

The tasks are parallel in cohort structure but different in event semantics.

== Simon conflict (`ds003509`)

The event surface contains compact trigger-family labels such as:

- `training_stimulus_congruent`
- `training_stimulus_incongruent`
- `training_response_correct`
- `training_response_incorrect`
- `training_feedback_reward`
- `training_feedback_punishment`
- `test_stimulus_easy`
- `test_stimulus_direct_conflict`
- `test_stimulus_relative_conflict`
- `test_response_correct`
- `test_response_incorrect`

The article-local wrapper also creates collapsed family surfaces such as `training_all`, `test_all`, `training_feedback_all`, and `test_conflict_all`.

== Reinforcement learning (`ds003506`)

The event surface contains compact choose/match trigger families such as:

- `choose_instruction`
- `choose_stimulus`
- `choose_response_left`
- `choose_response_right`
- `choose_feedback_reward`
- `choose_feedback_punishment`
- `match_instruction`
- `match_stimulus`
- `match_response_left`
- `match_response_right`
- `match_feedback_reward`
- `match_feedback_punishment`
- `match_feedback_error`

The wrapper also creates collapsed families such as `choose_all`, `match_all`, `choose_feedback_all`, `match_feedback_all`, and reward / punishment / timeout / error aggregates.

= Standard and wrapper execution

For each dataset, the stamped analysis ran four linked passes.

1. A standard `ndt-analysis` pass under `subject_anchored`.
2. A standard `ndt-analysis` pass under `cohort_anchored`.
3. An article-local event wrapper under `subject_anchored`.
4. An article-local event wrapper under `cohort_anchored`.

The standard layer exports global and regional `MNPS 3D`, `MNPS 9D`, Jacobian, and reachability summaries. The wrapper layer adds path length, tortuosity, peak displacement, hysteresis, recovery residual, entropy-rate, irreversibility, transition sparsity, and noetic-action summaries in the same coordinate spaces.

= Result directories

The stamped result targets are:

- `articles/CLINICAL/parkinson_cognitive_workload_ON_OFF/results/parkinson_simon_conflict_20260608`
- `articles/CLINICAL/parkinson_cognitive_workload_ON_OFF/results/parkinson_reinforcement_learning_20260608`

These directories now hold:

- `standard_cleaned_subject/`
- `standard_analysis_subject/`
- `standard_cleaned_cohort/`
- `standard_analysis_cohort/`
- `event_metrics_subject/`
- `event_metrics_cohort/`
- `wrapper_subject/`
- `wrapper_cohort/`
- `analysis_summary.md`
- `primary_standard_contrasts.csv`
- `primary_event_contrasts.csv`
- wrapper summaries such as `wrapper_subject/wrapper_event_summary.md` and `wrapper_cohort/wrapper_event_summary.md`
- stamped subject- and cohort-level analysis parquets
- and pipeline manifests for the stamped article-facing passes.
