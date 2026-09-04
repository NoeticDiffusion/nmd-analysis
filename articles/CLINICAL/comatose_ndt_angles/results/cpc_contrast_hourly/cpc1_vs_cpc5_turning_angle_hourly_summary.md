# Hour-resolved CPC1 vs CPC5 turning-angle localization

This is an exploratory localization follow-up to the pooled first-12h analysis.
BH-FDR is applied within each predeclared (chart x lag x tail/spread feature) cell across its 12 hours.

- Cells with at least one within-cell FDR-significant hour: 29/45
- Cells whose strongest hour has larger |d| than pooled-12h: 42/45

## Strongest localized effects

- `e3__lag4__turn_angle_p90`: strongest `3_4h`, d=-0.555, p=1.62e-05, within-cell q=0.000194, pooled d=-0.382, FDR-significant hours=11
- `e3__lag1__turn_angle_p90`: strongest `8_9h`, d=-0.531, p=3.37e-05, within-cell q=0.000405, pooled d=-0.564, FDR-significant hours=10
- `9d__lag2__turn_angle_mad`: strongest `2_3h`, d=-0.512, p=2.18e-05, within-cell q=0.000261, pooled d=-0.358, FDR-significant hours=11
- `3d__lag4__turn_angle_p90`: strongest `3_4h`, d=-0.511, p=3.93e-06, within-cell q=4.71e-05, pooled d=-0.489, FDR-significant hours=12
- `9d__lag4__turn_angle_p90`: strongest `4_5h`, d=-0.505, p=6.29e-05, within-cell q=0.000378, pooled d=-0.481, FDR-significant hours=11
- `e3__lag2__turn_angle_iqr`: strongest `2_3h`, d=-0.481, p=0.000167, within-cell q=0.00201, pooled d=-0.459, FDR-significant hours=9
- `3d__lag2__turn_angle_mad`: strongest `2_3h`, d=-0.478, p=1.57e-05, within-cell q=0.000188, pooled d=-0.271, FDR-significant hours=7
- `e3__lag2__turn_angle_mad`: strongest `8_9h`, d=-0.456, p=0.00179, within-cell q=0.0113, pooled d=-0.300, FDR-significant hours=5
- `9d__lag4__turn_angle_mad`: strongest `4_5h`, d=-0.444, p=0.000127, within-cell q=0.00153, pooled d=-0.370, FDR-significant hours=8
- `e3__lag4__turn_angle_iqr`: strongest `4_5h`, d=-0.444, p=0.0005, within-cell q=0.003, pooled d=-0.358, FDR-significant hours=9
- `e3__lag2__turn_angle_p90`: strongest `11_12h`, d=-0.442, p=0.00128, within-cell q=0.00514, pooled d=-0.332, FDR-significant hours=12
- `3d__lag2__turn_angle_iqr`: strongest `4_5h`, d=-0.439, p=3.84e-05, within-cell q=0.000354, pooled d=-0.388, FDR-significant hours=11
- `3d__lag1__turn_angle_p90`: strongest `7_8h`, d=-0.413, p=4.4e-05, within-cell q=0.000528, pooled d=-0.319, FDR-significant hours=10
- `d3__lag4__turn_angle_p90`: strongest `4_5h`, d=-0.413, p=0.00118, within-cell q=0.00709, pooled d=-0.354, FDR-significant hours=10
- `d3__lag4__turn_angle_mad`: strongest `11_12h`, d=-0.397, p=0.000669, within-cell q=0.00802, pooled d=-0.265, FDR-significant hours=7
