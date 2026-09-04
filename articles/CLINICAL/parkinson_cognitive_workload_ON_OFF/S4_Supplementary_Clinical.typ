#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary",
  short-title: "Parkinson Clinical Summary",
  subtitle: "A cautious clinician-facing interpretation of the dual-dataset Parkinson cognitive workload study",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope

This supplement provides a clinician-facing summary of the current dual-dataset Parkinson cognitive workload result set.

Its job is to translate the `ds003509` and `ds003506` findings into plain clinical language without overstating the maturity of the evidence. The practical clinical question is not whether there is one task-general Parkinson workload signature, but whether some task contexts preserve a more recoverable disease-state signal than others.

= Clinical questions

The clinical interpretation can be organized around three questions.

1. Does untreated or less-medicated Parkinson physiology differ from controls across both tasks?
2. Does medication move the physiology toward control in either task, or does it mainly produce a different non-control state?
3. Do conflict control and reinforcement learning show the same disease-state pattern, or do they separate into task-specific physiological stories?

= Clinician-facing interpretation

The shortest clinically useful summary is that task context changes how much Parkinson-versus-control physiology is recoverable. Both tasks show evidence of disease-state physiology, but not in the same way.

In the Simon conflict dataset, both Parkinson `OFF` and Parkinson `ON` remained clearly separated from controls in the corrected standard layer. The retained rows were broad and mostly geometric, especially regional and global `9D` summaries, with an added corrected collapse/reachability tail in the `ON` branch. Medication did not erase the group-level non-control pattern. There was some weaker paired `OFF vs ON` movement, but it was small compared with the broader disease-state separation.

In the reinforcement-learning dataset, the clearest corrected signal still came from Parkinson `OFF` versus control. That signal mixed geometric rows with more conventional EEG-facing summaries, especially relative alpha measures. The medicated Parkinson `ON` group showed a small but nonzero corrected Jacobian branch, with `aci_mean` already entering at `q < 0.05` and additional Jacobian rows surviving at `q < 0.1`. No corrected paired `OFF vs ON` result survived in this task, and no corrected reachability branch emerged.

Across both datasets, the event-locked wrapper did not yield corrected positive rows. Clinically, that means the present analysis does not support a claim that short task-window trajectory summaries provide a robust biomarker-like signal beyond the standard layer.

= Interpretation boundary

The same caution as the main manuscript still applies:

- this is a group-level exploratory physiology study,
- not a validated bedside biomarker,
- not a treatment-response predictor,
- and not a substitute for neurological examination, medication review, or standard EEG interpretation.

The most defensible clinical takeaway is therefore limited: conflict-control EEG geometry appears to preserve a more recoverable Parkinson-versus-control signature than reinforcement-learning EEG geometry in this cohort, while medication-related within-subject changes remain modest under the present corrected analysis.
