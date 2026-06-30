"""NDT analysis refactor package."""

from .adapters import AnalysisAdapter, build_adapters
from .analysis_pipeline import run_cleaned_analysis_pipeline
from .anchor_surface import (
    AnchorCapabilityProbe,
    AnchorCoupling,
    AnchorCouplingDiagnostics,
    AnchorQuality,
    AnchorState,
    AnchorStateDot,
    AnchorSurface,
    probe_anchor_capabilities_from_manifest,
    read_anchor_surface,
)
from .block_native import (
    DS003838_STAGE_LABELS,
    DS006036_STAGE_LABELS,
    SLEEP_STAGE_CODE_TO_LABEL,
    KNOWN_STAGE_LABELS,
    BlockStageSummary,
    RunInventory,
    build_run_inventory,
    combined_qc_mask,
    compute_stage_summaries,
    iter_subject_dirs,
    load_block_native_table,
    load_event_locked_table,
    load_run_block_native_table,
    load_run_event_locked_table,
    load_run_manifest,
    load_subject_summary,
    qc_mask_from_config,
    stage_labels_from_config,
    stage_labels_from_dataset_id,
    stage_labels_from_manifest,
    subject_center,
)
from .analysis_config import BlockNativeAnalysisConfig, BlockNativeQCConfig, load_analysis_config
from .pipeline import run_dataset_pipeline
from .regional_geometry import compute_regional_geometry
from .regional_mnps import (
    NetworkMNPS,
    RegionalMNPSResult,
    compute_regional_mnps,
    load_and_compute_regional_mnps,
)
from .regional_stratified_mnps import (
    NetworkStratifiedMNPS,
    RegionalStratifiedResult,
    compute_regional_stratified,
    load_and_compute_regional_stratified,
)

__all__ = [
    # adapters / pipelines
    "AnalysisAdapter",
    "build_adapters",
    "run_dataset_pipeline",
    "run_cleaned_analysis_pipeline",
    # embodied anchor surface (H5 reader)
    "AnchorState",
    "AnchorStateDot",
    "AnchorQuality",
    "AnchorCouplingDiagnostics",
    "AnchorCoupling",
    "AnchorSurface",
    "AnchorCapabilityProbe",
    "read_anchor_surface",
    "probe_anchor_capabilities_from_manifest",
    # analysis config (block_native section)
    "BlockNativeAnalysisConfig",
    "BlockNativeQCConfig",
    "load_analysis_config",
    # block-native sidecar loader
    "DS003838_STAGE_LABELS",
    "DS006036_STAGE_LABELS",
    "SLEEP_STAGE_CODE_TO_LABEL",
    "KNOWN_STAGE_LABELS",
    "stage_labels_from_config",
    "stage_labels_from_manifest",
    "stage_labels_from_dataset_id",
    "qc_mask_from_config",
    "BlockStageSummary",
    "RunInventory",
    "build_run_inventory",
    "combined_qc_mask",
    "compute_stage_summaries",
    "iter_subject_dirs",
    "load_block_native_table",
    "load_event_locked_table",
    "load_run_block_native_table",
    "load_run_event_locked_table",
    "load_run_manifest",
    "load_subject_summary",
    "subject_center",
    # regional MNPS
    "NetworkMNPS",
    "RegionalMNPSResult",
    "compute_regional_mnps",
    "load_and_compute_regional_mnps",
    "NetworkStratifiedMNPS",
    "RegionalStratifiedResult",
    "compute_regional_stratified",
    "load_and_compute_regional_stratified",
    "compute_regional_geometry",
]
