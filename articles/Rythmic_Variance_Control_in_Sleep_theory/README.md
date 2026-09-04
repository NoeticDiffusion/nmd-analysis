# aa_template

Generic article template for the NoeticDiffusion repository. Copy this folder to start a new article.

## Contents

```
aa_template/
  template_eLife.typ                  shared Typst engine (netn-template, clean-table, netn-box) - normally do NOT edit
  manuscript.typ                      main article template (generic headings + placeholder text)
  S1_Supplementary_methods.typ        supplementary methods template
  S2_Supplementary_data.typ           supplementary data tables template
  S3_Supplementary_QC_Robustness.typ  supplementary QC / robustness template
  S4_Supplementary_Clinical.typ       clinician-facing summary template
  S5_Glossary.typ                     shared glossary template
  references.bib                      starter bibliography (section-comment layout)
  README.md                           this file
  figures/                            figures (+ figures/conceptual/ for conceptual panels)
  handover/                           pipeline run logs / handover notes
  peer_review/                        adversarial self-review notes (pr_NN.md)
  sciencelead/                        science-lead verdicts (NNN.md)
  results/                            pipeline result CSVs / outputs
  src/                                analysis scripts
  old_template/                       legacy templates (untouched)
```

## How to start a new article

1. Copy this folder to `articles/<new article name>/`.
2. Rename `manuscript.typ` to the article title (e.g. `Walking-State Geometry Separates Parkinson Disease from Controls.typ`), matching the convention used by other articles in this repository.
3. In the renamed file, fill in the `#show: netn-template.with(...)` metadata block: `title`, `short-title` (<= 70 chars), `subtitle`, `authors`, `affiliations`, `corresponding-author`, `keywords` (<= 6), `article-type`, `abstract`, `author-summary`, `author-contributions`, `funding-info`, `data-availability`, `competing-interests`.
4. Replace the placeholder `[...]` section text and placeholder tables with the article's content. Keep or delete the `Theory` / `Embodied Anchoring Principle` and `R5` / `R6` subsections as appropriate.
5. Rename the `S1`-`S5` supplement files only if the article uses a different supplement scheme; otherwise fill in their placeholders.
6. Populate `references.bib` with the references actually cited, keeping the section-comment layout.
7. Drop figures into `figures/` (and `figures/conceptual/`), pipeline outputs into `results/`, analysis scripts into `src/`.
8. Record pipeline runs in `handover/`, adversarial self-review in `peer_review/`, science-lead verdicts in `sciencelead/`.

## Building

Compile any `.typ` file with Typst, e.g.:

```
typst compile manuscript.typ
```

The `#bibliography("references.bib", style: "apa")` call at the end of each file requires `references.bib` to be present in the same folder (it is, in this template).

## Notes

- The shared engine `template_eLife.typ` is generic; edit it only if you need to change page layout, table style, or box style for all articles derived from this template.
- Placeholder author is `Robin Langell, Langell Konsult AB, Vallentuna, Sweden` - change as needed.
- Placeholder text is in English, matching the language of the existing articles.
