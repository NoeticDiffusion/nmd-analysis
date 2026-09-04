#import "resuscitation_template.typ": *

#show: resuscitation-template.with(
  title: "Supplementary clinical interpretation",
  short-title: "Coma Clinical Summary",
  authors: (),
  affiliations: (),
  corresponding-author: "",
  article-type: "Supplement",
  show-summary: false,
)

#align(center)[#text(size: 9pt)[Author information is withheld for blinded peer review.]]


= Scope

This supplement provides a concise clinical reading of the pooled secondary analysis.
It does not provide a clinical decision rule.

The study reports group-level differences in derived short-horizon EEG dynamical
features between patients with later CPC 1 and CPC 5 in the first `12 h` after
EEG-anchor. The primary cohort contained `281` patients (`141` CPC 1 and `140` CPC 5).

== What the results mean

The most defensible interpretation is that the outcome groups differed in the
organization and recording-to-recording variability of derived EEG features. This is
compatible with differences in early EEG dynamics, but it does not show a mechanism,
consciousness, neural viability, or individual-patient prognostic accuracy.

The restricted prediction comparison showed an internal AUROC increase after adding
the derived features. It was not a comparison with contemporary multimodal
neuroprognostication, because the locked export lacks serial examination, SSEP,
pupillometry, biomarkers, neuroimaging, and expert EEG interpretation.

== What the results do not support

The results should not be used to:

- predict outcome for an individual patient;
- guide WLST or other treatment-limitation decisions;
- identify a precise physiological or prognostic hour after cardiac arrest;
- claim independence from sedation, artifact, mortality, or treatment pathways; or
- claim superiority to standard multimodal prognostication.

The primary timing analysis is relative to EEG-anchor, not a direct ROSC-to-EEG clock.
The hourly profile is exploratory; a circular-shift null did not support a precise
peak-hour claim. `CPC 5` is not a brain-specific endpoint and may capture systemic
illness, mortality, treatment limitation, and site pathways. WLST, time-of-death,
sedation burden, and direct artifact measures were unavailable.

== What would strengthen clinical relevance

The necessary next steps are independent prospective validation of a frozen feature
set, explicit treatment-pathway and sedation data, direct artifact measures, a
ROSC-to-recording clock, and comparison with conventional EEG interpretation and
multimodal prognostic workflows.

/*

== 1. Better outcome was associated with broader nearby future dynamics, not simply a shift in one static EEG level

The strongest reachability rows indicate that the better-outcome group had a broader
and more persistent short-horizon state-space organization. In the manuscript's
language this appears in `tube_d_eff_median`, `persistence_log_det_median`, and
`persistence_log_eig_var_median`.

The safest clinical translation is:

- better-outcome patients retained a wider nearby repertoire of measurable neural movement,
- that repertoire was not only broader but also more temporally organized,
- and the poor-outcome group looked more constrained or less sustainably organized on this exported surface.

This should not be read as proof of consciousness, preserved cognition, or any single
mechanism. It is a group-level descriptor of how the early EEG dynamics appear to be
structured over short horizons.

== 2. Poor outcome looked more locally expansive and less stable across recordings

The Jacobian layer points in the opposite direction from the reachability-breadth story:
`CPC 5` patients had higher local expansion and deformation summaries, while `CPC 1`
patients had lower `MNJ` spectral-radius and Frobenius-norm anchors.

The between-run variability results add a second clinically interesting point.
In the recording-complete subset (`n = 130`), poor-outcome patients showed larger
between-run fluctuation in `tube_capture_gate_median` and
`persistence_hysteresis_log_det_median`.

Clinically, the restrained reading is:

- worse outcome was not only associated with a different average geometry,
- it was also associated with less stable geometry across recording sessions,
- which is compatible with reduced attractor stability or less reliable maintenance of organized dynamics.

That remains an interpretation, not a validated mechanism. The study does not prove
why those patients fluctuate more.

== 3. The timing signal is early and suggestive, but not precise enough for hour-specific claims

Some of the separation appears early. For example, `tube_d_eff_median` is already
positive in `0_1h` and reaches its largest observed values around `2_3h` to `3_4h`.
However, the subject-wise circular-shift null in `S3` does *not* support a strong
claim that those observed peaks mark a precise biologic hour of maximal discrimination.

For clinicians, this means:

- early post-anchor structure is present,
- broad early-hour enrichment is plausible,
- but the current data do not justify statements such as "the decisive geometry window is exactly 2-3 h."

The timing axis is also anchored to EEG start, not to a validated ROSC-to-recording
clock. So the hourly bins should be read as anchor-relative monitoring windows rather
than as exact post-arrest physiologic phases.

== 4. Late-window (`12_24h`) exploratory pattern differs from the early-window hierarchy

In the exploratory late-window rerun (`12_24h`), the strongest globally corrected
rows shifted toward cone/tube log-eigenvalue and kappa branches (for example,
`tube_log_eig_var_median`, `cone_log_eig_var_h1..h4_median`, and
`cone_kappa_h1..h4_median`), with additional support from `MNJ 3D trace` and
`MNPS 9D e_s` rows.

Clinically, this means the later-window signal profile may not be a direct replay of
the early `0_12h` pattern. The safer interpretation is that early and late windows may
weight different geometry subfamilies rather than expressing one fixed single-layer
signature across all post-anchor phases.

This late-window branch should still be treated as exploratory and multiplicity-sensitive:
the prespecified five-row late-window family is informative, but in the global-pool
correction it is no longer jointly BH-FDR-positive.

= How to read the geometry clinically

The manuscript necessarily uses geometric language, but the safest clinical translation is simple.

- `MNPS` / state-space position: where the exported physiology tends to sit.
- Reachability metrics: how broad or constrained the nearby future movement appears to be.
- Jacobian metrics: how strongly the local rules of motion appear to expand, contract, or deform.
- Between-run variability metrics: how stable or unstable those summaries are across a patient's recording sessions.

These are descriptive layers for organizing physiology. They are not direct disease
mechanisms, and they are not yet validated clinical entities.

= How to read the predictive increment clinically

The predictive result is best understood as bounded complementarity, not as a ready-made
biomarker. Adding the fixed five-feature geometry layer raised internal AUROC from
`0.599` to `0.662` in repeated cross-validation, and the leave-one-subject-out result
remained directionally supportive.

That is enough to say the geometry contains information not fully captured by the
`limited_clinical_only` + qEEG baseline available in the locked export.

It is *not* enough to say:

- that the model is ready for bedside use,
- that it would outperform a full modern prognostication workflow,
- or that the geometry is already validated under prospective external deployment conditions.

The export also omits several clinically important variables, and the whole pipeline
should be read as internal validation after external preprocessing rather than as a
fully deployment-like test.

A specific reading trap is worth flagging explicitly. The `clinical+qEEG` comparator
in this ladder (labeled `limited_clinical_only` in the main article) is not a stand-in
for real-world clinical judgment. It is capped at the `14` clinical variables the
locked export happens to preserve, and it omits SSEP, quantitative pupillometry, motor
score, neuron-specific enolase, and structural neuroimaging — all standard inputs to
contemporary multimodal neuroprognostication, and all associated with meaningfully
higher discrimination in the published literature than the `~0.60` AUROC reported for
this restricted baseline. The geometry layer's `+0.062` AUROC gain is measured against
that same restricted baseline, not against full clinical practice. The honest clinical
reading is "geometry adds information beyond this locked, feature-poor comparator,"
not "geometry beats standard-of-care neuroprognostication."

= The main clinical caution

This paper is easier to overread than many case-control EEG studies because the endpoint
is clinically serious and the effect sizes are sometimes large. The caution therefore
matters more, not less.

The central limitation is that `CPC 5` is not a pure neural endpoint. Without explicit
WLST, time-of-death, sedation burden, and fuller care-pathway annotations, the results
cannot cleanly separate recovery-linked neural geometry from treatment-pathway and
severity-pathway effects.

The artifact boundary also remains incomplete. Direct artifact burden is unavailable in
the locked export, so the current QC package relies on coarser proxies such as channel
count, channel coverage, and usable-window summaries. Those checks argue against a
trivial coverage-only explanation, but they do not prove full artifact independence.

= A restrained clinical bottom line

If the paper were summarized in clinic-facing language, the most defensible wording
would be close to this:

Early post-arrest EEG in patients with later good versus poor neurological outcome
differs not only in average state but also in short-horizon geometric organization.
Better-outcome patients show broader and more persistent nearby dynamics with lower
local expansion, while poor-outcome patients show more constrained or unstable geometry.
Those signals are clinically interesting at group level, but they are not yet a bedside
prognostic tool and should not be interpreted independently of the major endpoint and
timing limitations.

= What clinicians should not conclude

This supplement is meant to reduce overinterpretation. The current article should *not*
be used to conclude that:

1. one NDT/NMD metric can predict outcome for an individual comatose patient,
2. the geometry isolates brain-intrinsic viability independently of WLST or mortality pathways,
3. the strongest observed hour bins identify an exact prognostic time window after arrest,
4. the current model outperforms full standard neuroprognostication practice,
5. or the retained metrics are already ready for interventional or withdrawal decisions.

= What would increase clinical confidence

The clinically most useful next steps would be:

1. replication in an independent post-arrest cohort with a prospectively frozen metric set,
2. explicit linkage to sedation, WLST, time-of-death, neuroimaging, and somatosensory evoked potential data,
3. more direct comparison against conventional EEG prognostic features and expert EEG interpretation,
4. validation using a true ROSC-to-recording clock rather than anchor-relative hourly bins,
5. and stronger artifact-aware analyses with preserved upstream burden measures.
*/

#bibliography("cardiac_arrest_comatose_references_blinded.bib", style: "resuscitation-vancouver.csl", title: none)
