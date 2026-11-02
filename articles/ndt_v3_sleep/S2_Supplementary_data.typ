#import "template_eLife.typ": *
#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "S2 Data - Sleep state geometry",
  subtitle: "Frozen table specifications and artifact provenance",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S2.1 Support manifest

The accepted descriptive artifact is `results/descriptive_epoch_sub99_20260907_r10`. Its analysis manifest and SHA256 sidecar pin the run, with input epoch manifest, table, source-code, configuration and output hashes. The linked epoch manifest retains the original HDF5 source hash. A separate coordinator script recomputed all 120 summary rows without importing the descriptive runner.

= S2.2 Participant and recording coverage

One recording contributes 1,068 windows, of which nine have unknown labels. Primary counts are Wake 275, N1 20, N2 642, N3 15, REM 107. Under the two-sided same-label boundary rule the counts are 249, 2, 581, 0 and 103 respectively, in both representations. Window and transition rows are not independent participants.

The separate run-support audit records 84 contiguous label/status bouts: 83
known-stage bouts and one code-8 unknown/disconnection bout. Known-stage bout
counts and window totals are Wake 17/275, N1 16/20, N2 33/642, N3 15/15,
and REM 2/107. The window-length vectors are Wake
`[213,4,1,1,3,1,17,3,4,10,11,2,1,1,1,1,1]`, N1
`[4,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1]`, N2
`[19,30,1,1,3,6,14,10,4,1,1,1,2,5,7,13,12,34,16,54,17,87,22,4,19,32,39,38,64,32,5,8,41]`,
N3 `[1]` repeated 15 times, and REM `[61,46]`. These run lengths describe
recorded annotation support in one recording; they do not establish stage
purity for any estimator.

= S2.3 Primary measurement tables

The primary and boundary coordinate-summary CSV files each retain every known stage for all 3D and 9D coordinates. The N3 boundary rows explicitly contain n = 0 and unavailable medians/quartiles. Primary and boundary 3D tables each contain 15 rows; their 9D counterparts each contain 45 rows. These summarize global coordinates by recorded labels, not stage-conditioned geometries. Per-window eligibility, producer-mask states and neighbor support remain in separate audit tables. The PPG fallback for e_m is not semantically equivalent to the intended feature.

= S2.4 Dynamical diagnostics

Q/W_Q, FTR, Jacobian, destination, resilience, and DF-DRIFT-C1 tables will retain their recording or candidate status. The 9D `v_norm` endpoint will be labeled method-limited where applicable.

#bibliography("references.bib", style: "apa")
