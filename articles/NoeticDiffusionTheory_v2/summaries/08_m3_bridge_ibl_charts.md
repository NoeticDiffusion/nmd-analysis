# 08 — m3-bridge IBL / Repro-ephys chart-readout STOP cluster

**Source repo (read only):** `J:\repos\m3-bridge`  
**Article cluster:** IBL Brain-Wide Map (DANDI 000409) + IBL Reproducible Ephys Neuropixels charts  
**Date:** 2026-08-30  
**Status of sources:** `iblreach` and `repro_ephys` are preprint drafts (v0.3 / v0.1), not peer reviewed. `prior_dynamics`, `prior_side_dynamics`, `decision_geometry`, and `ibl2` are frozen STOP/boundary articles (v1.0).

These articles are **measurement-contract / chart-readout boundaries**. They do **not** validate NDT, MNPS identity, or thalamic access. STOP results constrain the **tested readout**, not the absence of all neural information.

---

## Architecture filter and tag schema

**Architecture filter (frozen):** State geometry → Local dynamical geometry → Geometry of possible futures → Control of accessibility.

**Recoverability ladder:** (1) association → (2) mechanism discrimination → (3) latent-order preservation → (4) dynamical-operator identification. Success at one level does not license a stronger claim. On this cluster, Level 1 is mostly **not established as condition-specific**; Level 4 **fails** under the tested discrete-flow / MNJ / chart-distance contracts.

**Tag schema:** Layer (`state` / `local_dynamics` / `possible_futures` / `control` / `epistemic` / `measurement_contract`) · Evidence class (`established_external` / `internal_validated` / `plausible` / `speculative` / `rejected`) · Flagship role (`main_text_anchor` / `evidence_matrix` / `supplement` / `exclude` / `terminology_only`) · Claim ceiling (one sentence).

**Do not import:** S5 NDT primers in `iblreach` and `repro_ephys` (they equate NDT with NMD and use an older rhythmic-control SDE). Role: `terminology_only`. Flagship theory is `sciencelead/sl_1.md` / `sl_001.md` plus summaries `01`–`05`, not those primers.

**Skipped backends** (no published-claim change found in their READMEs): `articles/iblreach2/` (IBL2 analysis backend; cited in place by `ibl2`); `articles/DANDI/ibl_000409_prior_reachability/` (stale “Phase E000” README; provenance for E030–E037 lives in `iblreach/README.md`); `articles/DANDI/ibl_repro_ephys/` (audit backend). Exception noted below: `E_RE008` / `E_RE009` qualify **reproducibility of Q4 BH-FDR**, not the Q1–Q4 scientific verdicts (`repro_ephys/README.md`).

`articles/order.md` is a Zenodo-status list, not a claim ledger. Verified against manuscripts, READMEs, and claim ledgers rather than copied: E037 is quality-gated **inconclusive** (not a validated BWM association); E034 is a real-`J_spectral_radius` **broad-group null in anatomically non-equivalent groups**, not an RSP replication; prior/decision/ibl2 are frozen STOP/boundary articles.

---

## Inventory

| Object | Path / identity | Frozen? | Notes |
|---|---|---|---|
| **iblreach** (draft v0.3, 2026-07-12) | `articles/iblreach/` — *Estimator quality and anatomical matching constrain cross cohort neural manifold flow inference* | Draft, not peer reviewed | Canonical `.typ` is the long title file, **not** stale `iblreach.typ` (v0.2). |
| E037 BWM association-cortex \(J_\mathrm{SR}\)–RT | Backend `DANDI/ibl_000409_prior_reachability/results/E037/` | Quality-gated | All-row \(\rho=-0.476\); **3/23** pass residual gate → correlation **not estimable**. |
| E034 Repro C9a/C9b | Backend `DANDI/ibl_repro_ephys/results/E034/` | Corrected real MNJ | \(n=47\) AC rows, 11 labs. **Not** an RSP test. |
| E030 / E031-A anatomy | Same BWM backend | Audit | Repro “association_cortex” is 60% VISa/VISam; **zero RSP** sessions. |
| **repro_ephys** (draft v0.1, 2026-06-26) | `articles/repro_ephys/` — *Region-specific neural manifold dynamics along a standardised visual-hippocampal-thalamic recording axis* | Draft | RepeatedSite: VISa → CA1/DG → LP. **Manuscript vs committed-CSV \(n\) mismatch** (see memo). |
| **prior_dynamics** (final v1.0, 2026-07-02) | `articles/prior_dynamics/` — *Behavioral Prior Adaptation Without Time-Matched Neural Prior-State Evidence* | Closed boundary | H1/H2 PASS; H3 downgraded; H4 not supported; H5 not run. |
| **prior_side_dynamics** (final v1.0, 2026-07-03) | `articles/prior_side_dynamics/` | Frozen STOP | Time-matched left vs right prior geometry. |
| **decision_geometry** (final v1.0, 2026-07-03) | `articles/decision_geometry/` | Frozen STOP | Stimulus-side geometry. |
| **ibl2** (final v1.0, 2026-07-04) | `articles/ibl2/` — *A Trial-to-Trial Discrete Chart-Transition Readout Does Not Clear Its Own Sensitivity Floor* | Frozen STOP | Canonical analysis in `iblreach2/`; IBL2-003 **not authorized**. |

**Denominators (do not mix):** BWM committed inventory **103** sessions (association cortex **23**). Repro neural cohort **85** sessions (12 labs; 1 access failure in inventory). Article 3 behavioral gate: **93** eligible sessions from a 110-session trial inventory — **not** 93 Neuropixels recordings. Chart-distance / IBL2 universe: **69** sessions.

---

## Executive take for flagship (≤15 lines)

This cluster is a **chart-readout ceiling**, not an NDT validation and not a biological null of prior, stimulus, or accessibility information.

On IBL Neuropixels, three nested contracts were tested and stopped: (i) session-level MNJ \(J_\mathrm{SR}\) vs behaviour, (ii) group-level 9D MNPS **centroid distance** on prior/stimulus labels, (iii) a **single-trial 3D discrete chart-transition** operator. None licensed geometry–behaviour coupling, prior-state geometry, or operator identification.

Two failures are **estimator/design gates**, not biology. E037’s BWM \(J_\mathrm{SR}\)–RT association is quality-limited (**3/23** residual-passing rows). Article 3’s strong-vs-neutral neural contrast is **structurally `NOT_TESTABLE`**: neutral trials occupy only the initial block (0/69 sessions overlap). E034’s Repro \(J_\mathrm{SR}\) null is a real-column test in a **non-equivalent** “association cortex” group (60% VISa/VISam; zero RSP) — it is **not** an RSP replication fail.

Where the design *is* time-matched (Articles 4–5) or the signal is independently shown to exist (IBL2-002A decoder **PASS**, median accuracy 0.588, \(+0.088\), \(p_\mathrm{perm}=0.0030\)), the NDT-facing readout still **STOP**s. That is recoverability Level 4: association/decoding ≠ mechanism ≠ latent-order ≠ operator ID.

**Flagship placement:** one compact **`evidence_matrix`** cell (required negative / measurement-contract), **not** a fourth empirical anchor. Do not put E037’s all-row \(\rho\) in any positive cell. Do not cite S5 primers as NDT theory.

---

## Per-article memos

### 1. iblreach — estimator quality and anatomical matching

**Question.** Does session-level discrete-transition \(J_\mathrm{SR}\) in BWM “association cortex” associate with session-median RT (C1), and can Repro Ephys port that claim (C9)?

**What passed.** Pipeline hygiene: E036 recovers all 23 BWM AC sessions via NWB metadata (not filenames). E030/E031-A make the anatomical mismatch explicit. Historical v2 NDT–behaviour correlations: **0 of ~90** survive BH-FDR (S3 falsification record). Circular \(m_{a,\mathrm{mean}}\) “prior” splits (E018/E018_A) are archived as K1-non-compliant.

**What did not.** E037 all-row Spearman \(\rho=-0.476\), \(p=0.0216\), \(p_\mathrm{perm}=0.0226\), \(n=23\); global sensitivity \(q=0.108\). Residual gate \(J_\mathrm{resid\_frac}<0.5\): **20/23 fail, 3 pass** → quality-filtered correlation **not estimable**. Manuscript classifies C1 as **inconclusive / MNJ-quality limited**, not a validated behavioural relation. E034 (real `J_spectral_radius`, \(n=47\), 11 labs): C9a \(r=+0.123\), \(p_\mathrm{one-sided}=0.794\); C9b \(r_\mathrm{partial}=-0.044\), \(p_\mathrm{perm}=0.452\). Neither registered criterion met. Repro AC is 60% VISa/VISam; BWM AC is primarily RSP/PTLp/AUD. E031-A: **zero RSP** sessions (RepeatedSite targets VISa/CA1/LP). The RSP \(J_\mathrm{SR}\)–RT hypothesis remains **open**.

**Recoverability.** Level 1 **not established** after quality gate. Level 4 not reached. Anatomical mismatch is a **cohort-eligibility** stop, distinct from E034’s numerical null.

**Claim ceiling.** Estimator residual quality and atlas-label matching are prerequisites for cross-cohort MNJ inference; this paper does not establish geometry–behaviour coupling or falsify an RSP hypothesis that Repro cannot host.

| Tag | Value |
|---|---|
| Layer | `measurement_contract` (also `epistemic`) |
| Evidence class | `internal_validated` (quality gate, anatomy audit, E034 null in **broad non-equivalent groups**); `rejected` (v2 FDR-inflated NDT–behaviour list; interpreting E034 as RSP replication) |
| Flagship role | `evidence_matrix` (methods constraint in the compact IBL cell) |
| Claim ceiling | Quality-gated MNJ and matched anatomy are required before \(J_\mathrm{SR}\)–RT inference; BWM AC association is inconclusive; Repro is ineligible for the RSP claim. |

---

### 2. repro_ephys — RepeatedSite region-specific MNJ / reachability

**Question (S1 frozen 2026-06-26).** Q1: cross-lab portability of \(J_\mathrm{SR}\) and `tube_effective_dim` (\(\mathrm{ICC}_\mathrm{lab}\le 0.20\)). Q2: VISa/VISam \(J_\mathrm{SR}\) vs RT (\(\rho>+0.25\), \(p<0.05\), \(n\ge 20\)). Q3: CA1 pre-stim `tube_effective_dim` strong > neutral (\(d>+0.30\), one-sided). Q4: exploratory thalamic contrast correlations.

**Provenance warning (do not paper over).** The manuscript/S3 ledger and the article-local committed reports **disagree on \(n\)**. README names `results/E_RE004`–`E_RE007` as canonical evidence. E_RE008: null **verdicts** look genuine, but seed inconsistency and a Q4 BH-FDR script gap existed; E_RE009 reconstructs the five BH values from the committed permutation table and **does not change** the exploratory-null conclusion. Flagship should cite **verdicts**, not a single \(n\).

| Endpoint | Manuscript / S3 | Article-local report | Shared verdict |
|---|---|---|---|
| Q2 VISa \(J_\mathrm{SR}\)–RT | \(n=13\), \(\rho=+0.272\), \(p_\mathrm{perm}=0.292\) | E_RE005: \(n=6\), **NOT_TESTABLE** (\(n<10\)) | Not primary; exploratory/null or not testable |
| Q3 CA1 \(\Delta\)tube | \(n=30\), \(d=+0.099\), \(p=0.371\) | E_RE006B: \(n=31\), \(d=+0.120\), \(p=0.356\) | **NOT_SUPPORTED** (primary) |
| Q4 thalamus | \(n=24\), 10 labs; RT covariate \(p_\mathrm{BH}=0.12\) | E_RE007 report: \(n=14\), 7 labs; E_RE009 BH from manuscript-scale table | **EXPLORATORY_NULL** |

**Q1 (manuscript S3).** Hippocampus \(J_\mathrm{SR}\) / `tube_eff_dim`: \(\mathrm{ICC}=0.000\), \(n=44\), 12 labs (portable). Broad AC `tube_eff_dim`: \(\mathrm{ICC}=0.533\), \(p=0.015\) (lab-dependent), resolving to 0.194 after VISa/VISam purity filter (underpowered). E_RE004 quality-gated table is stricter (VISa filtered \(J_\mathrm{SR}\) \(n=6\), **NOT_TESTABLE**). Do **not** write “the measurement layer is validated.” Write: **some** session-level MNJ/reachability summaries show low lab ICC in hippocampus when \(n\) is adequate; VISa Q2 eligibility is quality-limited.

**Q3 limitation (both sources).** Fixed session-level \(d_n\) (inter-region dispersion) shared across prior conditions. \(\Delta\)tube is CA1-internal geometry, not a fully condition-specific multi-region cone.

**Median MNJ residual (manuscript):** Repro 0.25 vs BWM AC 0.55 — **descriptive**, not a biological claim that RepeatedSite dynamics are more linear.

**Claim ceiling.** On this standardised trajectory, pre-specified VISa \(J_\mathrm{SR}\)–RT and CA1 prior-conditioned tube hypotheses are not supported at primary level; that is a **readout/endpoint null**, not “CA1 does not encode priors.”

| Tag | Value |
|---|---|
| Layer | `measurement_contract`; attempted `local_dynamics` / `possible_futures` (tube) |
| Evidence class | `internal_validated` (Q3 NOT_SUPPORTED; Q2 not primary); `plausible` (hippocampus ICC portability at manuscript \(n\)); `rejected` (session-average tube as prior proxy — refused in S3) |
| Flagship role | `supplement` inside the IBL matrix cell (do not expand Q1 into a positive NDT result) |
| Claim ceiling | RepeatedSite MNJ/tube endpoints did not support the registered behaviour/prior hypotheses; portability is anatomy- and \(n\)-dependent. |

---

### 3. prior_dynamics — behavioural prior without time-matched neural prior-state

**Gates.** H1 behavioural adaptation **CONFIRMED**: 93 sessions, 12 labs, median choice bias \(+0.48\), \(p_\mathrm{perm}=0.0001\), 100% sessions positive. H2 conditioned 9D features **CONFIRMED** (VISa/VISam \(n=36\), CA1 \(n=30\), thalamus coverage). H3 A3-003 apparent separability (VISa \(q=0.0009\), CA1 \(q=0.0092\)) **fails** A3-006A time-shift and firing-rate residualization (both regions STOP) and is **structurally `NOT_TESTABLE`** (A3-006B: 0/69 overlap; median gap 1 trial). H4 VISa \(\Delta=-0.030\), \(p=0.6455\), LOLO 0% — **NOT SUPPORTED**. H5 **not run**.

**This is not a neural null of prior information.** It is a **design confound**: condition \(\equiv\) trial index. Naive label-shuffle nulls do not protect against session drift.

**Claim ceiling.** Animals track block priors in behaviour; a time-matched strong-vs-neutral **neural** contrast cannot be built in this task structure under the tested chart.

| Tag | Value |
|---|---|
| Layer | `measurement_contract` (neural arm); H1 is behaviour, not NDT |
| Evidence class | `internal_validated` (H1; NOT_TESTABLE design); `rejected` (H3 as prior-state-specific; NDT/MNPS biological validation) |
| Flagship role | `evidence_matrix` (design-eligibility negative) |
| Claim ceiling | Behavioural prior adaptation is real; time-matched strong-vs-neutral chart geometry is not estimable here. |

---

### 4. prior_side_dynamics — time-matched left vs right prior (STOP)

**A4-000 PASS:** 69/69 sessions; median nearest-neighbour 13–15 trials; median 5 left / 5 right blocks. Structurally unlike Article 3.

**A4-001 STOP** (no region BH-FDR \(q<0.05\)): VISa/VISam median \(\Delta_\mathrm{PSI}=+0.015\), \(p_\mathrm{perm}=0.177\), \(q=0.324\); CA1 \(+0.037\), \(q=0.324\); thalamus \(-0.017\), \(q=0.642\) (LOLO 0% positive). Time-local adjacent-block null. VISa/thalamus fail time-shift control; CA1 fails choice-stratification — **not needed** for STOP (primary already non-significant).

**Claim ceiling.** Under the frozen 9D group-centroid chart-distance at `pre_stim`, time-matched prior-side geometry is not detected. **Rejected:** “these regions lack prior-side information”; “validates NDT/MNPS.”

| Tag | Value |
|---|---|
| Layer | `measurement_contract` / attempted `state` (centroid distance, not flow) |
| Evidence class | `internal_validated` (STOP); `rejected` (biological absence; mechanism) |
| Flagship role | `supplement` (STOP row under the IBL cell) |
| Claim ceiling | This chart-distance pipeline does not detect left-vs-right prior geometry in the registered regions/epoch. |

---

### 5. decision_geometry — stimulus-side geometry (STOP)

**A5-000 PASS:** 69/69; median nearest-neighbour **1–2 trials**; mean minority fraction \(\approx 0.41\). Cleanest exogenous contrast in the line.

**A5-001 STOP:** VISa/VISam \(\Delta=+0.014\), \(p=0.397\) (36 sessions / 11 labs); CA1 \(-0.016\), \(p=0.828\); thalamus \(-0.082\), \(p=0.973\). Movement-censored sensitivity also non-significant (\(p=0.161\), \(0.129\), \(0.992\)). Median 28.5% of VISa trials have movement onset before `stim_early` (0–150 ms) closes; session median RT \(\approx 158\) ms. Manuscript states single-unit/decoding literature **does** report stimulus-side coding in this dataset with **other** analyses.

**Claim ceiling.** Group-level 9D centroid distance at `stim_early` is **insensitive** to stimulus side here. **Rejected:** “VISa lacks stimulus information.”

| Tag | Value |
|---|---|
| Layer | `measurement_contract` / attempted `state` |
| Evidence class | `internal_validated` (STOP); `rejected` (absence of stimulus coding) |
| Flagship role | `supplement` |
| Claim ceiling | The tested `stim_early` chart-distance summary does not separate stimulus side; that is a readout floor, not a sensory-null. |

---

### 6. ibl2 — discrete chart-transition sensitivity floor

**Hierarchy as implemented.** Articles 3–5 tested **positional** 9D centroids (chart layer). IBL2 asked whether a **discrete** trial-to-trial operator \(x_{t+1}=A_c x_t+b_c+\varepsilon_t\) on a **new** per-trial 3D chart (magnitude / displacement / entropy of the pre-stim population vector) is estimable **before** any prior-side test. Continuous-time Jacobian was **not** the contract.

**IBL2-001 STOP (full scale, 69 sessions):** qualifying sessions VISa/VISam **4/36** (4 labs), CA1 **0/31**, thalamus **1/54**. Binding failure: held-out fit (median \(\mathrm{cv\_resid\_frac}=1.001\), threshold \(<0.5\)). Conditioning, \(\rho(A)<1\), bootstrap: not binding.

**IBL2-002A PASS (pilot, 15 sessions):** raw-population stimulus-side decoder in VISa/VISam, median accuracy **0.588** (\(+0.088\), \(p_\mathrm{perm}=0.0030\)). Positive-control anchor, **not** a prior-side inference.

**IBL2-002B STOP / no metric selected:** none of five frozen flow-geometry metrics met the selection rule (three wrong direction, 0% LOLO).

**IBL2-003 not authorized.** Relaxing failed gates is not an allowed path.

**This is the cluster’s cleanest recoverability sentence:** the information exists (decoder); this discrete-flow readout does not recover it. Parallel to DANDI 000458 Level-4 operator failure, on a different chart and species/scale.

**Claim ceiling.** One single-trial discrete affine transition model fails its own estimability floor in this cohort; that does not imply IBL Repro lacks dynamics or that all flow/reachability estimators fail.

| Tag | Value |
|---|---|
| Layer | `measurement_contract`; attempted `local_dynamics` / `possible_futures` (discrete \(A_c\), \(h=1\)) |
| Evidence class | `internal_validated` (001 STOP, 002A PASS, 002B no-selection); `rejected` (operator ID; biological null; authorizing 003) |
| Flagship role | `evidence_matrix` (primary exhibit inside the IBL cell) |
| Claim ceiling | Label-blind discrete chart-transition estimability fails on model fit; a raw decoder still reads stimulus side in a pilot. |

---

## Claims table

| Object | Claim | Evidence class | Layer | Flagship role | Claim ceiling | Negative / limit |
|---|---|---|---|---|---|---|
| E037 all-row \(J_\mathrm{SR}\)–RT | Apparent AC association | `rejected` as validated inference | `local_dynamics` (attempted) | `exclude` from positives | Descriptive all-row \(\rho=-0.476\), \(n=23\), \(q=0.108\) | **3/23** residual-pass; quality-filtered **not estimable** |
| E037 residual gate | MNJ quality is a hard stop | `internal_validated` | `measurement_contract` | `evidence_matrix` | Residual ratio must be gated before behavioural MNJ claims | Gate \(\neq\) proof that no coupling exists in RSP |
| E034 C9a/C9b | Repro AC \(J_\mathrm{SR}\) vs RT | `internal_validated` null in **broad groups** | `measurement_contract` | `evidence_matrix` | Real `J_spectral_radius`; criteria not met | **Not** RSP; groups anatomically non-equivalent |
| E030 / E031-A | Repro ineligible for BWM RSP claim | `internal_validated` | `measurement_contract` | `evidence_matrix` | 60% VISa/VISam; 0 RSP sessions | Does not falsify RSP \(J_\mathrm{SR}\)–RT |
| v2 BWM NDT–behaviour list | FDR-surviving correlations | `rejected` | `epistemic` | `exclude` | 0/~90 at \(q<0.05\) | Do not rehabilitate v2 \(r\) values |
| Circular \(m_a\) prior (E018) | Exogenous prior modulation | `rejected` | `epistemic` | `exclude` | K1-non-compliant | Needs trial-level `probability_left` |
| Repro Q1 ICC | Chart metrics portable across labs | `plausible` (hippocampus); underpowered (VISa) | `measurement_contract` | `supplement` | Low lab ICC where \(n\) adequate in S3 | Manuscript \(n\) \(\neq\) E_RE004 quality-gated \(n\) |
| Repro Q2 | VISa \(J_\mathrm{SR}\) predicts RT | `rejected` as primary | `local_dynamics` | `supplement` | Direction \(+\) but \(n\) below primary | Quality-passing coverage bottleneck |
| Repro Q3 | Strong prior widens CA1 tube | `rejected` as supported | `possible_futures` (attempted) | `supplement` | \(d\sim 0.10\), \(p\sim 0.36\), **NOT_SUPPORTED** | Fixed \(d_n\); not “CA1 has no prior” |
| Repro Q4 | Thalamic MNJ vs contrast | `rejected` as positive | `local_dynamics` | `supplement` | Exploratory null after BH | Informational RT \(\rho\) does not survive FDR; \(n\) mismatch |
| A3-001 H1 | Behavioural prior adaptation | `internal_validated` | (behaviour, not NDT layer) | `supplement` (context only) | Bias \(+0.48\), 93 sessions | Not a neural geometry result; \(\neq\) 85 ephys sessions |
| A3-003 H3 as prior-state | Pre-stim chart separates prior | `rejected` as specific | `state` | `exclude` | Apparent \(q<0.01\) fails controls | Time/activity confound |
| A3-006B | Strong vs neutral time-matchable | `internal_validated` **NOT_TESTABLE** | `measurement_contract` | `evidence_matrix` | 0/69 overlap | Dataset design, not analysis rescue |
| A3 H4 / H5 | Adaptation / neural–behaviour coupling | H4 `rejected`; H5 not run | `state` | `exclude` | No growth signal; H5 unauthorized | Do not imply coupling was tested and failed |
| A4-001 | Left vs right prior chart-distance | `internal_validated` STOP | `state` | `supplement` | No region \(q<0.05\) | Constrains this pipeline only |
| A5-001 | Stimulus-side chart-distance | `internal_validated` STOP | `state` | `supplement` | No region; censored also ns | Decoder literature says signal exists under other readouts |
| IBL2-001 | Discrete \(A_c\) estimable | `internal_validated` STOP | `local_dynamics` | `evidence_matrix` | 4/36, 0/31, 1/54; \(\mathrm{cv\_resid}=1.001\) | Fit failure, not sample-size/conditioning |
| IBL2-002A | Stimulus side in raw population | `internal_validated` PASS (pilot) | `state` (decoder, not MNPS) | `evidence_matrix` | Acc. 0.588, \(p=0.0030\) | Pilot 15/69; not prior-side; not MNJ |
| IBL2-002B | Flow metrics detect that contrast | `internal_validated` STOP | `local_dynamics` | `evidence_matrix` | No metric selected | Five frozen candidates only |
| IBL2-003 | Prior-side flow test | `rejected` (not authorized) | — | `exclude` | Not run | New dated addendum required |
| S5 primers (iblreach, repro) | NDT = NMD chart pipeline | `speculative` / outdated | `terminology_only` | `terminology_only` | Do not import equations | Flagship uses sl_001 + summary `05` |
| Whole cluster as NDT validation | IBL confirms MNPS/MNJ/reachability | `rejected` | — | `exclude` | No Level-4 recovery | STOP ≠ absence of neural information |
| Whole cluster as 4th anchor | IBL as empirical pillar beside spindles/coma/000458 | `rejected` | — | `exclude` | Methods ceiling only | Compact matrix cell at most |

---

## Required negatives / STOP results

Do not rehabilitate:

1. **E037 quality-filtered \(J_\mathrm{SR}\)–RT** — inconclusive, not a flagship association. All-row \(\rho\) is not a result.
2. **E034 as RSP replication** — real-column null in the **wrong tissue mix**. RSP hypothesis remains open.
3. **v2 BWM significant NDT–behaviour correlations** — 0/~90 FDR survivors.
4. **Circular \(m_a\) prior contrasts** — not exogenous prior tests.
5. **Article 3 H3 as prior-state geometry** — failed specificity; contrast **NOT_TESTABLE**.
6. **A4-001 / A5-001 as “no prior / no stimulus in VISa–CA1–thalamus”** — readout STOP only.
7. **IBL2-001 as “no neural dynamics”** — decoder PASS on the same cohort (pilot).
8. **IBL2-003** — not run; not a hidden negative of prior-side flow.
9. **Repro Q3 as “CA1 does not encode priors”** — `tube_effective_dim` with fixed \(d_n\) only.
10. **S5 primers as NDT v2 theory** — NMD/NDT conflation; old SDE.
11. **Thalamic access / MNPS identity / latent \(X_t\)** — never tested at recoverability levels 2–4.

Distinguish **estimator-quality / eligibility gates** (E037 residual \(n=3\); E031-A zero RSP; Q2 \(n\) below primary; A3-006B NOT_TESTABLE; IBL2-001 \(\mathrm{cv\_resid}\)) from **numerical nulls under a feasible design** (E034 broad AC; Q3; A4-001; A5-001; IBL2-002B). Both constrain the **contract**; only the second class is a completed hypothesis test, and even then only of that contract.

---

## Flagship placement

**Cluster role: `evidence_matrix` — one cell, not six papers and not a fourth empirical anchor.**

Main-text empirical anchors stay: (1) spindles, (2) coma, (3) DANDI 000458 meso→macro. This IBL line does not join them. It does not add a new layer of accessibility geometry; it shows that **several NDT-facing chart estimators failed their own gates or registered tests** on public IBL Neuropixels.

**Why `evidence_matrix` rather than `exclude`:** the IBL2 decoder-vs-flow dissociation is the rodent-ephys analogue of 000458’s Level-1 vs Level-4 split: **signal can be present while the local-linear / discrete-flow operator is not recoverable.** Estimator-quality and anatomical-matching gates belong in the same cell as required discipline (parallel to “do not treat MNPS as NDT”).

**Why not `main_text_anchor`:** no control-of-accessibility result; no identified Jacobian of latent \(X_t\); no thalamic mechanism; drafts (`iblreach`, `repro_ephys`) still carry manuscript/CSV \(n\) tension.

**Suggested Figure 5 cell (one row):**

> **IBL Repro/BWM chart-readout STOP.** Quality-gated MNJ and atlas matching are prerequisites (E037 3/23; Repro \(\neq\) RSP). Time-matched 9D centroid distance: STOP on prior-side and stimulus-side. Discrete trial-to-trial \(A_c\): STOP on estimability; raw decoder PASS (pilot). Ceiling: tested readout, not absent information. Recoverability: Level 4 not reached.

**Citation hygiene.** Prefer frozen v1.0 STOP articles (`prior_dynamics`, `prior_side_dynamics`, `decision_geometry`, `ibl2`) plus `iblreach` methods conclusions. Treat `repro_ephys` Q1 “portability confirmed” as **over-strong** relative to quality-gated E_RE004. Do not cite `order.md` as science.

**Optional `supplement`:** S1 contracts, denominators (93 vs 85 vs 69), movement-leakage diagnostic, \(d_n\) limitation, E_RE008/009 reproducibility notes.

---

## Unified lesson (for parent synthesis)

NDT v2 may use this cluster only as a **measurement-contract negative**: IBL Neuropixels did not recover MNJ / reachability / chart-distance / discrete-flow operators that license geometry–behaviour or prior-state claims. The theory is not tested by these STOPs, and biology is not falsified by them. If a single IBL fact enters the evidence matrix, it is IBL2’s dissociation (information present; this flow readout fails), bundled with the eligibility gates (residual quality, anatomical matching, time-matchability)—never E037’s ungated \(\rho\), never “Repro replicated RSP,” never “thalamus/MNPS validated.”
