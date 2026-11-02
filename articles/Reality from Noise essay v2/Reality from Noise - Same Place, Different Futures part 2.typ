// Reality from Noise: Same Place, Different Futures — Part 2
// Texture, nudge, and nearby horizons (NDT v2 framing)
// Author: Robin Langell, 2026

#import "template.typ": essay-template, clean-table

#show: doc => essay-template(
  title: text(hyphenate: false)[Reality from Noise:\ Same Place, Different Futures],
  subtitle: [Part 2: Texture, Nudge, and Nearby Horizons],
  author: [Robin Langell],
  date: [2026],
  series-description: [An illustrated research essay on Noetic Diffusion Theory],
  doc,
)

== Prelude: The Questions We Deferred

Part 1 separated a measured pin from the law of nearby futures. Here we examine four objects: feature texture, local deformation, short-horizon predictive spread, and control at matched state.

We also named the three commitments that carry the theory:

- *C1.* A reduced measured pin need not determine the latent future law.
- *C2.* In some regimes, summaries of chart-conditional future dynamics should add reproducible held-out information beyond present location and standard static or spectral summaries.
- *C3.* Nominated contextual or physiological controls should change specified future-law features at matched chart state beyond ordinary covariates. Better prediction from an extra covariate alone is insufficient.

C1 motivates the distinction; *C2 and C3 carry the empirical burden*. Part 1's evidence ledger separates these requirements from the partial evidence available so far @langell2026ndt_current.

#figure(
  image("figures/ndt_v.1/fig1_ndt_architecture_v2.png", width: 80%),
  caption: [*Schematic.* The NDT architecture, in one picture. A measured point is surrounded by local dynamical objects. Candidate controls act from above. Recordings enter only through an observation map and a versioned chart. The chart is not the theory.],
)

*Reading route.* The conceptual sections carry the argument; the measurement contract, covariance recursion and technical reference explain the numbers. Part 3 collects clinical comparisons. Lifespan and philosophy remain speculative.

*Evidence and figures.* Specifying a formula does not validate its interpretation. Watercolor terrain is metaphor only; captions distinguish schematics, measured charts and model-derived estimates. The four inferential questions below require different evidence.

#pagebreak()


= Texture of the Pin

== Elevation is not geology

In Part 1 we drew a three-axis sketch: entropy ($e$), mobility / coordination ($m$), and deviation from an integration–segregation balance ($d$). That sketch answers a *state* question. It tells you roughly where a recording sits. It does not tell you why.

Two hikers can share an altitude while standing on different rock. Likewise, two hypothetical recordings could share $(m,d,e)$ while their nine-feature patterns differ, with changes cancelling in the projection. This illustrates information lost by aggregation; it is not an established match between experiences or diagnoses. C1 asks the further question of whether reduced present state suffices for the latent future law.

== Nine coordinates, three families

The three families retain the order $[m,d,e]$: mobility or coordination, deviation from an integration–segregation balance, and entropy or complexity pressure. These are interpretive families. The measurements are the configured signal features.

The coordinates retain their exported symbols, but this essay uses signal-derived labels: low-frequency and alpha-derived proxies, power ratios, Hjorth features and declared entropy or arousal features. The reference mapping and historical aliases are collected in @feature-reference. A gamma-power feature is not a measured network diffusion tensor, and a beta/alpha ratio is not a direct test of cognitive flexibility.

The 9D layer is still a *map*. It is a finer subway diagram, not the land. Its job is to show that the same 3D pin can be assembled in different ways. That is already enough to make some clinical questions visible.

#figure(
  image("figures/ndt_v.1/fig_p2_texture_projection_v2.png", width: 100%),
  caption: [A schematic many-to-one projection. Two hypothetical nine-feature patterns can share a three-coordinate summary under a declared mapping. Tile shades are illustrative, not numerical feature values or the release's projection weights. The extra coordinates describe measured texture, not nine mental faculties.],
)

#pagebreak()
= The Measurement Contract

== A map that can be audited

A reproducible coordinate system lets different analyses ask comparable questions. NeuralManifoldDynamics specifies how recordings become auditable features and trajectories. Scientific contrasts, estimator choices, null controls and biological interpretation remain responsibilities of the analysis layer @langell2026_neuralmanifolddynamics.

It is not NDT. It is a *pipeline specification*. Projection weights, normalization, temporal sampling and validity policy must be recorded. Reusing names or software is not enough: different references and sampling choices can change what a coordinate means. Cross-cohort comparisons in Part 3 therefore require their own provenance and compatibility checks.

#figure(
  grid(
    columns: (1fr, 1fr), gutter: 8pt,
    block(fill: rgb("#f2f6f8"), inset: 10pt)[*Association*\ Does a measured quantity covary with a label or outcome under the declared contract?],
    block(fill: rgb("#f2f6f8"), inset: 10pt)[*Mechanism discrimination*\ Can the observations separate specified competing explanations?],
    block(fill: rgb("#f2f6f8"), inset: 10pt)[*Preservation of latent order*\ Does a chart summary retain an independently known ordering in a qualified reference system?],
    block(fill: rgb("#f2f6f8"), inset: 10pt)[*Operator identification*\ Does a fitted dynamical operator recover the relevant law under justified assumptions and fit checks?],
  ),
  caption: [A schematic set of inferential questions. The equal panels carry no ranking or progression: each claim needs evidence suited to its own question. A positive result in one panel does not automatically establish another.],
)

== Canonical 3D from 9D

The pipeline's primary export is a three-number time series: $x_t = [m_t, d_t, e_t]$. These are projected from a 9D vector:

$ x_t^((9)) = W_(9D) dot z_t, quad quad x_t = P dot x_t^((9)) $

where $z_t$ is the standardized feature vector, $W_(9D)$ maps features to the nine subcoordinates, and $P$ is a release-fixed projection. Comparability requires the declared release and configuration. $P$ is fixed within that contract, not a universal biological projection; reference fitting and available inputs must also match the question.

The 9D layer can reveal *texture* where the 3D composite reveals only *presence*. When two sub-coordinates move in opposite directions, their weighted average can stay flat. That is a property of the projection, discussed below; it is not by itself a mechanism claim.

== Two frames, two questions

Not every "where is this person?" question is the same.

_Cohort-anchored_ coordinates place everyone in a shared frame set by a reference group. Between-subject questions: does this Parkinson patient differ from healthy controls?

_Subject-anchored_ coordinates use a declared subject/session reference. That reference can pool observations and need not represent a healthy or pre-treatment baseline. Within-subject questions: does this patient change from rest to walking, or from OFF to ON?

A treatment that "normalizes" a patient toward the group average may not restore *their* healthy future-law. Part 3 therefore identifies the frame used for each comparison rather than assuming every chart supports the same question.

== Block-native versus event-locked

_Block-native_ analysis summarizes geometry during a sustained condition: a sleep stage, a task block.

_Event-locked_ analysis aligns windows to transients—spindle onsets, trial starts, seizures—and compares them with matched controls.

Averaging all of N2 together cannot answer the spindle question. An event-timing question needs event-aligned baselines and appropriate within-stage controls; comparing events only with other N2 windows can instead reveal neighborhood or event-selection differences. The distinction is not bookkeeping. It determines which claims are licensed.

== Validity policy

Each estimator needs explicit checks for artifacts, temporal gaps, neighborhood support, conditioning and applicable inputs. Invalid or unsupported estimates must remain unavailable, with reasons and coverage reported. A number being serialized does not make it a qualified operator. A result that survives in 90% of subjects across two cohorts is a different epistemic object from a single-dataset result without those controls.

== Why a composite can hide texture

A weighted sum can stay flat while its parts move. If one sub-coordinate rises and another falls, their projection onto a single axis need not change. That is arithmetic, not neuroscience: it says only that a 3D "null" is not evidence that nothing happened at 9D.

An earlier version illustrated that arithmetic with a Parkinson's story—L-DOPA lowering the Hjorth-mobility feature ($d_l$) while raising the gamma-power proxy ($d_n$), the two cancelling in 3D. That story is *not* supported by the FDR-corrected source article, and this edition withdraws it @langell2026_parkinson_onoff.

== What the Parkinson data actually show

Dataset ds003490: 25 Parkinson ON/OFF pairs and 25 controls, processed under one contract but two frames.

*Across the full analysis,* 47 rows survived BH-FDR $q < 0.05$ within contrast and analysis-type families: 46 disease-state rows and one paired medication row.

*Disease state (cohort-anchored, controls as anchor):* The leading disease-state representatives were not level shifts of $d_l$ or $d_n$, but a dispersion row (`d_n_std`), a trajectory-speed row (`speed_median`, PD OFF slower, $d_C = -1.212$), and a 9D Jacobian-change ratio (`mdr_median`, PD ON elevated, $d_C = 1.167$). The medicated state is not simply "closer to control." It remains non-control-like in Jacobian and deformation terms.

*Medication (subject-anchored, ON minus OFF):* one row survived—a temporal-region 3D Jacobian eigenvalue-anisotropy summary (`anisotropy_abs_eig_mean`, $d_z = -0.483$, $q = 0.038$). Here temporal names the EEG region, not a temporal derivative. The result is a narrow hypothesis-generating signal, not a validated medication-response signature.

The texture lesson survives in a weaker, more honest form. The layer that carries a disease-state signal in this dataset is dispersion, speed, and local deformation—not the 3D composite pin. Where medication *does* register, it registers in a Jacobian summary, not as opposite $d_l$/$d_n$ level shifts. Same patients. Different questions. Different layers.

These representatives were selected after analysis, without preregistered primary endpoints or external validation. This is still mostly a *state and local-deformation* result. It does not yet answer what the nearby futures did. That is the next instrument.

#pagebreak()
= What a Small Nudge Does

== Drift is not the Jacobian

Part 1's hiker had a slope: local drift, which way the ground carries you. The Jacobian is a different question. If two nearby hikers are nudged a little apart, does their separation grow, shrink, shear, or rotate?

$ J_(i j)(x, t) = (partial (b_x)_i) / (partial x_j) $

Here $b_x$ denotes drift in a declared chart model. An empirical fit yields estimates $hat(b)_x$ and $hat(J)$, whose use requires a justified local dynamical approximation. It is not automatically the projection of a fully identified latent drift.

In the three-axis chart that is a $3 times 3$ matrix of how each coordinate's rate of change depends on the others. Under the declared Euclidean chart norm, the symmetric part $S = (J + J^T)/2$ gives instantaneous stretching and shrinking, and the antisymmetric part $Omega = (J - J^T)/2$ gives a rotational component. These are properties of the local model; they do not by themselves identify an anatomical feedback circuit or a response to an experimental intervention.

A few things this is *not*:

- It is not "the second derivative of consciousness."
- It is not the intelligence of the landscape, a terraformer, or a conductor's wisdom.
- It is not an intrinsic tensor of a unique brain manifold. Current Jacobian summaries are *chart-level* measurements. A nonlinear change of coordinates would mix them. We estimate $J$ in a declared measurement chart, and we should say so.

Drift is which way you are already being carried. The Jacobian is what happens to nearby travelers. Those can come apart. A system can sit in a similar place, with a similar average slope, and still amplify a small perturbation in one person while damping it in another.

#figure(
  image("figures/ndt_v.1/fig_p2_deformation_diffusion_v2.png", width: 100%),
  caption: [Two distinct local-model questions. Left: a neighborhood is redrawn beside its original shape to illustrate deformation of nearby displacements. Right: a schematic fluctuation cloud illustrates directional stochastic spread. Neither drawing is an empirical estimate; local diffusion alone does not specify a finite-horizon future distribution.],
)

== Growth, decay, and a gap between them

From $J$ one can read several non-equivalent summaries:

- *Spectral abscissa* $alpha(J) = max_i Re(lambda_i (J))$: modal growth or decay in the frozen local linear model.
- *Numerical abscissa* $omega(J) = lambda_max ((J+J^T)/2)$: maximal instantaneous growth rate in the declared norm.
- *Reactivity gap* $Delta_"react" = omega - alpha$: the room between those two.

The last is a known phenomenon in non-normal networks: every eigenmode can be stable while a carefully aimed shove still flares before it dies. That is not "eigenvalue slowing." It is a different local question. For a time-varying flow, instantaneous eigenvalues do not establish long-term stability. The gap is not a complete measure of non-normality, and none of these summaries is finite-horizon predictive spread. Instantaneous growth and the size of the next-few-seconds cloud are different objects.

== What a local model can and cannot explain

Imagine two locally fitted flows at similar chart locations. One initially damps a small displacement; another amplifies it along a particular direction. This is a useful model comparison. Establishing that a biological perturbation would behave that way requires evidence beyond a fit to spontaneous recordings.

Nor is local linear stability the same as metastability. A negative spectral abscissa concerns infinitesimal modes in a local approximation. Metastability concerns coordination that persists while transitions remain possible. Neither is directly measured by the MNPS feature family named $m$.

Part 3 reports cohort-level differences in geometric summaries. Translating them into psychological processes requires separate tests: a rotational component does not establish thought content, a limit cycle or a causal explanation of depression.

The theory's own companion work makes this caution concrete. Some recordings support decodable information while the nominated chart fails operator-recovery checks. Synthetic systems can validate an estimator inside a known envelope; that success does not automatically transfer to EEG @langell2026ndt_current.

== Sleep at finer resolution

Part 1's nightly renovation was a question about what changes during sleep and what remains changed afterward. At finer resolution, we can separate location, local deformation, stochastic spread and finite-horizon prediction. These quantities need not move together.

Earlier within-subject PSG comparisons reported lower traversal and temporal repertoire in deep NREM, together with smaller predictive-spread summaries than Wake or REM. The ANPHY analysis likewise reported stage differences in estimated local predictive spread, with more selective Jacobian effects @langell2025_extreme @langell2026_sleep_reachability. These are results of their particular chart, reference and estimator. They are not a direct measurement of how many experiences a sleeper could have.

The newer descriptive cohort in Part 1 sharpens the distinction: lower diffusion magnitude in N2 was common, while changes in directional shape and effective dimensionality varied across people. That analysis used recording-relative references and estimator neighborhoods that could mix stages. It does not independently identify latent diffusion or a full reachable set @langell2026_sleep_families_revision.

Inside N2, an event-versus-baseline test and a comparison with matched non-spindle N2 answer different questions. The newer spindle work distinguishes event timing from the kind of neighborhood in which an event occurs. Its timing result held in two datasets but remained inconclusive in RichSleep; the older spindle-window study's strongest $d$-labelled endpoint also used its own historical definition @langell2026_rvc_sleep_revision @langell2026_spindle_windows.

None of these contrasts identifies a memory save operation. Memory, next-day performance and lasting changes in access require their own outcomes. What the finer map offers is a way to specify those tests.

#figure(
  image("figures/reachability/ds005555_sub-25_wake_vs_nrem3.png", width: 85%),
  caption: [*Model estimate.* Legacy within-subject illustration from ds005555, labeled T=8 s, H=5 and k=20. Those settings differ from the refreshed report's main defaults. Read its capacity labels as model-implied covariance spread, not usable mental options; the newer sleep decomposition is strongly innovation-dominated. This panel does not independently validate the current estimator.],
)

#pagebreak()
= Nearby Futures, Not Occupancy

== A Predictive-Spread Ellipsoid

Having nine sub-coordinates and a Jacobian still answers *local* questions. Short-horizon predictive spread asks a different one: from here, over a declared horizon, how does a local model propagate variation in next states? The companion research calls this object stochastic reachability; this essay uses predictive spread to keep its second-moment scope visible.

For a frozen local affine model with transition matrix $A_t$ and residual covariance $Q_t$, the illustrative covariance recursion is @langell2026ndt_current @langell2026_reachability_current:

$ Sigma_t^((0)) = 0, quad Sigma_t^((h+1)) = A_t Sigma_t^((h)) A_t^T + Q_t $

Here $h$ counts prediction steps; the sampling interval determines physical duration. Holding $A_t$ and $Q_t$ fixed across those steps is an approximation. The covariance $Sigma_t^((h))$ is not the noise-amplitude matrix $Sigma$ in Part 1, and $Q_t$ is not automatically an identified continuous-time diffusion tensor.

Following the current theory's terminology, the ellipsoid around that covariance is *not* classical control-theoretic reachability, and it is not a list of every physically possible brain state. It is a second-moment picture of predictive spread. A large occupied cloud on the map (where the system *has been*) is not the same as a wide horizon of possible next moves.

We summarize the ellipsoid with a few numbers:

- *Volume proxy* ($1/2 log det Sigma$): spread at a declared horizon, where covariance is positive definite and the regularization policy is stated.
- *Anisotropy / condition number:* how unevenly spread is distributed across directions; a large ratio need not imply behavioral rigidity.
- *Effective dimensionality $d_"eff":$* how evenly covariance eigenvalues distribute the spread across directions.

There is no universal healthy ellipsoid size. Increasing residual noise can inflate this cloud without improving controllability or meaningful access. Changing normalization can change its shape. A larger value is not automatically better.

Occupancy and predictive spread nevertheless ask different questions: where observations have accumulated, and how a local model predicts variation from a specified start. Neither a broad occupied cloud nor a narrow predicted one proves that a person is trapped.

Validity depends on temporal continuity, estimation support, the horizon and whether a neighborhood leaks across conditions. The predicted covariance must be checked against held-out observations. A failed check leaves that inference unavailable, even when the picture is attractive @langell2026ndt_current.

== Reduced capacity is a family, not a verdict

Deep sleep, propofol, and epilepsy can all show capacity loss. They dissociate in transport capture and pathological lock-in. A low-capacity state may be restorative, pharmacologically suppressed, or pathologically trapped. Part 3 makes that comparison with numbers @langell2026_reduced_capacity. The lesson for this part is conceptual: do not fold C, capture, and lock-in into one "dynamical complexity" score.

The refreshed multi-dataset reachability report supplies an important qualification. Its sleep estimates are strongly innovation-dominated: the reported $Q$ contribution stays above 0.94 through four tested prediction steps. Several resting clinical contrasts remain weak or unresolved, and its propofol surface fails that report's validity contract @langell2026_reachability_current. Those descriptive contraction rows are not positive predictive-spread evidence under that estimator. Results from another companion or export must retain their own qualification boundaries.

== What we still do not estimate here

Part 1 named two further questions and left them on the bench, and they stay there:

- *Committor:* toward which of two declared destinations is the process committed? That needs disjoint destinations, independent segments, and a qualified estimator. Stage labels are not committor truth.
- *Finite-amplitude resilience:* can a larger shove change the regime? Local Jacobian stability and spontaneous variation cannot substitute for an observed perturbation protocol.

Those remain questions. Naming them is part of the theory. Computing them as if they were already exports would be a category error.

#pagebreak()
#[
#set par(leading: 0.5em)
= What Can Change the Law at the Same Pin

== C3 is not "covariates help prediction"

If the pin does not fix the future-law, something else can. C3 asks whether nominated physiological or contextual variables change defined features of that law *at matched present state*. Adding a covariate that improves a regression is weaker than that.

Part 1 grouped candidate controls into fast rhythmic/access, history, and physiology. Here we put the body into the equations, then report what has actually been measured.

== A formal slot for the body

In the current theory, bodily measurements can enter context $c_t^"body"$ and potentially condition drift, stochastic spread or access routes. There is no requirement that every influence reduce to one universal scalar @langell2026ndt_current.

An earlier Embodied Anchoring formulation proposed a self-prior:

$ V(X,t) mapsto V(X,t) + lambda(t) V_"self"(X,s_t) $

Here $s_t$ represents bodily variables and $lambda(t)$ a proposed weighting. This is a modeling extension, expressed using Part 1's potential notation, not an empirically recovered bodily potential @langell2025_6. Windowed HRV proxies do not by themselves identify that weight, millisecond phase locking or the latent variance schedule.

Heartbeat and breath are therefore candidate contextual controls, not extra universal MNPS axes. Particular configured feature sets may include bodily proxies; that is a measurement choice, distinct from demonstrating causal control.

== What the two empirical tests actually showed

One task study (`ds003838`, up to 65 neural contributors and 62 with usable cardiac/anchor data, digit-span) found strong task-phase modulation of vagal index, and trajectory efficiency ranging from 0.04 at rest to 0.98 during easy memorization @langell2025_embodied. The RMSSD-driven vagal proxy peaked during listening; geometric trajectory efficiency peaked during easy encoding. Other cardiac indices need not share that maximum. Trajectory efficiency is net displacement relative to path length, not cognitive success or metabolic efficiency. Direct within-subject correlation between heart-rate and MNPS position, controlling for stage, was modest. Between-subject correlations died after FDR. The body tracks task phase. It has not been shown to steer moment-to-moment position.

The second test (`ds006848`) asked whether elevated manifold dynamics during encoding mean *success* @langell2025_itemupdating. They do not. Fast sequential presentation drove higher $m$ and $d$ than simultaneous display, and produced *worse* recall. After encoding ended, the conditions became geometrically indistinguishable. The dissociation is compatible with additional reconfiguration demand; the coordinates do not directly measure cognitive cost or explain why recall differed.

Together: physiology co-modulates with chart geometry at the scale of minutes and task phases. That is a C3-shaped *association*. It is not operator identification, and it is not a consciousness coordinate.

]

#pagebreak()
= When the Geometry Breaks — A Preview

The clinical companions ask whether these layers reveal useful group differences. Their patterns depend on cohort, task, reference and analysis. They are research contrasts, not a completed diagnostic atlas.

Some portraits below are already tied to dedicated cohort reports. Others remain geometric readings. Read them at different confidence levels.

*Depression* motivates questions about the shape of estimated spread and local deformation. Reported geometric differences do not by themselves show recirculating thoughts or establish a monotonic symptom marker.

*First-episode psychosis* produces real signal in a shared frame, but the layer that carries it shifts with dataset and medication. Cross-cohort differences constrain any claim of a single fingerprint; usefulness must be assessed for a specified task and population.

#block(fill: rgb("#fff8e1"), stroke: (left: 3pt + rgb("#f9a825")), inset: (left: 1em, right: 1em, top: 0.75em, bottom: 0.75em), radius: 3pt)[
  *Speculative interpretation*

  *PTSD and anxiety* invite hypotheses about persistent threat-related dynamics or altered bodily context. The cited analyses here do not test those hypotheses. A steep trauma basin or an amplified self-prior is a model proposal, not a measured mechanism or an inference from these disorders' names.
]

*At the acute extremes,* propofol and epilepsy bracket capacity loss with and without capture. Post-cardiac-arrest coma brings the same vocabulary into the ICU: differences in diffusion organization and predictive-spread dimensionality are recovery-linked without being a consciousness oracle.

Part 3 presents those comparisons with cohort exports, effect sizes, and bounds. The clinical question is the same as the theoretical one: *same place, different futures?*

#pagebreak()
= Reshaping Horizons — A Research Question

If an intervention changes a trajectory, which layer changed: present location, feature composition, local drift or finite-horizon spread? Did the geometric change accompany an independently measured improvement, and did it persist?

Those questions are useful without claiming that medication changes a particular potential, therapy rewrites a basin or bodily practice tunes a known control parameter. Competing mechanisms can produce similar observed changes. Longitudinal comparisons need declared outcomes, appropriate controls and estimates that generalize beyond the fitting data.

Rhythmic interventions offer one possible test because their timing can be manipulated. Spindle-related associations motivate such experiments but do not establish a treatment target or guarantee benefit @langell2026_spindle_windows. The present framework does not select treatments for individuals.

#pagebreak()


= The Arc of a Life

*Speculative extension.* The cited work does not provide a longitudinal MNPS atlas from birth to old age. The framework does not predict a developmental sequence merely by naming its coordinates.

A useful lifespan question would distinguish change in the recording from change in the process. If a feature's distribution changes with age, applying one reference might exaggerate differences, while fitting a separate reference at every age might erase them. The measurement frame is part of the question.

Likewise, a narrower predictive spread could reflect a more specialized task repertoire, a different physiological condition, an estimator limitation or a clinically consequential restriction. The geometry alone does not decide among them. Development and aging require age-appropriate measurements, longitudinal support and behavioral outcomes.

The personal intuition can remain: what is easy to do next changes across a life. But the theory does not yet translate that intuition into measured entropy spikes during tantrums, an adolescent Jacobian, or a universal healthy adult balance of $d_l$ and $d_n$.

At the end of life, neither a coordinate plot nor a diffusion equation settles questions about subjective experience. The current essays supply no validated test of awareness at that boundary. The scientific task is to state where the measurements remain meaningful, and where they stop supporting the interpretation.

#pagebreak()
= Implications, With the Baton Down

#block(fill: rgb("#fff8e1"), stroke: (left: 3pt + rgb("#f9a825")), inset: (left: 1em, right: 1em, top: 0.75em, bottom: 0.75em), radius: 3pt)[
  *Speculative extension*

  Philosophical and societal readings below are interpretations of the framework, not necessary conclusions and not validated applications.
]

== Self as flow, not as a noise term

The old free-will debate asks whether we are uncaused or machines. A better NDT-shaped option is narrower: we are path-dependent processes whose future-laws can be reshaped by practice, sleep, and environment.

You are not "free" in the sense of being outside the dynamics. You are not "free" because $sigma(t)$ is random either. A dice roll is unpredictable and has no agency. The framework can represent stochastic variation and history-dependent changes in access. Whether learning rewrites a potential or changes access while structure stays fixed is a separate empirical question. Neither random variation nor either history mechanism establishes agency.

A relatively persistent pattern of activity can serve as a metaphor for personal continuity. The chart does not establish that identity is topological or resolve competing accounts of the self. That philosophical reading adds an interpretation to the measured dynamics.

== Experience

NDT does not solve the hard problem. It does not say that denoising *is* consciousness viewed from inside. If, after matching state, responsiveness, arousal, power, and complexity, the future-law still failed to distinguish reported experience from its absence, NDT would remain a theory of enabling dynamics. That test is named. It has not been run.

== Science, not a civilization plan

The strongest scientific value is a shared measurement language for pin, texture, nudge, and horizon across sleep, anesthesia, task, and clinic. A cellular-scale hypothesis—that some routes stay easier to reopen because of slow dendritic accessibility—is a speculative substrate, not a required layer @langell2026_cytodendritic_accessibility.

The framework is strongest where it is tied to datasets, versioned contracts, and falsifiable comparisons. It is weakest where it drifts into mind-reading, city redesign, or the claim that we already know how to tune a life.

Habits, sleep, and social structure probably shape which trajectories become easy. That is not yet a philosophy of self-cultivation, and it is not a public-health program.

Questions about synthetic systems that might instantiate similar dynamics belong to a later part of the series, if at all. Current language models are not a test of NDT.

#pagebreak()
= The Pin Is Not the Future

I wake with a start, and for exactly one second I have no idea where I am.

We began there in Part 1. The opening dream gave us an intuition about a scene becoming recognizable. It did not measure a variance schedule, a shifted attractor or a control signal. We can now say more carefully what a study of such a transition would need to record.

The room becomes familiar, and the day begins. That is still a good intuition pump. It is still not a proof. And we can now add the sentence that Part 1 was written to earn: two people can share that waking pin and still differ in what happens next.

What this part added is the instruments for that sentence.

We learned that the pin has texture: the same $(m, d, e)$ can hide opposite movements in $d_l$ and $d_n$. We learned that a versioned contract is what makes a comparison a comparison. We learned that a small nudge is a different scientific object from drift, and that a short-horizon cloud is a different object from occupancy. We learned that the body can co-modulate the chart at the scale of task phases without being shown to write the melody. Sleep supplied concrete comparisons while showing why magnitude, shape and model validity must remain separate.

We also learned the limits. The Jacobian is a chart-level measurement. The predictive-spread ellipsoid is a second-moment summary, not a list of possible minds. Committors and finite-amplitude resilience remain questions. MNPS is a subway map. Using it as geology is how a measurement chart becomes a theory of soul.

The atlas remains a working collection of measurements and questions.

You are a process whose present location does not exhaust what can still happen. Some of that future structure can already be measured, in some regimes, under a named contract, with known failure modes. Most of it cannot yet. The atlas is being drawn. It is not a globe.

See you in Part 3, where the same questions meet disease.

#pagebreak()

= Technical Reference: The Nine Feature Slots <feature-reference>

Signal-derived labels are primary here. Older psychological names are historical aliases, not measurements of the named faculties. _Attentional Mobility_ does not directly measure voluntary attention; _Affective Mobility_ does not isolate emotion. _Network Diffusivity_ is not the stochastic diffusion tensor $a$, and _Local Coupling_ is not a direct count of neuronal connections. Similarly, an entropy-family slot need not measure timing disorder or metabolic efficiency merely because an older name suggests it.

The reference table below gives neutral labels for the cited contract; these editorial labels do not rename exported slots or change their formulas. An analysis must declare its actual configuration: some companion studies use different inputs or EEG-only replacements. A familiar coordinate name does not guarantee an identical measurement.

#figure(
  kind: table,
  clean-table(
    columns: (0.6fr, 1.4fr, 1.8fr),
    align: left,
    inset: 5pt,
    table.header([*Sub-coordinate*], [*Signal-derived label*], [*Reference feature mapping*]),
    [$m_a$], [Low-frequency power proxy], [$-0.5 dot$ delta power $- 0.5 dot$ theta power],
    [$m_e$], [Alpha-derived proxy], [$-1.0 dot$ alpha power],
    [$m_o$], [Beta/alpha ratio], [beta / alpha power ratio],
    [$d_n$], [Gamma-power proxy], [gamma power],
    [$d_l$], [Hjorth-mobility feature], [Hjorth mobility],
    [$d_s$], [Alpha/theta ratio], [alpha / theta power ratio],
    [$e_e$], [Permutation-entropy feature], [permutation entropy],
    [$e_s$], [Hjorth-complexity feature], [Hjorth complexity],
    [$e_m$], [Declared arousal-source proxy], [embodied arousal proxy],
  ),
  caption: [Reference name-to-feature mapping for the 9D chart described by @langell2026_neuralmanifolddynamics. Features are standardized before projection. Configured relative weights are $(0.62,0.55,0.45)$ for $m$, $(0.50,0.82,0.28)$ for $d$, and $(0.85,0.62,0.03)$ for $e$, in the displayed family order. Runtime projection L2-normalizes its columns and renormalizes available support. These are release parameters, not unnormalized equality formulas or a unique ontology.],
)

The $e_m$ proxy selects the first finite source in a declared hierarchy, from cardiac and other bodily measurements to EEG high-frequency power. Its recorded source can change across epochs or datasets. Reduced support also changes the projection's support class; it is not automatically equivalent to full support.

Read the table together with the study configuration before interpreting a 9D result. When Part 3 says a psychosis cohort shifted on $m_o$, it means the beta/alpha ratio moved under one contract. The metaphor is a reading aid. The feature is the measurement.

Historical aliases, in slot order, are Attentional Mobility, Affective Mobility, Oscillatory Flexibility; Network Diffusivity, Local Coupling, Representational Dispersion; Dynamic Entropy, Phase Entropy, and Efficiency Proxy. They are included to help read older reports, not as primary scientific labels.

#pagebreak()

= Glossary (Part 2)

*Canalization* — Concentrated predictive spread in a declared chart and model. It does not by itself establish behavioral rigidity or a restricted set of physically possible states.

*Chart-level Jacobian ($J$)* — Local derivative of flow in a declared measurement chart. Stretch, shrink, shear, rotation of nearby states after a small nudge. Not an intrinsic brain-manifold tensor.

*C1 / C2 / C3* — Reduced-state insufficiency for the latent law; reproducible held-out information from chart-future summaries beyond standard baselines; specified conditional-control effects at matched chart state beyond ordinary covariates.

*Cohort- vs subject-anchored coordinates* — Shared cohort reference versus a declared subject/session reference. Different questions. Different frames.

*Effective dimensionality ($d_"eff"$)* — A summary of how evenly covariance eigenvalues distribute predictive spread across directions; not a count of mental options.

*Event-locked vs block-native* — Transient-aligned comparison versus condition-level summary. Spindles require the first.

*NeuralManifoldDynamics* — Versioned measurement contract. Not the theory.

*Predictive spread (stochastic reachability in the companion research)* — Short-horizon second-moment model-implied spread of next states. Not occupancy, not classical controllability, not a consciousness scalar.

*Reactivity gap* — Room between instantaneous growth ($omega$) and modal growth ($alpha$). Non-normal transients, not eigenvalue slowing.

*Stratified MNPS* — Nine configured feature coordinates projected to $[m,d,e]$. Finer measurement detail, not nine identified mental faculties.

#pagebreak()

= References

#context {
  set par(leading: 0.5em)
  bibliography("references.bib")
}

#pagebreak()

== Acknowledgments
This work emerged through structured correspondence among human and AI collaborators; large language models from OpenAI, Anthropic, and Google assisted in literature synthesis, drafting, peer review, and editorial refinement. We also gratefully acknowledge the original investigators, clinical teams, participants, and data stewards who created, curated, and shared the public datasets and metadata that made these analyses possible.

We extend our gratitude to the *OpenNeuro* platform and the *Stanford Center for Reproducible Neuroscience* for access to high-quality neuroimaging data, and to the *Center for Open Science* for the sleep-cohort infrastructure used in companion analyses.

= Contact

Robin Langell — hello(at)noeticdiffusion.com

= Licensing

This manuscript provides only a brief licensing summary; full terms are available via the Mychainos multi-layer licensing framework (`https://noeticdiffusion.com/license.html`). Conceptual content: CC BY-SA 4.0. Software: GPLv3. Unified ethical guardrails apply: no coercive, military, or surveillance applications.

= Data and Code Availability


Reference implementations: `https://github.com/NoeticDiffusion` 

The bibliography distinguishes public records from the local working revisions consulted here.
