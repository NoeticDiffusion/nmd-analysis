# Data

This directory holds the input and output data for the `nmd-analysis`
pipeline. It is organised in three logical tiers; only `raw/` is checked in
here (cleaned and analysis outputs are generated and gitignored at the
package level).

```
data/
└── raw/        # ingested HDF5 datasets + run manifests (checked in)
```

Generated at runtime (not in the repo by default):

```
data/cleaned/   # `nmd-analysis run`   output — cleaned Parquet tables
data/analysis/  # `nmd-analysis analyze` output — statistics & contrasts
```

## `data/raw/` — provenance

Each subdirectory of `data/raw/` is an **ingest run** produced by the
upstream `NeuralManifoldDynamics` (MNDM) ingestion tool, named

```
neuralmanifolddynamics_<dataset-id>_<YYYYMMDD>_<HHMMSS>/
```

Each run directory contains:

- `run_manifest.json` — schema `mndm.run_manifest.v2`, recording
  `dataset_id`, `created_at`, `git_rev`, Python version, platform, file
  counts, and the received/processed paths.
- `command_used.txt` — the exact CLI command and provenance line needed to
  reproduce the run.
- `config_ingest_<dataset>.yaml` — the ingest config used.
- `features_snapshot.json`, `normalization_report.json` — feature and
  normalization provenance.
- `regional_mnps_subjects_<HHMMSS>.csv` — regional MNPS subject summary.
- `sub-<id>_<task>/` — per-subject, per-task folders containing the HDF5
  files plus `summary.json`, `qc_summary.json`, `qc_reliability.json`.

### Currently included

| Run | Dataset | Source | Notes |
| --- | --- | --- | --- |
| `neuralmanifolddynamics_ds003969_20260630_105036` | `ds003969` | OpenNeuro | 196 H5 files; 3D MNPS + Jacobian + 9D coords probed. |

## Acquiring datasets

The ingested datasets originate from [OpenNeuro](https://openneuro.org).
To reproduce an ingest:

1. Download the dataset from OpenNeuro (e.g. `ds003969`).
2. Run the upstream `NeuralManifoldDynamics` ingestion tool using the
   `config_ingest_<dataset>.yaml` and `command_used.txt` recorded in the
   run directory.
3. Point the corresponding `nmd-analysis/config/ndt-analysis-<dataset>.yaml`
   `input.h5_root` at the produced run directory.

## Privacy and licensing — read before redistributing

- OpenNeuro datasets (e.g. `ds003969`) are released under open data licenses
  (typically CC0 or PDDL / OpenNeuro Data License) — confirm the license of
  **each** dataset on its OpenNeuro page before redistribution.
- Subject-level data must only be redistributed under the terms of the
  original dataset license and any participant consent it requires. Remove
  or further anonymise any subject data that carries stricter consent terms
  before publishing forks or derived packages.
- The `nmd-analysis` **code** is GPLv3; data retains the license of its
  source dataset.
