# Handover: RVC/TRV Analysis — NMD → Analysis Repo

**Date:** 2026-07-02  
**From:** NeuralManifoldDynamics (NMD) ingest pipeline  
**To:** Analysis repo (Pass A / B / C)

---

## 1. What has been done

The full RVC/TRV dual-dataset pipeline is complete and Gate #2 QC has passed. Four output roots are frozen on K: drive. The analysis repo should not modify NMD outputs; all further work happens on the analysis side.

**Datasets:**
- **ANPHY** — 27 subjects, HD-EEG sleep (Biosemi, 93 channels), local dataset at `M:/datasets/received/ANPHY/Subjects/`
- **BOAS / ds005555** — 128 subjects, PSG sleep, OpenNeuro dataset

**Four frozen output roots:**

| Surface | Dataset | Run directory |
|---------|---------|---------------|
| Primary EEG-only | ANPHY | `K:/ExternalReceivedDatasets/mndm_rvc_processed/ANPHY/ANPHY/neuralmanifolddynamics_ANPHY_20260702_082429/` |
| Primary EEG-only | BOAS | `K:/ExternalReceivedDatasets/mndm_rvc_processed/ds005555/ds005555/neuralmanifolddynamics_ds005555_20260702_080821/` |
| Anchor-augmented sensitivity | ANPHY | `K:/ExternalReceivedDatasets/mndm_rvc_processed/ANPHY/ANPHY/neuralmanifolddynamics_ANPHY_20260702_084940/` |
| Anchor-augmented sensitivity | BOAS | `K:/ExternalReceivedDatasets/mndm_rvc_processed/ds005555/ds005555/neuralmanifolddynamics_ds005555_20260702_084946/` |

Distinguish surfaces using `run_manifest.json → config.digest_sha256` (first 16 chars):

| Surface | Dataset | config_hash |
|---------|---------|-------------|
| Primary | ANPHY | `b6d72c504414c540` |
| Anchor-aug | ANPHY | `e52ce463339d642b` |
| Primary | BOAS | `19e24fb3acea8f8e` |
| Anchor-aug | BOAS | `1374fa95bc12d6d1` |

---

## 2. Per-subject outputs

Each subject directory (e.g. `sub-EPCTL16_sleep_sleep/`) under the run root contains:

**H5 file** (`sub-EPCTL16_sleep_sleep.h5`) — the main geometry export. Key groups:

| H5 group | Content |
|----------|---------|
| `coords_9d/values` (538 × 9) | 9D MNPS coordinates per window |
| `coords_9d/names` | `[m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m]` |
| `mnps_3d/values` (538 × 3) | Primary 3D MNPS |
| `anchor_state/values` (538 × 5) | Composite anchor indices per window |
| `anchor_state/names` | ANPHY: `[sympathetic_index, vagal_index, anchor_index, ocular_stability_index, anchor_index_v02]` / BOAS: `[sympathetic_index, anchor_index, resp_anchor_index, ocular_stability_index, anchor_index_v02]` |
| `features_raw/values` (538 × N_feats) | All extracted features — raw, used for anchor join |
| `features_raw/names` | Feature names including `ecg_hrv_rmssd_ms` (ANPHY) and `resp_regular_index` (BOAS) |
| `labels/stage` | AASM sleep stage per window |
| `time` | Window center times (seconds) |
| `jacobian/` | MNJ (3D) |
| `jacobian_9D/` | MNJ (9D) |
| `regional_mnps/` | Per-network regional MNPS (17 networks, ANPHY) |

**Event-locked parquet** (`sub-EPCTL16_sleep_event_locked_v1_eeg.parquet`) — the primary analysis input. One row per aligned window × event/control. Key columns:

| Column | Description |
|--------|-------------|
| `condition` | `spindle_event` or `matched_control` |
| `bin_label` | `pre_far`, `pre_near`, `event`, `post_near`, `post_far` (spindle_event only); `control` (matched_control) |
| `event_id` | Window-level identifier |
| `matched_event_id` | For controls: links back to the source spindle's `event_id` |
| `subject_id` | e.g. `sub-EPCTL16` |
| `m, d, e` | MNPS 3D coordinates |
| `m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m` | Full 9D coordinates |
| `coords_9d_finite` | 1 = all 9D coords finite (use as validity filter) |
| `sympathetic_index`, `vagal_index`, `anchor_index`, `ocular_stability_index`, `anchor_index_v02` | Composite anchor state (aligned to window) |
| **`ecg_hrv_rmssd_ms`** (ANPHY) | Raw cardiac HRV — **Pass C primary anchor**, 0% NaN |
| `ecg_hrv_sdnn_ms`, `ecg_hrv_pnn50` | Additional HRV metrics |
| **`resp_regular_index`** (BOAS) | Raw respiratory regularity — **Pass C primary anchor**, NaN for ~66/128 subjects |
| `resp_depth_index`, `resp_rate_bpm` | Additional respiratory metrics |
| `n2`, `n3`, `rem`, `wake` | Stage indicators (1/0) |
| `event_onset_sec`, `event_duration_sec` | Spindle timing |
| `frequency_hz` | YASA spindle peak frequency |
| `event_channel` | Detection channel (e.g. `C3`, `PSG_C3`) |
| `event_type` | `sleep_spindle` |
| `match_rank`, `match_distance`, `matched_event_id` | Control matching metadata |
| `window_center_sec` | MNPS window center time (seconds) |
| `window_id` | Direct index into H5 `features_raw/values` rows |
| `dataset_id` | `ANPHY` or `ds005555` |
| `profile_name` | `rvc_spindle_v1` |

---

## 3. Geometry contract (dual-surface design)

The dual-surface contract must NOT be violated during analysis.

**Primary surface** (use for Pass A and Pass C):
- `e_m` composed of EEG-only features: `eeg_hjorth_mobility (0.6) + eeg_beta_alpha (0.4)`
- No cardiac, respiratory, or other body signals enter `coords_9d`
- Body signals are in `anchor_state` sidecars and event-locked rows only
- All inferences about spindle geometry effects and EAP moderation use this surface

**Anchor-augmented sensitivity surface** (Pass B only):
- ANPHY `e_m`: `ecg_hrv_rmssd_ms (0.8) + eeg_hjorth_mobility (0.2)` — HRV enters geometry
- BOAS `e_m`: `resp_regular_index (0.7) + eeg_beta_alpha (0.3)` — resp enters geometry
- Use only to answer: "Does the spindle effect persist / weaken when the anchor signal is embedded inside the geometry?"
- Do NOT use anchor-aug geometry for the main scientific claim

**Surface divergence (empirical check):**

| Dataset | Subject | r(primary e_m, aug e_m) |
|---------|---------|--------------------------|
| ANPHY | EPCTL16 | 0.38 — large shift (HRV orthogonal to EEG) |
| BOAS | sub-85 | 0.94 — smaller shift (resp partly tracks EEG state) |

---

## 4. Gate #2 QC results (summary)

| Check | Status |
|-------|--------|
| ANPHY `ecg_hrv_rmssd_ms` in event-locked rows | ✅ 0% NaN, all bins |
| BOAS `resp_regular_index` in event-locked rows | ⚠ 0% NaN in 54/128 subjects; **66/128 have no respiratory channel** — data limitation, must restrict N for Pass C |
| Primary geometry free of body signals | ✅ Clean |
| Matched controls are N2, within-subject | ✅ >99.8% N2 purity |
| All 5 spindle time bins populated | ✅ |
| Primary vs anchor-aug runs unambiguously identified | ✅ via config_hash |
| Detector covariates (`duration`, `frequency_hz`) | ✅ usable |
| `sigma_power` | ❌ absent — YASA v1 CSV only has `onset_sec`, `duration_sec`, `peak_sec`, `frequency_hz`. Add as post-Pass-A follow-up if reviewers require |

---

## 5. Analysis plan: Pass A → B → C

### Pass A — Primary RVC replication

**Input:** Primary EEG-only event-locked parquets (both datasets).

**Filter rows before modelling:**
```python
df = df[df["coords_9d_finite"] == 1]
df = df[df["n2"] == 1]  # N2 only (already enforced by design, but verify)
```

**Model (per dataset, then meta-analysis):**
```
geometry_col ~ condition * bin_label + event_duration_sec + frequency_hz + (1 | subject_id)
```

**Key coefficient:** `condition[spindle_event] × bin_label[event]`

**Primary endpoints (test each separately):** `m`, `d`, `e`, `d_n`, `d_l`, `d_s`, `e_e`, `e_s`, `e_m`

**Secondary:** regional MNPS from the H5 `regional_mnps/` group if needed.

**Meta-analysis:** random-effects across ANPHY + BOAS after getting per-dataset effect sizes.

**Note on control structure:** `matched_control` rows have `bin_label="control"` (single bin). The contrast is spindle-window geometry across bins vs matched-N2 baseline. The primary test is `spindle_event[event]` vs `matched_control[control]`, adjusting for time-of-night via the matching.

### Pass B — Surface sensitivity

**Input:** Primary AND anchor-augmented parquets for the same subjects.

**Question:** Does the `condition × bin_label[event]` effect from Pass A weaken, strengthen, or hold when `e_m` includes the anchor signal?

If effect weakens substantially → resp/HRV drives geometry; report in sensitivity section.  
If effect holds → moderation is over and above geometry contribution; supports Pass C.

### Pass C — EAP × RVC moderation

**Input:** Primary EEG-only parquets. Use `pre_far` bin as the pre-event anchor window ([-30, -10] s from spindle onset).

**ANPHY model:**
```
geometry ~ condition * ecg_hrv_rmssd_ms_pre_far + event_duration_sec + frequency_hz + (1 | subject_id)
```
where `ecg_hrv_rmssd_ms_pre_far` = the `ecg_hrv_rmssd_ms` value at `bin_label=="pre_far"` for each event, merged onto all bins of that event.

**BOAS model** (restrict to subjects with valid `resp_regular_index`, N ≈ 54):
```
geometry ~ condition * resp_regular_index_pre_far + event_duration_sec + frequency_hz + (1 | subject_id)
```

**Key coefficient:** `condition[spindle_event] × anchor_pre_far`

**Sensitivity for BOAS:** rerun with `anchor_index_v02` as anchor (available in 127/128 subjects) and compare magnitude/direction.

---

## 6. Known limitations to document

1. **BOAS Pass C N reduction**: 66/128 subjects have no respiratory signal. Pass C BOAS effective N ≈ 54. Report in methods.
2. **Matched controls: single bin**: Controls contribute one window each, not a pre/event/post structure. The within-spindle temporal contrast (`event` vs `pre_far`) is computed within spindle_event rows only.
3. **`event_confidence` all NaN**: YASA v0.7 does not export a per-spindle confidence score in the CSV we generated. Use `event_duration_sec` and `frequency_hz` as detector proxy covariates.
4. **`sigma_power` absent**: Not in YASA v1 CSV. Can be added by rerunning `project/scripts/16_yasa_spindle_detection.py` with `sp.summary()` full output — but defer until reviewers request it.
5. **9D falsification warnings (ANPHY)**: The 9D MNPS has `CRITICAL WARNING: Matrix is effectively 3-dimensional` for all ANPHY subjects (and all regional MNPS sub-networks). This is expected — ANPHY is EEG-only so the 9D space is rank-3. Use `coords_9d_finite` filter and interpret 9D cautiously. The 3D MNPS (`m`, `d`, `e`) is the primary geometry.

---

## 7. File locations for scripting

```python
from pathlib import Path
import pandas as pd

BASE = Path("K:/ExternalReceivedDatasets/mndm_rvc_processed")

# Load all primary event-locked parquets for one dataset
def load_event_locked(run_dir: Path) -> pd.DataFrame:
    pqs = sorted(run_dir.rglob("*event_locked*.parquet"))
    return pd.concat([pd.read_parquet(p) for p in pqs], ignore_index=True)

ANPHY_PRIMARY = BASE / "ANPHY/ANPHY/neuralmanifolddynamics_ANPHY_20260702_082429"
BOAS_PRIMARY  = BASE / "ds005555/ds005555/neuralmanifolddynamics_ds005555_20260702_080821"
ANPHY_AUG     = BASE / "ANPHY/ANPHY/neuralmanifolddynamics_ANPHY_20260702_084940"
BOAS_AUG      = BASE / "ds005555/ds005555/neuralmanifolddynamics_ds005555_20260702_084946"

anphy = load_event_locked(ANPHY_PRIMARY)
boas  = load_event_locked(BOAS_PRIMARY)

# Recommended base filter for Pass A
def pass_a_filter(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["coords_9d_finite"] == 1) & (df["n2"] == 1)]
```

---

## 8. NMD repo changes made in this session (for reference only)

Two bugs were fixed in NMD that may be relevant if ingest ever needs to be re-run:

1. **`mndm/src/mndm/pipeline/summary.py`** — `_resolve_event_locked_csv_sources` now accepts a `fallback_search_dirs` parameter. When `stage_events_path` is None (non-BIDS datasets like ANPHY), the pipeline derives the subject's raw data directory from `config.paths.dataset_received_dirs[ds_id]` and searches there with wildcard glob. Without this fix, ANPHY event_locked exports were silently empty.

2. **`core/src/core/config_loader.py`** — `_deep_merge_dict` now supports a `__replace: true` sentinel. When present in an override dict, it replaces (rather than merges into) the base dict. Used in anchor-aug configs to prevent primary `e_m` subcoord keys bleeding through on import.