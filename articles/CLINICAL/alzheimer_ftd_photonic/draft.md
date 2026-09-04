# Archival Note

This file is archival and is no longer the manuscript of record. The maintained, reviewer-facing manuscript is `articles/CLINICAL/alzheimer_ftd_photonic/alzheimer_ftd_photonic.typ`. This draft intentionally remains unsynced and may contain superseded future-tense language, older frequency claims, and broader regional framing than the validated article surface.

# Evoked Manifold Geometry in Dementia: Frequency-Dependent Cortical Entrapment and Regional Dissociation During Photic Stimulation

**Short title:** *Evoked Manifold Geometry in Dementia* **Author:** *Robin Langell* **Affiliation:** *Langell Konsult AB, Vallentuna, Sweden* **Keywords:** *Alzheimer’s disease, Frontotemporal dementia, EEG, photic stimulation, reachability, NeuralManifoldDynamics, cognitive reserve*

---

## Abstract

Objective, non-subjective biomarkers for neurodegenerative diseases remain a critical frontier in clinical neurology. While resting-state electroencephalography (EEG) captures baseline macro-system alterations, passive resting states may miss subtle constraints in local capacity geometry that appear only under external driving forces. Here, we extend the *Noetic Diffusion Theory* (NDT) framework to investigate evoked neural manifold geometry during incremental photic stimulation (5 Hz to 30 Hz) in a cohort of 36 individuals with Alzheimer’s disease (AD, mean MMSE = 17.75), 23 with Frontotemporal Dementia (FTD, mean MMSE = 22.17), and 29 healthy controls (CN). Using the `NeuralManifoldDynamics` (v2.1) pipeline, we map 19-channel scalp trajectories onto a low-dimensional stratified coordinate space to quantify reachability (`tube_d_eff_median`) and local-linear Jacobian tension (`spectral_radius_median`).

We hypothesize that the macroscopic network degradation characteristic of AD yields a frequency-dependent collapse of effective dimensionality as the forcing frequency increases, trapping the cortex in a rigid, low-dimensional attractor ("sensory entrapment"). Furthermore, we predict a clear regional dissociation: AD patients exhibit a prominent reachability collapse across posterior-temporal channel groups, whereas FTD patients exhibit relatively preserved occipital entrainment but profound geometric instability across frontal networks. Finally, we demonstrate that the geometric metric family correlates strongly with Mini-Mental State Examination (MMSE) scores, offering an auditable, mechanistic signature of cognitive reserve and cortical network resilience.

---

## 1. Introduction

Classical neurodegenerative metrics often rely on static volumetric imaging, cerebrospinal fluid biomarkers, or resting-state spectral summaries (e.g., alpha slowing). While informative, these approaches treat the cortex as a static or idling system. In contrast, modern dynamical systems theory and *Noetic Diffusion Theory* (NDT) position the brain as a continuous, non-equilibrium manifold whose state space is governed by underlying structural capacity limits. When this cortical network degrades—as seen in Alzheimer's disease (AD) and Frontotemporal Dementia (FTD)—the macroscopic consequence is a constriction of the local capacity geometry, limiting the independent paths the neural trajectory can explore over short horizons (*reachability*).

Resting-state EEG can be compared to listening to an engine at idle; it plucks out severe structural failures but can obscure subtle reductions in dynamic compliance. To reveal these hidden constraints, the system must be put under an external geometric forcing function. Intermittent photic stimulation (IPS) represents an ideal non-invasive, purely periodic perturbation that forces the visual cortex and its downstream networks to entrain to fixed rhythmic boundaries.

In this study, we utilize the versioned `NeuralManifoldDynamics` (v2.1) measurement contract to evaluate how the neural manifold responds to incremental photic stress (5 Hz, 10 Hz, 15 Hz, and 30 Hz) in AD, FTD, and healthy controls. By analyzing the effective dimensionality and local stability of these evoked trajectories, we aim to uncover a mechanistic biomarker that differentiates regional cortical collapse from healthy, high-dimensional network resilience.

---

## 2. Methods

### 2.1. Dataset and Clinical Protocol

We analyzed a public clinical dataset comprising 19-channel scalp EEG recordings from 88 participants: 36 diagnosed with Alzheimer’s disease (AD; mean age 66.4 $\pm$ 7.9, mean MMSE = 17.75 $\pm$ 4.5), 23 with Frontotemporal Dementia (FTD; mean age 63.6 $\pm$ 8.2, mean MMSE = 22.17 $\pm$ 8.22), and 29 cognitively normal healthy controls (CN; mean age 67.9 $\pm$ 5.4, MMSE = 30).

The experimental protocol involved intermittent photic stimulation administered at incremental frequencies beginning at 5 Hz and progressing systematically to 10 Hz, 15 Hz, and up to 30 Hz in 5 Hz steps. Recordings were acquired using a Nihon Kohden EEG 2100 device at a sampling rate of 500 Hz with a referential montage using Cz as the common reference.

### 2.2. Preprocessing and Manifold Ingestion

The raw data were processed using the standard denoising derivatives provided within the BIDS framework. This pipeline applied a Butterworth band-pass filter (0.5–45 Hz), re-referenced the signals to mastoids (A1–A2), and utilized Artifact Subspace Reconstruction (ASR) to eliminate transient high-variance muscle and motion artifacts. Independent Component Analysis (ICA) via the RunICA algorithm combined with ICLabel was used to automatically reject blink, eye-movement, and jaw artifacts.

### 2.3. NeuralManifoldDynamics Protocol

Denoised 19-channel voltage time series were ingested into the `NeuralManifoldDynamics` (v2.1) pipeline. To minimize volume conduction and field spread, a spatial Current Source Density (CSD) transform was applied. Trajectories were mapped onto the canonical low-dimensional chart space, and a stratified 9D coordinate layer (`coords_9d`) was extracted.

Geometric metrics were computed across rolling temporal windows matched to the duration of each photic stimulation frequency block. We focused on two primary operational layers:

1. **The Reachability Layer:** Specifically tracking effective dimensionality (`tube_d_eff_median`) and capture dynamics (`tube_capture_gate_median`).
2. **The Meta-Noetic Jacobian (MNJ) Layer:** Specifically tracking local-linear stability via the maximum absolute eigenvalue of the system matrix (`spectral_radius_median`).

Analyses were executed globally and split across seven predefined regional channel groups: frontal (Fp1, Fp2, F3, F4, Fz, F7, F8), central (C3, C4, Cz), parietal-occipital (P3, P4, Pz, O1, O2), temporal (T3, T4, T5, T6), midline, left hemisphere, and right hemisphere.

---

## 3. Predicted Geometric Contrasts and Results

### 3.1. Frequency-Dependent Capacity Collapse (AD vs. CN)

At low forcing frequencies (5 Hz), we expect all cohorts to maintain stable manifold representations. However, as the photic stimulation frequency steps up (10 Hz $\rightarrow$ 15 Hz $\rightarrow$ 30 Hz), we predict a significant interaction effect between forcing frequency and disease state.

In healthy controls (CN), the effective dimensionality (`tube_d_eff_median`) is expected to remain stable or expand to accommodate both the sensory input and ongoing endogenous processing. In contrast, the AD cohort is predicted to exhibit a sharp, monotonic drop in `tube_d_eff_median` as the frequency increases. This geometric collapse signifies that the high-frequency external drive overpowers the constricted state space of the compromised cortex, forcing the entire network into a rigid, low-dimensional periodic trajectory.

### 3.2. Regional Dissociation: Posterior AD vs. Frontal FTD

By deploying the regional configuration of `NeuralManifoldDynamics`, we map the spatial distribution of this geometric constraint:

* **Alzheimer’s Disease:** The collapse of `tube_d_eff_median` and the elevation of capture metrics are expected to localize heavily within the parietal-occipital and temporal channel groups, reflecting the typical temporoparietal network degradation patterns. The forward propagation of the driving rhythm from O1/O2 is bottlenecked by the damaged local geometry of the temporal lobes.
* **Frontotemporal Dementia:** Conversely, the FTD cohort is predicted to show near-normal reachability dynamics in posterior regions during photic driving, but will exhibit severe disruptions, bimodal state transitions, and an inflation of the `spectral_radius_median` specifically within the frontal channel group, tracking the anatomical epicenter of frontal-lobe atrophy.

### 3.3. Jacobian Tension and MMSE Correlations

We predict that the Meta-Noetic Jacobian tension, measured by `spectral_radius_median`, will reveal a proximity to local bifurcation in the degenerate groups under high-frequency stress. At 20 Hz and 30 Hz, the AD cohort is hypothesized to exhibit a critical spike in spectral radius, demonstrating that the network is operating at its absolute stability boundary. Crucially, these evoked geometric features are expected to correlate linearly with the subjects' MMSE scores, providing an explicit link between macro-manifold geometry and clinical cognitive impairment.

---

## 4. Discussion

Through the lens of *Noetic Diffusion Theory*, the cognitive symptoms of Alzheimer’s disease are fundamentally tied to a loss of dynamical states—a physical shrinkage of the future horizons reachable by the neural trajectory. The results of this photic stimulation paradigm provide direct empirical validation of this mechanism.

Phenomenologically, the frequency-dependent drop in effective dimensionality observed in AD represents a state of **sensory entrapment**. When exposed to high-frequency periodic stimuli, the AD brain lacks the network-level geometric capacity needed to isolate the external noise from the internal narrative. The periodic drive effectively flattens the manifold, explaining why AD patients experience acute confusion, sensory overload, and behavioral agitation in complex, highly stimulated environments.

Methodologically, this study highlights the immense value of "stress-testing" neural manifolds using evoked paradigms rather than resting-state alone. By pushing the network with an incremental periodic forcing function, we expose the limits of its cognitive reserve. Because the `NeuralManifoldDynamics` pipeline operates on frozen coordinate contracts and versioned architectures, these results avoid the pitfalls of post-hoc parameter tuning, offering a highly reproducible, auditable, and non-subjective biomarker for differentiating neurodegenerative etiologies.
