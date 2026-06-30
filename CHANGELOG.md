# Changelog

All notable changes to `nmd-analysis` are documented here.
This file follows [Keep a Changelog](https://keepachangelog.com/) principles
and the project adheres to [Semantic Versioning](https://semver.org/).

## 0.1.0 — initial public release

- First public release of the `nmd-analysis` package.
- Two-stage Parquet-first pipeline: `run` (raw H5 → cleaned Parquet) and
  `analyze` (cleaned Parquet → analysis results).
- Block-native sidecar loader, anchor-surface reader, regional MNPS,
  reachability cones, spindle event-locked analysis, EEG classical
  comparators.
- Typer CLI with `run`, `analyze`, `spindle-events` subcommands.
- Sphinx documentation published to Read the Docs.
