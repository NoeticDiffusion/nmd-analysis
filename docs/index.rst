nmd-analysis
============

``nmd-analysis`` is a Parquet-first analysis pipeline for the **Noetic
Diffusion Theory (NDT)** framework. It turns neural time-series (EEG / MEG /
fMRI stored as HDF5) into interpretable coordinates in the
**Meta-Noetic Phase Space (MNPS)** — manifolds, Jacobians, reachability
cones, and regional geometry — and produces statistical contrasts across
groups and conditions.

The pipeline is two-stage:

1. ``run``    — raw HDF5  →  cleaned Parquet tables
2. ``analyze`` — cleaned Parquet  →  analysis results (statistics, contrasts)

.. toctree::
   :maxdepth: 2
   :caption: Getting started

   installation
   cli
   configuration

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api
   visuals
   changelog

.. toctree::
   :maxdepth: 2
   :caption: Background

   theory
