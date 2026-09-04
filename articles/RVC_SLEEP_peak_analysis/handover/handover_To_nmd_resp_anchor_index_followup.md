# Handover to NMD: `resp_anchor_index` sensitivity-anchor finding — investigated, resolved on analysis side, no ingest work needed now

**Date:** 2026-07-09 (updated same day, twice — see §7 for the latest)
**From:** Analysis repo (RVC_SLEEP / EAP-moderation work)
**To:** NMD
**Status:** §1-§5 = original investigation (pre-sign-bug-discovery). §6 = NMD's
sign-bug finding + first re-summarize request. §7 = **read this first** — round-2
re-verification results (the sign fix fully resolves the original finding; a new,
weaker pattern emerged; two unrelated delivery regressions found in the ANPHY/BOAS
re-summarize need attention before those two datasets' run roots can be updated.

---

## 7. Round 2 (2026-07-09, after the 5-dataset re-summarize): resolved + new pattern + delivery issues

**Thank you for the fast turnaround — all 5 re-summarize runs were delivered and
picked up.** Results:

### 7a. RichSleep: fully resolved, clean

`neuralmanifolddynamics_RichSleep_20260709_100219` is clean: 24/24 subjects, all
expected columns present, no corrupted files, geometry (`m`/`d`/`e`) bit-identical
to the pre-fix run where compared. Adopted as the new RichSleep run root.

Re-running the moderation test: the original `event_control`-mode finding
(§1-§4 above) is now a **clean null** — `m`/`d`/`d_l`/`e_m` coefficients at
$p \approx 0.23$-$0.93$, matching the primary `cardioresp_anchor_index` anchor's
null pattern exactly. The sign bug *was* the explanation; §2's artifact checks were
correct to rule out scale/multicollinearity/outlier-subject, they just couldn't
catch a bug upstream of the anchor's construction. This closes the original finding
as a resolved false positive.

A **different, weaker** pattern appeared in the `event_prefar` delta mode, which
was null pre-fix and now has 4 FDR survivors (`d`, `e`, `d_n`, `e_s`, all
positive-signed, plus `e_e` at the FDR boundary $q=0.050$). Re-running the same
three artifact checks: ordinary scale, low multicollinearity ($|r|\le0.18$); 3 of
4 (`e`, `d_n`, `e_s`) hold a 71-75% subject-majority direction and survive
excluding the single most influential subject with equal/stronger significance,
but `d` and `e_e` lose significance on that same exclusion. Given that this exact
anchor's signal has now completely flipped once already, we're reporting this at
deliberately low confidence in the manuscript (S2.6a, S3.4f) — a hypothesis for a
future independently-replicated test, not a finding.

**Update (diary 240):** ran two additional, stricter checks before finalizing
this at low confidence. (1) A joint BH-FDR correction pooling both delta modes'
108 sensitivity-anchor tests into one family (rather than 09's two separate
54-test families) — `d`/`e`/`d_n`/`e_s` all still survive ($q\le0.021$); `e_e`
does not ($q=0.073$) and is downgraded from boundary to non-significant. (2)
Excluding the subject with the single most extreme *raw* `resp_anchor_index`
value (`sub-xn024`, mean $-2.34$ vs. cohort mean $-0.06$, $>3$ SD out — a genuine
data-quality-looking anomaly, distinct from the most-influential-*slope* subject
`sub-xn003` checked earlier) leaves every coefficient essentially unchanged.
`d` remains the one endpoint that's specifically sensitive to the slope-outlier
exclusion. Net: this pattern now survives every artifact check we can run on this
one sample, which is worth knowing, but per the sign-bug precedent above, we're
treating "survives every sample-internal check" as distinct from "established" —
still not requesting anything from NMD on this, just noting that `sub-xn024`'s
anomalous respiratory-anchor signal might be worth a data-quality look on your
side independent of this specific finding.

**No action needed from NMD on the `resp_anchor_index` finding itself** —
flagging only so the history is on record if this ever gets revisited.

### 7b. ANPHY/BOAS: two delivery regressions — reverted, not adopted, need a fix before re-delivery

We independently verified all 5 delivered run directories before switching
`rvc_sleep_support.py` over, and found two problems specific to the ANPHY/BOAS
re-summarize (RichSleep, §7a, is unaffected and was kept):

1. **2 of 27 ANPHY primary subjects have corrupted event-locked parquet files.**
   `neuralmanifolddynamics_ANPHY_20260709_100213/sub-EPCTL13_sleep_sleep/sub-EPCTL13_sleep_event_locked_v1_eeg.parquet`
   and the equivalent for `sub-EPCTL16` both fail to open in `pyarrow`
   (`TProtocolException: Invalid data` / `"don't know what type"`). File sizes are
   nonzero but different from the old run's files for the same subjects, so this
   looks like a copy/transfer corruption rather than a write-time ingest bug — but
   we can't rule out the latter without your side re-checking. The 23 other ANPHY
   primary subjects, all 25 ANPHY anchor-aug subjects, and all 128×2 BOAS subjects
   read fine.
2. **The new BOAS export (both primary and anchor-aug) is missing
   `resp_regular_index`, `resp_depth_index`, `resp_rate_bpm`** — raw respiratory
   feature columns that were present in the frozen 2026-07-02 BOAS export.
   `resp_regular_index` is BOAS's *primary* Pass C anchor (per your original
   handover, §1) — if we'd adopted the new run without checking, this would have
   silently broken the frozen R5 EAP-moderation result for BOAS. Everything else we
   checked in the new BOAS export (geometry `m`/`d`/`e`, both surfaces, confirmed
   bit-identical to the old run) is fine, so this looks like an export/column-list
   regression specific to this re-summarize, not a change to the underlying
   pipeline.

**What we did:** reverted `RUN_ROOTS`/`CONFIG_HASH` for ANPHY (both surfaces) and
BOAS (both surfaces) back to the original frozen 2026-07-02 runs in
`rvc_sleep_support.py` (diary 239). RichSleep stays on the new, verified-clean
`..._100219` run. No primary manuscript result (R2-R5) was re-run against the new
ANPHY/BOAS exports, and none needed to be, since we didn't adopt them.

**What we'd need before adopting the new ANPHY/BOAS runs:**
- Re-delivery of the 2 corrupted ANPHY primary files (or the whole run, if easier),
  and confirmation of whether this was a delivery/copy issue or an ingest-side one.
- Confirmation of whether `resp_regular_index`/`resp_depth_index`/`resp_rate_bpm`
  were intentionally dropped from the BOAS export schema, or whether this is a
  regression to fix. If intentional, we'd need an alternative way to compute BOAS's
  primary Pass C anchor from whatever is now exported instead.

Not urgent — the frozen ANPHY/BOAS results are untouched and correct as-is, this
only blocks adopting the *new* re-summarize for those two datasets.

---

## 6. Update (2026-07-09, after NMD's reply)

NMD's reply (`project/ideas/TRV/handover_To_analysis_resp_anchor_sign_bug.md`,
not present in this repo) independently traced the exact construction of
`resp_anchor_index` and found something this analysis-side investigation could not
have found without the construction formula: `resp_anchor_index` is a robust-Z
composite of `resp_regular_index` (regularity), `resp_depth_index` (amplitude), and
`resp_slowing_index` (`= -rate_bpm/20`, already inverse-coded so slow breathing is
positive). A sign bug in `anchor_state.py` placed the already-inverted
`resp_slowing_index` into the `"negative"` bucket, double-negating it — every
existing `resp_anchor_index` export therefore rewards *fast* breathers, the
opposite of the intended "slow breathing = strong anchor" design. NMD found and
left an unresolved comment about this ("note: slowing_index = -rate, so neg of neg
= +rate") in the original code without acting on it; it has now been fixed.

This does not overturn §2-§3's artifact-elimination checks (scale,
multicollinearity, outlier-subject robustness are properties of *any* version of
the anchor, buggy or fixed) but it does mean the *specific* coefficient magnitudes
and the *interpretation* ("more regular/phase-locked breathing dampens
reconfiguration") reported in manuscript R6/S2.6a/S3.4f were computed on a
mis-signed rate component and are now provisional pending a corrected re-export.
Robin has asked NMD to re-run `mndm summarize` for all three datasets (ANPHY,
BOAS, RichSleep) to regenerate `resp_anchor_index` (and anything else touched by
the fix) with the corrected sign.

**What we need back, once the re-run is done:**
1. Confirmation that all three re-summarized runs (ANPHY, BOAS, RichSleep) are
   complete and which run-directory timestamps replace the current frozen ones for
   `resp_anchor_index` purposes specifically (ideally: do the *other* anchor
   columns and 9D/3D geometry coordinates change at all, or only
   `resp_anchor_index`? If only `resp_anchor_index` changed, that's useful to know
   so we don't need to re-verify the primary Pass A/B/C results, which do not use
   this anchor).
2. Delivery/copy of the corrected run(s) into this repo's `data/raw/` (or
   `K:/ExternalReceivedDatasets/...`), same as prior handovers.
3. Confirmation of the new `run_manifest.json → config.digest_sha256` per corrected
   run, for the sanity-check registry in `rvc_sleep_support.py`.

**What is NOT blocked by this:** The manuscript's primary claims (R2-R6 timing
effects, the primary `cardioresp_anchor_index` EAP-moderation null, Mål B/C) do not
use `resp_anchor_index` and are unaffected. Only the exploratory R6/S2.6a/S3.4f
`resp_anchor_index` finding is provisional pending the corrected re-export - it has
been flagged as such in the manuscript (2026-07-09).

---

## 1. Why you're getting this

R6/S2.5 of the RVC_SLEEP manuscript's RichSleep EAP-moderation test reports six
sensitivity anchors alongside the primary dual-arm composite
`cardioresp_anchor_index`. Five of them (`anchor_index`, `anchor_index_v02`,
`sympathetic_index`, `ocular_stability_index`, plus the primary itself) behave
exactly as expected: either null, or nominally FDR-significant with a coefficient so
numerically small ($\approx 10^{-8}$–$10^{-9}$ per raw unit) that it's clearly a
scale/multicollinearity artifact of those anchors' large raw magnitude (up to
$10^8$).

`resp_anchor_index` did not fit that pattern — its FDR-surviving coefficients on
`m`, `d`, `d_l`, `e_m` are ordinary, non-negligible magnitude ($\approx -0.19$ to
$-0.36$). This handover documents the follow-up investigation into whether that's a
genuine signal or a different kind of artifact, run entirely on the analysis side
with data you've already delivered — **you don't need to do anything**, but the
open question at the end (§4) is something only NMD could eventually help resolve
if a dedicated follow-up is ever prioritized.

## 2. What was checked (all using the already-delivered, corrected
`neuralmanifolddynamics_RichSleep_20260708_135627` ingest — no new export needed)

1. **Scale.** `resp_anchor_index` sits on an ordinary $\approx[-1, 1]$ scale (like
   `cardioresp_anchor_index`), unlike `anchor_index`/`sympathetic_index`/
   `ocular_stability_index`, which range up to $10^8$. Rules out the scale-artifact
   explanation used for the other anchors.
2. **Multicollinearity.** Spearman correlation of `resp_anchor_index` against the
   primary anchor and every nuisance covariate in the moderation model: max
   $|r| = 0.196$. Not collinear with anything already in the model.
3. **Model robustness.** Bivariate (anchor-only, no covariates) vs.
   covariate-adjusted coefficients agree closely in sign/magnitude at all four
   endpoints (e.g. `d_l`: $-0.131$ vs. $-0.199$). Not a covariate-adjustment
   artifact.
4. **Outlier-subject robustness.** The negative direction holds in 18–20/24
   subjects per endpoint, and the effect gets *stronger*, not weaker, after
   excluding the single most extreme subject at each endpoint. Not a 1-2-subject
   artifact.

None of the three candidate artifacts (scale, multicollinearity, outlier subject)
explains the finding. Full detail: diary 237, manuscript S2.6a/S3.4f,
`articles/RVC_SLEEP/src/11_richsleep_resp_anchor_followup.py`.

## 3. Conclusion (analysis side, no ingest implication)

`resp_anchor_index`'s moderation of the spindle-locked geometry response is a
genuine, robust, but **exploratory, non-primary, non-pre-registered, single-dataset
finding** — reported as such in the manuscript, not elevated to a headline claim,
and not overturning R6's primary `cardioresp_anchor_index` null. Directionally,
higher `resp_anchor_index` (more regular/phase-locked breathing) is associated with
a *smaller* spindle-locked geometry reconfiguration — an "anchoring dampens
reconfiguration" reading, mildly convergent with a similarly-signed,
similarly-named finding in this lab's separate `ds004511` gambling/cognitive-control
article (different task domain, not replication).

This closes the investigation for this round. No re-ingest, no re-export, and no
schema change is being requested.

## 4. Open question for a *possible future* dedicated follow-up (not requested now)

If this ever becomes worth a dedicated, pre-registered test, the open question is:
**does `resp_anchor_index` carry moderation information that is not already in
`cardioresp_anchor_index`, or is it effectively redundant with the composite once
measured with adequate power?** The weak-but-nonzero correlation we found
($r=-0.13$) between the two on your existing export doesn't fully settle this
(it's just a raw Spearman correlation, not a proper redundancy/incremental-validity
test).

Concretely, if/when this is prioritized, it would help to know from your side:
- **How `resp_anchor_index` is actually constructed** (exact formula/weights) —
  the cross-article glossary describes it only qualitatively ("MNDM-native
  respiration-derived feature quantifying how regular and how strongly
  phase-locked a subject's breathing is relative to their concurrent neural
  trajectory"). Knowing its construction would let us reason about *why* it might
  carry independent information from the composite `cardioresp_anchor_index`
  (which is built to combine both channels) rather than just re-testing this
  post-hoc.
- Whether a **larger RichSleep-like cohort** (or a second dataset with both
  simultaneous ECG+respiration and a `resp_anchor_index`-equivalent feature) is
  available or plannable, since this finding has $N=24$ subjects and would benefit
  from independent replication before being treated as more than exploratory.

This is not a request for immediate action — just flagging it so it's not lost, in
case a future EAP-focused study round picks it up.

## 5. What is NOT requested

- No re-run, re-export, or schema change to any RichSleep/ANPHY/BOAS ingest.
- No changes to `anchor_state`/`resp_anchor_index` construction at this time.
- No blocking dependency on the manuscript — R6/S2.5/S2.6a/S3.4f are already
  updated and the manuscript compiles cleanly with this finding fully documented.
