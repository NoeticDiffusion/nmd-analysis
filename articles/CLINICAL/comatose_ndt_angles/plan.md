Yes—this is a good, mathematically clean extension, and **turning angles can be computed in 9D just as well as in 3D**.

The current psychosis manuscript says that trajectory curvature was included among the generic first-order descriptors, but the reported psychosis results were dominated by location, dispersion, delta dynamics, and Jacobian measures. I do not see evidence that the distribution of explicit three-point turning angles was treated as a dedicated endpoint. So this appears to be a genuinely new analysis, although related to the existing curvature metric. 

## 1. Three-point angles in any dimension

For three consecutive MNPS points,

[
x_{t-1},\quad x_t,\quad x_{t+1}\in\mathbb{R}^D,
]

define the incoming and outgoing displacement vectors:

[
u_t=x_t-x_{t-1},
\qquad
v_t=x_{t+1}-x_t.
]

The turning angle is

[
\theta_t=
\arccos
\left(
\frac{u_t^\top v_t}
{|u_t|,|v_t|}
\right),
\qquad
0\leq\theta_t\leq\pi.
]

This formula works for (D=3), (D=9), or any other dimension.

Interpretation:

* (0^\circ): continued movement in approximately the same direction.
* (90^\circ): strong redirection into an orthogonal direction.
* (180^\circ): reversal or backtracking.

For numerical work, I would primarily store

[
T_t=1-\cos(\theta_t)
====================

1-\frac{u_t^\top v_t}{|u_t|,|v_t|},
]

rather than only (\theta_t). It is more numerically stable:

* (T=0): straight continuation.
* (T=1): orthogonal redirection.
* (T=2): complete reversal.

## 2. Your psychosis hypothesis

Your intuition can be stated as:

> **Plausible interpretation:** resting FEP trajectories undergo less directionally persistent and more abrupt local reorientation than healthy-control trajectories.

The direct prediction would be:

[
\operatorname{median}(\theta)_{\mathrm{FEP}}

>

\operatorname{median}(\theta)_{\mathrm{Healthy}},
]

or equivalently

[
\mathbb{E}[\cos\theta]*{\mathrm{FEP}}
<
\mathbb{E}[\cos\theta]*{\mathrm{Healthy}}.
]

I would not yet call this an NDT prediction. It is a **new exploratory geometric hypothesis**. Larger angles could indicate unstable switching or disorganized trajectory guidance, but they could also arise from measurement noise, very small movements, oscillatory reversals, or genuine exploration.

The most plausible place to see it is probably **ds003947 unmedicated FEP versus Healthy**, because that cohort’s strongest corrected result already appeared in trajectory dynamics rather than static state-space location. In contrast, ds003944 medicated FEP was mainly separated by relatively stable (m)-axis displacement, which does not necessarily imply sharper turning. 

So my tentative prediction would be:

* **ds003947, unmedicated FEP:** larger or more heavy-tailed angles.
* **ds003944, medicated FEP:** possibly unchanged median angle despite shifted occupancy.
* **Medication pooling:** likely to dilute the effect, as it already diluted the main ds003947 dynamic result.

## 3. The important 9D complication

The problem with 9D is not that angles cannot be calculated. The problem is **angle concentration**.

As dimensionality increases, unrelated or random vectors tend to be nearly orthogonal. In 9D, even a trajectory with weak serial structure may naturally produce many angles near (90^\circ). Therefore:

> A raw 9D median angle of (88^\circ) versus (85^\circ) is difficult to interpret without a trajectory-specific null.

The 9D chart is also a structured decomposition, not nine independent physiological axes. Its dimensions have different variances and correlations, and some recombine into the same 3D families. 

I would therefore compute two 9D versions.

### Euclidean 9D angle

Use the existing standardized, fixed-contract coordinates directly:

[
\cos\theta_t^{(9)}
==================

\frac{u_t^\top v_t}
{|u_t||v_t|}.
]

This is the simplest and should be the primary contract-preserving analysis.

### Metric-adjusted 9D angle

As a sensitivity analysis:

[
\cos\theta_{t,G}
================

\frac{u_t^\top Gv_t}
{\sqrt{u_t^\top Gu_t}\sqrt{v_t^\top Gv_t}},
]

where (G) could be a shrinkage inverse covariance estimated from the pooled or healthy-reference 9D trajectory.

This asks whether the redirection remains after accounting for correlated and unequal coordinate scales. The metric must be fixed across groups; whitening each subject separately could remove the very group structure being tested.

## 4. Better than only comparing mean angles

For each subject, I would export:

| Metric                   | Interpretation                                       |
| ------------------------ | ---------------------------------------------------- |
| `turn_cos_mean`          | directional persistence                              |
| `turn_angle_median`      | typical redirection                                  |
| `turn_angle_iqr` / `mad` | variability of redirection                           |
| `turn_angle_p90`         | extreme turns                                        |
| `turn_fraction_gt_90`    | frequent orthogonal/backward changes                 |
| `turn_fraction_gt_120`   | strong reversals                                     |
| `turn_entropy`           | diversity of turning regimes                         |
| `turn_length_coupling`   | whether large turns occur during large or tiny steps |

The upper tail may be more informative than the mean. Psychosis might not make every turn larger; it might produce **intermittent abrupt redirections**, visible as increased (p_{90}), MAD, or reversal fraction.

## 5. Essential protection against false effects

Angles become unstable when one displacement is almost zero:

[
|u_t|\approx0
\quad\text{or}\quad
|v_t|\approx0.
]

Tiny random fluctuations can then produce an apparently arbitrary large angle. I would therefore:

1. Exclude angles where either adjacent step length is below a pre-specified threshold, such as the pooled 10th percentile.
2. Report how many angles remain per subject.
3. Analyse turning jointly with speed.
4. Require the effect to survive a matched-step analysis, comparing FEP and control angles at similar step-length distributions.

This distinction is central:

* **Large angle + substantial movement:** meaningful trajectory redirection.
* **Large angle + near-zero movement:** jitter around one location.
* **Large angle + alternating reversal:** oscillatory backtracking.
* **Large angle + high speed:** abrupt state switching.

## 6. Use more than one temporal lag

Because consecutive MNPS windows overlap, the three-point angle at lag 1 may partly reflect window construction.

For EEG with an approximately four-second MNPS step, I would calculate:

[
u_t^{(\ell)}=x_t-x_{t-\ell},
\qquad
v_t^{(\ell)}=x_{t+\ell}-x_t
]

for:

* (\ell=1): local turning.
* (\ell=2): medium-scale turning.
* (\ell=4): broader trajectory redirection.

A genuine group effect should ideally preserve its direction over at least two lags. An effect present only at lag 1 would be suspicious for overlapping-window noise.

## 7. Subject-specific temporal null

This is especially important for 9D.

Within each subject, preserve all displacement vectors and their lengths, but randomly permute their temporal order. Then compute the shuffled turning-angle distribution.

Define:

[
Z_{\theta,s}
============

\frac{
\operatorname{median}(\theta_s^{\mathrm{observed}})
---------------------------------------------------

\mathbb{E}*{\mathrm{shuffle}}
[\operatorname{median}(\theta_s^{\mathrm{null}})]
}{
\operatorname{SD}*{\mathrm{shuffle}}
[\operatorname{median}(\theta_s^{\mathrm{null}})]
}.
]

This tests whether a subject’s trajectory is more or less directionally organized than expected from its own displacement repertoire.

The stronger psychosis hypothesis is then not merely:

[
\theta_{\mathrm{FEP}}>\theta_{\mathrm{Healthy}},
]

but:

[
Z_{\theta,\mathrm{FEP}}>Z_{\theta,\mathrm{Healthy}},
]

meaning that FEP trajectories show **excess redirection beyond their own step-length and dimensionality baseline**.

## 8. Recommended analysis hierarchy

I would run the following as one compact exploratory batch:

1. **3D MNPS turning:** primary interpretable analysis.
2. **9D MNPS turning:** higher-resolution secondary analysis.
3. **Family-specific 3D turning:**

   * (m_*=[m_a,m_e,m_o])
   * (d_*=[d_n,d_l,d_s])
   * (e_*=[e_e,e_s,e_m])
4. **Metric-adjusted 9D:** robustness only.
5. **Lag sensitivity:** (\ell=1,2,4).
6. **Increment-permutation nulls.**
7. **Medication-stratified contrasts in both cohorts.**

The family-specific angles may be particularly valuable. They would tell us whether excess turning occurs mainly within metastability structure, diffusion structure, or entropy structure, rather than producing one opaque 9D scalar.

## Scientific status before running it

* **Established mathematical result:** turning angles are well-defined in 3D and 9D.
* **Internal project result:** curvature-like trajectory descriptors already exist, but an explicit angle-distribution analysis does not appear to have been promoted as a psychosis endpoint. 
* **Plausible interpretation:** psychosis may involve reduced directional persistence and a heavier tail of abrupt turns.
* **Speculative extension:** larger angles may operationalize disorganized or weakly guided noetic flow.
* **Falsification condition:** no replicated angle effect across the two cohorts, or effects that disappear after step-length filtering, lag sensitivity, or increment-shuffle normalization.

My recommendation is to treat **3D null-normalized turning persistence as the primary endpoint**, with **9D and the three family subspaces as localization and sensitivity analyses**. This is small, falsifiable, and unusually well matched to the difference already seen between static ds003944 effects and dynamic ds003947 effects.
