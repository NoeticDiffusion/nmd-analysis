# SBEG — Spontaneous Burst-Evoked Geometry

## Cohort

- processed roots: `2`
- runs analyzed: `4645`
- subjects analyzed: `277`

| label | n |
|---|---:|
| CPC1 | 140 |
| CPC5 | 137 |

## Detector

```text
Activity score:
  A_k = 0.5 * rank_z(log broadband power)
      + 0.25 * rank_z(Hjorth mobility)
      + 0.25 * rank_z(entropy / complexity)
Suppression: A_k <= q25(A)
Active:      A_k >= q60(A)
Burst onset: >= 5 suppression windows before, >= 3 active windows after
Refractory period: 60.0 s
```

## Contrast — sorted by |Cohen's d|

| Metric | CPC1 med | CPC5 med | d | MW p | AUROC | n (1/5) |
|---|---|---|---|---|---|---|
| `run_median_frob` | 0.1506 | 0.1695 | -0.517 | 1.72e-07 | 0.318 | 140/137 |
| `run_median_lambda` | 0.0716 | 0.07539 | -0.461 | 3.59e-07 | 0.323 | 140/137 |
| `R_CD` | 0.03046 | 0.03619 | -0.354 | 9.71e-06 | 0.340 | 130/127 |
| `sbeg_p95` | 2.302 | 2.431 | -0.277 | 0.0762 | 0.436 | 130/127 |
| `R_lambda` | 0.5275 | 0.5805 | -0.264 | 0.0117 | 0.409 | 130/127 |
| `H_CD` | 0.007731 | 0.00977 | -0.227 | 1.91e-08 | 0.297 | 130/127 |
| `sbeg_recovery` | 1.341 | 1.299 | -0.187 | 0.489 | 0.475 | 130/127 |
| `E_frobenius` | 0.03393 | 0.02442 | -0.143 | 0.912 | 0.496 | 130/127 |
| `R_frobenius` | 0.5878 | 0.5999 | -0.068 | 0.548 | 0.478 | 130/127 |
| `event_rate_per_min` | 0.02503 | 0.0254 | -0.044 | 0.977 | 0.499 | 140/137 |
| `no_burst` | 0 | 0 | -0.029 | 0.81 | 0.494 | 140/137 |
| `E_lambda` | 0.08738 | 0.06003 | +0.005 | 0.634 | 0.517 | 130/127 |

## Circular-shift null (sbeg_recovery)

- observed |d| = `0.187`
- null mean |d| = `0.106`
- null p95  |d| = `0.249`
- empirical p   = `0.1740`

## Notes

- SBEG measures the *shape* of peri-burst geometry: pre → peak → recovery.
- `sbeg_recovery` = E_lambda + E_F + R_lambda + R_F (higher = more evoked deformation / worse recovery).
- `no_burst` = fraction of runs with zero detected burst-onsets.
- `run_median_lambda` = spectral radius median across full run (baseline comparator).
- Per the ideas.md spec, the key hypothesis is that CPC5 shows either absent burst response
  or higher baseline deformation with poor recovery form, not just elevated amplitude.