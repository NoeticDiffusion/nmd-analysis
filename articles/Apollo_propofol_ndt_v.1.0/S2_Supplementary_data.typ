// S2 Supplementary Data — Apollo propofol occupancy secondary analysis.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "S2 Data - Apollo propofol occupancy",
  subtitle: "Occupancy tables, LOR join, match support, and discovery local-chart screens",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S2.0 Occupancy by participant and phase

Full subject table: `results/v1_occupancy_20260921/occupancy_subject.csv`. Cohort medians:
baseline 2.71, first sedation 4.07, later sedation 8.68, recovery 3.95. Contrasts versus
baseline are reported as Table 1 in the main manuscript (source: `occupancy_contrasts.csv`).

= S2.1 Occupancy versus behavioural hit count

#figure(
  image("figures/occupancy/fig2_occupancy_paired_deltas.png", width: 85%),
  caption: [Subject-level baseline-referenced radial-displacement change at first protocol
  sedation versus baseline. Blue: increase; red: decrease. Source:
  `results/v1_occupancy_20260921/occupancy_subject.csv`.],
) <figS-deltas>

The occupancy-versus-hits scatter has moved to the main text because it is the most direct
display of the exploratory behavioural question.

#figure(
  image("figures/occupancy/figS_occupancy_vs_hits.png", width: 85%),
  caption: [Occupancy versus correct responses / 40 at later protocol sedation. Colour is the
  occupancy-blind Chennu LOR split. Spearman $rho=-0.08$, $p=0.73$, $n=20$. Source:
  `results/v1_lor_20260921/lor_occupancy_joined.csv`.],
) <figS-hits>

The Spearman estimate is an exploratory descriptive association, not a test of equivalence or
independence. The point estimate supplies no evidence of a monotonic occupancy/hit-count
association in this $n=20$ sample, but does not establish that an association is absent; the
LOR-group contrast remains NOT_TESTABLE because the impaired arm has $n=7$.

#figure(
  image("figures/occupancy/figS_lor_trajectory.png", width: 85%),
  caption: [Occupancy trajectory split by occupancy-blind LOR status. Red: LOR-impaired ($n=7$);
  blue: responsive ($n=13$). Medians are within group. This is a descriptive exhibit, not a
  testable group contrast. Source: `results/v1_lor_20260921/lor_occupancy_joined.csv`.],
) <figS-lor-traj>

Hit counts, LOR/ROR status, and concentration: `results/v1_lor_20260921/lor_behaviour_labels.csv`.
Group contrasts: `lor_contrasts.csv`. Occupancy-blind split is 7/13, matching Chennu et al.
All seven impaired participants returned at recovery.

= S2.2 Match support for the baseline-anchor C3 test

Copied from `results/v1_c3_anchor_20260921/` into the occupancy result directory. Included
($>=20$ pairs): sub-002, sub-013, sub-014, sub-022, sub-023, sub-028, sub-029 (7/20). Zero
pairs: sub-005, sub-006. Main-text Figure 3 displays this collapse.

On the seven included participants, matched speed $d_z=0.10$ (Holm $p=1$) and matched spread
$d_z=-0.14$ (Holm $p=1$). Matched occupancy QC: 2.11 versus 2.16, $d_z=0.25$. Unmatched
increment speed $d_z=+0.31$ and spread $d_z=-0.27$ ($n=20$) do not reproduce local-chart
unmatched spread contraction.

= S2.3 Local-chart discovery screen (descriptive)

Exported recording-local dynamical scalars, first protocol sedation minus baseline, $n=20$
unless noted. Holm applies only to original H1/H2 sign tests. BH-FDR is across the frozen
Wilcoxon family. No BH $q<0.05$. Largest paired $|d_z|$ in this screen: `diffusion_total`
$d_z=-0.70$ (sign $p=0.012$, Holm $p=0.024$, BH $q=0.28$). `diffusion_effective_dimension`
$d_z=+0.11$. `R_b_over_a` and `A_bD` are empty (0/80). Jacobian spectral abscissa
$d_z=-0.31$. Source: `results/v1_stage_20260921/`.

A broader L1/L2/L3 complete-case panel (`results/v1_level_20260921/`) likewise has no BH
$q<0.05$ among tests with $n>=10$. Largest L1 $|d_z|$: `chart_drift_b_hat_norm` $-0.86$
(Wilcoxon $p=0.0023$, BH $q=0.24$). L2/L3 complete-case $n$ at first sedation is 4, below the
$n=10$ gate (NOT_TESTABLE). Chart-Jacobian $alpha$ is Family B, not one-step L3.

= S2.4 Occupancy robustness branch

The isolated post-hoc robustness branch is in
`results/v1_occupancy_robustness_20260922_reviewfix/`. It keeps the original full-eight-feature robust-$z$
eligibility mask and participant-level pairing. It reports full-MAD occupancy, eight
leave-one-feature-out radii, and baseline-only sample-SD and normalised-IQR scale alternatives;
the frozen primary outputs are unchanged. All 11 variants retained $n=20$ paired participants at
first sedation. Across variants, the first-sedation median paired difference ranged from $1.295$
to $1.757$ and $d_z$ from $1.049$ to $1.228$; the scale alternatives gave $d_z=1.166$ and
$1.171$. Feature contributions are descriptive squared-radius shares; beta/alpha ratio and gamma
had the largest average shares (18.1% and 16.6%). The lock manifest records exact input, source,
plan, and output hashes. This is computational robustness evidence only, not a G3/G4 or biological
confirmation.

= S2.4a Local-chart matched-state screen (not transported)

= S2.5 PR-01 geometric and caliper diagnostics

The separate post-hoc PR-01 branch (`results/v1_pr01_geometric_20260922_final2/`) retained the
frozen eight-feature baseline robust-$z$ frame and eligibility mask. At first sedation,
phase-cloud centre displacement increased by median 2.60 ($d_z=1.83$) and within-phase
dispersion by 0.477 ($d_z=0.585$); the 10% covariance-shrinkage-whitened radial displacement
gave $d_z=1.21$. These are descriptive chart-level decompositions, not a latent-state or
biological identification.

#figure(
  image("figures/pr01/fig4_caliper_sensitivity.png", width: 80%),
  caption: [Sensitivity of first-sedation baseline matching support to multiples of the frozen
  subject-specific caliper. The original 1x gate remains the primary diagnostic; wider calipers
  are not used to rescue C3. Source: `results/v1_pr01_geometric_20260922_final2/caliper_sensitivity.csv`.],
) <figS-caliper>

Matching in exported recording-local MNPS coordinates included 19/20 participants. Matched
speed $d_z=-0.16$ (Holm $p=0.36$) and matched spread $d_z=-0.33$ (Holm $p=0.13$). Unmatched
spread $d_z=-0.69$ (sign $p=0.012$). This chart is re-centred per recording; it is not a
baseline-fixed physical frame. Source: `results/v1_c3_20260921/`.

= S2.6 Coverage inventory

80/80 files readable. L0/L1 identities finite on 80/80 except `A_bD` and `R_b_over_a` (0/80).
Lag-1 one-step L2/L3 finite on 46/80. L4 iterated horizon map 0/80. Destination and resilience
`not_testable`. Source: `results/v1_coverage_20260921/`.

#bibliography("references.bib", style: "apa")
