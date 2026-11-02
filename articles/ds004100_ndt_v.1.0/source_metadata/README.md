# September source-sidecar audit

The September provenance source **is accessible** at `K:\ExternalReceivedDatasets\openneuro\ds004100`. It differs from the unavailable M: source named by the August export. No EDF waveform was opened.

Run from the analysis repository:

```powershell
.\.venv\Scripts\python.exe articles\ds004100_ndt_v.1.0\source_metadata\audit_source_metadata.py
```

The [script](audit_source_metadata.py) links source sidecars to all 319 H5 identities by subject/session/task/acquisition/run and saves [the complete audit and sidecar SHA-256 hashes](source_metadata_audit.json).

- Local `dataset_description.json` identifies `doi:10.18112/openneuro.ds004100.v1.1.3`.
- All 319 linked iEEG JSON files and 319 channel TSV files exist.
- All 208 ictal source files have events with parseable `sz onset` / `sz offset` pairs; none of the 111 interictal sources has a corresponding events TSV. The absence of an interictal events file is not proof of spike-free or seizure-free activity.
- The raw channel name/type/status signature is stable within each of 57 subject/session/acquisition groups. This does not establish identical channels after processing or reference equivalence; every iEEG JSON reports `iEEGReference=n/a`.
- Only 38 of 208 ictal recordings, from 18 participants, contain at least 30 exported **nominal** windows fully between source onset and offset. Counts range from 0 to 280. These are metadata counts, not endpoint means or effect estimates.
- All 319 source task labels agree with the H5 task. For 164 files the final nominal window end exceeds the JSON recording duration by 0.0009765625–0.00390625 seconds; every excess is at most one original sampling interval. The audit records both the strict comparison and the one-sample tolerance, consistent with a possible endpoint convention difference. This does not certify the raw clock mapping.

Example: HUP060 ictal run 01 has onset 120 seconds and offset 317.998 seconds in a 377.998-second source file. Its filename labels the recording, which includes substantial pre/post-seizure activity.

Nominal overlap uses H5 `window_start/window_end` against source event seconds. It does not certify the original-sample mapping, effective filter support or the scope of neighbors/operator fitting. Therefore it cannot certify seizure-pure exported family values. The current protocol's primary whole-recording label contrast remains explicit; an event-restricted re-estimation requires its own frozen measurement/support plan.
