#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Task Contrasts Dissociate Across Neural-Dynamics Estimators",
  short-title: "Estimator-specific EEG task contrasts",
  subtitle: "Local drift and chart-Jacobian contrasts do not recur in identified one-step dynamics",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("EEG", "within-subject", "local dynamics", "reachability", "quality control", "exploratory analysis"),
  article-type: "Research Article",
  abstract: [We asked whether resting state, cognitive control (CC), and gambling (GG) differ in explicitly non-interchangeable summaries of a subject-anchored neural chart. We reanalysed 134 EEG recordings from 45 OpenNeuro participants (45 Rest, 45 CC, 44 GG; one documented GG recording absent). Within-subject Wilcoxon tests and BH-FDR were applied in separate endpoint families. Local L1 drift magnitude showed the clearest hierarchy: chart-drift norm effects were $d_z=1.82$, $0.505$, and $1.43$ for GG--Rest, CC--Rest, and GG--CC, respectively, and remained $1.44$, $0.536$, and $0.947$ under a deterministic 400-s prefix sensitivity. GG minus Rest also increased the local chart-Jacobian spectral abscissa (median difference 0.01248, paired $d_z=1.42$, $n=44$, $q=5.61 times 10^-10$), whereas the independently identified lag-1 one-step spectral abscissa did not increase ($d_z=-0.33$, $n=32$, $q=0.18$). On common support, standardized subject-level chart and L3 task contrasts were inversely rank-associated for GG--Rest ($rho_s=-0.38$, $n=32$, bootstrap 95% CI [-0.68, -0.001]) and agreed in sign for only 12/32 pairs. Reachability amplitude summaries were available for 131/134 recordings; all three missing certificates failed the same numerical PSD gate, one in each task. Because task durations did not overlap and reachability was exported only as recording-level scalars, its large contrasts are not established as duration-independent. These export-level results establish a dissociation among estimators, not a neural mechanism, clinical biomarker, or confirmatory task effect.],
  author-summary: [The same EEG data can support different mathematical summaries of change. Gambling altered a local chart-Jacobian quantity but not its separately estimated one-step analogue. Occupancy, local flow, one-step dynamics, and reachability must therefore be tested and reported as different questions.],
  author-contributions: [RL: Conceptualization, Methodology, Software, Data Curation, Analysis, Writing, and Editing.],
  funding-info: [No dedicated funding is reported.],
  data-availability: [OpenNeuro ds004511 is publicly available under CC0. Article-local code, pinned configuration, result tables, and provenance are in the accompanying NeuralManifoldDynamics repository.],
  competing-interests: [The author developed NDT, MNPS, and software used in this analysis.],
)

#set heading(numbering: "1.")

= Introduction <sec:intro>

Neural recordings are increasingly analysed as trajectories of coordinated populations rather than as independent feature lists. Dimensionality reduction makes this shift operational but also makes the choice of coordinates part of the measurement problem @cunningham2014dimensionality. Population-level analyses have connected low-dimensional representations to computation, context, and cognitive complexity @saxena2019neural @vyas2020computation @shine2019low. A low-dimensional state description, however, does not by itself identify the rule that moves the state through that space. The distinction between manifold structure and dynamical law is explicit in the neural-population literature @duncker2021dynamics.

That distinction motivates the present measurement study. Occupancy describes where a recording lies in a declared chart; a local chart Jacobian describes a local derivative of an estimated flow; an identified one-step map describes a fitted transition relation conditional on support; and a finite-horizon reachability certificate describes a separate propagation construction. Rotational population dynamics and context-dependent recurrent dynamics provide useful precedents for studying trajectories and operators, but they do not make every local or finite-step summary interchangeable @churchland2012neural @mante2013context. Data-driven operator methods likewise make the measurement representation and identification support explicit @brunton2016extracting @brunton2022koopman.

The measurement-boundary formulation of Noetic Diffusion Theory (NDT) supplies the present MNPS chart and qualification vocabulary, while the external literature supplies the broader reason to separate representation from dynamics @langell2025ndt. The scientific question is therefore not whether two names for one quantity disagree. It is whether task contrasts remain coherent across declared estimator classes, and if not, which level carries the task information and which level is limited by support or duration.

#netn-box(title: [Core question])[
  In a fixed, subject-anchored export, do task contrasts agree across local chart-Jacobian, identified one-step L2/L3, and reachability summaries, or do they expose estimator-specific structure and limitations?
]

= Methods <sec:methods>

== Dataset and fixed measurement contract

The frozen export contains 134 recordings from 45 healthy participants: 45 Rest, 45 CC, and 44 GG recordings from OpenNeuro ds004511 @makowski2026_ds004511. One participant has no recorded GG EEG; this is retained as documented missingness rather than imputed. The input contract is the canonical MNPS `[m,d,e]` chart and its stratified 9D definition, with coordinates declared `subject_anchored`. No analysis retunes a measurement against task differences.

== Endpoint families and statistics

The first family contains chart occupancy, local chart-Jacobian invariants, L1 local-law quantities, and recording-level reachability. Its substantive correction contains 45 pairwise tests; rank-degenerate `reach_d_eff` is retained as QC but excluded from BH correction and significance sorting. The second, separate 36-test family contains chart-Jacobian alpha as a bridge endpoint alongside lag-1 one-step L2/L3 quantities. Unless explicitly labelled otherwise, chart-alpha $q$ values quoted in the main text come from this bridge family, avoiding a choice between duplicate corrections after seeing the result. Chart-Jacobian alpha is the spectral abscissa of a local chart Jacobian; L3 alpha is the spectral abscissa of the matrix-log generator proxy `log(Phi)/dt` for an identified direct lag-1 map (4 s), not the spectral abscissa of `Phi` itself and not an Ito generator. They are not two labels for one estimator. Lag-2 was attempted, but only 13 direct L2 maps and 10 L3 proxies were computed (8 s; task-imbalanced), too sparse for a panel. L4 `reach_a_q` and `reach_v_norm` are amplitude summaries rather than validated capacity or dimension measures.

Recording values were reduced to subject-by-task medians. Pairwise later-minus-earlier contrasts used complete-case Wilcoxon signed-rank tests @wilcoxon1945, paired $d_z$, and BH-FDR @benjamini1995 within the relevant panel. The L2/L3 pairwise panel's reported $q$ is the global 36-test Wilcoxon family; its Friedman table is a separate 12-test family. Friedman tests use complete triplets. Bootstrap summaries use 10,000 draws with seed 20260921. This is an exploratory discovery analysis on one export: `exploratory_discovery_20260921_g4_not_locked`.

== Why the estimators need not agree

The local chart quantity is formed from an estimated local flow $hat b_x$ in the declared chart and summarized through its Jacobian,
$
  hat J_x(x) = partial hat b_x(x) / partial x,
$
with chart-Jacobian alpha equal to the spectral abscissa of the exported local Jacobian summary. The one-step map instead has the affine form
$
  x_(t + Delta t) approx Phi (x_t - bar x) + c,
$
and the exported L3 generator proxy is
$
  hat A_("L3") = G / Delta t.
$
Here $G$ denotes the exported `logm(Phi)` matrix. The latter is a qualified matrix-log proxy, not an Itô generator and not the spectral abscissa of $Phi$ itself. In this export it is written only when the lag-1 map passes the existing two-fold out-of-fold identification gate and `logm(Phi)/Delta t` is real; otherwise the L3 leaves remain unsupported. A real generator is therefore a qualification outcome of the frozen exporter, not a numerical instruction to repair or reinterpret unsupported maps.

These objects would approximate one continuous-time local generator only under restrictive conditions: a locally linear and approximately time-homogeneous process, the same effective state representation, adequate sampling, comparable conditioning and support, and a one-step map that actually represents the local flow in the region being summarized. Even then, the nonlinearity of spectral and logarithmic operations means there is no general identity between a median of window-level chart-Jacobian abscissae and the abscissa of a fitted matrix-log proxy. The present result is thus a measurement-science result about non-interchangeability, not a paradox between identical estimators.

To test the estimator contrast directly without comparing raw endpoint units, we also ran a separate exploratory interaction analysis on the 121 recordings with both production-supported alpha estimators. Each estimator was centered by its pooled common-support recording median and scaled by 1.4826 times MAD before task contrasts were formed. The interaction for each complete subject was `(chart-alpha_z later - chart-alpha_z earlier) - (L3-alpha_z later - L3-alpha_z earlier)`. Wilcoxon signed-rank tests and BH-FDR over the three task contrasts form a separate three-test family; 100,000 sign-flips and 10,000 bootstrap draws are robustness summaries. This estimand is normalization-dependent and exploratory, not a raw-unit equality test.

Because recording duration differs strongly by task, a bounded post-discovery sensitivity diagnostic re-aggregated the already exported chart-Jacobian alpha series over the deterministic first 100 four-second windows (400 s) of every recording. It retained the production finite-value rule (at least 30 finite windows and at least 50% valid), introduced no padding or re-fitting, and corrected the three fixed-prefix alpha contrasts as their own sensitivity family. L4 could not be re-estimated on this prefix because the export contains recording-level certificate scalars rather than per-window L4 series; duration associations for L4 are therefore audit-only.

#figure(
  image("figures/conceptual/ds004511_estimator_pipeline_concept_20260921.png", width: 100%),
  caption: [Conceptual analysis map. EEG recordings are processed through NeuralManifoldDynamics and nmd-analysis before task contrasts are formed. Chart-Jacobian, identified one-step L2/L3, and L4 reachability are separate estimator classes. This illustration contains no empirical values or biological interpretation.]
) <fig-conceptual-pipeline>

= Results <sec:results>

== R1: Coverage and quality control <sec:r1>

All 134 recordings had a finite included chart-Jacobian alpha. Lag-1 one-step quantities were identified for 121/134 recordings (115/134 for the history-conditioned L2 quantity); hence the L2/L3 paired samples are smaller than the chart-Jacobian samples. Three recordings lacked finite included `reach_a_q`: one Rest, one CC, and one GG recording from different people. Each was marked invalid after `post_dtype_psd_failure` at gate F. This is a numerical certificate failure pattern, not evidence for task-specific absence.

#figure(kind: table, clean-table(
  columns: (2.3fr, 1.2fr, 2.5fr), align: (left, center, left), inset: 4pt,
  table.header([*Object*], [*Finite recordings*], [*Interpretive status*]),
  [Chart-Jacobian alpha], [134/134], [Included; local-chart quantity],
  [Lag-1 one-step L2/L3], [121/134], [Included only on identified support],
  [History-conditioned L2], [115/134], [Secondary identified-support quantity],
  [L4 amplitude summaries], [131/134], [Included with invalid certificates visible],
  [L4 effective dimension], [131/134], [Method-limited; not tested as dimension],
), caption: [Endpoint coverage. Missingness changes the eligible paired sample; it is not replaced by zeros.]) <tab-coverage>

== R2: Local drift and diffusion carry different task information <sec:r2>

The complete L1 family makes the estimator hierarchy visible before the alpha bridge. The local chart-drift norm `chart_drift_b_hat_norm` showed large full-recording effects for GG--Rest ($d_z=1.82$, $q=1.62 times 10^-11$), CC--Rest ($d_z=0.505$, $q=0.0151$), and GG--CC ($d_z=1.43$, $q=1.08 times 10^-10$). Re-aggregating every recording over the same first 400 s retained all three directions and their fixed-prefix family correction: $d_z=1.44$, $0.536$, and $0.947$, with $q=2.02 times 10^-9$, $0.00586$, and $1.37 times 10^-6$, respectively. Thus the local drift-norm hierarchy is not explained by the unequal recording lengths in this bounded sensitivity.

Diffusion-norm results were weaker and more duration-sensitive. Full-recording $d_z$ values for `diffusion_a_hat_frob` were $0.520$, $0.166$, and $0.332$ for GG--Rest, CC--Rest, and GG--CC; the corresponding fixed-prefix values were $0.445$, $0.272$, and $0.133$. The fixed-prefix diffusion-total and diffusion-norm rows attenuated similarly, while effective dimension remained method-limited. The complete 12-row L1 table and its separate fixed-prefix correction are provided in S2 and S3; no row was selected by significance.

#figure(kind: table, clean-table(
  columns: (1.25fr, 2.1fr, .55fr, .75fr, .8fr, .8fr),
  align: (left, left, center, center, center, center), inset: (x: 5pt, y: 3.5pt),
  table.header([*Contrast*], [*L1 metric*], [*$n$*], [*Full $d_z$*], [*400-s $d_z$*], [*400-s $q$*]),
  [GG -- Rest], [`diffusion_a_hat_frob`], [44], [0.520], [0.445], [0.00836],
  [GG -- Rest], [`diffusion_total`], [44], [0.551], [0.453], [0.00836],
  [GG -- Rest], [`diffusion_effective_dimension`], [44], [0.146], [0.0667], [0.759],
  [GG -- Rest], [`chart_drift_b_hat_norm`], [44], [1.82], [1.44], [2.02e-9],
  [CC -- Rest], [`diffusion_a_hat_frob`], [45], [0.166], [0.272], [0.219],
  [CC -- Rest], [`diffusion_total`], [45], [0.155], [0.266], [0.304],
  [CC -- Rest], [`diffusion_effective_dimension`], [45], [0.0218], [-0.0811], [0.732],
  [CC -- Rest], [`chart_drift_b_hat_norm`], [45], [0.505], [0.536], [0.00586],
  [GG -- CC], [`diffusion_a_hat_frob`], [44], [0.332], [0.133], [0.489],
  [GG -- CC], [`diffusion_total`], [44], [0.433], [0.162], [0.392],
  [GG -- CC], [`diffusion_effective_dimension`], [44], [0.182], [0.193], [0.380],
  [GG -- CC], [`chart_drift_b_hat_norm`], [44], [1.43], [0.947], [1.37e-6],
), caption: [Complete L1 hierarchy. Full $q$ values are in S2; the displayed 400-s $q$ values use the separate 12-row fixed-prefix sensitivity family.]) <tab-l1-main>

== R3: Chart-Jacobian and one-step alpha dissociate <sec:r3>

GG minus Rest increased chart-Jacobian alpha (median difference 0.01248, $d_z=1.42$, $n=44$, $p=1.56 times 10^-11$, $q=5.61 times 10^-10$). The identified one-step L3 generator-proxy spectral abscissa did not show a positive or FDR-significant counterpart ($d_z=-0.328$, $n=32$, $p=0.129$, global-36-test $q=0.178$). These are different complete-case subpopulations, not a formal test of a difference between operator effects; on the same 32 GG--Rest pairs, the chart-alpha contrast remains positive ($d_z=1.461$, median difference 0.01271, $p=3.26 times 10^-9$). CC minus Rest likewise increased chart-Jacobian alpha ($d_z=0.433$, $n=45$, $q=0.0167$), while the L3 proxy was uninformative on its smaller support ($d_z=-0.103$, $n=32$, $q=0.595$).

The fixed-prefix sensitivity retained all 134 recordings and the direction of every chart-alpha contrast. GG minus Rest remained positive (median difference 0.01450, $d_z=1.119$, $n=44$, $p=9.20 times 10^-9$, three-contrast $q=2.76 times 10^-8$); CC minus Rest was 0.00593 ($d_z=0.394$, $n=45$, $q=0.0124$), and GG minus CC was 0.00995 ($d_z=0.648$, $n=44$, $q=7.21 times 10^-5$). This supports robustness of the chart-alpha direction to equalized sampling support, not equivalence of full-recording and fixed-prefix estimands.

The separate standardized interaction test found a positive chart-versus-L3 difference for GG minus Rest (median interaction 1.888, $d_z=0.966$, $n=32$, Wilcoxon $p=6.79 times 10^-6$, three-test $q=2.04 times 10^-5$; sign-flip $p=1.0 times 10^-5$) and GG minus CC (median 1.229, $d_z=0.771$, $n=43$, $q=2.13 times 10^-5$). CC minus Rest was smaller and not FDR-significant (median 0.555, $d_z=0.327$, $n=32$, $q=0.0837$). This is a formal exploratory test of the declared standardized interaction estimand on common support; it does not make the raw chart and L3 units commensurate or establish estimator equivalence.

The common-support concordance analysis asks a complementary subject-level question: do people with a larger chart-alpha task contrast also have a larger L3-alpha task contrast? Spearman associations were negative for GG--Rest ($rho_s=-0.383$, $n=32$, $p=0.030$, bootstrap 95% CI [-0.683, -0.001]), CC--Rest ($rho_s=-0.251$, $n=32$, $p=0.166$, CI [-0.570, 0.099]), and GG--CC ($rho_s=-0.284$, $n=43$, $p=0.0646$, CI [-0.559, 0.041]). Same-direction signs occurred in only 12/32, 13/32, and 11/43 nonzero pairs, respectively. These are descriptive concordance quantities in estimator-specific robust-z units and are not a new inferential family.

#netn-box(title: [Primary dissociation])[
  The GG--Rest chart-Jacobian alpha result is not a one-step L3 result. The raw endpoint rows use distinct estimators and supports; a separate outcome-blind standardized interaction test on 32 common subjects was positive ($q=2.04 times 10^-5$). That interaction is normalization-dependent and exploratory, not a raw-unit effect-difference or estimator-equivalence test.
]

#figure(
  image("figures/results/ds004511_common_support_concordance_20260922.svg", width: 100%),
  caption: [Common-support subject-level concordance of standardized task contrasts. Each point is one complete subject pair; axes use the estimator-specific pooled robust-z calibration declared for the interaction analysis. The diagonal is a visual reference only. Negative or weak rank association and low same-sign agreement make the dissociation tangible without implying raw-unit commensurability.]
) <fig-estimator-concordance>

== R4: Identified-support rotation results <sec:r4>

On the 32 complete GG--Rest one-step pairs, GG decreased L2 `operator_rotation_rate` ($d_z=-1.10$, median difference -0.03589, $q=8.04 times 10^-6$) and L3 `one_step_generator_rotation_norm` ($d_z=-1.08$, median difference -0.05222, $q=8.04 times 10^-6$). These results are internally coherent within the identified subset, but they do not generalize automatically to the 13 recordings without lag-1 support.

#figure(kind: table, clean-table(
  columns: (2.25fr, .8fr, 1fr, 1fr, 1.15fr), align: (left, center, center, center, center), inset: 4pt,
  table.header([*GG minus Rest metric*], [*$n$*], [*$d_z$*], [*$p$*], [*BH $q$*]),
  [Chart-Jacobian alpha], [44], [1.42], [1.56e-11], [5.61e-10],
  [One-step L3 spectral abscissa], [32], [-0.328], [0.129], [0.178],
  [L2 rotation rate], [32], [-1.10], [6.91e-7], [8.04e-6],
  [L3 generator rotation norm], [32], [-1.08], [6.91e-7], [8.04e-6],
), caption: [Key exploratory GG--Rest contrasts. Jacobian alpha and L2/L3 rows belong to distinct endpoint families.]) <tab-key>

== R5: Reachability QC boundary <sec:r5>

Finite L4 amplitude summaries differ strongly in the exploratory panel, but their interpretation is bounded by the certificate construction, the three invalid records, and recording duration. Task-duration ranges do not overlap (Rest 480--596 s; CC 904--1324 s; GG 2396--4652 s), and within GG both L4 amplitude scalars correlate positively with duration (Spearman $rho approx 0.35$, uncorrected $p approx 0.02$). Because L4 is not available per window, this audit cannot remove the duration alternative; L4 contrasts are therefore not presented as duration-robust effects. In contrast, 109 of 131 finite `reach_d_eff` values were within $10^-6$ of 1 (median 1; maximum 1.31377). Its small-residual Wilcoxon rows are therefore not reported as capacity or dimension results.
The certificate-count figure is retained as a QC panel in S3 rather than treated as one of the main empirical figures. It documents the failure boundary but does not establish a task effect.

= Discussion <sec:discussion>

== Estimator dissociation rather than a unitary stability axis

On this fixed export, task contrasts dissociate across estimator classes. The complete L1 panel shows that local drift magnitude is the most stable task-sensitive quantity under the available fixed-duration check, while diffusion summaries are weaker and partly attenuated. The chart-Jacobian alpha contrast is strong and directionally robust, but it does not entail a positive one-step L3 alpha contrast. The identified subset instead shows reduced L2 and L3 rotation summaries. The common-support scatter adds a subject-level constraint: standardized chart and L3 task contrasts are weakly or negatively rank-concordant, with low same-sign agreement. Together these observations argue against treating one scalar as a generic readout of local flow, a fitted one-step generator, or future accessibility.

== Relation to neural-population and operator work

The result is consistent with a broader measurement distinction in neural-population analysis. Low-dimensional coordinates provide a useful state description, while the dynamical rule on that state requires additional identification and support assumptions @cunningham2014dimensionality @duncker2021dynamics. Population dynamics can express context-dependent computations and rotations, but those phenomena are tied to a declared representation and analysis protocol rather than to a universal scalar of stability @churchland2012neural @mante2013context. Data-driven operator methods make the same point from another direction: finite-dimensional approximations are measurement-dependent and need not recover one underlying law outside their qualified support @brunton2016extracting @brunton2022koopman.

The practical contribution is therefore modest but portable. Downstream studies should match the estimator to the scientific question and report support, qualification and missingness alongside the scalar. The NDT terminology provides the local measurement hierarchy used here; it does not license a latent neural-law interpretation by itself @langell2025ndt.

== Rest, active tasks and what the contrasts mean

Rest is a resting-state task label, whereas GG and CC are active task labels in this export. The contrasts bundle eye state, sensory input, arousal, motor and reporting demands, and recording duration with task identity. The local HDF5 task metadata does not encode an eye-state field, so we do not relabel Rest as eyes-closed in the present article. This is important because independent EEG work shows that eyes-closed and eyes-open resting conditions can differ broadly in spectral measures @barry2007eeg. The safe interpretation is consequently “GG versus the exported Rest condition” or “CC versus the exported Rest condition,” not a mechanistic claim about gambling, deception or cognitive control.

The GG--CC contrast is particularly useful because it avoids making Rest the only baseline: the chart-drift and chart-alpha effects remain positive, while the standardized chart-versus-L3 interaction is also positive and the common-support concordance is weak. This does not isolate a cognitive mechanism, but it shows that the estimator distinction is not reducible to one Rest comparison.

== Support, duration and the next gate

The analysis does not establish causal control, individual-level prediction, a consciousness measure, a biological mechanism, or a validated mapping from MNPS to a latent neural operator. Subject anchoring, one export, partial L2/L3 support, distinct BH families, task-duration imbalance, and the interaction's normalization choice constrain the claims. A bounded QC audit found that all 13 absent lag-1 maps failed the existing out-of-fold fidelity gate (`one_step_fit_not_better_than_baseline`), despite regular 4-s grids and 120--260 lag-1 pairs; they comprised 12 Rest, 1 CC, and 0 GG recordings. This diagnoses a reproducible support boundary rather than restoring a map or resolving selection bias.

An equal-duration/equal-lag-pair L2/L3 refit would be a valuable next gate, but it is not performed here: the current frozen export does not expose a validated 400-s L2/L3 refit path, and re-fitting would change the declared estimator contract. The fixed-prefix result therefore narrows the duration concern for chart-Jacobian and L1 drift summaries only; it does not validate L4 or the identified one-step estimators. Independent replication on a locked export with a declared multiplicity plan is required before a confirmatory task claim.

= Acknowledgements

We acknowledge the ds004511 contributors and OpenNeuro for public data sharing. Large language models assisted structured drafting and review; they are not authors and did not supply experimental observations.

#bibliography("references.bib", style: "apa")
