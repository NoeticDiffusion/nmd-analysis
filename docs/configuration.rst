Configuration
=============

The pipeline is driven by two YAML config families that live in
``nmd-analysis/config/``. They are **not** duplicates — each drives a
different pipeline stage.

.. contents::
   :local:
   :depth: 1

Dataset configs — ``ndt-analysis-<dataset>.yaml``
-------------------------------------------------

Used by ``nmd-analysis run`` (raw HDF5 → cleaned Parquet). Loaded by
``nmd_analysis.config.load_dataset_config``.

Key sections:

``dataset``
   Required dataset identifier string.

``input.h5_root``
   Path to the raw HDF5 dataset directory.

``coordinate_contract``
   Coordinate normalization contract (e.g. ``subject_anchored``).

``output``
   ``directory``, ``filename_pattern`` (e.g.
   ``{dataset}_{analysisType}_{timestamp}.parquet``), ``timestamp_format``,
   and ``parquet`` sub-keys (``compression``, ``index``).

``runtime``
   ``fail_on_missing_input``, ``skip_disabled_analyses``,
   ``continue_on_analysis_error``, ``workers``.

``flags``
   ``sleep_data_contrast`` (bool), ``stage_code_map`` (int → label),
   ``min_stage_timepoints``.

``modality_rules``
   Modality-specific overrides (mapping).

``analyses``
   Mapping of analysis type → bool (enabled/disabled).

``ndt-analysis-template.yaml`` is the starter template.

Analysis configs — ``analysis-<dataset>.yaml``
----------------------------------------------

Used by ``nmd-analysis analyze`` (cleaned Parquet → analysis results).
Loaded by ``nmd_analysis.analysis_config.load_analysis_config``.

Key sections:

``input.cleaned_root``
   Path to the cleaned Parquet directory.

``coordinate_contract``
   Coordinate normalization contract.

``output``
   Same shape as the dataset config ``output`` section.

``runtime``
   ``fail_on_missing_input``, ``continue_on_error``.

``qc``
   ``require_finite_ok``, ``exclude_not_testable``, ``exclude_validity_limited``.

``design``
   ``pairing_keys`` (e.g. ``subject_id``), ``condition_column``,
   ``group_column``.

``statistics``
   ``permutation_n``, ``bootstrap_n``, ``random_seed``, ``min_group_n``,
   ``min_pairs``, ``fdr_group_by``.

``blocks``
   Mapping of analysis block → ``enabled`` plus optional ``validity`` gates
   with ``min`` / ``max`` / ``require_true`` thresholds.

``contrasts``
   List of contrast definitions, each with ``name``, ``type`` (e.g.
   ``paired``), ``left`` / ``right`` (group + condition), optional
   ``subset`` and ``pairing_keys``.

Typical workflow
----------------

.. code-block:: bash

   # 1. raw H5  ->  cleaned parquet
   nmd-analysis run --config nmd-analysis/config/ndt-analysis-ds003490.yaml

   # 2. cleaned parquet  ->  analysis results
   nmd-analysis analyze --config nmd-analysis/config/analysis-ds003490.yaml

See ``nmd-analysis/config/README.md`` for a condensed in-repo reference.
