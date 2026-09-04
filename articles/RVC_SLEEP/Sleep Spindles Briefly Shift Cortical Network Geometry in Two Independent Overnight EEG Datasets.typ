// RVC_SLEEP manuscript — two-dataset A2r timing result in ANPHY/BOAS,
// an inconclusive same-estimand RichSleep timing test, and a scoped
// tonic EAP-moderation null. Frozen Pass A/B/C plus RichSleep verification;
// see articles/RVC_SLEEP/results/ for per-pass result tables.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Sleep Spindles Briefly Shift Cortical Network Geometry in Two Independent Overnight EEG Datasets",
  short-title: "Spindle-locked cortical geometry",
  subtitle: "A timing-locked change in how far the EEG state sits from an integration–segregation balance; a third dataset did not confirm the same test, and pre-spindle heart and breathing state did not detectably moderate the effect",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "sleep spindles",
    "cortical geometry",
    "integration-segregation balance",
    "overnight EEG",
    "cardiorespiratory coupling",
    "replication",
  ),
  article-type: "Research Article",
  abstract: [
    Sleep spindles are short thalamocortical bursts during N2 sleep. We asked whether they coincide with a brief change in the geometric structure of cortical EEG. Each 30 s window was summarized with a nine-coordinate Meta-Noetic Phase Space (MNPS) chart: three mobility coordinates, three coordinates for how far the state sits from an integration–segregation balance, and three entropy/complexity coordinates. The primary test compared each spindle with its own pre-event baseline, giving every subject equal weight, in three overnight recordings (ANPHY, $N=27$; BOAS/ds005555, analysis $N=110$–$112$; RichSleep, $N=24$).

    In ANPHY and BOAS the balance-deviation coordinate $d_n$ rose at the spindle (subject-mean $+0.106$ and $+0.165$; permutation FDR $q=0.009$ and $0.011$). In ANPHY the companion $t$-based 95% CI included zero. An entropy-shape coordinate $e_s$ supported the same direction in BOAS ($q=0.011$) but not in ANPHY ($q=0.062$). The same timing test in RichSleep was underpowered and inconclusive ($d_n$ $+0.047$, $q=0.72$; 160 paired events). A broader comparison with matched non-spindle N2 windows was significant on most coordinates in ANPHY/BOAS, but a decomposition showed that several of those differences, including the cross-dataset sign conflict on $d_n$, come from how each cohort's pre-spindle baseline relates to generic N2 rather than from spindle timing itself. That broader contrast is therefore not treated as a substitute for the timing result.

    We also asked whether heart-rate and breathing state just before a spindle changes the size of this EEG-only effect. Under tonic (multi-minute) composite anchors, including a dual-arm cardiorespiratory index covering all 24 RichSleep subjects, we did not detect moderation. Two more direct RichSleep tests — whether spindle onset locks to a preferred cardiac or respiratory phase, and whether heartbeat-evoked-potential amplitude predicts the geometric change — were also null, at lower power.

    A spindle-timed shift in cortical network-balance geometry is therefore a two-dataset result. A third dataset does not yet confirm or refute the same test. No tested cardiorespiratory operationalization detected moderation of the EEG-only effect.
  ],
  author-summary: [
    Sleep spindles are brief bursts of brain activity during light sleep. We asked whether they coincide with a short change in how cortical EEG is organized, using a compact geometric summary of each 30-second window. In two independent overnight recordings the EEG state moved farther from an integration–segregation balance at the spindle, relative to the same spindle's own moment just before. A third recording was too sparsely powered for that same timing test to decide. Heart-rate and breathing state just before a spindle did not detectably change the size of the EEG effect under the tests reported here.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted at submission.],
  data-availability: [ANPHY-Sleep is openly available via OSF (@anphy_sleep_osf, described in @wei2024_anphy_sleep). BOAS (ds005555) is openly available via OpenNeuro (@ds005555_1_1_1). RichSleep is described in @richsleep2026; a public DOI was not available at freeze, and access details will be added at submission (corresponding author on request until then). NMD (NeuralManifoldDynamics) pipeline outputs and all analysis scripts are frozen and versioned in the analysis repository under `articles/RVC_SLEEP/src/`, with per-pass result tables under `articles/RVC_SLEEP/results/`.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")

= Introduction <sec:intro>

Sleep spindles - 0.5-2 s bursts of 11-16 Hz thalamocortical oscillation during N2 sleep - are one of the best-characterized rhythmic events in human electrophysiology and are widely linked to memory consolidation and thalamocortical gating @fernandez2020spindles @staresina2015nesting. Within Noetic Diffusion Theory (NDT), spindles have been proposed as candidate *Rhythmic Variance Control* (RVC) events: rhythm-defined windows in which a transient increase in gating precision should show up as a measurable, reproducible reconfiguration of the brain's local state-space geometry, distinct from and prior to any downstream consolidation outcome @langell2025ndt. That RVC / gating-precision mapping is a *speculative extension* of the measurement reported here: this study tests whether a detector-defined spindle is followed by a subject-level change in one MNPS coordinate, not whether spindles implement variance control, TRN gating, or memory consolidation.

An internal single-dataset analysis of BOAS (ds005555) previously reported that spindle-rich N2 windows differed from matched non-spindle N2 controls on several stratified geometry endpoints, most consistently `d`, `d_s`, `d_n`, `e_m`, and `d_l`. That result raised three open questions that motivate the present study: (1) does the effect replicate in an independent dataset with different hardware, staging protocol, and spindle-density distribution; (2) is the effect a genuine peri-event *timing* signature, or could it instead be driven by pre-existing differences between the spindle-adjacent and matched-control sleep baselines; and (3) does pre-event bodily (cardiac/respiratory) state - the Embodied Anchor Principle (EAP) side of NDT - moderate the size of the effect, which would tie a purely EEG-defined event to interoceptive/autonomic state.

This study answers all three questions using two rounds of analysis. First, ANPHY (HD-EEG) and BOAS (PSG) were run through an identical subject-weighted contrast protocol (Methods), frozen after a 2026-07-03 protocol amendment that replaced an event-weighted estimator after a BOAS heterogeneity audit (`src/02c_pass_a1r_subject_weighted_specificity.py`). The protocol separates the *timing* question (event vs. pre-spindle baseline, within the same spindle) from the *specificity* question (event vs. matched non-spindle control), because the two ask different things and, as shown below, can even disagree in sign for the same endpoint if the pre-spindle baseline itself differs by dataset. Second, a third, independent PSG dataset (RichSleep) with simultaneous, near-complete cardiac *and* respiratory recording was added specifically to (a) attempt an out-of-sample replication of the *same* timing estimand and (b) run the cleanest EAP-moderation test attempted in this line of work: unlike the cardiac-only (ANPHY) and respiratory-only, majority-missing (BOAS) anchors used previously, RichSleep's anchor state combines both channels with near-100% subject coverage, removing the missingness objection that could previously explain a null moderation result. RichSleep is therefore an instrumentation-and-replication dataset, not a third timing confirmation unless the A2r test itself survives.

#netn-box(title: [Core question])[
  Does a spindle-locked within-spindle timing change in MNPS geometry, previously reported in a single PSG dataset, replicate under a subject-weighted protocol that separates timing from specificity, and is that EEG-only effect moderated by pre-event embodied (cardiorespiratory) anchor state once that state can be measured without single-channel missingness?
]

= Theory <sec:theory>

== Theoretical framework and primary metric

NDT models a latent noetic state $X_t$ evolving under a geometry-shaped stochastic drift, $d X_t = -G_t (X_t) nabla Phi(X_t, t) d t + sigma(t) d W_t$, and is measured through a versioned chart that projects raw electrophysiology into a low-dimensional Meta-Noetic Phase Space (MNPS). The canonical 3D chart $x_t = [m_t, d_t, e_t]^T$ separates *metastability/mobility* ($m$), *deviation from optimal integration-segregation balance* ($d$), and *entropy/entropic energy* ($e$). Each axis is additionally decomposed into a 9D stratified chart <eq:core9d>,

$ x_t^((9)) = [m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m]^T, quad x_t = P_"fixed" x_t^((9)) $ <eq:core9d>

where $P_"fixed"$ is a release-fixed, auditable projection (not a claim of unique ontology). The *tested* primary endpoint family is the frozen 9-name set used in code (`GEOMETRY_COLS`): $m, d, e, d_n, d_l, d_s, e_e, e_s, e_m$. The three composite axes $m, d, e$ are algebraic recompositions of stratified sub-coordinates and are retained for interpretability; they are still treated as separate FDR tests, which is a conservative-or-not design choice named here rather than hidden. The remaining stratified chart coordinates $m_a, m_e, m_o$ are exported by the 9D chart and were *not* tested. Interpretive labels for the six tested stratified coordinates are: $d_n$ (network-integration deviation), $d_l$ (local clustering-based segregation load), $d_s$ (representational-geometry deviation), $e_e$ (sample/permutation-entropy family), $e_s$ (entropy-shape / complexity family), and $e_m$ (Hjorth-mobility/beta-alpha composite on the primary surface). Operational feature mappings for this article's ingest contract are in Methods, `S1.2`; those mappings are the computation, the labels above are not.

== Embodied Anchoring Principle (EAP)

NDT's Embodied Anchoring Principle proposes that bodily/interoceptive rhythms (cardiac, respiratory, ocular) can condition the same latent landscape that governs cortical state-space dynamics, so that pre-event bodily state could in principle *moderate* how strongly a cortical event (here, a spindle) reconfigures MNPS geometry. Each NMD run co-exports an `anchor_state` layer alongside the EEG-only MNPS coordinates. Two flavors of anchor coverage are contrasted here: single-channel anchors (ANPHY: cardiac HRV only; BOAS: respiratory regularity only, majority-missing) and RichSleep's `cardioresp_anchor_index`, a composite built from *simultaneous*, near-fully-covered ECG and respiratory channels - closer to a genuine dual-arm embodied anchor than either single-channel predecessor. EAP is tested here strictly as a *moderator* of an EEG-only geometric effect, never as a component of the primary geometry itself (Methods, dual-surface contract).

= Methods <sec:methods>

== Dataset

Three independent overnight PSG datasets were used, none with any experimental manipulation (purely observational):

- *ANPHY* (@wei2024_anphy_sleep, @anphy_sleep_osf) - 27 healthy adults, high-density scalp EEG (Biosemi, 93 channels), whole-night PSG. Ingest $N=27$; A1r/A2r analysis $N=27$.
- *BOAS / ds005555* (@ds005555_1_1_1) - 128 subjects, PSG (Bitbrain Open Access Sleep dataset, OpenNeuro). Ingest $N=128$; A1r analysis $N=112$; A2r analysis $N=110$ after dropna on the subject-weighted estimator. Pass C on the primary respiratory anchor is further restricted to $N=35$ subjects with a usable pre-event `resp_regular_index`.
- *RichSleep* (@richsleep2026) - 24 subjects, whole-night PSG with six EEG channels (F3-A2, F4-A1, C3-A2, C4-A1, O1-A2, O2-A1), two EOG channels (EOG-L, EOG-R), chin EMG, ECG, respiratory/snoring/leg-movement/blood-oxygen/carbon-dioxide channels, chest/abdominal movement, and breath-interval duration; 200 Hz sampling; impedance kept below 10 $Omega$ during acquisition; hypnogram stages W/N1/N2/N3/R. Formal access details will be added at submission; the description used here is the ingest note supplied with the analysis export. RichSleep was added as an out-of-sample verification dataset with a richer, near-complete simultaneous cardiac+respiratory anchor (Results, R6). RichSleep's event-locked exports underwent standard QA prior to analysis; two data-processing issues (a subject-scoping bug in event-catalog resolution and a sign error in one secondary respiratory sensitivity index) were identified and corrected upstream before the run used here (`S1.7`).

Sleep-spindle events were detected with YASA (@vallat2021yasa, C3-A2 channel, 200 Hz, sigma 12-15 Hz, N2-only hypnogram epochs) and exported as `sleep_spindle` events with per-event onset, duration, and peak frequency. "N2-only" refers to the detector's staging input. Event-locked MNPS windows are 30 s and carry the stage label of the *window centre*, not of the spindle onset; a 0.5–2 s spindle near a stage boundary can therefore sit in a window whose centre is not N2 (R6b, `S1.0`).

== NMD pipeline

All three datasets were processed through the same NeuralManifoldDynamics (NMD) `summarize` pipeline, using a `primary_eeg_only` MNPS coordinate contract (`rvc_v1_eeg_only_e_m`: $e_m = 0.6 dot "eeg_hjorth_mobility" + 0.4 dot "eeg_beta_alpha"$, identical weights in all three datasets) so that the composite geometry itself never contains body-signal information. ANPHY and BOAS were additionally run through a second, *anchor-augmented* configuration in which $e_m$'s EEG term is partially or fully replaced by the dataset's primary body anchor (ANPHY: 80% HRV RMSSD + 20% Hjorth mobility; BOAS: 70% respiratory regularity + 30% beta/alpha) - used only for the Pass B surface-sensitivity check (R5), never for the primary claim. RichSleep has no anchor-augmented counterpart; it is used only on its `primary_eeg_only` surface. Each subject's per-epoch export is aligned into $30$ s windows and event-locked around each detected spindle into five bins (`pre_far`, `pre_near`, `event`, `post_near`, `post_far`) plus a `matched_control` condition. Matching draws non-spindle N2 windows from the same subject with a $>= 30$ s exclusion margin from any spindle/K-complex/arousal. Those matched windows are then expanded onto the same 30 s MNPS grid, so the *row* count of controls is much larger than 3× unique spindles (Table @tab-qc); analysis median-collapses the control pool per `matched_event_id` before computing deltas, so the estimand is one control median per spindle, not one row per control window (`S1.1`).

== Primary endpoints

The frozen primary endpoint family is the nine names $m, d, e, d_n, d_l, d_s, e_e, e_s, e_m$. The three composites are algebraic recompositions of stratified sub-coordinates and are retained for interpretability; $m_a, m_e, m_o$ are chart coordinates that were not tested. Reachability-cone and MNJ endpoints were specified as secondary layers to be added only if stable, but were not run under the current freeze and are not reported here. Operational feature mappings are in `S1.2`.

== Statistical design

The biological unit of analysis is the *subject*, not the event, because per-subject spindle counts are highly uneven (ANPHY median $approx 40$; BOAS median 5, range 1-18; RichSleep range 14-362). For every (endpoint, dataset) cell: (1) an event-level delta is computed (either `event_bin - matched_control_median`, aggregated per event, or `event_bin - mean(pre_far bins, same event)`); (2) event-level deltas are collapsed to one *subject-mean delta*; (3) the primary $p$-value is a subject-level *sign-flip permutation test* ($n=2000$ permutations) on the grand mean of subject-mean deltas - chosen because it directly tests the within-subject direction question without assuming a parametric distribution; (4) a one-sample $t$-test and Wilcoxon signed-rank on the same subject means are reported as sensitivity checks, together with a $t$-based 95% CI on the subject-mean delta; (5) Benjamini-Hochberg FDR @benjamini1995fdr is applied fresh within each frozen test family (9 endpoints $times$ number of datasets in that family) at $alpha = 0.05$.

== Robustness protocol

1. *Subject-weighted vs. event-weighted estimand* - the primary estimand (A1r/A2r) subject-weights every event-count-imbalanced subject equally; an event-weighted cluster-robust OLS analysis (A1-original) is retained only as a pre-amendment sensitivity table.
2. *A1/A2 decomposition* - `event - control = (event - pre_far) + (pre_far - control)`, used to test whether an event-vs-control effect is a genuine timing effect, a pre-existing baseline-separation effect, or both (R4).
3. *Surface sensitivity (Pass B)* - comparing primary vs. anchor-augmented geometry on the identical subject-weighted estimand, to confirm the anchor-augmented surface behaves as a construction should (only the directly-modified coordinate moves) rather than as an implicit EAP test.
4. *EAP moderation (Pass C)* - `delta ~ anchor_pre_far + <mean-centered nuisance covariates>`, weighted inverse to each subject's event count, cluster-robust SE by subject, with a companion per-subject-slope sign-flip permutation test immune to event-count imbalance by construction.
5. *Cross-dataset replication (RichSleep)* - the identical A1r/A2r/Pass-C machinery re-run on an independent third dataset, with explicit sign-agreement reporting against the frozen ANPHY/BOAS tables (R6).

== Secondary analysis

The RichSleep EAP-moderation test additionally reports six sensitivity anchors beyond the primary dual-arm composite (`anchor_index`, `anchor_index_v02`, `sympathetic_index`, `vagal_index`, `resp_anchor_index`, `ocular_stability_index`; 7 anchors $times$ 9 endpoints $times$ 2 delta modes $= 126$ fitted rows) to check whether any single composite index behaves differently from the mechanistically-motivated primary anchor; these are exploratory and are flagged where their coefficients are numerically negligible despite nominal FDR significance (R6).

= Results <sec:results>

== R1: Data quality and coverage <sec:r1>

#figure(
  kind: table,
  clean-table(
    columns: (1.15fr, 0.7fr, 0.85fr, 0.85fr, 0.85fr, 1.1fr),
    align: (left, center, center, center, center, center),
    inset: 4.5pt,
    table.header([*Dataset*], [*Ingest $N$*], [*A1r / A2r $N$*], [*Event-bin rows*], [*A1r / A2r events*], [*Control rows (grid)*]),
    [ANPHY], [27], [27 / 27], [1,076], [1,075 / 1,037 paired], [34,263],
    [BOAS (ds005555)], [128], [112 / 110], [634], [625 / 575 paired], [192,312],
    [RichSleep], [24], [24 / 24], [see note], [mixed-bin 3,615; A2r 160 paired; event-bin N2 190], [32,931],
  ),
  caption: [Accounting table. Ingest $N$ is the recording sample; analysis $N$ is the tested subject count after dropna. Event-bin rows are `bin_label="event"` coverage (`event_locked_coverage.csv`). A1r/A2r "events" are the rows retained by each estimator (A2r requires an event/`pre_far` pair). Control *rows* are 30 s MNPS-grid expansions of matched non-spindle N2 windows, not 3 unique controls per spindle; analysis median-collapses them per `matched_event_id` (`S1.1`). RichSleep raw all-bin spindle_event rows: 46,058; N2/coords-filtered all-bin: 3,900. RichSleep A1r (3,615) was *not* restricted to `bin_label="event"` (`S1.5`, R6). Primary anchors: ANPHY `ecg_hrv_rmssd_ms` 27/27; BOAS `resp_regular_index` ~34% (Pass C $N=35$); RichSleep `cardioresp_anchor_index` 24/24.]
) <tab-qc>

#figure(
  image("figures/fig5_qc_coverage.svg", width: 88%),
  caption: [ANPHY/BOAS event-locked row coverage by condition and peri-event bin (source: `event_locked_coverage.csv`). Control-row inflation relative to unique spindles is the MNPS-grid expansion described in Table @tab-qc, not a 3-row matching design.]
) <fig-qc>

Config-hash and subject-count sanity checks passed for all three datasets (ANPHY/BOAS: `run_manifest_check.csv`; RichSleep: `sanity_check.csv`, config digest `0c8d751c52029306`, $N=24$). RichSleep's `cardioresp_anchor_index`, `anchor_index`, `anchor_index_v02`, `sympathetic_index`, `vagal_index`, `resp_anchor_index`, and `ocular_stability_index` all show 0% missingness across all 24 subjects after the pass-A base filter - a substantially cleaner anchor-coverage profile than either single-channel predecessor.

== R2: Event-vs-matched-control specificity (A1r) <sec:r2>

Spindle-event windows differ from matched non-spindle N2 controls on 8 of 9 endpoints in the same direction in both ANPHY and BOAS, most surviving BH-FDR (Table @tab-a1r). The exception is `d_n`, whose sign differs between datasets - resolved by decomposition in R4.

#figure(
  kind: table,
  clean-table(
    columns: (0.7fr, 1.1fr, 0.7fr, 1.1fr, 0.7fr, 0.9fr),
    align: (left, center, center, center, center, center),
    inset: 4.5pt,
    table.header([*Endpoint*], [*ANPHY $Delta$*], [*$q$*], [*BOAS $Delta$*], [*$q$*], [*Agreement*]),
    [`m`], [$+0.430$], [$<0.001$], [$+0.230$], [$<0.001$], [same sign],
    [`d`], [$+0.203$], [$<0.001$], [$+0.404$], [$<0.001$], [same sign],
    [`e`], [$+0.100$], [$<0.001$], [$+0.274$], [$<0.001$], [same sign],
    [`d_n`], [$-0.189$], [$<0.001$], [$+0.589$], [$<0.001$], [*opposite sign*],
    [`d_l`], [$+0.392$], [$<0.001$], [$+0.349$], [$<0.001$], [same sign],
    [`d_s`], [$+0.500$], [$<0.001$], [$+0.427$], [$<0.001$], [same sign],
    [`e_e`], [$+0.049$], [$0.082$ (ns)], [$+0.103$], [$0.0016$], [same sign],
    [`e_s`], [$+0.077$], [$0.0016$], [$+0.485$], [$<0.001$], [same sign],
    [`e_m`], [$+0.488$], [$<0.001$], [$+0.397$], [$<0.001$], [same sign],
  ),
  caption: [Pass A1r: subject-weighted event-vs-matched-control delta (subject-mean of `event_bin - matched_control_median`), sign-flip permutation $p$, BH-FDR $q$ across the frozen 18-test family. Source: `results/rvc_sleep_20260703/02c_pass_a1r_subject_weighted_specificity/`.]
) <tab-a1r>

Read together with R4, this broad specificity result is real but should not be read as a single clean "spindle-specific" mechanism - see the decomposition below.

== R3: Within-spindle timing contrast (A2r) - primary claim <sec:r3>

The within-spindle timing contrast (event bin vs. the same spindle's own `pre_far` baseline) is the primary claim: `d_n` is the only endpoint that is FDR-significant, same-sign, in both ANPHY and BOAS (Table @tab-a2r, Figure @fig-a2r). RichSleep's replication of this *same* estimand is underpowered and inconclusive (R6) and is not rescued by switching to A1r.

#figure(
  kind: table,
  clean-table(
    columns: (0.8fr, 1.1fr, 0.9fr, 1.1fr, 0.9fr),
    align: (left, center, center, center, center),
    inset: 5pt,
    table.header([*Endpoint*], [*ANPHY $Delta$*], [*$q$*], [*BOAS $Delta$*], [*$q$*]),
    [`d_n`], [$+0.106$], [$0.009$], [$+0.165$], [$0.011$],
    [`e_s`], [$+0.062$], [$0.062$ (ns)], [$+0.114$], [$0.011$],
    [`d`], [$+0.040$], [$0.037$], [$+0.072$], [$0.014$],
    [`e_e`], [$-0.064$], [$0.009$], [$-0.019$], [$0.57$ (ns)],
    [all others], [ns], [-], [ns], [-],
  ),
  caption: [Pass A2r: subject-balanced event-vs-pre_far within-spindle timing delta. ANPHY $d_n$ permutation $q=0.009$; the companion $t$-based 95% CI on the subject-mean delta includes zero (`ci95` $[-0.003, +0.214]$; sensitivity $t$ $p=0.057$, Wilcoxon $p=0.008$). Primary inference is the sign-flip permutation. Source: `results/rvc_sleep_20260703/03b_pass_a2r_subject_balanced_profile/`.]
) <tab-a2r>

#figure(
  image("figures/fig2r_pass_a2r_profile.svg", width: 92%),
  caption: [Subject-balanced A2r peri-spindle profile (event vs. `pre_far`) for ANPHY and BOAS. This is the primary estimand; it does not include a post-event return test.]
) <fig-a2r>

#netn-box(title: [Primary finding])[
  Sleep spindles are followed by a rise in $d_n$ relative to their own pre-spindle baseline in ANPHY and BOAS under a subject-weighted sign-flip test. RichSleep's same-estimand A2r test is inconclusive ($q=0.72$, 160 paired events). This within-spindle timing signature, not the broader event-vs-control contrast, is the study's primary claim; A1r is not used as a substitute timing confirmation.
]

== R4: Decomposition - resolving the `d_n` sign conflict <sec:r4>

Decomposing the event-vs-control delta as $C ("event"-"control") = A ("event"-"pre_far") + B ("pre_far"-"control")$ shows that the two datasets *agree* on the timing component ($A$, both positive) but *disagree* on how each dataset's own pre-spindle baseline compares to its matched generic-N2 controls ($B$: ANPHY $-0.293$, BOAS $+0.427$) - which fully explains why the A1r-original `d_n` sign flips between datasets while the A2r timing sign does not (Table @tab-decomp). `d_s` and, to a lesser extent, `m` show the opposite pattern: their event-vs-control effect is driven almost entirely by $B$ (baseline separation), with a near-zero or slightly negative timing component $A$.

#figure(
  kind: table,
  clean-table(
    columns: (0.7fr, 1.6fr, 1.6fr, 2.3fr),
    align: (left, center, center, left),
    inset: 4.5pt,
    table.header([*Endpoint*], [*ANPHY $A$ / $B$ / $C$*], [*BOAS $A$ / $B$ / $C$*], [*Reading*]),
    [`d_n`], [$+0.106 \/ -0.293 \/ -0.187$], [$+0.166 \/ +0.427 \/ +0.593$], [$A$ agrees (timing rise, both $+$); $B$ disagrees by dataset - explains the A1r sign conflict],
    [`d_s`], [$+0.018 \/ +0.484 \/ +0.501$], [$+0.066 \/ +0.354 \/ +0.420$], [mostly $B$ (baseline separation), weak/no timing component],
    [`e_s`], [$+0.062 \/ +0.017 \/ +0.079$], [$+0.116 \/ +0.368 \/ +0.484$], [$A$ positive both datasets; $B$ small in ANPHY, large in BOAS],
    [`m`], [$-0.013 \/ +0.442 \/ +0.429$], [$-0.041 \/ +0.295 \/ +0.254$], [timing component near-zero/negative both datasets; result is baseline-driven],
  ),
  caption: [Pass A1 decomposition: $A$ = timing component (event$-$pre_far), $B$ = pre-spindle-baseline vs. matched-control separation, $C = A + B$ = the A1r event-vs-control delta. Source: `results/rvc_sleep_20260703/02d_pass_a1_decomposition/`.]
) <tab-decomp>

== R5: Embodied-anchor moderation is not supported (Pass B / Pass C) <sec:r5>

*Pass B (surface-sensitivity, construction-validity check, not an EAP test).* Comparing primary vs. anchor-augmented geometry on the identical subject-weighted estimand: 7 of 9 endpoints (`m, d, d_n, d_l, d_s, e_e, e_s`) are byte-identical between surfaces (surface delta $= 0$, $r=1.0$) in both datasets and both delta modes - expected, since these coordinates never touch body-signal input. Only `e_m` (directly modified by anchor injection) and, more weakly, `e` (which recomposes from `e_m`) show any divergence ($e_m$ correlations $r = 0.22$-$0.74$ across the four `e_m` cells; $e$: $r >= 0.97$ everywhere). FDR-significance status changes in *0 of 36* testable rows. Per the dual-surface guardrail, this shows the anchor-augmented surface is sensitive to injected body signals exactly where expected and provides no information about whether pre-event anchor state moderates EEG-only spindle geometry.

*Pass C (the moderation test itself).* Modeling `delta ~ anchor_pre_far + nuisance covariates`, weighted inverse to subject event count, cluster-robust SE, across 2 delta modes $times$ 3 anchor models $times$ 9 endpoints (54 tests): *53/54 do not survive FDR.* The single nominal exception (ANPHY `d_l`, HRV anchor, event-control delta, pooled $q=0.0015$) does not replicate in its own subject-level-slope sensitivity check ($p=0.140$, ns) and is treated as a pooled-model weighting artifact rather than a genuine effect.

#netn-box(title: [Dissociation finding])[
  Anchor-augmented geometry moves only where it structurally must ($e_m$, weakly $e$) and never flips an FDR conclusion (Pass B); the direct moderation test (Pass C) is null on 53/54 comparisons in two independent single-channel anchors. No tonic-anchor moderation of the EEG-only geometric effect was detected in this dataset pair.
]

== R6: RichSleep - same-estimand timing test and a dual-arm EAP test <sec:r6>

RichSleep was added specifically to (a) test whether R3's primary *timing* estimand (A2r) survives in a fully independent PSG dataset, and (b) run the EAP-moderation test with an anchor that does not carry ANPHY's cardiac-only or BOAS's majority-missing respiratory limitation. RichSleep's `cardioresp_anchor_index` is built from simultaneous ECG and respiratory channels with 0% missingness across all 24 subjects (Table @tab-qc), so a tonic-anchor null here cannot be attributed to single-channel missingness. An earlier RichSleep ingest had a subject-scoping bug in event-locked source resolution (detected via a signature check across per-subject spindle catalogs) that was traced and fixed prior to the run used here (`S1.7`); all geometry-based A1r/A2r numbers below are from the corrected run.

*A1r (event vs. matched-control; mixed-bin, not used as timing corroboration).* The RichSleep A1r script did not restrict to `bin_label=="event"`; the 3,615 rows are N2-filtered peri-spindle windows across bins, not unique event-bin spindles (Table @tab-qc). The contrast was also never decomposed into timing vs. baseline components, and ANPHY A1r `d_n` is itself negative, so a mean-of-ANPHY-and-BOAS "agreement" cell would hide the conflict R4 exists to explain. Table @tab-richsleep-a1r is therefore a descriptive mixed-bin specificity table, not a substitute for A2r. `e_e` disagrees in sign with ANPHY/BOAS A1r (FDR-significant, opposite direction) - a genuine open discrepancy.

#figure(
  kind: table,
  clean-table(
    columns: (0.9fr, 1.2fr, 1fr, 1.6fr),
    align: (left, center, center, left),
    inset: 5pt,
    table.header([*Endpoint*], [*RichSleep $Delta$*], [*$q$*], [*Vs ANPHY / BOAS A1r sign*]),
    [`m`], [$+0.230$], [$0.0006$], [agrees with both],
    [`d`], [$+0.349$], [$0.0006$], [agrees with both],
    [`e`], [$+0.019$], [$0.139$], [agrees (ns here)],
    [`d_n`], [$+0.292$], [$0.0006$], [agrees with BOAS; *opposite* ANPHY],
    [`d_l`], [$+0.433$], [$0.0006$], [agrees with both],
    [`d_s`], [$+0.148$], [$0.0006$], [agrees with both],
    [`e_e`], [$-0.222$], [$0.0006$], [*opposite* both],
    [`e_s`], [$+0.223$], [$0.0006$], [agrees with both],
    [`e_m`], [$+0.556$], [$0.0006$], [agrees with both],
  ),
  caption: [RichSleep mixed-bin A1r (not event-bin restricted; not decomposed). Not used as corroboration of the A2r timing claim. Source: `results/rvc_sleep_20260709/09_richsleep_verification/richsleep_a1r_specificity.csv`.]
) <tab-richsleep-a1r>

*A2r replication (event vs. pre_far, $N=24$ subjects, 160 paired events).* This is the only RichSleep contrast that matches the primary estimand. The headline timing endpoints do not survive FDR (`d_n`: $+0.047$, $q=0.72$; `e_s`: $q=0.71$). CSV `sign_agree_with_frozen` is 7/9 True and 2 False (`m`, `e`). Two non-headline endpoints reach FDR significance (`e_e`: $q=0.0045$; `e_m`: $q=0.036$). Given 160 paired events vs. 1,037 (ANPHY) and 575 (BOAS), this is read as *underpowered and inconclusive for the primary timing claim*, not as a disconfirmation of R3.

*EAP moderation, primary dual-arm anchor (`cardioresp_anchor_index_pre_far`, $N=24$ subjects, mixed-bin 2,260–2,435 rows, both delta modes).* A clean null across all 9 endpoints in both delta modes (18 tests; $p$ range $approx 0.04$-$0.94$, no FDR survivors, min $q approx 0.32$) - the same qualitative result as Pass C's ANPHY/BOAS null, on the one dataset where the missingness objection does not apply. These row counts are mixed-bin, as in RichSleep A1r, and are therefore *not* comparable as unique-spindle $N$ with the 190 event-bin rows used in R6b. Several single-channel sensitivity anchors (`anchor_index`, `anchor_index_v02`, `sympathetic_index`, `ocular_stability_index`) show nominally FDR-significant but numerically negligible coefficients ($approx 10^(-8)$-$10^(-9)$ per raw unit of a large-scale composite index); this is read as a scale/multicollinearity artifact of those raw composites rather than genuine moderation, the same caution already applied to BOAS's `anchor_index_v02` sensitivity model.

#netn-box(title: [`resp_anchor_index`: an upstream construction bug, and its resolution])[
  One sensitivity anchor, `resp_anchor_index`, initially showed FDR-surviving coefficients of ordinary, non-negligible magnitude on `m`, `d`, `d_l`, and `e_m` in the `event_control` delta mode. A dedicated follow-up (S2.5, S2.5a, S3.4f) ruled out scale, multicollinearity, and single-subject-outlier artifacts, but tracing the anchor's exact construction surfaced an upstream sign bug in its rate/slowing component that had been rewarding fast breathers instead of the intended slow breathers; this was corrected prior to the export used throughout this manuscript (`S1.7`). Re-running the moderation test against the corrected export fully resolves the original `event_control`-mode finding to a clean null ($p approx 0.23$-$0.93$), matching the primary anchor's null pattern. A different, weaker pattern emerges in the `event_prefar` delta mode on the corrected data (`d`, `e`, `d_n`, `e_s`, positive-signed; `e_e` at the FDR boundary). This pattern survives the same three modeling-artifact checks plus two stricter checks (a joint FDR correction pooling both delta modes' 108 sensitivity-anchor tests, and exclusion of the most extreme-slope or most extreme-anchor-value subject) with coefficients essentially unchanged, except `d`, which loses significance under extreme-slope exclusion and is the weakest of the four. Given that this anchor's signal has already flipped completely once after a single upstream fix, this pattern is reported at deliberately low confidence, despite surviving every artifact check attempted, as a hypothesis for a dedicated, independently-replicated test - not as a claim to be built on (S2.5a, S3.4f).
]

This is reported as a resolved false-positive artifact (`event_control`) plus one new, weaker, exploratory hypothesis (`event_prefar`) - not as evidence against R6's primary `cardioresp_anchor_index` null either way, and not yet as an established EAP-moderation effect under any anchor (S2.5, S2.5a, S3.4f).

#netn-box(title: [Synthesis])[
  ANPHY and BOAS agree on a within-spindle $d_n$ timing rise (A2r). RichSleep does not yet confirm that estimand (A2r inconclusive; A1r not used as a substitute). No tested tonic composite anchor, including RichSleep's dual-arm cardiorespiratory index, detected moderation of the EEG-only geometric effect. An unreplicated `resp_anchor_index` `event_prefar` pattern is held as a low-confidence hypothesis.
]

== R6b: RichSleep phase-resolved EAP mechanism test <sec:r6b>

R6's `cardioresp_anchor_index_pre_far` moderation test uses a tonic (multi-minute pre-event average) anchor as a proxy for embodied-anchor state - a coarse test of the mechanism EAP proposes (phase-resolved cardiorespiratory coupling at spindle timescale; the NDT flagship equation is not reproduced here). Using the phase-resolved RichSleep export (`event_phase_v2`, independently verified 24/24-subject onset-catalog match against the corrected event-locked run before use), we ran two more direct tests on the N2-window, geometry-valid event-bin population (190 events, 24 subjects).

That 190/2,253 split is a *stage-window mismatch*, not evidence that YASA detected non-N2 spindles. The detector was restricted to N2 hypnogram epochs. Event-locked MNPS windows are 30 s and carry the stage of the window centre. A 0.5–2 s spindle near a stage boundary can sit in a window whose centre is N1, N3, Wake, or REM. ANPHY/BOAS retained rows are already ~100% N2 (`frac_n2` $0.9995$ / $0.9999$). RichSleep's numeric `stage` codebook labels the MNPS window; Pass A then keeps only `stage==2`. A2r and R6b use that conservative window-N2 subset. A sensitivity that uses onset-stage rather than window-stage is an open follow-up (`S3.4e`).

*Aim B (self-prior/boundary-condition test): does spindle onset preferentially occur at a particular cardiac or respiratory phase?* A per-subject Rayleigh test found no within-subject phase-locking for either channel (0/24 subjects FDR-significant for cardiac onset phase, 0/24 for respiratory onset phase; some subjects have $n=1$–$2$ events and are not Rayleigh-testable). A second-order Rayleigh test on the 24 subject-level mean directions found no population-level common preferred phase either (cardiac: $R=0.160$, $p=0.547$; respiratory: $R=0.109$, $p=0.755$).

*Aim C (HEP-amplitude moderation): does pre-event heartbeat-evoked-potential amplitude moderate the spindle-locked geometry response?* Using `hep_amplitude_pre_far` as the sole predictor in the same WLS-cluster + subject-level-slope-permutation machinery as R6/Pass C, across both delta modes and all 9 endpoints (18 tests): a clean null ($p$ range $approx 0.10$-$0.96$, 0/18 FDR survivors, matching the companion slope-permutation test). Large coefficient magnitudes ($approx 10^4$–$10^5$) reflect unstandardized microvolt-scale HEP units, not an anomaly (`S2.6`).

#netn-box(title: [R6b summary])[
  Direct phase-locking and HEP-amplitude moderation are also null on the window-N2 event-bin subset. Given 190 events / 24 subjects, this is *no effect detected at this power*, not a stronger disconfirmation of phase-locked embodied anchoring than the tonic-anchor null (S2.6, S3.4e). The tonic mixed-bin $N$ (2,260–2,435) should not be compared with 190 as if both counted unique spindles.
]

= Discussion <sec:discussion>

== Primary finding

The within-spindle timing rise in $d_n$ is the most consistent *positive* result in this study: it is FDR-significant in the same direction in ANPHY and BOAS, two independent PSG datasets with different hardware, staging protocols, and spindle-density distributions. That is a stronger evidentiary position than the original single-dataset (BOAS) observation, and it is still a *two-dataset* result. RichSleep's same-estimand A2r test is inconclusive. Treating a detector-defined $d_n$ rise as a geometrically detectable RVC / gating-precision event remains a speculative interpretation, not a validated mechanism: no gating-precision observable, TRN recording, or consolidation outcome was measured.

== Confound interpretation

The broader event-vs-matched-control contrast (A1r, R2) is real on most endpoints but is not, by itself, a clean single mechanism: the decomposition (R4) shows that for `d_n` specifically, the apparent cross-dataset disagreement in A1r sign is fully explained by a dataset-specific difference in how each cohort's *pre-spindle* baseline relates to its matched generic-N2 controls, not by any disagreement in the *timing* signature. For `d_s` and `m`, the event-vs-control effect is mostly a baseline-separation effect with little or no timing component. This is why the manuscript leads with the timing contrast (A2r/R3) rather than the broader specificity contrast (A1r/R2, R6) as the primary claim - the latter should be read as "broad, present, and baseline-sensitive," not as direct evidence of a single spindle-specific geometric signature across every endpoint, and not as a third-dataset timing confirmation.

== Secondary findings

Pass B's surface-sensitivity result (R5) is a construction-validity check, not an EAP finding: it confirms the anchor-augmented geometry export behaves exactly as intended (only the directly-modified coordinate, and weakly its recomposition, respond to injected body signal) and never changes an inferential conclusion. Pass C and its RichSleep tonic-anchor replication are read together as a genuine negative result for embodied-anchor moderation of spindle-locked geometry *under the tonic composite operationalizations tested here* - not a failure of the analysis, and not evidence that EAP-style body-brain coupling is absent in general.

== Why did EAP moderation come back null?

The EAP tests are not evidentially equivalent. R5/R6's primary Pass C test operationalizes "embodied anchor state" as a *tonic* quantity - a multi-minute pre-event average of cardiac and/or respiratory regularity (`anchor_pre_far`) - which is a deliberately coarse proxy for phase-resolved cardiorespiratory coupling at spindle timescale. A tonic proxy could fail to detect a genuinely phase-locked mechanism simply because it averages away the phase information the mechanism depends on. This is why R6b was run: it replaces the tonic proxy with onset phase-locking and HEP-amplitude moderation.

That more direct test is also null, at substantially lower power. The tonic test uses mixed-bin row counts (2,260–2,435); the phase-resolved tests use 190 event-bin window-N2 rows. A null at that sample size is compatible with a moderate true effect going undetected. The overall picture is therefore asymmetric: the tonic-proxy null is better powered but a blunt test of the mechanism; the phase-resolved null is a fairer test of the mechanism but underpowered to rule out a moderate effect. The most defensible reading is that no moderation was *detected* under any anchor or mechanism tested at the power achieved here, not that moderation has been *ruled out* at the phase-resolved level.

== Limitations

- BOAS's respiratory-anchor Pass C model runs on a restricted $N$ ($35$/128 subjects with a valid pre-event `resp_regular_index`); the larger-$N$ sensitivity anchor (`anchor_index_v02`, $N approx 90$) is still null, but this does not fully remove the missingness concern for BOAS specifically - RichSleep's dual-arm anchor was added in part to address this.
- RichSleep's A2r within-spindle timing replication remains underpowered relative to ANPHY/BOAS ($N=24$ subjects, 160 paired events vs. 1,037/575) and the two headline endpoints (`d_n`, `e_s`) are not FDR-significant here; this is reported as inconclusive rather than as a second disconfirmation of R3.
- The `e_e` sign discrepancy between RichSleep and ANPHY/BOAS in the mixed-bin A1r contrast (R6) is a genuine open finding that has not yet been investigated at the subject level; RichSleep's more fragmented sleep-stage architecture (documented in its ingest configuration) is one candidate explanation, not yet tested.
- RichSleep's `resp_anchor_index` sensitivity model (R6) initially showed FDR-surviving, non-negligible `event_control`-mode coefficients that survived scale/multicollinearity/outlier checks (S2.5, S2.5a, S3.4f) but traced to an upstream sign bug in the anchor's rate/slowing component, since corrected (`S1.7`). Re-verified against the corrected export: the original `event_control` finding is now a clean null - but a new, weaker, `event_prefar`-mode pattern emerged on `d`, `e`, `d_n`, `e_s` (one of which, `d`, is itself subject-dependent on re-check) that was null before the fix. Given that this anchor's signal has already flipped completely once, this new pattern is reported at low confidence as a hypothesis for a future independently-replicated test - not as an established finding. Neither version overturns the primary `cardioresp_anchor_index` null.
- R6b's phase-resolved tests (Aim B/C) ran on a materially smaller sample (190 events, 24 subjects) than R6's tonic mixed-bin rows, because they require an exact-onset join and the window-N2 filter described above. This null is *no effect detected at this power*.
- RichSleep A1r and tonic EAP were not re-fit on `bin_label=="event"` under the current freeze; mixed-bin $N$ must not be read as unique-spindle $N$.
- Reachability-cone and Meta-Noetic Jacobian endpoints were specified as planned secondary layers but were not run under the current analysis freeze.
- `frequency_hz` and sigma-power residualization of the spindle detector are not available in the current NMD event-locked export schema and are not silently substituted for; this remains an open follow-up for detector-strength robustness.
- Leave-one-subject-out and a formal power analysis for RichSleep A2r were not run (`S3.3`).
- All three datasets are healthy-adult, observational, cross-sectional samples; no clinical population, intervention, or longitudinal design is tested (see `S4_Supplementary_Clinical.typ`).

== Conclusion

In two independent PSG datasets (ANPHY analysis $N=27$; BOAS analysis $N=110$ on the primary timing contrast), spindle events are followed by a rise in the $d_n$ state-space endpoint relative to their own pre-spindle baseline. A third dataset (RichSleep, $N=24$) does not yet confirm or refute that same estimand. The broader event-vs-matched-control specificity result is real but baseline-sensitive and is not used as a third-dataset timing confirmation. Pre-event embodied (cardiac and/or respiratory) anchor state did not moderate this effect under the tonic composite anchors tested here, including a dual-arm, near-fully-covered cardiorespiratory composite; a more direct, phase-resolved test is also null, at substantially lower power, and should be read as no detected effect rather than a general disconfirmation of embodied anchoring.

= Acknowledgements

The author thanks the ANPHY-Sleep, BOAS (ds005555), and RichSleep dataset contributors for open data access, and the YASA project for the spindle-detection tooling used throughout.

#bibliography("references.bib", style: "apa")
