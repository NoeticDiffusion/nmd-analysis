// S2 Supplementary Data — RichSleep_EAP_v2
// Full result tables underlying manuscript.typ R1-R5. All values are read
// directly from the frozen CSVs cited in each caption; nothing here is
// re-derived.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "S2 Data - RichSleep_EAP_v2",
  subtitle: "Complete cross-carrier phase-locking tables, per-subject Rayleigh summary, both onset-hazard tests, and the full qe-interaction and SO-coupled-descriptive families",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S2.0 Complete cross-carrier pooled family (10 tests, main text R2)

#figure(
  kind: table,
  clean-table(
    columns: (1.15fr, 0.65fr, 0.65fr, 0.7fr, 0.7fr, 0.7fr, 0.75fr, 0.75fr, 0.65fr, 0.65fr),
    align: (left, left, center, center, center, center, center, center, center, center),
    inset: 3.5pt,
    table.header([*Carrier*], [*Ch.*], [*$N$*], [*$R_1$*], [*$R_2$*], [*$T_2$*], [*perm $p$ ($R_1$)*], [*perm $p$ ($T_2$)*], [*FDR $q$ ($R_1$)*], [*FDR $q$ ($T_2$)*]),
    [N2-spindle onset], [cardiac], [23,029], [0.00927], [0.01508], [0.00031], [0.3533], [0.0815], [0.4417], [0.1018],
    [N2-spindle onset], [resp], [23,029], [0.01895], [0.02102], [0.00080], [0.1514], [0.0265], [0.2163], [0.0378],
    [N2-spindle peak], [cardiac], [23,029], [0.01593], [0.02005], [0.00066], [0.0200], [0.0015], [0.0333], [0.0025],
    [N2-spindle peak], [resp], [23,029], [0.04530], [0.01083], [0.00217], [0.0005], [0.0005], [0.0010], [0.0010],
    [N3-SO trough], [cardiac], [42,009], [0.06446], [0.01044], [0.00426], [0.0005], [0.0005], [0.0010], [0.0010],
    [N3-SO trough], [resp], [42,009], [0.05347], [0.01757], [0.00317], [0.0005], [0.0005], [0.0010], [0.0010],
    [N3-SO upstate], [cardiac], [42,009], [0.06258], [0.00763], [0.00397], [0.0005], [0.0005], [0.0010], [0.0010],
    [N3-SO upstate], [resp], [42,009], [0.05036], [0.00791], [0.00260], [0.0005], [0.0005], [0.0010], [0.0010],
    [REM-theta], [cardiac], [2,412], [0.01938], [0.02714], [0.00111], [0.4508], [0.3233], [0.4508], [0.3423],
    [REM-theta], [resp], [2,412], [0.02250], [0.02892], [0.00134], [0.4348], [0.3423], [0.4508], [0.3423],
  ),
  caption: [Complete cross-carrier pooled subject-rotation permutation family, both harmonic statistics ($n_"perm"=2000$), BH-FDR jointly across all 10 rows within each statistic. Source: `03_multistage_phase_locking.py`, `phase_locking_pooled.csv`.]
) <tab-pooled-full>

= S2.1 Second-order (subject-mean) Rayleigh test, complete family

#figure(
  kind: table,
  clean-table(
    columns: (1.15fr, 0.65fr, 0.65fr, 0.95fr, 0.8fr, 0.85fr, 0.75fr),
    align: (left, left, center, center, center, center, center),
    inset: 3.5pt,
    table.header([*Carrier*], [*Ch.*], [*$N$ subj.*], [*Mean angle*], [*$R$*], [*Rayleigh $p$*], [*FDR $q$*]),
    [N2-spindle onset], [cardiac], [24], [$-85.6 degree$], [0.2729], [0.1682], [0.1869],
    [N2-spindle onset], [resp], [24], [$-131.4 degree$], [0.4029], [0.0187], [0.0267],
    [N2-spindle peak], [cardiac], [24], [$+28.3 degree$], [0.4622], [0.00492], [0.00820],
    [N2-spindle peak], [resp], [24], [$-127.7 degree$], [0.6649], [$6.81 times 10^(-6)$], [$1.70 times 10^(-5)$],
    [N3-SO trough], [cardiac], [24], [$+1.6 degree$], [0.6538], [$1.07 times 10^(-5)$], [$2.15 times 10^(-5)$],
    [N3-SO trough], [resp], [24], [$-82.8 degree$], [0.7539], [$2.47 times 10^(-7)$], [$2.47 times 10^(-6)$],
    [N3-SO upstate], [cardiac], [24], [$-166.4 degree$], [0.6687], [$5.84 times 10^(-6)$], [$1.70 times 10^(-5)$],
    [N3-SO upstate], [resp], [24], [$-85.3 degree$], [0.7077], [$1.18 times 10^(-6)$], [$5.88 times 10^(-6)$],
    [REM-theta], [cardiac], [23], [$+37.4 degree$], [0.3693], [0.0417], [0.0521],
    [REM-theta], [resp], [23], [$-178.2 degree$], [0.2412], [0.2649], [0.2649],
  ),
  caption: [Second-order Rayleigh test on the 24 (23 for REM-theta, one subject excluded for $<5$ epochs) subject-mean directions, BH-FDR jointly across all 10 rows. Both channels' $mu_("resp,peak")$/N2-spindle-peak rows are consistent with `S1.4`'s $mu_("resp,peak")=-128.4 degree$. Source: `03_multistage_phase_locking.py`, `phase_locking_second_order.csv`.]
) <tab-secondorder-full>

= S2.2 Per-subject Rayleigh test summary (all 5 carriers $times$ 2 channels)

#figure(
  kind: table,
  clean-table(
    columns: (1.15fr, 0.65fr, 0.85fr, 1fr, 1.1fr, 0.7fr, 0.9fr),
    align: (left, left, center, center, center, center, center),
    inset: 4pt,
    table.header([*Carrier*], [*Ch.*], [*Median $R$*], [*Median $N$/subj.*], [*Range $N$/subj.*], [*$N$ subj.*], [*$N$ FDR-sig.*]),
    [N2-spindle onset], [cardiac], [0.0465], [1,030], [161-2,562], [24], [0/24],
    [N2-spindle onset], [resp], [0.0611], [1,030], [161-2,562], [24], [7/24],
    [N2-spindle peak], [cardiac], [0.0364], [1,030], [161-2,562], [24], [1/24],
    [N2-spindle peak], [resp], [0.0708], [1,030], [161-2,562], [24], [8/24],
    [N3-SO trough], [cardiac], [0.0788], [1,713], [448-3,725], [24], [16/24],
    [N3-SO trough], [resp], [0.0441], [1,713], [448-3,725], [24], [9/24],
    [N3-SO upstate], [cardiac], [0.0875], [1,713], [448-3,725], [24], [17/24],
    [N3-SO upstate], [resp], [0.0440], [1,713], [448-3,725], [24], [9/24],
    [REM-theta], [cardiac], [0.1067], [84], [2-219], [24], [0/24],
    [REM-theta], [resp], [0.1156], [84], [2-219], [24], [1/24],
  ),
  caption: [Per-subject Rayleigh test (Zar 1999 approximation), summarized across subjects; full 237-row per-subject table (subject ID, $N$, mean angle, $R$, $p$, FDR $q$) in `phase_locking_per_subject.csv`. N2-onset/peak numbers reproduce the companion article's own S2.2 table (median $R$ 0.046/0.061/0.036/0.071 there vs. 0.0465/0.0611/0.0364/0.0708 here - rounding only). N3-SO shows the highest per-subject FDR-survivor rate of any carrier (16-17/24), consistent with S2.0/S2.1's ranking. Source: `03_multistage_phase_locking.py`, `phase_locking_per_subject.csv`.]
) <tab-persubject-full>

= S2.3 Onset-hazard tests, full detail (main text R3)

#figure(
  kind: table,
  clean-table(
    columns: (0.7fr, 0.75fr, 0.75fr, 0.75fr, 0.75fr, 0.75fr, 0.7fr, 0.9fr, 0.7fr),
    align: (left, center, center, center, center, center, center, center, center),
    inset: 3.5pt,
    table.header([*Ch.*], [*$N$ cases*], [*$N$ ctrl.*], [*$b_"cos"$*], [*$b_"sin"$*], [*$p_"cos"$*], [*$p_"sin"$*], [*Wald $chi^2(2)$*], [*Wald $p$*]),
    [cardiac], [23,029], [66,827], [0.0112], [$-0.0177$], [0.348], [0.207], [1.94], [0.379],
    [resp], [23,029], [66,827], [$-0.0217$], [0.0755], [0.227], [$5.68 times 10^(-8)$], [29.48], [$3.96 times 10^(-7)$],
  ),
  caption: [Test A: case-control logistic regression, `is_case ~ cos(phase) + sin(phase)`, cluster-robust SE by subject (`S1.3`). BH-FDR $q$ (2-test family): cardiac 0.379, resp $7.92 times 10^(-7)$. Implied preferred phase: cardiac $-57.8 degree$ (ns), resp $+106.1 degree$. Source: `04_spindle_onset_hazard_model.py`, `case_control_logit.csv`.]
) <tab-testA>

#figure(
  kind: table,
  clean-table(
    columns: (0.7fr, 0.8fr, 0.85fr, 0.85fr, 0.85fr, 1fr, 1fr, 0.75fr),
    align: (left, center, center, center, center, center, center, center),
    inset: 3.5pt,
    table.header([*Ch.*], [*$N$*], [*obs $R_1$*], [*obs $T_2$*], [*null $R_1$ mean*], [*null $T_2$ 95%*], [*perm $p$ ($R_1$)*], [*perm $p$ ($T_2$)*]),
    [cardiac], [23,029], [0.01035], [0.00034], [0.00572], [0.00021], [0.0758], [0.00399],
    [resp], [23,029], [0.02145], [0.00085], [0.04154], [0.00287], [1.000], [1.000],
  ),
  caption: [Test B: circular time-shift surrogate ($n_"perm"=500$, `S1.3`). BH-FDR $q$ (2-test family, $T_2$): cardiac 0.00798, resp 1.000. Note the *resp* null mean $R_1$ (0.0415) exceeds the observed $R_1$ (0.0215) - the surrogate itself has higher baseline dispersion for respiration than cardiac, a property of the shifted-stream construction, not of the real data; see main text R3 for the histogram-based corroboration check that resolves which of Test A/B's disagreeing channel-specific findings is more likely genuine. Source: `04_spindle_onset_hazard_model.py`, `circular_time_shift_surrogate.csv`.]
) <tab-testB>

#figure(
  clean-table(
    columns: (1.6fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center),
    inset: 4.5pt,
    table.header([*Null construction*], [*Cardiac $p$*], [*Resp $p$*], [*Construction principle*]),
    [Null 0: subject-rotation permutation], [0.0815], [0.0265], [Parametric: uniform rotation of discrete event phases],
    [Test A: case-control logit vs. `non_event_risk_v1`], [0.379], [$3.96 times 10^(-7)$], [Exposure-grounded: real N2 non-event timepoints as controls],
    [Test B: circular time-shift surrogate], [0.0040], [1.000], [Exposure-grounded: shifted continuous physiological stream],
  ),
  caption: [Cross-null summary, all three onset-phase-locking tests side by side (main text Table `tab-hazard`, reproduced here with the construction-principle column). Source: `04_spindle_onset_hazard_model.py`, `cross_null_convergence.csv`.]
) <tab-crossnull>

= S2.4 Complete qe-interaction family, all three operationalizations (54 tests total, main text R4)

#figure(
  kind: table,
  clean-table(
    columns: (0.85fr, 0.5fr, 0.5fr, 0.75fr, 0.75fr, 0.75fr, 0.7fr, 0.7fr),
    align: (left, center, center, center, center, center, center, center),
    inset: 3.5pt,
    table.header([*Delta mode*], [*Endp.*], [*$N$*], [*align. $p$*], [*qe $p$*], [*interaction coef*], [*int. $p$*], [*FDR $q$*]),
    [event_control], [`m`], [172], [0.726], [0.879], [$+0.081$], [0.135], [0.834],
    [event_control], [`d`], [172], [0.082], [0.263], [$+0.024$], [0.730], [0.876],
    [event_control], [`e`], [172], [0.326], [0.845], [$+0.024$], [0.642], [0.865],
    [event_control], [`d_n`], [172], [0.080], [0.341], [$+0.038$], [0.785], [0.883],
    [event_control], [`d_l`], [172], [0.115], [0.521], [$+0.008$], [0.898], [0.939],
    [event_control], [`d_s`], [172], [0.765], [0.187], [$+0.064$], [0.440], [0.865],
    [event_control], [`e_e`], [172], [0.632], [0.303], [$+0.006$], [0.939], [0.939],
    [event_control], [`e_s`], [172], [0.277], [0.155], [$+0.050$], [0.585], [0.865],
    [event_control], [`e_m`], [172], [0.577], [0.478], [$+0.082$], [0.344], [0.834],
    [event_prefar], [`m`], [160], [0.924], [0.886], [$+0.035$], [0.651], [0.865],
    [event_prefar], [`d`], [160], [0.023], [0.199], [$-0.147$], [0.279], [0.834],
    [event_prefar], [`e`], [160], [0.107], [0.501], [$-0.067$], [0.330], [0.834],
    [event_prefar], [`d_n`], [160], [0.096], [0.256], [$-0.329$], [0.292], [0.834],
    [event_prefar], [`d_l`], [160], [0.0030], [0.389], [$-0.049$], [0.516], [0.865],
    [event_prefar], [`d_s`], [160], [0.302], [0.550], [$-0.112$], [0.371], [0.834],
    [event_prefar], [`e_e`], [160], [0.345], [0.150], [$+0.044$], [0.353], [0.834],
    [event_prefar], [`e_s`], [160], [0.140], [0.226], [$-0.221$], [0.249], [0.834],
    [event_prefar], [`e_m`], [160], [0.173], [0.353], [$-0.048$], [0.673], [0.865],
  ),
  caption: [Primary family: $"qe" = log(1+"sigma_power_z_n2")$. No interaction term survives BH-FDR (min $q=0.834$). `align. $p$`/`qe $p$` are the model's main-effect $p$-values (not FDR-corrected, not the primary question of this family - see main text R4 for the `d`/`d_l` main-effect comparison against the companion article). Source: `05_qe_interaction_moderation.py`, `qe_interaction_primary_sigma_log.csv`.]
) <tab-qe-primary-full>

#figure(
  kind: table,
  clean-table(
    columns: (0.9fr, 0.55fr, 0.55fr, 0.9fr, 0.75fr, 0.75fr),
    align: (left, center, center, center, center, center),
    inset: 4pt,
    table.header([*Delta mode*], [*Endp.*], [*$N$*], [*interaction coef*], [*int. $p$*], [*FDR $q$*]),
    [event_control], [`m`], [172], [$-0.004$], [0.983], [0.988],
    [event_control], [`d`], [172], [$+0.010$], [0.952], [0.988],
    [event_control], [`e`], [172], [$+0.034$], [0.823], [0.988],
    [event_control], [`d_n`], [172], [$+0.032$], [0.878], [0.988],
    [event_control], [`d_l`], [172], [$+0.019$], [0.916], [0.988],
    [event_control], [`d_s`], [172], [$-0.366$], [0.134], [0.988],
    [event_control], [`e_e`], [172], [$+0.203$], [0.305], [0.988],
    [event_control], [`e_s`], [172], [$-0.085$], [0.679], [0.988],
    [event_control], [`e_m`], [172], [$-0.041$], [0.852], [0.988],
    [event_prefar], [`m`], [160], [$-0.145$], [0.425], [0.988],
    [event_prefar], [`d`], [160], [$-0.104$], [0.492], [0.988],
    [event_prefar], [`e`], [160], [$-0.031$], [0.707], [0.988],
    [event_prefar], [`d_n`], [160], [$+0.055$], [0.854], [0.988],
    [event_prefar], [`d_l`], [160], [$-0.220$], [0.307], [0.988],
    [event_prefar], [`d_s`], [160], [$-0.050$], [0.820], [0.988],
    [event_prefar], [`e_e`], [160], [$-0.052$], [0.653], [0.988],
    [event_prefar], [`e_s`], [160], [$+0.003$], [0.988], [0.988],
    [event_prefar], [`e_m`], [160], [$-0.125$], [0.605], [0.988],
  ),
  caption: [Robustness family: $"qe" = log(1+"amplitude")$. No interaction term survives BH-FDR (min $q=0.988$). Source: `05_qe_interaction_moderation.py`, `qe_interaction_robust_amplitude_log.csv`.]
) <tab-qe-amp-full>

#figure(
  kind: table,
  clean-table(
    columns: (0.9fr, 0.55fr, 0.55fr, 0.95fr, 0.75fr, 0.75fr),
    align: (left, center, center, center, center, center),
    inset: 4pt,
    table.header([*Delta mode*], [*Endp.*], [*$N$*], [*interaction coef*], [*int. $p$*], [*FDR $q$*]),
    [event_control], [`m`], [172], [$+0.0017$], [0.252], [0.725],
    [event_control], [`d`], [172], [$-0.0013$], [0.344], [0.725],
    [event_control], [`e`], [172], [$-0.0009$], [0.384], [0.725],
    [event_control], [`d_n`], [172], [$-0.0017$], [0.507], [0.725],
    [event_control], [`d_l`], [172], [$-0.0011$], [0.434], [0.725],
    [event_control], [`d_s`], [172], [$-0.0001$], [0.942], [0.942],
    [event_control], [`e_e`], [172], [$-0.0003$], [0.793], [0.840],
    [event_control], [`e_s`], [172], [$-0.0012$], [0.487], [0.725],
    [event_control], [`e_m`], [172], [$+0.0007$], [0.767], [0.840],
    [event_prefar], [`m`], [160], [$+0.0006$], [0.695], [0.834],
    [event_prefar], [`d`], [160], [$-0.0025$], [0.243], [0.725],
    [event_prefar], [`e`], [160], [$-0.0007$], [0.589], [0.757],
    [event_prefar], [`d_n`], [160], [$-0.0052$], [0.354], [0.725],
    [event_prefar], [`d_l`], [160], [$-0.0013$], [0.276], [0.725],
    [event_prefar], [`d_s`], [160], [$-0.0016$], [0.524], [0.725],
    [event_prefar], [`e_e`], [160], [$+0.0012$], [0.189], [0.725],
    [event_prefar], [`e_s`], [160], [$-0.0034$], [0.312], [0.725],
    [event_prefar], [`e_m`], [160], [$-0.0012$], [0.463], [0.725],
  ),
  caption: [Robustness family: $"qe" = $ untransformed `sigma_power_z_n2`. No interaction term survives BH-FDR (min $q=0.725$). Source: `05_qe_interaction_moderation.py`, `qe_interaction_robust_sigma_raw.csv`.]
) <tab-qe-raw-full>

= S2.5 SO-coupled descriptive-only correlations (exploratory, main text R5)

#figure(
  kind: table,
  clean-table(
    columns: (0.9fr, 0.55fr, 0.6fr, 0.7fr, 1.1fr, 1.1fr),
    align: (left, center, center, center, center, center),
    inset: 4pt,
    table.header([*Delta mode*], [*Endp.*], [*$N$ ev.*], [*$N$ subj.*], [*$r$(delta, coupling score)*], [*$r$(delta, SO amplitude)*]),
    [event_control], [`m`], [21], [14], [0.147], [$-0.275$],
    [event_control], [`d`], [21], [14], [0.070], [0.356],
    [event_control], [`e`], [21], [14], [0.174], [0.272],
    [event_control], [`d_n`], [21], [14], [0.207], [0.432],
    [event_control], [`d_l`], [21], [14], [$-0.165$], [$-0.062$],
    [event_control], [`d_s`], [21], [14], [$-0.046$], [0.384],
    [event_control], [`e_e`], [21], [14], [0.152], [$-0.290$],
    [event_control], [`e_s`], [21], [14], [0.087], [0.443],
    [event_control], [`e_m`], [21], [14], [0.135], [$-0.038$],
    [event_prefar], [`m`], [19], [13], [0.114], [$-0.171$],
    [event_prefar], [`d`], [19], [13], [$-0.031$], [0.175],
    [event_prefar], [`e`], [19], [13], [0.004], [0.133],
    [event_prefar], [`d_n`], [19], [13], [$-0.092$], [0.361],
    [event_prefar], [`d_l`], [19], [13], [$-0.017$], [$-0.009$],
    [event_prefar], [`d_s`], [19], [13], [0.007], [0.110],
    [event_prefar], [`e_e`], [19], [13], [0.040], [$-0.069$],
    [event_prefar], [`e_s`], [19], [13], [$-0.016$], [0.178],
    [event_prefar], [`e_m`], [19], [13], [0.138], [$-0.106$],
  ),
  caption: [Descriptive Pearson correlations only (no model, no FDR family, explicitly non-confirmatory - `S1.5` part 4). Signs and magnitudes are inconsistent across endpoints (range $-0.29$ to $+0.44$), with no discernible pattern. $N$ is lower than the SO-coupled subset's total (25 events/15 subjects) because each row additionally requires the relevant `delta` and covariate columns to be non-missing (the same per-mode attrition pattern as `S2.4`'s 172/160). Source: `05_qe_interaction_moderation.py`, `so_coupled_descriptive_exploratory.csv`.]
) <tab-so-descriptive>

= S2.6 Held-out population-preferred peak phase (self-contained recomputation)

#figure(
  kind: table,
  clean-table(
    columns: (1.4fr, 1fr, 0.9fr, 0.9fr, 1.1fr),
    align: (left, center, center, center, center),
    inset: 4.5pt,
    table.header([*$mu_("resp,peak")$*], [*$R$ (2nd-order)*], [*$N$ subj.*], [*$N$ held-out events*], [*$N$ excluded (geom.-valid)*]),
    [$-128.4 degree$ ($-2.2404$ rad)], [0.6657], [24], [22,839], [190],
  ),
  caption: [Recomputed on this article's own `phase_resolved_v3` catalog (`S1.4`); numerically identical to the companion article's own S2.6 estimate, as expected from the bit-identity guarantee (`S1.0`) between `phase_resolved_v3` and `event_phase_v2` on all shared columns. Source: `05_qe_interaction_moderation.py` console output (deterministic given fixed input data; not separately written to CSV).]
) <tab-mu-held-out>

#bibliography("references.bib", style: "apa")
