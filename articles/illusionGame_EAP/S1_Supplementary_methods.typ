#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "S1 Methods — ds004587 EAP",
  subtitle: "Measurement contract, synchronization gates, and planned inferential protocol",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S1.0 Scope and status

This supplement records both the prespecified gates and the completed export audit. Two chronological NMD exports are relevant. `neuralmanifolddynamics_ds004587_20260712_081757` (57 illusion-game H5 files, 47 participants; 8-second windows, 4-second overlap; 3D/9D MNPS, 3D/9D MNJ, raw features, formal anchor-state/quality) first added anchor-state exports but shipped a degenerate robust-z scale defect that inflated its composite `anchor_index` by up to $2.30 times 10^9$-fold relative to its IQR in 488 windows across 10 of 57 files (reported: `handover/handover_To_nmd_ds004587_anchor_index_scale_failure.md`). `neuralmanifolddynamics_ds004587_20260712_111138` (same file/participant counts and window parameters) fixed that defect: every anchor component and composite now satisfies $max|z|/"IQR" <= 14.3$ cohort-wide (confirmed: `handover/handover_To_nmd_ds004587_anchor_index_fix_verified.md`). Both exports contain no rest EEG, event/trial joins, time-reference provenance, or block-native windows. All statistics reported in the main text use `_111138`; results computed against `_081757` are retained under `results/ds004587_20260712/` for provenance. Statistical results are reported only where a versioned CSV exists.

Because `resp_anchor_index` and `anchor_index` are robust-z composites derived from cohort-wide scale statistics, correcting the scale defect changed their value for every participant, not only the participants originally implicated in the failure. Per-subject raw physiological features (e.g. `resp_regular_index`, `ecg_hrv_rmssd_ms`, `ppg_quality_score`) and every Jacobian-derived geometry summary (e.g. `frobenius_norm`) are numerically identical between the two exports; only the anchor-state composites differ.

= S1.1 Dataset and measurement contract

OpenNeuro `ds004587` contains EEG, physiological, and behavioral recordings from 103 healthy participants (ages 21--45) performing visual-illusion judgments and eyes-closed rest. @ds004587 The documented illusion task includes Ebbinghaus, Müller--Lyer, and Vertical--Horizontal families, two randomized series of three 64-trial blocks, and therefore 384 trials for a fully completed protocol. ECG, PPG, and respiration were acquired at 1000 Hz using BITalino/PLUX OpenSignals; the rest recording is documented as 8 minutes, eyes closed. @ds004587

The downstream analysis operates on a release-frozen MNDM export. The audit verified BIDS identifiers, run provenance, geometry outputs, raw physiology features, and anchor state/quality. It did not verify rest/illusion pairs, trial/event provenance, or timing columns; those absent fields close the associated inferential gates. MNDM coordinates and Jacobians are operational outputs of a versioned measurement contract, not direct measurements of latent neural variables. @langell2026nmd

= S1.2 Inclusion, missingness, and duplicate policy

The BIDS audit will create a participant-by-modality matrix before inference. Dataset documentation identifies missing physiology for `sub-FFE111` and `sub-FFE116`, missing behavior for `sub-FFE117`, `sub-FFE139`, and `sub-FFE146`, and duplicate EEG acquisition for `sub-FFE007`. @ds004587 These records are not automatic exclusions from every analysis: eligibility depends on the endpoint and must be reported separately for the primary neural, physiology, and behavioral subsets.

Before analysis, the `sub-FFE007` duplicate policy will be recorded as one of: a predeclared canonical session, a predeclared quality-based choice with criteria applied blind to outcomes, or an explicitly modeled repeated session. The selected rule and its consequences for the paired sample will be reported.

= S1.3 Timing, labels, and synchronization gates

Rest versus illusion is the primary contrast only when condition labels are traced to BIDS metadata or source events. Illusion family, objective strength, response time, accuracy, and event-level analyses require an auditable join between events and behavioral files.

The physiology analysis also requires a documented relation between EEG and BITalino clocks. The audit will test timestamp monotonicity, signal duration, sampling-rate consistency, trigger or shared-event correspondence when available, and drift or offset diagnostics. The gate outcome is:

- *Pass:* sufficient evidence supports the planned temporal alignment; analysis may use the validated resolution.
- *Fail:* event- and phase-resolved physiology analyses are omitted; only analyses justified by independently valid session-level summaries may proceed.
- *Indeterminate:* no temporal EAP inference is performed.

No phase coupling, heartbeat-evoked potential, or lead--lag claim will be made from windowed features without a passed timing gate.

= S1.4 Neural and physiological feature definitions

The primary neural candidate surface is the exported chart $x_t = (m_t, d_t, e_t)$ and, if its geometry contract is valid, the local Jacobian $J_t$. A general local-flow definition is:

$ J_t = partial f(x_t, t) / partial x $ <eq:mnj>

Candidate neural summaries will be selected before testing from fields confirmed in the export; unavailable fields will be recorded as unavailable rather than reconstructed post hoc.

Raw physiological quantities take precedence over composite indices. ECG-derived timing requires validated R peaks; PPG requires a documented pulse-quality rule; and respiration requires a documented signal-quality and phase-extraction rule if phase is used. HRV metrics will state the integration window, number of valid NN intervals, artifact rule, and whether estimates straddle condition boundaries. Standard HRV interpretation is bounded by window duration and signal quality. @taskforce1996

EAP anchor indices, if exported, are secondary operational composites. They are not direct measures of vagal efferent activity, interoceptive awareness, or causal variance control.

= S1.5 Primary and conditional analyses

The primary analysis compares participant-level eligible rest and illusion summaries. Aggregation (median or mean), endpoints, and exact exclusion rules will be fixed after the export audit and before primary testing. The result package will contain all tested endpoints, not only favorable results.

Secondary analyses of illusion family/strength, behavior, event locking, and anchor--geometry association are conditional on S1.3. They will report the exact data level, correlation or model specification, covariates, sample size, multiplicity family, and corrections. Association models cannot resolve causal direction.

= S1.6 Statistics and robustness

The planned paired contrast uses Wilcoxon signed-rank tests @wilcoxon1945 with paired $d_z$ @cohen1988 and confidence intervals. Benjamini--Hochberg FDR is applied within explicitly declared endpoint families at $q < 0.05$. @benjamini1995

The robustness audit includes intersection-sample analysis, epoch-count matching, leave-one-subject-out stability, participant bootstrap intervals, within-subject label permutation, artifact/usable-epoch balance, modality-quality sensitivity, and segmentation sensitivity. Each audit component will be labeled `pass`, `fail`, `not run`, or `not applicable`; no missing check will be narrated as supportive evidence.

#bibliography("references.bib", style: "apa")
