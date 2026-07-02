#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "S2 Data — MNJ Task Geometry (ds004511)",
  subtitle: "Complete contrast tables for MNPS, MNJ, regional/block Jacobian, EAP coupling, and physiological confounds",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S2.0 Complete global MNPS contrast table

All nine pre-specified pairwise contrasts (3 MNPS coordinates × 3 task pairs), Wilcoxon signed-rank test on session medians, BH-FDR applied across all nine simultaneously. Group medians (median of subject-level session medians) are shown per task. None survive correction — the global MNPS null reported as R2 in the main text.

#figure(
  kind: table,
  clean-table(
    columns: (0.8fr, 1.6fr, 1fr, 1fr, 1fr, 0.9fr, 0.9fr, 0.7fr),
    align: left,
    inset: 3.5pt,
    table.header(
      [*Coord.*], [*Contrast*], [*GG med.*], [*CC med.*], [*Rest med.*], [*$d$*], [*FDR $q$*], [*Sig.*]
    ),
    [`m`], [GG vs CC], [`0.0237`], [`0.0185`], [—], [`0.121`], [`0.541`], [No],
    [`m`], [GG vs Rest], [`0.0237`], [—], [`0.0178`], [`0.207`], [`0.540`], [No],
    [`m`], [CC vs Rest], [—], [`0.0185`], [`0.0178`], [`0.101`], [`0.541`], [No],
    [`d`], [GG vs CC], [`0.0458`], [`0.0473`], [—], [`-0.071`], [`0.541`], [No],
    [`d`], [GG vs Rest], [`0.0458`], [—], [`0.0593`], [`-0.269`], [`0.541`], [No],
    [`d`], [CC vs Rest], [—], [`0.0473`], [`0.0593`], [`-0.177`], [`0.665`], [No],
    [`e`], [GG vs CC], [`0.0196`], [`0.0285`], [—], [`-0.256`], [`0.540`], [No],
    [`e`], [GG vs Rest], [`0.0196`], [—], [`0.0093`], [`0.044`], [`0.940`], [No],
    [`e`], [CC vs Rest], [—], [`0.0285`], [`0.0093`], [`0.213`], [`0.541`], [No],
  ),
  caption: [Complete global MNPS pairwise contrast table (Wilcoxon signed-rank, session medians, BH-FDR over all 9 rows). $N = 44$ for GG-involving pairs, $N = 45$ for CC vs. Rest. Group medians are the median across subjects of each subject's session-median coordinate value. No coordinate differentiates any task pair after correction. Friedman omnibus (3-condition): `m` $chi^2 = 1.41$, $p = 0.49$; `d` $chi^2 = 1.14$, $p = 0.57$; `e` $chi^2 = 2.91$, $p = 0.23$. Source: `01_cross_task_mnps/mnps_pairwise.csv`, `mnps_cross_task_global.csv`, `mnps_friedman.csv`.]
) <tab-mnps-full>

= S2.1 Complete MNJ contrast table

All 21 pre-specified pairwise contrasts (7 MNJ metrics × 3 task pairs), Wilcoxon signed-rank on session medians, BH-FDR across all 21 simultaneously. This is the source table for the summary shown in the main text (R3); note that the main-text statistical-design paragraph (§Methods) describes an 18-test primary family (6 metrics, excluding `trace`) for the headline FDR claim, while this supplementary table reports the full 21-test family including `trace` for completeness.

#figure(
  kind: table,
  clean-table(
    columns: (1.5fr, 1.6fr, 1fr, 1fr, 1fr, 0.9fr, 0.9fr, 0.7fr),
    align: left,
    inset: 3.5pt,
    table.header(
      [*Metric*], [*Contrast*], [*GG med.*], [*CC med.*], [*Rest med.*], [*$d$*], [*FDR $q$*], [*Sig.*]
    ),
    [`frobenius_norm`], [GG vs CC], [`0.1560`], [`0.1280`], [—], [`1.620`], [`5.6e-12`], [Yes],
    [`frobenius_norm`], [GG vs Rest], [`0.1560`], [—], [`0.1310`], [`0.738`], [`2.8e-5`], [Yes],
    [`frobenius_norm`], [CC vs Rest], [—], [`0.1280`], [`0.1310`], [`-0.229`], [`0.284`], [No],
    [`rotation_norm`], [GG vs CC], [`0.0905`], [`0.0798`], [—], [`1.005`], [`7.7e-8`], [Yes],
    [`rotation_norm`], [GG vs Rest], [`0.0905`], [—], [`0.0861`], [`0.098`], [`0.331`], [No],
    [`rotation_norm`], [CC vs Rest], [—], [`0.0798`], [`0.0861`], [`-0.401`], [`0.034`], [Yes],
    [`trace`], [GG vs CC], [`-0.0035`], [`0.0015`], [—], [`-0.240`], [`0.182`], [No],
    [`trace`], [GG vs Rest], [`-0.0035`], [—], [`-0.0014`], [`-0.138`], [`0.350`], [No],
    [`trace`], [CC vs Rest], [—], [`0.0015`], [`-0.0014`], [`0.086`], [`0.671`], [No],
    [`spectral_radius`], [GG vs CC], [`0.0774`], [`0.0624`], [—], [`1.808`], [`5.6e-12`], [Yes],
    [`spectral_radius`], [GG vs Rest], [`0.0774`], [—], [`0.0599`], [`1.979`], [`5.6e-12`], [Yes],
    [`spectral_radius`], [CC vs Rest], [—], [`0.0624`], [`0.0599`], [`0.268`], [`0.147`], [No],
    [`rotational_power`], [GG vs CC], [`0.3699`], [`0.4034`], [—], [`-1.025`], [`1.1e-7`], [Yes],
    [`rotational_power`], [GG vs Rest], [`0.3699`], [—], [`0.4528`], [`-1.410`], [`8.1e-11`], [Yes],
    [`rotational_power`], [CC vs Rest], [—], [`0.4034`], [`0.4528`], [`-0.710`], [`7.8e-5`], [Yes],
    [`aci`], [GG vs CC], [`0.7662`], [`0.8223`], [—], [`-1.015`], [`1.0e-7`], [Yes],
    [`aci`], [GG vs Rest], [`0.7662`], [—], [`0.9097`], [`-1.340`], [`8.1e-11`], [Yes],
    [`aci`], [CC vs Rest], [—], [`0.8223`], [`0.9097`], [`-0.713`], [`6.3e-5`], [Yes],
    [`mdr`], [GG vs CC], [`0.7859`], [`0.7497`], [—], [`0.420`], [`0.006`], [Yes],
    [`mdr`], [GG vs Rest], [`0.7859`], [—], [`0.7078`], [`1.022`], [`3.1e-7`], [Yes],
    [`mdr`], [CC vs Rest], [—], [`0.7497`], [`0.7078`], [`0.703`], [`5.1e-5`], [Yes],
  ),
  caption: [Complete MNJ pairwise contrast table (Wilcoxon signed-rank, session medians, BH-FDR over all 21 rows). $N = 44$ for GG-involving pairs, $N = 45$ for CC vs. Rest. 15/21 contrasts survive FDR 5%; all 6 non-significant contrasts involve `trace`, `rotation_norm` (GG vs. Rest), or `frobenius_norm`/`spectral_radius` (CC vs. Rest), consistent with the interpretation that CC and Rest resemble each other in absolute deformation magnitude while GG is the outlier condition. Source: `03_mnj_reachability/mnj_cross_task_wilcoxon.csv`, `subject_mnj_summary.csv`.]
) <tab-mnj-full>

= S2.2 Regional MNPS contrasts (network-stratified)

MNPS coordinates were also tested within each of four cortical networks (frontal, central, parietal-occipital, temporal), applying BH-FDR separately within the 36-row family (4 networks × 3 coordinates × 3 task pairs). Full detail in `mnps_network_pairwise.csv`; the two rows surviving correction are shown below alongside the next-largest (uncorrected) effects for context.

#figure(
  kind: table,
  clean-table(
    columns: (1.3fr, 1fr, 1.6fr, 1fr, 0.9fr, 0.9fr, 0.7fr),
    align: left,
    inset: 3.5pt,
    table.header(
      [*Network*], [*Coord.*], [*Contrast*], [*$d$*], [*$p$*], [*FDR $q$*], [*Sig.*]
    ),
    [Central], [`m_median`], [GG vs CC], [`0.571`], [`0.0008`], [`0.020`], [Yes],
    [Temporal], [`m_median`], [GG vs Rest], [`0.454`], [`0.0011`], [`0.020`], [Yes],
    [Frontal], [`e_median`], [GG vs Rest], [`0.401`], [`0.015`], [`0.151`], [No],
    [Temporal], [`e_median`], [GG vs CC], [`-0.336`], [`0.019`], [`0.151`], [No],
    [Frontal], [`e_median`], [CC vs Rest], [`0.396`], [`0.021`], [`0.151`], [No],
    [Frontal], [`d_median`], [GG vs Rest], [`-0.299`], [`0.049`], [`0.291`], [No],
  ),
  caption: [Regional MNPS contrasts, top 6 of 36 rows by uncorrected $p$ (Wilcoxon signed-rank, BH-FDR within the full 36-row network family). Only two rows survive correction: mobility ($m$) is higher in gambling than cognitive control in the central network, and higher in gambling than rest in the temporal network. Both are small, spatially localized departures from the global MNPS null (S2.0) rather than a broad regional effect — 34/36 rows are non-significant. All other network × coordinate × contrast combinations had $q > 0.15$. Source: `01_cross_task_mnps/mnps_network_pairwise.csv`.]
) <tab-mnps-regional>

The presence of two significant regional rows out of 36 (5.6%) is close to the false-positive rate expected under BH-FDR at $alpha = 0.05$ applied to a family with a true null rate near 1; they should be interpreted as weak, localized signals rather than a confirmed regional MNPS effect, and are not treated as primary findings in the main text.

= S2.3 Block-level Jacobian contrasts (independent aggregation pathway)

Block-level Jacobian summaries are computed from task-segment aggregation rather than epoch-level medians (S1.2), providing an independent cross-check of the epoch-level MNJ result.

#figure(
  kind: table,
  clean-table(
    columns: (1.8fr, 1.6fr, 1fr, 0.9fr, 0.9fr, 0.7fr),
    align: left,
    inset: 3.5pt,
    table.header(
      [*Metric*], [*Contrast*], [*$d$*], [*$p$*], [*FDR $q$*], [*Sig.*]
    ),
    [`block_frobenius_mean`], [GG vs CC], [`1.695`], [`1.1e-13`], [`1.4e-12`], [Yes],
    [`block_frobenius_mean`], [GG vs Rest], [`0.596`], [`1.4e-4`], [`5.8e-4`], [Yes],
    [`block_frobenius_mean`], [CC vs Rest], [`-0.456`], [`0.0098`], [`0.015`], [Yes],
    [`block_trace_mean`], [GG vs CC], [`-0.258`], [`0.0085`], [`0.015`], [Yes],
    [`block_trace_mean`], [GG vs Rest], [`-0.030`], [`0.986`], [`0.986`], [No],
    [`block_trace_mean`], [CC vs Rest], [`0.176`], [`0.105`], [`0.125`], [No],
    [`block_anisotropy_mean`], [GG vs CC], [`0.388`], [`0.0009`], [`0.0028`], [Yes],
    [`block_anisotropy_mean`], [GG vs Rest], [`-0.146`], [`0.029`], [`0.038`], [Yes],
    [`block_anisotropy_mean`], [CC vs Rest], [`-0.151`], [`0.615`], [`0.671`], [No],
    [`c_rot_mean`], [GG vs CC], [`1.395`], [`3.8e-12`], [`2.3e-11`], [Yes],
    [`c_rot_mean`], [GG vs Rest], [`0.318`], [`0.0025`], [`0.006`], [Yes],
    [`c_rot_mean`], [CC vs Rest], [`-0.476`], [`0.0047`], [`0.009`], [Yes],
  ),
  caption: [Block-level Jacobian contrasts ($N = 44$/$45$, Wilcoxon signed-rank, BH-FDR within the 12-row block family). Friedman omnibus: `block_frobenius_mean` $chi^2 = 47.8$, $p < 10^{-10}$; `c_rot_mean` $chi^2 = 34.4$, $p < 10^{-7}$; `block_trace_mean` $chi^2 = 11.1$, $p = 0.004$; `block_anisotropy_mean` $chi^2 = 7.8$, $p = 0.021$. The GG $>$ CC Frobenius effect ($d = 1.70$) closely replicates the epoch-level result ($d = 1.62$, S2.1) using an entirely independent aggregation pathway. Source: `01_cross_task_mnps/block_jacobian_pairwise.csv`, `block_jacobian_friedman.csv`.]
) <tab-block-jacobian>

= S2.4 EAP-compatible respiratory-anchoring coupling (full table)

Session-level Spearman correlations between `resp_anchor_index` and MNJ metrics, computed separately within each task, with HRV (`ecg_hrv_rmssd_ms`) and cardiorespiratory RSA amplitude as additional physiological covariates for reference. BH-FDR applied within each task's 6-metric family.

#figure(
  kind: table,
  clean-table(
    columns: (1.6fr, 1.6fr, 1fr, 1fr, 0.8fr, 0.8fr),
    align: left,
    inset: 3.5pt,
    table.header(
      [*Task*], [*MNJ metric*], [*$r$ (resp.\ anchor)*], [*$p$*], [*FDR $q$*], [*Sig.*]
    ),
    [Gambling], [`frobenius_norm`], [`-0.216`], [`0.159`], [`0.410`], [No],
    [Gambling], [`rotation_norm`], [`-0.219`], [`0.153`], [`0.410`], [No],
    [Gambling], [`spectral_radius`], [`-0.253`], [`0.098`], [`0.410`], [No],
    [Gambling], [`rotational_power`], [`-0.040`], [`0.795`], [`0.917`], [No],
    [Gambling], [`aci`], [`-0.040`], [`0.795`], [`0.917`], [No],
    [Gambling], [`mdr`], [`-0.058`], [`0.707`], [`0.917`], [No],
    [Cognitive control], [`frobenius_norm`], [`+0.020`], [`0.895`], [`0.917`], [No],
    [Cognitive control], [`rotation_norm`], [`+0.021`], [`0.890`], [`0.917`], [No],
    [Cognitive control], [`spectral_radius`], [`-0.058`], [`0.703`], [`0.917`], [No],
    [Cognitive control], [`rotational_power`], [`-0.016`], [`0.917`], [`0.917`], [No],
    [Cognitive control], [`aci`], [`-0.016`], [`0.917`], [`0.917`], [No],
    [Cognitive control], [`mdr`], [`+0.065`], [`0.674`], [`0.917`], [No],
    [Rest], [`frobenius_norm`], [`-0.157`], [`0.303`], [`0.681`], [No],
    [Rest], [`rotation_norm`], [`-0.226`], [`0.135`], [`0.410`], [No],
    [Rest], [`spectral_radius`], [`-0.062`], [`0.687`], [`0.917`], [No],
    [Rest], [`rotational_power`], [*`-0.324`*], [*`0.030`*], [`0.179`], [No†],
    [Rest], [`aci`], [*`-0.324`*], [*`0.030`*], [`0.179`], [No†],
    [Rest], [`mdr`], [*`+0.352`*], [*`0.018`*], [`0.179`], [No†],
  ),
  caption: [Respiratory-anchoring × MNJ coupling by task (Spearman $r$, session medians, $N = 44$–45, BH-FDR within the 18-row full family used in the text). †: the rest-condition `rotational_power`/`aci`/`mdr` associations are the largest in the table (uncorrected $p < 0.05$) and are directionally consistent with the CC `resp_anchor × m` result reported in the main text (R6), but do not survive family-wise FDR ($q approx 0.18$) and are reported as suggestive only. `resp_anchor_index × m` for cognitive control (the primary EAP-compatible finding, $r = -0.415$, $p = 0.0046$) is reported separately in S2.5 because it uses the MNPS rather than MNJ metric family. Source: `03_mnj_reachability/mnj_resp_coupling.csv`.]
) <tab-eap-mnj-full>

= S2.5 EAP physio-MNPS coupling (global and per-network)

The `02_eap_physio_coupling` pipeline additionally tested `resp_anchor_index`, `ecg_hrv_rmssd_ms`, and `cardioresp_rsa_amplitude` against all three global MNPS coordinates and the two block-Jacobian summaries, per task. The strongest cell in this larger family is the one highlighted in the main text:

#figure(
  kind: table,
  clean-table(
    columns: (1.6fr, 1.8fr, 1.6fr, 1fr, 1fr, 0.8fr),
    align: left,
    inset: 3.5pt,
    table.header(
      [*Task*], [*Physio.*], [*Geometry*], [*$r$*], [*$p$*], [*FDR $q$*]
    ),
    [Cognitive control], [`resp_anchor_index`], [`m_median`], [*`-0.415`*], [*`0.0046`*], [`0.206`],
    [Cognitive control], [`resp_anchor_index`], [`d_median`], [`+0.282`], [`0.061`], [`0.981`],
    [Gambling], [`resp_anchor_index`], [`e_median`], [`-0.211`], [`0.168`], [`0.981`],
    [Rest], [`cardioresp_rsa_amplitude`], [`d_median`], [`-0.185`], [`0.223`], [`0.981`],
    [Rest], [`resp_anchor_index`], [`c_rot_mean`], [`-0.181`], [`0.233`], [`0.981`],
  ),
  caption: [Top-5 physio-MNPS coupling cells by uncorrected $p$ out of 45 tested (3 physiological measures × 5 geometry summaries × 3 tasks, BH-FDR across all 45). Only the cognitive-control `resp_anchor_index × m` cell approaches significance (uncorrected $p = 0.0046$) but does not survive the full 45-cell correction ($q = 0.206$); a targeted partial-correlation follow-up controlling for HRV (main text R6) was used to test this cell specifically rather than relying on the omnibus-corrected result. Full 45-row table: `02_eap_physio_coupling/coupling_per_task.csv`, `coupling_global.csv`, `coupling_per_network.csv`.]
) <tab-eap-mnps-full>

= S2.6 Physiological and temporal-structure confound partial-correlation table (combined)

Combined output of Script 05 (HR, respiration rate, respiratory anchor index, EOG blink rate), Script 07 (tonic EDA), Script 10 (corrugator EMG), and Script 11 (Sync-pulse event rate), testing whether GG$-$CC differences in each candidate confound track the GG$-$CC difference in MNJ Frobenius norm.

#figure(
  kind: table,
  clean-table(
    columns: (2.4fr, 1fr, 1fr, 1fr, 0.8fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Confound (GG−CC difference)*], [*$r_s$*], [*$p$*], [*FDR $q$*], [*Sig.*]
    ),
    [Heart rate], [`-0.06`], [`0.71`], [`0.77`], [No],
    [Respiration rate], [`-0.29`], [`0.06`], [`0.20`], [No],
    [Respiratory anchor index], [`+0.33`], [`0.03`], [`0.20`], [No],
    [EOG blink rate], [`-0.20`], [`0.19`], [`0.44`], [No],
    [Tonic EDA (SCL)], [`-0.10`], [`0.51`], [`0.77`], [No],
    [Corrugator EMG (RMS)], [`-0.08`], [`0.60`], [`0.77`], [No],
    [Sync-pulse event rate], [`-0.05`], [`0.77`], [`0.77`], [No],
  ),
  caption: [Physiological/temporal-structure confound audit for the primary GG$>$CC Frobenius-norm effect ($N = 44$ intersection sample, Spearman correlation of GG−CC difference series, BH-FDR over 7 rows; `eog_artifact_fraction` excluded for zero variance). No candidate confound survives correction. Source: `05_mnj_confound_audit/mnj_physio_confound_partial.csv`, `07_eda_confound_control/full_confound_table.csv`, `10_corrugator_emg_confound/full_confound_table_with_emg.csv`, `11_event_density_sensitivity/full_confound_table_with_event_rate.csv`.]
) <tab-confound-full>

= S2.7 EDA descriptive summary by task

Session-level EDA extraction summary (Script 06), 129 of the 134 valid EEG sessions had usable EDA data (five sessions across three subjects failed the session-level EDA quality gate; see S1.3).

#figure(
  clean-table(
    columns: (1.4fr, 1.2fr, 1.4fr, 1.6fr),
    table.header([*Task*], [*Mean epochs/\ session*], [*Mean QC pass\ rate*], [*Median tonic\ SCL (µS)*]),
    [Rest], [126], [99.7%], [2.06],
    [Cognitive control], [262], [98.3%], [3.22],
    [Gambling], [910], [98.9%], [3.35],
  ),
  caption: [EDA extraction summary by task (55,903 epochs total, 129 sessions). Both active tasks (GG, CC) show significantly higher tonic SCL than Rest (GG vs. Rest: $d = 0.56$, $p = 0.0002$; CC vs. Rest: $d = 0.67$, $p < 0.0001$); GG and CC are statistically indistinguishable from each other ($d = -0.07$, $p = 0.55$). Source: `06_eda_extraction/eda_qc_summary.csv`, `eda_features.parquet`.]
) <tab-eda-summary>

#bibliography("references.bib")
