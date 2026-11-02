#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S4 Supplementary Clinical Summary",
  short-title: "S4 Clinical Summary - BOAS reanalysis",
  subtitle: "Why this measurement audit is not a clinical result",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope and intent

#netn-box(title: [Important: no clinical or biological claim])[ 
  This analysis is an exploratory, stage-sampled reanalysis of computed research measurements. It tested no intervention, produced no diagnostic classifier, and supports no individual-level prediction. The interpretation ceiling is METHOD-LIMITED.
]

= What was studied

The source run contains 128 recording IDs from 100 biological participants, with sampled Wake, N2, N3, and REM windows. It contains explicit gaps and unequal fallback strata. The analysis reports descriptive contrasts in the supplied spectral and numerical abscissa outputs and records the availability of finite-time-response and newer family outputs.

= What the numbers mean

The primary A1 values are summaries of supplied local fitted-Jacobian outputs in reported measurement units. A target-minus-Wake value describes a difference between recorded stage strata under the registered reduction. It does not by itself identify a clinical state, mechanism, causal effect, or subjective experience.

= What was found

The frozen v5 package supports reproducible descriptive tables and figures, with explicit person/recording support and boundary sensitivity. Finite-time response is usable for all 3D recordings at h1/h2/h4 and for 126 of 128 9D recordings. The diffusion parent is not testable under irregular timing; a separate increment covariance child is computed but is not a qualified diffusion tensor.

= What was not established

The analysis does not establish a biomarker, diagnosis, prognosis, treatment response, causal sleep-stage effect, continuous full-night dynamics, independent confirmation, or a direct C1/C2/C3 test. Sleep-stage labels are observational context labels, not interventions and not reports of experience.

= What would increase confidence

Confidence would require a separately registered continuous-support or exact-time analysis, validated signal-support and fit-fidelity checks, independent data, predeclared qualification criteria, appropriate null controls, and eventual clinical validation in relevant patient cohorts. Those steps are outside this frozen reanalysis.

= Summary for clinical readers

Read this package as a transparent measurement audit. It shows what the supplied run can describe and where it cannot support a stronger claim. It should not be used for patient assessment or clinical decision-making.
