// Reality from Noise: Same Place, Different Futures — Part 4
// The Synthetic Mind: From Biological Geometry to Auditable AI (NDT v2 framing)
// Author: Robin Langell, 2026
//
// Proposed minor rewrite (peer review pr7, 2026-09-12). The original v1-framed
// Part 4 is kept unchanged as "...Rhythmic Geometry part 4.typ" for comparison.

#import "template.typ": essay-template

#show: doc => essay-template(
  title: text(hyphenate: false)[Reality from Noise:\ Same Place, Different Futures],
  subtitle: [Part 4: The Synthetic Mind],
  series-description: [A research companion to Noetic Diffusion Theory],
  author: [Robin Langell],
  date: [2026],
  doc,
)

== Prelude: The Question We Left Open

Part 2 closed its philosophical section with two sentences: _Questions about synthetic systems that might instantiate similar dynamics belong to a later part of the series, if at all. Current language models are not a test of NDT._

Here we are. The second sentence is still in force.

The question has also changed shape since the first draft of this part was written. It is not primarily a question about consciousness. It is a question about *measurement*, and it inherits the three commitments that carried Parts 1–3.

If a biological state is usefully described as a pin plus a future-law—where the system sits, what can still happen from there, and what changes those possibilities—then we can ask a narrow question about artificial systems: are there memory architectures that expose enough of their internal state that the same three questions can be *posed*? Not answered yet. Posed, with logs.

This is the most speculative part of the series. Most of what follows sits at Level 3 or Level 4. It is included because the direction matters, not because results are in. Where an idea has crossed from design into a controlled test, we say so and give the numbers.

#v(1em)

= Reader's Guide and Claim Boundary

== What This Part Is

Part 4 differs from Parts 1–3 in one respect: it is a conceptual and architectural essay, not a report on measured cohorts.

Parts 1–3 built upward from established neuroscience, through internal cohort evidence, to speculative extensions marked as such. Part 4 inverts the ratio. The bridge from biology to AI is methodological, not substrate-level equivalence.

Part 4 is therefore a research companion to the NDT series. It carries the same measurement questions into AI memory design while keeping its architectural proposals and internal demonstrations separate from the cohort evidence in Parts 1–3.

== Reading Convention

Watercolor terrain in this series is metaphorical. Diagrams in Part 4 describe proposed architectures or measurement schematics. A plotted benchmark is treated as empirical only under the protocol, controls, and scope stated with it; visual resemblance alone is not evidence of a shared substrate or mechanism.

The same four-level ladder applies, with the rungs relabelled for this domain so that "Level 1" does not quietly change meaning between parts:

1. *Specified machinery (internal):* the SPIRALbase, Hybrid-J, and SPIRAL Cortex architecture documents, and the NDT measurement vocabulary. Fully written down. Not external facts, and not products.
2. *Empirically supported (internal, narrow):* protocol-gap repair on a small set of *selected* repository-repair cases with ablation controls. In the frozen v0.80 run, six cases were behaviourally or test-positive with memory and one more at apply level; a later pass counted nine unique positives. Shuffled, wrong-subsystem, other-repository, and lesioned memory were inert in the confirmed cases. This is a mechanism demonstration, not a benchmark.
3. *Emerging (designed for, partially logged, not evaluated):* NDT-style diagnostics on memory traces. Routing scores, history bias, recall traces, and lesion flags are logged today. A local Jacobian approximation and a reachable candidate set are design targets.
4. *Theoretical extrapolation (Level 4):* Rhythmic Variance Control in AI, Synthetic Sleep, Embodied Anchoring for AI, and the question of whether any artificial system could instantiate noetic dynamics.

== The Three Commitments, in an AI Key

Parts 1–3 rested on C1, C2, C3. They translate, and the translation is the spine of this part.

#block(fill: luma(240), inset: 1em, radius: 5pt)[
  *C1 (AI).* The retrieved item is the pin. Two recalls that return the same item can differ in what happens next: which corridor was taken, whether a bridge opened, what was suppressed, how stably the dynamics settled.

  *C2 (AI).* Do summaries of that recall trajectory carry information that the output score does not—for example, about the *type* of failure when the answer is wrong? *This has not been tested.*

  *C3 (AI).* Does session context—project, operator, access mode—change the routing law at a matched cue? In selected protocol-gap cases, cues and local symptoms were treated as comparable while right-subsystem memory changed the action and wrong-context controls were inert. This is a C3-shaped ablation pilot, not yet a matched-state conditional-law test.
]

== What This Part Is Not

It does not claim that current AI systems are conscious.

It does not claim that geometric similarity between biological and artificial dynamics would establish consciousness in either direction.

It does not claim that SPIRALbase, Hybrid-J, or SPIRAL Cortex are implemented products, or that the protocol-gap cases constitute general performance evidence.

It does not claim that a shared vocabulary is evidence of a shared mechanism. As we will say plainly below, the vocabulary is shared partly *by construction*.

The central question is narrower: can we build AI memory systems that expose enough internal state that C1–C3 become testable? If yes, we gain a shared measurement discipline. If no, we learn something about the limits of the framework.

#pagebreak()

= The Memory Question

== The Pianist's Pause

I am sitting at the piano. My fingers are poised above the keys, but my mind is a sudden blank. The next chord—the one that should bridge the verse into the chorus—has vanished. If you asked me to name the notes, to write them on a staff, I couldn't. The "address" of that memory is gone.

Then I let my hands fall. I don't think; I listen. I feel the weight of the instrument, the tension in the strings, the resonance of the room. My fingers find the keys. Not because I found the memory in a file, but because the instrument remembered for me. The chord exists as a physical potential, a valley in the landscape of the song that my hands simply rolled into.

This is not how we usually think of computer memory. It is the picture that the rest of this part tries to make precise enough to audit.

== Overlapping Design Families

Several memory and access families are useful comparison points here. They are not mutually exclusive: a system can combine attention, recurrent state, external retrieval, policy gates, and attractor dynamics. The comparison concerns trade-offs in how information is represented and allowed to influence a computation.

*Dense attention: the Spiderweb.* In the dense self-attention formulation, each token can mix information with the other tokens in its permitted context @vaswani2017. This supports flexible content-based interaction, while leaving questions such as memory isolation, provenance, and policy-level permission to the surrounding architecture. Sparse masks, routing, retrieval, and other controls can change which interactions are permitted.

*Selective state-space models: the Scroll.* Selective state-space models such as Mamba update a recurrent state while processing a sequence, with a linear-time sequence formulation in the cited design @gu2023. The state is a learned summary whose contents depend on the model and task. Its finite representation creates a memory trade-off, but it does not by itself imply that all distant detail is discarded or that the model has one fixed access policy.

*External retrieval.* Retrieval-augmented systems add a store outside the current hidden state. Retrieval and reasoning need not occur in a fixed two-stage order: IRCoT, for example, interleaves retrieval with reasoning steps, letting each inform the next @trivedi2023ircot. A design can additionally specify where selection, routing and permission checks occur. A simple retrieve-then-generate pipeline is one choice, not a definition of the whole family.

*Attractor memory: the Instrument.* Associative attractor systems use dynamics that can settle noisy or partial cues toward stored patterns @hopfield1982. SPIRALbase is a designed, explicit descendant of that idea: it represents memories with learned potentials and adds context-specific projectors, blocks, and gates @langell2026spiralbase. In this family, the useful distinction is between the dynamics of settling and the separate machinery that selects which regions are active. Remembering can therefore be studied as a geometric process without implying that every retrieval system is an attractor system.

== Memory as Landscape

In Parts 1–3 we described a neural state as a location on a learned landscape, plus a law over nearby futures that rhythm, body, and history can reshape.

SPIRALbase imports the landscape half of that picture. Its design emphasizes a separation between structure and access: a query can open a context-specific subspace, after which only the selected region participates in attractor settling. Other attention, state-space, retrieval, and attractor systems can make different choices about selection and gating; the useful comparison is the resulting trade-off, not a claim that one family has a single universal access pattern.

That makes SPIRALbase a natural place to ask NDT-shaped questions. Whether it makes it a *counterpart* to a brain is a different matter, and not one this part claims.

#pagebreak()

= Building the Instrument: SPIRALbase and Hybrid-J

== Attractor Basins Instead of Indexed Records

In a conventional database, a record exists at an address. In SPIRALbase, a memory exists as a basin in a high-dimensional landscape. You don't need the address; you need to be in the neighbourhood. The dynamics settle into the nearest occupied basin because query and memory are geometrically close.

This is the principle of associative memory in Hopfield networks, where a partial or noisy cue completes a pattern because the pattern is a stable state of the dynamics @hopfield1982. SPIRALbase is a designed, explicit descendant of that idea.

Each basin has a _depth_ (how strongly it pulls) and a _width_ (how broadly it captures). The query lands somewhere, and the dynamics settle toward the nearest basin. If several are nearby, the system must choose. That is where the architecture becomes interesting.

== Projector Gating: Opening the Right Subspace

The key move in the middle generation of SPIRALbase was projector gating @langell2026spiralpk. Instead of using the query only as a cue, the system uses it as a _key_ that opens a subspace: a context-specific projector maps the query into a submanifold containing only the memories relevant to that context.

The same store can then serve different contexts without interference. A medical-record memory and a codebase memory can coexist, opened by different keys. The projector is not an address; it is a direction, derived from the cue itself.

One honest note from that generation: the hypothesis that the projector acts as a *coordinate transform* of the landscape was tested and did not survive. What survived is the gating role.

== Hybrid-J: The Block-Structured Substrate

Hybrid-J is the current realisation at scale @langell2026hybridj. It organises the landscape in three layers:

1. *Shared Core:* a small backbone of universal attractors carrying cross-context structure.
2. *Local Context Blocks:* neighbourhood-specific attractor clusters—one codebase, one patient record, one project—that do not pollute one another.
3. *Controlled Bridges:* sparse, explicit connections between blocks. Bridges are not automatically open. They have a direction, an amplitude, and a permission: the current cue must qualify to activate them.

The three-factor bridge—direction, accessibility amplitude, cue-conditional gating—has an *analogy* in the cytoskeletal-dendritic accessibility model of Part 2 @langell2026_cytodendritic_accessibility, where some routes are hypothesised to stay easier to reopen than others without changing synaptic weights. Hybrid-J implements a *software analogue*: accessibility $S_i$ is graded rather than binary, and recent use leaves a mild bias that makes some paths easier to re-enter. Analogy, not homology. The biological model is itself Level 4.

== Bounded Cost of Attractor Settling

Under the current Hybrid-J accounting @langell2026hybridj, *attractor-settling cost is constant with store size once the active block has been selected*. The claim concerns the fixed active matrix used by the settling subroutine: adding inactive patterns elsewhere does not change that subroutine's analytical FLOP count.

This bound does not include block selection or routing, candidate scoring, bridge traversal, encoding or decoding, memory access, or end-to-end policy cost. Those terms depend on the implementation and may change with the number of candidates or active blocks, so they require their own complexity analysis. The present statement is therefore an analytical claim about a bounded component of retrieval, not a measured wall-clock or system-level scaling result.

The architectural implication is narrower as well. Hybrid-J assigns most stored patterns to inactive blocks for a given query, then pays the settling cost for the selected active region. Whether that design reduces total cost or improves retrieval quality is an empirical question about routing, settling, and the surrounding policy together.

== The Instrument Begins to Listen to Itself

In the most recent SPIRALbase work, the instrument acquired the ability to report on its own movement. After a recall, it can answer not only _what_ it remembered but, in part, _how_: which routing scores competed, whether history biased the choice, which lesion or control condition was active, and a trace of the recall path.

That is a rudimentary second-order layer: visibility into first-order dynamics. Not consciousness. Bookkeeping.

It is also the technical prerequisite for asking C1–C3 of an AI memory system. Not that we have done it. But there is now something to measure.

#pagebreak()

= The Policy-First Principle: SPIRAL Cortex

== Memory Is Not the Actor

The central sentence in the SPIRAL Cortex architecture @langell2026spiralcortex, paraphrased: _the policy is the primary actor; memory is residual evidence_.

SPIRAL Cortex makes a different policy choice from a simple retrieval-then-generation pipeline. In that arrangement, retrieval runs before generation and the retrieved content is passed downstream as evidence. Interleaved retrieval and reasoning already supply a concrete alternative @trivedi2023ircot; retrieval augmentation does not imply one access order. The design question here is where responsibility for relevance and permission sits.

SPIRAL Cortex inverts this. The policy moves first. It assesses what it knows from local context. If that is sufficient, it acts without memory. Only when local context is *insufficient*—when there is a gap between what the policy knows and what the task requires—does memory enter. And when it enters, it passes through gates: a semantic quality check, an arbitration step, and an audit trace that records the path.

The loose biological picture is prefrontal: a layer that decides when to let memory influence behaviour and when to suppress it. That is a picture, not a homology.

== Protocol-Gap Cases

The clearest evidence for this architecture comes from protocol-gap cases in repository repair. A local symptom—a failing test, an exception—is insufficient to determine the right action. The right action requires knowledge of a broader obligation: a family-level constraint, a cross-subsystem dependency, a historical exception that set a precedent. Local evidence is not enough; the agent needs project memory.

In controlled runs on *selected* SWE-bench cases, SPIRAL Cortex supplied the missing convention while ablated controls—shuffled memory, wrong-subsystem memory, other-repository memory, lesioned memory—remained inert. Frozen v0.80: six behavioural or test-level positives and one apply-level positive; a later pass counted nine unique positives across repositories such as `astroid`, `pydicom`, and `sympy`. The mechanism is narrow: same-subsystem semantic memory, applied when the policy identifies a gap, can change the answer.

Read this as a *C3-shaped pilot*. The cue and local symptom are approximately comparable while the *context* of the memory changes. Right-subsystem memory changes the action; wrong-subsystem memory does not. That is the AI-side shape of "context changes the law at a matched pin," but it does not yet estimate a conditional law at matched measured states or test a pre-specified distribution. It is a handful of cases, and it says nothing yet about C2.

The analogy to clinical memory is close, not exact. A clinician recognising a pattern from last month's adverse reaction is retrieving a patient-specific precedent that is accessible only because a memory system kept it available *and* the present situation matched its activation conditions.

== Provenance-First: The Darwin Demonstration

The Darwin-corpus demonstration tested a different facet of the same principle: can a system with a curated historical corpus answer while citing its source, qualify when the source is incomplete, and abstain when the corpus does not support a conclusion?

In a four-question smoke demonstration, it did all three, with human-legible evidence display. Four questions is a demonstration, not an experiment. What it shows is that the answer/qualify/abstain contract can be *implemented*; whether it holds at scale is untested.

== Memory as Residual Evidence

SPIRAL Cortex's description of memory as _residual evidence_ deserves a pause. Memory is not a fact; it is an influence. It must pass through a gate. The gate is semantic: the memory must be relevant enough to justify influencing the policy. The gate is temporal: last week's relevance can be overridden by more recent information. And the gate is auditable: every influence is logged, so that we can ask, after the fact, why the policy behaved as it did.

Part 3 gave a biological picture that rhymes with this: depression's clearest Jacobian signature was not arrest but elevated local rotation—thought that still moves and curves back. Whether a *gating* failure is the right reading of that geometry is a plausible interpretation, not a result. SPIRAL Cortex is an attempt to build disciplined access into AI; it is not evidence about how the brain does it.

#pagebreak()

= The NDT–SPIRAL Bridge: A Shared Vocabulary

== Both Systems Use the Same Words—and Why

The biological and artificial systems in this series use the same vocabulary. Before reading the table, read this sentence: *they do so partly by construction.* The same author built both frameworks from the same motivating question—how to describe a system by the geometry of its internal state transitions rather than by its outputs. Shared words are therefore a design choice, not an independent convergence, and they are not evidence that the two systems share a mechanism.

With that stated, the table is still useful, because it says what would have to be logged for the same *questions* to be posed.

#block(fill: luma(245), inset: 1em, radius: 5pt)[
  *Trajectory.* NDT: the path of the measured state through the MNPS chart over time. SPIRALbase: the sequence of routing decisions, block activations, and bridge crossings during a recall.

  *Local flow.* NDT: first-order movement in the chart, $d x \/ d t$. SPIRALbase: settling dynamics within a block—speed and direction of convergence.

  *Accessibility.* NDT: the control-dependent law over which nearby futures are open at a matched pin (Parts 1–2). The dendritic-route reading is a Level 4 substrate hypothesis, not the definition. Hybrid-J: the $S_i$ parameter governing whether a route is open and how strongly its basin pulls.

  *Reachability.* NDT: the short-horizon second-moment cloud of likely next states. SPIRALbase: the set of candidate prototypes reachable from the current cue and working-memory state. *Design target on the AI side.*

  *Jacobian.* NDT: chart-level local derivative of the flow—stretch, shrink, shear, rotation. SPIRALbase: a local derivative of the retrieval trajectory approximated from routing scores and accessibility gradients. *Design target on the AI side.*

  *Regime.* NDT: a sustained dynamical mode (wake, NREM, REM, anaesthesia, seizure). SPIRAL Cortex: a sustained access configuration, set by two flags—`WIDTH` on/off and fine-grain on/off—with the all-off state as fail-closed boot. The analogy is loose: these are settings, not emergent modes.

  *Traversability.* NDT: capacity to move adaptively, as distinct from occupancy. SPIRALbase: whether a query can navigate from its entry point to a useful basin rather than being trapped in a local minimum.
]

== The AI Advantage

The brain is harder to study than an AI memory system in one specific respect. Neural state must be estimated from sensors. MNPS coordinates are a measurement chart. Jacobians are approximated from windowed data. Reachability is estimated, not read.

An AI memory system can log internal state directly. Here is what that looks like today, and what it is meant to become:

#block(fill: luma(245), inset: 1em, radius: 5pt)[
  *Logged today (SPIRALbase / SPIRAL Cortex traces):*
  - Selected block or prototype
  - Routing scores across candidate blocks
  - History bias (recent-use weighting)
  - Recall trace (`recall_with_trace`)
  - Lesion / control group flag
  - Access-mode flags and arbitration outcome

  *Design targets (specified, not yet exported):*
  - Workbench regime as a separate signal (hold, bridge, release)
  - Bridge permissions and activation state per step
  - Prototype focus distribution over time
  - Local Jacobian approximation
  - Reachable candidate set
]

This is cleaner than anything on the biological side. If a recall fails, the trace can be inspected. If a bridge did not open, that is in the log.

It does *not* mean that NDT-style diagnostics on AI memory are already in hand. They are designed for, partially logged, and not yet evaluated. The open question—C2 in this domain—is whether the trace carries information about outcome that the output alone does not.

== Shared Language Without Shared Substrate

The brain and SPIRALbase do not share substrate, implementation, evolutionary history, or embodiment. MNPS coordinates come from EEG; SPIRALbase coordinates come from routing scores. The neural Jacobian is estimated through a chart; the retrieval Jacobian, when it exists, will be computed from logs.

The safe claim is narrower: _both systems can be interrogated with the same three questions_—same pin, different next step? does the future-law summary carry non-redundant information? does context change the law at a matched pin?

That is how measurement frameworks travel. Thermodynamics applies to gases, liquids, and cells without claiming they are identical. The value of a shared vocabulary is that it makes comparisons *possible*. It does not make them true.

#pagebreak()

= What Would It Take? (Level 4 Speculation)

#block(fill: rgb("#fff8e1"), stroke: (left: 3pt + rgb("#f9a825")), inset: (left: 1em, right: 1em, top: 0.75em, bottom: 0.75em), radius: 3pt)[
  *Theoretical extrapolation — Level 4*

  This entire section is speculative. The mechanisms are research targets, not capabilities. They are included because the direction matters, not because results exist.
]

== Three Research Targets

If the three questions can be posed of both systems, then three biological *controls* from Parts 1–2 suggest AI analogues. None exist in the sense described here.

=== Rhythmic Variance Control in AI

In Part 1, the variance schedule $sigma(t)$ was not constant. It was modulated by rhythm: theta–gamma coupling in wake, slow-oscillation–spindle events in NREM, with the thalamic reticular nucleus as a *candidate* gate. The brain explores and commits on a schedule.

An AI memory system with Rhythmic Variance Control would alternate between high-variance exploration (testing several routes, letting bridges open broadly) and low-variance commitment (settling, suppressing alternatives, emitting an answer). The schedule would respond to current uncertainty and to the depth of the gap being resolved.

This is not uncertainty quantification with a new name. In Part 1 RVC was *structural*: the same machinery that gates access sets the variance. An AI RVC would have to be upstream of the access gates, not a confidence label on the output.

=== Synthetic Sleep

Part 1 argued that sleep is work: NREM narrows and consolidates, REM re-widens, and the nearby future at dawn is not the one at bedtime. Part 1 was also careful about what has *not* been shown: the audited datasets have not established that replay writes the landscape. The access-on-frozen-landscape question remains a question.

Synthetic Sleep would be a periodic offline phase during which the system replays recent recall trajectories, identifies routes that were frequently used or nearly missed, and adjusts accessibility $S_i$ accordingly—raising high-traffic routes, analysing failed ones by failure type (wrong accessibility, wrong bridge, wrong projector).

This is not fine-tuning. Fine-tuning changes weights in response to an explicit training signal. Synthetic Sleep would change *access* parameters in response to the system's own dynamics: a structural revision driven by the shape of the trajectory rather than the content of the answer. If it worked, it would be a software test of the "structure is not access" distinction that Part 1 could only name.

=== Embodied Anchoring for AI

In Parts 1–2, the body was a *candidate* C3 controller: vagal state and chart geometry co-modulated at the scale of task phases, and the body was not shown to steer moment-to-moment position. It set conditions.

An AI analogue would be a session-level regulation signal that biases which memory routes stay open: current project, operator, task phase, uncertainty level. It would not determine what the policy knows; it would determine which routes the policy is permitted to use.

SPIRAL Cortex's access flags are a coarse version of this. A full analogue would be continuous and graded, modulating accessibility across the landscape in real time. The research question is whether such a signal makes behaviour more predictable and auditable—the same *kind* of value the body seems to provide biologically: conditions, not melody.

#pagebreak()

= The Claim Boundary

== What NDT Does Not Claim About AI

The framework does not claim that current AI systems are conscious.

It does not claim that MNPS coordinates, applied to an AI, would measure anything equivalent to experience.

It does not claim that a high traversability or health score in SPIRALbase means what biological well-being means.

It does not claim that the parallels between Hybrid-J and cytoskeletal-dendritic accessibility are homologies. They are analogies between a software design and a Level 4 hypothesis.

It does not claim that shared vocabulary is evidence of shared mechanism. The vocabulary was shared by design.

It does not claim that Rhythmic Variance Control, Synthetic Sleep, or Embodied Anchoring for AI will be useful when built.

Most importantly: it does not claim that behavioural similarity or output quality is sufficient evidence for any of the properties the framework measures. The entire point of a geometric-diagnostic approach is that behaviour alone is an insufficient test for the kind of state dynamics the theory describes—in a brain or in a memory system.

== What the Framework Does Offer

A measurement vocabulary and three questions.

#block(fill: luma(245), inset: 1em, radius: 5pt)[
  *The narrow productive claim:*

  _For any system that exposes its internal state transitions, one can ask whether the present state determines the next step (C1), whether summaries of the local future-law carry information the output does not (C2), and whether context changes that law at a matched state (C3). NDT gives these questions a shared vocabulary. SPIRALbase and SPIRAL Cortex are systems in this research program deliberately built around these questions._
]

This is a methodological contribution, not a consciousness claim.

== The Test

Part 3 has presented the biological side: different conditions move different layers, effects are bounded, and none of it is a consciousness meter. That is the ground.

The AI side has not run the analogous test. Here is what it would be, on a fixed case set with frozen memory contents:

- *Baselines and ablations:* no memory; standard retrieval; oracle memory; shuffled memory; wrong-context (other-subsystem or other-repository) memory; local-context only; full SPIRAL Cortex. The protocol-gap runs used a subset of these. The full set is the design.
- *C1:* at matched retrieved item, do next actions differ, and does the trace say why?
- *C2:* do predeclared trace summaries add held-out information about a specified outcome or failure label beyond the output score or decision and declared current-state, cue and routing baselines? Keep correctness or failure type as the outcome, not a baseline input that reveals the answer. Replicate any added information in an independent case set.
- *C3:* at matched cue, does access mode or project context change the routing law? The inert controls are the first, small, positive sign.

If the trace features carry information that behaviour alone does not, the shared vocabulary is doing work. If they do not, the metaphor stays a metaphor, and we will have learned that from logs rather than from argument.

#pagebreak()

= Coda: The Instrument Listens

We began this series with a sentence rather than a definition: *the pin is not the future.*

Part 1 separated where a state sits from what can still happen from there, and named rhythm, body, and history as candidate controls—not as the theory.

Part 2 built the instruments: texture under the pin, what a small nudge does, how wide the next few seconds remain. It also said what those instruments are not.

Part 3 took the questions into the clinic and found that different conditions move different layers—sleep, depression, psychosis, Parkinson, coma, dementia—with cohort exports, effect sizes, and bounds. None of it a consciousness oracle.

Part 4 has asked whether an artificial memory system can be interrogated with the same three questions.

Not "could an AI be conscious?" That question may not be answerable, and nothing here bears on it. But "could an AI expose enough of its internal dynamics that C1–C3 become testable?"—that question is empirical, and the beginning of an answer is a set of logs.

An instrument is being built. It has begun to record its own movement. What remains is the experiment: whether what it records tells us anything that its answers alone do not.

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
The SPIRALbase, Hybrid-J, and SPIRAL Cortex working papers cited here are archived on Zenodo under the keys in the bibliography.

#pagebreak()
= References

#bibliography("references.bib")
