// S3 Supplementary QC and Robustness — RichSleep_EAP_v2

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "S3 QC/Robustness - RichSleep_EAP_v2",
  subtitle: "Data-delivery validation, sample coverage, the R3 histogram corroboration check, and a reviewer-facing robustness summary",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S3.0 Data-delivery validation (`01_validate_v3_delivery.py`)

Every check below passed (script exits 0; no `[FAIL]` lines in its console output):

- *`phase_resolved_v3`*: 24/24 subject files present; row counts match `run_meta_v3.json` for every subject; total 23,029 events. Bit-identity check against the companion articles' `event_phase_v2` on all 13 shared columns: identical (`subject`, `onset_sec`) key set and row order after sorting, and `np.allclose`/exact-string equality on every shared column - zero mismatched columns.
- *`slow_oscillation_v1`*: 24/24 files; covers both N2 (stage 2) and N3 (stage 3); all `so_qc_flag == "ok"`; 68,386 total (26,377 N2 + 42,009 N3).
- *`phase_continuous_v1`*: 24/24 files; sampling interval exactly 0.1 s (10 Hz) for all subjects; cardiac and respiratory phase-valid rate $>0.99$ for all subjects; 8,834,120 total rows, mean 10.22 h/subject.
- *`event_phase_n3_so_v1`*: 24/24 files; total events (42,009) exactly matches `slow_oscillation_v1`'s N3 count; cardiac/respiratory phase-valid rate $>0.99$ at both trough and upstate; `phase_coupling_qc_flag_trough` all `"ok"`.
- *`event_phase_rem_theta_v1`*: 24/24 files; total 2,412 epochs; `theta_phase_valid`/`cardiac_phase_valid`/`resp_phase_valid`/`autonomic_phase_eligible` all $=1$ for every row; 1 subject has $<5$ epochs (excluded from the per-subject-only arm, `S1.2`).
- *`non_event_risk_v1`*: 24/24 files; all rows `stage == 2` (N2) and `selection_status == "selected"`; cardiac and respiratory phase valid for all rows; 66,827 total, mean per-subject risk:spindle ratio consistent with the delivery's own $approx 2.9$ design target.
- *Cross-check*: all 190 companion-article geometry-valid events found in the v3 catalog by exact (subject, onset_sec) join; 25 SO-coupled across 15 subjects - confirms the plan's stated $N=25$/15-subject power caveat exactly.

= S3.1 Sample and coverage summary

#figure(
  clean-table(
    columns: (1.5fr, 0.8fr, 1.1fr, 1.6fr),
    align: (left, center, center, left),
    inset: 4.5pt,
    table.header([*Sample*], [*$N$ subj.*], [*$N$ events*], [*Role*]),
    [`phase_resolved_v3` full catalog], [24], [23,029], [N2-spindle onset/peak phase-locking (R2), Test A/B cases (R3)],
    [`event_phase_n3_so_v1`], [24], [42,009], [N3-SO trough/upstate phase-locking (R2)],
    [`event_phase_rem_theta_v1`], [24 (23 for 2nd-order)], [2,412], [REM-theta phase-locking (R2)],
    [`non_event_risk_v1`], [24], [66,827], [Test A controls (R3)],
    [`phase_continuous_v1`], [24], [8,834,120 rows], [Test B surrogate source (R3)],
    [Geometry-valid, N2-staged subsample (companion articles' population)], [24], [190], [qe-interaction primary/robustness family (R4)],
    [SO-coupled subset of the above], [15], [25 (21/19 after per-mode attrition)], [SO-coupled descriptive check (R5)],
  ),
  caption: [Sample definitions and roles across R2-R5. Sources: `01_validate_v3_delivery.py` output tables and `02_build_merged_table.py`/`05_qe_interaction_moderation.py`.]
) <tab-sample-coverage>

The SO-coupled subset (25/190 $=$ 13.2% of the geometry-valid sample) is far smaller than the primary qe-interaction family's 172/160 - this asymmetry is the reason R4 (well-powered, primary claim) and R5 (underpowered, descriptive-only) are reported with different evidentiary weight despite testing conceptually related questions.

= S3.2 R3 histogram corroboration check (companion to the cross-null disagreement)

The main text (R3) and `04_spindle_onset_hazard_model.py`'s console commentary reference an "ad hoc 12-bin case-vs-control histogram comparison" used to judge which of Test A's (case-control) and Test B's (time-shift) disagreeing per-channel findings is more likely a genuine effect rather than a false positive of that specific null construction. This check is implemented in `06_make_figures.py`'s `fig3_hazard_curve` panel (Fig. `fig-hazard` in the main text): empirical case:control density ratio in 12 phase bins, overlaid with Test A's fitted $exp(b_"cos" cos phi + b_"sin" sin phi)$ curve, one panel per channel.

#netn-box(title: [Reading Fig. 3])[
  *Cardiac panel*: the 12-bin empirical ratio scatters around 1.0 with no coherent monotonic trend matching the fitted curve's shape - visually consistent with Test A's own null result ($p=0.379$) and with treating Test B's $p=0.004$ hit as more likely a false positive of that specific surrogate construction than a real effect. *Respiratory panel*: the empirical ratio shows a small but visually coherent, monotonic excess/deficit pattern tracking the fitted first-harmonic curve - consistent with Test A's highly significant ($p=3.96 times 10^(-7)$) but small effect, and with Null 0's directionally-consistent (though non-significant) raw $p=0.0265$. This visual check is descriptive, not a separate formal statistical test; it is used only to adjudicate which of two already-computed, disagreeing $p$-values is more consistent with a visible shape in the data, not to generate a new $p$-value of its own.
]

= S3.3 R4/R5 robustness detail

The primary qe-interaction family (`S1.5`, `S2.4`) was repeated with three operationalizations of intrinsic spindle strength (log1p sigma-power z-score, log1p amplitude, untransformed sigma-power z-score); none produced any BH-FDR-significant interaction term (minimum FDR $q$: 0.834, 0.988, 0.725 respectively, across the three families). No single (delta_mode, endpoint) pair approaches significance under more than one operationalization simultaneously - there is no cross-transform-convergent candidate interaction being missed by the correction, only three independently null families.

The main-effect (non-interaction) `resp_peak_alignment` coefficients in this interaction model are nominally in the same direction as the companion article's own main-effect finding for the two endpoints it flagged as fragile BH-FDR survivors (`d`: this model's $p=0.023$ vs. companion's $q=0.021$; `d_l`: $p=0.0030$ vs. companion's $q=0.005$, both `event_prefar` mode) - but this model's main-effect $p$-value is not itself BH-FDR corrected within this family (the *interaction* term is the pre-specified quantity of interest here), so this consistency is reported as a qualitative cross-check, not as independent statistical confirmation of the companion article's finding.

= S3.4 Reviewer-facing robustness summary

#netn-box(title: [Robustness summary])[
  *Cross-carrier sweep (R2, primary claim of this article).* N3-SO phase-locking (trough and upstate, both channels) is significant under every statistic tried (pooled permutation $R_1$ and $T_2$, second-order Rayleigh, per-subject Rayleigh survivor rate 16-17/24) and is the strongest effect in the dataset by a wide margin. N2-spindle-peak reproduces the companion article's own numbers exactly (regression check, R2). REM-theta is uniformly null (all $p>0.32$, 0-1/24 per-subject FDR survivors). This ordering is treated as a robust, internally consistent result. *Onset-hazard tests (R3).* Three independent, individually defensible null constructions disagree in different directions per channel; this disagreement, and the histogram check used to adjudicate it (`S3.2`), is the reported result - not resolved to a single number. *qe-interaction (R4-R5).* A clean null across three qe operationalizations (54 tests total) and an underpowered, non-confirmatory descriptive check on the small SO-coupled subset. Open items not yet closed: the SO-coupling power gap (would need a substantially larger SO-coupled-event yield to become a well-powered test), the single-dataset limitation (no ANPHY/BOAS phase-resolved N3-SO/REM-theta export exists), the absence of any geometry outcome for N3-SO/REM-theta (so R2's carrier ordering cannot itself be linked to a downstream functional consequence the way R4 attempts for spindles), and the histogram check's own descriptive (non-formal-test) status.
]

#bibliography("references.bib", style: "apa")
