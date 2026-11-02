# Sleep cohort analysis handover (2026-09-12)

The article-local driver is frozen at `src/sleep_cohort_analysis.py` with
`config/sleep_cohort_analysis_20260912.json`. It consumes an explicit reviewed
H5 list; it does not discover H5 files from the processed directory. The
recovery execution manifest remains the deferred ingest route in
`config/sleep_cohort_analysis_recovery_20260912.json`. The completed full
artifact run below used the coordinator-reviewed direct manifest after the
128-recording/100-PID H5 review.

Set the two repository roots on `PYTHONPATH` before running from either
repository or an unrelated working directory:

```powershell
$env:PYTHONPATH='J:\repos\nmd-analysis\articles\ndt_v3_sleep\src;J:\repos\nmd-analysis\nmd-analysis'
& 'H:\SourceRepo2\NeuralManifoldDynamics\.venv\Scripts\python.exe' -B -m sleep_cohort_analysis `
  --config 'J:\repos\nmd-analysis\articles\ndt_v3_sleep\config\sleep_cohort_analysis_20260912.json' `
  --output 'J:\repos\nmd-analysis\articles\ndt_v3_sleep\results\sleep_cohort_20260912'
```

The command refuses an existing output directory. It requires `status=completed`,
`scope=full`, stable source/config/config-tree provenance and an explicit
producer H5 list (or linked `analysis_input_manifest`) with an H5 SHA-256 for
each existing H5. A null H5 row is retained as a failed expected recording.
The raw participant tables are bound to the SHA-256 values in the config.

The bounded real-data pilot used the producer H5
`J:\repos\nmd-analysis\.w\sleep_dataset_delivery_20260912\processed\ds005555\neuralmanifolddynamics_ds005555_20260912_125921\sub-99_Sleep_acq-psg\sub-99_Sleep_acq-psg.h5`
with SHA-256
`382820fa254ccd41fd4a9987f53df6613713c23eb68e41a2ac42197321050f28`.
Its direct-manifest pilot output is
`J:\repos\nmd-analysis\.w\sleep_cohort_analysis_pilot_20260912_r4\output`.
The pilot completed with one recording and one PID, yielded 9 endpoint
contrasts and 63 stage rows, and retained `temporal_support_status=unknown`
with the producer reason.

The primary cohort summaries are PID-level: recording stage medians are
reduced within PID across nights, then cohort medians/IQRs are computed over
PIDs. The 128-recording tables and per-recording outcomes remain separate.
`sub-1` and `sub-99` current H5s are included and flagged
`prior_development2`; the old 2026-09-10 H5 files and the 2026-09-04 sampled
run are historical and excluded.

The participant-level `prior_development2` flag is derived from all recording
rows for the PID, independently of endpoint or stage validity. Thus a PID
remains flagged when its known prior recording has an unsupported or empty
endpoint row; numeric denominators and medians still use only valid rows.

Validation command from any working directory:

```powershell
$env:PYTHONPATH='J:\repos\nmd-analysis\articles\ndt_v3_sleep\src;J:\repos\nmd-analysis\nmd-analysis'
& 'H:\SourceRepo2\NeuralManifoldDynamics\.venv\Scripts\python.exe' -m pytest -q `
  'J:\repos\nmd-analysis\articles\ndt_v3_sleep\tests\test_sleep_cohort_analysis.py'
```

Result at handover: `7 passed`.

The final bounded pilot used the same fresh sub-99 H5 and explicit direct
manifest after this metadata-only correction. Its output is
`J:\repos\nmd-analysis\.w\sleep_cohort_analysis_pilot_20260912_r4\output`;
`analysis_manifest.json` records runner SHA-256
`9be46a3d448fc1f7628f1c2a76f0e571d16d6acee56ca3d3e087b38fc1921ce1` and
completed status with one recording, PID66, 9 endpoint contrasts, 63 stage
rows, and recorded unknown temporal support.

## Recovery-manifest full run (deferred)

The recovery-specific config
`config/sleep_cohort_analysis_recovery_20260912.json` is byte-for-byte
equivalent in parsed content to the frozen config except for
`source.ingest_execution_manifest_path`, which points to
`H:\\SourceRepo2\\NeuralManifoldDynamics\\project\\v3\\sleep_dataset_delivery_20260912\\recovery_execution_manifest.json`.
Do not run this command until recovery reports all 128 current H5 outcomes,
the recovery manifest is completed and reviewed, and the output directory is
confirmed fresh:

```powershell
$env:PYTHONPATH='J:\\repos\\nmd-analysis\\articles\\ndt_v3_sleep\\src;J:\\repos\\nmd-analysis\\nmd-analysis'
& 'H:\\SourceRepo2\\NeuralManifoldDynamics\\.venv\\Scripts\\python.exe' -B -m sleep_cohort_analysis `
  --config 'J:\\repos\\nmd-analysis\\articles\\ndt_v3_sleep\\config\\sleep_cohort_analysis_recovery_20260912.json' `
  --output 'J:\\repos\\nmd-analysis\\articles\\ndt_v3_sleep\\results\\sleep_cohort_20260912'
```

This recovery-manifest command remains deferred. The completed full artifact
run used the reviewed direct manifest recorded below, which binds the same
current 128-recording H5 set without changing the frozen runner or config.

## Reviewed full-cohort descriptive run

The coordinator-reviewed direct source manifest is
`H:\SourceRepo2\NeuralManifoldDynamics\project\v3\sleep_dataset_delivery_20260912\coordinator_reviewed_analysis_inputs.json`
with SHA-256
`accc59a57da0afcf09985f135333e6b310ab05d3b03138b7acedd10623ba27fb` and
`coordinator_review.status=PASS_FOR_DESCRIPTIVE_ARTIFACT_ANALYSIS`. The frozen
runner and config were executed into the fresh output root with:

```powershell
$env:PYTHONPATH='J:\repos\nmd-analysis\articles\ndt_v3_sleep\src;J:\repos\nmd-analysis\nmd-analysis'
& 'H:\SourceRepo2\NeuralManifoldDynamics\.venv\Scripts\python.exe' -B -m sleep_cohort_analysis `
  --config 'J:\repos\nmd-analysis\articles\ndt_v3_sleep\config\sleep_cohort_analysis_20260912.json' `
  --source-manifest 'H:\SourceRepo2\NeuralManifoldDynamics\project\v3\sleep_dataset_delivery_20260912\coordinator_reviewed_analysis_inputs.json' `
  --output 'J:\repos\nmd-analysis\articles\ndt_v3_sleep\results\sleep_cohort_20260912'
```

The run completed with 128/128 source outcomes `ok`, 100 PID identities,
8064 recording-stage rows, and 1152 recording contrasts. The participant
contrast table has 100 valid PID values for every 3D endpoint and 98 for every
9D endpoint; PIDs 1 and 2 have null 9D contrasts as expected from the reviewed
producer coverage. The cohort contrast output independently matches the
coordinator expected-cohort oracle for all nine endpoints. The analysis
manifest SHA-256 is
`4d1ffcdfe691362c1e22c2dd0d11f48170911af532cd832c18dd20a51e0aa125`.

The resulting descriptive output root is
`J:\repos\nmd-analysis\articles\ndt_v3_sleep\results\sleep_cohort_20260912`.
It retains `claim_status=no_biological_claim`, participant-level medians/IQRs,
and no p-values or pooled-window inference.

## PID-level N2-minus-Wake contrast figure

`src/plot_sleep_cohort.py` reads the participant-level contrast table and its
completed (or completed-with-failures) `analysis_manifest.json`. It requires a
continuous-fullnight source scope of `pilot` or `full`; reviewed full direct
manifests additionally require coordinator descriptive-analysis approval. The
full route also requires the 128-recording/100-PID manifest counts and
per-successful-H5 full-night evidence. It then writes one static nine-panel figure in PNG,
PDF, and SVG. Each panel shows one point per PID with a finite contrast, the
PID median and IQR, a zero line, and the valid-PID `n`; it computes no p-values
or inferential contrasts. A pilot manifest is rendered with an explicit
`Pilot (development only; no cohort inference)` title.

Pilot render verification:

```powershell
$env:PYTHONPATH='J:\repos\nmd-analysis\articles\ndt_v3_sleep\src'
& 'H:\SourceRepo2\NeuralManifoldDynamics\.venv\Scripts\python.exe' -B -m plot_sleep_cohort `
  --input 'J:\repos\nmd-analysis\.w\sleep_cohort_analysis_pilot_20260912_r4\output\participant_n2_minus_wake.json' `
  --output-dir 'J:\repos\nmd-analysis\.w\sleep_cohort_plot_pilot_20260912_r3'
```

The verified pilot figure is under
`J:\repos\nmd-analysis\.w\sleep_cohort_plot_pilot_20260912_r3` and has one
valid PID in each of the nine panels. It is pilot evidence only and must not
be copied into the full-cohort results directory.

The figure canvas is 7 x 7.5 inches for the approximately 17 cm article
column width. Panel titles and axis labels use 8 pt type, the footer uses 7 pt
type, and each panel is limited to four major y ticks so the nine panels remain
readable at final physical size.

The completed full figure was rendered with:

```powershell
$env:PYTHONPATH='J:\repos\nmd-analysis\articles\ndt_v3_sleep\src'
& 'H:\SourceRepo2\NeuralManifoldDynamics\.venv\Scripts\python.exe' -B -m plot_sleep_cohort `
  --input 'J:\repos\nmd-analysis\articles\ndt_v3_sleep\results\sleep_cohort_20260912\participant_n2_minus_wake.json' `
  --output-dir 'J:\repos\nmd-analysis\articles\ndt_v3_sleep\results\sleep_cohort_20260912\figures'
```

It has 100 valid PID points in each 3D panel and 98 in each 9D panel. The
static figure hashes are PNG
`c75e88d97980c0ef012b4fac5f5570c4b71e779fc41acab576ee2e8891d178b2`, PDF
`ddfb2b04d839235bd0785d479d46d6ce0d164b5dbe28b784ebfb365d06559260`, and SVG
`70e30b15ef1c9f41cb8e0e063ea32a3710cdfd4cfb367b7caa5b4ee54e65fd5c`.
The plotting source SHA-256 is
`79fbbb691d18cc0d6d3ccd500fea979228b3180a25f72d613ee529684971bd1d`.

The bounded final sub-99 versus fresh pilot identity receipt is
`J:\repos\nmd-analysis\.w\sub99_final_vs_pilot_readonly_receipt_20260912.json`
(SHA-256 `4569d31e8533d3ad85f7a29cf239adfc79d0b6905caf14c306204d442153ffc0`).
It preserves the strict bit-identity failure while recording equal time/grid,
labels, masks, centers, source aliases, and exact shared feature values; final
geometry/Jacobian/diffusion values and the nine pilot contrasts differ only
numerically.
