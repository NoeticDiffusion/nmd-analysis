#import "network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "Trajectory Psychosis QC",
  subtitle: "Data coverage, known artefact risks, and outstanding validation steps",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Scope

This supplement documents:

1. data coverage and subject-level QC in the trajectory pipeline,
2. artefact risks specific to trajectory metrics computed from resting EEG,
3. the outstanding temporal shuffled-null validation,
4. codebook sensitivity,
5. and the relationship between the trajectory results and the companion static-geometry QC.

= Data coverage

All 82 subjects from `ds003944` and all 61 subjects from `ds003947` passed the minimum-window filter (16 valid windows). No subjects were excluded from metric computation. The codebook was fitted on all available subjects per dataset.

#figure(
  kind: table,
  table(
    columns: (1.0fr, 0.9fr, 0.9fr, 0.9fr, 0.9fr, 1.3fr),
    align: left,
    inset: 5pt,
    table.header(
      [*Dataset*],
      [*Total subjects*],
      [*Subjects in codebook fit*],
      [*Min windows*],
      [*Median windows*],
      [*Max windows*],
    ),
    [ds003944], [82], [82], [75], [75], [75],
    [ds003947], [61], [61], [75], [75], [75],
  ),
  caption: [Subject coverage in the trajectory pipeline. All subjects had exactly 75 analysis windows, confirming consistent recording length.]
) <tab-s3-coverage>

= Trajectory metric artefact risks

Trajectory metrics derived from short EEG recordings are more noise-sensitive than static coordinate summaries. The following artefact categories are specifically relevant here.

== Temporal autocorrelation artefacts

The noetic action jerk term ($||Delta^2 bold(z)_t||^2 / Delta t^4$) is sensitive to any temporal autocorrelation in the coordinate sequence. If the EEG pre-processing introduces temporal smoothing or if successive windows are highly correlated, the second finite difference $Delta^2 bold(z)_t$ will be artificially small, suppressing jerk estimates across all groups equally and reducing statistical power.

Conversely, if coordinate estimates have window-to-window noise that is independent across windows (i.e., random rather than temporally structured), $Delta^2 bold(z)_t$ will be inflated by noise, and jerk estimates will overestimate true dynamic variation. Group differences in jerk would then reflect differences in coordinate estimation noise rather than genuine dynamic differences.

_Recommended validation_: time-shuffled null (see below).

== Codebook resolution artefacts

With $N_S = 12$ states (3D) and $N_S = 24$ states (9D) and $T = 74$ transitions per subject, the expected number of transitions per state pair is low. Many off-diagonal entries of $P_{ij}$ will be zero, which inflates transition sparsity and may cause entropy rate to reflect codebook sparsity rather than genuine trajectory randomness.

The codebook size was chosen to match the coma trajectory pipeline @langell2026_trajectory and to provide at least 3 expected transitions per occupied state on average. For a 3D codebook with 12 states and 74 transitions, approximately 6 states will have at least 5 outgoing transitions on average. This is sufficient for entropy rate estimation but not for fine-grained transition probability estimation.

_Sensitivity check_: running with $N_S = 6$ (3D) and $N_S = 12$ (9D) as an alternative is recommended before manuscript submission.

== Potential function artefacts

The `noetic_action_potential` result ($d = +0.728$, $p = 0.012$ for FEP unmedicated vs healthy in `ds003944`) is partially collinear with the static `m`, `d`, `e` coordinate means. The potential $Phi = e - m + d$ is defined on the subject-anchored coordinates, but residual between-subject differences in subject-anchored mean coordinates can still contribute to potential-density estimates.

_Recommended validation_: residualise `noetic_action_potential` against each subject's mean $m$, $d$, $e$ coordinates and re-run contrasts on residuals. If the potential result disappears after residualisation, it is likely a restatement of the companion paper's static positional effect rather than a genuine trajectory-grammar result.

== Power-limited detection of jerk

The $n = 19$ unmedicated FEP subjects in `ds003944` and $n = 8$ in `ds003947` provide limited power for the jerk component specifically, because jerk is the noisiest metric: it uses a fourth-power temporal normalisation and is sensitive to window-spacing irregularities. The directional pattern (medicated lower jerk than unmedicated) is consistent across both datasets but does not survive correction in either.

= Outstanding: temporal shuffled-null test

The most important outstanding validation is a within-subject window-order permutation test. For each subject, randomly permute the temporal order of windows before computing trajectory metrics. Repeat $B$ times (e.g., $B = 100$) and record the distribution of shuffled metric values. The temporal specificity score for subject $i$ is

$
Z_i = frac(M_i - mu_i^"shuffle", sigma_i^"shuffle" + epsilon),
$

where $M_i$ is the observed metric and $mu_i^"shuffle"$, $sigma_i^"shuffle"$ are the mean and SD of the shuffled distribution.

A group comparison on $Z_i$ values tests whether the group difference depends on real temporal ordering rather than on the marginal distribution of coordinates. If the group differences in entropy rate, irreversibility, or noetic action disappear after shuffling, the metrics are insensitive to time ordering and should not be interpreted as dynamic measures.

This test has not been run for the present analysis and represents a mandatory validation step before the main results can be treated as established trajectory-geometry findings.

= Codebook sensitivity

The trajectory metrics have not been tested for sensitivity to codebook size. The default sizes ($N_S = 12$ for 3D, $N_S = 24$ for 9D) are inherited from the coma trajectory pipeline and have not been tuned for EEG resting-state data with 75 windows per subject. A minimal sensitivity check should run at half and double these sizes:

#figure(
  kind: table,
  table(
    columns: (0.7fr, 0.9fr, 0.9fr, 1.5fr),
    align: left,
    inset: 5pt,
    table.header(
      [*Dim*],
      [*Default $N_S$*],
      [*Sensitivity range*],
      [*Status*],
    ),
    [3D], [12], [6, 12, 24], [not yet run],
    [9D], [24], [12, 24, 48], [not yet run],
  ),
  caption: [Codebook size sensitivity check. The default sizes have not been validated for EEG resting-state data; this check is recommended before manuscript submission.]
) <tab-s3-codebook>

= Relationship to companion static-geometry QC

The companion static-geometry paper's QC (leave-one-subject-out, cross-fitted fold scores, between-site robustness) applies to the cohort-anchored MNPS and Jacobian metrics, not to the subject-anchored trajectory metrics used here. The present study inherits the same upstream H5 files and coordinate exports as the companion, but the downstream trajectory computation is fully article-local and has not been subject to the same QC framework.

Key pending QC items specific to this study:

1. Temporal shuffled null (above).
2. Codebook sensitivity sweep (above).
3. Residualisation of `noetic_action_potential` against static coordinate means.
4. Leave-one-subject-out stability check on `noetic_action` in `ds003944` (does the result depend on any single subject?).

= Conclusion

The trajectory metric pipeline runs cleanly and produces plausible results. However, the specific results reported in the main manuscript have not been validated against temporal shuffled nulls and have not been tested for codebook sensitivity. These validations are necessary before the results can be treated as established. The present draft should be read as an exploratory pilot that motivates further validation work.

#bibliography("psychosis.bib", style: "apa")
