from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from c2_train_only_accessibility import (  # noqa: E402
    C2UnavailableError,
    FEATURE_NAME,
    fit_c2_training_atlas,
    estimate_c2_origin_feature,
)


def synthetic_transitions(seed: int = 13) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for pid_index in range(12):
        pid = f"p{pid_index:02d}"
        base = rng.normal(size=3)
        for step in range(4):
            origin = base + rng.normal(scale=0.08, size=3)
            target = origin + rng.normal(scale=0.2, size=3)
            epoch = step
            rows.append({
                "pid": pid,
                "recording_id": f"r-{pid}",
                "segment_id": "seg-0",
                "target_segment_id": "seg-0",
                "epoch_id": epoch,
                "target_epoch_id": epoch + 1,
                "origin_time_seconds": epoch * 30.0,
                "target_time_seconds": (epoch + 1) * 30.0,
                "source_support_ok": True,
                "origin_coordinate_qc_ok": True,
                "target_coordinate_qc_ok": True,
                "origin_m": origin[0], "origin_d": origin[1], "origin_e": origin[2],
                "target_m": target[0], "target_d": target[1], "target_e": target[2],
            })
    return pd.DataFrame(rows)


def synthetic_query(pid: str = "heldout", point: np.ndarray | None = None) -> pd.DataFrame:
    x = np.zeros(3) if point is None else np.asarray(point, dtype=float)
    return pd.DataFrame([{
        "pid": pid, "recording_id": f"r-{pid}", "segment_id": "seg-0",
        "epoch_id": 20, "time_seconds": 600.0,
        "source_support_ok": True, "coordinate_qc_ok": True,
        "m": x[0], "d": x[1], "e": x[2],
    }])


def fit_atlas(rows: pd.DataFrame | None = None):
    transitions = synthetic_transitions() if rows is None else rows
    pids = sorted(transitions.pid.unique())
    return fit_c2_training_atlas(
        transitions,
        training_pids=pids,
        scale_training_pids=pids,
        outer_training_iqr=(1.0, 1.0, 1.0),
        n_neighbors=8,
    )


def test_candidate_uses_training_only_neighbors_and_returns_one_scalar():
    transitions = synthetic_transitions()
    atlas = fit_atlas(transitions)
    query_point = transitions.loc[:, ["origin_m", "origin_d", "origin_e"]].median().to_numpy(dtype=float)
    result = estimate_c2_origin_feature(atlas, synthetic_query(point=query_point), partition="apply")
    assert result.loc[0, "c2_feature_status"] == "candidate_computed"
    assert np.isfinite(result.loc[0, FEATURE_NAME])
    assert result.loc[0, "c2_neighbor_pid_count"] == 8
    assert np.isfinite(result.loc[0, "c2_neighbor_radius_scaled"])


def test_apply_query_rejects_future_target_column_and_training_pid_overlap():
    transitions = synthetic_transitions()
    atlas = fit_atlas(transitions)
    query = synthetic_query(point=transitions.loc[0, ["origin_m", "origin_d", "origin_e"]].to_numpy())
    with pytest.raises(C2UnavailableError, match="schema mismatch"):
        estimate_c2_origin_feature(atlas, query.assign(target_m=9999.0), partition="apply")
    with pytest.raises(C2UnavailableError, match="overlaps"):
        estimate_c2_origin_feature(atlas, synthetic_query(pid="p00"), partition="apply")


def test_query_support_failure_is_unavailable_not_zero():
    atlas = fit_atlas()
    query = synthetic_query().assign(source_support_ok=False)
    result = estimate_c2_origin_feature(atlas, query, partition="apply")
    assert result.loc[0, "c2_feature_status"] == "unavailable"
    assert result.loc[0, "c2_feature_reason"] == "source_support_ineligible"
    assert np.isnan(result.loc[0, FEATURE_NAME])


def test_bad_training_horizon_segment_or_gap_pair_is_excluded():
    transitions = synthetic_transitions()
    transitions.loc[0, "target_epoch_id"] += 1
    transitions.loc[1, "target_segment_id"] = "other-segment"
    transitions.loc[2, "target_time_seconds"] += 30.0
    atlas = fit_atlas(transitions)
    assert len(atlas.origin_states_scaled) == len(transitions) - 3
    assert atlas.pair_exclusion_counts["wrong_h1_row_lag"] == 1
    assert atlas.pair_exclusion_counts["segment_mismatch_or_missing"] == 1
    assert atlas.pair_exclusion_counts["noncontiguous_or_wrong_h1_time"] == 1


def test_candidate_covariance_uses_training_pid_set_only():
    transitions = synthetic_transitions()
    training = transitions.loc[transitions.pid != "p00"].copy()
    with pytest.raises(C2UnavailableError, match="outside the declared training roster"):
        fit_c2_training_atlas(
            transitions,
            training_pids=sorted(training.pid.unique()),
            scale_training_pids=sorted(transitions.pid.unique()),
            outer_training_iqr=(1.0, 1.0, 1.0),
            n_neighbors=8,
        )


def test_training_feature_crossfit_excludes_its_pid_from_transitions_and_scale():
    transitions = synthetic_transitions()
    heldout_train_pid = "p00"
    library = transitions.loc[transitions.pid != heldout_train_pid].copy()
    scale_roster = sorted(pid for pid in transitions.pid.unique() if pid != heldout_train_pid)
    atlas = fit_c2_training_atlas(
        library,
        training_pids=sorted(library.pid.unique()),
        scale_training_pids=scale_roster,
        outer_training_iqr=(1.0, 1.0, 1.0),
        n_neighbors=8,
    )
    assert heldout_train_pid not in atlas.training_pids
    query_point = transitions.loc[transitions.pid.eq(heldout_train_pid), ["origin_m", "origin_d", "origin_e"]].median().to_numpy()
    result = estimate_c2_origin_feature(
        atlas,
        synthetic_query(pid=heldout_train_pid, point=query_point),
        partition="training_oof",
    )
    assert result.loc[0, "c2_neighbor_pid_count"] == 8
