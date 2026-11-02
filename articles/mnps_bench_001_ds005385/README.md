# MNPS-BENCH-001: ds005385

This is the downstream H1 analysis for the frozen 100-person ds005385 subset.
It reads only the processed HDF5 outputs under the selected H1 run directory.
It does not open EDFs, `participants.tsv`, or `events.tsv`.

## Frozen analysis contract

The analysis follows the NMD repository's frozen protocol and amendment 1:

- H1 v3.1 has 16 columns: seven scalar streams and the nine ordered AR/M3
  adjacent-block-pair components. AR is aggregated component-wise across
  supported windows; components are never collapsed into a new scalar.
- The v2 comparator is the exported default `coords_9d` surface. The parser
  uses `qc/windows/coords_9d_valid` and finite values for support.
- All participant/state features are medians of supported windows. Time support
  is the union of `[start, end)` intervals, with overlapping windows counted
  once and a 60-second minimum per feature.
- Conventional tier-1 relative power is already exported as a per-recording
  median and finite-window count. Its `column` entries are text metadata, not
  feature values. Because the exact finite-window positions are not retained,
  the support audit uses the minimum possible interval union for the saved
  finite count; it passes only when that conservative lower bound reaches 60
  seconds.
- The primary H1 cohort requires all features in both arms and both states.
  It has a frozen minimum of 80 complete participants; no imputation is used.
- CV uses participant-grouped 5-fold outer splits repeated 20 times and 4-fold
  grouped inner tuning over the frozen C grid. The same folds are used for the
  two primary arms. The primary interval is a 2,000-draw participant bootstrap
  conditional on the fitted repeated-CV models.
- The secondary feature family contains exactly 16 v3.1 component contrasts,
  using the frozen bootstrap and sign-flip randomization procedures with one
  Holm adjustment.
- Descriptive effective rank is the Shannon effective number of dimensions
  from the normalized positive PCA eigenvalues after feature-wise
  standardization across participants in the relevant scope.

## Run sequence

1. Wait for the full H1 summary run to finish and confirm that its directory
   contains exactly 200 HDF5 recordings from the frozen subset.
2. Freeze the selection manifest, original protocol, accepted amendment, H1
   config, analysis code/tests, software versions, and all input HDF5 hashes:

   ```powershell
   .\.venv\Scripts\python.exe articles\mnps_bench_001_ds005385\analyze_h1.py freeze `
     --h1-run-dir K:\ExternalReceivedDatasets\mnps_bench_001_ds005385\processed\ds005385\<H1_RUN> `
     --selection-manifest H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\selection_manifest_outcome_blind.json `
     --execution-manifest H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\h1_execution_manifest.json `
     --protocol H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\mnps_bench_001_protocol_frozen_v1_20261007.md `
     --amendment H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\mnps_bench_001_amendment_1_m3_vector_20261007.md `
     --h1-config H:\SourceRepo2\NeuralManifoldDynamics\mndm\config\sources\openneuro\config_ingest_mnps_bench_001_ds005385.yaml `
     --out H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\h1_analysis_freeze_v3.json
   ```

3. Run the analysis with that exact freeze manifest:

   ```powershell
   .\.venv\Scripts\python.exe articles\mnps_bench_001_ds005385\analyze_h1.py analyze `
     --h1-run-dir K:\ExternalReceivedDatasets\mnps_bench_001_ds005385\processed\ds005385\<H1_RUN> `
     --selection-manifest H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\selection_manifest_outcome_blind.json `
     --execution-manifest H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\h1_execution_manifest.json `
     --freeze-manifest H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.1\bench_001\h1_analysis_freeze_v3.json `
     --out-dir K:\ExternalReceivedDatasets\mnps_bench_001_ds005385\analysis\h1
   ```

The freeze command hashes the processed HDF5 files byte-for-byte, but does not
open or interpret their content. The analysis command verifies every frozen
hash before parsing any recording, and verifies the files again after analysis.
Outputs include feature support, coverage, paired out-of-fold predictions,
primary estimates, feature-level contrasts, correlations, PCA spectra, and a
run manifest.

## Validation

`test_analyze_h1.py` builds synthetic HDF5 fixtures to verify separate legacy
and v3 time grids, component-wise AR preservation, participant-grouped splits,
paired-AUC ties, Holm adjustment, and nested-CV output shape. These tests do not
read the ds005385 dataset.

## H2: fast core plus MNJ

H2 is a separate secondary contrast: the same four 4-second fast-core features
(PCV, TP, OI, SC) versus those four features plus four summaries from the local
4D Jacobian. It consumes the saved fast-core windows in the H2 processed HDF5
files and imports the frozen NMD derivative, kNN, and Jacobian kernels. It does
not reopen EDF files or recompute EEG features.

Each Jacobian summary is the median over finite centers meeting the frozen
support contract: at least 30 finite centers, at least 50% of attempted
centers, and at least 60 seconds of unique center-window support. The four
summaries are the Jacobian Frobenius norm, antisymmetric Frobenius norm,
symmetric Frobenius norm, and largest-to-smallest singular-value ratio. The
anisotropy is missing when the smallest singular value is at or below 1e-10
and is capped at 1e6. The report preserves attempted, finite, and
underdetermined-center counts; unsupported values remain missing.

The H2 analysis uses the same participant-grouped repeated nested-CV schedule,
paired bootstrap, and 80-participant minimum as H1. It estimates the incremental
paired AUC difference for fast-core-plus-MNJ versus fast-core, without an
arbitrary success threshold. MNJ support failure does not invalidate the fast
core arm. The analysis freeze includes hashes for all selected H2 HDF5 inputs,
the extraction manifest, H2 config/index, analysis code/tests, protocol, and
upstream estimator kernels.

`test_analyze_h2.py` checks known-matrix summaries, finite scalar parsing,
segmentation at gaps/jumps, and supported versus insufficient synthetic
trajectories using the NMD kernels. These tests do not read ds005385.

## H2 result

The frozen H2 run completed for all 200 recordings from the selected 100
participants. The output set exactly matched the selected input stems; the
run manifest reports 200 HDF5, summary, QC-summary, and reliability-QC files,
zero run errors, and zero skipped recordings. All 200 recordings reported 64
EEG channels and average reference.

All four MNJ summaries passed their support requirements in all 100
participants in both states. Median support was 172 seconds with 43/43 finite
centers per recording. The minimum support was 148 seconds for EyesClosed and
152 seconds for EyesOpen; median underdetermined-center count was zero.

The paired participant AUC was 0.92 for the 4-second fast core and 0.93 after
adding MNJ. The prespecified increment was **+0.01 AUC** with a 95% participant
bootstrap interval of **[-0.02, +0.05]** (2,000 draws; conditional on the
fitted repeated-CV models; 100 participants). This small estimate and interval
do not show a clear incremental state-classification benefit from MNJ in this
benchmark. This is not a global rejection of MNJ: the benchmark is limited to
this dataset, and EyesClosed was always recorded before EyesOpen, confounding
state with recording order/time.

The ingest log repeatedly warned that the additional legacy 3D output fell
back from `from_v2` to `direct_features` because 9D coordinates were
unavailable. That output is not consumed by H2; the four H2 features are read
from saved v3.1 windows, and the run completed with zero errors. The exact
warning count was not persisted.

Outputs are under
`K:\ExternalReceivedDatasets\mnps_bench_001_ds005385\analysis\h2`; the H2
execution and analysis freeze manifests are in the NMD `project/bench_001`
directory.

## H2R result

H2R applies the same frozen H2 contract to the disjoint, outcome-blind
second 100-person subset. The participant-paired ΔAUC for fast-core-plus-MNJ
minus fast core was **−0.02** (conditional participant-bootstrap 95% interval
**[−0.08, +0.03]**; 2,000 draws; 100 participants). The result is consistent
with little observed incremental recording-state classification gain in this
benchmark, but it does not establish equivalence. H2R is a post-H1R,
same-dataset secondary replication, not a prospective confirmatory success
test. See [`h2r_results.md`](h2r_results.md) for support, exposure, and
reproducibility details.
