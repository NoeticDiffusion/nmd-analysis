# EAP in wake vs. sleep, and whether Rhythmic Variance Control needs reformalizing

**Status:** exploratory synthesis / reflection note. Not yet tested, not a manuscript draft, not a change to any existing `.typ` file. Written to seed a possible future update to this folder's `manuscript.typ` (currently an unfilled `aa_template` scaffold).

**Empirical anchors:** this note is triggered by comparing two already-completed studies:

- `articles/RVC_SLEEP/Rhythmic Variance Control at Sleep Spindles Three-Dataset Replication.typ` (three PSG datasets, ANPHY/BOAS/RichSleep, N=179) — abbreviated **RVC_SLEEP** below.
- `articles/Neural flow geometry differentiates gambling and cognitive control/Neural flow geometry differentiates gambling and cognitive control despite matched sympathetic arousal.typ` (`ds004511`, N=44–45, wake) — abbreviated **GG/CC** below.

It also draws on `J:\repos\trn-vg\articles\TRN_VG\Thalamic Reticular Inputs Regulate Population-Level Response Geometry, Not Single-Unit Variability, in the Auditory Thalamus.typ` (mouse, optogenetic TRN silencing) — abbreviated **TRN-VG** below — and on the core theory document `articles/NDT/NoeticDiffusionTheory.typ` and the dedicated EAP test article `articles/embodied_anchoring/Cardiac autonomic state and neural manifold geometry co-vary non-monotonically across working-memory task phases.typ`.

---

## 1. The question as posed, and why it needs sharpening first

The triggering observation was: *"EAP doesn't show null in the gambling/wake study — so shouldn't that mean EAP doesn't work in sleep the way it does in wake?"*

Before reasoning about mechanism, the premise itself needs a correction, because as stated it overstates both sides:

- **GG/CC's EAP result is not a confirmed finding either.** The pre-specified nine-test EAP family (R6) has exactly zero FDR survivors. The numerically largest hit — `resp_anchor_index` × MNPS mobility `m` during cognitive control, partial Spearman controlling for HRV, `r = -0.41`, `p = 0.006` — fails Benjamini-Hochberg FDR across the family (`q ≈ 0.05`, just above the 0.05 line) and is explicitly reported in that manuscript as *"FDR-non-significant... a directionally suggestive, hypothesis-generating result rather than a confirmed finding."* The gambling-condition trend (`resp_anchor_index` × Frobenius norm, `r = -0.22`, `p = 0.16`) is sign-consistent across all 44 leave-one-subject-out iterations but is likewise not significant, and a second, block-level operationalization of the same correlation is weaker (`r = -0.14`, `p = 0.35`) and its bootstrap CI spans zero.
- **RVC_SLEEP's EAP result is not one undifferentiated null.** It is two nulls at very different power: a well-powered *tonic* proxy test (`cardioresp_anchor_index_pre_far`, 2,260–2,435 events across 24 subjects, clean null, `p` range ≈0.04–0.94, no FDR survivors) and a *phase-resolved* mechanistic test (Mål B onset-phase-locking, Mål C HEP-amplitude moderation — the "fairer" test of what EAP's equation actually proposes) that ran on only 190 events across the same 24 subjects, roughly a 12-fold smaller sample driven by necessary quality/staging filters, not by a different hypothesis.

So the honest comparison is:

> a *non-FDR-significant, sign-consistent trend* at `N≈44` in wake **vs.** a *well-powered clean null* (tonic proxy) plus an *underpowered clean null* (phase-resolved, fair test) in sleep.

That is a real and interesting asymmetry — but it is "unconfirmed-but-suggestive" vs. "null," not "confirmed" vs. "refuted." The rest of this note treats it as such.

**Separately, and just as important:** RVC's *core* claim — that sleep spindles act as endogenous, rhythm-defined variance-control events that leave a measurable signature in state-space geometry (a rise in the `d_n` endpoint at spindle timing) — *did* replicate across ANPHY and BOAS, and is corroborated by RichSleep's broader event-vs-control contrast. Only the *EAP/interoceptive-moderation add-on* to that mechanism (does pre-event bodily state predict the size of the spindle effect?) came back null. These are two different claims, and the rest of this note keeps them visibly separate — collapsing them into "does RVC work in sleep?" is exactly the conflation the master theory document itself warns against (see §3).

---

## 2. Side-by-side: what was actually tested, where

| Study | Test | Sample | Statistic | FDR outcome |
|---|---|---|---|---|
| GG/CC | 9-test EAP family (`resp_anchor_index` × 3 geometry summaries × 3 tasks, partial on HRV) | N=44–45 | largest: CC/`m`, `r=-0.41`, `p=0.006` | 0/9 FDR survivors (`q≈0.05`, boundary) |
| GG/CC | Gambling `resp_anchor` × epoch-level Frobenius (LOOSO check) | N=44 | `r=-0.22`, `p=0.16`, 44/44 LOOSO sign-consistent | not part of the 9-test family; not FDR-corrected; descriptive |
| GG/CC | Same, block-level Jacobian version | N=44 | `r=-0.14`, `p=0.35`, bootstrap CI `[-0.43, 0.16]` | spans zero |
| RVC_SLEEP (ANPHY+BOAS) | Pass C tonic-anchor moderation (2 delta modes × 3 anchor models × 9 endpoints) | N=27 / N≈35–128 (anchor-dependent) | 53/54 tests, no FDR survivors | 1 nominal exception not replicated under subject-level-slope check |
| RVC_SLEEP (RichSleep) | Dual-arm `cardioresp_anchor_index_pre_far`, 2 delta modes × 9 endpoints | N=24, 2,260–2,435 events | `p` range ≈0.04–0.94 | 0/18 FDR survivors |
| RVC_SLEEP (RichSleep, R6b) | Mål B: per-subject + second-order Rayleigh, spindle-onset phase vs. cardiac/respiratory phase | N=24, 190 events (~8/subject) | per-subject: 0/24 (both channels); second-order: cardiac `R=0.160, p=0.547`; resp `R=0.109, p=0.755` | no significance at either level |
| RVC_SLEEP (RichSleep, R6b) | Mål C: HEP-amplitude moderation of spindle-locked geometry, 2 delta modes × 9 endpoints | N=24, 190 events | `p` range ≈0.10–0.96 | 0/18 FDR survivors |
| `embodied_anchoring` (ds003838, wake WM task) | Direct within-subject anchor↔MNPS coupling | N=62–65 | "modest" | not FDR-significant; between-subject correlation null after FDR |

Two things stand out from this table that the "wake works, sleep doesn't" framing misses:

1. **GG/CC's own EAP result is closer in evidentiary weight to RVC_SLEEP's phase-resolved null than to a confirmed effect** — both are underpowered-but-suggestive-direction results at `N` in the 24–45 range.
2. **The one EAP test in this entire program with the largest sample (`embodied_anchoring`, N=62–65, wake) is also null** for the direct coupling test. So "wake" is not uniformly more favorable to EAP than "sleep" — the pattern so far is closer to *every single EAP test run to date, in any state, has failed to survive multiple-comparison correction*, with GG/CC's cognitive-control trend being the closest any of them has come.

This reframes the puzzle from "why does EAP work in wake but not sleep" to something narrower and more tractable: **"is there a real, if small, wake-biased signal for peripheral interoceptive coupling with cortical/manifold geometry, and if so, why might it be harder to detect during NREM sleep specifically?"**

---

## 3. What the master theory already says about this

`articles/NDT/NoeticDiffusionTheory.typ` already stratifies exactly this distinction, and had done so before RVC_SLEEP was run:

> `= Rhythmic Variance Control (RVC) and TRN gating <sec:rvc>` — names the thalamic reticular nucleus (TRN) as the hypothesized implementer of the true control signal `r_true(t)`, observed only through rhythmic proxies (`\hat r(t)`) derived from phase-amplitude coupling, SO–spindle coupling, and phase coherence (`@halassa2016 @crabtree2018`).

> `== Embodied Anchoring Principle (EAP) <sec:eap>` — *"EAP should be read as a Tier-2 extension of NDT: its predictions are intended for a later wave of interoception-focused and neurophenomenological studies, whereas the core Tier-1 tests concern the minimal MNDM, RVC/TRN-VG, and MNPS geometry."*

In other words, the theory itself already treats:

- **RVC-core** (endogenous rhythms — theta–gamma PAC, SO–spindle–ripple nesting, TRN-implemented) as the primary, Tier-1, better-grounded mechanism, and
- **EAP** (cardiac/respiratory/HEP-based peripheral entrainment) as a secondary, Tier-2, explicitly-labeled-as-exploratory extension, "intended for a later wave" of validation.

RVC_SLEEP's result pattern — Tier-1 core claim replicates across three datasets, Tier-2 EAP addition is null — is therefore close to what the theory's own tiering predicted as the more mature vs. less mature claim. It should be read as the tiering working as intended, not as a surprise that needs explaining away. The `embodied_anchoring` article (the dedicated first EAP test, wake, N=62–65) reaches the same qualitative verdict: condition-level co-modulation, but "the present observational design does not demonstrate causal gating of manifold dynamics by the anchor surface," and its own Limitations section explicitly flags "generalization to... sleep... requires separate empirical support" as an untested speculative extension at the time it was written. RVC_SLEEP is that follow-up test, and it came back null — which is informative, not anomalous.

---

## 4. External literature: what is actually established outside this repository

These are treated as **established external results** (peer-reviewed or, where noted, preprint) per the repository's research-discipline convention, independent of any NDT claim:

### 4.1 Respiration phase-locks sleep spindle timing at the population level, in humans

- Ghibaudo, Juventin, Buonviso et al., "The timing of sleep spindles is modulated by the respiratory cycle in humans," *Clinical Neurophysiology* 166 (2024): 252–261, `doi:10.1016/j.clinph.2024.06.014` (preprint: `doi:10.1101/2023.03.31.534952`). Full-night PSG, N=20 healthy adults. Both slow and fast spindles show significant, population-level non-uniform phase distributions relative to the respiratory cycle (occurrence peaking mid-to-late expiration); slow-wave down-states couple differently, clustering near the inspiration/expiration transitions.
- Schreiner, Petzka, Staudigl, Staresina, "Respiration modulates sleep oscillations and memory reactivation in humans," *Nature Communications* 14 (2023), `doi:10.1038/s41467-023-43450-5`. Shows SO–spindle complexes are phase-locked to respiration (non-uniform circular distribution in 18/20 participants) and, critically, that **the strength of this respiration–SO–spindle coupling predicts the fidelity of learned-content memory reactivation** — an independent, non-NDT demonstration that phase-resolved cardiorespiratory–cortical coupling during NREM sleep has functional consequences, which is exactly the kind of mechanism EAP proposes (a different outcome variable — memory reactivation, not MNPS geometry — but the same causal shape).

**This is directly comparable to, and more statistically favorable than, our own Mål B.** Ghibaudo et al.'s design pools *all* detected spindle events from all 20 participants into one distribution and runs a single population-level circular-uniformity test (Hermans-Rasson, an alternative to Rayleigh robust to multimodality) on the pooled angles. Our Mål B instead ran (a) a per-subject Rayleigh test requiring within-subject FDR significance on a median of ~8 events/subject, and (b) a second-order Rayleigh test on the 24 subject-level *mean* directions — a substantially more conservative, hierarchical design that discards both event count and within-subject concentration information. See §7 for a concrete proposed re-analysis.

### 4.2 Cardiac phase modulates spindle phase directly; general interoceptive-cortical coupling attenuates with sleep depth

- Lechinger, Heib, Gruber, Schabus, Klimesch, "Heartbeat-related EEG amplitude and phase modulations from wakefulness to deep sleep: interactions with sleep spindles and slow oscillations," *Psychophysiology* 52.11 (2015), `doi:10.1111/psyp.12508`. N=23. Two findings relevant here, pointing in different directions:
  - Heartbeat-evoked EEG amplitude and inter-trial phase locking (the HEP) *decreases* monotonically with increasing sleep depth (wake → N2 → N3), with a partial recovery in REM — a general attenuation of stimulus-locked cardiac-cortical coupling as sleep deepens.
  - Despite that general attenuation, **the QRS complex was found to modulate spindle phase specifically** — attributed to the rough correspondence between cardiac-cycle frequency and spindle frequency (~12–15 Hz) — i.e., a targeted, spindle-specific cardiac coupling that survives even though the generic HEP signature weakens.
- Two supporting attenuation results, both narrower in scope: Bocchio et al./MDPI (2021, `doi:10.3390/brainsci11081089`) find HEP amplitude further modulated by hypnotizability and interoceptive-sensitivity traits during sleep (not simply a fixed attenuation); a 2025 preprint (`doi:10.1101/2025.11.20.689416`) shows that part of the wake/REM-vs-N3 HEP difference is confounded by a cardiac pulse-artifact that is itself state-dependent (largest in wake/REM, smallest in N3 due to slow-wave masking) — a methodological caveat worth flagging rather than treating the attenuation literature as unimpeachable.

Net reading: cardiac–cortical coupling, measured as a generic evoked potential, is genuinely weaker in deeper NREM than in wake — but a *spindle-specific* cardiac-phase relationship has itself been reported in the literature, using an analysis design (QRS phase vs. spindle phase, not HEP amplitude vs. geometry) that differs from our existing Mål C (HEP-*amplitude* moderation of the *downstream* geometry effect). This is not the same test we ran, and is a candidate follow-up (§7).

### 4.3 The wake-to-sleep transition is a phase shift, not simply a loss, of respiration-brain coupling

- "Respiratory coordination of excitability states across the human wake-sleep cycle," *Progress in Neurobiology* (2025), `doi:10.1016/j.pneurobio.2025.102857`. Full-night EEG+respiration, N=23. Finds a *robust phase shift* in respiration-locked aperiodic (excitation/inhibition-balance) brain activity across the wake→sleep transition, and — notably — coupling becomes *more consistent* (lower inter- and intra-individual variability) moving from wakefulness into deeper sleep stages, not simply weaker.

This nuances a naive "interoceptive coupling just gets weaker in sleep" story: the mechanism may reorganize (different phase relationship, different consistency profile) rather than switch off, which matters for how any updated EAP formulation should be written (§8).

### 4.4 Respiration-cognition coupling grounds EAP's wake-side plausibility, independent of NDT

- Kluger & Gross, "Respiration aligns perception with neural excitability," *eLife* (2021), `doi:10.7554/eLife.70907`; Kluger et al., *Nature Communications* (2023), `doi:10.1038/s41467-023-40250-9`; and 2024/2025 work (JNeurosci `doi:10.1523/JNEUROSCI.2236-24.2025`, bioRxiv `doi:10.1101/2024.12.03.626336`) showing respiratory phase modulates task-evoked visual representations and decision-related processing during wake. This is the general literature base that makes an EAP-style wake effect plausible in the first place, independent of any NDT-specific claim — and is consistent with GG/CC's cognitive-control-condition trend being, of all nine tests run, the numerically closest to significance.

### 4.5 The TRN is the established circuit generator of spindles, via a rhythmic, GABAergic burst-mediated gating mechanism

- Classic reticular-thalamocortical "ping-pong" rebound-burst model (Steriade/von Krosigk lineage; see e.g. the mechanistic review at PMC4064116) and recent biophysical multi-compartment modeling of TRN subpopulations (PMC12454877): TRN neurons, when hyperpolarized, generate T-type-calcium-channel-mediated burst firing; these bursts produce large, often extrasynaptic-spillover GABAergic IPSCs in thalamocortical relay cells, which then rebound-burst and re-excite the TRN, closing a self-sustaining oscillatory loop that *is* the spindle. This is textbook circuit neuroscience, entirely independent of NDT.

This is the literature-level grounding for treating spindles as "rhythm-defined variance-control events" at all: the TRN mechanism *is*, mechanistically, a periodic, high-precision, network-wide gating event — which is the biological referent RVC's name is pointing at, whether or not NDT's specific MNPS/geometry claims turn out to be correct.

---

## 5. TRN-VG as a candidate mechanistic bridge — explicitly scoped

`J:\repos\trn-vg\articles\TRN_VG\...typ` and `J:\repos\trn-vg\project\plan.md` are a separate, already-completed reanalysis (Rolon-Martinez et al.'s Dryad dataset, PLOS Biology) that is, per its own project plan, framed as *"the most NDT-like test [of TRN-implemented variance control] because 'variance' can be defined relative to a known [population] manifold."* Its main finding:

> **Internal validated result:** optogenetic silencing of PV+ (but not SOM+/SST+) auditory-TRN neurons contracts the effective dimensionality (participation ratio) of simultaneously recorded MGB population noise covariance — beyond the control-virus arm's own effect, and independent of the manipulation's own mean-firing-rate (gain) change. Participation-ratio DiD = −2.30, permutation `p=0.005`, passing all 7 pre-specified stability/falsification checks (leave-one-mouse-out, evoked-specificity, unit subsampling, alternate window, shrinkage-vs-raw covariance, equal-mouse-vs-equal-session weighting). The same test fails its stability gate for SOM (4/7 checks).

This is real, causal (optogenetic), converging evidence that a **variance/dimensionality-gating channel, dissociable from mean-gain control, exists and is implemented by TRN input** — at least for the PV pathway, in mouse auditory thalamus. That is exactly the general architectural claim underlying both RVC (endogenous rhythms gate variance) and EAP (peripheral rhythms gate variance): a rhythm-controlled "variance channel" separate from a "gain channel."

**What this bridge does *not* show, and must not be allowed to imply:**

- No cardiorespiratory measurement was made in TRN-VG at all — it says nothing about interoceptive coupling specifically.
- The auditory MGB→TRN pathway tested is not the same thalamic sector/loop that generates human sleep spindles (which involve widespread TRN–thalamocortical loops during NREM, not tone-evoked auditory relay).
- The manipulation was exogenous optogenetic silencing, not an endogenous rhythm — it demonstrates the *channel* can be causally moved, not that the *endogenous rhythm* (as opposed to the experimenter) is the one moving it in this specific pathway.
- Species (mouse) and behavioral state (awake, task-engaged) both differ from RVC_SLEEP's human NREM-sleep setting.

So TRN-VG should be cited as **plausible interpretation / speculative-extension-grade support** for "a TRN-gated variance channel, dissociable from gain, is a real, demonstrable thing in the mammalian thalamus" — not upgraded to a direct empirical result about spindles, EAP, or cardiorespiratory coupling. It strengthens the *architectural* case for RVC-core (which the master theory already predicted via `@halassa2016 @crabtree2018` before this reanalysis existed) without saying anything new about the EAP-moderation question that motivated this note.

---

## 6. Candidate hypotheses for the wake/sleep EAP asymmetry

Given §1–§5, two non-exclusive, explicitly-labeled **plausible interpretations** are worth carrying forward — neither is adjudicated by anything in this note, both are testable:

### H1 — Power/design-artifact hypothesis

Our Mål B used a two-stage hierarchical test (per-subject Rayleigh requiring within-subject FDR significance on ~8 events/subject, then a second-order Rayleigh on 24 subject-level *mean* directions) that discards exactly the information a pooled first-order test uses. Ghibaudo et al. (§4.1) found a robust population-level effect using a pooled, all-events-pooled-across-subjects design. It is entirely possible that RichSleep's phase-resolved null is a design/power artifact, not a genuine absence of coupling in that dataset — this is directly checkable without new data (§7.1).

### H2 — State-dependent-coupling-strength hypothesis

The cited literature (§4.2, §4.3) shows real, state-dependent *changes* in interoceptive-cortical coupling across wake→NREM — not simply "on in wake, off in sleep," but a *phase shift* and a *change in consistency*, plus a generic HEP attenuation that coexists with a preserved spindle-specific cardiac coupling. This motivates treating EAP's coupling strength as itself state-dependent, and considering that during NREM the *endogenous* RVC channel (SO–spindle nesting, TRN-implemented, Tier-1) may be the dominant driver of the variance schedule, with the *peripheral* EAP channel playing a smaller, harder-to-detect or differently-phased role — rather than the two channels simply adding independently as the current equation assumes (§8).

These are not mutually exclusive: H1 could fully explain the RichSleep null (a reanalysis resolves it) even if H2 is also true in some weaker form; conversely H1 could fail (a proper pooled reanalysis still finds nothing) while H2 remains a live, separately-testable hypothesis about *why*.

---

## 7. Concrete, falsifiable next analyses (recommended only — none executed here)

1. **Pooled/mixed-effects circular reanalysis of Mål B**, mirroring Ghibaudo et al.'s design: pool all 190 RichSleep spindle-onset phase values (cardiac and respiratory separately) across all 24 subjects into one population-level circular-uniformity test (Rayleigh or Hermans-Rasson), with a subject-cluster permutation (shuffle subject labels, not raw angles, to preserve within-subject clustering) to guard against pseudo-replication from unequal per-subject event counts. This is a direct power-artifact check for H1 and requires no new data — only a different statistical treatment of the existing `event_phase_v2` export.
2. **A targeted cardiac-phase-modulates-spindle-phase test**, distinct from the existing Mål C: replicate Lechinger et al.'s specific claim (QRS-complex phase predicts spindle phase, motivated by the ~12–15 Hz frequency correspondence) rather than testing HEP *amplitude* as a *moderator* of the downstream geometry delta. This is a different, more targeted hypothesis than either existing Mål B or Mål C.
3. **Within-subject dose-response test**: if #1 recovers any per-subject phase-locking strength (e.g., subject-level mean-vector length), test whether that strength predicts the *size* of the subject's own spindle-locked `d_n` geometry rise — a more sensitive, continuous alternative to the existing binary/group-level moderator tests, and closer in spirit to Schreiner et al.'s coupling-strength-predicts-reactivation-fidelity result (§4.1).
4. **Explicit numeric side-by-side publication** of the GG/CC EAP effect sizes/FDR status against RichSleep's tonic and phase-resolved nulls (the table in §2, or a version of it) in any future write-up, so readers are not left with an implicit "confirmed in wake, refuted in sleep" impression that neither dataset actually supports.
5. **A literature-only discussion** (no new data) explicitly tying RVC's TRN-gating hypothesis (already in the master theory, §3) to TRN-VG's PV-specific dimensionality-contraction result, scoped exactly as in §5 — useful context for a future RVC_SLEEP-adjacent theory piece, not a new empirical claim.

None of these require touching RVC_SLEEP's frozen manuscript; #1–#3 are new analyses on already-exported data, #4–#5 are writing/synthesis tasks.

---

## 8. A possible reformalization sketch (speculative — not proposed for any manuscript)

This section is explicitly **speculative extension** grade. It is not a recommendation to change any existing equation, only a sketch of what a state-aware version might look like if H1 is ruled out and H2 gains support.

EAP's current variance-schedule-entrainment equation (`@eq:rvc` in `articles/NDT/NoeticDiffusionTheory.typ` and reused verbatim across `embodied_anchoring` and the GG/CC article) is:

```
r(t) → r(t) · [1 + γ_entrain · cos(φ_cardiac − φ_θ) · cos(φ_resp − φ_α)]
```

with `γ_entrain ≈ 0.1–0.3` treated as a fixed constant. Two speculative directions, kept separate because they make different claims:

- **Direction A (state-dependent gain, same functional form).** Let `γ_entrain` become `γ_entrain(state)`, e.g. distinct values for wake, NREM, REM, motivated directly by §4.3's finding that respiration-brain coupling changes phase and consistency (not just magnitude) across the wake-sleep transition. This is the minimal change: same equation, state-indexed coefficient. It is directly falsifiable by fitting `γ_entrain` separately per state once a phase-resolved wake dataset and a phase-resolved sleep dataset (e.g., a successful #1/#2 re-analysis) both exist.
- **Direction B (channel dominance / gating interaction, different functional form).** Instead of one universal peripheral term added to `r(t)`, treat NREM's dominant variance-control channel as the endogenous RVC term (`r_true(t)` implemented via TRN/SO-spindle nesting, §3) and let the EAP peripheral term modulate *that* term's gain rather than `r(t)` directly — i.e., an interaction/gating structure (`r(t) → r_RVC(t) · [1 + small peripheral correction]`) rather than a symmetric additive combination of two independent rhythm sources. This is a stronger, structural claim: it says the two channels are not peers, and that during NREM the endogenous channel should be expected to dominate variance in a way it does not need to during wake (when no comparably strong endogenous thalamocortical rhythm is running). It is the more interesting hypothesis but requires more evidence (ideally a working within-subject dose-response result, #3) before it should be written into any formal equation.

Neither direction should be adopted without first ruling out H1 (§7.1) — if the RichSleep null turns out to be a design artifact and a real population-level phase-locking effect is recovered, the "sleep is EAP-deaf" premise motivating this whole section may simply be wrong, and no reformalization is needed at all.

---

## 9. Claim ledger

| # | Claim | Category |
|---|---|---|
| 1 | GG/CC's largest EAP-family test (`resp_anchor_index`×`m`, CC, `r=-0.41`) fails BH-FDR (`q≈0.05`) | Internal validated result (from GG/CC's own robustness reporting) |
| 2 | RVC_SLEEP's tonic-anchor EAP test is a well-powered clean null (18/18 non-significant, RichSleep dual-arm) | Internal validated result |
| 3 | RVC_SLEEP's phase-resolved EAP test (Mål B/C) is null at N=190 events/24 subjects | Internal validated result, explicitly flagged in-manuscript as underpowered |
| 4 | RVC's core spindle-timing claim (`d_n` rise) replicates across ANPHY, BOAS, and (via A1r) RichSleep | Internal validated result |
| 5 | The master theory (`NoeticDiffusionTheory.typ`) already tiers RVC/TRN-VG as Tier-1 and EAP as Tier-2, "a later wave" | Internal validated result (documented pre-existing theory text) |
| 6 | Respiration phase-locks sleep spindle timing at the population level in independent human PSG data (Ghibaudo et al. 2024; Schreiner et al. 2023) | Established external result |
| 7 | Coupling strength between respiration/SO-spindle events and memory reactivation fidelity (Schreiner et al. 2023) | Established external result |
| 8 | HEP amplitude generally attenuates with sleep depth; QRS phase specifically modulates spindle phase (Lechinger et al. 2015) | Established external result |
| 9 | Wake→sleep respiration-brain coupling shows a phase shift and *increased* consistency, not simple loss (2025 Prog. Neurobiol.) | Established external result |
| 10 | TRN generates spindles via a rebound-burst GABAergic "ping-pong" mechanism (classic + recent biophysical modeling) | Established external result |
| 11 | PV-TRN optogenetic silencing causally contracts MGB population noise-covariance dimensionality independent of mean-gain change (TRN-VG, this lab's own reanalysis) | Internal validated result (different repo/dataset/species) |
| 12 | TRN-VG's PV finding supports the *general architecture* ("a TRN-gated variance channel dissociable from gain exists") underlying both RVC and EAP | Plausible interpretation |
| 13 | TRN-VG's PV finding says anything directly about spindles, cardiorespiratory coupling, or EAP specifically | Explicitly rejected in this note — out of scope by species/pathway/manipulation-type; would be a mis-citation if claimed |
| 14 | RichSleep's Mål B null is a power/design artifact rather than a true absence of coupling (H1) | Plausible interpretation, directly testable (§7.1), not yet tested |
| 15 | EAP's coupling strength (`γ_entrain`) is state-dependent, and/or NREM's endogenous RVC channel dominates over the peripheral EAP channel (H2) | Plausible interpretation, motivated by external literature, not yet tested |
| 16 | A state-dependent or channel-dominance reformalization of `@eq:rvc` (§8, Directions A/B) | Speculative extension — explicitly not proposed for adoption pending #14/#15 |
