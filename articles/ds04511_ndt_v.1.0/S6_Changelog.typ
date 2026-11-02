// S6 Internal Changelog — ds004511 NDT v1.0.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S6 Internal Changelog",
  short-title: "S6 Changelog - ds004511 NDT v1",
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

Internal working document for the ds004511 NDT v1.0 article branch. Record how
the analysis result was obtained, which data and analysis artifacts were used,
and which decisions affect interpretation. Do not copy local raw-output paths
into the public manuscript.

= Analysis provenance

- Dataset accession: OpenNeuro ds004511.
- Measurement-run identifier: `neuralmanifolddynamics_ds004511_20260921_050009`.
- Coordinate contract: `subject_anchored`.
- Article code: `articles/ds04511_ndt_v.1.0/src`.
- First contrast panel: occupancy `(m,d,e)`, MNJ invariants, L1 local law,
  recording-level reachability summaries. Rest / CC / GG, complete-case
  within-subject.
- Second panel: chart-Jacobian α plus lag-1 L2/L3 one-step identities.
  Separate Wilcoxon family. Lag-2 omitted.

= Changelog

== 2026-09-21 — Article folder and first src cut

- Copied article template to `articles/ds04511_ndt_v.1.0`.
- Added Apollo-style G0–G2 collection and an exploratory task-contrast runner.
- Task labels come from the NMD stem only. `sub-S200203` Gambling remains missing.
- Status: exploratory; G3/G4 not locked. Occupancy is not MNJ and not reachability.

== 2026-09-21 — L4 QC and L2/L3 panel

- Three L4 `a_q` failures: `post_dtype_psd_failure`, one recording per task.
- `reach_d_eff` treated as method-limited (most values pinned near 1).
- Lag-1 L2/L3 identified on 121/134 recordings. Chart-Jacobian α is not
  one-step L3 on this export (GG−Rest signs do not match).

== 2026-09-22 — Peer-review robustness and multiplicity revision

- Added a deterministic 100-window (400 s) chart-Jacobian alpha sensitivity
  analysis. All 134 recordings remain eligible and all three contrast signs
  agree with the full-recording analysis.
- Audited the non-overlapping task-duration ranges. L4 is available only as
  recording-level scalars and cannot be declared duration-independent from
  this export.
- Retained `reach_d_eff` as raw QC but removed it from substantive BH and
  Friedman correction families: 45 pairwise and 15 omnibus tests remain.
- Added the complete frozen L1 family (four metrics by three contrasts plus
  four omnibus tests) to S2 rather than selecting significant L1 rows.
- Added a separate 400-s L1 sensitivity family. Drift-norm contrasts persist,
  while diffusion effects attenuate and diffusion omnibus rows no longer pass
  FDR in the fixed-prefix family.
- Added explicit citations for the dataset, NDT measurement boundary,
  Wilcoxon tests, and BH-FDR. G4 remains unlocked.

== 2026-09-22 — Common-support estimator interaction

- Added a separate exploratory chart-alpha versus one-step L3-alpha interaction
  runner on 121 common production-supported recordings.
- Calibrated each endpoint with a pooled median and $1.4826$ times MAD before
  subject-level task contrasts; no refit, interpolation, or zero filling.
- The GG--Rest and GG--CC standardized interactions are FDR-significant in a
  separate three-test family; the result is normalization-dependent and does
  not establish raw-unit effect differences or estimator equivalence.

== 2026-09-22 — Major peer-review revision

- Reframed the title and main argument around estimator dissociation rather
  than cortical layer specificity.
- Added verified external references on neural population representations,
  manifold dynamics, local linearization, data-driven operators, rotations,
  context-dependent dynamics, controllability, and EEG eye-state sensitivity.
- Added the supported mathematical bridge between local chart Jacobians and
  the qualified one-step matrix-log proxy; unsupported/non-real L3 leaves are
  not repaired or reinterpreted.
- Promoted the complete 12-row L1 hierarchy and fixed 400-s sensitivity into
  the main Results; retained full tables in S2 and S3.
- Added a frozen common-support concordance analysis and scatter plot. GG--Rest
  Spearman rho is -0.383 (n=32), with 12/32 same-sign pairs; no raw-unit
  comparison or new inferential family is claimed.
- Demoted the L4 certificate-count figure to S3 and foregrounded Rest-versus-
  active-task design limitations. Equal-duration L2/L3 refitting remains the
  next gate because no validated bounded refit path is present in this export.
