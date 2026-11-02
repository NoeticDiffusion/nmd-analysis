#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "S1 Methods - BOAS registered reanalysis",
  subtitle: "Measurement contract, registered reductions, support rules, and review protocol",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S1.0 Dataset and measurement contract

The source is the read-only OpenNeuro ds005555 v1.1.1 run identified in the accompanying run manifest (DOI: 10.18112/openneuro.ds005555.v1.1.1). The registered reanalysis uses 128 recording IDs and 100 biological `pid` values. It retains the canonical subject-anchored MNPS 3D `[m,d,e]` and 9D coordinate definitions, validity fields, missingness, fallback provenance, and native family grain. The reanalysis owns the stage contrasts, reductions, null/support controls, and interpretation boundary; it does not tune producer measurements to stage differences.

= S1.1 Epoch structure and feature export

The source run contains 30-second selected windows from stage-stratified five-minute blocks. The HDF5 outputs contain no original block IDs, so touching stored rows are treated only as observed contiguous runs. The selected run contains Wake, N2, N3, and REM; N1 is absent. Auxiliary fallback features are reported as separate strata: PPG rate, EOG blink rate, and EEG high-frequency power from 30--45 Hz.

= S1.2 Primary metric definitions

The preregistered A1 endpoints are the spectral abscissa and numerical abscissa of the supplied local fitted-Jacobian outputs. For target stage $s$, the recording-level contrast is target minus Wake:

$ Delta_(s - "Wake") (q) = M_(i in s)(q_i) - M_(i in "Wake")(q_i), $ <eq:s1-contrast>

where $M$ is the median over eligible centers. Recording contrasts require at least five eligible centers in each compared stage. Person-level values are medians across eligible recordings. Reactivity gap is retained as a diagnostic derived from the primary endpoint family; it is not a separate biological claim.

= S1.3 Boundary sensitivity

The boundary-only pass keeps an eligible center only when preceding, current, and following stored epochs have the same known stage and touch the current center. Any gap, unknown stage, or non-touching neighbor fails the rule. The full and boundary passes are written to separate A1 tables and are not pooled.

= S1.4 Finite-time response and family ledger

The A2 finite-time-response family is reported at h1, h2, and h4 using its serialized recording-horizon outputs. A horizon is usable only when the nominated summary is finite, actual duration is positive, and valid sequence support is present. The A3 ledger records each family role, computation status, measurement validity, support status, qualification status, claim status, failure reason, and native grain. The diffusion parent is not testable under materially irregular increment timing. Its increment-covariance child is reported separately as a computed recording-level covariance and is not divided by time or called an Ito diffusion tensor.

= S1.5 Statistical design

This package is descriptive and exploratory. It introduces no p-values, null-hypothesis tests, inferential effect-size qualification, or multiple-comparison correction. The registered uncertainty display is a 10,000-replicate person-cluster percentile bootstrap with seed 20260923. Unsupported values remain unavailable and are never replaced with zero.

= S1.6 Provenance and review

The frozen result directory is `results/registered_reanalysis_20260923_frozen_v5`. The analysis script SHA-256 recorded in its manifest is `934d85d99b3d003c8eefa08f377c48b6fa0ab4454f91360d64853e9dac983eb7`. The independent review reconstructed A1 recording contrasts from serialized eligible centers, checked person and summary reductions, verified A2/A3 status separation, and passed with `INDEPENDENT_V5_AUDIT=PASS`. Derived tables and figures were generated downstream from the frozen snapshot.

= S1.7 Interpretation ceiling and future gate

The results do not establish local fit fidelity, effective continuous signal support, stage-intrinsic biology, causal stage effects, independent confirmation, or C1/C2/C3. The planned continuous-support pilot is separate, was not run here, and must use a new output root and its own support and qualification audit.
