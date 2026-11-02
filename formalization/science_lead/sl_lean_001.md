Yes. I would make the Lean package **small, theorem-driven, and directly tied to the NDT-TRANS hierarchy**. The current NDT manuscript already makes the crucial distinction that the generator/local law, finite-horizon kernel \(K_h\), committor \(q\), and finite-amplitude response are different mathematical objects; it also defines \(K_h\) as an endpoint law rather than a path-space measure.  The existing compact formal layer already gives us the linear reachability recursion \(\Sigma_{h+1}=A\Sigma_hA^\top+Q\), so I would build on that rather than formalizing the full neural SDE first. 

My proposed Lean target is roughly the following.

1. **Fixed transition, different diffusion ⇒ different future geometry.** Start from the discrete linear stochastic model

$$
X_{n+1}=AX_n+b+\varepsilon_n,
\qquad
\mathbb E[\varepsilon_n]=0,
\qquad
\operatorname{Cov}(\varepsilon_n)=Q.
$$

For a fixed \(A,b\),

$$
\mu_h(x)
=
A^h x+\sum_{j=0}^{h-1}A^j b,
$$

and

$$
\Sigma_0=0,
\qquad
\Sigma_{h+1}=A\Sigma_hA^\top+Q,
$$

equivalently

$$
\Sigma_h
=
\sum_{j=0}^{h-1}A^jQ(A^j)^\top.
$$

The first core theorem should say that the deterministic operator can be identical while the stochastic future geometry differs:

$$
A_1=A_2,\qquad b_1=b_2,\qquad Q_1\neq Q_2
$$

does **not** imply

$$
K_h^{(1)}(x,\cdot)=K_h^{(2)}(x,\cdot).
$$

For \(h=1\) this is especially clean because

$$
\Sigma_1=Q.
$$

This is the formal version of

$$
\boxed{\text{same deterministic local dynamics}\not\Rightarrow
\text{same finite-horizon law}.}
$$

It is stronger than merely proving \(J\not\Rightarrow K_h\), because even the drift itself can be held fixed.

2. **Covariance order propagates through time.** If

$$
Q_1\preceq Q_2,
$$

then prove by induction that

$$
\Sigma_h(A,Q_1)\preceq\Sigma_h(A,Q_2)
\qquad
\forall h\ge1.
$$

The induction step follows from

$$
\Sigma_{h+1}^{(2)}-\Sigma_{h+1}^{(1)}
=
A(\Sigma_h^{(2)}-\Sigma_h^{(1)})A^\top
+
(Q_2-Q_1).
$$

Since

$$
P\succeq0
\quad\Rightarrow\quad
APA^\top\succeq0,
$$

positive-semidefinite order is preserved.

This connects very naturally to your existing covariance-gate Lean work. For positive-definite covariances define

$$
E(\Sigma,c)
=
\left\{
z:
z^\top\Sigma^{-1}z\le c
\right\}.
$$

Then ideally prove

$$
0\prec\Sigma_1\preceq\Sigma_2
\quad\Rightarrow\quad
E(\Sigma_1,c)\subseteq E(\Sigma_2,c),
$$

using the inverse-order relation

$$
0\prec\Sigma_1\preceq\Sigma_2
\quad\Rightarrow\quad
\Sigma_2^{-1}\preceq\Sigma_1^{-1}.
$$

That gives a rigorous bridge from **diffusion covariance** to **reachable gate inclusion**.

3. **Equal scalar summaries do not identify directional geometry.** This one could be exceptionally useful for NDT. Take

$$
Q_1=
\begin{pmatrix}
\lambda_1&0\\
0&\lambda_2
\end{pmatrix},
\qquad
Q_2=
\begin{pmatrix}
\lambda_2&0\\
0&\lambda_1
\end{pmatrix},
\qquad
\lambda_1>\lambda_2>0.
$$

Then

$$
Q_1\neq Q_2
$$

but

$$
\operatorname{tr}Q_1=\operatorname{tr}Q_2,
$$

$$
\det Q_1=\det Q_2,
$$

and they have the same eigenvalue multiset. Therefore volume-like quantities and effective-dimensionality quantities can be identical while orientation differs.

You can make the non-equivalence completely constructive. Let

$$
z=(\sqrt{\lambda_1},0)^\top.
$$

Then

$$
z^\top Q_1^{-1}z=1,
$$

while

$$
z^\top Q_2^{-1}z
=
\frac{\lambda_1}{\lambda_2}>1.
$$

Hence, at gate threshold \(c=1\),

$$
z\in E(Q_1,1)
$$

but

$$
z\notin E(Q_2,1).
$$

This proves something scientifically important:

$$
\boxed{
\text{same volume + same spectrum}
\not\Rightarrow
\text{same directional accessibility}.
}
$$

That is an excellent theorem for defending why NDT keeps the full covariance geometry rather than collapsing everything into tube volume or effective dimension.

4. **Terminal occupancy \(\neq\) first-hit probability.** Define

$$
O_T(x;B)
=
\Pr_x(X_T\in B),
$$

and

$$
q_T(x;A,B)
=
\Pr_x(
\tau_B<\tau_A,\,
\tau_B\le T
),
$$

where

$$
\tau_B=\inf\{t\ge0:X_t\in B\}.
$$

The theorem should first establish non-equivalence by explicit counterexample:

$$
\exists\,P,x,A,B,T:
\qquad
O_T(x;B)\neq q_T(x;A,B).
$$

A very simple finite-state example is enough. Let the deterministic path be

$$
x\rightarrow b\rightarrow c,
$$

with

$$
B=\{b\},\qquad T=2.
$$

Then the process certainly hits \(B\):

$$
q_2(x;A,B)=1,
$$

for any irrelevant/unreached \(A\), but it is no longer in \(B\) at the endpoint:

$$
O_2(x;B)=0.
$$

Then prove the positive result too. If \(A\) and \(B\) are disjoint and **both absorbing**, and \(x\notin A\cup B\), then

$$
\boxed{
O_T(x;B)=q_T(x;A,B).
}
$$

That is much stronger scientifically than merely saying “these metrics differ”: it states the exact assumptions under which they collapse to the same object.

5. **Finite-horizon committor \(\neq\) eventual committor.** Define

$$
q_T(x)
=
\Pr_x(
\tau_B<\tau_A,\,
\tau_B\le T
)
$$

and

$$
q_\infty(x)
=
\Pr_x(\tau_B<\tau_A).
$$

First prove monotonicity:

$$
q_T(x)\le q_{T+1}(x)\le q_\infty(x).
$$

More generally,

$$
T_1\le T_2
\quad\Rightarrow\quad
q_{T_1}(x)\le q_{T_2}(x).
$$

Then provide an explicit strict example:

$$
q_T(x)<q_\infty(x).
$$

Again this can be trivial and constructive. If

$$
x\rightarrow c\rightarrow B
$$

deterministically and \(T=1\), then

$$
q_1(x)=0,
\qquad
q_\infty(x)=1.
$$

This formally supports the TRANS rule:

$$
\boxed{
\text{finite-horizon destination probability}
\neq
\text{eventual commitment}.
}
$$

6. **Kernel sufficiency versus functional insufficiency.** This is perhaps the cleanest abstract theorem family. Let \(K_1,K_2\) be Markov kernels.

If

$$
K_1=K_2,
$$

then for every measurable \(B\),

$$
K_1(x,B)=K_2(x,B).
$$

And therefore every properly defined functional \(F\) satisfies

$$
F(K_1)=F(K_2).
$$

Conversely, equality of a **single** functional does not identify the kernel:

$$
F(K_1)=F(K_2)
\centernot\Rightarrow
K_1=K_2.
$$

For example, construct two finite-state kernels satisfying

$$
K_1(x,B)=K_2(x,B)
$$

for one nominated target \(B\), while

$$
K_1(x,C)\neq K_2(x,C)
$$

for another measurable set \(C\). Therefore

$$
K_1\neq K_2.
$$

This is directly relevant to NDT's inference discipline. If a reachability scalar is equal across two conditions, we have **not** shown that their future laws are equal. Conversely, if the complete kernel were equal, all kernel-derived endpoint functionals would necessarily agree.

Mathlib already has the right abstraction here: a probability kernel is represented as a measurable map from states to measures, and Markov kernels are kernels whose output at every state is a probability measure. Kernel extensionality is therefore already part of the surrounding formal ecosystem. ([Lean Community][1])

I would also add one **optional seventh theorem** if we want the Lean package to touch CHART as well as TRANS. Let

$$
\pi:S\rightarrow X
$$

be a non-injective measurement projection. Construct

$$
s_1\neq s_2,
\qquad
\pi(s_1)=\pi(s_2)=x,
$$

while their latent transition laws differ:

$$
K(s_1,\cdot)\neq K(s_2,\cdot).
$$

Then the reduced chart coordinate \(x\) cannot by itself identify the latent future law. That is essentially a constructive formal version of NDT-C1. The current NDT manuscript explicitly treats reduced-state insufficiency as a load-bearing modelling issue, while correctly noting that it is not itself novel. 

### The package I would actually build

I would **not start with continuous-time Itô calculus**. I would make the first formal TRANS paper/package use:

$$
X_{n+1}=AX_n+b+\varepsilon_n
$$

plus finite-state Markov chains.

That gives us two complementary formal domains:

$$
\text{linear algebra}
\quad\Rightarrow\quad
\Sigma_h,\ \text{PSD order},\ \text{ellipsoids},
$$

and

$$
\text{finite probability}
\quad\Rightarrow\quad
K_h,\ O_T,\ q_T,\ q_\infty.
$$

Only after those are finished would I generalize to arbitrary measurable Markov kernels or continuous-time diffusions.

If I were freezing the Lean specification today, I would make the **P0 set** exactly:

$$
\boxed{
\begin{aligned}
&\text{T1: } Q_1\neq Q_2
\Rightarrow
\Sigma_1^{(1)}\neq\Sigma_1^{(2)}
&&\text{with fixed }A,b,\\[2mm]
&\text{T2: } Q_1\preceq Q_2
\Rightarrow
\Sigma_h^{(1)}\preceq\Sigma_h^{(2)},\\[2mm]
&\text{T3: equal scalar covariance summaries}
\not\Rightarrow
\text{equal gates},\\[2mm]
&\text{T4: terminal occupancy}
\not\equiv
\text{finite first-hit committor},\\[2mm]
&\text{T5: }q_T\le q_\infty
\text{ with strict counterexample},\\[2mm]
&\text{T6: one kernel functional}
\not\Rightarrow
\text{kernel equality}.
\end{aligned}
}
$$

Those six results would already provide a remarkably clean formal backbone for the statement that

$$
\boxed{
J,\ a,\ K_h,\ q_T,\ q_\infty
\text{ are not interchangeable levels of description.}
}
$$

And importantly, they line up almost one-to-one with what TRANS is already trying to establish computationally. That is the Lean work I think would most improve the evidential burden of NDT rather than merely increase the theorem count.

[1]: https://leanprover-community.github.io/mathlib4_docs/Mathlib/Probability/Kernel/Basic.html?utm_source=chatgpt.com "Mathlib.Probability.Kernel.Basic"
