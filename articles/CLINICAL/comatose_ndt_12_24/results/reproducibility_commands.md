# Coma 12-24 h pilot reproducibility commands

The pilot entry point is:

```bash
python articles/CLINICAL/comatose_ndt_12_24/src/run_coma_12_24_pilot.py
```

This command targets the currently available processed root:

`J:/repos/NoeticDiffusion/data/raw/neuralmanifolddynamics_physionet_icare_2_1_20260605_060324_12_24h_part1`

It writes a stamped bundle with:

- one full-export `timeline_analysis_*` directory,
- one filtered `12_24h` `mnps_summary_*` directory,
- one filtered `12_24h` `outcome_contrasts_*` directory,
- one `reviewer_checks_*` directory,
- one figure directory under `figures/`,
- and one top-level `pilot_manifest_*.json`.

Useful variants:

```bash
python articles/CLINICAL/comatose_ndt_12_24/src/run_coma_12_24_pilot.py --limit-h5 60
```

```bash
python articles/CLINICAL/comatose_ndt_12_24/src/run_coma_12_24_pilot.py --workers 4
```

```bash
python articles/CLINICAL/comatose_ndt_12_24/src/run_coma_12_24_pilot.py --skip-figures
```

To compile the Typst drafts from the repository root while allowing access to the
shared clinical template, use:

```bash
typst compile --root "J:/repos/NoeticDiffusion/articles/CLINICAL" "J:/repos/NoeticDiffusion/articles/CLINICAL/comatose_ndt_12_24/Recovery-Linked Neural Geometry 12-24 h Pilot After Cardiac-Arrest Coma.typ"
```
