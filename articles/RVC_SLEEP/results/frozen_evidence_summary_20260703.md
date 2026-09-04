# RVC_SLEEP — Frozen Evidence Summary (2026-07-03)

Status: **Pass A / A1r / A2r / A1-decomposition / B / C frozen as complete**,
per `sciencelead/004.md`. No further analyses unless a specific
reviewer-facing robustness gap is identified.

This document has four sections: frozen evidence summary, claim ledger,
known limitations, manuscript decision.

---

## 1. Frozen evidence summary

Primary estimand for all specificity/timing tests (protocol amendment,
`sciencelead/001.md`, 2026-07-03): subject is the biological unit → subject-
level mean deltas, subject-level sign-flip permutation as the primary
p-value, BH-FDR across the frozen 9-endpoint x 2-dataset (18-test) family.
9 frozen endpoints: `m, d, e, d_n, d_l, d_s, e_e, e_s, e_m`.

### A1r — subject-weighted event-vs-matched-control specificity (primary)

`event_control_delta = event_bin − matched_control_median`, aggregated to
subject means, sign-flip permutation, BH-FDR over 18 tests.

| Endpoint | ANPHY delta (q) | BOAS delta (q) | Agreement |
|---|---|---|---|
| `m` | +0.430 (q<0.001) | +0.230 (q<0.001) | same sign |
| `d` | +0.203 (q<0.001) | +0.404 (q<0.001) | same sign |
| `e` | +0.100 (q<0.001) | +0.274 (q<0.001) | same sign |
| `d_n` | **−0.189** (q<0.001) | **+0.589** (q<0.001) | **opposite sign** — resolved by decomposition (§ below) |
| `d_l` | +0.392 (q<0.001) | +0.349 (q<0.001) | same sign |
| `d_s` | +0.500 (q<0.001) | +0.427 (q<0.001) | same sign |
| `e_e` | +0.049 (q=0.082, ns) | +0.103 (q=0.0016) | same sign, ANPHY ns |
| `e_s` | +0.077 (q=0.0016) | +0.485 (q<0.001) | same sign |
| `e_m` | +0.488 (q<0.001) | +0.397 (q<0.001) | same sign |

8/9 endpoints agree in sign across datasets and are FDR-significant in at
least one dataset. Read as: **broad, real, but not cleanly interpretable as
a single "spindle-specific" mechanism** — see decomposition.

### A2r — subject-balanced event-vs-pre_far timing (companion check)

`event_prefar_delta = event_bin − mean(pre_far bins, same event)`, same
subject-weighted machinery.

| Endpoint | ANPHY delta (q) | BOAS delta (q) |
|---|---|---|
| `d_n` | +0.106 (q=0.009) | +0.165 (q=0.011) |
| `e_s` | +0.062 (q=0.062, ns) | +0.114 (q=0.011) |
| `d` | +0.040 (q=0.037) | +0.072 (q=0.014) |
| `e_e` | −0.064 (q=0.009) | −0.019 (q=0.57, ns) |
| all others | ns | ns |

**`d_n` is the only endpoint that is FDR-significant, same-sign, in both
datasets under the timing (A2r) estimand.** This is the headline result.
`e_s` replicates in BOAS, trends in ANPHY (q=0.062).

### A1 decomposition — resolving the `d_n` sign conflict

`C (event−control) = A (event−pre_far) + B (pre_far−control)`.

| Endpoint | ANPHY A / B / C | BOAS A / B / C | Reading |
|---|---|---|---|
| `d_n` | +0.106 / **−0.293** / −0.187 | +0.166 / **+0.427** / +0.593 | **A agrees (timing rise, both +); B disagrees (baseline direction differs by dataset) → explains the A1r sign conflict** |
| `d_s` | +0.018 / +0.484 / +0.501 | +0.066 / +0.354 / +0.420 | mostly `B` (baseline separation), weak/no timing component |
| `e_s` | +0.062 / +0.017 / +0.079 | +0.116 / +0.368 / +0.484 | `A` positive both; `B` small in ANPHY, large in BOAS |
| `m` | −0.013 / +0.442 / +0.429 | −0.041 / +0.295 / +0.254 | timing component near-zero/negative in both; result is baseline-driven |

**Conclusion: `d_n` is a robust peri-spindle *timing* effect (`A`), with
matched-control *specificity* (`C`) complicated by dataset-specific N2
baseline structure (`B`).** This is the correct framing for the manuscript,
per `sciencelead/003.md`.

### Pass B — surface sensitivity (construction-validity check, not EAP test)

Primary vs. anchor-augmented surface, same subject-weighted estimand, both
delta modes.

- **7/9 endpoints (`m, d, d_n, d_l, d_s, e_e, e_s`) are byte-identical
  between surfaces** (surface_delta = 0.000000, r = 1.0) — structurally
  untouched by anchor augmentation.
- **Only `e_m` (directly modified by anchor injection) and `e` (recomposes
  from `e_m`) show any divergence** — `e_m`: r = 0.36–0.74 (event_control),
  ~0–0.59 (event_prefar), 59–75% sign agreement; `e`: r ≥ 0.97 everywhere
  (barely moves).
- **FDR significance status changed in 0/36 testable rows** — anchor
  augmentation never flips a conclusion.
- Reading (guardrail from `sciencelead/003.md`): this shows the surface
  behaves as expected when a signal is injected into `e_m` and partly
  propagates into `e`. It is a **construction-validity check**, not evidence
  for or against EAP moderation.

### Pass C — EAP moderation (the moderation test itself)

`delta ~ anchor_pre_far + <mean-centered nuisance covariates>`, WLS with
`1/n_events_subject` weights, cluster-robust SE by subject; per-subject
slope sign-flip permutation as a companion sensitivity; BH-FDR over the
9-endpoint family within each (delta_mode, dataset, anchor model) — 54 tests
total (2 delta modes x 3 models x 9 endpoints).

- **53/54 tests do not survive FDR.**
- **1 exception**: `event_control / ANPHY / ecg_hrv_rmssd_ms_pre_far
  (primary) / d_l` — pooled WLS `anchor_coef = 0.00097`, `q = 0.0015`. This
  does **not** replicate in its own subject-level slope sensitivity check
  (`slope_perm_p = 0.140`, ns) — a pooled-vs-subject-level discordance that,
  per this project's own protocol-amendment logic, points to a
  weighting/leverage artifact rather than a genuine effect. See erratum in
  `project/diary/229_...md` (this was mis-stated as "zero survive FDR" when
  first reported, and corrected here before the manuscript decision).
- **Verdict: Pass C is materially null.** No robust cardiac/respiratory
  anchor-state moderation of spindle-locked geometry in either dataset.

---

## 2. Claim ledger

| Claim | Status | Basis |
|---|---|---|
| `d_n` increases at spindle event vs. pre-spindle baseline (timing) | **Internal validated result**, both datasets | A2r + decomposition `A` component |
| `e_s` timing effect | Plausible/supportive, weaker | A2r: BOAS q=0.011, ANPHY q=0.062 (ns) |
| Spindle event-control specificity (A1r, broad) | Plausible, broad, baseline-sensitive | A1r 8/9 same-sign but decomposition shows baseline (`B`) contribution for several endpoints |
| `d_n` matched-control specificity (A1r `C`) | Not a clean cross-dataset effect — sign conflict explained by dataset-specific baseline (`B`), not timing | Decomposition |
| `d_s` specificity | Mostly baseline-separation, not timing | Decomposition (`B` dominates `A`) |
| EAP moderation via HRV/respiratory anchors | **Rejected / not supported** | Pass C, 53/54 null, 1 exception fails its own sensitivity check |
| Anchor-augmented surface behavior | Internal construction-validity check passed (only `e_m`/`e` respond; no FDR status changes) | Pass B |
| TRN-VG | Proxy-consistent only; not validated | Not directly tested in Pass A/B/C |
| RVC as a general mechanism | Plausible interpretation, not yet fully validated | Consistent with `d_n`/`e_s` timing but specificity is qualified |

---

## 3. Known limitations

1. **BOAS Pass C primary-anchor model runs on a restricted N** (~35
   subjects with valid `resp_regular_index_pre_far`), not the full 128;
   the sensitivity anchor (`anchor_index_v02_pre_far`, ~90 subjects) gives
   more power and is still null (`handover_From_nmd.md` §6, known
   limitation #1).
2. **BOAS has sparse, uneven spindle-event counts per subject** (median 5,
   range 1–18) — the original motivation for the A1r subject-weighted
   protocol amendment; A1-original (event-weighted OLS) is retained as a
   pre-amendment sensitivity table, not the primary result.
3. **`frequency_hz` is not present in the NMD event-locked schema** — listed
   defensively in Pass C nuisance covariates in case a future export adds
   it, but currently always dropped by `available_covariates()`.
4. **Sigma-power residualization is not available** in the current schema
   and is not approximated by duration/window-center covariates — flagged
   as a genuine gap, not silently substituted, and left as a possible
   follow-up detector-strength robustness analysis (not run under the
   current freeze).
5. **One Pass C row (ANPHY `d_l`, HRV anchor, event-control delta) survives
   pooled FDR but fails its own subject-level slope sensitivity** — treated
   as non-robust, documented explicitly rather than omitted, per erratum in
   diary 229.
6. **A1-original OLS coefficients are not directly interpretable** as a
   population mean because covariates (e.g. `window_center_sec`) were not
   centered, making the fitted intercept an extrapolation; this is exactly
   why A1r (which does not carry covariates in the primary model) was
   adopted as the corrected primary estimand.

---

## 4. Manuscript decision

Not yet made. Per `sciencelead/004.md`, the next decision is manuscript
framing: **short empirical report** vs. **methods-anchored RVC validation
note**. This document and the compact results memo
(`results/001_results_memo_20260703.md`) are inputs to that decision, not
the decision itself.

Recommended figure/table plan (per `sciencelead/004.md`), pending
manuscript-framing decision:

| Figure | Content |
|---|---|
| Fig 1 | A1r event-control specificity, subject-weighted |
| Fig 2 | A2r event-vs-pre_far timing, highlighting `d_n` |
| Fig 3 | A1 decomposition: `event−pre_far`, `pre_far−control`, `event−control` for `d_n` |
| Fig 4 | Pass C null EAP moderation |
| Fig S1 | Pass B surface sensitivity |
| Fig S2 | BOAS heterogeneity audit |

The main paper should lead with **A2r `d_n`**, not broad A1r significance.
