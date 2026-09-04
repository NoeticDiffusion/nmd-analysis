# Hysteresis / Recovery Residual

## One-line summary

In the ESB context, `hysteresis` means residual deformation after the perturbation ends. It asks whether the system returns toward baseline or remains geometrically displaced after stimulation.

## Core idea

A system can fail in at least two different ways under perturbation:

1. it can respond abnormally during stimulation,
2. it can fail to recover after stimulation.

`ESB-2` mainly addresses the first question. `Hysteresis` addresses the second.

Conceptually, the metric is the distance between a post-stimulus residual state and an appropriate pre-stimulus baseline. If the residual state remains far from baseline, recovery is incomplete and hysteresis is high.

## Generic form

At a high level:

```text
H_i = distance( post_stimulus_residual_i, baseline_i )
```

Possible interpretations:

- **Low hysteresis**: the subject returns close to baseline.
- **High hysteresis**: the subject remains displaced after the perturbation, suggesting persistence or incomplete recovery.

## Why state-matching matters

This metric is only interpretable if the baseline and residual states are genuinely comparable.

Example:

- eyes-open residual should ideally be compared to an eyes-open baseline
- post-photic residual should not be cleanly equated with an eyes-closed resting baseline unless that mismatch is explicitly accepted as a limitation

Without state matching, the score can mix true non-recovery with ordinary state differences such as alpha blocking, vigilance change, or sensory-off transition effects.

## Current article-local form

In the current photic ESB work, the exploratory residual term is `h_rest_raw`, defined as the distance between the post-photic residual geometry and the matched `ds004504` resting baseline.

That makes it useful as an exploratory residual-deviation quantity, but not as a clean recovery theorem, because:

- `ds004504` rest is eyes-closed
- the post-photic residual surface is not state matched to that baseline

For that reason, recovery-weighted variants and `ESB-3` are kept outside the manuscript's main claim boundary.

## Relationship to ESB-3

`ESB-3` can be understood as:

- `ESB-2` = evoked deviation during stimulation
- `Hysteresis` = residual non-return after stimulation
- `ESB-3` = a combined score that adds a normalized recovery term to `ESB-2`

This is conceptually attractive because a brittle system may both deform abnormally and fail to spring back. But the recovery term only becomes strong evidence when state matching is good.

## Current status in this repo

- hysteresis/recovery is **conceptually important**
- in the current photic article it remains **exploratory and bounded**
- the strongest defensible manuscript claim is still the `ESB-2` evoked-deviation result, not a recovery-failure theorem

## Do not overclaim

In this repo, hysteresis should be described as a promising recovery-oriented layer whose interpretation depends heavily on baseline design. The current data do not yet justify a strong clinical claim about persistent post-photic non-recovery.

## LLM shorthand

If an LLM needs a compact mental model, use:

> `Hysteresis` = post-perturbation residual distance from baseline; high values mean the system did not cleanly return.
