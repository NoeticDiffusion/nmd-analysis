"""Frozen 2026-09-21 Jacobian-α + L2/L3 one-step panel (values present only).

Lag-2 one-step and iterated L4 maps are omitted: lag-2 has no computed
identities on this export; iterated horizon maps are computed on 14/134 files.
Exploratory; G4 not locked. Chart-Jacobian α is not one-step L3.
"""
from __future__ import annotations

from ds04511_panel import CONTRASTS, MetricSpec, _m

ANALYSIS_ID = "level_jl23_within_subject_20260921"
CONFIRMATORY_STATUS = "exploratory_discovery_20260921_g4_not_locked"
FILE_PREFIX = "level"

LEVEL_METRICS = (
    _m(
        "jacobian_alpha",
        "jacobian",
        "jacobian_alpha",
        "jacobian/derived_metrics/v1/series/spectral_abscissa",
        "jacobian/derived_metrics/v1",
        "series",
        level="jacobian_alpha",
    ),
    _m(
        "one_step_phi_frob",
        "one_step",
        "L2",
        "dynamical_families/one_step/v1/affine_one_step_map_level2/series/phi_hat",
        "dynamical_families/one_step/v1/affine_one_step_map_level2",
        "broadcast",
        reduce="frobenius",
        level="L2",
    ),
    _m(
        "one_step_affine_mean_rate_norm",
        "one_step",
        "L2",
        "dynamical_families/one_step/v1/conditional_affine_mean_rate_level2/series/affine_mean_rate",
        "dynamical_families/one_step/v1/conditional_affine_mean_rate_level2",
        "broadcast",
        reduce="l2",
        level="L2",
    ),
    _m(
        "one_step_innovation_trace",
        "one_step",
        "L2",
        "dynamical_families/one_step/v1/innovation_covariance_level2/series/innovation_covariance",
        "dynamical_families/one_step/v1/innovation_covariance_level2",
        "broadcast",
        reduce="trace",
        level="L2",
    ),
    _m(
        "operator_max_gain_rate",
        "one_step",
        "L2",
        "dynamical_families/one_step/v1/operator_max_gain_rate_level2/series/operator_max_gain_rate",
        "dynamical_families/one_step/v1/operator_max_gain_rate_level2",
        "broadcast",
        level="L2",
    ),
    _m(
        "operator_volume_gain_rate",
        "one_step",
        "L2",
        "dynamical_families/one_step/v1/operator_volume_gain_rate_level2/series/operator_volume_gain_rate",
        "dynamical_families/one_step/v1/operator_volume_gain_rate_level2",
        "broadcast",
        level="L2",
    ),
    _m(
        "operator_rotation_rate",
        "one_step",
        "L2",
        "dynamical_families/one_step/v1/operator_rotation_rate_level2/series/operator_rotation_rate",
        "dynamical_families/one_step/v1/operator_rotation_rate_level2",
        "broadcast",
        level="L2",
    ),
    _m(
        "history_conditioned_phi_frob",
        "history",
        "L2",
        "dynamical_families/history/v1/history_conditioned_operator_level2/series/phi_hat",
        "dynamical_families/history/v1/history_conditioned_operator_level2",
        "broadcast",
        reduce="frobenius",
        level="L2",
    ),
    _m(
        "one_step_spectral_abscissa",
        "one_step",
        "L3",
        "dynamical_families/one_step/v1/spectral_abscissa_level3/series/spectral_abscissa",
        "dynamical_families/one_step/v1/spectral_abscissa_level3",
        "broadcast",
        level="L3",
    ),
    _m(
        "one_step_numerical_abscissa",
        "one_step",
        "L3",
        "dynamical_families/one_step/v1/numerical_abscissa_level3/series/numerical_abscissa",
        "dynamical_families/one_step/v1/numerical_abscissa_level3",
        "broadcast",
        level="L3",
    ),
    _m(
        "one_step_divergence",
        "one_step",
        "L3",
        "dynamical_families/one_step/v1/divergence_level3/series/divergence",
        "dynamical_families/one_step/v1/divergence_level3",
        "broadcast",
        level="L3",
    ),
    _m(
        "one_step_generator_rotation_norm",
        "one_step",
        "L3",
        "dynamical_families/one_step/v1/generator_rotation_norm_level3/series/generator_rotation_norm",
        "dynamical_families/one_step/v1/generator_rotation_norm_level3",
        "broadcast",
        level="L3",
    ),
)

LEVEL_CONTRASTS = CONTRASTS
METRIC_BY_ID = {metric.metric_id: metric for metric in LEVEL_METRICS}
