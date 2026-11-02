# Preregistration: layer-specific neural dynamics in interictal- and ictal-labelled iEEG

**Study:** NDT v1.0 / ds004100. **Protocol revision:** 1.1, 22 September 2026.  
**Data freeze:** `neuralmanifolddynamics_ds004100_20260918_083008`.  
**Status:** unregistered secondary-analysis draft, revised before new condition-effect estimation. The August protocol is superseded following the investigator's explicit source correction. No external registration or empirical hypothesis test has been performed.  
**Theory:** *Noetic Diffusion Theory: Neural State, Dynamical Accessibility, and the Geometry of Possible Futures*, in `articles/NoeticDiffusionTheory_v2/`. The study name does not rename the theory manuscript or the measurement software.

## 1. Question, scope, and inferential hierarchy

Do recordings labelled ictal and interictal differ in the dimensionality of local chart increments and in observed short-lag separation of nearby trajectories? Do the new measurement families show a coherent or dissociated pattern across spread, mean motion, amplification, history and turning?

The September export permits tests that the originally nominated August export could not supply directly. The primary analysis now uses two explicitly exported measurements: local increment effective dimension and same-pair neighbor gain. These are distinct operational quantities motivated by NDT's separation of state geometry, local law and possible futures. They are not interchangeable measures of consciousness or a single latent capacity.

The primary contrast is deliberately a **whole-recording label association** in a locally standardized observation chart. It is not an annotated seizure-interior comparison. This choice permits a transparent test of the processed export while preserving the label limitation; it must not be described later as a pure ictal-state effect. A separate, stronger NDT-C3 study would test different future laws at matched present state using independent event annotation and leakage-controlled forecasting. Section 10 sets its prerequisites; it is not a current confirmatory endpoint.

The current study primarily supports inferential class 1, association. It does not establish NDT-C2 (incremental out-of-sample information beyond conventional summaries), NDT-C3 (conditional control), latent-operator identification, an Itô drift/diffusion, a committor or finite-amplitude resilience. A positive primary result supports these nominated chart-level working hypotheses. It does not validate NDT as a whole; a negative or opposite result constrains the hypotheses in this dataset and measurement contract.

## 2. Data correction and previous exposure

The investigator corrected the source to:

`J:\repos\nmd-analysis\data\raw\neuralmanifolddynamics_ds004100_20260918_083008`

This is the resolved directory corresponding to the underscore-separated path in the request. No August and September files are pooled. The August [protocol](preregistration_ds004100_ndt_v1_20260922.md), coverage and reviews remain as superseded history. Revision 1.1 changes the endpoint hierarchy because the corrected export contains new measurement families; it is a disclosed pre-lock design change, not a response to new neural condition effects.

The dataset and prior ds004100 analyses are already known. During preparation of the earlier draft, repository searches exposed historical results describing lower ictal capacity and increased capture/canalization, including numerical summaries. Those historical constructs are not identical to the endpoints below. This is a preregistered reanalysis proposal of previously studied data, not an independent or outcome-naive replication.

For the corrected export, inspection is limited to schema, provenance, masks, support, missingness, time metadata, file identities and numerical availability. No condition means, effect sizes, new neural plots, classifiers or primary p-values are computed to select this protocol. Investigators must declare any additional prior exposure when registering.

The run manifest reports MNDM revision `58cf913bd817348f44d8713ea3f2aa9c1e98559f`; its built-in capability probe covers 200 files and is not treated as an all-file audit. The new [Luna xhigh coverage report](../coverage_september/coverage_report_september.md) and its input hashes identify all 319 corrected H5 inputs (739,229,963 bytes). Freeze the actual ingest/analysis source, imported configurations, environment, H5 hashes and protocol hash before execution; a dirty repository HEAD alone is not a software snapshot. The theory source hash remains `0b7cb65e69aec89b9263052ef6e9ac8adcc56ee2cb2e8c3a79a0ad8dc97f8f90`.

Upstream source identity is [OpenNeuro ds004100](https://openneuro.org/datasets/ds004100/versions/1.1.3), the HUP clinical iEEG dataset. Its [README](https://raw.githubusercontent.com/OpenNeuroDatasets/ds004100/master/README) describes ECoG/SEEG acquisition and surgical evaluation; its [dataset description](https://raw.githubusercontent.com/OpenNeuroDatasets/ds004100/master/dataset_description.json) gives version 1.1.3 and CC0. The accessible local source at `K:\ExternalReceivedDatasets\openneuro\ds004100` also identifies version 1.1.3 in its hashed dataset description. Local processed sample counts, not the upstream README's subject count, define screening.

## 3. What the corrected export contains

The corrected export contains **319 H5 files from 57 participants**, with **208 ictal-labelled and 111 interictal-labelled recordings** and **55 participants with both labels**. The coordinator's independent [endpoint-support check](../validation/endpoint_support_checks.json) found that all 319 files meet the numerical status/mask and >=30/50% criteria for both H1 and H2. Thus 55 is the structural upper bound for each paired analysis, not a declaration that contact/reference and other comparability gates passed. Full per-file counts, pairing, masks and nested qualifications are recorded in the September audit. The following table identifies each family's role; existence does not imply that all nested products or all rows are supported.

All paths below are relative to the H5 root. `DF` abbreviates `/dynamical_families` only in this table.

| Family / path | Measurement and role | Interpretation ceiling |
|---|---|---|
| `DF/diffusion/v1` | `series/diffusion_effective_dimension` is H1; `diffusion_total` is secondary | Local raw increment covariance divided by nominal dt; `ito_not_qualified`. Aliases `d_diff`, `D_total`, `a_hat` are not extra endpoints. |
| `DF/amplification/v1/neighbor_gain_q90_level1` | `series/neighbor_gain_q90` is H2 | Per-source 90th percentile of the ratio of successor distance to starting distance for the **same neighbor pairs**; not maximum operator amplification. |
| `DF/drift/v1` | Realized velocity and pooled/blocked-crossfit conditional mean rate | Finite differences and finite-lag conditional means; neither is automatically Itô drift or the existing MNPS derivative. |
| `DF/one_step/v1` | Lag-1 affine map, innovation covariance and gain/rotation/generator proxies | Recording-level fitted map; nested support and identification gates apply. Repeated window-shaped outputs do not create independent operators. Direct lag 2 and iterated maps are separate products. |
| `DF/history/v1` | Predictive gain and a separate history-conditioned operator | Level-1 gain can be computed while level-2 identification fails; neither certifies a leakage-free biological memory mechanism. |
| `DF/turning/v1` | Realized turning angle/rate | Trajectory turning, not operator rotation. |
| `DF/destination/v1` | Protocol/qualification placeholder | Not testable without explicit A/B definitions and qualified first-hit/reaction-coordinate support. File labels do not supply these. |
| `DF/resilience/v1` | Perturbation-protocol placeholder | Not testable without observed perturbation and recovery/survival outcomes. |
| `/jacobian*/derived_metrics/v1`, `/finite_time_response/v1` | Jacobian summaries and model-derived finite-time response | Distinct from same-pair gain and observed perturbational response. |
| `/transition_residuals/v1`, `/transition_residual_covariance_proxy/v1` | One-step prediction residuals and covariance proxy | Not identified biological process noise. |
| `/stochastic_reachability/v1` | Model-propagated discrete chart-space spread | Present in September, unlike August; exported horizons can depend on recording length and cannot be relabelled as a common H4 endpoint. |

The first audited September file declares MNDM 3.0.1 and `coords_3d_subject_anchored`, with eight-second windows and four-second steps. It contains all eight named families, but destination/resilience are `not_testable`; the lag-2 map and history-conditioned operator fail their separate support gates. `R_b_over_a` and `A_bD` exist as fields but have no finite observations in that file, with ratio semantics `not_applicable`. They are therefore not registered as available endpoints. The all-file audit determines their complete coverage, not this example.

The exemplar's signal-support provenance reports local-input-frame feature fitting, uncertified effective filter support (`temporal_support_status=unknown`) and unrecorded source quality. A `subject_anchored` name does not establish a single cross-recording reference. The new export includes support signatures and validity/grain certificates; computed families marked `measurement_validity=not_assessed` and `claim_status=no_biological_claim` remain unqualified biological objects.

The completed audit and independent nested-product check establish the following all-file distinctions:

| Product | September coverage / computation |
|---|---|
| Diffusion, amplification, history level 1 and turning | Computed in 319/319; measurement validity not assessed; no biological claim |
| Blocked-crossfit mean rate | 285 computed, 34 insufficient support |
| One-step lag-1 family | 85 computed, 234 insufficient support; within these, the nested affine product is 85 computed, 73 insufficient support and absent in 161 refused files |
| Direct lag-2 affine map | 9 computed, 310 insufficient support |
| Iterated one-step horizon map | 15 computed, 70 insufficient support, 234 not testable |
| History-conditioned operator level 2 | 72 computed, 247 insufficient support; do not inherit level-1 success |
| Destination and resilience | Not testable in all 319 files |
| `R_b_over_a`, `A_bD` | Present in all 319, but no file has a finite observation |
| Primary and 9D FTR, transition residuals/Q proxy | Computed in 319 files; no automatic biological or prediction qualification |
| Primary stochastic reachability | Computed in 319, but spans **42–323 propagator steps**, not a standardized short horizon |

Global 3D/9D coordinates and Jacobian arrays are present in all 319 files. Observed timestamps have no detected gap/nonpositive step at the expected grid, but temporal filter support is unknown and source quality unrecorded in all 319. These metadata distinctions, especially failed nested operators, are part of the scientific report and must not be hidden by a family-presence count.

### Original-source annotation and channel availability

The coordinator's separate [source-sidecar audit](../source_metadata/README.md) matched all 319 H5 identities to 319 iEEG JSON and 319 channel TSV files. All 208 ictal sources have parseable onset/offset events; the 111 interictal sources have no events TSV. These source annotations are available even though they are not embedded as aligned H5 events. All 57 subject/session/acquisition groups have stable raw channel name/type/status signatures across runs, but source reference is `n/a` throughout and processed contact/reference comparability remains unverified.

For HUP060 ictal run 01, the source annotation spans 120–317.998 seconds of a 377.998-second recording. Across all ictal files, only **38 files from 18 participants** contain at least 30 nominal exported windows wholly inside their annotated seizure; nominal contained counts range 0–280. This is a support audit, not a neural effect analysis. It ignores unknown effective filter support and whole-recording estimator fitting, so it cannot certify seizure-pure family values. Source metadata are now available for a future event-restricted reconstruction; lack of H5 event arrays must not be misreported as absence of original annotations.

## 4. Registered hypotheses and endpoints

**H1 — reduced effective dimensionality of increments.** Ictal-labelled recordings have a lower participant-level median local increment effective dimension than interictal-labelled recordings. Exact source: `/dynamical_families/diffusion/v1/series/diffusion_effective_dimension`. This is the effective dimension of a local increment covariance, not occupied-state dimension, reachable volume or number of biological degrees of freedom.

**H2 — reduced observed neighbor separation gain.** Ictal-labelled recordings have a lower participant-level median same-pair neighbor gain than interictal-labelled recordings. Exact source: `/dynamical_families/amplification/v1/neighbor_gain_q90_level1/series/neighbor_gain_q90`. The declared lag is one native step; verify actual nominal dt is four seconds and the same across included runs. Do not replace this endpoint with an affine operator's maximum gain, an amplification rate, or a finite-time-response gain.

Both are directional epilepsy working hypotheses, informed by the historical canalization/capacity interpretation. Neither direction is a mathematical necessity of NDT. H1 and H2 form the sole confirmatory family. No composite “NDT score” is fitted. They may dissociate, and a reduction in either does not establish loss of consciousness, a seizure attractor or diminished latent reachability.

The registered population targets are, separately, that **more than half of all supported paired participants have a strictly negative ictal-minus-interictal difference** in the respective endpoint. Exact ties count as non-improvement. This target is explicit because it differs from a sign test conditioned on nonzero differences.

Secondary families in Section 8 are descriptive only in revision 1.1. They cannot substitute for failed primary endpoints. This keeps a broad new export from becoming a search over many interchangeable-looking metrics.

## 5. Unit of analysis, labels and eligibility

Screen all participants and files in the corrected frozen export; no new data collection or outcome-dependent stopping is planned. Primary labels come from mutually consistent filename/task metadata and must be traceable to the source recording type. A conflicting/unknown label is excluded and logged. **Do not interpret every window of an ictal-labelled file as a seizure window.** Preictal/postictal padding and differing seizure fractions can affect this whole-file association.

All primary summaries use the entire valid exported recording. Original onset/offset annotations are available, as documented in Section 3, but their alignment and the estimators' effective temporal support have not been qualified for a seizure-interior analysis. Those annotations cannot replace this registered whole-recording contrast after inspection of its effects. A seizure-interior extension requires a separately frozen amendment and recomputation of any neighborhood/operator whose fitting support spans outside that interval.

The independent unit is the participant. Files, windows, neighbor pairs and fitted operators are repeated measurements. Each participant contributes at most one paired difference per primary endpoint. Within each participant, retain the session/acquisition stratum with the largest number of metadata-eligible source runs containing both labels; resolve ties lexicographically by session/acquisition. This ranking is frozen before endpoint aggregation. Do not mix SEEG and ECoG within a paired contrast.

Collapse exact duplicate exports and identify crops from the same original recording before aggregation. Repeated seizures can contribute recording summaries but cannot inflate participant N. At least one supported source recording per label is required for the association analysis; a two-per-label requirement belongs to future held-out forecasting, not these recording summaries.

Across the paired recordings, verify the same feature definition, preprocessing/reference policy and support/fallback signature. Contact coverage/reference must be consistent or demonstrably comparable from channel/derivation metadata. If that cannot be established, the corresponding participant's primary contrast is not confirmatory; file-label descriptions can still be shown as exploratory. Scalp-named regional groups cannot establish intracranial anatomical comparability. The corrected overlay disables regional and block-Jacobian outputs; no regional hypotheses are inherited from August.

Freeze a per-recording comparability ledger containing coordinate layer, feature-map/normalization recipe, fit-population identity/hash and fitted parameters, fallback signature, source contact signature and actual processing-reference provenance. Unknown reference is not replaced by an assumption of equality. Report these signatures with the paired analysis; raw channel-name stability alone does not close this gate.

Exclude corruption, inconsistent source identity, incompatible measurement definitions, or insufficient endpoint-specific support. Do not exclude a large endpoint value, an atypical seizure or a participant whose effect opposes the hypothesis. Do not reduce the dataset to complete cases across every secondary family.

## 6. Scaling, validity and support contract

Keep canonical MNPS `[m,d,e]` and the canonical nine-coordinate definition unchanged. No condition-trained axes, projection weights or newly selected feature subsets are permitted. Preserve feature fallback semantics and all validity/provenance records; finite numbers are not proof of source quality.

The **primary estimand is explicitly the relative geometry of the export's locally normalized chart**. Apply the existing declared transformation separately as recorded; do not retrospectively re-anchor or rescale either condition to obtain an expected effect. A recording-local normalization can change dimensionality and gain, including through anisotropic scaling. Thus even significant H1/H2 support differences in the fixed processing-defined measurement, not absolute neural variance, intrinsic coordinate-invariant geometry or a biological diffusion tensor. The same transformation recipe and feature support must hold across labels. A common-anchor reconstruction is a separate sensitivity/extension, never a silent replacement for the primary values.

For each endpoint require `computation_status=computed` at its own product path, `support_status=sufficient` where recorded, the correct coordinate/lag contract, and finite values passing the product's local mask. A family-level `computed` certificate cannot override a nested failure. `measurement_validity=not_assessed` permits a clearly labelled operational measurement contrast; it does not establish biological validity or a predictive operator. An explicit invalid/not-testable product is missing, not zero.

Use at least **30 valid native centers and at least 50% valid centers per recording per primary endpoint**, together with any stricter native estimator requirements. The denominator is all exported native MNPS rows for that recording; this conservative rule is fixed before scoring. Count supported query/source centers once, not each of their neighbor pairs. Native-grid series and transition-pool indices have different meanings: for **H1**, use the T-length `valid` mask and finite endpoint; `source_idx` identifies the increment training pool and is not a query mask. A terminal state can have a valid covariance estimate based on other supported increments. For **H2**, values are written at native source-center indices: index its T-length array by the supported `source_idx` entries, require finite gain and the product's neighbor-pair support, and count each source once. Do not zip a T-length series with T−1 indices, truncate H1 to the transition pool, or duplicate a recording scalar over windows. This distinction was checked against the writer at the declared ingest revision and the first H5's masks. Any other shape/mapping must be verified before use; otherwise mark it unavailable.

Require positive observed time steps and supported source/successor indices; no increment, neighbor pair or horizon may cross a source-file, segment, dropped-index or temporal gap. The nominal four-second grid does not certify effective filter support. For these whole-recording descriptors, unknown filter support limits interpretation and prevents an independent-future or event-boundary claim; it is not silently treated as known. A predictive extension cannot proceed on that basis.

For H1, retain the declared PSD regularization in the primary measurement and report the prevalence of `psd_floor_applied`; run a descriptive sensitivity excluding floor-affected centers with the same support thresholds. This is an explicit estimator sensitivity, not proof that regularized eigenvalues represent biological dimensions. H2 must preserve the same-pair estimator, source-distance epsilon, neighbor settings and successor support from the frozen export. Do not recompute q90 by pooling pairs across centers.

Before primary testing, complete the metadata/support audit, channel/signature comparability ledger and endpoint mapping checks without computing condition medians. All gate outcomes and exclusions are frozen. If a gate fails, preserve its negative evidence and report METHOD-LIMITED instead of changing the endpoint or threshold.

## 7. Aggregation and statistical decisions

For each supported recording, take the median over valid native centers for H1 or H2. Within participant and label, take the median of eligible recording medians. Define `Delta_i = median_ictal_i − median_interictal_i`. Use all eligible recordings under that rule; the number or duration of seizures must not increase a participant's weight. Report support, file counts, recording duration and missingness by label and participant.

For each primary endpoint let `K` be the number of paired participants with `Delta_i < 0`, and `N` all supported paired participants, **including exact ties**. Test `P(Delta < 0) <= 0.5` against `>0.5` with an exact one-sided binomial upper-tail p-value at p=0.5. No numerical tie tolerance is selected after inspecting effects. Require at least **20 supported paired participants per endpoint**; otherwise present descriptive effects and mark the endpoint insufficiently supported, without a confirmatory p-value.

Apply **Holm correction to the two primary hypotheses jointly**, familywise alpha 0.05. Keep an untestable member as p=1 solely for multiplicity bookkeeping, clearly distinguished from an observed null. Report both raw and adjusted p-values and the complete two-hypothesis family, including unavailable endpoints. No secondary p-value is promoted into this family. For orientation, the first Holm step (raw p<=0.025) requires at least 15/20, 21/30 or 36/55 negative participant differences at those sample sizes; these exact binomial calculations include ties in N and are not an observed-power analysis.

Report N, K, ties, the all-participant negative fraction with an exact two-sided 95% binomial interval, every paired difference, median paired difference and a descriptive 95% percentile bootstrap interval (10,000 participant resamples; seed 20260922). Raw paired differences are in this measurement's chart units and may have heterogeneous scaling across participants; do not call them a common physical effect. The bootstrap interval does not replace the probability-of-negative-difference test.

A primary **processed-chart association hypothesis** is supported only if G1–G4 have passed for that endpoint, its Holm-adjusted one-sided test rejects and the observed effect direction is negative. Keep `measurement_validity=not_assessed` and `claim_status=no_biological_claim` unchanged even in that case: the formal association does not become a qualified biological measurement. Every paired effect and p-value must carry its endpoint computation/support/validity/claim fields, temporal-support status, source/reference comparability verdict and normalization/fit signature. An incompatible or unverifiable G2/G3 case stays descriptive/METHOD-LIMITED and cannot be promoted by significance. The joint “reduced increment dimension and observed gain in the processed chart” statement requires both hypotheses. An opposite direction contradicts the directional working hypothesis descriptively; no unregistered opposite-tail significance claim is made. Nonsignificance is inconclusive, not equivalence or evidence that neural futures are identical. No observed post-hoc power is reported; tabulate exact binomial sensitivity at the final support-only N before testing.

## 8. Secondary measurement panel and sensitivities

Secondary outputs receive participant-level effects, support accounting and descriptive intervals, **no inferential p-values** in this version. The fixed panel is:

1. **Increment magnitude:** median `DF/diffusion/v1/series/diffusion_total`. It is locally normalized increment covariance magnitude, not absolute variance or latent stochastic capacity.
2. **Finite-lag mean motion:** median Euclidean norm of the blocked-crossfit conditional mean-rate vectors under `DF/drift/v1/conditional_mean_rate_level1/blocked_crossfit`; map the vector/mask/source index using the actual product schema. Realized velocity and pooled fits are separate descriptive comparators, not substitute drift estimates.
3. **Lag-1 operator gain:** one recording-level `operator_max_gain_rate` from `DF/one_step/v1/operator_max_gain_rate_level2/series`, only when its own upstream identification and support pass. A repeated per-window representation is counted once per fitted recording operator.
4. **Lag-1 operator rotation:** the separate recording-level `operator_rotation_rate` under `DF/one_step/v1/operator_rotation_rate_level2/series`, using the same rules. Do not interpret it as realized turning.
5. **History gain:** the declared recording summary `DF/history/v1/history_predictive_gain_level1/summary/history_predictive_gain`. A negative finite gain is retained. Failure of the level-2 history-conditioned operator does not invalidate level 1 automatically, and level-1 existence does not qualify level 2.
6. **Realized turning:** median `DF/turning/v1/turning_rate_level0/series/turning_rate` at valid centers. This is neither a rotation generator nor evidence of capture.
7. **Finite-time response:** median `g_max` and `d_resp` under `/finite_time_response/v1/primary/horizons/h2/series`, restricted to actual physical horizon 8 seconds (tolerance 1e-6 seconds). These remain model-derived, distinct from H2.

For native-center endpoints use Section 6's support rule; for recording-level scalar products use the product's full support/qualification gate, with the scalar once per recording. Aggregate recording products by median within participant/label, as above. Record all failures without zero filling. Verify each named path in the September coverage dictionary before analysis; a missing path is unavailable, not permission to search for a favorable alternative.

**Reachability:** do not compare the currently exported `w_q`, `d_eff`, `a_q` or `v_norm` across files as a common-horizon primary/secondary effect. The exemplar accumulates 90 propagator steps, whereas the named one-step forecast and FTR horizons are different objects. Report horizon/Q-provenance coverage only. A future fixed-physical-horizon reconstruction must freeze its propagator, admissible Q semantics, gap policy and validation separately. Do not equate full-record reachability to H4 or an Itô diffusion.

**Unavailable constructs:** `R_b_over_a`, `A_bD`, destination and resilience are not replaced with zero or synthesized from derivatives. Direct lag-2 and iterated one-step maps and the history-conditioned operator are reported as coverage/qualification results, including failures; they are not silently approximated from successful lag 1.

**Locked descriptive sensitivities:** H1 without PSD-floor centers; same primary summaries within ECoG and SEEG; lexicographically first supported source recording per label; and participants whose median recording-duration ratio between labels lies between 0.8 and 1.25 (same full-record endpoint values). Report all sensitivities even if no usable sample remains. The duration restriction is a diagnostic of support imbalance, not proof of duration invariance. Equal-duration cropped re-estimation would change neighborhoods and normalization and therefore requires an explicit future amendment; merely trimming exported summaries cannot represent that re-estimation. No 9D substitution is allowed when a 3D primary fails.

## 9. Method checks, confounds and qualification

Before empirical primary testing, independently review the complete extractor and test native-array/source-index alignment, false or absent masks, nonfinite endpoints, all-NaN products, nested failures beneath computed families, gaps, unequal grid steps, duplicate source files, PSD-floor exclusions and repeated recording-level operators. Check the complete aggregation/tie/multiplicity implementation on synthetic data with known expected participant counts and decisions. Tests must reject unsupported inputs, not manufacture valid zeros. During preparation, the bounded [structural check](../validation/check_endpoint_support.py) verified all-file primary mask support and toy cases for terminal diffusion queries, nonfinite/masked rows, duplicate indices, exact binomial tails and two-test Holm arithmetic. Full inferential extraction/aggregation, the remaining failure tests and the processing-control pilot are **UNRUN**; these limited checks do not close G4.

Run a processing-control pilot before claiming a neural interpretation of H1/H2: simulate matched stochastic systems with known covariance dimension and pair-separation behavior, pass them through the same feature/normalization/measurement recipe where possible, and examine unequal durations, amplitude-only changes and autocorrelation. Freeze simulation parameters independently of empirical condition effects. Report cases in which local normalization or support differences create the nominated signature. Such failures limit interpretation; they do not justify retuning the chart. A formal estimator-recovery claim needs a separately specified acceptance envelope, not merely a successful H5 write.

The association test does not require windows or neighbors to be independent: inference uses participant summaries. It does require participant independence and a population-direction estimand compatible with this convenience sample. No shuffled-window p-values are valid substitutes. Permuting ictal/interictal windows would destroy dependencies and ignores that labels belong to whole recordings.

Important alternative explanations include seizure fraction within files, recording duration, sleep/vigilance, medication, implantation site and contact composition, referencing, artifact, spectral/complexity changes and run-local scaling. Report available metadata and label-specific support distributions. A result does not show incremental value beyond conventional EEG simply because those features were used to construct MNPS. No causal mediation, clinical utility or consciousness conclusion is registered.

## 10. Stronger NDT-C2/C3 tests: gated future extension

The September families make richer tests possible in principle, but computed history/one-step certificates and `simulator_validated` method tags do not certify independent empirical prediction. Current chart location, power and complexity must be controlled, and all raw support and fitted transformations must be isolated from held-out data. Unknown filter support and recording-local fits are material obstacles.

An independently timestamped extension is required before any C2/C3 empirical scoring. It must include verified seizure onset/offset and original source-run grouping; comparable contact/reference support; training-only common anchors and feature fitting; a ledger of actual source support for all predictors; at least two independent runs per label for within-participant held-out comparisons; current-state/spectral/complexity common support; fixed physical horizons measured from feature completion; frozen models, covariance estimators and statistical family; and null/positive/unsupported simulations covering occupancy, duration, autocorrelation and leakage.

The previous draft's 8-second conditional-future forecasting design is retained as a methodological starting point in the superseded document, not a registered current endpoint or an approved analysis of this new export. Its corrected principles remain relevant: equal nominal forecast ensemble sizes, source-run holdout, symmetric support, participant-level inference including explicitly handled ties, and a prospective forecast origin. Event-boundary windows and operators trained across an event boundary require reconstruction; a post-hoc label mask does not undo fitting leakage.

No positive H1/H2 result, exported history gain, or successful lag-1 map alone closes this stronger gate. Without an amended C2/C3 protocol, report these questions as not tested.

## 11. Freeze, deviations and decision rules

| Gate | Required evidence | Failure consequence |
|---|---|---|
| G0: identity/disclosure | Correct September export hashes, actual software/config snapshots, exposure statement, protocol hash and external timestamp | Remains an unregistered draft |
| G1: primary label/recording identity | Consistent source recording labels, source-run duplicates/crops resolved, within-participant acquisition strata | Exclude ambiguous pairs; no pure-seizure claim |
| G2: measurement comparability | Same transformation recipe, feature/fallback signature and comparable contact/reference policy; endpoint masks/index mapping verified | Affected primary contrast is not confirmatory |
| G3: numerical support | Endpoint-level computed/sufficient status, >=30 centers and >=50% support; >=20 paired participants per hypothesis | Endpoint METHOD-LIMITED; p=1 only for Holm accounting |
| G4: implementation review | Correct extraction/aggregation/statistics verified independently using bounded real-file and synthetic checks | Do not execute confirmatory tests |
| G5: stronger inference | Source events, training-only preprocessing, temporal support, null-qualified held-out estimator and separate C2/C3 amendment | C2/C3 remain not tested |

Do not tune thresholds, directions, source versions or endpoints after inspecting their effects. Every deviation requires a dated reason and exposure disclosure; effect-informed deviations are exploratory. Preserve the original result, missingness and failed method gates. A new export or reprocessing is a new input freeze, not an invisible update.

**Verdict vocabulary:** PASS applies only to its named test or gate; PARTIAL PASS means only the stated subset passed; METHOD-LIMITED means the intended measurement/inference could not be supported; INCONCLUSIVE means available evidence is insufficient; FAIL identifies a failed specified criterion. None means “all of NDT validated.”

## 12. Outputs and current status

Release the corrected audit and hashes, protocol and amendments, support/exclusion flow, participant-level paired effects, primary raw/Holm-adjusted p-values, descriptive secondary results including negative findings, code/environment and exact commands. Prior analyses remain disclosed. The old and new exports are never treated as independent participants or independent replication cohorts.

Completed for this revision: source correction, new-family coverage review, revised hypothesis/endpoint hierarchy and explicit measurement gates. Not completed: external registration, source-level channel/event adjudication, primary or secondary effect estimation, inferential extractor qualification, simulation pilot, prediction/reachability reconstruction or C2/C3 testing. The next step is to close G1–G4 without changing the declared hypotheses in response to outcomes.
