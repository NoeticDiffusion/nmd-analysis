// Reality from Noise: Same Place, Different Futures — Part 3
// The clinical atlas as bounded probes of C1 / C2 / C3
// Author: Robin Langell, 2026

#import "template.typ": essay-template

#show: doc => essay-template(
  title: text(hyphenate: false)[Reality from Noise:\ Same Place, Different Futures],
  subtitle: [Part 3: When the Horizon Narrows],
  series-description: [An illustrated research essay on Noetic Diffusion Theory],
  author: [Robin Langell],
  date: [2026],
  doc,
)

= Prelude: Does the Future-Law Survive Clinical Data?

Parts 1 and 2 built a disciplined claim. A useful description of a neural state includes not only where it sits on a chart, but what can still happen from there, and what processes change those possibilities. The pin is a map. Texture, nudge, and short-horizon predictive spread are different questions. Rhythm, body, and history are candidate controls, not extra definitions of the theory @langell2026ndt_current.

These studies ask what the framework adds in clinical and altered-state contexts, under bounded measurement and inference contracts.

The clinical question is the same as the theoretical one:

- *C1.* Is reduced present chart state insufficient to determine the latent future law? Similar stage labels or group centroids alone do not test this.
- *C2.* Do chart-conditional future-law summaries add reproducible held-out information beyond current location and standard static or spectral summaries?
- *C3.* Do nominated controls change specified future-law features at matched chart state beyond ordinary covariates? A difference between conditions alone does not establish this.

Each portrait is tied to a cohort, a measurement contract, and auditable exports. Where the evidence is strong, we say so. Where it is cohort-specific, we say that too. Geometry is not on trial as a bedside oracle. The question is simpler: *does it see a different layer?*

*Reading route and figures.* Each portrait starts with three sentences: what changed, what it does not mean, and a proposed next test. Technical details follow. Here, *short-horizon predictive spread* names model-implied covariance spread; source endpoint names retain reachability terminology. Watercolor terrain is metaphor only, and captions distinguish schematics from empirical summaries and model estimates.

#figure(
  image("figures/ndt_v.1/fig_p3_comparison_designs_v2.png", width: 100%),
  caption: [Status: Schematic. Three comparison designs. Group differences, within-person changes and a matched-state control test answer different questions. The right panel depicts a hypothesis to test, not an established control effect; matching the pin alone does not remove confounding. Terrain and ellipses are illustrative metaphors.],
)

#pagebreak()
#[
#set par(leading: 0.5em)
= Sleep as a Clinical Instrument

Sleep is the sharpest methodological test in this essay, and it is the right place to start. Sleep is a physiological state rather than a disease condition. It is a repeated change in recorded state without a change of person, while the measurement contract stays visible. That makes it useful for asking how a chart-level quantity varies with a sleep label, and what remains only a candidate interpretation.

*Take-home.* Spindle timing was associated with a change in one chart coordinate; separate sleep-stage analyses reported differences in local geometry and model-derived predictive spread. These associations do not identify a latent future law, consciousness level, or causal sleep mechanism. Next, preregister an independently replicated timing and stage study that tests incremental predictive value, estimator validity, and matched measurement contracts.

*Technical detail*

#heading(level: 3, numbering: none)[Spindles: event-locked reconfiguration, not just sigma power]

Within N2, do detected spindle windows coincide with a chart change beyond their elevated band power? The cited event detector used a 12–15 Hz sigma band. The current spindle report separates two estimands that answer different questions. A timing contrast compares an event window with that same spindle's far pre-event baseline. A specificity contrast compares the event with matched non-spindle N2 windows. The second can be driven by a pre-event difference between the matched pools, so it cannot stand in for the first @langell2026_rvc_sleep_revision.

Under a subject-weighted timing protocol, the stratified $d_n$ coordinate rose in both ANPHY (27 healthy adults; $Delta = +0.106$, $q = 0.009$) and BOAS / OpenNeuro ds005555 ($Delta = +0.165$, $q = 0.011$). These are two within-spindle timing results on different overnight PSG/EEG datasets, not a claim that every endpoint moves. RichSleep's same-estimand test was inconclusive ($q = 0.72$, 160 paired events across 24 people), so it does not provide a third timing confirmation @langell2026_rvc_sleep_revision.

The broader event-versus-matched-control result was positive for many endpoints, but the $d_n$ sign differed between ANPHY and BOAS because their pre-event baselines related differently to the matched controls. The current report therefore treats that result as broad, baseline-sensitive specificity evidence. Reachability and Jacobian endpoints were not the primary spindle objects, and no classifier gain is used here to claim that geometry improves spindle detection.

*What this is:* A detector-defined spindle window coincides with a reproducible, subject-level shift in one stratified chart coordinate relative to its own pre-event baseline. It is chart-level state reconfiguration. It is not causal denoising, memory writing, thalamic or TRN identification, or proof that an event changes a latent future law. A later RichSleep analysis found no detectable spindle-strength moderation of the alignment–geometry association; its phase-resolved and tonic anchor tests were null at their available power @langell2026_richsleep_carriers_revision.


#heading(level: 3, numbering: none)[Full-cohort sleep geometry: descriptive stage associations]

The newer full-cohort ds005555 analysis asks a narrower question than a consciousness or reachability test: how do the existing Jacobian and diffusion measurement families differ between recorded labels under continuous 30-second processing? It covers 128 PSG nights from 100 people, not 128 independent participants. The local participant table, rather than the dataset README, governs this count; repeated nights are reduced to one person-level summary before cohort aggregation @langell2026_sleep_families_revision.

The fixed N2-minus-Wake contrast is descriptive. Total conditional increment-covariance magnitude was lower in N2 for 97 of 100 people, with median $Delta D_"total" = -0.033018$. Numerical abscissa and reactivity-gap contrasts had negative medians in both 3D and 9D. Effective diffusion dimension and concentration were heterogeneous: their between-person quartile intervals crossed zero. Missing 9D outputs in two recordings remained missing, and no values were imputed @langell2026_sleep_families_revision.

An earlier ANPHY report in 27 healthy adults used a precommitted local-reachability endpoint and found strong Wake-, REM- and N2-versus-N3 contrasts (Cohen's $d_z = 2.265$, $1.923$, and $2.265$, respectively; all $q = 0.0005$). Conventional comparators reached leave-one-subject-out stage-discrimination ceiling in that dataset, while a small leave-one-out ridge analysis reconstructed subject-level reachability contrasts only partially ($R^2 = 0.20$, $-0.43$, and $0.27$). The appropriate claim is that the reachability summary was not a near-lossless surrogate for that compact comparator panel under that contract. It does not show that spectra cannot reconstruct a latent future law, and it does not make the stage contrast a C1 test @langell2026_sleep_reachability.

Both sleep articles have limits that matter here. The full-cohort report uses recording-relative coordinates, a recording-global reference, and estimators whose effective temporal support is not fully known. It reports label associations without p-values, clinical qualification, or independent biological mechanism. The ANPHY reachability result is a separate, older cohort and endpoint. Together they motivate a nonredundancy question; they do not establish that N3 is a universal state with reduced short-horizon predictive spread or that a measured reachability ellipsoid is the latent future distribution.

#heading(level: 3, numbering: none)[Three regimes: reduced capacity is a family]

If N3, propofol, and seizures all reduce estimated short-horizon predictive spread, is reduced spread unconsciousness?

No. A separate comparative report across ANPHY sleep ($n=27$), propofol ($n=20$), and epilepsy interictal versus ictal ($n=55$) shows a family resemblance in its exported capacity summaries, not a single state @langell2026_reduced_capacity. The newer reachability-cone battery uses a stricter validity contract and treats its propofol contraction rows as diagnostic only; these are distinct exports @langell2026_reachability_current.

In the comparative report, all three show a lower tube-capacity summary, but the objects are not one universally validated endpoint. They dissociate on transport-innovation and capture:

- *N3:* Low capacity, *innovation-dominated*. Lower capture than wake in the source contrast (CaptureGate $d_C = 1.812$, $q < 0.001$). This does not identify a restorative mechanism.
- *Propofol (this dose range):* The comparative report describes capacity suppression ($d_C = -0.679$, $q = 0.035$) without clear lock-in. It is a descriptive pharmacological contrast here; the refreshed cone report fails its local validity gate and does not promote propofol as positive reachability evidence.
- *Epilepsy ictal:* Capacity suppressed ($d_C = -1.580$, $q = 0.001$) *and* capture elevated (Attractor-Capture Index $d_C = 0.830$; canalization-feature-capture $d_C = 1.184$; both $q = 0.001$). Higher capture-related summaries under the source definitions.

Adding geometry to conventional features improved AUC by $0.138$ for propofol and $0.148$ for epilepsy in the cited comparative report. Those are report-specific cross-validated classification increments, not evidence of a universal reachability estimator. Sleep was already at spectral AUC = 1.000 in the ANPHY classifier check, so an additive gain there was ceiling-limited rather than a test of whether reachability was redundant.

Keep capacity, capture and lock-in distinct: reduced predictive spread across different conditions does not define a consciousness meter.

]

#pagebreak()
= Depression — Symptom-Linked Chart Differences

*Take-home.* One ds003478 cohort showed differences in the shape of model-implied short-horizon predictive spread and in 9D Jacobian rotational power, with the latter weakening after centroid adjustment. These article-local associations do not identify thought content, establish a depression diagnosis, or support individual treatment decisions. Next, test preregistered longitudinal symptom and treatment trajectories with external validation and matched-state incremental prediction.

*Technical detail*

#heading(level: 3, numbering: none)[Cohort and chart contrast]

The cited study measures EEG geometry and symptom scores, not the trajectory of a thought. A young-adult cohort scored by Beck Depression Inventory supplies the comparison @langell2026_depressive_geometry.

*Dataset:* ds003478, 121 young adults, BDI 0–63. Cohort-anchored coordinates, low-symptom group as reference, BH-FDR across the feature set.

*What does not cleanly separate:* On the coarsest 3D summary, the prespecified low-versus-high contrast (BDI 0–13 versus 20–63) is only modest. Intuition says depression should mean less of everything. At the pin, that is not strongly confirmed. This is a chart contrast, not a C1 test of latent future-law insufficiency at matched reduced chart state.

*What does separate:*

- Reachability tube log-eigenvalue variance: $d = -0.678$, $q = 0.00296$. This is a change in the shape of model-implied covariance spread, not a uniform collapse of every reachable state.
- 9D Jacobian rotational power: $d = 0.569$, $q = 0.00317$. Local activity still moves, but the chart-level flow is more rotational. This result does not identify thought content or a clinical process.
- At the low-to-modest boundary (BDI 0–13 vs 14–19): reachability contrast $d = -0.831$, $q = 7.46 times 10^(-6)$. The strongest local contrast is at that boundary, not necessarily at the extreme.

*Reading:* The chart retains movement while the local geometry differs. The rotational result is a provisional geometric association: after 9D centroid adjustment, it weakens (raw $p = 0.108$, $q = 0.153$).

*Bound:* One resting-state cohort, one BDI symptom dimension, no longitudinal tracking, and no diagnostic comparison. BDI burden is not a confirmed major-depression diagnosis and these rows support no individual diagnosis or treatment decision. The newer reachability-cone battery does not promote stable ds003478 cone rows, so the effects above remain article-local geometry associations under their stated export. This is a measurable chart association at this contract, in this sample.

= First-Episode Psychosis — Cohort- and Medication-Stratified Geometry

*Take-home.* Two FEP cohorts showed subgroup differences in static $m$-family displacement or trajectory drift, with the carrying layer differing by cohort and medication stratum. These observational rows do not establish a psychosis-specific signature in short-horizon predictive spread or a medication effect. Next, replicate medication-aware, clinically anchored longitudinal contrasts with preregistered external validation and matched-state prediction.

*Technical detail*

#heading(level: 3, numbering: none)[Cohorts and observed contrasts]

The psychosis cohorts ask whether observed group differences appear in the same geometric layer @langell2026_psychosis_fep.

*Datasets:* ds003944 (32 HC, 19 unmedicated FEP, 31 medicated FEP); ds003947 (30 HC, 8 unmedicated FEP, 23 medicated FEP). Shared cohort-anchored frame, BH-FDR.

*The signal appears under medication-stratified observational contrasts:*

- ds003944, medicated FEP: global $m$ displacement $d_C = 0.881$ ($q = 0.016$), $m_"median"$ $d_C = 0.865$ ($q = 0.009$), $m_o$ mean $d_C = 0.814$ ($q = 0.027$). An $m$-family chart difference in the medicated subgroup.
- ds003947, unmedicated FEP: trajectory drift $d_C = -1.385$ ($q = 0.040$). Dynamic rather than positional. Small unmedicated subgroup ($n = 8$): cohort-local until replicated.

*Medication-stratified contrast:* In ds003944, medicated vs unmedicated FEP separated on $m_"std"$ ($d_C = 0.972$, $q = 0.018$). "Medicated FEP" and "unmedicated FEP" are different observed groups, but this observational comparison cannot separate medication exposure from illness severity, selection, or other group differences. It is not a C3 control test: a group contrast does not establish that medication changed the conditional future law.

*What does not replicate as one fingerprint:* The layer shifts. ds003944's strongest corrected effect is static/stratified $m$ for *medicated* FEP; ds003947's is trajectory dynamics for *unmedicated* FEP.

*Conventional EEG:* Some separation is also visible in simpler summaries (beta/alpha in ds003944 medicated FEP, $d_C = 0.768$; alpha power for unmedicated FEP in ds003947, $d_C = -0.817$). The shared-reference chart is not automatically superior. Its value is organizational: one frame makes medication-stratified geometry readable across pin, trajectory, and local-dynamical layers at once.

*Pooled sensitivity:* Pooling all FEP regardless of medication let ds003944 survive ($m_"mean"$ $d_C = 0.688$, $q = 0.022$) and *weakened* ds003947 ($m_"delta"$ $q$ from $0.040$ to $0.250$). Pooling attenuates a tested stratification; it is a sensitivity result, not evidence that a contextual control changed the law.

*Exploratory phenotype:* Higher hallucination burden (SAPS Q7) in ds003944 linked most clearly to $e$-weighted displacement; total BPRS to first-order and coupling effects. Hypothesis-generating, not biomarkers. The eventual clinical question is which layer differs *here, now*—a question requiring prospective, clinically anchored validation.

The newer reachability-cone battery likewise reports no FDR-stable ds003947 reachability signature after subject aggregation. That negative result narrows the claim: the article's $m$- and trajectory-family rows do not establish a psychosis-specific cone or a universal future-law difference @langell2026_reachability_current.

#figure(
  image("figures/clinical/psychosis_m_axis_focus.svg", width: 90%),
  caption: [Status: Mixed empirical summaries. First-episode psychosis, $m$-axis focus. Left: ds003944, static $m$-family displacement in medicated FEP. Right: ds003947, trajectory $m$-dynamics in unmedicated FEP. Different features separate the observed subgroups in the two cohorts. This is not replication of one biomarker or identification of a medication effect.],
)

#pagebreak()
= Parkinson Disease — Disease, Medication, and Task Frames

*Take-home.* PD versus HC geometry differed in cohort-anchored disease and walking contrasts, while the paired ON/OFF branch retained one exploratory temporal-region Jacobian row. These frame-specific associations do not show treatment efficacy, anatomical causation, or restoration of an individual's future-law summary. Next, preregister a replicated longitudinal study that compares rest, walking, and medication within person while testing clinical prediction.

*Technical detail*

Parkinson is the cleanest demonstration that *the inference question determines the measurement frame*. "Is this brain different from healthy?" and "does dopamine change *this* patient's geometry?" target different estimands and should be analyzed separately.

#heading(level: 3, numbering: none)[Disease state versus pharmacological effect]

The ON/OFF auditory oddball study asks both questions on the same patients, processed in two frames @langell2026_parkinson_onoff.

*Disease (cohort-anchored, HC as anchor):* 47 corrected rows were retained in total: 46 disease-state rows and 1 paired OFF/ON row. In the disease-state rows, PD OFF showed lower eyes-closed trajectory speed ($d_C = -1.212$); in PD ON, the global 9D Jacobian MDR was elevated ($d_C = 1.167$). MDR here is a Jacobian-change ratio, not a modal diffusion rate. The row inventory shows broad disease-state contrasts under this export; it is not itself an effect-size ranking.

*Pharmacology (subject-anchored, ON minus OFF):* one temporal-region 3D Jacobian eigenvalue-anisotropy row survived ($d_z = -0.483$, $q = 0.038$). Temporal names the EEG region. A retained paired association does not by itself identify the mechanism of a medication effect.

The export contains many more disease-state rows than paired ON/OFF rows (46 versus 1), but row counts are not a strength comparison. The paired branch remains hypothesis-generating, with no preregistered primary endpoint or external validation. Matching a control centroid does not establish restoration of an individual's future-law summary; this is the measurement-contract lesson from Part 2 applied to a pharmacological contrast.

These geometry results do not assess clinical treatment efficacy. They ask what changed in a particular measurement frame.

#heading(level: 3, numbering: none)[Walking: demand reveals what rest conceals]

Can geometry during walking separate PD from controls beyond rest? @langell2026_parkinson_walking

*Dataset:* 277 runs, 116 PD, 28 HC; rest, treadmill, obstacle, dual-task. Cohort-anchored, HC reference.

*Walking-state separation:* PD walking vs HC walking on $d_n$: $d_C = 0.766$. The walking contrast is retained under its cohort-anchored contract; the mixed-contract article does not establish universal superiority over an equivalent rest contrast. Motor demand may expose disease-related texture that rest obscures.

*Paired walk-vs-rest within PD:* $m_a$-IQR ($d_z = 0.472$, $q = 6.55 times 10^(-4)$) and $d$-IQR ($d_z = 0.403$, $q = 7.28 times 10^(-4)$). These are within-PD rest-to-walk contrasts; they do not alone establish that PD changes more than controls.

*Clinical associations:* Among PD, walking $d_s$-IQR correlated with age ($rho = -0.377$) and Color Trail Test ($rho = -0.351$). Parietal-occipital $e$-IQR with UPDRS total. Walking geometry was associated with clinical variation.

Part 2's Parkinson lesson was about *frame*: broad disease-state geometry against controls, and a narrow paired medication branch. Walking adds a protocol-dependent observation: task demand may expose a measured layer that rest does not. The same disease can therefore show different measured layers under different protocols. The walking report remains observational, has no conventional EEG sidecar or external replication, and does not identify an anatomical source from regional sensor groups.

#figure(
  image("figures/clinical/parkinson_walking_cohort_focals.svg", width: 90%),
  caption: [Status: Mixed empirical summaries. Parkinson walking, cohort-anchored focals (PD walk vs HC walk). The $d_n$ family carries the clearest between-group signal. Dispersion summaries sharpened the paired within-PD reconfiguration branch.],
)

#pagebreak()
#[
#set par(leading: 0.5em)
= Coma — Recovery-Linked Diffusion Geometry and Its Limits

*Take-home.* Across two internal cohorts, early diffusion organization and bounded summaries of short-horizon predictive spread differed between selected CPC recovery extremes, while local-generator fit passed for few recordings. These group associations do not provide individual prognosis, awareness measurement, or an identified operator. Next, prospectively test trajectory prediction and operator validity across hospitals with sedation and treatment-limitation covariates.

*Technical detail*

Post-cardiac-arrest coma provides an acute clinical test. Standard EEG already carries prognostic information; the newer I-CARE 2.1 report asks whether chart-level diffusion and summaries of short-horizon predictive spread show a bounded recovery-linked association @langell2026_coma_current. This revision postdates the older coma anchor still described in the current theory manuscript; the two exports should not be treated as the same result.

#heading(level: 3, numbering: none)[Two cohorts, explicit gates]

The analysis uses two nonoverlapping cohorts anchored to the first 0–12 h of EEG: a discovery inventory of 161 patients and a confirmatory inventory of 140. The primary-window CPC 1 versus CPC 5 comparisons include 71 versus 70 discovery patients and 70 versus 70 confirmatory patients. The time axis is relative to the EEG monitoring anchor, not to the arrest. Diffusion-family objects were computable for 98.0% of discovery and 97.8% of confirmatory recordings.

*Diffusion geometry:* Local effective diffusion dimensionality and normalized diffusion entropy were higher in CPC 1 than CPC 5 in both cohorts (discovery $d = 0.76$ and $0.58$; confirmatory $d = 0.61$ and $0.48$, respectively). Total diffusion power was not required to differ and was numerically higher in CPC 5, so the result is about organization and distribution rather than a generic amount of activity.

*Reachability companion:* Reachability-cone effective dimensionality at both tested horizons ($h = 1$ and $h = 4$), together with the tube effective-dimension summaries, followed the same CPC1-higher direction in both cohorts. These are chart-level covariance-spread summaries from local models, not observed responses to delivered perturbations. They are not counts of all mental alternatives and do not identify a latent future law.

#figure(
  image("figures/ndt_v.1/fig_p3_coma_association_gate_v2.png", width: 100%),
  caption: [Status: Schematic. The coma report's two evidential outcomes, drawn schematically. Diffusion organization showed a recovery-linked association, while almost all recordings failed the tested local-generator fit gate. Shapes, colors and paths do not encode cohort values or CPC categories. The association does not identify an operator or establish individual prognosis.],
)

#heading(level: 3, numbering: none)[The operator gate remains closed]

Only 22/1815 discovery recordings (1.2%) and 53/1838 confirmatory recordings (2.9%) had any window passing the local-generator fit gate. With so few recordings supporting an identified fit, the report cannot qualify its proposed fraction of locally stable-but-reactive windows, $F_"reactive"$, or identify a local operator. A separate post hoc result using diffusion perpendicular to a smoothed drift estimate remains a lead for a prospectively specified analysis; the originally nominated version did not replicate.

Residual hospital effects on derived metrics remained material ($eta^2 approx 0.11$–$0.18$). Hospital composition was balanced between confirmatory CPC groups, while discovery had residual site imbalance; sedation and withdrawal-of-life-sustaining-therapy covariates were unavailable, and conventional qEEG sidecars were not included. These limits block causal and bedside claims.


*What this is and is not:* A recovery-linked association in an extreme CPC contrast, replicated internally across two cohorts. It is not a viability assay, a CPC substitute, a readout of awareness, or evidence about within-state experience. The safe claim is narrower: under this contract, early chart-level diffusion organization and bounded reachability summaries differ between selected recovery extremes. Whether they predict an individual trajectory, generalize beyond this export, or reflect a modifiable mechanism remains unestablished.

]

#pagebreak()
= Alzheimer Disease and Frontotemporal Dementia — Defined Challenge Contrast

*Take-home.* Under defined photic stimulation, AD and FTD differed from healthy controls on article-local Jacobian and ESB-2 response summaries, while the resting overlap surface was near-null. These challenge contrasts do not establish a causal perturbation effect, a unique AD-versus-FTD signature, or general clinical sensitivity. Next, replicate state-matched photic and other challenge protocols with direct evoked-response validation and prospective clinical outcomes.

*Technical detail*

Resting-state neuroscience can miss condition differences that appear under a defined stimulus. Alzheimer's disease and frontotemporal dementia provide a useful challenge contrast, but the available export does not turn that contrast into a causal perturbation test.

#heading(level: 3, numbering: none)[The rest-state null]

In the cited photic export, the baseline rest branch is near-null on the reported overlap surface. That does not establish that disease has no resting geometry; it says that this comparison and contract provide little separation there @langell2026_alzheimer_photonic. The newer reachability-cone battery likewise leaves refreshed resting dementia reachability weak or unresolved, so the photic result below remains an article-local challenge contrast @langell2026_reachability_current.

#heading(level: 3, numbering: none)[Photic stimulation as a defined challenge]

The protocol presents eyes-open photic stimulation at exact frequencies. Under 20 Hz, the global 9D Jacobian MDR ($"mdr_median"$), a Jacobian-change ratio rather than a modal diffusion rate, separated AD from healthy controls ($d_C = -0.984$, $q = 0.0034$). The effect is a condition contrast on a defined stimulus surface; it does not by itself identify entrainment, a latent structural limit, or a changed future law.

Photic stimulation is a controlled neural challenge, and the geometry of the *response* is the measured surface. Here the study compares different people under that protocol; it is therefore a challenge-style association, not a C3 causal test among matched chart states.

#figure(
  image("figures/clinical/alzheimer_rest_vs_photic.svg", width: 90%),
  caption: [Status: Mixed empirical summaries. Rest versus photic stimulation, AD vs healthy controls. The overlap rest branch is near-null on this surface; under 20 Hz, global 9D Jacobian MDR separates ($d_C = -0.984$, $q = 0.003$). The panel illustrates a bounded challenge contrast, not a causal perturbation result.],
)

#heading(level: 3, numbering: none)[ESB-2 response composite]

ESB-2 is an exploratory article-local composite magnitude derived from baseline-subtracted rest-to-photic changes in posterior reachability and rotational power, expressed relative to a healthy response template. It summarizes deviation from that template on a frozen surface; it is not a canonical NDT state variable @langell2026_alzheimer_esb.

Both disease groups differed from healthy controls on this exploratory composite at 15 Hz (AD $d_C = 0.821$, FTD $d_C = 1.038$; cross-fit values were smaller, $0.676$ and $0.841$). These are group-level magnitudes, not proof that either disorder has a unique deformation pattern. No corrected AD-versus-FTD contrast was established, and the secondary profile-based Photic Resonance Loss (PRL) test remained negative. PRL here is not a phase-locking measurement.

The rest and photic branches also differ in eye state (eyes-closed rest versus eyes-open stimulation), so a simple baseline change mixes disease response with protocol and state differences. There is no direct SSVEP validation in this export. The result motivates replication with state-matched controls; it does not establish that dementia is generally more sensitive to disruption.

Direction still has to be read from axis-wise changes. PRL and hysteresis/recovery terms are secondary and, in current analyses, bounded by state-matching limits. Do not fold ESB-2 into the canonical NDT backbone as if it were a foundational layer. It is an article-local exploratory score on a frozen surface.

#figure(
  image("figures/clinical/alzheimer_esb_group_trajectories.svg", width: 90%),
  caption: [Status: Model estimate. Exploratory ESB-2 rest-to-photic magnitude at 15 Hz. AD and FTD differ from healthy controls on this exact surface (AD $d_C = 0.821$, FTD $d_C = 1.038$). Cross-fit effects attenuate; the panel does not establish distinct network pathology.],
)

Photic stimulation is one candidate challenge. Working-memory load, exercise, or controlled sleep restriction would require their own preregistered contracts. A measured response under challenge may separate groups where resting measurements do not, but sensitivity and clinical value remain to be tested.

#pagebreak()
= The Clinical Atlas — Bounded Claims

== Six domains, six take-homes

The six take-homes state the main route: measured differences occur in different chart or local-dynamics layers, under specific protocols and cohorts. Their numeric evidence, negative results, and qualification boundaries remain in the marked technical-detail sections above. Across domains, short-horizon predictive spread is a model-derived covariance object, and none of these studies establishes an individual clinical decision rule.

== What is missing

- Independent external validation. Most findings are single-cohort or two-cohort internal exports.
- Longitudinal tracking. Cross-section cannot tell whether geometry *changes with* treatment or recovery.
- Closed-loop application. The therapeutic loop has not been closed.
- Clinical pathway integration. Coma, walking, and photic probes would need to be tested against existing decision pathways, not only in research exports.
- Committor identification and finite-amplitude resilience protocols. Named in Part 2. Not computed here as if they were.

== The forward program

First, replication under declared contracts, with compatible references, temporal sampling and validity checks. Version-locking alone does not guarantee cross-dataset comparability.

Second, longitudinal questions. Does depression's rotational summary change with treatment? Does coma geometry predict *trajectory*, not only CPC extreme? Do Parkinson signatures precede clinical deterioration?

Third, perturbation paradigms. The AD/FTD load result suggests challenge-based probes may beat rest across conditions.

Fourth, keep inferential claims distinct; they are not one universal ladder. Association is not mechanism. Chart separation is not latent-state identification. Operator recovery is rarer still. On at least one meso-to-macro recording, coarser association succeeds while EEG-only operator identification fails. Clinical use should inherit that bound.

The measured distinctions are becoming more specific, but their clinical reliability is unresolved. Validation must establish whether any summary predicts an individual trajectory, responds to an intervention, or generalizes across contracts. Until then, the atlas is a research instrument: useful for stating bounded questions and preserving negative evidence, with bedside use unestablished.

#pagebreak()

= References

#context {
  set par(leading: 0.5em)
  bibliography("references.bib")
}

#pagebreak()

== Acknowledgments

This work emerged through structured correspondence among human and AI collaborators; large language models from OpenAI, Anthropic, and Google assisted in literature synthesis, drafting, peer review, and editorial refinement. We also gratefully acknowledge the original investigators, clinical teams, participants, and data stewards who created, curated, and shared the public datasets and metadata that made these analyses possible.

We extend our gratitude to the *OpenNeuro* platform, the *Stanford Center for Reproducible Neuroscience*, and the *Center for Open Science* for the public datasets and infrastructure that made these cohort analyses possible.

= Contact

Robin Langell — hello(at)noeticdiffusion.com

= Licensing

This manuscript provides only a brief licensing summary; full terms are available via the Mychainos multi-layer licensing framework (`https://noeticdiffusion.com/license.html`). Conceptual content: CC BY-SA 4.0. Software: GPLv3. Unified ethical guardrails apply: no coercive, military, or surveillance applications.

= Data and Code Availability

Reference implementations: `https://github.com/NoeticDiffusion` 

The bibliography distinguishes public records from the local working revisions consulted here.
