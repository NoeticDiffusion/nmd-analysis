"""Interactive Dash/Plotly explorer for MNPS trajectories and MNJ/reachability geometry.

This package is intentionally kept separate from the `ndt_analysis` pipeline
package: it is a thin, read-only visualization layer on top of the same H5
contract (`ndt_analysis.h5_contract`) and reachability math
(`ndt_analysis.reachability_core`). See `_vendor_path.py` for how those
modules are reused without requiring an editable pip install.
"""
