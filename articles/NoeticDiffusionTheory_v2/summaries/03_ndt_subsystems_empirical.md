# 03 — ndt-subsystems: empirical meso, TRN, HELS real-data

Internal cartography for NDT 1.0 / Noetic Diffusion Theory v2. Source repo: `J:\repos\ndt-subsystems`. Notation map: `agent/compact_summary.md` (canonical symbols; **stale vs late-August 2026 results** — it does not record TA-E2, HELS-A1-H0/H0B/M0, DANDI 000363 M1 authorization, or PRRG/SDSR closures). Companion numbers for Anchor 3 also live in `nmd-analysis/articles/NDT_2` (`ndt_2.typ` §§meso/bridge). Do not analogize any empirical chart here to simulator latents.

**Architecture filter (frozen):** State geometry → Local dynamical geometry → Geometry of possible futures → Control of accessibility.

**Recoverability ladder:** (1) association → (2) mechanism discrimination → (3) latent-order preservation → (4) dynamical-operator identification. Success at one level does not license a stronger claim.

**Tag schema:** Layer (`state` / `local_dynamics` / `possible_futures` / `control` / `epistemic` / `measurement_contract`) · Evidence class (`established_external` / `internal_validated` / `plausible` / `speculative` / `rejected`) · Flagship role (`main_text_anchor` / `evidence_matrix` / `supplement` / `exclude` / `terminology_only`) · Claim ceiling (one sentence).

---

## Inventory

| Cluster | Paths (ndt-subsystems unless noted) | Status as of 2026-08-28 |
|---|---|---|
| **Anchor 3 meso→macro** | Companion analysis cited by `NDT_2`; Claar/Rembado/Koch DANDI 000458 (simultaneous Neuropixels + surface EEG, cortical ES, wake/isoflurane). Proposed `articles/dandi_000458_meso_macro/` was never opened in this repo. | **Use as flagship epistemic spine.** Bounded Level-1 associations + Level-4 operator **failure**. |
| **000458 TRN/opto siblings** | `articles/DANDI_000458/`, `_opto/`, `_PRRG/`, `_SDSR/`, `_SDSR_Identifiability/`; Figshare `28440311` (Russo et al. 2025) | Distinct resource from the dandiset. PRRG/SDSR **closed**. ΔPR **stability-limited**. TA-E1 **FAIL_Q_PRESTIM_CONTROL**. Dandiset itself: **no usable TRN population** (1/24 sessions, 30 RT units, no co-recorded relay). |
| **PRRG closure** | `articles/PRRG_Falsification/` | Universal pause–rebound repertoire gate **rejected**. |
| **TRN-VG (Dryad)** | `articles/TRN_VG/`; DOI `10.5061/dryad.f7m0cfzb1` | Ladder **CLOSED** 2026-07-10. PV participation-ratio contraction supported; full TRN-VG / scalar variance clamp **not validated**. |
| **TA-E2 residual shape** | `project/TA/`; `articles/thalamic_access_rolon_martinez_dataDryad/` | PV-v1.1 and SST-v1.0 both `PASS_Q_SHAPE_PRESTIM_CLEAN`. Same Dryad resource as TRN-VG. **Not** operator ID, **not** RVC. |
| **Synthetic TA** | `articles/thalamic_access/` | Simulator article. Empirical mapping does **not** inherit its operators. |
| **TA-E4 / DANDI 000363** | `project/ta_dandi_000363/` | M1-Q **authorized** 2026-08-28; family archive **incomplete** (3/29 sessions in `session_metrics.csv`; no `family_summary.json` / `gate_report.md`). Geometry / Gram / `M(τ)` / operator ID **CLOSED**. |
| **HELS CRCNS** | `articles/CRCNS_hc19_HELS`, `_hc25_HELS`, `_hc28_HELS`; `project/HELS/hels_sciencelead_001.md` | Infrastructure frozen. **No HELS mechanism.** |
| **HELS-A1** | `project/HELS-A/` | H0/H0B eligibility **RATIFIED**; M0 estimator **FAIL**; M0R drafted; A1 scoring / download **CLOSED**. |
| **Other meso** | `DANDI_000939*`, `DANDI_000563_TemporalBarcode`, `IBL_BWM_*`, Dryad Garett/Hosford, Zenodo 8224756 | Status/ceiling only unless noted. |
| **RVC_SLEEP copy** | `articles/RVC_SLEEP/` | Duplicate / earlier freeze of `nmd-analysis/articles/RVC_SLEEP`. **Do not double-count.** |

---

## Executive take for flagship (≤15 lines)

DANDI 000458 as **Anchor 3** licenses a methodological lesson, not NDT geometry: post-artifact LFP-variance proxy and quality-filtered spike rate associate with EEG variance / spectral entropy at median subject correlations near **0.4** under sign-flip and circular time-shift nulls (Level 1). The same EEG-only chart yields median local-linear residual-variance fraction **0.856**, so Jacobian and reachability inference are **rejected** (Level 4 fail). That pair is the epistemic spine: association without operator ID.

TRN/TA real data show **population geometry and residual covariance shape**, not a scalar variance clamp and not NDT `σ(t)` / `A_noise` / `Q` / `M(τ)`. Dryad PV photoinhibition contracts evoked participation ratio (Stage 3, 7/7); SOM does not. TA-E2 finds non-scalar residual covariance-shape change in **both** PV-TRN and SST-TRN families on that same Dryad resource — Level 1, with a bounded Level-2 contrast against **scalar rescaling only**. Figshare optoTH (Russo) never established TRN-specific repertoire gating (PRRG fail; SDSR unidentifiable; TA-E1 prestim control fail). Do not claim NDT has found the thalamic mechanism.

HELS real data remain **qualification / eligibility**, not landscape writing. CRCNS hc-19/25/28: loaders, geometry pilots, decoder feasibility; predicted interactions null or uninterpretable. HELS-A1 on DANDI 001371: headers eligible, estimator M0 failed N3, spikes unread.

---

## DANDI 000458 (Anchor 3) memo

Two **non-interchangeable** 000458 objects exist. Flagship Anchor 3 is the **meso→macro companion** (Neuropixels + EEG). The Figshare opto companion is a separate TRN-perturbation resource.

### A. Meso→macro companion (Claar/Rembado/Koch dandiset)

**Design.** Simultaneous Neuropixels and surface EEG during cortical electrical stimulation in head-fixed mice, continuing from awake into isoflurane. Mesoscopic operationalization (ndt_2): post-artifact LFP-variance proxy, quality-filtered spike rate, population dimensionality (participation ratio). Macro: EEG variance and spectral entropy. Session estimates aggregated within subject; primary nulls = subject-level sign-flip and circular within-session time-shift; BH-FDR on a prespecified feature-pair family; LOSO and extraction sensitivity.

**Positive findings (Level 1).** LFP-variance-proxy–EEG-variance and spike-rate–EEG-spectral-entropy associations: median subject correlations **near 0.4**, surviving both null families. These are **bounded associations**. They do not identify direction, a common manifold, TRN, MNPS identity, or MNDM.

**Negative findings (Level 4).** Median local-linear residual-variance fraction **0.856** on the EEG-only chart. Jacobian and reachability interpretation **rejected**. A visually plausible chart plus a cross-scale correlation is insufficient for dynamical-operator identification.

**Recoverability reached.** Level 1 (association) **internal_validated** as a companion constraint. Level 2 (mechanism discrimination) **not established** — no TRN vs cortex vs arousal vs stimulation-artifact discrimination in this bridge. Level 3 (latent-order preservation) **not claimed**. Level 4 **failed** under the tested chart.

**Claim ceiling.** Simultaneous meso and macro observables can covary under stimulation-aligned windows after temporal/statistical nulls; the tested EEG chart does **not** recover a local flow/Jacobian/reachability operator. Role: **epistemic**, not ontology.

| Tag | Value |
|---|---|
| Layer | `epistemic` (bridge); measurements sit at `state` only |
| Evidence class | `internal_validated` (association); `rejected` (operator ID) |
| Flagship role | `main_text_anchor` |
| Claim ceiling | Cross-scale contact under nulls; not common latent identity, unique NDT geometry, causal direction, or MNJ. |

**Repo note.** `articles/TRN_VG/sciencelead/002.md` proposed `D458-000/001` inventory/alignment then a prediction test vs shuffle/wrong-region. That article folder was **not created**. Do not invent later stages. Import numbers from `NDT_2`, not from TRN-VG or Figshare opto.

### B. Figshare opto / PRRG / SDSR / TA-E1 (same calendar line, different claim)

Russo et al. 2025 companion (`10.6084/m9.figshare.28440311`): 6 mice / 11 sessions; `optoTH` vs `optoCT`; ES × opto factorial. Frozen optoTH relay cohort for later tests: mouse627041, mouse670246, mouse671439 (mouse673553 excluded for 4 relay units). DANDI 000458 NWB files **cannot** support a TRN-specific claim.

| Experiment | Result | Recoverability | Ceiling |
|---|---|---|---|
| Opto Exp 1 mean-response | Directional manipulation gate passed after area-column fix; RT activation mixed (one mouse net RT decrease with intact relay suppression; mouse670246 weak RT **and** weak relay suppression — kept by rule) | Level 1 descriptive | Manipulation occurred; not variance gating |
| Opto Exp 2 ΔPR | Equal-mouse ΔPR = **+13.12**; mice +20.4 / **−2.0** / +20.9; permutation p=0.002; **fixed-unit k=23 consistency 68.7% < 80%** | Level 1, **stability-limited** | Do not promote to TA operator or NDT `σ(t)` |
| PRRG Exp 1 | Aggregate signs match (ΔH_pause −0.00435, ΔH_rebound +0.01033, BRI +0.01468) but trial-shuffle BRI **increases**, rate-matching **reverses**, optoCT shows **same biphasic signs** | Level 1 descriptive; Level 2 **fail** | PRRG **rejected** for this dataset |
| SDSR Exp 1 | TLI-specific descriptive +0.1035 (availability more localized at intermediate units) | Level 1 descriptive | Direct-TRN SDSR **not established** (opto-only clock unresolved; held-out 72.5% unthresholded) |
| SDSR Exp 2A | Observed TLI-specific 0.0294 **below** gain-only 97.5th (0.0331); M4/M5 power **0/1000** | Level 2 **fail** (identifiability) | Ladder closed; 2B forbidden |
| TA-E1-Q | `FAIL_Q_PRESTIM_CONTROL` (primary p_scalar ≈ 5e-4 **and** prestim p ≈ 0.006) | Perturbation-localized shape **rejected** | Closed; `M(τ)` `METHOD_LIMITED` |

PRRG_Falsification also folds DANDI 000939: 50 ms protocol **stopped at Stage 0** (laser ~1 s; proposed rebound still during light); 1 s ArchT-minus-GFP test shows **opposite** central-pulse sign (ΔH_central −0.066, BRI +0.053 vs predicted BRI < 0). Branch closed. Do not claim inverse-PRRG.

---

## Thalamic / TRN empirical memo

### What changed vs what did not (read this first)

| Quantity | Dryad Rolón-Martínez (PV/SST photoinhibition, tone-locked) | Figshare Russo optoTH (ES-locked) | DANDI 000939 HD (ArchT) | Hosford pulvinar (Zenodo Fig. 4) |
|---|---|---|---|---|
| Mean rate | Stage 1 **passed** both cell types (manipulation validity) | Mixed; inclusion not by effect size | Silencing present by design | Mean encoding reduced (confirmatory reanalysis) |
| Single-unit variance / Fano | **Ambiguous**, estimator-dependent (Stage 2/2b); later SDSR screen **withdrawn** | Not the surviving claim | Stage 2 angular-dispersion **inconclusive** (p=0.20, 10 assignments) | Dispersion of encoding-strength **increased** (session-level; n=4 mice, permutation floor p=0.125) |
| Population geometry (PR) | **PV passed** 7/7 (DiD PR ≈ −2.30, perm p≈0.005); **SOM failed** 4/7 | ΔPR +13.12 but **fixed-unit fail** | Stage 3 **not run** | Not re-estimated from spikes (Branch A timeout) |
| Residual covariance **shape** (trace-normalized D vs scalar null) | TA-E2 PV **and** SST `PASS_Q_SHAPE_PRESTIM_CLEAN` | TA-E1 **FAIL** prestim | Not tested | Not tested |
| Decoder / information | Stage 4 PV p_perm=**0.0555**, suggestive, not α=0.05 | Not a licensed claim | N/A | N/A |
| Scalar variance clamp / RVC / `σ(t)` | **Not shown** | **Not shown** | **Not shown** | **Not shown** |
| NDT operator / `A_noise` / `Q` / `M(τ)` | **Not identified** | **Not identified** | **Not identified** | **Not identified** |

### Per dataset

**1. TRN_VG — Dryad auditory TRN→MGB (CLOSED 2026-07-10).**  
Hypothesis was trial-to-trial variance/dispersion regulation, not merely mean gain.  
- Layer: `state` (PR as repertoire size), not `local_dynamics`.  
- Evidence: PV Stage 3 **internal_validated** (subject to multiplicity audit in `sciencelead/001.md`; PR survived assumed-family Bonferroni at q=0.025). SOM residual-norm exploratory only. Whole TRN-VG **rejected**.  
- Cell types: PV vs SOM/SST **asymmetric**. Do not say “SOM has no role.”  
- Not shown: scalar Fano gate; information loss; NDT mechanism.  
- Flagship: `evidence_matrix` (control-of-accessibility **candidate**, bounded). Ceiling: *PV perturbation associated with contraction of evoked population dimensionality; variance-gating mechanism not established.*

**2. TA-E2 — same Dryad, residual covariance shape (PV 2026-08-23, SST 2026-08-24).**  
Windows `[-25,0)` vs `[0,25)` ms; laser ON/OFF; Ledoit–Wolf vs raw; shared-template permutation B=2000.  
- PV: `p_post=1/2001`, `p_pre=0.518`, 4/4 mice post, `p_CTL_post=0.628`; one mouse (S0163) mouse-level prestim reject compatible with family-clean prestim. `T_PV,post≈0.181`.  
- SST: `p_post=0.00050`, `p_pre=0.600`, 4/4 post, 0/4 prestim, `p_CTL_post=0.803`. `T_SST,post≈0.124`.  
- **Convergent families, not replication, not PV>SST contrast** (contrast CLOSED). Empty-virus n=2 cannot prove artifact absence. `D_diag`/`D_off` descriptive — **correlation geometry not established** (heterogeneous variance redistribution remains open).  
- Recoverability: Level 1 **internal_validated**; Level 2 only vs **scalar covariance rescaling**, not vs arousal/light/heating/mean–variance coupling; Levels 3–4 **closed**.  
- Layer: `state` / population variability geometry; **not** `possible_futures`, **not** `control` as identified mechanism.  
- Flagship: `evidence_matrix` under §10.3. Ceiling: *TRN cell-type photoinhibition can associate with non-scalar residual covariance-shape change in early MGB-assigned activity in this dataset; NDT has not identified the thalamic access operator.*

**3. Figshare Russo / DANDI_000458_opto / TA-E1.**  
See Anchor 3-B. TA-E1 D1 diagnostic: no unanimous prestim mean-state pattern; does not explain the prestim FAIL. Resource `ELIGIBLE_WITH_LIMITATIONS` for native-timescale shape tests; full `M(τ)` **not testable** (two onsets, one current/mouse). Flagship: `supplement` as **negative control** (prestim-localized difference ≠ perturbation-specific operator).

**4. DANDI 000939 + Figshare 24921252 (Peyrache HD).**  
Known 1-D HD ring — geometrically attractive, evidentially thin. Track split: only 5/9 DANDI `+ogen` sessions are TRN-ArchT; 4 are local PoSub PV/SST (out of scope). Matched-H5 PRRG 50 ms **invalid pulse contract**. 1 s silencing: robust **opposite** entropy pattern, no speed/circuit/timing arms. Stage 2 tuning-width DiD inconclusive; Stage 3 attractor geometry **not run**. Flagship: `supplement` / mostly `exclude` from mechanism paragraphs.

**5. DANDI 000563 Temporal Barcode (OpenScope).**  
Observational RT/LGd/VIS. RepeatFFF fidelity positive. Rate-normalized PR highest in VIS (≈26 / 31 / 116). Ridge RT↔LGd↔VIS predictability exceeds repeat-shift null **but reverse ≥ forward** — shared stimulus, not directed TRN routing. Flagship: `exclude` from causal TRN claims; optional `supplement` as association-without-direction example.

**6. Hosford TRN→pulvinar (Zenodo 19465617).**  
Branch B confirmatory on authors’ Fig. 4H–J summaries: mean down, dispersion up, all 4 mice directional; mouse-level permutation **p=0.125 floor**. Branch A raw spikes **CLOSED** (timeout). Independent lab/circuit, **not** a raw-spike TRN-VG replication. Flagship: `supplement`, small-n.

**7. DataDryad_RolonMartinez (feasibility) / _SDSR.**  
Stages 0–6: PSTH reconstruction PASS; subject-level residualized Fano contrast **≈0**. SDSR TLI screen **withdrawn** (frequency ≠ recruitment axis). Superseded scientifically by TRN_VG + TA-E2; keep as provenance, not a second result.

**8. Synthetic `thalamic_access` article.**  
Truth-known two-operator SDE. Jacobian errors ~1e-10. **No biological observation map.** Import only as terminology (`A_sig` vs `A_noise`) with explicit simulator boundary — belongs with `02_ndt_simulator_*`, not as empirical TA.

**9. ta_dandi_000363 (Inagaki/Li ALM photoinhibition → thalamus).**  
Question is heterogeneous unit modulation vs shared population gain in late-delay Table-2 thalamus-target sessions (29 sessions / 10 mice, pin `000363/0.231012.2129`). `sl_ta_363_011` authorized **one** M1-Q execution; T2, OTHER stim, delay-onset, off-target, NB, **geometry/Gram/`M(τ)`/access-operator inference all CLOSED**. Provenance hashes frozen 2026-08-28 with `real_spikes_read=false`; `session_metrics.csv` currently has **three** valid sessions only — **not a family result**. Do not cite deltas. Status: **authorized, incomplete, unratified**.

---

## HELS real-data memo

**Programme question.** Does hippocampal (CA1) state carry **incremental conditional information** about later cortical (mPFC) trajectory direction after matching current cortical state and observed task covariates — and, separately, does that equal causal access `A_H` / landscape writing? Those are three different claims (A0 synthetic possibility vs A1 observational information vs A2 perturbation).

### CRCNS hc-19 / hc-25 / hc-28 (frozen)

`project/HELS/hels_sciencelead_001.md`: **HELS internal validated mechanism result: none.**

| Dataset | What passed | What failed / bounded |
|---|---|---|
| hc-28 | Loader (epoch-cell unwrap), 51 labelled run epochs, ripple lock, decoder **feasible** (3086 events, time-shift/unit-shuffle/wrong-context nulls written) | Replay content ↛ later mPFC geometry; `wtr2−wtr1` transition entropy mean 0.046, sign-flip **p=1.0**; `lin` not pooled as familiar/novel |
| hc-25 | Five-rat 2×2 Sync/CTRL cohort constructed | Primary `delta_effective_dimension` interaction 0.758, sign-flip **p=0.50**; sorting mismatches (Rat214/220) recorded, not repaired |
| hc-19 | Input contract READY (3 days) | Decoder **WEAK** vs nulls; Falcon labels ≠ biological replay truth; pickle posteriors out of scope |

Eligibility ≠ mechanism. Geometry summaries are operational charts, not Φ.

### HELS-A1 (DANDI 001371 draft, 2026-08-28)

| Stage | Gate | Meaning |
|---|---|---|
| H0 | `ELIGIBLE_WITH_LIMITATIONS` | CA1/PFC labels, clock proxy, `U_t` inspectable remotely; two probed sessions; draft mutable |
| H0B | `SUPPORT_MULTI_ANIMAL` | **42/66** sessions, **7/7** mice meet header floor (≥20 CA1, ≥20 PFC, ≥50 trials) + finite `t_update`. Header count ≠ A1-usable units |
| M0 | `M0_FAIL` | Fabricated estimator: N3 family FP **0.78** at f=1.00 (allowance 0.10); P1 detection 1.00 is **not** biology. 4704 synthetic cells; **no 001371 spike times** |
| M0R | protocol drafted | Split N3 into N3O (observed-U sufficient → must be null) vs N3L (latent confound → **non-identifiable**, not a false positive to train away). `Δ>0` abandoned |
| A1 scoring / download | **CLOSED** | 001371 = `LEADING_CANDIDATE_NOT_SELECTED` vs hc-28 |

Science-lead (`sl_helsa_dandi_005`): even a future A1 pass would be **conditional information**, not “CA1 changed mPFC access.” `A_H` remains plausible interpretation until perturbation (A2).

**Do not promote.** Flagship: `terminology_only` / thin `evidence_matrix` cell “not tested / infrastructure only.” Layer: conceptually `possible_futures` / landscape formation; evidence class **speculative** for mechanism, **internal_validated** only for eligibility/estimator-failure.

---

## Other datasets (compact table)

| Dataset/article | Layer | Evidence class | Role | Ceiling |
|---|---|---|---|---|
| DANDI 000458 meso→macro (NDT_2 companion) | epistemic / state | internal_validated assoc.; rejected operator | **main_text_anchor** | ρ≈0.4 LFP/EEG & rate/entropy; residual fraction 0.856 forbids MNJ/reachability |
| DANDI 000458 NWB inventory | measurement_contract | internal_validated | exclude as TRN | No TRN+relay population |
| Figshare Russo opto / `_opto` ΔPR | state | internal_validated but stability-limited | supplement / negative | ΔPR +13, fixed-unit fail; not TA |
| `_PRRG` + `PRRG_Falsification` | control (failed) | rejected | evidence_matrix (falsification) | No universal pause–rebound gate |
| `_SDSR` + Identifiability | control (failed) | rejected (identifiability) | exclude mechanism | Gain-only can match TLI; power 0 |
| TRN_VG Dryad | state | internal_validated (PV PR only) | evidence_matrix | Dimensionality contraction ≠ variance clamp |
| TA-E2 Dryad PV+SST | state | internal_validated shape assoc. | evidence_matrix | Non-scalar residual shape; not `A_noise` |
| TA-E1 Figshare | state | rejected (prestim) | supplement (negative) | Difference not perturbation-localized |
| Synthetic TA article | local_dynamics (sim) | internal_validated **synthetic** | exclude from this empirical file | No biological map |
| ta_dandi_000363 M1 | state / control (test) | incomplete | exclude until family archive | Shared-gain vs hetero **unratified**; operator CLOSED |
| DANDI 000939 PRRG 50 ms | measurement_contract | rejected pulse contract | exclude | Rebound window during 1 s laser |
| DANDI 000939 PRRG 1 s | state | rejected predicted signs | supplement | Opposite entropy; n=2 ArchT / n=3 GFP; no speed |
| DANDI 000939 Stage 2/3 VG | state | inconclusive / not run | exclude | No attractor-geometry claim |
| DANDI 000563 barcode | state | internal_validated association | supplement | Repeat fidelity; **no directed routing** |
| IBL_BWM_SDSR (000409) | measurement_contract | rejected coverage | exclude | 0 RT–LGd; 1 RT–LP session; STOP |
| IBL_BWM_CCTG | measurement_contract | rejected identifiability | exclude | Shared-state estimator fails gain nulls; STOP |
| DataDryad_Garett / `dryad_dbrv15f3n` (VPm) | state | internal_validated burst-rate; rejected timing-dispersion | supplement | Relay, **not TRN**; Stage 2 SD/MAD null |
| DataDryad_Hosford | state | internal_validated confirmatory summaries | supplement | n=4; raw Branch A closed |
| Zenodo_8224756 SDSR-Indirect | measurement_contract | rejected contrast | exclude | No no-light + ≥3 LED doses in VPm files |
| CRCNS hc-19/25/28 HELS | measurement_contract | internal_validated infra; rejected/null mechanism | exclude mechanism | No landscape writing |
| HELS-A1 001371 | measurement_contract | eligibility pass; M0 fail | exclude mechanism | Spikes unread; estimator unsafe |
| RVC_SLEEP (this repo copy) | local_dynamics / control | — | **exclude (duplicate)** | Count `nmd-analysis/articles/RVC_SLEEP` once |

---

## Claims table

| ID | Claim (strongest licensed wording) | Ladder | Layer | Class | Role | Ceiling / forbid |
|---|---|---|---|---|---|---|
| A3+ | Meso LFP-variance proxy and spike rate associate with EEG variance/entropy under sign-flip and time-shift nulls | 1 | epistemic | internal_validated | main_text_anchor | Not direction, manifold, TRN, MNPS=latent |
| A3− | EEG-only local-linear residual fraction 0.856; Jacobian/reachability **out** | 4 fail | local_dynamics / possible_futures | rejected | main_text_anchor | Do not treat chart as MNJ-ready |
| TVG-PV | PV-TRN photoinhibition: evoked PR contraction, 7/7 + perm | 1 | state | internal_validated | evidence_matrix | Not TRN-VG as a whole; not Fano |
| TVG-SOM | SOM: no robust PR/Fano/decoder | 1 fail | state | rejected / exploratory | evidence_matrix | Not “SOM irrelevant” |
| TVG-all | Full TRN variance-gate hypothesis | 2 fail | control | rejected | evidence_matrix | Close the ladder |
| TA-E2 | PV and SST families: non-scalar residual covariance shape, prestim-clean at family level | 1 (+ bounded 2 vs scalar) | state | internal_validated | evidence_matrix | Not `Q`/`A_noise`; not correlation geometry; not PV vs SST; not independent replication |
| TA-E1 | Perturbation-window-specific shape under TA-E1-Q | 2 fail | state | rejected | supplement | Prestim also rejects |
| PRRG | Pause-compress / rebound-redistribute shared covariance, TRN-specific | 2 fail | control | rejected | evidence_matrix | Signs ≠ mechanism |
| SDSR | Selective near-threshold availability via TRN | 2 fail | control | rejected | exclude | Identifiability fail |
| 939-1s | ArchT 1 s entropy reversal as PRRG | 1 fail (wrong sign) | state | rejected | supplement | Descriptive opposite pattern only |
| HELS-mech | Replay/CA1 writes later cortical accessibility / Φ | 4 untested | possible_futures | speculative | terminology_only | Infrastructure ≠ writing |
| HELS-A1 | 001371 currently tests `A_H` | — | — | rejected as claim | exclude | M0_FAIL; spikes closed |
| TA-363 | Heterogeneous thalamic modulation vs shared gain | 2 (if pass) | control | **not yet** | exclude | Incomplete execution; operator still closed |
| RVC-TRN | TRN photoinhibition proves rhythmic variance control | — | control | rejected analogy | exclude | Different estimands, datasets, timescales |

---

## What NOT to import

- Do **not** analogize DANDI 000458 meso–macro associations to simulator latents, MNPS `(m,d,e)`, MNJ, or reachability cones. The companion’s **negative** operator result is the point.
- Do **not** treat TRN photoinhibition (Dryad or Figshare) as proof of **RVC**. RVC is event-locked macro variance scheduling (sleep spindles live in nmd-analysis). TA-E2 is residual **shape** during concurrent laser+tone, not a resting access state after offset, not `σ(t)`.
- Do **not** merge dandiset 000458 (almost no TRN units) with Figshare opto (causal TRN/cortical light).
- Do **not** promote Opto ΔPR +13 after the 68.7% fixed-unit fail, or PRRG aggregate signs after shuffle/rate/optoCT fails.
- Do **not** call TA-E2 a replication of TRN-VG Stage 3, a PV–SST comparison, or biological `A_noise`. Same Dryad; different endpoint; `D_off` closed.
- Do **not** import synthetic TA Jacobian/committor numbers as empirical thalamus.
- Do **not** use DANDI 000363 partial `session_metrics` rows as a result.
- Do **not** use HELS CRCNS geometry deltas or 001371 header yield as landscape writing.
- Do **not** double-count `RVC_SLEEP` from this repo.
- Do **not** read `compact_summary.md` cytodendritic bridge or C/TI/P as empirically recovered here. Generator identifiability warning in that file **does** apply: data constrain local laws more than unique `(G_t, Φ, σ)` splits — and 000458 already failed the local-linear law on EEG.

---

## Suggested manuscript placement

| sl_001 locus | What to put | What to keep out |
|---|---|---|
| **§13** Cross-scale grounding | Anchor 3 pair: ρ≈0.4 associations **and** residual 0.856 operator fail. Sentence: *cross-scale contact, not common latent identity.* | Figshare PRRG/SDSR; TRN-VG; TA-E2 |
| **§10.3** Thalamic Access | Candidate access-control architecture vs obsolete “TRN = variance clamp.” Empirics: PV PR contraction + TA-E2 non-scalar shape as **bounded biological associations**; TA-E1 and PRRG as **failed** stronger claims; 000363 **open**. | “NDT found the thalamic mechanism”; RVC identity; `M(τ)` |
| **§14.4** Evidence matrix | Rows: meso→macro; TRN perturbation (Dryad); TRN opto (Figshare, negative); HELS (not tested / infra). Columns: state / local_dynamics / diffusion / reachability / destination / mechanism. Code cells **bounded / null / not tested**. | Equal shading across programmes |
| **Figure 2** Inference ladder | Worked example: 000458 stops at (1); operator ID (4) **fails** on same chart. Optional second example: TA-E2 reaches (1) and a thin (2) vs scalar; (4) closed. | Simulator recoveries drawn as if they were 000458 |
| **Figure 5** Empirical map | Meso→macro: state **bounded**, local dynamics **null**, reachability **null**, mechanism **not tested**. Thalamus: state **bounded**, mechanism **speculative**. HELS: all **not tested** except measurement_contract. | Spindle/coma rows (other summaries) |

---

## Open questions

1. **ta_dandi_000363 M1-Q.** Authorized one-shot; family gate not archived as of this memo. Until `family_summary.json` + post-execution review exist, treat as **unexecuted for flagship purposes**. Even a `M1_HETEROGENEOUS_PASS` licenses only *shared population gain inadequate under this Poisson/T1 model* — not operator-valued access. Geometry/Gram/`M(τ)` remain closed by protocol.

2. **HELS-A1 mapping.** 001371 is a leading **unselected** candidate. M0R must distinguish calibrated nulls (N3O) from non-identifiable latent confounding (N3L). No spike download, no A1 score, no `A_H` claim until a new fabricated protocol **and** real-data preflight independently pass. Conditional information ≠ causal access.

3. **Independence of TA-E2.** Next gain is a **different laboratory / stimulus / species** testing a **different predicted consequence** (e.g. temporal propagation / `A_sig`-like), not more Dryad windows. Figshare Russo is not that independent test (TA-E1 already failed prestim).

4. **Meso→macro replication.** Anchor 3 is a single companion mouse ES dataset. Preregistered cross-lab EEG+spikes replication is unfilled. Do not paper over that with 000563 routing correlations.

5. **Cell-type vs circuit.** PV vs SST shape convergence is same-preparation. Hosford pulvinar is independent but summary-level and n=4. IBL BWM cannot currently host observational SDSR (coverage STOP).

6. **Notation-map hygiene.** Update `ndt-subsystems/agent/compact_summary.md` before treating it as an empirical claim ledger; it is a formula map and omits the 2026-08 TA-E2 / HELS-A1 / 000363 state.
