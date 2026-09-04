# Exploratory ESB proxy summary

This pass uses the current manuscript-facing photic export surface and tests two exploratory constructions:

1. `ESB-2 proxy`: healthy-template deviation in capacity-guidance space on the observed photic stage.
2. `ESB-3 proxy`: `ESB-2 proxy` plus a session-level recovery abnormality term derived from post-photic windows.

A stricter within-subject baseline/recovery variant is also attempted where pre-photic coverage is sufficient.

## Coverage

- Subjects with any pre-photic windows: `64` / `88`.
- Subjects with at least 4 pre-photic windows: `21` / `88`.
- Subjects with at least 4 post-photic windows: `68` / `88`.
- Subjects with at least 2 eye-labeled post-photic windows: `67` / `88`.

- Strict within-subject `ESB-2` coverage: `0` subjects contribute at least one finite score.

## AD vs Healthy highlights

- Strongest `esb2_proxy` row: `posterior_capacity_global_guidance` / `photo_5hz` with `d = 0.441`, `p = 0.03273`, `q = 0.06546`.
- Strongest `esb3_proxy` row: `posterior_capacity_frontal_guidance` / `photo_5hz` with `d = 0.458`, `p = 0.1618`, `q = 0.3235`.
- Strongest `esb2_strict` row: `posterior_capacity_frontal_guidance` / `photo_5hz` with `d = nan`, `p = nan`, `q = nan`.
- Strongest `esb3_strict` row: `posterior_capacity_frontal_guidance` / `photo_5hz` with `d = nan`, `p = nan`, `q = nan`.

## Frequency pattern check

- `esb2_proxy` best spec `posterior_capacity_global_guidance` across frequencies: `photo_5hz` d=0.441, `photo_10hz` d=-0.157, `photo_15hz` d=-0.065, `photo_20hz` d=-0.013.
- `esb3_proxy` best spec `posterior_capacity_frontal_guidance` across frequencies: `photo_5hz` d=0.458, `photo_10hz` d=-0.246, `photo_15hz` d=-0.390, `photo_20hz` d=-0.019.

## Readout

- Clear capture would look like AD-vs-Healthy separation growing toward higher photic frequencies and remaining at least directionally coherent after adding the recovery term.
- If the strict within-subject version is sparse but the proxy version is coherent, that suggests the concept may be real while the current ds006036 baseline labeling is too thin for a clean article-grade ESB-3.