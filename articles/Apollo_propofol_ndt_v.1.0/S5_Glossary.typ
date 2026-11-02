// S5 Glossary — Apollo propofol occupancy.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S5 - Glossary",
  short-title: "Glossary - Apollo propofol occupancy",
  subtitle: "Terminology used in the occupancy secondary analysis",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  keywords: ("glossary", "NDT", "occupancy", "propofol", "LOR", "matched state"),
  article-type: "Supplementary Material",
  abstract: [
    Terminology for the Apollo propofol occupancy article. Entries distinguish (1) *Implemented*
    — the exact computation; (2) *Interpretation* — the most defensible empirical reading;
    (3) *Not established* — theoretical mappings not directly confirmed here.
  ],
)

#set heading(numbering: none)

= A - D

*Baseline-fixed chart* - *Implemented*: eight `features_raw` columns robust-$z$ scored with
that participant's pre-drug median and MAD. *Interpretation*: a within-person reference that
can see occupancy. *Not established*: identification of a latent neural manifold.

*Caliper* - Median baseline leave-one-out nearest-neighbour Euclidean distance in the
baseline-fixed chart; greedy matches farther than the caliper are rejected.

*Common support* - Overlap between later-phase and baseline clouds that permits matching.
Collapse of common support is why C3 is NOT_TESTABLE here.

*$d_z$* - Paired Cohen's $d$: mean of within-subject differences divided by their sample SD.

= E - L

*Eligibility* - Finite occupancy features and observed $Delta t in [3.8, 4.2]$ s on a one-step
source window.

*First / later protocol sedation* - `datainfo` orders 2 and 3 (mild / moderate in the source
paper). Later protocol sedation is not LOR.

*G0–G4* - Preregistration gates: inventory, labels, support, independent code review, lock.
G0–G2 closed; G3/G4 not completed. All tests exploratory.

*LOR / ROR* - Loss / return of behavioural responsiveness from the Chennu binomial-CI rule on
$k\/40$, occupancy-blind. Not consciousness.

= M - R

*Matched state (NDT-C3 analogue)* - Increment speed/spread compared after pairing later and
baseline windows at similar $z$. *Implemented* here with greedy Euclidean matching. *Not
established*: a change in the latent future law.

*MNPS* - Exported three-dimensional neural-manifold coordinate. Occupancy does not use it as
the primary state.

*NDT-C1 / C3* - Present-state geometry versus conditional future law at matched state
@langell2025ndt.

*Occupancy* - Median $norm(z)_2$ of eligible unmatched windows in the baseline-fixed chart.
*Interpretation*: relocation away from the awake neighbourhood. *Not established*: anaesthetic
depth or unconsciousness.

*Protocol phase* - Cambridge `datainfo` column 2: baseline, first sedation, later sedation,
recovery. Not inferred from file order.

= S - Z

*Sign test* - Exact two-sided binomial test on the sign of non-zero paired differences.

*Subject-anchored (export)* - Recording-local MNPS scaling in the HDF5 bundle; ComBat disabled.
Distinct from the article-side baseline-fixed occupancy frame.

*Unresponsive (package alias)* - Legacy name for protocol order 3. Not used as LOR.

#bibliography("references.bib", style: "apa")
