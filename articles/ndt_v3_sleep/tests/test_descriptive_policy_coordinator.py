"""Coordinator acceptance checks against the written policy, not pilot outcomes."""
import numpy as np
import pandas as pd
import pytest

import descriptive_epoch_analysis as analysis


def seven_windows():
    frame = pd.DataFrame({
        "window_id": range(7), "epoch_id": range(7),
        "timestamp": np.arange(7) * 30.0 + 15,
        "window_start": np.arange(7) * 30.0,
        "window_end": np.arange(7) * 30.0 + 30,
        "stage_code": 0, "stage_label": "Wake", "stage_label_status": "recorded",
        "time_gap_before": False, "window_overlap_before": False,
    })
    for column in analysis.MASKS.values():
        frame[column] = 1
    for columns in analysis.COORDS.values():
        for offset, column in enumerate(columns):
            frame[column] = np.arange(7, dtype=float) + offset
    return frame


@pytest.mark.parametrize("change,expected_n", [
    ("none", 5), ("unknown", 2), ("gap", 3), ("overlap", 3), ("id_jump", 3),
])
def test_written_outputs_obey_two_sided_boundary_and_keep_empty_stages(tmp_path, monkeypatch, change, expected_n):
    frame = seven_windows()
    if change == "unknown":
        frame.loc[3, ["stage_code", "stage_label", "stage_label_status"]] = [8, None, "missing_or_unknown"]
    elif change in {"gap", "overlap"}:
        frame.loc[3:, ["timestamp", "window_start", "window_end"]] += 15 if change == "gap" else -15
        frame.loc[3, "time_gap_before" if change == "gap" else "window_overlap_before"] = True
    elif change == "id_jump":
        frame.loc[3:, "window_id"] += 1
    source = tmp_path / "source.parquet"
    frame.to_parquet(source, index=False)
    monkeypatch.setattr(analysis, "_figures", lambda *args: None)
    analysis.run(source, tmp_path / "result")
    for rep, width in (("3d", 3), ("9d", 9)):
        primary = pd.read_csv(tmp_path / "result" / f"coordinate_summary_{rep}.csv")
        boundary = pd.read_csv(tmp_path / "result" / f"coordinate_summary_boundary_{rep}.csv")
        for summary in (primary, boundary):
            assert len(summary) == 5 * width
            assert set(summary.stage_code) == {0, 1, 2, 3, 4}
            absent = summary.loc[summary.stage_code != 0]
            assert (absent.n == 0).all()
            assert absent[["median", "q1", "q3", "iqr"]].isna().all().all()
        assert set(boundary.loc[boundary.stage_code == 0, "n"]) == {expected_n}
        assert set(primary.loc[primary.stage_code == 0, "n"]) == {6 if change == "unknown" else 7}
    if change == "none":
        row = pd.read_csv(tmp_path / "result" / "coordinate_summary_boundary_3d.csv")
        row = row.loc[(row.stage_code == 0) & (row.coordinate == "mnps_3d_m")].iloc[0]
        assert [row["median"], row.q1, row.q3, row.iqr] == [3, 2, 4, 2]


def test_time_plot_keeps_each_eligible_point_once_and_never_bridges(tmp_path, monkeypatch):
    import matplotlib.figure
    frame = seven_windows()
    frame.loc[3:, ["timestamp", "window_start", "window_end"]] += 15
    # Deliberately leave cached gap flags false: geometry must use actual bounds.
    frame.loc[5, "producer_mask_coverage_ok"] = np.nan
    figures = []
    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", lambda fig, *args, **kwargs: figures.append(fig))
    eligible = {rep: analysis.eligibility(frame, rep)[0] for rep in analysis.COORDS}
    analysis._figures(frame, tmp_path, eligible)
    assert len(figures) == 2
    for ax in figures[0].axes[:3]:
        seen = []
        for line in ax.lines:
            xs = np.asarray(line.get_xdata(), dtype=float)
            ys = np.asarray(line.get_ydata(), dtype=float)
            finite = np.isfinite(xs) & np.isfinite(ys)
            seen.extend(xs[finite].tolist())
            for j in range(1, len(xs)):
                if finite[j - 1] and finite[j]:
                    assert xs[j] - xs[j - 1] == 30
        expected = frame.loc[eligible["3d"], "timestamp"].tolist()
        assert sorted(seen) == sorted(expected)
    stage_seen = []
    for line in figures[0].axes[3].lines:
        xs = np.asarray(line.get_xdata(), dtype=float)
        assert (np.diff(xs) == 30).all()
        stage_seen.extend(xs.tolist())
    assert sorted(stage_seen) == sorted(frame.timestamp.tolist())


def test_production_cli_requires_pinned_config():
    with pytest.raises(SystemExit) as exc:
        analysis.main(["--table", "unread.parquet", "--output", "unwritten"])
    assert exc.value.code == 2
