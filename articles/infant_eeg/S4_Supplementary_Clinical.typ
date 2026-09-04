#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary",
  short-title: "S4 Clinical Summary - Cohort-anchored infant EEG geometry",
  subtitle: "A cautious clinician-facing interpretation of the article",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope and intent

#netn-box(title: [Important: observational study - no intervention tested])[
  This study tested *no* clinical intervention and enrolled *no* clinical population. Participants were typically developing infants performing ordinary mixed rest/reaching EEG recordings; no physiology or brain state was manipulated. All reported findings are *observational, longitudinal-descriptive, and group- or child-level*, not individual-diagnostic. No causal inference beyond the tested statistical associations is warranted, and nothing here should inform an individual clinical decision.
]

This supplement is written for clinicians, researchers in adjacent fields, and other readers who are not specialists in this article's statistical methods (generalized estimating equations, spline models, permutation tests). The goal is a plain-language, appropriately hedged translation of the main manuscript, not an amplification of its claims. Three framing limitations apply throughout: (1) the sample is exclusively typically developing infants, so nothing here speaks to any clinical or at-risk population; (2) the design is correlational (age vs. an EEG-derived summary), not interventional or causal; and (3) the outcome metrics ("cohort-anchored coordinates", "reachability", "MNJ") are exploratory, non-validated research constructs specific to this analysis pipeline, not established clinical biomarkers.

= What is the framework, and why does it matter here?

The analysis pipeline (Noetic Diffusion Theory tooling) treats a window of EEG signal as a point in an abstract, multi-dimensional "state space", built from spectral and connectivity-like features of the EEG. Two things are then computed from a sequence of such points: (1) *where* a recording sits in that space (its "coordinates"), and (2) *how it locally moves* from one moment to the next (its "local dynamics", summarized as "MNJ" and "reachability"). This distinction matters clinically because a recording could occupy a different "place" in this space as a child ages, without that place-shift necessarily reflecting a detectable change in the moment-to-moment dynamics estimated from the same short recording -- and indeed that is what this study finds. Coordinates and dynamics are complementary but separable descriptions of the same signal, and this article deliberately tests both rather than assuming one implies the other.

= What was studied

The data are 70 EEG recordings from 22 typically developing infants (ages 38-203 days, roughly 1-7 months), collected during a mixed rest/reaching task, from a previously published, independently collected Figshare dataset (not new data collected for this study). Twenty of the 22 children had more than one recording over time, which allows within-child (i.e., "did this same child's numbers change as they aged") comparisons, not just between-child ("do older children look different from younger ones") comparisons. Before analysis, segments of each recording flagged as likely contaminated by movement or other artifacts (by an independent artifact-detection pass on the source recordings) were excluded, which removed roughly a quarter of the candidate short time-windows; this is a data-quality step, not a result, but it is mentioned here because one specific finding changed after this cleaning step (see "What was NOT found," below). All EEG-derived summaries were computed with a shared reference scale ("cohort anchor") common to the whole group, so that recordings from different children and visits are directly comparable on the same numeric scale.

= What the coordinates mean in plain language

Three headline "coordinate" summaries describe, in effect, how variable, how far-flung, and how disordered a recording's brain-state trajectory is within the abstract state space: an informal shorthand is "mobility" (how much the state moves), "deviation" (how far it strays from a typical/central pattern), and an entropy-related measure (how unpredictable/disordered its pattern is). A parallel nine-dimensional version of the same idea splits each of these three ideas into three further sub-facets. None of these numbers is a validated clinical marker of brain maturation, arousal, or any diagnosis; they are internal summary statistics of this specific analysis pipeline, reported here purely as descriptive, exploratory research quantities.

= The main findings, in order of clinical salience

== 1. EEG-derived coordinates changed with age, within individual children

Across all 12 coordinate summaries (3 in the simpler 3D version, 9 in the more detailed version), the position of a child's recording in this abstract space shifted consistently as that same child got older, not merely because older children looked different from younger children as separate groups. This "within-child" attribution is an important, reassuring technical detail: it means the age association is not simply an artifact of comparing different children's baseline levels to each other.

== 2. That finding is less certain for some coordinates than others

A stricter statistical check -- built specifically to guard against overconfident results when only 22 children contribute the data -- supported half (6 of 12) of the coordinate summaries once corrected for testing 12 things at once. Two coordinates ("mobility" and the entropy-related summary) were flagged as less statistically robust; the entropy-related summary in particular failed two internal robustness checks and should be treated as the least confirmed of the twelve findings.

== 3. No detectable change in moment-to-moment brain-state dynamics, tested two independent ways

Two separate analyses asked whether the *local dynamics* (not just the "place" in the state space, but how quickly and how it moves from moment to moment) also changed with age: one using each recording's own internal moment-to-moment pattern, and one pooling patterns from other children in the group to ask the same question at the level of the whole cohort. Neither analysis found a statistically supported age-related change; one narrower, secondary slice of the cohort-pooled analysis (a subset using only the most directly recorded ages) showed one summary crossing an uncorrected significance threshold, but this single result did not survive the same multiple-testing correction applied everywhere else and should not be read as a confirmed finding.

== 4. Classical EEG comparator context

As a descriptive context check, 34 conventional EEG measures were extracted from the same artifact-masked recordings. Twenty-four showed an age association in the asymptotic cohort model, but only five survived the conservative child-cluster permutation check; three spectral measures (the beta/alpha ratio and relative beta/gamma power) survived both checks. This confirms that recognizable classical EEG maturation signal is detectable in this cohort and pipeline, but it does not validate the exploratory MNPS coordinates or imply that the local-dynamics nulls are a generic failure of the data. Frontal-central coherence measures had 80% session coverage (the connectivity pack as a whole had 80--96%) and unusually extreme statistics, so they should not be used clinically or interpreted as established maturation markers without targeted replication. Xiao et al. (2018) and Schaworonkow and Voytek (2021) analysed this same Figshare corpus; Marshall et al. (2002) provide an independent developmental-EEG context @xiao2018power @marshall2002eeg @schaworonkow2021aperiodic.

= What was NOT found - equally important

No individual-level prediction, diagnostic classification, or clinical risk score is proposed, tested, or supported by this study. No comparison to any clinical, at-risk, or non-typically-developing population was made; every child in this dataset was typically developing. No claim is made that a specific brain region, neurotransmitter system, or developmental mechanism drives the observed coordinate shift -- the "coordinates" are abstract, pipeline-internal quantities, and the paper cautions against over-interpreting them as directly observed neural states. The moment-to-moment "local dynamics" analyses (item 3 above) found no statistically supported age effect in either of two independent tests, which is itself an important negative finding: it means the study should not be cited as evidence that "brain dynamics" (as opposed to "brain-state position") measurably change with age in this age range and sample size. Before the artifact-cleaning step described above, a small, non-definitive hint of a local-dynamics age effect had appeared in a different secondary analysis; after removing artifact-contaminated segments, that particular hint disappeared entirely. That pattern is reassuring in one specific sense (it suggests the earlier hint was likely a data-quality artifact rather than a genuine signal), but a separate, unrelated uncorrected hint (noted above) remains in one narrow subset even after cleaning, which illustrates why none of these local-dynamics findings should be treated as settled without independent replication.

= How to read the technical terminology clinically

"Cohort-anchored coordinate" can be read, loosely, as "where this recording sits on a shared numeric scale built from the whole group of children", roughly analogous to how a growth chart places a single measurement on a shared reference scale -- except this scale is a research construct specific to this pipeline, not a validated developmental reference. "Within-child effect" means the pattern held up when comparing a child to their own earlier/later self, which is generally a stronger form of evidence than only comparing different children to each other. "FDR-supported" ("false discovery rate") is a standard statistical adjustment for testing many things (here, 12 coordinates) at once, to avoid falsely calling a result significant purely by chance; "cluster-permutation check" is an additional, more conservative statistical safeguard used here specifically because the sample includes data from only 22 children, a regime where standard statistical formulas can understate uncertainty. "MNJ" and "reachability" refer to the local-dynamics analyses described above (item 3); none of these terms denote a clinically validated measurement.

= What clinicians should not conclude

Clinicians should not conclude that any individual infant's development can be assessed, screened, or risk-stratified using these coordinates or reachability summaries; the study provides no individual-level predictive validity. This study should not be cited as evidence of a specific neural mechanism, brain region, or developmental process, since the coordinates are abstract feature-space summaries, not directly observed neural states. It should not be generalized to any clinical, at-risk, or non-typically-developing population, since none was studied. It should not be read as demonstrating that infant brain "dynamics" (as opposed to state-space "position") change measurably with age at this sample size, since two independent tests of that specific question were both null. Finally, the two coordinates flagged as statistically fragile ("mobility" and the entropy-related summary) should not be treated as established findings pending independent replication.

= What would increase clinical confidence

Independent replication in a larger, age-balanced cohort with more children per age band would directly address the small-cluster statistical fragility identified here. Extension to clinical or at-risk populations (e.g., preterm infants, infants with known neurodevelopmental risk factors) would be needed before any clinical translation could even be considered, and was entirely outside the scope of this study. Longitudinal designs with denser, more evenly spaced repeated recordings per child would strengthen the within-child evidence base. Finally, any future clinical translation would require validating these EEG-derived summaries against independent, clinically accepted developmental outcome measures, which was not attempted here.

= Summary for clinical readers

In a group of typically developing infants, an EEG-derived summary of "where a recording sits" in an abstract state space shifted consistently with age within individual children, and 6 of 12 summaries remained supported under a conservative statistical robustness check, though two particular summaries were flagged as fragile. Two internal tests of whether the moment-to-moment brain-state dynamics (as opposed to state-space position) also changed with age were both negative, and a small earlier hint of such a dynamics effect disappeared entirely once artifact-contaminated recording segments were removed. This is a descriptive, hypothesis-generating result in typically developing infants; it supports no individual-level, diagnostic, or clinical-population conclusion, and should be read as one input into future, larger, and clinically extended replication work rather than as a validated clinical finding.

#bibliography("references.bib", style: "apa")
