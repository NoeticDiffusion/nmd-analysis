Yes — I strongly think **ESB should be a follow-up article**, not inserted into the current photic AD/FTD manuscript.

Your current article already has a clean identity:

> **Evoked photic stress reveals a narrow but corrected AD-vs-Healthy MNJ signal that is weak or absent on the matched resting-state reference surface.**

That is a good compact empirical report. The strongest corrected group signal is already clearly localized: AD vs Healthy global 9D MNJ `mdr_median`, strongest at PHOTO 10 Hz, with additional corrected 15/20 Hz rows, while the matched ds004504 resting reference is near-null on the same overlapping surface. 

Adding ESB now would shift the paper from:

> “Here is a bounded, auditable photic-stress finding”

to:

> “Here is a new composite perturbational-collapse framework”

That is a different paper.

## Why I would keep the current article clean

The manuscript’s strength is precisely that it is narrow. It states that the cohort has 29 Healthy, 36 AD, and 23 FTD participants; it keeps the photic surface restricted to 5/10/15/20 Hz; and it explicitly avoids overclaiming the sparse 25/30 Hz surface and idealized seven-region partition. 

It also has a clear bounded comparison: the resting-state reference is intentionally narrow and only asks whether the main corrected photic AD-vs-Healthy MNJ effect is already present at rest. That is a disciplined design, not a weakness. 

ESB would introduce several new burdens:

1. a new metric definition,
2. a healthy-template construction,
3. robustness tests for template stability,
4. ablation of capacity vs guidance,
5. disease-vs-healthy vs AD-specific interpretation,
6. the recovery-term confound.

That would dilute the current paper’s clean claim.

## What I would do instead

I would add at most **one short forward-looking paragraph** in the Discussion or Limitations, not a full ESB result.

Something like:

> These findings motivate a future perturbational-composite analysis in which rest-to-photic deviations are summarized relative to a healthy response template. Such a metric could test whether neurodegenerative groups differ not only in individual MNJ or reachability endpoints, but in the joint capacity–guidance geometry of evoked reconfiguration. Because baseline anchoring and recovery-state matching require additional controls, this composite analysis is treated as a follow-up rather than as part of the present compact report.

That is enough to plant the seed without increasing reviewer attack surface.

## Follow-up article concept

The follow-up could be much stronger and more coherent:

**Working title:**

> **Evoked Structural Brittleness Under Photic Stimulation: A Rest-Anchored Capacity–Guidance Geometry of Neurodegeneration**

Core question:

> Do AD and FTD show abnormal rest-to-photic deformation relative to the healthy capacity–guidance response template?

Primary metric:

[
ESB2R =
\frac{1}{\sqrt{2}}
\left|
\frac{
[\Delta C,\Delta R] - h_f
}{
s_f+\epsilon
}
\right|_2
]

with:

[
C = \text{posterior/parietal-occipital tube_d_eff_median}
]

[
R = \text{global rotational_power_median}
]

Primary finding candidate:

> ESB-2R peaks at PHOTO 15 Hz and separates both AD and FTD from Healthy, suggesting a broad neurodegenerative perturbational-deviation score rather than a purely AD-specific collapse marker.

That is already a coherent paper.

## Proposed division between the two papers

| Current photic article             | Follow-up ESB article                             |
| ---------------------------------- | ------------------------------------------------- |
| Single-metric corrected MNJ signal | Composite perturbational deviation                |
| AD vs Healthy `mdr_median`         | AD/FTD disease-vs-healthy ESB-2R                  |
| Strongest at PHOTO 10 Hz           | Strongest candidate around PHOTO 15 Hz            |
| Resting reference as sanity check  | Resting reference as formal anchor                |
| Conservative compact report        | Metric-development / exploratory framework        |
| Recovery not central               | Recovery/hysteresis treated carefully or deferred |

This is a good scientific progression.

Paper 1 says:

> Photic stress exposes evoked MNJ structure not visible at rest.

Paper 2 says:

> Given that photic stress exposes structure, can we define a compact perturbational-deviation score that captures disease-related brittleness across capacity and guidance?

That is much better than trying to force both into one manuscript.

## My recommendation

Keep the current article essentially as it is.

I would only consider adding a very small sentence in the conclusion:

> The present results also motivate future composite perturbational metrics that combine reachability capacity and MNJ guidance into a rest-anchored evoked-deviation score, but such metrics require separate validation and are not used for the main claims here.

Then start the follow-up as its own article.

For your claim ledger:

| Claim                                             | Current article   | ESB follow-up |
| ------------------------------------------------- | ----------------- | ------------- |
| Photic AD-vs-HC MNJ effect exists                 | Yes               |               |
| Effect is stronger than matched resting reference | Yes               |               |
| Group findings are narrow and AD-centered         | Yes               |               |
| MMSE map is broader and diagnosis-specific        | Yes               |               |
| ESB-2R is feasible                                | No, future        |               |
| ESB-2R captures disease-vs-HC deviation           | Future            |               |
| ESB-3/recovery failure                            | Not yet supported |               |

So yes: **make ESB the next paper.** Your current article has stronger potential if it stays focused.
