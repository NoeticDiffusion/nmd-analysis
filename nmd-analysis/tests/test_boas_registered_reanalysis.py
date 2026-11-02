from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "articles"
    / "BOAS_sleep_dataset_ndt._v.1.0"
    / "src"
    / "run_registered_reanalysis.py"
)
SPEC = importlib.util.spec_from_file_location("boas_registered_reanalysis", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
BOAS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOAS)


def _synthetic_centers() -> pd.DataFrame:
    rows = []
    stages = (0, 2, 3, 4)
    increments = {2: 2.0, 3: 4.0, 4: 3.0}
    for person in range(20):
        for recording, boundary_ok, target_scale in (
            ("interior", True, 1.0),
            ("nonboundary", False, 2.0),
        ):
            baseline = 100.0 + person
            for stage in stages:
                for center in range(5):
                    offset = 0.01 * center
                    stage_value = baseline + offset
                    if stage != 0:
                        stage_value += target_scale * increments[stage]
                    rows.append(
                        {
                            "recording_id": f"sub-{person:02d}_{recording}",
                            "pid": person,
                            "fallback_feature": "ppg_rate_bpm",
                            "dimension": 3,
                            "eligibility": True,
                            "boundary_ok": boundary_ok,
                            "stage_code": stage,
                            "spectral_abscissa": stage_value,
                            "numerical_abscissa": stage_value + 10.0,
                            "reactivity_gap": stage_value + 20.0,
                        }
                    )

    # This recording has recorded centers but insufficient Wake support. Its
    # contrasts must stay null and must not enter person/summary reductions.
    for stage in stages:
        n_centers = 4 if stage == 0 else 5
        for center in range(n_centers):
            value = 200.0 + center + (0.5 if stage else 0.0)
            rows.append(
                {
                    "recording_id": "sub-unsupported",
                    "pid": 999,
                    "fallback_feature": "ppg_rate_bpm",
                    "dimension": 3,
                    "eligibility": True,
                    "boundary_ok": True,
                    "stage_code": stage,
                    "spectral_abscissa": value,
                    "numerical_abscissa": value + 10.0,
                    "reactivity_gap": value + 20.0,
                }
            )
    return pd.DataFrame(rows)


def test_registered_contrasts_are_target_minus_wake_at_all_grains() -> None:
    centers = _synthetic_centers()
    full = BOAS._build_contrast_tables(centers)
    boundary = BOAS._build_contrast_tables(centers, boundary_only=True)

    expected = {
        "N2_minus_Wake": ("N2", 3.0, 2.0),
        "N3_minus_Wake": ("N3", 6.0, 4.0),
        "REM_minus_Wake": ("REM", 4.5, 3.0),
    }
    for contrast_id, (target, full_delta, boundary_delta) in expected.items():
        recording = full["recording"].query(
            "recording_id == 'sub-00_interior' and contrast_id == @contrast_id"
        ).iloc[0]
        assert recording["stage_a"] == "Wake"
        assert recording["stage_b"] == target
        person = full["person"].query(
            "pid == 0 and contrast_id == @contrast_id"
        ).iloc[0]
        summary = full["summary"].query("contrast_id == @contrast_id").iloc[0]
        assert summary["stage_a"] == "Wake"
        assert summary["stage_b"] == target
        boundary_recording = boundary["recording"].query(
            "recording_id == 'sub-00_interior' and contrast_id == @contrast_id"
        ).iloc[0]
        assert boundary_recording["stage_a"] == "Wake"
        assert boundary_recording["stage_b"] == target
        boundary_person = boundary["person"].query(
            "pid == 0 and contrast_id == @contrast_id"
        ).iloc[0]
        boundary_summary = boundary["summary"].query(
            "contrast_id == @contrast_id"
        ).iloc[0]
        assert boundary_summary["stage_a"] == "Wake"
        assert boundary_summary["stage_b"] == target

        for endpoint in ("spectral_abscissa", "numerical_abscissa", "reactivity_gap"):
            np.testing.assert_allclose(recording[f"{endpoint}_contrast"], boundary_delta)
            np.testing.assert_allclose(
                recording[f"{endpoint}_b_median"] - recording[f"{endpoint}_a_median"],
                boundary_delta,
            )
            np.testing.assert_allclose(person[f"{endpoint}_person_contrast"], full_delta)
            np.testing.assert_allclose(summary[f"{endpoint}_median"], full_delta)
            assert summary[f"{endpoint}_bootstrap_q025"] > 0
            assert summary[f"{endpoint}_bootstrap_q975"] > 0
            np.testing.assert_allclose(boundary_recording[f"{endpoint}_contrast"], boundary_delta)
            np.testing.assert_allclose(boundary_person[f"{endpoint}_person_contrast"], boundary_delta)
            np.testing.assert_allclose(boundary_summary[f"{endpoint}_median"], boundary_delta)
            assert boundary_summary[f"{endpoint}_bootstrap_q025"] > 0
            assert boundary_summary[f"{endpoint}_bootstrap_q975"] > 0

    unsupported = full["recording"].query(
        "recording_id == 'sub-unsupported' and contrast_id == 'N2_minus_Wake'"
    ).iloc[0]
    assert not unsupported["support_ok"]
    assert unsupported["contrast_status"] == "unavailable_minimum_stage_support"
    assert np.isnan(unsupported["spectral_abscissa_contrast"])
    unsupported_person = full["person"].query("pid == 999 and contrast_id == 'N2_minus_Wake'").iloc[0]
    assert unsupported_person["n_recordings"] == 0
    assert np.isnan(unsupported_person["spectral_abscissa_person_contrast"])
