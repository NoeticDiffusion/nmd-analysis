# Notebook: reproducing this article's results

`reproduce_results.ipynb` lets a reviewer run **selected parts** (or all) of
the analysis pipeline behind "Neural flow geometry differentiates gambling
and cognitive control despite matched sympathetic arousal" (dataset:
OpenNeuro `ds004511`, CC0).

## Quickstart

1. From the repo root, install dependencies: `pip install -r requirements.txt`.
2. Launch Jupyter from this `notebook/` folder (or anywhere inside the repo —
   the notebook locates the article directory automatically):
   ```
   jupyter lab
   ```
3. Open `reproduce_results.ipynb` and run cells top-to-bottom, or jump to a
   specific section using the claim-ledger table at the end of the notebook.

## What each section needs and how long it takes

| Section | Script | Data | Approx. runtime |
| --- | --- | --- | --- |
| Setup + data check | — | — | instant |
| 00 | `00_sanity_check.py` | bundled | a few seconds |
| 01 | `01_cross_task_mnps.py` | bundled | a few seconds |
| 02 | `02_eap_physio_coupling.py` | bundled | ~10-30s (2000 bootstrap draws) |
| 03 | `03_mnj_reachability.py` | bundled | ~1-2 min (134 HDF5 sessions) |
| 05 | `05_mnj_confound_audit.py` | bundled | **~2-5 min** (two H5 passes + 2000 bootstrap + 5000 permutation iterations) — the slowest section |
| 06 | `06_eda_extraction.py` | external-only (raw physio); falls back to committed output | instant (fallback) / long (full rerun, requires `neurokit2` + raw BioPac data) |
| 07 | `07_eda_confound_control.py` | committed-only | instant |
| 08 | `08_make_figures.py` | committed-only | a few seconds |
| 09 | `09_conventional_eeg_baseline.py` | bundled | a few seconds |
| 10 | `10_corrugator_emg_confound.py` | bundled + committed-only | a few seconds |
| 11 | `11_event_density_sensitivity.py` | bundled + network-fetch | **~1-3 min on first run** (fetches ~130 small `events.tsv` files from GitHub), near-instant afterwards (cached under `data/external_cache/`) |

Sections are independent of each other — each reads fixed, already-committed
intermediate results rather than another section's fresh output, so you can
run any single section (or run them out of order) without side effects on
the others.

## If something doesn't run

- **`FileNotFoundError` for `features.parquet`**: confirm
  `data/processed/ds004511/features.parquet` exists in your checkout (it's
  checked in via Git; if using Git LFS or a shallow/partial clone, make sure
  it was actually fetched).
- **Section 11 can't reach GitHub**: it needs outbound internet access to
  `raw.githubusercontent.com`; if you're offline, skip this section — every
  other section is unaffected.
- **Section 06**: this is the one genuinely external-data-dependent step
  (raw BioPac physiology, tens of GB). The notebook automatically falls back
  to the committed `eda_features.parquet` so Sections 07/08 still work.
