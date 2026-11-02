#import "template_eLife.typ": *
#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "S3 QC - Sleep state geometry",
  subtitle: "Temporal support, missingness, and numerical sensitivity",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S3.1 Temporal support

The QC records window endpoints, aligned stage labels, gaps, irregular dt, and unavailable joins. Full measurement-support containment is not assessed in this pilot. Timestep validity thresholds are not relaxed to obtain computed measurements. Matching labels in three consecutive windows are a boundary diagnostic and cannot close this support gate.

= S3.2 Measurement validity

Each family retains computation status, measurement validity, claim status, inferential grain, coordinate contract, and failure reason. Computed status is not treated as biological validity.

= S3.3 Numerical sensitivity

The bounded W_Q sensitivity diagnostic uses fixed horizons, fixed starts, fixed seeds, fixed production PSD floor, and separate Phi-only/Q-only perturbations. It is a model-input numerical diagnostic, not an EEG-preprocessing or biological robustness test. The 9D volume endpoint remains method-limited.

= S3.4 Audit policy

Unavailable and invalid measurements remain visible. No post hoc favorable horizon, seed, endpoint, or stage subset is selected.

= S3.5 Verified development results

All four source masks are true and all coordinate vectors are finite in the 1,068 exported windows. Nine unknown labels are excluded from coordinate summaries while retained in the audit. The fixed two-sided boundary policy retains 935 of the 1,059 eligible windows; it removes all 15 N3 windows and leaves only two N1 windows. This is a limitation of the selected descriptive support rule, not evidence of absent N3 physiology or a full-support certificate.

The annotation/run-support audit finds 84 contiguous bouts, comprising 83
known-stage bouts and one unresolved code-8 PSG-disconnection bout. All 15 N3
bouts are single 30-second windows. The original human `stage_hum` source
matches the row-to-epoch mapping, durations, and 256-Hz sample clock; the raw
recording ends 24 seconds after the final accepted epoch bound. These facts
explain the boundary-rule result while leaving full filter and
diffusion-neighborhood purity `not_assessed`.

The earlier r10 descriptive acceptance suite passed 42 tests. Synthetic acceptance cases cover exact boundary counts, label changes, unknown labels, gaps, overlaps, nonconsecutive IDs, missing coordinate values, unknown masks, empty stage groups and mandatory pinned configuration. Plot checks require each eligible point once and prohibit connected lines across gaps. A real integrated export reproduced the accepted Parquet table byte for byte. Independent review and all registered artifact hashes passed for run r10.



= S3.6 Increment support audit, 2026-09-08

The separate fixed audit retains all 1,067 adjacent pairs and all 21,360 candidate
selections. Matching known-stage endpoints occur in 976 adjacent pairs: Wake
258, N1 4, N2 609, N3 0, REM 105. Ten adjacent pairs touch code 8. Structural
admissibility does not establish full signal support: qualified counts remain
unavailable. The executed filter provenance is incomplete, while robust-z
reference fitting uses all 1,068 rows. No tensor or canonical mask was changed.

#bibliography("references.bib", style: "apa")
