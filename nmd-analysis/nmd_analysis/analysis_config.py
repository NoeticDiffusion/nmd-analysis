from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .h5_contract import DEFAULT_COORDINATE_CONTRACT, normalize_coordinate_contract


@dataclass(frozen=True)
class BlockNativeQCConfig:
    """QC thresholds applied to block-native windows before analysis."""

    require_mnps_finite: bool
    min_anchor_support: float
    min_anchor_state_finite: int


@dataclass(frozen=True)
class BlockNativeAnalysisConfig:
    """Dataset-agnostic configuration for block-native surface analysis.

    YAML section ``block_native`` in analysis config files.

    ``stage_code_map`` maps integer stage codes to human-readable labels.
    An empty map means: use the numeric code as the label (fully generic).

    ``anchor_state_cols`` and ``anchor_quality_cols`` may be left empty to
    use the module-level defaults from ``block_native.py``.
    """

    stage_code_map: Dict[int, str]
    anchor_state_cols: List[str]
    anchor_dot_cols: List[str]
    anchor_quality_cols: List[str]
    hrv_cols: List[str]
    qc: BlockNativeQCConfig
    prefer_parquet: bool


@dataclass(frozen=True)
class AnalysisOutputConfig:
    directory: str
    filename_pattern: str
    timestamp_format: str
    parquet_compression: str
    parquet_index: bool


@dataclass(frozen=True)
class AnalysisRuntimeConfig:
    fail_on_missing_input: bool
    continue_on_error: bool


@dataclass(frozen=True)
class AnalysisQCConfig:
    require_finite_ok: bool
    exclude_not_testable: bool
    exclude_validity_limited: bool


@dataclass(frozen=True)
class AnalysisStatisticsConfig:
    permutation_n: int
    bootstrap_n: int
    random_seed: int
    min_group_n: int
    min_pairs: int
    fdr_group_by: List[str]


@dataclass(frozen=True)
class AnalysisDesignConfig:
    pairing_keys: List[str]
    condition_column: str
    group_column: str


@dataclass(frozen=True)
class AnalysisBlockConfig:
    enabled: bool
    metrics: Optional[List[str]]
    validity_min: Dict[str, float]
    validity_max: Dict[str, float]
    validity_require_true: List[str]
    validity_require_false: List[str]
    validity_require_nonnull: List[str]


@dataclass(frozen=True)
class ContrastConfig:
    name: str
    type: str
    left: Dict[str, Any]
    right: Dict[str, Any]
    subset: Dict[str, Any]
    analyses: Optional[List[str]]
    metrics: Optional[List[str]]
    pairing_keys: Optional[List[str]]


@dataclass(frozen=True)
class NegativeControlConfig:
    name: str
    type: str
    source_contrast: str
    analyses: Optional[List[str]]
    metrics: Optional[List[str]]
    pairing_keys: Optional[List[str]]
    stage_order: Optional[List[str]]
    permutation_n: Optional[int]


@dataclass(frozen=True)
class AnalysisConfig:
    dataset: str
    cleaned_root: str | None
    coordinate_contract: str
    output: AnalysisOutputConfig
    runtime: AnalysisRuntimeConfig
    qc: AnalysisQCConfig
    statistics: AnalysisStatisticsConfig
    design: AnalysisDesignConfig
    blocks: Dict[str, AnalysisBlockConfig]
    contrasts: List[ContrastConfig]
    negative_controls: List[NegativeControlConfig]
    block_native: BlockNativeAnalysisConfig = field(
        default_factory=lambda: _default_block_native_config()
    )


def _default_block_native_config() -> BlockNativeAnalysisConfig:
    return BlockNativeAnalysisConfig(
        stage_code_map={},
        anchor_state_cols=[],
        anchor_dot_cols=[],
        anchor_quality_cols=[],
        hrv_cols=[],
        qc=BlockNativeQCConfig(
            require_mnps_finite=True,
            min_anchor_support=0.3,
            min_anchor_state_finite=1,
        ),
        prefer_parquet=True,
    )


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _as_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed


def _as_list_of_str(value: Any) -> Optional[List[str]]:
    if value is None:
        return None
    if isinstance(value, str):
        items = [part.strip() for part in value.split(",") if part.strip()]
        return items or None
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()] or None
    return None


def _as_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _as_float_mapping(value: Any) -> Dict[str, float]:
    if not isinstance(value, dict):
        return {}
    out: Dict[str, float] = {}
    for key, raw_value in value.items():
        try:
            out[str(key)] = float(raw_value)
        except (TypeError, ValueError):
            continue
    return out


def load_analysis_config(path: str | Path) -> AnalysisConfig:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Analysis config at {config_path} must be a mapping.")

    dataset = str(raw.get("dataset") or "").strip()
    if not dataset:
        raise ValueError(f"Analysis config at {config_path} is missing required key 'dataset'.")

    input_raw = _as_mapping(raw.get("input"))
    cleaned_root = input_raw.get("cleaned_root")
    if cleaned_root is not None:
        cleaned_root = str(cleaned_root)

    output_raw = _as_mapping(raw.get("output"))
    parquet_raw = _as_mapping(output_raw.get("parquet"))
    runtime_raw = _as_mapping(raw.get("runtime"))
    qc_raw = _as_mapping(raw.get("qc"))
    stats_raw = _as_mapping(raw.get("statistics"))
    design_raw = _as_mapping(raw.get("design"))

    blocks_raw = raw.get("blocks") or {}
    if not isinstance(blocks_raw, dict):
        blocks_raw = {}
    blocks: Dict[str, AnalysisBlockConfig] = {}
    for key, value in blocks_raw.items():
        block_raw = _as_mapping(value)
        blocks[str(key)] = AnalysisBlockConfig(
            enabled=_as_bool(block_raw.get("enabled"), True),
            metrics=_as_list_of_str(block_raw.get("metrics")),
            validity_min=_as_float_mapping(_as_mapping(block_raw.get("validity")).get("min")),
            validity_max=_as_float_mapping(_as_mapping(block_raw.get("validity")).get("max")),
            validity_require_true=_as_list_of_str(_as_mapping(block_raw.get("validity")).get("require_true")) or [],
            validity_require_false=_as_list_of_str(_as_mapping(block_raw.get("validity")).get("require_false")) or [],
            validity_require_nonnull=_as_list_of_str(_as_mapping(block_raw.get("validity")).get("require_nonnull")) or [],
        )

    contrasts_raw = raw.get("contrasts") or []
    if not isinstance(contrasts_raw, list):
        contrasts_raw = []
    contrasts: List[ContrastConfig] = []
    for item in contrasts_raw:
        contrast_raw = _as_mapping(item)
        name = str(contrast_raw.get("name") or "").strip()
        if not name:
            continue
        contrast_type = str(contrast_raw.get("type") or "between_subject").strip().lower()
        contrasts.append(
            ContrastConfig(
                name=name,
                type=contrast_type,
                left=_as_mapping(contrast_raw.get("left")),
                right=_as_mapping(contrast_raw.get("right")),
                subset=_as_mapping(contrast_raw.get("subset")),
                analyses=_as_list_of_str(contrast_raw.get("analyses")),
                metrics=_as_list_of_str(contrast_raw.get("metrics")),
                pairing_keys=_as_list_of_str(contrast_raw.get("pairing_keys")),
            )
        )

    negative_controls_raw = raw.get("negative_controls") or []
    if not isinstance(negative_controls_raw, list):
        negative_controls_raw = []
    negative_controls: List[NegativeControlConfig] = []
    for item in negative_controls_raw:
        control_raw = _as_mapping(item)
        name = str(control_raw.get("name") or "").strip()
        source_contrast = str(control_raw.get("source_contrast") or "").strip()
        if not name or not source_contrast:
            continue
        negative_controls.append(
            NegativeControlConfig(
                name=name,
                type=str(control_raw.get("type") or "negative_control").strip().lower(),
                source_contrast=source_contrast,
                analyses=_as_list_of_str(control_raw.get("analyses")),
                metrics=_as_list_of_str(control_raw.get("metrics")),
                pairing_keys=_as_list_of_str(control_raw.get("pairing_keys")),
                stage_order=_as_list_of_str(control_raw.get("stage_order")),
                permutation_n=(
                    max(1, _as_int(control_raw.get("permutation_n"), 1000))
                    if control_raw.get("permutation_n") is not None
                    else None
                ),
            )
        )

    return AnalysisConfig(
        dataset=dataset,
        cleaned_root=cleaned_root,
        coordinate_contract=normalize_coordinate_contract(
            raw.get("coordinate_contract"),
            default=DEFAULT_COORDINATE_CONTRACT,
        ),
        output=AnalysisOutputConfig(
            directory=str(output_raw.get("directory") or "data/analysis"),
            filename_pattern=str(
                output_raw.get("filename_pattern")
                or "{dataset}_{analysisType}_{timestamp}.parquet"
            ),
            timestamp_format=str(output_raw.get("timestamp_format") or "%Y%m%d_%H%M%S"),
            parquet_compression=str(parquet_raw.get("compression") or "snappy"),
            parquet_index=_as_bool(parquet_raw.get("index"), False),
        ),
        runtime=AnalysisRuntimeConfig(
            fail_on_missing_input=_as_bool(runtime_raw.get("fail_on_missing_input"), True),
            continue_on_error=_as_bool(runtime_raw.get("continue_on_error"), False),
        ),
        qc=AnalysisQCConfig(
            require_finite_ok=_as_bool(qc_raw.get("require_finite_ok"), True),
            exclude_not_testable=_as_bool(qc_raw.get("exclude_not_testable"), True),
            exclude_validity_limited=_as_bool(qc_raw.get("exclude_validity_limited"), False),
        ),
        statistics=AnalysisStatisticsConfig(
            permutation_n=max(100, _as_int(stats_raw.get("permutation_n"), 2000)),
            bootstrap_n=max(100, _as_int(stats_raw.get("bootstrap_n"), 1000)),
            random_seed=_as_int(stats_raw.get("random_seed"), 13),
            min_group_n=max(2, _as_int(stats_raw.get("min_group_n"), 3)),
            min_pairs=max(2, _as_int(stats_raw.get("min_pairs"), 3)),
            fdr_group_by=_as_list_of_str(stats_raw.get("fdr_group_by"))
            or ["contrast_name", "analysis_type"],
        ),
        design=AnalysisDesignConfig(
            pairing_keys=_as_list_of_str(design_raw.get("pairing_keys"))
            or ["subject_id", "session", "run"],
            condition_column=str(design_raw.get("condition_column") or "condition"),
            group_column=str(design_raw.get("group_column") or "group"),
        ),
        blocks=blocks,
        contrasts=contrasts,
        negative_controls=negative_controls,
        block_native=_parse_block_native_config(_as_mapping(raw.get("block_native"))),
    )


def _parse_stage_code_map(value: Any) -> Dict[int, str]:
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


def _parse_block_native_config(raw: Dict[str, Any]) -> BlockNativeAnalysisConfig:
    if not raw:
        return _default_block_native_config()

    qc_raw = _as_mapping(raw.get("qc"))

    def _col_list(key: str) -> List[str]:
        val = raw.get(key)
        items = _as_list_of_str(val)
        return items if items is not None else []

    return BlockNativeAnalysisConfig(
        stage_code_map=_parse_stage_code_map(raw.get("stage_code_map")),
        anchor_state_cols=_col_list("anchor_state_cols"),
        anchor_dot_cols=_col_list("anchor_dot_cols"),
        anchor_quality_cols=_col_list("anchor_quality_cols"),
        hrv_cols=_col_list("hrv_cols"),
        qc=BlockNativeQCConfig(
            require_mnps_finite=_as_bool(qc_raw.get("require_mnps_finite"), True),
            min_anchor_support=float(qc_raw.get("min_anchor_support", 0.3)),
            min_anchor_state_finite=max(0, _as_int(qc_raw.get("min_anchor_state_finite"), 1)),
        ),
        prefer_parquet=_as_bool(raw.get("prefer_parquet"), True),
    )
