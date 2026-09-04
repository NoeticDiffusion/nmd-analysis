# Laguerre Synthetic Controls

These controls run the current Laguerre v2b estimator on known synthetic geometries.

## Expected Patterns

- `sphere_patch`: low saddle fraction, high |shape index|, nonzero curvedness
- `saddle_patch`: high saddle fraction, shape index near 0
- `cylinder_patch`: intermediate |shape index|, lower curvedness than sphere
- `plane_patch`: near-zero curvedness and near-zero grad-II
- `noise_blob`: poor valid fraction or unstable geometry

## Aggregated Results

| Surface | Noise | Valid frac | Saddle frac | |Shape index| median | Curvedness median | Grad-II median | Shape entropy |
|---|---:|---:|---:|---:|---:|---:|---:|
| cylinder_patch | 0.000 | 0.999 | 0.629 | 0.484 | 0.629 | 7.568 | 0.730 |
| cylinder_patch | 0.010 | 0.571 | 0.685 | 0.349 | 0.996 | 22.430 | 0.942 |
| cylinder_patch | 0.030 | 0.409 | 0.777 | 0.285 | 2.047 | 38.253 | 0.908 |
| noise_blob | 0.000 | 0.130 | 0.906 | 0.237 | 1.028 | 5.308 | 0.806 |
| noise_blob | 0.010 | 0.146 | 0.905 | 0.217 | 1.109 | 6.750 | 0.813 |
| noise_blob | 0.030 | 0.148 | 0.912 | 0.234 | 1.095 | 6.175 | 0.805 |
| plane_patch | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | -0.000 |
| plane_patch | 0.010 | 0.412 | 0.682 | 0.328 | 0.666 | 13.102 | 0.940 |
| plane_patch | 0.030 | 0.384 | 0.771 | 0.288 | 1.796 | 34.307 | 0.904 |
| saddle_patch | 0.000 | 1.000 | 1.000 | 0.094 | 0.721 | 13.196 | 0.501 |
| saddle_patch | 0.010 | 0.662 | 0.838 | 0.264 | 1.041 | 23.230 | 0.853 |
| saddle_patch | 0.030 | 0.433 | 0.781 | 0.294 | 1.919 | 35.204 | 0.896 |
| sphere_patch | 0.000 | 0.998 | 0.160 | 0.895 | 0.900 | 14.427 | 0.675 |
| sphere_patch | 0.010 | 0.468 | 0.677 | 0.371 | 2.160 | 78.754 | 0.953 |
| sphere_patch | 0.030 | 0.330 | 0.860 | 0.253 | 4.177 | 110.703 | 0.842 |
