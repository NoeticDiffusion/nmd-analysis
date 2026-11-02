# M3 extension: nonlinear, observation-limited and 9D recovery

Prospective protocol, 2026-09-06. Coordinator Astra; reused Luna agents
Pascal (implementation), Mill (tests), Avicenna (independent review).
Numeric spec must be serialized and SHA256 recorded before primary outcomes.
Corrections after freezing retain original evidence and unchanged parameters.

## Question and scope

How do the existing local mean and local affine velocity candidates behave
under full nonlinear dynamics, nine-dimensional inputs, partial observation,
and additive observation noise? Can repeated independent training trajectories
separate pointwise bias from estimation variance at fixed held-out states?

This is synthetic analysis-owned qualification evidence, not a canonical MNPS
generator, an EEG forward model, an Itô-drift estimator or biological evidence.
Nine simulated coordinates have known truth but are not the canonical MNPS 9D
features. No production estimator/hyperparameter selection or gate threshold
will be fitted to the observed outcomes. No ingest changes or cohort run.

## Fixed systems and data

Six systems: full linear 3D; full nonlinear 3D; full linear 9D; full nonlinear
9D; linear latent 9D observed through its first three coordinates; linear 3D
with independent additive observation noise. Let S x = roll(x,1),
A=0.65 I+0.08 S, Q=0.09 I, and dt=0.1. Linear latent transitions are
x_next=A x+epsilon, epsilon~N(0,Q). Nonlinear full transitions add
0.12 tanh(S x). Independent innovation draws at every step.

For linear systems, initialize x~N(0,P), where P=A P A.T+Q, then burn 300
transitions. For nonlinear systems initialize zero and burn 300 transitions;
no claim that finite burn-in exactly samples a stationary law. Observations
y=H x+eta have independent eta~N(0,R); H is identity or first-three projection,
R=0.09 I in the noisy case and zero otherwise. Noise is independent across
time and from latent innovations. Full nonlinear cases have no observation
noise or partial observation; their observed truth is analytic.

Training seeds 101 through 112: twelve independent trajectories, 1800 retained
states each. Held-out seeds 9001,9002,9003: three trajectories of 49 states,
48 valid increments each, 144 evaluation source states total. Evaluation
trajectories are generated once per case and held fixed across all training
replicates and comparators. Pseudorandom streams are separated by system,
integer seed and role: SHA256 of compact sorted JSON [seed,system,role], first
8 hexadecimal characters as integer, then NumPy SeedSequence([token,20260906]).
Roles distinguish latent trajectory and observation noise. Reusing a seed
number across cases does not reuse a latent path. Do not count systems or
evaluation points as training replications; within each case evaluation points
are temporally correlated and all fits share those same fixed points.
Both training AND held-out trajectories use the same case-specific initial
law and 300-transition burn-in specified above. Hash both retained latent and
observed held-out arrays in partial/noisy cases; only observed arrays enter fits.

## Truth and identification boundary

For full nonlinear observation, exact discrete conditional velocity is
[A x+0.12 tanh(S x)-x]/dt. For full linear, use [A x-x]/dt.
For partial/noisy linear observations, define V=H P H.T+R and C=H A P H.T.
The exact one-step observed conditional velocity is [C V^-1 y-y]/dt,
with conditional next-observation covariance V-C V^-1 C.T. This is a
stationary one-observation conditional expectation, not the latent drift,
not a history-conditioned optimal forecast, and not proof of Markov sufficiency.
Keep analytic conditional covariance separate from observed raw covariance.

Coordinator analytic memory diagnostic (linear cases only): with
C2=H A^2 P H.T, compute Cov(y_next,y_previous | y_current)=C2-C V^-1 C.
For jointly Gaussian observations a nonzero matrix demonstrates remaining
one-lag information after conditioning on the current observation. Full exact
linear observation should give zero to numerical precision. Report this as a
model-derived witness, not an empirical memory estimate or a general test for
nonlinear systems. Do not attach a fitted scientific acceptance threshold.
Freeze numerical identity tolerance at 1e-10 (absolute): Lyapunov residual,
symmetry and full-observation zero-memory witness. Check P,V and conditional
covariance positive definite. A witness above 1e-10 in the partial/noisy models
is resolved nonzero numerical evidence for those specified Gaussian models,
not a statistical significance threshold.

Derivation: Cov(y_next,y)=C, Cov(y,y)=V; apply the Gaussian conditional
mean/covariance formula. References for the mathematical identity and solver:
[Gaussian conditioning proof](https://statproofbook.github.io/P/mvn-cond),
[SciPy discrete Lyapunov equation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_discrete_lyapunov.html).
Independent checks must use algebra or a separate covariance-series calculation,
not simply call the implementation's truth function as its own oracle.

## Estimation, seams and controls

Use unchanged `crossfit_local_chart_b`: local_mean and local_linear,
64 neighbours, minimum support 16, embargo 2*dt. Calls use an artificial
regular time carrier: one training segment, three zero padding states, then
three held-out segments. Training uses only its 1799 genuine increments;
evaluation uses only 48 genuine increments in each held-out segment.
Exclude every padding and inter-segment increment. The first evaluation source
is carrier index 1803; the last train support ends at 1799, a gap of 4*dt,
strictly greater than embargo. Carrier separation is bookkeeping: independent
simulation seeds establish independence, not fabricated elapsed time.

Save segment boundaries, valid increment indices, query-to-original-segment
mapping and array hashes. Do not advertise this carrier as a continuous
recording. Eval target states/velocities never enter training labels or fits.

Comparators: both cross-fit estimators; cross-segment order-corrupted predictions from
each estimator with source mapping roll(arange(144),17), scored against the
original unshifted truths; exact oracle. Never undo the control's displacement.
The order-corruption control is an implementation sanity check, not a formal
null test, temporal shift within a trajectory, or independent resample.
Circular mapping crosses segment boundaries and must be labelled artificial
cross-segment order corruption. Do not tune shift based on results.

## Fixed covariance and estimands

For each query select 64 nearest evaluation source states (stable tie order,
including the query itself) from the 144 fixed evaluation increments.
Compute their RAW observed increment sample covariance (ddof=1), divided by dt.
Do not residualize or replace this tensor with the analytic innovation tensor.
Use this same tensor and neighbour indices for every comparator/replicate.
Alignment is b_bar.T a b_bar / [(b_bar.T b_bar) trace(a)+1e-12], where
b_bar is that comparator's mean velocity over the SAME evaluation neighbours.
Oracle alignment uses the mean exact observed conditional velocity there.
Zero velocity/undefined statistics retain null and a reason, never zero-fill.
This restricted float64 diagnostic does not establish production C1 parity.

Retain per-query truth, predictions, covariances/neighbours and alignments so
coordinator validation can recompute metrics independently. Report per-training
replicate normalized velocity RMSE, alignment bias/rank; then at each fixed
query/component report prediction mean, bias, variance across training repeats,
and descriptive MCSE of the mean. Record ddof explicitly: population variance
(ddof=0) satisfies pointwise empirical MSE=bias^2+variance; unbiased sample
variance (ddof=1) yields MCSE=sqrt(sample_variance/12). Also compute analogous
pointwise alignment bias/variance/MCSE across repeats at the same neighbourhood.
Do not treat spatial or scenario variance as estimator variance. Twelve repeats
give limited precision; no bootstrap/coverage or biological CI is claimed.

## Validation, artifacts and claim ceiling

Small test configs use other seeds; no primary outcome inspection until numeric
spec/code/protocol freeze. Test truth, noise regression, seams, training-label
independence, shifts, moment identities, invalid configs and JSON/provenance.
Review final code independently before primary run; inspect actual outcomes
and controls afterward. Keep failures/refusals and all attempted primary runs.

No new real-data run is necessary: this step changes only synthetic experiments;
the preceding bounded reference established unchanged-estimator input support.
It cannot validate nonlinear/noisy/9D truth. Code and tests stage on H: because
J: is full; integrate only reviewed new files if disk space permits.

Artifacts stay at `H:/SourceRepo2/NeuralManifoldDynamics/project/astra/m3_extension_20260906`.
Record exact commands, source/runtime/spec hashes, independent review and
coordinator verdict. Diaries reserved: ingest 305, analysis 256.
Allowed verdict: bounded implementation PASS or failure; scientific M3 remains
PARTIAL PASS/METHOD-LIMITED unless separately justified. Empirical sufficiency,
history dependence, neural feature validity and downstream prediction remain
separate gates regardless of test success or synthetic recovery.
