# ds004587 analysis outputs

This directory receives dated outputs under `ds004587_YYYYMMDD/`. Results are
created only from a discovered completed NMD export; scripts do not generate
placeholder numbers.

## Required source export

The handover records `data/raw/neuralmanifolddynamics_ds004587_20260711_235903`,
which is not bundled with this article. Point the pipeline to a completed
export that contains Parquet artifacts:

```powershell
$env:NMD_DS004587_ROOT = "J:\path\to\neuralmanifolddynamics_ds004587_*"
```

Each script stops with a `FileNotFoundError` if no usable source export exists,
or a `ValueError` if required fields are absent. Resolve that gate before
interpreting later outputs.

## Execution order

From the repository root:

```powershell
python articles/illusionGame_EAP/src/00_sanity_check.py
python articles/illusionGame_EAP/src/01_label_audit.py
python articles/illusionGame_EAP/src/02_anchor_validation.py
python articles/illusionGame_EAP/src/03_rest_vs_ig_geometry.py
python articles/illusionGame_EAP/src/04_eap_physio_coupling.py
python articles/illusionGame_EAP/src/05_illusion_strength_behavior.py
python articles/illusionGame_EAP/src/06_robustness_confound_audit.py
python articles/illusionGame_EAP/src/08_make_figures.py
```

`05_illusion_strength_behavior.py` is conditional: it requires joint
subject/trial/strength and behavioral fields in the discovered source.
`08_make_figures.py` requires a completed `03` result directory and writes
source links to `articles/illusionGame_EAP/figures/figure_source_manifest.csv`.

Every analysis directory includes `run_metadata.json`, identifying its actual
source artifact and creation time. Treat all outcomes as observational;
successful execution does not validate causal EAP claims.
