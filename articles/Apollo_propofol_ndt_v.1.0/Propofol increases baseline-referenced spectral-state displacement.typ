// Apollo propofol NDT v1.0 — occupancy spine (exploratory secondary analysis).

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Propofol increases baseline-referenced spectral-state displacement: an exploratory analysis",
  short-title: "Exploratory spectral-state displacement under propofol",
  subtitle: "Exploratory secondary analysis of Cambridge propofol sedation EEG in a frozen NeuralManifoldDynamics export",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: (
    "propofol",
    "sedation",
    "EEG",
    "occupancy",
    "neural manifold dynamics",
    "responsiveness",
  ),
  article-type: "Research Article",
  abstract: [
    Propofol sedation is often discussed as a change in dynamical accessibility, yet present-state
    relocation and a changed future law at matched state are different claims. We re-analysed
    20-participant Cambridge propofol EEG @chennu2016propofol from a frozen NeuralManifoldDynamics
    export, using baseline-referenced radial displacement (legacy analysis variable: occupancy) — the median Euclidean radius of eligible windows in a baseline-fixed
    eight-feature spectral chart. Occupancy increased from 2.71 at pre-drug baseline to 4.07 at
    first protocol sedation ($n=20$, 18/20 increase, median $Delta=+1.70$, $d_z=+1.15$, exact sign
    $p=4.0 times 10^(-4)$) and to 8.68 at later protocol sedation (20/20 increase, median
    $Delta=+5.92$, $d_z=+1.12$), with incomplete return at recovery (3.95; median $Delta=+1.34$,
    $d_z=+0.45$). The exploratory responsiveness analysis provided no evidence of a monotonic
    association between this scalar and behavioural impairment: occupancy-blind binomial
    classification recovered the original 7/13 impaired/responsive split, occupancy versus hit
    count at later sedation was $rho=-0.08$, and the group contrast was NOT_TESTABLE because the
    impaired arm had $n=7$. These data cannot establish that an association is absent. Matched-state
    tests of a changed future law were not testable: only 7/20 participants had $>=20$ caliper-matched
    pairs. Propofol produced a large baseline-referenced spectral relocation that increased across
    protocol sedation and partially reversed during recovery; whether that displacement is associated
    with loss of responsiveness remains unresolved.
  ],
  author-summary: [
    During propofol sedation the measured spectral state moves far from its awake neighbourhood,
    more so at the later protocol phase, and only partly returns during recovery. That relocation
    is large and broadly consistent across people. This exploratory sample provides no evidence
    that the scalar is a monotonic marker of behavioural responsiveness: similarly huge displacement
    can coexist with 39/40 or 6/40 correct responses, while the small impaired arm limits inference.
    Whether the local future dynamics also change at a matched state remains untestable here,
    because sedation leaves too little overlap with the awake neighbourhood.
  ],
  author-contributions: [RL: Conceptualization, Methodology, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [Funding information will be inserted at submission.],
  data-availability: [
    Original EEG and `datainfo.mat` labels: University of Cambridge Apollo repository, DOI
    10.17863/cam.68959 @chennu2016data. NeuralManifoldDynamics processed bundle:
    `neuralmanifolddynamics_Sedation-RestingState_20260918_075713`. Article-local analysis:
    `articles/Apollo_propofol_ndt_v.1.0/src/` in the project repository. Occupancy, matching, and
    LOR tables: `results/v1_occupancy_20260921/` and `results/v1_lor_20260921/`. A reproducibility
    manifest is provided at `reproducibility_manifest.json`; it records the verified repository
    base commit, relative artifact paths, existing manifest hashes, and the limits of the raw-data
    hash coverage. The current article revision is a working-tree revision and is not claimed to
    have a release DOI.
  ],
  competing-interests: [The author declares no competing interests, subject to final confirmation at submission.],
)

#set heading(numbering: "1.")
#set math.equation(numbering: "(1)")

= Introduction <sec:intro>

Sedation with propofol is a controlled way to study how the brain leaves the awake behavioural
regime. It is also a setting in which two questions are easily conflated: how much drug is
present, and whether a person can still report a stimulus. Chennu and colleagues already showed,
in the Cambridge high-density EEG cohort analysed here, that network markers of drug exposure and
of behavioural responsiveness are not the same object @chennu2016propofol. Baseline
alpha-network strength predicted who became impaired, whereas slow–alpha phase-amplitude coupling
tracked plasma concentration.

Propofol EEG physiology is already known to involve frequency- and spatially structured changes:
low-frequency activity and frontal alpha emerge around unresponsiveness, posterior alpha is
attenuated, and induction and recovery need not be mirror images @purdon2013eeg @cimenser2011coherence.
Human intracranial and scalp work likewise identifies abrupt state transitions, altered
thalamocortical alpha organisation, and fragmentation of activity across time and space
@mukamel2014transition @lewis2012fragmentation @ching2010alpha. Complexity also changes under
propofol @schartner2015complexity. The present analysis is therefore not offered as a discovery
of those established phenomena; it asks whether a fixed multifeature chart separates present-state
displacement from behavioural responsiveness and from matched-state one-step summaries.

A related but distinct theoretical distinction is between where a measured neural state currently
sits and what can happen from that state. Noetic Diffusion Theory (NDT) treats the measurement
chart as an operational interface, not as the latent process: present-state geometry is not the
same claim as a change in the conditional future law at a matched state @langell2025ndt. A large
displacement under propofol could mean that the system has left the awake neighbourhood, that the
local transition law has changed, both, or neither in a form that a given export can test.

We performed an exploratory secondary analysis of the same 20-participant resting-state EEG,
using a frozen NeuralManifoldDynamics export rather than re-deriving connectivity graphs.
Protocol phases were taken from the original Cambridge `datainfo` table (pre-drug baseline, first
protocol sedation, later protocol sedation, recovery) and were not inferred from file order.
Later protocol sedation is the original moderate-sedation session; it is not a label of
unresponsiveness. Behavioural impairment was assigned occupancy-blind from the original 40-trial
hit counts using the binomial confidence-interval rule of the source paper.

  The main descriptive object, selected after a sequence of discovery screens, is baseline-referenced
  radial displacement (``occupancy'' in frozen code): the median
Euclidean radius of eligible windows in an eight-feature spectral chart whose centre and scale
are taken from that participant's pre-drug baseline only. Occupancy asks whether sedation
displaces the measured state relative to the awake neighbourhood; radius alone can reflect a
phase-centre shift, within-phase broadening, or both. A matched-state increment test
then asks whether one-step speed and spread still differ after pairing sedation windows to nearby
  baseline windows. Finally, occupancy is joined to the behavioural split for an exploratory
  association analysis with loss of responsiveness (LOR).

#netn-box(title: [Core question])[
  Does propofol produce baseline-referenced displacement of neural spectral state, what exploratory
  evidence is available for an association with behavioural loss of responsiveness, and can a change
  in the local future law be tested at matched present state?
]

= Results <sec:results>

All contrasts below are exploratory. Independent code review and a confirmatory analysis lock
were not completed. Occupancy was promoted after inspecting unmatched occupancy at first
sedation and recovery in a matched-state screen; later-sedation occupancy was then an ordered
  secondary on the same frozen scalar. The first-sedation contrast is retained as an ordered
  reporting contrast, not a confirmatory primary endpoint; its $p$-values are descriptive and
  exploratory. Exact procedures are in Methods and S1.

== R1: Baseline-referenced radial displacement increases across protocol phases <sec:r1>

In the baseline-fixed eight-feature spectral chart, occupancy increased from a cohort median of
2.71 at pre-drug baseline to 4.07 at first protocol sedation and 8.68 at later protocol sedation,
then returned only partly at recovery (3.95; @fig-trajectory). The shape is an ordered
protocol-phase trajectory with incomplete reversal, not a claim of monotonic unconsciousness.

#figure(
  image("figures/occupancy/fig1_occupancy_trajectory.png", width: 95%),
  caption: [Baseline-fixed occupancy trajectory. Light lines are participants; the black line is
  the cohort median. Occupancy is the median Euclidean radius of eligible one-step sources in an
  eight-feature `features_raw` robust-$z$ frame whose centre and scale come from that
  participant's pre-drug baseline only. Source: `results/v1_occupancy_20260921/occupancy_subject.csv`.],
) <fig-trajectory>

The first-sedation-minus-baseline reporting contrast showed a median
paired increase of $+1.70$ ($d_z=+1.15$, bootstrap 95% CI $[0.82, 1.69]$; exact two-sided sign
test $p=4.0 times 10^(-4)$; Wilcoxon $p=1.9 times 10^(-5)$; @tab-occupancy). Later protocol
sedation minus baseline was larger still (median $Delta=+5.92$, $d_z=+1.12$, 20/20 increase).
Recovery remained above baseline (median $Delta=+1.34$, $d_z=+0.45$, 19/20 increase).

#figure(
  kind: table,
  clean-table(
    columns: (2.1fr, 0.6fr, 0.9fr, 0.8fr, 0.8fr, 0.9fr),
    align: (left, center, center, center, center, center),
    inset: 5pt,
    table.header([*Contrast*], [*$n$*], [*$Delta$ med*], [*$d_z$*], [*n+/n−*], [*sign $p$*]),
    [First sedation − baseline (reporting contrast)], [20], [$+1.70$], [$+1.15$], [18/2], [$4.0 times 10^(-4)$],
    [Later sedation − baseline], [20], [$+5.92$], [$+1.12$], [20/0], [$1.9 times 10^(-6)$],
    [Recovery − baseline], [20], [$+1.34$], [$+0.45$], [19/1], [$4.0 times 10^(-5)$],
  ),
  caption: [Within-subject occupancy contrasts versus pre-drug baseline. $d_z$ is paired Cohen's
  $d$. Sign tests are exact two-sided binomial tests on non-zero differences. Bootstrap $n=10 thin 000$,
  seed 20260920. The first-sedation contrast is an ordered reporting contrast; all $p$-values are
  descriptive/exploratory and no confirmatory primary endpoint was locked. Source:
  `results/v1_occupancy_20260921/occupancy_contrasts.csv`.],
) <tab-occupancy>

== R2: Centre shift and feature composition accompany the radial displacement <sec:r2>

The PR-01 geometric dissection was specified before execution within a new post-hoc branch and
reused the frozen feature frame and eligibility mask. At first sedation, phase-cloud centre
displacement increased by a median 2.60 ($d_z=1.83$, bootstrap 95% CI $[1.55, 2.41]$), while
within-phase dispersion increased by 0.477 ($d_z=0.585$, 95% CI $[0.177, 1.15]$). Thus the
radial result contains a strong measured-chart centre shift and some broadening; it does not by
itself identify a latent-state relocation. Median baseline-standardised feature shifts show a
prominent beta/alpha and gamma component, alongside the other features (@fig-features).

#figure(
  image("figures/pr01/fig2_feature_phase_heatmap.png", width: 90%),
  caption: [Eight-feature composition of the measured-chart displacement. Each cell is the cohort
  median of participant-specific phase medians in the frozen baseline robust-$z$ frame. This is a
  descriptive physiological decomposition, not a feature-selection analysis. Source:
  `results/v1_pr01_geometric_20260922_final2/feature_phase_cohort_medians.csv`.],
) <fig-features>

== R3: Matched-state accessibility cannot currently be tested <sec:r3>

Radial displacement asks where the trajectory sits. NDT-C3 asks whether nominated local one-step
speed and spread summaries differ at a matched present state. In the same baseline-fixed chart, greedy one-to-one Euclidean matching
with a leave-one-out nearest-neighbour caliper yielded $>=20$ matched pairs in only 7 of 20
participants (@fig-match). Several participants had 0–4 pairs. The reporting gate of 10
adequately matched participants was therefore not met, and the matched speed/spread family is
NOT_TESTABLE rather than negative. As a support diagnostic only, 0.5x, 1x, 1.5x, and 2x the
frozen caliper yielded 0/20, 7/20, 11/20, and 14/20 participants with $>=20$ pairs (S2). This
does not change the primary gate or make wider-caliper pairs a matched-state result.

Where pairs existed, matched occupancy was similar (2.11 versus 2.16, $d_z=0.25$), as required
for a location-matched comparison. Matched increment speed and spread on those seven
participants were near zero and underpowered (Holm $p=1$). Unmatched increment speed and spread
in this baseline-fixed frame did not reproduce the local-chart contraction seen in a discovery
screen (S2). Local-chart matching, which treats recording-local coordinates as if they were the
same physical state across phases, is not transported here: exported `features_robust_z` is
centred at zero in every recording, so occupancy is invisible in that chart (S1).

#figure(
  image("figures/occupancy/fig3_c3_match_collapse.png", width: 95%),
  caption: [Common-support collapse for the matched-state test. Bars are the number of
  caliper-matched pairs at first protocol sedation versus baseline. Green: $>=20$ pairs
  (included); purple: below the pair gate. Only 7/20 participants are testable; the subject-level
  gate of $n=10$ is not lowered. Source: `results/v1_occupancy_20260921/c3_anchor_match_support.csv`.],
) <fig-match>

== R4: Exploratory association with behavioural responsiveness <sec:r4>

Behavioural labels were assigned from hit counts only, before occupancy was joined. An exact
binomial 95% Clopper–Pearson interval @clopper1934binomial on $k\/40$ at later protocol sedation
versus baseline classified a participant as LOR-impaired if the moderate interval lay entirely
below baseline, otherwise responsive. This recovered 7 impaired and 13 responsive participants,
matching Chennu et al. All twenty recordings at later protocol sedation share the same protocol
phase; only seven meet the behavioural rule. The package alias that names protocol 3
`unresponsive` would have labelled 20/20. All seven impaired participants had recovery intervals
that overlapped baseline (ROR returned 7 / not returned 0), so occupancy cannot be compared
between returned and not-returned.

The exploratory occupancy–LOR contrast — later-sedation occupancy $Delta$ in impaired versus
responsive participants — is NOT_TESTABLE because the impaired arm has $n=7<10$
(@tab-lor). The point estimate is not evidence for a larger relocation in the impaired group
(median $Delta$ 5.13 versus 7.34; Cohen's $d=+0.03$; Mann–Whitney $p=0.76$). The testable
$n=20$ association between occupancy and hit count at later sedation also supplied no evidence
of a monotonic association (Spearman $rho=-0.08$, $p=0.73$, bootstrap 95% CI $[-0.53, 0.39]$;
@fig-hits), but this exploratory estimate
does not establish that an association is absent. Large occupancy occurs with and without
impairment: sub-018 has occupancy 28.6 with 39/40 correct; sub-007 has occupancy 26.4 with 6/40
correct.

Plasma concentration at later sedation differed between groups (median 1149 versus 800
$mu$g/L, $d=1.22$, Mann–Whitney $p=0.096$) but also remains NOT_TESTABLE. This descriptive
contrast is reported as context and is not used as evidence for an occupancy/behavioural
dissociation; the source paper separately described distinctions between drug exposure and
responsiveness @chennu2016propofol.

#figure(
  image("figures/occupancy/figS_occupancy_vs_hits.png", width: 82%),
  caption: [Baseline-referenced radial displacement versus correct responses at later sedation.
  Colour is the occupancy-blind LOR split. The broad bootstrap interval for Spearman $rho$
  reinforces that this exploratory sample does not establish absence of association. Source:
  `results/v1_lor_20260921/lor_occupancy_joined.csv` and
  `results/v1_pr01_geometric_20260922_final2/behaviour_association_uncertainty.csv`.],
) <fig-hits>

#figure(
  kind: table,
  clean-table(
    columns: (1.55fr, 0.45fr, 0.45fr, 0.7fr, 0.55fr, 0.6fr, 1fr),
    align: (left, center, center, center, center, center, center),
    inset: 4.5pt,
    table.header([*Contrast*], [*$n_"LOR"$*], [*$n_"resp"$*], [*$Delta$ med*], [*$d$*], [*MW $p$*], [*Status*]),
    [Later − baseline], [7], [13], [$-2.21$], [$+0.03$], [0.76], [NOT_TESTABLE],
    [First − baseline], [7], [13], [$+1.60$], [0.68], [0.27], [NOT_TESTABLE],
    [Recovery − baseline], [7], [13], [$+0.97$], [0.68], [0.49], [NOT_TESTABLE],
    [Concentration (later)], [7], [13], [$+349$], [1.22], [0.096], [NOT_TESTABLE],
  ),
  caption: [Occupancy-blind LOR split joined to frozen occupancy. $Delta$ med is LOR-impaired
  minus responsive. Group tests require $>=10$ per arm. Spearman occupancy versus $k$ at later
  sedation: $rho=-0.08$, $p=0.73$, $n=20$. Source: `results/v1_lor_20260921/lor_contrasts.csv`.],
) <tab-lor>

#block(breakable: false)[
  #netn-box(title: [Dissociation finding])[
    Propofol produced a large baseline-referenced relocation of neural spectral state that
    increased across protocol sedation phases and partially reversed during recovery. In this
    exploratory cohort, the available data provided no evidence of a monotonic association with
    behavioural loss of responsiveness, while the group contrast remained NOT_TESTABLE.
  ]
]

= Discussion <sec:discussion>

== Two separations

The evidence supports two separations that are easy to collapse in sedation research and in
dynamical theories of neural state.

The first is that drug/protocol state relocation is not the same as behavioural
unresponsiveness. Occupancy moves strongly with protocol phase. At the later protocol phase,
where the original study classified drowsy versus responsive participants, the exploratory point
estimate showed no monotonic association with hit count and the group contrast was not testable.
These results provide no evidence of a simple responsiveness marker in this cohort, but they do
not establish that the scalar is independent of behavioural impairment.

The second is that state relocation is not a demonstrated change in dynamical accessibility.
NDT distinguishes present-state geometry from the conditional future law built on top of it
@langell2025ndt. Occupancy answers “where is the measured system?”. Matched-state increment
speed and spread would answer “does the one-step law differ at a comparable $z$?”. The second
question is presently unaskable for most participants because common support collapses
(@fig-match). Treating that collapse as a negative C3 result would confuse a sampling failure
with a null law.

== What the occupancy result can and cannot say about responsiveness

Occupancy was never preregistered as a consciousness marker. The LOR arm is under the $n=10$
group gate, behavioural hit count is only one operational endpoint, and all seven impaired
participants recovered behaviourally, so return-of-responsiveness occupancy cannot be tested.
The defensible statement is limited: this exploratory dataset provides no evidence of a monotonic
association between state displacement and the selected LOR labels, while the group contrast is
underpowered. It is not a verdict on whether some other chart, feature set, or behavioural
criterion would couple to impairment.

The concentration contrast is also NOT_TESTABLE and is retained only as descriptive context. It
does not validate an occupancy/behavioural dissociation or protect against interpreting occupancy
as “how anesthetized the brain is.”

== Measurement charts are not interchangeable

A discovery screen on exported recording-local coordinates found moderate reductions in
local-chart drift and diffusion amplitude at first sedation, with no FDR-surviving tests and
with Jacobian spectral abscissa remaining weak (S2). Those quantities live in a chart that is
re-centred in every recording, so they cannot see occupancy. Once the frame is fixed to
baseline, the dominant phenomenon is relocation, and unmatched increment contraction does not
survive. This is a measurement-boundary result as much as a propofol result: dynamical scalars
inherit the validity limits of the chart used to estimate them.

Within this post-hoc robustness branch, the sensitivity plan was specified before execution and
kept the same participant-level
eligibility mask and evaluated the full eight-feature radius, each leave-one-feature-out radius,
and two baseline-only scale alternatives (sample SD and normalised IQR). All 11 variants retained
$n=20$ paired participants at first sedation; the median paired difference ranged from $1.295$ to
$1.757$ and $d_z$ from $1.049$ to $1.228$. The scale alternatives gave $d_z=1.166$ and $1.171$.
Feature shares were decomposed descriptively, with beta/alpha ratio and gamma contributing the
largest average squared-radius shares (18.1% and 16.6%). This supports computational stability of
the frozen scalar under these bounded choices, not biological robustness or confirmatory validity.

The PR-01 branch further separates centre shift from within-phase dispersion and applies a 10%
baseline-covariance shrinkage whitening sensitivity. The first-sedation whitened radial
displacement remained large ($d_z=1.21$, 95% CI $[0.91, 1.76]$). These checks reduce concern that
the result is only marginal-scale weighting or only cloud broadening, but remain exploratory
properties of this eight-feature chart rather than a physiological or clinical confirmation.

== Limitations

The analysis is exploratory. Baseline-referenced radial displacement (legacy variable name:
occupancy) was promoted after unmatched occupancy at first sedation
and recovery had already been seen; later-sedation occupancy is an ordered secondary on that
promoted scalar, not an independent confirmation. Independent review of analysis code (G3) and a
confirmatory lock (G4) were not completed. The sample is 20 healthy volunteers from a single
published cohort; the LOR arm is 7. Occupancy uses eight spectral/complexity features, not the
exported three-dimensional MNPS coordinate, and windows are approximately 8 s with a 4 s step.
The bounded robustness branch decomposed the Euclidean radius and tested leave-one-feature-out,
sample-SD, and normalised-IQR alternatives while preserving the frozen eligibility mask. These
results support computational stability for the tested choices, but do not establish robustness
to other feature sets, preprocessing, cohorts, or biological interpretations. The branch remains
post-hoc and exploratory; independent code review and confirmatory locking are still outstanding.
Plasma concentration is a sparse protocol-phase measurement, not a continuous effect-site
series. No claim is made about subjective experience, identified Itô operators, or clinical
depth-of-anaesthesia monitoring.

== Conclusion

In this baseline-fixed spectral chart, propofol increases measured baseline-referenced radial
displacement in an
ordered protocol-phase trajectory with incomplete recovery. That relocation is large and broadly
consistent across participants. In this exploratory cohort, the available data provided no
evidence that occupancy is a monotonic marker of behavioural loss of responsiveness, but the
underpowered group comparison and post-hoc selection do not establish the absence of an
association. The relocation is strong enough that a matched-state test of changed accessibility
is not currently possible.
The stronger NDT question — whether the future law changes at matched present state — remains
open because the relevant counterfactual is inadequately sampled, not because it has been shown
to be null.

= Methods <sec:methods>

== Dataset and labels

We re-analysed the Cambridge propofol sedation resting-state EEG of 20 healthy adults, four
protocol phases per person, originally reported by Chennu et al. @chennu2016propofol
@chennu2016data. Each phase has a high-density EEG recording together with plasma propofol
concentration, mean reaction time, and the number of correct responses out of 40 auditory
buzz/noise trials. Protocol phase was taken from `datainfo.mat` column 2 (1 = pre-drug baseline,
2 = first protocol sedation / mild, 3 = later protocol sedation / moderate, 4 = recovery). Join
keys were original Cambridge filename keys (subject + acquisition/run), not FieldTrip-style
`run-1..4` order. Missing labels stayed missing. Later protocol sedation was not treated as
unresponsiveness.

== Measurement export

Analyses consume a frozen NeuralManifoldDynamics HDF5 export
(`neuralmanifolddynamics_Sedation-RestingState_20260918_075713`; 80/80 files readable). Primary
exported coordinates are `coords_3d_subject_anchored` with ComBat disabled; confirmatory
amplitude claims on that chart remain gated. Feature windows are nominally 8 s with a 4 s step.
The occupancy analysis does not use the exported MNPS coordinate as its state; it uses eight
MNPS-used `features_raw` columns: delta, theta, alpha, beta, and gamma power, alpha/theta and
beta/alpha ratios, and sample entropy.

== Baseline-referenced radial-displacement scalar

For each participant, all baseline rows with finite values in all eight features define a robust
centre (column median) and scale ($1.4826 times$ median absolute deviation). This scaling step is
separate from one-step eligibility. Scales that are non-finite or $<=10^(-8)$ are set to invalid
(`NaN`); no floor value is substituted or clamped. Later-phase rows are mapped into that frame,

$ z_(t,j) = (x_(t,j) - m_j^"base") / s_j^"base", $ <eq:z>

and baseline-referenced radial displacement (legacy analysis variable ``occupancy'') is the median Euclidean radius of eligible one-step source windows,

$ "occupancy" = op("median")_t {norm(z_t)_2 : t "eligible"}. $ <eq:occ>

Eligibility follows the one-step source mask used for increment matching (finite features,
observed $Delta t$ in $[3.8, 4.2]$ s). Occupancy is unmatched: it summarises the whole eligible
cloud, not the matched subset.

== Matched-state rule

Within participant, later-phase eligible windows were paired greedily one-to-one to baseline
windows by Euclidean distance in $z$, with caliper equal to the median baseline leave-one-out
nearest-neighbour distance. A participant was included if at least 20 pairs were obtained. The
cohort-level test required at least 10 included participants; that gate was not lowered.
C3 outcomes were matched increment speed and spread. Occupancy of matched pairs was a
location-match QC, not a C3 outcome.

== LOR/ROR labels

Hit count $k$ out of $n=40$ was converted to an exact binomial 95% Clopper–Pearson interval
@clopper1934binomial at baseline and at later protocol sedation. A participant was LOR-impaired
if the later interval lay entirely below the baseline interval, otherwise responsive
@chennu2016propofol. Among impaired participants, recovery was returned if the recovery interval
overlapped baseline. Labels were assigned from $k$ only, then joined to frozen occupancy.

== Statistics

The initially selected first-sedation-minus-baseline contrast is retained as an ordered reporting
contrast, not a confirmatory primary endpoint. It was tested descriptively with an exact two-sided
sign test on non-zero differences and reported with a Wilcoxon signed-rank $p$ @wilcoxon1945,
paired Cohen's $d_z$ @cohen1988statistical, and a percentile bootstrap 95% CI (10 000 resamples
of participants, seed 20260920). Later sedation and recovery were ordered descriptive contrasts
on the same scalar. LOR group contrasts used two-sided Mann–Whitney
tests @mannwhitney1947 and two-sample Cohen's $d$, with a reporting gate of $>=10$ participants
per arm. Occupancy versus hit count used Spearman $rho$ @spearman1904. Discovery screens of
exported local-chart metrics used Holm adjustment @holm1979 on the two original H1/H2 sign tests
and Benjamini–Hochberg FDR @benjamini1995fdr across a frozen Wilcoxon family; no FDR survivor is
interpreted as a primary result (S2).

== Exploratory status

A dated preregistration draft specified G0–G4 gates before confirmatory condition contrasts.
G0–G2 (inventory, labels, support) were closed on the frozen export. G3 independent code review
and G4 lock were not completed. All inferential numbers in this article are therefore exploratory
and all reported $p$-values are descriptive. Occupancy promotion relative to the 2026-09-20 draft
is post-hoc for first-sedation and recovery values; later-sedation occupancy was computed after
that promotion on the same scalar. The first-sedation contrast is therefore a reporting contrast
rather than a confirmatory primary endpoint.

= Acknowledgements

We thank the original investigators, participants, and data stewards of the Cambridge propofol
sedation EEG study. This work emerged through structured correspondence among human and AI
collaborators; large language models from OpenAI, Anthropic, Google, and xAI assisted in
literature synthesis, drafting, and editorial refinement.

#bibliography("references.bib", style: "apa")
