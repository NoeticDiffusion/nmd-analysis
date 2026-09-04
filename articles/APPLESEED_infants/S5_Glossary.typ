#import "template_eLife.typ": *
#show: netn-template.with(
  title: "S5 Glossary",
  short-title: "APPLESEED glossary",
  subtitle: "Operational terms used in this reanalysis",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

#set heading(numbering: none)
= Terms
*Meta-Noetic Pattern Space (MNPS).* The exported feature chart used as input to downstream summaries. It is an operational representation of processed EEG, not a demonstrated latent neural state.

*MNJ.* Meta-Noetic Jacobian: the local derivative of the fitted chart flow. This analysis summarizes its trace, overall magnitude, antisymmetric rotation magnitude, and spectral radius per session.

*Reachability.* A local, model-based short-horizon description of variation reachable from a chart location. It is summarized here by covariance log-determinant, effective dimension, condition number, directional entropy, and a rotation proxy.

*Subject anchoring.* Coordinate normalization relative to a subject-level reference. It supports repeated-measure summaries but does not warrant interpreting absolute coordinate levels across children as a common scale.

*ICC(A,1).* Two-way absolute-agreement, single-measure intraclass correlation. It quantifies agreement while retaining a penalty for systematic session differences; it is not equivalent to Pearson correlation.

*SEM and MDC95.* Standard error of measurement and minimum detectable change at 95%. Both translate reliability estimates into the original endpoint scale.

*Pseudo-replication.* Artificially increasing apparent sample size by treating dependent epochs, windows, or repeated sessions as independent. The primary tests use one summary per child-session and one paired value per child.

*BH-FDR.* Benjamini--Hochberg false-discovery-rate adjustment applied to a stated endpoint family.

*Exploratory analysis.* A result-generating analysis whose raw p-values and effect sizes are used for hypothesis generation rather than confirmation. The balanced age contrasts, coordinate-position contrasts, 9D sensitivity analyses, and event-locked analyses are exploratory; the nine-endpoint dynamical family is reported with named BH-FDR sensitivities.
