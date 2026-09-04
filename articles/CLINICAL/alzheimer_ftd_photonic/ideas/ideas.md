Yes. I would simplify ESB quite aggressively.

The original ESB is a **theory-building metric**. For the current Alzheimer/photic paper, I would reduce it to a **three-component perturbation-deviation score**.

# Simplified ESB: ESB-3

The reviewer-safe version:

[
\boxed{
ESB3_i(f)
=========

\frac{1}{\sqrt{3}}
\left|
\frac{
r_i(f)-h_f
}{
s_f+\epsilon
}
\right|_2
}
]

where (i) is subject and (f) is photic frequency.

The response vector is only:

[
r_i(f)=
[
\Delta C_i(f),
\Delta R_i(f),
H_i(f)
]
]

with:

| Component  | Meaning                             | Suggested metric                             |
| ---------- | ----------------------------------- | -------------------------------------------- |
| (\Delta C) | evoked capacity response            | (\Delta) d-block `tube_d_eff_median`         |
| (\Delta R) | evoked guidance / rotation response | (\Delta) `rotational_power_mean` or (\rho_A) |
| (H)        | non-recovery / hysteresis           | post-stimulus residual from baseline         |

The healthy template is:

[
h_f=\mathrm{median}_{HC}(r_i(f))
]

and the robust scaling is:

[
s_f=\mathrm{MAD}_{HC}(r_i(f))
]

So the metric simply asks:

> How far is this subject’s photic response from the normal healthy response at the same frequency?

That is much easier to defend than the full ESB.

---

## Why this is better

The full ESB had four risks:

1. too many variables,
2. too much covariance instability,
3. unclear weighting,
4. risk of double-counting related failures.

ESB-3 solves most of that.

It uses only **three axes**:

[
\text{capacity} \quad + \quad \text{guidance} \quad + \quad \text{recovery}
]

That maps beautifully onto the biological intuition:

> Can the system open?
> Can it organize the opening?
> Can it return?

This is also consistent with the current NDT measurement surface: reachability already treats local capacity through log-det, anisotropy/canalization, effective dimensionality, rotation, and persistence, while explicitly warning that reachability should be interpreted as local capacity, not prediction or semantic content.  NeuralManifoldDynamics also frames 3D MNPS, 9D coordinates, and Jacobian summaries as auditable operational exports rather than direct latent truth claims, which supports a conservative composite metric like this. 

---

# The three components

## 1. Capacity response

Use:

[
\Delta C_i(f)
=============

C_i(\text{photic }f)-C_i(\text{baseline})
]

where:

[
C = \text{d-block tube_d_eff_median}
]

Why d-block? Because your dementia work already suggests that dementia effects can be weak in global 3D but clearer in stratified d-family/block-cone geometry. The reachability report specifically notes near-null global 3D cone metrics in dementia, while stratified block-cones show robust d-block differences for AD/FTD versus healthy controls. 

Interpretation:

> Does photic stimulation open the local reachable future-space in the expected way?

---

## 2. Guidance response

Use:

[
\Delta R_i(f)
=============

R_i(\text{photic }f)-R_i(\text{baseline})
]

where:

[
R = \text{rotational_power_mean}
]

or, if using reachability-cone notation:

[
R = \rho_A
]

Interpretation:

> Does the evoked response have organized local dynamical structure, or is it just dispersion?

This is important because a pathological system may still “react” strongly but without coherent guidance.

---

## 3. Recovery / hysteresis

Use:

[
H_i(f)
======

\left|
z_i(\text{recovery})-z_i(\text{baseline})
\right|
]

where (z) can be just the two-dimensional vector:

[
z=[C,R]
]

So:

[
H_i(f)
======

\sqrt{
\left(C_i(\text{recovery})-C_i(\text{baseline})\right)^2
+
\left(R_i(\text{recovery})-R_i(\text{baseline})\right)^2
}
]

Interpretation:

> After stimulation, does the system return to baseline geometry?

This gives you the “old rubber” idea without introducing a large extra machinery.

---

# Even simpler: ESB-2

If you want the absolute minimum:

[
r_i(f)=
[
\Delta C_i(f),
\Delta R_i(f)
]
]

[
ESB2_i(f)
=========

\frac{1}{\sqrt{2}}
\left|
\frac{
r_i(f)-h_f
}{
s_f+\epsilon
}
\right|_2
]

Then report recovery separately as:

[
H_i(f)
]

This may actually be the most reviewer-safe version.

Main metric:

> **ESB-2: healthy-template deviation in capacity–guidance space.**

Secondary metric:

> **Hysteresis: post-stimulus residual deformation.**

That avoids bundling too much into one scalar.

---

# My recommendation

For the current paper, I would use:

## Primary exploratory metric

[
\boxed{
ESB2_i(f)
=========

\frac{1}{\sqrt{2}}
\sqrt{
\left(
\frac{\Delta C_i(f)-\mathrm{median}*{HC}(\Delta C_f)}
{\mathrm{MAD}*{HC}(\Delta C_f)+\epsilon}
\right)^2
+
\left(
\frac{\Delta R_i(f)-\mathrm{median}*{HC}(\Delta R_f)}
{\mathrm{MAD}*{HC}(\Delta R_f)+\epsilon}
\right)^2
}
}
]

with:

[
C=\text{d-block tube_d_eff_median}
]

[
R=\text{rotational_power_mean}
]

Then separately:

[
H_i(f)
======

\left|
[C_i(\text{recovery}),R_i(\text{recovery})]
-------------------------------------------

[C_i(\text{baseline}),R_i(\text{baseline})]
\right|
]

This is clean.

It says:

> ESB-2 measures whether the subject’s photic response deviates from the healthy response in a two-axis space of evoked capacity and evoked dynamical guidance. Hysteresis is reported separately as recovery failure.

---

# Why not use cosine anymore?

I would drop cosine similarity in the simplified version.

Cosine is elegant, but with only 29 healthy controls and noisy EEG, it creates reviewer questions:

* Is the healthy vector direction stable?
* What happens if the vector norm is small?
* Is orthogonality meaningful in this feature space?
* Are you comparing direction or magnitude?

Euclidean deviation after robust HC scaling is much easier:

[
\text{distance from healthy response}
]

Everyone understands it.

---

# What phenotypes remain visible?

Even with ESB-2 + H, you still keep the core biology.

| Phenotype        |       (\Delta C) |       (\Delta R) |           (H) | Interpretation                         |
| ---------------- | ---------------: | ---------------: | ------------: | -------------------------------------- |
| Healthy          | near HC template | near HC template |           low | adaptive evoked deformation            |
| AD blunted       |      low / wrong |              low | moderate/high | weak opening and weak guidance         |
| FTD misorganized | high or abnormal | wrong / unstable |          high | strong but misdirected deformation     |
| Severe collapse  |              low |              low |          high | no adaptive response and poor recovery |

So the concept survives, but the math becomes much cleaner.

---

# Paper-facing wording

I would write it like this:

> To avoid overfitting a high-dimensional composite, we define a minimal exploratory Evoked Structural Brittleness score in a two-dimensional response space. For each stimulation frequency, we quantify each subject’s baseline-to-photic change in d-block reachable effective dimensionality and rotational dynamical structure. ESB-2 is the robust Euclidean distance between this subject-level response vector and the healthy-control median response vector at the same frequency, scaled by the healthy-control MAD. Recovery hysteresis is reported separately as the post-stimulation residual distance from baseline in the same two-dimensional space.

That is the version I would actually put in the current article.

Final simplified structure:

[
\boxed{
\text{ESB-2} = \text{abnormal evoked capacity–guidance response}
}
]

[
\boxed{
\text{Hysteresis} = \text{failure to return}
}
]

Together, they capture collapse without becoming a kitchen-sink metric.
