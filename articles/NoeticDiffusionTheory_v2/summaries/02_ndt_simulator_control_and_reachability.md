# 02 — ndt-simulator: control, history, reachability

Source repo: `J:\repos\ndt-simulator`. Architecture filter: **State geometry → Local dynamical geometry → Geometry of possible futures → Control of accessibility**. Canonical SDE: \(dX_t = b(X_t,t;c_t)\,dt + \Sigma(X_t,t;c_t)\,dW_t\). Control \(c_t\) may reshape \(b\), \(\Sigma\), \(G\), \(\Phi\), and transition gates. O1/J1 local-dynamics recovery is out of scope (file `01`).

Every claim below is tagged **Layer / Evidence / Role / Ceiling**. Layers: `state` / `local_dynamics` / `possible_futures` / `control` / `epistemic` / `measurement_contract`. Evidence: `established_external` / `internal_validated` / `plausible` / `speculative` / `rejected`. Roles: `main_text_anchor` / `evidence_matrix` / `supplement` / `exclude` / `terminology_only`.

---

## Inventory

| Programme | Article / archive | Title (or status) | Gate IDs | Verdict |
| --- | --- | --- | --- | --- |
| Thalamic Access | `article/thalamic_access/` | Directional Access in a Fixed Dynamical Landscape | TA-0, TA-1, TA-2, TA-3, TA-4, TA-JQ1, TA-5 v1.2 | PASS (synthetic, staged) |
| TA remainder | `article/thalamic_access/claim_ledger.md` | Native-domain finite-amplitude | TA-7A/010, TA-7A-ND, TA-7B | 7A/010 rejected; 7A-ND DEV-only; 7B closed |
| HELS-A | `article/HELS-A/`; `project/HELS-A/programme_map.md` | Context-Conditioned Access Operators Reshape Route Accessibility on Fixed Dynamical Landscapes | A0 G1–G8; A0B G1–G8+G4U; A0C G8 | A0/A0B RATIFIED DEV PASS; A0C G8 FAIL |
| HELS legacy | `project/HELS-A/programme_map.md` | \(\partial\Phi/\partial t\) evidence | — | CLOSED |
| RVC gen1 | `project/claim_ledger.md` | Periodic write-gating | Gate G / E033 | **Rejected / frozen** |
| RVC gen2 | `article/rythm_2nd_gen/`; `results/m3_e046_rhythm_gen2/` | Event-Triggered Replay Does Not Outperform Matched-Energy Controls | Gate G2 / E046-A | **FAIL** (valid, not inconclusive) |
| Reachability R | `article/Reachability_over_closure_epoch/`; doi:10.5281/zenodo.22141078 | Calibrated Closure-Epoch Covariance Does Not Imply Memory-Specific Reachability | Gate R / E044; E044R | R-1/R-4 PASS; **R-3 rejected** |
| Reachability RD | `article/Directed_reachability_under_exclusive_replay/`; doi:10.5281/zenodo.22141880 | Exclusive Replay Does Not Produce Target-Private Latent Reachability | Gate RD / E045 | Calibration PASS; **specificity rejected** |
| Reachability RC | `article/Coupled_Resource_Reachability_over_Closure_Epoch/` | Resource Coupling Does Not Produce Direction-Specific Closure-Epoch Reachability | Gate RC / E047 | RC-0/1/4 PASS; **RC-2 rejected** |
| SSMR-1 | `article/SSMR/`; doi:10.5281/zenodo.22083593 | Predictive Information Is Not Recoverability | SSMR-1C-0/1/2, 1D-0 | Information ≠ recoverability; **1D-0 specificity FAIL** |
| SSMR-2 | `article/SSMR-2/` | True Recent History Improves Linear Prediction of Post-Stimulation Measured EEG Beyond the Current State | Gate H, Gate X; SSMR-2A-1 | `SPECIFIC_HISTORY_PASS` (H strong; X knife-edge) |
| Slow Branch | `article/Slow Branch-Level Accessibility as a Structural Constraint on Memory Linking/` | Slow Branch-Level Accessibility as a Structural Constraint on Memory Linking | E017–E022R | Joint SIG profile supported in simulator |
| Cytodendritic | `article/A branch-resolved cytoskeletal-dendritic accessibility model of associative memory/` | A branch-resolved cytoskeletal-dendritic accessibility model of associative memory | DANDI 000718/000336/001710 bridges | **Speculative** forward model |
| Fibre bundle | `project/fibre_bundle/` | FB-RN-3…4B | RN3 FAIL; 3F report; 4A complete; 4B QC unauthorized | **Speculative**; not an evidence pillar |

Master ledger: `project/claim_ledger.md`. HELS map: `project/HELS-A/programme_map.md`. Flagship placement targets: `sciencelead/sl_001.md` §§8, 10–11, 16 (P1, P5, P6), S3–S4.

---

## Executive take for flagship (≤15 lines)

This corpus **does not license a positive memory-specific reachability story**. It licenses a sharper *question*: which futures remain accessible under control \(c_t\), and can that be distinguished from occupancy, covariance size, replay identity, or landscape rewriting.

**Control of accessibility.** Thalamic Access supplies the strongest *synthetic* positive: on a *fixed* \(\Phi\), directional \(A_{\mathrm{sig}}\) and \(A_{\mathrm{noise}}\) change short-horizon dispersion, reactivity (\(\alpha<0<\omega\)), finite-time gain, \(J\)–\(Q\) interaction, and a reflected-domain committor interaction. HELS-A supplies the complementary positive: context-conditioned \(A_H\) changes route/committor accessibility while speed-matched scalar gain does not. Both are **operator existence results**, not TRN or hippocampal mechanism validation. RVC survives only as the *minimal* scalar special case (\(A=cI\) or \(\sigma(t)\)); Gate G (E033) and Gate G2 (E046-A) **reject** two stronger “event/rhythm specificity” controllers under matched-energy tests. Those negatives must remain negatives.

**Geometry of possible futures.** Gate R/RD/RC form a three-step falsification ladder: aggregate closure-epoch covariance *calibrates* (R-1), but desired/false and target-private ratios stay \(\approx 1\) under all-trace replay, exclusive replay, and the one coded cross-branch coupling (`translation_budget`). Calibration ≠ directional reachability. Promote the *question* (sl_001 §8.1); do not import the failed directional claims as NDT support.

**History / landscape.** HELS-A answers “can access change without rewriting \(\Phi\)?” (yes, synthetically). It does **not** answer “where does \(\Phi\) come from?” HELS legacy is closed as \(\partial\Phi/\partial t\) evidence. SSMR-2 is the only empirical history-positive here, and it is a *measured-state linear* finding on DANDI 000458, not latent non-Markovianity and not HELS-A1.

---

## Programme-by-programme memos

### Thalamic Access

**What was tested.** Two-operator SDE on frozen `FrozenDoubleWell2D`: \(dX_t = A_{\mathrm{sig}} b_0(X_t)\,dt + A_{\mathrm{noise}}\Sigma_0\,dW_t\), \(\Phi\) held fixed. Staged write-once qualifications in `article/thalamic_access/Directional Access in a Fixed Dynamical Landscape.typ` (peer-review closeout `pr_06_grok46_closeout.md`).

**What passed (internal_validated, synthetic).**

- **TA-0** — truth contracts; identity / scalar-RVC / trace-matched tensor; `results/thalamic_access_ta0/`. *Layer: measurement_contract. Role: supplement.*
- **TA-1** — directional diffusion: mean aligned-vs-opposite margin \(0.262\); max rotation error \(0.0186\) rad; seeds `41101–41108`. Trace-matched anisotropic \(Q\) rotates short-horizon geometry without changing total diffusion power. *Layer: local_dynamics + possible_futures. Role: evidence_matrix (control geometry).*
- **TA-3** — stable reactivity: CR \(\alpha=-0.1647\), \(\omega=0.3317\); scalar CS \(\alpha=\omega=-0.8\); seeds `42101–42108`. *Layer: local_dynamics. Role: evidence_matrix.*
- **TA-2** — instantaneous signal/noise factorization (non-leakage); seeds `43101–43108`. *Layer: local_dynamics. Role: supplement.*
- **TA-4** — deterministic finite-time gain \(G_{\max}(\mathrm{CR})=1.0764\) at \(\tau=0.5\); identity/scalar/unrotated controls \(<1\). *Layer: possible_futures. Role: evidence_matrix.*
- **TA-JQ1** — finite-horizon \(J\)–\(Q\) covariance interaction \(\Delta_{\mathrm{int,max}}=0.1076\). *Layer: possible_futures. Role: evidence_matrix.*
- **TA-5 v1.2** — reflected-domain committor/basin-access interaction; PDE \(\Delta_q^{\mathrm{PDE}}(+)=0.06207\), MC \(0.05554\); seeds `55201–55208`; \(\delta_q=0.05\), \(\varepsilon_q=0.03\). *Layer: possible_futures. Role: evidence_matrix (committor object, not biology).*

**What failed / remains closed.**

- **TA-7A/010** — reflected-domain finite-amplitude recovery: **rejected** (boundary criterion). *Evidence: rejected. Role: supplement (boundary).*
- **TA-7A-ND** — native-domain measurement estimable in DEV only; confirmatory eight-seed pool **unexecuted**. *Evidence: plausible (implementation), not confirmatory. Role: exclude from main-text positives.*
- **TA-7B** — direction-by-condition recovery contrast: **closed**.
- **TRN implements \(A_{\mathrm{sig}}/A_{\mathrm{noise}}\)** — *Evidence: plausible (external physiology only). Role: terminology_only in main text; empirical mapping belongs to ndt-subsystems.*

**Claim ceiling.** A fixed 2-D potential can support distinct access states via directional control of drift and diffusion; scalar gain/variance is a special case, not the general mechanism. **Not** a biological thalamus/TRN result, not MNPS identity, not consciousness.

**Flagship role.** Main-text *computational* anchor for sl_001 §10.3 and P5: “thalamic circuitry = candidate access-control architecture,” not “TRN = variance clamp.” Keep anatomical commitment weak. Cite the two-operator equation as the NDT control specialisation of \(c_t\) acting on \(b\) and \(\Sigma\) with \(\Phi\) frozen.

### HELS-A

**What was tested.** Context as SPD access operator only: \(dX_t = -A_H\nabla\Phi(X_t)\,dt + \sigma\,dW_t\); \(\Phi\) and isotropic noise frozen. Programme map `project/HELS-A/programme_map.md`; article science-lead `article/HELS-A/sciencelead/001.md`; adjudication `project/HELS-A/science_lead/helsa_sl_009.md`. Official seeds `81101–81108`, `82101–82108`, `83101–83108` **unconsumed**. Simulator experiments **closed**.

**What passed.**

- **HELS-A0** (`results/hels_a0_dev/`, seeds `81001–81002`): G1–G8 PASS. On isotropic quadratic, directional access saturates first-passage (\(p_X(H_X)=1\), \(p_X(H_Y)=0\)) while speed-matched scalar does not (\(p_X(aI)=0.5225\)). Classification: `TRUTH_KNOWN_DIRECTIONAL_ACCESS_QUALIFIED`. *Layer: control + possible_futures. Evidence: internal_validated (DEV, two-seed). Role: evidence_matrix.*
- **HELS-A0B** (`results/hels_a0b_dev/`, seeds `82001–82002`): G1–G8 + G4U PASS. Unsaturated double-well committor: \(q_R=0.6535\), \(q_L=0.340\); scalar/baseline \(\approx 0.5\); wrong-context reverses; shuffle collapses. Classification: `UNSATURATED_CONTEXT_CONDITIONED_COMMITTOR_BIAS`. *Same tags.*

**What failed / bounded.**

- **HELS-A0C** (`results/hels_a0c_dev/`): G1–G7 PASS, **G8 FAIL** (\(|\Delta_S|=0.075>0.06\) at `xp1` under full-field dt-halving). Neighborhood \(\Delta_A(x)\approx 0.30\) even off the \(q\approx 0.5\) knife-edge. Classification: `SUPPORTIVE_NEIGHBORHOOD_RESULT_WITH_ROBUSTNESS_GATE_FAILURE`. Do **not** call A0C a PASS. *Evidence: plausible (supportive numbers) + rejected (coded AND-gate). Role: supplement.*
- **HELS-A0D** not opened; **HELS-A1** deferred to ndt-subsystems (“does \(H_t\) predict \(X_{t+h}\) after conditioning on \(X_t,U_t\)?”).
- **HELS legacy** CLOSED as evidence for \(\partial\Phi/\partial t\).
- Hippocampus implements \(A_H\): **explicit non-claim**.

**Claim ceiling.** A fixed stored potential does not uniquely determine route accessibility: \(\Phi\) fixed and \(X_0\) fixed do not imply \(q(X_0)\) fixed when \(A_H\) changes, and that split is not reproduced by matched scalar speed. Two-seed DEV means, not official confirmatory estimates. **Not** hippocampal, thalamic, memory, or NDT-macro.

**Flagship role.** Primary synthetic answer to sl_001 §11 (“where does \(\Phi\) come from?” is *not* yet answered; what *is* answered is that access operators can change futures *without* rewriting \(\Phi\)). Place in S4 as landscape/history *programme*, not mechanism validation. Infrastructure ≠ evidence.

### RVC / rhythm gen2

**What was tested.** Two independent write-permission audits on the Slow-Branch memory simulator. Neither modulates \(\Sigma(t)\) in the original RVC sense; both test *transition-gate* timing on `modulatory_drive`.

- **Gate G / E033** (`project/claim_ledger.md`): periodic consolidation write-gate vs matched-energy / shuffled-timing. **Rejected / frozen.** Does not reopen.
- **Gate G2 / E046-A** (`article/rythm_2nd_gen/`; `results/m3_e046_rhythm_gen2/`): eligibility-triggered binary replay. Absolute threshold \(0.5\) was all-closed (method-limited); outcome-blind median calibration in `sciencelead/002.md` made schedules non-degenerate (6/12 open). Confirmatory rule: +0.01 overlap-advantage margin vs constant energy *and* shuffled timing, plus held-out `chain_overlap`. Validity contracts all passed → **fail, not inconclusive**.

**Numbers (canonical).** Event-triggered overlap advantage \(0.002689\) vs constant energy \(0.003897\) (margin \(-0.001208\)); vs shuffle \(+0.00104\) to \(+0.00133\); held-out mean margin \(-0.001061\). Wrong-trace and all-trace under the same schedule were at least as large (descriptive, not scored). Mechanism seeds 0–3 are bit-identical except shuffle.

**What this does not test.** State-dependent gain, phase-dependent access, noise modulation, EEG biomarkers, biological replay, MNPS, macro NDT. Controller is oracle-latent.

**Claim ceiling.** Event-triggered write permission, under this regime, is not more specific than matched energy or shuffled timing. Combined with E033: two families of *rhythmic/event scheduling of a write gate* fail specificity after energy matching. This **constrains P1**, it does not falsify every possible rhythmic control of \(\Sigma(t)\). Original scalar RVC remains the *minimal* accessibility-control case, not a validated necessity claim.

**Flagship role.** sl_001 §10.2 and P1: keep RVC as minimal \(\sigma(t)\) model; put E033+E046-A in the evidence matrix as **negatives** on event-triggered / periodic *specificity*. S3 supplement. Do not rescue G with G2 or vice versa.

### Reachability family

Shared protocol: six-step closure epoch; oracle latent (eligibility, translation readiness, structural accessibility); isotropic \(\Sigma_0=10^{-6}I\); `saturation_avoiding`; covariance recursion \(\Sigma_{h+1}=A_h\Sigma_h A_h^\top\) (\(Q=0\)) vs 2,000 MC rollouts. Direction test requires desired/false or target-private ratio \(\ge 1.5\).

**Gate R / E044** (`article/Reachability_over_closure_epoch/`).

- **Passed:** R-1 aggregate calibration (Frobenius error \(0.060\)–\(0.102\); 90% coverage \(0.901\)–\(0.907\)); R-4 seed stability.
- **Rejected:** R-3 memory-specific directional reachability. Analytical ratios \(0.997\)–\(1.000\); MC \(0.974\)–\(0.988\).
- **E044R diagnostic:** near-one ratio already at horizon 1 (mean \(0.9999\)).
- **`dev_canonical`:** predicted rank-deficient inconclusive (96/96 controls).
- *Layer: possible_futures + measurement_contract. Evidence: internal_validated (calibration PASS; direction rejected). Role: main_text_anchor for the **question** and the **negative**.*

**Gate RD / E045** (`article/Directed_reachability_under_exclusive_replay/`).

- **Passed:** aggregate calibration and seed stability under exclusive / wrong / all / empty replay.
- **Rejected:** target-private vs other-private specificity. Analytical \(0.995\)–\(1.009\); MC \(0.987\)–\(1.006\); below \(1.5\) and below \(0.25\) control margin.
- **Diagnostic (E044R2):** true Jacobian is block-diagonal per branch when `translation_budget=0.0` (default in every R/RD-tested regime). Replay identity cannot create cross-branch directional variance under this architecture.
- Not pristine prospective confirmation (smoke test saw near-neutral ratio before the full matrix). Does not revise Gate R.

**Gate RC / E047** (`article/Coupled_Resource_Reachability_over_Closure_Epoch/`).

- Activates the one coded coupling channel: \(P'_b = P_b\cdot B/\sum_i P_i\) when \(\sum P_i>B\).
- **RC-0:** cap binds at tight sweep values \(0.5\), \(1.0\); \(2.0\)/\(4.0\) never activate; composed operator **rank deficient** at every active value (structural null of sum-then-rescale; numpy default-tol rank bug corrected, diary 056).
- **RC-1/RC-4:** reduced-rank calibration PASS.
- **RC-2 rejected:** desired/false \(0.996\)–\(1.000\) analytical, \(0.937\)–\(1.010\) MC; exclusive-replay secondary ratios \(\approx 1.008\), margin \(0.01\)–\(0.014 \ll 0.25\).
- Does not revise R or RD. Rank deficiency is a diagnostic, not a veto of RC-1/RC-2.

**Claim ceiling.** In this simulator, a calibrated closure-epoch covariance cloud is **not** memory-specific directional reachability, even under exclusive replay and even with the coded resource cap on. The *question* of finite-horizon reachability is live; these *answers* are negative under the tested isotropic protocol.

**Flagship role.** sl_001 §8.1: promote the reachability *question* and the occupancy ≠ reachability ≠ traversability ≠ consciousness fence. Put R/RD/RC in the evidence matrix as a **negative ladder**. Exclude any prose that treats replay, coupling, or calibration as positive NDT directional support.

### SSMR / history

**SSMR-1** (`article/SSMR/`). Truth-known discrete simulator. Four-way split: predictive information \(\neq\) representational retention \(\neq\) finite recoverability \(\neq\) estimator-specific recovery. Oracle compression retained \(\approx 97\%\) of S1/S2 information (net displacement retained S2 but only \(11.4\%\) of S1). Finite Laplace tables failed S1. Nested estimator crossed the current-state floor **and** produced a stable S0 history gain in the Markov control → **1D-0 specificity FAIL**. Programme closed after 1D-0. *Layer: epistemic + measurement_contract. Evidence: internal_validated. Role: supplement (P6 measurement hygiene).*

**SSMR-2** (`article/SSMR-2/`; `results/ssmr_2a_1_dandi000458_history_specificity/`). DANDI 000458 mouse stimulation EEG; frozen 3-D chart (amplitude, spectral entropy, beta); OLS; LOSO; \(r=0.5\); \(N=21\). Class `SPECIFIC_HISTORY_PASS`.

- **Gate H PASS:** median \(\Delta_H=+0.069\); 17/21; \(p=0.0036\). True recent history improves post-stim prediction beyond \((X_t,U_t)\).
- **Gate X PASS at exact minimum:** median \(\Delta_\times=+0.026\); 15/21; \(p=0.0392\). Becomes 14/20 unresolved if predeclared `sub-521887` is dropped. Slow-state sensitive (2A-1A \(\tau\) diagnostic: near-time residue remains).
- **Gate W:** positive wrong-history advantage did not meet resolution; `PASS_CONTROL` / UNRESOLVED.
- Not latent non-Markovianity, not MNPS/NDT, not consciousness, not estimator rescue, not SSMR-2A-2. SSMR-2B (arousal/running/pupil control) unrun.

**Claim ceiling for P6.** Measured-state history can add linear predictive information beyond current chart+input on this EEG contract; specificity is threshold-level and slow-state-limited. This is the nearest *empirical* contact for sl_001 P6, **not** a HELS landscape-writing result and **not** HELS-A1.

**Flagship role.** H as evidence-matrix row for P6; X as limitation, not a second primary. Keep in S4 / measurement-contract discussion. Do not collapse SSMR-2 into HELS-A.

### Slow-branch / cytodendritic

**Slow Branch** — thin copy in this repo. **Canonical intake is `summaries/06_cytodend_slow_branch_micro.md`** (`I:\AAA_PYTHON_REPOS_BACKUP\cytodendaccessmodel\`). Simulator-first: fast access vs slow structural variable \(M_b\). E017–E022R: overlap-branch slow writing (SIG-A \(=0.128\)), linking gain (SIG-B \(=0.240\)), targeted rescue; nine comparator classes fail the joint profile; bounded write–replay regime; hub-overlap over-links. DANDI analyses are S3 exploratory bridges, **not** primary evidence. Molecular/cytoskeletal code: **NOT SUPPORTED**. *Layer: control (structural gate) + possible_futures (linking routes). Evidence: internal_validated (simulator); plausible (biology). Role: supplement — micro end of a dashed micro–meso–macro chain, not a flagship biological proof.*

**Cytodendritic forward model** (`article/A branch-resolved cytoskeletal-dendritic accessibility model of associative memory/`). Same \(M_b\) idea plus DANDI 000718/000336/001710 as “observable bridges.” Explicitly a **speculative** implementation hypothesis (microtubules, local translation, mitochondria as candidate space). Do **not** promote to core NDT biology. *Evidence: speculative. Role: exclude from main mechanism; terminology_only if dendrites are mentioned.*

**Claim ceiling.** Slow branch-level accessibility is an *executable discriminator* in the memory simulator that later reachability and rhythm gates inherit. It is not a demonstrated cytoskeletal memory code and does not convert R/RD/RC negatives into biological falsifications.

### Fibre bundle (status)

`project/fibre_bundle/`. **Not an evidence pillar.** Speculative geometric language for chart/fibre splitting.

| Stage | Status |
| --- | --- |
| FB-RN-3 | `FAIL_POSITION_DEPENDENT_HORIZONTAL_NOT_DEMONSTRATED` (`results/fbrn_3_position_dependent_horizontal/`) |
| FB-RN-3D | `DIRECT_SEPARATION_DETECTED` |
| FB-RN-3E | `DESCRIPTIVE_RDM_DISPLACEMENT_REPORT` |
| FB-RN-3F | `MECHANISM_DISCRIMINATION_REPORT` (execution-complete; not a mechanism PASS) |
| FB-RN-4A | `FORMAL_BASELINE_BRANCH = COMPLETE`; frozen **flat** negative-control baseline |
| FB-RN-4B | source-only PASS; test/QC **not authorized** (`sl_043.md`); holonomy / non-flat / RDM re-analysis prohibited |
| Remainder \(E\) | formally ratified as finite-step nonlinear remainder; **\(E\neq 0 \not\Rightarrow F\neq 0\)**; \(F_\lambda=0\) exactly on the declared connection |

**Claim ceiling.** Formal synthetic remainder accounting on a flat connection. No biological fibre bundle, no MNPS, no NDT validation.

**Flagship role.** `exclude` from evidence matrix; `terminology_only` if a later draft needs a “charts vs fibres” metaphor. Do not cite RN3–4B as reachability or control results.

---

## Claims table

| Programme | Claim | Evidence class | Layer | Flagship role | Claim ceiling |
| --- | --- | --- | --- | --- | --- |
| TA | Fixed \(\Phi\), directional \(A_{\mathrm{noise}}\) rotates short-horizon dispersion at matched trace (TA-1) | internal_validated | local_dynamics / possible_futures | evidence_matrix | 2-D synthetic; not TRN |
| TA | Non-normal \(A_{\mathrm{sig}}\) yields \(\alpha<0<\omega\) while scalar stays contractive (TA-3) | internal_validated | local_dynamics | evidence_matrix | Local Jacobian at declared points only |
| TA | Finite-time \(G_{\max}(\mathrm{CR})>1\); controls \(<1\) (TA-4) | internal_validated | possible_futures | evidence_matrix | Deterministic local-linear; not FAR |
| TA | Signal–noise orientation interaction \(\Delta_{\mathrm{int,max}}=0.1076\) (TA-JQ1) | internal_validated | possible_futures | evidence_matrix | Frozen horizon family; not stochastic paths |
| TA | Reflected-domain committor interaction (TA-5 v1.2) | internal_validated | possible_futures | evidence_matrix | Not native-domain; not TA-7B |
| TA | Native-domain finite-amplitude recovery (TA-7A-ND confirmatory) | speculative (unexecuted) | possible_futures | exclude | DEV-only; no contrast licensed |
| TA | TA-7A/010 reflected FAR | rejected | possible_futures | supplement | Boundary-limited failure |
| TA | Biological TRN implements the two operators | plausible | control | terminology_only | External physiology; no perturbation map in this repo |
| HELS-A0 | Directional \(A_H\) saturates first-passage; scalar does not | internal_validated | control / possible_futures | evidence_matrix | Two-seed DEV; official seeds unconsumed |
| HELS-A0B | Unsaturated committor bias; wrong-context reverses; shuffle collapses | internal_validated | control / possible_futures | evidence_matrix | One geometry; not hippocampus |
| HELS-A0C | Neighborhood split robust under coded G8 | rejected (gate) / plausible (numbers) | possible_futures | supplement | Supportive field; AND-gate FAIL |
| HELS legacy | \(\partial\Phi/\partial t\) from HELS infrastructure | rejected | control | exclude | Closed as landscape-writing evidence |
| HELS-A1 | Hippocampal \(H_t\) predicts \(X_{t+h}\mid X_t,U_t\) | speculative (deferred) | epistemic | exclude | Lives in ndt-subsystems; not this corpus |
| RVC / G | Periodic write-gate is more specific than matched energy (E033) | rejected | control | evidence_matrix | Frozen fail; not a \(\sigma(t)\) test |
| RVC / G2 | Event-triggered eligibility gate beats matched energy/shuffle (E046-A) | rejected | control | evidence_matrix | Valid fail; margin \(-0.0012\); does not rescue G |
| RVC scalar | \(\sigma(t)=\sigma_{\min}+\sigma_0(1-r(t))\) as *minimal* access control | plausible | control | main_text_anchor | Special case of \(c_t\) on \(\Sigma\); not necessity |
| Gate R | Closure-epoch covariance calibrates vs MC (R-1) | internal_validated | measurement_contract | evidence_matrix | Aggregate cloud only; latent oracle |
| Gate R | Desired/false structural reachability (R-3) | rejected | possible_futures | main_text_anchor (negative) | Ratios \(\approx 1\); isotropic \(\Sigma_0\) |
| Gate RD | Exclusive replay → target-private reachability | rejected | possible_futures | evidence_matrix | Block-diagonal Jacobian at budget 0 |
| Gate RC | `translation_budget>0` → direction-specific reachability | rejected | possible_futures | evidence_matrix | Calibration holds; ratios still \(\approx 1\); singular cap |
| SSMR-1 | Predictive information \(\neq\) finite recoverability \(\neq\) specificity | internal_validated | epistemic | supplement | 1D-0 specificity fail; closed |
| SSMR-2 H | True recent EEG history improves linear \(Y_{t+h}\) prediction | internal_validated | state / epistemic | evidence_matrix | Measured 3-D chart; not latent |
| SSMR-2 X | History *specificity* vs matched wrong history | internal_validated (knife-edge) | epistemic | supplement | 15/21 exact minimum; slow-state open |
| Slow Branch | Replay-dependent \(M_b\) joint SIG profile vs comparators | internal_validated | control | supplement | Simulator; not molecular code |
| Cytodendritic | Cytoskeleton implements \(M_b\) | speculative | control | exclude | Forward model; open-data bridges only |
| Fibre bundle | Position-dependent horizontal demonstrated (RN3) | rejected | epistemic | exclude | FAIL_POSITION_DEPENDENT_HORIZONTAL |
| Fibre bundle | Remainder \(E\) is curvature/holonomy | rejected | epistemic | exclude | \(E\neq 0\not\Rightarrow F\neq 0\) |
| Fibre bundle | FB-RN as NDT evidence pillar | speculative | epistemic | exclude | Status-only; QC unauthorized for 4B |

---

## What this does to old NDT story

- **RVC:** keep as the *minimal* accessibility-control case (\(c_t\) acting as scalar \(\sigma(t)\) or \(A=cI\)). Gen1 (E033) and gen2 (E046-A) **reject event-triggered / periodic write-gate specificity** after energy matching. Do not equate those negatives with “rhythm does nothing”; they constrain *this controller family*, and they do not test the original variance-schedule object. P1 remains open for other rhythmic channels (gain, \(\Sigma\) geometry, phase-dependent access) and closed for the two tested write-gates.
- **TRN:** weaken anatomical commitment. Deepen the *computational* access-control concept (two operators; directional \(\Sigma\) and non-normal \(b\)). External thalamic physiology stays `established_external` motivation; simulator TA results stay `internal_validated` and non-biological. P5 should be stated as a future perturbation prediction, not as a completed mapping.
- **Landscape \(\Phi\):** HELS-A shows that *access without landscape rewriting* is a real synthetic mechanism class. That is **not** an answer to “where does \(\Phi\) come from?” HELS legacy is closed as \(\partial\Phi/\partial t\) evidence. Treat HELS as a landscape/history *programme* (sl_001 §11.4 already: plausible/speculative pending direct validation). Do not let A0/A0B drift into hippocampal implementation.
- **Reachability:** promote the *question* (which nearby futures remain available; covariance recursion; committor as destination geometry). Do **not** import failed memory-specific or directional claims as positive NDT support. The strongest reachability results in this repo are **negatives**. TA-5 is a *fixed-landscape committor interaction*, not a memory-trace reachability result; do not conflate it with Gate R.

---

## What NOT to import

- Gate G / G2 as evidence that “rhythmic control works” or that RVC is confirmed.
- Gate R-1 calibration as memory-specific reachability, meso-to-macro coupling, or consciousness geometry.
- Gate RD exclusive replay, or Gate RC `translation_budget`, as positive directional-access results.
- HELS-A0C as a PASS; official HELS confirmatory numbers (unconsumed seeds).
- HELS-A as hippocampal mechanism, landscape writing, or \(\partial\Phi/\partial t\).
- TA-7A-ND DEV, TA-7B, or “TRN = these operators.”
- SSMR-1D-0 nested-estimator gain as history-specific recovery.
- SSMR-2 Gate X as a robust specificity pillar; SSMR-2 as latent HELS-A1.
- Slow-branch DANDI bridges as primary biological validation of \(M_b\).
- Cytodendritic manuscript as core NDT biology.
- Fibre-bundle RN3–4B, remainder \(E\), or holonomy language as NDT evidence.
- Occupancy, entropy, traversability, controllability, or MNPS location as substitutes for reachability.
- Any identification of reachability, committor, or access operators with consciousness.
- O1/J1 local-dynamics recovery (owned by summary `01`).
- Chart-space / observed Jacobians from Gate O / O-Ca (E046/E048) as reachability support (those are a different, already-failed observation-map line).

---

## Suggested manuscript placement

Targets in `articles/NoeticDiffusionTheory_v2/sciencelead/sl_001.md`:

| sl_001 locus | Import | How |
| --- | --- | --- |
| §8 Geometry of possible futures | Reachability *question*; TA-4/TA-JQ1/TA-5 as synthetic objects; R/RD/RC negatives | Centrepiece: calibration ≠ direction; committor ≠ volume; fence occupancy/traversability/consciousness |
| §10 Control of accessibility | Two-operator TA equation as \(c_t\) on \(b,\Sigma\); RVC as \(c_t\) on scalar \(\Sigma\); G/G2 negatives | Keep RVC minimal; TA as candidate architecture |
| §11 History and landscape | HELS-A0/A0B as access-without-rewriting; HELS-A1/SSMR-2 as open empirical P6 | Infrastructure ≠ \(\partial\Phi/\partial t\) |
| §16 P1 | E033 + E046-A | Failure mode already written: “rhythmic scheduling adds no held-out explanatory value” — true here for *write-gate specificity*, not yet for \(\sigma(t)\) |
| §16 P5 | TA computational positive; biological mapping untested | Failure mode: thalamic variables vs arousal/gain — **not tested in this repo** |
| §16 P6 | SSMR-2 Gate H; SSMR-1 specificity hygiene; HELS-A1 deferred | Do not claim HELS landscape writing |
| S3 Rhythmic and thalamic | RVC formula; TA staged table; G/G2 negatives | Alternatives: matched energy, scalar gain, shuffle |
| S4 History and learning | HELS-A programme map; Slow Branch as simulator substrate; SSMR split | Replay/hysteresis remain open; cytodendritic out |

---

## Open questions

1. **Does any non-scalar, non-write-gate rhythmic \(c_t\) (phase-dependent \(\Sigma\), state-dependent gain) beat matched-energy controls?** G/G2 left this untested. (control / speculative)
2. **TA-7A-ND confirmatory and TA-7B:** can native-domain finite-amplitude recovery, and a direction-by-condition contrast, be qualified? Currently closed/unexecuted. (possible_futures)
3. **Biological P5:** do thalamic/TRN perturbations change accessibility geometry after arousal/gain controls? Requires ndt-subsystems mapping, not more FrozenDoubleWell runs. (control / speculative)
4. **HELS-A1:** does measured hippocampal state predict future neural state after \(X_t,U_t\)? Deferred. Two-seed DEV A0/A0B must not be treated as a substitute. (epistemic)
5. **P6 robustness:** does SSMR-2 Gate X survive independent slow-state/arousal matching (SSMR-2B)? Present X is threshold-level. (epistemic / measurement_contract)
6. **Reachability under a different perturbation family:** anisotropic \(\Sigma_0\), non-normalizing coupling, or control-set (not covariance) reachability were explicitly *not* tested; R-3/RD/RC negatives do not forbid those questions, and they do not license them either. (possible_futures)
7. **Where does \(\Phi\) come from?** HELS-A froze the *access* answer and closed the legacy *writing* claim. Landscape learning, replay-driven \(\partial\Phi/\partial t\), and hysteresis remain unanswered. (control / speculative)
8. **Committor as an empirical NDT object:** TA-5 and HELS-A0B are synthetic; C2 finite-data committor recovery is closed in the local-dynamics line (summary `01`). Do not smuggle a measured committor into the flagship. (measurement_contract)

---

*Intake complete for control / history / reachability. Negatives stay negative. RVC is the minimal case. TRN is a candidate architecture. HELS is a programme. Reachability is a question whose best current answers in this simulator are no.*
