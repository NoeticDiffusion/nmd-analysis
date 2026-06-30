# Theory and naming

`nmd-analysis` is the computational arm of the **Noetic Diffusion** project.
This page summarises the layered naming scheme and the core hypothesis so
that different audiences (public, clinical, neuroscience, ML) can meet the
work at the right level while referring to the same underlying framework.

## Canonical names (and how they relate)

- **Project banner**: Noetic Diffusion
- **Overarching philosophy**: The Reconstructive Theory of Being (RTB)
  - A public-facing umbrella: the self and its world are continuously rebuilt
    from multi-scale noise into coherent experience.
- **Scientific umbrella**: Noetic Diffusion Theory (NDT)
  - The mechanistic account: experience emerges via time-resolved denoising
    (diffusion) guided by learned score functions and rhythmic variance
    schedules.
- **Mathematical core**: Meta-Noetic Diffusion Model (MNDM)
  - The formal score-based generative model (reverse SDE / DDPM-style) over
    meaning-bearing (noetic) states, with an explicit variance schedule.
- **Cartography / visualization**: The Noetic Atlas (over the
  Meta-Noetic Phase Space, MNPS)
  - Tools and figures that map state-space geometry / topology (manifolds,
    hubs, trajectories, entropy slopes).

### Named subsystems (modules within NDT / MNDM)

- **Embodied Anchoring Principle (EAP)**: Insula / ACC self-prior and
  interoceptive precision control.
- **Rhythmic Variance Control (RVC)**: Cross-frequency coupling implements
  the variance schedule; sleep as batch denoising.
- **TRN Variance Gate (TRN-VG)**: Thalamic reticular nucleus as the executor
  of denoising iterations and their timing.
- **Geometric Pharmacology (GP)**: Drugs as curvature / variance modulators;
  lithium as variance stabilizer.
- **Collective Variance Fields (CVF)**: Social coupling as shared variance
  scheduling and distributed denoising.
- **Noetic Diffusion Health Index (NDHI)**: Composite geometry / entropy /
  metastability index for manifold "fitness".

### Relationship diagram

```text
Noetic Diffusion (project/banner)
  ├─ The Reconstructive Theory of Being (RTB)  [philosophical umbrella]
  └─ Noetic Diffusion Theory (NDT)             [scientific/mechanistic umbrella]
       ├─ Meta-Noetic Diffusion Model (MNDM)   [formal equations, code]
       │    ├─ EAP  (Embodied Anchoring Principle)
       │    ├─ RVC  (Rhythmic Variance Control)
       │    └─ TRN-VG (TRN Variance Gate)
       ├─ The Noetic Atlas over MNPS           [maps/metrics/figures]
       ├─ GP   (Geometric Pharmacology)        [clinical translation]
       └─ NDHI (Noetic Diffusion Health Index) [summary metric]
```

## Style guide (when to use which name)

- **Public / philosophical writing**: Lead with RTB; optionally add "powered
  by NDT."
- **Papers, grants, seminars**: Lead with NDT; instantiate the MNDM;
  visualize in the Noetic Atlas.
- **Methods sections**: "We implement the MNDM within NDT and render
  trajectories in the Noetic Atlas (MNPS). EAP sets the self-prior, RVC times
  denoising, and TRN-VG executes iterations."
- **Clinical / translation**: Use GP and NDHI terminology alongside NDT.

## Glossary (selected)

- **Noetic**: Pertaining to intelligible, meaning-bearing states
  (experience-as-structured-content).
- **Variance schedule**: The time-varying control of noise removal across
  denoising iterations (implemented by rhythms / coupling).
- **Score function**: The guiding gradient that steers denoising toward more
  probable, coherent states.

## Core hypothesis — The Diffusion of Being

Consciousness may not be a fixed state or a linear computation, but a
**diffusive process** unfolding in a high-dimensional affective-mnemonic
space. In this view, the *self* is not an object but a **dynamic
reconstruction** — continuously denoised from emotional noise, sensory
input, and memory traces through iterative cycles of prediction, correction,
and forgetting.

### 1. Diffusion as the generative principle of mind

The brain operates as a **probabilistic diffusion system**:

- **Noise** arises from affective centers (amygdala, limbic activity,
  spontaneous cortical fluctuations).
- **Structure** emerges through iterative reconstruction in higher-order
  cortical regions that act as denoisers.
- The *felt world* is the stable equilibrium of these opposing dynamics —
  between emotional turbulence and cognitive constraint.

### 2. Psychopathology as failed diffusion

Mental disorders may be understood as **pathologies of diffusion dynamics**:

| Domain | Diffusion failure | Phenomenological result |
| --- | --- | --- |
| Psychosis | Excessive noise or weakened denoising → runaway reconstruction | Hallucination, delusional world-generation |
| PTSD | Fixed latent "seed" that resists denoising | Intrusive memory loops, traumatic flashbacks |
| Schizophrenia | Desynchronized multi-channel diffusion | Fragmented selves, incoherent narrative worlds |
| Depression | Negatively biased latent manifold | Persistent convergence toward hopeless interpretations |
| Mania | Under-constrained, over-energized diffusion | Expansive, unstable world-creation |
| Drug-induced states | Artificially elevated noise levels | Hyper-associative or chaotic perception |

### 3. Therapeutic and philosophical implications

Healing, from this perspective, is not merely biochemical correction but
**topological rebalancing** of the mind's latent space. Interventions
(pharmacological, psychotherapeutic, contemplative) work by modulating the
**variance, rhythm, and connectivity** of this diffusive process — restoring
coherence between emotion, memory, and perception.

> **In short:**
> Consciousness is diffusion with memory.
> Pathology is diffusion without rhythm.
> Healing is the restoration of rhythmic denoising between feeling, memory,
> and world.

:::{admonition} Research-discipline note
:class: note

The narrative above is a **plausible interpretation / speculative extension**,
not an established external result. `nmd-analysis` provides the computational
machinery to test specific, falsifiable predictions of NDT/MNDM against
neural data; it does not by itself validate the broader philosophical claims.
See the repository `role` documentation for the evidence-category
conventions used throughout this project.
:::
