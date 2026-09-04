#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Block-Jacobian Coupling in Early Cardiac-Arrest Coma",
  short-title: "Block-Jacobian Coupling in Coma",
  subtitle: "Interim `part1` discovery results with `part2` verification pending",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "cardiac-arrest coma",
    "I-CARE",
    "EEG",
    "block Jacobian",
    "family coupling",
    "NeuralManifoldDynamics",
  ),
  article-type: "Research Article / Draft Manuscript Shell",
  abstract: [
    This draft defines a standalone follow-up that tests whether family-level blocks of the repaired `9 x 9` Jacobian differ between later `CPC 1` and later `CPC 5` patients during the first `12 h` after EEG-anchor in the I-CARE cohort. The scientific goal is narrower than in the scalar `9D` Jacobian paper: to ask whether within-family and cross-family coupling patterns carry outcome-linked structure that is not visible in whole-matrix scalar summaries alone. The current article-local `part1` discovery export retains all `141` extreme-outcome patients (`71 / 70`) despite `88` upstream failed groupings, and its clearest provisional signal is lower diagonal block Frobenius magnitude in better-outcome patients (`d = -0.326`, `p = 4.13e-4`). Lower `ee`, `dd`, and `ed` block Frobenius summaries also appear in `CPC 1`, while directional asymmetry remains exploratory. Because `part2` verification and pooled synthesis are still pending, the current manuscript should be read as an interim discovery-side result rather than as a replication-complete final article.
  ],
  author-summary: [
    The main reachability paper asked whether short-horizon reachable geometry differs by later outcome, and the scalar `9D` Jacobian paper asks whether whole-matrix local-linear summaries add a complementary signal. This follow-up is narrower. It asks whether family-to-family coupling structure inside the repaired `9D` Jacobian carries outcome-linked information during the same early coma window. The current `part1` discovery export suggests that better-outcome patients have lower diagonal and selected cross-family block magnitude, especially in Frobenius-like summaries, but the manuscript still treats those as provisional block candidates until `part2` verification is available.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Analysis Design, Writing, and Editing.],
  funding-info: [Funding information will be inserted in the submission version.],
  data-availability: [The underlying I-CARE dataset is available through PhysioNet version `2.1` at https://doi.org/10.13026/m33r-bj81. The current article-local `part1` block-Jacobian wrapper outputs are stored under `articles/CLINICAL/comatose_block_jacobian/results/mnps_summary_20260528_part1_block_jacobian_cpc15_primary12h/` and `articles/CLINICAL/comatose_block_jacobian/results/block_pilot_20260528_part1_cpc15_primary12h/`. `part2` verification outputs and pooled synthesis are still pending.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

= Introduction

The main coma reachability paper already established that early geometry in the first monitored EEG hours separates later `CPC 1` from later `CPC 5` patients in the I-CARE cohort and its PhysioNet dataset release.@langell2026_reachability, @amorim2023icare, @PhysioNet-i-care-2.1, @sandroni2021european, @nolan2025postresuscitation The scalar `9D` Jacobian follow-up then asks whether whole-matrix local-linear summaries such as spectral radius and Frobenius norm add a complementary signal inside the same `0-12 h` window.

This manuscript asks a narrower question. Rather than collapsing each repaired local `9 x 9` Jacobian to whole-matrix scalars, it treats the Jacobian as a family-structured object. The repaired `9D` state space groups coordinates into three `3D` families (`m`, `d`, `e`), making it natural to partition each local Jacobian into a `3 x 3` grid of `3 x 3` family blocks. That construction can, in principle, separate within-family deformation from cross-family coupling and test whether outcome-linked structure is concentrated on specific family-to-family pathways rather than only in global matrix magnitude.

As in the sibling coma papers, the aim is not to claim a bedside-ready neuroprognostic model, a direct measure of consciousness, or a pure neural-viability assay. The narrower goal is to define an auditable block-Jacobian analysis contract for the first `12 h` after EEG-anchor, while keeping the clinical interpretation conservative.

#netn-box(title: [Core question])[
  During the first `12 h` after EEG-anchor, do later `CPC 1` and later `CPC 5` patients differ in repaired block-Jacobian coupling structure in a way that replicates across the `part1` / `part2_140sub_9d` split?
]

= Cohort and provenance scope

This draft remains restricted to the same `9D`-enabled source bundles used by the scalar `9D` Jacobian follow-up, because those are the dated cohorts that actually support a symmetric repaired `9D` comparison. At the moment, however, only `part1` has an article-local block export; `part2` rerun and pooled synthesis remain pending.

1. `part1`: `timeline_analysis_20260524_part1_primary12h_9d` + `mnps_summary_20260524_part1_primary12h_9d_targeted`
2. `part2`: `timeline_analysis_20260523_part2_primary12h_9d` + `mnps_summary_20260523_part2_primary12h_9d`

The intended pooled synthesis will concatenate only non-overlapping `part1` and `part2` subject-timebin rows after explicit subject and run overlap checks, mirroring the provenance discipline used in the sibling coma manuscripts.

#figure(
  kind: table,
  table(
    columns: (2.4fr, 1.25fr, 1.25fr, 1.45fr),
    align: left,
    inset: 5pt,
    table.header([*Bundle item*], [*`part1` `9D`*], [*`part2` `9D`*], [*Planned pooled synthesis*]),
    [Analyzable subjects in local `0-12 h` index], [161], [140], [301],
    [Extreme-outcome `CPC 1 / CPC 5` subset], [141 (`71 / 70`)], [140 (`70 / 70`)], [281 (`141 / 140`)],
    [`9D` coordinates present in source run manifest], [yes], [yes], [yes by construction],
    [Article-facing block export status], [interim `part1` discovery export available], [pending rerun], [pending],
    [Role in this manuscript], [current discovery-side result], [planned verification], [planned synthesis after overlap audit],
  ),
  caption: [Current cohort scope for the standalone block-Jacobian article. `part1` now has an article-local discovery export, whereas `part2` verification and pooled synthesis remain pending.]
) <tab-block-scope>

== Outcome interpretation

The primary endpoint remains later `CPC 1` versus later `CPC 5`, chosen to sharpen outcome separation while preserving compatibility with the sibling coma papers.@rittenberger2011cpc The interpretive caution is the same here as elsewhere in the coma line: `CPC 5` intersects with death, systemic illness severity, treatment limitation, and potentially withdrawal-of-life-sustaining therapy rather than representing a pure neural recovery assay.@rajajee2023neuroprognostication, @nolan2025postresuscitation Until article-facing metadata include explicit WLST and time-of-death annotations, any observed block-coupling effect should be read as recovery-associated geometry rather than as a pure neural-viability signal.

= Methods

== Primary analysis contract

As in the sibling coma manuscripts, the primary time bin is the first `12 h` after EEG-anchor and the primary unit of inference is the patient.@westhall2016standardized, @ruijter2019early, @hofmeijer2015early The planned inferential contrast is later `CPC 1` versus later `CPC 5`.

This manuscript is intentionally narrower than the scalar `9D` Jacobian paper. It will test block-Jacobian structure only. Whole-matrix scalar summaries such as spectral radius, Frobenius norm, `mdr`, or rotational power may be referenced as context in Discussion, but they are not the primary article-facing targets here.

== Block-Jacobian definition

For each analyzable local window, let $J_t in RR^(9 times 9)$ denote the repaired local Jacobian on the stratified `9D` state space. Reorder the coordinates into the three `3D` families `m`, `d`, and `e`, then partition `J_t` into a `3 x 3` grid of `3 x 3` blocks:

$
J_t =
mat(
  B_("mm",t), B_("md",t), B_("me",t);
  B_("dm",t), B_("dd",t), B_("de",t);
  B_("em",t), B_("ed",t), B_("ee",t)
)
$

where each $B_(a,b,t)$ is a `3 x 3` block describing how local perturbations in family $b$ map into local linear change in family $a$ at window $t$.

The planned inferential targets are:

1. within-family deformation (`B_mm`, `B_dd`, `B_ee`)
2. cross-family coupling (`B_md`, `B_me`, `B_dm`, `B_de`, `B_em`, `B_ed`)
3. diagonal-versus-off-diagonal balance
4. directional asymmetry between paired cross-family blocks

== Interim article-facing summaries

The exact final block hierarchy is not frozen yet, because `part2` verification and pooled synthesis have not been materialized. The current interim draft therefore reports a discovery-side `part1` export from `articles/CLINICAL/comatose_block_jacobian/results/`, with two clearly separated layers:

1. raw block summaries tied to named `3 x 3` blocks
2. transparent block aggregates such as diagonal-versus-off-diagonal balance and paired directional asymmetry

The current discovery screen still asks the same substantive questions:

1. Are some within-family blocks consistently weaker or stronger in better-outcome patients?
2. Are some cross-family coupling blocks selectively attenuated or amplified by outcome?
3. Does the diagonal-versus-cross-family balance shift by outcome?
4. Do any candidate asymmetry summaries survive once paired cross-family blocks are compared directly?

For this interim draft, BH-FDR is shown within each provisional contrast family rather than as a final manuscript-wide multiplicity correction. That choice is intentionally temporary and will need refreshing once the `part2` verification layer exists.

== Statistical summary and claim discipline

The planned article will follow the same discipline as the sibling coma papers:

1. patient-level summaries as the primary inferential layer
2. cohort-specific reporting before pooled synthesis
3. effect sizes and medians emphasized alongside Mann-Whitney `p`
4. explicit distinction between replicated signals, pooled-promoted signals, and exploratory appendix material

If blockwise screening is extensive, family-wise error control or BH-FDR will be reported against the exact block-candidate pool frozen for the primary `0-12 h` contrast.

= Results

#netn-box(title: [Draft Status])[
  Numerical results are now populated for an interim `part1` discovery export. `part2` verification, pooled synthesis, and any final frozen block hierarchy remain pending, so all current block findings should be read as provisional discovery-side candidates rather than as replicated final leads.
]

== Primary `0-12 h` contrast

The refreshed block-Jacobian wrapper now yields an article-local `part1` discovery export for the primary `0-12 h` `CPC 1` versus `CPC 5` contrast. After restricting to the extreme-outcome subset, the patient-level handoff retains `141` patients (`71 / 70`) and `1269` patient-block rows, corresponding to the full `3 x 3` family grid per patient. The upstream run still records `88` failed groupings across `27` subjects, but those failures are partial rather than whole-subject losses: all `141` extreme-outcome patients remain represented in the patient-level export.

The strongest current `part1` signal is not a directional-asymmetry metric but a scale-like one. Better-outcome patients have lower diagonal block Frobenius magnitude than poorer-outcome patients (`0.204` versus `0.238`, `d = -0.326`, `p = 4.13e-4`, within-family `q = 2.89e-3`). That diagonal aggregate is then mirrored by named raw blocks. Within-family `ee` block Frobenius mean is lower in `CPC 1` (`0.209` versus `0.255`, `d = -0.313`, `p = 0.00131`), `dd` block Frobenius mean also separates (`0.214` versus `0.240`, `d = -0.240`, `p = 3.58e-4`), and the clearest cross-family Frobenius signal appears on the `ed` block (`0.216` versus `0.242`, `d = -0.279`, `p = 8.15e-5`).

Cross-family coupling summaries beyond Frobenius point in the same general direction. The `de` / `ed` symmetry and rotation summaries are both lower in better-outcome patients (`c_sym_mean` and `c_rot_mean`, each `d approx -0.244`), while the broader off-diagonal aggregates remain lower as well (`offdiag_block_frobenius_mean`, `offdiag_c_sym_mean`, `offdiag_c_rot_mean`; all `d approx -0.23`). By contrast, the current directional-asymmetry layer is weaker. The best asymmetry candidate, `frobenius_de_ed_absdiff`, remains only exploratory (`d = -0.241`, `p = 0.0349`, within-family `q = 0.210`).

Anisotropy-like block summaries also show discovery-side separation, but they are less stable in support and scale than the Frobenius-like layer. For example, diagonal aggregate anisotropy differs (`139` versus `3420`, `d = 0.172`, `p = 0.00148`), and `dd` block anisotropy is lower in `CPC 1` (`77.9` versus `151`, `d = -0.195`, `p = 2.73e-4`), yet these rows lose some subject support (`69 / 68`) and should therefore be treated more cautiously than the better-supported Frobenius-like candidates.

== Interim `part1` summary table

#figure(
  kind: table,
  table(
    columns: (1.45fr, 2.45fr, 1.15fr, 0.85fr, 0.9fr, 0.95fr, 1.2fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Target*],
      [*Current `part1` discovery summary*],
      [*`CPC 1 / CPC 5` med*],
      [*`d`*],
      [*`p`*],
      [*`q`*],
      [*Current status*],
    ),
    [Diagonal-versus-off-diagonal balance], [`diag_block_frobenius_mean`], [`0.204 / 0.238`], [`-0.326`], [`4.13e-4`], [`2.89e-3`], [provisional lead],
    [Within-family deformation], [`ee` `block_frobenius_mean`], [`0.209 / 0.255`], [`-0.313`], [`0.00131`], [`0.00321`], [provisional lead],
    [Cross-family coupling], [`ed` `block_frobenius_mean`], [`0.216 / 0.242`], [`-0.279`], [`8.15e-5`], [`5.50e-4`], [provisional lead],
    [Within-family deformation], [`dd` `block_frobenius_mean`], [`0.214 / 0.240`], [`-0.240`], [`3.58e-4`], [`0.00161`], [supportive],
    [Cross-family coupling], [`de` / `ed` `c_sym_mean`], [`0.154 / 0.205`], [`-0.244`], [`0.00740`], [`0.0105`], [supportive],
    [Directional asymmetry], [`frobenius_de_ed_absdiff`], [`0.0222 / 0.0508`], [`-0.241`], [`0.0349`], [`0.210`], [exploratory only],
  ),
  caption: [Interim `part1` discovery table for the primary `0-12 h` block-Jacobian contrast. Median entries are shown as `CPC 1 / CPC 5`. BH-FDR `q` values are currently reported within provisional contrast families rather than as a final manuscript-wide multiplicity correction.]
) <tab-part1-block-discovery>

== Hourly localization

Pending export. If the block handoff is materialized at hourly resolution, this subsection will test whether any replicated block-coupling signal is already present in the first hour or only appears later in the `0-12 h` window.

== Relationship to sibling coma papers

The current `part1` block discovery is broadly concordant with the scalar `9D` Jacobian paper rather than orthogonal to it. The clearest current block signal is lower Frobenius-like magnitude in better-outcome patients, both when averaged across diagonal blocks and when localized to `ee`, `dd`, and selected cross-family blocks. That is directionally consistent with the scalar `9D` article, where lower whole-matrix Frobenius magnitude also remained a stable comparator in `CPC 1`.

What the block view adds, even at this interim stage, is localization. The scalar `9D` result says that local-linear magnitude tends to be lower in better-outcome patients. The current block export suggests that this difference may be concentrated most clearly in diagonal family structure and in selected cross-family pathways such as `ed` / `de`, rather than being distributed uniformly across the entire `9 x 9` matrix. That interpretation still requires `part2` verification before it should be promoted from a plausible localization pattern to a replicated article-level claim.

= Discussion

The main scientific value of this article is now easier to see, even though the replication layer is incomplete. The scalar `9D` paper asks whether whole-matrix local-linear summaries carry an outcome-linked signal. The present manuscript asks whether that signal can already be localized to specific within-family or cross-family coupling pathways. The current `part1` discovery export points most clearly toward lower diagonal and selected cross-family Frobenius-like magnitude in better-outcome patients, especially in `ee`, `dd`, and `ed`. If that organization replicates in `part2`, it would strengthen the claim that repaired `9D` Jacobians are informative not only because they are larger matrices, but because they expose structured family-level coupling geometry.

The article should still be framed conservatively. Any blockwise finding remains a recovery-associated geometry result in an early post-arrest EEG cohort, not a direct consciousness assay and not a bedside-ready model. The current evidence also does not yet justify a strong asymmetry story: paired `de` versus `ed`, `md` versus `dm`, and `me` versus `em` contrasts remain much weaker than the diagonal/off-diagonal magnitude layer. The strongest eventual manuscript should therefore separate three claim types clearly: replicated family-coupling signals, pooled-promoted or hierarchy-promoted signals, and exploratory pathway maps that still need follow-up.

= Limitations

This interim draft has five immediate limitations.

1. The manuscript is not results-complete; only the article-local `part1` block export is currently available.
2. The current numerical results come only from `part1`; `part2` verification and pooled synthesis are still absent, so no replication claim can yet be made.
3. The outcome contrast remains `CPC 1` versus `CPC 5`, which sharpens separation but inherits the same WLST and death-pathway caution as the sibling coma papers.
4. The source run still includes `88` failed groupings across `27` subjects from duplicate `coords_9d` signatures. All extreme-outcome subjects remain represented, but that upstream loss still constrains how confidently weak block effects should be interpreted.
5. Regional block Jacobians and exact hourly block exports are not yet available in the current article-facing bundle, so the present draft cannot test whether the current family-level findings localize further in time or network space.

= Conclusion

This file now establishes an interim results-bearing draft for a coma `0-12 h` block-Jacobian follow-up. The current `part1` export suggests that better-outcome patients show lower diagonal and selected cross-family block magnitude, with the clearest current signals in diagonal Frobenius average and the `ee`, `dd`, and `ed` Frobenius summaries. Those findings remain discovery-side rather than definitive because `part2` verification, pooled synthesis, and any final block hierarchy are still pending. The next substantive step is therefore no longer to create the first export, but to replicate and audit the current provisional block candidates in the second dated cohort.

= Appendix: Block notation

This manuscript uses the compact notation $B_(a,b,t)$ for the `3 x 3` block that maps family $b$ into family $a$ at local window $t$. Diagonal blocks (`mm`, `dd`, `ee`) describe within-family local deformation, while off-diagonal blocks describe cross-family coupling. Any future article-facing metric should remain explicitly traceable to one of those named objects or to a transparent aggregate built from them.

#bibliography("cardiac_arrest_comatose_references.bib")
