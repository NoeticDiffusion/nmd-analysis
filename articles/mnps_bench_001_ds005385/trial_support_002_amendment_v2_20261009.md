# TRIAL-SUPPORT-002 amendment v2 — matching boundary guards

Date: 2026-10-09. This amendment applies the independent FILTER-SUPPORT-001 boundary results without changing either estimator.

- Internal trial boundary margin: `g_trial = 2 s` at both ends.
- Physical recording edge margin: `g_recording = 4 s`, applied only to candidate windows lying within four seconds of the actual recording start or end.
- The six pilot task intervals lie well inside their recordings (minimum start margin 571.432 s; minimum end margin 12.318 s), so `g_recording` does not remove any pilot task-window support.
- Snap each bound inward to the 250 Hz grid. Anchor 4-second and 20-second step grids at the inward-snapped trial start. Do not bridge trials.
- The exact shifted full-v3 load-13 window must also pass the recall-boundary replay at its measured new gap.

The v1 support gate remains at least four distinct eligible trials per participant × condition × load. It is a bounded readiness rule, not inferential evidence or a universal scientific threshold. QC is condition-blind; labels are joined only for the final participant-level balance table.
