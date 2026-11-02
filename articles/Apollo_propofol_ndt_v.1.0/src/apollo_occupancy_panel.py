"""Frozen 2026-09-21 occupancy / state-relocation primary line.

Exact scalar from the baseline-anchor C3 pipeline. No new metrics.
"""
from __future__ import annotations

from apollo_c3_panel import SPECTRAL_FEATURES
from apollo_panel import PHASES

ANALYSIS_ID = "occupancy_relocation_20260921"
CONFIRMATORY_STATUS = "exploratory_discovery_20260921_g4_not_locked"
FILE_PREFIX = "occupancy"
BASELINE_PHASE = "pre_drug_baseline"
PRIMARY_LATER_PHASE = "first_protocol_sedation"
ORDERED_LATERS = (
    "first_protocol_sedation",
    "later_protocol_sedation",
    "recovery",
)
OCCUPANCY_FEATURES = SPECTRAL_FEATURES
PROTOCOL_PHASES = PHASES
PRIMARY_CONTRAST_ID = "first_sedation_minus_baseline"
PREDICTION_PRIMARY = "later > earlier"
C3_ANCHOR_SUBJECTS = "results/v1_c3_anchor_20260921/c3_anchor_subject.csv"
