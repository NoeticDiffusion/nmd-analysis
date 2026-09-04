# Evoked Structural Brittleness (ESB-2)

## One-line summary

`ESB-2` is a robust distance-from-healthy score in a 2D evoked-response space. It asks: how far does a subject's photic response depart from the healthy template after subtraction of that same subject's resting baseline?

## Core idea

The metric is built from two response axes at a given stimulation frequency `f`:

- `Delta C`: change in evoked capacity relative to rest
- `Delta R`: change in evoked guidance relative to rest

For subject `i`:

- `Delta C_i(f) = C_i(f) - C_i(rest)`
- `Delta R_i(f) = R_i(f) - R_i(rest)`

The healthy reference is the median healthy response at that frequency, with robust scaling by the healthy-group median absolute deviation (`MAD`) on each axis.

## Formula

Let:

- `h_C(f)` = healthy median of `Delta C`
- `h_R(f)` = healthy median of `Delta R`
- `s_C(f)` = healthy MAD of `Delta C`
- `s_R(f)` = healthy MAD of `Delta R`
- `epsilon` = small numerical stabilizer

Then:

```text
ESB-2_i(f) =
  (1 / sqrt(2)) *
  sqrt(
    ((Delta C_i(f) - h_C(f)) / (s_C(f) + epsilon))^2 +
    ((Delta R_i(f) - h_R(f)) / (s_R(f) + epsilon))^2
  )
```

Equivalent intuition:

1. rest-subtract the subject,
2. locate the subject in `Delta C / Delta R` space,
3. standardize each axis relative to the healthy template,
4. compute robust Euclidean distance from the healthy centroid.

## Inputs needed

- a subject-level resting baseline
- a subject-level photic-stage summary
- one capacity feature
- one guidance feature
- a healthy comparison group to define the template

In the current ESB article, the primary specification is:

- capacity = parietal-occipital `tube_d_eff_median`
- guidance = global `rotational_power_median`
- baseline = matched `ds004504` rest

## How to read the score

- **Low ESB-2**: the subject's evoked response is close to the healthy template.
- **High ESB-2**: the subject's evoked response deviates strongly from the healthy template.

Important limitation: `ESB-2` is a scalar magnitude, not a direction label. A high score means "abnormal evoked deformation," but not by itself whether the abnormality is mainly capacity-led, guidance-led, blunted, or misaligned. That requires looking back at the component axes.

## Current status in this repo

- `ESB-2` is the **primary empirical metric** in the photic ESB follow-up article.
- The strongest realized disease-versus-healthy separation is at `PHOTO 15 Hz`.
- The current interpretation is **posterior-capacity-led** rather than purely guidance-led.
- The metric is described as **internally stabilized**, not externally validated.

## Do not overclaim

`ESB-2` is not currently a general biomarker theorem. In this repo it should be described more narrowly as a healthy-template deviation score on a frozen, article-local photic surface with explicit QC and bounded interpretation.

## LLM shorthand

If an LLM needs a compact mental model, use:

> `ESB-2` = robust distance between a subject's rest-to-photic response vector and the healthy rest-to-photic response template in capacity-guidance space.
