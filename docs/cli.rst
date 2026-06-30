Command-line interface
======================

The ``nmd-analysis`` command is a `Typer <https://typer.tiangolo.com/>`_ CLI
exposed by ``nmd_analysis.cli``. It has three subcommands.

Show the top-level help::

   nmd-analysis --help

``nmd-analysis run`` — raw H5 to cleaned Parquet
------------------------------------------------

Run the dataset pipeline from a **dataset config** (the
``ndt-analysis-<dataset>.yaml`` family).

.. code-block:: bash

   nmd-analysis run \
       --config nmd-analysis/config/ndt-analysis-ds003490.yaml \
       --input-root data/raw \
       --output-root data/cleaned \
       --workers 4 \
       --analyses global_mnps_3d,reachability_cones

Options:

- ``--config`` (required): path to a dataset YAML config.
- ``--input-root`` / ``--output-root``: override the roots from the config.
- ``--workers``: parallel worker processes (default: config ``runtime.workers``
  or ``cpu_count() - 1``).
- ``--analyses``: comma-separated subset of analysis types to run
  (default: all enabled in the YAML).

``nmd-analysis analyze`` — cleaned Parquet to analysis results
--------------------------------------------------------------

Run the cleaned-to-analysis pipeline from an **analysis config** (the
``analysis-<dataset>.yaml`` family).

.. code-block:: bash

   nmd-analysis analyze \
       --config nmd-analysis/config/analysis-ds003490.yaml \
       --cleaned-root data/cleaned \
       --output-root data/analysis \
       --analyses global_mnps_3d,reachability_cones \
       --contrasts Parkinson_OFF_vs_ON,Control_vs_Parkinson_OFF

Options:

- ``--config`` (required): path to an analysis YAML config.
- ``--cleaned-root`` / ``--output-root``: override the roots from the config.
- ``--analyses``: comma-separated analysis blocks to include.
- ``--contrasts``: comma-separated contrast names to run.

``nmd-analysis spindle-events`` — event-locked baseline-delta analysis
----------------------------------------------------------------------

Run a spindle event-locked baseline-delta analysis from event Parquet exports.

.. code-block:: bash

   nmd-analysis spindle-events \
       --event-root data/cleaned/spindle_events \
       --output-root data/analysis/spindle_events \
       --channel psg_c3 \
       --condition spindle_event \
       --baseline-bin pre_far \
       --min-subjects 3

Options:

- ``--event-root`` (required): directory of event Parquet exports.
- ``--output-root`` (required): where to write outputs.
- ``--channel``: event parquet channel suffix (default ``psg_c3``).
- ``--condition``: condition label (default ``spindle_event``).
- ``--baseline-bin``: baseline bin name (default ``pre_far``).
- ``--min-subjects``: minimum subjects for paired tests (default ``3``).

Python entry point
------------------

The same functionality is available as a Python module::

   from nmd_analysis import run_dataset_pipeline, run_cleaned_analysis_pipeline
