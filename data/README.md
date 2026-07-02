# Data

This directory holds the input and output data for the `nmd-analysis`
pipeline. It is organised in logical tiers; `raw/` and `processed/` are
checked in here (cleaned and analysis outputs are generated and gitignored
at the package level).

```
data/
├── raw/            # ingested HDF5 datasets + run manifests (checked in)
├── processed/      # article-specific derived tables too large/slow to
│                    # regenerate quickly, checked in for reproducibility
└── external_cache/ # small files fetched on demand from public mirrors by
                     # article scripts/notebooks (gitignored, not checked in)
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
| `neuralmanifolddynamics_ds004511_20260701_193708` | `ds004511` | OpenNeuro | Final N=44/45 corrected run for the "Neural flow geometry differentiates gambling and cognitive control" article (`articles/Neural flow geometry differentiates gambling and cognitive control/`); 134 H5 sessions (44 GG + 45 CC + 45 Rest) + regional MNPS / block-Jacobian cohort CSVs. |

## `data/processed/` — article-specific derived tables

Some article scripts need a derived table that is expensive to regenerate
(hours of raw-signal processing) but small enough to check in directly, so
reviewers can rerun the *statistical* analysis without repeating the full
raw-EEG/physio feature-extraction pipeline.

| Path | Dataset | Contents | Used by |
| --- | --- | --- | --- |
| `processed/ds004511/features.parquet` | `ds004511` | Epoch-level EEG + physio feature table (57,526 epochs × 161 columns: band power/complexity, HRV, respiration, EOG, EMG, conventional-EEG baselines) produced by the upstream NMD feature-extraction step (see `articles/Neural flow geometry differentiates gambling and cognitive control/handover/handover.md`). | `articles/Neural flow geometry differentiates gambling and cognitive control/src/{00,02,03,06,09,10}_*.py` via `ds004511_support.load_features()` |

`ds004511_support.py` resolves this path automatically (repo-committed copy
first, then an external workstation fallback for the original authors) — see
`_resolve_features_parquet()`. If this file is ever missing, `load_features()`
raises a clear `FileNotFoundError` explaining what's needed and which scripts
require it, rather than failing on an unrelated path error deep in a script.

## `data/external_cache/` — on-demand fetches from public mirrors

`articles/Neural flow geometry differentiates gambling and cognitive control/src/ds004511_support.py::load_events()`
needs a handful of small (~20-50 KB) raw BIDS `events.tsv` files for
`11_event_density_sensitivity.py`. Rather than bundling raw BIDS data, the
loader fetches just these files on demand from the public
[OpenNeuroDatasets/ds004511](https://github.com/OpenNeuroDatasets/ds004511)
GitHub mirror when no local raw-BIDS mirror is found, and caches them under
`data/external_cache/ds004511_events/`. This directory is gitignored — it is
reviewer/runtime-local, not part of the committed dataset.

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

- OpenNeuro datasets (e.g. `ds003969`, `ds004511`) are released under open
  data licenses (typically CC0 or PDDL / OpenNeuro Data License) — confirm
  the license of **each** dataset on its OpenNeuro page before
  redistribution. `ds004511` ("Deception_data", Makowski, Pham & Lau) is
  CC0-licensed, which is why its derived `features.parquet` table and
  small `events.tsv` files can be checked in / fetched here.
- Subject-level data must only be redistributed under the terms of the
  original dataset license and any participant consent it requires. Remove
  or further anonymise any subject data that carries stricter consent terms
  before publishing forks or derived packages.
- The `nmd-analysis` **code** is GPLv3; data retains the license of its
  source dataset.
