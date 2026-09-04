#import "template_eLife.typ": *

#show: netn-template.with(
  title: "Supplementary Data",
  short-title: "S2 Data - hypoglycemia dynamics",
  subtitle: "Selected complete paired contrasts and feature-level sanity checks",
  authors: ((name: "Robin Langell", affil: 1),),
  affiliations: ("Langell Konsult AB, Vallentuna, Sweden",),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S2. Data files

Machine-readable full results are retained in
`results/hypoglycemia_t1d_20260723/ndt_paired_contrast_results.csv`, with
feature checks in `raw_eeg_feature_paired_results.csv`. Tables below reproduce
the prespecified medians used in the main text. Effects are HYPO minus EU.

= S2.1 Coarse and stratified coordinates

#figure(
  kind: table,
  clean-table(
    columns: (2fr, 0.8fr, 0.8fr, 0.8fr, 0.8fr),
    align: (left, center, center, center, center),
    inset: 4pt,
    table.header([*Metric*], [*N*], [*Delta*], [*p*], [*q*]),
    [$m$ median], [34], [-0.7429], [0.0002], [0.00090],
    [$d$ median], [34], [0.0278], [0.8592], [0.9640],
    [$e$ median], [34], [-0.2440], [0.0332], [0.0747],
    [$m_a$ median], [34], [-1.0956], [0.0002], [0.0018],
    [$m_e$ median], [34], [-0.6848], [0.0004], [0.0018],
    [$m_o$ median], [34], [-0.3578], [0.0924], [0.1330],
    [$d_n$ median], [34], [1.0135], [0.0008], [0.0031],
    [$d_l$ median], [34], [-0.4404], [0.0310], [0.0598],
    [$d_s$ median], [34], [-0.3110], [0.2022], [0.2274],
    [$e_e$ median], [34], [-0.7084], [0.0176], [0.0396],
    [$e_s$ median], [34], [0.3226], [0.1194], [0.1612],
    [$e_m$ median], [34], [1.0242], [0.0016], [0.0048],
  ),
  caption: [Paired coordinate medians from the engine-level contrast table. Engine-level q-values include all exported summaries within each analysis block, not only the median rows shown here.]
)

= S2.2 Local flow and reachability

#figure(
  kind: table,
  clean-table(
    columns: (2.3fr, 0.8fr, 0.9fr, 0.8fr, 0.8fr),
    align: (left, center, center, center, center),
    inset: 4pt,
    table.header([*Metric*], [*N*], [*Delta*], [*p*], [*q*]),
    [3D Jacobian Frobenius median], [34], [-0.00968], [0.2452], [0.6654],
    [3D Jacobian rotation median], [34], [-0.00526], [0.4277], [0.6947],
    [3D Jacobian trace median], [34], [-0.00971], [0.0378], [0.6654],
    [9D Jacobian operator norm median], [33], [-0.1283], [0.0042], [0.0342],
    [9D Jacobian Frobenius median], [33], [-0.1297], [0.0054], [0.0342],
    [9D Jacobian rotation median], [33], [-0.0903], [0.0052], [0.0342],
    [Tube effective dimension median], [33], [0.2512], [0.0124], [0.1343],
    [Tube directional entropy median], [33], [0.0881], [0.0298], [0.1534],
    [Tube condition number median], [33], [-2871.5], [0.0602], [0.1698],
    [Tube log-volume median], [33], [0.3950], [0.2454], [0.5367],
    [Tube rotation median], [33], [0.00437], [0.8324], [0.9171],
  ),
  caption: [Local-flow and reachability medians. The 9D Jacobian rows are exploratory. Reachability outputs were validity-limited under the frozen split-half criteria and are not confirmatory endpoints.]
)

= S2.3 Secondary raw EEG feature checks

#figure(
  kind: table,
  clean-table(
    columns: (2fr, 0.8fr, 0.9fr, 0.8fr, 0.8fr),
    align: (left, center, center, center, center),
    inset: 4pt,
    table.header([*Feature*], [*N*], [*Delta*], [*p*], [*q*]),
    [Theta power], [34], [0.1297], [0.0000022], [0.000013],
    [Delta power], [34], [0.1025], [0.000029], [0.000086],
    [Alpha power], [34], [0.1693], [0.00433], [0.00865],
    [Sample entropy], [34], [-0.0280], [0.0358], [0.0430],
    [Permutation entropy], [34], [-0.0280], [0.0358], [0.0430],
    [Hjorth complexity], [34], [0.0846], [0.1682], [0.1682],
  ),
  caption: [Secondary raw-feature checks. The exported sample and permutation entropy fields are identical in this release.]
)

#bibliography("references.bib", style: "apa")
