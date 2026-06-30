# Visuals

Visualiseringarna i denna mapp är standalone för `nmd-analysis` och ska använda
output från `data/cleaned` och `data/analysis`.

## Outputstruktur

- `output/<dataset>/violin/`
- `output/<dataset>/lollipop/`
- `output/<dataset>/boxplots/`
- `output/<dataset>/report/`
- `output/<dataset>/rose/`
- `output/<dataset>/profile/`
- `output/<dataset>/density/`
- `output/<dataset>/voxels/`
- `output/<dataset>/profile-grid/`
- `output/<dataset>/reachability/`

## Exempel

```powershell
python nmd-analysis/visuals/violin_plots.py --input-path "data/analysis/ANPHY_subject_metrics_20260317_120000.parquet" --dataset ANPHY
python nmd-analysis/visuals/violin_plots.py --plot-mode endpoints --dataset ANPHY --input-path "data/cleaned/ANPHY_reachability_cones_20260317_120000.parquet" --input-path "data/cleaned/ANPHY_global_mnps_jacobian_3d_20260317_120000.parquet" --input-path "data/cleaned/ANPHY_global_mnps_3d_20260317_120000.parquet" --input-path "data/cleaned/ANPHY_regional_mnps_jacobian_3d_20260317_120000.parquet" --metrics "tube_log_det_median,frobenius_norm_median,mnps_M_mean,v2_e_s_mean" --category-column condition --category-order "awake,nrem2,nrem3,rem" --group-filter Healthy --task-filter sleep --filename anphy_claim_endpoints
python nmd-analysis/visuals/stratified_plots.py --group-diff-json "data/analysis/ds003490_Healthy_vs_Parkinson_OFF_group_diff.json" --csv "data/analysis/ds003490_stratified_subjects.csv" --groups "Healthy,Parkinson:OFF" --dataset ds003490
python nmd-analysis/visuals/stratified_density.py --group-diff-json "data/analysis/ds003490_Healthy_vs_Parkinson_OFF_group_diff.json" --csv "data/analysis/ds003490_stratified_subjects.csv" --groups "Healthy,Parkinson:OFF" --dataset ds003490
python nmd-analysis/visuals/reachability_plots.py --csv "data/analysis/ANPHY_reachability_cones_subjects.csv" --groups "Healthy:awake,Healthy:nrem3" --dataset ANPHY
python nmd-analysis/visuals/reachability_dataset_panels.py --input-root "data/analysis" --input-root "data/cleaned" --figures-dir "nmd-analysis/visuals/output/reachability_panels"
```

`violin_plots.py` accepterar:

- äldre JSON-summary-filer
- CSV-tabeller
- Parquet-tabeller
- flera `--input-path` i samma körning för att kombinera endpoints från olika exportfiler
- `--plot-mode endpoints` för manus-/endpoint-fokuserade violiner
- `--group-filter`, `--condition-filter`, `--task-filter` och `--category-column` för att styra grupperingen
- subject-plots endast när `--subject-plots` anges

`stratified_plots.py` genererar:

- lollipop
- boxplots
- report-lik violin/box/jitter-figur
- rose / dual-rose
- grouped bar profile

`stratified_density.py` genererar:

- density slices
- voxel-density jämförelser
- profilgrid per grupp
- profiljämförelse per subkoordinat

`reachability_plots.py` genererar:

- gruppjämförelse av endpoint-ovalitet
- gruppjämförelse av tube-likeness/kompakthet
- shape-map där bubbelstorlek visar reachability-storlek
