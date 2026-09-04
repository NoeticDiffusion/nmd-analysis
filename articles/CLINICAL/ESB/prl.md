# Photic Resonance Loss (PRL)

## One-line summary

`PRL` is a profile-shape score. It asks whether a subject's multi-frequency `ESB-2` curve still resembles the healthy frequency-response pattern, rather than only whether one single frequency is abnormal.

## Core idea

`ESB-2` is stage-local: it tells you how abnormal the response is at one frequency such as `15 Hz`.

`PRL` is profile-level: it compares the subject's full `ESB-2` pattern across frequencies against the healthy median profile. In the current article logic, it is defined as:

```text
PRL_i = 1 - corr( subject_ESB2_profile_i, healthy_median_ESB2_profile )
```

where the profile is the ordered set of `ESB-2` values across the available photic frequencies.

## What it is trying to capture

A healthy cortex is expected to show a structured frequency-tuning pattern rather than a flat or random response surface. `PRL` therefore tries to quantify loss of rhythmic selectivity or loss of healthy profile shape.

Interpretation:

- **Low PRL**: the subject's multi-frequency ESB profile still looks similar to the healthy pattern.
- **High PRL**: the subject's profile shape has drifted away from the healthy pattern.

## Inputs needed

- the subject's `ESB-2` values across multiple stimulation frequencies
- a healthy-group median `ESB-2` profile on the same frequency grid
- a correlation operator

In the current photic ESB article, the profile is based on the four-frequency surface:

- `PHOTO 5 Hz`
- `PHOTO 10 Hz`
- `PHOTO 15 Hz`
- `PHOTO 20 Hz`

## Why PRL is different from ESB-2

- `ESB-2` asks: "How abnormal is this one response point?"
- `PRL` asks: "Has the frequency-response shape itself lost healthy organization?"

So `PRL` is best thought of as a second-layer metric built on top of `ESB-2`, not a replacement for it.

## Current status in this repo

- `PRL` is a **secondary** metric in the current ESB article.
- It was included for transparency and theoretical interest.
- It **did not stabilize as an article-level discriminator** on the present four-frequency surface.
- The manuscript therefore treats `PRL` as a negative or bounded result rather than a headline claim.

## Do not overclaim

In the current repo state, `PRL` should not be described as validated evidence for a resonance-loss theorem. The metric is conceptually useful, auditable, and reproducible, but the present dataset and frequency support were not sufficient to harden it into the article's main empirical claim.

## LLM shorthand

If an LLM needs a compact mental model, use:

> `PRL` = one minus the similarity between a subject's multi-frequency `ESB-2` curve and the healthy median `ESB-2` curve.
