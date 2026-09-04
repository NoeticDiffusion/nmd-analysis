# 001 — ds004587 Illusion-Game EAP: data-contract verdict

## Decision

**No-go for the planned rest-versus-illusion EAP article.**

The result is not a theoretical failure of EAP. The release has no rest EEG,
so no neural rest-versus-illusion comparison exists to estimate. It also lacks
an auditable bridge from trial behavior to EEG windows.

## What is internally validated

- The refreshed NMD run
  `neuralmanifolddynamics_ds004587_20260712_081757` exports MNPS/MNJ,
  raw physiology features, `anchor_state`, and `anchor_quality` across 57
  illusion-game H5 files.
- The run-01 IG-only QC/label audit establishes 47 EEG participants, no rest
  rows, and no exported trial/behavior fields.
- The composite `anchor_index` fails a gross-scale integrity screen and is
  excluded.
- The exploratory IG-only participant-median association families contain no
  BH-FDR survivor.

## What remains a plausible interpretation

The sign-stable negative `resp_anchor_index`--Frobenius screen may justify a
future preregistered IG-only study after timing validation. Its bootstrap
interval crosses zero and it is FDR-non-significant, so it is not a result to
headline or use as EAP support.

## What is not supported

- a rest-versus-illusion neural effect;
- trial-level modulation by illusion family or strength;
- phase-resolved cardiorespiratory coupling;
- any causal anchor-to-geometry mechanism.

## Next decision

Either acquire an EEG source with rest recordings for the original question,
or explicitly reframe this branch as an IG-only methods/data-contract note
after resolving behavioral timing and the composite-anchor defect.

## Addendum — 2026-07-13, composite-anchor defect resolved

The composite-anchor defect referenced above and in the "next decision" is
resolved: NMD export `neuralmanifolddynamics_ds004587_20260712_111138`
passes the scale-integrity gate for `anchor_index` and every anchor
component. The IG-only screen was re-run including `anchor_index`; the
decision, and "what is not supported," are unchanged. The previously noted
`resp_anchor_index`--Frobenius-norm point estimate is substantially weaker
under the corrected export ($r_s = -0.07$, was $-0.26$) because that
composite is a cohort-wide robust-z index that the fix necessarily
recomputed for every participant; it should no longer be described as a
"sign-stable negative" screen worth a future preregistration on its own
merits — it is now a small, non-significant, FDR-non-surviving estimate
like every other anchor-geometry pair tested. The remaining decision
(acquire rest EEG, or reframe as an IG-only data-contract note) is
unchanged.
