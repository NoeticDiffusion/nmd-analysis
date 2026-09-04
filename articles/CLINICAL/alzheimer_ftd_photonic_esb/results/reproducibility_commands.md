# Reproducibility commands

Regenerate local article outputs:

```powershell
python articles/CLINICAL/alzheimer_ftd_photonic_esb/src/build_esb_article_outputs.py
```

Regenerate the conventional comparator panel:

```powershell
python articles/CLINICAL/alzheimer_ftd_photonic_esb/src/build_esb_comparator_panel.py
```

Regenerate article figures:

```powershell
python articles/CLINICAL/alzheimer_ftd_photonic_esb/src/build_esb_figures.py
```

Run the full local pipeline:

```powershell
python articles/CLINICAL/alzheimer_ftd_photonic_esb/src/run_esb_followup_pipeline.py
```

Compile the manuscript:

```powershell
typst compile "articles/CLINICAL/alzheimer_ftd_photonic_esb/Evoked Structural Brittleness Under Photic Stimulation in Alzheimer Disease and Frontotemporal Dementia.typ"
```
