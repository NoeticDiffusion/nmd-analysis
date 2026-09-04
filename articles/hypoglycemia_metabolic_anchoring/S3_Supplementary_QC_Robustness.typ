#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Supplementary Quality Control and Robustness",
  short-title: "S3 QC - hypoglycemia dynamics",
  subtitle: "Coverage, paired label-swap null, and adjusted-geometry sensitivity",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S3.1 Coverage and contract QC

The H5 run manifest recorded 68 source files, no bad files, finite 3D
coordinates for all files, finite 9D coordinates for all files, 3D Jacobians
for all files, and 9D Jacobians for 67 files. All files contained 74 windows.
The primary coordinate analyses therefore used 34 pairs; the reachability
surface used 33 pairs. The absence of regional, time-reference, event, and
embodied-anchor surfaces precluded those analyses. In addition, the
reachability surface was validity-limited for all participants: its frozen
split-half criteria required $n >= 50$ and $rho >= 0.5$, whereas the exported
effective-dimension summary had $n = 35$ and median $rho approx 0.04$. The
reachability rows below are consequently an exploratory audit, not a valid
confirmatory test.

#figure(
  kind: table,
  clean-table(
    columns: (2.4fr, 1fr, 1fr, 1.2fr),
    align: (left, center, center, center),
    inset: 4pt,
    table.header([*Contract layer*], [*EU files*], [*HYPO files*], [*Status*]),
    [3D coordinates], [34], [34], [Available],
    [9D coordinates], [34], [34], [Available],
    [3D Jacobian], [34], [34], [Available],
    [9D Jacobian], [34], [33], [One unavailable HYPO file],
    [Regional MNPS], [0], [0], [Not exported],
    [Embodied anchors], [0], [0], [Not exported],
  ),
  caption: [H5 capability audit from the run manifest.]
)

= S3.2 Paired label-swap null

The robustness script independently swapped euglycemia/hypoglycemia labels
within each participant for 10,000 draws. It evaluated 11 prespecified
stratified-coordinate and reachability endpoints: six coordinate medians
($m_a$, $m_e$, $d_l$, $d_n$, $e_e$, and $e_m$) and five reachability medians.
$m_o$ and $d_s$ were not included in this robustness panel. This restricted
family is a supplementary robustness test and is distinct from the broader
engine-level FDR families reported in the main manuscript.

#figure(
  kind: table,
  clean-table(
    columns: (2.3fr, 0.8fr, 0.9fr, 0.9fr),
    align: (left, center, center, center),
    inset: 4pt,
    table.header([*Endpoint*], [*N*], [*Null p*], [*Null q*]),
    [$m_a$ median], [34], [0.00010], [0.0011],
    [$m_e$ median], [34], [0.00030], [0.0015],
    [$d_l$ median], [34], [0.0300], [0.0412],
    [$d_n$ median], [34], [0.00040], [0.0015],
    [$e_e$ median], [34], [0.0172], [0.0315],
    [$e_m$ median], [34], [0.0018], [0.0050],
    [Tube effective dimension], [33], [0.0147], [0.0315],
    [Tube directional entropy], [33], [0.0282], [0.0413],
    [Tube log-volume], [33], [0.2409], [0.2650],
    [Tube condition number], [33], [0.0637], [0.0778],
    [Tube rotation], [33], [0.8354], [0.8354],
  ),
  caption: [Two-sided paired label-swap null across the fixed 11-endpoint robustness panel. Full output is in `paired_label_swap_null.csv`.]
)

= S3.3 Adjusted-geometry sensitivity

Three hypoglycemia files were marked `adjusted` by their embedded geometry
contract: `sub-004`, `sub-017`, and `sub-021`. The last participant also
accounts for the unavailable 9D-Jacobian/reachability pairing. The retained
9D-Jacobian windows were 24/72 for `sub-004`, 70/72 for `sub-017`, and 0/72
for `sub-021`. The engine nevertheless exported reachability summaries for
the first two adjusted files; because the reachability surface failed its
split-half criteria globally, those summaries remain exploratory. Excluding
these participants preserved the sign of all 11 prespecified endpoints.

#figure(
  kind: table,
  clean-table(
    columns: (2.3fr, 1fr, 1fr, 1fr),
    align: (left, center, center, center),
    inset: 4pt,
    table.header([*Endpoint*], [*Full delta*], [*Sensitivity delta*], [*Sign preserved*]),
    [$m_a$ median], [-1.096], [-1.043], [Yes],
    [$m_e$ median], [-0.685], [-0.639], [Yes],
    [$d_l$ median], [-0.440], [-0.503], [Yes],
    [$d_n$ median], [1.014], [0.862], [Yes],
    [$e_e$ median], [-0.708], [-0.812], [Yes],
    [$e_m$ median], [1.024], [0.708], [Yes],
    [Tube effective dimension], [0.251], [0.237], [Yes],
    [Tube directional entropy], [0.088], [0.080], [Yes],
    [Tube log-volume], [0.395], [0.450], [Yes],
    [Tube condition number], [-2871.509], [-3010.731], [Yes],
    [Tube rotation], [0.00437], [0.00174], [Yes],
  ),
  caption: [Directional sensitivity excluding the three adjusted-geometry hypoglycemia sessions. This is not a re-estimated restricted-sample significance test.]
)

= S3.4 Reviewer-facing robustness summary

#netn-box(title: [Robustness summary])[
  The paired condition association is supported by complete coordinate coverage,
  a paired label-swap null, and preservation of direction after removing the
  three adjusted-geometry hypoglycemia files. Reachability is validity-limited
  and cannot support a confirmatory collapse or expansion claim. The analysis
  does not resolve the pooled-anchor limitation and cannot test glucose dose,
  recovery, awareness, regional anatomy, or embodied-anchor mechanisms.
]

#bibliography("references.bib", style: "apa")
