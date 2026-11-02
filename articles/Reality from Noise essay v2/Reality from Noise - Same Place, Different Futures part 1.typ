// Reality from Noise: Same Place, Different Futures
// A popular science essay on Noetic Diffusion Theory (NDT v2 framing)
// Author: Robin Langell, 2026

#import "template.typ": essay-template, clean-table

#show: doc => essay-template(
  title: text(hyphenate: false)[Reality from Noise:\ Same Place, Different Futures],
  subtitle: [Part 1: How Your Brain Charts What Happens Next],
  author: [Robin Langell],
  date: [2026],
  series-description: [An illustrated research essay on Noetic Diffusion Theory],
  doc,
)

== Reader's Guide to the Essay

This essay presents *Noetic Diffusion Theory (NDT)*—a framework for understanding mind-relevant neural regimes not only by *where they sit*, but by *what can still happen from there*, and by *what processes change those possibilities*. Earlier versions of this work treated rhythmic reconstruction as the primary story: the brain denoising chaos into meaning on a learned geometric landscape. That picture remains useful. It is no longer the whole theory @langell2025_6 @langell2026ndt_current.

The present formulation asks a broader dynamical question. Given a measured state now, what distribution of nearby futures remains available? And what can reshape that distribution without simply moving the pin on the map?

The first three parts of the essay develop the neuroscience argument:

This is a research-facing long-form essay. Its main thread is *present state → local law → possible futures → control of futures*. Read Part 1 for that thread, Part 2 for the measurement objects, and the three-sentence portrait summaries in Part 3 for the empirical picture. Equations, feature mappings and detailed cohort results provide a technical reading route. Part 4 is a companion on synthetic systems; engineering demonstrations there do not validate the neuroscience argument.

*Part 1: Same Place, Different Futures*
Here we build the instrument and the intuition. A GPS pin answers one question—*where?*—and leaves others open. We keep the orchestra metaphor, but we now use it as a way to talk about *candidate controls*: heartbeat and breath as physiology, theta–gamma coupling as fast rhythmic access, sleep spindles as a candidate nightly control. We introduce a first map of state (Meta-Noetic Phase Space, or MNPS) and a minimal dynamical recipe. We also present early tests of cardiac and neural co-variation, and newer overnight evidence separating event timing, fluctuation magnitude and directional shape.

*Part 2: Texture, Nudge, and Nearby Horizons*
Here we look under the hood with greater precision. Stratified MNPS is a more detailed measurement chart. A Jacobian describes local drift deformation, where its estimation is justified. Short-horizon predictive spread summarizes model-implied variation in next states, not occupancy. NeuralManifoldDynamics is the versioned contract that makes those numbers auditable. The body is treated as a candidate C3 control, not an extra axis.

*Part 3: When the Horizon Narrows*
Here we test the same questions against disease. Sleep (spindle events, stage-level predictive spread, capacity versus capture), depression, first-episode psychosis, Parkinson disease, cardiac-arrest coma, and Alzheimer/FTD—tracking which *layer* moves, what holds, and what remains uncertain.

The appendix and glossary at the end of this document are intended as shared reference material for the essay series, not just for Part 1.

*A Note on Evidence*

The theory distinguishes five kinds of statement: established external findings; internally checked measurements or simulations; plausible interpretations; speculative extensions; and tested paths that failed or remain limited by the method @langell2026ndt_current. We keep those distinctions here. An event-associated EEG change can be reproducible while its proposed explanation remains uncertain. A null or failed test belongs in the story too.

There is a second distinction: what a result establishes. An association, discrimination between mechanisms, preservation of a known ordering, and recovery of a dynamical operator answer different questions. A successful classifier does not automatically identify the rule that moves the system. A mathematical proof under explicit assumptions does not establish that a brain meets those assumptions.

This essay follows the current working theory and selected companion reports. The evidence constrains particular layers; no dataset has validated the whole chain from biological control to measured accessibility to experience.

The atlas is being drawn, not complete.

#block(
  breakable: false,
  fill: rgb("#f2f6f8"),
  stroke: (left: 3pt + rgb("#52788a")),
  inset: 1em,
  radius: 4pt,
)[
  #set par(first-line-indent: 0pt, leading: 0.5em)
  == Mini Glossary: Signal, Map, and Pin

  *EEG (electroencephalography)* records changes in electrical voltage through electrodes on the scalp. It gives us signals from which to calculate features of brain activity.

  *MNPS (Meta-Noetic Phase Space)* is the measurement map used in this essay. Selected signal features are summarized as three coordinates, $[m,d,e]$, describing mobility/coordination, deviation, and entropy-related properties. These are computed summaries, not a complete description of the brain or its thoughts.

  *The pin* is one measured location in MNPS: a particular set of $[m,d,e]$ values for a recording window. Like a GPS marker, it tells us where we are on the map. Here the map is a space of measurements, not a physical place inside the brain. A sequence of pins traces a trajectory.

  The detailed coordinate definitions come in @mnps-three-coordinates. For now: *EEG supplies the signal; MNPS supplies the map; the pin marks the measured state.*
]

Let's begin.

#v(2em)

---

#v(2em)

#figure(
  image("figures/ndt_v.1/fig_s4_5_story_strip_v2.png", width: 100%),
  caption: [*Schematic.* A reading map for this essay. Each panel is a different question about the same moment: where you are, which way the ground slopes, how fluctuations spread, what nearby futures remain open, and what can change those possibilities without moving the pin.],
)

#pagebreak()
== Evidence Ledger: Where the Burden Lies

C1 motivates the question. *C2 and C3 carry the distinctive empirical burden.* Losing information in a reduced map is unsurprising; showing that a specified future-law summary adds useful information, or that a nominated control changes it, requires further evidence. This ledger summarizes the studies discussed in the series, not every possible test of NDT @langell2026ndt_current.

#clean-table(
  columns: (0.65fr, 1.2fr, 3.2fr),
  inset: 7pt,
  align: left,
  table.header([*Claim*], [*Status here*], [*Evidence and remaining test*]),
  [*C1*], [Illustrative projection; latent claim untested],
  [A many-to-one projection can discard information. Different group means or sleep labels do not demonstrate different latent future laws at the same reduced state. That requires an explicit sufficiency test with access to a qualified reference law.],
  [*C2*], [Limited probes; full test not demonstrated],
  [Some reports test classifier increments or nonredundancy against selected comparators. A gain from event-level chart features is not itself a test of future-law information. The decisive test must predeclare future-law summaries, current location, ordinary static and spectral baselines, and replicate the added information on held-out observations.],
  [*C3*], [Full matched-state control test not yet demonstrated],
  [Bodily covariation and event associations motivate candidate controls; several tests are null or inconclusive. A prospective test must nominate the control and future-law feature, compare matched chart states, account for ordinary covariates, and distinguish an intervention effect from better prediction by context alone.],
)

A positive chart contrast is not automatically a pass on any of these commitments. Failed estimators and unresolved comparisons stay visible in Parts 2 and 3. The synthetic pilot in Part 4 is a separate engineering result, not a substitute for the biological C3 test.

*Reading the figures.* Watercolor terrain is metaphor only. An MNPS pin is a computed measurement summary; arrows, clouds and ellipsoids may be schematic or model-estimated objects. Captions identify the relevant status and data source. Illustration detail is not evidence of a physically mapped landscape, and neither a measured chart nor an estimated ellipsoid is the latent brain state.

#pagebreak()


= Dreaming of Structure

== The Space Station Dream

I wake with a start, and for exactly one second—perhaps less—I have absolutely no idea where I am.

In my dream, I was trapped on a space station. It was cramped, claustrophobic, the walls pressing in on all sides. Then, without warning, new modules began appearing from nowhere—just materializing in the void like soap bubbles forming in mid-air. People walked through them, ordinary people in everyday clothes, stepping casually into my floating prison as if they'd just taken the bus. I remember the confusion most clearly: _Shouldn't they have arrived on a shuttle? How did they get here?_ They didn't seem to notice anything odd. They couldn't see me, or perhaps I couldn't see them properly. Was I a ghost? Were they?

Then I opened my eyes.

For that brief, disorienting moment, the bedroom around me was pure noise—shapes, shadows, the vague awareness of a ceiling, a window, fabric. My mind grasped desperately for context. _Where am I? What time is it? What day is it? Who am I?_

And then, like a camera lens snapping into focus, the world reconstructed itself. The shadows resolved into my bedside table. The fabric became my duvet. The formless anxiety crystallized into the memory of today's deadline. In perhaps two seconds, I went from complete disorientation to lying in my familiar bedroom, fully inhabiting my familiar life, already thinking about coffee.

This transition—from noise to meaning, from chaos to clarity—happened so fast I almost didn't notice it. But it happened. Something in my brain took the raw, ambiguous sensory data and _constructed_ a coherent world. Not passively, like a movie projector displaying a pre-recorded film, but through a rapid change in what the scene meant to me.

That moment is a good *intuition pump*. It is not a proof. It shows that a usable world can be assembled from ambiguous input. The scientific question is slightly different, and larger.

== Same Place, Different Futures

The bedroom has not moved. Yet my relationship to it changes completely: first disorientation, then recognition, then the ability to get up and begin the day. The anecdote invites a question about transitions, rather than providing their mechanism.

Now imagine two observations that look similar on a coarse neural map. Do they lead to the same distribution of next states? Could a change of context make one route more likely without first moving the measured pin?

NDT separates "here" from "what can happen from here" @langell2026ndt_current. It predicts that, in some neural regimes, measured features of future dynamics add reproducible information beyond current location and ordinary static or spectral summaries. That prediction is stronger than observing that two groups occupy different parts of a chart.

#figure(
  image("figures/ndt_v.1/fig_s4_1_same_place_different_futures_v2.png", width: 100%),
  caption: [*Schematic.* Same measured state, different future law. Matching the present pin does not imply matching drift, stochastic spread, destination probabilities, or short-horizon transition structure. The pin answers *where*. It does not, by itself, answer *what happens next*.],
)

That is the organizing question of this essay. Earlier NDT used rhythmic reconstruction as its primary explanatory framing @langell2025_6. The present formulation still needs rhythm—badly, as we will see during sleep—but it no longer *identifies* the theory with a single denoising mechanism. Rhythm is one of the clearest candidate controls that can reshape the distribution of nearby futures. It is not the whole theory.

== The Idea: A Forecast as Well as a Map

A map tells you where you stand. A forecast tells you what may happen there. Knowing the location does not give you the wind, and knowing the average wind does not tell you how widely the next gust might vary.

NDT proposes a similar distinction for neural dynamics. Present state, systematic movement, fluctuations and destination probabilities describe different aspects of an evolving process. Two clouds of possible futures can cover the same territory while giving very different probabilities to the places inside it. Accessibility therefore means more than a list of reachable points.

Think of two doors that both remain open. In one condition, almost every visitor takes the left door; in another, most take the right. The set of open doors has not changed, but the future law has. Likewise, a small change in context could redirect a neural trajectory while its present measured coordinates remain similar.

Rhythm enters this picture as one possible control. The earlier denoising story imagined alternating periods of stabilization and exploration. The current theory places that image inside a broader model: controls may change the direction of movement, the size and orientation of fluctuations, or the ease of particular routes. A single dial between order and noise cannot describe all of those changes.

The word _noetic_ identifies the theory's interest in mind-relevant neural dynamics. It does not mean that an EEG coordinate contains a thought, measures meaning, or reveals whether someone is aware. The theory asks about the organization that may enable cognition and experience; it does not identify that organization with experience itself @langell2026ndt_current.

== Why This Matters

Consider what an intervention might need to change. Moving the average state, reducing fluctuations and changing the likelihood of leaving a persistent pattern are different objectives. A description that keeps those objectives separate could help formulate more precise experiments.

That is the motivation for studying sleep, task engagement, anesthesia and clinical conditions together. A reduced local horizon can accompany physiological sleep, sedation or seizure, while the accompanying transport and deformation measures differ @langell2026_reduced_capacity. A shared reduction does not make those regimes equivalent.

The same discipline applies to mental-health examples. Persistent returns to a pattern or unstable transitions are useful dynamical questions. They are not established geometric explanations of depression, psychosis or trauma, and they do not yet specify a treatment.

NDT's nearer promise is a way to ask and test those questions. Could an estimated local law predict the next part of a recording? Would a nominated control change that prediction at a matched measured state? Would the result survive comparison with ordinary power, complexity, movement and arousal measures?

Those tests concern neural organization. Whether they also distinguish reported experience from no reported experience within the same physiological regime is a separate, still-open test. A better forecast of brain activity would be valuable even before that stronger question is answered.

== The Journey Ahead

This essay is an invitation to see yourself differently—not as a static being observing a fixed reality, but as a dynamic pattern whose present location does not exhaust what can still happen. We are not nouns but verbs, not objects but processes, not observers but composers.

We'll start with a metaphor—the orchestra—to build intuition for the *controls* that can reshape a future-law. We'll explore sleep as a setting where rhythms and measured dynamics change together. We'll look under the hood at the model: a rule for movement, a description of fluctuations, and controls that can affect both. Then we'll ask what a measurement chart can reveal about that rule, and why Part 2 needs more than a map of visited states.

The coordinates are set. The atlas is being drawn. The symphony is playing.

Let's listen.

#pagebreak()


= Rhythm as a Candidate Control

== The Orchestration of Signals

Imagine standing in a concert hall. The orchestra is warming up—a cacophony of disconnected sounds. Violins squeak through scales. The timpani rumbles. A clarinet tests a trill. Each musician plays their own fragment, creating a soup of noise that would make any composer weep.

Then the conductor raises the baton. Silence falls. The baton drops, and suddenly—impossibly—all that chaos becomes Beethoven's Fifth. Dozens of instruments, hundreds of moving parts, thousands of individual notes, all coordinating in time to create something far greater than their sum.

But listen closer. It isn't just a wall of sound. It is a rich, layered structure. You can hear the "local chatter" of the violins playing in tight unison, distinct from the "global sweep" of the brass carrying the theme across the hall. You can hear the texture changing—sometimes dense and knotted, sometimes airy and expansive. And if you watch the conductor, you see something else: they aren't just keeping time. They are listening, adapting, shaping the flow of the performance in real-time. They are managing the dynamics of the dynamics.

The orchestra is an image of coordination across timescales. In the neural case, the coordination is distributed: no single conductor needs to know the whole score. Different circuits and bodily conditions may affect different aspects of the performance.

In the updated theory, the orchestra is not the definition of NDT. It is a way to talk about *what can reshape the distribution of nearby futures without simply moving the present pin*. The technical paper groups those somethings into a few classes, not a catalogue of subsystems @langell2026ndt_current:

- *Fast rhythmic and access control.* A rhythm that turns noise up or down, or a thalamic gate that opens a channel.
- *History.* A stored landscape of preferences, and—separately—whether a context operator can still change which routes are easy while the hills stay fixed.
- *Physiology.* Heartbeat, breath, and metabolic adequacy, which may condition what is feasible, as a bass line conditions a room without composing the melody.

Let's meet those candidate controls.

== The Foundation: Embodied Anchoring

Every orchestra needs a foundation—the double basses, the cellos, sometimes a piano providing the harmonic ground. In the orchestra of your mind, this role is played by something even more fundamental: your heartbeat.

Right now, your heartbeat and breathing continue alongside whatever you are thinking. Their rhythms vary, but they provide recurring bodily signals with which neural activity can interact.

Researchers can measure neural responses aligned to the heartbeat, often discussed as heartbeat-evoked potentials, or HEPs. Work on these responses and on interoceptive regions such as the insula links bodily sensing to aspects of perception and self-related processing @park2019. The orchestra's bass line is an image for this continuing exchange, rather than a master clock for everything the brain does.

That exchange motivates a question about feeling grounded or detached: could altered processing of bodily signals contribute to those experiences? A heartbeat-related response is not, by itself, a calibrated dial of presence or a diagnosis of detachment.

Breathing adds another timescale to that exchange. The question for NDT is whether bodily state helps condition neural transitions, and whether any such contribution remains after accounting for arousal and other covariates.

The current theory places candidate bodily influences in a contextual control variable, $c_t^"body"$. Older NDT writing used the self-prior notation $lambda(t)$. The newer framing does not require one universal bodily scalar: cardiac state, breathing phase and slower metabolic constraints can affect different questions. Nor does including a bodily feature in a measurement chart demonstrate that the body controls the resulting dynamics @langell2026ndt_current.

For now, just remember: the orchestra of experience has roots. It doesn't float free. It's anchored in the flesh.

=== The Bass Line Put to the Test

One internal study brought the bodily-context question into a working-memory task. It recorded brain activity, heart rhythms, pulse responses and pupil diameter in up to 65 healthy adults; 62 contributed usable cardiac/anchor data @langell2025_embodied.

The task was elegant in its simplicity. Participants first listened passively to a series of numbers. Then they memorized five, then nine, then thirteen of them in sequence—each stage pressing harder on working memory. Four minutes of resting baseline bracketed everything.

Here is what happened to the cardiac signal—the bass line.

During passive _listening_, the RMSSD-driven vagal proxy was higher than during active memorization. The source reports raw RMSSD of 48.9 ms during listening and 39.7 ms during thirteen-digit memorization; another HRV measure, pNN50, instead peaked at rest. The large standardized listen-versus-pooled-memorization contrast, 2.085, belongs to a scaled composite. It is not a direct gauge of calmness or sympathetic takeover.

The brain's trajectory also changed. A measure called _trajectory efficiency_—net displacement relative to total path length—ranged from 0.04 at rest to 0.98 during five-digit memorization. The name is geometric: a straighter path is not automatically better cognition, and its value depends on how the trajectory is sampled.

The interesting feature is the offset. The autonomic proxy peaked during listening; trajectory efficiency peaked during the easiest active memory condition. Both varied with task phase, but their maxima occurred in different phases. That fits the idea that bodily context and neural processing need not vary in lockstep. It does not establish that the cardiac change caused the neural change, led it in time, or altered a future law at a matched pin.

#figure(
  image("figures/ndt_v.1/fig_s4_3_control_matched_state_v2.png", width: 100%),
  caption: [*Hypothesis schematic.* Conditional accessibility. Context, history, or physiology can change the future law among observations that sit at the same present pin. In the strongest version of the idea, even the underlying landscape may remain unchanged while access to routes changes.],
)

Direct within-person coupling between the tested anchor indices and MNPS was modest, and between-person correlations did not survive correction. Task-related co-variation is the supported finding. In the orchestra metaphor, the bass and melody respond to the same movement; this study does not identify which directs the other.

A follow-up study added another dimension to this picture @langell2025_itemupdating. When participants memorized seven digits displayed all at once versus rapidly one by one, their neural manifold dynamics were dramatically more active during rapid sequential presentation—even though simultaneous display actually produced _better_ memory performance. In other words, the brain "worked harder" geometrically when items arrived quickly, even when that hard work yielded lower recall. Elevated dynamics during encoding therefore reflect _how demanding the process is_, not _how successful it will be_.

This dissociation matters for how we understand the body-brain link. Bodily state may help shape the processing context, but that causal role remains a hypothesis here. What happens inside that context—how efficiently items are actually stored—depends on many other factors. The orchestra's bass line shapes the acoustic conditions; whether the performance earns an ovation depends on the whole ensemble.

These studies constrain the bodily-context hypothesis at the level of measured co-variation. The stronger conditional-control test remains to be established: does a predefined bodily variable change a feature of future dynamics at a matched chart state, beyond ordinary nuisance covariates?

== Nested Rhythms: Theta and Gamma

Now listen to the rhythm section. A slow beat can organize several faster notes without dictating what every note must mean.

Theta and gamma provide a neural example: activity in a faster gamma band can vary with the phase of a slower theta rhythm. This _phase-amplitude coupling_ is a relationship between measured rhythms. It does not specify a universal moment when information enters consciousness.

Lisman and Jensen's theta–gamma coding account proposes that different items can be organized within successive gamma subcycles of a theta cycle. Evidence is especially clear for spatial coding in the hippocampus, and the account motivates questions about how rhythms organize memory @lisman2013. It does not establish that every gamma burst encodes one perceptual detail or that experience refreshes at a fixed rate.

For NDT, such coordination motivates a candidate control of dynamics. The minimal Rhythmic Variance Control model asks what follows if a rhythmic proxy reduces stochastic amplitude. The broader theory also allows rhythmic influences on drift and directional spread. Establishing one of those roles requires testing a specified proxy against alternative explanations; detecting coupling alone does not identify it @langell2026ndt_current.

== Coordinated Events: Slow Oscillations and Spindles

At night, the orchestra changes its timing. Slow oscillations alternate between relatively active and quiet periods. Sleep spindles are brief thalamocortical bursts, typically around 11–16 Hz, which can align with phases of those slower waves. Hippocampal ripples can nest within this coordination, linking rhythms at several timescales @staresina2023.

Imagine a conductor preparing an entrance, a section joining, and a soloist finding a moment within the shared rhythm. The analogy concerns coordinated opportunities for activity; it does not imply that every spindle is perfectly synchronized across the brain or that each one performs a discrete memory save.

For NDT, these events are candidate controls: possible ways to change the conditions under which neural activity unfolds. The measurements so far show event-associated shifts in EEG-derived coordinates. Establishing a change in a future law, or a causal improvement in memory, takes another test @langell2026_spindle_windows.

The newer sleep work also asks which moment of an event matters. Its start, its amplitude peak, and the surrounding slow wave can have different relationships with heartbeat and breath. We will return to that distinction in "The Nightly Renovation."

== One State, Several Questions

Before we turn the orchestra into an equation, we need a clearer picture of what the pin on the map *does not* tell us.

Imagine a hiker on a ridge in fog. A GPS pin answers one question: *where?* That pin does not answer the others.

1. *Where is the system?* A low-dimensional chart—in this theory, MNPS, with three operational feature families, $[m,d,e]$, each built from a specified family of signal features—reports a location. Two recordings can occupy similar coordinates and still differ in what happens next. The chart is a *map*. It is not the latent neural process, and it is not NDT.

2. *Which way does the ground slope?* Local drift is the systematic tendency of motion: downhill on a potential, around a cycle, or along some other flow. This is the part the orchestra's "score" is trying to capture.

3. *How does the weather spread?* Stochastic diffusion is not a single noise knob. It has size, shape, and preferred directions. Two states can share a slope and differ in how fluctuations fan out—a narrow corridor versus a broad fan. Rhythmic Variance Control, in its simplest form, turns that weather up or down.

There are further questions: how local drift deforms a small displacement (a Jacobian); how uncertainty spreads over a chosen horizon; which destination is reached first (a committor); and whether a larger perturbation changes the regime. A forecast at a fixed time, a first-arrival probability and a response to an intervention are different objects. They belong to the same controlled process, but cannot all be recovered from one endpoint distribution. Part 2 develops these distinctions.

#figure(
  image("figures/ndt_v.1/fig_s4_2_one_state_questions_v2.png", width: 100%),
  caption: [*Schematic.* The same moment supports non-equivalent dynamical questions. This essay stays with the first three: location, local drift, and how fluctuations spread. The remaining panels—nudge, short-horizon cloud, destination, larger shove—are the work of Parts 2 and 3.],
)

The theory makes three commitments @langell2026ndt_current:

- *C1 — reduced-state insufficiency.* A measured pin need not determine the latent process's future law.
- *C2 — non-redundant accessibility.* In some regimes, summaries of measured future dynamics should add reproducible information on held-out data beyond current chart location and standard static or spectral summaries.
- *C3 — conditional control.* Predefined context, history or physiological variables can change nominated features of the measured future law among observations matched on current chart state, beyond standard state, spectral and nuisance covariates.

The first point concerns a _reduced_ chart. If we knew a complete Markov state and the future control protocol, that state would determine its conditional future law. NDT is not claiming otherwise. In an experiment, however, the pin is a partial observation, and the relevant context may include recent history or a changing control protocol over the interval ahead.

C1 alone is therefore not distinctive; coarse measurements commonly leave things out. C2 and C3 carry the stronger empirical burden. Another feature improving a classifier is not enough to establish either one, and a conditional association is not automatically causal identification.

Rhythm, thalamus, history, body and metabolism are candidate influences on this law. They are not extra definitions of NDT.

== The Score: The Potential Landscape

Every orchestra has some organization that persists beyond the current note: a score, a learned theme, a shared expectation. In the simplest dynamical model, a _potential landscape_, $V(X,t)$, gives one way to describe a persistent tendency.

Imagine a ball on a hillside. The local slope makes some movement easier than other movement. A valley can stand for a pattern the system tends to approach. The image is useful for thinking about recurring thoughts, but the mathematical valley does not itself contain meaning, and not every neural flow can be represented as downhill motion alone.

The theory writes this potential as $V$. It does not define it as a combination of MNPS coordinates. The shape of a potential and the ease of movement across it are separate ingredients: changing the routes need not mean rewriting the hills.

The score captures one part of the recipe: a tendency of motion. The next ingredient determines how much variation accompanies it.

== The Variance Schedule: Room for Variation

Think of musicians following a theme while allowing more or less improvisation. In the minimal model, the stochastic amplitude $sigma(t)$ plays that role. A candidate rhythmic variable, $r(t)$, adjusts it: higher $r(t)$ permits less stochastic variation, lower $r(t)$ permits more.

The orchestra metaphor calls these tighter and looser modes of playing. It does not give us a direct reading of someone's concentration or creativity. Whether a recorded rhythm acts like this control is something to test, and a control may affect the direction of movement as well as its variability.

== What the Orchestra Metaphor Can Ask

The orchestra groups candidate influences by timescale: heartbeat and breath, faster neural rhythms, and coordinated sleep events. It does not define a healthy state in which every influence is synchronized. More regularity or tighter coupling need not mean better perception, mood or function.

Its useful question is narrower: could a change in one nominated influence alter what happens next without a large shift of the measured pin? That is a C3 question. A clinical interpretation would additionally need independently measured symptoms or function, appropriate comparisons and evidence that generalizes beyond the fitted recording.

Before returning to clinical differences, we can watch coordination change within an ordinary night. Sleep lets us examine rhythms at several timescales without assuming in advance that they all perform the same operation.

Sleep lets us ask how present state, local dynamics and estimated nearby futures change together.

#pagebreak()


= Why Sleep Matters—The Nightly Renovation

== A Building That Stays Alive

Imagine a library closing for the night. The visitors leave, the doors shut, and the building becomes quiet. From the street, it looks as though nothing is happening.

Inside, the work changes. Books return to shelves. A passage is cleared. Some rooms close while others remain in use. The building has not moved, but what can happen inside it depends on more than its address.

That is a useful way to approach sleep. The brain remains active while its relationship with the outside world changes. Rhythms that were background players become prominent; different forms of coordination take turns. The question for NDT is what these changes do to the organization of neural activity, and eventually to the possibilities available after waking.

The word _renovation_ is a metaphor for that research question. We can measure changes during the night. Establishing that a particular change rebuilds memory, improves tomorrow's thinking, or rewrites a neural landscape requires additional evidence. The newer sleep studies make the story richer precisely because they separate these questions.

== The First Clue: An Entropy Drop

An earlier internal validation study followed 44 adults across 74 nights in two cohorts @langell2025_4. It reported a decrease in spectral entropy around detected slow-oscillation–spindle events: an average relative reduction of 48.2% in the primary cohort and 44.1% in the replication cohort, with reported standardized effect sizes of 0.49 and 0.28. The study reported the pattern as statistically significant in 98% of the primary cohort's 50 nights. Event counts were on the order of several hundred per night, with substantial variation and dependence on detector settings.

What does that mean? Spectral entropy asks how evenly signal power is distributed across frequencies. When activity becomes concentrated in a rhythm, that number can fall. A spindle is itself a rhythmic burst, so an entropy drop around a detected spindle is an informative observation with an important built-in connection to how the event was selected.

It does not mean that half of the brain's confusion has disappeared. It does not count memories saved, measure subjective clarity, or show that entropy keeps descending like a staircase throughout the night. These are local signal changes around events. Their explanation needs controls that preserve the relevant spectral and temporal structure.

#figure(
  image("figures/Sleep_Cohort_stages.png", width: 100%),
  caption: [*Measured chart: sleep-stage occupancy.* Pooled observations from 74 nights, shown separately for Wake, REM, N2 and N3. The nested surfaces describe frequently and less frequently visited regions. This figure uses the validation study's earlier chart, rather than the current canonical $[m,d,e]$ coordinates. It shows where observations accumulated; it does not measure the set of futures available from any one observation.],
)

The first map gave us a reason to look closer. The next question was whether a spindle changes the measured state even when we compare it with other moments in the same sleep stage.

== Inside N2: The Event and Its Neighborhood

Imagine watching the library from above. Comparing an open afternoon with a closed night tells you something about the building. Comparing the moment a librarian moves a trolley with the moment just before tells you something more specific about the action.

An event-window study in BOAS, the OpenNeuro ds005555 sleep dataset, made that closer comparison @langell2026_spindle_windows. That earlier report found differences in MNPS, strongest in its $d$-labelled endpoint family, relative to both the event's earlier baseline and matched non-spindle N2 windows. The later cross-dataset work below narrows the reproducible timing claim and shows why the matched-control contrast cannot be generalized in the same way. The paper called this a deviation family; its historical interpretation should not be substituted for the feature definitions introduced later in this essay. Time-shifted pseudo-events did not reproduce the positive effect. Geometry added a small amount of classification information beyond an already strong spectral-power baseline: in the EEG-channel C3 analysis, ROC-AUC rose from 0.953 to 0.956. The event has a measurable signature, but much of its distinguishability is already in the spectrum.

A later study separated two questions that the phrase "spindle effect" can conceal @langell2026_rvc_sleep_revision:

- *Timing:* How does the event window differ from that same event's pre-spindle baseline?
- *Neighborhood:* How does it differ from a matched non-spindle N2 window elsewhere in the recording?

#figure(
  image("figures/ndt_v.1/fig_p1_event_neighborhood_v2.png", width: 100%),
  caption: [Two schematic comparisons within N2. Timing compares a 30-second window containing the spindle with its own earlier baseline; neighborhood uses separately matched non-spindle windows. The waveforms and map patches illustrate the comparisons, not event-resolved MNPS measurements or a causal effect.],
)

These comparisons need not agree. A neighborhood may already be different before a spindle starts. In the later analysis, several event-versus-control differences reflected those pre-existing differences; one coordinate even changed comparison direction between datasets. Treating every difference from generic N2 as a change produced at spindle time would have told the wrong story.

The within-event timing result was more consistent: the study's $d_n$ endpoint increased in ANPHY and BOAS, with permutation-adjusted $q$ values of 0.009 and 0.011. In ANPHY, a companion conventional confidence interval still included zero. RichSleep, the third dataset, had only 160 paired events available for this test and was inconclusive ($q = 0.72$). That is support in two datasets and an unresolved third test. The BOAS analyses also reuse a source dataset; they are not separate independent replications of one another.

Those coordinate names belong to the studies' specified feature mappings. They should not be read as direct measurements of an optimal brain-network balance, nor should the EEG-only event study's coordinates be silently substituted for the multimodal chart used elsewhere. Its 30-second measurement windows also cannot resolve every step inside a roughly one-second spindle.

Still, something useful has emerged. N2 is not one uniform room. It contains brief events and changing neighborhoods. We can begin to distinguish an event's local signature from the background in which it occurs.

== The Body Keeps More Than One Clock

Now listen for the bass line again.

The later spindle study asked whether heart and breathing state in the preceding minutes predicted the size of the EEG geometry change. Under the tested composite measures, it found no detectable moderation, including in RichSleep with both cardiac and respiratory recordings. That limits the simple story in which a stronger bodily anchor automatically produces a stronger spindle-related change @langell2026_rvc_sleep_revision.

But a body's condition over several minutes and its phase within one breath are different questions. A room can have the same average sound level while a note lands on a different beat.

A follow-up examined the full RichSleep catalog: 23,029 detected spindles from 24 people @langell2026_rvc_peak_revision. The moment of maximum spindle amplitude showed a small but consistent population-level preference for a respiratory phase. The cardiac counterpart was weaker and less robust. Spindle onset did not show the same robust pattern. Breathing was more clearly associated with the crest of the event than with its beginning.

The next analysis widened the view to other rhythms in the same sleepers @langell2026_richsleep_carriers_revision. Slow-oscillation troughs and upstates showed stronger autonomic phase-locking than the spindle-peak result; the tested REM-theta events showed none. Tests of spindle onset disagreed when the researchers changed the null model—the comparison used to decide what chance timing should look like. Onset therefore remains sensitive to the method, rather than a settled universal absence or presence of coupling.

This is a more specific picture of embodiment: different neural events can relate differently to the body's clocks. The beat may matter at one point in an event and scarcely at another. A small secondary analysis suggested that respiratory alignment might also relate to the size of a geometry change, but that result remains fragile. A later test found no detectable change in that alignment–geometry association with spindle strength; it did not establish that strength has no effects of its own. These reports share RichSleep data and are successive analyses, not independent replications.

The distinction matters. *When a rhythm peaks*, *how much the measured state changes*, and *whether a memory improves* are three different outcomes. The newer findings make bodily timing a sharper candidate mechanism without turning it into a demonstrated controller of memory or nearby futures.

== NREM: Quiet Does Not Mean Locked

Back in the library, some routes are temporarily quieter. That can be compatible with useful work. A closed reading room and a jammed emergency exit both restrict movement, but they are very different kinds of restriction.

Earlier ANPHY sleep-stage analyses estimated a smaller short-horizon predictive-spread volume in N3 than in Wake, REM or N2 @langell2026_sleep_reachability. The cited research calls this stochastic reachability: a model-based summary of how local fluctuations propagate through a measured chart. It is a step beyond plotting where the state has been, although it is not a catalogue of thoughts someone could actually have.

Comparative work then asked whether reduced capacity meant the same thing in sleep, propofol sedation and epilepsy @langell2026_reduced_capacity. Capacity could fall in all three, while the accompanying transport and deformation measures differed. Deep sleep did not show the seizure-like combination of capture and pathological lock-in. A small local horizon therefore cannot, by itself, diagnose unconsciousness, illness or failed restoration.

The unpublished September 2026 full-cohort manuscript adds another piece @langell2026_sleep_families_revision. It describes 128 nights from 100 people in the locally available BOAS cohort, processed on a continuous 30-second grid. Repeated nights were summarized within each person, so someone with three nights did not count as three independent people.

The most consistent result concerned *magnitude*: the measured conditional increment-covariance magnitude was lower at N2-labeled observations than at Wake-labeled observations in 97 of 100 people. In plain language, the chart's estimate of local fluctuation spread was usually smaller. But its *shape* did not change uniformly: effective diffusion dimension increased in 64 people and decreased in 36. Concentration also varied in direction.

Picture a small cloud and a large cloud. The small one need not be a thin line. It can be smaller overall while spreading across just as many directions. That is why "less spread," "fewer directions," and "more trapped" need separate measurements.

Local-Jacobian summaries also tended to show lower instantaneous amplification measures in N2. These are estimates from observed trajectories, not responses to experimentally applied nudges. The manuscript describes associations with sleep labels: normalization uses the whole recording, estimator neighborhoods can extend outside the labeled stage, and the full temporal influence of upstream filtering is unresolved. It does not establish an isolated N2 mechanism or validate the earlier reachability model. Nor does a stage contrast by itself test whether two observations matched at the same pin have different future laws.

The defensible picture is already richer than a single entropy score: during sleep, fluctuation magnitude, directional shape and local response estimates can change differently.

== What Might the Renovation Actually Do?

There is a biological reason to take coordinated sleep rhythms seriously. Direct recordings in humans show that slow oscillations, spindles and hippocampal ripples organize neuronal firing and communication across memory-related regions @staresina2023. In mice, experimentally timing thalamic spindles to the slow-oscillation upstate enhanced coordinated coupling and memory performance @latchoumane2017_triple. Those findings support a role for timing in memory processing. They do not identify an EEG entropy drop as the mechanism that stores a memory.

The library metaphor can now earn its keep. Changing which books are retained is like changing stored structure. Opening a passage to a book already on the shelf is like changing access. A night of neural activity could involve both processes, on different timescales. An EEG trajectory does not tell us which book was moved or which doorway opened.

The cytoskeletal-dendritic accessibility model offers one candidate account of how cellular structure and current access might interact @langell2026_cytodendritic_accessibility. It proposes routes by which durable organization could bias later retrieval. The sleep studies discussed here have not established that substrate-level mechanism. It is a possible bridge from coordinated activity to lasting change, with experiments still needed along the bridge.

== REM and the Return of Possibility

If NREM suggests a library reorganizing its use of space, REM invites the image of an after-hours workshop: familiar materials appearing in unfamiliar combinations.

The older validation chart placed REM above NREM in its standardized entropy coordinate, and the ANPHY analysis estimated a broader short-horizon predictive-spread volume in REM than in N3 @langell2025_4 @langell2026_sleep_reachability. These findings concern different measurements. They do not directly show valleys being smoothed, memories generalized, or a latent noise amplitude increasing.

_Regularization_ remains a useful analogy from machine learning: learning needs enough structure to retain what matters and enough flexibility to avoid becoming tied to particular examples. In NDT, alternating sleep regimes might help balance those demands. The specific claim that NREM overfits memories and REM repairs them is a hypothesis, rather than the measured result of these studies.

The earlier report also fitted a decline in the amplitude of NREM–REM entropy differences over successive cycles, with a characteristic timescale of about 2.2 cycles in that cohort @langell2025_4. That describes an overnight pattern under one chart. It is not a universal timetable dividing the night into consolidation, creativity and integration, or evidence that completing cycles matters more than total sleep duration.

#figure(
  image("figures/Sleep_SLP019_night3_stages_trajectory.png", width: 90%),
  caption: [*Measured chart: one recording, changing sleep stages.* SLP019, night 3, from the earlier validation analysis. The trail follows successive samples through the night; the translucent surfaces summarize stage occupancy. The paths show measured change over time. They do not identify completed integration, memory content, or restored next-day capacity.],
)

== The Morning Question

The renovation metaphor points beyond what the overnight studies have measured. If sleep changes the conditions for tomorrow's thinking, can we connect a particular overnight signature to a particular improvement after waking?

That requires the morning measurement: memory, attention, behavior, or a reproducible change in estimated dynamics. The studies here do not establish a single noise budget that fills every hour awake and empties during sleep. They cannot tell us an unmeasured person's entropy, prescribe a target spindle count, or show that one recovery night restores every function.

Sleep as _infrastructure_ remains a compelling image. Its scientific value is that it asks what is maintained, by which process, and with what observable consequence. The newer work gives us a way to separate timing from efficacy, the size of fluctuations from their shape, and a temporarily narrow horizon from pathological capture.

When the library opens in the morning, its address is unchanged. What we want to understand is whether its contents, its passages, or the rules for moving through it have changed—and how to tell those changes apart.

That takes us to the machinery of the map.

#pagebreak()

= The Machinery of Mind

== From Metaphor to Mathematics

If you are not a "math person", you can still read this section comfortably: feel free to let your eyes skim past the formulas and focus on the surrounding plain-language explanations and metaphors. The equations are there for readers who enjoy seeing the machinery; the core ideas do not require you to calculate anything.

We've been speaking in metaphors—orchestras, conductors, landscapes, hikers in fog. Metaphors are wonderful for building intuition, but they can only take us so far. Eventually, if we want to make precise predictions, design interventions, or truly understand what's happening, we need to peek under the hood.

Don't worry—we're not abandoning the metaphors. We're translating them into a language that can be measured, tested, and refined. Think of it like moving from "the heart pumps blood" to understanding the actual mechanics of cardiac muscle, electrical signals, and fluid dynamics. The poetry doesn't disappear; it just gains precision.

The older _Meta-Noetic Diffusion Model_ (MNDM) supplies an accessible starting point: systematic movement plus rhythmic control of stochastic variation. The current NDT theory begins more broadly, with a controlled stochastic process @langell2026ndt_current.

The denoising image partly drew inspiration from machine-learning diffusion models, which learn ways to generate structured samples from noise @song2021. That is an analogy about reconstruction. Neural recordings have not established that the brain implements such an algorithm, and NDT's future-law question does not depend on that identification.

== The Manifold: The Stage for the Dance

Before we dive into the equation, we must clarify a central concept: the manifold.

In mathematics, a manifold is a topological space that locally resembles flat space but can be globally curved—like the surface of the Earth. You can walk north, south, east, or west (local flatness), but if you walk far enough, the curvature becomes apparent.

In Noetic Diffusion Theory, a manifold is a proposed space for the modeled neural process. Imagine it as a vast, undulating surface. A point specifies a state within that model; identifying its relationship to a particular thought, feeling or perception requires separate evidence.

To speak about distance or steepness, we must additionally specify a geometry. To speak about a preferred direction, we need a dynamical rule. A manifold alone supplies neither hills nor a potential. In the continuous diffusion model, sample paths are continuous; other observation scales may require hybrid or delayed models. The mathematical choice does not establish a universal rule about transitions between experiences.

The image suggests why a change of state might depend on the route as well as the endpoints. It does not establish geometric distances between emotions. Two travelers at the same point can still face different weather, different slopes, and different open routes.

== The General Recipe

The current theory starts with:

$ d X_t = b(X_t,t | c_t) d t + Sigma(X_t,t | c_t) d W_t $

Read this as: *the modeled state follows a systematic tendency plus fluctuations, with both allowed to depend on context* @langell2026ndt_current.

*$X_t$ is the modeled neural state.* Its biological detail may be much richer than our recordings. Signals such as EEG arise through an observation process, with measurement noise. Feature extraction then gives a reduced chart $x_t$, such as MNPS. Capital $X$ and lowercase $x$ are deliberately different.

*$b$ is drift.* It describes the local systematic tendency of movement. Drift can lead toward a valley, around a cycle, or through an asymmetric flow. The general model does not require every trajectory to descend a potential.

*$Sigma$ shapes the fluctuations.* This matrix controls their amplitude and orientation. The associated diffusion tensor is $a = Sigma Sigma^top$, the local covariance rate in the model. It describes how stochastic variation spreads across directions. Neither $a$ nor $Sigma$ is the MNPS coordinate called $d$.

*$c_t$ is context or control.* Depending on the question, it can include a rhythmic proxy, task context or bodily state. Predictions over an interval may also need the control's evolution and relevant history. Knowing one control value now is not always enough.

*$d W_t$ supplies idealized stochastic increments.* Brownian motion is an effective modeling choice here, not an assertion about the microscopic origin of neural noise. The theory allows extensions when delays, correlated fluctuations or memory require them.

This is a class of possible models. Writing the equation does not mean that its terms have been identified from a particular EEG recording.

== Hills and the Ease of Crossing Them

One useful part of drift can be written as potential-driven motion:

$ b = -M nabla V + u_"nc" $

The potential $V$ supplies a slope. The positive-definite mobility matrix $M$ determines how that slope is converted into movement under the chosen geometry. The remaining term $u_"nc"$ allows flow not represented by potential descent under the chosen geometry.

Imagine keeping a hillside unchanged while altering the grip of the paths across it. A traveler starting at the same spot may move differently even though the height map has not changed. In the model, that is one way to distinguish access from stored structure.

Mobility $M$ and stochastic spread $a$ are separate quantities; the theory does not impose a relation between them. Neither is the scalar chart coordinate $m$. Nor does an observed path uniquely reveal how much of its motion came from the potential, mobility or remaining flow. Even Jacobian asymmetry can arise from directional or state-dependent mobility; it is not proof of a separate non-conservative mechanism.

== The Minimal Rhythmic Case

For a simpler example, take identity mobility, remove the non-conservative term, and let stochastic amplitude be isotropic:

$ d X_t = -nabla V(X_t,t) d t + sigma(t) d W_t $

Now add the proposed rhythmic schedule:

$ sigma(t) = sigma_min + sigma_0(1-r(t)), quad 0 <= r(t) <= 1 $

With nonnegative parameters, increasing $r(t)$ reduces stochastic amplitude. In this isotropic case, covariance rate is $a = sigma(t)^2 I$. Lowering the amplitude changes how much fluctuation accompanies the drift; it does not switch the underlying potential gradient on or off.

In orchestra language, musicians follow a theme while allowing more or less variation around it. This is the minimal RVC hypothesis. A real rhythm could instead affect direction, gain or routing, and stronger coupling does not by itself reveal a value of $sigma$.

The theory also preserves negative evidence: companion tests have not supported a general claim that rhythmic timing is necessary for writing, when compared with energy-matched or shuffled-timing controls. That limits a proposed implementation. It does not turn every observed spindle-associated change into a failed observation, or every rhythmic association into a successful mechanism @langell2026ndt_current.

== The Thalamus: A Candidate Access Architecture

Thalamic circuitry provides a biological candidate for rhythmic access control. The thalamic reticular nucleus, or TRN, is an inhibitory structure that regulates thalamic relay activity; it is not a gateway through which every cortex–thalamus signal literally passes @halassa2016. Its involvement in spindle generation helps motivate the connection between rhythms and access.

That connection is a hypothesis about implementation. Demonstrating thalamic participation in a rhythm does not identify the rhythm with NDT's control variable or show that the circuit implements the theory's full future law. The orchestra image gives us a candidate role; recordings and interventions must establish what that role does.

== Event-Locked Change in Continuous Time

Rhythmic events can produce brief changes within an otherwise continuous process. The earlier sleep validation reported that a step-wise model fit its event-aligned entropy traces better than one particular exponential-decay alternative @langell2025_4. That comparison concerns the tested models and signal windows. It does not rule out continuous neural dynamics or establish one discrete update of consciousness per spindle.

The newer timing-versus-neighborhood analysis makes the prediction more precise: compare the event with its own baseline, preserve the surrounding temporal structure in the controls, and ask what changes beyond event selection itself @langell2026_rvc_sleep_revision. That is how a vivid denoising analogy becomes a testable measurement question.

== Making It Measurable: The Three Coordinates <mnps-three-coordinates>

To investigate this empirically, we need concrete measurements that summarize aspects of the modeled state and let us track their evolution. In what follows we will introduce three such numbers; if the formulas feel heavy, it is enough to remember that they are just three different ways of quantifying different properties of a recorded signal.

Enter the _Meta-Noetic Phase Space_, or MNPS. This is a three-dimensional coordinate system where every possible measured state corresponds to a point. MNPS is a *map*. It is not the land, and it is not NDT.

The coordinate names are interpretive. The numbers come from a documented feature mapping, normalization and projection. The current theory uses $m$ for mobility or coordination, $d$ for deviation from an integration–segregation balance, and $e$ for entropy or complexity pressure; none is a unique biological axis @langell2026ndt_current.

*$m$: the mobility / coordination family*

This name reflects an interest in how coordination persists and changes. A reference EEG mapping uses low-frequency powers and a beta/alpha ratio. Such features are not direct measurements of attention, emotion, metastability or the ability to switch thoughts.

*$d$: a state-feature family, distinct from diffusion*

The theory's deviation terminology and the "diffusivity" wording in some pipeline descriptions refer to a coordinate family. A reference feature mapping includes gamma power, Hjorth mobility and an alpha/theta ratio. These features do not directly measure distance from an optimal network balance, and $d$ is not the diffusion tensor $a$. A coordinate can change during a spindle while the corresponding stochastic law remains unestimated.

*$e$: the entropy / complexity family*

Entropy summarizes uncertainty under a specified representation. For intuition, spectral entropy asks how evenly a window's power is distributed across frequencies:

$ e_"spectral" = -sum_f P_f log P_f, quad P_f = S_f / sum_(f') S_(f') $

Concentrated power gives lower spectral entropy; evenly distributed power gives higher spectral entropy. This illustrates one signal property. It is not the complete $e$ coordinate in the cited configurations and does not measure a person's confusion or clarity.

*What is actually computed*

The NeuralManifoldDynamics export `mnps_3d = [m, d, e]` is a versioned chart derived from a nine-coordinate layer @langell2026_neuralmanifolddynamics. In the reference mapping summarized here, the families use band powers and ratios for $m$; gamma power, Hjorth mobility and an alpha/theta ratio for $d$; and permutation entropy, Hjorth complexity and an arousal-related slot for $e$. Projection weights and feature mappings belong to the specified configuration, including any physiological inputs and fallbacks. They must be checked for the actual recording, rather than inferred from the coordinate names.

For example, the later RVC spindle study deliberately used an EEG-only primary mapping: $e_m$ combined Hjorth mobility and beta/alpha, while $e_s$ combined alpha/theta and gamma features. Its bodily anchor was tested separately @langell2026_rvc_sleep_revision. That is why a shared label does not license pooling numbers from different configurations. Fixed, documented computations make comparisons auditable; the biological interpretations of their names remain hypotheses.

Together, e, d, and m give us a coordinate system for the *pin*. Each supported measurement window contributes a point in canonical order $[m,d,e]$; a named condition occupies a distribution of points. Matching that point does not imply matching the future-law.

But coordinates alone are not the whole story. Recent sleep-stage work adds a second layer: once a state is placed in this space, we can also ask what the local future around that point looks like. In ANPHY sleep EEG, `Wake`, `REM`, and `N2` separate from `N3` not only in their mean location, but in short-horizon predictive spread and local Jacobian magnitude, showing differences in additional model-derived summaries alongside differences in location @langell2026_sleep_reachability. Testing C2 further requires checking what these summaries add beyond location and conventional features. We will not unpack the estimators here.

These measurements locate observations. They do not define the potential $V$. Earlier essay formulas that combined $e$, $m$ and $d$ into a landscape score were teaching constructions, not the potential specified by the current theory. We therefore keep the chart and the dynamical model separate here.

== The Landscape Takes Shape

Once the coordinates are defined, we can plot successive measured states. A recording becomes a path through the chart. Stage colors can reveal where N2 or REM observations tend to accumulate, and event markers can locate a spindle-associated shift.

Those are observations of the pin. A narrow cloud of visited points does not prove that the underlying landscape contains a deep valley. A higher $d$ value does not itself mean more accessible destinations, and an $m$ value does not directly measure the capacity to switch thoughts. In particular, the spindle findings should not be reduced to "NREM lowers every axis": event timing and whole-stage comparisons ask different questions.

To describe possible movement from a point, we need estimates of local dynamics and explicit choices about the prediction horizon, coordinate scaling and data support. Those estimates can fail even when the coordinate plot looks smooth. Part 2 explains what the extra measurements add, and what their validity requires.

== What the Recipe Lets Us Test

The model becomes useful when its terms support predictions. Can local estimates anticipate a short part of the next trajectory on data held out from fitting? Do context or recent history change those predictions beyond what the present chart already supplies? Can a known perturbation separate two models that fit ordinary observations equally well?

Those are stronger tests than drawing a smooth trajectory or finding a group difference. The theory's selected Lean formalizations check mathematical components under explicit assumptions; simulator tests ask whether estimators recover known objects within specified conditions. Neither kind of success identifies those objects in a human recording @langell2026ndt_current.

The next step is therefore not simply to add more axes. We need to know which question each measurement can answer, and what would make that answer fail.

= The Limits of the Map

We have built the machinery. We have defined the coordinates. We have seen sleep-associated changes in measured state and dynamics, and asked how they might relate to the futures available tomorrow.

But if you look closely at the map we have drawn so far—the basic MNPS with its three feature families, $[m,d,e]$—you might notice something missing. It is grainy. It is low-resolution.

Consider two hypothetical recordings with similar three-coordinate summaries. Their nine-coordinate patterns could differ in ways that cancel when combined into three numbers. Even if those richer patterns also matched, the next part of each trajectory might differ. These are possibilities to test, not established matches between particular diagnoses or experiences.

#figure(
  image("figures/ndt_v.1/fig_s4_4_map_not_land_v2.png", width: 92%),
  caption: [*Schematic.* The map is useful precisely because it is not the land. Estimates of local dynamics are made through the chart, not as transparent views of the latent process. Think of a subway map: invaluable for getting across town, a terrible geological survey.],
)

Think of a subway map. It is invaluable for getting across town. It is a terrible geological survey. MNPS is closer to the subway map. Using it as if it were the terrain is how a measurement chart gets mistaken for a theory of mind.

That caution now extends to reduced dynamical capacity as well. Newer comparative work shows that low traversability or reduced local capacity is not, by itself, a universal scalar of unconsciousness: deep sleep, propofol sedation, and epilepsy can all show capacity loss, but they dissociate in transport capture and pathological deformation. A low-capacity state may therefore be physiologically restorative, pharmacologically suppressive, or pathologically trapped—and the map has to be rich enough to tell those apart @langell2026_reduced_capacity.

The distinction between evidence and inference has already mattered in the theory's companion work. A meso-to-macro study found associations between population activity and EEG summaries, while the tested EEG chart failed its local-operator criterion. An IBL analysis likewise found decodable information without a valid nominated chart-transition operator @langell2026ndt_current.

The lesson is not that the signals contain nothing. It is that information in a recording and the ability to recover a dynamical rule from a particular chart are different achievements. A failed estimator remains unavailable for that claim, even when the plotted states look convincing.

== Structure is not access

NDT repeatedly separates *what is stored or structurally available* from *what is dynamically accessible now*. Changing access need not require rewriting the underlying structure.

The current theory distinguishes two history questions. One is whether learning or replay writes the potential itself. The other is whether context changes access while the potential stays fixed.

The second now has a bounded computational answer. Companion simulations demonstrate that, on specified landscapes, changing a directional access operator can change first-arrival probabilities from the same starting point without rewriting the potential. An extension testing robustness across neighborhoods did not pass. This is a bounded computational existence result, not a demonstration of hippocampal memory or a validated empirical MNPS operator @langell2026ndt_current.

The biological landscape-writing question remains open. The distinction protects both ideas: finding altered access does not prove altered storage, and finding stored structure does not tell us which routes are currently easy.

== What Would Count Against the Theory?

C2 requires future-dynamics summaries to add reproducible information on held-out data beyond location and conventional summaries. If their apparent contribution disappears under suitable alternative charts, ordinary spectral features or valid null controls, the accessibility claim must narrow. C3 requires nominated controls to change specified future-law features at a matched measured state, beyond standard covariates. A generic association with an extra variable does not meet that test.

The rhythmic proposal also needs comparisons with stationary or smoothly varying controls, event density, power and temporal autocorrelation. A spindle-associated coordinate shift is evidence about an event; it does not by itself establish a uniquely rhythmic schedule or a causal write operation.

Failure has a scope. A failed chart can be replaced, and a failed thalamic implementation can be rejected without making future dynamics meaningless. But repeated failure across reasonable charts, estimators and controls would substantially weaken NDT's proposed contribution. The existence of possible futures is not a way to protect every claim about them from testing @langell2026ndt_current.

== What this essay is not

- Not a bedside score, a CPC substitute, or a test of awareness.
- Not Integrated Information Theory's $Phi$, workspace ignition, or a report.
- Not the claim that "noetic" means knowledge-bearing structure in the coordinates. The name marks the intended domain of mind-relevant dynamics.
- Not a completed theory of why any of this should *feel like* anything.
- Not a licence to treat every named object (committor, finite-amplitude resilience, dendritic access) as an empirical export. Several remain questions, and they belong to later parts of the series.
- Not the claim that rhythmic denoising *is* consciousness, or that the measurement chart called MNPS *is* NDT.

If, after matching state, responsiveness, arousal, power, and complexity, the future law still failed to distinguish reported experience from no reported experience, NDT would remain a theory of enabling dynamics. That test is named in the technical paper. It has not been run.

Part 2 develops the richer chart and the local dynamical estimates. Higher resolution can expose differences hidden by averaging, but it does not guarantee a valid operator or identify a biological mechanism. Each step inherits the limits of the recording and the measurements before it.

The next question is how the flow varies around a measured point. A local drift derivative describes that variation; it is not, by itself, a measure of learning, adaptation or a second derivative of thought.

This brings us to the frontier of the theory, and to Part 2: the high-resolution texture of Stratified MNPS, the local response information in the Jacobian, and the geometric differences investigated in clinical cohorts.

The instrument is built. The pin is not the future. Now we must learn how the map plays the symphony of a human life.

See you in Part 2.

#pagebreak()


= Appendix: NDT in the Landscape of Theories

The current theory treats its neighbors as approaches to partly different questions. NDT concerns neural dynamical capacity and its control. It does not currently identify what experience is, how content becomes reportable, or how a system represents its own awareness @langell2026ndt_current.

== Predictive Processing and the Free-Energy Principle

Predictive-processing accounts describe inference using a generative model; particular models can include precision weighting, bodily prediction and dynamics @friston2010free @clark2013whatever @seth2013interoceptive. NDT asks about state-dependent transition structure. The two may be related through a specified model, but an estimated drift is not automatically variational free energy, and a rhythmic proxy is not precision under another name. The distinction is not simply "content versus process" or "continuous versus rhythmic."

== Integrated Information Theory

IIT identifies experience with irreducible intrinsic cause–effect structure, rather than with a generic ability to integrate information @tononi2016integrated. NDT makes no corresponding identity claim. Its forecast geometry is not IIT's $Phi$, and agreement that total activity is insufficient does not imply that the theories share an ontology.

== Global Neuronal Workspace

Global neuronal workspace theory proposes that information becomes broadly available through a nonlinear ignition and sustained global access @mashour2020conscious. NDT's dynamical accessibility might describe conditions that enable or restrict such a transition. It does not itself model global broadcast, report or workspace competition. A larger predicted spread is not workspace ignition.

== Dynamical Landscapes, Metastability and Network Control

These are NDT's closest relatives. They already study trajectories, transitions, coordination and constraints; they do not merely place a pin on a static map @deco2011emerging @kelso2012multistability @gu2015controllability.

NDT's proposed contribution is their organization into distinct questions about state, local law, future structure and conditional control, with explicit measurement limits. Transition laws and diffusion tensors are established mathematics. The empirical commitments are whether the separated quantities add information, and whether specified controls reshape them at a matched chart state @langell2026ndt_current.

Metastability motivates an interest in coordination that persists while remaining open to change. MNPS $m$ is a configured feature family, not a direct Kuramoto order parameter or a universally calibrated measure of metastability.

Network control theory also asks about possible transitions, often using explicit inputs and control-energy objectives. NDT's current short-horizon stochastic-spread estimates do not introduce an input matrix or optimize control energy. Their covariance-based volumes are not structural-connectome controllability or measurements of the effort of thinking.

== Other Questions Remain Other Questions

Recurrent-processing theories concern recurrent sensory processing; higher-order theories and attention-schema theory concern forms of meta-representation. NDT does not identify a chart rotation with anatomical feedback, and an attention-related feature slot is not an attention schema @langell2026ndt_current. These possible connections require shared definitions and tests. Compatibility alone validates neither framework.

#pagebreak()

= References

#context {
  set par(leading: 0.5em)
  bibliography("references.bib")
}

#pagebreak()

#[
#set par(leading: 0.5em)
= Glossary

== A-D

*Affective Mobility (historical alias, $m_e$)* - The alpha-derived proxy in the reference mapping; the signal-derived name is preferred. It does not directly measure emotion-driven switching or isolate the limbic system.

*Attentional Mobility (historical alias, $m_a$)* - The low-frequency power proxy in the reference mapping; the signal-derived name is preferred. It does not directly measure voluntary shifts of attention.

*Attractor* - Long-time organization toward which trajectories tend under a specified dynamical model. A stable fixed point is one example; an attractor need not be a single point or a low-potential valley. It differs from short-horizon predictive spread.

*C1 / C2 / C3* - C1: a reduced measured state need not determine the latent future law. C2: summaries of measured future dynamics should add reproducible held-out information beyond current chart location and standard static/spectral summaries in some regimes. C3: nominated controls can change specified features of that measured future law at matched chart state beyond standard covariates.

*Coherence (legacy terminology)* - Earlier essays used an exponential potential score under this name. It is not a defining quantity in the current NDT framework. The theory instead uses $Omega$ for the antisymmetric part of a chart Jacobian; those objects must not be identified.

*Coupling (SO-spindle)* - A statistical timing relationship between slow oscillations and spindles. Its phase and strength depend on how the events are defined and measured. It does not require perfect coincidence or imply a memory save at every event.

*d (State-feature family)* - Called deviation from an integration–segregation balance in the theory and diffusivity in some operational descriptions. Its value comes from a versioned feature mapping, not a directly measured optimum or the diffusion tensor $a$.

*Denoising* - Recovering structure from a corrupted signal in a specified model. NDT borrows this as an analogy for reconstruction and as a candidate account of some dynamics. An EEG entropy decrease alone does not establish that mental noise was removed or meaning created.

*Diffusion Model (ML)* - A class of machine learning models that learn to transform noise into structured data through iterative denoising steps. NDT borrows iterative denoising as an analogy and candidate mechanism; this does not establish that the brain implements the machine-learning algorithm.

*Diffusion tensor ($a$)* - The model's local stochastic covariance rate, $a = Sigma Sigma^top$. It has magnitude and directional shape. Empirical estimation requires its own support and validity checks; it is not the state coordinate $d$.

*Dynamical Accessibility* - The family of future laws conditioned on horizon and control protocol. Latent-state laws $K^X$ differ from laws conditioned on a measured chart, $K^x$. Endpoint distributions, local drift and spread, first-arrival probabilities and intervention responses describe different aspects of the process. Accessibility is not merely a reachable set or conscious access in the workspace sense.

== E-H

*e (Entropy)* - The MNPS entropy-family coordinate, computed from the versioned feature mapping and reference normalization. It is not a direct measure of confusion or clarity. The spectral-entropy formula in the text is a pedagogical surrogate, distinct from the full coordinate.

*Embodied Anchoring Principle (EAP)* - The proposal that bodily signals may condition neural dynamics and aspects of experience. NDT treats this as a candidate physiological control of accessibility, not an extra MNPS axis or a demonstrated controller in every tested regime.

*Geodesic* - A locally shortest path under a specified metric. Applying the idea to transitions between mental states requires a justified geometry; a plotted path does not establish psychological ease or difficulty.

*Gradient Descent (ML)* - Movement along a function's negative gradient. NDT permits potential-driven drift $-M nabla V$ as one component of a broader flow. Lower potential does not automatically mean greater meaning or better health.

*Horizon* - The time interval over which a prediction is made. A distribution at its end does not by itself specify every path taken to get there.

== I-M

*$lambda(t)$ (Legacy self-prior notation)* - Earlier notation for a proposed bodily weighting. The current theory treats bodily influences as contextual variables such as $c_t^"body"$, rather than requiring one universal bodily-control scalar.

*Landscape* - A model illustration of tendencies and routes over a state space. The three-dimensional MNPS chart is a reduced measurement view, not the full space of possible mental states. Neither the illustration nor the chart alone specifies a future law.

*Local Coupling (historical alias, $d_l$)* - The Hjorth-mobility feature in the reference mapping. Hjorth mobility is used in the reference mapping discussed here; other claims require the actual configuration. The name alone does not establish local network coupling.

*m (Mobility / Coordination Family)* - A configured family of state features. Reference EEG mappings use low-frequency powers and a beta/alpha ratio. It is distinct from the mobility matrix $M$ and is not a direct measure of thought-switching capacity.

*Manifold* - A mathematical space that locally resembles Euclidean space. NDT proposes such a space for modeled neural dynamics; MNPS is a reduced observation chart, not a demonstrated map of every possible mental state.

*Meta-Noetic Diffusion Model (MNDM)* - The earlier minimal rhythmic model, nested within current NDT's broader controlled diffusion. The scalar illustration is $d X_t = -nabla V(X_t,t) d t + sigma(t) d W_t$. Reduced observations $x_t$ need not follow that same equation.

*Meta-Noetic Jacobian (MNJ)* - A local drift derivative estimated in the MNPS chart, where the estimator is justified. It describes local deformation of small displacements. It is not automatically a biological perturbation-response operator or a second temporal derivative.

*Meta-Noetic Phase Space (MNPS)* - A versioned reduced measurement chart in canonical order $[m,d,e]$. The families have interpretive names and configured feature definitions. Unsupported observations remain missing; the chart is not the latent neural state or the theory itself.

*Mobility matrix ($M$)* - The matrix converting a potential gradient into drift. It is distinct from both the MNPS coordinate $m$ and the diffusion tensor $a$.

== N-R

*Network Diffusivity (historical alias, $d_n$)* - The gamma-power proxy in the reference mapping, also called network deviation in some manuscripts. Gamma power is used in the reference mapping discussed here. The slot is not a directly estimated network diffusion tensor.

*Noetic Atlas* - The repository of aggregated noetic mappings, forming a living cartography of measured states. Like a book of maps, it compiles individual landscapes into a shared reference database.

*Noetic Diffusion Mapping (NDM)* - The analytical process of converting brain signals (EEG, fMRI) into MNPS coordinates. This is the technique used to create the maps.

*Noetic Diffusion Theory (NDT)* - The theory that mind-relevant neural regimes are characterized by a control-dependent law over possible futures, not by present reduced-state location alone. "Noetic" marks the intended domain of mind-relevant dynamics; it does not mean that the coordinates themselves contain knowledge. "Diffusion" refers to stochastic transition dynamics and spread; a potential landscape can supply one component of drift. Rhythmic reconstruction is one candidate control, not the identity of the theory.

*NREM Sleep* - Non-REM sleep, comprising N1, N2 and N3. Slow oscillations, spindles and memory-related coordination motivate NDT hypotheses; measured entropy and capacity changes do not by themselves establish denoising or memory writing.

*Oscillatory Flexibility (historical alias, $m_o$)* - The beta/alpha-ratio feature in the reference mapping described here. Its name is an interpretation, not a direct test of cognitive flexibility.

*Overfitting (ML)* - Learning examples in a way that fails to generalize. The suggestion that NREM promotes overfitting and REM corrects it is a modeling analogy, not an established finding of the sleep analyses.

*$r(t)$ (Rhythmic Control)* - A normalized candidate control variable in the minimal model. By assumption, increasing it reduces the scalar stochastic amplitude. A strong recorded rhythm does not automatically identify its value.

*Reachability Cone (legacy visual name)* - In the current theory, stochastic short-horizon reachability is a covariance-based approximation to finite-horizon predictive spread, often drawn as an ellipsoid. It does not identify every reachable state or the full distribution. Small volume alone does not establish capture or unconsciousness.

*Recurrence Rate (RR)* - A recurrence-analysis quantity: what fraction of visited states are returns to previously visited states. Mentioned here as vocabulary only; no clinical reference values are claimed in this series.

*Regularization (ML)* - Methods that constrain learning to improve generalization. REM-related landscape regularization is a hypothesis in the essay, not a directly measured sleep function.

*REM Sleep* - Rapid-eye-movement sleep. The cited studies report distinct entropy and estimated predictive-spread profiles relative to NREM comparisons. They do not independently identify a rise in the latent noise amplitude or literal landscape smoothing.

*Representational Dispersion ($d_s$)* - An interpretive name for a versioned $d$-family feature slot (an alpha/theta ratio in the reference mapping discussed here). It does not directly measure the diversity or depth of represented thoughts.

*Rhythmic Variance Control (RVC)* - The smallest accessibility controller: a rhythmic proxy that turns isotropic noise up or down. One slot in the local law, not a proof that spindles write memory or implement consciousness.

== S-Z

*Score Matching (ML)* - Learning a probability density's logarithmic gradient. It motivates diffusion-model analogies; the sleep measurements here do not establish that the brain learns this score.

*$sigma(t)$ (Stochastic Amplitude)* - The scalar amplitude multiplying Brownian increments in the minimal model. Isotropic covariance per unit time is proportional to its square. The proposed schedule is $sigma(t) = sigma_min + sigma_0(1-r(t))$.

*Sleep Curriculum* - A metaphor for changing organization across the night. The earlier cohort-specific cycle pattern does not establish a universal sequence of consolidation, regularization and integration.

*SO-Spindle Event* - A detector-defined association between a slow oscillation and spindle activity. Counts and timing depend on the protocol; not every detected spindle is an SO-coupled event.

*Stratified MNPS* - A nine-coordinate chart $[m_a,m_e,m_o,d_n,d_l,d_s,e_e,e_s,e_m]$ recomposed into $[m,d,e]$ by a release-fixed projection. It can reveal feature differences hidden by aggregation. It does not directly isolate global broadcast, local chatter or psychological faculties.

*Theta-Gamma Coupling (PAC)* - Variation of gamma-band amplitude with theta phase. It motivates temporal coding and control hypotheses, without establishing a fixed refresh rate of experience or identifying stochastic amplitude.

*Topology* - The study of shapes and spaces independent of exact distances—what stays the same when you stretch or bend but don't tear. In landscape illustrations, topology concerns how regions and routes connect. Distances, transition probabilities and transition times require additional geometric and dynamical information.

*TRN (Thalamic Reticular Nucleus)* - Inhibitory thalamic circuitry involved in regulating relay activity and spindle generation. The current theory treats it as one candidate access architecture, whose role need not reduce to scalar variance control.

*V (Potential; F in older essays)* - A scalar function supplying a potential-driven component of drift. The current theory does not define it as a sum of MNPS coordinates. Its decomposition from mobility and other flow components is not uniquely identified by trajectories.

*Variance Schedule* - The time dependence of the stochastic amplitude $sigma(t)$ in the model. Its associated covariance depends on the squared amplitude. Particular healthy or pathological schedules require empirical identification.

]

#pagebreak()

== Acknowledgments

This work emerged through structured correspondence among human and AI collaborators; large language models from OpenAI, Anthropic, and Google assisted in literature synthesis, drafting, peer review, and editorial refinement. We also gratefully acknowledge the original investigators, clinical teams, participants, and data stewards who created, curated, and shared the public datasets and metadata that made these analyses possible.

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
Reference implementations: `https://github.com/NoeticDiffusion` 

The bibliography distinguishes public records from the local working revisions consulted here.

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

- *Repository:* `https://github.com/NoeticDiffusion` 
- *Toolkit:* Includes Python implementations for MNPS coordinate extraction, Stratified MNPS decomposition, and basic visualization scripts.

Science thrives on verification. We invite the community to test, break, and refine these maps.
