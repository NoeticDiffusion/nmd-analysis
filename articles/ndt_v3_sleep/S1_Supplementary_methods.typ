#import "template_eLife.typ": *
#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "S1 Methods - Sleep state geometry",
  subtitle: "Measurement contract, temporal support, and analysis governance",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S1.1 Source and support

The verified ds005555 sub-99 recording is read-only. Source, code, config, runtime, and output hashes are retained with each run. A stage-conditioned measurement requires containment of its full support within an explicit stage interval. The present development experiment instead describes global coordinates by aligned recorded window label, with full filter support and neighborhood purity explicitly not assessed. Gaps, irregular timebase, absent labels, and unknown alignment remain visible.

The annotation audit compares the export with the original human-scored
`stage_hum` event source. It checks row-to-epoch mapping, onset and 30-second duration,
the pinned 256-Hz sample clock, and the recording end. Code 8 remains an
unknown PSG-disconnection status and is not bridged or relabelled; `stage_ai`
is not substituted. The recording duration is 32,064 seconds and the epoch
table ends at 32,040 seconds, leaving a 24-second unrepresented tail. This is
an annotation/table support check, not a full estimator-purity certificate.

= S1.2 Measurement families

MNPS coordinates and diffusion summaries are read from their canonical versioned families. Q/W_Q is a recording-level one-step transition residual covariance proxy. Destination and resilience families may be unavailable. DF-DRIFT-C1 is a candidate analysis estimator and is not a qualified empirical endpoint. The 9D `v_norm` measure remains method-limited.

= S1.3 Repeated measurements

Windows and transitions are repeated observations. They are summarized within participant and recording before any cohort inference. No row count is interpreted as a participant count.

= S1.4 Statistical governance

The first stage is descriptive support and missingness auditing. Participant inclusion, aggregation, contrast, effect size, and correction family for any later cohort analysis are frozen after the audit and before outcome inspection. No refusal is converted to zero and no diagnostic horizon is selected post hoc.

= S1.5 Robustness

The audit retains computation status, measurement validity, coordinate contract, grain, support, finite-value checks, and failure reasons. Numerical sensitivity results qualify method behavior only; they do not establish EEG-preprocessing robustness or biological generalization.

= S1.6 Fixed label-boundary experiment

For each representation, row eligibility requires a known label, a finite complete coordinate vector, true producer coverage and retained-after-QC masks, and its corresponding 3D geometry or 9D coordinate mask. The sensitivity subset also requires the immediately preceding and following labels to match, consecutive epoch IDs, and touching window bounds. It excludes recording endpoints. This local label condition does not certify filter support. Every stage and coordinate is retained in counts and median/25th/75th percentile tables; empty cells remain unavailable.

The policy was specified after the source support audit and before the new descriptive summaries. No population p-values, classifier, clinical prediction or stage-conditioned diffusion estimator is evaluated. The source PPG fallback for `e_m` has `semantic_equivalence=false`, and complete anchor provenance remains unverified.

#bibliography("references.bib", style: "apa")
