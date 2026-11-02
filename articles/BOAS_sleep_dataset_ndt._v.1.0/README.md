# aa_template

Generic article template for the `nmd-analysis` repository. Copy this folder to start a new article.

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
  S6_Changelog.typ                    internal development / revision history
  references.bib                      starter bibliography (section-comment layout)
  README.md                           this file
  figures/                            figures (+ figures/conceptual/ for conceptual panels)
  handover/                           pipeline run logs / handover notes
  peer_review/                        adversarial self-review notes (pr_NN.md)
  sciencelead/                        science-lead verdicts (NNN.md)
  results/                            pipeline result CSVs / outputs
  src/                                analysis scripts + contrast_config.yaml
  old_template/                       legacy templates (untouched)
```

## How to start a new article

1. Copy this folder to `articles/<new article name>/`.
2. Rename `manuscript.typ` to the article title (e.g. `Walking-State Geometry Separates Parkinson Disease from Controls.typ`), matching the convention used by other articles in this repository.
3. In the renamed file, fill in the `#show: netn-template.with(...)` metadata block: `title`, `short-title` (<= 70 chars), `subtitle`, `authors`, `affiliations`, `corresponding-author`, `keywords` (<= 6), `article-type`, `abstract`, `author-summary`, `author-contributions`, `funding-info`, `data-availability`, `competing-interests`.
4. Replace the placeholder `[...]` section text and placeholder tables with the article's content. Keep or delete the `Theory` / `Embodied Anchoring Principle` and `R5` / `R6` subsections as appropriate.
5. Rename the `S1`-`S5` supplement files only if the article uses a different supplement scheme; otherwise fill in their placeholders.
6. Fill in `S6_Changelog.typ` with the internal analysis provenance, result history, decisions, reviews, and manuscript revisions. Keep it internal unless it has been deliberately sanitized.
7. Populate `references.bib` with the references actually cited, keeping the section-comment layout.
8. Drop figures into `figures/` (and `figures/conceptual/`), pipeline outputs into `results/`, analysis scripts into `src/`.
9. Record pipeline runs in `handover/`, adversarial self-review in `peer_review/`, science-lead verdicts in `sciencelead/`.

## Building

Compile the renamed manuscript or any supplement with Typst, e.g.:

```
typst compile "Walking-State Geometry Separates Parkinson Disease from Controls.typ"
```

## Starting a contrast analysis

`src/contrast_analysis.py` is a small, configuration-driven starting point for
condition contrasts. Copy the template folder, then edit
`src/contrast_config.yaml` before running it:

```bash
python src/contrast_analysis.py --config src/contrast_config.yaml
```

The input is a CSV or Parquet table in long format, with one row per
`unit_id`, `condition`, and `measure`, and a numeric `value` column. Configure
the dataset folder and file, input column names, optional exact-match filters,
measures, and one or more comparisons in the YAML file. Paths in that file are
resolved relative to the YAML file. Each comparison states its design as
`paired` or `independent`; the reported direction is always
`condition_b - condition_a`.

Repeated rows for the same unit, condition, and measure are rejected. Choose
and document any recording/session reduction upstream using the study's
predefined measurement rules. Missing or non-finite values remain missing and
are counted; paired summaries use only complete unit pairs. Outputs include a
descriptive summary, a paired unit-level table, and a provenance manifest.
The script does not select inferential estimators, compute p-values or
confidence intervals, or scientifically qualify the results. Add those steps
only after the article has specified its contrast, support, missingness,
estimator, and interpretation rules.

## Auditing data coverage

Run `src/coverage_audit.py` with the same configuration to list missing
unit-condition-measure rows, rows with missing values, duplicate rows, and
observations outside an expected inventory:

```bash
python src/coverage_audit.py --config src/contrast_config.yaml
```

For a complete expected-support check, set
`coverage.expected_inventory_file` to a CSV or Parquet file containing one row
per expected `unit_id` and `condition` assignment. Include the configured
measure column when expected measures differ by assignment; otherwise the
script expects every configured measure for each assignment. Paired designs
need both expected conditions listed for every unit. Keep the inventory
consistent with the same cohort/session filters as the data.

Without an inventory, the audit checks missing condition-measure cells for
observed units (both conditions for paired designs) and missing values in
observed rows. It cannot detect units absent from the input entirely. The
coverage manifest records this limitation. Add `--fail-on-incomplete` in a
pipeline or manual check when an incomplete audit should return a non-zero
exit code.

The `#bibliography("references.bib", style: "apa")` call at the end of each file requires `references.bib` to be present in the same folder (it is, in this template).

## Notes

- The shared engine `template_eLife.typ` is generic; edit it only if you need to change page layout, table style, or box style for all articles derived from this template.
- Placeholder author is `Robin Langell, Langell Konsult AB, Vallentuna, Sweden` - change as needed.
- Placeholder text is in English, matching the language of the existing articles.
- `S6_Changelog.typ` is an internal audit trail for analysis provenance, result history, decisions, and manuscript revisions. Keep internal experiment names and repository workflow jargon there rather than in `manuscript.typ` or public S1-S5 supplements. Do not include S6 in a public submission package unless it has been deliberately sanitized.
