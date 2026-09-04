#import "../comatose_ndt/network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary - Recovery-Linked Neural Geometry 12-24 h Pilot After Cardiac-Arrest Coma",
  short-title: "Coma 12-24 h Clinical Summary",
  subtitle: "A cautious clinician-facing interpretation of the late-window pilot",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope

This supplement is written for clinicians and clinically oriented readers who want a plain-language reading of the `12_24h` coma pilot without having to work directly in the full geometry terminology.

The current frozen article release corresponding to this late-window line is archived on Zenodo.@langell2026_coma_v011

The goal is caution, not promotion. This pilot is:

1. a group-level observational measurement study,
2. not a validated bedside prognostic biomarker,
3. not a WLST-independent assay of neural viability,
4. and not a substitute for standard multimodal prognostication.

= What was compared

The pilot uses a no-regional subject-anchored `part1` export and focuses on the true `12_24h` slice after timing reconstruction. The important practical detail is that the processed root is mixed-bin: most runs are still in `0_12h`, and only `143` runs from `97` subjects belong to the actual late-window slice used for the inferential comparison.

The clinical contrast is still later `CPC 1` versus later `CPC 5` (`47` versus `50` subjects). As in the early-window paper, that outcome contrast should be read as recovery-linked rather than as a pure neural-viability label.@sandroni2021european

= Clinician-facing headline

The cleanest late-window message is not that the early geometry story simply continues unchanged. The cleaner message is that a later-window geometry signal is still present, but it is reweighted.

In practical terms:

- the late-window pilot is *not* led by `tube_d_eff_median`,
- the stronger fixed-family rows are instead a mixed-sign trio,
- and the current slice looks less Jacobian-led than the early `0_12h` article.

That is clinically interesting because it suggests that early and later monitoring windows may weight different geometry subfamilies rather than replaying one fixed hierarchy across the whole post-anchor period.

= Three clinically relevant takeaways

== 1. Late-window geometry still separates groups, but not in the same way as the early-window paper

In the early `0_12h` article, the most visible main-text reachability story centered on broader effective dimensionality and strong persistence-log-determinant separation. In the late-window pilot, the fixed five-row family shifts.

The corrected late-window rows are:

- `persistence_kappa_median`, higher in `CPC 5`,
- `tube_a_operator_norm_median`, higher in `CPC 1`,
- `tube_capture_gate_median`, higher in `CPC 1`.

Clinically, the safest translation is that later good and poor outcome groups still differ in short-horizon geometry, but the later window appears to weight anisotropy/conditioning and transport-style summaries more strongly than the early-window paper did.

== 2. The late-window signal is mixed-sign rather than uniformly “better is broader”

The early-window paper could be summarized more simply: better outcome was associated with broader and more persistent short-horizon geometry. The late-window pilot is less one-directional.

Here, one of the stronger corrected rows (`persistence_kappa_median`) is higher in `CPC 5`, while two others (`tube_a_operator_norm_median` and `tube_capture_gate_median`) are higher in `CPC 1`.

Clinically, that means the late-window pilot should *not* be overtranslated as “good outcome always equals larger geometry.” A more careful reading is:

- later-window separation is present,
- but the direction depends on which subfeature of reachability is being summarized,
- and the current pilot is more consistent with reweighting of geometry subfamilies than with a single monotone severity axis.

== 3. Repeated-run instability is only exploratory in this late window

The manuscript includes a repeated-run MAD/IQR pass because instability across recordings may itself be informative. But the late-window slice is sparse: only `5` subjects per metric meet the strict `>=3`-run threshold, so no confirmatory repeated-run contrasts are available there.

Under the exploratory `>=2`-run threshold (`12` subjects total; `8 CPC 1`, `4 CPC 5`), the strongest MAD row is `persistence_log_eig_var_median_mad`, which is larger in `CPC 5`.

Clinically, the restrained reading is:

- there is a hint that poor-outcome patients may be more unstable on persistence-side summaries even later in the course,
- but the repeated-run evidence is much too sparse to make a confident late-window instability claim.

= How to read the geometry clinically

The safest clinical translation remains simple:

- `MNPS`: where the exported physiology tends to sit or spread.
- Reachability metrics: how broad or constrained the nearby future movement appears to be.
- `MNJ`: how strongly the local rules of motion appear to expand or deform.
- Between-run variability: how stable those summaries are across repeated recordings.

These are organizing descriptors of physiology, not direct disease mechanisms and not validated clinical entities.

= The main clinical caution

This pilot is easier to overread than it should be, because it is tempting to treat it as a “late window confirmation” of the early-window paper. That is not the safest framing.

The main limitations are:

1. the current export is `part1`-only,
2. the full root is mixed-bin and only a minority of runs belong to the true `12_24h` slice,
3. the fixed-family signal is mixed-sign and therefore harder to summarize as one simple physiologic direction,
4. repeated-run coverage is sparse,
5. and the locked export still does not resolve WLST, time-to-death, sedation burden, or direct artifact burden.

The late-window pilot should therefore be read as bounded continuity evidence rather than as a clinically mature second-window biomarker study.

= What clinicians should not conclude

This supplement is meant to reduce overinterpretation. The current pilot should *not* be used to conclude that:

1. one late-window NDT/NMD metric can prognosticate an individual comatose patient,
2. the late-window geometry isolates brain-intrinsic viability independently of mortality-pathway effects,
3. the mixed-sign trio already defines a clinically frozen late-window panel,
4. the late-window results are pooled and stable across `part1` and `part2`,
5. or the current pilot is ready to inform bedside withdrawal or escalation decisions.

= What would increase clinical confidence

The clinically most useful next steps would be:

1. a pooled `part1` / `part2` late-window rerun under the same fixed metric contract,
2. better repeated-run coverage inside the true `12_24h` slice,
3. explicit linkage to sedation, WLST, time-to-death, imaging, and conventional EEG interpretation,
4. stronger artifact-aware analyses with preserved upstream burden measures,
5. and direct comparison of the early-window and late-window hierarchies in the same patients under a frozen protocol.

= A restrained clinical bottom line

If this pilot were summarized in clinic-facing language, the most defensible wording would be close to this:

Late post-arrest EEG geometry still differs between patients with later good and poor neurological outcome, but the pattern is not a simple replay of the early-window paper. In the current `12_24h` slice, the separation is mixed-sign and centered on a later-window reachability trio rather than on effective dimensionality alone. That is clinically interesting as a group-level signal, but it remains a bounded `part1` pilot with major endpoint, timing, and coverage limitations rather than a bedside prognostic tool.

#bibliography("../comatose_ndt/cardiac_arrest_comatose_references.bib")
