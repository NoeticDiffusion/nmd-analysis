# Main dynamical-family metric inventory

This read-only inventory covers existing NMD-v3 H5 surfaces for accepted full-night `sub-99` and independent `sub-1`. It uses the installed/staged `nmd_analysis.dynamical_families` and `nmd_analysis.local_dynamics` readers/adapters; it does not estimate, pool, or qualify metrics.

The reproducible script is `src/inventory_new_families.py`; output is `results/new_family_inventory_20260910/family_metric_inventory.json`. The command requires nmd-analysis on `PYTHONPATH`; reader source hashes and H5 before/after hashes are recorded.

| Surface | Grain/path | sub-99 | sub-1 | Definition | Qualification |
|---|---|---:|---:|---|---|
| spectral abscissa | local Jacobian windows, 3D | 1066 finite/adapter-valid | 913 finite/adapter-valid | `mndm/src/mndm/dynamics/jacobian_metrics.py` | not assessed |
| numerical abscissa | local Jacobian windows, 3D | 1066 finite/adapter-valid | 913 finite/adapter-valid | same Jacobian implementation | not assessed |
| spectral abscissa | local Jacobian windows, 9D | 1066 finite/adapter-valid | 856 finite/adapter-valid | same Jacobian implementation | not assessed |
| numerical abscissa | local Jacobian windows, 9D | 1066 finite/adapter-valid | 856 finite/adapter-valid | same Jacobian implementation | not assessed |
| `a_hat`, diffusion tensor, `d_diff`, `D_total`, `c_diff`, concentration, effective dimension | diffusion windows | 1068 finite/adapter-valid | 915 finite/adapter-valid | `mndm/src/mndm/dynamical_families/diffusion_geometry.py` | not assessed |
| `drift_diffusion_alignment`, `A_bD`, `R_b_over_a` | diffusion windows | 0 finite/adapter-valid | 0 finite/adapter-valid | same diffusion geometry surface | not assessed |

The local Jacobian abscissae are eigenvalue/symmetric-part metrics of the local Jacobian and are distinct from diffusion-family drift or tensor quantities. Diffusion `a_hat` is a window-local increment covariance/tensor surface; `D_total`, `c_diff`, and concentration are canonical scalar diffusion series. Drift-related diffusion fields are unavailable as finite values because no independently supplied drift is recorded; they are not treated as zero and are not an ItÃ´ drift estimate. Exact units for exported family fields are not recorded by the adapter; Jacobian abscissae are per-time metrics from the implementation contract.

Qualification was not evaluated by these readers, so qualification counts are `null`, not zero. Computed, finite, and adapter-valid values are measurement inventory facts only; no scientific or biological qualification follows.

Final coordinator inventory also includes reactivity_gap and distinguishes adapter finite flags from measurement validity. Historical JSON variants remain in H as superseded evidence and are not installed.
