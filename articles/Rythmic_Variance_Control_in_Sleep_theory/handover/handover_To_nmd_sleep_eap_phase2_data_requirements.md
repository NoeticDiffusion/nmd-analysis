# Handover to NMD: data requirements for a faithful test of the sleep-EAP phase-coupling model (`qz(t)`/`bqg`)

**Date:** 2026-07-11
**From:** Analysis repo (Rhythmic Variance Control in Sleep theory / sleep-EAP formalization work)
**To:** NMD
**Status:** INFORMATIONAL / not urgent — no re-run is being requested right now. This
documents a schema gap found while scoping what a future NMD re-run would need to
supply, so the requirement is on record if/when a dedicated follow-up round is
prioritized.

---

## 1. Why you're getting this

Two internal review documents (`articles/Rythmic_Variance_Control_in_Sleep_theory/plan/02_response.md`
and `.../plan/03_more.md`) proposed a more mechanistic model of how the
Embodied Anchoring Principle (EAP) might operate in sleep than the tests in
the `RVC_SLEEP` manuscript could evaluate: a continuous phase-and-amplitude
gating function `qz(t)` and an event-efficacy interaction term `bqg`
(does endogenous event *strength* — slow-oscillation/spindle coupling —
modulate how strongly phase alignment affects the downstream geometry
response?), plus a genuine point-process/hazard formulation (§4A) and a
stage-general ("state determines carrier") extension to N3/REM (§8).

Before asking you for anything, we checked concretely — column by column,
not from memory — whether the two RichSleep exports already in this repo
(`event_phase_v2`, `event_level_richsleep.parquet`) could support that model
as written. They cannot, for one specific, well-defined reason (§3 below).
Three of the four things the review documents flagged as valuable turned out
to be answerable with **no NMD work at all** (§2) and are already being
implemented on the analysis side (diary 241/242/243,
`articles/RVC_SLEEP_peak_analysis/`); this handover isolates the one part
that genuinely requires new data from you.

## 2. What is *not* being requested, because it is already testable today

For context, so the ask in §3 is not mistaken for the whole model — these do
**not** need anything from NMD:

- **Corrected, full-power spindle-*onset* phase-locking test.** `event_phase_v2`
  already has phase at every detected event (23,029 onsets across 24
  subjects, not just the 190-event geometry-valid subsample RVC_SLEEP's
  original Mål B used). Re-running with a proper subject-rotation surrogate
  null and a freely-estimated mean direction (rather than testing against
  phase zero) uses data already delivered. Done: `articles/RVC_SLEEP_peak_analysis/src/11_richsleep_maalb_corrected.py`
  (diary 241) — this is also where the *peak*-phase (not onset) respiratory
  coupling finding came from.
- **Onset-vs-peak-phase comparison.** `event_phase_v2` already has phase at
  two reference points per event (`phi_*_onset`, `phi_*_peak`); comparing
  locking strength between them needs no new export.
- **Approximate `bqg` test using a weak endogenous-strength proxy.**
  `event_level_richsleep.parquet` already has `event_duration_sec` and
  `event_confidence`, which can stand in for true endogenous event strength
  (`qe`) as an explicitly-labelled *approximation*, not the real slow-oscillation/
  spindle-coupling quantity. Done: `articles/RVC_SLEEP_peak_analysis/src/13_peak_phase_alignment_moderation.py`
  (diary 243) — reported as fragile/exploratory, precisely because it is only
  an approximation of the model the review documents actually describe.

## 3. What genuinely requires new columns or a new export

We inspected both RichSleep exports directly:

- `RichSleep_resolved/phase_resolved_v2/*_event_phase_v2.parquet` (24 files,
  14 columns: `subject`, `onset_sec`, `peak_sec`, `duration_sec`,
  `event_type`, `phi_cardiac_onset`, `phi_cardiac_peak`, `phi_resp_onset`,
  `phi_resp_peak`, `rr_interval_ms_at_onset`, `inhale_at_onset`,
  `hep_amplitude_pre_far`, `cardiac_phase_quality`, `resp_phase_quality`).
- `results/rvc_sleep_20260709/09_richsleep_verification/event_level_richsleep.parquet`
  (93 columns — full list available on request, but confirmed to contain no
  match for any of the items below).

**Neither export contains slow-oscillation (SO) amplitude, spindle
amplitude/sigma-power, an SO-spindle coupling index, or spindle frequency.**
This is already flagged as an open limitation in the RVC_SLEEP manuscript
itself (`frequency_hz`/sigma-power "not available in the current NMD
event-locked export schema") — this handover just makes the *downstream
consequence* of that gap explicit: it is the one thing blocking a faithful
implementation of `02_response.md`'s model, specifically:

1. **The real `qz(t)`/`bqg` test (`02_response.md` §3, §5).** As proposed,
   this needs, per spindle event: SO amplitude (or SO presence/phase, if
   detected independently), spindle amplitude/sigma-power, and an
   SO-spindle temporal-coupling index (e.g. spindle-peak latency relative to
   the nearest SO up-state, or a coupling-strength score). None of these
   exist today; §2's `event_duration_sec`/`event_confidence` proxy is a
   deliberately weaker stand-in. **This is the single most valuable request
   in this document if a faithful sleep-EAP test is ever prioritized.**
2. **A continuous phase time series, plus a genuine "non-event" risk set.**
   Both the point-process/hazard formulation (§4A) and a legitimate
   within-subject time-shift surrogate (`02_response.md` §7, alternative 4)
   need phase sampled continuously (or at matched non-event control times),
   not only at each detected spindle. Today we only have phase *at* each
   detected event, never off it — there is no "background" phase stream or
   matched non-event timestamp catalog to compare against.
3. **A multi-stage phase-resolved export (N3 slow oscillations, REM theta).**
   `event_level_richsleep.parquet` carries a `stage` column, but the
   phase-resolved export (`event_phase_v2`) is spindle-specific and
   N2-dominated. The "state determines carrier" framework (`02_response.md`
   §8) cannot be tested for N3/REM without a new, stage-aware extraction
   (SO detection for N3, theta-band phase for REM).

**Cross-dataset note (not really an ask, more a feasibility flag):** even if
the above were extracted for RichSleep, a cross-dataset replication of the
respiratory-coupling result specifically would likely stay RichSleep-only
regardless of any RichSleep re-run, because ANPHY has no respiration channel
(ECG-only) and BOAS's respiration coverage is mostly missing. Worth
confirming from your side whether that channel-availability picture has
changed, but we are not expecting it to.

## 4. A hard architectural limit this cannot fix (documented for completeness, not a request)

Independent of any re-run: `coords_9d` is fixed at 1 value per 30 s epoch
(already documented in `phase_resolved_v1/run_meta.json`). Even with full
SO/spindle amplitude and coupling data, any `bqg` test will therefore always
use one integrated geometry delta per spindle event, never a continuous,
within-event-phase-resolved geometry signal. This is a detector/epoch design
constraint, not something a re-run with different flags would change — flagging
it here only so nobody re-derives the same conclusion again in a future round.

## 5. Suggested priority, if this is ever picked up

Per `03_more.md`'s own ordering, adapted to this handover's scope:

1. (No NMD action — already in progress, §2.)
2. (No NMD action — already in progress, §2.)
3. **If prioritized:** SO/spindle amplitude, sigma-power, SO-spindle
   coupling index, and spindle frequency, added to `event_phase_v2` and/or
   `event_level_richsleep.parquet` (item 1 in §3) — this alone would unlock
   the real `qz(t)`/`bqg` test and is the highest-value single addition.
   The continuous-phase/non-event risk-set (item 2) and multi-stage
   extension (item 3) are logically separate, larger asks, useful mainly if
   the hazard-model or N3/REM generalization is specifically wanted.

## 6. What is NOT requested right now

- No re-run, re-export, or schema change is being requested at this time —
  this is a documentation-only handover.
- No changes to any existing RichSleep, ANPHY, or BOAS ingest.
- No blocking dependency on any current manuscript: `RVC_SLEEP` and
  `RVC_SLEEP_peak_analysis` are both already complete and submission-ready
  using only data already delivered; nothing in either article is waiting on
  this.
