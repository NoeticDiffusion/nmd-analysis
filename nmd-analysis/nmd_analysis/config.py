from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml

from .h5_contract import DEFAULT_COORDINATE_CONTRACT, normalize_coordinate_contract


@dataclass(frozen=True)
class OutputConfig:
    directory: str
    filename_pattern: str
    timestamp_format: str
    parquet_compression: str
    parquet_index: bool


@dataclass(frozen=True)
class RuntimeConfig:
    fail_on_missing_input: bool
    skip_disabled_analyses: bool
    continue_on_analysis_error: bool
    workers: int | None


@dataclass(frozen=True)
class DatasetFlagsConfig:
    sleep_data_contrast: bool
    stage_code_map: Dict[int, str]
    min_stage_timepoints: int


@dataclass(frozen=True)
class DatasetConfig:
    dataset: str
    h5_root: str | None
    coordinate_contract: str
    output: OutputConfig
    runtime: RuntimeConfig
    analyses: Dict[str, bool]
    modality_rules: Dict[str, Any]
    flags: DatasetFlagsConfig


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _as_stage_code_map(value: Any) -> Dict[int, str]:
    if not isinstance(value, dict):
        return {}
    out: Dict[int, str] = {}
    for raw_key, raw_label in value.items():
        try:
            key = int(raw_key)
        except (TypeError, ValueError):
            continue
        label = str(raw_label).strip()
        if label:
            out[key] = label
    return out


def load_dataset_config(path: str | Path) -> DatasetConfig:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Config at {config_path} must be a mapping.")

    output_raw = raw.get("output") or {}
    if not isinstance(output_raw, dict):
        output_raw = {}
    parquet_raw = output_raw.get("parquet") or {}
    if not isinstance(parquet_raw, dict):
        parquet_raw = {}

    runtime_raw = raw.get("runtime") or {}
    if not isinstance(runtime_raw, dict):
        runtime_raw = {}

    flags_raw = raw.get("flags") or {}
    if not isinstance(flags_raw, dict):
        flags_raw = {}

    analyses_raw = raw.get("analyses") or {}
    if not isinstance(analyses_raw, dict):
        analyses_raw = {}

    analyses = {str(key): _as_bool(value, False) for key, value in analyses_raw.items()}
    dataset = str(raw.get("dataset") or "").strip()
    if not dataset:
        raise ValueError(f"Config at {config_path} is missing required key 'dataset'.")

    input_raw = raw.get("input") or {}
    if not isinstance(input_raw, dict):
        input_raw = {}
    h5_root = input_raw.get("h5_root")
    if h5_root is not None:
        h5_root = str(h5_root)

    output = OutputConfig(
        directory=str(output_raw.get("directory") or "nmd-analysis/outputs"),
        filename_pattern=str(
            output_raw.get("filename_pattern")
            or "{dataset}_{analysisType}_{timestamp}.parquet"
        ),
        timestamp_format=str(output_raw.get("timestamp_format") or "%Y%m%d_%H%M%S"),
        parquet_compression=str(parquet_raw.get("compression") or "snappy"),
        parquet_index=_as_bool(parquet_raw.get("index"), False),
    )
    runtime = RuntimeConfig(
        fail_on_missing_input=_as_bool(runtime_raw.get("fail_on_missing_input"), True),
        skip_disabled_analyses=_as_bool(runtime_raw.get("skip_disabled_analyses"), True),
        continue_on_analysis_error=_as_bool(runtime_raw.get("continue_on_analysis_error"), False),
        workers=_as_int(runtime_raw.get("workers")),
    )
    modality_rules = raw.get("modality_rules") or {}
    if not isinstance(modality_rules, dict):
        modality_rules = {}

    return DatasetConfig(
        dataset=dataset,
        h5_root=h5_root,
        coordinate_contract=normalize_coordinate_contract(
            raw.get("coordinate_contract"),
            default=DEFAULT_COORDINATE_CONTRACT,
        ),
        output=output,
        runtime=runtime,
        analyses=analyses,
        modality_rules=modality_rules,
        flags=DatasetFlagsConfig(
            sleep_data_contrast=_as_bool(flags_raw.get("sleep_data_contrast"), False),
            stage_code_map=_as_stage_code_map(flags_raw.get("stage_code_map")),
            min_stage_timepoints=_as_int(flags_raw.get("min_stage_timepoints")) or 20,
        ),
    )
