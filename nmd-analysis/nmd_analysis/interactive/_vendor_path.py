"""Make the sibling `ndt_analysis` package importable without installing it.

`ndt-analysis/interactive/` and `ndt-analysis/ndt_analysis/` share the same
parent directory (`ndt-analysis/`). This module just prepends that parent
directory to `sys.path` at runtime so code in this package can do
`import ndt_analysis...` and reuse the existing H5 contract and reachability
math. It never modifies anything under `ndt_analysis/` itself.
"""

from __future__ import annotations

import sys
from pathlib import Path

_INTERACTIVE_DIR = Path(__file__).resolve().parent
NDT_ANALYSIS_PACKAGE_ROOT = _INTERACTIVE_DIR.parent
REPO_ROOT = NDT_ANALYSIS_PACKAGE_ROOT.parent

_ensured = False


def ensure_ndt_analysis_on_path() -> None:
    """Idempotently add `ndt-analysis/` to `sys.path` if not already present."""
    global _ensured
    if _ensured:
        return
    root_str = str(NDT_ANALYSIS_PACKAGE_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    _ensured = True


ensure_ndt_analysis_on_path()
