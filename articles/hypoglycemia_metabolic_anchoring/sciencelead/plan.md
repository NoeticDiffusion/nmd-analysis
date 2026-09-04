# EAP extension: glucose as a metabolic anchoring constraint

Yes. I think glucose belongs in EAP—but **not as another rhythmic anchor comparable to heartbeat or respiration**, and not as a direct “consciousness variable.”

The cleanest interpretation is:

> Cardiac and respiratory signals help time and contextualize reconstruction, whereas glucose availability constrains whether metabolically expensive reconstruction remains possible at all.

This makes glucose a **slow homeostatic boundary condition** or **metabolic accessibility gate** beneath the faster embodied anchors.

The present EAP already separates landscape conditioning through a self-prior from body-synchronized variance gating. Its interoceptive state currently contains cardiac phase, respiratory phase, and HEP amplitude, while rhythmic entrainment modulates (r(t)).   The glucose extension should preserve that architecture rather than inserting glucose into the phase-coupling equation.

## What the research supports

### 1. Glucose, rather than insulin itself, is the acute limiting variable

Controlled hypoglycemic-clamp studies show that cognitive performance deteriorates as plasma glucose falls, commonly becoming clearly impaired around approximately (2.8–3.1\ \mathrm{mmol/L}), although thresholds vary between people and with diabetes history. Severe hypoglycemia can progress from impaired attention and confusion to seizures or loss of consciousness. ([PubMed][1])

The brain’s basal glucose supply is predominantly mediated by GLUT1 and GLUT3 rather than by the insulin-dependent GLUT4 mechanism that dominates in tissues such as skeletal muscle. Insulin nevertheless has central signaling roles in hypothalamic regulation, reward, memory, regional perfusion, and functional connectivity. Human intranasal-insulin studies show regional brain effects, but cognitive effects are heterogeneous: a large 12-month trial did not find a significant primary cognitive benefit. ([PMC][2])

Therefore:

* **Blood glucose availability** belongs in the acute EAP state.
* **Peripheral insulin** belongs primarily in the dynamical model producing glucose changes.
* **Central insulin signaling** is better treated as a slower modulatory variable, not an instantaneous index of consciousness.

### 2. Hypoglycemia produces an NDT-relevant neural signature

A hyperinsulinemic–hypoglycemic clamp study in 34 people with type 1 diabetes recorded 19-channel EEG during euglycemia and hypoglycemia. Hypoglycemia was associated with increased regularity, greater delta/theta activity, reduced EEG complexity, and previously reported reductions in directed connectivity. Nonlinear EEG features distinguished hypoglycemia from euglycemia with approximately 90% classification accuracy in that proof-of-concept analysis. ([MDPI][3])

This is especially interesting for NDT because it creates a **metabolic version of the Grand Mal paradox**:

* slow rhythmic power may increase;
* signal complexity may decrease;
* but cognition and conscious access worsen.

A minimal (F=e-m) interpretation could therefore falsely identify hypoglycemia as improved coherence. The (d)-family, MNJ, reachability, and a metabolic adequacy gate are required to distinguish functional denoising from metabolically driven low-complexity collapse.

### 3. Hypoglycemia awareness is directly relevant to EAP

Human fMRI work indicates that insular and basal-ganglia networks participate in hypoglycemia awareness, and that this mediation differs in type 1 diabetes. Repeated hypoglycemia can produce impaired awareness: actual metabolic danger becomes progressively dissociated from the subjective warning signal. ([PMC][4])

That gives EAP an unusually clean dissociation:

[
\text{metabolic state} \neq \text{interoceptive awareness of metabolic state}.
]

This is theoretically valuable because the current EAP already distinguishes bodily signal transmission from ownership or binding. Glucose adds another distinction:

1. **Metabolic adequacy:** is sufficient substrate available?
2. **Metabolic signaling:** does the organism generate autonomic warning?
3. **Conscious metabolic awareness:** is that warning represented and experienced?

### 4. High and low glucose should not be modeled symmetrically

Moderate hyperglycemia is not simply the opposite of hypoglycemia. Acute loss of consciousness at the high end usually occurs in severe metabolic emergencies such as hyperosmolar hyperglycemic state or diabetic ketoacidosis, where hyperosmolality, dehydration, electrolyte disturbance, impaired perfusion, ketosis, and acidosis contribute to altered sensorium. ([PubMed][5])

The glucose penalty must therefore be **asymmetric**:

* relatively steep and rapid on the low-glucose side;
* much shallower over ordinary hyperglycemia;
* steep again only in the extreme hyperosmolar or acidotic regime.

---

# Recommended conceptual architecture

I would extend EAP into two coupled layers.

## A. Fast embodied anchoring

Retain the existing state:

[
s_t^{\mathrm{fast}}
===================

\left(
\phi_{\mathrm{cardiac}},
\phi_{\mathrm{resp}},
A_{\mathrm{HEP}}
\right),
]

which conditions the self-prior and phase-resolved RVC.

## B. Slow metabolic anchoring

Introduce:

[
z_t^{\mathrm{met}}
==================

\left(
g_t^{p},
g_t^{b},
\dot g_t^{p},
a_t^{\mathrm{hypo}},
i_t^{p},
i_t^{c},
k_t,
o_t
\right),
]

where:

* (g_t^{p}): measured plasma or interstitial glucose;
* (g_t^{b}): latent effective cerebral glucose availability;
* (\dot g_t^{p}): direction and rate of glucose change;
* (a_t^{\mathrm{hypo}}): autonomic/interoceptive warning signal;
* (i_t^{p}): peripheral insulin;
* (i_t^{c}): effective central insulin signaling;
* (k_t): alternative fuel availability, especially ketones;
* (o_t): hyperosmolar/metabolic-crisis load.

For a minimal EAP extension, only (g_t^{p}), (\dot g_t^{p}), and (a_t^{\mathrm{hypo}}) are needed. The remaining variables prevent later overidentification of blood glucose with actual cerebral fuel availability.

## The central distinction

Define two different quantities:

[
q_t^{\mathrm{met}}
\in [0,1]
]

as the latent **metabolic adequacy gate**, and

[
a_t^{\mathrm{met}}
\in [0,1]
]

as the **experienced or cortically represented metabolic alarm**.

Normally:

[
a_t^{\mathrm{met}}
\approx
\psi!\left(1-q_t^{\mathrm{met}}\right).
]

But the two can dissociate:

* **impaired hypoglycemia awareness:** (q_t^{\mathrm{met}}\downarrow), (a_t^{\mathrm{met}}\approx0);
* **anxiety or false metabolic alarm:** (q_t^{\mathrm{met}}\approx1), (a_t^{\mathrm{met}}\uparrow);
* **ordinary fasting:** moderate signal with preserved adequacy;
* **severe neuroglycopenia:** both cortical representation and metabolic adequacy eventually fail.

A useful mismatch index would be:

[
\Delta_{\mathrm{met}}(t)
========================

\left|
a_t^{\mathrm{met}}
------------------

\psi!\left(1-q_t^{\mathrm{met}}\right)
\right|.
]

This is a genuinely EAP-like quantity: not glucose itself, but the discrepancy between body state and its embodied representation.

---

## Proposed manuscript-ready extension

### Metabolic Anchoring: Glucose Availability and Insulin Signaling

#### Scope and epistemic status

The Embodied Anchoring Principle currently models embodied conditioning through fast interoceptive signals, including cardiac phase, respiratory phase, and heartbeat-evoked cortical responses. We propose a slower metabolic extension in which cerebral fuel availability constrains the neural states that can be stabilized, maintained, and traversed. This extension is speculative at the level of its exact NDT implementation, although the dependence of cognition and neural activity on glucose availability is externally established.

Glucose should not be treated as an additional rhythmic phase variable. Unlike heartbeat and respiration, glycemic variation ordinarily evolves over minutes to hours and does not provide a stable phase reference for individual denoising cycles. It is therefore modeled as a slow homeostatic boundary condition on the potential, effective geometry, and variance-control efficacy.

Insulin is not treated as a direct scalar of conscious level. Peripheral insulin primarily influences the dynamics of plasma glucose, while central insulin signaling may modulate cognition, salience, learning, and regional neural gain over slower timescales. The immediate EAP variable is consequently metabolic adequacy rather than insulin concentration itself.

#### Fast and slow embodied state

We decompose embodied state into fast and metabolic components:

[
s_t^{\mathrm{body}}
===================

\left(
s_t^{\mathrm{fast}},
z_t^{\mathrm{met}}
\right),
]

with

[
s_t^{\mathrm{fast}}
===================

\left(
\phi_{\mathrm{cardiac}}(t),
\phi_{\mathrm{resp}}(t),
A_{\mathrm{HEP}}(t)
\right),
]

and

[
z_t^{\mathrm{met}}
==================

\left(
g_t^{p},
g_t^{b},
\dot g_t^{p},
a_t^{\mathrm{met}},
i_t^{p},
i_t^{c},
k_t,
o_t
\right).
]

Here (g_t^{p}) is measured plasma or interstitial glucose, (g_t^{b}) is latent effective cerebral glucose availability, (a_t^{\mathrm{met}}) is the autonomic and cortically represented metabolic warning signal, (i_t^{p}) and (i_t^{c}) denote peripheral and central insulin states, (k_t) represents alternative metabolic substrate availability, and (o_t) summarizes hyperosmolar, acidotic, or related systemic metabolic stress.

The distinction between (g_t^{p}) and (g_t^{b}) prevents plasma glucose from being identified directly with cerebral energy availability. A minimal latent-substrate model is:

[
\tau_b \dot g_t^{b}
===================

## T_g!\left(g_t^{p},k_t\right)

C!\left(X_t,t\right),
]

where (T_g) represents effective substrate transport and (C(X_t,t)) represents state-dependent metabolic consumption.

#### Metabolic strain

Define an asymmetric metabolic-strain functional:

[
H_{\mathrm{met}}(z_t)
=====================

\eta_L
\operatorname{softplus}
\left(
\frac{\theta_L-g_t^{b}}{s_L}
\right)^2
+
\eta_H
\operatorname{softplus}
\left(
\frac{g_t^{b}-\theta_H}{s_H}
\right)^2
+
\eta_{\dot g}
\left|\dot g_t^{p}\right|
+
\eta_o o_t.
]

The low-glucose penalty is expected to become relevant substantially closer to the ordinary physiological range than the high-glucose penalty. The high-glucose term is therefore interpreted primarily as a severe hyperosmolar or acidotic-regime term rather than as a symmetric penalty for ordinary postprandial hyperglycemia.

The rate term allows rapidly falling glucose to alter embodied state before an absolute critical threshold is crossed.

#### Metabolic conditioning of the noetic potential

The EAP-conditioned potential becomes:

[
\Phi_{\mathrm{EAP}}(X,t)
========================

\Phi_0(X,t)
+
\lambda_{\mathrm{self}}(t)
F_{\mathrm{self}}
\left(
X,s_t^{\mathrm{fast}}
\right)
+
\lambda_{\mathrm{met}}(t)
F_{\mathrm{met}}
\left(
X,z_t^{\mathrm{met}}
\right).
]

A useful decomposition is:

[
F_{\mathrm{met}}(X,z_t)
=======================

H_{\mathrm{met}}(z_t)C_X(X)
+
F_{\mathrm{homeo}}(X,a_t^{\mathrm{met}}),
]

where (C_X(X)) is the metabolic cost associated with maintaining or traversing state (X), and (F_{\mathrm{homeo}}) biases the landscape toward food seeking, interruption of ongoing goals, defensive action, or other homeostatically relevant attractors.

Under mild metabolic strain, this term changes the content and action relevance of experience without necessarily reducing conscious level. Under severe strain, it progressively makes high-cost and highly differentiated trajectories inaccessible.

#### Metabolic adequacy gate

Define metabolic adequacy as:

[
q_t^{\mathrm{met}}
==================

\exp
\left[
-H_{\mathrm{met}}(z_t)
\right],
\qquad
q_t^{\mathrm{met}}\in(0,1].
]

The effective geometry is then:

[
G_t^{\mathrm{EAP}}
==================

q_t^{\mathrm{met}}G_t^{0}
+
\left(
1-q_t^{\mathrm{met}}
\right)
G_t^{\mathrm{failure}},
]

where (G_t^{0}) is the ordinary task- and attention-dependent geometry and (G_t^{\mathrm{failure}}) is a low-rank or highly anisotropic geometry associated with metabolic failure.

This formulation predicts that metabolic deterioration need not merely move the trajectory to another location in MNPS. It can reduce the number of locally available directions, increase canalization, and contract short-horizon reachability.

#### Metabolic gating of rhythmic variance control

The observed strength of a neural rhythm should not be equated automatically with its ability to implement functional variance control. Hypoglycemia may increase slow-frequency EEG power while simultaneously impairing cognition and reducing signal complexity. We therefore distinguish observed rhythmic structure (r_{\mathrm{obs}}(t)) from effective control (r_{\mathrm{eff}}(t)):

[
r_{\mathrm{eff}}(t)
===================

\chi_{\mathrm{met}}(t)
r_{\mathrm{obs}}(t)
\left[
1+
\gamma_{\mathrm{entrain}}
\cos
\left(
\phi_{\mathrm{cardiac}}-\phi_\theta
\right)
\cos
\left(
\phi_{\mathrm{resp}}-\phi_\alpha
\right)
\right],
]

where

[
\chi_{\mathrm{met}}(t)
======================

q_t^{\mathrm{met}}
]

in the minimal formulation.

The variance schedule remains:

[
\sigma(t)
=========

\sigma_{\min}
+
\sigma_0
\left[
1-r_{\mathrm{eff}}(t)
\right].
]

Thus, high rhythmic amplitude under metabolic impairment does not necessarily imply strong functional denoising. Metabolic adequacy determines whether rhythmic coordination can be translated into controlled state reconstruction.

#### Warning and failure regimes

A single monotonic glucose-to-consciousness function is unlikely to be sufficient. We instead distinguish three regimes:

1. **Transparent metabolic adequacy.** Metabolic state remains mostly phenomenologically backgrounded. Fast cardiac and respiratory anchors dominate EAP modulation.

2. **Homeostatic warning.** Falling glucose increases autonomic salience, bodily urgency, attentional narrowing, and the attractor strength of food-seeking or interruption behaviors. Experience remains coherent but becomes increasingly organized around bodily need.

3. **Neuroglycopenic failure.** Metabolic adequacy falls below the level required to sustain differentiated state-space dynamics. Working memory, semantic continuity, orientation, and behavioral control deteriorate. At greater severity, reachability and effective dimensionality collapse, with possible seizure or loss of consciousness.

A warning function (w_t) and failure function (c_t) may be defined as:

[
w_t
===

\sigma_{\mathrm{log}}
\left(
\frac{\theta_W-g_t^{b}}{s_W}
\right)
\left[
1-
\sigma_{\mathrm{log}}
\left(
\frac{\theta_C-g_t^{b}}{s_C}
\right)
\right],
]

[
c_t
===

\sigma_{\mathrm{log}}
\left(
\frac{\theta_C-g_t^{b}}{s_C}
\right),
]

with (\theta_C<\theta_W).

Interoceptive self-prior strength can then be nonmonotonic:

[
\lambda_{\mathrm{met}}(t)
=========================

\lambda_0
\left[
1+\kappa_W w_t-\kappa_C c_t
\right].
]

This captures increased bodily salience during early warning followed by failure of coherent cortical representation during severe neuroglycopenia.

#### Metabolic awareness dissociation

Let (a_t^{\mathrm{met}}) denote the represented metabolic alarm and (q_t^{\mathrm{met}}) actual metabolic adequacy. In the ordinary case:

[
a_t^{\mathrm{met}}
\approx
\psi
\left(
1-q_t^{\mathrm{met}}
\right).
]

Define the metabolic anchoring mismatch:

[
\Delta_{\mathrm{met}}(t)
========================

\left|
a_t^{\mathrm{met}}
------------------

\psi
\left(
1-q_t^{\mathrm{met}}
\right)
\right|.
]

A high mismatch can arise in at least two directions:

* low adequacy with weak warning, as in impaired awareness of hypoglycemia;
* preserved adequacy with strong perceived metabolic alarm, as in false-alarm or anxiety-like interoceptive states.

This dissociation makes glucose particularly relevant to EAP: embodied anchoring depends not only on physiological state, but on whether that state is transmitted, represented, and bound into the self-model.

#### Insulin dynamics

Peripheral insulin may be represented through a minimal glucose–insulin control system:

[
\dot g_t^{p}
============

*

\left(
p_1+x_t^I
\right)
\left(
g_t^{p}-g_b
\right)
+
\frac{R_a(t)}{V_g},
]

[
\dot x_t^I
==========

-p_2x_t^I
+
p_3
\left(
i_t^{p}-i_b
\right),
]

where (R_a(t)) is glucose appearance from meals or treatment and (x_t^I) is effective peripheral insulin action.

Central insulin (i_t^c) is treated as an optional slower modulation of geometry, learning, or self-prior precision:

[
G_t
\mapsto
G_t
+
\kappa_I h_I(i_t^c)G_I,
]

or

[
\dot\theta_\Phi
\mapsto
\dot\theta_\Phi
+
\eta_I h_I(i_t^c)
\nabla_{\theta_\Phi}\mathcal L.
]

No claim is made that central insulin directly determines conscious level. Its proposed role is modulatory and currently less identifiable than the acute effect of metabolic substrate availability.

#### Predictions

The metabolic EAP extension predicts:

1. Hypoglycemia will produce a dissociation between increased low-frequency rhythmic power and reduced complexity, connectivity, reachability, or effective dimensionality.

2. The coarse (m) coordinate may increase under hypoglycemia because of greater delta/theta structure, while stratified coordinates and reachability reveal functional collapse. This constitutes a metabolic analogue of the hypersynchrony paradox.

3. Early warning will increase coupling between autonomic signals, insular activity, and homeostatic behavior before severe MNPS contraction occurs.

4. Individuals with impaired hypoglycemia awareness will show a reduced relationship between metabolic strain and interoceptive signal indices despite retaining glucose-linked EEG deterioration.

5. Recovery after glucose administration will not necessarily retrace the hypoglycemic trajectory exactly. Hysteresis may occur because counterregulatory activation, autonomic arousal, and neural recovery have different time constants.

6. Moderate hyperglycemia will produce weaker and slower geometric effects than comparable deviations below the euglycemic range, whereas hyperosmolar or acidotic crisis will produce strong contraction and disorganization through additional systemic variables.

#### Claim boundary

Metabolic anchoring is not proposed as a fourth MNPS axis and blood glucose is not interpreted as a consciousness meter. The extension treats metabolic state as an external and partially latent conditioning variable that changes the potential, effective geometry, and efficacy of rhythmic control. The exact equations are speculative and should be tested against simpler alternatives, including glucose as a mere covariate, a potential-only model, a geometry-only model, and a model based solely on autonomic arousal.

## Operationalization is more possible than it first appeared

There is in fact a highly relevant open dataset. The Rubega et al. Zenodo record contains a 361.5 MB `DataAndCode.zip` under CC BY 4.0, associated with the 34-participant clamp EEG study. ([zenodo.org][6])

It appears suitable for a first bounded NDT test:

[
\text{euglycemia}
\rightarrow
\text{hypoglycemia}
\rightarrow
\text{recovery}.
]

The study recorded glucose approximately every five minutes during the clamp and selected simultaneous five-minute resting EEG intervals for the glycemic conditions. ([MDPI][3])

A realistic first analysis would not attempt to estimate the full continuous metabolic state. It would test whether the fixed NeuralManifoldDynamics contract distinguishes the three experimentally controlled regimes.

### Minimal empirical test

**Primary contrast**

[
\mathrm{HYPO}-\mathrm{EU}
]

with within-subject inference.

**Recovery contrast**

[
\mathrm{RECOVERY}-\mathrm{EU},
\qquad
\mathrm{RECOVERY}-\mathrm{HYPO}.
]

**Primary predictions**

* EEG complexity and (e_e)-like features decrease.
* Slow-frequency (m)-related features may increase.
* Connectivity-related or (d)-family structure decreases or redistributes.
* Effective reachability dimension decreases.
* Local geometry becomes more anisotropic or canalized.
* Recovery may exhibit hysteresis rather than immediate return to the euglycemic path.

**Most important falsification comparison**

1. Ordinary 3D MNPS.
2. Stratified 9D MNPS.
3. MNJ/reachability.
4. Same models plus glucose condition.
5. Time-shuffled glucose labels.
6. Hypoglycemia-aware versus impaired-awareness participants.

The strongest theoretical result would be:

> Hypoglycemia increases slow rhythmic structure and lowers entropy, yet reduces reachability or effective dimensionality.

That would directly demonstrate why NDT cannot identify healthy denoising from (m) and (e) alone.

## Claim ledger

| Status                          | Claim                                                                                                                         |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Established external result** | Acute hypoglycemia impairs cognition and can cause seizure or loss of consciousness.                                          |
| **Established external result** | Hypoglycemia alters EEG spectral structure, connectivity, and nonlinear complexity.                                           |
| **Established external result** | Insular networks contribute to hypoglycemia awareness.                                                                        |
| **Internal theoretical result** | Current EAP contains fast interoceptive self-prior conditioning and phase-resolved variance entrainment.                      |
| **Plausible interpretation**    | Metabolic adequacy gates whether observed rhythms can implement functional RVC.                                               |
| **Plausible interpretation**    | Glucose-related loss of consciousness should appear more clearly in reachability and stratified geometry than in coarse MNPS. |
| **Speculative extension**       | The exact metabolic potential, metric gate, warning/failure transition, and mismatch equations above.                         |
| **Rejected formulation**        | Insulin concentration as a direct scalar of consciousness.                                                                    |
| **Rejected formulation**        | Adding glucose to the cardiac–respiratory phase-coupling term.                                                                |
| **Rejected formulation**        | Treating low and high glucose deviations as symmetric.                                                                        |
| **Rejected formulation**        | Interpreting increased delta/theta power during hypoglycemia as stronger functional denoising.                                |

My overall recommendation is therefore to add this to EAP under the name **Metabolic Anchoring** or **Metabolic Adequacy Gating**, and to consider the open clamp EEG dataset a genuine future NDT experiment rather than leaving the extension permanently non-operational.

[1]: https://pubmed.ncbi.nlm.nih.gov/28589447/?utm_source=chatgpt.com "Cognitive, neurophysiologic and metabolic sequelae of ..."
[2]: https://pmc.ncbi.nlm.nih.gov/articles/PMC7896252/?utm_source=chatgpt.com "Insulin Resistance Is Associated With Enhanced Brain ... - PMC"
[3]: https://www.mdpi.com/1099-4300/22/1/81 "Detection of Hypoglycemia Using Measures of EEG Complexity in Type 1 Diabetes Patients"
[4]: https://pmc.ncbi.nlm.nih.gov/articles/PMC4524972/?utm_source=chatgpt.com "Functional Connectivity of Insula, Basal Ganglia, and ... - PMC"
[5]: https://pubmed.ncbi.nlm.nih.gov/25905280/?utm_source=chatgpt.com "Hyperglycemic Crises - PubMed - NIH"
[6]: https://zenodo.org/record/3465213 "Detection of hypoglycemia using measures of EEG complexity in type 1 diabetes patients"
