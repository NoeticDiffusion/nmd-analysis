// S2 Supplementary Data — RVC_SLEEP
// Full result tables underlying manuscript.typ R1-R6. All values are read
// directly from the frozen CSVs cited in each caption; nothing here is
// re-derived.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "S2 Data - RVC_SLEEP",
  subtitle: "Complete A1r/A2r contrast tables, A1 decomposition, Pass B/C moderation tables, and descriptive summaries",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S2.0 Complete A1r table (event vs. matched-control), all three datasets

#figure(
  kind: table,
  clean-table(
    columns: (0.7fr, 1fr, 0.6fr, 0.7fr, 0.7fr, 0.9fr),
    align: (left, center, center, center, center, center),
    inset: 4pt,
    table.header([*Dataset*], [*Endpoint*], [*$N$ subj.*], [*Delta*], [*perm $p$*], [*FDR $q$*]),
    [ANPHY], [`m`], [27], [$+0.4302$], [$<0.001$], [$<0.001$],
    [ANPHY], [`d`], [27], [$+0.2026$], [$<0.001$], [$<0.001$],
    [ANPHY], [`e`], [27], [$+0.0999$], [$<0.001$], [$<0.001$],
    [ANPHY], [`d_n`], [27], [$-0.1889$], [$<0.001$], [$<0.001$],
    [ANPHY], [`d_l`], [27], [$+0.3920$], [$<0.001$], [$<0.001$],
    [ANPHY], [`d_s`], [27], [$+0.5003$], [$<0.001$], [$<0.001$],
    [ANPHY], [`e_e`], [27], [$+0.0495$], [$0.082$], [$0.082$ (ns)],
    [ANPHY], [`e_s`], [27], [$+0.0773$], [$0.0015$], [$0.0016$],
    [ANPHY], [`e_m`], [27], [$+0.4876$], [$<0.001$], [$<0.001$],
    [BOAS], [`m`], [112], [$+0.2296$], [$<0.001$], [$<0.001$],
    [BOAS], [`d`], [112], [$+0.4035$], [$<0.001$], [$<0.001$],
    [BOAS], [`e`], [112], [$+0.2740$], [$<0.001$], [$<0.001$],
    [BOAS], [`d_n`], [112], [$+0.5893$], [$<0.001$], [$<0.001$],
    [BOAS], [`d_l`], [112], [$+0.3489$], [$<0.001$], [$<0.001$],
    [BOAS], [`d_s`], [112], [$+0.4272$], [$<0.001$], [$<0.001$],
    [BOAS], [`e_e`], [112], [$+0.1030$], [$0.0015$], [$0.0016$],
    [BOAS], [`e_s`], [112], [$+0.4851$], [$<0.001$], [$<0.001$],
    [BOAS], [`e_m`], [112], [$+0.3967$], [$<0.001$], [$<0.001$],
    [RichSleep], [`m`], [24], [$+0.2296$], [$<0.001$], [$0.0006$],
    [RichSleep], [`d`], [24], [$+0.3487$], [$<0.001$], [$0.0006$],
    [RichSleep], [`e`], [24], [$+0.0190$], [$0.139$], [$0.139$ (ns)],
    [RichSleep], [`d_n`], [24], [$+0.2918$], [$<0.001$], [$0.0006$],
    [RichSleep], [`d_l`], [24], [$+0.4330$], [$<0.001$], [$0.0006$],
    [RichSleep], [`d_s`], [24], [$+0.1480$], [$<0.001$], [$0.0006$],
    [RichSleep], [`e_e`], [24], [$-0.2216$], [$<0.001$], [$0.0006$],
    [RichSleep], [`e_s`], [24], [$+0.2229$], [$<0.001$], [$0.0006$],
    [RichSleep], [`e_m`], [24], [$+0.5564$], [$<0.001$], [$0.0006$],
  ),
  caption: [Complete Pass A1r table: subject-weighted event-vs-matched-control delta, sign-flip permutation $p$, BH-FDR $q$ (ANPHY/BOAS: 18-test family; RichSleep: separate 9-test family, R6). RichSleep figures are from the QA-corrected `neuralmanifolddynamics_RichSleep_20260709_100219` ingest (S1.0). Sources: `results/rvc_sleep_20260703/02c_pass_a1r_subject_weighted_specificity/pass_a1r_subject_weighted_specificity.csv`; `results/rvc_sleep_20260709/09_richsleep_verification/richsleep_a1r_specificity.csv`.]
) <tab-a1r-full>

= S2.1 Complete A2r table (event vs. pre_far, within-spindle timing), all three datasets

#figure(
  kind: table,
  clean-table(
    columns: (0.7fr, 1fr, 0.6fr, 0.7fr, 0.7fr, 0.9fr),
    align: (left, center, center, center, center, center),
    inset: 4pt,
    table.header([*Dataset*], [*Endpoint*], [*$N$ subj.*], [*Delta*], [*perm $p$*], [*FDR $q$*]),
    [ANPHY], [`m`], [27], [$-0.0131$], [$0.650$], [$0.731$ (ns)],
    [ANPHY], [`d`], [27], [$+0.0402$], [$0.012$], [$0.037$],
    [ANPHY], [`e`], [27], [$-0.0099$], [$0.491$], [$0.632$ (ns)],
    [ANPHY], [`d_n`], [27], [$+0.1056$], [$<0.001$], [$0.009$],
    [ANPHY], [`d_l`], [27], [$+0.0081$], [$0.719$], [$0.761$ (ns)],
    [ANPHY], [`d_s`], [27], [$+0.0177$], [$0.644$], [$0.731$ (ns)],
    [ANPHY], [`e_e`], [27], [$-0.0637$], [$<0.001$], [$0.009$],
    [ANPHY], [`e_s`], [27], [$+0.0617$], [$0.024$], [$0.062$ (ns)],
    [ANPHY], [`e_m`], [27], [$+0.0356$], [$0.119$], [$0.215$ (ns)],
    [BOAS], [`m`], [110], [$-0.0410$], [$0.088$], [$0.196$ (ns)],
    [BOAS], [`d`], [110], [$+0.0721$], [$0.004$], [$0.014$],
    [BOAS], [`e`], [110], [$+0.0368$], [$0.098$], [$0.196$ (ns)],
    [BOAS], [`d_n`], [110], [$+0.1651$], [$0.002$], [$0.011$],
    [BOAS], [`d_l`], [110], [$+0.0185$], [$0.419$], [$0.581$ (ns)],
    [BOAS], [`d_s`], [110], [$+0.0632$], [$0.139$], [$0.228$ (ns)],
    [BOAS], [`e_e`], [110], [$-0.0186$], [$0.381$], [$0.571$ (ns)],
    [BOAS], [`e_s`], [110], [$+0.1141$], [$0.002$], [$0.011$],
    [BOAS], [`e_m`], [110], [$+0.0053$], [$0.814$], [$0.814$ (ns)],
    [RichSleep], [`m`], [24], [$+0.0766$], [$0.325$], [$0.585$ (ns)],
    [RichSleep], [`d`], [24], [$+0.0649$], [$0.219$], [$0.494$ (ns)],
    [RichSleep], [`e`], [24], [$-0.0340$], [$0.397$], [$0.595$ (ns)],
    [RichSleep], [`d_n`], [24], [$+0.0470$], [$0.720$], [$0.720$ (ns)],
    [RichSleep], [`d_l`], [24], [$+0.0814$], [$0.048$], [$0.144$ (ns)],
    [RichSleep], [`d_s`], [24], [$+0.0485$], [$0.642$], [$0.720$ (ns)],
    [RichSleep], [`e_e`], [24], [$-0.1005$], [$<0.001$], [$0.0045$],
    [RichSleep], [`e_s`], [24], [$+0.0477$], [$0.551$], [$0.709$ (ns)],
    [RichSleep], [`e_m`], [24], [$+0.1594$], [$0.008$], [$0.036$],
  ),
  caption: [Complete Pass A2r table: subject-balanced event-vs-pre_far within-spindle delta, sign-flip permutation $p$, BH-FDR $q$. RichSleep figures are from the QA-corrected `neuralmanifolddynamics_RichSleep_20260709_100219` ingest, $N=24$ subjects, 160 paired events. The two headline endpoints (`d_n`, `e_s`) remain non-significant at this event count relative to ANPHY (1,037) or BOAS (575); `e_e` and `e_m` newly reach FDR significance and are reported but are not the endpoints the manuscript leads with (R6). ANPHY $d_n$ $t$-based 95% CI includes zero. Sources: `results/rvc_sleep_20260703/03b_pass_a2r_subject_balanced_profile/pass_a2r_subject_balanced_profile.csv`; `results/rvc_sleep_20260709/09_richsleep_verification/richsleep_a2r_profile.csv`.]
) <tab-a2r-full>

= S2.2 A1 decomposition (full 9-endpoint family, ANPHY and BOAS)

#figure(
  kind: table,
  clean-table(
    columns: (0.7fr, 1.9fr, 1.9fr),
    align: (left, center, center),
    inset: 4pt,
    table.header([*Endpoint*], [*ANPHY $A$ / $B$ / $C$*], [*BOAS $A$ / $B$ / $C$*]),
    [`m`], [$-0.013 \/ +0.442 \/ +0.429$], [$-0.041 \/ +0.295 \/ +0.254$],
    [`d`], [$+0.040 \/ +0.162 \/ +0.202$], [$+0.074 \/ +0.340 \/ +0.414$],
    [`e`], [$-0.010 \/ +0.110 \/ +0.101$], [$+0.039 \/ +0.245 \/ +0.283$],
    [`d_n`], [$+0.106 \/ -0.293 \/ -0.187$], [$+0.166 \/ +0.427 \/ +0.593$],
    [`d_l`], [$+0.008 \/ +0.382 \/ +0.390$], [$+0.020 \/ +0.349 \/ +0.370$],
    [`d_s`], [$+0.018 \/ +0.484 \/ +0.501$], [$+0.066 \/ +0.354 \/ +0.420$],
    [`e_e`], [$-0.064 \/ +0.113 \/ +0.050$], [$-0.017 \/ +0.134 \/ +0.117$],
    [`e_s`], [$+0.062 \/ +0.017 \/ +0.079$], [$+0.116 \/ +0.368 \/ +0.484$],
    [`e_m`], [$+0.036 \/ +0.450 \/ +0.486$], [$+0.005 \/ +0.417 \/ +0.422$],
  ),
  caption: [$A$ = timing component (event $-$ pre_far, subject-mean delta), $B$ = pre-spindle-baseline-vs.-matched-control separation, $C = A + B$ = A1r event-vs-control delta. All values subject-mean deltas (units of the standardized endpoint); statistical tests for each component are in the source CSV. Source: `results/rvc_sleep_20260703/02d_pass_a1_decomposition/pass_a1_decomposition.csv` (54 rows: 9 endpoints $times$ 2 datasets $times$ 3 components).]
) <tab-decomp-full>

= S2.3 Pass B surface sensitivity (full 36-test table, condensed)

28 of 36 (delta_mode $times$ dataset $times$ endpoint) rows have `surface_delta = 0.000000` exactly (`m, d, d_n, d_l, d_s, e_e, e_s`, both delta modes, both datasets) - the anchor-augmented surface is structurally identical to the primary surface for every endpoint that does not algebraically depend on `e_m`. The remaining 8 rows (all involving `e` or `e_m`) are shown in full; none change FDR status.

#figure(
  kind: table,
  clean-table(
    columns: (1.1fr, 0.7fr, 0.6fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center, center, center, center, center),
    inset: 4pt,
    table.header([*Delta mode*], [*Dataset*], [*Endp.*], [*Primary*], [*Anchor-aug*], [*Surf. $Delta$*], [*Corr.*], [*FDR flip*]),
    [event_control], [ANPHY], [`e`], [$0.0999$], [$0.0939$], [$-0.0060$], [$0.997$], [No],
    [event_control], [BOAS], [`e`], [$0.2740$], [$0.2724$], [$-0.0016$], [$0.9996$], [No],
    [event_control], [ANPHY], [`e_m`], [$0.4876$], [$0.4765$], [$-0.0111$], [$0.358$], [No],
    [event_control], [BOAS], [`e_m`], [$0.3967$], [$0.3502$], [$-0.0465$], [$0.742$], [No],
    [event_prefar], [ANPHY], [`e`], [$-0.0099$], [$-0.0106$], [$-0.0008$], [$0.9996$], [No],
    [event_prefar], [BOAS], [`e`], [$0.0368$], [$0.0358$], [$-0.0009$], [$0.9993$], [No],
    [event_prefar], [ANPHY], [`e_m`], [$0.0356$], [$-0.0021$], [$-0.0377$], [$0.215$], [No],
    [event_prefar], [BOAS], [`e_m`], [$0.0053$], [$-0.0409$], [$-0.0461$], [$0.587$], [No],
  ),
  caption: [Non-identical rows of the full Pass B table. All 36 rows (including the 28 identical ones) are in the source CSV. Source: `results/rvc_sleep_20260703/04_pass_b_surface_sensitivity/pass_b_surface_sensitivity.csv`.]
) <tab-passb-full>

= S2.4 Pass C EAP moderation (full 54-test family, ANPHY and BOAS)

#figure(
  kind: table,
  clean-table(
    columns: (1fr, 1fr, 1.2fr, 0.7fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center, center, center, center),
    inset: 4pt,
    table.header([*Delta mode*], [*Dataset*], [*Anchor (primary)*], [*Endp.*], [*coef*], [*$p$*], [*FDR $q$*]),
    [event_control], [ANPHY], [`ecg_hrv_rmssd_ms`], [`m`], [$0.00082$], [$0.074$], [$0.132$],
    [event_control], [ANPHY], [`ecg_hrv_rmssd_ms`], [`d`], [$0.00055$], [$0.045$], [$0.101$],
    [event_control], [ANPHY], [`ecg_hrv_rmssd_ms`], [`e`], [$0.00039$], [$0.033$], [$0.100$],
    [event_control], [ANPHY], [`ecg_hrv_rmssd_ms`], [`d_n`], [$0.00007$], [$0.900$], [$0.904$],
    [event_control], [ANPHY], [`ecg_hrv_rmssd_ms`], [`d_l`], [$0.00097$], [$<0.001$], [$0.0015$ #sym.dagger],
    [event_control], [ANPHY], [`ecg_hrv_rmssd_ms`], [`d_s`], [$0.00007$], [$0.904$], [$0.904$],
    [event_control], [ANPHY], [`ecg_hrv_rmssd_ms`], [`e_e`], [$0.00069$], [$0.097$], [$0.145$],
    [event_control], [ANPHY], [`ecg_hrv_rmssd_ms`], [`e_s`], [$0.00014$], [$0.741$], [$0.904$],
    [event_control], [ANPHY], [`ecg_hrv_rmssd_ms`], [`e_m`], [$0.00092$], [$0.031$], [$0.100$],
    [event_control], [BOAS], [`resp_regular_index`], [`m`], [$-0.667$], [$0.296$], [$0.381$],
    [event_control], [BOAS], [`resp_regular_index`], [`d`], [$-0.879$], [$0.093$], [$0.261$],
    [event_control], [BOAS], [`resp_regular_index`], [`e`], [$-0.681$], [$0.126$], [$0.261$],
    [event_control], [BOAS], [`resp_regular_index`], [`d_n`], [$-1.251$], [$0.145$], [$0.261$],
    [event_control], [BOAS], [`resp_regular_index`], [`d_l`], [$-0.926$], [$0.077$], [$0.261$],
    [event_control], [BOAS], [`resp_regular_index`], [`d_s`], [$-0.281$], [$0.703$], [$0.703$],
    [event_control], [BOAS], [`resp_regular_index`], [`e_e`], [$-0.554$], [$0.369$], [$0.415$],
    [event_control], [BOAS], [`resp_regular_index`], [`e_s`], [$-0.722$], [$0.238$], [$0.357$],
    [event_control], [BOAS], [`resp_regular_index`], [`e_m`], [$-1.055$], [$0.057$], [$0.261$],
  ),
  caption: [Pass C primary-anchor rows (`event_control` delta mode; the `event_prefar` delta mode and the BOAS `anchor_index_v02` sensitivity-anchor rows follow the identical pattern - all null except the flagged exception). #sym.dagger = ANPHY `d_l` survives pooled FDR ($q=0.0015$) but fails its own subject-level-slope sensitivity check ($p_"slope, perm" = 0.140$, ns; see manuscript R5) and is treated as a non-robust pooled-model artifact. All 54 rows (2 delta modes $times$ 3 anchor models $times$ 9 endpoints) are in the source CSV. Source: `results/rvc_sleep_20260703/05_pass_c_eap_moderation/pass_c_eap_moderation.csv`.]
) <tab-passc-full>

= S2.5 RichSleep EAP moderation (full anchor family, `event_control` delta mode)

#figure(
  kind: table,
  clean-table(
    columns: (1.5fr, 0.7fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center, center),
    inset: 4pt,
    table.header([*Anchor*], [*Endp.*], [*coef*], [*$p$*], [*FDR $q$*]),
    [`cardioresp_anchor_index` (primary)], [`m`], [$0.0035$], [$0.916$], [$0.916$],
    [`cardioresp_anchor_index` (primary)], [`d`], [$0.0235$], [$0.477$], [$0.858$],
    [`cardioresp_anchor_index` (primary)], [`e`], [$0.0490$], [$0.150$], [$0.594$],
    [`cardioresp_anchor_index` (primary)], [`d_n`], [$-0.0219$], [$0.665$], [$0.899$],
    [`cardioresp_anchor_index` (primary)], [`d_l`], [$0.0417$], [$0.198$], [$0.594$],
    [`cardioresp_anchor_index` (primary)], [`d_s`], [$0.0423$], [$0.398$], [$0.858$],
    [`cardioresp_anchor_index` (primary)], [`e_e`], [$0.0765$], [$0.035$], [$0.316$],
    [`cardioresp_anchor_index` (primary)], [`e_s`], [$0.0108$], [$0.799$], [$0.899$],
    [`cardioresp_anchor_index` (primary)], [`e_m`], [$-0.0147$], [$0.709$], [$0.899$],
    [`anchor_index` (sensitivity)], [`e_e`], [$-1.5 times 10^(-8)$], [$<0.001$], [$0.0038$ #sym.dagger],
    [`anchor_index` (sensitivity)], [`e_m`], [$2.0 times 10^(-8)$], [$<0.001$], [$<0.001$ #sym.dagger],
    [`anchor_index_v02` (sensitivity)], [`d`], [$-9.7 times 10^(-9)$], [$<0.001$], [$<0.001$ #sym.dagger],
    [`anchor_index_v02` (sensitivity)], [`d_l`], [$-1.1 times 10^(-8)$], [$<0.001$], [$<0.001$ #sym.dagger],
    [`sympathetic_index` (sensitivity)], [`e_e`], [$-7.5 times 10^(-9)$], [$<0.001$], [$0.0038$ #sym.dagger],
    [`sympathetic_index` (sensitivity)], [`e_m`], [$1.0 times 10^(-8)$], [$<0.001$], [$<0.001$ #sym.dagger],
    [`resp_anchor_index` (sensitivity)], [`m`], [$0.0524$], [$0.227$], [$0.396$],
    [`resp_anchor_index` (sensitivity)], [`d`], [$0.0061$], [$0.932$], [$0.932$],
    [`resp_anchor_index` (sensitivity)], [`d_l`], [$0.0387$], [$0.468$], [$0.596$],
    [`resp_anchor_index` (sensitivity)], [`e_m`], [$-0.0099$], [$0.891$], [$0.920$],
    [`ocular_stability_index` (sensitivity)], [`d_l`], [$-2.2 times 10^(-9)$], [$<0.001$], [$<0.001$ #sym.dagger],
  ),
  caption: [RichSleep EAP-moderation table, `event_control` delta mode, $N=24$ subjects, on the QA-corrected `neuralmanifolddynamics_RichSleep_20260709_100219` export (the `event_prefar` mode and all coefficients/SEs are in the source CSV, 126 total rows across both delta modes and 7 anchors). #sym.dagger = nominal FDR survivor with a coefficient magnitude ($approx 10^(-8)$-$10^(-9)$ per unit of a large-scale raw composite index) read as a scale/multicollinearity artifact rather than genuine moderation (manuscript R6, S1.7). `resp_anchor_index`'s `event_control`-mode coefficients are a clean null, matching the primary anchor's pattern exactly - see S2.5a for an exploratory pattern found under an alternative delta-mode specification. The primary, mechanistically-motivated anchor (`cardioresp_anchor_index`) shows no FDR survivors at all. Source: `results/rvc_sleep_20260709/09_richsleep_verification/richsleep_eap_moderation.csv`.]
) <tab-richsleep-eap>

== S2.5a `resp_anchor_index`: sensitivity-anchor exploratory result

The `resp_anchor_index` sensitivity model in Table @tab-richsleep-eap is null in the primary `event_control` delta mode ($p approx 0.23$-$0.93$ on `m`, `d`, `d_l`, `e_m`), matching the primary anchor's null pattern. Under the alternative `event_prefar` delta-mode specification, a weaker, exploratory pattern emerges on four endpoints:

#figure(
  kind: table,
  clean-table(
    columns: (0.55fr, 0.8fr, 0.75fr, 0.85fr, 0.85fr, 0.9fr, 0.95fr),
    align: (left, center, center, center, center, center, center),
    inset: 4pt,
    table.header([*Endp.*], [*coef*], [*$p$*], [*FDR $q$*], [*joint $q$ (108)*], [*excl. slope-outlier*], [*excl. value-outlier*]),
    [`d`], [$+0.111$], [$0.0087$], [$0.0151$], [$0.0213$], [$p=0.075$ (loses sig. by Wilcoxon)], [$p=0.0077$ (holds)],
    [`e`], [$+0.102$], [$0.0003$], [$0.0006$], [$0.0010$], [$p=0.005$ (strengthens)], [$p=0.0002$ (holds)],
    [`d_n`], [$+0.285$], [$0.0005$], [$0.0011$], [$0.0017$], [$p=0.02$ (holds)], [$p=0.0005$ (holds)],
    [`e_s`], [$+0.205$], [$0.0002$], [$0.0006$], [$0.0009$], [$p=0.009$ (holds)], [$p=0.0002$ (holds)],
    [`e_e`], [$+0.030$], [$0.035$], [$0.0501$ (boundary)], [$0.0732$ (fails)], [-], [$p=0.039$ (unchanged, still weak)],
  ),
  caption: [`resp_anchor_index_pre_far` moderation, `event_prefar` delta mode, with two robustness checks beyond scale/multicollinearity/single-subject-outlier (all of which this pattern also passes: $approx[-1,1]$ anchor scale, max $|r|=0.18$ with the primary anchor/covariates). *Joint $q$ (108)*: BH-FDR recomputed pooling both delta modes' 108 sensitivity-anchor tests into one family - a stricter check against testing two delta-mode specifications; `d`/`e`/`d_n`/`e_s` all survive ($q<=0.021$), `e_e` does not ($q=0.073$) and is downgraded from boundary to non-significant. *Excl. slope-outlier*: Wilcoxon signed-rank $p$ on subject-level slopes after excluding the single subject with the most extreme fitted slope; `d` alone loses significance. *Excl. value-outlier*: WLS-cluster coefficient $p$ after excluding the single subject with the most extreme *raw* `resp_anchor_index` value instead - a different, complementary outlier check; all coefficients are essentially unchanged, none lose significance. Source: `results/rvc_sleep_20260709/11_richsleep_resp_anchor_followup/{resp_anchor_robustness_checks,check5_joint_fdr_108,check6_anchor_value_outlier_exclusion}.csv`.]
) <tab-resp-anchor-prefar>

This pattern is not a scale, multicollinearity, or single-outlier artifact (in either the slope-influence or raw-value sense), and holds up under a substantially stricter joint-family FDR correction across both delta-mode specifications tested. Three of the four survivors (`e`, `d_n`, `e_s`) pass every check attempted; `d` is the one exception, losing significance specifically when the most-influential-slope subject is excluded (though not when the most-extreme-value subject is excluded instead) - a genuine, if narrower, weakness worth naming rather than glossing over. `e_e`, previously reported at the FDR boundary, is downgraded to non-significant under the stricter joint correction and should not be read as a fifth survivor. This anchor's `event_control`-mode signal was previously found to be null after an upstream construction-bug fix (manuscript R6); given that history, "passed every artifact check attempted" is treated as a hypothesis for a dedicated, independently-replicated test - not as proof of a genuine effect.

= S2.6 RichSleep phase-resolved EAP mechanism test (Aim B + Aim C, manuscript R6b)

#figure(
  kind: table,
  clean-table(
    columns: (1.3fr, 0.9fr, 0.9fr, 1fr, 1fr),
    align: (left, center, center, center, center),
    inset: 4pt,
    table.header([*Level*], [*Channel*], [*$N$*], [*$R$*], [*$p$*]),
    [Within-subject, median across 24 subj.], [`phi_cardiac_onset`], [24 subj.], [$0.307$ (median)], [0/24 FDR-sig.],
    [Within-subject, median across 24 subj.], [`phi_resp_onset`], [24 subj.], [$0.324$ (median)], [0/24 FDR-sig.],
    [Second-order (population)], [`phi_cardiac_onset`], [24 subj.], [$0.160$], [$0.547$],
    [Second-order (population)], [`phi_resp_onset`], [24 subj.], [$0.109$], [$0.755$],
  ),
  caption: [Aim B: spindle-onset cardiac/respiratory phase-locking, Rayleigh test (Zar 1999 large-sample approximation). "Within-subject" summarizes 24 independent per-subject Rayleigh tests per channel (full per-subject $R$/$p$/FDR-$q$ in the source CSV); "second-order" is a single Rayleigh test on the 24 subject-level mean-direction angles, testing for a common population-level preferred phase. Both null at every level. Subjects with $n=1$–$2$ events are not Rayleigh-testable. Source: `results/rvc_sleep_20260708/10_richsleep_phase_resolved_eap/molB_within_subject_phase_locking.csv`, `molB_second_order_population_phase.csv`.]
) <tab-richsleep-molb>

#figure(
  kind: table,
  clean-table(
    columns: (1fr, 0.9fr, 0.9fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center, center, center),
    inset: 4pt,
    table.header([*Delta mode*], [*Endpoint*], [*$N$ events*], [*coef*], [*$p$*], [*FDR $q$*]),
    [`event_control`], [`m`], [172], [$-1.03 times 10^4$], [$0.839$], [$0.904$],
    [`event_control`], [`d`], [172], [$+1.06 times 10^4$], [$0.658$], [$0.904$],
    [`event_control`], [`e`], [172], [$-4.77 times 10^3$], [$0.882$], [$0.904$],
    [`event_control`], [`d_n`], [172], [$+5.82 times 10^3$], [$0.904$], [$0.904$],
    [`event_control`], [`d_l`], [172], [$-4.09 times 10^3$], [$0.903$], [$0.904$],
    [`event_control`], [`d_s`], [172], [$+8.56 times 10^4$], [$0.100$], [$0.904$],
    [`event_control`], [`e_e`], [172], [$-4.08 times 10^4$], [$0.323$], [$0.904$],
    [`event_control`], [`e_s`], [172], [$+3.90 times 10^4$], [$0.231$], [$0.904$],
    [`event_control`], [`e_m`], [172], [$+1.25 times 10^4$], [$0.836$], [$0.904$],
    [`event_prefar`], [`m`], [160], [$+1.56 times 10^5$], [$0.175$], [$0.789$],
    [`event_prefar`], [`d`], [160], [$-1.50 times 10^4$], [$0.819$], [$0.922$],
    [`event_prefar`], [`e`], [160], [$-2.03 times 10^4$], [$0.673$], [$0.922$],
    [`event_prefar`], [`d_n`], [160], [$-1.35 times 10^5$], [$0.531$], [$0.922$],
    [`event_prefar`], [`d_l`], [160], [$+4.23 times 10^4$], [$0.275$], [$0.826$],
    [`event_prefar`], [`d_s`], [160], [$+3.07 times 10^4$], [$0.734$], [$0.922$],
    [`event_prefar`], [`e_e`], [160], [$-9.06 times 10^2$], [$0.962$], [$0.962$],
    [`event_prefar`], [`e_s`], [160], [$-5.19 times 10^4$], [$0.604$], [$0.922$],
    [`event_prefar`], [`e_m`], [160], [$+8.64 times 10^4$], [$0.158$], [$0.789$],
  ),
  caption: [Aim C: `hep_amplitude_pre_far` moderation of the spindle-locked geometry response, WLS-cluster (weights $=1"/"n_"events, subject"$, cluster-robust SE by subject) + centered nuisance covariates, identical machinery to the manuscript R6/Pass C moderation models. Large coefficient magnitudes ($approx 10^4$-$10^5$) reflect `hep_amplitude_pre_far`'s presumably microvolt-scale raw units, not an anomaly. 0/18 tests FDR-significant; companion subject-level-slope sign-flip permutation test (source CSV) agrees at every endpoint. Source: `results/rvc_sleep_20260708/10_richsleep_phase_resolved_eap/molC_hep_moderation.csv`.]
) <tab-richsleep-molc>

Both mechanism-level tests use the window-N2, geometry-valid RichSleep event-bin population (190 of 2,253 raw `event`-bin rows; 24 subjects, ~7-8 events/subject on average). The 190/2,253 split is a stage-window mismatch (S1.1, S1.8): the detector used N2 hypnogram epochs; the event-locked `stage` label is the 30 s MNPS window centre. This is a conservative construct-validity filter, not evidence that YASA detected non-N2 spindles. Tonic EAP mixed-bin row counts (2,260–2,435) are a different object and must not be compared with 190 as unique-spindle $N$.

= S2.7 Nuisance-covariate coverage by pass

#figure(
  clean-table(
    columns: (1.6fr, 2.6fr),
    align: (left, left),
    inset: 4pt,
    table.header([*Pass*], [*Covariates retained ($>= 50%$ coverage)*]),
    [Pass C, ANPHY], [`event_duration_sec`, `window_center_sec`, `ocular_stability_index`, `sympathetic_index`, `vagal_index`, `eog_quality_quality`, `ecg_quality_quality`, `anchor_support_fraction_quality`],
    [Pass C, BOAS], [same family as ANPHY, coverage-permitting per anchor model],
    [RichSleep EAP moderation], [`event_duration_sec`, `window_center_sec`, `ocular_stability_index`, `sympathetic_index`, `vagal_index`, `eog_quality_quality`, `ecg_quality_quality`, `resp_quality_quality`, `cardioresp_quality_quality`, `anchor_support_fraction_quality`],
  ),
  caption: [Covariates actually included after `available_covariates()` filtering (S1.6). `frequency_hz` is requested defensively in every pass but is never present in the NMD event-locked schema and is always dropped.]
) <tab-covariates>

= S2.8 Descriptive summary by dataset

#figure(
  clean-table(
    columns: (1.1fr, 0.8fr, 1fr, 1fr, 1.3fr),
    align: (left, center, center, center, center),
    inset: 4pt,
    table.header([*Dataset*], [*$N$ subj.*], [*Median events/subj.*], [*Range*], [*Total spindle events*]),
    [ANPHY], [27], [$approx 40$], [-], [1,076],
    [BOAS (ds005555)], [128], [5], [1-18], [634],
    [RichSleep], [24], [$approx 161$], [14-362], [46,058 raw (all bins) / 3,900 filtered],
  ),
  caption: [Per-subject spindle-event distribution. BOAS's sparse, uneven event counts (median 5, range 1-18) directly motivated the subject-weighted A1r/A2r protocol amendment (S1.6). RichSleep's per-subject counts (14-362, from `event_level_richsleep.parquet`) are comparably uneven; the same subject-weighted machinery was applied without modification. All 24 subjects are usable on this ingest.]
) <tab-descriptive>

#bibliography("references.bib", style: "apa")
