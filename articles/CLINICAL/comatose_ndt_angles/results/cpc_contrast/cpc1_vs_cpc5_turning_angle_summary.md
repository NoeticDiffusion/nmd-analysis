# CPC1 vs CPC5 first-12h turning-angle contrast

- good_cpc=1 (Good), poor_cpc=5 (Poor)
- n_cells_tested=150

Adapted from plan.md (originally written for FEP psychosis vs. Healthy, medication-stratified). Here the contrast is CPC1 vs. CPC5; the metric-adjusted (shrinkage-covariance) 9D angle from plan.md section 3 is not included in this pass (see coma_angle_support.py module docstring and README.md).

## FDR-significant cells (q < 0.05): 36

- `3d__lag4__turn_angle_p90`: delta_median=-1.436, cohens_d=-0.489, cliffs_delta=-0.322, mannwhitney_p=3.126e-06, q_bh=0.000307
- `3d__lag2__turn_angle_p90`: delta_median=-1.304, cohens_d=-0.383, cliffs_delta=-0.318, mannwhitney_p=4.094e-06, q_bh=0.000307
- `e3__lag1__turn_angle_p90`: delta_median=-2.137, cohens_d=-0.564, cliffs_delta=-0.307, mannwhitney_p=1.218e-05, q_bh=0.0006017
- `9d__lag4__turn_angle_p90`: delta_median=-2.271, cohens_d=-0.481, cliffs_delta=-0.294, mannwhitney_p=2.044e-05, q_bh=0.0006017
- `9d__lag2__turn_angle_p90`: delta_median=-1.973, cohens_d=-0.372, cliffs_delta=-0.294, mannwhitney_p=2.057e-05, q_bh=0.0006017
- `3d__lag1__turn_angle_p90`: delta_median=-2.421, cohens_d=-0.319, cliffs_delta=-0.291, mannwhitney_p=2.407e-05, q_bh=0.0006017
- `e3__lag2__turn_angle_p90`: delta_median=-1.573, cohens_d=-0.332, cliffs_delta=-0.281, mannwhitney_p=4.599e-05, q_bh=0.0008735
- `3d__lag2__turn_angle_iqr`: delta_median=-3.296, cohens_d=-0.388, cliffs_delta=-0.281, mannwhitney_p=4.659e-05, q_bh=0.0008735
- `e3__lag4__turn_angle_p90`: delta_median=-1.772, cohens_d=-0.382, cliffs_delta=-0.276, mannwhitney_p=6.328e-05, q_bh=0.001055
- `3d__lag4__turn_angle_iqr`: delta_median=-2.437, cohens_d=-0.333, cliffs_delta=-0.269, mannwhitney_p=9.606e-05, q_bh=0.001441
- `3d__lag4__turn_angle_mad`: delta_median=-0.9438, cohens_d=-0.275, cliffs_delta=-0.254, mannwhitney_p=0.0002345, q_bh=0.002999
- `e3__lag2__turn_angle_iqr`: delta_median=-2.641, cohens_d=-0.459, cliffs_delta=-0.253, mannwhitney_p=0.0002399, q_bh=0.002999
- `9d__lag2__turn_angle_iqr`: delta_median=-2.242, cohens_d=-0.329, cliffs_delta=-0.252, mannwhitney_p=0.0002615, q_bh=0.003017
- `9d__lag4__turn_angle_mad`: delta_median=-1.528, cohens_d=-0.37, cliffs_delta=-0.247, mannwhitney_p=0.000353, q_bh=0.003782
- `9d__lag2__turn_angle_mad`: delta_median=-1.272, cohens_d=-0.358, cliffs_delta=-0.236, mannwhitney_p=0.000619, q_bh=0.005961
- `9d__lag4__turn_angle_iqr`: delta_median=-3.002, cohens_d=-0.351, cliffs_delta=-0.236, mannwhitney_p=0.0006359, q_bh=0.005961
- `9d__lag1__turn_angle_p90`: delta_median=-2.005, cohens_d=-0.214, cliffs_delta=-0.229, mannwhitney_p=0.0009228, q_bh=0.008143
- `e3__lag4__turn_angle_iqr`: delta_median=-2.474, cohens_d=-0.358, cliffs_delta=-0.221, mannwhitney_p=0.00136, q_bh=0.01134
- `3d__lag4__turn_angle_median`: delta_median=-0.7994, cohens_d=-0.364, cliffs_delta=-0.206, mannwhitney_p=0.002844, q_bh=0.02002
- `3d__lag1__turn_length_coupling`: delta_median=-0.01886, cohens_d=-0.261, cliffs_delta=-0.206, mannwhitney_p=0.002857, q_bh=0.02002
- `d3__lag4__turn_angle_mad`: delta_median=-1.504, cohens_d=-0.265, cliffs_delta=-0.206, mannwhitney_p=0.002857, q_bh=0.02002
- `m3__lag2__turn_angle_p90`: delta_median=-3.553, cohens_d=-0.267, cliffs_delta=-0.204, mannwhitney_p=0.002985, q_bh=0.02002
- `3d__lag2__turn_angle_mad`: delta_median=-0.9596, cohens_d=-0.271, cliffs_delta=-0.204, mannwhitney_p=0.00307, q_bh=0.02002
- `d3__lag4__turn_angle_p90`: delta_median=-4.839, cohens_d=-0.354, cliffs_delta=-0.199, mannwhitney_p=0.003886, q_bh=0.02398
- `d3__lag2__turn_angle_mad`: delta_median=-0.9617, cohens_d=-0.264, cliffs_delta=-0.199, mannwhitney_p=0.003996, q_bh=0.02398
- `3d__lag1__turn_fraction_gt_120`: delta_median=-0.01301, cohens_d=-0.162, cliffs_delta=-0.194, mannwhitney_p=0.004963, q_bh=0.02863
- `9d__lag2__turn_entropy`: delta_median=-0.0259, cohens_d=-0.352, cliffs_delta=-0.19, mannwhitney_p=0.005867, q_bh=0.03143
- `d3__lag4__turn_angle_iqr`: delta_median=-4.971, cohens_d=-0.174, cliffs_delta=-0.191, mannwhitney_p=0.005685, q_bh=0.03143
- `3d__lag1__turn_entropy`: delta_median=-0.008432, cohens_d=-0.191, cliffs_delta=-0.186, mannwhitney_p=0.007072, q_bh=0.03571
- `d3__lag2__turn_angle_iqr`: delta_median=-4.4, cohens_d=-0.168, cliffs_delta=-0.185, mannwhitney_p=0.007229, q_bh=0.03571
- `m3__lag4__turn_angle_p90`: delta_median=-3.75, cohens_d=-0.26, cliffs_delta=-0.184, mannwhitney_p=0.007379, q_bh=0.03571
- `e3__lag4__turn_angle_mad`: delta_median=-0.977, cohens_d=-0.23, cliffs_delta=-0.183, mannwhitney_p=0.007855, q_bh=0.03682
- `e3__lag2__turn_angle_mad`: delta_median=-0.769, cohens_d=-0.3, cliffs_delta=-0.179, mannwhitney_p=0.009436, q_bh=0.04289
- `m3__lag1__turn_angle_p90`: delta_median=-3.426, cohens_d=-0.198, cliffs_delta=-0.177, mannwhitney_p=0.009956, q_bh=0.04392
- `3d__lag1__turn_angle_mad`: delta_median=-0.6489, cohens_d=-0.313, cliffs_delta=-0.176, mannwhitney_p=0.01083, q_bh=0.04642
- `d3__lag1__turn_length_coupling`: delta_median=-0.01077, cohens_d=-0.249, cliffs_delta=-0.174, mannwhitney_p=0.01178, q_bh=0.04907

## Top 10 cells by raw p-value (uncorrected, for context only)

- `3d__lag4__turn_angle_p90`: delta_median=-1.436, mannwhitney_p=3.126e-06, q_bh=0.000307
- `3d__lag2__turn_angle_p90`: delta_median=-1.304, mannwhitney_p=4.094e-06, q_bh=0.000307
- `e3__lag1__turn_angle_p90`: delta_median=-2.137, mannwhitney_p=1.218e-05, q_bh=0.0006017
- `9d__lag4__turn_angle_p90`: delta_median=-2.271, mannwhitney_p=2.044e-05, q_bh=0.0006017
- `9d__lag2__turn_angle_p90`: delta_median=-1.973, mannwhitney_p=2.057e-05, q_bh=0.0006017
- `3d__lag1__turn_angle_p90`: delta_median=-2.421, mannwhitney_p=2.407e-05, q_bh=0.0006017
- `e3__lag2__turn_angle_p90`: delta_median=-1.573, mannwhitney_p=4.599e-05, q_bh=0.0008735
- `3d__lag2__turn_angle_iqr`: delta_median=-3.296, mannwhitney_p=4.659e-05, q_bh=0.0008735
- `e3__lag4__turn_angle_p90`: delta_median=-1.772, mannwhitney_p=6.328e-05, q_bh=0.001055
- `3d__lag4__turn_angle_iqr`: delta_median=-2.437, mannwhitney_p=9.606e-05, q_bh=0.001441
