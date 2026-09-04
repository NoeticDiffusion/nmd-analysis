# 01 — ndt-simulator: local dynamics and truth-known recoverability

Architecture filter (sciencelead freeze): **state geometry → local dynamical geometry → geometry of possible futures → control of accessibility.**

NDT here is *state-dependent control → structured stochastic dynamics → geometry of accessible neural futures*. MNPS is an observation chart, not the theory. NeuralManifoldDynamics (NMD / MNDM) is a versioned empirical implementation, not NDT. Canonical process (conceptual): \(dX_t = b(X_t,t;c_t)\,dt + \Sigma(X_t,t;c_t)\,dW_t\), optional split \(b = -G\nabla\Phi + u_{\mathrm{nc}}\).

Terminology freeze (`nmd-analysis/project/extensions_ndt/1.md`, article `pr_04`): drop **MNJ-vNext**. Use **local diffusion geometry** and **Jacobian-derived summaries** \((\alpha,\omega,\Delta_{\mathrm{react}},G_{\mathrm{peak}})\). **MNJ** = Jacobian in an MNPS chart only.

This memo covers local dynamics and recoverability only. Thalamic Access, HELS-A, RVC gen-2, and related control/reachability articles are assigned to summary `02`.

---

## Inventory

Read (abstracts, sciencelead, READMEs, claim ledgers, selected effect-summary headers — not full 80-page manuscripts):

| Source | What was used |
| --- | --- |
| `nmd-analysis/articles/NoeticDiffusionTheory_v2/sciencelead/sl_1.md`, `sl_001.md` | Architecture freeze; §§3.4, 6–8, 14.1; S1 math; Figure 5 map |
| `nmd-analysis/project/extensions_ndt/1.md` | MNJ / MNJ-vNext terminology correction |
| `ndt-simulator/project/claim_ledger.md` | O1, J1, J2, F1, JQ1, O2/O2b, C2-CL0, Gate Q/E038–E043, Gate O/E046–E051, Gate J-O |
| `article/Truth-Known Recovery of Local Diffusion Geometry and MNJ vNext Summaries/` | README, sciencelead README, `.typ` abstract + S1 methods (folder name is historical; title is Jacobian-derived) |
| `results/orthogonal_dynamics_stage_{o1,j1,j2}_gate/README.md` | Frozen held-out pass/fail and envelopes |
| `article/observatory_robustness/` | README, sciencelead `001.md`/`006.md`, `.typ` abstract |
| `article/Separable Levels of Observability…/` | README, `.typ` abstract, S4 claim boundaries |
| `article/Closure-Signature Recoverability…/` | README, `.typ` abstract (current title: *Recoverability of Multi-Step Memory-Model Dynamics…*), S6 claim boundaries |
| `project/orthagonal_dynamics/commitor/sl_020.md` | C2-G1 STOP; 2D recovery paused; C3 blocked |
| `results/orthogonal_dynamics_c2_cl0_closure_audit/` | README + claim ledger (no-new-seed synthesis) |
| `results/orthogonal_dynamics_stage_o2b_gate/README.md` | 1D committor replacement PASS |
| `project/orthagonal_dynamics/015_o1_o3_program_archive.md`, `017_stage_o3_preregistration.md`, diary `074`/`075` | O3 / FAR status conflict (see below) |
| `project/fibre_bundle/science_lead/sl_043.md`, `claim_ledger/008_fbrn_4b_claim_ledger.md` | Programme status only |
| Diaries `153` (2026-08-25 O1/J1/J2 pr_02), `155` (Zenodo packaging); `pr_04` nomenclature in ledger | Claim status unchanged after packaging/nomenclature |

Not read in full: HELS-A, thalamic_access, rythm_2nd_gen manuscripts; fibre-bundle sciencelead stack beyond status; 80-page Typst bodies except abstracts/S1/S4/S6.

---

## Executive take for flagship (≤15 lines)

This repo’s unique contribution is **estimator discipline under inspectable truth**, not biology and not MNPS identity.

**Local dynamics.** On declared constant-linear SDEs, Stage **O1** recovers the local diffusion tensor \(a(x)\) (O1-A/O1-B PASS; O1-C maps support/timestep/bandwidth/noise breakdown). Stages **J1/J2** recover Jacobian-derived \(\alpha,\omega,\Delta_{\mathrm{react}}\) and show they are **not interchangeable**; J1 also recovers simulator-only \(G_{\mathrm{peak}}\) under the J1-A contract, but later **F1 fails**, so finite-time ordered propagation is **not** promoted with the instantaneous trio. J2 shows observation-noise envelopes are **estimator-specific**. All of this is Type-D simulator validation.

**Possible futures.** Truth-level committor information can exist where a 1D projection loses it (C2-S0). **1D** local-law committor recovery passes only after replacing the failed O2 estimator (**O2b PASS**; **O2 FAIL frozen**). **2D finite-sample recovery is CLOSED** (C2-CL0): three estimator families failed; held-out `13201–13210` unconsumed; **C3 not authorized**; **do not implement `committor/v2` in MNDM**. Finite-amplitude resilience (O3/FAR) is **not a confirmed flagship pillar** (preregistered; no matching `results/` archive or claim-ledger PASS row; diary 075 says not run).

**Epistemic / measurement contract.** The four-level recoverability ladder (association → mechanism discrimination → latent-order preservation → dynamical-operator identification) is the flagship’s inference spine. Memory-simulator results show the ladder is **not monotonic**: charts can discriminate mechanisms while failing order or operator ID; observation maps and local observed-Jacobian fits **break** previously recovered closure signatures (Gate O / E046–E051). Success at one level does not license a stronger claim.

---

## Claims table

| Object | Claim | Evidence class | Layer | Flagship role | Claim ceiling | Negative/limit |
| --- | --- | --- | --- | --- | --- | --- |
| Spectral/numerical abscissa, \(\log m\), Itô \(a=\Sigma\Sigma^\top\) | Standard continuous-time linear-algebra / SDE objects | established_external | local_dynamics | terminology_only | These symbols are textbook; the simulator does not invent them. | Not empirical neural estimators |
| Canonical NDT SDE \(dX=b\,dt+\Sigma\,dW\) | Conceptual generator for NDT 1.0 | plausible | local_dynamics | main_text_anchor | Flagship may *state* this as the working process class, not as a fitted neural SDE. | Not identified on data |
| O1-A/O1-B | Local diffusion tensor \(a\) and orientation summaries recovered on both frozen linear-SDE systems | internal_validated | local_dynamics | main_text_anchor | Under `N=5000`, `dt=1e-3`, held-out seeds `(11…111)`, \(E_F\le0.08\), eigenvalue error \(\le0.02\), \(\rho(A_b^D)\ge0.95\). | Linear 2D SDE only; not MNPS, not biology |
| O1-C envelope | Recovery degrades at low support, coarse \(\lvert\alpha\rvert dt\), bad bandwidth, and observation noise | internal_validated | measurement_contract | evidence_matrix | Descriptive envelope, not a frozen universal threshold. | Naive noise estimator catastrophically biased even at \(\sigma_{\mathrm{obs}}=0.01\); bias correction only near-latent at \(\sigma_{\mathrm{obs}}\le0.01\) for this burst design |
| O1 gauge | Orthogonal rotation leaves \(a\)-summaries invariant to float tol; nonuniform rescaling does not | internal_validated | measurement_contract | supplement | Diffusion geometry is chart-gauge sensitive under anisotropic rescaling. | Do not treat recovered \(a\) as coordinate-free without a declared chart |
| O1 stage synthesis | O1 PASS with a wide validity envelope relative to the gated reference | internal_validated | local_dynamics | evidence_matrix | Does not validate Axis B/C, 2D committor, macro NDT, or NMD ingest. | Cite `results/orthogonal_dynamics_stage_o1_gate/` not scouting |
| O1.5 smoke | Nonlinear drift / state-dependent \(a\) / one nonlinear observation remain descriptively compatible | plausible | local_dynamics | exclude | Smoke only; no frozen threshold. | Do not promote as generalized O1 |
| J1 conversion | Fitted discrete \(A_d\) needs \(\log m(A_d)/dt\), not \((A_d-I)/dt\), when integration is finer than sampling | internal_validated | local_dynamics | supplement | Naive Euler conversion is a bias, not a shortcut. | Pairing at the integration step produced the opposite pattern (Euler artifact) |
| J1-A | \(\alpha,\omega,\Delta_{\mathrm{react}},G_{\mathrm{peak}}\) recovered on 8 constant-linear systems | internal_validated | local_dynamics | main_text_anchor | Held-out seeds `(211…311)`; abs tols 0.10 / rel \(G_{\mathrm{peak}}\) 0.20; `N_IC=8`, `dt=1e-3`, \(\sigma=0.02\). | Constant 2D linear only; \(G_{\mathrm{peak}}\) is a propagator functional, not an instantaneous summary |
| J1-B | Protected dissociations: \(\alpha\neq\omega\); rotation \(\neq\) reactivity; \(\omega\) match can leave \(G_{\mathrm{peak}}\) separated | internal_validated | local_dynamics | main_text_anchor | “Stable” is not a sufficient phenotype: modal decay, instantaneous growth, and finite-time gain can split. | Three matched pairs only |
| J1-C | Observation noise dominates J1 discrete-transition failure; also low \(n_{\mathrm{ics}}\), coarse \(dt\), short trajectories | internal_validated | measurement_contract | evidence_matrix | No J1 noise-correction estimator; errors-in-variables at fine \(dt\). | Do not translate \(\alpha/\omega\) from noisy fine-sampled positions without a noise-aware estimator |
| J1 nomenclature | Calling J1 quantities “MNJ-vNext” is rejected | rejected | epistemic | terminology_only | Quantities are generic Jacobian summaries until \(J\) is an MNPS Jacobian. | Historical gate folders still say MNJ-vNext |
| J2-A/B/D | Clean recovery PASS; noise-aware envelopes wider than OLS `E0`; documented `E-NMD-contract` PASS inside \(\sigma_{\mathrm{obs}}\le0.05\) | internal_validated | local_dynamics | evidence_matrix | Envelopes are per-estimator, not a single J2 number. | `E-NMD-contract` ≠ literal NMD ingest; `E2-EM` never converged (`em_convergence_rate=0`) |
| J2-C | `E0` bias is directional (keeps negative sign, loses small-positive \(\omega\)); IV/EM fragility is estimator-specific | plausible | measurement_contract | supplement | 3 seeds / P1 only; do not freeze a grey-zone half-width. | Descriptive |
| F1 ordered local-\(J\) propagation | **FAIL** (T3 cosine margin 0.0048 < 0.01; T5 \(d_{\mathrm{resp}}\) 0.0617 > 0.05) | rejected | possible_futures | main_text_anchor | Instantaneous Jacobian recovery does **not** license ordered finite-time \(\Phi\) / \(G_{\mathrm{peak}}\) promotion. | F0 scout remains scout-only |
| JQ1-A/B | Literal MNDM Jacobian pipeline ≠ `E-NMD-contract`; synthetic replay fails frozen error bounds (56/56 rows) | rejected | measurement_contract | main_text_anchor | Simulator J1/J2 success does not transfer to the literal NMD ingest. | Block empirical \(\alpha/\omega\) promotion via MNDM until a new qualification |
| MNJ / MNPS homology | Simulator coordinates are not empirical MNPS | rejected | state | exclude | Do not identify \(X_t\) with \((m,d,e)\). | Ledger: unsafe / unsupported |
| Recoverability ladder (4 levels) | Association ≠ mechanism discrimination ≠ latent-order ≠ operator ID | internal_validated | epistemic | main_text_anchor | This is the flagship inference rule, instantiated in the memory-simulator series. | Operational observability ≠ Kalman / observability-rank theorems |
| Separable Levels (E029–E037) | Oracle FD consistency and some mechanism discrimination can pass while Level-3 order and Level-4 operator ID fail | internal_validated | epistemic | main_text_anchor | Chain inversion is a robust Level-3 negative; lag-embedded BranchSummary has structurally null \(A_{\mathrm{resp}}\) (Gate J-O FAIL); J+ positive control shows the pipeline can detect a planted echo. | Motif-limited; hub not a latent audit; Gate H not a general Level-3 pass |
| Gate G (E033) | Periodic write-gate timing did not beat matched-energy / shuffled controls on the predeclared overlap-advantage endpoint | rejected | control | exclude | Rhythm-as-necessity fails in this identity-modulatory family. | Belongs primarily to summary `02`; keep as ladder Level-2 negative only |
| Gate Q `dev_canonical` (E038/E038R) | AND-rule FAIL; \(A_{\mathrm{epoch}}\) rank-deficient (saturation); cue-inclusive Q4 **sign reversal** | rejected | epistemic | evidence_matrix | High-drive default is not a valid operator-recovery regime; epoch definition can invert depth-order sign. | Do not average epoch definitions |
| Saturation-avoiding regime (E039/E039c) | Joint weak-drive (`sleep_gain=0.0`, reduced replay/cue/encoding) restores full rank; at \(n_{\mathrm{pert}}=192\), 36-D `lag_embedded` passes Q1–Q4 on 3 motifs × 2 epoch defs | internal_validated | epistemic | evidence_matrix | Reportable Gate Q is **regime-qualified**, not default consolidation. | Q2 position baseline degenerate; not operator ID; not `dev_canonical` |
| E040–E042 matrix vs summary | Positive entrywise correlation can coexist with ~zero-estimator Frobenius error and with Q4/Q6 failure; `branch_summary` \(\hat A_{\mathrm{epoch}}\equiv 0\); block-average dim-match **worse** than front-\(k\) | internal_validated | epistemic | supplement | Same-shape association is not operator identification. | Chart-specific; ridge-sensitive scale |
| E043 latent mechanisms | True \(A_{\mathrm{epoch}}\) separates three matched-endpoint pairs on canonical; `eligibility_only` ≡ `frozen_structure` under this protocol; some charts **over-separate** vs truth | internal_validated | epistemic | supplement | Latent non-identifiability and observer amplification are both assets. | Canonical only; causal isolation of `replay_gain` incomplete |
| Gate O / E046 | One-pole BranchSummary filter + noise **rejects** clean-chart Q1/Q4 transfer (clean \(\rho_{\mathrm{Q1}}\) 0.467–0.513 vs transformed 0.144–0.347) | rejected | measurement_contract | main_text_anchor | Observation maps can destroy a previously recovered closure relation. | Synthetic map, not biological calcium |
| E047 (observatory) | Calcium-like / BOLD-like **formulas** meet numerical contracts | internal_validated | measurement_contract | supplement | Formula correctness ≠ biological observation. | Do not reinterpret E046 |
| E048–E049 | Gate O-Ca method-limited (matched clean Q4 fails); Q4 estimator-sensitive (2/16 draws) | rejected | measurement_contract | evidence_matrix | Clean-chart Q4 is not a stable prerequisite here. | Floor artifact in `depth` (>95% floor in 12–36D Jacobians) |
| E050–E051 | Q4-K numerically qualified but 0/16 clean recovery; loss localized to **local observed-Jacobian estimation** | rejected | measurement_contract | main_text_anchor | Operator-ID failure can sit *before* epoch composition. | Do not tune Q4-K or calcium; new identifiability study required |
| O2 1D committor | FAIL (MC agreement on B1 seeds 543, 576) | rejected | possible_futures | evidence_matrix | Protected B0/B1 dissociation cannot rescue failed recovery. | Frozen; do not overwrite with O2b |
| O2b 1D committor | PASS (oracle-grid err 0.00105, RMSE 0.00110, B0/B1 sep 0.2860) | internal_validated | possible_futures | supplement | 1D resolved-grid local-law committor is recoverable under that contract. | Replacement estimator only; no NMDM / high-D / empirical |
| C2-S0 | Same-\(x_1\) states can have different 2D committors (`D_corridor=0.322419`) | internal_validated | possible_futures | main_text_anchor | Existence of transition information ≠ recoverability. | One corridor landscape; truth-level only |
| C2 SQ-A / OP–OK / G1 | Finite-sample 2D recovery **rejected** under tested families; program **CLOSED** (`sl_020`, C2-CL0) | rejected | possible_futures | main_text_anchor | Under tested support/lag/observation/Galerkin contracts, C2-S0 information was not recovered to the preregistered standard. | Not universal 2D impossibility; held-out unconsumed |
| C3 / MNDM `committor/v2` | Not authorized | rejected | possible_futures | exclude | Do not open 3D or empirical committor from a failed 2D finite-data program. | New scientific branch would need a new question |
| O3 / FAR | Preregistered (`017`); Axis-C scout exists; **no confirmed held-out archive in `results/`**; ledger has no O3 PASS row; diary 075: not run. File `015_o1_o3_program_archive.md` claims PASS — **do not trust without archive reconciliation** | speculative | possible_futures | exclude | FAR is a conceptual NDT object, not a validated simulator gate in the current evidence set. | Another agent covers TA finite-amplitude work |
| Fibre-bundle FB-RN | 4B source-only PASS; test/QC **not authorized** (2026-08-28); RN3 position-dependent horizontal **FAIL**; 4A is a frozen flat negative-control baseline | speculative | possible_futures | exclude | Geometric programme, not a flagship evidence pillar. | Do not dump the programme into NDT 1.0 |

---

## Equations / objects to import

### Process and local law

\[
dX_t = b(X_t,t;c_t)\,dt + \Sigma(X_t,t;c_t)\,dW_t,\qquad
a(x,t)=\Sigma\Sigma^\top,\qquad
J(x,t)=\partial b/\partial x.
\]

Optional drift split \(b=-G\nabla\Phi+u_{\mathrm{nc}}\) is **conceptual** (plausible), not an O1/J1 estimand.

Drift (established_external definition): \(b(x)=\lim_{\Delta t\to0}\mathbb{E}[X_{t+\Delta t}-X_t\mid X_t=x]/\Delta t\).

### Local diffusion geometry (O1 objects)

\[
D_{\mathrm{total}}=\mathrm{tr}(a),\quad
d_{\mathrm{diff}}=\mathrm{tr}(a)^2/\mathrm{tr}(a^2),\quad
c_{\mathrm{diff}}=\lambda_{\max}(a)/(\mathrm{tr}(a)+\varepsilon),\quad
A_b^D=(b^\top a b)/(\lVert b\rVert^2\mathrm{tr}(a)+\varepsilon).
\]

**Gauge warning:** O1 coordinate audit — orthogonal rotation invariant to float tolerance; **nonuniform rescaling is not invariant**. Identifiability of \(a\) is chart-relative.

### Jacobian-derived summaries (J1/J2 objects)

\[
\alpha(J)=\max_i\mathrm{Re}\,\lambda_i(J),\qquad
\omega(J)=\lambda_{\max}\bigl((J+J^\top)/2\bigr),\qquad
\Delta_{\mathrm{react}}=\omega-\alpha.
\]

\(\Delta_{\mathrm{react}}\) is a **derived, non-normality-sensitive gap**, not a complete non-normality measure.

\[
G_{\mathrm{peak}}(J;T)=\max_{0<t\le T}\lVert e^{Jt}\rVert
\]

is a **finite-time propagator functional**, not an instantaneous matrix summary. J1-A recovers it in-simulator; **F1 fails** ordered estimated-\(J\) propagation — keep \(G_{\mathrm{peak}}\) out of the main \(\alpha,\omega,\Delta_{\mathrm{react}}\) trio.

Continuous/discrete: \(A_d=\mathrm{expm}(J\,dt)\), \(J=\mathrm{logm}(A_d)/dt\). Naive \((A_d-I)/dt\) is a contrast, not the contract.

**MNJ:** \(J_{\mathrm{MNPS}}=\partial\dot x/\partial x\) in an MNPS chart only. Simulator \(J\) is not MNJ.

### Recoverability ladder (epistemic spine)

| Level | Question | Typical objects in this repo |
| --- | --- | --- |
| 1 Association | Does an observable covary with a latent/target? | Q1, \(\rho\), entrywise matrix correlation |
| 2 Mechanism discrimination | Can matched-endpoint alternatives be told apart? | Gate F-style pairs; E043 matrix separation |
| 3 Latent-order preservation | Is a predefined ranking preserved (correct sign)? | Q4 / Q4-K; Gate H; chain inversion |
| 4 Dynamical-operator identification | Does a local/composed operator predict response/evolution? | Gate J-O \(A_{\mathrm{resp}}\); composed \(A_{\mathrm{epoch}}\); O1 \(a\); J1 \(J\) |

**Consequence for NDT:** MNPS separation can be meaningful at Levels 1–3. Jacobian, diffusion, reachability, and committor claims require Level 4 (or a declared weaker ceiling).

### Committor (possible futures; import as object + stop)

For basins \(A,B\), \(q(x)=\mathbb{P}(\tau_B<\tau_A\mid X_0=x)\). Import the **existence/recoverability dissociation**, not a 2D estimator.

---

## Negative results that MUST appear

These are assets: they show NDT’s inference discipline.

1. **C2 closed.** Truth can hide transition information off a 1D projection (C2-S0). SQ-A: 0/2592 candidate rows. Analogue OP/OL/OK: no robust lag/\(k\) band. Unregularized Galerkin G1: 0/3 bases eligible on DEV; held-out `13201–13210` reserved_unconsumed. **Not** “2D committors are impossible.” **Do** say: tested families failed; C3 blocked; no `committor/v2` in MNDM.

2. **O2 FAIL vs O2b PASS.** First 1D local-law gate failed MC agreement; replacement resolved-grid estimator passed. Keep both. Success of O2b does not reopen C2.

3. **F1 FAIL.** J1 recovery of local summaries ≠ ordered finite-time propagator recovery. Do not promote \(\Phi\)-derived metrics or empirical \(G_{\mathrm{peak}}\).

4. **JQ1 FAIL.** Documented `E-NMD-contract` ≠ literal MNDM ingest; synthetic replay misses frozen bounds. Simulator validation does not baptize the empirical pipeline.

5. **Gate J-O FAIL (E037/E037R).** Lag-embedded BranchSummary has structurally null response block on the tested channel; planted J+ control shows the detector works. Level-4 operator ID failed for that chart.

6. **Chain inversion (Gate H / Separable Levels).** A plausible summary can reverse latent order. Level-2 success does not imply Level-3.

7. **Observation-map ladder (E046–E051).** Clean closure recovery does not survive the declared calcium-like+noise map (Gate O reject). Q4 `depth` is floor-dominated in 12–36D. Q4-K fixes the floor then still recovers 0/16 clean draws; E051 localizes loss at **local observed-Jacobian estimation**.

8. **Saturation / rank deficiency (E038).** Default high-drive composed operator is exactly rank-deficient via `_clamp01` saturation. Reportable Q results require a **saturation-avoiding** weak-drive regime with `sleep_gain=0.0` — not “sleep consolidation validated.”

9. **Epoch-definition sign reversal (E038R Q4).** Depth-order sign is not invariant across closure-epoch definitions under rank-deficient `dev_canonical`.

10. **Matrix association ≠ operator ID (E040–E042).** Modest entrywise \(\rho\) with Frobenius error ~1 (zero-estimator scale); `branch_summary` all-zero \(\hat A_{\mathrm{epoch}}\).

Do **not** recast any of these as near-passes or as biological calcium/BOLD/NDT failures.

---

## What NOT to import into the flagship

- Branded **MNJ-vNext**, “mesoscopic” as a property of 2D linear SDEs, or MNPS homology from simulator coordinates.
- Failed gates presented as positive (O2, F1, JQ1, C2 recovery, Gate O, Gate J-O, E038 AND-rule, E044/E045 directional reachability — the last pair is mainly summary `02`).
- **Unvalidated MNDM translation** of \(\alpha/\omega/\Delta_{\mathrm{react}}\) or any `committor/v2`.
- **O1.5** smoke as a generalization of O1.
- **Fibre-bundle programme** as evidence (status: geometric R&D; 4B tests unauthorized; RN3 horizontal FAIL).
- **O3/FAR** as a validated gate until `results/` + claim ledger agree (current conflict: `015` vs diary 075 / missing archive).
- Thalamic Access, HELS-A, RVC gen-2, Gate G rhythm necessity as *this* memo’s pillars (other agent / summary `02`).
- E047 calcium/BOLD **formula** checks as biological observation models.
- Scouting rows (MNJ-vNext 4-matrix scout, F0, C2-S0 beyond existence, Axis-C FAR scout) as held-out gates.
- `dev_canonical` Gate Q “almost” — it is FAIL / rank-deficient.
- Treating E039c `lag_embedded` Q1–Q4 as Level-4 operator identification.

---

## Suggested manuscript placement

Map to `sl_001` (and `sl_1`) architecture:

| sl_001 locus | Import from this repo |
| --- | --- |
| **§3.4 Four levels of recoverability** | Ladder as frozen inference rule; Separable Levels + Closure-Signature as the worked example; “success at one level does not authorize a stronger claim.” |
| **§6 Local dynamical geometry** | \(J,\alpha,\omega,\Delta_{\mathrm{react}}\); J1-B dissociations as the conceptual centre (“stable is not a phenotype”); \(\log m\) conversion in S1; **not** MNJ. |
| **§6.7 Finite-time amplification** | Define \(G_{\mathrm{peak}}\); cite J1-A recovery **and** F1 FAIL in the same breath. |
| **§7 Local diffusion geometry** | \(a,D_{\mathrm{total}},d_{\mathrm{diff}},c_{\mathrm{diff}},A_b^D\); O1-A/B PASS; orthogonality of \(J\) vs \(a\) as interpretation, O1 as estimator support. |
| **§8 Geometry of possible futures** | Committor as *object*; C2 existence/recoverability split; O2/O2b 1D story in one paragraph; **stop** before 2D/3D/MNDM. Reachability negatives (E044/E045) → summary `02` unless a one-line cross-ref is needed. |
| **§14.1 Truth-known simulation** | Primary empirical-methods subsection: O1, J1, J2 envelopes, F1, JQ1, Gate O/E051, C2-CL0. Purpose sentence already in sl_001: “Can candidate mathematical quantities recover their known latent targets?” |
| **S1 Mathematical definitions** | Canonical SDE, \(a\), \(J\), \(\alpha,\omega,\Delta_{\mathrm{react}}\), \(G_{\mathrm{peak}}\), ladder, committor; gauge/identifiability notes; MNJ reservation. |
| **S2 Measurement contract** | Estimator families (`E0`, `E-NMD-contract`, IV, EM); observation-noise envelopes; “documented contract ≠ literal ingest.” |
| **Figure 5 evidence map** | Row **truth-known simulator**: local dynamics = validated (O1/J1/J2 within envelope); diffusion = validated (O1); reachability = null/bounded (defer to `02`); destination/committor = **null** for 2D finite-sample, **bounded** for 1D O2b; mechanism = not this repo’s biology. Cell coding must show **validated vs null vs not tested**, not a wall of green. |
| **Main text (short)** | One boxed dissociation: *information can exist in truth and still fail finite-sample recovery* (C2) **and** *local \(J\) recovery does not imply finite-time \(\Phi\)* (F1) **and** *chart association does not imply operator ID* (Gate J-O, E051). |

Do not let §6–8 become a catalogue of experiment IDs. IDs belong in 14.1 / S6 evidence ledger / Figure 5 footnotes.

---

## Open questions / missing evidence

1. **Nonlinear / state-dependent local law.** O1.5 is smoke. No held-out O1 analogue for nonlinear drift or state-dependent \(\Sigma(x)\).
2. **Time-varying \(J(x,t)\).** J1/J2 are constant-linear. Switching-order F0/F1 did not qualify estimated sequences.
3. **Literal NMD ingest.** JQ1 failed; no authorized retry with isolated components.
4. **2D (or chart-space) committor.** Closed. Any sequel is a new branch (regularized Galerkin / diffusion maps / reduced-state) with a new question — not a C2 rescue.
5. **O3/FAR archive reconciliation.** Runner `gate_o3_resilience.py` exists; `015` claims PASS; diary 075 and missing `results/orthogonal_dynamics_stage_o3_gate/` say otherwise. Until reconciled, FAR stays out of the evidence matrix.
6. **Observation-map identifiability.** E051 diagnoses local observed-Jacobian loss but does not isolate chart vs fit vs sample diversity. No authorized follow-up.
7. **`dev_canonical` operator recovery.** Unsolved; saturation-avoiding results do not license the default high-drive regime.
8. **Fibre geometry.** Speculative relative to NDT 1.0; 4B tests unauthorized as of 2026-08-28.
9. **Empirical MNPS Jacobian.** No internal_validated path from this repo. Plausible future: apply \((\alpha,\omega,\Delta_{\mathrm{react}})\) *after* a validated MNPS \(J\). That is not done here.

**Claim-status note (Aug 2026 diaries):** Packaging/Zenodo (`153`, `155`) and nomenclature (`pr_04`) did **not** change O1/J1/J2/C2/F1/JQ1 scientific status. Fibre-bundle 4B remains source-only. Do not silently upgrade O3 from `015`.
