# Hypoglycemia and stratified EEG dynamics

This directory contains a paired reanalysis of public euglycemic and
hypoglycemic clamp EEG excerpts from 34 people with type 1 diabetes. The
article's focus is a condition-associated neural-dynamics signature and its
limits; it is not an empirical test of the Embodied Anchoring Principle.

## Dataset and archive audit

The source data record is the Zenodo deposit
`10.5281/zenodo.3465213`, *Detection of hypoglycemia using measures of EEG
complexity in type 1 diabetes patients*, associated with the original Entropy
article by Rubega et al. (2020). An OpenNeuro catalogue search performed on
18 August 2026 found no matching OpenNeuro dataset or dataset-specific
publication. OpenNeuro is therefore not a second source archive for this
analysis.

No script in this pipeline estimates cardiac, respiratory,
heartbeat-evoked, autonomic, ownership, or interoceptive-awareness variables.

## Empirical design

- Two five-minute scalp-EEG excerpts per participant: euglycemia and
  hypoglycemia.
- Paired primary contrast: hypoglycemia minus euglycemia.
- NeuralManifoldDynamics outputs: 3D and stratified 9D coordinates, 3D/9D
  Jacobians, exploratory reachability audit summaries, and raw EEG feature
  checks.
- Robustness: paired label-swap null and sensitivity excluding three
  hypoglycemia sessions with an adjusted geometry contract. The reachability
  surface is validity-limited under the frozen split-half criteria and is not a
  confirmatory endpoint.
- Scope boundary: the source bundle has no continuous clamp trajectory,
  participant-level glucose time series, recovery, behavioral performance,
  autonomic measures, or awareness subgroup metadata.

## Key files

- `manuscript.typ` — main article.
- `src/run_hypoglycemia_t1d_ndt.py` — maps source task labels to the
  condition column and executes the paired pipeline.
- `src/summarize_hypoglycemia_t1d_results.py` — exports article-local raw EEG
  sanity checks and paired results.
- `src/04_hypoglycemia_robustness.py` — paired label-swap null and
  adjusted-geometry sensitivity.
- `results/hypoglycemia_t1d_20260723/` — result tables and report.
- `S2_Supplementary_data.typ` and `S3_Supplementary_QC_Robustness.typ` —
  numerical tables and robustness documentation.

## Reproduction

From the repository root, after the required source H5 bundle and
`ndt-analysis` package are available:

```text
python articles/hypoglycemia_metabolic_anchoring/src/run_hypoglycemia_t1d_ndt.py
python articles/hypoglycemia_metabolic_anchoring/src/summarize_hypoglycemia_t1d_results.py
python articles/hypoglycemia_metabolic_anchoring/src/04_hypoglycemia_robustness.py
```

Compile the manuscript from this directory:

```text
typst compile manuscript.typ
```

## Interpretation boundary

The analysis tests a controlled metabolic condition contrast. It supports
neither a glucose dose-response nor a metabolic gate, a confirmatory
reachability collapse or expansion claim, a recovery trajectory, an
embodied-anchor mechanism, or direct inference about consciousness.
