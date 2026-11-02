"""Frozen 2026-09-21 occupancy LOR/ROR constants.

Chennu binomial-CI labels on n_correct / 40. Occupancy scalar is not recomputed.
"""
from __future__ import annotations

from apollo_occupancy_panel import BASELINE_PHASE, ORDERED_LATERS

ANALYSIS_ID = "occupancy_lor_20260921"
CONFIRMATORY_STATUS = "exploratory_discovery_20260921_g4_not_locked"
FILE_PREFIX = "lor"
MODERATE_PHASE = "later_protocol_sedation"
RECOVERY_PHASE = "recovery"
FIRST_PHASE = "first_protocol_sedation"
PRIMARY_CONTRAST_ID = "later_sedation_minus_baseline_lor_vs_responsive"
PREDICTION_PRIMARY = "lor_impaired occupancy Δ > responsive occupancy Δ"
OCCUPANCY_SUBJECT = "results/v1_occupancy_20260921/occupancy_subject.csv"
OCCUPANCY_CONTRASTS = "results/v1_occupancy_20260921/occupancy_contrasts.csv"
OCCUPANCY_SUPPORT = "results/v1_occupancy_20260921/c3_anchor_match_support.csv"
CHENNU_N_IMPAIRED = 7
CHENNU_N_RESPONSIVE = 13
PHASE_COLUMNS = (BASELINE_PHASE, *ORDERED_LATERS)
