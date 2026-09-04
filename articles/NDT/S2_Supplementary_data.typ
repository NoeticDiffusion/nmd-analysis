// S2 Supplementary: NDT subsystem extensions (CCTG, HELS, NDT-Q) and
// candidate TRN substrates. Moved out of the NoeticDiffusionTheory.typ
// main-text Appendix to keep the main article focused on Tier-1 claims.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary: Subsystem Theoretical Extensions",
  short-title: "S2 Subsystems - NDT",
  subtitle: "Context-Conditional Transition Geometry (CCTG), the Hippocampal--Entorhinal Landscape System (HELS), NDT-Q operational content sections, and candidate TRN substrates",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

#set par(leading: 0.8em, spacing: 0.6em)
#set math.equation(supplement: none)
#show math.equation: set block(above: 1em, below: 1em)

#netn-box(title: [Relation to the main article])[
  This supplement expands three appendix pointers from the main article
  (`NoeticDiffusionTheory.typ`, Appendix): *Subsystem extensions: CCTG and
  HELS*, *NDT-Q: operational content sections*, and *Candidate TRN substrates
  and CCTG*. None of these is a Stage-1 result. They are speculative or
  infrastructure-only extensions that must earn support through their own
  dedicated causal or reversal tests.
]

= S2.0 Subsystem extensions: CCTG and HELS

Context-Conditional Transition Geometry (CCTG) is a speculative replacement
for universal TRN--variance-gate language. It proposes a context- and
circuit-dependent contribution to the drift field,

#math.equation(block: true,
  $
    d X_t = [b_0(X_t,t) + u_k(t) K^("TRN")_(k,c)(X_t)] d t
      + Sigma_t d W_t.
  $
) <eq:cctg>

Here $K^("TRN")_(k,c)$ is a transition-field hypothesis, not an identified
diffusion controller. CCTG predicts context-dependent changes in labeled
representation transitions and must be evaluated against its own reversal and
causal falsifiers. HELS is orthogonal: it proposes that hippocampal--entorhinal
history and replay may update a context-conditioned landscape $F_c$. Neither
proposal is a Stage-1 result; HELS currently has validated infrastructure but
no validated mechanism result.

= S2.1 NDT-Q: operational content sections

MNPS characterizes a global dynamical regime, not the identity of an experienced
or represented content. NDT-Q therefore treats content as a separate,
operational readout problem. Let a regime base be represented by
$pi_B:E -> B$, with compatible realizations $F_b = pi_B^(-1)(b)$ and a
content readout $rho_b:F_b -> C$. A content section $s_c(b)$ satisfies
$rho_b(s_c(b)) = c$.

This factorization supports a measurable episode profile
$P_t = (c_t, chi_t, S_t, R_t, V_t)$: content, closure/stability,
self-anchoring, reachability, and valence. It is an explanatory mathematical
architecture, not a claim that neural tissue literally instantiates a fibre
bundle or that current animal decoding measures qualia. Current synthetic and
population-code results are narrow operational evidence; failed centroid and
transport tests remain failures under their frozen contracts. The constitutive
reading remains philosophical and is not adjudicated by this framework.

*First empirical precursor (content-generalization decoding, not phenomenology).*
In a public mouse visual-cortex electrophysiology dataset (illusory-contour
paradigm), a frozen, genuinely blind pre-specification tested whether a
decoder trained only on physically real, orientation-matched edge trials
(never exposed to any illusory-contour trial) classifies held-out
illusory-contour-evoked population activity as its correct orientation-matched
real-edge counterpart. It does, at a session-level median rate of $0.743$
(chance $0.5$), beyond a temporal circular-shift null and a non-visual
control-region check (which is at chance), and the effect requires the
specific orientation-matched training axis rather than an arbitrary two-way
split of real-edge trials. Gross pre-event locomotor state and pupil-indexed
arousal do not account for the effect. This is an *internal validated result*
for content-generalization decoding under this specific design—an order of
analysis simpler than the content-fiber machinery above or a closure-signature
transport measurement, since no trajectory geometry or transport tensor is
computed. A companion, higher-order test of session- and
orientation-general representational convergence (a frozen crossnobis-style
centroid-distance margin) did *not* find a robust effect, and a companion
transport-tensor proxy likewise found no convergence signal; both are rejected
for their tested operationalizations, not merely inconclusive. No phenomenal
report exists in mice, so none of this speaks to content *experience*—only to
whether a specific population code generalizes across a stimulus
manipulation.

= S2.2 Candidate TRN substrates and CCTG

This section records a candidate TRN contribution and a phenomenological
simulation mapping; it does not identify TRN as the biological implementation
of NDT's variance schedule.

*Evidence ceiling.* The auditory PV/SOM TRN reanalysis archived as Zenodo
21774408 found a robust, dataset-bounded PV-linked contraction of MGB
population noise dimensionality. It did not validate a full single-unit
variance-gating mechanism, a stable SOM analogue, or identification of
$r_("true")(t)$/$sigma(t)$ with TRN firing. TRN anatomy and physiology motivate
candidate circuit mechanisms @halassa2016 @crabtree2018, but that motivation is
not evidence of the NDT mapping.

*Candidate circuit sketch.*

#math.equation(block: true,
  $
    text("Cortical state")
      ->_("L6/L5")
      text("TRN activity")
      ->_("inhibition")
      text("Thalamic relay")
      ->_("gating")
      text("Candidate state-dependent gating")
  $
)

1. *Candidate inputs:* Layer‑6 corticothalamic neurons (carrying prediction
   errors and task demands), layer‑5 projections, brainstem arousal systems,
   and hippocampal novelty signals converge on TRN sectors
   @halassaKastner2017 @hadinger2022 @takata2019. These inputs can influence
   TRN firing patterns and thalamocortical state.
2. *Candidate consequences:* TRN output may change thalamocortical gain,
   timing, or population transition geometry @lewis2015; their relation to a
   coarse NDT variance parameter is not yet identified.
3. *Observable signatures:* Thalamocortical dynamics can produce
   measurable rhythmic patterns—theta–gamma PAC, SO–spindle coupling, phase
   coherence—which we use to *estimate* a proxy $hat(r)(t)$ via the $r(t)$
   construction formula given in the main article's Rhythmic Variance Control
   section.

*Critically,* $hat(r)(t)$ constructed from observables is a proxy for a
functional schedule, not for a known TRN firing signal. Its convergent and
predictive validity can be tested without claiming TRN causality. Closed-loop
or optogenetic perturbation remains a future causal test, requiring
mean-matched controls and simultaneous schedule and geometry readouts.

*Simulation ansatz (candidate TRN → variance).* A conductance-dependent
mapping may be used in simulations:

#math.equation(block: true,
  $
    sigma(t)
      = sigma_min
        + (sigma_0 - sigma_min)
          exp(- kappa g_("TRN")(t)),
      quad kappa > 0
  $
)

This equation is not an empirical law and has no identified $kappa$ in NDT
units. It should be varied in simulations rather than reported as a
physiological calibration.

*Biological rationale and boundary.* TRN inhibitory conductance, PV cells,
channel dynamics, and electrical coupling can motivate simulations of
state-dependent thalamocortical gating @lewis2015 @halassa2016 @li2024. They
do not calibrate a coarse-grained NDT variance parameter. Any conductance range
or variance ratio used in a simulation is therefore a sensitivity setting, not
an empirical mapping or prediction.

*Interneuron and channel specifics (mechanistic substrates).* TRN neurons are
predominantly GABAergic and parvalbumin-positive (PV+); PV TRN activity
regulates spindle density and background spectral context @thankachan2019.
Sectoral heterogeneity (sensory vs. associative TRN) and CaV3.3 T-type
Ca^(2+) channels support fast spindles (Fernandez et al., 2018), while electrical
coupling synchronizes sectoral bursts at the network level @li2024. On the
cortical side, layer‑6 corticothalamic neurons (L6 CT) provide state- and
task-dependent drive to TRN, and layer‑5 projections route content
@halassaKastner2017 @hadinger2022. Together, these elements are candidate
substrates for inhibitory timing and population-state regulation. They do not
yet instantiate an identified NDT variance gate.

*CCTG successor hypothesis.* A more conservative circuit extension treats TRN
as potentially changing relative transitions in a context-dependent drift field
instead of as a universal variance executor (Eq. @eq:cctg). This CCTG framing
is speculative; it must earn support through context-reversal and causal tests
of labeled representation transitions.

#netn-box(title: [Status ceiling])[
  CCTG and the candidate TRN circuit are speculative; HELS has infrastructure
  but no mechanism result; NDT-Q is an operational content architecture, not a
  qualia measurement or an established neural fibre-bundle topology. None of
  these are required for, or should be read as strengthening, the Stage-1
  Minimal-MNDM / functional RVC / MNPS claims in the main article.
]

#bibliography("references.bib", style: "apa")
