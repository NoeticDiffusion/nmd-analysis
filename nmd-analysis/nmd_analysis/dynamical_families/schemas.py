"""Schema constants and small validation helpers for NMD v3 family exports."""
from __future__ import annotations

FAMILY_SCHEMA = {
    "diffusion": "mndm.diffusion_geometry.v1",
    "destination": "mndm.committor.v1",
    "resilience": "mndm.finite_amplitude_resilience.v1",
    "chart_drift": "mndm.chart_drift.v1",
    "one_step": "mndm.affine_one_step.v1",
    "amplification": "mndm.amplification.v1",
    "history": "mndm.history.v1",
    "turning": "mndm.turning.v1",
}
# API family_id → HDF5 group name under /dynamical_families/.
FAMILY_H5_NAME = {
    "chart_drift": "drift",
}
LEGACY_NAME = {
    "diffusion": "diffusion_geometry",
    "destination": "committor",
    "resilience": "finite_amplitude_resilience",
}
FAMILY_IDS = tuple(FAMILY_SCHEMA)
KNOWN_STATUSES = frozenset({
    "computed",
    "not_requested",
    "not_testable",
    "insufficient_support",
    "invalid",
    "not_recorded",
})
# Subgroups that belong to a family/identity payload, not nested identities.
PARENT_SUBGROUPS = frozenset({"series", "summary", "provenance", "grain", "amplitude_curve"})
# Series that index lag-1 (or lag-k) source transitions, not the MNPS time grid.
TRANSITION_INDEX_FIELDS = frozenset({"source_idx"})

ONE_STEP_IDENTITIES = (
    "affine_one_step_map_level2",
    "conditional_affine_mean_rate_level2",
    "innovation_covariance_level2",
    "operator_max_gain_rate_level2",
    "operator_volume_gain_rate_level2",
    "operator_rotation_rate_level2",
    "spectral_abscissa_level3",
    "numerical_abscissa_level3",
    "divergence_level3",
    "generator_rotation_norm_level3",
    "iterated_one_step_horizon_map_level4",
)
AMPLIFICATION_IDENTITIES = (
    "neighbor_gain_q90_level1",
    "neighbor_gain_rate_q90_level1",
    "neighbor_separation_rate_level1",
    "cloud_volume_change_rate_level1",
)
AMPLIFICATION_PRIMARY = {
    "neighbor_gain_q90_level1": "neighbor_gain_q90",
    "neighbor_gain_rate_q90_level1": "neighbor_gain_rate_q90",
    "neighbor_separation_rate_level1": "neighbor_separation_rate",
    "cloud_volume_change_rate_level1": "cloud_volume_change_rate",
}


def h5_family_name(family: str) -> str:
    return FAMILY_H5_NAME.get(family, family)


def validate_schema(family: str, schema_version: object) -> str:
    expected = FAMILY_SCHEMA[family]
    value = str(schema_version)
    if value != expected:
        raise ValueError(f"unsupported {family} schema_version {value!r}; expected {expected!r}")
    return value


def with_table_identity(row: dict, *, family: str, grain: str) -> dict:
    row["family_id"] = family
    row["grain"] = grain
    row["table_grain"] = grain
    row["table_schema"] = "nmd_analysis.dynamical_families.v1"
    return row
