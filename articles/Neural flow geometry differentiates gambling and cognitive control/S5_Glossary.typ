#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S5 — Glossary",
  short-title: "Glossary",
  subtitle: "NDT · MNDM · Embodied Anchoring — shared terminology across articles",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("glossary", "NDT", "MNDM", "MNPS", "embodied anchoring"),
  article-type: "Supplementary Material",
  abstract: [
    This document defines the core terminology used across Noetic Diffusion Theory (NDT) articles. Entries cover the theoretical framework (NDT, EAP), the computational pipeline (MNDM, MNPS, MNJ), embodied anchor metrics (HRV-derived indices, pupillometry, PPG, EDA), the full family of MNJ scalar summaries (Frobenius norm, spectral radius, rotation norm, rotational power, ACI, MDR, trace), trajectory geometry, robustness-audit methods (LOOSO, bootstrap, permutation testing, epoch-count matching), and statistical methods. Definitions reflect the current implementation as of MNDM 2.4 and the `ds004511` gambling-vs-cognitive-control confound-audit protocol.
  ],
)

#set heading(numbering: none)

_Note: This is a living document. Definitions are updated to match the current MNDM pipeline version. Version-specific changes to metric computation are noted in the relevant entry._

_*Reading guide for reviewers.* Where relevant, entries distinguish three layers: (1) *Implemented* — the exact computation in the MNDM pipeline; (2) *Interpretation* — the most defensible empirical reading; (3) *Speculative / Not established* — theoretical mappings not yet directly confirmed. This three-layer structure is especially important for anchor surface metrics and trajectory geometry, which are operational constructs in an early validation stage._

= A – D

*ACI — Anisotropic Compression Index (`aci`)* — An MNJ scalar summary quantifying how directionally lopsided the local Jacobian's deformation is: $text("aci") = ||J_"anti"||_F / (||J_"sym"||_F + epsilon)$, the ratio of the antisymmetric (rotational) to symmetric (stretching/compression) component norms. Introduced in the `ds004511` gambling-vs-cognitive-control article as a secondary/structural MNJ endpoint, alongside `rotational_power`. Lower ACI indicates deformation dominated by expansion/compression (as observed during gambling); higher ACI indicates more balanced rotational structure (as observed during cognitive control and rest). See also: _Meta-Noetic Jacobian_, _Rotational Power_.

*Affective Mobility ($m_e$)* — A sub-coordinate of the Metastability axis ($m$) within the 9D stratified MNPS. Captures how readily the neural state transitions in the dimension linked to limbic and affective processing. High $m_e$ indicates fluid emotional state dynamics; low $m_e$ indicates affective rigidity or entrainment. See also: _Stratified MNPS_, _Metastability_.

*Anchor Quality (`anchor_quality`)* — A per-window indicator of how many anchor modalities contributed to the current `anchor_index` estimate. Windows using all four components (HRV + PPG + pupil + blink) receive the highest quality; windows relying on a single fallback modality receive lower scores. In primary analyses, windows with `anchor_quality > 0.5` are included. Sensitivity analyses using `anchor_quality > 0` are reported separately.

*Anchor State (`anchor_state`, `anchor_state_dot`)* — The scalar time-series output of the AnchorState pipeline representing the overall embodied anchoring level at each block-native epoch. `anchor_state_dot` is the first temporal derivative — the rate of change of anchoring. Both are exported by MNDM 2.3+. Distinct from `anchor_index`, which is the within-subject z-scored composite of named indices.

*AnchorState v0.1* — The first production version of the embodied anchor surface, exported by MNDM 2.3+. Comprises four named composite indices (`vagal_index`, `sympathetic_index`, `vascular_index`, `pupil_arousal_index`) and the overall `anchor_index`. All indices are computed from robust-z (median/MAD) standardized component features within each subject's run. No softmax; weights are fixed and equal within each index. See also: _anchor\_index_.

*`anchor_index`* — The top-level composite embodied anchor signal.

- *Implemented:* $text("anchor_index")(t) = text("nanmean")(text("sympathetic_index"), text("vagal_index"), text("vascular_index"), text("pupil_arousal_index"))$. Missing modalities dropped and mean renormalized. Equal fixed weights; robust-z scaled; no softmax; not trained.
- *Interpretation:* a convenience composite of available autonomic and arousal proxies. Useful for exploratory analyses; less interpretable than individual components.
- *Not established:* a validated biomarker, a direct measure of EAP "anchor strength," or a clinically meaningful index. Absolute values depend on R-peak detection accuracy (ECG component) pending validation.

*Attentional Mobility ($m_a$)* — A sub-coordinate of the Metastability axis ($m$) within the 9D stratified MNPS. Reflects the capacity for deliberate attentional switching, linked to top-down control networks (frontal, parietal). High $m_a$ is associated with flexible task engagement; low $m_a$ may reflect attentional capture or rigidity. See also: _Stratified MNPS_.

*Attractor* — A stable region in the neural state manifold to which trajectories tend to return after small perturbations. Geometrically, a local minimum in the potential landscape $F$. Examples of attractor-like states: focused task engagement, eyes-closed rest, consolidated sleep stage. Attractors are inferred from MNPS occupancy and reachability geometry, not defined a priori.

*Bootstrap Confidence Interval* — A resampling-based robustness check: subject-level paired differences are resampled with replacement (typically 2000–5000 resamples depending on the release), and the statistic of interest (e.g., Cohen's $d$) is recomputed on each resample to build an empirical distribution. The 2.5th and 97.5th percentiles form the 95% CI. In the `ds004511` gambling-vs-cognitive-control article specifically, 2000 resamples were used (`N_BOOT = 2000` in `05_mnj_confound_audit.py`), distinct from the separate 5000-iteration permutation test — used in the confound-audit protocol as one of several checks that a primary MNJ effect is not an artifact of sampling variability; a CI that excludes zero indicates the effect is unlikely to be a chance sampling result. See also: _LOOSO_, _Permutation Test (Within-Subject Sign-Flip)_.

*BH-FDR (Benjamini–Hochberg False Discovery Rate)* — The multiple-comparison correction used throughout NDT articles. Controls the expected proportion of false discoveries among rejected hypotheses. Used in preference to Bonferroni correction (which is overly conservative for correlated within-subject comparisons). Threshold: $q < 0.05$ for primary analyses.

*Block-Native Epoch* — The fundamental output unit of the MNDM pipeline. One row in `block_native_windows.parquet` corresponding to an analysis window within a task block; the default MNDM window is 4 seconds (2-second step/overlap), but the window length is a release-specific configuration parameter, not a fixed constant. HRV metrics are computed over a 60-second superwindow centered on each epoch's midpoint; MNPS coordinates are computed over the epoch's own neural data at whichever window length that release specifies. In the `ds004511` gambling-vs-cognitive-control article, epochs are 8 seconds long on a sliding basis (see S1.1), not the 4-second default described above. See also: _HRV Sliding-Superwindow Architecture_.

*`block_native_windows.parquet`* — The primary output file of an MNDM run. Contains one row per block-native epoch, including MNPS coordinates ($m$, $d$, $e$), MNJ outputs, anchor surface metrics, HRV metrics, quality flags, and task metadata.

*CC — Cognitive Control (task label)* — One of three within-subject conditions in `ds004511`. A four-part response-inhibition/conflict-resolution battery (processing-speed, response-selection, response-inhibition, and conflict-resolution sub-tasks, 460 trials total) requiring participants to override an automatic or prepotent response tendency in favor of a rule-governed one. Contrasted against gambling (GG) and eyes-closed rest. See also: _GG — Gambling Game (task label)_.

*Cohen's d* — Effect size metric used throughout. $d = Delta mu / "SD"_"pooled"$ for between-group comparisons; for paired within-subject tests, $d = "mean difference" / "SD of differences"$. Benchmarks (conventional): small $approx 0.2$, medium $approx 0.5$, large $approx 0.8$.

*`coupl_*` columns* — Twelve directed inter-regional Jacobian coupling channels exported by MNDM 2.4. Each channel (e.g., `coupl_frontal_to_parietal`) represents the strength of directed dynamical influence from one EEG network region to another, derived from the stage-level block Jacobian. A value near zero indicates independence; higher values indicate that perturbations in the source region deform the trajectory of the target region. See also: _Meta-Noetic Jacobian_.

*d (Diffusivity)* — The second coordinate axis of MNPS. Captures how broadly spread the current neural state is across the manifold — the configurational breadth of the state. High $d$ corresponds to exploration, representational richness, or transitional states. Low $d$ corresponds to concentrated, convergent activity. Decomposes into three 9D sub-coordinates: $d_n$ (network diffusivity), $d_l$ (local coupling), $d_s$ (representational dispersion).

*DFA $alpha_1$ (`ecg_hrv_dfa_alpha1`)* — Short-range detrended fluctuation analysis exponent of the RR interval series, computed over the 4–16 beat scale. Reflects fractal scaling (long-range correlations) in cardiac variability. $text("DFA") alpha_1 approx 1.0$ is characteristic of healthy long-range correlations; values deviating from unity in either direction indicate altered autonomic complexity. @peng1995

= E – L

*e (Entropy)* — The third coordinate axis of MNPS. Captures local informational uncertainty or complexity of the neural state. High $e$ reflects diverse, unpredictable activity (exploratory states, REM sleep, high cognitive load); low $e$ reflects ordered, predictable activity (consolidated sleep, deep anesthesia, rigid states). Decomposes into three 9D sub-coordinates: $e_e$, $e_s$, $e_m$.

*EAP — Embodied Anchoring Principle* — A Tier-2 extension of NDT.

- *Theory:* posits that interoceptive signals — particularly cardiac phase ($phi_"cardiac"$), respiratory phase ($phi_"resp"$), and HEP — act as boundary conditions for the neural variance schedule $sigma(t)$ and for the potential landscape $F$ via a self-prior term $F_"self"$. Formally: $F mapsto F + lambda(t) F_"self"(X, s_t)$ and $r(t) mapsto r(t)[1 + gamma_"entrain" cos(phi_"cardiac" - phi_theta) cos(phi_"resp" - phi_alpha)]$.
- *Implemented (proxy test):* the anchor surface (`vagal_index`, `anchor_index`, etc.) provides an observational proxy for $lambda_"signal"(t)$. Stage-level co-modulation between the anchor surface and MNPS metrics is tested.
- *Not established:* the cycle-by-cycle entrainment mechanism; any causal influence of interoceptive signals on manifold geometry; applicability to individual prediction. EAP remains Tier-2: mechanism is theorized; the present measurement layer is an initial observational test at stage resolution.

See also: _anchor\_index_, _vagal\_index_, _variance schedule_.

*EDA — Electrodermal Activity* — A measure of skin conductance driven by sweat-gland activity under sympathetic (not parasympathetic) nervous system control, providing a peripheral index of arousal independent of the cardiac/respiratory channels used elsewhere in the anchor surface. Standard practice (and the approach used in the `ds004511` gambling-vs-cognitive-control article) decomposes the raw signal into a *tonic* component (slow-varying skin conductance level, SCL) and a *phasic* component (fast skin conductance responses, SCRs, time-locked to discrete arousing events). Extracted via `neurokit2.eda_process`. @makowski2021neurokit2 Not part of AnchorState v0.1; introduced as a standalone confound-control feature because the primary MNDM pipeline does not natively decompose EDA. See also: _Tonic EDA (SCL)_, _Phasic EDA (SCR)_.

*Epoch-Count Matching* — A robustness/sensitivity procedure that subsamples each subject's epoch-level data (without replacement) to the minimum epoch count observed across the conditions being compared, before recomputing subject-level medians and contrasts. Used to rule out the possibility that a task with systematically more epochs (e.g., a longer gambling session) produces artificially stabilized — and thus artificially larger-looking — effect-size estimates relative to a shorter comparison condition. See also: _Intersection Sample_, _LOOSO_.

*ECG (Electrocardiography)* — The electrical recording of cardiac activity, here recorded simultaneously with EEG in multimodal datasets. Used to detect R-peaks (ventricular depolarizations) from which RR intervals are derived. All HRV metrics in AnchorState v0.1 are computed from the ECG channel.

*Entropy Sub-coordinates ($e_e$, $e_s$, $e_m$)* — The three 9D stratified decompositions of the base $e$ coordinate. $e_e$ captures entropic efficiency; $e_s$ captures state-level entropy; $e_m$ captures meta-entropy (uncertainty about uncertainty). Their precise computation is documented in the MNDM source. See also: _Stratified MNPS_.

*F (Potential Landscape)* — The scalar field over noetic state space defining the "terrain" of possible mental states. $F(X, t)$ assigns a potential energy to each position $X$. The MNDM drifts toward low-$F$ regions: $d X_t = -nabla F(X_t, t) d t + sigma(t) d W_t$. Low $F$ corresponds to attractors (stable, coherent states); high $F$ to saddle points and transition zones. EAP modifies $F$ by adding a self-prior term proportional to interoceptive congruence.

*$F_"self"$  (Self-Prior Potential)* — The EAP addition to the potential landscape. Penalizes neural states that are incongruent with the current bodily state $s_t$: high arousal neural signatures during physiological calm, or constrained geometry during high-load conditions. Scaled by $lambda(t) = lambda_"signal"(t) lambda_"binding"(t)$. Not yet directly measured; the anchor surface provides an indirect proxy.

*Friedman Test* — Non-parametric repeated-measures test (analogue of one-way ANOVA for ranks). Used throughout NDT articles to test whether MNPS coordinates or anchor metrics differ across task stages within subjects. Robust to non-normality; appropriate for the within-subject, repeated-measures design. Follow-up pairwise tests use Wilcoxon signed-rank with BH-FDR correction.

*GG — Gambling Game (task label)* — One of three within-subject conditions in `ds004511`. Officially the "Spontaneous Deception Task": a solitary, self-paced task in which participants privately observed the outcome of a dice roll, placed a bet on their own prediction, and self-reported to the system whether the prediction was correct, over 144 rounds, under a cover story designed to create an unmonitored opportunity to misreport outcomes. There is no computerized partner, no cooperate/defect choice, and no social-interaction component. Contrasted against cognitive control (CC) and eyes-closed rest. GG sessions are substantially longer than CC or Rest sessions, motivating the epoch-count-matching sensitivity check. Trial-level outcome/deception labels are not available in the BIDS `events.tsv` files, so all GG effects reported in the `ds004511` gambling-vs-cognitive-control article are block-level rather than trial- or deception-specific. See also: _CC — Cognitive Control (task label)_, _Epoch-Count Matching_.

*`geometry_contract`* — A quality gate in the MNDM pipeline ensuring that Jacobian computations are valid (sufficient retained windows, minimal artifact contamination). Analyses of MNJ-derived metrics are restricted to windows and subjects passing the geometry contract.

*HEP — Heartbeat-Evoked Potential* — An EEG waveform time-locked to the R-peak of the ECG, reflecting cortical processing of cardiac signals. In EAP, HEP amplitude ($A_"HEP"(t)$) is a component of the interoceptive state vector $s_t$ that conditions the self-prior. Not yet extracted in the current MNDM pipeline; included in the formal EAP framework as a future measurement layer.

*HRV — Heart Rate Variability* — The variation in time intervals between successive heartbeats (RR intervals or NN intervals). Reflects autonomic nervous system modulation of cardiac pacemaking: higher HRV generally indicates stronger parasympathetic (vagal) tone and adaptive autonomic flexibility. In MNDM, computed from the ECG channel using a 60-second sliding superwindow. Key HRV metrics: RMSSD, pNN50, SDNN, HR mean, SampEn, DFA $alpha_1$. Reference standard: @taskforce1996

*HRV Sliding-Superwindow Architecture* — The MNDM pipeline computes HRV over a 60-second window centered on each block-native epoch's midpoint, extracting all valid RR intervals within that 60-second span. The 4-second epoch step defines output resolution (how densely the pipeline samples the block), not the HRV integration window. This architecture yields reliable short-term HRV estimates at fine temporal resolution.

*Intersection Sample* — In a multi-task design, the subset of subjects with valid, quality-passing data in *all* conditions being compared (as opposed to the full per-condition sample, which may vary in composition from condition to condition). Restricting analyses to the intersection sample removes any imbalance introduced by subjects contributing to only a subset of conditions. In the `ds004511` gambling-vs-cognitive-control article, the intersection sample comprises $N = 44$ of 45 subjects (44 valid GG, 45 valid CC, 45 valid Rest; one subject, `sub-S200203`, has no GG data and is excluded from the intersection). See also: _Epoch-Count Matching_.

*Jacobian Frobenius Norm* — A scalar summary of the local MNJ: $||bold(J)||_F = sqrt(sum_(i,j) J_(i j)^2)$. Reflects the overall magnitude of local state-space deformation — how strongly small perturbations in the current MNPS position are amplified or attenuated. Used as the primary MNJ summary in regional and stage-level comparisons.

*$lambda(t)$ (Lambda — Self-Prior Strength)* — The EAP parameter that scales how strongly the self-prior $F_"self"$ influences the potential landscape. $lambda(t) = lambda_"signal"(t) lambda_"binding"(t)$: the signal component reflects the reliability of interoceptive signaling (strong vagal tone → stronger signal); the binding component reflects neural processing of that signal. `vagal_index` is the operational proxy for $lambda_"signal"(t)$.

*Local Coupling ($d_l$)* — A sub-coordinate of the Diffusivity axis ($d$) within the 9D stratified MNPS. Measures short-range, intense communication between adjacent neural elements. High $d_l$ is associated with local synchrony, rumination, or tremor-like activity. Contrast with $d_n$ (global broadcast).

*LOOSO — Leave-One-Subject-Out* — A robustness check in which a group-level contrast (e.g., a paired Cohen's $d$) is recomputed once per subject, each time excluding that one subject from the sample. If the sign and approximate magnitude of the effect are preserved across all iterations ("sign-consistent"), the effect is not being driven by a small number of outlier subjects. Used in the `ds004511` gambling-vs-cognitive-control confound audit, alongside bootstrap and permutation checks. See also: _Bootstrap Confidence Interval_, _Permutation Test (Within-Subject Sign-Flip)_.

= M – R

*m (Metastability / Mobility)* — The first coordinate axis of MNPS. Captures the overall regime or configurability of the neural state: how reconfigurable, coordinated, and dynamically navigable the current state is. High $m$ indicates states with broad access to the manifold (flexible, task-engaged); low $m$ indicates constrained or rigid states. In the 9D decomposition it separates into $m_a$, $m_e$, $m_o$. _Note: should be read as a broad mobility/metastability proxy rather than as any single EEG formula._

*Manifold* — The geometric structure (lower-dimensional surface embedded in high-dimensional brain-state space) on which neural trajectories unfold. NDT assumes that neural activity during a given functional state lives near a learned manifold; the MNPS coordinates are a low-dimensional description of position and dynamics on this manifold. Topology (basins, ridges, corridors) is inferred from occupancy and reachability.

*MDR — Manifold Deformation Rate (`mdr`)* — An MNJ scalar summary measuring the proportion of the local Jacobian's total magnitude attributable to its diagonal (axis-aligned expansion/compression) terms: $text("mdr") = sum_i |J_(i i)| / (||J||_F + epsilon)$. A secondary/structural MNJ endpoint alongside `rotational_power` and `aci`, higher during gambling than cognitive control or rest in the `ds004511` article, consistent with gambling's deformation being more axis-aligned/expansive and less rotationally structured. See also: _Meta-Noetic Jacobian_, _ACI — Anisotropic Compression Index_.

*MNDM — Meta-Noetic Diffusion Model* — The mathematical model and computational pipeline at the center of NDT. (1) _Theory_: the stochastic differential equation $d X_t = -nabla F(X_t,t) d t + sigma(t) d W_t$ describing how neural state evolves on a potential landscape under rhythmic variance control. (2) _Pipeline_: the NeuralManifoldDynamics software that processes EEG (and multimodal) data into MNPS coordinates, MNJ outputs, anchor surface metrics, and trajectory geometry. The pipeline version (2.3, 2.4, etc.) determines which outputs are available.

*MNPS — Meta-Noetic Phase Space* — The three-dimensional coordinate system for neural state: $(m, d, e)$ — metastability/mobility, diffusivity, entropy. Every block-native epoch is mapped to a point in MNPS. The 9D stratified extension decomposes each axis into three sub-coordinates for finer-grained analysis. MNPS coordinates are the primary empirical objects tested in NDT articles.

*MNJ — Meta-Noetic Jacobian* — The local Jacobian of the neural flow field at the current MNPS position: how small perturbations to the current state would evolve under the current dynamics. The MNJ describes the *shape* of the flow (expansion, contraction, rotation, shear) rather than its direction. Summarized by the Frobenius norm (overall deformation magnitude), eigenvalue structure (directions of expansion/contraction), and — in MNDM 2.4 — inter-regional directed coupling (`coupl_*`).

*Network Diffusivity ($d_n$)* — A sub-coordinate of the Diffusivity axis ($d$) within the 9D stratified MNPS. Captures the breadth of global information broadcast — how widely activity spreads across the whole brain. High $d_n$ is associated with widespread synchrony or global workspace engagement; low $d_n$ with isolated local processing.

*NDT — Noetic Diffusion Theory* — The overarching theoretical framework. Core claim: conscious neural dynamics emerge from rhythmically guided denoising on a learned geometric manifold. "Noetic" (knowledge-bearing) signals that the process generates meaningful content, not mere signal processing. "Diffusion" refers to both the stochastic differential equation governing dynamics and the analogy with generative diffusion models (learned score functions / gradients of the data distribution). NDT organizes its empirical claims into a four-layer hierarchy: MNPS coordinates → MNJ structure → Reachability → Anchoring.

*NN Intervals* — Normal-to-normal intervals: the time intervals between consecutive R-peaks that have both been classified as normal sinus beats (artifact-free). The primary input to HRV metrics. NN count (the number of valid NN intervals in a window) is a key quality indicator: too few NN intervals (< 10–20 per window) yield unreliable HRV estimates.

*Noetic Atlas* — A planned repository of aggregated MNPS mappings forming a reference database of neural state geometries across conditions, populations, and datasets. Analogous to a cartographic atlas: individual participant manifolds contribute to a shared coordinate frame.

*Oscillatory Flexibility ($m_o$)* — A sub-coordinate of the Metastability axis ($m$) within the 9D stratified MNPS. Reflects how readily neural oscillations change frequency or phase. High $m_o$ allows fluid mode-switching between cognitive operations; low $m_o$ indicates frequency-locked, rhythmically rigid states.

*Page Trend Test* — Non-parametric test for an ordered (monotone) alternative across $k$ repeated conditions. Used in NDT articles to test whether MNPS or anchor metrics increase or decrease monotonically across the cognitive load gradient (rest → listen → mem5 → mem9 → mem13).

*Permutation Test (Within-Subject Sign-Flip)* — A non-parametric significance test in which the sign of each subject's paired difference (e.g., a GG$-$CC contrast) is randomly flipped (Rademacher $plus.minus 1$) many times (typically 5000), and the observed statistic (e.g., median difference) is compared against the resulting null distribution to obtain an exact $p$-value. Makes no distributional assumptions beyond exchangeability of sign under the null hypothesis of no true difference. Used as one leg of the `ds004511` confound-audit protocol. See also: _Bootstrap Confidence Interval_, _LOOSO_.

*Phasic EDA (SCR — Skin Conductance Response)* — The fast-varying component of electrodermal activity, consisting of discrete skin conductance responses (SCRs) time-locked to arousing events. Summarized per epoch by SCR rate (events/min), mean SCR amplitude, and SCR count. Contrast with the slow-varying tonic component (SCL). See also: _EDA — Electrodermal Activity_, _Tonic EDA (SCL)_.

*pNN50* — Proportion of consecutive NN intervals differing by more than 50 ms. A time-domain HRV metric reflecting high-frequency (vagal) modulation. Complements RMSSD; both are captured by `vagal_index`.

*PPG — Photoplethysmography* — An optical measure of blood volume pulse at a peripheral site (e.g., fingertip). Provides heart rate and, importantly, pulse waveform amplitude and its variability — the basis for `vascular_index`. PPG is a modality fallback in AnchorState: when ECG quality fails, PPG-derived HRV is used.

*`pupil_arousal_index`* — Pupillometry-based component of AnchorState v0.1. Derived from pupil dilation velocity and diameter (z-scored within subject). Reflects noradrenergic/locus coeruleus–NE arousal. Falls back to this index when both ECG and PPG are unavailable or low quality.

*r(t) (Rhythmic Control)* — A time-varying signal in [0, 1] reflecting the strength of slow neural rhythms (theta–gamma phase–amplitude coupling, spindle–slow oscillation nesting, cardiac/respiratory oscillations). Directly controls the variance schedule: $sigma(t) = sigma_"min" + sigma_0(1 - r(t))$. High $r(t)$ narrows variance (focused denoising); low $r(t)$ widens it (exploration). EAP extends $r(t)$ by adding cardiac and respiratory entrainment.

*Reachability* — The short-horizon capacity of the neural system to transition from its current MNPS position into nearby future states, given the current flow structure (MNJ eigengeometry). Separates *where the system is* (occupancy in MNPS) from *what it can still do from there* (dynamical freedom). Characterized by the reachability cone: volume ($log$-determinant), shape (canalization, $kappa$), and effective dimensionality ($d_"eff"$). Low reachability volume indicates dynamical arrest.

*Representational Dispersion ($d_s$)* — A sub-coordinate of the Diffusivity axis ($d$) within the 9D stratified MNPS. Measures the richness and diversity of simultaneously active neural representations. High $d_s$ is associated with complex stimuli, integrative processing, or creative cognition. Low $d_s$ with simple, sparse representations.

*RMSSD* — Root mean square of successive differences between adjacent NN intervals. The primary time-domain HRV metric for vagal (parasympathetic) tone. Robust to non-stationarities in the RR series. The main physiological driver of `vagal_index`. Units: milliseconds.

*`resp_anchor_index`, `resp_regular_index`, `resp_phase_consistency`* — MNDM-native respiration-derived features quantifying how regular and how strongly phase-locked a subject's breathing is relative to their concurrent neural trajectory. Higher values indicate more regular, more strongly phase-locked breathing. Tested as candidate EAP-compatible coupling variables and as physiological confound candidates against the primary MNJ effect in the `ds004511` gambling-vs-cognitive-control article; in cognitive control, higher `resp_anchor_index` was moderately associated with lower MNPS mobility ($m$) after controlling for HRV, a secondary/exploratory finding. See also: _EAP — Embodied Anchoring Principle_.

*Rotation Norm (`rotation_norm`)* — An MNJ scalar summary of the antisymmetric (purely rotational) component of the local Jacobian: $text("rotation_norm") = ||J_"anti"||_F$, where $J_"anti" = frac(1,2)(J - J^top)$. Captures the magnitude of structured, cyclical local flow, independent of the expansive/contractive (symmetric) component. See also: _Rotational Power_, _ACI — Anisotropic Compression Index_.

*Rotational Power (`rotational_power`)* — An MNJ scalar summary normalizing the rotational component by the total deformation: $text("rotational_power") = ||J_"anti"||_F^2 / (||J||_F^2 + epsilon)$. Distinguishes deformation that is predominantly structured/cyclical (high rotational power, as in cognitive control and rest, consistent with organized oscillatory dynamics) from deformation that is predominantly expansive/contractive and unstructured (low rotational power, as observed during gambling). See also: _Jacobian Frobenius Norm_, _ACI — Anisotropic Compression Index_, _MDR — Manifold Deformation Rate_.

= S – Z

*$s_t$ (Interoceptive State Vector)* — The EAP vector summarizing the current bodily state as perceived by the brain: $s_t = (phi_"cardiac"(t), phi_"resp"(t), A_"HEP"(t))$. Conditions the self-prior $F_"self"$ and the variance entrainment equation. Not directly measured in current MNDM analyses; operationalized through the AnchorState proxy surface.

*SampEn — Sample Entropy (`ecg_hrv_sampen`)* — A nonlinear HRV complexity metric quantifying the unpredictability of the RR interval series. Defined as $-ln(A/B)$ where $A$ counts template matches at length $m+1$ and $B$ at length $m$ (parameters $m = 2$, $r = 0.2 times "SDNN"$). Higher SampEn indicates more complex, less predictable cardiac dynamics — reflecting richer interoceptive input under EAP. @richman2000

*SDNN* — Standard deviation of all NN intervals within a window. A global HRV metric reflecting overall autonomic modulation (both sympathetic and parasympathetic contributions). Included in `vagal_index` computations in some MNDM configurations.

*$sigma(t)$ (Variance Schedule)* — The noise amplitude in the MNDM SDE: $sigma(t) = sigma_"min" + sigma_0(1 - r(t))$. Governs how much stochastic exploration is permitted at each moment. High $sigma$: wide, winding trajectories through the manifold (creative, flexible, or confused states). Low $sigma$: narrow, directed trajectories (focused denoising, efficient task performance). EAP's core claim is that bodily signals modulate $sigma(t)$ via $r(t)$.

*Spectral Radius (`spectral_radius`)* — An MNJ scalar summary defined as the largest-magnitude eigenvalue of the local Jacobian, $rho(J) = max_i |lambda_i(J)|$. Along with the Frobenius norm, one of the two primary (absolute deformation magnitude) MNJ endpoints in the `ds004511` gambling-vs-cognitive-control article; substantially elevated during gambling relative to both cognitive control and rest. See also: _Jacobian Frobenius Norm_, _Meta-Noetic Jacobian_.

*Spearman Rank Correlation* — Non-parametric correlation used throughout for within-subject anchor–MNPS associations and cross-lag analyses. Robust to outliers and non-normal distributions. Reported as $r_s$; significance after BH-FDR correction.

*Stratified MNPS (9D Sub-coordinates)* — A higher-resolution decomposition of the three base MNPS axes $(m, d, e)$ into nine sub-coordinates: $m_a$ (attentional mobility), $m_e$ (affective mobility), $m_o$ (oscillatory flexibility), $d_n$ (network diffusivity), $d_l$ (local coupling), $d_s$ (representational dispersion), $e_e$ (entropic efficiency), $e_s$ (state entropy), $e_m$ (meta-entropy). Each sub-coordinate provides finer information about the texture of the neural state within its parent dimension. Available from MNDM 2.4+ (`coords_9d`).

*`sympathetic_index`* — AnchorState component.

- *Implemented:* $text("sympathetic_index")(t) approx -z(text("RMSSD")) + z(text("HR"))$. Shares RMSSD term with `vagal_index` — not independent.
- *Interpretation:* a composite arousal proxy (high HR + low short-term HRV). Raw HR and RMSSD are the primary physiological quantities; `sympathetic_index` is an operationalization of their balance.
- *Not established:* direct sympathetic nervous system activity. The label "sympathetic" is a conventional shorthand for the sympathovagal balance direction, not a direct measurement of efferent sympathetic outflow.

*Tonic EDA (SCL — Skin Conductance Level)* — The slow-varying baseline component of electrodermal activity, reflecting sustained sympathetic arousal over seconds-to-minutes timescales, distinct from event-locked phasic responses. In the `ds004511` gambling-vs-cognitive-control article, tonic SCL was equally elevated during gambling and cognitive control relative to rest, but did not differ between gambling and cognitive control themselves ($d = -0.08$, $p = 0.51$) — a key dissociation used to rule out generic arousal as an explanation for the large MNJ Frobenius-norm difference between those two tasks. See also: _EDA — Electrodermal Activity_, _Phasic EDA (SCR)_.

*Trace (`trace`)* — An MNJ scalar summary equal to the sum of the local Jacobian's diagonal entries, $text("trace") = sum_i J_(i i)$, indicating net local expansion (positive) or contraction (negative) averaged across all axes. In the `ds004511` gambling-vs-cognitive-control article, `trace` was the one MNJ metric that did not differentiate any pair of tasks after correction, unlike the other six non-trace MNJ scalars. See also: _Meta-Noetic Jacobian_, _Jacobian Frobenius Norm_.

*Trajectory Efficiency (`traj_efficiency`)* — A per-block metric quantifying how directed the neural trajectory was in MNPS.

- *Implemented:* $text("traj_efficiency") = text("endpoint_distance") / text("path_length")$, where endpoint distance $= || bold(x)_n - bold(x)_1 ||_2$ and path length $= sum_{i=1}^{n-1} || bold(x)_{i+1} - bold(x)_i ||_2$. Values near 1 = straight-line motion; near 0 = winding path returning near start. Undefined for blocks with fewer than two finite-MNPS windows.
- *Interpretation:* directedness of the neural chart trajectory within a block. A mem5 task-geometry optimum (efficiency ≈ 0.98) vs rest (≈ 0.04) has been observed in ds003838. The within-task non-monotone gradient (mem5 > mem9 > mem13) is the more controlled finding.
- *Not established:* cognitive efficiency, neural optimality, consciousness quality, or health status. No validated clinical reference range exists. The result has not been benchmarked against simpler EEG baselines (PCA, bandpower trajectories) in the current article.

*`traj_mean_curvature`, `traj_max_curvature`* — Per-block trajectory geometry metrics. Mean curvature is the average angular deflection between consecutive MNPS steps; max curvature is the largest single deflection. High curvature indicates abrupt direction changes (tortuous, non-linear traversal); low curvature indicates smooth, ballistic movement through the manifold.

*`traj_path_length`* — Cumulative Euclidean distance traveled through MNPS within a block. Longer path lengths indicate greater dynamical exploration; short path lengths indicate constrained, low-energy dynamics. Path length is normalized by window count in some analyses to control for block-length differences.

*`vagal_index`* — The primary HRV-derived autonomic proxy in AnchorState v0.1.

- *Implemented:* $text("vagal_index")(t) = z(text("RMSSD")) + z(text("pNN50"))$, within-subject z-scored across all valid windows, computed from the ECG channel via the HRV v0.1 pipeline with a 60-second superwindow.
- *Interpretation:* HRV-derived proxy for vagally mediated cardiac modulation. Higher values reflect greater short-term RR interval variability. Stage-level ordering (listen > mem phases) is the primary empirical claim.
- *Not established:* direct measurement of vagal nerve activity, absolute parasympathetic tone, or $lambda_"signal"(t)$. RMSSD values are physiologically plausible (rest ~40 ms; see S2.0). The theoretical EAP mapping to $lambda_"signal"(t)$ remains speculative.

*Variance Schedule Entrainment* — The EAP mechanism by which cardiac and respiratory phase alignment amplifies rhythmic variance control: $r(t) mapsto r(t)[1 + gamma_"entrain" cos(phi_"cardiac" - phi_theta) cos(phi_"resp" - phi_alpha)]$. When cardiac, respiratory, and neural rhythms align in phase, variance control is tightened (more efficient, directed trajectories); desynchronization loosens it. Coupling strength $gamma_"entrain" approx 0.1$–$0.3$ is a theoretical parameter; not yet estimated empirically.

*`vascular_index`* — AnchorState component reflecting peripheral vascular tone from PPG waveform: $text("vascular_index")(t) approx z(text("PPG_amplitude")) - z(text("PPG_amplitude_CV"))$. High amplitude with low coefficient of variation indicates stable, strong pulse — a proxy for parasympathetically mediated vascular tone and peripheral blood flow regulation.

*Wilcoxon Signed-Rank Test* — Non-parametric test for paired within-subject comparisons. Used for pairwise stage contrasts in NDT articles. Reports $W$ statistic, two-tailed $p$-value, and Cohen's $d$ on rank-transformed differences. BH-FDR applied across all contrasts within a family.

---

#bibliography("references.bib")

_Abbreviation index: ACI (Anisotropic Compression Index) · BH-FDR (Benjamini–Hochberg False Discovery Rate) · CC (Cognitive Control task label) · DFA (Detrended Fluctuation Analysis) · EAP (Embodied Anchoring Principle) · ECG (Electrocardiography) · EDA (Electrodermal Activity) · GG (Gambling task label) · HEP (Heartbeat-Evoked Potential) · HRV (Heart Rate Variability) · LC-NE (Locus Coeruleus – Norepinephrine) · LOOSO (Leave-One-Subject-Out) · MDR (Manifold Deformation Rate) · MNJ (Meta-Noetic Jacobian) · MNDM (Meta-Noetic Diffusion Model / NeuralManifoldDynamics pipeline) · MNPS (Meta-Noetic Phase Space) · NDT (Noetic Diffusion Theory) · NN (Normal-to-Normal intervals) · PAC (Phase-Amplitude Coupling) · PPG (Photoplethysmography) · RMSSD (Root Mean Square of Successive Differences) · RVC (Rhythmic Variance Control) · SCL (Skin Conductance Level) · SCR (Skin Conductance Response) · SDNN (Standard Deviation of NN intervals) · SDE (Stochastic Differential Equation)_
