#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S5 Glossary",
  short-title: "S5 Glossary - BOAS reanalysis",
  subtitle: "Terms used in the registered descriptive measurement audit",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplementary Material",
)

= Computed versus qualified

*Computed* means that a value was serialized by the measurement or analysis pipeline under its declared schema and support fields. *Qualified* would require a separate scientific gate establishing that the object supports the nominated interpretation. A computed value in this article is not automatically a qualified biological estimand.

= Fallback feature

An auxiliary feature used when the canonical source channel or coordinate component is unavailable. PPG rate, EOG blink rate, and EEG high-frequency power are retained as separate strata and are not treated as semantically equivalent.

= Finite-time response

A model-derived response summary at a registered horizon, here h1, h2, or h4. The article reports its serialized usability and native grain; it does not promote it to a qualified future law.

= Gap

An omitted interval between selected stored windows. Gaps are preserved as missing temporal support. Touching stored rows are observed contiguous runs, not proof that an unrecorded continuous interval has been recovered.

= MNPS 3D and 9D

The canonical subject-anchored coordinate representations used by the source run. The 3D representation uses `[m,d,e]`; the 9D representation expands the coordinate channels. The analysis keeps dimensions separate.

= Numerical abscissa

The supplied local-Jacobian endpoint associated with instantaneous numerical growth or reactivity under the producer's declared semantics. In this article it is a descriptive measurement output, not a biological stability label.

= Person-cluster bootstrap

A resampling display that resamples person-level recording summaries as clusters before taking the median. The registered display uses 10,000 replicates and seed 20260923. It is not described as a confirmatory confidence interval.

= Spectral abscissa

The supplied local-Jacobian endpoint associated with the largest real part of the local spectrum under the producer's declared semantics. In this article it is reported descriptively and remains subject to fit, support, and fallback limitations.

= Support status

The declared availability of the observations or sequences needed for a measurement. `sufficient`, `not_recorded`, `insufficient_local_support`, `not_applicable`, and related values remain explicit in the tables.

= METHOD-LIMITED

The coordinator verdict used when arithmetic and provenance can be checked but the available data or measurement qualification do not support biological interpretation. This is the final scientific ceiling for the present package.
