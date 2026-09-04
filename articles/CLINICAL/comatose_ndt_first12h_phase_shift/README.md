# Coma first-12h "d_n phase-shift" pipeline

## Status

Pipeline-only. No manuscript has been written yet - this folder currently
holds the `aa_template` scaffold (`manuscript.typ`, `S1`-`S6`, etc. are still
generic placeholders) plus a working analysis pipeline in `src/`. See
`project/diary/` for the working session that produced it.

## Hypothesis

`articles/CLINICAL/comatose_ndt` separates CPC1 (good outcome) from CPC5
(poor outcome) after cardiac-arrest coma using *aggregate* first-12h MNPS /
Jacobian / reachability geometry. `articles/RVC_SLEEP` separately found that
sleep spindles are associated with a measurable *within-event* rise in the
chart coordinate `d_n`.

This project asks a different question: instead of building a
sleep-spindle-like event detector for comatose EEG (which has no canonical
spindle morphology to detect), can we separate CPC1 from CPC5 using how often
and how strongly the patient's neural-geometry chart coordinates *shift*
(changepoint frequency and shift magnitude/quality) during the first 12h,
treated as a general regime-change signal rather than a spindle-specific one?

## Critical naming caveat: `d_n` is not one thing across articles

`d_n` means two different things depending on which article's feature
contract you are reading:

- **RVC_SLEEP** (`articles/RVC_SLEEP/S1_Supplementary_methods.typ`): `d_n` is
  a heat-kernel network-diffusivity term built from a per-window graph
  Laplacian, `d_n = 1 - norm(avg_W(Tr(e^{-t_h L(w)}) / |V|))`.
- **comatose_ndt** (`articles/CLINICAL/comatose_ndt/S1_Supplementary_methods.typ`):
  under the current I-CARE EEG feature contract, `d_n` is an operational
  alias for `eeg_gamma` (log gamma-band power). No graph or Laplacian is
  built for I-CARE.

The `d_n` column already stored per-epoch in the I-CARE H5 exports
(`/coords_9d_subject_anchored/values`) is therefore gamma-band power, **not**
network diffusivity. This pipeline does not try to reconcile the two, and
does not recompute the heat-kernel version for I-CARE. Instead, the
changepoint detector runs generically across all nine 9D-chart coordinates
(`m_a, m_e, m_o, d_n, d_l, d_s, e_e, e_s, e_m`) plus the fixed-weight `m, d, e`
composites, and lets the CPC1-vs-CPC5 contrast decide which coordinate(s) -
possibly `d_n`, possibly not - carry a discriminative shift signal. See the
module docstring in `src/coma_phase_shift_support.py` for the full detail.

## Pipeline

See `src/README.md` for how to run the four pipeline stages
(`01_extract_epoch_series.py` -> `02_detect_shifts.py` ->
`03_aggregate_patient_features.py` -> `04_cpc_contrast.py`).

## Research-discipline status of this branch

Per the repository's role/discipline conventions: this is currently a
**speculative extension** (a plausible reading of the RVC_SLEEP finding
applied to a new dataset/question), not yet an internal validated result.
It becomes a validated result only once the pipeline has been run against
the real I-CARE part1+part2 H5 exports and the CPC1-vs-CPC5 contrast in
`04_cpc_contrast.py` has been inspected after BH-FDR correction.
