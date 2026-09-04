# 06 — cytodendaccessmodel: slow branch-level accessibility (micro end of the chain)

Canonical source (this intake): `I:\AAA_PYTHON_REPOS_BACKUP\cytodendaccessmodel\`

Primary article: `article/Slow Branch-Level Accessibility as a Structural Constraint on Memory Linking/`

A thin copy also lives under `J:\repos\ndt-simulator\article\Slow Branch-Level Accessibility as a Structural Constraint on Memory Linking\` and was only sketched in summary `02`. **This file is the intake.** Use `02` as a pointer, not as the source of truth.

Architecture filter: **State geometry → Local dynamical geometry → Geometry of possible futures → Control of accessibility.**

Sciencelead placement (`sl_1.md`): slower structural accessibility is an **explicitly speculative substrate bridge**, not a core validated NDT pillar. Compact-summary §3 already writes the same boundary: the micro→MNPS/MNJ/reachability map is a forward model, not required for macro inference.

---

## Inventory

| Source | Used for |
| --- | --- |
| `README.md`, `CLAIMS_TO_EXPERIMENTS.md` | Evidence tiers; reviewer path; DANDI firewalled |
| `article/.../v2_claim_ledger.md` | C01–C15; explicit non-claims C-NC1–C-NC3 |
| Manuscript `.txt` / `.typ` (abstract, equations, results, discussion) | Claim surface and \(M_b\) formalization |
| `S3_Appendix.txt` | DANDI 000718 / 000336 / 001710 as *downstream* bridges only |
| Companion `article/A branch-resolved cytoskeletal-dendritic accessibility model of associative memory/` | Older/broader conceptual paper; DANDI more in-main than Slow Branch allows |
| `project/science_lead/014_article_polish3.md` | Submission-ready freeze: simulator-first, no cytoskeletal code |
| `nmd-analysis` compact_summary §3 | Speculative \(\Psi: Z_t \to x_t^{(\mathrm{mem})}\) export into MNJ/reachability |
| `summaries/02_…` Slow-branch subsection | Prior thin mention; superseded here |

Not treated as primary: `exp001–exp016` legacy; DANDI `000871`; fibre-bundle; ndt-simulator Gate R/G2 (they *inherit* this substrate but are not this paper’s claims).

Public record: GitHub `NoeticDiffusion/cytodendaccessmodel`; Slow Branch snapshot DOI `10.5281/zenodo.20813821` (S3 appendix also cites `10.5281/zenodo.19498499` for pipeline snapshot — do not conflate).

---

## Executive take for flagship (≤15 lines)

This is the **micro** end of a still-theoretical micro→meso→macro accessibility chain.

At branch scale, NDT-style accessibility is already executable: fast access \(A_b^f\) opens a dendrite moment-to-moment, while a slower phenomenological variable \(M_b\) biases which branches remain recruitable after replay. Effective access is the product \(A_b = A_b^f A_b^s(M_b)\). Memory linking is operationalized as shared slow accessibility, not as a synaptic-weight identity. In the locked four-branch / two-trace simulator (E017–E022R), replay-dependent slow writing reproduces a *joint* profile — overlap-branch strengthening, linking gain, perturbation-sensitive loss, targeted rescue — that nine comparator classes do not reproduce. Robustness is a bounded write–replay regime; hub overlap over-links; shuffled replay loses specificity as allocation space grows.

That is **internal_validated model discrimination**, not dendritic biology and not MNPS. \(M_b\) compresses a plural family (spine geometry, actin, microtubules, local translation, transport, mitochondria). The paper’s own non-claims forbid a unique cytoskeletal memory code and forbid treating DANDI as primary evidence.

For NDT 1.0 the import is conceptual: **accessibility control is not only thalamic/rhythmic at meso–macro scales; it can be stated at the dendritic branch.** Compact-summary §3 then *speculatively* exports \(Z_t=\{x_b,s_i,M_b,E_b,P_b\}\) through \(\Psi\) into mesoscopic memory charts and, further, into metric/Jacobian/reachability objects. That export is **not demonstrated** by Slow Branch, DANDI 000458, or NMD. Flagship role: one control-layer subsection + one Figure-4 panel, with the bridge dashed. Do not make this a fourth empirical anchor.

---

## Two manuscripts in the same repo (do not collapse)

| Paper | Role | DANDI | Flagship use |
| --- | --- | --- | --- |
| **Slow Branch-Level Accessibility as a Structural Constraint on Memory Linking** | Claim-disciplined, simulator-first. Primary ladder E017–E022R. | S3 only; C-NC3 **NOT SUPPORTED** as primary | **Cite this.** |
| **A branch-resolved cytoskeletal-dendritic accessibility model of associative memory** | Broader research-programme paper. Same \(M_b\) idea; biology + simulator + open-data in one ladder. | In-main as “observable bridges” (000718 modest PRI; 000336 above-null inter-plane coupling; 001710 SparseKO vs Cre) | `terminology_only` / lineage. Do not let its more promotional DANDI wording override Slow Branch’s firewall. |

---

## Microstate and equations (importable objects)

Operational split (keep):

- **Fast access** — cue, local dendritic/spine state, context.
- **Slow structural accessibility** \(M_b\) — persistent branch bias; “writing” means persistent simulator-state update, not molecular content storage.
- **Memory linking** — shared structural accessibility between traces.

Minimal Slow Branch formalization (phenomenological):

\[
A_b(t)=A_b^f(t)\,A_b^s(t),\qquad
\tau_x\dot x_b=-x_b+A_b(t)\bigl[I_b(t)+R_b(t)\bigr]
\]

\[
\tau_E\dot E_b=-E_b+\varphi(x_b,I_b),\qquad
\tau_P\dot P_b=-P_b+\rho_{\mathrm{replay}} r_b(t)+\rho_\nu\nu(t)
\]

\[
\dot M_b=\eta E_b(t)P_b(t)W(t)\,(M_{\max}-M_b)-\lambda_M M_b+\varepsilon_b(t)
\]

\[
R_\mu(t)=\sum_b a_{\mu b} A_b(t) x_b(t),\qquad
L_{\mu\nu}(t)=\sum_b a_{\mu b}a_{\nu b} M_b(t)
\]

Compact-summary §3 is a *slightly different* write equation (thresholded eligibility × consolidation, plus thermal noise). For the flagship, cite **Slow Branch (1)–(7)** as the article-local micro model, and treat compact-summary’s \(\Psi\), \(G_{\mathrm{MNPS}}\approx P^\top G_{\mathrm{access}}P\), and block-Jacobian coupling as the **speculative meso/macro export**, not as Slow Branch results.

| Compact-summary export | Status for flagship |
| --- | --- |
| \(Z_t\to x_t^{(\mathrm{mem})}\) | speculative |
| \(J_t^{(\mathrm{mem})}\), reachability \(\Sigma_t^{(h)}\) from micro | speculative; **not** licensed by E017–E022R |
| \(G_{\mathrm{MNPS}}(X,Z)\), \(\Phi_{\mathrm{access}}\) | speculative; do not identify with NMD `/mnps_3d` |
| Block Jacobian from dendritic \(G_{\mathrm{access}}\) | speculative; do not equate to empirical `/jacobian/J_hat` |

---

## Primary simulator ladder (internal_validated)

Canonical protocol: 4 branches, 2 traces, 1 overlap branch. Deterministic E017/E018 (`structural_noise=0`). Signatures:

| ID | Object | Canonical value | Diagnostic? |
| --- | --- | --- | --- |
| SIG-A | overlap-branch \(M_b\) writing | 0.1281 (> 0.02) | yes (mechanistic) |
| SIG-B | linking gain after consolidation | 0.2397 (> 0.05) | yes |
| SIG-C | context separation | 0.1545 | **no** — architectural / fast gating |
| SIG-D | linking vs recall under overlap damage | 20.98 pp | **no** — geometry can produce it |
| SIG-E | targeted vs generic rescue (normalized) | 1.57 (> 0.10) | yes (with SIG-A/B) |

**Joint profile, not any single signature.** Comparators that fail the joint profile: fast-context-only, replay-without-structure, random slow drift, fixed allocation, Hebbian weight-only, soma/global-gain, eligibility-only, resource-only, shuffled replay. Hebbian can produce large *output-level* linking (B1) without branch-specific structural writing or rescue of a written \(M_b\).

Robustness: write × replay heatmap 70.7% joint pass; overlap below ~0.40 fails; eligibility lifetime × timing gap is a tag-decay boundary. Scaling 4–32 branches: canonical/strong-overlap pass; weak-overlap fails as designed; **hub-overlap writes but over-links** (specificity fail). E022R: shuffled-replay apparent n=4 match is a sampling artefact (~7% of full-model gSIG-A; → 0 by n=32). Identity-preserving replay is required for scalable specificity.

**Claim ceiling.** Replay-dependent slow branch-level writing better reproduces the tested joint SIG profile than the tested comparators, inside a bounded write–replay and non-hub motif regime. Simulator result, not biology.

| Tag | Value |
| --- | --- |
| Layer | `control` (structural gate) + `possible_futures` (which linking routes remain) |
| Evidence class | `internal_validated` |
| Flagship role | `supplement` (main-text: one short control-layer paragraph) |
| Claim ceiling | Executable micro-accessibility discriminator; not MNPS, not consciousness, not cytoskeleton. |

---

## S3 open-data bridges (do not promote)

These test *downstream observables* of an accessibility hypothesis. They do **not** observe \(M_b\). Slow Branch C-NC2 / C-NC3: not primary evidence.

| Dataset | Question | Retained ceiling | Recoverability |
| --- | --- | --- | --- |
| DANDI **000718** | NeutralExposure core units enriched in later offline high-synchrony events? | Modest enrichment above matched-window and registration-shuffle; sits on a strong generic burst background | Level 1 association, bounded |
| DANDI **000336** (OpenScope dendritic coupling) | Cross-plane coupling above circular-shift null, and below within-plane? | All pairs above null (z ≈ 4.0–5.2); strict cross < both-within only clean in supplementary cross-area pair | Level 1; partial Level-2 “access constraint” |
| DANDI **001710** | SparseKO (postsynaptic membrane-fusion / structural-write candidate) lower cross-day place-code stability? | SparseKO vs Cre: mean 0.262 vs 0.337, permutation p=0.009; vs Ctrl directional, not null-separated (p=0.099); channel-sensitive | Level 1 group contrast; not \(M_b\) |

**Flagship role:** `exclude` from main-text anchors; optional S3/S4 footnote that micro-hypothesis has *contactable* observables. Do not analogize 000718 offline events to RVC spindles, or 000336 planes to MNPS axes, or SparseKO to NDT \(\Phi\)-writing.

---

## How this sits on the micro–meso–macro chain

Dashed = speculative / not demonstrated as a unique identification.

```text
MICRO (this paper, internal_validated simulator)
  Z_t = {x_b, s_i, M_b, E_b, P_b}
  A_b = A^f · A^s(M_b)
  linking L_μν from shared M_b
        |  speculative Ψ  (compact_summary §3)
        v
MESO (summaries 02–03; mixed)
  population / LFP / TRN geometry / HELS eligibility
  DANDI 000458: Level-1 contact, Level-4 operator FAIL
        |  NMD chart (summary 05)
        v
MACRO (summaries 04–05)
  MNPS 3D/9D, MNJ, gated reachability, spindles, coma
```

**What the chain currently licenses**

1. Accessibility is scale-general *as a question*: branch routes, thalamic operators, EEG charts, clinical futures.
2. Slow × fast factorization at micro is the same *logical* move as RVC (minimal \(\Sigma(t)\)) and TA (\(A_{\mathrm{sig}},A_{\mathrm{noise}}\) on fixed \(\Phi\)): control can change futures without rewriting content.
3. History dependence at micro is replay-and-eligibility writing of \(M_b\), which is the dendrite-scale analogue of HELS’s “where does \(\Phi\) come from?” — but HELS-A showed access can change *without* rewriting \(\Phi\). Do not collapse \(M_b\)-writing into HELS landscape writing.

**What the chain does not license**

- Identification of \(M_b\) with MNPS \(m,d,e\).
- Identification of \(A_b\) with NMD `/jacobian/J_hat` or `/stochastic_reachability`.
- Using Gate R/RD/RC negatives (ndt-simulator, same code family) as biological falsification of dendritic accessibility — those gates test *closure-epoch covariance directionality* in the inherited simulator, not Slow Branch’s SIG profile.
- Using Gate G/G2 (event-triggered replay specificity fail) to erase Slow Branch: G2 tests a *write-gate schedule* against energy-matched controls; Slow Branch tests whether *any* identity-preserving replay-dependent \(M_b\) write beats comparators. Different questions. Keep both: Slow Branch SIG profile can pass while rhythmic *timing specificity* fails.

---

## Relation to neighbouring NDT programmes

| Neighbour | Relation | Do not do |
| --- | --- | --- |
| RVC | Fast/slow access split is kindred; RVC is scalar \(\sigma(t)\) at meso–macro | Do not say spindles write \(M_b\) |
| Thalamic Access | Both: control operators on a frozen landscape/content layer | Do not say TRN implements \(M_b\) |
| HELS-A | Complementary: HELS-A = access without \(\partial\Phi/\partial t\); Slow Branch = slow structural bias that *is* a write | Do not treat HELS-A0 as dendritic confirmation |
| HELS real-data (`03`) | Still eligibility, not landscape writing | Do not merge CRCNS/HELS-A1 with Slow Branch DANDI |
| Cytodendritic companion | Implementation-hypothesis / programme paper | Do not let it set the claim ceiling |
| compact_summary §3 | Speculative micro→macro coupling | Keep the BOUNDARY paragraph verbatim in spirit |

---

## Claims table

| Object | Claim | Evidence class | Layer | Flagship role | Claim ceiling |
| --- | --- | --- | --- | --- | --- |
| \(A_b=A^f A^s(M_b)\) | Fast/slow access factorization is a usable micro control law | internal_validated (simulator) / plausible (biology) | control | supplement | Phenomenological; not a unique molecule |
| Joint SIG-A/B/E | Replay-dependent \(M_b\) writing needed vs tested comparators | internal_validated | control / possible_futures | supplement | E017–E022R; non-hub, bounded write–replay |
| SIG-C, SIG-D | Present but non-diagnostic | internal_validated | epistemic | supplement | Fast gating / overlap geometry |
| Hub / weak-overlap / shuffled-replay | Informative failure modes | internal_validated | possible_futures | supplement | Specificity is topology- and identity-dependent |
| Cytoskeletal / microtubule code | Unique molecular write | rejected (C-NC1) | control | exclude | Explicit non-claim |
| DANDI as validation of \(M_b\) | Direct biological support | rejected (C-NC2/3) | epistemic | exclude | S3 bridges only |
| \(\Psi:Z\to\) MNPS/MNJ | Micro identifies macro charts | speculative | epistemic | terminology_only | compact_summary forward model |
| Dendrites as NDT substrate | Candidate implementation of accessibility control | plausible | control | supplement (one paragraph) | sl_1 “speculative substrate bridge” |

---

## What NOT to import

- Cytoskeletal memory-code language in the abstract or §1.
- DANDI 000718/000336/001710 as flagship empirical anchors (those remain spindles, coma, 000458).
- Equating Slow Branch linking \(L_{\mu\nu}\) with EEG reachability cones or committor \(q(x)\).
- Using the companion cytoskeletal paper’s in-main DANDI wording.
- Treating ndt-simulator copies as a second independent result.
- Promoting compact-summary block-Jacobians as empirically recovered.

---

## Suggested manuscript placement

- **Main §10 (biological control), short subsection** “Slow structural accessibility at dendritic scale”: factorization \(A^f A^s\); \(M_b\) as phenomenological latent; simulator-first ceiling; dashed link to meso–macro.
- **Figure 1 or 4:** one small panel under Control — dendrite with overlap branch + \(M_b\) — visually parallel to thalamus/rhythm/history, with a dashed arrow into \(c_t\) / \(G\) / transition gates, **not** into MNPS coordinates.
- **S1 math:** optional restatement of (1)–(7) as a micro example of \(c_t\) acting on access, distinct from RVC’s \(\sigma(t)\).
- **S4 / history:** contrast with HELS-A (access without rewriting \(\Phi\)) and with G2 (timing specificity fail).
- **Figure 5 evidence matrix row:** Slow Branch | control + futures | internal_validated simulator | not biology | S3 DANDI bounded.
- **Not** §§2–8 core dynamics; those stay chart/SDE/Jacobian/diffusion/reachability.

---

## Open questions

- Is \(\Psi\) even the right export, or should micro remain a *constraint on which meso routes exist* without a chart map?
- Can a later study connect \(M_b\)-style slow bias to HELS landscape \(\Phi(x\mid H_t)\) without category drift?
- Branch-resolved longitudinal linking + perturbation + rescue (the paper’s own future test) is the biological ceiling; nothing in NMD currently measures it.
- Keep notation: Slow Branch \(\dot M_b=\eta E P W (M_{\max}-M_b)-\lambda_M M_b\) vs compact-summary thresholded form — pick one for S1 or show both as variants.
