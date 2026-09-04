# Literature-Guided MNPS/MNJ Geometry Ideas for Coma

**Date:** 2026-05-26  
**Status:** Exploratory idea document. None of the proposed metrics are validated in the NDT coma bundles yet.  
**Scope:** New geometry ideas built on MNPS and/or MNJ, guided by external coma and disorders-of-consciousness research.

This document complements `ideas_geometric_cartography_20260526.md`. That earlier note already covered pseudospectra, persistent homology, Fisher-Bures reachability geodesics, Birkhoff/Hopf normal forms, stratified foliations, magnitude functions, and Lorentzian causal cones. The ideas below avoid repeating those as primary proposals.

## External Clues From Coma Research

The literature points to five recurring mechanisms that are geometrically useful:

1. **Dynamic connectivity matters, not just static EEG state.** In post-anoxic coma, dynamic EEG functional connectivity differs by outcome: poor outcome is associated with lower link rate and longer link duration, while good outcome shows more dynamic interactions between brain regions. See [Dynamic functional connectivity of the EEG in relation to outcome of postanoxic coma](https://www.sciencedirect.com/science/article/pii/S1388245720305599).

2. **Recovery is linked to re-emergence of long-range corticocortical and thalamocortical integration.** Reviews of disorders of consciousness emphasize restoration of excitatory neurotransmission across corticocortical, thalamocortical, and thalamostriatal connections, plus DMN/salience/executive-network interaction. See [Recovery from disorders of consciousness](https://preview-www.nature.com/articles/s41582-020-00428-x) and [Dysfunctional connectivity as a neurophysiologic mechanism of disorders of consciousness](https://pmc.ncbi.nlm.nih.gov/articles/PMC10394244/).

3. **Reactivity is favorable when measurable objectively.** Standardized quantitative EEG reactivity after electrical stimulation improved good-outcome prediction in post-cardiac-arrest coma, with reported AUC around `0.93` in one recent study. See [Quantitative EEG reactivity induced by electrical stimulation predicts good outcome](https://link.springer.com/article/10.1186/s13613-024-01339-6).

4. **Consciousness depends on integrated and differentiated responses.** PCI/TMS-EEG work frames consciousness as the ability to generate responses that are both distributed and information-rich, rather than stereotyped or locally extinguished. See [A theoretically based index of consciousness independent of sensory processing and behavior](https://www.science.org/doi/10.1126/scitranslmed.3006294).

5. **Continuity and suppression are time-dependent.** Early EEG suppression can be transient; persistent suppression or burst-suppression later is more ominous, while transition toward continuous normal-voltage background within the first day is favorable. See [EEG monitoring after cardiac arrest](https://pmc.ncbi.nlm.nih.gov/articles/PMC9468095/) and [Neuroprognostication guidelines](https://www.neurocriticalcare.org/Portals/0/Guidelines/Neuroprognostication_in_comatose_survivors_of_cardiac_arrest_Neurocritical_Care_March_2023.pdf?ver=94xDTV7WFckEc1lXxWncCQ%3D%3D).

The common geometric message is: good recovery is not merely "large signal" or "more variance." It looks more like preserved **dynamic integration**, **reactive deformation**, **network-state mobility**, and **non-stereotyped but coherent propagation**.

## Idea 1: MNPS Reactivity Vector Field

### Motivation

EEG reactivity is one of the clearest favorable signs when measured reliably. Even if explicit stimulation events are not present in the current I-CARE exports, we can define a geometry of spontaneous reactivity: how the local MNPS state responds after internally detected perturbation-like events.

### Geometry

Let `x_t` be the MNPS state and let `P_t` mark a perturbation event. `P_t` could be:

- an explicit stimulus marker if available,
- a burst onset,
- a sharp change in qEEG power,
- a large innovation residual under the local MNPS predictor,
- or a large transient in `||dot(x_t)||`.

Define the response displacement:

$$
r_t(\tau) = x_{t+\tau} - x_t.
$$

Define the baseline local prediction:

$$
\hat{x}_{t+\tau} = x_t + \tau f(x_t,t).
$$

Then define reactivity residual:

$$
R_t(\tau) =
x_{t+\tau} - \hat{x}_{t+\tau}.
$$

The patient-level reactivity geometry is:

$$
\mathrm{ReactAmp}_i =
\operatorname{median}_{t \in P_i}
\lVert R_t(\tau) \rVert,
$$

and the directional spread is:

$$
\mathrm{ReactDim}_i =
\frac{
\left(\sum_k \lambda_k(C_i^R)\right)^2
}{
\sum_k \lambda_k(C_i^R)^2 + \varepsilon
},
$$

where

$$
C_i^R =
\operatorname{Cov}\{R_t(\tau): t \in P_i\}.
$$

### Why It May Separate CPC1 and CPC5

If recovery depends on preserved responsiveness, later `CPC 1` should show response residuals that are not only larger, but more directionally differentiated. Later `CPC 5` may show either absent response or stereotyped low-dimensional response. This turns clinical "reactivity" into an MNPS vector-field object.

### First Test

Use spontaneous perturbation events first. Then test whether `ReactDim` and `ReactAmp` add beyond `tube_d_eff_median`, `spectral_radius_median`, and `frobenius_norm_median`.

## Idea 2: MNJ Stimulus-Gain Tensor

### Motivation

The external reactivity literature suggests that outcome may depend on how a perturbation changes the system's local dynamics, not only where the state moves. MNJ gives a direct object for this.

### Geometry

For perturbation windows `P_t`, compare pre- and post-event Jacobians:

$$
\Delta J_t^{(\tau)} =
J_{t+\tau} - J_{t-\tau}.
$$

Define gain:

$$
G^J_t =
\frac{
\lVert \Delta J_t^{(\tau)} \rVert_F
}{
\lVert J_{t-\tau} \rVert_F + \varepsilon
}.
$$

Define structured gain on symmetric and rotational parts:

$$
G^S_t =
\frac{\lVert S_{t+\tau} - S_{t-\tau} \rVert_F}
{\lVert S_{t-\tau} \rVert_F + \varepsilon},
\qquad
G^\Omega_t =
\frac{\lVert \Omega_{t+\tau} - \Omega_{t-\tau} \rVert_F}
{\lVert \Omega_{t-\tau} \rVert_F + \varepsilon}.
$$

where

$$
S_t = \frac{J_t + J_t^\top}{2},
\qquad
\Omega_t = \frac{J_t - J_t^\top}{2}.
$$

### Why It May Separate CPC1 and CPC5

Static MNJ metrics may miss whether the brain can update its local rules after perturbation. `CPC 1` may show bounded but real gain: the operator changes after perturbation without destabilizing. `CPC 5` may show either no gain (unreactive lock-in) or excessive rotational gain (pathological response).

This is a direct MNJ translation of quantitative EEG reactivity.

## Idea 3: Dynamic Connectivity as MNPS Edge-Flow

### Motivation

Post-anoxic coma studies suggest that good outcome has more dynamic interactions, while poor outcome has lower link rate and longer link duration. This maps naturally to graph flow on regional MNPS states.

### Geometry

Let `x_t^r` be the regional MNPS state for region `r`. Define dynamic similarity:

$$
w_{rs}(t) =
\exp\left(
-\frac{\lVert x_t^r - x_t^s \rVert^2}{\sigma^2}
\right).
$$

Define an edge as active if

$$
w_{rs}(t) > \theta.
$$

MNPS link rate:

$$
\mathrm{LR}^{MNPS}_i =
\frac{1}{T}
\sum_t
\frac{1}{|E|}
\sum_{r<s}
\mathbf{1}[w_{rs}(t) > \theta].
$$

MNPS link duration:

$$
\mathrm{LD}^{MNPS}_i =
\operatorname{median}
\{\text{run length of active } (r,s) \text{ edges}\}.
$$

### Why It May Separate CPC1 and CPC5

External EEG dynamic connectivity work reports poor outcome as lower link rate and longer link duration. In MNPS terms, this suggests that `CPC 5` may have fewer active inter-regional geometric couplings, and the remaining ones may persist too long as rigid links. `CPC 1` may have more frequent but less frozen inter-regional interactions.

This gives a regional extension of reachability that is explicitly dynamic-connectivity-like.

## Idea 4: MNJ Edge Plasticity Graph

### Motivation

Dynamic connectivity can be reframed in operator language. Instead of asking whether regional states are similar, ask whether regional local dynamics are coupled or co-changing.

### Geometry

For each region `r`, estimate a regional Jacobian `J_t^r`. Define inter-regional operator similarity:

$$
a_{rs}(t) =
\frac{
\langle J_t^r, J_t^s \rangle_F
}{
\lVert J_t^r \rVert_F \lVert J_t^s \rVert_F + \varepsilon
}.
$$

Define operator edge plasticity:

$$
P_{rs}(t) =
|a_{rs}(t+1) - a_{rs}(t)|.
$$

Patient-level graph plasticity:

$$
\mathrm{GraphPlasticity}_i =
\operatorname{median}_t
\frac{1}{|E|}
\sum_{r<s} P_{rs}(t).
$$

### Why It May Separate CPC1 and CPC5

If recovery requires flexible large-scale coordination, later `CPC 1` should preserve changing relationships among regional operators. Later `CPC 5` may show operator couplings that are either absent or stuck. This is closer to "dynamic functional connectivity" than whole-brain `spectral_radius_median`.

## Idea 5: Thalamocortical Proxy as Hub-Gated MNPS Geometry

### Motivation

The coma literature repeatedly emphasizes thalamocortical and corticocortical integration. Scalp EEG does not observe thalamus directly, but MNPS can still test a proxy: whether midline/frontal/central dynamics act like a hub that gates distributed cortical mobility.

### Geometry

Let `h_t` be a hub proxy built from midline, frontal, and central regional MNPS:

$$
h_t =
\operatorname{concat}
(x_t^\mathrm{midline}, x_t^\mathrm{frontal}, x_t^\mathrm{central}).
$$

Let `y_t` be the remaining regional state:

$$
y_t =
\operatorname{concat}
(x_t^\mathrm{temporal}, x_t^\mathrm{parietal-occipital},
x_t^\mathrm{left}, x_t^\mathrm{right}).
$$

Fit a local gating model:

$$
\dot{y}_t =
A_t y_t + B_t h_t + \epsilon_t.
$$

Define hub-gate strength:

$$
H_i =
\operatorname{median}_t
\frac{\lVert B_t \rVert_F}
{\lVert A_t \rVert_F + \varepsilon}.
$$

Define hub-gate stability:

$$
H^\mathrm{stab}_i =
\left(
\operatorname{var}_t
\frac{\lVert B_t \rVert_F}
{\lVert A_t \rVert_F + \varepsilon}
\right)^{-1}.
$$

### Why It May Separate CPC1 and CPC5

If recovery requires reactivation of long-range hub-mediated integration, later `CPC 1` may show stronger and more stable hub-to-distributed gating. Later `CPC 5` may show weak `B_t` coupling: regional systems move locally but fail to be globally integrated.

This is not a direct thalamus measure. It is a scalp-level proxy for hub-gated integration, explicitly labeled as such.

## Idea 6: DMN-Like Posterior-Midline Integration Proxy

### Motivation

DMN integrity and midline frontoparietal connectivity are repeatedly linked to consciousness recovery in fMRI DoC studies. EEG channel groups cannot reconstruct DMN, but the regional pipeline has midline and parietal-occipital groups that can serve as a weak proxy.

### Geometry

Define posterior-midline integration:

$$
D_t =
\exp\left(
-\frac{
\lVert x_t^\mathrm{midline} - x_t^\mathrm{parietal-occipital} \rVert^2
}{
\sigma^2
}
\right).
$$

Define operator version:

$$
D^J_t =
\frac{
\langle J_t^\mathrm{midline}, J_t^\mathrm{parietal-occipital} \rangle_F
}{
\lVert J_t^\mathrm{midline} \rVert_F
\lVert J_t^\mathrm{parietal-occipital} \rVert_F
+ \varepsilon
}.
$$

Patient summaries:

$$
D_i = \operatorname{median}_t D_t,
\qquad
D^J_i = \operatorname{median}_t D^J_t.
$$

### Why It May Separate CPC1 and CPC5

If recovery requires midline/posterior integration, later `CPC 1` should show stronger and more coherent posterior-midline coupling. Later `CPC 5` may show decoupling or rigid coupling without dynamic range.

This is deliberately a weak proxy. Its value is not as proof of DMN recovery, but as a testable EEG geometry inspired by DMN recovery literature.

## Idea 7: Integration-Differentiation Balance in MNPS

### Motivation

PCI frames consciousness as simultaneous integration and differentiation. MNPS/reachability can approximate this without TMS by comparing shared regional movement to region-specific movement.

### Geometry

Let regional MNPS states be `x_t^r`. Define global integrated component:

$$
\bar{x}_t =
\frac{1}{R}\sum_{r=1}^R x_t^r.
$$

Integration:

$$
I_t =
\frac{1}{R}
\sum_r
\exp\left(
-\frac{\lVert x_t^r - \bar{x}_t \rVert^2}{\sigma^2}
\right).
$$

Differentiation:

$$
Q_t =
\operatorname{rank}_{\mathrm{eff}}
\left(
\operatorname{Cov}_r(x_t^r)
\right).
$$

Balance:

$$
B_t^{ID} =
I_t \cdot Q_t.
$$

Patient summary:

$$
B_i^{ID} =
\operatorname{median}_t B_t^{ID}.
$$

### Why It May Separate CPC1 and CPC5

A globally synchronized coma pattern may have high integration but low differentiation. A fragmented pathological state may have differentiation without integration. Recovery should require both. This TAC directly maps the PCI logic into regional MNPS geometry.

Expected pattern:

- `CPC 1`: moderate/high integration and preserved differentiation,
- `CPC 5`: low balance due to either collapse into uniform suppression or disorganized fragmentation.

## Idea 8: MNJ Response Complexity Without External Perturbation

### Motivation

PCI uses perturbation response complexity. Without TMS, we can ask whether the spontaneous MNJ field has algorithmic or symbolic complexity across windows.

### Geometry

Construct a symbolic sequence from Jacobian states. For example, define symbol `s_t` by the signs or quantile bins of:

$$
z_t =
\left[
\rho(J_t),
\lVert S_t \rVert_F,
\lVert \Omega_t \rVert_F,
\operatorname{var}_i(|\lambda_i(J_t)|),
\mathrm{MDR}_t
\right].
$$

Discretize:

$$
s_t = q(z_t).
$$

Define compression complexity:

$$
C^J_i =
\frac{
\mathrm{LZ}(s_1,\ldots,s_T)
}{
T / \log T
}.
$$

### Why It May Separate CPC1 and CPC5

PCI suggests that conscious-capable systems generate responses that are integrated and differentiated rather than stereotyped. A low-complexity MNJ sequence may reflect a rigid coma attractor. A higher but structured complexity may reflect preserved dynamical repertoire.

The important control is shuffled-time complexity. If complexity survives all shuffles unchanged, it is distributional rather than dynamical.

## Idea 9: Continuity Recovery Geometry

### Motivation

EEG monitoring literature emphasizes transition toward continuous normal-voltage background as favorable, while persistent suppression/burst-suppression is poor. MNPS can translate this into continuity of state-space motion and continuity of local operator validity.

### Geometry

Define MNPS continuity at window `t`:

$$
C^x_t =
\exp\left(
-\frac{\lVert x_t - x_{t-1} \rVert^2}{\sigma_x^2}
\right)
\cdot
\mathbf{1}[\mathrm{valid}(x_t)].
$$

Define Jacobian continuity:

$$
C^J_t =
\exp\left(
-\frac{\lVert J_t - J_{t-1} \rVert_F^2}{\sigma_J^2}
\right)
\cdot
\mathbf{1}[\mathrm{valid}(J_t)].
$$

Define recovery slope in the first 12 h:

$$
\beta_i^C =
\operatorname{slope}_t
\left(
\operatorname{logit}
\left(
\operatorname{smooth}(C^x_t C^J_t)
\right)
\right).
$$

### Why It May Separate CPC1 and CPC5

This converts EEG continuity recovery into a geometry of continuous state/operator evolution. `CPC 1` should show increasing continuity over the first hours. `CPC 5` may remain discontinuous, suppressed, or burst-like in geometry.

This candidate is likely to align with clinical EEG background, so it should be tested both with and without qEEG background covariates.

## Idea 10: Network-State Dwell Geometry

### Motivation

Dynamic connectivity findings imply that not only the available states but also dwell times in states matter. Poor outcome may correspond to long dwell in a small number of low-capacity states.

### Geometry

Cluster MNPS windows into `K` geometry states:

$$
c_t = \operatorname{kmeans}(x_t, K).
$$

Build transition matrix:

$$
P_{ab} =
\Pr(c_{t+1}=b \mid c_t=a).
$$

Define dwell entropy:

$$
H^\mathrm{dwell}_i =
-\sum_a \pi_a \log(\pi_a + \varepsilon),
$$

where `pi_a` is the stationary or empirical occupancy of state `a`.

Define transition mobility:

$$
M_i =
1 - \frac{1}{K}\operatorname{tr}(P).
$$

Define lock-in index:

$$
L_i =
\max_a P_{aa}.
$$

### Why It May Separate CPC1 and CPC5

External dynamic connectivity studies suggest poor outcome has fewer dynamic interactions and longer durations. In MNPS state geometry this should appear as high lock-in, low transition mobility, and low dwell entropy. `CPC 1` should show broader state repertoire and more transitions.

This is distinct from reachability because it describes realized state switching, not short-horizon admissible futures.

## Idea 11: Innovation Propagation Geometry

### Motivation

Recovery may require that local innovations propagate across regions rather than remaining local. This maps to effective connectivity more directly than correlation.

### Geometry

Fit a regional vector autoregressive MNPS model:

$$
x_{t+1}^r =
\sum_s A_{rs} x_t^s + \epsilon_t^r.
$$

Define directed propagation strength:

$$
P_{s \to r} =
\lVert A_{rs} \rVert_F.
$$

Define global propagation efficiency:

$$
E^\mathrm{prop}_i =
\frac{1}{R(R-1)}
\sum_{r \neq s}
\mathbf{1}[P_{s \to r} > \theta].
$$

Define propagation asymmetry:

$$
A^\mathrm{prop}_i =
\frac{1}{R(R-1)}
\sum_{r<s}
|P_{r \to s} - P_{s \to r}|.
$$

### Why It May Separate CPC1 and CPC5

The DoC literature distinguishes thalamocortical arousal and corticocortical awareness. Scalp EEG cannot directly recover those circuits, but a directed regional MNPS model can test whether innovations propagate globally or remain locally trapped.

Expected pattern:

- `CPC 1`: higher propagation efficiency with moderate asymmetry,
- `CPC 5`: low propagation efficiency or excessive one-way pathological drive.

## Idea 12: Recovery-Vector Alignment

### Motivation

Clinical recovery is temporal: patients improve or fail to improve. Instead of only comparing distributions of geometry, estimate whether each patient's early geometry points toward the cohort-level recovery direction.

### Geometry

Let the group-level recovery vector be the difference between CPC1 and CPC5 centroids:

$$
v_\mathrm{rec} =
\mu_{\mathrm{CPC1}} - \mu_{\mathrm{CPC5}}.
$$

For each patient, define early MNPS drift:

$$
d_i =
\operatorname{median}_{t \in 0-12h} \dot{x}_t.
$$

Recovery alignment:

$$
A_i^\mathrm{rec} =
\frac{
\langle d_i, v_\mathrm{rec} \rangle
}{
\lVert d_i \rVert \lVert v_\mathrm{rec} \rVert + \varepsilon
}.
$$

MNJ-conditioned alignment:

$$
A_i^{J\mathrm{rec}} =
\frac{
\langle J_i d_i, v_\mathrm{rec} \rangle
}{
\lVert J_i d_i \rVert \lVert v_\mathrm{rec} \rVert + \varepsilon
}.
$$

### Why It May Separate CPC1 and CPC5

This asks whether early dynamics point toward the recovered region of MNPS space. `CPC 1` should align with the recovery vector, while `CPC 5` may drift orthogonally, reverse, or remain stationary.

This is a more directional alternative to static distance-from-centroid metrics.

## Prioritized Next Geometry Choices

### Highest Priority

1. **MNPS dynamic connectivity / edge-flow:** Directly supported by post-anoxic dynamic EEG connectivity literature, and likely implementable from regional MNPS outputs.

2. **Integration-differentiation balance:** Strong conceptual support from PCI and DoC complexity literature, with a simple regional MNPS implementation.

3. **Continuity recovery geometry:** Closest to validated clinical EEG background evolution; likely to explain part of CPC separation and provide a bridge to clinicians.

### Medium Priority

4. **MNPS/MNJ reactivity field:** Very well motivated, but strongest if explicit stimulus markers are available. Spontaneous perturbation proxies are feasible but less clean.

5. **Hub-gated MNPS geometry:** Strong external mechanism from thalamocortical/DMN literature, but scalp EEG proxy must be described cautiously.

6. **Network-state dwell geometry:** Good match to dynamic connectivity duration findings; simple to implement, but may overlap with reachability persistence.

### Lower Priority

7. **MNJ response complexity:** Conceptually attractive but sensitive to symbolization choices.

8. **Recovery-vector alignment:** Simple and useful, but risks circularity unless the recovery vector is frozen from discovery and tested in a separate cohort.

9. **Innovation propagation geometry:** Mechanistically appealing, but higher risk of overfitting with many regional VAR parameters.

## Suggested Pilot Package

The most disciplined first implementation should avoid exotic geometry and test the literature-guided signals most directly:

1. Build `mnps_dynamic_connectivity_pilot.py`.
   - Inputs: regional MNPS time series.
   - Outputs: `LR_MNPS`, `LD_MNPS`, edge turnover, transition mobility.
   - External anchor: dynamic EEG connectivity in post-anoxic coma.

2. Build `mnps_integration_differentiation_pilot.py`.
   - Inputs: regional MNPS states and optionally regional Jacobians.
   - Outputs: integration, differentiation, product balance, shuffled-region null.
   - External anchor: PCI/integration-differentiation theory.

3. Build `mnps_continuity_recovery_pilot.py`.
   - Inputs: MNPS state validity, step size, Jacobian validity/change.
   - Outputs: early continuity slope, continuity area, burst-like discontinuity fraction.
   - External anchor: EEG continuity/suppression recovery literature.

4. Only after those: test reactivity-like geometry.
   - If explicit stimulation markers are absent, use spontaneous perturbation proxies and label the result as "reactivity-like", not true stimulus reactivity.

## Interpretation Discipline

These ideas are not claims that MNPS directly measures thalamus, DMN, PCI, or clinical EEG reactivity. They are geometric translations of externally supported mechanisms into the NDT measurement system.

The right claim, if a pilot works, would be:

> A geometry inspired by dynamic connectivity, integration-differentiation, or continuity recovery adds outcome-linked structure beyond the current MNJ/reachability summaries.

The wrong claim would be:

> MNPS proves thalamocortical recovery or directly measures consciousness.

The latter requires multimodal or perturbational validation that the current EEG-only bundles do not provide.
