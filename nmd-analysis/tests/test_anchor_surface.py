"""
Tests for anchor_surface.py and block_native.py.

Split into two test classes:
  - AnchorSurfaceH5Tests: unit tests using synthetic H5 files
  - BlockNativeTests: unit tests using synthetic CSV files
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from nmd_analysis.anchor_surface import (
    ANCHOR_QUALITY_DEFAULT_NAMES,
    ANCHOR_STATE_DEFAULT_NAMES,
    AnchorCoupling,
    AnchorQuality,
    AnchorState,
    AnchorSurface,
    probe_anchor_capabilities_from_manifest,
    read_anchor_surface,
)
from nmd_analysis.analysis_config import (
    BlockNativeAnalysisConfig,
    BlockNativeQCConfig,
    load_analysis_config,
)
from nmd_analysis.block_native import (
    DS003838_STAGE_LABELS,
    DS006036_STAGE_LABELS,
    SLEEP_STAGE_CODE_TO_LABEL,
    KNOWN_STAGE_LABELS,
    ANCHOR_STATE_COLS,
    BlockStageSummary,
    RunInventory,
    anchor_support_mask,
    build_run_inventory,
    combined_qc_mask,
    compute_stage_summaries,
    iter_subject_dirs,
    load_block_native_table,
    load_event_locked_table,
    load_run_block_native_table,
    load_run_manifest,
    mnps_finite_mask,
    qc_mask_from_config,
    stage_labels_from_config,
    stage_labels_from_dataset_id,
    stage_labels_from_manifest,
    subject_center,
)


# ---------------------------------------------------------------------------
# Helpers for building synthetic H5 files
# ---------------------------------------------------------------------------

def _make_anchor_h5(
    path: Path,
    *,
    T: int = 50,
    A: int = 5,
    Q: int = 4,
    with_coupling: bool = True,
    W_coupling: int = 20,
) -> None:
    """Write a minimal synthetic H5 with anchor surfaces."""
    rng = np.random.default_rng(42)
    with h5py.File(path, "w") as f:
        # anchor_state
        grp = f.create_group("anchor_state")
        grp.create_dataset("values", data=rng.standard_normal((T, A)).astype(np.float32))
        names_arr = np.array(ANCHOR_STATE_DEFAULT_NAMES[:A], dtype=object)
        grp.create_dataset("names", data=names_arr)

        # anchor_state_dot
        grp_dot = f.create_group("anchor_state_dot")
        grp_dot.create_dataset("values", data=rng.standard_normal((T, A)).astype(np.float32))
        grp_dot.create_dataset("names", data=names_arr)

        # anchor_quality
        grp_q = f.create_group("anchor_quality")
        q_vals = rng.uniform(0, 1, (T, Q)).astype(np.float32)
        grp_q.create_dataset("values", data=q_vals)
        grp_q.create_dataset("names", data=np.array(ANCHOR_QUALITY_DEFAULT_NAMES[:Q], dtype=object))

        if with_coupling:
            X = 3  # MNPS dims
            Z = A + X
            grp_c = f.create_group("anchor_coupling")
            grp_c.create_dataset("J_ax", data=rng.standard_normal((W_coupling, A, X)).astype(np.float32))
            grp_c.create_dataset("J_xa", data=rng.standard_normal((W_coupling, X, A)).astype(np.float32))
            grp_c.create_dataset("J_z", data=rng.standard_normal((W_coupling, Z, Z)).astype(np.float32))
            grp_c.create_dataset("centers", data=np.arange(W_coupling, dtype=np.int32))
            grp_c.create_dataset(
                "metric_names",
                data=np.array(["forward_drive", "reverse_drive", "asymmetry", "exchange"], dtype=object),
            )
            grp_c.create_dataset("metrics", data=rng.uniform(0, 1, (W_coupling, 4)).astype(np.float32))

            diag = grp_c.create_group("diagnostics")
            policy = diag.create_group("policy")
            policy.create_dataset("windows_raw", data=np.int64(T))
            policy.create_dataset("windows_retained", data=np.int64(W_coupling))
            policy.create_dataset("invalid_windows", data=np.int64(T - W_coupling))
            policy.create_dataset("invalid_window_fraction", data=np.float64((T - W_coupling) / T))
            policy.create_dataset("status", data=np.bytes_("adjusted"))
            policy.create_dataset("condition_number_threshold", data=np.float64(1e6))
            policy.create_dataset("min_windows_required", data=np.int64(3))
            diag.create_dataset("windows_raw", data=np.float64(T))
            diag.create_dataset("forward_drive_median", data=np.float64(0.5))
            diag.create_dataset("reverse_drive_median", data=np.float64(0.3))
            diag.create_dataset("directional_asymmetry_median", data=np.float64(0.1))
            diag.create_dataset("rotational_exchange_median", data=np.float64(0.2))


def _make_block_native_csv(
    path: Path,
    *,
    subject_id: str = "sub-001",
    n_rows: int = 40,
    stage_codes: tuple = (0, 1, 5),
) -> None:
    """Write a minimal synthetic block_native_windows.csv."""
    rng = np.random.default_rng(7)
    n = n_rows
    stages = np.tile(stage_codes, n // len(stage_codes) + 1)[:n]
    df = pd.DataFrame({
        "subject_id": subject_id,
        "dataset_id": "ds003838",
        "block_id": np.repeat(np.arange(len(stage_codes)), n // len(stage_codes) + 1)[:n],
        "window_id_within_block": np.arange(n),
        "stage_code": stages,
        "block_start_sec": rng.uniform(0, 100, n),
        "window_center_sec": rng.uniform(0, 200, n),
        "relative_pos_0_1": rng.uniform(0, 1, n),
        "m": rng.standard_normal(n),
        "d": rng.standard_normal(n),
        "e": rng.standard_normal(n),
        "mnps_finite": 1,
        "m_dot": rng.standard_normal(n),
        "d_dot": rng.standard_normal(n),
        "e_dot": rng.standard_normal(n),
        "ecg_hrv_hr_mean_bpm": rng.uniform(50, 100, n),
        "ecg_hrv_rmssd_ms": rng.uniform(20, 80, n),
        "ecg_hrv_sdnn_ms": rng.uniform(30, 90, n),
        "sympathetic_index": rng.standard_normal(n),
        "vagal_index": rng.standard_normal(n),
        "vascular_index": rng.standard_normal(n),
        "pupil_arousal_index": rng.standard_normal(n),
        "anchor_index": rng.standard_normal(n),
        "ecg_quality_quality": rng.uniform(0.7, 1.0, n),
        "anchor_support_fraction_quality": rng.uniform(0.3, 1.0, n),
        "task_state_label": np.where(stages == 0, "rest", "listen"),
        "task_load_n": stages,
    })
    df.to_csv(path, index=False)


# ---------------------------------------------------------------------------
# Tests: AnchorSurface H5 reader
# ---------------------------------------------------------------------------

class AnchorSurfaceH5Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _h5_path(self, name: str = "test.h5") -> Path:
        return self.root / name

    def test_read_anchor_surface_full(self) -> None:
        h5p = self._h5_path()
        T, A, W = 50, 5, 20
        _make_anchor_h5(h5p, T=T, A=A, W_coupling=W)

        surf = read_anchor_surface(h5p, subject_id="sub-001", task="rest")

        self.assertIsInstance(surf, AnchorSurface)
        self.assertTrue(surf.has_state)
        self.assertTrue(surf.has_quality)
        self.assertTrue(surf.has_coupling)

        self.assertIsNotNone(surf.state)
        assert surf.state is not None
        self.assertEqual(surf.state.n_timepoints, T)
        self.assertEqual(len(surf.state.names), A)
        self.assertEqual(surf.state.names, ANCHOR_STATE_DEFAULT_NAMES[:A])
        self.assertEqual(surf.state.subject_id, "sub-001")
        self.assertEqual(surf.state.task, "rest")

    def test_read_anchor_surface_no_coupling(self) -> None:
        h5p = self._h5_path()
        _make_anchor_h5(h5p, with_coupling=False)

        surf = read_anchor_surface(h5p, load_coupling=False)
        self.assertFalse(surf.has_coupling)
        self.assertTrue(surf.has_state)

    def test_anchor_state_as_dict(self) -> None:
        h5p = self._h5_path()
        T = 30
        _make_anchor_h5(h5p, T=T)
        surf = read_anchor_surface(h5p)
        assert surf.state is not None
        d = surf.state.as_dict()
        self.assertEqual(set(d.keys()), set(ANCHOR_STATE_DEFAULT_NAMES))
        for arr in d.values():
            self.assertEqual(len(arr), T)

    def test_anchor_quality_ok_mask(self) -> None:
        h5p = self._h5_path()
        _make_anchor_h5(h5p, T=100, Q=4)
        surf = read_anchor_surface(h5p)
        assert surf.quality is not None
        mask = surf.quality.ok_mask(min_support=0.5)
        self.assertEqual(len(mask), 100)
        self.assertTrue(mask.dtype == bool)

    def test_anchor_coupling_dims(self) -> None:
        h5p = self._h5_path()
        A, W = 5, 15
        _make_anchor_h5(h5p, A=A, W_coupling=W)
        surf = read_anchor_surface(h5p)
        assert surf.coupling is not None
        self.assertEqual(surf.coupling.n_windows, W)
        self.assertEqual(surf.coupling.anchor_dim, A)
        self.assertEqual(surf.coupling.mnps_dim, 3)

    def test_coupling_diagnostics_usable(self) -> None:
        h5p = self._h5_path()
        _make_anchor_h5(h5p, T=100, W_coupling=20)
        surf = read_anchor_surface(h5p)
        assert surf.coupling is not None
        d = surf.coupling.diagnostics
        self.assertEqual(d.status, "adjusted")
        self.assertTrue(d.is_usable(min_retained=5, min_retention=0.1))

    def test_coupling_forward_reverse_drive(self) -> None:
        h5p = self._h5_path()
        _make_anchor_h5(h5p, W_coupling=10)
        surf = read_anchor_surface(h5p)
        assert surf.coupling is not None
        fwd = surf.coupling.forward_drive()
        rev = surf.coupling.reverse_drive()
        self.assertEqual(fwd.shape, (10,))
        self.assertEqual(rev.shape, (10,))
        self.assertTrue(np.all(fwd >= 0))

    def test_summary_dict(self) -> None:
        h5p = self._h5_path()
        _make_anchor_h5(h5p)
        surf = read_anchor_surface(h5p, subject_id="sub-test", task="digit_span")
        s = surf.summary()
        self.assertEqual(s["subject_id"], "sub-test")
        self.assertEqual(s["task"], "digit_span")
        self.assertIn("coupling_windows_retained", s)

    def test_missing_anchor_state_returns_none(self) -> None:
        h5p = self._h5_path()
        with h5py.File(h5p, "w") as f:
            f.create_dataset("mnps_3d", data=np.zeros((10, 3), dtype=np.float32))
        surf = read_anchor_surface(h5p)
        self.assertFalse(surf.has_state)
        self.assertFalse(surf.has_quality)
        self.assertFalse(surf.has_coupling)

    def test_probe_anchor_capabilities_from_manifest(self) -> None:
        manifest = {
            "capabilities": {
                "anchor_state": True,
                "anchor_quality": True,
                "anchor_coupling": True,
                "counts": {
                    "h5_with_anchor_state": 130,
                    "h5_with_anchor_quality": 128,
                    "h5_with_anchor_coupling": 52,
                },
            }
        }
        probe = probe_anchor_capabilities_from_manifest(manifest)
        self.assertTrue(probe.has_anchor_state)
        self.assertTrue(probe.has_anchor_coupling)
        self.assertEqual(probe.n_with_anchor_state, 130)
        self.assertEqual(probe.n_with_anchor_coupling, 52)
        self.assertTrue(probe.is_usable())


# ---------------------------------------------------------------------------
# Tests: block_native module
# ---------------------------------------------------------------------------

class BlockNativeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _make_subject_dir(
        self,
        name: str = "sub-001_rest",
        *,
        subject_id: str = "sub-001",
        n_rows: int = 40,
        stage_codes: tuple = (0, 1, 5),
        write_summary: bool = True,
    ) -> Path:
        d = self.root / name
        d.mkdir(parents=True, exist_ok=True)
        _make_block_native_csv(d / "block_native_windows.csv", subject_id=subject_id, n_rows=n_rows, stage_codes=stage_codes)
        if write_summary:
            summary = {"subject": subject_id, "task": name.split("_", 1)[-1]}
            (d / "summary.json").write_text(json.dumps(summary))
        return d

    def test_load_block_native_table(self) -> None:
        d = self._make_subject_dir()
        df = load_block_native_table(d)
        self.assertIsNotNone(df)
        assert df is not None
        self.assertGreater(len(df), 0)
        self.assertIn("m", df.columns)
        self.assertIn("anchor_index", df.columns)

    def test_load_block_native_table_missing(self) -> None:
        d = self.root / "empty"
        d.mkdir()
        result = load_block_native_table(d)
        self.assertIsNone(result)

    def test_mnps_finite_mask(self) -> None:
        d = self._make_subject_dir()
        df = load_block_native_table(d)
        assert df is not None
        mask = mnps_finite_mask(df)
        self.assertEqual(len(mask), len(df))
        self.assertTrue(mask.all())

    def test_anchor_support_mask(self) -> None:
        d = self._make_subject_dir()
        df = load_block_native_table(d)
        assert df is not None
        mask = anchor_support_mask(df, min_support=0.5)
        self.assertEqual(len(mask), len(df))
        self.assertTrue(mask.dtype == bool)

    def test_combined_qc_mask(self) -> None:
        d = self._make_subject_dir()
        df = load_block_native_table(d)
        assert df is not None
        mask = combined_qc_mask(df, require_mnps_finite=True, min_anchor_support=0.3)
        self.assertEqual(len(mask), len(df))

    def test_subject_center(self) -> None:
        d1 = self._make_subject_dir("sub-001_rest", subject_id="sub-001")
        d2 = self._make_subject_dir("sub-002_rest", subject_id="sub-002")
        df = pd.concat([load_block_native_table(d1), load_block_native_table(d2)], ignore_index=True)  # type: ignore[arg-type]
        df_sc = subject_center(df, ["m", "d", "e", "anchor_index"])
        self.assertIn("m_sc", df_sc.columns)
        self.assertIn("anchor_index_sc", df_sc.columns)
        for sub in ["sub-001", "sub-002"]:
            subset = df_sc[df_sc["subject_id"] == sub]
            self.assertAlmostEqual(float(subset["m_sc"].median()), 0.0, places=10)

    def test_compute_stage_summaries(self) -> None:
        d = self._make_subject_dir(stage_codes=(0, 1, 5))
        df = load_block_native_table(d)
        assert df is not None

        # without labels: numeric codes used as label strings
        summaries_generic = compute_stage_summaries(df)
        codes = {s.stage_code for s in summaries_generic}
        self.assertIn(0, codes)
        self.assertIn(1, codes)
        labels_generic = {s.stage_label for s in summaries_generic}
        self.assertIn("0", labels_generic)
        self.assertIn("1", labels_generic)

        # with explicit ds003838 labels
        summaries = compute_stage_summaries(df, stage_labels=DS003838_STAGE_LABELS)
        labels = {s.stage_label for s in summaries}
        self.assertIn("rest", labels)
        self.assertIn("listen", labels)
        for s in summaries:
            self.assertIn("m", s.mnps_stats)
            self.assertIn("anchor_index", s.anchor_stats)

    def test_load_run_block_native_table(self) -> None:
        self._make_subject_dir("sub-001_rest", subject_id="sub-001", n_rows=20, stage_codes=(0,))
        self._make_subject_dir("sub-002_rest", subject_id="sub-002", n_rows=20, stage_codes=(0,))
        df = load_run_block_native_table(self.root)
        self.assertEqual(len(df), 40)
        self.assertEqual(df["subject_id"].nunique(), 2)

    def test_load_run_block_native_table_with_qc(self) -> None:
        self._make_subject_dir("sub-001_rest", subject_id="sub-001", n_rows=30, stage_codes=(0, 1))
        df = load_run_block_native_table(self.root, apply_qc=True, qc_kwargs={"min_anchor_support": 0.5})
        self.assertGreater(len(df), 0)
        self.assertLessEqual(len(df), 30)

    def test_iter_subject_dirs(self) -> None:
        self._make_subject_dir("sub-001_rest")
        self._make_subject_dir("sub-002_digit_span")
        (self.root / "some_other_file.json").write_text("{}")
        dirs = list(iter_subject_dirs(self.root))
        self.assertEqual(len(dirs), 2)

    def test_build_run_inventory(self) -> None:
        self._make_subject_dir("sub-001_rest", subject_id="sub-001", n_rows=30, stage_codes=(0,))
        self._make_subject_dir("sub-002_rest", subject_id="sub-002", n_rows=30, stage_codes=(0,))

        # generic: no stage labels, numeric code as key
        inv_generic = build_run_inventory(self.root)
        self.assertEqual(inv_generic.n_subject_dirs, 2)
        self.assertEqual(inv_generic.n_with_block_native, 2)
        self.assertGreater(inv_generic.n_windows_total, 0)
        self.assertIn("0", inv_generic.stage_window_counts)

        # with explicit ds003838 labels
        inv = build_run_inventory(self.root, stage_labels=DS003838_STAGE_LABELS)
        self.assertEqual(inv.n_subject_dirs, 2)
        self.assertEqual(inv.n_with_block_native, 2)
        self.assertIn("rest", inv.stage_window_counts)

    def test_load_run_manifest(self) -> None:
        manifest = {"schema": "v2", "dataset_id": "ds003838", "capabilities": {}}
        (self.root / "run_manifest.json").write_text(json.dumps(manifest))
        loaded = load_run_manifest(self.root)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded["dataset_id"], "ds003838")

    def test_load_run_manifest_missing(self) -> None:
        result = load_run_manifest(self.root)
        self.assertIsNone(result)

    def test_run_inventory_fractions(self) -> None:
        self._make_subject_dir("sub-001_rest", subject_id="sub-001")
        inv = build_run_inventory(self.root)
        self.assertGreaterEqual(inv.anchor_availability_fraction, 0.0)
        self.assertLessEqual(inv.anchor_availability_fraction, 1.0)
        self.assertGreaterEqual(inv.anchor_window_fraction, 0.0)
        self.assertLessEqual(inv.anchor_window_fraction, 1.0)

    # --- Config bridging tests ---

    def test_stage_labels_from_dataset_id(self) -> None:
        self.assertEqual(stage_labels_from_dataset_id("ds003838"), DS003838_STAGE_LABELS)
        self.assertEqual(stage_labels_from_dataset_id("ds006036"), DS006036_STAGE_LABELS)
        self.assertEqual(stage_labels_from_dataset_id("unknown_ds"), {})

    def test_known_stage_labels(self) -> None:
        self.assertIn("ds003838", KNOWN_STAGE_LABELS)
        self.assertIn("ds006036", KNOWN_STAGE_LABELS)
        self.assertEqual(KNOWN_STAGE_LABELS["ds003838"][0], "rest")
        self.assertEqual(KNOWN_STAGE_LABELS["ds006036"][50], "photic_5hz")

    def test_stage_labels_from_manifest(self) -> None:
        # known dataset_id → infer from KNOWN_STAGE_LABELS
        manifest = {"dataset_id": "ds003838", "capabilities": {}}
        labels = stage_labels_from_manifest(manifest)
        self.assertEqual(labels[0], "rest")
        self.assertEqual(labels[1], "listen")

    def test_stage_labels_from_manifest_explicit(self) -> None:
        # explicit stage_code_map in manifest capabilities
        manifest = {
            "dataset_id": "custom",
            "capabilities": {
                "stage_code_map": {100: "condition_a", 200: "condition_b"}
            },
        }
        labels = stage_labels_from_manifest(manifest)
        self.assertEqual(labels[100], "condition_a")
        self.assertEqual(labels[200], "condition_b")

    def test_stage_labels_from_manifest_unknown(self) -> None:
        manifest = {"dataset_id": "totally_new_dataset", "capabilities": {}}
        labels = stage_labels_from_manifest(manifest)
        self.assertEqual(labels, {})

    def test_stage_labels_from_config_block_native(self) -> None:
        cfg = BlockNativeAnalysisConfig(
            stage_code_map={0: "baseline", 1: "task"},
            anchor_state_cols=[],
            anchor_dot_cols=[],
            anchor_quality_cols=[],
            hrv_cols=[],
            qc=BlockNativeQCConfig(
                require_mnps_finite=True,
                min_anchor_support=0.3,
                min_anchor_state_finite=1,
            ),
            prefer_parquet=True,
        )

        class FakeCfg:
            block_native = cfg

        labels = stage_labels_from_config(FakeCfg())
        self.assertEqual(labels[0], "baseline")
        self.assertEqual(labels[1], "task")

    def test_stage_labels_from_config_empty(self) -> None:
        class EmptyCfg:
            pass
        labels = stage_labels_from_config(EmptyCfg())
        self.assertEqual(labels, {})

    def test_qc_mask_from_config(self) -> None:
        d = self._make_subject_dir(n_rows=30)
        df = load_block_native_table(d)
        assert df is not None

        cfg = BlockNativeAnalysisConfig(
            stage_code_map={},
            anchor_state_cols=[],
            anchor_dot_cols=[],
            anchor_quality_cols=[],
            hrv_cols=[],
            qc=BlockNativeQCConfig(
                require_mnps_finite=True,
                min_anchor_support=0.5,
                min_anchor_state_finite=1,
            ),
            prefer_parquet=True,
        )

        class FakeCfg:
            block_native = cfg

        mask = qc_mask_from_config(df, FakeCfg())
        self.assertEqual(len(mask), len(df))
        self.assertTrue(mask.dtype == bool)

    def test_block_native_analysis_config_from_yaml(self) -> None:
        yaml_content = (
            "dataset: testds\n"
            "block_native:\n"
            "  stage_code_map:\n"
            "    10: condition_a\n"
            "    20: condition_b\n"
            "  anchor_state_cols:\n"
            "    - sympathetic_index\n"
            "    - vagal_index\n"
            "  prefer_parquet: true\n"
            "  qc:\n"
            "    require_mnps_finite: true\n"
            "    min_anchor_support: 0.4\n"
            "    min_anchor_state_finite: 2\n"
        )
        yaml_path = self.root / "test_cfg.yaml"
        yaml_path.write_text(yaml_content)
        cfg = load_analysis_config(yaml_path)
        self.assertEqual(cfg.block_native.stage_code_map[10], "condition_a")
        self.assertEqual(cfg.block_native.stage_code_map[20], "condition_b")
        self.assertIn("sympathetic_index", cfg.block_native.anchor_state_cols)
        self.assertAlmostEqual(cfg.block_native.qc.min_anchor_support, 0.4)
        self.assertEqual(cfg.block_native.qc.min_anchor_state_finite, 2)
        self.assertTrue(cfg.block_native.prefer_parquet)

    def test_block_native_analysis_config_defaults_from_yaml(self) -> None:
        # No block_native section → defaults
        yaml_content = "dataset: testds\n"
        yaml_path = self.root / "minimal_cfg.yaml"
        yaml_path.write_text(yaml_content)
        cfg = load_analysis_config(yaml_path)
        self.assertEqual(cfg.block_native.stage_code_map, {})
        self.assertEqual(cfg.block_native.anchor_state_cols, [])
        self.assertAlmostEqual(cfg.block_native.qc.min_anchor_support, 0.3)
        self.assertTrue(cfg.block_native.prefer_parquet)

    def test_load_run_block_native_table_with_cfg(self) -> None:
        self._make_subject_dir("sub-001_rest", subject_id="sub-001", n_rows=20)
        cfg = BlockNativeAnalysisConfig(
            stage_code_map={0: "rest"},
            anchor_state_cols=[],
            anchor_dot_cols=[],
            anchor_quality_cols=[],
            hrv_cols=[],
            qc=BlockNativeQCConfig(
                require_mnps_finite=True,
                min_anchor_support=0.3,
                min_anchor_state_finite=1,
            ),
            prefer_parquet=False,
        )

        class FakeCfg:
            block_native = cfg

        df = load_run_block_native_table(self.root, apply_qc=True, cfg=FakeCfg())
        self.assertGreater(len(df), 0)

    def test_build_run_inventory_with_cfg(self) -> None:
        self._make_subject_dir("sub-001_rest", subject_id="sub-001", n_rows=30, stage_codes=(0,))
        cfg = BlockNativeAnalysisConfig(
            stage_code_map={0: "rest"},
            anchor_state_cols=[],
            anchor_dot_cols=[],
            anchor_quality_cols=[],
            hrv_cols=[],
            qc=BlockNativeQCConfig(
                require_mnps_finite=True,
                min_anchor_support=0.3,
                min_anchor_state_finite=1,
            ),
            prefer_parquet=True,
        )

        class FakeCfg:
            block_native = cfg

        inv = build_run_inventory(self.root, cfg=FakeCfg())
        self.assertIn("rest", inv.stage_window_counts)

    def test_compute_stage_summaries_string_stage_col(self) -> None:
        """compute_stage_summaries must not crash when stage_col holds strings (e.g. condition)."""
        df = pd.DataFrame(
            {
                "condition": ["awake", "awake", "nrem2", "nrem3"],
                "subject_id": ["s1", "s1", "s1", "s1"],
                "block_id": [0, 0, 1, 2],
                "mnps_m": [1.0, 1.1, 2.0, 3.0],
            }
        )
        summaries = compute_stage_summaries(df, stage_col="condition")
        labels = {s.stage_label for s in summaries}
        self.assertIn("awake", labels)
        self.assertIn("nrem2", labels)
        self.assertIn("nrem3", labels)
        # stage_code should be None for string-valued stage columns
        for s in summaries:
            self.assertIsNone(s.stage_code)

    def test_build_run_inventory_string_stage_col(self) -> None:
        """build_run_inventory must handle a string condition column gracefully."""
        sub_dir = self.root / "sub-001_sleep"
        sub_dir.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(
            {
                "condition": ["awake"] * 10 + ["nrem3"] * 10,
                "subject_id": ["sub-001"] * 20,
                "block_id": [0] * 10 + [1] * 10,
                "mnps_m": [1.0] * 20,
                "mnps_d": [0.5] * 20,
            }
        )
        df.to_csv(sub_dir / "block_native_windows.csv", index=False)
        inv = build_run_inventory(self.root, stage_col="condition")
        self.assertIn("awake", inv.stage_window_counts)
        self.assertIn("nrem3", inv.stage_window_counts)

    def test_sleep_stage_code_to_label_constant(self) -> None:
        """SLEEP_STAGE_CODE_TO_LABEL mirrors legacy_adapters and is in KNOWN_STAGE_LABELS."""
        self.assertIn(0, SLEEP_STAGE_CODE_TO_LABEL)  # awake
        self.assertIn(2, SLEEP_STAGE_CODE_TO_LABEL)  # nrem2
        self.assertIn(3, SLEEP_STAGE_CODE_TO_LABEL)  # nrem3
        self.assertIn(4, SLEEP_STAGE_CODE_TO_LABEL)  # rem
        self.assertEqual(SLEEP_STAGE_CODE_TO_LABEL[0], "awake")
        self.assertIn("_sleep_default", KNOWN_STAGE_LABELS)
        self.assertIs(KNOWN_STAGE_LABELS["_sleep_default"], SLEEP_STAGE_CODE_TO_LABEL)

    def test_stage_labels_from_config_sleep_data_contrast_flag(self) -> None:
        """stage_labels_from_config returns SLEEP_STAGE_CODE_TO_LABEL when sleep_data_contrast=True."""
        from nmd_analysis.block_native import stage_labels_from_config

        class FakeFlags:
            stage_code_map: dict = {}
            sleep_data_contrast: bool = True

        class FakeCfg:
            flags = FakeFlags()

        result = stage_labels_from_config(FakeCfg())
        self.assertEqual(result, SLEEP_STAGE_CODE_TO_LABEL)

    def test_stage_labels_from_config_sleep_contrast_overridden_by_explicit_map(self) -> None:
        """Explicit stage_code_map takes precedence over sleep_data_contrast fallback."""
        from nmd_analysis.block_native import stage_labels_from_config

        class FakeFlags:
            stage_code_map: dict = {0: "baseline", 1: "stim"}
            sleep_data_contrast: bool = True

        class FakeCfg:
            flags = FakeFlags()

        result = stage_labels_from_config(FakeCfg())
        self.assertEqual(result, {0: "baseline", 1: "stim"})


if __name__ == "__main__":
    unittest.main()
