## Överlämning till analysrepo: I-CARE H5 (nya strukturer)

Här är en direkt överlämning ni kan använda i analysrepot för I-CARE-exporterna.

- **Scope:** gäller I-CARE-körningarna med `time_reference.v1` aktiverat via `mndm/config/config_ingest_physionet_i-care_2_1.yaml` och `mndm/config/config_ingest_physionet_i-care_2_1_sleep_spindles.yaml`.
- **Validerat på faktiska filer:** t.ex. under `E:/Science_Datasets/physionet/processed/physionet_icare_2_1/neuralmanifolddynamics_physionet_icare_2_1_20260513_073832` och `..._073909`.

### 1) Bakåtkompatibilitet (oförändrat)
- Canonical tidsaxel är fortfarande:
  - `/time`
  - `/window_start`
  - `/window_end`
- Existerande analyskod som bara använder dessa pathar ska fortsätta fungera.

### 2) Ny H5-struktur för tid (Time Reference v1)
Nytt under:
- `/extensions/time_reference/run/*`
- `/extensions/time_reference/windows/*`

**Run-nivå (`/extensions/time_reference/run/*`) innehåller bl.a.:**
- `schema_version` (`time_reference.v1`)
- `parser` (`wfdb_header`)
- `status` (ex. `ok`)
- `anchor_mode` (ex. `first_recording`)
- `header_path` (vilken `.hea` som användes)
- `run_start_clock_raw`, `run_end_clock_raw` (text från WFDB-header)
- `run_start_clock_sec`, `run_end_clock_sec` (sekunder, rollover-hanterat)
- `run_start_elapsed_sec`, `run_end_elapsed_sec` (sekunder relativt subject-anchor)
- `run_duration_sec`
- `subject_anchor_start_sec`
- `bins_hours`, `bins_seconds`, `parse_errors`

**Window-nivå (`/extensions/time_reference/windows/*`) innehåller:**
- `window_start_from_run_sec`
- `window_end_from_run_sec`
- `window_start_from_anchor_sec`
- `window_end_from_anchor_sec`
- `window_bin_id` (`int32`)
- `window_bin_label` (stränglabels, ex. `0-24h`)

### 3) Nya root-attribut i H5 (snabbåtkomst)
Nya attrs med prefix `time_reference_*`, bl.a.:
- `time_reference_schema_version`
- `time_reference_source`
- `time_reference_status`
- `time_reference_anchor_mode`
- `time_reference_header_path`
- `time_reference_run_start_elapsed_sec`
- `time_reference_run_end_elapsed_sec`
- `time_reference_subject_anchor_start_sec`
- `time_reference_enabled`

### 4) Metadata från `0332.txt` (nu i H5)
För I-CARE-sidecar (`0332.txt`) finns metadata i:
- root attrs med `meta_*` (ex. `meta_outcome`, `meta_cpc`, `meta_age`, etc.)
- `/participant/row_json`
- `/participant/mapped_json`
- `/participant/source_json`
- `/participant` attrs med `field_*`, `mapped_*`, `source_*`

### 5) Summary/manifest för downstream-detektion
- `summary.json` innehåller nu ett `time_reference`-block (status, anchor, bins, run offsets).
- `run_manifest.json` innehåller:
  - `capabilities.time_reference`
  - `capabilities.time_reference_path` (`/extensions/time_reference`)
  - `capabilities.counts.h5_with_time_reference`
  - field guide för time-reference-pathar

### 6) Rekommenderad lässtrategi i analysrepo
- Primär patient-relativ tid: `window_start_from_anchor_sec` / `window_end_from_anchor_sec`.
- Om time-reference saknas: fallback till `/window_start` / `/window_end`.
- Tolka `status` defensivt (`ok`, `ok_with_warnings`, etc.) och logga `parse_errors` vid behov.
- Dekoda bytes→str för textfält där `h5py` returnerar bytes.

```python
with h5py.File(h5_path, "r") as f:
    has_tr = "extensions" in f and "time_reference" in f["extensions"]
    if has_tr and "windows" in f["extensions"]["time_reference"]:
        w = f["extensions"]["time_reference"]["windows"]
        t0 = w["window_start_from_anchor_sec"][()]
        t1 = w["window_end_from_anchor_sec"][()]
    else:
        t0 = f["window_start"][()]
        t1 = f["window_end"][()]
```

### 7) Notering om coverage
- För subject `0332` skippades en kort run (`run-001/acq-022`) av coverage-regler i summarize.
- Förväntat i dessa valideringskörningar: 6 H5 istället för 7 för just den subject-körningen.

Om du vill kan jag också skriva detta som ett färdigt PR-issue-template för analysrepot (med checklista för reader-migrering och valideringstester).