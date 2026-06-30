from __future__ import annotations

from pathlib import Path
from typing import Dict

from .legacy_adapters import LegacyAnalysisAdapter, _build_adapters_impl

AnalysisAdapter = LegacyAnalysisAdapter


def build_adapters(config_path: Path) -> Dict[str, AnalysisAdapter]:
    """Return native nmd-analysis adapter registry."""
    return _build_adapters_impl(config_path)


__all__ = [
    "AnalysisAdapter",
    "LegacyAnalysisAdapter",
    "build_adapters",
]
