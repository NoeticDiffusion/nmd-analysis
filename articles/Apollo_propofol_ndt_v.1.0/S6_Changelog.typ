// S6 Internal Changelog — Apollo propofol occupancy.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S6 Internal Changelog",
  short-title: "S6 Changelog - Apollo propofol occupancy",
  subtitle: "Internal analysis provenance and manuscript revision history",
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

Internal working document. Record how the manuscript numbers were obtained, which artifacts
were used, and which decisions affect interpretation. Do not copy internal experiment names or
workflow jargon into the public manuscript.

= Analysis provenance

- Dataset: Cambridge propofol sedation EEG, DOI 10.17863/cam.68959.
- Export: `neuralmanifolddynamics_Sedation-RestingState_20260918_075713`.
- Labels: article `metadata/datainfo.mat`, SHA-256 `ea8824f3…`.
- Occupancy: `results/v1_occupancy_20260921/` (`occupancy_relocation_20260921`).
- LOR join: `results/v1_lor_20260921/` (`occupancy_lor_20260921`).
- Matching exhibit: `results/v1_c3_anchor_20260921/` copied into the occupancy folder.
- Figures: `figures/occupancy/fig1_occupancy_trajectory`, `fig2_occupancy_paired_deltas`,
  `fig3_c3_match_collapse`; supplement `figS_occupancy_vs_hits`, `figS_lor_trajectory`.
- Addenda: `preregistration/addendum_20260921_{occupancy_primary,occupancy_lor}.md`.
- Bootstrap seed 20260920, 10 000 resamples. Confirmatory status:
  `exploratory_discovery_20260921_g4_not_locked`.

= Changelog

- 2026-09-20. Preregistration draft. G0–G4 specified. No confirmatory contrasts.
- 2026-09-21. G0–G2 collection (`results/ingest_20260920/`). 80/80 labels joined.
- 2026-09-21. Exploratory local-chart stage panel: no BH survivor; largest $|d_z|$ diffusion
  total $-0.70$. Coverage: L2/L3 partial; L4 empty.
- 2026-09-21. Level panel including Jacobian $alpha$: no BH survivor; L2/L3 $n=4$ at first
  sedation. Local-chart C3: 19/20 matched, Holm null; unmatched spread $d_z=-0.69$.
- 2026-09-21. Baseline-anchor C3: 7/20 matched, NOT_TESTABLE. Unmatched occupancy $d_z=+1.15$.
- 2026-09-21. Occupancy freeze (`sl_004`/`sl_005`). Later-sedation occupancy ordered secondary.
- 2026-09-21. LOR/ROR on frozen occupancy (`sl_006`/`sl_007`): 7/13 split recovered; the
  exploratory occupancy association gave Spearman $rho=-0.08$; the impaired arm was $n=7$.
- 2026-09-21. `sl_008` stops metric branching; manuscript draft from occupancy spine, three
  Results figures, LOR as a compact subsection.
- 2026-09-22. Bounded occupancy robustness branch (`apollo_occupancy_robustness_20260922_v1`):
  full-MAD decomposition, eight leave-one-feature-out variants, and sample-SD/normalised-IQR
  alternatives reused the frozen eligibility mask. All 11 variants retained $n=20$ at first
  sedation; the computational lock manifest hashes all 80 H5 inputs and isolated outputs.
- 2026-09-22 review fix. The preserved pre-review snapshot remains under
  `results/v1_occupancy_robustness_20260922/`; the corrected isolated run is under
  `results/v1_occupancy_robustness_20260922_reviewfix/` and reproduces all 80 finite frozen
  subject/phase cells (maximum absolute difference $3.55 times 10^(-15)$). Synthetic tests now
  cover non-finite later rows and out-of-range time gaps.
- Unresolved: G3 review, G4 lock, NDT-C3 (support collapse), independent replication.

= Manuscript revisions

- v0 draft (this file's companion `manuscript.typ`): first complete Typst draft. Three main
  figures; LOR table in Results; discovery screens in S2; clinical caution in S4.
- v1 revision (2026-09-22): reclassified occupancy as a post-hoc exploratory reporting line;
  removed confirmatory-primary language, limited the LOR interpretation to no evidence in this
  exploratory sample, corrected all-finite baseline scaling and invalid-scale handling, repaired
  the LOR table layout, and added the bounded computational robustness branch. See
  `reproducibility_manifest.json` and the robustness lock manifest for exact hashes.
