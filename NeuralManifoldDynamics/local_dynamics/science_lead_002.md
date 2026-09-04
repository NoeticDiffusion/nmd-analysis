Yes. This version is now **architecturally sound enough that I would stop redesigning it and move toward implementation**. The important changes from the previous draft are all there: recording is primitive, subject is derived, FTR has its own `recording_horizon` grain, residual/Q is treated as model validity, no local (W_Q) is manufactured, and the inferential families are beginning to be frozen. 

I would make **four changes before freezing**, plus a few smaller cleanups.

## 1. Include the coordinate contract in every uniqueness key

This is the most important remaining schema point.

You currently freeze, for example:

```text
(recording_id, coordinate_dimension)
```

for recording rows.

But one of the core principles of the entire NMD architecture is that different coordinate contracts must not silently mix. A recording could eventually have, for example, both a subject-anchored and cohort-anchored 9D surface.

So I would use:

```text
(recording_uid, coordinate_dimension, coordinate_contract)
```

and correspondingly:

```text
window:
(recording_uid,
 coordinate_dimension,
 coordinate_contract,
 window_id)

sequence:
(recording_uid,
 coordinate_dimension,
 coordinate_contract,
 horizon_steps,
 start_window_id)

transition:
(recording_uid,
 coordinate_dimension,
 coordinate_contract,
 source_window_id,
 target_window_id)
```

Ideally `coordinate_contract` here is not merely a human-readable label but a **stable contract ID/digest**.

I would also prefer `recording_uid` over a generic `recording_id`, constructed deterministically from dataset/session/run/acquisition identity. Otherwise recording IDs from two datasets can eventually collide.

This reinforces exactly the boundary the plan already wants. 

---

# 2. Subject aggregation should really mean **subject × condition**

This is a subtle future pseudoreplication issue.

The new plan correctly says:

[
\text{recording}\rightarrow\text{subject}\rightarrow\text{contrast}.
]

But consider a later within-subject dataset:

```text
subject 01:
    rest run 1
    rest run 2
    task run 1
    task run 2
```

You absolutely do **not** want a generic recording → subject mean, because that would average away the experimental condition.

The real hierarchy should be:

[
\boxed{
\text{recording}
\rightarrow
\text{subject-condition}
\rightarrow
\text{inferential contrast}
}
]

So I'd freeze something like:

```text
aggregation_keys:
    participant_id
    condition
    session?        # depending on design
```

and:

```text
subject_aggregation_policy:
    identity
    mean_within_condition
    median_within_condition
    selected_recording
```

For ds003947 it is trivial because the design effectively gives you one relevant resting recording per participant. But making this explicit now prevents the analysis framework from later averaging wake/NREM, drug/placebo, or rest/task together.

Internally I would possibly call the grain:

```text
subject_condition
```

rather than simply `subject`.

---

# 3. Move all horizon-specific 9D transfer metrics to `recording_horizon`

There is one small inconsistency in section 3.

You correctly put:

```text
g_max_mean
gamma_1_mean
d_resp_mean
c_1_mean
```

in the `recording_horizon` surface.

But the preceding line says the cross-horizon FTR recording row contains:

> cross-horizon `g_peak...` and **9D transfer fields**. 

The transfer matrix

[
T_{a\leftarrow b}(h)
]

is inherently horizon-dependent.

So I would place:

```text
transfer_m_from_m
transfer_m_from_d
transfer_m_from_e
...
transfer_self
transfer_cross
```

in:

```text
finite_time_response_9d_recording_horizon
```

not the cross-horizon recording row.

The recording-level FTR table should contain only metrics that genuinely collapse across horizons:

```text
g_peak_over_horizons
tau_peak_over_horizons
peak_horizon_steps
```

plus perhaps explicitly named derived summaries such as:

```text
max_transfer_cross_over_horizons
```

**only if upstream actually defines them**.

Do not let analysis invent such cross-horizon summaries implicitly.

---

# 4. The model-fidelity gate needs a frozen decision rule

I strongly like this addition:

```text
differential_model_fidelity = false|warn|fail
```

But this cannot remain a qualitative implementation decision.

Otherwise the analyst can see an interesting FTR result and subsequently decide that the model-fidelity difference is "small enough."

Freeze how it is determined **before viewing the clinical FTR contrasts**.

I would assess at least:

[
\text{rel-MSE},
]

[
\text{transition residual norm},
]

[
\text{Jacobian valid fraction},
]

[
\text{FTR valid-sequence fraction},
]

and missing/capability rates.

Then something along the lines of:

```text
PASS:
    no material group imbalance in model validity

WARN:
    some imbalance, but adequate support in both groups

FAIL:
    severe differential fit/support failure capable of
    confounding the FTR contrast
```

The exact numerical thresholds can be designed from the measurement behavior, but they should be **predeclared and independent of the FTR effect direction**.

And importantly:

> `FAIL` should normally downgrade/block biological interpretation, not silently delete the problematic group or subjects.

Otherwise the QC gate itself can introduce selection bias.

---

# I would also tighten the inferential hierarchy

This is already moving in the right direction:

> primary Jacobian = spectral abscissa, numerical abscissa, reactivity gap, stable-reactive fraction
> primary FTR = (G_{\max},d_{\rm resp},c_1) at predefined horizons. 

The remaining danger is the phrase **"at predefined horizons."**

Suppose there are four horizons. Then the FTR primary surface becomes:

[
3\times4=12
]

tests per contrast before 3D/9D or other subdivisions.

I would therefore freeze one of two approaches.

### Preferred for the first psychosis pilot

Choose **one primary horizon** per FTR layer:

[
h^*.
]

Then:

```text
Primary:
    G_max(h*)
    d_resp(h*)
    c1(h*)

Secondary:
    same metrics at other horizons
```

This gives the pilot an extremely readable claim surface.

### Alternative

Treat all configured horizons as one multiplicity family and correct them jointly.

I prefer the first option initially.

The `recording_horizon` table still preserves all of the data; we're only narrowing inference.

---

# Q-proxy naming needs one small safeguard

You propose:

```text
trace_Q
logdet_Q
rank/effective-rank
```

This is okay if the upstream covariance is always full-rank after regularization.

But because you explicitly have PSD/rank handling, I'd make the determinant naming mathematically explicit.

If it is calculated after regularization:

```text
q_logdet_regularized
```

If it is a pseudodeterminant:

```text
q_log_pdet
```

rather than just:

```text
logdet_Q
```

Otherwise a future reader won't know whether a singular 9D covariance was repaired, truncated or pseudodeterminanted.

I also support keeping these values under:

```text
model_validity
```

rather than a normal clinical metric family.

---

# Add a small capability/availability table

Your explicit `unavailable` recording rows are an excellent design choice. 

I would go one step further and generate one simple table:

```text
local_dynamics_availability.parquet
```

with, for each recording/dimension/contract:

```text
recording_uid
coordinate_dimension
coordinate_contract

jacobian_metrics_available
finite_time_response_available
transition_residuals_available
transition_q_proxy_available
stochastic_reachability_available

jacobian_computation_status
ftr_computation_status
q_computation_status

failure_reason
```

Then every audit can immediately answer:

> 61 recordings existed; 61 had Jacobian metrics; 61 had FTR; 60 had admissible Q; 0 had stochastic reachability.

without reconstructing that information from multiple Parquet tables.

Not essential, but I think it would pay off quickly.

---

# One test wording should change

At the end you still say:

> "full 61-subject-run". 

Given the architectural correction, I would change that to:

> **full 61-recording ingestion, followed by verification of the resulting subject-analysis-unit count.**

For ds003947 that may still be 61 subjects, but the wording should follow the contract.

This is small, but it helps enforce the mental model.

---

# I agree with the package layout

This now looks right:

```text
nmd_analysis/local_dynamics/
    readers.py
    schemas.py
    adapters.py
    validity.py
```

and reserving:

```text
reachability.py
operator_dynamics.py
```

is sensible. 

I would **not create `operator_dynamics.py` yet**, though. Reserve the name in documentation, but create the module only when there is code. Empty placeholder modules tend to become misleading architecture fossils.

---

# I strongly agree with not computing (W_Q) locally

This line should remain:

> no interim (W_Q) calculation in `nmd-analysis`. 

That is exactly the correct ownership model:

[
\boxed{
\text{NMD ingest}
=================

\text{measurement definition}
}
]

[
\boxed{
\text{nmd-analysis}
===================

\text{statistical use of measurement}
}
]

A research notebook can certainly experiment with

[
Q+\Phi\rightarrow W_Q,
]

but if the result proves useful, implementation should go **back upstream** and become a versioned ingest capability before it enters production analyses.

---

# My recommended final grain hierarchy

I'd freeze this explicitly in the documentation:

[
\boxed{
\begin{array}{c}
\text{recording}\
\downarrow\
\text{window / sequence / transition}
\end{array}
}
]

with FTR additionally having:

[
\boxed{
\text{recording}\times\text{horizon}
}
]

and inferential aggregation:

[
\boxed{
\text{recording}
\rightarrow
\text{subject-condition}
\rightarrow
\text{contrast}.
}
]

That gives every table a precise scientific meaning.

---

## Final verdict

**Approve with minor revision.**

I no longer see a structural flaw in the plan. The four things I would change before coding are:

1. include **coordinate contract** in grain uniqueness;
2. formalize recording → **subject-condition**, not generic subject;
3. put horizon-specific **9D transfer metrics in `recording_horizon`**;
4. freeze the **differential model-fidelity decision rule** independently of clinical results.

Then I would implement.

Most importantly, I think you should resist further architectural expansion at this point. `operator_dynamics`, stochastic reachability, (W_C/W_O), pseudospectral margins, etc. can all come later. The immediate scientific value is now to get a **clean ds003947 Jacobian Metrics + FTR pilot** through this pipeline and see whether the new metrics actually reveal anything beyond the existing psychosis findings. That is the next falsifiable step, and the revised plan gives us a defensible way to do it.
