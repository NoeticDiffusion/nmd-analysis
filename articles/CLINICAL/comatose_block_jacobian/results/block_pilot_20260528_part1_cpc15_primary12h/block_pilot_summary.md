# Block-Jacobian Pilot Summary

- patient rows: `1269`
- unique subjects: `141`
- CPC1 subjects: `71`
- CPC5 subjects: `70`

## Top within-family raw block contrasts

- `block_frobenius_mean` on `ee`: medians `0.209301` vs `0.254707`, `d = -0.313`, `p = 0.00131`
- `block_frobenius_mean` on `dd`: medians `0.214187` vs `0.239821`, `d = -0.240`, `p = 0.000358`
- `block_trace_mean` on `ee`: medians `-0.00138149` vs `-0.00187722`, `d = -0.229`, `p = 0.527`
- `block_anisotropy_mean` on `dd`: medians `77.8611` vs `150.778`, `d = -0.195`, `p = 0.000273`
- `block_anisotropy_mean` on `mm`: medians `120.84` vs `251.277`, `d = 0.168`, `p = 0.00344`
- `block_trace_mean` on `dd`: medians `0.000674722` vs `-0.0011911`, `d = 0.159`, `p = 0.524`

## Top cross-family raw block contrasts

- `block_frobenius_mean` on `ed`: medians `0.216125` vs `0.242319`, `d = -0.279`, `p = 8.15e-05`
- `c_sym_mean` on `ed`: medians `0.153816` vs `0.204599`, `d = -0.244`, `p = 0.0074`
- `c_sym_mean` on `de`: medians `0.153816` vs `0.204599`, `d = -0.244`, `p = 0.0074`
- `c_rot_mean` on `ed`: medians `0.182447` vs `0.225799`, `d = -0.244`, `p = 0.0104`
- `c_rot_mean` on `de`: medians `0.182447` vs `0.225799`, `d = -0.244`, `p = 0.0104`
- `block_frobenius_mean` on `de`: medians `0.228314` vs `0.254504`, `d = -0.243`, `p = 0.0364`

## Balance and asymmetry aggregates

- `diag_block_frobenius_mean`: medians `0.204366` vs `0.237941`, `d = -0.326`, `p = 0.000413`
- `offdiag_block_frobenius_mean`: medians `0.224384` vs `0.269999`, `d = -0.230`, `p = 0.00967`
- `offdiag_c_rot_mean`: medians `0.174981` vs `0.214621`, `d = -0.230`, `p = 0.0109`
- `offdiag_c_sym_mean`: medians `0.159662` vs `0.201546`, `d = -0.230`, `p = 0.00878`
- `diag_block_trace_mean`: medians `-0.000167938` vs `-0.000532847`, `d = -0.226`, `p = 0.585`
- `diag_minus_offdiag_frobenius`: medians `-0.00364105` vs `-0.00585442`, `d = 0.179`, `p = 0.731`
- `diag_block_anisotropy_mean`: medians `139.088` vs `3420.32`, `d = 0.172`, `p = 0.00148`
- `frobenius_de_ed_absdiff`: medians `0.022217` vs `0.0508146`, `d = -0.241`, `p = 0.0349`

## Upstream run errors

- run errors present: `True`
- errors total: `88`
- subjects with errors: `27`
