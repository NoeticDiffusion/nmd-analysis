#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S6 Changelog",
  short-title: "S6 Infant EEG changelog",
  subtitle: "Cohort-anchored age analysis, artifact masking, and robustness checks",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope and intent

This changelog is written for readers who want to know what has changed since the initial analysis release, both during self-review (`peer_review/pr_01.md`, `pr_02.md`) and during data-quality iteration on the underlying export.

= Changelog

== 2026-08-05: Initial cohort-anchored analysis release
- Audited the 70 H5 recordings from 22 children (`figshare_infant_eeg_20260805`): 68 `ok` and 2 `adjusted` geometry contracts, all retained under the standard invalidity policy.
- Froze the subject-balanced global IQR anchor `figshare_infant_eeg_global_cohort_all_visits_iqr_v2_1`, providing both subject- and cohort-anchored 3D/9D coordinate layers.
- Implemented the primary within-child MNJ/reachability robustness family and the primary cohort-coordinate GEE family (12 endpoints: 3D $m,d,e$ plus nine 9D coordinates).
- Wrote the initial manuscript and Supplements S1-S4.

== 2026-08-05: Self-review round 1 (`pr_01.md`, M1-M7)
- *M1/M2*: surfaced two previously undisclosed nominal (uncorrected) results in the within-child direct-age sensitivity subset and the 9D MNJ sensitivity family, which had not been reported in the manuscript despite being computed.
- *M3 (within/between decomposition)*: added a Neuhaus-Kalbfleisch-style decomposition to the primary cohort-coordinate GEE, separating within-child from between-child age association. Result: all 12 endpoints are driven by within-child change; no endpoint's between-child term is FDR-significant.
- *M4 (cluster-permutation robustness)*: added a 500-iteration child-cluster row-permutation check of the omnibus GEE Wald statistic, motivated by the known anti-conservative bias of GEE sandwich covariance at 22 clusters. Result: only 5 of 12 endpoints (later 6 of 12 after artifact masking, see below) survived this stricter, FDR-corrected check, versus 12/12 under the asymptotic GEE alone.
- *M5*: clarified in S1.2/S1.3 that within-child reachability is a strictly single-session estimate (no cross-visit or cross-child neighbor pooling).
- *Cohort-pooled reachability*: implemented a new, genuinely cohort-level reachability analysis (`05_cohort_pooled_reachability.py`), answering M5's explicit follow-up question. Leave-one-child-out local flow fields at each visit's own cohort coordinate; no FDR-supported age effect in any of 5 endpoints.
- *M6/M7*: fixed an "11-coordinate family" miscount (code and CSVs use 12) and a "subject-anchored" labeling error on what is actually a cohort-anchored MNJ/reachability computation (both found by a Grok 4.5 code-review pass).
- Filled in Supplement S4 (clinical summary), previously an unfilled generic template.

== 2026-08-05 (later same day): Artifact-masked re-export
- Upstream ingest updated to mask 715 publicly released BAD\_-interval artifact annotations (2,143.7 s total) at the sample level before epoching; any 8-s epoch overlapping a masked interval is dropped rather than bridged.
- Usable epoch pool fell from 6,929 to 5,265 (median 78.5/session, range 20-109, down from median 98/range 30-148). Re-froze the cohort anchor on the masked pool (new hash `45bbfa21...c301a89e`). Re-ran the full pipeline end-to-end against the new export `neuralmanifolddynamics_figshare_infant_eeg_20260805_132612`.
- Net effect: the primary cohort-coordinate GEE (R2) remained 12/12 FDR-supported and the weakest 3D endpoint (mobility) improved (FDR p 0.034 -> 0.011); the cluster-permutation check (M4) improved from 5/12 to 6/12 FDR-supported endpoints (gained 9D $m_e$); the primary forms of both local-dynamics robustness families (R4, R5) became cleaner after masking, with the two previously nominal within-child direct-age hits (`frobenius_norm_median`, `rotation_norm_median`, raw p=0.043-0.050) disappearing entirely (now raw p > 0.2), while the cohort-pooled direct-age sensitivity retained one separate nominal rotational-proxy hit (raw p=0.040).
- Regenerated the manuscript, S1-S4, and all figures from the new results (`results/figshare_infant_cohort_20260805_132612/`).

== 2026-08-06: Self-review round 2 (`pr_02.md`)
- *Headline-null overstatement fix*: the abstract, discussion, and conclusion previously stated the two local-dynamics robustness checks showed "no supported, or even nominal, age effect" after artifact masking. This was inconsistent with the manuscript's own Results R5 / Supplement S2.8 / S3.4, which report one nominal (uncorrected) hit in the cohort-pooled reachability direct-age-sensitivity subset (rotational proxy, raw p=0.040). Reworded all four headline locations (abstract, author summary, discussion, conclusion) and the equivalent passages in S4 to state the FDR-supported null precisely while explicitly retaining this one remaining nominal, non-FDR-supported exception.
- *Filled in Supplement S5* (glossary), previously an unfilled generic template: added definitions for MNPS, cohort/subject anchoring, the 3D and 9D coordinate families (including a code-to-meaning table for all nine 9D codes $m_a$, $m_e$, $m_o$, $d_n$, $d_l$, $d_s$, $e_e$, $e_s$, and $e_m$), MNJ, within-child vs. cohort-pooled reachability, GEE, the within/between decomposition, the cluster-permutation check, BH-FDR, direct-age sensitivity, and the nominal-vs.-FDR-supported distinction.
- *Rewrote Supplement S6* (this file), previously a mis-copied duplicate of the S4 clinical-summary template (wrong title, wrong content), as an actual dated changelog.
- Housekeeping: flagged (not yet actioned) that the two superseded pre-masking result trees (`results/figshare_infant_20260805/`, `results/figshare_infant_cohort_20260805/`) and their `smoke_export/` subfolders remain alongside the canonical `results/figshare_infant_cohort_20260805_132612/` export; the manuscript's own figure/data paths already point only to the canonical export.
- Clarified the S3.3 eligibility accounting: 2 children had only one visit, 20 contributed to the primary within-child family, and the direct-age subsets retained 18 children/36 visits after their additional age-source restriction.
- Recommended adding a conventional-qEEG comparator family (relative band power, band ratios, alpha-peak/median frequency, spectral/permutation entropy) as a further robustness/context check on the primary cohort-coordinate result, given how well-established age-related qEEG maturation is in this literature.

== 2026-08-06 (later same day): Conventional-EEG comparator pipeline implemented
- Confirmed the `..._132612` export already contains 34 `eeg_conventional_*` per-epoch columns (`tier1`, `complexity`, `connectivity` packs, per `config_ingest_figshare_infant_eeg.yaml`).
- Added `06_conventional_eeg_age.py` plus shared helpers (`conventional_eeg_medians`, `fit_spline_gee_family`) in `figshare_infant_support.py`, refactoring `03_cohort_coordinate_age.py` to reuse the same cohort-level GEE fitter for full method parity with the primary family. Added a `--with-conventional-eeg` flag to `run_infant_eeg_analysis.py`.
- First run (against the primary `..._132612` export) surfaced a real data gap, not a bug: all 16 `connectivity` columns were 100% missing (NaN) in all 70 sessions -- a raw per-epoch coverage issue, not an artifact of per-session aggregation. Added a not-testable guard (`fit_spline_gee`) so degenerate/all-missing endpoints are reported explicitly rather than crashing the family fit.
- A second H5 re-extraction, `..._20260806_122539` (same 5,265-epoch artifact mask, `connectivity` coverage fixed), landed the same day. Every shared numeric MNPS/MNJ/reachability session-metric column was confirmed bit-identical (max abs diff 0.0) between the two exports before use; only `06_conventional_eeg_age/` outputs come from the new export (`results/README.md`).
- Extracted the shared M3 (within/between decomposition) and M4 (child-cluster row-permutation) checks out of `03_cohort_coordinate_age.py` into `figshare_infant_support.py` (`fit_within_between_family`, `cluster_permutation_p`) and applied them to the conventional-EEG family too, confirming the refactor reproduces `03`'s original numbers exactly (max abs diff 0.0 on `wald_chi2`, `within_wald_chi2`, and `cluster_permutation_p`).
- Final numbers (18 non-connectivity endpoints at 100% coverage; 16 connectivity endpoints at 80-96% coverage after the fix): cohort-level GEE 24/34 FDR-supported; within/between decomposition shows the effect is overwhelmingly within-child (31/34 FDR-supported) not between-child (1/34); child-cluster permutation check (the same conservative M4 check as R2) supports only 5/34 (alpha frontal-central coherence mean/SD, beta/alpha ratio, relative beta/gamma power); within-child sign-permutation check (the R4/R5 estimator) supports 6/34, overlapping the permutation-robust set at the beta/alpha ratio and relative beta/gamma power. The two frontal-central coherence endpoints reach the most extreme test statistics in the entire study (raw p down to $10^-94$) and are flagged in the main text as plausibly reflecting an age-correlated non-neural confound given their 80% coverage, rather than reported as an unqualified coherence-maturation finding.
- Integrated as Results R6 in the main manuscript (with matching Abstract/Author Summary/Discussion/Limitations/Conclusion edits), Methods subsection "Conventional-EEG comparator family", S1.8, S2.10-S2.12, S3.6, and two new S5 glossary entries. `results/README.md` updated with the second-export provenance note. The runner now requires the coverage-fixed `_20260806_122539` export for R6 and a separate output tree.

== 2026-08-17: Peer-review round 3 polish
- Corrected the R6 within-child FDR range to 0.007--0.044 and disclosed that two comparator references analyse the same Figshare corpus, while Marshall et al. provides independent developmental-EEG context.
- Added the same coverage/export guard to the direct `06_conventional_eeg_age.py` entry point, tightened the author summary and clinician-facing coverage wording, and regenerated the SVG figures used by Typst.

== 2026-08-18: Literature expansion and OpenNeuro audit
- Expanded the infant-EEG bibliography with independent developmental EEG studies covering normative qEEG, source-space spectra, functional/effective connectivity, aperiodic and periodic activity, network maturation, entropy, and inter-individual variability.
- Added the OpenNeuro `ds004577` dataset record and Harmony et al. (2024) dataset article, while explicitly documenting that it is distinct from the analysed Figshare `5598814` release and was not pooled or used for the MNPS anchor.
- Corrected the Figshare dataset authors, repaired APPLESEED metadata, clarified same-corpus versus external evidence, and documented the literature/archive audit in the project diary.
