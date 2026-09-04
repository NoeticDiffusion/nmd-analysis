# Parkinson walking contrasts

This pass keeps the design intentionally simple:

- Anchor mode: `subject`
- `HC vs PD` within `rest`
- `HC vs PD` within `walk`
- `rest vs walk` within `HC` and within `PD` for participants with both runs

## Group contrasts

### HC_vs_PD_rest

- `d_s_median`: HC median=0, PD median=0, d=0.4137, p=0.01211, q=0.5644
- `m_e_median`: HC median=0, PD median=0, d=-0.2366, p=0.01394, q=0.5644
- `d_n_median`: HC median=0, PD median=0, d=0.0716, p=0.04032, q=0.837
- `e_median`: HC median=0.004101, PD median=0.05889, d=0.4074, p=0.04756, q=0.837
- `m_a_mean`: HC median=-0.1361, PD median=-0.0462, d=0.2933, p=0.05541, q=0.837
- `m_median`: HC median=-0.04671, PD median=0.01032, d=0.4008, p=0.06431, q=0.837
- `m_mean`: HC median=-0.02066, PD median=0.02783, d=0.1992, p=0.07355, q=0.837
- `d_s_mad`: HC median=0.6745, PD median=0.6745, d=0.3212, p=0.09179, q=0.837

### HC_vs_PD_walk

- `m_o_mad`: HC median=0.6745, PD median=0.6745, d=-0.5087, p=0.0448, q=0.8879
- `m_e_mean`: HC median=0.05127, PD median=-0.02275, d=-0.3826, p=0.05353, q=0.8879
- `e_s_mean`: HC median=0.01815, PD median=0.1288, d=0.4014, p=0.05655, q=0.8879
- `m_mean`: HC median=0.09082, PD median=0.0268, d=-0.3863, p=0.07477, q=0.8879
- `m_a_mad`: HC median=0.6545, PD median=0.6121, d=-0.4091, p=0.08828, q=0.8879
- `e_std`: HC median=0.6271, PD median=0.7139, d=0.3561, p=0.09634, q=0.8879
- `d_s_mean`: HC median=0.2907, PD median=0.1913, d=-0.3603, p=0.09996, q=0.8879
- `d_s_iqr`: HC median=1.414, PD median=1.364, d=-0.2794, p=0.1089, q=0.8879

## Paired task contrasts

### HC_walk_vs_rest

- `m_a_mean`: rest median=-0.146, walk median=0.07362, d=0.8884, p=0.0004752, q=0.03849
- `m_mean`: rest median=-0.007218, walk median=0.09082, d=0.6822, p=0.006033, q=0.1812
- `d_l_mean`: rest median=-0.1328, walk median=0.1536, d=0.6563, p=0.006711, q=0.1812
- `d_mean`: rest median=-0.02498, walk median=0.1381, d=0.634, p=0.01353, q=0.274
- `d_mad`: rest median=0.4171, walk median=0.4829, d=0.5468, p=0.01956, q=0.3168
- `m_a_mad`: rest median=0.5957, walk median=0.6545, d=0.5083, p=0.02542, q=0.3432
- `m_mad`: rest median=0.5066, walk median=0.5765, d=0.4448, p=0.03009, q=0.3454
- `d_iqr`: rest median=0.8532, walk median=0.9836, d=0.492, p=0.03543, q=0.3454

### PD_walk_vs_rest

- `m_a_iqr`: rest median=1.161, walk median=1.285, d=0.4717, p=8.081e-06, q=0.0006546
- `d_iqr`: rest median=0.794, walk median=0.9282, d=0.4025, p=2.526e-05, q=0.0007283
- `d_n_mean`: rest median=0.003687, walk median=0.1101, d=0.4089, p=2.806e-05, q=0.0007283
- `d_mad`: rest median=0.4004, walk median=0.4551, d=0.4125, p=3.597e-05, q=0.0007283
- `d_mean`: rest median=-0.01678, walk median=0.07233, d=0.3506, p=0.0003242, q=0.005252
- `jac9_anisotropy_abs_eig_median`: rest median=1.763, walk median=1.823, d=0.2137, p=0.002616, q=0.03531
- `d_std`: rest median=0.7055, walk median=0.7528, d=0.2918, p=0.008566, q=0.08682
- `e_s_mad`: rest median=0.6745, walk median=0.6745, d=-0.02965, p=0.008575, q=0.08682

