#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "APPLESEED methods",
  subtitle: "Measurement contract, endpoint computation, and statistical protocol",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S1.1 Dataset and measurement contract
The APPLESEED Example Dataset, OpenNeuro ds003710 version 1.0.2 @OpenNeuroDS003710, contains 48 longitudinal recordings from 13 infants (7 male and 6 female in the exported participant metadata). Sessions 1 and 2 are approximately one week apart at four months. Sessions 3 and 4 are approximately eight and twelve months, respectively, and are available for 11 children. The source export is `neuralmanifolddynamics_ds003710_20260804_153346`; the complete cohort-anchor identifier and hash are recorded in S3 and the machine-readable manifest. Ages are nominal file-stratum labels rather than individually measured ages in this reanalysis. The release follows BIDS and its EEG extension @Gorgolewski2016 @Pernet2019. The dataset is public and de-identified; no new data collection or participant contact was involved.

The export was created from 32-channel EEG, downsampled to 250 Hz, average-referenced, and band-passed from 1 to 45 Hz. It uses 8-s analysis windows with 4-s steps. All statistical analyses operate on recording summaries, not raw epochs.

= S1.2 Coordinate and Jacobian contract
The export supplies a three-dimensional chart in order $[m,d,e]$, a nine-dimensional stratified coordinate set, Jacobians, and a geometry-contract status for each recording. The primary analysis requests the `cohort_anchored` coordinate contract, constructed with the frozen subject-balanced global IQR anchor `ds003710_global_cohort_all_timepoints_iqr_v2_1` from 8,179 usable epochs. This supports a common descriptive coordinate scale across age strata. The global anchor includes all study ages and therefore is not a held-out-age normalization. Subject-anchored coordinates are used only for within-session event contrasts. The 3D cohort layer and 3D Jacobian are available in all 48 sessions; 9D Jacobians are available in 46/48.

For a local chart flow $dot(x)=f(x,t)$, the MNJ is:

$ J_(i j)(x,t) = partial f_i(x,t) / partial x_j $. <eq:mnj>

The primary MNJ scalar summaries are the trace of $J$, its Frobenius norm, its antisymmetric rotation norm, and its spectral radius. The reachability summaries are covariance log-determinant, effective dimension, condition number, directional entropy, and rotation proxy. For covariance eigenvalues $lambda_i$, effective dimension is $(sum_i lambda_i)^2 / sum_i lambda_i^2$, condition number is the largest-to-smallest eigenvalue ratio, and directional entropy is the normalized entropy of eigenvalue proportions. The Jacobian and reachability quantities are chart/model outputs with endpoint-specific units; per-window values are reduced to a session median.

= S1.3 Reachability computation
The shared `ndt-analysis` implementation fits local linear transitions and propagates:

$ Sigma_t^(h+1) = A_t Sigma_t^(h) A_t^T + Q_t $. <eq:reach>

The frozen primary specification is 3D cohort-anchored coordinates, within-session $k=12$ neighbors, horizon $h=3$, ridge estimation with alpha 0.001, and median aggregation. Neighbors are never pooled across visits or children. Session endpoints are `tube_log_det_median`, `tube_d_eff_median`, `tube_kappa_median`, `tube_dir_entropy_median`, and `tube_rotation_median`. Reachability represents locally modelled variation in the chart; it is neither state occupancy nor a direct measure of cognitive capacity.

= S1.4 Primary reliability analysis
For each primary endpoint, session 1 and session 2 values from the 13 children form the paired sample. The reported ICC is McGraw and Wong's two-way absolute-agreement single-measure ICC(A,1), with fixed session occasions treated as the two measurement occasions. We also report Pearson correlation descriptively, mean and median session difference, paired $d_z$, standard error of measurement, and minimum detectable change at 95%. ICC intervals use 2,000 subject-resampling bootstrap draws. The FDR column applies to paired Wilcoxon session-difference p-values, not to the ICC. Agreement is not inferred from correlation alone @ShroutFleiss1979 @McGrawWong1996 @BlandAltman1986.

= S1.5 Longitudinal analysis
The longitudinal panel contains only the 11 children with all four sessions; the two reliability-only children are excluded. The primary age comparisons pair each child's four-month mean, calculated as the mean of sessions 1 and 2, with session 3 at eight months and session 4 at twelve months. We report exact two-sided Wilcoxon signed-rank raw p-values using SciPy's `zero_method="wilcox"`, paired $d_z$, and 2,000-draw child bootstrap intervals for the mean difference. Each age-specific 3D dynamical result has its own nine-endpoint FDR family. Coordinate positions use a separate three-endpoint family; conventional EEG comparators use a separate four-endpoint family. Session-1-only contrasts and Friedman tests are secondary baseline sensitivities; the 18-test retest-mean output is a pooled-multiplicity sensitivity of the two primary contrasts, not a different estimand. Nine-dimensional Jacobian summaries are separate complete-case sensitivity analyses with n=10 at 8 months and n=9 at 12 months because `sub-13/ses-2` and `sub-10/ses-4` have no retained 9D Jacobian windows.

= S1.6 Multiple tests and exploratory events
The primary family contains nine endpoints. As this is an exploratory reanalysis, raw p-values and effect sizes are the emphasized quantities for the balanced 4-to-8-month comparison, while both 4-to-8- and 4-to-12-month nine-endpoint families are reported. Benjamini--Hochberg values are retained as named transparency sensitivities, not as a single pooled discovery threshold @BenjaminiHochberg1995. Event-window analyses cover object, water, speech, and face labels. For each child-session-event type, event windows are contrasted with pre-near windows and then averaged across available sessions within child before a 2,000-draw sign-flip permutation test. The event analysis therefore pools ages and reports the number of contributing sessions and minimum stage-label coverage. These analyses are explicitly exploratory.

= S1.7 Reproducibility
`src/run_appleseed_analysis.py` orchestrates the analysis. `01_export_session_metrics.py` reads H5 contracts and exports one row per child-session. `02_reliability_longitudinal.py` performs the primary statistics. `03_event_locked_exploratory.py` is separate from the primary pipeline. `04_make_figures.py` creates the displayed figures.

#bibliography("references.bib", style: "apa")
