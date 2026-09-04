// S5 Glossary — generic template.
// Shared terminology across articles. Living document: update to match the
// current MNDM pipeline version, and note version-specific changes in entries.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S5 - Glossary",
  short-title: "Glossary",
  subtitle: "Shared terminology across articles",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("glossary", "NDT", "MNDM", "MNPS", "embodied anchoring"),
  article-type: "Supplementary Material",
  abstract: [
    This document defines the core terminology used across articles in this repository. Entries cover the theoretical framework, the computational pipeline, embodied anchor metrics, the family of primary metric scalar summaries, trajectory geometry, robustness-audit methods, and statistical methods. Definitions reflect the current implementation as of the latest pipeline version; version-specific changes to metric computation are noted in the relevant entry.
  ],
)

#set heading(numbering: none)

_Note: This is a living document. Definitions are updated to match the current pipeline version. Version-specific changes to metric computation are noted in the relevant entry._

_*Reading guide for reviewers.* Where relevant, entries distinguish three layers: (1) *Implemented* - the exact computation in the pipeline; (2) *Interpretation* - the most defensible empirical reading; (3) *Speculative / Not established* - theoretical mappings not yet directly confirmed._

= A - D

*AnchorState v0.1* - The implemented embodied proxy surface comprising
`vagal_index`, `sympathetic_index`, `vascular_index`, `pupil_arousal_index`,
and `anchor_index`. It is a fixed, within-subject standardized convenience
surface, not a direct measure of interoceptive awareness, vagal nerve activity,
HEP, or EAP anchor strength.

*Attractor* - A stable region of a specified state-space model toward which
nearby trajectories tend to return. In NDT it is a theoretical landscape
object; empirical MNPS occupancy alone does not uniquely identify an attractor.

*CCTG (Context-Conditional Transition Geometry)* - A speculative subsystem
hypothesis in which a circuit- and context-specific field
$K^("TRN")_(k,c)$ changes relative state transitions. It replaces neither the
functional RVC test nor the need for causal validation. It is not a validated
TRN variance gate.

*Content section* - An NDT-Q operational map selecting a content-compatible
realization over a regime base: $rho_b(s_c(b)) = c$. It is not a neural-fibre
topology claim or a quale measurement.

= E - L

*EAP (Embodied Anchoring Principle)* - A Tier-2 formal extension in which a
self-prior and bodily rhythms may condition the landscape and schedule. The
implemented AnchorState surface supports observational tests of co-modulation;
causal entrainment, HEP-based binding, and clinical translation are not
established.

*HELS (Hippocampal--Entorhinal Landscape System)* - A prospective account in
which history and replay may update a context-conditioned landscape $F_c$.
Current work validates infrastructure and data eligibility, not the mechanism.

*MNPS coordinate* - The operational chart $(m,d,e)$: mobility/metastability,
deviation from an integration--segregation corridor, and entropy/complexity.
Its 9D decomposition improves diagnostic resolution but does not identify a
unique latent ontology or experienced content.

= M - R

*Meta-Noetic Jacobian (MNJ)* - The estimated local flow derivative
$J=partial f/partial x$ under a declared measurement contract. It should not
be conflated with a Jacobian in a truth-known simulator unless an observation
map has been separately validated.

*Reachability* - A short-horizon model-propagated uncertainty object, commonly
$Sigma_(t)^(h+1) = A_t Sigma_t^(h) A_t^T + Q_t$. Its volume, effective
dimension, and directionality are separate endpoints. Aggregate calibration
does not establish directional selectivity.

*RVC (Rhythmic Variance Control)* - The functional hypothesis that rhythm-linked
signals organize a schedule relevant to exploration and denoising. Stage-1
tests use observable $hat(r)(t)$; they do not require identification of TRN as
the anatomical controller.

= S - Z

*Timing versus efficacy* - In EAP/RichSleep analyses, phase locking asks when
an event occurs relative to a bodily rhythm; efficacy asks whether alignment
changes a geometry or behavioral outcome. Evidence for timing does not establish
efficacy or causality.

*TRN--VG* - The proposed thalamic-reticular variance-gate mechanism. It is not
validated in NDT. Zenodo 21774408 supports a bounded PV-linked population
geometry result, not a universal single-unit variance gate or an identified
$g_("TRN") -> sigma(t)$ map.

*BH-FDR* - Benjamini--Hochberg false-discovery-rate correction. Primary claims
are assessed within their prespecified endpoint family; nominal effects that
fail the relevant broader family are not promoted to confirmed findings.

#bibliography("references.bib", style: "apa")
