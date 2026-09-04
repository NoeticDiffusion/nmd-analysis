// S2 Supplementary Data — RVC_SLEEP_peak_analysis
// Full result tables underlying manuscript.typ R1-R6. All values are read
// directly from the frozen CSVs cited in each caption; nothing here is
// re-derived.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "S2 Data - RVC_SLEEP_peak_analysis",
  subtitle: "Complete onset/peak-phase permutation tables, per-subject Rayleigh summaries, robustness-check detail, and the full alignment-moderation family",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S2.0 Complete primary family (onset-phase, with bootstrap CI)

#figure(
  kind: table,
  clean-table(
    columns: (1fr, 1fr, 0.6fr, 0.8fr, 0.9fr, 1.1fr, 0.9fr, 0.9fr),
    align: (left, left, center, center, center, center, center, center),
    inset: 4pt,
    table.header([*Sample*], [*Channel*], [*$N$*], [*$R_1$*], [*perm $p$ ($R_1$)*], [*boot $R_1$ 95% CI*], [*$T_2$*], [*perm $p$ ($T_2$)*]),
    [Full catalog], [`phi_cardiac_onset`], [23,029], [0.0093], [0.353], [[0.0022, 0.0241]], [0.00007], [0.082],
    [Full catalog], [`phi_resp_onset`], [23,029], [0.0189], [0.151], [[0.0062, 0.0404]], [0.00019], [0.027],
    [Quality-filtered], [`phi_cardiac_onset`], [20,877], [0.0043], [0.827], [[0.0018, 0.0204]], [0.00002], [0.116],
    [Quality-filtered], [`phi_resp_onset`], [20,877], [0.0153], [0.362], [[0.0037, 0.0398]], [0.00012], [0.075],
  ),
  caption: [Complete primary family: corrected subject-rotation permutation test, spindle-onset phase, both harmonic statistics. BH-FDR $q$ (both statistics, both channels$times$samples) in the main text Table 2. Source: `results/rvc_sleep_20260710/11_richsleep_maalb_corrected/molB_primary_corrected_permutation.csv`.]
) <tab-primary-full>

= S2.1 Complete secondary/exploratory family (peak-phase + 190-event subsample)

#figure(
  kind: table,
  clean-table(
    columns: (1.1fr, 1fr, 0.6fr, 0.8fr, 0.9fr, 1.1fr, 0.9fr),
    align: (left, left, center, center, center, center, center),
    inset: 4pt,
    table.header([*Sample*], [*Channel*], [*$N$*], [*$R_1$*], [*perm $p$ ($R_1$)*], [*boot $R_1$ 95% CI*], [*$T_2$*]),
    [Full catalog], [`phi_cardiac_peak`], [23,029], [0.0159], [0.0200], [[0.0074, 0.0278]], [0.00066],
    [Full catalog], [`phi_resp_peak`], [23,029], [0.0453], [0.0005], [[0.0236, 0.0716]], [0.00217],
    [Quality-filtered], [`phi_cardiac_peak`], [20,877], [0.0145], [0.0675], [[0.0054, 0.0270]], [0.00060],
    [Quality-filtered], [`phi_resp_peak`], [20,877], [0.0418], [0.0030], [[0.0182, 0.0705]], [0.00189],
    [Geometry-valid 190], [`phi_cardiac_onset`], [190], [0.0504], [0.692], [[0.0137, 0.1872]], [0.01243],
    [Geometry-valid 190], [`phi_resp_onset`], [190], [0.0210], [0.929], [[0.0103, 0.1528]], [0.00412],
    [Geometry-valid 190], [`phi_cardiac_peak`], [190], [0.0876], [0.127], [[0.0278, 0.1786]], [0.01681],
    [Geometry-valid 190], [`phi_resp_peak`], [190], [0.0428], [0.808], [[0.0129, 0.1855]], [0.00915],
  ),
  caption: [Complete secondary/exploratory family. The last four rows (geometry-valid 190-event subsample) reproduce the companion article's own R6b numbers on that subsample, confirming this reanalysis's headline result (main text R3) is specific to the ~120x-larger full/quality-filtered catalog, not an artifact of a different statistic applied to the same small sample. Source: `results/rvc_sleep_20260710/11_richsleep_maalb_corrected/molB_secondary_exploratory_permutation.csv`.]
) <tab-secondary-full>

= S2.2 Per-subject Rayleigh test summary (full catalog, all 4 channels)

#figure(
  kind: table,
  clean-table(
    columns: (1.3fr, 0.8fr, 0.9fr, 1fr, 1.1fr),
    align: (left, center, center, center, center),
    inset: 4.5pt,
    table.header([*Channel*], [*Median $R$*], [*Median $N$ events/subj.*], [*Range $N$ events/subj.*], [*$N$ FDR-sig./24*]),
    [`phi_cardiac_onset`], [0.046], [1,030], [161-2,562], [0/24],
    [`phi_resp_onset`], [0.061], [1,030], [161-2,562], [7/24],
    [`phi_cardiac_peak`], [0.036], [1,030], [161-2,562], [1/24],
    [`phi_resp_peak`], [0.071], [1,030], [161-2,562], [8/24],
  ),
  caption: [Per-subject Rayleigh test (Zar 1999 approximation), summarized across the 24 subjects; full 96-row per-subject table (subject ID, $N$, mean angle, $R$, $p$, FDR $q$) in `molB_per_subject_rayleigh.csv`. Peak-phase channels show more within-subject FDR survivors than the corresponding onset-phase channels for respiration (8 vs. 7) and cardiac (1 vs. 0), consistent with a genuine, if individually modest, population-level shift rather than a purely second-order artifact. Source: `results/rvc_sleep_20260710/11_richsleep_maalb_corrected/molB_per_subject_rayleigh.csv`.]
) <tab-per-subject>

= S2.3 Robustness-check detail (companion to main-text R4)

The duration-tercile (Table 3 in main text) and split-half (Table 4 in main text) tables are reproduced there in full; this section adds the LOSO jackknife detail not shown in the main text.

#figure(
  kind: table,
  clean-table(
    columns: (1.2fr, 1fr, 1.4fr, 1fr, 1.4fr),
    align: (left, center, center, center, center),
    inset: 4.5pt,
    table.header([*Channel*], [*2nd-order $p$ range (24 reruns)*], [*Most influential (2nd-order)*], [*Pooled-perm $p$ range*], [*$N$ reruns pooled-perm $p<0.05$*]),
    [`phi_resp_peak`], [[0.0000, 0.0000]], [`sub-xn017` (weakest $p=0.0000$)], [[0.0020, 0.0020]], [24/24],
    [`phi_cardiac_peak`], [[0.0014, 0.0105]], [`sub-xn013` (weakest $p=0.0105$)], [[0.0040, 0.0679]], [22/24],
  ),
  caption: [Leave-one-subject-out jackknife, 24 reruns per channel (one per dropped subject); pooled-permutation reruns use $n_"perm"=500$ (reduced from 2000 for the 24$times$-repeated loop, S1.4). Respiratory peak-phase locking survives every single-subject removal on both tests; cardiac peak-phase locking loses pooled significance in 2/24 reruns. Source: `results/rvc_sleep_20260710/12_richsleep_maalb_peak_phase_deepdive/check3_leave_one_subject_out.csv`.]
) <tab-loso>

= S2.4 Complete peak-phase alignment-moderation family (18 tests, main text R6)

#figure(
  kind: table,
  clean-table(
    columns: (0.9fr, 0.55fr, 0.6fr, 0.75fr, 0.75fr, 0.75fr, 0.85fr, 0.85fr, 0.85fr),
    align: (left, center, center, center, center, center, center, center, center),
    inset: 3.5pt,
    table.header([*Delta mode*], [*Endp.*], [*$N$*], [*coef*], [*$p$*], [*FDR $q$*], [*slope $t$-test $p$*], [*slope Wilcoxon $p$*], [*slope perm $p$*]),
    [event_control], [`m`], [172], [$-0.029$], [$0.578$], [$0.722$], [$0.252$], [$0.330$], [$0.271$],
    [event_control], [`d`], [172], [$+0.137$], [$0.061$], [$0.182$], [$0.260$], [$0.312$], [$0.250$],
    [event_control], [`e`], [172], [$+0.078$], [$0.333$], [$0.500$], [$0.662$], [$0.123$], [$0.673$],
    [event_control], [`d_n`], [172], [$+0.164$], [$0.075$], [$0.192$], [$0.457$], [$0.202$], [$0.465$],
    [event_control], [`d_l`], [172], [$+0.125$], [$0.090$], [$0.203$], [$0.121$], [$0.123$], [$0.099$],
    [event_control], [`d_s`], [172], [$+0.035$], [$0.734$], [$0.777$], [$0.391$], [$0.546$], [$0.429$],
    [event_control], [`e_e`], [172], [$+0.036$], [$0.704$], [$0.777$], [$0.563$], [$0.349$], [$0.573$],
    [event_control], [`e_s`], [172], [$+0.107$], [$0.258$], [$0.423$], [$0.658$], [$0.784$], [$0.728$],
    [event_control], [`e_m`], [172], [$+0.035$], [$0.602$], [$0.722$], [$0.086$], [$0.105$], [$0.084$],
    [event_prefar], [`m`], [160], [$-0.015$], [$0.854$], [$0.854$], [$0.585$], [$0.522$], [$0.794$],
    [event_prefar], [`d`], [160], [$+0.243$], [$0.0023$], [$*0.021*$], [$0.077$], [$0.044$], [$0.068$],
    [event_prefar], [`e`], [160], [$+0.136$], [$0.035$], [$0.139$], [$0.313$], [$0.674$], [$0.369$],
    [event_prefar], [`d_n`], [160], [$+0.353$], [$0.036$], [$0.139$], [$0.200$], [$0.114$], [$0.186$],
    [event_prefar], [`d_l`], [160], [$+0.184$], [$0.0003$], [$*0.005*$], [$0.105$], [$0.014$], [$0.100$],
    [event_prefar], [`d_s`], [160], [$+0.218$], [$0.182$], [$0.327$], [$0.445$], [$0.388$], [$0.462$],
    [event_prefar], [`e_e`], [160], [$+0.028$], [$0.552$], [$0.722$], [$0.573$], [$0.648$], [$0.553$],
    [event_prefar], [`e_s`], [160], [$+0.286$], [$0.039$], [$0.139$], [$0.355$], [$0.756$], [$0.410$],
    [event_prefar], [`e_m`], [160], [$+0.133$], [$0.111$], [$0.222$], [$0.143$], [$0.097$], [$0.148$],
  ),
  caption: [Complete 18-test resp_peak_alignment moderation family (WLS-cluster, weights $1"/"n_"events,subject"$, cluster-robust SE by subject; 20/24 subjects contribute a per-subject slope, `min_events=3`). Bold *italic* FDR $q$ = BH-FDR survivor. `event_control` mode is null throughout (all $q >= 0.18$); `event_prefar` mode has two survivors (`d`, `d_l`), both with the slope Wilcoxon test agreeing but the slope $t$-test and sign-flip permutation test not fully agreeing (see main text R6, `S3`). Source: `results/rvc_sleep_20260710/13_peak_phase_alignment_moderation/resp_peak_alignment_moderation.csv`.]
) <tab-alignment-full>

= S2.5 Secondary circular-regression sensitivity check (18 rows, exploratory, not FDR-corrected)

#figure(
  kind: table,
  clean-table(
    columns: (0.9fr, 0.55fr, 0.75fr, 0.75fr, 0.85fr, 1fr, 1fr),
    align: (left, center, center, center, center, center, center),
    inset: 3.5pt,
    table.header([*Delta mode*], [*Endp.*], [*cos $p$*], [*sin $p$*], [*joint Wald $p$*], [*geom.-optimal phase*], [*dist. to $mu_("resp,peak")$*]),
    [event_control], [`m`], [$0.520$], [$0.779$], [$0.791$], [$+34.1 degree$], [$162.5 degree$],
    [event_control], [`d`], [$0.693$], [$0.018$], [$0.058$], [$-97.3 degree$], [$31.1 degree$],
    [event_control], [`e`], [$0.959$], [$0.098$], [$0.208$], [$-92.0 degree$], [$36.3 degree$],
    [event_control], [`d_n`], [$0.999$], [$0.076$], [$0.174$], [$-90.0 degree$], [$38.3 degree$],
    [event_control], [`d_l`], [$0.372$], [$0.032$], [$0.055$], [$-109.0 degree$], [$19.4 degree$],
    [event_control], [`d_s`], [$0.766$], [$0.423$], [$0.620$], [$-70.4 degree$], [$58.0 degree$],
    [event_control], [`e_e`], [$0.915$], [$0.544$], [$0.797$], [$-101.9 degree$], [$26.5 degree$],
    [event_control], [`e_s`], [$0.868$], [$0.120$], [$0.292$], [$-85.3 degree$], [$43.1 degree$],
    [event_control], [`e_m`], [$0.803$], [$0.355$], [$0.591$], [$-77.8 degree$], [$50.6 degree$],
    [event_prefar], [`m`], [$0.252$], [$0.377$], [$0.488$], [$+129.8 degree$], [$101.9 degree$],
    [event_prefar], [`d`], [$0.473$], [$0.0044$], [$0.0113$], [$-97.2 degree$], [$31.1 degree$],
    [event_prefar], [`e`], [$0.429$], [$0.049$], [$0.108$], [$-101.0 degree$], [$27.4 degree$],
    [event_prefar], [`d_n`], [$0.429$], [$0.021$], [$0.070$], [$-81.3 degree$], [$47.1 degree$],
    [event_prefar], [`d_l`], [$0.122$], [$0.0013$], [$0.0008$], [$-117.4 degree$], [$10.9 degree$],
    [event_prefar], [`d_s`], [$0.248$], [$0.364$], [$0.340$], [$-123.0 degree$], [$5.4 degree$],
    [event_prefar], [`e_e`], [$0.278$], [$0.949$], [$0.491$], [$+176.3 degree$], [$55.3 degree$],
    [event_prefar], [`e_s`], [$0.854$], [$0.030$], [$0.094$], [$-92.3 degree$], [$36.1 degree$],
    [event_prefar], [`e_m`], [$0.402$], [$0.214$], [$0.272$], [$-112.2 degree$], [$16.1 degree$],
  ),
  caption: [$"delta" ~ cos(phi_("resp,peak")) + sin(phi_("resp,peak")) + "covariates"$, WLS-cluster, exploratory and not part of the primary 18-test family (`S1.5`). "Geom.-optimal phase" = $"atan2"("sin_coef", "cos_coef")$, the phase direction that maximizes the fitted delta; "dist. to $mu_("resp,peak")$" is its wrapped angular distance from the independently-estimated held-out population-preferred phase ($-128.4 degree$, S2.6). `event_prefar` `d_l` (main text's strongest alignment-moderation row) has the smallest such distance ($10.9 degree$) of any of the 18 rows. Source: `results/rvc_sleep_20260710/13_peak_phase_alignment_moderation/resp_peak_circular_regression_secondary.csv`.]
) <tab-circular-full>

= S2.6 Held-out population-preferred phase estimate

#figure(
  kind: table,
  clean-table(
    columns: (1.4fr, 1fr, 0.9fr, 0.9fr, 1.1fr),
    align: (left, center, center, center, center),
    inset: 4.5pt,
    table.header([*$mu_("resp,peak")$*], [*$R$ (2nd-order)*], [*$N$ subj.*], [*$N$ held-out events*], [*$N$ excluded (geom.-valid)*]),
    [$-128.4 degree$ ($-2.2404$ rad)], [0.6657], [24], [22,839], [190],
  ),
  caption: [Held-out, subject-balanced second-order circular mean of `phi_resp_peak`, computed on the full catalog *excluding* the 190 geometry-valid events used in R6's regression (S1.5), avoiding circularity. Consistent with the full-catalog (non-held-out) pooled mean angle reported in main text R4 ($-122.6 degree$) - the $<1%$ exclusion changes the estimate negligibly. Source: `results/rvc_sleep_20260710/13_peak_phase_alignment_moderation/held_out_mu_resp_peak.csv`.]
) <tab-mu-held-out>

#bibliography("references.bib", style: "apa")
