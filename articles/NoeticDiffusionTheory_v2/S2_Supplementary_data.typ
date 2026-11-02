// S2 Supplementary Data — canonical companion sources for this article.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "S2 Data - NDT",
  subtitle: "Canonical source freeze for every empirical number in this article",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

#import "langell_citations.typ": langell-cite
#show cite: langell-cite

= Source-binding rule

Every empirical number in the main text must point to one canonical companion
artifact and, where relevant, one frozen result bundle. Intermediate or
superseded merges are not used. This table is the freeze.

#figure(
  kind: table,
  clean-table(
    columns: (1.15fr, 2.0fr, 1.7fr, 1.9fr),
    align: (left, left, left, left),
    inset: 4.5pt,
    table.header([*Anchor*], [*Canonical article*], [*Frozen bundle / contract*], [*Numbers used here*]),
    [Spindles],
      [Sleep Spindles Briefly Shift Cortical Network Geometry in Two Independent Overnight EEG Datasets],
      [ANPHY $N=27$; BOAS/ds005555 $N=128$; RichSleep $N=24$; Pass A/B/C 2026-07-03],
      [Timing $d_n$: ANPHY $+0.106$ ($q=0.009$), BOAS $+0.165$ ($q=0.011$); matched-control specificity incomplete],
    [Coma],
      [Recovery-Linked Neural Geometry After Cardiac-Arrest Coma],
      [I-CARE PhysioNet 2.1; invalidity-fixed merge, 2026-06-06],
      [$301$ analyzable patients, $5322$ runs; $281$ CPC 1 vs 5 ($141$/$140$); persistence $d=-0.909$ and $0.896$; tube $d=0.838$ ($0.786$ in $0$--$1$ h); AUROC $0.599 -> 0.662$],
    [Meso--macro],
      [Trial-aligned associations between Neuropixels proxies and surface EEG during cortical stimulation in head-fixed mice],
      [DANDI 000458 Claar/Rembado Neuropixels + surface EEG; NMD EEG-only local-linear chart; alignment incompletely validated],
      [Median subject $r = 0.406$ (LFP SD with EEG SD) and $r = 0.395$ (spike rate with EEG spectral entropy), claim class 1, conditional on nominal event labels; residual-variance fraction $0.856$ (archived diagnostic $0.8557$), claim class 4 fail],
  ),
  caption: [Canonical sources. Do not substitute a later or earlier bundle without rewriting both this table and the main-text sentences that cite it. Companion analyses: @langell2026_rvc_spindles; @langell2026_coma_v011; @langell2026_dandi000458. Dataset records remain @wei2024_anphy_sleep, @ds005555_1_1_1, @amorim2023icare, and @dandi000458.],
) <tab:s2-sources>

= What is not the coma source

A corrected-ComBat merge dated `20260602` reported $298$ analyzable patients
($278$ in the extreme-outcome contrast in some ledgers), pooled
`tube_d_eff_median` $d = 0.638$, and a predictive increment near AUROC
$0.595 -> 0.687$. That merge is a documented intermediate. The canonical
article in the canonical coma companion is the *invalidity-fixed* pooled
synthesis of `20260606_combined_invalidityfix`, which restored $301$/$281$ and the AUROC pair
$0.599 -> 0.662$. Numbers in this article follow that companion, not the ComBat
intermediate.

= Coma layer summary (canonical article)

Copied from the frozen companion, not re-estimated here.

#figure(
  kind: table,
  clean-table(
    columns: (1.8fr, 1.1fr, 1.4fr),
    align: (left, left, left),
    inset: 4.5pt,
    table.header([*Layer*], [*Pooled $d$*], [*Role*]),
    [persistence hysteresis log-det], [$-0.909$], [strongest reachability volume-dynamics separator],
    [persistence log-det], [$+0.896$], [reachability volume companion],
    [tube effective dimensionality], [$+0.838$], [lead dimensionality; $+0.786$ already in $0$--$1$ h],
    [MNJ 9D spectral radius], [$-0.603$], [aligned, cohort-heterogeneous],
    [MNJ 3D Frobenius], [$-0.499$], [aligned, cohort-heterogeneous],
    [MNPS 9D spread], [$-0.302$], [descriptive, not the lead],
  ),
  caption: [Pooled CPC 1 versus CPC 5 anchors from the canonical coma article. Positive $d$ means higher in CPC 1.],
)

= Spindle timing versus specificity

This article uses the *timing* estimand (event versus far pre-event baseline)
as the primary spindle constraint. The event-versus-matched-N2 contrast is
reported in the companion as incomplete: several endpoints are
baseline-dominated, and $d_n$ changes sign across datasets for that reason.
Reachability was not computed. EAP moderation of the geometry effect is
rejected under the primary protocol. Peak-phase respiratory locking is a
separate RichSleep companion and is not a second theoretical anchor.

= Dissociation matrix sources

Rows in the main-text dissociation table and Figure 5 are companion constraints,
not additional anchors. Canonical sources are the corresponding companion
articles. Anesthesia and epilepsy rows in
Figure 5 remain unpaid (not tested), not hidden positives.

The three added matrix rows are likewise not fourth anchors.

#figure(
  kind: table,
  clean-table(
    columns: (1.2fr, 1.9fr, 2.0fr),
    align: (left, left, left),
    inset: 4.5pt,
    table.header([*Matrix row*], [*Canonical companion*], [*Numbers / ceiling*]),
    [Expected-stimulus omission (VISp)],
      [Allen Visual Behavior omission geometry @langell2026_avb_omission],
      [Median $delta approx 0.980$, 30/30 sessions; AVB-adapted chart; Jacobian, diffusion, and reachability untested],
    [IBL chart readout],
      [Discrete chart-transition readout @langell2026_ibl2],
      [Population decoder PASS (median accuracy $0.588$, $p_"perm" = 0.0030$); discrete-flow operator STOP (held-out residual $approx 1.001$)],
    [Human MTL--scalp],
      [DANDI 000574 Sternberg analogue @langell2026_dandi000574],
      [Primary pairs $r = 0.100$ and $r = 0.062$ fail conjunctive nulls ($n = 9$); design-specific negative, not a 000458 replication],
  ),
  caption: [Matrix-only constraints imported from the m3-bridge freeze. They bound recoverability; they do not expand the three-anchor spine.],
) <tab:s2-matrix>

#show bibliography: it => {
  show "(2026a). Sleep Spindles": [(2026j). Sleep Spindles]
  show "(2026b). Recovery-Linked": [(2026k). Recovery-Linked]
  show "(2026c). Trial-aligned": [(2026b). Trial-aligned]
  show "(2026d). Omission of an Expected": [(2026l). Omission of an Expected]
  show "(2026e). A Discrete Trial-to-Trial": [(2026c). A Discrete Trial-to-Trial]
  show "(2026f). Scalp EEG variance": [(2026m). Scalp EEG variance]
  it
}

#bibliography("references.bib", style: "apa")
