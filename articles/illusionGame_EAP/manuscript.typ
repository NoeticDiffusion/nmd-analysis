#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Cardiorespiratory anchor indices and neural manifold geometry during visual-illusion perception",
  short-title: "EAP in visual-illusion perception",
  subtitle: "A gated analysis audit for OpenNeuro ds004587",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("visual illusion", "EEG", "ECG", "respiration", "neural manifold", "embodied anchoring"),
  article-type: "Research Article",
  abstract: [
    We audited OpenNeuro `ds004587`, a public multimodal visual-illusion dataset with 103 enrolled healthy participants. @ds004587 The accessible EEG export contains 57 illusion-game recordings from 47 participants, but no resting EEG, trial/event labels, time-reference provenance, or block-native windows. We corrected an NMD configuration defect that had left the embodied anchor-state export incomplete, then identified a second NMD defect in which a degenerate robust-z scale could inflate one anchor component (and, through it, the composite `anchor_index`) by up to nine orders of magnitude; a subsequent NMD export fixed this defect (confirmed: cohort-wide $max|z| / "IQR" <= 14.3$, versus $>2.3 times 10^9$ before the fix). Using the corrected export, we performed a limited IG-only participant-median association screen that now includes `anchor_index`. Neither direct nor HRV-adjusted associations of any retained anchor, including `anchor_index`, with MNPS/MNJ summaries survived BH-FDR correction (all $q >= 0.78$; $N = 45$ for physiology-complete participants). The planned rest-versus-illusion and trial-strength analyses remain not estimable from this release: the fix corrected a scale defect, not the absence of rest EEG or trial labels. These results neither validate nor refute a causal Embodied Anchoring Principle; they document a null exploratory screen and the data-contract requirements for a valid follow-up.
  ],
  author-summary: [
    We checked whether this dataset can test body--brain anchoring during visual-illusion perception. It cannot support the planned rest comparison or trial-level question because the released data lack rest EEG and an auditable trial-to-EEG alignment. Along the way we found and reported a scale defect in the measurement pipeline's composite anchor index; a corrected export let us re-run the exploratory screen with that composite included. In the available illusion-game recordings, no body--geometry association survived multiple-comparison correction, with or without the composite anchor.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be confirmed before submission.],
  data-availability: [The source dataset is OpenNeuro `ds004587` (doi: 10.18112/openneuro.ds004587.v1.0.0). Versioned analysis outputs and scripts will be cited here after the analysis run is completed.],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")

= Introduction <sec:intro>

Visual perception is shaped by stimulus context, internal state, and task demands. The present study uses a public dataset designed around perceptual judgments of three classical visual-illusion families: Ebbinghaus, Müller--Lyer, and Vertical--Horizontal. @ds004587 The dataset includes repeated illusion blocks with manipulated task difficulty and illusion strength, plus eyes-closed resting-state recordings. These features support a carefully bounded comparison of rest and illusion-perception conditions; they do not identify neural mechanisms of illusion susceptibility.

Low-dimensional neural state-space methods summarize time-varying neural activity as trajectories, complementing conventional sensor-level or spectral analyses. @cunningham2014 @vyas2020 The present analysis uses a versioned MNDM measurement layer to derive an operational three-coordinate neural chart and optional local-flow summaries. These quantities are analysis constructs, not direct measurements of a latent manifold or cognitive content.

Cardiac and respiratory signals can covary with neural dynamics and cognition. @azzalini2019 @kluger2021 The Embodied Anchoring Principle (EAP) provides a speculative framework in which interoceptive state constrains a neural variance schedule. This study cannot test that causal mechanism: it can only test condition-level differences and, contingent on validated alignment, observational associations between physiology-derived summaries and neural geometry.

#netn-box(title: [Core question])[
  Do pre-specified physiology-derived anchor summaries and EEG-derived neural-geometry summaries differ between eyes-closed rest and visual-illusion perception in `ds004587`, and are any direct associations robust after synchronization and quality-control gates?
]

= Theory and inferential boundary <sec:theory>

== Operational neural geometry

For an analysis trajectory $x_t$, MNDM represents local flow by an estimated Jacobian:

$ J(t) = partial f(x_t, t) / partial x $ <eq:mnj>

where $f$ is an estimated local flow field. Candidate summaries include the Frobenius norm $||J||_F$, rotation-related summaries, and the three exported chart coordinates $(m, d, e)$. Their availability, units, preprocessing dependencies, and quality gates will be documented from the completed run manifest. They are versioned computational measurements, rather than direct observables of mental states. @langell2026nmd

== Embodied anchoring as a secondary framework

EAP proposes that cardiac and respiratory variables may condition neural dynamics. A schematic formulation is:

$ d X_t = -G_t(X_t) nabla Phi(X_t, t) d t + sigma(t) d W_t $ <eq:ndt>

This equation is a theoretical framing, not a fitted causal model in this study. Physiology-derived features such as R-peak-derived timing, respiratory phase, or windowed HRV will be treated as measured covariates only after signal-specific quality checks. Cardiorespiratory phase and neural phase must be demonstrably synchronized before any phase-resolved analysis is permitted. @taskforce1996 @park2014heartbeat

= Methods <sec:methods>

== Dataset and verified acquisition facts

`ds004587` (`IllusionGameEEG_data`) contains EEG, physiological, and behavioral data from 103 healthy participants aged 21--45 years, collected during visual-illusion tasks and resting-state recordings. @ds004587 Participants completed perceptual judgments for Ebbinghaus, Müller--Lyer, and Vertical--Horizontal illusions. The documented task has two randomized series of three illusion blocks, each block containing 64 trials, for 384 illusion trials per participant when fully completed. The dataset documentation describes an 8-minute eyes-closed resting recording; ECG, PPG, and respiration were recorded through the BITalino/PLUX OpenSignals system at 1000 Hz. @ds004587

Dataset documentation also reports missing physiological recordings for `sub-FFE111` and `sub-FFE116`, missing behavioral data for `sub-FFE117`, `sub-FFE139`, and `sub-FFE146`, and duplicate EEG acquisition for `sub-FFE007`. @ds004587 The analysis will confirm these cases against the downloaded BIDS release and specify a duplicate-session rule before any statistical test. No enrolled, usable, or paired analysis sample size is asserted here.

== Analysis contract and preprocessing status

The original full export (`neuralmanifolddynamics_ds004587_20260711_235903`) contained 57 illusion-game H5 files from 47 participants, using 8-second windows and 4-second overlap. It included 3D/9D MNPS, 3D/9D Jacobians, regional MNPS, and raw physiology features, but lacked formal anchor state, labels, event joins, time-reference provenance, block-native windows, and rest EEG. A summarize-only refresh (`neuralmanifolddynamics_ds004587_20260712_081757`) corrected the configuration placement of `anchor_state`, yielding anchor state and quality groups in all 57 H5 files. It did not add rest EEG, labels, timing provenance, or block-native windows. The audit and run contract are recorded in `handover/20260712_ds004587_phase0_audit.md`.

That refresh introduced a second, independent defect: its composite `anchor_index` failed a gross-scale integrity check (cohort maximum $8.75 times 10^8$ against an IQR of $0.38$, i.e. $max|z|/"IQR" approx 2.30 times 10^9$), traced to a degenerate robust-z scale in one fallback feature (`eog_blink_rate`) propagating unbounded into `sympathetic_index` and, via the nanmean composite, into `anchor_index`; the failure recurred in 488 windows across 10 of 57 run files, not only the single worst case. This was reported upstream (`handover/handover_To_nmd_ds004587_anchor_index_scale_failure.md`). A further NMD export (`neuralmanifolddynamics_ds004587_20260712_111138`, 57 illusion-game H5 files, 47 participants) resolved this defect: across all files, $max|z|/"IQR" <= 14.3$ for every anchor component and composite, with no window exceeding an absolute `anchor_index` value of $10^3$ (confirmed in `handover/handover_To_nmd_ds004587_anchor_index_fix_verified.md`). This export did not add rest EEG, trial/event labels, or timing provenance; those gates are unchanged. All results reported below use the `_111138` export.

== Endpoint hierarchy

The planned primary contrast was each participant's eligible eyes-closed rest versus aggregated illusion-perception epochs. It is not estimable: the canonical BIDS release has no rest EEG recordings. The only completed empirical screen is therefore secondary and IG-only: participant medians of retained respiratory/HRV features and the composite `anchor_index` versus MNPS/MNJ summaries. `anchor_index` now passes the scale-integrity gate in the corrected export and is included alongside its components.

Illusion-family, objective-strength, response-time, accuracy, and event-locked analyses are secondary and conditional. They will be omitted if BIDS event labels, behavioral joins, or EEG--BITalino clock alignment cannot be verified.

== Statistical design

The unit of inference will be the participant-level paired summary, constructed from valid epochs according to a predeclared aggregation rule. The planned primary contrast is a paired Wilcoxon signed-rank test, with paired $d_z$ and a confidence interval reported alongside the exact sample size. @wilcoxon1945 @cohen1988 Multiplicity will be controlled within predeclared endpoint families using Benjamini--Hochberg FDR at $q < 0.05$. @benjamini1995 No significance, direction, or effect size is pre-filled in this scaffold.

== Robustness and confound protocol

Before interpreting any primary contrast, the analysis will assess: (1) subject and session intersection; (2) epoch-count matching; (3) leave-one-subject-out stability; (4) participant bootstrap intervals; (5) within-subject condition-label permutation; (6) EEG artifact and usable-epoch balance; (7) ECG, PPG, and respiratory quality and coverage; and (8) sensitivity to rest/illusion segmentation. Each check will be reported as passed, failed, not run, or not applicable; absent results will remain `TBD`.

== Conditional EAP association analysis

After synchronization validation, a separate, secondary family will estimate within-subject associations between preregistered anchor features and neural endpoints, with task condition and appropriate quality variables handled explicitly. Effect sizes, uncertainty, correction family, and leave-one-subject-out direction stability will be reported. Such associations cannot distinguish a physiology-to-neural pathway from task-driven co-modulation, reverse dependence, or unmeasured common causes.

= Results <sec:results>

== R1: Coverage, label provenance, and synchronization

The refreshed run contains 47 run-01 illusion-game recordings (10,251 original windows before pilot-run selection), with no rest rows; all 47 participants are therefore ineligible for the planned paired contrast. The label audit found only the filename-derived `illusion_game` condition, with no trial ID, illusion family/strength, block, onset, duration, response-time, or correctness column. The required EEG--BITalino synchronization and event-join evidence is absent. Event- and phase-resolved inference was not attempted.

== R2: Primary rest-versus-illusion comparison

Not estimable. The release contains no rest EEG, hence no participant has paired rest and illusion neural geometry. The planned Wilcoxon, effect-size, and robustness analyses were intentionally gated and return no result.

== R3: Robustness audit

Not estimable for the planned contrast because the paired sample is empty. This is a data-availability limitation, not evidence of a null rest-versus-illusion effect.

== R4: Conditional anchor--geometry associations

The exploratory IG-only participant-median screen included 45 physiology-complete participants after excluding the two documented missing-physiology cases, using the corrected export in which `anchor_index` passes the scale-integrity gate. Across all retained anchors (including `anchor_index`) and MNPS/MNJ summaries, no direct or HRV-adjusted association survived its BH-corrected family (smallest direct uncorrected $p = 0.022$, `ppg_quality_score` versus $m$; all corrected $q >= 0.78$). The strongest predeclared directional screen was `resp_anchor_index` versus Frobenius norm ($r_s = -0.07$, leave-one-subject-out range $[-0.11, -0.01]$, sign-consistent, bootstrap 95% CI $[-0.38, 0.28]$); it is not statistically supported. `anchor_index` itself showed its largest uncorrected association with `trace` ($r_s = -0.30$, $p = 0.046$, $q = 0.85$), also not surviving correction. These participant-level associations do not establish timing, phase coupling, or causal modulation.

The `resp_anchor_index`--Frobenius-norm point estimate differs between the two NMD export versions used during this audit (uncorrected export: $r_s = -0.26$; anchor-index-fix export: $r_s = -0.07$). We verified this is the expected consequence of the fix, not a new instability: per-subject Frobenius-norm medians and every raw physiological feature (e.g. `resp_regular_index`, `ecg_hrv_rmssd_ms`) are bit-identical across the two exports, while `resp_anchor_index` and `anchor_index` are robust-z composites computed from cohort-wide scale statistics; correcting the degenerate-scale defect necessarily recomputed those statistics for every participant, not only the originally flagged cases, changing every subject's `resp_anchor_index`/`anchor_index` value. Neither point estimate was significant before correction, and correction changes only the composite anchor values, not the neural-geometry endpoints.

== R5: Conditional illusion-strength and behavior analyses

Not attempted. The release contains behavior files but the NMD export contains no trial identifiers or timing bridge; filename matching cannot establish trial-to-EEG alignment.

= Discussion <sec:discussion>

== Interpretation policy

This section will be completed only from versioned outputs. A rest-versus-illusion difference would support a condition-sensitive association in the chosen measurement contract. It would not isolate visual-illusion processing from differences in eye state, visual stimulation, attention, task demands, movement, or peripheral physiology. Likewise, a direct anchor--geometry association would remain observational and would not demonstrate EAP's proposed causal variance-schedule mechanism.

== Limitations fixed by design

The rest and illusion conditions differ along multiple dimensions, so the primary contrast is not process-pure. Physiology availability and behavioral availability are incomplete for documented participants. @ds004587 Windowed HRV and phase-resolved physiology answer different questions and must not be conflated. The article will report the exact time resolution used and will not use a low-resolution association to support cycle-level cardiac or respiratory claims.

== Conclusion

The ds004587 release supports a refreshed IG-only anchor export and a null, non-phase-resolved exploratory association screen. It does not support the planned rest-versus-illusion article or trial-level illusion-strength claims. A valid follow-up requires rest EEG or a reframed IG-only question, together with a frozen behavior/physiology timing contract.

= Acknowledgements

We acknowledge the dataset contributors and participants who made `ds004587` publicly available.

#bibliography("references.bib", style: "apa")
