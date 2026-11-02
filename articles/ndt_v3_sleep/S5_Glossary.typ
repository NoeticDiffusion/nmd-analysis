#import "template_eLife.typ": *
#show: netn-template.with(
  title: "S5 Glossary",
  short-title: "S5 Glossary - Sleep state geometry",
  subtitle: "Terms used in the measurement contract",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Terms

*MNPS* — Meta-Noetic Phase Space coordinates used by the analysis pipeline. Coordinate meaning is contract-specific and does not by itself establish a biological mechanism.

*Measurement family* — A versioned output surface with a schema, status, validity, grain, and provenance.

*Q/W_Q* — A recording-level one-step transition residual covariance proxy and its propagated reachability matrix. It is not a stage-native noise estimate.

*Support* — The time interval and source samples required to compute a measurement.

*Inferential grain* — The native repeated-measure and biological-unit metadata attached to a measurement.

*Method-limited* — A status indicating that numerical or estimator behavior prevents the endpoint from supporting the intended interpretation.

*Candidate not qualified* — An implemented diagnostic estimator whose scientific recovery and bias program is incomplete.

*Unavailable* — A deliberate status for missing, invalid, or contract-inadmissible data; it is not a zero.

#bibliography("references.bib", style: "apa")
