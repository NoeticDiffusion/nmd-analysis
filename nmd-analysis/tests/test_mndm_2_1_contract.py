from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from nmd_analysis.analysis_pipeline import run_cleaned_analysis_pipeline
from nmd_analysis.adapters import build_adapters
from nmd_analysis.config import load_dataset_config


class Mndm21ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_dataset_config(self, *, coordinate_contract: str | None = None) -> Path:
        config_path = self.root / "dataset.yaml"
        contract_line = (
            f"coordinate_contract: {coordinate_contract}\n"
            if coordinate_contract is not None
            else ""
        )
        config_path.write_text(
            (
                "dataset: demo\n"
                "input:\n"
                "  h5_root: null\n"
                f"{contract_line}"
                "output:\n"
                "  directory: data/cleaned\n"
                "runtime:\n"
                "  fail_on_missing_input: true\n"
                "  skip_disabled_analyses: true\n"
                "  continue_on_analysis_error: false\n"
                "flags:\n"
                "  sleep_data_contrast: false\n"
                "modality_rules: {}\n"
                "analyses:\n"
                "  global_mnps_3d: true\n"
                "  global_mnps_jacobian_3d: true\n"
                "  reachability_cones: true\n"
            ),
            encoding="utf-8",
        )
        return config_path

    def _write_analysis_config(self, cleaned_root: Path, *, coordinate_contract: str | None = None) -> Path:
        config_path = self.root / "analysis.yaml"
        contract_line = (
            f"coordinate_contract: {coordinate_contract}\n"
            if coordinate_contract is not None
            else ""
        )
        config_path.write_text(
            (
                "dataset: demo\n"
                "input:\n"
                f"  cleaned_root: {cleaned_root.as_posix()}\n"
                f"{contract_line}"
                "output:\n"
                f"  directory: {(self.root / 'analysis_out').as_posix()}\n"
                "runtime:\n"
                "  fail_on_missing_input: true\n"
                "  continue_on_error: false\n"
                "qc:\n"
                "  require_finite_ok: true\n"
                "  exclude_not_testable: true\n"
                "  exclude_validity_limited: false\n"
                "design:\n"
                "  pairing_keys: [subject_id, session, run]\n"
                "  condition_column: condition\n"
                "  group_column: group\n"
                "statistics:\n"
                "  permutation_n: 100\n"
                "  bootstrap_n: 100\n"
                "  random_seed: 13\n"
                "  min_group_n: 2\n"
                "  min_pairs: 2\n"
                "blocks:\n"
                "  trajectory_dynamics:\n"
                "    enabled: true\n"
                "contrasts: []\n"
                "negative_controls: []\n"
            ),
            encoding="utf-8",
        )
        return config_path

    def _write_cleaned_catalog_stub(self, cleaned_root: Path, h5_path: Path, *, source_h5_path: str | None = None) -> Path:
        cleaned_root.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame(
            [
                {
                    "subject_id": "sub-01",
                    "source_h5_path": source_h5_path if source_h5_path is not None else str(h5_path),
                    "source_dataset_path": "/stub",
                    "finite_ok": True,
                    "not_testable": False,
                    "m_mean": 0.0,
                }
            ]
        )
        parquet_path = cleaned_root / "demo_global_mnps_3d_20260520_120000.parquet"
        frame.to_parquet(parquet_path, index=False)
        return parquet_path

    def _write_legacy_h5(self, path: Path) -> Path:
        with h5py.File(path, "w") as h5:
            h5.attrs["dataset_id"] = "demo_ds"
            h5.attrs["subject_id"] = "sub-01"
            h5.attrs["session"] = "ses-01"
            h5.attrs["run"] = "run-01"
            h5.attrs["modality"] = "eeg"
            h5.create_dataset("mnps_3d", data=np.tile(np.array([[1.0, 2.0, 3.0]]), (32, 1)))
            coords_9d = h5.create_group("coords_9d")
            coords_9d.create_dataset("values", data=np.tile(np.arange(9, dtype=float), (32, 1)))
            coords_9d.create_dataset("names", data=np.array([f"f{i}".encode("utf-8") for i in range(9)]))
            jacobian = h5.create_group("jacobian")
            jacobian.create_dataset("J_hat", data=np.repeat(np.eye(3)[None, :, :], 8, axis=0))
            jacobian.create_dataset("centers", data=np.arange(8, dtype=int))
            h5.create_dataset("time", data=np.arange(32, dtype=float))
        return path

    def _write_subject_only_h5(self, path: Path) -> Path:
        with h5py.File(path, "w") as h5:
            h5.attrs["dataset_id"] = "demo_ds"
            h5.attrs["subject_id"] = "sub-01"
            h5.attrs["session"] = "ses-01"
            h5.attrs["run"] = "run-01"
            h5.attrs["modality"] = "eeg"
            h5.attrs["schema_version"] = "mnps_tensor_spec_v2_1"
            h5.attrs["mndm_version"] = "2.1"
            h5.attrs["primary_coordinate_layer"] = "coords_3d_subject_anchored"
            h5.attrs["primary_coordinate_contract"] = "subject_anchored"
            group3 = h5.create_group("coords_3d_subject_anchored")
            group3.create_dataset("values", data=np.tile(np.array([[10.0, 20.0, 30.0]]), (32, 1)))
            group3.create_dataset("names", data=np.array([b"m", b"d", b"e"]))
            group9 = h5.create_group("coords_9d_subject_anchored")
            group9.create_dataset("values", data=np.tile(np.arange(100.0, 109.0), (32, 1)))
            group9.create_dataset("names", data=np.array([f"s{i}".encode("utf-8") for i in range(9)]))
            participant = h5.create_group("participant")
            participant.create_dataset(
                "row_json",
                data=np.bytes_(b'{"participant_id":"sub-01","type":"FEP","CPZ_at_scan":0}'),
            )
            participant.create_dataset(
                "mapped_json",
                data=np.bytes_(b'{"group":"FEP","condition":"rest","task":"rest"}'),
            )
            jacobian = h5.create_group("jacobian")
            jacobian.create_dataset("J_hat", data=np.repeat((2.0 * np.eye(3))[None, :, :], 8, axis=0))
            jacobian.create_dataset("centers", data=np.arange(8, dtype=int))
            h5.create_dataset("time", data=np.arange(32, dtype=float))
        return path

    def _attach_geometry_contract(
        self,
        path: Path,
        *,
        degenerate_axes: list[str],
        jacobian_9d_windows_retained: int,
        jacobian_9d_invalid_windows: int,
    ) -> None:
        with h5py.File(path, "a") as h5:
            h5.attrs["geometry_contract_status"] = "adjusted"
            h5.attrs["geometry_invalidity_policy"] = "standard_invalidity_v1"
            h5.attrs["geometry_jacobian_9d_invalid_windows"] = int(jacobian_9d_invalid_windows)
            prov = h5.require_group("provenance")
            contract_grp = prov.require_group("contract")
            geometry_grp = prov.require_group("geometry_contract")
            coords_9d_grp = geometry_grp.require_group("coords_9d")
            jacobian_9d_grp = geometry_grp.require_group("jacobian_9d")

            for key in ("geometry_contract_status", "geometry_invalidity_policy"):
                if key in contract_grp:
                    del contract_grp[key]
            contract_grp.create_dataset("geometry_contract_status", data=np.bytes_("adjusted"))
            contract_grp.create_dataset("geometry_invalidity_policy", data=np.bytes_("standard_invalidity_v1"))

            if "status" in geometry_grp:
                del geometry_grp["status"]
            geometry_grp.create_dataset("status", data=np.bytes_("adjusted"))

            if "degenerate_axes" in coords_9d_grp:
                del coords_9d_grp["degenerate_axes"]
            if degenerate_axes:
                dtype = h5py.string_dtype(encoding="utf-8")
                coords_9d_grp.create_dataset("degenerate_axes", data=np.asarray(degenerate_axes, dtype=dtype), dtype=dtype)
            else:
                coords_9d_grp.create_dataset("degenerate_axes", data=np.asarray([], dtype=h5py.string_dtype(encoding="utf-8")))

            for key in ("windows_retained", "invalid_windows", "status"):
                if key in jacobian_9d_grp:
                    del jacobian_9d_grp[key]
            jacobian_9d_grp.create_dataset("windows_retained", data=np.int64(jacobian_9d_windows_retained))
            jacobian_9d_grp.create_dataset("invalid_windows", data=np.int64(jacobian_9d_invalid_windows))
            jacobian_9d_grp.create_dataset("status", data=np.bytes_("adjusted"))

    def _write_cohort_h5(self, path: Path) -> Path:
        with h5py.File(path, "w") as h5:
            h5.attrs["dataset_id"] = "demo_ds"
            h5.attrs["subject_id"] = "sub-01"
            h5.attrs["session"] = "ses-01"
            h5.attrs["run"] = "run-01"
            h5.attrs["modality"] = "eeg"
            h5.attrs["schema_version"] = "mnps_tensor_spec_v2_1"
            h5.attrs["mndm_version"] = "2.1"
            h5.attrs["primary_coordinate_layer"] = "coords_3d_cohort_anchored"
            h5.attrs["primary_coordinate_contract"] = "cohort_anchored"
            h5.attrs["anchor_id"] = "anchor-demo"
            h5.attrs["anchor_hash"] = "hash-demo"
            line_coords = np.column_stack(
                [
                    np.arange(32, dtype=float),
                    2.0 * np.arange(32, dtype=float),
                    3.0 * np.arange(32, dtype=float),
                ]
            )
            subject3 = h5.create_group("coords_3d_subject_anchored")
            subject3.create_dataset("values", data=10.0 + line_coords)
            subject3.create_dataset("names", data=np.array([b"m", b"d", b"e"]))
            cohort3 = h5.create_group("coords_3d_cohort_anchored")
            cohort3.create_dataset("values", data=1.0 + line_coords)
            cohort3.create_dataset("names", data=np.array([b"m", b"d", b"e"]))
            subject9 = h5.create_group("coords_9d_subject_anchored")
            subject9.create_dataset("values", data=np.tile(np.arange(100.0, 109.0), (32, 1)))
            subject9.create_dataset("names", data=np.array([f"s{i}".encode("utf-8") for i in range(9)]))
            cohort9 = h5.create_group("coords_9d_cohort_anchored")
            cohort9.create_dataset("values", data=np.tile(np.arange(1.0, 10.0), (32, 1)))
            cohort9.create_dataset("names", data=np.array([f"c{i}".encode("utf-8") for i in range(9)]))
            participant = h5.create_group("participant")
            participant.create_dataset(
                "row_json",
                data=np.bytes_(b'{"participant_id":"sub-01","type":"FEP","CPZ_at_scan":125.0}'),
            )
            participant.create_dataset(
                "mapped_json",
                data=np.bytes_(b'{"group":"FEP","condition":"rest","task":"rest"}'),
            )
            jacobian = h5.create_group("jacobian")
            jacobian.create_dataset("J_hat", data=np.repeat((3.0 * np.eye(3))[None, :, :], 8, axis=0))
            jacobian.create_dataset("centers", data=np.arange(8, dtype=int))
            h5.create_dataset("time", data=np.arange(32, dtype=float))
        return path

    def test_dataset_config_defaults_to_cohort_anchored(self) -> None:
        cfg = load_dataset_config(self._write_dataset_config())
        self.assertEqual(cfg.coordinate_contract, "cohort_anchored")

    def test_global_mnps_3d_default_prefers_cohort_anchored_layer(self) -> None:
        h5_path = self._write_cohort_h5(self.root / "cohort.h5")
        adapter = build_adapters(self._write_dataset_config())["global_mnps_3d"]
        rows = adapter.collect_rows(h5_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_dataset_path"], "/coords_3d_cohort_anchored/values")
        self.assertEqual(rows[0]["requested_coordinate_contract"], "cohort_anchored")
        self.assertEqual(rows[0]["resolved_coordinate_contract"], "cohort_anchored")
        self.assertEqual(rows[0]["anchor_id"], "anchor-demo")
        self.assertEqual(rows[0]["medication_group"], "FEP medicated")
        self.assertAlmostEqual(rows[0]["cpz_at_scan"], 125.0)

    def test_global_mnps_3d_subject_request_uses_subject_layer(self) -> None:
        h5_path = self._write_subject_only_h5(self.root / "subject_only.h5")
        adapter = build_adapters(self._write_dataset_config(coordinate_contract="subject-anchor"))["global_mnps_3d"]
        rows = adapter.collect_rows(h5_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_dataset_path"], "/coords_3d_subject_anchored/values")
        self.assertEqual(rows[0]["requested_coordinate_contract"], "subject_anchored")
        self.assertEqual(rows[0]["resolved_coordinate_contract"], "subject_anchored")

    def test_legacy_h5_falls_back_and_marks_legacy(self) -> None:
        h5_path = self._write_legacy_h5(self.root / "legacy.h5")
        adapter = build_adapters(self._write_dataset_config())["global_mnps_3d"]
        rows = adapter.collect_rows(h5_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_dataset_path"], "/mnps_3d")
        self.assertEqual(rows[0]["requested_coordinate_contract"], "cohort_anchored")
        self.assertEqual(rows[0]["resolved_coordinate_contract"], "legacy")
        self.assertIsNone(rows[0]["primary_coordinate_contract"])

    def test_subject_requested_jacobian_skips_on_cohort_primary_run(self) -> None:
        h5_path = self._write_cohort_h5(self.root / "cohort_jacobian.h5")
        adapter = build_adapters(self._write_dataset_config(coordinate_contract="subject_anchored"))[
            "global_mnps_jacobian_3d"
        ]
        rows = adapter.collect_rows(h5_path)
        self.assertEqual(rows, [])

    def test_trajectory_dynamics_custom_block_carries_contract_provenance(self) -> None:
        h5_path = self._write_cohort_h5(self.root / "cohort_for_pipeline.h5")
        cleaned_root = self.root / "cleaned"
        self._write_cleaned_catalog_stub(cleaned_root, h5_path)
        analysis_config = self._write_analysis_config(cleaned_root)
        result = run_cleaned_analysis_pipeline(
            analysis_config,
            blocks_filter=["trajectory_dynamics"],
        )
        subject_metrics = pd.read_parquet(result["written_files"]["subject_metrics"])
        traj_rows = subject_metrics[subject_metrics["analysis_type"] == "trajectory_dynamics"].copy()
        self.assertFalse(traj_rows.empty)
        self.assertTrue((traj_rows["requested_coordinate_contract"] == "cohort_anchored").all())
        self.assertTrue((traj_rows["resolved_coordinate_contract"] == "cohort_anchored").all())
        self.assertTrue((traj_rows["trajectory_source_dataset_path"] == "/coords_3d_cohort_anchored/values").all())
        self.assertTrue((traj_rows["anchor_id"] == "anchor-demo").all())
        values = traj_rows.set_index("metric")["value"]
        self.assertIn("path_length", values.index)
        self.assertIn("endpoint_dist", values.index)
        self.assertIn("traj_efficiency", values.index)
        self.assertAlmostEqual(float(values["path_length"]), float(values["endpoint_dist"]), places=6)
        self.assertAlmostEqual(float(values["traj_efficiency"]), 1.0, places=6)

    def test_trajectory_dynamics_resolves_stale_absolute_source_h5_paths(self) -> None:
        actual_h5 = (
            self.root
            / "data"
            / "raw"
            / "neuralmanifolddynamics_demo_20260612"
            / "sub-01_rest_Rest"
            / "sub-01_rest_Rest.h5"
        )
        actual_h5.parent.mkdir(parents=True, exist_ok=True)
        self._write_cohort_h5(actual_h5)
        stale_h5 = (
            r"h:\SourceRepo2\NoeticDiffusion\data\raw\neuralmanifolddynamics_demo_20260612"
            r"\sub-01_rest_Rest\sub-01_rest_Rest.h5"
        )
        cleaned_root = self.root / "cleaned"
        self._write_cleaned_catalog_stub(cleaned_root, actual_h5, source_h5_path=stale_h5)
        analysis_config = self._write_analysis_config(cleaned_root)

        old_cwd = Path.cwd()
        os.chdir(self.root)
        try:
            result = run_cleaned_analysis_pipeline(
                analysis_config,
                blocks_filter=["trajectory_dynamics"],
            )
        finally:
            os.chdir(old_cwd)

        self.assertEqual(int(result["n_source_h5_files"]), 1)
        self.assertNotIn("trajectory_dynamics:no_rows", result["skipped"])
        subject_metrics = pd.read_parquet(result["written_files"]["subject_metrics"])
        traj_rows = subject_metrics[subject_metrics["analysis_type"] == "trajectory_dynamics"].copy()
        self.assertFalse(traj_rows.empty)
        self.assertIn("traj_efficiency", set(traj_rows["metric"].tolist()))

    def test_reachability_cones_9d_gate_triggers_on_degenerate_axes(self) -> None:
        h5_path = self._write_subject_only_h5(self.root / "subject_degenerate_axes.h5")
        self._attach_geometry_contract(
            h5_path,
            degenerate_axes=["d_n", "m_a", "m_e"],
            jacobian_9d_windows_retained=21,
            jacobian_9d_invalid_windows=0,
        )
        adapter = build_adapters(self._write_dataset_config(coordinate_contract="subject_anchor"))["reachability_cones"]
        rows = adapter.collect_rows(h5_path)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertTrue(bool(row["not_testable"]))
        self.assertFalse(bool(row["finite_ok"]))
        self.assertTrue(bool(row["geometry_gate_9d_triggered"]))
        self.assertIn("coords_9d_degenerate_axes", str(row.get("geometry_gate_9d_reason")))
        self.assertTrue(np.isnan(float(row["persistence_log_det_median"])))

    def test_reachability_cones_9d_gate_triggers_on_zero_retained_jacobian(self) -> None:
        h5_path = self._write_subject_only_h5(self.root / "subject_zero_retained.h5")
        self._attach_geometry_contract(
            h5_path,
            degenerate_axes=[],
            jacobian_9d_windows_retained=0,
            jacobian_9d_invalid_windows=21,
        )
        adapter = build_adapters(self._write_dataset_config(coordinate_contract="subject_anchor"))["reachability_cones"]
        rows = adapter.collect_rows(h5_path)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertTrue(bool(row["not_testable"]))
        self.assertTrue(bool(row["geometry_gate_9d_triggered"]))
        self.assertIn("jacobian_9d_windows_retained", str(row.get("geometry_gate_9d_reason")))
        self.assertEqual(int(row.get("geometry_jacobian_9d_windows_retained")), 0)

    def test_reachability_cones_9d_gate_does_not_trigger_for_clean_contract(self) -> None:
        h5_path = self._write_subject_only_h5(self.root / "subject_clean_contract.h5")
        self._attach_geometry_contract(
            h5_path,
            degenerate_axes=[],
            jacobian_9d_windows_retained=21,
            jacobian_9d_invalid_windows=0,
        )
        adapter = build_adapters(self._write_dataset_config(coordinate_contract="subject_anchor"))["reachability_cones"]
        rows = adapter.collect_rows(h5_path)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertFalse(bool(row["not_testable"]))
        self.assertFalse(bool(row["geometry_gate_9d_triggered"]))
        self.assertTrue(np.isfinite(float(row["persistence_log_det_median"])))


if __name__ == "__main__":
    unittest.main()
