from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import h5py
import numpy as np

from nmd_analysis.analysis_pipeline import (
    _handle_stage_code_map,
    _iter_handle_stage_indices,
    _iter_sleep_stage_indices,
    _sleep_stage_dynamics_row,
)


class StageMappingConsistencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_handle_stage_code_map_reads_h5_codebook_dataset(self) -> None:
        h5_path = self.root / "codebook.h5"
        with h5py.File(h5_path, "w") as h5:
            stage = np.concatenate(
                [
                    np.full(25, 1, dtype=int),
                    np.full(25, 2, dtype=int),
                    np.full(25, 3, dtype=int),
                ]
            )
            h5.create_dataset("/labels/stage", data=stage)
            stage_group = h5.require_group("/codebooks/stage")
            stage_group.create_dataset("codes", data=np.array([1, 2, 3], dtype=np.int32))
            stage_group.create_dataset(
                "labels",
                data=np.array([b"awake", b"unresponsive", b"recovery"]),
            )

        with h5py.File(h5_path, "r") as h5:
            mapping = _handle_stage_code_map(h5)
            self.assertEqual(mapping, {1: "awake", 2: "unresponsive", 3: "recovery"})
            slices = _iter_handle_stage_indices(h5, n_samples=75, min_points=20)
            labels = {label for _, label, _ in slices}
            self.assertEqual(labels, {"awake", "unresponsive", "recovery"})

    def test_iter_sleep_stage_indices_honors_custom_map(self) -> None:
        stage = np.concatenate(
            [
                np.full(25, 1, dtype=int),
                np.full(25, 2, dtype=int),
                np.full(25, 3, dtype=int),
            ]
        )
        slices = _iter_sleep_stage_indices(
            stage,
            n_samples=75,
            stage_code_map={1: "awake", 2: "unresponsive", 3: "recovery"},
            min_points=20,
        )
        labels = {label for _, label, _ in slices}
        self.assertEqual(labels, {"awake", "unresponsive", "recovery"})

    def test_sleep_stage_dynamics_jacobian_filter_uses_stage_code(self) -> None:
        n_samples = 40
        coords = np.column_stack(
            [
                np.linspace(0.0, 1.0, n_samples),
                np.linspace(1.0, 2.0, n_samples),
                np.linspace(2.0, 3.0, n_samples),
            ]
        )
        stage = np.array([2 if idx % 2 == 0 else 1 for idx in range(n_samples)], dtype=int)
        sample_idx = np.arange(n_samples, dtype=int)
        jacobian = np.repeat(np.eye(3)[None, :, :], n_samples, axis=0)
        for idx in range(0, n_samples, 2):
            jacobian[idx] = np.diag([10.0, 1.0, 1.0])
        centers = np.arange(n_samples, dtype=int)

        row = _sleep_stage_dynamics_row(
            label="awake",
            coords=coords,
            base_row={"dataset_id": "demo"},
            source_dataset_path="/coords_3d",
            sample_idx=sample_idx,
            thr_low=np.array([0.2, 1.2, 2.2], dtype=float),
            thr_high=np.array([0.8, 1.8, 2.8], dtype=float),
            stage_code=1,
            stage=stage,
            jacobian=jacobian,
            jacobian_centers=centers,
            dt=1.0,
        )
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["stage_code"], 1)
        self.assertAlmostEqual(float(row["tier2_jacobian_condition_number_median"]), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
