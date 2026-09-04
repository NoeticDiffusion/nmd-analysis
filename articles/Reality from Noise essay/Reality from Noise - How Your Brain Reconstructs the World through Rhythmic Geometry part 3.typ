// Reality from Noise: How Your Brain Reconstructs the World through Rhythmic Geometry
// A popular science essay on Noetic Diffusion Theory
// Author: Robin Langell, 2025

#import "template.typ": essay-template

#show: doc => essay-template(
  title: [Reality from Noise - Part 3],
  subtitle: [How Your Brain Reconstructs the World through Rhythmic Geometry],
  author: [Robin Langell],
  date: [2025],
  doc,
)
#pagebreak()


#pagebreak()
= Prelude: Where the Theory Meets Suffering

The framework is built. We have the coordinates, the measurement contract, the Jacobian, the embodied anchor. Part 1 showed how the brain reconstructs experience. Part 2 showed how we measure it.

Now comes the harder question: does it survive contact with real suffering?

Theory that cannot be tested against disease is a beautiful garden behind a wall. The clinical studies in this part were designed to climb that wall—not with the ambition of solving psychiatry, but with the more modest goal of determining whether the geometric framework says anything useful, falsifiable, and bounded when it faces conditions where the landscape has genuinely gone wrong.

Each disorder portrait below is tied to a specific cohort, a specific measurement contract, and auditable quantitative outputs. Where the evidence is strong, we say so; where it is bounded or cohort-specific, we say that too. The framework is not on trial. The question is simpler: does it see?

#pagebreak()
= Sleep as a Clinical Instrument

== The Nightly Spindle — Micro-Event as Macro-Signature

Sleep might seem like the least dramatic starting point for a clinical chapter. But it turns out to be the sharpest methodological test the framework has passed to date, and its results have cascading implications for how we interpret clinical states.

The question was surgical: within N2 sleep, do the 12--15 Hz bursts called sleep spindles—familiar from the spectral literature for decades—correspond to measurable changes in neural state-space geometry? Or are they just elevated sigma power, already well-characterized?

In OpenNeuro ds005555 (128 subject sleep recordings), each spindle was isolated as an event, and the geometry of the 5-second window centered on the spindle was compared to two things: the geometry of the pre-spindle baseline, and the geometry of carefully matched non-spindle N2 windows from the same night @langell2026_spindle_windows.

*The pre-spindle baseline comparison* was unambiguous: 115 of 117 QC-pass subjects showed positive MNPS-$d$ shifts during spindles. Event-locked mean $Delta d_"bc" = +0.2164$, Cohen's $d_z = 1.819$, $p = 2.79 times 10^(-42)$. Every spindle-rich window was also examined on stratified 9D subcoordinates—the strongest effects appeared in $d_s$ ($d_z = 1.922$) and $d_n$ ($d_z = 1.772$), the local and network diffusivity channels.

*The matched non-spindle control comparison* was the key specificity test: 114 of 128 subjects positive; event-minus-control $Delta d = +0.2988$; $d_z = 0.900$; $p = 1.16 times 10^(-20)$. Replacing the primary channel with the frontal channel (F3), the effect was even cleaner: $d_z = 1.513$, 119/128 subjects positive.

*What spectral features cannot do:* Standard sigma-band ROC already achieves AUC = 0.953 for spindle detection. Adding the geometry layer raises it to 0.956—a modest $Delta"AUC" = +0.0028$, $p = 0.035$. The geometry is not replacing the spectral signal; it is adding a different layer of information. Where spindles were already clearly identified, geometry adds little. Where the spectral signal is ambiguous—flanks, smaller bursts—geometry begins to diverge from the spectral readout.

*What this means:* Sleep spindles are not merely sigma bursts in the frequency domain. Each spindle is associated with a brief, reproducible shift in the brain's state-space position. The brain moves geometrically during spindles—its local diffusivity coordinates shift, the neural state briefly visits a different neighborhood of MNPS space, and then returns. This is an event-locked reconfiguration, not just a spectral modulation.

This finding matters for sleep medicine and memory research alike. If spindles are reconfiguration events—not just power bursts—then counting their density tells only part of the story. Their geometric character, their timing relative to baseline, and their consistency across the night may all carry additional information.

#figure(
  image("figures/clinical/sleep_spindle_matched_control.svg", width: 90%),
  caption: [
    Sleep spindle specificity test. Each point shows one subject's geometry shift during a spindle window minus a matched non-spindle N2 window. 114 of 128 subjects are positive (right of zero), confirming that spindles produce a geometrically distinct state beyond ordinary N2 sleep. Median $Delta d = +0.2988$, $d_z = 0.900$.
  ],
)

== Deep Sleep and Reachability — What the Landscape Can No Longer Reach

Zooming from micro-events to macro-stages, the ANPHY study asked a complementary question: across canonical sleep stages (Wake, REM, N2, N3), does short-horizon _reachability_ add anything to the already well-characterized spectral profile? @langell2026_anphy

In 27 healthy adults (ANPHY dataset, 83-channel overnight EEG), the answer was clear. Reachability—operationalized as the log-determinant of the short-horizon reachable volume—showed very large effect sizes separating all stages from deep sleep (N3):

- Wake vs N3: $Delta = 6.158$, $d_z = 2.265$, $q = 0.0005$
- REM vs N3: $Delta = 4.079$, $d_z = 1.923$, $q = 0.0005$
- N2 vs N3: $Delta = 3.132$, $d_z = 2.265$, $q = 0.0005$

The conventional spectral features—delta, theta, alpha, entropy—already achieve 100% accuracy in stage classification on this dataset. There is no room for reachability to improve that ceiling. But the question was different: can spectral features _predict_ the magnitude of the reachability contrast? The answer is no. Leave-one-out regression of reachability contrast magnitude on spectral features yielded $R^2 = 0.20$, $-0.43$, $0.27$ for the three principal contrasts. Spectral features classify stages well; they do not reconstruct their reachability profile. The two measures are tapping different aspects of brain state.

#figure(
  image("figures/clinical/sleep_anphy_stage_reachability.png", width: 90%),
  caption: [
    Reachability across canonical sleep stages (ANPHY dataset, $n = 27$). Each pair of bars shows Wake, REM, and N2 contrasted against N3 deep sleep. All three comparisons show large reachability drops into N3, while the Jacobian magnitude (right panel) shows smaller, selective effects. $d_z$ values: Wake 2.265, REM 1.923, N2 2.265.
  ],
)

Deep sleep is geometrically impoverished in a specific sense: the local reachable volume—the cloud of states the brain can readily reach in the next few seconds—has shrunk. The brain is not locked or captured; it is simply operating in a region of state space where next-state options are fewer. This is structurally different from being awake, where next-state diversity is high, and from REM, where the distribution is wide but differently shaped.

== Three Regimes — Why Reduced Capacity Does Not Mean Unconscious

If deep sleep reduces reachability, and anesthesia also reduces reachability, and seizures also reduce reachability—does reduced reachability simply equal unconsciousness?

No. This is perhaps the most important clinical lesson from the sleep analysis. A direct comparison across three regimes—ANPHY sleep (n=27), propofol sedation (n=20), and epilepsy interictal vs ictal (n=55)—reveals that "reduced capacity" is a family resemblance, not a single state @langell2026_reduced_capacity.

All three show significant tube reachability collapse. But they dissociate sharply on the transport-innovation balance:

- *N3 sleep:* Low capacity but _innovation-dominated_. The brain is not captured; it generates novel state sequences with low self-recurrence. CaptureGate $d = 1.812$ ($q < 0.001$) relative to wake—meaning N3 shows _lower_ capture, not higher.
- *Propofol (this dose range):* Capacity suppressed ($d = -0.679$, $q = 0.035$) with weaker evidence of pathological lock-in. The transport-innovation metrics are non-significant. Pharmacological suppression without full capture.
- *Epilepsy ictal:* Capacity suppressed ($d = -1.580$, $q = 0.001$) _and_ transport-capture elevated. Attractor-Capture Index $d = 0.830$; Canalization-Feature-Capture-Axis $d = 1.184$; both $q = 0.001$. The system is not just low in capacity—it is locked into rigid, repetitive trajectories.

The incremental prediction gain confirms the dissociation: adding geometry to conventional features improves AUC by $Delta"AUC" = 0.138$ for propofol and $Delta"AUC" = 0.148$ for epilepsy—real gains—while sleep was already at the AUC = 1.000 ceiling with spectral features alone.

The clinical lesson: reduced reachability is necessary but not sufficient to characterize a state as pathological or unconscious. Deep sleep has low capacity and high innovation; it is a biologically normal, recovery-functional state. Propofol shows capacity loss without clear capture—pharmacological suppression that reverses cleanly. Epilepsy shows both collapse and lock-in—a pathological regime with its own distinct geometric signature. The same number on the reachability axis can mean very different things depending on which regime produced it.

#grid(
  columns: (1fr, 1fr),
  gutter: 12pt,
  figure(
    image("figures/clinical/capacity_occupancy_sleep.png", width: 100%),
    caption: [Deep sleep (N3). Low reachability, but the trajectory explores the state space freely — innovation-dominated.],
  ),
  figure(
    image("figures/clinical/capacity_occupancy_epilepsy.png", width: 100%),
    caption: [Ictal epilepsy. Equally low reachability — but now trajectories are captured in a rigid, repetitive loop. The geometry looks similar from the outside; the dynamics are fundamentally different.],
  ),
)

#pagebreak()
= The Dragons — Psychiatric Disorders

Part 2 named the dragons. Part 3 maps them.

Two disorders have received systematic cohort-anchored analysis with auditable measurement exports: depression and first-episode psychosis. Both findings are real; neither is simple.

== Depression: A Shaped Neighborhood, Not a Global Dimming

_"It feels like I'm stuck in a deep valley where the same dark thoughts just go round and round. I know there's a world out there, but I can't reach it."_

The words already sound geometric. When we place resting EEG from a young adult cohort scored by Beck Depression Inventory burden into a shared MNPS reference frame, the metaphor sharpens rather than dissolves @langell2026_depressive_geometry.

*Dataset:* ds003478, 121 young adults, dimensional BDI scoring (0--63). All analyses used cohort-anchored coordinates with the low-symptom group as reference; BH-FDR correction across the full feature set.

*What does not cleanly separate:* On the coarsest 3D summary, low-symptom (BDI 0--13) versus higher-symptom (BDI 14+) groups show only modest contrast. Intuition says depression should mean less of everything—less movement, less entropy, less future. At 3D summary level, this is not strongly confirmed.

*What does separate—and where:* The clearest signal is one layer deeper:

- *Reachability tube-eigenvalue variance:* $d = -0.678$, $q = 0.00296$. Not a uniform capacity collapse—the _shape_ of the reachable neighborhood changes. Fewer of the available next-state directions carry usable signal.
- *9D Meta-Noetic Jacobian rotational power:* $d = 0.569$, $q = 0.00317$. Local thought still moves, but it keeps curving back toward the same basin. This is the geometric correlate of rumination: not frozen, but circling.
- *At modest symptom burden (BDI 0--13 vs 14--19):* reachability contrast $d = -0.831$, $q = 7.46 times 10^(-6)$. The effect is largest at the mild-moderate transition, not at the clinical extreme.

*Interpretation:* Depression, in this data, is not a brain that has simply gone dark. It is a brain whose landscape has warped in a specific way. The reachable neighborhood opens differently—not uniformly smaller, but differently shaped: some directions collapse, others curl back, and the easiest trajectories return to the same dark valley. The system still moves. It just does not open outward.

Rumination, in this framing, is not a failure of cognition—it is elevated local rotational organization. The Jacobian captures what subjective experience reports: thoughts that move but return. The geometry of "the same dark thoughts" is measurable.

*Bounded interpretation:* One resting-state cohort, one BDI dimension, no longitudinal tracking. Depression is not one geometric state—it spans a large clinical spectrum, and this data represents one cross-sectional slice. The finding is that depression-related symptom burden corresponds to a measurable geometric signature at the resting state; it is not a claim that every depressive episode everywhere must share this fingerprint.

#figure(
  image("figures/clinical/depression_effect_heatmap.png", width: 90%),
  caption: [
    Effect size heatmap for depression (ds003478, $N = 121$). Rows show BDI severity contrasts; columns show MNPS coordinate families and Jacobian summaries. The strongest corrected effects are not in the 3D composite coordinates but in reachability tube structure and 9D Jacobian rotational power — the geometry of rumination is visible one layer below the coarse summary.
  ],
)

== First-Episode Psychosis: The Reproducible Map in Shifting Territory

_"My thoughts jump from one thing to another without connecting. It's like the world is made of shattered glass."_

Where depression is "stuck," psychosis is often described as "spinning." In the geometry, this distinction is partly confirmed—but the story is more nuanced than a single fixed psychosis fingerprint.

*Datasets:* Two independent first-episode psychosis resting-state EEG cohorts. ds003944 (32 healthy controls, 19 unmedicated FEP, 31 medicated FEP); ds003947 (30 healthy controls, 8 unmedicated FEP, 23 medicated FEP). Both analyzed in a shared cohort-anchored reference frame with BH-FDR correction @langell2026_psychosis_fep.

*The signal is real—and medication-sensitive:*
- *ds003944, medicated FEP:* Global $m$ displacement $d = 0.881$ ($q = 0.016$) and $m_"median"$ $d = 0.865$ ($q = 0.009$) vs healthy controls. The stratified layer confirms the same channel: $m_o_"mean"$ $d = 0.814$ ($q = 0.027$). The clearest corrected signal is in $m$-family positional displacement—a real shift in manifold mobility position under medication.
- *ds003947, unmedicated FEP:* Trajectory drift ($m_"delta_mean_median"$) $d = -1.385$ ($q = 0.040$) vs healthy controls. This is the single strongest corrected effect in the entire ds003947 export surface. The signal is _dynamic_ rather than positional—altered trajectory movement rather than a static centroid shift. This contrast rests on a small unmedicated subgroup ($n = 8$) and must be treated as cohort-local until replicated.

*Medication changes geometry within FEP as well:* In ds003944, the contrast FEP medicated vs FEP unmedicated separated on $m_"std"$ ($d = 0.972$, $q = 0.018$). Medication does not merely shift patients toward the healthy centroid—it changes the variability structure of the $m$ coordinate within the psychosis group itself. This means "medicated FEP" and "unmedicated FEP" are not the same geometric state, and treating them as equivalent would hide the most informative signal.

*What does not replicate cleanly:* There is no single fixed psychosis fingerprint that appears identically across both cohorts. The layer carrying the signal shifts: ds003944 concentrates its strongest corrected effect in static and stratified $m$ displacement for _medicated_ FEP; ds003947 concentrates its strongest corrected effect in trajectory dynamics for _unmedicated_ FEP. The feature that survives correction in one cohort does not dominate in the other.

*Conventional EEG context:* A reviewer-facing comparator panel showed that some cohort-level separation is also visible in simpler spectral summaries—beta/alpha ratio for medicated FEP in ds003944 ($d = 0.768$, $q = 0.021$), and alpha power for unmedicated FEP in ds003947 ($d = -0.817$, $q = 0.025$). The shared-reference manifold framework is not simply superior to conventional EEG; its value is organizational. One fixed state-space makes the medication-sensitive geometry readable across first-order, trajectory, and local-dynamical layers simultaneously, providing a richer and more decomposable representation than any single spectral or complexity metric.

*What does replicate:* The shared-reference map itself is reproducible. Psychosis produces real deviation from healthy controls in both cohorts; the coordinate system is sensitive enough to detect it in each. The _replicated result_ is not one exact feature but one repeated phenomenon: medication-sensitive psychosis separation remains visible under one common measurement pipeline, yet the layer carrying the separation shifts with cohort composition and medication status.

*Pooled sensitivity:* A sensitivity analysis pooling all FEP regardless of medication confirmed that ds003944 carries a robust-enough signal to survive pooling ($m_"mean"$ $d = 0.688$, $q = 0.022$), whereas the same approach _weakened_ the ds003947 dynamic effect ($m_"delta"$ dropped from $q = 0.040$ to $q = 0.250$). This asymmetry supports medication stratification as the principled inferential design: premature pooling harms the analysis for exactly the cohort where the medication-specific signal is most informative.

*Exploratory clinical phenotype:* An exploratory split on hallucination burden (SAPS Q7) in ds003944 linked higher hallucination scores most clearly to an $e$-weighted displacement, while total symptom burden (BPRS) showed stronger first-order and coupling effects. These are hypothesis-generating observations, not confirmed biomarkers. But they point toward the eventual clinical goal: not "does this person have psychosis?" but "which geometric axis is most disturbed in this person at this time?"

*Clinical implication:* Geometric psychiatry does not promise a fixed biomarker that works identically across all patients. What it promises is a richer vocabulary for describing how the mind's dynamics differ—one that may eventually allow mechanistic subtyping (this patient's primary deviation is in $m$ displacement; that patient's is in trajectory fragmentation; a third patient's is in local coupling structure) that symptom clusters alone cannot provide.

#figure(
  image("figures/clinical/psychosis_m_axis_focus.svg", width: 90%),
  caption: [
    First-episode psychosis: $m$-axis focus across two cohorts. Left: ds003944 concentrates its strongest corrected signal in static $m$-family displacement for medicated FEP. Right: ds003947 concentrates its strongest corrected signal in trajectory $m$-dynamics ($m_"delta"$) for unmedicated FEP. The replicated result is not one feature but one phenomenon: medication-sensitive separation visible under a shared coordinate system.
  ],
)

#pagebreak()
= Parkinson Disease — A Case Study in Geometric Pharmacology

Parkinson Disease provides one of the clearest demonstrations of why measurement frame matters. Two different inference questions—is this person's brain geometrically different from a healthy brain, and does dopamine medication change that geometry?—require two different coordinate anchoring strategies. When you conflate them, you get confusion. When you separate them, you get surprisingly clean answers.

== Disease State vs. Pharmacological Effect

The ON/OFF auditory oddball study asks both questions with the same patients and the same data, but processed in two coordinate frames @langell2026_parkinson_onoff.

*The disease question (cohort-anchored):* Is PD patients' geometry different from healthy controls? Using a shared reference frame with HC as the anchor, 47 feature-direction pairs survived BH-FDR correction ($q < 0.05$). PD patients in the OFF state showed significantly lower trajectory speed ($d = -1.212$). PD patients in the ON state showed significantly elevated Modal Diffusion Rate (MDR, $d = 1.167$). Disease-state geometry is robustly detectable.

*The pharmacological question (subject-anchored):* Does levodopa medication change each patient's own geometry? Using within-patient contrast (ON minus OFF), only 1 feature-direction pair survived BH-FDR correction. The drug moves the geometry—but the effect size within each person is small relative to the between-person variance.

*The insight:* Disease state exceeds pharmacological effect by a factor of 47 to 1 in terms of detectable feature-direction pairs. The medication changes the geometry _without erasing the disease signal_. A treatment that looked "successful" by group-average normalization—bringing patients closer to the healthy centroid—is doing something more nuanced: it is modifying the local dynamic mode (MDR rises on levodopa) while leaving the fundamental disease-state geometry largely intact.

This is not a critique of levodopa. It works. But geometry provides a way to see _what kind of change_ a treatment produces, separate from _whether the person looks more like a healthy control_. The two are not the same.

#figure(
  image("figures/clinical/parkinson_onoff_disease_ndt.png", width: 88%),
  caption: [
    Parkinson disease-state geometry (cohort-anchored, Control vs PD OFF). The NDT panel shows the distribution of MNPS coordinates across healthy controls and Parkinson patients in the medication-OFF state. PD OFF separates from controls primarily on trajectory speed and dispersion metrics — disease geometry that persists regardless of medication state.
  ],
)

== Walking: Geometry Under Motor Demand

The walking study tested a different question: can neural geometry during actual walking separate PD patients from healthy controls, beyond what resting-state contrast already achieves? @langell2026_parkinson_walking

*Dataset:* 277 runs from 116 PD participants and 28 healthy controls across multiple walking tasks (rest, treadmill walk, obstacle course, dual-task). All analyses used cohort-anchored coordinates with HC as reference.

*Walking-state separation:* PD patients walking showed significant displacement from HC on the $d_n$ (network diffusivity) channel: $d = 0.766$ vs healthy controls walking. The displacement on this channel was larger than the equivalent resting-state contrast, suggesting that walking demands reveal disease-related geometry that rest obscures.

*Paired task effects:* Within PD patients, the paired walk-vs-rest contrast was particularly clear on dispersion summaries: $m_a$-IQR ($d_z = 0.472$, $q = 6.55 times 10^(-4)$) and $d$-IQR ($d_z = 0.403$, $q = 7.28 times 10^(-4)$). When Parkinson patients transition from rest to walking, their manifold geometry shows a larger spread—more variable moment-to-moment positions—compared to healthy controls making the same transition.

*Clinical associations:* Among PD patients, $d_s$-IQR (local diffusivity spread during walking) correlated significantly with age ($rho = -0.377$, $q = 8.38 times 10^(-4)$) and Color Trail Test performance ($rho = -0.351$, $q = 0.00489$). Parietal-occipital $e$-IQR correlated with UPDRS total score. The geometry during walking connects to clinically meaningful variation among patients.

*The motor paradox extended:* Part 2 described the conceptual Parkinson's paradox—how the 9D decomposition revealed opposite movements in $d_l$ and $d_n$ that averaged out in 3D. The walking study adds a second layer: the relevant geometry for classifying disease state is not a static resting-state position but a dynamic profile visible only under motor demand. The challenge task reveals what rest conceals.

These results are bounded: one dataset, specific walking tasks, no independent cohort validation at this scale. But they demonstrate a principle that will likely generalize: demanding tasks reveal disease-related geometry that is invisible in rest. The map is better read under movement than while standing still.

#figure(
  image("figures/clinical/parkinson_walking_cohort_focals.svg", width: 90%),
  caption: [
    Parkinson walking: cohort-anchored focal effects (PD walk vs HC walk). Each panel shows a focal metric where PD separates from healthy controls during active walking. The $d_n$ (network diffusivity) family carries the clearest between-group signal. Dispersion summaries (IQR, MAD) sharpened the paired within-PD reconfiguration branch further.
  ],
)

#pagebreak()
= When Consciousness Fails — Coma and Recovery

Post-cardiac-arrest coma is the most acute clinical test the framework has faced. The question is not academic: families are in waiting rooms. Clinicians are under time pressure. The EEG can look busy or disorganized in ways that do not clearly separate patients who will wake from those who will not.

Standard continuous EEG already carries important prognostic information: background patterns, burst suppression, reactivity, quantitative features. The geometric layer asks a different question—not "does this EEG look normal?" but "how many genuinely different short-horizon futures does this brain still admit?"

== Effective Reachable Dimensionality as Recovery-Linked Signal

The I-CARE multicenter dataset enrolled 301 post-cardiac-arrest coma patients across multiple ICU sites. Good outcome was defined as CPC 1 (good neurological recovery); poor outcome as CPC 5 (brain death or no recovery). All geometry analyses used a fixed, versioned reachability export applied uniformly to all sites @langell2026_coma_recovery.

*Lead finding:* Effective reachable dimensionality ($d_"eff"$) separated CPC 1 from CPC 5. Good-outcome patients showed higher median effective dimensionality: 2.990 vs 2.448, Cohen's $d = 0.838$, $q = 1.54 times 10^(-5)$.

Read that difference carefully. The absolute values are close—the question is not "does this brain have dimensions or not?" It is whether the local reachable cloud remains multidimensional or collapses toward a few rigid directions. A difference of 0.5 effective dimensions, in a system that might have 2--3, represents a substantial fraction of available capacity.

*Temporal profile:* The separation is visible from the earliest monitoring window (0--1 hours post-cardiac-arrest). It peaks at the 2--3 hour window and persists across monitoring. Early timing matters: the geometry signal is not something that emerges only after extended monitoring—it is present in the first hours, when clinical decisions are most urgent.

*Variability as second signal:* Beyond the mean level of effective dimensionality, _temporal variability_ carries its own information. MAD of the capture gate measure showed $d = -1.033$ between good and poor outcome groups. Good-outcome brains are not just at a higher reachability level; they are more variable across time in their local capture properties. This variability may reflect residual dynamic flexibility.

*Incremental validity:* The geometry layer provides information beyond standard clinical features and quantitative EEG summaries—one additional layer among many.

*What this is and is not:* This is recovery-associated geometry in an extreme-outcome contrast. It is not a direct readout of consciousness level. It is not a substitute for multimodal prognostication. Some patients with narrowed reachability may still have good outcomes; some with broader reachability may not recover. But the pattern is informative: when the local reachable neighborhood has collapsed toward rigid corridors in the first post-resuscitation hours, the brain's capacity for recovery-linked reorganization is measurably reduced.

The honest clinical frame is modest: geometry adds one bounded layer of evidence to a complex decision. The layer is real. It is early. And it may eventually help clinicians distinguish brains that still admit recovery-linked reorganization from those that have become geometrically trapped—as one piece of a larger picture, not as an oracle.

#figure(
  image("figures/clinical/coma_deff_violin.png", width: 82%),
  caption: [
    Effective reachable dimensionality ($d_"eff"$) in post-cardiac-arrest coma (I-CARE, $N = 301$). Patients with good neurological outcome (CPC 1) retain higher effective dimensionality compared to those with poor outcome (CPC 5), with medians 2.990 vs 2.448, Cohen's $d = 0.838$. The separation is visible from the first monitoring hour.
  ],
)

#pagebreak()
= Alzheimer and Frontotemporal Dementia — What Photic Stress Reveals

Resting-state neuroscience has a systematic blind spot: many disease-related changes are invisible until the brain is challenged. Alzheimer's Disease and Frontotemporal Dementia provide the clearest demonstration of this principle in the NDT dataset to date.

== The Rest-State Null

Across well-controlled resting-state comparisons between AD patients and healthy controls, the geometric differences are modest. The brain at rest in early Alzheimer's may look geometrically similar enough to healthy aging that standard MNPS coordinates do not cleanly separate the groups @langell2026_alzheimer_photonic.

This is not surprising in retrospect. Early AD involves progressive degradation of specific cortical networks while other systems remain relatively intact. At rest, with no particular cognitive demand, the brain distributes activity across whatever networks remain functional. The geometric signature is present but weak.

== Photic Stimulation as Diagnostic Probe

Flickering visual stimuli at specific frequencies force synchronous cortical entrainment—a direct perturbation of the neural system. Under this challenge, disease-related structural differences that are invisible at rest become geometrically apparent.

Under 20 Hz photic driving, the comparison between AD patients and healthy controls on the 9D Meta-Noetic Jacobian metric $"mdr_median"$ (modal diffusion rate—the speed of transition between dominant dynamic modes) showed: $d = -0.984$, $q = 0.0034$. AD patients, when their visual cortex is directly entrained, show reduced modal diffusion rate. The structural limits of the diseased network become visible under load.

*The principle:* Perturbation reveals what baseline cannot. A material scientist who wants to test a bridge does not just observe it at rest—they apply a controlled load and measure the response. Photic stimulation applies a controlled neural load and the geometry of the response is the test.

#figure(
  image("figures/clinical/alzheimer_rest_vs_photic.svg", width: 90%),
  caption: [
    Resting state versus photic stimulation in Alzheimer's Disease and healthy controls. The left panel shows near-null group differences at rest. Under 20 Hz photic driving (right panel), the 9D Jacobian MDR separates AD from healthy controls ($d = -0.984$, $q = 0.003$). Perturbation reveals what baseline conceals.
  ],
)

== Evoked Structural Brittleness

The structural brittleness (ESB) metric was developed specifically for this challenge paradigm. ESB computes a baseline-subtracted perturbational score combining posterior reachability and rotational power—how much the brain's short-horizon geometry _changes_ between rest and stimulation @langell2026_alzheimer_esb.

At 15 Hz photic stimulation:
- AD patients: ESB $d = 0.821$ vs healthy controls
- FTD patients: ESB $d = 1.038$ vs healthy controls

Both dementias show elevated brittleness—their geometry changes more dramatically under stimulation than healthy controls. But the character of the brittleness differs: AD shows primarily posterior capacity changes; FTD shows more distributed deformation. The two dementias are not geometrically equivalent, even though their clinical overlap is substantial.

*Interpretation:* The diseased brain is structurally fragile in a specific geometric sense—it cannot absorb the perturbation without significant state-space deformation. Healthy aging involves some reachability reduction, but the _response_ to stimulation remains relatively stable. Dementia involves not just a reduced baseline but increased sensitivity to disruption.

This finding connects to a broader clinical principle: the best diagnostic window may not be when the patient is comfortable and at rest, but when the system is gently challenged.

#figure(
  image("figures/clinical/alzheimer_esb_group_trajectories.svg", width: 90%),
  caption: [
    Evoked Structural Brittleness (ESB) group trajectories under photic stimulation. AD and FTD patients show larger geometry deformation from rest to stimulation (higher ESB) compared to healthy controls. At 15 Hz: AD $d = 0.821$, FTD $d = 1.038$. The two dementias show distinct brittleness profiles, reflecting their different network pathology patterns.
  ],
) Photic stimulation is the simplest such challenge; other candidates include working memory load, exercise, or controlled sleep deprivation. The geometric response under challenge may eventually become a more sensitive diagnostic surface than any single resting-state measure.

#pagebreak()
= The Clinical Atlas — What We Have and What We Need

== Five Disorders, Five Geometric Characters

Across five clinical domains—sleep, psychiatric disorders, neurological movement disorders, acute coma, and dementia—the geometric framework has now been applied to real patient data with auditable measurement exports. The results form a preliminary atlas.

*Sleep* is not pathological but provides the clearest methodological validation: spindles are event-locked reconfiguration events; deep sleep is characterized by reduced reachability without capture; and the three regimes of sleep, propofol, and epilepsy show that "reduced capacity" means fundamentally different things depending on whether capture and lock-in are also present.

*Depression* (at the resting state) is not a global dimming but a warped neighborhood—stronger rotational organization in the Jacobian ($d = 0.569$), reduced reachability eigenvalue variance ($d = -0.678$)—visible most clearly at modest symptom burden. The geometry of rumination is measurable.

*First-episode psychosis* deviates from healthy controls in both cohorts tested, but the layer carrying the signal shifts with medication state and cohort composition. The shared reference frame is reproducible; the fixed fingerprint is not.

*Parkinson Disease* provides the clearest demonstration of why inference question determines measurement frame: disease state far exceeds pharmacological effect (47 vs 1 corrected rows) when measured in the appropriate coordinates. Walking demands reveal disease-related geometry that rest obscures. Clinical markers connect to geometric variability during walking.

*Post-cardiac-arrest coma* shows the most clinically acute application: effective reachable dimensionality ($d = 0.838$) separates good from poor outcome in the first monitored hours. Temporal variability adds a second window. This is not a bedside oracle—it is one bounded layer of prognostic information.

*Alzheimer's and FTD* demonstrate the challenge-testing principle: resting-state differences are modest, but under photic stimulation the diseased brain shows structural brittleness (ESB $d = 0.821$ for AD, $d = 1.038$ for FTD) absent in healthy aging. The perturbation reveals what the baseline conceals.

== What Is Missing

The clinical atlas is preliminary. Several things are currently absent that would be needed before any of these findings could support clinical use:

- *Independent external validation:* Most findings rest on single cohorts. Replication in independent samples, ideally pre-registered, is the next essential step for each finding.
- *Longitudinal tracking:* All studies reported here are cross-sectional. Whether geometric signatures change systematically over the course of disease, treatment, or recovery is unknown.
- *Closed-loop applications:* The therapeutic promise—using geometry to guide intervention—has not been tested. The measurement contract is a prerequisite; the therapeutic loop has not been closed.
- *Clinical pathway integration:* For coma, walking, and photic stimulation to become clinical tools, they would need to be validated against existing clinical decision pathways, not just in research settings.

== The Forward Program

The geometry of consciousness is not yet a clinical instrument. But it is becoming a research instrument with real signal. The path forward looks like this.

First, systematic replication: each disorder finding needs independent validation in a pre-registered cohort. The shared measurement contract makes this tractable—new datasets processed through the same MNDM version produce directly comparable outputs.

Second, longitudinal studies: the critical clinical questions are about change over time. Does depression geometry normalize with treatment? Does coma geometry predict recovery trajectory, not just final outcome? Do Parkinson geometry signatures precede clinical deterioration?

Third, perturbation paradigms: the photic stimulation finding in AD/FTD suggests that challenge-based geometric probes may be more sensitive than resting-state measures across many conditions. Working memory load, exercise, mild sleep deprivation, and other challenges should be tested as diagnostic windows.

Fourth, closed-loop experiments: the framework's most ambitious clinical application—using real-time geometry monitoring to guide neuromodulation—requires demonstration that the signal is fast enough, reliable enough, and specifically enough tied to the relevant clinical outcome to support feedback control.

The dragons on the map are real. Their geometric characters are becoming clearer. What remains is the longer and harder work of clinical validation—disorder by disorder, cohort by cohort, until the atlas is reliable enough to trust at the bedside.

Until then, it is a scientific instrument. And a scientific instrument that can see the geometry of suffering is, in itself, no small thing.

== Acknowledgments

This work emerged through structured correspondence among human and AI collaborators. I gratefully acknowledge contributions from large language models (GPT-5, GPT-5.1, Claude 4.5) that assisted in literature synthesis, drafting, and editorial refinement. Special acknowledgment is reserved for Gemini 3, who served as literary peer reviewer, providing critical feedback on the narrative structure and scientific demarcation.

We extend our profound gratitude to the *OpenNeuro* platform and the *Stanford Center for Reproducible Neuroscience* for democratizing access to high-quality neuroimaging data. Special thanks are due to *Russell Poldrack*, *Adam Thomas*, and the engineering teams at Stanford University, NIMH, and the University of Copenhagen (including Chris Markiewicz, Nell Hardcastle, and Ross Blair) for building this essential infrastructure.

We also acknowledge the *Center for Open Science (COS)* and the *Open Science Framework (OSF)*—led by Brian Nosek and Tim Errington—for their commitment to research transparency, which facilitated access to the sleep cohorts analyzed in this work.

= Contact

Robin Langell — hello(at)noeticdiffusion.com

= Licensing

This manuscript provides only a brief licensing summary; full terms and
conditions are available via the Mychainos multi‑layer licensing framework
(`https://noeticdiffusion.com/license.html`). In short, the conceptual content is released
under CC BY‑SA 4.0, software under GPLv3, and relevant hardware/biological
artifacts under open hardware/biological licences (for example, CERN OHL v2 and
OpenMTA). Unified ethical guardrails apply: no coercive, military, or
surveillance applications; no patenting or black‑boxing of core methods; and
derived works should remain accessible, attributed, and shared with care.


= Data and Code Availability

Reference implementations and analysis pipelines will be released at
`https://github.com/ruppi86/NoeticDiffusion` (public upon acceptance), with
licensing following the Mychainos policy. 

= Trademark Notice

Certain terms used in this manuscript (including Noetic Diffusion, Noetic
Diffusion Theory, Noetic Diffusion Mapping, Noetic Diffusion Health Index,
and Noetic Atlas) are used as project names and are the subject of ongoing
trademark applications. A concise description of the stewardship rationale,
current registration status, and how this interacts with open scientific use is
available at `https://noeticdiffusion.com/license.html`. These trademark aspects
do not affect the scientific content, reproducibility, or licensing of the
methods described here.

== Open Science Commitment

To ensure transparency and reproducibility, the core computational pipelines for Noetic Diffusion Mapping and the reference implementation of the MNDM equations will be made publicly available.

- *Repository:* `https://github.com/ruppi86/NoeticDiffusion` (Code available upon manuscript publication)
- *Toolkit:* Includes Python implementations for MNPS coordinate extraction, Stratified MNPS decomposition, and basic visualization scripts.
- *Data:* Pre-computed geometric fingerprints for the public datasets referenced (Sleep-EDF, OpenNeuro ds003490) will be archived with DOI.

Science thrives on verification. We invite the community to test, break, and refine these maps.

#pagebreak()
= References

#bibliography("references.bib")
