# Sleep study roles and boundaries

This article uses the parent repository's research conventions. Preserve
unrelated edits and the original `articles/aa_template`.

- Coordinator: define the current question and scope, reserve diary filenames,
  integrate work, and distinguish engineering readiness from scientific claims.
- Implementation engineer: maintain article-local `src/`, `config/` and tests;
  reuse analysis-package readers and estimators. Run bounded, explicit inputs
  into a fresh output directory and retain source/config/code provenance.
- Independent reviewer: inspect final code and tests, then inspect actual pilot
  artifacts before the coordinator interprets numerical results. Record findings
  and their resolution in `peer_review/`.

Use Luna subagents as requested by the user. Record only model/effort settings
actually applied. Write substantial work to the repository's `project/diary/`
with coordinator-reserved numbers; put commands and run evidence in `handover/`.

Keep canonical MNPS definitions and producer validity/qualification unchanged.
Unknown, unavailable and invalid values must remain visible, never filled with
zeros. A recording-level measure cannot become a sleep-stage measure through
label replication. Timestamp alignment does not establish stage purity across
an estimator's full temporal support. Do not bridge gaps or mix coordinate
contracts. Participants, not overlapping epochs, are the unit for population
inference.

The initial sub-99 run is a development and support pilot. No cohort inference,
estimator tuning, empirical M3 qualification or publication is implied. Keep
9D W_Q volume outside biological conclusions pending numerical qualification.
Separate prospective plans from already inspected pilot evidence.
