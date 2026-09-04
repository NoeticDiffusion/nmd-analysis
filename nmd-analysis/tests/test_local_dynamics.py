from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import h5py
import numpy as np

from nmd_analysis.local_dynamics.adapters import collectors


class LocalDynamicsAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "demo.h5"
        with h5py.File(self.path, "w") as h5:
            h5.attrs.update(
                dataset_id="demo",
                subject_id="sub-01",
                session="ses-01",
                run="run-01",
                primary_coordinate_contract="cohort_anchored",
                primary_coordinate_layer="/coords_3d_cohort_anchored",
                anchor_hash="anchor",
            )
            h5.create_dataset("/jacobian/centers", data=np.array([10, 20], dtype=np.int32))
            metrics = h5.create_group("/jacobian/derived_metrics/v1")
            metrics.create_dataset("schema_version", data=np.bytes_("mndm.jacobian_metrics.v1"))
            prov = metrics.create_group("provenance")
            prov.create_dataset("dimension", data=3)
            prov.create_dataset("primary_coordinate_contract", data=np.bytes_("cohort_anchored"))
            prov.create_dataset("primary_coordinate_layer", data=np.bytes_("/coords_3d_cohort_anchored"))
            series = metrics.create_group("series")
            series.create_dataset("spectral_abscissa", data=np.array([-1.0, -2.0]))
            series.create_dataset("numerical_abscissa", data=np.array([0.5, -0.1]))
            series.create_dataset("stable_reactive_flag", data=np.array([1, 0], dtype=np.int8))
            summary = metrics.create_group("summary")
            summary.create_dataset("mean_spectral_abscissa", data=-1.5)
            summary.create_dataset("n_windows_total", data=2)
            summary.create_dataset("n_windows_metrics_valid", data=2)
            summary.create_dataset("stable_reactive_fraction", data=0.5)

            ftr = h5.create_group("/finite_time_response/v1/primary")
            ftr.create_dataset("schema_version", data=np.bytes_("mndm.finite_time_response.v1"))
            ftr.create_dataset("computation_status", data=np.bytes_("computed"))
            ftr.create_dataset("validation_level", data=np.bytes_("model_derived"))
            ftr.create_dataset("n_windows", data=2)
            ftr.create_group("summary").create_dataset("g_peak_over_horizons", data=1.4)
            h1 = ftr.create_group("horizons/h1")
            h1.create_dataset("horizon_steps", data=1)
            h1.create_dataset("mean_g_max", data=1.2)
            h1.create_dataset("n_sequences_valid", data=1)
            h1.create_dataset("n_sequences_candidate", data=1)
            h1.create_dataset("start_windows", data=np.array([0], dtype=np.int32))
            h1.create_group("series").create_dataset("g_max", data=np.array([1.2]))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_contract_grains_and_capability_denominator(self) -> None:
        registry = collectors()
        recording = registry["jacobian_metrics_3d_recording"](self.path)
        windows = registry["jacobian_metrics_3d_window"](self.path)
        horizons = registry["finite_time_response_3d_recording_horizon"](self.path)
        sequences = registry["finite_time_response_3d_sequence"](self.path)
        missing = registry["stochastic_reachability_3d_recording"](self.path)
        availability = registry["local_dynamics_availability"](self.path)

        self.assertEqual(recording[0]["table_grain"], "recording")
        self.assertEqual(recording[0]["jacobian_metrics_valid_fraction"], 1.0)
        self.assertEqual([row["center"] for row in windows], [10, 20])
        self.assertEqual(horizons[0]["table_grain"], "recording_horizon")
        self.assertEqual(sequences[0]["start_window_id"], 0)
        self.assertEqual(missing[0]["failure_reason"], "capability_missing")
        self.assertEqual({row["coordinate_dimension"] for row in availability}, {3, 9})


if __name__ == "__main__":
    unittest.main()
