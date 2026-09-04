# 09 — m3-bridge: Allen Visual Behavior + cross-scale dataset audits

Internal cartography for NDT 1.0 / Noetic Diffusion Theory v2. Date: **2026-08-30**. Source repo (read-only): `J:\repos\m3-bridge`. This file is **not** manuscript prose.

Primary sources: article abstracts, README, sciencelead, S2/S3, claim ledgers, and frozen result notes cited below. Numbers are taken from those sources; none were recomputed here.

---

## Architecture filter + tag schema

**Architecture filter (frozen):** State geometry → Local dynamical geometry → Geometry of possible futures → Control of accessibility.

**Recoverability ladder:** (1) association → (2) mechanism discrimination → (3) latent-order preservation → (4) dynamical-operator identification. Success at one level does not license a stronger claim.

**Tag schema:** Layer (`state` / `local_dynamics` / `possible_futures` / `control` / `epistemic` / `measurement_contract`) · Evidence class (`established_external` / `internal_validated` / `plausible` / `speculative` / `rejected`) · Flagship role (`main_text_anchor` / `evidence_matrix` / `supplement` / `exclude` / `terminology_only`) · Claim ceiling (one sentence).

**Object-identity rule for this cluster.** Folder names that say “reachability” do **not** automatically mean NDT stochastic short-horizon predictive-spread ellipsoids \(\Sigma^{(h)}\) under an admissible residual contract. Three different objects appear in this cluster:

| Label in m3-bridge | Object actually measured | NDT layer it can constrain |
|---|---|---|
| AVB `delta_omission_geometry` | Pre→post change in Euclidean chart distance between omission and matched-expected conditions on an AVB-adapted 9D→3D spike-population chart | `state` (event-locked population geometry). Not Jacobian, not \(\Sigma^{(h)}\). |
| ARR D2 `delta_coupling` | Pearson correlation of two regions’ 5-step epoch-to-epoch **chart-speed** sequences; omission-minus-expected | Trajectory-speed **coupling**, not NDT reachability. At most `state` / weak `local_dynamics`. |
| ARR D1 \((A,Q,\Sigma^{(h)})\) | Discrete local-linear transition + innovation covariance, then \(\Sigma^{(h)}=\sum_{k=0}^{h-1} A^k Q (A^k)^\top\) at \(h\in\{1,3\}\) | **Attempted** NDT-adjacent reachability / local operator. Estimator quality **does not clear** an admissible residual contract for a headline claim. |
| AGR G2 `delta_global_coupling` | Mean of the six pairwise D2 speed correlations among CA1/VISp/VISam/LP | Scalar average of speed couplings. Not a joint transfer operator; not \(\Sigma^{(h)}\). |

Blocked or unreadable data is an **acquisition / release-contract** finding (`measurement_contract`). It is **not** a rejected biological hypothesis.

---

## Inventory

| Cluster | Path under `J:\repos\m3-bridge\articles\` | Status as of 2026-08-30 |
|---|---|---|
| **AVB** omission-locked population geometry | `allen_visual_behavior/` | **AVB-000..006 PASS**; AVB-007 manuscript **internal draft**, not submission-ready. Real source is the long-title `.typ`, not a `manuscript.typ` stub. Claim ledger: `results/AVB_007_claim_ledger.md`. |
| **ARR** region “reachability” | `allen_visual_behaviour_region_reachability/` | **ARR-000..006 complete**; manuscript + S1–S6 drafted, internal review. Headline is **CA1–VISam speed coupling** (D2), not D1 operator ID. Read-only w.r.t. AVB. |
| **AGR** global “reachability” | `allen_visual_behaviour_global_reachability/` | **Computation complete, write-up incomplete.** AGR-002 G2: `NOT_SIGNIFICANT` (\(p=0.1194\)). `manuscript.typ` and S1–S6 remain **aa_template placeholders**. README header and later table disagree; trust the AGR-002 result note. |
| **24h mPFC Ca–EEG–EMG** | `24-hour mPFC calcium–EEG–EMG dataset/` | **E001_BLOCKED_UNREADABLE_OR_INCOMPLETE** (git-annex / local unreadability). Audit article complete. No physiology computed. |
| **Dryad Cecchetto** | `DataDryad Simultaneous two-photon imaging multichannel LFP/` | **E001_LIMITED_AVERAGE_ONLY**. Public release is peri-stimulus figure-source averages. E003 descriptive reproduction only (\(n=6\) voltage, \(n=4\) calcium). |

Not in this intake: DANDI 000458 (already cartographed in `03`); IBL 000409 prior-reachability (ARR imports that estimator code; do not double-count IBL results here); qMRI / cytodendritic bridge (none of these datasets has a structural-imaging arm).

---

## Executive take for flagship (≤15 lines)

The strongest Allen result is **AVB**: omission of an expected image produces a reproducible, control-robust increase in VISp population-chart separation (`delta_omission_geometry` median **0.980**, 30/30 sessions positive, \(p=9.999\times10^{-5}\)), surviving C1–C5 and AVB-006 A/B1/B2/C/D. That is an event-locked **state-geometry** constraint on an **AVB-adapted** chart (`m_a` redefined; not canonical MNPS). Recoverability: Level 1, with bounded Level 2 only against **technical** alternatives (matching artifact, alignment, coarse behavior, reward proximity, image dominance, locality). Not prediction-error mechanism, not Jacobian, not \(\Sigma^{(h)}\), not operator ID.

ARR’s folder name is misleading for NDT. The headline object is **undirected chart-speed coupling** between CA1 and VISam (`delta_coupling` median **0.579**, BH-FDR \(p=0.003\), 25/28 sessions). The paper itself labels this a **plausible interpretation**: post-hoc “confirm the biggest hit,” two controls not five, no pupil series. The D1 object that *would* be NDT-adjacent reachability (discrete \(A,Q\) and \(\Sigma^{(h)}\)) is **estimator-quality WARN**: every one of 240 fits sits at residual-df floor \(=1\); residual-fraction gate \(\le 0.5\) is mostly unmet. Do not import ARR as coma-style possible-futures evidence.

AGR G2 (mean of six pairwise speed correlations) is **rejected for that exact design** (\(n=23\), median \(0.1131\), \(p=0.1194\)). Joint transfer-operator G1 was rejected *before* computation. Manuscript unwritten.

The 24-hour G-Node resource is a **promising future cellular→EEG ladder** (Han et al. 2025; 5 mice / 6 sessions) whose **local copy is unreadable** (git-annex). Dryad Cecchetto is a **release-contract mismatch**: original acquisition was simultaneous optical + laminar LFP + surface signal; **public files are 4–6 s peri-airpuff averages**. Neither audit is a biological null. Neither licenses NDT geometry, Jacobian, or reachability.

Default flagship placement for the whole cluster: **`evidence_matrix` or `supplement`**. Do not add a fourth main-text empirical anchor.

---

## Per-article memos with ceilings

### 1. AVB — omission-locked VISp population geometry

**Source of truth.** `allen_visual_behavior/Omission of an Expected Visual Stimulus Produces a Reproducible, Control-Robust Alteration of Population-Geometry in Mouse Primary Visual Cortex.typ` (README’s `manuscript.typ` pointer is stale). Frozen contract: AVB-003 matching + AVB-003F chart hashes. Ledger: `results/AVB_007_claim_ledger.md`. Chart boundary: `NDT_CHART_ADAPTATION_MAPPING.md`. Science-lead wording (`project/sciencelead/alllen_institute/011.md`): the result validates **this operational endpoint**, not NDT generally.

**Design.** Allen Visual Behavior Neuropixels, `allensdk==2.16.2`, 30 sessions / 30 mice (one session per mouse). Primary contrast: omission vs locally matched expected image in the **active** block; no-replacement tier-1 matcher (same preceding-image identity, \(|\Delta\) flashes since last change\(|\le 2\)); 100% match, 30/30, median distance 1 presentation. Rejected as primary: `active_vs_passive` (non-interleaved block gap ~1822 s); `hit_vs_miss` (PASS but motor-confounded by construction). Chart: 25 ms bins, six named 150–300 ms epochs, 9D features → 3D \((x_m,x_d,x_e)\). Endpoint: \(\delta_{\mathrm{omission}} = \overline{d}_{\mathrm{post}} - \overline{d}_{\mathrm{pre}}\).

**What was measured.** Chart **distance** between two conditions, then its pre→post change. Not a local flow, not residual covariance shape, not \(\Sigma^{(h)}\). AVB-003’s `mnj_reachability` block existed in the epoch contract but was **gated exploratory and never executed**; AVB closed on the scalar geometry endpoint.

**Primary numbers (AVB-005 / S2).** VISp median \(\delta=0.9799\) (\(\approx 0.980\)), \(p=9.999\times10^{-5}\), 30/30 LOSO positive. Secondary (BH-FDR): VISam \(n=28\), median \(1.1385\), \(q=1.5\times10^{-4}\); LP \(n=25\), median \(0.8299\), \(q=1.5\times10^{-4}\); CA1 \(n=30\), median \(0.0085\), \(q=0.312\) (not significant). LGd 13/30: descriptive only.

**Falsification (C1–C5, all PASS).** C1 pre-event: median pre \(0.512\) vs post \(1.455\), \(p(\mathrm{pre\,excess})=0.398\). C2 pseudo-omission: median \(-0.103\), \(p=0.173\). C3 time-shift: true \(0.980\) vs shifted \(-0.458\), paired \(p=9.999\times10^{-5}\). C4 behavior: ratio \(1.006\). C5 unit-count/rate: ratio \(1.012\).

**Specificity (AVB-006, 5/5 PASS).** A reward \(\pm 3\) s: median \(0.9825\), ratio \(1.0026\). B1 leave-one-image: 14/14 LOO medians positive. B2 identity-specific: only 2/14 identities meet \(\ge 10\) pairs and \(\ge 20/30\) sessions (im083_r \(0.703\), im111_r \(0.825\)); 12/14 not formally counted — **genuine power limit**. C locality \(|\mathrm{abs\_distance}|\le 2\): median \(0.9698\), ratio \(0.9897\). D VISp vs CA1 paired: median difference \(1.1711\), \(p=1.0\times10^{-4}\), \(n=30\).

**Recoverability.** Level 1 **internal_validated**. Level 2 only vs the frozen technical battery (matching, alignment, coarse locomotion/lick/time-in-block, reward proximity, single-image dominance, pair distance). **Not** Level 2 vs prediction-error / memory-trace / generative-model / conscious-expectation. Levels 3–4 **not attempted**. Residual contract for operator ID: **absent**.

**Claim ceiling.** Under the frozen AVB-adapted contract, omission of an expected image produces a reproducible, event-locked increase in omission-vs-expected population-chart distance in mouse VISp, with within-dataset secondary-region convergence in VISam and LP and a paired excess over CA1; this does not validate canonical MNPS, a mechanism, a Jacobian, or reachability.

| Tag | Value |
|---|---|
| Layer | `state` (AVB-adapted chart geometry). `measurement_contract` for the `m_a` redefinition. **Not** `possible_futures`. |
| Evidence class | `internal_validated` (VISp primary + C1–C5 + A–D); CA1 null is `internal_validated` as this operationalization, `plausible` as biological specificity |
| Flagship role | `evidence_matrix` (closest analog: spindles as event-locked *state* reconfiguration). Not a new main-text anchor. |
| Claim ceiling | Event-locked VISp chart-separation change under this contract; not MNPS identity, not NDT operator, not prediction error. |

---

### 2. ARR — CA1–VISam speed coupling (folder says “reachability”)

**Source of truth.** `allen_visual_behaviour_region_reachability/manuscript.typ` title: *Stimulus Omission Is Associated with a Reproducible, Control-Robust Increase in CA1-Visual-Association-Cortex Speed Coupling*. Glossary (`S5`) is the object-ID record. README + abstract: **plausible interpretation, not established finding**. Diverging track; cannot change AVB.

**Two constructs — do not collapse.**

**D2 (primary, matrix-free).** For each region, 5 epoch-to-epoch speeds \(\|\Delta X_t\|_2\). Coupling = Pearson \(r\) of the two speed sequences. \(\Delta\mathrm{coupling} =\) omission − expected. Symmetric / undirected. **This is not \(\Sigma^{(h)}\).**

D2 numbers (S2): descriptive screen — only CA1–VISam stands out (25/28 positive, sign-test \(p=2.7\times10^{-5}\)); other five pairs near chance (fractions 0.40–0.52). Inferential: CA1–VISam median \(\Delta\mathrm{coupling}=0.5793\), \(N_{\mathrm{perm}}=2000\), raw \(p=5.00\times10^{-4}\), BH-FDR \(p=0.003\), `SURVIVES_FDR`; other five pairs `NOT_SIGNIFICANT` at \(N=100\). ARR-004a residualization (run speed / lick / time-in-block): unadjusted \(0.579\) → adjusted \(0.599\), ratio **1.03**, no attenuation. ARR-004b pseudo-omission: median \(-0.020\), \(p=0.856\), ratio \(-0.034\). **Deferred:** full AVB-006 battery, C3 time-shift, pupil.

**D1 (attempted NDT-adjacent reachability; not the headline).** Discrete \(A,Q\) on 6-epoch trajectories; \(\Sigma^{(h)}\) at \(h=1,3\); quality gate spectral radius \(<1\) **and** residual fraction \(\le 0.5\); bar \(\ge 20\) sessions with \(\ge 50\%\) pass. Verdicts: VISp omission 15/30 = 0.500 `PASS` (exact boundary); VISp expected 11/30 = 0.367 `WARN`; most other cells `WARN`; LGd `STOP` (\(n<20\)). **Every one of 240 fits has `J_residual_df_per_output = 1`** (5 transitions vs 4 parameters per output). `FIT_OK` is near-universal; quality is not. No-rescue rule: VISp is reported as the combined marginal picture, not rescued by the omission-only boundary PASS.

D1 therefore **does not** supply an admissible residual contract for Level-4 operator identification. Importing D1 \(\Sigma^{(h)}\) as NDT possible-futures evidence would be category drift.

**ARR-005 methodological (not a biological win).** Naive pooling of omission+expected epochs inflates \(\mathrm{Tr}(Q)\) in **100% of 126** session×region combinations (median ~2.2–3.6×; VISp ~3.6×; sign-flip \(p<0.007\) every region). Confirms condition-separated fitting. Ill-conditioned flags: `cone_anisotropy` 8/504 rows, `innovation_transport_ratio` 0/504. Level-2 post-hoc screen: 17/85 well-conditioned metric×region×horizon combinations survive BH-FDR + residualization + C2-style control (VISam 10, VISp 5, LP 2). Paper: secondary, post-hoc, inherits D1 WARN quality — **not** promoted to the D2 claim.

**Recoverability.** D2: Level 1 association, **plausible**; bounded technical Level 2 (two controls); disclosed post-hoc pair selection blocks treating CA1–VISam as an independent pre-registered hit. D1: estimator-quality **method-limited**; Level 4 **not licensed**.

**Claim ceiling.** Omission is associated with a control-robust increase in **undirected CA1–VISam chart-speed coupling** under this exploratory contract; NDT reachability cones, Jacobian identity, anatomical direction, and mechanism are **not** established. D1 residual-starved fits do not identify a local operator.

| Tag | Value |
|---|---|
| Layer | D2: `state` (speed-profile coupling). D1 attempted `local_dynamics` / `possible_futures` and **failed the quality gate for claims**. |
| Evidence class | D2 `plausible`; D1 quality result `internal_validated` as a **negative/method-limit**; pooling inflation `internal_validated` (methods) |
| Flagship role | `evidence_matrix` or `supplement`. **Terminology warning:** do not say “Allen reachability” without naming D2 vs D1. |
| Claim ceiling | Speed coupling, one pair, post-hoc selected; not NDT \(\Sigma^{(h)}\). |

---

### 3. AGR — global (joint) speed-coupling average

**Actual status (do not trust the README table blindly).** Header + `results/AGR_002/AGR_002_result_interpretation.md`: AGR-002 **complete**. The same README’s relationship table still says “AGR-002 not yet run,” and `manuscript.typ` / S1–S6 are **unedited aa_template placeholders**. Computationally closed; article **not written**.

**What was (and was not) tested.**

- **G1** joint transfer-operator fit: **rejected before computation** (parameter starvation inherited from D1’s 6-epoch floor, worse in 12D joint state). So AGR never estimated a global \(A,Q,\Sigma^{(h)}\).
- **G2** (run): `global_coupling` = mean of 6 pairwise D2 speed correlations on the 4-region set (CA1, VISp, VISam, LP). Strict all-four-or-drop rule: **23/30** sessions jointly eligible.
- **G3** joint-state volume: **parked**.

**G2 numbers.** AGR-001a descriptive: median \(\Delta=0.113\), 52.2% sessions positive, sign-test \(p=1.0\); secondary eigenvalue-fraction 69.6% positive, descriptive \(p=0.093\) (**not promoted**). AGR-002: observed median `delta_global_coupling` **0.1131**, \(N=200\), two-sided \(p=0.1194\), Monte Carlo SE \(\approx 0.035\), verdict **`NOT_SIGNIFICANT`**. Higher-\(N\) confirmatory **not planned**.

**Object ID.** G2 is a **scalar average of speed couplings**. Averaging the five non-significant pairs with CA1–VISam is expected to dilute ARR’s local hit; that dilution reading is `plausible`, not a decomposed contribution audit.

**Recoverability.** Formal permutation execution: `internal_validated`. Scientific path for this G2 design: `rejected`. Not a falsification of “global reachability” as a general NDT construct (that object was never estimated). Not qMRI.

**Claim ceiling.** The matrix-free 4-region mean of pairwise chart-speed correlations shows no significant omission-related shift on this sample; this does not test NDT global reachability cones.

| Tag | Value |
|---|---|
| Layer | `state` (averaged speed coupling). G1 would have been operator-class and was **not run**. |
| Evidence class | `rejected` (G2 design); `internal_validated` (the p-value / execution) |
| Flagship role | `supplement` as a **negative design note**, or `exclude` from main-text geometry paragraphs |
| Claim ceiling | This G2 scalar is not a significant omission effect; do not generalize to NDT possible-futures. |

---

### 4. 24-hour mPFC calcium–EEG–EMG (Han / G-Node)

**Source of truth.** Long-title audit article `What a 24-Hour Simultaneous mPFC Calcium-EEG-EMG Dataset Can Support.typ`; README; `sciencelead/001.md` (handover of **dataset facts**, written before the local block); `preregistration/E001_measurement_and_primary_analysis_contract.md`.

**External resource (established_external; not re-derived locally).** Han et al., *Scientific Data* 2025 (`10.1038/s41597-025-05527-2`); G-Node `10.12751/G-NODE.1762HN`. Five mice, six recordings (>24 h); mouse 4 has two sessions; mouse `#4_2` part 1 lacks EEG. GCaMP6f, one prelimbic FOV, mostly **1.92 Hz** (mouse 5: **0.96 Hz**); EEG–EMG **1,000 Hz**, two EEG channels + neck EMG; sleep/behavior labels; reversed LD cycle. **Not** spikes, **not** dendrites, **not** whole-brain, **not** millisecond Ca–EEG directionality.

**Local audit (internal_validated as a gate, not as physiology).** 1,840 source entries at commit `dc27abf49f370fb820444914c492cdb446d78ce7`. Required processed calcium traces, filtered EEG–EMG, and behavior labels: git-annex pointers or unreadable. Readable ROI-set assets in some parts are **insufficient** for multimodal eligibility. Gate: **`E001_BLOCKED_UNREADABLE_OR_INCOMPLETE`**. Zero eligible complete segments. S2: no state/spectral/geometry/prediction table exists because E001 was outcome-blind and blocked.

**What the dataset can support *if* readable assets are acquired** (frozen future question, not a result): whether a predeclared mPFC population-geometry feature set improves blocked held-out prediction of a slow EEG spectral/state representation **beyond** mean calcium, variance, EMG, annotated behavior, circadian time, recording part, and quality covariates. That would still be Level 1 association on a slow common grid, not Jacobian ID, not RVC, not human EEG.

**What the block does not mean.** It does **not** reject state-dependent calcium geometry, Ca–EEG correspondence, alignment, circadian reconfiguration, or NDT accessibility. Synchronization has **not been tested**. Biological \(n=5\) remains the inference unit if analysis later proceeds; frames/ROIs/parts/sessions are not independent mice.

**Claim ceiling.** The local copy cannot currently support any neural-state, dynamics, or cross-scale claim; the public dataset description remains a candidate cellular→EEG ladder pending readable acquisition.

| Tag | Value |
|---|---|
| Layer | `measurement_contract` (now); future question would sit at `state` / `epistemic` (cross-scale association), not `possible_futures` |
| Evidence class | Gate: `internal_validated`. Dataset facts: `established_external`. All physiology: **untested**. |
| Flagship role | `supplement` (audit boundary) or `exclude` from empirical matrix cells until E001/E002 pass |
| Claim ceiling | Unreadable local annex ≠ biological null. |

---

### 5. Dryad Cecchetto — simultaneous acquisition vs figure-source release

**Source of truth.** `DataDryad Simultaneous two-photon imaging multichannel LFP/manuscript.typ`; sciencelead `001` (gate) and `002` (E003 executed). Dryad `10.5061/dryad.dbrv15f23`; paper `10.3389/fnins.2021.741279`.

**Release contract.** Original experiment acquired two-photon voltage **or** calcium with 32-channel laminar LFP and a surface electrical signal (called **EEG** in the release; not scalp EEG). Public product: **67 MAT files**, eight usage notes, **280** inspected variables; every array is a **4 s (4001 samples) or 6 s (6001 samples)** peri-airpuff window. No continuous timebase, frame-sync, TTL, or raw timestamp channel. Nested archive: 75 members, name/size match, **no hidden raw**. **No mouse** has matched single-trial optical **and** electrical data. Voltage branch: 6 mice, already-averaged VSD/LFP/EEG/speed. Calcium branch: 4 mice, per-mouse averages; **no per-mouse LFP or EEG**.

**Gate:** **`E001_LIMITED_AVERAGE_ONLY`**. Blocks Stage 2 synchronization and the original E004–E010 geometry / prediction / MNPS ladder **as designed**.

**E003 (descriptive only; sciencelead: not a standalone paper).** Frozen windows: voltage 0–500 ms, calcium 0–2000 ms, baseline −500 to −100 ms. Mouse-level mean ± SD of **one already-averaged waveform per mouse**; **no p-values**. Example S2 numbers (not tests): VSD 50 µm signed peak anaesthesia \(-0.33\pm 0.10\) vs awake rest \(-0.99\pm 0.53\); speed sanity 0.000 / 0.007 / 5.223 cm/s (anaesth / rest / running) — mapping check only. QC rows: 216 voltage, 1,728 LFP-channel, 58 calcium (two expected rows missing). Documented release inconsistencies: Fig2E/F documentation vs mouse4-only files (excluded); Figure S2 130 µm running calcium **three columns** vs four-mouse Figure 7 ROI counts (identity not guessed); 4/46 calcium polarity rows opposite signed peak.

**Recoverability.** File-mapping QC: `internal_validated`. Cross-scale geometry / trial prediction / Jacobian / reachability: **not feasible from this release**. Do not treat author-facing pattern match as independent replication.

**Claim ceiling.** The public Dryad product supports descriptive reproduction of peri-stimulus **averages**, not reconstruction of simultaneous cross-scale dynamics; acquisition simultaneity does not license release simultaneity.

| Tag | Value |
|---|---|
| Layer | `measurement_contract` |
| Evidence class | Gate + E003 mapping: `internal_validated`. NDT geometry: **not supportable** (do not code as `rejected` biology). |
| Flagship role | `supplement` (reuse-boundary caution) or `exclude` from empirical cells |
| Claim ceiling | Figure-source averages ≠ continuous synchronized optical–electrical series. |

---

## Claims table

| Object | Claim | Evidence class | Layer | Flagship role | Claim ceiling | Negative/limit |
|---|---|---|---|---|---|---|
| AVB `delta_omission_geometry` (VISp) | Omission increases omission-vs-expected chart distance; median 0.980; 30/30; \(p=9.999\times10^{-5}\) | `internal_validated` | `state` | `evidence_matrix` | Event-locked AVB-adapted chart separation in VISp | Not MNPS identity; `m_a` redefined; single paradigm; no Jacobian/\(\Sigma^{(h)}\) |
| AVB C1–C5 / 006 A–D | Effect not pre-event, not matcher artifact, not shifted alignment; survives coarse behavior, unit/rate, reward window, image non-dominance, locality; VISp > CA1 paired | `internal_validated` | `state` / `measurement_contract` | `evidence_matrix` | Technical alternatives in the frozen battery are not sufficient explanations | B2: only 2/14 identities formally powered; not mechanism discrimination vs prediction error |
| AVB VISam / LP | Secondary-family FDR-significant same-sign \(\delta\) | `internal_validated` | `state` | `evidence_matrix` | Within-dataset regional convergence | Same animals/paradigm/contract; not independent replication (sciencelead 011) |
| AVB CA1 \(\delta\) | Not significant after FDR (\(q=0.312\)); paired VISp−CA1 median diff 1.171 | `internal_validated` (this chart); `plausible` as anatomy | `state` | `supplement` | Specificity observation under this contract | Cannot separate genuine absence vs power/chart masking |
| ARR D2 CA1–VISam `delta_coupling` | Median 0.579; FDR \(p=0.003\); residualization ratio 1.03; C2 median −0.020 | `plausible` | `state` (speed coupling) | `evidence_matrix` or `supplement` | Undirected chart-speed coupling, one pair | Post-hoc biggest-hit; 2/5 AVB-class controls; not \(\Sigma^{(h)}\); no direction |
| ARR D2 other 5 pairs | Near chance; FDR non-significant | `internal_validated` (nulls) | `state` | `supplement` | Coupling shift is not a generic all-pairs phenomenon | Does not prove anatomical uniqueness beyond this family |
| ARR D1 \((A,Q,\Sigma^{(h)})\) | 6-epoch local-linear reachability estimator is residual-starved (df=1 everywhere); mostly WARN | `internal_validated` (quality **fail** for claims) | attempted `local_dynamics` / `possible_futures` | `supplement` (method limit) | Construct not usable for a primary NDT reachability claim | Residual fraction gate largely unmet; not operator ID |
| ARR-005 pooling \(\mathrm{Tr}(Q)\) | Mixed-condition pooling inflates innovation 2.2–3.6×; 126/126 | `internal_validated` | `measurement_contract` | `supplement` | Do not pool tasks then call the cone “reachability” | Methods lesson; not a biological accessibility result |
| ARR Level-2 17/85 cluster | Post-hoc well-conditioned metrics survive two controls; VISam 10/17 | `plausible` | `local_dynamics` (weak, inherits D1 WARN) | `exclude` from headline cells | Hypothesis-generating only | Selected from 85; not pre-registered |
| AGR G2 `delta_global_coupling` | Median 0.1131; \(p=0.1194\); NOT_SIGNIFICANT | `rejected` (this design) | `state` | `supplement` / `exclude` | Mean pairwise speed coupling is not a significant omission effect | G1 operator never fit; G3 parked; manuscript unwritten |
| 24h Han dataset (published facts) | Simultaneous mPFC Ca + EEG–EMG + video, 5 mice, >24 h | `established_external` | `measurement_contract` | `supplement` (candidate ladder) | Resource exists as described by authors | Slow Ca rate; \(n=5\); one FOV; two EEG channels |
| 24h E001 local gate | No readable complete processed multimodal segment (git-annex) | `internal_validated` (access) | `measurement_contract` | `supplement` | Analysis blocked until acquisition | **Not** a biological null |
| Dryad release structure | Peri-stimulus averages; 67 MAT; no sync/TTL/continuous | `internal_validated` | `measurement_contract` | `supplement` | Figure-source reuse only | Original simultaneity ≠ public product |
| Dryad E003 averages | Mouse-level descriptive peaks; speed mapping 0 / 0.007 / 5.223 cm/s | `internal_validated` (extraction) | `measurement_contract` | `exclude` from NDT geometry | Reproduction of averages, no tests | Fig2E/F and S2 mismatches; 4/46 polarity disagreements |

---

## Required negatives / method limits

1. **Do not call ARR or AGR “NDT reachability.”** Headline ARR is Pearson of chart **speeds**. AGR G2 is the mean of those Pearsons. NDT possible-futures objects are residual-calibrated predictive-spread / \(\Sigma^{(h)}\) (coma-class), not speed coupling. Say the object.
2. **AVB does not estimate local dynamics or futures.** Population-geometry change on omission is a **state** constraint. MNJ/reachability was explicitly deferred in AVB-003 and never run on the primary line.
3. **ARR D1 is not a back-door operator ID.** Residual-df floor = 1 on all 240 fits; quality mostly WARN; residual-fraction \(\le 0.5\) not generally met. Level 4 remains closed. Pooling-inflated \(Q\) (ARR-005c) is a documented way to **fake** a larger cone; it is a caution, not a result to promote.
4. **CA1–VISam is not an independent replication of AVB.** Different object (coupling vs chart distance), post-hoc pair selection, thinner control battery. AVB’s CA1 **null** on \(\delta_{\mathrm{omission}}\) and ARR’s CA1–VISam **coupling hit** are not a contradiction and must not be averaged into “hippocampus does/doesn’t participate.”
5. **VISam/LP are not independent labs.** Same mice, same flashes, same chart.
6. **AVB chart ≠ canonical MNPS.** `m_a` functional form changed; cross-dataset distance magnitudes are **not currently justified** (`NDT_CHART_ADAPTATION_MAPPING.md`).
7. **No prediction-error / expectation / consciousness claim** from AVB or ARR (both papers’ own ceilings).
8. **No qMRI / cytodendritic bridge** from this cluster (no structural arm).
9. **AGR G2 fail is design-specific.** It does not falsify global NDT reachability in general, because that estimator was never identified (G1 not run).
10. **`E001_BLOCKED_UNREADABLE_OR_INCOMPLETE` ≠ no Ca–EEG coupling in mice.** Git-annex pointers are metadata, not empty physiology.
11. **`E001_LIMITED_AVERAGE_ONLY` ≠ the original Cecchetto experiment lacked simultaneity.** The **release** lacks continuous synchronized trial data. Do not analyze averages as if they were residual time series.
12. **AGR manuscript is not a result.** Placeholder typst is not a negative paper; the result lives in `AGR_002_result_interpretation.md`.

---

## Flagship placement vs existing anchors

Main-text empirical anchors remain exactly three (`00_synthesis.md` / summaries README):

1. **Sleep spindles / RVC event-locking** — event-locked 9D *state* reconfiguration (`d_n` timing), not denoising.
2. **Coma / recovery-linked geometry** — strongest “where you are is insufficient” constraint; short-horizon **reachability-class** geometry under that clinical contract.
3. **DANDI 000458** — Level-1 meso–macro association (\(\rho\approx 0.4\)) **plus** Level-4 operator **failure** (residual fraction 0.856).

**Where this cluster sits.**

| Candidate | Relation to anchors | Default placement |
|---|---|---|
| **AVB omission geometry** | Same *kind* of claim as spindles (event-locked **state** reconfiguration), different species/paradigm/chart. Stronger control battery than many matrix cells, but AVB-adapted `m_a` and no operator test. | **`evidence_matrix`** (one bounded cell: expectation-omission changes sensory-cortical chart geometry). Not Anchor 4. |
| **ARR D2 speed coupling** | **Not** analog to coma reachability. Coma constrains possible futures; ARR D2 constrains correlated **speeds**. | **`evidence_matrix` or `supplement`**, labeled speed-coupling. |
| **ARR D1 / AGR G1** | Would have been the Allen test of local operator / futures; D1 quality fail, G1 not run. Complements 000458’s Level-4 fail: **another** chart where operator ID is not licensed. | **`supplement`** as estimator-limit, alongside 000458 residual 0.856. |
| **AGR G2** | Negative on a **non-NDT** global scalar. | `supplement` / `exclude` from futures paragraphs. |
| **24h Han** | Would be a cellular→EEG cousin of Anchor 3 **if** E001/E002 pass. Currently blocked. | `supplement` (resource + access gate). Do not fill a matrix cell with “no effect.” |
| **Dryad Cecchetto** | Would have been optical–laminar–surface, closer to a true meso–macro chain than 000458’s LFP-proxy–EEG. Release forbids it. | `supplement` (release-boundary). Same moral as 000458: **contact is not identity**, and here even contact is not in the public files. |

**Editorial default (this intake):** evidence_matrix or supplement, **not** a new main-text anchor. If a later pass wants a fourth empirical beat, AVB state-geometry is the only candidate in this folder that is `internal_validated` at Level 1 with a real control battery — and even then it should sit next to spindles as *state*, never next to coma as *reachability*.
)
