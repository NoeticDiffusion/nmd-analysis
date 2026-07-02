#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Neural flow geometry differentiates gambling and cognitive control despite matched sympathetic arousal",
  short-title: "MNJ task geometry in GG/CC/Rest",
  subtitle: "Local Jacobian structure reveals task-specific neural flow reorganization in a multimodal EEG–physiology dataset",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "neural flow geometry",
    "Meta-Noetic Jacobian",
    "MNJ",
    "neural manifold",
    "MNPS",
    "Noetic Diffusion Theory",
    "NeuralManifoldDynamics",
    "gambling",
    "cognitive control",
    "electrodermal activity",
    "Embodied Anchoring Principle",
    "EEG",
  ),
  article-type: "Research Article",
  abstract: [
    Task-related differences in neural dynamics are often sought in global state-space coordinates or spectral power. Here we ask whether the *local geometry of neural flow* — the Jacobian deformation of the manifold trajectory at each moment — distinguishes task contexts that leave global manifold coordinates largely unchanged. We analyzed `ds004511`, a multimodal EEG–ECG–respiration–EDA dataset, using the `N = 44` primary GG/CC intersection sample from a release containing 45 ingested subject directories (44 officially listed participants; see Methods), with healthy adults performing a gambling game (GG), a cognitive control task (CC), and eyes-closed rest. Using the NeuralManifoldDynamics pipeline, we extracted epoch-level Meta-Noetic Phase Space (MNPS) coordinates `(m, d, e)` and Meta-Noetic Jacobian (MNJ) metrics — Frobenius norm, spectral radius, rotation norm, rotational power, anisotropic compression index (ACI), and manifold deformation rate (MDR) — across 57,526 eight-second epochs. Global MNPS coordinates did not separate tasks (all Friedman $p > 0.23$). In contrast, MNJ metrics strongly differentiated task context, especially the gambling-vs-cognitive-control contrast, which was significant for all six non-trace MNJ metrics: gambling produced substantially higher Frobenius norm and spectral radius than cognitive control (Cohen's $d = 1.62$ and $d = 1.81$ respectively, both $p < 10^{-12}$ after FDR correction), while CC and rest showed relatively greater rotational power and ACI. The GG-vs-Rest and CC-vs-Rest contrasts showed more selective, metric-specific differences rather than a uniform separation (`trace` was non-significant for every task pair). The GG $>$ CC Frobenius effect survived intersection-sample restriction ($N = 44$, $d = 1.62$, $p = 8.0 times 10^{-13}$), epoch-count matching ($d = 1.44$), leave-one-subject-out testing (100% sign-consistent), bootstrap confidence intervals ($d$: 95% CI [1.31, 2.13]), and within-subject permutation (0/5000 permutations exceeded the observed statistic, reported as $p < 0.0002$). Critically, BioPac-derived tonic electrodermal activity (EDA) did not differ between gambling and cognitive control ($d = -0.07$, $p = 0.55$), ruling out peripheral sympathetic arousal as a confound for that specific contrast (EDA did differ from rest in both active tasks, so this arousal-independence claim is scoped to GG vs. CC and does not extend to the GG-vs-Rest or CC-vs-Rest comparisons). Two further confound checks corroborate this: a matched conventional-EEG baseline (band power, spectral/permutation entropy, Hjorth complexity) shows its largest GG-vs-CC effect (relative theta power, $d = 0.63$) at less than half the size of the MNJ Frobenius effect, and corrugator-EMG activity — a candidate facial-affect/muscle-artifact confound — neither differs between GG and CC ($d = 0.08$, $p = 0.51$) nor correlates with the GG−CC Frobenius difference ($r_s = -0.08$, $p = 0.60$). As a secondary exploratory analysis consistent with the Embodied Anchoring Principle (EAP), respiratory anchoring showed a partial correlation with manifold mobility during cognitive control after controlling for HRV ($r = -0.41$, $p = 0.006$, the numerically largest but FDR-non-significant association in the nine-test EAP family), and a sign-stable negative association with Frobenius norm during gambling ($r = -0.22$, LOOSO sign-consistent). These findings demonstrate that local neural flow geometry captures task-context reorganization beyond global manifold position, and — at least for the gambling-vs-cognitive-control comparison — beyond peripheral autonomic arousal; the same contrast is also larger in effect size than every tested conventional-EEG summary statistic (a baseline effect-size comparison, not a demonstration of incremental predictive validity in a joint model). A direct sensitivity check using raw Sync(1) trigger-pulse timing confirms that GG and CC differ in event/response-rate structure, but not in the assumed direction: session-level pulse rate is, if anything, higher in CC (median 0.45 Hz) than GG (median 0.36 Hz), the event-rate difference does not correlate with the Frobenius difference ($r_s = -0.05$, $p = 0.77$), and the effect is essentially unchanged when restricted to each subject's lowest-event-density epochs ($d = 1.70$ vs. $d = 1.62$ on the full sample). This narrows, without fully closing, the event/response-rate alternative (a small epoch-level coupling, $r_s approx 0.03$, remains); the present result should be read as a task-context MNJ difference rather than a process-pure gambling-specific mechanism.
  ],
  author-summary: [
    When people switch from rest to a gambling game or a cognitive control task, their brain's overall "position" in neural state space changes little — but the *way the neural state flows* changes dramatically. Using a geometric framework that tracks how the local trajectory of neural activity is stretched, rotated, or compressed moment to moment, we find that gambling produces much higher flow-field deformation than cognitive control (a large effect, GG vs. cognitive control specifically) — even though both active tasks show identical levels of peripheral physiological arousal (skin conductance). This dissociation shows that the neural flow geometry is sensitive to cognitive context beyond what arousal alone can explain. Secondary, exploratory analyses suggested a possible association between respiratory anchoring and lower manifold mobility during cognitive control, but this did not survive correction for multiple comparisons and requires replication before it can be treated as an established finding.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted at submission.],
  data-availability: [Analysis scripts, the epoch-level feature table, and result CSVs are publicly available in the `nmd-analysis` repository (`https://github.com/NoeticDiffusion/nmd-analysis`, `articles/Neural flow geometry differentiates gambling and cognitive control/`), including a Jupyter notebook (`notebook/reproduce_results.ipynb`) that reruns and displays every reported analysis from the code and committed data in that repository, with a closing table mapping each manuscript result to its reproducing notebook section. The underlying dataset `ds004511` ("Deception_data") is available via OpenNeuro (doi: 10.18112/openneuro.ds004511.v1.0.2; the ingested release contains 45 subject directories, one more than the 44 listed in the dataset's official participants table — see Methods §Dataset and Limitations). The NeuralManifoldDynamics processing framework is available via `https://github.com/NoeticDiffusion/NeuralManifoldDynamics`. Raw BioPac physiology (needed only to regenerate the standalone EDA features from scratch, §S1.3) is not redistributed in the repository but is available directly from OpenNeuro; the already-extracted `eda_features.parquet` is committed so that all downstream EDA analyses (§R5) remain independently reproducible without it.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")

= Introduction <sec:intro>

The neural basis of cognitive task performance is typically analyzed through spectral power, event-related potentials, or, more recently, through the trajectory of activity across a low-dimensional state-space manifold. @cunningham2014 @vyas2020 @churchland2012 These manifold-level analyses have proven powerful for motor and cognitive domains: population geometry, trajectory efficiency, and dimensionality each vary meaningfully across task conditions and behavioral outcomes. @gallego2017 @jazayeri2021 Yet most such analyses operate on *global* coordinates — where the system sits in state space — rather than on the *local geometry of flow* — how the neural trajectory is deformed, rotated, or expanded at each point in time.

Noetic Diffusion Theory (NDT) formalizes both layers. @langell2025ndt The Meta-Noetic Phase Space (MNPS) captures global state position through three coordinates $(m, d, e)$: manifold mobility, diffusivity, and entropy. Alongside MNPS, the *Meta-Noetic Jacobian* (MNJ) describes the local deformation structure of neural flow — the directional Jacobian of the manifold trajectory evaluated at each epoch. The MNJ provides a richer characterization of task-state geometry than coordinates alone: two tasks could occupy similar regions of MNPS while differing radically in how trajectories move through those regions.

This distinction matters in settings where cognitive contexts differ in *process* rather than in *state position*. A gambling/betting task and a cognitive control task may activate overlapping prefrontal–subcortical circuits @rangel2008 @miller2001 and produce similar baseline arousal, yet differ fundamentally in how neural dynamics unfold over time — one context involving high-variance, self-paced prediction and betting under a spontaneous-deception cover story (a well-studied paradigm class in its own right, distinct from instructed-lying designs @yin2016 @chen2024deception), the other involving tight inhibitory control over prepotent responses. @botvinick2001 If the MNJ is sensitive to this distinction, it would support a key architectural prediction of NDT: that local flow geometry tracks cognitive context beyond what global manifold position can resolve.

The present study tests this prediction using `ds004511`, @ds004511 a multimodal EEG–ECG–respiration–EDA dataset collected during three conditions: a solitary dice-prediction gambling game with a spontaneous-deception cover story (GG; participants privately observe a dice-roll outcome, bet on their own prediction, and self-report whether it was correct, with no computerized partner or live social interaction), a cognitive control task (CC) requiring response inhibition, and eyes-closed rest. The dataset offers an unusual opportunity: three task conditions with very different cognitive demands, combined with continuous multimodal physiology (ECG, respiration, electrodermal activity), allow us to simultaneously test whether MNJ separates tasks and whether peripheral arousal can account for any observed differences.

A secondary question concerns the *Embodied Anchoring Principle* (EAP) from NDT, @langell2025ndt which proposes that interoceptive signals — cardiac and respiratory rhythms — condition the neural variance schedule and thus modulate which regions of the manifold are traversed. Our prior work on a working-memory dataset found EAP-compatible comodulation at the condition level but modest direct anchor–MNPS coupling. @langell2025ndt Here we ask whether respiratory anchoring shows EAP-compatible associations with MNJ flow geometry in a context with strong task-structure contrast.

The central question is:

#netn-box(title: [Core question])[
  Does local neural flow geometry (MNJ) differentiate task contexts that do not strongly differ in global MNPS coordinates, and is any observed effect reducible to peripheral sympathetic arousal?
]

= Theory: NDT layers and the Meta-Noetic Jacobian <sec:theory>

== Meta-Noetic Phase Space and Jacobian

NDT models neural state dynamics as rhythmically guided denoising on a learned manifold, governed by:

$ d X_t = -nabla F(X_t, t) d t + sigma(t) d W_t $ <eq:mndm>

where $sigma(t) = sigma_"min" + sigma_0(1 - r(t))$ is the variance schedule regulated by neural rhythms. The MNPS coordinates $(m, d, e)$ locate the system on this manifold; high $m$ corresponds to a mobile, exploratory state; low $m$ to a constrained, converged state.

The Meta-Noetic Jacobian captures how small perturbations to the current state evolve under the flow:

$ J(t) = nabla_X [-nabla F(X_t, t)] $ <eq:mnj>

From $J$ we derive six epoch-level metrics:

- *Frobenius norm* ($||J||_F$): total flow-field deformation — how strongly the manifold stretches nearby trajectories in all directions.
- *Spectral radius* ($rho(J) = max_i |lambda_i (J)|$): the largest-magnitude eigenvalue of $J$ — the single most amplified local direction (not the largest singular value/operator norm; see S1.2 for the exact formula).
- *Rotation norm* ($||J - J^top||_F \/ 2$): antisymmetric component — rotational or cyclical structure in flow.
- *Rotational power*: fraction of total Frobenius explained by rotation; high values indicate organized cyclical dynamics.
- *ACI* (anisotropic compression index): the ratio of the antisymmetric (rotational) to symmetric (stretching/compression) component norms, $||J_"anti"||_F \/ (||J_"sym"||_F + epsilon)$; low ACI indicates deformation dominated by symmetric expansion/compression, high ACI indicates relatively more rotational structure (not a ratio of compressive-to-expansive singular values; see S1.2).
- *MDR* (manifold deformation rate): the fraction of total Frobenius magnitude attributable to the diagonal (axis-aligned) terms of $J$, $sum_i |J_(i i)| \/ (||J||_F + epsilon)$ — an axis-aligned deformation fraction, not a signed net-expansion-vs-contraction measure (see S1.2).

The distinction between high Frobenius (large deformation) and high rotational power (structured cyclical flow) is theoretically important: gambling may produce high absolute deformation with low rotational structure (expansive, unpredictable dynamics), while rest and cognitive control may show more structured cyclical flow, consistent with established resting-state oscillatory organization. @kluger2021

== The Embodied Anchoring Principle

EAP extends NDT's variance schedule by positing that interoceptive signals modulate $r(t)$:

$ r(t) mapsto r(t)[1 + gamma_"entrain" cos(phi_"cardiac" - phi_theta) cos(phi_"resp" - phi_alpha)] $

Higher respiratory anchoring (respiratory phase more regularly entrained to alpha-band oscillations) should tighten variance control, reduce manifold exploration, and reduce Frobenius norm. The present study tests a proxy version of this prediction using session-level respiratory anchor indices derived from respiration-MNPS coherence metrics.

= Methods <sec:methods>

== Dataset

`ds004511` @ds004511 ("Deception_data," OpenNeuro DOI version `v1.0.2`) is a publicly available EEG–physiology dataset collected at Nanyang Technological University. Its official participants table and README list `N = 44` healthy adults, but the ingested data release contains 45 subject directories; the 45th subject (`sub-S200203`) is present with valid cognitive-control and rest data but is not listed in the official demographics table, and has no gambling-game EEG acquisition at all (see below). We therefore report `N = 45` as the total number of subjects contributing data to at least one task, consistent with the ingested pipeline manifest, while noting the version-specific 44-vs-45 discrepancy explicitly here. Participants performed three conditions in a single session: (1) *gambling game* (GG) — officially the "Spontaneous Deception Task," in the tradition of gambling-based spontaneous-lying paradigms in the deception-neuroscience literature @yin2016: a solitary, self-paced task in which participants were given an initial stake and completed 144 rounds of privately predicting a dice-roll outcome, placing a bet (10-80 cents) on that prediction, and self-reporting to the system whether their prediction was correct; participants were told this cover story to create an unmonitored opportunity to misreport outcomes, but there is no computerized partner, no cooperate/defect choice, and no social-interaction component; (2) *cognitive control* (CC) — a four-part response-inhibition/conflict-resolution battery (processing-speed, response-selection, response-inhibition, and conflict-resolution sub-tasks, 460 trials total); and (3) *eyes-closed rest* (Rest). EEG was recorded using a 128-channel TruScan system. BioPac physiological sensors recorded ECG, respiration (RSP), two EMG channels placed over the corrugator supercilii muscle, and electrodermal activity (EDA) continuously at 4000 Hz.

== NMD pipeline

Continuous EEG was processed using the NeuralManifoldDynamics pipeline (run identifier `193708`, 2026-07-01), which also computed a conventional-EEG feature pack (band power, band ratios, alpha peak frequency, spectral/permutation entropy, Hjorth complexity) and injected the two BioPac corrugator-EMG channels (`EMGA`, `EMGB`) alongside the primary MNPS/MNJ geometry, in the same run. Independent component analysis (ICA) removed cardiac and ocular artifacts (1–2 components per session); ECG-derived heartbeat events were used for ICA identification (`ECG=["ECG"]`). EEG epochs of 8 seconds were extracted on a sliding basis. Per-epoch features include MNPS coordinates $(m, d, e)$, epoch-level ECG/HRV indices (RMSSD, pNN50), respiration metrics (rate, anchor index, RSA, cardiorespiratory PLV), EOG stability, conventional-EEG summary metrics, and corrugator-EMG RMS. Failed sessions: one GG session produced zero valid epochs and was excluded from GG analyses — `sub-S200203` (no GG EEG acquisition exists for this subject; documented in the dataset's own README as a recording-time technical error). Two further GG sessions (`sub-S200211`, `sub-S210317`) were initially unreadable because their EDF files were unresolved `git-annex` placeholders (105-byte stub files) rather than the actual recordings in an earlier local mirror of the dataset; both were re-fetched in full from the OpenNeuro S3 mirror, hash-verified against their `git-annex` keys, and successfully processed in run `193708`, so they contribute normally to all GG analyses reported here. `sub-S200203` contributed valid CC and Rest data and was not otherwise excluded.

== EDA extraction

The NMD pipeline injected EDA as a miscellaneous channel but did not compute EDA features. We therefore implemented a standalone extraction script (`06_eda_extraction.py`). For each session, the EDA column (column index 5, "EDA, Y, PPGED-R", 4000 Hz) was extracted from the BioPac `*_physio.tsv.gz` file by streaming line iteration. EDA was downsampled from 4000 Hz to 50 Hz using cascaded `scipy.signal.decimate` calls ($q = 8$, then $q = 10$, zero-phase). Full-session EDA decomposition into tonic and phasic components used `neurokit2.eda_process` @makowski2021neurokit2 (method: "neurokit"). Epoch-level features included tonic SCL (mean tonic level), tonic slope, phasic AUC, SCR rate, SCR amplitude, and SCR count. Sessions failing quality checks (tonic range $<$ 0.01 µS or mean outside 0–100 µS) were rejected.

== Primary endpoints and MNJ computation

Epoch-level MNJ metrics were extracted from per-session H5 files (`jacobian_subject_anchored/J_hat`, shape: epochs × 3 × 3). The six MNJ metrics (Frobenius norm, spectral radius, rotation norm, rotational power, ACI, MDR) were computed from the Jacobian tensor following the NDT specification. @langell2025ndt Primary endpoints for the task-contrast analysis were `frobenius_norm` and `spectral_radius` (absolute deformation); secondary endpoints were `rotation_norm`, `rotational_power`, `aci`, and `mdr` (structural/directional aspects of flow).

== Statistical design

Session-level medians of all epoch-level metrics were computed per subject per task. Cross-task contrasts used the Wilcoxon signed-rank test on matched subject pairs. @wilcoxon1945 Effect sizes are reported as Cohen's $d_z$: the mean of the paired within-subject differences divided by the standard deviation of those differences. @cohen1988 Multiple comparisons across the six MNJ metrics × three task pairs (18 tests for MNJ; 9 tests for MNPS, three coordinates × three task pairs) were controlled using Benjamini–Hochberg FDR at $alpha = 0.05$. @benjamini1995 All reported contrasts with "✓" survive FDR 5%.

*Robustness protocol* (following science lead audit, `sciencelead/001.md`; ten parts in total, following the same numbering used in S1.6 and R4):
(1) *Intersection sample*: all contrasts re-run on the $N = 44$ subjects with valid data for all three tasks.
(2) *Epoch-count matching*: per-subject random subsampling to the minimum epoch count across tasks ($approx 122$ epochs/subject).
(3) *LOOSO*: leave-one-subject-out test for the four primary MNJ metrics.
(4) *Bootstrap CIs*: 2000 resamples of subject-level medians.
(5) *Within-subject permutation*: 5000 shuffles of task labels within subjects.
(6) *Artifact balance*: epoch QC rates, EOG blink rate, and high-frequency power (30–45 Hz, EMG proxy) compared by task.
(7) *Physiological confounds*: Spearman correlations between GG–CC Frobenius difference and HR, respiration rate, respiratory anchor index, EOG blink rate, and tonic EDA differences (the EDA confound test was run as a dedicated follow-up script, `07_eda_confound_control.py`, once the standalone EDA extraction was complete).
(8) *Corrugator EMG*: the same confound-partial-correlation procedure applied to corrugator-EMG RMS (`10_corrugator_emg_confound.py`), run once the EMG channels had been added to the NMD ingest configuration.
(9) *Conventional-EEG baseline*: a matched comparison (`09_conventional_eeg_baseline.py`) of the GG-vs-CC MNJ Frobenius effect against 16 conventional band-power/complexity metrics computed on the same epochs and subjects, to assess whether the MNJ dissociation is recoverable from simpler raw-EEG summaries — a baseline effect-size comparison rather than a confound test in the strict sense.
(10) *Event/response-rate sensitivity*: raw BIDS `events.tsv` Sync(1) trigger-pulse timing joined to the epoch-level Jacobian windows (`11_event_density_sensitivity.py`), testing session-level event-rate contrasts by task, a confound-partial correlation of GG-CC event-rate difference against GG-CC Frobenius difference, within-task epoch-level event-density × Frobenius correlation, and a density-matched (below-median-density-epochs-only) re-test of the GG-vs-CC Frobenius contrast.

== Secondary EAP analysis

Session-level Spearman correlations between `resp_anchor_index` and MNPS/MNJ session medians were computed per task. Partial Spearman correlations controlling for HRV (RMSSD) were computed for the CC condition where the direct association was strongest. Bootstrap 95% CIs (2000 resamples) and LOOSO sign-consistency tests were run for the primary EAP trends.

= Results <sec:results>

== R1: Data quality and task coverage <sec:r1>

Of 135 possible sessions (45 subjects × 3 tasks), 134 produced valid epoch-level data (one GG session failed; see below), yielding 57,526 epochs. Task coverage by modality was uniformly excellent:

#figure(
  kind: table,
  clean-table(
    columns: (1.8fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center),
    inset: 5pt,
    table.header([*Modality*], [*GG*], [*CC*], [*Rest*]),
    [ECG / HRV (% epochs QC-OK)], [99.6%], [98.6%], [98.0%],
    [Cardiorespiratory RSA (% QC-OK)], [99.4%], [98.3%], [98.9%],
    [Respiration (% QC-OK)], [73.4%], [85.1%], [57.7%],
    [EDA tonic (% QC-OK)], [98.8%], [98.3%], [99.7%],
    [EOG blink rate (events/min)], [0.43], [0.43], [0.19],
  ),
  caption: [Physiological data quality by task. All modalities show high QC pass rates for GG and CC. Respiration QC is lower for Rest (57.7%), likely reflecting reduced breathing regularity during passive rest. EOG blink rate confirms that the Rest condition was performed with eyes closed.]
) <tab-qc>

Five EDA sessions across three subjects were rejected outright at the session-quality gate (flat/saturated signal): `sub-S201222` Rest; `sub-S200303` Rest; and `sub-S201210` (GG, CC, and Rest — all three tasks). One further subject (`sub-S200203`) had zero valid GG epochs and was excluded from GG analyses only (no GG EEG acquisition exists for this subject; see §NMD pipeline); this subject contributed valid CC and Rest data. Per-task subject counts were therefore 44 (GG), 45 (CC), and 45 (Rest); the intersection sample (all three tasks valid) comprised $N = 44$ subjects.

#figure(
  image("figures/fig6_qc_coverage.svg", width: 62%),
  caption: [Respiration and EDA epoch-level QC pass rates by task. Respiration QC is markedly lower during Rest (57.7%), consistent with less regular breathing during passive eyes-closed rest; EDA QC is uniformly high ($>$98%) across all three tasks.]
) <fig-qc>

== R2: Global MNPS coordinates are mostly null across tasks <sec:r2>

Session-level medians of global MNPS coordinates $(m, d, e)$ did not differentiate tasks:

- Friedman tests across GG, CC, Rest: $chi^2 < 3.0$, all $p > 0.23$
- 0 / 9 MNPS pairwise contrasts survived FDR 5%
- Absolute differences in $m$ across tasks: GG = 0.024, CC = 0.019, Rest = 0.018 (arbitrary units)

Network-stratified MNPS showed two FDR-surviving contrasts: central $m$ (GG vs CC: $d = 0.57$) and temporal $m$ (GG vs Rest: $d = 0.45$). These network-level effects are modest and do not constitute a global MNPS task separation.

#netn-box(title: [Key null])[
  Task type does not strongly reorganize global manifold position. The gambling, cognitive control, and rest conditions occupy largely overlapping regions of $(m, d, e)$ space at the session-average level.
]

This null is important as a background for the MNJ results: the contrast between global-coordinate insensitivity and flow-geometry sensitivity is the central finding of the paper.

#figure(
  image("figures/fig1_mnps_vs_mnj_dissociation.svg", width: 100%),
  caption: [Global MNPS mobility ($m$) shows no reliable task separation (left), while MNJ Frobenius norm shows a large, robust GG $>$ CC effect (right). Points are session medians; boxes show quartiles across $N = 44$–45 subjects.]
) <fig-mnps-mnj>

== R3: MNJ flow geometry differentiates task context, especially GG vs CC <sec:r3>

Epoch-level MNJ metrics yielded robust cross-task differentiation, most cleanly and uniformly for the GG-vs-CC contrast; GG-vs-Rest and CC-vs-Rest showed more selective, metric-specific patterns rather than a uniform separation (see @tab-mnj). @tab-mnj presents pairwise contrasts (Wilcoxon signed-rank, BH-FDR corrected at 5%):

#figure(
  kind: table,
  clean-table(
    columns: (1.8fr, 1.1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center, center, center, center),
    inset: 5pt,
    table.header(
      [*MNJ metric*],
      [*GG vs CC* $d$],
      [*p*],
      [*FDR*],
      [*GG vs Rest* $d$],
      [*p*],
      [*CC vs Rest* $d$],
    ),
    [`frobenius_norm`], [1.62], [$< 10^{-12}$], [✓], [0.74], [$< 10^{-4}$], [-0.23],
    [`spectral_radius`], [1.81], [$< 10^{-12}$], [✓], [1.98], [$< 10^{-11}$], [0.27],
    [`rotation_norm`], [1.01], [$< 10^{-7}$], [✓], [0.10], [0.30], [-0.40],
    [`rotational_power`], [-1.03], [$< 10^{-7}$], [✓], [-1.41], [$< 10^{-10}$], [-0.71],
    [`aci`], [-1.02], [$< 10^{-7}$], [✓], [-1.34], [$< 10^{-10}$], [-0.71],
    [`mdr`], [0.42], [$< 0.01$], [✓], [1.02], [$< 10^{-6}$], [0.70],
  ),
  caption: [Epoch-level MNJ cross-task pairwise contrasts (Wilcoxon signed-rank, BH-FDR corrected). Cohen's $d$ reported as paired $d_z$ (mean difference / SD of differences). ✓ = survives FDR 5%. All six metrics survive FDR for GG vs CC. The GG vs Rest contrast is driven primarily by spectral radius, rotational power, ACI, and MDR. CC vs Rest contrasts for rotational power and ACI reflect structured cyclical flow in both active conditions relative to gambling.]
) <tab-mnj>

The pattern reveals two complementary effects:

*Gambling produces high absolute flow deformation.* Frobenius norm ($d = 1.62$), spectral radius ($d = 1.81$), and MDR ($d = 1.02$ vs Rest) are all substantially elevated during GG. This indicates that the local neural flow field is highly deformed and expansive — trajectories are stretched and accelerated more strongly during the gambling context.

*Cognitive control and rest show relatively more structured rotational dynamics.* Rotational power ($d_{"GG vs CC"} = -1.03$; $d_{"GG vs Rest"} = -1.41$) and ACI ($d_{"GG vs CC"} = -1.02$) are substantially lower during gambling than during CC or rest, despite gambling having a higher total Frobenius norm. This indicates that the *composition* of flow deformation differs: gambling deformation is predominantly expansive and anisotropic, while CC and rest dynamics contain a relatively larger rotational component, consistent with organized oscillatory structure.

Block-level Jacobian estimates (from the `block_frobenius_mean` and `c_rot_mean` outputs of the NMD summarize step) replicated these patterns: Friedman $chi^2 = 47.77$, $p < 0.0001$ for Frobenius; $chi^2 = 34.41$, $p < 0.0001$ for rotational component. GG vs CC block Frobenius: $d = 1.70$, $p < 10^{-12}$.

#figure(
  image("figures/fig2_mnj_effect_sizes.svg", width: 72%),
  caption: [Cohen's $d$ for all six MNJ metrics across the three pairwise task contrasts. Asterisks mark contrasts surviving BH-FDR 5%. Gambling shows elevated absolute deformation (Frobenius, spectral radius) but reduced rotational structure (rotational power, ACI) relative to cognitive control and rest.]
) <fig-mnj-effects>

== R4: Robustness and confound audit <sec:r4>

The GG $>$ CC Frobenius effect was subjected to a ten-part robustness/confound/baseline audit: (1) intersection sample, (2) epoch-count matching, (3) leave-one-subject-out, (4) bootstrap, (5) within-subject permutation, (6) artifact balance, (7) physiological confounds including EDA, (8) corrugator EMG, (9) a conventional-EEG baseline comparison, and (10) event/response-rate sensitivity. The first six parts are reported in this section; parts 7–8 (confound partial correlations, including the dedicated EDA and EMG checks) are reported below and in §R5; part 9 is reported separately in §R5a because it addresses a different question (whether MNJ is recoverable from simpler EEG summaries) rather than a confound for the Frobenius effect itself; part 10 is reported in §R5b.

=== Intersection sample and epoch matching

Restricting to the $N = 44$ subjects with valid data across all three tasks, GG $>$ CC Frobenius remained $d = 1.62$, $p = 8.0 times 10^{-13}$ (6/7 MNJ metrics surviving FDR). Epoch-count matching (subsampling per subject to $approx 122$ epochs, the minimum count across tasks) yielded $d = 1.44$ — a modest $approx 11%$ reduction with no change in significance direction.

=== Leave-one-subject-out and bootstrap

LOOSO for the four primary MNJ metrics (Frobenius, spectral radius, rotation norm, rotational power) showed 100% sign consistency across all 44 LOO iterations, with 100% of iterations reaching $p < 0.05$. Bootstrap confidence intervals from 2000 resamples:

#figure(
  kind: table,
  clean-table(
    columns: (2fr, 1fr, 2fr),
    align: (left, center, center),
    inset: 5pt,
    table.header([*Metric (GG vs CC)*], [*d*], [*95% Bootstrap CI*]),
    [`frobenius_norm`], [1.62], [[1.31, 2.13]],
    [`spectral_radius`], [1.81], [[1.45, 2.44]],
    [`rotational_power`], [-1.03], [[-1.42, -0.74]],
  ),
  caption: [Bootstrap CIs for primary MNJ metrics (2000 resamples, $N = 44$). All CIs lie entirely on one side of zero.]
) <tab-bootstrap>

=== Within-subject permutation

Within-subject task-label permutation (5000 shuffles) yielded 0/5000 permuted medians as extreme as the observed one for all four primary metrics, reported as $p < 0.0002$ — the observed effect was never reproduced under the null distribution.

=== Artifact balance

EOG QC pass rates were identical across tasks (1.0 for all conditions). High-frequency EEG power (30–45 Hz, EMG proxy) was slightly *higher* in CC than GG ($d = -0.15$, $p = 0.005$) — the opposite direction of a confound for GG $>$ CC Frobenius. Rest showed markedly elevated high-frequency power (likely reflecting relaxed muscle tone and reduced signal amplitude generally). No artifact imbalance explains the observed MNJ pattern.

=== Physiological confound controls

Spearman correlations between the GG–CC difference in Frobenius and candidate confound differences (subject medians, $N = 44$ intersection sample) yielded:

#figure(
  kind: table,
  clean-table(
    columns: (2.7fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center),
    inset: 5pt,
    table.header([*Confound (GG−CC difference)*], [*$r_s$*], [*p*], [*FDR $q$*]),
    [Heart rate], [-0.06], [0.71], [0.77],
    [Respiration rate], [-0.29], [0.06], [0.20],
    [Respiratory anchor index], [+0.33], [0.03], [0.20],
    [EOG blink rate], [-0.20], [0.19], [0.44],
    [Tonic EDA (SCL)], [-0.10], [0.51], [0.77],
    [Corrugator EMG (RMS)], [-0.08], [0.60], [0.77],
    [Sync-pulse event rate], [-0.05], [0.77], [0.77],
  ),
  caption: [Physiological/temporal-structure confound associations with GG−CC Frobenius difference. None of the seven candidate confounds survives BH-FDR correction. The respiration-rate and respiratory-anchor associations ($p approx 0.03$–$0.06$ uncorrected) are the largest in magnitude but do not survive correction across the seven-confound family ($q approx 0.20$); they may reflect a task-engagement covariate rather than a disqualifying confound. Tonic EDA, corrugator EMG, and Sync(1) event rate — extracted independently in `07_eda_confound_control.py`, `10_corrugator_emg_confound.py`, and `11_event_density_sensitivity.py` — show no relationship to the Frobenius effect ($r_s = -0.10$, $p = 0.51$; $r_s = -0.08$, $p = 0.60$; and $r_s = -0.05$, $p = 0.77$ respectively), consistent with the direct EDA, EMG, and event-rate task-contrast checks reported in R5a/R5b and the Limitations section.]
) <tab-confounds>

#figure(
  image("figures/fig3_bootstrap_robustness.svg", width: 78%),
  caption: [Bootstrap 95% confidence intervals (blue bars, 2000 resamples) and leave-one-subject-out range (grey ticks) for the four primary MNJ metrics, GG vs CC, $N = 44$. All intervals exclude zero and are stable under subject removal.]
) <fig-bootstrap>

Across all ten audit parts described above, the GG $>$ CC Frobenius effect remained robust. The finding cannot be attributed to sample composition, epoch count, data artifacts, task-label chance, or any of the seven tested peripheral-physiological/temporal-structure confounds (parts 7–8, 10). Part 9 — direct comparison against a conventional-EEG baseline — is reported separately below (§R5a) because it addresses a different question (whether MNJ is recoverable from simpler EEG summaries) rather than a confound for the Frobenius effect itself; part 10 — event/response-rate sensitivity — is reported in §R5b.

== R5: EDA dissociation — neural flow geometry diverges from sympathetic arousal <sec:r5>

Epoch-level tonic SCL (skin conductance level), extracted from the BioPac EDA channel using `neurokit2` decomposition, was elevated during both active tasks relative to rest:

- GG vs Rest: $d = 0.56$, $p = 0.0002$
- CC vs Rest: $d = 0.67$, $p < 0.0001$

Crucially, GG and CC did not differ in tonic SCL: $d = -0.07$, $p = 0.55$ ($N = 43$ matched subjects). Median tonic SCL: GG = 3.35 µS, CC = 3.22 µS, Rest = 2.06 µS.

#netn-box(title: [Dissociation finding])[
  GG and CC produce equal sustained sympathetic arousal (EDA tonic SCL), while MNJ Frobenius norm differs very substantially ($d = 1.62$). The task effect on neural flow geometry is not reducible to peripheral arousal state.
]

#figure(
  image("figures/fig4_eda_dissociation.svg", width: 100%),
  caption: [Left: tonic EDA (SCL) by task; gambling and cognitive control are statistically indistinguishable while both exceed rest. Right: subject-level GG−CC differences in EDA and MNJ Frobenius norm are uncorrelated ($r_s = -0.10$, $p = 0.51$, $N = 43$), confirming that the Frobenius effect is not tracking individual differences in arousal change.]
) <fig-eda>

This dissociation has two implications. First, it rules out the simplest confound hypothesis — that gambling "looks different" because participants are generally more physiologically aroused. Second, it argues against a generic peripheral-arousal explanation and supports the interpretation that MNJ captures task-structure information not resolved by tonic EDA: the neural flow field differentiates self-paced, uncertainty-laden dice-prediction and betting from inhibitory control at a level that peripheral sympathetic activation does not resolve. This does not, on its own, establish that the effect is process-pure cognitive/computational rather than reflecting the two tasks' differing event/response-rate structure — an alternative that has since been directly tested and substantially narrowed, though not fully closed (§R5b, Limitations).

== R5a: Conventional-EEG baseline and corrugator-EMG confound checks <sec:r5a>

Two remaining alternative explanations for the GG $>$ CC Frobenius effect — that it is recoverable from simple raw-EEG summary statistics, or that it reflects corrugator-muscle EMG contamination or affective facial activity rather than neural flow geometry — were tested directly once the NMD ingestion config was extended to compute a conventional-EEG feature pack and inject the two BioPac corrugator-EMG channels in the same pipeline run as the primary MNPS/MNJ geometry (`09_conventional_eeg_baseline.py`, `10_corrugator_emg_confound.py`; same epochs and subjects as the primary analysis).

*Conventional-EEG baseline.* Sixteen conventional metrics (relative band power in five bands, four band-ratio indices, three spectral-edge/peak-frequency indices, and three complexity indices: spectral entropy, permutation entropy, Hjorth complexity) were contrasted GG vs. CC on the $N = 44$ intersection sample using the same paired-Wilcoxon protocol as the primary MNJ analysis. 31/48 contrasts (across all three task pairs) survived BH-FDR at 5%. For GG vs. CC specifically, the largest effect was relative theta power ($d = 0.63$, $p_{"FDR"} < 0.001$), followed by the theta/alpha and alpha/theta ratios ($|d| approx 0.31$–$0.38$) and Hjorth complexity ($d = 0.29$). Every conventional-EEG effect size was substantially smaller than the MNJ Frobenius effect ($d = 1.62$) or spectral-radius effect ($d = 1.81$) for the same contrast — the largest conventional metric reaches only $39%$ of the Frobenius effect size. This is a baseline effect-size comparison, not a test of incremental predictive validity (e.g., a joint classification or mixed-effects model showing MNJ explains variance beyond conventional EEG features was not performed). Within that scope, the result indicates that the MNJ dissociation is not simply recapitulating a broadband power or complexity difference between tasks of comparable magnitude; the Jacobian-based flow-geometry description shows a substantially larger effect than the tested conventional band-power/complexity summaries, though it does not rule out that some fraction of the Frobenius effect is shared with the theta-band difference, nor does it establish that MNJ provides independent information once conventional features are accounted for in a joint model.

*Corrugator EMG.* Tonic corrugator-EMG RMS (from the two BioPac `EMGA`/`EMGB` channels placed over the corrugator supercilii) did not differ between GG and CC ($d = 0.08$, $p = 0.51$, $N = 44$) — mirroring the EDA null above — while both active tasks showed higher EMG than rest (GG vs Rest: $d = 0.54$, $p < 0.001$; CC vs Rest: $d = 0.57$, $p < 0.0001$), plausibly reflecting general postural/facial muscle tone during eyes-open active tasks versus eyes-closed rest. Critically, the subject-level GG−CC difference in corrugator EMG was uncorrelated with the GG−CC difference in MNJ Frobenius norm ($r_s = -0.08$, $p = 0.60$, $N = 44$; row added to @tab-confounds above). This closes the corrugator-EMG question raised as an open confound in an earlier draft of this manuscript: corrugator EMG is matched between GG and CC (like EDA) and does not track the Frobenius effect.

#netn-box(title: [Two further confounds addressed])[
  Neither a 16-feature conventional-EEG baseline nor corrugator-EMG activity accounts for the GG $>$ CC MNJ Frobenius effect: the largest conventional-EEG effect size is less than half of the Frobenius effect, and corrugator EMG is matched between tasks and uncorrelated with the Frobenius difference.
]

== R5b: Event/response-rate sensitivity analysis <sec:r5b>

GG (144 self-paced dice-betting rounds across a long session) and CC (~460 trials in a much shorter four-part battery) differ enormously in task structure, raising a further candidate non-geometric explanation for the Frobenius effect (see Limitations): if Jacobian-based deformation is partly driven by the sheer density of discrete task events (stimulus onsets, button presses, feedback) rather than task content, GG's much larger effect size could in principle be a temporal-structure artifact rather than a geometric one. We tested this directly using the raw BIDS `events.tsv` Sync(1) trigger-pulse timestamps — dataset-native trigger pulses that are independent of the NMD ingest pipeline and require no re-ingest (`11_event_density_sensitivity.py`).

*Session-level event rate.* Contrary to a naive "GG is a slow, low-event-rate task" assumption, the per-second Sync(1) pulse rate was, if anything, *higher* in CC (median 0.453 Hz) than in GG (median 0.357 Hz; $d_z = -4.0$, $p < 0.0001$, $N = 44$). GG has far more *total* pulses per session (~1,285 vs. ~470 for CC, reflecting multiple sync markers per gambling round across 144 rounds), but its session is proportionally much longer (median session duration ≈ 60 min vs. ≈ 17 min for CC), so the per-second rate is actually lower. This reversal is itself informative: a purely event-density account of GG $>$ CC Frobenius would predict the opposite direction of effect from what is observed.

*Subject-level confound test.* The subject-level GG$-$CC difference in event rate did not correlate with the GG$-$CC difference in Frobenius norm ($r_s = -0.05$, $p = 0.77$, $N = 44$; row added to @tab-confounds above).

*Epoch-level covariate.* Within each task, epochs with more local Sync(1) pulses (counted in the same 8 s window as the Jacobian estimate) showed a small but statistically significant *increase* in Frobenius norm (gambling: $r_s = 0.03$, $p = 2 times 10^{-9}$, $n = 39{,}985$ epochs; cognitive control: $r_s = 0.03$, $p = 6.8 times 10^{-4}$, $n = 11{,}363$ epochs) — a real but practically negligible local coupling ($r^2 approx 0.001$), and one that goes in the same direction in both tasks rather than being GG-specific.

*Density-matched sensitivity.* Restricting the GG-vs-CC Frobenius contrast to each subject's below-median local-event-density epochs in *both* tasks (median 644 GG epochs and 162 CC epochs retained per subject) left the effect essentially unchanged: $d = 1.70$, $p < 0.0001$, compared with $d = 1.62$ on the full sample.

#netn-box(title: [Event/response-rate confound narrowed])[
  Sync(1) pulse rate is higher in CC than GG per second (opposite to a naive event-density account of the effect), subject-level event-rate differences do not track the Frobenius difference, and the GG $>$ CC Frobenius effect is undiminished when restricted to low-event-density epochs in both tasks. The event/response-rate confound is substantially narrowed by this direct test, though a small epoch-level coupling ($r approx 0.03$) and the dataset's lack of stimulus-vs-response pulse labeling mean it is narrowed rather than fully closed (see Limitations).
]

== R6: Secondary EAP-compatible physiology coupling <sec:r6>

The pre-specified EAP partial-correlation family comprises nine tests: `resp_anchor_index` vs. each of three flow-geometry summaries (block-level Frobenius mean, block-level rotational component `c_rot_mean`, and MNPS mobility `m`), controlling for HRV (RMSSD), separately within each of the three tasks (GG, CC, Rest). None of the nine survives BH-FDR at 5% ($N approx 44$–45, underpowered for effects $r approx 0.25$); the full $3 times 3$ table is:

#figure(
  kind: table,
  clean-table(
    columns: (1.3fr, 1.6fr, 1fr, 1fr, 1fr),
    align: (left, left, center, center, center),
    inset: 4pt,
    table.header([*Task*], [*Geometry (resp\_anchor $|$ HRV)*], [*$r$*], [*$p$*], [*FDR $q$*]),
    [Cognitive control], [`m` (mobility)], [-0.41], [0.006], [0.05],
    [Gambling], [rotational component], [-0.19], [0.21], [0.42],
    [Gambling], [block Frobenius], [-0.19], [0.23], [0.42],
    [Rest], [rotational component], [-0.18], [0.25], [0.42],
    [Rest], [block Frobenius], [-0.18], [0.26], [0.42],
    [Cognitive control], [rotational component], [-0.17], [0.28], [0.42],
    [Cognitive control], [block Frobenius], [-0.15], [0.33], [0.42],
    [Gambling], [`m` (mobility)], [-0.12], [0.45], [0.51],
    [Rest], [`m` (mobility)], [$<$0.01], [0.99], [0.99],
  ),
  caption: [The complete pre-specified nine-test EAP partial-correlation family (`resp_anchor_index` vs. flow-geometry metric, controlling for HRV, per task), sorted by uncorrected $p$. None survives BH-FDR at 5%; the cognitive-control/mobility test is the numerically largest but is FDR-non-significant ($q approx 0.05$, just above the $alpha = 0.05$ threshold). Source: `02_eap_physio_coupling/coupling_partial.csv`.]
) <tab-eap-family>

*Cognitive control:* Partial Spearman between `resp_anchor_index` and session-median `m` (manifold mobility), controlling for HRV (RMSSD): $r = -0.41$, $p = 0.006$. The HRV partial does not explain the respiratory effect (HRV | resp: $r = 0.010$, $p = 0.95$). This is the numerically largest association in the nine-test family above but does not survive BH-FDR ($q approx 0.051$, failing the pre-declared $alpha = 0.05$ correction threshold by a narrow margin) and should be reported as FDR-non-significant rather than as a confirmed finding. Interpretation, offered cautiously: during cognitive control, stronger respiratory anchoring is associated with lower manifold mobility — the system is more constrained.

*Gambling:* Session-level Spearman `resp_anchor × frobenius` (epoch-level MNJ Jacobian, the version used for the headline LOOSO check): $r = -0.22$, $p = 0.16$ ($n = 44$). LOOSO sign-consistency: the negative association was maintained in all 44 LOO iterations (range: $-0.27$ to $-0.17$). The block-level Jacobian version of this same correlation is directionally consistent but smaller in magnitude ($r = -0.14$, $p = 0.35$; LOOSO range $-0.20$ to $-0.09$; bootstrap 95% CI $[-0.43, 0.16]$, spanning zero) — the two operationalizations no longer agree as closely as in an earlier draft of this analysis, underscoring that this remains an underpowered, non-significant trend under either version of the metric.

*Rest:* Exploratory, non-pre-specified Spearman correlations (not part of the nine-test family above, reported descriptively and uncorrected): `resp_anchor × rotational_power`: $r = -0.32$, $p = 0.03$; `resp_anchor × mdr`: $r = +0.35$, $p = 0.02$.

#figure(
  image("figures/fig5_eap_resp_coupling.svg", width: 100%),
  caption: [Secondary, exploratory EAP-compatible respiratory-anchoring associations. Left: cognitive control, respiratory anchor index vs. MNPS mobility $m$ (partial $r = -0.41$ controlling for HRV). Right: gambling, respiratory anchor index vs. MNJ Frobenius norm ($r = -0.22$, sign-consistent in 44/44 LOOSO iterations). Neither survives BH-FDR across the full test family; both are reported as directionally consistent, underpowered secondary findings.]
) <fig-eap>

These findings are consistent with the EAP prediction that respiratory anchoring moderates neural flow geometry, but the present sample ($N approx 44$) is underpowered to demonstrate this robustly after correction. The CC partial-Spearman result is the numerically largest but FDR-non-significant EAP-compatible association observed in this dataset, and should be read as a directionally suggestive, hypothesis-generating result rather than a confirmed finding.

= Discussion <sec:discussion>

== MNJ reveals task geometry invisible to global MNPS coordinates

The central finding is a dissociation between global manifold position and local flow geometry. While MNPS coordinates $(m, d, e)$ showed no reliable cross-task separation (Friedman $p > 0.23$ for all), epoch-level MNJ metrics yielded some of the largest between-task effects sizes we have observed across NDT analyses: GG $>$ CC Frobenius at $d = 1.62$, GG $>$ Rest spectral radius at $d = 1.98$. This dissociation is not a calibration artifact: the epoch-count matching, LOOSO, bootstrap, and permutation tests collectively confirm that it reflects a genuine, large, and reproducible difference in neural flow geometry, and it is not recoverable from a matched conventional-EEG baseline (§R5a).

The pattern of which MNJ metrics drive the separation is informative. High Frobenius in gambling with *low* rotational power indicates that the deformation is expansive/contracting rather than structured-rotational. In contrast, cognitive control and rest both show relatively higher rotational power — consistent with organized neural oscillations contributing a more cyclical, structured trajectory structure. This maps onto a theoretically sensible picture: resting-state dynamics are known to be organized by slow oscillations, spindles, and alpha rhythms that generate cyclical flow structure @kluger2021; cognitive control activates prefrontal control networks that may similarly impose structured rotational trajectory organization @churchland2012; gambling disrupts this with high-variance, uncertainty- and decision-dependent neural dynamics that generate strongly deformed, expansive flow fields. @rangel2008 @knutson2001 We deliberately avoid the term "outcome-dependent" here: as noted in Limitations, `ds004511`'s BIDS `events.tsv` files do not encode trial-level win/loss outcomes, so this account should be read as a plausible process-level interpretation rather than a claim tied to specific trial outcomes.

== The EDA dissociation strengthens the neural interpretation

The finding that tonic EDA does not differ between gambling and cognitive control ($d = -0.07$, $p = 0.55$) while MNJ Frobenius differs very substantially ($d = 1.62$) is scientifically important beyond ruling out a confound. EDA tonic SCL is a well-validated index of sympathetic nervous system activation and general arousal. @boucsein2012 @dawson2017 Its equality across GG and CC means that participants were equally "aroused" in both conditions in peripheral terms — yet the neural flow field was organized radically differently. This argues against a generic peripheral-arousal explanation and supports the interpretation that MNJ captures task-structure information not resolved by tonic EDA, rather than establishing that the effect is purely cognitive/computational in origin (event/response-rate structure is a separate alternative that has been directly tested and substantially narrowed, though not fully closed; see §R5b and Limitations).

This dissociation is consistent with a growing body of work suggesting that brain state reorganization during complex tasks involves cognitive-specific neural configurations rather than global arousal modulation. @critchley2004 @seth2012 Within the NDT framework, it supports the prediction that MNJ captures *task-specific* landscape deformation rather than a general activation gradient. The MNJ is sensitive to the *way* neural dynamics are organized, not merely to whether the system is more or less active.

== EAP-compatible physiology — secondary and exploratory

The respiratory anchoring results are consistent with EAP but do not confirm it. The CC partial Spearman result ($r = -0.41$, $p = 0.006$) is the numerically largest association among the nine pre-specified EAP partial-correlation tests, but it does not survive BH-FDR correction across that family ($q approx 0.05$) and should be described as FDR-non-significant rather than as a confirmed finding: stronger respiratory anchoring during cognitive control is associated with lower manifold mobility independently of HRV. This aligns with EAP's prediction that respiratory entrainment moderates neural variance. @langell2025ndt @azzalini2019 @kluger2021 The gambling trend ($r = -0.22$, LOOSO sign-consistent) points in the same direction but is underpowered at $N = 44$.

These findings should be interpreted cautiously. The session-level $N$ is borderline for detecting effects of $|r| approx 0.25$ at $alpha = 0.05$. Epoch-level coupling is highly heterogeneous across subjects. The partial-Spearman result does not survive BH-FDR across the full test family. Replication in a larger or independent dataset is required before EAP-compatible coupling can be considered an established result.

== Limitations

Several important limitations bound the current findings. First, the `ds004511` behavioral records do not include trial-type labels in the BIDS `events.tsv` files: only synchronization pulses are recorded. We therefore cannot identify individual gambling trial outcomes (win/loss) or the moments at which a participant chose to misreport a prediction within the GG task. All GG effects are block-level rather than trial-level contrasts; outcome-specific claims are not supported by the current analysis. This limitation is sharpened once the GG task is correctly understood as a *spontaneous-deception* paradigm rather than a generic gambling task (see §Dataset): because we cannot identify which rounds involved a misreported prediction, we cannot determine what fraction, if any, of the large MNJ Frobenius/spectral-radius effect reflects deception-related neural processes specifically (as opposed to dice-prediction, betting, or self-report processes more generally that do not involve deception). This is an open question that the present block-level analysis cannot resolve.

Second, and most important for interpreting the primary effect: *event/response-rate structure was raised as the main non-geometric alternative explanation in earlier drafts of this manuscript and has now been directly tested (§R5b), narrowing but not fully closing the concern.* GG (144 self-paced dice-betting rounds across a long session) and CC (~460 trials in a much shorter four-part battery) differ enormously in task structure, so task-related evoked-activity density is a mundane, non-geometric explanation for elevated raw EEG variability during GG worth ruling out directly. Using the raw BIDS `events.tsv` Sync(1) trigger-pulse timestamps (independent of the NMD pipeline), we found: (1) the per-second pulse rate is, if anything, *higher* in CC (median 0.45 Hz) than in GG (median 0.36 Hz) — the opposite of the naive "GG is event-dense" framing, because GG's much larger total pulse count is spread over a proportionally much longer session; (2) the subject-level GG$-$CC difference in event rate does not correlate with the GG$-$CC difference in Frobenius norm ($r_s = -0.05$, $p = 0.77$); and (3) restricting the GG-vs-CC contrast to each subject's below-median-event-density epochs in both tasks leaves the effect essentially unchanged ($d = 1.70$ vs. $d = 1.62$ on the full sample). Together with the conventional-EEG baseline (§R5a, which shows that simple band-power/complexity summaries do not reproduce an effect of comparable size) and the corrugator-EMG and EDA checks (which rule out two specific peripheral/muscular explanations), this substantially narrows the event/response-rate account. It does not fully close it: a small but statistically significant epoch-level coupling between local event density and Frobenius norm remains within both tasks ($r_s approx 0.03$, likely of negligible practical size given $r^2 approx 0.001$ but not zero), the dataset's Sync(1) pulses do not distinguish stimulus-onset from response-execution events, and no trial-type labels are available to test event *type* (only event *timing*) as a covariate. Consequently, the current study should be read as establishing a robust *task-context* MNJ difference between GG and CC that survives a direct, quantitative event/response-rate sensitivity check, not a process-pure claim that isolates gambling-specific (still less deception-specific) neural mechanisms from all possible temporal-structure differences between the two tasks.

Third, $N = 44$–45 is a moderate sample for the EAP secondary analysis. The resp-anchor associations, while directionally consistent, are underpowered. A second dataset or a within-subject longitudinal design would substantially strengthen the EAP conclusion.

Fourth, EDA features were extracted using a standalone script rather than the NMD pipeline (which does not yet include an EDA extractor module). The extraction quality was high (98–99.7% epoch QC across tasks), but pipeline integration would improve reproducibility.

Fifth, the TruScan EEG system used in this dataset does not include digitization of electrode positions, preventing current-source density (CSD) analysis. The MNJ estimates are based on surface-potential trajectories.

Sixth, GG and CC differ enormously in task structure (144 self-paced dice-betting rounds vs. a four-part, ~460-trial RT/inhibition/conflict battery), so a skeptical reading is that at least part of the large Frobenius/spectral-radius effect could be recoverable from a much simpler raw-power or complexity contrast, without needing Jacobian-based flow geometry at all. This is directly tested in §R5a: a 16-feature conventional-EEG baseline (band power, band ratios, spectral-edge/peak-frequency indices, and complexity measures) shows its largest GG-vs-CC effect (relative theta power, $d = 0.63$) at well under half the size of the MNJ Frobenius effect ($d = 1.62$). This is a baseline effect-size comparison, not a demonstration of incremental predictive validity, and it substantially narrows but does not entirely close the concern: it remains possible that some fraction of the Frobenius effect is shared with the theta-band difference, and the 16 tested features do not exhaust the space of possible conventional-EEG or raw-signal summaries (e.g., full spectral connectivity, higher-order statistics, or a joint model combining conventional and MNJ features were not tested).

Seventh, the corrugator-EMG channel raised as an untested alternative/contributing explanation for the GG vs. CC effect in an earlier draft of this manuscript has now been directly tested and addressed. The BioPac hardware recorded two EMG channels over the corrugator supercilii muscle, a standard, well-validated facial-affect/frowning channel that tracks negative-valence responses even when not visibly expressed @larsen2003. Tonic corrugator-EMG RMS, extracted and analyzed in §R5a, does not differ between GG and CC ($d = 0.08$, $p = 0.51$) and is uncorrelated with the GG−CC Frobenius difference ($r_s = -0.08$, $p = 0.60$), closing this confound question for the GG-vs-CC contrast specifically.

Eighth, the dataset's own OpenNeuro documentation reports `N = 44` healthy individuals, while the ingested data release used here (DOI version `v1.0.2`) contains a 45th subject directory (`sub-S200203`) not listed in the official participants table; we report figures based on the ingested `N = 45` release throughout and flag this version-specific discrepancy explicitly rather than silently reconciling it.

== Conclusion

Local neural flow geometry, quantified by MNJ metrics derived from the Noetic Diffusion Theory framework, differentiates a gambling task from cognitive control — and, with more selective, metric-specific patterns, from rest — even when global MNPS coordinates show no task separation. The GG-vs-CC effect is large ($d = 1.62$ for Frobenius norm), survives all major robustness checks, and is dissociated from peripheral sympathetic arousal for that specific contrast (EDA tonic SCL GG = CC; tonic EDA does differ from rest in both active tasks, so this dissociation is not established for the GG-vs-Rest or CC-vs-Rest contrasts). These findings support a key architectural prediction of NDT: the MNJ layer captures task-context information that global manifold coordinates do not, and, for gambling vs. cognitive control, does so in a way that is not reducible to the tested peripheral-arousal, corrugator-EMG, artifact, or conventional-EEG-power confounds. The event/response-rate confound raised as an open question in earlier drafts has now been directly tested (§R5b): CC actually shows a higher per-second Sync-pulse rate than GG, event-rate differences do not track the Frobenius difference, and the effect survives restriction to low-event-density epochs — narrowing, though not fully closing, this alternative, together with residual overlap with theta-band power; the current study should therefore be read as establishing a robust *task-context* MNJ difference between gambling and cognitive control, not a process-pure claim that isolates a gambling- or deception-specific neural mechanism from every possible temporal-structure difference between the two tasks. Secondary EAP-compatible associations between respiratory anchoring and flow geometry are present but remain exploratory and FDR-non-significant. Together, these results support the MNJ as a sensitive index of task-context geometry — with matched sympathetic arousal specifically for the gambling-vs-cognitive-control contrast — and position it as a useful complement to global manifold coordinates and conventional EEG summaries in NDT-based neural state analysis.

= Acknowledgements

The `ds004511` dataset was made publicly available on OpenNeuro by Makowski, Pham, and Lau. Analysis used the NeuralManifoldDynamics pipeline and the NeuroKit2 physiological signal processing toolbox. @makowski2021neurokit2

#bibliography("references.bib", style: "apa")
