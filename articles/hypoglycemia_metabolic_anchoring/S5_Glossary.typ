#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S5 - Glossary",
  short-title: "S5 Hypoglycemia dynamics glossary",
  subtitle: "Operational terms used in this reanalysis",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("glossary", "NDT", "MNDM", "MNPS", "EEG", "reachability"),
  article-type: "Supplementary Material",
)

#set heading(numbering: none)

This glossary distinguishes operational computation from interpretation. None
of the coordinates below is a validated clinical biomarker or a direct measure
of consciousness.

= A - D

*Cohort-anchored coordinate* - A coordinate standardized with feature centers
and scales fitted from pooled euglycemia and hypoglycemia rows. It supplies a
shared comparison frame, not an euglycemia-only physiological baseline.

*Condition-associated* - A difference between the paired hypoglycemia and
euglycemia summaries in this dataset. It does not by itself establish a
mechanism, dose-response, or individual-level effect.

*Coordinate* - A pipeline-defined aggregate of processed EEG features. The
3D families are mobility ($m$), deviation ($d$), and entropy-related structure
($e$); they are not unique latent neural variables.

*3D chart* - The vector $(m,d,e)$ exported by the frozen contract.

*9D chart* - The ordered vector
$(m_a,m_e,m_o,d_n,d_l,d_s,e_e,e_s,e_m)$. The codes identify operational
subcomponents; their names do not establish biological ontology.

= E - L

*$e_e$ and $e_s$* - The exported permutation-entropy coordinate and the
contract's Hjorth-complexity slot, respectively. They are related to the
upstream feature fields but remain contract-specific summaries.

*$e_m$* - An energy/arousal-related high-frequency EEG proxy used in the
EEG-only export when peripheral physiological channels are unavailable. It is
not a direct embodied measure and is not an entropy estimator. The frozen
contract clips standardized features at 6.0, so values at the ceiling are
bounded outputs.

*Engine-level FDR* - Benjamini--Hochberg correction within contrast and
analysis type, applied to all exported summaries in that block, including
means, medians, standard deviations, and auxiliary metrics.

*FDR-supported* - An endpoint with engine-level $q < 0.05$ under the stated
family. This label does not imply clinical validity or biological specificity.

*HYPO minus EU* - The signed contrast produced by passing euglycemia as the
left condition and hypoglycemia as the right condition to an engine that
reports `right - left`.

= M - R

*Jacobian (MNJ)* - The local derivative of the fitted chart flow,
$J = partial f / partial x$. The 3D and 9D Jacobian families summarize local
flow geometry; they do not measure consciousness or behavior.

*Mobility-family coordinates* - $m_a$, $m_e$, and $m_o$, which are exported
aggregates associated with movement or variability on the chart. Their
direction is contract-defined and should not be read as a direct measure of
functional coordination.

*Paired permutation* - A within-participant randomization of the condition
contrast used by the engine with 5,000 draws for the main analysis.

*Reachability* - A short-horizon covariance geometry propagated from a local
linear model, summarized by volume, effective dimension, condition number,
directional entropy, and rotation. It is not observed occupancy or
controllability.

*Validity-limited* - A result whose exported internal QC did not meet the
frozen split-half criteria. All reachability outputs in this run have this
status because the effective-dimension split-half count was 35 (required 50)
and the median correlation was approximately 0.04 (required 0.5).

= S - Z

*Robustness panel* - The 11-endpoint article-local label-swap set: six 9D
coordinate medians ($m_a$, $m_e$, $d_l$, $d_n$, $e_e$, $e_m$) and five
reachability medians. $m_o$ and $d_s$ were outside this panel.

*Standardized-feature clip* - The upper 6.0 bound applied by the frozen
contract to standardized feature values. It limits the interpretation of
coordinates that reach the ceiling.

*Wilcoxon feature check* - A secondary paired Wilcoxon test of six exported
raw EEG feature summaries. Sample and permutation entropy were identical in
the released surface and therefore are not independent replications.

*Not established* - This package does not establish a glucose dose-response,
recovery hysteresis, metabolic gate, embodied-anchoring mechanism, validated
reachability effect, or individual clinical prediction.

#bibliography("references.bib", style: "apa")
