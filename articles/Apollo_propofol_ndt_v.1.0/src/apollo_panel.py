"""Frozen 2026-09-21 within-subject stage panel.

Listed before inspecting dynamical stage effects. G3 independent review and
G4 lock were not completed; all inferential p-values are exploratory.
Reachability, destination, resilience and 9D are excluded.
"""
from __future__ import annotations

from dataclasses import dataclass

BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 20260920
MIN_TESTABLE_N = 10
ANALYSIS_ID = "stage_within_subject_20260921"
CONFIRMATORY_STATUS = "exploratory_discovery_20260921_g4_not_locked"

PHASES = (
    "pre_drug_baseline",
    "first_protocol_sedation",
    "later_protocol_sedation",
    "recovery",
)


@dataclass(frozen=True)
class ContrastSpec:
    contrast_id: str
    later_phase: str
    earlier_phase: str
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
    level: str | None = None


CONTRASTS = (
    ContrastSpec("first_sedation_minus_baseline", "first_protocol_sedation", "pre_drug_baseline", True, "H1_H2_primary"),
    ContrastSpec("later_sedation_minus_baseline", "later_protocol_sedation", "pre_drug_baseline", False, "secondary"),
    ContrastSpec("recovery_minus_baseline", "recovery", "pre_drug_baseline", False, "secondary"),
    ContrastSpec("later_minus_first_sedation", "later_protocol_sedation", "first_protocol_sedation", False, "secondary"),
    ContrastSpec("recovery_minus_first_sedation", "recovery", "first_protocol_sedation", False, "secondary"),
    ContrastSpec("recovery_minus_later_sedation", "recovery", "later_protocol_sedation", False, "secondary"),
)

METRICS = (
    MetricSpec(
        "diffusion_total",
        "diffusion",
        "H1",
        "dynamical_families/diffusion/v1/series/diffusion_total",
        "dynamical_families/diffusion/v1",
        "series",
        valid_path="dynamical_families/diffusion/v1/series/valid",
        extra_exclude_path="dynamical_families/diffusion/v1/series/psd_floor_applied",
        prediction_primary="later < earlier",
    ),
    MetricSpec(
        "diffusion_effective_dimension",
        "diffusion",
        "H2",
        "dynamical_families/diffusion/v1/series/diffusion_effective_dimension",
        "dynamical_families/diffusion/v1",
        "series",
        valid_path="dynamical_families/diffusion/v1/series/valid",
        extra_exclude_path="dynamical_families/diffusion/v1/series/psd_floor_applied",
        prediction_primary="later < earlier",
    ),
    MetricSpec(
        "R_b_over_a",
        "diffusion",
        "S1",
        "dynamical_families/diffusion/v1/series/R_b_over_a",
        "dynamical_families/diffusion/v1",
        "series",
        valid_path="dynamical_families/diffusion/v1/series/valid",
        prediction_primary="two-sided",
    ),
    MetricSpec(
        "A_bD",
        "diffusion",
        "S1",
        "dynamical_families/diffusion/v1/series/A_bD",
        "dynamical_families/diffusion/v1",
        "series",
        valid_path="dynamical_families/diffusion/v1/series/valid",
        prediction_primary="two-sided",
    ),
    MetricSpec(
        "diffusion_concentration",
        "diffusion",
        "exploratory",
        "dynamical_families/diffusion/v1/series/diffusion_concentration",
        "dynamical_families/diffusion/v1",
        "series",
        valid_path="dynamical_families/diffusion/v1/series/valid",
        prediction_primary="two-sided",
    ),
    MetricSpec(
        "neighbor_gain_q90",
        "amplification",
        "S2",
        "dynamical_families/amplification/v1/neighbor_gain_q90_level1/series/neighbor_gain_q90",
        "dynamical_families/amplification/v1/neighbor_gain_q90_level1",
        "series",
        prediction_primary="later < earlier",
    ),
    MetricSpec(
        "operator_max_gain_rate",
        "one_step",
        "S2",
        "dynamical_families/one_step/v1/operator_max_gain_rate_level2/series/operator_max_gain_rate",
        "dynamical_families/one_step/v1/operator_max_gain_rate_level2",
        "broadcast",
        prediction_primary="later < earlier",
    ),
    MetricSpec(
        "history_predictive_gain",
        "history",
        "S3",
        "dynamical_families/history/v1/history_predictive_gain_level1/summary/history_predictive_gain",
        "dynamical_families/history/v1/history_predictive_gain_level1",
        "summary",
        prediction_primary="two-sided",
    ),
    MetricSpec(
        "jacobian_spectral_abscissa",
        "jacobian",
        "exploratory",
        "jacobian/derived_metrics/v1/series/spectral_abscissa",
        "jacobian/derived_metrics/v1",
        "series",
        prediction_primary="two-sided",
    ),
    MetricSpec(
        "jacobian_trace",
        "jacobian",
        "exploratory",
        "jacobian/derived_metrics/v1/series/trace",
        "jacobian/derived_metrics/v1",
        "series",
        prediction_primary="two-sided",
    ),
    MetricSpec(
        "jacobian_rotation_norm",
        "jacobian",
        "exploratory",
        "jacobian/derived_metrics/v1/series/rotation_norm",
        "jacobian/derived_metrics/v1",
        "series",
        prediction_primary="two-sided",
    ),
    MetricSpec(
        "jacobian_reactivity_gap",
        "jacobian",
        "exploratory",
        "jacobian/derived_metrics/v1/series/reactivity_gap",
        "jacobian/derived_metrics/v1",
        "series",
        prediction_primary="two-sided",
    ),
    MetricSpec(
        "turning_rate",
        "turning",
        "exploratory",
        "dynamical_families/turning/v1/turning_rate_level0/series/turning_rate",
        "dynamical_families/turning/v1/turning_rate_level0",
        "series",
        prediction_primary="two-sided",
    ),
    MetricSpec(
        "ftr_g_max_h1",
        "finite_time_response",
        "exploratory",
        "finite_time_response/v1/primary/horizons/h1/series/g_max",
        "finite_time_response/v1/primary",
        "series",
        prediction_primary="two-sided",
    ),
    MetricSpec(
        "ftr_g_max_h2",
        "finite_time_response",
        "exploratory",
        "finite_time_response/v1/primary/horizons/h2/series/g_max",
        "finite_time_response/v1/primary",
        "series",
        prediction_primary="two-sided",
    ),
)

METRIC_BY_ID = {metric.metric_id: metric for metric in METRICS}
CONTRAST_BY_ID = {contrast.contrast_id: contrast for contrast in CONTRASTS}
