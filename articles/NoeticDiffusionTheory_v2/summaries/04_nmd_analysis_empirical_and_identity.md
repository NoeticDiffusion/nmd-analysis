# 04 — nmd-analysis: old identity, spindles, coma, evidence matrix

Internal cartography for NDT 1.0 (flagship rebuild). Not manuscript prose.
Architecture freeze: `sciencelead/sl_1.md`, `sciencelead/sl_001.md`.
Tags: **Layer** = `state` / `local_dynamics` / `possible_futures` / `control` / `epistemic` / `measurement_contract`.
**Evidence class** = `established_external` / `internal_validated` / `plausible` / `speculative` / `rejected`.
**Flagship role** = `main_text_anchor` / `evidence_matrix` / `supplement` / `exclude` / `terminology_only`.

---

## Inventory

| Source | What it is | Status in this repo | Flagship use |
| --- | --- | --- | --- |
| `articles/NDT/NoeticDiffusionTheory.typ` (+ `.txt`) | NDT 0.8 identity donor. Title: *Noetic Diffusion Theory: A Rhythmic, Geometric Framework for Neural State Reconstruction and Conscious Correlates*. Zenodo 10.5281/zenodo.20112950. | Complete Typst (~1710 lines). | Theory identity: MNDM, RVC, landscape, sleep curriculum, phenomenology, research programme. |
| `articles/NDT_2/ndt_2.typ` (+ `.txt`, `sciencelead/ndt_lack.md`) | Meso-to-macro epistemic donor. Title: *Noetic Diffusion Theory: A Meso-to-Macro Geometry of Neural State Reconstruction*. | Complete. | Ladder, scale separation, DANDI-cited bridge, metabolic slow, TRN ansatz. |
| `articles/NeuralManifoldDynamics/…Measurement Contract….typ` | NMD v2.4 methods paper. | Present here; canonical contract also lives in the NMD repo (`summaries/05_…`). | Split: NDT owns theory; NMD owns versioned charts/exports. |
| `articles/RVC_SLEEP/` | *Rhythmic Variance Control at Sleep Spindles: A Three-Dataset Replication…* | Frozen Pass A/B/C (2026-07-03). ANPHY N=27, BOAS/ds005555 N=128, RichSleep N=24. | **Anchor 1.** |
| `articles/RVC_SLEEP_peak_analysis/` | *Sleep Spindles Phase-Lock to Respiration at Their Amplitude Peak, Not Onset…* | RichSleep full catalog (23,029 spindles). | Anchor-1 companion: EAP *timing*, not RVC causal proof. |
| `articles/Rythmic_Variance_Control_in_Sleep_theory/` | Intended theory article. | Empty template; useful notes in `plan/02_response.md`. | Do not cite as a result. |
| `articles/CLINICAL/comatose_ndt/` | *Recovery-Linked Neural Geometry After Cardiac-Arrest Coma*. I-CARE PhysioNet 2.1. | Primary: 301 analyzable / 281 CPC 1 vs 5; 5322 H5 runs. | **Anchor 2.** |
| Coma siblings | `comatose_ndt_12_24`, `_regional`, `_angles`, `_first12h_phase_shift`, `comatose_block_jacobian`, `comatose_geometric_trajectory`, `comatose_laguerre`, `comatose_experimental` (TAC). | Mixed: one late-window pilot with numbers; several shells/interim. | Matrix / supplement only. None upgrades the 0–12 h pooled anchor. |
| Clinical / task / development / EAP / metabolic | See evidence matrix below. | Heterogeneous maturity. | **One matrix, not a catalogue.** |
| `articles/NoeticDiffusionTheory_v2/` | Flagship scaffold. | Empty template (`manuscript.typ` is placeholder). | Do not treat as a result. |
| `project/extensions_ndt/1.md` | Terminology freeze. | Drop **MNJ-vNext**. Jacobian is the object; α/ω/Δ_react are summaries; MNJ = Jacobian *on an MNPS chart*. | Enforce in flagship vocabulary. |
| `project/diary/` | Session diary. | **Not present** in this repo snapshot (RVC_SLEEP still cites `229_…md`). | No article-status change found here. |
| DANDI 000458 | Meso→macro empirical analysis. | **Lives in ndt-subsystems** (`summaries/03_…`). nmd-analysis side: NMD ingest configs (`config_ingest_dandi_000458.yaml`) + ndt_2 citation of ρ≈0.4 associations and residual fraction 0.856. | **Anchor 3** is not owned by this summary; note the ingest/citation surface only. |

Missing as named folders: `eeg_meg_depression` does not exist. Closest clinical depression line is `CLINICAL/depression*` (ds003478 / ds003474). `psychosis_first_time_local_dynamics/` is an empty template.

---

## Executive take for flagship (≤15 lines)

NDT 0.8 still owns the *identity*: rhythmic reconstruction, MNDM, RVC, landscape F, sleep as two-timescale curriculum, phenomenology as Tier-2, and an explicit staged research programme. Its centre of gravity is obsolete: MNPS location + scalar-σ denoising, with Jacobian/reachability demoted to appendices. ndt_2 owns the *epistemic architecture*: latent X vs chart x, four-level recoverability ladder, meso→macro as a constrained bridge (not the ontology of NDT), TRN as phenomenological ansatz, metabolic adequacy as a slow feasibility boundary. The nmd-analysis empirical corpus does **not** validate the old denoising story and does **not** license a consciousness scalar. What it actually constrains is the new centre: **accessibility geometry**. Spindles (Anchor 1) show replicable event-locked 9D *state* reconfiguration (`d_n` timing), not causal variance-clamping or memory writing; matched-control specificity is baseline-contaminated. Coma (Anchor 2) is the strongest demonstration that “where you are” is insufficient: short-horizon reachability and local Jacobian deformation separate CPC 1 vs 5, and geometry adds a bounded increment beyond a restricted clinical+qEEG model. The rest of the corpus is a **structured-dissociation matrix**: depression moves reachability/9D Jacobian more than 3D location; FEP moves different layers by medication stratum; gambling vs cognitive control moves MNJ with MNPS null; hypoglycemia moves 3D/9D state without confirmatory reachability collapse; infant age moves chart coordinates (and classical qEEG) without FDR-supported local-flow change. NMD is the implementation contract, not the theory. RVC survives as the *minimal special case* of accessibility control. EAP is Tier-2 contextual conditioning. Metabolic is speculative feasibility. Demote Noetic Atlas and NDHI. Promote J, α/ω/Δ_react, diffusion tensor, reachability, committor (conceptual), FAR, attractors (carefully). Drop MNJ-vNext.

---

## Identity harvest from NoeticDiffusionTheory.typ

**Working title / claim of 0.8.** Conscious-state correlates as time-resolved denoising on a learned geometric manifold; MNDM as guided SDE with rhythmic variance schedule; RVC linking that schedule to measurable rhythms; MNPS as canonical Stage-1 chart.

**Minimal MNDM (preserve, then generalize).**

```text
dX_t = −∇F(X_t, t) dt + σ(t) dW_t
F_min = e − m
σ(t) = σ_min + σ_0 (1 − r(t))
```

**Extended MNDM (preserve as special structured component, not the general law).** Adaptive geometry G_t, time-varying landscape weights, meta-field Φ. Sciencelead requires replacing pure gradient flow with

```text
dX_t = b(X_t, t; c_t) dt + Σ(X_t, t; c_t) dW_t
b = −G ∇Φ + u_nc
```

Potential descent remains the conservative piece; rotation, non-normality, transient amplification, and asymmetric access live in `u_nc` and in `a = ΣΣ⊤`.

### Preserve

| Element | Why | New status |
| --- | --- | --- |
| MNDM as named dynamical core | Identity; still the right acronym | KEEP, generalize beyond gradient flow |
| RVC | Distinctive, falsifiable temporal claim | KEEP as **minimal** `r(t) → Σ(t)` special case of accessibility control |
| MNPS 3D `(m, d, e)` | Canonical observation chart | KEEP as chart, not as theory |
| Stratified 9D | Resolution layer that actually carries several clinical effects | KEEP as measurement resolution |
| Sleep as two-timescale curriculum (NREM centralize / REM expand; overnight amplitude decay) | Identity + still-open prediction | KEEP as **prediction**, not as demonstrated result of the sleep papers here |
| Phenomenology as Tier-2 | 0.8 already disciplined | KEEP: pulsed/clarity/presence not Stage-1 |
| Landscape learning / HELS as follow-on | 0.8 correctly calls this a gap | KEEP as history module; not evidence |
| Research programme: signature predictions, null models, falsifiers | Makes the paper a programme, not a manifesto | KEEP; rewrite around accessibility, not entropy-drop-as-denoising |
| Grand Mal / hypersynchrony warning (`d(X)` term) | Distinguishes meaningful structure from hyper-ordered collapse | KEEP; ndt_2 metabolic analogue strengthens it |
| Constitutive-consciousness reading as optional metaphysics | 0.8 already says it adds no extra empirical predictions | KEEP **optional and labeled**; never in the abstract claim |

### Demote

| Element | Why |
| --- | --- |
| Noetic Atlas (Mapper, persistent homology, RQA, metastability indices as *theory*) | Toolbox readouts, not NDT objects. Optional S1 terminology. |
| NDHI (Noetic Diffusion Health Index) | Exploratory composite; 0.8 already forbids biomarker/consciousness-score use. Flagship should not name it in the main claim set. |
| MNPS location as the centre | Empirical corpus repeatedly shows 3D occupancy is the *weak* layer (depression, gambling, parts of FEP). |
| Scalar σ(t) as “the” diffusion | Promote diffusion *tensor* `a(x,t)`. |
| Jacobian / reachability as “appendices / second-order extensions” | 0.8 §Predictions still says this. Reverse it. |
| TRN = variance controller | 0.8 already cautious (Zenodo 21774408: bounded PV-linked MGB noise-dimensionality contraction only). Deepen as candidate **access-control** implementation. |
| Event-locked entropy drop as proof of denoising | Signature Prediction 1 remains a *prediction*; spindle papers measure 9D chart reconfiguration, not entropy-as-denoising. |
| Clinical signatures as theory-defining | Bounded, dataset-specific; matrix only. |

### Rewrite

| 0.8 formulation | NDT 1.0 rewrite |
| --- | --- |
| rhythmic variance control → denoising on a potential → MNPS geometry | state-dependent control → structured stochastic dynamics → geometry of accessible neural futures |
| NDT = MNPS → MNJ → reachability | MNPS is one observation chart through which some NDT quantities can be estimated |
| Stage-1 = entropy + topology + NDHI | Stage-1 = state chart + local law (b, J, a) + short-horizon futures |
| TRN executes r(t) | thalamic/TRN circuitry is a *candidate* biological implementation of access control |
| Signature P1 “entropy drops after SO–spindle” as the flagship sleep result | Replace with the actual spindle result: peri-event 9D reconfiguration, timing-primary, specificity incomplete |
| Signature P4 illustrative Mapper/volume-collapse operationalizations | Already internally falsified as stated (FEP is medication-stratified m/path-cost; depression is reachability/9D rotation, not 3D volume). Use that *failure of the sketch* as an asset: structured dissociations. |

**0.8 predictions still usable after rewrite.** P1 event-locking (reframed); P3 sleep curriculum (still untested as topology/Mapper in this corpus); P5 anti-phase temporal-order distinguisher vs predictive-coding (still the best competitive test; unexecuted). P2 wake theta-phase encoding = Tier-2. Falsifiers 1–4 remain, but “smooth entropy” is no longer the sole RVC killer: the new killer is *no event-locked advantage after smooth/rhythm-free/power-matched nulls*.

---

## Epistemic harvest from ndt_2.typ

ndt_2 is the wrong *flagship* but the right *ruler*. Do not structure NDT 1.0 as “metabolism → meso → macro”. Put the ladder near the front as **Figure 2 / epistemic spine**.

### Four-level recoverability ladder (import verbatim in spirit)

1. **Association** — observable covaries with another measured/latent quantity.
2. **Mechanism discrimination** — observations separate alternatives with matched task outputs.
3. **Latent-order preservation** — measured ordering tracks a predefined latent summary.
4. **Dynamical-operator identification** — chart supports a nontrivial, response-generating local operator (Jacobian, diffusion, reachability). Requires residual-quality, local sampling, robustness.

Editorial rule (ndt_2 and sciencelead): **success at one level does not license a stronger claim at another.**

### Meso→macro (ndt_2’s actual empirical spine; Anchor 3 lives elsewhere)

- DANDI 000458 companion: LFP-variance-proxy–EEG-variance and spike-rate–EEG-spectral-entropy associations, median subject correlations **near 0.4**, surviving sign-flip and circular time-shift nulls. **Level 1 only.**
- Same analysis: median local-linear residual-variance fraction **0.856** on the EEG-only chart → Jacobian/reachability inference **rejected**. This negative is scientifically more important than the positive correlation.
- nmd-analysis contribution: NMD DANDI/NWB *ingest path* (measurement contract), not the association analysis. Flagship cites ndt-subsystems for the result and NMD for the chart implementation.

### Metabolic slow (keep as feasibility, speculative)

- `q_met = exp(−H_met)` is a proposed adequacy gate, **not** a consciousness score and **not** in the current measurement contract.
- Metabolic hypersynchrony paradox: low glucose can increase slow rhythmic power while complexity/cognition fall. Order ≠ successful reconstruction.
- Hypoglycemia EEG reanalysis in this repo (see EAP/metabolic section) is the only nmd-analysis constraint: 3D/9D *state* shift, reachability **not confirmatory**.

### TRN ansatz warning (keep and strengthen)

ndt_2 Eq. for σ(t) via `g_TRN` is explicitly a **phenomenological ansatz**. `g_TRN` and κ are not recovered from scalp EEG. Old NDT’s PV/SOM reanalysis did not validate a general single-unit variance gate. Sciencelead: weaken anatomical commitment, deepen computational concept (access control that *can* express as variance modulation).

### ndt_lack.md (use as gap list, not as extra theory)

Still missing: uniquely identifying prediction vs precision/arousal/power; validated X→chart recovery map; causal intervention on r(t); landscape-learning dynamics; perception–action loop. Flagship should *name* these as open, not paper over them with more metrics.

### Local-operator boundary (ndt_2 §MNPS)

Cone size ≠ occupancy, entropy, controllability, or consciousness. `Ĵ` and short-horizon reachability are conditional local estimators requiring Level 4. Import this sentence into the flagship methods/epistemic section.

---

## Anchor 1 — spindles

**Question for the flagship.** Do physiologically discrete rhythmic events coincide with local state-space reconfiguration?

**Not the question.** Do spindles prove RVC denoising, memory consolidation, TRN execution, or causal variance clamping?

### Primary paper — RVC_SLEEP

- **Title:** *Rhythmic Variance Control at Sleep Spindles: A Three-Dataset Replication of Timing-Locked State-Space Reconfiguration Without Embodied-Anchor Moderation*
- **Datasets:** ANPHY (HD-EEG, N=27), BOAS/ds005555 (N=128), RichSleep (N=24); total 179. YASA spindles, N2, C3-A2.
- **Chart:** NMD stratified 9D, frozen 9-endpoint family `m, d, e, d_n, d_l, d_s, e_e, e_s, e_m`.
- **Primary estimand (protocol amendment):** subject as biological unit; event vs *pre-spindle baseline* (timing, A2r) vs event vs matched non-spindle N2 (specificity, A1r).

**What moved.** **Layer: `state` (stratified 9D), especially `d_n` (network-integration deviation).** Not Jacobian, not reachability, not diffusion tensor.

| Contrast | Finding | Ceiling |
| --- | --- | --- |
| Timing A2r (event − pre_far) | `d_n` +0.106 (ANPHY q=0.009) and +0.165 (BOAS q=0.011); same sign. `e_s` supportive (BOAS q=0.011; ANPHY q=0.062 ns). | **Internal validated** peri-spindle *timing* rise in `d_n`. |
| Specificity A1r (event − matched control) | 8/9 endpoints same-sign FDR in ≥1 dataset, but decomposition shows **baseline (B) dominates** several endpoints (`m`, `d_s`). `d_n` A1r **sign conflict** across datasets, explained by opposite baseline B, not by timing A. | Specificity **incomplete**. Do not headline “spindle-specific mechanism.” |
| RichSleep timing | Underpowered (`d_n` q=0.72); event-vs-control `d_n` +0.29, q=0.0006 (different, less power-matched contrast). | Corroboration, not a third independent timing replication. |
| EAP moderation Pass C | 53/54 FDR-null; one ANPHY `d_l` exception fails subject-level sensitivity. RichSleep dual-arm composite also null. Phase-locking at *onset* null in the geometry-valid subsample. | **Rejected** as moderator of this effect under the primary composite. |
| Pass B surface injection | Only `e_m`/`e` move; 0/36 FDR-status flips. | Construction validity, **not** EAP evidence. |

**Claim ceiling (Anchor 1).** Discrete spindle events coincide with a replicable, within-event rise in stratified deviation coordinate `d_n`. This is chart-level state reconfiguration at a rhythm-defined micro-event. It is **not** causal denoising, **not** matched-control-pure specificity, **not** reachability change, **not** TRN identification.

**Known gaps (must travel with the result).** No sigma-power residualization in the frozen schema; BOAS sparse event counts (median 5); RichSleep timing underpowered; event-locking ≠ mechanism discrimination (Level 2).

### Companion — RVC_SLEEP_peak_analysis (do not merge into Anchor 1’s RVC claim)

- Full RichSleep catalog: onset phase-locking remains null even at 23,029 events; **peak** (not onset) respiratory coupling is robust (pooled R₁=0.045, p=0.0005; second-order R=0.665, p=7×10⁻⁶). Cardiac weaker/fragile.
- Geometry-moderation by preferred respiratory phase: 2/18 FDR survivors (`d_l`, `d`); framed as event-*timing*, not confirmed event-*efficacy*. Pending replication.

**Layer:** `control` (EAP timing pathway). **Role:** evidence-matrix / supplement next to EAP, not a second main-text empirical pillar.

### Theory folder

`Rythmic_Variance_Control_in_Sleep_theory/` is an empty template. `plan/02_response.md` usefully splits EAP into timing vs efficacy pathways — import the distinction, not the empty manuscript.

### Flagship placement

Main-text Anchor 1 + one panel: event-locked `d_n` timing across ANPHY/BOAS, with an explicit “specificity incomplete / not denoising” caveat box. Peak-phase and EAP nulls go to the evidence matrix / control section.

---

## Anchor 2 — coma

**Question for the flagship.** Does a clinically important state difference appear more clearly in accessible futures and local flow than in static state alone?

**Primary paper.** *Recovery-Linked Neural Geometry After Cardiac-Arrest Coma* (`articles/CLINICAL/comatose_ndt/`).

- **Dataset:** I-CARE PhysioNet 2.1, two independently processed non-overlapping roots, invalidity-fixed NMD exports. Pooled **301** analyzable patients, **281** in CPC 1 vs CPC 5 (141/140), **5322** H5 runs. Window: **0–12 h after EEG-anchor** (not ROSC clock).
- **Layers evaluated jointly:** MNPS 3D/9D spread; MNJ 3D and invalidity-corrected MNJ 9D; short-horizon reachability (`tube_d_eff`, `persistence_*`, `tube_capture_gate`).
- **Vocabulary caution** (`extensions_ndt/1.md`): the coma manuscript still uses spectral *radius* as “local expansion.” Flagship should prefer **spectral abscissa α** as signed modal growth where the estimator contract allows it; radius remains an unsigned magnitude summary.

**What moved.**

| Layer | Direction (better outcome CPC 1 vs poor CPC 5) | Strength |
| --- | --- | --- |
| `possible_futures` (reachability) | Broader / more persistent short-horizon geometry. All five prespecified metrics BH-FDR in pooled cohort. Lead: `persistence_hysteresis_log_det_median` d=−0.909; `persistence_log_det_median` d=0.896. `tube_d_eff_median` already significant in **0–1 h** (d=0.786, p=1.2×10⁻⁴) and positive across all 12 hourly bins. | **Internal validated** (pooled, two-cohort). Strongest flagship illustration of accessible futures. |
| `local_dynamics` (MNJ) | Directionally aligned (lower local expansion/deformation in CPC 1); **cohort-heterogeneous in magnitude**. | Internal, secondary to reachability. |
| `state` (MNPS spread) | Lower spread in better-outcome patients; restored as a *descriptive* anchor, not the lead. | Supports the hierarchy: location < deformation < reachable futures. |
| Between-run instability | Complementary axis in n=130 with ≥3 qualifying recordings. | Plausible additional futures/stability readout. |
| Incremental prediction | Geometry layer on `limited_clinical_only` baseline: AUROC 0.599 → **0.662**. | Bounded increment; **not** full multimodal prognostication. |

**Claim ceiling (Anchor 2).** Early post-arrest EEG contains recovery-linked *layered* geometry: reachable dimensionality and local deformation carry information that static severity/location does not exhaust. Interpret as **recovery-linked geometry**, not neural-viability assay (WLST, time-to-death, sedation unavailable). Not a consciousness meter. Circular-shift null does **not** support a precise “which hour is strongest” claim — only “detectable early.”

**Level-4 caveat.** These are empirical NMD-chart estimators, not truth-known operator identification. Residual-quality and perturbation-response were not the I-CARE design. Flagship must not promote coma reachability to “validated dynamical-operator recovery.” It is a **strong Level-1/descriptive-geometry constraint** that *motivates* Layer D, plus internal predictive increment.

### Sibling census (matrix only; none replaces the anchor)

| Folder | Title / content | Verdict |
| --- | --- | --- |
| `comatose_ndt_12_24` | *Recovery-Linked Neural Geometry 12–24 h Pilot…* Part1-only; true 12–24 h slice 97 subjects (47/50). Mixed-sign reachability trio FDR; `tube_d_eff` ns; Jacobian modest. | Does **not** upgrade the 0–12 h story. Shows the late window is not a copy of the early one (structured dissociation in time). Matrix row. |
| `comatose_ndt_regional` | *Regional Recovery-Linked Neural Geometry…* Channel-group reachability. | Manuscript shell; regional export not finalized. Exclude from main text. |
| `comatose_ndt_angles` | Empty template. | Exclude. |
| `comatose_ndt_first12h_phase_shift` | First-12 h phase-shift line. | Do not promote without a frozen result that beats the pooled reachability paper. |
| `comatose_block_jacobian` | *Block-Jacobian Coupling in Early Cardiac-Arrest Coma.* Part1 discovery: lower diagonal block Frobenius in CPC 1 (d=−0.326, p=4.13×10⁻⁴). Part2 pending. | Interim. Matrix as `local_dynamics` hypothesis, not anchor. |
| `comatose_geometric_trajectory`, `comatose_laguerre` | Trajectory / Laguerre variants. | Do not narrate. |
| `comatose_experimental` (TAC) | Incremental-validity / σ-Jacobian TAC result bundles exist; no article-facing Typst in the census. | Methods/supplement if cited at all. |
| `comatose_ndt/resusciation/` | *Early EEG dynamical features after cardiac arrest* (Resuscitation-format fork). | Same empirical object, different venue shell. Do not double-count. |

---

## Evidence matrix table

One table for everything that is **not** Anchor 1/2. Columns match sciencelead Figure 5 (state / local dynamics / diffusion / reachability / destination-FAR / mechanism), plus claim ceiling and Fig. 5 usability.

Legend for cells: **V** = internal validated (FDR/replication under a frozen contract); **B** = bounded / mixed / one-cohort; **N** = tested and null or validity-failed; **—** = not tested; **S** = speculative construct.

| Condition / paper | Dataset | State | Local dyn. | Diff. | Reach. | Dest./FAR | Mech. | Effect direction (if known) | Claim ceiling | Fig. 5? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Depression rest — *Resting-State Neural Geometry Across Depressive Symptom Burden* | ds003478, BDI, n≈121 | B (3D weak) | V 9D rotation d=0.569 | — | V tube log-eig-var d=−0.678; log-det d=0.735 | — | — | Higher BDI: reachability + 9D rotational power, **not** 3D volume collapse | Symptom-burden geometry on one young rest cohort; not MDD biomarker | **Yes** (depression row: reachability/J, 3D weak) |
| Depression task — *Depressive Symptom Geometry Across Rest and Probabilistic Selection* | ds003474+ds003478 paired | B | B block-Frobenius e→d d=−0.778 | — | V task tube log-eig-var d=−0.719 | — | — | Same ordering as rest; **task−rest delta broadly null** | Rest/task *state-level* signal; no robust BDI-dependent reconfiguration | Yes (null delta is the dissociation) |
| Depression events — *Event-First Reinforcement-Learning Geometry…* | ds003474 PST | V (task-native path/hysteresis) | — | — | — | — | — | Feedback correct vs incorrect geometry is real; **BDI does not modulate** those contrasts after FDR | Event geometry ≠ symptom geometry | Optional (shows layer split inside one cohort) |
| FEP static — *First-Episode Psychosis Geometry Across Two Resting-State EEG Cohorts* | ds003944, ds003947 | V medicated `m` d=0.881 (944); unmedicated trajectory `m_delta` d=−1.385 (947, n_unmed=8) | B block-MNJ exploratory | — | B 944 pooled capture-gate q≈0.06; 947 weak | — | — | **Medication-stratified double dissociation**, not one FEP signature. Original Mapper/DET sketch untested-as-stated | Bounded, cohort- and medication-dependent | **Yes** (psychosis row: layer shifts with medication) |
| FEP trajectory grammar — *Trajectory Grammar of First-Episode Psychosis…* | same | — | — (action/entropy-rate, not J) | — | — | — | — | Unmedicated elevated noetic_action (944, q=0.052, misses FDR); reverse of static paper | Exploratory complementary grammar; do not treat as validated | Optional |
| FEP angles / local_dynamics template | `psychosis_first_time_angles`, `psychosis_first_time_local_dynamics` | | | | | | | Empty or not article-ready | Exclude |
| AD/FTD rest — `AD_FTD_article.typ` | ds004504 | B | B block-MNJ d→d AD d=−0.526, FTD d=−0.623; FTD MMSE–9D spectral radius ρ=0.754 | — | — (export emphasized MNJ not reachability) | — | — | Dementia vs healthy on block coupling, not a universal scalar; AD vs FTD weak on selected surface | One-cohort local-coupling constraint | Yes (neurodegeneration: local dyn. > coarse state) |
| AD/FTD photic — *Evoked Neural Geometry Under Photic Stress…* | ds006036 + ds004504 rest ref | N rest `mdr` d=−0.080 | V AD vs HC 9D `mdr` at PHOTO 20 Hz d=−0.984 | — | — | — | S (photic as perturbation, not identified mechanism) | Evoked MNJ signal **specific to photic driving** | Frequency-specific evoked J, not rest biomarker | Yes if space; else supplement |
| AD/FTD ESB — *Evoked Structural Brittleness…* | same photic | — | B rotational_power in ESB-2 | — | B posterior `tube_d_eff` in ESB-2 | — | S composite | PHOTO 15 Hz ESB-2 AD d=0.821, FTD d=1.038 vs HC | Internally stabilized deviation score; **not** a resonance-loss theorem | No (construct too composite) |
| PD walking — *Walking-State Geometry Separates PD…* | ds007526, 144 ppts | V walk `d` family d≈0.71–0.77 vs HC | — | — | — | — | — | Disease-state (cohort-anchored walk) clearer than paired rest→walk reconfiguration | Between-subject `d`-family disease geometry | Optional |
| PD ON/OFF — *Shared-Reference Disease-State Geometry Exceeds Paired Pharmacology…* | ds003490, 25 pairs + 25 HC | V disease-state broad | V ON elevated 9D MDR vs HC | — | — | — | B (medication as weak paired effect) | Disease-state ≫ paired OFF vs ON | Pharmacology branch hypothesis-generating | Optional |
| Gambling vs CC — *Neural flow geometry differentiates gambling and cognitive control despite matched sympathetic arousal* | ds004511, N=45, 57,526 epochs | **N** Friedman p>0.23 | **V** GG vs CC Frobenius d=1.62, spectral radius d=1.81 | — | — | — | N EDA-matched (d=−0.07) | Local flow separates tasks that **do not** separate in MNPS; not arousal | Strongest clean *state vs local-dynamics* dissociation in the repo | **Yes** (even though not clinical) |
| EEG–MEG concordance | ds003645 FacePerception, 18 ppts | B feature-family dependent | — | — | — | — | — | Temporal concordance varies; EEG regional MNPS collapsed (export bug) | Measurement-contract audit, not a clinical effect | No (belongs in NMD/`05_`) |
| Infant Figshare — *Cohort-Anchored Infant EEG State-Space Geometry Tracks Age…* | Xiao et al. 2017, 22 infants | B/V half of 12 coords under conservative permutation | **N** MNJ/reachability FDR-null | — | **N** | — | — | Within-child chart age signal; classical qEEG stronger (β/α etc.) | Development moves **state chart** more than local flow here | Yes (development row: state without local dyn.) |
| APPLESEED — *Early Changes in Infant EEG State-Space Geometry* | ds003710, 13 infants | B exploratory `m` at 12 mo d_z=−1.51 | **N** primary 3D MNJ/reachability | — | **N** | — | — | Small-N; ICC imprecise; no primary dynamical endpoint | Reliability caution, not a developmental mechanism | Optional (same lesson, weaker) |
| Spindle peak-phase (companion) | RichSleep | — | — | — | — | — | B respiratory peak-lock | Peak-not-onset; geometry-moderation fragile | EAP *timing*, not RVC | Yes in EAP/control column |
| RichSleep EAP v2 | RichSleep SO/REM catalogs | — | — | — | — | — | V SO trough lock (R₁ 0.050–0.064); N REM-theta; onset nulls disagree; strength×geometry **N** | Carrier-specific autonomic locking; SO ≫ spindle peak ≫ REM theta | Body phase conditions *some* sleep events, not a general gate | **Yes** (EAP row: SO timing, spindle efficacy null) |
| Illusion-game EAP | ds004587 | N | N | — | — | — | N (after scale-bug fix) | Dataset cannot support rest or trial-level EAP | Negative + contract defect | No (or “not tested / invalid design”) |
| Hypoglycemia | Zenodo 3465213, T1D clamp, n=34 | V 3D `m` Δ=−0.743; 9D m_a, m_e, d_n, e_m | B Jacobian exported, not the lead | — | **N** split-half validity-limited | — | S metabolic gate | Slow-rhythm↑ / mobility↓ without confirmatory reachability collapse | Feasibility-boundary *constraint*, not identified q_met | **Yes** (metabolic: state without futures) |

**Matrix lesson (the actual theoretical yield).** NDT 1.0 should predict **which layer moves**, not a universal consciousness or “health” deformation. Depression: futures + local rotation, weak 3D. FEP: layer identity depends on medication. Gambling: local flow without location. Coma: futures lead. Spindles: stratified state at events, futures untested. Infants: chart age without local flow. Hypoglycemia: state without confirmatory futures. That heterogeneity is the flagship’s empirical signature, not a failure to find “the” NDT biomarker.

---

## EAP and metabolic (Tier-2 / feasibility)

### EAP = contextual conditioning of accessibility, not a consciousness coordinate

0.8 already placed EAP in Appendix / S3: self-prior F_self + rhythmic entrainment of r(t); companion evidence = bounded autonomic/MNPS co-modulation, not causal body→manifold gating.

**What this repo actually shows.**

1. **Spindle geometry is not moderated by pre-event HRV/respiratory anchor** (RVC_SLEEP Pass C, three datasets including RichSleep composite). **Rejected** for that specific efficacy hypothesis.
2. **Respiratory phase locks to spindle *peak*, not onset** (peak_analysis). Timing pathway, RichSleep-only, not a geometry mechanism.
3. **SO troughs lock more strongly than spindles; REM theta does not** (RichSLeep_EAP_v2). Carrier-specific. Three onset-null constructions disagree — report disagreement, do not shop the null.
4. **Intrinsic spindle strength does not moderate the peak-phase–geometry link** (18 interaction tests FDR-null).
5. **ds004587 illusion-game** cannot test the planned rest/trial EAP question; after correcting an NMD `anchor_index` scale defect (9 orders of magnitude), remaining associations are FDR-null.
6. **Gambling article:** exploratory respiratory–mobility association did **not** survive correction; EDA-matched MNJ effect shows local flow is *not* reducible to sympathetic arousal — useful as an EAP *negative control*, not as EAP support.

**Flagship role.** One subsection under “What changes what the system can do”: `c_t^{body} → contextual conditioning of accessibility`. Evidence class mix: internal validated *timing* (SO/spindle-peak), rejected *efficacy* for spindles, speculative causal gating. **Do not** put EAP in the core SDE required for NDT.

### Metabolic = slow feasibility boundary, speculative extension

ndt_2’s `q_met` equations stay in a short subsection / one figure panel.

**nmd-analysis constraint:** *hypoglycemia_metabolic_anchoring* — paired euglycemia vs hypoglycemia EEG, 34 T1D, NMD 3D/9D + Jacobian; exploratory reachability audited and **validity-limited**. Reproducible stratified MNPS condition shift (mobility down, slow power up) **without** FDR-supported reachability collapse. No continuous glucose, autonomic, interoceptive, recovery, or behavioural measurement in that study — it does **not** test an EAP metabolic gate.

**Claim ceiling.** Metabolic strain can move the *state chart* and can dissociate rhythmic order from functional capacity (hypersynchrony analogue). It does not identify q_met, does not show futures collapse, and is not a consciousness coordinate.

---

## Claims table

| Claim | Layer | Evidence class | Flagship role | Claim ceiling |
| --- | --- | --- | --- | --- |
| NDT’s scientifically relevant object is accessibility geometry (flow, diffusion, reachable futures, commitment, resilience), not MNPS location alone | `possible_futures` + `local_dynamics` | `plausible` (architecture); constrained by internal results | Core thesis | Motivated by dissociations; not a theorem |
| MNDM generalizes to `dX = b dt + Σ dW` with potential as a special component | `local_dynamics` | `speculative` (equation); potential form is 0.8 identity | Core maths | Formal proposal; not fitted to neural data |
| MNPS 3D/9D are operational charts, not the latent manifold | `measurement_contract` | `internal_validated` (NMD contract language) | § measurement | Always |
| NMD is a versioned implementation contract, not NDT | `measurement_contract` | `internal_validated` (NMD methods paper) | Ownership table | Always |
| RVC is the minimal accessibility-control case `r(t)→Σ(t)` | `control` | `plausible` | Biological control | Distinctive prediction; not shown to be the executor |
| Spindle events coincide with 9D `d_n` timing reconfiguration | `state` | `internal_validated` (ANPHY+BOAS timing) | **Anchor 1** | Event-locked chart change; ≠ denoising, ≠ specificity-pure |
| Matched-control spindle specificity is a single mechanism | `state` | `rejected` / incomplete | Caveat with Anchor 1 | Baseline-driven for several endpoints |
| Pre-event cardiorespiratory state moderates spindle geometry | `control` | `rejected` | EAP subsection | Null under primary composite |
| Early coma CPC 1 vs 5 separates on reachability (and aligned MNJ) | `possible_futures` / `local_dynamics` | `internal_validated` (pooled I-CARE) | **Anchor 2** | Recovery-linked geometry; not viability or consciousness |
| Geometry adds incremental outcome information beyond a restricted clinical+qEEG model | `possible_futures` | `internal_validated` (AUROC 0.599→0.662) | Anchor 2, bounded | Not full clinical prognostication |
| DANDI 000458: meso–macro association without operator recovery | `epistemic` | `internal_validated` (cited from ndt_2 / ndt-subsystems) | **Anchor 3** (other summary) | Level 1 only; residual 0.856 kills Level 4 |
| Depression burden deforms reachability/9D J more than 3D volume | `possible_futures` / `local_dynamics` | `internal_validated` (one cohort) | Evidence matrix | Not diagnostic; falsifies 0.8 volume-collapse sketch |
| FEP has one universal MNPS signature | `state` | `rejected` | Evidence matrix | Medication-stratified layer shift instead |
| Local Jacobian can separate tasks with matched MNPS and matched EDA | `local_dynamics` | `internal_validated` (ds004511) | Evidence matrix (strong) | Task-context flow, not a clinical or consciousness claim |
| Infant age changes local flow/reachability | `local_dynamics` / `possible_futures` | `rejected` (FDR-null in both infant lines) | Evidence matrix | Chart/qEEG age signal ≠ operator change |
| Hypoglycemia collapses reachability | `possible_futures` | `rejected` as confirmatory (validity-limited) | Metabolic panel | State chart *does* move |
| TRN is the identified RVC executor | `control` | `speculative` (ansatz); prior PV result bounded | Candidate mechanism | Do not claim identification |
| Committor / FAR as empirical NMD exports | `possible_futures` | `speculative` in this repo (conceptual promote; simulator-side elsewhere) | Conceptual hierarchy | Do not fold into the measurement contract |
| Attractors/basins organize long-run trajectories | `possible_futures` | `plausible` conceptually; **not** validated on these charts | Conceptual, careful | Landscape language without claiming recovered attractors |
| NDHI indexes consciousness or clinical health | — | `rejected` as biomarker | `exclude` from main claims | Exploratory composite only |
| Constitutive “experience *is* denoising” | — | `speculative` metaphysics | Optional discussion | No extra empirical content |
| Drop “MNJ-vNext” | `terminology_only` | — | Vocabulary | J is generic; MNJ = J on MNPS |

---

## What NOT to import (NDHI, Atlas as theory, constitutive consciousness, universal signature)

1. **NDHI** as a main-text object, figure, or “health” coordinate. 0.8 already demoted it; flagship should go further: omit or one glossary footnote.
2. **Noetic Atlas** as if Mapper/PH/RQA *were* NDT. Optional toolbox in S1. Do not rebuild Signature P3 around untested Mapper hubs.
3. **Constitutive consciousness** in abstract, highlights, or predictions. Keep as a labeled optional reading if at all.
4. **Universal NDT / consciousness signature.** The corpus falsifies this: different conditions move different layers. Import that as a *positive* prediction of structured dissociations.
5. **NMD = NDT.** Charts, windows, coverage, HDF5, invalidity policy, EAP `anchor_state` exports belong to NMD.
6. **DANDI 000458 as a consciousness or Jacobian result.** Association + failed operator. Analysis is not an nmd-analysis empirical paper.
7. **Spindle event-locking as causal RVC / denoising / consolidation.** Timing ≠ mechanism.
8. **EAP as a third MNPS axis or required term in the core SDE.**
9. **Metabolic q_met as fitted physiology or a consciousness scalar.**
10. **MNJ-vNext, spectral radius as “dominant local expansion” in continuous time, cone size as controllability or awareness.**
11. **Empty templates as results:** `NoeticDiffusionTheory_v2/manuscript.typ`, `Rythmic_Variance_Control_in_Sleep_theory/manuscript.typ`, `psychosis_first_time_local_dynamics/`, `comatose_ndt_angles/`.
12. **Clinical catalogue prose** (epilepsy, propofol, PTSD, etc. if not in the matrix). Extreme-regime leftovers stay in Figure 5 cells, not sections.
13. **0.8 Signature P4 operationalizations as still-open primary tests** — the *existence* of bounded deformation is supported; the original Mapper-fragmentation / 3D-volume-collapse sketches are the wrong targets.
14. **Coma siblings as additional main-text anchors.** 12–24 h mixed-sign pilot is a matrix footnote about temporal non-stationarity, not a second coma paper.

---

## Suggested manuscript placement

Maps onto sciencelead §10 architecture (not an invitation to expand empirical sections).

| Flagship section (sciencelead) | Material from this summary |
| --- | --- |
| 1. Scope and epistemic status | 0.8 claim-tier language **rewritten** onto accessibility; ndt_2 evidence-class labels; “not a consciousness scalar” |
| 2. From neural state to neural accessibility | Identity harvest rewrite table; flagship sentence from `sl_1.md` |
| 3. NDT multiscale measurement ladder | ndt_2 ladder + DANDI residual-0.856 as the worked example (cite `03_ndt_subsystems…` for the analysis) |
| 4. Core stochastic dynamics | Generalized SDE; 0.8 potential as `b_pot`; diffusion tensor promoted |
| 5. Measured state: MNPS and the NMD boundary | NMD v2.4 ownership; 3D/9D as charts; this repo’s DANDI ingest note only |
| 6. Local dynamical geometry | Promote J, α/ω/Δ_react; gambling row as intuition pump; drop MNJ-vNext; coma MNJ as empirical constraint |
| 7. Accessible futures | Coma reachability as Anchor 2; committor/FAR conceptual; attractors careful |
| 8. Biological control of accessibility | RVC as special case (Anchor 1 spindles); TRN/Thalamic Access as candidate (not this repo’s main evidence); EAP subsection; metabolic panel |
| 9. What the current evidence actually supports | Anchors 1–2 here; Anchor 3 from subsystems; **Figure 5 = evidence matrix above** |
| 10–12. Competitors, adversarial tests, failure conditions | 0.8 P5 anti-phase distinguisher; ndt_2 four RVC tests (event, schedule, incremental, null specificity); ndt_lack identification gap |
| 13–14. Discussion / conclusion | Accessibility geometry; structured dissociations |

**Figure 5 rows this repo can actually fill:** spindle; coma; depression; psychosis; neurodegeneration (AD/FTD rest+photic); (optional) PD; gambling-as-task-dissociation; infant development; EAP; metabolic. Leave truth-known simulator, meso→macro detail, anesthesia, epilepsy to other summaries / empty cells.

**Empirical main-text budget (sciencelead 15%).** Spindle (event-level state) + coma (futures + flow) + DANDI (epistemic). Everything else is the matrix.

---

## Open questions

1. **Can spindle-locked `d_n` be residualized on sigma power / event density / arousal** so that RVC’s *schedule-specificity* test (ndt_2 four-way) is actually run? Until then Anchor 1 is Level-1 event association.
2. **Do spindles change reachability or J, or only 9D occupancy?** Not measured in the frozen RVC_SLEEP contract. A positive would upgrade Anchor 1 toward Layers B–D; a negative would keep it as state-only.
3. **Coma Level-4:** residual fraction / perturbation-response on I-CARE charts is unknown. How far can Anchor 2 be pushed without pretending operator identification?
4. **Spectral abscissa vs radius** in the coma and gambling papers: does switching the signed stability summary change the clinical/task story?
5. **Sleep curriculum (0.8 P3)** — NREM centralization vs REM expansion in MNPS topology — is still a prediction, not a result of the spindle papers (which are N2-event, not stage-topology).
6. **Causal RVC test** (ndt_lack): closed-loop SO-phase stimulation, spindle perturbation, or TRN manipulation with preregistered geometry mediation. None exists here.
7. **FEP n_unmed=8** in ds003947: is the dynamics-vs-position dissociation robust enough for Figure 5, or only a cautionary cell?
8. **ESB-2** is an internally frozen composite; importing it would smuggle Atlas-like indexation back in. Keep out unless decomposed into named NDT objects.
9. **Diary gap:** RVC_SLEEP cites `project/diary/229_…md` for a Pass C erratum; that tree is absent in this snapshot. Confirm no later freeze changed Anchor 1/2 status before drafting.
10. **Anchor 3 ownership:** confirm ndt-subsystems DANDI numbers (ρ≈0.4, residual 0.856) are the ones the flagship will cite, not a later rerun.
11. **Committor/FAR:** conceptually promoted; this repo has no empirical committor/FAR ceiling. Do not imply I-CARE or spindles measured them.
12. **Identifiability** (0.8 + ndt_lack): Φ vs G vs Σ vs observation map still not separable from MNPS motion. Flagship should state the equivalence class, not imply the coma/depression effects identify a unique latent law.
