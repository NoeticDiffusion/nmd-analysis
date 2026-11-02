"""Smoke the 3.0.1 I-CARE dump. Skips when the bundle is not present."""
from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import pytest

from nmd_analysis.dynamical_families.adapters import collectors
from nmd_analysis.dynamical_families.readers import read_family, read_identity
from nmd_analysis.local_dynamics.adapters import collectors as local_collectors
from nmd_analysis.local_dynamics.adapters import jacobian_metrics_recording_rows

SMOKE_H5 = Path(
    r"J:/repos/nmd-analysis/data/raw/"
    "neuralmanifolddynamics_physionet_icare_2_1_20260917_194039/"
    "sub-1015_post_cardiac_arrest_coma_continuous_eeg_run-012_acq-013/"
    "sub-1015_post_cardiac_arrest_coma_continuous_eeg_run-012_acq-013.h5"
)

pytestmark = pytest.mark.skipif(not SMOKE_H5.exists(), reason="3.0.1 I-CARE smoke H5 is not present")


def test_smoke_icare_301_identities(tmp_path):
    with h5py.File(SMOKE_H5, "r") as handle:
        assert handle.attrs.get("mndm_version") == "3.0.1"
        assert handle.attrs.get("schema_version") == "mnps_tensor_spec_v2_4"

    diffusion = read_family(SMOKE_H5, "diffusion")
    assert diffusion["computation_status"] == "computed"
    assert diffusion["qualification_status"] == "ito_not_qualified"
    assert "increment_covariance_level0" not in diffusion
    source_idx = np.asarray(diffusion["series"]["source_idx"])
    a_hat = np.asarray(diffusion["series"]["a_hat"])
    assert source_idx.shape[0] != a_hat.shape[0]

    windows = collectors()["diffusion_geometry_window"](SMOKE_H5)
    assert len(windows) == a_hat.shape[0]
    assert "source_idx" not in windows[0]
    abd = np.asarray([row["A_bD"] for row in windows], dtype=float)
    assert not np.any(np.isfinite(abd))

    recording = collectors()["diffusion_geometry_recording"](SMOKE_H5)[0]
    assert recording["source_idx_n"] == int(source_idx.size)
    pd.DataFrame([recording]).to_parquet(tmp_path / "diffusion_recording.parquet")
    pd.DataFrame(windows[:5]).to_parquet(tmp_path / "diffusion_windows.parquet")

    chart = read_family(SMOKE_H5, "chart_drift")
    assert chart["computation_status"] == "computed"
    pooled = read_identity(SMOKE_H5, "chart_drift", "conditional_mean_rate_level1/pooled")
    assert pooled["qualification_status"] == "ito_not_qualified"

    jac = jacobian_metrics_recording_rows(SMOKE_H5, dimension=3)[0]
    assert jac["computation_status"] == "insufficient_support"
    assert jac["failure_reason"] == "local_linear_fit_not_better_than_baseline"
    assert jac["rel_mse_baseline_oos_median"] != "not_recorded"

    one_step = {row["identity_path"]: row for row in collectors()["one_step_recording"](SMOKE_H5)}
    lag1 = one_step["affine_one_step_map_level2"]
    assert lag1["computation_status"] == "computed"
    assert lag1["qualification_status"] == "one_step_identified"
    assert lag1["table_grain"] == "recording"
    assert one_step["spectral_abscissa_level3"]["qualification_status"] == (
        "generator_proxy_from_qualified_one_step_not_ito"
    )
    lag2 = one_step["declared_lag_2/affine_one_step_map_level2"]
    assert lag2["computation_status"] == "insufficient_support"
    assert lag2["failure_reason"] == "one_step_fit_not_better_than_baseline"
    lag2_l3 = one_step["declared_lag_2/spectral_abscissa_level3"]
    assert lag2_l3["computation_status"] == "not_testable"
    assert lag2_l3["failure_reason"] == "upstream_one_step_not_identified"
    assert one_step["iterated_one_step_horizon_map_level4"]["computation_status"] == "insufficient_support"

    amp = collectors()["amplification_window"](SMOKE_H5)
    assert amp and amp[0]["qualification_status"] == "same_pair_observed_gain_not_operator_max_gain"
    hist = collectors()["history_predictive_gain_recording"](SMOKE_H5)[0]
    assert hist["qualification_status"] == "history_error_reduction_not_markov_restoration"
    turn = collectors()["turning_window"](SMOKE_H5)
    assert turn and turn[0]["qualification_status"] == "realized_turning_not_operator_rotation"

    dest = collectors()["destination_recording"](SMOKE_H5)[0]
    assert dest["computation_status"] == "not_testable"
    res = collectors()["resilience_recording"](SMOKE_H5)[0]
    assert res["computation_status"] == "not_testable"

    reach = local_collectors()["stochastic_reachability_3d_recording"](SMOKE_H5)[0]
    assert reach["computation_status"] == "unavailable"
    assert reach["failure_reason"] == "upstream_jacobian_local_fit_not_identified"
