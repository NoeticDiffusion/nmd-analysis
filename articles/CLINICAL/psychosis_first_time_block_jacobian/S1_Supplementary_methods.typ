#import "../psychosis_first_time_geometric_trajectory/network_neuroscience_template.typ": *

#show: netn-template.with(
  title: "S1 Supplementary Methods",
  short-title: "Block-Jacobian Coupling Supplementary Methods",
  subtitle: "Block Jacobian formulation, sub-block derivation, and coupling decomposition",
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

This supplement expands the methods section of the main manuscript. It covers:

1. the 9D MNPS family structure and the block partitioning of the Jacobian,
2. the per-window and per-subject metric derivation,
3. the coupling decomposition into symmetric and rotational components,
4. the statistical design and BH-FDR application,
5. and known limitations of the current implementation.

= The 9D MNPS family structure

NeuralManifoldDynamics 2.1 projects EEG features into a 9-dimensional Meta-Noetic Phase Space (MNPS). The nine coordinates are organised into three functional families of three coordinates each:

- *Metastability family* ($m$): $m_a, m_e, m_o$ — coordinates associated with the metastability dimension across arousal, engagement, and orienting sub-systems.
- *Diffusivity family* ($d$): $d_a, d_e, d_o$ — coordinates associated with temporal diffusivity or spreading of neural activity.
- *Entropy family* ($e$): $e_a, e_e, e_o$ — coordinates associated with local entropy or distributional complexity of neural states.

The coordinate ordering in the 9D vector is $bold(z)_t = (m_a, m_e, m_o, d_a, d_e, d_o, e_a, e_e, e_o)^T$.

= Block partitioning of the Jacobian

The local linear dynamics of the 9D trajectory at window $t$ are summarised by the $9 × 9$ Jacobian $hat(J)_t$, estimated by NMD from the observed coordinate transitions. The Jacobian is partitioned into nine $3 × 3$ sub-blocks by the family structure:

$
hat(J)_t = mat(
  J_t^{m m}, J_t^{m d}, J_t^{m e};
  J_t^{d m}, J_t^{d d}, J_t^{d e};
  J_t^{e m}, J_t^{e d}, J_t^{e e}
)
$

The notation convention is $J_t^{AB}$ for the block in row family $A$ and column family $B$: it captures the instantaneous influence of family $B$'s state on the rate of change of family $A$'s state. For example:

- $J_t^{e e}$ (diagonal) — how strongly the entropy sub-system drives its own future dynamics.
- $J_t^{m e}$ (off-diagonal) — how strongly the entropy sub-system drives the rate of change of the metastability sub-system.
- $J_t^{e m}$ (off-diagonal) — how strongly the metastability sub-system drives the entropy sub-system.

== Sub-block summary metrics

For each sub-block $B = J_t^{AB}$, the following scalar summaries are computed:

*Block trace* (diagonal blocks only):
$
"block_trace" = "tr"(B) = sum_{i=1}^{3} B_{ii}.
$
Positive trace indicates net self-amplification (expanding dynamics); negative trace indicates net self-damping (contracting dynamics). The mean over analysis windows is reported as `block_trace_mean`.

*Block Frobenius norm* (all blocks):
$
"block_frobenius" = ||B||_F = sqrt(sum_{i,j} B_{ij}^2).
$
This captures total coupling magnitude, regardless of sign or direction. For diagonal blocks, it reflects self-coupling strength. For off-diagonal blocks, it reflects cross-family coupling strength. The mean over windows is `block_frobenius_mean`.

*Block anisotropy* (all blocks):
$
"block_anisotropy" = frac(sigma_1 - sigma_3, sigma_1 + sigma_3 + epsilon),
$
where $sigma_1 geq sigma_2 geq sigma_3 geq 0$ are the singular values of $B$. Anisotropy near 1 indicates that coupling is dominated by a single direction; anisotropy near 0 indicates isotropic, equally distributed coupling. The mean over windows is `block_anisotropy_mean`.

= Coupling decomposition: symmetric and rotational components

For any off-diagonal block $B = J_t^{AB}$ (with $A != B$), the coupling has a reciprocal (symmetric) and a directed (antisymmetric) component:

$
C_S = frac(B + B^T, 2), quad C_R = frac(B - B^T, 2).
$

The *symmetric coupling* $c_{"sym"} = ||C_S||_F$ captures the mutual, reciprocal part: how much families $A$ and $B$ influence each other in a balanced way. When $c_{"sym"}$ is large, both families are co-regulated.

The *rotational coupling* $c_{"rot"} = ||C_R||_F$ captures the directed, asymmetric part: how much the relationship between $A$ and $B$ is non-reciprocal. A large $c_{"rot"}$ means one family systematically leads or drives the other in an unbalanced way. For the pair ($d$, $e$), elevated `c_rot_mean` in medicated FEP (as found in the main results) indicates that the $d$-to-$e$ and $e$-to-$d$ relationships are more asymmetric — that one of the families is driving the other in a systematic, directional manner.

Note that the `c_rot_mean` values for the two complementary blocks ($d → e$ and $e → d$) are numerically identical by construction, since $C_R^{AB} = -(C_R^{BA})$ and $||C_R^{AB}||_F = ||C_R^{BA}||_F$.

= Per-subject aggregation

All sub-block metrics are computed at each analysis window $t$. The subject-level summary is the mean over windows:

$
text("block_frobenius_mean") = frac(1, T) sum_{t=1}^{T} ||J_t^{AB}||_F,
$

and analogously for trace, anisotropy, $c_{"sym"}$, and $c_{"rot"}$. This mean summarises the average coupling structure across the resting-state recording.

The per-window values are available in the NMD H5 export under `block_jacobians/values` (if exported); the present analysis uses only the pre-aggregated subject-level CSV (`stratified_block_jacobians_subjects_*.csv`) provided by the NMD pipeline.

= Statistical design

All contrasts use Mann-Whitney U (two-sided). Cohen's $d$ is computed as

$
d = frac(bar(x)_A - bar(x)_B, s_{"pooled"}},
$

where $bar(x)_A$ and $bar(x)_B$ are group means and $s_{"pooled"}$ is the pooled SD. The sign convention is that positive $d$ indicates the first-named group has a higher value (e.g., `FEP medicated vs FEP unmedicated` gives positive $d$ when medicated exceeds unmedicated).

BH-FDR is applied within each {dataset × contrast label} family. This means correction is applied over the set of all block-pair × metric combinations tested within one contrast, yielding $q$ values that control the false discovery rate within that contrast. No manuscript-wide correction is applied.

The test matrix per contrast is:
- 3 diagonal blocks × 3 metrics (trace, Frobenius, anisotropy) = 9 diagonal tests
- 6 off-diagonal blocks × 3 metrics (Frobenius, $c_{"sym"}$, $c_{"rot"}$) = 18 off-diagonal tests
- Total: 27 tests per contrast, 81 tests per dataset

= Implementation

The article-local analysis script is `articles/CLINICAL/psychosis_first_time_block_jacobian/src/run_psychosis_block_jacobian_contrasts.py`. It:

1. reads the `stratified_block_jacobians_subjects_*.csv` CSV for each dataset,
2. reads medication group assignments from the corresponding H5 files,
3. pivots the long-format CSV to wide format (one row per subject, one column per block_pair × metric),
4. runs Mann-Whitney U and Cohen's $d$ for each of the three contrasts,
5. applies BH-FDR within each contrast, and
6. writes the results to `results/block_jacobian_contrasts_20260607/`.

The script uses `h5py`, `numpy`, `pandas`, and `scipy` only; no NDT-core dependencies beyond what is available in a standard scientific Python environment.

= Known limitations

*Cross-sectional confounding.* The medicated vs unmedicated comparison is cross-sectional; subjects were not randomised to medication. Between-group differences in coupling structure could reflect pre-medication differences, selection into treatment, illness severity, or specific medication type rather than direct pharmacological effects.

*Medication heterogeneity.* The medicated group includes subjects on different antipsychotic agents with different receptor profiles. The block Jacobian contrasts collapse across this heterogeneity. A dose-response analysis within the medicated group (e.g., correlating coupling strength with CPZ equivalent dose) would provide more specific evidence.

*Aggregation over time.* By using per-window means, the analysis discards temporal information about how coupling structure evolves within a recording. If coupling patterns are non-stationary (e.g., bursts of $m → e$ coupling), the mean may obscure the relevant signal. Variance or entropy of per-window coupling metrics would be an alternative summary.

*Upstream NMD sensitivity.* The block Jacobian depends on the NMD fitting procedure, including the choice of manifold dimensionality, embedding, and Jacobian estimation method. Changes to any of these would change the block structure. The current analysis inherits the NMD 2.1 defaults without sensitivity testing.

*Small unmedicated group in ds003947.* The `ds003947` unmedicated group ($n = 8$) has limited power for block Jacobian contrasts. The $d → d$ trace finding ($d = -0.926$, $p = 0.041$) in this cohort should be treated with particular caution.

#bibliography("../psychosis_first_time_geometric_trajectory/psychosis.bib", style: "apa")
