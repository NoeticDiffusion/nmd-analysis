# Higher-Order Geometry TACs for Cardiac-Arrest Coma

## Scope

This note defines exploratory geometric TACs (testable analytic candidates) for separating later `CPC 1` from later `CPC 5` after cardiac-arrest coma. The framing is deliberately dynamical/geometric rather than clinical: the question is whether coma outcome is better described by the shape and temporal deformation of local operator fields, reachability ellipsoids, and cone bundles than by static state-space position alone.

These candidates are speculative until run against frozen bundles. They should be treated as exploratory geometry features, not as validated biomarkers.

## Shared Notation

Let

$$
x_t \in \mathbb{R}^d
$$

be the exported MNPS or stratified MNPS state at window `t`, with `d = 3` for the base chart or `d = 9` for the repaired stratified chart.

Let

$$
J_t = \frac{\partial f}{\partial x}(x_t,t) \in \mathbb{R}^{d \times d}
$$

be the local Jacobian of the fitted flow, and let

$$
\Sigma_t^{(h)}
$$

be the reachability covariance at horizon `h`. When no horizon is written explicitly, use the article-facing terminal or aggregated horizon:

$$
\Sigma_t = \Sigma_t^{(H)}.
$$

For numerical stability, all normalized ratios use

$$
\varepsilon > 0.
$$

Patient-level features should usually be summarized as median, p95, and robust dispersion across valid windows:

$$
M_\mathrm{patient} = \operatorname{median}_t M_t,
\qquad
M_{\mathrm{p95,patient}} = \operatorname{quantile}_{0.95,t} M_t.
$$

## TAC 1: Jacobian Velocity / MDR

The current `mdr_median` is already a first higher-order object. It measures the speed of change of the local dynamics rule:

$$
\dot{J}_t \approx \frac{J_{t+1} - J_{t-1}}{2\Delta t}
$$

and

$$
\mathrm{MDR}_t =
\frac{\lVert \dot{J}_t \rVert_F}
{\lVert J_t \rVert_F + \varepsilon}.
$$

Patient summary:

$$
\mathrm{MDR}_{\mathrm{med}} =
\operatorname{median}_t(\mathrm{MDR}_t).
$$

### Rationale

Static Jacobian summaries ask whether the local flow is large, anisotropic, or rotational at a given window. MDR asks whether the local flow rule itself is changing. This may separate outcome groups if later `CPC 1` retains adaptive reconfiguration while later `CPC 5` is either rigidly locked or pathologically unstable.

The current 9D article already finds `mdr_median` directionally separated, but weaker than spectral radius and Frobenius scale. That makes it a useful anchor: new higher-order TACs should improve on MDR or explain why MDR is only a partial proxy.

## TAC 2: Jacobian Acceleration

The next derivative asks whether the velocity of the local operator field is itself changing:

$$
\ddot{J}_t \approx
\frac{J_{t+1} - 2J_t + J_{t-1}}{\Delta t^2}.
$$

Define normalized Jacobian acceleration:

$$
A^J_t =
\frac{\lVert \ddot{J}_t \rVert_F}
{\lVert \dot{J}_t \rVert_F + \varepsilon}.
$$

Alternative scale-normalized version:

$$
\tilde{A}^J_t =
\frac{\lVert \ddot{J}_t \rVert_F}
{\lVert J_t \rVert_F + \varepsilon}.
$$

Patient summaries:

$$
A^J_{\mathrm{med}} =
\operatorname{median}_t(A^J_t),
\qquad
A^J_{\mathrm{p95}} =
\operatorname{quantile}_{0.95,t}(A^J_t).
$$

### Rationale

Two subjects can have similar `MDR` but differ in whether Jacobian change is smooth or burst-like. `CPC 1` may preserve controlled remodeling: moderate `dot(J)` with low acceleration. `CPC 5` may show abrupt operator jumps caused by unstable collapse, artifact-sensitive bursts, or pathological transitions. Conversely, a very low acceleration in `CPC 5` after low reachability may indicate rigid lock-in.

This TAC can therefore separate at least two geometrically distinct bad-outcome modes:

1. frozen low-capacity dynamics,
2. unstable high-curvature operator switching.

Both can be missed by static spectral radius alone.

## TAC 3: Jacobian Jerk

The third derivative measures abrupt change in Jacobian acceleration:

$$
J^{(3)}_t \approx
\frac{J_{t+2} - 3J_{t+1} + 3J_t - J_{t-1}}{\Delta t^3}.
$$

Define normalized Jacobian jerk:

$$
K^J_t =
\frac{\lVert J^{(3)}_t \rVert_F}
{\lVert \ddot{J}_t \rVert_F + \varepsilon}.
$$

Scale-normalized companion:

$$
\tilde{K}^J_t =
\frac{\lVert J^{(3)}_t \rVert_F}
{\lVert J_t \rVert_F + \varepsilon}.
$$

### Rationale

Jerk is a candidate for detecting discontinuous or near-discontinuous reorganization of the local flow rule. If `CPC 5` contains intermittent collapse/release episodes, jerk may capture them better than median spectral radius, because median scale suppresses rare but important deformation events.

This is the noisiest TAC in this note. It should only be used after temporal smoothing or local polynomial fitting:

$$
J_t \approx B_0 + B_1 \tau + B_2 \tau^2 + B_3 \tau^3,
$$

where the derivative estimates are taken from the fitted coefficients rather than raw finite differences.

## TAC 4: Jacobian Path Curvature

Instead of treating `J_t` as separate matrices, treat the sequence as a curve in matrix space. A simple Euclidean version is:

$$
v_t = J_{t+1} - J_t,
\qquad
a_t = J_{t+1} - 2J_t + J_{t-1}.
$$

Flatten matrices with `vec`. The curvature of the Jacobian path is:

$$
\kappa^J_t =
\frac{
\sqrt{
\lVert v_t \rVert_F^2 \lVert a_t \rVert_F^2
- \langle v_t, a_t \rangle_F^2
}
}
{(\lVert v_t \rVert_F + \varepsilon)^3}.
$$

Here

$$
\langle A,B \rangle_F = \operatorname{tr}(A^\top B).
$$

### Rationale

MDR measures how fast the operator moves. Path curvature measures whether the operator keeps moving in the same direction or bends through matrix space. This can distinguish:

- coherent adaptive drift: smoother low-curvature operator path,
- pathological wandering: high-curvature operator path,
- rigid lock-in: low speed and low curvature.

This may improve CPC separation because recovery may depend not only on having low local expansion, but on having a stable direction of reconfiguration.

## TAC 5: Symmetric-Skew Decomposition Dynamics

Decompose the Jacobian into symmetric deformation and skew rotational parts:

$$
S_t = \frac{1}{2}(J_t + J_t^\top),
\qquad
\Omega_t = \frac{1}{2}(J_t - J_t^\top).
$$

Define deformation and rotation velocities:

$$
V^S_t =
\frac{\lVert \dot{S}_t \rVert_F}
{\lVert S_t \rVert_F + \varepsilon},
\qquad
V^\Omega_t =
\frac{\lVert \dot{\Omega}_t \rVert_F}
{\lVert \Omega_t \rVert_F + \varepsilon}.
$$

Define a rotation/deformation reconfiguration ratio:

$$
R^{\Omega/S}_t =
\frac{V^\Omega_t}
{V^S_t + \varepsilon}.
$$

### Rationale

The 9D article already shows rotational-power signals, but those are mostly static eigenvalue summaries. This TAC asks whether rotational structure is changing faster than deformation structure.

Potential separation logic:

- later `CPC 1`: lower pathological expansion, possibly smoother and more coordinated rotation/deformation balance,
- later `CPC 5`: disproportionate rotational reconfiguration or collapse of rotational adaptability.

This is especially relevant because rotational-power signals were pooled-promoted but weaker than spectral radius. Their temporal dynamics may carry information that their static magnitude does not.

## TAC 6: SPD Reachability Velocity

Reachability covariances live on the manifold of symmetric positive-definite matrices:

$$
\Sigma_t \in \mathrm{SPD}(d).
$$

A log-Euclidean velocity is:

$$
L_t = \log(\Sigma_t + \epsilon I),
$$

$$
V^\Sigma_t =
\frac{\lVert L_{t+1} - L_t \rVert_F}
{\Delta t + \varepsilon}.
$$

The Bures-Wasserstein version is:

$$
V^{BW}_t =
\frac{d_{BW}(\Sigma_{t+1}, \Sigma_t)}
{\Delta t + \varepsilon},
$$

with

$$
d_{BW}^2(A,B)
=
\operatorname{tr}(A) + \operatorname{tr}(B)
- 2\operatorname{tr}\left((A^{1/2}BA^{1/2})^{1/2}\right).
$$

### Rationale

This is the cleanest continuation of the Surface B result. Static reachability asks how large or high-dimensional the local future cloud is. SPD velocity asks how rapidly the future cloud changes shape.

Possible CPC separation:

- later `CPC 1`: reachable set remains open and can remodel coherently,
- later `CPC 5`: reachable set is either compressed and static, or deforms sharply around a narrowed pathological channel.

Surface B pilot results already suggest that reachability covariance deformation has outcome signal, especially in p95 tails and Bures/log-Euclidean summaries.

## TAC 7: SPD Reachability Acceleration

Using the log-Euclidean path:

$$
A^\Sigma_t =
\frac{\lVert L_{t+1} - 2L_t + L_{t-1} \rVert_F}
{\Delta t^2 + \varepsilon}.
$$

Normalized version:

$$
\tilde{A}^\Sigma_t =
\frac{
\lVert L_{t+1} - 2L_t + L_{t-1} \rVert_F
}
{
\lVert L_t \rVert_F + \varepsilon
}.
$$

Bures-distance acceleration can be approximated by change in Bures velocity:

$$
A^{BW}_t =
\frac{
\left|
d_{BW}(\Sigma_{t+1},\Sigma_t)
- d_{BW}(\Sigma_t,\Sigma_{t-1})
\right|
}
{\Delta t^2 + \varepsilon}.
$$

### Rationale

Velocity of `Sigma_t` captures deformation rate. Acceleration captures whether deformation is smooth or abruptly changing. This may better separate CPC groups when both have nonzero reachability deformation but differ in regularity.

Hypothesis:

- `CPC 1` may show lower acceleration relative to velocity, consistent with smoother adaptive remodeling.
- `CPC 5` may show higher acceleration in p95 tails, consistent with punctuated collapse, unstable reopening, or estimator-visible deformation around low-dimensional geometry.

## TAC 8: Cone-Field Twist via Principal Angles

Let `U_t^(k)` contain the top `k` eigenvectors of `Sigma_t`:

$$
\Sigma_t U_t^{(k)} = U_t^{(k)} \Lambda_t^{(k)}.
$$

The principal angles between consecutive reachable subspaces are:

$$
\theta_i(t) =
\arccos \sigma_i\left((U_t^{(k)})^\top U_{t+1}^{(k)}\right),
$$

where `sigma_i` are singular values.

Define cone-field twist:

$$
T^\mathrm{cone}_t =
\left(
\sum_{i=1}^{k} \theta_i(t)^2
\right)^{1/2}.
$$

Spatial version for neighboring centers `p` and `q`:

$$
T^\mathrm{cone}_{p,q} =
\left(
\sum_{i=1}^{k}
\arccos^2
\sigma_i\left((U_p^{(k)})^\top U_q^{(k)}\right)
\right)^{1/2}.
$$

### Rationale

Reachability volume and effective dimension can be similar while the direction of reachable futures differs. Cone-field twist asks whether the admissible future directions rotate coherently or erratically.

Potential separation:

- later `CPC 1`: broader reachable subspace with coherent directional transport,
- later `CPC 5`: narrow and unstable reachable directions, or strong canalization into a few repeatedly changing axes.

This could add information beyond `tube_d_eff_median`, because it measures orientation dynamics rather than size.

## TAC 9: Cone-Field Torsion

A discrete torsion-like measure asks whether changes in reachable direction themselves change direction. Let

$$
\Delta U_t = \operatorname{Proj}(U_{t+1}^{(k)}) - \operatorname{Proj}(U_t^{(k)}),
$$

where

$$
\operatorname{Proj}(U) = UU^\top.
$$

Then define

$$
\tau^\mathrm{cone}_t =
\frac{
\lVert \Delta U_t - \Delta U_{t-1} \rVert_F
}
{
\lVert \Delta U_{t-1} \rVert_F + \varepsilon
}.
$$

### Rationale

Twist measures rotation of reachable directions. Torsion measures whether that rotation is itself stable or twisting unpredictably.

This may matter because coma might not only reduce reachable capacity; it may distort the transport frame. A patient can retain some reachability but lose stable directional organization. That would appear as higher cone torsion even if volume or effective dimensionality is only moderately changed.

## TAC 10: 9D Block-Jacobian Shear Flux

In the repaired 9D chart, group the Jacobian into `m`, `d`, and `e` family blocks:

$$
J_t^{(9)} =
\begin{bmatrix}
J_{m \leftarrow m} & J_{m \leftarrow d} & J_{m \leftarrow e} \\
J_{d \leftarrow m} & J_{d \leftarrow d} & J_{d \leftarrow e} \\
J_{e \leftarrow m} & J_{e \leftarrow d} & J_{e \leftarrow e}
\end{bmatrix}.
$$

Define the block energy matrix:

$$
B_{ab}(t) =
\lVert J_{a \leftarrow b}(t) \rVert_F,
\qquad
a,b \in \{m,d,e\}.
$$

Define block shear flux:

$$
\dot{B}_{ab}(t)
\approx
\frac{B_{ab}(t+1) - B_{ab}(t-1)}
{2\Delta t}.
$$

Cross-family flux:

$$
F^\mathrm{cross}_t =
\sum_{a \neq b} |\dot{B}_{ab}(t)|.
$$

Within-family flux:

$$
F^\mathrm{within}_t =
\sum_{a=b} |\dot{B}_{ab}(t)|.
$$

Cross/within shear ratio:

$$
R^\mathrm{block}_t =
\frac{F^\mathrm{cross}_t}
{F^\mathrm{within}_t + \varepsilon}.
$$

### Rationale

The 9D chart may reveal reconfiguration that is invisible in global 3D summaries. If coma outcome depends on whether subfamilies can still coordinate, then cross-family block flux may be more informative than whole-matrix Frobenius scale.

Hypothesis:

- later `CPC 1`: preserved cross-family coordination with bounded operator scale,
- later `CPC 5`: either excessive cross-family shear, indicating unstable coupling, or suppressed cross-family flux, indicating modular lock-in.

This TAC is especially attractive because it uses the repaired 9D structure rather than treating the 9D Jacobian as an undifferentiated matrix.

## TAC 11: Operator-Conditioned Reachability Deformation

This TAC asks whether reachability deformation remains after conditioning on local Jacobian scale.

First fit, at subject level:

$$
G^\Sigma_i =
\beta_0
+ \beta_1 \rho^J_i
+ \beta_2 F^J_i
+ \beta_3 d_{\mathrm{eff},i}
+ \epsilon_i,
$$

where `G_i^Sigma` is an SPD deformation metric, `rho_i^J` is spectral radius, `F_i^J` is Frobenius norm, and `d_eff` is reachability effective dimensionality.

The residual feature is:

$$
G^{\Sigma,\perp}_i =
G^\Sigma_i
-
\widehat{G^\Sigma_i}.
$$

### Rationale

Many geometry metrics will separate CPC1/CPC5 simply because CPC5 has larger Jacobian scale or smaller reachability. Residualized deformation asks a stricter question: among patients with comparable local-linear scale and reachable dimensionality, does the geometry still deform differently?

If yes, the TAC is more likely to represent a genuinely new geometric layer rather than a relabeled severity proxy.

## TAC 12: Time-Shuffled Higher-Order Null

For any higher-order metric `M`, define a time-shuffled control by permuting window order within subject:

$$
\pi_i : \{1,\dots,T_i\} \rightarrow \{1,\dots,T_i\}
$$

and recomputing

$$
M^{\mathrm{shuffle}}_i =
M(J_{\pi_i(t)}, \Sigma_{\pi_i(t)}).
$$

The temporal specificity score is:

$$
Z^\mathrm{time}_i =
\frac{
M_i - \mu(M^{\mathrm{shuffle}}_i)
}
{
\sigma(M^{\mathrm{shuffle}}_i) + \varepsilon
}.
$$

### Rationale

Acceleration, jerk, curvature, and torsion are vulnerable to noise and irregular sampling. A time-shuffled null tests whether the metric depends on real temporal order rather than only on the marginal distribution of matrices.

This is essential before interpreting higher-order TACs biologically.

## Why These TACs May Improve CPC1/CPC5 Separation

The validated coma geometry results already show that later `CPC 1` tends to have lower local-linear scale and broader/less captured reachability than later `CPC 5`. The TACs above ask additional questions that static metrics cannot answer:

1. **Rule-change geometry:** `dot(J)`, `ddot(J)`, and `J^(3)` measure whether the local dynamics rules are smoothly adapting, abruptly switching, or frozen.
2. **Path geometry:** Jacobian path curvature measures whether the operator evolves coherently through matrix space rather than merely moving fast.
3. **Ellipsoid-manifold geometry:** SPD velocity and acceleration measure how the reachable future set changes shape on its natural manifold.
4. **Orientation geometry:** cone twist and torsion measure whether reachable directions remain organized, independent of reachable volume.
5. **9D family geometry:** block shear flux tests whether mechanism-specific subfamilies remain coordinated or become locked/cross-coupled.
6. **Residual geometry:** conditioning on spectral radius, Frobenius norm, and `d_eff` tests whether a candidate adds signal beyond already validated severity-linked geometry.

The best-case pattern would not simply be "larger is worse" or "smaller is better." A stronger result would show a structured dissociation:

$$
\text{CPC 1}:
\quad
\text{lower operator scale}
+ \text{broader reachability}
+ \text{smoother remodeling}
+ \text{coherent cone orientation}
$$

versus

$$
\text{CPC 5}:
\quad
\text{higher operator scale}
+ \text{narrower reachability}
+ \text{abrupt or frozen remodeling}
+ \text{unstable/canalized cone orientation}.
$$

That dissociation would justify a geometric coma model in which outcome is linked not only to how much local capacity remains, but to whether the system can reshape its own future-state geometry in a controlled way.

## Minimal Pilot Recommendation

Run a small frozen pilot using existing `J_hat`, `J_dot`, and reachability covariance exports:

1. Estimate smoothed `ddot(J)` and, only if stable, `J^(3)`.
2. Compute log-Euclidean and Bures SPD velocity/acceleration of `Sigma_t`.
3. Compute cone twist from leading eigenspaces of `Sigma_t`.
4. Compute 9D block shear flux where repaired 9D Jacobians are available.
5. Report raw CPC1/CPC5 contrasts.
6. Residualize candidates against spectral radius, Frobenius norm, and `tube_d_eff_median`.
7. Run time-shuffled and subject-label permutation controls.

Only TACs surviving steps 5-7 should be promoted into a manuscript-facing candidate family.
