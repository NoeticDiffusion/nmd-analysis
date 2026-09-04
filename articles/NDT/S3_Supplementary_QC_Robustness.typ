// S3 Supplementary: Embodied Anchoring Principle (EAP) — formal targets and
// empirical status. Moved out of the NoeticDiffusionTheory.typ main-text
// Appendix (dedicated file per the EAP appendix's size and its close ties to
// companion empirical articles) to keep the main article focused on Tier-1
// claims.

#import "template_eLife.typ": *

#show: netn-template.with(
  title: "S3 Supplementary: Embodied Anchoring Principle (EAP)",
  short-title: "S3 EAP - NDT",
  subtitle: "Formal integration with RVC, neural substrates and rhythms, exploratory phenomenology, the measurement plan, and empirical status from companion analyses",
  authors: (
    (name: "Robin Langell", affil: 1),
  ),
  affiliations: (
    "Langell Konsult AB, Vallentuna, Sweden",
  ),
  corresponding-author: "Robin Langell, hello@noeticdiffusion.com",
  article-type: "Supplement",
)

#set par(leading: 0.8em, spacing: 0.6em)
#set math.equation(supplement: none)
#show math.equation: set block(above: 1em, below: 1em)

#netn-box(title: [Relation to the main article])[
  This supplement expands the *Embodied Anchoring Principle (EAP)* appendix
  pointer from the main article (`NoeticDiffusionTheory.typ`, Appendix). EAP is
  a *Tier-2* extension: its predictions target a later wave of
  interoception-focused and neurophenomenological studies. The core Tier-1
  tests concern the minimal MNDM, functional RVC, and MNPS geometry, and do not
  require any result reported here.
]

= S3.0 Role and empirical priority

EAP states that denoising is *conditioned* on interoceptive/body state: A
*self-prior* anchors reconstruction to a world‑for‑me. The anterior insula
(AIC) and ACC adjust precision on interoceptive channels and bind
interoceptive with exteroceptive streams, thereby shaping which latent samples
are stabilized and *when* @critchley2013 @khalsa2018 @wang2019. In terms of
empirical priority, EAP should be read as a *Tier‑2* extension of NDT: its
predictions are intended for a later wave of interoception‑focused and
neurophenomenological studies, whereas the core Tier‑1 tests concern the
minimal MNDM, functional RVC, and MNPS geometry.

= S3.1 Model implementation and integration with RVC

*Formal integration.* EAP introduces two forms of embodied modulation:
(i) landscape conditioning via a self-prior, and (ii) variance schedule
entrainment via bodily rhythms. We specify both mathematically.

*Landscape conditioning.*

#math.equation(block: true,
  $
    F(X, t)
      mapsto F(X, t) + lambda(t) F_("self")(X, s_t),
      quad
      alpha, beta
        = alpha_0 + kappa_alpha h(s_t),
          beta_0 + kappa_beta h(s_t)
  $
) <eq:eap-landscape>

where:

- $s_t = (phi_("cardiac")(t), phi_("resp")(t), A_("HEP")(t))$ is the
  interoceptive state vector (cardiac phase, respiratory phase, HEP amplitude).
- $F_("self")(X, s_t)$ penalizes neural states $X$ that are incongruent with
  bodily state $s_t$ (for example, high‑arousal neural signatures during
  physiological calm).
- $lambda(t)$ sets self-prior strength, decomposed as
  $lambda(t) = lambda_("signal")(t) lambda_("binding")(t)$, where
  $lambda_("signal") prop A_("HEP")$ (interoceptive signal strength) and
  $lambda_("binding") prop "FC"_("AIC-PCC")$ (ownership binding).
- $h(s_t)$ is a context-sensitive modulator that adjusts landscape weights.

*Alternative gating formulation.* While Eq. @eq:eap-landscape presents EAP as an
additive potential term (energetic cost), it may also be implemented as a
*gain control* or gating mechanism, where $lambda(t)$ modulates the *slope* of
$F$ (steepening gradients in task-relevant directions) rather than adding a separate
basin. Both formulations predict that body state shapes the attractor landscape,
but the gating model emphasizes signal-to-noise ratio modulation.

*Identifiability note.* Because both the $d(X)$ term in the extended potential and
the self-prior $F_("self")$ penalize "misconfigured" states, there is a risk of
confusing generic deviations from optimal metastability with specifically
embodied misalignment. Our empirical strategy is to *isolate* $F_("self")$
using paradigms with strong interoceptive manipulation (for example,
cardio‑visual synchrony, threat vs. safety contexts) and to examine whether
EAP-related indices (HEP, AIC–PCC connectivity, phase‑coupling terms in
$lambda(t)$) explain variance in phenomenology and MNPS geometry beyond what is
captured by $d(X)$ alone. In early datasets, we therefore treat EAP effects as
exploratory and require that any putative self‑prior signatures remain after
controlling for $d(X)$-based metastability deviations.

*Variance schedule entrainment.*

#math.equation(block: true,
  $
    r(t)
      mapsto r(t) [
        1
        + gamma_("entrain")
          cos(phi_("cardiac") - phi_("theta"))
          cos(phi_("resp") - phi_("alpha"))
      ]
  $
) <eq:eap-rvc-coupling>

This is a *formal target*, not an estimator used in the present article or a
calibrated biological law. If such coupling exists, phase alignment could
modulate the effective schedule; its strength, sign, and state dependence
remain empirical questions. We therefore do not assign a fixed empirical
value to $gamma_("entrain")$.

= S3.2 Empirical status from companion analyses

The current implemented measurement layer is AnchorState: windowed HRV, PPG,
and pupil-derived proxies such as `vagal_index`, `sympathetic_index`,
`vascular_index`, and `anchor_index`. These are operational autonomic/arousal
proxies, not direct measurements of HEP, vagal nerve activity, AIC--PCC binding,
or $lambda_("signal")(t)$. In a working-memory dataset, the anchor surface and
MNPS/trajectory geometry varied non-monotonically with task phase, whereas
direct block-native anchor--MNPS coupling was modest and between-subject
correlations were null after correction. This supports a constrained
condition-level co-modulation result, not causal body-to-manifold gating.

In the RichSleep phase-resolved data, autonomic phase locking was
carrier-specific: slow-oscillation trough/upstate timing was stronger than
spindle-onset timing, and REM-theta did not provide a uniform positive result.
The spindle-onset conclusion was method-sensitive across null constructions,
and intrinsic event strength did not yield FDR-supported alignment-to-geometry
efficacy. Thus event--body timing is EAP-relevant but does not establish
Eq. @eq:eap-rvc-coupling.

= S3.3 Metabolic perturbation boundary (not EAP validation)

A paired type-1-diabetes clamp EEG reanalysis provides a useful counterexample
to treating slow rhythmic structure as a scalar benefit. Hypoglycemia was
associated with lower 3D mobility and a mixed stratified signature
(lower $m_a$, $m_e$, and $e_e$; higher $d_n$ and $e_m$), while neither
prespecified 3D Jacobian endpoints nor reachability log-volume supported a
confirmed reachability collapse after the relevant correction. The dataset
contains no continuous glucose, recovery, cardiac, respiratory, HEP,
interoceptive-awareness, or behaviour measures. It is therefore a bounded
metabolic condition contrast, not a test of EAP, a metabolic adequacy factor,
or a consciousness measure; it is also unrelated to HELS landscape learning.

*Mechanistic pathway (AIC → variance modulation).*

#math.equation(block: true,
  $
    text("Cardiac signal")
      ->_("NTS/insula")
      A_("HEP")
      ->_("AIC → L6 CT")
      text("Corticothalamic gain")
      ->_("L6 → TRN")
      r(t) text(" modulation")
  $
)

AIC detection of interoceptive signals modulates layer‑6 corticothalamic (CT)
neuron excitability via local interneuron circuits @wang2019. Since L6 CT
neurons control TRN firing (see the main article's Rhythmic Variance Control
and TRN gating section), interoceptive state indirectly gates variance: Strong
interoceptive signal → enhanced L6→TRN drive → tighter variance clamping. This
creates the observed cardiac‑phase‑dependent perceptual gating @salomon2016.

= S3.4 Neural substrates and rhythms

*Insula/ACC as precision and binding.* AIC adjusts gain on interoceptive
channels (precision control) and participates in interoceptive–exteroceptive
integration; ACC contributes evaluative control and autonomic set @wang2019.
*Critically,* we distinguish two separable components of the self-prior:

1. *Interoceptive signal transmission* (AIC‑mediated): Can the bodily signal
   reach cortex? Measurable via HEP amplitude and interoceptive accuracy tasks.
2. *Self-binding/ownership attribution* (AIC–PCC/TPJ‑mediated): Does the signal
   feel like *mine*? Measurable via AIC–PCC connectivity and ownership‑illusion
   paradigms.

This distinction is crucial for understanding depersonalization: *Signals can
be detected (component 1 intact) while ownership fails (component 2
disrupted)* @medford2016. We predict DPD shows normal or even heightened HEP
amplitude but reduced AIC–PCC functional connectivity, especially during
interoceptive tasks. Posterior parietal/TPJ and posterior cingulate (PCC)
provide the ownership tag that binds interoceptive content to the first-person
perspective @salomon2016.

*Cardiac/respiratory entrainment and phase landscape.* The self-prior is *not
static* but oscillates rhythmically with bodily cycles, creating a
body-synchronized variance schedule. Perception, attention, and memory encoding
fluctuate with cardiac (∼1 Hz) and respiratory (∼0.2–0.3 Hz) phase, suggesting
that *$lambda(t)$ itself is rhythmic*.

We predict a *continuous phase landscape* of denoising efficiency:

#math.equation(block: true,
  $
    cal(D)(phi_("cardiac"), phi_("resp"), phi_("theta"))
      = cal(D)_0
        [
          1 + sum_i w_i cos(phi_i - phi_i^*)
        ]
        ∏_(j < k)
        [
          1 + c_(j k) cos(phi_j - phi_k)
        ]
  $
)

where $cal(D)$ is denoising efficiency, $phi_i^*$ are optimal individual
phases, $w_i$ are phase weights, and $c_(j k)$ capture phase–phase
interactions.

*Illustrative future targets:*

- *Primary peaks:* The location, magnitude, and even the number of phase
  optima must be estimated rather than fixed a priori. Candidate cardiac,
  respiratory, and theta combinations provide a preregisterable search space,
  not numerical NDT predictions.
- *Secondary structure:* Additional peaks/troughs at cardiac–respiratory
  harmonic combinations (2:1, 3:1 ratios).
- *Empirical validation:* Measure entropy $e(t)$, recall performance, and
  subjective clarity as function of 3D phase coordinates
  $(phi_("cardiac"), phi_("resp"), phi_("theta"))$ during encoding.

*Practical operationalization.* Since \< 100 ms phase precision exceeds current
phenomenological methods, we test via (i) phase-triggered stimulus
presentation with neural/behavioral readout, (ii) post‑hoc phase‑binning of
continuous encoding data, and (iii) phase‑shuffling controls to verify that the
observed structure is not random.

*Pathological phase relationships:*

- *Anxiety:* Over‑rigid cardiac–neural coupling (pathologically locked
  $lambda(t)$), creating context‑insensitive hyper‑anchoring. Predict:
  elevated HEP–theta phase‑locking across contexts, even when this is
  contextually inappropriate.
- *Depersonalization:* Absent or random cardiac/respiratory–neural coupling
  (decorrelated $lambda(t)$). Predict: no systematic phase effects on
  perception, flat HEP–context interactions.

These phase‑coupling patterns may be measurable and manipulable in future
biofeedback studies, but that possibility is an exploratory research hypothesis
rather than a therapeutic claim.

*Section takeaway (EAP for this manuscript).* Within the present paper, EAP's
role is primarily to (i) formalize a self‑prior term $F_("self")$ and its
coupling to interoceptive signals, and (ii) sketch how this could, in
principle, modulate denoising schedules and MNPS geometry. Detailed phase
landscapes, SPI‑style composite indices, and therapeutic applications are
treated as Tier‑2, future‑work directions rather than requirements for the
initial validation of NDT's core sleep and clinical geometry predictions.

= S3.5 Exploratory phenomenology, pathology, and training

*Mirror failures.* *Under‑anchoring* (DPD): Denoising proceeds but fails to
bind to self (high $Omega$ yet low ownership), associated with low/flat
$lambda(t)$ or weak AIC–PCC coupling. *Over‑anchoring* (panic/anxiety):
Bodily noise overweighted, forcing threat‑consistent reconstructions
(exaggerated, context‑insensitive $lambda(t)$). EAP thus predicts
*topologically distinct* failures in MNPS (low recurrence and unstable hubs in
DPD; over‑recurrence in anxiety during anticipatory phases).

*Trainability.* Interoceptive training (breath/heartbeat attention) may
recalibrate EAP: increase AIC–ACC coupling, restore context-sensitive
$lambda(t)$ modulation, and alter component readouts linked to
curvature/variance *flexibility* (anchored exploration). These training and
pharmacology ideas are exploratory roadmap claims, not clinical recommendations.

= S3.6 Measurement plan and composite index

*Self-prior index (SPI).* We propose a composite measure combining multiple
EAP signatures:

1. *Signal strength:* HEP amplitude and latency (baseline interoceptive
   precision).
2. *Context sensitivity:* HEP modulation by task/context (for example, HEP
   difference between safe vs. threat contexts, or cardio‑visual synchrony
   effects).
3. *Anatomical substrate:* AIC/ACC activation during interoceptive tasks
   (fMRI/PET).
4. *Binding network:* AIC–PCC/TPJ functional connectivity (distinguishes signal
   from ownership).
5. *Phase coupling:* Cardiac/respiratory–neural phase coherence and its
   task-dependent modulation.

*Predicted covariations.* SPI should correlate with (i) cycle‑averaged
coherence $bar(Omega)$ during active denoising (tasks, encoding), (ii) Atlas
component profiles linked to flexible geometry (see *Supplementary Methods
S1*), and (iii) subjective presence/embodiment ratings. After interoceptive
training or successful therapy for DPD/anxiety, SPI should normalize—
specifically, *context sensitivity* (component 2) and *binding connectivity*
(component 4) should improve more than raw signal strength (component 1).

*Estimation pipeline for $lambda(t)$ with artifact control.* We standardize
EAP estimation as follows: (i) extract R‑peaks and respiratory phase; (ii)
compute HEP using robust averaging with ECG/EOG artifact regression and
cardioballistic artifact suppression (template subtraction); (iii) estimate
instantaneous $lambda_("signal")(t) prop A_("HEP")$ and $lambda_("binding")(t)$
via AIC–PCC functional connectivity; (iv) derive phase‑aligned coupling terms
for Eq. @eq:eap-rvc-coupling; (v) validate with phase‑shuffled surrogates and
cross‑condition controls (safe vs. threat) @park2019 @coll2021.

*Falsifiable contrasts.* If EAP is correct: (a) HEP/context interactions
predict presence/ownership beyond raw HEP; (b) DPD shows normal interoceptive
*detection* but reduced insula–PCC coupling and weak $lambda(t)$ modulation;
(c) phase‑locked sampling benefits vanish when cardiac/respiratory phases are
randomized or misaligned.

#netn-box(title: [Status ceiling])[
  EAP remains Tier-2. Current companion evidence supports bounded,
  condition-level autonomic/MNPS co-modulation in wake and carrier-specific
  (SO-trough-dominant) autonomic phase-locking in sleep. It does *not* support
  causal body-to-manifold gating, phase-resolved variance entrainment
  (Eq. @eq:eap-rvc-coupling remains an untested formal target), HEP-based
  binding, or clinical translation. The hypoglycemia contrast documents a
  bounded metabolic MNPS dissociation, not an EAP metabolic gate.
]

#bibliography("references.bib", style: "apa")
