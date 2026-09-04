#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Hypoglycemia Reshapes Stratified Neural Dynamics in a Validity-Bounded Paired Analysis",
  short-title: "Hypoglycemia and neural dynamics",
  subtitle: [A paired reanalysis of 34 type 1 diabetes EEG recordings],
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("hypoglycemia", "type 1 diabetes", "EEG", "neural dynamics", "state-space geometry", "metabolic perturbation"),
  article-type: "Research Article",
  abstract: [
    Acute hypoglycemia can increase slow EEG activity while impairing cognition, making rhythmic structure alone an ambiguous index of functional neural organization. We reanalyzed public 19-channel EEG from 34 people with type 1 diabetes studied during euglycemic and hypoglycemic clamp excerpts. A fixed NeuralManifoldDynamics contract summarized each five-minute condition with 3D and stratified 9D coordinates and local Jacobian metrics; exploratory short-horizon reachability outputs were also audited. In paired hypoglycemia minus euglycemia contrasts, 3D mobility decreased (mean delta = -0.743, FDR q = 0.00090). In the 9D chart, m_a, m_e, d_n, and e_m changed with engine-level FDR q <= 0.0048, while e_e also decreased (q = 0.0396). Raw EEG sanity checks replicated higher theta and delta power and lower exported entropy measures. Reachability outputs were validity-limited under the prespecified split-half criteria; nominal effective dimension and directional entropy were higher in the 33-pair exploratory subset and are not treated as confirmatory evidence. A 10,000-draw paired label-swap test and exclusion of three adjusted-geometry hypoglycemia files preserved the directions of the prespecified 9D robustness panel. These results establish a bounded condition-associated stratified state-space signature, not a glucose dose-response, a recovery trajectory, a causal metabolic gate, or a validated reachability effect.
  ],
  author-summary: [
    Low blood glucose changes the EEG, but a larger slow rhythm does not automatically mean better neural coordination. In a paired diabetes EEG dataset, hypoglycemia altered several components of a multi-part neural-dynamics chart while the exported reachability surface was validity-limited and not confirmatory for collapse or expansion. The result shows why metabolic perturbation must be separated from any direct inference about neural capacity, cognition, or consciousness.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [No external funding supported this analysis.],
  data-availability: [The source EEG dataset is available through Zenodo record 3465213. The H5-derived analysis wrappers and result tables are in this repository under `articles/hypoglycemia_metabolic_anchoring/`.],
  competing-interests: [The author declares no competing interests.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")

= Introduction <sec:intro>

Acute hypoglycemia is a clinically important metabolic perturbation that can
alter cognition and surface electrophysiology. Its cognitive consequences are
heterogeneous across clinical histories and exposure regimes, but severe
hypoglycemia is associated with adverse cognitive outcomes in important
subgroups @tupola2020systematic. Quantitative EEG studies show that
insulin-induced hypoglycemia can increase low-frequency activity
@reno2015eeg. This creates an interpretation problem for dynamical accounts
that treat rhythmic regularity as intrinsically beneficial.

Rubega and colleagues released 19-channel EEG from 34 people with type 1
diabetes recorded in paired euglycemic and hypoglycemic clamp excerpts
@rubega2020detection. Their analysis established condition-sensitive nonlinear
complexity features. We use the same bounded design to ask whether a fixed
multicomponent neural-dynamics measurement contract differentiates the two
metabolic conditions, and whether it supports a claim of reduced
short-horizon reachability.

== Relation to prior hypoglycemia literature

The relevant literature contains several partially separable evidence layers.
Quantitative EEG work has reported increased delta, theta, and alpha amplitude
and lower characteristic frequencies across age, diabetes duration, sex, and
awareness strata @remvig2012eeg. A later clamp study found increased low
frequency activity during hypoglycemia but no difference in the EEG response
between participants with normal and impaired awareness during a single
episode @reno2015eeg. The broader review by Blaabjerg and Juhl synthesized 42
eligible publications and emphasized that EEG changes are measurable but that
blood glucose alone does not reliably predict neuroglycopenia
@blaabjerg2016overview.

Nonlinear and multivariate EEG analyses motivate the present separation between
spectral checks, entropy-related coordinates, and local geometry. Multiscale
entropy detected scale-dependent changes in EEG irregularity during a clamp
@fabris2014mse, while multivariate information partial directed coherence
decreased across selected theta and alpha channel pairs during hypoglycemia
@rubega2016coherence. Antecedent hypoglycemia did not materially change the
subsequent EEG power or frequency response in another clamp study
@sejling2017antecedent. These results support testing more than one signal
layer, but they do not validate the present 3D/9D chart or its reachability
contract.

The clinical relevance of the perturbation is also established independently
of this EEG reanalysis: acute hypoglycemia impairs selective attention and
processing speed @mcaulay2006attention and can impair executive function with
large effects @graveling2013executive. Metabolic studies provide a complementary
boundary rather than a direct EEG explanation: in one clamp/MRS study, TCA-cycle
flux in people with type 1 diabetes did not differ significantly between
euglycemia and hypoglycemia, but was approximately 45% higher during
hypoglycemia than in a previously studied healthy comparison group
@vandeven2013metabolism. Neuroimaging reviews describe additional heterogeneous
adaptations in glucose delivery, uptake, and counterregulation
@rooijackers2016brain. None of these external results licenses an inference
from the current chart to cognition, cerebral fuel availability, or
consciousness.

#netn-box(title: [Core question])[
  Does experimentally induced hypoglycemia produce a reproducible paired shift
  in a fixed 3D/9D neural-dynamics chart, and does that shift justify a claim
  of reduced short-horizon reachability?
]

= Theory <sec:theory>

== Measurement-chart framing

Let $X_t$ denote an unobserved neural process and $Y_t$ the recorded EEG. The
analysis does not identify $X_t$; it constructs a versioned chart $x_t$ from
$Y_t$:

$Y_t = g(X_t) + epsilon_t, quad x_t = C(Y_t).$ <eq:measurement>

The chart has a coarse representation $(m,d,e)$ and a stratified
representation $(m_a,m_e,m_o,d_n,d_l,d_s,e_e,e_s,e_m)$. These coordinates
are operational feature aggregates, not unique latent variables. Local flow is
summarized by an estimated Jacobian $J_t$, while reachability summarizes the
covariance of nearby model-propagated futures:

$Sigma_t^(h+1) = A_t Sigma_t^(h) A_t^T + Q_t.$ <eq:reachability>

Realized coordinates, local flow, and short-horizon capacity are therefore
distinct layers. None is interpreted as a direct measure of consciousness.

== Scope boundary: a metabolic perturbation, not embodied anchoring

This analysis does not test the Embodied Anchoring Principle. The pipeline
exports no cardiac, respiratory, heartbeat-evoked, autonomic, ownership, or
interoceptive-awareness variable, and its paired contrast is solely
hypoglycemia minus euglycemia. Metabolic state is therefore treated here as an
experimentally controlled perturbation condition, not as an embodied anchor,
a rhythmic phase signal, or a direct variable of conscious level.

A future study with continuous glucose, rate of change, autonomic signals,
behavior, and recovery could test whether metabolic availability constrains a
neural-dynamics model. The present excerpts cannot estimate a metabolic
adequacy factor, identify a causal gate on local geometry, or distinguish
metabolic state from its interoceptive representation.

= Methods <sec:methods>

== Dataset

We reanalyzed the public Rubega et al. type 1 diabetes clamp EEG dataset
@rubega2020detection. The corresponding public data record is the Zenodo
deposit `10.5281/zenodo.3465213` @rubega2019dataset. At the time of this
audit (18 August 2026), no matching dataset or dataset-specific article was
found in the public OpenNeuro catalogue; the Zenodo record is therefore the
data archive cited for this reanalysis. The frozen ingest staged 19 scalp-EEG
channels sampled at 200 Hz. The provenance confirmed the identity of T5, T6,
P3, P4, Pz, O1, and O2; the remaining channel labels were filled by the
ingest's best-effort convention mapping. Each participant contributed two
separately excerpted five-minute recordings: euglycemia and hypoglycemia.
The release contains neither a common continuous timeline between excerpts nor
participant-level glucose, awareness, demographic, recovery, or behavioral
measures.

== NeuralManifoldDynamics pipeline

The source H5 bundle was generated on 23 July 2026 under the identifier
`neuralmanifolddynamics_hypoglycemia_t1d_20260723_180515`. EEG was filtered
from 1 to 45 Hz, notch filtered at 50 Hz, and average rereferenced according
to the embedded ingest configuration. The pipeline used 8-second windows at
4-second steps, yielding 74 windows per condition and participant. It exported
3D and 9D coordinates, 3D and 9D Jacobians, raw EEG features, and
subject- and cohort-anchored coordinate layers.

The preprocessing is not a byte-for-byte reproduction of the source article:
this reanalysis used a 1--45 Hz bandpass, 8-second windows with 4-second
steps, and no ICA or amplitude-based artifact rejection in the frozen ingest.
The source analysis used 1--40 Hz filtering, non-overlapping 4-second epochs,
and artifact handling. The present results should therefore be read as a
reanalysis under the stated contract, not as a direct replication of every
source-processing choice.

The primary analysis uses the cohort-anchored layer. Its frozen feature anchor
was fit from pooled euglycemia and hypoglycemia rows, so it supplies a shared
comparison frame but is not an euglycemia-only metabolic baseline.

== Operational meaning of the 9D coordinates

The frozen export ordered the stratified chart as
$(m_a,m_e,m_o,d_n,d_l,d_s,e_e,e_s,e_m)$. The coordinates are pipeline-defined
aggregates rather than latent biological variables. In this EEG-only run,
$m_a$ and $m_e$ are mobility-family aggregates, $m_o$ summarizes within-window
spectral concentration, $d_n$, $d_l$, and $d_s$ are deviation/connectivity
aggregates, $e_e$ is the exported permutation-entropy coordinate, and $e_s$ is
the contract's exported Hjorth-complexity slot. The $e_m$ field is an exported
energy/arousal-related high-frequency EEG proxy used when peripheral
physiological channels are unavailable; it is not a direct embodied measure
and is not an entropy estimator. The exact upstream formulas and signs are
part of the frozen H5 contract, while the article reports the coordinate
names and their empirical contrasts.

The frozen contract applied an upper standardized-feature clip at 6.0. The
hypoglycemia $e_m$ medians for `sub-004`, `sub-017`, and `sub-021` reached that
ceiling; this is why $e_m$ is interpreted as a bounded exported coordinate,
not as an unbounded physiological quantity. The three adjusted-geometry files
were retained in the full coordinate analysis and removed in the directional
sensitivity check.

== Endpoints and statistical design

The prespecified coordinate summaries were the medians of 3D $m$, $d$, and $e$
and the nine stratified coordinates. The 3D Jacobian family comprised
Frobenius norm, rotation norm, and trace. The 9D Jacobian and reachability
families were retained as secondary audit families because the latter's
validity criteria were not met in this short recording design. Raw delta,
theta, alpha, sample/permutation entropy, and Hjorth complexity served as
secondary feature-level sanity checks.

The unit of inference was the participant-condition summary. We tested HYPO
minus EU with the pipeline's paired permutation procedure (5,000 permutations)
and bootstrap confidence intervals. Benjamini--Hochberg FDR controlled
multiplicity within contrast and analysis type @benjamini1995fdr. The
engine-level q-values include all exported summaries in each analysis block
(including means, medians, standard deviations, and auxiliary metrics), not
only the median rows reproduced in S2. The engine reports `right - left`; the
final configuration therefore explicitly defined euglycemia as left and
hypoglycemia as right.

== Robustness protocol

All 34 pairs were complete for 3D/9D coordinate analyses. Thirty-three pairs
had exported reachability summaries because one 9D Jacobian export was
unavailable, but the reachability surface was validity-limited for all
participants: the split-half effective-dimension sample count was 35 and its
median split-half correlation was approximately 0.04, below the frozen
criteria of $n >= 50$ and $rho >= 0.5$. Reachability results are therefore
reported only as an exploratory validity audit. We added a 10,000-draw
within-participant label-swap null over a fixed 11-endpoint robustness panel:
six 9D coordinate medians ($m_a$, $m_e$, $d_l$, $d_n$, $e_e$, and $e_m$) and
five reachability medians. A second sensitivity analysis excluded three
hypoglycemia files whose embedded geometry contract was marked `adjusted`
(`sub-004`, `sub-017`, and `sub-021`). These checks assess association
stability, not unmeasured physiological confounding.

= Results <sec:results>

== R1: Data quality and coverage <sec:r1>

The input bundle contained 68 readable H5 files (34 participant pairs). Every
file provided finite 3D and 9D coordinates and 74 time windows. The 3D
Jacobian was available for all pairs. One hypoglycemia 9D Jacobian was absent,
leaving 33 reachability pairs. However, the engine marked the reachability
surface validity-limited for all participants: its split-half sample-count
summary was 35 rather than the required 50, and its effective-dimension
split-half correlation was approximately 0.04 rather than 0.5. No regional,
continuous-time, or embodied-anchor exports were present.

#figure(
  kind: table,
  clean-table(
    columns: (2.1fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center),
    inset: 5pt,
    table.header([*Surface*], [*EU*], [*HYPO*], [*Paired N*]),
    [3D and 9D coordinates], [34], [34], [34],
    [3D Jacobian], [34], [34], [34],
    [Reachability], [33], [33], [33],
  ),
  caption: [Participant-condition summaries with finite exported values. Reachability summaries are shown for audit but were validity-limited and are not confirmatory.]
) <tab-qc>

== R2: Coarse and stratified coordinates <sec:r2>

Hypoglycemia was associated with lower coarse mobility ($Delta m = -0.743$,
$q = 0.00090$). Coarse $d$ did not differ after correction and the coarse
$e$ decrease did not survive FDR ($q = 0.0747$). The stratified chart resolved
a mixed pattern: $m_a$, $m_e$, and $e_e$ were lower under hypoglycemia, while
$d_n$ and $e_m$ were higher. $d_l$ was nominally lower but did not survive the
engine-level FDR family ($q = 0.0598$); $m_o$ and $d_s$ were also not
FDR-supported. The condition effect is therefore not a uniform shift along a
single coarse coordinate.

== R3: Local flow and validity-bounded reachability audit <sec:r3>

None of the three prespecified 3D Jacobian endpoints survived FDR. In the
secondary 9D Jacobian family, the median operator norm, Frobenius norm, and
rotation norm were lower under hypoglycemia (all engine-level $q = 0.0342$);
these results are reported as exploratory because this family was not part of
the primary 3D local-flow panel. The reachability surface did not meet its
prespecified split-half validity criteria in any participant. Its nominal
effective-dimension and directional-entropy contrasts were higher under
hypoglycemia, while log-volume was not significant, but these outputs cannot
adjudicate reachability collapse in this dataset. They are retained to make
the validity failure and the direction of the exploratory estimates
auditable.

#figure(
  kind: table,
  clean-table(
    columns: (2.3fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center),
    inset: 5pt,
    table.header([*Endpoint*], [*HYPO - EU*], [*p*], [*FDR q*]),
    [$m$ median], [-0.743], [0.0002], [0.00090],
    [$m_a$ median], [-1.096], [0.0002], [0.0018],
    [$m_e$ median], [-0.685], [0.0004], [0.0018],
    [$d_n$ median], [1.014], [0.0008], [0.0031],
    [$e_e$ median], [-0.708], [0.0176], [0.0396],
    [$e_m$ median], [1.024], [0.0016], [0.0048],
    [Reachability dimension], [0.251], [0.0124], [0.134],
    [Reachability log-volume], [0.395], [0.245], [0.537],
  ),
  caption: [Selected paired endpoint results. Reachability rows are exploratory validity audits. Full engine-level tables are in Supplementary Data S2.]
) <tab-primary>

== R4: Label-swap null and adjusted-geometry sensitivity <sec:r4>

The 10,000-draw paired label-swap null supported lower $m_a$, $m_e$, $d_l$, and
$e_e$, and higher $d_n$ and $e_m$, after FDR across the prespecified
11-endpoint robustness set. The same restricted null also supported higher
reachability dimension and directional entropy. The latter two findings remain
exploratory and validity-limited because the reachability surface failed its
frozen split-half criteria; $m_o$ and $d_s$ were not members of this
robustness panel.

Excluding the three adjusted-geometry hypoglycemia sessions preserved the
direction of every prespecified 9D and reachability effect. This directional
check does not establish restricted-sample significance or resolve the pooled
anchor limitation.

== R5: Feature-level sanity check <sec:r5>

Raw feature summaries replicated higher theta ($Delta = 0.130$,
$q = 1.3 times 10^(-5)$) and delta ($Delta = 0.102$,
$q = 8.6 times 10^(-5)$) and lower exported sample/permutation entropy
($Delta = -0.028$, $q = 0.043$). Alpha was also higher. The exported sample-
and permutation-entropy fields had identical values in this pipeline surface
and should not be treated as independent replications.

#netn-box(title: [Dissociation finding])[
  Hypoglycemia increased low-frequency power while the fixed stratified chart
  showed lower mobility- and entropy-related components. Because some
  mobility-family coordinates may share spectral inputs with the raw EEG
  checks, this should be read as a condition-associated multicomponent pattern,
  not as an independent physiological dissociation. It is not evidence that
  either layer indexes conscious level.
]

= Discussion <sec:discussion>

== Primary finding

The central empirical result is a stable paired shift on a fixed stratified
neural-dynamics surface. Lower coarse mobility was decomposed into lower $m_a$
and $m_e$, while lower exported permutation entropy ($e_e$) alongside higher
bounded high-frequency proxy ($e_m$) shows why these features should not be
collapsed into a single complexity score. This extends feature-level
hypoglycemia sensitivity in the source study @rubega2020detection without
claiming that the chart reconstructs a unique metabolic neural state.

== What the analysis does not show

The analysis does not establish a reachability result. The exported
reachability surface failed its prespecified validity criteria, and its
nominal and restricted-null estimates point in the opposite direction from
the initial collapse prediction. Local capacity proxies cannot be equated
with occupancy, behavior, cognition, or consciousness.

The excerpts are not a continuous metabolic trajectory. The data therefore
cannot identify a glucose threshold, rate-of-fall effect, recovery hysteresis,
autonomic warning signal, impaired-awareness subgroup, or metabolic adequacy
gate.

== Implications for metabolic perturbation studies

The result establishes a bounded condition-associated stratified EEG signature,
not a metabolic-anchoring mechanism. Its principal theoretical implication is
negative: increased low-frequency power and altered complexity cannot, by
themselves, be interpreted as stronger functional coordination or reduced
neural capacity. A future study may test metabolic availability as a slow
constraint on neural dynamics, but it would require continuous glucose,
recovery, behavioral performance, and interoceptive measurements. It would
also require a validated reachability contract and an euglycemia-only feature
anchor before interpreting absolute position relative to a metabolic reference
condition.

== Limitations

The data provide 34 paired excerpts but no subject-level clinical covariates or
continuous metabolic measurements. The cohort anchor pools both conditions,
the recording segments are short, and regional exports are unavailable. The
results are condition associations under a specific preprocessing and chart
contract. They should not be generalized to untreated hypoglycemia, recovery,
clinical severity, or conscious experience.

== Conclusion

Hypoglycemia produced a reproducible paired change in a fixed stratified EEG
state-space chart and replicated low-frequency and entropy-related feature
changes. The reachability export was validity-limited and cannot support a
confirmatory conclusion about collapse or expansion, and the study does not
test an embodied-anchoring mechanism. This boundary is substantive: neural
dynamics under metabolic challenge should be assessed with separable
coordinate, local-flow, and validity-audited reachability layers rather than a
single rhythm or complexity score.

= Acknowledgements

We thank Rubega and colleagues for making the source dataset available and
acknowledge the maintainers of the analysis infrastructure used to produce the
versioned H5 exports.

#bibliography("references.bib", style: "apa")
