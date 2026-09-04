// S3 Supplementary QC / robustness — NDT claim ledger and required negatives.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary QC and Robustness",
  short-title: "S3 Ledger - NDT",
  subtitle: "Required negatives, development-gate status, and what would count as robustness",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

= Intent

This supplement holds claim-ledger detail that does not belong in the
main theoretical article: closed gates, failed estimator qualifications, and
the distinction between synthetic operator existence and biological
identification. It is an audit trail, not a second results section.

= Required negatives (do not rehabilitate)

The following paths stay closed under current assumptions. A later redesign
must say so explicitly; it must not be narrated as a pass.

1. Two-dimensional finite-sample committor recovery is closed. Committor is
   promoted as a *question*, not as an NMD export.
2. Instantaneous Jacobian recovery does not license ordered finite-time
   propagation or empirical $alpha$/$omega$ via current NMD ingest.
3. Periodic and event-triggered replay/write gates do not beat matched-energy
   or shuffled-timing controls.
4. Calibrated residual covariance is not memory-specific or target-private
   reachability.
5. DANDI 000458 EEG-only local-linear operator identification fails
   (residual-variance fraction $0.856$).
6. Repertoire-gate and prestimulus-controlled shape claims on a separate
   optogenetic resource are closed.
7. A HELS-A neighbourhood robustness extension is not a pass. HELS-A1
   fabricated-estimator qualification for a state-matched hippocampal
   incremental test has not passed family false-positive control.
8. An IBL stimulus-side population decoder can pass a pilot positive-control
   test while a predefined single-trial discrete chart-transition operator
   fails its held-out residual floor (median residual fraction $approx 1.001$).
   Failure of that readout is not a neural-information null.
9. A three-stage meso $->$ regional $->$ surface-macro prediction chain on
   DANDI 000458 is blocked: event alignment remains inconclusive and the
   parent feature table is not region- or unit-resolved. The parent claim-class-1
   associations are neither promoted nor demoted by that gate.
10. A joint TRN $->$ mesoscopic $->$ surface-macro causal bridge is not
    estimable from the audited public archives. DANDI 000458 has meso and
    surface EEG without a usable TRN perturbation; the companion Figshare
    resource has timed TRN perturbation without surface EEG. Pooling the two
    does not identify the missing chain.
11. Condition mixing can inflate the innovation term of a local-linear
    predictive-spread fit. In a companion Allen analysis, pooling expected and
    omission epochs increased $op("Tr")(Q)$ in all $126$ examined
    session $times$ region combinations, typically several-fold. Residual
    degrees of freedom were $1$ throughout those six-epoch fits of $A$, $Q$,
    and $Sigma^((h))$. Condition-separated fitting is required before any
    predictive-spread interpretation. Chart-speed coupling of regional
    trajectories is not stochastic short-horizon reachability.

= Rhythmic variance control

Scalar $r(t) -> sigma(t)$ remains the *minimal* special case of accessibility
control. Event-locked spindle $d_n$ timing is a chart constraint (S2), not
causal denoising. Write-gate specificity against energy-matched controls is
not supported. Power-matched and phase-shuffle nulls remain unpaid for the
full discriminant.

= Thalamic access

Two-operator existence on a frozen landscape is computational
@langell2026_thalamic_access. In one
auditory TRN-to-relay preparation, PV-selective photoinhibition is associated
with evoked participation-ratio contraction @langell2026_trn_geometry; a full TRN variance-gate
hypothesis, including a scalar Fano clamp, is not validated. On the same
resource, both PV- and SST-family photoinhibition associate with non-scalar
change in residual covariance *shape* after prestimulus cleaning
@langell2026_ta_rolon --- a bounded
contrast against scalar rescaling, not identification of $A_"noise"$ or of a
chart Jacobian. Stronger repertoire-gating and prestimulus-controlled shape
claims on a separate optogenetic resource have been rejected. Direct mapping
onto NDT operators remains open. A joint TRN $->$ meso $->$ surface-macro
test is not currently estimable from the audited archives (item 10). NDT has
not found the thalamic mechanism.

= HELS versus HELS-A versus HELS-A1

- *HELS (legacy):* where does $V$ come from? Infrastructure is not writing.
- *HELS-A:* context operator $A_H$ on frozen $V$. Synthetic access can
  change first-passage and unsaturated committor bias without rewriting the
  landscape @langell2026_hels_a. Official confirmatory seeds were not consumed as a pass. A
  neighbourhood robustness gate failed.
- *HELS-A1:* header eligibility of a CA1--prefrontal archive is not a
  hippocampal mechanism. Spike-time scoring remains closed until an estimator
  is independently qualified. Header yield is not a CA1 result.

A measured-state history constraint (recent history improves linear prediction
of subsequent EEG beyond current state on DANDI 000458) is P6-adjacent. It is
not landscape writing. The corresponding prediction uses measured chart state
$x_t$, not latent $X_t$.

= Dendritic mobility bias

A companion simulator separates fast dendritic access from a slower
phenomenological bias $M_b$ @langell2026_slow_branch. The same logical move ---
control changing futures without rewriting content --- can be stated at the
dendrite. That is a speculative microscale analogue, not an empirical MNPS
identity, and the micro--meso--macro chain remains mostly dashed.

= Robustness meaning by layer

#figure(
  kind: table,
  clean-table(
    columns: (1.3fr, 2.4fr),
    align: (left, left),
    inset: 4.5pt,
    table.header([*Layer*], [*What would count as robustness*]),
    [State chart], [Same direction under alternative features, preprocessing, and site],
    [Local $J$ / $a$], [Truth-known envelopes *and* residual-quality gates on the empirical chart],
    [Reachability], [Horizon/noise sensitivity plus a residual gate; not Gramian controllability],
    [Committor / FAR], [Declared destinations / perturbation family; currently conceptual],
    [Mechanism], [Causal or discriminative test against arousal, power, and matched-energy controls],
  ),
  caption: [Robustness is layer-specific. Surviving a clinical contrast is not operator identification.],
)

#netn-box(title: [Robustness summary])[
  The article's discipline is negative as much as positive. Spindle timing
  replicates on two datasets and is incomplete on matched-control specificity.
  Coma geometry is recovery-linked on the invalidity-fixed 301-patient merge
  (S2). Meso--macro contact does not license a different inferential claim
  class. IBL
  decoder PASS versus discrete-flow STOP is the same lesson on a different
  chart. Closed gates stay closed.
]

#bibliography("references.bib", style: "apa")
