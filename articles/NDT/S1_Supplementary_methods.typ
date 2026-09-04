// S1 Supplementary Methods — NDT model variants, Noetic Atlas, and simulator audits.
// Moved out of the NoeticDiffusionTheory.typ main-text Appendix to keep the main
// article focused on Tier-1 claims. See NoeticDiffusionTheory.typ for the
// canonical MNDM/RVC/MNPS formulation that these materials extend or audit.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "S1 Methods - NDT",
  subtitle: "Model variants and comparators, the Noetic Atlas readout streams, the Stage-1 NDHI composite, and truth-known simulator recoverability audits",
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
  (`NoeticDiffusionTheory.typ`, Appendix): *Model variants and comparators*,
  *Noetic Atlas: geometric and topological readouts*, and *Truth-known
  simulator audits*. None of the content here is required to evaluate the
  Stage-1 Minimal-MNDM / functional RVC / MNPS predictions; it supports later
  model comparison, exploratory geometric readouts, and estimator-validity
  discipline.
]

= S1.0 Model variants and comparators

The MNDM can be systematically simplified to test which components are
necessary:

1. *Minimal‑MNDM:* Fixed geometry, no meta‑field, and only the core $(m,d,e)$
   landscape. This is the simplest falsifiable form and should be tested first.
2. *Fixed‑geometry (FG‑MNDM):* Set $bold(G)_t equiv bold(I)$ (identity). This
   tests whether adaptive attention geometry is necessary or whether
   rhythm-only scheduling suffices.
3. *No‑meta (NM‑MNDM):* Set $Phi equiv 0$ and $delta equiv 0$. This tests
   whether meta‑regulation is necessary beyond the $(m,d,e)$ landscape.
4. *Continuous‑rhythm (CR‑MNDM):* Use a smooth $r(t)$ rather than event‑locked
   pulses. This tests whether discrete denoising steps are necessary or whether
   continuous modulation suffices.
5. *Extended‑geometry MNDM:* Allow $bold(G)_t$ and the landscape weights
   $(alpha,beta,gamma,delta)$ to vary. This form is reserved for later analyses
   or for cases where Minimal‑MNDM and structured nulls fail.

These variants support hierarchical model comparison. A variant should be
accepted only when it improves held‑out prediction, survives multiverse
robustness checks, and explains signatures that simpler rhythm or precision
models cannot reproduce.

= S1.1 Noetic Atlas: geometric and topological readouts

The Noetic Atlas applies four complementary analysis streams to
MNPS‑embedded data, each revealing different aspects of denoising dynamics:

*Stream 1: Manifold embedding and geodesic flow.* Low‑dimensional projection
(for example, PCA, PHATE, Laplacian eigenmaps) reveals intrinsic dimensionality
and trajectory structure @shine2016. We compute global dimensionality
(participation ratio, intrinsic‑dimension estimates), geodesic distances
between states, local curvature (tangent‑space PCA), and flow velocity and
directionality along principal manifold axes.

*Stream 2: Topological Data Analysis (Mapper/persistent homology).* TDA reveals
the "shape" of explored state space without assuming linearity. Mapper
constructs a graph where nodes are clusters of similar states and edges encode
transitions @saggar2018 @saggar2022 @zhang2021. We extract hub nodes (high
betweenness), component fragmentation (number of disconnected subgraphs), and
topological features (loops, voids) via persistent homology (Betti numbers)
@sizemore2019.

*Stream 3: Recurrence Quantification Analysis (RQA).* RQA characterizes how
trajectories revisit previous states. From recurrence plots we extract
recurrence rate (RR), determinism (DET), laminarity (LAM), and entropy of
line‑length distributions (structural complexity of revisits) @lopes2021.

*Stream 4: Metastability and criticality indices.* These quantify proximity to
the critical regime where denoising is maximally informative: metastability
index (variance of synchrony over time), avalanche‑like branching‑ratio
estimates, and DFA exponents capturing long‑range temporal correlations.

Each stream provides complementary information: Embedding reveals trajectory
paths, TDA reveals manifold structure, RQA reveals temporal organization, and
metastability indices quantify proximity to criticality. Together, they form a
comprehensive geometric portrait of denoising dynamics.

= S1.2 Stage-1 composite summary (NDHI)

The Noetic Diffusion Health Index (NDHI) is retained here as a *Stage‑1
composite summary* for visualization and exploratory cross-condition comparison.
It aggregates manifold dimensionality, curvature smoothness, hub/connector
structure, recurrence, and metastability with equal weights in the first report
and mandatory sensitivity analysis. The index is not used as a clinical
biomarker, diagnostic label, or consciousness score.

This distinction is central. NDHI summarizes one operational question only: how
close a measured trajectory appears to a metastable, flexible, near-critical
regime under a specified measurement contract. Its value depends on the chosen
MNPS chart, feature preprocessing, normalization, and weighting assumptions.
Therefore every NDHI report must be accompanied by its component scores,
confidence intervals or resampling uncertainty, and weight-perturbation
sensitivity. Learned-weight variants may be reported for predictive benchmarking
but are exploratory and not part of the primary construct definition.

The name "health" is used in this manuscript in the narrow dynamical sense above
and should not be read as a normative, medical, or person-level evaluation. If
future validation does not show reliability, cross-dataset stability, and
outcome relevance beyond simpler features, NDHI should be treated as a plotting
convenience rather than a validated endpoint.

= S1.3 Truth-known simulator audits: recoverability and reachability

*Source model.* The programme forks from Slow Branch, a simulator-first model
of replay-dependent slow branch-level accessibility ($M_b$) for memory linking
@langell2026_slowbranch. In a canonical two-trace motif, replay-dependent slow
writing reproduces a joint profile of overlap-branch strengthening, linking
gain, perturbation-sensitive loss, and targeted rescue that is not reproduced
by nine tested simpler or alternative comparator classes, and this profile
generalizes across tested branch counts and motif classes. This is a
model-*discrimination* result inside the simulator; it does not establish a
unique molecular or cytoskeletal memory code, and $M_b$ must never be renamed
to an empirical MNPS or NDT coordinate.

The Slow Branch follow-on simulator programme supplies a methodological,
rather than biological, extension to NDT. In truth-known synthetic systems it
asks which latent distinctions survive a specified observation map and estimator.
The four recoverability levels separate association, mechanism discrimination,
latent-order preservation, and response-operator identification. This is useful
discipline for empirical MNJ work: an observed chart need not identify the
transition operator that generated it.

For local linearized synthetic dynamics, the epoch operator and propagated
uncertainty are

#math.equation(block: true,
  $
    A_("epoch") = J_(H-1) dots J_0,
    quad
    Sigma_(h+1) = A_h Sigma_h A_h^T + Q.
  $
) <eq:simulator-recoverability>

The corrected simulator ladder recovered aggregate reachability calibration
under its frozen contract, but its directional desired-versus-false-axis Gate R
failed. Closure-signature recovery also depended on a saturation-avoiding
regime. A separate audit found that a lag-embedded observer's local
response-generating operator was structurally null on the tested reachable
channel (Gate J-O / E037R), while a deliberately lag-1-sensitive positive
control confirmed the pipeline can detect a nonzero response block when one is
present—an important negative result that bounds how far any chart-based
estimate of a local transition operator can be trusted without a comparable
positive-control check. These are internal validated and rejected results,
respectively, for a synthetic model; they do *not* validate empirical MNJ
estimates, MNPS reachability cones, or a micro-to-macro neural mechanism. Full
contracts and gate ledgers are retained in the companion handover material
@langell2026_observability_simulator.

#netn-box(title: [Status ceiling])[
  Model-variant comparisons, Atlas readouts, NDHI, and simulator audits are all
  *methodological and exploratory* relative to the Stage-1 claim set. None of
  them substitutes for the event-locked entropy, sleep-curriculum topology, or
  bounded clinical-geometry tests defined in the main article.
]

#bibliography("references.bib", style: "apa")
