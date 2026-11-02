# Addendum 2026-09-21: LOR/ROR on frozen occupancy

Status: dated exploratory branch after `sl_006.md`. Occupancy scalar is the
one frozen in `addendum_20260921_occupancy_primary.md`. No new dynamical
metrics. L1, Jacobian α, and C3 matching are not reopened. G3/G4 not locked.
Not consciousness.

Behavioural labels are assigned from `n_correct_responses` / 40 only, before
joining occupancy.

## LOR rule (Chennu 2016, occupancy-blind)

Task: 40 auditory buzz/noise trials per protocol phase (Cambridge
`datainfo.mat` column 5). Fit an exact binomial 95% Clopper–Pearson interval
to hit count \(k\) out of \(n=40\) at pre-drug baseline and at later protocol
sedation (moderate). A subject is **LOR-impaired** if the moderate interval
lies entirely below the baseline interval (upper moderate < lower baseline).
Otherwise **responsive**. Missing \(k\) stays missing.

This is the original paper’s drowsy/responsive split (7 impaired, 13
responsive in Chennu et al.), not protocol phase 3 and not the package alias
`unresponsive`.

**ROR:** among LOR-impaired subjects, recovery is **returned** if the recovery
binomial interval overlaps the baseline interval; otherwise **not returned**.
Responsive subjects are not scored for ROR.

## Occupancy question

Does the frozen occupancy scalar show a displacement or recovery pattern
tied to this behavioural split, rather than only to protocol phase?

## Primary (one test)

Between-group Mann–Whitney on subject occupancy Δ (later protocol sedation −
baseline): LOR-impaired vs responsive. Two-sided. Prediction: LOR-impaired
have larger Δ. Reporting gate: ≥10 subjects per arm; otherwise NOT_TESTABLE
with effects still listed. No Holm (single primary).

## Secondaries (not replacements)

- Occupancy Δ (first sedation − baseline) by LOR group (does relocation
  precede the moderate-sedation behavioural split?).
- Occupancy Δ (recovery − baseline) by LOR group.
- Spearman occupancy vs \(k/40\) at later protocol sedation (n=20, two-sided).
- ROR table among LOR-impaired subjects only.

## Not in this run

New occupancy distances; L1/Jacobian/C3; treating protocol 3 as LOR;
confirmatory G4; calling LOR unconsciousness.
