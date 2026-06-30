from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd


def rows_to_frame(rows: Iterable[Dict[str, Any]]) -> pd.DataFrame:
    data: List[Dict[str, Any]] = [dict(row) for row in rows]
    return pd.DataFrame(data)


def write_parquet_table(
    rows: Iterable[Dict[str, Any]],
    output_path: str | Path,
    compression: str = "snappy",
    index: bool = False,
) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame = rows_to_frame(rows)
    frame.to_parquet(out, compression=compression, index=index)
    return out


def write_parquet_frame(
    frame: pd.DataFrame,
    output_path: str | Path,
    compression: str = "snappy",
    index: bool = False,
) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out, compression=compression, index=index)
    return out


def read_parquet_table(path: str | Path) -> pd.DataFrame:
    return pd.read_parquet(Path(path))
