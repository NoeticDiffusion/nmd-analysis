// S2 Supplementary Data — coma_ndt_v.1.0 (I-CARE 2.1 CPC1 vs CPC5)

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "S2 Data - coma_ndt_v1.0",
  subtitle: "Complete contrast tables: discovery cohort, confirmatory cohort, joint replication call, TTM sensitivity, and Family-B subtypes",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S2.0 Discovery cohort — complete contrast table

Bundle `20260911_125829`, $n=71$ CPC1 / $70$ CPC5, primary `0_12h` window. Source:
`results/part1_corrected/outcome_contrasts.csv`.

#figure(
  kind: table,
  clean-table(
    columns: (1.1fr, 1.5fr, 0.7fr, 0.7fr, 1fr, 1fr, 0.6fr, 0.6fr),
    align: (left, left, center, center, center, center, center, center),
    inset: 4pt,
    table.header([*Family*], [*Metric*], [*n1*], [*n5*], [*$d$*], [*MW $p$*], [*BH $q$*], [*Test.*]),
    [diffusion H1-H3], [`d_eff_a_median`], [71], [70], [+0.76], [$7.0 times 10^(-7)$], [$2.0 times 10^(-6)$], [Y],
    [diffusion H1-H3], [`h_tilde_a_median`], [71], [70], [+0.58], [$1.3 times 10^(-6)$], [$2.0 times 10^(-6)$], [Y],
    [diffusion H1-H3], [`e_perp_median`], [71], [70], [+0.10], [0.043], [0.043], [Y],
    [diffusion H4], [`d_total_median`], [71], [70], [$-$0.47], [0.049], [n/a], [Y],
    [mnj_v3 primary], [`f_reactive`], [7], [6], [$-$0.27], [0.943], [n/a], [N],
    [mnj_v3 secondary], [`alpha_mean`], [7], [6], [+0.79], [0.138], [n/a], [N],
    [mnj_v3 secondary], [`omega_mean`], [7], [6], [+0.51], [0.101], [n/a], [N],
    [mnj_v3 secondary], [`f_contract`], [7], [6], [+0.51], [0.440], [n/a], [N],
    [mnj_v3 secondary], [`f_unstable`], [7], [6], [+0.26], [0.943], [n/a], [N],
    [mnj_v3 secondary], [$R_g mid alpha<0$], [7], [4], [$-$0.85], [0.788], [n/a], [N],
    [reachability], [`cone_d_eff_h1`], [71], [70], [+0.81], [$1.1 times 10^(-6)$], [n/a], [Y],
    [reachability], [`cone_d_eff_h4`], [71], [70], [+0.80], [$5.7 times 10^(-6)$], [n/a], [Y],
    [reachability], [`tube_d_eff`], [71], [70], [+0.82], [$2.2 times 10^(-6)$], [n/a], [Y],
  ),
  caption: [Discovery-cohort contrasts. `Test.` = `family_testable` (>=10 per arm). $d$ = Cohen's $d$, CPC1 minus CPC5. A 2026-09-12 ingest re-run left Family A tensors bit-identical (S2.12); H1-H4 were not recomputed.]
) <tab-s2-p1>

= S2.1 Confirmatory cohort — complete contrast table

Bundle `20260911_123135`, $n=70$ CPC1 / $70$ CPC5, primary `0_12h` window, zero subject overlap
with the discovery cohort. Source: `results/part2_confirmatory/outcome_contrasts.csv`.

#figure(
  kind: table,
  clean-table(
    columns: (1.1fr, 1.5fr, 0.7fr, 0.7fr, 1fr, 1fr, 0.6fr, 0.6fr),
    align: (left, left, center, center, center, center, center, center),
    inset: 4pt,
    table.header([*Family*], [*Metric*], [*n1*], [*n5*], [*$d$*], [*MW $p$*], [*BH $q$*], [*Test.*]),
    [diffusion H1-H3], [`d_eff_a_median`], [70], [70], [+0.61], [$5.3 times 10^(-4)$], [$1.6 times 10^(-3)$], [Y],
    [diffusion H1-H3], [`h_tilde_a_median`], [70], [70], [+0.48], [$4.8 times 10^(-3)$], [$7.2 times 10^(-3)$], [Y],
    [diffusion H1-H3], [`e_perp_median`], [70], [70], [$-$0.10], [0.134], [0.134], [Y],
    [diffusion H4], [`d_total_median`], [70], [70], [$-$0.36], [0.360], [n/a], [Y],
    [mnj_v3 primary], [`f_reactive`], [11], [11], [$-$0.11], [0.157], [n/a], [Y (borderline)],
    [mnj_v3 secondary], [`alpha_mean`], [11], [11], [$-$1.27], [0.013], [n/a], [Y (borderline)],
    [mnj_v3 secondary], [`omega_mean`], [11], [11], [+0.47], [0.511], [n/a], [Y (borderline)],
    [mnj_v3 secondary], [`f_contract`], [11], [11], [n/a], [1.000], [n/a], [Y (borderline)],
    [mnj_v3 secondary], [`f_unstable`], [11], [11], [+0.11], [0.157], [n/a], [Y (borderline)],
    [mnj_v3 secondary], [$R_g mid alpha<0$], [6], [10], [$-$0.62], [0.016], [n/a], [N],
    [reachability], [`cone_d_eff_h1`], [70], [70], [+0.66], [$2.3 times 10^(-4)$], [n/a], [Y],
    [reachability], [`cone_d_eff_h4`], [70], [70], [+0.74], [$8.3 times 10^(-5)$], [n/a], [Y],
    [reachability], [`tube_d_eff`], [70], [70], [+0.70], [$1.6 times 10^(-4)$], [n/a], [Y],
  ),
  caption: [Confirmatory-cohort contrasts, same metrics and pipeline as S2.0. "Y (borderline)" =
  n meets the 10-per-arm threshold but is well below typical power for the observed effect sizes;
  do not over-read the nominal `alpha_mean` result (S2.3). A 2026-09-12 ingest re-run left Family A
  tensors bit-identical (S2.12); H1-H4 were not recomputed.]
) <tab-s2-p2>

= S2.2 Joint replication table

#figure(
  kind: table,
  clean-table(
    columns: (1.1fr, 1.4fr, 0.8fr, 0.8fr, 1.6fr),
    align: (left, left, center, center, left),
    inset: 4pt,
    table.header([*Family*], [*Metric*], [*Disc. $d$*], [*Conf. $d$*], [*Replication call*]),
    [diffusion H1-H3], [`d_eff_a_median`], [+0.76], [+0.61], [replicated],
    [diffusion H1-H3], [`h_tilde_a_median`], [+0.58], [+0.48], [replicated],
    [diffusion H1-H3], [`e_perp_median`], [+0.10], [$-$0.10], [did_not_replicate],
    [diffusion H4], [`d_total_median`], [$-$0.47], [$-$0.36], [same_direction_not_both_bh_sig],
    [mnj_v3 primary], [`f_reactive`], [$-$0.27], [$-$0.11], [not_testable],
    [mnj_v3 secondary], [`alpha_mean`], [+0.79], [$-$1.27], [not_testable],
    [reachability], [`cone_d_eff_h1`], [+0.81], [+0.66], [same_direction_not_both_bh_sig],
    [reachability], [`cone_d_eff_h4`], [+0.80], [+0.74], [same_direction_not_both_bh_sig],
    [reachability], [`tube_d_eff`], [+0.82], [+0.70], [same_direction_not_both_bh_sig],
  ),
  caption: [`replicated` requires family-BH-significance in both cohorts with the same sign
  (applies only to the H1-H3 family, the only family with a defined BH correction group here).
  Reachability rows are individually significant, same-sign, in both cohorts but are not pooled
  into a BH family. Full machine-readable version:
  `results/replication/replication_summary.csv`.]
) <tab-s2-repl>

= S2.3 Family B (local generator) — why the small-$n$ numbers above should not be over-read

`alpha_mean` shows a nominally significant contrast in the confirmatory cohort ($p=0.013$,
$n=11$ vs $11$), in the *opposite* direction from `f_reactive`'s prediction ($alpha$ more
negative, i.e. more locally stable, in CPC5 rather than CPC1). Given: (1) this sample is drawn
from the $2.9%$ of confirmatory-cohort recordings that passed an increasingly strict fit-fidelity
gate, (2) that sample is not a random subsample of the cohort (it is conditioned on which
windows happened to be locally linear), and (3) the discovery cohort shows the opposite-signed,
non-significant trend on an even smaller sample ($n=7$ vs $6$), we do not interpret this as
evidence about $alpha$ or `F_reactive` in either direction. It is reported here in full for
transparency, consistent with `family_testable = "False"` / borderline `"True"` in the main-text
tables.

= S2.4 TTM subgroup sensitivity (H1-H3)

Source: `results/part1_corrected/ttm_sensitivity_contrasts.csv`,
`results/part2_confirmatory/ttm_sensitivity_contrasts.csv`.

#figure(
  kind: table,
  clean-table(
    columns: (0.9fr, 1.3fr, 0.8fr, 0.7fr, 0.7fr, 0.9fr, 0.9fr),
    align: (left, left, center, center, center, center, center),
    inset: 4pt,
    table.header([*Cohort*], [*Metric*], [*TTM*], [*n1*], [*n5*], [*$d$*], [*MW $p$*]),
    [Discovery], [`d_eff_a_median`], [33], [55], [49], [+0.52], [0.0013],
    [Discovery], [`h_tilde_a_median`], [33], [55], [49], [+0.34], [0.0016],
    [Discovery], [`e_perp_median`], [33], [55], [49], [+0.19], [0.023],
    [Discovery], [`d_eff_a_median`], [36], [7], [11], [n/a (below 10/arm)], [n/a],
    [Confirmatory], [`d_eff_a_median`], [33], [50], [50], [+0.47], [0.032],
    [Confirmatory], [`h_tilde_a_median`], [33], [50], [50], [+0.31], [0.145],
    [Confirmatory], [`e_perp_median`], [33], [50], [50], [$-$0.38], [0.0039],
    [Confirmatory], [`d_eff_a_median`], [36], [8], [8], [n/a (below 10/arm)], [n/a],
  ),
  caption: [TTM 33 degrees C is the dominant stratum in both cohorts (majority TTM-managed
  patients) and reproduces the H1 direction and significance. TTM 36 degrees C is under-powered
  in both cohorts and not reported as a contrast.]
) <tab-s2-ttm>

= S2.5 CPC5 majority-regime subtypes (descriptive only)

#figure(
  kind: table,
  clean-table(
    columns: (1fr, 1fr, 1fr, 1fr),
    table.header([*Cohort*], [*Majority regime*], [*n*], [*Fraction*]),
    [Discovery], [unassigned], [64], [0.914],
    [Discovery], [unstable], [6], [0.086],
    [Confirmatory], [unassigned], [59], [0.843],
    [Confirmatory], [unstable], [11], [0.157],
  ),
  caption: [CPC5-only subtyping by whichever of `f_contract`/`f_unstable`/`f_reactive` is
  numerically largest per patient. The large `unassigned` fraction in both cohorts reflects the
  fit-fidelity gate (S1.3), not an absence of dynamical structure; this subtyping is not
  currently informative and is reported for completeness only.]
) <tab-s2-subtypes>

= S2.6 Bootstrap confidence intervals (H1-H3, both cohorts)

Percentile bootstrap 95% CI, 2000 resamples, arms resampled independently, fixed seed
`20260912`. Source: `cohens_d_ci_lo`/`cohens_d_ci_hi` columns in
`results/part1_corrected/outcome_contrasts.csv`, `results/part2_confirmatory/outcome_contrasts.csv`.

#figure(
  kind: table,
  clean-table(
    columns: (1fr, 1.3fr, 0.8fr, 1.3fr, 0.8fr, 1.3fr),
    align: (left, left, center, center, center, center),
    inset: 4pt,
    table.header([*Metric*], [*Disc. $d$*], [*Disc. 95% CI*], [*Conf. $d$*], [*Conf. 95% CI*], []),
    [`d_eff_a_median`], [+0.76], [[0.40, 1.20]], [+0.61], [[0.29, 0.99]], [],
    [`h_tilde_a_median`], [+0.58], [[0.23, 1.01]], [+0.48], [[0.16, 0.83]], [],
    [`e_perp_median`], [+0.10], [[$-$0.20, 0.55]], [$-$0.10], [[$-$0.46, 0.23]], [],
  ),
  caption: [H1-H3 bootstrap CIs, both cohorts, original `mnps_3d_dot` drift proxy for $E_perp$.
  Note $E_perp$'s CI spans zero in both cohorts, consistent with the non-replication call.
  Full precision in `outcome_contrasts.csv`.]
) <tab-s2-bootstrap>

= S2.7 Leave-one-subject-out (LOSO) sensitivity

Source: `results/part1_corrected/loso_sensitivity_summary.csv`,
`results/part2_confirmatory/loso_sensitivity_summary.csv`. `stable_at_0.05` = true iff every
single-patient drop keeps nominal significance on the same side of $alpha=0.05$ as the baseline.

#figure(
  kind: table,
  clean-table(
    columns: (1fr, 1.1fr, 1.4fr, 1.4fr, 1fr),
    align: (left, left, center, center, center),
    inset: 4pt,
    table.header([*Cohort*], [*Metric*], [*Baseline $p$*], [*LOSO $p$ range*], [*Stable?*]),
    [Discovery], [`d_eff_a_median`], [$7.0 times 10^(-7)$], [[$2.4 times 10^(-7)$, $1.1 times 10^(-6)$]], [Yes],
    [Discovery], [`h_tilde_a_median`], [$1.3 times 10^(-6)$], [[$4.8 times 10^(-7)$, $2.1 times 10^(-6)$]], [Yes],
    [Discovery], [`e_perp_median`], [0.043], [[0.029, 0.058]], [*No*],
    [Confirmatory], [`d_eff_a_median`], [$5.3 times 10^(-4)$], [[$2.8 times 10^(-4)$, $7.9 times 10^(-4)$]], [Yes],
    [Confirmatory], [`h_tilde_a_median`], [$4.8 times 10^(-3)$], [[$2.8 times 10^(-3)$, $6.9 times 10^(-3)$]], [Yes],
    [Confirmatory], [`e_perp_median`], [0.134], [[0.097, 0.172]], [Yes (stably non-sig.)],
  ),
  caption: [H1 and H2 never cross the $alpha=0.05$ boundary under any single-patient drop, in
  either cohort. H3 (original drift proxy) straddles the boundary in the discovery cohort
  (unstable) and is stably non-significant in the confirmatory cohort.]
) <tab-s2-loso>

= S2.8 Run-level mixed-effects cross-check (H1-H3)

Linear mixed model, subject random intercept, REML, fit on per-run medians in the primary
window (not collapsed to one value per patient: discovery 1556 runs / 141 subjects, mean 11.0
runs/subject; confirmatory 1692 runs / 140 subjects, mean 12.1 runs/subject). Source:
`results/part1_corrected/mixed_effects_check.csv`, `results/part2_confirmatory/mixed_effects_check.csv`.

#figure(
  kind: table,
  clean-table(
    columns: (1fr, 1.2fr, 1fr, 1fr, 1fr, 1fr),
    align: (left, left, center, center, center, center),
    inset: 4pt,
    table.header([*Cohort*], [*Metric*], [*coef (1$-$5)*], [*SE*], [*$z$*], [*$p$*]),
    [Discovery], [`d_eff_a_median`], [+0.228], [0.050], [4.53], [$5.8 times 10^(-6)$],
    [Discovery], [`h_tilde_a_median`], [+0.091], [0.026], [3.48], [$5.0 times 10^(-4)$],
    [Discovery], [`e_perp_median`], [+0.009], [0.013], [0.63], [0.526],
    [Confirmatory], [`d_eff_a_median`], [+0.152], [0.042], [3.65], [$2.6 times 10^(-4)$],
    [Confirmatory], [`h_tilde_a_median`], [+0.073], [0.024], [3.04], [$2.4 times 10^(-3)$],
    [Confirmatory], [`e_perp_median`], [$-$0.015], [0.021], [$-$0.72], [0.474],
  ),
  caption: [Run-level mixed model independently confirms H1/H2 in both cohorts (same sign,
  significant) and confirms H3's non-significance with the original drift proxy. This rules out
  the patient-median collapse as the source of the H1/H2 signal.]
) <tab-s2-mixed>

= S2.9 Post-hoc residual hospital batch-effect diagnostic

One-way $eta^2$ of hospital on the *derived* Family-A metrics (not the raw upstream features),
flagged against a 0.06 medium-effect convention (Cohen 1988). Source:
`results/part1_corrected/combat_residual_batch_effect.csv`,
`results/part2_confirmatory/combat_residual_batch_effect.csv`,
`results/{part1_corrected,part2_confirmatory}/hospital_cpc_composition.csv`.

#figure(
  kind: table,
  clean-table(
    columns: (1fr, 1.2fr, 1fr, 1fr, 1fr),
    align: (left, left, center, center, center),
    inset: 4pt,
    table.header([*Cohort*], [*Metric*], [*$eta^2$*], [*$p$*], [*Flagged?*]),
    [Discovery], [`d_eff_a_median`], [0.172], [$3.4 times 10^(-5)$], [Yes],
    [Discovery], [`h_tilde_a_median`], [0.179], [$1.9 times 10^(-5)$], [Yes],
    [Discovery], [`e_perp_median`], [0.115], [$2.2 times 10^(-3)$], [Yes],
    [Discovery], [`d_total_median`], [0.020], [0.589], [No],
    [Confirmatory], [`d_eff_a_median`], [0.132], [$7.2 times 10^(-4)$], [Yes],
    [Confirmatory], [`h_tilde_a_median`], [0.170], [$4.4 times 10^(-5)$], [Yes],
    [Confirmatory], [`e_perp_median`], [0.151], [$1.8 times 10^(-4)$], [Yes],
    [Confirmatory], [`d_total_median`], [0.037], [0.270], [No],
  ),
  caption: [Residual hospital $eta^2$ on H1-H3 remains above the flag threshold in both cohorts
  after ComBat. Hospital-CPC composition: discovery is imbalanced at one site (hospital E: 2
  CPC1 / 15 CPC5); confirmatory is exactly balanced at every site (A 38/38, B 9/9, D 7/7, E 7/7,
  F 9/9), so the confirmatory-cohort residual $eta^2$ cannot itself be a CPC-selection confound.]
) <tab-s2-combat-diag>

= S2.10 Qualified-drift $E_perp$ robustness check (post-hoc, both cohorts)

Full detail for the Savitzky-Golay smoothed-drift $E_perp$ re-derivation (main text §4.7).
Source: `results/{part1_corrected,part2_confirmatory}/qualified_drift_contrast.csv`,
`qualified_drift_loso_summary.json`.

#figure(
  kind: table,
  clean-table(
    columns: (1.3fr, 0.8fr, 0.8fr, 1.3fr, 1.3fr, 1.2fr),
    align: (left, center, center, center, center, center),
    inset: 4pt,
    table.header([*Cohort*], [*n1*], [*n5*], [*$d$ (95% CI)*], [*MW $p$*], [*LOSO $d$ range*]),
    [Discovery], [71], [70], [+0.68 [0.39, 0.99]], [$6.4 times 10^(-6)$], [[0.656, 0.750]],
    [Confirmatory], [70], [70], [+0.47 [0.16, 0.79]], [0.0088], [[0.440, 0.519]],
  ),
  caption: [Qualified-drift $E_perp$ (Savitzky-Golay window 11, 2nd-order polynomial). LOSO:
  0/141 (discovery) and 0/140 (confirmatory) single-patient drops flip nominal significance or
  sign.]
) <tab-s2-qualdrift>

#figure(
  kind: table,
  clean-table(
    columns: (0.9fr, 1fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center, center),
    inset: 4pt,
    table.header([*Savgol window*], [*Disc. $d$*], [*Disc. $p$*], [*Conf. $d$*], [*Conf. $p$*]),
    [7 ($approx$28 s)], [+0.73], [$5.3 times 10^(-7)$], [+0.49], [$6.5 times 10^(-3)$],
    [11 ($approx$44 s, primary)], [+0.68], [$6.4 times 10^(-6)$], [+0.47], [$8.8 times 10^(-3)$],
    [15 ($approx$60 s)], [+0.71], [$3.1 times 10^(-6)$], [+0.53], [$5.1 times 10^(-3)$],
    [21 ($approx$84 s)], [+0.69], [$2.5 times 10^(-6)$], [+0.48], [$1.4 times 10^(-2)$],
  ),
  caption: [Smoothing-window sensitivity sweep. The direction, significance, and approximate
  effect size are stable across a 3x range of smoothing bandwidth in both cohorts, arguing
  against a cherry-picked window as the explanation for R7's finding.]
) <tab-s2-qualdrift-sweep>

= S2.11 Spectral abscissa — ingest re-run identity and gated CPC contrast

Paired recording-level comparison of `/jacobian/derived_metrics/v1` on every
matching stem between the 2026-09-11 predecessor bundles and the 2026-09-12
re-runs (`icare_v2_family_b_ingest_comparison.py`). Family B remains not
testable; this table is a measurement-identity check plus the descriptive
gated $alpha$ contrast already in S2.0–S2.1.

#figure(
  kind: table,
  clean-table(
    columns: (1.3fr, 1fr, 1fr),
    align: (left, center, center),
    inset: 4pt,
    table.header([*Quantity*], [*Discovery*], [*Confirmatory*]),
    [Paired stems (old vs new)], [1815 / 1815], [1838 / 1838],
    [`computation_status` agree], [1815 / 1815], [1838 / 1838],
    [Gate `computed` (old = new)], [22], [53],
    [$|Delta "rel\_mse"|$ median / max], [0 / 0], [0 / 0],
    [$|Delta alpha_"mean"|$ on `computed` runs], [0 / 0], [0 / 0],
    [New files with `knn_k` in provenance], [1773 / 1815], [1696 / 1838],
    [Old files with `knn_k`], [0], [0],
  ),
  caption: [The 2026-09-12 re-runs document an existing kNN Jacobian
  (`knn_k=20`, `min_samples=4`) but do not change spectral abscissa or the
  fit-fidelity residual. Source:
  `results/replication/family_b_abscissa_comparison_summary.csv`.]
) <tab-s2-alpha-ingest>

#figure(
  kind: table,
  clean-table(
    columns: (1.4fr, 1fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center, center),
    inset: 4pt,
    table.header([*Contrast (gated $alpha$)*], [*n1 / n5*], [*$d$*], [*MW $p$*], [*Call*]),
    [Discovery, patient-level, 0–12h], [7 / 6], [+0.79], [0.138], [not testable],
    [Discovery, `computed` runs], [16 / 6], [+0.81], [n/a], [descriptive],
    [Confirmatory, patient-level, 0–12h], [11 / 11], [$-$1.27], [0.013], [borderline $n$],
    [Confirmatory, `computed` runs], [24 / 29], [$-$0.95], [n/a], [descriptive],
    [Discovery $F_"reactive"$ (patient)], [7 / 6], [$-$0.27], [0.943], [not testable],
    [Confirmatory $F_"reactive"$ (patient)], [11 / 11], [$-$0.11], [0.157], [borderline $n$],
  ),
  caption: [The CPC1–CPC5 sign of $alpha$ flips across cohorts. Do not treat
  the confirmatory $p=0.013$ as a Family B finding: the sample is the 2.9%
  of recordings that happened to be locally linear, and discovery points the
  other way. Source: `results/replication/family_b_abscissa_comparison.md`.]
) <tab-s2-alpha-cpc>

= S2.12 Diffusion and drift ingest audit (2026-09-12 re-runs)

Paired every matching recording (`icare_v2_diffusion_drift_ingest_comparison.py`).
Family A tensors are identical to the 2026-09-11 predecessors; H1–H4 do not
need to be recomputed. Stored alignment $A_"bD"$ is all-NaN (contract:
`drift_source = not_supplied`). `/mnps_3d_dot` is unchanged across ingest
generations and is closer to a Savitzky-Golay chart derivative than to a raw
one-step increment.

#figure(
  kind: table,
  clean-table(
    columns: (1.6fr, 1fr, 1fr),
    align: (left, center, center),
    inset: 4pt,
    table.header([*Quantity*], [*Discovery*], [*Confirmatory*]),
    [Paired stems], [1815], [1838],
    [Diffusion status agree / `computed`], [1815 / 1778], [1838 / 1797],
    [$|Delta d_"eff"|$ median / max], [0 / 0], [0 / 0],
    [$|Delta D_"total"|$ median / max], [0 / 0], [0 / 0],
    [$|Delta |a_"hat"||$ median], [0], [0],
    [$|Delta |"mnps\_3d\_dot"||$ median / max], [0 / 0], [0 / 0],
    [$|Delta |"coords\_3d"||$ median], [0], [0],
    [Stored $A_"bD"$ finite fraction], [0], [0],
    [`mnps_3d_dot` vs $Delta x/Delta t$ MAE], [0.115], [0.111],
    [`mnps_3d_dot` vs Savitzky-Golay 7/3 MAE], [0.057], [0.057],
    [Closer to Savitzky-Golay than one-step], [99.9%], [99.9%],
  ),
  caption: [Diffusion geometry is bit-stable across the 2026-09-12 re-run.
  `mnps_3d_dot` is a configured MNPS derivative, not a raw finite difference,
  and is still not a qualified Itô drift. Source:
  `results/replication/diffusion_drift_ingest_comparison.md`.]
) <tab-s2-diff-drift-audit>

= S2.13 Rank discrimination — AUROC and AUPRC

Direct CPC1-high AUROC / AUPRC on the same 0-12h patient-medians as R2-R3, plus
univariate logistic repeated-CV AUROC. Not a prognostic model. Source:
`results/replication/family_a_auroc_comparison.csv`.

#figure(
  kind: table,
  clean-table(
    columns: (1.4fr, 1.5fr, 1.5fr, 0.9fr, 0.9fr),
    align: (left, center, center, center, center),
    inset: 4pt,
    table.header(
      [*Metric*],
      [*Disc. AUROC [CI]*],
      [*Conf. AUROC [CI]*],
      [*Disc. AUPRC*],
      [*Conf. AUPRC*],
    ),
    [`d_eff_a_median` (H1)], [0.74 [0.66, 0.83]], [0.67 [0.58, 0.76]], [0.74], [0.67],
    [`h_tilde_a_median` (H2)], [0.74 [0.65, 0.82]], [0.64 [0.55, 0.73]], [0.73], [0.65],
    [`e_perp_median` (H3 stored)], [0.60 [0.51, 0.69]], [0.43 [0.33, 0.52]], [0.56], [0.44],
    [`d_total_median` (H4)], [0.40 [0.31, 0.50]], [0.46 [0.36, 0.55]], [0.42], [0.45],
    [`cone_d_eff_h1`], [0.74 [0.65, 0.82]], [0.68 [0.59, 0.77]], [0.73], [0.67],
    [`e_perp_qualified` (R7, post-hoc)], [0.72 [0.63, 0.81]], [0.63 [0.53, 0.72]], [0.70], [0.65],
  ),
  caption: [Chance AUROC = 0.5; chance AUPRC $approx$ 0.50 (balanced arms). Direct AUROC is
  the Mann-Whitney rank probability, not a fitted model. Univariate logistic repeated-CV
  AUROC matches the direct values for H1/H2 (discovery 0.74 / 0.74; confirmatory 0.67 /
  0.64). Hospital-LOSO AUROC is lower (H1 0.70 / 0.62; H2 0.69 / 0.55). R7 remains post-hoc.]
) <tab-s2-auroc>

= S2.14 Local-dynamics coverage (beyond spectral abscissa)

Window- and run-level scan of every recording in the 2026-09-11 article bundles
(`icare_v2_local_dynamics_coverage.py`). This is coverage under the current contract,
not a CPC contrast and not an ingest-identity check.

#figure(
  kind: table,
  clean-table(
    columns: (1.7fr, 1fr, 1fr, 1.6fr),
    align: (left, center, center, left),
    inset: 4pt,
    table.header([*Object*], [*Disc. `computed`*], [*Conf. `computed`*], [*Call*]),
    [Diffusion `a_hat`], [1778/1815 (98.0%)], [1797/1838 (97.8%)], [usable for H1/H2/H4],
    [`/mnps_3d_dot` row-finite], [1.00], [1.00], [present; not Itô drift],
    [Stored $A_"bD"$ finite], [0], [0], [`drift_source = not_supplied`],
    [Jacobian 3D $alpha$], [22/1815 (1.2%)], [53/1838 (2.9%)], [Family B not testable],
    [Jacobian 9D $alpha$], [1200/1815 (66%)], [340/1838 (18%)], [not the article chart],
    [FTR 3D], [1791/1815 (99%)], [1767/1838 (96%)], [`model_derived`; 1769/1715 files also Jac3-gated],
    [Stored reachability 3D], [18/1815 (1.0%)], [38/1838 (2.1%)], [inherits Jac3 gate],
    [Transition residuals 3D], [1772/1815 (98%)], [1693/1838 (92%)], [populated; not a primary endpoint],
    [Destination / resilience], [0/1815], [0/1838], [contract `not_testable`],
  ),
  caption: [Mean window-level finite fraction of `a_hat` is 1.00 on files that carry a series.
  `qc_ok_eeg = -1` on 100% of windows. `conventional_eeg` is absent from both exports.
  Source: `results/replication/local_dynamics_coverage.md`.]
) <tab-s2-local-dyn-cov>

*Why stored Itô drift is absent.* Chart velocity `/mnps_3d_dot` is fully populated
(Savitzky-Golay derivative of the MNPS chart). Ingest still passes `drift=None` into the
diffusion adapter (C1 default): MNPS $dot(x)$, Jacobian intercepts, and same-sample increment
means are contractually *refused* as $b$. Identification of an independent chart drift belongs
in the analysis repo (SL-005 / DF-DRIFT-C1-M3), not ingest. Consequence: `A_bD` and $R_(b/a)$
are explicitly `not_testable` with `drift_alignment_failure_reason =
independent_drift_not_supplied`. Empty alignment is not a silent miss and must not be filled by
piping `/mnps_3d_dot` into `drift_source`.

*Jacobian 9D $alpha$ is the same functional, not the article Family B object.*
`/jacobian_9D/derived_metrics/v1/series/spectral_abscissa` is $alpha = max "Re" lambda(J)$ with
the same schema (`mndm.jacobian_metrics.v1`), the same fidelity gate (`rel_mse_baseline_median
< 0.9`), and the same units (`1/second`) as 3D Family B. The operator is fit on
`coords_9d`, whose `e_m` axis is a documented non-equivalent fallback (S3.4d). Recording-level
`computed` is 1200/1815 (discovery) and 340/1838 (confirmatory), of which 1192 and 322 files
are 9D-`computed` while 3D Jacobian remains gated. Confirmatory 9D-`computed` files often
retain only a thin window sliver (median 20 windows). This is not a rescue of Family B.

#bibliography("references.bib", style: "apa")
