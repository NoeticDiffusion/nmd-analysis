# nmd-analysis

A Parquet-first analysis pipeline for the **Noetic Diffusion Theory (NDT)**
framework. `nmd-analysis` turns neural time-series (EEG / MEG / fMRI stored
as HDF5) into interpretable coordinates in the **Meta-Noetic Phase Space
(MNPS)** — manifolds, Jacobians, reachability cones, and regional geometry —
and produces statistical contrasts across groups and conditions.

## Pipeline

```text
raw HDF5  ─▶  cleaned Parquet  ─▶  analysis results
   nmd-analysis run            nmd-analysis analyze
```

- **`run`** — raw HDF5 → cleaned Parquet tables
- **`analyze`** — cleaned Parquet → statistics, contrasts, reachability,
  Jacobian summaries
- **`spindle-events`** — event-locked baseline-delta analysis

## Install

Requires Python 3.10+.

```bash
pip install nmd-analysis
```

From source (this repository):

```bash
pip install -e ./nmd-analysis
```

## Quickstart

```bash
# 1. raw H5  ->  cleaned parquet
nmd-analysis run --config nmd-analysis/config/ndt-analysis-ds003490.yaml

# 2. cleaned parquet  ->  analysis results
nmd-analysis analyze --config nmd-analysis/config/analysis-ds003490.yaml
```

## Documentation

Full documentation (API reference, CLI guide, configuration reference,
theory) is hosted on Read the Docs:
<https://nmd-analysis.readthedocs.io>.

The project source, data provenance notes, and full README live at the
repository root of the `nmd-analysis` GitHub project.

## License

Released under the **GNU General Public License v3 (GPLv3)** — see
`LICENSE`.
