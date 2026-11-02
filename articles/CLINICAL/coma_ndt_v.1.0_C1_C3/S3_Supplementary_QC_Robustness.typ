// S3 Supplementary QC and Robustness — coma_ndt_v.1.0 (I-CARE 2.1 CPC1 vs CPC5)

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "S3 QC/Robustness - coma_ndt_v1.0",
  subtitle: "Coverage, ingest fidelity gate, ComBat validation, replication design, and confound audit",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S3.0 Sample and recording coverage

#figure(
  clean-table(
    columns: (1.6fr, 1fr, 1fr),
    align: (left, center, center),
    table.header([*Quantity*], [*Discovery (`20260911_125829`)*], [*Confirmatory (`20260911_123135`)*]),
    [Subjects (all CPC)], [161], [140],
    [CPC1 / CPC2 / CPC3 / CPC4 / CPC5], [71 / 10 / 7 / 3 / 70], [70 / 0 / 0 / 0 / 70],
    [Hospitals A/B/D/E/F (subjects)], [73 / 30 / 23 / 18 / 17], [76 / 18 / 14 / 14 / 18],
    [TTM 33 / 36 / missing (subjects)], [117 / 22 / 22], [100 / 16 / 24],
    [Recordings (H5 files)], [1815], [1838],
    [Empty grouped run dirs], [7], [11],
    [Primary `0_12h` recordings], [1811 / 1815], [1732 / 1838],
    [Primary-window CPC1/CPC5 patients], [71 / 70], [70 / 70],
  ),
  caption: [Coverage overview. Source: `results/part1_corrected/qc_summary.json`,
  `results/part2_confirmatory/qc_summary.json`.]
) <tab-s3-coverage>

Subject-ID overlap between the two bundles is zero. Hospital E in the discovery cohort has a
severe CPC imbalance (2 CPC1 vs 15 CPC5 subjects, unchanged from the predecessor bundle since it
is the same population); see S3.2 for the harmonization applied against this.

= S3.1 Ingest-contract status counts

#figure(
  clean-table(
    columns: (1.8fr, 1fr, 1fr),
    align: (left, center, center),
    table.header([*Status*], [*Discovery*], [*Confirmatory*]),
    [`time_reference_status = ok`], [1815 / 1815 (100%)], [1838 / 1838 (100%)],
    [`diffusion_computation_status = computed`], [1778 / 1815 (98.0%)], [1797 / 1838 (97.8%)],
    [`jacobian_metrics_3d_status = computed`], [22 / 1815 (1.2%)], [53 / 1838 (2.9%)],
    [`jacobian_metrics_3d_status = insufficient_support`], [1793 / 1815 (98.8%)], [1785 / 1838 (97.1%)],
    [`stochastic_reachability_3d_status = unavailable`], [1797 / 1815 (99.0%)], [1798 / 1838 (97.8%)],
    [`geometry_contract_status = adjusted`], [1537 / 1815 (84.7%)], [1838 / 1838 (100%)],
    [`destination` / `resilience`], [`not_testable` (all)], [`not_testable` (all)],
  ),
  caption: [Full status-count table. The 0-12h filename-hour restriction at ingest resolves the
  WFDB HH>=24 clock-parsing failure mode identified in the predecessor bundle for this scope: 0
  runs with `time_reference_status != ok` in either bundle (previously 156/3484). Source:
  `results/part1_corrected/qc_summary.json`, `results/part2_confirmatory/qc_summary.json`.]
) <tab-s3-status>

= S3.2 ComBat harmonization validation (ingest-computed)

`normalization_report.json` validation probes, sampled up to 150 000 rows per bundle,
`target_keys = (group, cpc)`, `batch_key = hospital`:

#figure(
  clean-table(
    columns: (1.6fr, 1fr, 1fr),
    align: (left, center, center),
    table.header([*Probe*], [*Discovery*], [*Confirmatory*]),
    [Batch $eta^2$ median, pre-ComBat], [0.0012], [0.0188],
    [Batch $eta^2$ median, post-ComBat], [0.00014], [0.00012],
    [Batch $eta^2$ p95, pre-ComBat], [0.163], [0.292],
    [Batch $eta^2$ p95, post-ComBat], [0.00047], [0.0086],
    [CPC $eta^2$ median, pre-ComBat], [0.00018], [0.0000672],
    [CPC $eta^2$ median, post-ComBat], [0.00323], [0.000406],
    [Perturbation median abs. pct. shift], [228.4%], [154.5%],
  ),
  caption: [Batch-associated feature variance ($eta^2$) drops sharply post-harmonization on both
  bundles while CPC-associated variance is preserved or increases, consistent with removing
  site structure without washing out outcome signal. Source:
  `data/raw/.../normalization_report.json` for each bundle.]
) <tab-s3-combat>

= S3.3 Replication design (primary robustness check)

Unlike a single-cohort study with post hoc robustness checks, the central robustness claim here
is a pre-planned independent-cohort replication: the discovery and confirmatory bundles are
non-overlapping subject sets, ingested from the same fixed contract, and analyzed with the
identical, unmodified `src/` pipeline (`icare_v2_run_pipeline.py`, no cohort-specific code
paths; only the `--config` target differs). Full results in S2.2.

=== Cross-check: recomputed vs stored $d_"eff"^((a))$

Median absolute difference between the article-local reimplementation and the ingest-stored
`d_diff` series: $4.1 times 10^(-8)$ (discovery, `n_valid_windows_total = 1 439 968`),
$3.6 times 10^(-8)$ (confirmatory, `n_valid_windows_total = 1 458 931`). This validates that
$E_perp$ (computed only article-side, since it requires the drift proxy) is built on the same
diffusion-tensor eigenvalues as the certified $d_"eff"^((a))$ and $tilde(H)_a$.

=== TTM subgroup sensitivity

See S2.4. The dominant 33 degrees C stratum reproduces H1's direction and significance in both
cohorts; the 36 degrees C stratum is under-powered ($<10$ per arm) in both cohorts and is
excluded from interpretation via the `family_testable` gate rather than reported as a null
result.

=== Family-testable gating

`family_testable = "False"` (or borderline `"True"` with $n$ at the 10-per-arm floor) is applied
uniformly to every contrast row, not only to Family B; in this dataset it activates almost
exclusively for Family B (S1.3, S2.3) because the Jacobian fit-fidelity gate removes the large
majority of usable windows before any statistical test is run.

= S3.4 Follow-ups

== S3.4a Jacobian fit-fidelity gate confirmation

Full detail in `handover/ingest_response_confirmation.md`. Summary: all four Priority-1 items
requested from ingest (`fit_fidelity_gate`, `fit_fidelity_threshold`, `operator_semantics`,
`nominal_dt_sec`) are present and verified in `/jacobian/derived_metrics/v1/provenance` on both
bundles (S1.3).

== S3.4b Empty run directories

7 (discovery) and 11 (confirmatory) grouped run directories contain no H5 file and no explicit
error record (`skipped_recordings.json` records `coverage_too_low` reasons for a different,
non-overlapping set of recordings). Not investigated further; excluded from all counts by
construction (`discover_h5_files` globs only existing `.h5` files).

== S3.4c Conventional-feature (qEEG) baseline comparison

Not currently possible: the `conventional_eeg` pack is enabled in both ingest overlays but not
materialized in either export (S1.1). Flagged to ingest for a future features-stage rerun.

== S3.4d `9D` `e_m` fallback

`/support_signature/v1` on sampled files from both bundles shows `coordinates/e_m/source =
fallback` (mapped from `eeg_highfreq_power_30_45`), `semantic_equivalence = "false"`. Not used
by any primary or secondary metric in this article (all metrics here use MNPS-3D, not the 9D
`e_m` axis).

= S3.6 Additional robustness checks (added 2026-09-12)

Following a measurement-quality review of the local-generator gate failure and the H3
non-replication, additional article-local checks were added without changing any
pre-registered primary result:

- *LOSO (S2.7)*: H1/H2 never cross the $alpha=0.05$ significance boundary under any single-patient
  drop in either cohort. H3 with the original drift proxy is LOSO-unstable in the discovery
  cohort (straddles $alpha=0.05$ across drops) and stably non-significant in the confirmatory
  cohort.
- *Run-level mixed-effects cross-check (S2.8)*: fit on 1556 (discovery) / 1692 (confirmatory)
  individual runs rather than the further-collapsed per-patient median, subject random intercept.
  Confirms H1/H2 independently of the median-collapse step; confirms H3's non-significance with
  the original drift proxy.
- *Post-hoc residual hospital $eta^2$ on derived metrics (S2.9)*: 0.11-0.18 on H1-H3 in *both*
  cohorts after ComBat, above a 0.06 flag threshold. Because the confirmatory cohort's hospitals
  are exactly CPC-balanced, this residual effect there is site-level variance orthogonal to
  outcome, not a demonstrated outcome confound - but it does mean ComBat at the raw-feature
  level does not fully remove site structure from the *derived*, nonlinear metrics, and a
  hospital-random-effect model is a natural next robustness step.
- *Family A ingest identity (S2.12)*: paired 1815 (discovery) + 1838 (confirmatory) recordings
  on the 2026-09-12 summarize re-runs versus the 2026-09-11 predecessors used for all primary
  contrasts. Diffusion `computation_status`, $d_"eff"$, $D_"total"$, $|a_"hat"|$,
  `/mnps_3d_dot`, and subject-anchored coordinates are identical ($|Delta| = 0$). Stored
  $A_"bD"$ remains all-NaN (`drift_source = not_supplied`). H1-H4 were therefore not recomputed
  on the later bundles.
- *Qualified-drift $E_perp$ re-derivation (S2.10)*: an article-local Savitzky-Golay
  estimator (window 11, polyorder 2), built after H3 was found weak/non-replicating with the
  stored ingest derivative (`/mnps_3d_dot`: window 7, polyorder 3, plus `derivative_robust`),
  produces a large ($d=+0.68$/$+0.47$), LOSO-stable, cross-cohort-replicating CPC1
  advantage, stable across a 3x range of article-side smoothing bandwidths. This is reported as a *promising
  post-hoc finding requiring prospective confirmation*, not a confirmed result - the estimator
  choice was made after seeing the original result, which is a real, acknowledged
  garden-of-forking-paths risk that a pre-registered replication on a third cohort would resolve.
  A parallel handover (`handover/ingest_jacobian_estimator_quality_handover.md`) requests the
  analogous fix (a pooled neighborhood estimator, matching what diffusion already does) at
  ingest for the local-generator (Family B) fit itself, which is a structurally similar
  under-determined-estimator problem (8 s window / 4 s step $approx$ 1-2 increments per window,
  vs. diffusion's pooled `neighborhood: {k: 20}, min_samples: 30`) compounded by a complete
  absence of EEG-artifact rejection (`qc_ok_eeg = -1`/not_assessed on 100% of sampled windows in
  both bundles).
- *Rank discrimination (S2.13)*: direct AUROC / AUPRC on the same patient-medians. H1/H2
  moderate CPC1-high AUROC replicates (0.74 / 0.67 and 0.74 / 0.64); stored H3 does not.
  Univariate logistic repeated-CV matches the rank AUROC; hospital-LOSO is lower (H2
  confirmatory 0.55), in line with residual hospital $eta^2$. Not a prognostic model.
- *Local-dynamics coverage (S2.14)*: diffusion `a_hat` is populated on 98% of recordings;
  `/mnps_3d_dot` is fully finite but is not a qualified Itô drift (`A_bD` empty);
  3D Jacobian / stored 3D reachability remain gated; FTR is `computed` on 96-99% of files
  *including* those that fail the Jacobian gate (`model_derived`). Destination and
  resilience are contract-empty. 9D Jacobian coverage is higher but is not the article chart.

= S3.7 Reviewer-facing robustness summary

#netn-box(title: [Robustness summary])[
  H1 ($d_"eff"^((a))$) and H2 ($tilde(H)_a$) survive: independent-cohort replication (same
  direction, both BH-significant within the H1-H3 family), LOSO, a run-level mixed-effects
  cross-check, a TTM-33 subgroup check, a recomputed-vs-stored numerical cross-check, and a
  paired ingest-identity audit of the 2026-09-12 re-runs (S2.12). Direct AUROC of the same
  patient-medians is moderate for H1/H2 in both cohorts (S2.13) and is a translation of the
  Mann-Whitney ranking, not a new endpoint. They
  also carry a non-trivial residual hospital effect on the derived metrics (S3.6) that a
  hospital-stratified sensitivity analysis has not yet addressed. H4 (`Tr(a)`, not required to
  differ) does not survive replication as a significant, BH-corrected finding and is reported
  descriptively. H3 ($E_perp$) did not replicate with the stored ingest chart-velocity
  `/mnps_3d_dot`, but a post-hoc, LOSO-stable, window-sweep-stable reanalysis with a different
  Savitzky-Golay implementation (article 11/2 vs ingest 7/3+robust) found a
  large, replicating CPC1 advantage (S3.6) - reported as promising, not confirmed, pending a
  prospective test with the estimator fixed in advance. A paired 2026-09-12 ingest re-run left
  Family A tensors bit-identical (S2.12), so H1/H2/H4 were not recomputed. Family B (local generator,
  `F_reactive`) is not testable on this dataset once an honest fit-fidelity gate is applied -
  this was directly confirmed by requesting and verifying the gate at ingest, not inferred - and
  the small-$n$ numbers that remain after gating (S2.3) should not be read as either a positive
  or a null result. Sedation, other medications, and WLST status remain uncontrolled confounds
  in this export (verified: not present in the exported participant metadata at all).
]

#bibliography("references.bib", style: "apa")
