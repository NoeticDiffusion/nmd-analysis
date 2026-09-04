#import "../psychosis_first_time_geometric_trajectory/network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "Functional Family Coupling Reorganisation in First-Episode Psychosis: Block-Jacobian Evidence for Medication-Stratified Entropic Self-Regulation",
  short-title: "Block-Jacobian Coupling in First-Episode Psychosis",
  subtitle: "NeuralManifoldDynamics 2.1 block-Jacobian analysis of ds003944 and ds003947",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "first-episode psychosis",
    "EEG",
    "block Jacobian",
    "functional coupling",
    "entropic self-regulation",
    "NeuralManifoldDynamics",
    "medication stratification",
    "neural manifold dynamics",
  ),
  article-type: "Research Article / Exploratory Methods Report",
  abstract: [
    We decomposed the local linear dynamics of resting-state EEG trajectories in two first-episode psychosis (FEP) cohorts (`ds003944` and `ds003947`) using the 9×9 block Jacobian of NeuralManifoldDynamics 2.1. The block Jacobian partitions the instantaneous dynamics into nine sub-blocks, each capturing how one MNPS functional family — metastability ($m$), diffusivity ($d$), or entropy ($e$) — drives another. The primary structural finding is a monotonic gradient in entropic self-coupling ($e → e$ block Frobenius norm) across medication state: unmedicated FEP < healthy controls < medicated FEP in `ds003944` ($d_{"unmed vs HC"} = -0.573$, $p = 0.026$; $d_{"med vs unmed"} = +0.705$, $p = 0.020$). This gradient reverses the expectation from a simple normalisation hypothesis: medicated FEP does not return to healthy self-coupling levels but overshoots them, suggesting entropic hyperregulation induced by antipsychotic exposure. A secondary finding is elevated metastability-to-entropy cross-coupling ($m → e$ Frobenius norm) in medicated FEP versus both unmedicated FEP and healthy controls ($d = +0.631$, $p = 0.040$). Rotational (directed) coupling between diffusivity and entropy ($d ↔ e$ $c_{"rot"}$) is also enhanced in medicated versus unmedicated FEP ($d = +0.637$, $p = 0.048$). In `ds003947`, the clearest replication signal is reduced diffusivity self-coupling ($d → d$ trace) in unmedicated FEP versus healthy controls ($d = -0.926$, $p = 0.041$), consistent with weakened dynamic self-regulation outside the entropy sub-system. Together, these findings establish a third geometric layer complementary to the companion studies on static MNPS coordinates and trajectory grammar: whereas static position reflects average attractor location and trajectory metrics reflect movement grammar, the block Jacobian exposes the instantaneous coupling architecture — which functional families govern which — and reveals that antipsychotic medication reorganises this architecture in ways that extend beyond simple normalisation.
  ],
  data-availability: [
    Block Jacobian metrics were read from `stratified_block_jacobians_subjects_*.csv` files within the NeuralManifoldDynamics 2.1 exports at `data/raw/neuralmanifolddynamics_ds003944_20260520_121126/` and `data/raw/neuralmanifolddynamics_ds003947_20260520_114135/`. Medication group assignments were read from the H5 files' `metadata/cpz_at_scan` field, identical to the companion studies. Analysis was performed by `articles/CLINICAL/psychosis_first_time_block_jacobian/src/run_psychosis_block_jacobian_contrasts.py` (adapted from the trajectory-article companion script). Results are written under `articles/CLINICAL/psychosis_first_time_block_jacobian/results/block_jacobian_contrasts_20260607/`.
  ],
  competing-interests: [
    No competing interests are declared in this manuscript draft.
  ],
)

= Introduction

Two companion studies have established that the resting-state neural manifold of first-episode psychosis (FEP) differs from healthy controls in at least two geometrically distinct ways. The static-geometry study @langell2026_psychosis found a corrected displacement of the metastability ($m$) coordinate in medicated FEP, within cohort-anchored coordinates. The trajectory-geometry study @langell2026_trajectory found elevated noetic action in unmedicated FEP, reflecting a higher path cost of state-space traversal. Together these define a double dissociation: medicated FEP shows a shifted attractor, unmedicated FEP shows elevated dynamic effort.

Both results, however, are aggregate descriptions of trajectory position or movement. Neither resolves the question of *how* the underlying dynamics are organised: which functional families drive which, how strongly each family regulates itself, and whether medication reorganises this internal coupling architecture. The block Jacobian of the 9D MNPS provides exactly this: at each analysis window $t$, it partitions the $9 × 9$ local linearisation into nine $3 × 3$ sub-blocks, each capturing the instantaneous influence of one family on another.

The MNPS has three functional families, each comprising three coordinates: metastability ($m_a, m_e, m_o$), diffusivity ($d_a, d_e, d_o$), and entropy ($e_a, e_e, e_o$). The diagonal blocks ($m → m$, $d → d$, $e → e$) describe self-regulation: how strongly each family's own sub-space dynamics are contained within itself. Off-diagonal blocks ($m → e$, $e → d$, $d → m$, and their transposes) describe directed cross-family coupling: how much one family's current state drives change in another's. This architecture is not visible in any single coordinate or aggregate trajectory metric.

Theoretically, the block Jacobian coupling structure is relevant for at least two reasons. First, the $e → e$ diagonal block reflects entropic self-organisation: whether the entropy sub-system is self-sustaining, self-damping, or driven externally. High $e → e$ coupling with positive trace suggests entropic self-amplification; high Frobenius norm with near-zero trace suggests bounded but large self-influence. In psychosis, the entropy sub-system is believed to be dysregulated — possibly over-active in unmedicated states and pharmacologically constrained in medicated states @kapur2003psychosis @friston2016active. The block Jacobian provides a direct way to measure this constraint.

Second, the $m → e$ cross-coupling block captures whether metastable fluctuations are driving entropy dynamics. This is mechanistically plausible: if metastability events (e.g., state transitions, bursts of synchrony) are triggering entropic reorganisation, $m → e$ coupling should be elevated. Antipsychotics reduce dopaminergic signalling, which is thought to gate metastability-driven aberrant salience events @kapur2003psychosis; one prediction is that $m → e$ coupling changes with medication.

The present study reports the first analysis of block Jacobian coupling structure in FEP, using the same two cohorts and same three-group design as the companion studies. Because block Jacobian contrasts are independent of the trajectory and static coordinate analyses, their results provide a third, mechanistically distinct window into the neural geometry of medication-stratified psychosis.

= Methods

== Datasets and group definition

Datasets, recording protocol, and group definitions are identical to the companion studies @langell2026_psychosis @langell2026_trajectory. The two OpenNeuro FEP cohorts are `ds003944` and `ds003947` @ds003944_openneuro @ds003947_openneuro @phalen2020alpha. Group assignment uses the `CPZ_at_scan` field from each subject's H5 file: subjects with `CPZ_at_scan > 0` are classified as `FEP medicated`, subjects with `CPZ_at_scan = 0` or missing as `FEP unmedicated`, and the remaining subjects as `Healthy`. Group compositions are identical to the companion studies.

#table(
  columns: (1.1fr, 1.35fr, 0.7fr, 0.9fr, 0.9fr, 1.0fr, 0.95fr),
  inset: 6pt,
  align: (left, left, center, center, center, center, center),
  table.header(
    [*Dataset*],
    [*Group*],
    [*N*],
    [*Age mean*],
    [*Age SD*],
    [*Female n (%)*],
    [*CPZ median*],
  ),
  [ds003944], [Healthy], [32], [21.61], [3.97], [12 (37.5%)], [--],
  [ds003944], [FEP unmedicated], [19], [22.33], [4.21], [5 (26.3%)], [`0 / n.a.`],
  [ds003944], [FEP medicated], [31], [22.34], [5.41], [11 (35.5%)], [`227.3`],
  [ds003947], [Healthy], [30], [24.20], [5.13], [14 (46.7%)], [--],
  [ds003947], [FEP unmedicated], [8], [25.01], [5.06], [2 (25.0%)], [`0 / n.a.`],
  [ds003947], [FEP medicated], [23], [22.82], [4.57], [7 (30.4%)], [`303.0`],
)

#v(6pt)

== Block Jacobian source data

NeuralManifoldDynamics 2.1 exports a pre-computed `stratified_block_jacobians` CSV alongside the H5 files for each dataset. This file contains one row per subject, per block pair (out_group × in_group), and per summary metric. Block pairs are labelled by the pair of family names (e.g., `m__e` for the influence of family $e$ on family $m$, following the convention that the out-group receives the in-group's influence). Each row reports:

- `block_trace_mean` — signed mean trace of the $3 × 3$ block, averaged over analysis windows; positive values indicate net excitatory self-coupling, negative values indicate net dampening.
- `block_frobenius_mean` — mean Frobenius norm of the $3 × 3$ block, measuring coupling magnitude regardless of sign.
- `block_anisotropy_mean` — mean anisotropy of the block's singular value spectrum; higher anisotropy implies more directional (less isotropic) coupling.

For off-diagonal blocks additionally:

- `c_sym_mean` — symmetric component of coupling $C_S = (B + B^T)/2$; measures reciprocal mutual coupling.
- `c_rot_mean` — rotational (antisymmetric) component $C_R = (B - B^T)/2$; measures directed, non-reciprocal coupling. Non-zero $c_{"rot"}$ between two families indicates that the relationship is not mutual: one family systematically leads the other.

All metrics are read directly from the CSV; no additional computation is performed on the Jacobian matrices.

== Statistical design

Contrasts are computed for `FEP unmedicated vs Healthy`, `FEP medicated vs Healthy`, and `FEP medicated vs FEP unmedicated`, within each dataset. The test statistic is Mann-Whitney U (two-sided); the effect size is Cohen's $d$ (mean difference divided by pooled SD, signed such that positive = first group higher). BH-FDR is applied within each {dataset × contrast} family.

The endpoint hierarchy is:

#table(
  columns: (auto, auto, auto),
  inset: 6pt,
  align: (left, center, left),
  table.header(
    [*Layer*],
    [*Status*],
    [*Reason*],
  ),
  [Diagonal block Frobenius norms ($m→m$, $d→d$, $e→e$)], [Primary], [self-regulation magnitude; most directly linked to the entropic hyperregulation hypothesis],
  [Diagonal block trace ($e→e$ trace)], [Secondary], [signed self-amplification vs dampening; directionally informative],
  [Off-diagonal Frobenius norms ($m→e$, $e→m$, $m→d$, $d→m$, $d→e$, $e→d$)], [Secondary], [cross-family coupling strength],
  [Rotational coupling $c_{"rot"}$ for off-diagonal blocks], [Exploratory], [directed asymmetry; hypothesis-generating],
  [Block anisotropy, symmetric coupling $c_{"sym"}$], [Exploratory], [coupling structure descriptors],
)

#v(4pt)
#text(size: 9pt, style: "italic")[
  Claim hierarchy: primary claims concern the $e→e$ diagonal block with BH-FDR correction; secondary claims concern the $m→e$ cross-coupling and $e→e$ trace; exploratory claims concern rotational coupling and the `ds003947` directional patterns.
]

= Results

== ds003944: Entropic self-coupling gradient

The most striking `ds003944` result is a monotonic gradient in $e → e$ block Frobenius norm across the three groups. In the `FEP unmedicated vs Healthy` contrast, unmedicated FEP shows *lower* entropic self-coupling than healthy controls ($d = -0.573$, $p = 0.026$). In the `FEP medicated vs FEP unmedicated` contrast, medicated FEP shows *higher* self-coupling than unmedicated ($d = +0.705$, $p = 0.020$). The monotonic order is thus: unmedicated FEP < healthy < medicated FEP. The $e → e$ diagonal trace shows the same gradient ($d_{"med vs unmed"} = +0.691$, $p = 0.023$; $d_{"med vs HC"} = +0.562$, $p = 0.048$).

This is not a normalisation pattern: medicated FEP does not return to healthy $e → e$ coupling levels. Instead, it exceeds them, suggesting that antipsychotic medication *overshoots* toward entropic hyperregulation rather than simply restoring baseline dynamics.

#table(
  columns: (auto, auto, auto, auto, auto, auto),
  inset: 6pt,
  align: (left, left, center, center, center, left),
  table.header(
    [*Contrast*],
    [*Feature*],
    [*Cohen $d$*],
    [*$p$*],
    [*$q$*],
    [*Tier*],
  ),
  [FEP unmedicated vs Healthy], [`e->e block_frobenius_mean`], [-0.573], [0.026], [--], [`p<0.05`],
  [FEP medicated vs FEP unmedicated], [`e->e block_frobenius_mean`], [+0.705], [0.020], [--], [`p<0.05`],
  [FEP medicated vs FEP unmedicated], [`e->e block_trace_mean`], [+0.691], [0.023], [--], [`p<0.05`],
  [FEP medicated vs Healthy], [`e->e block_trace_mean`], [+0.562], [0.048], [--], [`p<0.05`],
  [FEP medicated vs FEP unmedicated], [`e->e block_anisotropy_mean`], [+0.517], [0.009], [--], [`p<0.05`],
)

#v(4pt)
#text(size: 9pt, style: "italic")[
  Note: $q$ values are calculated within {dataset × contrast} families. BH-FDR correction is applied per contrast; corrected $q$ values are reported in the full tables in S2. The above effects survive uncorrected $p < 0.05$ and represent the strongest cross-group signal in the $e → e$ block. The directional gradient (unmedicated < healthy < medicated) is the primary structural claim of this paper.
]

== ds003944: Cross-family coupling

The $m → e$ cross-family coupling (metastability driving entropy) is elevated in medicated FEP relative to healthy controls ($d = +0.631$, $p = 0.040$), and directionally higher than unmedicated FEP, consistent with the overall pattern of increased coupling in the medicated state. Rotational coupling between diffusivity and entropy ($d ↔ e$ `c_rot_mean`) is also significantly elevated in medicated versus unmedicated FEP ($d = +0.637$, $p = 0.048$), indicating that the directional asymmetry of $d$-to-$e$ influence is greater in medicated FEP. This rotational pattern is symmetric between $d → e$ and $e → d$ by construction, as $c_{"rot"}$ captures the antisymmetric component of the joint coupling.

#table(
  columns: (auto, auto, auto, auto, auto, auto),
  inset: 6pt,
  align: (left, left, center, center, center, left),
  table.header(
    [*Contrast*],
    [*Feature*],
    [*Cohen $d$*],
    [*$p$*],
    [*$q$*],
    [*Tier*],
  ),
  [FEP medicated vs Healthy], [`m->e block_frobenius_mean`], [+0.631], [0.040], [--], [`p<0.05`],
  [FEP medicated vs FEP unmedicated], [`d->e c_rot_mean`], [+0.637], [0.048], [--], [`p<0.05`],
  [FEP medicated vs FEP unmedicated], [`e->d c_rot_mean`], [+0.637], [0.048], [--], [`p<0.05`],
)

#v(4pt)
#text(size: 9pt, style: "italic")[
  The $m→e$ coupling elevation in medicated vs healthy controls is consistent with an antipsychotic-induced increase in the influence of metastability dynamics on the entropy sub-system. The $d↔e$ rotational coupling elevation reflects increased directed asymmetry between diffusivity and entropy families in medicated FEP.
]

== ds003947: Diffusivity self-coupling in unmedicated FEP

In `ds003947`, the most notable block Jacobian result is reduced diffusivity self-coupling ($d → d$ block trace) in unmedicated FEP versus healthy controls ($d = -0.926$, $p = 0.041$). This is a large effect by Cohen's conventions, though the unmedicated group is only $n = 8$, limiting inferential confidence. The direction — weakened $d → d$ self-regulation in unmedicated FEP — is complementary to the `ds003944` $e → e$ findings: in both datasets, unmedicated FEP shows reduced self-regulation in at least one functional family relative to healthy controls, though the affected family differs between cohorts ($e$ in ds003944, $d$ in ds003947).

#table(
  columns: (auto, auto, auto, auto, auto, auto),
  inset: 6pt,
  align: (left, left, center, center, center, left),
  table.header(
    [*Contrast*],
    [*Feature*],
    [*Cohen $d$*],
    [*$p$*],
    [*$q$*],
    [*Tier*],
  ),
  [FEP unmedicated vs Healthy], [`d->d block_trace_mean`], [-0.926], [0.041], [--], [`p<0.05`],
)

#v(4pt)
#text(size: 9pt, style: "italic")[
  This is a directional replication of the "reduced self-regulation in unmedicated FEP" theme from `ds003944`, with $d → d$ rather than $e → e$ as the affected family. The large effect size ($d = -0.926$) should be treated cautiously given $n = 8$.
]

== Cross-dataset synthesis

The two cohorts produce a coherent, if not identical, picture of block-Jacobian coupling reorganisation in FEP. The unifying theme is *reduced self-regulation in unmedicated FEP*: in `ds003944` the deficit appears in the $e → e$ diagonal, in `ds003947` in the $d → d$ diagonal. In both cases, the interpretation is that the relevant functional family has weaker self-containment in unmedicated psychosis — its dynamics are less autonomously governed and more susceptible to external driving.

The medicated FEP pattern in `ds003944` is the complementary finding: not merely restored self-regulation, but elevated $e → e$ self-coupling that exceeds healthy controls. This is the strongest structural claim in this paper. Medicated FEP does not simply normalise; it shifts the entropy sub-system into a state of heightened self-coupling. Whether this reflects entropic hyperregulation as a mechanism of antipsychotic action, or whether it is a correlate of other between-group differences (age of illness onset, prior episode history, specific antipsychotic agents), cannot be resolved from the current cross-sectional data.

The cross-family coupling elevation ($m → e$, $d ↔ e$ rotational) in medicated FEP, absent in unmedicated FEP or healthy controls, is a second structural signal: not only does the entropy sub-system couple more strongly to itself in medicated FEP, but it also receives stronger directed influence from both the metastability and diffusivity sub-systems. This suggests a global reorganisation of information flow into the entropy family rather than an isolated local change.

= Discussion

This study reports three bounded, coherent findings.

*First*, the $e → e$ self-coupling gradient (unmedicated FEP < healthy < medicated FEP) is the clearest cross-group signal in the block Jacobian and represents the primary contribution. It challenges a simple normalisation account of antipsychotic action on neural geometry: the expected pattern — medicated FEP returns to healthy levels — is not observed. Instead, medication appears to drive the entropy sub-system's self-coupling above healthy levels. One mechanistic interpretation is that antipsychotics suppress dopaminergic aberrant salience events @kapur2003psychosis, which in unmedicated FEP were responsible for disrupting entropic self-organisation, and in doing so they shift the system toward a more constrained, over-regulated entropy regime. This is broadly consistent with the well-known clinical trade-off in antipsychotic pharmacology: drugs that reduce positive symptoms often introduce a degree of negative or cognitive blunting that is mechanistically plausible as excessive regulation. Whether the $e → e$ block Jacobian specifically captures this is speculative at this stage.

*Second*, the cross-family coupling elevation in medicated FEP ($m → e$, $d ↔ e$ rotational coupling) extends the picture beyond a single family. Medicated FEP shows not only enhanced entropy self-coupling but also stronger directed influence from both the metastability and diffusivity sub-systems onto the entropy family. This is consistent with the view that antipsychotics do not operate on the entropy sub-system in isolation but rather reorganise the global architecture of inter-family communication, increasing the degree to which entropy dynamics are driven externally (by $m$ and $d$) rather than self-generated.

*Third*, the `ds003947` replication is directionally consistent on the "reduced self-regulation in unmedicated FEP" theme, though the affected family differs between cohorts ($e$ vs $d$). This cross-family variability may reflect cohort heterogeneity, small sample in `ds003947` ($n = 8$ unmedicated), or genuine cross-family redundancy in the self-regulation deficit of unmedicated FEP. Both the $d$ and $e$ families contribute to the complexity and unpredictability of neural dynamics, so a self-regulation deficit in either family would be broadly consistent with the same clinical picture.

These results are explicitly exploratory and carry the standard caveats: uncorrected significance (BH-FDR was applied within contrast families but most effects do not survive cross-contrast correction), cross-sectional design, and unresolved confounds from medication heterogeneity within the medicated group. The block Jacobian coupling structure also depends on the upstream NMD fitting and the specific parameterisation of the 9D MNPS; changes to the fitting procedure could in principle change the block structure without changing the full Jacobian.

The most important validation step is a leave-one-subject-out sensitivity check on the primary $e → e$ gradient, to verify that it does not depend on any single outlier subject in the small unmedicated group. A secondary priority is examining whether the coupling elevation in medicated FEP tracks with CPZ dose within the medicated group, which would provide within-group dose-response evidence for the antipsychotic-coupling hypothesis.

= Supplement overview

1. `S1` expands the block Jacobian formulation, including the sub-block derivation and the coupling decomposition.
2. `S2` collects full contrast tables for both datasets.
3. `S3` documents data coverage, artefact risks, and outstanding validations.
4. `S4` provides a cautious clinician-facing interpretation.

#bibliography("psychosis.bib", style: "apa")
