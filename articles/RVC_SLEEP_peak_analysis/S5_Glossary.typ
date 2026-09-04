// S5 Glossary — RVC_SLEEP_peak_analysis

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S5 Glossary",
  short-title: "S5 Glossary - RVC_SLEEP_peak_analysis",
  subtitle: "Terms specific to this article, plus carried-over NDT/RVC/EAP terms used throughout",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= S5.0 Terms new to this article

#figure(
  clean-table(
    columns: (1.3fr, 3fr),
    align: (left, left),
    inset: 5pt,
    table.header([*Term*], [*Definition*]),
    [Onset-phase vs. peak-phase], [Two distinct reference points within a detected spindle event at which cardiac/respiratory phase can be measured: `onset_sec` (event start, used by the companion RVC_SLEEP article's Mal B) vs. `peak_sec` (the time of maximum amplitude within the event, the reference point this article shows carries the population-level coupling).],
    [Event-timing pathway], [The hypothesis that body phase helps determine *when* an endogenous RVC event (or a specific feature of it, e.g. its amplitude peak) occurs - operationalized here as non-uniformity of event phase relative to the cardiac/respiratory cycle (R2-R5).],
    [Event-efficacy pathway], [The logically separate hypothesis that, given an event has occurred, the body's phase at that moment changes *how strongly* the event reconfigures state-space geometry - operationalized here as the alignment-moderation test (R6).],
    [Subject-rotation permutation null], [A Monte Carlo null distribution constructed by adding one i.i.d. $"Uniform"(0,2pi)$ rotation per subject to all of that subject's phases, repeated $n_"perm"$ times; destroys any common population-level preferred phase while exactly preserving each subject's event count and within-subject clustering. Replaces an earlier, retracted subject-label-shuffle proposal that left the pooled statistic invariant.],
    [Harmonic statistic ($R_1$, $R_2$, $T_2$)], [$R_1$: first-harmonic mean resultant length (classical Rayleigh concentration). $R_2$: second-harmonic mean resultant length (sensitive to axial/bimodal structure). $T_2 = R_1^2+R_2^2$: an omnibus statistic combining both, used throughout this article's permutation tests.],
    [Duration-tercile stratification], [Splitting events into three equal-sized groups by duration (short/mid/long) and re-running a test independently within each group, to check whether an effect is duration-general or concentrated in a duration subrange (e.g. a tail artifact).],
    [Leave-one-subject-out (LOSO) jackknife], [Re-running a population-level test 24 times, once per dropped subject, to check that no single subject's data disproportionately drives the pooled result.],
    [Deterministic split-half replication], [Splitting subjects into two fixed, non-overlapping halves (here: alphabetically first 12 vs. last 12) and re-running a test independently in each half - the strongest single check here for whether an effect is population-general.],
    [Held-out estimation], [Estimating a population parameter (here, $mu_("resp,peak")$) on a data subset that excludes the events subsequently used to test a hypothesis involving that parameter, to avoid circularity/data leakage.],
    [(Peak-phase) alignment], [$"alignment"_e = cos(phi_e - mu)$ for a given event $e$'s phase $phi_e$ and a reference (population-preferred) phase $mu$: $+1$ when $e$'s phase exactly matches $mu$, $-1$ when diametrically opposite, used as a continuous moderator in R6's regression.],
    [Alignment moderation], [Testing whether an event's alignment (above) to a population-preferred phase predicts the size of a separate, downstream outcome for that same event (here, the spindle-locked geometry delta) - distinct from testing whether phase itself is non-uniformly distributed (a timing test).],
    [Geometry-optimal phase], [In the secondary circular-regression check (S1.5, S2.5), the phase direction $"atan2"("sin_coef","cos_coef")$ implied by a free two-coefficient fit as maximizing the fitted geometry delta - compared against the independently-estimated timing-preferred phase $mu_("resp,peak")$, not assumed to coincide with it a priori.],
  ),
  caption: [Terms introduced or newly operationalized in this article.]
) <tab-glossary-new>

= S5.1 Carried-over NDT/RVC/EAP terms

#figure(
  clean-table(
    columns: (1.3fr, 3fr),
    align: (left, left),
    inset: 5pt,
    table.header([*Term*], [*Definition*]),
    [Noetic Diffusion Theory (NDT)], [The parent geometric framework for neural state dynamics within which RVC and EAP are formulated (@langell2025ndt); not itself tested by this article.],
    [Rhythmic Variance Control (RVC)], [The Tier-1 NDT mechanism under which endogenous, rhythm-defined events (e.g. sleep spindles) are treated as candidate transient gating-precision-change windows.],
    [Embodied Anchoring Principle (EAP)], [The Tier-2 NDT extension proposing that peripheral bodily rhythms (cardiac, respiratory) can additionally condition the same latent landscape RVC events act on; this article's R6 is a test relevant to (but not dispositive of) this principle in its event-efficacy form.],
    [`d`, `d_n`, `d_l`, `d_s`, `e`, `e_e`, `e_s`, `e_m`, `m`], [The 9 primary geometry endpoints inherited from the companion RVC_SLEEP article's `coords_9d` state-space representation; not redefined here (see companion article's `S1`/`S5` for full definitions).],
    [`event_control` vs. `event_prefar` delta mode], [Two ways of computing a geometry "delta" for a given event: `event_control` = event value minus a matched control-window median; `event_prefar` = event value minus the same event's own pre-spindle baseline window ("far") value - both inherited unchanged from the companion article's Mal C machinery.],
    [WLS-cluster (fit_wls_cluster)], [Weighted least squares with weights $1"/"n_"events,subject"$ (equalizing each subject's total contribution regardless of event count) and cluster-robust standard errors by subject; the shared regression machinery for all moderation tests in both this article and its companion.],
    [BH-FDR], [Benjamini-Hochberg false discovery rate correction (@benjamini1995fdr), applied within each pre-specified test family (4-test primary onset family, S1.3; 18-test alignment-moderation family, S1.5) but not across families, matching the companion article's own convention.],
  ),
  caption: [Terms inherited from the companion RVC_SLEEP article and the broader NDT framework, retained here without modification unless otherwise noted.]
) <tab-glossary-carried>

#bibliography("references.bib", style: "apa")
