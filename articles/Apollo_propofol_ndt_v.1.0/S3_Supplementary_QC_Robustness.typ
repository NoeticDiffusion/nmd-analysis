// S3 Supplementary QC and Robustness — Apollo propofol occupancy.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "S3 QC - Apollo propofol occupancy",
  subtitle: "Support, missingness, matching collapse, and reviewer-facing robustness summary",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S3.0 Sample and file coverage

20 participants, 80 recordings, four protocol phases each. G0 inventory and G1 join: 80/80
files matched to `datainfo.mat`. G2 H1/H2 support: 80/80 recordings met $>=30$ valid timepoints
and $>=50%$ valid. Occupancy eligible-window counts are in
`results/v1_occupancy_20260921/occupancy_subject.csv` (`n_eligible_*` columns; typically 60–105
windows per recording).

= S3.1 Identity and scaling QC

Filename identity is `sub-NNN_sedation_rest_run-RRR_acq-AAA`. Join keys are original Cambridge
filename keys (subject + acq/run), not FieldTrip `run-1..4`. Scaling of the occupancy frame uses
all baseline rows finite in all eight features, with a within-participant baseline median/MAD;
one-step eligibility is applied separately. Non-finite or $<=10^(-8)$ scales become invalid
(`NaN`); no MAD floor is clamped in. ComBat is not applied. Exported `features_robust_z` medians
are 0 in every recording — a positive control that local robust-$z$ cannot carry occupancy.

= S3.2 Matching and testability

Baseline-anchor matching: 7/20 participants with $>=20$ pairs. The $n=10$ subject gate is not
lowered. Local-chart matching included 19/20 but is not a cross-phase physical match (S2.4).
L2/L3 complete-case $n$ at first sedation is 4 (NOT_TESTABLE). LOR group contrasts: impaired
arm $n=7$ (NOT_TESTABLE). ROR occupancy contrast: not-returned $n=0$.

= S3.3 Bootstrap and sign-test QC

Occupancy bootstrap uses 10 000 participant resamples, seed 20260920. First-sedation reporting
contrast median $Delta$ CI $[0.56, 2.40]$; $d_z$ CI $[0.82, 1.69]$. These intervals and the
sign tests are descriptive/exploratory; no confirmatory primary endpoint was locked. Sign-test
zeros: none in the three occupancy contrasts. Two first-sedation decreases (sub-014, sub-028)
remain in the table and in the sign denominator.

= S3.4 Label QC

Occupancy-blind LOR labels recover 7/13, matching Chennu et al. Examples that protocol 3 is not
automatically an LOR label: sub-002 later $k=39\/40$ (responsive); sub-003 later $k=3\/40$
(impaired). Package `unresponsive` would have labelled both.

= S3.5 Reviewer-facing robustness summary

#netn-box(title: [Robustness summary])[
  The occupancy trajectory is within-subject, uses a baseline-only frame, and is consistent in
  18/20 participants at first sedation and 20/20 at later sedation. The matched-state question
  fails a pre-specified support gate rather than being rescued by lowering $n$. The exploratory
  LOR association analysis uses occupancy-blind labels that recover the published 7/13 split but
  does not establish an absence of association; the impaired arm has $n=7$. The isolated
  robustness branch retained 20/20 paired participants for all 11 tested variants and found
  first-sedation $d_z$ values from 1.049 to 1.228, with no variant-specific support failure.
  Feature shares and scale alternatives are computational diagnostics, not biological validation.
  Remaining limits are the exploratory status (G3/G4 remain open), post-hoc occupancy promotion,
  and the fact that untested preprocessing, feature sets, and cohorts may behave differently.
]

#bibliography("references.bib", style: "apa")
