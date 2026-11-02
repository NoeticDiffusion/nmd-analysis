Yes. Below is essentially the same answer, but with the mathematical objects written explicitly. I’ll also sharpen one part that matters for the **new orthogonal axes**: we can now distinguish diffusion **along the local drift** from diffusion **orthogonal to it**.

The central prediction remains:

> **Recovery-linked coma should be characterized by a broader and less canalized local accessibility geometry, while simultaneously having less explosively unstable deterministic dynamics and a greater probability of transitioning toward recovery-compatible neural regimes.**

That is much more specific than “CPC1 has more dynamics.”

---

# 1. Starting point: the new local stochastic decomposition

Write the measured MNPS dynamics locally as

$$
dX_t
=
b(X_t,t)\,dt
+
\Sigma(X_t,t)\,dW_t ,
$$

where

$$
X_t\in\mathbb{R}^{d}
$$

is the MNPS state, normally \(d=3\) or \(d=9\),

$$
b(x,t)
=
\mathbb{E}\left[
\frac{X_{t+\Delta t}-X_t}{\Delta t}
\mid X_t=x
\right]
$$

is the local deterministic drift, and

$$
a(x,t)
=
\Sigma(x,t)\Sigma(x,t)^{T}
$$

is the local diffusion tensor.

Empirically,

$$
\hat b(x)
\approx
\frac{1}{\Delta t}
\mathbb{E}[\Delta X_t\mid X_t\approx x],
$$

and

$$
\hat a(x)
\approx
\frac{1}{\Delta t}
\operatorname{Cov}[\Delta X_t\mid X_t\approx x].
$$

This is precisely the distinction the newer NDT layer needs: **the deterministic vector field and the stochastic accessibility geometry are different objects**. 

---

# 2. Why I-CARE is already pointing toward this decomposition

Our existing corrected I-CARE result has an interesting combination.

For CPC1 versus CPC5 during 0–12 h:

$$
d_{\mathrm{eff}}^{\mathrm{reach}}
:
2.912
>
2.470
$$

with

$$
d=+0.638,
$$

while simultaneously the local Jacobian was **smaller** in CPC1:

$$
\rho(J)_{\mathrm{CPC1}}
<
\rho(J)_{\mathrm{CPC5}}
$$

with approximately

$$
d=-0.536,
$$

and likewise

$$
\|J\|_F{}_{\mathrm{CPC1}}
<
\|J\|_F{}_{\mathrm{CPC5}}.
$$



So:

$$
\boxed{
\text{CPC1}
=
\text{greater reachable dimensionality}
+
\text{smaller local deformation}
}
$$

That is not contradictory.

It suggests that **reachable richness may be coming from the geometry of the innovations/diffusion rather than from an unstable deterministic operator**.

---

# 3. Prediction 1: diffusion effective dimensionality should be larger in CPC1

Let

$$
a
=
V\Lambda V^{T}
$$

with eigenvalues

$$
\lambda_1\geq \lambda_2\geq \ldots\geq\lambda_d\geq0.
$$

Total diffusion power is simply

$$
D_{\mathrm{tot}}
=
\operatorname{Tr}(a)
=
\sum_{i=1}^{d}\lambda_i .
$$

But I **would not make \(D_{\mathrm{tot}}\) the primary prediction**.

A very noisy pathological system might also have large total variance.

The more interesting quantity is diffusion effective dimensionality:

$$
\boxed{
d_{\mathrm{eff}}^{(a)}
=
\frac{
\left(\sum_i\lambda_i\right)^2
}{
\sum_i\lambda_i^2
}
}
$$

For a 3D system:

$$
1
\leq
d_{\mathrm{eff}}^{(a)}
\leq
3.
$$

If

$$
\lambda_1\gg\lambda_2,\lambda_3,
$$

then

$$
d_{\mathrm{eff}}^{(a)}
\rightarrow 1,
$$

meaning fluctuations are essentially confined to one local direction.

If

$$
\lambda_1\approx\lambda_2\approx\lambda_3,
$$

then

$$
d_{\mathrm{eff}}^{(a)}
\rightarrow3.
$$

### Prediction

$$
\boxed{
d_{\mathrm{eff}}^{(a)}
(\mathrm{CPC1})
>
d_{\mathrm{eff}}^{(a)}
(\mathrm{CPC5})
}
$$

This would mean better-outcome brains retain **more independent locally accessible directions**.

That interpretation is compatible with independent coma work. Kustermann et al. found richer functional-network dynamics in favorable-outcome patients, while Keijzer et al. found reduced dynamic functional connectivity in poor-outcome patients. ([PubMed][1])

Those papers do not test NDT diffusion tensors, but they support the more general external proposition that favorable recovery is associated with a richer dynamical repertoire.

---

# 4. A second measure: diffusion entropy

Normalize the diffusion eigenvalues:

$$
p_i
=
\frac{\lambda_i}
{\sum_j\lambda_j+\epsilon}.
$$

Then define

$$
H_a
=
-\sum_i
p_i\log p_i
$$

and normalized diffusion entropy

$$
\boxed{
\widetilde H_a
=
\frac{H_a}{\log d}
}
$$

so that approximately

$$
0\leq\widetilde H_a\leq1.
$$

Low value:

$$
\widetilde H_a\approx0
$$

means a highly canalized diffusion direction.

High value:

$$
\widetilde H_a\approx1
$$

means the diffusion tensor supports several comparable directions.

### Prediction

$$
\boxed{
\widetilde H_a(\mathrm{CPC1})
>
\widetilde H_a(\mathrm{CPC5})
}
$$

I would expect this to tell approximately the same story as \(d_{\mathrm{eff}}^{(a)}\), but using a different functional of the eigenvalue spectrum.

---

# 5. The genuinely new orthogonal question: along the drift or across it?

This is especially interesting given our new orthogonal simulator work.

Take the normalized local drift direction

$$
\hat b
=
\frac{b}{\|b\|+\epsilon}.
$$

Construct the projector along the drift:

$$
P_{\parallel}
=
\hat b\hat b^{T}
$$

and the orthogonal projector

$$
\boxed{
P_{\perp}
=
I-P_{\parallel}.
}
$$

Then split the local diffusion tensor into drift-aligned and drift-orthogonal components.

### Drift-aligned diffusion

$$
\boxed{
D_{\parallel}
=
\hat b^{T}a\hat b
}
$$

### Orthogonal diffusion

$$
\boxed{
D_{\perp}
=
\operatorname{Tr}
(P_{\perp}aP_{\perp})
}
$$

and, because \(P_\perp\) is a projector,

$$
D_{\perp}
\approx
\operatorname{Tr}(a)-D_{\parallel}.
$$

We can normalize:

$$
f_{\parallel}
=
\frac{D_{\parallel}}
{\operatorname{Tr}(a)+\epsilon}
$$

and

$$
\boxed{
f_{\perp}
=
\frac{D_{\perp}}
{\operatorname{Tr}(a)+\epsilon}.
}
$$

Approximately,

$$
f_\parallel+f_\perp=1.
$$

---

# 6. What do I expect in coma?

Here I would make a **new but explicitly speculative** prediction.

### CPC5

A badly injured system may have activity, but its locally available fluctuations may be highly canalized:

$$
\lambda_1\gg\lambda_2,\lambda_3
$$

and/or disproportionately aligned with an already pathological drift:

$$
D_{\parallel}\gg D_{\perp}.
$$

Thus:

$$
d_{\mathrm{eff}}^{(a)}\downarrow ,
$$

$$
\widetilde H_a\downarrow ,
$$

$$
f_{\perp}\downarrow .
$$

That would be a system that can fluctuate but has few ways of **escaping its current trajectory**.

### CPC1

The recoverable system may instead retain appreciable innovation in directions not already dictated by its present drift:

$$
D_{\perp}\uparrow
$$

and therefore

$$
\boxed{
f_{\perp,\mathrm{CPC1}}
>
f_{\perp,\mathrm{CPC5}}.
}
$$

This is potentially very important.

It would mean that recovery is associated not simply with noise, but with **degrees of freedom transverse to the current flow**.

In intuitive terms:

> CPC5 may still move, but mostly along the groove it is already in.
> CPC1 retains ways of moving *out of* that groove.

That is exactly the kind of distinction the original MNPS/reachability layer could not make.

---

# 7. Connection to our existing reachability result

Our reachability model is

$$
X_{t+1}
=
A_tX_t+b_t+\varepsilon_t,
$$

where

$$
\varepsilon_t
\sim
\mathcal N(0,Q_t).
$$

The reachability covariance obeys

$$
\boxed{
\Sigma_t^{(h+1)}
=
A_t
\Sigma_t^{(h)}
A_t^{T}
+
Q_t
}
$$

with

$$
\Sigma_t^{(0)}=0.
$$



Now look at horizon one:

$$
\Sigma_t^{(1)}
=
Q_t.
$$

At horizon two:

$$
\Sigma_t^{(2)}
=
A_tQ_tA_t^T+Q_t.
$$

At horizon three:

$$
\Sigma_t^{(3)}
=
A_t^2Q_t(A_t^2)^T+
A_tQ_tA_t^T+
Q_t.
$$

More generally, in a locally stationary approximation,

$$
\boxed{
\Sigma^{(h)}
=
\sum_{k=0}^{h-1}
A^kQ(A^k)^T.
}
$$

This gives us an excellent experiment.

---

# 8. We can decompose the old I-CARE result into innovation versus propagation

Suppose CPC1 has greater effective reachability dimensionality:

$$
d_{\mathrm{eff}}^{\mathrm{reach}}
(\mathrm{CPC1})
>
d_{\mathrm{eff}}^{\mathrm{reach}}
(\mathrm{CPC5}).
$$

We can now ask **where it first appears**.

### Case A — already present at \(h=1\)

Because

$$
\Sigma^{(1)}=Q,
$$

if

$$
d_{\mathrm{eff}}^{(1)}
(\mathrm{CPC1})
>
d_{\mathrm{eff}}^{(1)}
(\mathrm{CPC5}),
$$

then the result is fundamentally an **innovation/diffusion geometry effect**.

That would support:

$$
\boxed{
\text{Recovery}
\rightarrow
\text{broader instantaneous innovation geometry}.
}
$$

### Case B — absent at \(h=1\), appears at \(h=4\)

If

$$
d_{\mathrm{eff}}^{(1)}
(\mathrm{CPC1})
\approx
d_{\mathrm{eff}}^{(1)}
(\mathrm{CPC5})
$$

but

$$
d_{\mathrm{eff}}^{(4)}
(\mathrm{CPC1})
>
d_{\mathrm{eff}}^{(4)}
(\mathrm{CPC5}),
$$

then diffusion itself is not the primary difference.

Instead the group distinction emerges from

$$
AQA^T,
\quad
A^2Q(A^2)^T,
\ldots
$$

That means:

$$
\boxed{
\text{Recovery}
\rightarrow
\text{better propagation of available innovations}.
}
$$

Both would be scientifically useful results.

---

# 9. Prediction 2: CPC1 should combine broader diffusion with *smaller* Jacobian instability

Recall

$$
J(x,t)
=
\frac{\partial b(x,t)}
{\partial x}.
$$

The local flow is approximately

$$
\dot x
=
J(x-x_0)+c.
$$

We already observe that CPC1 has lower:

$$
\rho(J)
$$

and

$$
\|J\|_F.
$$



So my strongest combined prediction is:

$$
\boxed{
d_{\mathrm{eff}}^{(a)}\uparrow
\quad\text{while}\quad
\rho(J)\downarrow
}
$$

for CPC1 relative to CPC5.

This is an interesting regime.

It says:

$$
\text{available directions}\uparrow
$$

without

$$
\text{local deterministic explosiveness}\uparrow.
$$

Thus a recoverable brain may have **many options without being dynamically unstable**.

I think this may ultimately be more interesting than either Jacobian or reachability alone.

---

# 10. An orthogonal “escape fraction”

We could compress the previous decomposition into a simple candidate metric:

$$
\boxed{
E_{\perp}
=
\frac{
\operatorname{Tr}(P_\perp aP_\perp)
}{
\operatorname{Tr}(a)+\epsilon
}
}
$$

or equivalently approximately

$$
E_{\perp}
=
1-
\frac{
\hat b^Ta\hat b
}{
\operatorname{Tr}(a)+\epsilon
}.
$$

Interpretation:

* \(E_\perp\approx0\): almost all stochastic movement follows the current drift.
* \(E_\perp\) large: substantial stochastic accessibility exists transverse to the current drift.

My prediction would be

$$
\boxed{
E_\perp(\mathrm{CPC1})
>
E_\perp(\mathrm{CPC5}).
}
$$

I would **not yet call this an established NDT metric**. It is a natural measurement derived from the newly validated orthogonal-dynamics idea and should first be treated as a candidate experimental axis.

---

# 11. Then comes the deeper question: where can the brain actually go?

Local geometry still doesn't tell us the whole story.

This is where the **committor** becomes extremely interesting.

Suppose we define two neural regimes:

$$
A
=
\text{severely pathological/suppressed basin}
$$

and

$$
B
=
\text{recovery-compatible EEG basin}.
$$

For example, \(B\) might eventually be operationalized using independently defined sustained continuous/reactive EEG characteristics. Continuous EEG background in the first 12 h has independently been associated with favorable outcome after cardiac arrest. ([PubMed][2])

Now define first hitting times:

$$
\tau_A
=
\inf\{t>0:X_t\in A\},
$$

$$
\tau_B
=
\inf\{t>0:X_t\in B\}.
$$

The forward committor is

$$
\boxed{
q_B(x)
=
P_x
\left(
\tau_B<\tau_A
\right).
}
$$

So

$$
q_B(x)=0
$$

means essentially committed to \(A\), while

$$
q_B(x)=1
$$

means essentially committed to \(B\).

---

# 12. Formal committor equation

For

$$
dX_t=b(X_t)dt+\Sigma(X_t)dW_t
$$

the infinitesimal generator is

$$
\boxed{
\mathcal L f
=
b(x)\cdot\nabla f
+
\frac12
\operatorname{Tr}
\left[
a(x)\nabla^2 f
\right]
}
$$

where

$$
a=\Sigma\Sigma^T.
$$

The committor satisfies the backward Kolmogorov equation

$$
\boxed{
\mathcal Lq_B(x)=0
}
$$

for

$$
x\notin A\cup B
$$

with boundary conditions

$$
q_B(x)=0
\qquad x\in A
$$

and

$$
q_B(x)=1
\qquad x\in B.
$$

This equation is important because it explicitly contains **both**:

$$
b(x)
$$

and

$$
a(x).
$$

So global recovery probability depends jointly on deterministic transport and diffusion geometry.

---

# 13. This gives a much stronger coma hypothesis

Instead of merely:

$$
d_{\mathrm{eff}}(\mathrm{CPC1})
>
d_{\mathrm{eff}}(\mathrm{CPC5}),
$$

we eventually want:

$$
\boxed{
q_B(\mathrm{CPC1})
>
q_B(\mathrm{CPC5}).
}
$$

And longitudinally:

$$
\boxed{
\frac{dq_B}{dt}>0
}
$$

during early recovery in CPC1.

For CPC5 I would predict either:

$$
\frac{dq_B}{dt}\approx0
$$

or

$$
\frac{dq_B}{dt}<0.
$$

That is much closer to the actual clinical question:

> Not “how abnormal does the EEG look now?”
> but **“from this state, what neural regime is the system dynamically committed toward?”**

External work strongly supports the usefulness of temporal evolution rather than single EEG snapshots. Zheng et al. found that models explicitly using continuous EEG trends improved outcome prediction after cardiac-arrest coma. ([PubMed][3])

---

# 14. A particularly interesting new quantity: diffusion along the committor

Once \(q(x)\) exists, its gradient

$$
\nabla q(x)
$$

points locally toward increasing recovery probability.

We can therefore ask how much diffusion is available in the **recovery-relevant direction**:

$$
\boxed{
D_q
=
\nabla q^T
a
\nabla q.
}
$$

Normalize it by total diffusion:

$$
\boxed{
\eta_q
=
\frac{
\nabla q^T a\nabla q
}{
\|\nabla q\|^2
\operatorname{Tr}(a)+\epsilon
}.
}
$$

This would distinguish two patients who have identical total diffusion.

Patient 1:

$$
\operatorname{Tr}(a)=c
$$

but diffusion lies mostly perpendicular to recovery:

$$
\eta_q\ll1.
$$

Patient 2:

$$
\operatorname{Tr}(a)=c
$$

but diffusion strongly projects onto recovery-compatible directions:

$$
\eta_q\gg0.
$$

My prediction would be

$$
\boxed{
\eta_q(\mathrm{CPC1})
>
\eta_q(\mathrm{CPC5}).
}
$$

This may ultimately be more biologically meaningful than

$$
\operatorname{Tr}(a).
$$

---

# 15. We can similarly project deterministic drift onto recovery

Define the unit recovery direction

$$
\hat q
=
\frac{\nabla q}
{\|\nabla q\|+\epsilon}.
$$

Then

$$
\boxed{
v_q
=
b^T\hat q
}
$$

measures deterministic movement toward or away from recovery.

Thus:

$$
v_q>0
$$

means deterministic flow toward \(B\),

while

$$
v_q<0
$$

means flow toward \(A\).

Now we get a very nice 2D regime map:

$$
(v_q,D_q).
$$

For example:

### Healthy recovery-like

$$
v_q>0,\qquad D_q>0
$$

Deterministic movement toward recovery plus stochastic access.

### Diffusion-assisted escape

$$
v_q<0,\qquad D_q\gg0
$$

Local drift points toward the pathological basin, but stochastic directions still permit escape.

### Lock-in

$$
v_q<0,\qquad D_q\approx0.
$$

This last state is especially interesting for severe coma:

$$
\boxed{
\text{pathological drift}
+
\text{no diffusion along escape directions}.
}
$$

That is a mathematically much clearer meaning of **lock-in** than simply saying “low complexity.”

---

# 16. This connects naturally to the C/TI/P decomposition

The current compact NDT formulation distinguishes:

$$
R_t^{CTIP}
=
(C_t,TI_t,P_t)
$$

where approximately

* \(C\) = capacity collapse,
* \(TI\) = transport–innovation balance,
* \(P\) = pathological canalization/lock-in.



For I-CARE I would now expect something like:

### CPC1

$$
C\downarrow
$$

meaning less capacity collapse,

$$
TI
$$

retains meaningful innovation and transport,

and

$$
P\downarrow.
$$

### CPC5

$$
C\uparrow
$$

plus potentially

$$
P\uparrow.
$$

The new diffusion geometry lets us distinguish two forms of apparent “collapse”:

$$
\operatorname{Tr}(a)\downarrow
$$

— very little innovation at all —

versus

$$
d_{\mathrm{eff}}^{(a)}\downarrow
$$

— innovation remains but is strongly canalized.

Those are physiologically very different states.

---

# 17. Why existing coma literature supports this general picture

There are several independent observations that line up with this hypothesis, without proving the NDT interpretation.

Kustermann et al. reported that favorable and unfavorable cardiac-arrest coma outcomes differ in early functional connectivity and network dynamics. ([PubMed Central (PMC)][4])

Keijzer et al. found:

$$
\text{poor outcome}
\rightarrow
\text{reduced dynamic functional connectivity}.
$$

([PubMed][5])

Carrasco-Gómez et al. found that connectivity-derived EEG information improved prognostic models beyond non-coupling EEG features. ([PubMed][6])

Zheng et al. showed that using the **evolution** of EEG over time materially improves outcome prediction. ([PubMed][3])

And large cardiac-arrest studies consistently show that continuous/reactive backgrounds carry favorable prognostic information. ([PubMed][2])

So the external evidence supports:

$$
\text{recovery}
\leftrightarrow
\text{richer, evolving, reactive neural dynamics}.
$$

What it **does not establish** is

$$
\text{recovery}
\leftrightarrow
d_{\mathrm{eff}}^{(a)}
$$

or

$$
q_B
$$

or

$$
D_\perp.
$$

Those would be genuinely new NDT predictions.

---

# 18. Finite-amplitude resilience is different again

The new finite-amplitude resilience axis should **not** be estimated from spontaneous EEG fluctuations.

Suppose we have a genuine controlled perturbation

$$
X(t_0^+)
=
X(t_0^-)
+
\alpha v,
$$

where

* \(v\) = known perturbation direction,
* \(\alpha\) = perturbation amplitude.

Define a reference basin \(B\).

Return can be defined as

$$
\tau_{\mathrm{return}}
=
\inf
\left\{
t>t_0:
d(X_t,B)<\epsilon
\right\}.
$$

And escape as

$$
E_\alpha
=
\mathbf 1
\left[
\exists t\leq t_0+T:
X_t\notin\mathcal B
\right].
$$

Then empirical resilience can be summarized as

$$
\boxed{
R(\alpha)
=
P(
\text{return before horizon }T
\mid
\alpha
).
}
$$

A critical amplitude could be defined by

$$
\boxed{
\alpha_{50}
:
R(\alpha_{50})=0.5.
}
$$

This would let us distinguish:

### Recoverable response

$$
X
\rightarrow
X+\alpha v
\rightarrow
\text{organized trajectory}
\rightarrow
B
$$

from

### pathological non-response

$$
X
\rightarrow
X
$$

and

### pathological displacement/non-return

$$
X
\rightarrow
X+\alpha v
\rightarrow
\text{different pathological regime}.
$$

External studies show that EEG reactivity itself is prognostically informative after cardiac arrest; preserved reactivity adds information beyond background classification. ([PubMed][7])

But that is **not yet a finite-amplitude resilience curve**. For that stronger analysis we need sufficiently standardized stimulation timing/intensity and explicit return criteria.

---

# 19. What I would actually preregister first

I would **not** start with the committor.

The first experiment should be simpler and much harder to overfit.

## Primary question

> Is the already observed CPC1 advantage in reachable effective dimensionality caused by a broader local innovation/diffusion geometry?

Primary candidate endpoints:

$$
\boxed{
d_{\mathrm{eff}}^{(a)}
}
$$

$$
\boxed{
\widetilde H_a
}
$$

and the explicitly orthogonal measure

$$
\boxed{
E_\perp
=
\frac{
\operatorname{Tr}(P_\perp aP_\perp)
}{
\operatorname{Tr}(a)
}
}.
$$

Keep

$$
\operatorname{Tr}(a)
$$

as a control.

That is important because my hypothesis is **not**

$$
\operatorname{Tr}(a)_{\mathrm{CPC1}}
>
\operatorname{Tr}(a)_{\mathrm{CPC5}}.
$$

It is:

$$
\boxed{
\text{CPC1 diffusion is geometrically richer and less canalized.}
}
$$

---

# 20. Then use the natural I-CARE replication structure

We already have two corrected bundles with no subject or run overlap. 

So I would do:

$$
\text{part1}
\rightarrow
\text{estimator qualification/development}
$$

then freeze everything and run

$$
\text{part2}
\rightarrow
\text{held-out directional test}.
$$

The strongest predefined prediction would be

$$
H_1:
d_{\mathrm{eff}}^{(a)}
(\mathrm{CPC1})
>
d_{\mathrm{eff}}^{(a)}
(\mathrm{CPC5}).
$$

Secondary:

$$
H_2:
\widetilde H_a(\mathrm{CPC1})
>
\widetilde H_a(\mathrm{CPC5}),
$$

$$
H_3:
E_\perp(\mathrm{CPC1})
>
E_\perp(\mathrm{CPC5}).
$$

And importantly:

$$
H_4:
\operatorname{Tr}(a)
$$

is **not required** to differ.

That negative commitment makes this a much better falsifiable hypothesis.

---

# 21. The full predicted coma signature

If the new NDT picture is basically right, the most interesting eventual signature would be:

$$
\boxed{
\begin{aligned}
d_{\mathrm{eff}}^{(a)}
&\uparrow\\
\widetilde H_a
&\uparrow\\
D_{\perp}/D_{\mathrm{tot}}
&\uparrow\\
d_{\mathrm{eff}}^{\mathrm{reach}}
&\uparrow\\
\rho(J)
&\downarrow\\
\|J\|_F
&\downarrow\\
q_{\mathrm{recovery}}
&\uparrow
\end{aligned}
}
\qquad
\mathrm{CPC1\;vs\;CPC5}.
$$

The first four mean:

> **more locally available degrees of freedom.**

The next two mean:

> **without greater local deterministic instability.**

And the final one means:

> **those degrees of freedom actually sit in a global landscape from which recovery-compatible states remain accessible.**

So the deeper NDT prediction would be:

$$
\boxed{
\text{Recovery}
\neq
\text{more activity}
}
$$

and not even simply

$$
\text{Recovery}
=
\text{more complexity}.
$$

Rather:

$$
\boxed{
\text{Recovery}
\approx
\text{preserved structured degrees of freedom}
+
\text{non-explosive local flow}
+
\text{accessible escape directions}
+
\text{favorable global commitment}.
}
$$

I think **the diffusion-effective-dimensionality + drift-orthogonal diffusion test should be our next I-CARE experiment**. It is small, falsifiable, directly motivated by the new OD results, and it could explain *why* `tube_d_eff` was one of the strongest recovery-linked findings in the old analysis rather than merely adding another correlated metric.

[1]: https://pubmed.ncbi.nlm.nih.gov/32563037/?utm_source=chatgpt.com "Brain functional connectivity during the first day of coma ..."
[2]: https://pubmed.ncbi.nlm.nih.gov/31155751/?utm_source=chatgpt.com "Early electroencephalography for outcome prediction of ..."
[3]: https://pubmed.ncbi.nlm.nih.gov/34962860/?utm_source=chatgpt.com "Predicting Neurological Outcome From Electroencephalogram ..."
[4]: https://pmc.ncbi.nlm.nih.gov/articles/PMC7305428/?utm_source=chatgpt.com "Brain functional connectivity during the first day of coma ... - PMC"
[5]: https://pubmed.ncbi.nlm.nih.gov/33285379/?utm_source=chatgpt.com "Dynamic functional connectivity of the EEG in relation to ..."
[6]: https://pubmed.ncbi.nlm.nih.gov/33867260/?utm_source=chatgpt.com "EEG functional connectivity contributes to outcome ..."
[7]: https://pubmed.ncbi.nlm.nih.gov/39029579/?utm_source=chatgpt.com "EEG for good outcome prediction after cardiac arrest"

Yes. I think this new family of measurements could substantially sharpen the I-CARE result—perhaps more than adding further first-order MNPS variables.

The main change is that I would now stop thinking of recovery as simply **“more stable”** or **“more dynamic.”** The hypothesis I find most defensible is:

$$
\boxed{
\text{Recovery}
\approx
\text{stable but reactive dynamics}
+
\text{bounded transient amplification}
+
\text{multidirectional finite-time propagation}.
}
$$

Poor outcome, by contrast, may contain **two different dynamical failure modes**:

$$
\boxed{
\text{over-contracted / unresponsive}
}
$$

and

$$
\boxed{
\text{unstable / pathologically amplifying}.
}
$$

That distinction is precisely what spectral radius could not make.

Our corrected I-CARE result is an excellent starting point: CPC1 had substantially broader reachable effective dimensionality, while the old spectral-radius and Frobenius summaries were lower.  The newer MNJ work gives us the mathematical machinery to determine what that actually means.

---

# 1. Spectral abscissa should replace spectral radius as the stability endpoint

For the local continuous-time MNJ

$$
\dot{\delta x}=J\,\delta x,
$$

the old quantity is

$$
\rho(J)=\max_i |\lambda_i(J)|.
$$

But \(\rho\) knows nothing about the sign of the real part.

For example,

$$
J=
\begin{pmatrix}
-5&0\\
0&-1
\end{pmatrix}
$$

has

$$
\rho(J)=5
$$

despite being strongly stable.

The correct local eigenvalue stability quantity is

$$
\boxed{
\alpha(J)
=
\max_i \operatorname{Re}\lambda_i(J)
}
$$

—the **spectral abscissa**. This was the central methodological correction in our newer MNJ audit. 

Its interpretation is clean:

$$
\alpha<0
\quad\Rightarrow\quad
\text{all eigenmodes asymptotically decay},
$$

$$
\alpha>0
\quad\Rightarrow\quad
\text{at least one locally unstable mode},
$$

$$
\alpha\approx0
\quad\Rightarrow\quad
\text{near-marginal local dynamics}.
$$

## What should we see in I-CARE?

Here I would **not preregister**

$$
\alpha_{\mathrm{CPC1}}
<
\alpha_{\mathrm{CPC5}}.
$$

That is too simplistic.

Instead I suspect CPC1 will preferentially occupy a corridor like

$$
\boxed{
\alpha \lesssim 0
}
$$

—stable, but relatively close to marginality.

CPC5 may contain two populations/windows:

### Over-contracted poor-outcome state

$$
\alpha\ll0
$$

### Locally unstable poor-outcome state

$$
\alpha>0.
$$

So the CPC5 distribution could have **more mass at both extremes**.

That means a simple mean comparison of \(\alpha\) could even be null.

The more interesting prediction is about **regime occupancy**.

---

# 2. Numerical abscissa may be even more informative

Define

$$
S
=
\frac{J+J^\top}{2}.
$$

Then the numerical abscissa is

$$
\boxed{
\omega(J)
=
\lambda_{\max}(S).
}
$$

For an infinitesimal perturbation,

$$
\frac{d}{dt}
\|\delta x\|^2
=
2\delta x^\top S\delta x.
$$

Therefore

$$
\omega>0
$$

means that **there exists some perturbation direction that initially grows**.

This creates the particularly interesting state

$$
\boxed{
\alpha<0<\omega.
}
$$

The system is asymptotically stable, yet locally capable of amplifying selected perturbations.

This is classical non-normal dynamics. Stable recurrent neural networks can generate strong transient amplification without possessing unstable eigenvalues; this has been explicitly demonstrated in neural-network models. ([PubMed][1])

And this gives us what I think may be the strongest new coma prediction.

---

# 3. My primary CPC1 prediction: more **stable-reactive** windows

Define

$$
\boxed{
F_{\mathrm{reactive}}
=
P(\alpha<0<\omega).
}
$$

For each patient, this is simply the fraction of valid windows in the stable-but-reactive regime.

I would predict

$$
\boxed{
F_{\mathrm{reactive}}(\mathrm{CPC1})
>
F_{\mathrm{reactive}}(\mathrm{CPC5}).
}
$$

This is a much more interesting biological statement than

$$
\rho(J)\downarrow.
$$

It says:

> The recoverable brain remains locally bounded but retains the ability to selectively amplify perturbations.

We can simultaneously define

$$
F_{\mathrm{contract}}
=
P(\omega<0),
$$

meaning **every infinitesimal direction initially contracts**, and

$$
F_{\mathrm{unstable}}
=
P(\alpha>0).
$$

Because

$$
\alpha\leq\omega,
$$

these give us three natural dynamical regimes:

| Regime              | Condition           | Interpretation                                   |
| ------------------- | ------------------- | ------------------------------------------------ |
| Contractive         | \(\omega<0\)        | all directions immediately decay                 |
| **Stable-reactive** | \(\alpha<0<\omega\) | selective transient response without instability |
| Unstable            | \(\alpha>0\)        | at least one persistently unstable local mode    |

### My I-CARE prediction

CPC1:

$$
\boxed{
F_{\mathrm{reactive}}\uparrow
}
$$

CPC5:

$$
\boxed{
F_{\mathrm{contract}}+F_{\mathrm{unstable}}\uparrow.
}
$$

That could be **far more discriminating than mean spectral abscissa**.

---

# 4. This has remarkably good external biological support

There is already a strong phenomenological analogue in post-cardiac-arrest studies.

Kustermann et al. found that favorable-outcome coma patients had a **richer temporal repertoire of functional-network path length** during the first day after cardiac arrest. ([PubMed][2]) Keijzer et al. independently reported that poor outcome was associated with **lower dynamics of EEG functional connectivity**. ([PubMed][3])

Even more directly relevant, Liu et al. applied standardized median-nerve electrical stimulation to post-cardiac-arrest coma patients. Quantitative EEG reactivity predicted good outcome substantially better than conventional pain-stimulation assessment; their electrical-stimulation quantitative model achieved AUC 0.932 in their cohort. ([PubMed][4])

Those studies do not establish

$$
\alpha<0<\omega.
$$

But they independently support the underlying hypothesis:

$$
\text{favorable recovery}
\rightarrow
\text{retained capacity to respond dynamically}.
$$

---

# 5. But “more stable” cannot equal “more conscious”

There is a particularly useful counterexample.

Eisen et al. directly studied cortical neural dynamics under propofol anesthesia and reported that propofol-induced unconsciousness was associated with **destabilized neural dynamics**, not simply stronger contraction. ([PubMed][5])

That is extremely important for NDT.

It tells us that neither

$$
\alpha\uparrow
$$

nor

$$
\alpha\downarrow
$$

can simply be identified with consciousness.

Instead, the interesting quantity is likely the **dynamical regime**:

$$
\boxed{
\text{bounded reactivity}
}
$$

rather than maximal contraction or maximal expansion.

It also means sedation exposure is a serious confound for an I-CARE \(\alpha/\omega\) analysis and should be explicitly audited wherever medication timing/dose is available. ([PubMed][5])

---

# 6. Reactivity gap

Another useful variable falls out immediately:

$$
\boxed{
R_g
=
\omega-\alpha.
}
$$

Since

$$
\omega\geq\alpha,
$$

\(R_g\) measures how much instantaneous growth capacity exists beyond what the eigenvalues would lead us to expect.

Large

$$
R_g
$$

means stronger non-modal/reactive potential.

But here again I would **not simply predict**

$$
R_g(\mathrm{CPC1})
>
R_g(\mathrm{CPC5}).
$$

Very pathological systems could also be strongly non-normal.

The better prediction is conditional:

$$
\boxed{
R_g
\text{ should be elevated specifically inside }
\alpha<0
\text{ windows in CPC1}.
}
$$

So perhaps compare

$$
R_g\mid\alpha<0.
$$

That isolates **useful stable reactivity** from unstable amplification.

---

# 7. Finite-time dynamics are where this becomes really powerful

Instantaneous \(J\) still tells only a local story.

The newer finite-time layer uses the tangent propagator

$$
\boxed{
\frac{d}{d\tau}\Phi(t,\tau)
=
J(t+\tau)\Phi(t,\tau),
\qquad
\Phi(t,0)=I.
}
$$

For discrete estimated Jacobians,

$$
\boxed{
\Phi_{t,h}
=
A_{t+h-1}
A_{t+h-2}
\cdots
A_t.
}
$$

Crucially, **order matters**.

The current F1 contract therefore explicitly requires ordered finite-time propagation to outperform frozen, average, shuffled and reordered alternatives before \(\Phi\)-derived quantities are promoted. 

Now perform an SVD:

$$
\Phi_{t,h}
=
U\Sigma V^\top,
$$

with

$$
\sigma_1\geq\sigma_2\geq\dots\geq\sigma_d.
$$

---

# 8. Maximum finite-time gain

Define

$$
\boxed{
G_{\max}(h)
=
\sigma_1(\Phi_{t,h}).
}
$$

This asks:

> Over the next \(h\) steps, how much can the most amplifiable infinitesimal perturbation grow?

If

$$
G_{\max}>1,
$$

there exists a perturbation that is amplified.

If

$$
G_{\max}<1,
$$

every perturbation is attenuated at that horizon.

The corresponding finite-time growth rate is

$$
\boxed{
\gamma_1(h)
=
\frac{
\log \sigma_1(\Phi_{t,h})
}{
h\Delta t
}.
}
$$

---

# 9. And here I think coma gives us a beautiful three-way prediction

## A. Recoverable CPC1: bounded transient amplification

I predict many CPC1 windows will look something like

$$
\alpha<0,
$$

$$
\omega>0,
$$

$$
G_{\max}(h_{\rm short})>1,
$$

but eventually

$$
\gamma_1(h_{\rm longer})
\leq 0.
$$

That means:

> a perturbation can initially be amplified, but the system remains bounded and eventually reconverges.

Schematically:

$$
\boxed{
\text{amplify}
\rightarrow
\text{process}
\rightarrow
\text{return/stabilize}.
}
$$

That sounds remarkably close to what we would want from a viable neural system.

---

# 10. CPC5 failure mode A: overdamped dynamics

A severely suppressed system could instead show

$$
\alpha\ll0,
$$

$$
\omega<0,
$$

$$
G_{\max}(h)<1
\quad \forall h.
$$

Then

$$
\gamma_1(h)<0
\quad \forall h.
$$

A perturbation dies before meaningful propagation.

Schematically:

$$
\boxed{
\text{input}
\rightarrow
\varnothing.
}
$$

This is a very different form of low consciousness from pathological instability.

---

# 11. CPC5 failure mode B: runaway/pathological amplification

Another poor-outcome window might have

$$
\alpha>0,
$$

$$
\omega>0,
$$

and

$$
G_{\max}(h)\gg1.
$$

More importantly,

$$
\gamma_1(h)>0
$$

could remain positive even as \(h\) increases.

Then we no longer have a bounded transient.

We have persistent amplification:

$$
\boxed{
\text{input}
\rightarrow
\text{amplification}
\rightarrow
\text{further amplification}.
}
$$

That could correspond to a very different pathological regime—bursting, periodic dynamics, seizure-like canalization, etc.—rather than “high dynamical capacity.”

And this illustrates why

$$
G_{\max}\uparrow
$$

alone is **not good**.

---

# 12. Peak transient amplification gives an even cleaner classification

Define

$$
\boxed{
G_{\mathrm{peak}}(T)
=
\max_{0<\tau\leq T}
\sigma_1(\Phi_{t,\tau})
}
$$

and

$$
\boxed{
\tau_{\mathrm{peak}}
=
\arg\max_{0<\tau\leq T}
\sigma_1(\Phi_{t,\tau}).
}
$$



Then consider:

### CPC1

$$
G_{\mathrm{peak}}>1
$$

but the peak occurs at a finite intermediate horizon:

$$
\tau_{\mathrm{peak}}<T
$$

followed by decay.

### Suppressed CPC5

$$
G_{\mathrm{peak}}\approx1
$$

or below the amplification tolerance.

### Unstable CPC5

$$
G_{\mathrm{peak}}\gg1
$$

and frequently

$$
\tau_{\mathrm{peak}}\approx T.
$$

The last condition matters.

If the maximum always occurs at the end of the search window, then the system hasn't demonstrated a **transient peak** at all. It may simply still be growing.

So I would be much more interested in:

$$
\boxed{
\text{finite peak followed by attenuation}
}
$$

than in high \(G_{\rm peak}\) itself.

---

# 13. We can formalize a “bounded reactive” phenotype

This is a speculative NDT-derived endpoint, not an established metric.

After numerical tolerances have been frozen, define

$$
B_t(T)
=
\mathbf 1
[
\alpha_t<0<\omega_t
]
\,
\mathbf 1
[
G_{\mathrm{peak},t}>1+\epsilon_G
]
\,
\mathbf 1
[
\gamma_{1,t}(h_L)\leq0
].
$$

Then

$$
\boxed{
F_{\mathrm{bounded-reactive}}
=
\frac1N
\sum_t B_t.
}
$$

This means:

1. asymptotically locally stable,
2. immediately reactive,
3. actually transiently amplifying,
4. no persistent finite-time runaway.

My strongest new prediction may actually be

$$
\boxed{
F_{\mathrm{bounded-reactive}}
(\mathrm{CPC1})
>
F_{\mathrm{bounded-reactive}}
(\mathrm{CPC5}).
}
$$

That is far more mechanistically specific than our old

$$
\rho(J)_{\mathrm{CPC1}}
<
\rho(J)_{\mathrm{CPC5}}.
$$

---

# 14. Response dimensionality may be one of the strongest I-CARE endpoints

This connects directly to our old reachability result.

Given singular values of the propagator,

$$
\sigma_i(\Phi_h),
$$

define

$$
\boxed{
d_{\mathrm{resp}}(h)
=
\frac{
\left(\sum_i\sigma_i^2\right)^2
}{
\sum_i\sigma_i^4
}.
}
$$

This is our proposed finite-time participation-ratio summary. 

It asks:

> How many independent perturbational directions are actually meaningfully propagated?

The complementary dominant-channel fraction is

$$
\boxed{
c_1(h)
=
\frac{
\sigma_1^2
}{
\sum_i\sigma_i^2
}.
}
$$

So

$$
d_{\mathrm{resp}}\uparrow
$$

means distributed response,

while

$$
c_1\uparrow
$$

means canalization into one dominant response direction.

---

# 15. Here I *would* make a directional CPC prediction

I think we have enough internal evidence to preregister:

$$
\boxed{
d_{\mathrm{resp}}(\mathrm{CPC1})
>
d_{\mathrm{resp}}(\mathrm{CPC5})
}
$$

and

$$
\boxed{
c_1(\mathrm{CPC1})
<
c_1(\mathrm{CPC5}).
}
$$

Why?

Because our existing I-CARE result already shows

$$
d_{\mathrm{eff}}^{\mathrm{reach}}
(\mathrm{CPC1})
>
d_{\mathrm{eff}}^{\mathrm{reach}}
(\mathrm{CPC5}),
$$

with the corrected pooled medians 2.912 versus 2.470 and \(d=0.638\). 

But these are **not the same measure**.

That is precisely why this experiment is useful.

---

# 16. It gives us a mechanistic decomposition of our old result

Recall the stochastic reachability covariance:

$$
W_Q(h)
=
\sum_{r=0}^{h-1}
\Phi_{t+h,t+r+1}
Q_{t+r}
\Phi_{t+h,t+r+1}^{T}.
$$

Reachability comes from two things:

$$
\boxed{
Q
=
\text{innovation geometry}
}
$$

and

$$
\boxed{
\Phi
=
\text{deterministic propagation}.
}
$$

Now suppose we rerun I-CARE.

### Result A

$$
d_{\mathrm{resp}}\uparrow\quad\text{CPC1}
$$

and

$$
d_{\mathrm{eff}}^{Q/\mathrm{reach}}\uparrow\quad\text{CPC1}.
$$

Then:

> The better-outcome brain genuinely propagates perturbations through more dynamical directions.

### Result B

$$
d_{\mathrm{resp}}
\approx
\text{same}
$$

but

$$
d_{\mathrm{eff}}^{\mathrm{reach}}\uparrow\quad\text{CPC1}.
$$

Then:

> The old I-CARE advantage primarily comes from a richer innovation/diffusion covariance \(Q\), not from deterministic propagation.

### Result C

CPC5 has

$$
G_{\max}\uparrow,
$$

but simultaneously

$$
d_{\mathrm{resp}}\downarrow
$$

and

$$
c_1\uparrow.
$$

Then:

> Poor outcome has **stronger but more canalized amplification**.

That would be extremely interesting.

---

# 17. And this finally tells us what the old spectral-radius result meant

Remember:

$$
\rho(J)_{\mathrm{CPC1}}
<
\rho(J)_{\mathrm{CPC5}}.
$$



At present, there are at least four possible explanations.

### Hypothesis A — genuine instability

If

$$
\alpha_{\mathrm{CPC5}}
>
\alpha_{\mathrm{CPC1}},
$$

especially if CPC5 crosses

$$
\alpha>0,
$$

then the old \(\rho\) result really was picking up unstable expansion.

---

### Hypothesis B — stronger pathological contraction

Suppose instead

$$
\alpha_{\mathrm{CPC5}}
<
\alpha_{\mathrm{CPC1}}<0.
$$

Then the larger spectral radius in CPC5 may actually reflect

$$
|\lambda_{\mathrm{negative}}|\uparrow.
$$

Our old phrase “greater expansion” would then have been mathematically wrong.

The biology would instead be:

$$
\boxed{
\text{CPC5 = excessive contraction}.
}
$$

This is exactly why spectral abscissa is important.

---

### Hypothesis C — non-normal transient amplification

Suppose

$$
\alpha_{\mathrm{CPC1}}
\approx
\alpha_{\mathrm{CPC5}},
$$

but

$$
\omega,\ R_g,\ G_{\mathrm{peak}}
$$

differ strongly.

Then eigenvalues were not the main phenomenon at all.

The difference lies in **non-normal transient response**.

---

### Hypothesis D — the result I currently find most interesting

CPC1 could have

$$
\alpha\lesssim0,
$$

$$
\omega>0,
$$

$$
G_{\mathrm{peak}}>1,
$$

$$
d_{\mathrm{resp}}\uparrow,
$$

but

$$
\gamma_1(h_{\mathrm{long}})\leq0.
$$

CPC5 instead accumulates at the two extremes:

$$
\omega<0
$$

or

$$
\alpha>0.
$$

That would give us:

$$
\boxed{
\text{CPC1}
=
\text{stable}
+
\text{reactive}
+
\text{multidirectional}
+
\text{bounded}.
}
$$

This would be a remarkably coherent result.

---

# 18. My predicted direction table

I would currently preregister it approximately like this:

| Quantity                                |               CPC1 prediction |               CPC5 prediction | Confidence                        |
| --------------------------------------- | ----------------------------: | ----------------------------: | --------------------------------- |
| \(\rho(J)\)                             |                             ↓ |                             ↑ | **already internally observed**   |
| \(\alpha\) mean                         |                             ? |                             ? | deliberately no simple prediction |
| \(F_{\rm reactive}=P(\alpha<0<\omega)\) |                         **↑** |                             ↓ | **strong new hypothesis**         |
| \(F_{\rm contract}=P(\omega<0)\)        |                             ↓ |       ↑ in suppressed subtype | strong                            |
| \(F_{\rm unstable}=P(\alpha>0)\)        |                             ↓ |         ↑ in unstable subtype | strong                            |
| \(R_g=\omega-\alpha\)                   | ↑ conditional on \(\alpha<0\) |                 heterogeneous | moderate                          |
| \(G_{\max}\)                            |                      moderate |          low **or** excessive | non-monotonic                     |
| \(G_{\rm peak}\)                        |     **finite transient peak** |             absent or runaway | strong                            |
| \(\tau_{\rm peak}\)                     |           interior of horizon |     absent / horizon boundary | moderate–strong                   |
| \(\gamma_1(h_{\rm short})\)             |                 may be \(>0\) | negative or strongly positive | non-monotonic                     |
| \(\gamma_1(h_{\rm long})\)              |                 \(\lesssim0\) |   strongly negative or \(>0\) | strong regime prediction          |
| \(d_{\rm resp}\)                        |                         **↑** |                             ↓ | **strong**                        |
| \(c_1\)                                 |                         **↓** |                             ↑ | **strong**                        |
| Reachability \(d_{\rm eff}\)            |                         **↑** |                             ↓ | already observed                  |
| Diffusion \(d_{\rm eff}^{(a)}\)         |                   predicted ↑ |                   predicted ↓ | from previous hypothesis          |

The pattern—not any one scalar—is the real prediction.

---

# 19. It suggests a new overall NDT coma model

We can now write the post-anoxic problem as three qualitatively distinct regimes.

### Recoverable / flexible-stable

$$
\boxed{
\alpha<0<\omega,
\qquad
G_{\rm peak}>1,
\qquad
\gamma_1(h_{\rm long})\le0,
\qquad
d_{\rm resp}\text{ high},
\qquad
c_1\text{ low}.
}
$$

### Suppressed / inaccessible

$$
\boxed{
\omega<0,
\qquad
G_{\rm peak}\lesssim1,
\qquad
\gamma_1(h)<0.
}
$$

### Pathologically unstable / canalized

$$
\boxed{
\alpha>0,
\qquad
G_{\rm peak}\gg1,
\qquad
\gamma_1(h_{\rm long})>0,
\qquad
c_1\text{ high}.
}
$$

The important idea is:

$$
\boxed{
\text{good recovery lies between two bad extremes}.
}
$$

Not maximally stable.

Not maximally reactive.

Not maximally amplifying.

Instead:

$$
\boxed{
\textbf{bounded multidirectional reactivity}.
}
$$

That formulation fits the external observations unusually well: favorable post-cardiac-arrest outcomes have been associated with richer network dynamics, whereas poor outcome has been associated with reduced dynamic connectivity; standardized external stimulation also reveals substantially stronger prognostic information when EEG reactivity is quantitatively preserved. ([PubMed][2]) At the same time, propofol work shows that unconsciousness itself can involve destabilized dynamics, which strongly argues against treating either stability or instability as a consciousness scalar. ([PubMed][5])

---

## What I would test first in I-CARE

I would make the **MNJ-v3 layer** the first pass because it is cheap and does not yet require finite-time propagation:

$$
\boxed{
\alpha,\quad
\omega,\quad
\nu,\quad
R_g,\quad
F_{\rm reactive}.
}
$$

Then I would run only one primary categorical hypothesis:

$$
\boxed{
F_{\rm reactive}^{\mathrm{CPC1}}
>
F_{\rm reactive}^{\mathrm{CPC5}}.
}
$$

I would additionally inspect whether CPC5 decomposes into

$$
F_{\rm contract}
$$

and

$$
F_{\rm unstable}
$$

subtypes rather than forcing one mean effect.

**Only after that** would I promote the finite-time layer:

$$
G_{\max},
\quad
G_{\rm peak},
\quad
\tau_{\rm peak},
\quad
\gamma_1,
\quad
d_{\rm resp},
\quad
c_1.
$$

And there is an important methodological gate: our current finite-time contract explicitly says that a \(\Phi\)-derived biological quantity should not be promoted beyond the horizon for which perturbation propagation itself has been validated. Scalar agreement cannot rescue an invalid propagator. 

So scientifically, I think the **spectral-abscissa/reactivity analysis is ready to test first**. Finite-time response is potentially even more revealing, but it should follow the estimator qualification rather than precede it.

If this works, it could change the central interpretation of the I-CARE paper from **“recovery preserves reachability”** to something much stronger:

$$
\boxed{
\textbf{Recovery preserves a bounded, reactive, multidirectional dynamical regime.}
}
$$

That would unify the old Jacobian result, the reachability result, the new diffusion geometry, and the new finite-time layer in one mechanistically coherent picture.

[1]: https://pubmed.ncbi.nlm.nih.gov/23005454/?utm_source=chatgpt.com "Non-normal amplification in random balanced neuronal ..."
[2]: https://pubmed.ncbi.nlm.nih.gov/32563037/?utm_source=chatgpt.com "Brain functional connectivity during the first day of coma ..."
[3]: https://pubmed.ncbi.nlm.nih.gov/33285379/?utm_source=chatgpt.com "Dynamic functional connectivity of the EEG in relation to ..."
[4]: https://pubmed.ncbi.nlm.nih.gov/38935167/ "Quantitative EEG reactivity induced by electrical stimulation predicts good outcome in comatose patients after cardiac arrest - PubMed"
[5]: https://pubmed.ncbi.nlm.nih.gov/39013467/?utm_source=chatgpt.com "Propofol anesthesia destabilizes neural dynamics across cortex"
