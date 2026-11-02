"""Frozen 2026-09-21 Jacobian-α + L1/L2/L3 panel (values present only).

Lag-2 one-step, A_bD, R_b_over_a, destination, resilience and L4 horizon maps
are omitted because they have no finite values on this export.
Exploratory; G4 not locked. Chart-Jacobian α is not one-step L3.
"""
from __future__ import annotations

from apollo_panel import CONTRASTS, MetricSpec

ANALYSIS_ID = "level_jl123_within_subject_20260921"
CONFIRMATORY_STATUS = "exploratory_discovery_20260921_g4_not_locked"
FILE_PREFIX = "level"


def _m(
    metric_id: str,
    family: str,
    level: str,
    value_path: str,
    cert_path: str,
    grain: str,
    *,
    reduce: str | None = None,
    valid_path: str | None = None,
) -> MetricSpec:
    return MetricSpec(
        metric_id=metric_id,
        family=family,
        role=level,
        value_path=value_path,
        cert_path=cert_path,
        grain=grain,
        valid_path=valid_path,
        reduce=reduce,
        level=level,
        prediction_primary="two-sided",
    )


LEVEL_METRICS = (
    _m(
        "jacobian_alpha",
        "jacobian",
        "jacobian_alpha",
        "jacobian/derived_metrics/v1/series/spectral_abscissa",
        "jacobian/derived_metrics/v1",
        "series",
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
    ),
    _m(
        "diffusion_total",
        "diffusion",
        "L1",
        "dynamical_families/diffusion/v1/series/diffusion_total",
        "dynamical_families/diffusion/v1",
        "series",
        valid_path="dynamical_families/diffusion/v1/series/valid",
    ),
    _m(
        "diffusion_effective_dimension",
        "diffusion",
        "L1",
        "dynamical_families/diffusion/v1/series/diffusion_effective_dimension",
        "dynamical_families/diffusion/v1",
        "series",
        valid_path="dynamical_families/diffusion/v1/series/valid",
    ),
    _m(
        "diffusion_concentration",
        "diffusion",
        "L1",
        "dynamical_families/diffusion/v1/series/diffusion_concentration",
        "dynamical_families/diffusion/v1",
        "series",
        valid_path="dynamical_families/diffusion/v1/series/valid",
    ),
    _m(
        "chart_drift_b_hat_norm",
        "chart_drift",
        "L1",
        "dynamical_families/drift/v1/conditional_mean_rate_level1/pooled/series/b_hat",
        "dynamical_families/drift/v1/conditional_mean_rate_level1/pooled",
        "series",
        reduce="l2",
    ),
    _m(
        "neighbor_gain_q90",
        "amplification",
        "L1",
        "dynamical_families/amplification/v1/neighbor_gain_q90_level1/series/neighbor_gain_q90",
        "dynamical_families/amplification/v1/neighbor_gain_q90_level1",
        "series",
    ),
    _m(
        "neighbor_gain_rate_q90",
        "amplification",
        "L1",
        "dynamical_families/amplification/v1/neighbor_gain_rate_q90_level1/series/neighbor_gain_rate_q90",
        "dynamical_families/amplification/v1/neighbor_gain_rate_q90_level1",
        "series",
    ),
    _m(
        "neighbor_separation_rate",
        "amplification",
        "L1",
        "dynamical_families/amplification/v1/neighbor_separation_rate_level1/series/neighbor_separation_rate",
        "dynamical_families/amplification/v1/neighbor_separation_rate_level1",
        "series",
    ),
    _m(
        "cloud_volume_change_rate",
        "amplification",
        "L1",
        "dynamical_families/amplification/v1/cloud_volume_change_rate_level1/series/cloud_volume_change_rate",
        "dynamical_families/amplification/v1/cloud_volume_change_rate_level1",
        "series",
    ),
    _m(
        "history_predictive_gain",
        "history",
        "L1",
        "dynamical_families/history/v1/history_predictive_gain_level1/summary/history_predictive_gain",
        "dynamical_families/history/v1/history_predictive_gain_level1",
        "summary",
    ),
    _m(
        "one_step_phi_frob",
        "one_step",
        "L2",
        "dynamical_families/one_step/v1/affine_one_step_map_level2/series/phi_hat",
        "dynamical_families/one_step/v1/affine_one_step_map_level2",
        "broadcast",
        reduce="frobenius",
    ),
    _m(
        "one_step_affine_mean_rate_norm",
        "one_step",
        "L2",
        "dynamical_families/one_step/v1/conditional_affine_mean_rate_level2/series/affine_mean_rate",
        "dynamical_families/one_step/v1/conditional_affine_mean_rate_level2",
        "broadcast",
        reduce="l2",
    ),
    _m(
        "one_step_innovation_trace",
        "one_step",
        "L2",
        "dynamical_families/one_step/v1/innovation_covariance_level2/series/innovation_covariance",
        "dynamical_families/one_step/v1/innovation_covariance_level2",
        "broadcast",
        reduce="trace",
    ),
    _m(
        "operator_max_gain_rate",
        "one_step",
        "L2",
        "dynamical_families/one_step/v1/operator_max_gain_rate_level2/series/operator_max_gain_rate",
        "dynamical_families/one_step/v1/operator_max_gain_rate_level2",
        "broadcast",
    ),
    _m(
        "operator_volume_gain_rate",
        "one_step",
        "L2",
        "dynamical_families/one_step/v1/operator_volume_gain_rate_level2/series/operator_volume_gain_rate",
        "dynamical_families/one_step/v1/operator_volume_gain_rate_level2",
        "broadcast",
    ),
    _m(
        "operator_rotation_rate",
        "one_step",
        "L2",
        "dynamical_families/one_step/v1/operator_rotation_rate_level2/series/operator_rotation_rate",
        "dynamical_families/one_step/v1/operator_rotation_rate_level2",
        "broadcast",
    ),
    _m(
        "history_conditioned_phi_frob",
        "history",
        "L2",
        "dynamical_families/history/v1/history_conditioned_operator_level2/series/phi_hat",
        "dynamical_families/history/v1/history_conditioned_operator_level2",
        "broadcast",
        reduce="frobenius",
    ),
    _m(
        "one_step_spectral_abscissa",
        "one_step",
        "L3",
        "dynamical_families/one_step/v1/spectral_abscissa_level3/series/spectral_abscissa",
        "dynamical_families/one_step/v1/spectral_abscissa_level3",
        "broadcast",
    ),
    _m(
        "one_step_numerical_abscissa",
        "one_step",
        "L3",
        "dynamical_families/one_step/v1/numerical_abscissa_level3/series/numerical_abscissa",
        "dynamical_families/one_step/v1/numerical_abscissa_level3",
        "broadcast",
    ),
    _m(
        "one_step_divergence",
        "one_step",
        "L3",
        "dynamical_families/one_step/v1/divergence_level3/series/divergence",
        "dynamical_families/one_step/v1/divergence_level3",
        "broadcast",
    ),
    _m(
        "one_step_generator_rotation_norm",
        "one_step",
        "L3",
        "dynamical_families/one_step/v1/generator_rotation_norm_level3/series/generator_rotation_norm",
        "dynamical_families/one_step/v1/generator_rotation_norm_level3",
        "broadcast",
    ),
)

LEVEL_CONTRASTS = CONTRASTS
METRIC_BY_ID = {metric.metric_id: metric for metric in LEVEL_METRICS}
