#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "APPLESEED results",
  subtitle: "Frozen primary reliability and longitudinal estimates",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S2.1 Primary test--retest results
In the cohort-anchored 13-child session 1--2 comparison, reachability condition number had ICC(A,1)=0.946 (bootstrap 95% CI -0.132 to 0.990), reachability log-determinant had 0.779 (0.216 to 0.942), and directional entropy had 0.535 (-0.160 to 0.826). MNJ scalar estimates were low or negative. The FDR column below adjusts the nine paired Wilcoxon session-difference p-values; it does not test ICC. No paired session difference survived this sensitivity analysis (all adjusted p >= 0.945). These small-sample intervals remain broad and should not be treated as precise reliability classification.

#figure(
  kind: table,
  clean-table(
    columns: (2.2fr, 0.7fr, 1.3fr, 0.7fr, 0.7fr, 0.8fr, 0.8fr, 0.7fr, 0.7fr),
    align: (left, center, center, center, center, center, center, center, center),
    table.header([*Endpoint*], [*ICC*], [*95% CI*], [*$r$*], [*SEM*], [*MDC95*], [*Mean Δ*], [*Raw p*], [*FDR p*]),
    [`frobenius_norm`], [0.064], [-0.360, 0.421], [0.062], [0.018], [0.050], [0.0032], [0.542], [0.945],
    [`rotation_norm`], [0.119], [-0.380, 0.449], [0.115], [0.013], [0.036], [0.0031], [0.685], [0.945],
    [`trace`], [-0.074], [-0.515, 0.212], [-0.068], [0.013], [0.035], [0.0002], [0.946], [0.946],
    [`spectral_radius`], [-0.290], [-0.762, 0.199], [-0.270], [0.008], [0.024], [0.0017], [0.735], [0.945],
    [`tube_log_det`], [0.779], [0.216, 0.942], [0.769], [0.253], [0.701], [-0.0502], [0.414], [0.945],
    [`tube_d_eff`], [0.442], [-0.158, 0.771], [0.471], [0.150], [0.416], [0.0614], [0.216], [0.945],
    [`tube_kappa`], [0.946], [-0.132, 0.990], [0.941], [1.644], [4.558], [0.0569], [0.735], [0.945],
    [`tube_dir_entropy`], [0.535], [-0.160, 0.826], [0.562], [0.062], [0.172], [0.0247], [0.340], [0.945],
    [`tube_rotation`], [0.217], [-0.545, 0.627], [0.204], [0.084], [0.233], [-0.0056], [0.946], [0.946],
  ),
  caption: [Primary absolute-agreement reliability results. Each line uses 13 paired children. Mean Δ is session 2 minus session 1; SEM and MDC95 retain endpoint units. FDR is BH adjustment within the nine paired session-difference tests.]
)

= S2.2 Cohort-anchored 4-to-8-month dynamical contrasts
Eleven complete children contributed the primary cohort-anchored four-month mean to eight-month panel. No primary endpoint survived the nine-test BH-FDR sensitivity correction; the smallest raw p-values were 0.102 for lower reachability effective dimension and lower directional entropy. The table reports all nine endpoints, not only the post-hoc display subset.

#figure(
  kind: table,
  clean-table(
    columns: (2.1fr, 1.2fr, 0.9fr, 0.8fr, 0.8fr),
    align: (left, left, center, center, center),
    table.header([*Endpoint*], [*Contrast*], [*Mean difference*], [*$d_z$*], [*Raw p / FDR p*]),
    [`frobenius_norm`], [4-month mean to 8 months], [0.0090], [0.34], [0.240 / 0.309],
    [`rotation_norm`], [4-month mean to 8 months], [0.0061], [0.35], [0.206 / 0.309],
    [`trace`], [4-month mean to 8 months], [0.0063], [0.37], [0.413 / 0.413],
    [`spectral_radius`], [4-month mean to 8 months], [0.00493], [0.47], [0.175 / 0.309],
    [`tube_log_det`], [4-month mean to 8 months], [0.198], [0.36], [0.175 / 0.309],
    [`tube_d_eff`], [4-month mean to 8 months], [-0.096], [-0.48], [0.102 / 0.309],
    [`tube_kappa`], [4-month mean to 8 months], [0.373], [0.04], [0.147 / 0.309],
    [`tube_dir_entropy`], [4-month mean to 8 months], [-0.0425], [-0.39], [0.102 / 0.309],
    [`tube_rotation`], [4-month mean to 8 months], [0.0333], [0.37], [0.278 / 0.313],
  ),
  caption: [Complete nine-endpoint cohort-anchored 4-month mean to 8-month family. Raw p-values are exact two-sided Wilcoxon signed-rank values; FDR is BH within these nine tests. Bootstrap intervals for mean differences are in the machine-readable CSV.]
)

= S2.3 Cohort-anchored 4-to-12-month dynamical contrasts
The same 11 complete children contributed the four-month mean to twelve-month panel. None of the nine 3D dynamical endpoints had raw p below 0.365 and none survived the nine-test BH-FDR sensitivity correction.

#figure(
  kind: table,
  clean-table(
    columns: (2.1fr, 1.2fr, 0.9fr, 0.8fr, 0.8fr),
    align: (left, left, center, center, center),
    table.header([*Endpoint*], [*Contrast*], [*Mean difference*], [*$d_z$*], [*Raw p / FDR p*]),
    [`frobenius_norm`], [4-month mean to 12 months], [0.0209], [0.45], [0.638 / 0.717],
    [`rotation_norm`], [4-month mean to 12 months], [0.0143], [0.45], [0.465 / 0.717],
    [`trace`], [4-month mean to 12 months], [0.0075], [0.29], [0.465 / 0.717],
    [`spectral_radius`], [4-month mean to 12 months], [0.0057], [0.37], [0.638 / 0.717],
    [`tube_log_det`], [4-month mean to 12 months], [0.0284], [0.04], [0.831 / 0.831],
    [`tube_d_eff`], [4-month mean to 12 months], [-0.0720], [-0.35], [0.577 / 0.717],
    [`tube_kappa`], [4-month mean to 12 months], [2.468], [0.37], [0.520 / 0.717],
    [`tube_dir_entropy`], [4-month mean to 12 months], [-0.0365], [-0.34], [0.365 / 0.717],
    [`tube_rotation`], [4-month mean to 12 months], [0.0233], [0.20], [0.520 / 0.717],
  ),
  caption: [Complete nine-endpoint cohort-anchored 4-month mean to 12-month family. FDR is BH within these nine tests.]
)

= S2.4 Coordinate-position and comparator reliability
Coordinate positions were not used as a substitute for dynamical validation. Their session 1--2 ICC(A,1) estimates were 0.575 for mobility (bootstrap 95% CI 0.038 to 0.895), 0.458 for deviation (0.072 to 0.706), and 0.700 for entropy-related coordinate (0.019 to 0.894); these intervals provide context for the 12-month mobility contrast. In that separate three-coordinate family, mobility decreased in all 11 children (raw p=0.00098; BH p=0.0029).

#figure(
  kind: table,
  clean-table(
    columns: (2fr, 0.8fr, 1.4fr, 0.8fr),
    align: (left, center, center, center),
    table.header([*Coordinate*], [*ICC*], [*Bootstrap 95% CI*], [*$r$*]),
    [Mobility], [0.575], [0.038, 0.895], [0.629],
    [Deviation], [0.458], [0.072, 0.706], [0.603],
    [Entropy-related], [0.700], [0.019, 0.894], [0.686],
  ),
  caption: [Descriptive session 1--2 reliability of the three cohort-anchored coordinate positions; n=13.]
)

The conventional EEG comparator endpoints exported by the same pipeline were also treated descriptively. Session 1--2 ICC estimates were approximately 0.41 for alpha/theta ratio, 0.76 for beta/alpha ratio, 0.45 for relative delta, and 0.79 for permutation entropy; complete values, intervals, SEM, and paired tests are in `reliability_conventional.csv`.

#figure(
  kind: table,
  clean-table(
    columns: (2.4fr, 0.8fr, 1.4fr, 0.8fr, 0.8fr),
    align: (left, center, center, center, center),
    table.header([*Comparator*], [*ICC*], [*Bootstrap 95% CI*], [*$r$*], [*FDR p*]),
    [`alpha/theta ratio`], [0.405], [0.058, 0.687], [0.498], [0.751],
    [`beta/alpha ratio`], [0.763], [0.545, 0.879], [0.799], [0.751],
    [`relative delta`], [0.455], [-0.008, 0.651], [0.453], [0.787],
    [`permutation entropy`], [0.793], [-0.212, 0.941], [0.803], [0.787],
  ),
  caption: [Descriptive reliability of conventional EEG comparators exported by the same pipeline; FDR is within this four-endpoint family.]
)

= S2.5 Nine-dimensional sensitivity and event outputs
The 9D Jacobian analysis tests ten exported summaries rather than the 3D reachability family. Its complete cases are n=10 for 4-to-8 months and n=9 for 4-to-12 months; the lowest raw p-values were 0.193 and 0.039, respectively, with separate-family FDR p-values of 1.000 and 0.391. The 4-to-8 loss is driven by `sub-13/ses-2` (155 invalid windows; zero retained), and the 4-to-12 loss additionally includes `sub-10/ses-4` (140 invalid windows; zero retained). No 9D value was imputed.

The event analysis pools available ages after averaging event-minus-`pre_near` contrasts within child. All 12 event-by-axis tests used 13 children, but the number of contributing sessions and minimum stage-label fraction are reported in `event_exploratory_tests.csv`. The water-deviation contrast had raw permutation p=0.0055 and BH p=0.066; it remains exploratory and is not evidence for a developmental or mechanistic effect.
