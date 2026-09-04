#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "S3 QC — ds004587 EAP",
  subtitle: "Prespecified gates, sensitivity analyses, and claim boundaries",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S3.0 Status

This supplement records the completed data-contract audit and the gates it closes. The anchor-index-fix export (`neuralmanifolddynamics_ds004587_20260712_111138`) has 47 run-01 illusion-game recordings but no rest EEG, trial/event labels, time-reference provenance, or block-native windows. Therefore the paired primary contrast and its robustness family are not estimable; the IG-only association screen remains exploratory and non-phase-resolved. This export also resolves the composite `anchor_index` scale-integrity failure present in the prior export (`neuralmanifolddynamics_ds004587_20260712_081757`); the two data-contract gates (rest EEG, trial labels) are independent of that fix and remain closed.

= S3.1 BIDS coverage and provenance audit

The audit enumerated the available participant/session/run combinations, task labels, and modality surfaces. It verified the documented missing physiological recordings (`sub-FFE111`, `sub-FFE116`), missing behavioral records (`sub-FFE117`, `sub-FFE139`, `sub-FFE146`), and special multi-run recordings (`sub-FFE007`, `sub-FFE111`, `sub-FFE121`). @ds004587

The completed coverage report must distinguish files that are absent from files that fail quality criteria. It must also state the data-release version, retrieval date, and selected duplicate-session policy.

= S3.2 EEG and geometry quality gates

The completed audit will report preprocessing provenance, retained EEG epochs, rejected epochs, recording-duration balance, and the geometry-contract status per participant and condition. If an endpoint requires a valid Jacobian, participants or epochs without a valid geometry contract are ineligible for that endpoint. The report will not substitute a coordinate-only result for an unavailable Jacobian result without stating the change.

= S3.3 Physiological quality and synchronization gates

ECG analysis requires an auditable R-peak detector, NN-interval quality rule, and a reported window duration. @taskforce1996 PPG and respiration analyses require signal-specific quality rules and retained-duration summaries. The audit must report physiology coverage separately for rest and illusion conditions.

The synchronization audit must state the evidence for EEG--BITalino alignment, any offset/drift correction, and the temporal resolution justified by the evidence. No phase-resolved, event-locked, or directional cardiorespiratory claim is permitted if the timing gate is failed or indeterminate.

= S3.4 Primary-contrast sensitivity checks

If a future export includes rest EEG, the primary rest--illusion contrast will be re-estimated under the following planned checks:

1. *Intersection sample:* participants with eligible data in both conditions.
2. *Epoch-count matching:* within-participant subsampling or weighting to address unequal usable duration.
3. *Leave-one-subject-out:* sign, range, and correction status across all folds.
4. *Participant bootstrap:* confidence intervals using a stated number of resamples.
5. *Within-subject permutation:* null distribution constructed by condition-label permutation within participant.
6. *Segmentation sensitivity:* justified alternative rest/illusion boundaries.
7. *Artifact and quality balance:* comparison of quality flags and retained duration across conditions.

Each check will report its eligible $N$, effect estimate, uncertainty or permutation result, and whether it changes the interpretation. A robustness check is not a substitute for controlling unmeasured task differences.

= S3.5 Conditional anchor-association sensitivities

The timing gate did not pass. The exploratory participant-median screen previously excluded the composite `anchor_index` because one value exceeded its IQR by >2 billion-fold under the `_081757` export; under the corrected `_111138` export, `anchor_index` passes the scale check ($max|z|/"IQR" = 12.1$ cohort-wide) and is included. All retained anchors, including `anchor_index`, have documented coverage and scale checks in `02_anchor_validation`. The direct and HRV-adjusted families contain no BH-FDR survivor (smallest uncorrected $p = 0.022$; all $q >= 0.78$). The main claim remains limited to the estimand actually tested. A correlation surviving these checks would not be evidence of an upstream physiological cause.

= S3.6 Confounds that remain structurally unresolved

Eyes-closed rest and visual-illusion perception differ simultaneously in visual input, eye state, task engagement, motor/response behavior, expectancy, and likely movement or blink patterns. These are design differences, not nuisances that can be eliminated by one covariate. Results will therefore be called condition contrasts, not illusion-specific mechanisms.

Similarly, a common task-state driver can create neural--physiology co-modulation without direct coupling. The current observational dataset has no perturbation, randomization of physiology, or intervention capable of identifying EAP's proposed causal pathway.

= S3.7 Reviewer-facing reporting template

#netn-box(title: [Claim boundary])[
  The audit passed the IG-only anchor-export gate but failed the rest-pair, trial-label, and timing-provenance gates. No paired condition difference was estimated; no exploratory direct or HRV-adjusted association survived correction; causal, phase-resolved, behavioral, and illusion-specific claims remain unsupported.
]

#bibliography("references.bib", style: "apa")
