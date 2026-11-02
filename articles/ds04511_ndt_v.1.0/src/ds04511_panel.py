"""Frozen 2026-09-21 within-subject Rest / CC / GG NDT v1.0 panel.

Listed before inspecting task effects. G3 independent review and G4 lock
were not completed; all inferential p-values are exploratory.

Occupancy (m, d, e) is chart state, not reachability and not MNJ.
Destination, FAR, committor, 9D, and C/TI/P are excluded from this first cut.
The reachability effective-dimension readout is retained for QC only because
the L4 audit found it rank-degenerate; it is not part of substantive
Wilcoxon/Friedman families.
"""
from __future__ import annotations

from dataclasses import dataclass

BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 20260921
MIN_TESTABLE_N = 10
ANALYSIS_ID = "task_within_subject_20260921"
CONFIRMATORY_STATUS = "exploratory_discovery_20260921_g4_not_locked"

TASKS = ("rest", "cognitive_control", "gambling")


@dataclass(frozen=True)
class ContrastSpec:
    contrast_id: str
    later_task: str
    earlier_task: str
    primary: bool
    role: str


@dataclass(frozen=True)
class MetricSpec:
    metric_id: str
    family: str
    role: str
    value_path: str
    cert_path: str
    grain: str
    valid_path: str | None = None
    extra_exclude_path: str | None = None
    prediction_primary: str = "two-sided"
    reduce: str | None = None
    column: int | None = None
    require_computed: bool = True
    level: str | None = None


CONTRASTS = (
    ContrastSpec(
        "gambling_minus_rest",
        "gambling",
        "rest",
        True,
        "task_vs_rest",
    ),
    ContrastSpec(
        "cognitive_control_minus_rest",
        "cognitive_control",
        "rest",
        True,
        "task_vs_rest",
    ),
    ContrastSpec(
        "gambling_minus_cognitive_control",
        "gambling",
        "cognitive_control",
        True,
        "cross_task",
    ),
)


def _m(
    metric_id: str,
    family: str,
    role: str,
    value_path: str,
    cert_path: str,
    grain: str,
    *,
    valid_path: str | None = None,
    extra_exclude_path: str | None = None,
    reduce: str | None = None,
    column: int | None = None,
    require_computed: bool = True,
    level: str | None = None,
) -> MetricSpec:
    return MetricSpec(
        metric_id=metric_id,
        family=family,
        role=role,
        value_path=value_path,
        cert_path=cert_path,
        grain=grain,
        valid_path=valid_path,
        extra_exclude_path=extra_exclude_path,
        reduce=reduce,
        column=column,
        require_computed=require_computed,
        level=level,
        prediction_primary="two-sided",
    )


METRICS = (
    _m(
        "occupancy_m",
        "occupancy",
        "occupancy",
        "coords_3d_subject_anchored/values",
        "provenance/geometry_contract/mnps_3d",
        "series",
        valid_path="qc/windows/mnps_3d_valid",
        column=0,
        require_computed=False,
        level="occupancy",
    ),
    _m(
        "occupancy_d",
        "occupancy",
        "occupancy",
        "coords_3d_subject_anchored/values",
        "provenance/geometry_contract/mnps_3d",
        "series",
        valid_path="qc/windows/mnps_3d_valid",
        column=1,
        require_computed=False,
        level="occupancy",
    ),
    _m(
        "occupancy_e",
        "occupancy",
        "occupancy",
        "coords_3d_subject_anchored/values",
        "provenance/geometry_contract/mnps_3d",
        "series",
        valid_path="qc/windows/mnps_3d_valid",
        column=2,
        require_computed=False,
        level="occupancy",
    ),
    _m(
        "jacobian_spectral_abscissa",
        "jacobian",
        "mnj",
        "jacobian/derived_metrics/v1/series/spectral_abscissa",
        "jacobian/derived_metrics/v1",
        "series",
        level="mnj",
    ),
    _m(
        "jacobian_numerical_abscissa",
        "jacobian",
        "mnj",
        "jacobian/derived_metrics/v1/series/numerical_abscissa",
        "jacobian/derived_metrics/v1",
        "series",
        level="mnj",
    ),
    _m(
        "jacobian_reactivity_gap",
        "jacobian",
        "mnj",
        "jacobian/derived_metrics/v1/series/reactivity_gap",
        "jacobian/derived_metrics/v1",
        "series",
        level="mnj",
    ),
    _m(
        "jacobian_trace",
        "jacobian",
        "mnj",
        "jacobian/derived_metrics/v1/series/trace",
        "jacobian/derived_metrics/v1",
        "series",
        level="mnj",
    ),
    _m(
        "jacobian_rotation_norm",
        "jacobian",
        "mnj",
        "jacobian/derived_metrics/v1/series/rotation_norm",
        "jacobian/derived_metrics/v1",
        "series",
        level="mnj",
    ),
    _m(
        "jacobian_frobenius_norm",
        "jacobian",
        "mnj",
        "jacobian/derived_metrics/v1/series/frobenius_norm",
        "jacobian/derived_metrics/v1",
        "series",
        level="mnj",
    ),
    _m(
        "diffusion_a_hat_frob",
        "diffusion",
        "L1",
        "dynamical_families/diffusion/v1/series/a_hat",
        "dynamical_families/diffusion/v1",
        "series",
        reduce="frobenius",
        valid_path="dynamical_families/diffusion/v1/series/valid",
        extra_exclude_path="dynamical_families/diffusion/v1/series/psd_floor_applied",
        level="L1",
    ),
    _m(
        "diffusion_total",
        "diffusion",
        "L1",
        "dynamical_families/diffusion/v1/series/diffusion_total",
        "dynamical_families/diffusion/v1",
        "series",
        valid_path="dynamical_families/diffusion/v1/series/valid",
        extra_exclude_path="dynamical_families/diffusion/v1/series/psd_floor_applied",
        level="L1",
    ),
    _m(
        "diffusion_effective_dimension",
        "diffusion",
        "L1",
        "dynamical_families/diffusion/v1/series/diffusion_effective_dimension",
        "dynamical_families/diffusion/v1",
        "series",
        valid_path="dynamical_families/diffusion/v1/series/valid",
        extra_exclude_path="dynamical_families/diffusion/v1/series/psd_floor_applied",
        level="L1",
    ),
    _m(
        "chart_drift_b_hat_norm",
        "chart_drift",
        "L1",
        "dynamical_families/drift/v1/conditional_mean_rate_level1/pooled/series/b_hat",
        "dynamical_families/drift/v1/conditional_mean_rate_level1/pooled",
        "series",
        reduce="l2",
        valid_path="dynamical_families/drift/v1/conditional_mean_rate_level1/pooled/series/valid",
        level="L1",
    ),
    _m(
        "reach_d_eff",
        "reachability",
        "L4",
        "stochastic_reachability/v1/primary/d_eff",
        "stochastic_reachability/v1/primary",
        "summary",
        level="L4",
    ),
    _m(
        "reach_a_q",
        "reachability",
        "L4",
        "stochastic_reachability/v1/primary/a_q",
        "stochastic_reachability/v1/primary",
        "summary",
        level="L4",
    ),
    _m(
        "reach_v_norm",
        "reachability",
        "L4",
        "stochastic_reachability/v1/primary/v_norm",
        "stochastic_reachability/v1/primary",
        "summary",
        level="L4",
    ),
)

METRIC_BY_ID = {metric.metric_id: metric for metric in METRICS}
CONTRAST_BY_ID = {contrast.contrast_id: contrast for contrast in CONTRASTS}

# ``reach_d_eff`` remains in the extraction/paired tables so the degeneracy
# audit is reproducible, but it is not a substantive dimension endpoint.
QC_ONLY_METRIC_IDS = frozenset({"reach_d_eff"})
SUBSTANTIVE_METRIC_IDS = tuple(
    metric.metric_id for metric in METRICS if metric.metric_id not in QC_ONLY_METRIC_IDS
)


def metric_test_scope(metric_id: str) -> str:
    """Return the inferential scope without changing metric extraction."""
    return "qc_only_degenerate" if metric_id in QC_ONLY_METRIC_IDS else "substantive"
