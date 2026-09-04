# 05 — NeuralManifoldDynamics: measurement contract and NDT boundary

**Source repo (canonical):** `H:\SourceRepo2\NeuralManifoldDynamics`  
**Contract paper:** `project/articles/NeuralManifoldDynamics/NeuralManifoldDynamics A Versioned Measurement Contract for Low-Dimensional Neural-Manifold Trajectories.typ` (+ S1–S6)  
**Code package:** `mndm` (`mndm/src/mndm/__about__.py`: `__version__ = "2.5.0"`)  
**Guides:** `mndm/Output_variables_guide.md` (documents the **2.6** surface plus v3 Round 1 `/dynamical_families/`, Round 2 validity certificate, Round 3 inferential grain, and Round 4 `/support_signature/v1/`), `mndm/CONFIG_GUIDE.md`, `mndm/src/mndm/reporting/schema_docs.md`, `mndm/src/mndm/reporting/dynamical_families.md`  
**Release notes:** `RELEASE_NOTES_v2.5.0.md`, `RELEASE_NOTES_v2.6.0.md`, `CHANGELOG.md`

**Copy in this repo (not canonical):** `j:\repos\nmd-analysis\articles\NeuralManifoldDynamics\` holds (i) an older methods draft (`NeuralManifoldDynamics.typ`, title *A Measurement Model for Robust 3D and Stratified 9D…*) and (ii) a snapshot of the contract paper **without** S1–S6. Live code, changelog, and supplements live in SourceRepo2.

**Coma pointer only:** `H:\SourceRepo2\NeuralManifoldDynamics\project\articles\coma` is a draft pointer. I-CARE / recovery-linked geometry empirical work lives in **this** repo (`nmd-analysis`), not in the NMD measurement-contract paper.

---

## Inventory

| Object | Path / identity | Frozen? |
| --- | --- | --- |
| Package version in code | `mndm.__version__ = "2.5.0"` | Code identity |
| Root README release line | NeuralManifoldDynamics **2.5.0** | Docs lag |
| Contract manuscript | v **2.5.0** (abstract, S1, S6) | Paper freeze |
| HDF5/schema guide | **MNDM 2.6** measurement surface | Guide ahead of paper |
| Jacobian metrics / FTR / Q-gate | `RELEASE_NOTES_v2.6.0.md` | Code+notes, not in contract paper |
| Schema id for anchored coords | `mnps_tensor_spec_v2_1` / `mndm.coordinate_layer.v2.1` | Intentionally retained 2.1 names |
| Geometry invalidity | `standard_invalidity_v1` (v2.4) | Always-on |
| Dynamical families | `mndm.diffusion_geometry.v1`, `mndm.committor.v1`, `mndm.finite_amplitude_resilience.v1` | Opt-in, gated; HDF5 `/dynamical_families/{diffusion,destination,resilience}/v1` |
| Jacobian-derived families | `mndm.jacobian_metrics.v1`, `mndm.finite_time_response.v1`, `mndm.residual_covariance_proxy.v1`, `mndm.stochastic_reachability.v1` | Additive on `J_hat` |

**Layer:** `measurement_contract`  
**Evidence class:** `internal_validated` for export/serialization; `plausible` for NDT-chart alignment; `speculative` for biological identity of `[m,d,e]`.  
**Flagship role:** `main_text_anchor` for the NDT/NMD split in §5; `supplement` (S2) for HDF5 paths, gates, and estimator defaults.  
**Claim ceiling:** NMD serializes a versioned observation chart and selected chart-level estimators; it does not identify latent \(X_t\), and v2.6.0 derived metrics are mathematical measurements with provenance, not cohort statistics or biology.

---

## Executive take for flagship (≤15 lines)

The exact sentence that should appear in NDT v2 §5:

> **NeuralManifoldDynamics is a versioned empirical measurement contract that implements selected MNPS and local-dynamics quantities; MNPS is an observation chart through which some NDT quantities can be estimated, not the theory itself.**

Supporting lines (keep in §5, not in the sentence):

- NDT owns latent \(X_t\), drift \(b\), diffusion \(a\), accessibility, landscapes, and control. NMD owns windows, transforms, coverage, the feature→chart map \(W_{9D}\), the fixed projection \(P_{\mathrm{fixed}}\), HDF5 names, and particular estimators.
- Do **not** write NDT = MNPS → MNJ → reachability.
- `J_hat` under `/jacobian` is an **MNJ**: a Jacobian estimated in an MNPS chart, not a generic \(J(X_t)\).
- v2.6.0 Jacobian Metrics v1 and Finite-Time Response v1 are per-recording mathematical measurements with validity/provenance. They are **not** biological claims, **not** cohort statistics, and **not** S3-licensed empirical NDT \(\alpha/\omega/G_{\mathrm{peak}}\) (`RELEASE_NOTES_v2.6.0.md`). Theory \(G_{\mathrm{peak}}\) serializes as FTR `g_peak_over_horizons`, not as a jacobian_metrics field.
- `mndm.dynamical_families` is a separate family from MNPS coordinates and from Jacobian-derived `mndm.dynamics`. Diffusion geometry, committor, and FAR carry explicit `not_testable` / qualification gates. Stochastic reachability is gated: no silent derivative-residual → \(Q\) conversion; summarize currently does not emit computed \(W_Q\). Canonical HDF5: `/dynamical_families/{diffusion,destination,resilience}/v1`. Schema IDs unchanged. Legacy `/orthogonal_dynamics/` is read-only. I-CARE / analysis-repo coma reachability (e.g. `tube_d_eff_median`) is **not** `mndm.stochastic_reachability.v1`.
- v3 Round 2 adds sibling certificate fields `computation_status`, `measurement_validity`, and `claim_status` on family and local-dynamics v1 groups. Value existence is not regime validity; regime validity is not an NDT license. New writes set `claim_status=no_biological_claim` and do not emit `ndt_licensed`. Diffusion, when enabled, is `computed`/`not_assessed` if the estimator has support; OD-TQ1 id/hash in `provenance` are method tags, not a compute gate and not `translation_qualified`. Destination and FAR still require protocol plus TQ stamp for `translation_qualified`. Jacobian metrics and FTR stay `not_assessed` when computed. `validation_level` is a method-validation tag, not `measurement_validity`. Legacy readers must fill missing fields as `not_recorded` and must not infer TQ or claim licensing.
- v3 Round 3 records nested `grain/` on the same groups (`native` / `parent` / `biological_unit=subject` / `repeated_measure` / `direct_between_subject_inference=forbidden`). A window or HDF5 file is not a participant. Ingest does not yet refuse analysis-side `N=windows` pooling. Legacy missing grain fields are `not_recorded`; do not infer `window` from series.
- v3 Round 4 adds `/support_signature/v1/` (`mndm.support_signature.v1`): per-9D coordinate `source` (direct vs policy fallback, `semantic_equivalence=false` for entropy/`e_m` substitutions) plus one modality capability row (`spread=gated`, FAR `resilience=perturbational_only`, fMRI MNJ `limited`). `coords_9d` present is not the same feature support and not the same modality capability. This is metadata, not `geometry_contract` and not an NDT license. Legacy missing fields are `not_recorded`; do not infer `chart_3d=yes` from `/mnps_3d`.
- Simulator C2 (C2-G1 DEV stop, `ndt-simulator` diary 100) does **not** authorize a committor/v2 product. NMD’s `mndm.committor.v1` stub is not that authorization.

---

## Current released objects

Convention: **implemented?** = serialized by the current summarize writer when support/config allow. **Validity gate** = the documented refusal, not a silent zero. NDT counterparts are theoretical objects; the chart is not identity.

| HDF5 path | Object / schema | NDT theoretical counterpart | Implemented? | Validity gate | Claim ceiling |
| --- | --- | --- | --- | --- | --- |
| `/time`, `/window_start`, `/window_end` | MNPS grid | observation time base for \(x_t\) | yes | `geometry_contract.time_grid` (`dt`, finite/non-positive bounds) | Windowed ingest time, not latent time |
| `/mnps_3d` `[T,3]` | canonical chart \(x_t=[m,d,e]\) | coarse measurable state; **not** \(X_t\) | yes (core) | drop non-finite rows; `min_axis_coverage` default 0.3; `geometry_contract` | Operational proxy families under the release map; not unique biological axes |
| `/mnps_3d_dot` | Savitzky–Golay \(\dot x\) (EEG `window=7, polyorder=3`; fMRI `5/2`; central-diff fallback) | chart velocity, input to MNJ | yes | segmented derivative; boundary SG not post-trimmed | Estimator-limited \(\dot x\), not \(b(X,t)\) |
| `/coords_9d/values` `[T,9]` | `[m_a,m_e,m_o,d_n,d_l,d_s,e_e,e_s,e_m]` | stratified chart \(x_t^{(9)}\) | yes if `mnps_9d.enabled` | separate validity from 3D; non-finite 9D can drop shared grid | Masking-reduction chart, not nine biological primitives |
| `x = coords_9d @ P_fixed` | `mnps_3d.mode = from_v2`; `P_fixed` from `mnps_projection.v1_mapping`; L2-normalized columns + coverage renormalization | NDT 9D→3D recomposition idea | yes | degraded-support class recorded, not equated to full support | Release-fixed weights (EEG e.g. \(m\leftarrow 0.62 m_a+0.55 m_e+0.45 m_o\)); not learned optima |
| `/coords_*_subject_anchored`, `/coords_*_cohort_anchored` | MNDM 2.1 layers | within- vs between-subject geometry | yes when configured | `primary_coordinate_layer` attr; skipped contracts logged | Subject-anchored for trajectory/Jacobian shape; cohort-anchored for group contrast — do not mix |
| `/feature_anchors/*` | frozen center/scale | not a dynamical object | yes when cohort-anchored | `anchor_id` / `anchor_hash` | Feature scaling only; **not** `/anchor_state` |
| `/nn/indices` `[T,k]` | Euclidean kNN in chart space, default `k=20` | neighbourhood for local \(J\) | yes if Jacobian path | finite `mnps_3d` required before kNN | Chart neighbourhood, not anatomical neighbours |
| `/jacobian/J_hat` `[W,3,3]` | MNJ: ridge local affine \(\dot x \approx J(x-x_{\mathrm{ref}})+b\); defaults `super_window=3`, `ridge.alpha=1.0`, `whiten=true` (`config_ingest_common_eeg.yaml`) | chart Jacobian \(J(x,t)=\partial b/\partial x\) **in MNPS** | optional, usually on for EEG | support seconds/epochs; finite rows; hard condition-number drop (`geometry_contract`); no clamp | MNJ, not generic \(J(X_t)\); not a unique biophysical SDE |
| `/jacobian/J_dot`, `/jacobian/centers`, affine_reference/intercept | window centres + meta-plasticity proxy | — | with `J_hat` | invalid windows removed, counted | Temporal difference of MNJ, not \(\dot J\) of latent \(f\) |
| `/jacobian/derived_metrics/v1/` | `mndm.jacobian_metrics.v1`: `spectral_abscissa` \(\alpha\), `numerical_abscissa` \(\omega\) (Euclidean chart metric), `reactivity_gap`, `symmetric_rate_{min,max}`, `stable_reactive_flag`, `dynamical_regime`, `spectral_radius`, `frobenius_norm`, `trace`, `rotation_norm`, `henrici_departure` | NDT modal stability / reactivity summaries of \(J\) | additive when `J_hat` exists (v2.6.0) | NaN/−1 for invalid windows; zero-tolerance provenance | **Mathematical measurement + provenance. Not biology. Not cohort stats.** |
| `/jacobian_9D/J_hat` `[W2,K,K]` + `/jacobian_9D/derived_metrics/v1/` | same MNJ / metrics in 9D; metrics **not** synthesized from 3D | stratified \(J^{(9)}\) | optional | finite 9D; fMRI regional 9D block-J withheld by default (rank) | Direct 9D field only |
| `/finite_time_response/v1/{primary,stratified_9d}/` | `mndm.finite_time_response.v1`; primary propagator `time_ordered_expm`; `frozen_j_expm` comparator; `g_peak_over_horizons` is the serialized \(G_{\mathrm{peak}}\) analogue | finite-time tangent map of chart \(J(\cdot)\) | **opt-in** `local_dynamics.finite_time_response.enabled` | original-center gaps + observed time gaps are hard boundaries; `computation_status` ∈ {`not_requested`,`unavailable`,`invalid`,`computed`}; `validation_level` independent (default `model_derived`) | Not predictive; not perturbational; not FAR; **not S3-licensed empirical NDT** |
| `/residual_covariance_proxy/v1/` | `mndm.residual_covariance_proxy.v1` | **not** Itô \(a(x)\); not \(W_Q\) unless conversion frozen | library exists; **summarize does not emit** (no one-step transition residual) | `conversion_model: required_before_stochastic_reachability` for derivative residuals | Derivative residual covariance is not admissible \(W_Q\) |
| `/transition_residuals/v1/`, `/transition_residual_covariance_proxy/v1/` | opt-in cross-fitted one-step residual; recording-level PSD \(Q\) proxy | discrete innovation for reachability | residuals opt-in; proxy **not yet wired to** `W_Q` (`CONFIG_GUIDE.md`) | irregular `dt` → unavailable; `min_eigenvalue` PSD floor | Not biological process noise |
| `/stochastic_reachability/v1/{primary,stratified_9d}/` | `mndm.stochastic_reachability.v1` | NDT reachability / \(W_Q\) | **not emitted** by current summarize until admissible one-step \(Q\) | `compute_stochastic_reachability` refuses unless `q_time_semantics=one_step_transition_covariance`, `q_units=state_squared`, `conversion_model=not_applicable`; else `q_contract_not_admissible` | No silent derivative-residual → \(Q\). No computed \(W_Q\) in production summarize. **I-CARE analysis reachability ≠ this schema** |
| `/dynamical_families/diffusion/v1` (legacy `/orthogonal_dynamics/diffusion_geometry/v1`) | `mndm.diffusion_geometry.v1`; increment covariance; ingest `drift=None` | diffusion tensor \(a(x)\) | opt-in `dynamical_families.enabled` + family enabled | estimator support (samples, gaps, regular \(dt\)); `computed` + `not_assessed` when support holds; OD-TQ1 id/hash are provenance method tags, not a compute gate; `A_bD` / `R_b_over_a` are **`not_testable` / `independent_drift_not_supplied`** on ingest (NaN is not zero alignment); MNPS \(\dot x\) is **not** SDE drift; library C1 can consume an externally qualified chart \(b\) without changing `a_hat` (Gate C1-A); analysis owns identification of \(b\) (SL-005) | Chart-dependent increment covariance. Not Jacobian residual covariance. `computed` ≠ testable \(A_{bD}\) / \(R_{b/a}\). Not Itô \(a(x)\). |
| `/dynamical_families/destination/v1` (legacy `/orthogonal_dynamics/committor/v1`) | `mndm.committor.v1`; production adapter `local_law_dense_grid_o2b`; first-hit `estimate_committor` is a separate estimator | committor \(q\) to regimes A/B | stub + gated adapter | **not_testable** unless explicit A/B, disjoint regimes, multiple independent segments with both, reaction-coordinate contract; destination/FAR still need TQ stamp for `translation_qualified`; stage labels alone are not committor truth; O2b does **not** serialize \(V_{1/2}\) or \(\lvert\nabla q\rvert\); first-hit serializes `q_A_to_B` only | **Not committor/v2.** Simulator C2-G1 DEV stop does not authorize this as a recovered 2D Galerkin committor |
| `/dynamical_families/resilience/v1` (legacy `/orthogonal_dynamics/finite_amplitude_resilience/v1`; schema `mndm.finite_amplitude_resilience.v1`) | observed perturbation-outcome summary | FAR | opt-in | retrospective ingest → `not_testable` / `no_perturbation_protocol`; needs complete protocol fields + qualification certificate | Does not infer basins from Jacobian, FTR, or spontaneous trajectories |
| `/anchor_state`, `/anchor_state_dot`, `/anchor_quality`, optional `/anchor_coupling` | EAP \(a_t\); indices `vagal_index`, `sympathetic_index`, `anchor_index`, `vascular_index`; HRV v0.1 | NDT embodiment / control covariates (theory-side) | optional v2.3+ | NaN for invalid guarded components; HRV contamination flags | Additive body surface, **not** a fourth MNPS axis, not `feature_anchors` |
| `/blocks/*`, `/block_windows/*` | block-native v2; `source_window_index`; relative position | analysis windows, not a dynamical law | when `block_native` enabled | `block_native_qc`; membership mode (`midpoint_in_interval` / `fully_contained` / `overlap_frac_ge`) | Derived layer; not canonical MNPS grid. Event-locked sidecars similarly **not** canonical HDF5 unless promoted |
| `/labels/stage`, `/events/*`, `/epoch_id` | stage/event provenance | regime labels for later tests | optional | stage_mapping_qc | Labels ≠ committor truth |
| `/extensions/conventional_eeg/*`, coma pack | qEEG comparators; ICU proxies | not NDT objects | optional | multimodal coma biomarkers (`SSEP`,`NSE`,`GCS`,`S100B`) marked `unavailable` without sidecars | Comparator pack, not MNPS |
| `/provenance/geometry_contract/*` + `summary.json.geometry_contract` | always-on math validity | estimator domain | always | invalid rows/windows **dropped**, not clamped | Gate for downstream MNPS / MNJ / reachability-style use |
| `/extensions/e_kappa`, `/rfm`, `/o_koh`, `/tig` | EEG-first extras | not core NDT 4-layer objects | optional | documented as extensions | Do not promote to NDT core without a later decision |

**v2.6.0 claim box (quote-paraphrase):** “adds per-recording mathematical measurements and explicit validity/provenance; it does not add cohort statistics or biological claims.” Finite-time response is `model_derived` by default. ds003944 / ds003947 reruns are “internal descriptive output; not a group-level clinical claim.”

---

## NDT vs NMD ownership table

Filled from the **NMD contract paper** (Intro, Claims/Non-Claims, B.5 Interpretation boundary, S1) and NMD code/guides, then checked against NDT v2 sciencelead (`sl_1.md`, `sl_001.md` §5.4–5.5). Mismatches flagged.

| Layer | NDT owns (theory) | NMD owns (as actually documented) | Mismatch vs sciencelead freeze? |
| --- | --- | --- | --- |
| Latent theory | \(X_t\), \(dX=f\,dt+\sigma dW\), accessibility, landscapes, control | **None.** Paper: “does not claim to learn \(X_t\)”; “does not estimate the latent manifold \(\mathcal{M}\) from scratch.” | Aligned |
| Chart concept | measurable \(x_t\), 3D/9D idea, family grouping | exact \(z_t=\phi(Y)_t\), \(x^{(9)}=W_{9D}z_t\), \(x=P x^{(9)}\); EEG vs fMRI feature tables; MEG shadow map; ephys dedicated 9D map | Aligned. **Do not** treat MNPS as NDT. |
| Preprocessing | requirements/boundaries (coverage, no silent zero-fill) | windows (`fs_out=4` Hz, 8 s / 50% overlap EEG reference), SG derivatives, `robust_z→clip` / `log10→robust_z→clip`, ComBat optional, ICA/bad-channel, CSD optional | Aligned. NMD also owns **modality adapters** (BDF, NWB, FIF, WFDB) — sciencelead table under-specifies this; still NMD. |
| Local dynamics | mathematical \(J\), \(b\), \(a\), reachability, committor, FAR | **particular estimators:** kNN+ridge MNJ; Jacobian Metrics v1; FTR v1; gated \(Q\)/reachability; dynamical families under `/dynamical_families` | Sciencelead says NMD owns “particular estimators where implemented.” **True.** Gap: paper still talks “MNJ as second-order layer on MNPS” in a way that can be misread as theory identity — flagship must keep MNJ = chart Jacobian. |
| Interpretation | theoretical meaning of \(\alpha,\omega,a,W_Q,q,\mathrm{FAR}\) | what was serialized: paths, `computation_status`, `validation_level`, `claim_status=no_biological_claim` on orthogonal contracts | Aligned in v2.6 notes + orthogonal contracts. **Mismatch:** contract **manuscript is still v2.5.0** and does not document Jacobian Metrics / FTR / Q-gate. |
| Empirical studies | hypotheses / predicted dissociations | reproducible input measurement contract (HDF5 + manifests + hashes) | Aligned. **Mismatch if flagship cites NMD paper for coma/spindle *results***: those analyses live in `nmd-analysis`, not in the NMD methods paper. NMD S2 is audited *ingest* numbers (e.g. ds003838 export scale), not NDT clinical inference. |

**mndm/README.md mismatch (do not copy):** it glosses MNPS as “mobility, diffusivity, and entropy.” The contract paper and S5 freeze **metastability / deviation-from-balance / entropy–energetic-complexity** as *operational proxy families*. Flagship follows the contract paper, not the package README slogan.

**Older MNPS 1.2 vs 2.x:** 2.x splits feature surfaces vs coordinates vs anchoring vs geometry_contract. Flagship should cite 2.x, not 1.2.

---

## What NMD explicitly does NOT claim

From the contract paper Claims/Non-Claims box and Limitations (paraphrase; keep this ceiling in §5/S2):

- **No diagnosis, no consciousness-level inference, no condition interpretation at ingest.** Ingest does not adapt to contrasts of interest.
- **No claim that ingest-level proxies exhaust the theoretical meaning of `[m,d,e]`.** Chart labels are operational labels in the current release.
- **No unique biological identifiability** of projection weights, anchors, or axis names. Weights are release-fixed operational priors, not supervised optima. Chart stability under feature substitution remains a **future validation target**.
- **Does not learn \(X_t\) or \(\mathcal{M}\).** \(W_{9D}\) and \(P\) are versioned configuration, not contrast-adaptive embeddings.
- **MNJ is not a unique biophysical state equation** (S1, S5, Appendix B.4).
- **EEG channel groups are not homologues of fMRI networks.** MEG shadow mapping does not establish cross-modal biological equivalence. Neuropixels/LFP paths are rodent transport/QC, **no cross-species chart homology**, no MEG-like readiness score.
- **Not a benchmark** vs HMM/DyNeMo, CAP, LEiDA, microstates, CEBRA.
- **Embodied `anchor_state` is not a fourth MNPS axis** and not a replacement for `feature_anchors`. HRV v0.1 has no HF / LF/HF. ds006848 WM-HRV claims withheld (87.7% of 60 s windows overlap retrieval).
- **v2.6.0 derived local-dynamics layer:** not cohort comparison, not retrospective clinical audit, not biology (`CHANGELOG.md` / release notes). FTR `validation_level=model_derived` is not held-out predictive or perturbational validation.
- **Orthogonal contracts:** `claim_status = no_biological_claim`. Diffusion is not transition-residual covariance. Committor first-hit is not simulator Monte-Carlo / generator validation. FAR does not infer resilience from Jacobian or FTR.
- **Event-locked / spindle sidecars** are derived artifacts with their own provenance, not the canonical measurement surface.

---

## Estimator inheritance rule

NDT v2 should state (from NMD paper B.5 + sciencelead §5.5, tightened to NMD’s actual stack):

Any downstream Jacobian, metric, FTR, reachability, diffusion, committor, or FAR claim **inherits the validity limits of**, in order:

1. **Raw measurement** (modality, montage, NWB/FIF/BDF/WFDB adapter, rodent vs human).
2. **Preprocessing** (resample, reference, ICA, masking, CSD failure reasons).
3. **Feature construction** \(\phi(Y)\) (window 8 s / step 4 s EEG reference; ephys 2 s / 1 s; MEG `features_projection_z` vs degenerate raw robust-z).
4. **Chart definition** \(W_{9D}\), \(P_{\mathrm{fixed}}\), subject vs cohort anchoring, coverage renormalization, `e_m` nine-level fallback (`embodied_arousal_proxy_source`).
5. **Local estimator** (SG \(\dot x\); kNN \(k=20\); ridge MNJ; Jacobian Metrics on **that** \(J_{\mathrm{hat}}\); FTR on **that** field and observed gaps; \(Q\) only from one-step transition residuals; dynamical families only after translation qualification).

`geometry_contract` is the machine-readable stop: invalid MNPS rows / Jacobian windows are **removed**, not clamped. Capability flags that are `false` mean **no serialized surface**, not a measured zero (`Output_variables_guide.md`).

**Coordinate-layer inheritance:** local-dynamics outputs preserve their primary coordinate contract and **do not merge** subject- and cohort-anchored series (`RELEASE_NOTES_v2.6.0.md`). Mixing layers silently is a contract violation.

**Dynamical families vs dynamics inheritance:** `/dynamical_families/*` “do not alter `/mnps_3d`, `/coords_9d`, or `/jacobian`” (`schema_docs.md`). Legacy `/orthogonal_dynamics/` is read-only. FTR is not FAR. Residual covariance is not \(a(x)\).

---

## Terminology to freeze

| Term | Freeze as | Do not write |
| --- | --- | --- |
| **NDT** | theory of latent dynamics and controlled accessibility | “NDT = the MNDM pipeline” |
| **NMD / NeuralManifoldDynamics / MNDM** | versioned ingest measurement contract (`mndm` = package/CLI name) | “NMD is the theory” |
| **MNPS / `mnps_3d`** | observation chart \(x_t=[m,d,e]\) through which some NDT quantities can be estimated | “MNPS is NDT”; README’s “mobility/diffusivity” gloss |
| **Stratified MNPS / `coords_9d`** | release-bound 9D operational decomposition | uniquely correct latent primitives |
| **\(P_{\mathrm{fixed}}\)** | configured 9D→3D map `mnps_projection.v1_mapping`, L2-normalized + coverage-renorm | learned projection; identity “mean of 9” |
| **MNJ** | Jacobian **estimated in an MNPS (or stratified MNPS) chart** = `/jacobian/J_hat` (3D) or `/jacobian_9D/J_hat` | generic \(J=\partial f/\partial x\) on \(X_t\); “the” neural Jacobian |
| **`mndm.dynamics`** | Jacobian-derived surfaces: metrics v1, FTR v1, residual/transition \(Q\), stochastic reachability | dynamical_families |
| **`mndm.dynamical_families`** | diffusion, destination (committor), resilience (FAR) — HDF5 tree `/dynamical_families`; schema IDs unchanged | “extra Jacobian metrics”; old package `mndm.orthogonal_dynamics` |
| **\(\alpha\), \(\omega\)** | `spectral_abscissa`, `numerical_abscissa` of **exported MNJ** in Euclidean chart metric | latent modal stability of \(X_t\) |
| **FTR** | time-ordered expm of the MNJ field; `model_derived` unless a higher validation_level is recorded | FAR; predictive impulse response |
| **\(W_Q\)** | discrete one-step transition-residual covariance with frozen time semantics | derivative-residual covariance; Itô \(a\) |
| **committor/v1** | NMD schema `mndm.committor.v1` (gated first-hit / O2b adapter) | **committor/v2**; C2 Galerkin recovery |
| **C2 stop** | `ndt-simulator` C2-G1 DEV: no candidate basis survived; held-out closed; method-limited, not biological falsification of NDT | “NMD implements the C2 committor” |
| **Versions** | Paper/package identity **2.5.0**; Jacobian-metrics/FTR/Q-gate documented as **2.6.0** in release notes + output guide. Sub-schemas may still say `v2.1`. | Treat 2.5.0 paper as already containing 2.6.0 objects |
| **EAP / `anchor_state`** | additive embodied surface \(a_t\) | fourth MNPS axis |
| **`feature_anchors`** | cohort/external feature scaling | embodied anchors |
| **Block-native / event-locked** | derived analysis layers joinable by `source_window_index` / window id | canonical MNPS export |

---

## Suggested manuscript placement

- **Main §5 (measurement contract):** the exact sentence above; ownership table (short); MNPS-as-chart; MNJ definition; inheritance rule in one paragraph; v2.6.0 mathematical-not-biological box; pointer that empirical spindle/coma/DANDI tests use this contract as **input**, with results owned by NDT empirical sections / `nmd-analysis`.
- **Supplement S2 (measurement contract):** this file’s object table; EEG/fMRI `P_fixed` weights; Jacobian defaults (`k=20`, ridge 1, super-window 3, whitening); `geometry_contract`; anchoring layers; orthogonal gates (`not_testable` reasons); Q-admissibility; C2 vs `committor.v1` boundary; version map 2.1→2.6.0.
- **Figure 1 (dashed boundaries):** sciencelead Figure 1 already wants latent state / observation map / EEG–LFP–fMRI / MNPS–NMD **below** the dynamical glyphs. Draw three dashed boxes: **latent** (\(X_t,f,a\)) · **measurement** (\(Y\to z\to x= P W z\), NMD) · **inference** (MNJ, \(\alpha,\omega\), FTR, gated \(W_Q\), orthogonal families). Do not draw a single arrow MNPS→MNJ→reachability as the theory spine.

---

## Open questions / contract gaps

1. **Version split:** code `__version__` and contract paper are **2.5.0**; `Output_variables_guide.md` and `RELEASE_NOTES_v2.6.0.md` already define Jacobian Metrics, FTR, and Q-gates. Flagship must cite **which** contract readers inherit. Do not imply the Typst methods paper already freeze-documents 2.6.0.
2. **Stochastic reachability not emitted:** summarize has no exported one-step transition residual as a live \(W_Q\) input; transition-residual proxy “is not yet wired to stochastic reachability.” Downstream NDT reachability claims that assume an NMD `W_Q` file are **false** unless a later release emits it.
3. **Derivative residual ≠ \(Q\):** `make_derivative_residual_covariance_proxy` sets `conversion_model: required_before_stochastic_reachability`. No YAML permits silent conversion (`CONFIG_GUIDE.md`).
4. **Committor not testable without A/B regimes + qualification:** stage labels are insufficient. Simulator **C2-G1 DEV stop** (no 5×5/7×7/9×9 basis DEV-eligible; held-out closed) does **not** authorize committor/v2. NMD `mndm.committor.v1` remains a gated stub/adapter, including sleep-committor scouts that must not be promoted.
5. **FAR needs an explicit perturbation protocol** (`no_perturbation_protocol` on standard retrospective ingest). Jacobian/FTR cannot substitute.
6. **Diffusion geometry:** adapter currently passes `drift=None` (MNPS \(\dot x\) is not an independently qualified SDE drift). `computed` increment covariance is not testable \(A_{bD}\) / \(R_{b/a}\); those scalars are explicit `not_testable` / `independent_drift_not_supplied`, not silent NaN-as-zero. Jacobian residual is not \(a\). OD-TQ1 tags are method provenance, not a compute gate. Library C1 (ingest M1–M2, SL-005 freeze) can consume an externally qualified chart-space \(b\) without changing `a_hat`. Identification of \(b\) (cross-fit, embargo, contamination audit) belongs in **this** analysis repo, not ingest. C2 residualization is not authorized.
7. **Chart invariance untested:** paper states feature-substitution / weight-perturbation stability is future work. NDT must not treat \(P_{\mathrm{fixed}}\) as identified.
8. **MEG / ephys ceilings:** MEG exploratory (ds003645 5-subject pilot, readiness 0.7879); d-family EEG–MEG sign inversion is a documented modality-space fact, not a chart bug. Ephys is rodent transport/QC only.
9. **fMRI regional 9D block Jacobians disabled by default** (rank deficiency). Do not cite “regional MNJ” as uniformly available.
10. **`e_m` fallback chain** weakens cross-dataset identity; comparisons need `embodied_arousal_proxy_source`.
11. **Coma empirical ≠ NMD paper:** I-CARE reachability analyses (e.g. `tube_d_eff_median` family) are `nmd-analysis` empirical products on an NMD export, and they inherit older reachability estimators that **may not** be the v2.6.0 gated `mndm.stochastic_reachability.v1` surface. Flagship must not collapse those into the measurement contract.
12. **Family CONFIG:** `CONFIG_GUIDE.md` documents `local_dynamics` and `dynamical_families`. The family YAML is overlay-only (`dynamical_families.enabled`); common EEG/fMRI/ephys must not import it. S2 should show both trees. Canonical write `/dynamical_families/`; legacy read `/orthogonal_dynamics/`.
13. **Reproducibility bound:** ds003059 hash match (`n_jobs` 1 vs 4) is same-environment replay, not cross-BLAS identity.

---

### Tag recap for intake

| Field | Value |
| --- | --- |
| **Layer** | `measurement_contract` (objects above); `local_dynamics` / `possible_futures` only as *chart-level estimators*, never as latent identification |
| **Evidence class** | `internal_validated` (export, gates, unit/writer tests); `plausible` (NDT-aligned chart); `rejected` for silent \(Q\) conversion and for C2→committor/v2 promotion |
| **Flagship role** | `main_text_anchor` (§5 sentence + ownership); `supplement` (S2 table); `exclude` NMD clinical numbers from theory identity |
| **Claim ceiling** | NMD is the versioned empirical measurement contract for selected MNPS/local-dynamics quantities; MNPS is an observation chart, MNJ is a Jacobian in that chart, and v2.6.0 derived metrics are mathematical measurements with validity/provenance — not biology, not cohort inference, not latent \(X_t\). |
