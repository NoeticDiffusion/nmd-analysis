// S4 Conceptual guide — NDT.
// Conceptual companion to the formal specification. Not a second theory and
// not a licence to restore rhythmic reconstruction as the identity of NDT.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S4 Conceptual Guide to Dynamical Accessibility",
  short-title: "S4 Conceptual guide - NDT",
  subtitle: "Where a neural state sits is not the same as what it can still become",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("accessibility", "conceptual guide", "NDT", "possible futures"),
  article-type: "Supplementary Material",
  abstract: [
    A conceptual reading of Noetic Diffusion Theory. The central move is that
    a map of the present is not the law governing what happens next: the same
    measured location need not imply the same dynamical future. Location,
    local flow, stochastic spread, destination structure, and control of
    access are different questions about that law. The measurement chart is a
    map, not the land. Rhythmic control is one candidate control mechanism,
    not the whole theory.
  ],
)

#let langell-year = (
  "langell2025ndt": "2026a",
  "langell2026_dandi000458": "2026b",
  "langell2026_ibl2": "2026c",
  "langell2026_truth_known": "2026d",
  "langell2026_thalamic_access": "2026e",
  "langell2026_trn_geometry": "2026f",
  "langell2026_ta_rolon": "2026g",
  "langell2026_hels_a": "2026h",
  "langell2026_slow_branch": "2026i",
  "langell2026_rvc_spindles": "2026j",
  "langell2026_coma_v011": "2026k",
  "langell2026_avb_omission": "2026l",
  "langell2026_dandi000574": "2026m",
  "langell2026_ndt_theories": "2026n",
)

// Keep APA year-letters identical to the main article.
#show cite: it => {
  let k = str(it.key)
  if k.starts-with("<") { k = k.slice(1, k.len() - 1) }
  if k in langell-year {
    [#hide(it) (Langell, #langell-year.at(k))]
  } else {
    it
  }
}

#show bibliography: it => {
  show "(2026b, )": [(2026g, )]
  show "(2026b). Rhythmic": [(2026g). Rhythmic]
  show "(2026c). Recovery-Linked": [(2026h). Recovery-Linked]
  show "(2026d). Trial-aligned": [(2026b). Trial-aligned]
  it
}

= Who this is for

This note is a conceptual decoder for the article, not a watered-down second
theory. The metaphors are borrowed from a longer essay written for a general
audience. The *claims* are those of the present article. In particular, NDT is
not identified with rhythmic denoising, with a consciousness scalar, or with
the measurement chart called Meta--Noetic Phase Space (MNPS).

#netn-box(title: [One sentence])[
  A useful description of a neural state includes not only *where it is*, but
  *what can still happen from there*, and *what processes change those
  possibilities*.
]

#figure(
  image("figures/conceptual/fig_s4_5_story_strip_v2.png", width: 100%),
  caption: [Reading map for this note. Each panel is a different question about the same moment.],
) <fig:s4-story>

= Same place, different futures

You wake, and for a second the room is only shapes. Then the bedside table
returns, the day returns, and you are again a person in a place. Something
in the brain took ambiguous input and assembled a usable world.

That moment is a good *intuition pump*. It is not a proof. Earlier NDT used
rhythmic reconstruction as its primary explanatory framing. The present
formulation asks a broader dynamical question: given a measured state now,
what distribution of nearby futures remains available, and what can reshape
that distribution?

Two people can occupy similar coordinates on a coarse map and still differ in
what happens next. One can leave a shock and return to ordinary life; another
stays in the same valley. A weather map that only reports "here" cannot tell
those stories apart. NDT keeps "here" and "what can happen from here" as
separate scientific objects @langell2025ndt.

#figure(
  image("figures/conceptual/fig_s4_1_same_place_different_futures_v2.png", width: 100%),
  caption: [Same measured state, different future law. Matching the present pin does not imply matching drift, stochastic spread, destination probabilities, or finite-horizon transition structure.],
) <fig:s4-c1>

That is C1, and much of C2, in one picture. The pin on a reduced map need not
determine the law of nearby futures. In some distinct neural regimes,
summaries of that future law carry information that location and ordinary
spectral scores do not.

= One state, several questions

Imagine a hiker on a ridge in fog. A GPS pin answers one question: *where?*
That pin does not answer the others.

1. *Where is the system?* A low-dimensional chart --- in this theory, MNPS,
   with axes that operationally track mobility or coordination ($m$),
   deviation from an integration--segregation balance ($d$), and entropy or
   complexity pressure ($e$) --- reports a location. A nine-dimensional
   refinement adds texture, as elevation is not the same as geology. Two
   recordings can occupy similar 3D coordinates while differing in local flow,
   stochastic spread, or short-horizon prediction. The chart is a *map*. It is
   not the latent neural process, and it is not NDT.

2. *Which way does the ground slope?* Local drift is the systematic tendency
   of motion: downhill on a potential, around a cycle, or along some other
   flow.

3. *What happens to a small nudge?* A Jacobian describes how the local flow
   changes around the point: if two nearby states are nudged apart, does
   their separation grow, shrink, shear, or rotate? Drift is which way the
   hiker is already being carried; the Jacobian is what happens to nearby
   hikers. Current Jacobian summaries here are *chart-level* measurements.
   They are not intrinsic tensors of a unique brain manifold.

4. *How does the weather spread?* Stochastic diffusion is not a single noise
   knob. It has size, shape, and preferred directions. Two states can share a
   slope and differ in how fluctuations fan out --- a narrow corridor versus
   a broad fan.

5. *What nearby futures remain likely?* Short-horizon *predictive spread* is
   a second-moment picture of those futures, not classical control-theoretic
   reachability and not a list of every physically possible brain state. A
   large occupied cloud on the map is not the same as a wide horizon of
   possible next moves.

6. *Toward which destination?* A committor asks a different question still:
   if two basins compete, which one is favoured?

7. *What if the shove is no longer tiny?* Finite-amplitude resilience asks
   whether a larger displacement changes the regime.

These objects can come apart. That is why they must not be collapsed into a
single "dynamical complexity" score.

#figure(
  image("figures/conceptual/fig_s4_2_one_state_questions_v2.png", width: 100%),
  caption: [The same moment supports non-equivalent dynamical questions. The main article's Figure 3 is the formal companion; this panel is the hiker version.],
) <fig:s4-questions>

The theory's three commitments, in the same language:

- *C1.* The pin on a reduced map need not determine the law of nearby
  futures.
- *C2 (non-redundant accessibility).* In some distinct neural regimes,
  summaries of that future law carry information that location and ordinary
  spectral scores do not.
- *C3.* Context, history, or physiology can change the future law among
  observations that sit at the same pin.

A coarse map losing information is not, by itself, evidence for NDT. The
stronger test is whether the missing future structure can be measured
reproducibly and whether defined conditions systematically reshape it. C3 is
not the generic observation that extra covariates improve prediction. It asks
whether nominated physiological or contextual variables change defined
features of the future law at a matched pin.

That is the whole load-bearing structure. Rhythm, thalamus, sleep spindles,
coma geometry, and body signals are candidate ways of changing the law. They
are not extra definitions of NDT.

= The map is not the land

Brain recordings --- EEG, MEG, spikes, field potentials --- are observations
of a latent process we do not fully see. A pipeline then builds features and
projects them onto a chart. NeuralManifoldDynamics is one versioned contract
for doing that. When the contract changes, the version number should change.
A pretty embedding plus a correlation is still only association. Recovering
a local dynamical operator --- something that correctly predicts a short
future or a perturbation --- is a much stronger claim, and on at least one
meso-to-macro recording it fails even when coarser association succeeds.

Think of a subway map. It is invaluable for getting across town. It is a
terrible geological survey. MNPS is closer to the subway map. Using it as if
it were the terrain is how a measurement chart gets mistaken for a theory of
mind.

#figure(
  image("figures/conceptual/fig_s4_4_map_not_land_v2.png", width: 92%),
  caption: [The map is useful precisely because it is not the land. Estimates of local dynamics are made through the chart, not as transparent views of the latent process.],
) <fig:s4-map>

= Same place, different controls

If the present pin does not fix the future law, something else can. C3 is
the plain-language question: *what can reshape the distribution without
moving the present point?* The theory groups those somethings into a few
classes, not a catalogue of subsystems.

#figure(
  image("figures/conceptual/fig_s4_3_control_matched_state_v2.png", width: 100%),
  caption: [Conditional accessibility. Context can change the future law at matched present state. In the strongest version of the example, even the underlying landscape may remain unchanged while access to routes changes.],
) <fig:s4-c3>

*Fast rhythmic and access control.* The simplest special case is still
Rhythmic Variance Control: a rhythmic proxy that turns isotropic noise up or
down, as a conductor might ask the orchestra for *forte* or *piano*. That is
one slot in the local law. It is not a proof that sleep spindles write
memory, clamp variance, or implement consciousness. Thalamic circuitry is a
*candidate* access architecture --- a possible way to rotate spread or open
channels --- not an identified biological executor.

*History.* A stored landscape of preferences is one question: where did the
hills come from? A different question is whether, with the hills held fixed,
a context operator can still change which routes are easy.

*Physiology.* Heartbeat, breath, and metabolic adequacy may condition what is
feasible, as a bass line conditions a room without composing the melody.
They are not extra MNPS axes and not consciousness coordinates. Autonomic
composites did not moderate the primary spindle-geometry effect under the
tested protocol.

= Structure is not access

NDT repeatedly separates *what is stored or structurally available* from
*what is dynamically accessible now*. Changing access need not require
rewriting the underlying structure.

That distinction is not only a hippocampal story. It is the same logical
move at several scales: memory content versus retrieval; a potential $V$
versus mobility or gating; a stored landscape versus a context-conditioned
route; an attractor versus a committor; a dendritic substrate versus which
branch is currently easy. The currently audited hippocampal datasets have not
established landscape writing. The access-on-frozen-landscape question is a
different question, and it remains a question.

= What the companion studies actually showed

These are constraints, not a validation of the chain.

*Spindles.* In two overnight EEG datasets, a discrete spindle event coincides
with a modest, timing-locked rise in one stratified chart coordinate
($d_n$). That is event-locked *state* reconfiguration. It is not causal
denoising, not a complete spindle-versus-matched-N2 mechanism, and not
thalamic identification. Matched-control specificity is incomplete
@langell2026_rvc_spindles.

*Coma.* In early EEG after cardiac arrest, short-horizon spread and local
deformation carry recovery-linked information that static location does not
exhaust. Geometry added a bounded increment on a feature-limited
clinical-plus-qEEG baseline. Withdrawal of life-sustaining therapy and
sedation were not available. Read as recovery-linked geometry, not as a
viability assay and not as a consciousness meter
@langell2026_coma_v011.

*Meso to macro.* Simultaneous Neuropixels and surface EEG can covary under
careful nulls. The same EEG-only chart does not recover a local flow or
reachability operator. Contact across scales is real at association. It is
not operator identification @langell2026_dandi000458.

Other companions --- depression, psychosis, gambling versus cognitive
control, hypoglycaemia, infant age --- mainly show that *different
conditions move different layers*. That pattern is the result. Reduced
spread is not itself reduced consciousness. Complexity scores can separate
global state from reported experience within a state; NDT has not been shown
to do better @bajwa2025repeated.

= What this is not

- Not a bedside score, CPC substitute, or test of awareness.
- Not Integrated Information Theory's $Phi$, workspace ignition, or a report.
- Not the claim that "noetic" means knowledge-bearing structure in the
  coordinates. The name marks the intended domain of mind-relevant dynamics.
- Not a completed theory of why any of this should *feel like* anything.
- Not a licence to treat every named object (committor, finite-amplitude
  resilience, dendritic access) as an empirical export. Several remain
  questions.

If, after matching state, responsiveness, arousal, power, and complexity, the
future law still failed to distinguish reported experience from no reported
experience, NDT would remain a theory of enabling dynamics. That test is
named in the main text. It has not been run.

= A short translation table

#figure(
  kind: table,
  clean-table(
    columns: (1.3fr, 2.2fr),
    align: (left, left),
    inset: 5pt,
    table.header([*Technical object*], [*Plain question*]),
    [Chart $x_t$ / MNPS], [Where does this recording sit on the current map?],
    [Drift $b$], [Which way does the local flow point?],
    [Mobility $M$ and potential $V$], [How much of that flow is downhill on a landscape, and in which geometry?],
    [Diffusion $a$], [How do random fluctuations spread, and in which directions?],
    [Jacobian $J$], [If nearby states are nudged apart, does their separation grow, shrink, shear, or rotate?],
    [Predictive-spread ellipsoid], [How broad is the short-horizon cloud of likely next states?],
    [Committor $q$], [Toward which of two destinations is the process committed?],
    [Control / protocol $gamma$], [What is allowed to change the future law at the same present pin?],
    [RVC], [The smallest such controller: a rhythm that turns isotropic noise up or down.],
  ),
  caption: [The main paper's objects, without the symbols doing the work. Empirical availability of each row is a separate contract.],
)

The orchestra metaphor is useful only up to a point. Keep bass line, rhythm
section, fog, and ridge if they help. Then put the baton down. The scientific
claim is simpler: mind-relevant neural regimes may be better characterized by
a controlled law over possible futures than by present reduced-state location
alone.

Year-letter suffixes for Langell (2026) follow the main article (2026a--n).

#bibliography("references.bib", style: "apa")
