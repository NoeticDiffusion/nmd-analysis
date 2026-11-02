# C2 candidate specification — 2026-09-30

## Status

**Candidate only; not qualified and not an authorization to score outcomes.**
This v1 note is superseded for training-row cross-fitting and scalar units by
`c2_accessibility_candidate_20261001_v2.md`. Keep this file as the historical
candidate definition; do not implement its original shared-scale OOF rule.
This is an article-local proposal for one C2 accessibility feature. The
preregistered continuous protocol defers C2, the fold-safe H5 preflight did not
read coordinate values, and Gate 8 remains closed. This file does not amend the
source preregistration. No real H5 chart coordinates, future chart values,
stage fields, C1/C2 scores, or condition effects were read or computed for this
proposal.

## Primary candidate

For each 3D `[m,d,e]` forecast origin `t`, estimate a local conditional
distribution of the h1 future chart endpoint from outer-training participants.
Let `z=(x-center)/scale`, where `center` and coordinate-wise `scale` are the
same outer-training, participant-balanced median/IQR transform used for the
fold's C1 chart coordinates. The centering cancels in distances and covariance;
the IQR scale fixes a common dimensionless unit.

1. Build a training transition library from eligible pairs `(x_j, x_{j+1})`
   belonging only to the outer-training PID roster. A pair must be in the same
   recording and verified segment, have exact consecutive row identities
   (`target_epoch_id = epoch_id + 1`), have a nominal 30-second timestamp
   difference (tolerance 0.01 s), pass coordinate QC at both ends, and have
   externally hash-bound causal source support at both ends. The transition
   table must not contain stage or condition labels. Missing or unsupported
   pairs represented in the supplied candidate-pair table are excluded with
   mutually exclusive first-failure counts/reasons; never interpolate or fill
   them.
2. At an apply origin, use only the present 3D state `x_t`, current source
   support, current coordinate QC, and its identity/time metadata. For each
   outer-training PID, find its nearest eligible training origin in scaled
   Euclidean 3D state space. Retain the closest transition for each PID, then
   take the nearest `k=32` distinct training PIDs. This prevents long or dense
   recordings from dominating the local distribution.
3. Reject the feature if fewer than 32 distinct training PIDs are available,
   or if the 32nd-neighbor radius exceeds the training-only support threshold.
   The threshold is the linear-method 95th percentile of leave-one-PID-out
   32nd-neighbor radii. Calibration uses one participant-balanced median
   training-origin query per library PID and the same nearest-transition-per-
   other-PID distance rule used for apply queries. It is fitted without apply
   PIDs or apply targets.
4. Let `Y_1,...,Y_32` be the selected training **future endpoints** transformed
   by the shared outer-training scale. Compute the ordinary unbiased sample
   covariance `Sigma_h1(t)=cov(Y_1,...,Y_32)` and the single scalar
   `A_C2(t)=log(det(Sigma_h1(t)))`. Do not add a ridge term or use a
   pseudo-determinant. A singular/non-positive-definite covariance is
   unavailable with an explicit reason, not zero.

The output unit is a log determinant in outer-training-IQR-scaled 3D chart
coordinates. It estimates local training-fold future-state dispersion around
the queried present state. It is not the unavailable H5 Jacobian, a direct
physical accessibility measurement, a causal quantity, or a claim about an
unrestricted future law.

## Leakage boundary and fitting

- Outer split stays the frozen five-fold participant GroupKFold. Every
  training transition, scale, support threshold, and neighbor library is
  restricted to the outer-training PID set. No apply-PID chart target enters
  the feature or its calibration.
- When constructing `A_C2` for rows that train the C2 outcome model, use
  participant-level cross-fitting: for a training PID query, fit its transition
  library and radius threshold on the other outer-training PIDs only. Reuse the
  same outer-fold chart scale for all such feature rows. This prevents a
  training origin's own PID future values from entering its feature.
- Apply queries contain current chart values only. The estimator API has a
  separate exact query schema and rejects target/stage/outcome columns. It has
  no HDF5 reader.
- Keep canonical 3D `[m,d,e]` as the primary representation and h1 as the
  primary horizon. A 9D or h2/h4 extension would need a separately dated
  amendment and its own support qualification.

## Comparator and eventual qualification

The intended C2 contrast is `B` versus `B + A_C2` on the same eligible
origin-target rows at h1. `B` is current 3D state, standard pre-origin EEG
spectral features, recording-relative time, and prespecified current QC;
`B + A_C2` adds exactly the one scalar above. This note does **not** lock the
C2 outcome model or score. Reusing the C1 Ridge/MSE reduction would test only
whether `A_C2` adds conditional-mean prediction; it would not establish an
improved full future law from a covariance feature. A later C2 protocol must
choose a score aligned to its claim (or explicitly narrow the claim), freeze
the estimator and preprocessing, and require identical support and evaluation
rows. The fold-safe chart H5 files include `/features_raw`, a per-row
original-scale feature matrix with candidate EEG bandpower, ratio, entropy, and
Hjorth fields. The inspected H5 provenance does not certify its temporal or
source-quality support, so those arrays are candidate inputs and are not yet
admitted to `B`. Keep the named spectral baseline and withhold scoring until
the row mapping, temporal support, source-quality support, and fold-local
preprocessing gates pass; do not silently weaken the comparator to chart-only.
Handover 532 records the feature inventory, producer contract, and
qualification requirements. Report per-PID/per-recording coverage and preserve
unavailable reasons. Any later score/effect run requires the separate
protocol/hash freeze, review, and authorization gates.

Qualification before any effect analysis must establish: exact transition
support/hash binding; no cross-PID fold leakage; participant-level cross-fitting
for training features; apply-query target invariance; gaps, invalid QC,
singular covariance, and out-of-radius inputs fail closed; stable schema/unit
provenance; and adequate participant support. The included synthetic checks
exercise only the estimator contract and leakage boundary. They do not qualify
the feature on BOAS data or open any gate.

## Source basis and current limits

Handover 530 states that the fold-safe H5 surface has 3D/9D charts, identity,
time, QC/support metadata and nearest-neighbor indices, but no qualified
`a_hat`, effective dimension, predictive covariance, `kappa`, or MNJ predictor.
Handover 531 records an outcome-blind support map only; it checked chart array
shapes without reading their values. The source preregistration explicitly
defers C2 and bars relabeling a Jacobian, FTR field, stage contrast, or
deterministic baseline transform as an accessibility feature. This candidate
avoids the existing unqualified nearest-neighbor export by constructing a new
training-PID-only local future covariance, but still requires prospective
review and qualification.

The module is an estimator interface, not an H5 runner. The actual chart arrays
were not loaded to fit or qualify it. The candidate remains **unqualified**
until separately authorized real-data support/leakage validation and protocol
review are complete.

The estimator can count failed rows only when the upstream builder supplies a
candidate transition row. An origin with no target identity at all is absent
from this table; the existing support-map/preflight layer must report that
missing-pair count and preserve its reason. If upstream supplies too few
distinct supported training PIDs after exclusions, atlas fitting fails closed.
Apply feature queries do not contain future target identities or values; later
outcome eligibility must come from the separate hash-bound support map.
