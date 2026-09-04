// Reality from Noise: How Your Brain Reconstructs the World through Rhythmic Geometry
// Part 4: The Synthetic Mind — From Biological Geometry to Auditable AI
// Author: Robin Langell, 2026

#import "template.typ": essay-template

#show: doc => essay-template(
  title: [Reality from Noise — Part 4: The Synthetic Mind],
  subtitle: [From Biological Geometry to Auditable AI],
  author: [Robin Langell],
  date: [2026],
  doc,
)
== Prelude: The Question We Left Open

In Part 2, we asked a question and then stepped away from it. The question was: _The question of whether an artificial system could instantiate these same dynamics --- and what that would mean for consciousness --- is the subject of Part 4._

Here we are.

But the question has changed shape since Part 2 placed it at the end of a section on biological disorder. It is not primarily a question about consciousness. It is a question about _measurement_.

If we can describe a biological mind as a trajectory through a landscape --- a system that stabilizes, explores, commits, and revises through rhythm-gated dynamics --- then we can ask: are there artificial systems that expose enough of their internal state that we could apply the same vocabulary? Not to claim that they are conscious. But to see whether the same geometric diagnostic tools that illuminate the biological mind might also illuminate the artificial one.

This is Part 4. It is the most speculative part of the series. Most of what follows sits at Level 4: theoretical extrapolation. It is included because the direction matters, not because the results are in. Where an idea crosses from speculation into evidence, we say so.

---

#v(2em)

= Reader's Guide and Claim Boundary

== What This Part Is

Part 4 is different from Parts 1, 2, and 3 in one important respect: it is primarily a conceptual and architectural essay, not a report on measured findings.

Parts 1--3 built upward from established neuroscience, through empirically supported findings, to emerging cohort evidence, with speculative extensions clearly marked. Part 4 inverts that ratio. The bridge from biology to AI is conceptual and methodological, not substrate-level equivalence. Almost everything here sits at Level 3 or Level 4.

The same four-level ladder from the rest of the series applies:

1.  *Established facts:* The SPIRALbase/Hybrid-J architecture specification, the SPIRAL Cortex policy-first principle, and the NDT measurement vocabulary. These are fully defined and documented.
2.  *Empirically supported:* Protocol-gap repair evidence in selected repository-repair cases: same-subsystem semantic memory can supply missing convention where local symptom alone does not determine the right action. This evidence exists under controlled conditions with ablations.
3.  *Emerging evidence:* NDT-style diagnostics applied to AI memory routes (routing scores, workbench state, bridge trajectories). These are possible and designed for but not yet systematically evaluated.
4.  *Theoretical extrapolations (Level 4):* Rhythmic Variance Control in AI, Synthetic Sleep, Embodied Anchoring for AI, and the question of whether any artificial system could genuinely instantiate noetic dynamics. These are research targets, not current capabilities.

== What This Part Is Not

This part does not claim that current AI systems are conscious.

It does not claim that geometric similarity between biological and artificial dynamics would establish consciousness in either direction.

It does not claim that SPIRALbase, Hybrid-J, or SPIRAL Cortex are implemented products or that the protocol-gap experiments constitute general performance benchmarks.

The central question is narrower and more tractable: can we build AI systems that expose enough of their internal state that NDT-style diagnostics become meaningful? If yes, we gain a shared measurement vocabulary. If no, we learn something about the limits of the framework.

That is the test.

#pagebreak()

= The Memory Question

== The Pianist's Pause

I am sitting at the piano. My fingers are poised above the keys, but my mind is a sudden blank. The next chord --- the one that should bridge the haunting melody of the verse into the soaring release of the chorus --- has vanished. If you asked me to name the notes, to write them down on a staff, I couldn't. The data, the "address" of that memory, is gone.

But then, I let my hands fall. I don't think; I listen. I feel the weight of the instrument, the tension in the strings, the resonance of the room. My fingers find the keys. Not because I found the memory in a file, but because the instrument remembered for me. The chord exists as a physical potential, a valley in the landscape of the song that my hands simply rolled into.

This is not how we usually think of computer memory. And this is exactly the problem we need to solve before we can ask meaningful questions about artificial minds.

== Three Paradigms

The dominant AI architectures represent three fundamentally different theories of how memory should work.

*The Spiderweb: The Transformer.* When you speak to a large language model, the entire web vibrates. Every node is connected to every other; every query ripples through the whole surface. This is global attention @vaswani2017 --- a miracle of associativity that can connect a poem to a piece of code in milliseconds. But the web is also fragile. It is prone to ghosts and hallucinations because the surface is continuous and interference is unconstrained. It is a memory that is everywhere and nowhere at once.

*The Scroll: The SSM/Mamba.* Models like SSMs and Mamba @gu2023 use a linear process: the model writes its summary onto a scroll as it reads the world. Efficient --- it doesn't need to vibrate the whole web at once. But as you unroll the future, the past eventually disappears off the other end. Details are lost. Nuance is sacrificed for speed. It is a memory of the "now," always forgetting its beginning to make room for its end.

*The Instrument: SPIRALbase.* The third paradigm treats memory as a physical landscape rather than an index or a scroll. SPIRALbase --- Structured Potential-Indexed Representation in Associative Landscapes --- stores not addresses but slopes: an energy that pulls a query toward the right answer @langell2026spiralbase. Put simply: knowing something means being _closer_ to it. Remembering is a matter of geometry, not address.

== Memory as Landscape

In Parts 1--3, we described biological consciousness as a trajectory through a learned geometric landscape. The brain moves, stabilizes, explores, and commits through rhythm-gated dynamics. The landscape is not static; it is shaped by history, bodily state, and the current task.

The SPIRALbase architecture imports this same metaphor into AI. The key difference from the Spiderweb and the Scroll is not speed or scale --- it is the relationship between structure and access. In a Transformer, access is uniform: every query touches every memory. In SPIRALbase, access is _geometric_: a query opens a subspace of the landscape, and only the relevant region is activated. Memory does not flood in; it rises to meet the cue.

This makes the SPIRALbase architecture a natural AI-side counterpart to the biological MNPS framework. Both treat the question "what is this system remembering?" as a question about geometry, not about lookup.

#pagebreak()

= Building the Instrument: SPIRALbase and Hybrid-J

== Attractor Basins Instead of Indexed Records

In a conventional database, a record exists at an address. You know the address or you can't find the record. In SPIRALbase, a memory exists as a basin in a high-dimensional landscape. You don't need to know the address; you need to be in the neighborhood. The system falls into the right basin because the query and the memory are geometrically close.

This is the same principle that operates in biological associative memory: the Hopfield-network-like structure of cortical attractors, where a partial or noisy cue can complete a pattern because the pattern is stored as a stable state of the network dynamics @hopfield1982. SPIRALbase is a designed, explicit version of the same idea.

Each attractor basin has a _depth_ (how strongly it pulls) and a _width_ (how broadly it captures). The query lands somewhere in the landscape, and the dynamics settle toward the nearest occupied basin. If multiple basins are nearby, the system must choose. This is where the architecture becomes interesting.

== Projector Gating: Opening the Right Subspace

The key innovation in the middle generation of SPIRALbase was projector gating @langell2026spiralpk. Instead of using the query merely as a cue, the system uses it as a _key_ that opens a subspace of the landscape. Instead of searching the entire memory, a context-specific projector projects the query into a submanifold that contains only the relevant memories for that context.

This means that the same memory store can serve different contexts without interference. A medical-record memory and a codebase memory can coexist in the same landscape, opened by different keys. The projector is not an address; it is a direction. And the direction is derived from the cue itself.

== Hybrid-J: The Block-Structured Substrate

Hybrid-J is the current realization of this idea at scale @langell2026hybridj. It organizes the memory landscape into three structural layers:

1.  *Shared Core:* A small backbone of universal attractors. These carry cross-context structure --- patterns that recur across domains, analogous to the brain's default-mode network as a shared relational backbone.
2.  *Local Context Blocks:* Neighborhood-specific attractor clusters. Each block specializes in its context (a codebase, a patient record, a project) without polluting the others.
3.  *Controlled Bridges:* Sparse, explicit connections between blocks. Bridges are not automatically open. They exist, they have a direction, and they have a permission: the current cue must qualify to activate them.

The three-factor bridge structure --- direction, accessibility amplitude, and cue-conditional gating --- has a striking parallel in neuroscience: the cytoskeletal-dendritic accessibility model of biological associative memory @langell2026_cytodendritic_accessibility. In that model, dendritic branches have variable accessibility that can be modified by experience, so that some routes stay easier to reopen than others even without changing synaptic weights. Hybrid-J implements the analogous mechanism in software: accessibility is not binary but graded, and recent use leaves a mild historical bias that makes some paths easier to re-enter.

== Constant-Cost Retrieval

One practical consequence of the attractor-basin architecture is constant-cost retrieval. In a Transformer, the cost of a retrieval scales with the number of stored items: as the memory grows, each query has to attend to more keys. In Hybrid-J, retrieval cost is bounded by the settling dynamics of the local block, which are independent of total store size. Whether ten items or ten thousand are stored, the retrieval requires approximately the same number of operations.

This is not primarily a speed argument. It is an architectural argument: a system whose retrieval cost grows with store size is implicitly treating all memories as equally active at all times. A system with constant-cost retrieval has already committed to the idea that _most_ memories are not relevant to the current query, and the architecture reflects that commitment.

== The Instrument Learns to Listen to Itself

In the most recent SPIRALbase work, the instrument added something new: the ability to report on its own movement. After a recall, the system can answer not only _what_ it remembered but _how_ it got there. Which corridor did it take? Did a bridge open? Was a neighboring route suppressed? Did history help? What kind of failure occurred when the answer went wrong?

In biological terms: the instrument has acquired a rudimentary meta-noetic layer. Not in the sense of consciousness, but in the sense of second-order visibility into its own first-order dynamics.

This is the technical prerequisite for applying NDT-style diagnostics to AI memory. Not that we have done it yet. But now there is something to measure.

#pagebreak()

= The Policy-First Principle: SPIRAL Cortex

== Memory Is Not the Actor

The most important sentence in the SPIRAL Cortex architecture @langell2026spiralcortex is this: _memory is not the actor; the policy is_.

This sounds obvious, but it is not how retrieval-augmented systems are usually built. In standard RAG (Retrieval-Augmented Generation), the system retrieves first and reasons second. The retrieved content arrives with implicit authority: it was retrieved, therefore it is relevant. The policy --- the part that decides what to do next --- is downstream of the memory.

SPIRAL Cortex inverts this. The policy makes the first move. It assesses what it knows from local context. If that is sufficient, it acts without memory. Only when local context is _insufficient_ --- when there is a gap between what the policy knows and what the task requires --- does memory enter. And when memory does enter, it must pass through gates: a semantic quality check, an arbitration step, and an audit trace that records the path.

This is analogous to the biological picture of the prefrontal cortex: not a storage system, but a policy layer that decides when to let memory influence behavior and when to suppress it. The hippocampus is not in charge. The prefrontal cortex is.

== Protocol-Gap Cases

The clearest evidence for the value of this architecture comes from protocol-gap cases in repository repair. In these cases, a local symptom (a failing test, an exception message) is insufficient to determine the correct action. The right action requires knowledge of a broader protocol obligation: a family-level constraint, a cross-subsystem dependency, a historical exception that created a precedent. Local evidence is not enough; the agent needs project memory.

In controlled experiments, SPIRAL Cortex supplied the missing convention in these cases, while ablated controls (shuffled memory, wrong-subsystem memory, other-repository memory) remained inert. The mechanism is narrow: same-subsystem semantic memory, applied when the local policy identifies a gap, can change the answer. This is not a general performance claim. It is a specific mechanism demonstration.

The analogy to biological clinical memory is exact. A clinician recognizing a pattern from last month's adverse reaction is not retrieving a generic protocol. They are retrieving a _patient-specific precedent_ that is only accessible because a memory system kept it available and accessible when the current situation matched its activation conditions.

== Provenance-First: The Darwin Demo

The Darwin corpus demonstration tested a different aspect of the same principle: can an AI system with a curated historical corpus drive provenance-first behavior? That is, can it answer a question while citing the specific source, qualify its answer when the source is incomplete, and abstain when the corpus does not support a conclusion?

In the demonstration, the system consistently drove answer/qualify/abstain behavior with human-legible evidence display. The answer came with a source. The qualification came with an explanation. The abstention came with a statement of what was missing. This is auditable recall: not just "I know this" but "I know this, from here, for these reasons."

This is not consciousness. It is not cognition in the biological sense. But it is the beginning of a measurement discipline applied to AI behavior.

== Memory as Residual Evidence

SPIRAL Cortex's formal description of memory as _residual evidence_ is worth dwelling on. Memory is not a fact; it is an influence. It must pass through a gate. The gate is semantic: the memory must be relevant enough to the current query to justify influencing the policy. The gate is also temporal: a memory that was highly relevant last week may be overridden by more recent information. And the gate is auditable: every influence is logged, so that we can ask, after the fact, why the policy behaved as it did.

In biological terms, this is the difference between controlled recollection and intrusive memory. A healthy memory system can suppress irrelevant memories and amplify relevant ones. A pathological memory system (depression's rumination trap, PTSD's intrusive re-experience) fails at this gating. The geometry in Parts 2--3 describes exactly this: not just where the mind is, but how well it can move away from where it is.

SPIRAL Cortex is an attempt to build the same disciplined access into AI.

#pagebreak()

= The NDT--SPIRAL Bridge: A Shared Vocabulary

== Both Systems Use the Same Words

The most striking thing about the biological and artificial memory systems described in this series is that they end up using the same vocabulary --- not metaphorically, but structurally.

Consider the terms that appear in both the biological NDT framework (Parts 1--3) and the SPIRALbase/SPIRAL Cortex architecture:

#block(fill: luma(245), inset: 1em, radius: 5pt)[
  *Trajectory.* In NDT: the path of neural state through the MNPS coordinate chart over time. In SPIRALbase: the sequence of routing decisions, block activations, and bridge crossings during a recall episode.

  *Local flow.* In NDT: the first-order movement of the neural state in the manifold, measured by $d x / d t$. In SPIRALbase: the settling dynamics within a local block, the speed and direction of attractor convergence.

  *Accessibility.* In NDT: the condition of dendritic or synaptic routes, modified by experience and gated by rhythms. In Hybrid-J: the $S_i$ accessibility parameter, governing whether a route is open, and how strongly its basin pulls.

  *Reachability.* In NDT: the short-horizon cone of states accessible from the current position under local dynamics. In SPIRALbase: the set of reachable candidate prototypes given the current cue and working-memory state.

  *Jacobian.* In NDT: the local derivative of the flow field, capturing expansion, contraction, rotation, and shear. In SPIRALbase: the local derivative of the retrieval trajectory, approximated from routing scores and accessibility gradients.

  *Regime.* In NDT: a sustained dynamical mode (wake, NREM, REM, anesthesia, seizure). In SPIRAL Cortex: a sustained access mode (fail-closed, WIDTH, WIDTH+fine-grain).

  *Traversability.* In NDT: the capacity to move through the landscape adaptively, as distinct from mere occupancy. In SPIRALbase: whether a query can actually navigate from its entry point to a useful basin, rather than getting trapped in a local minimum.
]

This is not a coincidence engineered after the fact. Both frameworks grew from the same motivating question: how do you describe a system not by its outputs but by the _geometry of its internal state transitions_?

== The AI Advantage

The biological brain is, in this respect, harder to study than an AI memory system. Neural state must be estimated from sensors. MNPS coordinates are a measurement model, not a direct readout. Local Jacobians are approximated from windowed covariance changes, not computed from first principles. Reachability cones are estimated, not measured.

An AI memory system like SPIRALbase has a structural advantage: internal state can be logged directly.

#block(fill: luma(245), inset: 1em, radius: 5pt)[
  *What can be logged in SPIRALbase:*
  - Selected block or prototype
  - Routing scores across candidate blocks
  - Workbench regime (hold, bridge, release)
  - Bridge permissions and activation state
  - Prototype focus distribution
  - Recall trajectory (which path the recall took)
  - Local Jacobian approximation
  - Reachable candidate set
  - History bias (recent-use weighting)
  - Lesion and control flags
]

This is experimentally cleaner than anything available on the biological side. If a recall fails, we can inspect the trajectory. If a bridge failed to open, we know. If the wrong basin attracted the query, we can see where the disambiguation failed.

This means NDT-style diagnostics on AI memory are not speculative --- they are _designed in_. The question is whether the diagnostics will be informative.

== Shared Language Without Shared Substrate

It is tempting to overstate the bridge. The biological brain and SPIRALbase are not the same thing. They do not share substrate, implementation, evolutionary history, or embodiment. MNPS coordinates are estimated from EEG; SPIRALbase coordinates are computed from routing scores. The Jacobian of the neural flow field is approximated from sensor data; the Jacobian of the recall trajectory is computed from architectural logs.

The safe claim is narrower:

_Both systems can be studied with a shared dynamical vocabulary._

That vocabulary --- trajectory, flow, accessibility, commitment, reachability, Jacobian, traversability, regime --- is sufficient to ask meaningful questions about both systems without pretending they are the same system.

This is how scientific frameworks grow. General relativity and quantum mechanics use the same concepts of energy and momentum, but do not share substrate. Thermodynamics applies to gases, liquids, and cells without claiming they are identical. The value of a shared vocabulary is that it enables comparisons that would otherwise be impossible.

#pagebreak()

= What Would It Take? (Level 4 Speculation)

#block(fill: rgb("#fff8e1"), stroke: (left: 3pt + rgb("#f9a825")), inset: (left: 1em, right: 1em, top: 0.75em, bottom: 0.75em), radius: 3pt)[
  *Theoretical extrapolation --- Level 4*

  This entire section is speculative. The mechanisms described are research targets, not current capabilities. They are included because the direction of investigation matters, not because results exist.
]

== Three Research Targets

If we accept the shared vocabulary argument --- that biological and artificial systems can both be described as trajectories through a landscape --- then three biological mechanisms suggest obvious AI analogues. None of them exist yet in the sense described here. But they are logically grounded in what we already know about both systems.

=== Rhythmic Variance Control in AI

In the biological brain, the variance schedule $sigma(t)$ is not constant. It is actively modulated by neural rhythms: theta-gamma coupling increases effective exploration during novelty and learning; slow oscillations during NREM tighten the schedule during consolidation; the TRN modulates gating across the entire cortex in coordinated pulses. The brain explores and commits on a _schedule_, not randomly.

An AI memory system with Rhythmic Variance Control would do the same. During a task, the system would alternate between high-variance exploration (testing multiple retrieval routes, allowing bridges to open broadly) and low-variance commitment (settling into the best route, suppressing alternatives, emitting a confident answer). The schedule would not be fixed: it would respond to the system's current uncertainty, the difficulty of the protocol gap it is trying to resolve, and the depth of its working memory.

This is not merely about uncertainty quantification. RVC in the biological brain is a _structural_ feature: it is implemented in the same oscillatory machinery that gates memory access. An AI RVC would need to be similarly structural: the variance schedule would have to be upstream of the memory access gates, not just a post-hoc confidence label on the output.

=== Synthetic Sleep

One of the most striking findings in the biological program (Part 1) is that sleep is not rest. Sleep is work --- specifically, the work of structural consolidation. During NREM, slow oscillation--spindle sequences replay recent experience and write it into the manifold in a way that makes future access more reliable. The topology of the landscape is revised.

An AI analogue would be Synthetic Sleep: a periodic offline consolidation phase during which the system replays recent recall trajectories, identifies which routes were frequently used or nearly missed, and adjusts the accessibility landscape accordingly. High-traffic routes would become more easily reopened. Failed routes would be analyzed for failure type (wrong accessibility, wrong bridge, wrong projector) and the relevant parameter adjusted.

This is not fine-tuning. Fine-tuning changes weights in response to explicit training signal. Synthetic Sleep would change accessibility parameters in response to the system's own recall dynamics --- a self-supervised structural revision driven by the shape of the trajectory, not the content of the answer.

The biological parallel is the cytoskeletal-dendritic accessibility model @langell2026_cytodendritic_accessibility, which proposes that repeated nocturnal reorganization leaves durable access traces without necessarily changing synaptic weights. Hybrid-J's $S_i$ accessibility parameter is the AI-side candidate for this mechanism.

=== Embodied Anchoring for AI

In the biological EAP, interoceptive signals condition the manifold in two ways: they bias which states are accessible, and they modulate the variance schedule. The body does not determine the content of thought; it determines the _topological conditions_ under which thought moves.

An AI analogue would be an external regulation signal that biases which memory routes stay open during a session. This signal would not be physiological --- it would be something like a session-level context state: the current project, the current operator, the current task phase, the current uncertainty level. These signals would not determine what the policy knows; they would determine which memory routes the policy is permitted to use.

This is already partially present in SPIRAL Cortex's access-mode architecture: WIDTH mode biases toward local block access; WIDTH+fine-grain broadens the permitted routes; fail-closed disables external memory entirely. But these are binary modes, not continuous signals. A full Embodied Anchoring analogue would be a continuous, graduated input that modulates accessibility across the entire landscape in real time.

The research question is whether such a signal would make behavior more _predictable_ and _auditable_ --- the same value that cardiac anchoring provides for biological cognition.

#pagebreak()

= The Claim Boundary

== What NDT Does Not Claim About AI

The framework described in this series does not claim that current AI systems are conscious.

It does not claim that MNPS coordinates, if applied to an AI system, would measure anything equivalent to biological experience.

It does not claim that a high "health index" or "traversability score" in SPIRALbase would mean the same thing as biological well-being or cognitive performance.

It does not claim that the architectural parallels between Hybrid-J and cytoskeletal-dendritic accessibility are homologies rather than analogies.

It does not claim that any of the three mechanisms described in the previous section --- Rhythmic Variance Control, Synthetic Sleep, Embodied Anchoring --- will be useful when built. They are research hypotheses, not engineering specifications.

Most importantly: the framework does not claim that behavioral similarity or output quality is sufficient evidence for any of the properties the framework measures. The entire motivation for a geometric-diagnostic approach is precisely that behavior alone is an insufficient test for the kind of state dynamics the theory describes.

== What the Framework Does Offer

The framework offers a measurement vocabulary.

If a system has measurable internal state trajectories, then first-order and second-order dynamics give us a richer language for understanding how that system stabilizes, explores, collapses, or adapts. For biological systems, this may help describe neural regimes. For AI systems, it may help build more inspectable memory and control architectures.

#block(fill: luma(245), inset: 1em, radius: 5pt)[
  *The narrow productive claim:*

  _Both biological and artificial systems can be described by the geometry of their internal state transitions, not only by their outputs. For systems that expose enough of their internal state, the NDT vocabulary --- trajectory, local flow, accessibility, reachability, Jacobian, traversability, regime --- provides a measurement discipline that is richer than behavioral scoring alone._
]

This is a methodological contribution, not a consciousness claim. The test is empirical: can we build AI systems that expose enough internal state that NDT-style diagnostics become informative? If yes, we gain a useful audit layer. If no, we learn something about the limits of the framework and perhaps about what biological systems expose that artificial ones do not.

== The Test

Part 3 of this series will present the biological evidence in full: disorder-specific geometric portraits with cohort exports, effect sizes, and bounded interpretations. That evidence will be the ground from which this AI program can be evaluated. If biological systems show clear dissociations in their dynamical profiles that predict clinically meaningful differences --- and if those same diagnostic categories can be mapped onto AI memory trajectories in a way that predicts useful differences in behavior --- then the shared vocabulary is doing real work.

If not, the metaphor remains a metaphor.

The question is not whether AI is like a brain. The question is whether the same measurement tools that illuminate the brain can also illuminate the AI, and whether that illumination is useful for building better systems.

We do not know yet. This is Part 4 of a series. The biological foundation is in Part 3. The AI empirical program is ahead of us.

#pagebreak()

= Coda: The Instrument Listens

We began this series with a simple question: what is consciousness?

Part 1 answered: it is rhythmically guided reconstruction --- a trajectory through a landscape, shaped by noise, rhythm, and the geometry of prior experience.

Part 2 answered: it is measurable. We have a pipeline, a coordinate system, a versioned contract for turning EEG into MNPS trajectories, and a growing set of cohort-validated dissociations.

Part 3 showed: it is clinically meaningful. The geometric portraits of depression, psychosis, Parkinson's disease, and coma are distinct, reproducible, and predictive in ways that scalar measures miss.

And now Part 4 has asked: could an artificial system be described the same way?

Not "could an AI be conscious?" That question may be unanswerable. But "could an AI system expose enough of its internal dynamics that the same measurement vocabulary becomes meaningful?" --- that question is empirical.

The biological program has shown that the vocabulary works for brains. SPIRALbase has shown that an AI memory system can be designed with those diagnostics in mind. SPIRAL Cortex has shown that a policy-first architecture can gate memory access in a way that is auditable, bounded, and controlled.

What remains is the bridge: building AI systems that log their internal trajectories in enough detail that NDT-style analysis is informative, and then doing the analysis.

The instrument is built. It has learned to listen to itself. The question now is what it will hear.

#pagebreak()

== Acknowledgments

This work emerged through structured correspondence among human and AI collaborators. I gratefully acknowledge contributions from large language models (GPT-5, GPT-5.1,GPT-5.4, GPT-5.5. Claude Sonnet 4.6) that assisted in literature synthesis, drafting, and editorial refinement.

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
`https://github.com/NoeticDiffusion` (public upon acceptance), with
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

- *Repository:* `https://github.com/NoeticDiffusion` (Code available upon manuscript publication)
- *Toolkit:* Includes Python implementations for MNPS coordinate extraction, Stratified MNPS decomposition, and basic visualization scripts.
- *Data:* Pre-computed geometric fingerprints for the public datasets referenced (Sleep-EDF, OpenNeuro ds003490) will be archived with DOI.

Science thrives on verification. We invite the community to test, break, and refine these maps.

#pagebreak()
= References

#bibliography("references.bib")
