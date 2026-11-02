# Diary 288 — independent sleep increment-support review

Date: 2026-09-08

Measurement question: can the accepted sub-99 diffusion candidate increments
be audited against the pinned H5 epoch geometry and stage labels while
preserving unknown temporal support and avoiding a tensor rerun or new
estimator semantics?

Gate: bounded candidate-only structural and label audit under
`increment_support_policy_20260908.md`. The audit must check exact epoch IDs,
indices, bounds, raw-file identity, touching windows, positive exact dt,
stage-code/unknown flags, selected query coverage and neighbor counts. It
must also enumerate the complete adjacent H5 pool independently of selected
candidate membership. Feature/filter support and neighborhood stage purity
remain tri-state and cannot become qualified from labels or window bounds.

The final runner is `src/increment_support_audit.py`; the final output is
`results/increment_support_sub99_20260908_r2`. It reads the pinned H5 and
candidate tables, validates the upstream candidate-only manifest gates, and
writes structural/label tables. It does not rerun diffusion tensors, refit
covariance, tune neighborhoods, or claim historical membership.

Producer evidence was independently inspected first. The H5 contains 1,068
30-second epochs on a 30-second step through 32,040 seconds, while the raw
recording metadata gives 32,064 seconds and a 24-second unrepresented tail.
The nine code-8 epochs are retained and represent PSG disconnection. The
embedded time-grid contract resolves the apparent generic 8-second/4-Hz
root-attribute difference as a generic metadata layer rather than a shifted
runtime epoch clock. Effective preprocessing/filter support is still
UNKNOWN: the accepted output does not link the executed preprocessing branch,
raw EDF hash, filter/resampling edge padding and effective length, or a
per-epoch disconnection support mask. Robust normalization is recording-global
over the 1,068 rows, so exact epoch alignment does not establish stage purity.

Independent tests added in
`tests/test_increment_support_audit_independent.py` cover: separation of
structural admissibility from code-8 stage eligibility; an epoch-ID gap in a
selected pair; fractional candidate and H5 IDs; fail-closed malformed bounds;
exact stage-code mismatch; duplicate selections; complete adjacent-pool
enumeration; wrong input pins before output creation; and empty selected
membership before export.

Validation:

- focused engineer and independent increment tests — **15 passed**;
- complete article suite with the repository source paths — **80 passed**;
- independent H5/CSV recomputation — **PASS** for all 21,360 selected rows,
  all 1,067 adjacent pairs, and all reported counts;
- `handover/verify_increment_support_coordinator.py` — **PASS**;
- output hash index and sidecar — **match**;
- input before/after hashes for H5, candidate files, policy and runner —
  **match**.

Observed final counts: 21,360 candidate rows, all structurally admissible;
16,869 same-known-stage rows structurally eligible; 1,067 adjacent pool rows,
976 known-equal endpoint pairs and 10 code-8-touching pairs. The report keeps
`feature_filter_support_status: not_assessed`,
`neighborhood_stage_purity_status: not_assessed`,
`historical_membership_status: not_claimed`, and
`full_qualified_rows: null`. Unknown stage rows are represented explicitly;
they are not converted to zero-qualified support.

Provenance: H5 SHA-256
`3657fd599bbcddb774aa8ae237cb017f0a566c3a21e0877f4b43634d0d98a427`;
runner SHA-256
`b8ae3eb61ef2cdb6009cff79f37cc17f4149dcf20f4057d72305e1eada8ce15b`;
output audit-manifest SHA-256
`6b5c4a8cdb62d1bdfa4c166312b73bb035ae48fc2d63384fd7cbda4a09ad1145`.

Verdict: **PASS for the bounded structural/label gate; METHOD-LIMITED for
feature/filter support.** The safe claim is provenance-pinned agreement with
the accepted H5 and explicit adjacent-pool/stage handling. Full temporal
support, stage-conditioned neighborhood purity, historical membership and
biological interpretation remain unestablished. The next step is to export
resolved preprocessing and filter-padding provenance and a conservative
support mask; until then the qualified status stays `not_assessed`.
