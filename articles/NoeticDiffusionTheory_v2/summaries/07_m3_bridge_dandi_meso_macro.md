# 07 — m3-bridge: DANDI / meso–macro cluster

Internal cartography for NDT 1.0 / Noetic Diffusion Theory v2. Source repo: `J:\repos\m3-bridge`. Intake date: **2026-08-30**. Architecture filter (frozen): **State geometry → Local dynamical geometry → Geometry of possible futures → Control of accessibility.**

**Recoverability ladder:** (1) association → (2) mechanism discrimination → (3) latent-order preservation → (4) dynamical-operator identification. Success at one level does not license a stronger claim.

**Tag schema:** Layer (`state` / `local_dynamics` / `possible_futures` / `control` / `epistemic` / `measurement_contract`) · Evidence class (`established_external` / `internal_validated` / `plausible` / `speculative` / `rejected`) · Flagship role (`main_text_anchor` / `evidence_matrix` / `supplement` / `exclude` / `terminology_only`) · Claim ceiling (one sentence).

**Overlap with `03_ndt_subsystems_empirical.md`.** Summary 03 already ingested DANDI 000458 from ndt-subsystems / NDT_2 as Anchor 3: Level-1 ρ≈0.4; Level-4 residual fraction 0.856 FAIL; Figshare opto PRRG/SDSR/TA-E1 closed. **m3-bridge is now the canonical article source for the 000458 association + residual pair.** The numbers match (see §Overlap). PRRG/SDSR/TA-E1 were **not** re-run here; keep those closures on summary 03. Do not double-count.

MNPS ≠ NDT. NMD ≠ NDT. Cross-scale correlation ≠ operator ID. A blocked audit gate is not biological negative evidence. Do not restore TRN-as-variance-clamp. Do not treat 000458 association as MNPS identity.

---

## Inventory

Read (abstracts, READMEs, sciencelead/handovers, S2/S3/S6, claim ledgers — not full 80-page bodies). Skipped `aa_template`, backends, and incomplete template workspaces except where they change a claim (they do not). Folder name `000458_TRN_meso_macro_brige` is the real on-disk spelling.

| Cluster | Path under `m3-bridge/articles/` | Status as of 2026-08-30 |
|---|---|---|
| **000458 discovery association** | `DANDI/000458/` — `Trial-aligned associations between Neuropixels proxies and surface EEG.typ` (preprint v0.2, 2026-08-19); `claim_ledger.md`; README; S2/S3/S6 | **Canonical article for Anchor 3 numbers.** Conditional Level-1 associations; Level-4 EEG-chart FAIL. Alignment INCONCLUSIVE. |
| **E012 replication lock** | `DANDI/000458/Exact independent replication is currently not estimable.typ`; `sciencelead_material/` | **Canonical method-boundary.** No eligible public Tier-A source. Not a negative replication. |
| **Meso–macro chain** | `DANDI/000458_meso_macro_chain/` | **NEW.** `BLOCKED_NO_CHAIN_INFERENCE` / `TERMINATED_NO_REEXTRACTION`. Measurement gate, not a biological null. |
| **TRN causal bridge** | `DANDI/000458_TRN_meso_macro_brige/` (typo is real). `manuscript.typ` is still `aa_template`. Real content: sciencelead `002`, handover `003`, `results/TRN_C001_source_qualification/` | **NEW.** `NOT_ESTIMABLE_WITH_CURRENT_ARCHIVES`. Do not pool DANDI + Figshare. |
| **Figshare opto (m3-bridge)** | `DANDI/000458_Figshare_opto/` — `TRN optogenetic rebound timing reanalysis.typ`; `meso_only_claim_ledger.md`; F101 protocol. `manuscript.typ` and S2/S6 remain template | **Different experiment from summary-03 PRRG/SDSR/TA-E1.** Meso-only rebound-timing mixed. No macro EEG. |
| **000574 human MTL** | `DANDI/000574/` — titled negative manuscript; README; claim ledger; S2/S3 | **NEW.** Both frozen primary pairs FAIL (median r=0.100 / 0.062). Independent of 000458; not a replication. |
| **000939 audit (this repo)** | `DANDI/000939/` | **NEW as m3-bridge local audit.** Gate **BLOCKED** (no local NWB; no documented macro). Do not overwrite ndt-subsystems 000939 PRRG closures. |
| **000248** | `DANDI/000248/` | **Incomplete.** Download handover only; README and `manuscript.typ` are templates. No analysis. |
| **Replacement chain audit** | `replacement_meso_macro_audit/` | **NEW.** `NO_QUALIFYING_PUBLIC_SOURCE_IDENTIFIED`. Metadata-only. |

Not in this cluster (skip): `DANDI/ibl_000409_prior_reachability/`, other DANDI folders.

---

## Overlap with summary 03 (do not double-count)

| Object | Summary 03 (ndt-subsystems / NDT_2) | This intake (m3-bridge) | Verdict |
|---|---|---|---|
| Anchor 3 Level-1 | ρ≈0.4 LFP–EEG variance and spike–entropy | Median subject Spearman **r=0.406** (LFP SD ↔ EEG SD) and **r=0.395** (spike rate ↔ EEG spectral entropy); both sign-flip q=0.027, time-shift q=0.003; 17 subjects / 18 sessions | **Match.** Cite m3-bridge for exact r. Same claim ceiling. |
| Anchor 3 Level-4 | Residual fraction **0.856** FAIL | Manuscript 0.856; S2/S3 **0.8557**; 1,440 points / 24 sessions EEG-only 3-coordinate chart | **Match.** Round 0.856 in main text; 0.8557 is the archived diagnostic. |
| Alignment | Not foregrounded in 03 | E002 **INCONCLUSIVE**: 0/24 unqualified pass; 1/24 partial timestamp coverage; 23/24 inconclusive | **Reporting update**, not a number change. Associations remain *conditional on nominal event alignment*. |
| Isoflurane / E007–E008 | Not in 03’s Anchor 3 pair | After spectral-splice bugfix: isoflurane spike–entropy stratum **FAIL** (r=0.043, sign-flip q=0.161); paired Δ=−0.261 (exploratory, post hoc) | **New internal constraint** on the same dataset. Does not replace the primary pair. |
| Figshare Russo | PRRG rejected; SDSR unidentifiable; TA-E1 `FAIL_Q_PRESTIM_CONTROL`; ΔPR stability-limited | m3-bridge: F103 locked all-good-unit rebound Δ=**−0.32 ms**, sign-flip **p=1.0**, LOO unstable; no EEG/ECoG in archive | **Do not merge.** 03 remains canonical for PRRG/SDSR/TA-E1. This repo’s rebound paper is a separate meso-only secondary endpoint. |
| 000939 | ndt-subsystems: PRRG 50 ms invalid pulse; 1 s opposite entropy | m3-bridge: local transfer **not done**; meso–macro **BLOCKED** | **Do not overwrite 03.** This folder is a measurement-contract audit, not a PRRG result. |

**Canonical-source rule.** For the flagship Anchor 3 *article* and exact association/residual numbers, use `m3-bridge/articles/DANDI/000458/`. For TRN mechanism falsifications (PRRG, SDSR, TA-E1, TRN-VG, TA-E2), keep summary 03 / ndt-subsystems.

---

## Executive take for the NDT article (≤15 lines)

m3-bridge is the **canonical write-up of Anchor 3**, not a second discovery. Under a frozen 60-trial protocol, Neuropixels LFP-SD and quality-filtered spike rate associate with surface-EEG SD and spectral entropy at median subject r **0.406** and **0.395**. The same archive’s EEG-only local-linear chart has residual-variance fraction **0.856**, so Jacobian/reachability remain **rejected**. That pair still licenses only Level-1 contact plus Level-4 operator failure. Alignment was never validated; claims stay conditional on nominal event labels.

What is new here is mostly **gates, not geometry**. A three-stage prediction chain (local population geometry → distributed regional dynamics → surface EEG) is blocked: timing INCONCLUSIVE and the parent table is not region/unit-resolved. Exact independent replication of the exploratory awake–isoflurane spike–entropy contrast is **not estimable** from public metadata (E012). A TRN → meso → macro causal bridge is **not estimable** because DANDI 000458 has no TRN opto and Figshare opto has no surface EEG; pooling is forbidden. Figshare in this repo yields a mixed all-unit rebound-timing summary, not a restored variance clamp. Human DANDI 000574 fails the same style of conjunctive nulls (r=0.100 / 0.062) — a **design-matched negative**, not a falsification of 000458 and not a new main-text anchor. 000939 (this repo) and 000248 contribute no neural result.

---

## Per-article memos

### 1. DANDI 000458 — trial-aligned associations (canonical Anchor 3 article)

**Design.** DANDI 000458 version `0.230317.0039`; 24 NWB / 23 mice; 18 sessions / 17 subjects with EEG+LFP+units. Meso: post-artifact LFP-SD proxy (median-positioned channel per probe, 10× decimated, probe-averaged); quality-filtered spike rate; participation ratio (not a primary passer). Macro: EEG SD (first eight channels) and spectral entropy. Subject-level Spearman; sign-flip and circular time-shift nulls; BH-FDR on nine meso×macro pairs; LOSO.

**Level 1 (internal_validated, conditional).** Two of nine pairs pass both nulls: LFP-SD ↔ EEG-SD r=0.406; spike rate ↔ EEG spectral entropy r=0.395. Both survive 11/11 extraction-sensitivity variants (LFP r range 0.293–0.444; spike r range 0.309–0.402 on the grid as reported). E009c speed-control family **PASS** (all four frozen tests q=0.001; speed-adjusted r: LFP 0.307/0.323, spike–entropy 0.221/0.178). This is sensitivity, not causality.

**Level 1 limits (do not drop).** E002 alignment **INCONCLUSIVE**. Matched artifact-window LFP pairs **non-estimable**. E009b structured nulls **INCONCLUSIVE** (circular shift / wrong-state / amplitude shuffle pass at q=0.001; same-state wrong-session has 1 subject / 2 sessions, below the 5-subject gate). E009d prestimulus specificity **BLOCKED** (raw-NWB stall). Isoflurane-alone spike–entropy **FAIL** after spectral-splice fix. Recovery underpowered (8–9 subjects). E008 spike–entropy paired Δ=−0.261 is **exploratory** (protocol locked after E007 inspection). LFP–EEG state contrast does not pass sign-flip (Δ=+0.195, q=0.146).

**Level 4 (rejected).** EEG-only chart (SD, spectral entropy, beta power): median residual variance fraction **0.856** (0.8557 in S2). Association does not repair estimator failure. Exploratory J_trace 0.6330, J_rotation_norm 0.2849, reachability effective dimension 2.1679 are **not** licensed as MNJ.

**Recoverability.** Level 1 bounded; Level 2 not established (no TRN/cortex/arousal/artifact discrimination); Level 3 not claimed; Level 4 failed.

| Tag | Value |
|---|---|
| Layer | `epistemic` (bridge); measurements sit at `state` only |
| Evidence class | `internal_validated` (association); `rejected` (operator ID) |
| Flagship role | `main_text_anchor` — **same Anchor 3, not a new anchor** |
| Claim ceiling | Conditional trial-aligned covariation under nominal event alignment after subject-level nulls; not validated coupling, direction, common latent, MNPS identity, MNJ, TRN, or NDT mechanism. |

### 2. Exact independent replication is currently not estimable (E012)

Metadata-only audit for a Tier-A independent test of the **exploratory** awake-versus-isoflurane spike–entropy Δ. Contract: independent subjects; simultaneous surface EEG + units; explicit awake and isoflurane; compatible timing; reconstructable unit QC; adequate paired support. Result: **NO ELIGIBLE PUBLIC SOURCE**; E013–E023 not authorized. Absence of a candidate is **not** a negative replication and does not change the discovery association.

| Tag | Value |
|---|---|
| Layer | `measurement_contract` |
| Evidence class | `internal_validated` (procedural / source-availability); `rejected` as a biological outcome |
| Flagship role | `supplement` |
| Claim ceiling | Exact independent replication of the E008 contrast is not estimable from audited public metadata; this is a data-availability boundary. |

### 3. 000458 meso–macro prediction chain (D458_MMC)

Prespecified chain: local population geometry → distributed regional dynamics → surface-EEG dynamics. Primary endpoint (never run on real data): held-out subject-level M4−M1 R² for EEG spectral-entropy prediction. Frozen gates: validated EEG–ephys timing (≥10 fully passing subjects) and a region- and unit-resolved trial table.

**Gate: `BLOCKED_NO_CHAIN_INFERENCE`.** Parent E002 INCONCLUSIVE; parent feature table aggregates probes (no `region_id` / `unit_id` / per-region spike-count vector). Provenance follow-up: `TERMINATED_NO_REEXTRACTION`. Synthetic fixture only: M4−M1 median R² **0.072**; circular shift **−0.014**; amplitude shuffle **0.004** — workflow check, not biology. Parent LFP–EEG association is neither promoted nor demoted.

| Tag | Value |
|---|---|
| Layer | `measurement_contract` / conceptually `possible_futures` if ever run |
| Evidence class | `internal_validated` (software + synthetic); real-data chain **not estimable** |
| Flagship role | `supplement` (epistemic: association ≠ ordered chain) |
| Claim ceiling | DANDI 000458 cannot currently support this three-stage prediction claim. Blocked gate ≠ evidence that meso and macro are uncoupled. |

### 4. TRN meso–macro bridge (`000458_TRN_meso_macro_brige`)

`manuscript.typ` is an unfilled template. Canonical record: TRN_C001 source qualification (2026-08-03).

DANDI 000458: meso + macro, **no** TRN opto. Figshare 28440311 v1: timed TRN opto + processed meso (6 mice, 32 probe pairs), **no** documented surface EEG/ECoG (F001: zero `eeg`/`ecog`/`surface` filename candidates). **Decision: `NOT_ESTIMABLE_WITH_CURRENT_ARCHIVES`.** Do not pool. Mixed F103 rebound result does not speak to this estimand. Ceiling of a *future* joint study (handover): preparation-level change of one predeclared meso and one predeclared macro endpoint — still not NDT, SDSR, PV-vs-SOM, or variance-gating.

| Tag | Value |
|---|---|
| Layer | `measurement_contract` / `control` (untested) |
| Evidence class | `internal_validated` (qualification); causal bridge **not estimable**; absence-of-TRN-effect **rejected** as a reading |
| Flagship role | `exclude` from mechanism paragraphs; `supplement` as identifiability stop |
| Claim ceiling | No current archive jointly records TRN perturbation, meso, and surface macro with shared identifiers. |

### 5. Figshare opto — locked rebound-timing reanalysis (m3-bridge only)

Russo et al. processed deposit `10.6084/m9.figshare.28440311.v1`; SHA-256 `bdeb5790…1108`; 99,668 ZIP members; 8,223 matched source-QC-good units. Meso–macro Tier-C closed (no macro). Locked all-good-unit capped first-rebound latency (75–250 ms): Opto75 minus ES-only median mouse Δ=**−0.32 ms**; exact sign-flip **p=1.00**; bootstrap 95% **−2.32 to +4.99 ms**; LOO not uniformly positive. 125-ms condition likewise mixed. Does **not** contradict Russo’s regional/unit-class analyses; does **not** show TRN has no effect; does **not** replicate 000458.

**Do not cite this folder for PRRG, SDSR, TA-E1, or ΔPR +13.** Those live in ndt-subsystems (summary 03).

| Tag | Value |
|---|---|
| Layer | `state` (meso timing summary) |
| Evidence class | `internal_validated` mixed/negative for this locked endpoint |
| Flagship role | `supplement` (negative-control on pooling / endpoint fishing); `exclude` as TRN mechanism |
| Claim ceiling | This processed all-unit rebound-timing summary is mixed; it is not a meso–macro result and not a variance clamp. |

### 6. DANDI 000574 — human MTL / scalp EEG (negative)

Boran / Fedele / Sarnthein; version `0.250815.1108`; 9 subjects, 37 sessions; Sternberg verbal WM; scalp EEG 200 Hz, macro iEEG 2 kHz, micro-LFP 32 kHz; units in 29/37. Frozen **before extraction**: primary pairs scalp-EEG-std ↔ micro-LFP-std and scalp-EEG-std ↔ unfiltered spike rate; SOZ excluded; unfiltered spikes primary.

**E004 FAIL (internal_validated negative).** LFP–EEG: 35 sessions, 9 subjects, median r=**0.100**; time-shift FDR=0.008 (pass) but sign-flip FDR=**0.696** (fail). Spike–EEG: 28 sessions, 9 subjects, median r=**0.062**; FDR 0.696 / 0.076. Conjunctive rule fails both. Time-shift-only LFP pass is a weak, subject-inconsistent, temporally specific signal — **not** a pass. E003 session-level medians (r=0.104 / −0.007) are uncorrected screens. Secondary `lfp × ieeg` r=0.184 **not promoted**. Spectral-entropy pairs |r|≤0.03, untested at E004. Not pooled with 000458; does not statistically weaken or confirm 000458.

QC negatives (not biology): naive rate estimator fails on trial-concatenated storage; `sub-08/ses-05` constant-zero macro; `sub-02/ses-05` short micro-LFP; no native unit QC; 1,487 vs published 1,526 units unresolved.

| Tag | Value |
|---|---|
| Layer | `state` / `epistemic` |
| Evidence class | `internal_validated` **negative** for this design; `rejected` as 000458 replication |
| Flagship role | `evidence_matrix` (human analog **null** under this contract) — **not** a new main-text anchor |
| Claim ceiling | Under this frozen pairing and conjunctive nulls, scalp EEG variance is not robustly coupled to MTL micro-LFP or spike rate in these nine patients. Not a general falsification of meso–macro contact; not operator ID. |

### 7. DANDI 000939 — measurement-contract audit (this repo)

Handover-only: DOI `10.48324/dandi.000939/0.260512.1701`; companion Figshare `10.6084/m9.figshare.24921252`; Duszkiewicz et al. *Nat. Neurosci.* **Gate: BLOCKED.** No local NWB, checksum, QC, optogenetic cohort/target map, or documented EEG/ECoG/MEG/fMRI/widefield. S2 explicitly reports **no** effect sizes. Published-paper statements remain `established_external`; local analysis is non-estimable.

| Tag | Value |
|---|---|
| Layer | `measurement_contract` |
| Evidence class | `internal_validated` (audit of absence); neural claims **not estimable** here |
| Flagship role | `exclude` from meso–macro evidence; do not use to rewrite summary-03 PRRG rows |
| Claim ceiling | This package establishes no neural result and cannot support a meso–macro test from present local evidence. |

### 8. DANDI 000248 — incomplete

Handover `001_20260729_dandi_000248_download_handover.md` only: OpenScope Illusion, version `0.240502.2344`, ~173 GiB / 78 files / 12 mice; candidate question is illusory vs real vs control contour geometry — **not** qualia. README and `manuscript.typ` are `aa_template`. No inventory, QC, or features in this folder.

| Tag | Value |
|---|---|
| Layer | `measurement_contract` |
| Evidence class | incomplete / not a result |
| Flagship role | `exclude` |
| Claim ceiling | No analysis has been run. Do not cite as a meso–macro or content-construction result. |

### 9. Replacement meso–macro dataset audit

Outcome-blind metadata audit for a source that could run the frozen D458_MMC contract. **`NO_QUALIFYING_PUBLIC_SOURCE_IDENTIFIED`.** Registry: 000458 `TERMINATED_NO_REEXTRACTION`; 000574 `REJECTED_FOR_FROZEN_THREE_STAGE_CHAIN`; 24 h mPFC calcium–EEG `BLOCKED`; IBL widefield+Neuropixels `INCONCLUSIVE_DO_NOT_EXTRACT`; BraiDyn-BC `REJECTED`; Allen Visual Behavior Neuropixels `REJECTED` (no macro). Not an outcome analysis.

| Tag | Value |
|---|---|
| Layer | `measurement_contract` |
| Evidence class | `internal_validated` (catalogue gate) |
| Flagship role | `supplement` |
| Claim ceiling | No audited public source currently clears every frozen three-stage-chain gate. |

---

## Claims table

| Object | Claim | Evidence class | Layer | Flagship role | Claim ceiling | Negative/limit |
|---|---|---|---|---|---|---|
| DANDI 000458 existence (simultaneous EEG + ephys, ES, wake/iso) | Public dandiset with those modalities | established_external | measurement_contract | terminology_only | Dataset identity only. | Not a coupling result |
| 000458 LFP-SD ↔ EEG-SD | Median subject r=0.406; both FDR nulls pass | internal_validated | state / epistemic | main_text_anchor | Conditional association under nominal alignment and frozen extraction. | Alignment INCONCLUSIVE; not MNPS; not operator |
| 000458 spike rate ↔ EEG spectral entropy | Median subject r=0.395; both FDR nulls pass | internal_validated | state / epistemic | main_text_anchor | Same ceiling as LFP pair. | Isoflurane-alone FAIL (r=0.043, q=0.161); E008 exploratory |
| 000458 extraction sensitivity / E009c speed | Both pairs survive 11 variants and four speed-adjusted tests | internal_validated | measurement_contract | supplement | Stability under declared variants, including running-speed mean/SD. | Does not validate alignment or exclude other drivers |
| 000458 E009b / E009d | Structured common-driver and prestimulus specificity | rejected as completed controls | measurement_contract | supplement | E009b INCONCLUSIVE (wrong-session n); E009d BLOCKED. | Do not treat incomplete controls as passed |
| 000458 EEG-only residual fraction | Median 0.856 (0.8557 archived); Jacobian/reachability out | rejected (Level 4) | local_dynamics / possible_futures | main_text_anchor | First-order EEG chart does not recover a local flow. | Association does not repair this |
| 000458 as NDT / MNPS / MNJ identity | Cross-scale contact = theory or manifold | rejected | epistemic | exclude | Forbidden. | MNPS ≠ NDT |
| E012 / exact replication manuscript | Independent replication of E008 contrast | not estimable | measurement_contract | supplement | No eligible public Tier-A source; not a negative replication. | Discovery association unchanged |
| D458_MMC three-stage chain | Local geometry → regional dynamics → EEG prediction | not estimable (blocked) | measurement_contract | supplement | Timing + regional-resolution gates fail; synthetic R² 0.072 is not biology. | Blocked ≠ uncoupled |
| TRN_C001 causal bridge | Timed TRN-opto changes meso and co-recorded surface EEG | not estimable | control / measurement_contract | exclude | Archives do not jointly contain the three links. | Do not pool; mixed F103 ≠ no TRN effect |
| Figshare F103 rebound (this repo) | Locked all-unit rebound latency Opto75−ES | internal_validated mixed | state | supplement | Δ=−0.32 ms, p=1.0, LOO unstable. | Not PRRG/SDSR/TA-E1; not macro |
| Figshare PRRG/SDSR/TA-E1 | (see summary 03) | — | — | **do not recode here** | Canonical in ndt-subsystems. | Double-count forbidden |
| 000574 primary pairs | Scalp EEG-std coupled to MTL LFP-std or spike rate | rejected (this design) | state | evidence_matrix | r=0.100 and 0.062 fail conjunctive nulls (n=9). | Not a 000458 replication; time-shift-only ≠ pass |
| 000574 as NDT mechanism | Human MTL test validates accessibility | speculative / unvalidated | epistemic | exclude | Even a future pass would be association-level. | Different species/task/chart |
| 000939 (m3-bridge folder) | Meso–macro or TRN analysis in this package | not estimable | measurement_contract | exclude | BLOCKED: no local data, no documented macro. | Do not overwrite 03 PRRG rows |
| 000248 Illusion | Illusory-contour geometry / meso–macro | incomplete | measurement_contract | exclude | Handover only. | Not qualia |
| Replacement audit E000 | Public replacement for D458_MMC | internal_validated (none qualify) | measurement_contract | supplement | No candidate clears all frozen gates. | Catalogue rejection ≠ biological null |

---

## Required negatives (do not rehabilitate)

- **Level-4 operator ID on the 000458 EEG chart remains FAIL** (residual 0.856). Do not let r≈0.4 “rescue” Jacobian, reachability, MNJ, or MNPS identity.
- **Alignment is INCONCLUSIVE**, not validated. Do not upgrade “trial-aligned” to sample-level coupling.
- **Isoflurane spike–entropy stratum FAIL** after the spectral-splice fix; do not cite the pre-fix “pass” (r=0.106).
- **E008 state contrast is exploratory**, not confirmatory, and has **no independent replication** (E012 not estimable — which is not a negative biological replication).
- **Three-stage chain is blocked**, not shown to be absent in nature. Do not write “the chain failed biologically.”
- **TRN → meso → macro is not estimable** from current archives. Do not pool DANDI 000458 with Figshare opto. Do not restore **TRN-as-variance-clamp**.
- **F103 mixed rebound is not “TRN has no effect.”** It is one locked processed-source endpoint. Do not use it to reopen or overwrite summary-03 PRRG/SDSR/TA-E1 closures.
- **000574 FAIL is design-specific** (scalp variance vs MTL LFP/spikes, n=9, conjunctive nulls). It does not falsify 000458 and does not license promoting the secondary iEEG pair (r=0.184).
- **000939 BLOCKED here ≠ 000939 PRRG result in ndt-subsystems.** Missing local files are not a HD-ring or TRN-VG finding.
- **000248 is incomplete.** Do not treat the Illusion handover as a result.
- **Replacement-audit rejections are availability gates**, not evidence that meso–macro coupling does not exist in other species or labs.

---

## Flagship placement

**Do not add a fourth main-text empirical anchor.** 000574, the chain package, TRN_C001, E012, and the replacement audit do **not** change the Anchor 3 pair (association + operator fail). They qualify it.

| sl_001 / article locus | What could enter | Exclude |
|---|---|---|
| **Anchor 3 / §13 cross-scale** | Cite **m3-bridge 000458** as the article of record: r=0.406 / 0.395 **and** residual 0.856. One clause: *conditional on nominal alignment (E002 INCONCLUSIVE).* | New human “anchor”; chain as if run; Figshare as EEG bridge |
| **Evidence matrix** | 000574 row: human Sternberg analog, **null** under this contract (state bounded/null; operator untested). Chain row: **not estimable**. TRN three-link: **not estimable**. | Shading 000574 as replication of 000458; TRN clamp restored |
| **Supplement / methods** | E012 method boundary; D458_MMC blocked contract; replacement-audit registry; F103 as pooling/endpoint discipline | E012 as “replication failed biologically” |
| **§10.3 Thalamic Access** | Point to summary 03 for PRRG/SDSR/TA-E1/TRN-VG/TA-E2. From this repo: only “joint TRN+EEG archive does not exist here.” | F103 as mechanism; 000939 audit as PRRG |
| **Figure 2 ladder** | Unchanged worked example: 000458 stops at (1); (4) fails. Optional footnote: 000574 also stops — it never clears (1) under the conjunctive rule. | Chain M4 R² 0.072 as empirical |
| **Exclude from flagship prose** | 000248; unfilled TRN `manuscript.typ`; Figshare `manuscript.typ` template; 000939 local “results”; secondary 000574 pairs | — |

**Anchor 3 numbers vs summary 03:** they **match**. Update citation source to m3-bridge and optionally print exact r=0.406 / 0.395 instead of ρ≈0.4. Do not treat the more precise values, the alignment caveat, or the isoflurane stratum fail as a new empirical pillar.
