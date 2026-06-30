Installation
============

Requirements
------------

- Python 3.10 or newer
- A C compiler is not required for the core pipeline; ``h5py`` wheels are
  used for HDF5 I/O and ``pyarrow`` wheels for Parquet I/O.

Install the package
-------------------

The package lives in the ``nmd-analysis/`` subdirectory of this repository.
Install it in editable mode from a clone::

   git clone https://github.com/nmd-analysis/nmd-analysis.git
   cd nmd-analysis
   python -m venv .venv
   . .venv/Scripts/activate     # Windows PowerShell
   # source .venv/bin/activate  # macOS / Linux
   pip install -e ./nmd-analysis

This installs the ``nmd-analysis`` console script (see :doc:`cli`).

Optional scientific stack
-------------------------

The full research stack (MNE, Nilearn, topological / recurrence / criticality
toolkits) is listed in the repository-root ``requirements.txt``::

   pip install -r requirements.txt

These are only needed for the optional comparators and visualisation scripts,
not for the core ``run`` / ``analyze`` pipeline.

Data
----

The pipeline expects raw HDF5 input under ``data/raw/`` and writes cleaned
Parquet to ``data/cleaned/`` and analysis results to ``data/analysis/``.
See ``data/README.md`` for dataset provenance and acquisition notes, and
:doc:`configuration` for how to point configs at your data.
