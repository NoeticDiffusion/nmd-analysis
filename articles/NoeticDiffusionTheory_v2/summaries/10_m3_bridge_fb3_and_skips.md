# 10 — m3-bridge: FB3 color geometry and skip inventory

Canonical source (this intake): `J:\repos\m3-bridge\`

Primary article: `articles/FB3 Color Geometry/`

Canonical Typst title: *A Frozen fMRI Analysis of Reported Color Similarity and No-Report Neural Geometry*. Older/export title (`.txt`): *Individual Color-Similarity Structure Corresponds to No-Report Neural Geometry Beyond Controls*. Short title: FB3 Color Geometry.

Date of this cartography: **2026-08-30**. Numbers below are taken from the manuscript, S1–S3, S5–S6, `project/qualia/claim_ledger.md`, the dated E001 amendment (2026-08-13), and FB3-RV1 (2026-08-17).

Architecture filter: **State geometry → Local dynamical geometry → Geometry of possible futures → Control of accessibility.**

Recoverability ladder: (1) association → (2) mechanism discrimination → (3) latent-order preservation → (4) dynamical-operator identification. Success at one level does not license a stronger claim.

**This is fibre-bundle / qualia / no-report RSA geometry, not MNPS and not NDT accessibility.** Do not identify color RDMs with MNPS \((m,d,e)\), with \(K^h\), with Jacobian/reachability, or with a consciousness meter. Frozen analysis ≠ independent biological replication.

---

## Tags (programme-level)

| Field | Value |
| --- | --- |
| Layer | `state` (relational RSA of BOLD patterns). Not `local_dynamics`, not `possible_futures`, not `control`. |
| Evidence class | `internal_validated` for the frozen dual-high-pass E001 correspondence; `rejected` as NDT/MNPS/\(K^h\)/consciousness validation; fibre-as-ontology remains `speculative` |
| Flagship role | **`evidence_matrix`** (one neighboring-programme / boundary row). Main-text NDT empirical use: **`exclude`**. Fibre/section/quotient vocabulary, if mentioned at all: **`terminology_only`**. |
| Claim ceiling | Under one frozen dual-high-pass ranked-control contract, a 30-person cohort shows a small participant-level residual correspondence between reported color-similarity RDMs and no-report ventral-visual crossnobis geometry; this does not license NDT, MNPS, accessibility, or phenomenal identity. |

---

## Inventory

| Source | Used for |
| --- | --- |
| `articles/FB3 Color Geometry/A Frozen fMRI Analysis of Reported Color Similarity and No-Report Neural Geometry.typ` | Canonical manuscript (abstract, methods, results, discussion, FB-RN/NDT boundary) |
| `Individual Color-Similarity Structure Corresponds to No-Report Neural Geometry Beyond Controls.txt` | Earlier title/export; same endpoint numbers; weaker “beyond controls” wording than the Typst draft after science-lead revision |
| S1 methods, S2 data, S3 QC/robustness, S5 glossary, S6 changelog | Cohort flow, participant rhos, hashes, RV1, remaining not-run items |
| `peer_review/pr_1.md` | Pre-RV1 review: permutation-null concern; 19/30 vs 30/30 LOO; internally frozen ≠ preregistered |
| `project/qualia/claim_ledger.md` §4 / §4a | Programme ledger: historical STOP, defects A/B, dated corrected PASS |
| `project/qualia/science_lead/001.md`, `002.md` | Finish confirmation → focused FB3 paper; **do not call this Fibre Bundle v3 validation**; not the NDT-Q article; CSQ out |
| `articles/FB3 Color Geometry/sciencelead/` | Template README only; no numbered verdict files |
| `project/qualia/results/FB3_H1_ds005684_E001_full_recompute_frozen30_20260812/` | Fresh non-cached run + independent reproduction |
| `project/qualia/results/FB3_H1_ds005684_RV1_20260817/` | Reviewer-validation batch (null, true LOO, high-pass, reliability) |

**Skip inventory (confirmed present; no new empirical NDT summary):** `articles/NDT/`, `articles/Slow Branch-Level Accessibility as a Structural Constraint on Memory Linking/`, `articles/compendium/`, `articles/aa_template/`, `articles/iblreach2/` plus `articles/DANDI/` backends. See § Skip list.

Article-folder README is still the `aa_template` copy; do not treat it as a result.

---

## Executive take for flagship (≤15 lines)

FB3 is a **human no-report RSA paper** on OpenNeuro `ds005684` v1.0.1 (Hirao et al., 2025): nine colors, report vs no-report, four sessions, frozen bilateral ventral-visual ROI. The biological unit is the **participant**, not the 36 RDM cells. After two implementation defects were corrected against an already-frozen specification, a fresh 30-person recomputation passed the conjunctive E001 rule (median partial \(\rho = 0.0922684\), one-sided \(p = 0.0179964\), 30/30 LOO-median diagnostic). An independent endpoint script reproduced those numbers. RV1’s residual-label null survived (\(p = 0.0172\)); a FMRIPrep-cosines-only high-pass sensitivity did not (\(\rho = 0.0232\), \(p = 0.3113\)).

That licenses **Level-1 relational correspondence under one preprocessing contract**. It does **not** license NDT. There is no MNPS chart, no local Jacobian, no reachability cone, no \(K^h\), no \(c_t\), no RVC, and no recoverability above association. No-report trials remove the explicit similarity response; they do not isolate phenomenology or measure consciousness. The LOO diagnostic is a median-stability check (LOO medians take only two values); **19/30** participant rhos are positive (range \(\approx -0.345\) to \(0.323\)). Computational reimplementation is not a second cohort.

Science-lead (`001.md`, `002.md`) and the manuscript itself: theory-relevant to Fibre-Bundle Relational Neurodynamics, **not theory-validating**. Plausible reading: content may be relational across realizations rather than a shared neural point. Speculative: fibre/section/quotient. Keep CSQ out. Flagship role: **one evidence-matrix boundary row**, not a fourth empirical anchor.

---

## FB3 memo (numbers from sources)

### Question and contract

Core question (Typst): under the frozen ranked-control and dual-high-pass contract, does no-report ventral-visual fMRI geometry show participant-level residual correspondence with reported color-similarity geometry?

Primary statistic (S1 / eq. in manuscript): partial Spearman via average ranks of target \(B_i\), no-report neural RDM \(N_i\), and four controls — physical circular hue \(H\) (angles \([0,40,\ldots,320]^\circ / 180\)), leave-one-participant-out group-rating \(G_i\), report-trial neural \(R_i\), response-magnitude \(M_i\). Headline: median \(\rho_i\). Null: 5,000 within-participant neural color-label permutations, seed `20260731`, sorted subject IDs. Plus-one \(p\). ROI: Harvard–Oxford 25% Occipital Fusiform + posterior Temporal Fusiform + Lingual Gyrus, MNI 2 mm, no spatial smoothing. Neural object: signed crossnobis across sessions 1–2 vs 3–4 (Walther et al., 2016). TR = 1 s.

PASS rule: \(n \ge 29\); median \(\rho_i > 0\); one-sided \(p < 0.05\); \(\ge 29\) positive LOO medians. The executed LOO omitted each \(\rho_i\) from the already-computed median; it did not refit \(G_i\) or the GLMs.

### Cohort

| Stage | n | Source |
| --- | --- | --- |
| Source participants | 35 | S2 / manuscript Table |
| Motion/output QC | 33 | `sub-02`, `sub-09` failed (FD-censor \(> 20\%\) on runs) |
| No_Report coverage | 33/33 | all nine colors in both halves |
| Frozen E001 cohort | 30 | historical list locked; `sub-33`–`sub-35` not added |
| Post-GLM exclusions | 0 | all frozen participants retained |

### Historical as-run vs corrected amendment

| Statistic | Original as-run (2026-08-12) | Corrected full run (2026-08-13) | Frozen criterion |
| --- | --- | --- | --- |
| Median partial \(\rho\) | 0.0604 | 0.0923 (exact 0.09226840438409781) | \(> 0\) |
| One-sided permutation \(p\) | 0.0918 | 0.0180 (exact 0.017996400719856028) | \(< 0.05\) |
| Positive LOO medians | 30/30 | 30/30 | \(\ge 29\) |
| Cohort | 30 | 30 | \(\ge 29\) |
| Gate | **STOP** | **PASS** (dated amendment) | all required |

Defect A (ledger): permutation stream followed incidental dict/glob order (non-deterministic \(p\); earlier write \(p = 0.0844\) vs on-disk 0.0918). Defect B: controls left unranked; 2×2 decomposition says B is decisive (median \(0.0604 \to 0.0923\); \(p\) into \(0.017\)–\(0.018\)). Independent reproduction: `independent_reproduction: true`; SHA-256 of fresh result `718B1F4E…2F0B`, independent check `F91258FD…D9F8` (S2 / decision JSON). Independent script did **not** re-estimate first-level GLMs.

Participant-level (S2 independent reproduction): **19/30** positive, 11 negative; range `sub-12` \(-0.3445570675\) to `sub-25` \(0.3226440716\). LOO medians take only two values: \(0.0697523192\) and \(0.1147844895\) (pr_1 / S2). Illustrative figure participant: `sub-05` (rho nearest the median).

### RV1 (2026-08-17; does not replace E001)

| Check | Result | Status in RV1 ledger |
| --- | --- | --- |
| Residual-label (Freedman–Lane-style) null | median \(\rho = 0.0923\); \(p = 0.0171966\) (reported 0.0172) | SURVIVES_RV1_NULL |
| True group-control LOO refit | 30/30 positive medians | diagnostic only |
| Behavioral split-half Spearman | 0.895; \(n=27\) complete 36-pair halves; no imputation | DESCRIPTIVE |
| FMRIPrep-cosines-only high-pass | median \(\rho = 0.0231876\) (0.0232); residual-label \(p = 0.311338\) (0.3113); 30/30 retained | NOT_SUPPORTED as preprocessing-invariant |
| Neural within-half Mahalanobis reliability (that sensitivity) | median Spearman 0.088 | DESCRIPTIVE |

S3 remaining **Not run** (cannot upgrade PASS): behavioral half-subset, hue-test summary, report-neural as target, three-mask Holm ROI, participant sign-flip, alternative magnitude co-permutation, new ROIs/targets, topology/nonlinear RSA.

### Interpretation ceiling (manuscript + science-lead)

**Internal validated:** no-report ventral-visual relational geometry contains participant-level residual information about reported color-similarity structure under the specified dual-high-pass ranked-control contract, after computational reimplementation.

**Plausible:** compatible with FB-RN / Fibre Bundle v3’s restrained idea that perceptual content may be relational across realizations rather than a common neural point (`001.md`; manuscript § Relation to FB-RN).

**Speculative:** fibre, section, quotient, phenomenal content object, CSQ closure.

**Rejected for this result:** qualia meter, consciousness score, phenomenal identity, causal generation, fibre-bundle ontology, NDT validation, MNPS \((m,d,e)\), \(K^h\), operator identification. No-report ≠ consciousness isolation. Dataset paper’s “qualia structure” language does not collapse neural correspondence into phenomenal identity (`001.md`).

`001.md` explicit: “Do not call this validation of Fibre Bundle v3.” Working paper is “a focused human empirical article, not yet the NDT-Q article.” Median \(\rho \approx 0.09\) is interesting because of **controls and consistency**, not magnitude. CSQ remains a separate speculative branch (Gate Q in the truth-known simulator; DANDI 000248 E004 STOP on a coarse transport proxy is not P2).

---

## Claims table

| Object | Claim | Evidence class | Layer | Flagship role | Claim ceiling |
| --- | --- | --- | --- | --- | --- |
| E001 corrected PASS | Dual-high-pass ranked partial RSA: median \(\rho=0.0922684\), \(p=0.0179964\), \(n=30\) | internal_validated | state | evidence_matrix (boundary) | One dataset, ROI, task, contract; 19/30 rhos positive |
| Independent reproduction | Endpoint mathematics match fresh RDMs | internal_validated | measurement_contract | evidence_matrix | Not a second biological sample; GLMs not re-fit |
| Historical STOP | As-run \(p=0.0918\) before ranking/order fixes | internal_validated (provenance) | epistemic | exclude as current biology | Keep as defect history, not a negative on the hypothesis |
| RV1 residual-label null | \(p=0.0172\) | internal_validated (sensitivity) | state | evidence_matrix | Does not replace E001 |
| RV1 high-pass sensitivity | \(\rho=0.0232\), \(p=0.3113\) | internal_validated (negative for invariance) | measurement_contract | evidence_matrix | Conditional inference is preprocessing-sensitive |
| Behavioral split-half | Spearman 0.895, \(n=27\) | descriptive | state | supplement | Not reliability-corrected RSA |
| FB-RN relational content | Correspondence consistent with relational-not-centroid content | plausible | epistemic | terminology_only | Not fibre identification |
| Fibre / section / quotient / CSQ | Phenomenal or closure ontology | speculative | epistemic | exclude | Explicit non-claim |
| No-report geometry as consciousness / NDT | Accessibility, \(K^h\), MNPS, RVC, operator ID | rejected | — | exclude | Wrong objects |
| Color RDM = MNPS \((m,d,e)\) | Identity of charts | rejected | state | exclude | RSA of nine colors ≠ phase-space chart |

---

## Skip list (confirmed; no new empirical NDT summaries)

| Path in `J:\repos\m3-bridge\` | Exists | Why skip | Pointer |
| --- | --- | --- | --- |
| `articles/NDT/` | Yes. Title: *Noetic Diffusion Theory: A Rhythmic, Geometric Framework…* Version 0.8; Zenodo `10.5281/zenodo.20112950` | Duplicate identity donor of NDT 0.8 | **Summary `04`** (`articles/NDT/NoeticDiffusionTheory.typ` in nmd-analysis) |
| `articles/Slow Branch-Level Accessibility as a Structural Constraint on Memory Linking/` | Yes. Full Typst + `v2_claim_ledger.md` + S1–S5 | Duplicate of the cytodend Slow Branch paper | **Summary `06`** (canonical: `I:\AAA_PYTHON_REPOS_BACKUP\cytodendaccessmodel\`). m3-bridge copy is not a second result |
| `articles/compendium/` | Yes. *Noetic Diffusion Theory Compendium* v0.1 | Notation dump across MNDM/MNPS/MNJ/reachability/NMD/cytodend; not a result | Reference only; do not cite as evidence |
| `articles/aa_template/` | Yes. Generic eLife scaffold + synthetic examples | Template; FB3 README is still this file copied | Not a result |
| `articles/iblreach2/` | Yes. IBL2-000A/001/002A/002B | Backend/pilot measurement layer, not a flagship article | **One sentence:** IBL2-001 full-scale discrete chart-transition operator **FAIL**s its gate (primary VISa_VISam: 4 qualifying blocks / 4 labs; among blocks with \(\ge 40\) transitions, median `cv_resid_frac = 1.001`); IBL2-002B selects **no** flow metric (`selected_metric: null`) despite IBL2-002A decoder signal — “decoder PASS / flow-metric STOP.” Coherent with existing recoverability negatives (`03` 000458 Level-4 residual fraction 0.856; simulator operator-ID fails). Does **not** uniquely change an NDT v2 flagship claim; do not promote to a fourth anchor |
| `articles/iblreach/` | Yes (`iblreach.pdf`/`.txt`) | Earlier IBL reachability backend | Same skip; no unique NDT upgrade found |
| `articles/DANDI/` | Yes. `000458`, `_meso_macro_chain`, `_TRN_meso_macro_brige`, `_Figshare_opto`, `000248`, `000574`, `000939`, … | Analysis backends / sibling papers | **000458 meso→macro** already in **summary `03`** (Anchor 3). Other DANDI lines (000248 mouse IC/XRE; 000574 MTL–EEG FAIL; 000939) do not uniquely rewrite NDT accessibility identity for this intake. 000248 is FB-RN/CSQ-adjacent (E002 PASS decoder generalization; E003/E004 STOP on centroid/transport proxies) — neighboring programme, not NDT \(K^h\) |

Skipping is **correct**. Do not open parallel empirical summaries for these folders unless a later editorial decision treats IBL2’s decoder/flow dissociation as an explicit recoverability-matrix cell (still not an NDT mechanism result).

---

## Flagship placement

**Recommended role: `evidence_matrix` (one boundary / neighboring-programme row). Not `main_text_anchor`.**

- **Main text (§§2–8, anchors 1–3):** **`exclude`.** Spindles, coma, and DANDI 000458 remain the only empirical anchors (`00_synthesis.md`). FB3 does not sit on the architecture chain (state *dynamics* → futures → control). It is RSA of event-modelled BOLD patterns vs ordinal color reports.
- **If phenomenology / content is mentioned:** one `terminology_only` sentence: a neighboring FB-RN line found a small, preprocessing-sensitive no-report relational correspondence in humans; it is not a test of NDT, MNPS, or accessibility.
- **Figure 5 matrix row (suggested):** FB3 / ds005684 | `state` (RSA, not MNPS) | internal_validated correspondence under dual-high-pass; high-pass sensitivity negative | **not NDT; not \(K^h\); not a consciousness meter; frozen ≠ replication**.
- **Do not:** add a fourth anchor; identify color geometry with \((m,d,e)\); treat no-report as a qualia isolation; promote RV1 or `sub-33`–`sub-35` as replication; fold CSQ/Gate Q into NDT 1.0 on this evidence; use the older title’s “Beyond Controls” as if it meant causal or exhaustive control.

**Recoverability reached:** Level 1 (association) only, and only inside the frozen contract. Levels 2–4 are not claimed and are not estimable from this fMRI RSA design.

**What NOT to import**

- MNPS, MNJ, \(K^h\), \(F\), \(\sigma(t)\), RVC, HELS, committor, FAR as if FB3 measured them.
- “No-report neural geometry tracks qualia” or any consciousness-score reading (S5: PASS means frozen E001 criteria, not theory validation).
- Fibre-bundle ontology as demonstrated (manuscript: “does not measure a fibre, section, quotient, noetic diffusion, or phenomenal object”).
- Independent *replication* language for the independent *reimplementation*.
- DANDI 000248 + ds005684 as one NDT-Q synthesis in the flagship (`001.md`: keep the human paper standalone; mouse IC is complementary FB-RN, not NDT).

---

## Open questions (not this intake)

- Whether a later MEG/iEEG color-geometry resource (science-lead names OpenNeuro `ds003352` / MEGco) can time-resolve relational geometry; that would still be FB-RN, not NDT, unless a prospective accessibility object is defined.
- Gate Q / CSQ remain a separate speculative branch (`001.md`, `002.md`); unimplemented in this snapshot of the qualia ledger’s Gate Q rows.
- `sub-33`–`sub-35` cohort extension is explicitly not an independent replication.

---

## Sources (paths)

- `J:\repos\m3-bridge\articles\FB3 Color Geometry\`
- `J:\repos\m3-bridge\project\qualia\claim_ledger.md`
- `J:\repos\m3-bridge\project\qualia\science_lead\001.md`, `002.md`
- `J:\repos\m3-bridge\project\qualia\results\FB3_H1_ds005684_E001_full_recompute_frozen30_20260812\`
- `J:\repos\m3-bridge\project\qualia\results\FB3_H1_ds005684_RV1_20260817\`
