import numpy as np
import pandas as pd
import pytest

from src.fullnight_stage_description import _load_policy, _mask_states


def test_mask_state_counts_preserve_unknown_and_invalid():
    frame = pd.DataFrame({
        "producer_mask_coverage_ok": [1, 0, np.nan, 2],
        "producer_mask_retained_after_qc": [1, 1, 1, 1],
        "producer_mask_geometry_valid": [1, 1, 1, 1],
        "producer_mask_coords_9d_valid": [1, 1, 1, 1],
    })
    result = _mask_states(frame)
    assert result["coverage_ok"] == {"true": 1, "false": 1, "unknown": 1, "invalid": 1}
    assert result["retained_after_qc"]["true"] == 4


def test_missing_mask_is_explicitly_unknown():
    frame = pd.DataFrame({"producer_mask_coverage_ok": [1, 1]})
    result = _mask_states(frame)
    assert result["geometry_valid"] == {"true": 0, "false": 0, "unknown": 2, "invalid": 0}


def test_policy_rejects_relaxed_or_non_descriptive_contract(tmp_path):
    policy = tmp_path / "policy.json"
    policy.write_text('{"schema":"wrong"}', encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported"):
        _load_policy(policy)
