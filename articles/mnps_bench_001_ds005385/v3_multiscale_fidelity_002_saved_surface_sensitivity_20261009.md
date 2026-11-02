# V3-MULTISCALE-FIDELITY-002 — saved-output surface sensitivity

## Question and scope

This post-pilot descriptive check asks how the saved native63 and Core19 values
compare on the same participant, trial, candidate, duration, and first-window
sample interval. It uses no task labels or condition contrasts. The input is
the hash-checked V3-COVERAGE-001 candidate table for the six frozen
ds003838 participants. Every value remains exploratory and unqualified.

For each participant and scalar candidate, I computed Spearman rank
correlation, Lin concordance correlation coefficient (CCC), median signed
difference (native minus Core19), and median absolute difference. The table
summarizes the six participant-level results by their median; CCC range is
the min–max across participants. Trials are repeated observations within
participants, not independent inferential units. No equivalence threshold was
applied.

## Scalar surface sensitivity

| Candidate | Duration | Pairs per participant | Rank median | CCC median (range) | Median signed difference | Median absolute difference |
|---|---:|---:|---:|---:|---:|---:|
| PCV | 4 s | 162 | 0.7523 | 0.6040 (0.4848–0.6654) | -0.007084 | 0.007699 |
| PCV | 8 s | 162 | 0.8016 | 0.5506 (0.4414–0.6676) | -0.006687 | 0.006763 |
| PCV | 12 s | 108 | 0.8022 | 0.4825 (0.3634–0.6479) | -0.006543 | 0.006543 |
| PCV | 20 s | 54 | 0.8574 | 0.4353 (0.3150–0.6395) | -0.006860 | 0.006860 |
| TP | 4 s | 162 | 0.9526 | 0.9225 (0.8258–0.9594) | 0.001141 | 0.003453 |
| TP | 8 s | 162 | 0.9580 | 0.9224 (0.7828–0.9780) | 0.001429 | 0.003436 |
| TP | 12 s | 108 | 0.9599 | 0.9125 (0.7923–0.9844) | 0.001775 | 0.003105 |
| TP | 20 s | 54 | 0.9561 | 0.9323 (0.7367–0.9811) | 0.002104 | 0.003162 |
| NIE | 4 s | 162 | 0.9690 | 0.8838 (0.5701–0.9064) | -0.002614 | 0.027788 |
| NIE | 8 s | 162 | 0.9618 | 0.8197 (0.4615–0.8868) | -0.004725 | 0.026315 |
| NIE | 12 s | 108 | 0.9664 | 0.8214 (0.3827–0.9063) | -0.005892 | 0.025050 |
| NIE | 20 s | 54 | 0.9670 | 0.8127 (0.3196–0.9247) | -0.009163 | 0.025416 |
| RD | 4 s | 162 | 0.6664 | 0.5786 (0.3625–0.6660) | -0.164169 | 0.181532 |
| RD | 8 s | 162 | 0.8337 | 0.7062 (0.4868–0.8512) | -0.212305 | 0.212305 |
| RD | 12 s | 108 | 0.8301 | 0.6991 (0.4692–0.8734) | -0.219997 | 0.219997 |
| RD | 20 s | 54 | 0.8227 | 0.6446 (0.2783–0.8380) | -0.260757 | 0.260757 |
| OI | 4 s | 162 | 0.9010 | 0.9017 (0.7561–0.9297) | -0.003494 | 0.005451 |
| OI | 8 s | 162 | 0.9183 | 0.9039 (0.7051–0.9397) | -0.003741 | 0.005830 |
| OI | 12 s | 108 | 0.9058 | 0.8868 (0.6551–0.9320) | -0.004209 | 0.005605 |
| OI | 20 s | 54 | 0.9063 | 0.8657 (0.6391–0.9473) | -0.004385 | 0.005560 |
| SC | 4 s | 162 | 0.9322 | 0.9179 (0.8054–0.9598) | -0.002907 | 0.008721 |
| SC | 8 s | 162 | 0.9340 | 0.9256 (0.7334–0.9668) | -0.002798 | 0.009179 |
| SC | 12 s | 108 | 0.9404 | 0.9220 (0.7141–0.9713) | -0.002353 | 0.007987 |
| SC | 20 s | 54 | 0.9470 | 0.9260 (0.5921–0.9553) | -0.001150 | 0.008052 |
| ED | 4 s | 162 | 0.9536 | 0.8681 (0.6093–0.9704) | 0.274759 | 0.275812 |
| ED | 8 s | 162 | 0.9553 | 0.7619 (0.5814–0.9485) | 0.329869 | 0.329869 |
| ED | 12 s | 108 | 0.9486 | 0.7309 (0.5614–0.9252) | 0.322265 | 0.322265 |
| ED | 20 s | 54 | 0.9512 | 0.6996 (0.6236–0.9095) | 0.359971 | 0.359971 |

## AR/M3 component-wise surface sensitivity

AR remains a duration-dependent vector: 1, 3, 5, and 9 components at 4, 8,
12, and 20 seconds. I compared matching components without collapsing the
vector.

| Duration | Components compared | Pairs per participant | Median absolute component difference across participant medians | Participant range | Largest absolute difference observed |
|---|---:|---:|---:|---:|---:|
| 4 s | 1 | 162 | 0.033931 | 0.002456–0.141387 | 0.912695 |
| 8 s | 3 | 162 | 0.029853 | 0.001904–0.148466 | 0.912695 |
| 12 s | 5 | 108 | 0.028554 | 0.001808–0.153915 | 0.694196 |
| 20 s | 9 | 54 | 0.026646 | 0.001313–0.148611 | 0.677559 |

## Interpretation limits

TP, OI, and SC have stronger native/Core19 agreement in this pilot, while PCV
has modest concordance despite rank association. RD and ED show larger level
differences; ED's high rank correlations do not erase its systematic
native-minus-Core19 offset. AR has a small median component difference but
large individual-window extremes.

These are different sensor/reference realizations, so the results describe
sensitivity rather than equivalence. They do not separate channel-count and
reference effects, assess task-time confounding, validate PCV filter edges, or
establish test–retest reliability. No thresholds, labels, classifier, or
scientific qualification were used.
