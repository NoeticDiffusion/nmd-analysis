# NDT v2 flagship — source intake summaries

Working files for rebuilding `articles/NoeticDiffusionTheory_v2` from companion research.
These are **internal cartography**, not manuscript prose.

Guiding architecture (frozen in `sciencelead/sl_1.md` and `sciencelead/sl_001.md`):

> **State geometry → Local dynamical geometry → Geometry of possible futures → Control of accessibility**

Canonical claim to test material against:

> NDT has evolved from rhythmically scheduled denoising in neural state space into a theory of dynamically controlled neural accessibility.

## How to tag each result

| Field | Allowed values |
| --- | --- |
| **Layer** | `state` / `local_dynamics` / `possible_futures` / `control` / `epistemic` / `measurement_contract` |
| **Evidence class** | `established_external` / `internal_validated` / `plausible` / `speculative` / `rejected` |
| **Flagship role** | `main_text_anchor` / `evidence_matrix` / `supplement` / `exclude` / `terminology_only` |
| **Claim ceiling** | one sentence: the strongest statement the result actually licenses |

Main-text empirical anchors (do not expand without a later editorial decision):

1. Sleep spindles / RVC event-locking
2. Coma / recovery-linked geometry
3. DANDI 000458 meso→macro (positive association + negative operator inference)

## File plan

| File | Source repo | Status |
| --- | --- | --- |
| `00_synthesis.md` | this folder | Freeze after `01`–`06`; **2026-08-30 addendum** folds m3-bridge `07`–`10` |
| `01_ndt_simulator_local_dynamics.md` | `J:\repos\ndt-simulator` | Done — O1/J1/J2, observatory, C2 stop |
| `02_ndt_simulator_control_and_reachability.md` | `J:\repos\ndt-simulator` | Done — TA, HELS-A, G/G2, R/RD/RC, SSMR |
| `03_ndt_subsystems_empirical.md` | `J:\repos\ndt-subsystems` | Done — DANDI 000458, TRN/TA real data, HELS eligibility |
| `04_nmd_analysis_empirical_and_identity.md` | this repo | Done — NDT 0.8 + ndt_2, spindles, coma, matrix |
| `05_neuralmanifolddynamics_contract.md` | `H:\SourceRepo2\NeuralManifoldDynamics` | Done — NDT vs NMD, v2.5/2.6 gates |
| `06_cytodend_slow_branch_micro.md` | `I:\AAA_PYTHON_REPOS_BACKUP\cytodendaccessmodel` | Done — dendritic \(M_b\); micro end of the chain |
| `07_m3_bridge_dandi_meso_macro.md` | `J:\repos\m3-bridge` | Done 2026-08-30 — 000458 now canonical article source (r 0.406/0.395; residual 0.856); 000574 FAIL; chain/TRN-bridge blocked |
| `08_m3_bridge_ibl_charts.md` | `J:\repos\m3-bridge` | Done 2026-08-30 — IBL chart-readout STOP cluster; IBL2 decoder PASS vs discrete-flow STOP; not a fourth anchor |
| `09_m3_bridge_allen_cross_scale.md` | `J:\repos\m3-bridge` | Done 2026-08-30 — AVB omission chart-separation (median 0.980); ARR/AGR “reachability” is chart-speed, not \(\Sigma^{(h)}\); 24h/Dryad are measurement blocks |
| `10_m3_bridge_fb3_and_skips.md` | `J:\repos\m3-bridge` | Done 2026-08-30 — FB3 no-report RSA (median ρ=0.092); not NDT; NDT/Slow Branch skips → `04`/`06` |

## Editorial rules (from sciencelead)

- Do not treat MNPS as NDT.
- Do not treat NMD as the theory.
- Do not fold committor/FAR into the measurement contract unless qualified.
- RVC is the *minimal* accessibility-control case, not the whole mechanism.
- Success at one recoverability level does not license a stronger claim at another.
- Heterogeneous clinical results are an asset if framed as **structured dissociations**.
- Slow branch-level \(M_b\) is a **speculative substrate bridge** (sciencelead): simulator-validated at micro, not identified with MNPS/MNJ.
