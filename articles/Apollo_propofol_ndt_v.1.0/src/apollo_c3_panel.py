"""Frozen 2026-09-21 matched-state C3 constants.

Exploratory; G4 not locked. Does not reopen the 132-test level panel.
"""
from __future__ import annotations

ANALYSIS_ID = "matched_state_c3_20260921"
CONFIRMATORY_STATUS = "exploratory_discovery_20260921_g4_not_locked"
FILE_PREFIX = "c3"

LATER_PHASE = "first_protocol_sedation"
EARLIER_PHASE = "pre_drug_baseline"
CONTRAST_ID = "first_sedation_minus_baseline"

COORD_PATH = "coords_3d_subject_anchored/values"
DXDT_PATH = "dynamical_families/drift/v1/realized_velocity_level0/series/dx_dt"
DXDT_VALID_PATH = "dynamical_families/drift/v1/realized_velocity_level0/series/valid"
DXDT_DT_PATH = "dynamical_families/drift/v1/realized_velocity_level0/series/observed_dt"
FEATURE_VALUES_PATH = "features_raw/values"
FEATURE_NAMES_PATH = "features_raw/names"

SPECTRAL_FEATURES = (
    "eeg_delta",
    "eeg_theta",
    "eeg_alpha",
    "eeg_beta",
    "eeg_gamma",
    "eeg_alpha_theta",
    "eeg_beta_alpha",
    "eeg_sample_entropy",
)

DT_MIN = 3.8
DT_MAX = 4.2
CALIPER_MULTIPLIER = 1.0
MIN_PAIRS = 20
MIN_TESTABLE_N = 10
MAD_FLOOR = 1e-8
BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 20260920
RANDOM_MATCH_SEED = 20260920

PRIMARY_ENDPOINTS = ("matched_speed", "matched_spread")
