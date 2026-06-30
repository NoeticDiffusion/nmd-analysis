Visuals
=======

The scripts in ``nmd-analysis/visuals/`` are standalone plotting tools for
``nmd-analysis``. They consume output from ``data/cleaned`` and
``data/analysis`` and write figures under ``nmd-analysis/visuals/output/``.

Output structure
----------------

- ``output/<dataset>/violin/``
- ``output/<dataset>/lollipop/``
- ``output/<dataset>/boxplots/``
- ``output/<dataset>/report/``
- ``output/<dataset>/rose/``
- ``output/<dataset>/profile/``
- ``output/<dataset>/density/``
- ``output/<dataset>/voxels/``
- ``output/<dataset>/profile-grid/``
- ``output/<dataset>/reachability/``

Examples
--------

.. code-block:: powershell

   python nmd-analysis/visuals/violin_plots.py `
       --input-path "data/analysis/ANPHY_subject_metrics_20260317_120000.parquet" `
       --dataset ANPHY

   python nmd-analysis/visuals/stratified_plots.py `
       --group-diff-json "data/analysis/ds003490_Healthy_vs_Parkinson_OFF_group_diff.json" `
       --csv "data/analysis/ds003490_stratified_subjects.csv" `
       --groups "Healthy,Parkinson:OFF" `
       --dataset ds003490

   python nmd-analysis/visuals/stratified_density.py `
       --group-diff-json "data/analysis/ds003490_Healthy_vs_Parkinson_OFF_group_diff.json" `
       --csv "data/analysis/ds003490_stratified_subjects.csv" `
       --groups "Healthy,Parkinson:OFF" `
       --dataset ds003490

   python nmd-analysis/visuals/reachability_plots.py `
       --csv "data/analysis/ANPHY_reachability_cones_subjects.csv" `
       --groups "Healthy:awake,Healthy:nrem3" `
       --dataset ANPHY

   python nmd-analysis/visuals/reachability_dataset_panels.py `
       --input-root "data/analysis" `
       --input-root "data/cleaned" `
       --figures-dir "nmd-analysis/visuals/output/reachability_panels"

Script reference
----------------

``violin_plots.py``
   Accepts legacy JSON summary files, CSV tables, Parquet tables, and
   multiple ``--input-path`` arguments to combine endpoints from different
   export files. Supports ``--plot-mode endpoints`` for manuscript /
   endpoint-focused violins, plus ``--group-filter``,
   ``--condition-filter``, ``--task-filter`` and ``--category-column`` to
   control grouping. Subject-level plots are produced only when
   ``--subject-plots`` is given.

``stratified_plots.py``
   Generates lollipop plots, boxplots, a report-style violin / box / jitter
   figure, rose / dual-rose, and grouped bar profiles.

``stratified_density.py``
   Generates density slices, voxel-density comparisons, a profile grid per
   group, and a per-subcoordinate profile comparison.

``reachability_plots.py``
   Generates group comparisons of endpoint ovality, group comparisons of
   tube-likeness / compactness, and a shape map where bubble size encodes
   reachability size.

Additional scripts in the directory (``cone_tube_heatmap_panels.py``,
``mnps_heatmap_panels.py``, ``generate_appendix_heatmaps.py``,
``export_reachability_typst_tables.py``,
``export_reachability_controls_typst.py``,
``export_adaptive_collapse_typst.py``,
``generate_adaptive_collapse_tables.py``,
``update_reachability_article_tables.py``,
``Adaptive_traversability_collapse_occupancy.py``) produce the manuscript
heatmap panels, Typst table exports, and adaptive-collapse summaries. Run
any of them with ``--help`` for its specific options.
