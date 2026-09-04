#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Supplementary Methods",
  short-title: "S1 Methods - hypoglycemia dynamics",
  subtitle: "Measurement contract, coordinate construction, and paired inference",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S1. Dataset and H5 measurement contract

The analysis used 68 H5 files representing 34 participants by two separately
excerpted conditions: euglycemia and hypoglycemia. Each H5 file contained 74
overlapping windows from an approximately five-minute EEG segment. The contract
included raw and robust-z EEG features, 3D MNPS, 9D coordinates, local 3D/9D
Jacobians, and subject- and cohort-anchored coordinate layers. It did not
include participant-level glucose, a shared time reference, recovery, regional
MNPS, anchor-state, anchor-quality, anchor-coupling, or block-window exports.

= S2. Preprocessing and epochs

The embedded ingest configuration specified 19-channel scalp EEG at 200 Hz,
1--45 Hz bandpass filtering, a 50 Hz notch filter, and average rereferencing.
Windows were 8 s with a 4 s step. The H5 provenance reported 300 s of measured
coverage and 296 s of effective window coverage per condition.

This preprocessing differs from the source article's 1--40 Hz filtering,
non-overlapping 4-s epochs, and artifact handling. The frozen ingest used no
ICA or amplitude-based artifact rejection. Seven channel identities (T5, T6,
P3, P4, Pz, O1, O2) were confirmed in the provenance; the remaining staged
labels used best-effort convention mapping. The present analysis therefore
does not claim exact replication of the source preprocessing or of
channel-specific physiology.

= S3. Coordinate layers

The 9D coordinate order was
$(m_a,m_e,m_o,d_n,d_l,d_s,e_e,e_s,e_m)$. The 3D export was a fixed weighted
projection of these three coordinate families. In the cohort-anchored layer,
feature centers and scales were fit from pooled euglycemia and hypoglycemia
rows. This makes between-condition coordinates comparable within the released
surface, but it does not make euglycemia an external or physiological zero.

Let $z_t$ be the 9D chart and $P$ its fixed projection. Then

$x_t = P z_t, quad x_t = (m_t,d_t,e_t).$

The projection is an analysis contract. It is not evidence that the three
coordinates are a unique ontology of neural state.

For this EEG-only export, $m_a$ and $m_e$ are mobility-family aggregates and
$m_o$ summarizes within-window spectral concentration. The deviation-family
coordinates $d_n$, $d_l$, and $d_s$ are exported network/local aggregates.
$e_e$ is the permutation-entropy coordinate and $e_s$ is the contract's
Hjorth-complexity slot. The $e_m$ coordinate is an energy/arousal-related high-frequency
EEG proxy used when peripheral physiological channels are unavailable; it is
not a direct embodied measure and is not an entropy estimator. The precise
upstream formulas and signs are versioned in the frozen H5 contract. The
contract applied an upper standardized-feature clip at 6.0, and the
hypoglycemia $e_m$ medians for `sub-004`, `sub-017`, and `sub-021` reached that
ceiling. These rows are therefore interpreted as bounded exported values.

= S4. Local flow and reachability

For a local linear approximation, the exported dynamics estimate a Jacobian
$J_t$ and a discrete transition operator $A_t$. Reachability was summarized
from

$Sigma_t^(h+1) = A_t Sigma_t^(h) A_t^T + Q_t,$

where $Q_t$ is a local residual covariance. We report tube log-determinant as
a volume proxy, effective dimension, condition number, directional entropy,
and a rotation proxy. These metrics describe local model-propagated geometry;
they do not establish actual state occupancy, controllability, cognitive
performance, or consciousness. In this run the reachability surface was
validity-limited for all participants: split-half sample count was 35 rather
than the required 50, and split-half effective-dimension correlation was
approximately 0.04 rather than the required 0.5. Reachability results are
therefore exploratory audit outputs, not confirmatory endpoints.

= S5. Primary paired inference

All analyses used participant summaries. For the engine-level analysis,
euglycemia was passed as the left condition and hypoglycemia as the right
condition because the implementation reports `right - left`. The contrast is
therefore HYPO minus EU throughout the manuscript and tables.

The engine used 5,000 paired permutations, bootstrap confidence intervals, and
Benjamini--Hochberg false-discovery-rate correction within contrast and analysis
type. Engine-level q-values include all exported summaries in each analysis
block, including means, medians, standard deviations, and auxiliary metrics;
the S2 tables reproduce selected median rows. One unavailable 9D Jacobian
reduced the exported reachability sample to 33 pairs, without making that
surface valid for confirmatory inference.

= S6. Robustness protocol

The article-local robustness script performed a 10,000-draw paired label-swap
null on 11 prespecified 9D and reachability medians. Each draw independently
multiplied every participant's HYPO minus EU difference by plus or minus one;
the two-sided Monte Carlo probability compared the observed mean difference to
the absolute null distribution. This is the appropriate label permutation for
the paired two-condition design.

The script additionally read H5 geometry-contract provenance and excluded the
three hypoglycemia sessions marked `adjusted`: `sub-004`, `sub-017`, and
`sub-021`. Its fixed 11-endpoint panel contains six 9D coordinate medians
($m_a$, $m_e$, $d_l$, $d_n$, $e_e$, and $e_m$) and five reachability medians;
$m_o$ and $d_s$ are not part of that robustness panel. It reports whether the
direction of each endpoint is preserved. It does not rerun FDR-corrected
restricted-sample inference, so this sensitivity is directional rather than a
replacement primary test.

= S7. Feature-level sanity checks

Median raw values were extracted for delta, theta, alpha, sample entropy,
permutation entropy, and Hjorth complexity. Paired Wilcoxon tests
@wilcoxon1945individual and six-feature Benjamini--Hochberg correction were
used for this secondary check. The exported sample- and permutation-entropy
fields were identical for this H5 release; their separate table rows are
therefore not independent replications.

#bibliography("references.bib", style: "apa")
