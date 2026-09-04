## Handover

### What was implemented
A generic, reusable interval-membership and stage-blocking layer was added so block-based event labeling is no longer `ds006036`-specific.

Main code changes:
- Added shared interval geometry in `mndm/src/mndm/pipeline/intervals.py`
- Added shared block inference + config normalization in `mndm/src/mndm/pipeline/stage_blocking.py`
- Refactored both consumers to use the shared core:
  - `mndm/src/mndm/features/epoch_selection.py`
  - `mndm/src/mndm/pipeline/summary_events.py`
- Refactored `mndm/src/mndm/pipeline/event_alignment.py` to reuse the shared overlap helpers

What this means functionally:
- block inference is now separated from window-membership geometry
- membership modes are now generic:
  - `midpoint_in_interval` (default / old behavior)
  - `fully_contained`
  - `overlap_frac_ge`
- legacy config aliases still work:
  - `photic_regex`
  - `hv_mark_labels`
  - `use_hv_marks`
  - `hv_tail_sec`
  - `hv_tail_cap_sec`
  - `preserve_photic_blocks`
  - `expected_frequencies_hz`

Important semantic fix:
- carrier/block-start rows no longer “leak” labels back onto boundary windows through point-event fallback when a stricter membership mode is active

### ds006036 practical test
I then enabled strict block membership for `ds006036` in:
- `mndm/config/config_ingest_ds006036.yaml`

New active policy:
- `stage_blocking.window_membership.mode: "fully_contained"`
- canonical tail keys now used:
  - `bridge_tail_sec`
  - `bridge_tail_cap_sec`

Fresh rerun:
- output root:
  - `E:/Science_Datasets/openneuro/processed_ds006036_strict_fully_contained_v1`
- subject-anchor run:
  - `E:/Science_Datasets/openneuro/processed_ds006036_strict_fully_contained_v1/ds006036/neuralmanifolddynamics_ds006036_20260603_114851`

Status:
- run completed successfully
- `labels_stage: true`
- `h5_with_stage: 88`

Comparison vs previous subject-anchor baseline:
- baseline run:
  - `E:/Science_Datasets/openneuro/processed_ds006036_subject_then_cohort_anchor_v2/ds006036/neuralmanifolddynamics_ds006036_20260528_093207`
- mean `stage_frac_labeled`
  - old: `0.584536`
  - new: `0.533997`
  - delta: about `-8.65%`
- total labeled windows
  - old: `3422`
  - new: `3178`
- photic-labeled windows only
  - old: `1856`
  - new: `979`
  - delta: about `-47.25%`

Interpretation:
- the stricter rule worked as intended
- photic windows became much cleaner / more selective
- overall stage coverage dropped moderately, but not catastrophically
- raw frequency detection stayed intact

### Where the new H5 nodes are
The key additions/clarifications are in the H5 event-provenance area.

#### Core stage label surface
Still here:
- `/labels/stage`

This remains the main per-window stage surface used by downstream analyses.

#### New / expanded event provenance nodes
Under:
- `/events/*`

Relevant columnar nodes:
- `/events/onset_sec`
- `/events/duration_sec`
- `/events/raw_event_label`
- `/events/normalized_event_label`
- `/events/mapped_stage_code`
- `/events/mapping_mode`
- `/events/mapping_rule`
- `/events/source_event_column`
- `/events/inferred_block_id`
- `/events/window_assignment_count`

Stage-block helper nodes:
- `/events/is_stage_block_event`
- `/events/stage_block_frequency_hz`

Backward-compatible aliases may also still be present:
- `/events/is_photic`
- `/events/photic_frequency_hz`

What they mean:
- `mapped_stage_code`: numeric stage code after stage-map/codebook resolution
- `mapping_mode`: whether the row was direct, inferred via block support, etc.
- `inferred_block_id`: block identity for inferred block rows
- `window_assignment_count`: how many MNPS windows that event/block actually labeled
- `is_stage_block_event`: whether the raw event matched the configured block-start regex
- `stage_block_frequency_hz`: numeric parameter captured from the regex, e.g. photic frequency

#### Related explicit codebook nodes
Also relevant for interpretation:
- `/codebooks/stage/*`

These make the stage integers self-describing.

#### Event-window join table
Also available when exported:
- `/event_windows/*`

This is the row-per-event/window alignment surface for exact event-locked joins, separate from the main `/labels/stage` block labeling.

### Documentation updated
Updated docs:
- `README.md`
- `mndm/README.md`
- `mndm/Output_variables_guide.md`

They now describe:
- the generic interval-membership model
- canonical `bridge_*` config names
- legacy alias support
- the difference between:
  - `mnps.overlap` = window stride overlap
  - `stage_blocking.window_membership.min_overlap_fraction` = interval geometry overlap

### Session notes / diary
Session notes were written to:
- `project/diary/085_20260603_generic_interval_membership_core.md`
- `project/diary/086_20260603_ds006036_fully_contained_test.md`

### Tests run
Validated unit tests:
- `mndm/tests/test_event_alignment.py`
- `mndm/tests/test_epoch_selection_point_events.py`

Result:
- `19 passed`

If you want, I can next turn this into a shorter “operator handover” version, or a copy-pasteable research log entry for your notes.