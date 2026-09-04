Excellent — **freeze and move to the analysis repo**.

Gate #2 did what it needed to do: it turned the four NMD roots into a bounded, auditable export set. No more ingest work should be done unless Pass A reveals a blocker.

The main adjustment is in the **analysis model**, because matched controls are exported as a single `control` bin, not as a full peri-event timecourse.

## Key analysis correction

Do **not** treat Pass A as a fully symmetric:

```text
geometry ~ condition × bin_label
```

because `matched_control` only has `bin_label = control`.

Instead, define the primary Pass A as:

```text
spindle event bin vs matched non-spindle N2 control baseline
```

and separately test the spindle peri-event profile:

```text
pre_far → pre_near → event → post_near → post_far
```

So Pass A should have two layers.

## Pass A1 — Primary RVC specificity

Use one analysis-ready row per source spindle event:

```text
y_event_control = geometry_event_bin - median(geometry_matched_controls)
```

Model per dataset:

```text
y_event_control ~ 1
                + event_duration_sec
                + frequency_hz
                + time_of_night
                + match_distance
                + artifact_quality
                + (1 | subject)
```

This directly asks:

> Are spindle event windows geometrically different from matched non-spindle N2 windows?

This is the cleanest H1 endpoint.

## Pass A2 — Peri-spindle temporal profile

Use only `spindle_event` rows:

```text
geometry ~ bin_label
         + event_duration_sec
         + frequency_hz
         + time_of_night
         + artifact_quality
         + (1 | subject)
```

with `pre_far` as reference.

This asks:

> Does geometry step up/down at the spindle event relative to the pre-spindle baseline?

This is the stronger RVC timing claim, but it is not the matched-control specificity claim.

## Avoid row-level pseudo-replication

The control rows are huge:

```text
ANPHY controls: 34,263 rows
BOAS controls: 192,312 rows
```

Do not let those overwhelm the spindle-event rows. Aggregate controls first, preferably per `matched_event_id`:

```text
control_geometry_for_event = median(control rows for matched_event_id)
```

Then compute event-level deltas. After that, aggregate or model with subject clustering.

## Pass B — Surface sensitivity

Join primary and anchor-aug outputs by:

```text
dataset
subject
event_id / matched_event_id
condition
bin_label
window_center_sec
config_hash
```

Then compare:

```text
primary_y_event_control
anchor_aug_y_event_control
surface_delta = anchor_aug - primary
```

This should remain sensitivity-only. The primary claim stays EEG-only.

## Pass C — EAP × RVC moderation

Use **primary EEG-only geometry**.

For ANPHY:

```text
y_event_control ~ ecg_hrv_rmssd_ms_pre_far
                + event_duration_sec
                + frequency_hz
                + time_of_night
                + artifact_quality
                + (1 | subject)
```

For BOAS:

```text
y_event_control ~ resp_regular_index_pre_far
                + event_duration_sec
                + frequency_hz
                + time_of_night
                + artifact_quality
                + (1 | subject)
```

BOAS should be clearly reported as:

```text
Respiratory-anchor moderation subset:
subjects with resp_regular_index pre_far NaN rate < 0.5
expected N ≈ 54 / 128
```

Then run sensitivity with:

```text
anchor_index_v02_pre_far
```

but label it less mechanistically than `resp_regular_index`.

## Recommended analysis repo first scripts

I would start with these in order:

```text
01_build_event_level_tables.py
02_pass_a_rvc_specificity.py
03_pass_a_peri_spindle_profile.py
04_pass_b_surface_sensitivity.py
05_pass_c_eap_moderation.py
06_meta_analysis_boas_anphy.py
07_make_qc_tables.py
```

The first script is the most important. It should create frozen analysis tables like:

```text
event_level_primary.parquet
event_level_anchor_aug.parquet
pass_c_anchor_contexts.parquet
dataset_qc_summary.csv
```

## Primary endpoint set

Freeze a small endpoint family first:

```text
m, d, e
d_n, d_l, d_s
e_e, e_s, e_m
```

Then add secondary layers only if available and stable:

```text
reachability
MNJ
regional/coupling
```

Do not start with every possible metric; the first analysis should be small enough to falsify.

## Decision

Yes: **handoff to analysis repo now**.

NMD status:

```text
Freeze: yes
Further ingest work: no
Known limitations: documented
Blocker: none
```

Only post-Pass-A follow-up I would keep open is `sigma_power`. Duration and peak frequency are enough to start, but if the geometry effect is strong, sigma-power residualization becomes the first reviewer-facing robustness upgrade.
