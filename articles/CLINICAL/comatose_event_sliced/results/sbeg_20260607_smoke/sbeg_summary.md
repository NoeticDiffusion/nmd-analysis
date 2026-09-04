# SBEG — Spontaneous Burst-Evoked Geometry

## Cohort

- processed roots: `2`
- runs analyzed: `239`
- subjects analyzed: `20`

| label | n |
|---|---:|
| CPC1 | 10 |
| CPC5 | 10 |

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
| `run_median_frob` | 0.1571 | 0.1838 | -1.028 | 0.0173 | 0.180 | 10/10 |
| `H_CD` | 0.007711 | 0.00885 | -0.986 | 0.0637 | 0.235 | 9/9 |
| `run_median_lambda` | 0.07452 | 0.08111 | -0.937 | 0.00728 | 0.140 | 10/10 |
| `R_CD` | 0.03313 | 0.03338 | -0.647 | 0.216 | 0.321 | 9/9 |
| `R_frobenius` | 0.6094 | 0.5574 | +0.457 | 0.331 | 0.642 | 9/9 |
| `sbeg_p95` | 2.557 | 2.893 | -0.412 | 0.536 | 0.407 | 9/9 |
| `E_frobenius` | 0.1182 | 0.1594 | -0.390 | 0.791 | 0.457 | 9/9 |
| `sbeg_recovery` | 1.404 | 1.2 | -0.248 | 0.791 | 0.457 | 9/9 |
| `R_lambda` | 0.5253 | 0.5579 | -0.214 | 0.791 | 0.457 | 9/9 |
| `event_rate_per_min` | 0.03228 | 0.03337 | +0.197 | 0.969 | 0.510 | 10/10 |
| `E_lambda` | 0.04797 | 0.1193 | -0.106 | 0.86 | 0.469 | 9/9 |
| `no_burst` | 0 | 0 | +0.000 | 1 | 0.500 | 10/10 |

## Circular-shift null (sbeg_recovery)

- observed |d| = `0.248`
- null mean |d| = `0.408`
- null p95  |d| = `1.030`
- empirical p   = `0.5840`

## Notes

- SBEG measures the *shape* of peri-burst geometry: pre → peak → recovery.
- `sbeg_recovery` = E_lambda + E_F + R_lambda + R_F (higher = more evoked deformation / worse recovery).
- `no_burst` = fraction of runs with zero detected burst-onsets.
- `run_median_lambda` = spectral radius median across full run (baseline comparator).
- Per the ideas.md spec, the key hypothesis is that CPC5 shows either absent burst response
  or higher baseline deformation with poor recovery form, not just elevated amplitude.