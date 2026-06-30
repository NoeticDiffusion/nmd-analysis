# nmd-analysis

A Parquet-first analysis pipeline for the **Noetic Diffusion Theory (NDT)**
framework. `nmd-analysis` turns neural time-series (EEG / MEG / fMRI stored as
HDF5) into interpretable coordinates in the **Meta-Noetic Phase Space
(MNPS)** — manifolds, Jacobians, reachability cones, and regional geometry —
and produces statistical contrasts across groups and conditions.

It is the computational arm of the broader **Noetic Diffusion** project
(philosophical umbrella: *The Reconstructive Theory of Being*, RTB). See
[the theory docs](https://nmd-analysis.readthedocs.io/en/latest/theory.html)
for the naming scheme and core hypothesis.

## Pipeline at a glance

```text
raw HDF5  ──▶  cleaned Parquet  ──▶  analysis results
   nmd-analysis run            nmd-analysis analyze
```

- **`run`** — raw HDF5 → cleaned Parquet tables
- **`analyze`** — cleaned Parquet → statistics, contrasts, reachability,
  Jacobian summaries
- **`spindle-events`** — event-locked baseline-delta analysis

## Installation

Requires Python 3.10+. The package lives in the `nmd-analysis/`
subdirectory:

```bash
git clone https://github.com/nmd-analysis/nmd-analysis.git
cd nmd-analysis
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# . .venv/Scripts/activate       # Windows PowerShell
pip install -e ./nmd-analysis
```

The optional full research stack (MNE, Nilearn, topological / recurrence /
criticality toolkits) is in `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Quickstart

```bash
# 1. raw H5  ->  cleaned parquet
nmd-analysis run --config nmd-analysis/config/ndt-analysis-ds003490.yaml

# 2. cleaned parquet  ->  analysis results
nmd-analysis analyze --config nmd-analysis/config/analysis-ds003490.yaml
```

Configs come in two families (see
[Configuration](https://nmd-analysis.readthedocs.io/en/latest/configuration.html)):

- `nmd-analysis/config/ndt-analysis-<dataset>.yaml` — dataset configs for `run`
- `nmd-analysis/config/analysis-<dataset>.yaml` — analysis configs for `analyze`

## Documentation

Full documentation is hosted on Read the Docs:
<https://nmd-analysis.readthedocs.io>.

It includes an [API reference](https://nmd-analysis.readthedocs.io/en/latest/api.html)
(auto-generated from docstrings), a [CLI guide](https://nmd-analysis.readthedocs.io/en/latest/cli.html),
a [configuration reference](https://nmd-analysis.readthedocs.io/en/latest/configuration.html),
and the [theory / naming](https://nmd-analysis.readthedocs.io/en/latest/theory.html)
background.

Build the docs locally:

```bash
pip install -r docs/requirements.txt
sphinx-build -b html docs docs/_build/html
```

## Repository layout

```
nmd-analysis/
├── nmd-analysis/        # the nmd_analysis Python package
│   ├── nmd_analysis/    # library modules (pipeline, analysis, reachability, …)
│   ├── config/          # dataset + analysis YAML configs
│   ├── tests/           # pytest suite
│   └── visuals/         # standalone plotting scripts
├── data/                # raw / cleaned / analysis data (see data/README.md)
├── docs/                # Sphinx documentation source
├── .readthedocs.yaml    # Read the Docs build config
├── pyproject metadata   # see nmd-analysis/pyproject.toml
├── LICENSE              # GPLv3
└── CHANGELOG.md
```

## License

Released under the **GNU General Public License v3 (GPLv3)** — see
[LICENSE](LICENSE).

## Status

This is a research codebase. Theoretical claims of NDT/MNDM are
plausible interpretations / speculative extensions unless backed by a
specific, reproducible analysis run from this repository. See the
`docs/theory` research-discipline note for the evidence-category
conventions used throughout the project.
