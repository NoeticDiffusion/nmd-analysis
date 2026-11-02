from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "src" / "plot_new_family_sleep.py"
SPEC = importlib.util.spec_from_file_location("plot_new_family_sleep", SOURCE)
assert SPEC and SPEC.loader
plot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plot)


def _row(*, family: str, metric: str, dimension: int = 3, stage_key: str = "Wake", center: int = 0, value: float = 1.0) -> dict:
    return {
        "recording": "sub-1_Sleep",
        "family": family,
        "dimension": dimension,
        "metric": metric,
        "value": value,
        "stage_key": stage_key,
        "stage_code": {"Wake": 0, "N2": 2, "Code8": 8, "Unknown": None}[stage_key],
        "stage_label": stage_key,
        "mapped_epoch_position": center,
        "epoch_id": center,
        "time": float(center * 30),
        "center": center,
        "center_gap_before": None if center == 0 else 2,
        "center_gap_before_is_nonconsecutive": None if center == 0 else True,
        "finite": True,
        "producer_finite_ok": True,
        "used": True,
        "support_count": 20 if family == "diffusion_geometry" else None,
        "support_n": 20 if family == "diffusion_geometry" else None,
        "producer_valid_flag": True if family == "diffusion_geometry" else None,
        "psd_floor_applied": False if family == "diffusion_geometry" else None,
        "raw_min_eigenvalue": 0.1 if family == "diffusion_geometry" else None,
        "measurement_validity": "not_assessed",
        "qualification_valid": None,
    }


def test_validate_rows_preserves_code8_and_unknown_as_visible_categories():
    rows = [
        _row(family="local_jacobian", metric="spectral_abscissa", stage_key="Code8"),
        _row(family="local_jacobian", metric="spectral_abscissa", stage_key="Unknown", center=2),
    ]
    validated = plot._validate_rows(rows)
    assert [row["stage_category"] for row in validated] == ["Code8 (unknown source)", "Unknown/other"]
    assert validated[0]["stage_code"] == 8
    assert validated[1]["stage_code"] is None


def test_validate_rows_rejects_missing_runner_contract_column():
    row = _row(family="diffusion_geometry", metric="D_total")
    row.pop("psd_floor_applied")
    with pytest.raises(ValueError, match="psd_floor_applied"):
        plot._validate_rows([row])


def test_validate_rows_rejects_combined_json_and_csv_duplicates():
    row = _row(family="diffusion_geometry", metric="D_total")
    with pytest.raises(ValueError, match="duplicate natural row identity"):
        plot._validate_rows([row, dict(row)])


def test_input_root_prefers_authoritative_json_over_csv(tmp_path):
    (tmp_path / "endpoint_rows.json").write_text("[]", encoding="utf-8")
    (tmp_path / "endpoint_rows.csv").write_text("recording\n", encoding="utf-8")
    args = argparse.Namespace(endpoint_rows=None, input_manifest=None, input_root=tmp_path)
    assert plot._resolve_inputs(args) == [(tmp_path / "endpoint_rows.json").resolve()]


def test_diffusion_diagnostics_are_one_row_per_query_not_three_metrics():
    rows = []
    for metric in plot.DIFFUSION_METRICS:
        rows.extend([
            _row(family="diffusion_geometry", metric=metric, stage_key="Wake", center=0, value=1.0),
            _row(family="diffusion_geometry", metric=metric, stage_key="Code8", center=2, value=2.0),
        ])
    validated = plot._validate_rows(rows)
    unique = plot._unique_diffusion_queries(validated)
    assert len(validated) == 6
    assert len(unique) == 2
    support = {label: sum(row["stage_category"] == label for row in unique) for _, label in plot.STAGES}
    assert support["Wake"] == 1
    assert support["Code8 (unknown source)"] == 1
    assert support["Unknown/other"] == 0


def test_diffusion_diagnostics_must_agree_across_metric_rows():
    rows = [_row(family="diffusion_geometry", metric=metric, stage_key="Wake", center=0, value=1.0) for metric in plot.DIFFUSION_METRICS]
    rows[1]["support_count"] = 19
    with pytest.raises(ValueError, match="producer diagnostics disagree"):
        plot._validate_rows(rows)


BOUNDED_ROWS = Path(__file__).resolve().parents[1] / "results/new_family_sleep_20260910/endpoint_rows.json"


@pytest.mark.skipif(not BOUNDED_ROWS.is_file(), reason="bounded runner output is unavailable")
def test_bounded_runner_support_counts_are_unique_queries():
    rows = plot._validate_rows(plot.read_rows(BOUNDED_ROWS))
    expected = {
        "sub-1_Sleep_acq-psg": {"Wake": 200, "N1": 57, "N2": 398, "N3": 172, "REM": 87, "Code8 (unknown source)": 1, "Unknown/other": 0},
        "sub-99_Sleep_acq-psg": {"Wake": 275, "N1": 20, "N2": 642, "N3": 15, "REM": 107, "Code8 (unknown source)": 9, "Unknown/other": 0},
    }
    for recording, expected_counts in expected.items():
        unique = plot._unique_diffusion_queries([row for row in rows if row["recording"] == recording])
        counts = {label: sum(row["stage_category"] == label for row in unique) for _, label in plot.STAGES}
        assert counts == expected_counts


def test_static_figures_keep_nonconsecutive_center_points_unconnected(tmp_path):
    rows = []
    for dimension in (3, 9):
        for metric in plot.JACOBIAN_METRICS:
            rows.extend([
                _row(family="local_jacobian", metric=metric, dimension=dimension, center=0, value=1.0),
                _row(family="local_jacobian", metric=metric, dimension=dimension, stage_key="N2", center=2, value=2.0),
            ])
    for metric in plot.DIFFUSION_METRICS:
        rows.extend([
            _row(family="diffusion_geometry", metric=metric, stage_key="Wake", center=0, value=1.0),
            _row(family="diffusion_geometry", metric=metric, stage_key="Code8", center=2, value=2.0),
        ])
    rows = plot._validate_rows(rows)
    artifacts = plot.plot_abscissa_timeline(rows, tmp_path, "sub-1_Sleep", 9)
    artifacts.extend(plot.plot_abscissa_distributions(rows, tmp_path, "sub-1_Sleep", 9))
    artifacts.extend(plot.plot_diffusion(rows, tmp_path, "sub-1_Sleep"))
    assert len(artifacts) == 9
    assert all(Path(path).is_file() for path in artifacts)
