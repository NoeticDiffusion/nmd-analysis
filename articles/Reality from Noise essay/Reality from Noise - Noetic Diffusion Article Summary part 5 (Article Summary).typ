// Reality from Noise - Noetic Diffusion Article Summary part 5
// Scientific summaries of the core theoretical and empirical manuscripts in NDT

#import "template.typ": essay-template

#show: doc => essay-template(
  title: [Noetic Diffusion Article Summaries],
  subtitle: [Scientific review of the core theoretical and empirical manuscripts],
  author: [Robin Langell],
  date: [2026],
  doc,
)

= Introduction

This document provides scientific summaries of the foundational and currently published manuscripts defining Noetic Diffusion Theory (NDT), its measurement frameworks (MNPS, Stratified MNPS, MNJ), and its empirical validation across clinical, sleep, altered-state, and computational settings. The summaries follow the structure of Abstract, Methods, Results, and Discussion to facilitate technical review and integration into the broader scientific narrative. This version tracks the current published Zenodo corpus where a stable source manuscript is available in the repository.

#pagebreak()

= Article 1: #link("https://doi.org/10.5281/zenodo.17367307")[Noetic Diffusion Theory (NDT)]
*A Rhythmic, Geometric Framework for Neural State Reconstruction and Conscious Correlates*

== Abstract
Noetic Diffusion Theory (NDT) introduces a mechanistic account of consciousness as a process of rhythmically guided denoising on a learned geometric manifold. The theory formalizes the Meta–Noetic Diffusion Model (MNDM), a stochastic differential equation (SDE) where conscious states correspond to trajectories in a latent phase space. By linking neural rhythms (e.g., theta–gamma, SO–spindle) to a variance schedule, NDT provides a bridge between neurobiology and the geometric organization of mental states. The manuscript defines the theoretical core, introduces the Noetic Atlas over Meta–Noetic Phase Space (MNPS), and derives testable predictions regarding entropy dynamics and manifold topology.

== Method
The MNDM is formulated as a guided SDE: $d X_t = -nabla F(X_t, t) d t + sigma(t) d W_t$, where $X_t$ is the noetic state, $F$ is a potential landscape representing learned meaning, and $sigma(t)$ is a rhythmic variance schedule. Rhythmic Variance Control (RVC) specifies that high-amplitude neural rhythms (high $r(t)$) anti-phasically modulate the noise variance ($sigma(t) approx 1 - r(t)$), forcing the system into aggressive denoising epochs. The Meta–Noetic Phase Space (MNPS) is defined by three primary axes: entropy ($e$), diffusivity ($d$), and mobility ($m$), which serve as a measurement chart for BOLD or EEG-derived features.

== Results
Simulations demonstrate that RVC reproduces characteristic wake–sleep trajectories and step-wise entropy reductions time-locked to rhythmic events (e.g., spindles). The model identifies "meaningful" states as low-potential basins in $F$ that balance integration and segregation ($d$-axis). A critical finding is the resolution of the "Grand Mal Paradox": by incorporating the deviation term $d(X)$, the model distinguishes between functional coherence and pathological hypersynchrony (seizures), which otherwise would appear as "maximal meaning" in a simpler $e-m$ potential.

== Discussion
NDT positions consciousness as an active reconstructive process rather than a passive observation. By framing conscious level as a property of manifold traversability rather than raw activity, it offers a geometric alternative to information-theoretic models (like IIT) and connects to the Free-Energy Principle through the lens of precision scheduling. The theory's primary contribution is providing explicit empirical hooks—geometric signatures in MNPS—that can be tested using existing public datasets without requiring new experimental paradigms.

#pagebreak()

= Article 2: #link("https://doi.org/10.5281/zenodo.17643472")[Stratified MNPS]
*Unmasking Neural Mechanisms beneath the Manifold*

== Abstract
Stratified MNPS extends the base 3D MNPS framework into a 9D sub-coordinate chart to resolve the mechanistic ambiguity inherent in composite axes. While the base axes ($m, d, e$) describe that a state differs, the stratified layer reveals how that difference is achieved. This manuscript specifies the mathematical and operational definitions for nine sub-coordinates (three per principal axis) and demonstrates their utility in clinical EEG data from Parkinson’s disease and mTBI.

== Method
Each MNPS axis is decomposed into three channels:
- *Metastability ($m$)*: Attentional ($m_a$), Affective ($m_e$), and Oscillatory ($m_o$) mobility.
- *Diffusivity ($d$)*: Network diffusivity ($d_n$), Local coupling ($d_l$), and Representational dispersion ($d_s$).
- *Entropy ($e$)*: Dynamic entropy ($e_e$), Phase entropy ($e_s$), and Efficiency proxy ($e_m$).
These are operationalized using specific EEG features (e.g., wPLI for $d_l$, spectral-centroid CV for $m_o$, multiscale entropy for $e_e$). Inference is performed on within-subject robust z-scores, recomposing back to (m, d, e) via robust aggregates (Huber mean/median).

== Results
Pilot analysis of the ds003490 (Parkinson's) dataset revealed a "mechanistic dissociation" masked at the composite level: L-DOPA medication robustly reduced local coupling ($d_l$) while increasing attentional mobility ($m_a$), yielding a near-zero net change in the composite diffusivity ($d$). In mTBI (ds005114), the framework identified a directionally distinct profile characterized by increased local coupling ($d_l$) and reduced representational spread ($d_s$), illustrating the diagnostic power of the 9D vector over 3D composites.

== Discussion
Stratified MNPS addresses the problem of "same composite, different mechanism." It provides a high-resolution measurement contract that remains theory-aligned through its link to the MNDM potential. The results suggest that the brain may employ homeostatic conservation, trading off specific sub-mechanisms to maintain stable global coordinates. This framework is proposed as a necessary layer for "geometric psychiatry," enabling more precise subtyping of disorders.

#pagebreak()

= Article 3: #link("https://doi.org/10.5281/zenodo.17505071")[Geometric Fingerprints of Alzheimer’s Disease]
*First Visualization via Noetic Diffusion Mapping™*

== Abstract
This manuscript provides the first proof-of-concept for Noetic Diffusion Mapping™ (NDM™), establishing that clinically-relevant signatures of neurodegeneration are detectable from ultra-brief (8-second) EEG segments. By generating "geometric fingerprints"—spatial portraits of state organization in MNPS—the study identifies robust patterns of manifold collapse and rhythmic disruption in patients with Alzheimer's disease (AD).

== Method
Resting-state EEG (eyes closed) from 80 AD patients and 12 healthy controls (ds004504) was projected into MNPS coordinates (E, R, D). A hybrid visualization approach was used to generate three-panel fingerprints: density fields, trajectories with traffic-light speed coding, and cluster assignments. Group differences were quantified using Welch t-tests and BH-FDR correction across coordinate axes and dynamical indices.

== Results
AD patients exhibited a very large elevation in rhythmic deviation (R-axis; Cohen's $d = 2.31$, $p < 10^{-6}$) and a large shift in density topology (D-axis; $d = -0.85$). Visually, AD fingerprints were characterized by "collapsed manifold volume": tighter clustering around limited states, reduced spatial exploration, and slower trajectory speeds. Individual cases showed high within-group consistency, with AD patients spending ~45% of their time in a single "pathological corner" of MNPS compared to the balanced distribution seen in healthy elders.

== Discussion
The study demonstrates that 8-second EEG snapshots carry sufficient geometric information for clinical discrimination. The observed signatures—canalized trajectories and reduced degrees of freedom—align with phenomenological reports of cognitive rigidity in AD. By bridging molecular pathology and real-time functional geometry, NDM™ offers a promising bedside modality for screening and longitudinal monitoring that complements structural imaging and molecular biomarkers.

#pagebreak()

= Article 4: #link("https://doi.org/10.5281/zenodo.17505010")[The Meta-Noetic Jacobian (MNJ)]
*Measuring Second-Order Dynamics of Conscious Systems*

== Abstract
The Meta–Noetic Jacobian (MNJ) framework elevates NDT from a state-based description to a second-order dynamical theory. By defining the Jacobian of the flow in MNPS, the manuscript introduces a tensorial representation of meta-dynamics—the dynamics of the rules of change themselves. This allows for the quantification of higher-order properties such as meta-stability, rotation (cyclic meta-coupling), and meta-plasticity.

== Method
Given the MNPS state vector $bold(x)(t) = [m, d, e]$, the flow field is $bold(F)(bold(x), t) = dot(bold(x))(t)$. The MNJ is the Jacobian $bold(J) = partial bold(F) / partial bold(x)$, capturing cross-axis couplings (e.g., $partial dot(m) / partial e$). $bold(J)$ is estimated from discretely sampled MNPS trajectories using robust local linear models (kNN + ridge regression). Key scalar invariants are derived: trace (meta-expansion/divergence), rotational norm (curl/cyclic coupling), and eigenvalue dispersion (anisotropy/channelization).

== Results
The tensorial approach reveals that conscious systems regulate their own self-transformation. High MNJ rotation corresponds to structured, cyclic exploration (found in wake and REM), while low rotation and trace near zero define "dynamical arrest" (found in anesthesia and seizures). The real parts of the Jacobian eigenvalues quantify meta-stability, with stable configurations corresponding to bounded real parts ($Re(lambda_k) < 0$).

== Discussion
The MNJ framework provides a formal language for self-reference, metacognition, and "thinking of thought." It distinguishes systems that may have similar static complexity but different adaptive rules. The manuscript proposes the "Meta-Noetic Hypothesis": conscious systems maintain coherence not by stabilizing their states, but by regulating the meta-geometry of their own transformation. This has implications for both clinical biomarker development and the design of self-regulating artificial intelligence.

#pagebreak()

= Article 5: #link("https://doi.org/10.5281/zenodo.17802244")[Regional MNPS in fMRI Child–Adult Movie Viewing]
*Child–Adult Manifold Dynamics in a Naturalistic Movie*

== Abstract
This article applies the MNPS framework to fMRI BOLD data, shifting the focus from global manifolds to regional realizations. Using the ds000228 dataset, it characterizes developmental changes in manifold geometry across childhood (ages 3–12) and adulthood. The results reveal that developmental MNPS signatures are network-specific and progressively resolved at finer analytical scales.

== Method
Parcellated BOLD features (variance, LF-power, modularity) were projected into 3D and 9D Stratified MNPS coordinates for 122 children and 33 adults. Regional MNPS was implemented by computing network-specific trajectories for canonical systems (VIS, SMN, DMN, FPN, SAL). Event-locked analyses compared MNPS deltas during Theory-of-Mind (ToM) and pain movie segments. Group differences were assessed using Cliff's delta ($delta$).

== Results
Children showed a modest global expansion of manifold volume ($delta approx 0.19$). However, Regional MNPS revealed much stronger network-specific effects: visual (VIS) and somatomotor (SMN) networks showed robust child > adult increases in all coordinates ($delta approx 0.35$--$0.39$), while the default mode network (DMN) showed minimal differences. Event-locked ToM segments in children produced more structured, entropy-dampened configurations ($m_a$ and $d_n$ up, $e_e$ down), while pain segments produced more entropic states.

== Discussion
The study establishes fMRI-based MNPS as a viable tool for mesoscale developmental neuroscience. The VIS/SMN-dominant results suggest that sensory manifolds undergo more pronounced geometric contraction during development than association networks. The findings position Regional MNPS as a "phase-space reparametrisation" of traditional connectivity results, providing a unifying geometric vocabulary for the maturation of the "social brain."

#pagebreak()

= Article 6: #link("https://doi.org/10.5281/zenodo.17856521")[Dynamical Arrest Under Propofol]
*Reduced Traversability and Meta-Noetic Jacobian Flattening*

== Abstract
This manuscript treats propofol-induced anesthesia as a "traversability contraction test" for NDT. By analyzing both EEG and fMRI during graded sedation, the study asks whether loss of consciousness corresponds to a geometric restriction of accessible manifold space rather than simple amplitude dampening.

== Method
 matched MNPS/MNJ pipelines were applied to fMRI (ds003171) and EEG (ds005620) data across awake, sedation, and recovery states. Traversability was operationalized using the TraversabilityIndex ($T = v_"med" dot (1 - a_"norm")$), combining trajectory speed and Jacobian anisotropy. EEG stratified profiles were examined for redistribution patterns across $d_s$, $e_s$, and $m_o$.

== Results
EEG results showed a dramatic reduction in traversal speed and a significant "flattening" of the Meta–Noetic Jacobian (rotation and Frobenius norms dropped; trace remained near zero). This defines a state of dynamical arrest: the system moves into a high-dispersion ($d_s$), high-entropy ($e_s$), but low-velocity pocket of the manifold. Manifold volume (MV) paradoxically increased in EEG (confinement to a rigid, high-coordinate sector) but decreased modestly in fMRI. fMRI MNJ was unresolved at the TR temporal scale, serving as a methodological boundary check.

== Discussion
The study redefines "geometric collapse" operationally as reduced traversability. Loss of consciousness is not necessarily a uniform coordinates shrinkage but a confinement to a "rigid sector" where the mind's horizon of possibility collapses. The staged recovery results suggest that manifold directions reconstitute in a specific order, with behavioral recovery preceding full restoration of manifold diversity. This work establishes the MNJ as a diagnostic marker for "order without adaptive traversal."

#pagebreak()

= Article 7: #link("https://doi.org/10.5281/zenodo.18071624")[Extreme Neurodynamic Regimes]
*A Multi-State Validation Plan Reveal Meta–Noetic Dissociations*

== Abstract
This manuscript presents a comprehensive multi-dataset stress-test of NDT's measurement apparatus across extreme neurodynamic regimes: deep sleep, anesthesia, seizures, psychedelics, and clinical pathologies. It serves as a large-scale validation of whether MNPS, Stratified MNPS, and MNJ remain discriminative and interpretable under conditions where traditional scalar metrics often collapse or blur.

== Method
The study utilizes a fixed "reporting contract" across a diverse battery of open datasets (ds005555, ds004100, ds004504, ds003059, etc.). It prioritizes dissociations between occupancy (state location) and capacity (traversal speed + MNJ structure). Analysis includes the "Stratified Block-Jacobian" (9×9 Jacobian grouped into coordinate-family blocks) to identify mechanism-specific meta-dynamic shifts.

== Results
The strongest dissociations were found in regimes with clear staging:
- *Sleep (ds005555)*: Large, coherent separations across all layers; NREM3 showed "centralization" (low $d_n$, low $m_o$), while REM showed "repertoire expansion."
- *Seizures (ds004100)*: The Spread ↑ but Capacity ↓ signature—broad occupancy coupled with collapsed speed and rotational structure.
- *Clinical EEG (ds004504, ds003478, ds003947)*: Global MNPS was often near-null, but Stratified 9D or Block-Jacobians revealed selective, mechanism-specific shifts (e.g., $d$-block collapse in dementia).
- *fMRI (ds006623, ds003059)*: 3D MNJ was resolution-limited, but 9D block summaries and behavior-anchored segmentation revealed meta-dynamic effects in sedation.

== Discussion
Article 7 establishes that consciousness is better tracked by traversability-based indices than by raw entropy or activity. The findings constrain the conditions under which NDT's signatures appear and document regime-specific failure modes. The "Meta-Noetic Dissociation" principle—where different layers of the same state description diverge—is proposed as the primary falsification surface for future work. The study positions NDT as a robust, reproducible framework for mapping the boundaries of conscious experience.

#pagebreak()

= Article 8: #link("https://doi.org/10.5281/zenodo.18527974")[Reachability Cones as Local Capacity Geometry in NDT]
*A Multi-Dataset Report Across Extreme Neurodynamic Regimes*

== Abstract
Article 8 introduces "reachability cones" as a short-horizon, local capacity geometry derived from locally linear stochastic models in MNPS. The primary objective is to separate "occupancy dispersion" (where the system has been) from "forward availability" (where the system can go in the immediate future). This measurement object provides a more nuanced view of dynamical organization by quantifying the local horizon of admissible state transitions across diverse altered-state and clinical datasets.

== Method
Reachability cones are constructed using a local linear stochastic model: $x_(t+1) = A_t x_t + b_t + epsilon_t$, where innovations satisfy $epsilon_t ~ (0, Q_t)$. The reachability covariance $Sigma_t^{(h)}$ is propagated forward through a recursion $Sigma_t^{(h+1)} = A_t Sigma_t^{(h)} A_t^T + Q_t$. A minimal set of cone metrics is extracted, including:
- *Cone volume (size)*: $1/2 log(det(Sigma))$.
- *Anisotropy/Canalization*: Eigenvalue spread ($kappa$).
- *Effective Dimensionality ($d_"eff"$)*: Participation ratio of available degrees of freedom.
- *Rotation strength*: Skew-symmetric components of local flow.
The framework adopts a multi-dataset reporting contract with subject-aggregated inference, BH-FDR control, and explicit validity diagnostics (e.g., prediction error, split-half stability).

== Results
Reachability geometry reveals strong, FDR-stable separations in regimes with marked dynamical disruption:
- *Epilepsy (ds004100)*: Ictal states show reduced cone size and effective dimensionality combined with increased canalization.
- *Sleep (ds005555)*: NREM3 exhibits a collapse in reachability volume relative to wake, while REM shows contrast-specific reconfiguration of size and rotation.
- *Dementia (ds004504)*: While global MNPS 3D results are near-null, stratified block-cones reveal robust breakdown in the network's ability to diffuse information ($d$-block).
- *fMRI*: Effects are generally smaller and more fragile, consistent with the temporal-resolution boundaries of BOLD imaging.

== Discussion
Reachability cones provide a "capacity-layer" that is partially dissociable from occupancy. They resolve the paradox where some disordered states show high activity or entropy while remaining functionally arrested. By separating "canalization" from "spread," the method offers a clearer view of why consciousness vanishes in "rigid corridors" of activity (like seizures). The manuscript emphasizes transparency by reporting explicit failure modes—such as local linearization failure or innovation heteroskedasticity—as fundamental constraints on the validity domain of the reachability measurement.

#pagebreak()

= Article 9: #link("https://doi.org/10.5281/zenodo.17648437")[Reality from Noise]
*How Your Brain Reconstructs the World through Rhythmic Geometry*

== Abstract
This essay-length synthesis translates the core claims of NDT into a broader conceptual narrative. Its central claim is that conscious experience is not passively received but rhythmically reconstructed from noisy inputs through embodied, oscillatory, and geometric constraints. The text functions as an interpretive bridge between the formal theory papers and a wider scientific or interdisciplinary readership.

== Method
Rather than introducing a new dataset, the essay integrates the existing theory stack into a layered explanatory arc. Part 1 emphasizes embodied anchoring, theta-gamma timing, slow-oscillation/spindle scheduling, and traversability as the operational distinction between mere activity and adaptive conscious dynamics. Part 2 develops the higher-resolution machinery of Stratified MNPS and the Meta-Noetic Jacobian, then uses those tools to interpret psychopathology, development, culture, and long-timescale selfhood as geometry-and-dynamics problems rather than as static trait labels.

== Results
The main output is conceptual compression rather than a new inferential statistic. The essay clarifies how NDT connects rhythmic control, manifold geometry, and adaptive traversal; why similar first-order states can differ mechanistically once stratified coordinates are inspected; and why second-order dynamics are needed to distinguish flexible exploration from rigid or pathological flow. It also foregrounds a practical translational claim: if these geometries can be measured reliably, they offer a route toward richer clinical fingerprints than scalar symptom summaries alone.

== Discussion
`Reality from Noise` serves as the narrative integrator of the project. Its role is not to establish new empirical proof, but to make the theoretical and methodological corpus legible as one coherent research program. In that sense, it is the public-facing synthesis that links formal equations, measurement contracts, and emerging empirical findings into a common reconstructive picture of mind.

#pagebreak()

= Article 10: #link("https://doi.org/10.5281/zenodo.17388941")[The Synthetic Sleep Test]
*A Minimal Viable Experiment for Noetic AI*

== Abstract
This paper asks whether a minimal synthetic system can reproduce one of NDT's most concrete empirical motifs: rhythmically scheduled, sleep-like denoising with geometric state transformations. Rather than treating synthetic consciousness as an all-or-nothing metaphysical verdict, the manuscript frames a narrower architectural test: can an artificial system exhibit the temporal and geometric signatures that NDT treats as foundational to biological reconstruction?

== Method
The proposed experiment centers on an exogenously scheduled synthetic "sleep" cycle in which a model's variance or denoising precision is rhythmically modulated. The key measurements are event-locked entropy reduction, manifold geometry, curvature synchronization, and architecture-native write-free consolidation behavior under repeated cycles. The paper treats the Synthetic Sleep Test as a first-stage falsification protocol, intentionally separated from stronger requirements such as embodiment or full developmental equivalence.

== Results
The manuscript's main result is methodological rather than empirical: it defines a concrete test surface for synthetic noeticity. It clarifies what would count as architectural success, what would count as failure, and which biological properties are being bracketed rather than claimed. In doing so, it turns "AI consciousness" from an abstract debate into a narrower question about whether synthetic systems can reproduce the rhythmic geometric transformations that the theory predicts.

== Discussion
The importance of the paper lies in claim discipline. It does not argue that passing the Synthetic Sleep Test would prove phenomenology, but that failing it would constrain a class of architecture-level consciousness claims. The manuscript therefore gives the NDT program an AI-facing experimental foothold while explicitly distinguishing structural consciousness tests from stronger claims about lived experience.

#pagebreak()

= Article 11: #link("https://doi.org/10.5281/zenodo.17401134")[Cross-Cohort Validation of Noetic Diffusion Theory]
*Event-locked Entropy Dynamics and Sleep Curriculum*

== Abstract
This article presents an early cross-cohort validation of two sleep-facing NDT predictions: event-locked entropy reductions around slow-oscillation/spindle coupling and a broader "sleep curriculum" in which NREM sleep centralizes the manifold while REM re-expands it. The central goal is replication across two sleep cohorts rather than one favorable dataset.

== Method
The analysis uses open sleep EEG data with event detection for slow oscillations and spindles, MNPS feature construction, and within-subject statistical tests supplemented by mixed-effects aggregation, surrogate controls, and multiverse sensitivity checks. The paper explicitly foregrounds methodological repair, including resolution of a prior issue in the `d` component, and frames itself as a first-stage validation of the theory's temporal machinery.

== Results
Across both cohorts, the manuscript reports significant stepwise entropy drops time-locked to SO-spindle events together with stage-dependent manifold reorganization across NREM and REM. The entropy effect is reported as moderate but highly consistent, and the curriculum analysis suggests a systematic contraction/regularization profile across sleep cycles. The combined result is not merely a one-cohort sleep finding, but a replication-oriented argument that the rhythmic denoising logic survives cross-dataset testing.

== Discussion
The paper is important because it shifts NDT from conceptual prediction to replicated sleep-facing evidence. It still remains bounded: the analysis validates temporal and geometric signatures, not the entire theory stack at once. But it establishes a cross-cohort empirical anchor for later measurement-layer and clinical expansions.

#pagebreak()

= Article 12: #link("https://doi.org/10.5281/zenodo.17686202")[Microtubular Key-Lock Geometry]
*Subcellular Realization of Holiarchic Noetic Manifolds*

== Abstract
This manuscript proposes a biological bridge from manifold-level NDT claims to subcellular structure. Its core hypothesis is that microtubular states act as dynamic "keys" that gate dendritic "locks," thereby biasing which dendritic integration states and regional manifold trajectories become physically available. The paper explicitly rejects quantum-coherence dependence and instead frames the mechanism in classical structural, metabolic, and signaling terms.

== Method
The argument is organized as a holiarchic model with nested levels from microtubular configuration to dendritic gating, regional manifolds, and global conscious trajectories. The paper integrates literature on dendritic spikes, microtubule plasticity, Tau/MAP-dependent mechanics, mitochondrial positioning, and classical electrodynamic signaling. These ingredients are then mapped onto NDT objects such as MNPS, regional manifolds, and the metric substrate that would constrain traversable trajectories.

== Results
The main result is a mechanistic proposal rather than a direct experimental demonstration. The manuscript sharpens how one might translate noetic geometry into a physically instantiated gating substrate and clarifies what the hypothesis does and does not claim. It generates concrete falsification hooks around anesthesia, tauopathy, dendritic impedance, metabolic gating, and microtubule-dependent access control.

== Discussion
`Microtubular Key-Lock Geometry` is best read as a biological extension paper. Its value lies in disciplined narrowing: it does not claim that microtubules encode thoughts directly, but that they may participate in the metric and accessibility constraints that shape dendritic and regional manifold dynamics. Within the broader corpus, it opens a subcellular path for grounding the otherwise abstract geometry.

#pagebreak()

= Article 13: #link("https://doi.org/10.5281/zenodo.18943743")[NeuralManifoldDynamics]
*A Versioned Measurement Contract for Low-Dimensional Neural-Manifold Trajectories*

== Abstract
This methods paper defines the ingest-layer measurement contract that operationalizes the NDT program in data analysis. Rather than discovering a new latent space for each contrast, NeuralManifoldDynamics fixes a versioned export system for canonical 3D trajectories, stratified 9D coordinates, Jacobian estimates, and regional derivatives from EEG and fMRI. Its contribution is reproducibility and auditability at the measurement level.

== Method
The paper specifies the chart definition, preprocessing rules, derivative estimation, coverage policy, missing-data handling, regionalization logic, and HDF5 serialization scheme used by the pipeline. The contract distinguishes `mnps_3d`, `coords_9d`, and Jacobian-based dynamical summaries as separate but coordinated objects. It also formalizes how regional EEG and fMRI trajectories are generated under one shared export logic while preserving modality-specific safeguards.

== Results
The main result is infrastructural: the paper turns the theory stack into a replayable measurement system. Relative to earlier MNPS-only versions, it introduces stronger estimator hygiene, clearer 3D/9D separation, deterministic feature transforms, better support diagnostics, and self-describing outputs. In practical terms, this allows later empirical papers to compare datasets under a stable contract rather than under contrast-specific re-fitting.

== Discussion
NeuralManifoldDynamics is the methodological backbone of the later empirical literature. It does not claim diagnostic or consciousness-level inference by itself; instead, it defines what exactly is being measured before any claim is made. That distinction between theory, chart, and measurement contract is one of the strongest clarifications in the mature NDT corpus.

#pagebreak()

= Article 14: #link("https://doi.org/10.5281/zenodo.18943755")[State-Space Reachability and Local Jacobian Dynamics Across Canonical Sleep Stages]
*A bounded sleep-stage test of local dynamical structure*

== Abstract
This paper tests whether local reachability and local Jacobian magnitude remain informative once sleep-stage effects are compared against explicit null controls and conventional EEG baselines. The central result is that reachability separates `Wake`, `REM`, and `N2` from `N3` more strongly and more consistently than local Jacobian magnitude in ANPHY sleep EEG.

== Method
The manuscript analyzes stage-aware ANPHY summaries under a fixed measurement contract, using one primary reachability endpoint (`tube_log_det_median`) and one secondary Jacobian endpoint (`frobenius_norm_median`). It adds negative controls, a compact conventional comparator family, a ceiling-aware incremental-validity check, and a small sensitivity suite that includes both within-surface summary variations and one outside-surface estimator perturbation.

== Results
Reachability remains large and directionally stable across all three planned contrasts against `N3`, while Jacobian magnitude is weaker and more selective. Conventional spectral and complexity summaries also distinguish stages strongly, but they do not reconstruct the subject-level reachability contrasts especially well. The paper's most important reviewer-facing result is therefore bounded nonredundancy rather than additive classifier gain.

== Discussion
The manuscript sharpens a key principle in the NDT line of work: a geometric summary does not become useful merely because it separates familiar conditions. It becomes useful if it survives skeptical checks, null controls, and comparison to simpler baselines. In that sense, the paper is less about "sleep proves consciousness theory" and more about how to stress-test a dynamical measurement in a regime where conventional EEG already works well.

#pagebreak()

= Article 15: #link("https://doi.org/10.5281/zenodo.19384063")[Reduced Dynamical Capacity Does Not Imply Unconsciousness]
*Sleep, Propofol, and Epilepsy Dissociate in Transport Capture and Pathological Deformation*

== Abstract
This comparative paper asks whether low local dynamical capacity can serve as a generic unconsciousness marker. Its answer is no: sleep, propofol sedation, and epilepsy can all show reduced capacity, but they dissociate once transport-innovation balance and pathological lock-in are measured explicitly. The manuscript therefore replaces a one-dimensional unconsciousness scalar with a multi-axis typology of reduced-capacity regimes.

== Method
The study analyzes three datasets under a common framework: ANPHY sleep EEG, propofol EEG, and epilepsy iEEG. It decomposes the problem into three partially independent layers: capacity collapse, transport-innovation balance, and pathological lock-in. These layers are quantified using traversability, reachability, Jacobian, and block-Jacobian summaries, then tested both as descriptive contrasts and as incremental-validity candidates beyond classical spectral features.

== Results
Capacity collapse appears across all three regime families, but the other layers dissociate them. Deep sleep shows low capacity while remaining relatively innovation-dominated; propofol produces a clearer capacity shift but weaker evidence for pathological capture at the analyzed depth; epilepsy shows the strongest joint signature of collapse, transport capture, and lock-in, together with substantial incremental validity beyond spectral baselines. The important result is therefore not "which state is most unconscious," but that different low-capacity regimes occupy different positions in geometric phenotype space.

== Discussion
This paper is one of the clearest examples of mature claim discipline in the project. It explicitly rejects overinterpretation of any single summary and reframes low-capacity states as a family that must be dissociated mechanistically. That move substantially improves the clinical and conceptual precision of the broader NDT program.

#pagebreak()

= Article 16: #link("https://doi.org/10.5281/zenodo.20038829")[Sleep-Spindle-Rich Windows Are Associated With Local Meta-Noetic Phase-Space Shifts in N2 Sleep]
*An event-locked measurement-layer analysis of spindle-associated reconfiguration*

== Abstract
This paper moves from stage-level sleep contrasts to event-level analysis by asking whether spindle-rich N2 windows differ from matched non-spindle N2 windows in local state-space geometry. The manuscript treats spindles not as direct proof of memory writing, but as time-localized physiological events that may carry reproducible MNPS, stratified, reachability, or Jacobian signatures.

== Method
Using ds005555 processed under the NeuralManifoldDynamics contract, the study performs event-locked comparisons around detector-defined N2 spindles, baseline-corrected subject summaries, matched-control windows, label permutations, time-shifted pseudo-events, and detector-source sensitivity analyses. The promoted endpoint is spindle-locked MNPS deviation, supplemented by Stratified 9D and MNJ summaries as well as a modest incremental-validity check against spectral power.

== Results
The strongest and most reproducible spindle effect is a positive event-locked shift in MNPS deviation relative both to pre-event baseline and to matched non-spindle N2 controls. Stratified 9D results show that the change is not confined to one 3D composite and is strongest in deviation-family and entropy-memory-family coordinates. Jacobian changes are present but weaker, and geometry adds only modest incremental discrimination on top of already-strong spectral power. The retained interpretation is therefore a local measurement-layer reconfiguration claim rather than a full mechanistic theory of spindle function.

== Discussion
The manuscript sharpens the spindle story in two useful ways. First, it relocates the question from broad sleep-stage differences to tightly matched within-stage events. Second, it demonstrates how bounded interpretation can be preserved even when an effect is strong: spindle windows look geometrically different, but the paper explicitly stops short of claiming that this alone proves memory consolidation or a specific structural-write mechanism.

#pagebreak()

= Article 17: #link("https://doi.org/10.5281/zenodo.19391708")[A Cytoskeletal-Dendritic Accessibility Model of Associative Memory]
*A branch-resolved bridge from biological memory theory to executable and open-data tests*

== Abstract
This paper develops a narrower biological memory theory in which associative recall depends not only on synaptic weights but also on a slower, branch-level accessibility structure distributed across dendrites and spines. The claim is deliberately restrained: structural accessibility is presented as a biologically motivated, executable, and empirically contactable hypothesis, not as a uniquely established molecular memory code.

== Method
The manuscript works across three linked levels. First, it synthesizes active dendrites, spine compartmentalization, tagging/capture, local translation, replay, and cytoskeletal dynamics into a slow-accessibility hypothesis. Second, it instantiates that logic in a minimal branch-resolved simulator with replay-dependent structural writing and perturbation tests. Third, it confronts the model with several open datasets chosen as downstream signature tests rather than as direct microscopic validation.

== Results
In simulation, branch-specific structural writing, replay-dependent consolidation, and damage/rescue asymmetries survive stronger comparator and ablation tests than simpler alternatives. In open data, the paper finds modest but structured signature support across three dataset families, including replay-adjacent enrichment, inter-plane dendritic coupling, and weaker cross-day stability under perturbation. The combined result is not proof of a hidden structural code, but evidence that the accessibility hypothesis survives initial executable and empirical sharpening.

== Discussion
This is one of the most biologically ambitious papers in the corpus, but also one of the most careful about claim boundaries. Its contribution is to connect dendritic physiology, cytoskeletal plasticity, and memory linking to a formal and testable accessibility layer. In the larger NDT ecosystem, it also provides a plausible substrate-level complement to the more abstract geometric and dynamical articles.

#pagebreak()

= Article 18: #link("https://doi.org/10.5281/zenodo.20410200")[Resting-State Neural Geometry Across Depressive Symptom Burden]
*A compact NeuralManifoldDynamics 2.1 report for ds003478*

== Abstract
This compact clinical report asks where depressive symptom burden is most visible in a fixed NeuralManifoldDynamics 2.1 export from resting-state EEG. Using Beck Depression Inventory (BDI) score as the primary axis in OpenNeuro `ds003478`, the manuscript shows that the clearest low-versus-high symptom separation does not live in coarse 3D MNPS summaries. Instead, it concentrates in reachability tubes, 9D Meta-Noetic Jacobian (MNJ) rotation, and distribution summaries tied to the entropy-memory subfamily. The dominant organization is a low-to-elevated symptom regime contrast rather than a clean monotonic gradient within the high-BDI range alone.

== Method
The study analyzes `121` young adults with usable BDI scores under a predefined low-versus-high contrast (`BDI 0-13` vs `BDI 20-63`), supplemented by continuous BDI correlations and exploratory clinical bands (`0-13`, `14-19`, `20-63`). Each recording is processed through the full paper-facing export surface: global 3D and 9D MNPS, 3D and 9D MNJ, block-MNJ, reachability cones, tier2 summaries, and distribution metrics. Inference uses exported effect sizes with BH-FDR control within the selected metric families. The paper is explicitly bounded: it is not framed as a diagnostic major-depression biomarker study, but as an auditable geometry report in one cohort with uneven symptom-band counts.

== Results
On the coarse 3D map, low-versus-high BDI separation is modest. The stronger picture appears one layer deeper:
- *Reachability:* `tube_log_eig_var_mean` and related tube-volume summaries show the clearest corrected effects (e.g. `d approx -0.68` to `0.74`, `q < 0.003`), implying a altered local neighborhood of next states rather than uniform capacity loss.
- *9D MNJ:* `rotational_power_mean` rises with symptom burden (`d = 0.569`, `q = 0.003`), consistent with more loop-like local dynamics.
- *Stratified coordinates:* displacement is channel-specific, especially in `e_m` and `m_o`, rather than a uniform flattening of the whole manifold.
Continuous BDI analyses preserve the same ordering (reachability and 9D MNJ outperform 3D), while `BDI 0-13` vs `14-19` shows especially strong reachability and distribution effects and `14-19` vs `20-63` is comparatively weak—supporting a regime contrast more than a smooth severity slope across the full range.

== Discussion
The report sharpens the geometric-psychiatry reading of depression: the phenomenology of being "stuck" may correspond less to global shutdown than to warped reachability and recirculating local dynamics. Because the cohort is young, resting-state, and BDI-anchored rather than diagnostically confirmed, the findings should travel only as bounded internal evidence. Still, the paper is an important bridge from the multi-dataset stress-tests to a dedicated symptom-burden manuscript with an explicit export contract and claim discipline.

#pagebreak()

= Article 19: #link("https://doi.org/10.5281/zenodo.20410572")[First-Episode Psychosis Geometry Across Two Resting-State EEG Cohorts]
*NeuralManifoldDynamics 2.1 analysis of ds003944 and ds003947*

== Abstract
This manuscript tests whether first-episode psychosis (FEP) can be organized in a shared cross-subject neural state space when medication status is treated as a primary stratifier. Two OpenNeuro resting-state EEG cohorts (`ds003944`, `ds003947`) are compared as `Healthy`, `FEP unmedicated`, and `FEP medicated` (`CPZ_at_scan` rule). Psychosis-related separation is real in the shared frame, but the signal-bearing layer shifts with cohort: in `ds003944` the strongest corrected effects are stable `m`-family displacements in medicated FEP versus healthy controls; in `ds003947` the strongest corrected effect is reduced trajectory drift in unmedicated FEP. The paper argues for a reproducible analysis surface rather than a single universal FEP biomarker.

== Method
NeuralManifoldDynamics 2.1 maps each recording to 3D MNPS trajectories, stratified 9D coordinates, local Jacobians, block-MNJ summaries, and reachability sensitivity exports. Contrasts are run per dataset for unmedicated vs healthy, medicated vs healthy, and medicated vs unmedicated, with BH-FDR applied within each contrast and analysis family. A pooled `Healthy vs FEP` sensitivity analysis and compact spectral/speed baselines test whether generic EEG summaries recover the main dynamic findings. Endpoint hierarchy treats first-order and stratified MNPS as primary, Jacobian layers as secondary, and reachability as appendix-level sensitivity because that block was refreshed after the first pooled pass.

== Results
In `ds003944` (`32` healthy, `19` unmedicated, `31` medicated), medicated FEP vs healthy shows robust global and stratified `m`-family shifts (e.g. `m_mean`, `d = 0.881`, `q = 0.016`; `m_o_mean`, `d = 0.814`, `q = 0.027`). In `ds003947` (`30` healthy, `8` unmedicated, `23` medicated), the standout corrected effect is dynamic: unmedicated FEP vs healthy shows reduced `m_delta_mean_median` (`d = -1.385`, `q = 0.040`). Pooled sensitivity preserves a stable psychosis signal in `ds003944` but weakens the `ds003947` dynamic contrast, supporting medication-aware interpretation. Some separation is also visible in simple spectral summaries, but generic speed/curvature baselines do not recover the main dynamic result. Reachability shifts appear as a secondary, cohort-sensitive layer rather than one settled signature.

== Discussion
Psychosis, in this framing, is less a single geometric inverse of depression's "locked valley" than a family of fragmented, medication-sensitive distortions. The small `ds003947` unmedicated subgroup (`n = 8`) means the dynamic finding should be treated as cohort-local until replicated. The paper's main contribution is methodological and interpretive: it shows how a fixed shared-reference map can expose where FEP signal lives—sometimes in static `m`-family displacement, sometimes in trajectory instability—without collapsing those layers into one headline metric. That caution is essential for both clinical translation and integration into broader essays on geometric psychiatry.

#pagebreak()

= Article 20: #link("https://doi.org/10.5281/zenodo.20410486")[Recovery-Linked Neural Geometry After Cardiac-Arrest Coma]
*Discovery-selected reachability geometry with verification in I-CARE*

== Abstract
This clinical study tests whether early EEG after cardiac arrest carries recovery-linked geometric information beyond conventional severity readouts. In the multicenter I-CARE cohort, analysed through NeuralManifoldDynamics with a three-layer design—locked discovery (`part1`, `141` extreme-outcome patients), non-overlapping verification (`part2`, `140` patients), and audited pooled synthesis (`281` patients)—later good recovery (CPC `1`) versus poor outcome (CPC `5`) is most clearly associated with broader effective reachable dimensionality in the first `12 h` after EEG monitoring start. Persistence and capture-related reachability summaries remain directionally consistent but are weaker and less stable than the dimensionality contrast. The geometry layer improves internal prediction beyond a restricted clinical+qEEG comparator, but the manuscript does not claim bedside readiness or a direct consciousness meter.

== Method
The primary contrast is patient-level CPC `1` vs CPC `5` within the first `12 h` after EEG-anchor. A five-metric reachability family—emphasizing `tube_d_eff_median`, persistence summaries, and capture/operator norms—was ranked exploratorily in the locked discovery bundle and then carried forward without re-ranking into verification and pooled analyses. Verification tests directional replication only; pooled predictive modelling is treated as synthesis rather than external validation. Feature selection for the predictive layer was frozen from discovery before merged-cohort reruns. WLST and time-of-death metadata were unavailable in the manuscript-facing bundle, so `CPC 5` is interpreted as recovery-associated geometry rather than pure neural viability.

== Results
In independent verification, all five discovery-selected metrics retain the same directional pattern; the largest standardized effects remain effective dimensionality (`tube_d_eff_median`, `d = 0.703`) and operator-norm capture (`tube_a_operator_norm_median`, `d = -0.713`), with smaller persistence effects. In the pooled synthesis, the signal is more conservative: `tube_d_eff_median` remains clearest (`2.217` vs `2.009`, `d = 0.513`), while persistence stays weakly positive and operator/capture summaries attenuate. Adding geometry to a restricted structured clinical+qEEG comparator improves repeated cross-validation `AUROC` from `0.583` to `0.672`, `AUPRC` from `0.572` to `0.653`, and Brier score from `0.260` to `0.237`; leave-one-site-out `AUROC` rises from `0.571` to `0.612`. These are complementarity results, not replacement claims for standard neuroprognostic practice.

== Discussion
Cardiac-arrest coma is the natural ICU bridge between experimental arrest states (propofol, seizure) and translational NDT. The clinically relevant question is not only whether the EEG looks suppressed or disorganized, but whether short-horizon dynamics still admit multiple independent futures. The study supports a bounded capacity-geometry claim: better later outcome tends to co-occur with broader local reachability, especially in effective dimensionality, while occupancy alone can mislead. Because withdrawal-of-care pathways cannot be fully partitioned in the current export, and because discovery-side metric ranking introduces optimism, prospective external validation remains necessary. Within the corpus, this paper moves reachability from phenomenological metaphor toward recovery-linked, auditable early EEG structure—without equating geometry with consciousness or prognosis by itself.
#pagebreak()

= Article 21: #link("https://doi.org/10.5281/zenodo.21006812")[Cardiac Autonomic State and Neural Manifold Geometry]
*Co-vary Non-Monotonically Across Working-Memory Task Phases*

== Abstract
This article provides the first measurement-layer empirical test of the Embodied Anchoring Principle (EAP) from Noetic Diffusion Theory. Using ds003838 (N = 65 healthy adults with simultaneous EEG, ECG, PPG, and pupillometry during rest and a five-stage digit-span working-memory task), the paper asks whether HRV-derived autonomic proxies co-vary systematically with neural manifold geometry across task phase. Both the autonomic anchor surface and MNPS geometry are strongly task-modulated with convergent non-monotone profiles -- but direct within-subject anchor-MNPS coupling is modest and between-subject correlations are null after FDR correction.

== Method
HRV-derived anchor proxies (vagal_index, sympathetic_index, vascular_index, composite anchor_index) were exported alongside MNPS coordinates and local Jacobian summaries via NeuralManifoldDynamics. Statistical inference used 36 pre-specified paired contrasts with BH-FDR correction, supplemented by within-subject coupling analyses and leave-one-out controls.

== Results
Autonomic state and manifold geometry both varied strongly with task phase (Friedman chi^2(4) = 88.04, p < 1e-18 for vagal_index; 24/36 pre-specified contrasts survived FDR). The listen-vs-memorization contrast for vagal_index yielded Cohen's d = 2.085. Trajectory efficiency ranged from 0.04 at rest to 0.98 during five-digit memorization (24-fold difference). Both curves are non-monotone with a systematic stage offset: the autonomic proxy peaks during passive listening while manifold trajectory efficiency peaks during the easiest active memory condition (mem5).

== Discussion
EAP receives qualified support: autonomic state and neural geometry are task-co-modulated parallels, not a demonstrated causal gating relationship in this observational design. The paper is the first to operationalize the EAP anchor surface inside the NeuralManifoldDynamics pipeline, and provides groundwork for future trial-aligned HRV-MNPS coupling studies.
#pagebreak()

= Article 22: #link("https://doi.org/10.5281/zenodo.21034528")[Rapid Item-Updating Elevates Neural Manifold Dynamics During Encoding]
*Evidence from a Fixed-Load Verbal Working-Memory Dataset*

== Abstract
This article extends EAP validation to ds006848 (N = 30), where memory load is held constant (seven digits) while presentation mode varies: simultaneous, fast sequential, fast-with-delay, and slow sequential. Rapid item-updating conditions elevate manifold mobility (m) and diffusivity (d) during encoding, while simultaneous presentation yields the highest recall accuracy -- a behavioral dissociation showing that m/d reflects encoding demand rather than encoding success.

== Method
NeuralManifoldDynamics was applied to ds006848 EEG-ECG-PPG recordings with direct BIDS event-locking and corrected ECG polarity (92.9% of epochs had inverted QRS). Friedman tests across four presentation conditions were run separately for encoding, maintenance, and retrieval phases. Purity filters and leave-one-out subject removal (30/30 runs) were applied.

== Results
Rapid sequential modes (Fast and FastDelay) produced significantly higher m and d during encoding (Friedman chi^2(m) = 17.12, p = 0.00067; chi^2(d) = 20.12, p = 0.00016; 7 BH-FDR-significant pairwise contrasts). The behavioral ordering was inverted: Fast had the lowest recall accuracy (median 4/7) while Simultaneous had the highest (7/7; Friedman p = 1.2e-8). A complementary null was confirmed: the four modes produced indistinguishable geometry during maintenance (Friedman m: p = 0.96). Event-locked analysis confirmed a steep encoding-to-maintenance m-drop for the Fast condition.

== Discussion
The result adds a second validation axis (presentation tempo rather than memory load) to MNPS sensitivity. The encoding-specific effect -- with no carry-forward into maintenance -- supports the interpretation that m/d reflects online state-reconfiguration demands rather than storage success. Simultaneous presentation achieves equivalent memory storage with lower manifold excursion.
#pagebreak()

= Article 23: #link("https://doi.org/10.5281/zenodo.20597114")[Shared-Reference Disease-State Geometry Exceeds Paired Pharmacology Effects in Parkinson ON/OFF Auditory Oddball EEG]
*A Mixed-Contract NeuralManifoldDynamics Analysis of ds003490*

== Abstract
This article separates two distinct inference problems in Parkinson ON/OFF EEG that require different coordinate frames: disease-state structure (between-subject, best evaluated in cohort-anchored coordinates) and medication response (within-subject, best evaluated in subject-anchored coordinates). Using a mixed-contract NeuralManifoldDynamics rerun of ds003490 (75 runs: 25 Controls, 25 Parkinson OFF, 25 Parkinson ON), disease-state geometry proves broader and more stable than the paired pharmacology signal.

== Method
Cohort-anchored coordinates were used for Control vs Parkinson OFF and Control vs Parkinson ON; subject-anchored coordinates were used for the paired Parkinson OFF vs ON comparison. An article-local event-locked trajectory layer was added using exact H5 event_windows indices for standard/novel/target tone segmentation. Main-text threshold: BH-FDR q < 0.05.

== Results
At q < 0.05, 47 rows survived: 35 standard rows, 12 event-locked trajectory rows. Control vs Parkinson OFF was characterized by lower cohort-anchor 9D dispersion and lower eyes-closed trajectory speed (frontal d_n_std: d = -1.268, q = 0.018; global speed_median: d = -1.212, q = 0.0025). Control vs Parkinson ON was led by elevated global 9D Jacobian mdr_median (d = 1.167, q = 0.0095) and novel-tone trajectory asymmetry. The paired medication comparison retained only one subject-anchor row. Medication changed some exported dynamics but did not collapse the Parkinson state onto controls.

== Discussion
The key contribution is methodological: conflating disease-state and pharmacology inference into one coordinate frame suppresses the most informative signal. Within this dataset, disease-state geometry is internally stable and broad while the paired medication effect is narrow and hypothesis-generating. The paper is best read as a disease-state geometry report with a modest pharmacological branch, not a dopaminergic normalization story.
#pagebreak()

= Article 24: #link("https://doi.org/10.5281/zenodo.20593874")[Evoked Neural Geometry Under Photic Stress in Alzheimer Disease and Frontotemporal Dementia]
*A Frequency-Resolved EEG Study with Resting-State Reference*

== Abstract
This compact empirical report applies NeuralManifoldDynamics to the ds006036 photic-stimulation EEG cohort (29 Healthy, 36 AD, 23 FTD) at four stimulation frequencies (5/10/15/20 Hz) to test whether external rhythmic visual driving reveals group separation in MNJ metrics not visible at rest. The central finding is a narrow but corrected AD-versus-Healthy signal on global 9D MNJ mdr_median under photic driving, strongest at 20 Hz, while the matched resting-state baseline on the same surface is near null.

== Method
A canonical exact-block/native-block rerun was anchored at the ds006036 neuralmanifolddynamics export from 2026-06-04 (1757 selected windows across 397 block instances). Group contrasts and MMSE severity correlations were tested with BH-FDR. A paired ds004504 resting-state reference was extracted on the same MNJ surface for explicit baseline comparison.

== Results
All corrected group rows localized to AD vs Healthy global 9D MNJ mdr_median: strongest at PHOTO 20 Hz (d = -0.984, q = 0.0034), with additional corrected rows at 10 and 15 Hz. No corrected FTD vs Healthy or AD vs FTD group contrast survived FDR. The resting-state reference showed near-null AD vs Healthy on the same surface (d = -0.080, q = 0.909), confirming photic specificity. MMSE structure was broader: 8 corrected severity rows, led by pooled-dementia PHOTO 20 Hz global 9D MNJ rotational_power_median (rho = -0.470, q = 0.0020).

== Discussion
The evoked approach reveals MNJ sensitivity to AD that is absent at baseline, suggesting that perturbational driving unmasks dynamical brittleness not detectable from spontaneous activity alone. The signal is narrow and AD-specific at the group level in this analysis. The result motivates the follow-up Evoked Structural Brittleness study (Article 25), which introduces an explicit deviation score with broader sensitivity to both AD and FTD.
#pagebreak()

= Article 25: #link("https://doi.org/10.5281/zenodo.20593954")[Evoked Structural Brittleness Under Photic Stimulation in Alzheimer Disease and Frontotemporal Dementia]
*A ds004504-Anchored Photic EEG Follow-up Study*

== Abstract
Building on Article 24, this follow-up introduces Evoked Structural Brittleness (ESB-2) -- a subject-level perturbational deviation score measuring how far an individual's rest-to-photic response vector deviates from the Healthy evoked template. ESB-2 combines posterior-occipital reachability capacity (tube_d_eff_median) with global dynamical guidance (rotational_power_median) after ds004504 baseline subtraction.

== Method
ESB-2 was computed as a standardized distance from the healthy response template in a two-axis capacity-guidance space. Subject-matched ds004504 resting baselines were subtracted before scoring. Cross-fitted healthy rescoring, leave-one-out, permutation, and recovery-subset QC were applied. The secondary Photic Resonance Loss (PRL) score was evaluated but is not treated as a co-equal result.

== Results
The strongest disease-versus-healthy separation localized to PHOTO 15 Hz: AD vs Healthy d = 0.821, q = 0.00626; FTD vs Healthy d = 1.038, q = 0.00269. Cross-fitted healthy rescoring preserved the 15 Hz effect (AD: d = 0.676; FTD: d = 0.841). Axis decomposition showed the deviation was mainly posterior-capacity-led, with corrected capacity rows at PHOTO 5/10/15 Hz for AD. A conventional comparator panel showed partial overlap with alpha-linked power change, but its direct association with ESB-2 remained weak and non-corrected. The secondary PRL test remained negative.

== Discussion
ESB-2 is the first explicit perturbational deviation score in the NDT clinical corpus. Unlike Article 24, which found no FTD signal at the group MNJ level, ESB-2 detects both AD and FTD at 15 Hz, suggesting that deviation-from-template framing is more sensitive than single-endpoint group testing for FTD. The bounded conclusion is that ESB-2 is an internally stabilized disease-versus-healthy perturbational score on this cohort, not an externally validated biomarker. The paper is a proof-of-concept for perturbation-based clinical NDT.
#pagebreak()

= Article 26: #link("https://doi.org/10.5281/zenodo.20446681")[SPIRAL Cortex]
*A Policy-First Noetic Memory Architecture for Controlled Retrieval and Auditable Recall*

== Abstract
SPIRAL Cortex is a policy-first memory architecture designed to study when structured external memory causally improves an existing agent policy under ambiguity. Rather than proposing a new model backbone, the paper isolates the memory contribution by using selected SWE-bench protocol-gap cases, separates semantic same-subsystem memory from generic retrieval and wrong-context controls, and frames the resulting traces as a future bridge to NDT-style trajectory diagnostics.

== Method
SWE-bench cases were selected where an agent policy fails due to a local context gap rather than a reasoning limitation. Memory is categorized as semantic same-subsystem (nearest past solution in the same component), generic retrieval (top-k embedding), or wrong-context (other component). Causal contribution is assessed by comparing agent outcomes across memory-present, lesioned-memory, and wrong-memory conditions.

== Results
Semantic same-subsystem memory produced the strongest policy improvement in the selected protocol-gap cases. Generic retrieval showed attenuated benefit, and wrong-context memory sometimes degraded performance. The separation between memory conditions provides an initial causal trace linking memory type and policy behavior.

== Discussion
SPIRAL Cortex represents the NDT program's first explicit AI-facing memory architecture paper. Its significance is twofold: (1) it operationalizes structured memory access as a causal variable rather than a retrieval augmentation, and (2) it proposes linking retrieval trace geometry to NDT-style manifold trajectory diagnostics, creating a bridge between biological NDT and AI memory architecture. The paper is an early-stage working paper; causal claims are bounded to the selected SWE-bench cases.
#pagebreak()

= Article 27: #link("https://doi.org/10.5281/zenodo.20813821")[Slow Branch-Level Accessibility as a Structural Constraint on Memory Linking]
*A Simulator-First Evaluation of Branch-Resolved Memory Architecture*

== Abstract
This article develops and tests the slow branch-level accessibility hypothesis: that associative recall is constrained not only by synaptic weights but also by a slow structural variable distributed across dendritic branches that gates which memories can be linked during replay-dependent consolidation. Using a simulator-first framework, the paper validates branch-resolved structural writing, perturbation-sensitive loss, and targeted rescue across scaled topologies against nine comparator classes.

== Method
The framework operates at three linked levels: a slow branch-level accessibility variable governing which dendritic branches are structurally available during consolidation, a minimal branch-resolved simulator with replay-dependent structural writing and perturbation tests, and downstream signature tests against open datasets. Nine alternative comparator classes are evaluated in ablation.

== Results
Branch-specific structural writing, replay-dependent consolidation, and damage/rescue asymmetries survive stronger comparator and ablation tests than simpler alternatives. Open-data signature support is modest but structured across three dataset families, including replay-adjacent enrichment, inter-plane dendritic coupling, and cross-day stability under perturbation.

== Discussion
This article is a significant update to the earlier Cytoskeletal-Dendritic Accessibility Model (Article 17), with stronger ablation design, expanded simulator validation, and clearer claim boundaries. In the NDT corpus it occupies the substrate level: it does not claim that branches encode conscious content, but that structural accessibility may co-determine which recall pathways are open -- a biological complement to the abstract reachability geometry in the formal NDT measurement layer.
#pagebreak()

= Article 28: #link("https://doi.org/10.5281/zenodo.20033884")[Adaptive Capacity, Transport Capture, and Structural Accessibility]
*A Multi-Scale Evaluation of Noetic Diffusion Theory*

== Abstract
This integrative article evaluates NDT as a multi-scale, measurement-facing framework for consciousness research, arguing that conscious-level interpretation should not rely on any single summary (entropy, occupancy, or capacity) but on a three-layer regime geometry: capacity collapse (C), transport-innovation balance (TI), and pathological lock-in (P). Evidence from sleep, propofol, and epilepsy is integrated with MNPS, MNJ, reachability, NeuralManifoldDynamics, and a speculative cytoskeletal-dendritic accessibility bridge.

== Method
The paper synthesizes results from sleep (ANPHY, ds005555), propofol (ds005620, ds003171), and epilepsy (ds004100) datasets under one C/TI/P regime typology. Each regime is characterized on three partially independent layers: capacity collapse, transport-innovation balance, and pathological lock-in. The contribution of each layer to discriminating between regime types is evaluated both descriptively and as an incremental-validity candidate.

== Results
Capacity collapse appears across all three regime families, but TI balance and pathological lock-in dissociate them. Deep sleep shows low capacity while remaining relatively innovation-dominated. Propofol produces a clearer capacity shift with weaker pathological capture. Epilepsy shows the strongest joint signature: collapse, transport capture, and lock-in together with substantial incremental validity beyond spectral baselines. The C/TI/P typology positions each low-capacity state in a distinct region of geometric phenotype space rather than on a single unconsciousness axis.

== Discussion
This article functions as the theoretical integrator for the multi-dataset stress-test series (Articles 7, 8, 14, 15). Its contribution is framing C/TI/P as the correct analytical granularity for consciousness research: not "is capacity low?" but "which combination of capacity, transport balance, and lock-in is present?" The speculative cytoskeletal bridge connects the abstract measurement layer to the biological substrate papers (Articles 12, 17, 27), completing a multi-scale arc from molecular accessibility to manifold geometry to regime typology.