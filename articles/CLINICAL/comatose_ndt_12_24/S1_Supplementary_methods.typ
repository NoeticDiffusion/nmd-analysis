#import "../comatose_ndt/network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "Coma 12-24 h Methods",
  subtitle: "Processed-bundle contract, timing reconstruction, and fixed pilot metric families",
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

This supplement records the methods boundary for the current `12_24h` coma pilot. It is intentionally parallel to the early-window article under `articles/CLINICAL/comatose_ndt/`, but it is narrower in three ways:

1. the current late-window rerun is `part1`-only,
2. the processed root is mixed-bin rather than window-pure,
3. and the fixed article-facing metric family differs from the early-window paper.

The frozen article release that anchors this late-window manuscript line is archived on Zenodo.@langell2026_coma_v011

= Processed bundle contract

The stamped pilot reported here consumes the no-regional subject-anchored processed root:

- `J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260607_151559_no_regional_12_24h_subject_anchor`

The directory name is not treated as a trusted time-bin label. Instead the pilot rebuilds timing from the H5 timing contract, assigns runs to the `primary_12h` bins by run midpoint, audits the full export, and only then filters the geometry summaries to the true `12_24h` slice.

For the stamped `20260608_part1_noregional_subjectanchor` rerun:

- the full export contained `1575` H5 runs across `124` subjects,
- run-level timing used `time_reference` for `1561` runs and `wfdb_header_subject_anchor` fallback for `14`,
- `1561` runs had timing status `ok` and `14` were labeled `missing_or_invalid_start_end`,
- the run-level time-bin audit yielded `1412` runs in `0_12h`, `143` in `12_24h`, `11` in `24_48h`, and `9` in `72h_plus`,
- and the true inferential `12_24h` slice therefore settled at `143` runs from `97` subjects (`47 CPC 1`, `50 CPC 5`).

The filtered `mnps_summary_20260608_part1_noregional_subjectanchor_primary12h_true1224` bundle contains only `12_24h` rows, and all exported patient-level metric rows in that filtered bundle carry `time_reference_status = ok` and `run_anchor_source = time_reference`. The full-root fallback rows therefore do not enter the manuscript-facing late-window contrasts.

= Analysis stack

The local execution stack mirrors the early-window coma article while remaining article-local to `comatose_ndt_12_24/src/`:

- `icare_patient_timeline_analysis.py`
- `icare_mnps_summary_analysis.py`
- `icare_outcome_contrast_analysis.py`
- `reviewer_response_checks.py`
- `make_coma_figures.py`
- `compute_between_run_iqr_mad.py`
- `run_coma_12_24_pilot.py`

The configuration layer is recorded in `config/icare_ndt_analysis.yaml` and preserves the same `subject_anchored` coordinate contract as the broader coma line. Reproducibility commands are stored in `results/reproducibility_commands.md`.

The stamped pilot entry point used here was:

```text
python articles/CLINICAL/comatose_ndt_12_24/src/run_coma_12_24_pilot.py \
  --processed-root J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260607_151559_no_regional_12_24h_subject_anchor \
  --stamp 20260608_part1_noregional_subjectanchor \
  --workers 4
```

The repeated-run variability pass was then evaluated under both the strict and exploratory coverage thresholds:

```text
python articles/CLINICAL/comatose_ndt_12_24/src/compute_between_run_iqr_mad.py \
  --input-dir articles/CLINICAL/comatose_ndt_12_24/results/mnps_summary_20260608_part1_noregional_subjectanchor_primary12h_true1224 \
  --output-dir articles/CLINICAL/comatose_ndt_12_24/results/between_run_iqr_mad_20260608_part1_noregional_subjectanchor_true1224_min3 \
  --primary-time-bin 12_24h \
  --min-runs 3

python articles/CLINICAL/comatose_ndt_12_24/src/compute_between_run_iqr_mad.py \
  --input-dir articles/CLINICAL/comatose_ndt_12_24/results/mnps_summary_20260608_part1_noregional_subjectanchor_primary12h_true1224 \
  --output-dir articles/CLINICAL/comatose_ndt_12_24/results/between_run_iqr_mad_20260608_part1_noregional_subjectanchor_true1224_min2 \
  --primary-time-bin 12_24h \
  --min-runs 2
```

= Fixed measurement contract

As in the main coma article, the pilot does not redefine the `m`, `d`, and `e` coordinates inside the manuscript code. It consumes a fixed `NeuralManifoldDynamics` export contract under the `subject_anchored` chart and then summarizes `MNPS`, `MNJ`, and reachability rows downstream.@langell2026_mndm

The operational hierarchy is unchanged:

- `MNPS`: descriptive state-space spread,
- `MNJ`: local linear deformation,
- reachability: short-horizon nearby-future geometry.

What *does* change from the early-window article is the fixed five-metric reachability family carried into this late-window pilot.

= Fixed pilot metric families

The article-facing `12_24h` reachability family is:

- `tube_d_eff_median`
- `persistence_kappa_median`
- `persistence_log_eig_var_median`
- `tube_a_operator_norm_median`
- `tube_capture_gate_median`

Their operational readings are:

#figure(
  kind: table,
  table(
    columns: (1.9fr, 2.9fr),
    align: left,
    inset: 4pt,
    table.header([*Metric*], [*Operational reading in this pilot*]),
    [`tube_d_eff_median`], [effective dimensionality of the reachable tube; higher values indicate broader short-horizon directional support],
    [`persistence_kappa_median`], [stability of reachability anisotropy/condition structure across neighboring windows],
    [`persistence_log_eig_var_median`], [stability of the log-eigenspectrum spread across neighboring windows],
    [`tube_a_operator_norm_median`], [magnitude of the local linear transport operator],
    [`tube_capture_gate_median`], [transport-versus-innovation balance in the short-horizon tube],
  ),
  caption: [Operational readings for the five fixed reachability metrics carried into the `12_24h` pilot.]
) <tab-s1-metrics>

The supportive classical anchors are:

- `MNPS 3D`: `m_std`
- `MNPS 9D`: `m_e_std`
- `MNJ 3D`: `spectral_radius_median`, `frobenius_norm_median`
- `MNJ 9D`: supportive `spectral_radius_median`, `frobenius_norm_median`, `anisotropy_abs_eig_median`, `mdr_median`

The pilot therefore tests continuity of the measurement contract under a later anchor-relative window, not a de novo metric-search exercise.

= Timing and prefilter contract

The late-window inferential bundle is created in two stages.

1. `icare_patient_timeline_analysis.py` audits the full mixed-bin export under `primary_12h`.
2. `icare_mnps_summary_analysis.py` reuses that audit and applies `--prefilter-time-bin 12_24h`.

This separation is important. The full-export audit answers what is currently present in the no-regional root, whereas the inferential bundle answers what remains after restricting the analysis to the true `12_24h` slice. The manuscript therefore treats the root name as provenance only, not as an inferential guarantee.

= Between-run variability protocol

Between-run variability is summarized locally by `compute_between_run_iqr_mad.py` for the same five reachability metrics. For each patient and metric, the script computes:

- between-run IQR = `q75 - q25`,
- between-run MAD = median `|x_run - median(runs)|`.

Two coverage thresholds are used:

- strict threshold: at least `3` finite per-run values per patient,
- exploratory threshold: at least `2` finite per-run values per patient.

In the current rerun, only `5` subjects per metric meet the strict `>=3` threshold, so no strict-threshold contrasts are testable. Under the exploratory `>=2` threshold, `12` subjects per metric are analyzable (`8 CPC 1`, `4 CPC 5`), and those rows are reported as exploratory in the manuscript and `S2`.

= Endpoint and validation boundary

As in the main article, the endpoint is later `CPC 1` versus later `CPC 5`. This remains a recovery-linked association contrast rather than a pure assay of neural viability.@sandroni2021european

The current late-window pilot is further bounded by:

- `part1`-only coverage,
- no `part2` merge,
- no claim that the current export is a complete later-window cohort,
- mixed-bin provenance at the full-root level,
- anchor-relative rather than validated ROSC-relative timing,
- and limited repeated-run support in the true `12_24h` slice.

The `12_24h` manuscript should therefore be read as a bounded continuation of the coma geometry line under a fixed downstream contract, not as a finished pooled late-window study.

#bibliography("../comatose_ndt/cardiac_arrest_comatose_references.bib")
