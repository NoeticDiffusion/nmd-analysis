param(
  [string]$PilotRoot = 'J:\repos\nmd-analysis\articles\ds004148_mnps_v3_2_reliability\results\SL020_MNPS32_RETEST\run_20261019_v1\PILOT12',
  [string]$CohortRoot = 'J:\repos\nmd-analysis\articles\ds004148_mnps_v3_2_reliability\results\SL020_MNPS32_RETEST\run_20261019_v1\COHORT',
  [string]$DatasetRoot = 'K:\ExternalReceivedDatasets\openneuro\received\ds004148',
  [string]$R1Root = 'J:\repos\nmd-analysis\articles\ds004148_mnps_v3_2_reliability\results\SL020_MNPS32_RETEST\run_20261019_v1\R1_COMPLETE',
  [string]$Runner = 'H:\SourceRepo2\NeuralManifoldDynamics\mndm\src\mndm\mnps\v3_2\experiments\sl020_ds004148.py',
  [string]$AnalysisScript = 'J:\repos\nmd-analysis\articles\ds004148_mnps_v3_2_reliability\code\sl020_analysis.py',
  [string]$AnalysisRoot = 'J:\repos\nmd-analysis\articles\ds004148_mnps_v3_2_reliability\results\SL020_MNPS32_RETEST\run_20261019_v1\R3_ANALYSIS',
  [string]$Protocol = 'H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.2\protocols\SL-020-MNPS32-RETEST-001.md',
  [string]$Amendment001 = 'H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.2\protocols\SL-020-PROTOCOL-AMENDMENT-001.md',
  [string]$Amendment002 = 'H:\SourceRepo2\NeuralManifoldDynamics\project\new_mnps_v.3.2\protocols\SL-020-PROTOCOL-AMENDMENT-002.md',
  [switch]$ResumeExistingCohort
)
$ErrorActionPreference = 'Stop'
$families = @('PCV','TP','AR','NIE','RD','OI','SC','ED')
$expectedPilot = @('sub-16','sub-21','sub-23','sub-55','sub-42','sub-19','sub-39','sub-58','sub-13','sub-07','sub-32','sub-29')
$baselines = @(
  'log10_median_channel_rms_uV','relative_delta_1_4hz','relative_theta_4_8hz',
  'relative_alpha_8_13hz','relative_beta_13_30hz','relative_gamma_30_45hz',
  'normalized_spectral_entropy_1_45hz','median_channel_autocorrelation_lag_1s',
  'mean_absolute_zero_lag_channel_correlation'
)
$expectedRows = 12 * 15 * (75 + 15)
$gatePath = Join-Path (Split-Path -Parent $PilotRoot) 'PILOT_GATE.json'
$manifestPath = Join-Path $PilotRoot 'run_manifest.json'
$reportPath = Join-Path $PilotRoot 'engineering_support_report.json'
$waitStarted = [DateTime]::UtcNow

Write-Output 'SL020 gate: waiting up to 12 hours for the engineering pilot support report.'
while (-not (Test-Path -LiteralPath $reportPath)) {
  if (([DateTime]::UtcNow - $waitStarted).TotalHours -ge 12) {
    $timeoutDecision = [ordered]@{
      phase = 'SL-020 pilot gate'; pilot_root = $PilotRoot
      checked_utc = [DateTime]::UtcNow.ToString('o'); outcome_values_inspected = $false
      status = 'FAIL'; failures = @('pilot_support_report_timeout_12h'); qualified = $false
    }
    $timeoutDecision | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $gatePath -Encoding utf8
    throw 'Pilot gate timed out after 12 hours without a final support report.'
  }
  if (Test-Path -LiteralPath $manifestPath) {
    try { $liveManifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json }
    catch { $liveManifest = $null }
    if ($null -ne $liveManifest -and $liveManifest.status -eq 'failed') {
      $failedDecision = [ordered]@{
        phase = 'SL-020 pilot gate'; pilot_root = $PilotRoot
        checked_utc = [DateTime]::UtcNow.ToString('o'); outcome_values_inspected = $false
        status = 'FAIL'; failures = @('pilot_runner_manifest_failed'); qualified = $false
      }
      $failedDecision | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $gatePath -Encoding utf8
      throw 'Pilot runner manifest reports failure before the final support report was written.'
    }
  }
  Start-Sleep -Seconds 30
}

$report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$counts = $report.support_counts
$failures = [System.Collections.Generic.List[string]]::new()
$computedRows = [ordered]@{}
if ($report.status -ne 'complete') { $failures.Add('pilot_status_not_complete') }
if ($report.selected_participant_count -ne 12 -or $report.completed_participant_count -ne 12) { $failures.Add('pilot_participant_count_mismatch') }
if (($manifest.frozen_identity.selected_participants -join ',') -ne ($expectedPilot -join ',')) { $failures.Add('pilot_roster_mismatch') }
if ($report.selected_recording_count -ne 180) { $failures.Add('pilot_recording_count_mismatch') }
if ($report.feature_values_inspected_by_gate -ne $false -or $manifest.feature_values_printed_to_stdout -ne $false) { $failures.Add('pilot_value_blind_gate_flag_mismatch') }
foreach ($family in $families) {
  $requestedKey = "family:$family`:requested"
  $requested = [int]$counts.$requestedKey
  $statusTotal = 0
  foreach ($property in $counts.PSObject.Properties) {
    if ($property.Name -like "family:$family`:status:*") { $statusTotal += [int]$property.Value }
  }
  $computedCount = 0
  foreach ($property in $counts.PSObject.Properties) {
    if ($property.Name -like "family:$family`:status:computed*") { $computedCount += [int]$property.Value }
  }
  $computedRows["family:$family"] = $computedCount
  if ($requested -ne $expectedRows -or $statusTotal -ne $expectedRows) {
    $failures.Add("family_status_coverage:$family`:$requested`:$statusTotal")
  }
  if ($computedCount -lt 1) { $failures.Add("family_no_computed_pilot_rows:$family") }
}
foreach ($baseline in $baselines) {
  $statusTotal = 0
  foreach ($property in $counts.PSObject.Properties) {
    if ($property.Name -like "baseline:$baseline`:status:*") { $statusTotal += [int]$property.Value }
  }
  $computedCount = 0
  foreach ($property in $counts.PSObject.Properties) {
    if ($property.Name -like "baseline:$baseline`:status:computed*") { $computedCount += [int]$property.Value }
  }
  $computedRows["baseline:$baseline"] = $computedCount
  if ($statusTotal -ne $expectedRows) { $failures.Add("baseline_status_coverage:$baseline`:$statusTotal") }
  if ($computedCount -lt 1) { $failures.Add("baseline_no_computed_pilot_rows:$baseline") }
}
if ($report.free_bytes_after_run -lt 10GB) { $failures.Add('pilot_disk_guard_below_10_gib') }

$decision = [ordered]@{
  phase = 'SL-020 pilot gate'
  pilot_root = $PilotRoot
  checked_utc = [DateTime]::UtcNow.ToString('o')
  outcome_values_inspected = $false
  expected_rows_per_family_and_baseline = $expectedRows
  computed_rows_by_feature = $computedRows
  status = if ($failures.Count -eq 0) { 'PASS' } else { 'FAIL' }
  failures = @($failures)
  disk_free_bytes_after_pilot = $report.free_bytes_after_run
  qualified = $false
}
$decision | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $gatePath -Encoding utf8
Write-Output ("SL020 gate: {0}; family and baseline status coverage inspected only." -f $decision.status)
if ($failures.Count -gt 0) {
  throw ('Pilot gate failed: ' + ($failures -join ', '))
}
$runCohort = $true
if (Test-Path -LiteralPath $CohortRoot) {
  $existing = Get-ChildItem -LiteralPath $CohortRoot -Force
  if (@($existing).Count -gt 0) {
    if (-not $ResumeExistingCohort) { throw 'Refusing to overwrite a nonempty cohort root without -ResumeExistingCohort.' }
    $cohortManifestPath = Join-Path $CohortRoot 'run_manifest.json'
    if (-not (Test-Path -LiteralPath $cohortManifestPath)) { throw 'Cannot resume a nonempty cohort root without its run manifest.' }
    $existingCohort = Get-Content -LiteralPath $cohortManifestPath -Raw | ConvertFrom-Json
    if ($existingCohort.frozen_identity.mode -ne 'cohort' -or $existingCohort.status -notin @('running','complete')) {
      throw 'Existing cohort manifest is not a resumable cohort run.'
    }
    if ($existingCohort.status -eq 'complete') { $runCohort = $false }
    Write-Output ("SL020 cohort: preserving existing root; runner will verify identity and completed shards before resume (status={0})." -f $existingCohort.status)
  }
}
$analysisParent = Split-Path -Parent $AnalysisRoot
if (Test-Path -LiteralPath $AnalysisRoot) {
  $existingAnalysis = Get-ChildItem -LiteralPath $AnalysisRoot -Force
  if (@($existingAnalysis).Count -gt 0) { throw 'Refusing to overwrite a nonempty R3 analysis root.' }
}
$logSuffix = if ($ResumeExistingCohort) { '_RESUME_' + (Get-Date -Format 'yyyyMMdd_HHmmss') } else { '' }
$logPath = Join-Path (Split-Path -Parent $CohortRoot) ("COHORT_RUN{0}.log" -f $logSuffix)
Write-Output 'SL020 gate: PASS; starting the full 60-participant cohort on J:.'
if ($runCohort) {
  python $Runner --mode cohort --dataset-root $DatasetRoot --r1-root $R1Root --output-root $CohortRoot 2>&1 |
    Tee-Object -FilePath $logPath
  if ($LASTEXITCODE -ne 0) { throw "Cohort runner failed with exit code $LASTEXITCODE; see $logPath" }
} else {
  Write-Output 'SL020 cohort already complete; continuing to the frozen R3 analysis.'
}
$analysisLog = Join-Path $analysisParent 'R3_ANALYSIS.log'
Write-Output 'SL020 cohort complete; starting the frozen R3 analysis.'
python $AnalysisScript --cohort-root $CohortRoot --protocol $Protocol --amendment-001 $Amendment001 `
  --amendment-002 $Amendment002 --output-root $AnalysisRoot 2>&1 |
  Tee-Object -FilePath $analysisLog
if ($LASTEXITCODE -ne 0) { throw "R3 analysis failed with exit code $LASTEXITCODE; see $analysisLog" }
Write-Output ("SL020 R3 analysis complete; artifacts: {0}" -f $AnalysisRoot)
