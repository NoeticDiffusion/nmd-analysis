# Apollo propofol NDT v1.0

Exploratory secondary analysis of Cambridge propofol sedation EEG
@chennu2016propofol in a frozen NeuralManifoldDynamics export. Occupancy (baseline-fixed
spectral relocation) is the article's descriptive spine and was selected post hoc; analyses are
not G4-locked. The LOR analysis reports exploratory associations and does not establish absence
of an association.

## Manuscript

- `manuscript.typ` — main article (compile with Typst)
- `S1_Supplementary_methods.typ` — occupancy, matching, LOR rule
- `S2_Supplementary_data.typ` — tables, LOR scatter, discovery screens
- `S3_Supplementary_QC_Robustness.typ` — support and testability
- `S4_Supplementary_Clinical.typ` — clinician-facing caution
- `S5_Glossary.typ`
- `S6_Changelog.typ` — internal provenance
- `reproducibility_manifest.json` — verified base commit, artifact paths, existing hashes, and
  raw-data hash limitations
- `references.bib`

```
typst compile manuscript.typ
```

## Figures

`figures/occupancy/`: Fig. 1 trajectory, Fig. 2 paired deltas, Fig. 3 match collapse.
Supplement: occupancy vs hit count; LOR-split trajectory.

## Results (frozen)

- Occupancy: `results/v1_occupancy_20260921/`
- Occupancy robustness branch: `results/v1_occupancy_robustness_20260922_reviewfix/`
- LOR join: `results/v1_lor_20260921/`
- Labels/support: `results/ingest_20260920/`

The collection and analysis manifests in these directories record the frozen export, label hash,
occupancy/LOR input hashes, a pinned example H5 hash, and the ingest sidecar hashes. The
robustness lock manifest additionally hashes all 80 source H5 files, the analysis source, plan,
and isolated outputs. The
article-local `reproducibility_manifest.json` records the exact repository base commit
(`d1c7fcedfb92c34162437fe11cdb35aa64620018`) and explains that the present article revision is
uncommitted and that the existing collection manifest does not hash every raw H5 file. No release
archive or additional DOI is claimed for this working-tree revision.

## Analysis code

`src/apollo_*.py`, tests in `tests/`. Preregistration draft and addenda in
`preregistration/`. Science-lead notes in `sciencelead/`.
