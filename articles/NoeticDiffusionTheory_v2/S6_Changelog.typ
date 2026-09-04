// S6 Internal Changelog — NDT manuscript rebuild.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S6 Internal Changelog",
  short-title: "S6 Changelog - NDT v2",
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

Internal working document for the NDT manuscript rebuild. Public claim
discipline lives in the manuscript; this file records drafting provenance.

= Provenance

Sciencelead freeze: `sciencelead/sl_1.md`, `sciencelead/sl_001.md`.
Source intake: `summaries/00_synthesis.md` and `summaries/01`--`06`.
Identity donor: `articles/NDT/NoeticDiffusionTheory.typ`.
Epistemic donor: `articles/NDT_2/ndt_2.typ`.

= Changelog

== 2026-08-28 --- first prose pass (manuscript §§1--8)

Replaced the generic empirical template with theoretical-framework architecture.
Wrote scope, introduction (state $->$ accessibility), recoverability ladder,
canonical SDE with non-conservative split, MNPS/NMD boundary, local Jacobian
summaries, diffusion tensor, and possible-futures objects (reachability,
committor, FAR). Control, empirical anchors, and neighbouring-theory comparison
are outlined but not yet drafted. Companion experiment IDs are kept out of the
public text; DANDI 000458 appears only as the Level-1 / Level-4 illustration
already used in ndt_2.

== 2026-08-28 --- control layer (manuscript § Biological control)

Drafted RVC, thalamic access, HELS vs HELS-A vs HELS-A1, embodiment/metabolism,
and dendritic $M_b$. HELS-A intake from `ndt-subsystems/project/HELS-A`
(H0/H0B eligibility; M0/M0R fabricated-estimator FAIL; A1 and spikes closed)
plus simulator A0/A0B operator existence on frozen $Phi$. Empirical anchors
and neighbouring theories remain stubs.

== 2026-08-28 --- empirical anchors (manuscript § Empirical constraints)

Replaced the empirical stub with three main-text anchors (spindle-locked $d_n$
timing; I-CARE recovery-linked reachability/Jacobian; DANDI 000458 Level-1 /
Level-4 split) plus a compact dissociation matrix. Neighbouring theories
remain a stub. Dataset records added to `references.bib`.

== 2026-08-28 --- neighbouring frameworks and predictions

Replaced the remaining stub with neighbouring frameworks (positioning,
dynamical family, bridge table, Cogitate / state-vs-experience discipline)
and predictions (P1--P7 plus hierarchical failure). Source harvest:
`J:/repos/NoeticDiffusion/articles/ndt_compared_to_other_theories`, rewritten
for NDT 1.0 (accessibility, not denoising identity).

== 2026-08-28 --- discussion, limitations, conclusion

Closed the main text: discussion (denoising $->$ accessibility; retain /
promote / separate; consciousness-research implication), limitations, and
conclusion thesis from `sciencelead/sl_001.md` §§18--20. Public supplements
remain template stubs.

== 2026-08-28 --- conceptual figures (script + five sciencelead panels)

Added reusable generator `src/make_conceptual_figures.py` (PNG+SVG, CLI
`--only` / `--formats` / `--list`). Emitted fig1--fig5 into
`figures/conceptual/` and wired them into the manuscript. Figure 5 cell codes
follow summaries `01`/`03`/`04`; anesthesia and epilepsy rows are unpaid.

== 2026-08-28 --- canonical coma freeze, S1--S5 populated

Audited pr_1 comment 7 against
`articles/CLINICAL/comatose_ndt/Recovery-Linked Neural Geometry After Cardiac-Arrest Coma.typ`.
The 298-patient ComBat merge is an intermediate; the canonical article is
`20260606_combined_invalidityfix` ($301$/$281$, AUROC $0.599 -> 0.662$).
The article now binds that source (S2) and says patients, not recordings.
Claim-ledger HELS/seed language moved toward S3. S1--S5 filled
(math/kernel, source freeze, negatives, clinical translation, glossary).

== 2026-08-29 --- pr_2 core: kernel in main text

Moved $cal(L)$ and protocol-conditional $K_(t : t+h)^gamma$ plus revised
C1--C3 into the main paper as a transition-law section after the canonical
SDE. Drift split now uses mobility $M$ and potential $V$ (IIT $Phi$
untouched); main text no longer claims that pure potential descent cannot
represent reactivity. Coordinate-dependence warning, predictive-spread
ellipsoid terminology, and renamed non-equivalent questions are in the main
text. Biological-control section cut to three classes. Companion analyses
cited alongside datasets. P8 within-state experience test added. S3 dropped
the closure-signature negative. S6 remains internal and is not a journal
supplement.

== 2026-08-30 --- S4 rebuilt as non-technical explanation

Replaced the clinician-facing S4 with a plain-language companion
(`S4_Non_technical_explaination.typ`). Tone and metaphors are borrowed from
the *Reality from Noise* essays (waking disorientation, map versus land,
texture versus elevation, ridge in fog). Claims stay on NDT 1.0:
accessibility as a future law, MNPS as a chart, RVC as a special case, three
anchors as constraints. The older denoising identity is explicitly not
restored. Main text points to S4 after the noetic-accessibility paragraph.

== 2026-08-30 --- public tone: flagship / programme

Replaced internal labels (*flagship*, self-referential *programme*) in the
main text and S1--S5 with *theory*, *article*, or *present theory*. Neighbouring
empirical programmes (HOT/AST) left as ordinary academic usage. S6 remains
internal.

== 2026-08-30 --- pr_3: m3-bridge targeted import, then freeze

External Science Lead review (`peer_review/pr_3.md`) plus summaries `07`--`10`.
Empirical intake for this draft is now frozen. Three anchors unchanged.
Kernel $cal(L)$ / $K^h$, mobility $M$, potential $V$, weaker drift-split
wording, and Jacobian coordinate dependence were already in the main text
from pr_2; they were not re-litigated.

- Anchor 3 cites the m3-bridge 000458 article of record: $r = 0.406$ /
  $r = 0.395$, residual $0.856$, alignment incomplete.
- Recoverability ladder elevated as a methodological contribution, with IBL
  decoder PASS / discrete-flow STOP as a second worked boundary (not Anchor 4).
- TRN section: joint TRN $->$ meso $->$ surface-macro chain not estimable
  from audited archives.
- Figure 5 / dissociation table: AVB state geometry, IBL readout STOP, DANDI
  000574 human MTL--scalp null. ARR, AGR, FB3, 24h, and Cecchetto stay out of
  the main matrix.
- S1/S3: ARR condition-mixing inflation of $op("Tr")(Q)$ in 126/126 fits;
  000458 three-stage chain blocked. S5: chart-speed coupling $eq.not$
  stochastic reachability. S2 source freeze updated. S6 remains internal.

== 2026-08-30 --- Zenodo DOI refresh

Public records for ORCID `0009-0006-6927-7456` (59 hits). Companion DOIs
updated where a public version exists:

- NDT 0.8 identity paper remains `10.5281/zenodo.20112950` (latest of concept
  `17367307`).
- Coma companion: `10.5281/zenodo.21263084` (v.0.3), not v.0.1.1
  `20410486`. Analysis freeze unchanged.
- Anchor 3: `10.5281/zenodo.22041386` (v.0.1).
- Neighbourhood essay: `10.5281/zenodo.21226430`.
- Still unpublished: RVC three-dataset spindle companion, IBL2 discrete-flow
  STOP, AVB omission, DANDI 000574.

== 2026-08-31 --- pr_4 literature neighbourhood

Abstract already rewritten by the author; not retouched. Author Summary kept
as the measurement-facing companion.

Introduction now opens from population-dynamics literature (Breakspear,
Cunningham--Yu, Vyas, Duncker, Hancock, Hudson, Barttfeld) before NDT
history. Added 17 neighbourhood citations: non-normal transients
(Hennequin, Christodoulou), TPT (E--Vanden-Eijnden), thalamic access
(Halassa, Schmitt), cortical gain (Ferguson), context-dependent dynamics
(Mante), variability quenching (Churchland), recoverability (Nejatbakhsh),
and consciousness-dynamics repertoire (Demertzi). No new empirical anchors.

== 2026-08-31 --- pr_5: present-tense theory, not a version diff

Removed v0.8$->$v1.0 narration from the public article. Author Summary no
longer says *rebuilds*. Introduction presents RVC/MNDM/MNPS as a restricted
realization of accessibility control. RVC is derived as the isotropic
variance-control limit. Thalamic prose drops *obsolete slogan*. Discussion
$13.1$/$13.2$ collapsed into *Dynamical accessibility as the organizing
principle*, with one continuity citation to the earlier formulation.
Release-note detail stays in this internal S6 / Zenodo version notes.

== 2026-08-31 --- pr_6: journal-surface cleanup

Architecture frozen. Main-text cleanup only: repository/governance phrasing
translated (no *fail closed*, *product-level export*, *source freeze*,
*unpaid*, PASS/STOP in captions). NMD section cut to the measurement-contract
distinction. Diffusion SDE given an explicit non-Brownian / non-Markov scope
sentence. C2 renamed *non-redundant accessibility*. Empirical coma freeze
hash moved to S2. Defensive reviewer sentence in neighbours replaced.
Conclusion left intact.

== 2026-08-31 --- pr_7: kernel split and compression

Architecture remains frozen. Formal fix: latent kernel $K^X$ versus chart
kernel $K^x$, with dummy $xi$ in the generator; unadorned $K^h$ means $K^x$.
C1/C3 and P8 follow the chart-conditional object. DANDI 000458 / IBL numbers
live only in Anchor 3; §3 is a compact claim-level example. Coma ceiling
says study-specific chart-level estimators. NMD wording is specifies /
operationalizes. Generator uses $frac(1, 2)$. Light §9 citations added for
truth-known, TRN geometry, and Slow Branch where public DOIs exist;
HELS-A and the two-operator simulator still point to S3. No fourth
anchor. S6 remains internal.

== 2026-08-31 --- pr_8: S4 conceptual decoder and figures

S4 reorganized as a pedagogical derivation (same place / several questions /
map vs land / matched-state control / structure vs access). Softened the
older-essay sentence and the closing line so they do not read as a version
diff. Five sparse S4 schematics added to `src/make_conceptual_figures.py`
(`s4a`--`s4e`); not a single packed infographic. Main text gains a hiker
primer box after Figure 1. S6 remains internal.

== 2026-08-31 --- pr_9: C1/C3 non-triviality and package consistency

C1 alone is not distinctive; empirical content is C2/C3. C3 is not generic
covariate conditioning. Latent $xi$ restored in $a$ and the drift split;
chart estimates marked $hat(b)_x$ etc. Named summaries are non-equivalent
functionals, not projections of one kernel. Evidence class and inferential
claim class declared orthogonal; "ladder"/"climb" language removed. S4
hide-cites Langell 2026 keys in main-article order so APA letters match
(then a--i; now a--k after the 2026-09-01 DOI refresh). S4 retitled as
conceptual guide; Jacobian, hippocampal, autonomic, and "two minds"
wording tightened. No new figure, dataset, or mechanism.

== 2026-09-01 --- Zenodo DOI refresh (spindles, TA simulator, Rolón)

Public records for ORCID `0009-0006-6927-7456` (63 hits). Companion DOIs
updated where a public version exists:

- Spindle companion: `10.5281/zenodo.22206108` (v.0.1), two-dataset title.
  Not the earlier window paper `20038829`.
- Two-operator simulator: `10.5281/zenodo.22204100` (v.0.1), now cited in
  §9 / S3 instead of "remain in S3".
- Rolón-Martínez covariance-shape: `10.5281/zenodo.22229790` (v.0.1). This
  is the new empirical TA deposit, not DANDI 000363.
- Still unpublished: IBL2 discrete-flow STOP, AVB omission, DANDI 000574.
  DANDI 000363 has no manuscript and no public DOI.

Main-article Langell 2026 first-cite order is now a--k (simulator e,
TRN-VG f, Rolón g, Slow Branch h, spindles i, coma j, neighbourhood k).
No fourth empirical anchor. S6 remains internal.

== 2026-09-02 --- IBL2, AVB, DANDI 000574 DOIs

`python -m zenodo catalog` wrote `zenodo/langell_articles.json` (67 public
records). Companion DOIs:

- IBL2: `10.5281/zenodo.22231817` (v1.0).
- AVB omission: `10.5281/zenodo.22232650` (v1.0).
- DANDI 000574: `10.5281/zenodo.22243202` (v1.0).
- Empirical TA companion remains Rolón-Martínez `10.5281/zenodo.22229790`,
  not DANDI 000363.

First-cite order is now a--m (AVB k, 000574 l, neighbourhood m). No fourth
empirical anchor. S6 remains internal.

== 2026-09-02 --- pr_10 visual / notation freeze pass

Architecture remains frozen. Notation: empirical Jacobian $hat(J)_x$; P6 uses
measured $x_t$. Accessibility kinds $cal(L)$ / $K^h$ / $q$ / FAR distinguished.
Dendritic $M_b$ shortened in §9; detail in S3. Coma prose uses
predictive-spread summaries. Novelty: systematically and state-dependently
modulated; synthesis not new stochastic mathematics. Fig 2 enlarged; Fig 5
header separated from title; Fig 4 given a weak page break. DANDI 000458
dataset citation completed. Claim-class wording replaces leftover Level 1/4
in public text. Funding / competing-interest placeholders resolved. No new
dataset, mechanism, or theoretical layer.

== 2026-09-02 --- HELS-A simulator DOI

HELS-A companion: `10.5281/zenodo.22253543` (v.0.1), *Context-Conditioned
Access Operators Reshape Route Accessibility on Fixed Dynamical Landscapes*.
Cited in §9 and S3. First-cite order is now a--n (HELS-A h, Slow Branch i,
spindles j, coma k, AVB l, 000574 m, neighbourhood n). Not a fourth empirical
anchor. S6 remains internal.
