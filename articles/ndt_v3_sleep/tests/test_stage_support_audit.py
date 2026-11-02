import numpy as np
import pandas as pd

from stage_support_audit import audit_bouts, raw_alignment


def _epochs():
    return pd.DataFrame({
        "window_id": [0, 1, 2, 4, 5, 6],
        "window_start": [0., 30., 60., 120., 150., 180.],
        "window_end": [30., 60., 90., 150., 180., 210.],
        "stage_code": [1, 1, 3, 3, 8, 3],
        "stage_label": ["N1", "N1", "N3", "N3", None, "N3"],
        "stage_label_status": ["recorded", "recorded", "recorded", "recorded", "missing_or_unknown", "recorded"],
    })


def test_bouts_split_on_id_gap_and_unknown_code_with_known_lengths():
    bouts, summary = audit_bouts(_epochs())
    assert bouts[["stage_code", "n_windows"]].values.tolist() == [[1, 2], [3, 1], [3, 1], [8, 1], [3, 1]]
    n1 = summary.loc[summary.stage_code == 1].iloc[0]
    n3 = summary.loc[summary.stage_code == 3].iloc[0]
    assert (int(n1.n_bouts), int(n1.n_windows), n1.bout_lengths_windows) == (1, 2, "2")
    assert (int(n3.n_bouts), int(n3.n_windows), n3.bout_lengths_windows) == (3, 3, "1,1,1")
    assert int(summary.loc[summary.stage_code == 4, "n_windows"].iloc[0]) == 0


def test_raw_alignment_requires_exact_stage_onset_and_duration():
    epoch = _epochs().iloc[:2].copy()
    raw = pd.DataFrame({"onset": [0., 30.], "duration": [30., 30.], "begsample": [1, 7681], "endsample": [7680, 15360], "offset": [0, 0], "stage_hum": [1, 1], "stage_ai": [1, 1]})
    out = raw_alignment(epoch, raw, 256.0)
    assert out.stage_hum_match.all() and out.onset_matches_window_start.all() and out.duration_matches_bounds.all()
    raw.loc[1, "stage_hum"] = 3
    assert not raw_alignment(epoch, raw, 256.0).stage_hum_match.all()


def test_stage_ai_is_optional_but_sample_clock_and_integer_stage_are_strict():
    epoch = _epochs().iloc[:2].copy()
    raw = pd.DataFrame({"onset": [0., 30.], "duration": [30., 30.], "begsample": [1., 7681.], "endsample": [7680., 15360.], "offset": [0., 0.], "stage_hum": [1., 1.]})
    assert raw_alignment(epoch, raw, 256.0).sample_clock_ok.all()
    raw.loc[1, "stage_hum"] = 1.5
    import pytest
    with pytest.raises(ValueError, match="nonfinite or noninteger"):
        raw_alignment(epoch, raw, 256.0)
