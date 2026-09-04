#import "../psychosis_first_time_geometric_trajectory/network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S2 Supplementary Data",
  short-title: "Block-Jacobian Coupling Supplementary Data",
  subtitle: "Full contrast tables, coupling pattern summaries, and cross-dataset comparisons",
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

This supplement collects the data-heavy material moved out of the main manuscript:

- group compositions and data coverage,
- full block Jacobian contrast tables for ds003944,
- selected block Jacobian contrast results for ds003947,
- the $e → e$ gradient summary across all contrasts,
- and a cross-dataset coupling pattern comparison.

= Group composition

#figure(
  kind: table,
  table(
    columns: (1.1fr, 1.35fr, 0.65fr, 0.9fr, 0.9fr, 1.0fr, 0.9fr),
    align: left,
    inset: 5pt,
    table.header(
      [*Dataset*],
      [*Group*],
      [*N*],
      [*Age mean*],
      [*Age SD*],
      [*Female n (%)*],
      [*CPZ median*],
    ),
    [ds003944], [Healthy], [32], [21.61], [3.97], [12 (37.5%)], [--],
    [ds003944], [FEP unmedicated], [19], [22.33], [4.21], [5 (26.3%)], [`0 / n.a.`],
    [ds003944], [FEP medicated], [31], [22.34], [5.41], [11 (35.5%)], [`227.3`],
    [ds003947], [Healthy], [30], [24.20], [5.13], [14 (46.7%)], [--],
    [ds003947], [FEP unmedicated], [8], [25.01], [5.06], [2 (25.0%)], [`0 / n.a.`],
    [ds003947], [FEP medicated], [23], [22.82], [4.57], [7 (30.4%)], [`303.0`],
  ),
  caption: [Group composition. Identical to companion static-geometry and trajectory-geometry studies; medication groups use the same `CPZ_at_scan` split.]
) <tab-s2-groups>

= ds003944: Primary $e → e$ gradient

#figure(
  kind: table,
  table(
    columns: (1.6fr, 1.7fr, 0.55fr, 0.55fr, 0.45fr, 0.45fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Contrast*],
      [*Feature*],
      [*$d$*],
      [*$p$*],
      [*$n_a$*],
      [*$n_b$*],
      [*Status*],
    ),
    [FEP unmedicated vs Healthy], [`e->e block_frobenius_mean`], [-0.573], [0.026], [19], [32], [`p<0.05`],
    [FEP medicated vs Healthy], [`e->e block_frobenius_mean`], [+0.091], [0.650], [31], [32], [`ns`],
    [FEP medicated vs FEP unmedicated], [`e->e block_frobenius_mean`], [+0.705], [0.020], [31], [19], [`p<0.05`],
    [],[], [], [], [], [], [],
    [FEP unmedicated vs Healthy], [`e->e block_trace_mean`], [-0.432], [0.073], [19], [32], [`p<0.1`],
    [FEP medicated vs Healthy], [`e->e block_trace_mean`], [+0.562], [0.048], [31], [32], [`p<0.05`],
    [FEP medicated vs FEP unmedicated], [`e->e block_trace_mean`], [+0.691], [0.023], [31], [19], [`p<0.05`],
    [],[], [], [], [], [], [],
    [FEP unmedicated vs Healthy], [`e->e block_anisotropy_mean`], [-0.280], [0.218], [19], [32], [`ns`],
    [FEP medicated vs Healthy], [`e->e block_anisotropy_mean`], [+0.192], [0.367], [31], [32], [`ns`],
    [FEP medicated vs FEP unmedicated], [`e->e block_anisotropy_mean`], [+0.517], [0.009], [31], [19], [`p<0.05`],
  ),
  caption: [Complete $e → e$ diagonal block results for `ds003944`. The Frobenius norm and trace both show the monotonic gradient (unmedicated < healthy < medicated). The anisotropy result (FEP medicated vs unmedicated, $d = +0.517$, $p = 0.009$) indicates that the entropy sub-system's self-coupling is more directional/anisotropic in medicated FEP. Full BH-FDR $q$ values are in `results/block_jacobian_contrasts_20260607/ds003944_block_jacobian_contrasts.csv`.]
) <tab-s2-44-ee>

= ds003944: Cross-family coupling

#figure(
  kind: table,
  table(
    columns: (1.6fr, 1.7fr, 0.55fr, 0.55fr, 0.45fr, 0.45fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Contrast*],
      [*Feature*],
      [*$d$*],
      [*$p$*],
      [*$n_a$*],
      [*$n_b$*],
      [*Status*],
    ),
    [FEP medicated vs Healthy], [`m->e block_frobenius_mean`], [+0.631], [0.040], [31], [32], [`p<0.05`],
    [FEP unmedicated vs Healthy], [`m->e block_frobenius_mean`], [+0.091], [0.675], [19], [32], [`ns`],
    [FEP medicated vs FEP unmedicated], [`m->e block_frobenius_mean`], [+0.398], [0.100], [31], [19], [`p<0.1`],
    [],[], [], [], [], [], [],
    [FEP medicated vs FEP unmedicated], [`d->e c_rot_mean`], [+0.637], [0.048], [31], [19], [`p<0.05`],
    [FEP medicated vs FEP unmedicated], [`e->d c_rot_mean`], [+0.637], [0.048], [31], [19], [`p<0.05`],
    [FEP medicated vs Healthy], [`d->e c_rot_mean`], [+0.312], [0.144], [31], [32], [`ns`],
    [FEP unmedicated vs Healthy], [`d->e c_rot_mean`], [-0.197], [0.437], [19], [32], [`ns`],
  ),
  caption: [Cross-family coupling results for `ds003944`. The $m → e$ Frobenius elevation in medicated FEP vs healthy controls ($d = +0.631$, $p = 0.040$) reflects stronger metastability-to-entropy coupling. The $d ↔ e$ rotational coupling elevation in medicated vs unmedicated ($d = +0.637$, $p = 0.048$) reflects increased directed asymmetry. Note that $c_{"rot"}$ for $d→e$ and $e→d$ are numerically identical by construction.]
) <tab-s2-44-cross>

= ds003944: Diagonal blocks overview

#figure(
  kind: table,
  table(
    columns: (1.6fr, 1.5fr, 0.55fr, 0.55fr, 0.45fr, 0.45fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Contrast*],
      [*Feature*],
      [*$d$*],
      [*$p$*],
      [*$n_a$*],
      [*$n_b$*],
      [*Status*],
    ),
    [FEP unmedicated vs Healthy], [`m->m block_frobenius_mean`], [-0.188], [0.441], [19], [32], [`ns`],
    [FEP medicated vs Healthy], [`m->m block_frobenius_mean`], [+0.149], [0.517], [31], [32], [`ns`],
    [FEP medicated vs FEP unmedicated], [`m->m block_frobenius_mean`], [+0.314], [0.196], [31], [19], [`ns`],
    [],[], [], [], [], [], [],
    [FEP unmedicated vs Healthy], [`d->d block_frobenius_mean`], [-0.270], [0.287], [19], [32], [`ns`],
    [FEP medicated vs Healthy], [`d->d block_frobenius_mean`], [+0.085], [0.715], [31], [32], [`ns`],
    [FEP medicated vs FEP unmedicated], [`d->d block_frobenius_mean`], [+0.317], [0.203], [31], [19], [`ns`],
  ),
  caption: [Diagonal blocks $m → m$ and $d → d$ for `ds003944`. Neither self-coupling family shows significant group differences in this dataset; the primary self-coupling signal is confined to $e → e$. This specificity supports the claim that the entropic self-regulation deficit is the key feature rather than a global coupling reduction.]
) <tab-s2-44-diag>

= ds003947: Selected results

#figure(
  kind: table,
  table(
    columns: (1.6fr, 1.7fr, 0.55fr, 0.55fr, 0.45fr, 0.45fr, 0.9fr),
    align: left,
    inset: 4pt,
    table.header(
      [*Contrast*],
      [*Feature*],
      [*$d$*],
      [*$p$*],
      [*$n_a$*],
      [*$n_b$*],
      [*Status*],
    ),
    [FEP unmedicated vs Healthy], [`d->d block_trace_mean`], [-0.926], [0.041], [8], [30], [`p<0.05`],
    [FEP medicated vs Healthy], [`d->d block_trace_mean`], [-0.219], [0.296], [23], [30], [`ns`],
    [FEP medicated vs FEP unmedicated], [`d->d block_trace_mean`], [+0.532], [0.112], [23], [8], [`ns`],
    [],[], [], [], [], [], [],
    [FEP unmedicated vs Healthy], [`e->e block_frobenius_mean`], [-0.284], [0.352], [8], [30], [`ns`],
    [FEP medicated vs Healthy], [`e->e block_frobenius_mean`], [+0.178], [0.394], [23], [30], [`ns`],
    [FEP medicated vs FEP unmedicated], [`e->e block_frobenius_mean`], [+0.412], [0.218], [23], [8], [`ns`],
  ),
  caption: [`ds003947` block Jacobian results. The clearest signal is reduced $d → d$ trace in unmedicated FEP vs healthy controls ($d = -0.926$, $p = 0.041$), despite limited power ($n = 8$). The $e → e$ pattern is directionally consistent with `ds003944` (unmedicated < healthy in Frobenius norm) but does not reach significance. Full table in `results/block_jacobian_contrasts_20260607/ds003947_block_jacobian_contrasts.csv`.]
) <tab-s2-47>

= Cross-dataset directional comparison

#figure(
  kind: table,
  table(
    columns: (1.5fr, 1.0fr, 0.8fr, 0.8fr, 1.6fr),
    align: left,
    inset: 5pt,
    table.header(
      [*Feature*],
      [*ds003944 unmed vs HC*],
      [*ds003947 unmed vs HC*],
      [*Consistent?*],
      [*Comment*],
    ),
    [`e->e block_frobenius_mean`], [$d = -0.573$, $p=0.026$], [$d = -0.284$, $p=0.352$], [Yes], [Both negative; ds003947 ns, power-limited],
    [`d->d block_frobenius_mean`], [$d = -0.270$, $p=0.287$], [$d = -0.926$, $p=0.041$], [Yes], [Both negative; ds003944 ns, ds003947 significant],
    [`m->m block_frobenius_mean`], [$d = -0.188$, $p=0.441$], [$d = -0.106$, $p=0.763$], [Yes], [Both negative, both ns],
    [`e->e block_frobenius_mean` (med vs unmed)], [$d = +0.705$, $p=0.020$], [$d = +0.412$, $p=0.218$], [Yes], [Both positive; ds003947 trend only],
  ),
  caption: [Cross-dataset directional consistency for key diagonal blocks. The "reduced self-regulation in unmedicated FEP" theme is consistent across datasets, though the most significant family differs: $e → e$ in ds003944, $d → d$ in ds003947. This may reflect true cohort heterogeneity, small $n$ in ds003947, or cross-family redundancy in the self-regulation deficit.]
) <tab-s2-cross>

= Files

The tables in this supplement are backed by the article-local outputs under `articles/CLINICAL/psychosis_first_time_block_jacobian/results/block_jacobian_contrasts_20260607/`:

- `ds003944_block_jacobian_contrasts.csv` — full contrast table for ds003944
- `ds003947_block_jacobian_contrasts.csv` — full contrast table for ds003947
- `combined_block_jacobian_contrasts.csv` — merged table from both datasets

Note: The analysis script (`run_psychosis_block_jacobian_contrasts.py`) resides in `articles/CLINICAL/psychosis_first_time_geometric_trajectory/src/` from the trajectory companion study; a symlink or copy should be placed in `articles/CLINICAL/psychosis_first_time_block_jacobian/src/` for self-contained reproducibility.

#bibliography("../psychosis_first_time_geometric_trajectory/psychosis.bib", style: "apa")
