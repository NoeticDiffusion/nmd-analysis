# Curvature-Change Geometry of Recovery-Linked Neural Reachability After Cardiac-Arrest Coma

## A Laguerre-Form-Inspired Follow-Up Analysis of Surface Deformation in Early EEG State Space

**Article type:** Methods-anchored empirical follow-up / exploratory-to-confirmatory geometry report
**Short title:** Curvature-Change Geometry After Coma
**Author:** Robin Langell
**Keywords:** cardiac-arrest coma, EEG, I-CARE, reachability, curvature, Laguerre form, neural geometry, NeuralManifoldDynamics, Noetic Diffusion Theory, recovery prognosis

---

## Abstract

Early EEG after cardiac arrest already supports neuroprognostication through background interpretation, continuity, reactivity, seizures, and quantitative EEG summaries. Recent reachability-based work suggests that outcome-relevant information may also reside in the local geometry of admissible neural state transitions. In a prior I-CARE analysis, later CPC 1 and CPC 5 patients differed in short-horizon reachability during the first 12 h after EEG anchor, with better outcome associated with broader effective dimensionality and weaker local capture. However, reachability size, dimensionality, persistence, and capture do not directly quantify how the reachable state surface itself bends or deforms.

Here we propose and test a Laguerre-form-inspired curvature-change layer for recovery-linked EEG geometry. The central measurement object is not neural activity amplitude, static complexity, or local Jacobian magnitude alone, but the variation of extrinsic curvature across empirically fitted MNPS or reachability surfaces. Operationally, we estimate local surface patches from short-window neural state trajectories and reachability-tube summaries, compute second-fundamental-form-like bending descriptors, and summarize their local covariant variation as curvature-change metrics. Candidate endpoints include `laguerre_norm_median`, `laguerre_norm_p95`, `laguerre_anisotropy`, `laguerre_persistence`, and `laguerre_hourly_slope`.

The primary question is whether later recovery is associated with smoother, more coherent, and adaptively unfolding reachability surfaces, while poor outcome is associated with flattened arrest, pathological folding, or persistent curvature defects. The analysis is designed as a follow-up rather than a replacement for the existing five-metric reachability family. We test whether curvature-change metrics add incremental information beyond clinical variables, qEEG, and the previously frozen reachability layer. The intended contribution is a bounded geometric claim: recovery-linked neural geometry may differ not only in local capacity and capture, but also in the way the accessible state surface bends, unfolds, or becomes pathologically deformed over early monitored time.

---

## Author Summary

After cardiac arrest, the clinically important question is not only whether early EEG appears suppressed, slow, discontinuous, or severe. A deeper dynamical question is whether the brain retains a locally reachable state space that can support later recovery. Previous reachability work showed that patients who later recover well tend to retain broader effective reachable dimensionality and weaker local capture than patients who later reach CPC 5.

This follow-up asks a new question: does the shape of the reachable state surface itself differ between recovery and poor outcome? A Laguerre-form-inspired metric measures how rapidly local surface bending changes across the empirical neural state manifold. In practical terms, this may distinguish a smooth but low-capacity state from a pathologically folded, kinked, or flattened state. The analysis is not presented as a consciousness marker or a bedside biomarker. It is a candidate third-order geometry layer that may complement reachability, Jacobian, qEEG, and clinical predictors.

---

## 1. Introduction

Cardiac-arrest coma is a stringent test case for geometry-based EEG analysis because early neural dynamics must be interpreted under severe clinical heterogeneity, ICU confounding, sedation exposure, variable recording onset, and outcome pathways that may include withdrawal of life-sustaining therapy. Standard EEG interpretation and quantitative EEG already carry prognostic information, and any new geometric layer must therefore be judged by whether it adds disciplined information rather than by whether it simply rediscovers severity.

In the preceding recovery-linked geometry study, the central analytic object was local short-horizon reachability. Each short window of EEG-derived state-space activity was treated as a point in an empirical neural manifold, and local linear stochastic approximations were used to estimate the geometry of nearby admissible futures. The most stable outcome-linked pattern was that later CPC 1 patients retained broader effective reachable dimensionality and weaker local capture/contraction than later CPC 5 patients. The study deliberately framed this as a complement to clinical and qEEG predictors rather than as a direct measurement of consciousness or a bedside-ready biomarker. 

That result raises a natural follow-up question. Reachability summaries describe how large the local reachable cloud is, how many effective directions it spans, how persistent the structure remains, and how strongly the dynamics appear captured. They do not directly measure how the accessible state surface itself bends or deforms. Two patients could have similarly reduced reachability but differ sharply in surface organization: one may occupy a smooth low-capacity state, while another may occupy a locally folded, kinked, or pathologically warped geometry. Likewise, an early recovering patient may show subtle “unfolding” of the reachable surface before scalar capacity summaries fully normalize.

The present follow-up introduces a curvature-change layer inspired by the classical Laguerre form. In differential geometry, the Laguerre form is built from the covariant derivative of the second fundamental form of an embedded surface. In the present empirical setting, we do not claim to recover a literal biological Laguerre form. Instead, we use the mathematical idea as a disciplined measurement template: fit local surface patches in MNPS or reachability-derived coordinates, estimate their extrinsic bending, and summarize how that bending changes across the surface.

The guiding question is:

> During the first 12 h after EEG anchor, do later CPC 1 and later CPC 5 patients differ in the curvature-change geometry of their local reachable neural state surfaces?

The intended contribution is narrow. We do not propose a new scalar consciousness index. We do not claim that curvature-change geometry replaces reachability, qEEG, clinical EEG interpretation, or multimodal prognostication. Instead, we ask whether a third-order surface-deformation descriptor adds interpretable information to an already established geometry layer.

---

## 2. Conceptual Framework

### 2.1 From reachability capacity to surface deformation

The previous reachability analysis can be summarized as a capacity/capture framework. Each local state neighborhood has a short-horizon reachable cloud. That cloud can be summarized by size, effective dimensionality, persistence, and capture/contraction. In the existing coma manuscript, these were organized into capacity/dimensionality, persistence, and capture/contraction families, with `tube_d_eff_median`, `persistence_kappa_median`, `persistence_log_eig_var_median`, `tube_a_operator_norm_median`, and `tube_capture_gate_median` forming the article-facing reachability family. 

Curvature-change geometry asks a different question. Instead of measuring the reachable cloud itself, it asks how the surface supporting or approximating those local reachable clouds bends across time and state. In simplified notation, if an empirical local surface is written as

[
\Sigma: (u,v) \mapsto x(u,v) \in \mathbb{R}^k,
]

then its second fundamental form (II) describes extrinsic bending, while a Laguerre-like curvature-change object summarizes

[
|\nabla II|.
]

This is not equivalent to trajectory curvature. Trajectory curvature measures how a one-dimensional path turns. The proposed curvature-change metric measures how an estimated two-dimensional local state or reachability surface changes its bending from one neighborhood to another.

### 2.2 Why this may matter after coma

Post–cardiac-arrest coma may contain several geometrically distinct low-capacity states. A poor-outcome patient may show:

1. **flattened arrest**, where the reachable geometry is smooth but closed, low-dimensional, and weakly deforming;
2. **pathological folding**, where the surface is locally warped, kinked, or sharply anisotropic;
3. **unstable fragmentation**, where curvature-change hotspots appear intermittently without coherent reopening;
4. **recovering unfolding**, where curvature structure becomes smoother, more coherent, and increasingly compatible with broader reachability over time.

The previous reachability layer can identify capacity and capture differences. The present layer asks whether poor and good outcomes also differ in the *shape-change organization* of the accessible surface.

---

## 3. Hypotheses

### H1. Recovery-linked smooth openness

Later CPC 1 patients will show curvature-change profiles consistent with organized surface openness rather than pathological deformation. Operationally, we expect CPC 1 to show:

* higher effective reachable dimensionality, replicating the previous reachability layer;
* lower capture/contraction summaries;
* lower or moderate `laguerre_norm_median`;
* lower `laguerre_norm_p95`, except during transient reopening periods;
* more coherent temporal evolution of curvature-change metrics over the first 12 h.

This would support the interpretation that recovery-capable brains retain not only broader local reachability but also a smoother and more coherent accessible geometry.

### H2. Poor-outcome flattened arrest or pathological folding

Later CPC 5 patients may show either of two curvature-change phenotypes.

**H2a: Flattened arrest**

* low effective dimensionality;
* high capture/contraction;
* low `laguerre_norm_median`;
* low curvature-change variability;
* weak hourly reopening.

This would indicate a smooth but dynamically closed surface.

**H2b: Pathological folding**

* low effective dimensionality;
* high capture/contraction;
* high `laguerre_norm_p95`;
* high `laguerre_anisotropy`;
* persistent curvature-change hotspots.

This would indicate that poor outcome is not merely low-capacity, but locally deformed or folded.

### H3. Curvature-change metrics add incremental information beyond reachability

The curvature-change layer is strengthened if it improves prediction or stratification beyond:

1. clinical covariates,
2. qEEG summaries,
3. the prior five-feature reachability family.

It is weakened if all curvature-change effects are fully explained by `tube_d_eff_median`, `tube_a_operator_norm_median`, qEEG severity, usable-window counts, or simple trajectory curvature.

### H4. Curvature-change is most useful for subtyping ambiguous or heterogeneous cases

The curvature-change layer may be especially useful for:

* CPC 2–4 intermediate outcomes,
* CPC 5 patients with divergent geometric phenotypes,
* early time bins where reachability capacity has not yet separated strongly,
* patients with possible transition-like geometry over the first monitored hours.

This hypothesis is exploratory unless tested in a separately frozen cohort.

---

## 4. Methods

### 4.1 Dataset and analysis design

The analysis uses the same I-CARE-derived NeuralManifoldDynamics exports as the prior recovery-linked geometry article. The original design included a locked discovery bundle, an explicit non-overlapping verification bundle, and a pooled synthesis after subject/run overlap auditing. The primary window was the first 12 h after EEG anchor, and the main contrast was later CPC 1 versus later CPC 5. 

For the present follow-up, the preferred design is:

1. freeze curvature-change metric definitions before outcome testing;
2. compute the metrics across the existing part1 and part2 bundles;
3. use part1 for calibration and estimator debugging only;
4. treat part2 as the first directional verification set;
5. report pooled analyses as synthesis rather than as external validation.

A stronger future design would evaluate the same frozen curvature-change endpoints in a fully independent I-CARE subset or another post–cardiac-arrest EEG cohort.

### 4.2 Empirical state space

For each EEG run, NeuralManifoldDynamics exports short-window state trajectories in Meta-Noetic Phase Space (MNPS):

[
x_t = [m_t,d_t,e_t]^T
]

with optional stratified 9D coordinates. These coordinates are operational measurement objects, not direct biological variables. They provide a fixed coordinate contract in which local dynamics, reachability, and curvature-change summaries can be computed consistently across patients.

### 4.3 Local surface construction

A Laguerre-form-inspired metric requires a surface, not only a one-dimensional trajectory. We therefore define local empirical surfaces in one of three ways.

#### Surface A: MNPS local patch surface

For each anchor window (t), collect neighboring points in MNPS space within subject or within a condition-matched pooled reference. Fit a local two-dimensional tangent patch using weighted PCA or local polynomial regression. The surface is embedded in 3D MNPS.

#### Surface B: Reachability-tube surface

For each anchor window, use short-horizon reachability covariance summaries to define an ellipsoidal or tube-like local surface. The surface is represented by the dominant two-dimensional reachable subspace, with embedding coordinates derived from MNPS plus reachability deformation.

#### Surface C: Time-by-state recovery surface

For each patient, construct a coarse two-dimensional surface using time since EEG anchor and one state-coordinate direction, embedded into MNPS/reachability feature space. This may be useful for hourly unfolding analyses but is less geometrically pure than local patch surfaces.

The primary analysis should use Surface B if the scientific question is specifically about reachable geometry. Surface A can serve as a simpler MNPS-only comparator.

### 4.4 Curvature-change estimation

For each fitted surface patch, estimate:

1. local tangent basis,
2. normal vector or normal subspace,
3. second-fundamental-form-like bending matrix,
4. neighborhood-wise variation of that bending.

In conceptual form:

[
II_{ij}(p) = \langle \partial_i\partial_j x(p), n(p) \rangle,
]

and the Laguerre-like curvature-change magnitude is approximated as:

[
L_\chi(p) = |\nabla II(p)|.
]

In practice, the estimator should be regularized and reported as an empirical approximation, not as a literal smooth-manifold invariant.

### 4.5 Candidate metrics

The primary curvature-change metric family is:

1. **`laguerre_norm_median`**
   Median local curvature-change magnitude over the first 12 h.

2. **`laguerre_norm_p95`**
   Upper-tail curvature-change magnitude, intended to capture hotspots, kinks, transition rims, or pathological folds.

3. **`laguerre_anisotropy`**
   Directionality of curvature-change. High values indicate bending changes concentrated along a dominant direction.

4. **`laguerre_persistence`**
   Temporal persistence of high curvature-change states.

5. **`laguerre_hourly_slope`**
   Directional change in curvature-change over the first 12 h, used to test unfolding or deterioration.

Secondary metrics may include curvature-change entropy, hotspot count, and curvature-change/reachability coupling.

### 4.6 Comparator metrics

The curvature-change layer should be compared against:

* the prior five-feature reachability family;
* qEEG summaries;
* MNPS path length and displacement;
* trajectory curvature;
* Jacobian Frobenius norm, spectral radius, trace, condition;
* usable-window count and coverage proxies;
* clinical covariates where available.

This is essential because curvature-change metrics may otherwise collapse into ordinary trajectory curvature, artifact burden, or reachability effective dimensionality.

### 4.7 Statistical analysis

The main inferential unit is the patient.

Primary contrast:

[
\text{later CPC 1} \quad \text{vs} \quad \text{later CPC 5}
]

Primary window:

[
0\text{–}12 \text{ h after EEG anchor}
]

For each metric, report:

* group medians,
* robust effect size,
* Cohen’s (d),
* Cliff’s delta,
* Mann–Whitney U test,
* BH-FDR correction across the frozen curvature-change family.

Incremental validity models compare:

1. clinical only,
2. qEEG only,
3. clinical + qEEG,
4. clinical + qEEG + prior reachability,
5. clinical + qEEG + prior reachability + curvature-change.

The curvature-change layer is considered supportive if model 5 improves AUROC, AUPRC, Brier score, calibration, or subgroup separation without relying on an obvious leakage or QC artifact.

### 4.8 Negative controls and robustness checks

The following controls are required before making strong claims:

1. **Time-shuffle control**
   Recompute local surfaces after disrupting temporal order. Curvature-change persistence and hourly slope should weaken.

2. **Outcome-label permutation**
   CPC labels are permuted at the patient level. Group separation should collapse.

3. **Surface-randomization control**
   Fit local surfaces from random neighborhoods rather than state-space neighborhoods. Laguerre-like structure should weaken.

4. **Coverage/QC control**
   Test whether curvature-change metrics are explained by usable-window count, missingness, or recording coverage.

5. **Reachability-residual control**
   Regress curvature-change metrics on the prior reachability family and test whether residual curvature-change still separates outcomes.

6. **Classical curvature control**
   Compare against one-dimensional trajectory curvature to show that the proposed metric is not merely path turning.

---

## 5. Results — Draft Structure

### 5.1 Estimator validity and surface reconstruction quality

Report local surface fit diagnostics:

* neighborhood size,
* explained local surface variance,
* reconstruction residual,
* conditioning,
* percentage of windows passing validity masks,
* subject-level coverage.

Curvature-change results should only be interpreted where surface validity is adequate.

### 5.2 CPC 1 versus CPC 5 curvature-change separation

Report the frozen curvature-change family.

Possible result patterns:

**Pattern 1: CPC 5 flattened arrest**

CPC 5 shows low `laguerre_norm_median`, low `laguerre_norm_p95`, low effective dimensionality, and high capture. This would support a smooth but closed low-capacity geometry.

**Pattern 2: CPC 5 pathological folding**

CPC 5 shows high `laguerre_norm_p95`, high anisotropy, and high capture. This would support pathological surface deformation.

**Pattern 3: CPC 1 adaptive unfolding**

CPC 1 shows moderate curvature-change early, followed by increasing reachability and decreasing capture over time. This would support a geometric reopening interpretation.

### 5.3 Relationship to prior reachability metrics

Correlate curvature-change metrics with:

* `tube_d_eff_median`,
* `tube_a_operator_norm_median`,
* `tube_capture_gate_median`,
* `persistence_kappa_median`,
* `persistence_log_eig_var_median`.

The best outcome is not zero correlation. The best outcome is partial dependence: curvature-change should relate to reachability but not be redundant with it.

### 5.4 Incremental validity over clinical + qEEG + reachability

Report repeated cross-validation and leave-one-site-out sensitivity if site labels are available.

The key test:

> Does curvature-change improve the already stronger geometry-augmented model, or does it merely restate the prior reachability layer?

### 5.5 Intermediate outcomes and geometric subtypes

If CPC 2–4 are included exploratorily, report whether curvature-change metrics place them between CPC 1 and CPC 5 or reveal distinct subgroups.

This section should be explicitly exploratory.

---

## 6. Discussion

This follow-up introduces a curvature-change layer for recovery-linked neural geometry after cardiac-arrest coma. The motivation is that local capacity and capture do not exhaust the geometry of early EEG state space. A patient may retain a reachable cloud that is small but smoothly organized, or may show a reachable cloud that is locally folded, kinked, or anisotropically deformed. A Laguerre-form-inspired metric provides a principled way to ask whether recovery-linked geometry differs in surface deformation, not only in reachability size or effective dimensionality.

The strongest possible contribution would be a dissociation between low-capacity states. If poor-outcome patients show either flattened arrest or pathological folding, while better-outcome patients show smoother unfolding or coherent curvature-change trajectories, then the curvature-change layer would refine the existing capacity/capture framework. It would suggest that early recovery is not only a matter of how much reachable state space remains, but also of how the accessible surface is shaped.

The interpretation must remain bounded. The proposed metric is not a direct biological Laguerre form. It is an empirical surface-deformation descriptor computed from measurement-derived neural state coordinates. It does not measure consciousness, memory, cortical viability, or prognosis directly. It tests whether a third-order geometry layer adds structure to an already auditable EEG-derived state-space analysis.

The strongest methodological risk is overfitting. Because the prior coma article already contains a discovery-selected reachability family, the present follow-up must avoid adding new metrics post hoc and presenting them as confirmatory. The curvature-change family should be frozen before outcome testing, evaluated against negative controls, and reported as incremental only if it adds information beyond qEEG, clinical variables, and the prior reachability layer.

---

## 7. Limitations

1. **Surface estimation is nontrivial.**
   A Laguerre-form-inspired metric requires local surface construction. Poorly conditioned surfaces would make curvature-change estimates unreliable.

2. **Empirical surfaces are not biological tissue surfaces.**
   The surfaces are fitted in MNPS or reachability feature space, not in anatomical cortex.

3. **Curvature-change is not inherently good or bad.**
   Low curvature-change can mean healthy smoothness or pathological flattening. High curvature-change can mean adaptive transition or pathological folding.

4. **The prior reachability layer is already strong.**
   Any new metric must prove incremental value rather than merely adding mathematical ornament.

5. **Outcome labels are clinically complex.**
   CPC 5 intersects with mortality and care pathways, including possible withdrawal-of-care effects.

6. **Prospective validation remains required.**
   Even if curvature-change improves internal or split-bundle performance, it should not be treated as a frozen biomarker without external prospective validation.

---

## 8. Proposed Claim Ledger

| Claim                                                                               | Status before analysis     | Evidence required                     |
| ----------------------------------------------------------------------------------- | -------------------------- | ------------------------------------- |
| Laguerre-inspired curvature-change can be estimated from MNPS/reachability surfaces | Methodological proposal    | Surface validity diagnostics          |
| CPC 1 and CPC 5 differ in curvature-change geometry                                 | Untested hypothesis        | Frozen metric contrast                |
| Curvature-change adds information beyond reachability                               | Untested hypothesis        | Incremental validity / residual tests |
| Poor-outcome coma has flattened or folded reachable surfaces                        | Speculative                | Pattern-specific results              |
| Curvature-change is a consciousness marker                                          | Rejected/non-claim         | Not tested and should not be claimed  |
| Curvature-change is a bedside biomarker                                             | Rejected/non-claim for now | Would require prospective validation  |

---

## 9. Suggested Figures

**Figure 1. Conceptual schematic**
Three local geometries: open smooth surface, flattened arrest surface, folded/captured surface.

**Figure 2. Pipeline**
EEG → NeuralManifoldDynamics → MNPS/reachability → local surface fitting → curvature-change metrics → patient-level aggregation.

**Figure 3. CPC 1 vs CPC 5 curvature-change violin plots**
`laguerre_norm_median`, `laguerre_norm_p95`, `laguerre_anisotropy`, `laguerre_persistence`.

**Figure 4. Curvature-change versus reachability**
Scatterplots against `tube_d_eff_median` and `tube_a_operator_norm_median`.

**Figure 5. Hourly unfolding map**
0–1 h through 11–12 h curvature-change trajectories by outcome.

**Figure 6. Negative controls**
Observed versus shuffled/permuted curvature-change effects.

---

## 10. Provisional Conclusion

A Laguerre-form-inspired curvature-change layer is best understood as a follow-up to reachability-based recovery geometry rather than as a replacement for it. The prior coma analysis established that early recovery-linked EEG geometry is visible in effective reachable dimensionality, persistence, and local capture. The present follow-up asks whether the accessible state surface also differs in how it bends, unfolds, flattens, or becomes pathologically deformed.

If successful, the analysis would support a refined geometric view of post–cardiac-arrest coma: recovery may depend not only on retained local capacity, but also on the organization of the surface through which nearby neural futures remain accessible. If unsuccessful, the result would still be useful by showing that reachability size/capture captures the relevant geometry without requiring third-order surface deformation metrics.

Either outcome would sharpen the NDT measurement program.

---

## Draft ending sentence

**The safest final sentence would be:**

> Curvature-change geometry should therefore be treated not as a new prognostic biomarker, but as a candidate surface-deformation layer for testing whether recovery-linked neural reachability is smooth, flattened, folded, or actively unfolding during the earliest monitored hours after cardiac arrest.

---

My recommendation: call this a **methods-anchored empirical follow-up**, not a theory paper. Best title variant:

**“Curvature-Change Geometry of Recovery-Linked Neural Reachability After Cardiac-Arrest Coma”**

It sounds serious, bounded, and less exotic than putting “Laguerre form” in the main title.
