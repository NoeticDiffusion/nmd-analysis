I think this is a **strong analysis-repo integration plan**, and the boundary with ingest is now correctly drawn. I would approve it, but I would make **three important architectural changes before implementation** and a few smaller ones.

The biggest issue is not the local-dynamics mathematics anymore; it is avoiding statistical/grain ambiguity downstream.

## 1. Make `recording`, not `subject`, the primitive grain

This is the most important change.

Right now ds003947 happens to give you 61 H5 files corresponding neatly to 61 participants. That makes

```text
table_grain = subject
```

look natural.

But the H5 artifact is really a **recording/run-level measurement object**. In another dataset you can easily have:

```text
subject A
    run 1
    run 2
    run 3
```

If the adapter itself emits all three as `subject`, the architecture has already opened the door to pseudoreplication.

I would therefore define:

```text
table_grain =
    recording
    recording_horizon
    window
    sequence
    transition
```

Then **subject is created only by an explicit analysis aggregation step**.

So:

[
\text{H5 recording}
\rightarrow
\text{recording metrics}
\rightarrow
\text{subject aggregation}
\rightarrow
\text{group contrast}.
]

For ds003947:

[
1\ \text{recording}=1\ \text{subject}
]

so the results are unchanged.

But the contract becomes future-proof.

I would require identifiers such as:

```text
participant_id
recording_id
session_id
run_id
source_h5
```

where applicable.

And explicit uniqueness:

```text
recording:
    unique(recording_id, coordinate_dimension)

window:
    unique(recording_id, coordinate_dimension, window_id)

sequence:
    unique(recording_id, coordinate_dimension,
           horizon_steps, start_window_id)

transition:
    unique(recording_id, coordinate_dimension,
           source_window_id, target_window_id)
```

This will save you considerable trouble later.

---

# 2. Add `recording_horizon` for FTR

I would also reconsider putting all finite-time horizons into one very wide recording row.

For example:

```text
mean_g_max_h1
mean_g_max_h2
mean_g_max_h4
mean_g_max_h8
mean_d_resp_h1
...
```

works today, but horizon is actually a legitimate analysis dimension.

I prefer:

```text
finite_time_response_recording_horizon.parquet
```

with rows like:

| recording | dim | horizon_steps | actual_sec | g_max_mean | d_resp_mean | c1_mean |
| --------- | --: | ------------: | ---------: | ---------: | ----------: | ------: |

Then maintain a separate recording-level FTR summary for genuinely cross-horizon quantities:

```text
g_peak_over_horizons
tau_peak_over_horizons
peak_horizon_steps
```

So:

[
\text{sequence}
\rightarrow
\text{recording × horizon}
\rightarrow
\text{recording cross-horizon summary}.
]

This is mathematically much cleaner.

It also means that if you later change from

[
h={1,2,4}
]

to

[
h={1,2,4,8,16},
]

you don't change the table schema.

---

# 3. Transition residuals and (Q)-proxy should be **validity blocks first**

This matters scientifically.

I would **not initially register**

```text
transition_residuals_3d
transition_q_proxy_3d
```

as ordinary phenotype-analysis blocks alongside

```text
jacobian_metrics
finite_time_response
```

because they answer a different question.

### Jacobian/FTR

Ask:

> What local dynamics does the fitted model imply?

### Transition residuals/Q proxy

Ask:

> How well does that local model describe the observed evolution, and how much unexplained transition variance remains?

Therefore I would classify analysis families explicitly:

```text
scientific_measurement:
    jacobian_metrics
    finite_time_response

model_validity:
    transition_residuals
    transition_q_proxy
    local_fit_diagnostics

future_scientific_measurement:
    stochastic_reachability
```

You can absolutely statistically compare residual/Q quantities between groups.

But the first interpretation should be:

> **Does model adequacy differ systematically between groups?**

not:

> psychosis has more stochasticity.

That distinction is important.

---

# Add a **differential model-validity gate**

This would be a particularly valuable addition.

Suppose you eventually find:

[
G_{\max}^{FEP}>G_{\max}^{HC}.
]

But simultaneously:

[
\text{transition prediction error}^{FEP}
\gg
\text{transition prediction error}^{HC}.
]

Then the finite-time difference becomes harder to interpret biologically because the local model itself fits one group worse.

So before promoting FTR contrasts, I would require an audit of:

```text
rel_mse_baseline
transition_residual_norm
valid_sequence_fraction
jacobian_valid_fraction
FTR valid support
```

across groups.

Not necessarily a hard rule that these must be identical, but an explicit flag:

```text
differential_model_fidelity = false / warn / fail
```

This is especially useful in clinical data.

It gives us:

[
\boxed{
\text{group difference in dynamics}
\neq
\text{group difference in model fit}
}
]

as an explicit falsification condition.

---

# 4. I would remove the local interim (W_Q) implementation

Your plan currently allows:

> interim calculation from Q-proxy + J/propagator behind a research flag.

I would actually **not implement that yet**.

The central virtue of the architecture we just built is:

> analysis consumes upstream measurement contracts.

If analysis then constructs

[
W_Q
]

independently, you have two implementations:

```text
NMD ingest W_Q
```

and

```text
nmd-analysis local W_Q.
```

Even if one is marked `local_interim`, that's a future parity problem.

I would instead implement only:

```text
if capability stochastic_reachability_v1 exists:
    read it
else:
    explicit unavailable
```

If you need a methodological experiment before ingest emits it, do that in a separate research script/notebook that never registers itself as an analysis type.

That preserves one source of truth.

---

# 5. Capability absence should preserve the denominator

You currently allow missing capabilities to give either empty output or explicit `unavailable`.

I strongly prefer **explicit unavailable recording rows**.

Imagine:

```text
61 recordings
53 have FTR
8 lack FTR
```

If the adapter returns only 53 rows, downstream analysis can easily mistake:

[
N=53
]

for cohort availability rather than capability availability.

Better:

```text
recording_id = X
computation_status = unavailable
failure_reason = capability_missing
```

and metric values:

```text
NaN
```

Then you can always audit:

```text
n_recordings_total = 61
n_capability_present = 53
n_computed = 51
n_valid = 48
```

This is much safer.

---

# 6. I would parameterize dimension rather than duplicate code

Keeping analysis types such as

```text
jacobian_metrics_3d
jacobian_metrics_9d
```

may be convenient for the current registry.

That's fine.

But internally the reader should be one implementation:

```python
read_jacobian_metrics(handle, dimension=3)
read_jacobian_metrics(handle, dimension=9)
```

and every output should carry:

```text
coordinate_dimension = 3 / 9
coordinate_layer
coordinate_contract
```

Likewise FTR.

So even if the adapter registry exposes separate analysis types, **do not create parallel 3D/9D parsing logic**.

That prevents semantic drift.

---

# 7. I would slightly rename the analysis types

With the recording-grain correction, something like this is clearer:

### Jacobian

```text
jacobian_metrics_3d_recording
jacobian_metrics_9d_recording

jacobian_metrics_3d_window
jacobian_metrics_9d_window
```

### FTR

```text
finite_time_response_3d_recording
finite_time_response_9d_recording

finite_time_response_3d_recording_horizon
finite_time_response_9d_recording_horizon

finite_time_response_3d_sequence
finite_time_response_9d_sequence
```

### Residuals

```text
transition_residual_summary_3d_recording
transition_residual_summary_9d_recording

transition_residuals_3d_transition
transition_residuals_9d_transition
```

### Q

```text
transition_q_proxy_3d_recording
transition_q_proxy_9d_recording
```

Notice specifically:

```text
transition_residual_summary
```

for the aggregated surface.

That avoids calling a recording aggregate simply `transition_residuals`, which sounds like the actual residual series.

---

# 8. I would make `local_dynamics` a package, not one file

Given where this is heading, I think:

```text
nmd_analysis/local_dynamics.py
```

will become crowded quickly.

I'd start with:

```text
nmd_analysis/local_dynamics/
    __init__.py
    readers.py
    schemas.py
    adapters.py
    validity.py
```

Potential future additions:

```text
reachability.py
operator_dynamics.py
```

The responsibility split could be:

### `readers.py`

H5 paths/version/capabilities.

### `schemas.py`

Column contracts, grain enums, uniqueness.

### `adapters.py`

H5 → Parquet/table transformation.

### `validity.py`

Support/status/QC gates.

This mirrors the cleanliness you just achieved upstream.

---

# 9. Be careful with the proposed parity test

You write:

> test that H5 series mean agrees with H5-summary.

Good idea, but don't make this generically:

```python
np.mean(series) == summary
```

because different fields have different semantics.

For example:

[
\text{stable reactive fraction}
===============================

\frac{# stable\ reactive}
{# valid},
]

not a mean over every stored window.

And:

[
G_{\rm peak}
]

is a max across horizons.

Some summary quantities may use only validity-masked observations.

So I would freeze a **field-specific aggregation contract**:

```text
spectral_abscissa_mean:
    nanmean(valid series)

stable_reactive_fraction:
    sum(flag & valid) / sum(valid)

g_peak_over_horizons:
    max(valid configured horizons)

...
```

Then parity testing validates the **upstream aggregation semantics**, not merely floating-point equality.

---

# 10. Add inferential tiers now

There are already enough new metrics that the psychosis analysis could become a multiple-comparison machine.

I'd modify analysis config to allow:

```yaml
primary_metrics:
secondary_metrics:
qc_metrics:
exploratory_metrics:
```

For the first ds003947 pilot, I would not call everything primary.

Something narrow such as:

### Jacobian primary

[
\text{spectral abscissa}
]

[
\text{numerical abscissa}
]

[
\text{reactivity gap}
]

[
\text{stable reactive fraction}
]

### FTR primary

At frozen horizons:

[
G_{\max},
\qquad
d_{\rm resp},
\qquad
c_1.
]

### Secondary

```text
symmetric_rate_min
Henrici
family-transfer matrix
peak timing
```

### QC

```text
transition residuals
Q proxy
fit metrics
support metrics
condition number
```

And define correction families explicitly.

Otherwise the new layer could generate dozens of attractive retrospective hits.

---

# 11. I would keep `dynamical_regime`, but not promote it yet

The window rows contain:

```text
dynamical_regime
stable_reactive_flag
```

That's good.

Eventually this lets you analyze things like:

[
P(\text{stable-reactive})
]

or transition structure between:

```text
stable_nonreactive
stable_reactive
unstable
marginal
```

But I would **not mix that operator/regime work into this first integration**.

Get:

1. readers,
2. grains,
3. subject/recording contrasts,
4. model-validity auditing

working first.

Then make regime occupancy/transitions a separate research gate.

---

# Recommended final data model

I would revise your diagram to something like:

```text
                      H5 + manifest
                           │
                           ▼
                  versioned readers
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        recording       window        sequence
        summaries       series        series
             │                             │
             │                         FTR horizon
             │                           layer
             │
             ├──────────── transition series
             │                    │
             │                    ▼
             │              model-validity QC
             │
             ▼
       subject aggregation
             │
             ▼
        cohort contrasts
```

And later:

```text
upstream stochastic_reachability_v1
                  │
                  ▼
          recording summaries
                  │
                  ▼
            cohort analysis
```

No local recomputation.

---

## What I would change in your TODO list

I'd make it:

1. **`local-dynamics-readers`**
   Versioned, capability-gated readers.

2. **`local-dynamics-grain-schema`**
   Freeze recording/window/sequence/transition/recording-horizon identities and uniqueness.

3. **`grain-separated-adapters`**
   Build normalized Parquet surfaces.

4. **`subject-aggregation-guard`**
   Make subject an explicit aggregation product rather than an ingest grain.

5. **`model-fidelity-gate`**
   Residual/support/FTR-validity comparison before biological FTR interpretation.

6. **`ds003947-config`**
   Freeze the final 20260810 run and inferential metric families.

7. **`reachability-consumer`**
   Capability-gated only; no local (W_Q) derivation.

8. **`local-dynamics-tests`**
   Fixtures, parity, grain, support, provenance and full 61-recording run.

## Science-lead verdict

**Proceed**, but I would change the primitive analysis grain from `subject` to **`recording`** before any adapters are written.

That is the one modification I regard as architectural rather than cosmetic.

My other strongest recommendation is to introduce the **differential model-fidelity gate**:

[
\boxed{
\text{Before interpreting a clinical FTR difference, test whether the local model is comparably valid in the contrasted groups.}
}
]

If you make those two changes, I think the analysis repository will be extremely well positioned: it will preserve the ingest contract, prevent repeated-measure pseudoreplication, keep raw local-dynamics sequences away from cohort statistics, and give us a defensible route from the new mathematical surfaces to the first psychosis experiment.
